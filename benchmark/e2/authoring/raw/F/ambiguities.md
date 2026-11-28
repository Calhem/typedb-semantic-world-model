# Ambiguities (author F)

Each entry: the passage, the readings, and what I did. Where a question was kept, only the parts the contracts fix are expected.

## A1. A polarity-disputed position statement used by `where` (F-010 T-F2, F-011 T-F3)
- **Passages:** where output `candidates`: "one per position statement that holds for the perspective at t"; WH-8 "Direct candidates carry their own support's status"; WH-9 "DISPUTED on a verified conflict (or a verified DISPUTED candidate)"; WH-21 (a disputed *transform* gives a candidate with no position, DISPUTED); §0.7 "it is not disputed, unless the contract says the rule accepts a disputed premise. The answer must then be DISPUTED"; poses PO-4 / PO-6 (polarity-disputed positions listed in place, "holding or disputed at t").
- **Reading 1 (used):** the disputed statement is still a candidate (as in poses / facts_about, which list disputed contents), marked DISPUTED; the answer is DISPUTED.
- **Reading 2:** a statement that does not *hold* is not a candidate at all; no candidate, records visible, so UNKNOWN (WH-11).
- **What I did:** kept the questions because the slots require them and because §0.7 together with WH-8/WH-9 and the poses/facts_about treatment of disputed contents point to DISPUTED; recorded the residual doubt in each question's `uncertainty`. I expect **only `status`**. Not expected: whether the derived candidate is listed, its range (None or the mapped box), its derivation, or the judgement. The where evidence table has no row saying in which field a polarity-disputed statement and its accepted denial are cited, so all evidence is **admissible only** (assertion and chain transform as supporting, denial as conflicting per §0.4 "accepted denials"); required sets are empty. The disputed position statement is excluded from `admissible_premises` (§0.7).

## A2. Conflicting evidence of a disputed `frame-transform` slot inside `where` (F-012)
- **Passage:** where evidence table: conflicting = `candidates[*].search.inconsistent[*].support` "a candidate DISPUTED because its chains disagree"; TB-9 treats two accepted different transforms for one pair as disputed edges.
- **Readings:** the two rival edge attestations appear in `search.inconsistent` (conflicting), or the candidate is DISPUTED by the slot without `search.inconsistent` entries (nothing cited).
- **What I did:** both rival edges are admissible conflicting evidence, none required. The f-arm statement (candidate without a position) is admissible supporting only, since the supporting row covers "every candidate that has a position".

## A3. Citing the same-as link in an alias answer (F-002, F-009)
- **Passage:** holds §4 "The links relied on are not added to the evidence (ID-D §3.10)"; WH-17 says only that the thing is judged with its established same-as group.
- **Readings:** the link must not be cited (as for holds) or may be cited as what the identity rests on.
- **What I did:** the same-as attestation is admissible but not required, and not forbidden.

## A4. Unknown end in `where` (F-023)
- **Passage:** the rule "An unknown end assumes no continuation (B-D §2.4)" is stated in the holds contract; where WH-14 says only statements that hold at t count.
- **Readings:** applied to positions through the shared judgement (no candidate at a later t), or the statement could be treated as holding until something ends it.
- **What I did:** kept F-023 (UNKNOWN), because the shared position judgement is read through facts_about (PO-1) and v0.2 §5.3 requires that an attestation "certainly holds at t". Recorded in `uncertainty`.

## A5. Basis of a fixture `position` / `relate_frames` step
- **Passage:** fixture-format does not name the basis these steps write; where says direct candidates are "ASSERTED/STIPULATED (direct, by basis)".
- **What I did:** gold uses ASSERTED for actual-world steps: stipulation is allowed only in hypothetical worlds (v0.2 E7), basis inference is reserved for rule-derived attestations (§0.7), and observation and testimony both give ASSERTED (OBSERVED is not produced, §0.3; compare_measurements "observation gives ASSERTED"). Stipulated variant content is written with `attest` and `stance: "stipulates"` (v0.2 §4.4), giving STIPULATED.

## A6. Inherited base content after the branch point (avoided)
- **Passage:** v0.2 §6.2 "restricted to valid times before β (their starts before β; their endings counted only before β)".
- **Readings:** an inherited claim that started before β (a) holds only for valid times before β, or (b) continues after β (only its endings after β are ignored).
- **What I did:** no question depends on it. F-025 s1 is settled by WH-15 (the variant's own stipulation overrides the inherited claim under either reading); F-026 asks at T8 < β; F-024 uses only the variant's own stipulations.

## A7. Is an unreviewed claim a "visible position record" for WH-11? (avoided)
- **Passage:** WH-11 "UNKNOWN when position records about the thing are visible, NOT_YET_KNOWN otherwise".
- **Readings:** an unreviewed (or other-perspective) claim counts as visible (UNKNOWN), or only usable records count (NOT_YET_KNOWN).
- **What I did:** no question has a thing whose only position records are unaccepted. F-006 has an accepted denial (usable), so UNKNOWN is fixed.

## A8. Base position that starts after the branch point, asked in the variant (avoided)
- Same passage as A6; whether such a record is "visible" in the variant for WH-11 (UNKNOWN vs NOT_YET_KNOWN) is not fixed. I wrote no such question; F-027 uses a thing that exists only in the variant and asks the actual world instead (v0.2 C10 fixes NOT_YET_KNOWN).

## A9. A position whose end is an uncertain window containing t (avoided)
- SD-CAU-5 says a window is uncertainty about one instant with both bounds possible, but no where text says whether a possibly-ended statement is a candidate. Not used.

## A10. Unverified (truncated) candidates and the SD-SPA-4 judgement (F-017)
- **Passage:** SD-SPA-4 "`compatible` only when every pair of positioned, verified candidates was compared and overlaps ... `single` / None for one / no candidate".
- **Readings:** with one direct candidate and one statement left incomparable by truncation, the judgement could be `single` (one candidate) or None (not every statement compared).
- **What I did:** F-017 does not expect `judgement`; it expects status UNKNOWN, `verified: false`, the direct candidate and an empty `conflicts`.

## A11. "Verified conflict" in SD-SPA-4 when a candidate is DISPUTED by its chain (F-012)
- **Passage:** SD-SPA-4 "`conflicting` on a verified conflict"; WH-9 distinguishes "a verified conflict (or a verified DISPUTED candidate)"; `conflicts` lists "verified conflicting pairs".
- **Reading used:** a verified conflict is a verified conflicting pair; a DISPUTED candidate without a position forms no pair. Hence `conflicts` is empty and the judgement is None (neither compatible, since one pair was not compared, nor conflicting). This matches the T-F4 slot description. The alternative reading (any verified DISPUTED candidate makes the judgement `conflicting`) is not supported by the field definition of `conflicts`, but it is noted here.

## A12. Key names inside `frame_info` `parents[*]` / `children[*]` (F-034)
- The contract says "parent or child id, `translation`, `rotation`, `status`, `support`" without naming the id key. Gold uses `parent` and `child`; recorded in the question's `uncertainty`.

## A13. `holds` with a particular position (probe G-F-05)
- holds takes no parameters (A2 D-A2-5); passing one would be an execution error, and calling without one asks about different content. The probe therefore has an empty plan (not callable).
