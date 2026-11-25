"""Stage E2 harness: run questions and write results.json and report.md.

    uv run python -m evaluation.e2.run --questions Q.jsonl [...] --fixtures DIR --out DIR
        [--budget 5] [--reference-limit 60] [--gold-commit C] [--selftest]

For each scenario, a child process loads the fixture (evaluation.loader) and answers each question's plan, first on the
selective path under the hard budget, then on the full-load path under the reference limit (worker.py). A question whose
selective run was stopped is not run on the full-load path (its agreement is unverified). Questions are checked first
(check.py); the run refuses questions with problems. Expected answers are read, never changed.
"""

import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evaluation.e2.check import check, read_fixtures, read_questions  # noqa: E402
from evaluation.e2.report import report_md, summarise  # noqa: E402
from evaluation.e2.score import score  # noqa: E402
from evaluation.e2.worker import Worker  # noqa: E402

BUDGET_S = 5.0                     # E2-D6: hard execution budget per question, selective path (F-1)
REFERENCE_LIMIT_S = 60.0           # the full-load path has no budget (F-2); beyond this its agreement is unverified


class QuestionProblems(ValueError):
    pass


def run(question_paths, fixtures, budget=BUDGET_S, reference_limit=REFERENCE_LIMIT_S, selftest=False, log=None):
    problems = check(question_paths, fixtures, selftest)
    if problems:
        raise QuestionProblems("; ".join(f"{f}:{n} {i}: {p}" for f, n, i, p in problems[:20]))
    by_scenario = defaultdict(list)
    for _, _, q in read_questions(question_paths):
        by_scenario[q["scenario"]].append(q)
    results, workers = [], {}
    for sid, qs in sorted(by_scenario.items()):
        w = Worker(fixtures[sid], selftest=selftest)
        try:
            w.start()
        except RuntimeError as e:
            for q in qs:
                sel = {"harness_error": f"fixture did not load: {e}"}
                results.append(score(q, sel, None, {}, set(), budget, "the fixture did not load"))
            continue
        try:
            for q in qs:
                if not q["plan"]:
                    results.append(score(q, {}, None, w.names, w.recorded, budget))
                    continue
                sel = w.ask(q, True, budget)
                full, reason = None, None
                if "timeout" in sel:
                    reason = "the selective path timed out, so the reference path was not run"
                elif q["class"] != "G":
                    full = w.ask(q, False, reference_limit)
                results.append(score(q, sel, full, w.names, w.recorded, budget, reason))
                if log:
                    log(results[-1])
        finally:
            workers[sid] = {"restarts": w.restarts, "load_ms": w.load_ms}
            w.stop()
    return results, workers


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", nargs="+", required=True, type=Path)
    ap.add_argument("--fixtures", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--budget", type=float, default=BUDGET_S)
    ap.add_argument("--reference-limit", type=float, default=REFERENCE_LIMIT_S)
    ap.add_argument("--gold-commit", default=None)
    ap.add_argument("--selftest", action="store_true", help="allow the harness self-test readers")
    a = ap.parse_args(argv)
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    meta = {"started": datetime.now(timezone.utc).isoformat(timespec="seconds"), "commit": commit,
            "questions": ", ".join(str(p) for p in a.questions), "gold_commit": a.gold_commit,
            "budget": a.budget, "reference_limit": a.reference_limit, "selftest": a.selftest}
    t0 = time.perf_counter()
    results, workers = run(a.questions, read_fixtures(a.fixtures), a.budget, a.reference_limit, a.selftest)
    meta["seconds"] = round(time.perf_counter() - t0, 1)
    meta["workers"] = workers
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "results.json").write_text(json.dumps({"meta": meta, "summary": summarise(results), "results": results},
                                                   indent=1, default=str) + "\n")
    (a.out / "report.md").write_text(report_md(results, meta))
    scored = [r for r in results if r["class"] != "G"]
    print(f"{sum(r['correct'] for r in scored)}/{len(scored)} scored correct, "
          f"{sum(r['class'] == 'G' for r in results)} probes, in {meta['seconds']} s -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
