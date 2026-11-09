# 3. GUPI answer-quality baseline: protocol (frozen before execution)

**Status:** this protocol is committed before any run. Changes after the development run must be committed before
the held-out run, and none are allowed after it (GUPI's own rule, `benchmarks/config.json`).

## 3.1 What was found when inspecting GUPI (V, read 2026-11-09)
- **There is no existing GUPI answer-quality evaluation for LongMemEval.** GUPI's LongMemEval work is
  retrieval-only: Phase 5 (all 447 held-out questions, keyword) and Phase 6D (a 64-question held-out subset).
- GUPI's only answer harness, `benchmarks/phase8c_answers.py` (unmerged branch), targets **LoCoMo**. It uses AML's
  prompts and `gpt-4o-mini`, and "a paid run has no command until it has its own approval". It was never run.
- **On LongMemEval, GUPI main formed 0 claims** (Phase 6D: 31,839 observations, 0 with candidates). So GUPI's
  structured retriever returns nothing on this dataset. Its contribution here is its **BM25 keyword retriever over
  turns stored in TypeDB**, scoped to the question's own sessions.
- **Splits (kept unchanged):** `benchmarks/split.json` fixes 53 development questions (sha256(question_id) mod 10
  == 0; verified) and **447 held-out** questions. Held-out by type: multi-session 121, temporal-reasoning 120,
  knowledge-update 71, single-session-user 59, single-session-assistant 50, single-session-preference 26; 25 are
  abstention (`_abs`).

So this is an **answer-quality baseline for GUPI's current retrieval on LongMemEval**, not a test of its claims.
That is still the baseline the world-ontology memory profile must beat or match later.

## 3.2 Exact configuration
| Item | Value |
|---|---|
| GUPI version | `main` at `6db22d4` (Stage 4 merge), exported read-only with `git archive` into a scratch directory; the GUPI repository is not modified. Unmerged research branches (Phase 8 conversational retrieval) are **excluded** |
| Dataset | LongMemEval S cleaned, revision `98d7416c…`, `longmemeval_s_cleaned.json` SHA-256 `d6f21ea9…`; oracle file `longmemeval_oracle.json` SHA-256 `821a2034…` (GUPI docs/datasets.md); MIT licence |
| Database | an isolated TypeDB 3.14.1 (`wm-typedb`, 127.0.0.1:1735), throwaway database per run, deleted afterwards |
| Retrieval | GUPI `evidence.keyword` (BM25, k1 1.2, b 0.75, frozen in GUPI's config), scope = the question's own sessions, depth 50; **top 10 turns** passed to the answerer |
| Conditions | **K10:** GUPI keyword top-10 turns. **O:** the oracle file's evidence sessions (upper bound for retrieval). (Embedding and hybrid are excluded: GUPI limited embeddings to a 64-question subset for cost, and on this dataset hybrid = keyword + embedding) |
| Context format | each turn as `[session date] role: text`, ordered by date, then the question and its question date |
| Answerer | `gpt-4o-mini-2024-07-18`, temperature 0, max 256 output tokens; instruction: answer from the history only; say the information is not available if it isn't |
| Judge | LongMemEval's official `evaluate_qa.py` prompts (per question type, abstention prompt for `_abs`), judge `gpt-4o-2024-08-06`, temperature 0, max 10 tokens, as in the official script |
| Metric | accuracy = judge "yes" / questions, overall and per type; 95% bootstrap intervals (10,000 resamples, seed 0); K10 vs O paired |
| Retrieval metrics | session and turn recall@10 from GUPI's own `metrics` function (gold evidence ids only; no answers read) |

## 3.3 Leakage rules
1. Development questions only for checking the pipeline (formatting, parsing). **No tuning** on held-out results.
2. The prompt and the parameters above are frozen in this commit. Any change after the development run is
   committed, with a reason, before the held-out run.
3. Gold answers are read only by the judge step. The retrieval stage never reads them.
4. The judge prompt is LongMemEval's, unmodified.

## 3.4 Stages and gates
| Stage | Cost | Gate |
|---|---|---|
| 1. Export GUPI main; retrieval on **development** (53) | free, local | runs now |
| 2. Retrieval on **held-out** (447); token counts from the real contexts | free, local | runs after stage 1 passes |
| 3. Answer + judge on development, then held-out | **paid (OpenAI)** | **needs your approval and your `OPENAI_API_KEY`**; hard cap enforced by the script |

## 3.5 Cost estimate (stage 3)
Measured sizes (V, from the dataset): a turn averages 975 characters (≈ 244 tokens), so a 10-turn context is
≈ 2,700 input tokens with instructions. Oracle evidence averages 26,425 characters (≈ 6,800 tokens).
Prices: `gpt-4o-mini` $0.15 / $0.60 and `gpt-4o` $2.50 / $10.00 per million input / output tokens (third-party
trackers, A: confirm on OpenAI's pricing page before running).

| Item | Tokens (447 held-out) | Cost |
|---|---|---|
| K10 answers | 1.21 M in, ≈ 0.07 M out | ≈ $0.22 |
| O answers | 3.04 M in, ≈ 0.07 M out | ≈ $0.50 |
| Judge, 2 conditions | ≈ 0.31 M in, ≈ 4.5 k out | ≈ $0.83 |
| Development run (53, both conditions) | ≈ 12% of the above | ≈ $0.19 |
| **Total** | | **≈ $1.75; hard cap $5** |

Stage 2 replaces these estimates with token counts from the actual retrieved contexts.
**Optional:** `gpt-4o` as answerer (closer to the LongMemEval paper's setup) adds about $8 for both conditions.

## 3.6 Known limitations
- The baseline measures **retrieval + a fixed answering model**, not GUPI's claim layer, which forms nothing here.
- The judge is a model; the official prompts are used, and 10% of judgements (stratified by type) should be checked
  by a person before results are quoted.
- A single answering model and seed; no variance across models.
- LongMemEval is chat-assistant memory, where GUPI found structure does not help retrieval. A null result here says
  little about dense-relationship domains (Phase 1B 05 §5.6).
