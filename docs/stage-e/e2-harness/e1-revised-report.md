# Stage E1 benchmark results, revised evaluation

Run 2026-11-24T14:10:33+00:00 on commit `38c7b41`; 272 questions, both query paths. Expected answers were frozen at commit `(not given)` before this run.

**Revised evaluation** (LABS-1.052): the frozen questions with `benchmark/e1/revised/overlay.json` applied (4 revised: LAB-010, ORG-011, TEMP-017, X-003), event_role unions scored from the resolved role-player set (R1), restatements counted as their claims' evidence (C3). See `benchmark/e1/CLARIFICATIONS.md`. The original evaluation is in `benchmark/e1/results/`.

| Category | Questions | Correct | % | Wrong judgement | Wrong values | Missing evidence | Forbidden evidence | Error | Paths disagree |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| conflict-provenance | 30 | 30 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| cross-domain | 33 | 33 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| identity | 42 | 42 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| laboratory | 36 | 36 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| mechanical | 33 | 33 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| organisation | 31 | 31 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| temporal | 37 | 37 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| worlds-perspectives | 30 | 30 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| **all** | 272 | 272 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |

## Incorrect items

| Id | Template | Failure | Expected | Actual (selective path) |
|---|---|---|---|---|
