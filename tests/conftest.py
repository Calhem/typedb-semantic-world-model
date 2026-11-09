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
