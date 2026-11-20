# Notes: worlds-perspectives and cross-domain questions

Author: independent question author (model-authored, development tier). Sources read: benchmark/e1/README.md,
TEMPLATES.md, spec/reader-docs.md, world-ontology-v0.2 (sections 4 to 7), core-0.3 README and
supersession-and-endings, core-0.4 increment B, C and D designs, identity design, multiplicity design with decision
gate section 3.2, core-0.4 plan. Nothing under src/, tests/, probes/, results/ or other authors' question files was
read; no reader was called. The only command run was the format checker (`evaluation.check --load`).

Files: `questions/worlds-perspectives.jsonl` (WORLD-001 to WORLD-030), `questions/cross-domain.jsonl` (X-001 to
X-033); fixtures `world-snapshot`, `world-nested`, `world-agents`, `x-reorg`, `x-replace`, `x-sample`, `x-identity`,
`x-move`.

## Assumptions
1. **Inherited claims continue past the branch time.** v0.2 6.2 restricts inherited attestations to "valid times
   before beta (their starts before beta; their endings counted only before beta)". I read this as: an inherited claim
   must start strictly before beta (increment D 13 item 4: "inheritance needs a start strictly before the branch"),
   and an "until superseded" claim keeps holding after beta. Increment C example E1 (a plan branching on day 2, an
   inherited holding judged established on day 5) confirms it. Several questions ask after beta on that basis
   (WORLD-001, 007, 025, X-003, X-033 and others).
2. **A stated end before beta is counted** in the variant (Cal's appointment ending T6 in x-reorg, branch T8; cert-77
   ending T4 in x-sample, branch T6).
3. **Default stance in hypothetical worlds is `stipulates`** (reader-docs `attest`). The fixture writers `grant`,
   `appoint`, `authorise`, `act_in_office` and `calibrate` take no `stance` field (the checker refused it), so their
   steps in hypothetical worlds rely on that default to be stipulations. If those writers do not inherit the default,
   the plan-side answers of WORLD-009 to 012 and X-003, 004, 008, 015, 022 would change; this is the main fixture-level
   risk.
4. **Stipulations count as accepted for every perspective** (E7), whoever the attester is (world-agents plan3,
   planner-1 and planner-2).
5. **Nearest world decides only where it decides at t.** A plan's own claim that is silent at t (starts later) does not
   override an inherited claim at t (increment B 2.2: `overridden` when "a nearer world decides"). No question depends
   on this alone except indirectly (WORLD-012: the plan's stipulation is the only applicable holding).
6. **Classification of an occurrence through `grant`.** The one-for-one classification (`classified-as(o-swap,
   mechanical:one-for-one)`) is written with the `grant` step (holder = the occurrence, concept = the category id).
   I assume this is the content ER-2 reads. The category is the mechanical profile's own vocabulary item and is not
   created by the fixture.
7. **Role names.** `classified-as` uses roles `classified` / `class` (from ER-2's wording); `part-of` uses `part` /
   `whole`; `same-as` uses one multi-player role `same`. The fixtures load without error, which I take as evidence the
   names are valid; they are not stated in the permitted documents.
8. **Same-as written without an interval** (ID-3: identity is timeless; attestations with a start are to be refused).
   Without a start it is "from the start of the world" and so is inherited by a later-branching plan.
9. **Move origin = the attester's own (authored) attestations only**, not those it accepted. Reader-docs: "the place the
   attester's own records hold the thing at"; `move` "ends the attester's location attestations", and an attester can
   only end its own claims (D10, E3). In x-move the system accepts no one else's location record, so X-029 does not
   depend on this choice.
10. **Pending vs not established.** In `capable`, an unreviewed holding is "not established" (increment B 2.4 label
    table). Where a question in a variant involves an inherited claim the perspective has not accepted, I used
    `capable` (whose vocabulary does not separate pending from unknown) rather than `holds`, because v0.2 6.2 says only
    *usable* base attestations are inherited, so whether such a claim is "pending" or invisible ("unknown") in the
    variant is not determined (see ambiguity A2).
11. **Status omitted where not determined.** For `holds` questions answered `unknown` because nothing is inherited
    (WORLD-015, 016, 020) the status (UNKNOWN vs NOT_YET_KNOWN) is left unscored; for WORLD-027 (pending) likewise.
12. `event_role` players are given as identity groups; the order inside a group and of groups is not meant to matter.
13. Office holders are reported by the holder ids the appointments state.

## Ambiguities found (and how each was handled)
- **A1. Endings after the branch time.** "Their endings counted only before beta" does not say what an inherited
  claim becomes when its stated end (or a superseding restatement's end) falls after beta: holding indefinitely, end
  unknown, or something else. No question asks about such a claim after beta (fixtures put ends before the branch or
  ask before it).
- **A2. Unaccepted base claims in a variant.** v0.2 6.2 inherits "the attestations usable in <b, p, min(tau, kappa)>",
  but increment C E1 lists, for the audit perspective, "the inherited holding unreviewed". So it is unclear whether an
  unaccepted base claim is visible in the variant as a pending alternative or not at all. Avoided with `capable`
  (assumption 10); no `holds` question in a variant depends on it.
- **A3. TEMPLATES vs increment B on "begins after t".** TEMPLATES.md lists "begins after t and nothing else decides"
  under `not holding`; increment B 2.4 gives UNKNOWN / not_yet_effective for an accepted assertion beginning after t.
  No `holds` question asks before a claim's start; the not-yet-effective case is asked through `capable` (WORLD-012),
  where the vocabulary is unambiguous.
- **A4. Attested constraints across worlds.** Increment B 2.1 says that "for functional types, a holding in the nearer
  world overrides inherited holdings for the same key". Whether the attested exclusive-office constraint counts as a
  "functional type" here (so a stipulated appointment in a plan would override an inherited one rather than conflict
  with it) is not stated. X-003 is built so that only one appointment is established in the plan, which makes the
  answer the same either way.
- **A5. Locations and functional exclusivity in `holds`.** v0.2 4.4 says "shelf-3?" is false, INFERRED by functional
  exclusivity, once another place is established, while increment B 2.4 has no such case in its judgement table (a
  content with no accepted attestation of its own would be PENDING or UNKNOWN). No `holds` question about a location
  was written; locations are asked with `value_at`.
- **A6. Move origin when the mover accepted others' records** (assumption 9). Not asked.
- **A7. Move in a variant.** Whether "the attester's own records" in a plan include inherited base records, and whether
  nearest-world precedence is applied before checking for several places, is not stated. No move question in a variant.
- **A8. Union players from unaccepted accounts.** Increment D 3.2 step 5 says an unconstrained role's players list
  "its accounts, each with its own account state", which could include players named only by unaccepted accounts. No
  union question has an unaccepted account (all accounts in X-011, 012, 016 are accepted by the asking perspective).
- **A9. Existence of a sample from an accepted sampling account.** `exists` infers existence from "taking part in
  content holding"; whether being the product of an accepted sampling description counts is not stated (the sampling
  report says the account establishes no existence). Not asked.

## Questions not written (the specification does not determine the answer)
- In world-snapshot, a base claim that ends after the plan's branch time, asked in the plan after its end (A1).
- In x-reorg, `office_holders` in the plan with an inherited and a stipulated appointment both established under the
  inherited exclusive-office constraint: `conflict` true, or the inherited one overridden (A4).
- In x-move, a move by the system after the system accepted the robot's record (origin bay-2, or refused because its
  view holds two places) (A6); a move inside the relocation plan (A7); a move by an attester with no location records at
  all (recorded with an empty origin is likely but "at most one origin" does not say so explicitly).
- `holds(located-at(crate, bay-1))` for the system in x-move (not holding by functional exclusivity, pending, or
  disputed) (A5).
- The inspector's own view of job o-swap's removed role (union with one player, or including the unaccepted CMMS
  account's player) (A8).
- `exists(s-1)` after the accepted sampling account (A9).
- A co-signed act established through an `organisation:co-signed` classification (`set` multiplicity): MP-4 is
  recommended for approval at the decision gate, but whether organisation 0.3's category id and declaration are
  installed in this database is not stated in the permitted sources; only the unconditional `one` behaviour is used.
- Holds questions whose `status` would be UNKNOWN vs NOT_YET_KNOWN in a variant where nothing is inherited (left
  unscored, not dropped).

## Adversarial items
WORLD (13 of 30): 002, 003, 005, 007, 013, 015, 016, 018, 020, 025, 027, 029, 030 (inherited claims started after the
branch, acceptance or records after the knowledge limit, a base correction after the knowledge limit, another agent's
acceptances, an agent's own unaccepted claim seen by the system, a missing end, opposite stipulations by unaccepted
planners). Cross-domain (17 of 33): see the `adversarial` flags (scope look-alike `depot`, name look-alike `b-smyth`, unaccepted
denials and certifications, authority versus capability, claimed effects versus parts, a late classification
acceptance, whose location records count).
