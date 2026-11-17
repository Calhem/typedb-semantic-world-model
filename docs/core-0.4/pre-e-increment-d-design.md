# Pre-Stage E correction, increment D: event-role exclusivity (DI-2), design

**Status: approved at `4596507` (LABS-1.043, ER-1 to ER-8); implemented on the same branch and validated
(LABS-1.044), awaiting review, not merged. See [pre-e-increment-d.md](pre-e-increment-d.md).** Sections 6 and 7 describe the state before
implementation ("Current" is the code as merged after increment C). Branch `feature/pre-e-d-event-roles`, from
`main` at `bf8bb34` (increment C merged). Stage E has not begun. The foundational ontology is unchanged; the one schema
addition (section 8) is an additive storage module, as functional slots were (A0.3).

Approved direction: R-6 with choices F, G and H ([pre-stage-e-correctness-review.md](pre-stage-e-correctness-review.md),
sections 5 and 6), and LABS-1.036:
- **R-6:** a core mechanism (single-valued event roles as data); declarations by profiles; one naming rule for roles
  in the merged view;
- **F:** the merged occurrence view uses each description's own role name, with the core role alongside;
- **G:** single-valued declarations decided per profile, against the domain's actual semantics;
- **H:** declarations stored as data; players compared through same-as;
- **LABS-1.036:** event-role cardinality is scoped to the intended event kind and role, never universal; a constraint
  that is not established never makes otherwise compatible accounts disputed; one canonical judgement mechanism.

Executable examples: `probes/pre_e_d_examples.py` (output `.out.txt`, section 6). Impact on the reference worlds:
`probes/pre_e_d_impact.py` (output `.out.txt`, section 7). Both compute the proposed rule in
`probes/pre_e_d_rule.py`, from public readers only.

## 1. The defect, and two corrections to its premises
**DI-2.** v0.2 §3.2 (D9) says that roles a profile declares single-valued for an event kind make different players
DISPUTED in the merged view of an occurrence. `occurrence()` has no such rule: it unions, under each core role name,
the players of every description the perspective links to the occurrence.

Preparing this design established two facts that change how the issue should be read:
1. **Within one account, every event role already holds at most one player.** In TypeDB 3.14.1 a role with no
   cardinality annotation is `@card(0..1)`, and no event role (core or profile) declares another. Writing one
   description with two actors, two patients, two removed or two fitted parts is refused by the database (checked on
   a throwaway database: `[CNT5] Constraint '@card(0..1)' has been violated`). So several players of one role can
   only arise **across accounts** of the same occurrence, and a job that replaced two bearings can only be recorded as
   two accounts of one occurrence (or as two occurrences). Two accounts naming different removed parts are therefore
   ambiguous on their face: two sources disagreeing, or two parts of one job. This is registered as a new finding
   (DI-13, section 10); this increment does not change it.
2. **The review's reference conflict is a vocabulary artefact.** The pre-Stage E review counted one reference
   occurrence, `o-bearing-replacement`, whose accepted accounts name "different removed parts (bearing-1 and
   bearing-3)". Those two players come from different roles: bearing-1 is the removed part of the CMMS's
   `replacement` account, and bearing-3 is the `patient` of the technician's core work log (the part the technician
   worked on, which is the fitted part). The current view merges them because both are reported under the core role
   name `patient`. The genuinely conflicting account (the inspector's, removed = bearing-2) is not accepted by the
   system. Section 7 gives the measured counts.

## 2. Terms
- **Account:** an event description together with a source's attestation of it (its occurrence interval). The
  perspective accepts it or not, exactly as `interval()` and `occurrence_status()` judge it today.
- **Link:** a `describes(description, occurrence)` claim, judged by the canonical per-content record (increment B).
- **Compared account:** an account whose description is of the constrained event type (or a subtype), whose link to
  the occurrence is established and whose account is accepted, for the perspective at the knowledge time.
- **Own role name / core role:** the role as stored (`replacement:removed`) and the core role it specialises
  (`patient`; `core_role()`); a profile's own new role (`replacement:fitted`) is its own core-level role.

## 3. Proposed semantics
### 3.1 Declaration and scope
An **event-role constraint** says: for an occurrence, the compared accounts of event type `E` (and its subtypes) name
at most one player, under identity, in core role `R`. It is:
- **declared by a profile, on the profile's own event types only.** The core declares none, and no constraint can be
  placed on the core `event` type, so cardinality is never universal (LABS-1.036). A profile cannot constrain another
  profile's types (the rule profile slots already follow);
- **named by the core role** (`actor` for `official-act:official`), as functional slots are, and inherited by
  subtypes: a subtype adds constraints and never loses one;
- **unconditional or kind-scoped.** An unconditional constraint applies to every occurrence with compared accounts of
  that type. A kind-scoped constraint names an event kind (a category); it applies to an occurrence only where
  `classified-as(occurrence, kind)` is **established** for the perspective and knowledge time, at the occurrence's
  start (the earliest start among the accepted accounts with an established link, whatever their type). Not
  established, disputed, pending or unknown: the constraint does not apply, and the role is a union (LABS-1.036: an
  unestablished constraint never makes compatible accounts disputed). This is how a role whose cardinality depends
  on the operation is constrained: the operation is said to be of that kind, by a claim that is itself judged;
- **stored as data** (choice H), with no change to the foundational ontology (section 8).

### 3.2 Evaluation by the canonical mechanism
For one occurrence, one world, one perspective and one knowledge time:
1. **Accounts.** Every description linked to the occurrence (or to anything the perspective's identity makes the same
   occurrence) by a visible `describes` claim is listed, accepted or not. Each gets the link's canonical judgement
   (`claim_label` of its record, as `occurrence_status` reports it) and its account state in `occurrence_status`'s
   vocabulary (accepted, unreviewed, rejected, none), and its world depth.
2. **Applicable constraints.** For each constraint on the description types present: unconditional, or kind-scoped and
   its classification established at the occurrence's start (the classification is an ordinary content, judged by
   the canonical record; its own judgement is reported with the constraint).
3. **Comparison.** Only compared accounts take part. Among them, the **nearest world** with a compared account of the
   constrained type decides, as for functional slots (`_judge`: a variant overrides what it inherited); accounts from
   deeper worlds are listed as `overridden`. Players are grouped by the perspective's identity (`same-as`).
4. **Judgement of a constrained role.** One question ("who was the official?"), so rule Q (increment C) applies:
   - two or more distinct players: **DISPUTED**, `support` empty; each player lists its names, the accounts naming it
     and their sources, and the support status of those accounts;
   - one player: **established**, status the core rule (`answer_status`) over the union of the deciding account
     attestations, listed in `support`;
   - no compared account names the role: not judged (`judgement` None).
5. **Unconstrained roles** stay a union (rule C: no collective status); each player lists its accounts, each with its
   own account state.

The occurrence's own existence (`occurrence_status`, `exists`) is never decided by this: a dispute about who took part
says nothing about whether it happened (v0.2 §3.2).

### 3.3 Role specialisation in the merged view (choice F)
`occurrence()` gains two fields; nothing is removed:
- **`accounts`**: one entry per linked description: its event type, sources, link judgement, account state, world
  depth and its players by **own role name**, each with the core role it specialises;
- **`roles`**: one entry per stored role label (`replacement:removed`, `event:patient`, `official-act:official`), with
  its own name, its core role, its players (each citing its accounts) and, for a constrained role, the constraint
  (declaring type, kind, whether it applies and why), the judgement, status, support and the overridden accounts.
  Keys are stored labels, so two profiles' roles with the same short name never merge.

`descriptions` and `participants` keep their current answers (they are the core-role projection, documented as such):
`participants` is what a caller reads today, and keeping it avoids an incompatible change. Every caller that needs the
precise view reads `roles`. The one naming rule (R-6): **the merged view is keyed by the stored role label; the core
role is an attribute of each entry.** Accounts of different types are never compared against each other: the core
work log's `patient` and a replacement's `removed` are listed side by side, each under its own label.

### 3.4 Identity
Players are compared under the perspective's identity at the knowledge time, the same `Identity` every other reader
uses (H). Two names connected by an accepted `same-as` are one player (listed with both names); for a perspective that
has not accepted that link they are two, and a constrained role naming both is DISPUTED for that perspective. The
occurrence itself is identified the same way (`descriptions()` already merges co-referring occurrences).

### 3.5 Conflicting accepted accounts
Nothing is merged in storage and nothing is hidden:
- every account stays listed with its own judgement, whether compared or not, and an unreviewed, rejected or disputed
  one is shown with its state (a pending account never decides, and never hides an accepted one);
- a DISPUTED role cites every player, every account and every source, in the same shape as other disputes (increment
  B): `judgement` "disputed", status DISPUTED, the players on each side;
- each account's own report (`replacement`, `official_act`, the sampling reports) is unchanged: it describes what that
  source says.

### 3.6 Worlds, perspectives, valid time and knowledge time
- **Perspective:** decides which links and accounts are accepted, which `same-as` links hold and whether a kind is
  established. The same occurrence can be DISPUTED for one perspective and established for another (X1, X1b, X3b).
- **Knowledge time:** `as_of` limits every claim and acceptance to those recorded by then (X6a).
- **Hypothetical worlds:** a variant inherits its base's claims up to its branch point (the existing rule), so an
  account of an occurrence after the branch is not part of the plan (X6b). Where the plan has its own account, the
  plan's stipulation decides and the inherited ones are `overridden` (X6c), as for functional slots.
- **Valid time:** a constrained role is not a state at a time: an occurrence's participants do not change while it
  happens. The accounts' own intervals are reported, not used for the role judgement; valid time enters only through
  the kind-scoped classification, judged at the occurrence's start (X6d: a classification beginning later does not
  apply).

### 3.7 Multiplicity is not conflict
Several players of one role across the accounts of one occurrence are **never, by themselves, a conflict**. A role is
exclusive only where an **applicable, established** cardinality constraint requires it:
- an unconditional constraint declared by a profile for the event type (or a supertype) of the compared accounts; or
- a kind-scoped constraint whose classification of the occurrence is ESTABLISHED by its canonical record for the
  world, perspective and knowledge time, at the occurrence's start.

In every other case (no constraint; a kind-scoped constraint whose classification is pending, disputed, not holding,
not yet effective or unknown; accounts of a type the constraint does not cover; accounts not accepted, or with a link
not established) the players are a **union**: each is listed with the accounts that name it and their own judgements,
and the role has no judgement and no status (rule C). Examples X2, X2b, X2d, X6d and X7a, X7b, X7c, X7d2 and X7d4
are multiplicity without conflict; X1, X2c, X3b, X7a2, X7d and X7d3 are conflicts under an established constraint.

## 4. Domain declarations (choice G)
Each role was examined against what the operation is, not against what the reference data happen to contain.

| Profile | Event type | Role (own / core) | Cardinality per occurrence | Proposed |
|---|---|---|---|---|
| organisation | `official-act` | `official` / `actor` | one: the profile's act is one official's act in one office (a joint act is several acts) | **unconditional** |
| organisation | `official-act` | `office` / `office` | one: the act is performed in one capacity; authority is judged for that office | **unconditional** |
| organisation | `official-act` | `office-context` / `office-context` | one: (office, context) identifies the position acted in | **unconditional** |
| mechanical | `replacement` | `removed` / `patient` | depends on the operation: a pair of bearings, a gasket set, two seals replaced by one combined seal | **kind-scoped**: `mechanical:one-for-one` |
| mechanical | `replacement` | `fitted` / `fitted` | depends on the operation (as above) | **kind-scoped**: `mechanical:one-for-one` |
| mechanical | `replacement` | `actor`, `instrument`, `location` | several technicians, tools or bays are ordinary | none |
| laboratory | `sampling` | `sampler` / `actor` | several people may take one sample | none |
| laboratory | `sampling` | `sampled` / `origin` | a composite sample comes from several specimens | none |
| laboratory | `sampling` | `product` / `destination` | one sampling may produce several aliquots | none |
| core | `event` and every core role | | never universal (LABS-1.036) | none |

**Replacement, in particular.** A replacement that removed two parts is legitimate, and today it can only be recorded
as two one-for-one accounts of one occurrence (finding 1). Declaring `removed` or `fitted` single-valued for every
replacement would make every such job DISPUTED (X2), so the profile declares them only for occurrences established as
`mechanical:one-for-one`: a source (or the system) states that the job swapped one part for one part, and that claim is
judged like any other. With it, two sources naming different removed parts are DISPUTED (X2c); without it, they stay
a union, each part citing its account (X2b). A finer rule, "for each fitted part, one removed part", was considered and
rejected: one new part can replace two old ones.

## 5. Inventory: every reader that uses event roles
| Reader | Module | Uses roles how | Proposed | Changes? |
|---|---|---|---|---|
| `occurrence` | core | merges the players of every linked description | sections 3.2 and 3.3 | fields added (`accounts`, `roles`); `descriptions`, `participants` unchanged |
| `descriptions` | core | the descriptions with an accepted link | unchanged | no |
| `occurrence_status`, `exists` | core | the occurrence's own existence; each description's account and link | unchanged (a role dispute never decides existence) | no |
| `occurrences_of` | core | the occurrences a description is linked to | unchanged | no |
| `events`, `interval`, `account_attestations` | core | one account at a time | unchanged | no |
| `effects_of`, `causes_of` | core | claims about one description or occurrence | unchanged | no |
| `check_action` | core (agency) | one description's actors | unchanged (per account) | no |
| `actions_of` | core (dynamics) | the events naming an agent, each with its occurrences | unchanged (per account) | no |
| `replacement` | mechanical | one account's removed and fitted parts | unchanged (per account) | no |
| `official_act` | organisation | one account's official, office and context | unchanged (per account); the act's occurrence-level dispute is read from `occurrence` | no |
| sampling reports, `provenance` | laboratory | one account's sampler, specimen and product; constitution claims | unchanged (per account; provenance follows constitution, not event roles) | no |
| `measurement` readers | core (qualities) | a measurement activity's participants | unchanged (core, no declarations) | no |
| schema export (`schema_export`) and its explorer | core tools | lists functional slots | lists event-role constraints separately | added section |

Only `occurrence` changes, and only by added fields. No reader inside the library calls `occurrence`.

## 6. Examples (executed)
From `probes/pre_e_d_examples.py` (a throwaway database; all accounts on day 5). "Current" is `wm.occurrence`;
"Proposed" is the probe's computation of section 3.

| # | Case | Perspective | Current | Proposed |
|---|---|---|---|---|
| X1 | official act: HR names bea, the clerk names cal, both accepted; plus a core event account (actor dan) | system | `actor`: {bea, cal, dan}, no dispute | `official-act:official` **DISPUTED** (bea; cal), each citing its account; `office`, `office-context` established; `event:actor` dan listed apart, never compared |
| X1b | the same | auditor (accepts HR's only) | `actor`: {bea} | official established: bea; the clerk's account listed, not compared |
| X6a | the same, before the clerk's account was accepted | system, earlier `as_of` | `actor`: {bea} | established: bea |
| X6b | plan branching on day 2, stipulating its own account (cal) | system | lists the 3 actual descriptions (links inherited) but only the plan's players | the actual accounts are "none in this world", not compared; established: cal |
| X6c | plan branching on day 6, stipulating its own account (bea) | system | `actor`: {bea, cal, dan} | established: bea (the plan's own); the 2 inherited official-act accounts `overridden` |
| X3 | two accounts name bea and b-smith; `same-as` accepted | system | `actor`: {bea, b-smith} | established: one player, names [b-smith, bea] |
| X3b | the same | qa (accepts both accounts, not the `same-as`) | `actor`: {bea, b-smith} | **DISPUTED** |
| X4a | the clerk's account and link unreviewed | system | `actor`: {bea}; the clerk's description not listed at all | established: bea; the clerk's account listed, not accepted, not compared |
| X4b | the clerk's link denied by an accepted denial (disputed) | system | both descriptions, both players | the link DISPUTED, not compared; established: bea |
| X2 | a two-bearing job: CMMS accounts b1→b3 and b2→b4 of one occurrence | system | `patient`: {b1, b2} | union, no dispute: the constraint does not apply (not one-for-one) |
| X2b | CMMS b1→b3, inspector b2→b3, both accepted; a core work log (patient b3) | system | `patient`: {b1, b2, b3} (removed and the work log's patient merged) | `replacement:removed` {b1, b2}, `event:patient` {b3}, listed apart; no dispute (not one-for-one) |
| X2c | the same, the occurrence established as `mechanical:one-for-one` at its start | system | as X2b | `replacement:removed` **DISPUTED** (b1; b2); `fitted` established (b3) |
| X2d | the same | inspector (has not accepted the classification) | its own account only | the constraint does not apply for this perspective |
| X6d | classified one-for-one only from day 6 | system | as X2b | the constraint does not apply (not established at the start) |
| X7a | the swaps of X2b; classified one-for-one by the CMMS, before the system accepted it | system, earlier `as_of` | union | classification **pending** (canonical record): does not apply |
| X7a2 | the same, after the system accepted it | system | union | classification established: `replacement:removed` **DISPUTED** |
| X7b | classification asserted and denied, both accepted | system | union | classification **disputed** (reason `polarity`): does not apply |
| X7c | classification held from day 1 to day 4 (valid time) | system | union | classification **not holding** (reason `ended`) at day 5: does not apply |
| X7d | plan branching on day 6 (after the swap): inherits the classification and both accounts | system | union | classification established (inherited): **DISPUTED** |
| X7d2 | plan branching on day 6 that stipulates the denial of the inherited classification | system | union | classification **not holding** (reason `denied`; the plan's own claim decides): does not apply |
| X7d3 | plan branching on day 6 that classifies an occurrence the actual world leaves unclassified | system | union | classification established in the plan: **DISPUTED** |
| X7d4 | the same occurrence in the actual world | system | union | classification **unknown** (reason `no_evidence`): does not apply |

In every X2 and X7 case the classification is read from `wm.judgement` (the canonical per-content record of increment
B, the same one every reader uses), and its judgement and reasons are reported with the constraint.
The prototype judges each link and account from its attestations' acceptance at the nearest world level (the polarity
layer of `_judge`), a simplification: the implementation judges links through their canonical records and accounts
as `occurrence_status` does, and the permanent tests and the baseline comparison check that it gives these answers.

## 7. Impact on the reference worlds
`probes/pre_e_d_impact.py` on the reference database rebuilt from merged `main`: every occurrence named by a
`describes` claim, in all 11 worlds, for the system and every attester at the latest knowledge time and for the system
at the snapshot's earlier knowledge time (398 views). The occurrence view is not part of the 106,752-answer snapshot,
so this probe is its baseline.

| | Views |
|---|---:|
| a constrained role judged (`official-act` in `org` and `org-plan-reorg`: one account each) | 12 |
| DISPUTED (a judgement change) | **0** |
| a kind-scoped constraint not applying (no reference occurrence is classified one-for-one) | 12 |
| `participants` merging two differently named roles under one core name (`o-bearing-replacement`: `event:patient` and `replacement:removed`, in `actual` and `plan-rig-control`, four perspectives each) | 8 |
| `descriptions` listing a description with no account in the world (plans branching before the events: `plan-relubricate-only`, `lab-plan-recal`) | 18 |
| a `participants` player taken from an account the perspective has not accepted | 0 |

**Expected changes:** no judgement changes; `occurrence` gains `accounts` and `roles` in all 398 views. The 8 merged
views are the vocabulary issue F resolves (in `roles`; `participants` keeps its answer). The 18 listings are a
separate finding (section 10). DI-2's own example (the inspector's removed bearing-2) stays a union in the reference
worlds, as it should: nothing there says the job was one-for-one, and the inspector's account is not accepted by the
system. The executed examples are what exercise the rule; they become permanent tests.

**Frozen baseline (LABS-1.042, item 6).** `probes/pre_e_d_impact.py --out` froze all 398 views in
`probes/pre_e_d_occurrence_baseline.json.gz`: for each view, the current answer (`descriptions`, `participants`), the
proposed `accounts` and `roles`, the judgement of each constrained role (whether it applies, the classification's
judgement, the role's judgement, the players by identity) and whether the view has a role-presentation change. A
second database rebuilt from the same code reproduces it exactly (`--compare`, output
`probes/pre_e_d_baseline_check.out.txt`: 0 differences in existing fields, judgements or presentation changes).
The implementation must pass the same comparison, with the library's own `occurrence` in place of the prototype:

| Kind of change | Views | Authorised |
|---|---:|---|
| role presentation: `roles` lists `event:patient` and `replacement:removed` apart where `participants` merges them under `patient` (`o-bearing-replacement`; `actual` and `plan-rig-control`; system, cmms, inspector, technician) | 8 | yes (choice F; `participants` itself unchanged) |
| fields added (`accounts`, `roles`) | 398 | yes (ER-5) |
| `descriptions` or `participants` changed | 0 | none may change |
| a judgement (a constrained role DISPUTED, or a link, account or existence judgement) changed | 0 | none may change |

## 8. Storage and installation
### 8.1 Representation
A new additive core module, **`core-0.4-event-roles`** (version 1), file `schema/core/core-0.4-event-roles.tql`:

```
define
attribute event-role-constraint-id, value string;  # "<event type>|<core role>|<kind id, or *>"
attribute constrained-event-type, value string;    # a profile's own event type label, e.g. official-act
attribute constrained-role, value string;          # a core role name, e.g. actor (official-act:official)
attribute constraint-kind, value string;           # a category id; absent: unconditional
attribute declaring-module, value string;          # the module record that declared it, e.g. profile:organisation
entity event-role-constraint, owns event-role-constraint-id @key, owns constrained-event-type @card(1..1),
  owns constrained-role @card(1..1), owns constraint-kind @card(0..1), owns declaring-module @card(1..1);
```

It adds one entity type and five attribute types and changes no existing type, role or foundational type. Reusing
`functional-slot` (with a reserved key role) was rejected: it would overload a proposition constraint with an event
one, slot readers and the schema export would have to filter it out, and it has no place for the kind.

In code: `Profile.event_roles`, a tuple of `EventRole(event_type, role, kind=None)` (role: the core role name), as a
profile already has `slots` and `vocabulary`; `wm.event_role_constraints()` reads every record once per installed
schema (cached, reset by installation and upgrade, as `slots()`); a type's constraints are its ancestors' and its own.

**Validation** (at installation and upgrade; a refusal writes nothing): the event type is one the profile's own
schema declares and is a subtype of `event`; the role is the core role of a role that type relates; the kind, if any,
is in the same profile's vocabulary; no record with the same id but different content exists.

The proposed declarations:
- organisation **0.2**: `EventRole("official-act", "actor")`, `EventRole("official-act", "office")`,
  `EventRole("official-act", "office-context")`;
- mechanical **0.2**: `EventRole("replacement", "patient", "mechanical:one-for-one")`,
  `EventRole("replacement", "fitted", "mechanical:one-for-one")`, and the vocabulary item
  `("category", "mechanical:one-for-one", "one-for-one replacement")`;
- laboratory: unchanged (0.1); the core: none.
The 0.2 schema files are identical in content to 0.1: only data is added.

### 8.2 New databases
`WorldModel.create` installs `core-0.4-event-roles` with the other core modules. `install_profile` writes a profile's
`event_roles` in its existing single schema transaction, with its schema, vocabulary, slots and module record.

### 8.3 Existing databases (migration)
Two explicit operations; nothing is migrated implicitly when a database is opened.

**`wm.upgrade_to_event_roles()`** adds the core module.
- **Preconditions:** the full core is installed (the A0 module and every later core module recorded); otherwise
  refused, nothing written.
- **Idempotence:** if the module record `core-0.4-event-roles` exists, it returns False and writes nothing. If the
  module's types exist without a record (only possible by a manual `define`), it is refused as a conflict (the rule
  `profile_status` applies to profiles).
- **Atomicity and rollback:** one schema transaction defines the module and inserts its module record, and commits
  only after both succeed. Any failure (a TypeDB error, a refused check, an interruption) closes the transaction
  uncommitted: no type, no record. TypeDB 3.14.1 schema transactions are exclusive, so no other write interleaves.

**`wm.upgrade_profile(name)`** brings an installed profile from its previous version to the code's version.
- **Preconditions:** the profile is installed; its installed version is the new version's `upgrades_from` (0.1 for
  0.2); `core-0.4-event-roles` is installed (otherwise refused with the instruction to run
  `upgrade_to_event_roles()` first); the profile's schema in the database (its types, relates, plays, owns and role
  parents, from `schema_snapshot`) equals what its schema files define. Any difference is refused, since a profile's
  schema is never changed in place.
- **What it writes:** the vocabulary items, slots and event-role constraints of the new version that are absent. An
  existing concept with the same id must have the same kind and name (then it is kept); an existing constraint with
  the same id must be identical. Anything else is refused. The module record's version is replaced (0.1 → 0.2) in the
  same transaction. No attestation, acceptance, content or world is written or changed.
- **Idempotence:** if the installed version already equals the code's, it returns False and writes nothing; running
  it again after success is therefore a no-op.
- **Atomicity and rollback:** one schema transaction for every addition and the version record; any failure leaves
  the previous version's declarations, vocabulary and record exactly as they were.
- **No downgrade.** A committed upgrade is not reversed by the library, as an installation is not. Rollback is
  defined for a failure before commit.

### 8.4 Backward compatibility
- **New code, database not upgraded** (no module, or profiles at 0.1): no constraint exists, so no role is exclusive.
  `occurrence` still returns `accounts` and `roles` (each role with `constraint` None and no judgement), and no reader
  fails. `wm.upgrades_available()` reports what each upgrade would add, and writes nothing.
- **Old code (`bf8bb34`) on an upgraded database:** the added entity and attributes are never queried by the old
  code; every existing type, role, slot, concept and content is unchanged, so its answers are unchanged. The old
  code's `install_profile("organisation")` refuses a database that records 0.2, which is the existing rule ("another
  version is refused").
- **Existing answers:** `descriptions` and `participants` of `occurrence`, and every other reader, keep their answers
  (section 7, baseline).
- **Declarations are not claims.** Like functional slots, they carry no valid or knowledge time: once installed, a
  reading at an earlier `as_of` applies them too. They can only add constrained-role judgements, which did not exist
  before; no existing field changes.
- **Schema export.** Format 1's module records are closed (fixed kinds, no other properties), so the exporter moves to
  **format 2** (`wm-schema-export-2`), which adds the record kind `event-role-constraint` (`event_type`, `role`,
  `event_kind`, `declared_by`). Format-1 files remain valid against the format-1 schema; the exporter writes format 2.

## 9. Tests (to be written with the implementation)
- the examples X1 to X7d4, as permanent tests on both query paths;
- a constraint on the core `event`, on another profile's type, on a role the type does not relate, or with a kind
  that is not the profile's, is refused; a subtype inherits its supertype's constraints;
- an unestablished, disputed or pending kind classification never applies a constraint;
- accounts of different types are never compared; `roles` keys are stored labels; `participants` and `descriptions`
  unchanged on every reference view;
- `occurrence_status`, `exists` and every per-account report unchanged where a role is DISPUTED;
- identifiers and query-result order cannot change a judgement (renamed accounts, reversed and shuffled loads);
- the upgrade paths: atomic (a refused or failing upgrade, including a failure injected after the first write, leaves
  no declaration, no vocabulary item and no record change), idempotent (a second run writes nothing), refused on a
  schema difference, a wrong installed version or a missing core module; old code reading an upgraded database
  answers as before;
- the frozen 398-view baseline: `--compare` with the library's `occurrence` gives 0 differences in existing fields
  and judgements, and exactly the 8 authorised presentation changes;
- the reference snapshot gains the `occurrence` reader, so before and after are compared answer by answer.

## 10. Findings registered with this design
- **DI-13 (new, proposed: deferred limitation).** Every event role holds at most one player per account (TypeDB's
  default `@card(0..1)`), a universal per-account cardinality that the domain does not always have (a two-part
  replacement, a team sampling). Recording such an operation needs several accounts of one occurrence, which this
  design handles correctly; allowing several players in one account would change the core and profile schemas and is
  not proposed here.
- **DI-14 (registered, deferred): inherited links without accounts.** Section 13, item 4.
- **Correction to the review's DI-2 impact** (section 1): recorded in the register with the design.

## 11. Not changed
Per-content judgement (increment B), aggregation (increment C), `descriptions`, `participants`, `occurrence_status`,
`exists`, every per-account report and every proposition reader. DI-3 and DI-4 are reassessed after this increment.
DI-7, DI-9, DI-10 and DI-12. The foundational ontology.

## 12. Decisions for approval (exact wording)
**ER-1. Event-role constraints.** An event-role constraint is a pair (event type, core role). It says that, for one
occurrence, the compared accounts (section 2) of that event type or of any of its subtypes name at most one player of
that core role, players being compared under the perspective's identity. Constraints are declared only by profiles,
only on event types the declaring profile's own schema defines; no constraint may be declared on the core `event`
type or on another profile's type, and the core declares none. A subtype has every constraint of its supertypes, and
its own add to them; none replaces or weakens an inherited one.

**ER-2. Kind-scoped constraints.** A constraint may name an event kind (a category of the declaring profile's
vocabulary). It then applies to an occurrence only where the canonical judgement (`wm.judgement`) of
`classified-as(classified: occurrence, class: kind)`, for the world, perspective and knowledge time of the reading, at
the occurrence's start (the earliest start among the accepted accounts with an established link), is ESTABLISHED.
Otherwise (pending, disputed, not holding, not yet effective, unknown, or no accepted account) it does not apply, and
the reason is reported with the role.

**ER-3. Comparison.** For each applicable constraint, the compared accounts are those of the constrained type (or a
subtype) whose `describes` link to the occurrence is established and whose account is accepted. Among them, the
accounts of the nearest world in the variant chain decide; accounts from deeper worlds are listed as `overridden`.
Players are grouped by the perspective's identity at the knowledge time. Accounts of other types, accounts not
accepted, and accounts whose link is not established are listed with their own judgements and never compared.

**ER-4. Judgement of a role.** A role under an applicable constraint is one question and is judged by rule Q: two or
more distinct players make it DISPUTED (status DISPUTED, `support` empty, every player listed with its names, its
accounts, their sources and their support status); exactly one makes it established (status: the core rule over the
union of the deciding account attestations, listed in `support`); none leaves it unjudged. Every other role is a union
with no judgement and no status; each player lists the accounts naming it. Multiplicity alone is never a conflict
(section 3.7). The occurrence's existence (`exists`, `occurrence_status`) is never decided by a role judgement.

**ER-5. The merged view.** `occurrence` adds two fields and changes none: `accounts` (every description linked to the
occurrence by a visible `describes` claim, with its event type, sources, link judgement, account state in
`occurrence_status`'s vocabulary, and world depth) and `roles` (keyed by stored role label, each entry with its own
name, its core role, its players citing their accounts, and for a constrained role the constraint, whether it
applies and why, the judgement, status, support and overridden accounts). `descriptions` and `participants` keep their
current answers.

**ER-6. Profile declarations.** organisation 0.2 declares `official-act` `actor`, `office` and `office-context`,
unconditionally. mechanical 0.2 declares `replacement` `patient` (removed) and `fitted` only for kind
`mechanical:one-for-one`, which it adds to its vocabulary. The laboratory profile and the core declare none.

**ER-7. Storage and migration.** Constraints are stored as data in the additive core module `core-0.4-event-roles`
(entity `event-role-constraint`, section 8.1). New databases receive the module at creation and a profile's
constraints at its installation. Existing databases receive them only through two explicit operations,
`upgrade_to_event_roles()` and `upgrade_profile(name)`, each one schema transaction that commits everything or nothing,
each idempotent (a second run writes nothing), each refused, with nothing written, when its preconditions do not hold
(section 8.3). Upgrades add data only and never change a type, a claim or an acceptance; old code reads an upgraded
database with unchanged answers; a database not upgraded behaves as today with no exclusive role (section 8.4). The
schema export moves to format 2 to carry the new records.

**ER-8. Findings.** DI-13 (one player per role per account, TypeDB's default cardinality) is registered as a deferred
limitation, not changed in this increment. DI-14 (descriptions listed in a variant without an account there) stays
registered as deferred and is not corrected in this increment. The correction to the review's DI-2 impact stays
recorded in the register.

## 13. Clarifications (LABS-1.042)
1. **Exact wording of ER-1 to ER-8, storage and migration:** section 12; representation section 8.1; migration 8.3.
2. **Multiplicity versus conflicting accounts:** confirmed. A role is exclusive only where an applicable, established
   cardinality constraint requires it (section 3.7, ER-1, ER-2, ER-4); otherwise several players are a union. The
   examples and the 398-view baseline show both sides.
3. **Conditional one-for-one constraints through the canonical judgement:** the classification is read from
   `wm.judgement`, the per-content record every reader uses, and the constraint applies only where its judgement is
   ESTABLISHED. Executed (section 6): perspective (X2c established for the system; X2d pending for the inspector),
   knowledge time (X7a pending before acceptance, X7a2 established after), polarity (X7b disputed), valid time (X6d not
   yet effective at the occurrence's start, X7c ended before it), and hypothetical worlds (X7d inherited, X7d2 denied by
   the plan's own stipulation, which decides because it is nearer, X7d3 classified by the plan alone, X7d4 the actual
   world unaffected).
4. **The 18 inherited accounts.** Reproduction: `probes/pre_e_d_inherited_links.py` (output `.out.txt`): an account on
   day 5 whose link `account()` wrote with no start; a plan branching on day 2 lists the description (the link is
   inherited) but has no account (interval None, `occurrence_status` account "none", the occurrence not established
   there); a plan branching on day 6 has both; a link given the event's start is not inherited either. All 18
   reference views are this mechanism: link with no start, account starting at or after the branch point (the
   three views in `lab-plan-recal`, two descriptions, start exactly at the branch instant, which the rule excludes:
   inheritance needs a start strictly before the branch).
   **Classification: expected historical visibility under the current inheritance rule, not incorrect inheritance.**
   The rule is applied as specified: the link is an identity claim with no start and is kept whole; the account is a
   claim about an event after the branch and is excluded. No judgement is taken from the missing account: every reader
   that judges from an account (`interval`, `occurrence_status`, the occurrence checks of `causes_of`, and the proposed
   role judgement) finds none. The gap is in reporting: `descriptions`, `occurrence` (`descriptions`, and
   `participants` by omission) and `process_steps` list such a description without saying that the world holds no
   account of it. Registered as **DI-14** (deferred), with two later remedies, neither chosen here: `account()` could
   write the link from the event's start (new data only), or the readers could mark descriptions without an account in
   the world. Not corrected in increment D; the proposed `accounts` field reports the account as "none in this world",
   which is a report of the existing state, not a correction.
5. **Existing databases (ER-7):** section 8.3 (atomicity, idempotence, refusal and rollback) and 8.4 (backward
   compatibility).
6. **The 398-view baseline:** frozen and reproduced (section 7). The 8 authorised changes are role presentation in the
   new `roles` field; `descriptions`, `participants` and every judgement are unchanged in all 398 views.
