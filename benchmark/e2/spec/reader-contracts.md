# Stage E2 reader contracts (draft for approval, E2-D3)

**LABS-1.062, 25 November 2026.** **Draft:** no E2 question may rest on these contracts until the owner approves them.
Review package: [docs/stage-e/stage-e2-reader-contracts-review.md](../../../docs/stage-e/stage-e2-reader-contracts-review.md).

**What this covers:** the 22 reader templates the E2 harness can call (`evaluation/e2/readers.py`).

**How it was written:**
- From the approved ontology (`docs/architecture/world-ontology-v0.2.md`), the Core 0.3 and 0.4 design documents, and
  the recorded semantic decisions.
- The generated reader documentation (`reader-docs.md` here) and the implementation are supplementary only.
- Every statement is labelled [E] established, [P] proposed or [D] discrepancy (§0.1), and cited.
- The full citations and line numbers for each part are in its evidence record under `docs/stage-e/e2-reader-contracts/`.

**Parts:**
- §0: shared rules (evidence roles, fixture names, precision with empty sets, derivation premises, refusals, ordering).
- A: `holds`, `value_at`, `facts_about`, `occurrence`, `occurrence_status`, `office_holders`.
- B: `transform_between`, `where`, `poses`, `frame_info`.
- C: `measurements`, `compare_measurements`, `convert`, `calibration_status`, `measurement_calibration`.
- D: `causes_of`, `effects_of`, `explain`, `changes`, `process_steps`, `before`, `interval`.


## 0. Rules shared by every contract

### 0.1 Status of each statement
Every statement in a contract carries one label:
- **[E] Established:** an approved design text or semantic decision. The citation names it.
- **[P] Proposed:** a new rule this draft proposes. It needs the owner's approval before questions rest on it. Proposals
  are numbered (P-n) and collected in the review package.
- **[D] Discrepancy:** the implementation or its docstring differs from the design, goes beyond it, or the design is
  silent. Discrepancies are numbered (D-n) and collected in the review package.

Where a docstring and its design text differ, the contract records the difference and **does not pick one** (design 5.2).
No question may depend on such a point until the owner rules on it.

Sources are cited by path and section. Generated reader documentation (`benchmark/e2/spec/reader-docs.md`) and the
implementation are cited only as supplementary, never as the reason a semantic statement holds.

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

### 0.4 Evidence roles [P-1, with [E] parts]
A cited attestation has exactly one role in an answer:

| Role | Meaning | Scored by |
|---|---|---|
| **supporting** | the answer rests on it: it is evidence for the value, status or judgement given | recall (required), precision (admissible); E2-D6 "precision 100 % for supporting evidence" |
| **conflicting** | the answer reports it as the other side of a dispute that made the answer DISPUTED (rivals; the constraint that makes them rivals; accepted denials) | recall of required conflicting evidence; never counted in supporting precision; forbidden still applies |
| **alternative** | listed but not rested on: unaccepted, superseded, incomparable, a statement beside measurements, a candidate outside the comparison | never cited; citing it as supporting is an inadmissible citation |
| not reported | anything else | — |

- [E] For a DISPUTED `holds` answer, the dispute rests on its own claims, the rivals and the constraint (A0 F-4,
  increment B design §2.3, DI-19). E1 counted all three as cited.
- [P-1] The proposal is to keep them **apart**: `support` is supporting; `conflicts` and `constraint_support` are
  conflicting. Supporting precision then measures only what the answer rests on for its value. The gold lists
  `required_evidence` / `admissible_evidence` (supporting) and `required_conflict_evidence` /
  `admissible_conflict_evidence` (conflicting); `forbidden_evidence` applies to both. This changes the harness (H-4); it
  changes no reader.

### 0.5 Fixture-level names for evidence [P-2]
Evidence is named by fixture step, never by attestation id. An attestation the library writes on a fixture step's
behalf gets a **deterministic name derived from that step**, so it is never inadmissible merely because the library
generated it:

| Written by | Name |
|---|---|
| the step's own claim (attest, position, relate_frames, claim_cause, …) | `<step>` |
| `measure` | `<step>` (reported content), `<step>/activity` (the activity's account), `<step>/activity-kind` (its `measurement` classification), `<step>/produced`, `<step>/reports` |
| `account`, `record_event`, `act_in_office`, `replace_part`, `take_sample` | `<step>` (the occurrence interval), `<step>/kind:<category>` (each classification), `<step>/describes` (the describes link, if `occurrence` is given), `<step>/effect:<n>` (the n-th effect, from 0, in the order the fixture lists them or the profile documents them) |
| `move` | `<step>` (the account), `<step>/effect:<n>`, `<step>/ended:<restated step>` (each claim it ends) |
| `end`, `correct` | `<step>` |
| `destroy` | `<step>/ended:<restated step>` (each system claim ended), `<step>/denied:<restated step>` (each other attester's claim denied) |
| a restatement of step X by the library (same attester, content and start: end(), move()) | counts as X (E1 C3 [E], approved LABS-1.053) |

- Names are assigned by the loader from the writer's return values and the fixture's own order. They never depend on
  a run, on a reader, or on random ids.
- A cited attestation that still has no name is **unattributed**. It is reported in its own count, it is neither
  admissible nor inadmissible, and it blocks a pass of the precision criterion until it is adjudicated (H-1).

### 0.6 Precision and recall with empty sets [P-3]

| Case | Recall | Precision | Outcome |
|---|---|---|---|
| nothing required, nothing cited | n/a | n/a (vacuous) | no evidence failure; not counted in family totals |
| evidence required, nothing cited | 0 | **undefined**, never 1.0 | `missing-evidence`; counted in the family recall denominator; listed as "no evidence returned" |
| nothing admissible stated (`admissible_evidence: []`), something cited | n/a | 0 | `inadmissible-evidence` |
| `admissible_evidence` absent on a scored question whose reader cites evidence | — | — | refused by the checker (H-3): every such question must state its admissible set |
| cited only unattributed ids | as computed | undefined | the precision criterion is `unverified` until adjudicated |

Family precision is the sum, over questions, of admissible cited / cited. It is computed only over questions that cite
something, and the number of "no evidence returned" questions is reported beside it.

### 0.7 Derivations and premise admissibility [P-4, with [E] parts]
- [E] The model records one derivation rule, `frame-transform/v1` (stage-a2). It derives a pose or a transform from a
  frame chain and position statements. No general derivation record exists (DI-7, deferred), and basis `inference` is
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

### 0.8 Refusals [E, P-5]
- A refusal is a documented, deliberate "no answer" (an exception naming why), distinct from an execution error.
- [E] Only refusals in this contract's refusal tables are refusals (LABS-1.062). A refusal is **established** only when
  an approved design text states it. Gap probes accept only established refusals.
- [P-5] A precondition failure (a profile not installed, an id that names nothing) is an execution precondition, not a
  semantic refusal. It is reported as an execution error.

### 0.9 Ordering and multiplicity
Unless a contract states an order [E], a list in an answer is compared as a **multiset**. A question that needs one
item picks it by field (`[field=value]`), never by position. An order the implementation happens to produce but no
design states is recorded as [D] and is not relied on.


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
| `constraint_support[].support` | an applied attested constraint (in practice only in a constraint dispute) | conflicting: it is what makes the rivals conflict | [E] content (DI19 §1; REG DI-19); role P-1 |
| `alternatives` | any case | alternative: never cited | [E] v0.2 §6.2 |
| `evidence` | any case | detail of `support` and `conflicts`, never a separate role | [E] A0 F-4 |

**`value_at()` and `value_of()`, by field:**
- **`support` holds every side of a dispute.** It contains the deciding attestations of every content in the slot
  that holds or is polarity-disputed: all listed values and, for a polarity-disputed value, its accepted denials.
  There is no `conflicts` field. The field's contents are [D] (D-VA-1): in the implementation only; the design says
  only that `value_at` "reports DISPUTED" (A0 F-4; SB Q-B2).
- **Proposed roles** (P-VA-1, applying P-1):
  - an attestation in `support` with polarity true is **supporting**, because every value it supports is in
    `values`. This holds for a functional dispute too: all rival values are listed, so no rival is "the other side"
    of a single answered value;
  - an attestation in `support` with polarity false (it arises only where a value is polarity-disputed) is
    **conflicting**.
- `alternatives`: alternative [E] (v0.2 §6.2).
- `constraint_support`: always empty [E] (DI19 §1).

**E1 compatibility.** E1's harness counted all of `support` as cited for `value_at`. Under P-VA-1 the same ids are
cited, now split into two roles.

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
   - [D] Partially specified roles are accepted: subset matching (D-HO-1).
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
   - [D] PENDING and UNKNOWN records both answer `Status.UNKNOWN` (D-HO-3).
4. **Visibility**
   - [E] common 0.2; v0.2 §6.2, §6.3.
   - [E] Supersession is per perspective (SUP §2).
   - [E] Nearest-world precedence applies (B-D §2.1).
   - [E] Identity follows ID-2 to ID-8. The links relied on are not added to the evidence (ID-D §3.10).
   - [E] A constraint is cited only where the perspective accepts it, within its valid and knowledge time; a
     superseded constraint cites its successor; inherited constraints are cited in variants (DI19 §2).
5. **Ordering and multiplicity**
   - [E] `constraint_support` is sorted by constraint and key (DI19 §1).
   - [D] `support`, `conflicts` and `alternatives` are sorted ids, but only in the implementation. Compare them as
     multisets (common 0.9).
   - [D] When several contents match, the first decided one is returned (D-HO-2).
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
   - [E] None are presented. INFERRED comes from basis `inference` (DI-7, not a recorded derivation) or from
     query-time exclusivity (REG DI-7; C03 D8). No `{rule, premises}` may appear (E2DEC §4).
8. **Refusals**

   | Name | Condition | Exception / message | Established? | Source |
   |---|---|---|---|---|
   | unknown-role | a role name the type does not relate (core names, inherited included) | `UnknownRoleError` (ValueError), naming the type, the unknown names, the valid names and a hint for stored profile names | yes | R R2; HR §9 |

9. **Limitations and gaps**
   - [E] DI-7.
   - [E] DI-17 (ID-5 groups; about 12 E2 identity questions, E2DEC §2).
   - [E] TI-1 to TI-3 (ID §10).
   - [E] D-A2-5 / GAP-SPATIAL-8.
   - [E] No OBSERVED, PRESUMED or persistence (C03 D1).
   - [E] Performance: DI-9 (exclusivity cost) and DI-20 to DI-23 (REG).

**Local items**
- D-HO-1: partial role matching. The `judgement()` docstring says "with the given players among its own" (code: subset
  match); B-D §3 says the record is "of one content". The design is silent on partial questions.
- D-HO-2: with partial roles or parameterised types, several contents match and the code returns the first decided one
  in load order. C-D §7 and D-D §9 require order independence for their readers; `holds` has no such test.
- D-HO-3: PENDING (B-D §2.4) is not observable through `holds()`: the code maps it to UNKNOWN. Questions that need
  `pending` must read `judgement()`.
- D-HO-4: reason `not_supporting` (UNKNOWN) appears only in `judgement.py`. B-D §2.4 and the reasons recorded in B do
  not include it.
- D-HO-5: "support" means non-empty for a DISPUTED `holds` (A0 F-4) but empty for rule-Q readers and event roles
  (C §"Points decided" 2; ER-4). The word must be defined per reader.
- P-HO-1: in a polarity dispute, split `support` by polarity: assertions supporting, accepted denials conflicting
  (applies common P-1).

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
   - [D] `key_role` without `value_role` (D-VA-2). Explicit roles that form no constraint (D-VA-3).
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `status` | Status | STIPULATED, ASSERTED, INFERRED (the core rule over the values held), DISPUTED, UNKNOWN (records visible, no value), NOT_YET_KNOWN | [E] C-D §3.3, §4; C03 |
   | `values` | ids | canonical ids under the perspective's identity; empty when none | [E] B-D §2.3; A0 F-5; T |
   | `support` | ids | deciding attestations of every value held or disputed | [D] contents (D-VA-1) |
   | `alternatives` | ids | unreviewed, not superseded keyed attestations with a verdict at t | [E] v0.2 §6.2; C03 example |
   | `constraint_support` | list | always empty | [E] DI19 §1 |
   | `evidence` | list of dicts | as for `holds` | [E] C03 |

   - [D] Which name of an identity class is canonical (the least name) is in code only. Questions must not depend on
     it unless the class has one member.
3. **Judgement and uncertainty**
   - [E] One functional-conflict judgement is shared with `holds`, `facts_about` and `changes` (SB Q-B2). DISPUTED
     arises when two holding contents give different value players to one constraint key, or a value is
     polarity-disputed (A0 shelf root cause; D2D §3 "Judgement: polarity").
   - [E] Parameter values conflict only when they cannot both be true (A2 D-A2-1).
   - [E] Only declared slots apply; attested constraints never do (DI19 §1).
   - [E] Status rests on the values held, not on accepted denials of other values (C-D §3.3, C-6).
   - [E] Unreviewed rivals never create a dispute (A0 F-4 "Unchanged").
   - [D] Only accepted denials, no value held: UNKNOWN. This is consistent with v0.2 §5.5 by analogy only (D-VA-4).
4. **Visibility**
   - [E] common 0.2.
   - [E] A nearer world's value overrides inherited values for the same key (A0; B-D §2.1).
   - [E] Value identity agrees on both load paths (A0 F-5).
   - [E] Selection is by identity class (ID-D §3.8).
5. **Ordering and multiplicity**
   - [E] Several values are possible: compatible values under explicit roles, or every value in a dispute (A0 shelf
     table).
   - [D] `values` sorted and ids sorted: implementation only. Compare as multisets.
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `support[i]` where `evidence[attestation=i].polarity` is true | always (in a dispute, every listed value's claims) | P-VA-1; contents [D] D-VA-1 |
   | conflicting | `support[i]` where `evidence[attestation=i].polarity` is false | a polarity-disputed value | P-VA-1 (P-1) |
   | alternative | `alternatives` | always | [E] v0.2 §6.2 |
   | not cited | `constraint_support` (always empty), `evidence` | always | [E] DI19 §1 |

7. **Derivations and admissible premises**
   - [E] None are presented. INFERRED comes only from basis `inference` (REG DI-7).
8. **Refusals**

   | Name | Condition | Exception / message | Established? | Source |
   |---|---|---|---|---|
   | unknown-role | `key_role`, `value_role` or a `value_of` key role the type does not relate | `UnknownRoleError` | yes | R R2; HR §9 |
   | no-single-slot | `value_at` without `key_role` on a type without exactly one one-role functional constraint (for example `office-holding`, `has-quality`) | `ValueError` ("… one-role functional constraints …: name key_role and value_role") | **yes** | A0 "What uses them" (L58-60); DI19 §1 and test `test_value_readers_never_apply_attested_constraints` |
   | no-matching-slot | `value_of` whose key does not name exactly the key roles of one constraint | `ValueError` | yes (by approved test) | DI19 §2 test; message in code |
   | params-slot | `value_of` on a constraint whose value is the content's parameters | `ValueError` ("ask with where/poses") | no: code only, consistent with A2 D-A2-5 | code `model.py` `value_of` |

9. **Limitations and gaps**
   - [E] GAP-MEAS-6.
   - [E] DI-3 (no joint-kind slot).
   - [E] DI-7.
   - [E] DI-17.
   - [E] A2 range propagation can miss a conflict, never invent one (A2 limitations).
   - [E] No attested constraints in value readers (DI19).

**Local items**
- D-VA-1: `support` contains every side of a dispute and accepted denials, and there is no `conflicts` field (code
  `_value`). The design (A0 F-4, SB Q-B2) says only "reports DISPUTED".
- D-VA-2: `key_role` given without `value_role` returns UNKNOWN with empty values even when the content holds (code
  `value_at`/`_value`). The design (A0) is silent.
- D-VA-3: explicit roles that form no declared constraint are accepted. For example, `office-holding` with
  `key_role="class", value_role="classified"` lists every holder in every context, ASSERTED, never DISPUTED under an
  established exclusive office. This contradicts what `holds`/`office_holders` say for the same facts (B "Answer
  changes"). DI19 §1 says the value readers "refuse a type with no declared slot".
- D-VA-4: accepted denials only give UNKNOWN (code). No design text states it.
- D-VA-5: B-D §3 and DI19 §1 say `value_at` projects the canonical record through `_answer`; the code uses `_judge` +
  `_conflicts`. The answers agree (B: `value_at` unchanged); the documented code path does not.
- D-VA-6: HR §9 lists the no-single-slot refusal as "not established, documented only in the implementation". It is
  established by A0 and DI19 §1 (recorded so here); the harness's refusal table should be corrected.
- P-VA-1: `support` with polarity true is supporting and with polarity false is conflicting (P-1). No functional-rival
  split is needed, because all rival values are listed in `values`.

---

### `facts_about(world, subject, t, as_of=None, perspective="system")`

**Serves:** X2, second step (`measurement_calibration` → `facts_about`: who issued the certificate, E2D §3.6); X plans
(HR §1). Gap probes: GAP-MULTI-6, GAP-MULTI-8 (DI-17 groups in variant worlds).

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
   - [E] A polarity dispute is listed in place, citing both sides (DI-1, REG).
   - [E] Declared and attested constraints are applied (SB Q-B2; DI-11; B "Answer changes").
   - [E] A dispute is listed only while it is one, for the perspective and knowledge time asked (B "Tests").
4. **Visibility**
   - [E] common 0.2.
   - [E] A value overridden by a nearer world is not listed (B points decided 3).
5. **Ordering and multiplicity**
   - [E] One entry per content class under identity (B-D §2.5); compare as a multiset keyed by `type` and `roles`.
   - [D] Sorted by (type, str(roles)): code only. B-D §3 says "sorted as today" without defining the order.
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `[entry].support` | `judgement` = established | [E] B-D §4 |
   | supporting | `[entry].assertions` | `judgement` = disputed | [E] contents B-D §4; role P-1 |
   | conflicting | `[entry].denials` | disputed by polarity | [E] contents; role P-1 |
   | conflicting | `[entry].conflicts` | disputed by a constraint | [E] contents B-D §4; role P-1 |
   | not cited | listed contents not asked about by the question | — | common 0.9 (pick by field) |

7. **Derivations and admissible premises**
   - [E] None are presented (REG DI-7).
8. **Refusals**
   - None documented.
9. **Limitations and gaps**
   - [E] DI-9: the exclusivity cost (`facts_about(cal)` in the plan: 27 → 47 queries; B "After the merge").
   - [E] DI-7.
   - [E] DI-17.
   - [E] GAP-MEAS-6 (two stated values of one quality are not disputed).

**Local items**
- D-FA-1: an attested-constraint dispute lists `conflicts` but not the constraint's attestations. This is the gap
  DI-19 closed for `holds` only (REG DI-19), unregistered for listings.
- D-FA-2: the docstring adds "including rivals that do not mention the subject". B-D §4 says "any constraint rivals".
  The two are consistent, but the docstring is more specific.
- D-FA-3: the entry order is not stated in design (see Ordering).

---

### `occurrence(world, occurrence, as_of=None, perspective="system")`

**Serves:** first step of X3 and X6 (the `event_role` template, E2D §3.6; T `event_role`). Gap probes: GAP-MULTI-8
(DI-14 and DI-17 in variants), GAP-MULTI-2.

1. **Inputs and conditions**
   - [E] An occurrence id. Any member of its identity class gives the same view, apart from the `occurrence` key
     (ID-9).
   - [E] There is no valid time: participants are not a state at a time (D-D §3.6).
   - [D] A non-occurrence id is not refused (code). No design text covers it.
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
   - [E] DI-14: a variant lists an inherited link whose account is `none` (REG DI-14).
5. **Ordering and multiplicity**
   - [E] Order and identifiers never change a judgement (D-D §9; D §4).
   - [E] `roles` is keyed by stored label (ER-5).
   - [D] List orders (accounts, players, constraints) are code only: compare as multisets.
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
   - [E] DI-9 (about 19 → 86 queries per view; D §7, O-3).
   - [E] DI-14.
   - [E] ID-10 not implemented.
   - [E] DI-17.
   - [E] TI-1 `derived` marker deferred.
   - [E] Destination and product stay single.
   - [E] GAP-MULTI-8.

**Local items**
- D-OC-1: `participants` collects every attestation of each listed description, accepted or not (code). ER-5 says
  "unchanged" (Core 0.3) and D-D §7 measured 0 such cases. Questions read `resolved` instead.
- D-OC-2: `descriptions` uses usable links, while `accounts` uses ESTABLISHED canonical records (ID-10 deferred;
  GATE §1.5).
- D-OC-3: the input is not validated as an occurrence (code). Design is silent.
- P-OC-1: cite the classification's support as supporting when a kind-scoped constraint applies (ER-2 makes it part of
  the judgement).

---

### `occurrence_status(world, occurrence, t, as_of=None, perspective="system", details=True)`

**Serves:** X4, second step (`explain` → `occurrence_status`, E2D §3.6); C2, through the per-occurrence status that
`causes_of` reports (E2D §3.4; SB LABS-1.011). Gap probes: GAP-MULTI-8 (DI-14), GAP-MULTI-2.

1. **Inputs and conditions**
   - [E] An occurrence id and a valid time t. Aliases take the identity class (ID-D §3.9; ID §4).
   - [D] A non-occurrence id is not refused (D-OS-1).
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `status` | str | `accepted`, `denied`, `disputed`, `not established` | [E] SB LABS-1.011, LABS-1.012; T |
   | `answer` | Answer | the `exists()` answer that `status` is read from | [E] SB "One existence judgement" |
   | `existence[*]` | list | judgement (claim label), status, attestations | [E] SB L422-424 |
   | `descriptions[*]` | list | description, `account` (`accepted`/`unreviewed`/`rejected`/`none`), `account_by`, `describes` (claim label), `describes_by` | [E] SB LABS-1.011; D "After the merge"; B-D §6 (DI-5 labels) |

3. **Judgement and uncertainty**
   - [E] The status is judged only from the occurrence's own existence attestations. Descriptions, links, causal
     claims and process membership never establish it (Occ-1; SB LABS-1.011).
   - [E] `exists()` gives ASSERTED or STIPULATED (true, or false before the existence starts or after it ends), or
     DISPUTED. Otherwise it gives UNKNOWN or NOT_YET_KNOWN, and never INFERRED (SB L419-421).
   - [E] An accepted account of a denied occurrence stays visible (Occ-2).
   - [E] A role dispute never decides existence (ER-4).
   - [D] `denied` also covers "before creation" and "after it ended" at t (D-OS-2).
4. **Visibility**
   - [E] common 0.2.
   - [E] A plan can stipulate that an event did not happen: `denied` in the plan, the base unchanged (SB LABS-1.011
     "Hypothetical overrides").
5. **Ordering and multiplicity**
   - [D] `descriptions` sorted by id: code only; compare as a multiset keyed by `description`.
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
   - [E] DI-20 (loads a whole world; 52 → 71 ms with perspectives).
   - [E] DI-14.
   - [E] GAP-MULTI-8.

**Local items**
- D-OS-1: for a non-occurrence id, `exists()` infers existence from participation, so the status can be `accepted`
  (code `exists`). SB LABS-1.011 scopes the reader to occurrences without stating a refusal.
- D-OS-2: `denied` = `exists().holds is False`, which includes temporal non-existence at t. SB L345 lists `denied`
  without saying so.
- D-OS-3: `describes` is judged at t here, but at the account's start in `occurrence()` (D §2). D-D §3.2 calls them
  the same label.

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
   - [D] `holders` and `appointments` sorted by holder: code only; compare as multisets.
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `appointments[judgement=established].evidence[acceptance=accepted].attestation` | always | [E] D2 §3; CL C1 |
   | supporting | `conflict.appointments[*].attestations` | a conflict | [E] D2 §3 |
   | conflicting | `conflict.constraint.support` | a conflict | [E] contents D2 §3, REG DI-19; role P-1 |
   | alternative | `appointments[*].evidence[acceptance≠accepted]` | always | [E] v0.2 §6.2; D2 §3 |
   | not cited | the claims of appointments that are not established (denied, expired) | explanatory, never required | [E] CL C1 (X-003) |

   - Under P-1, a conflict's appointments are each other's rivals. Supporting vs conflicting is not decidable per
     holder, because the answer lists all of them (as for value_at, P-VA-1). They are therefore supporting.
     [P] P-OH-1.
7. **Derivations and admissible premises**
   - [E] None are presented. No authority from an office, no office from an act (D2D §2).
8. **Refusals**
   - None documented. "The organisation profile is not installed" is a precondition (common P-5).
9. **Limitations and gaps**
   - [E] DI-9 (exclusivity cost).
   - [E] DI-22 (cross-world growth, 40 → 55 ms).
   - [E] D-D-4 (no context containment).
   - [E] DI-17.
   - [E] GAP-MULTI-2.

**Local items**
- D-OH-1: D2D §2-3 has status ASSERTED/INFERRED/…, "value_of on the slot", "unaccepted claims as alternatives" and
  INFERRED non-holders. These are superseded by D2 §1 (no slot, no inference) and C-5 (status None). The
  implementation has no `alternatives` field: unaccepted claims appear in each appointment's `evidence`. Cite D2 and
  C-5 only.
- D-OH-2: the office is matched by stated id (`e.stated("class")`) but the context by identity class; `holder` is the
  first attestation's stated name (code). Design is silent.
- D-OH-3: the `ValueError` for a missing profile is code only. Common P-5 treats it as a precondition.
- P-OH-1: the claims of every established holder in a conflict are supporting; only the constraint's support is
  conflicting.


## Part B. Spatial transformations and frames

### Reader contracts: spatial transformations and frames (S, F)

Draft for LABS-1.062. Shared rules: `this document's §0` (labels, evidence roles, premise admissibility, refusals,
ordering). Evidence and full citations: `docs/stage-e/e2-reader-contracts/evidence-spatial.md`.

Citation abbreviations: **A1** `docs/core-0.4/stage-a1.md`; **A2** `docs/core-0.4/stage-a2.md`; **v0.2**
`docs/architecture/world-ontology-v0.2.md`; **Plan** `docs/plans/core-0.4-plan.md`; **IB-D**
`docs/core-0.4/pre-e-increment-b-design.md`; **IB** `docs/core-0.4/pre-e-increment-b.md`; **IC-D**
`docs/core-0.4/pre-e-increment-c-design.md`; **ID-D** `docs/core-0.4/pre-e-identity-design.md`; **E2-D**
`docs/stage-e/stage-e2-evaluation-design.md`; **INV** `docs/stage-e/stage-e-entry/e2-capability-inventory.md`;
**B** `docs/core-0.4/stage-b.md`; **RD** `benchmark/e2/spec/reader-docs.md` (supplementary); **phys**
`src/worldmodel/physical.py`, **spat** `src/worldmodel/spatial.py` (supplementary).

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
   - TB-3 [D] No angular-tolerance parameter; chain agreement always uses 1e-9 rad (spat `close_to`). The design
     says "the angular tolerance" without naming which (A2 "Agreement"). See D-TB-1.
   - TB-4 [D] `source == target`, unknown frame ids: not covered by the design. The implementation returns INFERRED
     with an identity transform and an empty chain for any id (phys `_resolve`). See D-TB-2.
2. **Output fields and vocabulary:**

| Field | Type | Values | Label/source |
|---|---|---|---|
| `status` | Status | INFERRED, DISPUTED, UNKNOWN | [E] A2 "Outcomes"; E2-D 2 table |
| `transform` | (q, t) or None | the composed source→target transform (p_target = R(q) p_source + t); None when DISPUTED or no chain; an unverified candidate when truncated but reached | [E] A2 "Outcomes", "Results"; conventions Plan 9.6 |
| `chain` | list of steps | the shortest chain, each step `parent`, `child`, `direction` (`forward` child→parent / `inverse`), with its supporting attestations | [E] A2 "Search", "Conventions/Inverse"; step fields `translation`, `rotation`, `disputed` [D] (phys `_describe`) |
| `frames` | list of ids | frames along the chain | [E] A2 "Results" (field named); content [D] |
| `reason` | text or None | "no frame chain from X to Y"; "search truncated after N edge examinations (limit L) without reaching Y"; "verification incomplete: search truncated, other chains were not checked for agreement" | [E] A2 "Resource limit"; other strings [D] (phys `_resolve`) |
| `search.complete` / `.truncated` | bool | always one of the two true | [E] A2 "Resource limit" |
| `search.verified` | bool | true when every route was checked | [E] A2 "Outcomes"; value for complete no-chain [D] (D-TB-5) |
| `search.cycle`, `.hops`, frames reached, edges examined, edges checked | ints/bool | as named | [E] A2 "Resource limit" (field spellings [D]) |
| `search.inconsistent` | list | each inconsistent edge with its sources, translation gap (m) and angle gap (rad) | [E] A2 "Outcomes" |
| `rule` | text | `frame-transform/v1` | [E] A2 "Frame chains / Provenance" (present on every result [D]) |

   - TB-5 [D] NOT_YET_KNOWN is never returned, even when no transform is visible; v0.2 5.6 distinguishes it (D-TB-2).
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
     "Points decided" 6; ID-D 3.8, ID-8). See D-TB-4 on GAP-SPATIAL-5.
   - TB-16 [D] Plan 9.6 "Time": a derived result holds over the intersection of its inputs' intervals, with the
     latest input as its knowledge time. The answer reports neither (D-TB-6).
5. **Ordering and multiplicity:**
   - TB-17 [E] Exactly one chain is reported, the shortest (A2 "Search"). `chain` runs from source to target [E]
     (A2 "Results": "step by step").
   - TB-18 [D] Tie-breaking between equally short chains is not designed (phys sorts edges by parent, child,
     support). Questions must not depend on which shortest chain is reported when there are several.
   - TB-19 `search.inconsistent` is a multiset (common 0.9).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `chain[*].support` | status INFERRED | [E] A2 "Provenance" (cites every transform on the chain) |
| conflicting | `search.inconsistent[*].support` | status DISPUTED by an inconsistent edge | [E] A2 "Outcomes" |
| conflicting | `chain[*].support` where `chain[*].disputed` is true | DISPUTED by a disputed transform on the chain | [D] step `disputed` flag only in phys; design says only "DISPUTED" (A2 "Outcomes") |
| not cited | a disputed but consistent edge on a route other than `chain` | DISPUTED with reason "a transform on a chain is disputed" | [D] D-TB-3 |
| alternative | none: unreviewed transforms are not reported | always | [D] D-TB-7 (v0.2 6.2) |
| supporting (unverified) | `chain[*].support` | UNKNOWN, `verified: false`, transform returned | [E] A2 LABS-1.009 ("candidate only"); never authoritative |

7. **Derivations and admissible premises:**
   - TB-20 [E] Rule `frame-transform/v1`; premises are the transform attestations on the chain (A2 "Provenance";
     v0.2 3.5 C8). No derivation record is stored (Plan Stage A table; common 0.7).
   - TB-21 [E] Admissible premises: `frame-transform` steps that hold for the question's world, perspective, `as_of`
     and `t` (A2 "Edges"; common 0.7). A disputed transform is not admissible to yield a transform: the answer is
     DISPUTED with no transform (A2 "Outcomes").
   - TB-22 [D] A truncated, reached candidate whose chain contains a disputed edge still returns its transform (phys
     `_resolve`); the design is silent (D-TB-8). `source == target` presents the rule with no premises (D-TB-2).
8. **Refusals:** none documented. A missing chain is an UNKNOWN answer, never a refusal and never invented [E]
   (A2 "Frame chains / Missing"). Writer refusals of `relate_frames` (parent == child, non-unit quaternion) are
   writer-side and not reader refusals [E for the norm, Plan 9.6].

| Name | Condition | Exception / message | Established? | Source |
|---|---|---|---|---|
| — | — | — | — | — |

9. **Limitations and gaps:** [E] GAP-SPATIAL-1 (no transform uncertainty), -3 (quaternions only), -4 (no units on
   spatial content), -5 (see D-TB-4); GAP-FRAME-1 (anchors not used in chains), -4 (no hierarchy) (INV 1-2; E2-D 4).
   [E] Every question loads all judged transforms of the world (A2 "Known limitations").

**Local items:**
- D-TB-1: chain agreement uses "the angular tolerance" (A2 "Agreement"; "Where it applies") vs fixed 1e-9 rad, no parameter (phys `_resolve`, spat `close_to`).
- D-TB-2: `source == target` / unknown ids not covered by design vs INFERRED identity with no premises and never NOT_YET_KNOWN (phys `_resolve`; v0.2 5.6; common 0.7 rule 2).
- D-TB-3: "a disputed transform on any route: DISPUTED" and v0.2 5.3 "never silent" vs off-chain disputed edge not cited in `chain` or `search.inconsistent` (A2 "Outcomes"; phys `_resolve`).
- D-TB-4: GAP-SPATIAL-5 lists frames judged without same-as as a gap (INV 1; E2-D 4) vs design: frames cannot be same-as, DI-12 closed (IB point 6; ID-D ID-8; deferred-issues DI-12); phys code comment stale.
- D-TB-5: `verified` for a completed no-chain search not designed (A2 "Resource limit") vs `false` (phys `_resolve`).
- D-TB-6: Plan 9.6 "Time" (intersection interval, knowledge time of latest input) vs not reported (phys `transform_between`).
- D-TB-7: v0.2 6.2 unaccepted attestations returned as alternatives vs no `alternatives` field (phys `transform_between`).
- D-TB-8: truncated-but-reached candidate through a disputed edge: design silent (A2 LABS-1.009) vs transform returned (phys `_resolve`).
- D-TB-9: step fields `translation`, `rotation`, `disputed`, `search.edges_in_graph`, `relevant_edges`, and reason strings beyond A2 are implementation-only (phys `_describe`, `_search`).

---

### `where(world, thing, frame, t, as_of=None, perspective='system', angle_tolerance=1e-9, limit=None)`
**Serves:** F1-F6 (H) (E2-D 3.2); X1 (H, via `measurements` → `where`) (E2-D 3.6). Gap probes F7 (GAP-FRAME-1, -2),
F8 (GAP-FRAME-3: must stay UNKNOWN between stated poses, E2-D 3.7), F10 (GAP-FRAME-6), GAP-SPATIAL-2, -6, -7, -8.

1. **Inputs and conditions:**
   - WH-1 [E] "Where is `thing` in `frame` at t", judged for the perspective; `where` is the position-specific
     interface because `holds` names no parameters (A2 "`holds` (D-A2-5)").
   - WH-2 [E text, D ruling] `angle_tolerance`: per-question policy (v0.2 Π), default 1e-9 rad (A2 "Orientation
     comparison policy"). D-A2-7 is "please confirm" with no recorded ruling (A2 decisions table). D-WH-1.
   - WH-3 [E] `limit` as TB-2, applied to each candidate's search (A2 "Resource limit").
   - WH-4 [E] `world`, `t`, `as_of`, `perspective` as common 0.2.
2. **Output fields and vocabulary:**

| Field | Type | Values | Label/source |
|---|---|---|---|
| `status` | Status | STIPULATED, ASSERTED, INFERRED, DISPUTED, UNKNOWN, NOT_YET_KNOWN | [E] E2-D 2 table; IC-D 4 (`where` row) |
| `candidates` | list | one per position statement that holds for the perspective at t and can be related to `frame` | [E] A2 "Position judgement / Candidates" |
| `candidates[*].x/.y/.z` | (lower, upper) metres or None | mapped range; None when the candidate's chains disagree | [E] A2 "Results"; "Ranges" |
| `candidates[*].orientation` | quaternion or None | orientation in `frame` | [E] v0.2 3.5 (optional orientation); derivation shape [D] |
| `candidates[*].status` | Status | ASSERTED/STIPULATED (direct, by basis), INFERRED (derived), DISPUTED (chain disagrees), UNKNOWN (truncated) | [E] A2 "Measurement uncertainty"; "Truncated results in `where`" |
| `candidates[*].direct` | bool | stated in `frame` vs derived | [E] A2 "Candidates" (field name [D]) |
| `candidates[*].chain`, `.search` | as TB | the candidate's frame chain and search | [E] A2 "Results" |
| `candidates[*].verified` | bool | false for a candidate from a truncated search | [E] A2 "Truncated results in `where`" |
| `candidates[*].position_support` | ids | the position attestations | [E] A2 "Provenance" (field name [D]) |
| `conflicts` | list of candidate pairs | verified conflicting pairs | [E] A2 "Disjoint" ("conflicting pairs are listed") |
| `conflict_details[*].kind` | text | `disjoint ranges`, `orientations differ`; with separation and tolerance used; `unverified` flag | [E] A2 "Reporting"; "Truncated results" |
| `verified`, `reason` | bool, text | false and "verification incomplete…" while any candidate is unverified or a truncated search left a statement incomparable | [E] A2 "Truncated results in `where`" |
| `incomparable` | list | statements whose frame cannot be related to `frame`, each with its `search` | [E] A2 "Different frames"; "Results"; D-A2-4 |
| `alternatives` | ids | unreviewed claims | [E] A2 "Time, perspective and worlds" |
| `judgement` | text or None | `compatible` [E] (A2 "Overlapping"); `conflicting`, `single`, None [D] | D-WH-2 |
| `angle_tolerance` | float | the tolerance used | [E] A2 "Reporting" |
| `stated_in`, `stated`, `orientation_stated`, `rule`, `candidates[*].reason` | — | implementation-only shape | [D] (phys `where`) |

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
   - WH-13 [D] The chain agreement inside each candidate uses 1e-9 rad, not `angle_tolerance` (D-TB-1, D-WH-1).
4. **Visibility:**
   - WH-14 [E] Only statements that hold at t for the perspective count; no persistence beyond a stated interval
     (A2 "Time, perspective and worlds"; Plan 9.6 "no extrapolation"; E2-D F4).
   - WH-15 [E] A variant's own position or transform overrides the inherited one; the actual world is unaffected
     (A2 "Time, perspective and worlds"; demonstration table).
   - WH-16 [E] As known before an acceptance or supersession (`as_of`), the earlier answer stands (A2 demonstration;
     v0.2 C8).
   - WH-17 [E] The thing is judged with its established same-as group (ID-D ID-8); frame chains are not (TB-15).
     [D] The implementation selects `alternatives` and the UNKNOWN/NOT_YET_KNOWN test by the raw id (D-WH-5).
5. **Ordering and multiplicity:**
   - WH-18 [D] No design order for `candidates`, `incomparable`, `alternatives`, `conflicts`. The implementation
     orders candidates by stated frame id, and `conflicts` are index pairs into `candidates`. Questions pick
     candidates by field (`stated_in`, `direct`) and compare `conflicts` as sets of candidate identities, never by
     position (common 0.9; D-WH-6).
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
   - WH-22 [D] Disputed position premise: a derived candidate takes its chain's status, so a position statement
     disputed by polarity (listed by `poses` since DI-1) mapped through a consistent chain yields an INFERRED
     candidate, and the answer can be INFERRED. v0.2 5.2 E6 requires every premise usable; common 0.7 admits a
     disputed premise only with a DISPUTED answer; A2 covers disputed transforms only (phys `where`, candidate
     `status`). No question may rest on this case until ruled (D-WH-3).
   - WH-23 [E] Direct candidates present no derivation.
8. **Refusals:** none documented. Unrelatable frames give `incomparable` entries, never a refusal or a guess [E]
   (A2 "Different frames"). `value_of` on a parameter-valued slot points to `where`/`poses` (implementation only,
   not a `where` refusal) [D].

| Name | Condition | Exception / message | Established? | Source |
|---|---|---|---|---|
| — | — | — | — | — |

9. **Limitations and gaps:** [E] conservative range propagation (GAP-SPATIAL-2); orientations exact, tolerance per
   question (A2 "Known limitations"); no best estimate; truncated searches give unverified candidates; about 32-35
   queries, cross-world growth (DI-22). Gap ids: GAP-SPATIAL-6, -7, -8; GAP-FRAME-1, -2, -3, -6; GAP-MULTI-2, -5
   (INV 1, 2, 6; E2-D 4). No identity from proximity [E] (A2 "No identity from proximity").

**Local items:**
- D-WH-1: per-question `angle_tolerance` "serves … chain agreement" (A2 "Where it applies") and D-A2-7 unconfirmed vs chain agreement fixed at 1e-9 rad (phys `where` → `_resolve`).
- D-WH-2: `judgement` values `conflicting`, `single`, None not in design (A2 "Position judgement" uses compatible/conflict) vs phys `where`; also `compatible` reported when status is UNKNOWN with an unverified disjoint pair, or DISPUTED by a disputed chain.
- D-WH-3: disputed position premise (WH-22): v0.2 E6 / common 0.7 vs INFERRED derived candidate (phys `where`).
- D-WH-4: `alternatives` scope: "unreviewed claims" (A2) vs unreviewed position claims in any frame, ids only (phys `where`, model `_alternatives`).
- D-WH-5: ID-8 subject identity class (ID-D 9) vs raw-id filter for `about`/`alternatives` (phys `where`); effect on aliases unverified.
- D-WH-6: no designed order of candidates (A2 silent) vs frame-id order with `conflicts` as indices (phys `poses`, `where`).
- D-WH-7: Plan 9.6 "Time" reporting absent for derived candidates (as D-TB-6).
- P-WH-1: in a DISPUTED answer, supports of candidates outside every `conflicts` pair stay supporting.

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
| `assertions`, `denials`, `judgement` | — | required for listings by IB-D 4, not returned | [D] D-PO-2 |

3. **Judgement and uncertainty:**
   - PO-3 [E] Disjoint positions of one thing in one frame (or orientations differing beyond the default 1e-9 rad)
     are DISPUTED with their rivals in `conflicts` (A2 "The same rule everywhere", "Where it applies"; IB-D 6 table).
     [D] The docstring says conflicts "are not judged in A1" (RD `poses`), true only of A1 (A1 D-A1-2). D-PO-1.
   - PO-4 [E] Polarity-disputed positions are listed in place, marked DISPUTED (DI-1; IB "Readers"). [D] The
     docstring says "positions that hold at t" (D-PO-1).
   - PO-5 [E] Ranges are reported as stated; nothing reconciled (A2 "Nothing is reconciled").
4. **Visibility:**
   - PO-6 [E] As `facts_about`: holding or disputed at t, with world inheritance, acceptance and supersession (A1
     "API"; IB-D 2.1). An ended position does not hold after its end (A1 "The reference world / Time").
   - PO-7 [E] `facts_about` uses the context's identity (ID-D 3.8). [D] `poses` filters entries by the raw id in
     `positioned` (phys `poses`); effect on aliases unverified (D-PO-3).
5. **Ordering and multiplicity:**
   - PO-8 [E] Several positions in one frame are all listed (A1 D-A1-2; A2 "Identical": identical ranges are one
     entry with several supporting attestations).
   - PO-9 [D] Sorted by frame id in the implementation; no design order. Compared as a multiset (common 0.9; D-PO-4).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `[*].support` | every entry | [E] B "One functional judgement" |
| conflicting | `[*].conflicts` | entry DISPUTED by the slot | [E] B; A2 "The same rule everywhere"; split per common 0.4 [P-1] |
| conflicting | the denials of a polarity dispute | entry DISPUTED by polarity | [E] IB-D 4 requires them; [D] not returned (D-PO-2) |
| alternative | none reported | — | [D] (phys `poses`; no alternatives field) |

7. **Derivations and admissible premises:** none presented [E] (A1 "API": stated positions only).
8. **Refusals:** none documented.

| Name | Condition | Exception / message | Established? | Source |
|---|---|---|---|---|
| — | — | — | — | — |

9. **Limitations and gaps:** [E] every new position is a new proposition (D-A1-5, U-3); GAP-SPATIAL-8 (`holds` cannot
   single out a position), GAP-FRAME-6 (parts not positioned through their assembly) (INV 1-2).

**Local items:**
- D-PO-1: docstring "positions that hold at t … conflicts … not judged in A1" (RD `poses`) vs A2 slot conflicts and DI-1 disputed entries (A2 "The same rule everywhere"; IB "Readers").
- D-PO-2: IB-D 4 "citing the assertions, the denials and any constraint rivals" vs `judgement`, `assertions`, `denials` not projected (phys `poses`).
- D-PO-3: ID-8 identity class (ID-D 9) vs raw-id filter (phys `poses`).
- D-PO-4: frame-id order is implementation-only (phys `poses`).

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
| `parents[*]` / `children[*]` | parent or child id, `translation` (m), `rotation` (w,x,y,z), `status`, `support` | transforms as stored, one hop, not composed | [E] A1 "Selected results"; IB-D Q5 (slot applies); field names and "as stored" [D] (RD `frame_info`) |
| `positioned` | ids | things positioned in the frame at t | [D] docstring only (RD `frame_info`); no status per id |
| `name` | text | display name | [D] not judged for world, perspective or time (phys `names`); A1 says reads are judged (A1 "API") |

3. **Judgement and uncertainty:**
   - FI-3 [E] Two different accepted transforms for one pair are DISPUTED (`frame-transform` slot) (IB-D Q5; A2 "The
     same rule everywhere"). A second accepted anchor is DISPUTED (A1 "Tests"; IB-D 2.3).
   - FI-4 [E] Polarity-disputed content is listed and marked DISPUTED (IB-D 4; IB "Readers").
   - FI-5 [D] A disputed position appears in `positioned` without any marking (phys `frame_info`; D-FI-1).
4. **Visibility:** FI-6 [E] as `facts_about` (A1 "API"; IB-D 2.1): inheritance, acceptance, supersession, `as_of`.
5. **Ordering and multiplicity:** FI-7 [D] `positioned` is sorted and de-duplicated; other lists follow
   `facts_about` order; no design order. Compared as multisets (common 0.9).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `parents[*].support`, `children[*].support` | every transform entry | [E] A1 "Selected results" (status shown); IB-D 2.2 |
| conflicting | rivals of a DISPUTED transform or anchor | entry DISPUTED | [E] IB-D 4 requires citing them; [D] not returned (D-FI-1) |
| not cited | anchors and positions | always (no support field) | [D] D-FI-1 |

7. **Derivations and admissible premises:** none presented [E]: transforms are stored values, not composed (A1 "API";
   composition is A2's `transform_between`).
8. **Refusals:** none documented. An unknown frame id is a precondition question, not a refusal (common 0.8 [P-5]).

| Name | Condition | Exception / message | Established? | Source |
|---|---|---|---|---|
| — | — | — | — | — |

9. **Limitations and gaps:** [E] GAP-FRAME-1 (anchoring has no geometric effect: reported only), GAP-FRAME-4 (one hop,
   no hierarchy), GAP-FRAME-5 (no history reader for a frame) (INV 2; E2-D 4).

**Local items:**
- D-FI-1: IB-D 4 "citing the assertions, the denials and any constraint rivals" vs `anchored_to` without support, `positioned` without status or support, no conflicts/denials anywhere (phys `frame_info`).
- D-FI-2: A1 "API" (every answer judged) vs `name` read directly, unjudged (phys `names`).
- D-FI-3: field names, "as stored" and `positioned` are docstring-only (RD `frame_info`); design gives only the A1 output line.


## Part C. Measurement and calibration

### Reader contracts: measurement family (draft, LABS-1.062)

These are the reader contracts for `measurements` (ME), `compare_measurements` (CM), `convert` (CV),
`laboratory.calibration_status` (CS) and `laboratory.measurement_calibration` (MC).

- **Status of statements:** labels [E], [P] and [D] follow `this document's §0` §0.1.
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
   - [D] **D-ME-1:** the meaning of `t` ("only attestations that hold at t") is docstring only (qualities.py
     docstring); no design text was found. Questions should use `t=None` until the owner rules.
   - [E] The fixture defines a unit and a quality kind of the same dimension (stage-c C1 `measure`).
2. **Output fields and vocabulary**
   - The answer is a list of entries, one per visible `has-quality` attestation about (bearer, quality).

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `[*].attestation` | id | — | [E] stage-c D-C-2 (the attestation is the unit of provenance) |
   | `[*].kind` | str | `measurement` (rests on records) / `statement` (no record) | [E] stage-c C0 "stay separate"; C1 API |
   | `[*].range` | (float, float) | [v − ku, v + ku] in the dimension's SI unit | [E] v0.2 §3.3; D-C-1 |
   | `[*].unit` | id | the SI unit | [E] D-C-1; stage-c C0 units |
   | `[*].coverage_level` | float | a function of k (k = 2 ≈ 0.954) | [E] v0.2 §3.3, C4 (the formula is [D] D-ME-2) |
   | `[*].acceptance` | str | accepted / unreviewed / rejected / retracted / superseded | [E] v0.2 §5.6; incB §2.2 |
   | `[*].records[*].raw_value`, `raw_unit`, `standard_uncertainty`, `coverage_factor`, `conditions`, `calibration` | — | as written; conditions as exact text | [E] D-C-1, D-C-7; v0.2 clarification B |
   | `[*].records[*].report` | str | whether the `reports` claim is accepted | [E] stage-c "As implemented" (judged parts) |
   | `[*].records[*].activities[*].start`, `end`, `operator`, `instrument` | Window / ids | from the activity's account | [E] stage-c provenance read; [D] field names |
   | `[*].usable` | bool | accepted, not superseded, supporting stance, polarity true | [D] D-ME-3 (implementation only) |
   | `[*].attester`, `basis`, `valid`, `content` | — | — | [D] D-ME-4 (no design statement) |

   - [E] No answer status is given: this is a collection, and rule C folds nothing (incC §4, `measurements` row).
3. **Judgement and uncertainty**
   - [E] The range carries the measurement uncertainty. Credence and stance are separate, and calibration doubt never
     widens a range (v0.2 §3.3 "two kinds of uncertainty"; plan acceptance criterion C).
   - [E] Nothing is combined or reconciled (v0.2 clarification B).
   - [E] Each entry's acceptance is judged per perspective. The rests-on link, the record values, the operator and the
     instrument are not judged (stage-c "As implemented").
4. **Visibility**
   - [E] Supersession is per perspective. A perspective keeps the original until it accepts the correction, and the
     superseded attestation keeps its own record (stage-c "Correction"; core-0.3 supersession).
   - [E] One measurement is visible at `as_of` all together or not at all (D-C-8, one transaction time).
   - [E] Variant worlds inherit attestations with their links (stage-c "Hypothetical worlds"; v0.2 §6.2).
   - [D] **D-ME-5:** same-as identity is not applied. Attestations about an accepted alias of the bearer are dropped
     (src Discrepancy 10; v0.2 §4.2, ID increment). Do not author identity questions here until ruled.
   - [D] **D-ME-6:** with `t` given, the filter uses the attestation's own interval, so a measurement written without
     `persists` or `end` has an empty [s, s) interval and never holds at t (src Discrepancy 2; plan §9.2 "the
     quality's valid time"). This was found by reading code; it needs a probe.
5. **Ordering and multiplicity**
   - [E] One entry per attestation, not per content (stage-c D-C-2 probe case 1).
   - [E] Records and attestations are many-to-many (stage-c "As implemented").
   - The list is a multiset (common §0.9). [D] Sorting by attestation id is implementation only (stage-c
     Validation: random ids).
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `[kind=measurement, usable=true].attestation` | always | [P] P-ME-1, from v0.2 §6.2 (usable attestations support); harness §5.1 |
   | supporting or alternative | `[kind=statement, usable=true].attestation` | a "values stated" question | [D] D-ME-7: the harness counts usable statements as support; stage-c keeps statements apart. Ruling needed |
   | alternative | `[usable=false].attestation` (unaccepted, superseded, rejected, retracted, non-supporting stance, denials) | always | [E] v0.2 §6.2 |
   | not cited | `records[*].record`, `activities[*].activity` (not attestations); `produced` and `reports` ids (not returned) | — | [E] stage-c D-C-2 (structural link, not an attestation) |

   - For M4, gold names the current value by its `[acceptance=accepted]` entry, and history by
     `[acceptance=superseded]` (common §0.5 names `<step>`).
7. **Derivations and admissible premises**
   - [E] None presented. The content has basis observation, and conversion to SI on write is not an inference
     (D-C-1). DI-7: no derivation record exists.
   - [E] Any `{rule, premises}` in the answer is fabricated (harness §9.3).
8. **Refusals**
   - None documented. An unknown bearer or quality returns an empty list. [D] D-ME-8: the design is silent on this.
9. **Limitations and gaps**
   - GAP-MEAS-6: `has-quality` is not a slot.
   - GAP-MEAS-7: no current-value or trend reader.
   - GAP-MEAS-8: N+1 reads (D-C-6, DI-9).
   - GAP-MEAS-10: no "undermines" link (G-3).
   - GAP-MEAS-11: DI-7.
   - [D] D-ME-9: categorical `has-quality` values (without `lower`) are not listed, despite "every stated value"
     (v0.2 §3.3 value category; stage-c C1 API).

**Local items**
- D-ME-1: the meaning of `t` is in the docstring (qualities.py) only; no design text (stage-c C1 is silent).
- D-ME-2: coverage_level = erf(k/√2) is in the implementation (qualities.py `coverage_level`); v0.2 says "95 %" for
  k = 2. Gold uses the formula with a stated tolerance.
- D-ME-3: `usable` AND-ed with polarity is implementation only; v0.2 §6.2 defines usability without polarity.
- D-ME-4: the fields `attester`, `basis`, `valid` and `content` are not in any design.
- D-ME-5: identity is not applied (qualities.py filters literal ids) versus v0.2 §4.2 and the ID increment.
- D-ME-6: point measurements have empty intervals under the `t` filter (qualities.py `measure`, end = start) versus
  plan §9.2.
- D-ME-7: are usable statements support? The harness extractor says yes; stage-c C0 says statements are listed apart.
- D-ME-8: an unknown id gives `[]`. Not a refusal (common §0.8); design silent.
- D-ME-9: categorical values are excluded (qualities.py) versus v0.2 §3.3.
- D-ME-10: statements written by generic `attest` are not normalised to SI (examples/lab.py spec) versus D-C-1
  ("the reported content is in SI").
- P-ME-1: the supporting evidence is the usable measurement attestations; everything else listed is an alternative.

---

### `compare_measurements(world, bearer, quality, t=None, as_of=None, perspective=system)`

**Serves:**
- M2 and M3 (H) (E2 §3.3);
- gap probes M7 (GAP-MEAS-1), M8 (GAP-MEAS-4), GAP-MEAS-2 and GAP-MEAS-3.

1. **Inputs and conditions**
   - [E] The same as `measurements`. It compares the measurements the perspective accepts (v0.2 clarification B;
     stage-c C1 API).
   - [D] `t` as D-ME-1.
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `status` | Status | DISPUTED / ASSERTED / STIPULATED / INFERRED / UNKNOWN / NOT_YET_KNOWN | [E] v0.2 clarification B; incC §4 (`compare_measurements` row); D-C-5 |
   | `pairs[*].relation` | str | `possibly compatible` / `incompatible` / `incomparable` | [E] v0.2 clarification B table; DR-07; stage-c C0 |
   | `pairs[*].a`, `pairs[*].b` | attestation ids | the two compared measurements | [E] v0.2 ("both ranges, each with its evidence") |
   | `pairs[*].reason` | str or None | the reason for incomparability (units, coverage levels, conditions, valid times) | [E] that a reason is given (v0.2); [D] D-CM-1: the exact strings are implementation only |
   | `measurements` | list of `measurements` entries | the compared (usable) measurements | [E] stage-c C1; fields as ME §2 |
   | `alternatives` | list | unaccepted measurements | [E] v0.2 §6.2; [D] D-CM-2 (actual content) |
   | `statements` | list | entries with no result record | [E] stage-c C0 ("listed apart, never compared") |

3. **Judgement and uncertainty**
   - [E] Pairs are judged as follows (v0.2 clarification B table):
     - comparable and the ranges overlap: possibly compatible, which is not agreement and gives no intersection;
     - comparable and disjoint: incompatible, giving DISPUTED;
     - not comparable: incomparable, with the reason.
   - [E] Incomparable when the coverage levels differ (no harmonisation: v0.2 C4; GAP-MEAS-3), the condition texts
     differ (D-C-7) or the SI units differ.
   - [E] Overlap uses closed bounds (plan §4: `$la <= $ub; $lb <= $ua`).
   - [D] **D-CM-3:** v0.2 limits the non-overlapping valid time reason to "a changing quantity"; the implementation
     applies it to every quantity. Combined with D-ME-6, point measurements at one instant are "incomparable".
   - [D] **D-CM-4:** v0.2 says "units without an accepted conversion"; the implementation compares SI unit ids
     ("no common SI unit").
   - [E] Calibration never enters the comparison (D-D3-2; d3 §3 "Never invalidating"; "calibration states that
     matter" are deferred, `stage-d-review.md` D3 Df).
   - [E] The status is decided in this order:
     - DISPUTED if any comparable pair is incompatible;
     - otherwise the core rule over the compared measurements (observation gives ASSERTED; stipulation gives
       STIPULATED);
     - otherwise UNKNOWN when something is held and NOT_YET_KNOWN when nothing is.

     Sources: incC §4; D-C-5; common §0.3.
   - [D] **D-CM-5:** "something is held" includes statements and alternatives in the implementation; the design does
     not say.
   - [E] Nothing is combined. INFERRED would need a named reconciliation policy, and none exists (v0.2 §3.3; GAP-MEAS-4).
   - [D] **D-CM-6 (accepted denials).** The design requires a dispute here:
     - v0.2 §5.3: an accepted assertion and an accepted denial of a content make it DISPUTED;
     - stage-c "Disputes" names "a polarity denial or disjoint ranges" as rival measurement attestations.

     The implementation does not produce one:
     - it excludes polarity-false attestations from `usable`, so an accepted denial resting on a record is listed in
       `alternatives` (described as "unaccepted") and never makes the status DISPUTED;
     - with `t` given, the denial is dropped entirely (qualities.py `measurements` / `compare_measurements`).

     This is a potential gap. Questions about denied measurements must not be authored until the owner rules.
4. **Visibility**
   - [E] As `measurements`; two perspectives can give different comparisons (stage-c "Disputes"; d3-design P2).
5. **Ordering and multiplicity**
   - [E] There is one comparison per pair of compared measurements (v0.2: pairwise).
   - [D] **D-CM-7:** pairs are formed over attestations, not contents (implementation), whereas v0.2 says "two
     contents". Which item is `a` and which `b` depends on ids (stage-c Validation).
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
   - D-CM-6: accepted denials (above).

**Local items**
- D-CM-1: the reason strings are implementation only (qualities.py `_incomparable`); v0.2 requires only "with the
  reason".
- D-CM-2: `alternatives` holds every unusable measurement (denials, hypotheses, superseded, rejected) versus the
  docstring "unaccepted measurements" and v0.2 §6.2.
- D-CM-3: the valid-time test applies to all quantities (implementation) versus v0.2 "for a changing quantity".
- D-CM-4: SI unit ids are compared (implementation) versus v0.2 "units without an accepted conversion".
- D-CM-5: UNKNOWN when only statements or alternatives exist (implementation); D-C-5 does not cover this case.
- D-CM-6: an accepted denial does not dispute and is filed as an alternative (implementation) versus v0.2 §5.3 and
  stage-c "Disputes".
- D-CM-7: pairs are attestation pairs (implementation) versus v0.2 content pairs.
- D-CM-8: the coverage tolerance of 1e-6 is implementation only.
- P-CM-1: in a DISPUTED answer, incompatible-pair attestations are conflicting; the other compared ones are
  supporting.

---

### `convert(value, unit, to=None)`

**Serves:**
- M5 (H) (E2 §3.3);
- gap probe M9 (GAP-MEAS-5).

1. **Inputs and conditions**
   - [E] Takes a number and a defined unit; `to` must be a unit of the same dimension (stage-c C1 API "refused across
     dimensions"; plan Stage C units).
   - [D] **D-CV-1:** the default `to=None` (giving the SI value) is docstring only.
   - [E] Units are timeless reference systems (v0.2 §3, abstract entities). There is no world, perspective, `as_of`
     or `t`.
2. **Output fields and vocabulary**

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | (value) | float | the value expressed in `to` | [E] stage-c C1 API; E2 M5 |

   - The answer carries no status and no evidence.
3. **Judgement and uncertainty**
   - [E] A unit owns `dimension`, `si-factor` and `si-offset` (plan Stage C; stage-c C0).
   - [D] **D-CV-2:** the formula si = raw × factor + offset, result = (si − offset_to) / factor_to, is in the
     `define_unit` docstring and the code only. It is standard affine conversion, consistent with the attributes.
     Gold may use it once ruled, with a stated tolerance (E2 §5.3).
   - [E] Round trips are an acceptance criterion (plan §5 C).
   - No uncertainty is propagated: the input is a value, not a range.
4. **Visibility**
   - [E] None. Reference data is timeless. [D] D-CV-3: unit definitions are not attested, so `as_of` cannot hide a
     unit (implementation).
5. **Ordering and multiplicity**
   - Not applicable.
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | not cited | — | always | [E] no attestation is involved (v0.2 §3 reference systems); harness §5.1 |

7. **Derivations and admissible premises**
   - [E] None presented. "Conversions are derived" (D-C-1) means computed rather than stored; no derivation record is
     involved (DI-7). Any `{rule, premises}` is fabricated.
8. **Refusals**

   | Name | Condition | Exception / message | Established? | Source |
   |---|---|---|---|---|
   | cross-dimension | `to` has another dimension than `unit` | `ValueError` "cannot convert …" | **yes** [E] | stage-c C1 API; harness §9 |
   | not-a-unit | `unit` or `to` names no unit with a dimension | `ValueError` "… is not a unit with a dimension" | no: a precondition failure, reported as an execution error [P] P-5 | common §0.8; qualities.py only (harness §9 "not established") |
   | compound unit | N ↔ kg·m/s² | (none: no such unit can be defined) | not a refusal; the gap is unsupported | E2 M9; GAP-MEAS-5 |

9. **Limitations and gaps**
   - GAP-MEAS-5: single-dimension, affine only; no prefixes or algebra.
   - D-CV-4: no check on non-finite values.

**Local items**
- D-CV-1: the default target is the SI unit in the docstring only; stage-c C1 API is silent.
- D-CV-2: the affine formula is in the docstring and code only; plan Stage C gives only the attributes.
- D-CV-3: `as_of` cannot hide a unit (implementation); v0.2 treats reference systems as timeless, so this is
  consistent, but not stated.
- D-CV-4: a non-finite input is not checked (qualities.py `convert`); the design is silent.
- D-CV-5: with `to=None` no SI unit needs to exist (implementation), while `measure` requires one; the design is
  silent.
- P-CV-1: not-a-unit is a precondition failure, not a refusal (common §0.8, P-5).

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
   | `in_force` | ids | certificates whose own judgement is established | [E] as a field (d3 §2); [D] D-CS-1 (its definition) |

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
   - [D] D-CS-2: whether the instrument's same-as aliases are applied is not stated by d3 (common §0.2). It needs a
     probe.
5. **Ordering and multiplicity**
   - [E] One entry per calibration content (certificate).
   - [E] The answer is independent of order and of ids (incC-report tests E7/E7b). `support` is sorted (C-4).
   - `certificates` is a multiset; the sort by certificate id is [D] (implementation).
6. **Evidence**

   | Role | Where in the answer | When | Label/source |
   |---|---|---|---|
   | supporting | `support[*]` | judgement established, expired or denied | [E] C-4; incC §3.1 |
   | conflicting | `certificates[*].evidence[acceptance=accepted].attestation` of the holdings that make the answer disputed (the accepted assertion and the accepted denial) | judgement disputed (support empty) | [P] P-CS-1 (common §0.4); [D] D-CS-3 |
   | supporting? | `certificates[judgement=not yet effective].evidence[acceptance=accepted].attestation` | judgement not yet effective (support empty) | [D] D-CS-3: E1 gold cited it (LAB-003), but the approved rule Q leaves support empty |
   | alternative | `certificates[*].evidence[acceptance≠accepted].attestation` (unreviewed, rejected, retracted, superseded) | always | [E] v0.2 §6.2; C-3 |
   | not cited | `certificates[*].certificate` (an information object, not an attestation) | — | [E] d3 §1; D-D-7 |

7. **Derivations and admissible premises**
   - [E] None presented. Calibration is a content judged like a capability; no rule is applied (d3 §2 "Shared
     judgement"; DI-7).
8. **Refusals**

   | Name | Condition | Exception / message | Established? | Source |
   |---|---|---|---|---|
   | profile-not-installed | the laboratory profile is absent | `ValueError` "the laboratory profile is not installed …" | no: a precondition failure, reported as an execution error [P] P-5 | common §0.8; laboratory.py only |

9. **Limitations and gaps**
   - GAP-MEAS-9: the reference is text, checked as exact text (G-6).
   - GAP-MEAS-10: no "undermines" relation (G-3).
   - DI-9 / GAP-MEAS-8: performance.
   - Calibration aggregation follows capable() (d3 §8).

**Local items**
- D-CS-1: `in_force` is named in d3 §2 but not defined; the implementation lists certificates judged established,
  even when the overall answer is disputed.
- D-CS-2: identity handling of the instrument is not stated in d3; the implementation is not verified.
- D-CS-3: evidence for disputed and not-yet-effective answers. The approved rule Q gives `support` empty
  (incC-report "Points decided" 2), whereas E1 gold (LAB-003, LAB-004) and the harness `deciding` fallback
  (evaluation/run.py) cite the certificates' usable claims. The owner must rule on which claims are required and in
  which role.
- D-CS-4: the certificate list is sorted by id in the implementation; no design states an order.
- P-CS-1: in a disputed answer, the accepted claims of the disputing holdings are conflicting evidence (common §0.4).

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
   - [D] **D-MC-1:** `t=None` appears in the design signature (d3 §2), but its meaning is not stated. In the
     implementation, `t` filters the measurements as `measurements(t)`, and calibration is still judged at each
     activity start. Use `t=None` until ruled.
   - [P] P-5 for the profile.
2. **Output fields and vocabulary**
   - The answer is a list of rows, one per measurement record and activity instrument.

   | Field | Type | Values | Label/source |
   |---|---|---|---|
   | `[*].record`, `[*].attestation`, `[*].instrument`, `[*].activity` | ids | — | [E] d3 §2 ("per measurement record and activity instrument"); [D] field names |
   | `[*].acceptance`, `[*].usable` | — | copied unchanged from `measurements` | [E] d3 §2, §3 "Never invalidating" |
   | `[*].stated_reference` | str or None | the record's `calibration-ref`, as exact text | [E] D-D3-2; G-6 |
   | `[*].attested` | `calibration_status` answer, or None | judged at the activity's start; includes `support` | [E] d3 §2; incC-report "Readers"; [D] D-MC-2 (when it is None) |
   | `[*].reference_check.check` | str | `matches a certificate` / `no certificate with the stated reference` / `no reference stated` / `no certificate recorded for the instrument` / `no instrument recorded` | [E] d3 §3 reference checks; d3 §6a item 3 |
   | `[*].reference_check.certificates[*]` | certificate and judgement | the matching certificates, each with its own judgement | [E] d3 §3 ("with that certificate's judgement") |
   | `[*].at` | time | the instant at which calibration is judged | [E] the activity's start (D-D3-2); [D] D-MC-3 (earliest bound) |

3. **Judgement and uncertainty**
   - [E] Calibration never invalidates, discards or downgrades a measurement. The stated reference and the attested
     calibration are reported side by side and never reconciled (D-D3-2; G-6; d3 §3).
   - [E] `attested` uses CS's judgements (incC §4: "inherits").
   - [E] Calibration doubt is not measurement uncertainty (v0.2 §3.3).
   - [D] **D-MC-4:** the precedence among the five checks is implementation only (no instrument, then no reference,
     then no certificate, then match).
   - [D] **D-MC-5:** when the activity has no usable account (`attested` None), the check says "no certificate
     recorded for the instrument" even if the instrument has certificates. d3 §3 defines that check as "the instrument
     has no calibration content".
4. **Visibility**
   - [E] Calibration is judged at the activity's start (d3-design §1; D-D-7).
   - [E] The activity's times come from its account and depend on the perspective (stage-c "As implemented").
   - [E] Perspective, `as_of` and world apply to both sides (d3 §3, hypothetical renewal).
   - [D] **D-MC-2:** "an activity without an accepted account has no time, so its calibration is not judged (None)"
     is docstring only.
   - [D] **D-MC-3:** the earliest bound of the start Window is implementation only (GAP-MULTI-2: gold must state the
     instant).
5. **Ordering and multiplicity**
   - [E] One row per (record, activity instrument) (d3 §2).
   - [D] **D-MC-6:** the following are implementation only:
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
   | conflicting | as CS row "conflicting", under `[*].attested.certificates` | attested judgement disputed | [P] P-CS-1; [D] D-CS-3 |
   | as CS | `[*].attested.certificates[...]` | attested judgement not yet effective | [D] D-CS-3 |
   | alternative | `[usable=false].attestation`; unaccepted certificate claims | always | [E] v0.2 §6.2 |
   | not cited | `reference_check.certificates[*].certificate`, `stated_reference` (text, not evidence); records and activities | — | [E] G-6 (reported, never reconciled) |

7. **Derivations and admissible premises**
   - [E] None presented. This is a fixed composition: measurements, then the activity start, then calibration status
     (d3 §2; D-D3-2). No rule is recorded (DI-7).
8. **Refusals**

   | Name | Condition | Exception / message | Established? | Source |
   |---|---|---|---|---|
   | profile-not-installed | the laboratory profile is absent | `ValueError` "the laboratory profile is not installed …" | no: a precondition failure [P] P-5 | common §0.8; laboratory.py only |

9. **Limitations and gaps**
   - GAP-MEAS-8: 411 queries for sample-12 (DI-9).
   - GAP-MEAS-9: the reference is text.
   - GAP-MULTI-2: which instant counts.
   - Inherits D-ME-5, D-ME-6 and D-CM-6 through `measurements`.

**Local items**
- D-MC-1: the meaning of `t` is not in d3 §2 (signature only); in the implementation it filters measurements.
- D-MC-2: `attested` None when there is no usable account or no instrument is docstring only; d3 is silent.
- D-MC-3: calibration is judged at the start Window's earliest bound (implementation) versus d3 "the activity's
  start".
- D-MC-4: the order of the reference checks is implementation only; the d3 §3 table has no precedence.
- D-MC-5: a misleading "no certificate recorded for the instrument" when the time is unknown (laboratory.py
  `_reference_check`) versus the d3 §3 definition.
- D-MC-6: row multiplicity (per attestation; None rows; statements absent) and the sort order are implementation
  only.
- D-MC-7: the earlier design (D-D-7, G6) placed calibration status in `measurements()`. The later approved D-D3-2
  and D-D3-3 place it in this profile function. The later decision governs; this is recorded only.
- P-MC-1: the supporting evidence is the usable measurement attestation plus the calibration's `support`.


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
| DYN | `src/worldmodel/dynamics.py` (supplementary only) |

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
- gap probes GAP-CAUSE-1, -2, -4, -5, -7 (INV §4 "Not implemented").

1. **Inputs and conditions:**
   - `effect` is an occurrence or an event description [E] (SB "Schema and API"; PLAN §8 DX-4).
   - `t` is the valid time at which claims and occurrence statuses are judged [E] (common 0.2).
   - The reader is keyed on the effect only: there is no forward reader [E] (INV GAP-CAUSE-2).
   - World, perspective and `as_of` follow common 0.2 [E].
2. **Output fields and vocabulary** (one entry per causal claim):

| Field | Type | Values | Label/source |
|---|---|---|---|
| `[i].cause`, `[i].effect` | id | the claim's players (`effect` is the queried id or the target it was lifted from) | [E] SB "Schema and API" ("every causal claim, direct or lifted") |
| `[i].level` | str | `description`, `occurrence`, `mixed` | [E] for description and occurrence (PLAN §9.3); the label `mixed` is [D] D-CO-5 |
| `[i].lifted` | bool | True when the claim answers through a describes link | [E] SB U-2 |
| `[i].lifted_via` | obj or null | {description, occurrence} | [E] that the link is identified (SB U-2); its form is [D] D-CO-2 |
| `[i].occurrences` | {id: str} | `accepted`, `denied`, `disputed`, `not established` | [E] SB "LABS-1.011", the amendment |
| `[i].applies` | bool or null | False if an involved occurrence is denied; null if one is disputed; True otherwise | [E] SB LABS-1.011; SB U-2 |
| `[i].judgement` | str | the claims vocabulary | [E] SB B0; IBD §2.4 |
| `[i].status` | Status | common 0.3 | [E] IBD §2.4 (`status`) |
| `[i].claimed_by` | [str] | attesters | [E] SB B0 ("sources") |
| `[i].attestations` | [obj] | attestation, attester, polarity, basis, stance, acceptance | [E] SB B0 ("every claim lists its attestations") |
| `[i].cause_occurrences` | [id] | — | [D] D-CO-5, not expected |

3. **Judgement and uncertainty:**
   - [E] Each entry's `judgement` is the canonical record of its own `causes` content (IBD §2.4).
     - An accepted assertion plus an accepted denial is `disputed`.
     - Unreviewed claims never decide.
   - [E] **Lifting** (PLAN §9.3; SB U-2):
     - a description-level claim answers an occurrence-level question only through describes links the perspective
       accepts, **for both descriptions**;
     - the lifted claim keeps its original status;
     - lifting is one hop: a sibling description's claim is not transferred (SB "Scope of causal claims").
     - The implementation checks only the effect side: D-CO-1.
   - [E] **F-B1:** description-level and occurrence-level claims never dispute each other automatically (SB
     LABS-1.012).
   - [E] A claim with `applies: false` stays visible as its source's account and never answers what caused the denied
     happening (SB, the LABS-1.011 "Clarification").
   - [E] Nothing is derived from order or chained (PLAN §9.3).
4. **Visibility:**
   - [E] Judged per perspective, knowledge time and world (SB B0; SB "Scope of causal claims": acceptance recorded
     later, perspective denials, snapshots).
   - [E] Only describes links the perspective accepts lift a claim (SB "Lifting"). What counts as an accepted link is
     D-CO-3.
   - [E] The hypothetical override: a plan stipulating that an occurrence did not happen gives `denied` there and
     `applies: false`; the base world is unchanged (SB LABS-1.011 table).
   - [E] Identity follows common 0.2.
5. **Ordering and multiplicity:**
   - The list is a multiset (common 0.9). The implementation's sort (judgement rank, cause, effect) is [D] D-CO-4.
   - [E] One entry per claim content: all of its attestations are in that entry (IBD §2.2).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `[i].attestations[acceptance=accepted, polarity=true].attestation` | `[i].judgement = accepted` and `[i].applies = true` ("what caused E") | [E] for the claim's attestations (SB B0); the restriction to `applies = true` is [P] P-CO-1, from SB LABS-1.011 Clarification |
| supporting | `[i].attestations[acceptance=accepted, polarity=false].attestation` | a question about one claim's `denied` judgement | [E] IBD §2.4 (deciding denials) |
| conflicting | `[i].attestations[acceptance=accepted].attestation` (both polarities) | `[i].judgement = disputed` | [E] IBD §2.2 (polarity dispute) |
| alternative | `[i].attestations[acceptance≠accepted]` | any | [E] V02 §6.2 (unaccepted attestations are alternatives) |
| not cited | entries with `applies = false` for "what caused E" | — | [P] P-CO-1 |
| not reported | the describes-link attestations used by lifting | — | [D] D-CO-2: PLAN §9.3 requires them to be cited |

7. **Derivations and admissible premises:**
   - None presented [E] (DI-7; E2DEC §4 "no fabricated derivations").
   - Lifting is a read-time link, not a derivation (SB F-B1 "Why").
   - A claim with basis `inference` gets status INFERRED with no derivation record (DI-7, GAP-CAUSE-7) [E].
8. **Refusals:** none documented. A missing `effect` id is a precondition (common 0.8).
9. **Limitations and gaps:**
   - GAP-CAUSE-1 to -7 [E] (INV §4; E2D §4).
   - DI-20, a whole-world load (performance) [E].
   - The writer `claim_cause` refuses `cause == effect`, but only in code (DYN `claim_cause`). That is not an
     established refusal [D] D-CO-6.

**Local items:**
- D-CO-1: lifting requires describes links for both descriptions (PLAN §9.3, "both descriptions"). The code checks
  only the effect side and returns a cause description with no accepted link as `lifted` with `applies: true` (DYN
  `causes_of`).
- D-CO-2: the design requires the describes links to be cited (PLAN §9.3, "cites the describes links"; SB "Lifting",
  "says which link it used"). `lifted_via` gives two ids with no attestations or judgement, and only the effect side
  (DYN `causes_of`).
- D-CO-3: "accepted describes link" (SB U-2). The code counts any usable positive attestation, even when the link's
  canonical judgement is DISPUTED (DYN `_Memo.occurrences`; model `descriptions`).
- D-CO-4: no design order. The code sorts by judgement rank (six labels; the rest last), then cause, then effect (DYN
  `causes_of`).
- D-CO-5: `cause_occurrences` and the label `mixed` come from the docstring and code only. PLAN §9.3 describes the
  mixed form without naming it.
- D-CO-6: the self-causation refusal exists in code only (DYN `claim_cause`), with no design text.
- P-CO-1: for "what caused E", only accepted claims with `applies: true` are supporting. Claims with `applies: false`
  are not cited (SB LABS-1.011 Clarification). For `applies: null`, the question states its own admissible set. HR
  §5.1 and the harness extractor `ev_claims` currently cite every accepted claim.

---

### `effects_of(world, event, t, as_of=None, perspective=SYSTEM)`
**Serves:**
- C3 (H) (E2D §3.4; GAP-HARNESS-2);
- gap probe GAP-CAUSE-3 (INV §4).

1. **Inputs and conditions:**
   - `event` is an event description [E] (V02 §3.2: `initiates(event, proposition)`; SB B0 "about a description").
   - The outcome is a proposition identified by its A0.1 id [E] (SB "Schema and API"; PLAN Stage A0).
   - Effects are written by `claim_effect` or `account` [E as recorded] (SB D-B-1).
   - `t` judges the claim contents [D] D-EF-6.
2. **Output fields and vocabulary** (one entry per effect claim):

| Field | Type | Values | Label/source |
|---|---|---|---|
| `[i].kind` | str | `initiates`, `terminates` | [E] V02 §3.2 |
| `[i].outcome` | obj | {type, roles, params} | [E] SB "Schema and API" ("each claimed effect") |
| `[i].outcome_id` | id | `p:` + hash | [E] PLAN Stage A0 (proposition ids) |
| `[i].claim` | str | the claims vocabulary | [E] SB B0 (`claim`); IBD §2.4 |
| `[i].claim_status` | Status | common 0.3 | [E] IBD §2.4 |
| `[i].claimed_by`, `[i].attestations` | as in `causes_of` | — | [E] SB B0 |
| `[i].state.accepted_change` | bool | True / False | [E] that the field exists (SB B0: `state.accepted_change`); its rule is [D] D-EF-1 and D-EF-2 |
| `[i].state.before`, `[i].state.after` | Answer | status, holds, support, conflicts | [E] SB B0 ("judged ... before and after the event"); the instants are [D] D-EF-2 |
| `[i].state` | null | when the event has no accepted account | [E] SB D-B-6 (no timing for the perspective) |

3. **Judgement and uncertainty:**
   - [E] The claim and the change are judged separately. An accepted claim does not make a change, and an accepted
     state does not confirm the claim (SB B0; SB reference world, "Effect claims").
   - [E] The states are judged from the outcome's own attestations (SB B0), with the canonical and functional judgement
     (IBD §4; Q-B2).
   - [D] D-EF-1: whether a move into or out of UNKNOWN counts as an accepted change. Q-B1.2 calls it a judgement
     transition in `changes` (SB "The changes contract"), but `effects_of` counts it as accepted.
   - [D] D-EF-2: the sampling instants and delayed effects.
   - [D] D-EF-5: there is no occurrence-status check.
4. **Visibility:**
   - [E] Context ⟨w, p, τ⟩ as in common 0.2. Illustration: the technician's own view of the vibration claim (SB "Tests").
   - [E] The event's times come only from an accepted account (SB D-B-6). Under DI-14, a variant without the account
     gives `state: null` [E] (DI-14).
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
| conflicting (state) | `[i].state.<side>.conflicts`, `[i].state.<side>.constraint_support[].support` | that side is DISPUTED | [E] Q-B2; DI-19; common 0.4 P-1 |
| alternative | `[i].attestations[acceptance≠accepted]`; `[i].state.<side>.alternatives` | any | [E] V02 §6.2 |
| not reported | the event's account attestation (it gives the times) | — | [D] D-EF-3 |

   - [E] The claim evidence and the state evidence never support each other (SB B0).
   - [E] A denial of the same effect claim is conflicting only for the claim judgement.
   - [P] P-EF-1: another event's claim about the same outcome is a different content, not a rival, and is not
     reported. No design text makes claims by different events compete.
7. **Derivations:** none presented [E] (DI-7). `accepted_change` is a comparison of two judged answers, not a recorded
   derivation [E] (E2DEC §4).
8. **Refusals:** none documented for the reader. The `claim_effect` writer checks (kind, proposition ids) exist in code
   only [D] D-EF-7.
9. **Limitations and gaps:**
   - GAP-HARNESS-2, GAP-MULTI-2 (the instants), GAP-CAUSE-3 [E] (E2D §4; INV §6, §4).
   - DI-20 (performance) [E].

**Local items:**
- D-EF-1: Q-B1.2 says moving into or out of UNKNOWN is "never presented as physical change" (SB "The changes
  contract"). `accepted_change` is True for UNKNOWN → held (DYN `effects_of`; recorded output
  dynamics-output.md Q2, bearing-3). The design does not rule whether Q-B1 binds `effects_of`.
- D-EF-2: the states are sampled at start earliest − 1 µs and at end latest only (DYN `effects_of`; INV GAP-MULTI-2).
  A delayed effect, which Q-B1 probe case 6 allows (SB), gives False.
- D-EF-3: the account behind the times is the lowest-id usable account, and it is not reported (DYN `interval`). SB
  D-B-6 requires only that it be accepted.
- D-EF-4: the docstring lists five claim labels; IBD §2.4 has the full vocabulary.
- D-EF-5: no `occurrence_status` or `applies` is given. SB Occ-2 is worded generally, but the LABS-1.011 amendment
  names `causes_of` only.
- D-EF-6: `t` judges only the claims; the states use the event's own times (DYN `effects_of`). SB "Schema and API"
  does not define `t`.
- D-EF-7: the `claim_effect` refusals exist in code only (DYN `claim_effect`).
- P-EF-1: claims by other events about the same outcome are neither rivals nor reported.

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
| `content` | obj | {type, roles} | [D] docstring only |
| `holds` | Answer | status, holds, support, conflicts, constraint_support, alternatives | [E] SB "Schema and API" ("the judged state"); IBD §3 (holds is the record's projection); DI-19 |
| `initiated_by[i].event` | id | an event description claimed to initiate the content | [E] SB "Schema and API" |
| `initiated_by[i].claim`, `.claim_status`, `.claimed_by` | str / Status / [str] | the claims vocabulary | [E] SB B0 |
| `initiated_by[i].occurrences` | [id] | occurrences the description is accepted as describing | [E] SB "Schema and API" ("on the occurrences it is accepted as describing", docstring); PLAN §9.3 |
| `initiated_by[i].start`, `.end` | Window | the accepted occurrence interval | [E] SB B-time and D-B-6 |
| `initiated_by[i].causes[j]` | `causes_of` entry | as in `causes_of` | [E] SB "Schema and API" ("their causal claims") |
| `initiated_by[i]` initiating-claim attestations | — | **absent** | required [E] by SB B0 ("every claim lists its attestations"); missing: [D] D-EX-4 |

3. **Judgement and uncertainty:**
   - [E] `holds` is the canonical judgement. It may be INFERRED by functional exclusivity (IBD §2.4 addendum, R3).
   - [E] Causes follow the `causes_of` contract: lifting, F-B1, U-2, `applies`.
   - [E] An explanation is only what was asserted and accepted. Order or proximity never adds one (PLAN §9.3; SB
     Q-B1.4).
   - [D] Which initiators are included:
     - D-EX-1: accepted claims only, or claims of any judgement;
     - D-EX-2: the "ended by t" filter vs the B-time rule;
     - D-EX-3: initiators with no accepted account.
   - [D] D-EX-5: initiators are listed even when the content does not hold at t.
4. **Visibility:**
   - [E] Context ⟨w, p, τ, t⟩.
   - [E] The initiators' times come only from accepted accounts (SB D-B-6).
   - [E] Occurrence statuses are not checked here; X4 composes `occurrence_status` (E2D §3.6).
5. **Ordering and multiplicity:**
   - `initiated_by` and `causes` are multisets (common 0.9).
   - [D] D-EX-6: within one initiator, a cause appears once per (cause, effect). Which variant is kept (and so its
     `lifted` flag) depends on call order.
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `holds.support` | `holds.status` is not DISPUTED | [E] IBD §2.2; SB "Schema and API" |
| conflicting | `holds.conflicts`, `holds.constraint_support[].support` | `holds.status = DISPUTED` | [E] DI-19; common 0.4 P-1 |
| alternative | `holds.alternatives` | any | [E] V02 §6.2 |
| supporting | `initiated_by[i].causes[j].attestations[acceptance=accepted, polarity=true].attestation` | as in the `causes_of` table (`judgement = accepted`, `applies = true`, P-CO-1) | [E] SB B0; [P] P-CO-1 |
| conflicting / alternative | `initiated_by[i].causes[j].attestations` | as in the `causes_of` table | [E] |
| not reported | the initiating `initiates` claims' attestations, and each initiator's account attestation | — | [D] D-EX-4: required by SB B0, missing |

   - **Citable today:** `holds.support` (with conflicts and constraint support when DISPUTED), and the attestations of
     the causal claims under `initiated_by[i].causes[j]`.
   - **Not yet requirable:** until the owner rules on D-EX-4, no question may require (in `required_evidence`) or
     score the attestations of the initiating claims, or the account attestation of an initiator. The requirement
     itself is not weakened: D-EX-4 stays open as a potential gap.
   - Until D-EX-1 to D-EX-3, D-EX-5 and D-EX-6 are ruled, no question may depend on:
     - whether an unaccepted initiator is listed;
     - an initiator whose account is missing or which has not ended by t;
     - a cause's `lifted` flag inside `explain`.
7. **Derivations:** none presented [E] (DI-7; E2DEC §4). `explain` is a fixed composition (holds → initiating claims →
   `causes_of`; INV §6), not a derivation.
8. **Refusals:**

| Name | Condition | Exception / message | Established? | Source |
|---|---|---|---|---|
| unknown-role | `roles` names a role the type does not relate (core names, inherited ones included) | `UnknownRoleError` (a `ValueError`) naming the type, the unknown names and the valid ones | yes | R2 ("Readers affected: ... explain (roles)"), approved LABS-1.053; HR §9 |

9. **Limitations and gaps:**
   - One step only: GAP-CAUSE-1 [E] (SB "Deferred capabilities").
   - GAP-MULTI-4 and GAP-MULTI-6 [E] (INV §6).

**Local items:**
- D-EX-1: the design says "its **accepted** initiating events" (SB "Schema and API"). The docstring says "with each
  claim's judgement", and the code includes claims of any judgement (DYN `explain`).
- D-EX-2: the code uses "ended by t" (`end.latest ≤ t`; DYN `explain`), a rule in no decision. SB mentions it only in
  a performance note ("Obvious repeated retrieval"). The approved timing rule is SB B-time.
- D-EX-3: an initiator with no accepted account is dropped (DYN `explain`). SB B-time keeps an explanation whose time
  is unavailable, as `timing: "unresolved"`.
- D-EX-4: SB B0 requires every claim to list its attestations. `initiated_by` gives only claim, claim_status and
  claimed_by (DYN `_events_claiming`; raised in HR §5.1). This is a potential gap; the contract is not weakened.
- D-EX-5: no check that the content holds (DYN `explain`). The design is silent; E2D C4 presupposes it holds.
- D-EX-6: causes are gathered from the event and then its occurrences, deduplicated with the first kept and not
  re-sorted (DYN `explain`). A direct occurrence-level claim can show `lifted` (dynamics-output.md Q5).

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
   - t1 ≥ t2 is unspecified [D] D-CH-8.
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
| `began`, `ended` | [view] | views over the transitions | [E]; extra fields in their entries are [D] D-CH-6 |
| `unchanged` | int | — | [E] |

3. **Judgement and uncertainty:**
   - [E] **Categories** (Q-B1.2):
     - world-state is between two accepted states (a value, or an accepted "does not hold");
     - judgement is into or out of UNKNOWN or DISPUTED, never presented as physical change.
   - [E] **Windows** (Q-B1.1):
     - accepted A, then only UNKNOWN, then accepted B ≠ A is one world-state transition whose window is the gap;
     - no instant is invented;
     - certain if the window lies inside the interval, possible if it overlaps, omitted if outside.
     - The design does not cover A → UNKNOWN → A, or gaps through DISPUTED: [D] D-CH-4.
   - [E] **Q-B2:** one functional-conflict judgement, the same as `value_at`, rivals included. Attested constraints
     are applied at each boundary (IB "Answer changes").
   - [E] **C-6:** a slot's status rests on the values held only (ICD §3.3; IC "Readers").
   - [E] **Explanations** (Q-B1.4):
     - only accepted initiates or terminates claims about a content that began or ended in the transition count;
     - one temporal constraint applies: an effect cannot precede its event's start (B-time);
     - proximity is never evidence;
     - a claim that fits several activations on the whole timeline is `ambiguous` on each and never chosen;
     - unresolved times are kept with `timing: unresolved` (B-time). The boundary is [D] D-CH-3.
   - [E] The SB probe cases 1-6 are the worked examples.
4. **Visibility:**
   - [E] Event time, transition valid time, knowledge time and explanations are kept apart (SB Q-B1, the requested
     contract).
   - [E] Judged for world, perspective and `as_of`.
   - [E] An event outside the interval may explain a transition inside it, and is never itself an in-period change.
5. **Ordering and multiplicity:**
   - `transitions`, `explanations`, `began` and `ended` are multisets (common 0.9). The implementation's sorts are [D]
     D-CH-6.
   - [E] One claim may be listed under several transitions (`ambiguous`), and one event may be listed twice on one
     transition (initiates and terminates).
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting (required, both sides) | `transitions[i].before.support` **and** `transitions[i].after.support` | `transitions[i].category = world-state` | [E] Q-B1.2 ("between two accepted states") with the per-side `support` of the contract schema; known gap [D] D-CH-1 |
| supporting | `transitions[i].<side>.support` for each side whose status is not UNKNOWN or DISPUTED | `category = judgement` | [E] SB contract |
| conflicting | `transitions[i].<side>.support` and `.conflicts` | that side's status is DISPUTED | [E] Q-B2 ("its own support and the rival attestations"); common 0.4 P-1 |
| not cited | `transitions[i].explanations[k]` | any | [E] SB B0: an asserted effect is not evidence of the change |
| not reported | the attestations of the explanation claims | — | [D] D-CH-2 |

   - Where the answer establishes a transition (category `world-state`), evidence from **both** sides is required
     supporting evidence. `before.support` and `after.support` must each be non-empty and cited.
   - An answer with an empty side fails recall. This is not excused: questions that exercise a holds → does-not-hold
     content transition carry D-CH-1 in their adjudication notes.
7. **Derivations:** none presented [E] (DI-7). Values excluded by functional exclusivity are a declared query-time rule
   (V02 §5.6, INFERRED), not a recorded derivation.
8. **Refusals:** none documented.
9. **Limitations and gaps:**
   - GAP-CAUSE-1 to -4; GAP-MULTI-2 [E].
   - DI-9 and DI-20 to DI-22 (performance) [E].
   - Stale design text: [D] D-CH-7.

**Local items:**
- D-CH-1: Q-B1.2 and the per-side `support` in the contract schema (SB) imply an accepted "does not hold" side cites
  its deciding attestations. The code builds `support` only from contents judged true or disputed (DYN `changes`,
  `state_at`), so that side's `support` is empty while its status rests on the denial.
- D-CH-2: SB B0 says every claim lists its attestations. The Q-B1 schema (SB) and the code give explanations
  claim, claim_status and claimed_by only. The two design texts differ; the owner must rule.
- D-CH-3: SB B-time says a start window that **overlaps** the transition window gives `unresolved`. The code gives
  `consistent` when `start.latest ≤ window earliest`, so touching windows are consistent (DYN `changes`, `timing`).
- D-CH-4: A → UNKNOWN → A, and gaps through DISPUTED, are not covered by Q-B1.1. The code reports two judgement
  transitions and never merges a DISPUTED gap.
- D-CH-5: explanation claims are judged at t2 (DYN `changes`). Claims are timeless (D-B-2); the design specifies no
  valid time for judging them.
- D-CH-6: the extra fields in `began`/`ended` entries (status, stated_by, one-side support, outcome_id, category,
  within, window, claimed_events), and the sorts of transitions and explanations, are code only.
- D-CH-7: SB "Remaining limitations" ("`changes` lists every claimed event ... needs a ruling") and SB "Schema and
  API" describe the pre-Q-B1 behaviour, which Q-B1.4 superseded.
- D-CH-8: no design text covers t1 ≥ t2.
- D-CH-9: explanations carry no occurrence status or `applies`. Q-B1 and B-time do not cover it; SB Occ-2 is worded
  generally.

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
| `[i].judgement` | str | `established`, `disputed` | [E] IB "What changed" (each step gains judgement and status); DI-1 |
| `[i].status` | Status | DISPUTED for a dispute, otherwise the support status | [E] IBD §4; IBD §2.4 |
| `[i].support` | [id] | the part-of content's deciding attestations | [E] IBD §2.2 |
| `[i].start`, `[i].end` | Window or null | an accepted account's interval | [E] SB D-B-6; the choice among several accounts is [D] D-PS-3 |
| `[i].descriptions` | [id] | descriptions the perspective accepts as describing the step | [E] V02 §3.2 ("Queried"); [D] D-PS-4 (DI-14) |
| `[i].kinds`, `[i].actors` | [str] | from accepted accounts | [D] docstring only (SB D-B-4: actions are classifications, with no capacity check) |

3. **Judgement and uncertainty:**
   - [E] Membership is judged by the canonical record of part-of at t.
   - [E] Disputed steps are listed and flagged, never dropped (DI-1; IBD §4).
   - [D] D-PS-5: pending memberships are not listed.
   - [E] Processes are not modelled as ongoing (SB "Deferred capabilities"; GAP-PROC-5).
4. **Visibility:**
   - [E] Context ⟨w, p, τ, t⟩.
   - [E] Intervals come only from accepted accounts (D-B-6).
   - [E] DI-14: in a variant, a description is listed without its account (no flag).
5. **Ordering and multiplicity:**
   - [E] The steps are ordered by interval start (E2D §2, the P row).
   - [D] D-PS-1: which bound of the start window, and how ties are broken.
   - [D] D-PS-2: where undated steps go.
   - [P] P-PS-1: the list order is presentation only and asserts no succession. Succession is asked with `before` (SB
     B0, the succession-vs-causation row; E2D P4). P4 questions compare steps with `before`, never by list position.
   - Steps are otherwise a multiset with one entry per part-of content and part.
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `[i].support` | `[i].judgement = established` | [E] IBD §2.2; HR §5.1 |
| conflicting | `[i].support` | `[i].judgement = disputed` (both sides cited, DI-1) | [E] DI-1 ("citing both sides"); the role is [P] by common 0.4 P-1 |
| not reported | the account attestations behind `start`/`end` | — | [D] D-PS-3 |

7. **Derivations:** none presented [E]. The order is not a derivation, and no order relation exists (GAP-PROC-1).
8. **Refusals:** none documented.
9. **Limitations and gaps:**
   - GAP-PROC-1 to -7 [E] (INV §5; E2D §4).
   - DI-14 and GAP-MULTI-8 [E].

**Local items:**
- D-PS-1: E2D gives "ordered by interval start". The code uses `start.earliest` and then the occurrence id, ignoring
  `start.latest` (DYN `process_steps`).
- D-PS-2: INV §5 says undated steps go last. The code gives them the latest dated start as their key, so they can
  precede that step (DYN `process_steps`). No design text covers this.
- D-PS-3: for a step with several descriptions, the code uses the earliest-starting description's interval and does
  not report the account attestation (DYN `process_steps`). No design text covers this.
- D-PS-4: DI-14 (open). Descriptions with no account in the variant are listed without a flag.
- D-PS-5: through `facts_about`, only established and disputed memberships are listed. IBD §4 is silent on pending
  ones.
- P-PS-1: list order asserts no succession.

---

### `before(world, a, b, as_of=None, perspective=SYSTEM)`
**Serves:**
- P3 (H) (E2D §3.5);
- gap probes GAP-PROC-1 and GAP-PROC-4.

1. **Inputs and conditions:**
   - `a` and `b` are event descriptions [E] (SB B0: "`before()` compares intervals").
   - P3's steps (occurrences) are mapped to descriptions by the question's plan [D] D-BE-3.
   - Context as in common 0.2 (no `t`: the intervals are valid times).
2. **Output fields and vocabulary:**

| Field | Type | Values | Label/source |
|---|---|---|---|
| (the answer) | bool or null | True: a certainly ends before b starts; False: b certainly before a; null: they overlap or cannot be ordered | [E] SB B0 ("certainly before, or None if they overlap"); False is [D] (docstring) |

3. **Judgement and uncertainty:**
   - [E] Judged from the windows, never a guess. Succession says nothing about causation (SB B0; V02 §3.2).
   - [D] D-BE-2: whether touching intervals count as "before".
   - [D] D-BE-4: clocks.
4. **Visibility:** [E] only accounts the perspective can use (SB D-B-6). There is no account (and so null) for an
   unaccepted account, or for an account not inherited (DI-14).
5. **Ordering and multiplicity:** not applicable. When there are several accounts, see `interval`, D-IV-1.
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| not cited | — | any | [P] P-BE-1 (HR §5.1: "nothing"); no design text gives an evidence rule |

7. **Derivations:** none presented [E].
8. **Refusals:** none documented.
9. **Limitations and gaps:** GAP-PROC-1, GAP-PROC-4, GAP-MULTI-2 [E].

**Local items:**
- D-BE-1: the `False` branch is docstring only. SB B0 states True and None only.
- D-BE-2: the code counts `a.end.latest ≤ b.start.earliest` as before, including touching intervals (semantics
  `certainly_before`). SB B0 does not rule on touching.
- D-BE-3: E2D P3 is phrased with steps (occurrences). The reader takes descriptions, and an occurrence gives null (DYN
  `before`).
- D-BE-4: V02 §4.5 says times on different clocks compare only through an accepted alignment, otherwise UNKNOWN.
  `before` has no clock handling.
- P-BE-1: `before` cites no evidence. A P3 question's evidence comes from `interval` in its plan.

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
   §6.2); otherwise null (DI-14).
5. **Ordering and multiplicity:** one result. [D] D-IV-1: the choice among several usable accounts.
6. **Evidence:**

| Role | Where in the answer | When | Label/source |
|---|---|---|---|
| supporting | `attestation` | the answer is not null | [P] P-IV-1 (HR §5.1: "the account attestation it uses"); consistent with SB D-B-6 |

7. **Derivations:** none presented [E].
8. **Refusals:** none documented.
9. **Limitations and gaps:** GAP-PROC-4 (no duration), GAP-MULTI-2 [E].

**Local items:**
- D-IV-1: SB D-B-6 says only "an account the perspective can use". The code returns the lowest-id usable attestation
  (DYN `interval`), which does not depend on time or world depth, and does not report the others.
- P-IV-1: the account attestation used is the supporting evidence.

