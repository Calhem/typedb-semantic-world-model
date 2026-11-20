# Stage E1 architectural reconciliation: output contract (LABS-1.052)

**Status: specification, written before the code changes it describes.** Branch `feature/stage-e1-reconciliation`
from `main` `6809e4c`. Direction approved under LABS-1.052. Sources: the Stage E1 adjudication
([benchmark/e1/results/adjudication.md](../../benchmark/e1/results/adjudication.md)). No foundational ontology
semantics change: R1 adds a reported field, R2 refuses malformed questions, and R3 and R4 are documentation.

## R1. The resolved role-player set (MP-2 alongside ER-5)
**Problem.** For a role without an applying constraint, `occurrence()["roles"][label]["players"]` lists the players
of **every** account linked to the occurrence (ER-5), including unreviewed or rejected accounts and accounts whose
describes link is not established. MP-2 defines the role's players as those of the **compared** accounts. No field
reports MP-2's set, so a reader cannot tell the participants the compared accounts state from names only an
unaccepted account gives (Stage E1, LAB-025 and LAB-026).

**Contract.** Each entry of `roles` keeps every existing field unchanged (ER-5: `name`, `core_role`, `players` with
the accounts naming each player, `constraints`) and gains one field, `resolved`:

| Field | Meaning |
|---|---|
| `judgement` | `established`: an applying constraint holds (one player under `one`, the same set in every compared account under `set`). `disputed`: an applying constraint is violated. `union`: no constraint applies; the players are those the compared accounts state. `none`: no compared account names this role |
| `players` | the resolved participants: for `established`, the constraint's players; for `union`, every player of every compared account of the nearest world, grouped under the perspective's identity; for `disputed` and `none`, **empty** (the rival candidates stay in `constraints[].players`). Each entry: `names`, `accounts` (description and attesters), `status` (the answer status of those accounts' deciding attestations) |
| `compared` | the descriptions compared for this role (accepted account, describes link established, nearest world) |
| `overridden` | compared descriptions of a farther world, set aside by a nearer one |
| `not_compared` | every other description naming this role, each with why: `account <state>` (unreviewed, rejected, none) or `describes <judgement>` |
| `constraint` | the applying constraint (`event_type`, `role`, `kind`, `multiplicity`) or null |
| `support` | the attestation ids the resolved set rests on |

**Accepted evidence is not an established conclusion.** `resolved` answers only *who took part according to the
compared accounts, under the applicable rule*:
- `union` is not `established`: no rule was applied beyond reading the compared accounts;
- no part of `resolved` says the occurrence happened (that is `occurrence_status`, judged from existence
  attestations only, LABS-1.011), or that any other claim of an account holds;
- each player's `status` is the evidence status of the accounts naming it (ASSERTED, STIPULATED), never a judgement.

**Never resolved:** a player named only by an account that is not compared (unaccepted, rejected, describes link
not established) or only by a farther world's account.

**Compatibility.** Additive: no existing field changes. Every role entry of every occurrence view gains `resolved`
(the 398-view baseline: presentation only, counted at the gate). No schema change, no migration, no new query: the
set is computed from data `occurrence()` already reads. `participants` and `descriptions` are unchanged. Readers built on
`occurrence()` should use `resolved` for "who took part" and `players` for "who is said to have taken part, by
whom".

**Tests** (`tests/test_w_resolved_roles.py`): accepted accounts (a union of their players); an unaccepted account
(its player not resolved, listed in `not_compared`); a rejected account; a describes link disputed; a disputed `one`
constraint (empty, candidates in `constraints`); an established `set`; conflicting sets; identity grouping; a plan
whose own account overrides inherited ones; perspectives; both query paths.

## R2. Role-name validation
**Problem.** `holds` and `judgement` accept role names that the content type does not have and answer
NOT_YET_KNOWN, so a malformed question looks like an answer (Stage E1, ORG-011). The organisation module notes
wrote `office-holding(holder, office, context)`; its roles are `classified`, `class` and `context`.

**Contract.** Readers that take role names judge content by the **core role names** stored with every attestation
(a profile role is stored under the core role it specialises: `official-act:official` as `actor`; a profile's own new
role under its own name). The valid names of a content type are the core role names of every role it relates,
inherited ones included. A question naming any other role is refused with `UnknownRoleError` (a `ValueError`), whose
message names the type, the unknown names and the valid ones, and, for a profile's stored role name, the core name
to use instead. Nothing is answered and nothing is written.

Readers affected: `holds` and `judgement` (`roles`), `explain` (`roles`), `value_of` (`key`), `value_at`
(`key_role`, `value_role` when given). Writers are unchanged (TypeDB already refuses a role a type does not relate).

**Compatibility.** A question with valid names answers exactly as before. A question with an invalid name, which
answered NOT_YET_KNOWN or UNKNOWN, now raises. The 106,752-answer baseline is checked for any such call.

**Documentation.** The organisation module notes give the stored roles: `office-holding(classified: holder, class:
office, context)` and `classified-as(classified: holder, class: capability, context?)`.

**Tests** (`tests/test_w_role_names.py`): refused names (with the valid list); a profile's stored name pointing to
its core name; inherited roles accepted; every reader above; answers with valid names unchanged.

## R3. Functional exclusivity: v0.2 and the canonical judgement
World Ontology v0.2 4.4 says that when an accepted attestation gives a single-valued slot one value at t, another
value "is false, INFERRED by functional exclusivity", and its status table lists functional exclusivity under
INFERRED. The canonical judgement design (increment B, 2.4) lists `NOT_HOLDING` only with the reasons `denied` and
`ended`, and `PENDING` for an undecided content that a pending attestation would decide. It does not mention
exclusivity.

**Reconciliation (documentation; the implementation already does this).** A content in a functional slot whose
slot holds another value at t, established for the perspective, does **not hold**: `judgement` `not holding`,
`holds` false with status INFERRED, citing the established value's attestations. This is decided before `pending`:
an unreviewed attestation of the content itself does not make it pending while the slot is decided otherwise. It
applies only where the other value is established (ASSERTED, STIPULATED or INFERRED); a disputed slot decides
nothing. An addendum to the increment B design records this, and a test pins it (`tests/test_w_role_names.py`,
exclusivity section).

## R4. Benchmark clarifications and a revised evaluation
The frozen gold (`d0f0aa2`) and the original results stay unchanged. Clarifications are written in
`benchmark/e1/CLARIFICATIONS.md`. A **revised evaluation** applies them through a separate overlay
(`benchmark/e1/revised/overlay.json`, each change with its reason and the clarification it applies) and writes its
results to `benchmark/e1/results-revised/`, reported apart from the original:
- **Evidence for list answers:** required evidence is what supports the listed items (and any conflict); a claim
  that only excludes a candidate is explanatory, not required (X-003).
- **Writer-specific defaults:** a writer's documented interval default wins over the core `attest` rule (the
  `calibrate` writer attests until superseded when no end is given: LAB-010).
- **Restatements:** an attestation that ends or corrects a fixture claim (a restatement by the same attester) counts
  as that claim's evidence (LAB-034).
- **The reconciled contracts:** R1 (`event_role` union questions score `resolved` players: LAB-025, LAB-026), R2
  (ORG-011 is re-asked with the stored role names; its expected answer is unchanged), R3 (TEMP-017's expected answer
  follows v0.2 4.4).

E1 is recorded as **development-tier** evidence (model-authored inside the project); the external sealed evaluation
is deferred. All 272 questions are kept.
