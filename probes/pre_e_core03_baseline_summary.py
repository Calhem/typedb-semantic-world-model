"""Summary of the fresh Core 0.3 workload baseline (LABS-1.046, Stage E entry criterion P-1).

    python3 -I probes/pre_e_core03_baseline_summary.py docs/core-0.4/bench-pre-e-baseline
    python3 -I probes/pre_e_core03_baseline_summary.py docs/core-0.4/bench-pre-e-controlled --first 60

`--first N` adds the run-level median and p95 of the first N questions only: with the bench's fixed seed, the first 60
questions of a 180-question run are the 60 questions of the original workload (they are drawn first, after the same
build).

Reads the run records `NN-<impl>.json` written by `probes/pre_e_core03_baseline.py` (`00-warmup-*` is discarded), where
<impl> is `main` (the entry commit) or `c03` (unchanged Core 0.3, b64f635), and prints:
1. every run: selective median / p95, full median, ingestion, move median / p95, database size;
2. per implementation: median, min-max and coefficient of variation (sample standard deviation / mean) of each measure;
   queries and attestations per question; whether selective and full answers were identical;
3. the pooled per-question latency distributions (every question of every run);
4. the entry commit against Core 0.3 and the plan section 9.4 thresholds. A threshold is reported as **met** when the
   difference is within it, **missed** when it exceeds it, and **not demonstrable** when either implementation's CV
   for that measure exceeds the 10 % tolerance (P-1: the noise must be reduced before judging).
Pure Python, reads files only.
"""

import json
import statistics
import sys
from pathlib import Path

folder = Path(sys.argv[1])
FIRST = int(sys.argv[sys.argv.index("--first") + 1]) if "--first" in sys.argv else None
runs = []
for f in sorted(folder.glob("[0-9][0-9]-*.json")):
    if "warmup" in f.name:
        continue
    impl = f.stem.split("-", 1)[1]
    runs.append((f.stem.split("-")[0], impl, json.loads(f.read_text())))
IMPLS = [("c03", "Core 0.3 (b64f635)"), ("main", "entry commit")]
NAME = dict(IMPLS)

MEASURES = [  # key, label, unit, getter, threshold (fraction) or None
    ("sel_med", "selective median", "ms", lambda r: r["bench"]["selective"]["ms_median"], 0.10),
    ("sel_p95", "selective p95", "ms", lambda r: r["bench"]["selective"]["ms_p95"], 0.15),
    ("full_med", "full-load median", "ms", lambda r: r["bench"]["full"]["ms_median"], 0.10),
    ("ingest", "ingestion", "s", lambda r: r["bench"]["ingest"]["seconds"], 0.10),
    ("move_med", "move median", "ms", lambda r: r["bench"]["ingest"]["move_ms_median"], None),
    ("move_p95", "move p95", "ms", lambda r: r["bench"]["ingest"]["move_ms_p95"], None),
    ("db", "database size", "MB", lambda r: r["bench"]["database_bytes"] / 1e6, 0.05),
]
TOLERANCE = 0.10


def fmt(x, unit):
    return f"{x:,.2f}" if unit == "MB" else f"{x:,.1f}"


def cv(xs):
    return statistics.stdev(xs) / statistics.fmean(xs) if len(xs) > 1 else 0.0


print("## Runs (after one discarded warm-up)")
print("| Run | Impl. | Selective median / p95 (ms) | Full median (ms) | Ingest (s) | Move median / p95 (ms) | DB (MB) |")
print("|---|---|---|---|---|---|---|")
for n, impl, r in runs:
    b = r["bench"]
    print(f"| {int(n)} | {NAME[impl].split(' (')[0]} | {b['selective']['ms_median']} / {b['selective']['ms_p95']} | "
          f"{b['full']['ms_median']:,.1f} | {b['ingest']['seconds']} | {b['ingest']['move_ms_median']} / "
          f"{b['ingest']['move_ms_p95']} | {b['database_bytes'] / 1e6:.2f} |")

by = {i: [r for _, impl, r in runs if impl == i] for i, _ in IMPLS}
print(f"\n## Per implementation ({', '.join(f'{NAME[i]}: {len(by[i])} runs' for i, _ in IMPLS)})")
print("| Measure | " + " | ".join(f"{NAME[i]}: median (min-max, CV)" for i, _ in IMPLS) + " |")
print("|---|---|---|")
stats = {}
for key, label, unit, get, _ in MEASURES:
    cells = []
    for i, _ in IMPLS:
        xs = [get(r) for r in by[i]]
        stats[(i, key)] = (statistics.median(xs), cv(xs))
        cells.append(f"{fmt(statistics.median(xs), unit)} {unit} ({fmt(min(xs), unit)}-{fmt(max(xs), unit)}, "
                     f"{100 * cv(xs):.1f} %)")
    print(f"| {label} | " + " | ".join(cells) + " |")
for path in ("selective", "full"):
    cells = []
    for i, _ in IMPLS:
        q = {r["bench"][path]["typeql_queries_per_question"] for r in by[i]}
        a = {r["bench"][path]["attestations_per_question"] for r in by[i]}
        cells.append(f"{' / '.join(str(x) for x in sorted(q))} / {' / '.join(str(x) for x in sorted(a))}"
                     + (" in every run" if len(q) == len(a) == 1 else " (varies)"))
    print(f"| {path}: queries / attestations per question | " + " | ".join(cells) + " |")
for label, get in (("TypeDB share of selective time (median)", lambda r: r["instrumented"]["selective"]["typedb_share_of_total"]),
                   ("TypeDB share of full-load time (median)", lambda r: r["instrumented"]["full"]["typedb_share_of_total"])):
    print(f"| {label} | " + " | ".join(f"{statistics.median([get(r) for r in by[i]]):.3f}" for i, _ in IMPLS) + " |")
print("| answers selective = full | " + " | ".join(
    f"{sum(r['bench']['identical_answers'] for r in by[i])} of {len(by[i])}" for i, _ in IMPLS) + " |")

print("\n## Pooled per-question latency (every question of every run, ms)")
print("| Impl. | Path | n | min | p10 | p50 | p90 | p95 | p99 | max | mean |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for i, _ in IMPLS:
    for path in ("selective", "full"):
        xs = sorted(x for r in by[i] for x in r["distribution"][path]["latencies_ms"])
        pct = lambda p: xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]
        print(f"| {NAME[i]} | {path} | {len(xs)} | {xs[0]:,.1f} | {pct(.1):,.1f} | {statistics.median(xs):,.1f} | "
              f"{pct(.9):,.1f} | {pct(.95):,.1f} | {pct(.99):,.1f} | {xs[-1]:,.1f} | {statistics.fmean(xs):,.1f} |")

print("\n## Entry commit against Core 0.3 (plan 9.4)")
print("| Measure | Core 0.3 | entry commit | difference | threshold | CV Core 0.3 / entry | result |")
print("|---|---|---|---|---|---|---|")
for key, label, unit, _, limit in MEASURES:
    (c, cvc), (m, cvm) = stats[("c03", key)], stats[("main", key)]
    d = (m - c) / c
    if limit is None:
        result = "no threshold"
    elif key != "db" and max(cvc, cvm) > TOLERANCE:
        result = "not demonstrable (CV above 10 %)"
    else:
        result = "met" if d <= limit else "missed"
    print(f"| {label} | {fmt(c, unit)} {unit} | {fmt(m, unit)} {unit} | {100 * d:+.1f} % | "
          f"{'+' + str(int(limit * 100)) + ' %' if limit else '-'} | {100 * cvc:.1f} % / {100 * cvm:.1f} % | {result} |")

nq = len(by["main"][0]["distribution"]["selective"]["latencies_ms"])
print(f"\n## Selective path, question by question (the same {nq} questions in every run)")
lat = {i: [r["distribution"]["selective"]["latencies_ms"] for r in by[i]] for i, _ in IMPLS}
ratios = sorted(statistics.median(x[q] for x in lat["main"]) / statistics.median(x[q] for x in lat["c03"])
                for q in range(len(lat["main"][0])))
pick = lambda p: ratios[min(len(ratios) - 1, int(round(p * (len(ratios) - 1))))]
print(f"ratio of per-question medians, entry / Core 0.3: min {ratios[0]:.2f}, p10 {pick(.1):.2f}, "
      f"median {statistics.median(ratios):.2f}, p90 {pick(.9):.2f}, max {ratios[-1]:.2f}; "
      f"questions more than 25 % slower: {sum(x > 1.25 for x in ratios)}, more than 20 % faster: "
      f"{sum(x < 0.8 for x in ratios)}")
for i, _ in IMPLS:
    print(f"{NAME[i]}: questions above 120 ms, per run: {[sum(v > 120 for v in x) for x in lat[i]]}")
for i, _ in IMPLS:
    ins = [r["instrumented"]["selective"] for r in by[i]]
    print(f"{NAME[i]}: TypeDB reads median {statistics.median(x['typedb_reads']['median_ms'] for x in ins):.1f} ms, "
          f"Python median {statistics.median(x['python']['median_ms'] for x in ins):.1f} ms (medians of run medians)")

if FIRST:
    print(f"\n## The first {FIRST} questions only (the original question set; run-level medians and p95 recomputed)")
    print("| Measure | " + " | ".join(f"{NAME[i]}: median (min-max, CV)" for i, _ in IMPLS) + " | difference |")
    print("|---|---|---|---|")
    for path in ("selective", "full"):
        for label, fn in (("median", statistics.median), ("p95", lambda xs: sorted(xs)[min(len(xs) - 1, int(round(
                0.95 * (len(xs) - 1))))])):
            per = {i: [fn(r["distribution"][path]["latencies_ms"][:FIRST]) for r in by[i]] for i, _ in IMPLS}
            cells = [f"{statistics.median(per[i]):,.1f} ms ({min(per[i]):,.1f}-{max(per[i]):,.1f}, "
                     f"{100 * cv(per[i]):.1f} %)" for i, _ in IMPLS]
            d = statistics.median(per["main"]) / statistics.median(per["c03"]) - 1
            print(f"| {path} {label} | " + " | ".join(cells) + f" | {100 * d:+.1f} % |")

envs = {json.dumps({k: v for k, v in r["environment"].items() if k not in ("commit", "containers_running")},
                   sort_keys=True) for _, _, r in runs}
print("\n## Environment")
print("commits:", {i: sorted({r["environment"]["commit"] for r in by[i]}) for i, _ in IMPLS})
print("containers running:", sorted({r["environment"]["containers_running"] for _, _, r in runs}))
print("identical in every run:" if len(envs) == 1 else "VARIES between runs:", *envs, sep="\n")
print("workload:", json.dumps(runs[0][2]["bench"]["dataset"]),
      "| attestations in the actual world:", runs[0][2]["bench"]["attestations_in_actual_world"],
      "| propositions:", runs[0][2]["bench"]["propositions"])
