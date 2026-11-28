# Author assignment F: frames

**Family code:** `F`
**Write your files in:** `<work>/out/` (and nowhere else).
**Your pack:** `<work>/pack/` (read `README.md` first). Read nothing outside `<work>/`.

## What to write

- `fixtures/<fixture id>.json`: about 4 fixtures. Ids start `e2-f-`. Synthetic, invented names.
- `questions.jsonl`: exactly **35 scored questions**, ids F-001 to F-035, class H.
- `probes.jsonl`: exactly **6 class G probes**, ids G-F-01 to G-F-06 (below).
- `calc/<question id>.md`: one sheet for every question with a numeric expected value.
- `slots.json`: `{"<slot>": "<question id>"}` for each boundary-condition slot below.
- `ambiguities.md`: every place where the contracts did not fix an answer (what you left out, and why).
- `self-report.md`: which files you read (paths), anything you were unsure of, and confirmation that you read nothing outside your work directory.

## Case types (exact counts over your scored questions)

| case_type | count |
|---|---:|
| positive | 14 |
| negative | 5 |
| disputed | 8 |
| unknown | 8 |
| refusal | 0 |

## Competencies (counts over your scored questions)

| Competency | count |
|---|---:|
| F1 directly stated position | 6 |
| F2 position derived through a chain | 7 |
| F3 conflicting sources | 6 |
| F4 no persistence beyond the stated interval | 4 |
| F5 hypothetical variant and the actual world | 4 |
| F6 as_of | 4 |
| angle_tolerance for candidate comparison (SD-SPA-1) | 2 |
| poses and frame_info | 2 |

## Minimum variation (questions may count towards several)

- as_of: at least 4
- perspective: at least 3
- variant world: at least 4
- alias or same-as: at least 2
- numeric derived ranges: at least 6
- at least one third of your scored questions `adversarial: true` (conflicts, denials, unknowns, wrong perspective, superseded claims, variant worlds, aliases, boundary instants, truncation).

## Boundary-condition slots

Each slot is one scored question that must exercise exactly this situation. Derive its gold from the contracts like any other.

| Slot | Situation |
|---|---|
| T-F1 | a position stated under an alias of the thing (the same-as link is accepted), asked with the canonical name |
| T-F2 | a position derived through a chain whose position statement is disputed by an accepted denial |
| T-F3 | a position derived through a chain whose position statement is disputed for the question's perspective only (another perspective sees no dispute) |
| T-F4 | `where` with two candidates of which one has no position comparable with the other, so not every pair was compared (judgement label) |

## Probes (class G)

| Probe | gap or decision | what it asks |
|---|---|---|
| G-F-01 | GAP-FRAME-1 | a point fixed in a frame anchored to a thing that moved |
| G-F-02 | GAP-FRAME-3 | a position between two stated poses (interpolation) |
| G-F-03 | GAP-FRAME-4 | the root of a frame hierarchy |
| G-F-04 | GAP-FRAME-6 | a part's position given only its assembly's |
| G-F-05 | GAP-SPATIAL-8 | holds() asked for one particular position |
| G-F-06 | GAP-SPATIAL-9 | the interval over which a derived position holds |

Each probe gives `gap` (the id in the table), `probe.accept`, `probe.path` and `prohibited` (question-format.md). Where no reader can be asked, give an empty plan.

## Quality

- Each question exercises an identifiable competency or boundary condition; no near-duplicates.
- Multi-step questions give every step's expected answer.
- Every expected field, and every evidence set, follows from the contracts and your fixture. Cite the contract section in `spec` and explain in `justification`.
- Never expect a field the contracts do not fix, or a G-unimpl field in a scored question.
