# E2 competency questions (author pack)

From `docs/stage-e/stage-e2-evaluation-design.md` section 3 (approved, E2-D1/D2). Each CQ is a question form; your assignment says which forms and how many. The class column is the design's; your assignment's class is authoritative where they differ.

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

