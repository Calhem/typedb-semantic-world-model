# DI-9 investigation: cross-world and in-world performance degradation (LABS-1.055)

**Status: at the DI-9 review gate.** Branch `feature/stage-e-entry-validation`. No production code, schema, ontology,
benchmark or reference result was changed; the corrections in section 5 are a design for review, not implemented.
DI-7, DI-17 and DI-19 stay registered for later review. Stage E2 not started.

Records: [di9/](di9/). Probes (read-only):
- `probes/stage_e_di9_instrumented.py`: per reader call, every read query split into time to first response, time to
  stream (and decode) its rows, rows returned; transaction opening timed; the rest of the call is Python. Plus fixed
  scope queries. Records `di9/pass1.json`, `di9/pass2.json` (second pass in reverse database order),
  `di9/instrumented-analysis.md`, `di9/parts-fresh-process-repeats.txt`.
- `probes/stage_e_di9_replay.py`: a call's exact queries captured, then each replayed alone (new read transaction per
  run, timed to the last row) with alternative formulations checked to return the same rows. Records `di9/replay-*.json`.
- `probes/stage_e_core03_selective.py`: the Core 0.3 workload (same data and questions as `bench_query_paths.py`) on the
  selective path, instrumented, with an optional full-load sample. Records `di9/core03-{1,5,10}.json`.

## 1. Environment and cleanup

- **Docker:** Docker Desktop stopped at 17:02:49 during the LABS-1.054 Core 0.3 10× run. `wm-typedb` received SIGTERM
  and was then stopped with exit code 137 as the Docker VM shut down; it was **not** killed for memory
  (`OOMKilled=false`). Docker Desktop was running again at 17:10; this session did not restart it. The other projects'
  containers came back through their own restart policies and were not touched. `wm-typedb` (restart policy `no`)
  was started with `docker start wm-typedb`: this project's container only.
- **Conditions:** TypeDB 3.14.1, Docker VM 10 CPUs / 7.7 GiB, Apple M2 Pro, 15 containers running throughout (other
  projects' load is uncontrolled noise). `wm-typedb` memory: 118 MiB at the start, 260–272 MiB after the instrumented
  passes, 541 MiB after the Core 0.3 10× selective run (`di9/run-log.txt`).
- **Cleanup** (each database checked against what this investigation built before deletion):

  | Database | Check | Result |
  |---|---|---|
  | `wm-bench-83eb7477` | worlds `actual`, `plan`; 2,000 objects, 300 places, 33,499 attestations = the interrupted Core 0.3 10× dataset | deleted |
  | `wm-probe-scale-worlds-{1,5,10}`, `wm-probe-scale-perspectives-{5,10}` | attestation and world counts equal the LABS-1.054 build records (322/11, 1,633/47, 3,272/92, 1,522/11, 3,022/11); `zf-` filler present except at 1× | deleted after the measurements |
  | `wm-probe-core03-{1,5,10}` | built by this investigation (200 / 1,000 / 2,000 objects, 2 worlds) | deleted after the measurements |

  Kept (approved reference and earlier probe databases, not touched): `wm-probe-stage-e`, `wm-probe-pre-e-d`,
  `-d-new`, `-d-u`, `-d-x`, `wm-probe-pre-e-mp-new`, `-mp-u`, `wm-reference-gearbox`, `-gearbox-c`, `-gearbox-d1`,
  `wm-reference-lab`, `wm-reference-organisation`. All the deleted databases can be rebuilt by the probes
  (deterministic seeds).

## 2. Core 0.3 at 10× (the outstanding EN-6 item)

Selective path, 60 questions, seed 11, single run per scale (`stage_e_core03_selective.py`); every question's
answer on the full-load sample was identical to the selective answer (6 / 6).

| Scale | Ingest (s; move median / p95 ms) | Selective p50 / p95 / p99 (ms) | Queries / transactions / rows per question | Median split: open / first / stream / Python (ms) | Database | Server memory after |
|---|---|---|---|---|---|---|
| 1× (200 objects, 1,000 moves) | 45.6; 35.9 / 73.8 | 44.8 / 59.4 / 67.3 | 17.7 / 3.0 / 25.9 | 1.9 / 12.5 / 27.9 / 2.2 | 3.7 MB | 291 MiB |
| 5× | 343.4; 55.9 / 104.2 | 123.5 / 185.5 / 219.7 | 17.0 / 3.0 / 29.8 | 1.9 / 11.3 / 107.0 / 2.3 | 49.2 MB | 346 MiB |
| **10×** (2,000 objects, 10,000 moves) | **1,160.0; 90.8 / 192.2** | **233.5 / 293.6 / 315.5** | 17.2 / 3.0 / 25.0 | 2.2 / 13.8 / 215.9 / 2.6 | 101.7 MB | 541 MiB |

- The selective path keeps its query count and rows per question at every scale; latency grows 2.8× (5×) and 5.2×
  (10×), all of it in the stream phase (server-side execution, section 4). Python and transaction opening are flat.
- The query count here (about 17) counts every executed read; the bench's own counter (13.5 at 1×) counts fewer, so
  the two are not comparable. The 5× median (123.5 ms) is within run-to-run noise of LABS-1.054's 142.0 ms.
- **Full load:** sampled at 1× (2.2–3.3 s per question, 11,600–12,100 rows) and 5× (49–59 s, 58,200–60,800 rows):
  97–99 % of its time is streaming rows. 5× the rows take about 20× the time. **The 10× full-load run stays deferred:**
  by that trend at least 3–4 minutes per question (about 3–4 hours for 60), and the Docker VM stopped during the last
  attempt. The 5× result is retained.

## 3. Instrumented measurements

Median of the two passes (n = 7 rounds each), ms; rows are per call (identical in both passes). Full tables:
[di9/instrumented-analysis.md](di9/instrumented-analysis.md).

| Call | DB | Total | Open | First | Stream | Python | Queries / tx | Rows |
|---|---|---|---|---|---|---|---|---|
| `parts actual bay-1` | worlds 1× | 18.5 | 1.3 | 7.0 | 7.3 | 2.8 | 11 / 2 | 75 |
| | worlds 10× | 171.6 | 1.5 | 15.7 | 153.2 | 3.3 | 11 / 2 | 75 |
| | perspectives 10× | 91.1 | 3.1 | 54.6 | 26.6 | 4.5 | 11 / 2 | 75 |
| `occurrence actual o-repair` | worlds 1× | 74.6 | 7.0 | 34.3 | 24.4 | 9.3 | 53 / 10 | 106 |
| | worlds 10× | 163.7 | 8.7 | 50.1 | 93.3 | 11.7 | 53 / 10 | 106 |
| | perspectives 10× | 322.6 | 16.5 | 85.9 | 184.9 | 41.5 | 53 / 10 | **1,762** |
| `where actual gbx-100` | worlds 1× | 286.2 | 6.0 | 222.8 | 47.6 | 10.2 | 39 / 8 | 159 |
| | worlds 10× | 547.8 | 7.6 | 110.4 | 444.8 | 14.2 | 39 / 8 | 159 |
| `effects_of` (worklog replacement) | worlds 1× / 10× / persp. 10× | 304 / 635 / 954 | 25 / 30 / 50 | 145 / 186 / 353 | 101 / 379 / 467 | 34 / 40 / 87 | 197 / 33 | 304 / 304 / **1,960** |
| `provenance lab s12-b` | worlds 1× / 10× / persp. 10× | 518 / 946 / 1,677 | 59 / 68 / 120 | 236 / 306 / 518 | 150 / 490 / 819 | 71 / 86 / 201 | 336 / 80 | 657 / 657 / **5,625** |
| `value_at actual gbx-100` | worlds 1× / 10× | 16.6 / 30.7 | 2.2 / 2.6 | 7.9 / 10.6 | 3.9 / 14.4 | 2.1 / 2.3 | 11 / 3 | 3 / 3 |

**Run-to-run variation is large for some calls.** `parts actual bay-1` at 10 worlds took 302 ms per call in pass 1
and 41 ms in pass 2; in three later fresh processes per database it was stable at **16 → 27 → 38 ms** (1×, 5×, 10×
worlds; `di9/parts-fresh-process-repeats.txt`). The LABS-1.054 "×10" for `parts` (29 → 307 ms) matches the slow
state, not the stable one. Both are real measurements; section 4 separates them.

**Scope queries** (each alone, rows and median ms; `experiments` in the pass files): a database-wide attestation scan
grows with the database (5 → 54 ms at 322 → 3,272 attestations), while the world-scoped `part-of` head returns 23 rows
in 1–3.6 ms at every scale, whichever way it is written. So the world predicate does narrow the basic head.

**Replay of single queries** (`di9/replay-*.json`; each query alone, 9 runs, timed to the last row):

| Query (as the code writes it) | Rows | 1× | 5× | 10× | Alternative, same rows | 10× |
|---|---|---|---|---|---|---|
| `where`: supersession + new attestations' acceptances for frame-transform in `actual` | 0 | 0.9 ms | – | **294 ms** | anchored on the 3 head attestation ids | **2.3 ms** |
| Core 0.3: `same-as` head for one subject (fetch) | 0 | 2.8 ms | 11.7 ms | **21.9 ms** | subject's `same-as` contents only: 0.6–0.7 ms flat; subject's contents and their attestations (no type): 0.7–0.8 ms flat | 0.7 ms |
| Core 0.3: `located-at` head for one subject (as one query) | 6–11 | 1.0 ms | 1.0 ms | **1.2 ms** | two steps by content key | 1.4 ms |
| Core 0.3: supersessions of the subject's `located-at` attestations | 3–4 | 8.6 ms | 22.8 ms | **72.4 ms** | anchored on the head ids | 52.1 ms |
| `occurrence`: every event in `actual` + its role players | 46 → 1,288 | 2.1 ms | – | 37.2 ms (persp. 10×) | – (whole-world load; section 4, F4) | |

Core 0.3 at 10×, one question's queries replayed: 162.5 ms in all, of which the four `same-as` queries (0 rows each)
are **80 ms (49 %)** and the `located-at` supersession query 72 ms (44 %). At 1×: 27 ms in all.

## 4. Root cause

### Confirmed (by measurement)
- **F1. Row streaming, decoding and Python are not the cause** of the cross-world slowdown. On the worlds axis every
  call returns the same rows at every scale, Python time is flat (2.8 → 3.3 ms for `parts`), and transaction opening is
  flat (1–3 ms). The growth is in the stream phase of queries that return **no rows at all** (for example 0.2 → 252 ms
  in pass 1, 0.9 → 294 ms in replay). TypeDB executes lazily, so "stream" time is the server executing the query; with
  nothing to decode, the cost is server-side work.
- **F2. Supersession and acceptance joins are not narrowed to the world's attestations.** `_level` matches the world
  head and then supersession and acceptance relations in the same query. When the database holds many supersessions in
  other worlds (8 at 1×, 897 at 10× worlds, all from the filler's moves), these queries slow by up to about 300× while
  returning 0–2 rows. Binding the same query to the head's attestation ids removes the growth with identical rows
  (294 → 2.3 ms for `where`). Effect: the cross-world component of `where`, `parts` and the per-world loads.
- **F3. A subject-bound query about a type with no instances costs time in proportion to the data.** In Core 0.3 (no
  `same-as` content exists) each of the four `same-as` queries per question returns 0 rows but costs 2.8 → 11.7 →
  21.9 ms. Each of its parts alone (subject → contents, subject → `same-as`, subject → attestations) is flat at about
  0.6–0.9 ms, and the same query for a populated type (`located-at`) is flat at about 1 ms. So the combination is
  executed in an order that scans, but only for the empty type. This accounts for about half of Core 0.3's selective
  query time at 10×, and for 24 `same-as` queries (about 75 ms) per occurrence view at perspectives 10×.
- **F4. `occurrence()` loads every event in the world.** Its memo loads every event attestation in the world with its
  role players and keeps those of the occurrence's descriptions in Python (`_Memo.events`). With more attesters in the
  same world, rows per view grow 106 → 842 → 1,762 and Python 9 → 41 ms. This is a whole-world load, not a planner
  effect. `effects_of` (304 → 1,960 rows) and `provenance` (657 → 5,625) show the same pattern on that axis.
- **F5. The full load is proportional to the rows it reads**, and costs more per row at larger scale (5× rows, about
  20× time). That is inherent to the reference path.

### Partly explained
- **F6. The Core 0.3 `located-at` supersession query** grows 8.6 → 22.8 → 72.4 ms with 3–4 rows; supersessions in the
  world grow 1,050 → 10,499. Anchoring on the head ids helps at 5× (23 → 8 ms) but much less at 10× (68 → 52 ms), so
  part of the cost remains in the supersession lookup itself. Not explained further.

### Hypotheses (not established)
- **H1. Transient slow states.** In some processes or passes (the whole LABS-1.054 read run; pass 1 here; one
  fresh-process run on the plan world), calls were 5–10× slower than in other runs on the same database, with the same
  queries and rows; isolated replays never showed it. Candidates: server state after a restart or bulk ingestion (cold
  storage cache, background compaction, statistics refresh changing plans). No measurement separates them yet.
- **H2. The mechanism of F2 and F3** is most likely the query planner's join order when the database's statistics show
  a rare or empty type (or many supersessions elsewhere). Query plans are not available through the 3.14 driver, so this
  is inferred from which reformulations remove the cost, not read from a plan. (The project already records one
  TypeDB 3.14.1 planner issue, QPL1, in a related project.)

## 5. Proposed optimisation (design only; not implemented)

All three changes are internal to the core's loading. They change neither what is loaded nor any reader's output;
query counts change and are recorded.

### O-1. Anchor supersession, acceptance and role queries on the head's attestation ids (`_level`)
- **Now:** each of the role, acceptance, supersession and new-acceptance queries repeats the world head (world →
  attestation → type, subject, time filters) and joins the relation to it in one query.
- **Cause:** F2; partly F6.
- **Change:** take the attestation ids from the head query (already fetched) and run the other queries bound to those
  ids (a disjunction of ids in chunks, as `_linked_ids` does), skipping them when the head returned nothing. Cap the
  chunk size: anchored on 198 ids the query was slower (72 vs 21 ms), so above a measured threshold keep the current
  form.
- **Expected:** removes the cross-world growth of these queries. `where` at 92 worlds: about −290 ms of its ~440 ms
  stream time. Small gains elsewhere at small scale.
- **Risks:** time, knowledge and perspective filters must still apply. They do, because the ids come from the filtered
  head and the queries on the superseding attestations keep their own filters. Chunking must not drop or duplicate
  rows. Every variant was checked to return identical rows (`same_values_as_captured: true`).

### O-2. Do not query content types that have no attestations in the world
- **Now:** a subject-bound load queries each content type in the chain (including `same-as` for identity), four to
  five queries per type per world, whether or not the type has any attestation there.
- **Cause:** F3.
- **Change:** within one read transaction, check once per type and world whether any attestation of the type exists
  (about 1 ms, flat), and skip that type's queries when none does. Alternatively, query in two steps: the subject's
  contents of the type first (about 0.7 ms), then their attestations by content key (about 1.4 ms), the form that
  measured flat.
- **Expected:** Core 0.3 selective 10× loses most of the 80 ms `same-as` share of its ~160 ms query time: median about
  234 → 140–160 ms. `occurrence` at perspectives 10× loses about 75 ms per view. No effect where the type has data.
- **Risks:** the presence check must respect knowledge time, and an operation's own uncommitted writes (reads inside
  an operation use its transaction). So it is cached per read transaction only, never across transactions. Identity
  semantics are unchanged: `same-as` is still loaded whenever any exists.

### O-3. Load only the occurrence's own accounts in `occurrence()`
- **Now:** every event attestation in the world, with its role players, is loaded and then filtered in Python (F4).
- **Change:** an internal content-id filter on `_load` (the events whose description ids are linked to the occurrence
  or its aliases by any visible `describes` claim, accepted or not). Then load those events only.
- **Expected:** rows per view at perspectives 10×: 1,762 → about 110 (as at 1×); Python 41 → about 10 ms; total
  roughly back to the worlds-axis level (about 320 → 160 ms).
- **Risks:** ER-5 lists unaccepted accounts, and inherited `describes` links (DI-14 behaviour) must stay listed
  exactly as now. So the filter must use every linked description, not only accepted ones. Acceptance: the 398 views
  stay identical.

### Not proposed now
Full-load optimisation (it is the reference path); the remaining cost of F6 (needs its own experiment); H1 (a
measurement plan, decision DI9-D5); `effects_of` and `provenance` whole-world loads (same pattern as F4; to be
designed after O-3 is measured).

### Acceptance criteria for the corrections
- **Correctness:**
  - 744 tests in all four configurations, twice;
  - 106,752 reference answers identical (S5 / S6 snapshot, fresh build masked);
  - 398 occurrence views identical;
  - E1 revised results unchanged (272 / 272).
- **Query counts:** recorded per reader before and after. They may fall; answers may not change.
- **Performance** (proposed thresholds, owner to set), two passes as here, plus fresh-process repeats:
  - worlds axis: every reader's p50 at 10× within 1.3× of 1× (now 1.3–2.9×);
  - `where` at 92 worlds within 1.2× of 11 worlds;
  - `occurrence` at perspectives 10×: rows per view at most 1.2× of 1×;
  - Core 0.3 selective 10× median at most 160 ms (now 233.5);
  - no reader more than 10 % slower at 1× than before.

## 6. Remaining performance limitations
- The full load grows faster than its rows; the 10× full-load run is deferred.
- Supersession lookups in a large world (F6) keep part of their cost after O-1.
- Transient slow states (H1) can make any run 5–10× slower; until they are explained, performance comparisons need
  two passes and fresh-process repeats, as here.
- The query planner's choices are not observable through the driver (H2), so further diagnosis relies on
  reformulation experiments.
- Other projects' containers run on the same Docker VM; absolute timings carry that noise.

## 7. Decisions requiring architectural approval

| ID | Decision | Recommendation |
|---|---|---|
| DI9-D1 | Accept findings F1–F5 as the confirmed DI-9 causes; F6, H1 and H2 stay open | accept |
| DI9-D2 | Implement O-1 and O-2 as one increment in `_level`, to the acceptance criteria above | approve (largest measured effect; one function) |
| DI9-D3 | Implement O-3 as a separate, later increment, gated on the 398-view baseline | approve after O-1/O-2 are measured |
| DI9-D4 | EN-6: Core 0.3 10× selective is now complete; the 10× full load stays deferred (cost about 3–4 h; VM stopped during the last attempt); 5× retained | accept |
| DI9-D5 | H1: a controlled measurement (immediately after a restart, after bulk ingestion, after idle) before relying on single-pass timings | approve as a probe-only task |
| DI9-D6 | Report the F2/F3 planner behaviour to TypeDB with a minimal reproduction (outward-facing) | owner to decide |
| DI9-D7 | The performance thresholds in section 5 | owner to set |
| DI9-D8 | Cleanup as recorded in section 1; keep `wm-probe-stage-e` as the fresh reference database | accept |
