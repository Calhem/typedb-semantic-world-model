# Stage E2 capability inventory (typedb-semantic-world-model)

Read-only inventory, compiled 2026-11-20 from branch `feature/stage-e-entry-validation` at `8663cb2`. Nothing was run
against a database. All paths below are relative to the repository root.
Line numbers are `def` lines.

## 0. What counts as public API here

- `src/worldmodel/__init__.py:1-11` exports `WorldModel`, `connect`, `Window`, `SYSTEM`, `proposition_key`,
  `proposition_id`, the exception classes, the module tuples (`PHYSICAL_MODULES`, `DYNAMICS_MODULES`,
  `QUALITY_MODULES`, `CORE_MODULES`), `Profile`, `ProfileError`, `PROFILES`, and the profile modules `mechanical`,
  `organisation`, `laboratory`.
- `WorldModel` (`model.py:160`) mixes in `JudgementMixin` (judgement.py), `PhysicalMixin` (physical.py),
  `DynamicsMixin` (dynamics.py), `QualitiesMixin` (qualities.py), `AgencyMixin` (agency.py) and `ProfileMixin`
  (profiles.py). Every public mixin method is a public `WorldModel` method.
- `worldmodel.spatial` (pure functions: quaternions, `Transform`) and `worldmodel.semantics` (`Status`, `Answer`) are
  **not** in `__all__`. They are importable modules with public names, and readers return their objects (`Transform`,
  `Status`).
- Optional schema modules: physical (`core-0.4-a`, `-a2`), dynamics (`core-0.4-b`) and qualities (`core-0.4-c`) are
  opt-in (`model.py:51-57`). The E1 harness installs `CORE_MODULES` (all of them) (`evaluation/loader.py:101`).

### Status vocabularies a reader can return

| Vocabulary | Values | Where defined |
|---|---|---|
| Answer status (`Status`) | `OBSERVED`, `ASSERTED`, `STIPULATED`, `INFERRED`, `PRESUMED`, `DISPUTED`, `UNKNOWN`, `NOT_YET_KNOWN`. **`OBSERVED` and `PRESUMED` are never produced** (no code constructs them; grep for `Status.OBSERVED` / `Status.PRESUMED` finds nothing). Observations are reported `ASSERTED`. Mixed support is labelled STIPULATED > ASSERTED > INFERRED (`semantics.answer_status`, semantics.py:162) | semantics.py:12 |
| Canonical judgement | `established`, `disputed`, `not holding`, `pending`, `unknown`, each with a reason (`polarity`, `constraint`, `denied`, `ended`, `overridden`, `excluded`, `not_yet_effective`, `end_unknown`, `not_supporting`, `unaccepted`, `no_evidence`, `silent`) | judgement.py:29-42 |
| Claim label (causes_of, effects_of, replacement) | `accepted`, `disputed`, `denied`, `unreviewed`, `rejected`, `retracted` (sort order in dynamics.py:703) | `judgement.claim_label`, judgement.py:211 |
| Applicability (capable, authorised, calibration_status) | `established`, `denied`, `expired`, `not yet effective`, `disputed`, `not established` | agency.py:56; reader-docs.md:100-118 |
| Occurrence status | `accepted`, `denied`, `disputed`, `not established` | dynamics.py:410 |
| Account state | `accepted`, `unreviewed`, `rejected`, `none` | dynamics.py:57 |
| Measurement acceptance | `accepted`, `unreviewed`, `rejected`, `retracted`, `superseded`; plus `usable` (bool) and `kind` (`measurement` / `statement`) | qualities.py:193-234 |
| Measurement pair relation | `possibly compatible`, `incompatible`, `incomparable` (+ reason) | qualities.py:236-288 |
| Position judgement (`where`) | `judgement`: `conflicting`, `compatible`, `single`, None; conflict kinds `disjoint ranges`, `orientations differ` | physical.py:381-447 |
| Transition category (`changes`) | `world-state`, `judgement`; `within`: `certain`, `possible`; explanation `ambiguous` | dynamics.py:162 |
| Event-role judgement | `established`, `disputed`, `union` (+ `multiplicity` one / set, dispute reasons) | reader-docs.md:62-80 |

Rules an evaluator needs (from `benchmark/e1/spec/reader-docs.md` and TEMPLATES.md "Vocabularies"):
- `not holding` = an accepted denial covers t (`denied`) or an accepted holding ended before t (`ended`).
  `pending` = only an unreviewed attestation would decide. `unknown` = nothing decides (`not_yet_effective`,
  `end_unknown`, `unaccepted`, `no_evidence`). `UNKNOWN` (something visible, nothing applicable) and `NOT_YET_KNOWN`
  (nothing visible at the knowledge time) stay distinct (D-C-5).
- Stances `doubts` and `hypothesises` never support an answer (semantics.py:26). In hypothetical and simulated worlds
  the default stance is `stipulates`, so answers there are `STIPULATED` (reader-docs.md:139-153).
- Nearest-world attestations win; an assertion and a denial at the same world depth are a dispute
  (`semantics.decide`, semantics.py:173).
- `INFERRED` currently means either (a) a rule the model applies itself (frame chains, rule `frame-transform/v1`;
  `exists` from participation) or (b) any accepted attestation with basis `inference`, with no rule or premises
  recorded (DI-7, open).
- An accepted account does not establish that its occurrence happened; a claimed effect is not a state change; a
  capability never establishes an action (reader-docs.md module notes, 404-475).
- Readers that are **not** documented in reader-docs.md (E2 authors would need them added): `where`,
  `transform_between`, `poses`, `frame_info`, `composition`, `contents`, `measurements`, `compare_measurements`,
  `convert`, `explain`, `process_steps`, `before`, `interval`, `events`, `history`, `facts_about`, `value_of`,
  `dependencies`, `actions_of`, `check_action`, `laboratory.measurement_calibration`, `laboratory.interpretations`,
  `mechanical.connections`. (`changes`, `causes_of`, `effects_of`, `provenance`, `calibration_status` are documented.)

---

## 1. Spatial transformations

### Public functions and methods

| Name and signature | Returns | Statuses | Ref |
|---|---|---|---|
| `WorldModel.relate_frames(world, parent, child, translation, rotation=(1,0,0,0), **attest)` | attestation id of `frame-transform(parent, child)` with params tx,ty,tz,qw..qz (child pose in parent: p_P = R(q) p_C + t). Rejects parent == child, non-finite translation, non-unit quaternion (norm off by > 1e-9) | writer | physical.py:69 |
| `WorldModel.transform_between(world, source, target, t, as_of=None, perspective=SYSTEM, limit=None)` | `{source, target, status, rule: "frame-transform/v1", transform: Transform or None, chain: [steps with parent, child, direction forward/inverse, translation, rotation, support, disputed], frames, reason, search: {complete, truncated, limit, edges_examined, frames_reached, hops, cycle, relevant_edges, verified, inconsistent: [gaps]}}`. BFS shortest chain, edges usable forward or inverted; every edge on any simple source-target chain is checked for agreement (1e-9 m and angle tolerance) | `INFERRED` (chain found and verified; also source == target), `DISPUTED` (chains disagree, or a disputed transform on a relevant chain; no transform chosen), `UNKNOWN` (no chain, or search truncated; a truncated search that reached the target returns an unverified candidate) | physical.py:371 (resolver `_resolve` physical.py:314) |
| `WorldModel.frames_linked_in_database(world, frame)` | ids of frames connected by frame-transform records (TypeDB function `frames_linked`); ignores time, acceptance, perspective (inspection only) | none (structural) | physical.py:449; schema/core/core-0.4-a2.tql:12 |
| `physical.yaw(radians)` | unit quaternion for rotation about +z (module-level, not exported from `__init__`) | n/a | physical.py:46 |
| `spatial.qmul(a, b)`, `qconj(q)`, `rotate(q, v)` | Hamilton product, conjugate, active rotation of a vector | n/a (pure) | spatial.py:30, 40, 45 |
| `spatial.angular_separation(a, b)`, `same_rotation(a, b, tol)` | angle (0..pi) between orientations; agreement under tolerance | n/a | spatial.py:51, 57 |
| `spatial.Transform(q, t)`: `.apply(p)`, `.then(inner)` (composition self ∘ inner), `.inverse()`, `.close_to(other, tol, angle_tol)`, `.gap(other)` | rigid transform object; composition and inverse are computed, never stored | n/a | spatial.py:63-84 |
| `spatial.map_box(transform, box)`, `boxes_overlap`, `boxes_equal`, `params_compatible`, `angle_about_z(q)` | conservative 8-corner box mapping; range overlap; parameter compatibility; z-angle for display | n/a | spatial.py:90-126 |

Conventions (spatial.py:1-19, docs/core-0.4/stage-a2.md:16): right-handed frames, metres, radians, unit quaternions
(w,x,y,z), Hamilton, active rotation. Default `ANGLE_TOLERANCE = 1e-9` rad and `TOLERANCE = 1e-9` m.
`frame-transform` is a functional slot per (child, parent) pair: two different accepted transforms for one pair are
DISPUTED (model.py:95-97, physical.py:197-207).

### Not implemented

- **GAP-SPATIAL-1: no uncertainty on transforms.** `relate_frames` stores exact tx..qz (physical.py:74-79); only
  positions carry ranges. Orientation uncertainty is a per-question policy, not a stored per-claim value
  (docs/core-0.4/stage-a2.md:240).
- **GAP-SPATIAL-2: only conservative range propagation through rotations** (8-corner bounding box,
  spatial.py:90-94); ranges widen along rotated chains, so conflicts can be missed (stage-a2.md:239).
- **GAP-SPATIAL-3: no rotation representations other than quaternions.** No Euler / roll-pitch-yaw / axis-angle /
  rotation-matrix input or output (grep for `euler`, `axis_angle`, `roll`, `matrix` in src and schema: no hits). Only
  `yaw()` (about +z) and `angle_about_z()` (display only, for level rotations).
- **GAP-SPATIAL-4: no length/angle units on spatial content.** `positioned-in` and `frame-transform` have no unit
  role; metres and radians are fixed conventions (schema/core/core-0.4-a.tql:6-10, 21-24). `convert()` (Stage C) is
  not applied to positions or transforms.
- ~~**GAP-SPATIAL-5: frame chains are judged without same-as identity.**~~ **Withdrawn (LABS-1.063, reader-contract
  review D-TB-4):** not a gap. Same-as relates particulars only, so frames cannot be declared the same; frame chains
  are unchanged by design (pre-e-increment-b.md point 6; pre-e-identity-design.md). The code comment this entry quoted
  was stale and is corrected.
- **GAP-SPATIAL-6: no shapes, extents or geometry** (no containment of a point in a volume, no distance between
  objects other than via caller arithmetic) (stage-a2.md:259; stage-a1.md:131-139).
- **GAP-SPATIAL-7: no distance/relative-position reader.** "How far is A from B" or "pose of A relative to B" needs
  the caller to combine two `where` answers; there is no reader for it (no matching method in physical.py).
- **GAP-SPATIAL-8: `holds` cannot single out one position** (D-A2-5, stage-a2.md:86 and 248); `where` is the only
  position interface.

- **GAP-SPATIAL-9: derived poses and transforms report no validity interval or knowledge time** (registered
  LABS-1.064, from D-TB-6; Plan 9.6). A derived answer says what holds at `t`, not over which interval it holds or
  from when it was known. Questions on it are G probes.

### E1 coverage
None. No E1 question, fixture or template uses `positioned-in`, `frame-transform`, `where` or `transform_between`
(grep of `benchmark/e1/questions` and `fixtures`: 0 hits). Listed as not reached in
docs/stage-e/stage-e1-overnight-report.md:142.

---

## 2. Frames

### Public functions and methods

| Name and signature | Returns | Statuses | Ref |
|---|---|---|---|
| `WorldModel.add_entity("spatial-frame", name, ...)` | a frame (a `reference-system`) | writer | model.py:571 |
| `WorldModel.anchor_frame(world, frame, anchor, **attest)` | attestation of `anchored-to(frame, anchor)`; functional slot: one anchor per frame at a time (a second accepted anchor is DISPUTED) | writer | physical.py:81; model.py:95 |
| `WorldModel.position(world, thing, frame, x, y, z, orientation=None, **attest)` | attestation of `positioned-in(thing, frame)`; each axis exact or (lower, upper) metres; optional orientation quaternion. Functional slot per (frame, positioned) | writer | physical.py:59; model.py:96 |
| `WorldModel.poses(world, thing, t, as_of=None, perspective=SYSTEM)` | list per frame statement holding at t: frame, x/y/z ranges, orientation, status, support, conflicts, support_status | from facts_about: `ASSERTED`/`STIPULATED`/`INFERRED`/`DISPUTED` per entry | physical.py:91 |
| `WorldModel.frame_info(world, frame, t, as_of=None, perspective=SYSTEM)` | name, `anchored_to` [{anchor, status}], `parents` / `children` transforms (as stored, with status and support), things positioned in it | per-entry status | physical.py:107 |
| `WorldModel.where(world, thing, frame, t, as_of=None, perspective=SYSTEM, angle_tolerance=1e-9, limit=None)` | `{thing, frame, status, candidates: [x/y/z mapped ranges, orientation, status, stated_in, stated, direct, rule, chain, reason, search, verified], conflicts, conflict_details, angle_tolerance, verified, reason, judgement, incomparable, alternatives}`. Every holding position is a candidate (direct or mapped through the shortest chain); candidates are compared, never merged | `STIPULATED` / `ASSERTED` (direct, by basis), `INFERRED` (only derived candidates), `DISPUTED` (disjoint ranges, orientations beyond tolerance, or a disputed chain), `UNKNOWN` (positions exist but none comparable, or a search truncated), `NOT_YET_KNOWN` (no position statement visible) | physical.py:381 |
| `WorldModel.transform_between(...)` | see family 1 | see family 1 | physical.py:371 |
| `WorldModel.contents(world, place, t, ...)` | place-based containment tree (located-at, part-of of places) | `value_at` status | physical.py:142 |
| `WorldModel.value_at(world, "located-at", thing, t, ...)` | the place (not a frame) the thing is at | Answer status | model.py:1179 |
| `WorldModel.move(world, thing, to, at, actor=None, kind=None, as_of=None, attester=SYSTEM)` | records a movement event; ends the attester's prior `located-at`; new `located-at` from `at`; refuses with `MovementConflict` when the origin is ambiguous | writer (E1 `move` template) | model.py:1368 |
| `WorldModel.changes(world, subject, t1, t2, ...)` | transitions of the subject's slots, including `positioned-in` and `anchored-to` (any functional slot keyed on the subject) | `world-state` / `judgement` categories | dynamics.py:162 |

Time: frame transforms, anchors and positions are ordinary attestations with valid intervals, so
`where(..., t)` and `transform_between(..., t)` use whatever holds at t. A changing transform is a new attestation (and
a new proposition: U-3, stage-a2.md:245).

### Not implemented

- **GAP-FRAME-1: anchoring has no geometric effect.** `anchored-to` is only reported (`frame_info`, physical.py:115);
  it is not used in frame chains (`_frame_edges` reads only `frame-transform`, physical.py:189-208). A frame anchored
  to a thing does not move when the thing's pose changes, and a thing's `positioned-in` pose is not turned into a
  frame-transform for its anchored frame.
- **GAP-FRAME-2: `move()` updates places, not frames.** It writes `located-at` only (model.py:1393-1396); it never
  writes `positioned-in` or `frame-transform`. Place location and frame position are two separate systems with no link.
- **GAP-FRAME-3: no motion, interpolation or trajectories.** Between two attested poses nothing is inferred (grep for
  `velocity`, `trajectory`, `motion`, `interpolat`, `extrapolat`: no hits). The pose is UNKNOWN in gaps.
- **GAP-FRAME-4: no frame-hierarchy reader.** There is no "tree of frames" or "root frame of F" method; hierarchy is
  visible only one hop at a time (`frame_info` parents / children) or as an unjudged set (`frames_linked_in_database`).
  `transform_between` gives one chain, not the hierarchy.
- **GAP-FRAME-5: no frame-over-time history reader.** No method lists how F's transform to its parent changed over an
  interval except the generic `changes(world, frame, t1, t2)` and `history(world, frame)`.
- **GAP-FRAME-6: parts are not positioned through their assembly.** `part-of` does not imply a pose; a part's position
  in a vehicle frame needs its own `positioned-in` or a frame anchored to it with a transform (no derivation in
  physical.py).
- (Shared with family 1: GAP-SPATIAL-5 identity, GAP-SPATIAL-6 no geometry.)

### E1 coverage
- No frame questions (0). Place-based location is heavily covered: `value_at` on `located-at` **37**, `holds` on
  `located-at` **14**, `move` **12** (temporal 10, cross-domain 2).

---

## 3. Measurements

### Public functions and methods

| Name and signature | Returns | Statuses | Ref |
|---|---|---|---|
| `WorldModel.define_unit(name, dimension, si_factor=1.0, si_offset=0.0, id=None)` | unit id; si = raw × factor + offset (affine, so °C works) | writer | qualities.py:49 |
| `WorldModel.define_quality_kind(name, dimension=None, id=None)` | quality-kind id (numeric with dimension, or categorical without) | writer | qualities.py:59 |
| `WorldModel.si_unit(dimension)` | the dimension's SI unit id (factor 1, offset 0); raises if none | n/a | qualities.py:83 |
| `WorldModel.convert(value, unit, to=None)` | value in `to` (default SI); raises across dimensions | n/a | qualities.py:95 |
| `WorldModel.measure(world, bearer, quality, value, unit, uncertainty, k=2.0, start=None, end=None, instrument=None, operator=None, conditions=(), calibration=None, attester=SYSTEM, occurrence=None, persists=False, supersedes=None, id=None)` | `{activity, result, content, produced, reports, range: (lo, hi) SI, coverage_level}`. Writes atomically: activity (event kind `measurement`, patient/actor/instrument), result record (raw value, raw unit, u, k, conditions, calibration ref), `has-quality` content with range [v − ku, v + ku] in SI, basis observation; `persists` makes it hold until superseded; `supersedes` corrects | writer | qualities.py:108 |
| `WorldModel.evidence_of(attestation)` | result-record ids it rests on (structural) | none | qualities.py:165 |
| `WorldModel.measurements(world, bearer, quality, t=None, as_of=None, perspective=SYSTEM)` | every stated value: attestation, content, `kind` measurement/statement, SI range, unit, coverage_level, attester, basis, acceptance, usable, valid interval, records (raw value/unit, u, k, conditions, calibration, report label, activities with start/end/operator/instrument/occurrences) | acceptance vocabulary (no `Status`) | qualities.py:193 |
| `WorldModel.compare_measurements(world, bearer, quality, t=None, ...)` | `{status, measurements (usable), pairs: [{a, b, relation, reason}], alternatives (unaccepted), statements (design values, listed apart)}`. Incomparable when SI units, coverage levels (> 1e-6 apart), condition texts or non-overlapping valid times differ | `DISPUTED` (any comparable pair incompatible), else `ASSERTED`/`STIPULATED`/`INFERRED` by basis of accepted measurements, `UNKNOWN` (values but none usable), `NOT_YET_KNOWN` (nothing) | qualities.py:236 |
| `laboratory.register_certificate(wm, name, reference=None, id=None)` | certificate (information object with `calibration-ref`) | writer | laboratory.py:180 |
| `laboratory.calibrate(wm, world, certificate, instrument, start=None, end=None, attester=SYSTEM, polarity=True, **attest)` | `calibration-of` attestation resting on the certificate; default holds until superseded (CLARIFICATIONS.md C2) | writer | laboratory.py:194 |
| `laboratory.calibration_status(wm, world, instrument, t, ...)` | holds / status / judgement + every certificate naming the instrument with reference, own judgement, evidence | applicability vocabulary + `Status` | laboratory.py:216 |
| `laboratory.measurement_calibration(wm, world, bearer, quality, t=None, ...)` | per measurement × record × instrument: acceptance, usable, activity, `at` (activity start earliest), stated reference, attested calibration_status at that time, `reference_check` (exact text). Never changes a measurement's acceptance | applicability vocabulary per row | laboratory.py:254 |
| `laboratory.interpret(wm, world, record, type, roles, attester, tentative=False, ...)` / `interpretations(wm, world, record, t, ...)` | an analyst's conclusion resting on a record (testimony or hypothesis; basis `inference` refused) / everything resting on a record with mode and `supports_answer` | writer / per-row judgement | laboratory.py:279, 295 |
| `laboratory.provenance(wm, world, sample, t, ...)` | constitution chain, sampling accounts, existence, locations of a sample | per-link judgement | laboratory.py:108 |

### Not implemented

- **GAP-MEAS-1: no comparison of a measurement against a specification, tolerance or design value (no pass/fail).**
  `compare_measurements` lists statements "apart and never compared with measurements" (qualities.py:241-242). No
  nominal value, tolerance band, limit or conformity verdict exists (grep `nominal`, `spec limit`, `pass`, `fail`,
  `within_tolerance`: no hits). "The part whose measurement failed" has no representation unless a source attests a
  category (e.g. `classified-as(part, failed)`) itself.
- **GAP-MEAS-2: no condition ontology.** Conditions are exact text; any difference is "incomparable" (D-C-7,
  docs/core-0.4/stage-c.md:38 and 244; stage-d3-design.md:91 G-4). Conditions are not linked to attested states of the
  set-up, and carry no units or tolerances.
- **GAP-MEAS-3: no coverage-level harmonisation.** Measurements at different k are "incomparable"
  (qualities.py:274-276); no rescaling to a common k, although u and k are stored on the record.
- **GAP-MEAS-4: no combination or estimation.** Nothing is averaged, weighted or reconciled (qualities.py:11-13,
  "never reconciled"); no best estimate of a quality.
- **GAP-MEAS-5: unit model is single-dimension affine only.** `dimension` is a plain string; no compound or derived
  units, no dimensional algebra (e.g. N = kg·m/s²), no prefixes beyond separately defined units (qualities.py:49-56,
  95-104). Conversion across dimensions is refused.
- **GAP-MEAS-6: `has-quality` is not a functional slot.** Only `located-at`, `anchored-to`, `positioned-in` and
  `frame-transform` are slots (model.py:86, 95-97), so `holds`/`facts_about` do not dispute two different stated
  values of one quality; disagreement is reported only by `compare_measurements`.
- **GAP-MEAS-7: no "latest/current value" or trend reader.** `measurements(t=None)` lists every value; with `t` it
  filters to those holding at t. No time series, drift or rate-of-change reader.
- **GAP-MEAS-8: measurement reads are N+1** (D-C-6, stage-c.md:37 and 243; DI-9 deferred-issues.md:271): batching
  deferred. `measurement_calibration` cost 411 queries in bench-d3 (deferred-issues.md:274-276). Relevant to E2
  question budgets.
- **GAP-MEAS-9: calibration reference is text, not a link** (stage-d3-design.md:93 G-6); only exact-text checking.
- **GAP-MEAS-10: no "undermines" evidence relation** (stage-d3-design.md:90 G-3): rests-on records support only.
- **GAP-MEAS-11: formal derivation provenance missing** (DI-7, deferred-issues.md:205-235): a derived quantity (e.g.
  computed from two measurements) cannot name its rule and premises.

- **GAP-MEAS-12: categorical measurements** (newly identified LABS-1.064, from SD-MEA-3). `measurements` and
  `compare_measurements` cover interval-valued quantities only; categorical `has-quality` values ("open", a colour)
  are read through `holds` and `facts_about`, with no measurement record, comparison or coverage semantics.
- **GAP-MEAS-13: no declaration of a constant quantity** (newly identified LABS-1.064, from SD-MEA-4). Measurements at
  disjoint valid times are always incomparable, because nothing can declare a quantity constant (for example the rest
  mass of a sealed reference).

### E1 coverage
- No question on `measure`, `measurements`, `compare_measurements`, `has-quality` or units (0 hits).
- Calibration is covered: template `calibrated` (`laboratory.calibration_status`) **24** questions (laboratory 22,
  cross-domain 2), fixtures lab-1, lab-2 (+ cross-domain). Sampling covered via `event_role` on `sampling:*` roles
  (**6**) and `exists` (laboratory 3).

---

## 4. Causal relationships

### Public functions and methods

| Name and signature | Returns | Statuses | Ref |
|---|---|---|---|
| `WorldModel.claim_cause(world, cause, effect, polarity=True, **attest)` | `causes(cause, effect)` attestation (descriptions or occurrences in any mix; timeless, until superseded; polarity False = denial). Never inferred | writer | dynamics.py:397 |
| `WorldModel.claim_effect(world, event, kind, type, roles, params=None, polarity=True, **attest)` | `initiates`/`terminates(event, outcome: proposition id)` claim. Asserted effect only | writer | dynamics.py:89 |
| `WorldModel.record_event(world, roles, start, end=None, kind=None, ends=(), effects=(), ...)` | description + its attestation + ended attestations + new effect attestations (state written directly, not via claims) | writer | model.py:1347 |
| `WorldModel.causes_of(world, effect, t, as_of=None, perspective=SYSTEM)` | list of claims: cause, effect, level (description/occurrence/mixed), lifted (via accepted describes links), lifted_via, cause_occurrences, `occurrences` {id: occurrence_status}, `applies` (False if an involved occurrence is denied, None if disputed, True otherwise), judgement, status, claimed_by, attestations. Sorted accepted, disputed, denied, unreviewed, rejected, retracted | claim label + `Status` per claim | dynamics.py:653 |
| `WorldModel.effects_of(world, event, t, as_of=None, perspective=SYSTEM)` | per initiates/terminates claim: kind, outcome, claim label, claim_status, claimed_by, attestations, `state` {before (Answer just before start), after (Answer at end), accepted_change bool} | claim label; Answer statuses | dynamics.py:134 |
| `WorldModel.explain(world, type, roles, t, as_of=None, perspective=SYSTEM)` | `{content, holds: Answer, initiated_by: [events claimed to initiate it that ended by t, each with claim judgement, occurrences and `causes`: causes_of on the event and its occurrences]}`. One step back only | Answer + claim labels | dynamics.py:706 |
| `WorldModel.changes(world, subject, t1, t2, ...)` | transitions with explanations: accepted initiates/terminates claims fitting the transition (`ambiguous` when several fit) | categories as in section 0 | dynamics.py:162 |
| `WorldModel.occurrence_status(world, occurrence, t, ...)` / `exists(...)` | whether a happening happened (only from its own existence attestations) | occurrence status / Answer | dynamics.py:410; model.py:1504 |
| `WorldModel.before(world, a, b, ...)` | True / False / None temporal succession (explicitly not causation) | n/a | dynamics.py:384 |
| `mechanical.replacement`, `laboratory.provenance`, `organisation.official_act` | profile reports that include `effects_of`-style claimed effects and occurrence statuses | per field | mechanical.py:99; laboratory.py:108; organisation.py:223 |
| Hypothetical / simulated worlds: `create_world(name, kind="hypothetical", base, branch_at, knowledge_at)` + `attest`/`deny` in the variant | variant inherits base attestations (base valid time up to `branch_at`, base knowledge as of `knowledge_at`); variant statements default to `stipulates` and, being nearer, win over the base | `STIPULATED` etc. | model.py:585; semantics.py:173 |

### Not implemented

- **GAP-CAUSE-1: no causal chain query.** "The plan's 'list asserted links along a chain'" is deferred; `explain`
  stops one step back (docs/core-0.4/stage-b.md:33, 462-463). `causes_of` docs: "Nothing is inferred from order or
  chained" (dynamics.py:658-659). No transitive cause closure.
- **GAP-CAUSE-2: no forward causal reader ("what did X cause?").** `causes_of` is keyed on the effect only
  (`entry.about("effect")`, dynamics.py:677). No `effects`-of-a-cause reader for `causes` claims (`effects_of` reads
  initiates/terminates, not `causes`). The generic `facts_about(world, cause, t)` may list `causes` contents in which
  the subject is the cause, but without describes-lifting or occurrence checks (not verified by running).
- **GAP-CAUSE-3: no counterfactual intervention operator.** No `intervene`/`counterfactual`/`do` in src or schema
  (grep: no hits). A hypothetical world only holds what is stipulated or inherited; denying an event in a variant does
  not retract its claimed effects or the states attested after it, because states are judged from their own
  attestations, not derived from events (dynamics.py:3-11; effects_of docstring dynamics.py:135-138). "No prediction,
  simulation, automatic causal inference" (stage-b.md:473; agency.py:11-12).
- **GAP-CAUSE-4: no automatic causal inference** from succession, co-occurrence or effects (stage-b.md:473;
  dynamics.py:8-9).
- **GAP-CAUSE-5: no causal strength, probability, mechanism type or enabling/preventing distinction.** `causes` has
  only `cause` and `effect` roles (schema/core/core-0.4-b.tql:13); polarity is the only qualifier. `credence` exists on
  attestations (reader-docs.md:139) but no reader uses it for causation.
- **GAP-CAUSE-6: no failure propagation through dependencies** (`direct_dependencies`: "no transitivity, no failure
  propagation", model.py:1648; mechanical notes reader-docs.md:436-448).
- **GAP-CAUSE-7: derived (rule-based) causal conclusions have no derivation record** (DI-7).

### E1 coverage
- None for `causes_of`, `effects_of`, `explain`, `changes` (0 questions; overnight-report.md:142). No fixture uses
  `causes`, `initiates` or `terminates` directly (`replace_part` fixtures write claimed part-of effects internally:
  15 `replace_part` steps; 6 `take_sample`).
- Indirect: `parts` after replacement accounts (MECH-013/014, X-010), `occurrence_status` **4**, `exists` **9**.
- Hypothetical worlds (the substrate for counterfactual questions): **42** E1 questions are asked in a hypothetical
  world (worlds-perspectives 24, cross-domain 9, identity 4, conflict-provenance 3, laboratory 2), **35** at base
  depth 1 and **7** at depth 2 (nested variant, fixture `world-nested`).

---

## 5. Process steps

### Public functions and methods

| Name and signature | Returns | Statuses | Ref |
|---|---|---|---|
| `WorldModel.account(world, roles, start, end=None, kind=None, occurrence=None, attester=SYSTEM, id=None, type="event", **attest)` | event description + interval attestation + classification + optional describes link | writer | dynamics.py:68 |
| `WorldModel.attest(world, "part-of", {"part": step_occ, "whole": process_occ}, ...)` | how a step is made part of a process (core part-of on occurrences) | writer | model.py:735 |
| `WorldModel.process_steps(world, process, t, as_of=None, perspective=SYSTEM)` | occurrences that are part-of the process at t, **ordered by their earliest description start** (undated last), each with descriptions, start/end Windows, kinds, actors, support, judgement, status (disputed steps listed, never dropped) | per step: `established`/`disputed` + `Status` | dynamics.py:728 |
| `WorldModel.parts(world, whole, t, ..., report=False)` / `composition(...)` | transitive part-of closure / tree; generic, so usable for nested sub-events | established only; `not_traversed` with judgement | model.py:1624; physical.py:129 |
| `WorldModel.interval(world, description, ...)` | (start Window, end Window, record) of an accepted account, or None | n/a | dynamics.py:113 |
| `WorldModel.before(world, a, b, ...)` | certain succession True / False / None | n/a | dynamics.py:384 |
| `WorldModel.events(world, participant=None, ...)` | accepted event descriptions ordered by start window, with kinds and roles | n/a | model.py:1398 |
| `WorldModel.occurrence(world, occurrence, ...)` | merged view: descriptions, participants, accounts, role judgements under event-role constraints | event-role vocabulary | model.py:1432 |
| `WorldModel.actions_of(world, agent, ...)` / `check_action(world, event, capability=None, context=None, ...)` | an agent's action-classified events / structured check (account, kinds, occurrences, agency, capability at start) | per field | dynamics.py:749; agency.py:100 |

The laboratory profile's experiments are classifications whose steps are core `part-of`, read with `process_steps`
(reader-docs.md:470-471).

### Not implemented

- **GAP-PROC-1: no explicit step order.** Order is derived only from description intervals (dynamics.py:745-746); no
  `next`/`precedes`/sequence-number relation (grep `sequence`, `next step`: no hits; no such type in the schema).
  Steps with overlapping or unknown intervals have no stated order.
- **GAP-PROC-2: no procedure/plan type (prescriptive steps) distinct from executed occurrences.** No `procedure`,
  `plan`, `instruction` type in the schema (type list in schema/core and schema/profiles). Hypothetical worlds are
  used as "plans" in E1 (e.g. "reorganisation plan"), but there is no plan-vs-execution comparison reader.
- **GAP-PROC-3: no preconditions or postconditions** (grep `precondition`, `prerequisite`, `postcondition`: no hits).
  `check_action` reports capability at start but concludes nothing (agency.py:100-128).
- **GAP-PROC-4: no duration reader.** Intervals are Windows (earliest/latest bounds); no method computes a duration or
  its bounds (grep `duration`: no hits). Caller arithmetic only.
- **GAP-PROC-5: processes are not modelled as ongoing/homogeneous**; no persistence policy across gaps (v0.2 C9)
  (stage-b.md:34, 464-465).
- **GAP-PROC-6: `process_steps` is one level.** It lists direct part-of steps only (dynamics.py:734-744); nested
  sub-steps need `parts()` (unordered) or repeated calls.
- **GAP-PROC-7: step completion / missing-step detection absent.** No reader says which expected step did not occur.

### E1 coverage
- None for `process_steps`, `before`, `interval`, `events`, `actions_of`, `check_action` (0 questions).
- Event structure is covered through `event_role` (`occurrence`) **47** questions (official-act 26, replacement 13,
  sampling 6, event:actor 2) and `officials` 1.

---

## 6. Multi-step reasoning

### What exists

Fixed compositions inside single readers (each answerable in one call):
- `explain` = holds → initiating-event claims → causes_of (dynamics.py:706).
- `where` = poses → frame chain search → candidate comparison (physical.py:381).
- `laboratory.measurement_calibration` = measurements → activity start → calibration_status at that instant
  (laboratory.py:254).
- `organisation.official_act` = account → occurrence status → appointment, authority, capability, agency at the act's
  start (organisation.py:223).
- `mechanical.replacement` = account → occurrences → effects_of (mechanical.py:99).
- `laboratory.provenance` = constitution chain (all routes) → sampling accounts → existence → locations
  (laboratory.py:108).
- Transitive readers: `parts` (model.py:1624), `dependencies` (model.py:1640), identity closure (`identity`,
  model.py:1028), frame chains (`transform_between`). All perspective-, knowledge-time- and world-aware.
- Variant-world inheritance applies to every reader through the core load (nearest world wins; nested bases).

Chaining several readers otherwise is done by the caller: e.g. `interval(world, E)` → choose t from its Window →
`where(world, part, F, t)` or `value_at(world, "located-at", part, t)`.

### Not implemented

- **GAP-MULTI-1: no general composition or query interface over readers.** Each template in E1 is answered "through
  one public reader" (TEMPLATES.md:3-4); there is no reader that takes a question plan. E2 multi-step questions need
  either a harness-side composition (and gold for every intermediate step) or a new reader.
- **GAP-MULTI-2: no "at the time of event E" helper.** Readers take a valid time t; event times are Windows (earliest,
  latest). Picking t (start earliest? end latest?) is a caller choice the readers do not define, except inside the
  fixed compositions (`measurement_calibration` uses activity start earliest, laboratory.py:265; `effects_of` uses
  start earliest − 1 µs and end latest, dynamics.py:147-150). E2 gold must state which instant is meant.
- **GAP-MULTI-3: no failed-measurement concept** to start such a chain (GAP-MEAS-1).
- **GAP-MULTI-4: no causal chains** to traverse (GAP-CAUSE-1/2).
- **GAP-MULTI-5: transitive parts do not carry poses** (GAP-FRAME-6). (Frame chains not using identity, formerly
  GAP-SPATIAL-5, is by design and withdrawn; LABS-1.063.)
- **GAP-MULTI-6: no derivation record for a chained answer** (DI-7): a composed answer cannot cite a named rule and
  its premises; `required_evidence` across steps must be assembled by the harness.
- **GAP-MULTI-7: cost.** Per-item N+1 reads and cross-world slowdown (DI-9, deferred-issues.md:271-290; `where`
  ×2.5-2.8 with other worlds present). Long chains may be slow.
- **GAP-MULTI-8: DI-14** (variant world lists descriptions whose account is not inherited, no flag) and **DI-17**
  (a conflict group with one disputed pair is not merged at all) can affect chained answers in variant worlds and
  identity-heavy chains (deferred-issues.md:43, 46).

### E1 coverage
- Transitive parts: `parts` **6** (MECH-001/002/003/013/014, X-010); `dependencies` **4** (direct only).
- Identity: `same_thing` **27**, `aliases` **4**.
- Inherited variant worlds: **42** questions (35 depth 1, 7 depth 2).
- Cross-domain category: **33** questions, but each is still one reader (event_role 12, capable 5, office_holders 3,
  value_at 3, authorised 2, calibrated 2, same_thing 2, move 2, parts 1, aliases 1). Their questions mention
  cross-domain context (e.g. X-009, X-021) without a chained answer.
- No question chains two or more readers.

---

## 7. E1 benchmark facts relevant to E2 design

- 272 questions, 30 fixtures, 15 templates, 8 categories (counts: holds 53, event_role 47, value_at 37, same_thing 27,
  calibrated 24, capable 23, office_holders 13, move 12, exists 9, authorised 8, parts 6, occurrence_status 4,
  aliases 4, dependencies 4, officials 1). Content types in `holds`: classified-as 24, located-at 14, part-of 8,
  depends-on 2, employment 2, same-as 2, office-holding 1. All 37 `value_at` are `located-at`.
- Authoring (benchmark/e1/README.md): model-authored, development tier; four authors, two categories each; authors
  worked only from the specification documents and `spec/reader-docs.md`, forbidden to read `src/`, `tests/`,
  `probes/`, `*-output.md` or results, or to call readers; gold committed (`d0f0aa2`) before the harness ran; no kappa;
  each question has expected fields per template, `required_evidence`, `forbidden_evidence`, justification, spec
  citations, uncertainty, adversarial flag and difficulty. Scoring: all expected fields must match (sets unless
  ordered), evidence recall separately, failure categories including `unsupported`. Both query paths (selective and
  full load) must agree. Results 267/272 original, 272/272 revised (CLARIFICATIONS.md C1-C4).
- Author notes on unwritten questions: `benchmark/e1/notes/*.md` (4 files).
- **Harness gaps that block E2 fixtures for families 1-3 and part of 4** (evaluation/loader.py:129-250):
  - **GAP-HARNESS-1:** the `attest`/`deny` step accepts no `params` (allowed keys: world, type, roles, attester,
    stance, interval; loader.py:164-166), so `positioned-in`, `frame-transform` and `has-quality` ranges cannot be
    written from a fixture.
  - **GAP-HARNESS-2:** no fixture ops for `position`, `relate_frames`, `anchor_frame`, `define_unit`,
    `define_quality_kind`, `measure`, `claim_cause`, `claim_effect`, `describe_occurrence`, `declare_existence` /
    `create_thing` / `destroy`, `record_event`, `interpret` (op list loader.py:133-244). `causes` (roles cause,
    effect) and `existence`, `part-of` on occurrences can be written through the generic `attest` op;
    `initiates`/`terminates` need a proposition id as the outcome player, which a fixture cannot name.
  - **GAP-HARNESS-3:** no templates or answer extractors for `where`, `transform_between`, `poses`, `frame_info`,
    `measurements`, `compare_measurements`, `measurement_calibration`, `causes_of`, `effects_of`, `explain`,
    `changes`, `process_steps`, `before` (TEMPLATES.md table; overnight-report.md:142 estimates 2-3 days).
  - **GAP-HARNESS-4:** reader-docs.md lacks documentation strings for those readers (section 0 list); E1's
    independence rule makes reader-docs the authors' only view of reader semantics.

## 8. Quick answerability matrix

| Question family | Answerable now with public API | Needs new capability |
|---|---|---|
| Pose of X in frame F at t, via a chain (direct/derived, ranges, orientation, conflicts, unknown when unlinked, truncated search) | yes: `where`, `transform_between` | harness ops + templates (GAP-HARNESS-1..3) |
| Compose / invert transforms, chain agreement, disputed transforms | yes (`transform_between`; `spatial.Transform`) | none for exact transforms; uncertain transforms GAP-SPATIAL-1 |
| Rotations in Euler/axis-angle, units other than m/rad | no | GAP-SPATIAL-3, -4 |
| Frame hierarchy / anchored frame moving with its anchor / interpolation | no (one hop via `frame_info`; anchors reported only) | GAP-FRAME-1..5 |
| Frame or transform at different times (piecewise) | yes (attested intervals, `where(t)`, `changes`) | none |
| Stated measured values, provenance, instrument, operator, conditions, correction/supersession | yes: `measurements` | none |
| Compare two measurements (compatible/incompatible/incomparable) | yes: `compare_measurements` | GAP-MEAS-2, -3 for richer cases |
| Measurement vs spec / pass-fail / tolerance | no | GAP-MEAS-1 |
| Unit conversion within a dimension (incl. affine) | yes: `convert` (and SI storage) | compound units GAP-MEAS-5 |
| Calibration at measurement time | yes: `measurement_calibration`, `calibration_status` | none |
| What caused E (direct, lifted via describes, denied occurrences) | yes: `causes_of` | none |
| What did E cause / causal chains | no (partial via `facts_about`, unverified) | GAP-CAUSE-1, -2 |
| Claimed effects vs accepted state change | yes: `effects_of`, `changes`, `explain` | none |
| Counterfactual "if E had not happened" with propagated consequences | no (only stipulated content in a variant world) | GAP-CAUSE-3 |
| Steps of a process, ordered by time, disputed steps | yes: `process_steps` | none |
| Explicit order, preconditions, procedures, durations, missing steps | no | GAP-PROC-1..4, -7 |
| Chained questions (event → time → location/pose; failed measurement → part → location) | only by caller composition; no failed-measurement concept | GAP-MULTI-1..3 |
| Transitive parts, inherited variant worlds, identity | yes (`parts`, `dependencies`, worlds, `identity`) | none |
