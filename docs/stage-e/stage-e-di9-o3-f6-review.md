# DI-9: O-3 occurrence optimisation and F6 investigation (LABS-1.057)

Branch `feature/stage-e-entry-validation`, from d2771f1 (the O-1/O-2 report,
[stage-e-di9-optimisation.md](stage-e-di9-optimisation.md)). Approved decisions: DI9-D9 (O-1), D10 (O-2) and D12 (O-3
and an F6 experiment). DI9-D11 (the `where` target) is still open. DI9-D13 (merge) is deferred.

| Commit | Content |
|---|---|
| 4ce7933 | O-3: `occurrence()` loads only the occurrence's linked accounts |
| this commit | F6 probe and findings, O-3 measurements, full regression, this report |

There is no F6 correction, no merge, no Stage E2 and no ontology change. The O-1 and O-2 code is unchanged.

Records are in [di9-o3-f6/](di9-o3-f6/):
- `o3/`: occurrence off/on measurements and the 398-view checks;
- `f6/`: supersession formulations, the `where` breakdown and the run log;
- `validate-o3-full/`: the full regression.

**Timing rules (as in LABS-1.056).**
- Times are client-observed query time (from submitting a query to its last row), not elapsed wall time.
- Each step records its `pmset` sleep events and power source. No step had a sleep event, and every step was on AC power.
- Other projects' containers were running on the same Docker VM and were not touched.

## 1. O-3: scoped occurrence loading (F4)
**Before.** `occurrence()` built a `_Memo` whose `events()` loaded every event attestation in the world. Only two
things were used from it:
- the descriptions the perspective accepts (`participants`);
- the descriptions linked by any visible describes claim, accepted or not (`accounts`, `roles`; ER-5).

Identity and the describes links were loaded twice, once by `descriptions()` and once by `_event_roles`.

**After** (4ce7933):
- `_load` / `_level` take `contents` (event types only): the head matches `$c has wm-id == $cid`, with one given row
  per description id (the same mechanism as O-1).
- A `_Memo` can be scoped to a set of descriptions. It is scoped only by `occurrence()`, which knows them beforehand.
- `occurrence()` does one identity load (the occurrence and its aliases) and one describes load for those members.
  From that load it takes both the accepted descriptions (exactly as `descriptions()` filters them) and every linked
  description. It loads the events of their union only.
- Every other reader uses the unscoped memo exactly as before. `occurrence_status`, `causes_of` and `effects_of`
  still load the whole world.

**Why the semantics cannot change.**
- Every description `occurrence()` reads is in the scope. The scoped head applies the same world chain, knowledge
  time, branch time and perspective acceptances as the full head; it only adds the content id.
- Unaccepted, rejected and disputed accounts, aliases' accounts and inherited accounts are all named by a visible
  describes claim, so all of them are in the scope.
- `SCOPE_OCCURRENCE = False` keeps the old path. The tests compare the two paths on every answer.

**Tests** (`tests/test_x_o3_occurrence.py`, 43). Every view is compared with the old path:
- disputed events (two accounts naming different patients) and a describes link denied by an auditor;
- an unreviewed account and one rejected by the reviewer;
- an alias accepted by the system only;
- a hypothetical branch with its own account and its base world's accounts;
- an earlier knowledge time, before the alias, the later accounts and the plan existed;
- unrelated events in the same world, and the same occurrence in another world;
- an operation's own uncommitted account, seen inside the operation and not outside;
- three perspectives, four occurrences (one with no accounts) and three worlds.

Two further checks:
- Only the linked descriptions are loaded (spy on the event heads' given rows), and an occurrence with no describes
  links runs no event head at all.
- `_load(contents=...)` equals the full load filtered to those contents.

**Mutation check.** Scoping the memo to the accepted descriptions only (dropping unaccepted links) made 21 of the 43
tests fail. The tests detect a scope that is too narrow.

**One compatibility fix before the commit.** An existing test (`test_h_b4_consolidation`) replaces `_load` with a
fixed-signature spy. The memo therefore passes `contents` only when it is scoped, so unscoped calls are exactly as
before.

### O-3 measurements (`o3/`; n = 5, off and on alternating per round; 42 `occurrence` calls of the scale read set)

| Database | ms per round, off → on | Queries | Rows (all queries) | Event rows | Identical answers |
|---|---|---|---|---|---|
| 1× (worlds-1) | 1,910 → 1,334 | 1,834 → 1,384 | 3,383 → 1,189 | 422 → 40 | 42/42 |
| perspectives 5× | 2,471 → 1,354 | 1,834 → 1,384 | 11,111 → 1,189 | 2,354 → 40 | 42/42 |
| perspectives 10× | 3,270 → 1,399 | 1,834 → 1,384 | 20,771 → 1,189 | 4,769 → 40 | 42/42 |
| worlds 10× | 2,181 → 1,550 | 1,834 → 1,384 | 3,383 → 1,189 | 422 → 40 | 42/42 |

"Event rows" are the documents returned by event heads: the event attestations retrieved.

Per call (ms, queries, rows, event rows):

| Call | 1× off | 1× on | perspectives 10× off | perspectives 10× on |
|---|---|---|---|---|
| `actual o-repair` | 41.8, 37, 108, 14 | 30.7, 29, 37, 1 | 144.9, 37, 1,764, 428 | 30.4, 29, 37, 1 |
| `lab o-split-b` | 40.5, 37, 78, 12 | 30.0, 29, 22, 1 | 83.6, 37, 906, 219 | 29.9, 29, 22, 1 |

**The improvement comes from reduced retrieval, not changed semantics.**
- Answers are identical in every call at every scale, the 398 frozen views are identical (section 3), and so are the
  regression answers.
- With O-3, rows retrieved per round are the same at every scale (1,189), so the perspectives filler is no longer
  read at all.
- **Occurrence row-count target:** rows per view at perspectives 10× are 1.00× of 1× (target ≤ 1.2×; before, 6.1×).
- **Latency:** at perspectives 10× it is 1.05× of 1× (before, 1.71×).
- **Two sources of the gain:**
  - fewer event rows, which removed all the growth;
  - 450 fewer queries per round (about 11 per call: the duplicate identity and describes loads), which is most of
    the 30 % gain at 1×.

## 2. F6: the supersession lookup (investigation only)
**Probe.** `probes/stage_e_f6_supersession.py` (records in `f6/`, two passes in opposite order) works in two steps:
1. It records every anchored supersession lookup `_level` makes. For Core 0.3 these come from the 60 `value_at`
   questions (the same seeded questions as `stage_e_core03_selective.py`). For `where` they come from the
   instrumented call.
2. It replays each lookup on exactly the same anchor ids in eight formulations. Every formulation returned the same
   rows as the current one, in every database and both passes.

None of the formulations filters by time or perspective: `_load` applies knowledge time, branch time and the new
attestation's world afterwards, and acceptances are separate queries. So identical rows preserve temporal and
perspective semantics.

**Median ms per lookup, pass 1 / pass 2:**

| Formulation | core03-1 | core03-5 | core03-10 | where, 11 worlds | where, 92 worlds |
|---|---|---|---|---|---|
| C: current (O-1, given rows) | 5.35 / 5.49 | 28.7 / 30.0 | 53.7 / 53.2 | 1.28 / 1.23 | 2.42 / 2.82 |
| N: no `content` role on the anchor | 5.17 / 5.22 | 27.5 / 31.0 | 51.9 / 51.9 | 1.17 / 1.21 | 2.37 / 2.62 |
| L: `links` form | 5.47 / 5.53 | 30.3 / 28.9 | 53.3 / 53.4 | 1.28 / 1.36 | 2.53 / 2.87 |
| P: one query per anchor (no given rows) | 8.97 / 9.11 | 33.6 / 33.4 | 57.6 / 57.7 | 2.39 / 2.51 | 3.84 / 4.09 |
| H: head form (before O-1) | 11.5 / 11.9 | 44.9 / 44.4 | 71.9 / 70.3 | 1.72 / 1.74 | 4.92 / 5.13 |
| **S: two steps** (pairs, then the new attestations by id) | **1.98 / 2.13** | **2.33 / 2.55** | **2.27 / 2.25** | 1.50 / 1.37 | **1.17 / 2.20** |
| M: pairs only, `(aid, nid)` | 0.82 / 0.87 | 0.97 / 1.03 | 1.02 / 0.98 | 0.96 / 0.85 | 0.83 / 0.88 |
| R: pairs + the supersession's `recorded-at` | 0.91 / 0.95 | 1.07 / 1.14 | 1.08 / 0.99 | 0.88 / 0.83 | 0.72 / 0.85 |

**Scale of each case:**

| | core03-1 | core03-5 | core03-10 | where, 11 worlds | where, 92 worlds |
|---|---|---|---|---|---|
| Lookups (anchor ids per lookup) | 61 (7.0) | 63 (7.9) | 63 (6.5) | 4 (9.5) | 4 (9.5) |
| Rows returned | 206 | 240 | 202 | 3 | 3 |
| Supersessions in the database | 1,050 | 5,249 | 10,499 | 8 | 897 |
| Supersessions in the asked world | 1,049 | 5,220 | 10,445 | 7 | 7 |
| Attestations in the database | 3,350 | 16,749 | 33,499 | 322 | 3,272 |

### Findings
**Measured:**
- **F6-a. The lookup is reproduced and grows linearly with the database.** At the same ~3 rows per lookup, the
  current form costs 5.4 → 29 → 53.5 ms (×10 from 1× to 10×), while supersessions and attestations both grow ×10.
  For `where`, the asked world keeps 7 supersessions while the database grows from 8 to 897; the lookup still
  doubles. So it grows with the database, not with the asked world.
- **F6-b. Finding the supersessions is not the cost.** Matching the supersession pairs from the anchors (M), even
  with the supersession's own `recorded-at` (R), is flat at about 1 ms at every scale.
- **F6-c. The cost appears when the new attestation's attributes and roles are joined in the same query.** These are
  `$n has wm-id, has stance; $n isa attestation (context: $nwo, attester: $nwho); ...`. Fetching exactly the same
  values in a second query bound by `$n`'s id (S) is flat at about 2.0–2.6 ms: ×1.1 from 1× to 10×, against ×10
  for C.
- **F6-d. Neither the anchoring nor the batch is the cause.**
  - Dropping the `content` role on the anchor (N) or using `links` (L) changes nothing beyond noise.
  - One query per anchor (P) is slower at every scale and grows the same way.
  - The pre-O-1 head form (H) is slowest.
  - Bounded id anchoring was already in place (O-1); a different batch does not change the growth.

**Hypothesis (not established).**
- **H2 (refined).** In the single query, TypeDB 3.14.1's planner most likely starts the new-attestation part of the
  join from a broad pattern (all attestations of a context, or all attesters) instead of from `$n` bound through the
  supersession. When `$n` arrives as a given value, it starts from the bound id.
- Query plans are not observable through the driver, so this is inferred from F6-b and F6-c, not read from a plan.
- It is the same kind of behaviour as F2 and F3, and as the planner issue QPL1 recorded in a related project.

### Does F6 explain the remaining `where` growth?
**Measured** (`f6/where_shapes.txt`, from the five LABS-1.056 o2 runs at 11 and 92 worlds):
- `where` runs the same 35 queries and returns the same 161 rows at both scales.
- The growth is in streaming time (median 27 → 39 ms). Time to first response (23 → 23), Python (9 → 8) and
  transaction opening (5 → 5) are flat.

By kind of query (ms per call, mean of the five runs):

| Query kind | 11 worlds | 92 worlds | Difference |
|---|---|---|---|
| Supersession lookups (4 queries) | 5.8 | 13.8 | **+8.0** |
| Heads and parameter fetches (9) | 21.0 | 25.4 | +4.4 |
| Roles, acceptances, superseder acceptances, world chain, other (22) | 26.3 | 24.9 | −1.4 |
| Total of these | 53.1 | 64.1 | +11.0 |

The F6 replay agrees: for `where`, the current form takes 6.1 → 13.5 / 14.7 ms for its four lookups (+7.4 to
+8.6 ms), while the two-step form S takes 6.3–8.7 → 6.2–9.4 ms (no growth).

**Conclusion.**
- F6 explains about 70 % of the remaining `where` growth (8 of 11 ms).
- The rest is the heads and parameter fetches (+4.4 ms), not investigated here.
- **Projection, not a measurement of a corrected reader:** with a flat supersession lookup, `where` at 92 worlds
  would be about 1.05–1.10× its 11-world time, inside the 1.2× target. That would close DI9-D11.
- In the same way, Core 0.3 10× runs 63 lookups per 60 questions at about 53 ms each. A flat lookup would remove
  roughly 50 ms of the 68 ms median per question (projection).

## 3. Correctness
O-3's own gate, before its commit:

| Check | Result |
|---|---|
| 398 frozen occurrence views, upgraded reference database (`wm-probe-pre-e-mp-u`) | 398 = 398; fields 0, judgements 0, role presentation 0 different |
| 398 frozen occurrence views, fresh reference database (`wm-probe-stage-e`) | the same |
| Occurrence and reader tests (the nine test files that call `occurrence()`, 200 tests, plus the 43 new tests) | pass |
| Full suite, one configuration | 814/815: one spy-signature failure, fixed as described in section 1, then that file and the new tests passed (51) |

**Full regression after O-3**, on 4ce7933 from its own worktree (`validate-o3-full/`):

| Check | Result |
|---|---|
| Test suite: 815 tests (772 existing + 43 new), four configurations (selective on/off × profiling on/off), each run twice | 8 of 8 runs: 815 passed, 0 failed (10–14 min per run) |
| Reference answers, upgraded database against S5 and S7 | 106,752 identical, 0 extended, 0 changed, 0 other (each) |
| Reference answers, fresh database against S8 | 106,752 identical, 0 extended, 0 changed, 0 other |
| 398 frozen occurrence views, upgraded and fresh databases | 398 = 398 on both; 0 differences |
| E1 (revised question set) | 272/272 correct |
| Sleep events during the run (12:49–14:24 UTC, `pmset`) | none |

## 4. Remaining risks
- **F6 is uncorrected.** It is now the largest identified cost on the selective path. It also causes most of the
  `where` miss: DI9-D11 stays open until a correction is measured end to end.
- **A planner-dependent fix.** A correction such as S depends on the TypeDB 3.14.1 planner's behaviour (H2). A later
  TypeDB version could plan the single query well, or the two-step form badly, so a correction should stay covered
  by a probe like this one.
- **Other whole-world loads remain.** `occurrence_status`, `causes_of` and `effects_of` still use the unscoped memo:
  the F4 pattern outside `occurrence()`. `provenance` and `effects_of` still load whole worlds.
- **Head and parameter fetches** grow by about 4 ms from 11 to 92 worlds; the cause is not investigated.
- **H1 (transient slow states)** is still unexplained. This session's steps were steady, but only the controlled runs
  can be relied on.
- **Measurement noise.** Other projects' containers share the Docker VM.

## 5. Proposed next decisions

| Id | Decision | Recommendation |
|---|---|---|
| DI9-D14 | Accept O-3 (4ce7933) | accept |
| DI9-D15 | Accept F6-a to F6-d as measured, and H2 (refined) as a hypothesis | accept |
| DI9-D16 | F6 correction: the two-step supersession lookup (S) in `_level`, as its own increment, gated on identical rows, the 106,752 answers and the 398 views, with `where` and Core 0.3 measured end to end | approve as the next increment |
| DI9-D11 | `where` 1.2× target | keep open; decide after D16 is measured |
| DI9-D17 | Scope the memo in `occurrence_status`, `causes_of` and `effects_of` (the F4 pattern) | design after D16 |
| DI9-D18 | Report the F6 planner behaviour to TypeDB with a minimal reproduction (outward-facing; with DI9-D6) | owner to decide |
| DI9-D13 | Merge `feature/stage-e-entry-validation` into main | deferred, as instructed |
