"""Stage E2 harness: summaries, the acceptance criteria (E2-D6 as amended, F-1 to F-4) and the report.

- **Families** S, F, M, C, P and X, each over its scored (A and H) questions; the identity-conflict questions are part
  of X and are also summarised on their own (`X/identity`, F-4); classes A and H are also summarised apart.
- **Correctness, two ways (F-3):** among completed questions (correct / completed), and successful within budget across
  every scheduled question (correct / scheduled), so that a timeout stays in the denominator.
- **Evidence:** recall over questions with required evidence (found / required, summed); precision over questions
  with an admissible set (admissible cited / cited, summed); forbidden hits counted.
- **Latency (F-1, F-2):** the selective path's p50 and p95 over every scheduled question, a stopped question counted at
  the budget (so the p95 is a lower bound when there are timeouts); the full-load path's p50 and p95 recorded
  separately, with no target.
- **Gap probes** are never in these numbers: they have their own section.
"""

import json
import math
from collections import Counter

from evaluation.e2.score import ORDER

FAMILIES = ("S", "F", "M", "C", "P", "X")
THRESHOLDS = {"correctness": 0.95, "recall": 0.90, "precision": 1.0, "p95_ms": 1000.0}


def percentile(xs, p):
    """Nearest-rank percentile (no interpolation): the smallest value with at least p % of values at or below it."""
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    return xs[max(0, math.ceil(p / 100 * len(xs)) - 1)]


def role_summary(rs, role):
    """One evidence role over a group (P-1 and P-3 as amended): recall over questions requiring it (nothing returned
    counts, recall 0); precision over questions with an admissible set that cite something named; unattributed
    citations make precision unverified; questions requiring evidence but citing nothing are counted apart."""
    evs = [r["evidence"][role] for r in rs if r.get("evidence")]
    req = [e for e in evs if e["required"]]
    adm = [e for e in evs if "admissible" in e]
    found, required = sum(len(e["found"]) for e in req), sum(len(e["required"]) for e in req)
    cited = sum(len(e["cited"]) for e in adm)
    inadmissible = sum(len(e["inadmissible"]) for e in adm)
    unattributed = sum(len(e["unattributed"]) for e in evs)
    return {"recall": round(found / required, 4) if required else None, "recall_questions": len(req),
            "precision": round(1 - inadmissible / cited, 4) if cited else None, "precision_questions": len(adm),
            "inadmissible": inadmissible, "unattributed": unattributed, "precision_verified": unattributed == 0,
            "no_evidence_returned": sum(1 for e in req if not e["cited"] and not e["unattributed"])}


def summarise_group(rs):
    n = len(rs)
    completed = [r for r in rs if r["completed"]]
    correct = sum(r["correct"] for r in rs)
    fails = Counter(f for r in rs for f in r["failures"])
    roles = {role: role_summary(rs, role) for role in ("supporting", "conflicting")}
    agree = Counter(r["agreement"] for r in rs)
    return {
        "scheduled": n, "completed": len(completed), "correct": correct,
        "correct_among_completed": round(correct / len(completed), 4) if completed else None,
        "success_within_budget": round(correct / n, 4) if n else None,
        "failures": {k: fails[k] for k in ORDER if fails[k]},
        "evidence_recall": roles["supporting"]["recall"], "evidence_precision": roles["supporting"]["precision"],
        "evidence": roles,
        "forbidden_hits": sum(len(r["evidence"]["forbidden_cited"]) for r in rs if r.get("evidence")),
        "alternatives_as_support": sum(len(r["evidence"]["alternative_as_support"]) for r in rs if r.get("evidence")),
        "fabricated_derivations": sum(len(r.get("fabricated", [])) for r in rs),
        "selective_p50_ms": percentile([r["latency_ms"] for r in rs], 50),
        "selective_p95_ms": percentile([r["latency_ms"] for r in rs], 95),
        "timeouts": fails["timeout"], "p95_is_lower_bound": fails["timeout"] > 0,
        "full_p50_ms": percentile([r["full_ms"] for r in rs], 50),
        "full_p95_ms": percentile([r["full_ms"] for r in rs], 95),
        "agreement": {k: agree[k] for k in ("agree", "consistent-failure", "disagree", "unverified") if agree[k]},
    }


def summarise(results):
    scored = [r for r in results if r["class"] in ("A", "H")]
    probes = [r for r in results if r["class"] == "G"]
    out = {"families": {f: summarise_group([r for r in scored if r["family"] == f])
                        for f in FAMILIES if any(r["family"] == f for r in scored)},
           "classes": {c: summarise_group([r for r in scored if r["class"] == c])
                       for c in ("A", "H") if any(r["class"] == c for r in scored)},
           "all": summarise_group(scored) if scored else None}
    ident = [r for r in scored if r["family"] == "X" and r.get("subset") == "identity"]
    if ident:
        out["x_identity"] = summarise_group(ident)
    # LABS-1.064 item 26: targeted defect coverage reported apart from broad competency coverage (both stay inside
    # their family's scores)
    targeted = [r for r in scored if r.get("targets")]
    if targeted:
        out["targeted"] = {**summarise_group(targeted),
                           "by_di": dict(Counter(d for r in targeted for d in r["targets"]))}
        out["competency"] = summarise_group([r for r in scored if not r.get("targets")]) \
            if len(targeted) < len(scored) else None
    out["probes"] = {"probes": len(probes), "passed": sum(r["passed"] is True for r in probes),
                     "failed": sum(r["passed"] is False for r in probes),
                     "not_callable": sum(r["passed"] is None for r in probes),
                     "by_result": dict(Counter(r["probe"] for r in probes))}
    out["criteria"] = criteria(out, results)
    return out


def _verdict(ok):
    return "pass" if ok is True else "fail" if ok is False else "n/a"


def criteria(s, results):
    """E2-D6 as amended, per family where it is per family. 'n/a' when nothing in the run applies."""
    rows = []
    for f, g in s["families"].items():
        rows.append({"criterion": f"correctness {f} (correct / scheduled, timeouts included)", "value":
                     g["success_within_budget"], "threshold": ">= 0.95",
                     "verdict": _verdict(g["success_within_budget"] >= THRESHOLDS["correctness"])})
        if g["evidence_recall"] is not None:
            rows.append({"criterion": f"supporting evidence recall {f}", "value": g["evidence_recall"],
                         "threshold": ">= 0.90", "verdict": _verdict(g["evidence_recall"] >= THRESHOLDS["recall"])})
        con = g["evidence"]["conflicting"]
        if con["recall"] is not None:
            rows.append({"criterion": f"conflicting evidence recall {f} (reported)", "value": con["recall"],
                         "threshold": "reported", "verdict": "n/a"})
    a = s["all"]
    if a:
        prec, sup, con = a["evidence_precision"], a["evidence"]["supporting"], a["evidence"]["conflicting"]
        verdict = _verdict(None if prec is None else prec >= THRESHOLDS["precision"])
        if verdict == "pass" and not sup["precision_verified"]:
            verdict = "unverified"                    # unattributed evidence prevents a verified pass (LABS-1.063)
        rows.append({"criterion": "evidence precision (supporting evidence)", "value": prec, "threshold": "= 1.0",
                     "verdict": verdict})
        rows.append({"criterion": "inadmissible conflicting evidence", "value": con["inadmissible"],
                     "threshold": "= 0", "verdict": _verdict(con["inadmissible"] == 0)})
        rows.append({"criterion": "conflicting evidence precision (reported)", "value": con["precision"],
                     "threshold": "reported", "verdict": "n/a" if con["precision_verified"] else "unverified"})
        rows.append({"criterion": "unattributed evidence (blocks a verified precision pass)",
                     "value": sup["unattributed"] + con["unattributed"], "threshold": "= 0",
                     "verdict": _verdict(sup["unattributed"] + con["unattributed"] == 0)})
        rows.append({"criterion": "alternatives presented as support", "value": a["alternatives_as_support"],
                     "threshold": "= 0", "verdict": _verdict(a["alternatives_as_support"] == 0)})
        rows.append({"criterion": "forbidden evidence cited", "value": a["forbidden_hits"], "threshold": "= 0",
                     "verdict": _verdict(a["forbidden_hits"] == 0)})
        rows.append({"criterion": "selective p95 latency (ms; lower bound if timeouts)", "value": a["selective_p95_ms"],
                     "threshold": "< 1000", "verdict": _verdict(None if a["selective_p95_ms"] is None else
                                                               a["selective_p95_ms"] < THRESHOLDS["p95_ms"])})
        rows.append({"criterion": "questions over the 5 s hard budget", "value": a["timeouts"], "threshold": "= 0",
                     "verdict": _verdict(a["timeouts"] == 0)})
        ag = a["agreement"]
        dis, cf, unv = ag.get("disagree", 0), ag.get("consistent-failure", 0), ag.get("unverified", 0)
        # only answers compared equal on both paths satisfy agreement (LABS-1.062): a consistent failure does not
        rows.append({"criterion": "path agreement: agree / scheduled (disagree, consistent failure, unverified)",
                     "value": f"{ag.get('agree', 0)} / {a['scheduled']} ({dis}, {cf}, {unv})",
                     "threshold": "all agree", "verdict": "fail" if dis or cf else "unverified" if unv else "pass"})
    fab = sum(len(r.get("fabricated") or []) for r in results)
    rows.append({"criterion": "fabricated derivations (scored questions and probes)", "value": fab, "threshold": "= 0",
                 "verdict": _verdict(fab == 0)})
    return rows


def _pct(x):
    return "–" if x is None else f"{100 * x:.1f}"


def _ms(x):
    return "–" if x is None else f"{x:.0f}"


def report_md(results, meta):
    s = summarise(results)
    lines = [f"# {meta.get('title', 'Stage E2 evaluation results')}", "",
             f"Run {meta['started']} on commit `{meta['commit']}`. Questions: `{meta['questions']}`; gold frozen at "
             f"`{meta.get('gold_commit') or '(not given)'}`. Hard budget {meta['budget']} s (selective path); "
             f"reference limit {meta['reference_limit']} s (full-load path).", ""]
    head = ("| Group | Scheduled | Completed | Correct | % of completed | % within budget (all scheduled) | Recall % | "
            "Precision % | Timeouts | Sel. p50 / p95 ms | Full p50 / p95 ms | Agree / consistent failure / disagree / unverified |")
    lines += [head, "|---|" + "---:|" * 11]

    def row(name, g):
        ag = g["agreement"]
        p95 = _ms(g["selective_p95_ms"]) + ("+" if g["p95_is_lower_bound"] else "")
        lines.append(f"| {name} | {g['scheduled']} | {g['completed']} | {g['correct']} | "
                     f"{_pct(g['correct_among_completed'])} | {_pct(g['success_within_budget'])} | "
                     f"{_pct(g['evidence_recall'])} | {_pct(g['evidence_precision'])} | {g['timeouts']} | "
                     f"{_ms(g['selective_p50_ms'])} / {p95} | {_ms(g['full_p50_ms'])} / {_ms(g['full_p95_ms'])} | "
                     f"{ag.get('agree', 0)} / {ag.get('consistent-failure', 0)} / {ag.get('disagree', 0)} / "
                     f"{ag.get('unverified', 0)} |")
    for f, g in s["families"].items():
        row(f, g)
    if "x_identity" in s:
        row("X, identity subset", s["x_identity"])
    for c, g in s["classes"].items():
        row(f"class {c}", g)
    if s["all"]:
        row("**all scored**", s["all"])
    lines += ["", "`+`: a lower bound (a stopped question counts at the budget).", "",
              "## Failures by kind", "", "| Group | " + " | ".join(ORDER) + " |", "|---|" + "---:|" * len(ORDER)]
    for f, g in list(s["families"].items()) + ([("all", s["all"])] if s["all"] else []):
        lines.append(f"| {f} | " + " | ".join(str(g["failures"].get(k, 0)) for k in ORDER) + " |")
    lines += ["", "## Acceptance criteria (E2-D6 as amended)", "", "| Criterion | Value | Threshold | Verdict |",
              "|---|---|---|---|"]
    for c in s["criteria"]:
        lines.append(f"| {c['criterion']} | {c['value']} | {c['threshold']} | {c['verdict']} |")
    lines += ["", "## Scored questions with a failure", "", "| Id | Family | Class | Failures | Detail |", "|---|---|---|---|---|"]
    for r in results:
        if r["class"] != "G" and r["failures"]:
            detail = (r.get("error") or r.get("plan_error") or r.get("harness_error") or
                      r.get("wrong_fields") or r.get("fabricated") or
                      {k: v for k, v in (r.get("evidence") or {}).items() if k in ("supporting", "conflicting",
                                                                                     "forbidden_cited")})
            lines.append(f"| {r['id']} | {r['family']} | {r['class']} | {', '.join(r['failures'])} | "
                         f"`{json.dumps(detail, default=str)[:300]}` |")
    unv = [r for r in results if r["class"] != "G" and r["agreement"] != "agree"]
    if unv:
        lines += ["", "## Path agreement not established", "", "| Id | Agreement | Reason |", "|---|---|---|"]
        lines += [f"| {r['id']} | {r['agreement']} | {r['agreement_reason']} |" for r in unv]
    p = s["probes"]
    lines += ["", "## Gap probes (class G; never part of the scores above)", "",
              f"{p['probes']} probes: {p['passed']} pass, {p['failed']} fail, {p['not_callable']} not callable "
              "(no reader to call).", "", "| Id | Gap | Reader(s) | Returned | Result |", "|---|---|---|---|---|"]
    for r in results:
        if r["class"] == "G":
            readers = ", ".join(s_["reader"] for s_ in r.get("steps", [])) or "none"
            lines.append(f"| {r['id']} | {r['gap']} | {readers} | `{json.dumps(r.get('returned'), default=str)[:120]}` "
                         f"| {r['probe']} |")
    return "\n".join(lines) + "\n"
