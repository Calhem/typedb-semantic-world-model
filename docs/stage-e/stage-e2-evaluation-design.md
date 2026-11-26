# Stage E2 evaluation design: space, measurement, causation, process and multi-step questions

**Status:** design for review (LABS-1.054, steps 5–7), 20 November 2026. **Nothing here is implemented:** no question,
fixture, template, harness change or gold answer has been written, and no reader or ontology change is proposed.
Stage E2 starts only after this design is approved.

**Decisions (LABS-1.060):** E2-D1 to E2-D7 are approved, with E2-D6's thresholds amended, along with DI-17
(evaluation only, about 12 identity-conflict questions) and the DI-7 deferral. See
[stage-e2-decisions.md](stage-e2-decisions.md); it amends section 7 and wins where the two differ. E2 has not started.

**Companion:** [stage-e-entry-report.md](stage-e-entry-report.md) (the Stage E entry baseline, performance and
correctness risks this design relies on).

**Evidence base for this design:** a read-only inventory of the public API, the schema, the reader documentation and
the deferral registers (each gap below cites where it was found), checked by hand at the main references
(`transform_between` physical.py:371, `where` physical.py:381, `process_steps` dynamics.py:728, `causes_of`
dynamics.py:653, `explain` dynamics.py:706, `convert` qualities.py:95, `measure` qualities.py:108,
`compare_measurements` qualities.py:236; the fixture loader's operations, evaluation/loader.py:129–250).

## 1. Purpose
Stage E1 (272 questions) tested one reader per question over identity, roles, places, offices, calibration status and
variant worlds. It asked **no** question about frames, transforms, measurements, causal claims, explanations or process
steps (E1 overnight report, "not reached"). E2 extends the evaluation to six families:

| Family | Code | What it tests |
|---|---|---|
| Spatial transformations | S | composing and inverting frame transforms; chains that agree or conflict |
| Frames | F | where a thing is in a frame at a time; frames that change over time |
| Measurements | M | stated values, units and conversion, uncertainty, comparison, calibration at measurement time |
| Causal relationships | C | stated causes (direct and through descriptions), claimed effects against accepted change, one-step explanations |
| Process steps | P | the steps of a process and their order by time, including disputed steps |
| Multi-step reasoning | X | questions whose answer needs two or more readers in a defined order |

E2 has two aims, reported separately:
1. **Conformance:** do the existing public readers answer as their specification says, on questions in these families?
2. **Coverage:** which reasonable questions in these families the model **cannot** answer yet, and why. A missing
   capability is reported as a gap, never as a reasoning failure (section 4).

## 2. What E2 can build on (existing public API)
| Family | Readers and helpers | Statuses they return |
|---|---|---|
| S | `transform_between` (shortest frame chain, composed and inverted, every chain checked for agreement); `spatial.Transform.then / inverse` | INFERRED, DISPUTED, UNKNOWN (no chain, or search truncated) |
| F | `where(world, thing, frame, t)` (every candidate pose, not merged); `poses`; `frame_info`; `changes`/`history` on a frame | STIPULATED, ASSERTED, INFERRED, DISPUTED, UNKNOWN, NOT_YET_KNOWN |
| M | `measure`, `measurements`, `compare_measurements` (possibly compatible / incompatible / incomparable), `convert` (same dimension, affine), `laboratory.measurement_calibration`, `calibration_status` | as reader-docs; comparisons use their own vocabulary |
| C | `causes_of` (direct claims and claims lifted through accepted `describes` links, with each occurrence's status), `effects_of` (claimed effect against accepted state change), `explain` (one step back), `changes` | as reader-docs |
| P | `process_steps` (direct `part-of` steps ordered by interval start, disputed steps kept), `before`, `interval` | as reader-docs |
| X | fixed compositions only: `explain`, `where`, `measurement_calibration`, `official_act`, `replacement`, `provenance`; transitive `parts`, `dependencies`, identity; variant-world inheritance | per reader |

## 3. Competency questions
Each competency question (CQ) is a question **form**; E2 questions instantiate forms over fixtures. Every CQ is
classified:
- **A:** answerable by an existing public reader **and** the E1 harness can already express its fixture and answer
  (in these families only M6's calibration-status part, which E1 already covers: every other CQ needs harness work);
- **H:** answerable by an existing public reader, but the harness cannot yet express the fixture or extract the answer
  (harness work, not a model change; section 6);
- **G:** needs a capability that is not implemented (a gap id from section 4). G questions are written down as
  coverage probes but are **not** scored as conformance.

### 3.1 Spatial transformations (S)
| CQ | Question form | Reader(s) | Class |
|---|---|---|---|
| S1 | What is the transform from frame A to frame C, given A→B and B→C? | `transform_between` | H |
| S2 | What is the transform from C to A (the inverse of a stated chain)? | `transform_between` | H |
| S3 | Two chains from A to D disagree beyond tolerance: is the transform disputed, and which claims conflict? | `transform_between` | H |
| S4 | No chain links A and Z: is the answer UNKNOWN rather than a guess? | `transform_between` | H |
| S5 | A transform stated by one perspective only: what does another perspective see? | `transform_between(perspective=)` | H |
| S6 | A transform superseded at t1: which transform holds before and after t1? | `transform_between(t)` | H |
| S7 | What is the transform with stated uncertainty propagated? | none | G (GAP-SPATIAL-1) |
| S8 | Give the rotation as roll, pitch and yaw / in degrees | none | G (GAP-SPATIAL-3, -4) |

### 3.2 Frames (F)
| CQ | Question form | Reader(s) | Class |
|---|---|---|---|
| F1 | Where is thing X in frame F at t (directly stated)? | `where` | H |
| F2 | Where is X in frame G at t, when X is stated in F and F→G is known (derived through a chain)? | `where` | H |
| F3 | Two sources place X differently in F at t: are both candidates reported, and is the answer disputed? | `where` | H |
| F4 | X's pose is stated only before t: is X's pose at t unknown (no persistence beyond the stated interval)? | `where` | H |
| F5 | In a hypothetical variant where X is stipulated elsewhere, where is X, and does the actual world change? | `where` on both worlds | H |
| F6 | As known at an earlier knowledge time (`as_of`), where was X? | `where(as_of=)` | H |
| F7 | Frame F is anchored to a thing that moved: where is a point fixed in F now? | none | G (GAP-FRAME-1, -2) |
| F8 | Where was X between two stated poses (interpolation)? | none | G (GAP-FRAME-3) |
| F9 | What is the frame hierarchy / root frame of F? | `frame_info` one hop only | G (GAP-FRAME-4) |
| F10 | Where is a part, given only where its assembly is? | none | G (GAP-FRAME-6) |

### 3.3 Measurements (M)
| CQ | Question form | Reader(s) | Class |
|---|---|---|---|
| M1 | What values of quality Q of X have been stated, by whom, with which instrument, uncertainty and conditions? | `measurements` | H |
| M2 | Do two measurements of the same quality agree within their stated uncertainties? | `compare_measurements` | H |
| M3 | Two measurements under different stated conditions, or at different coverage factors: comparable? | `compare_measurements` | H |
| M4 | A measurement was corrected or superseded: which value is current, and which is history? | `measurements` | H |
| M5 | What is 20 °C in kelvin, or 1,500 g in kilograms (same-dimension conversion)? | `convert` | H |
| M6 | Was the instrument calibrated when the measurement was taken? | `measurement_calibration`, `calibration_status` | H (calibration status alone: A, as in E1) |
| M7 | Does the measured value meet the specification or tolerance (pass or fail)? | none | G (GAP-MEAS-1) |
| M8 | What is the best estimate of Q from several measurements? | none | G (GAP-MEAS-4) |
| M9 | Convert a compound unit (N to kg·m/s²) | none | G (GAP-MEAS-5) |

### 3.4 Causal relationships (C)
| CQ | Question form | Reader(s) | Class |
|---|---|---|---|
| C1 | What caused event or state E, according to the accounts accepted in the world? | `causes_of` | H (`causes` is writable through the generic `attest` step, but there is no template or extractor for `causes_of`) |
| C2 | A cause is stated against an occurrence description that is disputed or denied: is that reported with the occurrence's own status? | `causes_of` | H (describes links need fixture support) |
| C3 | An event claims an effect: did the claimed change actually follow (accepted state change), or not? | `effects_of` | H (GAP-HARNESS-2: initiates/terminates need a proposition id) |
| C4 | Why does state S hold at t (one step back: the event and claim that explain it)? | `explain` | H |
| C5 | When did S begin and end, and which boundaries are certain or only possible? | `changes` | H |
| C6 | What did E cause (forward), and what did that in turn cause (chains)? | none | G (GAP-CAUSE-1, -2) |
| C7 | If E had not happened, would S hold (intervention)? | none | G (GAP-CAUSE-3) |

### 3.5 Process steps (P)
| CQ | Question form | Reader(s) | Class |
|---|---|---|---|
| P1 | What are the steps of process R, in time order? | `process_steps` | H |
| P2 | A step's occurrence is disputed: is it kept and flagged, not silently dropped? | `process_steps` | H |
| P3 | Did step a end before step b began (with interval windows)? | `before`, `interval` | H |
| P4 | Two steps with overlapping or unknown intervals: is no order asserted? | `process_steps` | H |
| P5 | What are the sub-steps of a step (nesting)? | `parts`, repeated `process_steps` | H (one level per call) |
| P6 | In what order SHOULD the steps happen (procedure), and was it followed? | none | G (GAP-PROC-1, -2) |
| P7 | Which preconditions held when a step started? | none | G (GAP-PROC-3) |
| P8 | How long did step a take? | none | G (GAP-PROC-4) |
| P9 | Which expected step did not happen? | none | G (GAP-PROC-7) |

### 3.6 Multi-step reasoning (X)
Each X question names its **plan**: the readers in order and how each step's answer feeds the next (for example "the
instant is the start's earliest bound of the event's interval"). Every intermediate answer has its own expected value,
so a wrong final answer can be traced to the step that went wrong.

| CQ | Question form | Plan | Class |
|---|---|---|---|
| X1 | Where was the instrument (in frame F) when it took measurement m? | `measurements` → instant of m → `where` | H |
| X2 | Was the sample's measuring instrument calibrated, and by whom was the calibration certificate issued? | `measurement_calibration` → `facts_about` | H |
| X3 | Which part was replaced by event E, and where is the new part now? | `event_role` → `value_at` | H (both readers have E1 templates; the two-step plan needs the plan runner) |
| X4 | What explains state S, and was the explaining event's occurrence accepted? | `explain` → `occurrence_status` | H |
| X5 | In the plan variant, which steps of process R differ from the actual world? | `process_steps` on both worlds, compared | H |
| X6 | Who held the office whose holder authorised step a of process R? | `process_steps` → `event_role` → `office_holders` | H |
| X7 | Where was the part whose measurement failed when the event that caused X happened? | needs a failed-measurement concept and forward causation | G (GAP-MULTI-3, GAP-CAUSE-2) |
| X8 | Any free question composed by the system itself (a query plan) | none | G (GAP-MULTI-1) |

### 3.7 Size and mix (proposed)
- **About 180 scored questions** (A and H) over about 20 new fixtures: S 25, F 35, M 35, C 30, P 25, X 30. At least
  one third adversarial (conflicts, denials, unknowns, wrong perspective, superseded claims, variant worlds), as in E1.
- **About 25 gap probes** (G), one or more per gap above, kept in a separate file. They are not scored for
  conformance. Each records what a correct answer would need, and checks only that no existing reader fabricates an
  answer where one is called (for example that `where` stays UNKNOWN between two stated poses).
- Every question on both query paths (selective and full load), and with `as_of` and perspective variation where the
  family allows it.

## 4. Gaps: missing capabilities are not reasoning failures
The gaps found (full list with evidence in section 9):

| Gap | What is missing | Families |
|---|---|---|
| GAP-SPATIAL-1..8 | uncertain transforms; rotations other than quaternions; units other than metres and radians; ~~frames judged without same-as identity~~ (GAP-SPATIAL-5, withdrawn in LABS-1.063: by design); no geometry; no distance reader; `holds` cannot pick out one position | S, F |
| GAP-FRAME-1..6 | anchoring has no geometric effect; `move()` updates places, not frames; no interpolation; no hierarchy or history reader; parts not positioned through their assembly | F |
| GAP-MEAS-1..11 | no specification, tolerance or pass/fail; conditions as exact text; no coverage-factor harmonisation; no best estimate; single-dimension units; `has-quality` not a functional slot; no trend reader; N+1 reads; calibration reference is text; no "undermines"; no derivation record | M |
| GAP-CAUSE-1..7 | no causal chains; no forward "what did E cause"; no intervention; no automatic causal inference; no strength or mechanism; no failure propagation; no derivation record | C |
| GAP-PROC-1..7 | no explicit order; no procedure or plan type; no pre- or postconditions; no duration; processes not ongoing; one level only; no missing-step detection | P |
| GAP-MULTI-1..8 | no general composition; no "at the time of event E" rule; no failed-measurement concept; the other gaps compound | X |
| GAP-HARNESS-1..4 | the harness's `attest` takes no `params`; no fixture steps for position, frames, measurement, causal claims or describes; no templates or extractors for the new readers; reader-docs.md lacks those readers | all (harness only) |

**Rule for reporting (proposed acceptance rule G-1):** a question is classified A, H or G **before** gold is written,
by the design owner, from this inventory, never from a run. A G question that fails is reported under its gap id. An
A or H question that fails is adjudicated (section 5.5); only a confirmed implementation defect counts as a
reasoning failure. A question that turns out to need a missing capability during adjudication is reclassified G
**with the evidence**, and the reclassification is listed in the report; it is never silently dropped.

## 5. Independent expected answers: specification and method
### 5.1 What gold may rest on
As E1 (README, "Specification sources"), plus the design documents of the readers E2 adds:
`docs/core-0.4/stage-a1.md`, `stage-a2.md` (frames, transforms, `where`), `stage-b.md` (events, `causes_of`,
`effects_of`, `explain`, `changes`, `process_steps`), `stage-c.md` (measurement, units, comparison), and
`stage-d3-design.md` (calibration at measurement time). **Not allowed:** `src/`, `tests/`, `probes/` and their
outputs, results, or calling any reader.

### 5.2 Reader contracts before authoring
E1's `reader-docs.md` is the documentation strings copied from the implementation. For E2 that is weaker, because the
new readers have richer outputs (poses with ranges, comparison classes, effect checks). Proposed:
1. Write `benchmark/e2/spec/reader-contracts.md` **from the design documents** (each statement cited to a section),
   using documentation strings only as a supplement. Where a docstring and its design document differ, the contract
   records the difference and **stops for the owner's decision**; it does not pick one.
2. The owner approves the contracts before any question is written. This is the step that makes the gold independent
   of the implementation's own description of itself.

### 5.3 Authoring protocol
- **Authors:** one author per two families (three authors), spec-only, as E1: no access to the implementation,
  tests, probes, outputs or results, and no reader calls.
- **Each question records:** the fixture; the CQ form; its class (A, H or G); the expected answer field by field; the
  plan with intermediate answers (X); `required_evidence` and `forbidden_evidence`; the specification citations; a
  justification; the uncertainty; the adversarial flag and the difficulty.
- **Numbers:** geometry and unit gold (composed transforms, converted values, uncertainty bounds) is computed by the
  author **by hand-derived formula** in a small calculation sheet beside the question (`benchmark/e2/calc/`), using
  only the formulas in the design documents and standard mathematics. It must not import the library. A second author
  recomputes every numeric answer independently; any difference beyond the stated tolerance is adjudicated before the
  gold is frozen.
- **Tolerances:** stated per question (for example 1e-9 m for exact composed translations, 1e-6 rad for rotations),
  never chosen after a run.
- **Two-author agreement:** for non-numeric fields, a second author answers a random 20 % of each family blind, and the
  agreement is reported (Cohen's kappa per field type). E1 did not measure this.
- **Freeze:** gold, fixtures, contracts and calculation sheets are committed **before the harness first runs a
  question**, and the commit is named in the results (as E1 `d0f0aa2`).

### 5.4 Harness prerequisites (E2 implementation work, not done now)
- `attest` with `params`; fixture steps for `position`, `relate_frames`, `anchor_frame`, `define_unit`,
  `define_quality_kind`, `measure`, `claim_cause`, `claim_effect`, `describe_occurrence`, `record_event`, with names a
  fixture can refer to (so that initiates/terminates can name their proposition);
- templates and answer extractors for `where`, `transform_between`, `poses`, `frame_info`, `measurements`,
  `compare_measurements`, `measurement_calibration`, `causes_of`, `effects_of`, `explain`, `changes`,
  `process_steps`, `before`, `convert`;
- multi-step plans: a plan runner that calls each reader in order and records every intermediate answer;
- harness tests for each new step and extractor, as for E1. **The harness must not change any reader**; if a reader
  cannot be called as the plan needs, that is a gap.

### 5.5 Scoring and adjudication
- **Correct:** every expected field matches (sets unless ordered; numbers within the stated tolerance), on both query
  paths, which must agree.
- **Evidence:** recall and precision of `required_evidence`, reported separately, with `forbidden_evidence` a hard
  failure (it means an answer leaked something it must not cite).
- **Failure categories:** implementation defect; specification ambiguity (both readings defensible); gold error; gap
  (reclassified to G with evidence); harness error. Every failure is adjudicated in writing before results are
  reported. As in E1, clarifications never edit frozen gold: they go into a clarifications file and a revised
  evaluation reported **beside** the original.
- **Performance:** each question's latency, queries and transactions are recorded (section 7 criterion 6). Slow is
  reported, not scored as wrong.

## 6. Benchmark coverage after E2 (proposed)
| Area | E1 | E2 (proposed) |
|---|---:|---:|
| identity, roles, offices, places, calibration status, variant worlds | 272 | (unchanged; kept frozen) |
| spatial transformations | 0 | 25 |
| frames and poses | 0 | 35 |
| measurements and units | 0 (24 calibration-status) | 35 |
| causal claims and explanations | 0 | 30 |
| process steps | 0 | 25 |
| multi-step | 0 (every E1 question uses one reader) | 30 |
| gap probes (not scored) | 0 | about 25 |

## 7. Proposed acceptance criteria for E2
1. **Independence:** contracts approved, gold frozen and committed before the first run; no gold value traceable to
   system output (checked by the commit order, as E1).
2. **Conformance:** at least 95 % of scored questions correct in each family on the original frozen evaluation, and
   every failure adjudicated. Any confirmed implementation defect is registered with a reproduction, whatever the
   percentage.
3. **Path agreement:** 100 % of answers identical on the selective and full-load paths; zero harness errors.
4. **Evidence:** evidence recall at least 0.9 per family; zero forbidden-evidence hits.
5. **No fabrication at the gaps:** every gap probe that calls an existing reader gets UNKNOWN or an explicit refusal,
   never a definite answer the model has no basis for.
6. **Performance budget:** no scored question above the budget set from the entry baseline (proposed: 5 s on the
   reference-size fixtures, and query counts recorded); questions over budget are listed under DI-9.
7. **Frozen history kept:** E1 original 267/272 and revised 272/272 unchanged and reported beside E2.
8. **Two-author agreement** reported per family (no threshold proposed for this first measurement).

## 8. Decisions for review
| # | Decision | Recommendation |
|---|---|---|
| E2-D1 | Scope: the six families, about 180 scored questions and about 25 gap probes | approve as proposed |
| E2-D2 | Classification A/H/G before authoring, and rule G-1 (gaps are never reasoning failures) | approve |
| E2-D3 | Reader contracts written from design documents and approved before authoring (5.2) | approve: this closes E1's weakest point (gold resting on the implementation's own docstrings) |
| E2-D4 | Numeric gold by independent calculation sheets, recomputed by a second author (5.3) | approve |
| E2-D5 | Harness extensions listed in 5.4 as the first E2 implementation step (harness only; no reader change) | approve |
| E2-D6 | Acceptance criteria in section 7, including the 95 % threshold and the 5 s budget | owner to set the thresholds |
| E2-D7 | E2 stays development-tier, like E1; the external sealed evaluation stays deferred | confirm |

## 9. Evidence for the gaps
The full inventory, with file and line references for every gap and every reader, is kept with the entry records:
[stage-e-entry/e2-capability-inventory.md](stage-e-entry/e2-capability-inventory.md).
