"""Test fixtures. Live tests use a real TypeDB server (WM_TYPEDB_ADDRESS, default 127.0.0.1:1735, the isolated
`wm-typedb` container from environments/compose.yaml) and a throwaway database per test, deleted afterwards."""

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from worldmodel import WorldModel, connect


def T(hhmm, day=9):
    """Valid times in the test worlds: 2026-11-<day> hh:mm UTC."""
    h, m = map(int, hhmm.split(":"))
    return datetime(2026, 11, day, h, m, tzinfo=timezone.utc)


class FakeClock:
    """Deterministic transaction time: 2030-01-01 00:00 UTC, one second later on every call."""

    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


@pytest.fixture(scope="session")
def driver():
    d = connect()
    yield d
    leftovers = [db.name for db in d.databases.all() if db.name.startswith("wm-test-")]
    for name in leftovers:
        d.databases.get(name).delete()


@pytest.fixture
def wm(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    model = WorldModel.create(name, driver=driver, clock=FakeClock())
    model.selective = os.environ.get("WM_SELECTIVE", "1") != "0"     # WM_SELECTIVE=0 runs the full-load reference path
    try:
        yield model
    finally:
        driver.databases.get(name).delete()


AUTO_PROFILES = {"on": False}


def pytest_configure(config):
    config.addinivalue_line("markers", "own_profiles: the test installs profiles itself (no core-protection install)")


@pytest.fixture(autouse=True)
def _own_profiles(request):
    """Tests marked own_profiles test installation on a bare core, so the core-protection run leaves them alone."""
    if os.environ.get("WM_PROFILES") != "1":
        yield
        return
    AUTO_PROFILES["on"] = request.node.get_closest_marker("own_profiles") is None
    yield
    AUTO_PROFILES["on"] = True


@pytest.fixture(scope="session", autouse=True)
def core_protection():
    """WM_PROFILES=1 (LABS-1.022, core-protection run): every test database created with at least the Stage C core
    gets the rest of the core (core-0.4-d, LABS-1.023), the registered domain profiles (mechanical) and the three
    fixture profiles, before the test writes anything, so the whole suite checks that profile vocabulary changes no
    core answer. Off by default."""
    if os.environ.get("WM_PROFILES") != "1":
        yield
        return
    AUTO_PROFILES["on"] = True
    import profile_fixtures
    from worldmodel import PROFILES
    from worldmodel.model import CORE_MODULES, QUALITY_MODULES
    original = WorldModel.create.__func__

    def create(cls, database, *args, **kwargs):
        wm = original(cls, database, *args, **kwargs)
        modules = kwargs.get("modules", args[1] if len(args) > 1 else None)
        if AUTO_PROFILES["on"] and modules is not None and set(QUALITY_MODULES) <= set(modules) and not wm.profiles():
            for m in CORE_MODULES:
                if m not in wm.modules():
                    wm.install_module(m)
            for p in (*PROFILES.values(), *profile_fixtures.ALL):
                wm.install_profile(p)
        return wm
    WorldModel.create = classmethod(create)
    try:
        yield
    finally:
        WorldModel.create = classmethod(original)
