"""Core 0.4 Stage B2 (LABS-1.010): processes, actions and asserted causation in the gearbox reference world.

The repair is a process occurrence with five step occurrences; the steps are the technician's actions. Causal claims
are asserted by sources at the occurrence or the description level, lifted only through describes links the
perspective accepts, and judged per perspective, knowledge time and world. Nothing is inferred from order.
"""

import uuid

import pytest

from conftest import FakeClock
from worldmodel import DYNAMICS_MODULES, WorldModel
from worldmodel.examples import gearbox as g
from worldmodel.semantics import Status

OPERATIONAL = {"bearer": "gbx-100", "quality": "condition", "value": "operational"}


@pytest.fixture(scope="module")
def ref(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=DYNAMICS_MODULES, clock=FakeClock())
    try:
        yield wm, g.extend_causality(wm, g.extend_dynamics(wm, g.build(wm)))
    finally:
        driver.databases.get(name).delete()


@pytest.fixture
def world(ref):
    wm, ids = ref
    wm.selective = True
    yield wm, ids["world"], ids
    wm.selective = True


def judged(wm, world, effect, t=g.AFTER, **kw):
    return {(c["cause"], c["effect"]): c for c in wm.causes_of(world, effect, t, **kw)}


def test_process_membership_order_and_overlap(world):
    wm, w, _ = world
    steps = wm.process_steps(w, "o-repair", g.AFTER)
    assert [s["occurrence"] for s in steps] == ["o-disassembly", "o-bearing-replacement", "o-relubrication",
                                                "o-reassembly", "o-test-run"]
    assert all(s["actors"] == ["technician"] and "action" in s["kinds"] for s in steps)
    assert {k for e in wm.events(w) if e["event"] == "ev-repair" for k in e["kinds"]} == {"process", "repair"}
    assert wm.before(w, "ev-relubrication", "ev-reassembly") is None                  # overlapping steps
    assert wm.before(w, "ev-disassembly", "ev-worklog-replacement") is True
    assert wm.process_steps(w, "o-repair", g.AFTER, perspective="inspector") == []    # not accepted by the inspector


def test_actions_and_participant_roles(world):
    wm, w, _ = world
    actions = {a["event"]: a for a in wm.actions_of(w, "technician")}
    assert set(actions) == {"ev-disassembly", "ev-worklog-replacement", "ev-relubrication", "ev-reassembly",
                            "ev-test-run"}                                            # the repair itself is a process
    assert actions["ev-relubrication"]["occurrences"] == ["o-relubrication"]
    lube = wm.occurrence(w, "o-relubrication")["participants"]
    assert (lube["actor"], lube["patient"], lube["instrument"]) == (
        {"technician": [("ev-relubrication", "technician")]}, {"shaft-asm-in": [("ev-relubrication", "technician")]},
        {"grease-gun": [("ev-relubrication", "technician")]})
    assert [a["event"] for a in wm.actions_of(w, "inspector")] == ["ev-inspection-report"]


def test_causal_claims_are_judged_not_inferred(world):
    wm, w, ids = world
    c = judged(wm, w, "o-test-run")
    assert (c[("o-bearing-replacement", "o-test-run")]["judgement"], c[("o-bearing-replacement", "o-test-run")]["status"]) \
        == ("accepted", Status.ASSERTED)
    lifted = c[("ev-worklog-replacement", "ev-test-run")]
    assert (lifted["level"], lifted["lifted"], lifted["judgement"]) == ("description", True, "accepted")
    assert lifted["lifted_via"] == {"description": "ev-test-run", "occurrence": "o-test-run"}
    assert lifted["cause_occurrences"] == ["o-bearing-replacement"]
    lube = c[("o-relubrication", "o-test-run")]
    assert (lube["judgement"], lube["status"], lube["claimed_by"]) == ("disputed", Status.DISPUTED, ["cm-1", "inspector"])
    assert {x["polarity"] for x in lube["attestations"]} == {True, False}
    assert c[("o-inspection", "o-test-run")]["judgement"] == "rejected"
    assert c[("o-reassembly", "o-test-run")]["judgement"] == "unreviewed"
    assert ("o-disassembly", "o-test-run") not in c                    # earlier, part of the process, never claimed
    assert wm.before(w, "ev-inspection-report", "ev-test-run") is True    # succession holds; causation was rejected
    # exactly the six causal contents written (a claim and its denial share one content), nothing derived
    assert wm.count("causes") == 6


def test_lifting_needs_accepted_describes_links(world):
    wm, w, _ = world
    insp = judged(wm, w, "o-test-run", perspective="inspector")
    assert ("ev-worklog-replacement", "ev-test-run") not in insp       # the inspector accepts no describes link
    assert insp[("o-relubrication", "o-test-run")]["judgement"] == "accepted"   # its own claim
    from_description = judged(wm, w, "ev-test-run")                     # asked about the description: lifted upwards
    assert from_description[("o-bearing-replacement", "o-test-run")]["lifted"] is True
    assert from_description[("ev-worklog-replacement", "ev-test-run")]["lifted"] is False


def test_perspectives_and_knowledge_time(world):
    wm, w, ids = world
    tech = judged(wm, w, "o-test-run", perspective="technician")
    assert tech[("o-bearing-replacement", "o-test-run")]["judgement"] == "accepted"
    assert tech[("o-relubrication", "o-test-run")]["judgement"] == "unreviewed"
    earlier = judged(wm, w, "o-test-run", as_of=ids["known_before_denial"])
    assert earlier[("o-relubrication", "o-test-run")]["judgement"] == "accepted"     # before the denial was accepted
    assert earlier[("o-inspection", "o-test-run")]["judgement"] == "unreviewed"      # not yet rejected


def test_hypothetical_causal_account_and_snapshot(world):
    wm, w, ids = world
    plan = judged(wm, ids["causal_plan"], "o-test-run")
    assert (plan[("o-relubrication", "o-test-run")]["judgement"], plan[("o-relubrication", "o-test-run")]["status"]) \
        == ("accepted", Status.STIPULATED)                               # the variant's stipulation wins
    assert plan[("o-bearing-replacement", "o-test-run")]["judgement"] == "denied"
    # the description-level claim is other content: inherited and still accepted (recorded as finding F-B1)
    assert plan[("ev-worklog-replacement", "ev-test-run")]["judgement"] == "accepted"
    assert ("o-disassembly", "o-bearing-replacement") in judged(wm, w, "o-bearing-replacement")
    assert judged(wm, ids["causal_plan"], "o-bearing-replacement") == {}  # recorded in the base after the plan
    assert judged(wm, w, "o-test-run")[("o-relubrication", "o-test-run")]["judgement"] == "disputed"


def test_explaining_why_the_gearbox_is_operational_again(world):
    wm, w, _ = world
    e = wm.explain(w, "has-quality", OPERATIONAL, g.AFTER)
    assert e["holds"].status == Status.ASSERTED and e["holds"].holds is True
    (init,) = e["initiated_by"]
    assert (init["event"], init["claim"], init["occurrences"]) == ("ev-test-run", "accepted", ["o-test-run"])
    causes = {c["cause"]: c["judgement"] for c in init["causes"]}
    assert causes == {"o-bearing-replacement": "accepted", "ev-worklog-replacement": "accepted",
                      "o-relubrication": "disputed", "o-reassembly": "unreviewed", "o-inspection": "rejected"}
    before = wm.explain(w, "has-quality", OPERATIONAL, g.BEFORE)        # operational at T0: no initiating event known
    assert before["holds"].holds is True and before["initiated_by"] == []
    fault = wm.explain(w, "has-quality", {**OPERATIONAL, "value": "faulty"}, g.INSPECTION[1])
    assert fault["holds"].holds is True and fault["initiated_by"] == []  # the inspection recorded it, did not cause it


def test_selective_and_full_load_agree_on_causal_answers(world):
    wm, w, ids = world

    def answers():
        out = [wm.causes_of(w, e, g.AFTER, perspective=p) for e in ("o-test-run", "ev-test-run", "o-bearing-replacement")
               for p in ("system", "technician", "inspector")]
        out += [wm.causes_of(w, "o-test-run", g.AFTER, as_of=ids["known_before_denial"]),
                wm.causes_of(ids["causal_plan"], "o-test-run", g.AFTER),
                wm.explain(w, "has-quality", OPERATIONAL, g.AFTER), wm.process_steps(w, "o-repair", g.AFTER),
                wm.actions_of(w, "technician")]
        return out

    wm.selective = True
    selective = answers()
    wm.selective = False
    assert answers() == selective
