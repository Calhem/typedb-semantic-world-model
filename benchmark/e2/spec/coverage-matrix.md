# Stage E2 coverage matrix and proposed corpus allocation

**LABS-1.064, 28 November 2026. Proposal for review.** No question, fixture or gold exists yet. This plan bounds the
authoring; it is not itself authoring.

**Inputs:**
- scope E2-D1 (as recorded in `docs/stage-e/stage-e2-decisions.md`): about 180 scored questions over six families,
  about 12 identity-conflict questions (X family, reported apart), about 25 gap probes;
- the final reader contracts (`reader-contracts.md`, including §0.11);
- the decision record (`docs/stage-e/stage-e2-semantic-decisions.md`).

**Unchanged rules:**
- A/H/G classification is made before gold is written (E2-D2, rule G-1).
- The E2-D6 thresholds stay as approved:
  - correctness ≥ 95 % per family;
  - supporting recall ≥ 90 % per applicable family;
  - supporting precision 100 %;
  - no fabricated derivations;
  - p95 < 1 s on the selective path, with a 5 s hard budget;
  - no unintended regression.
- E2 is a **development-tier** evaluation (E2-D7). It is not externally independent or sealed.

## 1. Corpus allocation by family

| Family | Scored (A/H) | of which targeted defect coverage | Identity subset | Gap probes (existing gaps) | Probes for new gaps | Approved-unimplemented probes | Fixtures (approx.) |
|---|---:|---:|---:|---:|---:|---:|---:|
| S spatial transformations | 25 | 3 | — | 3 | 0 | 2 | 3 |
| F frames | 35 | 4 | — | 5 | 1 | 0 | 4 |
| M measurements | 35 | 6 | — | 5 | 2 | 0 | 4 |
| C causal relationships | 30 | 6 | — | 4 | 0 | 5 | 3 |
| P process steps | 25 | 3 | — | 5 | 0 | 1 | 3 |
| X multi-step | 30 | 6 | 12 (additional) | 3 | 0 | 1 | 4 + 2 identity |
| **total** | **180 + 12 = 192** | **28 (14.6 %)** | **12** | **25** | **3** | **9** | **about 23** |

**What the columns mean:**
- **Identity subset:** the 12 identity-conflict questions are additional to X's 30, as E2-D1 and F-4 record. They
  count towards X's scores, and they are also reported on their own. Each has its desirability note (DI-17), which is
  never scored.
- **Gap probes:**
  - **Existing gaps:** 25 probes, as approved.
  - **New gaps:** 3 probes, one each for GAP-SPATIAL-9, GAP-MEAS-12 and GAP-MEAS-13 (newly identified, LABS-1.064).
  - **Approved-unimplemented:** 9 probes for the capabilities the decisions approved but no reader provides (the
    `unimplemented` entries of `blocked.json`). They are reported separately from the gap probes. Each accepts
    `absent` and checks that nothing is fabricated in the capability's place.
  - **Total:** 37 class G questions (25 + 3 + 9). The adjustment is **+12** over the approved "about 25", and every
    added probe is named in section 5.
- **Targeted defect coverage:** questions that deliberately exercise a registered DI. Each records it in `targets`.
  - **Cap:** about 15 % of the scored corpus, with no family above 20 %.
  - **Reporting:** these questions stay in their family's scores, and the report also summarises them apart from
    broad competency coverage (`report.py`: `targeted`, `competency`).

## 2. Coverage dimensions × families (scored questions)

Counts are planned minimums per cell. Rows overlap (one question may cover two dimensions), so a column does not sum
to its family total.

| Dimension | S | F | M | C | P | X | Main readers |
|---|---:|---:|---:|---:|---:|---:|---|
| Temporal and epistemic transitions (valid time, `as_of`, supersession, acceptance, NOT_YET_KNOWN) | 4 | 6 | 5 | 6 | 4 | 4 | all; `changes` |
| Spatial transformations and uncertain premises (composition, inversion, disagreeing chains, disputed premises, truncation, convention identity) | 21 | 12 | — | — | — | 4 | `transform_between`, `where`, `poses`, `frame_info` |
| Measurements and calibration (units, uncertainty, comparison, instants, the `t` filter, calibration window, not yet effective) | — | — | 33 | — | — | 5 | `measurements`, `compare_measurements`, `convert`, `calibration_status`, `measurement_calibration` |
| Causal lifting and effect attribution (describes links, occurrence status, accepted change, unique / ambiguous attribution, initiators) | — | — | — | 26 | — | 5 | `causes_of`, `effects_of`, `explain`, `changes` |
| Process and temporal ordering (steps, `before`, windows, instants, several accounts) | — | — | — | 4 | 22 | 3 | `process_steps`, `before`, `interval` |
| Cross-domain composition (multi-step plans with intermediate answers) | — | 4 | 2 | 2 | — | 30 | the plan runner |
| Identity conflicts, perspectives and hypothetical worlds | 4 | 8 | 4 | 4 | 3 | 12 identity + 6 | every reader with `perspective`; variant worlds |

## 3. Case types per family (scored questions)

| Family | Positive (holds, derived, compatible) | Negative (denied, not holding, incompatible) | Disputed | Unknown / not yet known | Refusal (established) | Adversarial (flag; overlaps) |
|---|---:|---:|---:|---:|---:|---:|
| S | 9 | 3 | 6 | 5 | 2 | ≥ 9 |
| F | 12 | 5 | 8 | 8 | 2 | ≥ 12 |
| M | 12 | 7 | 7 | 6 | 3 | ≥ 12 |
| C | 10 | 6 | 6 | 6 | 2 | ≥ 10 |
| P | 9 | 5 | 5 | 5 | 1 | ≥ 9 |
| X (incl. identity) | 15 | 8 | 10 | 7 | 2 | ≥ 14 |
| **total** | **67** | **34** | **42** | **37** | **12** | **≥ 66 (≥ 1/3)** |

- **Adversarial** (as E1) covers conflicts, denials, unknowns, the wrong perspective, superseded claims, variant
  worlds, aliases, boundary instants and truncated searches. At least one third of the corpus is adversarial.
- **Refusals** are expected only where the contract makes them **established**:
  - the existing documented refusals: unknown role, cross-dimension conversion, no single slot;
  - the refusals approved under LABS-1.064: a malformed `holds` content (SD-CORE-1); `value_at` with a half-specified
    role pair (SD-CORE-2); `changes` with t1 > t2 (SD-CAU-8).

  The readers do not implement the LABS-1.064 refusals yet. Those questions are eligible and expected to fail
  (DI-31, DI-27, DI-35).
- **Every question runs on both query paths.** Where the family allows, the corpus also varies `as_of` and the
  perspective.

## 4. Decisions × planned coverage

Every approved decision with an eligible part has scored coverage. The questions on an approved-unimplemented part
are G probes (section 5).

| Decision | Scored questions (planned) | Of which targeted | Notes |
|---|---:|---:|---|
| SD-CORE-1 | 4 (X) | 2 (DI-31) | exact content; an omitted optional role; a missing mandatory role (refusal) |
| SD-CORE-2 | 2 (X) | 1 (DI-27) | refusal of a half-specified call; both roles given |
| SD-CORE-3 | 0 | — | probe only |
| SD-CORE-4 | 0 | — | precondition (not authored) |
| SD-SPA-1 | 3 (F) | 0 | `angle_tolerance` for candidates; chains decided at 1e-9 rad |
| SD-SPA-2 | 3 (S) | 1 (DI-32) | identity by convention (`convention`); NOT_YET_KNOWN; UNKNOWN |
| SD-SPA-3 | 2 (S, F) | 1 (DI-25) | truncation through a disputed edge |
| SD-SPA-4 | 3 (F) | 1 (DI-32) | the label over compared pairs |
| SD-MEA-1 | 4 (M) | 1 (DI-26) | `t` as valid time; a denial covering `t` |
| SD-MEA-2 | 3 (M) | 1 (DI-33) | explicit instants; two at one instant compared |
| SD-MEA-3 | 1 (M) | 0 | the omission of categorical values |
| SD-MEA-4 | 2 (M) | 0 | disjoint valid times |
| SD-MEA-5 | 2 (M) | 0 | not yet effective, with supporting evidence |
| SD-MEA-6 | 3 (M, X) | 2 (DI-34) | an uncertain start window, including a lapse inside it |
| SD-CAU-1 | 5 (C) | 2 (DI-35) | UNKNOWN-adjacent outcomes; delayed effects; ambiguous attribution in `changes` (H-9) |
| SD-CAU-2 | 3 (C, X) | 1 (DI-35) | unaccepted initiators excluded; an initiator overlapping t; no accepted time |
| SD-CAU-3 | 1 (C) | 0 | a content that does not hold |
| SD-CAU-4 | 0 | — | probe only |
| SD-CAU-5 | 5 (P, C) | 1 (DI-36) | the boundary examples of the decision record |
| SD-CAU-6 | 2 (C) | 0 | A → UNKNOWN → A; a gap through DISPUTED |
| SD-CAU-7 | 2 (C) | 1 (DI-35) | timeless claims across `t`; `as_of` still applies |
| SD-CAU-8 | 2 (C) | 0 | t1 > t2 (refusal), t1 = t2 (empty) |
| SD-CAU-9 | 0 | — | probes only |
| SD-CAU-10 | 3 (P) | 1 (DI-36) | certainty across several accounts |
| SD-CAU-11 | 0 | — | precondition; ONT-SC-1 blocked |

**The other targeted questions:**
- DI-24: 2 (F, M);
- DI-25: 2 more (F);
- DI-26: 1 more (M);
- DI-27: 1 more (X);
- DI-28: 3 (C);
- DI-29: 2 (C, X: the eligible components, such as the support of a negative transition side);
- DI-30: 1 (M).

Together with the table above, that makes 28 targeted questions. The split across families in section 1 is planned;
it may move by one question between families when fixtures are specified, within the 15 % / 20 % caps.

**Defects must not dominate the corpus:**
- Diagnostic fixtures and shapes (DX-1 to DX-14) are **not reused**. A targeted question is specified as a situation in
  the approved semantics ("a position stated under an alias, asked by the canonical name"), never as a known output.
- Targeted questions are written by the same spec-only authors, from the contracts (protocol §3).

## 5. Gap and capability probes

| Kind | Probes | Gap or DI |
|---|---:|---|
| Existing gaps: spatial and frames | 8 | GAP-SPATIAL-1, -3/-4, -6, -7, -8; GAP-FRAME-1/-2, -3, -4, -6 (S7, S8, F7 to F10 forms) |
| Existing gaps: measurement | 5 | GAP-MEAS-1, -4, -5, -7, -11 (derivation; DI-7) |
| Existing gaps: causation | 4 | GAP-CAUSE-1/-2, -3, -5, -7 (derivation; DI-7) |
| Existing gaps: process | 5 | GAP-PROC-1/-2, -3, -4, -6, -7 |
| Existing gaps: multi-step | 3 | GAP-MULTI-1, -3, -6 (derivation; DI-7) |
| **New gaps (LABS-1.064)** | 3 | GAP-SPATIAL-9; GAP-MEAS-12; GAP-MEAS-13 |
| **Approved but unimplemented** | 9 | SD-CORE-3 (DI-29); SD-SPA-1 `chain_tolerance` and SD-SPA-2 `basis` (DI-32); SD-CAU-1 `attribution` in `effects_of` (DI-35); SD-CAU-2 `timing` (DI-35) and `alternatives` (DI-29); SD-CAU-4 (DI-29); SD-CAU-9 (DI-28); SD-CAU-10 `usable_accounts` (DI-36) |
| **total** | **37** | |

**How a probe is checked:**
- A probe of an existing or new gap accepts UNKNOWN, NOT_YET_KNOWN or an established refusal, and never a fabricated
  answer or derivation.
- A probe of an approved-but-unimplemented capability also accepts `absent`.

## 6. Readers × families (scored questions, planned)

| Reader | S | F | M | C | P | X |
|---|---:|---:|---:|---:|---:|---:|
| `transform_between` | 25 | 2 | | | | 3 |
| `where` | | 25 | | | | 6 |
| `poses`, `frame_info` | | 8 | | | | 1 |
| `measurements`, `compare_measurements`, `convert` | | | 24 | | | 4 |
| `calibration_status`, `measurement_calibration` | | | 11 | | | 4 |
| `causes_of` | | | | 8 | | 2 |
| `effects_of` | | | | 8 | | 1 |
| `explain` | | | | 6 | | 4 |
| `changes` | | | | 8 | | 2 |
| `process_steps`, `before`, `interval` | | | | | 25 | 3 |
| `holds`, `value_at`, `facts_about`, `occurrence`, `occurrence_status`, `office_holders` (compositions) | | | | | | 14 + 12 identity |

The X column counts reader steps, not questions: an X question has two or more steps.
