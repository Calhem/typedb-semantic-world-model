"""Stage E1 evaluation harness (LABS-1.051): run the benchmark through the public reasoning API and score it.

    uv run python -m evaluation.run [--only CATEGORY ...] [--out benchmark/e1/results]

For every scenario: load its fixture into an isolated database (evaluation.loader), ask each of its questions on
both query paths (selective and full load), normalise the reader's answer to the template's fields
(benchmark/e1/TEMPLATES.md), compare it with the expected answer, and record correctness, evidence, the two paths'
agreement and a failure category. Writes results.json (machine-readable) and report.md (human-readable). Expected
answers are read, never changed.
"""

import argparse
import json
import sys
import time
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from worldmodel import MovementConflict, RoleCardinalityError, connect  # noqa: E402
from worldmodel import laboratory as lab, organisation as org  # noqa: E402

from evaluation.check import BENCH, fixtures, questions  # noqa: E402
from evaluation.loader import T, drop, load  # noqa: E402

PATHS = (("selective", True), ("full", False))
NOT_SUPPORT = {"pending", "alternatives", "only_in", "not_traversed", "accounts", "descriptions", "superseded_by_source"}
UNUSABLE = {"unreviewed", "rejected", "retracted"}
REFUSALS = (MovementConflict, RoleCardinalityError, ValueError)


def _ctx(L, p):
    return {"as_of": L.at(p.get("as_of")), "perspective": p.get("perspective", "system")}


def _status(s):
    return getattr(s, "name", s)


def _ids(xs):
    return sorted({str(x) for x in xs or ()})


def usable_evidence(x):
    """Evidence entries ({"attestation": id, "acceptance": ...}) the perspective can use, anywhere under x, except under
    keys that list non-supporting material (pending, alternatives, only_in, not_traversed, accounts, descriptions)."""
    out = set()

    def walk(v, key=None):
        if key in NOT_SUPPORT:
            return
        if isinstance(v, dict):
            if isinstance(v.get("attestation"), str) and v.get("acceptance") not in UNUSABLE:
                out.add(v["attestation"])
            for k, w in v.items():
                walk(w, k)
        elif isinstance(v, (list, tuple)):
            for w in v:
                walk(w, key)
    walk(x)
    return out


def deciding(r, entries_key):
    """What an applicability answer (capable, authorised, calibration_status) rests on: its `support` (rule Q's
    deciding claims) where the reader states one; otherwise (a dispute between entries, or an answer such as "not yet
    effective" whose support the reader leaves empty) the usable evidence of the entries it reports as applicable."""
    if r.get("support"):
        return set(r["support"])
    return set().union(set(), *(usable_evidence(e) for e in r.get(entries_key, [])))


# ---- adapters: one public reader per template; each returns (normalised answer, cited attestation ids) --------------
def a_holds(L, p):
    wm, c = L.wm, _ctx(L, p)
    rec = wm.judgement(p["world"], p["type"], p["roles"], T(p["t"]), **c)
    ans = wm.holds(p["world"], p["type"], p["roles"], T(p["t"]), **c)
    return {"judgement": rec.judgement.value, "status": _status(ans.status), "holds": ans.holds}, ans.support


def a_value_at(L, p):
    ans = L.wm.value_at(p["world"], p["type"], p["subject"], T(p["t"]), **_ctx(L, p))
    return {"status": _status(ans.status), "values": _ids(ans.values)}, ans.support


def a_exists(L, p):
    ans = L.wm.exists(p["world"], p["thing"], T(p["t"]), **_ctx(L, p))
    return {"status": _status(ans.status), "holds": ans.holds}, ans.support


def _identity(L, p):
    return L.wm.identity(p["world"], **_ctx(L, p))


def a_same_thing(L, p):
    ident = _identity(L, p)
    conflict = any(p["a"] in c["names"] or p["b"] in c["names"] for c in ident.conflicts)
    return {"same": ident.canonical(p["a"]) == ident.canonical(p["b"]), "conflict": conflict}, ()


def a_aliases(L, p):
    return {"members": _ids(_identity(L, p).members(p["x"]))}, ()


def a_parts(L, p):
    return {"parts": _ids(L.wm.parts(p["world"], p["whole"], T(p["t"]), **_ctx(L, p)))}, ()


def a_dependencies(L, p):
    deps = L.wm.direct_dependencies(p["world"], p["dependent"], T(p["t"]), **_ctx(L, p))
    disputed = [d["dependee"] for d in deps if _status(d["status"]) == "DISPUTED"]
    support = [s for d in deps for s in d.get("support", [])]
    return {"dependees": _ids(d["dependee"] for d in deps if d["dependee"] not in disputed),
            "disputed": _ids(disputed)}, support


def a_event_role(L, p):
    c = _ctx(L, p)
    view = L.wm.occurrence(p["world"], p["occurrence"], **c)
    role = view["roles"].get(p["role"])
    if role is None:
        return {"judgement": "union", "players": [], "reason": None, "multiplicity": None,
                "_note": f"no role {p['role']!r} in the view; roles: {sorted(view['roles'])}"}, ()
    applying = [x for x in role["constraints"] if x["applies"]]
    if applying:
        x = applying[0]
        cited = (set(x.get("support", [])) | set((x.get("classification") or {}).get("support", [])) |
                 {a["description"] for g in x["players"] for a in g["accounts"]})
        out = {"judgement": x["judgement"], "players": sorted(sorted(g["names"]) for g in x["players"]),
               "reason": x.get("reason"), "multiplicity": x.get("multiplicity")}
        if len(applying) > 1:
            out["_note"] = f"{len(applying)} constraints apply; the first is scored"
        return out, cited
    players = sorted(role["players"])
    ident = L.wm.identity(p["world"], ids=players, **c) if players else None
    groups = defaultdict(list)
    for x in players:
        groups[ident.canonical(x)].append(x)
    cited = [d for ds in role["players"].values() for d in ds]
    return {"judgement": "union", "players": sorted(sorted(g) for g in groups.values()), "reason": None,
            "multiplicity": None}, cited


def a_occurrence_status(L, p):
    r = L.wm.occurrence_status(p["world"], p["occurrence"], T(p["t"]), **_ctx(L, p))
    return {"status": r["status"]}, getattr(r.get("answer"), "support", ())


def a_office_holders(L, p):
    r = org.office_holders(L.wm, p["world"], p["office"], p["context"], T(p["t"]), **_ctx(L, p))
    cited = set().union(*(usable_evidence(a) for a in r.get("appointments", []) if a.get("judgement") == "established"))
    for a in (r["conflict"] or {}).get("appointments", []):
        cited.update(a.get("attestations", []))
    cited.update(((r["conflict"] or {}).get("constraint") or {}).get("support", []))
    return {"holders": _ids(r["holders"]), "conflict": r["conflict"] is not None}, cited


def _applicability(r, entries_key):
    return {"judgement": r["judgement"]}, deciding(r, entries_key)


def a_capable(L, p):
    return _applicability(L.wm.capable(p["world"], p["holder"], p["capability"], T(p["t"]), p.get("context"),
                                       **_ctx(L, p)), "applicable")


def a_authorised(L, p):
    return _applicability(org.authorised(L.wm, p["world"], p["holder"], p["power"], p["scope"], T(p["t"]),
                                         **_ctx(L, p)), "grants")


def a_calibrated(L, p):
    return _applicability(lab.calibration_status(L.wm, p["world"], p["instrument"], T(p["t"]), **_ctx(L, p)),
                          "certificates")


def a_officials(L, p):
    return {"officials": _ids(org.official_act(L.wm, p["world"], p["event"], **_ctx(L, p))["officials"])}, ()


def a_move(L, p):
    """A write: the harness gives it a freshly loaded copy of the scenario, used once and dropped."""
    try:
        eid, _ = L.wm.move(p["world"], p["thing"], p["to"], T(p["t"]), actor=p.get("actor"),
                           attester=p.get("attester", "system"))
    except REFUSALS as e:
        return {"outcome": "refused", "origin": [], "_note": f"{type(e).__name__}: {e}"[:300]}, ()
    return {"outcome": "recorded", "origin": _ids(L.wm.content(eid)["roles"].get("origin", []))}, ()


ADAPTERS = {"holds": a_holds, "value_at": a_value_at, "exists": a_exists, "same_thing": a_same_thing,
            "aliases": a_aliases, "parts": a_parts, "dependencies": a_dependencies, "event_role": a_event_role,
            "occurrence_status": a_occurrence_status, "office_holders": a_office_holders, "capable": a_capable,
            "authorised": a_authorised, "calibrated": a_calibrated, "officials": a_officials, "move": a_move}
SUPPORTED_EVIDENCE = {"holds", "value_at", "exists", "dependencies", "event_role", "occurrence_status",
                      "office_holders", "capable", "authorised", "calibrated"}


# ---- comparison ------------------------------------------------------------------------------------------------------
def _norm(field, v):
    if field == "players":
        return sorted(sorted(g) for g in (v or []))
    if isinstance(v, list):
        return sorted(v, key=str)
    return v


def compare(expected, actual):
    """Fields of `expected` whose value differs from `actual` (lists as sets; players as a set of groups)."""
    return sorted(f for f, v in expected.items() if _norm(f, v) != _norm(f, actual.get(f)))


def category_of(template, wrong):
    if not wrong:
        return None
    if any(f in ("judgement", "status", "holds", "same", "conflict", "outcome") for f in wrong):
        return "wrong-judgement"
    return "wrong-values"


def ask_one(L, q, adapter, selective):
    """One answer on one query path."""
    L.wm.selective = selective
    t0 = time.perf_counter()
    try:
        actual, cited = adapter(L, q["params"])
        return {"answer": actual, "cited": sorted(map(str, cited)), "ms": round((time.perf_counter() - t0) * 1000, 1)}
    except Exception as e:                                      # an error is a result, recorded per path
        return {"error": f"{type(e).__name__}: {' '.join(str(e).split())[:400]}",
                "trace": traceback.format_exc(limit=3)[-800:]}
    finally:
        L.wm.selective = True


def ask(L, q, adapter):
    """A read on both query paths, on one loaded scenario."""
    return {name: ask_one(L, q, adapter, selective) for name, selective in PATHS}


def score(q, runs, names):
    sel = runs["selective"]
    rec = {"id": q["id"], "category": q["category"], "template": q["template"], "scenario": q["scenario"],
           "expected": q["expected"], "adversarial": q["adversarial"], "difficulty": q["difficulty"]}
    if "error" in sel:
        rec.update(correct=False, failure="error", error=sel["error"], actual=None)
    else:
        actual = {k: v for k, v in sel["answer"].items() if not k.startswith("_")}
        wrong = compare(q["expected"], actual)
        cited = {names.get(a, a) for a in sel["cited"]}
        required, forbidden = set(q["required_evidence"]), set(q["forbidden_evidence"])
        ev = None
        if q["template"] in SUPPORTED_EVIDENCE and (required or forbidden):
            ev = {"required": sorted(required), "found": sorted(required & cited), "recall":
                  round(len(required & cited) / len(required), 3) if required else None,
                  "forbidden_cited": sorted(forbidden & cited)}
        failure = category_of(q["template"], wrong)
        if failure is None and ev and ev["forbidden_cited"]:
            failure = "forbidden-evidence"
        elif failure is None and ev and required and ev["recall"] < 1:
            failure = "missing-evidence"
        rec.update(correct=not wrong, wrong_fields=wrong, actual=actual, evidence=ev, failure=failure,
                   note=sel["answer"].get("_note"))
    full = runs["full"]
    rec["paths_agree"] = ("error" in full and "error" in sel) or (
        "error" not in full and "error" not in sel and full["answer"] == sel["answer"])
    if not rec["paths_agree"]:
        rec["full_path"] = full.get("answer", full.get("error"))
    rec["ms"] = {k: runs[k].get("ms") for k in runs}
    return rec


def run(only=None, driver=None):
    driver = driver or connect()
    fx = fixtures()
    by_scenario = defaultdict(list)
    for _, _, q in questions():
        if not only or q["category"] in only:
            by_scenario[q["scenario"]].append(q)
    results = []
    for sid, qs in sorted(by_scenario.items()):
        reads = [q for q in qs if q["template"] != "move"]
        if reads:
            L = load(fx[sid], driver)
            try:
                names = L.evidence_names()
                for q in reads:
                    results.append(score(q, ask(L, q, ADAPTERS[q["template"]]), names))
            finally:
                drop(L)
        for q in qs:
            if q["template"] == "move":                         # a write: a fresh copy for each path
                runs = {}
                for name, selective in PATHS:
                    L = load(fx[sid], driver)
                    try:
                        runs[name] = ask_one(L, q, a_move, selective)
                    finally:
                        drop(L)
                results.append(score(q, runs, {}))
    return results


def summarise(results):
    by_cat = defaultdict(Counter)
    for r in results:
        c = by_cat[r["category"]]
        c["questions"] += 1
        c["correct"] += r["correct"]
        c["paths_disagree"] += not r["paths_agree"]
        if r.get("failure"):
            c[r["failure"]] += 1
    return {k: dict(v) for k, v in sorted(by_cat.items())}


def report_md(results, meta):
    s = summarise(results)
    tot = Counter()
    for v in s.values():
        tot.update(v)
    lines = [f"# Stage E1 benchmark results", "",
             f"Run {meta['started']} on commit `{meta['commit']}`; {len(results)} questions, both query paths. "
             f"Expected answers were frozen at commit `{meta['gold_commit']}` before this run.", "",
             "| Category | Questions | Correct | % | Wrong judgement | Wrong values | Missing evidence | Forbidden evidence | Error | Paths disagree |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for k, v in list(s.items()) + [("**all**", dict(tot))]:
        n = v.get("questions", 0)
        lines.append(f"| {k} | {n} | {v.get('correct', 0)} | {100 * v.get('correct', 0) / n:.0f} | "
                     f"{v.get('wrong-judgement', 0)} | {v.get('wrong-values', 0)} | {v.get('missing-evidence', 0)} | "
                     f"{v.get('forbidden-evidence', 0)} | {v.get('error', 0)} | {v.get('paths_disagree', 0)} |")
    lines += ["", "## Incorrect items", "", "| Id | Template | Failure | Expected | Actual (selective path) |",
              "|---|---|---|---|---|"]
    for r in results:
        if not r["correct"] or r.get("failure"):
            act = r.get("error") if r.get("actual") is None else {k: r["actual"].get(k) for k in r["expected"]}
            lines.append(f"| {r['id']} | {r['template']} | {r.get('failure')} | `{json.dumps(r['expected'])}` | "
                         f"`{json.dumps(act, default=str)[:300]}` |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    import subprocess
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="categories to run (default: all)")
    ap.add_argument("--out", type=Path, default=BENCH / "results")
    ap.add_argument("--gold-commit", default=None, help="the commit that froze the expected answers")
    a = ap.parse_args(argv)
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    meta = {"started": datetime.now(timezone.utc).isoformat(timespec="seconds"), "commit": commit,
            "gold_commit": a.gold_commit or "(not given)"}
    t0 = time.perf_counter()
    results = run(a.only)
    meta["seconds"] = round(time.perf_counter() - t0, 1)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "results.json").write_text(json.dumps({"meta": meta, "summary": summarise(results), "results": results},
                                                   indent=1, default=str) + "\n")
    (a.out / "report.md").write_text(report_md(results, meta))
    n = sum(r["correct"] for r in results)
    print(f"{n}/{len(results)} correct in {meta['seconds']} s -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
