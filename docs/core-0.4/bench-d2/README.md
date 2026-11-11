# Stage D-2 benchmark (LABS-1.026)

`scripts/measure_physical.py --extended --mechanical`, plus `--organisation`, 5 rounds per run. There were four
interleaved rounds of each configuration: rounds 1-2 in the order main, D2 code, D2 + organisation, and rounds 3-4
reversed, to separate code effects from run order and drift. Both D-2 configurations ran from a clean checkout of
6a7bc56; the baseline ran from a clean checkout of `main` 153c2f2 (D-1).

| Configuration | Code | Files |
|---|---|---|
| D1 (main) | 153c2f2 | `r1-4-d1-main-153c2f2.json` |
| D2 code | 6a7bc56, the same gearbox world | `r1-4-d2-code.json` |
| D2 + organisation | 6a7bc56, plus the organisation profile and the Acme world in the same database | `r1-4-d2-organisation.json` |

Median over the four runs' medians (ms); queries per question were identical in every run.

| Question | q (all three) | D1 | D2 code | D2 + org |
|---|---:|---:|---:|---:|
| poses(gear-in) | 14 | 27.9 | 29.6 | 28.6 |
| composition(gbx-100) | 218 | 489.6 | 558.8 | 506.2 |
| contents(workshop) | 114 | 195.1 | 224.2 | 241.2 |
| materials(cover) | 42 | 70.8 | 72.5 | 79.5 |
| frame_info(f-bench) | 16 | 29.7 | 30.3 | 32.7 |
| facts_about(housing) | 14 | 33.2 | 34.1 | 34.4 |
| where(gbx-100, f-workshop) | 39 | 107.3 | 139.8 | 115.1 |
| where(gear-in, f-workshop) | 33 | 61.2 | 62.5 | 62.2 |
| where(bench-1, f-gearbox) | 40 | 70.6 | 78.0 | 70.4 |
| transform_between | 7 | 12.8 | 13.3 | 12.7 |
| effects_of(ev-worklog-replacement) | 197 | 405.2 | 469.9 | 323.8 |
| changes(gbx-100, repair) | 71 | 239.8 | 268.9 | 227.3 |
| causes_of(o-test-run) | 129 | 274.6 | 274.3 | 243.4 |
| explain(operational) | 284 | 534.8 | 533.8 | 509.3 |
| process_steps(o-repair) | 153 | 282.1 | 275.3 | 301.8 |
| actions_of(technician) | 73 | 173.5 | 176.9 | 164.0 |
| value_of(condition) | 23 | 54.4 | 52.6 | 49.8 |
| measurements(housing, mass) | 100 | 165.7 | 187.0 | 184.7 |
| compare_measurements(housing, mass) | 100 | 184.7 | 170.6 | 163.2 |
| capable(technician, workshop) | 14 | 30.7 | 31.6 | 30.6 |
| is_agent(apprentice) | 14 | 21.1 | 20.9 | 21.7 |
| roles_of(apprentice) | 16 | 26.4 | 27.3 | 27.5 |
| check_action(worklog) | 109 | 193.8 | 188.2 | 186.8 |
| account_attestations(worklog) | 19 | 34.0 | 33.4 | 33.8 |
| direct_dependencies(output-shaft) | 14 | 25.7 | 23.4 | 23.8 |
| dependencies(output-shaft, functional) | 5 | 43.0 | 41.6 | 43.5 |
| connections(input-shaft) | 14 | 26.8 | 25.4 | 26.7 |
| replacement(ev-cmms-replacement) | 110 | 173.7 | 190.8 | 174.1 |
| **office_holders(site-manager, day 9)** (new) | 29 | | | 91.3 |
| **offices_of(cal, day 9)** (new) | 44 | | | 92.2 |
| **authorised(bea)** (new) | 15 | | | 23.9 |
| **official_act(ev-cal-signs)** (new) | 115 | | | 193.2 |
| **employment(acme)** (new) | 14 | | | 24.7 |

- **Build time (s):** D1 4.50–5.92; D2 code 4.71–6.32; D2 + organisation 5.69–8.56 (which includes installing the
  profile and building Acme).
- **Database size (bytes):** D1 720,192–720,406 (one run at 737,711); D2 code 720,270–720,346; D2 + organisation
  801,313–801,689, which is +11% for the profile and the Acme world.

## Reading
- **Existing questions: no regression.**
  - Query counts are identical in all three configurations for all 28 existing questions, including the
    capability questions that now use the shared judgement helpers.
  - Medians move both ways (`composition` +14%, `effects_of` −20% with the organisation world present). Individual
    runs vary more than that: `effects_of` in D2 code ranges 372–671 ms. With the reversed rounds, no consistent
    direction remains, so these are run-to-run noise.
- **The Acme world in the same database** changes no gearbox query count. The two worlds share only the `agent` and
  `can-sign-off` concepts.
- **New reports:**
  - `authorised`, `employment` and the capability questions cost 14–15 queries (about 24 ms);
  - `office_holders` costs 29 queries: the appointments, the constraint, and per-appointment judgement;
  - `offices_of` costs 44: it checks the conflict of each established office;
  - `official_act` costs 115: the account, the occurrence status, the office, authority, capability and agency.
