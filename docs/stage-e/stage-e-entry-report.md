# Stage E entry report (LABS-1.054)

**Status: at the Stage E entry review gate.** Branch `feature/stage-e-entry-validation`, from verified `main` at
`8663cb2`. Nothing in `src/`, the schema, the ontology, the frozen benchmark or the reference results was changed.
Stage E2 is designed ([stage-e2-evaluation-design.md](stage-e2-evaluation-design.md)) but not implemented. Not merged.

Records: [stage-e-entry/](stage-e-entry/) (`validation/`, `performance/`, the E2 capability inventory). Probes:
`probes/stage_e_scale.py`, `probes/stage_e_di9_queries.py`, `probes/stage_e_entry_di.py` (+ `.out.txt`).

## 1. Summary

| Item (LABS-1.054 step) | Result |
|---|---|
| 2. Regression suite, twice in all four configurations | **8 / 8 runs: 744 passed** (one known driver warning); no `wm-test-*` database left |
| 2. 106,752-answer reference baseline | **106,752 identical** to S6 (reconciled) and to S5 (approved); a fresh rebuild on `main` is **106,752 identical** after masking ids and clock times |
| 2. 398 occurrence views | **398 / 398, 0 differences** (fields, judgements, role presentation) on the kept database and on a fresh build |
| 3. 1×, 5×, 10× scale | measured on two axes (more worlds; more perspectives). Answers identical at every scale; query and transaction counts identical; time grows 1.26–1.62× overall. Core 0.3 measured at 1× and 5×; **10× did not complete** (Docker stopped, section 3.5) |
| 4. DI-7, DI-17, DI-19 | all three reproduce exactly as registered (section 4) |
| 4. DI-9 | cross-world slowdown reproduced and quantified; the cause is narrowed but **not proven** (section 4.4) |
| 5–7. E2 competency questions, gaps, independent gold | designed: about 180 scored questions + about 25 gap probes, classes A/H/G, gold method independent of the implementation |
| 9. Commits | `e54eb7a`, `941146d`, and this report's commit (section 9) |

## 2. Validation

### 2.1 Regression matrix (two runs × four configurations)
From a detached worktree at `8663cb2`, serially (the suite's teardown deletes every `wm-test-*` database, so runs never
overlap). `WM_SELECTIVE` 1/0 × `WM_PROFILES` 0/1. Record: [validation/suite-matrix.txt](stage-e-entry/validation/suite-matrix.txt).

| Configuration | Run 1 | Run 2 |
|---|---|---|
| selective, no profiles | 744 passed (15:49) | 744 passed (13:31) |
| selective, profiles | 744 passed (13:56) | 744 passed (18:34) |
| full load, no profiles | 744 passed (11:23) | 744 passed (13:45) |
| full load, profiles | 744 passed (14:24) | 744 passed (12:45) |

Wall times vary because the reference snapshots ran at the same time on the same server; they are not performance data.

### 2.2 Reference baseline (106,752 answers)
- **S7**: `main` reading the kept upgraded reference database. S6 → S7 and S5 → S7: 106,752 identical, 0 extended,
  0 changed, 0 other, in every reader ([validation/snapshot-*.out.txt](stage-e-entry/validation/)).
- **S8**: `main` building a fresh reference database (`wm-probe-stage-e`, 11 worlds, 322 attestations) and reading it.
  S7 vs S8 after masking attestation ids and clock times: 106,752 identical, 0 different
  ([validation/repro-S7-up--S8-fresh.out.txt](stage-e-entry/validation/repro-S7-up--S8-fresh.out.txt)).

So the merged `main` reproduces the approved answers both on the old database and from scratch.

### 2.3 Occurrence views (398)
On both databases: 398 frozen views, 398 now, same views; existing fields, judgements and role-presentation changes
all 0 different ([validation/views-*.out.txt](stage-e-entry/validation/)).

## 3. Performance (1×, 5×, 10×)

### 3.1 Method
- **Server and host:** TypeDB 3.14.1 in Docker (10 CPUs, 7.7 GiB), Apple M2 Pro. Other projects' containers kept
  running (15 at the start), so absolute numbers carry that noise; ratios between scales are the result.
- **Scale databases** (`probes/stage_e_scale.py`): the reference worlds plus K − 1 filler units of about 300–330
  attestations each (ids `zf-`, times in 2025, so they never touch the reference subjects):
  - *worlds axis*: each unit adds 3 actual worlds and 6 hypothetical variants (47 worlds at 5×, 92 at 10×);
  - *perspectives axis*: each unit adds 4 new attesters writing into the reference's own `actual`, `lab` and `org`
    worlds (still 11 worlds).
- **Reads:** a fixed set of 267 calls across 14 readers on the reference subjects only, 5 rounds per pass, two passes
  (second in reverse database order); the driver is wrapped to count queries and transactions. Answers masked (ids,
  clock times) and compared with 1×.
- Records: [performance/](stage-e-entry/performance/) (`build-*`, `read1-*`, `read2-*`, `di9-queries.json`,
  `core03-*.json`, `analysis.md`, `run-log.txt`).

### 3.2 Ingestion and size

| Database | Attestations | Worlds | Ingestion (filler) | Reference ingestion | Size |
|---|---|---|---|---|---|
| 1× | 322 | 11 | – | 55.7 att/s | 0.91 MB |
| worlds 5× | 1,633 | 47 | 52.2 att/s | 71.1 att/s | 2.26 MB |
| worlds 10× | 3,272 | 92 | 58.6 att/s | 74.7 att/s | 3.93 MB |
| perspectives 5× | 1,522 | 11 | 70.3 att/s | 63.4 att/s | 2.17 MB |
| perspectives 10× | 3,022 | 11 | 70.4 att/s | 63.5 att/s | 3.73 MB |

Ingestion throughput does not fall with size at these scales; size grows linearly (about 1 KB per added attestation).

### 3.3 Reads

| Database | Time per round (sum of 267 per-call medians) | All calls p50 / p95 / p99 | Queries / transactions per round | Answers vs 1× |
|---|---|---|---|---|
| 1× | 26.0 s | 61 / 380 / 644 ms | 14,601 / 1,950 | – |
| worlds 5× | 33.4 s (×1.29) | 81 / 425 / 702 ms | 14,601 / 1,950 | 267 / 267 identical |
| worlds 10× | 41.4 s (×1.59) | 98 / 466 / 840 ms | 14,601 / 1,950 | 267 / 267 identical |
| perspectives 5× | 32.7 s (×1.26) | 77 / 441 / 889 ms | 14,601 / 1,950 | 267 / 267 identical |
| perspectives 10× | 42.1 s (×1.62) | 97 / 536 / 1,167 ms | 14,601 / 1,950 | 267 / 267 identical |

The two passes agree within 3–11 %. **No call changes its query or transaction count with scale**: every slowdown is
per-query cost, not more queries. Per reader (p50, ratio to 1×; full table with p95 in
[performance/analysis.md](stage-e-entry/performance/analysis.md)):

| Reader | worlds 10× | perspectives 10× | Reader | worlds 10× | perspectives 10× |
|---|---|---|---|---|---|
| parts | **×2.87** | ×1.84 | changes | ×1.70 | ×1.67 |
| occurrence | ×1.88 | **×2.08** | value_at | ×1.78 | ×1.76 |
| office_holders | ×1.84 | ×1.93 | provenance | ×1.27 | ×1.75 |
| causes_of | ×1.75 | ×1.82 | offices_of | ×1.45 | ×1.80 |
| capable | ×1.77 | ×1.70 | interpretations | ×1.32 | ×1.38 |
| calibration_status | ×1.61 | ×1.91 | facts_about | ×1.32 | ×1.28 |
| authorised | ×1.48 | ×1.78 | occurrence_status | ×1.53 | ×1.70 |

### 3.4 What the additional worlds and perspectives change
- **Additional worlds (same subjects, unrelated worlds):** every reader slows, so queries pay for data in worlds they
  do not read (DI-9's cross-world effect, now measured at three points). The outlier is **`parts`, which grows roughly
  in proportion to the number of worlds**: `parts actual bay-1` 29 → 307 ms (×10.5), `parts actual gbx-100` 32 → 306
  ms (×9.7) at 92 worlds against 11. Its query does not narrow to the world before matching parthood.
- **Additional perspectives (same worlds, more attesters):** similar overall growth; the largest is `occurrence` in the
  actual world (×3.0–3.2 on every reference occurrence), which reads every account in the world, so more attesters in
  that world means more accounts to judge, even when they say nothing about the occurrence. `provenance` and
  `offices_of` also grow more on this axis than on the worlds axis, for the same reason.
- **Growth is sub-linear overall** (10× data → about 1.6× time) and the answers do not change.

### 3.5 Core 0.3 workload (`value_at` on both paths, plan 9.4)

| Scale | Ingest (move median / p95) | Selective median / p95 | Selective queries / attestations per question | Full load median / p95 | Full: attestations per question | Size |
|---|---|---|---|---|---|---|
| 1× (200 objects, 30 places, 1,000 moves) | 33.5 / 70.7 ms | 44.6 / 62.3 ms | 13.5 / 7.1 | 3,513 / 4,004 ms | 3,283.9 | 10.4 MB |
| 5× | 58.5 / 113.2 ms | 142.0 / 293.8 ms | 13.0 / 8.2 | 53,539 / 61,406 ms | 16,373.5 | 51.1 MB |
| 10× | **not completed** | | | | | |

- 1× agrees with the LABS-1.046 ten-run baseline (selective 52.2 ms, full 3,707 ms; identical counts 13.5 / 7.1 and
  9.4 / 3,283.9), single run here. Selective and full answers identical at 1× and 5×.
- 1× → 5×: the **selective path** keeps its query count and attestations per question (so the selective design holds)
  but gets 3.2× slower per question; the **full load** grows 15× (it reads 5× the attestations, and each costs more).
- **10× did not complete.** About an hour in (full-load phase, which at 5× already took about 53 s per question),
  the TypeDB connection broke and Docker Desktop was no longer running (`performance/core03-10.error.txt`). The cause
  (Docker VM memory, a crash, or Docker being quit) is not known; Docker was not restarted from this session because it
  also hosts other projects. The 10× full-load measurement is impractical at about 3–4 minutes per question in any
  case; a 10× selective-only run is proposed (decision D-6).

## 4. Deferred issues in isolation
Reproductions: `probes/stage_e_entry_di.py` → [`probes/stage_e_entry_di.out.txt`](../../probes/stage_e_entry_di.out.txt)
(throwaway databases, deleted afterwards; 6.7 s). No correction implemented.

### 4.1 DI-7: formal derivation provenance is not recorded
- **Observed:** `laboratory.interpret(..., basis='inference')` is refused, but the core `wm.attest(..., basis='inference')`
  accepts the same write. The answer is `INFERRED` (holds, judgement established), with only a `rests-on` evidence
  record; the schema has no rule, derivation or premise type.
- **Expected** (world ontology v0.2 E6; D-D3-4): `INFERRED` only for an attestation that names its rule and premises and
  whose attester is the reasoner; usable only while every premise is.
- **Potential corrections** (register): (a) a derivation record (rule + premises), with other `inference` attestations
  reported as testimony; (b) refuse `basis=inference` without one; (c) documentation only. Register recommends (a) + (b).
- **Stage E relevance:** E2's multi-step family (X) needs derivations it can cite; until (a) exists those questions are
  gaps (GAP-MULTI), not failures.

### 4.2 DI-17: conflict-group identity may be over-restrictive
- **Observed:** s1~s2 and s2~s3 established, s1~s3 denied: nothing merges (s1~s2 is set aside too), one conflict group
  is reported.
- **Expected:** this is the approved ID-5 behaviour (LABS-1.049, case I16). The risk is that one denial switches off
  every sound equivalence in the group.
- **Reference impact:** 0 `same-as` attestations and 0 conflict groups in the reference data (78 contexts). The E1/E2
  data therefore cannot show whether this matters.
- **Potential corrections** (each needs its own design): keep links not on a path to the disputed pair; merge maximal
  consistent subgroups; merge and flag.

### 4.3 DI-19: a constraint dispute through `holds()` does not cite the constraint
- **Observed:** `holds()` is DISPUTED with support `[a-bea]` and conflicts `[a-cal]`, and the exclusive-office
  attestation `x-sm` appears nowhere in the answer. The canonical judgement (`constraints[].judgement.support`) and
  `organisation.office_holders` (`conflict.constraint.support`) do carry `x-sm`. E1 question ORG-011 (revised): correct
  judgement, evidence recall 0.667.
- **Expected:** the answer to a constrained question cites the rule that caused the dispute.
- **Potential correction** (proposed in the register, not implemented): additive `constraint_support` on `holds()`
  answers; existing fields unchanged; the 106,752-answer baseline gains the field only on constraint disputes.

### 4.4 DI-9: query counts and cross-world scaling (performance)
- **Reproduced:** with the reference worlds unchanged and more unrelated worlds in the database, the DI-9 calls slow at
  identical query and transaction counts (median ms at 11 / 47 / 92 worlds):

  | Call | 1× | 5× | 10× | Queries / transactions |
  |---|---|---|---|---|
  | `where` (gbx-100, f-workshop) | 242 | 289 | 438 | 39 / 8 |
  | `effects_of` (worklog replacement) | 256 | 376 | 504 | 197 / 33 |
  | `contents` (bay-1) | 63 | 77 | 88 | 38 / 7 |
  | `facts_about` (gbx-100) | 57 | 65 | 80 | 20 / 4 |
  | `value_at` (gbx-100) | 14 | 18 | 22 | 11 / 3 |
  | `provenance` (s12-b) | 458 | 588 | 737 | 336 / 80 |
  | `measurement_calibration` (sample-12) | 553 | 665 | 809 | 411 / 111 |

  The report counts (336 and 411 queries) are unchanged from DI-9's original record.
- **Cause, narrowed but not proven.** The probe timed each query from submission to the driver's first response
  (`q.run`). That time is **flat across scales** (for `where`: 204 / 200 / 197 ms per round), while the whole call grows
  (242 → 438 ms). So the extra time is spent after the first response: most plausibly in streaming the rows of each
  answer (TypeDB executes lazily, so a query's work continues while its rows are read), possibly in opening read
  transactions. Per-query-shape attribution therefore needs a second probe that times each query **including reading
  all its rows**; that is a small probe change, not done here because the server became unavailable.
- **Clearest single target:** `parts`, which grows almost in proportion to the number of worlds (section 3.4).
- **Potential corrections** (register options): (b) narrow each query to the world (and its bases) before matching
  types; (a) batch the per-item reads in reports (336 / 411 queries); (c) accept and budget. The measurements support
  doing (b) first, for `parts` and `occurrence`, then (a).

## 5. Benchmark coverage
- **Frozen and unchanged:** the 106,752-answer reference snapshot (S5 approved, S6 reconciled), 398 occurrence views,
  744 tests, the E1 benchmark and its revised results (not touched).
- **Added at entry:** scale databases on two axes with a fixed 267-call read set and masked answer comparison; DI-9
  per-call query and transaction counts; DI-7/17/19 reproductions.
- **E2 (designed):** six families (spatial transformations S, frames F, measurements M, causal relationships C, process
  steps P, multi-step X), about 180 scored questions and about 25 gap probes. Class A (answerable and harness-ready):
  only part of M6; class H (public reader exists, harness work needed): most; class G (capability not implemented):
  identified per question with a named gap (GAP-SPATIAL, -FRAME, -MEAS, -CAUSE, -PROC, -MULTI, -HARNESS). Rule G-1:
  a gap is never scored as a reasoning failure. See the design, sections 3–4, and the
  [capability inventory](stage-e-entry/e2-capability-inventory.md).

## 6. Correctness risks
1. **Gold resting on the implementation.** E1's reader documentation was the code's own docstrings. E2 requires reader
   contracts written from the design documents and approved before any gold is written (E2-D3).
2. **INFERRED without a derivation (DI-7).** Any question about inferred facts can be answered "correctly" by an
   attestation that names no rule. E2 treats derivation questions as gaps until DI-7 is resolved.
3. **Incomplete provenance on constraint disputes (DI-19).** Evidence-recall scoring will keep marking these answers
   down; the expected-answer specification must say which field carries constraint evidence, or DI-19 must be fixed
   first (decision D-3).
4. **Identity conflicts untested by the data (DI-17).** No reference or benchmark data contains a conflict group, so
   the over-restriction risk is invisible to every current metric. E2 should include identity-conflict cases if
   identity matters to any family (it does for X).
5. **Performance budget under scale.** A 5 s budget per question (proposed for E2) holds at 10× for every measured
   reader on the selective path, but the full-load path is already about 53 s per question at Core 0.3 5×; E2 must run
   on the selective path, or the budget fails for reasons unrelated to reasoning.
6. **Measurement noise.** Other projects' containers ran throughout; between-pass agreement is 3–11 %. Ratios are
   reliable to roughly ±10 %, absolute times less so.

## 7. Proposed Stage E entry acceptance criteria
Met by this branch unless noted.

| ID | Criterion | Status |
|---|---|---|
| EN-1 | 744 tests pass twice in all four configurations | **met** (8 / 8) |
| EN-2 | 106,752 reference answers identical to the approved snapshot, on the kept database and on a fresh build (after masking) | **met** |
| EN-3 | 398 occurrence views identical to the frozen baseline | **met** |
| EN-4 | Answers identical at 1×, 5× and 10× on both axes; query and transaction counts unchanged by scale | **met** |
| EN-5 | Time growth at 10× recorded per reader, and no reader above 5 s at 10× (selective path) | **met** (worst p95 1.6 s, `provenance`) |
| EN-6 | Core 0.3 workload measured at 1× and the scale trend recorded | **met at 1× and 5×; 10× not completed** |
| EN-7 | DI-7, DI-9, DI-17, DI-19 reproduced in isolation, with expected semantics and options | **met** (DI-9 cause narrowed, not proven) |
| EN-8 | E2 questions classified A/H/G, with gold method independent of the implementation | **met** (design; awaiting approval) |

## 8. Decisions for review

| ID | Decision | Recommendation |
|---|---|---|
| D-1 | Accept the Stage E entry baseline (EN-1 to EN-8) with the Core 0.3 10× gap noted | accept |
| D-2 | DI-9: next step is the follow-up probe (timing each query including row reads), then narrowing `parts` and `occurrence` to the world first (option b); no change before that is measured and approved | approve the probe; the code change needs its own approval |
| D-3 | DI-19: implement the additive `constraint_support` before E2, or have the E2 specification name where constraint evidence is found | implement before E2 (small, additive), subject to its own approval |
| D-4 | DI-7: keep derivation questions as E2 gaps until the derivation record is designed | yes |
| D-5 | DI-17: add identity-conflict cases to E2 so its risk becomes measurable; no semantic change | yes |
| D-6 | Core 0.3 10×: rerun selective path only, after Docker is restarted, or accept 1× and 5× | rerun selective only |
| D-7 | Keep `wm-probe-stage-e` (fresh reference build from `main`) as the new reference database; drop the `wm-probe-scale-*` databases | yes |
| D-8 to D-14 | The E2 design decisions E2-D1 to E2-D7 ([design section 8](stage-e2-evaluation-design.md)) | as recommended there; the owner sets the E2 thresholds (E2-D6) |

## 9. Commits on `feature/stage-e-entry-validation`
- `e54eb7a` test(stage-e): entry probes for scale, DI-9 query shapes and DI-7/17/19
- `941146d` docs(stage-e): Stage E2 evaluation design and capability inventory
- this report and the validation and performance records (hash given in the gate message)

## 10. Housekeeping still open
- Docker Desktop stopped during the last benchmark; it was not restarted from this session. Once it is running:
  drop `wm-probe-scale-worlds-{1,5,10}`, `wm-probe-scale-perspectives-{5,10}`, and any `wm-bench-*` database left by the
  interrupted 10× run.
- The detached worktree used for the long runs can be removed after review.
