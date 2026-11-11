"""Core 0.4 Stage D-1 (LABS-1.023): dependency kinds (core) and the mechanical profile, on the gearbox world.

Typed dependencies never reinterpret untyped (historical) ones, which stay "unspecified"; dependency is not parthood;
connections are symmetric and timed; a replacement description names the removed and fitted parts apart, and its
acceptance establishes neither the occurrence nor the state change; perspective, knowledge time, valid time and
hypothetical worlds behave as for any content; both query paths agree.
"""

import uuid

import pytest

import profile_fixtures as F
from conftest import FakeClock
from worldmodel import CORE_MODULES, QUALITY_MODULES, ProfileError, WorldModel, mechanical as m
from worldmodel.examples import gearbox as g
from worldmodel.keys import proposition_key
from worldmodel.model import DEPENDENCY_KINDS, READ
from worldmodel import typeql as q
from worldmodel.semantics import Status

pytestmark = pytest.mark.own_profiles


def build(driver, chain=False):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    wm.install_profile("mechanical")
    ids = g.build(wm)
    if chain:
        ids = g.extend_qualities_agency(wm, g.extend_causality(wm, g.extend_dynamics(wm, g.extend_spatial(wm, ids))))
    else:
        ids = g.extend_dynamics(wm, ids)
    return wm, g.extend_mechanical(wm, ids)


@pytest.fixture(scope="module")
def ref(driver):
    wm, ids = build(driver)
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
def make(driver):
    made = []

    def _make(modules=CORE_MODULES):
        name = f"wm-test-{uuid.uuid4().hex[:10]}"
        made.append(name)
        return WorldModel.create(name, driver=driver, modules=modules, clock=FakeClock())
    yield _make
    for name in made:
        driver.databases.get(name).delete()


def deps(wm, w, x, t=g.AFTER, **kw):
    return [(d["dependee"], d["kind"]) for d in wm.direct_dependencies(w, x, t, **kw)]


# ---- installation and coexistence --------------------------------------------------------------------------------------
def test_installs_alone_and_with_the_fixtures_and_needs_the_full_core(make):
    alone = make()
    assert alone.install_profile("mechanical") == ["connected-to", "replacement"]
    assert alone.profile_status("mechanical") == "installed"
    together = make()
    for p in ("mechanical", *F.ALL):
        together.install_profile(p)
    assert set(together.profiles()) == {"mechanical", *(p.name for p in F.ALL)}
    stage_c = make(QUALITY_MODULES)                                   # a Stage C database: no core-0.4-d
    with pytest.raises(ProfileError, match="core-0.4-d"):
        stage_c.install_profile("mechanical")
    stage_c.install_module("core-0.4-d")                               # the upgrade path: add the module, then the profile
    assert stage_c.install_profile("mechanical") == ["connected-to", "replacement"]


def test_the_core_module_seeds_the_kinds_and_keeps_untyped_keys(make):
    wm = make()
    with wm.driver.transaction(wm.database, READ) as tx:
        seeded = sorted(q.opt(r, "i") for r in q.rows(tx, 'match $c isa category, has wm-id $i; $i like "^dependency:";'))
    assert seeded == sorted(DEPENDENCY_KINDS) and len(seeded) == 4
    untyped = proposition_key("depends-on", {"dependent": "a", "dependee": "b"}, {})
    assert untyped == "depends-on|dependee=b|dependent=a"                                  # no kind in the key
    assert untyped != proposition_key("depends-on", {"dependent": "a", "dependee": "b", "kind": "dependency:control"}, {})


# ---- typed and unspecified dependencies -------------------------------------------------------------------------------
def test_typed_dependencies_never_reinterpret_untyped_ones(world):
    wm, w, ids = world
    assert deps(wm, w, "output-shaft") == [("input-shaft", "dependency:functional"), ("input-shaft", "unspecified")]
    old = next(h for h in wm.history(w, "output-shaft") if h["attestation"] == ids["dependencies"]["untyped"])
    assert (old["attester"], old["roles"].get("kind"), old["state"]) == ("design-office", None, "accepted")
    assert wm.dependencies(w, "output-shaft", g.AFTER) == ["input-shaft"]                  # unchanged: any kind
    assert wm.dependencies(w, "output-shaft", g.AFTER, kind="dependency:functional") == ["input-shaft"]
    assert wm.dependencies(w, "output-shaft", g.AFTER, kind="dependency:physical") == []
    assert deps(wm, w, "output-shaft", as_of=ids["known_before_kinds"]) == [("input-shaft", "unspecified")]


def test_an_untyped_dependency_counts_as_no_kind(make):
    wm = make()
    w = wm.create_world("w", id="w")
    for i in ("pump", "motor"):
        wm.add_entity("physical-object", i, id=i)
    wm.depend(w, "pump", "motor", start=g.T0)
    assert deps(wm, w, "pump") == [("motor", "unspecified")]
    assert wm.dependencies(w, "pump", g.AFTER) == ["motor"]
    for kind in DEPENDENCY_KINDS:
        assert wm.dependencies(w, "pump", g.AFTER, kind=kind) == []


def test_every_core_kind_and_kind_filtered_closure(world):
    wm, w, ids = world
    assert deps(wm, w, "gear-in") == [("input-shaft", "dependency:physical")]
    assert deps(wm, w, "gbx-100") == [("manual-gbx", "dependency:informational")]
    assert deps(wm, w, "test-rig") == [("rig-controller", "dependency:control")]
    assert wm.dependencies(w, "test-rig", g.AFTER, kind="dependency:functional") == []


def test_dependency_is_not_parthood(world):
    wm, w, ids = world
    assert "input-shaft" not in wm.parts(w, "gear-in", g.AFTER)                            # gear-in depends on it ...
    assert "gear-in" in wm.parts(w, "shaft-asm-in", g.AFTER)                               # ... and both are parts
    assert "shaft-asm-in" not in wm.dependencies(w, "gear-in", g.AFTER)
    assert all(c["other"] != "shaft-asm-in" for c in m.connections(wm, w, "gear-in", g.AFTER))


# ---- connections -------------------------------------------------------------------------------------------------------
def test_connections_are_symmetric_typed_and_timed(world):
    wm, w, ids = world
    one = [(c["other"], c["joint_kind"]) for c in m.connections(wm, w, "gear-in", g.AFTER)]
    other = [(c["other"], c["joint_kind"]) for c in m.connections(wm, w, "input-shaft", g.AFTER)]
    assert one == [("input-shaft", "mechanical:splined")]
    assert ("gear-in", "mechanical:splined") in other
    before = {c["other"] for c in m.connections(wm, w, "input-shaft", g.BEFORE)}
    after = {c["other"] for c in m.connections(wm, w, "input-shaft", g.AFTER)}
    assert "bearing-1" in before and "bearing-3" not in before
    assert "bearing-3" in after and "bearing-1" not in after


# ---- replacement ---------------------------------------------------------------------------------------------------------
def test_replacement_roles_distinguish_removed_and_fitted(world):
    wm, w, ids = world
    content = wm.content("ev-cmms-replacement")
    assert (content["roles"]["removed"], content["roles"]["fitted"]) == (["bearing-1"], ["bearing-3"])
    assert (wm.core_role("replacement:removed"), wm.core_role("replacement:fitted")) == ("patient", "fitted")
    for part in ("bearing-1", "bearing-3"):
        assert "ev-cmms-replacement" in {e["event"] for e in wm.events(w, participant=part)}


def test_an_accepted_replacement_account_does_not_establish_the_occurrence(world):
    wm, w, ids = world
    r = m.replacement(wm, w, "ev-cmms-replacement", g.AFTER)
    assert (r["account"], r["removed"], r["fitted"]) == ("accepted", ["bearing-1"], ["bearing-3"])
    (occ,) = r["occurrences"]
    own = wm.occurrence_status(w, "o-bearing-replacement", g.REPLACEMENT[0], details=False)["status"]
    assert occ == {"occurrence": "o-bearing-replacement", "status": own}
    assert own == "not established"                       # no existence attestation for the occurrence
    effects = {(e["kind"], e["outcome"]["part"][0]): e for e in r["effects"]}
    assert effects[("terminates", "bearing-1")]["claim"] == "accepted"
    assert (effects[("terminates", "bearing-1")]["before"], effects[("terminates", "bearing-1")]["after"]) == (True, False)
    # nothing says where bearing-3 was before: UNKNOWN (None), not false; it is part of the assembly afterwards
    assert (effects[("initiates", "bearing-3")]["before"], effects[("initiates", "bearing-3")]["after"]) == (None, True)
    assert all(e["accepted_change"] for e in r["effects"])          # judged from the states, not from the claims


def test_historical_state_before_and_after_the_replacement(world):
    wm, w, ids = world
    whole = {"whole": "shaft-asm-in"}
    assert wm.holds(w, "part-of", {"part": "bearing-1", **whole}, g.BEFORE).holds is True
    assert wm.holds(w, "part-of", {"part": "bearing-1", **whole}, g.AFTER).holds is False
    assert wm.holds(w, "part-of", {"part": "bearing-3", **whole}, g.AFTER).holds is True


# ---- perspectives, knowledge time, hypothetical worlds ----------------------------------------------------------------
def test_perspectives_disagree_about_the_replacement_and_a_dependency(world):
    wm, w, ids = world
    sys_view = m.replacement(wm, w, "ev-inspector-replacement", g.AFTER)
    own = m.replacement(wm, w, "ev-inspector-replacement", g.AFTER, perspective="inspector")
    assert (sys_view["account"], own["account"], own["removed"]) == ("not accepted", "accepted", ["bearing-2"])
    assert {e["before"] for e in sys_view["effects"]} == {None}      # no accepted account: no state judged around it
    assert ("bearing-2", "dependency:functional") in deps(wm, w, "gear-out")
    assert ("bearing-2", "dependency:functional") not in deps(wm, w, "gear-out", perspective="inspector")
    key = {"dependent": "gear-out", "dependee": "bearing-2", "kind": "dependency:functional"}
    assert wm.holds(w, "depends-on", key, g.AFTER, perspective="inspector").holds is False
    wm.accept(ids["dependency_denial"])
    try:
        assert wm.holds(w, "depends-on", key, g.AFTER).status == Status.DISPUTED
        assert [d["status"] for d in wm.direct_dependencies(w, "gear-out", g.AFTER)
                if d["dependee"] == "bearing-2"] == [Status.DISPUTED]
    finally:
        wm.accept(ids["dependency_denial"], verdict="retracted")


def test_a_disputed_connection_is_listed_as_disputed_not_dropped(make):
    wm = make()
    wm.install_profile("mechanical")
    w = wm.create_world("w", id="w")
    for i in ("a", "b"):
        wm.add_entity("physical-object", i, id=i)
    wm.add_entity("social-object", "Auditor", id="auditor")
    m.connect(wm, w, "a", "b", "mechanical:bolted", start=g.T0)
    denial = wm.deny(w, "connected-to", {"endpoint": ["a", "b"], "joint-kind": "mechanical:bolted"}, start=g.T0,
                     until_superseded=True, attester="auditor")
    assert [(c["other"], c["status"]) for c in m.connections(wm, w, "a", g.AFTER)] == [("b", Status.ASSERTED)]
    assert m.connections(wm, w, "a", g.AFTER, perspective="auditor") == []          # its own denial: not connected
    wm.accept(denial)
    assert [(c["other"], c["status"]) for c in m.connections(wm, w, "b", g.AFTER)] == [("a", Status.DISPUTED)]


def test_hypothetical_control_upgrade_stays_in_its_world(world):
    wm, w, ids = world
    plan, later = ids["plan_rig_control"], g.PROFILE_AT.replace(hour=12)
    assert deps(wm, plan, "test-rig", later) == [("plc-2", "dependency:control"), ("rig-controller", "dependency:control")]
    assert deps(wm, plan, "test-rig", g.AFTER) == [("rig-controller", "dependency:control")]   # before the upgrade
    assert deps(wm, w, "test-rig", later) == [("rig-controller", "dependency:control")]
    assert [d["status"] for d in wm.direct_dependencies(plan, "test-rig", later) if d["dependee"] == "plc-2"] == \
        [Status.STIPULATED]


# ---- compatibility -------------------------------------------------------------------------------------------------------
def test_the_full_reference_chain_composes_with_the_profile(driver):
    wm, ids = build(driver, chain=True)
    try:
        w = ids["world"]
        assert m.replacement(wm, w, "ev-cmms-replacement", g.AFTER)["account"] == "accepted"
        assert wm.capable(w, "technician", "can-replace-bearing", g.T1, "workshop")["judgement"] == "established"
        assert [p["relation"] for p in wm.compare_measurements(w, "housing", "mass", g.AFTER)["pairs"]] == \
            ["possibly compatible"]
    finally:
        driver.databases.get(wm.database).delete()


def test_core_queries_are_unaffected_by_the_profile_vocabulary(world):
    wm, w, ids = world
    assert {"shaft-asm-in", "housing", "bearing-3"} <= set(wm.parts(w, "gbx-100", g.AFTER))      # transitive parts
    assert set(wm.parts(w, "shaft-asm-in", g.AFTER)) == {"input-shaft", "gear-in", "bearing-3"}
    assert wm.value_of(w, "has-quality", {"bearer": "gbx-100", "quality": "condition"}, g.AFTER).values == \
        ("operational",)


def test_selective_and_full_load_agree(world):
    wm, w, ids = world

    def answers():
        return [wm.direct_dependencies(w, x, g.AFTER, perspective=p) for x in ("output-shaft", "gear-out")
                for p in ("system", "inspector")] + \
               [wm.dependencies(w, "output-shaft", g.AFTER, kind="dependency:functional"),
                m.connections(wm, w, "input-shaft", g.BEFORE), m.connections(wm, w, "input-shaft", g.AFTER),
                m.replacement(wm, w, "ev-cmms-replacement", g.AFTER),
                m.replacement(wm, w, "ev-inspector-replacement", g.AFTER, perspective="inspector"),
                wm.direct_dependencies(ids["plan_rig_control"], "test-rig", g.PROFILE_AT.replace(hour=12))]
    wm.selective = True
    a = answers()
    wm.selective = False
    assert answers() == a
