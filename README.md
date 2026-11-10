# Semantic World Model (research)

**An experimental Noodlelab research project. Nothing here is a product, a standard or a finished ontology.**

The question we are investigating: can one **small, evidence-aware semantic core**, held in
[TypeDB](https://typedb.com) 3.x, give quite different applications a shared way to represent their environment?
That means what exists, what happened, when, where, who knows it, and on what evidence. The applications range
from a robot to a video understanding pipeline to an agent's long-term memory.

## Status (2026-11-10)
| Phase | State |
|---|---|
| 1. Research and architecture | Complete ([docs/phase-1](docs/phase-1/README.md)) |
| 1B. Research validation and architectural review | Complete ([docs/phase-1b](docs/phase-1b/README.md)) |
| 1C. Preparation: semantics, environments, baselines | Complete ([docs/phase-1c](docs/phase-1c/README.md)) |
| M1. Executable foundational core | Superseded by Core 0.3; its 41 tests are ported ([docs/m1](docs/m1/README.md)) |
| World Ontology v0.1 | Proposal reviewed; D2 preferred ([docs/architecture/world-ontology-v0.1.md](docs/architecture/world-ontology-v0.1.md)) |
| World Ontology v0.2 | **Frozen baseline** ([docs/architecture/world-ontology-v0.2.md](docs/architecture/world-ontology-v0.2.md)) |
| **Core 0.3** | **Merged into `main` (2026-11-10): World Ontology v0.2 implemented, 78 tests** ([docs/core-0.3](docs/core-0.3/README.md)) |
| **Core 0.4 Stage A0** | **Merged into `main` (2026-11-10, c9750d2):** proposition ids, profile subtypes and roles, functional constraints as data, and four corrections; 128 tests ([docs/core-0.4](docs/core-0.4/README.md)) |
| **Core 0.4 Stage A1** | **Merged into `main` (2026-11-10, cb1e201):** physical structure and the gearbox reference world; 142 tests ([docs/core-0.4/stage-a1.md](docs/core-0.4/stage-a1.md)) |
| Core 0.4 Stage A2 | On branch `feature/core-0.4-a2-spatial`, awaiting review (LABS-1.007): positions derived across frames, position-conflict judgement; 158 tests ([docs/core-0.4/stage-a2.md](docs/core-0.4/stage-a2.md)) |
| Next | World-representation layer (composition, causality, space and frames, quantities, agency, domain extensions); not started |

Start with **[Phase 1C's outstanding decisions](docs/phase-1c/07-outstanding-decisions.md)**, then the
[Phase 1B executive summary](docs/phase-1b/07-executive-summary.md). Phase 1 ([docs/phase-1/README.md](docs/phase-1/README.md))
is kept unchanged; its corrections are in [changes-to-phase-1.md](docs/phase-1b/changes-to-phase-1.md). **[docs/phase-1/verification-status.md](docs/phase-1/verification-status.md)** lists which findings are
measured and which rest on assumptions still to verify.

## Research objectives
1. **Lightweight semantic infrastructure:** a compact core with optional domain modules, so a constrained
   application loads only what it needs. The cost of the model and the cost of the database are measured separately.
2. **Meaningful world understanding:** important entities, events, identities, times and evidence, rather than an
   exhaustive list of everything observed.
3. **A reusable foundation:** substantially different applications share the core through *World Ontology Profiles*
   (a pinned set of modules plus the questions it must answer).

Principles: semantic correctness before size; evidence before assertion; no invented continuity (a fact's end is
unknown until observed); real TypeDB operations only; every claim of advantage tested against a simpler baseline.

## The three reference applications
| Application | What it tests | State |
|---|---|---|
| **ROS 2 robotics integration** | A robot builds and queries a persistent semantic record of its environment, outside its real-time control, from simulated or recorded (rosbag2) data. Simulators give independent ground truth | Designed ([ros2-reference-application.md](docs/phase-1/ros2-reference-application.md)); proposed as the first real test |
| **Visual World Explorer (VWE)** | A short video becomes a coherent, queryable world model with a grounded explanation | A new application, not yet built. (Not the same as the [Noodlelab Visual Explorer](https://github.com/Calhem/typedb-noodlelab-visual-explorer), a 3D vehicle explorer) |
| **GUPI agent memory** | Whether a shared profile keeps [GUPI](https://github.com/Calhem/typedb-gupi-agent-memory)'s evidence and time model while improving coherence and interoperability | GUPI research is paused; a parity check only, until an independent answer set exists |

## Repository
- `docs/architecture/`: the ontology architecture proposal; `docs/typedb-modelling-best-practices.md`: verified
  TypeDB modelling constraints.
- `schema/`, `src/worldmodel/`, `tests/`: the world model (TypeQL schema modules, Python interface, tests);
  `scripts/bench_query_paths.py`: selective vs full query benchmark.
- `docs/phase-1/`: framework comparison, core ontology proposal, modules and profiles, TypeDB capability
  assessment, competency questions, experiment protocols, ROS 2 design, recommendation and decisions.
- `environments/`: isolated PostgreSQL 18, TypeDB and ROS 2 environments with smoke tests.
- `evaluations/gupi-lme/`: the GUPI LongMemEval answer-baseline harness.
- `probes/typedb_capabilities.py`: checks what TypeDB 3.14.1 accepts on the points the design depends on, in
  throwaway databases only (`wm-probe-*`). Output: `probes/typedb_capabilities.out.json`. Run it with any Python
  that has `typedb-driver` 3.x and can reach a server, for example
  `docker exec -i <container> python - < probes/typedb_capabilities.py` (`TYPEDB_ADDRESS` sets the server;
  `admin`/`password` are TypeDB's local development defaults).

## Notes
Every robot, vehicle, person and scenario in this project is invented. Licence not yet chosen (decision D5 in the
Phase 1 README); until then, all rights are reserved by the author.
