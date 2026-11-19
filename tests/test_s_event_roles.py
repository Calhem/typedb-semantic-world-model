"""Increment D (DI-2; LABS-1.041/1.042 design, LABS-1.043 approval): event-role constraints.

Storage and migration (ER-7): the core-0.4-event-roles module, its explicit upgrade, and its atomicity and
idempotence. The semantics (ER-1 to ER-6) are tested in tests/test_s_occurrence_roles.py.

LABS-1.049 (DI-13): the profiles' current versions (organisation 0.3, mechanical 0.3, laboratory 0.2) open roles, so
they also need core-0.4-event-multiplicity; increment D's behaviour is kept and tested on the versions it shipped
(`PROFILE_01`, `PROFILE_02`), and upgrades walk from any earlier version. Multiplicity itself is tested in
tests/test_u_multiplicity.py.
"""

import dataclasses
import uuid

import pytest

import profile_fixtures as F
from conftest import FakeClock
from worldmodel import CORE_MODULES, PROFILES, ProfileError, WorldModel
from worldmodel import laboratory as lb, mechanical as mech, organisation as org
from worldmodel.model import EVENT_ROLES_MODULE, MULTIPLICITY_MODULE, PROFILE_BASE_MODULES
from worldmodel.profiles import schema_snapshot
from worldmodel.profiles import EventRole

pytestmark = pytest.mark.own_profiles


@pytest.fixture
def make(driver):
    made = []

    def _make(modules=CORE_MODULES):
        name = f"wm-test-{uuid.uuid4().hex[:10]}"
        made.append(name)
        return WorldModel.create(name, driver=driver, modules=modules, clock=FakeClock())
    yield _make
    for name in made:
        if driver.databases.contains(name):
            driver.databases.get(name).delete()


def entity_types(wm):
    from worldmodel import typeql as q
    with wm._reading() as tx:
        return {r.get("t").get_label() for r in q.rows(tx, "match entity $t;")}


def test_a_new_database_has_the_module_and_no_constraints(make):
    wm = make()
    assert EVENT_ROLES_MODULE in wm.modules() and "event-role-constraint" in entity_types(wm)
    assert MULTIPLICITY_MODULE in wm.modules()                     # LABS-1.049: new databases get it too
    assert wm.event_role_constraints() == {} and wm._event_constraints("event") == []


def test_upgrade_adds_the_module_once(make):
    wm = make(PROFILE_BASE_MODULES)                     # a database created before increment D
    assert EVENT_ROLES_MODULE not in wm.modules() and wm.event_role_constraints() == {}
    assert wm.upgrade_to_event_roles() is True
    assert EVENT_ROLES_MODULE in wm.modules() and "event-role-constraint" in entity_types(wm)
    before = wm.modules()
    assert wm.upgrade_to_event_roles() is False          # idempotent: nothing written
    assert wm.modules() == before


def test_upgrade_is_refused_without_the_rest_of_the_core(make):
    wm = make(("core", "core-0.4-a0"))
    with pytest.raises(ValueError, match="missing modules"):
        wm.upgrade_to_event_roles()
    assert EVENT_ROLES_MODULE not in wm.modules() and "event-role-constraint" not in entity_types(wm)


def test_a_failing_upgrade_leaves_nothing(make, monkeypatch):
    wm = make(PROFILE_BASE_MODULES)
    real = wm.install_module

    def install_then_fail(*a, **k):
        real(*a, **k)                                    # the schema and the module record are written ...
        raise RuntimeError("injected failure")           # ... then the operation fails before commit
    monkeypatch.setattr(wm, "install_module", install_then_fail)
    with pytest.raises(RuntimeError, match="injected"):
        wm.upgrade_to_event_roles()
    monkeypatch.undo()
    assert EVENT_ROLES_MODULE not in wm.modules() and "event-role-constraint" not in entity_types(wm)
    assert wm.upgrade_to_event_roles() is True           # and it can then be run normally


def test_a_database_without_the_module_still_installs_profiles_without_event_roles(make):
    wm = make(PROFILE_BASE_MODULES)
    assert wm.install_profile(lb.PROFILE_01)                  # laboratory 0.1: no event roles, no opened role
    assert "profile:laboratory" in wm.modules() and EVENT_ROLES_MODULE not in wm.modules()


@pytest.mark.parametrize("name", ["organisation", "mechanical"])
def test_installing_a_profile_with_event_roles_on_an_older_database_says_what_to_run(make, name):
    """Accepted under LABS-1.045: a database created before increment D must run upgrade_to_event_roles() before a
    first installation of organisation or mechanical 0.2; the refusal says so and writes nothing."""
    wm = make(PROFILE_BASE_MODULES)
    v02 = {"organisation": org, "mechanical": mech}[name].PROFILE_02
    before = (wm.modules(), entity_types(wm))
    with pytest.raises(ProfileError, match=r"run wm\.upgrade_to_event_roles\(\) first, then install the profile"):
        wm.install_profile(v02)
    assert (wm.modules(), entity_types(wm)) == before
    assert wm.upgrade_to_event_roles() is True and wm.install_profile(v02)
    assert wm.modules()[f"profile:{name}"] == "0.2" and wm.event_role_constraints()


@pytest.mark.parametrize("name", ["organisation", "mechanical", "laboratory"])
def test_installing_a_current_profile_on_an_older_database_names_both_upgrades(make, name):
    """LABS-1.049 (MP-5): the current versions open roles, so a database created before increment D must run both
    upgrades, in order; one created before LABS-1.049 only the multiplicity upgrade. Each refusal writes nothing."""
    wm = make(PROFILE_BASE_MODULES)
    before = (wm.modules(), entity_types(wm))
    with pytest.raises(ProfileError, match=r"run wm\.upgrade_to_event_roles\(\), then "
                                           r"wm\.upgrade_to_event_multiplicity\(\) first, then install the profile"):
        wm.install_profile(name)
    assert (wm.modules(), entity_types(wm)) == before
    wm.upgrade_to_event_roles()
    with pytest.raises(ProfileError, match=r"run wm\.upgrade_to_event_multiplicity\(\) first, then install"):
        wm.install_profile(name)
    assert wm.upgrade_to_event_multiplicity() is True and wm.install_profile(name)
    assert wm.modules()[f"profile:{name}"] == PROFILES[name].version


# ---- profile declarations (ER-1, ER-2, ER-6) ----------------------------------------------------------------------
def all_profiles(wm):
    for p in ("mechanical", "organisation", "laboratory"):
        wm.install_profile(p)
    return wm


def test_profiles_declare_the_approved_constraints(make):
    wm = all_profiles(make())
    assert wm.event_role_constraints() == {
        "official-act": [("actor", "organisation:co-signed", "profile:organisation", "set"),     # LABS-1.049, MP-4
                         ("actor", None, "profile:organisation", "one"),
                         ("office", None, "profile:organisation", "one"),
                         ("office-context", None, "profile:organisation", "one")],
        "replacement": [("fitted", "mechanical:one-for-one", "profile:mechanical", "one"),
                        ("patient", "mechanical:one-for-one", "profile:mechanical", "one")]}
    assert [c[1] for c in wm._event_constraints("official-act")] == ["actor", "actor", "office", "office-context"]
    assert wm._event_constraints("sampling") == [] and wm._event_constraints("event") == []   # never universal
    assert "mechanical:one-for-one" in state(wm)[1]


@pytest.mark.parametrize("declaration,why", [
    (EventRole("event", "actor"), "not an event type of this profile's own"),
    (EventRole("part-swap", "office"), "not one of its core roles"),
    (EventRole("part-swap", "patient", "mechanical-fixture:nowhere"), "not in the profile's vocabulary"),
])
def test_invalid_declarations_are_refused_and_nothing_is_installed(make, declaration, why):
    wm = make()
    bad = dataclasses.replace(F.MECHANICAL, event_roles=(declaration,))
    with pytest.raises(ProfileError, match=why):
        wm.install_profile(bad)
    assert bad.module not in wm.modules() and wm.event_role_constraints() == {}


def test_a_valid_fixture_declaration_is_inherited_by_name(make):
    wm = make()
    wm.install_profile(dataclasses.replace(F.MECHANICAL, event_roles=(EventRole("part-swap", "patient"),
                                                                      EventRole("part-swap", "actor"))))
    assert [c[1] for c in wm._event_constraints("part-swap")] == ["actor", "patient"]


# ---- upgrade_profile (ER-7) -----------------------------------------------------------------------------------------
def v01(name):
    """The profile as it was at 0.1 (before increment D): no event-role constraints, no one-for-one category, no
    opened role: the oldest version of its chain (LABS-1.049)."""
    return PROFILES[name].chain()[-1]


@pytest.fixture
def old(make):
    """A database as created before increment D: no event-role module, organisation and mechanical at 0.1."""
    wm = make(PROFILE_BASE_MODULES)
    wm.install_profile(v01("organisation"))
    wm.install_profile(v01("mechanical"))
    return wm


def state(wm):
    from worldmodel import typeql as q
    with wm._reading() as tx:
        cats = {q.opt(r, "id") for r in q.rows(tx, "match $c isa category, has wm-id $id;")}
    return wm.modules(), cats, (wm.event_role_constraints() if EVENT_ROLES_MODULE in wm.modules() else None)


def test_upgrade_profile_needs_the_core_module_first(old):
    before = state(old)
    assert old.upgrades_available() == {"event_roles_module": True, "multiplicity_module": True,
                                        "profiles": {"mechanical": ("0.1", "0.3"), "organisation": ("0.1", "0.3")}}
    with pytest.raises(ProfileError, match="upgrade_to_event_roles"):
        old.upgrade_profile("organisation")
    old.upgrade_to_event_roles()
    with pytest.raises(ProfileError, match="upgrade_to_event_multiplicity"):
        old.upgrade_profile("organisation")
    assert old.profiles() == {"organisation": "0.1", "mechanical": "0.1"} and state(old)[1] == before[1]


def upgrade_core(wm):
    assert wm.upgrade_to_event_roles() is True and wm.upgrade_to_event_multiplicity() is True


def test_upgrade_profile_adds_data_and_widens_roles_once(old):
    """From 0.1 to the current version in one step (LABS-1.049): data, and the profile's widening-only schema steps
    (no type, role, plays or owns changes)."""
    upgrade_core(old)
    with old._reading() as tx:
        snap_before = schema_snapshot(tx)
    assert old.upgrade_profile("organisation") is True and old.upgrade_profile("mechanical") is True
    modules, cats, constraints = state(old)
    assert (modules["profile:organisation"], modules["profile:mechanical"]) == ("0.3", "0.3")
    assert {"mechanical:one-for-one", "organisation:co-signed"} <= cats and len(sum(constraints.values(), [])) == 6
    with old._reading() as tx:
        assert schema_snapshot(tx) == snap_before                                   # no type, role, plays or owns
    assert old._schema_differences(PROFILES["organisation"]) == [] == old._schema_differences(PROFILES["mechanical"])
    again = state(old)
    assert old.upgrade_profile("organisation") is False and old.upgrade_profile("mechanical") is False
    assert state(old) == again and old.upgrades_available() == {"event_roles_module": False,
                                                                 "multiplicity_module": False, "profiles": {}}


def test_increment_d_versions_keep_working_and_upgrade_in_steps(old):
    """MP-5: a database may stay on increment D's versions; 0.1 -> 0.2 is data only, as before, and 0.2 -> 0.3
    later."""
    old.upgrade_to_event_roles()
    schema_before = old.driver.databases.get(old.database).schema()
    assert old.upgrade_profile(org.PROFILE_02) is True and old.upgrade_profile(mech.PROFILE_02) is True
    assert old.driver.databases.get(old.database).schema() == schema_before          # data only
    assert (old.profiles()["organisation"], old.profiles()["mechanical"]) == ("0.2", "0.2")
    old.upgrade_to_event_multiplicity()
    assert old.upgrade_profile("organisation") is True and old.profiles()["organisation"] == "0.3"


def test_upgrade_profile_refuses_another_installed_version(make):
    wm = make()
    wm.install_profile(dataclasses.replace(v01("organisation"), version="0.0-other"))
    with pytest.raises(ProfileError, match="upgrades only from 0.2, 0.1"):
        wm.upgrade_profile("organisation")
    assert wm.modules()["profile:organisation"] == "0.0-other" and wm.event_role_constraints() == {}


def test_upgrade_profile_refuses_a_schema_that_differs_from_the_files(old):
    from worldmodel.model import SCHEMA
    upgrade_core(old)
    with old.driver.transaction(old.database, SCHEMA) as tx:          # an annotation changed outside the profile
        tx.query("define relation official-act relates office @card(0..2);").resolve()
        tx.commit()
    before = state(old)
    with pytest.raises(ProfileError, match="differs from the profile's files"):
        old.upgrade_profile("organisation")
    assert state(old) == before


def test_upgrade_profile_refuses_a_conflicting_concept(old):
    upgrade_core(old)
    old.add_entity("social-role", "not a category", id="mechanical:one-for-one")
    before = state(old)
    with pytest.raises(ProfileError, match="exists as another concept"):
        old.upgrade_profile("mechanical")
    assert state(old) == before


def test_a_failing_profile_upgrade_leaves_nothing(old, monkeypatch):
    import worldmodel.profiles as profiles
    upgrade_core(old)
    schema_before = old.driver.databases.get(old.database).schema()
    before = state(old)
    real, calls = profiles._insert_event_role, []

    def insert_then_fail(*a, **k):
        real(*a, **k)
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("injected failure after two writes")
    monkeypatch.setattr(profiles, "_insert_event_role", insert_then_fail)
    with pytest.raises(RuntimeError, match="injected"):
        old.upgrade_profile("organisation")
    monkeypatch.undo()
    assert state(old) == before                                    # nothing kept: neither data nor the schema step
    assert old.driver.databases.get(old.database).schema() == schema_before
    assert old.upgrade_profile("organisation") is True


def test_a_database_not_upgraded_reads_as_before_until_upgraded(old):
    """Design 8.4 (LABS-1.044): the new code on a database created before increment D lists the new `accounts` and
    `roles` with no constraint and no judgement; the explicit upgrades then add the judgement and change no existing
    field of the view, and no account."""
    from datetime import datetime, timezone
    from worldmodel import organisation as org
    T5 = datetime(2026, 11, 5, 9, tzinfo=timezone.utc)
    w = old.create_world("actual", id="w")
    for p in ("bea", "cal", "hr", "clerk"):
        old.add_entity("person", p, id=p)
    old.add_entity("organisation", "depot", id="depot")
    old.add_entity("social-role", "site-manager", id="site-manager")
    old.add_entity("occurrence", "o-act", id="o-act")
    for official, attester in (("bea", "hr"), ("cal", "clerk")):
        e = org.act_in_office(old, w, official, "site-manager", "depot", T5, occurrence="o-act", attester=attester,
                              id=f"act-{attester}")
        for a in old.account_attestations(w, e):
            old.accept(a)
    before = old.occurrence("w", "o-act")
    assert sorted(a["description"] for a in before["accounts"]) == ["act-clerk", "act-hr"]
    assert {a["account"] for a in before["accounts"]} == {"accepted"}
    assert before["roles"]["official-act:official"]["players"] == {"bea": ["act-hr"], "cal": ["act-clerk"]}
    assert all(r["constraints"] == [] for r in before["roles"].values())          # nothing is judged
    upgrade_core(old)
    old.upgrade_profile("organisation")
    after = old.occurrence("w", "o-act")
    assert (after["descriptions"], after["participants"], after["accounts"]) == \
        (before["descriptions"], before["participants"], before["accounts"])
    official = after["roles"]["official-act:official"]
    assert official["players"] == before["roles"]["official-act:official"]["players"]
    assert [(c["role"], c["kind"], c["applies"], c["judgement"]) for c in official["constraints"]] == \
        [("actor", None, True, "disputed"), ("actor", "organisation:co-signed", False, None)]   # LABS-1.049
