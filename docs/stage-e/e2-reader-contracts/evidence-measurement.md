<!-- Evidence record for Part C of benchmark/e2/spec/reader-contracts.md (LABS-1.062): the specification evidence gathered before drafting, with full citations. Supplementary to the contracts. -->

# Specification evidence for the measurement reader contracts

Readers covered: `WorldModel.measurements`, `WorldModel.compare_measurements`, `WorldModel.convert`
(`src/worldmodel/qualities.py`), and `laboratory.measurement_calibration`, `laboratory.calibration_status`
(`src/worldmodel/laboratory.py`).

Repository: `the repository` (read only; nothing run). All paths
below are relative to it.

Tags:
- **[ESTABLISHED]**: stated in an approved design document or decision.
- **[INFERRED]**: my reading, or supported only by a docstring or the implementation.

Line numbers are those of the files at the time of reading.

## 0. Sources and their standing

| Source | Standing |
|---|---|
| `docs/architecture/world-ontology-v0.2.md` (v0.2) | frozen baseline 2026-11-09 (§12); §3.3 incorporates clarification B (line 4) |
| `docs/plans/core-0.4-plan.md` (plan) | approved plan; Stage C row 75-79; §9.2 DX-2 amended (249-266) |
| `docs/core-0.4/stage-c.md` | "Stage C ontology and API approved (LABS-1.020)" (line 5); decisions D-C-1..D-C-8 (lines 30-39) |
| `docs/core-0.4/stage-d-review.md` | Stage D review; D-D-7, D-D-8 (lines 245-246), gap G6 (line 107) |
| `docs/core-0.4/stage-d3-design.md` | "approved (LABS-1.028) and implemented" (line 3); D-D3-1..6 (lines 99-104) |
| `docs/core-0.4/stage-d3.md` | implementation report of the approved design; §6a lists the deviations from the design (182-190) |
| `docs/core-0.4/pre-e-increment-b-design.md` | approved with Q1-Q6 (LABS-1.038) (line 3); judgement and label vocabulary §2.4 |
| `docs/core-0.4/pre-e-increment-c-design.md` | approved at b1c45c4 (LABS-1.040, C-1..C-6) (line 3); rule Q §3.1 |
| `docs/core-0.4/pre-e-increment-c.md` | implementation report; DI-6 "corrected in increment C, approved and merged (LABS-1.041)" (`deferred-issues.md` line 45) |
| `docs/core-0.4/deferred-issues.md` | DI register |
| `docs/stage-e/stage-e2-evaluation-design.md` | E2 design; E2-D3 (contracts from design documents) approved (`stage-e2-decisions.md` line 42) |
| `docs/stage-e/stage-e-entry/e2-capability-inventory.md` | read-only inventory (GAP-MEAS-1..11); describes the implementation, not design |
| `docs/stage-e/stage-e2-harness-review.md` | harness review (LABS-1.061/1.062); §5.1 proposes evidence extractors that the contracts "must confirm" |
| `benchmark/e1/TEMPLATES.md`, `CLARIFICATIONS.md` | E1 scoring vocabulary and clarifications |
| `benchmark/e2/spec/reader-docs.md` | docstrings only: "not the E2 reader contracts" (line 3) |

Allowed gold sources for E2 measurement questions are `stage-c.md` and `stage-d3-design.md`, plus E1's sources
(`stage-e2-evaluation-design.md` §5.1, lines 166-171) **[ESTABLISHED]**. Where a docstring and its design document
differ, the contract must record the difference and stop for the owner's decision (§5.2, lines 177-179)
**[ESTABLISHED]**.

### Shared background (applies to all five readers)

- **The three layers of a measurement.** A measurement is three things: the activity (an event description
  classified `measurement`: operator as actor, bearer as patient, instrument as instrument), the result record (an
  information object with raw value, raw unit, u, k, conditions and calibration reference) and the reported content
  (a `has-quality` range in canonical SI, attested with basis observation). They are linked by `produced` and
  `reports`. Sources: plan §9.2 table (lines 254-259); stage-c C0 table (lines 11-19). **[ESTABLISHED]**
- **Measurement, observation, statement and acceptance stay separate** (stage-c lines 23-27) **[ESTABLISHED]**:
  - a measurement has a result record and an activity;
  - a statement with no result record (a specification) is listed apart and never compared with measurements;
  - acceptance is per perspective.
- **Evidence link.** Each measurement-backed attestation names its own records through the structural
  `rests-on(attestation, record)`. Nothing is matched by source, time or content. It is immutable, has no one-to-one
  constraint and records dependency, not truth. Sources: D-C-2 (stage-c line 33); correction section (lines 80-106);
  "As implemented" (lines 108-133). **[ESTABLISHED]**
- **Acceptance vocabulary.**
  - v0.2 §5.6 (line 472) gives accepted / rejected / unreviewed / superseded. **[ESTABLISHED]**
  - Increment B adds `retracted` to the per-claim acceptance state: "accepted, unreviewed, rejected, retracted,
    superseded" (`pre-e-increment-b-design.md` §2.2 line 51; `pre-e-increment-b.md` line 18). **[ESTABLISHED]**
- **Status vocabulary.**
  - ASSERTED, STIPULATED, INFERRED, DISPUTED, UNKNOWN, NOT_YET_KNOWN (`benchmark/e1/TEMPLATES.md` line 17).
    **[ESTABLISHED]**
  - Observations are reported ASSERTED (Core 0.3 D1; TEMPLATES.md line 18). v0.2's OBSERVED status is not
    produced, because observations are deferred (v0.2 §12 line 804; plan §9.2 line 250). **[ESTABLISHED]**
  - Mixed support: STIPULATED > ASSERTED > INFERRED (D4; TEMPLATES.md line 19). **[ESTABLISHED]**
- **Context ⟨w, p, τ, t⟩ and visibility.**
  - Every question has a context ⟨w, p, τ, t⟩ (v0.2 §6.1 lines 493-504). **[ESTABLISHED]**
  - Visibility: own and accepted attestations, plus stipulations; variants inherit the base at min(τ, κ) and only
    before β. Unaccepted attestations by others are **alternatives, never support** (v0.2 §6.2 lines 506-515).
    **[ESTABLISHED]**
  - Later corrections in the base never reach a variant (v0.2 §6.3). **[ESTABLISHED]**

---

## 1. `WorldModel.measurements(world, bearer, quality, t=None, as_of=None, perspective=SYSTEM)`

### 1.1 Supported question classes and input conditions
- **What it answers:** every stated value of a quality of a bearer, with judgement and provenance, of kind
  measurement or statement. Source: stage-c C1 API (line 48), "`measurements`: every stated value, with judgement and
  provenance, kind measurement or statement". **[ESTABLISHED]**
- **E2 classes.** **[ESTABLISHED]** (E2 design, §3.3 lines 88 and 91):
  - M1: values stated, by whom, with which instrument, uncertainty and conditions;
  - M4: a corrected or superseded value, which is current and which is history.
- **Quality identity.** A quality is identified by the slot (bearer, quality kind). No quality instance exists:
  instances are deferred (v0.2 clarification C, lines 230-240; D-D-8, stage-d-review line 246). Measurements are
  therefore asked by (bearer, quality kind). **[ESTABLISHED]**
- **`t` optional.** "If t is given, only attestations that hold at t" (docstring, qualities.py 198-199;
  reader-docs 147-148). No design text found. **[INFERRED]**
- **Inputs:** the bearer and quality ids. No refusal is documented for unknown ids: the implementation returns `[]`.
  **[INFERRED]**

### 1.2 Output fields and permitted vocabulary
- **Per value:** the attestation's acceptance for the perspective, from accepted, unreviewed, rejected, retracted,
  superseded.
  - Design vocabulary: see §0. **[ESTABLISHED]**
  - The per-reader list appears in the docstring (qualities.py 194-195) and in the inventory (line 32).
    **[INFERRED]**
- **`kind`.**
  - "measurement" when the value rests on result records (rests-on); otherwise "statement". **[ESTABLISHED]**:
    stage-c lines 24-26 and 48; D-C-2 "Provenance read" (lines 89-91).
  - A specification (design value) is a statement: stage-c line 26; Stage C reference world "a specification"
    (line 54); stage-d-review line 59, "the design value is a statement". **[ESTABLISHED]**
- **Range.** `range` (lower, upper) in the dimension's SI unit, with `unit` (the SI unit) and `coverage_level`.
  - The reported content is the range [v − ku, v + ku] in SI with its coverage level: v0.2 §3.3 table (lines 222-228);
    D-C-1 (stage-c line 32); plan §9.2 (line 258). **[ESTABLISHED]**
- **Per record.** Raw value, raw unit (`expressed-in`), standard uncertainty, coverage factor, conditions and
  calibration reference: D-C-1 (stage-c line 32); v0.2 clarification B "Faithful preservation" (lines 244-246).
  **[ESTABLISHED]**
- **Per activity.** Start, end, operator, instrument and occurrences: stage-c "Provenance read" (line 89, attestation
  → rests-on → record → produced → activity); "Judged parts stay judged" (lines 117-119). **[ESTABLISHED]**
  - The field names (`activities`, `operator`, `instrument`, `occurrences`) are implementation only. **[INFERRED]**
- **Per record, `report`:** "whether the `reports` claim is accepted" (stage-c line 117). **[ESTABLISHED]**
  - Its value is a `claim_label` string, or "none" (qualities.py 214-216). **[INFERRED]**
- **Implementation-only fields:** `attester`, `basis`, `usable`, `valid` (start and end Windows), `content`
  (qualities.py 229-233). **[INFERRED]**
  - The design supports including the basis: "values without one are statements, with their basis" is docstring
    only; v0.2 §5.6 layer 1 makes basis an evidence property (line 471). **[INFERRED]**
  - `usable` = accepted, not superseded for the perspective, supporting stance, **and polarity true**
    (qualities.py 232; semantics.py 115-118). **[INFERRED]**
- **No answer status.** "acceptance vocabulary (no `Status`)" (inventory line 170). `measurements` is a collection:
  "each content's own record, unchanged" (`pre-e-increment-c-design.md` §4 table line 122). Rule C does not apply to
  it; nothing folds a status. **[ESTABLISHED]** for "collection, no folded status".

### 1.3 Judgement and uncertainty semantics
- **The range.** The range is [v − ku, v + ku], converted to SI. The coverage level is stored on the content. The
  measurement keeps the raw value, unit, u and k. Sources: v0.2 §3.3 lines 223-228; plan §9.2 line 261 (measurement
  uncertainty is on the result record and fixes the range; credence is on attestations). **[ESTABLISHED]**
- **Two kinds of uncertainty stay separate.** A doubtful calibration lowers credence or makes the attestation
  `doubts`; it does not widen the range (v0.2 lines 259-261; plan acceptance criterion C, line 176). **[ESTABLISHED]**
- **Coverage level from k.** The coverage level is computed as erf(k/√2) (normal assumption; k = 2 gives 0.9545,
  qualities.py 30-32).
  - v0.2 uses "95 %" for k = 2 (lines 225, 377) and "k = 3 (99.7 %)" (line 593). **[ESTABLISHED]** that coverage
    level is a function of k.
  - The exact formula is implementation only. **[INFERRED]**
- **Conditions are exact text** (D-C-7, stage-c line 38). **[ESTABLISHED]**
  - Sorted and de-duplicated on write (qualities.py 137). **[INFERRED]**
- **Never combined.** Nothing is overwritten by a combined estimate (v0.2 line 246). **[ESTABLISHED]**

### 1.4 Temporal, perspective and world visibility
- **Acceptance and supersession are per perspective (D14).**
  - A perspective that has not accepted a correction keeps the original attestation and record. One that accepted it
    sees the new ones. Source: stage-c "Correction" and "Supersession" (lines 92-96). **[ESTABLISHED]**
  - A source's revision is not another perspective's acceptance: v0.2 §6.2; `docs/core-0.3/supersession-and-endings.md`.
    **[ESTABLISHED]**
- **`as_of` (knowledge time).** A measurement's attestations share one transaction time, so an `as_of` query "sees all
  of the measurement or none of it" (D-C-8, stage-c lines 39 and 148-149; test described at 172-173). **[ESTABLISHED]**
- **Judged and structural parts.** **[ESTABLISHED]** (stage-c lines 117-119; line 99, "The link is a fact about an
  attestation ... so it is not judged"):
  - judged (depend on the perspective): the record's `report` label, and the activity's times (from its account);
  - not judged: the rests-on link, the record's values and conditions, and the activity's operator and instrument.
- **Hypothetical worlds.** A variant's own measurements rest on their records; inherited attestations bring their
  links; snapshots filter attestations and the links follow (stage-c lines 102-103). **[ESTABLISHED]**
- **Valid time of the content.**
  - Plan §9.2 (line 258) gives "the quality's valid time" for the reported content, and "occurrence interval" for
    the activity. **[ESTABLISHED]**
  - In the implementation, the content is attested over the activity's interval, or from its start until superseded
    when `persists` (measure docstring, qualities.py 116-117). **[INFERRED]**
- **The `t` filter.**
  - Implemented as `verdict(a, t) is True` (qualities.py 207-208), so it filters on the attestation's own interval
    and polarity, not on acceptance. **[INFERRED]**
  - Side effects: denials are always removed when t is given, and unaccepted attestations that hold at t remain.
    **[INFERRED]**

### 1.5 Ordering and multiplicity
- **No design text on ordering.**
  - The implementation sorts values by attestation id (qualities.py 203). Ids are random, so the order carries no
    meaning: stage-c line 238, "random ids (and so the order within pairs)". **[INFERRED]**
  - Records are sorted by record id (`evidence_of`, qualities.py 170). **[INFERRED]**
- **One entry per attestation**, not per content:
  - two attestations of one content are two entries (stage-c D-C-2 probe case 1, lines 63 and 69-70);
  - an attestation may rest on several records, and a record may support several attestations (stage-c
    lines 109-111).

  **[ESTABLISHED]**

### 1.6 Supporting, conflicting and alternative evidence
- **Usable versus alternatives.** Only usable attestations can support. Unaccepted attestations by others are
  alternatives (v0.2 §6.2 line 515). **[ESTABLISHED]**
- **Harness proposal (not yet a decision).** "`measurements`: the attestation of each **usable** value"
  (harness review §5.1 line 152), proposed for the contracts to confirm (line 140). **[INFERRED]**
  - The implementation's extractor `ev_measurements` (evaluation/e2/readers.py 163-164) counts usable
    **statements** as well as measurements. The contract must decide whether a usable specification statement is
    support for "what values were stated" (M1). **[INFERRED]**
- **Not citable as support.** **[INFERRED]**
  - Result-record ids and activity ids are not attestations.
  - The `produced` and `reports` attestation ids are not returned: only the `report` label is.
  - The activity's account attestation ids are not returned either.

### 1.7 Derivation rules and admissible premises
- **No derivation record.** A measurement-backed content has basis observation and rests on its records. `rests-on`
  gives premises in effect but no rule. DI-7: no derivation record exists, and basis inference gives INFERRED without
  one (`deferred-issues.md` DI-7, lines 219-249). **[ESTABLISHED]**
- **Conversion to SI is not an inference.** Conversion to SI on write is part of producing the reported content
  ("conversions are derived; the reported content is in SI", D-C-1). The content's basis stays observation.
  **[ESTABLISHED]**: D-C-1; plan §9.2 line 258.
- **A record alone is not a measurement.** "A record without an attestation is not reported as a measurement.
  `reports(result, content)` alone does not create one" (stage-c Remaining limitations, item 4, lines 247-248).
  **[ESTABLISHED]**

### 1.8 Documented refusals and unsupported operations
- **Refusals:** none in design for the reader. **[ESTABLISHED]** (absence)
- **Unsupported operations:** **[ESTABLISHED]** (stage-c lines 243-244; GAP-MEAS-6 and -7)
  - "latest/current value", trend or time series (GAP-MEAS-7);
  - quality instances (D-D-8);
  - batching (D-C-6).

### 1.9 Known limitations and gaps
- **GAP-MEAS-6:** `has-quality` is not a functional slot.
- **GAP-MEAS-7:** no latest-value or trend reader.
- **GAP-MEAS-8:** N+1 reads (D-C-6).
- **GAP-MEAS-10:** rests-on records support only; there is no "undermines" link (G-3).
- **GAP-MEAS-11:** DI-7, no derivation record.

Source: inventory lines 196-207.

---

## 2. `WorldModel.compare_measurements(world, bearer, quality, t=None, as_of=None, perspective=SYSTEM)`

### 2.1 Supported question classes and input conditions
- **E2 classes.** **[ESTABLISHED]** (E2 design lines 89-90):
  - M2: do two measurements agree within their uncertainties;
  - M3: different conditions or coverage factors, are they comparable.
- **What it compares.** It compares the measurements the perspective accepts (v0.2 clarification B; stage-c C0
  "comparability" line 19; C1 API line 49). **[ESTABLISHED]**
  - In v0.2, the comparison applies to "two `has-quality` contents with the same bearer and kind, at overlapping
    valid times" (lines 247-248). **[ESTABLISHED]**

### 2.2 Output fields and permitted vocabulary
- **Pair relations.** "possibly compatible", "incompatible" and "incomparable", each with its reason (v0.2 table
  lines 250-254; DR-07 line 713; stage-c line 19). **[ESTABLISHED]**
  - **possibly compatible:** comparable, and the ranges overlap. "One underlying value could explain both. It is not
    agreement." Both ranges are given, with no intersection. **[ESTABLISHED]**
  - **incompatible:** comparable, and the ranges are disjoint. "incompatible at the stated coverage", giving
    DISPUTED and citing both. **[ESTABLISHED]**
  - **incomparable:** "different coverage levels, units without an accepted conversion, different measurement
    conditions or calibration states the profile says matter, or non-overlapping valid times for a changing
    quantity". Both ranges are given, with the reason. **[ESTABLISHED]**
- **Reason strings** are implementation only (qualities.py 272-287). **[INFERRED]** They are:
  - "different units (no common SI unit)";
  - "different coverage levels (la vs lb)";
  - "different measurement conditions (…)";
  - "valid times do not overlap";
  - `None` for comparable pairs.
- **Output partitions.** `measurements` (usable), `pairs`, `alternatives` (unaccepted measurements) and `statements`
  (listed apart).
  - "Statements (no result record) are listed apart and never compared with measurements" (stage-c line 26).
    **[ESTABLISHED]**
  - "unaccepted measurements are listed as alternatives" is docstring (qualities.py 242), consistent with v0.2 §6.2.
    **[ESTABLISHED]** in principle; the field names are **[INFERRED]**.
- **Status.**
  - DISPUTED if any comparable pair is incompatible (v0.2 table line 253; increment-C inventory line 119: "DISPUTED
    on an incompatible pair, else core rule over the union; already rule Q"). **[ESTABLISHED]**
  - Otherwise, the core rule (`answer_status`) over the union of the usable measurements: observation gives
    ASSERTED, stipulation gives STIPULATED (increment-C design line 28; TEMPLATES line 18). **[ESTABLISHED]**
  - With no usable measurement: UNKNOWN if something is held, NOT_YET_KNOWN if nothing is (D-C-5, stage-c line 36).
    **[ESTABLISHED]**
  - In the implementation, "something" includes statements, alternatives and denials: any entry of `measurements`
    (qualities.py 262). **[INFERRED]**

### 2.3 Judgement and uncertainty semantics
- **Never combined or reconciled.**
  - Combining is "a named, versioned reconciliation policy ... Its result is an INFERRED attestation citing the policy
    and every input" (v0.2 lines 256-258); "no reconciliation without a named policy" (plan acceptance C, line 176).
    **[ESTABLISHED]**
  - No policy exists in the code (GAP-MEAS-4), so no INFERRED estimate is ever produced. **[ESTABLISHED]**
    (inventory line 191; E2 design M8 is a G question, line 95)
- **Overlap.** Closed intervals: `al <= bh and bl <= ah` (qualities.py 255). This matches the plan's TypeQL overlap
  `$la <= $ub; $lb <= $ua` (plan §4 line 166). **[ESTABLISHED]** (plan) / **[INFERRED]** (closed-interval detail)
- **Coverage levels.** Different coverage levels give incomparable. v0.2 C4 (line 593): "m2 at k = 3 (99.7 %) is
  incomparable with m1 at k = 2 unless a policy converts coverage". There is no harmonisation (GAP-MEAS-3).
  **[ESTABLISHED]**
  - The tolerance of 1e-6 is implementation only (qualities.py 27). **[INFERRED]**
- **Conditions.** Compared as exact text; any difference is incomparable (D-C-7, line 38; stage-c limitation 2,
  line 244). **[ESTABLISHED]**
  - The implementation compares the **set** of each attestation's records' sorted condition tuples. Order within one
    record does not matter, and duplicates are dropped (qualities.py 277-280, 137). **[INFERRED]**
  - Comparability reads each attestation's own conditions, "never a merged set" (stage-c lines 97-98). **[ESTABLISHED]**
- **Calibration does not affect comparison.**
  - "calibration states the profile says matter" (v0.2 line 254): no profile declares any. Which conditions or
    calibration states matter is deferred (stage-d-review line 96, Df).
  - Calibration never changes comparison (D-D3-2, stage-d3-design line 100; stage-d3 §3 "Never invalidating",
    lines 111-116: "the 15:00 weighing, on an expired calibration, is still compared").

  **[ESTABLISHED]**
- **Units.**
  - Contents are stored in the dimension's SI unit (D-C-1; C0 line 14), so units differ only across dimensions or
    when the SI unit ids differ. **[ESTABLISHED]**
  - The reason text "no common SI unit" is **[INFERRED]**.
- **Valid times.**
  - "non-overlapping valid times for a changing quantity" (v0.2). **[ESTABLISHED]**
  - The implementation applies the test to every quantity (it has no notion of a "changing" quantity), using windows:
    certainly disjoint if a.end.latest <= b.start.earliest. A missing start or end is unbounded (qualities.py
    281-287). **[INFERRED]**

### 2.4 Temporal, perspective and world visibility
- **The same as `measurements`** (§1.4): the comparison is built on its output (qualities.py 244). **[INFERRED]**
- **Two perspectives give different comparisons.** Stage-c "Disputes" (lines 97-98) and D-3 P2 (stage-d3-design
  line 75, "`compare_measurements` (two perspectives)"). **[ESTABLISHED]**
- **With `t`.** Only attestations whose own interval holds at t are compared. **[INFERRED]** (docstring of
  `measurements`)

### 2.5 Ordering and multiplicity
- **Pairs.** Every unordered pair of usable measurements, once each (i < j over the usable list, sorted by attestation
  id).
  - Which attestation is `a` and which is `b` depends on random ids (stage-c line 238). **[INFERRED]**
  - The pairs are pairs of **attestations**, not contents. Two attestations of one content are a pair: identical
    ranges, so "possibly compatible". **[INFERRED]**
  - v0.2 speaks of pairs of contents (line 247): see Discrepancies.

### 2.6 Supporting, conflicting and alternative evidence
- **DISPUTED cites both sides** (v0.2 line 253). **[ESTABLISHED]**
- **For possibly compatible pairs:** "both ranges, each with its evidence" (v0.2 line 252). **[ESTABLISHED]**
- **Harness proposal.** "the attestations of the compared measurements. **Not cited:** alternatives, statements"
  (harness review line 153). Consistent with v0.2 §6.2 and stage-c line 26. **[INFERRED]** (proposal; it needs the
  owner's approval)
- **No certificate ids.** Calibration never enters comparison, so certificate ids are never cited. **[ESTABLISHED]**
  (D-D3-2)

### 2.7 Derivation rules and admissible premises
- **No derivation.** The relation labels are a query-time comparison, not an attestation. They are never stored
  (v0.2 E9: answer statuses never stored, line 418). **[ESTABLISHED]**
- **INFERRED needs a named policy.** INFERRED would only arise from a named reconciliation policy (v0.2 §5.6
  INFERRED row, line 479), and none exists. **[ESTABLISHED]**

### 2.8 Documented refusals and unsupported operations
- **Refusals:** none for the reader. **[ESTABLISHED]** (absence)
- **Unsupported operations:** **[ESTABLISHED]** (E2 design lines 94-95; inventory 181-191)
  - comparison against a specification, tolerance or pass/fail (M7, GAP-MEAS-1);
  - a best estimate (M8, GAP-MEAS-4);
  - coverage harmonisation (GAP-MEAS-3).

### 2.9 Known limitations and gaps
- GAP-MEAS-1, -2, -3, -4, -6, -8 (inventory lines 181-202).

---

## 3. `WorldModel.convert(value, unit, to=None)`

### 3.1 Supported question classes and input conditions
- **E2 class M5:** "What is 20 °C in kelvin, or 1,500 g in kilograms (same-dimension conversion)?" (E2 design line 92).
  **[ESTABLISHED]**
- **Same dimension only.** The stage-c C1 API (line 45): "`convert` (refused across dimensions)". **[ESTABLISHED]**
- **Default target.** "`to` default: the SI unit" is docstring only (qualities.py 96). **[INFERRED]**

### 3.2 Output fields and permitted vocabulary
- **Output:** a number only. No status, no world, no perspective, no evidence (harness review line 163: "`convert`:
  nothing" cited). **[INFERRED]** (signature and docstring; harness proposal)
- **Why there is no context.** Units are reference systems: abstract entities, timeless in v0.2 (v0.2 §3, lines
  127-128; §8.2 line 672). So no ⟨w, p, τ, t⟩ context applies. **[ESTABLISHED]** for "timeless reference data";
  **[INFERRED]** that convert therefore takes no context.

### 3.3 Judgement and uncertainty semantics
- **Unit model.** A unit owns `dimension`, `si-factor` and `si-offset` (plan Stage C, line 78; stage-c C0 line 14).
  **[ESTABLISHED]**
- **Formula.**
  - si = raw × si_factor + si_offset; result = (si − offset_to) / factor_to. This is in the `define_unit` docstring
    and the code (qualities.py 50, 98-104). **[INFERRED]** (no design text states the formula)
  - It is standard affine conversion, and it is "single-dimension affine" (inventory GAP-MEAS-5).
- **Round trips.** "unit conversion round trips" are an acceptance criterion (plan line 176). **[ESTABLISHED]**
- **Values only.** No uncertainty propagation: convert takes a value, not a range. **[INFERRED]**

### 3.4 Temporal, perspective and world visibility
- None (see 3.2). **[INFERRED]**
- **Unit definitions are not attested.** They are read straight from the database, so `as_of` cannot hide a unit
  defined later. **[INFERRED]** (qualities.py 66-74)

### 3.5 Ordering and multiplicity
- Not applicable.

### 3.6 Supporting, conflicting and alternative evidence
- None (harness proposal, line 163). **[INFERRED]**

### 3.7 Derivation rules and admissible premises
- **"conversions are derived"** (D-C-1, stage-c line 32). **[ESTABLISHED]**
  - In context this means converted values are computed, not stored: the original value and unit are kept on the
    record, and the content is in SI.
  - It does **not** make a converted value an INFERRED attestation, and no derivation record is involved. **[INFERRED]**
- **Do not fabricate derivations.** The harness fails any answer that includes a `{rule, premises}` object
  (harness review §9 item 3). A contract should state that convert presents no derivation. **[ESTABLISHED]**
  (LABS-1.062 correction)

### 3.8 Documented refusals and unsupported operations

| Refusal | Source | Standing |
|---|---|---|
| across dimensions (`ValueError "cannot convert …"`) | stage-c C1 API line 45; harness review §9 line 255 | **[ESTABLISHED]** |
| name that is not a unit, or a unit without a dimension (`"… is not a unit with a dimension"`) | qualities.py 72-73 only; harness review line 256 marks it **not established** | **[INFERRED]**: needs an owner decision |
| compound or derived units (N to kg·m/s²) | E2 design M9 (line 96), GAP-MEAS-5 | **[ESTABLISHED]** unsupported (a G question) |
| non-finite values | no check in convert (qualities.py 95-104); `measure` checks them | not covered |

### 3.9 Known limitations and gaps
- GAP-MEAS-5: `dimension` is a plain string; there is no dimensional algebra and no prefixes.

---

## 4. `laboratory.calibration_status(wm, world, instrument, t, as_of=None, perspective=SYSTEM)`

### 4.1 Supported question classes and input conditions
- **What it answers:** is the instrument calibrated at t, for the perspective. One question answered by several
  holdings: every certificate whose `calibration-of` content names the instrument.
  - Sources: stage-d3-design §3 (line 65); stage-d3 §2 (line 39) and §3 (lines 84-96); increment-C design §2 "One
    question" (lines 43-44) and §3.1 (lines 50-52). **[ESTABLISHED]**
- **Content shape.** `calibration-of(certificate, calibrated)`:
  - the certificate is an information object and the calibrated thing a physical object;
  - it is attested over the certificate's valid time and rests on the certificate.

  Sources: D-D3-1 (stage-d3-design line 99); stage-d3 §1 (line 13); D-D-7 (stage-d-review line 245). **[ESTABLISHED]**
- **E2 class:** M6, with calibration status alone as class A, "as in E1" (E2 design line 93). E1 template
  `calibrated`, expected field `judgement` (TEMPLATES line 38). **[ESTABLISHED]**
- **`t` is required.** **[ESTABLISHED]** (stage-d3-design §3 signature)
- **Writer default.** `calibrate` without an end holds until superseded (CLARIFICATIONS C2). **[ESTABLISHED]**

### 4.2 Output fields and permitted vocabulary
- **holds / status / judgement**, using the capable() cases with no new statuses.
  - The judgements are established, expired, denied, disputed, not yet effective and not established (D-C-3,
    stage-c line 34; stage-d3 §3 table lines 89-96; TEMPLATES line 20). **[ESTABLISHED]**

  | judgement | holds | status | design example |
  |---|---|---|---|
  | established | True | core rule over the established holdings' support (ASSERTED, STIPULATED, …) | B3 at 09:00 |
  | expired | False | core rule over the ended holdings' support; no denial | B3 at 15:00 (certificate ended 10:00); D-C-4 |
  | denied | False | core rule over the denials' support | B7 in the quality office's perspective |
  | disputed | None | DISPUTED | B7 for the system (assertion and denial both accepted) |
  | not yet effective | None | UNKNOWN | B3 before its certificate's start |
  | not established | None | UNKNOWN (something found) or NOT_YET_KNOWN (nothing) | B9, no certificates (NOT_YET_KNOWN); an unreviewed calibration (UNKNOWN) |

  - The rows come from stage-c C2 table (lines 198-205), stage-d3 §3 and increment-C §3.1. **[ESTABLISHED]**
  - "not established" with no certificates means that no calibration is recorded at all (stage-d3 line 95; docstring).
    **[ESTABLISHED]**
- **`support`.** The sorted ids of the deciding claims (C-4, increment-C design line 212; increment-C report line 33).
  **[ESTABLISHED]**
  - It is empty for DISPUTED and undecided answers (increment-C report, "Points decided in implementation" 2,
    lines 74-75). **[ESTABLISHED]** (approved and merged under LABS-1.041)
- **`certificates`.** Each certificate with its reference number (`calibration-ref`, exact text), its own judgement
  and its evidence (stage-d3 §2 line 39). **[ESTABLISHED]**
  - A certificate without a number has reference None and never matches (stage-d3 line 109). **[ESTABLISHED]**
- **`in_force`.** Listed in stage-d3 §2 (line 39) without a definition. **[ESTABLISHED]** as a field; its meaning
  (certificates whose own judgement is established) is **[INFERRED]** from laboratory.py 234.
- **Per-certificate entries:** the core per-content judgement (`_judgement`: judgement, holds, status, evidence =
  `claims()`, shared with organisation; stage-d3 §2 "Shared judgement", lines 44-48). **[ESTABLISHED]**
  - The exact evidence fields are increment B's claims (§2.2). **[ESTABLISHED]**

### 4.3 Judgement and uncertainty semantics
Rule Q (C-1 to C-3; increment-C design §3.1 lines 49-71) **[ESTABLISHED]**:
1. **Conflict first.** DISPUTED if any holding is disputed, or if one is established while another is denied by an
   accepted denial.
2. **Established.** If any holding is established: holds, with the status from the core rule over the **union** of
   the deciding support of every established holding. This is independent of order (E7 / E7b examples, design
   line 143).
3. **Does not hold.** Otherwise, denied (if any) or expired: the core rule over the union of the denied and expired
   holdings' support.
4. **Undecided.** Otherwise UNKNOWN or NOT_YET_KNOWN; "not yet effective" if a holding is, else "not established".

Further rules:
- **Undecided holdings beside an established one** do not change it (C-3). An expired holding beside an established
  one is not a conflict. **[ESTABLISHED]**
- **One disputed certificate and another in force** gives DISPUTED overall, while each certificate keeps its own
  judgement (stage-d3 §8, lines 226-228). **[ESTABLISHED]**
- **Per-content cases** (increment B §2.4 and the label table, lines 79-111) **[ESTABLISHED]**:
  - an unknown end is "not established", not "not yet effective" (DI-5);
  - unreviewed means pending, which gives "not established";
  - rejected, retracted or superseded alone give "not established".
- **Calibration never invalidates a measurement:** see §5.3. **[ESTABLISHED]**

### 4.4 Temporal, perspective and world visibility
- **Perspective.** B7 is disputed for the system and denied for the quality office (stage-d3 §3 line 119).
  **[ESTABLISHED]**
- **Knowledge time.** Before the denial was recorded, B7 is established (line 120). **[ESTABLISHED]**
- **Hypothetical world.**
  - A plan stipulating a renewed certificate makes the calibration established (STIPULATED) there.
  - Both certificates are listed (B3 expired, B3-r established).
  - The actual world is unchanged (lines 121-123).

  **[ESTABLISHED]**
- **Valid time.** The attestation's interval (stage-d3-design line 34: "Temporal validity of calibration: the
  attestation's interval"). **[ESTABLISHED]**

### 4.5 Ordering and multiplicity
- **Certificates.** One entry per calibration content (certificate) naming the instrument, sorted by certificate id
  (laboratory.py 230). **[INFERRED]**
  - Rule Q's result does not depend on that order (increment-C tests, renamed certificates E7/E7b, report line 87).
    **[ESTABLISHED]**
- **`support` is sorted.** **[ESTABLISHED]** (C-4 text "the sorted ids")

### 4.6 Supporting, conflicting and alternative evidence
- **Support.** The `calibration-of` attestations that decide (`support`). **[ESTABLISHED]** (C-4)
- **E1 practice (`benchmark/e1/questions/laboratory.jsonl`):** `required_evidence` was the calibration attestation
  ids:
  - established and expired: the deciding claim (LAB-001, LAB-002);
  - disputed: both the assertion and the denial (LAB-004);
  - not yet effective: the accepted future claim (LAB-003).
  - The E1 harness cites `support` when it is non-empty, otherwise "the usable evidence of the entries"
    (evaluation/run.py 73-79).

  The harness proposal for E2 is "the calibration's deciding support (as E1's `calibrated`)" (harness review
  line 155). **[INFERRED]** (E1 gold practice, not a design decision)
- **The certificate is not an attestation.** It is the information object the attestation rests on (rests-on). It is
  identified in `certificates[].certificate`, not in `support`. **[ESTABLISHED]**: stage-d3 §1 line 13; D-D-7.
- **Not support:** unreviewed or rejected calibration claims stay listed with their own judgement (C-3). Under v0.2
  §6.2 they are alternatives. **[ESTABLISHED]**

### 4.7 Derivation rules and admissible premises
- **No derivation.** Calibration is a content judged like a capability; no rule is applied (stage-d3 §2 line 47).
  **[ESTABLISHED]**
- **The reference link is text.** The stated reference is text, not a link, and is reported, never reconciled
  (G-6, D-D3-2). **[ESTABLISHED]**

### 4.8 Documented refusals and unsupported operations
- **Profile not installed.** `ValueError` "the laboratory profile is not installed" (laboratory.py 49-51). There is no
  design text. **[INFERRED]**: it needs an owner decision on whether it is a documented refusal.
- **Unsupported:** **[ESTABLISHED]** (deferred lists in stage-d3-design line 120 and stage-d3 §8)
  - automatic invalidation (stage-d-review line 90);
  - calibration history on quality instances (D-D-8);
  - an "undermines" relation (G-3).

### 4.9 Known limitations and gaps
- GAP-MEAS-9: the reference is text, checked as exact text.
- GAP-MEAS-10: G-3.
- DI-9 / GAP-MEAS-8: performance (16 queries).

---

## 5. `laboratory.measurement_calibration(wm, world, bearer, quality, t=None, as_of=None, perspective=SYSTEM)`

### 5.1 Supported question classes and input conditions
- **E2 classes.** **[ESTABLISHED]** (E2 design lines 93 and 130)
  - M6: was the instrument calibrated when the measurement was taken;
  - X2: a fixed composition with `facts_about`.
- **What it is.** For each measurement record: the activity's instrument, its **stated** calibration reference, and
  the **attested** calibration judged at the activity's start. It is a report beside the measurement and never
  changes usability or comparison.
  - Sources: stage-d3-design §3 (line 66); D-D3-2 (line 100); stage-d3 §2 (line 40). **[ESTABLISHED]**
- **No new link.** Calibration at measurement time is "computed from the activity's instrument and time (no new link
  from record to certificate)" (D-D3-2). **[ESTABLISHED]**
- **`t=None` is optional** (stage-d3 §2 signature, line 40). **[ESTABLISHED]**
  - Its meaning (it filters which measurements are listed, as `measurements(t)`; calibration is still judged at each
    activity's start, not at t) is **[INFERRED]** (laboratory.py 262-268).

### 5.2 Output fields and permitted vocabulary
- **One row per measurement record and activity instrument.** Each row has:
  - the stated reference;
  - the attested calibration (the whole `calibration_status` answer at the activity's start);
  - an exact-text reference check;
  - the measurement's own acceptance and usability, copied unchanged.

  Source: stage-d3 §2 (line 40). **[ESTABLISHED]**
- **Reference-check vocabulary** (stage-d3 §3 table, lines 101-107; deviation 3 in §6a line 187) **[ESTABLISHED]**:

  | check | design example |
  |---|---|
  | "matches a certificate" (with that certificate's judgement) | the 15:00 weighing states CAL-B3-2026-10, which matches B3, expired at that time |
  | "no certificate with the stated reference" (inconsistent) | Bo's B7 record states CAL-B7-2026-09; the certificate is CAL-B7-2026-08 |
  | "no reference stated" | the k = 3 result on B7 (still reported as disputed) |
  | "no certificate recorded for the instrument" | a stated reference where the instrument has no calibration content |
  | "no instrument recorded" | lab 2's external result |

  - Deviation 3 is approved as "reporting only" (stage-d3 §6a): its effect on approved semantics is listed as none.
- **`attested`.**
  - It embeds the whole `calibration_status` answer, so it includes `support` (increment-C report lines 38-39).
    **[ESTABLISHED]**
  - It is None when no time or instrument is known (docstring, laboratory.py 258-259). **[INFERRED]**: the design
    does not state it, though stage-c line 118 (activity times come from its account and depend on the perspective)
    implies it.
- **Implementation-only field names:** `record`, `attestation`, `acceptance`, `usable`, `activity`, `at`,
  `instrument`, `stated_reference`, `attested`, `reference_check` (laboratory.py 269-274). **[INFERRED]**

### 5.3 Judgement and uncertainty semantics
- **Calibration never invalidates, discards or downgrades a measurement.**
  - Acceptance and usability are copied from `measurements()`, and they are equal in three perspectives.
  - Writing calibrations and denials for every balance leaves `measurements()` and `compare_measurements()` identical.

  Sources: stage-d3-design line 36; D-D3-2; stage-d3 §3 "Never invalidating" (lines 111-116); D-D-7, "no automatic
  invalidation". **[ESTABLISHED]**
- **Stated beside attested.** The stated reference and the attested calibration are reported side by side; they can
  differ (P4). They are never reconciled (G-6). **[ESTABLISHED]**
- **Calibration and measurement uncertainty stay apart.** Calibration doubt belongs to credence or stance; it never
  widens a range (v0.2 lines 259-261). **[ESTABLISHED]**
- **Judgements as `calibration_status`**, inherited (increment-C inventory line 112: "inherits"). **[ESTABLISHED]**

### 5.4 Temporal, perspective and world visibility
- **Calibration time.** Calibration is judged at the measurement activity's **start** (stage-d3-design line 35;
  D-D3-2; stage-d3 §3 line 85; D-D-7, "at the activity's time"). **[ESTABLISHED]**
  - The instant used is the start Window's **earliest** bound (laboratory.py 265). That is implementation only
    (GAP-MULTI-2, inventory line 341: "E2 gold must state which instant is meant"). **[INFERRED]**
- **Activity times are judged.** The activity's start comes from an account the perspective can use. Without one,
  the activity has no time and its calibration is not judged.
  - Stage-c line 118 says activity times depend on the perspective. **[ESTABLISHED]**
  - The None outcome is **[INFERRED]** (docstring; `interval` docstring, reader-docs line ~125).
- **Measurement and calibration share the context.** Perspective, `as_of` and world apply to both the measurement
  and the calibration (hypothetical renewal example, stage-d3 line 121). **[ESTABLISHED]**

### 5.5 Ordering and multiplicity
- **One row per (measurement attestation × record × activity × instrument).**
  - A record with no activity gives one row with activity None.
  - An activity with no instrument gives one row with instrument None.
  - Statements (no records) give **no rows**.
  - Rows are sorted by (record, instrument or "").

  Source: laboratory.py 261-275. **[INFERRED]**: the design says only "per measurement record and activity
  instrument" (stage-d3 line 40, **[ESTABLISHED]**).
- **Shared records.** A record shared by two attestations (allowed by stage-c lines 109-111) gives two rows. Their
  relative order falls back on the stable sort of `measurements` (attestation id). **[INFERRED]**

### 5.6 Supporting, conflicting and alternative evidence
- **Harness proposal.** "the usable measurement, and the calibration's deciding support (as E1's `calibrated`)"
  (harness review line 154; evaluation/e2/readers.py 171-178). **[INFERRED]** (proposal)
- **Matching certificates are reported, not cited.** A certificate matched by reference is reported with its own
  judgement, even an expired or rejected one. The match is a text check, not support. **[ESTABLISHED]** (G-6:
  "reported, never reconciled")
- **Unusable measurements still get rows.** Rows for unusable measurements (alternatives, superseded) are listed,
  with calibration judged. They should not be cited as measurement support. **[INFERRED]**

### 5.7 Derivation rules and admissible premises
- **No derivation.** This is a fixed composition: measurements, then the activity start, then `calibration_status`
  (inventory line 320). No rule is recorded (DI-7). **[ESTABLISHED]** (composition stated in stage-d3 §2 and D-D3-2)

### 5.8 Documented refusals and unsupported operations
- **Profile not installed.** As §4.8: implementation only. **[INFERRED]**
- **Unsupported:** **[ESTABLISHED]** (stage-d3-design D-D3-2; v0.2 line 254, profile-declared; Df)
  - linking a record to a certificate (D-D3-2);
  - invalidation;
  - "calibration states that matter" for comparability.

### 5.9 Known limitations and gaps
- GAP-MEAS-8: 411 queries for sample-12 (DI-9, `deferred-issues.md` lines 287-288).
- GAP-MEAS-9: the reference is text.
- GAP-MULTI-2: which instant is "the activity's start".

---

## 6. Discrepancies (docstring or implementation versus design)

Each item cites both sides. The items marked **owner decision** are those the E2 design (§5.2) requires the contract
to stop on.

1. **Polarity disputes are not reported by `compare_measurements`.**
   - *Design:* v0.2 §5.3 (lines 437-439): an accepted assertion and an accepted denial make the answer DISPUTED.
     Stage-c "Disputes" (lines 97-98) explicitly contemplates "a polarity denial or disjoint ranges" as rival
     measurement attestations.
   - *Implementation:* `usable` is AND-ed with `a.polarity` (qualities.py 232). An accepted denial resting on a
     record is therefore placed in `alternatives` (described as "unaccepted measurements", although it is accepted)
     and never makes the status DISPUTED (qualities.py 245-262).
   - *With `t`:* denials are dropped entirely, since `verdict` is False for a denial inside its interval
     (qualities.py 207).
   - **Owner decision.**
2. **Point-in-time measurements (no `persists`, `end` omitted) may never "hold at t", and may be incomparable with
   each other.**
   - *Implementation:* `measure` sets `end = end or start` (qualities.py 125). Intervals are half-open
     (semantics.py 121-137). An attestation [s, s) then gives `verdict(a, s)` False, so `measurements(t=s)` excludes
     it.
   - Two such measurements at the same instant give `a1 <= b0`, so the pair is "valid times do not overlap"
     (qualities.py 286).
   - The reference world avoids this by always passing `persists=True` with a 5-minute interval
     (examples/lab.py 38-60).
   - *Design:* v0.2 makes non-overlapping times a reason only "for a changing quantity". Plan §9.2 gives the content
     "the quality's valid time".
   - *Verification:* found by reading the code; not checked by execution. A probe is needed. **Owner decision** on
     the intended valid time of a non-persisting result.
3. **Non-overlapping valid times are applied to every quantity.**
   - *Design:* v0.2 line 254 says "for a changing quantity".
   - *Implementation:* every quantity (qualities.py 281-287); there is no notion of a changing quantity.
   - Not decided in stage-c.
4. **"units without an accepted conversion" versus "different units (no common SI unit)".**
   - *Design:* v0.2 line 254.
   - *Implementation:* compares the content's SI unit ids (qualities.py 272-273).
   - *Edge case:* `si_unit` takes the alphabetically first unit with factor 1 and offset 0 (qualities.py 90-93).
     Defining a second SI-like unit for a dimension could split contents of one dimension into "different units".
     **[INFERRED]**
5. **Comparison is per attestation, not per content.**
   - *Design:* v0.2 line 247, "two `has-quality` contents".
   - *Implementation:* pairs of usable attestations (qualities.py 245-256). Two attestations of one content are
     compared ("possibly compatible", trivially).
   - Stage-c D-C-2 makes the attestation the unit of provenance (lines 68-70), which supports attestation-level
     pairs, but no design text says so for comparison.
6. **`alternatives` holds more than "unaccepted measurements".**
   - *Design / docstring:* v0.2 §6.2 says unaccepted attestations by others are alternatives; the docstring
     (qualities.py 242) says "unaccepted measurements are listed as alternatives".
   - *Implementation:* every unusable measurement-kind entry (qualities.py 267). That includes accepted denials (item
     1), accepted hypotheses and doubts (non-supporting stances), superseded attestations (the correction history,
     M4), rejected, retracted and unreviewed ones.
   - The design does not say where the superseded original of a correction is listed. Stage-c (lines 92-96) only says
     the perspective "sees the new attestation and record".
7. **Status UNKNOWN when only statements are usable.**
   - *Implementation:* UNKNOWN when `everything` is non-empty, which includes accepted specifications
     (qualities.py 262).
   - *Design:* D-C-5 defines UNKNOWN as "something is held, but nothing applicable". Whether an accepted design value
     counts as "something held" for a measurement comparison is not stated. **[INFERRED]**
8. **Categorical qualities are excluded.**
   - *Design:* v0.2 §3.3 (line 222) allows a `value` category ("open"). Stage-c line 48 says "every stated value".
   - *Implementation:* `measurements` skips any `has-quality` attestation without `lower` (qualities.py 204-206).
     Categorical has-quality values are never listed. Not documented in the docstring.
9. **Statements are not normalised to SI.**
   - *Design:* D-C-1 says "the reported content is in SI"; v0.2 says content is stored in a canonical unit
     (line 228).
   - *Implementation:* only `measure` converts. A statement written through generic `attest` keeps whatever unit and
     range the attester gave (example: the spec in examples/lab.py 53-54 uses kg, which happens to be SI).
     `measurements` reports it as is. **[INFERRED]**
10. **Identity (same-as) is computed but not used.**
    - *Implementation:* `_view` returns the perspective's identity (`ident`), but `measurements` filters on the
      literal ids (`bearer in a.roles["bearer"]`, qualities.py 201-205). Measurements stated about an accepted alias
      of the bearer are loaded and then dropped.
    - *Design:* v0.2 §4.2 makes content equivalence semantic under identity. The identity increment corrected
      traversals for it (DI-12). Not covered by stage-c. **[INFERRED]**: needs a probe.
11. **The reference check is misleading when the activity's time is unknown.**
    - *Implementation:* when the instrument is recorded but the activity has no accepted account (`at` None),
      `attested` is None and the check runs against an empty certificate list (laboratory.py 267-274). A stated
      reference then gives "no certificate recorded for the instrument" even if the instrument has certificates.
    - *Design:* stage-d3 §3 (line 106) defines that check as "where the instrument has no calibration content".
      **[INFERRED]** (code reading)
12. **The order of the reference checks is not in the design.**
    - *Implementation:* no instrument, then no reference stated, then no certificate, then match or mismatch
      (laboratory.py 238-251).
    - *Design:* the stage-d3 table lists five cases without precedence.
13. **The calibration instant.**
    - *Design:* "at the activity's start" (D-D3-2; stage-d3 §3).
    - *Implementation:* the earliest bound of the start Window (laboratory.py 265).
    - The choice matters when the start is uncertain (GAP-MULTI-2).
14. **The `t` parameter of `measurement_calibration`.**
    - *Design:* the signature gives `t=None` (stage-d3 line 40) but no meaning.
    - *Implementation:* t filters the measurements, and calibration is judged at the activity start regardless of t.
15. **Where calibration status is reported.**
    - *Earlier design:* D-D-7 and G6 (stage-d-review lines 107 and 245) say "`measurements()` reports calibration
      status at the activity's time".
    - *Later approved design:* D-D3-2 and D-D3-3 moved it to the profile function `measurement_calibration`;
      `measurements()` reports no calibration status, only the record's stated `calibration` reference.
    - The later decision supersedes the earlier one. Record it in the contract.
16. **The plan's laboratory profile and links.**
    - *Plan:* the laboratory profile lists `instrument sub physical-object` and `quality-instance` (plan line 93), and
      the scenario uses `result-of` links (line 146).
    - *Superseded by:* plan §9.2 (`produced` / `reports`), D-D-8 (quality instances deferred) and the D-3 schema
      (no `instrument` type; the core instrument role, stage-d3-design line 32).
17. **`convert` refuses a name that is not a unit.**
    - *Implementation:* `ValueError "… is not a unit with a dimension"` (qualities.py 72-73).
    - *Design:* none. The harness marks it unestablished (harness review line 256). **Owner decision.**
18. **The laboratory profile refusal.**
    - *Implementation:* `calibration_status` and `measurement_calibration` raise `ValueError` when the laboratory
      profile is not installed (laboratory.py 49-51).
    - *Design:* none. **Owner decision** on whether it is a documented refusal.
19. **`convert` without a target needs no SI unit.**
    - *Implementation:* with `to=None`, `convert` returns raw × factor + offset without checking that an SI unit for
      the dimension is defined. `measure` requires one (via `si_unit`).
    - *Docstring:* "default: the SI unit". Not covered by design. **[INFERRED]**
20. **The meaning of `in_force`.**
    - *Design:* named in stage-d3 §2 (line 39), undefined.
    - *Implementation:* certificates whose own judgement is "established" (laboratory.py 234). It can list a
      certificate while the overall judgement is "disputed" (because another certificate is disputed).
21. **Evidence for "not yet effective" and "disputed" calibration answers.**
    - *Approved design:* `support` is empty for DISPUTED and undecided answers (increment-C report lines 74-75).
    - *E1 gold and harness:* E1 required evidence (LAB-003, LAB-004), and the harness extractor fills it from "the
      usable evidence of the entries" (evaluation/run.py 73-79).
    - The E2 contract must state which rule cites evidence for these cases. **Owner decision.**
22. **Usable statements and the `measurements` extractor.**
    - *Harness:* `ev_measurements` cites every usable entry, statements included (evaluation/e2/readers.py 163-164).
    - *Harness review text:* "the attestation of each **usable** value" (line 152).
    - *Design:* statements are a separate kind (stage-c line 26).
    - Decide whether a specification's attestation is support for a "stated values" question.
23. **Coverage tolerance and the formula.**
    - *Implementation:* 1e-6 tolerance (qualities.py 27) and coverage_level = erf(k/√2) (qualities.py 30-32).
    - *Design:* "95 %" for k = 2 (v0.2 lines 225 and 377). The implementation's 0.9545 differs from the design's
      rounded wording.
    - Gold should use the formula or state a tolerance.
24. **Docstring wording versus design wording for statements.**
    - *Docstring:* lists statement bases ("a design specification by testimony, a reading noted without a record",
      qualities.py 197-198).
    - *Design:* names only specifications (stage-c line 26). "A reading noted without a record" as a statement is
      docstring only.
