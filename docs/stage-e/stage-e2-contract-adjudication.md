# Stage E2 reader contracts: discrepancy adjudication register

**LABS-1.063, 27 November 2026.** Branch `feature/e2-reader-contracts`. **For review.**

**What this covers:** the 118 discrepancies recorded by the reader-contract review (LABS-1.062).

**Sources:**
- the contracts: [benchmark/e2/spec/reader-contracts.md](../../benchmark/e2/spec/reader-contracts.md);
- the diagnostic reproductions: [e2-contract-adjudication/diagnostics.json](e2-contract-adjudication/diagnostics.json),
  from `probes/e2_contract_diagnostics.py`.

**Diagnostic fixtures are not E2 fixtures.** Their observed outputs must never become E2 gold.

**What this register does not do:**
- it changes no reader;
- the proposed DI entries (section 4) are not registered in `docs/core-0.4/deferred-issues.md` until the owner
  approves them;
- the semantic decisions (section 5) are not adopted.

## 1. Rules applied

**Classes** (exactly one per item):

| Class | Meaning |
|---|---|
| semantic-defect | a wrong answer against an unambiguous approved design |
| provenance-defect | a right answer, but missing or wrong required provenance |
| unsupported | a capability the design does not provide (a gap) |
| unresolved-decision | the design is silent, or two approved texts conflict |
| api-convention | names, extra fields, ordering or messages; no semantics |
| documentation | a docstring or text error; the contract stands |
| superseded | a duplicate of another item, or already resolved |

**Severity:**
- **high:** a plausible E2 question gets a wrong status, value or judgement.
- **medium:** provenance is wrong or missing, or the answer is wrong only in an edge case.
- **low:** convention, documentation or cosmetic.

**E2 eligibility (LABS-1.063, amending the blanket exclusion of LABS-1.062):**

| Class | Eligibility |
|---|---|
| semantic-defect, provenance-defect against an unambiguous approved contract | **ELIGIBLE** (A/H scored). A question is never excluded because the current implementation is expected to fail it. |
| unsupported | **G probe** (rule G-1) |
| unresolved-decision | **BLOCKED** until the owner decides. `benchmark/e2/spec/blocked.json` lists each decision; the question checker refuses questions that depend on one (H-8 as amended). |
| api-convention | **ELIGIBLE** where the contract fixes the convention; otherwise questions do not expect that field (each row says which) |
| documentation | **ELIGIBLE**: the contract stands |
| superseded | n/a |

## 2. Summary

| Class | Items | | Severity | Items | | E2 eligibility | Items |
|---|---:|---|---|---:|---|---|---:|
| unresolved-decision | 38 | | high | 11 | | ELIGIBLE | 69 |
| api-convention | 29 | | medium | 36 | | BLOCKED | 36 |
| documentation | 20 | | low | 64 | | G probe | 3 |
| semantic-defect | 10 | | n/a (superseded) | 7 | | n/a (superseded) | 9 |
| provenance-defect | 9 | | | | | split (D-CS-3: disputed ELIGIBLE, not yet effective BLOCKED) | 1 |
| superseded | 9 | | | | | | |
| unsupported | 3 | | | | | | |
| **all** | **118** | | | **118** | | | **118** |

**Reproduced:** 17 items, through 14 diagnostic cases (section 3). Every other item is classified from the design
sources and from code inspection only, and its row says so.

**High severity (11):**
- **Semantic defects:** D-WH-3, D-WH-5, D-PO-3, D-ME-5, D-CM-6, D-VA-3, D-CO-1, D-CO-3. Each is reproduced and
  **eligible**.
- **Unresolved decisions:** D-ME-6, D-EF-1, D-EX-1 (blocked).

## 3. Diagnostic reproduction results

All 14 cases were run on both query paths, which agree in every case. The fixtures are minimal and isolated
(`probes/e2_contract_diagnostics.py`).

| Case | Items | Expected (approved contract) | Observed | Result |
|---|---|---|---|---|
| DX-1 | D-WH-3 | a derived pose rests on its position premise, so a premise disputed by an accepted denial gives no undisputed INFERRED candidate | `poses`: DISPUTED; `where`: **INFERRED**, candidate INFERRED | reproduced |
| DX-2 | D-WH-5, D-PO-3 | a reader judges the subject with its same-as group (ID-8) | position stated under the alias: `where`/`poses` by the canonical name find it; **by the alias name they find nothing** | reproduced |
| DX-3 | D-ME-5 | measurements of an alias are the bearer's | measurement under the alias: `measurements(box)` = 0, `measurements(box-alias)` = 1 | reproduced |
| DX-4 | D-CM-6 (and D-ME-3) | an accepted denial of the measured content disputes it, with or without t | `compare_measurements`: ASSERTED, the denial not listed; **with t: NOT_YET_KNOWN** (the measurement disappears). The denial's content equals the measured content | reproduced |
| DX-5 | D-ME-6 | a measurement over an instant holds at it; two at one instant are comparable | `measurements(t=instant)` = 0; the pair is "incomparable: valid times do not overlap" | reproduced (the intended semantics is SD-MEA-2) |
| DX-6 | D-VA-3 | value readers apply declared slots only and never report an exclusive office's holders as undisputed | `value_at(office-holding, class→classified)`: ASSERTED [bea, cal], while `office_holders` reports the conflict | reproduced |
| DX-7 | D-FA-1 | (whether listings cite the constraint is SD-CORE-3) | `facts_about`: DISPUTED, does not cite `x-sm`; `holds` cites it in `constraint_support` | reproduced (behaviour); decision open |
| DX-8 | D-CO-1 | lifting needs accepted describes links for both descriptions | a cause description with no link is lifted with `applies: true` and no cause occurrence | reproduced |
| DX-9 | D-CO-2 | a lifted claim cites the describes links it used | `lifted_via` gives only {description, occurrence} ids | reproduced |
| DX-10 | D-CO-3 | a describes link disputed by an accepted denial does not lift | the claim is lifted, `applies: true` | reproduced |
| DX-11 | D-EX-1, D-EX-4 | `explain` lists accepted initiating events; every claim lists its attestations | an **unreviewed** initiating claim is listed; `initiated_by` has no attestation ids | reproduced |
| DX-12 | D-EX-3 | an initiator whose time is unavailable is kept as `unresolved` | the initiator with no accepted account is dropped | reproduced |
| DX-13 | D-CH-1 | each side of a transition cites what it rests on | world-state transition true → false: `after.support` = [], while `holds` at that time cites the denial | reproduced |
| DX-14 | D-EF-1 | a move from UNKNOWN to held is a judgement transition (Q-B1.2); whether it binds `effects_of` is SD-CAU-1 | `accepted_change: true` (UNKNOWN → ASSERTED); `changes` classifies the same move as `judgement` | reproduced (behaviour); decision open |

## 4. Proposed consolidated DI entries (for approval; not registered)

The 19 semantic and provenance defects consolidate into seven issues. None is corrected here: each is a later
implementation increment, and each needs the owner's approval to be registered. E2 questions on them stay **eligible**:
a reader that fails such a question fails it in the E2 results, and the failure is adjudicated as an implementation
defect under this DI.

| Proposed | Title | Items | Class / severity | Reproduced | Recommended correction (later, not now) |
|---|---|---|---|---|---|
| **DI-24** | Subject-keyed readers ignore the subject's same-as group | D-WH-5, D-PO-3, D-ME-5 (related notes: D-OH-2, D-CS-2) | semantic, high | DX-2, DX-3 | apply ID-8 to `where`, `poses` and `measurements` subject selection, as DI-12 did for traversals |
| **DI-25** | A derived pose can be INFERRED from a disputed position premise | D-WH-3 | semantic, high | DX-1 | a derived candidate takes the worse of its chain's and its position's status (v0.2 E6) |
| **DI-26** | Accepted denials of measured content are not judged | D-CM-6, D-ME-3 (related: D-CM-2) | semantic, high | DX-4 | judge the reported content with its denials (DISPUTED or not holding), list the denial, and stop the `t` filter from dropping the measurement |
| **DI-27** | Value readers on types without the asked slot; dispute sides in `value_at` | D-VA-3, D-VA-1 (related: D-VA-5, corrected) | semantic high / provenance medium | DX-6 | refuse explicit roles that form no declared slot (DI-19 report §1), and report rivals apart from support |
| **DI-28** | Causal lifting through describes links | D-CO-1, D-CO-3, D-CO-2 | semantic high / provenance medium | DX-8, DX-10, DX-9 | require accepted (ESTABLISHED) links on both sides, and cite the links used |
| **DI-29** | Provenance completeness: dispute sides, initiating claims, transition sides, alternatives | D-EX-4, D-CH-1, D-TB-3, D-PO-2, D-FI-1, D-TB-7 | provenance, medium | DX-11, DX-13 | additive fields, as DI-19: initiating claims' attestations, the deciding attestations of a negative side, off-chain disputed edges, both sides of listed disputes, unaccepted transforms as alternatives |
| **DI-30** | Measurement reporting: canonical units and the reference check | D-ME-10, D-MC-5 | semantic, low / medium | no | normalise generic statements to SI, and report "time unknown" instead of "no certificate" when the activity has no accepted time |

**Proposed gap (unsupported, not a DI):** GAP-SPATIAL-9 (D-TB-6). Derived poses and transforms don't report the
interval they hold over or their knowledge time (Plan 9.6). Questions on it are G probes. D-BE-3 and D-BE-4 map to
existing GAP-PROC and clock items (see their rows).

**Already resolved under LABS-1.063:**
- D-PO-1, D-CH-7, D-TB-4 (documentation corrected);
- D-VA-5 (DI-19 report corrected);
- D-VA-6 (harness corrected).

## 5. Outstanding semantic decisions (owner's approval needed)

There are 25 decisions covering the 38 unresolved items. Each one's full text is in its family's part of the register
below: bounded alternatives, each grounded in the ontology or prior decisions, and a recommendation with its reason.
**No recommendation adopts current implementation behaviour by default.** Where one coincides with it, the reason
given is from the design. Until a decision is made, the questions depending on it are refused by the checker
(`blocked.json`).

| Decision | Question | Items | Recommendation (short) |
|---|---|---|---|
| SD-CORE-1 | what `holds()` asks when only some roles are bound | D-HO-1, D-HO-2 | read the given roles as the exact content (v0.2 §4.2; increment B §3) |
| SD-CORE-2 | `value_at` with `key_role` but no `value_role` | D-VA-2 | refuse as malformed (A0; R2's principle) |
| SD-CORE-3 | must listings cite the constraint behind a constraint dispute? | D-FA-1 | yes: extend DI-19 additively to `facts_about` |
| SD-CORE-4 | occurrence readers given a non-occurrence id | D-OC-3, D-OS-1 | a P-5 precondition for E2 |
| SD-SPA-1 | which angular tolerance decides chain agreement | D-TB-1, D-WH-1 | keep 1e-9 rad for chain agreement, and confirm D-A2-7 in that wording (transforms carry no uncertainty) |
| SD-SPA-2 | trivial (source = target) and empty chains | D-TB-2 | identity transform with no derivation presented; NOT_YET_KNOWN when no transform touches either frame |
| SD-SPA-3 | a truncated search through a disputed transform | D-TB-8 | DISPUTED, no transform |
| SD-SPA-4 | the `where` judgement label | D-WH-2 | "compatible" only when every pair was compared and overlaps |
| SD-MEA-1 | what `t` means in the measurement readers | D-ME-1, D-MC-1 | valid time, with denials kept |
| SD-MEA-2 | a measurement over an instant | D-ME-6 | holds at its instant (for the reported content) |
| SD-MEA-3 | categorical qualities | D-ME-9 | out of scope for `measurements`, stated in the contract |
| SD-MEA-4 | disjoint valid times | D-CM-3 | incomparable now; a declared constant quantity later |
| SD-MEA-5 | evidence for a not-yet-effective calibration | D-CS-3 | the accepted claim is supporting |
| SD-MEA-6 | which instant judges calibration when the start is uncertain | D-MC-3 | judge over the whole window |
| SD-CAU-1 | what an accepted state change is in `effects_of` | D-EF-1, D-EF-2 | one definition of change for every reader, through `changes` (the Q-B2 precedent) |
| SD-CAU-2 | which initiating events `explain` lists | D-EX-1, D-EX-2, D-EX-3 | accepted claims only, with B-time timing; others listed as alternatives |
| SD-CAU-3 | initiators when the content does not hold | D-EX-5 | list them anyway (B0: claim and state independent) |
| SD-CAU-4 | do `changes` explanations list attestations? | D-CH-2 | yes: stage-b B0 governs |
| SD-CAU-5 | touching windows | D-CH-3, D-BE-2 | half-open intervals (ontology convention; Q-B1.1) |
| SD-CAU-6 | A → UNKNOWN → A, and gaps through DISPUTED | D-CH-4 | follow the Q-B1.2 categories literally |
| SD-CAU-7 | the valid time at which timeless claims are judged | D-CH-5, D-EF-6 | independently of it (D-B-2) |
| SD-CAU-8 | `changes` with t1 ≥ t2 | D-CH-8 | refuse t1 > t2; an empty answer for t1 = t2 |
| SD-CAU-9 | occurrence applicability for effect claims and explanations | D-EF-5, D-CH-9 | extend `applies` (Occ-2's general wording) |
| SD-CAU-10 | several usable accounts or timed descriptions | D-IV-1, D-EF-3, D-PS-3 | report every account; "certain" only if all agree |
| SD-CAU-11 | writer-side refusals | D-CO-6, D-EF-7 | establish only those the design implies |

**Measurement-family note:**
- **SD-MEA-5:** its recommendation (supporting) would turn the `undetermined` role for not-yet-effective calibration
  claims into supporting. Until it is approved, the harness counts them in no role.
- **SD-CAU-1:** if approved, `effects_of` questions on `accepted_change` become eligible.

## 6. The register

One row per discrepancy, by contract part. The columns are as required by LABS-1.063:
- identifier;
- authoritative design source;
- expected behaviour (where established);
- reported implementation behaviour;
- whether independently reproduced;
- classification and severity;
- E2 eligibility;
- recommended disposition and group.

## Part A. Core and organisation

**Brief:** LABS-1.063. **Sources:** the contracts in `benchmark/e2/spec/reader-contracts.md` (core section), the
evidence file `docs/stage-e/e2-reader-contracts/evidence-core.md`, and the diagnostics in
`docs/stage-e/e2-contract-adjudication/diagnostics.json`. The diagnostics reproduce two core items: DX-6 (D-VA-3) and
DX-7 (D-FA-1); both query paths agree in each.

**Applied as approved by the owner (LABS-1.063):**
- P-1 to P-5, with amendments: supporting and conflicting evidence each have independently authored required and
  admissible sets.
- P-VA-1 as qualified: positive attestations of mutually exclusive rival values keep their conflicting relationship.
- P-OH-1 as qualified: the conflict relationship between established holders is kept.

**Short source names:**

| Name | Path |
|---|---|
| A0 | `docs/core-0.4/README.md` |
| A2 | `docs/core-0.4/stage-a2.md` |
| SB | `docs/core-0.4/stage-b.md` |
| D2 | `docs/core-0.4/stage-d2.md` |
| B-D | `docs/core-0.4/pre-e-increment-b-design.md` |
| D-D / D | `docs/core-0.4/pre-e-increment-d-design.md` / `pre-e-increment-d.md` |
| ID-D | `docs/core-0.4/pre-e-identity-design.md` |
| GATE | `docs/core-0.4/pre-e-decision-gate.md` |
| R | `docs/stage-e/e1-reconciliation-design.md` |
| DI19 | `docs/stage-e/stage-e-di19-constraint-support.md` |
| C-D | `docs/core-0.4/pre-e-increment-c-design.md` |
| common | `benchmark/e2/spec/reader-contracts.md` §0 |

### Items

| ID | Authoritative design source | Expected (where established) | Implementation behaviour (reported) | Reproduced | Class | Severity | E2 eligibility | Recommended disposition | Group |
|---|---|---|---|---|---|---|---|---|---|
| D-HO-1 | B-D §3 (the record "of one content"); v0.2 §4.2 (the canonical key is type + role bindings + params) | Silent on questions that bind only some of a content's roles | Given roles are a subset filter (docstring: "with the given players among its own") | no (inspection only) | unresolved-decision | medium | BLOCKED for partial-role questions; full-role questions ELIGIBLE | decision SD-CORE-1 (holds-question-scope) | holds-question-scope |
| D-HO-2 | as D-HO-1; C-D §7 and D-D §9 (order independence for their readers); A2 D-A2-5 (parameters are not part of holds' question) | Silent; the parameter part is GAP-SPATIAL-8 | When several contents match, the first decided record in load order is returned; the others are not reported | no (inspection only) | unresolved-decision | medium | BLOCKED (partial roles); parameter-variant questions are G (GAP-SPATIAL-8) | decision SD-CORE-1 (holds-question-scope) | holds-question-scope |
| D-HO-3 | B-D §2.4 (PENDING is a record judgement); B-D §5 (holds answers unchanged); E1 TEMPLATES (judgement is read from `judgement()`) | PENDING is a judgement of the record, not of `Answer` | `holds()` returns UNKNOWN for PENDING records | n/a | api-convention | low | ELIGIBLE: pending questions read `judgement()`, never `holds().status` | contract note | answer-projection |
| D-HO-4 | B-D §2.4 and B points decided 1-3 (the reason lists) | Reasons as listed there | Extra UNKNOWN reason `not_supporting` (an accepted doubt or hypothesis); the judgement word is correct | n/a | api-convention | low | ELIGIBLE; questions do not expect `reasons` = `not_supporting` | contract note | answer-projection |
| D-HO-5 | A0 F-4 (DISPUTED holds has `support`); C points decided 2 and ER-4 (rule Q DISPUTED has empty `support`) | Roles are defined per reader by P-1 | Two meanings of `support` across readers | n/a | superseded | n/a | n/a | none (superseded by P-1 / P-HO-1, approved) | evidence-roles |
| D-VA-1 | A0 F-4; SB Q-B2; P-VA-1 as qualified | A dispute keeps its conflicting relationship between rival values; polarity alone is not enough | `support` holds every value's claims; there is no `conflicts` field and no mapping from attestation to value in the answer, so the extractor cannot tell which claims are rivals | no (inspection only) | provenance-defect | medium | ELIGIBLE (A/H scored; supporting and conflicting gold authored independently) | DI-27 (value-dispute-sides) | value-dispute-sides |
| D-VA-2 | A0 "What uses them" ("otherwise the question must say which"); R R2 (a malformed question must not look like an answer) | Silent on `key_role` given without `value_role` | Answers UNKNOWN with empty `values` even where the content holds | no (inspection only) | unresolved-decision | medium | BLOCKED for half-specified calls; questions name both roles or neither | decision SD-CORE-2 (value-at-roles) | value-at-roles |
| D-VA-3 | B-D §2 and §3 (every reader takes its facts from the canonical records; value_at is a projection of them); DI19 §1 (value readers never apply attested constraints); D2 §3; v0.2 §5.3 ("never silent") | No reader reports content that is DISPUTED for p as undisputed | `value_at(office-holding, key_role="class", value_role="classified")` gives ASSERTED [bea, cal] while `office_holders` reports the conflict | yes, DX-6 | semantic-defect | high | ELIGIBLE (A/H scored) | DI-27 (value-readers-unslotted) | value-readers-unslotted |
| D-VA-4 | v0.2 §5.5 ("absence of x from a place says nothing about where x is"); v0.2 §5.6 (UNKNOWN definition) | A denial of one value does not decide the value: UNKNOWN | Only accepted denials, no value held: UNKNOWN | n/a | documentation | low | ELIGIBLE | contract note (cite v0.2 §5.5, §5.6) | value-at-roles |
| D-VA-5 | B-D §3; DI19 §1 | Answers identical to the records' projection | Code path is `_judge` + `_conflicts`, not `_answer`; the answers agree | n/a | documentation | low | ELIGIBLE | documentation fix (DI19 §1 description of the code path) | value-readers-unslotted |
| D-VA-6 | A0; DI19 §1 | The no-single-slot refusal is established | Was listed as unestablished in the harness review | n/a | superseded | n/a | n/a | none (superseded: already corrected, LABS-1.063) | refusals |
| D-FA-1 | B-D §4 (listings cite "the assertions, the denials and any constraint rivals"); DI19 and REG DI-19 (scoped to `holds()`); B-D §2 (one record for every reader) | The two approved texts differ in scope: listings must cite rivals; whether they must also cite the constraint is not decided | A `facts_about` entry disputed under `exclusive-office` does not cite `x-sm`, while `holds()` does | yes, DX-7 | unresolved-decision | medium | BLOCKED for questions requiring constraint evidence from `facts_about`; otherwise ELIGIBLE | decision SD-CORE-3 (constraint-provenance-listings) | constraint-provenance-listings |
| D-FA-2 | B-D §2.3 (a rival counts if it holds at the polarity layer); B-D §4 | Rivals under the constraint, whatever they name | The docstring adds "including rivals that do not mention the subject"; consistent with B-D | n/a | documentation | low | ELIGIBLE | contract note | listing-dispute-sides |
| D-FA-3 | B-D §3 ("sorted as today", undefined) | No order is established | Sorted by (type, str(roles)) | n/a | api-convention | low | ELIGIBLE; entries compared as a multiset (common 0.9) | contract note | ordering |
| D-OC-1 | D-D ER-5 (`participants` unchanged, the Core 0.3 projection); R R1 (use `resolved` for who took part) | `participants` is "who is said to take part"; `resolved` is the answer | `participants` also takes unaccepted attestations of listed descriptions | n/a | api-convention | low | ELIGIBLE; questions do not expect `participants` (read `roles[*].resolved`) | contract note | occurrence-projection |
| D-OC-2 | v0.2 §3.2 (descriptions = usable describes links); ER-3 (compared = ESTABLISHED); ID-10 (optional, deferred by LABS-1.049) | `descriptions` by usable link, as approved | `descriptions` by usable link; `accounts` by canonical record | n/a | superseded | n/a | n/a (questions expect `descriptions` by usable link) | none (superseded by ID-10, already registered and deferred) | occurrence-projection |
| D-OC-3 | SB LABS-1.011 and D-D §2 (scoped to occurrences); common P-5 (an id that names nothing is a precondition) | Silent on an id of another kind | No check that the id is an occurrence | no (inspection only) | unresolved-decision | low | BLOCKED for non-occurrence inputs only (none expected in E2) | decision SD-CORE-4 (occurrence-input-kind) | occurrence-input-kind |
| D-OS-1 | SB LABS-1.011 / Occ-1 (existence of an occurrence only from its own existence attestations); Core 0.3 participation rule for other things | Silent on calling the reader with a non-occurrence | `exists()` participation inference can make the status `accepted` for a non-occurrence | no (inspection only) | unresolved-decision | medium | BLOCKED for non-occurrence inputs only | decision SD-CORE-4 (occurrence-input-kind) | occurrence-input-kind |
| D-OS-2 | SB LABS-1.012 (exists is false before the existence starts or after it ends; status read from it); B-D §2.4 claims vocabulary (NOT_HOLDING/ended → "denied") | `denied` covers explicit denial and temporal non-existence at t | As established | n/a | documentation | low | ELIGIBLE; gold uses `denied` for ended or not-yet-started existence | contract note | occurrence-status-vocabulary |
| D-OS-3 | SB LABS-1.011 (describes judged in the asked context, at t); D §2 (`occurrence()` judges at the account's start); D-D §3.2 ("as occurrence_status reports it" names the vocabulary, not the time) | Each reader follows its own approved text | `occurrence_status` judges the link at t; `occurrence()` at the account's start | n/a | documentation | low | ELIGIBLE (differences arise only for time-bounded describes links) | contract note | occurrence-projection |
| D-OH-1 | D2 §1 and C-D C-5 (approved) supersede D2D §2-3 | No slot, no inference about the unmentioned, `status` None without conflict, unaccepted claims in `evidence` | As D2 and C-5 | n/a | documentation | low | ELIGIBLE (cite D2 and C-5, never D2D §2-3) | contract note | office-holders-history |
| D-OH-2 | ID-D §3.8 (identity class selection); ID-D (same-as relates particulars only, so concepts have no aliases) | Context by identity class; office (a concept) by its id | Matches that; `holder` shows the first attestation's stated name | n/a | api-convention | low | ELIGIBLE; with aliased holders, gold accepts any member of the class | contract note | identity-in-readers |
| D-OH-3 | common P-5 (approved: a precondition failure is not a refusal) | The missing profile is an execution precondition | `ValueError` from `_require` | n/a | superseded | n/a | n/a | none (superseded by P-5) | refusals |

**Counts.**

| Class | Count | Items |
|---|---|---|
| semantic-defect | 1 | D-VA-3 |
| provenance-defect | 1 | D-VA-1 |
| unsupported | 0 | (the parameter part of D-HO-2 maps to the existing GAP-SPATIAL-8) |
| unresolved-decision | 6 | D-HO-1, D-HO-2, D-VA-2, D-FA-1, D-OC-3, D-OS-1 |
| api-convention | 5 | D-HO-3, D-HO-4, D-FA-3, D-OC-1, D-OH-2 |
| documentation | 6 | D-VA-4, D-VA-5, D-FA-2, D-OS-2, D-OS-3, D-OH-1 |
| superseded | 4 | D-HO-5, D-VA-6, D-OC-2, D-OH-3 |

### Semantic decisions

### SD-CORE-1. What does `holds()` ask when the question binds only some of a content's roles? (D-HO-1, D-HO-2)

**Alternatives**
- **(a) Exact content.** The given roles are the content's whole role set; a role not given is absent. For example,
  `classified-as(classified, class)` is the content without a context.
  - Grounds: v0.2 §4.2 (structural identity is the canonical key: type, role bindings, parameters); B-D §3 (the record
    "of one content"); R R2 (a question that names no content must not look like an answer).
  - Parameterised types stay a gap under A2 D-A2-5 / GAP-SPATIAL-8.
- **(b) Existential question.** "Does some content with these players hold?", answered by rule Q over every matching
  record, which makes it independent of order.
  - Grounds: C-D §3.1 (one question answered by several holdings; rule Q is defined for one-question readers).
  - It would make `holds` a one-question aggregate, which C-D §4 lists as "one content, reference".
- **(c) Refuse incomplete questions.** Unless every required role is bound, refuse with a domain error, by analogy with
  R2.
  - Optional roles (such as the context of `classified-as`) still need rule (a) to define what "bound" means.

**Recommendation: (a).** It follows the approved definition of content identity and of `holds` as a projection of one
record, and it is order-independent by construction. (b) changes `holds` from the reference reader into an aggregate,
against C-D §4. The current subset match is not adopted: no design states it, and it is order-dependent (D-HO-2).

### SD-CORE-2. `value_at` given `key_role` but not `value_role` (D-VA-2)

**Alternatives**
- **(a) Refuse as malformed.** Grounds: A0 ("the question must say which"); R R2 (a malformed question must not look
  like an answer, as UNKNOWN does).
- **(b) Derive `value_role`** from the unique declared constraint whose key is `key_role`, and refuse if there is none
  or more than one. Grounds: A0.3 constraints as data.
- **(c) Require both roles only when they do not form a declared constraint.** This is a variant of (b) that keeps the
  inverse use allowed by the A0 shelf case.

**Recommendation: (a).** It is the reading closest to A0's wording and to R2's principle. An UNKNOWN that is not
"nothing decides t" (v0.2 §5.6) is the worst outcome. (b) remains a compatible later extension.

### SD-CORE-3. Must a listing that shows a content disputed under an attested constraint cite the constraint? (D-FA-1)

**Alternatives**
- **(a) Extend DI-19 additively** to listing entries: a `constraint_support` per `facts_about` entry, from the same
  record.
  - Grounds: B-D §2 (one canonical record; every reader takes its facts from it); DI-19's reason ("a reader cannot see
    from the answer alone which rule caused the dispute", REG DI-19); E2DEC §4 evidence recall.
- **(b) Keep listings at B-D §4** (assertions, denials, constraint rivals). Constraint provenance is read through
  `holds()` or `office_holders` (`conflict.constraint.support`). Grounds: DI19 / LABS-1.060 scoped the correction to
  `holds()`.

**Recommendation: (a).** DI-19's justification applies equally to a listing that marks the same content DISPUTED. The
change is additive, so no existing field changes, as with DI-19 itself. Until the owner decides, no `facts_about`
question requires the constraint's attestation.

### SD-CORE-4. `occurrence()` and `occurrence_status()` called with an id that is not an occurrence (D-OC-3, D-OS-1)

**Alternatives**
- **(a) Refuse with a domain error** ("not an occurrence"), nothing answered. Grounds: SB LABS-1.011 scopes the
  readers to occurrences; R R2 principle.
- **(b) Treat it as an execution precondition** under common P-5, widened from "an id that names nothing" to "an id of
  the wrong kind". It is reported as an execution error, not a refusal.
- **(c) Answer by the Core 0.3 rule for other things** (participation implies existence). This is current behaviour,
  but a description id passed by mistake would read `accepted` from its own participation, which works against Occ-1's
  intent (SB LABS-1.012).

**Recommendation: (b) for E2.** It needs no semantic change and is consistent with the approved P-5. (a) is the
long-term form, if the owner wants it documented as a refusal. (c) is not recommended: SB's decision exists precisely
so that participation never makes an occurrence "accepted".

## Part B. Spatial

Sources: contracts in `benchmark/e2/spec/reader-contracts.md` (spatial section); evidence
`docs/stage-e/e2-reader-contracts/evidence-spatial.md`; diagnostics `docs/stage-e/e2-contract-adjudication/diagnostics.json`
(DX-1, DX-2). Abbreviations as in the contract (A1, A2, v0.2, Plan, IB-D, ID-D, INV, common). Read-only; nothing run.

Counts: semantic-defect 3, provenance-defect 4, unsupported 1, unresolved-decision 5, api-convention 7,
documentation 2, superseded 1 (23 items).

| ID | Authoritative design source | Expected (where established) | Implementation behaviour (reported) | Reproduced | Class | Severity | E2 eligibility | Recommended disposition | Group |
|---|---|---|---|---|---|---|---|---|---|
| D-TB-1 | A2 "Agreement", "Orientation comparison policy / Where it applies"; D-A2-7 (unconfirmed) | silent on which angular tolerance decides chain agreement | always 1e-9 rad; no parameter | no (inspection only) | unresolved-decision | medium | BLOCKED: questions with rotation disagreement between 1e-9 rad and a caller tolerance | decision SD-SPA-1 (frame-tolerance) | frame-tolerance |
| D-TB-2 | v0.2 5.6 (UNKNOWN vs NOT_YET_KNOWN); common 0.7 rule 2 (approved P-4) | silent on source == target and on unknown/unlinked frames with nothing visible | INFERRED identity transform, empty chain, rule presented with no premises; never NOT_YET_KNOWN | no (inspection only) | unresolved-decision | low | BLOCKED: source == target questions; NOT_YET_KNOWN vs UNKNOWN for S4 with no visible transforms (S4 with visible transforms ELIGIBLE: UNKNOWN [E]) | decision SD-SPA-2 (chain-trivial-and-empty) | chain-trivial-and-empty |
| D-TB-3 | A2 "Outcomes" (disputed transform on any route: DISPUTED); v0.2 5.3 "never silent"; common 0.4 (P-1 approved) | DISPUTED, with the disputed transform's attestations reported as conflicting evidence | DISPUTED with reason only; an off-chain disputed edge is in neither `chain` nor `search.inconsistent` | no (inspection only) | provenance-defect | medium | ELIGIBLE (S3) | DI-29 (dispute-sides-cited) | dispute-sides-cited |
| D-TB-4 | IB "Points decided" 6; ID-D 3.8, ID-8; deferred-issues DI-12 (closed) | frames cannot be same-as; chains unaffected by identity | code comment and GAP-SPATIAL-5 call it deferred | n/a | documentation | low | ELIGIBLE (contract TB-15 stands) | documentation fix (being corrected) | identity-in-readers |
| D-TB-5 | A2 "Resource limit" | `complete: true` for a completed no-chain search; `verified` not stated | `verified: false` | no (inspection only) | api-convention | low | ELIGIBLE; questions do not expect `search.verified` when no chain exists | contract note | search-metadata |
| D-TB-6 | Plan 9.6 "Time" | derived result holds over the intersection of input intervals; knowledge time = latest input | answers at instant t only; neither interval nor knowledge time reported | no (inspection only) | unsupported | low | G probe for "over which interval / since when known" of a derived pose or transform; point-at-t questions ELIGIBLE | proposed gap GAP-SPATIAL-9 (derived-validity-reporting; unsupported, G probe) | derived-validity-reporting |
| D-TB-7 | v0.2 6.2 ("Unaccepted attestations by others are returned as alternatives") | unreviewed transforms bearing on the answer listed as alternatives | no `alternatives` field | no (inspection only) | provenance-defect | medium | ELIGIBLE (S5) | DI-29 (alternatives-reporting) | alternatives-reporting |
| D-TB-8 | A2 "Resource limit" (LABS-1.009); A2 "Outcomes" | silent on a truncated-but-reached chain that contains a disputed edge | UNKNOWN, unverified, composed transform returned | no (inspection only) | unresolved-decision | low | BLOCKED: truncated searches through a disputed edge | decision SD-SPA-3 (truncation-with-dispute) | truncation-with-dispute |
| D-TB-9 | A2 "Results", "Resource limit" | `chain`, `frames`, `search` with the A2-named metadata | extra step fields (`translation`, `rotation`, `disputed`), `edges_in_graph`, `relevant_edges`, extra reason strings | n/a | api-convention | low | ELIGIBLE; questions do not expect the extra fields or reason strings beyond A2's three | contract note | search-metadata |
| D-WH-1 | A2 "Orientation comparison policy"; D-A2-7 (unconfirmed) | candidate comparison uses `angle_tolerance` [E]; chain agreement tolerance not stated | chain agreement fixed at 1e-9 rad; candidate comparison uses `angle_tolerance` | no (inspection only) | unresolved-decision | medium | BLOCKED: derived candidates whose chains disagree by less than a caller tolerance; other F questions ELIGIBLE | decision SD-SPA-1 (frame-tolerance) | frame-tolerance |
| D-WH-2 | A2 "Position judgement" (compatible / conflict); A2 LABS-1.009 | `compatible` = overlapping ranges can both be true; conflicts listed | adds `single`, None; `compatible` also when a pair was not compared (chain-disputed candidate) or only an unverified disjoint pair exists | no (inspection only) | unresolved-decision | medium | BLOCKED for `judgement` in those cases; ELIGIBLE for `compatible` (verified overlapping pairs) and DISPUTED with `conflicts` | decision SD-SPA-4 (position-judgement-label) | position-judgement-label |
| D-WH-3 | A2 "Provenance" (position is a premise); v0.2 5.2 E6; common 0.7 (P-4 approved: premise must be visible, usable, applicable, not disputed unless answer DISPUTED) | a derived candidate from a position disputed by an accepted denial is not INFERRED; the answer is not an undisputed INFERRED | `poses` DISPUTED, derived candidate INFERRED, `where` INFERRED | yes, DX-1 | semantic-defect | high | ELIGIBLE (F2/F3 with a disputed position) | DI-25 (disputed-premise) | disputed-premise |
| D-WH-4 | A2 "Time, perspective and worlds" ("Unreviewed claims are listed as alternatives"); A2 "Candidates" (every position statement of the thing, any frame) | unreviewed position claims of the thing are alternatives | ids of unreviewed, unsuperseded position claims of the thing with a verdict at t, in any frame | no (inspection only) | api-convention | low | ELIGIBLE: contract fixes alternatives as unreviewed position claims of the thing in any frame (symmetric with candidates), compared as an id set | contract note | alternatives-reporting |
| D-WH-5 | ID-D 9, ID-8 (approved); common 0.2 | the thing is judged with its established same-as group; asking by any member gives the same candidates | asking by the alias under which the position was stated returns no candidates; canonical name works | yes, DX-2 | semantic-defect | high | ELIGIBLE (F1/F2 asked by an alias) | DI-24 (identity-in-readers) | identity-in-readers |
| D-WH-6 | common 0.9; A2 silent on order | multiset comparison; conflicts identified by candidates | candidates by stated frame id; `conflicts` as index pairs | n/a | api-convention | low | ELIGIBLE: candidates picked by field, `conflicts` resolved to candidate identities, never by position | contract note | listing-order |
| D-WH-7 | Plan 9.6 "Time" | as D-TB-6 | as D-TB-6 | n/a | superseded | low | n/a | none (superseded by D-TB-6) | derived-validity-reporting |
| D-PO-1 | A2 "The same rule everywhere"; IB "Readers" (DI-1) | slot conflicts and polarity disputes listed as DISPUTED | behaves as designed; docstring stale | n/a | documentation | low | ELIGIBLE (contract PO-3/PO-4 stand) | documentation fix (being corrected) | listing-dispute-sides |
| D-PO-2 | IB-D 4 ("citing the assertions, the denials and any constraint rivals") | disputed entries cite both sides | `judgement`, `assertions`, `denials` not projected; polarity denials not cited | no (inspection only) | provenance-defect | medium | ELIGIBLE (conflicting evidence of a polarity-disputed pose) | DI-29 (listing-dispute-sides) | listing-dispute-sides |
| D-PO-3 | ID-D 9, ID-8 (approved) | same as D-WH-5 for `poses` | `poses(alias)` empty; `poses(canonical)` finds the position | yes, DX-2 | semantic-defect | high | ELIGIBLE (poses asked by an alias) | DI-24 (identity-in-readers) | identity-in-readers |
| D-PO-4 | common 0.9 | multiset | sorted by frame id | n/a | api-convention | low | ELIGIBLE; compared as a multiset, picked by `frame` | contract note | listing-order |
| D-FI-1 | IB-D 4; DI-1 correction | disputed transforms, anchors and positions marked and cited on both sides | `anchored_to` without support; `positioned` ids without status or support; no conflicts/denials | no (inspection only) | provenance-defect | medium | ELIGIBLE for transform/anchor status and support; questions do not expect a status on `positioned` until fixed (expected as [E], scored, may fail) | DI-29 (listing-dispute-sides) | listing-dispute-sides |
| D-FI-2 | A1 "API" (reads judged); A1 "Tests" (identity is the id, a description is text) | names are display text; not a judged domain fact in the design | read directly, unjudged | n/a | api-convention | low | ELIGIBLE; questions do not expect `name` | contract note | display-names |
| D-FI-3 | A1 "Selected results" (anchor, transforms with status) | anchor and one-hop transforms with status | field names and `positioned` docstring-only | n/a | api-convention | low | ELIGIBLE for anchor, parents, children (contract fixes names); questions do not expect `positioned` | contract note | listing-order |

Note on D-FI-1 eligibility: under the amended rules a provenance-defect against an approved contract is ELIGIBLE; the
contract's [E] requirement (IB-D 4) is scored even though the implementation is expected to fail it.

### Semantic decisions

### SD-SPA-1: which angular tolerance decides frame-chain agreement? (D-TB-1, D-WH-1; frame-tolerance)
- (a) The question's `angle_tolerance`, in `where` and as a new parameter of `transform_between`: v0.2 6.1 puts
  policies Π in the question context; A2 "Where it applies" says the same measure serves chain agreement.
- (b) Always the default 1e-9 rad: transforms are exact values with no stated uncertainty (A2 "Conventions": rotations
  exact; "Known limitations"; GAP-SPATIAL-1), and D-A2-7 names the question's tolerance as an accuracy of the
  compared *claims* (A2: "for example a sensor's stated angular accuracy").
- (c) A separate, reported chain-agreement tolerance parameter, default 1e-9 rad.
- **Recommendation: (b), with D-A2-7 confirmed in that wording.** A position's sensor accuracy says nothing about
  whether two transform claims agree; applying it to chains would accept disagreeing transforms without a resolution
  policy, contrary to A2 "Nothing is reconciled" and v0.2 5.3 (resolution only by acceptance or a named policy).
  Until transforms carry uncertainty (GAP-SPATIAL-1), only numerical noise may be absorbed. The answer should state
  the chain tolerance used (as A2 "Reporting" does for candidates).

### SD-SPA-2: trivial and empty chains (D-TB-2; chain-trivial-and-empty)
Question: what is answered for `source == target`, and when is "no chain" NOT_YET_KNOWN rather than UNKNOWN?
- (a) As implemented: identity INFERRED under `frame-transform/v1` with no premises; never NOT_YET_KNOWN. Conflicts
  with common 0.7 rule 2 (a derivation names at least one premise) and v0.2 5.6.
- (b) `source == target`: identity transform by convention (Plan 9.6 composition identity), **no derivation
  presented**, status INFERRED as "a declared query-time rule concludes it" (v0.2 5.6). No chain: NOT_YET_KNOWN when
  no `frame-transform` record involving `source` or `target` is visible at `as_of`, UNKNOWN otherwise (v0.2 5.6).
- (c) `source == target` refused or UNKNOWN unless the frame is known; no-chain always UNKNOWN (A2 "Missing").
- **Recommendation: (b).** It keeps the trivial answer, removes a premise-less derivation that the approved P-4 rule
  would flag as fabricated, and applies v0.2 5.6's visible/not-visible distinction to the relation asked about, which
  A2's "UNKNOWN, no frame chain" does not exclude (A2 never addresses the nothing-visible case).

### SD-SPA-3: truncated search whose reached chain contains a disputed transform (D-TB-8; truncation-with-dispute)
- (a) As LABS-1.009 literally: UNKNOWN, unverified candidate transform returned.
- (b) UNKNOWN with no transform: a chain through a disputed transform never yields a transform (A2 "Outcomes").
- (c) DISPUTED with no transform: a disputed transform on a known route already decides (A2 "Outcomes": "a disputed
  transform on any route: DISPUTED"), and LABS-1.009 lets verified conflicts decide despite truncation.
- **Recommendation: (c).** The dispute is established on a route actually found, so completeness of the search is not
  needed to decide it; returning a transform through a disputed edge contradicts A2 "Outcomes". (a) treats an
  established dispute as merely unverified.

### SD-SPA-4: the `where` judgement label when not every pair is decided (D-WH-2; position-judgement-label)
- (a) `compatible` only when every pair of positioned, verified candidates was compared and overlaps; `conflicting`
  on a verified conflict; otherwise no label (undecided). `single`/None as conventions for one/no candidate.
- (b) As implemented: count-based (`compatible` for two or more candidates without a verified conflict).
- (c) No `judgement` field in the contract; questions use `status`, `conflicts`, `conflict_details` only.
- **Recommendation: (a).** A2 defines "compatible" as overlapping ranges that can both be true; labelling an
  uncompared pair (a candidate with no position, or an unverified disjoint pair) compatible asserts an overlap the
  model has not established, against A2 "never guessed" and LABS-1.009 ("an unverified candidate … cannot support an
  authoritative answer"). (b) is not justified by any design text.

## Part C. Measurement and calibration

### Scope and sources
- **Items:** every D item in `benchmark/e2/spec/reader-contracts.md`, sections `measurements`, `compare_measurements`,
  `convert`, `laboratory.calibration_status` and `laboratory.measurement_calibration`.
- **Evidence:** `docs/stage-e/e2-reader-contracts/evidence-measurement.md`.
- **Reproductions:** `docs/stage-e/e2-contract-adjudication/diagnostics.json`, cases DX-3, DX-4 and DX-5.
- **Approved proposals applied** (LABS-1.063): P-1 to P-5, P-ME-1, P-CM-1 (with the shared role amendment), P-CS-1,
  P-MC-1 and P-CV-1.
- **Method:** read-only. Nothing was run besides the diagnostics already recorded.

Abbreviations used in the table:
- **v0.2:** `docs/architecture/world-ontology-v0.2.md`;
- **stage-c:** `docs/core-0.4/stage-c.md`;
- **d3:** `docs/core-0.4/stage-d3.md`;
- **d3-design:** `docs/core-0.4/stage-d3-design.md`;
- **incB / incC:** the increment B and C design documents;
- **incC-rep:** `docs/core-0.4/pre-e-increment-c.md`;
- **ID:** `docs/core-0.4/pre-e-identity-design.md`;
- **plan:** `docs/plans/core-0.4-plan.md`;
- **common:** `contracts/common.md`.


| ID | Authoritative design source | Expected (where established) | Implementation behaviour (reported) | Reproduced | Class | Severity | E2 eligibility | Recommended disposition | Group |
|---|---|---|---|---|---|---|---|---|---|
| D-ME-1 | none (stage-c C1 is silent on `t`); common §0.2 (t is valid time) | not established | `t` keeps attestations whose own interval holds at t; denials covering t are dropped | no (inspection only) | unresolved-decision | medium | BLOCKED for questions passing `t` (use `t=None`) | decision SD-MEA-1 (measurement-t-filter) | measurement-t-filter |
| D-ME-2 | v0.2 §3.3 and C4 (k = 2 "95 %", k = 3 "99.7 %"); D-C-1 | coverage level is a function of k (normal coverage) | erf(k/√2): 0.9545 at k = 2 | n/a | api-convention | low | ELIGIBLE: the contract fixes erf(k/√2) with a stated tolerance (E2 §5.3) | contract note | coverage-level |
| D-ME-3 | v0.2 §6.2 (usability has no polarity condition), §5.3; common §0.4 P-1 (accepted denials are conflicting) | an accepted denial is usable conflicting evidence | `usable` = usable AND polarity, so an accepted denial is shown as unusable (an alternative under P-ME-1); with `t` it is absent | yes, DX-4 (denial not listed with `t`) | provenance-defect | medium | ELIGIBLE | DI-26 (measurement-denials) | measurement-denials |
| D-ME-4 | v0.2 §5.2 E1 (one attester), §5.6 layer 1 (basis), §4.4 (interval on the attestation) | attester, basis and valid interval are attestation facts | extra fields `attester`, `basis`, `valid`, `content` | n/a | api-convention | low | ELIGIBLE for `attester`, `basis`, `valid` (fixed by contract note); questions do not expect `content` | contract note | output-fields |
| D-ME-5 | ID §3.8 ID-8 ("every reader … selects contents by the subject's whole identity class"); v0.2 §4.2 | measurements of an alias are measurements of the bearer | literal-id filter: `measurements(box)` = 0 while `measurements(box-alias)` = 1 | yes, DX-3 | semantic-defect | high | ELIGIBLE | DI-24 (identity-in-readers) | identity-in-readers |
| D-ME-6 | plan §9.2 (content has "the quality's valid time"); v0.2 §5.6 (an observation supports at t within its phenomenon interval); no text on instant intervals | not established | the content is attested over [s, s) (empty), so `measurements(t=s)` = 0 and two such measurements are "incomparable: valid times do not overlap" | yes, DX-5 | unresolved-decision | high | BLOCKED for instant measurements (fixtures may use `persists` or an end after the start meanwhile) | decision SD-MEA-2 (point-intervals) | point-intervals |
| D-ME-7 | P-ME-1 (approved LABS-1.063): supporting = usable measurement attestations; everything else is an alternative | statements are alternatives | (harness extractor counts usable statements) | n/a | superseded | n/a | n/a | none (superseded by P-ME-1; harness extractor to follow it) | statement-role |
| D-ME-8 | common §0.8 P-5 (precondition, not a refusal) | not a refusal | an unknown bearer or quality gives `[]` | no (inspection only) | api-convention | low | ELIGIBLE: an id with nothing recorded expects `[]` (compare: NOT_YET_KNOWN, D-C-5) | contract note | unknown-ids |
| D-ME-9 | v0.2 §3.3 (value may be a category); plan Stage C (`has-quality` value or range); stage-c C1 ("every stated value") | not established for this reader (clarification B is defined only for ranges) | categorical `has-quality` values are not listed | no (inspection only) | unresolved-decision | low | BLOCKED for categorical-quality questions on `measurements` | decision SD-MEA-3 (categorical-qualities) | categorical-qualities |
| D-ME-10 | D-C-1 ("the reported content is in SI"); v0.2 §3.3 (content stored in a canonical unit) | `has-quality` content is in the SI unit | generic `attest` stores a statement in any unit; the reader reports it as stored | no (inspection only) | semantic-defect | low | ELIGIBLE (fixtures write statements in SI; a non-SI statement is a writer edge case) | DI-30 (canonical-units) | canonical-units |
| D-CM-1 | v0.2 clarification B ("with the reason") | a reason is given | fixed English strings | n/a | api-convention | low | ELIGIBLE for `relation`; questions do not expect the `reason` text, only its category | contract note | output-fields |
| D-CM-2 | common §0.4 (alternatives: unaccepted, superseded, non-supporting); v0.2 §6.2 | unusable measurements are alternatives; accepted denials are conflicting | every unusable measurement is in `alternatives` (docstring: "unaccepted") | n/a | documentation | low | ELIGIBLE (the denial part follows D-CM-6) | documentation fix | measurement-denials |
| D-CM-3 | v0.2 clarification B ("non-overlapping valid times for a changing quantity"); no text on which quantities change | not established | the test applies to every quantity | no (inspection only) | unresolved-decision | medium | BLOCKED for comparisons of measurements whose valid times do not overlap | decision SD-MEA-4 (valid-time-comparability) | valid-time-comparability |
| D-CM-4 | D-C-1 (content in the dimension's SI unit); v0.2 ("units without an accepted conversion") | units differ only when the dimensions differ | compares SI unit ids; two SI-like units in one dimension would split | no (inspection only) | documentation | low | ELIGIBLE (fixtures define one SI unit per dimension) | contract note | output-fields |
| D-CM-5 | stage-c D-C-5 (UNKNOWN: something held, nothing applicable) | UNKNOWN when statements or alternatives exist but no usable measurement | the same | n/a | documentation | low | ELIGIBLE | contract note | unknown-vs-not-yet-known |
| D-CM-6 | v0.2 §5.3 (accepted assertion and accepted denial: DISPUTED); stage-c "Disputes" | DISPUTED, citing both, with or without `t` | ASSERTED without `t` (denial not listed); NOT_YET_KNOWN with `t` | yes, DX-4 | semantic-defect | high | ELIGIBLE | DI-26 (measurement-denials) | measurement-denials |
| D-CM-7 | stage-c D-C-2 regression tests (identical values at 20 °C and 35 °C: "the pair is incomparable"); stage-c "Disputes" (each attestation's own conditions) | pairs are attestation pairs (stage-c refines the v0.2 "contents" wording) | attestation pairs | n/a | documentation | low | ELIGIBLE (`pairs` compared as a multiset of unordered {a, b}) | contract note | pair-unit |
| D-CM-8 | v0.2 clarification B ("different coverage levels") | levels differ | tolerance of 1e-6 | n/a | api-convention | low | ELIGIBLE (fixtures use k values whose levels are equal or clearly distinct) | contract note | coverage-level |
| D-CV-1 | stage-c C1 API (silent on the default) | not established | `to=None` gives the SI value | n/a | api-convention | low | ELIGIBLE with `to` given explicitly; questions do not rely on the default | contract note | convert-default |
| D-CV-2 | plan Stage C (a unit owns si-factor and si-offset); E2 §5.3 (gold by standard mathematics) | si = raw × si-factor + si-offset (the meaning of the attributes) | the same | n/a | documentation | low | ELIGIBLE | contract note | convert-formula |
| D-CV-3 | v0.2 §3 (reference systems are timeless abstract entities) | no context applies | `as_of` cannot hide a unit | n/a | documentation | low | ELIGIBLE | contract note | convert-formula |
| D-CV-4 | none | not established | non-finite input is not checked | n/a | api-convention | low | ELIGIBLE: questions use finite inputs only | contract note | convert-default |
| D-CV-5 | as D-CV-1 | as D-CV-1 | with `to=None` no SI unit needs to exist | n/a | superseded | n/a | n/a | none (superseded by D-CV-1) | convert-default |
| D-CS-1 | d3 §2 (field named, undefined) | not established | certificates judged established, even when the overall answer is disputed | n/a | api-convention | low | ELIGIBLE: questions do not expect `in_force` (use `certificates[*].judgement`) | contract note | output-fields |
| D-CS-2 | ID §3.8 ID-8 (`_contents` selects by class members) | the instrument is judged with its identity class | `_contents` selects by class members | no (inspection only) | documentation | low | ELIGIBLE | contract note (ID-8 applies) | identity-in-readers |
| D-CS-3 | disputed: P-1 as amended and P-CS-1 (approved). Not yet effective: incC-rep "Points decided" 2 (support empty) versus common §0.4 (supporting = what the judgement rests on) and E1 gold LAB-003 | disputed: the accepted claims of the disputing holdings are conflicting. Not yet effective: not established | `support` is empty in both cases; the claims are visible in `certificates[*].evidence` | no (inspection only) | unresolved-decision | medium | disputed: ELIGIBLE (conflicting sets per P-1). Not yet effective: BLOCKED for evidence fields only; `judgement` is eligible | decision SD-MEA-5 (undecided-evidence) | undecided-evidence |
| D-CS-4 | common §0.9 | multiset | sorted by certificate id | n/a | api-convention | low | ELIGIBLE (multiset) | contract note | ordering |
| D-MC-1 | as D-ME-1; D-D3-2 (calibration at the activity's start) | calibration is judged at the activity start whatever `t` is; the `t` filter is not established | `t` filters measurements as `measurements(t)` | no (inspection only) | unresolved-decision | medium | BLOCKED for questions passing `t` | decision SD-MEA-1 (measurement-t-filter) | measurement-t-filter |
| D-MC-2 | stage-c "As implemented" (activity times come from the account, judged); v0.2 §6.2 (unaccepted attestations never support) | no usable account means no time, so no calibration judgement | `attested` None | n/a | documentation | low | ELIGIBLE | contract note | calibration-instant |
| D-MC-3 | D-D3-2 and d3 §3 ("the activity's start"); v0.2 §4.5 (windows; no invented precision) | an exact start: established. An uncertain start window: not established | the earliest bound of the start window | no (inspection only) | unresolved-decision | medium | ELIGIBLE for exact starts; BLOCKED for uncertain start windows | decision SD-MEA-6 (calibration-instant) | calibration-instant |
| D-MC-4 | d3 §3 table (five cases, no precedence) | each case as defined | fixed precedence: instrument, reference, certificate, match | n/a | api-convention | low | ELIGIBLE where exactly one case applies | contract note | reference-check |
| D-MC-5 | d3 §3 ("no certificate recorded for the instrument" = the instrument has no calibration content) | that check only when the instrument has no certificates | reported also when the activity has no usable account and certificates exist | no (inspection only) | semantic-defect | medium | ELIGIBLE | DI-30 (reference-check) | reference-check |
| D-MC-6 | d3 §2 (per measurement record and activity instrument); common §0.9 | one row per (record, instrument); multiset | per attestation × record × activity × instrument; rows with activity or instrument None; no rows for statements | n/a | api-convention | low | ELIGIBLE: rows selected by `[record, instrument]`; questions do not expect row counts | contract note | ordering |
| D-MC-7 | D-D3-2 and D-D3-3 (approved LABS-1.028) supersede D-D-7 and G6 | calibration is reported by `measurement_calibration`, not `measurements()` | as the later decision | n/a | superseded | n/a | n/a | none (superseded by D-D3-2 and D-D3-3) | calibration-placement |

**Counts by class (34 items):**
- semantic-defect: 4 (D-ME-5, D-ME-10, D-CM-6, D-MC-5);
- provenance-defect: 1 (D-ME-3);
- unsupported: 0;
- unresolved-decision: 7 (D-ME-1, D-ME-6, D-ME-9, D-CM-3, D-CS-3, D-MC-1, D-MC-3);
- api-convention: 11;
- documentation: 8;
- superseded: 3.

**High severity:**
- D-ME-5: identity is not applied (DX-3).
- D-CM-6: an accepted denial leaves the comparison ASSERTED (DX-4).
- D-ME-6: point measurements never hold and are mutually incomparable (DX-5).

**Proposed DI groups:**
- **identity-in-readers:** D-ME-5. Shared with the spatial family's D-WH-5 / D-PO-3.
- **measurement-denials:** D-CM-6 and D-ME-3. D-CM-2 is documentation only.
- **canonical-units:** D-ME-10.
- **reference-check:** D-MC-5.

### Semantic decisions

### SD-MEA-1: what does `t` mean in the measurement readers? (D-ME-1, D-MC-1)
- **The question.** When `t` is given to `measurements`, `compare_measurements` or `measurement_calibration`, which
  entries are included?
- **Alternatives:**
  - **(a) Each attestation's own interval** holds at t, keeping only positive verdicts. This is the current
    behaviour. It is grounded in v0.2 §4.4 (time is on attestations). It drops denials covering t, which contradicts
    v0.2 §5.3.
  - **(b) Valid time as in every other reader** (common §0.2; incB §2.1, "a record is a judgement at t"). Every
    attestation whose verdict at t is not silent is included, assertions and denials alike. Each keeps its acceptance
    and role, so a denial covering t stays visible as conflicting evidence (P-1).
  - **(c) No filter.** `t` is reserved, and the collection lists every value with its valid interval (stage-c C1
    "every stated value"; GAP-MEAS-7, no current-value reader).
- **Recommendation: (b).**
  - `t` is valid time everywhere else.
  - A filter that silently removes the other side of a dispute contradicts v0.2 §5.3 and the approved P-1 roles.
  - For `measurement_calibration`, `t` selects measurements only; calibration stays at the activity's start
    (D-D3-2).
  - (a) is not adopted merely because it is implemented.

### SD-MEA-2: the valid time of a measurement over an instant (D-ME-6)
- **The question.** A measurement written with a start and no end, and without `persists`, gets [s, s). Should its
  content hold at s, and be comparable with another measurement at s?
- **Alternatives:**
  - **(a) An instant attestation holds at its instant.** A degenerate interval [s, s] is closed. Grounds:
    - v0.2 §5.6, OBSERVED: an observation supports at t within its phenomenon interval, and an instantaneous
      phenomenon includes its instant;
    - plan §9.2: the activity has an occurrence interval and the content "the quality's valid time";
    - v0.2 C4 compares measurements stated at one time.
  - **(b) Keep half-open intervals universally** (Core 0.3 `in_interval`, `supersession-and-endings.md`) and treat a
    content with an empty interval as a writing error: `measure` must be given an end after the start, or `persists`.
    The empty case becomes a documented precondition (common §0.8).
  - **(c) Measured content persists from the activity start until superseded by default** (as `calibrate` does,
    E1 CLARIFICATIONS C2). This is not grounded for quantities that change: v0.2 §4.4 says "no invented continuity".
- **Recommendation: (a), limited to the reported content of a measurement.**
  - It is the only alternative under which a measurement at an instant says what its source observed at that
    instant.
  - (b) is acceptable if the owner wants half-open intervals without exception. It must then be stated as a writer
    precondition, not left as a silent empty interval.

### SD-MEA-3: categorical qualities in `measurements` (D-ME-9)
- **The question.** Should `measurements` list `has-quality` values that are categories ("open", a colour)?
- **Alternatives:**
  - **(a) List them as statements** (or as measurements, if they rest on records), with their category value.
    Grounds: stage-c C1 "every stated value"; v0.2 §3.3, value or category.
  - **(b) Out of scope.** `measurements` and `compare_measurements` cover interval-valued quantities (D-C-1: range in
    SI with a coverage level; clarification B defines comparison only for ranges). Categorical values are read
    through `holds` and `facts_about`.
- **Recommendation: (b), stated in the contract.**
  - The Stage C measurement model (record with u and k, range, coverage) is defined only for ranges.
  - Categorical comparison would need semantics no design gives.
  - "Every stated value" is read as every stated value of the measured quantity. A categorical-measurement question
    is then a G probe.

### SD-MEA-4: the valid-time reason for incomparability (D-CM-3)
- **The question.** v0.2 makes non-overlapping valid times a reason for incomparability "for a changing quantity",
  and nothing says which quantities change.
- **Alternatives:**
  - **(a) Every quantity is treated as possibly changing.** Non-overlapping valid times are always incomparable.
    Grounds: v0.2 §4.4 (no invented continuity); clarification B ("never invents precision") and C4 ("no false
    disputes").
  - **(b) A quality kind or profile declares the quantity constant** (for example the rest mass of a sealed
    reference). Only then are measurements at disjoint times compared. Grounds: v0.2 §3.3, where a profile says which
    conditions matter; `stage-d-review.md` D3, profile-specific comparability (Df).
  - **(c) Ignore valid time in comparison.** This contradicts v0.2's explicit reason.
- **Recommendation: (a) now, with (b) as a later, declared extension.**
  - (a) never reports disjoint-time measurements as compatible or incompatible without a basis, which is the
    conservative reading of clarification B.
  - (b) needs an approved declaration mechanism, which does not exist yet.
  - Recording (a) also fixes the gold for M3-style valid-time cases.

### SD-MEA-5: evidence for undecided calibration answers (D-CS-3, the "not yet effective" part)
The disputed part is settled by P-1 as amended and P-CS-1: the accepted claims of the disputing holdings are
conflicting evidence and may establish the DISPUTED judgement.

- **The question.** "Not yet effective" (status UNKNOWN) has an empty `support` (incC-rep "Points decided" 2). Is
  the accepted future calibration claim required evidence?
- **Alternatives:**
  - **(a) Nothing is required.** No status rests on deciding claims (incC-rep). The claim, if cited, is an
    alternative.
  - **(b) Supporting.** The judgement "not yet effective", as opposed to "not established", is decided by that
    accepted claim (incB §2.4, reason `not_yet_effective`: "an accepted assertion begins after t"). Common §0.4
    defines supporting as what the value, status *or judgement* rests on. E1 gold LAB-003 required it. Evidence path:
    `certificates[judgement=not yet effective].evidence[acceptance=accepted].attestation`.
  - **(c) Explanatory.** It may be cited and is not required. This follows E1 CLARIFICATIONS C1 for list answers, but
    common §0.4 has no explanatory role.
- **Recommendation: (b).**
  - The judgement given rests on that claim, and the approved P-1 makes judgement-deciding claims supporting.
  - The empty `support` field is read as "no status support", not "no evidence". This is a harness extractor rule; it
    changes no reader.
  - It also keeps E1's frozen gold consistent.

### SD-MEA-6: the instant used to judge calibration when the activity's start is uncertain (D-MC-3)
- **The question.** d3 says "at the activity's start", and the start is a window. Which instant is meant?
- **Alternatives:**
  - **(a) The earliest bound** (current). This picks one end of the window without a basis.
  - **(b) The whole window.** Established only if the calibration is established at both the earliest and the
    latest bound. Otherwise use the judgement the two bounds share, or "not established" (undecided) when they
    differ. Grounds: v0.2 §4.5 windows; `certainly_before` and Core 0.3 "never a guess"; clarification B (no
    invented precision).
  - **(c) The latest bound.** This is as unjustified as (a).
- **Recommendation: (b).**
  - A calibration that might have expired within the start window is not known to have been in force.
  - (b) agrees with (a) whenever the start is exact, so questions with exact starts are unaffected.
  - Whatever is chosen, it is recorded as the GAP-MULTI-2 answer for this composition.

## Part D. Causation, change and process

**Scope.** The discrepancies D-CO, D-EF, D-EX, D-CH, D-PS, D-BE and D-IV in
`benchmark/e2/spec/reader-contracts.md` (branch `feature/e2-reader-contracts`).
- **Evidence:** `docs/stage-e/e2-reader-contracts/evidence-causal.md`.
- **Reproductions:** `docs/stage-e/e2-contract-adjudication/diagnostics.json`, cases DX-8 to DX-14, with both query
  paths agreeing.
- **Method:** the repository was read only.

**Source abbreviations.**

| Short form | File |
|---|---|
| SB | `docs/core-0.4/stage-b.md` |
| V02 | `docs/architecture/world-ontology-v0.2.md` |
| PLAN | `docs/plans/core-0.4-plan.md` |
| IBD | `docs/core-0.4/pre-e-increment-b-design.md` |
| ICD | `docs/core-0.4/pre-e-increment-c-design.md` |
| DI | `docs/core-0.4/deferred-issues.md` |
| E2D | `docs/stage-e/stage-e2-evaluation-design.md` |
| R2 | `docs/stage-e/e1-reconciliation-design.md` §R2 |

### Items

| ID | Authoritative design source | Expected (where established) | Implementation behaviour (reported) | Reproduced | Class | Severity | E2 eligibility | Recommended disposition | Group |
|---|---|---|---|---|---|---|---|---|---|
| D-CO-1 | PLAN §9.3 "Lifting, per perspective" (DX-4, approved per PLAN §9.1); SB U-2 | A description-level claim answers an occurrence question only when **both** descriptions have usable describes links | A cause description with no describes link is returned `lifted`, `applies: true`, `cause_occurrences: []` | yes, DX-8 | semantic-defect | high | ELIGIBLE | DI-28 (causal-lifting) | causal-lifting |
| D-CO-2 | PLAN §9.3 ("cites the describes links"); SB "Lifting" ("says which link it used") | The lifted answer cites the describes links' attestations | `lifted_via` is {description, occurrence} ids only, effect side only; the link's 2 attestations are not cited | yes, DX-9 | provenance-defect | medium | ELIGIBLE | DI-28 (causal-lifting) | causal-lifting |
| D-CO-3 | SB U-2 ("accepted describes link"); V02 §3.2 (a describes link is "usable only when accepted"); IBD §2 (one canonical judgement; "nothing else judges content") | A link whose canonical judgement is DISPUTED is not accepted and does not lift | A link disputed by an accepted denial still lifts (any usable positive attestation counts) | yes, DX-10 | semantic-defect | high | ELIGIBLE | DI-28 (causal-lifting) | causal-lifting |
| D-CO-4 | none (common 0.9: multiset) | — | Sorted by judgement rank (6 labels, others last), then cause, then effect | n/a | api-convention | low | ELIGIBLE; questions do not expect the order of `causes_of` | contract note | listing-order |
| D-CO-5 | PLAN §9.3 (the mixed form exists, unnamed) | The level of a description → occurrence claim is the mixed form | Label `mixed`; extra field `cause_occurrences` | n/a | api-convention | low | ELIGIBLE for `level` ∈ {description, occurrence}; questions do not expect `cause_occurrences` or the literal `mixed` unless the contract fixes the label | contract note | field-names |
| D-CO-6 | none (V02 §3.2 states no irreflexivity of `causes`) | — | `claim_cause` (writer) refuses cause == effect, "a happening does not cause itself" | no (inspection only) | unresolved-decision | low | BLOCKED (no fixture or probe may rely on it as an established refusal) | decision SD-CAU-11 (writer-refusals) | writer-refusals |
| D-EF-1 | SB Q-B1.2 (UNKNOWN ↔ held is a judgement transition, "never presented as physical change"); SB B0 (`state.accepted_change`); not ruled whether Q-B1 binds `effects_of` | — (two approved texts) | `accepted_change: true` for UNKNOWN → ASSERTED, while `changes` calls the same move a judgement transition | yes, DX-14 | unresolved-decision | high | BLOCKED (C3 questions on UNKNOWN-adjacent outcomes) | decision SD-CAU-1 (effect-change-rule) | effect-change-rule |
| D-EF-2 | SB Q-B1 probe case 6 (delayed effects allowed, for `changes`); INV GAP-MULTI-2 | — | State sampled at start earliest − 1 µs and end latest only; a delayed effect gives False | no (inspection only) | unresolved-decision | medium | BLOCKED (delayed-effect C3 questions) | decision SD-CAU-1 (effect-change-rule) | effect-change-rule |
| D-EF-3 | SB D-B-6 ("an account the perspective can use"); SB B0 (claims list attestations) | Times from an accepted account | Lowest-id usable account; its attestation is not reported | no (inspection only) | unresolved-decision | medium | BLOCKED (events with several usable accounts) | decision SD-CAU-10 (multiple-accounts) | multiple-accounts |
| D-EF-4 | IBD §2.4 labelling table | Full claims vocabulary | The docstring lists 5 labels | n/a | documentation | low | ELIGIBLE | documentation fix | vocabulary-docs |
| D-EF-5 | SB Occ-2 (general wording); SB LABS-1.011 amendment (`causes_of` only) | — (scope not ruled) | No occurrence status or `applies` on effect claims | no (inspection only) | unresolved-decision | medium | BLOCKED (C3 questions about effects of denied occurrences) | decision SD-CAU-9 (occurrence-applicability) | occurrence-applicability |
| D-EF-6 | SB D-B-2 (claims are timeless); SB "Schema and API" | — | `t` judges only the claim contents; states use the event's own times | no (inspection only) | unresolved-decision | low | BLOCKED where a claim attestation carries a valid interval | decision SD-CAU-7 (claim-valid-time) | claim-valid-time |
| D-EF-7 | SB B0 deferral D2 (needs A0 ids); V02 §3.2 (two effect types) | — | `claim_effect` (writer) refuses other kinds and use without proposition ids, in code only | no (inspection only) | unresolved-decision | low | BLOCKED (as established refusals) | decision SD-CAU-11 (writer-refusals) | writer-refusals |
| D-EX-1 | SB "Schema and API" ("its **accepted** initiating events"); docstring ("with each claim's judgement") | — (which acceptance is meant is not stated; docstring differs) | Lists unreviewed initiating claims too (ev-rumour, unreviewed) | yes, DX-11 | unresolved-decision | high | BLOCKED (C4 / X4 questions with unaccepted initiators) | decision SD-CAU-2 (explain-initiators) | explain-initiators |
| D-EX-2 | SB B-time (the one approved timing rule); the "ended by t" filter appears only in an SB performance note | — | Drops initiators unless account end latest ≤ t | no (inspection only) | unresolved-decision | medium | BLOCKED (initiators overlapping t) | decision SD-CAU-2 (explain-initiators) | explain-initiators |
| D-EX-3 | SB B-time (an unavailable time is kept as "unresolved", stated for transitions) | — (B-time is stated for transitions, not holdings) | An initiator with no accepted account is dropped | yes, DX-12 | unresolved-decision | medium | BLOCKED | decision SD-CAU-2 (explain-initiators) | explain-initiators |
| D-EX-4 | SB B0 (four distinctions: "every claim lists its attestations ... in every answer"; B-arch approved LABS-1.011) | Each initiating claim lists its attestations | `initiated_by` entries have claim, claim_status, claimed_by and no attestations | yes, DX-11 | provenance-defect | medium | ELIGIBLE (questions may require the initiating claims' attestations) | DI-29 (initiating-provenance) | initiating-provenance |
| D-EX-5 | E2D C4 ("why does S hold"); SB B0 (claim independent of state) | — | Initiators are listed whatever `holds` says | no (inspection only) | unresolved-decision | medium | BLOCKED (`explain` on a non-holding content) | decision SD-CAU-3 (explain-non-holding) | explain-initiators |
| D-EX-6 | SB U-2 (lifted = answered through a describes link) | — | Causes from the event, then the occurrence, deduplicated first-kept: a direct occurrence claim may show `lifted` | no (inspection only) | api-convention | low | ELIGIBLE; questions do not expect `lifted` / `lifted_via` or the order inside `explain`'s `causes` | contract note | field-names |
| D-CH-1 | SB Q-B1.2 (world-state includes an accepted "does not hold"); SB contract schema (per-side `support`) | An accepted "does not hold" side cites its deciding attestations | after.support = [] for true → false, while `holds()` at that time cites [dep, not-dep] | yes, DX-13 | provenance-defect | medium | ELIGIBLE (both sides required) | DI-29 (transition-support) | transition-support |
| D-CH-2 | SB B0 ("every claim lists its attestations") vs SB Q-B1 contract schema (explanations without ids) | — (two approved texts) | Explanations: claim, claim_status, claimed_by only | no (inspection only) | unresolved-decision | medium | BLOCKED (requiring explanation-claim attestations) | decision SD-CAU-4 (initiating-provenance) | initiating-provenance |
| D-CH-3 | SB B-time ("start window **overlaps** the transition window" → unresolved) | — (closed vs half-open windows not ruled) | `consistent` when start.latest == window earliest | no (inspection only) | unresolved-decision | medium | BLOCKED at touching bounds | decision SD-CAU-5 (window-boundaries) | window-boundaries |
| D-CH-4 | SB Q-B1.1 (only accepted A, then UNKNOWN, then accepted B ≠ A is merged) | — | A → UNKNOWN → A gives two judgement transitions; gaps through DISPUTED are never merged | no (inspection only) | unresolved-decision | medium | BLOCKED (those shapes) | decision SD-CAU-6 (gap-transitions) | gap-transitions |
| D-CH-5 | SB D-B-2 | — | Explanation claims are judged at t2 | no (inspection only) | unresolved-decision | low | BLOCKED where claim attestations have intervals | decision SD-CAU-7 (claim-valid-time) | claim-valid-time |
| D-CH-6 | SB contract schema | Contract fields only | Extra fields in `began` / `ended` entries; transitions and explanations sorted | n/a | api-convention | low | ELIGIBLE; questions do not expect the extra `began` / `ended` fields or any order | contract note | field-names |
| D-CH-7 | SB Q-B1.4 (LABS-1.015) | The Q-B1 contract | Stale SB "Remaining limitations" and "Schema and API" text | n/a | documentation | low | ELIGIBLE | documentation fix (in progress) | stale-design-text |
| D-CH-8 | none | — | t1 ≥ t2 unspecified | no (inspection only) | unresolved-decision | low | BLOCKED (no question with t1 ≥ t2) | decision SD-CAU-8 (empty-interval) | empty-interval |
| D-CH-9 | SB Occ-2 (general wording); SB U-2 | — (scope not ruled) | Explanations list occurrences without status or `applies` | no (inspection only) | unresolved-decision | medium | BLOCKED (explanations by events of denied occurrences) | decision SD-CAU-9 (occurrence-applicability) | occurrence-applicability |
| D-PS-1 | E2D §2 ("ordered by interval start"); approved P-PS-1 (list order asserts no succession) | Ordered by start | start.earliest, then occurrence id | n/a | api-convention | low | ELIGIBLE where starts are certain and distinct; questions do not expect order among overlapping or uncertain starts | contract note | listing-order |
| D-PS-2 | INV §5 ("undated last", inventory only) | — | Undated steps keyed at the latest dated start, so they can precede it | n/a | api-convention | low | ELIGIBLE; questions do not expect the position of undated steps | contract note | listing-order |
| D-PS-3 | SB D-B-6 | — | A step's interval is its earliest-starting description's; other accounts are not shown | no (inspection only) | unresolved-decision | medium | BLOCKED (steps with several timed descriptions) | decision SD-CAU-10 (multiple-accounts) | multiple-accounts |
| D-PS-4 | DI-14 (open, registered) | — | Descriptions without an account in a variant are listed unflagged | n/a | superseded | low | n/a | none (superseded by DI-14) | variant-accounts |
| D-PS-5 | IBD §4 and Q1 (listings gain disputed entries); DI-1 option (a); facts_about ("holds or is disputed") | Established and disputed steps only | Pending memberships are not listed | n/a | documentation | low | ELIGIBLE (contract states that pending steps are not listed) | documentation fix | listing-dispute-sides |
| D-BE-1 | SB B0 ("certainly before, or None if they overlap") | True / None; False is before(b, a) | False when b is certainly before a | n/a | documentation | low | ELIGIBLE (False ≡ b certainly before a) | documentation fix | vocabulary-docs |
| D-BE-2 | SB B0; V02 §4.4 (half-open example intervals) | — (touching not ruled) | a.end.latest ≤ b.start.earliest → True (touching counts) | no (inspection only) | unresolved-decision | medium | BLOCKED at touching bounds | decision SD-CAU-5 (window-boundaries) | window-boundaries |
| D-BE-3 | SB B0 (`before` compares descriptions' intervals) | Inputs are descriptions | An occurrence id gives None | n/a | unsupported | low | G probe (occurrence inputs); P3 plans map steps to descriptions | contract note | occurrence-time |
| D-BE-4 | V02 §4.5 (clock alignment); V02 §12 (clock alignment reasoning deferred) | — | No clock handling | n/a | unsupported | low | G probe (cross-clock order) | contract note | clocks |
| D-IV-1 | SB D-B-6 | — | Lowest-id usable account; others are not reported | no (inspection only) | unresolved-decision | medium | BLOCKED (descriptions with several usable accounts) | decision SD-CAU-10 (multiple-accounts) | multiple-accounts |

**Counts (38 items).**
- semantic-defect 2;
- provenance-defect 3;
- unresolved-decision 20;
- api-convention 6;
- documentation 4;
- unsupported 2;
- superseded 1.

**High severity:**
- D-CO-1, D-CO-3 (semantic, eligible);
- D-EF-1, D-EX-1 (unresolved, blocked).

**Contract notes this adjudication implies:**
- c-causal said no question may require the initiating claims' attestations until ruled. With D-EX-4 classed as a
  provenance-defect, that sentence changes: questions may require them, and they are expected to fail until the DI is
  corrected.
- `explain`'s refusal row (unknown role, R2) is unchanged.

### Semantic decisions

**SD-CAU-1: what an "accepted state change" is in `effects_of`** (D-EF-1, D-EF-2).

Alternatives:
- **(a) Apply the Q-B1.2 categories to `effects_of`.** `accepted_change` is true only for a world-state change of the
  outcome (an accepted other or not-held state → accepted held, or the reverse for terminates). A move into or out of
  UNKNOWN or DISPUTED is reported as a judgement change, not an accepted one.
  - Grounds: SB Q-B1.2 ("never presented as physical change"); Q-B2 (one judgement for every reader); IBD §2.
- **(b) Keep the two-instant comparison** as a documented claim-check view (just before start, at end), including
  UNKNOWN → held.
  - Grounds: SB B0's description of `effects_of`.
  - Problem: it contradicts Q-B1.2 for the same state, and it misses delayed effects (SB probe case 6).
- **(c) Define the change through `changes`.** `accepted_change` is true when a world-state transition of the outcome
  is attributed to this claim under Q-B1.4 (any window after the event's start, attribution unique or ambiguous). The
  attribution is reported.
  - Grounds: SB Q-B1.4; Q-B1 case 6 (delayed effects); Q-B1.1 (no invented instants).

**Recommendation: (c).** One definition of change for every reader (the Q-B2 precedent). It handles delayed effects
without inventing instants. It keeps SB B0's separation: the claim is judged on its own, and the change is judged from
the outcome's attestations.

**SD-CAU-2: which initiating events `explain` lists, and with what timing** (D-EX-1, D-EX-2, D-EX-3).

Alternatives:
- **(a) Accepted `initiates` claims only.** Timing follows B-time applied to the holding: an event is excluded only if
  its accepted occurrence certainly starts after t. When the time is unavailable or uncertain, the event is kept with
  `timing: unresolved`.
  - Grounds: SB "Schema and API" ("accepted initiating events"); SB Q-B1.4 (accepted effect claims only); SB B-time.
- **(b) Every initiating claim, with its judgement, filtered by "ended by t".**
  - Grounds: the docstring only. "Ended by t" is in no decision.
- **(c) Accepted claims in `initiated_by` under the timing of (a); unaccepted ones in a separate `alternatives` list,
  never as explanations.**
  - Grounds: as (a), plus V02 §6.2 ("unaccepted attestations by others are returned as alternatives, never as
    support").

**Recommendation: (c).** It meets SB's "accepted initiating events" and V02 §6.2's alternatives rule. It uses the one
approved timing rule (B-time) instead of an undecided filter.

**SD-CAU-3: whether `explain` lists initiators when the content does not hold at t** (D-EX-5).

Alternatives:
- **(a) Only when `holds` is established.**
  - Grounds: E2D C4 presupposes the content holds.
- **(b) Always, beside the `holds` answer, with the contract stating that `initiated_by` implies nothing about
  `holds`.**
  - Grounds: SB B0 (an asserted effect and an accepted change are independent); V02 §5.3 ("never silent").
- **(c) Always, with an explicit marker on each initiator when the content does not hold.**

**Recommendation: (b).** SB B0 makes the claim and the state independent. Withholding accepted claims because the
state is not established would merge the two, and would hide evidence. The C4 questions read `holds` first.

**SD-CAU-4: whether `changes` explanations list their claims' attestations** (D-CH-2).

Alternatives:
- **(a) SB B0 governs.** Add each explanation claim's attestations as a new field; fields may only be added (IBD Q1).
- **(b) The Q-B1 schema governs.** `claimed_by` is enough, and attestations are read through `effects_of`.
- **(c) Cite the attestation ids only, without the attester, polarity and basis detail.**

**Recommendation: (a).** B0 is the architecture's general rule for "every answer". The Q-B1 schema lists fields
without excluding any. This also aligns with D-EX-4 (initiating-provenance).

**SD-CAU-5: touching windows** (D-CH-3, D-BE-2).

Alternatives:
- **(a) Closed windows.** Touching counts as overlap: B-time gives `unresolved`, and `before` gives None.
- **(b) Half-open intervals ("meets" is before).** An interval ending at e certainly precedes one starting at e. An
  event whose start is certainly no later than the transition's earliest time is `consistent`.
  - Grounds: V02 §4.4 (valid intervals such as [10:00, 10:10) and "from 10:10"); SB Q-B1.1 ("a change at exactly t1
    is already in effect at t1"); SB Q-B1.4 ("an effect cannot precede the start of its event"; a simultaneous
    effect does not precede it).
- **(c) Mixed:** `before` uses (b) and B-time uses (a).

**Recommendation: (b).** It follows the ontology's half-open interval convention and Q-B1.1's boundary rule, so both
readers use one convention. Under that convention, touching is not uncertainty.

**SD-CAU-6: A → UNKNOWN → A, and gaps through DISPUTED** (D-CH-4).

Alternatives:
- **(a) Report each judged-state change as a judgement transition.** Merge only Q-B1.1's case (accepted A, then
  UNKNOWN, then accepted B ≠ A).
  - Grounds: SB Q-B1.2 (into or out of UNKNOWN or DISPUTED is a judgement transition).
- **(b) Treat a DISPUTED gap like an UNKNOWN gap.** A, then DISPUTED, then B ≠ A is one world-state transition whose
  window is the disputed span.
- **(c) Suppress A → UNKNOWN → A,** since no change was accepted.

**Recommendation: (a).**
- Q-B1.2 classifies these moves explicitly, and Q-B1.1's merge is stated only for an UNKNOWN gap with B ≠ A.
- A dispute is a conflict, not missing knowledge: merging it would hide it (V02 §5.3).
- Suppressing A → UNKNOWN → A would hide judged-state changes the contract reports.

**SD-CAU-7: the valid time at which timeless claims are judged** (D-CH-5, D-EF-6).

Alternatives:
- **(a) Claims are judged independently of valid time.** The contract says so (SB D-B-2; V02 §4.4), and fixtures
  never give causal or effect claims a valid interval.
- **(b) Judge at the reader's t:** t for `effects_of` and `causes_of`, t2 for `changes`, as documented.
- **(c) Judge at each transition's own time** in `changes`.

**Recommendation: (a).** D-B-2 makes the contents timeless, so a valid time should not change their judgement. A
fixture convention keeps questions independent of the point, without a reader change.

**SD-CAU-8: `changes` with t1 ≥ t2** (D-CH-8).

Alternatives:
- **(a) Refuse** (a documented `ValueError`).
  - Grounds: R2's precedent that a malformed question must not look like an answer.
- **(b) Return no transitions.** (t1, t2] is empty, under Q-B1.1's intersection rule.
- **(c) Refuse t1 > t2, and answer t1 = t2 with no transitions.**

**Recommendation: (c).** An inverted interval is malformed (R2's reasoning). An equal pair is a well-defined empty
interval under Q-B1.1.

**SD-CAU-9: occurrence applicability for effect claims and `changes` explanations** (D-EF-5, D-CH-9).

Alternatives:
- **(a) Extend the LABS-1.011 fields** (each occurrence's status and `applies`) to `effects_of` entries and `changes`
  explanations, as additive fields.
  - Grounds: SB Occ-2 ("claims involving a denied occurrence do not apply"); SB U-2 ("a denied occurrence never gets
    an applicable explanation").
- **(b) Keep the check in `causes_of` only.** Callers compose with `occurrence_status`.
  - Grounds: the precedent of E2D X4.
- **(c) Report occurrence statuses without `applies`.**

**Recommendation: (a).** Occ-2 is an approved decision with general wording. An explanation of a transition by the
event of a denied occurrence is the case U-2 excludes. The fields are additive.

**SD-CAU-10: several usable accounts for one description, or several timed descriptions for one step** (D-IV-1, D-EF-3,
D-PS-3).

Alternatives:
- **(a) Report every usable account's interval and attestation.** Certainty judgements (`before`, B-time, the
  `effects_of` instants) hold only if they hold under every usable account.
  - Grounds: SB B0 (every claim lists its attestations); V02 §3.2 (windows: certainty, never a guess); SB D-B-6.
- **(b) Use one envelope** (the earliest start bound to the latest end bound), with all its accounts cited.
- **(c) Pick a single account deterministically** (nearest world, then attestation id), as documented.

**Recommendation: (a).** Choosing one account by id has no ground in the design, and it can turn an uncertain order
into a "certain" one. Option (a) keeps every account visible, and claims certainty only where every account gives it.

**SD-CAU-11: writer-side refusals** (D-CO-6, D-EF-7).

Alternatives:
- **(a) Establish them as approved writer validations.**
- **(b) Leave them as unestablished implementation checks.** Fixtures avoid them, and no probe counts them.
- **(c) Establish only the refusals grounded in design text:**
  - the two effect kinds (V02 §3.2);
  - proposition ids are required (SB B0, deferral D2; PLAN A0);
  - self-causation stays unestablished, because V02 states no irreflexivity for `causes`.

**Recommendation: (c).** Establish only what the design already implies, and leave self-causation to a separate
ontology decision.

