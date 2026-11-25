# Stage E2 reader contracts: review package

**LABS-1.062, 25 November 2026.** Branch `feature/e2-reader-contracts`, from `main` 5ded39a (the E2 harness merged).
**Draft for review (E2-D3).**

**Contracts:** [benchmark/e2/spec/reader-contracts.md](../../benchmark/e2/spec/reader-contracts.md). It covers all 22
reader templates, in four parts:
- core and organisation;
- spatial;
- measurement;
- causal and process.

**How they were written:**
- **Authoritative sources:** the approved ontology (world-ontology v0.2), the Core 0.3 and 0.4 design documents, and the
  recorded semantic decisions (increments A to D, identity, multiplicity, E1 reconciliation, DI-19, E2 decisions).
- **Supplementary only:** the generated reader documentation and the implementation. They are used to find
  discrepancies, never as the reason a semantic statement holds.
- **Labels:** every statement is labelled **[E]** established, **[P]** proposed or **[D]** discrepancy, and is cited.
- **Evidence records:** the specification evidence behind each part, with line-level citations, is in
  [e2-reader-contracts/](e2-reader-contracts/) (`evidence-core.md`, `-spatial.md`, `-measurement.md`, `-causal.md`).

**Not done:** no E2 question, fixture, calculation sheet or gold answer is written. No reader semantics, identity
behaviour or ontology is changed. DI-7 and DI-20 to DI-23 stay deferred.

## 1. What is established and what needs approval

| Kind | Count | Where | What the owner is asked |
|---|---:|---|---|
| **[E] established statements** | about 540 | each contract | nothing; they restate approved decisions with their sources. Questions may rest on them once the contracts are approved |
| **[P] shared proposals** | 5 (P-1 to P-5) | contracts §0 | approve, amend or reject each (section 3) |
| **[P] reader proposals** | 15 | "Local items" of each contract | approve, amend or reject each (section 3) |
| **[D] discrepancies** | 118 | "Local items" of each contract | rule on the ones in section 6.1; the rest are recorded. **No question may rest on a [D] point until it is ruled** |

A [D] item is never resolved by weakening a contract. Where the implementation doesn't meet a design requirement, the
item is recorded as a potential implementation gap (section 6.1), not as the intended behaviour.

## 2. Reader coverage matrix

**Column key:**
- **Ref.** documented refusals: established / documented elsewhere.
- **D / P:** the reader's local discrepancies and proposals.
- **Derivation:** what the reader presents (common §0.7).

| Reader | Family and CQs (design §3) | Gap probes it serves | Derivation | Ref. | D / P | Ready for questions? |
|---|---|---|---|---|---:|---|
| `transform_between` | S1–S6 | S7, S8, F9 | `frame-transform/v1` over the chain | 0 / 0 | 9 / 0 | yes, except D-TB-1 (tolerance) and D-TB-3 (off-chain dispute) |
| `where` | F1–F6; X1 | F7, F8, F10, GAP-SPATIAL-2/6/7/8 | `frame-transform/v1` per derived candidate | 0 / 0 | 7 / 1 | yes, except D-WH-1 and D-WH-3 (disputed position premise) |
| `poses` | F (listing) | GAP-SPATIAL-8, GAP-FRAME-6 | none | 0 / 0 | 4 / 0 | listing only; D-PO-2 (dispute sides not shown) |
| `frame_info` | F9 (one hop) | GAP-FRAME-1, -4, -5 | none | 0 / 0 | 3 / 0 | probes and fixture checks only; D-FI-1 |
| `measurements` | M1, M4; X1 | GAP-MEAS-6, -7, -11 | none (rests-on is provenance) | 0 / 0 | 10 / 1 | yes, except D-ME-5 (aliases) and D-ME-6 (point intervals; needs a probe) |
| `compare_measurements` | M2, M3 | M7, M8, GAP-MEAS-2, -3 | none | 0 / 0 | 8 / 1 | yes, except accepted-denial questions (D-CM-6) |
| `convert` | M5 | M9 | none | 1 / 0 (+1 precondition) | 5 / 1 | yes |
| `calibration_status` | M6 (A); X2 via MC | GAP-MEAS-9, -10 | none | 0 / 0 | 4 / 1 | yes; evidence for disputed / not-yet-effective needs P-CS-1 / D-CS-3 |
| `measurement_calibration` | M6; X2 | GAP-MEAS-9, GAP-MULTI-2 | none | 0 / 0 | 7 / 1 | yes, except D-MC-3 (which instant) and D-MC-5 |
| `causes_of` | C1, C2; X4 | GAP-CAUSE-1, -2, -4, -5, -7 | none (nothing inferred) | 0 / 0 | 6 / 1 | yes, except lifted-claim citations (D-CO-1, -2, -3) |
| `effects_of` | C3 | GAP-CAUSE-3 | none | 0 / 0 | 7 / 1 | yes, except into/out-of-UNKNOWN changes (D-EF-1) and delayed effects (D-EF-2) |
| `explain` | C4; X4 | GAP-CAUSE-1, GAP-MULTI-4, -6 | none | 1 / 0 | 6 / 0 | partly: initiating-claim provenance missing (D-EX-4); D-EX-1 to -3 |
| `changes` | C5; F (frames) | GAP-CAUSE-4 | none | 0 / 0 | 9 / 0 | yes, with both-sides evidence; except D-CH-1 (accepted "does not hold" side) |
| `process_steps` | P1, P2, P4, P5; X5, X6 | GAP-PROC-1 to -7 | none | 0 / 0 | 5 / 1 | yes; undated steps (D-PS-2) not relied on |
| `before` | P3 | GAP-PROC-1, -4 | none | 0 / 0 | 4 / 1 | yes, except touching intervals (D-BE-2) and descriptions vs occurrences (D-BE-3) |
| `interval` | P3; X time steps | GAP-PROC-4, GAP-MULTI-2 | none | 0 / 0 | 1 / 1 | yes, with one account per description (D-IV-1) |
| `holds` | X steps (E1 template) | GAP-SPATIAL-8, GAP-MULTI-6 | none | 1 / 0 | 5 / 1 | yes, with fully specified roles (D-HO-1, -2) |
| `value_at` | X3; X steps | GAP-MEAS-6, GAP-MULTI-2 | none | 2 / 1 | 6 / 1 | yes, without explicit-role questions on unslotted types (D-VA-2, -3) |
| `facts_about` | X2 | GAP-MULTI-6, -8 | none | 0 / 0 | 3 / 0 | yes, except constraint disputes (D-FA-1) |
| `occurrence` | X3, X6 (event roles) | GAP-MULTI-2, -8 | none | 0 / 0 | 3 / 1 | yes (E1 event-role contract, R1) |
| `occurrence_status` | X4; C2 | GAP-MULTI-2, -8 | none | 0 / 0 | 3 / 0 | yes, with occurrence ids only (D-OS-1); "denied" at t means D-OS-2 |
| `office_holders` | X6 | GAP-MULTI-2, -6 | none | 0 / 0 (+1 precondition) | 3 / 1 | yes (E1 contract) |

Every competency question of class A or H in design §3 has at least one reader contract. The class G forms have a
probe reader, or no reader at all (then they are not-callable probes).

## 3. Proposals for approval

### 3.1 Shared (contracts §0)

| Id | Proposal | Why | Effect |
|---|---|---|---|
| **P-1** | Three evidence roles: **supporting** (what the answer rests on for its value or status), **conflicting** (the other side of a dispute: rivals, the constraint that makes them rivals, accepted denials), **alternative** (listed, not rested on). Supporting precision covers the supporting role only; gold lists required and admissible evidence per role. | E2-D6 scores precision "for supporting evidence"; E1 mixed the roles; item 13 of LABS-1.062 | harness H-4; gold format |
| **P-2** | Deterministic fixture-level names for library-generated attestations (`<step>/activity`, `<step>/effect:<n>`, `<step>/ended:<step>`, …). An unnamed cited id is **unattributed**: neither admissible nor inadmissible, and the precision verdict waits for adjudication. | item 14: never inadmissible merely because the library generated it | harness H-1 |
| **P-3** | Empty sets: nothing required and nothing cited is vacuous. Required but nothing cited gives recall 0, precision **undefined** (never 1.0), and `missing-evidence`, counted as "no evidence returned". Something cited with an admissible set of [] gives precision 0. Every scored question whose reader cites evidence must state its admissible set. | item 16 | harness H-3, H-8 |
| **P-4** | Derivation premises are admissible by **question**, not by existence: a premise must name a step in the question's `admissible_premises`. That list is authored with the gold, by the rule's input content types and by visibility for the question's world, perspective, `as_of` and `t`. A disputed premise is admissible only where the contract says so, and the answer must then be DISPUTED. | item 15 | harness H-2; gold format |
| **P-5** | A precondition failure (profile not installed, id that names nothing, not a unit) is an execution error, not a semantic refusal. | item 2 of LABS-1.062: only documented refusal behaviour | harness refusal table (H-6) |

### 3.2 Reader proposals

| Id | Proposal (short) |
|---|---|
| P-HO-1 | In a polarity dispute, `holds.support` splits by `evidence[].polarity`: assertions supporting, accepted denials conflicting. |
| P-VA-1 | `value_at.support`: polarity-true supporting (every rival value is listed in `values`), polarity-false conflicting. |
| P-OC-1 | Where a kind-scoped event-role constraint applies, the classification's support is supporting (ER-2). |
| P-OH-1 | In an office conflict, every established holder's claims are supporting; the constraint's support is conflicting. |
| P-WH-1 | In a DISPUTED `where`, candidates outside every conflict pair keep supporting evidence. |
| P-ME-1 | `measurements`: supporting = usable measurement attestations; statements, unaccepted and superseded values are alternatives. |
| P-CM-1 | `compare_measurements`: in a DISPUTED answer, incompatible-pair attestations are conflicting; the other compared ones supporting. |
| P-CV-1 | `convert`: not-a-unit is a precondition failure (P-5), not a refusal. |
| P-CS-1 | `calibration_status`: in a disputed answer, the disputing holdings' accepted claims are conflicting evidence. |
| P-MC-1 | `measurement_calibration`: supporting = the usable measurement attestation plus the calibration's `support`. |
| P-CO-1 | `causes_of`: only accepted claims with `applies: true` support "what caused E"; `applies: false` claims are alternatives. |
| P-EF-1 | `effects_of`: other events' claims about the same outcome are neither rivals nor reported. |
| P-PS-1 | `process_steps`: list order asserts no succession (succession is `before`'s question). |
| P-BE-1 | `before` cites nothing; a P3 question's evidence comes from the `interval` steps of its plan. |
| P-IV-1 | `interval`: the account attestation used is the supporting evidence. |

## 4. Evidence extraction rules (the resolved questions)

These are the rules the harness extractors will be rebuilt on (H-5). The full tables are in each contract's part 6.

| Question (LABS-1.062) | Resolution | Status |
|---|---|---|
| **10. `where()`: candidates vs alternatives and incomparable** | **Supporting:** each candidate's `position_support` and its chain's `support`. **Conflicting** (DISPUTED): both candidates of every verified `conflicts` pair, and `search.inconsistent` for a candidate whose chains disagree. **Alternative**, never supporting: `alternatives`, `incomparable[*].support`, and unverified candidates and pairs. | [E] A2 "Provenance", "Disjoint", "Different frames", LABS-1.009; roles P-1, P-WH-1 |
| **11. `changes()`: both sides** | A transition the answer establishes (category `world-state`, between two accepted states, Q-B1.2) requires **both** `before.support` and `after.support` as supporting evidence. A `judgement` transition (into or out of UNKNOWN or DISPUTED) rests on the side that has an accepted state, and its `conflicts` are conflicting. D-CH-1: an accepted "does not hold" side currently has empty `support`. That is recorded as a potential gap; the contract is not weakened. | [E] Q-B1.2 and per-side `support` in the SB contract schema; [D] D-CH-1 |
| **12. `explain()`: initiating-claim provenance** | The existing contract requires it: stage-b B0, "every claim lists its attestations". `initiated_by` gives the claim label, status and claimed-by, but no attestation ids: **D-EX-4, a potential gap**. Citable today: `holds.support` (with `conflicts` and `constraint_support` when DISPUTED) and the attestations of each initiating event's causal claims. Until the owner rules, no question may require the initiating claims' or the accounts' attestations. | [E] B0; [D] D-EX-4 (and D-CH-2 for `changes` explanations, where the Q-B1 schema itself omits the ids: the two design texts conflict) |
| **13. support vs conflicts, all readers** | `holds`: `support` supporting; `conflicts` and `constraint_support[].support` conflicting; `alternatives` alternative; a polarity dispute splits `support` by polarity (P-HO-1). "Not holding by exclusivity" (R3) cites the other value's attestations as supporting, so gold must list them as admissible. `value_at`: `support` carries every side (no `conflicts` field, D-VA-1); split by polarity (P-VA-1); `constraint_support` always empty. The same split applies to `office_holders`, `calibration_status`, `compare_measurements` and `where` (P-OH-1, P-CS-1, P-CM-1, P-WH-1). | [E] A0 F-4, B-D §2.3, DI-19, R3; roles P-1 |
| **14. names for generated attestations** | P-2 (section 3.1). | proposal |
| **15. premise admissibility** | P-4 (section 3.1). For `frame-transform/v1`, admissible premises are visible, usable `positioned-in` and `frame-transform` steps; a disputed transform never yields a position. A disputed **position** premise currently yields INFERRED (D-WH-3): no question may rest on it until ruled. | [E] A2; [P] P-4; [D] D-WH-3 |
| **16. empty evidence sets** | P-3 (section 3.1). | proposal |

## 5. Refusal rules and derivation validation

### 5.1 Documented refusals (the complete table)

| Reader | Refusal | Condition | Established? | Source |
|---|---|---|---|---|
| `holds`, `explain` | `unknown-role` | a role name the type does not relate | **yes** | R2 (LABS-1.053) |
| `value_at` | `unknown-role` | `key_role` / `value_role` not a role of the type | **yes** | R2 |
| `value_at` | `no-single-slot` | no `key_role`, and the type has not exactly one one-role constraint | **yes** | core-0.4 README, A0 constraints |
| `value_of` (no template) | `no-matching-slot` | key not exactly one constraint's key roles | by approved test only | DI-19 report and its test (not a design text) |
| `value_of` (no template) | `params-slot` | the slot's value is parameters | no (implementation only) | `model.py` |
| `convert` | `cross-dimension` | units of different dimensions | **yes** | stage-c (convert) |

**Not refusals:**
- **Preconditions (P-5):** not-a-unit, profile not installed, an unknown id.
- **Writer-side refusals:** self-causation, the `claim_effect` kinds, `relate_frames` of a frame to itself. These are
  fixture errors, not reader answers.

**Harness state:**
- The templates carry `unknown-role` (holds, explain, value_at), `no-single-slot` (value_at; established, corrected in
  LABS-1.062), `cross-dimension` and `not-a-unit` (convert; not established).
- Under P-5 / P-CV-1, `not-a-unit` would leave the table and be an execution error (H-6).

### 5.2 Derivation validation requirements
1. The only recorded rule is `frame-transform/v1` [E].
2. Every presented `{rule, premises}` object is checked, wherever it is nested [E, harness LABS-1.062].
3. A derivation is valid only if:
   - its rule is recorded;
   - it has at least one premise;
   - every premise is admissible for the question (P-4).
4. Only `where` (derived candidates) and `transform_between` (a non-trivial chain) present derivations. Every other
   reader presents none, so any derivation there is fabricated by definition [E, DI-7].
5. A gap probe fails on any fabricated derivation, whatever its status [E, harness LABS-1.062].
6. Open points:
   - D-TB-2: `source == target` gives INFERRED with no premises, which under rule 3 is no valid derivation. The
     harness doesn't count it today, because the template presents no derivation for an empty chain.
   - D-WH-3: a disputed position premise yields INFERRED.

## 6. Ambiguities and implementation discrepancies

All 118 are listed, with both sides cited, in the contracts' "Local items". They fall into three groups.

### 6.1 Potential implementation gaps against an approved design (register candidates; owner's ruling needed)
No question may rest on these until they are ruled. Each would be registered as a deferred issue only on the owner's
decision; none is corrected here.

| Area | Items |
|---|---|
| Disputed or off-chain premises in frame reasoning | D-WH-3 (disputed position statement → INFERRED); D-TB-3 (disputed edge off the reported chain is not cited); D-TB-1 / D-WH-1 (chain agreement ignores `angle_tolerance`; D-A2-7 never confirmed) |
| Dispute sides not reported by listings | D-PO-2, D-FI-1 (`poses`, `frame_info` omit assertions and denials, increment B §4); D-FA-1 (`facts_about` omits the constraint's attestations: the DI-19 gap in another reader) |
| Identity not applied | D-WH-5, D-PO-3, D-ME-5 (raw-id filters where ID-8 / v0.2 §4.2 require the identity class) |
| Accepted denials of measurements | D-CM-6 (an accepted denial never makes a comparison DISPUTED, and disappears with `t`) |
| Causal provenance and lifting | D-EX-4 / D-CH-2 (initiating-claim attestations missing); D-EX-1 (non-accepted initiators included); D-EX-3 (initiators without an accepted account dropped); D-CO-1, -2, -3 (lifting checks one side, doesn't cite describes links, treats disputed links as accepted) |
| Change semantics | D-CH-1 (accepted "does not hold" side has no support); D-EF-1 (a move into or out of UNKNOWN counted as an accepted change, against Q-B1.2); D-EF-2 (delayed effects) |
| Value readers | D-VA-3 (`value_at` with explicit roles on `office-holding` ignores the exclusive office); D-VA-2 (`key_role` without `value_role` answers UNKNOWN) |
| Occurrence status | D-OS-1 (non-occurrence input accepted); D-OS-2 ("denied" includes existence that ended or has not started) |
| Measurement time | D-ME-6 (point measurements may never hold at t; from code reading, needs a probe); D-MC-3 (which instant is "the activity's start"); D-MC-5 (misleading reference check when the time is unknown) |
| Ordering | D-PS-2 (undated steps not last); D-IV-1 (lowest-id account chosen) |

### 6.2 Design silent: a ruling on vocabulary or output is needed
These are fields and values in the implementation that no design states, or cases no design covers:
- **Spatial:** `where.judgement` values (D-WH-2); `source == target` (D-TB-2).
- **Comparison and calibration:** comparison reason strings (D-CM-1); `in_force` (D-CS-1).
- **Causal and change:** `cause_occurrences` and the label `mixed` (D-CO-5); `t1 ≥ t2` (D-CH-8); touching intervals
  (D-BE-2).
- **Holds:** PENDING not observable through `holds` (D-HO-3); partial role matching (D-HO-1, -2).
- **The rest:** see the contracts.

Until ruled, questions do not expect those fields or cases (common §0.1).

### 6.3 Documentation errors (no semantic question)

| Item | Correction |
|---|---|
| D-PO-1 | the `poses` docstring still says conflicts between positions are not judged (A1). That stopped being true after A2 |
| D-CH-7 | stage-b.md lines 201 and 470–472 describe `changes` as it was before the Q-B1 rulings |
| D-TB-4 | GAP-SPATIAL-5 is listed as a gap, but the identity design makes frames unable to be same-as (DI-12 closed); a stale code comment too |
| D-VA-5 | the DI-19 report says `value_at` projects through `_answer`; it uses `_judge` + `_conflicts`. **Corrected in this commit.** |
| D-VA-6 | the harness review called `no-single-slot` not established. **Corrected in LABS-1.062** (harness and review) |
| stale status | the DI-19 report and the E2 decisions record said "at review" after DI-19 was merged. **Corrected in this commit** |

Docstring corrections (D-PO-1) and the stage-b and inventory text (D-CH-7, D-TB-4) are left for the owner. A
docstring change touches `src/`, which this step does not change.

## 7. Further harness changes required (after contract approval)

| Id | Change | From |
|---|---|---|
| H-1 | the loader assigns the fixture-level names of P-2; scoring reports unattributed ids apart, and the precision verdict is `unverified` while any remain | P-2 |
| H-2 | derivation premises are checked against the question's `admissible_premises` (step names), not against existence | P-4 |
| H-3 | the checker requires `admissible_evidence` (and `admissible_conflict_evidence` where conflicting evidence is cited) on every scored question whose reader cites evidence | P-3 |
| H-4 | extractors return evidence by role (supporting / conflicting / alternative); the gold format gains `required_conflict_evidence` and `admissible_conflict_evidence`; supporting precision covers the supporting role only; citing an alternative as supporting is inadmissible | P-1 |
| H-5 | rebuild each template's extractor from its contract's part 6 table. This covers the `where` conflict pairs, the `holds` / `value_at` polarity split, `changes` both sides, `explain` causes only, `measurements` without statements, `causes_of` `applies: true` only, `calibration_status` P-CS-1 and `interval` P-IV-1. One test per row. | contracts part 6 |
| H-6 | the refusal table as in section 5.1: `not-a-unit` becomes a precondition (execution error) under P-5 | P-5, P-CV-1 |
| H-7 | the report gives "no evidence returned" counts and undefined precision per family | P-3 |
| H-8 | the checker refuses a question whose expected fields name a [D] field or value until it is ruled (a list kept with the contracts) | common §0.1 |

None of these changes a reader. Each is a harness change, re-validated as the LABS-1.061 and LABS-1.062 increments
were.

## 8. After approval
1. The owner rules on sections 3 and 6.1. Each ruling is recorded in the contracts ([P] → [E], or the item is
   removed), and any accepted implementation gap is registered as a DI.
2. Harness changes H-1 to H-8, with tests.
3. E2 authoring (design 5.3): fixtures, questions, calculation sheets and gold, from the approved contracts only.
