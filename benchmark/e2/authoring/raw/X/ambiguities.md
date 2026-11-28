# Ambiguities recorded by author X

Each entry: the passage, the two readings, and what I did (left the field or question out, or designed around it).

## A-1. Status of a holds question whose exact content is unrecorded but a context-bearing variant is (T-X1, X-023)
- Passage: §0.3 "UNKNOWN: something relevant is recorded, but no answer follows. NOT_YET_KNOWN: nothing relevant is recorded"; SD-CORE-1 "Omitted optional roles identify the content without them".
- Reading 1: the contextual classification gr-arno is a different content, so nothing relevant is recorded: NOT_YET_KNOWN.
- Reading 2: a record about the same classified and class is "relevant": UNKNOWN.
- Done: X-023 s3 expects only `holds: null` and `support: []` (fixed either way); `status` is not expected.

## A-2. `replace_part` parameters and role labels (X3)
- Passage: fixture-format "connect, replace_part, take_sample, employ, authorise | as E1"; the E1 definition is not in the pack, nor is the order of its `<step>/effect:<n>` parts or its role labels beyond "removed" and "fitted" in the occurrence multiplicity note.
- Readings: unknown parameter names and stored labels, so any question on a `replace_part` step would guess them.
- Done: X3 questions use a core `account` (kind part-fitting) whose `patient` is the fitted part, and read it through `occurrence` (the reader serving the event_role step). No question uses `replace_part`.

## A-3. Support of a calibration judged established throughout an uncertain window (T-X5, X-006)
- Passage: SD-MEA-6 in full; calibration_status `support` "the deciding claims".
- Reading 1: support is the union of every certificate claim established somewhere in the window (cal-1 and cal-2).
- Reading 2: support is taken at some bound or only for one sub-window.
- Done: X-006 expects `judgement: established` and `holds: true` (fixed: established at every instant of [T14, T16], with the handover at T15 under half-open intervals), not `support` or `status`; both certificate claims are admissible (and required through facts_about steps that cite them as their own entries' support).
- Also not written: a window containing a gap between certificates. SD-MEA-6 says the answer is then "not established" and the judgements found are kept, but the value of `judgement` (for example "not established" or "expired") is not fixed, so no such question was written.

## A-4. Resolved judgement of the `official` role of an official act (X6, X-019 to X-022, X-024, X-026)
- Passage: occurrence §3 rule Q (one / set / no applicable constraint: union); MP §2 lists official among roles allowing several players per account. Whether the organisation profile declares a constraint on the official role is not stated.
- Readings: `resolved.judgement` "established" (a constraint applies) or "union" (none applies).
- Done: only `roles.official.resolved.players` is expected (one compared account gives one player either way).

## A-5. occurrence_status after the occurrence's existence interval has ended
- Passage: occurrence_status §3 "exists() gives ASSERTED or STIPULATED (true, or false before the existence starts or after it ends)"; the status vocabulary accepted / denied / disputed / not established.
- Readings: an ended existence asked about later maps to "denied", or to "not established".
- Done: every occurrence_status step is asked at an instant inside the declared existence interval.

## A-6. Initiating-claim attestations in `explain` (X4)
- Passage: explain §6 "Initiating-claim provenance: adjudicated as a provenance defect. A question may require the initiating claims' attestations (the established B0 requirement) and stays" (sentence truncated in the author edition).
- Readings: the claim_effect attestations are required supporting evidence, or optional.
- Done: the claim_effect steps (eff-fit-1, eff-flush, eff-drain) are admissible, never required.

## A-7. Inheritance of timeless effect and causal claims into a variant
- Passage: v0.2 §6.2 inherited attestations are "restricted to valid times before β (their starts before β ...)"; SD-CAU-7 timeless claims are judged independently of valid time.
- Readings: a timeless claim is always inherited, or never (it has no start before β).
- Done: no `explain`, `effects_of` or `causes_of` step is asked in a variant world (X-015 asks `explain` in the actual world and `occurrence_status` in the variant).

## A-8. Event intervals that start before a branch and end after it
- Passage: v0.2 §6.2 "their endings counted only before β".
- Readings: the inherited account's end is unknown in the variant, or reported as recorded.
- Done: X5 questions expect step membership (`occurrence`, `judgement`, `support`, `status`), never `start` or `end`, in variant worlds.

## A-9. Per-candidate status inside a DISPUTED `where` answer (X-029)
- Passage: where `candidates[*].status` "ASSERTED/STIPULATED (direct, by basis), INFERRED (derived), DISPUTED (chain disagrees)"; WH-8 "Direct candidates carry their own support's status".
- Readings: in a position conflict each candidate keeps its own status, or is marked DISPUTED.
- Done: X-029 expects the top-level status, judgement, ranges, position_support and conflict kind only.

## A-10. `office_holders.exclusive.support`
- Passage: office_holders §2 `exclusive` "the constraint's own holds, status and support at t"; its evidence table gives no role for `exclusive.support` (only `conflict.constraint.support`, conflicting in a conflict).
- Readings: the exclusivity declaration is supporting evidence of an unconflicted answer, or not cited.
- Done: in X-019 and X-022 the declarations are neither admissible nor forbidden supporting evidence; in X-020 ex-ql is conflicting only.

## A-11. Representation of a certificate's issuer (X2)
- Passage: fixture-format `certificate` takes `name` and `reference` only, with no attestation; no content type names an issuer.
- Readings: issuance could be any of several content types.
- Done (a fixture design choice, not a semantic reading): each certificate's issuer is an explicit `depends-on(dependent certificate, dependee issuer, kind issued-by)` claim, read through `facts_about`. The questions say so.

## A-12. Form of single-player role values in `facts_about` entries
- Passage: facts_about §2 `roles` "roles canonical under identity".
- Readings: a role maps to one id, or to a list of ids.
- Done: expected as one id (`[type=depends-on].roles.dependee`), recorded in each question's `uncertainty`. A verifier who reads it as a list should treat this as a format, not a semantic, difference.
