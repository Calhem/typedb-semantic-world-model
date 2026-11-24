# Stage E, DI-9: the F6 supersession lookup correction (LABS-1.058)

Branch `feature/stage-e-entry-validation`.
- Starting point: d9fb186 (O-1, O-2 and O-3, the O-3/F6 review).
- Correction: 75dd89b.
- Decisions approved for this step: DI9-D14, D15 and D16. DI9-D11 stays open and DI9-D13 (merge) stays deferred.
- Not done here: no merge into main, no scoped loading in other readers, no ontology change, no Stage E2.

## 1. Summary
- **The change.** `_level` now reads the supersessions of its anchored attestations in two queries instead of one.
  The first query reads the pairs and their recorded times, anchored as before. The second reads the new
  attestations by id. Both run in the same transaction. This is the S formulation measured in LABS-1.057.
- **Correctness.** Every check gives the same answers as before:
  - 877 tests in four configurations, each run twice;
  - 106,752 reference answers, 0 changed;
  - 398 occurrence views, 0 different;
  - E1 272/272;
  - 267/267 scale-read answers identical on all five scale databases.

  62 new tests compare the two forms on complete results.
- **Core 0.3 selective, median p50 per question:**

  | Scale | Before | After | Before ÷ after |
  |---|---|---|---|
  | 1× | 19.6 ms | 16.6 ms | 1.2× |
  | 5× | 50.0 ms | 18.5 ms | 2.7× |
  | 10× | 66.0 ms | 17.5 ms | 3.8× |

  Latency is now flat from 1× to 10×.
- **`where` at 92 against 11 worlds:**
  - Before: median 1.23×. 6 of 7 runs were above 1.2×, the highest 1.32×.
  - After: median 1.05×. No run was above 1.2× (0 of 7), the highest 1.12×.

  The 1.2× target is met in every run, without changing the threshold.
- **Costs:** one more query per lookup that has supersessions (+0.6 % queries on the scale read set, +1 per Core 0.3
  question). No reader is slower at small scale. Large anchor counts are where the gain is largest, so there is no
  fallback.
- **Cause of the slowdown.** TypeDB 3.14.1 slows down when a query matches two role players of the attestation it
  reaches through the supersession, and those role players are not narrowed to concrete types. A minimal schema
  reproduces this. The reproduction is kept private for review and nothing has been published.

## 2. The change (75dd89b)
`WorldModel._supersessions(tx, follow)` replaces the single supersession query in `_level`:

1. **Pairs.** For each anchored attestation, the query reads (old id, new id, recorded-at) through `follow`. That is
   the same `_anchored` path as before, including its head-form fallback above ANCHOR_MAX ids:
   `$su isa supersession (old: $a, new: $n), has recorded-at $srec; $n has wm-id $nid;`
2. **New attestations.** For the distinct new ids, the query reads their world, attester, stance and optional
   valid-from-earliest. It runs on the same transaction, with given rows of ANCHOR_CHUNK ids per query.
3. **Rebuilt rows.** The rows are rebuilt as the cross product, per new id, of the pair rows and the attribute rows.
   This is exactly the answer multiset of the single query:
   - `wm-id` is a key, so each id names one attestation;
   - a duplicated supersession relation gives two pair rows, as before;
   - a new attestation without a world, attester or stance gives no row, as before;
   - an attestation with no valid-from-earliest gives one row with the value missing.
4. **No pairs, no second query.** The query count rises by one only when there are pairs.

Everything after this is unchanged:
- `_load` still filters by knowledge time, by the branch's valid-time limit and by the new attestation's world;
- the superseder acceptances are a separate, unchanged query, measured flat (section 4.3);
- perspectives, acceptance states and judgements are untouched.

`SUPERSESSION_TWO_STEP = False` keeps the single query as the reference that the tests compare with. The probes use
it too.

## 3. Semantic checks
### 3.1 Focused tests: `tests/test_y_f6_supersession.py` (62 tests)
Every test runs both forms. Raw `_level` rows are compared as multisets, since TypeDB's answer order is not part of
the result, and `_load` and reader answers are compared in full.

| Case | Covered by |
|---|---|
| Several supersessions | a chain a1 → a2 → a3; one attestation corrected twice (two successors); an `end` |
| Duplicate targets | one new attestation superseding two old ones; a duplicated supersession relation (two rows kept, folded once by `_load`) |
| Optional field missing | a correction with no start |
| Disputed acceptances | the last correction accepted by one perspective and rejected by another; 4 perspectives |
| Inherited worlds | a branch made before the corrections; the branch correcting its base; a base correction starting after the branch point |
| Temporal boundaries | `_load` at 7 knowledge times, before, exactly at and after each supersession |
| Readers | `value_at` at 4 valid times, plus `facts_about` |
| Empty results | an empty world (no follow-up queries); an attestation with no successor (no second query); an empty head |
| Uncommitted writes | an operation's own `end`, seen inside the operation by both forms and invisible outside it |
| Anchoring | chunks of 1 and 2 ids, and the head-form fallback (ANCHOR_MAX 1 and 3) |
| Query shape | two queries, the first without the new attestation's attributes |

A mutation check confirmed the tests catch broken implementations:

| Deliberate break | Tests failed |
|---|---|
| Deduplicate the pairs | 11 |
| Drop rows with no start, and keep only the first row per new id | 17 |
| Run the second query in another transaction | 1 (the uncommitted-write test) |

The code was restored after each check.

### 3.2 Full regression on 75dd89b, from its own worktree (`di9-f6-correction/validate-f6-full/`)

| Check | Result |
|---|---|
| Test suite: 877 tests (815 existing + 62 new); four configurations (selective on/off × profiling on/off), each run twice | 8 of 8 runs: 877 passed, 0 failed |
| Reference answers, upgraded database against S5 and S7 | 106,752 identical, 0 extended, 0 changed, 0 other (each) |
| Reference answers, fresh database against S8 | 106,752 identical, 0 changed |
| 398 frozen occurrence views, upgraded and fresh databases | 398 = 398 on both; 0 differences; output identical to O-3's |
| E1 (revised question set) | 272/272 correct |
| Scale-read answers in the benchmarks (masked), five databases, both passes | 267/267 identical to the single query on each |

The only warning was a SyntaxWarning that the TypeDB driver package prints the first time a fresh virtual environment
compiles it.

The Mac went into clamshell sleep once during the test-suite part (17:24:55 UTC). That does not affect correctness:
every run passed. No benchmark step had a sleep event.

## 4. End-to-end benchmarks (`di9-f6-correction/bench/`, `bench-summary.txt`)
**Method**
- Versions: o3 (4ce7933, the single query) and f6 (75dd89b, two steps), each from its own worktree.
- Runs:
  - pass A (o3, then f6) and pass B (f6, then o3);
  - five fresh-process repeats, R1–R5, alternating the order;
  - 66 steps in all, every one on AC power with 0 sleep events and 0 failures.
- Probes: those of LABS-1.056, unchanged (`stage_e_core03_selective.py`, `stage_e_scale.py`,
  `stage_e_di9_instrumented.py`).
- 11 containers were running on the Docker VM, as before.

### 4.1 Core 0.3 selective (60 `value_at` questions, the measurement databases kept from LABS-1.056)
p50 ms per question in each run, p95 in brackets:

| Scale | o3 (A, B, R1–R5 at 1× and 10×) | f6 | f6 ÷ o3, median p50 |
|---|---|---|---|
| 1× | 20.6 (47), 19.0 (30), 18.8 (30), 19.6 (32), 20.0 (31), 19.2 (30), 19.1 (30) | 16.8 (23), 16.8 (24), 16.1 (21), 16.5 (21), 17.1 (27), 16.5 (24), 16.6 (21) | 0.86 |
| 5× | 51.0 (98), 49.0 (96) | 18.3 (26), 18.6 (26) | 0.37 |
| 10× | 69.1 (160), 65.1 (139), 65.0 (141), 66.1 (140), 64.6 (140), 66.0 (138), 66.7 (138) | 17.0 (26), 17.8 (25), 17.5 (23), 17.4 (23), 17.5 (25), 17.7 (25), 17.4 (25) | 0.27 |

Latency distribution in pass A, at 10×:

| Version | p10 | p50 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|
| o3 | 34.0 | 69.1 | 140.1 | 160.1 | 176.8 | 213.7 |
| f6 | 13.1 | 17.0 | 22.9 | 26.0 | 30.4 | 36.5 |

The spread collapses because the slow questions were those with many supersession lookups.

Queries per question: 11.7 → 12.7 (one more per question with supersessions).

### 4.2 Scale read set (267 calls, 14 readers, five databases)
Totals per round (sum of per-call medians), pass A / pass B, then queries per round:

| Database | o3 | f6 |
|---|---|---|
| worlds-1 | 8.8 / 8.7 s, 7,604 q | 8.7 / 8.7 s, 7,653 q |
| worlds-5 | 10.9 / 9.1 s | 9.0 / 9.0 s |
| worlds-10 | 11.0 / 9.6 s | 9.3 / 9.3 s |
| perspectives-5 | 12.4 / 9.6 s | 9.4 / 9.5 s |
| perspectives-10 | 10.3 / 10.3 s | 10.3 / 10.3 s |

Per reader (pooled p50; full table in `bench-summary.txt`):
- worlds-1: within ±6 % of o3 for every reader.
- worlds-5 and worlds-10: most readers 5–20 % faster. The largest gains are `parts` (24 → 20 ms at worlds-10) and
  `facts_about` (27 → 22 ms).
- `office_holders` (worlds-10 ×1.11, perspectives-10 ×1.15) is an artefact of pooling calls of different lengths:
  - per call, f6 is within −21 % to +3 % of o3 in both passes;
  - the query counts are identical;
  - it has no supersessions.

### 4.3 `where("actual", "gbx-100", "f-workshop", AFTER)`, 92 worlds against 11
Total ms per call: the median of 7 runs in A and B, 5 runs in the repeats.

| Run | o3 | f6 |
|---|---|---|
| A | 72 → 83 (×1.16) | 74 → 73 (×0.98) |
| B | 64 → 84 (×1.32) | 74 → 77 (×1.05) |
| R1 | 56 → 68 (×1.22) | 57 → 59 (×1.04) |
| R2 | 58 → 71 (×1.23) | 57 → 61 (×1.07) |
| R3 | 57 → 70 (×1.23) | 58 → 61 (×1.06) |
| R4 | 56 → 69 (×1.23) | 59 → 66 (×1.12) |
| R5 | 57 → 70 (×1.23) | 58 → 59 (×1.02) |
| **Median / max / runs above 1.2×** | **×1.23 / ×1.32 / 6 of 7** | **×1.05 / ×1.12 / 0 of 7** |

Query time by kind per round (mean of the 7 runs), at 11 → 92 worlds:

| Kind | o3 | f6 |
|---|---|---|
| Supersession, single query (4 q) | 5.0 → 12.7 ms (**+7.7**) | — |
| Supersession step 1: pairs (4 q) | — | 3.6 → 3.4 ms (−0.3) |
| Supersession step 2: new attestations by id (2 q) | — | 1.8 → 1.7 ms (−0.1) |
| Superseder acceptance (2 q) | 2.3 → 2.2 ms | 2.4 → 2.1 ms |
| Heads and parameter fetches (9 q) | 21.8 → 28.3 ms (+6.5) | 23.4 → 26.7 ms (+3.2) |
| Acceptance, roles, world chain, other (20 q) | +0.1 ms in all | −0.6 ms in all |
| **Call total (median)** | **57 → 70** | **58 → 61** |

- `where` now runs 37 queries for 164 rows, against 35 for 161, at both scales.
- LABS-1.057 projected 1.05–1.10× for a flat lookup. The measured median is 1.05×.
- The growth that remains is in the heads and parameter fetches (section 7).

## 5. Small scales and large anchor counts (`probes/stage_e_f6_anchors.py`, `di9-f6-correction/anchors/`)
Method:
- One process toggles SUPERSESSION_TWO_STEP.
- Unfiltered and per-type `_load`s (75 loads) run in the worlds `actual`, `lab` and `org`, on worlds-1, worlds-10 and
  perspectives-10, 5 rounds in alternating order.
- Two anchoring settings: ANCHOR_MAX as configured (heads above 1,000 ids use the head form) and every head anchored.
- Every load gave an identical result in every round and setting.

Median ms per lookup, single → two steps, by number of anchor ids. The two anchoring settings agree within noise, so
the configured one is shown:

| Anchors | worlds-1 | worlds-10 | perspectives-10 |
|---|---|---|---|
| 1–10 (28–30 lookups) | 0.71 → 0.68 | 0.76 → 0.70 | 0.73 → 0.71 |
| 11–100 (6–8 lookups) | 1.51 → 1.54 | 1.46 → 1.59 | 1.41 → 1.32 |
| 101–1,000 | 8.2 → 6.6 (198 ids) | 27.9 → 5.9 (198 ids) | 605 → 48 (up to 942 ids) |
| 1,001–5,000 (head form) | — | — | 1,219 → 83 (1,548 ids); anchored: 1,251 → 98 |

Per round, at 11–100 anchors the second query costs at most about 0.1 ms per lookup (+1.1 ms per round at worlds-1).
In every other bucket two steps cost the same or less, and the gap widens with both scale and anchor count. On the
scale read set, worlds-1 totals are equal (8.7 s). Core 0.3 at 1× is 14 % faster.

**No fallback is kept:** no measurement justifies one. The head-form fallback above ANCHOR_MAX (from O-1) is kept as
it was. Both of its forms now use two steps, and the two-step lookup was faster than the single query in both.

## 6. Planner behaviour behind F6 (measured)
### 6.1 Ablation on the world model's databases (`probes/stage_e_f6_ablate.py`, `di9-f6-correction/ablate-set*.txt`)
Each variant runs from 4 fixed anchors and returns the same 4 rows. Median ms of 15 runs:

| Variant | core03 1× | 5× | 10× |
|---|---|---|---|
| Current single query | 6.75 | 35.6 | 69.4 |
| Pairs only; + stance; + start; + context alone; + attester alone | 0.8–1.3 | 0.9–1.1 | 0.9–1.1 |
| + context and attester together (with or without their ids) | 7.2–7.4 | 32.7–33.1 | 64.0–64.5 |
| Any two roles of the new attestation (content + context, content + attester; `isa` or `links`, one or two statements) | 7.0–7.3 | 32.5–32.8 | 64.3–65.1 |
| The same two roles with the role players typed (`$nwo isa world; $nwho isa social-object;`) | 0.94 | 0.94 | 1.08 |
| The same two roles on the anchored, old attestation | 0.91 | 0.99 | 1.06 |

What triggers the slowdown, measured:
- It takes **two role players of the attestation reached through the supersession** (`$n`), with those role players
  not narrowed to concrete types.
- Each role alone is flat, and so is each attribute.
- The same pair is flat on the anchored side. It is also flat once the role players are typed.
- The cost grows with the supersessions (and attestations) in the database, not with the answer.

The two-step form avoids the trigger: its second query anchors `$n` itself by id.

### 6.2 Minimal TypeDB 3.14.1 reproduction (private)
A standalone script reproduces the behaviour on a minimal schema with generated data:
- the single query grows from 6.0 to 47 ms between 1,000 and 10,000 supersessions;
- two steps stay at about 2 ms;
- typing a role player with its concrete type makes the single query flat, and its abstract supertype does not;
- the rows are identical in every form.

Its first version, where each role player could be only one type, stayed flat: the trigger needs role players that
can be several types, as the world model's attester can (physical or social objects).

It uses no world-model data. It is kept **outside this public repository**, for review, as instructed. No issue has
been published or drafted.

The same work found a second, separate behaviour (hypothesis, not verified):
- **Observed:** straight after a bulk load of 1,000 supersessions, the first single query did not finish within a
  60 s transaction timeout, in 4 of 4 builds. Earlier, with the default timeout, it ran for 300 s. The same query took
  about 6 ms a few minutes later.
- **Hypothesis:** planner statistics that do not yet reflect the loaded data.
- **What it needs:** a minimal case of its own before any report.

## 7. Remaining performance issues
- **Head and parameter fetches** still grow by about 3 ms in `where` from 11 to 92 worlds (+3.2 ms; it was +6.5 ms
  with the single query). This is now the main growth in `where`. It is not investigated.
- **Whole-world loads in other readers (DI9-D17, not done).** With the unscoped memo, `occurrence_status` and
  `provenance` still grow with perspectives:
  - `occurrence_status` at perspectives-10: 69 / 71 ms, against 52 ms at worlds-1;
  - `provenance` at perspectives-10: 335 / 320 ms, against 236 ms at worlds-1.
- **Planner dependence.** The correction relies on how TypeDB 3.14.1 plans an id-anchored query. `stage_e_f6_ablate.py`
  and `stage_e_f6_supersession.py` (with SUPERSESSION_TWO_STEP) should be rerun on any TypeDB upgrade.
- **Fresh databases.** The first-query behaviour after a bulk load (section 6.2) could affect a newly seeded
  deployment. The tests and probes have not met it, because they do not query straight after a large load.
- **H1 (transient slow states)** is still unexplained. Every step here was steady. Measurement noise remains: other
  projects' containers share the Docker VM.
- **A known limitation, not new (needs no change now).** `_load` folds duplicate (old, new) supersessions by
  keeping the first row. If two supersession relations between the same pair had different recorded times, the result
  would depend on TypeDB's answer order. That is true in both forms. The API never creates such pairs; only a direct
  insert in the tests does.

## 8. Recommendations (for the owner's decision)
- **DI9-D11 (the `where` growth target): close it.**
  - 1.2× is met in 7 of 7 runs: median ×1.05, highest ×1.12, from the same instrumented probe and databases as
    LABS-1.056.
  - The threshold was not changed.
- **DI9-D13 (merge into main): review now, merge on approval.**
  - The branch holds O-1, O-2, O-3 and F6, each validated by the full regression.
  - The merge is still deferred until you decide.
- **DI9-D17 (scope the memo in `occurrence_status`, `causes_of` and `effects_of`): next increment.**
  - These readers, with `provenance`, are now the ones that grow most with perspectives (section 7).
  - Do it as the same kind of isolated increment, compared against the unscoped path.
- **DI9-D18 (report the planner behaviour to TypeDB): review the private reproduction first.** Then decide whether to
  report two separate issues:
  - role-player typing through a relation reached from a bound relation (6.2);
  - the first query after a bulk load (6.2), once it has a minimal case of its own.

  Nothing goes out without your approval.
- **Do not switch to a typed single query instead of two steps.** It would need a disjunction over the attester's
  types (physical or social object), which changes the query that has been validated. The two-step form is
  type-agnostic and measured flat.

## 9. Records
- `di9-f6-correction/validate-f6-full/`: the regression's status, the suite summary, the answer diffs against S5, S7
  and S8, the view comparisons and E1.
- `di9-f6-correction/bench/`: every benchmark JSON (gzipped) and the step log with sleep and power checks.
  `bench.sh` and `analyse.py` produced `bench-summary.txt`.
- `di9-f6-correction/anchors/` and `ablate-set1.txt`, `ablate-set2.txt`: sections 5 and 6.1.
- Paths are written as `<scratch>` and `<projects>`.
- Kept for review:
  - databases `wm-probe-scale-*` and `wm-probe-core03-{1,5,10}[-mixed]`;
  - worktrees `../wm-entry-wt`, `../wm-o1-wt`, `../wm-o2-wt`, `../wm-o3-wt` (4ce7933) and `../wm-f6-wt` (75dd89b).
- The reproduction's own databases were deleted; they rebuild in seconds.
