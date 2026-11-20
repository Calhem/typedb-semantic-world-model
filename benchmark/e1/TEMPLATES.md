# Question templates (Stage E1)

Each template is one kind of question, answered through one public reader (see `spec/reader-docs.md`). Common
parameters: `world`, `t` (a valid time, `"T<d>"`), optional `as_of` (a knowledge time, `"@mark"`; default: now) and
`perspective` (default `system`). `expected` may contain only the fields listed; omit a field to leave it unscored.

## Vocabularies
- **Judgement** (canonical, increment B design 2.4): `established`, `disputed`, `not holding`, `pending`, `unknown`.
  - `not holding`: what the perspective accepts says the content does not hold at t (an accepted denial covers t, or an
    accepted claim has ended before t, or begins after t and nothing else decides).
  - `pending`: nothing the perspective accepts decides t, but an unreviewed attestation would.
  - `unknown`: nothing decides t (no records, or only records that do not cover t, or a missing end).
- **Status** (v0.2 5.6 with Core 0.3 D1, D4): `ASSERTED`, `STIPULATED`, `INFERRED`, `DISPUTED`, `UNKNOWN`,
  `NOT_YET_KNOWN` (nothing about the content visible at the knowledge time). Observations are reported `ASSERTED`
  (D1); mixed support is labelled STIPULATED > ASSERTED > INFERRED (D4).
- **Applicability** (capable, authorised, calibration): `established`, `denied`, `expired`, `not yet effective`,
  `disputed`, `not established` (see `capable` in reader-docs).

## Templates
| Template | Reader | Parameters | `expected` fields |
|---|---|---|---|
| `holds` | `holds` / `judgement` | `type`, `roles` | `judgement`; `status` |
| `value_at` | `value_at` | `type`, `subject` (functional slot, e.g. `located-at` with subject the located thing) | `status`; `values` (ids; empty when none) |
| `exists` | `exists` | `thing` | `status`; `holds` (true, false or null) |
| `same_thing` | `identity` | `a`, `b` | `same` (true when the perspective treats them as one thing); `conflict` (true when either is in a reported conflict group, ID-5) |
| `aliases` | `identity` | `x` | `members` (every name in x's identity class, x included) |
| `parts` | `parts` | `whole` | `parts` (every transitive part established at t) |
| `dependencies` | `direct_dependencies` | `dependent` | `dependees` (established at t); `disputed` (dependees whose dependency is disputed) |
| `event_role` | `occurrence` | `occurrence`, `role` (a stored role label, e.g. `official-act:official`, `event:actor`) | `judgement` (`established`, `disputed`, or `union` when no event-role constraint applies to the role); `players` (list of identity groups, each a list of names); `reason` (for a dispute: `several players in one account`, `accounts name different players`, both joined by `; `, or `accounts name different sets of players`); `multiplicity` (`one` or `set`, of the applying constraint) |
| `occurrence_status` | `occurrence_status` | `occurrence`, `t` | `status` (`accepted`, `denied`, `disputed`, `not established`) |
| `office_holders` | `organisation.office_holders` | `office`, `context` | `holders` (established holders at t); `conflict` (true when an established exclusive-office constraint is violated at t) |
| `capable` | `capable` | `holder`, `capability`, `context` (optional) | `judgement` (applicability vocabulary) |
| `authorised` | `organisation.authorised` | `holder`, `power`, `scope` | `judgement` (applicability vocabulary) |
| `calibrated` | `laboratory.calibration_status` | `instrument` | `judgement` (applicability vocabulary) |
| `move` | `move` (a write, run on a fresh copy of the scenario) | `thing`, `to` (one id or a list), `t` (when the move happens), `actor`, `attester` | `outcome` (`recorded` or `refused`); `origin` (when recorded: list of places) |
| `officials` | `organisation.official_act` | `event` (an official-act description id) | `officials` (every official the act names) |

## Notes for authors
- State the context completely in `params` (world, t, perspective, as_of where it matters).
- Give at least one question per category for each of established, disputed, not holding (or denied), and unknown
  (or not established, or pending) outcomes where the category allows it; include adversarial items (distractors,
  look-alike names, stale knowledge times, an unaccepted claim that would change the answer if it counted).
- `required_evidence`: the ids whose attestations the answer must rest on (for `holds`, `value_at`, `exists`: the
  deciding attestations; leave it empty where the template reports no support). `forbidden_evidence`: ids that must
  not be cited as support (for example an unaccepted or rejected claim).
- Every expected answer cites, in `spec`, the rule it follows, and says in `justification` why, in a sentence or two.
