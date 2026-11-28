# Author assignment S: spatial transformations

**Family code:** `S`
**Write your files in:** `<work>/out/` (and nowhere else).
**Your pack:** `<work>/pack/` (read `README.md` first). Read nothing outside `<work>/`.

## What to write

- `fixtures/<fixture id>.json`: about 3 fixtures. Ids start `e2-s-`. Synthetic, invented names.
- `questions.jsonl`: exactly **25 scored questions**, ids S-001 to S-025, class H.
- `probes.jsonl`: exactly **5 class G probes**, ids G-S-01 to G-S-05 (below).
- `calc/<question id>.md`: one sheet for every question with a numeric expected value.
- `slots.json`: `{"<slot>": "<question id>"}` for each boundary-condition slot below.
- `ambiguities.md`: every place where the contracts did not fix an answer (what you left out, and why).
- `self-report.md`: which files you read (paths), anything you were unsure of, and confirmation that you read nothing outside your work directory.

## Case types (exact counts over your scored questions)

| case_type | count |
|---|---:|
| positive | 11 |
| negative | 3 |
| disputed | 6 |
| unknown | 5 |
| refusal | 0 |

## Competencies (counts over your scored questions)

| Competency | count |
|---|---:|
| S1 composition (two or three transforms, with rotations) | 5 |
| S2 inverse of a stated chain | 4 |
| S3 disagreeing chains or a disputed transform | 4 |
| S4 no chain: UNKNOWN vs NOT_YET_KNOWN | 3 |
| S5 perspective | 3 |
| S6 supersession and as_of | 3 |
| frame to itself (convention) | 1 |
| truncated search (limit) | 2 |

## Minimum variation (questions may count towards several)

- as_of: at least 3
- perspective: at least 3
- variant world: at least 1
- numeric with rotation: at least 4
- at least one third of your scored questions `adversarial: true` (conflicts, denials, unknowns, wrong perspective, superseded claims, variant worlds, aliases, boundary instants, truncation).

## Boundary-condition slots

Each slot is one scored question that must exercise exactly this situation. Derive its gold from the contracts like any other.

| Slot | Situation |
|---|---|
| T-S1 | a frame asked about itself, the frame being visible in the world (mark the convention) |
| T-S2 | two distinct frames where no frame-transform involving either frame is visible at the question's as_of (another transform becomes visible only later) |
| T-S3 | a search truncated by `limit` whose route already reached contains a transform disputed by an accepted denial |

## Probes (class G)

| Probe | gap or decision | what it asks |
|---|---|---|
| G-S-01 | GAP-SPATIAL-1 | a transform with propagated uncertainty |
| G-S-02 | GAP-SPATIAL-3 | the rotation as roll, pitch and yaw |
| G-S-03 | GAP-SPATIAL-7 | the distance between two positioned things |
| G-S-04 | SD-SPA-1 | `chain_tolerance` reported by transform_between (accept absent) |
| G-S-05 | SD-SPA-2 | `basis` of a frame-to-itself transform (accept absent) |

Each probe gives `gap` (the id in the table), `probe.accept`, `probe.path` and `prohibited` (question-format.md). Where no reader can be asked, give an empty plan.

## Quality

- Each question exercises an identifiable competency or boundary condition; no near-duplicates.
- Multi-step questions give every step's expected answer.
- Every expected field, and every evidence set, follows from the contracts and your fixture. Cite the contract section in `spec` and explain in `justification`.
- Never expect a field the contracts do not fix, or a G-unimpl field in a scored question.
