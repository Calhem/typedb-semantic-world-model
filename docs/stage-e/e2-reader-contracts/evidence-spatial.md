<!-- Evidence record for Part B of benchmark/e2/spec/reader-contracts.md (LABS-1.062): the specification evidence gathered before drafting, with full citations. Supplementary to the contracts. -->

# Specification evidence: spatial readers (`transform_between`, `where`, `poses`, `frame_info`)

Repository: `typedb-semantic-world-model` (read-only extraction, nothing run). All paths are relative to the
repository root. Line numbers for design docs are as read on 2026-11-25; for `src/` they are file line numbers.

Marking:
- **[ESTABLISHED]**: stated in an approved design document or decision record.
- **[INFERRED]**: my reading, or found only in a docstring (`benchmark/e2/spec/reader-docs.md`, generated from
  docstrings) or in the implementation.

Abbreviations used in citations:
- **A1** = `docs/core-0.4/stage-a1.md`; **A2** = `docs/core-0.4/stage-a2.md`
- **v0.2** = `docs/architecture/world-ontology-v0.2.md`; **Plan** = `docs/plans/core-0.4-plan.md`
- **IB-D** = `docs/core-0.4/pre-e-increment-b-design.md`; **IB** = `docs/core-0.4/pre-e-increment-b.md`
- **IC-D** = `docs/core-0.4/pre-e-increment-c-design.md`; **ID-D** = `docs/core-0.4/pre-e-identity-design.md`
- **DI** = `docs/core-0.4/deferred-issues.md`; **E2-D** = `docs/stage-e/stage-e2-evaluation-design.md`
- **INV** = `docs/stage-e/stage-e-entry/e2-capability-inventory.md`; **RD** = `benchmark/e2/spec/reader-docs.md`
- **phys** = `src/worldmodel/physical.py`; **spat** = `src/worldmodel/spatial.py`

Approval state of the relevant decisions:
- A2 merged into `main` (LABS-1.009) after the LABS-1.008 corrections [ESTABLISHED] (A2 line 3-4).
- D-A2-1 conditionally approved; D-A2-2 approved; D-A2-3 amended as required; D-A2-4 approved; D-A2-5 provisionally
  accepted; **D-A2-7 "please confirm" with no recorded ruling found** in docs/ (A2 "Decisions and deviations for
  review", lines 228-234; grep of docs/ for D-A2-7 finds only stage-b.md:85, which uses it) [ESTABLISHED as to the
  text; the missing ruling is INFERRED from the grep].
- D-A1-2 (no functional constraint on positions in A1) and D-A1-4 (composition deferred) are resolved by A2 (A1 line
  3-4; A2 "Position judgement", "The same rule everywhere") [ESTABLISHED].
- Increment B Q1-Q6 approved (IB-D status line 3; Q5: frame edges apply the slot) [ESTABLISHED].
- E2-D3: contracts from design docs; where docstring and design differ, the contract **stops for the owner's
  decision** (E2-D 5.2, lines 174-180; stage-e2-decisions.md line 42) [ESTABLISHED].

## 0. Shared conventions (apply to all four readers)

- Right-handed Cartesian frames; lengths in metres; angles in radians [ESTABLISHED] (Plan 9.6; A2 "Conventions").
- Rotations are unit quaternions (w, x, y, z), Hamilton product, active rotation v' = q v q*; a norm more than 1e-9
  from 1 is rejected on write; q and -q are the same rotation [ESTABLISHED] (Plan 9.6; A2 "Conventions", line 18-19).
- `frame-transform(parent P, child C)` holds (q, t) and maps a point in C to P: p_P = R(q) p_C + t [ESTABLISHED]
  (Plan 9.6 "Transform semantics"; A2 line 20-21).
- Composition T_AC = T_AB ∘ T_BC (R_AC = R_AB R_BC, t_AC = R_AB t_BC + t_AB); inverse T_CP = (q*, -R(q*) t)
  (Plan: (Rᵀ, -Rᵀ t), equivalent), computed and never stored [ESTABLISHED] (Plan 9.6; A2 lines 22-24).
- Range boxes are mapped by their 8 corners and the bounding box is taken (conservative); rotations are treated as
  exact [ESTABLISHED] (Plan 9.6 "Uncertainty"; A2 lines 25-27; v0.2 C8 "Awkward").
- Positions agree within 1e-9 m; orientations by angular separation 2·atan2(‖v‖, |w|) of q₁* q₂ under an angular
  tolerance (default 1e-9 rad) [ESTABLISHED] (A2 lines 28-30, "Orientation comparison policy" lines 72-84). The
  earlier rule 1 − |q₁·q₂| ≤ 1e-9 is superseded [ESTABLISHED] (A2 line 29-30).
- Answers are computed for a context ⟨world, perspective, τ (as_of), t, Π (policies)⟩ and never stored
  [ESTABLISHED] (v0.2 5.1, 5.2 E9, 6.1).
- Schema: `positioned-in(positioned, frame)` with `x-min`…`z-max` (metres), optional `qw qx qy qz`;
  `frame-transform(parent, child)` with `tx ty tz`, `qw qx qy qz`; `anchored-to(frame, anchor)`, functional (frame →
  anchor) [ESTABLISHED] (A1 "Schema added" table; Plan Stage A table; v0.2 3.5).
- Declared functional slots: `anchored-to` (frame → anchor), `positioned-in` ((frame, positioned) → position, value =
  parameters), `frame-transform` ((child, parent) → transform, value = parameters) [ESTABLISHED] (IB-D 2.3 lines
  64-67; A2 "The same rule everywhere" lines 147-151; D-A2-1).
- Status vocabulary (layer 3): OBSERVED, ASSERTED, STIPULATED, INFERRED, PRESUMED, DISPUTED, UNKNOWN, NOT_YET_KNOWN;
  UNKNOWN = records visible but none decides t; NOT_YET_KNOWN = nothing visible at τ [ESTABLISHED] (v0.2 5.6).
  OBSERVED and PRESUMED are never produced by the implementation; observations are reported ASSERTED [INFERRED]
  (INV section 0, status table; semantics.py:162-170). A2 itself says "a direct observation or testimony is ASSERTED"
  [ESTABLISHED] (A2 "Position judgement", line 143-144).
- INFERRED covers "a declared query-time rule concludes it (… frame transform …)" [ESTABLISHED] (v0.2 5.6 table).
- No INCOMPARABLE status: incomparability and truncation live in structured fields (D-A2-4, approved) [ESTABLISHED]
  (A2 line 231).

---

## 1. `transform_between(world, source, target, t, as_of=None, perspective='system', limit=None)`

### 1.1 Supported question classes and input conditions
- "How do coordinates of frame `source` map into frame `target` at t?" for a world, perspective, knowledge time and
  valid time [ESTABLISHED] (A2 "Frame chains" lines 117-120; E2-D 3.1 S1-S6, line 42).
- Question classes with design support: composition of a chain (S1), inverse of a stated chain (S2), disagreeing
  chains (S3), no chain (S4), perspective variation (S5), supersession over time (S6) [ESTABLISHED] (E2-D 3.1, lines
  62-67, class H). Uncertain transforms (S7) and other rotation formats (S8) are gaps [ESTABLISHED] (E2-D 3.1 lines
  68-69).
- Parameters: `world`, `source`, `target`, `t`, `as_of`, `perspective`, and `limit` = the edge-examination resource
  limit, default 100,000, "settable per call" [ESTABLISHED] (A2 "Resource limit" line 50-52).
- No angle-tolerance parameter exists on `transform_between`; chain agreement uses "the angular tolerance"
  [ESTABLISHED for the text] (A2 line 28, 42, 81). Which tolerance (default vs caller's) is not stated for
  `transform_between`; the implementation always uses the default 1e-9 rad (`Transform.close_to` default, spat:79;
  phys:356) [INFERRED].
- Any perspective id and any world id are accepted; no existence check of frames [INFERRED] (phys:371-379; no
  validation code).
- `source == target`: identity transform, status INFERRED, empty chain, `verified: true` [INFERRED] (phys:325-329,
  379; INV line 67 "also source == target"). Not covered by the design.

### 1.2 Output fields and vocabulary
- Returns `chain`, `frames` and `search` [ESTABLISHED] (A2 "Results" line 68). The shortest chain is reported "step
  by step, with its sources" [ESTABLISHED] (A2 line 37-38). Each step is `forward` (child → parent) or `inverse`
  [ESTABLISHED] (A2 line 23-24).
- `search` always says `complete` or `truncated`, plus frames reached, edges examined, hops, cycle, edges checked,
  `verified` and the inconsistent edges [ESTABLISHED] (A2 lines 50-52). `search.inconsistent` lists each edge, its
  sources and the translation and angle gaps [ESTABLISHED] (A2 line 46-47).
- Implementation field set: `{source, target, status, rule: "frame-transform/v1", transform (Transform(q, t)) or
  None, chain: [{parent, child, direction, translation, rotation, support, disputed}], frames, reason, search:
  {complete, truncated, limit, edges_examined, frames_reached, edges_in_graph, hops, cycle, relevant_edges, verified,
  inconsistent: [{parent, child, support, translation_gap_m, angle_gap_rad}]}}` [INFERRED] (phys:305-312, 314-379;
  INV line 67).
- `transform` maps source coordinates into target: p_target = R(q) p_source + t (the composed transform from source
  to target) [ESTABLISHED for the convention, A2 lines 20-24; INFERRED for the field's direction from RD line 218
  "How `source` frame coordinates map into `target`" and phys:231].
- Statuses: INFERRED (consistent), DISPUTED (inconsistent edge or disputed transform), UNKNOWN (no chain, or
  truncated) [ESTABLISHED] (A2 "Outcomes" lines 44-58; E2-D line 42). NOT_YET_KNOWN is never returned [INFERRED]
  (phys:314-379).
- Reason strings: "no frame chain from X to Y"; "search truncated after N edge examinations (limit L) without
  reaching Y"; "verification incomplete: search truncated, other chains were not checked for agreement"
  [ESTABLISHED] (A2 lines 53-58, 122). "chains disagree (ambiguous frame relationships)" and "a transform on a chain
  is disputed" [INFERRED] (phys:364, 367).

### 1.3 Judgement and uncertainty semantics
- Search: breadth-first from source, no hop limit, each frame reached once (cycles terminate); every reached frame
  gets the composed transform along a shortest chain [ESTABLISHED] (A2 lines 35-38; D-A2-3 amended).
- Agreement checked completely: every edge on any simple source-target chain (edges of the biconnected blocks on the
  route in the block-cut tree) is checked against the composed transforms, within 1e-9 m and the angular tolerance;
  no path is enumerated [ESTABLISHED] (A2 lines 39-43).
- Consistent → INFERRED, `search.verified: true` [ESTABLISHED] (A2 line 45).
- An inconsistent edge on a route → DISPUTED with **no transform chosen** [ESTABLISHED] (A2 line 46-47, 123-124;
  Plan 9.6 "Chains").
- A disputed transform on any route → DISPUTED [ESTABLISHED] (A2 line 48, 124). Two accepted different transforms
  for one frame pair are disputed edges (slot conflict) [ESTABLISHED] (IB-D Q5 line 250; IB line 39).
- A disagreement not on any route between the two frames does not affect the answer [ESTABLISHED] (A2 line 49).
- Cycles: a component with more edges than a tree is reported `cycle: true`; consistent cycles answer INFERRED,
  inconsistent ones DISPUTED [ESTABLISHED] (A2 lines 125-126).
- Truncation: completed search without chain → UNKNOWN, `complete: true`; truncated without reaching target →
  UNKNOWN, `truncated: true`; truncated but reached → the shortest chain's transform as an **unverified candidate
  only**, UNKNOWN, `verified: false` [ESTABLISHED] (A2 lines 50-58; LABS-1.009).
- Transforms carry no uncertainty; only exact values [ESTABLISHED] (A2 "Known limitations" line 240; GAP-SPATIAL-1,
  INV line 82-84).
- `verified` is false for a completed no-chain search [INFERRED] (phys:335); the design does not state `verified`
  for that outcome.

### 1.4 Temporal, perspective and world visibility
- Edges are the `frame-transform` contents judged for the asked world, perspective, knowledge time and valid time,
  as for any other content (inherited snapshots, acceptance, supersession) [ESTABLISHED] (A2 lines 34-35, 118-120).
- Relocalisation: a correction supersedes the transform attestation; derived answers change from that knowledge time
  only; as known before, the old answer stands [ESTABLISHED] (v0.2 3.5 C8 and section 7 C8; Plan 3 "Physical" and
  5 criterion A).
- Hypothetical worlds: a variant's own transform overrides the inherited one; a base transform recorded after the
  branch is excluded by the snapshot [ESTABLISHED] (A2 line 146; LABS-1.009 tests list, A2 lines 201-202; v0.2 6.2).
- Stipulations are constitutive, hold for every perspective [ESTABLISHED] (v0.2 5.2 E7).
- Frame chains are judged without same-as identity, by design: same-as relates particulars only, frames cannot be
  declared the same [ESTABLISHED] (IB "Points decided" 6, line 101; DI-12 section, line 399; ID-D 3.8 line 128 and
  ID-8 lines 238-240).
- Plan 9.6 "Time": a derived pose holds only where every input attestation certainly holds (intersection), no
  extrapolation, knowledge time = latest recorded input [ESTABLISHED] (Plan 9.6). The implementation evaluates each
  input at the instant t and reports no interval or knowledge time for the answer [INFERRED] (phys:189-208, 371-379).

### 1.5 Ordering and multiplicity
- One chain is reported: the shortest [ESTABLISHED] (A2 line 37-38, 105). Tie-breaking among equally short chains is
  not specified by the design [INFERRED]. Implementation: edges sorted by (parent, child, support) then BFS in
  adjacency order (phys:208, 216-232) [INFERRED].
- `chain` is ordered from source to target; `frames` = [source, …, target] [INFERRED] (phys:337-344).
- `search.inconsistent` is in edge-index order [INFERRED] (phys:353).
- Several attestations of one transform content are one edge with several supporting ids (corroboration)
  [ESTABLISHED for corroboration, v0.2 5.3; INFERRED for the edge shape, phys:205-207].

### 1.6 Supporting, conflicting, alternative evidence
- Support: the attestations of every transform on the chain [ESTABLISHED] (A2 line 127-128 "cites … every transform
  on its chain"; v0.2 3.5 C8). Implementation: `chain[i].support` [INFERRED] (phys:310).
- Conflict evidence: `search.inconsistent[].support` for inconsistent edges [ESTABLISHED] (A2 line 46-47); chain
  steps marked `disputed` [INFERRED] (phys:311).
- Alternatives (unreviewed transforms): **not reported** by `transform_between` [INFERRED] (phys:371-379, no field).
  v0.2 6.2 says unaccepted attestations by others are returned as alternatives [ESTABLISHED] (v0.2 6.2). See
  Discrepancies.

### 1.7 Derivation rule and admissible premises
- Rule `frame-transform/v1` [ESTABLISHED] (v0.2 3.5 C8; Plan Stage A table; A2 line 127).
- Premises: the transform attestations on the chain (for `where`, also the position attestation) [ESTABLISHED]
  (A2 line 127-128).
- Admissible premises: transforms that hold for the perspective at t (judged ESTABLISHED); polarity- or slot-disputed
  transforms are kept as marked edges and make any chain through them DISPUTED, so they never yield a transform
  [ESTABLISHED] (A2 line 119-120, 124; IB-D Q5). Pending/unknown/not-holding transforms are not edges [INFERRED]
  (phys:202-203).
- v0.2 E6: a derived conclusion is usable only while all its premises are usable [ESTABLISHED] (v0.2 5.2 E6). No
  derivation record is stored (D8 deferred) [ESTABLISHED] (Plan Stage A table "no derivation records").
- `rule` is returned on every result, including UNKNOWN/DISPUTED and source == target [INFERRED] (phys:379).
- E2 harness treats `frame-transform/v1` derivations of `where`/`transform_between` as derivations to check
  (rule recorded, premises non-empty, premises recorded attestations) [ESTABLISHED for the harness, not the reader]
  (docs/stage-e/stage-e2-harness-review.md lines 92-98).

### 1.8 Documented refusals
- None documented for `transform_between` [INFERRED] (A2; RD lines 215-223). Absence of a chain is an UNKNOWN
  answer, never a refusal and never invented [ESTABLISHED] (A2 line 122).
- Writer-side only: `relate_frames` rejects parent == child, non-finite translation, non-unit quaternion
  [ESTABLISHED for norm, Plan 9.6; INFERRED for the others, phys:72-77; INV line 66].

### 1.9 Limitations and gaps
- GAP-SPATIAL-1 (no uncertainty on transforms), -3 (quaternions only), -4 (no units on spatial content), -5 (frame
  chains judged without same-as; see Discrepancies) [ESTABLISHED as gap ids] (INV lines 82-95; E2-D 4 line 152).
- Performance: each question loads every judged transform of the world (constant query count) [ESTABLISHED] (A2
  "Known limitations" line 243).
- GAP-FRAME-1: `anchored-to` is not used in chains [ESTABLISHED as gap id] (INV line 134-137).
- GAP-FRAME-4: one chain, not the hierarchy [ESTABLISHED as gap id] (INV line 142-144).

---

## 2. `where(world, thing, frame, t, as_of=None, perspective='system', angle_tolerance=1e-9, limit=None)`

### 2.1 Supported question classes and input conditions
- "Where is `thing` in `frame` at t?" judged for the perspective [ESTABLISHED] (A2 "Position judgement" line 134).
  It is the position-specific query interface (D-A2-5; `holds` cannot single out one position) [ESTABLISHED] (A2
  lines 86-88, 232).
- Classes: directly stated (F1), derived through a chain (F2), two sources disagree (F3), no persistence beyond the
  stated interval (F4), hypothetical variant vs actual (F5), earlier knowledge time (F6) [ESTABLISHED] (E2-D 3.2
  lines 74-79). Gaps: anchored frame moving with its anchor (F7), interpolation (F8), hierarchy (F9), parts through
  their assembly (F10) [ESTABLISHED] (E2-D lines 80-83).
- `angle_tolerance`: a per-question policy parameter (v0.2's Π), default 1e-9 rad; caller may pass e.g. a sensor's
  stated angular accuracy [ESTABLISHED for the text] (A2 lines 75-78; D-A2-7, **"please confirm", no ruling found**).
- `limit`: per-search edge-examination limit as in 1.1 [ESTABLISHED] (A2 line 50-52). Implementation applies it
  per candidate search [INFERRED] (phys:398).
- No validation of `frame`, `thing`, negative or non-finite `angle_tolerance`, or `limit` [INFERRED] (phys:381-447).

### 2.2 Output fields and vocabulary
- Candidates: every position statement that holds for the perspective at t, direct (stated in `frame`) or derived
  (mapped through a chain) [ESTABLISHED] (A2 lines 134-136).
- Each candidate carries its `chain` and `search` [ESTABLISHED] (A2 line 68-69). A candidate whose chains disagree has
  no position (x, y, z are None) and is DISPUTED [ESTABLISHED] (A2 line 69).
- Incomparable statements are listed with their `search` [ESTABLISHED] (A2 line 70, 141-142; D-A2-4).
- Conflict kinds: `disjoint ranges`, `orientations differ`; each conflict reports the separation and the tolerance
  used [ESTABLISHED] (A2 lines 79-80).
- Unreviewed claims are listed as alternatives [ESTABLISHED] (A2 line 145-146; v0.2 6.2).
- Answer-level `verified` and the reason "verification incomplete" when truncated [ESTABLISHED] (A2 lines 62-63).
- Implementation field set: `{thing, frame, status, candidates: [{x, y, z (lower, upper) or None, orientation,
  status, stated_in, stated, orientation_stated, position_support, direct, rule (None if direct, else
  "frame-transform/v1"), chain, reason, search, verified}], conflicts: [(i, j)], conflict_details: [{pair, kind,
  separation_rad?, tolerance_rad?, unverified}], angle_tolerance, verified, reason, judgement, incomparable:
  [{frame, support, reason, search}], alternatives: (attestation ids)}` [INFERRED] (phys:400-447).
- `judgement` words: the design uses "compatible" and "conflict"/"DISPUTED" [ESTABLISHED] (A2 lines 138-140; demo
  table lines 157-164 shows "compatible"). The implementation returns `conflicting`, `compatible` (two or more
  candidates, no verified conflict), `single` (one candidate) or None (none) [INFERRED] (phys:445-446; INV line 34).
  "single" and None are not in any design text found [INFERRED].
- Overall status: STIPULATED / ASSERTED (direct, by basis), INFERRED (only derived), DISPUTED, UNKNOWN,
  NOT_YET_KNOWN [ESTABLISHED] (E2-D line 43; A2 line 143-144). Precise rule "DISPUTED on a verified conflict; UNKNOWN
  if unverified; else most direct status among direct candidates (= core rule over their union); INFERRED when only
  derived" [ESTABLISHED] (IC-D section 4 table, line 120).
- Units: metres for x/y/z, radians for separation and tolerance; orientation quaternion (w, x, y, z) [ESTABLISHED]
  (Plan 9.6; A2 conventions).
- Derived orientation = composed rotation applied to the stated orientation (q_total · q_stated); None when the
  statement has no orientation [INFERRED] (phys:407-408).

### 2.3 Judgement and uncertainty semantics
- Candidates are compared, never merged; nothing averaged, intersected or weighted; overlap means "can both be
  true", not equality [ESTABLISHED] (A2 lines 83-84, 136; "Known limitations" line 241).
- Identical ranges are one content: one candidate with several supporting attestations [ESTABLISHED] (A2 line 137).
- Overlapping ranges, including touching ones, are compatible; each keeps its own range [ESTABLISHED] (A2 line 138).
  Overlap tolerance 1e-9 m [INFERRED] (spat:97-99).
- Disjoint ranges, or orientations whose separation exceeds the tolerance, conflict → DISPUTED, conflicting pairs
  listed [ESTABLISHED] (A2 lines 139-140, 72-80; v0.2 5.3 rule 2 "disjoint ranges").
- Orientation comparison only for pairs whose ranges overlap and both have an orientation (a disjoint pair is
  reported once as `disjoint ranges`) [INFERRED] (phys:421-427).
- Direct candidates carry their own support's status (`support_status`), so the per-question angle tolerance decides
  orientation conflicts rather than the default-tolerance slot conflict [ESTABLISHED] (docs/core-0.4/stage-b.md line
  85; phys:409-411).
- Different frames are compared after derivation; with no chain the statement is incomparable, never guessed
  [ESTABLISHED] (A2 lines 141-142).
- Measurement uncertainty = the ranges, propagated conservatively; a widened range can hide a conflict (never invent
  one) [ESTABLISHED] (A2 line 143, 239).
- Truncation (LABS-1.009): a candidate derived through a truncated search keeps its computed position, status
  UNKNOWN, `verified: false`; while any candidate is unverified or a truncated search left a statement incomparable,
  the answer is UNKNOWN with `verified: false`; an unverified candidate cannot create a conflict (its conflicts are
  listed with `unverified: true`); verified conflicts still decide → DISPUTED [ESTABLISHED] (A2 lines 59-67, 186-191).
- Candidate whose chain is DISPUTED: no position, DISPUTED; the answer is DISPUTED [ESTABLISHED] (A2 line 69; IC-D
  line 120 "DISPUTED on a verified conflict"; LABS-1.009 tests A2 line 194-195). Implementation: any verified
  DISPUTED candidate makes the answer DISPUTED [INFERRED] (phys:433).
- Empty candidates: UNKNOWN when position records about the thing are visible, else NOT_YET_KNOWN [ESTABLISHED for the
  general definitions, v0.2 5.6; INFERRED for where's test `about` = any visible `positioned-in` attestation of the
  thing, phys:390-391, 442].
- Chain agreement inside `where` uses the default angular tolerance, not the caller's `angle_tolerance` [INFERRED]
  (phys:398 calls `_resolve` without it; spat:79). Design text: "The same measure serves … chain agreement" (A2 line
  81) without saying which tolerance. See Discrepancies.

### 2.4 Temporal, perspective and world visibility
- Only statements that hold at t for the perspective count [ESTABLISHED] (A2 line 145).
- No persistence beyond the stated interval (F4: UNKNOWN between/after stated poses) [ESTABLISHED] (E2-D line 77, 143;
  Plan 9.6 "no extrapolation"; GAP-FRAME-3).
- Knowledge time: as known before an acceptance or supersession, the earlier answer stands (demo: "As known before
  that acceptance (`as_of`), it is still compatible") [ESTABLISHED] (A2 line 163; v0.2 C8).
- Variant worlds: a variant's own position or transform overrides the inherited one; the actual world is unaffected
  [ESTABLISHED] (A2 line 146, demo line 162).
- Perspective: the rival's own perspective sees only its own claim; once the system accepts it, the system's answer
  is DISPUTED [ESTABLISHED] (A2 demo line 163; LABS-1.009 "perspective: unreviewed, the rival's own view, accepted,
  rejected", A2 line 199).
- Thing identity: readers use the perspective's same-as identity and select by the subject's class (ID-8), frame
  chains excepted [ESTABLISHED] (ID-D section 9, ID-8). Whether `where`'s `about` and `alternatives` include
  positions stated about an alias is unclear: the code filters by the raw id (`thing in a.roles["positioned"]`,
  phys:391; `poses` likewise phys:97) [INFERRED]. See Discrepancies.

### 2.5 Ordering and multiplicity
- Not specified by the design [INFERRED].
- Implementation: candidates follow `poses` order (sorted by stated frame id; ties in `facts_about` order), skipping
  incomparable ones; `conflicts` and `conflict_details` pairs are (i, j) with i < j indexing `candidates`;
  `incomparable` in `poses` order; `alternatives` a sorted tuple of attestation ids [INFERRED] (phys:105, 396-430;
  model.py:1275-1277).
- Several statements in different frames that map to the same range are separate candidates [INFERRED] (phys:396).

### 2.6 Supporting, conflicting, alternative evidence
- A derived candidate cites the position attestation(s) and every transform attestation on its chain [ESTABLISHED]
  (A2 line 127-128, "citing the position and every transform", A2 demo; v0.2 C8). Implementation: `position_support`
  + `chain[].support` [INFERRED] (phys:412-413).
- A direct candidate's support: its position attestations [ESTABLISHED] (A2 line 137 "several supporting
  attestations"); `position_support` [INFERRED].
- **Evidence supporting candidates** = each candidate's `position_support` (plus chain support for derived ones).
  **Conflict evidence** = the pairs in `conflicts`, identified by candidate index; the attestations are those of the
  two candidates; chain-level conflicts are in each candidate's `search.inconsistent` [ESTABLISHED for "conflicting
  pairs are listed", A2 line 140; INFERRED for the shape].
- **`alternatives`** = unreviewed, not superseded attestations of `positioned-in` about the thing that say something
  at t; they never support [ESTABLISHED for "Unreviewed claims are listed as alternatives", A2 line 145-146; v0.2
  6.2; IB-D 2.2 `pending` "never decide"]. Implementation selects them across **all frames** (not only `frame` or
  relatable frames) and returns ids only [INFERRED] (phys:390-392; model.py:1275-1277).
- **`incomparable`** entries = position statements that hold for the perspective but whose frame cannot be related
  to `frame` (complete search without chain, or truncated without reaching): they are accepted evidence, listed with
  their `support` and `search`, and neither support nor contradict the answer [ESTABLISHED] (A2 lines 141-142, 70;
  D-A2-4). An incomparable statement from a truncated search makes the answer UNKNOWN (A2 line 62-63)
  [ESTABLISHED]; from a complete search it does not affect the status [INFERRED] (phys:431).
- Rejected attestations: neither candidates nor alternatives [INFERRED] (model.py:1276; A2 LABS-1.009 tests mention
  "rejected" only as a perspective case).

### 2.7 Derivation rule and admissible premises
- Rule `frame-transform/v1`; derived positions INFERRED [ESTABLISHED] (A2 line 127; v0.2 3.5).
- Premises: the position statement **is** a premise, together with every transform on the chain [ESTABLISHED] (A2
  line 127-128 "cites the position attestations and the attestations of every transform on its chain").
- Disputed transforms are not admissible to produce a position: a chain using one is DISPUTED and has no position
  [ESTABLISHED] (A2 line 124, 69).
- Disputed position premises: not addressed by the design for derived candidates [INFERRED]. The implementation
  gives a derived candidate the chain's status, so a polarity-disputed position statement (listed by `poses` since
  DI-1) mapped through a consistent chain yields an INFERRED derived candidate [INFERRED] (phys:411 uses
  `r["status"]` when not direct). v0.2 E6 requires every premise usable [ESTABLISHED]. See Discrepancies.
- Direct candidates have `rule: None` [INFERRED] (phys:413).

### 2.8 Documented refusals
- None documented for `where` [INFERRED] (A2; RD lines 232-242). Unrelatable frames give incomparable entries, never
  a refusal or a guess [ESTABLISHED] (A2 line 141-142).
- Related refusal elsewhere: `value_of` on a parameter-valued slot refuses with "ask with where/poses" [INFERRED]
  (model.py:1297-1298). `holds(positioned-in, roles)` names no parameters (D-A2-5) [ESTABLISHED].
- Writer-side: `position` rejects non-finite ranges, lower > upper, non-unit quaternions [ESTABLISHED] (A1 "API" line
  29-31; Plan 9.6).

### 2.9 Limitations and gaps
- Conservative 8-corner range propagation (conflicts can be missed, never invented) [ESTABLISHED] (A2 line 239;
  GAP-SPATIAL-2).
- Orientations exact; tolerance is per question, not per claim; small sensor differences dispute unless the caller
  states a tolerance [ESTABLISHED] (A2 line 240; D-A2-7).
- No single best estimate [ESTABLISHED] (A2 line 241).
- Truncated searches give unverified candidates [ESTABLISHED] (A2 line 242).
- `where` makes about 32-35 queries; cross-world slowdown (DI-22: `where` +3.2 ms from 11 to 92 worlds) [ESTABLISHED]
  (A2 line 244; DI table line 61).
- GAP-SPATIAL-2, -6 (no geometry), -7 (no distance/relative-position reader), -8 (`holds` cannot pick out one
  position); GAP-FRAME-1 (anchoring no geometric effect), -2 (`move()` updates places only), -3 (no interpolation),
  -6 (parts not positioned through their assembly); GAP-MULTI-2 (no "at the time of event E" rule), GAP-MULTI-5
  [ESTABLISHED as gap ids] (INV lines 85-101, 134-150, 330-346; E2-D 4).
- No identity from proximity [ESTABLISHED] (A2 line 152).

---

## 3. `poses(world, thing, t, as_of=None, perspective='system')`

### 3.1 Supported question classes and input conditions
- Reading API from A1: the thing's positions at t, judged for a world, perspective, knowledge time and valid time
  through `facts_about` [ESTABLISHED] (A1 "API" lines 29-32).
- E2 family F lists `poses` as a reader [ESTABLISHED] (E2-D line 43).
- No frame parameter: all frames [INFERRED] (phys:91).

### 3.2 Output fields and vocabulary
- One entry per position content: frame, per-axis (lower, upper) ranges in metres, optional orientation (w, x, y, z),
  status, supporting attestations [ESTABLISHED for content shape, A1 schema table and A1 output line 73; INFERRED for
  field names, RD lines 199-205].
- Increment B: listings show polarity-disputed content in place, marked DISPUTED, "citing the assertions, the
  denials and any constraint rivals"; `poses` is one of these listings [ESTABLISHED] (IB-D section 4 lines 166-168;
  IB lines 31-33; DI-1 correction). Fields are only added, never removed or renamed [ESTABLISHED] (IB-D 4).
- Implementation fields: `frame, x, y, z, orientation (tuple or None), status, support, conflicts, support_status`
  [INFERRED] (phys:100-104). `judgement`, `assertions`, `denials` from `facts_about` are **not** projected
  [INFERRED]. See Discrepancies.
- Statuses per entry: ASSERTED / STIPULATED / INFERRED / DISPUTED [INFERRED] (INV line 119). `support_status` = the
  support's status before constraints, DISPUTED for a polarity dispute [ESTABLISHED for facts_about] (stage-b.md
  lines 81-86; IB-D 2.4 "keeps both statuses").

### 3.3 Judgement and uncertainty semantics
- A1: no functional constraint on positions; several positions in one frame are all listed, not judged (D-A1-2)
  [ESTABLISHED for A1] (A1 D-A1-2). **Superseded by A2**: module `core-0.4-a2` declares (positioned, frame) →
  position, so the shared conflict check reports disjoint positions (or orientations differing beyond the default
  tolerance) as DISPUTED with rivals, in `holds`/`facts_about` and hence in `poses` [ESTABLISHED] (A2 lines 147-151,
  82; IB-D section 6 table "poses, frame_info … constraint conflicts (already)" line 212).
- Constraint check uses the default angular tolerance (1e-9 rad) [ESTABLISHED] (A2 line 82; D-A2-7).
- Ranges are reported as stated; no reconciliation [ESTABLISHED] (A2 line 83-84).

### 3.4 Temporal, perspective and world visibility
- Through `facts_about`: holding or disputed at t for the world (with inheritance), perspective and knowledge time
  [ESTABLISHED] (A1 line 31-32; IB-D 2.1; RD facts_about lines 96-105).
- Positions change over time; an ended position does not hold after its end (A1 output: "bearing-1 after T1: no
  position holds") [ESTABLISHED] (A1 lines 59-60, 74).
- Identity: `facts_about` is on the judgement path that uses the context's identity [ESTABLISHED] (ID-D 3.8 line
  121). `poses` then filters entries by the raw id in the `positioned` role [INFERRED] (phys:97).

### 3.5 Ordering and multiplicity
- Not specified by design [INFERRED]. Implementation sorts by frame id (stable; ties in `facts_about` order)
  [INFERRED] (phys:105). Several positions in one frame are all listed [ESTABLISHED] (A1 D-A1-2; RD line 203-204).
- Identical ranges are one content with several supporting attestations [ESTABLISHED] (A2 line 137; D-A1-5 keys at
  12 significant digits).

### 3.6 Supporting, conflicting, alternative evidence
- `support`: the deciding attestations; `conflicts`: attestations of contents in conflict under the slot
  [ESTABLISHED for facts_about entries] (stage-b.md lines 81-85; RD lines 99-105). Polarity disputes cite both sides
  per IB-D section 4 [ESTABLISHED]; `poses` does not expose `assertions`/`denials` [INFERRED].
- No alternatives field [INFERRED] (phys:91-105).

### 3.7 Derivation rules
- None: `poses` reports stated positions only; no frame derivation [INFERRED] (phys:91-105; A2 places derivation in
  `where`). Status INFERRED only where the attestation's basis is inference [INFERRED] (semantics.py:162-170).

### 3.8 Refusals
- None documented [INFERRED].

### 3.9 Limitations and gaps
- U-3 / D-A1-5: every new position is a new proposition [ESTABLISHED] (A1 D-A1-5; A2 line 246).
- GAP-SPATIAL-8, GAP-FRAME-6 [ESTABLISHED as gap ids] (INV).

---

## 4. `frame_info(world, frame, t, as_of=None, perspective='system')`

### 4.1 Supported question classes and input conditions
- What is known about a frame at t: what it is anchored to, its stored transforms, and the things positioned in it,
  judged through `facts_about` [ESTABLISHED for the judged read] (A1 "API" lines 29-32; A1 output line 72
  "f-bench: anchored to bench-1; in f-workshop: translation …, rotation … [ASSERTED]"). Field list is from the
  docstring [INFERRED] (RD lines 108-112).
- E2: "What is the frame hierarchy / root frame of F?" is a gap, `frame_info` gives one hop only (F9, GAP-FRAME-4)
  [ESTABLISHED] (E2-D line 82).

### 4.2 Output fields and vocabulary
- Transforms "as stored: translation and rotation", not composed [INFERRED] (RD line 111; phys:117-123).
- Implementation: `{frame, name, anchored_to: [{anchor, status}], parents: [{parent, translation, rotation, status,
  support}], children: [{child, translation, rotation, status, support}], positioned: [sorted unique ids]}`
  [INFERRED] (phys:111-127; INV line 120).
- `name` comes from `names()`, a direct TypeDB read of `has name`, documented as "a convenience for readable output";
  it is not judged for world, perspective or time [INFERRED] (phys:176-186; A1 line 31 lists `names` among readers).
- Listing reader under DI-1: polarity-disputed content listed, marked DISPUTED, citing assertions and denials
  [ESTABLISHED] (IB-D section 4; IB line 31-33).

### 4.3 Judgement and uncertainty semantics
- `anchored-to` is functional (one anchor at a time); a second accepted anchor is DISPUTED [ESTABLISHED] (A1 schema
  table; A1 tests "one anchor per frame (functional: DISPUTED, with `holds` conflicts)").
- Transform entries are judged with the `frame-transform` slot: two different accepted transforms for one pair are
  DISPUTED [ESTABLISHED] (IB-D Q5; A2 line 148-151).
- `positioned` lists ids only: no status, so a disputed position is listed without marking [INFERRED] (phys:124-126).

### 4.4 Temporal, perspective and world visibility
- As `facts_about` (see 3.4) [ESTABLISHED] (A1 line 31-32).
- Frames are not subject to same-as [ESTABLISHED] (ID-D 3.8).

### 4.5 Ordering and multiplicity
- `positioned` sorted and de-duplicated; `anchored_to`, `parents`, `children` in `facts_about` order [INFERRED]
  (phys:126). Not specified by design.

### 4.6 Evidence
- `parents`/`children` carry `support`; `anchored_to` carries only `status` (no support); `positioned` carries
  neither [INFERRED] (phys:116-125). No `conflicts`, `assertions`, `denials` [INFERRED].

### 4.7 Derivation rules
- None (stored values only; no composition) [INFERRED] (RD line 111).

### 4.8 Refusals
- None documented [INFERRED]. An unknown frame id returns empty lists [INFERRED] (phys:110-127).

### 4.9 Limitations and gaps
- GAP-FRAME-1 (anchoring reported only, no geometric effect), GAP-FRAME-4 (no hierarchy reader), GAP-FRAME-5 (no
  history reader for a frame's transform) [ESTABLISHED as gap ids] (INV lines 134-146).

---

## Discrepancies

Each item cites both sides. Per E2-D 5.2, each needs the owner's decision; none is resolved here.

1. **`poses` docstring is stale on conflicts.** Docstring: "conflicts between positions are not judged in A1" (RD
   lines 202-204; phys:92-94). Design: since A2 the (positioned, frame) slot makes disjoint positions DISPUTED in
   `facts_about` (A2 lines 147-151; IB-D table line 212 "constraint conflicts (already)"); the implementation returns
   `conflicts` and a DISPUTED `status` (phys:103-104).
2. **`poses` lists disputed positions, docstring says "positions that hold at t".** Design: DI-1 requires listing
   polarity-disputed content (IB-D 4; IB lines 31-33). Docstring (RD line 202) does not mention disputed entries;
   `support_status` and `conflicts` fields are undocumented in the docstring (phys:103-104).
3. **Listings do not cite both sides of a polarity dispute.** Design: listings gain disputed contents "citing the
   assertions, the denials and any constraint rivals" (IB-D section 4, lines 166-168). `poses` drops `judgement`,
   `assertions`, `denials` (phys:100-104); `frame_info` gives `anchored_to` only `status` (no support), and
   `positioned` is a bare id list with no status, so a disputed position appears unmarked (phys:116, 124-126).
4. **Derived candidate from a disputed position statement.** Design: derived positions cite the position as a premise
   (A2 line 127-128); E6 requires every premise usable (v0.2 5.2 E6); a disputed *transform* makes the chain DISPUTED
   (A2 line 124). Not covered for a disputed *position* premise. Implementation: derived candidate status is the
   chain's status (phys:411), so a polarity-disputed position (included by `poses` since DI-1) mapped through a
   consistent chain yields an INFERRED candidate; `where`'s overall DISPUTED test only sees DISPUTED candidates
   (phys:433). Needs a decision.
5. **Angular tolerance for chain agreement.** Design: chains agree "within 1e-9 m and the angular tolerance" (A2 line
   28, 42) and the per-question policy "serves … chain agreement" (A2 line 81); only `holds` and variant overrides are
   named as using the default (A2 line 82). Implementation: `where(angle_tolerance=…)` is not passed to `_resolve`;
   chain agreement always uses 1e-9 rad (phys:398, 356; spat:79). `transform_between` has no tolerance parameter.
6. **D-A2-7 not confirmed.** A2 line 233 marks the per-question tolerance "please confirm (LABS-1.008)"; no ruling
   found in docs/. The implementation and stage-b.md:85 rely on it.
7. **`judgement` vocabulary beyond design.** Design uses "compatible" and conflicts/DISPUTED (A2 lines 138-140). The
   implementation adds `single` and None (phys:445-446). Also `judgement` is "compatible" whenever there are two or
   more candidates and no **verified** conflict, even when the status is UNKNOWN with an unverified disjoint pair in
   `conflict_details`, or DISPUTED because one candidate's chain is disputed (phys:430-446) [INFERRED].
8. **Plan 9.6 "Time" not reflected in output.** Plan 9.6: a derived pose holds only over the intersection of its
   inputs' intervals and its knowledge time is the latest recorded input. Implementation answers at instant t and
   reports neither interval nor knowledge time for derived candidates or transforms (phys:371-447). Point-in-time
   answers are consistent with the rule; the interval/knowledge-time reporting is absent.
9. **Plan Stage A / 9.6 chain-finding by TypeQL function** (`frames_reachable` finds the chain; Plan Stage A table,
   9.6 "Chains") vs A2: chains found in Python; `frames_linked` is inspection only (D-A2-2, approved; A2 lines
   129-131). Plan 9.6 "agree within 1e-9 m" (translation only) vs A2's added angular agreement (A2 line 28). The plan
   text is superseded by approved A2 decisions; recorded for completeness.
10. **GAP-SPATIAL-5 vs the identity design.** INV lines 93-95 and E2-D line 152 list "frames judged without same-as
    identity" as a gap and cite the code comment phys:199 ("DI-12, deferred"). Design: frames cannot be declared the
    same (same-as relates particulars only), so frame chains are unaffected and excluded from ID-8 by design (IB
    point 6 line 101; DI-12 line 399; ID-D 3.8 line 128, ID-8). DI-12 is closed (DI table line 51). The code comment
    is stale; whether GAP-SPATIAL-5 is a real gap needs the owner's ruling.
11. **Thing identity in `where`/`poses`.** Design ID-8: every reader selects contents by the subject's identity class,
    frame chains excepted (ID-D 9). `where`'s `about` set (UNKNOWN vs NOT_YET_KNOWN) and `alternatives` filter by the
    raw thing id (phys:391), and `poses` filters `facts_about` entries by the raw id in `positioned` (phys:97). ID-8's
    implementation note lists dynamics, agency, laboratory, organisation and mechanical, not physical
    (pre-e-identity-increment.md line 49). Whether positions stated about an alias are candidates/alternatives is
    unverified [INFERRED].
12. **`transform_between` reports no alternatives.** v0.2 6.2: unaccepted attestations by others are returned as
    alternatives. A2 requires alternatives for `where` only (line 145). `transform_between` has no `alternatives`
    field (phys:379), so an unreviewed transform is invisible there.
13. **Disputed edge off the reported chain is not cited.** Design: a disputed transform on any route gives DISPUTED
    (A2 line 48); v0.2 5.3 "never silent"; A2 "search.inconsistent lists the edge, its sources" (line 46-47) covers
    inconsistent edges only. Implementation: a disputed but consistent edge on a non-shortest route makes the answer
    DISPUTED with reason "a transform on a chain is disputed", but it appears neither in `chain` nor in
    `search.inconsistent` (phys:360-367), so its attestations are not reported.
14. **Truncated candidate through a disputed edge.** Design (LABS-1.009): truncated-but-reached returns the shortest
    chain's transform as an unverified UNKNOWN candidate (A2 lines 56-58). Not covered: if that chain contains a
    disputed edge, the implementation still returns the composed transform (phys:347-350), while a complete search
    would return no transform (A2 line 48).
15. **`source == target` and NOT_YET_KNOWN.** Not covered by design. Implementation returns INFERRED with an identity
    transform and an empty chain (no premises) for any id, even an unknown frame (phys:325-329, 379); the harness
    rule "a derivation with no premises is fabricated" (stage-e2-harness-review.md lines 92-98) could flag it.
    `transform_between` never returns NOT_YET_KNOWN, even with no visible transforms (v0.2 5.6 distinguishes it).
16. **`verified` for a complete no-chain search.** Design states `complete: true` for this case (A2 line 53) but not
    `verified`; implementation sets `verified: false` (phys:335). In `where` such incomparable entries do not make
    the answer unverified (phys:431), consistent with A2 line 62-63.
17. **Status order among supported kinds.** v0.2 5.6: OBSERVED/ASSERTED/STIPULATED/INFERRED have "no default order";
    observation → OBSERVED. A2 line 143-144 and IC-D line 120 choose "most direct status among direct candidates"
    (STIPULATED > ASSERTED > INFERRED, semantics.py:162-170) and report observations as ASSERTED. Design-to-design
    difference, resolved for A2 by its own text; recorded because v0.2 is frozen.
18. **`alternatives` scope.** A2 line 145: "Unreviewed claims are listed as alternatives" (in the context of the asked
    question). Implementation lists unreviewed position claims about the thing in **any** frame, as ids only, without
    frame or relation to candidates (phys:390-392; model.py:1275-1277).
19. **Ordering is implementation-only.** No design text fixes the order of `candidates`, `conflicts`, `poses`,
    `chain` tie-breaks or `frame_info` lists; the implementation sorts `poses` by frame and edges by (parent, child,
    support) (phys:105, 208). Because `conflicts` are candidate indices, their meaning depends on this order.
20. **INV says `where`/`transform_between`/`poses`/`frame_info` are undocumented in reader-docs** (INV line 52-53);
    `benchmark/e2/spec/reader-docs.md` now documents them (RD lines 108-242, GAP-HARNESS-4). INV is out of date on
    this point only.
21. **`frame_info.name` is not judged.** A1 line 29-32 says reading goes through `facts_about`/`value_at` so every
    answer is judged; `names()` reads `has name` directly, ignoring world, perspective and time (phys:176-186).
