# E2 reader contracts: author edition

**Generated for the E2 author pack (LABS-1.065)** from `benchmark/e2/spec/reader-contracts.md` by `scripts/e2_author_pack.py`. Statements about how any program behaves have been removed; what remains is the approved semantics. Where a field or value is not fixed here, a question must not expect it.

## 0. Rules shared by every contract

### 0.1 Status of each statement
- **[E] Established:** an approved design text or semantic decision. The citation names it.
- **[P] Proposal (approved):** approved under LABS-1.063, some with qualifications (§0.10); part of the contract.
- A field, value, order or behaviour this edition does not fix is **not part of the contract**: a question must not
  expect it.

**E2 classes** (decided by the coordinator before you write gold; your assignment says which):
- **A/H (scored):** the approved semantics fixes the answer; write the gold from these contracts.
- **G (probe):** the capability is missing (a gap id), or approved but not provided (the §0.11 "G-unimpl" fields).
  A probe states its acceptable outcomes (UNKNOWN, NOT_YET_KNOWN, an established refusal, or the field `absent`) and
  what would be a fabricated answer.
- **Blocked:** ONT-SC-1 (self-causation). Never write a question, fixture or probe that depends on it.

Sources are cited by path and section; the cited documents are not part of the pack unless listed in its README.

### 0.2 Common inputs and visibility [E]
- **`world`:** the world asked about. A variant world sees its base up to its branch point (v0.2 worlds; stage-d0).
- **`t`:** valid time (when the content is true in the world).
- **`as_of`:** knowledge time. Attestations recorded after it are invisible, as are acceptances and supersessions
  recorded after it (v0.2 §5; core-0.3 supersession-and-endings).
- **`perspective`:** the holder whose acceptances decide what is usable (v0.2 acceptance). The default is `system`.
  Nothing is merged across perspectives.
- **Identity:** readers that take an id judge it with its established same-as group, where the design says so (ID-1 to
  ID-9). A group containing a disputed or denied pair is not merged (ID-5).

### 0.3 Status vocabulary [E]
`STIPULATED`, `ASSERTED`, `INFERRED`, `DISPUTED`, `UNKNOWN`, `NOT_YET_KNOWN` (v0.2 §5.6; core rule as increment B/C).
- `UNKNOWN`: something relevant is recorded, but no answer follows.
- `NOT_YET_KNOWN`: nothing relevant is recorded (or visible at `as_of`).
`OBSERVED` and `PRESUMED` are not produced (v0.2 §5.6 note).

### 0.4 Evidence roles [P-1, approved with amendments LABS-1.063]
A cited attestation has exactly one role in an answer:

| Role | Meaning | Scored by |
|---|---|---|
| **supporting** | the answer rests on it: it is evidence for the value, status or judgement given | recall (required), precision (admissible); E2-D6 "precision 100 % for supporting evidence" |
| **conflicting** | the answer reports it as the other side of a dispute that made the answer DISPUTED (rivals; the constraint that makes them rivals; accepted denials) | recall of required conflicting evidence; never counted in supporting precision; forbidden still applies |
| **alternative** | listed but not rested on: unaccepted, superseded, incomparable, a statement beside measurements, a candidate outside the comparison | never cited; citing it as supporting is an inadmissible citation |
| not reported | anything else | — |

- [E] For a DISPUTED `holds` answer, the dispute rests on its own claims, the rivals and the constraint (A0 F-4,
  increment B design §2.3, the approved `constraint_support` rule). E1 counted all three as cited.
- [P-1, approved] They are kept **apart**: `support` is supporting; `conflicts` and `constraint_support` are
  conflicting. The amendments (LABS-1.063):
  - **Independent sets:** supporting and conflicting evidence each have **independently authored** required and
    admissible sets: `required_evidence` / `admissible_evidence` (supporting) and `required_conflict_evidence` /
    `admissible_conflict_evidence` (conflicting). `forbidden_evidence` applies to every role.
  - **Scores:** recall and precision are **reported separately for each role**. E2-D6's supporting-evidence thresholds
    are unchanged (recall ≥ 90 % per applicable family, precision 100 %). **Inadmissible conflicting evidence is an
    explicit failure.**
  - **What a role means:** a role describes the attestation's relationship to the answer. Conflicting evidence may
    legitimately establish a DISPUTED judgement.
  - **Components:** one attestation may hold different roles in different components of one answer, or in different
    plan steps. An established holder's claims, for example, support its appointment and conflict with the rival
    holder. It counts once in each role it holds. The one forbidden combination is an id listed as an alternative and
    as supporting in the same component.

### 0.5 Fixture-level names for evidence [P-2, approved LABS-1.063]
Evidence is named by fixture step, never by attestation id. An attestation the library writes on a fixture step's
behalf gets a **deterministic name derived from that step**, so it is never inadmissible merely because the library
generated it:

| Written by | Name |
|---|---|
| the step's own claim (attest, position, relate_frames, claim_cause, …) | `<step>` |
| `measure` | `<step>` (reported content), `<step>/activity` (the activity's account), `<step>/kind:measurement` (its classification; the uniform `<step>/kind:<category>` form, LABS-1.063), `<step>/produced`, `<step>/reports` |
| `account`, `record_event`, `act_in_office`, `replace_part`, `take_sample` | `<step>` (the occurrence interval), `<step>/kind:<category>` (each classification), `<step>/describes` (the describes link, if `occurrence` is given), `<step>/effect:<n>` (the n-th effect, from 0, in the order the fixture lists them or the profile documents them) |
| `move` | `<step>` (the account), `<step>/effect:<n>`; each claim it ends is a restatement named after the restated step (last row; E1 C3), with `<step>/ended:<restated step>` recorded beside it for reporting |
| `end`, `correct` | `<step>` |
| `destroy` | each system claim ended: a restatement named after the restated step (E1 C3), with `<step>/ended:<restated step>` recorded beside it; each other attester's claim denied: `<step>/denied:<restated step>` |
| a restatement of step X by the library (same attester, content and start: end(), move()) | counts as X (E1 C3 [E], approved LABS-1.053) |

- Names are assigned by the loader from the writer's return values and the fixture's own order. They never depend on
  a run, on a reader, or on random ids.
- A cited attestation that still has no name is **unattributed**. It is reported in its own count, it is neither
  admissible nor inadmissible, and it blocks a pass of the precision criterion until it is adjudicated (H-1).

### 0.6 Precision and recall with empty sets [P-3, approved with amendments LABS-1.063]

Amendments:
- **Missing required evidence is a failure** whether or not precision is defined.
- **Unattributed evidence prevents a verified precision pass** until it is resolved.

| Case | Recall | Precision | Outcome |
|---|---|---|---|
| nothing required, nothing cited | n/a | n/a (vacuous) | no evidence failure; not counted in family totals |
| evidence required, nothing cited | 0 | **undefined**, never 1.0 | `missing-evidence`; counted in the family recall denominator; listed as "no evidence returned" |
| nothing admissible stated (`admissible_evidence: []`), something cited | n/a | 0 | `inadmissible-evidence` |
| `admissible_evidence` absent on a scored question whose reader cites evidence | — | — | refused by the checker (H-3): every such question must state its admissible set |
| cited only unattributed ids | as computed | undefined | the precision criterion is `unverified` until adjudicated |

Family precision is the sum, over questions, of admissible cited / cited. It is computed only over questions that cite
something, and the number of "no evidence returned" questions is reported beside it.

### 0.7 Derivations and premise admissibility [P-4, approved with amendments LABS-1.063]

**Amendment:** premise admissibility requires **visibility, usability and applicability**, not merely existence. A
premise must meet all three:
- **visible:** its fixture step is in the question world's lineage;
- **usable:** it is listed in the question's authored `admissible_premises`, which encode its acceptance, supersession
  and interval for the question's perspective, `as_of` and `t`;
- **applicable:** its content type is one the rule takes.
- [E] The model records one derivation rule, `frame-transform/v1` (stage-a2). It derives a pose or a transform from a
  frame chain and position statements. No general derivation record exists, and basis `inference` is
  reserved for rule-derived attestations (D-D3-4).
- [P-4] A derivation an answer presents is **valid** only if all of these hold:
  1. its rule is one the model records;
  2. it names at least one premise;
  3. every premise is **admissible for the question**.
- **Admissibility is defined by the question, not by whether the attestation exists.** A premise is admissible when:
  - it names a fixture step in the question's `admissible_premises`. These are authored with the gold, from the
    fixture: the steps whose content type the rule takes as input (for `frame-transform/v1`: `positioned-in` and
    `frame-transform`) and which are visible and usable for the question's world, perspective, `as_of` and `t`;
  - and it is not disputed, unless the contract says the rule accepts a disputed premise. The answer must then be
    DISPUTED.
- A premise that exists in the database but is outside that set is **inadmissible** (a fabricated derivation). That
  covers another world, an unaccepted claim, a claim superseded by `as_of`, or the wrong content type.
- This replaces the harness's current existence check (H-2).

### 0.8 Refusals [E, P-5 approved LABS-1.063]
- A refusal is a documented, deliberate "no answer" (an exception naming why), distinct from an execution error.
- [E] Only refusals in this contract's refusal tables are refusals (LABS-1.062). A refusal is **established** only when
  an approved design text states it. Gap probes accept only established refusals.
- [P-5] A precondition failure (a profile not installed, an id that names nothing) is an execution precondition, not a
  semantic refusal. It is reported as an execution error.

### 0.9 Ordering and multiplicity
Unless a contract states an order [E], a list in an answer is compared as a **multiset**. A question that needs one
design states is recorded as (not fixed by the contract).

### 0.10 Approval record (LABS-1.063)

| Proposal | Status | Qualification |
|---|---|---|
| P-1 | approved | independent required and admissible sets per role; recall and precision per role; supporting thresholds of E2-D6 kept; inadmissible conflicting evidence fails; roles describe the relationship to the answer, and conflicting evidence may establish DISPUTED (§0.4) |
| P-2 | approved | unattributed evidence prevents a verified precision pass until resolved (§0.5, §0.6) |
| P-3 | approved | missing required evidence fails whether or not precision is defined (§0.6) |
| P-4 | approved | admissibility needs visibility, usability and applicability, not existence (§0.7) |
| P-5 | approved | — |
| P-HO-1, P-OC-1, P-WH-1, P-ME-1, P-CV-1, P-CS-1, P-MC-1, P-CO-1, P-PS-1, P-IV-1 | approved | as written |
| P-VA-1 | approved, qualified | positive attestations of **mutually exclusive rival values keep their conflicting relationship**; polarity alone does not decide a role. In a dispute between several values, every value's positive claims are conflicting |
| P-OH-1 | approved, qualified | the **conflict relationship between established holders is preserved**: each established appointment's claims support it, and in a conflict the same claims are also conflicting (the `conflict` component), with the constraint's support |
| P-CM-1 | approved, qualified | the shared role amendment (§0.4) applies |
| P-EF-1 | approved, qualified | **event-specific scope of `effects_of` only**; it establishes no general rule excluding causal rivals |
| P-BE-1 | approved, qualified | interval-based evidence extraction for E2; the absence of direct provenance in `before` is recorded as a limitation |

Evidence extraction must not conceal missing evidence, incorrectly presented alternatives or fabricated derivations
(LABS-1.063 item 3). The harness implements these rules in `evaluation/e2/evidence.py` and `score.py`. Its review is
`docs/stage-e/stage-e2-labs-1063-review.md`.


### 0.11 Approved semantic decisions (LABS-1.064) [E]

All 25 semantic decisions are approved (LABS-1.064). Each statement below is established and overrides any other
text in this edition that seems to differ. **Consequence labels:** **eligible** (scored A/H); **G-unimpl** (the approved
field or capability is not provided yet: only a G probe may ask for it, accepting `absent`); **G-gap** (a gap probe);
**precondition** (never authored).

**SD-CAU-5 boundary examples (binding):**

| Case | Relation | Answer |
|---|---|---|
| a holds over `[10, 12)`, b over `[12, 14)`, exact bounds | `before(a, b)` | True (half-open: no shared instant) |
| a's end window `[11, 12]`, b's start window `[12, 13]`, both durative | `before(a, b)` | True |
| a and b instantaneous, both at exactly 12 | `before(a, b)`, `before(b, a)` | None both |
| a instantaneous with window `[10, 12]`, b instantaneous with window `[12, 14]` | `before(a, b)` | None |
| a instantaneous at 12, b durative starting at exactly 12 | `before(a, b)` | None |
| a durative ending at exactly 12, b instantaneous at 12 | `before(a, b)` | True |
| event start window `[9, 10]`, transition window with earliest possible instant 10 | B-time timing | consistent |
| event start window `[9, 11]`, transition window `[10, 12]` | B-time timing | unresolved |
| event start certainly after the transition's latest possible instant | B-time timing | excluded |
| explicit instantaneous measurement at 12, asked at t = 12 | `measurements(t=12)` | listed |
| attestation with an explicit empty interval `[12, 12)` (not a measurement instant) | any reader at t = 12 | holds at no instant |

**SD-MEA-6 in full:** calibration is established only when established throughout the entire possible activity-start
window; agreement at the earliest and latest bounds is insufficient; every internal validity and judgement transition
counts; no arbitrary instant is selected; where continuous establishment cannot be shown, the judgements found and any
dispute are kept and the answer is not "established".

**SD-CAU-1 in full:** an established outcome change, an accepted effect claim and an established causal attribution
are different things; none implies another. An accepted claim associated with an ambiguous transition does not
establish unique causation.

| Decision | Contract statement [E] | Consequence |
|---|---|---|
| SD-CORE-1 | `holds()` addresses **exact content**: type, the given role bindings and the parameters. Omitted optional roles identify the content without them. A missing mandatory role makes the question malformed: a refusal. No load-order selection. | eligible; parameterised content G-gap (GAP-SPATIAL-8) |
| SD-CORE-2 | `value_at` with `key_role` and no `value_role` is malformed: a refusal. | eligible |
| SD-CORE-3 | `facts_about` entries disputed under an attested constraint cite it in an added `constraint_support`. | G-unimpl (`*constraint_support`) |
| SD-CORE-4 | `occurrence` and `occurrence_status` take an occurrence; another kind of id is an execution precondition. | precondition |
| SD-SPA-1 | Chain agreement uses 1e-9 rad; `angle_tolerance` governs candidate (position-claim) comparison only (as confirmed in LABS-1.064). The chain tolerance is reported in `chain_tolerance`. | eligible; `chain_tolerance` G-unimpl |
| SD-SPA-2 | `source == target` with a valid, visible frame: the identity transform as a **declared convention**, status INFERRED (v0.2 §5.6), **no derivation presented and no supporting attestation cited**; no visible record of the frame: NOT_YET_KNOWN. No chain between distinct frames: NOT_YET_KNOWN when no `frame-transform` involving either is visible, UNKNOWN otherwise. A convention-derived result is distinguished from evidence-derived inference (questions mark it `"convention": "frame-identity"`); its basis is reported in `basis`. | eligible; `basis` G-unimpl |
| SD-SPA-3 | A truncated search whose reached chain contains a disputed transform: DISPUTED, no transform. | eligible |
| SD-SPA-4 | `where` `judgement`: `compatible` only when every pair of positioned, verified candidates was compared and overlaps; `conflicting` on a verified conflict; otherwise none; `single` / None for one / no candidate. | eligible |
| SD-MEA-1 | `t` in the measurement readers is valid time: every attestation whose verdict at `t` is not silent is included, denials too, each with its acceptance and role. In `measurement_calibration`, `t` selects measurements only. | eligible |
| SD-MEA-2 | An **explicit instantaneous measurement** (`measure` with a start, no end, not `persists`) holds at its instant; two at one instant may be compared subject to the other conditions. Empty half-open intervals are not redefined; instant, empty interval and persistent content stay distinct. | eligible |
| SD-MEA-3 | `measurements` and `compare_measurements` cover interval-valued quantities only; categorical values are read through `holds` / `facts_about`. | eligible; categorical measurement G-gap (GAP-MEAS-12) |
| SD-MEA-4 | Measurements whose valid times do not overlap are incomparable (every quantity may change). | eligible; constant quantities G-gap (GAP-MEAS-13) |
| SD-MEA-5 | The accepted claim of a not-yet-effective certificate is **supporting** evidence; `support` empty means no status support. | eligible (harness extractor) |
| SD-MEA-6 | Calibration is established only if established **throughout** the whole possible activity-start window, considering every internal validity and judgement transition; no arbitrary instant; otherwise the judgements found and any dispute are preserved. | eligible |
| SD-CAU-1 | `effects_of` `accepted_change` uses `changes()` world-state transitions: UNKNOWN and DISPUTED transitions are not accepted changes; delayed effects count without invented precision; unique and ambiguous attribution preserved (`attribution`). An established outcome change, an accepted effect claim and an established causal attribution are distinct; an accepted claim on an ambiguous transition does not establish unique causation. | eligible; `effects_of` `attribution` G-unimpl; `changes` questions fix every inspected explanation's `attribution` (H-9) |
| SD-CAU-2 | `explain` `initiated_by`: accepted `initiates` claims only; excluded only if the accepted occurrence certainly starts after t; an unavailable or uncertain time keeps the event with `timing: unresolved`; unaccepted claims in `alternatives`, never explanations. | eligible (which events); `timing`, `alternatives` G-unimpl |
| SD-CAU-3 | `explain` lists initiators beside `holds` whatever it says; `initiated_by` implies nothing about `holds`. | eligible |
| SD-CAU-4 | Each `changes` explanation claim lists its attestations (`attestations`). | G-unimpl |
| SD-CAU-5 | Valid-time intervals are half-open; a window is uncertainty about one instant (both bounds possible); a shared possible instant is never discarded; strict precedence (`before`) and non-later-than consistency (B-time) are different relations. Boundary examples: decision record SD-CAU-5. | eligible |
| SD-CAU-6 | Each judged-state change is a judgement transition; only accepted A, UNKNOWN, accepted B ≠ A merges. | eligible |
| SD-CAU-7 | Timeless claims are judged independently of valid time; knowledge-time visibility, acceptance, perspective, world and supersession still apply. | eligible |
| SD-CAU-8 | `changes` with t1 > t2 is refused; t1 = t2 has no transitions. | eligible |
| SD-CAU-9 | Effect claims and `changes` explanations carry each occurrence's status (`occurrence_status`) and `applies`. | G-unimpl |
| SD-CAU-10 | Certainty holds only across every admissible account and combination; never from a representative or from no usable account; every usable account reported (`usable_accounts`). | eligible (certainty); `usable_accounts` G-unimpl |
| SD-CAU-11 | Established writer validations: the two effect kinds; proposition ids required. Self-causation is unestablished (ONT-SC-1, blocked). | precondition |

**Reserved field names.** `chain_tolerance`, `basis`, `constraint_support` (in `facts_about`), `attribution` (in
`effects_of`), `timing` (in `explain`), `alternatives` (in `explain`), `attestations` (in `changes` explanations),
`applies` and `occurrence_status` (in `effects_of` and `changes`), and `usable_accounts` name the approved but

### 0.12 Established rules restated (pack v1.1) [E]

These approved rules were stated inside entries this edition otherwise removes, so they are restated here. Each is
established; it overrides any other text in this edition that seems to differ.

| Reader | Rule | Source |
|---|---|---|
| `value_at` | A dispute keeps its conflicting relationship between rival values; polarity alone is not enough. | A0 F-4; SB Q-B2; P-VA-1 as qualified |
| every reader, incl. `value_at` | No reader reports content that is DISPUTED for the perspective as undisputed. Value readers apply declared slots only; an exclusive office whose holders conflict is never reported as undisputed by a value reader. | B-D §2, §3; DI19 report §1; D2 §3; v0.2 §5.3 |
| `transform_between` | A disputed transform on any route gives DISPUTED, with the disputed transform's attestations reported as conflicting evidence. | A2 "Outcomes"; v0.2 §5.3 |
| `transform_between` | Unreviewed transforms bearing on the answer are listed as alternatives. | v0.2 §6.2 |
| `where` | A derived candidate from a position disputed by an accepted denial is not INFERRED: the answer is not an undisputed INFERRED. | A2 "Provenance"; v0.2 §5.2 E6; common 0.7 |
| `where`, `poses` | The thing is judged with its established same-as group: asking by any member gives the same candidates. | ID-D 9, ID-8 |
| `poses` | Disputed entries cite both sides. | IB-D 4 |
| `frame_info` | Disputed transforms, anchors and positions are marked and cited on both sides. | IB-D 4 |
| `measurements` | An accepted denial is usable conflicting evidence. | v0.2 §6.2, §5.3; common §0.4 P-1 |
| `measurements` | Measurements of an alias are measurements of the bearer (selection by the whole identity class). | ID §3.8 ID-8 |
| `measurements` | `has-quality` content is reported in the SI unit. | D-C-1; v0.2 §3.3 |
| `compare_measurements` | An accepted assertion and an accepted denial of the measured content give DISPUTED, citing both, with or without `t`. | v0.2 §5.3; stage-c "Disputes" |
| `measurement_calibration` | The reference check "no certificate recorded" applies only when the instrument has no certificates. | d3 §3 |
| `causes_of` | A description-level claim answers an occurrence question only when both descriptions have usable describes links. | PLAN §9.3 "Lifting"; SB U-2 |
| `causes_of` | A lifted answer cites the describes links' attestations. | PLAN §9.3; SB "Lifting" |
| `causes_of` | A describes link whose judgement is DISPUTED is not accepted and does not lift. | SB U-2; V02 §3.2 |
| `explain` | Each initiating claim lists its attestations (required evidence may name them). | SB B0 |
| `changes` | An accepted "does not hold" side cites its deciding attestations. | SB Q-B1.2 |

## Part A. Core and organisation

### Reader contracts, core and organisation: `holds`, `value_at`, `facts_about`, `occurrence`, `occurrence_status`, `office_holders`

**Status:** draft for review (E2-D3, LABS-1.062). Follows `this document's §0` (rules 0.1 to 0.9) and the evidence
file `docs/stage-e/e2-reader-contracts/evidence-core.md`.

**Short source names** (repository paths):

| Name | Path |
|---|---|
| v0.2 | `docs/architecture/world-ontology-v0.2.md` |
| C03 | `docs/core-0.3/README.md` |
| SUP | `docs/core-0.3/supersession-and-endings.md` |
| A0 | `docs/core-0.4/README.md` (Stage A0) |
| A2 | `docs/core-0.4/stage-a2.md` |
| SB | `docs/core-0.4/stage-b.md` |
| D2D / D2 | `docs/core-0.4/stage-d2-design.md` / `stage-d2.md` |
| B-D / B | `docs/core-0.4/pre-e-increment-b-design.md` / `pre-e-increment-b.md` |
| C-D / C | `docs/core-0.4/pre-e-increment-c-design.md` / `pre-e-increment-c.md` |
| D-D / D | `docs/core-0.4/pre-e-increment-d-design.md` / `pre-e-increment-d.md` |
| ID-D / ID | `docs/core-0.4/pre-e-identity-design.md` / `pre-e-identity-increment.md` |
| GATE | `docs/core-0.4/pre-e-decision-gate.md` |
| MP-D / MP | `docs/core-0.4/pre-e-multiplicity-design.md` / `pre-e-multiplicity-increment.md` |
| REG | `docs/core-0.4/deferred-issues.md` |
| R | `docs/stage-e/e1-reconciliation-design.md` |
| DI19 | `docs/stage-e/stage-e-di19-constraint-support.md` |
| E2D | `docs/stage-e/stage-e2-evaluation-design.md` |
| E2DEC | `docs/stage-e/stage-e2-decisions.md` |
| HR | `docs/stage-e/stage-e2-harness-review.md` |
| INV | `docs/stage-e/stage-e-entry/e2-capability-inventory.md` |
| T / CL | `benchmark/e1/TEMPLATES.md` / `benchmark/e1/CLARIFICATIONS.md` |

### Evidence roles for `holds()` and `value_at()` under common 0.4

This section settles, field by field, the role each `holds()` and `value_at()` field has. It is the basis for the
evidence tables in HO and VA.

**What is established [E].** A DISPUTED `holds` answer rests on three things:
- its own claims (`support`);
- the rival contents' claims (`conflicts`);
- the attested constraint that made them rivals (`constraint_support`).

Sources: A0 F-4 ("support=<its own attestations>, conflicts=<the conflicting attestations>, evidence=<both>"); B-D
§2.3; D2 §3; DI19 §1. Unaccepted attestations are alternatives, never support (v0.2 §6.2; B-D §2.2). E1 counted all
three fields as cited (HR §5.1).

**What P-1 changes.** Under P-1 the three stay apart: supporting for the value, status or judgement given; conflicting
for the other side of a dispute.

**`holds()`, by field and case:**

| Field | Case | Role | Basis |
|---|---|---|---|
| `support` | established (holds True) | supporting | [E] C-D §2 "deciding support" |
| `support` | not holding by an accepted denial or an accepted end (holds False, not DISPUTED) | supporting: the denial or ended assertion is what the "false" answer rests on, not a rival | [E] B-D §2.4, C-D §2 |
| `support` | **not holding by exclusivity** (INFERRED, holds False): `support` holds the attestations of the *other*, established value of the slot | **supporting**: R3 says the answer cites "the established value's attestations". Gold must list that other value's steps as admissible supporting evidence, although they are not attestations of the content asked about | [E] R R3; B-D §2.4 addendum; CL C5 |
| `support` | **polarity dispute** (DISPUTED, reason `polarity`): `support` holds both the deciding accepted assertions and the deciding accepted denials | split by polarity: the assertions are supporting; the **accepted denials are conflicting** (common 0.4 lists "accepted denials" as conflicting). Answer path: each id in `support` whose entry in `evidence` has `polarity: false` | P-HO-1 (applies P-1); the field contents are [E] (C03 example; v0.2 §5.3) |
| `support` | constraint dispute (DISPUTED, reason `constraint`): the content's own claims | supporting | [E] A0 F-4 |
| `conflicts` | constraint dispute: the rival contents' deciding claims | conflicting | [E] content (A0 F-4; B-D §2.3); role P-1 |
| `constraint_support[].support` | an applied attested constraint (in practice only in a constraint dispute) | conflicting: it is what makes the rivals conflict | [E] content; role P-1 |
| `alternatives` | any case | alternative: never cited | [E] v0.2 §6.2 |
| `evidence` | any case | detail of `support` and `conflicts`, never a separate role | [E] A0 F-4 |

**`value_at()` and `value_of()`, by field:**
- **`support` holds every side of a dispute.** It contains the deciding attestations of every content in the slot
  that holds or is polarity-disputed: all listed values and, for a polarity-disputed value, its accepted denials.
  There is no `conflicts` field. The field's contents are (not fixed by the contract).
  only that `value_at` "reports DISPUTED" (A0 F-4; SB Q-B2).
- **Roles** (P-VA-1, approved with the LABS-1.063 qualification: polarity alone does not decide a role):
  - **one value held, not disputed:** `support` is **supporting**;
  - **a dispute between several (mutually exclusive) values:** every value's positive claims are **conflicting**, since
    they are rivals establishing the DISPUTED judgement. Each value's claims are conflicting with the others';
  - **one polarity-disputed value:** its assertions are **supporting**, and its accepted denials are **conflicting**.
- `alternatives`: alternative [E] (v0.2 §6.2).
- `constraint_support`: always empty [E] (DI19 §1).

**E1 compatibility.** E1's harness counted all of `support` as cited for `value_at`. Under P-VA-1 the same ids are
cited, now split into the roles above.

---

### `holds(world, type, roles, t, as_of=None, perspective="system")`

**Serves:** steps of X plans. `holds` is one of the E1 readers available to multi-step plans (HR §1; E2D §3.6). It
also carries the E1 `holds` template (T). Gap probes: GAP-SPATIAL-8 (`holds` cannot single out one position; INV),
GAP-MULTI-6 (no derivation record; E2DEC §1).

1. **Inputs and conditions**
   - [E] The question is about one content: `type` (a subtype is included, A0 A0.2) plus role bindings, in context
     ⟨world, t, as_of, perspective⟩ (B-D §2.1, §3).
   - [E] Role names are the type's core role names, inherited ones included (R R2).
   - [E] Parameters are not part of the question (A2 D-A2-5).
   - [E] A `same-as` question is judged by its stated names (ID-1) and is timeless (ID-3).
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `status` | Status | STIPULATED, ASSERTED, INFERRED, DISPUTED, UNKNOWN, NOT_YET_KNOWN | [E] v0.2 §5.6; C03 D1, D4 |
   | `holds` | bool or None | True, False, None (None when DISPUTED, UNKNOWN or NOT_YET_KNOWN) | [E] C03; A0 F-4 |
   | `support` | ids | the deciding attestations (see the evidence section above) | [E] A0 F-4; R R3 |
   | `conflicts` | ids | rival contents' deciding attestations, only in a constraint dispute | [E] A0 F-4 |
   | `constraint_support` | list of {constraint, key, value_role, support, evidence} | one entry per applied attested constraint | [E] DI19 §1; E2DEC §1 |
   | `alternatives` | ids | unreviewed, not superseded attestations with a verdict at t | [E] v0.2 §6.2; B-D §2.2 |
   | `evidence` | list of dicts | attester, stance, basis, polarity, world, interval, recorded_at, superseded_by_source | [E] C03 "Regression results"; SUP §2 |

   - [E] The canonical judgement word (established, disputed, not holding, pending, unknown) is not an `Answer` field.
     It is read from `judgement(...)`, as E1's `holds` template does (T; B-D §3).
3. **Judgement and uncertainty**
   - [E] `holds` is a projection of the canonical record. Rule Q does not apply: `holds` is the reference for it
     (C-D §4).
   - [E] Status is the core rule over the deciding attestations: STIPULATED > ASSERTED > INFERRED (C-D §1; C03 D4).
   - [E] DISPUTED arises in three ways (B-D §2.4; v0.2 §5.3; B "Answer changes"):
     - a polarity dispute at the nearest deciding depth;
     - a declared-slot conflict;
     - an attested-constraint conflict, where the constraint is ESTABLISHED in the same context.
   - [E] A constraint that is pending, unknown, denied or disputed never disputes compatible holdings (B-D §2.3).
   - [E] Functional exclusivity: another established value in the slot gives INFERRED false, decided before pending.
     A disputed slot decides nothing (R R3; A0 F-4 "Unchanged").
   - [E] There is no exclusivity inference under attested constraints: an unmentioned person gives NOT_YET_KNOWN
     (D2 §1).
   - [E] An unknown end assumes no continuation (B-D §2.4). An ended interval is false only until the content is
     re-attested (C03 D5).
4. **Visibility**
   - [E] common 0.2; v0.2 §6.2, §6.3.
   - [E] Supersession is per perspective (SUP §2).
   - [E] Nearest-world precedence applies (B-D §2.1).
   - [E] Identity follows ID-2 to ID-8. The links relied on are not added to the evidence (ID-D §3.10).
   - [E] A constraint is cited only where the perspective accepts it, within its valid and knowledge time; a
     superseded constraint cites its successor; inherited constraints are cited in variants (DI19 §2).
5. **Ordering and multiplicity**
   - [E] `constraint_support` is sorted by constraint and key (DI19 §1).
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `support` | status ≠ DISPUTED (established; not holding by denial or end; INFERRED false by exclusivity, which cites the other value's attestations) | [E] C-D §2; R R3 |
   | supporting | `support[i]` where `evidence[attestation=i].polarity` is true | DISPUTED, reason polarity | P-HO-1 |
   | conflicting | `support[i]` where `evidence[attestation=i].polarity` is false | DISPUTED, reason polarity | P-HO-1 (P-1) |
   | supporting | `support` | DISPUTED, reason constraint | [E] A0 F-4 |
   | conflicting | `conflicts` | DISPUTED, reason constraint | [E] A0 F-4; P-1 |
   | conflicting | `constraint_support[*].support` | an applied attested constraint | [E] DI19; P-1 |
   | alternative | `alternatives` | always | [E] v0.2 §6.2 |
   | not cited | `evidence`, `constraint_support[*].evidence` | detail only | [E] A0 F-4; DI19 |

7. **Derivations and admissible premises**
   - [E] None are presented. INFERRED comes from basis `inference` or from
     query-time exclusivity. No `{rule, premises}` may appear (E2DEC §4).
8. **Refusals**

   | Name | Condition | Exception / message | Established? | Source |
   |---|---|---|---|---|
   | unknown-role | a role name the type does not relate (core names, inherited included) | `UnknownRoleError` (ValueError), naming the type, the unknown names, the valid names and a hint for stored profile names | yes | R R2; HR §9 |

9. **Limitations and gaps**
   - [E] TI-1 to TI-3 (ID §10).
   - [E] D-A2-5 / GAP-SPATIAL-8.
   - [E] No OBSERVED, PRESUMED or persistence (C03 D1).

---

### `value_at(world, type, subject, t, as_of=None, perspective="system", key_role=None, value_role=None)`
(and `value_of(world, type, key, t, ...)`)

**Serves:** X3, second step (`event_role` → `value_at`: "where is the new part now?", E2D §3.6); the E1 `value_at`
template (T); X plans generally (HR §1). Gap probes: GAP-MEAS-6 (`has-quality` is not a functional slot), GAP-MULTI-2
("at the time of event E": gold states the instant), GAP-MULTI-6.

1. **Inputs and conditions**
   - [E] Without `key_role`, `type` must have **exactly one one-role functional constraint**. Otherwise the question
     names the roles, and composite keys use `value_of` (A0 "What uses them"; DI19 §1).
   - [E] With explicit `key_role` and `value_role`, the inverse or non-functional question is answered ("what is on
     the shelf?": several compatible values, ASSERTED; A0 "The shelf dispute").
   - [E] `value_of(key)` names a player for every key role of one constraint (A0 A0.3).
   - [E] Role names are checked as in `holds` (R R2).
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `status` | Status | STIPULATED, ASSERTED, INFERRED (the core rule over the values held), DISPUTED, UNKNOWN (records visible, no value), NOT_YET_KNOWN | [E] C-D §3.3, §4; C03 |
   | `values` | ids | canonical ids under the perspective's identity; empty when none | [E] B-D §2.3; A0 F-5; T |
   | `alternatives` | ids | unreviewed, not superseded keyed attestations with a verdict at t | [E] v0.2 §6.2; C03 example |
   | `constraint_support` | list | always empty | [E] DI19 §1 |
   | `evidence` | list of dicts | as for `holds` | [E] C03 |

3. **Judgement and uncertainty**
   - [E] One functional-conflict judgement is shared with `holds`, `facts_about` and `changes` (SB Q-B2). DISPUTED
     arises when two holding contents give different value players to one constraint key, or a value is
     polarity-disputed (A0 shelf root cause; D2D §3 "Judgement: polarity").
   - [E] Parameter values conflict only when they cannot both be true (A2 D-A2-1).
   - [E] Only declared slots apply; attested constraints never do (DI19 §1).
   - [E] Status rests on the values held, not on accepted denials of other values (C-D §3.3, C-6).
   - [E] Unreviewed rivals never create a dispute (A0 F-4 "Unchanged").
4. **Visibility**
   - [E] common 0.2.
   - [E] A nearer world's value overrides inherited values for the same key (A0; B-D §2.1).
   - [E] Value identity agrees on both load paths (A0 F-5).
   - [E] Selection is by identity class (ID-D §3.8).
5. **Ordering and multiplicity**
   - [E] Several values are possible: compatible values under explicit roles, or every value in a dispute (A0 shelf
     table).
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | conflicting | `support` (every value's positive claims) | DISPUTED between several values | P-VA-1 as qualified (LABS-1.063): mutually exclusive rivals |
   | supporting | `support[i]` where `evidence[attestation=i].polarity` is true | DISPUTED, one value (polarity dispute) | P-VA-1 |
   | conflicting | `support[i]` where `evidence[attestation=i].polarity` is false | DISPUTED, one value (polarity dispute) | P-VA-1 (P-1) |
   | alternative | `alternatives` | always | [E] v0.2 §6.2 |
   | not cited | `constraint_support` (always empty), `evidence` | always | [E] DI19 §1 |

7. **Derivations and admissible premises**
   - [E] None are presented. INFERRED comes only from basis `inference`.
8. **Refusals**

   | Name | Condition | Exception / message | Established? | Source |
   |---|---|---|---|---|
   | unknown-role | `key_role`, `value_role` or a `value_of` key role the type does not relate | `UnknownRoleError` | yes | R R2; HR §9 |
   | no-single-slot | `value_at` without `key_role` on a type without exactly one one-role functional constraint (for example `office-holding`, `has-quality`) | `ValueError` ("… one-role functional constraints …: name key_role and value_role") | **yes** | A0 "What uses them" (L58-60); DI19 §1 and test `test_value_readers_never_apply_attested_constraints` |

9. **Limitations and gaps**
   - [E] GAP-MEAS-6.
   - [E] A2 range propagation can miss a conflict, never invent one (A2 limitations).
   - [E] No attested constraints in value readers (DI19).

---

### `facts_about(world, subject, t, as_of=None, perspective="system")`

**Serves:** X2, second step (`measurement_calibration` → `facts_about`: who issued the certificate, E2D §3.6); X plans
(HR §1). Gap probes: GAP-MULTI-6, GAP-MULTI-8.

1. **Inputs and conditions**
   - [E] One subject (any particular), with contents of every non-event, non-identity type that involve it.
     Selection is by the subject's identity class (B-D §3 `judgements_about`; ID-D §3.8).
2. **Output fields and vocabulary** (a list of entries)

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `type`, `roles`, `params` | content | roles canonical under identity | [E] B-D §2.2, §4 |
   | `judgement` | str | `established`, `disputed` | [E] B-D §4; B "Readers"; B points decided 3 |
   | `status` | Status | DISPUTED for a dispute, else the support status | [E] B-D §2.4 |
   | `support_status` | Status | the core rule before constraints (DISPUTED for a polarity dispute) | [E] B-D §2.4 |
   | `support` | ids | deciding attestations | [E] B-D §4 |
   | `assertions`, `denials` | ids | the deciding accepted claims on each side | [E] B "Readers" |
   | `conflicts` | ids | rival contents' attestations under a declared or attested constraint | [E] B-D §4 |

3. **Judgement and uncertainty**
   - [E] Only ESTABLISHED and DISPUTED contents are listed. Not holding, pending, unknown and excluded contents are
     never listed (B points decided 3; B "Cost" 2).
   - [E] A polarity dispute is listed in place, citing both sides.
   - [E] Declared and attested constraints are applied.
   - [E] A dispute is listed only while it is one, for the perspective and knowledge time asked (B "Tests").
4. **Visibility**
   - [E] common 0.2.
   - [E] A value overridden by a nearer world is not listed (B points decided 3).
5. **Ordering and multiplicity**
   - [E] One entry per content class under identity (B-D §2.5); compare as a multiset keyed by `type` and `roles`.
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `[entry].support` | `judgement` = established | [E] B-D §4 |
   | supporting | `[entry].assertions` | `judgement` = disputed | [E] contents B-D §4; role P-1 |
   | conflicting | `[entry].denials` | disputed by polarity | [E] contents; role P-1 |
   | conflicting | `[entry].conflicts` | disputed by a constraint | [E] contents B-D §4; role P-1 |
   | not cited | listed contents not asked about by the question | — | common 0.9 (pick by field) |

7. **Derivations and admissible premises**
   - [E] None are presented.
8. **Refusals**
   - None documented.
9. **Limitations and gaps**
   - [E] GAP-MEAS-6 (two stated values of one quality are not disputed).

---

### `occurrence(world, occurrence, as_of=None, perspective="system")`

**Serves:** first step of X3 and X6 (the `event_role` template, E2D §3.6; T `event_role`). Gap probes: GAP-MULTI-8
, GAP-MULTI-2.

1. **Inputs and conditions**
   - [E] An occurrence id. Any member of its identity class gives the same view, apart from the `occurrence` key
     (ID-9).
   - [E] There is no valid time: participants are not a state at a time (D-D §3.6).
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `descriptions` | ids | descriptions with a usable describes link | [E] v0.2 §3.2; ER-5 (unchanged) |
   | `participants` | map | the core-role projection (Core 0.3) | [E] ER-5 |
   | `accounts[*]` | list | description, type, attesters, `describes` (claim label), `account` (`accepted`/`unreviewed`/`rejected`/`none`), depth, roles by stored label | [E] ER-5; D "After the merge" |
   | `roles[label].resolved` | dict | `judgement` ∈ {`established`, `disputed`, `union`, `none`}; `players` (empty for disputed and none); `compared`; `overridden`; `not_compared`; `constraint`; `support` | [E] R R1 |
   | `roles[label].constraints[*]` | list | `applies`, `why`, `classification`, `judgement` ∈ {`established`, `disputed`, None}, `status`, `support`, `players`, `overridden`, `multiplicity` ∈ {`one`, `set`}, `reason` ∈ {`several players in one account`, `accounts name different players` (joined `; `), `accounts name different sets of players`}, `sets` | [E] ER-4, ER-5; MP-2, MP-4; T |
   | `roles[label].players` | map | every player of every linked account ("who is said to have taken part, by whom") | [E] ER-5; R R1 |
   | `aliases`, `identity` | list / dict | the class members; the links used, with depth and conflicts | [E] ID-9 |

3. **Judgement and uncertainty**
   - [E] Compared accounts: describes link ESTABLISHED (judged at the account's start) and account accepted; the
     nearest world decides (ER-3; D §2).
   - [E] Constraints are profile-declared on the profile's own types and inherited by subtypes (ER-1).
     Kind-scoped constraints apply only where the classification is ESTABLISHED at the occurrence's start (ER-2).
     A kind-scoped declaration wins over an unconditional one (MP-3).
   - [E] Rule Q (ER-4, MP-2):
     - `one`: more than one distinct player is DISPUTED (support empty); exactly one is established, with the core
       rule over the account attestations;
     - `set`: the same set in every compared account is established; otherwise DISPUTED;
     - no applicable constraint: a union with no judgement.
     - Multiplicity alone is never a conflict (D-D §3.7).
   - [E] `union` is not `established`. A player's `status` is an evidence status, not a judgement. Nothing here
     decides existence (R R1; ER-4).
   - [E] Declarations are timeless: they also apply at an earlier `as_of` (D-D §8.4).
4. **Visibility**
   - [E] Perspective, knowledge time and variant inheritance apply as in D-D §3.6 (X1 to X7d4).
   - [E] Players are grouped under the perspective's identity: same-as merges only where ESTABLISHED (ID-2; MP-D M8,
     M9).
5. **Ordering and multiplicity**
   - [E] Order and identifiers never change a judgement (D-D §9; D §4).
   - [E] `roles` is keyed by stored label (ER-5).
   - [E] Several players per account are allowed for actor, patient, official, removed, fitted and sampler; every
     other role holds one (MP §2).
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `roles[label].resolved.support` | `resolved.judgement` ∈ {established, union} | [E] R R1 |
   | supporting | `roles[label].constraints[applies=true].support` | constraint judgement established | [E] ER-4 |
   | supporting | `roles[label].constraints[applies=true].classification.support` | a kind-scoped constraint that applies | [P] P-OC-1 |
   | conflicting | the account attestations of `constraints[*].players[*].accounts` | constraint judgement disputed (support is empty) | [E] contents ER-4; role P-1 |
   | alternative | `resolved.not_compared`, `resolved.overridden`, accounts not compared | always | [E] ER-3; R R1 |
   | not cited | `participants`, `descriptions`, `roles[label].players` | — | [E] R R1 ("use `resolved` for who took part") |

7. **Derivations and admissible premises**
   - [E] None are presented. Classification, identity and describes links are judged contents (ER-2; ID-9).
8. **Refusals**
   - None documented for the reader. Profile and module installation refusals are not reader refusals (D "After the
     merge"; MP-5; common P-5).
9. **Limitations and gaps**
   - [E] TI-1 `derived` marker deferred.
   - [E] Destination and product stay single.
   - [E] GAP-MULTI-8.

---

### `occurrence_status(world, occurrence, t, as_of=None, perspective="system", details=True)`

**Serves:** X4, second step (`explain` → `occurrence_status`, E2D §3.6); C2, through the per-occurrence status that
`causes_of` reports (E2D §3.4; SB LABS-1.011). Gap probes: GAP-MULTI-8, GAP-MULTI-2.

1. **Inputs and conditions**
   - [E] An occurrence id and a valid time t. Aliases take the identity class (ID-D §3.9; ID §4).
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `status` | str | `accepted`, `denied`, `disputed`, `not established` | [E] SB LABS-1.011, LABS-1.012; T |
   | `answer` | Answer | the `exists()` answer that `status` is read from | [E] SB "One existence judgement" |
   | `existence[*]` | list | judgement (claim label), status, attestations | [E] SB L422-424 |
   | `descriptions[*]` | list | description, `account` (`accepted`/`unreviewed`/`rejected`/`none`), `account_by`, `describes` (claim label), `describes_by` | [E] SB LABS-1.011; D "After the merge"; B-D §6 |

3. **Judgement and uncertainty**
   - [E] The status is judged only from the occurrence's own existence attestations. Descriptions, links, causal
     claims and process membership never establish it (Occ-1; SB LABS-1.011).
   - [E] `exists()` gives ASSERTED or STIPULATED (true, or false before the existence starts or after it ends), or
     DISPUTED. Otherwise it gives UNKNOWN or NOT_YET_KNOWN, and never INFERRED (SB L419-421).
   - [E] An accepted account of a denied occurrence stays visible (Occ-2).
   - [E] A role dispute never decides existence (ER-4).
4. **Visibility**
   - [E] common 0.2.
   - [E] A plan can stipulate that an event did not happen: `denied` in the plan, the base unchanged (SB LABS-1.011
     "Hypothetical overrides").
5. **Ordering and multiplicity**
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `answer.support` | status `accepted` or `denied` | [E] SB LABS-1.012 |
   | supporting | `answer.support[i]` with `evidence[attestation=i].polarity` true | status `disputed` | P-1 (as P-HO-1) |
   | conflicting | `answer.support[i]` with `evidence[attestation=i].polarity` false | status `disputed` | P-1 (as P-HO-1) |
   | alternative | `answer.alternatives` (unreviewed existence claims) | always | [E] SB L421 |
   | not cited | `descriptions[*]`, `existence[*].attestations` | reported provenance, not support | [E] SB LABS-1.011 |

7. **Derivations and admissible premises**
   - [E] None are presented. Inference from participation is excluded for occurrences (SB LABS-1.012).
8. **Refusals**
   - None documented.
9. **Limitations and gaps**
   - [E] GAP-MULTI-8.

---

### `organisation.office_holders(wm, world, office, context, t, as_of=None, perspective="system")`

**Serves:** X6, last step (`process_steps` → `event_role` → `office_holders`, E2D §3.6); the E1 `office_holders`
template (T). Gap probes: GAP-MULTI-2 (the instant of the act), GAP-MULTI-6.

1. **Inputs and conditions**
   - [E] An office (a `social-role` concept) and a context, matched exactly with no containment (D2D §3; D-D-4).
   - [E] Appointments are `office-holding(classified, class, context)` (R R2; CL C4).
   - [P] The organisation profile must be installed. This is a precondition (common P-5).
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `holders` | ids | the established appointments | [E] D2 §2; C-D §3.2; T |
   | `status` | Status or None | DISPUTED (a conflict or a disputed appointment); None (established without conflict); UNKNOWN (appointments, none established); NOT_YET_KNOWN (none) | [E] C-D §3.2, C-5 |
   | `exclusive` | dict | the constraint's own `holds`, `status` and `support` at t | [E] D2 §2; C-D §3.2 |
   | `conflict` | dict or None | `constraint.support`; `appointments[*].attestations` (accepted) | [E] D2 §2, §3 |
   | `appointments[*]` | list | holder; `judgement` ∈ {established, denied, expired, not yet effective, disputed, not established}; holds; status; evidence (every claim with its acceptance) | [E] B-D §2.4 holdings labels; D2 §2; B (choice A) |

3. **Judgement and uncertainty**
   - [E] Each appointment is judged before the exclusivity constraint, with the conflict reported beside it (B "What
     changed", choice A; B-D §8 Q4).
   - [E] Exclusivity is the attested `exclusive-office(office, context)` over its own valid time. It applies only
     where ESTABLISHED in the same context (D2 §1; B-D §2.3).
   - [E] There is no inference about unmentioned people. Denial is distinct from absence. An appointment event alone
     establishes nothing. Succession is not a conflict (D2 §1, §3; D2D §3).
   - [E] Rule C: there is no collective support status (C-5).
4. **Visibility**
   - [E] common 0.2; perspectives, knowledge time and plans as in D2 §3.
   - [E] Selection is by identity class (ID-8; GATE §1.2).
5. **Ordering and multiplicity**
   - [E] Several holders are possible (C-D §3.2).
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `appointments[judgement=established].evidence[acceptance=accepted].attestation` | always | [E] D2 §3; CL C1 |
   | conflicting | `conflict.appointments[*].attestations` (component `conflict`) | a conflict | [E] D2 §3; P-OH-1 as qualified: the conflict relationship between established holders is preserved |
   | conflicting | `conflict.constraint.support` | a conflict | [E] contents D2 §3,; role P-1 |
   | alternative | `appointments[*].evidence[acceptance≠accepted]` | always | [E] v0.2 §6.2; D2 §3 |
   | not cited | the claims of appointments that are not established (denied, expired) | explanatory, never required | [E] CL C1 (X-003) |

   - P-OH-1 (approved, qualified LABS-1.063): each established appointment's accepted claims **support that
     appointment** (component `appointments[i]`), conflict or not. In a conflict the **same claims are also
     conflicting** (component `conflict`), as the holders are each other's rivals, and so is the constraint's support.
     This is a legitimate cross-role membership (§0.4).
7. **Derivations and admissible premises**
   - [E] None are presented. No authority from an office, no office from an act (D2D §2).
8. **Refusals**
   - None documented. "The organisation profile is not installed" is a precondition (common P-5).
9. **Limitations and gaps**
   - [E] D-D-4 (no context containment).
   - [E] GAP-MULTI-2.

## Part B. Spatial transformations and frames

### Reader contracts: spatial transformations and frames (S, F)

Draft for LABS-1.062. Shared rules: `this document's §0` (labels, evidence roles, premise admissibility, refusals,
ordering). Evidence and full citations: `docs/stage-e/e2-reader-contracts/evidence-spatial.md`.

Citation abbreviations: **A1** `docs/core-0.4/stage-a1.md`; **A2** `docs/core-0.4/stage-a2.md`; **v0.2**
`docs/architecture/world-ontology-v0.2.md`; **Plan** `docs/plans/core-0.4-plan.md`; **IB-D**
`docs/core-0.4/pre-e-increment-b-design.md`; **IB** `docs/core-0.4/pre-e-increment-b.md`; **IC-D**
`docs/core-0.4/pre-e-increment-c-design.md`; **ID-D** `docs/core-0.4/pre-e-identity-design.md`; **E2-D**
`docs/stage-e/stage-e2-evaluation-design.md`; **INV** `docs/stage-e/stage-e-entry/e2-capability-inventory.md`;

Shared conventions for all four readers [E] (Plan 9.6; A2 "Conventions"): right-handed Cartesian frames; metres;
radians; unit quaternions (w, x, y, z), Hamilton product, active rotation; q and −q are the same rotation;
`frame-transform(parent P, child C)` maps C to P: p_P = R(q) p_C + t; composition T_AC = T_AB ∘ T_BC; inverse computed,
never stored; range boxes mapped by 8 corners (conservative); rotations exact; positions agree within 1e-9 m,
orientations by angular separation 2·atan2(‖v‖, |w|) under an angular tolerance. No INCOMPARABLE status (D-A2-4,
A2 decisions table).

---

### `transform_between(world, source, target, t, as_of=None, perspective='system', limit=None)`
**Serves:** S1-S6 (H) (E2-D 3.1). Gap probes S7 (GAP-SPATIAL-1), S8 (GAP-SPATIAL-3, -4); F9 (GAP-FRAME-4: one chain,
not the hierarchy).

1. **Inputs and conditions:**
   - TB-1 [E] `world`, `t`, `as_of`, `perspective` as common 0.2; edges are the `frame-transform` contents judged for
     that context (A2 "LABS-1.008 corrections / Edges"; A2 "Frame chains").
   - TB-2 [E] `limit`: the maximum number of edge examinations of one search, default 100,000, settable per call
     (A2 "Resource limit").
2. **Output fields and vocabulary:**

| Field | Type | Values | Label/source |
|---|---|---|---|
| `status` | Status | INFERRED, DISPUTED, UNKNOWN | [E] A2 "Outcomes"; E2-D 2 table |
| `transform` | (q, t) or None | the composed source→target transform (p_target = R(q) p_source + t); None when DISPUTED or no chain; an unverified candidate when truncated but reached | [E] A2 "Outcomes", "Results"; conventions Plan 9.6 |
| `chain` | list of steps | the shortest chain, each step `parent`, `child`, `direction` (`forward` child→parent / `inverse`), with its supporting attestations | [E] A2 "Search", "Conventions/Inverse"|
| `frames` | list of ids | frames along the chain | [E] A2 "Results" (field named)|
| `reason` | text or None | "no frame chain from X to Y"; "search truncated after N edge examinations (limit L) without reaching Y"; "verification incomplete: search truncated, other chains were not checked for agreement" | [E] A2 "Resource limit"|
| `search.complete` / `.truncated` | bool | always one of the two true | [E] A2 "Resource limit" |
| `search.verified` | bool | true when every route was checked | [E] A2 "Outcomes"|
| `search.cycle`, `.hops`, frames reached, edges examined, edges checked | ints/bool | as named | [E] A2 "Resource limit"|
| `search.inconsistent` | list | each inconsistent edge with its sources, translation gap (m) and angle gap (rad) | [E] A2 "Outcomes" |
| `rule` | text | `frame-transform/v1` | [E] A2 "Frame chains / Provenance"|

3. **Judgement and uncertainty:**
   - TB-6 [E] Breadth-first search, no hop limit, each frame reached once; cycles terminate (A2 "Search"; D-A2-3).
   - TB-7 [E] Every edge on any simple source–target route (the biconnected blocks on the route) is checked against
     the composed transforms, within 1e-9 m and the angular tolerance (A2 "Agreement, checked completely").
   - TB-8 [E] All consistent: INFERRED, `verified: true`. An inconsistent edge on a route: DISPUTED, no transform
     chosen. A disputed transform on any route: DISPUTED. A disagreement off every route: no effect (A2 "Outcomes").
   - TB-9 [E] Two accepted different transforms for one frame pair are disputed edges (`frame-transform` slot), so
     chains through them are DISPUTED (IB-D Q5; IB "Readers").
   - TB-10 [E] Cycles: `cycle: true`; consistent cycles INFERRED, inconsistent DISPUTED (A2 "Frame chains / Cycles").
   - TB-11 [E] Completed search, no chain: UNKNOWN, `complete: true`. Truncated before the target: UNKNOWN,
     `truncated: true`. Truncated but reached: transform returned as an unverified candidate only, UNKNOWN,
     `verified: false` (A2 "Resource limit", LABS-1.009). Never a silent "no chain".
   - TB-12 [E] Transforms are exact; no uncertainty on transforms (A2 "Known limitations"; GAP-SPATIAL-1).
4. **Visibility:**
   - TB-13 [E] Inherited snapshots, acceptance and supersession apply to transforms as to any content (A2 "Frame
     chains / Edges"). A variant's own transform overrides the inherited one; a base transform recorded after the
     branch is excluded (A2 "Position judgement / Time, perspective and worlds"; LABS-1.009 tests).
   - TB-14 [E] A relocalisation supersedes the transform; derived answers change from that knowledge time only (v0.2
     3.5 C8 and 7 C8; Plan 5 criterion A).
   - TB-15 [E] Frame chains are judged without same-as identity by design: frames cannot be declared the same (IB
     "Points decided" 6; ID-D 3.8, ID-8). on GAP-SPATIAL-5.
5. **Ordering and multiplicity:**
   - TB-17 [E] Exactly one chain is reported, the shortest (A2 "Search"). `chain` runs from source to target [E]
     (A2 "Results": "step by step").
   - TB-19 `search.inconsistent` is a multiset (common 0.9).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `chain[*].support` | status INFERRED | [E] A2 "Provenance" (cites every transform on the chain) |
| conflicting | `search.inconsistent[*].support` | status DISPUTED by an inconsistent edge | [E] A2 "Outcomes" |
| supporting (unverified) | `chain[*].support` | UNKNOWN, `verified: false`, transform returned | [E] A2 LABS-1.009 ("candidate only"); never authoritative |

7. **Derivations and admissible premises:**
   - TB-20 [E] Rule `frame-transform/v1`; premises are the transform attestations on the chain (A2 "Provenance";
     v0.2 3.5 C8). No derivation record is stored (Plan Stage A table; common 0.7).
   - TB-21 [E] Admissible premises: `frame-transform` steps that hold for the question's world, perspective, `as_of`
     and `t` (A2 "Edges"; common 0.7). A disputed transform is not admissible to yield a transform: the answer is
     DISPUTED with no transform (A2 "Outcomes").
8. **Refusals:** none documented. A missing chain is an UNKNOWN answer, never a refusal and never invented [E]
   (A2 "Frame chains / Missing"). Writer refusals of `relate_frames` (parent == child, non-unit quaternion) are
   writer-side and not reader refusals [E for the norm, Plan 9.6].

| Name | Condition | Exception / message | Established? | Source |
|---|---|---|---|---|
| — | — | — | — | — |

9. **Limitations and gaps:** [E] GAP-SPATIAL-1 (no transform uncertainty), -3 (quaternions only), -4 (no units on
   spatial content), -5; GAP-FRAME-1 (anchors not used in chains), -4 (no hierarchy) (INV 1-2; E2-D 4).
   [E] Every question loads all judged transforms of the world (A2 "Known limitations").

---

### `where(world, thing, frame, t, as_of=None, perspective='system', angle_tolerance=1e-9, limit=None)`
**Serves:** F1-F6 (H) (E2-D 3.2); X1 (H, via `measurements` → `where`) (E2-D 3.6). Gap probes F7 (GAP-FRAME-1, -2),
F8 (GAP-FRAME-3: must stay UNKNOWN between stated poses, E2-D 3.7), F10 (GAP-FRAME-6), GAP-SPATIAL-2, -6, -7, -8.

1. **Inputs and conditions:**
   - WH-1 [E] "Where is `thing` in `frame` at t", judged for the perspective; `where` is the position-specific
     interface because `holds` names no parameters (A2 "`holds` (D-A2-5)").
   - WH-2 [E text, D ruling] `angle_tolerance`: per-question policy (v0.2 Π), default 1e-9 rad (A2 "Orientation
   - WH-3 [E] `limit` as TB-2, applied to each candidate's search (A2 "Resource limit").
   - WH-4 [E] `world`, `t`, `as_of`, `perspective` as common 0.2.
2. **Output fields and vocabulary:**

| Field | Type | Values | Label/source |
|---|---|---|---|
| `status` | Status | STIPULATED, ASSERTED, INFERRED, DISPUTED, UNKNOWN, NOT_YET_KNOWN | [E] E2-D 2 table; IC-D 4 (`where` row) |
| `candidates` | list | one per position statement that holds for the perspective at t and can be related to `frame` | [E] A2 "Position judgement / Candidates" |
| `candidates[*].x/.y/.z` | (lower, upper) metres or None | mapped range; None when the candidate's chains disagree | [E] A2 "Results"; "Ranges" |
| `candidates[*].orientation` | quaternion or None | orientation in `frame` | [E] v0.2 3.5 (optional orientation)|
| `candidates[*].status` | Status | ASSERTED/STIPULATED (direct, by basis), INFERRED (derived), DISPUTED (chain disagrees), UNKNOWN (truncated) | [E] A2 "Measurement uncertainty"; "Truncated results in `where`" |
| `candidates[*].direct` | bool | stated in `frame` vs derived | [E] A2 "Candidates"|
| `candidates[*].chain`, `.search` | as TB | the candidate's frame chain and search | [E] A2 "Results" |
| `candidates[*].verified` | bool | false for a candidate from a truncated search | [E] A2 "Truncated results in `where`" |
| `candidates[*].position_support` | ids | the position attestations | [E] A2 "Provenance"|
| `conflicts` | list of candidate pairs | verified conflicting pairs | [E] A2 "Disjoint" ("conflicting pairs are listed") |
| `conflict_details[*].kind` | text | `disjoint ranges`, `orientations differ`; with separation and tolerance used; `unverified` flag | [E] A2 "Reporting"; "Truncated results" |
| `verified`, `reason` | bool, text | false and "verification incomplete…" while any candidate is unverified or a truncated search left a statement incomparable | [E] A2 "Truncated results in `where`" |
| `incomparable` | list | statements whose frame cannot be related to `frame`, each with its `search` | [E] A2 "Different frames"; "Results"; D-A2-4 |
| `alternatives` | ids | unreviewed claims | [E] A2 "Time, perspective and worlds" |
| `judgement` | text or None | `compatible` [E] (A2 "Overlapping")| — |
| `angle_tolerance` | float | the tolerance used | [E] A2 "Reporting" |

3. **Judgement and uncertainty:**
   - WH-5 [E] Candidates are compared, never merged: nothing averaged, intersected or weighted (A2 "Nothing is
     reconciled"; "Candidates").
   - WH-6 [E] Identical ranges are one content: one candidate with several supporting attestations (A2 "Identical").
   - WH-7 [E] Overlapping ranges, including touching ones, are compatible; each keeps its own range (A2
     "Overlapping"). Overlap means "can both be true", not agreement (A2 "Known limitations").
   - WH-8 [E] Disjoint ranges, or orientations whose separation exceeds `angle_tolerance`, conflict: DISPUTED, pairs
     listed (A2 "Disjoint"; v0.2 5.3 rule 2). Direct candidates carry their own support's status so that the
     question's tolerance decides orientation conflicts (B "One functional judgement").
   - WH-9 [E] Status: DISPUTED on a verified conflict (or a verified DISPUTED candidate); otherwise UNKNOWN if
     unverified; otherwise the most direct status among direct candidates; INFERRED when only derived (IC-D 4; A2
     "Measurement uncertainty"; "Truncated results").
   - WH-10 [E] An unverified candidate keeps its position but cannot create a conflict (listed `unverified: true`)
     nor support an authoritative answer; verified conflicts still decide (A2 LABS-1.009).
   - WH-11 [E] No candidate: UNKNOWN when position records about the thing are visible, NOT_YET_KNOWN otherwise
     (v0.2 5.6; E2-D 2 table).
   - WH-12 [E] Uncertainty is the ranges, propagated conservatively; a widened range can hide a conflict, never
     invent one (A2 "Known limitations"; GAP-SPATIAL-2).
4. **Visibility:**
   - WH-14 [E] Only statements that hold at t for the perspective count; no persistence beyond a stated interval
     (A2 "Time, perspective and worlds"; Plan 9.6 "no extrapolation"; E2-D F4).
   - WH-15 [E] A variant's own position or transform overrides the inherited one; the actual world is unaffected
     (A2 "Time, perspective and worlds"; demonstration table).
   - WH-16 [E] As known before an acceptance or supersession (`as_of`), the earlier answer stands (A2 demonstration;
     v0.2 C8).
   - WH-17 [E] The thing is judged with its established same-as group (ID-D ID-8); frame chains are not (TB-15).
 (not fixed by the contract).
5. **Ordering and multiplicity:**
   - WH-19 [E] Several statements in different frames are separate candidates even when they map to the same range
     (A2 "Candidates": each statement is a candidate).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `candidates[*].position_support` | every candidate that has a position (x not None) | [E] A2 "Provenance"; "Identical" |
| supporting | `candidates[*].chain[*].support` | derived candidates (`direct` false) with a position | [E] A2 "Provenance" ("every transform on its chain") |
| conflicting | `position_support` and `chain[*].support` of both candidates named in each `conflicts` pair | status DISPUTED by a verified conflict | [E] A2 "Disjoint" (pairs listed); split from supporting per common 0.4 [P-1] |
| conflicting | `candidates[*].search.inconsistent[*].support` | a candidate DISPUTED because its chains disagree | [E] A2 "Outcomes" |
| alternative | `alternatives` | always; never supporting | [E] A2 "Time, perspective and worlds"; v0.2 6.2 |
| alternative | `incomparable[*].support` | always; never supporting or conflicting | [E] A2 "Different frames" (never guessed); D-A2-4; role per common 0.4 |
| alternative | pairs in `conflict_details` with `unverified: true`, and supports of unverified candidates | answer UNKNOWN or DISPUTED by other pairs | [E] A2 LABS-1.009 ("cannot create a conflict"; "cannot support an authoritative answer") |
| supporting (DISPUTED answer) | supports of candidates in no `conflicts` pair | DISPUTED | [P] P-WH-1: they are still evidence for their own candidate, scored as supporting |

7. **Derivations and admissible premises:**
   - WH-20 [E] A derived candidate presents rule `frame-transform/v1` with premises = its position attestation(s) and
     every transform attestation on its chain; it is INFERRED (A2 "Provenance"; v0.2 3.5 C8). The position statement
     **is** a premise (A2 "Provenance").
   - WH-21 [E] Admissible premises: `positioned-in` and `frame-transform` steps visible and usable for the question's
     world, perspective, `as_of` and `t` (common 0.7). A disputed transform is not admissible to yield a position: the
     candidate has no position and is DISPUTED (A2 "Ambiguous"; "Results").
   - WH-23 [E] Direct candidates present no derivation.
8. **Refusals:** none documented. Unrelatable frames give `incomparable` entries, never a refusal or a guess [E]
   not a `where` refusal) (not fixed by the contract).

| Name | Condition | Exception / message | Established? | Source |
|---|---|---|---|---|
| — | — | — | — | — |

9. **Limitations and gaps:** [E] conservative range propagation (GAP-SPATIAL-2); orientations exact, tolerance per
   question (A2 "Known limitations"); no best estimate; truncated searches give unverified candidates; about 32-35
   queries, cross-world growth. Gap ids: GAP-SPATIAL-6, -7, -8; GAP-FRAME-1, -2, -3, -6; GAP-MULTI-2, -5
   (INV 1, 2, 6; E2-D 4). No identity from proximity [E] (A2 "No identity from proximity").

---

### `poses(world, thing, t, as_of=None, perspective='system')`
**Serves:** F1, F3, F4 as a supporting listing (E2-D 3.2 lists `poses` under F); gap probes GAP-SPATIAL-8,
GAP-FRAME-6.

1. **Inputs and conditions:**
   - PO-1 [E] The thing's stated positions at t, read through `facts_about`, so judged for world, perspective,
     knowledge time and valid time (A1 "API").
   - PO-2 [E] All frames; no frame parameter and no derivation (A1 "API"; derivation is `where`'s, A2 "Frame chains").
2. **Output fields and vocabulary:**

| Field | Type | Values | Label/source |
|---|---|---|---|
| `frame` | id | the stated frame | [E] A1 schema table (`positioned-in(positioned, frame)`) |
| `x`, `y`, `z` | (lower, upper) metres | as stated (lower = upper: exact) | [E] A1 schema table; Plan 9.6 |
| `orientation` | quaternion (w, x, y, z) or None | as stated | [E] A1 schema table |
| `status` | Status | ASSERTED, STIPULATED, INFERRED, DISPUTED | [E] A1 "API"; IB-D 4 (disputed entries marked DISPUTED) |
| `support` | ids | the deciding attestations | [E] B "One functional judgement"; IB-D 2.2 |
| `conflicts` | ids | rivals under the (positioned, frame) slot | [E] B "One functional judgement"; A2 "The same rule everywhere" |
| `support_status` | Status | status before constraints; DISPUTED for a polarity dispute | [E] B "One functional judgement"; IB-D 2.4 |

3. **Judgement and uncertainty:**
   - PO-3 [E] Disjoint positions of one thing in one frame (or orientations differing beyond the default 1e-9 rad)
     are DISPUTED with their rivals in `conflicts` (A2 "The same rule everywhere", "Where it applies"; IB-D 6 table).
 (not fixed by the contract).
   - PO-4 [E] Polarity-disputed positions are listed in place, marked DISPUTED. (not fixed by the contract).
   - PO-5 [E] Ranges are reported as stated; nothing reconciled (A2 "Nothing is reconciled").
4. **Visibility:**
   - PO-6 [E] As `facts_about`: holding or disputed at t, with world inheritance, acceptance and supersession (A1
     "API"; IB-D 2.1). An ended position does not hold after its end (A1 "The reference world / Time").
   - PO-7 [E] `facts_about` uses the context's identity (ID-D 3.8). (not fixed by the contract).
     `positioned`; effect on aliases unverified.
5. **Ordering and multiplicity:**
   - PO-8 [E] Several positions in one frame are all listed (A1 D-A1-2; A2 "Identical": identical ranges are one
     entry with several supporting attestations).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `[*].support` | every entry | [E] B "One functional judgement" |
| conflicting | `[*].conflicts` | entry DISPUTED by the slot | [E] B; A2 "The same rule everywhere"; split per common 0.4 [P-1] |
| conflicting | the denials of a polarity dispute | entry DISPUTED by polarity | [E] IB-D 4 requires them|

7. **Derivations and admissible premises:** none presented [E] (A1 "API": stated positions only).
8. **Refusals:** none documented.

| Name | Condition | Exception / message | Established? | Source |
|---|---|---|---|---|
| — | — | — | — | — |

9. **Limitations and gaps:** [E] every new position is a new proposition (D-A1-5, U-3); GAP-SPATIAL-8 (`holds` cannot
   single out a position), GAP-FRAME-6 (parts not positioned through their assembly) (INV 1-2).

---

### `frame_info(world, frame, t, as_of=None, perspective='system')`
**Serves:** F9 one hop only (gap probe GAP-FRAME-4) (E2-D 3.2); supporting listing for S and F fixtures; gap probes
GAP-FRAME-1, -5.

1. **Inputs and conditions:**
   - FI-1 [E] What is known about a frame at t: its anchor, its stored transforms to parent and child frames, and
     what is positioned in it, judged through `facts_about` (A1 "API"; A1 "Selected results": "f-bench: anchored to
     bench-1; in f-workshop: translation …, rotation … [ASSERTED]").
   - FI-2 [E] `world`, `t`, `as_of`, `perspective` as common 0.2. Frames are not subject to same-as (ID-D 3.8).
2. **Output fields and vocabulary:**

| Field | Type | Values | Label/source |
|---|---|---|---|
| `anchored_to[*].anchor`, `.status` | id, Status | the anchor; DISPUTED for two accepted anchors | [E] A1 schema table (functional, one anchor at a time); A1 "Tests" |
| `parents[*]` / `children[*]` | parent or child id, `translation` (m), `rotation` (w,x,y,z), `status`, `support` | transforms as stored, one hop, not composed | [E] A1 "Selected results"; IB-D Q5 (slot applies)|

3. **Judgement and uncertainty:**
   - FI-3 [E] Two different accepted transforms for one pair are DISPUTED (`frame-transform` slot) (IB-D Q5; A2 "The
     same rule everywhere"). A second accepted anchor is DISPUTED (A1 "Tests"; IB-D 2.3).
   - FI-4 [E] Polarity-disputed content is listed and marked DISPUTED (IB-D 4; IB "Readers").
4. **Visibility:** FI-6 [E] as `facts_about` (A1 "API"; IB-D 2.1): inheritance, acceptance, supersession, `as_of`.
5. **Ordering and multiplicity:** FI-7 (not fixed by the contract).
   `facts_about` order; no design order. Compared as multisets (common 0.9).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `parents[*].support`, `children[*].support` | every transform entry | [E] A1 "Selected results" (status shown); IB-D 2.2 |
| conflicting | rivals of a DISPUTED transform or anchor | entry DISPUTED | [E] IB-D 4 requires citing them|

7. **Derivations and admissible premises:** none presented [E]: transforms are stored values, not composed (A1 "API";
   composition is A2's `transform_between`).
8. **Refusals:** none documented. An unknown frame id is a precondition question, not a refusal (common 0.8 [P-5]).

| Name | Condition | Exception / message | Established? | Source |
|---|---|---|---|---|
| — | — | — | — | — |

9. **Limitations and gaps:** [E] GAP-FRAME-1 (anchoring has no geometric effect: reported only), GAP-FRAME-4 (one hop,
   no hierarchy), GAP-FRAME-5 (no history reader for a frame) (INV 2; E2-D 4).

## Part C. Measurement and calibration

### Reader contracts: measurement family (draft, LABS-1.062)

These are the reader contracts for `measurements` (ME), `compare_measurements` (CM), `convert` (CV),
`laboratory.calibration_status` (CS) and `laboratory.measurement_calibration` (MC).

- **Status of statements:** labels [E], [P] and (not fixed by the contract).
- **Evidence:** the full citations and line numbers are in `docs/stage-e/e2-reader-contracts/evidence-measurement.md` (cited below as "src §n").
- **Shared context:** common §0.2 to §0.9 apply throughout.
- **Repository paths:** relative to `typedb-semantic-world-model`.

Abbreviations used in citations:
- **v0.2:** `docs/architecture/world-ontology-v0.2.md`;
- **stage-c:** `docs/core-0.4/stage-c.md`;
- **d3-design:** `docs/core-0.4/stage-d3-design.md`;
- **d3:** `docs/core-0.4/stage-d3.md`;
- **incB:** `docs/core-0.4/pre-e-increment-b-design.md`;
- **incC:** `docs/core-0.4/pre-e-increment-c-design.md`;
- **incC-report:** `docs/core-0.4/pre-e-increment-c.md`;
- **E2:** `docs/stage-e/stage-e2-evaluation-design.md`;
- **inv:** `docs/stage-e/stage-e-entry/e2-capability-inventory.md`;
- **harness:** `docs/stage-e/stage-e2-harness-review.md`.

---

### `measurements(world, bearer, quality, t=None, as_of=None, perspective=system)`

**Serves:**
- M1 and M4 (H), and X1 as its first step (E2 §3.3, §3.6);
- gap probes GAP-MEAS-6, GAP-MEAS-7 and GAP-MEAS-11 (inv §M).

1. **Inputs and conditions**
   - [E] The question is asked by (bearer, quality kind). A quality is the slot, not an instance: v0.2 §3.3
     clarification C; D-D-8 (`stage-d-review.md` §6).
   - [E] It takes the common context ⟨world, perspective, as_of⟩ (common §0.2).
   - [E] The fixture defines a unit and a quality kind of the same dimension (stage-c C1 `measure`).
2. **Output fields and vocabulary**
   - The answer is a list of entries, one per visible `has-quality` attestation about (bearer, quality).

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `[*].attestation` | id | — | [E] stage-c D-C-2 (the attestation is the unit of provenance) |
   | `[*].kind` | str | `measurement` (rests on records) / `statement` (no record) | [E] stage-c C0 "stay separate"; C1 API |
   | `[*].range` | (float, float) | [v − ku, v + ku] in the dimension's SI unit | [E] v0.2 §3.3; D-C-1 |
   | `[*].unit` | id | the SI unit | [E] D-C-1; stage-c C0 units |
   | `[*].coverage_level` | float | a function of k (k = 2 ≈ 0.954) | [E] v0.2 §3.3, C4|
   | `[*].acceptance` | str | accepted / unreviewed / rejected / retracted / superseded | [E] v0.2 §5.6; incB §2.2 |
   | `[*].records[*].raw_value`, `raw_unit`, `standard_uncertainty`, `coverage_factor`, `conditions`, `calibration` | — | as written; conditions as exact text | [E] D-C-1, D-C-7; v0.2 clarification B |
   | `[*].records[*].report` | str | whether the `reports` claim is accepted | [E] stage-c (judged parts) |
   | `[*].records[*].activities[*].start`, `end`, `operator`, `instrument` | Window / ids | from the activity's account | [E] stage-c provenance read|

   - [E] No answer status is given: this is a collection, and rule C folds nothing (incC §4, `measurements` row).
3. **Judgement and uncertainty**
   - [E] The range carries the measurement uncertainty. Credence and stance are separate, and calibration doubt never
     widens a range (v0.2 §3.3 "two kinds of uncertainty"; plan acceptance criterion C).
   - [E] Nothing is combined or reconciled (v0.2 clarification B).
   - [E] Each entry's acceptance is judged per perspective. The rests-on link, the record values, the operator and the
     instrument are not judged (stage-c).
4. **Visibility**
   - [E] Supersession is per perspective. A perspective keeps the original until it accepts the correction, and the
     superseded attestation keeps its own record (stage-c "Correction"; core-0.3 supersession).
   - [E] One measurement is visible at `as_of` all together or not at all (D-C-8, one transaction time).
   - [E] Variant worlds inherit attestations with their links (stage-c "Hypothetical worlds"; v0.2 §6.2).
5. **Ordering and multiplicity**
   - [E] One entry per attestation, not per content (stage-c D-C-2 probe case 1).
   - [E] Records and attestations are many-to-many (stage-c).
   - The list is a multiset (common §0.9). (not fixed by the contract).
     Validation: random ids).
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `[kind=measurement, usable=true].attestation` | always | [P] P-ME-1, from v0.2 §6.2 (usable attestations support); harness §5.1 |
   | alternative | `[usable=false].attestation` (unaccepted, superseded, rejected, retracted, non-supporting stance, denials) | always | [E] v0.2 §6.2 |
   | not cited | `records[*].record`, `activities[*].activity` (not attestations); `produced` and `reports` ids (not returned) | — | [E] stage-c D-C-2 (structural link, not an attestation) |

   - For M4, gold names the current value by its `[acceptance=accepted]` entry, and history by
     `[acceptance=superseded]` (common §0.5 names `<step>`).
7. **Derivations and admissible premises**
   - [E] None presented. The content has basis observation, and conversion to SI on write is not an inference
     (D-C-1). no derivation record exists (deferred): no derivation record exists.
   - [E] Any `{rule, premises}` in the answer is fabricated (harness §9.3).
8. **Refusals**
   - None documented. An unknown bearer or quality returns an empty list. (not fixed by the contract).
9. **Limitations and gaps**
   - GAP-MEAS-6: `has-quality` is not a slot.
   - GAP-MEAS-7: no current-value or trend reader.
   - GAP-MEAS-8: N+1 reads.
   - GAP-MEAS-10: no "undermines" link (G-3).
   - GAP-MEAS-11: no derivation record exists (deferred).

---

### `compare_measurements(world, bearer, quality, t=None, as_of=None, perspective=system)`

**Serves:**
- M2 and M3 (H) (E2 §3.3);
- gap probes M7 (GAP-MEAS-1), M8 (GAP-MEAS-4), GAP-MEAS-2 and GAP-MEAS-3.

1. **Inputs and conditions**
   - [E] The same as `measurements`. It compares the measurements the perspective accepts (v0.2 clarification B;
     stage-c C1 API).
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `status` | Status | DISPUTED / ASSERTED / STIPULATED / INFERRED / UNKNOWN / NOT_YET_KNOWN | [E] v0.2 clarification B; incC §4 (`compare_measurements` row); D-C-5 |
   | `pairs[*].relation` | str | `possibly compatible` / `incompatible` / `incomparable` | [E] v0.2 clarification B table; DR-07; stage-c C0 |
   | `pairs[*].a`, `pairs[*].b` | attestation ids | the two compared measurements | [E] v0.2 ("both ranges, each with its evidence") |
   | `pairs[*].reason` | str or None | the reason for incomparability (units, coverage levels, conditions, valid times) | [E] that a reason is given (v0.2)|
   | `measurements` | list of `measurements` entries | the compared (usable) measurements | [E] stage-c C1; fields as ME §2 |
   | `alternatives` | list | unaccepted measurements | [E] v0.2 §6.2|
   | `statements` | list | entries with no result record | [E] stage-c C0 ("listed apart, never compared") |

3. **Judgement and uncertainty**
   - [E] Pairs are judged as follows (v0.2 clarification B table):
     - comparable and the ranges overlap: possibly compatible, which is not agreement and gives no intersection;
     - comparable and disjoint: incompatible, giving DISPUTED;
     - not comparable: incomparable, with the reason.
   - [E] Incomparable when the coverage levels differ (no harmonisation: v0.2 C4; GAP-MEAS-3), the condition texts
     differ (D-C-7) or the SI units differ.
   - [E] Overlap uses closed bounds (plan §4: `$la <= $ub; $lb <= $ua`).
   - [E] Calibration never enters the comparison (D-D3-2; d3 §3 "Never invalidating"; "calibration states that
     matter" are deferred, `stage-d-review.md` D3 Df).
   - [E] The status is decided in this order:
     - DISPUTED if any comparable pair is incompatible;
     - otherwise the core rule over the compared measurements (observation gives ASSERTED; stipulation gives
       STIPULATED);
     - otherwise UNKNOWN when something is held and NOT_YET_KNOWN when nothing is.

     Sources: incC §4; D-C-5; common §0.3.
   - [E] Nothing is combined. INFERRED would need a named reconciliation policy, and none exists (v0.2 §3.3; GAP-MEAS-4).
     - v0.2 §5.3: an accepted assertion and an accepted denial of a content make it DISPUTED;
     - stage-c "Disputes" names "a polarity denial or disjoint ranges" as rival measurement attestations.

     - it excludes polarity-false attestations from `usable`, so an accepted denial resting on a record is listed in
       `alternatives` (described as "unaccepted") and never makes the status DISPUTED;

     Adjudicated as a semantic defect: questions about denied measurements that
     expect the contract's DISPUTED answer are **eligible**.
4. **Visibility**
   - [E] As `measurements`; two perspectives can give different comparisons (stage-c "Disputes"; d3-design P2).
5. **Ordering and multiplicity**
   - [E] There is one comparison per pair of compared measurements (v0.2: pairwise).
   - Gold picks a pair by its unordered set {a, b}; `pairs` and every list are multisets.
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `measurements[*].attestation`, except those in an incompatible pair | always | [E] v0.2 ("both ranges, each with its evidence"); [P] P-CM-1 (exclusion) |
   | conflicting | `pairs[relation=incompatible].a`, `.b` | status DISPUTED | [E] v0.2 ("DISPUTED, citing both"); [P] P-CM-1 (role per common §0.4) |
   | alternative | `alternatives[*].attestation`, `statements[*].attestation` | always | [E] v0.2 §6.2; stage-c C0; harness §5.1 |
   | not cited | records, activities, certificates | — | [E] D-D3-2 |

7. **Derivations and admissible premises**
   - [E] None presented. The relations are query-time and never stored (v0.2 E9).
8. **Refusals**
   - None documented.
9. **Limitations and gaps**
   - GAP-MEAS-1: no specification or tolerance check (M7: probe expects no pass/fail field).
   - GAP-MEAS-2: no condition ontology.
   - GAP-MEAS-3: no coverage harmonisation.
   - GAP-MEAS-4: no estimate (M8).
   - GAP-MEAS-8: N+1 reads.

---

### `convert(value, unit, to=None)`

**Serves:**
- M5 (H) (E2 §3.3);
- gap probe M9 (GAP-MEAS-5).

1. **Inputs and conditions**
   - [E] Takes a number and a defined unit; `to` must be a unit of the same dimension (stage-c C1 API "refused across
     dimensions"; plan Stage C units).
   - [E] Units are timeless reference systems (v0.2 §3, abstract entities). There is no world, perspective, `as_of`
     or `t`.
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | (value) | float | the value expressed in `to` | [E] stage-c C1 API; E2 M5 |

   - The answer carries no status and no evidence.
3. **Judgement and uncertainty**
   - [E] A unit owns `dimension`, `si-factor` and `si-offset` (plan Stage C; stage-c C0).
   - [E] Round trips are an acceptance criterion (plan §5 C).
   - No uncertainty is propagated: the input is a value, not a range.
4. **Visibility**
   - [E] None. Reference data is timeless. (not fixed by the contract).
5. **Ordering and multiplicity**
   - Not applicable.
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | not cited | — | always | [E] no attestation is involved (v0.2 §3 reference systems); harness §5.1 |

7. **Derivations and admissible premises**
   - [E] None presented. "Conversions are derived" (D-C-1) means computed rather than stored; no derivation record is
     involved. Any `{rule, premises}` is fabricated.
8. **Refusals**

   | Name | Condition | Exception / message | Established? | Source |
   |---|---|---|---|---|
   | cross-dimension | `to` has another dimension than `unit` | `ValueError` "cannot convert …" | **yes** [E] | stage-c C1 API; harness §9 |
   | compound unit | N ↔ kg·m/s² | (none: no such unit can be defined) | not a refusal; the gap is unsupported | E2 M9; GAP-MEAS-5 |

9. **Limitations and gaps**
   - GAP-MEAS-5: single-dimension, affine only; no prefixes or algebra.

---

### `laboratory.calibration_status(wm, world, instrument, t, as_of=None, perspective=system)`

**Serves:**
- M6, calibration status alone (A, as E1 `calibrated`) (E2 §3.3);
- within MC, and X2 as its first step via MC;
- gap probes GAP-MEAS-9 and GAP-MEAS-10.

1. **Inputs and conditions**
   - [E] An instrument and a valid time `t` (required); the common context (d3-design §3; d3 §2).
   - [E] A calibration is `calibration-of(certificate, calibrated)`, attested over the certificate's valid time and
     resting on the certificate (D-D3-1; D-D-7).
   - [E] A `calibrate` step without an end holds until superseded (E1 CLARIFICATIONS C2).
   - [P] P-5: the laboratory profile must be installed (precondition, see §8).
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `judgement` | str | established / expired / denied / disputed / not yet effective / not established | [E] D-C-3; d3 §3 table; TEMPLATES (applicability) |
   | `holds` | bool or None | True / False / None, as the judgement | [E] stage-c C2 table; incC §3.1 |
   | `status` | Status | core rule over the deciding support; DISPUTED; UNKNOWN (something found) / NOT_YET_KNOWN (nothing found) | [E] incC §3.1, C-1 to C-3; D-C-5 |
   | `support` | sorted ids | the deciding claims; empty for disputed and undecided answers | [E] C-4; incC-report "Points decided" 2 |
   | `certificates[*].certificate`, `reference`, `judgement`, `status`, `holds`, `evidence` | — | every certificate naming the instrument; reference as exact text (None never matches) | [E] d3 §2, §3 |
   | `in_force` | ids | certificates whose own judgement is established | [E] as a field (d3 §2)|

3. **Judgement and uncertainty**
   - [E] Rule Q is applied in this order (incC §3.1; C-1, C-2, C-3):
     1. disputed: a disputed holding, or an established holding beside an accepted denial;
     2. established: the core rule over the union of the established holdings' support;
     3. denied or expired: the union of the denied and expired holdings' support;
     4. not yet effective, or not established.
   - [E] Undecided holdings beside an established one leave it established, and an expired holding is not a conflict
     (C-3).
   - [E] One disputed certificate beside one in force makes the answer disputed overall (d3 §8).
   - [E] Per-content labels follow incB §2.4:
     - an unknown end is not established;
     - unreviewed (pending) is not established;
     - rejected, retracted or superseded alone are not established.
   - [E] "Not established" with no certificates means no calibration is recorded at all (d3 §3).
4. **Visibility**
   - [E] Valid time is the attestation's interval (d3-design §1).
   - [E] Perspective: B7 is disputed for the system and denied for the quality office (d3 §3).
   - [E] Knowledge time: B7 is established before the denial was recorded (d3 §3).
   - [E] Variant world: a stipulated renewal is established (STIPULATED) there, and both certificates are listed; the
     actual world is unchanged (d3 §3).
5. **Ordering and multiplicity**
   - [E] One entry per calibration content (certificate).
   - [E] The answer is independent of order and of ids (incC-report tests E7/E7b). `support` is sorted (C-4).
   - `certificates` is a multiset; the sort by certificate id is (not fixed by the contract).
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `support[*]` | judgement established, expired or denied | [E] C-4; incC §3.1 |
   | conflicting | `certificates[*].evidence[acceptance=accepted].attestation` of the holdings that make the answer disputed (the accepted assertion and the accepted denial) | judgement disputed (support empty) | [P] P-CS-1 (common §0.4)|
   | alternative | `certificates[*].evidence[acceptance≠accepted].attestation` (unreviewed, rejected, retracted, superseded) | always | [E] v0.2 §6.2; C-3 |
   | not cited | `certificates[*].certificate` (an information object, not an attestation) | — | [E] d3 §1; D-D-7 |

7. **Derivations and admissible premises**
   - [E] None presented. Calibration is a content judged like a capability; no rule is applied (d3 §2 "Shared
     judgement"; no derivation record exists (deferred)).
8. **Refusals**

   | Name | Condition | Exception / message | Established? | Source |
   |---|---|---|---|---|

9. **Limitations and gaps**
   - GAP-MEAS-9: the reference is text, checked as exact text (G-6).
   - GAP-MEAS-10: no "undermines" relation (G-3).
   - Calibration aggregation follows capable() (d3 §8).

---

### `laboratory.measurement_calibration(wm, world, bearer, quality, t=None, as_of=None, perspective=system)`

**Serves:**
- M6 (H) (E2 §3.3);
- X2 as its first step (E2 §3.6);
- gap probes GAP-MEAS-9 and GAP-MULTI-2.

1. **Inputs and conditions**
   - [E] Bearer and quality as `measurements`, plus the common context (d3 §2).
   - [E] Calibration at measurement time is computed from the activity's instrument and time. There is no link from
     record to certificate (D-D3-2).
   - [P] P-5 for the profile.
2. **Output fields and vocabulary**
   - The answer is a list of rows, one per measurement record and activity instrument.

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `[*].record`, `[*].attestation`, `[*].instrument`, `[*].activity` | ids | — | [E] d3 §2 ("per measurement record and activity instrument")|
   | `[*].acceptance`, `[*].usable` | — | copied unchanged from `measurements` | [E] d3 §2, §3 "Never invalidating" |
   | `[*].stated_reference` | str or None | the record's `calibration-ref`, as exact text | [E] D-D3-2; G-6 |
   | `[*].attested` | `calibration_status` answer, or None | judged at the activity's start; includes `support` | [E] d3 §2; incC-report "Readers"|
   | `[*].reference_check.check` | str | `matches a certificate` / `no certificate with the stated reference` / `no reference stated` / `no certificate recorded for the instrument` / `no instrument recorded` | [E] d3 §3 reference checks; d3 §6a item 3 |
   | `[*].reference_check.certificates[*]` | certificate and judgement | the matching certificates, each with its own judgement | [E] d3 §3 ("with that certificate's judgement") |
   | `[*].at` | time | the instant at which calibration is judged | [E] the activity's start (D-D3-2)|

3. **Judgement and uncertainty**
   - [E] Calibration never invalidates, discards or downgrades a measurement. The stated reference and the attested
     calibration are reported side by side and never reconciled (D-D3-2; G-6; d3 §3).
   - [E] `attested` uses CS's judgements (incC §4: "inherits").
   - [E] Calibration doubt is not measurement uncertainty (v0.2 §3.3).
4. **Visibility**
   - [E] Calibration is judged at the activity's start (d3-design §1; D-D-7).
   - [E] The activity's times come from its account and depend on the perspective (stage-c).
   - [E] Perspective, `as_of` and world apply to both sides (d3 §3, hypothetical renewal).
5. **Ordering and multiplicity**
   - [E] One row per (record, activity instrument) (d3 §2).
     - one row per measurement attestation × record × activity × instrument, so a shared record gives one row per
       attestation;
     - rows with activity None or instrument None;
     - no rows for statements;
     - the sort by (record, instrument).
   - Rows are a multiset; gold selects a row by `[record=…, instrument=…]`.
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `[usable=true].attestation` | always | [P] P-MC-1 (as ME P-ME-1); harness §5.1 |
   | supporting | `[*].attested.support[*]` | attested judgement established, expired or denied | [E] C-4 (inherited) |
   | conflicting | as CS row "conflicting", under `[*].attested.certificates` | attested judgement disputed | [P] P-CS-1|
   | alternative | `[usable=false].attestation`; unaccepted certificate claims | always | [E] v0.2 §6.2 |
   | not cited | `reference_check.certificates[*].certificate`, `stated_reference` (text, not evidence); records and activities | — | [E] G-6 (reported, never reconciled) |

7. **Derivations and admissible premises**
   - [E] None presented. This is a fixed composition: measurements, then the activity start, then calibration status
     (d3 §2; D-D3-2). No rule is recorded.
8. **Refusals**

   | Name | Condition | Exception / message | Established? | Source |
   |---|---|---|---|---|

9. **Limitations and gaps**
   - GAP-MEAS-8: 411 queries for sample-12.
   - GAP-MEAS-9: the reference is text.
   - GAP-MULTI-2: which instant counts.

## Part D. Causation, change and process

### Reader contracts: causation, change and process (C and P families), draft for E2-D3

Draft for the owner's review. The shared rules are in `this document's §0` (0.1-0.9). The specification evidence and
its full citations are in `docs/stage-e/e2-reader-contracts/evidence-causal.md`.

Short names for the sources:

| Short name | File |
|---|---|
| SB | `docs/core-0.4/stage-b.md` |
| V02 | `docs/architecture/world-ontology-v0.2.md` |
| PLAN | `docs/plans/core-0.4-plan.md` |
| IBD | `docs/core-0.4/pre-e-increment-b-design.md` |
| IB | `docs/core-0.4/pre-e-increment-b.md` |
| ICD | `docs/core-0.4/pre-e-increment-c-design.md` |
| IC | `docs/core-0.4/pre-e-increment-c.md` |
| DI | `docs/core-0.4/deferred-issues.md` |
| E2D | `docs/stage-e/stage-e2-evaluation-design.md` |
| E2DEC | `docs/stage-e/stage-e2-decisions.md` |
| INV | `docs/stage-e/stage-e-entry/e2-capability-inventory.md` |
| HR | `docs/stage-e/stage-e2-harness-review.md` |
| R2 | `docs/stage-e/e1-reconciliation-design.md` §R2 |

### Shared Stage B rules (every reader below)
- **[E] Four distinctions are kept apart in the data and in every answer** (SB "B0: architecture review", the
  distinctions table; approved as B-arch, LABS-1.011):
  - occurrence vs description;
  - asserted effect vs accepted change;
  - succession vs causation;
  - a source's account vs the perspective's judgement: "every claim lists its attestations (attester, polarity, basis,
    acceptance state)".
- **[E] Causation is asserted, never inferred:** not from temporal order, not from co-reference alone, not transitively
  (V02 §3.2 "Participants, causes, effects, changes"; PLAN §9.3).
- **[E] None of these is required.** A state may hold with no known initiating event, and an event may have no known
  effect (V02 §3.2; V02 §7 C5).
- **[E] Causal and effect claims are timeless contents,** judged by acceptance, polarity, world and knowledge time
  (SB D-B-2; V02 §4.4).
- **[E] The claims vocabulary** is the canonical labelling (IBD §2.4 table): `accepted`, `disputed`, `denied`,
  `unreviewed`, `not yet effective`, `not established`, `unknown`, and for an unaccepted claim its best state
  (`rejected`, `retracted`, `superseded`).
- **[E] Occurrence existence** is judged only from attestations of its own existence (SB Occ-1, LABS-1.012). An
  accepted account of a denied occurrence stays visible; claims involving a denied occurrence do not apply (SB Occ-2).
- **[E] An event's times are its accepted occurrence interval,** never the recording time (SB B-time, LABS-1.016).
  Only an account the perspective can use gives times (SB D-B-6).
- **[E] Selective and full-load paths give identical answers** (PLAN §4).

---

### `causes_of(world, effect, t, as_of=None, perspective=SYSTEM)`
**Serves:**
- C1 and C2 (H) (E2D §3.4);
- part of X4 (E2D §3.6, through `explain`);

1. **Inputs and conditions:**
   - `t` is the valid time at which claims and occurrence statuses are judged [E] (common 0.2).
   - The reader is keyed on the effect only: there is no forward reader [E] (INV GAP-CAUSE-2).
   - World, perspective and `as_of` follow common 0.2 [E].
2. **Output fields and vocabulary** (one entry per causal claim):

| Field | Type | Values | Label/source |
|---|---|---|---|
| `[i].cause`, `[i].effect` | id | the claim's players (`effect` is the queried id or the target it was lifted from) | [E] SB "Schema and API" ("every causal claim, direct or lifted") |
| `[i].level` | str | `description`, `occurrence`, `mixed` | [E] for description and occurrence (PLAN §9.3)|
| `[i].lifted` | bool | True when the claim answers through a describes link | [E] SB U-2 |
| `[i].lifted_via` | obj or null | {description, occurrence} | [E] that the link is identified (SB U-2)|
| `[i].occurrences` | {id: str} | `accepted`, `denied`, `disputed`, `not established` | [E] SB "LABS-1.011", the amendment |
| `[i].applies` | bool or null | False if an involved occurrence is denied; null if one is disputed; True otherwise | [E] SB LABS-1.011; SB U-2 |
| `[i].judgement` | str | the claims vocabulary | [E] SB B0; IBD §2.4 |
| `[i].status` | Status | common 0.3 | [E] IBD §2.4 (`status`) |
| `[i].claimed_by` | [str] | attesters | [E] SB B0 ("sources") |
| `[i].attestations` | [obj] | attestation, attester, polarity, basis, stance, acceptance | [E] SB B0 ("every claim lists its attestations") |

3. **Judgement and uncertainty:**
   - [E] Each entry's `judgement` is the canonical record of its own `causes` content (IBD §2.4).
     - An accepted assertion plus an accepted denial is `disputed`.
     - Unreviewed claims never decide.
   - [E] **Lifting** (PLAN §9.3; SB U-2):
     - a description-level claim answers an occurrence-level question only through describes links the perspective
       accepts, **for both descriptions**;
     - the lifted claim keeps its original status;
     - lifting is one hop: a sibling description's claim is not transferred (SB "Scope of causal claims").
   - [E] **F-B1:** description-level and occurrence-level claims never dispute each other automatically (SB
     LABS-1.012).
   - [E] A claim with `applies: false` stays visible as its source's account and never answers what caused the denied
     happening (SB, the LABS-1.011 "Clarification").
   - [E] Nothing is derived from order or chained (PLAN §9.3).
4. **Visibility:**
   - [E] Judged per perspective, knowledge time and world (SB B0; SB "Scope of causal claims": acceptance recorded
     later, perspective denials, snapshots).
   - [E] Only describes links the perspective accepts lift a claim (SB "Lifting"). What counts as an accepted link is
   - [E] The hypothetical override: a plan stipulating that an occurrence did not happen gives `denied` there and
     `applies: false`; the base world is unchanged (SB LABS-1.011 table).
   - [E] Identity follows common 0.2.
5. **Ordering and multiplicity:**
   - [E] One entry per claim content: all of its attestations are in that entry (IBD §2.2).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `[i].attestations[acceptance=accepted, polarity=true].attestation` | `[i].judgement = accepted` and `[i].applies = true` ("what caused E") | [E] for the claim's attestations (SB B0); the restriction to `applies = true` is [P] P-CO-1, from SB LABS-1.011 Clarification |
| supporting | `[i].attestations[acceptance=accepted, polarity=false].attestation` | a question about one claim's `denied` judgement | [E] IBD §2.4 (deciding denials) |
| conflicting | `[i].attestations[acceptance=accepted].attestation` (both polarities) | `[i].judgement = disputed` | [E] IBD §2.2 (polarity dispute) |
| alternative | `[i].attestations[acceptance≠accepted]` | any | [E] V02 §6.2 (unaccepted attestations are alternatives) |
| alternative | the attestations of accepted entries with `applies` false or null, for "what caused E" | — | P-CO-1 (approved) |

7. **Derivations and admissible premises:**
   - None presented [E].
   - Lifting is a read-time link, not a derivation (SB F-B1 "Why").
   - A claim with basis `inference` gets status INFERRED with no derivation record [E].
8. **Refusals:** none documented. A missing `effect` id is a precondition (common 0.8).
9. **Limitations and gaps:**
   - GAP-CAUSE-1 to -7 [E] (INV §4; E2D §4).

---

### `effects_of(world, event, t, as_of=None, perspective=SYSTEM)`
**Serves:**
- C3 (H) (E2D §3.4; GAP-HARNESS-2);
- gap probe GAP-CAUSE-3 (INV §4).

1. **Inputs and conditions:**
   - `event` is an event description [E] (V02 §3.2: `initiates(event, proposition)`; SB B0 "about a description").
   - The outcome is a proposition identified by its A0.1 id [E] (SB "Schema and API"; PLAN Stage A0).
   - Effects are written by `claim_effect` or `account` [E as recorded] (SB D-B-1).
   - `t` judges the claim contents (not fixed by the contract).
2. **Output fields and vocabulary** (one entry per effect claim):

| Field | Type | Values | Label/source |
|---|---|---|---|
| `[i].kind` | str | `initiates`, `terminates` | [E] V02 §3.2 |
| `[i].outcome` | obj | {type, roles, params} | [E] SB "Schema and API" ("each claimed effect") |
| `[i].outcome_id` | id | `p:` + hash | [E] PLAN Stage A0 (proposition ids) |
| `[i].claim` | str | the claims vocabulary | [E] SB B0 (`claim`); IBD §2.4 |
| `[i].claim_status` | Status | common 0.3 | [E] IBD §2.4 |
| `[i].claimed_by`, `[i].attestations` | as in `causes_of` | — | [E] SB B0 |
| `[i].state.accepted_change` | bool | True / False | [E] that the field exists (SB B0: `state.accepted_change`)|
| `[i].state.before`, `[i].state.after` | Answer | status, holds, support, conflicts | [E] SB B0 ("judged ... before and after the event")|
| `[i].state` | null | when the event has no accepted account | [E] SB D-B-6 (no timing for the perspective) |

3. **Judgement and uncertainty:**
   - [E] The claim and the change are judged separately. An accepted claim does not make a change, and an accepted
     state does not confirm the claim (SB B0; SB reference world, "Effect claims").
   - [E] The states are judged from the outcome's own attestations (SB B0), with the canonical and functional judgement
     (IBD §4; Q-B2).
4. **Visibility:**
   - [E] Context ⟨w, p, τ⟩ as in common 0.2. Illustration: the technician's own view of the vibration claim (SB "Tests").
5. **Ordering and multiplicity:**
   - The list is a multiset (common 0.9).
   - [E] One entry per claim content (event, kind, outcome), with all of its attestations (IBD §2.2).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting (claim) | `[i].attestations[acceptance=accepted, polarity=true].attestation` | `[i].claim = accepted` | [E] SB B0; IBD §2.4 |
| supporting (claim) | `[i].attestations[acceptance=accepted, polarity=false].attestation` | `[i].claim = denied` | [E] IBD §2.4 |
| conflicting (claim) | `[i].attestations[acceptance=accepted].attestation` | `[i].claim = disputed` | [E] IBD §2.2 |
| supporting (state) | `[i].state.before.support`, `[i].state.after.support` | a question about the judged before or after state | [E] SB B0 (the outcome's own attestations) |
| conflicting (state) | `[i].state.<side>.conflicts`, `[i].state.<side>.constraint_support[].support` | that side is DISPUTED | [E] Q-B2; the approved `constraint_support` rule; common 0.4 P-1 |
| alternative | `[i].attestations[acceptance≠accepted]`; `[i].state.<side>.alternatives` | any | [E] V02 §6.2 |

   - [E] The claim evidence and the state evidence never support each other (SB B0).
   - [E] A denial of the same effect claim is conflicting only for the claim judgement.
   - [P] P-EF-1: another event's claim about the same outcome is a different content, not a rival, and is not
     reported. No design text makes claims by different events compete.
7. **Derivations:** none presented [E]. `accepted_change` is a comparison of two judged answers, not a recorded
   derivation [E] (E2DEC §4).
9. **Limitations and gaps:**
   - GAP-HARNESS-2, GAP-MULTI-2 (the instants), GAP-CAUSE-3 [E] (E2D §4; INV §6, §4).

---

### `explain(world, type, roles, t, as_of=None, perspective=SYSTEM)`
**Serves:**
- C4 (H) (E2D §3.4);
- X4 with `occurrence_status` (E2D §3.6);
- gap probes GAP-CAUSE-1, GAP-MULTI-4, GAP-MULTI-6.

1. **Inputs and conditions:**
   - A content (`type`, `roles` by core role names) and a valid time `t` [E] (R2).
   - Context as in common 0.2 [E].
2. **Output fields and vocabulary:**
   - [E] SB "Schema and API": "the judged state, its **accepted** initiating events, and their causal claims", one step
     back (SB "Deferred capabilities"; SB "Remaining limitations").

| Field | Type | Values | Label/source |
|---|---|---|---|
| `holds` | Answer | status, holds, support, conflicts, constraint_support, alternatives | [E] SB "Schema and API" ("the judged state"); IBD §3 (holds is the record's projection); the approved `constraint_support` rule |
| `initiated_by[i].event` | id | an event description claimed to initiate the content | [E] SB "Schema and API" |
| `initiated_by[i].claim`, `.claim_status`, `.claimed_by` | str / Status / [str] | the claims vocabulary | [E] SB B0 |
| `initiated_by[i].start`, `.end` | Window | the accepted occurrence interval | [E] SB B-time and D-B-6 |
| `initiated_by[i].causes[j]` | `causes_of` entry | as in `causes_of` | [E] SB "Schema and API" ("their causal claims") |
| `initiated_by[i]` initiating-claim attestations | — | **absent** | required [E] by SB B0 ("every claim lists its attestations")|

3. **Judgement and uncertainty:**
   - [E] `holds` is the canonical judgement. It may be INFERRED by functional exclusivity (IBD §2.4 addendum, R3).
   - [E] Causes follow the `causes_of` contract: lifting, F-B1, U-2, `applies`.
   - [E] An explanation is only what was asserted and accepted. Order or proximity never adds one (PLAN §9.3; SB
     Q-B1.4).
4. **Visibility:**
   - [E] Context ⟨w, p, τ, t⟩.
   - [E] The initiators' times come only from accepted accounts (SB D-B-6).
   - [E] Occurrence statuses are not checked here; X4 composes `occurrence_status` (E2D §3.6).
5. **Ordering and multiplicity:**
   - `initiated_by` and `causes` are multisets (common 0.9).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `holds.support` | `holds.status` is not DISPUTED | [E] IBD §2.2; SB "Schema and API" |
| conflicting | `holds.conflicts`, `holds.constraint_support[].support` | `holds.status = DISPUTED` | [E] the approved `constraint_support` rule; common 0.4 P-1 |
| alternative | `holds.alternatives` | any | [E] V02 §6.2 |
| supporting | `initiated_by[i].causes[j].attestations[acceptance=accepted, polarity=true].attestation` | as in the `causes_of` table (`judgement = accepted`, `applies = true`, P-CO-1) | [E] SB B0; [P] P-CO-1 |
| conflicting / alternative | `initiated_by[i].causes[j].attestations` | as in the `causes_of` table | [E] |

   - **Citable today:** `holds.support` (with conflicts and constraint support when DISPUTED), and the attestations of
     the causal claims under `initiated_by[i].causes[j]`.
   - **Initiating-claim provenance:** adjudicated as a provenance defect. A
     question may require the initiating claims' attestations (the established B0 requirement) and stays
     - whether an unaccepted initiator is listed;
     - an initiator whose account is missing or which has not ended by t;
     - a cause's `lifted` flag inside `explain`.
7. **Derivations:** none presented [E]. `explain` is a fixed composition (holds → initiating claims →
   `causes_of`; INV §6), not a derivation.
8. **Refusals:**

| Name | Condition | Exception / message | Established? | Source |
|---|---|---|---|---|
| unknown-role | `roles` names a role the type does not relate (core names, inherited ones included) | `UnknownRoleError` (a `ValueError`) naming the type, the unknown names and the valid ones | yes | R2 ("Readers affected: ... explain (roles)"), approved LABS-1.053; HR §9 |

9. **Limitations and gaps:**
   - One step only: GAP-CAUSE-1 [E] (SB "Deferred capabilities").
   - GAP-MULTI-4 and GAP-MULTI-6 [E] (INV §6).

---

### `changes(world, subject, t1, t2, as_of=None, perspective=SYSTEM)`
**Serves:**
- C5 (H) (E2D §3.4);
- F family `changes` on a frame (E2D §2);
- gap probe GAP-CAUSE-4.

1. **Inputs and conditions:**
   - The interval is (t1, t2], open at t1: "a change at exactly t1 is already in effect at t1" [E] (SB "The changes
     contract", Q-B1.1).
   - `subject` is any thing [E] (SB contract, `track`).
   - Context as in common 0.2.
   - t1 ≥ t2 is unspecified (not fixed by the contract).
2. **Output fields and vocabulary** [E] (SB "The changes contract", LABS-1.015, unless marked):

| Field | Type | Values | Label/source |
|---|---|---|---|
| `subject`, `from`, `to`, `context` | — | {world, perspective, as_of} | [E] |
| `transitions[i].track` | obj | {kind `slot`, type, key, value_role} or {kind `content`, type, roles, params} | [E] |
| `transitions[i].category` | str | `world-state`, `judgement` | [E] Q-B1.2 |
| `transitions[i].before`, `.after` | obj | {status, values or holds, support, conflicts} | [E] |
| `transitions[i].window` | (time, time) | possible transition interval; equal when certain | [E] Q-B1.1 |
| `transitions[i].within` | str | `certain`, `possible` | [E] Q-B1.1 |
| `transitions[i].began`, `.ended` | [content] | — | [E] |
| `transitions[i].explanations[k]` | obj | event, effect, content, claim, claim_status, claimed_by, start, end, occurrences, `attribution` (`unique` or `ambiguous`), `timing` (`consistent` or `unresolved`) | [E] Q-B1.4; `timing` from SB B-time |
| `began`, `ended` | [view] | views over the transitions | [E]|
| `unchanged` | int | — | [E] |

3. **Judgement and uncertainty:**
   - [E] **Categories** (Q-B1.2):
     - world-state is between two accepted states (a value, or an accepted "does not hold");
     - judgement is into or out of UNKNOWN or DISPUTED, never presented as physical change.
   - [E] **Windows** (Q-B1.1):
     - accepted A, then only UNKNOWN, then accepted B ≠ A is one world-state transition whose window is the gap;
     - no instant is invented;
     - certain if the window lies inside the interval, possible if it overlaps, omitted if outside.
     - The design does not cover A → UNKNOWN → A, or gaps through DISPUTED: (not fixed by the contract).
   - [E] **Q-B2:** one functional-conflict judgement, the same as `value_at`, rivals included. Attested constraints
     are applied at each boundary (IB "Answer changes").
   - [E] **C-6:** a slot's status rests on the values held only (ICD §3.3; IC "Readers").
   - [E] **Explanations** (Q-B1.4):
     - only accepted initiates or terminates claims about a content that began or ended in the transition count;
     - one temporal constraint applies: an effect cannot precede its event's start (B-time);
     - proximity is never evidence;
     - a claim that fits several activations on the whole timeline is `ambiguous` on each and never chosen;
     - unresolved times are kept with `timing: unresolved` (B-time). The boundary is (not fixed by the contract).
   - [E] The SB probe cases 1-6 are the worked examples.
4. **Visibility:**
   - [E] Event time, transition valid time, knowledge time and explanations are kept apart (SB Q-B1, the requested
     contract).
   - [E] Judged for world, perspective and `as_of`.
   - [E] An event outside the interval may explain a transition inside it, and is never itself an in-period change.
5. **Ordering and multiplicity:**
   - [E] One claim may be listed under several transitions (`ambiguous`), and one event may be listed twice on one
     transition (initiates and terminates).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting (required, both sides) | `transitions[i].before.support` **and** `transitions[i].after.support` | `transitions[i].category = world-state` | [E] Q-B1.2 ("between two accepted states") with the per-side `support` of the contract schema|
| supporting | `transitions[i].<side>.support` for each side whose status is not UNKNOWN or DISPUTED | `category = judgement` | [E] SB contract |
| conflicting | `transitions[i].<side>.support` and `.conflicts` | that side's status is DISPUTED | [E] Q-B2 ("its own support and the rival attestations"); common 0.4 P-1 |
| not cited | `transitions[i].explanations[k]` | any | [E] SB B0: an asserted effect is not evidence of the change |

   - Where the answer establishes a transition (category `world-state`), evidence from **both** sides is required
     supporting evidence. `before.support` and `after.support` must each be non-empty and cited.
   - An answer with an empty side fails recall. This is not excused: questions that exercise a holds → does-not-hold
7. **Derivations:** none presented [E]. Values excluded by functional exclusivity are a declared query-time rule
   (V02 §5.6, INFERRED), not a recorded derivation.
8. **Refusals:** none documented.
9. **Limitations and gaps:**
   - GAP-CAUSE-1 to -4; GAP-MULTI-2 [E].
   - Stale design text: (not fixed by the contract).

---

### `process_steps(world, process, t, as_of=None, perspective=SYSTEM)`
**Serves:**
- P1, P2, P4, P5 (H) (E2D §3.5);
- X5 and X6 (E2D §3.6);
- gap probes GAP-PROC-1 to -7.

1. **Inputs and conditions:**
   - `process` is an occurrence [E]. Process membership is `part-of` between occurrences, and a process is a
     classification (SB B-arch; V02 DR-05).
   - `t` judges membership [E] (IBD §6).
   - Context as in common 0.2.
2. **Output fields and vocabulary** (one entry per step):

| Field | Type | Values | Label/source |
|---|---|---|---|
| `[i].occurrence` | id | a part of the process | [E] SB B-arch |
| `[i].judgement` | str | `established`, `disputed` | [E] IB "What changed" (each step gains judgement and status); increment B |
| `[i].status` | Status | DISPUTED for a dispute, otherwise the support status | [E] IBD §4; IBD §2.4 |
| `[i].support` | [id] | the part-of content's deciding attestations | [E] IBD §2.2 |
| `[i].start`, `[i].end` | Window or null | an accepted account's interval | [E] SB D-B-6|
| `[i].descriptions` | [id] | descriptions the perspective accepts as describing the step | [E] V02 §3.2 ("Queried")|

3. **Judgement and uncertainty:**
   - [E] Membership is judged by the canonical record of part-of at t.
   - [E] Disputed steps are listed and flagged, never dropped.
   - [E] Processes are not modelled as ongoing (SB "Deferred capabilities"; GAP-PROC-5).
4. **Visibility:**
   - [E] Context ⟨w, p, τ, t⟩.
   - [E] Intervals come only from accepted accounts (D-B-6).
5. **Ordering and multiplicity:**
   - [E] The steps are ordered by interval start (E2D §2, the P row).
   - [P] P-PS-1: the list order is presentation only and asserts no succession. Succession is asked with `before` (SB
     B0, the succession-vs-causation row; E2D P4). P4 questions compare steps with `before`, never by list position.
   - Steps are otherwise a multiset with one entry per part-of content and part.
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `[i].support` | `[i].judgement = established` | [E] IBD §2.2; HR §5.1 |
| conflicting | `[i].support` | `[i].judgement = disputed` | [E] increment B ("citing both sides"); the role is [P] by common 0.4 P-1 |

7. **Derivations:** none presented [E]. The order is not a derivation, and no order relation exists (GAP-PROC-1).
8. **Refusals:** none documented.
9. **Limitations and gaps:**
   - GAP-PROC-1 to -7 [E] (INV §5; E2D §4).

---

### `before(world, a, b, as_of=None, perspective=SYSTEM)`
**Serves:**
- P3 (H) (E2D §3.5);
- gap probes GAP-PROC-1 and GAP-PROC-4.

1. **Inputs and conditions:**
   - `a` and `b` are event descriptions [E] (SB B0: "`before()` compares intervals").
   - P3's steps (occurrences) are mapped to descriptions by the question's plan (not fixed by the contract).
   - Context as in common 0.2 (no `t`: the intervals are valid times).
2. **Output fields and vocabulary:**

| Field | Type | Values | Label/source |
|---|---|---|---|
| (the answer) | bool or null | True: a certainly ends before b starts; False: b certainly before a; null: they overlap or cannot be ordered | [E] SB B0 ("certainly before, or None if they overlap")|

3. **Judgement and uncertainty:**
   - [E] Judged from the windows, never a guess. Succession says nothing about causation (SB B0; V02 §3.2).
4. **Visibility:** [E] only accounts the perspective can use (SB D-B-6). There is no account (and so null) for an
   unaccepted account, or for an account not inherited.
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| not cited | — | any | [P] P-BE-1 (HR §5.1: "nothing"); no design text gives an evidence rule |

7. **Derivations:** none presented [E].
8. **Refusals:** none documented.
9. **Limitations and gaps:** GAP-PROC-1, GAP-PROC-4, GAP-MULTI-2 [E].

---

### `interval(world, description, as_of=None, perspective=SYSTEM)`
**Serves:**
- P3 (H) with `before` (E2D §3.5);
- the time-picking step of X plans (E2D §3.6);
- gap probes GAP-PROC-4 and GAP-MULTI-2.

1. **Inputs and conditions:** an event description [E] (V02 §3.2: a description's interval is on its source's
   attestation). Context as in common 0.2.
2. **Output fields and vocabulary** (the harness projection {start, end, attestation}; the reader returns a tuple):

| Field | Type | Values | Label/source |
|---|---|---|---|
| `start`, `end` | Window | {earliest, latest} | [E] V02 §3.2 (uncertain boundaries, windows); V02 §4.5 (event time = occurrence interval) |
| `attestation` | id | the account used | [E] SB D-B-6 (an account the perspective can use) |
| (the answer) | null | no usable account | [E] SB D-B-6 |

3. **Judgement and uncertainty:**
   - [E] Only an account the perspective can use counts. An unaccepted account's times are never used (SB D-B-6).
   - [E] This is occurrence time, never record time (SB B-time).
4. **Visibility:** [E] per perspective and `as_of`. In a variant, the account is inherited within the snapshot (V02
   §6.2); otherwise null.
5. **Ordering and multiplicity:** one result. (not fixed by the contract).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `attestation` | the answer is not null | [P] P-IV-1 (HR §5.1: "the account attestation it uses"); consistent with SB D-B-6 |

7. **Derivations:** none presented [E].
8. **Refusals:** none documented.
9. **Limitations and gaps:** GAP-PROC-4 (no duration), GAP-MULTI-2 [E].

