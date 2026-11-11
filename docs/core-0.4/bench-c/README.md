# Stage C benchmark (LABS-1.019)

`scripts/measure_physical.py`, 5 rounds per run, three interleaved runs of each configuration on the same machine and
TypeDB 3.14.1 (`wm-typedb`), nothing else running:

| Configuration | Code | World | Files |
|---|---|---|---|
| B | `main` 8963734 (Stage B) | A1 + A2 + B1 + B2 | `r*-main-stage-b.json` |
| C-code | this branch | the same Stage B world, Stage B questions | `r*-branch-stage-b-world.json` |
| C-world | this branch | Stage B world + `extend_qualities_agency`, plus Stage C questions | `r*-branch-stage-c-world.json` |

B vs C-code isolates changes to existing queries caused by Stage C code. C-code vs C-world shows the cost of the larger
world and of the new questions. Numbers below are the median over the three runs of each run's median (ms), and the
TypeQL queries per question (identical in every run).

| Question | B ms | B q | C-code ms | q | C-world ms | q |
|---|---:|---:|---:|---:|---:|---:|
| poses(gear-in) | 21.7 | 14 | 21.4 | 14 | 21.9 | 14 |
| composition(gbx-100) | 354.4 | 218 | 344.4 | 218 | 353.6 | 218 |
| contents(workshop) | 199.2 | 114 | 154.0 | 114 | 203.5 | 114 |
| materials(cover) | 59.1 | 42 | 54.5 | 42 | 57.5 | 42 |
| frame_info(f-bench) | 29.1 | 16 | 24.6 | 16 | 26.4 | 16 |
| facts_about(housing) | 22.9 | 14 | 21.7 | 14 | 27.6 | 14 |
| where(gbx-100, f-workshop) | 84.7 | 39 | 75.8 | 39 | 120.6 | 39 |
| where(gear-in, f-workshop) | 50.1 | 33 | 45.6 | 33 | 48.0 | 33 |
| where(bench-1, f-gearbox) | 60.8 | 40 | 57.2 | 40 | 79.5 | 40 |
| transform_between(f-gearbox, f-workshop) | 10.2 | 7 | 10.4 | 7 | 10.7 | 7 |
| effects_of(ev-worklog-replacement) | 494.9 | 197 | 446.3 | 197 | 598.7 | 197 |
| changes(gbx-100, repair) | 195.8 | 71 | 195.1 | 71 | 199.3 | 71 |
| causes_of(o-test-run) | 204.2 | 129 | 213.2 | 129 | 201.2 | 129 |
| explain(operational) | 411.4 | 284 | 407.9 | 284 | 421.6 | 284 |
| process_steps(o-repair) | 181.1 | 136 | 182.7 | 136 | 191.6 | 144 |
| actions_of(technician) | 126.6 | 61 | 123.3 | 61 | 136.0 | 69 |
| value_of(condition) | 41.6 | 23 | 40.1 | 23 | 40.0 | 23 |
| measurements(housing, mass) | | | | | 143.1 | 100 |
| compare_measurements(housing, mass) | | | | | 135.5 | 100 |
| capable(technician, workshop) | | | | | 23.8 | 14 |
| is_agent(apprentice) | | | | | 18.1 | 14 |
| roles_of(apprentice) | | | | | 21.6 | 16 |
| check_action(worklog) | | | | | 146.3 | 105 |

Build time (s): B 2.76–2.92; C-code 2.74–3.06; C-world 3.11–3.22.

Database size (bytes, on disk): B 608,230–608,349; C-code 608,247–608,460; C-world 662,520–662,603.

## Reading
- **Existing queries, Stage C code (B vs C-code): no regression.** Query counts are identical for all 17 Stage A/B
  questions. Every latency is within run-to-run noise or lower. `contents(workshop)` is about 20% lower on this branch in
  all three runs (149–155 vs 183–203 ms) with the same queries. This is not explained, and no change targeted it, so it is not
  claimed as an improvement.
- **Larger world (C-code vs C-world): the same queries, more data per query.** The Stage C extension adds 2
  measurements, 7 grants, 1 action account and a plan world.
  - Query counts stay the same except `process_steps` (+8) and `actions_of(technician)` (+8). Both scan the
    technician's events, which now include the two weighing activities.
  - With unchanged counts, a few questions get slower: `effects_of` +34%, `facts_about(housing)` +27% (two more mass
    attestations for the housing), `where(gbx-100)` +59% and `where(bench-1)` +39%. The `where` figures vary widely
    between rounds (85–129 and 77–129 ms).
  - These are data-volume effects on unchanged queries, not code regressions. They are recorded for the Stage D
    performance pass (no optimisation in this stage).
- **New questions.**
  - Capability questions cost 14–16 queries (18–24 ms), the same order as `facts_about`.
  - `measurements` and `compare_measurements` cost 100 queries (about 140 ms) for 4 values. They load records one at a
    time: per record, `rests-on`, the record's attributes, its `reports` and `produced` claims, and the activity's
    occurrences. Batching them is an obvious optimisation, not done (scope).
  - `check_action` costs 105 queries (146 ms), mostly the occurrence and capability judgements it reports.
- **Storage growth:** +54 KB (+8.9%) for the Stage C extension. The Stage C schema alone, on the Stage B world, adds
  under 0.02% (C-code vs B).
