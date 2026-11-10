"""Core 0.4 Stage A2 (LABS-1.007): spatial reasoning across frames and judgement of position statements.

Part 1 tests the transform mathematics on its own (no database). Part 2 tests frame chains on small synthetic frame
graphs: multi-hop, inverse use, rotated frames, missing, ambiguous and cyclic relationships. Part 3 judges position
statements (identical, overlapping, disjoint, other frames, incomparable) with time, perspective and hypothetical
worlds. Part 4 uses the gearbox reference world, including selective/full-load equivalence.
"""

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from conftest import FakeClock
from worldmodel import PHYSICAL_MODULES, WorldModel
from worldmodel.examples import gearbox as g
from worldmodel.physical import yaw
from worldmodel.semantics import Status
from worldmodel.spatial import (Transform, boxes_overlap, map_box, params_compatible, qmul, rotate, same_rotation)

T0 = datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc)
T = T0 + timedelta(hours=2)


def close(a, b, tol=1e-9):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def flat(x):
    return [v for item in x for v in item]


# ---- part 1: mathematics ---------------------------------------------------------------------------------------
def test_rotation_and_translation_follow_the_documented_convention():
    t = Transform(yaw(math.pi / 2), (4.0, 2.5, 0.0))           # child axes turned +90 deg about z, origin at (4, 2.5)
    assert close(t.apply((1.0, 0.0, 0.0)), (4.0, 3.5, 0.0))     # child +x points along parent +y
    assert close(t.apply((0.0, 1.0, 0.0)), (3.0, 2.5, 0.0))     # child +y points along parent -x
    assert close(rotate(yaw(math.pi), (1.0, 2.0, 3.0)), (-1.0, -2.0, 3.0))


def test_composition_and_inverse():
    a = Transform(yaw(0.3), (1.0, -2.0, 0.5))
    b = Transform(qmul(yaw(-1.1), (math.cos(0.2), math.sin(0.2), 0.0, 0.0)), (0.2, 0.0, 3.0))
    p = (0.7, -0.4, 1.9)
    assert close(a.then(b).apply(p), a.apply(b.apply(p)))       # T_AC = T_AB ∘ T_BC
    assert close(a.inverse().apply(a.apply(p)), p)
    assert a.then(a.inverse()).close_to(Transform()) and a.inverse().then(a).close_to(Transform())
    assert close(a.then(b).inverse().apply(p), b.inverse().apply(a.inverse().apply(p)))


def test_quaternion_sign_and_parameter_compatibility():
    q = yaw(0.7)
    assert same_rotation(q, tuple(-c for c in q)) and not same_rotation(q, yaw(0.71))
    rng = {"x-min": 1.0, "x-max": 2.0, "y-min": 0.0, "y-max": 0.0, "z-min": 0.0, "z-max": 0.0}
    assert params_compatible(rng, rng)                                              # identical
    assert params_compatible(rng, {**rng, "x-min": 1.9, "x-max": 3.0})              # overlapping
    assert params_compatible(rng, {**rng, "x-min": 2.0, "x-max": 3.0})              # touching
    assert not params_compatible(rng, {**rng, "x-min": 2.1, "x-max": 3.0})          # disjoint
    assert not params_compatible({**rng, "qw": 1.0, "qx": 0.0, "qy": 0.0, "qz": 0.0},
                                 {**rng, **dict(zip(("qw", "qx", "qy", "qz"), yaw(0.5)))})  # different orientations
    assert params_compatible({"tx": 1.0, "qw": 1.0}, {"tx": 1.0 + 1e-12, "qw": 1.0})
    assert not params_compatible({"tx": 1.0}, {"tx": 1.001})


def test_range_propagation_is_conservative():
    box = {"x": (-1.0, 1.0), "y": (-0.5, 0.5), "z": (0.0, 0.0)}
    out = map_box(Transform(yaw(math.pi / 4), (10.0, 0.0, 0.0)), box)
    half = (1.0 + 0.5) / math.sqrt(2)                       # rotated 45 deg: the corners reach 1.5/sqrt(2)
    assert close(out["x"], (10.0 - half, 10.0 + half)) and close(out["y"], (-half, half))
    turned = map_box(Transform(yaw(math.pi / 2)), box)
    assert flat(turned[a] for a in "xyz") == pytest.approx([-0.5, 0.5, -1.0, 1.0, 0, 0])
    a, b = {"x": (0, 1), "y": (0, 1), "z": (0, 1)}, {"x": (1, 2), "y": (0.5, 3), "z": (-1, 0)}
    assert boxes_overlap(a, b) and not boxes_overlap(a, {**b, "x": (1.01, 2)})


# ---- part 2: frame chains in TypeDB ------------------------------------------------------------------------------
@pytest.fixture
def space(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=PHYSICAL_MODULES, clock=FakeClock())
    try:
        w = wm.create_world("actual", id="actual")
        for f in ("A", "B", "C", "D", "E"):
            wm.add_entity("spatial-frame", f"frame {f}", id=f)
        for n in ("box", "crate", "cam", "tracker"):
            wm.add_entity("physical-object", n, id=n)
        yield wm, w
    finally:
        driver.databases.get(name).delete()


def link(wm, w, parent, child, t, q=(1.0, 0.0, 0.0, 0.0), **kw):
    kw.setdefault("start", T0)
    kw.setdefault("until_superseded", "end" not in kw)
    return wm.relate_frames(w, parent, child, t, q, **kw)


def test_multi_hop_chain_with_rotations_and_inverse_use(space):
    wm, w = space
    ab = link(wm, w, "A", "B", (1.0, 0.0, 0.0), yaw(math.pi / 2))
    bc = link(wm, w, "B", "C", (0.0, 2.0, 0.0))
    dc = link(wm, w, "D", "C", (0.0, 0.0, 1.0), yaw(math.pi))      # C is D's child: reaching D from C is forward
    r = wm.transform_between(w, "C", "A", T)
    assert r["status"] == Status.INFERRED and [s["direction"] for s in r["chains"][0]["steps"]] == ["forward"] * 2
    assert close(r["transform"].apply((0.0, 0.0, 0.0)), (-1.0, 0.0, 0.0))     # C's origin: (0,2,0) in B -> (-1,0,0) in A
    back = wm.transform_between(w, "A", "C", T)
    assert back["transform"].then(r["transform"]).close_to(Transform())       # inverse chain
    assert [s["direction"] for s in back["chains"][0]["steps"]] == ["inverse", "inverse"]
    to_d = wm.transform_between(w, "A", "D", T)                               # A -> B -> C (inverse) -> D (forward)
    assert to_d["chains"][0]["frames"] == ["A", "B", "C", "D"]
    assert [s["direction"] for s in to_d["chains"][0]["steps"]] == ["inverse", "inverse", "forward"]
    assert {x for s in to_d["chains"][0]["steps"] for x in s["support"]} == {ab, bc, dc}   # provenance of every hop
    assert wm.frames_linked_in_database(w, "A") == ["B", "C", "D"]


def test_missing_chains_are_unknown_not_invented(space):
    wm, w = space
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    r = wm.transform_between(w, "A", "E", T)
    assert (r["status"], r["transform"], r["reason"]) == (Status.UNKNOWN, None, "no frame chain from A to E")
    wm.position(w, "box", "E", 1.0, 2.0, 3.0, start=T0, until_superseded=True)
    a = wm.where(w, "box", "A", T)
    assert a["status"] == Status.UNKNOWN and a["candidates"] == [] and a["incomparable"][0]["frame"] == "E"
    before = wm.transform_between(w, "A", "B", T0 - timedelta(hours=1))          # not yet related at that time
    assert before["status"] == Status.UNKNOWN


def test_ambiguous_and_cyclic_frame_relationships(space):
    wm, w = space
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    link(wm, w, "B", "C", (1.0, 0.0, 0.0))
    link(wm, w, "A", "C", (2.0, 0.0, 0.0))                          # a second, consistent route: a cycle A-B-C
    r = wm.transform_between(w, "C", "A", T)
    assert (r["status"], r["cycle"], len(r["chains"])) == (Status.INFERRED, True, 2)
    assert r["chains"][0]["frames"] == ["C", "A"]                   # shortest first
    link(wm, w, "C", "D", (0.0, 1.0, 0.0))
    link(wm, w, "B", "D", (1.0, 1.5, 0.0))                          # inconsistent: D is 0.5 m apart on two routes
    d = wm.transform_between(w, "D", "A", T)
    assert d["status"] == Status.DISPUTED and d["reason"] == "chains disagree (ambiguous frame relationships)"
    assert d["cycle"] and len(d["chains"]) >= 2


def test_two_transform_claims_for_one_pair_are_judged_by_the_shared_conflict_check(space):
    wm, w = space
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    other = link(wm, w, "A", "B", (1.2, 0.0, 0.0), attester="tracker")
    assert wm.transform_between(w, "B", "A", T)["status"] == Status.INFERRED     # unaccepted: not part of the view
    wm.accept(other)
    assert wm.transform_between(w, "B", "A", T)["status"] == Status.DISPUTED
    held = wm.holds(w, "frame-transform", {"parent": "A", "child": "B"}, T)
    assert held.status == Status.DISPUTED and len(held.conflicts) == 1
    assert wm.transform_between(w, "B", "A", T, perspective="tracker")["transform"].t == (1.2, 0.0, 0.0)


# ---- part 3: position judgement ----------------------------------------------------------------------------------
def pos(wm, w, thing, frame, x, y, z, **kw):
    kw.setdefault("start", T0)
    kw.setdefault("until_superseded", "end" not in kw)
    return wm.position(w, thing, frame, x, y, z, **kw)


def test_identical_overlapping_and_disjoint_positions(space):
    wm, w = space
    pos(wm, w, "box", "A", (1.0, 1.2), 0.0, 0.0)
    c = pos(wm, w, "box", "A", (1.0, 1.2), 0.0, 0.0, attester="cam")      # identical content, another source
    wm.accept(c)
    one = wm.where(w, "box", "A", T)
    assert (one["status"], one["judgement"], len(one["candidates"])) == (Status.ASSERTED, "single", 1)
    assert len(one["candidates"][0]["position_support"]) == 2              # one content, two attestations
    o = pos(wm, w, "box", "A", (1.15, 1.4), (-0.01, 0.01), 0.0, attester="cam")
    wm.accept(o)
    two = wm.where(w, "box", "A", T)
    assert (two["status"], two["judgement"], two["conflicts"]) == (Status.ASSERTED, "compatible", [])
    assert [c["x"] for c in two["candidates"]] == [(1.0, 1.2), (1.15, 1.4)]   # not merged into one range
    d = pos(wm, w, "box", "A", (3.0, 3.1), 0.0, 0.0, attester="tracker")
    wm.accept(d)
    three = wm.where(w, "box", "A", T)
    assert (three["status"], three["judgement"]) == (Status.DISPUTED, "conflicting")
    assert three["conflicts"] == [(0, 2), (1, 2)]
    held = wm.holds(w, "positioned-in", {"positioned": "box", "frame": "A"}, T)
    assert held.status == Status.DISPUTED                                  # same shared conflict check (F-4)


def test_positions_in_different_frames_are_compared_through_derivation(space):
    wm, w = space
    link(wm, w, "A", "B", (10.0, 0.0, 0.0), yaw(math.pi / 2))
    pos(wm, w, "box", "B", (0.9, 1.1), (-0.1, 0.1), 0.0)                    # in A: x 9.9-10.1, y 0.9-1.1
    seen = pos(wm, w, "box", "A", (9.95, 10.05), (1.0, 1.2), 0.0, attester="cam", basis="observation")
    wm.accept(seen)
    a = wm.where(w, "box", "A", T)
    assert (a["status"], a["judgement"]) == (Status.ASSERTED, "compatible")
    derived = next(c for c in a["candidates"] if not c["direct"])
    assert derived["x"] == pytest.approx((9.9, 10.1)) and derived["y"] == pytest.approx((0.9, 1.1))
    assert derived["status"] == Status.INFERRED and derived["rule"] == "frame-transform/v1"
    far = pos(wm, w, "box", "A", (12.0, 12.1), (1.0, 1.2), 0.0, attester="tracker")
    wm.accept(far)
    assert wm.where(w, "box", "A", T)["status"] == Status.DISPUTED
    in_b = wm.where(w, "box", "B", T)                                       # the same conflict seen from B
    assert in_b["status"] == Status.DISPUTED and len(in_b["candidates"]) == 3


def test_temporal_applicability_of_positions_and_transforms(space):
    wm, w = space
    t1 = T0 + timedelta(hours=4)
    link(wm, w, "A", "B", (1.0, 0.0, 0.0), end=t1)
    link(wm, w, "A", "B", (5.0, 0.0, 0.0), start=t1)
    pos(wm, w, "box", "B", 0.5, 0.0, 0.0)
    pos(wm, w, "crate", "A", 0.0, 0.0, 0.0, end=t1)
    assert wm.where(w, "box", "A", T)["candidates"][0]["x"] == pytest.approx((1.5, 1.5))
    assert wm.where(w, "box", "A", t1 + timedelta(hours=1))["candidates"][0]["x"] == pytest.approx((5.5, 5.5))
    assert wm.where(w, "box", "A", T0 - timedelta(hours=1))["status"] == Status.UNKNOWN    # before any statement
    gone = wm.where(w, "crate", "A", t1 + timedelta(hours=1))
    assert gone["status"] == Status.UNKNOWN and gone["candidates"] == []
    assert wm.where(w, "tracker", "A", T)["status"] == Status.NOT_YET_KNOWN


def test_perspective_specific_acceptance(space):
    wm, w = space
    pos(wm, w, "box", "A", 1.0, 0.0, 0.0)
    claim = pos(wm, w, "box", "A", 4.0, 0.0, 0.0, attester="tracker")
    a = wm.where(w, "box", "A", T)
    assert (a["status"], a["alternatives"]) == (Status.ASSERTED, (claim,))    # unreviewed: an alternative only
    own = wm.where(w, "box", "A", T, perspective="tracker")
    assert [c["x"] for c in own["candidates"]] == [(4.0, 4.0)]
    wm.accept(claim)
    assert wm.where(w, "box", "A", T)["status"] == Status.DISPUTED
    wm.accept(claim, "rejected")
    assert wm.where(w, "box", "A", T)["status"] == Status.ASSERTED


def test_hypothetical_worlds_override_inherited_positions_and_transforms(space):
    wm, w = space
    branch = T0 + timedelta(hours=3)
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    pos(wm, w, "box", "B", 0.0, 0.0, 0.0)
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=branch)
    link(wm, h, "A", "B", (7.0, 0.0, 0.0), start=branch)                      # the plan moves frame B
    pos(wm, h, "box", "B", (0.5, 0.6), 0.0, 0.0, start=branch)               # and the box within B
    later = branch + timedelta(hours=1)
    a = wm.where(h, "box", "A", later)
    assert (a["status"], a["judgement"]) == (Status.INFERRED, "single")       # inherited values are overridden
    assert a["candidates"][0]["x"] == pytest.approx((7.5, 7.6))
    assert wm.where(w, "box", "A", later)["candidates"][0]["x"] == pytest.approx((1.0, 1.0))
    assert wm.where(h, "box", "B", later)["status"] == Status.STIPULATED
    pos(wm, w, "crate", "A", 3.0, 0.0, 0.0, start=branch)                    # recorded in the base after the branch
    assert wm.where(h, "crate", "A", later)["status"] == Status.NOT_YET_KNOWN


# ---- part 4: the gearbox reference world -------------------------------------------------------------------------
@pytest.fixture(scope="module")
def ref(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=PHYSICAL_MODULES, clock=FakeClock())
    try:
        ids = g.extend_spatial(wm, g.build(wm))
        yield wm, ids
    finally:
        driver.databases.get(name).delete()


def test_gearbox_relative_to_the_workshop_and_a_component_relative_to_the_bench(ref):
    wm, ids = ref
    wm.selective = True
    w = ids["world"]
    gb = wm.where(w, "gbx-100", "f-workshop", g.AFTER)
    derived = next(c for c in gb["candidates"] if not c["direct"])
    assert derived["x"] == pytest.approx((3.6, 3.6)) and derived["y"] == pytest.approx((3.1, 3.1))
    assert [s["parent"] for s in derived["chain"]] == ["f-workshop"]
    assert (gb["status"], gb["judgement"], gb["alternatives"]) == (Status.ASSERTED, "compatible", (ids["tag_position"],))
    gear = wm.where(w, "gear-in", "f-bench", g.AFTER)
    (c,) = gear["candidates"]
    assert flat((c["x"], c["y"], c["z"])) == pytest.approx([0.62, 0.62, 0.46, 0.46, 1.0, 1.0])
    assert gear["incomparable"][0]["frame"] == "f-cam-2"                      # the camera's own frame is unrelated
    in_ws = wm.where(w, "gear-in", "f-workshop", g.AFTER)["candidates"][0]
    assert [s["child"] for s in in_ws["chain"]] == ["f-gearbox", "f-bench"]
    assert in_ws["x"] == pytest.approx((3.54, 3.54)) and in_ws["y"] == pytest.approx((3.12, 3.12))


def test_a_changed_transform_changes_derived_positions_only_where_it_applies(ref):
    wm, ids = ref
    w = ids["world"]
    later = wm.where(w, "gbx-100", "f-workshop", g.LATER)["candidates"][0]
    assert flat((later["x"], later["y"])) == pytest.approx([6.6, 6.6, 1.4, 1.4])
    assert later["chain"][0]["support"] == [ids["moved_transform"]]
    assert wm.where(w, "gear-in", "f-bench", g.LATER)["candidates"][0]["x"] == pytest.approx((0.62, 0.62))
    plan = wm.where(ids["bench_plan"], "gbx-100", "f-workshop", g.LATER)["candidates"][0]
    assert flat((plan["x"], plan["y"])) == pytest.approx([0.4, 0.4, 0.6, 0.6])   # the plan's 180 deg turn
    assert plan["chain"][0]["support"] == [ids["planned_transform"]]
    bench = wm.where(w, "bench-1", "f-gearbox", g.AFTER)["candidates"][0]     # an inverse chain, with ranges
    assert flat((bench["x"], bench["y"])) == pytest.approx([-0.65, -0.55, -0.45, -0.35])


def test_selective_and_full_load_agree_on_spatial_answers(ref):
    wm, ids = ref
    w = ids["world"]

    def answers():
        out = []
        for t in (g.BEFORE, g.AFTER, g.LATER):
            out += [wm.where(w, x, f, t) for x in ("gbx-100", "gear-in", "bench-1", "bearing-3")
                    for f in ("f-workshop", "f-bench", "f-gearbox")]
            out += [wm.transform_between(w, a, b, t) for a, b in (("f-gearbox", "f-workshop"), ("f-workshop", "f-cam-2"))]
        out += [wm.where(ids["bench_plan"], "gbx-100", "f-workshop", g.LATER),
                wm.where(w, "gbx-100", "f-workshop", g.AFTER, perspective="tag-reader")]
        return out

    wm.selective = True
    selective = answers()
    wm.selective = False
    try:
        assert answers() == selective
    finally:
        wm.selective = True
