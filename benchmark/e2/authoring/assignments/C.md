# Author assignment C: causal relationships

**Family code:** `C`
**Write your files in:** `<work>/out/` (and nowhere else).
**Your pack:** `<work>/pack/` (read `README.md` first). Read nothing outside `<work>/`.

## What to write

- `fixtures/<fixture id>.json`: about 3 fixtures. Ids start `e2-c-`. Synthetic, invented names.
- `questions.jsonl`: exactly **30 scored questions**, ids C-001 to C-030, class H.
- `probes.jsonl`: exactly **9 class G probes**, ids G-C-01 to G-C-09 (below).
- `calc/<question id>.md`: one sheet for every question with a numeric expected value.
- `slots.json`: `{"<slot>": "<question id>"}` for each boundary-condition slot below.
- `ambiguities.md`: every place where the contracts did not fix an answer (what you left out, and why).
- `self-report.md`: which files you read (paths), anything you were unsure of, and confirmation that you read nothing outside your work directory.

## Case types (exact counts over your scored questions)

| case_type | count |
|---|---:|
| positive | 12 |
| negative | 6 |
| disputed | 6 |
| unknown | 4 |
| refusal | 2 |

## Competencies (counts over your scored questions)

| Competency | count |
|---|---:|
| C1 stated causes (direct and lifted) | 6 |
| C2 occurrence status of causes | 4 |
| C3 claimed effect vs accepted change (SD-CAU-1) | 6 |
| C4 one-step explanation (SD-CAU-2, -3) | 5 |
| C5 begin and end, certain or possible (changes; H-9; SD-CAU-6) | 7 |
| t1 > t2 refusal and t1 = t2 (SD-CAU-8) | 2 |

## Minimum variation (questions may count towards several)

- as_of: at least 3
- perspective: at least 3
- ambiguous attribution: at least 2
- B-time boundary examples: at least 2
- at least one third of your scored questions `adversarial: true` (conflicts, denials, unknowns, wrong perspective, superseded claims, variant worlds, aliases, boundary instants, truncation).

## Boundary-condition slots

Each slot is one scored question that must exercise exactly this situation. Derive its gold from the contracts like any other.

| Slot | Situation |
|---|---|
| T-C1 | a causal claim made about an event description that no describes link connects to any occurrence |
| T-C2 | a causal claim about a description whose describes link is denied by an accepted denial |
| T-C3 | a cause lifted through describes links, with the links required as evidence |
| T-C4 | an effect claim whose outcome moves from UNKNOWN to held (no accepted prior state) |
| T-C5 | an effect claim whose outcome becomes held some time after the event ends (delayed effect) |
| T-C6 | a causal or effect claim whose attestation carries a valid interval that excludes the question's t (timeless claim, SD-CAU-7) |

## Probes (class G)

| Probe | gap or decision | what it asks |
|---|---|---|
| G-C-01 | GAP-CAUSE-1 | a causal chain of two or more steps |
| G-C-02 | GAP-CAUSE-2 | what an event caused (forward) |
| G-C-03 | GAP-CAUSE-3 | would the state hold if the event had not happened |
| G-C-04 | GAP-CAUSE-5 | the strength or mechanism of a cause |
| G-C-05 | SD-CAU-1 | `attribution` on effects_of entries (accept absent) |
| G-C-06 | SD-CAU-2 | `timing` on explain initiators (accept absent) |
| G-C-07 | SD-CAU-2 | `alternatives` listing unaccepted initiating claims in explain (accept absent) |
| G-C-08 | SD-CAU-4 | `attestations` on changes explanations (accept absent) |
| G-C-09 | SD-CAU-9 | `applies` on effects_of entries (accept absent) |

Each probe gives `gap` (the id in the table), `probe.accept`, `probe.path` and `prohibited` (question-format.md). Where no reader can be asked, give an empty plan.

## Quality

- Each question exercises an identifiable competency or boundary condition; no near-duplicates.
- Multi-step questions give every step's expected answer.
- Every expected field, and every evidence set, follows from the contracts and your fixture. Cite the contract section in `spec` and explain in `justification`.
- Never expect a field the contracts do not fix, or a G-unimpl field in a scored question.
