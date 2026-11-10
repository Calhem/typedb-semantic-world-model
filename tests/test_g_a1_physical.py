"""Core 0.4 Stage A1 (LABS-1.006): the physical reference world (a gearbox in a workshop) in TypeDB.

Identity, classification, composition, constitution, containment, frames and positions, measurement vs design values,
time, perspective and hypothetical worlds, and selective/full-load equivalence. The world is built once per module
(read-only tests) in a throwaway database; tests that change it build their own.
"""

import math
import uuid

import pytest

from conftest import FakeClock
from worldmodel import PHYSICAL_MODULES, WorldModel
from worldmodel import typeql as q
from worldmodel.examples import gearbox as g
from worldmodel.model import READ, DEFAULT_MODULES
from worldmodel.physical import yaw
from worldmodel.semantics import Status


def fresh(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=PHYSICAL_MODULES, clock=FakeClock())
    return wm, g.build(wm)


@pytest.fixture(scope="module")
def ref(driver):
    wm, ids = fresh(driver)
    try:
        yield wm, ids
    finally:
        driver.databases.get(wm.database).delete()


@pytest.fixture
def world(ref):
    wm, ids = ref
    wm.selective = True
    yield wm, ids["world"], ids
    wm.selective = True


@pytest.fixture
def own(driver):
    wm, ids = fresh(driver)
    try:
        yield wm, ids["world"], ids
    finally:
        driver.databases.get(wm.database).delete()


def flatten(tree):
    return [p["id"] for p in tree["parts"]] + [x for p in tree["parts"] for x in flatten(p)]


# ---- identity and classification ---------------------------------------------------------------------------------
def test_objects_frames_categories_and_measures_are_different_kinds_of_thing(world):
    wm, w, _ = world
    with wm.driver.transaction(wm.database, READ) as tx:
        kinds = wm._kinds_of(tx, ["gbx-100", "bearing-3", "workshop", "f-gearbox", "steel", "mass", "kg", "inspector"])
    assert kinds == {"gbx-100": "physical-object", "bearing-3": "physical-object", "workshop": "place",
                     "f-gearbox": "spatial-frame", "steel": "category", "mass": "quality-kind", "kg": "unit",
                     "inspector": "social-object"}
    assert wm.find("Gearbox GBX-100") == ["gbx-100"]                       # identity is the id, not the name
    with wm.driver.transaction(wm.database, READ) as tx:                    # a description is text on the thing
        (row,) = q.rows(tx, 'match $x has wm-id "gbx-100", has description $d;')
    assert q.opt(row, "d") == "two-stage spur gearbox, concept assembly"


def test_kinds_and_materials_are_classifications(world):
    wm, w, _ = world
    kinds = {c for f in wm.facts_about(w, "bearing-3", g.AFTER) if f["type"] == "classified-as"
             for c in f["roles"]["class"]}
    assert kinds == {"bearing", "steel"}
    assert {t: wm.materials(w, t, g.AFTER) for t in ("housing", "cover", "gasket", "gear-in")} == \
        {"housing": ["cast-iron"], "cover": ["aluminium"], "gasket": ["rubber"], "gear-in": ["steel"]}
    assert wm.materials(w, "gbx-100", g.AFTER) == []                         # an assembly has no single material


# ---- composition, constitution, containment ----------------------------------------------------------------------
def test_composition_is_a_tree_of_part_of_facts_that_changes_over_time(world):
    wm, w, _ = world
    before, after = (wm.composition(w, "gbx-100", t) for t in (g.BEFORE, g.AFTER))
    sub = {n["id"]: [p["id"] for p in n["parts"]] for n in before["parts"]}
    assert sub["shaft-asm-in"] == ["bearing-1", "gear-in", "input-shaft"]
    assert {n["id"]: [p["id"] for p in n["parts"]] for n in after["parts"]}["shaft-asm-in"] == \
        ["bearing-3", "gear-in", "input-shaft"]
    assert len(flatten(before)) == 14 and sorted(flatten(after)) == wm.parts(w, "gbx-100", g.AFTER)
    stored = wm.parts_in_database(w, "gbx-100")          # TypeDB function over records: ignores time and acceptance
    assert {"bearing-1", "bearing-3"} <= set(stored)


def test_constitution_is_not_composition(world):
    wm, w, _ = world
    facts = wm.facts_about(w, "cover", g.AFTER)
    made = [f for f in facts if f["type"] == "constitution"]
    assert [(f["roles"]["constituted"], f["roles"]["constituent"]) for f in made] == [(["cover"], ["alu-blank-7"])]
    assert "alu-blank-7" not in wm.parts(w, "cover", g.AFTER) and "alu-blank-7" not in wm.parts(w, "gbx-100", g.AFTER)


def test_containment_through_places(world):
    wm, w, _ = world
    c = wm.contents(w, "workshop", g.AFTER)
    assert c["located"] == [] and [p["place"] for p in c["places"]] == ["bay-1", "store-shelf"]
    bay, shelf = c["places"]
    assert bay["located"] == ["bench-1", "gbx-100", "scale-3"]
    assert shelf["located"] == ["bearing-1"]
    assert wm.contents(w, "store-shelf", g.BEFORE)["located"] == ["bearing-3"]
    loc = wm.value_at(w, "located-at", "gbx-100", g.AFTER)
    assert (loc.status, loc.values) == (Status.ASSERTED, ("bay-1",))
    # a component is in the gearbox by composition, not by location: it has no place of its own
    assert wm.value_at(w, "located-at", "gear-in", g.AFTER).status == Status.NOT_YET_KNOWN


# ---- frames and positions ----------------------------------------------------------------------------------------
def test_frames_are_anchored_and_related_by_stored_transforms(world):
    wm, w, _ = world
    bench = wm.frame_info(w, "f-bench", g.AFTER)
    assert [a["anchor"] for a in bench["anchored_to"]] == ["bench-1"]
    (parent,) = bench["parents"]
    assert parent["parent"] == "f-workshop" and parent["translation"] == (4.0, 2.5, 0.0)
    assert parent["rotation"] == pytest.approx(yaw(math.pi / 2))
    assert [c["child"] for c in bench["children"]] == ["f-gearbox"]
    assert bench["positioned"] == ["gbx-100"]
    assert wm.frame_info(w, "f-workshop", g.AFTER)["parents"] == []        # the root frame
    anchor = wm.value_at(w, "anchored-to", "f-gearbox", g.AFTER)
    assert (anchor.status, anchor.values) == (Status.ASSERTED, ("gbx-100",))


def test_positions_are_ranges_in_a_frame_and_change_over_time(world):
    wm, w, _ = world
    (bench,) = wm.poses(w, "bench-1", g.AFTER)
    assert (bench["frame"], bench["x"], bench["y"], bench["z"]) == ("f-workshop", (3.95, 4.05), (2.45, 2.55), (0.0, 0.0))
    assert bench["orientation"] == pytest.approx(yaw(math.pi / 2))
    (gear,) = wm.poses(w, "gear-in", g.AFTER)
    assert (gear["frame"], gear["x"], gear["orientation"]) == ("f-gearbox", (0.02, 0.02), None)
    assert [p["frame"] for p in wm.poses(w, "bearing-1", g.BEFORE)] == ["f-gearbox"]
    assert wm.poses(w, "bearing-1", g.AFTER) == []                          # removed at T1
    assert wm.poses(w, "bearing-3", g.BEFORE) == [] and len(wm.poses(w, "bearing-3", g.AFTER)) == 1
    hist = [h for h in wm.history(w, "bearing-1") if h["type"] == "positioned-in"]
    assert len(hist) == 2                                                   # the original and its stated end


def test_invalid_positions_and_rotations_are_rejected(own):
    wm, w, _ = own
    with pytest.raises(ValueError, match="lower <= upper"):
        wm.position(w, "gear-in", "f-gearbox", (0.1, 0.0), 0, 0, start=g.T0)
    with pytest.raises(ValueError, match="unit quaternion"):
        wm.position(w, "gear-in", "f-gearbox", 0, 0, 0, orientation=(1, 0, 0, 1e-4), start=g.T0)
    with pytest.raises(ValueError, match="unit quaternion"):
        wm.relate_frames(w, "f-bench", "f-gearbox", (0, 0, 0), (0.5, 0.5, 0.5, 0.5000001), start=g.T0)
    with pytest.raises(ValueError, match="two different frames"):
        wm.relate_frames(w, "f-bench", "f-bench", (0, 0, 0), start=g.T0)
    with pytest.raises(ValueError, match="unknown proposition parameters"):
        wm.attest(w, "located-at", {"located": "gbx-100", "place": "bay-1"}, params={"x-min": 1.0}, start=g.T0)


def test_a_frame_has_one_anchor_at_a_time(own):
    wm, w, _ = own
    assert wm.slots()["anchored-to"] == [(("frame",), "anchor")]
    wm.anchor_frame(w, "f-gearbox", "housing", start=g.T0, until_superseded=True)
    a = wm.value_at(w, "anchored-to", "f-gearbox", g.AFTER)
    assert (a.status, a.values) == (Status.DISPUTED, ("gbx-100", "housing"))
    held = wm.holds(w, "anchored-to", {"frame": "f-gearbox", "anchor": "housing"}, g.AFTER)
    assert held.status == Status.DISPUTED and len(held.conflicts) == 1


# ---- measurement vs design, perspective, hypothetical world ------------------------------------------------------
def test_a_measurement_and_a_design_value_are_separate_attested_statements(world):
    wm, w, ids = world
    masses = {f["support"][0]: f["params"] for f in wm.facts_about(w, "housing", g.AFTER) if f["type"] == "has-quality"}
    assert masses == {ids["measured_mass"]: {"lower": 12.35, "upper": 12.45},
                      ids["design_mass"]: {"lower": 12.5, "upper": 12.5}}
    bases = {r["attestation"]: (r["attester"], r["basis"]) for r in wm.history(w, "housing", type="has-quality")}
    assert bases == {ids["measured_mass"]: ("scale-3", "observation"), ids["design_mass"]: ("design-office", "testimony")}


def test_another_sources_material_claim_is_its_own_perspective(world):
    wm, w, ids = world
    assert wm.materials(w, "cover", g.AFTER) == ["aluminium"]
    assert wm.materials(w, "cover", g.AFTER, perspective="inspector") == ["magnesium"]
    claim = wm.holds(w, "classified-as", {"classified": "cover", "class": "magnesium"}, g.AFTER)
    assert claim.status == Status.UNKNOWN and claim.alternatives == (ids["inspector_claim"],)


def test_a_hypothetical_design_change_leaves_the_actual_world_alone(world):
    wm, w, ids = world
    plan = ids["plan"]
    assert wm.materials(plan, "cover", g.PLAN_AT) == ["steel"]
    assert wm.materials(plan, "cover", g.AFTER) == ["aluminium"]            # inherited before the plan's start
    assert wm.materials(w, "cover", g.PLAN_AT) == ["aluminium"]
    assert wm.composition(plan, "gbx-100", g.PLAN_AT) == wm.composition(w, "gbx-100", g.PLAN_AT)


# ---- equivalence and compatibility -------------------------------------------------------------------------------
def test_selective_and_full_load_agree_on_the_reference_world(world):
    wm, w, ids = world

    def answers():
        out = []
        for t in (g.BEFORE, g.AFTER):
            out += [wm.composition(w, "gbx-100", t), wm.contents(w, "workshop", t),
                    [wm.poses(w, x, t) for x in ("bench-1", "gbx-100", "bearing-1", "bearing-3", "cover")],
                    [wm.frame_info(w, f, t) for f, *_ in g.FRAMES],
                    [wm.materials(w, x, t) for x in ("housing", "cover", "bearing-3")],
                    wm.value_at(w, "located-at", "bearing-3", t), wm.value_at(w, "anchored-to", "f-bench", t),
                    wm.holds(w, "part-of", {"part": "bearing-1", "whole": "shaft-asm-in"}, t),
                    wm.facts_about(w, "housing", t)]
        out += [wm.materials(w, "cover", g.AFTER, perspective="inspector"), wm.materials(ids["plan"], "cover", g.PLAN_AT)]
        return out

    wm.selective = True
    selective = answers()
    wm.selective = False
    assert answers() == selective


def test_the_physical_module_is_opt_in_and_installs_on_an_existing_database(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, clock=FakeClock())
    try:
        assert DEFAULT_MODULES == ("core", "core-0.4-a0") and "positioned-in" not in wm.proposition_types()
        wm.install_module("core-0.4-a")
        assert {"positioned-in", "frame-transform", "anchored-to", "constitution"} <= wm.proposition_types()
        assert wm.slots()["anchored-to"] == [(("frame",), "anchor")]
        wm.add_entity("physical-object", "box", id="box")
        wm.add_entity("spatial-frame", "room frame", id="room")
        wm.create_world("actual", id="actual")
        wm.position("actual", "box", "room", (1.0, 1.2), 0.5, 0.0, start=g.T0, until_superseded=True)
        assert wm.poses("actual", "box", g.AFTER)[0]["x"] == (1.0, 1.2)
    finally:
        driver.databases.get(name).delete()
