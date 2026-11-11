# Stage D0 benchmark (LABS-1.022)

`scripts/measure_physical.py --extended --qualities`, 5 rounds per run, three interleaved runs of each configuration
on the same machine, nothing else running:

| Configuration | Code | Files |
|---|---|---|
| main | `main` 18003bc (Stage C) | `r*-main-18003bc.json` |
| d0 | this branch (subtype-aware APIs, profile packaging) | `r*-d0.json` |
| d0 + profiles | this branch, with the three fixture profiles installed before the world is built (`--fixture-profiles`) | `r*-d0-profiles.json` |

The table gives the median over three runs of each run's median (ms), and queries per question (identical in every
run of every configuration).

| Question | main | q | d0 | q | d0 + profiles | q |
|---|---:|---:|---:|---:|---:|---:|
| poses(gear-in) | 21.5 | 14 | 21.7 | 14 | 21.3 | 14 |
| composition(gbx-100) | 362.8 | 218 | 374.4 | 218 | 353.9 | 218 |
| contents(workshop) | 206.5 | 114 | 209.2 | 114 | 203.8 | 114 |
| materials(cover) | 58.2 | 42 | 59.7 | 42 | 57.3 | 42 |
| frame_info(f-bench) | 26.4 | 16 | 26.4 | 16 | 25.9 | 16 |
| facts_about(housing) | 28.0 | 14 | 28.1 | 14 | 28.0 | 14 |
| where(gbx-100, f-workshop) | 143.9 | 39 | 139.9 | 39 | 158.1 | 39 |
| where(gear-in, f-workshop) | 73.6 | 33 | 86.3 | 33 | 78.6 | 33 |
| where(bench-1, f-gearbox) | 106.1 | 40 | 109.6 | 40 | 87.3 | 40 |
| transform_between(f-gearbox, f-workshop) | 11.2 | 7 | 11.2 | 7 | 10.8 | 7 |
| effects_of(ev-worklog-replacement) | 483.4 | 197 | 412.5 | 197 | 264.5 | 197 |
| changes(gbx-100, repair) | 196.4 | 71 | 201.0 | 71 | 195.7 | 71 |
| causes_of(o-test-run) | 202.5 | 129 | 234.1 | 129 | 202.9 | 129 |
| explain(operational) | 415.3 | 284 | 434.6 | 284 | 396.6 | 284 |
| **process_steps(o-repair)** (fixed) | 198.3 | 144 | 197.6 | 144 | 194.0 | 144 |
| actions_of(technician) | 134.1 | 69 | 140.6 | 69 | 136.0 | 69 |
| value_of(condition) | 50.2 | 23 | 58.0 | 23 | 43.6 | 23 |
| measurements(housing, mass) | 137.3 | 100 | 156.7 | 100 | 130.2 | 100 |
| compare_measurements(housing, mass) | 129.7 | 100 | 132.5 | 100 | 133.1 | 100 |
| capable(technician, workshop) | 27.1 | 14 | 21.8 | 14 | 25.8 | 14 |
| is_agent(apprentice) | 17.7 | 14 | 17.4 | 14 | 17.1 | 14 |
| **roles_of(apprentice)** (fixed) | 22.4 | 16 | 22.4 | 16 | 21.7 | 16 |
| check_action(worklog) | 150.7 | 105 | 151.2 | 105 | 148.1 | 105 |
| **account_attestations(worklog)** (fixed) | 29.1 | 19 | 28.7 | 19 | 29.4 | 19 |

- **Build time (s):** main 3.09–3.53; d0 3.06–3.72; d0 + profiles 3.51–3.91, which includes installing the three
  profiles.
- **Database size (bytes):** main 654,778–654,906; d0 654,853–672,223 (one outlier run); d0 + profiles
  661,052–661,248, about +1% for the profiles' schema.

**Profile installation alone** (three fixture profiles over the full core, 3 rounds): 0.37–0.43 s in total, 0.10–0.16 s
each. The plan's ceiling is ≤ 5 s.

**Reading: no material impact.**
- Query counts are identical for every question in all three configurations, including the three corrected
  functions.
- Latencies move both ways within run-to-run noise, with no consistent direction. `effects_of` and `where` vary most,
  as in earlier benchmarks.
- The lattice tests replace string comparisons on lists that are already loaded, and add no queries.
