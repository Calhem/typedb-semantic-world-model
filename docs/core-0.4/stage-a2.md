# Core 0.4 Stage A2: spatial reasoning across frames (LABS-1.007, LABS-1.008)

**Status (2026-11-10): implemented on `feature/core-0.4-a2-spatial`. The architecture was approved under LABS-1.008,
and the traversal and orientation corrections it required are applied (see "LABS-1.008 corrections"). Awaiting
review; not merged. Stages B and C not started.** Base: `main` at cb1e201 (Stage A1 merged). Plan: [core-0.4-plan.md](../plans/core-0.4-plan.md), Stage A
and 9.6. Ontology: World Ontology v0.2 §3.5 (C8), §5.3; no new spatial ontology.

## Run it
```bash
uv run python -I scripts/show_spatial_reasoning.py      # builds wm-reference-gearbox (with A2 extensions) and prints
uv run pytest -q tests/test_g_a2_spatial.py tests/test_g_a2_traversal.py   # 16 + 13 tests
uv run python -I scripts/measure_traversal.py --typedb  # traversal scaling (traversal-scaling.json)
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
- **Agreement.** Chains agree when their composed transforms are within 1e-9 m and their orientations within the
  angular tolerance (below). *Superseded (LABS-1.008): the original rule 1 − |q₁·q₂| ≤ 1e-9 silently accepted
  orientations up to 8.9e-5 rad apart.*

## LABS-1.008 corrections
### Traversal semantics (replaces the 8-hop path enumeration)
- **Edges.** The judged `frame-transform` contents for the asked world, perspective, knowledge time and valid time,
  each usable forward (child → parent) or inverse.
- **Search.** Breadth-first from the source, with no hop limit. Each frame is reached once, so cycles always
  terminate. Every reached frame gets the composed transform from the source along a shortest chain, and the shortest
  chain to the target is the one reported, step by step, with its sources.
- **Agreement, checked completely.** The edges that lie on any simple chain from source to target are exactly the
  edges of the biconnected blocks on the route between them in the block-cut tree (an iterative Tarjan search).
  Every such edge is checked against the composed transforms. All simple chains agree exactly when every one of
  these edges is consistent, within 1e-9 m and the angular tolerance. No path is enumerated, so graphs whose route
  count is exponential stay linear: a 16-rung ladder has 65,536 simple routes, and 49 edges are checked.
- **Outcomes.**
  - *Consistent:* INFERRED, `search.verified: true`.
  - *An inconsistent edge on a route:* DISPUTED, with **no transform chosen**. `search.inconsistent` lists the edge,
    its sources and the translation and angle gaps.
  - *A disputed transform on any route:* DISPUTED.
  - *A disagreement that is not on any route between the two frames:* does not affect the answer.
- **Resource limit, never a silent UNKNOWN.** One search examines at most `limit` edges (default 100,000, settable
  per call). The `search` metadata always says `complete` or `truncated`, plus frames reached, edges examined, hops,
  cycle, edges checked, `verified` and the inconsistent edges.
  - A completed search with no chain: UNKNOWN, reason "no frame chain from X to Y", `complete: true`.
  - A truncated search that did not reach the target: UNKNOWN, reason "search truncated after N edge examinations
    (limit L) without reaching Y", `truncated: true`.
  - A truncated search that did reach the target: answered from the shortest chain, marked `verified: false`, with
    reason "other chains were not checked for agreement".
- **Results.** `transform_between` returns `chain`, `frames` and `search`; each `where` candidate carries its
  `chain` and `search`. A candidate whose chains disagree has no position (x, y, z are None) and is DISPUTED.
  Incomparable statements carry their `search`, so a truncated search is visible there too.

### Orientation comparison policy
- **Measure.** Two orientations are compared by their angular separation, the angle of the relative rotation
  q₁* q₂, computed as 2·atan2(‖v‖, |w|). It is 0 for q and −q, and accurate for tiny angles.
- **Tolerance.** They agree when the separation is at most the angular tolerance. The tolerance is a policy
  parameter of the question (v0.2's Π): `where(..., angle_tolerance=...)`. The default is 1e-9 rad, because Core 0.4
  orientations are stated as exact values, so only numerical noise is absorbed. A caller can pass, for example, a
  sensor's stated angular accuracy.
- **Reporting.** The answer reports each conflict's kind (`disjoint ranges` or `orientations differ`), the
  separation and the tolerance used.
- **Where it applies.** The same measure serves the shared conflict check (`params_compatible`) and chain agreement.
  The constraint check in `holds` and the variant overrides use the default tolerance.
- **Nothing is reconciled.** Overlapping ranges mean the claims *can* both be true, not that they are equal. Each
  stays a separate candidate with its own provenance; nothing is averaged, intersected or weighted.

### `holds` (D-A2-5)
Unchanged. `where` is the position-specific query interface: `holds(positioned-in, roles)` names no parameters, so it
cannot single out one position. It still reports DISPUTED when the positions of a thing in a frame conflict.

### Traversal scaling (`traversal-scaling.json`; median of five; laptop, Python 3.13)
Resolver alone (no database):
| Graph | Frames | Edges | Hops | Edges examined / checked | Outcome | ms |
|---|---|---|---|---|---|---|
| chain 8 / 9 / 16 | 9 / 10 / 17 | 8 / 9 / 16 | 8 / 9 / 16 | 16 / 8 … 32 / 16 | INFERRED, complete, verified | 0.06 / 0.07 / 0.13 |
| chain 64 / 256 / 1,024 / 4,096 | 65 … 4,097 | 64 … 4,096 | 64 … 4,096 | 2× edges / edges | INFERRED, complete, verified | 0.45 / 1.9 / 8.9 / 38.1 |
| ladder 4 / 8 / 12 / 16 (simple routes: 16 / 256 / 4,096 / 65,536) | 10 … 34 | 13 … 49 | 5 … 17 | 2× edges / edges | INFERRED, cycles, verified | 0.08 / 0.13 / 0.19 / 0.36 |
| ladder 64 / 256 / 1,024 | 130 / 514 / 2,050 | 193 / 769 / 3,073 | 65 / 257 / 1,025 | 2× edges / edges | INFERRED, verified | 1.1 / 4.1 / 18.8 |
| random, 100 frames, 199 edges | 100 | 199 | 3 | 398 / 192 | INFERRED, verified | 0.84 |
| random, 1,000 frames, 1,999 / 5,999 edges | 1,000 | 1,999 / 5,999 | 5 / 2 | 3,998 / 1,922; 11,998 / 5,999 | INFERRED, verified | 10.5 / 24.8 |
| random, 10,000 frames, 19,999 edges | 10,000 | 19,999 | 6 | 39,998 / 19,299 | INFERRED, verified | 193 |
| ladder 64 with one inconsistent rung | 130 | 193 | 65 | 386 / 193 | DISPUTED, 2 inconsistent edges | 1.0 |
| chain 256, limit 100 | 257 | 256 | — | 100 / — | UNKNOWN, **truncated** | 0.17 |
| ladder 1,024, limit 1,000 | 2,050 | 3,073 | — | 1,000 / — | UNKNOWN, **truncated** | 1.6 |

Paths examined: one chain is composed per question (the shortest). Agreement is established by checking edges, so no
alternative path is enumerated. Through TypeDB (`transform_between`, transforms stored as attestations):
| Graph | Edges | TypeQL queries | ms | Outcome |
|---|---|---|---|---|
| chain 8 | 8 | 6 | 27.7 | INFERRED, complete, verified |
| chain 32 | 32 | 6 | 29.3 | same |
| chain 128 | 128 | 6 | 84.2 | same |
| ladder 32 | 97 | 6 | 64.8 | same |

The query count is constant: the world's judged transforms are loaded once per question. Time grows with the
records loaded.

## Frame chains (`transform_between`, `where`; `src/worldmodel/physical.py`)
- **Edges.** The `frame-transform` contents are judged for the asked world, perspective, knowledge time and valid
  time, as for any other content (inherited snapshots, acceptance, supersession). Each holding content is an edge,
  usable in either direction. A polarity-disputed content is kept and marked.
- **Chains.** *Superseded by LABS-1.008 (above):* originally every simple chain up to 8 hops was enumerated.
- **Missing.** No chain gives UNKNOWN, with the reason "no frame chain from X to Y". Nothing is invented.
- **Ambiguous.** Chains that disagree, or two disagreeing transform claims for one frame pair, give DISPUTED with no
  transform chosen (LABS-1.008). A chain that uses a disputed transform is also DISPUTED.
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

Full suite after LABS-1.008: **171 passed, twice on each path** (13 new in `tests/test_g_a2_traversal.py`). Only the
intentional `wm-reference-gearbox` database remains.

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
| D-A2-1 | Functional constraints may take the content's parameters as their value (`@params`): ranges by overlap (possible compatibility), orientations by angular separation under a policy tolerance, other numbers exactly | one conflict and exclusivity logic for role and parameter values | **conditionally approved (LABS-1.008)**; the orientation policy is now angular separation |
| D-A2-2 | Chains are found in Python over the judged transforms; the TypeQL function `frames_linked` is for inspection | a database function cannot apply time, acceptance and perspective | **approved (LABS-1.008)** |
| D-A2-3 | *Amended (LABS-1.008):* no hop limit; complete agreement checking through biconnected blocks; an explicit resource limit with `complete`/`truncated` metadata | the 8-hop bound could silently produce UNKNOWN and miss disagreeing chains | amended as required |
| D-A2-4 | `where` keeps incomparability (and search truncation) in its structured result, with no new answer status | v0.2 has no INCOMPARABLE status | **approved (LABS-1.008)** |
| D-A2-5 | `holds` unchanged; `where` is the position-specific query interface | parameters are not part of `holds`' question | **provisionally accepted (LABS-1.008)** |
| D-A2-7 | The angular tolerance is a per-question policy parameter (`angle_tolerance`), default 1e-9 rad; the shared constraint check (holds, variant overrides) uses the default | Core 0.4 orientations carry no stated uncertainty; a stored per-claim angular uncertainty would be a schema addition | please confirm (LABS-1.008) |
| D-A2-6 | `extend_spatial` keeps the A2 additions out of the A1 world builder | the A1 tests and output stay valid unchanged | — |

## Risks and what remains absent
**Risks:**
- range propagation through rotated frames is conservative, so boxes grow along long rotated chains;
- one search loads every judged transform of the world (constant query count; time grows with the number of
  transforms);
- `composition` makes one judged read per node (212 queries for the gearbox, an A1 design, not optimised);
- every new position or transform is a new proposition (U-3).

**Absent:**
- shapes and extents;
- motion and dynamics (B);
- measurement activities and units (C);
- agency (C);
- profiles (D);
- any visual frontend.
