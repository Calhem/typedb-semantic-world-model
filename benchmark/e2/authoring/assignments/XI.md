# Author assignment XI: identity conflicts (X family, identity subset)

**Family code:** `X` (every question has `"subset": "identity"`)
**Write your files in:** `<work>/out/` (and nowhere else).
**Your pack:** `<work>/pack/` (read `README.md` first). Read nothing outside `<work>/`.

## What to write

- `fixtures/<fixture id>.json`: about 2 fixtures. Ids start `e2-xi-`. Synthetic, invented names.
- `questions.jsonl`: exactly **12 scored questions**, ids X-101 to X-112, class H.
- No probes.
- `calc/<question id>.md`: one sheet for every question with a numeric expected value.
- `slots.json`: `{"<slot>": "<question id>"}` for each boundary-condition slot below.
- `ambiguities.md`: every place where the contracts did not fix an answer (what you left out, and why).
- `self-report.md`: which files you read (paths), anything you were unsure of, and confirmation that you read nothing outside your work directory.
- `desirability.jsonl`: one line per question, written **after** its gold: `{"id", "expected_without_id5", "what_id5_hides"}`. This is a separate assessment of whether the ID-5 answer is the one an evaluator would want; it never changes the conformance gold.

## Case types (exact counts over your scored questions)

| case_type | count |
|---|---:|
| positive | 5 |
| negative | 3 |
| disputed | 4 |
| unknown | 0 |
| refusal | 0 |

## Competencies (counts over your scored questions)

| Competency | count |
|---|---:|
| chains with one denied same-as pair | 3 |
| cycles with one disputed pair | 3 |
| groups of 3 to 6 names | 3 |
| perspective or as_of at which a group splits or merges | 3 |

## Minimum variation (questions may count towards several)

- as_of: at least 2
- perspective: at least 2
- at least one third of your scored questions `adversarial: true` (conflicts, denials, unknowns, wrong perspective, superseded claims, variant worlds, aliases, boundary instants, truncation).

## Quality

- Each question exercises an identifiable competency or boundary condition; no near-duplicates.
- Multi-step questions give every step's expected answer.
- Every expected field, and every evidence set, follows from the contracts and your fixture. Cite the contract section in `spec` and explain in `justification`.
- Never expect a field the contracts do not fix, or a G-unimpl field in a scored question.
