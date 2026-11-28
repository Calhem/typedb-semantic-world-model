# Stage E2 semantic decisions (final record)

**LABS-1.064, 28 November 2026.** Branch `feature/e2-reader-contracts`. The owner accepted LABS-1.063 and approved all
25 semantic decisions in the adjudication register ([stage-e2-contract-adjudication.md](stage-e2-contract-adjudication.md)
§5), subject to the binding qualifications below. This record is authoritative for the E2 reader contracts
([benchmark/e2/spec/reader-contracts.md](../../benchmark/e2/spec/reader-contracts.md) §0.11). Where the register's
recommendation text and a qualification here differ, **the qualification wins**.

**What this record does not do:**
- It corrects no reader. Every implementation consequence is registered as deferred work (§4; the register is
  [docs/core-0.4/deferred-issues.md](../core-0.4/deferred-issues.md), DI-24 to DI-36).
- It changes no ontology text. One question stays open as an ontology decision (§5).
- It authors no E2 question, fixture or gold.

`main` at `5ded39a` remains the executable E2 baseline.

## 1. How a decision reaches E2 questions

An approved decision fixes what the contract says. Whether a question on it is scored depends on whether the
implementation **provides the capability** the question needs, not on whether it currently answers correctly
(LABS-1.064 items 18 and 19):

| Consequence | Meaning | E2 treatment |
|---|---|---|
| **eligible** | the reader already takes the question and reports the field, parameter or refusal the decision governs | A/H scored. A question is never excluded because the current implementation is expected to fail it. |
| **G (approved, unimplemented)** | the decision requires an output field, parameter, representation or reader that does not exist yet | a G probe under the DI that would implement it, never scored for conformance. Approval of the semantics does not establish the capability. `blocked.json` lists these paths; the checker refuses them in scored questions. |
| **G (gap)** | the decision places the capability outside the current model | a G probe under the gap id |
| **precondition** | the decision makes the input an execution precondition (P-5) | not authored; the checker refuses such inputs where it can detect them |
| **blocked** | still undecided | refused by the checker (§5) |

**Convention-derived and evidence-derived results** (SD-SPA-2) are distinguished in both the contract and the harness:
a convention-derived answer presents no derivation and cites no supporting attestation; an evidence-derived inference
presents a derivation with at least one admissible premise (common §0.7). A question marks a convention-derived answer
with `"convention"`; the harness then treats any presented derivation, and any supporting citation, as a failure
(`evaluation/e2/check.py`, `score.py`).

## 2. The decisions

Each entry gives the adopted alternative, the binding statement as it enters the contract, its consequence for E2,
and the deferred work it creates. "Current behaviour" is from the register; it never decided an alternative.

### Core and organisation

**SD-CORE-1. What `holds()` asks (D-HO-1, D-HO-2).** Adopted: **(a) exact content**, qualified.
- `holds()` addresses **exact content identity**: the type, the role bindings given, and the parameters (v0.2 §4.2).
- **Omitted optional roles** identify the content **without** those roles: `classified-as(classified, class)` is the
  content with no context, not "any content with these players".
- **Missing mandatory roles** make the question **malformed**: a refusal, never an answer. Mandatory and optional roles
  are those of the content type's definition in the ontology documentation.
- **Parameterised content** remains subject to GAP-SPATIAL-8 (`holds` cannot single out one position).
- **No load-order-dependent selection** is permitted: under exact identity one content is addressed, so no record is
  "picked".
- *E2:* exact-content questions, including omitted optional roles and the malformed-question refusal, are
  **eligible** (the current subset match is expected to fail some). Parameterised-content questions are **G**
  (GAP-SPATIAL-8). *Deferred work:* **DI-31**.

**SD-CORE-2. `value_at` with `key_role` but no `value_role` (D-VA-2).** Adopted: **(a) refuse as malformed.**
- *E2:* **eligible**. The harness template now passes `key_role` and `value_role` (it called `value_at` without them
  before). A half-specified question expects `{"refused": true}`; the reader currently answers UNKNOWN. *Deferred
  work:* **DI-27**.

**SD-CORE-3. Listings and the constraint behind a constraint dispute (D-FA-1).** Adopted: **(a)**, an additive
`constraint_support` per `facts_about` entry, from the same canonical record.
- *E2:* the field does not exist: **G (approved, unimplemented)** for `*constraint_support` in `facts_about`.
  `facts_about` questions stay eligible on every other field and do not require the constraint's attestation.
  *Deferred work:* **DI-29**.

**SD-CORE-4. Occurrence readers given a non-occurrence id (D-OC-3, D-OS-1).** Adopted: **(b)**, an execution
precondition under P-5 for E2.
- *E2:* **precondition**. No question passes a non-occurrence to `occurrence` or `occurrence_status`; the checker refuses
  an `occurrence` parameter that the fixture does not make an occurrence. A documented refusal (alternative (a)) is
  not adopted; it would need its own decision. *Deferred work:* none.

### Spatial

**SD-SPA-1. Which angular tolerance decides frame-chain agreement (D-TB-1, D-WH-1).** Adopted: **(b)**, with D-A2-7
confirmed in that wording.
- Chain agreement always uses **1e-9 rad** (transforms are exact values with no stated uncertainty, GAP-SPATIAL-1).
  The question's `angle_tolerance` is the accuracy of the compared **position claims** only.
- The answer should state the chain tolerance it used.
- *E2:* `where(angle_tolerance=)` is **eligible** (candidate comparison only). Reporting the chain tolerance is **G
  (approved, unimplemented)**. *Deferred work:* **DI-32**.

**SD-SPA-2. Trivial and empty chains (D-TB-2).** Adopted: **(b)**, qualified.
- `source == target` requires a **valid, visible frame**: the id names a frame (otherwise a P-5 precondition), and a
  record involving the frame is visible to the question's world, perspective and `as_of`. If none is visible, the
  answer is NOT_YET_KNOWN.
- With a visible frame, the answer is the identity transform, reported as a **declared mathematical convention**
  (Plan 9.6 composition identity), status INFERRED in the sense of v0.2 §5.6 ("a declared query-time rule concludes
  it").
- **No derivation is presented and no supporting attestation is cited.** A premise-less derivation, or one with
  invented premises, is fabricated (common §0.7 rule 2).
- No chain between distinct frames: NOT_YET_KNOWN when no `frame-transform` record involving `source` or `target` is
  visible at `as_of`; UNKNOWN otherwise.
- *E2:* status, transform and the absence of derivation and evidence are **eligible**; the question carries
  `"convention": "frame-identity"`. The current reader presents a premise-less derivation and never answers
  NOT_YET_KNOWN, so it is expected to fail these. A field naming the convention basis is **G (approved,
  unimplemented)**. *Deferred work:* **DI-32**.

**SD-SPA-3. A truncated search whose reached chain contains a disputed transform (D-TB-8).** Adopted: **(c) DISPUTED,
no transform.**
- *E2:* **eligible** (`limit` parameter questions). *Deferred work:* **DI-25** (a derivation never rests on a disputed
  premise or edge).

**SD-SPA-4. The `where` judgement label (D-WH-2).** Adopted: **(a)**: `compatible` only when every pair of
positioned, verified candidates was compared and overlaps; `conflicting` on a verified conflict; otherwise no label;
`single` and None as conventions for one or no candidate.
- *E2:* **eligible**. *Deferred work:* **DI-32**.

### Measurement and calibration

**SD-MEA-1. What `t` means in the measurement readers (D-ME-1, D-MC-1).** Adopted: **(b) valid time, denials kept.**
- Every attestation whose verdict at `t` is not silent is included, assertions and denials alike, each with its
  acceptance and role. For `measurement_calibration`, `t` selects measurements only; calibration is judged at the
  activity's start (as SD-MEA-6 qualifies it).
- *E2:* **eligible**. *Deferred work:* **DI-26**.

**SD-MEA-2. A measurement over an instant (D-ME-6).** Adopted: **(a)**, limited to the reported content of a
measurement, qualified.
- An **explicit instantaneous measurement** holds at its observation instant.
- Two observations at the same instant may be compared, subject to the remaining comparability conditions
  (quality, conditions, coverage, calibration as stated in the contract).
- Empty half-open intervals are **not** redefined globally: an attestation with an empty interval `[s, s)` that is not
  an explicit instantaneous measurement still holds at no instant.
- Instantaneous observation, empty interval and persistent content (`persists`) stay **three distinct cases**.
- **Representation implication (recorded for later):** the writer stores `measure(start=s)` and
  `measure(start=s, end=s)` identically (`end = end or start`), as `[s, s)`, so the stored record cannot tell an
  explicit instant from an empty interval. A correction needs an explicit instant marker on the reported content and
  a migration that marks existing measurement contents written without an end. Other attestations are not migrated.
- *E2:* **eligible** for measurements written as explicit instants: `measure` with `start`, no `end`, and no
  `persists` (the fixture convention; fixtures never write `end` equal to `start`). *Deferred work:* **DI-33**.

**SD-MEA-3. Categorical qualities (D-ME-9).** Adopted: **(b) out of scope** for `measurements` and
`compare_measurements`, stated in the contract. Categorical values are read through `holds` and `facts_about`.
- *E2:* that `measurements` omits categorical values is **eligible** (current behaviour conforms). A
  categorical-measurement question is **G (gap)** under the newly identified **GAP-MEAS-12**.

**SD-MEA-4. Disjoint valid times (D-CM-3).** Adopted: **(a) now**: every quantity is treated as possibly changing, so
measurements whose valid times do not overlap are incomparable. **(b)**, a declared constant quantity, is a later
extension.
- *E2:* **eligible** (current behaviour conforms). A question needing a declared constant quantity is **G (gap)** under
  the newly identified **GAP-MEAS-13**.

**SD-MEA-5. Evidence for a not-yet-effective calibration (D-CS-3).** Adopted: **(b) supporting.**
- The accepted future calibration claim decides the judgement "not yet effective", so it is **supporting** evidence.
  The empty `support` field means "no status support", not "no evidence".
- *E2:* **eligible**. The harness extractor now places accepted claims of a not-yet-effective certificate in the
  supporting role (`evaluation/e2/evidence.py`); no reader changes. *Deferred work:* none.

**SD-MEA-6. Calibration when the activity's start is uncertain (D-MC-3).** Adopted: **(b) the whole window**,
qualified.
- Calibration is **established** only when it is established **throughout the entire possible activity-start
  window**. Agreement at the earliest and latest bounds is insufficient.
- Every relevant **internal** validity and judgement transition inside the window is considered: a calibration that
  lapses and is renewed inside the window is not established throughout it.
- **No arbitrary instant is selected.**
- Where continuous establishment cannot be demonstrated, the uncertainty and any dispute are **preserved**: the answer
  reports the judgements found across the window, and is not "established".
- With an exact start, the window is one instant, so exact-start questions are unaffected.
- *E2:* **eligible** (the current earliest-bound rule is expected to fail uncertain-window questions). This is the
  GAP-MULTI-2 answer for this composition. *Deferred work:* **DI-34**.

### Causation, change and process

**SD-CAU-1. What an accepted state change is in `effects_of` (D-EF-1, D-EF-2).** Adopted: **(c) through
`changes`**, qualified.
- `effects_of` uses the **canonical world-state transition semantics of `changes()`**: `accepted_change` is true only
  when a world-state transition of the outcome, in the claimed direction, falls at or after the event's start.
- **UNKNOWN and DISPUTED transitions are not accepted physical changes.**
- **Delayed effects** count, without inventing temporal precision: the transition's window is reported as
  `changes` reports it.
- **Unique and ambiguous attribution** are preserved.
- Three things are kept apart: an **established outcome change** (the transition), an **accepted effect claim** (the
  claim's judgement), and an **established causal attribution** (the transition attributed uniquely to the claim).
  None implies another.
- **An accepted claim associated with an ambiguous transition does not establish unique causation.**
- *E2:* `accepted_change` is **eligible**. Reporting the attribution inside `effects_of` is **G (approved,
  unimplemented)**. In `changes`, a question that expects explanation entries must also fix each entry's
  `attribution`, so an answer that drops or misstates ambiguity cannot pass (checker rule H-9). *Deferred work:*
  **DI-35**.

**SD-CAU-2. Which initiating events `explain` lists (D-EX-1, D-EX-2, D-EX-3).** Adopted: **(c)**: accepted
`initiates` claims only in `initiated_by`, under B-time (an event is excluded only if its accepted occurrence
certainly starts after t; an unavailable or uncertain time keeps the event, marked `timing: unresolved`); unaccepted
claims in a separate `alternatives` list, never as explanations.
- *E2:* which events `initiated_by` lists is **eligible**. The `timing` marker and the `alternatives` list are **G
  (approved, unimplemented)**. *Deferred work:* **DI-35** (inclusion and timing) and **DI-29** (alternatives).

**SD-CAU-3. `explain` when the content does not hold (D-EX-5).** Adopted: **(b)**: initiators are listed beside the
`holds` answer; `initiated_by` implies nothing about `holds`.
- *E2:* **eligible** (current behaviour conforms). C4 questions read `holds` first.

**SD-CAU-4. Attestations of `changes` explanations (D-CH-2).** Adopted: **(a)**: SB B0 governs; each explanation
claim lists its attestations, as an added field.
- *E2:* **G (approved, unimplemented)** for explanation attestations. *Deferred work:* **DI-29**.

**SD-CAU-5. Touching windows (D-CH-3, D-BE-2).** Adopted: **(b) half-open validity intervals**, qualified.
- Ordinary **valid-time intervals remain half-open**: `[a, e)` and `[e, f)` share no instant, so the first
  certainly precedes the second ("meets" is before).
- A **window** expresses uncertainty about **one instant** (an uncertain start or end); it is not a validity interval.
  Its bounds are possible values of that instant, both included.
- A **shared possible instant is never discarded** by applying the half-open convention to a window or to an
  instantaneous event or observation.
- **Strict temporal precedence** (`before`: certainly earlier) and **non-later-than timing consistency** (B-time:
  an effect may not precede its event's start; a simultaneous effect is consistent) are different relations.
- **Boundary examples** (binding):

| Case | Relation | Answer |
|---|---|---|
| a holds over `[10, 12)`, b over `[12, 14)`, exact bounds | `before(a, b)` | **True** (half-open: no shared instant) |
| a's end window `[11, 12]`, b's start window `[12, 13]`, both durative | `before(a, b)` | **True** (every possible end ≤ every possible start, and a's interval excludes its end) |
| a and b instantaneous, both at exactly 12 (simultaneous) | `before(a, b)`, `before(b, a)` | **None** both (neither strictly precedes) |
| a instantaneous with window `[10, 12]`, b instantaneous with window `[12, 14]` | `before(a, b)` | **None** (both may be at 12) |
| a instantaneous at 12, b durative starting at exactly 12 | `before(a, b)` | **None** (a's instant is b's first instant) |
| a durative ending at exactly 12, b instantaneous at 12 | `before(a, b)` | **True** (a's interval excludes 12) |
| event start window `[9, 10]`, transition window with earliest possible instant 10 | B-time timing | **consistent** (the start is certainly not later than the change; simultaneity allowed) |
| event start window `[9, 11]`, transition window `[10, 12]` | B-time timing | **unresolved** (the start may be after the change) |
| event start certainly after the transition's latest possible instant | B-time timing | **excluded** |
| measurement at instant 12 (explicit), content asked at t = 12 | `measurements(t=12)` | listed (SD-MEA-2) |
| attestation with explicit empty interval `[12, 12)` (not a measurement instant) | any reader at t = 12 | holds at no instant |

- *E2:* **eligible** for every case above. *Deferred work:* **DI-36** (instantaneous events in `before`; the writer
  has no explicit instant marker for accounts either, as SD-MEA-2 found for measurements).

**SD-CAU-6. A → UNKNOWN → A, and gaps through DISPUTED (D-CH-4).** Adopted: **(a)**: each judged-state change is a
judgement transition; only Q-B1.1's case (accepted A, UNKNOWN, accepted B ≠ A) is merged into one world-state
transition.
- *E2:* **eligible** (current behaviour conforms).

**SD-CAU-7. The valid time at which timeless claims are judged (D-CH-5, D-EF-6).** Adopted: **(a)**, qualified.
- Timeless claim content (`causes`, `initiates`, `terminates`) is judged **independently of valid-time selection**:
  `t` (or `t2`) never changes a claim's judgement.
- **Knowledge-time visibility, acceptance, perspective, world and supersession still apply.**
- *E2:* **eligible**. The broad corpus follows the fixture convention that claims carry no valid interval; questions
  in which a claim attestation does carry one are allowed only as targeted defect coverage, and expect the timeless
  judgement. *Deferred work:* **DI-35**.

**SD-CAU-8. `changes` with t1 ≥ t2 (D-CH-8).** Adopted: **(c)**: t1 > t2 is refused as malformed; t1 = t2 answers no
transitions.
- *E2:* **eligible**. *Deferred work:* **DI-35** (the refusal).

**SD-CAU-9. Occurrence applicability for effect claims and `changes` explanations (D-EF-5, D-CH-9).** Adopted:
**(a)**: the LABS-1.011 fields (each occurrence's status and `applies`) are extended additively to `effects_of`
entries and `changes` explanations.
- *E2:* **G (approved, unimplemented)** for those fields. *Deferred work:* **DI-28**.

**SD-CAU-10. Several usable accounts, or several timed descriptions (D-IV-1, D-EF-3, D-PS-3).** Adopted: **(a)**,
qualified.
- Certainty is evaluated **across every admissible account and every relevant combination of accounts**: `before`,
  B-time and the `effects_of` instants are certain only if they hold under every combination.
- Certainty is **never inferred from a selected representative**, nor from the **absence** of usable accounts (no
  usable account gives no answer: null or unresolved, never "certain").
- **Account-specific provenance** is preserved: every usable account's interval and attestation is reported.
- *E2:* certainty answers (`before`, timing, `accepted_change`) on multi-account descriptions are **eligible**.
  Reporting every account (in `interval`, `process_steps`, `effects_of`) is **G (approved, unimplemented)**.
  *Deferred work:* **DI-36**.

**SD-CAU-11. Writer-side refusals (D-CO-6, D-EF-7).** Adopted: **(c)**: established writer validations are the two
effect kinds (V02 §3.2) and the required proposition ids (SB B0, deferral D2; PLAN A0). Self-causation stays
**unestablished**.
- *E2:* writer validations are fixture preconditions, not reader questions. No fixture, question or probe relies on
  the self-causation refusal (§5).

## 3. Summary

| Consequence | Decisions |
|---|---|
| eligible, current behaviour conforms | SD-MEA-3 (omission), SD-MEA-4, SD-CAU-3, SD-CAU-6 |
| eligible, correction deferred (current expected to fail some questions) | SD-CORE-1, SD-CORE-2, SD-SPA-1 (parameter), SD-SPA-2, SD-SPA-3, SD-SPA-4, SD-MEA-1, SD-MEA-2, SD-MEA-6, SD-CAU-1, SD-CAU-2 (inclusion), SD-CAU-5, SD-CAU-7, SD-CAU-8, SD-CAU-10 (certainty) |
| eligible through a harness change only | SD-MEA-5 (extractor), SD-CORE-2 (template parameters), SD-SPA-2 (`convention` marker) |
| G, approved but unimplemented (fields or parameters) | SD-CORE-3, SD-SPA-1 (reporting), SD-SPA-2 (basis field), SD-CAU-1 (attribution in `effects_of`), SD-CAU-2 (`timing`, `alternatives`), SD-CAU-4, SD-CAU-9, SD-CAU-10 (every account) |
| G, gap | SD-CORE-1 (parameters: GAP-SPATIAL-8), SD-MEA-3 (GAP-MEAS-12), SD-MEA-4 (GAP-MEAS-13) |
| precondition | SD-CORE-4; SD-CAU-11 (writer validations) |
| still open (ontology) | self-causation, from SD-CAU-11 (§5) |

## 4. Deferred work created or extended

Registered in [deferred-issues.md](../core-0.4/deferred-issues.md). None is implemented. Each component is marked as
a **reproduced defect** (a diagnostic case in `diagnostics.json`), an **inspection-only finding** (from the register,
not reproduced), or a **newly established requirement** (follows from a decision; the old behaviour was not wrong
against any approved text before it).

| DI | Priority | Components |
|---|---|---|
| DI-24 | high | same-as identity in `where`, `poses`, `measurements` (reproduced: DX-2, DX-3) |
| DI-25 | **critical (architectural)** | derived candidates take the worse of chain and premise status (reproduced: DX-1); truncated search through a disputed transform gives DISPUTED (newly established: SD-SPA-3) |
| DI-26 | high | denials of measured content judged, `t` filter keeps the measurement (reproduced: DX-4); `t` as valid time with denials kept (newly established: SD-MEA-1) |
| DI-27 | high / medium | value readers refuse roles forming no declared slot (reproduced: DX-6); dispute sides in `value_at` (inspection only); `key_role` without `value_role` refused (newly established: SD-CORE-2) |
| DI-28 | **critical (architectural)** | lifting needs accepted links on both sides (reproduced: DX-8, DX-10); cite the links used (reproduced: DX-9); occurrence status and `applies` on effect claims and `changes` explanations (newly established: SD-CAU-9) |
| DI-29 | medium | provenance completeness (reproduced: DX-11, DX-13; inspection only: D-TB-3, D-PO-2, D-FI-1, D-TB-7); `facts_about` `constraint_support` (newly established: SD-CORE-3); `changes` explanation attestations (newly established: SD-CAU-4); `explain` `alternatives` (newly established: SD-CAU-2) |
| DI-30 | medium | DI-30a canonical units (inspection only); DI-30b reference check "time unknown" (inspection only). The two parts are corrected and tested independently. |
| DI-31 | medium | `holds()` exact content addressing, malformed refusal, no load-order selection (inspection only: D-HO-1, D-HO-2; requirement newly established: SD-CORE-1) |
| DI-32 | medium | frame-chain conventions: chain tolerance reported (SD-SPA-1), identity by convention with a visible frame and NOT_YET_KNOWN (SD-SPA-2), the `where` label (SD-SPA-4) (inspection only: D-TB-1, D-TB-2, D-WH-2; newly established) |
| DI-33 | high | explicit instantaneous measurements: representation, reader and migration (reproduced: DX-5; requirement newly established: SD-MEA-2) |
| DI-34 | medium | calibration judged throughout the start window (inspection only: D-MC-3; newly established: SD-MEA-6) |
| DI-35 | high | `effects_of` change through `changes` with attribution (reproduced: DX-14; inspection only: D-EF-2); `explain` inclusion and timing (reproduced: DX-11, DX-12; inspection only: D-EX-2); timeless claims (inspection only: D-CH-5, D-EF-6); `changes` t1 > t2 refused (inspection only: D-CH-8) |
| DI-36 | medium | instants in `before` (newly established: SD-CAU-5); certainty across every account, every account reported (inspection only: D-IV-1, D-EF-3, D-PS-3; newly established: SD-CAU-10) |

**Gaps:** GAP-SPATIAL-9 (registered as proposed), and the newly identified GAP-MEAS-12 (categorical measurement)
and GAP-MEAS-13 (declared constant quantities), in
[e2-capability-inventory.md](stage-e-entry/e2-capability-inventory.md).

## 5. Remaining unresolved decisions

| Id | Question | Status | E2 treatment |
|---|---|---|---|
| ONT-SC-1 | Is `causes` irreflexive (may a happening cause itself)? From SD-CAU-11: V02 states no irreflexivity, and the writer's self-causation refusal is code only. | an **ontology decision**, outside E2's semantic scope; not proposed here (the ontology is unchanged) | **blocked** (`blocked.json`): no fixture, question or probe relies on it |

No other semantic decision is outstanding for the E2 readers.
