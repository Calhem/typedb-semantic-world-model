# Stage E performance phase: closure report (DI-9)

**Status:** for review (LABS-1.059), 24 November 2026. This report consolidates the performance phase. Nothing in
it is a new optimisation.
- **Approved and closed:** F6 is approved and DI9-D11 is closed.
- **Deferred:** DI9-D17.
- **Residual issues:** registered as DI-20 to DI-23 in
  [deferred-issues.md](../core-0.4/deferred-issues.md).

**Source reports (the detail and the raw records):**

| Report | What it covers |
|---|---|
| [stage-e-entry-report.md](stage-e-entry-report.md) | the baseline at 1×, 5× and 10× (LABS-1.054) |
| [stage-e-di9-investigation.md](stage-e-di9-investigation.md) | the causes F1 to F6 (LABS-1.055) |
| [stage-e-di9-optimisation.md](stage-e-di9-optimisation.md) | O-1 and O-2 (LABS-1.056) |
| [stage-e-di9-o3-f6-review.md](stage-e-di9-o3-f6-review.md) | O-3 and the F6 investigation (LABS-1.057) |
| [stage-e-di9-f6-correction.md](stage-e-di9-f6-correction.md) | F6 (LABS-1.058) |

## 1. What changed in the code

The changes are 4 code commits touching three files: `model.py`, `dynamics.py` and `typeql.py`.
- No schema, ontology or reader-contract change.
- No existing test changed. 133 tests were added, from 744 to 877.
- Each change keeps the earlier path behind a switch that the tests compare with.

| Change | Commit | What it does | Switch (False = earlier path) |
|---|---|---|---|
| O-1 | 144be5b | `_level`'s follow-up queries start from the head's attestation ids (given rows, chunks of 1,000; head form above 1,000 ids) | `ANCHOR_MAX` (head form above it) |
| O-2 | 92da365 | skip a subject-bound (type, subject) whose subject plays a role in no content of the type (one `limit 1` check per load) | `SKIP_ABSENT` |
| O-3 | 4ce7933 | `occurrence()` loads only the event descriptions its describes links name, and loads identity and the links once | `SCOPE_OCCURRENCE` |
| F6 | 75dd89b | supersessions read in two queries in one transaction: the pairs, then the new attestations by id | `SUPERSESSION_TWO_STEP` |

`typeql.run` also accepts a list of given rows, with the same names in every row. It is used only by O-1, O-3 and F6.

## 2. Cumulative improvement: Stage E entry code (main 8663cb2) → branch (75dd89b)

**Caveat:** the "base" figures and the F6 figures come from different sessions, LABS-1.056 and LABS-1.058, on the
same databases and the same probes. Within each session the versions were interleaved in passes in opposite order,
plus fresh-process repeats. Across sessions, take the ratios as indicative, not exact.

### Core 0.3 selective (60 `value_at` questions; median of per-run p50 ms per question)

| Scale | base | O-1 + O-2 | + O-3 | + F6 | base → F6 |
|---|---|---|---|---|---|
| 1× | 50.8 | 19.8 | 19.6 | 16.6 | ×0.33 |
| 5× | 146 (160.4, 131.9) | 62.8 (54.5, 71.1) | 50.0 | 18.5 | ×0.13 |
| 10× | 259.2 | 68.6 | 66.0 | 17.5 | ×0.07 |

- **Queries per question:** 17.2 → 12.7.
- **p95 at 10×:** about 140 ms with O-3, about 25 ms with F6.
- **Latency from 1× to 10×:** ×5.1 for base, ×1.05 with F6.

### Scale read set (267 calls, 14 readers, 5 databases): one round (sum of per-call medians; pass A / pass B)

| Database | base | F6 |
|---|---|---|
| worlds-1 (11 worlds) | 36.4 / 25.9 s | 8.7 / 8.7 s |
| worlds-10 (92 worlds) | 44.2 / 45.6 s | 9.3 / 9.3 s |
| perspectives-10 | 41.0 / 41.7 s | 10.3 / 10.3 s |

Queries per round: 14,601 → 7,653.

Per reader (p50 ms, passes pooled), base → F6:

| Reader | worlds-1 | worlds-10 | perspectives-10 |
|---|---|---|---|
| provenance | 703 → 235 | 818 → 260 | 1,132 → 320 |
| offices_of | 241 → 72 | 352 → 85 | 298 → 85 |
| occurrence | 122 → 34 | 222 → 35 | 232 → 35 |
| changes | 127 → 36 | 195 → 36 | 185 → 36 |
| value_at | 39 → 12 | 68 → 12 | 65 → 12 |

The other nine readers fell by similar factors; all 14 are in the source reports. No reader is slower than base on
any database.

### `where("actual", "gbx-100", "f-workshop")`: 92 worlds against 11 (ms per call; ratio)

| Version | Runs | 11 → 92 worlds | Ratio median (range) | Runs above 1.2× |
|---|---|---|---|---|
| base | 5 | 87–363 → 429–687 | 2.65 (1.57–4.97) | 5 of 5 |
| O-1 + O-2 | 5 | 58–68 → 70–79 | 1.16 (1.11–1.31) | 2 of 5 |
| + O-3 | 7 | 56–72 → 68–84 | 1.23 (1.16–1.32) | 6 of 7 |
| + F6 | 7 | 57–74 → 59–77 | 1.05 (0.98–1.12) | **0 of 7** |

### Provisional targets (set at the DI-9 review gate)

| Target | Result | Met |
|---|---|---|
| Core 0.3 selective 10× median ≤ 160 ms | 17.0–17.8 ms (7 runs) | yes |
| `where` at 92 worlds ≤ 1.2× its 11-world time | 7 of 7 runs; median ×1.05 | yes (DI9-D11 closed) |
| No reader more than 10 % slower than base at 1× | every reader faster than base | yes |
| `occurrence` rows at perspectives 10× ≤ 1.2× of 1× | 1.00× | yes |
| No correctness or provenance regression | section 3 | yes |

### Where the gains came from (measured, per increment)

| Increment | Source of the gain |
|---|---|
| O-1 | follow-up joins no longer scale with acceptance and supersession relations elsewhere in the database |
| O-2 | the empty subject-bound lookups, which scaled with the data, are gone |
| O-3 | event rows per occurrence round 4,769 → 40 at perspectives 10×, and 450 fewer queries per round |
| F6 | the supersession lookup is flat (5.4 → 53.5 ms per lookup from 1× to 10× before; about 2 ms after) |

## 3. Correctness validation (every code commit, full regression)

| Check | O-1 | O-1 + O-2 | + O-3 | + F6 |
|---|---|---|---|---|
| Tests, four configurations × 2 | 764 (×4) | 772 ×8 | 815 ×8 | 877 ×8 |
| 106,752 reference answers vs S5, S7 (upgraded), S8 (fresh) | 0 changed | 0 changed | 0 changed | 0 changed |
| 398 occurrence views (upgraded, fresh) | identical | identical | identical | identical |
| E1 revised | 272/272 | 272/272 | 272/272 | 272/272 |
| Benchmark answers vs the earlier version, 5 databases × 2 passes | 267/267 | 267/267 | 42/42 (O-3 calls) | 267/267 |

**Tests added:**

| File | Tests | What they compare |
|---|---|---|
| `test_v_di9_anchored.py` | 20 | anchored vs head form |
| `test_w_di9_absent_types.py` | 8 | skip vs no skip |
| `test_x_o3_occurrence.py` | 43 | scoped vs unscoped occurrence views, with a mutation check that fails 21 of 43 tests |
| `test_y_f6_supersession.py` | 62 | two-step vs single query, on complete results |

**Semantics preserved (audited against main, LABS-1.059):**
- World, perspective, valid-time, knowledge-time, branch-time and supersession rules are unchanged.
- An operation's uncommitted writes are still read inside its own transaction: O-2's check and F6's second query
  both run there.
- No schema file differs from main.

## 4. Outstanding limitations

Registered as deferred issues, with no optimisation scheduled:

| Issue | Limitation | Measured |
|---|---|---|
| DI-20 | whole-world loads in readers not yet scoped (DI9-D17 deferred): `occurrence_status`, `causes_of`, `effects_of`, `provenance` | worlds-1 → perspectives-10: `occurrence_status` 52 → 71 ms (×1.37), `provenance` 235 → 320 ms (×1.36) |
| DI-21 | H1: transient slow states between fresh processes | base `where` at 11 worlds ranged 87–363 ms in one quiet session. Every LABS-1.058 step was steady, but the cause is unknown |
| DI-22 | cross-world growth in head and parameter fetches | `where`: +3.2 ms from 11 to 92 worlds (now its main growth). Readers growing most from worlds-1 to worlds-10: `parts` 14 → 20 ms (×1.43), `office_holders` 40 → 55 ms (×1.38). `office_holders` was 11–15 % slower with F6 than with O-3 at 10× (within its spread, not explained) |
| DI-23 | performance depends on TypeDB 3.14.1's planner; first query after a bulk load | single supersession query 6 → 47 ms in a minimal schema (private reproduction); a first query after a fresh load did not finish in 60 s (4 of 4 builds, unverified) |

Not registered separately, because they are already recorded:
- The full-load (reference) path is unchanged by design.
- Query plans are not observable through the 3.14 driver (H2).
- Other projects' containers share the Docker VM, so absolute timings carry noise.
- `_load` folds duplicate (old, new) supersession pairs by keeping the first row. This is unchanged in both forms, and
  only a direct test insert creates such pairs.

## 5. Reproducing the results

The scripts and their outputs are committed under `docs/stage-e/` and `probes/`.

**Version checkouts:** the measurement worktrees were removed after this audit. Recreate them with:

```bash
git worktree add --detach ../wm-entry-wt 8663cb2
```

The same command with `144be5b` (o1), `92da365` (o2), `4ce7933` (o3) and `75dd89b` (f6). `bench.sh` takes the
checkouts as paths.

**Databases:** the benchmark databases are rebuilt by seeded builders, so the data is the same:

| Databases | Built by | Seed |
|---|---|---|
| `wm-probe-scale-worlds-{1,5,10}`, `wm-probe-scale-perspectives-{5,10}` | `probes/stage_e_scale.py --build --axis … --scale K --db NAME` | 54 (default) |
| `wm-probe-core03-{1,5,10}[-mixed]` | `probes/stage_e_core03_selective.py --scale K --db NAME --keep [--mixed]` | 11 (default) |

- **Checking a rebuild:** the build records give the counts to compare with, e.g. worlds-10: 3,272 attestations in
  92 worlds (`stage-e-entry/performance/build-*.json`).
- **Run validity:** every benchmark step records `pmset` sleep events and the power source, using
  `di9-optimisation/bench/slept.sh`. A step with a sleep event is invalid and is repeated.
- **Regression:** `di9-optimisation/validate-o2-full/validate.sh` reproduces the full regression; set `SP` to a
  scratch folder.
- **Kept, not touched:** the reference databases `wm-probe-stage-e`, `wm-probe-pre-e-*` and `wm-reference-*`.
