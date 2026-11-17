"""Increment D (LABS-1.044): summarise alternating pre_e_d_occurrence_bench.py runs, old code against new.

    uv run python -I probes/pre_e_d_occurrence_bench_summary.py --old o1.json .. --new n1.json .. [--json out.json]

Per category (unconstrained, established, disputed, inapplicable) and per flag (variant, perspective, earlier): the
number of views, the TypeDB queries of one call of each (summed over the views; deterministic), and the time: the sum
over the views of each view's median ms, given as the median over rounds with the lowest and highest round, so that
run-to-run variation is visible beside any difference. A difference in time smaller than that spread is not a result.
"""

import argparse
import json
import statistics
from collections import defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("--old", nargs="+", required=True)
ap.add_argument("--new", nargs="+", required=True)
ap.add_argument("--json")
a = ap.parse_args()
runs = {k: [json.load(open(f)) for f in getattr(a, k)] for k in ("old", "new")}


def key(r):
    return (r["world"], r["occurrence"], r["perspective"], tuple(r["flags"]))


views = {key(r): r for r in runs["new"][0]}
groups = defaultdict(list)
for k, r in views.items():
    groups["all"].append(k)
    groups["category: " + r["category"]].append(k)
    for f in r["flags"]:
        groups["flag: " + f].append(k)
    if not r["flags"]:
        groups["flag: none (actual world, system, latest)"].append(k)
stable = all(len({by[k]["queries"] for by in ({key(r): r for r in run} for run in runs[s])}) == 1
             for s in runs for k in views)
out = {}
print(f"Rounds: old {len(runs['old'])}, new {len(runs['new'])}. Queries per call (deterministic: {stable}); time: the sum of "
      "the views' median ms, median over rounds [lowest, highest round].")
print(f"{'group':44} {'views':>5} {'queries old':>11} {'new':>6} {'ms old':>22} {'ms new':>22}")
for g, ks in sorted(groups.items()):
    row = {}
    for s in ("old", "new"):
        by = [{key(r): r for r in run} for run in runs[s]]
        q = sum(by[0][k]["queries"] for k in ks)
        sums = [sum(b[k]["median_ms"] for k in ks) for b in by]
        row[s] = {"queries": q, "ms_median": round(statistics.median(sums), 1), "ms_min": round(min(sums), 1),
                  "ms_max": round(max(sums), 1)}
    out[g] = {"views": len(ks), **row}
    o, n = row["old"], row["new"]
    print(f"{g:44} {len(ks):5} {o['queries']:11} {n['queries']:6} "
          f"{o['ms_median']:9} [{o['ms_min']}, {o['ms_max']}]".ljust(0) +
          f" {n['ms_median']:9} [{n['ms_min']}, {n['ms_max']}]")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
