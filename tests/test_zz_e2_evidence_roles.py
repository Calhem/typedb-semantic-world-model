"""Stage E2 harness, LABS-1.063: evidence roles, fixture-level names, premise admissibility and blocked dependencies.

Harness mechanics only, on synthetic fixtures (tests/fixtures/e2/). The expected roles are those the approved reader
contracts give (benchmark/e2/spec/reader-contracts.md, part 6 of each reader, with the LABS-1.063 qualifications).
They are checked against the readers' **actual normalised outputs**, not only against hand-written dictionaries
(supplement finding 7). No E2 question or gold is written here.
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
ROLES_FX = json.loads((HERE / "evidence-roles.json").read_text())
SYN_FX = json.loads((HERE / "harness-synthetic.json").read_text())


@pytest.fixture(scope="module")
def roles(driver):
    L = load(ROLES_FX, driver)
    yield L, fixture_names(L, ROLES_FX)[0]
    drop(L)


@pytest.fixture(scope="module")
def syn(driver):
    L = load(SYN_FX, driver)
    yield L, fixture_names(L, SYN_FX)[0]
    drop(L)


def extract(L, names, reader, **params):
    out = run_plan(L, {"plan": [{"step": "s", "reader": reader, "params": {"world": "w", **params}}]}, True)
    assert "error" not in out and "plan_error" not in out, out
    st = out["steps"][0]
    return st["answer"], {r: sorted(names[i] for i in st["cited"][r]) for r in EV.ROLES}, st["cited"]


# ---- names (H-1) ------------------------------------------------------------------------------------------------------
def test_every_recorded_attestation_gets_a_deterministic_fixture_name(roles, syn):
    for (L, names), fx in ((roles, ROLES_FX), (syn, SYN_FX)):
        got, _, recorded = fixture_names(L, fx)
        assert recorded <= set(got), sorted(recorded - set(got))        # nothing unattributed
        assert len(set(got.values())) == len(got)                      # one attestation per name
    names = syn[1]
    assert {"m1", "m1/activity", "m1/kind:measurement", "m1/produced", "m1/reports"} <= set(names.values())
    assert {"ev-s2", "ev-s2/kind:action", "ev-s2/describes", "ev-s1", "ev-s1/kind:action"} <= set(names.values())


# ---- extractors on real reader outputs (supplement finding 7) --------------------------------------------------------
def test_holds_constraint_dispute_and_polarity_dispute(roles):
    L, names = roles
    a, r, _ = extract(L, names, "holds", type="office-holding", roles={"classified": "bea", "class": "sm",
                                                                         "context": "depot-7"}, t="T3")
    assert a["status"] == "DISPUTED" and r["supporting"] == ["a-bea"] and r["conflicting"] == ["a-cal", "x-sm"]
    a, r, _ = extract(L, names, "holds", type="depends-on", roles={"dependent": "box", "dependee": "pump"}, t="T3")
    assert a["status"] == "DISPUTED"
    assert r["supporting"] == ["dep"] and r["conflicting"] == ["not-dep"]        # the accepted denial conflicts


def test_mutually_exclusive_positive_claims_keep_their_conflict_relationship(roles):
    """P-VA-1 as qualified: two values of one slot, both positive claims: conflicting, not supporting."""
    L, names = roles
    a, r, _ = extract(L, names, "value_at", type="located-at", subject="box", t="T3")
    assert a["status"] == "DISPUTED" and sorted(a["values"]) == ["dock", "shelf"]
    assert r["supporting"] == [] and r["conflicting"] == ["at-dock", "on-shelf"]
    # polarity alone is insufficient: both rivals are positive (polarity true) and still conflict
    pol = {e["attestation"]: e["polarity"] for e in a["evidence"]}
    assert all(pol[i] is True for i in a["support"])


def test_office_holders_keeps_support_and_the_conflict_between_holders(roles):
    """P-OH-1 as qualified (finding 2): each established appointment's claims support it, and the same claims conflict
    with the rival holder in the `conflict` component; the constraint conflicts."""
    L, names = roles
    a, r, cited = extract(L, names, "office_holders", office="sm", context="depot-7", t="T3")
    assert a["conflict"] is not None
    assert r["supporting"] == ["a-bea", "a-cal"] and r["conflicting"] == ["a-bea", "a-cal", "x-sm"]
    comps = {(c, role, names[i]) for c, role, i in cited["entries"]}
    assert ("conflict", "conflicting", "a-bea") in comps and any(c.startswith("appointments[") and role == "supporting"
                                                                 and n == "a-bea" for c, role, n in comps)
    assert EV.alternatives_as_support(cited) == []                  # different roles in different components: legitimate


def test_incompatible_measurements_conflict(roles):
    L, names = roles
    a, r, _ = extract(L, names, "compare_measurements", bearer="box", quality="mass")
    assert a["status"] == "DISPUTED" and r["conflicting"] == ["m1", "m2"] and r["supporting"] == []


def test_accepted_but_non_applicable_causal_claim_is_an_alternative(roles):
    """P-CO-1 (finding 1): a claim whose cause occurrence is denied does not apply: alternative, never supporting."""
    L, names = roles
    a, r, _ = extract(L, names, "causes_of", effect="ev-d", t="T9")
    assert [(c["judgement"], c["applies"]) for c in a] == [("accepted", False)]
    assert r["alternative"] == ["c-causes-d"] and r["supporting"] == [] and r["conflicting"] == []


def test_listing_dispute_sides(roles, syn):
    L, names = roles
    _, r, _ = extract(L, names, "facts_about", subject="box", t="T3")
    assert "not-dep" in r["conflicting"] and "dep" in r["supporting"]
    L, names = syn
    a, r, _ = extract(L, names, "where", thing="crate", frame="A", t="T3")
    assert a["status"] == "DISPUTED" and r["conflicting"] == ["crate-in-a-1", "crate-in-a-2"]
    assert r["alternative"] == ["crate-in-b-params"] and r["supporting"] == []    # unreviewed: alternative only
    _, r, _ = extract(L, names, "poses", thing="crate", t="T3")
    assert r["conflicting"] == ["crate-in-a-1", "crate-in-a-2"]


@pytest.mark.parametrize("reader, params, supporting", [
    ("where", {"thing": "box", "frame": "A", "t": "T3"}, ["ab", "bc", "box-in-c"]),
    ("transform_between", {"source": "C", "target": "A", "t": "T3"}, ["ab", "bc"]),
    ("frame_info", {"frame": "C", "t": "T3"}, ["bc"]),
    ("measurements", {"bearer": "box", "quality": "mass"}, ["m1", "m2"]),
    ("compare_measurements", {"bearer": "box", "quality": "mass"}, ["m1", "m2"]),
    ("measurement_calibration", {"bearer": "box", "quality": "mass"}, ["m1", "m2"]),
    ("causes_of", {"effect": "ev-s2", "t": "T9"}, ["s1-causes-s2"]),
    ("effects_of", {"event": "ev-s2", "t": "T9"}, ["box-on-shelf", "s2-puts-box"]),
    ("explain", {"type": "located-at", "roles": {"located": "box", "place": "shelf"}, "t": "T9"},
     ["box-on-shelf", "s1-causes-s2"]),
    ("changes", {"subject": "box", "t1": "T1", "t2": "T9"}, ["box-in-c", "box-on-shelf"]),
    ("process_steps", {"process": "o-proc", "t": "T9"}, ["s1-in-proc", "s2-in-proc"]),
    ("interval", {"description": "ev-s1"}, ["ev-s1"]),
    ("holds", {"type": "located-at", "roles": {"located": "box", "place": "shelf"}, "t": "T9"}, ["box-on-shelf"]),
    ("value_at", {"type": "located-at", "subject": "box", "t": "T9"}, ["box-on-shelf"]),
    ("facts_about", {"subject": "box", "t": "T9"}, ["box-on-shelf"]),
    ("occurrence", {"occurrence": "o-s2"}, ["ev-s2"]),
    ("occurrence_status", {"occurrence": "o-s1", "t": "T9"}, []),
    ("calibration_status", {"instrument": "scale", "t": "T3"}, []),
])
def test_extractors_on_real_undisputed_answers(syn, reader, params, supporting):
    L, names = syn
    _, r, cited = extract(L, names, reader, **params)
    assert r["supporting"] == supporting and r["conflicting"] == [] and r["undetermined"] == []
    assert all(i in names for role in EV.ROLES for i in cited[role])     # every cited id is a recorded attestation


def test_extractor_field_names_match_real_outputs(syn, roles):
    """The answer fields the extractors read exist, with the documented nesting and status vocabulary."""
    L, names = syn
    w, _, _ = extract(L, names, "where", thing="crate", frame="A", t="T3")
    c = w["candidates"][0]
    assert {"position_support", "chain", "verified", "x", "status", "search"} <= set(c)
    assert w["conflict_details"] and {"pair", "unverified"} <= set(w["conflict_details"][0])
    tb, _, _ = extract(L, names, "transform_between", source="C", target="A", t="T3")
    assert {"support", "disputed"} <= set(tb["chain"][0]) and "verified" in tb["search"]
    co, _, _ = extract(L, names, "causes_of", effect="ev-s2", t="T9")
    assert {"judgement", "applies", "attestations"} <= set(co[0])
    assert {"attestation", "acceptance", "polarity"} <= set(co[0]["attestations"][0])
    L, names = roles
    oh, _, _ = extract(L, names, "office_holders", office="sm", context="depot-7", t="T3")
    assert {"judgement", "evidence"} <= set(oh["appointments"][0]) and "attestations" in oh["conflict"]["appointments"][0]
    assert oh["conflict"]["constraint"]["support"]
    statuses = {"STIPULATED", "ASSERTED", "INFERRED", "DISPUTED", "UNKNOWN", "NOT_YET_KNOWN"}
    for reader, p in (("holds", {"type": "depends-on", "roles": {"dependent": "box", "dependee": "pump"}, "t": "T3"}),
                      ("value_at", {"type": "located-at", "subject": "box", "t": "T3"})):
        a, _, _ = extract(L, names, reader, **p)
        assert a["status"] in statuses and all({"attestation", "polarity"} <= set(e) for e in a["evidence"])


# ---- no permissive defaults (finding 3) ---------------------------------------------------------------------------------
def test_where_never_promotes_unverified_candidates_or_pairs():
    a = {"status": "DISPUTED", "candidates": [
        {"x": [0, 1], "position_support": ["p1"], "chain": [], "status": "ASSERTED"},              # no verified flag
        {"x": [5, 5], "position_support": ["p2"], "chain": [], "status": "ASSERTED", "verified": True},
        {"x": [9, 9], "position_support": ["p3"], "chain": [], "status": "ASSERTED", "verified": True}],
         "conflicts": [[1, 2]], "conflict_details": [{"pair": [1, 2]}], "incomparable": [], "alternatives": []}
    ev = EV.ev_where(a)
    assert ev["alternative"] == {"p1"}                    # a missing verified flag is unverified
    assert ev["conflicting"] == set() and ev["supporting"] == {"p2", "p3"}   # a pair without unverified:false is no pair
    a["conflict_details"] = [{"pair": [1, 2], "unverified": False}]
    assert EV.ev_where(a)["conflicting"] == {"p2", "p3"}
    tb = {"status": "INFERRED", "chain": [{"support": ["e1"]}], "search": {}}  # no disputed / verified flags
    assert EV.ev_transform_between(tb)["supporting"] == set() and EV.ev_transform_between(tb)["conflicting"] == {"e1"}


# ---- scoring: missing, inadmissible conflicting, unattributed, undetermined -----------------------------------------
NAMES = {"att:a": "a", "att:b": "b", "att:c": "c", "att:d": "d"}


def run_with(cited, derivations=()):
    return {"run": {"steps": [{"step": "s1", "reader": "r", "answer": {"status": "DISPUTED"}, "cited": cited,
                               "derivations": list(derivations), "ms": 1.0}], "ms": 1.0}}


def question(**kw):
    return {"id": "X-1", "family": "X", "class": "H", "scenario": "x",
            "plan": [{"step": "s1", "reader": "holds", "params": {}, "expected": {"status": "DISPUTED"}}], **kw}


def cited(**roles):
    out = {r: sorted(roles.get(r, [])) for r in EV.ROLES}
    out["entries"] = [["answer", r, i] for r in EV.ROLES for i in roles.get(r, [])]
    return out


def test_missing_required_evidence_cannot_pass():
    q = question(required_evidence=["a"], admissible_evidence=["a"], admissible_conflict_evidence=[])
    r = SC.score(q, run_with(cited()), run_with(cited()), NAMES, set(NAMES), 5)
    sup = r["evidence"]["supporting"]
    assert "missing-evidence" in r["failures"] and sup["recall"] == 0.0 and sup["precision"] is None
    s = REP.summarise([r])
    assert s["all"]["evidence"]["supporting"]["no_evidence_returned"] == 1
    rows = {c["criterion"]: c["verdict"] for c in s["criteria"]}
    assert rows["supporting evidence recall X"] == "fail"
    assert rows["evidence precision (supporting evidence)"] == "n/a"       # undefined, never a pass


def test_inadmissible_conflicting_evidence_is_detected():
    q = question(admissible_evidence=["a"], required_conflict_evidence=["b"], admissible_conflict_evidence=["b"])
    run = run_with(cited(supporting=["att:a"], conflicting=["att:b", "att:c"]))
    r = SC.score(q, run, run, NAMES, set(NAMES), 5)
    con = r["evidence"]["conflicting"]
    assert "inadmissible-conflict-evidence" in r["failures"] and con["inadmissible"] == ["c"]
    assert con["recall"] == 1.0 and r["evidence"]["supporting"]["precision"] == 1.0   # roles scored apart
    rows = {c["criterion"]: c["verdict"] for c in REP.summarise([r])["criteria"]}
    assert rows["inadmissible conflicting evidence"] == "fail"
    q2 = question(admissible_evidence=["a"], required_conflict_evidence=["d"], admissible_conflict_evidence=["d"])
    assert "missing-conflict-evidence" in SC.score(q2, run, run, NAMES, set(NAMES), 5)["failures"]


def test_unattributed_evidence_prevents_verified_precision():
    q = question(admissible_evidence=["a"], admissible_conflict_evidence=[])
    run = run_with(cited(supporting=["att:a", "att:unnamed"]))
    r = SC.score(q, run, run, NAMES, set(NAMES), 5)
    sup = r["evidence"]["supporting"]
    assert sup["precision"] == 1.0 and sup["precision_verified"] is False and "unattributed-evidence" in r["failures"]
    assert r["correct"] is True                                          # not an answer failure
    rows = {c["criterion"]: c["verdict"] for c in REP.summarise([r])["criteria"]}
    assert rows["evidence precision (supporting evidence)"] == "unverified"


def test_undetermined_evidence_cannot_improve_a_score():
    """Supplement finding 5: evidence in the undetermined role neither finds a required attestation nor counts in
    precision, whichever result that would have favoured."""
    q = question(required_evidence=["a"], admissible_evidence=["a"], admissible_conflict_evidence=[])
    only_undetermined = run_with(cited(undetermined=["att:a"]))
    r = SC.score(q, only_undetermined, only_undetermined, NAMES, set(NAMES), 5)
    assert "missing-evidence" in r["failures"] and r["evidence"]["supporting"]["found"] == []
    assert r["evidence"]["undetermined"] == ["a"]
    q2 = question(admissible_evidence=["a"], admissible_conflict_evidence=[])
    mixed = run_with(cited(supporting=["att:a", "att:b"], undetermined=["att:a"]))
    r2 = SC.score(q2, mixed, mixed, NAMES, set(NAMES), 5)
    assert r2["evidence"]["supporting"]["precision"] == 0.5          # b stays inadmissible; a counts once


def test_calibration_not_yet_effective_evidence_is_supporting():
    """SD-MEA-5 (approved LABS-1.064): the accepted future claim decides "not yet effective", so it is supporting; an
    unaccepted one stays an alternative. Was `undetermined` while the decision was open (LABS-1.063)."""
    r = {"judgement": "not yet effective", "support": [], "certificates": [
        {"certificate": "c1", "evidence": [{"attestation": "att:x", "acceptance": "accepted"},
                                           {"attestation": "att:y", "acceptance": "unreviewed"}]}]}
    ev = EV.ev_calibration_status(r)
    assert ev["supporting"] == {"att:x"} and ev["alternative"] == {"att:y"}
    assert ev["undetermined"] == set() and ev["conflicting"] == set()


def test_cross_role_membership_and_alternative_as_support():
    """Finding 4: one attestation may hold different roles in different components (legitimate), and counts once per
    role; listed as an alternative and as supporting in the same component it is a failure."""
    q = question(admissible_evidence=["a"], admissible_conflict_evidence=["a"])
    ok = {"supporting": ["att:a"], "conflicting": ["att:a"], "alternative": [], "undetermined": [],
          "entries": [["appointments[0]", "supporting", "att:a"], ["conflict", "conflicting", "att:a"],
                      ["appointments[1]", "supporting", "att:a"]]}
    r = SC.score(q, run_with(ok), run_with(ok), NAMES, set(NAMES), 5)
    assert r["failures"] == [] and r["evidence"]["supporting"]["cited"] == ["a"]
    bad = {**ok, "alternative": ["att:a"], "entries": ok["entries"] + [["appointments[0]", "alternative", "att:a"]]}
    r = SC.score(q, run_with(bad), run_with(bad), NAMES, set(NAMES), 5)
    assert "alternative-as-support" in r["failures"]
    assert r["evidence"]["alternative_as_support"] == [["s1", "appointments[0]", "a"]]


# ---- checker: established discrepancies eligible; unresolved dependencies refused (H-8 as amended) -----------------
FIXTURES = {SYN_FX["id"]: SYN_FX}
BLOCKED = [{"id": "SD-S-4", "question": "where.judgement vocabulary", "reader": "where", "paths": ["judgement"]},
           {"id": "SD-M-5", "question": "not-yet-effective evidence", "reader": "calibration_status",
            "paths": ["judgement"], "when": {"judgement": "not yet effective"}}]


def scored(qid, steps, **kw):
    base = {"id": qid, "family": "F", "class": "H", "scenario": SYN_FX["id"], "plan": steps,
            "admissible_evidence": [], "admissible_conflict_evidence": [], "admissible_premises": []}
    return {**base, **kw}


def wh(expected):
    return {"step": "s1", "reader": "where", "params": {"world": "w", "thing": "box", "frame": "A", "t": "T3"},
            "expected": expected}


def test_established_contract_discrepancies_remain_eligible():
    """D-WH-3 (reproduced DX-1) is a semantic defect against an established contract: a question expecting the
    contract's answer is accepted, although the current implementation is expected to fail it."""
    q = scored("F-1", [wh({"status": "DISPUTED"})], notes="D-WH-3: the contract's DISPUTED")
    assert C.problems_of(q, FIXTURES, set(), blocked=BLOCKED) == []


def test_unresolved_semantic_dependencies_are_refused():
    by_path = C.problems_of(scored("F-2", [wh({"judgement": "compatible"})]), FIXTURES, set(), blocked=BLOCKED)
    assert any("SD-S-4" in p and "blocked" in p for p in by_path)
    by_dep = C.problems_of(scored("F-3", [wh({"status": "INFERRED"})], depends_on=["SD-S-4"]), FIXTURES, set(),
                           blocked=BLOCKED)
    assert any("depends on SD-S-4" in p for p in by_dep)
    cs = {"step": "s1", "reader": "calibration_status", "params": {"world": "w", "instrument": "scale", "t": "T3"}}
    hit = C.problems_of(scored("M-1", [{**cs, "expected": {"judgement": "not yet effective"}}]), FIXTURES, set(),
                        blocked=BLOCKED)
    miss = C.problems_of(scored("M-2", [{**cs, "expected": {"judgement": "established"}}]), FIXTURES, set(),
                         blocked=BLOCKED)
    assert any("SD-M-5" in p for p in hit) and miss == []                 # only the blocked value is refused


def test_checker_requires_both_role_sets_and_premises():
    q = scored("F-4", [wh({"status": "INFERRED"})])
    for k in ("admissible_evidence", "admissible_conflict_evidence", "admissible_premises"):
        bad = {x: v for x, v in q.items() if x != k}
        assert any(k in p for p in C.problems_of(bad, FIXTURES, set(), blocked=[])), k


def test_the_shipped_blocked_list_is_well_formed():
    """LABS-1.064: only ONT-SC-1 is still open; the approved-but-unimplemented paths name their decision and DI."""
    from evaluation.e2.readers import READERS
    blocked, unimpl = C.load_blocked(), C.load_unimplemented()
    assert [b["id"] for b in blocked] == ["ONT-SC-1"]
    assert unimpl, "benchmark/e2/spec/blocked.json lists the approved paths no reader provides yet"
    for b in unimpl:
        assert b["id"].startswith("SD-") and b["di"].startswith("DI-") and b["question"] and b["paths"]
        assert b["reader"] in READERS


def test_approved_decisions_unblock_their_questions():
    """The LABS-1.063 blocks are lifted where the approved contract is unambiguous (LABS-1.064 item 17)."""
    blocked, unimpl = C.load_blocked(), C.load_unimplemented()
    ef = {"step": "s1", "reader": "effects_of", "params": {"world": "w", "event": "ev-s2", "t": "T9"},
          "expected": {"[0].state.accepted_change": True}}
    tol = {**wh({"status": "INFERRED"}), "params": {**wh({})["params"], "angle_tolerance": 0.1}}
    label = wh({"judgement": "compatible"})
    for q in (scored("C-1", [ef], family="C"), scored("F-5", [tol]), scored("F-6", [label])):
        assert C.problems_of(q, FIXTURES, set(), blocked=blocked, unimplemented=unimpl) == [], q["id"]
