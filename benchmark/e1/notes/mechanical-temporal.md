# Notes: mechanical and temporal questions (Stage E1)

Author: independent question author (model-authored, development tier). Written from the specification documents
and `spec/reader-docs.md` only; no implementation, test, probe or result file was read and no reader was called.
The only command run was `uv run python -m evaluation.check --load` (format and fixture loading).

Files: fixtures `mech-1` to `mech-4`, `temp-1` to `temp-6`; questions `questions/mechanical.jsonl` (MECH-001 to
MECH-033) and `questions/temporal.jsonl` (TEMP-001 to TEMP-037).

## Assumptions
1. **Role names.** `part-of(part, whole)`, `depends-on(dependent, dependee)`, `located-at(located, place)`,
   `classified-as(classified, class)`, `existence(existent)`: taken from v0.2 3.4, the Core 0.3 README example, the
   increment D wording (`classified-as(classified: occurrence, class: kind)`) and reader-docs (`existence(existent: ...)`).
2. **System attestations need no acceptance.** The system's perspective is its own attestations plus its acceptances
   (v0.2 5.3), so `attester` left at the default `system` counts for the system.
3. **`end` and `correct` step ids** name the new (restating or correcting) attestation, per the README rule that an
   attestation gets the id of its step. Required evidence after an end therefore names the restatement (e.g.
   `loc-1-end`), not the original.
4. **`accepted_by` on `replace_part`** accepts the account's attestation and its describes link (README: "for an
   account: its own attestation, classifications and describes link"), so the link is established for the system.
5. **Status of "not holding".** Left unscored where the content ended (NOT_HOLDING / ended), because neither the
   canonical record nor v0.2 says which status `holds` returns for an ended holding (support status of the ended
   claim, or INFERRED by functional exclusivity as in v0.2 4.4). Scored as ASSERTED only for an accepted denial
   (v0.2 C6: "ASSERTED false").
6. **Pending status** is UNKNOWN (v0.2 5.6: records visible, none decides t for p; unaccepted attestations are
   alternatives, never support, 6.2).
7. **Parts questions** carry empty `required_evidence` (the template returns ids only).
8. **Transitivity.** `holds` on `part-of`/`depends-on` judges one content; transitive parthood exists only in
   `parts()` and nothing else is inferred (D8, reader-docs "Asserted dependencies only ... no transitivity"). So
   `holds(part-of(ring, car))` with no record is unknown / NOT_YET_KNOWN.
9. **A connection is not parthood or dependency** (mechanical module notes), but it is content in which the parts
   take part, so `exists` is INFERRED true from it.
10. **Replacement accounts change nothing by themselves**: reader-docs `replace_part` ("Claims only: nothing here
    establishes ... that the parts changed") and `effects_of` ("a claimed effect is not a state change"). So
    MECH-014/015 expect parts and `holds(part-of)` unchanged after an accepted but unfollowed replacement.
11. **Event-role players** are given as identity groups `[[name], ...]`; with no `same-as` each name is its own group.
12. **Moves.** "the attester's own records" read as attestations made by the attester. Questions are written only
    where the answer is the same under the alternative reading (perspective = own plus accepted), i.e. where the
    attester has accepted nothing about the thing. A superseded (self-corrected) record is not "holding" for the
    attester (D14: the attester's own replacement supersedes at once).
13. **Interval boundaries** are never asked at an exact start or end instant (closed vs half-open is not fixed for
    these fixtures; v0.2 writes `[10:00, 10:10)` in one example and `[start, end]` for windows elsewhere).

## Ambiguities found in the specification
- **A1. "Begins after t": not holding or unknown?** TEMPLATES.md defines `not holding` to include "begins after t and
  nothing else decides", but increment B 2.4 classifies an accepted assertion that begins after t as UNKNOWN with
  reason `not_yet_effective` (and its labels give "not yet effective", never "denied"). These disagree for `holds`.
  I wrote no `holds` question on a claim that begins after t; only `value_at` (UNKNOWN, no values, TEMP-010), which
  both readings give, and `parts`/`dependencies` exclusions.
- **A2. `exists` before creation.** reader-docs says existence attestations give false before creation and after
  destruction (ASSERTED/STIPULATED); the canonical judgement alone would call a claim beginning later
  "not yet effective". MECH-017 follows the specific `exists` documentation (ASSERTED, false) and records this in its
  `uncertainty` field.
- **A3. `exists` of a thing named only in unaccepted or not-yet-started content** (e.g. `roof`, `exhaust` in mech-1):
  UNKNOWN ("records about it are visible") or NOT_YET_KNOWN (nothing about its existence content)? Not determined;
  not written. Only the no-records case (C10 pattern, MECH-019) is asked.
- **A4. `value_at` when the slot's values are disputed.** DISPUTED is determined; whether `values` lists both places
  is not stated. TEMP-012 scores the status only.
- **A5. `value_at` after an ended claim with no successor.** Status could be UNKNOWN (nothing holds) or a supported
  "no value"; not determined. Asked through `holds` instead (TEMP-009, not holding).
- **A6. `holds` of the superseded value after a correction** (parcel at shelf-a once the system accepted the
  correction): the canonical record would give UNKNOWN / unaccepted (the original is superseded), but v0.2 4.4 says
  the old place is "false, INFERRED by functional exclusivity". Not written.
- **A7. Event-role player list with an unaccepted account.** ER-5 says a role's players cite their accounts and that
  `accounts` lists every linked account, accepted or not; whether the template's `players` for an established role
  includes the unaccepted account's player is not stated. MECH-025 scores judgement and multiplicity only.
- **A8. Dispute reason when both cases apply.** TEMPLATES says the two `one` reasons are "joined by `; `" but not in
  which order; no question has both at once.
- **A9. Move evidence ids and the moved-to location.** reader-docs says `move` records the movement "with the new
  location as its effect", without saying whether a `located-at` attestation (and with what end basis) is written,
  or which id it would carry. So no `value_at` question is asked after a fixture move (fixtures contain no `move`
  steps); location over time is built from `attest`/`end`/`correct`.
- **A10. A move to a list of destinations.** "one destination" (MP-1 restriction, reader-docs `move`) suggests a
  refusal, but how a writer reports a list for a single-valued destination (refusal vs a different error) is not
  specified. Not written.
- **A11. Move origin from a claim with a missing end, or from another attester's accepted claim.** Whether a begun
  claim with an unknown end "holds the thing just before" the move, and whether "own records" include accepted ones
  (v0.2 6.2 calls a perspective's accepted attestations part of its "own" usable set), are not determined. Not written.
- **A12. Joint-kind ids for `connect`** are not listed in the specification; connections were written without a joint
  kind.

## Questions deliberately not written
- `holds` for a claim beginning after t (A1); `exists` for things named only in unusable content (A3);
  `value_at` of a superseded or ended place (A5, A6); `value_at` after a recorded move (A9); move to two
  destinations (A10); move origins in the A11 cases; questions at exact interval boundaries (assumption 13);
  connection content via `holds` (the profile's role names for the connection are not in the specification);
  hypothetical-world inheritance of mechanical state (outside these categories' brief and better covered elsewhere).
