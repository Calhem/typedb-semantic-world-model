# Stage E1 results

Expected answers frozen at `d0f0aa2` (fixtures, questions and author notes), before any question was answered. No
expected answer was changed afterwards. Final results: `results.json` (machine-readable, every question on both query
paths) and `report.md` (human-readable). Adjudication of every remaining discrepancy: [adjudication.md](adjudication.md).

## Runs
The harness was corrected between runs. Every correction is to how it **reads evidence** from reader answers; none
changes a question, an expected answer, a template's meaning or how judgements are compared. Correct answers were
267/272 in every run.

| Run | Harness change before it | Evidence shortfalls | Forbidden evidence cited |
|---|---|---:|---:|
| [run-1](run-1/) | (first run) | 23 | 0 |
| [run-2](run-2/) | read evidence wherever readers report it (office_holders per appointment, occurrence_status in its answer, calibration per certificate), not only a top-level `support` | 1 | 5 |
| [run-3](run-3/) | cite only what an answer rests on: an Answer's `support`; an applicability answer's `support` (rule Q), or for a dispute the disputed entries' accepted evidence; office_holders' established appointments and its conflict. Run-2 had counted claims a reader merely lists beside a "not holding" judgement (a base claim overridden by a plan's stipulation) as citations | 8 | 0 |
| final (this directory) | an applicability answer without stated support (a dispute between entries, "not yet effective") cites its applicable entries' accepted evidence; office_holders' conflict cites the exclusive-office constraint's own support | 2 | 0 |

Each change came from reading the reader's documented answer shape for a shortfall, and each rule applies to every
question of its template alike. The two remaining shortfalls are explained in the adjudication.
