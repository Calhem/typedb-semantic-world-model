# 3a. GUPI answer baseline: results of the free stages

Run 2026-11-09 under the protocol committed at `d4d6a30` ([03-gupi-baseline-protocol.md](03-gupi-baseline-protocol.md)).
**Answer accuracy has not been measured**: stage 3 (paid) awaits approval.

## Configuration as run
| Item | Value |
|---|---|
| GUPI | `main` @ `6db22d4`, exported with `git archive` into a scratch directory; `.data` linked read-only; `uv sync --frozen` (Python 3.15 chosen by uv; typedb-driver 3.14.0). The GUPI repository was not modified (checked: clean, still on `feature/final-evaluation-pause`) |
| Database | isolated `wm-typedb` (TypeDB CE 3.14.1, 127.0.0.1:1735); one throwaway database per run, deleted afterwards (checked: 0 databases left) |
| Retriever | `gupi.evidence.keyword` (BM25, k1 1.2, b 0.75), depth 50, top 10 kept |
| Splits | GUPI's own: 53 development, 447 held-out; unchanged |
| Harness | `evaluations/gupi-lme/retrieve.py` (stage 1-2), `evaluations/gupi-lme/answer.py estimate` (token counts) |
| Outputs | `evaluations/gupi-lme/results/retrieval-{dev,heldout}.json`: question ids, retrieved observation ids, recall; no dataset text and no answers |

The `gupi_git` field in the outputs is empty because the export is not a git checkout. The commit is recorded here.

## Retrieval results
| Split | Questions | Session recall@10 | Turn recall@10 | Retrieval p50 / p95 per question | Ingest time | Peak Python memory |
|---|---|---|---|---|---|---|
| Development | 53 | 0.958 | 0.867 (49 with marked turns) | 0.139 s / 0.368 s | 194 s | 1.9 GB |
| **Held-out** | **447** | **0.930** | **0.791** (430 with marked turns) | 0.146 s / 0.344 s | 1,733 s | 1.3 GB |

**Reproduction check:** GUPI's own Phase 5 held-out keyword run reports session recall@10 **0.9296** on the same
447 questions (`docs/evaluation/phase-5/longmemeval-heldout-all.json`). This run gives 0.930. The exported code
reproduces GUPI's published retrieval.

## Real token counts and cost (replaces the protocol's estimate)
Contexts were built from the actual retrieved turns. Tokens are approximated as 4 characters per token; the paid
run records the provider's exact counts.

| Condition | Questions | Answer input tokens | Mean per question | Estimated cost (answer + judge) |
|---|---|---|---|---|
| K10, development | 53 | 137,953 | 2,603 | $0.08 |
| O, development | 53 | 339,606 | 6,408 | $0.11 |
| K10, held-out | 447 | 1,162,679 | 2,601 | $0.67 |
| O, held-out | 447 | 3,109,013 | 6,955 | $0.96 |
| **Total** | | | | **≈ $1.82 (cap $5)** |

Prices assumed: gpt-4o-mini $0.15 / $0.60, gpt-4o $2.50 / $10 per million tokens (third-party trackers; to confirm).

## Failures and limitations so far
- None in the free stages. Peak memory comes mostly from loading the 277 MB dataset file.
- The judge prompts are not yet wired into `answer.py`; that is deliberate until the paid stage is approved.
- The answer prompt text is fixed in `answer.py` (committed with these results, before any development answer
  run). Any change before the held-out answer run will be committed with a reason.
- Only GUPI's keyword retriever is evaluated. Its claim layer forms nothing on LongMemEval, and embeddings were
  limited to a subset in GUPI's own work.
