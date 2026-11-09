# Semantic World Model (research)

A Noodlelab research project: a small, evidence-aware semantic world ontology for TypeDB 3.x, intended to be shared
by a ROS 2 robot, a video understanding pipeline (Visual World Explorer) and an agent memory (GUPI).

**Status (2026-11-09): Phase 1 (research and architecture) complete, stopped for review.** No ontology has been
implemented. Start with [docs/phase-1/README.md](docs/phase-1/README.md).

- `docs/phase-1/`: framework comparison, ontology proposal, profiles, TypeDB assessment, competency questions,
  experiment protocols, ROS 2 design, recommendation and open decisions.
- `probes/typedb_capabilities.py`: checks what TypeDB 3.14.1 accepts on the points the design depends on; it uses
  throwaway databases only. Run it through any container that has the TypeDB Python driver, for example
  `docker exec -i noodlelab-api python - < probes/typedb_capabilities.py`.

Any vehicle, robot or scenario in this project is invented. No licence chosen yet (decision D5).
