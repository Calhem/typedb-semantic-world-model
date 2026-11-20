# Notes: laboratory and identity questions (Stage E1)

Author: an independent question author working from the specification only (benchmark/e1/README.md, TEMPLATES.md,
spec/reader-docs.md, world-ontology-v0.2, core-0.3 README, the pre-e identity, DI-16, decision-gate, increment B,
increment D and multiplicity designs, and the core-0.4 plan). Nothing under src/, tests/, probes/, results or any
`*-output.md` was read; no reader was called. The only command run was the format checker (`evaluation.check --load`).
`pre-e-increment-c-design.md` (rule Q) was not read, because it was outside this author's reading list; questions whose
answer would turn on rule Q's combination details were not written (see below).

## Files
- Fixtures: `fixtures/lab-1.json` (calibration, instrument location, a recalibration plan), `fixtures/lab-2.json`
  (sampling accounts, sample existence and location), `fixtures/id-1.json` (acceptance and polarity of links),
  `fixtures/id-2.json` (chains, cycles, conflict components), `fixtures/id-3.json` (knowledge time and worlds),
  `fixtures/id-4.json` (readers under identity, occurrence aliases, M8/M9, DI-16; organisation profile).
- Questions: `questions/laboratory.jsonl` (LAB-001 to LAB-036), `questions/identity.jsonl` (ID-001 to ID-042).

## Assumptions
1. **Attesters are entities.** Every non-system attester is created as an entity (social-object in laboratory and
   identity fixtures 1-3, organisation in id-4), since TypeDB restricts attesters to physical or social objects (D7).
2. **`accepted_by` on an `account`, `act_in_office` or `take_sample` step** accepts the account's attestation and its
   describes link (README), so those accounts are compared accounts for the listed perspectives.
3. **A source's own account is in its perspective** (own attestations, v0.2 5.3), including its describes link: used for
   the hr and field-team perspective questions (ID-039, LAB-026).
4. **Stipulations in a plan are written with the default attester (system)** and the default stance (stipulates in a
   hypothetical world), and are constitutive for every perspective (E7).
5. **Plan worlds are created after the base records they must inherit** (`knowledge_at` defaults to now at creation);
   plan-deny-child is created after plan-deny's stipulated denial so that it inherits it. plan-early deliberately sets
   `knowledge_at` before the m1~m2 link.
6. **`end` op (lab-1 `end-h1`)** is a superseding restatement by the original attester (metrology); under D14 it changes
   metrology's view at once and the system's view only once the system accepts it.
7. **Event-role player groups** are compared as sets of sets of names; where a group could include identity-class
   members that no compared account names (a reading the specification leaves open), the fixtures avoid it: each
   person name used in an event-role question appears only where every class member is named by a compared account.
8. **Organisation profile version.** The id-4 official-act questions assume organisation 0.3 (multiplicity, MP-4):
   `official-act` `actor` declared `one` unconditionally; no act is classified `organisation:co-signed`, so `one` applies.
9. **Laboratory profile version.** Team sampling assumes laboratory 0.2 (`sampler` open, MP-1); `sampled` and `product`
   stay one per account (decision gate 3.2: `product` deferred, `sampled` single). No laboratory event-role constraint
   exists (ER-6, MP-4), so every sampling role is `union`, including a role with one player.
10. **Union excludes uncompared accounts' players.** MP-2: "the role's players are every player of every compared
    account"; the intern's unreviewed sampling account (dan) is therefore not in the union (LAB-025). ER-4 says each
    player of a union "lists the accounts naming it", which could be read as including unaccepted accounts; MP-2 is
    the later and more specific wording. Recorded as low uncertainty on LAB-025.
11. **ID-5 wording.** The decision gate's recommended wording ("whose own link judgement is DISPUTED or NOT_HOLDING")
    is assumed; only accepted denials and disputes are conflict evidence; pending and rejected denials are not
    (decision gate 1.3). Used in ID-020 (pending denial: merged, no conflict) and ID-007 (rejected denial).
12. **Identity questions carry no valid time** (the identity reader takes none; ID-3). Timelessness is tested through
    `holds(same-as)` at a time and `value_at` through an alias at a valid time before the link was recorded (ID-030).
13. **`exists` before creation** answers holds false (reader-docs exists: "before creation ... false"); its status is
    not scored (LAB-031).
14. **Move evidence.** The location written by `move` has no fixture id of its own; LAB-033 and LAB-035 cite the move
    step `move-12` as required evidence (evidence recall only, not correctness).

## Ambiguities in the specification (recorded, not resolved)
- **A1. Rule Q over certificates in mixed cases.** `calibration_status` combines certificates by rule Q. When one
  certificate's calibration is expired and another's is not yet effective at t (lab-1 balance-b9 at T11), the
  applicability vocabulary does not say whether the answer is `expired` or `not yet effective`. Not written.
- **A2. Established certificate plus a denied or disputed one.** Whether one established certificate and another
  certificate's accepted denial combine to `established` or `disputed` ("rival accepted attestations") is not
  determined by the documents read. Not written. (LAB-019, one established plus one expired, was written: the capable
  table's "an applicable holding is accepted at t" covers it; low uncertainty recorded.)
- **A3. Existence of a sample known only from a sampling account.** `take_sample` claims `initiates existence(sample)`
  but "an account establishes neither its occurrence nor the sample's existence". Whether `exists` infers existence
  by participation (the sample is the product of an accepted event description, a kind of content?) is not
  determined. Not written.
- **A4. Status when nothing is recorded.** v0.2 5.6 gives NOT_YET_KNOWN; the judgement doc gives "UNKNOWN with reason
  no_evidence" for `judgement`. Statuses for value_at with no records (ID-031) and holds of an unlinked pair are not
  scored.
- **A5. Player groups and unnamed class members.** Whether an event-role player group lists only the names the compared
  accounts use or the whole identity class is not stated (X3 shows names that both appear in accounts). Avoided by
  fixture design (assumption 7).
- **A6. Status of a role judgement.** event_role's status is not in the template's expected fields; not scored.
- **A7. ID-5 "conflict" when a disputed link's pair is not otherwise connected.** Section 3.5 requires that established
  links connect them through other names; ID-5's short wording ("a component containing two names whose own link is
  disputed or denied") does not mention that. With the section 3.5 reading, a lone disputed link (I3, ID-004,
  ID-042) is no conflict. Followed section 3.5 and the decision gate's ID-5 row ("while established links connect
  them"); recorded here.
- **A8. same-as without until_superseded.** ID-3 says the link judgement treats each attestation as holding for the
  whole timeline, so a missing end should not matter for identity; not tested (all same-as use until_superseded, as
  instructed), because the write path for such a link is not documented.
- **A9. Correcting a calibration with a denial.** Case I6 (an assertion superseded by its own source's denial) needs a
  `correct` step with polarity false; the fixture format does not document polarity on `correct`. Not written.
- **A10. Sampling occurrence status.** Whether a sampling occurrence happened (occurrence_status) needs an existence
  attestation of the occurrence; not in this author's categories and not written.

## Questions decided NOT to write (answer not determined)
- balance-b9 at T11 (A1); an instrument with one established and one denied certificate (A2); sample-13's existence
  from the sampling account alone (A3); the status (not the values) of value_at for a name with no records (A4);
  hr's view of o-2's official players (A5: hr's group might list i-lowe through hr's own identity although only ivy is
  named in hr's own account; the judgement would be established, but the player group is open);
  conflict reports for a component split across a plan and its base (the design lists it as a test to add, without a
  stated answer); `identity()`'s `derived` marker (TI-1 recommendation, not a decision); a link whose same-as carries a
  start (refused on write, ID-3: not representable in a fixture).
