"""Stage E2 harness: score one question from its two path runs.

Scored questions (classes A and H). Each failure kind is recorded separately, so none can hide another:
- `timeout`: the selective path did not finish within the hard budget (it was stopped); not completed.
- `harness-error`: the harness itself failed (never a reader's answer).
- `execution-error`: a reader raised an exception that is not a refusal.
- `plan-error`: a plan step's parameter could not be resolved from an earlier answer.
- `unexpected-refusal`: a reader refused where the question expects an answer.
- `incorrect`: an expected field (on any step) differs.
- `fabricated-derivation`: the answer presents a derivation whose rule is not recorded by the model, or whose
  premises are missing or not attestations recorded in the scenario.
- `forbidden-evidence`: the answer cites a forbidden attestation as support.
- `inadmissible-evidence`: the answer cites as support an attestation outside the admissible set.
- `missing-evidence`: a required attestation is not cited.

`correct` means completed, no execution, plan or harness error, no unexpected refusal, and every expected field on
every step matches. Evidence and derivation failures are reported beside it, as separate criteria (E2-D6).
`failure` is the first kind present in the order above; `failures` lists them all.

Path agreement (F-2, corrected under LABS-1.062):
- `agree`: both paths **answered** (a documented refusal is an answer) and every step's answer is the same. Only this
  satisfies the semantic agreement criterion.
- `consistent-failure`: both paths failed in the same way (an execution or plan error at the same step, of the same
  exception type). Recorded, but it is **not** agreement: no answer was compared.
- `disagree`: the answers differ, or only one path failed, or they failed differently.
- `unverified`: the reference (full-load) run timed out, failed in the harness, or was not run (for example because the
  selective run timed out).

Gap probes (class G) are scored apart (`probe`). A probe passes only when (a) no derivation in any step's answer is
fabricated, whatever the status, and (b) the answer is a status the probe accepts (UNKNOWN-like) or an **established**
documented refusal of the reader. An undocumented exception is an execution error, and a refusal whose source is not an
approved decision is `unestablished-refusal`: neither passes. A probe with no plan is `not-callable` (listed, not run).
"""

from evaluation.e2.readers import KNOWN_RULES
from evaluation.e2.values import canonical, select, PathError, wrong_fields

ORDER = ["timeout", "harness-error", "execution-error", "plan-error", "unexpected-refusal", "incorrect",
         "fabricated-derivation", "forbidden-evidence", "inadmissible-evidence", "missing-evidence"]
ANSWER_FAILURES = {"timeout", "harness-error", "execution-error", "plan-error", "unexpected-refusal", "incorrect"}


def base(q):
    return {"id": q["id"], "family": q["family"], "subset": q.get("subset"), "class": q["class"],
            "gap": q.get("gap"), "scenario": q["scenario"], "adversarial": q.get("adversarial"),
            "difficulty": q.get("difficulty")}


def fabricated(steps, recorded, names):
    """Derivations presented by the answers that are not recorded: [{"step", "at", "rule", "why"}]."""
    out = []
    for st in steps:
        for d in st.get("derivations", []):
            why = []
            if d.get("rule") not in KNOWN_RULES:
                why.append(f"rule {d.get('rule')!r} is not a rule the model records")
            premises = d.get("premises") or []
            if not premises:
                why.append("no premises")
            missing = [p for p in premises if p not in recorded and p not in names]
            if missing:
                why.append(f"premises not recorded in the scenario: {missing}")
            if why:
                out.append({"step": st["step"], "at": d.get("at"), "rule": d.get("rule"), "why": "; ".join(why)})
    return out


def _check_steps(q, run):
    """(wrong [(step, path, reason)], unexpected refusals [step], first wrong step)."""
    expected = {st["step"]: st for st in q["plan"]}
    wrong, refused, first = [], [], None
    for st in run["steps"]:
        spec = expected[st["step"]]
        exp = spec.get("expected")
        if not exp or "answer" not in st:
            continue
        ans = st["answer"]
        if isinstance(ans, dict) and ans.get("refused") is True and "refused" not in exp:
            refused.append(st["step"])
            first = first or st["step"]
            continue
        bad = wrong_fields(exp, ans, spec.get("tolerance"), set(spec.get("ordered", [])))
        if bad:
            wrong += [(st["step"], p, r) for p, r in bad]
            first = first or st["step"]
    return wrong, refused, first


def evidence(q, cited_ids, names):
    required = set(q.get("required_evidence", []))
    forbidden = set(q.get("forbidden_evidence", []))
    has_admissible = "admissible_evidence" in q
    admissible = set(q.get("admissible_evidence", [])) | required
    cited = {names.get(a, a) for a in cited_ids}
    if not (required or forbidden or has_admissible):
        return None
    ev = {"cited": sorted(cited), "required": sorted(required), "found": sorted(required & cited),
          "recall": round(len(required & cited) / len(required), 3) if required else None,
          "forbidden_cited": sorted(forbidden & cited)}
    if has_admissible:
        inadmissible = sorted(cited - admissible)
        ev.update(admissible=sorted(admissible), inadmissible=inadmissible,
                  precision=round(1 - len(inadmissible) / len(cited), 3) if cited else None)
    return ev


def agreement(sel, full, reason=None):
    if full is None:
        return "unverified", reason or "the reference path was not run"
    if "timeout" in full:
        return "unverified", f"the reference path did not finish within its limit ({full['timeout']} s)"
    if "harness_error" in full:
        return "unverified", f"the reference path failed in the harness: {full['harness_error']}"
    if "run" not in sel:
        return "unverified", "the selective path has no result"
    a, b = sel["run"], full["run"]
    if "error" in a or "error" in b or "plan_error" in a or "plan_error" in b:
        def failure(r):
            if "error" in r:
                return ("execution", r["error"]["step"], r["error"]["message"].split(":", 1)[0])
            if "plan_error" in r:
                return ("plan", r["plan_error"]["step"])
            return None
        fa, fb = failure(a), failure(b)
        if fa is not None and fa == fb:
            return "consistent-failure", f"both paths failed the same way ({fa[0]} error at step {fa[1]!r}); " \
                                         "no answer was compared"
        return "disagree", "an error on one path only, or different errors"
    ans = lambda r: [canonical(s.get("answer")) for s in r["steps"]]
    return ("agree", None) if ans(a) == ans(b) else ("disagree", "the answers differ")


def latency(sel, budget):
    """Selective-path question latency in ms: the readers' own time; a stopped question counts at the budget."""
    if "timeout" in sel:
        return round(budget * 1000, 1), True
    if "run" in sel:
        return sel["run"]["ms"], False
    return None, False


def score(q, sel, full, names, recorded, budget, full_reason=None):
    if q["class"] == "G":
        return probe(q, sel, names, recorded)
    rec = base(q)
    failures, steps = [], []
    if "timeout" in sel:
        failures.append("timeout")
    elif "harness_error" in sel:
        failures.append("harness-error")
        rec["harness_error"] = sel["harness_error"]
    else:
        run = sel["run"]
        steps = run["steps"]
        if "error" in run:
            failures.append("execution-error")
            rec["error"] = run["error"]
        if "plan_error" in run:
            failures.append("plan-error")
            rec["plan_error"] = run["plan_error"]
        wrong, refused, first = _check_steps(q, run)
        if refused:
            failures.append("unexpected-refusal")
            rec["refused_at"] = refused
        if wrong:
            failures.append("incorrect")
        rec.update(wrong_fields=[{"step": s, "path": p, "reason": r} for s, p, r in wrong], first_wrong_step=first)
        fab = fabricated(steps, recorded, names)
        if fab:
            failures.append("fabricated-derivation")
            rec["fabricated"] = fab
        ev = evidence(q, {a for st in steps for a in st.get("cited", [])}, names)
        rec["evidence"] = ev
        if ev:
            if ev["forbidden_cited"]:
                failures.append("forbidden-evidence")
            if ev.get("inadmissible"):
                failures.append("inadmissible-evidence")
            if ev["required"] and ev["recall"] < 1:
                failures.append("missing-evidence")
    failures.sort(key=ORDER.index)
    ms, censored = latency(sel, budget)
    status, why = agreement(sel, full, full_reason)
    rec.update(completed="timeout" not in failures and "harness-error" not in failures,
               correct=not (set(failures) & ANSWER_FAILURES), failure=failures[0] if failures else None,
               failures=failures, latency_ms=ms, latency_censored=censored,
               full_ms=(full or {}).get("run", {}).get("ms"), agreement=status, agreement_reason=why,
               steps=[{k: v for k, v in s.items() if k != "trace"} for s in steps])
    if status == "disagree" and full and "run" in full:
        rec["full_steps"] = [{"step": s["step"], "answer": s.get("answer"), "error": s.get("error")}
                             for s in full["run"]["steps"]]
    return rec


def probe(q, sel, names, recorded):
    """A gap probe: never part of a family's scores."""
    rec = base(q)
    spec = q.get("probe") or {}
    accept = set(spec.get("accept", ["UNKNOWN", "NOT_YET_KNOWN", "refusal"]))
    if not q.get("plan"):
        rec.update(probe="not-callable", passed=None, returned=None,
                   note="no existing reader answers this question; listed with its gap")
        return rec
    if "timeout" in sel:
        rec.update(probe="timeout", passed=False, returned=None)
        return rec
    if "harness_error" in sel:
        rec.update(probe="harness-error", passed=False, returned=sel["harness_error"])
        return rec
    run = sel["run"]
    steps = run["steps"]
    rec["steps"] = [{k: v for k, v in s.items() if k != "trace"} for s in steps]
    rec["latency_ms"] = run["ms"]
    fab = fabricated(steps, recorded, names)
    if "error" in run or "plan_error" in run:
        rec.update(probe="execution-error" if "error" in run else "plan-error", passed=False,
                   returned=(run.get("error") or run.get("plan_error"))["message"])
        return rec
    last = steps[-1]["answer"]
    if isinstance(last, dict) and last.get("refused") is True:
        returned = f"refusal: {last.get('refusal')}"
        if not last.get("established"):
            rec.update(probe="fabricated-derivation" if fab else "unestablished-refusal", passed=False,
                       returned=returned, fabricated=fab)
            return rec
        ok = "refusal" in accept
    else:
        try:
            returned = select(last, spec.get("path", "status"))
        except PathError as e:
            returned, ok = f"(no {spec.get('path', 'status')!r}: {e})", False
        else:
            ok = returned in accept
    if fab:
        rec.update(probe="fabricated-derivation", passed=False, returned=returned, fabricated=fab)
    else:
        rec.update(probe="pass" if ok else "fabricated-answer", passed=ok, returned=returned)
    return rec
