# E2 gaps and approved-unimplemented capabilities (author pack)

A **gap** is a capability the model does not provide. An **approved-unimplemented** capability is one whose semantics is approved (contracts §0.11) but which no reader provides yet. Questions on either are class G probes: never scored for conformance, and they check only that nothing is fabricated in the capability's place.

## Gaps

| Gap | What is missing |
|---|---|
| GAP-SPATIAL-1 | no uncertainty on transforms. |
| GAP-SPATIAL-2 | only conservative range propagation through rotations |
| GAP-SPATIAL-3 | no rotation representations other than quaternions. |
| GAP-SPATIAL-4 | no length/angle units on spatial content. |
| GAP-SPATIAL-6 | no shapes, extents or geometry |
| GAP-SPATIAL-7 | no distance/relative-position reader. |
| GAP-SPATIAL-8 | `holds` cannot single out one position |
| GAP-SPATIAL-9 | derived poses and transforms report no validity interval or knowledge time |
| GAP-FRAME-1 | anchoring has no geometric effect. |
| GAP-FRAME-2 | `move()` updates places, not frames. |
| GAP-FRAME-3 | no motion, interpolation or trajectories. |
| GAP-FRAME-4 | no frame-hierarchy reader. |
| GAP-FRAME-5 | no frame-over-time history reader. |
| GAP-FRAME-6 | parts are not positioned through their assembly. |
| GAP-MEAS-1 | no comparison of a measurement against a specification, tolerance or design value (no pass/fail). |
| GAP-MEAS-2 | no condition ontology. |
| GAP-MEAS-3 | no coverage-level harmonisation. |
| GAP-MEAS-4 | no combination or estimation. |
| GAP-MEAS-5 | unit model is single-dimension affine only. |
| GAP-MEAS-6 | `has-quality` is not a functional slot. |
| GAP-MEAS-7 | no "latest/current value" or trend reader. |
| GAP-MEAS-9 | calibration reference is text, not a link |
| GAP-MEAS-10 | no "undermines" evidence relation |
| GAP-MEAS-11 | formal derivation provenance missing |
| GAP-MEAS-12 | categorical measurements |
| GAP-MEAS-13 | no declaration of a constant quantity |
| GAP-CAUSE-1 | no causal chain query. |
| GAP-CAUSE-2 | no forward causal reader ("what did X cause?"). |
| GAP-CAUSE-3 | no counterfactual intervention operator. |
| GAP-CAUSE-4 | no automatic causal inference |
| GAP-CAUSE-5 | no causal strength, probability, mechanism type or enabling/preventing distinction. |
| GAP-CAUSE-6 | no failure propagation through dependencies |
| GAP-CAUSE-7 | derived (rule-based) causal conclusions have no derivation record |
| GAP-PROC-1 | no explicit step order. |
| GAP-PROC-2 | no procedure/plan type (prescriptive steps) distinct from executed occurrences. |
| GAP-PROC-3 | no preconditions or postconditions |
| GAP-PROC-4 | no duration reader. |
| GAP-PROC-5 | processes are not modelled as ongoing/homogeneous |
| GAP-PROC-6 | `process_steps` is one level. |
| GAP-PROC-7 | step completion / missing-step detection absent. |
| GAP-MULTI-1 | no general composition or query interface over readers. |
| GAP-MULTI-2 | no "at the time of event E" helper. |
| GAP-MULTI-3 | no failed-measurement concept |
| GAP-MULTI-4 | no causal chains |
| GAP-MULTI-5 | transitive parts do not carry poses |
| GAP-MULTI-6 | no derivation record for a chained answer |

GAP-SPATIAL-5 is withdrawn (by design: frames have no same-as identity). Performance items are not gaps for authoring.

## Approved but unimplemented (probe with `"accept"` including `"absent"`)

| Decision | Reader | Reserved field |
|---|---|---|
| SD-CORE-3 | `facts_about` | `constraint_support` on entries |
| SD-SPA-1 | `transform_between`, `where` | `chain_tolerance` |
| SD-SPA-2 | `transform_between` | `basis` (convention-derived identity) |
| SD-CAU-1 | `effects_of` | `attribution` (unique / ambiguous) on entries |
| SD-CAU-2 | `explain` | `timing` on `initiated_by` entries; top-level `alternatives` |
| SD-CAU-4 | `changes` | `attestations` on explanation entries |
| SD-CAU-9 | `effects_of`, `changes` | `applies`, `occurrence_status` |
| SD-CAU-10 | `interval`, `process_steps`, `effects_of` | `usable_accounts` |

A scored question must never expect these fields.
