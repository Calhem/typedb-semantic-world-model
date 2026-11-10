"""LABS-1.015: the changes() temporal contract and functional judgement across read paths.

Transitions whose valid time intersects (t1, t2], judged for world, perspective and knowledge time; world-state vs
judgement transitions; uncertain windows classified as certain or possible; explanations only from accepted effect
claims, attributed to compatible activations, ambiguous when a claim fits several. Built from the six LABS-1.014
probe cases plus the gearbox reference world.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from conftest import FakeClock
from worldmodel import DYNAMICS_MODULES, WorldModel
from worldmodel.examples import gearbox as g
from worldmodel.semantics import Status


def T(h, m=0):
    return datetime(2026, 11, 9, h, m, tzinfo=timezone.utc)


@pytest.fixture
def space(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=DYNAMICS_MODULES, clock=FakeClock())
    try:
        w = wm.create_world("actual", id="actual")
        for kind, n in (("physical-object", "box"), ("place", "a"), ("place", "b"), ("place", "c"),
                        ("social-object", "cam"), ("physical-object", "tech")):
            wm.add_entity(kind, n, id=n)
        yield wm, w
    finally:
        driver.databases.get(name).delete()


def at(wm, w, place, start, end=None, **kw):
    if end is None:
        kw.setdefault("until_superseded", True)
    return wm.attest(w, "located-at", {"located": "box", "place": place}, start=start, end=end, **kw)


def lines(c):
    """(before values, after values, category, window, within) per transition of the box's location slot."""
    out = []
    for tr in c["transitions"]:
        if tr["track"]["kind"] == "slot" and tr["track"]["type"] == "located-at":
            out.append((tr["before"]["status"], [v[0] for v in tr["before"]["values"]], tr["after"]["status"],
                        [v[0] for v in tr["after"]["values"]], tr["category"], tr["window"], tr["within"]))
    return out


def both_paths(wm, ask):
    wm.selective = True
    a = ask()
    wm.selective = False
    b = ask()
    wm.selective = True
    assert a == b
    return a


A, U, D = Status.ASSERTED, Status.UNKNOWN, Status.DISPUTED


def test_multiple_transitions_and_a_return_to_the_original_state(space):
    wm, w = space
    at(wm, w, "a", T(9), T(10))
    at(wm, w, "b", T(10), T(11))
    at(wm, w, "a", T(11))
    c = both_paths(wm, lambda: wm.changes(w, "box", T(9, 30), T(12)))
    assert lines(c) == [(A, ["a"], A, ["b"], "world-state", (T(10), T(10)), "certain"),
                        (A, ["b"], A, ["a"], "world-state", (T(11), T(11)), "certain")]
    assert [(x["roles"]["place"], x["within"]) for x in c["began"]] == [(["b"], "certain"), (["a"], "certain")]


def test_uncertain_windows_are_certain_possible_or_outside(space):
    wm, w = space
    at(wm, w, "a", T(8), (T(10), T(10, 20)))
    at(wm, w, "b", (T(10), T(10, 20)))
    window = (T(10), T(10, 20))
    assert lines(wm.changes(w, "box", T(9), T(11))) == [(A, ["a"], A, ["b"], "world-state", window, "certain")]
    assert lines(wm.changes(w, "box", T(10, 15), T(11))) == [(A, ["a"], A, ["b"], "world-state", window, "possible")]
    assert lines(wm.changes(w, "box", T(9), T(10, 5)))[0][-1] == "possible"
    assert lines(wm.changes(w, "box", T(10, 30), T(11))) == []                     # outside
    assert lines(wm.changes(w, "box", T(8, 30), T(9, 30))) == []
    assert wm.value_at(w, "located-at", "box", T(10, 10)).status == U               # no instant is invented


def test_judgement_transitions_unknown_and_disputed(space):
    wm, w = space
    at(wm, w, "a", T(8), (T(10), T(10, 20)))                    # a, then unknown, then a again: no world change
    at(wm, w, "a", (T(10, 20), T(10, 20)))
    c = lines(wm.changes(w, "box", T(9), T(11)))
    assert [(x[0], x[2], x[4]) for x in c] == [(A, U, "judgement"), (U, A, "judgement")]
    wm.accept(at(wm, w, "b", T(11, 30), attester="cam"))        # an accepted rival claim from 11:30
    d = lines(wm.changes(w, "box", T(11), T(12)))
    assert d == [(A, ["a"], D, ["a", "b"], "judgement", (T(11, 30), T(11, 30)), "certain")]
    assert wm.changes(w, "box", T(7), T(9))["transitions"][0]["category"] == "judgement"   # first known (UNKNOWN -> a)
    assert wm.changes(w, "box", T(8), T(9))["transitions"] == []      # at exactly t1 it is already in effect: outside


def test_functional_conflicts_agree_across_read_paths(space):
    wm, w = space
    mine = at(wm, w, "a", T(9))
    rival = at(wm, w, "b", T(10), attester="cam")
    wm.accept(rival)
    facts = {f["roles"]["place"][0]: f for f in wm.facts_about(w, "box", T(10, 30)) if f["type"] == "located-at"}
    assert (facts["a"]["status"], facts["a"]["conflicts"]) == (D, [rival])
    assert (facts["b"]["status"], facts["b"]["conflicts"]) == (D, [mine])
    assert wm.value_at(w, "located-at", "box", T(10, 30)).status == D
    assert wm.holds(w, "located-at", {"located": "box", "place": "a"}, T(10, 30)).status == D
    (tr,) = wm.changes(w, "box", T(9, 30), T(10, 30))["transitions"]
    assert (tr["after"]["status"], sorted(tr["after"]["support"]), sorted(tr["after"]["conflicts"])) == \
        (D, sorted([mine, rival]), sorted([mine, rival]))
    shelf = {f["roles"]["located"][0]: f["status"] for f in wm.facts_about(w, "a", T(10, 30))}
    assert shelf == {"box": D}                                  # seen from the place, the same judgement
    (ptr,) = [tr for tr in wm.changes(w, "a", T(9, 30), T(10, 30))["transitions"]]
    assert (ptr["track"]["kind"], ptr["before"]["status"], ptr["after"]["status"], ptr["after"]["conflicts"]) == \
        ("content", A, D, [rival])                               # and through changes() from the place
    assert wm.facts_about(w, "box", T(9, 30))[0]["conflicts"] == []


def test_events_explain_only_compatible_activations_and_never_choose(space):
    wm, w = space
    for o in ("o-move-1", "o-move-2", "o-plan"):
        wm.add_entity("occurrence", o, id=o)
    at(wm, w, "a", T(8), T(9))
    at(wm, w, "b", T(9), T(13))
    at(wm, w, "a", T(13))
    late = wm.account(w, {"actor": "tech", "patient": "box"}, T(12, 50), T(13), occurrence="o-move-2", id="ev-late")
    wm.claim_effect(w, late, "initiates", "located-at", {"located": "box", "place": "a"})
    early = wm.changes(w, "box", T(7), T(8, 30))
    assert [tr["explanations"] for tr in early["transitions"]] == [[]]               # 12:50 cannot explain 08:00
    later = wm.changes(w, "box", T(12), T(14))["transitions"]
    assert [(e["event"], e["attribution"]) for e in later[0]["explanations"]] == [("ev-late", "unique")]
    plan = wm.account(w, {"actor": "tech", "patient": "box"}, T(7), T(7, 30), occurrence="o-plan", id="ev-plan")
    wm.claim_effect(w, plan, "initiates", "located-at", {"located": "box", "place": "a"})   # fits both activations
    first = wm.changes(w, "box", T(7, 45), T(8, 30))["transitions"][0]["explanations"]
    second = wm.changes(w, "box", T(12), T(14))["transitions"][0]["explanations"]
    assert [(e["event"], e["attribution"]) for e in first] == [("ev-plan", "ambiguous")]
    assert sorted((e["event"], e["attribution"]) for e in second) == [("ev-late", "unique"), ("ev-plan", "ambiguous")]
    unaccepted = wm.account(w, {"actor": "tech", "patient": "box"}, T(12, 55), T(13), id="ev-cam", attester="cam")
    wm.claim_effect(w, unaccepted, "initiates", "located-at", {"located": "box", "place": "a"}, attester="cam")
    assert "ev-cam" not in {e["event"] for e in wm.changes(w, "box", T(12), T(14))["transitions"][0]["explanations"]}


def test_delayed_effects_and_events_outside_the_interval(space):
    wm, w = space
    wm.add_entity("occurrence", "o-order", id="o-order")
    at(wm, w, "a", T(8), T(10, 45))
    at(wm, w, "b", T(10, 45))
    ev = wm.account(w, {"actor": "tech", "patient": "box"}, T(9, 50), T(10), occurrence="o-order", id="ev-order")
    wm.claim_effect(w, ev, "initiates", "located-at", {"located": "box", "place": "b"})
    c = wm.changes(w, "box", T(10, 30), T(11))
    assert lines(c) == [(A, ["a"], A, ["b"], "world-state", (T(10, 45), T(10, 45)), "certain")]
    (e,) = c["transitions"][0]["explanations"]
    assert (e["event"], e["attribution"], e["end"].latest) == ("ev-order", "unique", T(10))   # provenance only
    assert wm.changes(w, "box", T(9, 45), T(10, 30))["transitions"] == []           # the event is not a change


def test_perspective_and_knowledge_time(space):
    wm, w = space
    at(wm, w, "a", T(9))
    rival = at(wm, w, "b", T(10), attester="cam")
    assert wm.changes(w, "box", T(9, 30), T(10, 30))["transitions"] == []           # unreviewed: no change
    cams = lines(wm.changes(w, "box", T(9, 30), T(10, 30), perspective="cam"))
    assert cams == [(U, [], A, ["b"], "judgement", (T(10), T(10)), "certain")]      # cam has only its own claim
    before = wm.clock.now
    wm.accept(rival)
    assert lines(wm.changes(w, "box", T(9, 30), T(10, 30)))[0][2] == D
    assert wm.changes(w, "box", T(9, 30), T(10, 30), as_of=before)["transitions"] == []


def test_hypothetical_snapshots(space):
    wm, w = space
    at(wm, w, "a", T(8))
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(10), id="plan-move")
    at(wm, h, "c", T(11))                                        # the plan moves the box at 11:00
    at(wm, w, "b", T(9, 30), attester="cam")                     # base, after the plan was made, unaccepted anyway
    wm.accept(wm.end(w, wm.history(w, "box")[0]["attestation"], T(10, 30)))
    plan = lines(wm.changes(h, "box", T(10, 30), T(12)))
    assert plan == [(Status.ASSERTED, ["a"], Status.STIPULATED, ["c"], "world-state", (T(11), T(11)), "certain")]
    base = lines(wm.changes(w, "box", T(10, 15), T(12)))
    assert [(x[0], x[2]) for x in base] == [(A, U)]               # the base's own ending at 10:30, not the plan's move


def test_the_reference_world_changes_contract(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=DYNAMICS_MODULES, clock=FakeClock())
    try:
        ids = g.extend_causality(wm, g.extend_dynamics(wm, g.build(wm)))
        w = ids["world"]
        c = both_paths(wm, lambda: wm.changes(w, "gbx-100", g.BEFORE, g.AFTER))
        cond = [tr for tr in c["transitions"] if tr["track"]["kind"] == "slot" and tr["track"]["type"] == "has-quality"
                and tr["track"]["key"].get("quality") == ["condition"]]
        assert [([v[0] for v in tr["before"]["values"]], [v[0] for v in tr["after"]["values"]], tr["category"])
                for tr in cond] == [(["operational"], ["faulty"], "world-state"),
                                    (["faulty"], ["operational"], "world-state")]  # was "unchanged" (two instants)
        assert cond[0]["explanations"] == []                                      # recorded, not caused, by the inspection
        assert {(e["event"], e["effect"], e["attribution"]) for e in cond[1]["explanations"]} == {
            ("ev-test-run", "initiates", "unique"), ("ev-test-run", "terminates", "unique")}
        first = wm.changes(w, "gbx-100", g.T0 - timedelta(hours=1), g.T0 + timedelta(hours=1))
        assert all("ev-test-run" not in {e["event"] for e in tr["explanations"]} for tr in first["transitions"])
    finally:
        driver.databases.get(name).delete()
