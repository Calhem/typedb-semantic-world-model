# Family C: ambiguities recorded by the author

Each entry gives the passage, the readings, and what I did (left the question or field out, or designed around it).
All passages are from `pack/reader-contracts-author-edition.md` (cited as "contracts") unless named otherwise.

## A-01. Default basis of fixture attestations (status values ASSERTED / STIPULATED / INFERRED)
- **Passage:** v0.2 §5.3 "testimony → ASSERTED, inference → INFERRED, stipulation → STIPULATED"; fixture-format.md
  gives `attest`, `claim_cause`, `claim_effect` no basis parameter and states no default basis.
- **Readings:** (a) default basis testimony, so the system's claims are ASSERTED; (b) some other default.
- **Action:** no question expects a supported status value (ASSERTED etc.). Statuses are expected only where they do
  not depend on basis: DISPUTED (C-005, C-015, C-016, C-020, C-023). Otherwise `holds`, `judgement` or `claim` are
  expected.

## A-02. `causes_of` `[i].effect` for a lifted entry
- **Passage:** causes_of §2: "`effect` is the queried id or the target it was lifted from".
- **Readings:** for a lifted entry, `effect` is (a) the queried occurrence (o-trip) or (b) the description the claim
  names (a-trip).
- **Action:** `effect` is never expected on a lifted entry (C-001, C-003). `cause` is expected (the claim's players).

## A-03. `occurrences` and `applies` for description-level claims
- **Passage:** causes_of §2: `occurrences` {id: status}; `applies` "False if an involved occurrence is denied; null if
  one is disputed; True otherwise".
- **Readings:** which occurrences are "involved" in a description-level claim (none; the occurrences its descriptions
  describe; only when lifted) is not stated.
- **Action:** `occurrences` is expected only on occurrence-level claims (C-006, C-007, C-008, C-009, C-010). `applies`
  is expected on description-level claims only where every possible reading gives the same value: every occurrence
  that could count as involved has accepted existence, so no reading yields False or null (C-001, C-002). C-002's
  `applies: true` for a-rumour (which describes nothing) relies on the literal "True otherwise"; noted in its
  `uncertainty`.

## A-04. Lifting through a polarity-disputed describes link
- **Passage:** causes_of §4: "Only describes links the perspective accepts lift a claim (SB 'Lifting'). What counts
  as an accepted link is" (the sentence is cut off in the author edition).
- **Readings:** with an accepted assertion and an accepted denial of one link, (a) the link is "accepted" (its
  assertion is accepted) and lifts, or (b) the link content is disputed and does not lift.
- **Action:** not asked. Slot T-C2 (C-003) is built so that both readings agree: the system first **rejects** the
  matcher's link dl-spike and then accepts the auditor's denial, so no accepted assertion remains.

## A-05. Slot T-C3: "with the links required as evidence"
- **Passage:** causes_of §6 cites only `[i].attestations` (the causal claim's own attestations); §7 "Lifting is a
  read-time link, not a derivation"; no field carries the describes-link attestations.
- **Readings:** (a) the describes links are supporting evidence of a lifted answer and must be cited by causes_of;
  (b) causes_of cites only the claim's attestations.
- **Action:** I did not require causes_of to cite the links. C-001 instead requires them through two explicit `holds`
  steps on the `describes` contents, whose `support` is fixed (holds §6). This satisfies "links required as evidence"
  with a contract-fixed source.

## A-06. Occurrence-level claims and description-level questions ("downward" lifting)
- **Passage:** causes_of §3: "a description-level claim answers an occurrence-level question only through describes
  links ...". Nothing says whether an occurrence-level claim answers a question about a description of that occurrence.
- **Action:** the fixture avoids it: no occurrence-level causal claim names o-trip, so `causes_of(a-trip)` and
  `causes_of(a-trip-2)` (C-002, C-004) are unaffected by either reading.

## A-07. `effects_of` `state.before` / `state.after` instants
- **Passage:** effects_of §2 "judged ... before and after the event"; §9 GAP-MULTI-2 (the instants).
- **Action:** `state.before` is never expected. `state.after.status` is expected only in C-016, where every instant from
  the event's end onwards gives DISPUTED. Otherwise only `state.accepted_change` (fixed by SD-CAU-1) is expected.

## A-08. Role of the assertion on a polarity-disputed state side (effects_of, explain)
- **Passage:** explain §6 "conflicting | `holds.conflicts`, `holds.constraint_support[].support` | `holds.status =
  DISPUTED`" and effects_of §6 "conflicting (state) | `state.<side>.conflicts` ... | that side is DISPUTED", but in a
  polarity dispute `conflicts` is empty and `support` holds both sides; holds §6 / P-HO-1 split `support` by polarity
  (assertions supporting, accepted denials conflicting); changes §6 calls a DISPUTED side's `support` conflicting; and
  effects_of's "supporting (state) | before.support, after.support" does not mention DISPUTED.
- **Readings:** the system's assertion att-heat on the DISPUTED side is (a) supporting (P-HO-1) or (b) conflicting.
- **Action:** C-016 and C-020 list att-heat as admissible in **both** roles and required in neither. The accepted denial
  deny-heat-aud is required as conflicting (common 0.4 names accepted denials as conflicting under every reading).

## A-09. Requiring the initiating claims' attestations in explain
- **Passage:** explain §2 "`initiated_by[i]` initiating-claim attestations | absent | required [E] by SB B0"; §6
  "Initiating-claim provenance: adjudicated as a provenance defect. A question may require the initiating claims'
  attestations (the established B0 requirement) and stays" (cut off), followed by three cases.
- **Readings:** (a) questions require the initiating claim steps (ce-*) as supporting evidence; (b) they do not.
- **Action:** C-017 to C-020 require them, as the passage permits and SB B0 establishes. The three cut-off cases
  (unaccepted initiator listed; initiator with a missing account or not ended by t; a cause's `lifted` flag inside
  explain) are decided as follows. SD-CAU-2 (§0.11, overriding) settles the first (unaccepted claims are never
  explanations: C-017) and the second for an uncertain or later start (C-018). I did not ask about initiators with no
  accepted account, or about `lifted` inside explain.

## A-10. `changes` with t1 ≥ t2
- **Passage:** changes §1 "t1 ≥ t2 is unspecified"; §8 "Refusals: none documented"; §0.11 SD-CAU-8 "changes with
  t1 > t2 is refused; t1 = t2 has no transitions".
- **Action:** SD-CAU-8 is established and overrides (§0.11): C-029 expects a refusal, C-030 no transitions.

## A-11. Slot versus content tracks in `changes`
- **Passage:** changes §2: track {kind `slot`, ...} or {kind `content`, ...}. Which types are tracked by slot, and
  whether a slot type also gets content tracks, is not stated.
- **Action:** every changes question uses `classified-as` with no declared functional constraint (no profile
  constraint applies), so only content tracks can arise. `track` itself is never expected, and each subject has
  exactly one content.

## A-12. UNKNOWN to value as a "beginning" for attribution
- **Passage:** changes §3 Q-B1.4 ("a claim that fits several activations on the whole timeline is ambiguous").
  Whether a judgement transition out of UNKNOWN counts as an activation (the content "began") is not stated.
- **Action:** the fixtures are designed so that no attribution depends on it. Every initiates claim whose attribution
  is expected concerns a content first established by an accepted denial (tank-9, gate-3). For crane-1 and crane-2
  (UNKNOWN to True at T2) only terminates claims are asked. Where an UNKNOWN to False change exists (gate-3 at T1), it
  precedes the terminating event's start and is excluded by B-time whichever reading applies.

## A-13. Whether an activation excluded by B-time counts when judging "fits"
- **Passage:** changes §3: "one temporal constraint applies: an effect cannot precede its event's start (B-time)" and
  "a claim that fits several activations".
- **Action:** in every attribution question, each relevant activation is either consistent with the event or
  irrelevant under both readings. The only `ambiguous` cases (gate-3 at T4 and T9 for e-unlock, which starts at T3) have
  both activations consistent.

## A-14. Existence of an occurrence outside its existence interval
- **Passage:** occurrence_status §3: `exists()` is "false before the existence starts or after it ends". Whether that
  maps to `denied` or `not established` is not stated.
- **Action:** every occurrence-status judgement (direct, or inside causes_of) is asked at a t inside [T1, T30), the
  declared existence interval.

## A-15. Representation of time windows in expected answers
- **Passage:** changes §2 `window` "(time, time)"; explain / interval `start`, `end` "Window {earliest, latest}". The
  pack fixes no serialisation.
- **Action:** `changes` windows are written as two-item lists of fixture time strings, e.g. `["T6", "T9"]`, in the
  fixture's own notation. explain `start`/`end` are never expected.

## A-16. `causes_of` `level: mixed`
- **Passage:** causes_of §2 `level` values `description`, `occurrence`, `mixed`; "[E] for description and occurrence".
- **Action:** no claim mixes a description and an occurrence, so `mixed` is never needed.

## A-17. Attesters as entities
- **Passage:** fixture-format.md: attesters are named in `attester`; v0.2 E2 requires an agent capacity; kinds such
  as `person` need the organisation profile.
- **Action:** each fixture installs the organisation profile and declares every non-system attester as a `person`
  entity. No office, employment or constraint is written, so the profile adds nothing to any judged content.
