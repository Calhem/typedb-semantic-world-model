# Author assignment P: process steps

**Family code:** `P`
**Write your files in:** `<work>/out/` (and nowhere else).
**Your pack:** `<work>/pack/` (read `README.md` first). Read nothing outside `<work>/`.

## What to write

- `fixtures/<fixture id>.json`: about 3 fixtures. Ids start `e2-p-`. Synthetic, invented names.
- `questions.jsonl`: exactly **25 scored questions**, ids P-001 to P-025, class H.
- `probes.jsonl`: exactly **6 class G probes**, ids G-P-01 to G-P-06 (below).
- `calc/<question id>.md`: one sheet for every question with a numeric expected value.
- `slots.json`: `{"<slot>": "<question id>"}` for each boundary-condition slot below.
- `ambiguities.md`: every place where the contracts did not fix an answer (what you left out, and why).
- `self-report.md`: which files you read (paths), anything you were unsure of, and confirmation that you read nothing outside your work directory.

## Case types (exact counts over your scored questions)

| case_type | count |
|---|---:|
| positive | 10 |
| negative | 5 |
| disputed | 5 |
| unknown | 5 |
| refusal | 0 |

## Competencies (counts over your scored questions)

| Competency | count |
|---|---:|
| P1 steps in time order | 5 |
| P2 disputed step kept and flagged | 4 |
| P3 before with windows (SD-CAU-5 examples) | 8 |
| P4 overlapping or unknown intervals | 4 |
| P5 sub-steps, one level per call | 2 |
| several accounts (SD-CAU-10) | 2 |

## Minimum variation (questions may count towards several)

- as_of: at least 2
- perspective: at least 3
- windows: at least 5
- instantaneous events: at least 3
- variant world: at least 1
- at least one third of your scored questions `adversarial: true` (conflicts, denials, unknowns, wrong perspective, superseded claims, variant worlds, aliases, boundary instants, truncation).

## Boundary-condition slots

Each slot is one scored question that must exercise exactly this situation. Derive its gold from the contracts like any other.

| Slot | Situation |
|---|---|
| T-P1 | two instantaneous events whose possible instants share one moment (touching windows), ordered with before |
| T-P2 | a description with two usable accounts giving different times, ordered against another event |
| T-P3 | an instantaneous event at the very instant another, durative event starts, ordered with before |

## Probes (class G)

| Probe | gap or decision | what it asks |
|---|---|---|
| G-P-01 | GAP-PROC-1 | the explicit (prescribed) order of steps |
| G-P-02 | GAP-PROC-2 | was the procedure followed |
| G-P-03 | GAP-PROC-3 | which preconditions held when a step started |
| G-P-04 | GAP-PROC-4 | how long a step took |
| G-P-05 | GAP-PROC-7 | which expected step did not happen |
| G-P-06 | SD-CAU-10 | `usable_accounts` on interval (accept absent) |

Each probe gives `gap` (the id in the table), `probe.accept`, `probe.path` and `prohibited` (question-format.md). Where no reader can be asked, give an empty plan.

## Quality

- Each question exercises an identifiable competency or boundary condition; no near-duplicates.
- Multi-step questions give every step's expected answer.
- Every expected field, and every evidence set, follows from the contracts and your fixture. Cite the contract section in `spec` and explain in `justification`.
- Never expect a field the contracts do not fix, or a G-unimpl field in a scored question.
