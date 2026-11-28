# LABS-1.063: reader-contract adjudication and E2 harness finalisation (review package)

**27 November 2026.** Branch `feature/e2-reader-contracts`, from `main` 5ded39a. **Stop for review.**

**What did not change:**
- `main` is the E2 semantic baseline and is unchanged.
- No reader correction, E2 question, fixture, calculation sheet, gold answer or ontology change was made.
- DI-7, DI-17 implementation and DI-20 to DI-23 stay deferred.

## 1. Deliverables

| Deliverable | Where |
|---|---|
| Updated reader contracts (approvals, qualifications, amended eligibility) | [benchmark/e2/spec/reader-contracts.md](../../benchmark/e2/spec/reader-contracts.md) §0.1, §0.4–§0.7, §0.10 and parts A–D |
| Complete discrepancy adjudication register (118 items) | [stage-e2-contract-adjudication.md](stage-e2-contract-adjudication.md) §6 |
| Diagnostic reproduction results (14 cases, 17 items) | ibid. §3; [e2-contract-adjudication/diagnostics.json](e2-contract-adjudication/diagnostics.json); `probes/e2_contract_diagnostics.py` |
| Proposed consolidated DI entries (DI-24 to DI-30) | ibid. §4 (not registered) |
| Outstanding semantic decisions (25) | ibid. §5 and the family parts; [benchmark/e2/spec/blocked.json](../../benchmark/e2/spec/blocked.json) |
| Harness validation report | section 5 below |
| Updated E2 readiness and coverage matrix | section 6 below |

**Commits:**

| Commit | Content |
|---|---|
| 9373236 | diagnostic probe and its results |
| 5b696b1 | documentation corrections D-PO-1, D-CH-7, D-TB-4; reader docs regenerated; the src-unchanged check |
| d7b4d41 | harness H-1 to H-8 and the supplement findings |
| (this commit) | contracts, register, review, validation records |

## 2. Approvals applied (contracts §0.10)

- **P-1 to P-5** are approved with the amendments:
  - each role has independent required and admissible sets;
  - recall and precision are reported per role, with E2-D6's supporting thresholds kept;
  - inadmissible conflicting evidence is an explicit failure;
  - conflicting evidence may establish DISPUTED;
  - unattributed evidence blocks a verified precision pass;
  - missing required evidence fails even when precision is undefined;
  - premise admissibility needs visibility, usability and applicability.
- **All 15 reader proposals are approved.** Five carry qualifications, which the contracts now state:
  - **P-VA-1:** mutually exclusive positive rivals stay conflicting.
  - **P-OH-1:** the conflict between established holders is preserved, beside their supporting claims.
  - **P-CM-1:** the shared amendment applies.
  - **P-EF-1:** event-specific scope only.
  - **P-BE-1:** interval-based extraction, with the absence of direct provenance recorded as a limitation.
- **The blanket exclusion is replaced** by the eligibility rules (contracts §0.1; register §1):
  - an established-contract discrepancy stays eligible;
  - unsupported capabilities are G probes;
  - unresolved decisions are blocked;
  - documentation discrepancies don't invalidate a contract.

## 3. Adjudication, diagnostics and decisions (summary)

**Classes:** 38 unresolved decisions, 29 API conventions, 20 documentation, 10 semantic defects, 9 provenance defects,
9 superseded, 3 unsupported.

**E2 eligibility:** 69 eligible, 36 blocked, 3 G probes, 9 n/a, and D-CS-3 split by case.

**All 14 diagnostic cases reproduce,** on both query paths. The worst behaviours, all eligible for scored questions:
- **D-WH-3:** a pose is INFERRED from a disputed premise.
- **D-WH-5, D-PO-3:** `where` and `poses` find nothing when asked by the alias a position was stated under.
- **D-CM-6:** an accepted measurement denial disputes nothing, and with `t` given the measurement vanishes.
- **D-VA-3:** `value_at` reports both holders of an exclusive office as undisputed.
- **D-CO-1, D-CO-3:** causal claims lift through missing or disputed links.

**Proposed DIs:** the 19 semantic and provenance defects consolidate into seven:
- DI-24: identity in readers.
- DI-25: disputed premise.
- DI-26: measurement denials.
- DI-27: value readers on unslotted types, and dispute sides in `value_at`.
- DI-28: causal lifting.
- DI-29: provenance completeness.
- DI-30: measurement reporting.

Plus one proposed gap, GAP-SPATIAL-9. Each would be a later, separately approved increment. Under the amended rules,
E2 questions on these behaviours stay eligible, and a failure is adjudicated under its DI.

**25 semantic decisions,** each with bounded alternatives and a recommendation grounded in the design (none adopts
current behaviour by default), cover the 38 unresolved items. `blocked.json` encodes them for the checker.

## 4. Harness changes (H-1 to H-8, as amended) and the supplement findings

| Change | Implementation |
|---|---|
| H-1 names (P-2) | `evaluation/e2/names.py`: every attestation a fixture recorded gets a deterministic fixture-level name. See the notes after this table. On both test fixtures, every recorded attestation is named. |
| H-2 premises (P-4 as amended) | `score.fabricated`: a premise must name a fixture step and pass three checks: **visibility** (the step's world is in the question world's base lineage), **applicability** (a content type the rule takes: `positioned-in`, `frame-transform` for `frame-transform/v1`) and **usability** (listed in the question's authored `admissible_premises`). Existence alone never admits a premise. |
| H-3 authored sets | `check.py`: a scored question authors `admissible_evidence` whenever a reader cites evidence, `admissible_conflict_evidence` whenever a reader can cite conflicting evidence, and `admissible_premises` for `where` and `transform_between` (each may be []). |
| H-4 / H-5 roles | `evaluation/e2/evidence.py`: one extractor per reader, built from part 6 of its contract with the qualifications. It returns supporting, conflicting, alternative and undetermined ids, each with its answer component. `score.py` scores supporting and conflicting separately: recall, precision, inadmissible and missing per role, plus forbidden, alternative-as-support and unattributed. |
| H-6 refusals | `not-a-unit` removed: a precondition, so an execution error (P-5, P-CV-1). Established refusals: `unknown-role` (holds, explain, value_at), `no-single-slot` (value_at), `cross-dimension` (convert). |
| H-7 report | the report gives recall and precision per role, "no evidence returned" counts, unattributed counts, alternatives presented as support, and the criteria rows (supporting precision is `unverified` while anything is unattributed; inadmissible conflicting evidence = 0). |
| H-8 blocked (amended) | `benchmark/e2/spec/blocked.json` (25 decisions) and `check._blocked_hits`: see the notes after this table. A discrepancy against an established contract is **never** blocked. |

**H-1 names in detail:**
- A step's own claim is `<step>`.
- A measurement's parts are `<step>/activity`, `<step>/kind:<category>`, `<step>/produced` and `<step>/reports`.
- An account's parts are `<step>/kind:<category>` and `<step>/describes`.
- Effects are `<step>/effect:<n>`; `destroy`'s denials are `<step>/denied:<X>`.
- A library restatement is named as the claim it restates (E1 C3), with `<step>/ended:<X>` recorded beside it.
- Anything left unnamed is **unattributed**.

**H-8 in detail:** a question is refused when:
- it declares `depends_on` a decision;
- one of its steps expects a blocked answer path (a prefix, or a field anywhere such as `accepted_change`), optionally
  only with a given value (`judgement: not yet effective`);
- one of its steps passes a blocked parameter (`angle_tolerance`, `limit`, `t` for the measurement readers).

### Supplement findings (LABS-1.063 supplement) and their resolutions

| # | Finding | Resolution | Test |
|---|---|---|---|
| 1 | `_causal_claim` did not classify accepted but non-applicable claims | an accepted claim with `applies` false or null is an **alternative** (P-CO-1); unreviewed or rejected claims too | `test_accepted_but_non_applicable_causal_claim_is_an_alternative` (real `causes_of` output, denied cause occurrence) |
| 2 | `ev_office_holders` dropped the support of established holders in a conflict | each established appointment's claims are **supporting** in their `appointments[i]` component and **conflicting** in the `conflict` component, with the constraint's support (P-OH-1 as qualified) | `test_office_holders_keeps_support_and_the_conflict_between_holders` (real output) |
| 3 | permissive verification defaults in `ev_where` | a candidate counts as verified only with `verified: true`, and a conflict pair only when its detail says `unverified: false`. A candidate with no position or DISPUTED is conflicting. `ev_transform_between` likewise: only an explicitly verified search is authoritative, and a chain step without `disputed: false` is conflicting. | `test_where_never_promotes_unverified_candidates_or_pairs` |
| 4 | cross-role membership and deduplication unclear | every extracted id carries its answer component (`entries`). An id may hold different roles in different components or plan steps, and counts once per role. Alternative and supporting **in the same component** is the failure `alternative-as-support`. | `test_cross_role_membership_and_alternative_as_support` |
| 5 | undetermined evidence could improve a result | the `undetermined` role counts in no role: it neither finds a required attestation nor enters precision. It is reported apart. Not-yet-effective calibration claims are undetermined until SD-MEA-5. | `test_undetermined_evidence_cannot_improve_a_score`, `test_calibration_not_yet_effective_evidence_is_undetermined` |
| 6 | unused `accepted_only` parameter | removed | — |
| 7 | extractors tested only on synthetic dictionaries | 18 readers run on the synthetic fixture, and the disputed cases on a new fixture (`tests/fixtures/e2/evidence-roles.json`). The tests assert the roles by fixture name, that every cited id is a recorded attestation, and the field names, nesting and status vocabulary the extractors read. | `test_extractors_on_real_undisputed_answers` (18 cases), `test_holds_constraint_dispute_and_polarity_dispute`, `test_mutually_exclusive_positive_claims_keep_their_conflict_relationship`, `test_incompatible_measurements_conflict`, `test_listing_dispute_sides`, `test_extractor_field_names_match_real_outputs` |

### The regression tests LABS-1.063 item 16 asks for

| Requirement | Test |
|---|---|
| Missing required evidence cannot pass | `test_missing_required_evidence_cannot_pass` (recall 0, precision undefined, criteria fail / n/a, "no evidence returned") |
| Inadmissible conflicting evidence is detected | `test_inadmissible_conflicting_evidence_is_detected` (failure, criterion row fails, roles scored apart) |
| Mutually exclusive positive claims keep their conflict relationship | `test_mutually_exclusive_positive_claims_keep_their_conflict_relationship` (real `value_at`) |
| Unattributed evidence prevents verified precision | `test_unattributed_evidence_prevents_verified_precision` (and in the existing `test_score_evidence_failures_are_distinct_...`) |
| Invisible, unusable or inadmissible premises are rejected | `test_invisible_unusable_or_inadmissible_premises_are_rejected` |
| Established-contract discrepancies remain eligible | `test_established_contract_discrepancies_remain_eligible`, `test_shipped_blocked_list_matches_fields_anywhere_and_parameters` |
| Unresolved semantic dependencies are refused | `test_unresolved_semantic_dependencies_are_refused`, `test_shipped_blocked_list_matches_fields_anywhere_and_parameters` |

## 5. Harness validation report

The run is from a separate worktree at d7b4d41. Records are in [e2-contract-adjudication/validation/](e2-contract-adjudication/validation/).

| Check | Result |
|---|---|
| Harness tests (`test_zz_e2_harness.py` 51, `test_zz_e2_evidence_roles.py` 38) | 89 pass |
| Full suite (877 + 15 DI-19 + 89 harness = **981**), four configurations | **981 passed in all four** (`suite-summary.txt`); the one warning is the TypeDB driver's own `SyntaxWarning` |
| E1 format check, every fixture loaded | 272 questions, 30 fixtures, 0 problems |
| **E1 original** | 267/272, identical in every scored field to `main` |
| **E1 revised** | 272/272, identical in every scored field to the DI-19 run |
| **Executable reader behaviour unchanged** | `probes/src_semantics_unchanged.py main`: the only `src/` change is one docstring and one comment in `physical.py` (syntax trees with docstrings removed are identical); schema files byte-identical |
| Ontology and identity semantics unchanged | follows from the row above (no executable `src/` or `schema/` change) |
| Reader documentation regenerated and consistent | `reader_docs --check`: up to date (plus the test) |
| Diagnostic probe | 14/14 cases reproduced, both paths agree |

## 6. Updated E2 readiness and coverage matrix

**Column key:**
- **Eligible:** competency questions (design §3) that can be authored now (A/H).
- **Blocked:** what waits for a decision (the checker refuses it).
- **Expected failures:** eligible behaviour the current implementation is expected to fail, adjudicated under a
  proposed DI.
- **G:** gap probes.

| Reader | Eligible | Blocked (decision) | Expected failures (proposed DI) | G |
|---|---|---|---|---|
| `transform_between` | S1–S6 (not trivial chains) | NOT_YET_KNOWN / trivial chains (SD-SPA-2); `limit` truncation through a dispute (SD-SPA-3) | off-chain disputed edge not cited; no alternatives (DI-29) | S7, S8; F9 |
| `where` | F1–F6, X1 | `judgement` label (SD-SPA-4); `angle_tolerance` on chains (SD-SPA-1); `limit` (SD-SPA-3) | disputed premise gives INFERRED (DI-25); alias queries (DI-24) | F7, F8, F10; GAP-SPATIAL-9 (proposed) |
| `poses` | F (listing) | — | alias queries (DI-24); dispute sides not shown (DI-29) | GAP-SPATIAL-8 |
| `frame_info` | F9 one hop, fixture checks | — | dispute sides not shown (DI-29) | GAP-FRAME-1, -4, -5 |
| `measurements` | M1, M4, X1 (without `t`) | `t` (SD-MEA-1); point measurements (SD-MEA-2); categorical values (SD-MEA-3) | aliases (DI-24); denials (DI-26); units of statements (DI-30) | GAP-MEAS-6, -7, -11 |
| `compare_measurements` | M2, M3 (without `t`) | `t` (SD-MEA-1); disjoint valid times (SD-MEA-4) | accepted denials (DI-26) | M7, M8 |
| `convert` | M5 | — | — | M9 |
| `calibration_status` | M6 (A) | not-yet-effective evidence (SD-MEA-5) | — | — |
| `measurement_calibration` | M6, X2 (without `t`) | `t` (SD-MEA-1); uncertain start instant (SD-MEA-6) | misleading reference check (DI-30) | GAP-MEAS-9 |
| `causes_of` | C1, C2, X4 | — | lifting through missing or disputed links; links not cited (DI-28) | GAP-CAUSE-1, -2, -4, -5, -7 |
| `effects_of` | C3 (claims) | `accepted_change` and the judged states (SD-CAU-1); applicability (SD-CAU-9) | — | GAP-CAUSE-3 |
| `explain` | C4, X4 (the state and causal claims) | `initiated_by` membership and timing (SD-CAU-2, -3) | initiating-claim attestations (DI-29) | GAP-CAUSE-1, GAP-MULTI-4, -6 |
| `changes` | C5 | explanations' attestations (SD-CAU-4); gap transitions (SD-CAU-6); boundaries and t1 ≥ t2 (SD-CAU-5, -8, by `depends_on`) | negative side support (DI-29) | GAP-CAUSE-4 |
| `process_steps` | P1, P2, P4, P5, X5, X6 | several accounts per step (SD-CAU-10) | — | GAP-PROC-1 to -7 |
| `before` | P3 | touching windows (SD-CAU-5) | — | GAP-PROC-1, -4 |
| `interval` | P3, X time steps | several accounts (SD-CAU-10) | — | GAP-PROC-4, GAP-MULTI-2 |
| `holds` | X steps | partial role bindings (SD-CORE-1) | — | GAP-SPATIAL-8, GAP-MULTI-6 |
| `value_at` | X3, X steps | `key_role` without `value_role` (SD-CORE-2) | explicit roles on unslotted types; rivals inside support (DI-27) | GAP-MEAS-6, GAP-MULTI-2 |
| `facts_about` | X2 | constraint provenance in listings (SD-CORE-3) | — | GAP-MULTI-6, -8 |
| `occurrence` | X3, X6 (E1 contract, R1) | non-occurrence ids (SD-CORE-4) | — | GAP-MULTI-2, -8 |
| `occurrence_status` | X4, C2 | non-occurrence ids (SD-CORE-4) | — | GAP-MULTI-2, -8 |
| `office_holders` | X6 | — | — | GAP-MULTI-2, -6 |

**Readiness:** every family (S, F, M, C, P, X) has eligible competency questions on established contracts. Authoring
can start for those once the owner approves this package. Blocked aspects wait for the decisions in register §5. The
eligible questions that touch proposed DIs are authored from the contracts, never from the implementation's output or
the diagnostics, and are expected to fail until the DIs are corrected.

## 7. Not done (per LABS-1.063)

- The contracts branch is not merged; main is unchanged.
- No reader correction, and no proposed DI registered.
- No semantic decision adopted.
- No E2 question, fixture, calculation sheet or gold answer.
- No ontology or identity change.
