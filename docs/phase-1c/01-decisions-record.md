# 1. Provisional decisions recorded (2026-11-09)

Decisions given by the project owner after the Phase 1B review. "Provisional" means approved for preparation work;
the ontology itself stays on hold until the revised architecture is reviewed again.

| Phase 1B ref | Decision | Owner's ruling | Conditions |
|---|---|---|---|
| AD1 | Research claim | **Approved.** A compact, reusable semantic foundation with measurable interoperability, correctness and computational cost | **No novelty claimed** for capabilities KnowRob or other systems already demonstrate |
| AD2-AD10 | Revised core semantics | **Approved in principle** | Subject to detailed architectural review (this phase: [02-semantic-review.md](02-semantic-review.md)) |
| AD11 | Specification-first method | **Approved** | — |
| AD12 | Baselines | **Approved:** A event log / current state; B PostgreSQL 18 implementing the shared specification; C TypeDB implementing the same specification | — |
| AD12 | PostgreSQL 18 download | **Approved for installation** | — |
| AD14 | ROS 2 + Gazebo download | **Approved for installation** | Disk-space checks and a reproducible setup |
| AD15 | GUPI answer-quality evaluation | **Approved for preparation and execution** | Must not alter the existing GUPI implementation; paid API calls need a cost estimate and separate approval |

**Still on hold:** ontology implementation (Phase 2), the ROS 2 adapter, any new application functionality.

**Carried forward unresolved:** the thresholds (proposed in 04-comparative-evaluation-plan.md
for approval), who authors the withheld sets (format in 05-withheld-evaluation-spec.md),
D2 name, D5 licence, D8 outage spool.
