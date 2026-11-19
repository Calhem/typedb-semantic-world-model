# Fresh baseline of the unchanged Core 0.3 workload (LABS-1.046, Stage E entry criterion P-1)

**Status:** recorded, for review. Nothing was optimised; no code changed. The DI-9 benchmark probes
(`bench-d3`, `probes/pre_e_b_read_bench.py`, `probes/pre_e_d_occurrence_bench.py`, `probes/pre_e_c_perf_summary.py`)
are untouched and remain the reference for DI-9 work (entry criterion P-2).

## 1. What was run
- **Workload** (plan section 9.4, unchanged since Core 0.3): `scripts/bench_instrumented.py`, which runs each
  checkout's own `scripts/bench_query_paths.py`: 200 objects, 30 places, 1,000 moves, 60 random `value_at` questions,
  seed 11. Each question is answered on the selective path and on the full load, and the answers are compared. The
  built world holds 3,200 attestations and 1,140 propositions in the actual world.
- **Implementations:** the entry commit `bf60c1f` (`main` after the consolidation merge) and unchanged Core 0.3
  `b64f635`, each from its own clean worktree and Python environment.
- **Order:** one discarded warm-up (entry commit), then 20 runs alternating M C C M M C C M ... (10 each), between
  11:13 and 12:46 UTC on 2026-11-18, with nothing else running on the database (no test suite, no other benchmark).
- **Wrapper:** `probes/pre_e_core03_baseline.py` (new) runs the bench unchanged and adds every question's latency on
  both paths and the environment. Summary: `python3 -I probes/pre_e_core03_baseline_summary.py
  docs/core-0.4/bench-pre-e-baseline` (output [bench-pre-e-baseline/summary.md](bench-pre-e-baseline/summary.md)).
- **Records:** [bench-pre-e-baseline/](bench-pre-e-baseline/): one JSON per run (`NN-main.json`, `NN-c03.json`,
  `00-warmup-main.json`) and `runs.log` (exit codes and times; every run exited 0, no error output).

## 2. Environment (identical in every run)
Apple M2 Pro, macOS (Darwin 25.5.0); TypeDB `typedb/typedb:3.14.1` in Docker (VM: 10 CPUs, 7.7 GiB, shared with 16
running containers, most of them idle services of other projects); Python 3.13.17; TypeDB driver 3.14.0. The machine
was not otherwise quiet or pinned (see section 5).

## 3. Results
| Measure (10 runs each) | Core 0.3 `b64f635`: median (min-max, CV) | Entry `bf60c1f`: median (min-max, CV) | Difference | 9.4 threshold | Result |
|---|---|---|---|---|---|
| selective median | 48.1 ms (43.3-52.9, 6.7 %) | 52.2 ms (44.7-64.3, 11.0 %) | +8.5 % | +10 % | **not demonstrable** |
| selective p95 | 67.0 ms (57.9-84.3, 13.4 %) | 83.3 ms (62.5-148.8, 28.8 %) | +24.4 % | +15 % | **not demonstrable** |
| full-load median | 3,774.4 ms (3,651.2-3,904.8, 2.8 %) | 3,707.2 ms (3,484.5-4,338.5, 5.9 %) | -1.8 % | +10 % | met |
| ingestion (1,000 moves) | 57.0 s (51.5-70.4, 11.2 %) | 52.5 s (43.7-67.4, 14.0 %) | -8.0 % | +10 % | **not demonstrable** |
| move median / p95 | 46.3 / 84.2 ms | 42.7 / 79.9 ms | -7.8 / -5.1 % | none | - |
| database size | 12.32 MB | 10.36 MB | -15.9 % | +5 % | met |
| selective: queries / attestations per question | 13.5 / 7.1 in every run | 13.5 / 7.1 in every run | equal | - | - |
| full: queries / attestations per question | 9.4 / 3,283.9 in every run | 9.4 / 3,283.9 in every run | equal | - | - |
| answers identical on both paths | 10 of 10 runs | 10 of 10 runs | - | identical | met |

"Not demonstrable" follows P-1: a threshold is judged only when both implementations' coefficient of variation for
that measure is within the 10 % tolerance. Every run's figures are in [summary.md](bench-pre-e-baseline/summary.md).

**Latency distributions** (every question of every run pooled, 600 per path, ms):
| | min | p10 | p50 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|
| Core 0.3, selective | 21.5 | 29.7 | 47.4 | 65.8 | 72.4 | 90.4 | 204.8 |
| Entry, selective | 24.1 | 33.8 | 52.9 | 79.8 | 92.7 | 169.6 | 247.0 |
| Core 0.3, full load | 2,285.8 | 2,408.2 | 3,720.4 | 4,186.4 | 4,494.1 | 5,133.5 | 8,527.3 |
| Entry, full load | 2,189.1 | 2,389.9 | 3,707.8 | 4,295.2 | 4,605.2 | 5,755.0 | 6,200.9 |

## 4. Reading the results
- **Selective questions: a small, broad slowdown at equal query counts.** Comparing each of the 60 questions with
  itself (median of 10 runs each), the entry commit is slower on the typical question by a factor of 1.11 (middle 80 %
  of questions: 1.03 to 1.19). Only 1 question is more than 25 % slower and 1 more than 20 % faster. The query count
  per question is the same (13.5), so the extra time is per query and in Python: TypeDB reads 45.2 → 47.1 ms,
  Python 3.0 → 4.8 ms (medians of run medians). This is consistent with increments B to D adding judgement work to
  every read (canonical judgement, attested constraints) without adding queries on this workload. The run-level
  median (+8.5 %) is under the threshold, and the pooled median (+11.6 %) is over it. Neither can be judged until the
  entry commit's CV (11.0 %) is within tolerance.
- **Selective p95: mostly outliers.** The p95 gap comes from occasional slow questions (above 120 ms) concentrated in a
  few entry runs (0, 1, 0, 4, 3, 4, 0, 0, 0, 1 per run, against 0 to 1 for Core 0.3) rather than from particular
  questions. Whether these outliers belong to the entry commit or to the machine's state is not established.
- **Full load, ingestion and moves:** no slowdown shown; full load is within 2 % with low variation.
- **Database size:** 15.9 % smaller with equal stored-record counts; not investigated here (it is a reduction, and
  within the threshold).
- **Earlier sessions are not comparable.** Core 0.3 measured 55.3 ms selective / 4,119.5 ms full at A0 (LABS-1.003) and
  48.1 / 3,774.4 ms here: absolute figures move between sessions, so only same-session alternating comparisons count.

## 5. What this means for the entry criterion
P-1 asked for a fresh baseline: this is it, on the entry commit, alternating, 10 runs each, median, p95 and CV
reported. As P-1 provides, the variation exceeds the 10 % tolerance for three thresholds, so **before any 9.4 threshold
is judged in Stage E the noise has to be reduced**. Options, not done here:
- stop the 16 other containers' services for the measurement window, or pin the TypeDB container's CPUs;
- increase the questions per run (`--queries`; the default 60 means each run's p95 rests on its 3 slowest questions);
- keep the alternating order and the same two worktrees.

Until then, the honest statement is: on the unchanged Core 0.3 workload, the entry commit answers selective questions
about 10 % slower at the same query count, with a heavier tail of unknown origin. Full load, ingestion and storage show
no regression. No threshold is reported as missed and none is inferred as met where the noise does not allow it.
