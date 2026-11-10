"""Core 0.4 Stage B1 (LABS-1.010): events and state transitions in the gearbox reference world.

Occurrences vs descriptions, claimed effects (initiates / terminates) vs accepted state changes, what changed, when
and according to whom, temporal order, knowledge time, perspectives, hypothetical snapshots and query-path
equivalence.
"""

import uuid
from datetime import timedelta

import pytest

from conftest import FakeClock
from worldmodel import DYNAMICS_MODULES, WorldModel
from worldmodel.examples import gearbox as g
from worldmodel.model import READ
from worldmodel.semantics import Status

COND = {"bearer": "gbx-100", "quality": "condition"}


@pytest.fixture(scope="module")
def ref(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=DYNAMICS_MODULES, clock=FakeClock())
    try:
        yield wm, g.extend_dynamics(wm, g.build(wm))
    finally:
        driver.databases.get(name).delete()


@pytest.fixture
def world(ref):
    wm, ids = ref
    wm.selective = True
    yield wm, ids["world"], ids
    wm.selective = True


def condition(wm, w, t, **kw):
    a = wm.value_of(w, "has-quality", COND, t, **kw)        # the (bearer, quality) -> value constraint of this world
    return a.status, a.values


def test_an_occurrence_is_an_identity_and_descriptions_are_accounts_of_it(world):
    wm, w, _ = world
    with wm.driver.transaction(wm.database, READ) as tx:
        kinds = wm._kinds_of(tx, ["o-bearing-replacement", "ev-worklog-replacement", "ev-maintenance-record"])
    assert kinds == {"o-bearing-replacement": "occurrence", "ev-worklog-replacement": "event",
                     "ev-maintenance-record": "event"}
    view = wm.occurrence(w, "o-bearing-replacement")
    assert view["descriptions"] == ["ev-maintenance-record", "ev-worklog-replacement"]
    assert view["participants"]["patient"] == {"bearing-3": [("ev-worklog-replacement", "technician")],
                                               "bearing-1": [("ev-maintenance-record", "system")]}   # kept apart
    assert view["participants"]["actor"] == {"technician": [("ev-worklog-replacement", "technician")]}
    # describes is a judgement per perspective: the technician has not accepted the system's record as describing it
    assert wm.descriptions(w, "o-bearing-replacement", perspective="technician") == ["ev-worklog-replacement"]


def test_claimed_effects_and_accepted_state_changes(world):
    wm, w, ids = world
    effects = {(e["kind"], e["outcome"]["roles"].get("part", e["outcome"]["roles"].get("value"))[0]): e
               for e in wm.effects_of(w, "ev-worklog-replacement", g.AFTER)}
    fitted, removed = effects[("initiates", "bearing-3")], effects[("terminates", "bearing-1")]
    for e in (fitted, removed):
        assert (e["claim"], e["claimed_by"], e["state"]["accepted_change"]) == ("accepted", ["technician"], True)
    assert fitted["state"]["before"].holds is not True and fitted["state"]["after"].holds is True
    assert removed["state"]["before"].holds is True and removed["state"]["after"].holds is not True
    vib = effects[("initiates", "low")]                          # asserted, not accepted: neither claim nor state
    assert (vib["claim"], vib["state"]["after"].status, vib["state"]["accepted_change"]) == \
        ("unreviewed", Status.UNKNOWN, False)
    own = {e["outcome"]["roles"].get("value", [None])[0]: e
           for e in wm.effects_of(w, "ev-worklog-replacement", g.AFTER, perspective="technician")}
    assert (own["low"]["claim"], own["low"]["state"]["accepted_change"]) == ("accepted", True)   # its own account


def test_a_recorded_state_need_not_have_an_initiating_event(world):
    wm, w, _ = world
    c = wm.changes(w, "gbx-100", g.BEFORE, g.INSPECTION[1] + timedelta(minutes=1))
    began = {x["roles"]["value"][0]: x for x in c["began"] if x["type"] == "has-quality"}
    ended = {x["roles"]["value"][0]: x for x in c["ended"] if x["type"] == "has-quality"}
    assert began["faulty"]["stated_by"] == ["inspector"] and began["faulty"]["claimed_events"] == []
    assert ended["operational"]["stated_by"] == ["system"] and ended["operational"]["claimed_events"] == []


def test_what_changed_when_and_according_to_whom(world):
    wm, w, _ = world
    c = wm.changes(w, "gbx-100", g.INSPECTION[1] + timedelta(minutes=1), g.AFTER)
    began = {x["roles"]["value"][0]: x for x in c["began"]}
    ended = {x["roles"]["value"][0]: x for x in c["ended"]}
    assert began["operational"]["stated_by"] == ["technician"]
    (ev,) = began["operational"]["claimed_events"]
    assert (ev["event"], ev["claim"], ev["claimed_by"], ev["occurrences"]) == \
        ("ev-test-run", "accepted", ["technician"], ["o-test-run"])
    assert ev["end"].latest == g.RESTORED
    assert [e["event"] for e in ended["faulty"]["claimed_events"]] == ["ev-test-run"]
    parts = wm.changes(w, "shaft-asm-in", g.BEFORE, g.AFTER)
    assert [x["roles"]["part"] for x in parts["began"]] == [["bearing-3"]]
    assert [x["roles"]["part"] for x in parts["ended"]] == [["bearing-1"]]
    assert condition(wm, w, g.BEFORE) == (Status.ASSERTED, ("operational",))
    assert condition(wm, w, g.INSPECTION[1]) == (Status.ASSERTED, ("faulty",))
    assert condition(wm, w, g.AFTER) == (Status.ASSERTED, ("operational",))


def test_temporal_order_and_overlap(world):
    wm, w, _ = world
    assert wm.before(w, "ev-inspection-report", "ev-worklog-replacement") is True
    assert wm.before(w, "ev-test-run", "ev-worklog-replacement") is False
    assert wm.before(w, "ev-worklog-replacement", "ev-maintenance-record") is None      # same interval: overlap
    assert wm.before(w, "ev-test-run", "ev-sign-off") is True                         # touching instants


def test_knowledge_time_boundaries(world):
    wm, w, ids = world
    known = ids["known_before_repair"]
    assert condition(wm, w, g.AFTER, as_of=known) == (Status.ASSERTED, ("faulty",))     # the repair not yet recorded
    assert wm.effects_of(w, "ev-test-run", g.AFTER, as_of=known) == []
    assert condition(wm, w, g.AFTER) == (Status.ASSERTED, ("operational",))


def test_perspectives_judge_the_change(world):
    wm, w, _ = world
    # the inspector has accepted nothing of the technician's: in its view the gearbox is never restored
    assert condition(wm, w, g.AFTER, perspective="inspector")[0] in (Status.UNKNOWN, Status.NOT_YET_KNOWN)
    eff = wm.effects_of(w, "ev-test-run", g.AFTER, perspective="inspector")
    assert {e["claim"] for e in eff} == {"unreviewed"}
    assert condition(wm, w, g.AFTER, perspective="technician") == (Status.ASSERTED, ("operational",))


def test_hypothetical_snapshot_without_the_repair(ref, driver):
    wm, ids = ref
    w = ids["world"]
    # a plan made from what was known before the repair was recorded (a knowledge snapshot): no repair, no sign-off
    plan = wm.create_world("plan: no repair", kind="hypothetical", base=w, knowledge_at=ids["known_before_repair"],
                           branch_at=g.INSPECTION[1] + timedelta(hours=1), id=f"plan-{uuid.uuid4().hex[:6]}")
    assert condition(wm, plan, g.AFTER) == (Status.ASSERTED, ("faulty",))              # the repair is after the branch
    assert condition(wm, w, g.AFTER) == (Status.ASSERTED, ("operational",))
    assert wm.changes(plan, "gbx-100", g.INSPECTION[1] + timedelta(minutes=1), g.AFTER)["began"] == []


def test_selective_and_full_load_agree_on_dynamics(world):
    wm, w, ids = world

    def answers():
        return [wm.effects_of(w, e, g.AFTER, perspective=p) for e in ("ev-worklog-replacement", "ev-test-run")
                for p in ("system", "technician", "inspector")] + \
               [wm.changes(w, s, a, b) for s in ("gbx-100", "shaft-asm-in")
                for a, b in ((g.BEFORE, g.INSPECTION[1]), (g.INSPECTION[1], g.AFTER))] + \
               [wm.occurrence(w, "o-bearing-replacement"), condition(wm, w, g.AFTER, as_of=ids["known_before_repair"])]

    wm.selective = True
    selective = answers()
    wm.selective = False
    assert answers() == selective


def test_record_event_and_core_behaviour_are_unchanged(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, clock=FakeClock())
    try:
        assert "causes" not in wm.proposition_types()                                   # Stage B is opt-in
        w = wm.create_world("actual", id="actual")
        for kind, n in (("physical-object", "box"), ("place", "a"), ("place", "b")):
            wm.add_entity(kind, n, id=n)
        wm.attest(w, "located-at", {"located": "box", "place": "a"}, start=g.T0, until_superseded=True)
        eid, _ = wm.move(w, "box", "b", g.T1)
        assert (wm.count("initiates"), wm.count("terminates")) == (0, 0)               # move writes no effect claims
    finally:
        driver.databases.get(name).delete()
