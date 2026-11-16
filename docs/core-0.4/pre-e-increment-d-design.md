# Pre-Stage E correction, increment D: event-role exclusivity (DI-2), design

**Status: design for architectural review (LABS-1.041), not implemented.** Branch `feature/pre-e-d-event-roles`, from
`main` at `bf8bb34` (increment C merged). No library code has changed. Stage E has not begun. The foundational
ontology is unchanged; the one schema addition proposed (section 8) is an additive storage module, as functional slots
were (A0.3).

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
  start (the earliest start among the accepted accounts with an established link, whatever their type). Not established, disputed, pending or unknown: the
  constraint does not apply, and the role is a union (LABS-1.036: an unestablished constraint never makes compatible
  accounts disputed). This is how a role whose cardinality depends on the operation is constrained: the operation is
  said to be of that kind, by a claim that is itself judged;
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

## 8. Storage and installation
- **Storage (proposed: a dedicated additive module).** A new core module, `core-0.4-event-roles`, adds one entity,
  `event-role-constraint` (event type, core role, optional kind), stored as data like `functional-slot`. Reusing
  `functional-slot` with a reserved key role was considered: it needs no schema change but overloads a proposition
  constraint with an event one, so slot readers and the schema export would have to filter it, and it has no place
  for the kind. The new module changes no existing type and no foundational type.
- **Profiles.** A profile gains `event_roles` (as it has `slots` and `vocabulary`), validated at installation (own
  event types only; the role must be one the type relates; the kind must be the profile's own vocabulary) and
  written in the same atomic installation transaction.
- **Existing databases.** Profiles are never replaced in place, so the declarations come with new profile versions:
  organisation 0.2 (three unconditional constraints) and mechanical 0.2 (two kind-scoped constraints and the
  vocabulary item `mechanical:one-for-one`), with no schema change. An atomic, data-only `upgrade_profile` installs
  the new version's additions where the installed version is the previous one and the schema files are identical;
  anything else is refused. The new core module is added by an atomic `upgrade_to_event_roles` (as `upgrade_to_a0`).
  New databases get both at creation.

## 9. Tests (to be written with the implementation)
- the examples X1 to X6d, as permanent tests on both query paths;
- a constraint on the core `event`, on another profile's type, on a role the type does not relate, or with a kind
  that is not the profile's, is refused; a subtype inherits its supertype's constraints;
- an unestablished, disputed or pending kind classification never applies a constraint;
- accounts of different types are never compared; `roles` keys are stored labels; `participants` and `descriptions`
  unchanged on every reference view;
- `occurrence_status`, `exists` and every per-account report unchanged where a role is DISPUTED;
- identifiers and query-result order cannot change a judgement (renamed accounts, reversed and shuffled loads);
- the upgrade paths are atomic (a refused or failing upgrade leaves no declaration and no module record);
- the reference snapshot gains the `occurrence` reader, so before and after are compared answer by answer.

## 10. Findings registered with this design
- **DI-13 (new, proposed: deferred limitation).** Every event role holds at most one player per account (TypeDB's
  default `@card(0..1)`), a universal per-account cardinality that the domain does not always have (a two-part
  replacement, a team sampling). Recording such an operation needs several accounts of one occurrence, which this
  design handles correctly; allowing several players in one account would change the core and profile schemas and is
  not proposed here.
- **Inherited links without accounts.** In a plan branching before an occurrence, `descriptions()` lists the actual
  world's descriptions (their links are inherited) although their accounts are not part of the plan. Nothing is judged
  from them (`occurrence_status` reports the account as "none"); the new `accounts` field makes it visible. Proposed:
  documented, no change in this increment.
- **Correction to the review's DI-2 impact** (section 1): recorded in the register with the design.

## 11. Not changed
Per-content judgement (increment B), aggregation (increment C), `descriptions`, `participants`, `occurrence_status`,
`exists`, every per-account report and every proposition reader. DI-3 and DI-4 are reassessed after this increment.
DI-7, DI-9, DI-10 and DI-12. The foundational ontology.

## 12. Decisions for approval
| # | Decision | Recommended |
|---|---|---|
| ER-1 | Event-role constraints: (event type, core role), per occurrence, declared by profiles on their own event types only, inherited by subtypes; none on core `event` | approve |
| ER-2 | Kind-scoped constraints: apply only where `classified-as(occurrence, kind)` is established for the context at the occurrence's start | approve |
| ER-3 | Comparison: only compared accounts (established link, accepted account, constrained type); nearest world decides, deeper ones `overridden`; players under the perspective's identity | approve |
| ER-4 | Judgement of a constrained role by rule Q (DISPUTED, or established with status over the deciding accounts and `support`); unconstrained roles a union | approve |
| ER-5 | `occurrence` adds `accounts` and `roles` (keyed by stored role label, core role alongside); `descriptions` and `participants` unchanged | approve |
| ER-6 | Profile declarations: official-act `official`, `office`, `office-context` unconditional; replacement `removed` and `fitted` only as `mechanical:one-for-one`; none for sampling or core | approve |
| ER-7 | Storage and installation: additive module `core-0.4-event-roles`; profile `event_roles`; organisation 0.2 and mechanical 0.2 with atomic data-only upgrades | approve |
| ER-8 | Register DI-13 (one player per role per account) as a deferred limitation; document inherited links without accounts; record the correction to the review's DI-2 impact | approve |
