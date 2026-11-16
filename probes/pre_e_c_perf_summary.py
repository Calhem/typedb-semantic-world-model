"""Increment C (LABS-1.040): summarise alternating pre_e_b_read_bench.py --more runs into the aggregation overhead
and the office-exclusivity cost.

    uv run python -I probes/pre_e_c_perf_summary.py --old o1.json o2.json .. --new n1.json .. --noatt x1.json ..
                                                    [--json out.json]

old: the code before increment C (merged main d9d873a, which already applies contextual office exclusivity);
new: increment C; noatt: increment C read with --no-attested (exclusivity not applied). On the same database and the
same subjects, old -> new is the cost of the new aggregation alone (both apply exclusivity), new-no-excl -> new is the
cost of applying exclusivity (the cost recorded in LABS-1.039, DI-9). Each round's figure is the median of its calls;
the table shows the median over rounds, and the query count of one call (deterministic).
"""

import argparse
import json
import statistics

ap = argparse.ArgumentParser()
for k in ("old", "new", "noatt"):
    ap.add_argument("--" + k, nargs="+", required=True)
ap.add_argument("--json")
a = ap.parse_args()
runs = {k: [json.load(open(f)) for f in getattr(a, k)] for k in ("old", "new", "noatt")}
rows, totals = [], {}
for reader, subjects in runs["new"][0].items():
    for key in subjects:
        v = {}
        for k, rs in runs.items():
            got = [r[reader][key] for r in rs if key in r.get(reader, {})]
            v[k] = {"queries": got[0]["queries"] if got else None,
                    "ms": round(statistics.median(g["median_ms"] for g in got), 1) if got else None,
                    "query_counts_stable": len({g["queries"] for g in got}) <= 1}
        world, subject = key.split(" ", 1)
        rows.append({"reader": reader, "world": world, "subject": subject, **v})
        t = totals.setdefault(reader, {k: {"queries": 0, "ms": 0.0} for k in runs})
        for k in runs:
            t[k]["queries"] += v[k]["queries"] or 0
            t[k]["ms"] += v[k]["ms"] or 0
print(f"Rounds: old {len(runs['old'])}, new {len(runs['new'])}, new-no-excl {len(runs['noatt'])}. Median ms per call over "
      "rounds (each round's figure is itself a median of its calls); queries per call.")
print("A = old -> new differs in queries (aggregation overhead); X = new-no-excl -> new differs (exclusivity cost).")
print(f"{'':2} {'reader':18} {'world':22} {'subject':24} {'queries old/new/no-excl':>24} {'ms old':>8} {'ms new':>8} "
      f"{'ms no-excl':>10}")
for r in rows:
    q = [r[k]["queries"] for k in ("old", "new", "noatt")]
    flag = ("A" if q[0] != q[1] else " ") + ("X" if q[1] != q[2] else " ")
    print(f"{flag} {r['reader']:18} {r['world']:22} {r['subject'][:24]:24} {'/'.join(map(str, q)):>24} "
          f"{r['old']['ms']:8} {r['new']['ms']:8} {r['noatt']['ms']:10}")
print("\nTotals per reader over its subjects (queries; sum of the median ms):")
print(f"{'reader':18} {'queries old':>12} {'new':>8} {'no-excl':>8} {'ms old':>9} {'new':>9} {'no-excl':>9}")
for reader, t in totals.items():
    print(f"{reader:18} {t['old']['queries']:12} {t['new']['queries']:8} {t['noatt']['queries']:8} "
          f"{t['old']['ms']:9.1f} {t['new']['ms']:9.1f} {t['noatt']['ms']:9.1f}")
unstable = [(r["reader"], r["world"], r["subject"], k) for r in rows for k in runs if not r[k]["query_counts_stable"]]
print(f"\nQuery counts identical across rounds: {'yes' if not unstable else unstable}")
if a.json:
    json.dump({"rows": rows, "totals": totals}, open(a.json, "w"), indent=1)
