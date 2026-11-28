# LABS-1.064 review package: semantic decision closure and E2 authoring readiness

**28 November 2026.** Branch `feature/e2-reader-contracts`, not merged. `main` is at `5ded39a` and remains the
executable E2 baseline. **Stopped for review**, as instructed: before merging, before authoring E2 questions, before
building E2 fixtures, before generating gold, and before implementing any deferred correction.

## 1. Deliverables

| # | Deliverable | Where |
|---|---|---|
| 1 | Final semantic decision record | [stage-e2-semantic-decisions.md](stage-e2-semantic-decisions.md) |
| 2 | Updated deferred-issue register: DI-24 to DI-36; GAP-SPATIAL-9, GAP-MEAS-12, GAP-MEAS-13 | [deferred-issues.md](../core-0.4/deferred-issues.md); [e2-capability-inventory.md](stage-e-entry/e2-capability-inventory.md) |
| 3 | Final reader contracts | [reader-contracts.md](../../benchmark/e2/spec/reader-contracts.md) §0.11 and the per-reader "Decided" notes |
| 4 | Remaining unresolved decisions | decision record §5: ONT-SC-1 (self-causation), an ontology question, blocked |
| 5 | Harness validation report | section 4 below; records in [e2-semantic-decisions/validation/](e2-semantic-decisions/validation/) |
| 6 | E2 coverage matrix | [coverage-matrix.md](../../benchmark/e2/spec/coverage-matrix.md) §2–§6 |
| 7 | Authoring and isolation protocol | [authoring-protocol.md](../../benchmark/e2/spec/authoring-protocol.md) |
| 8 | Proposed corpus allocation by family | [coverage-matrix.md](../../benchmark/e2/spec/coverage-matrix.md) §1 |
| — | Updated adjudication register | [stage-e2-contract-adjudication.md](stage-e2-contract-adjudication.md) (header, §1, §2, §4, §5 and the 38 decided rows) |
| — | Reconciled blocked list | [blocked.json](../../benchmark/e2/spec/blocked.json) |

**Commits** (each pushed and verified with `git ls-remote`):

| Commit | Content |
|---|---|
| `a898223` | decision record; DI-24 to DI-36 registered; gaps; adjudication register |
| `32e20ff` | harness: the decisions applied (checker, scorer, extractor, templates, report); 17 tests; a new self-test fixture |
| `c507306` | final contracts (§0.11); coverage matrix and corpus allocation; authoring protocol; status of the E2 README and decisions record |
| this commit | validation records and this review package |

## 2. Decisions and their consequences

All 25 recommendations are adopted. The owner's binding qualifications are recorded verbatim in substance for these
decisions:
- SD-CORE-1, SD-SPA-2, SD-MEA-2, SD-MEA-6;
- SD-CAU-1, SD-CAU-5, SD-CAU-7, SD-CAU-10.

Where a qualification and a register recommendation differ, the qualification wins.

The rule for E2 questions (decision record §1) answers two of the items:
- **Item 18:** a question is eligible wherever the reader reports the field the decision governs, **even when the
  current implementation is expected to fail it**.
- **Item 19:** where the decision requires a field, parameter or representation that no reader provides, the question
  is a G probe under the DI that would add it. Approving the semantics does not make the capability exist.

| Consequence | Decisions |
|---|---|
| eligible; current behaviour conforms | SD-MEA-3 (the omission), SD-MEA-4, SD-CAU-3, SD-CAU-6 |
| eligible; correction deferred | SD-CORE-1, SD-CORE-2, SD-SPA-1 (parameter), SD-SPA-2, SD-SPA-3, SD-SPA-4, SD-MEA-1, SD-MEA-2, SD-MEA-6, SD-CAU-1, SD-CAU-2 (inclusion), SD-CAU-5, SD-CAU-7, SD-CAU-8, SD-CAU-10 (certainty) |
| eligible through a harness change only | SD-MEA-5, SD-CORE-2 (template parameters), SD-SPA-2 (the `convention` marker) |
| G: approved but unimplemented | SD-CORE-3; SD-SPA-1 and SD-SPA-2 (reporting fields); SD-CAU-1 (attribution in `effects_of`); SD-CAU-2 (`timing`, `alternatives`); SD-CAU-4; SD-CAU-9; SD-CAU-10 (every account) |
| G: gap | GAP-SPATIAL-8 (SD-CORE-1, parameters); the newly identified GAP-MEAS-12 (SD-MEA-3) and GAP-MEAS-13 (SD-MEA-4) |
| precondition | SD-CORE-4; SD-CAU-11 (writer validations) |
| still open | ONT-SC-1: whether `causes` is irreflexive (from SD-CAU-11). This is left for an ontology decision, and the ontology is unchanged. |

**Two findings from applying the decisions:**
- **SD-MEA-2 has a representation consequence.** The writer stores `measure(start=s)` and `measure(start=s, end=s)`
  identically (`end = end or start`). No reader can therefore tell an explicit instant from an empty interval. DI-33
  records the representation and migration this needs.
  - **E2 fixture convention:** an explicit instant is `measure` with a start and no end; `end` is never written equal
    to `start`.
  - **SD-CAU-5:** the same holds for instantaneous accounts in `before` (DI-36).
- **SD-SPA-2 exposed a harness blind spot.** For a frame to itself, the reader names `frame-transform/v1` with an empty
  chain (status None). The template's derivation extractor skipped empty chains, so this premise-less derivation went
  unscored. It is now extracted and scored as fabricated (section 3).

## 3. Harness changes (items 17, 20 and 21)

No executable production reader changed. Every change is in `evaluation/e2/` or in `blocked.json`.

| Change | Where | Decision |
|---|---|---|
| The LABS-1.063 blocks are lifted where the contract is now unambiguous. `blocked` keeps ONT-SC-1 only. `unimplemented` lists 13 reader and path entries under 8 decisions; scored questions may not expect those paths, and probes may | `blocked.json`, `check.py` | items 17, 19 |
| `convention: frame-identity`: the question must have empty evidence and premise sets, and a frame to itself must be marked. Any derivation presented for such a question is fabricated | `check.py`, `score.py` | SD-SPA-2 |
| The named rule of an identity answer is extracted as a derivation (with no premises), not skipped | `readers.py` `dv_transform` | SD-SPA-2 |
| H-9: a `changes` step that inspects an explanation must fix its `attribution` | `check.py` | SD-CAU-1 |
| The accepted claim of a not-yet-effective certificate is supporting evidence; no extractor now uses the `undetermined` role | `evidence.py` | SD-MEA-5 |
| An occurrence reader given an id that the fixture makes something else is refused as a precondition | `check.py` | SD-CORE-4 |
| `value_at` passes `key_role` and `value_role` | `readers.py` | SD-CORE-2 |
| A probe may accept `absent` (the capability is missing, and nothing is fabricated in its place) | `check.py`, `score.py` | item 19 |
| `targets` on a question; targeted and competency questions summarised apart | `check.py`, `score.py`, `report.py` | item 26 |

**The item 21 verifications** (`tests/test_zz_e2_decisions.py`). Each runs against real reader outputs on the
synthetic self-test fixture `tests/fixtures/e2/decisions.json`, plus hand-made answers for the cases no reader
produces:

| Check | Tests | Result |
|---|---|---|
| (a) Mathematical conventions do not generate fabricated derivations | `test_a_frame_to_itself_must_be_marked_as_a_convention`, `test_the_current_identity_answer_is_a_fabricated_derivation`, `test_a_convention_answer_without_derivation_passes_and_any_derivation_fails`, `test_an_evidence_derived_inference_keeps_its_premises` | holds. The current A → A answer is scored `fabricated-derivation`; a conforming answer passes; evidence-derived inference is unaffected |
| (b) Accepted future calibration claims can support a not-yet-effective judgement | `test_accepted_future_calibration_claim_supports_not_yet_effective` (and the unit test in `test_zz_e2_evidence_roles.py`) | holds, with the real `calibration_status` output (its `support` field is empty) |
| (c) Ambiguous causal attribution cannot be scored as unique causation | `test_changes_reports_the_ambiguous_attribution_…`, `test_checker_requires_the_attribution_…`, `test_a_unique_attribution_claim_fails_…`, `test_effects_of_accepted_change_is_eligible_and_its_attribution_is_a_probe` | holds. A real claim fitting two activations is `ambiguous`; "unique" gold fails; questions cannot skip the attribution |
| (d) Missing evidence cannot be reconstructed from fixture expectations | `test_missing_evidence_is_not_reconstructed_from_fixture_expectations` | holds. A fixture step that is required and even named in the expected answer, but not cited by the answer, is `missing-evidence` (recall 0.667, or 0 with nothing cited, with precision undefined) |
| (e) Evidence roles remain component-specific | `test_roles_are_recorded_per_component_on_a_real_answer` (and the LABS-1.063 cross-role test) | holds. Each appointment's claim supports its appointment and conflicts in the office conflict |
| (f) Unverified evidence cannot produce a verified precision pass | `test_unverified_candidate_evidence_cannot_pass_precision`, `test_unattributed_evidence_keeps_precision_unverified` | holds. Truncated-chain support is an alternative (precision n/a, never a pass); unattributed evidence keeps precision `unverified` |

## 4. Validation (items 29 to 31)

Run from a separate worktree at `32e20ff`, the last code commit. The later commits change documents only.

| Check | Result |
|---|---|
| Harness tests (E2) | 106 pass (`test_zz_e2_harness.py` 51, `test_zz_e2_evidence_roles.py` 38, `test_zz_e2_decisions.py` 17) |
| Full suite, 4 configurations (selective / full load × profiles off / on) | **998 passed in each** (981 at LABS-1.063, plus 17) |
| E1 original | 267/272; identical to the main reference run (`differ: []`) |
| E1 revised | 272/272; identical to the DI-19 reference run (`differ: []`). The committed `results-revised/` file predates DI-19 and differs on ORG-011 only (evidence), as recorded since LABS-1.061 |
| E1 format check (every fixture loaded) | 272 questions, 30 fixtures, 0 problems |
| Executable production readers, schema, ontology vs `main` | **no executable or schema difference** (AST comparison). The only `src/` difference is the LABS-1.063 docstring and comment change in `physical.py`. No change under `schema/` or `docs/architecture/` |
| Reader documentation | up to date |
| Mac sleep during the run | none (power log checked); keep-awake held |

## 5. E2 readiness

| Item | State |
|---|---|
| Reader contracts | final (§0.11), at review before merging |
| Semantic decisions | 25 of 25 approved; 1 ontology question open (ONT-SC-1, blocked) |
| Harness | applies every decision; 998 × 4 pass |
| Corpus allocation and coverage | proposed: 180 + 12 identity scored, 28 targeted (14.6 %), 37 G (25 existing gaps, 3 new gaps, 9 approved-unimplemented) |
| Authoring protocol | proposed: an author pack with implementation material removed and a leak check, spec-only derivation, recomputed numbers, explicit evidence sets per role, and a freeze before any fixture load. Development-tier, not externally independent or sealed |
| Questions, fixtures, calculation sheets, gold | **not started** |
| DI-24 to DI-36 corrections | **not implemented** |

## 6. Not done, as instructed

- The contracts branch is not merged.
- No E2 questions, fixtures or gold have been written.
- No reader correction has been made, and DI-24 to DI-36 are not implemented.
- The ontology is unchanged.
- DI-7, DI-17, DI-20 to DI-23 and the external sealed evaluation stay deferred.

## 7. For the owner

1. Approve or amend the authoring and isolation protocol, and the corpus allocation, including the transparent
   +12 G adjustment.
2. Decide whether ONT-SC-1 (self-causation) needs an ontology decision before E2, or stays blocked throughout E2. The
   recommendation is that it stays blocked: no E2 question depends on it.
3. Approve merging `feature/e2-reader-contracts` into `main`. The merge adds no executable reader change.
