# Stage D-3 benchmark (LABS-1.029)

`scripts/measure_physical.py --extended --mechanical --organisation`, plus `--laboratory`, 5 rounds per run. There
were four interleaved rounds of each configuration: rounds 1-2 in the order main, D3 code, D3 + laboratory, and
rounds 3-4 reversed. Both D-3 configurations ran from a clean checkout of f96aee9; the baseline ran from a clean
checkout of `main` 8461e23 (D-2), with its own script.

| Configuration | Code | Files |
|---|---|---|
| D2 (main) | 8461e23: the gearbox and Acme worlds | `r1-4-d2-main-8461e23.json` |
| D3 code | f96aee9, the same two worlds | `r1-4-d3-code.json` |
| D3 + laboratory | f96aee9, plus the laboratory profile and the laboratory world in the same database | `r1-4-d3-laboratory.json` |

Median over the four runs' medians (ms); q = queries per question, identical in every run of every configuration.

| Question | q | D2 main | D3 code | D3 + lab |
|---|---:|---:|---:|---:|
| poses(gear-in) | 14 | 24.4 | 24.5 | 30.6 |
| composition(gbx-100) | 218 | 411.8 | 399.2 | 490.2 |
| contents(workshop) | 114 | 211.9 | 205.6 | 335.7 |
| materials(cover) | 42 | 62.4 | 60.6 | 67.0 |
| frame_info(f-bench) | 16 | 26.4 | 26.0 | 29.2 |
| facts_about(housing) | 14 | 29.8 | 29.0 | 34.7 |
| where(gbx-100, f-workshop) | 39 | 84.9 | 82.5 | 228.5 |
| where(gear-in, f-workshop) | 33 | 50.5 | 50.2 | 111.6 |
| where(bench-1, f-gearbox) | 40 | 62.3 | 58.3 | 160.8 |
| transform_between(f-gearbox, f-workshop) | 7 | 10.8 | 10.7 | 12.1 |
| effects_of(ev-worklog-replacement) | 197 | 274.2 | 271.5 | 472.1 |
| changes(gbx-100, repair) | 71 | 207.2 | 203.7 | 203.5 |
| causes_of(o-test-run) | 129 | 229.2 | 233.7 | 251.0 |
| explain(operational) | 284 | 449.8 | 427.5 | 478.2 |
| process_steps(o-repair) | 153 | 252.8 | 233.1 | 235.7 |
| actions_of(technician) | 73 | 148.2 | 146.4 | 159.1 |
| value_of(condition) | 23 | 42.1 | 41.5 | 71.1 |
| measurements(housing, mass) | 100 | 149.3 | 142.7 | 142.8 |
| compare_measurements(housing, mass) | 100 | 143.8 | 142.6 | 153.7 |
| capable(technician, workshop) | 14 | 28.9 | 27.9 | 27.2 |
| is_agent(apprentice) | 14 | 19.1 | 18.2 | 19.5 |
| roles_of(apprentice) | 16 | 23.1 | 23.7 | 24.0 |
| check_action(worklog) | 109 | 172.3 | 158.9 | 167.7 |
| account_attestations(worklog) | 19 | 30.7 | 29.8 | 30.5 |
| direct_dependencies(output-shaft) | 14 | 20.8 | 20.6 | 21.6 |
| dependencies(output-shaft, functional) | 5 | 41.7 | 38.9 | 41.2 |
| connections(input-shaft) | 14 | 23.3 | 22.3 | 24.5 |
| replacement(ev-cmms-replacement) | 110 | 159.9 | 145.6 | 179.0 |
| office_holders(site-manager, day 9) | 29 | 82.1 | 81.8 | 72.9 |
| offices_of(cal, day 9) | 44 | 79.7 | 73.6 | 97.1 |
| authorised(bea) | 15 | 20.6 | 20.3 | 22.9 |
| official_act(ev-cal-signs) | 115 | 177.0 | 167.8 | 178.5 |
| employment(acme) | 14 | 21.9 | 21.4 | 22.2 |
| provenance(s12-b) | 336 |  |  | 637.6 |
| calibration_status(balance-b7) | 16 |  |  | 23.8 |
| measurement_calibration(sample-12) | 411 |  |  | 610.0 |
| interpretations(m-lab2-result) | 41 |  |  | 94.1 |
| compare_measurements(sample-12) | 315 |  |  | 483.9 |

- **Build time (s):** D2 4.64–5.44; D3 code 4.79–5.53; D3 + laboratory 6.62–7.01 (which includes installing the
  profile and building the laboratory world).
- **Database size (bytes):** D2 801,429–801,567; D3 code 801,478–818,705; D3 + laboratory 989,950–1,007,714, which is
  +24% for the profile and the laboratory world. With the profile alone (no laboratory world, a probe run twice) the
  size is 810,392–810,474, +1%.

## Reading
- **The D-3 code: no regression.** All 33 existing questions have the same query counts in D2 and D3 code, and their
  medians agree within run-to-run noise (D3 code is 0–9% faster on most). The shared-judgement change (`_claims`
  gains a `support` field) costs nothing measurable.
- **The laboratory world in the same database slows some gearbox questions, at identical query counts:**
  - `where` (the three frame questions) ×2.5–2.8, `effects_of` ×1.7, `contents` ×1.6, `value_of` ×1.7. The other
    existing questions are within noise;
  - this is consistent across all four runs (for example `where(gbx-100, f-workshop)`: 79–90 ms in D3 code,
    217–255 ms with the laboratory world);
  - **not the profile:** a probe with the laboratory profile installed but no laboratory world (run twice) gave D-2
    times (`where(gbx-100, f-workshop)` 85–96 ms, `effects_of` 259–281 ms);
  - so the cost comes from **another world's data**. The likely explanation (not verified) is that some queries
    match by type across every world before narrowing to theirs. The laboratory world (from Stage C) has many measurements, locations and attestations, while Acme, in
    D-2, had few and changed nothing. The cause was not isolated further (the scope was frozen during validation).
    It is a scaling finding for Stage E, not a correctness issue: answers are unchanged (tests: three worlds in one
    database).
- **New reports:**
  - `calibration_status` costs 16 queries (about 24 ms);
  - `interpretations` costs 41: the records' dependants, and one judgement per interpretation;
  - `provenance(s12-b)` costs 336: two constitution links, two sampling accounts (s12-b and s12-a), each with occurrence and effect
    statuses, existence (attested and core) and the location history;
  - `measurement_calibration(sample-12)` costs 411: seven records, each with the activity's instrument, its
    calibration status and its reference check;
  - `compare_measurements(sample-12)` (a core report, timed on the larger laboratory world) costs 315.
