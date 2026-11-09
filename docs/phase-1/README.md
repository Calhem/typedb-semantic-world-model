# Phase 1: research and architecture (for review)

**Status (2026-11-09): stopped for review. No TypeQL ontology written.** Which findings are measured and which are
assumptions: [verification-status.md](verification-status.md). The only code is a capability probe, run in
throwaway databases. The existing Visual Explorer and GUPI repositories were read, not changed.

| Deliverable | Document |
|---|---|
| Framework comparison | [framework-comparison.md](framework-comparison.md) |
| Design principles + upper ontology proposal | [upper-ontology-proposal.md](upper-ontology-proposal.md) |
| Domain taxonomy, module boundaries, profiles | [modules-and-profiles.md](modules-and-profiles.md) |
| TypeDB capability assessment (with probes) | [typedb-capability-assessment.md](typedb-capability-assessment.md) |
| Competency questions (22) | [competency-questions.md](competency-questions.md) |
| Experiment protocols | [experiment-protocols.md](experiment-protocols.md) |
| ROS 2 reference application | [ros2-reference-application.md](ros2-reference-application.md) |
| What is verified, assumed or incomplete | [verification-status.md](verification-status.md) |
| Critique, recommendation, open decisions, plan | this page |

## What I found in the existing work
- **The existing "Visual Explorer" is not a video system.** typedb-noodlelab-visual-explorer is a 3D engineering
  explorer of a concept vehicle (382 components, systems, dependencies) backed by TypeDB. The brief's Visual World
  Explorer (video in, world model out) does not exist yet. It should be a new application. The vehicle model is
  still useful: as held-out *input data* for the portability experiment (part-of, systems, dependencies).
- **GUPI already solved much of the epistemic layer.** Its core (observations, one claim per attestation, evidence
  spans, reviews, supersession, alternatives, reviewable identity, five time axes, open-world answers) answers the
  brief's identity, time and evidence problems for text. The proposed core reuses it.
- **GUPI has no answer-level baseline.** The brief says GUPI has "existing baseline results" to compare against. It
  has retrieval baselines (LoCoMo, LongMemEval, development only) and a 15-question developer-written answer set. The
  answer-quality comparison was never run, because no independent question pack exists, and the research is paused
  (final report, 2026-11-09). So Experiment 5 can test parity, not improvement, until that pack exists.
- **GUPI's central finding** is the most important input here: TypeDB's typed model was a modelling benefit, not a
  measured answer or recall gain, on chat data; most reasoning ran in Python; and extraction, not storage, was the
  bottleneck. Its report names dense, explicit-relationship domains such as robotics as the promising untested case.

## Critique of the proposal
1. **Substantial prior art.** KnowRob with SOMA/DUL and NEEMs already offers an upper ontology, an everyday-activity
   and robotics ontology, and persistent robot episodic memory. 3D scene graphs (Hydra, Khronos) give persistent
   object identities from perception. Cyc, SUMO and BFO are upper ontologies decades in the making. OpenCog's
   AtomSpace is a typed hypergraph knowledge store. Agent memory has bitemporal graphs (Graphiti, GUPI). What could
   be new is narrow: *one small, evidence-aware core in a typed hypergraph database, shared by a robot, a video
   pipeline and an agent memory, with measured costs.*
2. **A universal ontology is not feasible, and v1 should not claim to be one.** Every attempt (Cyc, SUMO, IEEE SUO)
   either stayed proprietary, grew unwieldy or never converged. "Universal" should be read as "domain-neutral core
   + profiles", and judged by Experiment 1 on a held-out domain.
3. **Foundational frameworks conflict.** BFO is realist, DOLCE descriptive; a model of beliefs and hypotheses is
   descriptive, so BFO alignment will be a lossy mapping. 3D vs 4D identity must be chosen once (recommend 3D, time
   on facts). Measurement and time patterns differ across SOSA, PROV and OWL-Time.
4. **TypeDB's advantage is real but specific.** It is in modelling: n-ary events, facts about facts, role
   specialisation and a checked schema (probes 1, 2, 7). It costs us multiple classification, namespaces and value
   metadata (probes 3-5), and has no geometry, vector or full-text index and no embedded mode. Most
   interoperability standards are OWL/RDF, so every reuse is a mapping.
5. **Profiles add complexity.** Without namespaces, profiles share one name space; modules can change core types
   (probe 10); versions multiply. Keep one version number and three profiles in v1.
6. **Constrained devices are at risk.** TypeDB is a server (218 MB image; 0.2-1.7 GB memory here), not a library.
   It fits a robot's main computer or a base station, not a microcontroller. The ontology can be light; the runtime
   is not. Measure both separately, as the brief asks.
7. **Simpler representations will win in places.** For "where is it now", an in-memory dictionary or a scene graph
   is faster. For narrative video questions, a direct video-to-text model is likely better. For chat memory, GUPI
   found text retrieval hard to beat. The structured model should win on history, provenance, disputes,
   multi-agent knowledge and exchange between applications; the experiments are designed to show where.
8. **Evaluation independence is the biggest delivery risk.** The v1 criteria (90% precision, 80% event coverage)
   need independently annotated data. GUPI never found outside annotators. **Simulation ground truth (ROS 2) solves
   this for robotics**; video and memory still need people.
9. **Six domains is too many for v1.** Three synthetic scenarios (warehouse, social, lunar) plus one real track
   (ROS 2) is enough to test the architecture.

## Recommendation
**Proceed, narrowed.** Build a small evidence-aware core (≈20 types) in a new, independent repository, prove it on
synthetic scenarios against a simple baseline, then on ROS 2 simulation, and only then on video and GUPI.

- **Repository:** independent (this one; public on GitHub since 2026-11-09, decision D1). VWE, the ROS 2 adapter and GUPI consume its
  modules. The ontology has its own versioning, tests and licence. GUPI is paused and the vehicle explorer has its own
  roadmap, so neither should host it.
- **Order:** core → three scenarios + baseline → ROS 2 → GUPI parity → video. ROS 2 moves ahead of video because its
  relationships are explicit (no extraction bottleneck) and simulation gives independent ground truth.

## Smallest meaningful implementation (Phase 2 proposal)
1. `core` module (≈20 types, upper-ontology-proposal.md), with the naming index and core-protection tests.
2. Fixtures for scenarios W, S and L, authored separately from the queries where possible.
3. Competency questions 1-20 as named TypeQL queries with expected answers, run in disposable databases.
4. Baseline B0 (JSON event log + state dictionary) answering the same 20 questions.
5. A one-page result: which questions each answers, concepts per fact, ingest and latency for both.

**Done means:** all 20 questions pass on TypeDB, the core needed no change for scenario L after W and S, and we know
which questions B0 can't answer. Estimated size: a few hundred lines of TypeQL and Python. No video, no ROS, no GUPI
changes.

## Unresolved decisions (for you)
| # | Decision | Options | My recommendation |
|---|---|---|---|
| D1 | Repository and visibility | new public repo / new private repo / keep local | **Decided 2026-11-09: new public repository** |
| D2 | Name | "semantic world model" / "world ontology" / other | Avoid bare "world model" (now means learned video-prediction models) |
| D3 | Foundational stance | DOLCE-style descriptive / BFO realist | Descriptive, 3D, with a BFO mapping for science |
| D4 | Every contingent fact a claim? | always / profile may declare static facts | Profiles may declare static facts; measured in Exp. 6 |
| D5 | Licence | Apache-2.0 (code) + CC BY 4.0 (spec) / other | Apache-2.0 + CC BY 4.0 |
| D6 | Independent annotators for video and memory | find people / simulation and synthetic only / defer | Robotics first with simulator truth; find annotators before Phase 6 |
| D7 | ROS 2 environment | Docker on this Mac / a Linux machine | Docker, headless, replaying bags; needs approval to download images |
| D8 | Outage spool file in the ROS adapter | allowed as a buffer / TypeDB-only, drop on outage | Allowed, bounded, counted (it is never queried) |
| D9 | Experiment 5 (GUPI) | parity only now / wait for an independent pack | Parity only; no improvement claim |
| D10 | Scope of the six domains | all six in v1 / three + ROS 2 | Three synthetic + ROS 2 |

## Implementation plan (after approval)
| Phase | Work | Stop for review when |
|---|---|---|
| 2 | Core module, W/S/L fixtures, CQs 1-20, baseline B0 | core passes CQs; result page written |
| 3 | `spatial`, `physical`, `social`, `memory` modules; three profiles; collision and core-protection tests | profiles install and exchange (CQ 21) |
| 4 | Temporal and multi-agent suites (Exp. 2, 3); resource baseline (Exp. 6) | results published |
| R | ROS 2: Docker environment, simulated warehouse bags with ground truth, adapter, B0, Experiment R | adapter results vs B0 |
| 5 | GUPI parity adapter on a branch in the GUPI repo, existing benchmarks only | parity report |
| 6 | Visual World Explorer (new app), one 20-60 s video, independent annotation | end-to-end demo + evaluation |
| 7 | Generalisation, held-out domains, specification draft | — |

Every phase: preregister, commit and push each validated step, report results including failures.
