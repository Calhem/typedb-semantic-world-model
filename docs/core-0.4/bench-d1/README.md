# Stage D-1 benchmark (LABS-1.023)

`scripts/measure_physical.py --extended --qualities` (plus `--mechanical`), 5 rounds per run, on one machine with
nothing else running.

| Configuration | Code | World | Files |
|---|---|---|---|
| D0 | `main` 8c60f04 (D0 merged) | A1 + A2 + B + C | `r1-3-d0-main-8c60f04.json`; rounds 4-5 in reversed order |
| D1 code | this branch | the same world | `r1-3-d1-code.json`; rounds 4-5 in reversed order |
| D1 + mechanical | this branch, full core with `core-0.4-d`, mechanical profile installed, `extend_mechanical` | the same world plus the D-1 extension | `r1-3-d1-mechanical.json` |

Median over rounds 1-3 of each run's median (ms), and queries per question (identical in every run):

| Question | D0 | q | D1 code | q | D1 + mechanical | q |
|---|---:|---:|---:|---:|---:|---:|
| poses(gear-in) | 21.6 | 14 | 28.7 | 14 | 32.2 | 14 |
| composition(gbx-100) | 374.6 | 218 | 546.3 | 218 | 470.3 | 218 |
| contents(workshop) | 212.7 | 114 | 266.5 | 114 | 186.5 | 114 |
| materials(cover) | 60.3 | 42 | 72.7 | 42 | 70.7 | 42 |
| frame_info(f-bench) | 27.4 | 16 | 33.9 | 16 | 31.0 | 16 |
| facts_about(housing) | 29.6 | 14 | 32.1 | 14 | 33.6 | 14 |
| where(gbx-100, f-workshop) | 146.6 | 39 | 161.8 | 39 | 94.5 | 39 |
| where(gear-in, f-workshop) | 56.6 | 33 | 88.6 | 33 | 59.2 | 33 |
| where(bench-1, f-gearbox) | 84.6 | 40 | 122.4 | 40 | 70.1 | 40 |
| transform_between(f-gearbox, f-workshop) | 11.9 | 7 | 15.1 | 7 | 11.9 | 7 |
| effects_of(ev-worklog-replacement) | 485.6 | 197 | 595.4 | 197 | 391.3 | 197 |
| changes(gbx-100, repair) | 201.7 | 71 | 221.7 | 71 | 224.0 | 71 |
| causes_of(o-test-run) | 211.8 | 129 | 230.1 | 129 | 251.3 | 129 |
| explain(operational) | 429.1 | 284 | 523.9 | 284 | 517.7 | 284 |
| process_steps(o-repair) | 211.1 | 144 | 266.5 | 144 | 258.1 | 153 |
| actions_of(technician) | 147.7 | 69 | 176.1 | 69 | 171.9 | 73 |
| value_of(condition) | 48.1 | 23 | 53.0 | 23 | 47.4 | 23 |
| measurements(housing, mass) | 145.8 | 100 | 168.4 | 100 | 163.2 | 100 |
| compare_measurements(housing, mass) | 153.3 | 100 | 163.3 | 100 | 159.0 | 100 |
| capable(technician, workshop) | 26.1 | 14 | 29.7 | 14 | 31.5 | 14 |
| is_agent(apprentice) | 18.9 | 14 | 20.9 | 14 | 21.0 | 14 |
| roles_of(apprentice) | 25.4 | 16 | 26.7 | 16 | 26.3 | 16 |
| check_action(worklog) | 155.1 | 105 | 176.1 | 105 | 186.7 | 109 |
| account_attestations(worklog) | 32.3 | 19 | 36.4 | 19 | 34.2 | 19 |
| **direct_dependencies(output-shaft)** (new) | | | | | 24.6 | 14 |
| **dependencies(output-shaft, functional)** (new) | | | | | 50.6 | 5 |
| **connections(input-shaft)** (new) | | | | | 27.4 | 14 |
| **replacement(ev-cmms-replacement)** (new) | | | | | 161.2 | 110 |

**Build time (s):** D0 3.44–3.92; D1 code 3.95–9.53; D1 + mechanical 4.63–8.07. The 9.53 and 8.07 s runs are single
outliers.

**Database size (bytes):**
- D0: 654,831–655,029;
- D1 code: 654,701–654,867, the same;
- D1 + mechanical: 720,166–720,460. That is +10% for the D-1 extension: 6 connections, 7 dependency attestations, two
  replacement accounts with four effect claims, the profile schema and vocabulary, and a plan world.

## Reading
- **Existing queries, D1 code vs D0: no regression in query counts.** All 24 questions issue exactly the same number
  of queries.
- **Latency.** In rounds 1-3, D1 code looked 5–45% slower. It always ran second in a round, and its code paths for most
  of these questions (`poses`, `composition`, `frame_info`) are unchanged. Rounds 4-5 reversed the order (D1 first):
  - D0 was then no faster: `poses` 26.2 / 28.6 vs 28.8 / 26.0 ms, `facts_about` 32.1 / 34.6 vs 30.0 / 33.0,
    `explain` 638.8 / 535.1 vs 688.5 / 497.3;
  - the machine had also become slower overall than in the D0 benchmark earlier the same day (D0 `poses` 21.5 ms then).
  - **Conclusion:** the difference is run order and machine drift, not D-1 code. This run is noisier than earlier
    ones, so a regression under about 15% could not be detected here.
- **Larger world, D1 + mechanical:**
  - `process_steps` +9 and `actions_of(technician)` +4 queries, because the technician is named in two more accounts;
  - `check_action` +4.
  - These are data-volume effects on unchanged queries.
- **New questions:**
  - `direct_dependencies` and `connections` cost 14 queries (25–27 ms);
  - a kind-filtered `dependencies` costs 5;
  - the `replacement` report costs 110 queries (161 ms): the account, the occurrence status and two claimed effects,
    each with its before and after state.
