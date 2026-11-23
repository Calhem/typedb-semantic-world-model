# DI-9 query optimisation: O-1 and O-2 (LABS-1.056)

Branch `feature/stage-e-entry-validation`. Starting point 51ef0f0 (the DI-9 investigation,
[stage-e-di9-investigation.md](stage-e-di9-investigation.md)). Approved decisions: DI9-D1, D2, D4 and D8.

| Commit | Content |
|---|---|
| 144be5b | O-1: `_level` follow-up queries anchored on the head's attestations |
| 92da365 | O-2: subject-bound loads skip types the subject has no content of |
| this commit | measurements, validation records and this report |

O-3 (occurrence loads) is not implemented. Nothing is merged. The ontology is unchanged.

Records are in [di9-optimisation/](di9-optimisation/):
- `o1-bounds/`: batch bounds;
- `o2-compare/` and `o2-rerun/`: the O-2 alternatives;
- `o2-alternatives.patch`: the evaluation build;
- `baseline/`: the baseline before the change;
- `bench/`: the before/after benchmark, with `summary.md`, the run log and the scripts;
- `validate-o1/` and `validate-o2-full/`: correctness validation.

Timings are milliseconds of client-observed query time (from just before the query to the last answer row), summed per
reader call. Elapsed wall-clock time of a run is never used as query time: overnight runs that spanned a sleep took
hours of wall time and are used for correctness only.

## 1. Measurement environment
- **Machine:** Mac on AC power, lid open, keep-awake requested for the session.
- **Validity checks:** every benchmark step records its window, the `pmset` sleep and wake events inside it, and the
  power source. A step with any sleep event is invalid and repeated. The before/after benchmark (73 steps, 10:33–11:58
  UTC on 2026-11-23) had **no sleep events, no failed steps and was on AC power throughout**, so no step needed repeating.
- **Databases:** TypeDB 3.14.1 (`wm-typedb`), one benchmark at a time. Other projects' containers were left running on
  the same Docker VM (11 containers; not touched, as instructed), so absolute timings carry their noise.
- **Earlier incidents:** before keep-awake, the Mac slept on battery during baseline runs. One Core 0.3 10× build
  failed with "clock went backwards" (a system clock step on wake). Those runs were dropped and repeated.

## 2. O-1: anchored follow-up queries in `_level` (F2, partly F6)
**Before.** `_level` fetched the head (the world's attestations of a type, in the asked valid-time and knowledge-time
window), then ran its follow-up lookups as separate queries that matched the world again:
- parameters;
- role players;
- acceptances by the perspective;
- supersessions;
- acceptances of superseding attestations.

The planner did not narrow those joins to the head's attestations, so their cost grew with every attestation in the
database, including other worlds' (F2).

**After.** Each follow-up query starts from the head's attestation ids: `match $a isa attestation (content: $c), has
wm-id == $anchor; ...`. The ids are passed as TypeDB *given rows*: one query with one row per id, answered as the union
of every row. `typeql.run` now accepts a list of parameter rows.
- World, perspective, valid-time and knowledge-time rules are unchanged, because the head that chose the ids still
  applies them.
- The follow-up queries only read facts about attestations already selected.
- An empty head runs no follow-up query at all.

**Why given rows, not a disjunction.** The first form tried was a disjunction of ids (`{ $a has wm-id == $a0; } or
...`). Its cost grew superlinearly with the number of ids. Given rows grew roughly linearly.

| Ids per query | 10 | 25 | 100 | 198 |
|---|---|---|---|---|
| Disjunction | ~5 ms | ~35 ms | 88–640 ms | – |
| Given rows | | | | ~24 ms |

Script and data: `o1-bounds/given-rows-vs-disjunction.py`.

**Bounds** (`ANCHOR_CHUNK = 1000`, `ANCHOR_MAX = 1000`). Larger batches were not assumed to be faster: chunk sizes
10–1000 and a capped variant were measured on five databases (`o1-bounds/`).

| Database (total ms per round) | head form | anchored, chunk 1000 |
|---|---|---|
| worlds-1 | 1,531 | 666 |
| worlds-10 | 2,358 | 871 |
| perspectives-10 | 3,349 | 2,755 |
| core03-10 (6 questions) | 808 | 441 |

- Chunk size made little difference; the gain comes from anchoring itself.
- At about 1,500 ids (the visible `actual` world at perspectives-10), the old head form was about 8 % faster (1,437
  versus 1,552 ms). Above 1,000 ids `_level` therefore keeps the head form.
- Answers were identical in every setting.

**Tests** (`tests/test_v_di9_anchored.py`, 20). Every answer is compared across three modes: head form, anchored, and
anchored in chunks of 2. The cases are:
- unrelated worlds;
- an attestation superseded in a hypothetical world but not in its base;
- disputed claims with opposite acceptances;
- valid-time and knowledge-time boundaries;
- quality parameters;
- three perspectives;
- that follow-up queries really are anchored;
- that an empty head runs no follow-up query.

## 3. O-2: skip absent (type, subject) pairs (F3)
**Problem (F3).** A subject-bound load of a type with *no* content in the database (for example `same-as` in
Core 0.3) cost time in proportion to the data. If the type exists anywhere, the cost disappears.

**Alternatives evaluated** (all with O-1). Every alternative is checked inside the reader's own transaction, and its
result is kept for that one `_load` call only. None is kept across transactions, as instructed.

| Alternative | Check |
|---|---|
| none | O-1 alone |
| database | the type has any content in the database (`limit 1`) |
| subject | the subject plays a role in any content of the type (`limit 1`); a two-step, subject-bound lookup |
| both | the database check first, then the subject check |

**Results** (total ms per round, n = 5, answers identical to `none` in every case):

| Database | none | database | subject | both |
|---|---|---|---|---|
| core03-1 | 107.8 | 89.0 | 89.1 | 92.3 |
| core03-5 | 312.8 | 215.5 | 216.0 | 217.2 |
| core03-10 | 446.7 | 241.9 | 245.0 | 246.5 |
| core03-1-mixed | 96.3 | 101.6 | 98.4 | 104.7 |
| core03-5-mixed | 213.8 | 213.1 | 217.2 | 211.8 |
| core03-10-mixed | 247.3 | 251.4 | 234.4 | 243.0 |
| worlds-1 | 674 | 688 | 699 | 709 |
| worlds-10 | 1,093 | 891 | 870 | 859 |
| perspectives-10 | 2,787 | 2,685 | 2,679 | 2,703 |

These figures are from 2026-11-22 (on battery, no sleep events). The AC-power rerun is in section 3a. `-mixed` adds
`same-as` content that the questions never touch: 20 links in an unrelated world, and 5 in `actual` between other
things.

**Selected: the subject check.**
- Where the type is absent, it saves as much as the database check.
- In the mixed case the database check can never skip, because the type exists somewhere. The subject check still
  skips subjects without content.
- It needs no knowledge of the schema or statistics, and it is a plain read in the same transaction. A write is
  therefore visible at once, including an operation's own uncommitted writes.

Its cost is one `limit 1` query per (type, subject) per load, not per world. At 1× it costs a few per cent where little
is absent (section 4). "both" adds a query and gains nothing measurable.

**Tests** (`tests/test_w_di9_absent_types.py`, 8). Every answer is compared with the check on and off. The cases are:
- absent types under three perspectives (system, a source, a reviewer);
- mixed worlds;
- a type's first content written after earlier reads, seen at once, while an earlier knowledge time still sees it as
  absent;
- inside an operation: uncommitted `part-of` and `same-as` writes seen by the operation and not by another model;
- the check is asked once per (type, subject) per load, and never when switched off.

### 3a. O-2 rerun on AC power
Rerun on 2026-11-23, 12:00–12:05 UTC, on AC power with no sleep events, in two passes: pass 2 reversed the database
order. The figures are total ms per round, pass 1 / pass 2, with answers identical to `none` everywhere.

| Database | none | database | subject | both |
|---|---|---|---|---|
| core03-1 | 119 / 117 | 96 / 95 | 96 / 93 | 97 / 98 |
| core03-5 | 355 / 349 | 231 / 230 | 232 / 233 | 235 / 236 |
| core03-10 | 514 / 492 | 268 / 265 | 268 / 263 | 289 / 267 |
| core03-1-mixed | 110 / 101 | 118 / 107 | 119 / 104 | 127 / 110 |
| core03-5-mixed | 239 / 225 | 241 / 233 | 231 / 225 | 240 / 231 |
| core03-10-mixed | 272 / 268 | 276 / 279 | 258 / 257 | 265 / 260 |
| worlds-1 | 745 / 773 | 708 / 741 | 733 / 736 | 719 / 753 |
| worlds-10 | 953 / 976 | 803 / 838 | 812 / 864 | 826 / 840 |
| perspectives-10 | 2,911 / 3,005 | 2,773 / 2,824 | 2,808 / 3,115 | 2,767 / 2,939 |

The rerun confirms the selection.
- Where the type is absent (core03), the subject check equals the database check.
- In the mixed case at 5× and 10× it beats both `none` and the database check in both passes. At 1× mixed, every check
  costs a few ms over `none`.
- On the scale databases the alternatives are within run-to-run noise of each other. Subject's 3,115 ms at
  perspectives-10 in pass 2 is a single-pass outlier; in pass 1 it was 2,808.

## 4. Before / after
**Versions:**

| Version | Code |
|---|---|
| base | 51ef0f0's code (main 8663cb2) |
| o1 | 144be5b |
| o2 | 92da365 (O-1 + O-2) |

**Runs:**
- Pass A runs base → o1 → o2.
- Pass B runs o2 → o1 → base.
- Three fresh-process repeat rounds (R1–R3) cover base and o2.

Each step is a new process. The full per-step data is in `bench/summary.md`.

### Core 0.3 selective (60 `value_at` questions; median ms per question, each pass and repeat)

| Scale | base | o1 | o2 | Queries per question base → o1 → o2 |
|---|---|---|---|---|
| 1× | 68.2, 50.8, 48.6, 49.8, 52.9 | 29.2, 24.3 | 19.8, 29.0, 19.3, 19.7, 21.5 | 17.7 → 11.3 → 11.7 |
| 5× | 160.4, 131.9 | 67.3, 83.2 | 54.5, 71.1 | 17.0 → 11.2 → 11.7 |
| 10× | 260.4, 259.1, 242.6, 259.2, 262.0 | 113.0, 113.5 | 71.3, 83.7, 65.3, 66.3, 68.6 | 17.2 → 11.2 → 11.7 |

At 10× the median of medians falls from 259.2 to 68.6 ms (×0.26).

The investigation's 10× figure was 233.5 ms, and the baseline run before the change was 221.6 ms. Today's base is
somewhat slower than either, which is within the run-to-run spread seen before (H1). O-2 adds about 0.5 queries per
question (the checks) but removes the expensive empty `same-as` lookups.

### Scale reads (14 readers, 5 calls each per pass; p50 ms with both passes pooled)

| Reader | worlds-1 (11 worlds): base / o1 / o2 | worlds-10 (92 worlds): base / o1 / o2 | perspectives-10: base / o1 / o2 |
|---|---|---|---|
| authorised | 34 / 19 / 18 | 46 / 24 / 19 | 44 / 24 / 19 |
| calibration_status | 40 / 20 / 20 | 60 / 24 / 22 | 50 / 26 / 21 |
| capable | 34 / 16 / 16 | 54 / 20 / 16 | 50 / 20 / 16 |
| causes_of | 133 / 47 / 58 | 160 / 64 / 50 | 149 / 63 / 56 |
| changes | 127 / 40 / 41 | 195 / 54 / 41 | 185 / 53 / 41 |
| facts_about | 97 / 24 / 26 | 102 / 32 / 28 | 95 / 32 / 28 |
| interpretations | 82 / 33 / 35 | 94 / 40 / 38 | 86 / 40 / 37 |
| occurrence | 122 / 54 / 51 | 222 / 82 / 51 | 232 / 101 / 72 |
| occurrence_status | 117 / 58 / 61 | 178 / 71 / 60 | 182 / 91 / 81 |
| office_holders | 94 / 51 / 49 | 192 / 79 / 55 | 164 / 77 / 56 |
| offices_of | 241 / 88 / 77 | 352 / 133 / 106 | 298 / 114 / 105 |
| parts | 33 / 15 / 17 | 73 / 23 / 27 | 58 / 23 / 24 |
| provenance | 703 / 256 / 262 | 818 / 351 / 270 | 1,132 / 392 / 370 |
| value_at | 39 / 16 / 12 | 68 / 25 / 12 | 65 / 24 / 12 |

**Per round** (sum of per-call medians; pass A / pass B):

| Database | base | o2 |
|---|---|---|
| worlds-1 | 36.4 / 25.9 s | 10.2 / 10.4 s |
| worlds-10 | 44.2 / 45.6 s | 11.5 / 10.5 s |
| perspectives-10 | 41.0 / 41.7 s | 14.6 / 12.5 s |

Queries per round fell from 14,601 (base) to 8,349 (o1) and 8,054 (o2).

**Growth from 11 to 92 worlds** (reader p50 at worlds-10 divided by p50 at worlds-1):

| Version | Range | Readers above 1.3× |
|---|---|---|
| base | 1.06–2.22× | – |
| o1 | 1.19–1.57× | – |
| o2 | 0.86–1.56× | parts 1.56×, offices_of 1.38× |

### Instrumented calls (n = 7; median ms per call at 11 / 92 worlds)

| Call | base A; B | o1 A; B | o2 A; B |
|---|---|---|---|
| `where` gbx-100 | 363/569; 354/687 | 65/87; 58/75 | 67/74; 58/76 |
| `parts` bay-1 | 30/309; 17/52 | 14/25; 14/22 | 16/22; 14/24 |
| `occurrence` o-repair | 72/132; 67/126 | 45/64; 45/61 | 53/48; 44/50 |
| `effects_of` | 268/578; 280/541 | 166/278; 162/252 | 196/210; 165/228 |
| `provenance` s12-b | 532/844; 481/768 | 346/483; 338/415 | 388/355; 340/396 |

## 5. Targets (provisional)

| Target | Result | Met? |
|---|---|---|
| Core 0.3 selective 10× median ≤ 160 ms (was 233.5) | o2 65.3–83.7 ms in five runs | **yes** |
| `where` at 92 worlds ≤ 1.2× its 11-world value | o2 ratios 1.11, 1.31, 1.21, 1.12, 1.16 (median 1.16); base 1.57–4.97 | **median yes; 2 of 5 runs no** |
| No reader more than 10 % slower at 1× than base | none; every o2 reader is 0.27–0.53× of base at worlds-1 | **yes** |
| No correctness or provenance regression | section 6 | **yes** |

**`where` is reported as a partial miss.** Two of five runs were above 1.2×: 1.21× and 1.31× (58 → 76 ms). In absolute
terms the growth is 7–18 ms, against 200–470 ms for base. Its 92-world time (70–79 ms) is below base's 11-world time
in every run (87–363 ms). The remaining growth was not tuned away. It is most likely the supersession lookups along the
longer world chain (the same cost as F6), and closing it needs the F6 experiment rather than a change to O-1 or O-2.

**O-2's cost at 1×.** Compared with O-1 alone, `causes_of` at worlds-1 is slower in both passes: 54 and 67 ms, against
49 and 45 ms. `parts` is 1–2 ms slower. These are the extra `limit 1` checks where little is absent; at 10× the same
readers are faster with O-2. The reader target compares with base, and against base every reader is about twice as
fast or better. This is a trade-off, not a regression against the baseline.

The occurrence row-count target belongs to O-3 and was not applied.

## 6. Correctness and provenance

| Check | O-1 (144be5b) | O-1 + O-2 (92da365) |
|---|---|---|
| Test suite, four configurations (selective on/off × profiles on/off) | 764 passed, ×4 | 772 passed, ×8 (each configuration twice) |
| 106,752 reference answers vs S5, S7 (upgraded) and S8 (fresh) | 0 different | 0 different |
| 398 occurrence views, upgraded and fresh | 0 different | 0 different |
| E1 revised | 272/272 | 272/272 |
| Benchmark answers vs base, 5 databases × 2 passes | 267/267 each | 267/267 each |

- The suite grew from 744 tests (the planned count) to 764 with O-1's 20 tests, and to 772 with O-2's 8.
- The reference answers include `provenance`, `roles_of`, `effects_of`, `causes_of` and the per-perspective
  (`reader@source`) readers. The per-reader tables are in the `diff-*.out.txt` files.
- The views check took about 1.3 minutes with O-1, against about 35 before.

## 7. Remaining issues
- **F6: supersession lookup in a large world.** It is now the main cost in Core 0.3 at 10×. The anchored supersession
  query runs 63 times per 60 questions and costs about 58 ms each, most of the 68 ms median. Anchoring helped, but the
  lookup itself still grows with the world's supersessions (10,499 at 10×). It needs its own experiment.
- **H1: transient slow states, still unexplained.** Base varied widely between fresh processes in this one quiet
  session: `where` at 11 worlds took 363, 354, 210, 102 and 87 ms. Core 0.3 base 1× took 68.2 ms in the session's first
  run and about 50 ms afterwards. O-2 was much steadier (58–68 ms), probably because it runs fewer and smaller queries.
  Its source is not identified (DI9-D5 still stands).
- **Full load** (reference path): unchanged.
- **Whole-world loads:** `effects_of` and `provenance` still load the whole world (the same pattern as F4).
- **Database growth:** `parts` (1.56×) and `offices_of` (1.38×) still grow by more than 1.3× from 11 to 92 worlds.
- **Planner (H2):** query plans are still not observable through the driver.

## 8. Recommendation on O-3
Proceed with O-3 as the separate, later increment already proposed (DI9-D3), gated on the 398-view baseline.
- After O-1 and O-2, `occurrence` is flat across worlds (51 ms at both 11 and 92 worlds).
- It still grows on the perspectives axis: 72 against 51 ms (1.40×), and `occurrence_status` 1.33×. That is the
  whole-world event load (F4), which O-1 and O-2 do not address.
- O-3 is now the largest identified structural cost outside F6.
- Run the F6 supersession experiment before or alongside it: F6 now dominates the Core 0.3 path, and it is the likely
  remaining cause of the `where` growth.

## 9. Decisions for review

| Id | Decision | Recommendation |
|---|---|---|
| DI9-D9 | Accept O-1 (given-row anchoring, bounds 1000/1000) | accept |
| DI9-D10 | Accept O-2 with the subject check (no cross-transaction state) | accept |
| DI9-D11 | `where` 1.2× target: accept the median (1.16×) or keep it open until the F6 experiment | keep open; review with F6 |
| DI9-D12 | Next: O-3 and an F6 supersession experiment, as separate increments | approve |
| DI9-D13 | Merge `feature/stage-e-entry-validation` into main | owner to decide; not done |
