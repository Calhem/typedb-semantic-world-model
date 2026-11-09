# 7. Executive summary

**Question:** is the proposed architecture justified by existing research, and can it be tested rigorously before we
invest in implementation?

**Answer:** partly justified, and testable. Existing work already covers most of what Phase 1 described. What
survives is narrower: one small, evidence-aware core that a robot, a video pipeline and an agent memory can share,
with measured information loss and cost. Whether TypeDB is the right store for it is an open question, and the
revised evaluation can answer "no".

## What Phase 1B verified
- **KnowRob already has robot beliefs, perspectives, confidence and uncertain time intervals** in released code.
  SOMA is already a modular robotics ontology on DUL. Hydra and Khronos already maintain changing scene graphs on
  ROS 2. Graphiti already does bitemporal agent memory. An upper ontology, robot memory or bitemporality would not
  be novel.
- **DOLCE models roles as a time-indexed classification relation.** That makes TypeDB's one-type-per-instance rule
  a natural fit, not the conflict Phase 1 suggested.
- **Strict "no invented continuity" leaves a robot knowing nothing about the present** (probe). Persistence
  policies and observed absence are needed in the core.
- **ROS 2 Lyrical (LTS to 2031) runs in arm64 Ubuntu containers**, with Nav2, Gazebo bridges and a TurtleBot3 sim
  available as binaries. `map` poses can jump, tf2 keeps 10 s, and tracker ids are optional, all verified.

## Retain from Phase 1
- A small core (about 18 types after revision) with modules and three profiles.
- The descriptive 3D stance, with time on relations.
- GUPI's evidence model: observations, claims, reviews, open-world answers.
- ROS 2 as the first substantial integration, with the semantic layer kept out of control loops.
- No geometry, pixels or raw signals in the semantic layer.

## Change
- **Claim:** from "universal" to *domain-neutral core plus profiles, tested on cross-application sharing* (AD1).
- **Foundation:** minimal core *aligned* to DUL with a tested mapping (AD2).
- **Facts:** the fact relation *is* the claim, at about one relation per fact, not four or five (AD4).
- **Time:** three time axes plus a time reference system on every value, not five axes (AD5).
- **Gaps:** add persistence policies (answers marked PRESUMED) and observed absence (AD6).
- **Uncertainty:** separate belief confidence from measurement uncertainty (AD8).
- **Method:** specification-first, and the same specification built in TypeDB and in PostgreSQL 18 (AD11, AD12).
- **Evaluation:** seven hypotheses with failure conditions, sealed and independent data, and ablations that
  separate the ontology, the database and the application code (AD13).
- **GUPI:** an answer-correctness test on independent gold answers, not parity only (AD15).

## Reject
- A universal ontology as the goal.
- Adopting DUL/SOMA wholesale (LGPL, OWL semantics, robotics-centred). Use it as the robotics reference instead.
- Typing things by detector labels or roles (breaks identity: probe).
- Struct values for coordinates in 3.14.1 (cannot be inserted: probe).
- The idea that TypeDB's modelling fidelity implies better answers. Nothing so far shows it, and it is now a
  hypothesis that can fail.

## Strongest case against the whole project
For robotics, KnowRob + SOMA plus a scene graph may already be enough. For memory, text retrieval is hard to beat
(GUPI). Cross-application sharing may be a solution without a user. The evaluation is designed to show this if it
is true: if H1 fails, the ontology adds nothing; if H2 or H4 fails, TypeDB is the wrong store.

## Decisions for you
See the end of [06-decision-register.md](06-decision-register.md): the narrowed claim, the revised core, the
method and thresholds, two downloads (PostgreSQL 18; ROS 2 + Gazebo, about 2-3 GB), who writes the withheld sets,
and whether to run the GUPI answer test.

**Not done:** Phase 2, any ontology TypeQL, any download. Full papers for SOMA, Hydra, Khronos and Zep were not
read (abstracts and repositories only). IEEE CORA and the ISO text were not read (paywalled).
