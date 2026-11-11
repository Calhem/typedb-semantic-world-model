"""Core 0.4 Stage D groundwork (LABS-1.022): profile packaging and subtype-aware generic APIs (D-D-6, D-D-9, D-D-10).

Profiles install alone or together, in any order, over the full core; anything but additive vocabulary of their own is
refused before commit; core answers are unchanged by installing them; roles_of, account_attestations and
process_steps recognise profile subtypes at any depth, with perspective, world, knowledge time and valid time intact.
"""

import uuid
from datetime import datetime, timezone

import pytest

import profile_fixtures as F
from conftest import FakeClock
from worldmodel import CORE_MODULES, Profile, ProfileError, WorldModel
from worldmodel.model import DEFAULT_MODULES
from worldmodel.examples import gearbox
from worldmodel.model import READ
from worldmodel.profiles import schema_snapshot


pytestmark = pytest.mark.own_profiles          # these tests install profiles themselves, on a bare core


def T(day, h=9):
    return datetime(2026, 11, day, h, 0, tzinfo=timezone.utc)


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


def snapshot(wm):
    with wm.driver.transaction(wm.database, READ) as tx:
        return schema_snapshot(tx)


# ---- installation ------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("profile", F.ALL, ids=lambda p: p.name)
def test_each_profile_installs_alone_over_the_full_core(make, profile):
    wm = make()
    before = snapshot(wm)
    assert wm.install_profile(profile) == F.NEW_TYPES[profile.name]
    assert wm.profiles() == {profile.name: profile.version}
    after = snapshot(wm)
    assert after["types"] - before["types"] == set(F.NEW_TYPES[profile.name])
    assert before["types"] <= after["types"] and before["relates"] <= after["relates"]   # nothing removed
    core_owns = {(t, a) for t, a in after["owns"] if t in before["types"]}
    assert core_owns == set(before["owns"])                                               # core types gain nothing
    w = wm.create_world("w", id="w")                                                      # core queries still work
    wm.add_entity("physical-object", "x", id="x")
    wm.add_entity("category", "c", id="c")
    wm.attest(w, "classified-as", {"classified": "x", "class": "c"}, start=T(1), until_superseded=True)
    assert [f["type"] for f in wm.facts_about(w, "x", T(2))] == ["classified-as"]


def test_all_profiles_install_together_in_any_order(make):
    one, two = make(), make()
    for p in F.ALL:
        one.install_profile(p)
    for p in reversed(F.ALL):
        two.install_profile(p)
    assert snapshot(one) == snapshot(two)                                                 # same schema ...
    assert one.slots() == two.slots() and one.profiles() == two.profiles()                # ... slots, records
    for label in ("acting-appointment", "protocol-step-of", "scheduled-maintenance-kind", "core-sample", "sampling"):
        assert one.ancestors(label) == two.ancestors(label)                               # ... and lattice


BAD = {
    "redeclares a core type": "define entity place sub particular;",
    "adds a role to a core relation": "define relation depends-on, relates kind; category plays depends-on:kind;",
    "adds an attribute to a core type": "define attribute badge, value string; physical-object owns badge;",
    "lets a core type play a core role": "define entity widget sub physical-object; spatial-frame plays member-of:member;",
    "is rejected by TypeDB itself": "define entity widget sub physical-object; spatial-frame plays part-of:part;",
    "specialises one core role twice": """define relation swap sub event, relates out-part as patient,
        relates in-part as patient; physical-object plays swap:out-part, plays swap:in-part;""",
}


@pytest.mark.parametrize("why", BAD)
def test_non_additive_profiles_are_refused_before_commit(make, tmp_path, why):
    wm = make()
    f = tmp_path / "bad.tql"
    f.write_text(BAD[why])
    before, modules = snapshot(wm), wm.modules()
    with pytest.raises(ProfileError, match="refused"):
        wm.install_profile(Profile("bad", "1", (str(f),)))
    assert snapshot(wm) == before and wm.modules() == modules


def test_slots_on_core_predicates_and_unprefixed_vocabulary_are_refused(make, tmp_path):
    wm = make()
    f = tmp_path / "p.tql"
    f.write_text("define relation sitting sub classified-as;")
    before = snapshot(wm)
    with pytest.raises(ProfileError, match="does not own"):
        wm.install_profile(Profile("p", "1", (str(f),), slots=(("classified-as", ("class",), "classified"),)))
    with pytest.raises(ProfileError, match="must start with"):
        wm.install_profile(Profile("p", "1", (str(f),), vocabulary=(("category", "overhaul", "overhaul"),)))
    assert snapshot(wm) == before


def test_collisions_between_profiles_are_refused_not_merged(make, tmp_path):
    wm = make()
    wm.install_profile(F.ORGANISATION)
    f = tmp_path / "hr.tql"
    f.write_text("define entity person sub physical-object; entity contractor sub physical-object;")
    before = snapshot(wm)
    with pytest.raises(ProfileError, match="redeclares existing types \\['person'\\]"):
        wm.install_profile(Profile("hr", "1", (str(f),)))
    assert snapshot(wm) == before and set(wm.profiles()) == {"organisation-fixture"}


def test_no_implicit_cross_profile_dependency(make, tmp_path):
    """A profile that relies on another profile's types fails on its own, so a dependency cannot hide."""
    wm = make()
    f = tmp_path / "payroll.tql"
    f.write_text("define relation payslip sub proposition, relates payee; person plays payslip:payee;")
    before = snapshot(wm)
    with pytest.raises(Exception):                                   # TypeDB: `person` is not defined
        wm.install_profile(Profile("payroll", "1", (str(f),)))
    assert snapshot(wm) == before


def test_profiles_need_the_full_core_and_are_never_replaced(make):
    with pytest.raises(ProfileError, match="full core"):
        make(DEFAULT_MODULES).install_profile(F.LABORATORY)
    wm = make()
    wm.install_profile(F.LABORATORY)
    assert wm.install_profile(F.LABORATORY) == []                    # the same version: a no-op
    with pytest.raises(ProfileError, match="never replaced"):
        wm.install_profile(Profile(F.LABORATORY.name, "0.1", F.LABORATORY.schema))


# ---- core semantics unchanged ------------------------------------------------------------------------------------------
def test_installing_profiles_changes_no_core_answer(make):
    wm = make()
    ids = gearbox.extend_qualities_agency(wm, gearbox.extend_causality(
        wm, gearbox.extend_dynamics(wm, gearbox.extend_spatial(wm, gearbox.build(wm)))))
    w, t = ids["world"], gearbox.AFTER

    def answers():
        return {
            "facts": wm.facts_about(w, "housing", t), "roles": wm.roles_of(w, "apprentice", gearbox.T1),
            "capable": wm.capable(w, "technician", "can-replace-bearing", gearbox.T1, "workshop"),
            "steps": wm.process_steps(w, "o-repair", t),
            "account": wm.account_attestations(w, "ev-worklog-replacement"),
            "compare": wm.compare_measurements(w, "housing", "mass", t),
            "where": wm.where(w, "gear-in", "f-workshop", t), "changes": wm.changes(w, "gbx-100", gearbox.REPAIR[0], t),
        }
    before = answers()
    for p in F.ALL:
        wm.install_profile(p)
    assert answers() == before


# ---- subtype-aware generic APIs (D-D-10) -----------------------------------------------------------------------------
@pytest.fixture(scope="module")
def world(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    try:
        for p in F.ALL:
            wm.install_profile(p)
        w = wm.create_world("w", id="w")
        wm.add_entity("person", "Bea", id="bea")
        wm.add_entity("organisation", "Acme", id="acme")
        wm.add_entity("place", "Depot 7", id="depot-7")
        for r in ("analyst", "deputy"):
            wm.add_entity("social-role", r, id=r)
        site = "organisation-fixture:site-manager"
        ids = {"w": w, "site": site}
        ids["analyst"] = wm.attest(w, "classified-as", {"classified": "bea", "class": "analyst", "context": "depot-7"},
                                   start=T(1), until_superseded=True)                       # a core classification
        ids["office"] = wm.attest(w, "office-holding", {"classified": "bea", "class": site, "context": "depot-7"},
                                  start=T(2), end=T(8))                                      # a profile subtype
        known = wm.clock.now
        ids["acting"] = wm.attest(w, "acting-appointment", {"classified": "bea", "class": "deputy",
                                                             "context": "acme"}, start=T(3), until_superseded=True,
                                  attester="acme")                                           # deeper; acme's claim
        ids["known_before_acting"] = known
        # an account classified through a core type and two profile subtypes, linked to an occurrence
        wm.add_entity("physical-object", "Pump", id="pump")
        wm.add_entity("occurrence", "service", id="o-service")
        for c in ("service", "overhaul-plan"):
            wm.add_entity("category", c, id=c)
        ids["event"] = wm.account(w, {"actor": "bea", "patient": "pump"}, T(4), kind="service",
                                  occurrence="o-service", id="ev-service")
        ids["kind"] = wm.attest(w, "maintenance-kind", {"classified": "ev-service", "class": "mechanical-fixture:overhaul"},
                                until_superseded=True)
        ids["sched"] = wm.attest(w, "scheduled-maintenance-kind", {"classified": "ev-service",
                                                                   "class": "overhaul-plan"},
                                 until_superseded=True, attester="acme")
        # an experiment whose steps are linked through part-of and two profile subtypes
        for o in ("o-experiment", "o-prep", "o-run", "o-readout", "o-old"):
            wm.add_entity("occurrence", o, id=o)
        for step, rel, kw in (("o-prep", "part-of", {"until_superseded": True}),
                              ("o-run", "step-of", {"until_superseded": True}),
                              ("o-readout", "protocol-step-of", {"until_superseded": True}),
                              ("o-old", "step-of", {"end": T(2)})):                         # ended before t
            wm.attest(w, rel, {"part": step, "whole": "o-experiment"}, start=T(1), **kw)
        ids["plan"] = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(5), id="plan")
        yield wm, ids
    finally:
        driver.databases.get(name).delete()


def roles(wm, w, t, **kw):
    return sorted((r["role"], r["context"]) for r in wm.roles_of(w, "bea", t, **kw))


def test_lattice_handles_deeper_hierarchies(world):
    wm, _ = world
    assert wm.ancestors("acting-appointment")[:3] == ["acting-appointment", "office-holding", "classified-as"]
    assert wm.core_type("core-sample") == "physical-object" and wm.core_type("protocol-step-of") == "part-of"
    assert wm.is_a_any("scheduled-maintenance-kind", ("describes", "classified-as"))
    assert not wm.is_a_any("step-of", ("classified-as", "describes"))


def test_roles_of_recognises_profile_subtypes_with_judgement_intact(world):
    wm, ids = world
    w, site = ids["w"], ids["site"]
    assert roles(wm, w, T(5)) == [("analyst", "depot-7"), (site, "depot-7")]               # acme's claim: unreviewed
    assert roles(wm, w, T(5), perspective="acme") == [("deputy", "acme")]                   # acme sees its own only
    wm.accept(ids["acting"])
    try:
        assert roles(wm, w, T(5)) == [("analyst", "depot-7"), ("deputy", "acme"), (site, "depot-7")]
        assert roles(wm, w, T(9)) == [("analyst", "depot-7"), ("deputy", "acme")]           # the office ended (valid time)
        assert roles(wm, w, T(5), as_of=ids["known_before_acting"]) == [("analyst", "depot-7"), (site, "depot-7")]
        # the plan's snapshot was taken before this acceptance, so it inherits the earlier view (knowledge time)
        assert roles(wm, ids["plan"], T(4)) == [("analyst", "depot-7"), (site, "depot-7")]
        assert roles(wm, w, T(1, 8)) == []                                                   # before everything
    finally:
        wm.accept(ids["acting"], verdict="retracted")


def test_the_office_slot_is_inherited_by_a_deeper_subtype(make):
    wm = make()
    wm.install_profile(F.ORGANISATION)
    w = wm.create_world("w", id="w")
    for p in ("bea", "cal"):
        wm.add_entity("person", p, id=p)
    wm.add_entity("place", "Depot 7", id="depot-7")
    site = "organisation-fixture:site-manager"
    wm.attest(w, "office-holding", {"classified": "bea", "class": site, "context": "depot-7"}, start=T(1),
              until_superseded=True)
    wm.attest(w, "acting-appointment", {"classified": "cal", "class": site, "context": "depot-7"}, start=T(2),
              until_superseded=True)                                       # accepted: the system's own attestations
    got = wm.value_of(w, "office-holding", {"class": site, "context": "depot-7"}, T(3))
    assert (got.status.value, got.values) == ("DISPUTED", ("bea", "cal"))   # judged, not refused at write (D-D-5)


def test_account_attestations_recognise_profile_subtypes(world):
    wm, ids = world
    w = ids["w"]
    every = wm.account_attestations(w, "ev-service")
    assert {ids["kind"], ids["sched"]} <= set(every)                       # both profile subtypes now included
    by_system = wm.account_attestations(w, "ev-service", attester="system")
    assert ids["kind"] in by_system and ids["sched"] not in by_system      # the attester filter still applies
    assert len(by_system) == 4                                             # account, core kind, describes, profile kind
    assert ids["sched"] not in wm.account_attestations(w, "ev-service", as_of=ids["known_before_acting"])


def test_process_steps_recognise_profile_subtypes(world):
    wm, ids = world
    steps = [s["occurrence"] for s in wm.process_steps(ids["w"], "o-experiment", T(5))]
    assert sorted(steps) == ["o-prep", "o-readout", "o-run"]                # core, subtype, deeper; o-old ended
    assert "o-old" in [s["occurrence"] for s in wm.process_steps(ids["w"], "o-experiment", T(1, 12))]
    assert sorted(s["occurrence"] for s in wm.process_steps(ids["plan"], "o-experiment", T(5))) == sorted(steps)


def test_profile_events_and_core_events_keep_their_cardinality(world):
    wm, ids = world
    w = ids["w"]
    for i in ("b1", "b3", "tool"):
        wm.add_entity("physical-object", i, id=i)
    rep = wm.account(w, {"actor": "bea", "swapped-out": "b1", "swapped-in": "b3"}, T(6), type="part-swap", id="ev-rep")
    assert wm.content(rep)["roles"] == {"actor": ["bea"], "swapped-out": ["b1"], "swapped-in": ["b3"]}
    core = wm.account(w, {"actor": "bea", "patient": "b1", "instrument": "tool"}, T(6), id="ev-core")
    assert set(wm.content(core)["roles"]) == {"actor", "patient", "instrument"}
    assert {e["event"] for e in wm.events(w, participant="b1")} >= {"ev-rep", "ev-core"}


def test_selective_and_full_load_agree(world):
    wm, ids = world
    w = ids["w"]

    def answers():
        return [wm.roles_of(w, "bea", T(5)), wm.roles_of(w, "bea", T(5), perspective="acme"),
                wm.account_attestations(w, "ev-service"), wm.process_steps(w, "o-experiment", T(5))]
    wm.selective = True
    a = answers()
    wm.selective = False
    try:
        assert answers() == a
    finally:
        wm.selective = True


# ---- atomic installation (LABS-1.023) ----------------------------------------------------------------------------------
def _assert_untouched(wm, before, profile):
    assert snapshot(wm) == before                                   # no type of the profile was committed
    assert profile.name not in wm.profiles()                         # never reported as installed
    assert wm.profile_status(profile) == "absent"


def test_a_failure_while_writing_vocabulary_rolls_back_the_schema(make):
    wm = make()
    wm.add_entity("social-role", "already here", id="organisation-fixture:site-manager")   # the profile's seed id
    before = snapshot(wm)
    with pytest.raises(ProfileError, match="nothing committed"):
        wm.install_profile(F.ORGANISATION)
    _assert_untouched(wm, before, F.ORGANISATION)
    with wm.driver.transaction(wm.database, READ) as tx:
        from worldmodel import typeql as q
        assert not q.rows(tx, 'match $s isa functional-slot, has slot-predicate "office-holding";')   # no slot row


def test_an_invalid_slot_is_refused_before_anything_is_written(make):
    wm = make()
    bad = Profile(F.ORGANISATION.name, "0.0-test", F.ORGANISATION.schema,
                  slots=(("office-holding", ("class", "nowhere"), "classified"),))
    before = snapshot(wm)
    with pytest.raises(ProfileError, match="invalid slot"):
        wm.install_profile(bad)
    _assert_untouched(wm, before, bad)


def test_a_failure_at_commit_installs_nothing(make, monkeypatch):
    wm = make()
    from worldmodel.model import SCHEMA
    from typedb.driver import TypeDBDriverException
    driver = wm.driver
    before = snapshot(wm)

    class FailingCommit:
        def __init__(self, tx):
            self._tx = tx

        def __enter__(self):
            self._tx.__enter__()
            return self

        def __exit__(self, *exc):
            return self._tx.__exit__(*exc)

        def commit(self):
            raise TypeDBDriverException("injected commit failure")

        def __getattr__(self, name):
            return getattr(self._tx, name)

    class Driver:
        databases = driver.databases

        def transaction(self, database, kind):
            tx = driver.transaction(database, kind)
            return FailingCommit(tx) if kind == SCHEMA else tx
    monkeypatch.setattr(wm, "driver", Driver())
    with pytest.raises(Exception, match="injected commit failure|nothing committed"):
        wm.install_profile(F.LABORATORY)
    monkeypatch.undo()
    _assert_untouched(wm, before, F.LABORATORY)


def test_schema_changed_outside_install_profile_is_a_conflict(make):
    wm = make()
    from worldmodel.model import SCHEMA
    with wm.driver.transaction(wm.database, SCHEMA) as tx:          # a manual define of one of the profile's types
        tx.query("define entity sample sub physical-object;").resolve()
        tx.commit()
    assert wm.profile_status(F.LABORATORY) == "conflict" and "laboratory-fixture" not in wm.profiles()
    with pytest.raises(ProfileError, match="redeclares existing types \\['sample'\\]"):
        wm.install_profile(F.LABORATORY)
    assert wm.profile_status(F.LABORATORY) == "conflict"
