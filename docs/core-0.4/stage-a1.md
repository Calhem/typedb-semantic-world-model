# Core 0.4 Stage A1: physical structure and a reference world (LABS-1.006)

**Status (2026-11-10): implemented on `feature/core-0.4-a1-physical`, awaiting review. Not merged; Stages B-D not
started.** Base: `main` at c9750d2 (Core 0.4 Stage A0 merged). Plan: [core-0.4-plan.md](../plans/core-0.4-plan.md),
Stage A. Ontology: World Ontology v0.2 (frozen), §3.4-3.5.

## Run it
```bash
docker compose -f environments/compose.yaml up -d typedb
uv run python -I scripts/show_reference_world.py          # builds database wm-reference-gearbox and prints it
uv run pytest -q tests/test_g_a1_physical.py              # 14 tests
```
The database is kept for inspection (TypeDB Studio on the `wm-typedb` container, or the queries below); `--drop`
deletes it. Saved output: [reference-world-output.md](reference-world-output.md).

## Schema added (module `core-0.4-a`, version 0.4.0-a1; `schema/core/core-0.4-a.tql`)
| Type | Roles | Owns | Meaning |
|---|---|---|---|
| `constitution` (proposition) | constituted, constituent | — | what a particular is made from (the cover from an aluminium blank); not part-of |
| `positioned-in` (proposition) | positioned, frame | `x-min` … `z-max` (metres), optional `qw qx qy qz` | a position in a frame as per-axis ranges (lower = upper: exact), optional orientation |
| `anchored-to` (proposition) | frame, anchor | — | a frame attached to a particular; functional constraint (frame → anchor): one anchor at a time |
| `frame-transform` (proposition) | parent, child | `tx ty tz`, `qw qx qy qz` | the child frame's pose in the parent: p_P = R(q)·p_C + t (plan 9.6) |

Players: every `particular` can be constituted, a constituent, positioned and an anchor; `spatial-frame` (a Core 0.3
reference system) is the frame of positions, anchors and transforms. Materials are categories: `classified-as(x,
steel)`, with `classified-as(steel, material)` marking a category as a material (D-A1-1). No new foundational
category, entity or attribute kind beyond the plan's Stage A table.

API (`src/worldmodel/physical.py`, mixed into `WorldModel`): `position`, `relate_frames`, `anchor_frame` (writing,
through ordinary attestations; ranges must be finite with lower ≤ upper; quaternions must be within 1e-9 of unit
norm); `composition`, `contents`, `poses`, `frame_info`, `materials`, `names` (reading, through `facts_about` and
`value_at`, so every answer is judged for a world, perspective, knowledge time and valid time). Proposition parameters
are now declared per type (`PARAMS`: has-quality, positioned-in, frame-transform) and fetched only for installed types
a question can involve.

## The reference world (`src/worldmodel/examples/gearbox.py`)
An invented, unbranded concept assembly: a two-stage spur gearbox (GBX-100) on a workbench in a workshop bay.
Dimensions and masses are illustrative, not real specifications.

| Group | Ids |
|---|---|
| places (containing environment) | `workshop` ⊃ `bay-1`, `store-shelf` (part-of) |
| physical objects | `bench-1`, `gbx-100` (assembly), `shaft-asm-in` (sub-assembly), `housing`, `cover`, `gasket`, `input-shaft`, `output-shaft`, `gear-in`, `gear-out`, `bearing-1`, `bearing-2`, `bearing-3` (spare), `bolt-1`…`bolt-4`, `alu-blank-7` (stock), `scale-3` (instrument) |
| agents (sources) | `system`, `design-office`, `inspector` (social objects); `scale-3` also attests |
| categories | kinds: `gearbox`, `sub-assembly`, `housing-part`, `shaft`, `gear`, `bearing`, `seal`, `fastener`, `workbench`, `stock`, `instrument`; materials: `steel`, `cast-iron`, `aluminium`, `rubber`, `magnesium` (each classified as `material`) |
| frames | `f-workshop` (anchored to workshop) → `f-bench` (bench-1; t = (4.0, 2.5, 0.0) m, 90° about z) → `f-gearbox` (gbx-100; t = (0.60, 0.40, 0.92) m) |
| measures | quality kind `mass`, unit `kg` |
| worlds | `actual`; `plan-steel-cover` (hypothetical, branches 2026-11-07 09:00) |

Facts, all attested:
- **Composition:** gbx-100 has 11 direct parts, one of them the input shaft sub-assembly (input shaft, pinion,
  bearing). Constitution: cover made from alu-blank-7.
- **Containment:** bench-1, gbx-100 and scale-3 are located at bay-1; bearing-3 is on store-shelf until T1.
- **Positions:** bench-1 in f-workshop (±5 cm, observed, oriented 90°); gbx-100 in f-bench; every component in
  f-gearbox (exact design positions).
- **Materials and kinds:** each thing is classified with a material and a kind.
- **Measurement vs design:** the housing mass is observed by scale-3 as 12.35-12.45 kg (basis observation) and stated
  by the design office as 12.5 kg (testimony). Both are accepted and both are kept.
- **Time:** at T1 (2026-11-05 14:00), bearing-1 is replaced by bearing-3. Bearing-1's part-of and position end, and it
  moves to the shelf; bearing-3 is fitted. History keeps both.
- **Perspective:** the inspector claims the cover is magnesium and accepts the system's list of materials only. The
  system has not accepted the claim.
- **Hypothetical:** in `plan-steel-cover` the cover is stipulated steel and aluminium is denied, from the plan time.

## Selected results (actual output, `reference-world-output.md`)
```
Composition of gbx-100 at 2026-11-06 12:00
- gbx-100: bearing-2, bolt-1..4, cover, gasket, gear-out, housing, output-shaft,
  shaft-asm-in: bearing-3, gear-in, input-shaft          (before T1: bearing-1 instead of bearing-3)
Containment: workshop: bay-1: bench-1, gbx-100, scale-3 [ASSERTED]; store-shelf: bearing-1 [ASSERTED]
Materials: housing cast-iron; cover aluminium; cover for the inspector: magnesium; cover in the plan: steel
f-bench: anchored to bench-1; in f-workshop: translation (4.0, 2.5, 0.0), rotation (0.707107, 0, 0, 0.707107) [ASSERTED]
bench-1 in f-workshop: x (3.95, 4.05), y (2.45, 2.55), z (0.0, 0.0), oriented 90° about z [ASSERTED]
bearing-1 after T1: no position holds; bearing-3 in f-gearbox: (-0.05, 0.06, 0.08) [ASSERTED]
```
Raw TypeQL (Q1-Q8 in the script) return the stored records rather than judged answers. For example, Q3 lists all
material classifications, including the inspector's magnesium claim and the plan's steel; Q4 lists both of bearing-1's
position attestations, one open-ended and one ended at T1.

## Tests (`tests/test_g_a1_physical.py`, 14)
- objects, places, frames, categories, quality kinds, units and agents are different kinds of record;
- identity is the id, and a description is text;
- kinds and materials are classifications, and an assembly has no single material;
- composition is a tree that changes at T1 and matches the `parts` closure; the TypeDB function `parts_in` (records
  only) returns both bearings;
- constitution is not composition;
- containment through places; a component has no place of its own;
- frames: anchors and transforms;
- positions as ranges, changing over time;
- invalid ranges, quaternions and parameters are rejected;
- one anchor per frame (functional: DISPUTED, with `holds` conflicts);
- measurement vs design;
- the inspector's perspective;
- the hypothetical plan;
- selective/full-load equivalence over a battery of questions;
- the module is opt-in and installs on an existing database.

Full suite: 142 passed, twice on each path. Only the intentional `wm-reference-gearbox` database remains.

## Decisions and deviations for review
| # | Decision | Why | Review |
|---|---|---|---|
| D-A1-1 | `concept plays classified-as:classified`, so a category can be classified as a material | the plan makes materials categories, but Core 0.3 had no way to say which categories are materials; this adds one role-playing line, not a type | please approve |
| D-A1-2 | `positioned-in` and `frame-transform` declare **no** functional constraint in A1, so two different positions of one thing in one frame are both listed, not judged | the plan's slot (positioned, frame) has its value in parameters (ranges), and v0.2 makes overlapping ranges compatible and disjoint ones a conflict: range-aware conflict detection is a new rule, deferred to A2 | deferral |
| D-A1-3 | the physical module is opt-in (`PHYSICAL_MODULES`), not in `DEFAULT_MODULES` | keeps every Core 0.3 and A0 test unchanged (two would otherwise change their expected module list again); proposal: make it default when Stage A is complete | please confirm |
| D-A1-4 | frame-transform composition (derived poses through chains, inverse use, range propagation, chain agreement) is **deferred to A2**; transforms are stored and retrieved only | LABS-1.006: defer rather than ship a partial implementation | deferral |
| D-A1-5 | positions and transforms are content parameters, so every new position is a new proposition (keys at 12 significant digits) | as planned; proposition growth with frequent pose updates is U-3 | U-3 open |

## What the model can represent now, and what is absent
**Can:**
- physical objects with stable ids, separate from their names and descriptions;
- kinds and materials as classifications;
- assemblies and sub-assemblies (part-of), and what things are made from (constitution);
- containment through places;
- spatial frames attached to things, with stored transforms between them;
- positions with uncertainty ranges and orientation in a frame;
- measured values kept apart from design values, with their sources;
- all of it over time, per perspective and in hypothetical worlds, with the same answers on both query paths.

**Absent:**
- poses derived through frame chains (A2) and conflict judgement between positions;
- geometry and extents (shapes, bounding volumes; v0.2 keeps spatial regions external);
- motion and dynamics (Stage B);
- measurement activities as events, and quantities with units and conversions (Stage C);
- agency and capabilities (Stage C);
- domain profiles (Stage D).
