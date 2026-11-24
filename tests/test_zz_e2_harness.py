"""Stage E2 harness (LABS-1.061): the harness's own mechanics, on synthetic fixtures and questions only.

Nothing here is an E2 evaluation question or gold answer: the expected values below are what the harness must
reproduce from the readers it calls (or from the self-test readers, which misbehave on purpose), so that each failure
kind is shown to be detected and kept distinct. The E2 reader contracts, questions and gold are not written yet.
"""

import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.e2 import check as C, report as REP, score as SC, values as V  # noqa: E402
from evaluation.e2.plan import run_plan  # noqa: E402
from evaluation.e2.readers import READERS  # noqa: E402
from evaluation.e2.run import QuestionProblems, run  # noqa: E402
from evaluation.loader import FixtureError, drop, load  # noqa: E402

pytestmark = pytest.mark.own_profiles
FX = json.loads((Path(__file__).resolve().parent / "fixtures" / "e2" / "harness-synthetic.json").read_text())
FIXTURES = {FX["id"]: FX}
SID = FX["id"]
YAW90 = [math.cos(math.pi / 4), 0.0, 0.0, math.sin(math.pi / 4)]


def q(id, plan, family="S", cls="H", **kw):
    return {"id": id, "family": family, "class": cls, "scenario": SID, "plan": plan, **kw}


def step(reader, params, expected=None, name="s1", **kw):
    st = {"step": name, "reader": reader, "params": {"world": "w", **params} if not reader.startswith(("convert",
          "selftest")) else params}
    if expected is not None:
        st["expected"] = expected
    st.update(kw)
    return st


# ---- values: normalisation, paths, comparison (no database) ----------------------------------------------------------
def test_normalise_gives_plain_json():
    from datetime import datetime, timezone
    from worldmodel.semantics import Status, Window
    t = datetime(2026, 11, 3, 9, tzinfo=timezone.utc)
    got = V.normalise({"s": Status.DISPUTED, "w": Window(t, None), "tup": (1, 2), "set": {"b", "a"}, "_private": 1,
                       "nested": [{"_x": 0, "y": (t,)}]})
    assert got == {"s": "DISPUTED", "w": {"earliest": "2026-11-03T09:00:00+00:00", "latest": None}, "tup": [1, 2],
                   "set": ["a", "b"], "nested": [{"y": ["2026-11-03T09:00:00+00:00"]}]}
    json.dumps(got)


def test_paths_select_and_refuse():
    a = {"candidates": [{"x": [1, 1], "chain": [{"support": ["ab"]}]}, {"x": [2, 2], "chain": []}], "status": "OK"}
    assert V.select(a, "status") == "OK"
    assert V.select(a, "candidates[1].x") == [2, 2]
    assert V.select(a, "candidates[-1].x[0]") == 2
    assert V.select(a, "candidates[*].x[0]") == [1, 2]
    assert V.select([{"a": 1}], "[0].a") == 1
    rows = [{"record": "m2-result", "v": 2}, {"record": "m1-result", "v": 1}, {"n": 3, "v": 3}]
    assert V.select(rows, "[record=m1-result].v") == 1 and V.select(rows, "[n=3].v") == 3
    for bad in ("[record=m9].v", "[v=1]x"):
        with pytest.raises(V.PathError):
            V.select(rows + [{"record": "m1-result"}] if bad.startswith("[record") else rows, bad)
    for bad in ("nope", "candidates[2]", "status[0]", "candidates[*].nope"):
        with pytest.raises(V.PathError):
            V.select(a, bad)
    with pytest.raises(V.PathError):
        V.parse_path("a..b[")


def test_comparison_rules():
    assert V.matches(1.0, 1.0) and not V.matches(1.0, 1.0 + 1e-12)            # exact unless a tolerance is stated
    assert V.matches(1.0, 1.0 + 1e-12, 1e-9) and not V.matches(1.0, 1.1, 1e-9)
    assert V.matches([1.0, 2.0, 0.0], [1.0 + 1e-10, 2.0, 0.0], 1e-9)           # tolerance applies to every number
    assert V.matches(YAW90, [-c for c in YAW90], {"rad": 1e-9})                 # q and -q: the same rotation
    assert not V.matches(YAW90, [1.0, 0.0, 0.0, 0.0], {"rad": 1e-6})
    assert V.matches(["b", "a"], ["a", "b"]) and not V.matches(["b", "a"], ["a", "b"], ordered=True)
    assert not V.matches(["a", "a"], ["a", "b"])                                # a multiset, not a set
    assert V.matches([[1.0, 2.0], [3.0]], [[3.0], [1.0 + 1e-12, 2.0]], 1e-9)
    assert not V.matches({"a": 1}, {"a": 1, "b": 2})                            # same keys
    assert not V.matches(True, 1) and not V.matches(1, True) and not V.matches(None, "None")
    assert V.wrong_fields({"status": "X", "a.b": 1, "zz": 0}, {"status": "X", "a": {"b": 2}}) == [
        ("a.b", "different"), ("zz", "missing: answer: no field 'zz'")]


# ---- the question checker (no database) --------------------------------------------------------------------------------
def _problems(*qs, selftest=False):
    seen = set()
    return [p for x in qs for p in C.problems_of(x, FIXTURES, seen, selftest)]


def test_checker_accepts_a_well_formed_plan():
    good = q("X-1", [step("measurements", {"bearer": "box", "quality": "mass"}, name="m"),
                     step("where", {"thing": "box", "frame": "A", "t": {"from": "m", "path": "[0].valid[0].earliest"}},
                          {"status": "INFERRED"}, name="w")], family="X",
             required_evidence=["box-in-c"], admissible_evidence=["box-in-c", "ab", "bc", "m1"],
             forbidden_evidence=["crate-in-a-1"])
    probe = q("G-1", [], cls="G", gap="GAP-FRAME-3")
    assert _problems(good, probe) == []


@pytest.mark.parametrize("change, problem", [
    ({"plan": [step("nope", {})]}, "unknown reader"),
    ({"plan": [step("where", {"thing": "box"}, {"status": "X"})]}, "params missing ['frame', 't']"),
    ({"plan": [step("where", {"thing": "box", "frame": "A", "t": "T3", "colour": 1}, {"status": "X"})]},
     "unknown params ['colour']"),
    ({"plan": [step("where", {"thing": "box", "frame": "A", "t": {"from": "later", "path": "x"}}, {"s": 1})]},
     "not an earlier step"),
    ({"plan": [step("where", {"thing": "box", "frame": "A", "t": "T3"})]}, "needs an expected answer"),
    ({"plan": [step("where", {"thing": "box", "frame": "A", "t": "T3", "world": "nowhere"}, {"s": 1})]},
     "world 'nowhere'"),
    ({"plan": [step("where", {"thing": "box", "frame": "A", "t": "T3", "as_of": "@nomark"}, {"s": 1})]},
     "names no mark"),
    ({"plan": [step("where", {"thing": "box", "frame": "A", "t": "T3"}, {"s": 1}, tolerance={"s": -1})]},
     "tolerance for 's'"),
    ({"class": "G"}, "gap id is given exactly when"),
    ({"gap": "GAP-X"}, "gap id is given exactly when"),
    ({"subset": "identity"}, "only 'identity', in family X"),
    ({"family": "Q"}, "unknown family"),
    ({"required_evidence": ["ab"], "admissible_evidence": ["bc"]}, "required evidence must be admissible"),
    ({"admissible_evidence": ["ab"], "forbidden_evidence": ["ab"]}, "both forbidden and"),
    ({"required_evidence": ["no-such-step"]}, "names no fixture step"),
    ({"plan": [step("selftest_echo", {"value": 1}, {"value": 1})]}, "self-test reader"),
    ({"plan": []}, "needs a plan"),
])
def test_checker_refuses(change, problem):
    base = q("S-1", [step("where", {"thing": "box", "frame": "A", "t": "T3"}, {"status": "INFERRED"})])
    got = _problems({**base, **change})
    assert any(problem in p for p in got), got


def test_checker_refuses_a_probe_that_accepts_a_definite_answer():
    bad = q("G-1", [step("where", {"thing": "box", "frame": "A", "t": "T9"})], cls="G", gap="GAP-FRAME-3",
            probe={"accept": ["UNKNOWN", "INFERRED"]})
    assert any("a probe accepts only" in p for p in _problems(bad))


def test_every_e2_reader_has_a_template():
    needed = {"where", "transform_between", "poses", "frame_info", "measurements", "compare_measurements",
              "measurement_calibration", "causes_of", "effects_of", "explain", "changes", "process_steps", "before",
              "convert", "interval", "calibration_status"}                       # design 5.4 and section 2
    assert needed <= set(READERS)


# ---- scoring (no database): every failure kind on its own and together -------------------------------------------------
NAMES = {"att:1": "ab", "att:2": "bc"}
RECORDED = {"att:1", "att:2", "att:3"}


def sel_run(answer, cited=(), derivations=(), ms=10.0, **extra):
    return {"run": {"steps": [{"step": "s1", "reader": "r", "answer": answer, "cited": list(cited),
                               "derivations": list(derivations), "ms": ms}], "ms": ms, **extra}}


def sq(**kw):
    return q("S-1", [{"step": "s1", "reader": "where", "params": {}, "expected": {"status": "INFERRED"}}], **kw)


def test_score_correct_answer_and_agreement():
    sel = sel_run({"status": "INFERRED"}, ["att:1"])
    r = SC.score(sq(required_evidence=["ab"], admissible_evidence=["ab", "bc"]), sel, sel, NAMES, RECORDED, 5)
    assert (r["correct"], r["failures"], r["agreement"]) == (True, [], "agree")
    assert r["evidence"]["recall"] == 1.0 and r["evidence"]["precision"] == 1.0


def test_score_incorrect_answer():
    r = SC.score(sq(), sel_run({"status": "DISPUTED"}), sel_run({"status": "DISPUTED"}), NAMES, RECORDED, 5)
    assert (r["correct"], r["failure"]) == (False, "incorrect")
    assert r["wrong_fields"] == [{"step": "s1", "path": "status", "reason": "different"}]
    assert r["first_wrong_step"] == "s1"


def test_score_evidence_failures_are_distinct_and_do_not_hide_each_other():
    sel = sel_run({"status": "INFERRED"}, ["att:1", "att:3", "forbidden-step"])
    r = SC.score(sq(required_evidence=["bc"], admissible_evidence=["ab", "bc"], forbidden_evidence=["forbidden-step"]),
                 sel, sel, NAMES, RECORDED, 5)
    assert r["correct"] is True                                       # evidence is scored beside correctness
    assert r["failures"] == ["forbidden-evidence", "inadmissible-evidence", "missing-evidence"]
    assert r["evidence"]["inadmissible"] == ["att:3", "forbidden-step"]   # an unnamed id is never admissible
    assert r["evidence"]["precision"] == round(1 - 2 / 3, 3) and r["evidence"]["recall"] == 0.0


def test_score_fabricated_derivations():
    sel = sel_run({"status": "INFERRED"}, derivations=[
        {"rule": "made-up/v1", "premises": ["att:1"], "at": "a"},
        {"rule": "frame-transform/v1", "premises": ["att:999"], "at": "b"},
        {"rule": "frame-transform/v1", "premises": [], "at": "c"},
        {"rule": "frame-transform/v1", "premises": ["att:1", "att:2"], "at": "ok"}])
    r = SC.score(sq(), sel, sel, NAMES, RECORDED, 5)
    assert r["correct"] is True and r["failures"] == ["fabricated-derivation"]
    assert [f["at"] for f in r["fabricated"]] == ["a", "b", "c"]
    assert "not a rule the model records" in r["fabricated"][0]["why"]
    assert "not recorded" in r["fabricated"][1]["why"] and "no premises" in r["fabricated"][2]["why"]


def test_score_timeout_execution_plan_and_refusal_are_distinct():
    t = SC.score(sq(), {"timeout": 5, "wall_ms": 5001}, None, NAMES, RECORDED, 5, "the selective path timed out")
    assert (t["failure"], t["completed"], t["correct"], t["latency_ms"], t["latency_censored"]) == (
        "timeout", False, False, 5000.0, True)
    assert t["agreement"] == "unverified"
    err = {"run": {"steps": [{"step": "s1", "reader": "r", "error": "RuntimeError: x", "ms": 1}], "ms": 1,
                   "error": {"step": "s1", "message": "RuntimeError: x"}}}
    e = SC.score(sq(), err, err, NAMES, RECORDED, 5)
    assert (e["failure"], e["completed"], e["agreement"]) == ("execution-error", True, "agree")
    pe = {"run": {"steps": [{"step": "s1", "reader": "r", "plan_error": "no x"}], "ms": 0,
                  "plan_error": {"step": "s1", "message": "no x"}}}
    assert SC.score(sq(), pe, pe, NAMES, RECORDED, 5)["failure"] == "plan-error"
    ref = sel_run({"refused": True, "refusal": "ValueError: no"})
    assert SC.score(sq(), ref, ref, NAMES, RECORDED, 5)["failure"] == "unexpected-refusal"
    want_refusal = q("S-2", [{"step": "s1", "reader": "r", "params": {}, "expected": {"refused": True}}])
    assert SC.score(want_refusal, ref, ref, NAMES, RECORDED, 5)["correct"] is True
    h = SC.score(sq(), {"harness_error": "boom", "trace": ""}, None, NAMES, RECORDED, 5)
    assert (h["failure"], h["completed"]) == ("harness-error", False)


def test_agreement_states():
    a, b = sel_run({"status": "INFERRED"}), sel_run({"status": "DISPUTED"})
    assert SC.agreement(a, a)[0] == "agree"
    assert SC.agreement(a, b) == ("disagree", "the answers differ")
    assert SC.agreement(a, {"timeout": 60})[0] == "unverified"
    assert SC.agreement(a, None, "not run")[0] == "unverified"
    err = {"run": {"steps": [], "ms": 0, "error": {"step": "s1", "message": "x"}}}
    assert SC.agreement(err, a)[0] == "disagree" and SC.agreement(err, err)[0] == "agree"


def test_probe_outcomes():
    g = lambda plan=True, **kw: q("G-1", [{"step": "s1", "reader": "r", "params": {}}] if plan else [], cls="G",
                                  gap="GAP-X", **kw)
    assert SC.score(g(), sel_run({"status": "UNKNOWN"}), None, NAMES, RECORDED, 5)["probe"] == "pass"
    assert SC.score(g(), sel_run({"refused": True, "refusal": "ValueError"}), None, NAMES, RECORDED, 5)["passed"]
    assert SC.score(g(), sel_run({"status": "INFERRED"}), None, NAMES, RECORDED, 5)["probe"] == "fabricated-answer"
    fab = sel_run({"status": "UNKNOWN"}, derivations=[{"rule": "x", "premises": ["att:1"]}])
    assert SC.score(g(), fab, None, NAMES, RECORDED, 5)["probe"] == "fabricated-derivation"
    assert SC.score(g(plan=False), {}, None, NAMES, RECORDED, 5)["probe"] == "not-callable"
    assert SC.score(g(), {"timeout": 5}, None, NAMES, RECORDED, 5)["probe"] == "timeout"


# ---- reporting (no database) ----------------------------------------------------------------------------------------
def test_report_keeps_timeouts_in_the_denominator_and_probes_apart():
    ok = sel_run({"status": "INFERRED"}, ["att:1"], ms=100.0)
    rs = [SC.score(sq(required_evidence=["ab"]) | {"id": f"S-{i}"}, ok, ok, NAMES, RECORDED, 5) for i in range(18)]
    rs.append(SC.score(sq() | {"id": "S-wrong"}, sel_run({"status": "NO"}), sel_run({"status": "NO"}), NAMES, RECORDED,
                       5))
    rs.append(SC.score(sq() | {"id": "S-slow"}, {"timeout": 5}, None, NAMES, RECORDED, 5, "timed out"))
    rs.append(SC.score(q("X-1", sq()["plan"], family="X", subset="identity"), ok, ok, NAMES, RECORDED, 5))
    rs.append(SC.score(q("G-1", [], cls="G", gap="GAP-X"), {}, None, NAMES, RECORDED, 5))
    s = REP.summarise(rs)
    S = s["families"]["S"]
    assert (S["scheduled"], S["completed"], S["correct"]) == (20, 19, 18)
    assert S["correct_among_completed"] == round(18 / 19, 4) and S["success_within_budget"] == 0.9
    # 20 latencies: the nearest-rank p95 is the 19th (100 ms); the stopped question entered at the budget (5000 ms)
    assert S["timeouts"] == 1 and S["p95_is_lower_bound"] and S["selective_p95_ms"] == 100.0
    assert S["failures"] == {"timeout": 1, "incorrect": 1}
    assert s["x_identity"]["scheduled"] == 1 and s["families"]["X"]["scheduled"] == 1
    assert s["all"]["scheduled"] == 21                                   # the probe is not scheduled for scoring
    assert s["probes"] == {"probes": 1, "passed": 0, "failed": 0, "not_callable": 1, "by_result": {"not-callable": 1}}
    verdicts = {c["criterion"]: c["verdict"] for c in s["criteria"]}
    assert verdicts["correctness S (correct / scheduled, timeouts included)"] == "fail"
    assert verdicts["questions over the 5 s hard budget"] == "fail"
    assert verdicts["path agreement (disagree / unverified)"] == "unverified"
    md = REP.report_md(rs, {"started": "now", "commit": "c", "questions": "q", "budget": 5, "reference_limit": 60})
    assert "X, identity subset" in md and "Gap probes (class G; never part of the scores above)" in md
    assert "100 / 100+" in md


def test_percentile_is_nearest_rank():
    assert REP.percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 95) == 10
    assert REP.percentile(list(range(1, 101)), 95) == 95
    assert REP.percentile([None], 50) is None


# ---- the loader's E2 steps and the plan runner (database) ---------------------------------------------------------------
@pytest.fixture(scope="module")
def L(driver):
    loaded = load(FX, driver)
    yield loaded
    drop(loaded)


def test_every_e2_step_loads_and_is_named(L):
    ops = {s["op"] for s in FX["steps"]}
    from evaluation.loader import E2_OPS
    assert {"position", "relate_frames", "anchor_frame", "define_unit", "define_quality_kind", "measure",
            "claim_cause", "claim_effect", "describe_occurrence", "record_event"} <= ops
    assert set(E2_OPS) >= ops - {"entity", "world", "mark", "attest", "account"}
    for sid in ("ab", "bc", "anchor-c", "box-in-c", "m1", "m2", "ev-s1", "d-s1", "ev-s2", "s1-causes-s2",
                "s2-puts-box", "crate-in-b-params"):
        assert L.written[sid], sid


def test_attest_params_reach_the_model(L):                          # GAP-HARNESS-1
    out = run_plan(L, q("F-1", [step("poses", {"thing": "crate", "t": "T3", "perspective": "tech"})]), True)
    frames = {(p["frame"], tuple(p["x"])) for p in out["steps"][0]["answer"]}
    assert ("B", (9.0, 9.0)) in frames


def test_where_extractors_on_a_derived_pose(L):
    out = run_plan(L, q("F-2", [step("where", {"thing": "box", "frame": "A", "t": "T3"})]), True)
    st = out["steps"][0]
    assert st["answer"]["status"] == "INFERRED"
    names = L.evidence_names()
    assert {names[a] for a in st["cited"]} == {"box-in-c", "ab", "bc"}
    assert st["derivations"][0]["rule"] == "frame-transform/v1"
    assert {names[a] for a in st["derivations"][0]["premises"]} == {"box-in-c", "ab", "bc"}
    # box at (1, 0, 0) in C; C is rotated 90 degrees about z and offset (0, 2, 0) in B; B offset (1, 0, 0) in A
    assert V.wrong_fields({"candidates[0].x": [1.0, 1.0], "candidates[0].y": [3.0, 3.0]}, st["answer"],
                          {"candidates[0].x": 1e-9, "candidates[0].y": 1e-9}) == []


def test_transform_numeric_comparison(L):
    out = run_plan(L, q("S-1", [step("transform_between", {"source": "C", "target": "A", "t": "T3"})]), True)
    a = out["steps"][0]["answer"]
    tol = {"transform.t": 1e-9, "transform.q": {"rad": 1e-9}}
    assert V.wrong_fields({"transform.t": [1.0, 2.0, 0.0], "transform.q": [-c for c in YAW90]}, a, tol) == []
    assert V.wrong_fields({"transform.t": [1.0, 2.0, 1e-6]}, a, tol) == [("transform.t", "different")]


def test_multi_step_plan_feeds_answers_forward(L):
    plan = [step("measurements", {"bearer": "box", "quality": "mass"}, name="m"),
            step("where", {"thing": "box", "frame": "A",
                           "t": {"from": "m", "path": "[*].records[record=m1-result]"}}, name="bad"),
            ]
    # a [*] map gives a list of matches per measurement; only one measurement has that record: not a time
    out = run_plan(L, q("X-0", plan, family="X"), True)
    assert out.get("plan_error") or out.get("error")
    plan = [step("measurements", {"bearer": "box", "quality": "mass"}, name="m"),
            step("measurement_calibration", {"bearer": "box", "quality": "mass"}, name="c"),
            step("where", {"thing": "box", "frame": "A", "t": {"from": "c", "path": "[record=m1-result].at"}},
                 name="w")]
    out = run_plan(L, q("X-1", plan, family="X"), True)
    assert "error" not in out and "plan_error" not in out
    assert out["steps"][2]["params"]["t"] == "2026-11-03T09:00:00+00:00"          # m1's activity start
    assert out["steps"][2]["answer"]["status"] == "INFERRED"
    assert out["ms"] >= out["steps"][2]["ms"] > 0


def test_plan_error_and_refusal(L):
    bad = [step("measurements", {"bearer": "box", "quality": "mass"}, name="m"),
           step("where", {"thing": "box", "frame": "A", "t": {"from": "m", "path": "[5].valid"}}, name="w")]
    out = run_plan(L, q("X-2", bad, family="X"), True)
    assert out["plan_error"]["step"] == "w" and "no item [5]" in out["plan_error"]["message"]
    notime = [step("measurements", {"bearer": "box", "quality": "mass"}, name="m"),
              step("where", {"thing": "box", "frame": "A", "t": {"from": "m", "path": "[0].unit"}}, name="w")]
    out = run_plan(L, q("X-3", notime, family="X"), True)
    assert out["plan_error"]["step"] == "w" and "not a time" in out["plan_error"]["message"]
    refused = run_plan(L, q("M-1", [step("convert", {"value": 1.0, "unit": "kg", "to": "kelvin"})]), True)
    assert refused["steps"][0]["answer"]["refused"] is True and "error" not in refused


def test_both_paths_answer_the_same(L):
    for r, p in [("transform_between", {"source": "C", "target": "A", "t": "T3"}),
                 ("compare_measurements", {"bearer": "box", "quality": "mass"}),
                 ("causes_of", {"effect": "ev-s2", "t": "T9"}), ("process_steps", {"process": "o-proc", "t": "T9"})]:
        question = q("P-1", [step(r, p)])
        a, b = run_plan(L, question, True), run_plan(L, question, False)
        assert [V.canonical(s["answer"]) for s in a["steps"]] == [V.canonical(s["answer"]) for s in b["steps"]], r
    assert L.wm.selective is True


def test_loader_refuses_bad_e2_steps(driver):
    bad = {"id": "bad", "steps": [{"op": "world", "id": "w"}, {"op": "entity", "kind": "spatial-frame", "id": "A"},
                                  {"op": "relate_frames", "id": "x", "world": "w", "parent": "A", "child": "A",
                                   "translation": [0, 0, 0], "colour": "red"}]}
    with pytest.raises(FixtureError, match="unknown fields"):
        load(bad, driver)


# ---- end to end through child processes: budget, restart, every failure kind (database) ---------------------------------
def _e2e_questions():
    W = {"world": "w"}
    tb = {"step": "s1", "reader": "transform_between", "params": {**W, "source": "C", "target": "A", "t": "T3"},
          "expected": {"status": "INFERRED", "transform.t": [1.0, 2.0, 0.0]}, "tolerance": {"transform.t": 1e-9}}
    wh = {"step": "s1", "reader": "where", "params": {**W, "thing": "box", "frame": "A", "t": "T3"},
          "expected": {"status": "INFERRED"}}
    echo = lambda **p: {"step": "s1", "reader": "selftest_echo", "params": p, "expected": {"value": 1}}
    return [
        q("S-ok", [tb], required_evidence=["ab", "bc"], admissible_evidence=["ab", "bc"]),
        q("S-wrong", [{**tb, "expected": {"status": "INFERRED", "transform.t": [1.0, 2.5, 0.0]}}]),
        q("F-inadmissible", [wh], family="F", required_evidence=["box-in-c"], admissible_evidence=["box-in-c"]),
        q("F-forbidden", [wh], family="F", forbidden_evidence=["ab"]),
        q("F-missing", [wh], family="F", required_evidence=["anchor-c"]),
        q("C-fabricated", [echo(value=1, derivations=[{"rule": "made-up/v1", "premises": ["ab"]},
                                                      {"rule": "frame-transform/v1", "premises": ["att:fake"]}])],
          family="C"),
        q("P-timeout", [{"step": "s1", "reader": "selftest_sleep", "params": {"seconds": 6},
                         "expected": {"slept": 6}}], family="P"),
        q("P-after-timeout", [tb], family="P"),                           # answered by a fresh child process
        q("M-error", [{"step": "s1", "reader": "selftest_raise", "params": {"kind": "crash"}, "expected": {"x": 1}}],
          family="M"),
        q("M-refusal-unexpected", [{"step": "s1", "reader": "selftest_raise", "params": {"kind": "refusal"},
                                    "expected": {"x": 1}}], family="M"),
        q("M-refusal-expected", [{"step": "s1", "reader": "convert", "params": {"value": 1.0, "unit": "kg",
                                  "to": "kelvin"}, "expected": {"refused": True}}], family="M"),
        q("X-plan-error", [{"step": "a", "reader": "measurements", "params": {**W, "bearer": "box", "quality": "mass"}},
                           {"step": "b", "reader": "where", "params": {**W, "thing": "box", "frame": "A",
                                                                      "t": {"from": "a", "path": "[9].valid"}},
                            "expected": {"status": "INFERRED"}}], family="X"),
        q("X-identity", [tb], family="X", subset="identity"),
        q("X-reference-slow", [{"step": "s1", "reader": "selftest_sleep", "params": {"seconds": 6, "on": "full"},
                                "expected": {"slept": 6}}], family="X"),
        q("X-disagree", [{"step": "s1", "reader": "selftest_path", "params": {}, "expected": {"selective": True}}],
          family="X"),
        q("G-unknown", [{"step": "s1", "reader": "where", "params": {**W, "thing": "box", "frame": "A", "t": "T9"}}],
          cls="G", gap="GAP-FRAME-3"),
        q("G-definite", [{"step": "s1", "reader": "where", "params": {**W, "thing": "box", "frame": "A", "t": "T3"}}],
          cls="G", gap="GAP-FRAME-1"),
        q("G-none", [], cls="G", gap="GAP-PROC-1"),
    ]


@pytest.fixture(scope="module")
def e2e(tmp_path_factory, driver):
    path = tmp_path_factory.mktemp("e2") / "questions.jsonl"
    path.write_text("\n".join(json.dumps(x) for x in _e2e_questions()) + "\n")
    results, workers = run([path], FIXTURES, budget=3.0, reference_limit=3.0, selftest=True)
    return {r["id"]: r for r in results}, workers, results


def test_e2e_each_failure_kind_is_detected(e2e):
    by, _, _ = e2e
    want = {"S-ok": None, "S-wrong": "incorrect", "F-inadmissible": "inadmissible-evidence",
            "F-forbidden": "forbidden-evidence", "F-missing": "missing-evidence",
            "C-fabricated": "fabricated-derivation", "P-timeout": "timeout", "P-after-timeout": None,
            "M-error": "execution-error", "M-refusal-unexpected": "unexpected-refusal", "M-refusal-expected": None,
            "X-plan-error": "plan-error", "X-identity": None, "X-reference-slow": None, "X-disagree": None}
    assert {k: by[k]["failure"] for k in want} == want
    assert by["S-ok"]["correct"] and by["S-ok"]["evidence"]["precision"] == 1.0
    assert set(by["F-inadmissible"]["evidence"]["inadmissible"]) == {"ab", "bc"}
    assert by["F-inadmissible"]["correct"] is True                   # the answer itself is right
    assert len(by["C-fabricated"]["fabricated"]) == 2


def test_e2e_budget_stops_the_question_and_the_next_one_runs(e2e):
    by, workers, _ = e2e
    t = by["P-timeout"]
    assert (t["completed"], t["correct"], t["latency_ms"], t["agreement"]) == (False, False, 3000.0, "unverified")
    assert by["P-after-timeout"]["correct"] and by["P-after-timeout"]["agreement"] == "agree"
    assert workers[SID]["restarts"] == 2                             # after the selective and the reference stops
    assert len(workers[SID]["load_ms"]) == 3


def test_e2e_reference_path_states(e2e):
    by, _, _ = e2e
    slow = by["X-reference-slow"]
    assert slow["correct"] and slow["agreement"] == "unverified" and "limit" in slow["agreement_reason"]
    assert slow["full_ms"] is None
    assert by["X-disagree"]["agreement"] == "disagree" and by["X-disagree"]["full_steps"][0]["answer"] == {
        "selective": False}
    assert by["S-ok"]["full_ms"] is not None


def test_e2e_probes_and_report(e2e):
    by, _, results = e2e
    assert by["G-unknown"]["probe"] == "pass" and by["G-unknown"]["returned"] == "UNKNOWN"
    assert by["G-definite"]["probe"] == "fabricated-answer" and by["G-definite"]["returned"] == "INFERRED"
    assert by["G-none"]["probe"] == "not-callable"
    s = REP.summarise(results)
    assert s["all"]["scheduled"] == 15 and s["probes"]["probes"] == 3
    assert s["x_identity"]["correct"] == 1
    assert s["families"]["P"]["success_within_budget"] == 0.5 and s["families"]["P"]["correct_among_completed"] == 1.0
    md = REP.report_md(results, {"started": "now", "commit": "c", "questions": "q", "budget": 3.0,
                                 "reference_limit": 3.0})
    assert "P-timeout" in md and "G-definite" in md


def test_run_refuses_questions_with_problems(tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text(json.dumps(q("S-1", [step("nope", {})])) + "\n")
    with pytest.raises(QuestionProblems, match="unknown reader"):
        run([path], FIXTURES)


def test_reader_docs_are_up_to_date():                           # GAP-HARNESS-4
    from evaluation.e2 import reader_docs
    assert reader_docs.OUT.read_text() == reader_docs.render(), "run: uv run python -m evaluation.e2.reader_docs"
    assert set(READERS) <= {line.split("`")[1].split("(")[0].split(".")[-1]
                            for line in reader_docs.OUT.read_text().splitlines() if line.startswith("## `")}


def test_command_line_writes_results_and_report(tmp_path, driver):
    from evaluation.e2.run import main
    qs = tmp_path / "q.jsonl"
    qs.write_text(json.dumps(q("S-1", [step("transform_between", {"source": "C", "target": "A", "t": "T3"},
                                            {"status": "INFERRED"})])) + "\n")
    fx = tmp_path / "fixtures"
    fx.mkdir()
    (fx / "f.json").write_text(json.dumps(FX))
    assert main(["--questions", str(qs), "--fixtures", str(fx), "--out", str(tmp_path / "out")]) == 0
    res = json.loads((tmp_path / "out" / "results.json").read_text())
    assert res["results"][0]["correct"] and res["meta"]["budget"] == 5.0 and res["meta"]["reference_limit"] == 60.0
    assert "Acceptance criteria" in (tmp_path / "out" / "report.md").read_text()
