"""LABS-1.011: occurrence vs description semantics, and the scope of causal claims.

Part 1: an occurrence's happening is judged only from attestations of its own existence. Accepted descriptions,
describes links and causal claims never establish it. An accepted account of a denied occurrence is reportable, and a
causal claim involving a denied occurrence stays visible as its source's account, marked as not applying.
Part 2: causal claims name particular occurrences or descriptions, so a claim about the first of two similar repairs
says nothing about the second. Knowledge time, perspectives, snapshots and descriptions of one occurrence are covered.
"""

import uuid
from datetime import timedelta

import pytest

from conftest import FakeClock
from worldmodel import DYNAMICS_MODULES, WorldModel
from worldmodel.examples import gearbox as g


def build(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=DYNAMICS_MODULES, clock=FakeClock())
    return wm, g.extend_second_repair(wm, g.extend_causality(wm, g.extend_dynamics(wm, g.build(wm))))


@pytest.fixture
def fresh(driver):
    wm, ids = build(driver)
    try:
        yield wm, ids["world"], ids
    finally:
        driver.databases.get(wm.database).delete()


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


def claims(wm, w, effect, t=g.AFTER, **kw):
    return {(c["cause"], c["effect"]): c for c in wm.causes_of(w, effect, t, **kw)}


def happened(wm, w, occ, **kw):
    return wm.occurrence_status(w, occ, g.AFTER, **kw)["status"]


# ---- part 1: occurrences and descriptions -------------------------------------------------------------------------
def test_an_accepted_description_does_not_establish_the_occurrence(world):
    wm, w, _ = world
    st = wm.occurrence_status(w, "o-bearing-replacement", g.AFTER)
    assert st["status"] == "not established" and st["existence"] == []
    assert [(d["description"], d["account"], d["account_by"], d["describes"]) for d in st["descriptions"]] == [
        ("ev-maintenance-record", "accepted", ["system"], "accepted"),
        ("ev-worklog-replacement", "accepted", ["technician"], "accepted")]
    # the generic exists() still infers existence from participation (Core 0.3); occurrence_status does not
    assert wm.exists(w, "o-bearing-replacement", g.AFTER).holds is True


def test_conflicting_descriptions_stay_attributable_to_their_sources(world):
    wm, w, _ = world
    view = wm.occurrence(w, "o-bearing-replacement")
    assert view["participants"]["patient"] == {"bearing-3": [("ev-worklog-replacement", "technician")],
                                               "bearing-1": [("ev-maintenance-record", "system")]}
    st = wm.occurrence_status(w, "o-bearing-replacement", g.AFTER, perspective="technician")
    assert {d["description"]: d["describes"] for d in st["descriptions"]} == \
        {"ev-maintenance-record": "unreviewed", "ev-worklog-replacement": "accepted"}


def test_an_accepted_account_of_a_denied_occurrence(fresh):
    wm, w, _ = fresh
    wm.accept(wm.deny(w, "existence", {"existent": "o-relubrication"}, until_superseded=True, attester="cm-1",
                      basis="inference"))
    st = wm.occurrence_status(w, "o-relubrication", g.AFTER)
    assert st["status"] == "denied"
    assert [(d["description"], d["account"], d["describes"]) for d in st["descriptions"]] == \
        [("ev-relubrication", "accepted", "accepted")]                 # the account stays accepted
    lube = claims(wm, w, "o-test-run")[("o-relubrication", "o-test-run")]
    assert lube["judgement"] == "disputed" and lube["applies"] is False  # still visible; does not apply
    assert lube["occurrences"]["o-relubrication"] == "denied"
    rest = [c for c in wm.causes_of(w, "o-test-run", g.AFTER) if c["cause"] != "o-relubrication"]
    assert all(c["applies"] is True for c in rest)
    assert happened(wm, w, "o-relubrication", perspective="technician") == "not established"   # not its view


def test_a_lifted_description_level_claim_never_establishes_a_denied_occurrence(fresh):
    wm, w, _ = fresh
    wm.accept(wm.deny(w, "existence", {"existent": "o-test-run"}, until_superseded=True, attester="cm-1"))
    lifted = claims(wm, w, "o-test-run")[("ev-worklog-replacement", "ev-test-run")]
    assert (lifted["lifted"], lifted["judgement"], lifted["applies"]) == (True, "accepted", False)
    assert happened(wm, w, "o-test-run") == "denied"                    # unchanged by any accepted claim
    assert wm.interval(w, "ev-test-run") is not None                    # the technician's account stands


def test_a_disputed_occurrence(fresh):
    wm, w, _ = fresh
    wm.accept(wm.attest(w, "existence", {"existent": "o-reassembly"}, until_superseded=True, attester="technician"))
    wm.accept(wm.deny(w, "existence", {"existent": "o-reassembly"}, until_superseded=True, attester="cm-1"))
    assert happened(wm, w, "o-reassembly") == "disputed"
    assert claims(wm, w, "o-test-run")[("o-reassembly", "o-test-run")]["applies"] is None


def test_hypothetical_worlds_keep_the_distinction(fresh):
    wm, w, _ = fresh
    wm.accept(wm.attest(w, "existence", {"existent": "o-relubrication"}, until_superseded=True, attester="technician"))
    # branched after the relubrication's account starts, so the plan inherits that account (a branch before it would
    # not inherit it: snapshots take only what starts before the branch)
    plan = wm.create_world("plan: no relubrication", kind="hypothetical", base=w,
                           branch_at=g.STEPS["o-relubrication"][1] + timedelta(hours=1), id="plan-no-lube")
    wm.deny(plan, "existence", {"existent": "o-relubrication"}, until_superseded=True)   # stipulated: it did not happen
    assert happened(wm, plan, "o-relubrication") == "denied"           # the variant's stipulation overrides
    assert happened(wm, w, "o-relubrication") == "accepted"
    st = wm.occurrence_status(plan, "o-relubrication", g.AFTER)
    assert st["descriptions"][0]["account"] == "accepted"              # the inherited account is still an account
    assert claims(wm, plan, "o-test-run")[("o-relubrication", "o-test-run")]["applies"] is False
    assert claims(wm, w, "o-test-run")[("o-relubrication", "o-test-run")]["applies"] is True


# ---- part 2: the scope of causal claims ---------------------------------------------------------------------------
def test_a_claim_about_the_first_repair_does_not_apply_to_the_second(world):
    wm, w, ids = world
    first, second = claims(wm, w, "o-test-run"), claims(wm, w, "o-test-run-2", t=g.TEST_RUN_2[1] + timedelta(hours=1))
    assert ("o-bearing-replacement", "o-test-run") in first and ("o-bearing-replacement-2", "o-test-run-2") in second
    assert not any("o-bearing-replacement" == c[0] for c in second)    # same kinds, actor and tools; other happening
    assert not any(c[0].endswith("-2") for c in first)
    assert {k for e in wm.events(w) if e["event"] in ("ev-test-run", "ev-test-run-2") for k in e["kinds"]} == \
        {"action", "test"}                                             # similar descriptions, distinct identities
    assert wm.before(w, "ev-test-run", "ev-worklog-replacement-2") is True   # ordered, never linked causally


def test_changes_in_acceptance_over_knowledge_time(world):
    wm, w, ids = world
    t = g.TEST_RUN_2[1] + timedelta(hours=1)
    before = claims(wm, w, "o-test-run-2", t=t, as_of=ids["known_before_claim_2_accepted"])
    assert before[("o-bearing-replacement-2", "o-test-run-2")]["judgement"] == "unreviewed"
    assert claims(wm, w, "o-test-run-2", t=t)[("o-bearing-replacement-2", "o-test-run-2")]["judgement"] == "accepted"


def test_perspective_specific_causal_disagreement_on_one_repair(fresh):
    wm, w, _ = fresh
    t = g.TEST_RUN_2[1] + timedelta(hours=1)
    wm.claim_cause(w, "o-bearing-replacement-2", "o-test-run-2", polarity=False, attester="inspector")
    assert claims(wm, w, "o-test-run-2", t=t, perspective="inspector")[
        ("o-bearing-replacement-2", "o-test-run-2")]["judgement"] == "denied"
    assert claims(wm, w, "o-test-run-2", t=t)[("o-bearing-replacement-2", "o-test-run-2")]["judgement"] == "accepted"
    assert claims(wm, w, "o-test-run")[("o-bearing-replacement", "o-test-run")]["judgement"] == "accepted"  # unaffected


def test_hypothetical_snapshots_of_causal_claims(fresh):
    wm, w, ids = fresh
    t = g.TEST_RUN_2[1] + timedelta(hours=1)
    plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=g.REPLACEMENT_2[0], id="plan-second")
    assert ("o-bearing-replacement-2", "o-test-run-2") in claims(wm, plan, "o-test-run-2", t=t)   # recorded before
    wm.accept(wm.claim_cause(w, "o-reassembly", "o-test-run-2", attester="cm-1"))   # recorded after the plan
    assert ("o-reassembly", "o-test-run-2") in claims(wm, w, "o-test-run-2", t=t)
    assert ("o-reassembly", "o-test-run-2") not in claims(wm, plan, "o-test-run-2", t=t)


def test_claims_involving_descriptions_of_the_same_occurrence(world):
    wm, w, ids = world
    assert wm.descriptions(w, "o-test-run") == ["ev-qa-test-log", "ev-test-run"]
    occ = claims(wm, w, "o-test-run")
    assert ("ev-worklog-replacement", "ev-test-run") in occ               # a claim about one description, lifted
    qa = claims(wm, w, "ev-qa-test-log")
    assert ("o-bearing-replacement", "o-test-run") in qa                  # the occurrence-level claim lifts down
    assert ("ev-worklog-replacement", "ev-test-run") not in qa            # a sibling description's claim does not
    assert qa[("o-bearing-replacement", "o-test-run")]["lifted"] is True


def test_selective_and_full_load_agree(world):
    wm, w, ids = world
    t2 = g.TEST_RUN_2[1] + timedelta(hours=1)

    def answers():
        return [wm.occurrence_status(w, o, g.AFTER, perspective=p) for o in
                ("o-bearing-replacement", "o-test-run", "o-relubrication") for p in ("system", "technician")] + \
               [wm.causes_of(w, e, t2) for e in ("o-test-run", "o-test-run-2", "ev-qa-test-log")] + \
               [wm.causes_of(w, "o-test-run-2", t2, as_of=ids["known_before_claim_2_accepted"])]

    wm.selective = True
    selective = answers()
    wm.selective = False
    assert answers() == selective
