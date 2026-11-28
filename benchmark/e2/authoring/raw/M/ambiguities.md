# Ambiguities recorded by author M

Each entry gives the passage, the two readings, and what I did (left the question or field out, or kept the
question but did not expect the unfixed part).

## A-1 Identity in `measurements` (slot T-M1)
- **Passage:** contracts §0.2 "readers that take an id judge it with its established same-as group, *where the design
  says so*"; the `measurements` contract (§1) says only "the question is asked by (bearer, quality kind)" and is
  silent on identity.
- **Readings:** (a) `measurements(bearer=ingot-n4)` also lists mm1, recorded against the accepted alias bar-0417;
  (b) it lists only attestations naming ingot-n4 itself.
- **Done:** T-M1 (M-014) asks through `facts_about`, whose contract fixes selection by identity class. No question
  expects whether mm1 appears in `measurements` / `compare_measurements` for ingot-n4: M-015 admits mm1 as supporting
  but does not require it or expect the full entry list; mass comparisons avoid T2-T4.

## A-2 Exact content of a denial of a measured content (slot T-M2)
- **Passage:** fixture-format `measure` writes "has-quality with the SI range ... and its coverage level"; measurements
  §2 `coverage_level` "a function of k (k = 2 ≈ 0.954)" (the formula is cut off). SD-CORE-1: content is type, role
  bindings and parameters.
- **Readings:** a `deny` must repeat the coverage-level parameter exactly; the formula could be erf(k/√2) (0.9544997…)
  or a rounded/tabulated value (0.954 or 0.9545), and the SI unit's id in the `unit` role is not stated.
- **Done:** d1 states unit `metre` (the dimension's unit with factor 1, offset 0), the exact binary bounds 11.75 and
  12.25, and coverage-level erf(2/√2); the fixture description states the intent (deny exactly l16's content). The
  gold of M-030 depends on this match; M-027 does not. No question expects `coverage_level` or `unit` values.

## A-3 Range of a statement written in a non-SI unit (slot T-M6)
- **Passage:** measurements §2 `range` "[v − ku, v + ku] in the dimension's SI unit"; conversion to SI is described
  for `measure` ("conversion to SI on write", D-C-1). A plain `attest` of has-quality carries `lower`/`upper` in its
  own `unit` role (degF).
- **Readings:** the statement's range is reported (a) converted to SI kelvin, or (b) as stated in degF.
- **Done:** M-003 expects kind, acceptance, usable and empty records only, not the range.

## A-4 Role of an accepted denial in a `measurements` answer
- **Passage:** ME §6 "alternative | [usable=false] ... denials"; §0.4 lists "accepted denials" as conflicting;
  SD-MEA-1 "each with its acceptance and role" (role not named).
- **Done:** M-027 neither requires nor forbids d1; it is listed only in `admissible_conflict_evidence`.

## A-5 Role of incomparable measurements in `compare_measurements`
- **Passage:** CM §6 "supporting | measurements[*].attestation, except those in an incompatible pair | always";
  §0.4 table "alternative: ... incomparable ...".
- **Done:** in M-028, M-032, M-033 and M-034, measurements that are only in incomparable pairs are admissible
  supporting evidence but not required.

## A-6 Order of `reference_check.check` outcomes
- **Passage:** MC §2 lists five check values; when more than one condition applies (no certificate for the instrument
  *and* the stated reference matches none; or an instrument whose only certificate claim is unreviewed) the precedence
  is not stated, nor whether an unreviewed calibration claim makes a certificate "name" the instrument.
- **Done:** `reference_check` is not expected for c6 (M-018) or c5 (M-021).

## A-7 `holds` field and calibration status labels
- **Passage:** CS §2 `holds` "True / False / None, as the judgement" (mapping per label not given); status for a
  "not yet effective" answer with empty support is not stated (CS §2 lists only the core rule, DISPUTED, UNKNOWN,
  NOT_YET_KNOWN).
- **Done:** `attested.holds` is never expected; `attested.status` is not expected for not-yet-effective answers
  (M-019).

## A-8 compare_measurements status when records exist but none holds at t
- **Passage:** CM §3 "UNKNOWN when something is held and NOT_YET_KNOWN when nothing is".
- **Readings:** for `t` where no measurement of the quality holds but others are visible at other times, "held" could
  mean "holds at t" (NOT_YET_KNOWN) or "recorded and visible" (UNKNOWN, as §0.3 and v0.2 §5.6 suggest).
- **Done:** I wrote no question on that case. M-008 (everything visible but unaccepted for the perspective) is kept: §0.3
  and v0.2 §5.6 both give UNKNOWN there, and I noted the reading in its `uncertainty`.

## A-9 Superseded entries under `t`
- **Passage:** SD-MEA-1 includes attestations "whose verdict at t is not silent". Whether a superseded attestation
  (mm2, persists from T6) has a non-silent verdict at a t after its correction is not stated.
- **Done:** the M4 questions that look at superseded entries (M-015, M-017) omit `t`. M-016 uses t = T11 but expects
  no full entry list.

## A-10 `measurement_calibration` `attested` when no certificate exists
- **Passage:** MC §2 `attested` "calibration_status answer, or None"; the case for None is not stated.
- **Readings:** None for an instrument with no certificate, or a CS answer "not established" (CS §3: "'Not
  established' with no certificates means no calibration is recorded at all").
- **Done:** M-018 follows CS §3: a CS answer, not established, NOT_YET_KNOWN. I read None as the case with no
  instrument. This is recorded in the question's `uncertainty`.

## A-11 Plan format for `convert`
- **Passage:** question-format "Parameters: world (required)"; CV §1 "There is no world, perspective, as_of or t."
- **Done:** the convert steps (M-010 to M-013) have no world parameter, and the bare float answer is named `value`.
  Each question notes this in `uncertainty`.

## A-12 Interval of a same-as attestation
- **Passage:** same-as is timeless (ID-3, SD-CAU-7); fixture-format says a step with neither `end` nor
  `until_superseded` has an unknown end, and does not say how to write a timeless claim.
- **Done:** sa1 is written with no interval, as a timeless claim. M-014's gold relies on the identity being
  established (accepted, timeless).
