"""Increment D (DI-2; LABS-1.041/1.042 design, LABS-1.043 approval): event-role constraints.

Storage and migration (ER-7): the core-0.4-event-roles module, its explicit upgrade, and its atomicity and
idempotence. The semantics (ER-1 to ER-6) are tested in tests/test_s_occurrence_roles.py.
"""

import uuid

import pytest

from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel
from worldmodel.model import EVENT_ROLES_MODULE, PROFILE_BASE_MODULES

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
    assert wm.install_profile("laboratory")
    assert "profile:laboratory" in wm.modules() and EVENT_ROLES_MODULE not in wm.modules()
