# Core 0.4 Stage A2: spatial reasoning across frames (LABS-1.007)

**Status (2026-11-10): implemented on `feature/core-0.4-a2-spatial`, awaiting review. Not merged; Stages B and C
not started.** Base: `main` at cb1e201 (Stage A1 merged). Plan: [core-0.4-plan.md](../plans/core-0.4-plan.md), Stage A
and 9.6. Ontology: World Ontology v0.2 §3.5 (C8), §5.3; no new spatial ontology.

## Run it
```bash
uv run python -I scripts/show_spatial_reasoning.py      # builds wm-reference-gearbox (with A2 extensions) and prints
uv run pytest -q tests/test_g_a2_spatial.py             # 16 tests
uv run python -I scripts/measure_physical.py . --extended
```
Saved output: [spatial-reasoning-output.md](spatial-reasoning-output.md). Measurements: [bench-a2/](bench-a2/).

## Conventions (plan 9.6, unchanged; `src/worldmodel/spatial.py`)
- **Frames and units.** Frames are right-handed Cartesian. Lengths are in metres and angles in radians.
- **Rotations.** A rotation is a unit quaternion (w, x, y, z), using the Hamilton product and active rotation
  (v' = q v q*). A norm more than 1e-9 from 1 is rejected on write. q and −q are the same rotation.
- **Transform direction.** `frame-transform(parent P, child C)` holds (q, t) and maps a point in C to P:
  p_P = R(q) p_C + t.
- **Composition.** T_AC = T_AB ∘ T_BC: R_AC = R_AB R_BC, t_AC = R_AB t_BC + t_AB.
- **Inverse.** T_CP = (q*, −R(q*) t), computed and never stored. A chain step is `forward` (child → parent) or
  `inverse`.
- **Ranges.** A range box is mapped by transforming its 8 corners and taking their bounding box. This is
  conservative: the result contains the true region, and may be larger when the rotation is not axis-aligned.
  Rotations are exact.
- **Agreement.** Chains agree when their composed transforms are within 1e-9 m and 1 − |q₁·q₂| ≤ 1e-9.

## Frame chains (`transform_between`, `where`; `src/worldmodel/physical.py`)
- **Edges.** The `frame-transform` contents are judged for the asked world, perspective, knowledge time and valid
  time, as for any other content (inherited snapshots, acceptance, supersession). Each holding content is an edge,
  usable in either direction. A polarity-disputed content is kept and marked.
- **Chains.** Every simple chain up to 8 hops is found, shortest first. Each chain's composed transform and every step
  are reported: parent, child, direction, translation, rotation and the supporting attestations.
- **Missing.** No chain gives UNKNOWN, with the reason "no frame chain from X to Y". Nothing is invented.
- **Ambiguous.** Chains that disagree, or two disagreeing transform claims for one frame pair, give DISPUTED, with
  every chain listed. A chain that uses a disputed transform is also DISPUTED.
- **Cycles.** A component with more edges than a tree is reported as `cycle: true`. Consistent cycles still answer
  (INFERRED); inconsistent ones are DISPUTED.
- **Provenance.** A derived position is INFERRED under rule `frame-transform/v1` and cites the position attestations
  and the attestations of every transform on its chain.
- **Database side.** The TypeQL function `frames_linked` (module `core-0.4-a2`) lists frames linked by
  `frame-transform` records, in either direction, transitively. It is for inspection, like `parts_in`: it does not
  apply time, acceptance or perspective. It is verified to terminate on cyclic graphs (probe P3).

## Position judgement (v0.2 §5.3 rule 2: "disjoint ranges" are a functional conflict)
- **Candidates.** `where(world, thing, frame, t)` takes every position statement of the thing that holds for the
  perspective at t. Each is a candidate, either stated in the frame (direct) or mapped into it through a chain
  (derived). Candidates are compared but never merged into one range: measurements are not reconciled.
- **Identical** ranges are one content: one candidate with several supporting attestations.
- **Overlapping** ranges, including touching ones, are compatible. The answer keeps every candidate's own range.
- **Disjoint** ranges, or different orientations, conflict. The answer is DISPUTED and the conflicting pairs are
  listed.
- **Different frames** are compared after derivation into the asked frame. If no chain exists, the statement is
  listed as incomparable, never guessed.
- **Measurement uncertainty** is the ranges themselves, propagated conservatively. Status follows the evidence: a
  direct observation or testimony is ASSERTED, a derived position is INFERRED, a stipulation is STIPULATED.
- **Time, perspective and worlds.** Only statements that hold at t for the perspective count. Unreviewed claims are
  listed as alternatives. A variant's own position or transform overrides the inherited one.
- **The same rule everywhere.** Module `core-0.4-a2` declares two functional constraints whose value is the content's
  parameters (`@params`): (positioned, frame) → position and (parent, child) → transform. The shared conflict check
  `_conflicts` compares such values by range overlap and rotation equality (`spatial.params_compatible`). So `holds`
  reports disjoint positions as DISPUTED (F-4 consistency), and the variant override uses the existing exclusivity
  logic.
- **No identity from proximity.** Nothing here ever infers that two things are the same because they are close.

## Demonstration (actual output, `spatial-reasoning-output.md`)
| Question | Answer |
|---|---|
| Where is the gearbox relative to the workshop (2026-11-06 12:00)? | ASSERTED, compatible. Derived: (3.600, 3.100, 0.920) m, via f-bench → f-workshop (t = (4.0, 2.5, 0), 90°). Observed by cam-2: 3.55..3.65, 3.05..3.15, 0.90..0.94. The tag reader's claim is an unreviewed alternative |
| Where is the pinion relative to the bench? | INFERRED (0.620, 0.460, 1.000), via f-gearbox → f-bench. The camera's image-frame claim is incomparable (no chain from f-cam-2) |
| … relative to the workshop? | INFERRED (3.540, 3.120, 1.000), two hops |
| Where is the bench relative to the gearbox? | INFERRED x −0.650..−0.550, y −0.450..−0.350, z −0.920, an inverse two-hop chain with ranges |
| What changes when the workshop → bench transform changes (T2)? | the gearbox in the workshop moves to (6.600, 1.400, 0.920), citing the new transform; the pinion relative to the bench is unchanged |
| … in the plan world (the bench by the door, 180°)? | INFERRED (0.400, 0.600, 0.920), citing the plan's stipulated transform; the actual world is unaffected |
| Which claims conflict? | the tag reader's own perspective sees only its claim (5.0..5.2, 3.0..3.2). Once the system accepts it, the system's answer is DISPUTED: candidates 0 and 2, and 1 and 2, are disjoint. As known before that acceptance (`as_of`), it is still compatible |
| Earlier (2026-11-03)? | INFERRED (3.6, 3.1, 0.92): the observations had not started |

Part 2 of the output is raw TypeQL over the stored records:
- `frames_linked` from f-gearbox;
- every `frame-transform` record with its world, source and interval: the ended original, its restatement, the moved
  transform and the plan's;
- every position record of gbx-100.
None of these rows applies time, acceptance or perspective.

## Tests (`tests/test_g_a2_spatial.py`, 16)
- **Mathematics:** convention checks, composition and inverse identities, quaternion sign, parameter compatibility,
  conservative range propagation.
- **Frame chains:** multi-hop with rotations and inverse steps, with per-hop provenance; missing chains; consistent
  and inconsistent cycles; competing transform claims (perspective-dependent, `holds` DISPUTED).
- **Positions:** identical, overlapping and disjoint statements; comparison across frames through derivation; time
  (transform and position changes); perspective (alternative, accepted, rejected); hypothetical override and
  snapshot.
- **Reference world:** the demonstration questions, and selective/full-load equivalence over 41 spatial questions.

Full suite: **158 passed, twice on each path.** Only the intentional `wm-reference-gearbox` database remains.

## Performance against A1 (`scripts/measure_physical.py`, three alternating runs each, same A1 world)
| Question | A1 median of runs (ms) | A2 (ms) | TypeQL queries, A1 / A2 |
|---|---|---|---|
| poses(gear-in) | 20.4 / 21.4 / 22.1 | 24.9 / 22.3 / 24.8 | 14 / 14 |
| composition(gbx-100) | 350 / 373 / 365 | 355 / 313 / 383 | 212 / 212 |
| contents(workshop) | 110 / 147 / 133 | 147 / 107 / 134 | 86 / 86 |
| materials(cover) | 53.5 / 60.9 / 65.4 | 53.2 / 58.6 / 62.8 | 42 / 42 |
| frame_info(f-bench) | 22.5 / 22.6 / 25.3 | 20.6 / 25.9 / 23.8 | 15 / 15 |
| facts_about(housing) | 25.5 / 24.6 / 25.9 | 22.9 / 25.0 / 23.7 | 14 / 14 |
| build the world | 1.52 / 1.08 / 1.30 s | 1.27 / 1.36 / 1.47 s | — |
| database size | 442.6 KB | 445.2 KB (+0.6 %: two constraint declarations and the function) | — |

New A2 questions (A2 world with extensions, 463.9 KB): `where` 43-60 ms (32-35 queries), `transform_between`
8-10 ms (6-7 queries). On a default Core 0.3 database (no physical modules), queries per question are unchanged:
36.48 before and after, with identical answers.

## Decisions and deviations for review
| # | Decision | Why | Review |
|---|---|---|---|
| D-A2-1 | Functional constraints may take the content's parameters as their value (`@params`), compared by range overlap, rotation equality and exact numbers | needed so that position conflicts (v0.2: disjoint ranges) and variant overrides use the one existing conflict and exclusivity logic, rather than a second algorithm; an extension of A0.3's data model, not a new ontology | please approve |
| D-A2-2 | Chains are found in Python over the judged transforms. The plan's TypeQL function is implemented (`frames_linked`) but used for inspection only | a database function cannot apply time, acceptance and perspective (as with `parts_in`); the judged transforms of a world are few and are loaded in one query set | please confirm |
| D-A2-3 | All simple chains up to 8 hops are enumerated, to detect ambiguity; longer chains are not searched | plan 9.6 requires chains to agree; the bound keeps cyclic graphs finite | please confirm the bound |
| D-A2-4 | `where` reports candidates and a judgement (compatible / conflicting / single, plus incomparable) in a dict, not a new answer status; "incomparable" is not added to the status vocabulary | v0.2 has no INCOMPARABLE status; an incomparable statement leaves the answer UNKNOWN when nothing else is comparable | please confirm |
| D-A2-5 | `holds(positioned-in, roles)` names no parameters, so it cannot ask about one particular position; `where` is the question for positions | an existing API limit (parameters are not part of `holds`' question) | note |
| D-A2-6 | `extend_spatial` keeps the A2 additions out of the A1 world builder | the A1 tests and output stay valid unchanged | — |

## Risks and what remains absent
**Risks:**
- range propagation through rotated frames is conservative, so boxes grow along long rotated chains;
- chain enumeration is exponential in the worst case (bounded at 8 hops);
- `composition` makes one judged read per node (212 queries for the gearbox, an A1 design, not optimised);
- every new position or transform is a new proposition (U-3).

**Absent:**
- shapes and extents;
- motion and dynamics (B);
- measurement activities and units (C);
- agency (C);
- profiles (D);
- any visual frontend.
