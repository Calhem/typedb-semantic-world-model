# Pre-Stage E correction: several participants in one role of one account (DI-13), design

**Status:** design only (LABS-1.046). No code or schema is changed; nothing here is implemented until approved.
Branch `feature/pre-e-corrections-design`, from `main` `bf60c1f`.

**In plain terms.** Today one record of an event (an *account*) can name only one actor, one patient, one official,
and so on: TypeDB refuses a second. So a job done by two technicians, or an act signed by two officials, has to be
split into two records from the same source. That miscounts the sources, and for official acts it creates a false
dispute (two records naming different officials look like disagreement). This design lets selected roles hold several
players **within one account**, and says exactly when several players are legitimate co-participation and when they
are conflicting evidence. It changes nothing for existing data, and nothing for roles that are not opened.

Evidence (throwaway databases or no database; library code unchanged):
- `probes/pre_e_di13_cardinality.py` → `.out.txt`: what TypeDB 3.14.1 does when a role is opened (C1 to C6);
- `probes/pre_e_di13_rule.py` → `.out.txt`: a prototype of the proposed rule on cases M1 to M12 (section 5);
- `probes/pre_e_consolidation.py` (LABS-1.045): the two-technician job and the co-signed act recorded today.

## 1. The limitation, and what TypeDB allows

| Finding | Evidence |
|---|---|
| Every event role is `@card(0..1)` (TypeDB's default; no event role declares another). One description naming two actors, or two officials, is refused with `[CNT5]`. | C1 |
| A role can be opened on a database that already holds data: `define relation event relates actor @card(0..);` is accepted; existing one-player descriptions read as before. | C2 |
| Opening a core role does **not** open a profile role that specialises it: after C2, `official-act:official` (`as actor`) still refuses two players; it must be opened itself, and both levels must be open. | C3, C4 |
| Narrowing a role back is refused while any description uses the wider cardinality, so opening is one-way once used. | C5 |
| Today's rule Q (increment D) already reads one accepted account naming two officials as DISPUTED: it counts distinct players, whichever account they come from. A schema change alone would therefore turn every co-signed act into a dispute. | C6 |

So the design needs two parts: a **schema** part (which roles may hold several players) and a **judgement** part
(what several players mean under a constraint).

## 2. Requirements (LABS-1.046) and how they are met
| Requirement | Met by |
|---|---|
| Additive | New module and attribute; opened roles widen a cardinality, never narrow one; no type, role or attribute removed or renamed; existing constraints keep their meaning (MP-4). |
| Account identity | One description stays one account: several players are role players of the same event relation, written by one `describe_event` call. No new entity stands for the group. |
| Provenance | One account, one attestation, one describes link, one source: exactly as written. |
| Contextual judgement | Which accounts are compared is unchanged (accepted account, established describes link, nearest world, kind classification at the occurrence's start, perspective's identity: ER-1 to ER-5). Only the comparison of their players changes (MP-2). |
| Established exclusivity | A role declared single-valued stays single-valued: an account naming several players of it is DISPUTED (M3, M10). Office exclusivity (an attested constraint on office holding) is a different content and is untouched. |
| Co-participation distinguished from conflict | Rule MP-2 compares each account's **set** of players; section 5. |
| No global weakening | Only the roles listed in MP-1 open, each with a reason; location, origin and every role of a non-event relation stay as they are. |
| Existing-data compatibility and migration | Section 6. |

## 3. Proposed representation

### 3.1 MP-1: which roles open (schema)
A new core module, `core-0.4-event-multiplicity`, opens these core event roles with `@card(0..)`:
- `event:actor`: joint actions (a two-technician job, a team, co-signatories);
- `event:patient`: several things acted on in one operation (a batch, several parts);
- `event:instrument`: several tools in one operation;
- `event:destination`: several products of one operation (aliquots; `sampling:product` specialises it).

Kept at one per account: `event:location` and `event:origin` (one place an account is about; a pooled sample from
several origins is left for a later decision). Profile roles open only in the profile's next version and only where
the operation allows it (each needs its core role open, C3/C4):
- organisation 0.3: `official-act:official` (co-signed acts);
- mechanical 0.3: `replacement:removed`, `replacement:fitted` (multi-part replacement);
- laboratory 0.2: `sampling:sampler` (team sampling), `sampling:product` (several aliquots).
Unopened profile roles (`official-act:office`, `official-act:office-context`, `sampling:sampled`) stay single.

### 3.2 MP-2: what several players mean (judgement)
For one occurrence and one role, take the compared accounts exactly as increment D does. Each compared account gives a
**set** of players, under the perspective's identity (names that are one thing count once: M8; names not established as
one thing count twice: M9). Then, by the declaration that applies to the role (MP-3):
- **no constraint: union.** The role's players are every player of every compared account (unchanged, now with
  several per account): M1, M11, M12.
- **`one` (today's constraint):** established when exactly one player is named across the compared accounts;
  otherwise DISPUTED, with the reason distinguishing *several players in one account* (M3, M10) from *accounts name
  different players* (M4). The second is today's judgement unchanged; the first is the new case, which today cannot be
  written.
- **`set` (new):** the role is co-participation, judged as a whole: established when every compared account states the
  same set of players (M2, M5); DISPUTED when the accounts state different sets, each account's set cited (M6, M7).

An account that states a subset (M6: one account names both co-signatories, another only one) is DISPUTED: the model
never decides that the shorter account is merely incomplete; the reader sees both sets and their sources. Unaccepted
accounts, and accounts whose describes link is not established, are listed and never compared (unchanged).

### 3.3 MP-3: declaring a multiplicity
An event-role constraint (the `event-role-constraint` entity of increment D) gains one optional attribute,
`role-multiplicity`, with the values `one` and `set`. Absent means `one`, so every existing constraint keeps its
meaning. For one (event type, core role), when several declarations apply, a **kind-scoped** declaration whose kind is
established at the occurrence's start wins over an **unconditional** one; two applicable kind-scoped declarations
with different multiplicities are refused when the second is declared (so evaluation never has to choose).

Proposed declarations:
- organisation 0.3: keeps `official-act / actor / unconditional / one` (ER-6) and adds the category
  `organisation:co-signed` with `official-act / actor / kind organisation:co-signed / set` (organisation 0.2 records
  the rule "a joint act is several acts" in `src/worldmodel/organisation.py`; 0.3 keeps it for every act except one
  established as co-signed);
- mechanical 0.3: no new constraint; the ER-6 declarations on `removed` (core role patient) and `fitted`, both scoped
  to `mechanical:one-for-one` and both `one`, stay, so a
  one-for-one replacement naming two removed parts is DISPUTED (M10) and a replacement of another kind is a union
  (M11);
- laboratory 0.2: no constraint (team sampling and aliquots are unions).

### 3.4 MP-4: reading and reporting
`occurrence()` keeps its shape. Each constraint entry in `roles[label]["constraints"]` gains `multiplicity` (`one` or
`set`), and for `set`, the established set or each account's set; `reason` distinguishes the two `one` disputes. Each
account in `accounts` already lists its roles' players as lists (several players need no new field). `participants`
(the Core 0.3 projection) already maps each player to the descriptions naming it. Writers: `account()` and
`describe_event()` already accept a list of players per role; only the database refused it.

## 4. Alternatives considered
- **(b) a "joint" kind that switches the constraint off, one account per participant** (LABS-1.045 option (b)): no
  schema change, but a single source's single record is still stored as several accounts, so account counts and
  provenance stay wrong, and nothing distinguishes "two sources agree" from "one source, two participants".
- **A group particular** (a team entity playing the role, with membership): no schema change, but the participant
  becomes the group, not the people; every reader must resolve membership (itself judged content); and a constraint
  sees one player (the group), so a single-valued role could no longer detect two different officials.
- **Reified participation** (one relation per participant per account): fully general, but every event reader and the
  stored form of all existing descriptions would change; not additive in practice.
- **Opening every event role**: rejected by the requirement not to weaken cardinality globally, and unnecessary.

## 5. Cases (prototype executed: `probes/pre_e_di13_rule.out.txt`)
| Case | Declaration applied | Judgement |
|---|---|---|
| M1 two-technician job, one account names both | none (actor) | union: dan, eve; **one account** (today: two accounts) |
| M2 co-signed act (kind established), one account names both | `set` | established: {bea, cal} (today: cannot be written; as two accounts, DISPUTED) |
| M3 the same account, kind not established | `one` | DISPUTED: several players in one account |
| M4 ordinary act, two accounts, different officials | `one` | DISPUTED: accounts name different players (unchanged) |
| M5 co-signed, two accounts, same two officials | `set` | established: {bea, cal} |
| M6 co-signed, one account names both, another one | `set` | DISPUTED: different sets, both cited |
| M7 co-signed, accounts disagree on the second official | `set` | DISPUTED: different sets |
| M8 ordinary act, one account names bea and b-smith, same-as established | `one` | established: bea (one player under identity) |
| M9 the same, same-as not established | `one` | DISPUTED: several players in one account |
| M10 one-for-one replacement removing two parts | `one` | DISPUTED: several players in one account |
| M11 replacement of another kind removing two parts | none | union |
| M12 team sampling, two accounts | none | union: three samplers |

Interaction with identity (DI-12/15/16 design): sets are taken under the perspective's identity as corrected there, so
M8 and M9 depend on whether the same-as link is *established*, not merely accepted.

## 6. Compatibility and migration
- **New databases:** the module is part of the core module list; profiles 0.3 / 0.2 install with their opened roles.
- **Existing databases:** an explicit `upgrade_to_event_multiplicity()` (as `upgrade_to_event_roles()`, ER-7): one
  schema transaction defining the `@card(0..)` annotations of MP-1 and the `role-multiplicity` attribute, and recording
  the module; idempotent; refused without the event-role module. No data is rewritten: every existing description has
  at most one player per role, which the wider cardinality accepts (C2). Then `upgrade_profile(name)` installs the
  profile's next version (its opened roles and declarations); installing it on a database without the module is
  refused with an actionable error naming the upgrade to run (the LABS-1.045 pattern).
- **One-way:** once a description uses several players, the role cannot be narrowed back (C5). The upgrade is
  therefore documented as irreversible in use; a database can stay on the earlier versions indefinitely.
- **Old code on an upgraded database:** reads several players as lists (roles are lists everywhere), and its rule Q
  counts distinct players, so a co-signed act reads DISPUTED, never wrongly established: old code is conservative.
  It ignores `role-multiplicity`.
- **Reference worlds and baselines:** no existing description can name two players of a role, so the 106,752-answer
  snapshot and the 398-view comparison cannot change on a database that is only upgraded; adding `multiplicity` and
  `reason` to constraint entries changes the 398 views' presentation only (to be counted and listed, as increment D's
  8 presentation changes were).
- **Schema export:** the export already carries each role's annotations from the schema text, so an upgraded
  database's export shows `@card(0..)` on the opened roles with no format change; the module and the new attribute
  appear as for any module.
- **Write path:** unchanged queries; `describe_event` inserts several role players in one statement.

## 7. Acceptance gates for the implementation
1. Cases M1 to M12 as permanent tests through `occurrence()`, both paths, four configurations, twice.
2. Upgrade tests: a database created before the module upgrades in place, keeps every answer, accepts several players
   afterwards; narrowing is refused while used; installing organisation 0.3 without the module gives the actionable
   error; old profile versions keep working.
3. The 106,752-answer snapshot: 0 differences; the 398 views: 0 field and 0 judgement changes, presentation changes
   listed.
4. Performance: no added query per `occurrence()` view (the declarations are already read with the constraints).

## 8. Not changed
The foundational ontology; event types; which accounts are compared; office exclusivity; location and origin roles;
every non-event relation's cardinality.

## 9. Decisions for approval (exact wording)
- **MP-1.** A core module `core-0.4-event-multiplicity` opens `event:actor`, `event:patient`, `event:instrument` and
  `event:destination` to several players per account; profiles open their own specialised roles only in their next
  versions: organisation 0.3 `official`; mechanical 0.3 `removed`, `fitted`; laboratory 0.2 `sampler`, `product`.
- **MP-2.** Several players of a role in compared accounts are judged per account set: a union without a constraint;
  under `one`, DISPUTED with the reason "several players in one account" or "accounts name different players"; under
  `set`, established when every compared account states the same set, otherwise DISPUTED.
- **MP-3.** Event-role constraints gain an optional `role-multiplicity` (`one` when absent); an applicable kind-scoped
  declaration wins over an unconditional one; conflicting kind-scoped declarations are refused when declared.
- **MP-4.** Organisation 0.3 adds the category `organisation:co-signed` and the `set` declaration for its official;
  mechanical and laboratory declare no new constraint.
- **MP-5.** Existing databases upgrade explicitly (`upgrade_to_event_multiplicity()`, then `upgrade_profile`), with an
  actionable error when the order is wrong; the upgrade is documented as one-way once used.
