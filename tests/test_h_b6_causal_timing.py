"""LABS-1.016: the approved Stage B causal rule. An event cannot explain a transition that certainly precedes the start
of its occurrence. Occurrence time (the event's accepted occurrence interval) is used, never the time the account was
recorded. Where the occurrence time is uncertain or unavailable, applicability is reported as unresolved, not rejected.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from conftest import FakeClock
from worldmodel import DYNAMICS_MODULES, WorldModel


def T(h, m=0):
    return datetime(2026, 11, 9, h, m, tzinfo=timezone.utc)


@pytest.fixture
def space(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=DYNAMICS_MODULES, clock=FakeClock())
    try:
        w = wm.create_world("actual", id="actual")
        for kind, n in (("physical-object", "box"), ("place", "a"), ("place", "b"), ("physical-object", "tech"),
                        ("social-object", "log")):
            wm.add_entity(kind, n, id=n)
        wm.attest(w, "located-at", {"located": "box", "place": "a"}, start=T(8), end=T(10))
        wm.attest(w, "located-at", {"located": "box", "place": "b"}, start=T(10), until_superseded=True)
        yield wm, w
    finally:
        driver.databases.get(name).delete()


def explain(wm, w, **kw):
    (tr,) = [t for t in wm.changes(w, "box", T(9), T(11), **kw)["transitions"] if t["category"] == "world-state"]
    return {e["event"]: e for e in tr["explanations"]}


def claim(wm, w, eid, start, end=None, attester="system", accept=True):
    e = wm.account(w, {"actor": "tech", "patient": "box"}, start, end, id=eid, attester=attester)
    for a in wm.account_attestations(w, e, attester=attester) if accept and attester != "system" else []:
        wm.accept(a)
    c = wm.claim_effect(w, e, "initiates", "located-at", {"located": "box", "place": "b"}, attester=attester)
    if accept and attester != "system":
        wm.accept(c)
    return e


def test_an_event_cannot_explain_a_transition_that_certainly_precedes_it(space):
    wm, w = space
    claim(wm, w, "ev-before", T(9, 30), T(9, 50))
    claim(wm, w, "ev-after", T(10, 30), T(10, 45))
    got = explain(wm, w)
    assert set(got) == {"ev-before"} and got["ev-before"]["timing"] == "consistent"


def test_occurrence_time_not_record_time(space):
    wm, w = space
    # recorded long after the transition (transaction time), but it says the move happened at 09:40 (valid time)
    claim(wm, w, "ev-logged-late", T(9, 40), T(9, 55), attester="log")
    got = explain(wm, w)
    assert got["ev-logged-late"]["timing"] == "consistent"
    assert wm.clock.now > T(11)                                  # recorded after the transition, by transaction time


def test_uncertain_occurrence_time_is_unresolved_not_rejected(space):
    wm, w = space
    claim(wm, w, "ev-uncertain", (T(9, 50), T(10, 20)), T(10, 25))   # may have started before or after 10:00
    got = explain(wm, w)
    assert got["ev-uncertain"]["timing"] == "unresolved"


def test_unavailable_occurrence_time_is_unresolved_not_rejected(space):
    wm, w = space
    e = wm.describe_event({"actor": "tech", "patient": "box"}, id="ev-no-account")   # no accepted account of it
    wm.claim_effect(w, e, "initiates", "located-at", {"located": "box", "place": "b"})
    got = explain(wm, w)
    assert got["ev-no-account"]["timing"] == "unresolved" and got["ev-no-account"]["start"] is None
