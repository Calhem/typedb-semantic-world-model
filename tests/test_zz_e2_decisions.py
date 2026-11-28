"""Stage E2 harness, LABS-1.064: the approved semantic decisions in the harness (item 21).

Harness mechanics only. The fixtures (tests/fixtures/e2/) are synthetic self-test fixtures, never E2 evaluation
fixtures or gold. Where a check concerns what a reader presents, it runs against the reader's **actual normalised
output**, not only a hand-written answer (LABS-1.063 supplement finding 7).

Item 21 checks:
- (a) mathematical conventions do not generate fabricated derivations (SD-SPA-2);
- (b) accepted future calibration claims can support a not-yet-effective judgement (SD-MEA-5);
- (c) ambiguous causal attribution cannot be scored as unique causation (SD-CAU-1, checker rule H-9);
- (d) missing evidence cannot be reconstructed from fixture expectations;
- (e) evidence roles remain component-specific;
- (f) unverified evidence cannot produce a verified precision pass.
Plus the decisions' checker consequences: approved-but-unimplemented paths are G probes only (item 19), probes may
accept an absent field, occurrence inputs are a precondition (SD-CORE-4), `value_at` takes both roles (SD-CORE-2), and
targeted defect coverage is reported apart (item 26).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.e2 import check as C, evidence as EV, report as REP, score as SC  # noqa: E402
from evaluation.e2.names import fixture_names  # noqa: E402
from evaluation.e2.plan import run_plan  # noqa: E402
from evaluation.loader import drop, load  # noqa: E402

pytestmark = pytest.mark.own_profiles
HERE = Path(__file__).resolve().parent / "fixtures" / "e2"
DEC_FX = json.loads((HERE / "decisions.json").read_text())
ROLES_FX = json.loads((HERE / "evidence-roles.json").read_text())
FIXTURES = {DEC_FX["id"]: DEC_FX, ROLES_FX["id"]: ROLES_FX}


@pytest.fixture(scope="module")
def dec(driver):
    L = load(DEC_FX, driver)
    yield L, fixture_names(L, DEC_FX)[0]
    drop(L)


@pytest.fixture(scope="module")
def roles(driver):
    L = load(ROLES_FX, driver)
    yield L, fixture_names(L, ROLES_FX)[0]
    drop(L)


def run(L, q):
    """Both 'paths' are the same in-process run here: these tests check scoring, not path agreement."""
    out = run_plan(L, q, True)
    return {"run": out}


def scored(qid, steps, scenario=DEC_FX["id"], **kw):
    base = {"id": qid, "family": "S", "class": "H", "scenario": scenario, "plan": steps,
            "admissible_evidence": [], "admissible_conflict_evidence": []}
    return {**base, **kw}


def step(reader, expected=None, **params):
    s = {"step": "s1", "reader": reader, "params": {"world": "w", **params}}
    if expected is not None:
        s["expected"] = expected
    return s


IDENTITY = {"status": "INFERRED", "transform.t": [0.0, 0.0, 0.0], "transform.q": [1.0, 0.0, 0.0, 0.0]}


# ---- (a) conventions present no derivation -----------------------------------------------------------------------------
def test_a_frame_to_itself_must_be_marked_as_a_convention():
    st = step("transform_between", IDENTITY, source="A", target="A", t="T3")
    unmarked = C.problems_of(scored("S-1", [st], admissible_premises=[]), FIXTURES, set())
    assert any("convention-derived" in p for p in unmarked)
    marked = scored("S-2", [st], convention="frame-identity", admissible_premises=[])
    assert C.problems_of(marked, FIXTURES, set()) == []
    leaky = scored("S-3", [st], convention="frame-identity", admissible_premises=["ab"], admissible_evidence=["ab"])
    probs = C.problems_of(leaky, FIXTURES, set())
    assert any("admissible_premises must be []" in p for p in probs)
    assert any("admissible_evidence must be []" in p for p in probs)
    wrong = scored("S-4", [step("transform_between", IDENTITY, source="A", target="D", t="T3")],
                   convention="frame-identity", admissible_premises=[])
    assert any("no transform_between step asks for a frame to itself" in p for p in C.problems_of(wrong, FIXTURES, set()))


def test_the_current_identity_answer_is_a_fabricated_derivation(dec):
    """The reader names frame-transform/v1 for A -> A with an empty chain: a premise-less derivation, which SD-SPA-2
    forbids. The harness extracts it and scores it fabricated; the question stays eligible (it fails)."""
    L, names = dec
    q = scored("S-5", [step("transform_between", IDENTITY, source="A", target="A", t="T3")],
               convention="frame-identity", admissible_premises=[])
    sel = run(L, q)
    assert sel["run"]["steps"][0]["derivations"] == [{"rule": "frame-transform/v1", "at": "transform", "premises": []}]
    r = SC.score(q, sel, sel, names, set(names), 5, fixture=DEC_FX)
    assert "fabricated-derivation" in r["failures"]
    assert "no premises" in r["fabricated"][0]["why"] and "declared convention" in r["fabricated"][0]["why"]


def test_a_convention_answer_without_derivation_passes_and_any_derivation_fails():
    q = {**scored("S-6", [step("transform_between", IDENTITY, source="A", target="A", t="T3")],
                  convention="frame-identity", admissible_premises=[])}
    answer = {"status": "INFERRED", "transform": {"t": [0.0, 0.0, 0.0], "q": [1.0, 0.0, 0.0, 0.0]}, "chain": []}
    none = {"run": {"steps": [{"step": "s1", "reader": "transform_between", "answer": answer, "derivations": [],
                               "cited": {r: [] for r in EV.ROLES} | {"entries": []}}], "ms": 1.0}}
    assert SC.score(q, none, none, {}, set(), 5, fixture=DEC_FX)["failures"] == []
    # even a derivation with visible, applicable premises is fabricated for a convention-derived result
    q2 = {**q, "admissible_premises": []}
    invented = {"run": {"steps": [{**none["run"]["steps"][0],
                                   "derivations": [{"rule": "frame-transform/v1", "at": "transform",
                                                    "premises": ["ab"]}]}], "ms": 1.0}}
    r = SC.score(q2, invented, invented, {"ab": "ab"}, {"ab"}, 5, fixture=DEC_FX)
    assert "fabricated-derivation" in r["failures"] and "declared convention" in r["fabricated"][0]["why"]


def test_an_evidence_derived_inference_keeps_its_premises(dec):
    L, names = dec
    q = scored("S-7", [step("transform_between", {"status": "INFERRED", "transform.t": [-1.0, -2.0, -3.0]},
                            source="A", target="D", t="T3")],
               admissible_evidence=["ab", "bc", "cd"], required_evidence=["ab", "bc", "cd"],
               admissible_premises=["ab", "bc", "cd"], tolerance=None)
    q["plan"][0]["tolerance"] = {"transform.t": 1e-9}
    del q["tolerance"]
    assert C.problems_of(q, FIXTURES, set()) == []
    sel = run(L, q)
    r = SC.score(q, sel, sel, names, set(names), 5, fixture=DEC_FX)
    assert r["failures"] == [] and r["evidence"]["supporting"]["recall"] == 1.0


# ---- (b) a not-yet-effective calibration rests on the accepted future claim -------------------------------------------
def test_accepted_future_calibration_claim_supports_not_yet_effective(dec):
    L, names = dec
    q = {**scored("M-1", [step("calibration_status", {"judgement": "not yet effective"}, instrument="gauge", t="T3")],
                  family="M"), "required_evidence": ["cal-later"], "admissible_evidence": ["cal-later"]}
    assert C.problems_of(q, FIXTURES, set()) == []            # no longer blocked (SD-MEA-5 approved)
    sel = run(L, q)
    assert sel["run"]["steps"][0]["answer"]["support"] == []    # the reader's support field stays empty
    r = SC.score(q, sel, sel, names, set(names), 5, fixture=DEC_FX)
    assert r["failures"] == [] and r["evidence"]["supporting"]["found"] == ["cal-later"]


# ---- (c) ambiguous attribution never passes as unique causation -------------------------------------------------------
def test_changes_reports_the_ambiguous_attribution_of_a_claim_fitting_two_activations(dec):
    L, names = dec
    out = run_plan(L, {"plan": [step("changes", subject="box", t1="T1", t2="T9")]}, True)
    exps = [e for tr in out["steps"][0]["answer"]["transitions"] for e in tr.get("explanations", [])]
    assert exps and {e["attribution"] for e in exps if e["event"] == "ev-put"} == {"ambiguous"}


def test_checker_requires_the_attribution_of_every_explanation_a_question_inspects():
    ch = lambda expected: step("changes", expected, subject="box", t1="T1", t2="T9")
    base = dict(family="C", admissible_evidence=["on-shelf-1"], admissible_conflict_evidence=[])
    only_event = scored("C-1", [ch({"transitions[0].explanations[event=ev-put].event": "ev-put"})], **base)
    assert any("H-9" in p for p in C.problems_of(only_event, FIXTURES, set()))
    with_attr = scored("C-2", [ch({"transitions[0].explanations[event=ev-put].event": "ev-put",
                                   "transitions[0].explanations[event=ev-put].attribution": "ambiguous"})], **base)
    whole = scored("C-3", [ch({"transitions[0].explanations": []})], **base)
    assert C.problems_of(with_attr, FIXTURES, set()) == [] and C.problems_of(whole, FIXTURES, set()) == []


def test_a_unique_attribution_claim_fails_against_the_real_ambiguous_answer(dec):
    L, names = dec
    path = "transitions[0].explanations[event=ev-put].attribution"
    q = scored("C-4", [step("changes", {path: "unique"}, subject="box", t1="T1", t2="T9")], family="C",
               admissible_evidence=["on-shelf-1", "on-shelf-2"])
    sel = run(L, q)
    r = SC.score(q, sel, sel, names, set(names), 5, fixture=DEC_FX)
    assert "incorrect" in r["failures"] and r["wrong_fields"][0]["path"] == path


def test_effects_of_accepted_change_is_eligible_and_its_attribution_is_a_probe():
    ef = lambda expected: step("effects_of", expected, event="ev-put", t="T9")
    q = scored("C-5", [ef({"[0].state.accepted_change": True})], family="C")
    assert C.problems_of(q, FIXTURES, set()) == []
    attr = scored("C-6", [ef({"[0].attribution": "unique"})], family="C")
    assert any("SD-CAU-1" in p and "DI-35" in p and "G probe" in p for p in C.problems_of(attr, FIXTURES, set()))


# ---- (d) missing evidence is never reconstructed from the fixture or the gold ----------------------------------------
def test_missing_evidence_is_not_reconstructed_from_fixture_expectations(dec):
    """The fixture records cd and the question requires it, and the expected answer even names it; the answer does not
    cite it, so it is missing. Evidence comes only from what the answer cites."""
    L, names = dec
    q = scored("S-8", [step("transform_between", {"status": "INFERRED", "chain[2].support": ["cd"]},
                            source="A", target="C", t="T3")],
               required_evidence=["ab", "bc", "cd"], admissible_evidence=["ab", "bc", "cd"],
               admissible_premises=["ab", "bc", "cd"])
    sel = run(L, q)
    assert "cd" in names.values()                                     # the fixture recorded it
    r = SC.score(q, sel, sel, names, set(names), 5, fixture=DEC_FX)
    sup = r["evidence"]["supporting"]
    assert "missing-evidence" in r["failures"] and sup["found"] == ["ab", "bc"] and sup["recall"] == 0.667
    empty = {"run": {"steps": [{**sel["run"]["steps"][0], "cited": {x: [] for x in EV.ROLES} | {"entries": []}}],
                     "ms": 1.0}}
    r2 = SC.score(q, empty, empty, names, set(names), 5, fixture=DEC_FX)
    assert r2["evidence"]["supporting"]["recall"] == 0.0 and r2["evidence"]["supporting"]["precision"] is None


# ---- (e) roles are component-specific ---------------------------------------------------------------------------------
def test_roles_are_recorded_per_component_on_a_real_answer(roles):
    L, names = roles
    out = run_plan(L, {"plan": [step("office_holders", office="sm", context="depot-7", t="T3")]}, True)
    entries = out["steps"][0]["cited"]["entries"]
    by_id = {}
    for comp, role, i in entries:
        by_id.setdefault(names[i], set()).add((comp.split("[")[0], role))
    # each appointment's claim supports its appointment and conflicts in the office conflict: two components
    for a in ("a-bea", "a-cal"):
        assert ("appointments", "supporting") in by_id[a] and ("conflict", "conflicting") in by_id[a], by_id[a]
    assert EV.alternatives_as_support(out["steps"][0]["cited"]) == []


# ---- (f) unverified evidence never gives a verified precision pass ---------------------------------------------------
def test_unverified_candidate_evidence_cannot_pass_precision():
    """A truncated (unverified) chain's support is an alternative, never supporting: precision stays undefined (n/a),
    not a pass, even when every cited id is admissible."""
    a = {"status": "UNKNOWN", "transform": {"t": [1, 2, 0], "q": [1, 0, 0, 0]},
         "chain": [{"support": ["att:a"], "disputed": False}], "search": {"verified": False, "truncated": True}}
    ev = EV.ev_transform_between(a)
    assert ev["supporting"] == set() and ev["alternative"] == {"att:a"}
    cited = EV.as_lists(ev)
    q = scored("S-9", [step("transform_between", {"status": "UNKNOWN"}, source="A", target="C", t="T3")],
               admissible_evidence=["a"], admissible_premises=[])
    run_ = {"run": {"steps": [{"step": "s1", "reader": "transform_between", "answer": a, "cited": cited,
                               "derivations": [], "ms": 1.0}], "ms": 1.0}}
    r = SC.score(q, run_, run_, {"att:a": "a"}, {"att:a"}, 5)
    assert r["evidence"]["supporting"]["precision"] is None
    rows = {c["criterion"]: c["verdict"] for c in REP.summarise([r])["criteria"]}
    assert rows["evidence precision (supporting evidence)"] != "pass"


def test_unattributed_evidence_keeps_precision_unverified():
    q = scored("S-10", [step("transform_between", {"status": "INFERRED"}, source="A", target="C", t="T3")],
               admissible_evidence=["a"], admissible_premises=[])
    cited = {"supporting": ["att:a", "att:unnamed"], "conflicting": [], "alternative": [], "undetermined": [],
             "entries": [["chain[0]", "supporting", "att:a"], ["chain[1]", "supporting", "att:unnamed"]]}
    run_ = {"run": {"steps": [{"step": "s1", "reader": "transform_between", "answer": {"status": "INFERRED"},
                               "cited": cited, "derivations": [], "ms": 1.0}], "ms": 1.0}}
    r = SC.score(q, run_, run_, {"att:a": "a"}, {"att:a"}, 5)
    assert r["evidence"]["supporting"]["precision_verified"] is False
    rows = {c["criterion"]: c["verdict"] for c in REP.summarise([r])["criteria"]}
    assert rows["evidence precision (supporting evidence)"] == "unverified"


# ---- approved but unimplemented: G probes only (item 19) --------------------------------------------------------------
def test_unimplemented_paths_are_refused_in_scored_questions_and_allowed_in_probes(dec):
    L, names = dec
    ex = step("explain", {"alternatives": []}, type="located-at", roles={"located": "box", "place": "shelf"}, t="T7")
    q = scored("C-7", [ex], family="C")
    assert any("SD-CAU-2" in p and "DI-29" in p for p in C.problems_of(q, FIXTURES, set()))
    probe = {"id": "G-1", "family": "C", "class": "G", "gap": "DI-29", "scenario": DEC_FX["id"],
             "plan": [{k: v for k, v in ex.items() if k != "expected"}],
             "probe": {"accept": ["absent"], "path": "alternatives"}}
    assert C.problems_of(probe, FIXTURES, set()) == []
    sel = run(L, probe)
    r = SC.score(probe, sel, sel, names, set(names), 5, fixture=DEC_FX)
    assert r["probe"] == "pass" and r["returned"] == "absent"
    strict = {**probe, "probe": {"accept": ["UNKNOWN"], "path": "alternatives"}}
    assert SC.score(strict, sel, sel, names, set(names), 5, fixture=DEC_FX)["passed"] is False


def test_occurrence_readers_take_occurrences_only():
    occ = lambda oid: scored("C-8", [step("occurrence_status", {"status": "accepted"}, occurrence=oid, t="T3")],
                             family="C")
    assert C.problems_of(occ("o-put"), FIXTURES, set()) == []
    assert any("SD-CORE-4" in p for p in C.problems_of(occ("box"), FIXTURES, set()))


def test_value_at_takes_both_roles_and_a_half_specified_call_is_eligible(dec):
    """SD-CORE-2: a half-specified call must be refused. The reader answers UNKNOWN today, so the eligible question
    fails as `incorrect`; the harness now passes the roles through."""
    L, names = dec
    q = scored("X-1", [step("value_at", {"refused": True}, type="located-at", subject="box", t="T3",
                            key_role="located")], family="X")
    assert C.problems_of(q, FIXTURES, set()) == []
    sel = run(L, q)
    r = SC.score(q, sel, sel, names, set(names), 5, fixture=DEC_FX)
    assert r["failures"] == ["incorrect"]


def test_targeted_defect_coverage_is_reported_apart():
    bad = scored("S-11", [step("transform_between", {"status": "INFERRED"}, source="A", target="C", t="T3")],
                 admissible_premises=[], targets=["D-WH-3"])
    assert any("targets" in p for p in C.problems_of(bad, FIXTURES, set()))
    recs = []
    for qid, tg in (("S-12", ["DI-25"]), ("S-13", [])):
        q = scored(qid, [step("transform_between", {"status": "INFERRED"}, source="A", target="C", t="T3")],
                   admissible_premises=[], targets=tg)
        run_ = {"run": {"steps": [{"step": "s1", "reader": "transform_between", "answer": {"status": "INFERRED"},
                                   "cited": {}, "derivations": [], "ms": 1.0}], "ms": 1.0}}
        recs.append(SC.score(q, run_, run_, {}, set(), 5))
    s = REP.summarise(recs)
    assert s["targeted"]["scheduled"] == 1 and s["targeted"]["by_di"] == {"DI-25": 1}
    assert s["competency"]["scheduled"] == 1 and s["families"]["S"]["scheduled"] == 2


# ---- LABS-1.065: uncertain time windows in fixture steps (harness only) -------------------------------------------------
WIN_FX = {"id": "e2-windows", "description": "LABS-1.065 harness self-test: uncertain windows. Synthetic; not E2.",
          "profiles": [], "steps": [
              {"op": "entity", "kind": "physical-object", "id": "tech"}, {"op": "entity", "kind": "occurrence", "id": "o-1"},
              {"op": "world", "id": "w", "kind": "actual"},
              {"op": "account", "id": "ev-1", "world": "w", "roles": {"actor": "tech"}, "start": ["T3", "T5"],
               "end": ["T6", "T6h12"], "occurrence": "o-1"}]}


def test_fixture_times_accept_windows_and_refuse_malformed_ones(driver):
    from evaluation.loader import FixtureError, T
    lo, hi = T(["T3", "T5h10"])
    assert (lo.day, hi.day, hi.hour) == (3, 5, 10)
    for bad in (["T5", "T3"], ["T3"], ["T3", "T4", "T5"]):
        with pytest.raises(FixtureError):
            T(bad)
    L = load(WIN_FX, driver)
    try:
        out = run_plan(L, {"plan": [step("interval", description="ev-1")]}, True)
        a = out["steps"][0]["answer"]
        assert a["start"]["earliest"].startswith("2026-11-03") and a["start"]["latest"].startswith("2026-11-05")
        assert a["end"]["latest"].startswith("2026-11-06T12")
    finally:
        drop(L)


def test_account_again_adds_a_second_account_to_one_description(driver):
    """LABS-1.065 loader step (harness only): two usable accounts of one description (SD-CAU-10)."""
    fx = {"id": "e2-accounts-selftest", "description": "synthetic", "profiles": [], "steps": [
        {"op": "entity", "kind": "physical-object", "id": "unit"}, {"op": "world", "id": "w", "kind": "actual"},
        {"op": "account", "id": "acc-x", "world": "w", "roles": {"patient": "unit"}, "start": "T3", "end": "T4"},
        {"op": "account_again", "id": "acc-y", "world": "w", "description": "acc-x", "start": ["T5", "T6"],
         "end": "T7"}]}
    L = load(fx, driver)
    try:
        assert len(L.written["acc-y"]) == 1 and L.written["acc-y"] != L.written["acc-x"]
        assert set(L.wm.account_attestations("w", "acc-x")) >= set(L.written["acc-x"]) | set(L.written["acc-y"])
    finally:
        drop(L)


def test_angle_tolerance_applies_to_each_rotation_in_a_list():
    """LABS-1.065: `candidates[*].orientation` with {"rad": x} compares every quaternion (q and -q alike)."""
    from evaluation.e2.values import matches
    tol = {"rad": 1e-9}
    assert matches([[1.0, 0, 0, 0], [0.96, 0, 0, 0.28]], [[0.96, 0, 0, 0.28], [-1.0, 0, 0, 0]], tol)
    assert not matches([[1.0, 0, 0, 0], [0.96, 0, 0, 0.28]], [[1.0, 0, 0, 0], [0.28, 0, 0, 0.96]], tol)
    assert matches([1.0, 0, 0, 0], [-1.0, 0, 0, 0], tol) and not matches([[1.0, 0, 0, 0]], [], tol)
