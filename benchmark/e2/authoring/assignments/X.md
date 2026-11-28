# Author assignment X: multi-step reasoning

**Family code:** `X`
**Write your files in:** `<work>/out/` (and nowhere else).
**Your pack:** `<work>/pack/` (read `README.md` first). Read nothing outside `<work>/`.

## What to write

- `fixtures/<fixture id>.json`: about 4 fixtures. Ids start `e2-x-`. Synthetic, invented names.
- `questions.jsonl`: exactly **30 scored questions**, ids X-001 to X-030, class H.
- `probes.jsonl`: exactly **4 class G probes**, ids G-X-01 to G-X-04 (below).
- `calc/<question id>.md`: one sheet for every question with a numeric expected value.
- `slots.json`: `{"<slot>": "<question id>"}` for each boundary-condition slot below.
- `ambiguities.md`: every place where the contracts did not fix an answer (what you left out, and why).
- `self-report.md`: which files you read (paths), anything you were unsure of, and confirmation that you read nothing outside your work directory.

## Case types (exact counts over your scored questions)

| case_type | count |
|---|---:|
| positive | 10 |
| negative | 5 |
| disputed | 6 |
| unknown | 5 |
| refusal | 4 |

## Competencies (counts over your scored questions)

| Competency | count |
|---|---:|
| X1 instrument position at measurement time | 4 |
| X2 calibration then certificate facts | 4 |
| X3 replaced part then its position or value | 3 |
| X4 explanation then occurrence status | 4 |
| X5 process steps across worlds | 3 |
| X6 office holder of a step's official | 4 |
| holds and value_at refusals and exact content (SD-CORE-1, -2) | 4 |
| cross-domain chained measurement and frames | 4 |

## Minimum variation (questions may count towards several)

- as_of: at least 4
- perspective: at least 4
- variant world: at least 3
- plans of 3 or more steps: at least 6
- at least one third of your scored questions `adversarial: true` (conflicts, denials, unknowns, wrong perspective, superseded claims, variant worlds, aliases, boundary instants, truncation).

## Boundary-condition slots

Each slot is one scored question that must exercise exactly this situation. Derive its gold from the contracts like any other.

| Slot | Situation |
|---|---|
| T-X1 | holds asked for a classification without its optional context, where the recorded classification has a context |
| T-X2 | holds asked for a content with a mandatory role missing |
| T-X3 | value_at given key_role without value_role |
| T-X4 | value_at asked for the holders of an exclusive office whose two accepted appointments conflict |
| T-X5 | a calibration-then-certificate plan where the measuring activity's start is an uncertain window inside which a certificate lapses and another begins |
| T-X6 | an explanation plan where one initiating claim is accepted and another is unreviewed |

## Probes (class G)

| Probe | gap or decision | what it asks |
|---|---|---|
| G-X-01 | GAP-MULTI-1 | a free question needing the system to compose its own plan (not callable) |
| G-X-02 | GAP-MULTI-3 | where was the part whose measurement failed |
| G-X-03 | GAP-MULTI-6 | the derivation record of a chained answer |
| G-X-04 | SD-CORE-3 | `constraint_support` on a facts_about entry disputed under an exclusive office (accept absent) |

Each probe gives `gap` (the id in the table), `probe.accept`, `probe.path` and `prohibited` (question-format.md). Where no reader can be asked, give an empty plan.

## Quality

- Each question exercises an identifiable competency or boundary condition; no near-duplicates.
- Multi-step questions give every step's expected answer.
- Every expected field, and every evidence set, follows from the contracts and your fixture. Cite the contract section in `spec` and explain in `justification`.
- Never expect a field the contracts do not fix, or a G-unimpl field in a scored question.
