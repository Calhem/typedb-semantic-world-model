"""LABS-1.012: one existence judgement for occurrences, settled lifted-claim rules, and events loaded once per question.

exists() and occurrence_status() give the same answer for an occurrence in every case (accepted, denied, disputed,
not established), with provenance; other things keep the Core 0.3 rule. A lifted claim keeps its own status, is
marked lifted, and applies only if the occurrences' own existence judgement allows.
"""

import uuid
from datetime import timedelta

import pytest

from conftest import FakeClock
from worldmodel import DYNAMICS_MODULES, WorldModel
from worldmodel.examples import gearbox as g
from worldmodel.semantics import Status

OPERATIONAL = {"bearer": "gbx-100", "quality": "condition", "value": "operational"}


def build(driver, cycles=0):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=DYNAMICS_MODULES, clock=FakeClock())
    ids = g.extend_second_repair(wm, g.extend_causality(wm, g.extend_dynamics(wm, g.build(wm))))
    w = ids["world"]
    for i in range(cycles):                      # later test runs that also claim "operational"
        day = g.TEST_RUN_2[1] + timedelta(days=i + 1)
        occ = f"o-test-x{i}"
        wm.add_entity("occurrence", f"test run {i}", id=occ)
        e = wm.account(w, {"actor": "technician", "patient": "gbx-100"}, day, day + timedelta(minutes=30),
                       kind=["test", "action"], occurrence=occ, attester="technician", id=f"ev-test-x{i}")
        for a in wm.account_attestations(w, e, attester="technician"):
            wm.accept(a)
        wm.accept(wm.claim_effect(w, e, "initiates", "has-quality", OPERATIONAL, attester="technician"))
    return wm, ids


@pytest.fixture
def fresh(driver):
    wm, ids = build(driver)
    try:
        yield wm, ids["world"], ids
    finally:
        driver.databases.get(wm.database).delete()


def both(wm, w, occ, t=g.AFTER, **kw):
    """exists() and occurrence_status() for one occurrence; they must agree."""
    a = wm.exists(w, occ, t, **kw)
    st = wm.occurrence_status(w, occ, t, **kw)
    expected = ("disputed" if a.status == Status.DISPUTED else "accepted" if a.holds is True else
                "denied" if a.holds is False else "not established")
    assert st["status"] == expected and st["answer"] == a
    return a, st


# ---- 1. one existence judgement --------------------------------------------------------------------------------------
def test_both_apis_agree_in_every_state(fresh):
    wm, w, _ = fresh
    a, st = both(wm, w, "o-bearing-replacement")                       # accounts accepted, no existence statement
    assert (a.status, a.holds, st["status"]) == (Status.UNKNOWN, None, "not established")
    wm.accept(wm.attest(w, "existence", {"existent": "o-bearing-replacement"}, until_superseded=True,
                        attester="technician", basis="observation"))
    a, st = both(wm, w, "o-bearing-replacement")
    assert (a.status, a.holds, st["status"]) == (Status.ASSERTED, True, "accepted")
    assert [x["attester"] for e in st["existence"] for x in e["attestations"]] == ["technician"]   # provenance
    assert a.evidence[0]["attester"] == "technician"
    wm.accept(wm.deny(w, "existence", {"existent": "o-relubrication"}, until_superseded=True, attester="cm-1"))
    a, st = both(wm, w, "o-relubrication")
    assert (a.holds, st["status"]) == (False, "denied")
    wm.accept(wm.attest(w, "existence", {"existent": "o-reassembly"}, until_superseded=True, attester="technician"))
    wm.accept(wm.deny(w, "existence", {"existent": "o-reassembly"}, until_superseded=True, attester="cm-1"))
    a, st = both(wm, w, "o-reassembly")
    assert (a.status, st["status"]) == (Status.DISPUTED, "disputed")
    wm.add_entity("occurrence", "never mentioned", id="o-unmentioned")
    a, st = both(wm, w, "o-unmentioned")
    assert (a.status, st["status"]) == (Status.NOT_YET_KNOWN, "not established")


def test_an_unreviewed_existence_claim_is_an_alternative_not_an_answer(fresh):
    wm, w, _ = fresh
    claim = wm.attest(w, "existence", {"existent": "o-test-run"}, until_superseded=True, attester="qa-lead")
    a, st = both(wm, w, "o-test-run")
    assert (a.holds, a.alternatives, st["status"]) == (None, (claim,), "not established")
    a, st = both(wm, w, "o-test-run", perspective="qa-lead")             # its own view
    assert (a.holds, st["status"]) == (True, "accepted")


def test_other_things_keep_the_core_rule(fresh):
    wm, w, _ = fresh
    assert wm.exists(w, "bearing-3", g.AFTER).status == Status.INFERRED     # participation implies existence
    assert wm.exists(w, "housing", g.AFTER).holds is True


def test_time_knowledge_perspective_and_worlds_are_preserved(fresh):
    wm, w, _ = fresh
    start = g.REPAIR[0]
    known = wm.clock.now
    wm.accept(wm.attest(w, "existence", {"existent": "o-repair"}, start=start, end=g.REPAIR[1],
                        attester="technician"))
    assert both(wm, w, "o-repair", t=start + timedelta(hours=1))[1]["status"] == "accepted"
    assert both(wm, w, "o-repair", t=start - timedelta(hours=1))[1]["status"] == "denied"   # before it began
    assert both(wm, w, "o-repair", t=start + timedelta(hours=1), as_of=known)[1]["status"] == "not established"
    assert both(wm, w, "o-repair", t=start + timedelta(hours=1), perspective="inspector")[1]["status"] == \
        "not established"
    plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=g.REPAIR[1] + timedelta(hours=1),
                           id="plan-no-repair-occurrence")
    wm.deny(plan, "existence", {"existent": "o-repair"}, start=start, until_superseded=True)
    assert both(wm, plan, "o-repair", t=start + timedelta(hours=1))[1]["status"] == "denied"
    assert both(wm, w, "o-repair", t=start + timedelta(hours=1))[1]["status"] == "accepted"


# ---- 2. lifted claims (F-B1, U-2 settled) -------------------------------------------------------------------------
def test_lifted_claims_keep_their_status_and_apply_only_to_occurrences_not_denied(fresh):
    wm, w, _ = fresh
    lifted = {(c["cause"], c["effect"]): c for c in wm.causes_of(w, "o-test-run", g.AFTER)}[
        ("ev-worklog-replacement", "ev-test-run")]
    assert (lifted["lifted"], lifted["status"], lifted["applies"]) == (True, Status.ASSERTED, True)
    assert lifted["lifted_via"] == {"description": "ev-test-run", "occurrence": "o-test-run"}
    wm.accept(wm.deny(w, "existence", {"existent": "o-test-run"}, until_superseded=True, attester="cm-1"))
    after = {(c["cause"], c["effect"]): c for c in wm.causes_of(w, "o-test-run", g.AFTER)}
    assert all(c["applies"] is False for c in after.values())          # no applicable explanation of a denied one
    assert after[("ev-worklog-replacement", "ev-test-run")]["status"] == Status.ASSERTED   # the account is kept
    e = wm.explain(w, "has-quality", OPERATIONAL, g.AFTER)
    assert all(c["applies"] is False for i in e["initiated_by"] for c in i["causes"])


def test_description_and_occurrence_level_claims_do_not_dispute_each_other(fresh):
    wm, w, _ = fresh
    wm.accept(wm.claim_cause(w, "o-bearing-replacement", "o-test-run", polarity=False, attester="cm-1"))
    c = {(x["cause"], x["effect"]): x for x in wm.causes_of(w, "o-test-run", g.AFTER)}
    assert c[("o-bearing-replacement", "o-test-run")]["judgement"] == "disputed"
    assert c[("ev-worklog-replacement", "ev-test-run")]["judgement"] == "accepted"   # F-B1: distinct contents
