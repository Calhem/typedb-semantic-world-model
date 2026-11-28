# Author assignment M: measurements

**Family code:** `M`
**Write your files in:** `<work>/out/` (and nowhere else).
**Your pack:** `<work>/pack/` (read `README.md` first). Read nothing outside `<work>/`.

## What to write

- `fixtures/<fixture id>.json`: about 4 fixtures. Ids start `e2-m-`. Synthetic, invented names.
- `questions.jsonl`: exactly **35 scored questions**, ids M-001 to M-035, class H.
- `probes.jsonl`: exactly **7 class G probes**, ids G-M-01 to G-M-07 (below).
- `calc/<question id>.md`: one sheet for every question with a numeric expected value.
- `slots.json`: `{"<slot>": "<question id>"}` for each boundary-condition slot below.
- `ambiguities.md`: every place where the contracts did not fix an answer (what you left out, and why).
- `self-report.md`: which files you read (paths), anything you were unsure of, and confirmation that you read nothing outside your work directory.

## Case types (exact counts over your scored questions)

| case_type | count |
|---|---:|
| positive | 14 |
| negative | 7 |
| disputed | 7 |
| unknown | 6 |
| refusal | 1 |

## Competencies (counts over your scored questions)

| Competency | count |
|---|---:|
| M1 stated values with instrument, uncertainty and conditions | 6 |
| M2 agreement within uncertainty | 6 |
| M3 different conditions or coverage | 3 |
| M4 corrected or superseded measurement | 3 |
| M5 conversion (affine and scale) | 4 |
| M6 calibration at measurement time | 7 |
| t as valid time (SD-MEA-1) | 2 |
| explicit instants (SD-MEA-2) | 2 |
| disjoint valid times (SD-MEA-4) | 1 |
| categorical values out of scope (SD-MEA-3) | 1 |

## Minimum variation (questions may count towards several)

- as_of: at least 3
- perspective: at least 3
- numeric: at least 14
- calibration not yet effective: at least 2
- at least one third of your scored questions `adversarial: true` (conflicts, denials, unknowns, wrong perspective, superseded claims, variant worlds, aliases, boundary instants, truncation).

## Boundary-condition slots

Each slot is one scored question that must exercise exactly this situation. Derive its gold from the contracts like any other.

| Slot | Situation |
|---|---|
| T-M1 | a measurement recorded against an alias of the bearer (same-as accepted), asked by the canonical name |
| T-M2 | two measurements compared where the measured content of one is denied by an accepted denial |
| T-M3 | measurements asked with `t` where an accepted denial of a measured content covers t |
| T-M4 | two explicit instantaneous measurements at the same instant, compared |
| T-M5 | measurement_calibration where the activity's start is an uncertain window inside which the certificate's validity ends |
| T-M6 | a stated (not measured) quality value given in a non-SI unit, as listed by measurements |

## Probes (class G)

| Probe | gap or decision | what it asks |
|---|---|---|
| G-M-01 | GAP-MEAS-1 | pass or fail against a specification |
| G-M-02 | GAP-MEAS-4 | the best estimate from several measurements |
| G-M-03 | GAP-MEAS-5 | conversion of a compound unit |
| G-M-04 | GAP-MEAS-7 | the latest or current value |
| G-M-05 | GAP-MEAS-11 | the derivation of a derived quantity |
| G-M-06 | GAP-MEAS-12 | comparison of categorical measured values |
| G-M-07 | GAP-MEAS-13 | comparison of measurements at disjoint times of a quantity declared constant |

Each probe gives `gap` (the id in the table), `probe.accept`, `probe.path` and `prohibited` (question-format.md). Where no reader can be asked, give an empty plan.

## Quality

- Each question exercises an identifiable competency or boundary condition; no near-duplicates.
- Multi-step questions give every step's expected answer.
- Every expected field, and every evidence set, follows from the contracts and your fixture. Cite the contract section in `spec` and explain in `justification`.
- Never expect a field the contracts do not fix, or a G-unimpl field in a scored question.
