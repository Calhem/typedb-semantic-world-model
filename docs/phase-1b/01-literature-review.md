# 1. Literature and prior-art review (verified)

**Date:** 2026-11-09. This replaces nothing in Phase 1; it checks it. Changes to Phase 1 findings are listed in
[changes-to-phase-1.md](changes-to-phase-1.md).

**Evidence labels** used in every table:
- **V** verified this phase in a primary source: the paper itself, the project's own repository (README, source
  file, licence file, read through GitHub's API or raw files on 2026-11-09), or a standard's own text.
- **I** my interpretation of verified material.
- **A** an assumption not checked in a primary source this phase.

**Method and limits.** I read the DOLCE paper (Borgo et al. 2022) and the KnowRob 2.0 paper (Beetz et al. 2018) in
full text. For the rest I read the projects' repositories and abstracts. I did **not** read full papers for SOMA,
Hydra, Khronos, ConceptGraphs or Zep, did not run any of these systems, and did not read paywalled standards
(IEEE 1872, ISO/IEC 21838 text). "Implements" below means *present in released code or files*, not *claimed in a
paper*.

## 1.1 Foundational ontologies

### DOLCE
Sources: S. Borgo, R. Ferrario, A. Gangemi, N. Guarino, C. Masolo, D. Porello, E. M. Sanfilippo, L. Vieu, "DOLCE: A
descriptive ontology for linguistic and cognitive engineering", *Applied Ontology* 17(1):45-69, 2022,
[doi:10.3233/AO-210259](https://doi.org/10.3233/AO-210259), preprint [arXiv:2308.01597](https://arxiv.org/abs/2308.01597);
files: [github.com/appliedontolab/DOLCE](https://github.com/appliedontolab/DOLCE).

| Question | Finding | |
|---|---|---|
| What it implements | A first-order axiomatisation in quantified modal logic QS5 (possibilist: quantifies over all *possible* entities); OWL files that are approximations of it | V |
| Identity and change | Endurants are wholly present at each time and can change; perdurants unfold over time | V |
| Time | Parthood between endurants, participation `PC(x, y, t)`, constitution and classification `CF(x, y, t)` are **time-indexed relations** | V |
| Roles and classification | Roles are anti-rigid concepts linked to things by the time-indexed **classification relation**, not by typing the thing | V |
| Qualities | An individual quality (this rose's colour) has a position (*quale*) in a quality space; values change over time | V |
| Co-location | Constitution distinguishes co-located things (a statue and its clay) | V |
| Evidence, uncertainty, perspectives | Not addressed by the core; DOLCE models a commonsense view, not who believes what | V (absence in the paper's scope) |
| Licence | CC BY 4.0 (repository licence) | V |
| Practical limitation | Full theory is not computable in OWL; the OWL version approximates it | V |

**I:** DOLCE already handles roles and changing classification as *time-indexed relations*. That is exactly what
TypeDB forces on us (one type per instance). So the conflict Phase 1 described between DOLCE and TypeDB's single
type is much smaller than stated. TypeDB's limitation matches DOLCE's own pattern.

### BFO
Sources: ISO/IEC 21838-2:2021; [github.com/BFO-ontology/BFO-2020](https://github.com/BFO-ontology/BFO-2020).

| Question | Finding | |
|---|---|---|
| What it implements | OWL and Common Logic files for BFO 2020, including a "temporalized relations" variant and a variant without them | V (repository, NCOR wiki) |
| Licence | CC BY 4.0 (README) | V |
| Time and change | Continuants vs occurrents; temporally qualified relations ("at all times", "at some time") | V (files named; semantics A) |
| Evidence, beliefs, hypotheses | No native treatment; BFO is realist | I (from its stated realism; not re-read this phase) |
| Use | Standard top level for OBO Foundry and Common Core Ontologies | A |

### SUMO
Source: [github.com/ontologyportal/sumo](https://github.com/ontologyportal/sumo).

| Question | Finding | |
|---|---|---|
| What it implements | SUO-KIF files (Merge.kif, Mid-level-ontology.kif and dozens of domain files from Anatomy to Military), WordNet mappings, tooling (SigmaKEE) | V |
| Licence | Repository README: GNU GPL with an attribution request ("provide credit in any writings... or other representations of any software which incorporates, builds on, or uses this code"). The website describes SUMO as free and owned by the IEEE | V |
| Limitation | Size and full first-order axioms; GPL plus attribution requirement complicates reuse in an Apache-licensed specification | V (licence) / I (consequence) |

### Cyc
Sources: secondary only ([Wikipedia](https://en.wikipedia.org/wiki/Cyc); M. K. Bergman,
[OpenCyc withdrawal, 2017](https://www.mkbergman.com/?p=2034)).

| Finding | |
|---|---|
| Proprietary knowledge base organised into **microtheories** (contexts; each must be free of monotonic contradictions) | A (secondary sources) |
| OpenCyc withdrawn around March 2017 | A (secondary sources agree) |

**I:** Microtheories remain the clearest precedent for our `world` / perspective contexts. Cyc is not reusable.

## 1.2 Robotics knowledge systems

### KnowRob (1, 2.0 and the current C++ version)
Sources: M. Beetz, D. Beßler, A. Haidu, M. Pomarlan, A. K. Bozcuoğlu, G. Bartels, "KnowRob 2.0 — A 2nd generation
knowledge processing framework for cognition-enabled robotic agents", ICRA 2018
([PDF](https://ai.uni-bremen.de/papers/beetz18knowrob.pdf)); [github.com/knowrob/knowrob](https://github.com/knowrob/knowrob)
(`dev` is the default branch; `master` is the ROS 1 Noetic Prolog version).

| Question | Finding | |
|---|---|---|
| Architecture (2.0 paper) | A knowledge base that "appears to be a conventional first-order time interval logic knowledge base, but it exists to a large part only virtually": facts are computed on demand from control-program data structures, robotics algorithms and logged data | V |
| Architecture (current `dev`) | A C++ shared library: a **hybrid** knowledge base whose query planner splits a query across reasoners and storage backends (plugins in C++ or Python); Prolog still used for rules. Dependencies: Redland/Raptor (RDF), SWI-Prolog, MongoDB, Boost, Eigen. ROS integration in a separate repository | V (README) |
| Belief, perspective, uncertainty | A modal query language with operators **KNOWLEDGE, BELIEF, ALWAYS, SOMETIMES**, an `agent` (perspective) parameter and a `confidence` parameter (`ModalOperator.h`) | V (source) |
| Time | Fuzzy time intervals whose start and end lie within ranges (`TimeInterval.h`); `holds(pose(r, ...), t)` for changing state | V |
| Episodic memory | NEEMs: experience (low-level data) linked to a narrative, stored in MongoDB, shared via openEASE | V (paper, NEEM handbook) |
| Ontology | SOMA on DUL, in RDF/OWL | V |
| Licence | BSD-3-Clause | V |
| Practical limitations | Large dependency stack; ROS 1 heritage; the ROS 2 integration repository's status was not checked | V (deps) / A (ROS 2 maturity) |

**I: KnowRob is the closest prior art, closer than Phase 1 said.** It already has agent perspective, belief vs
knowledge, confidence, uncertain time intervals and robot episodic memory, over a DUL-based ontology. What it does
*not* emphasise (I, from the material read): per-fact provenance to source observations, review and correction
history (transaction time), and use outside robotics (agent memory, video).

### SOMA
Sources: D. Beßler, R. Porzel, M. Pomarlan, A. Vyas, S. Höffner, M. Beetz, R. Malaka, J. Bateman, "Foundations of
the Socio-physical Model of Activities (SOMA) for autonomous robotic agents", FOIS 2021,
[arXiv:2011.11972](https://arxiv.org/abs/2011.11972); [github.com/ease-crc/soma](https://github.com/ease-crc/soma).

| Question | Finding | |
|---|---|---|
| What it implements | OWL modules over DUL: SOMA, SOMA-ACT, -AGENT, -Allen, -HOME, -IO, -NEEM, -OBJ, -PROC, -SAY, -STATE, -WF, and a **USD ontology** for translating OpenUSD scene descriptions into a knowledge graph | V (file list; USD.owl comment) |
| Size | DUL.owl declares ~79 classes, SOMA.owl ~30, SOMA-STATE ~25, USD ~34 (my count of class declarations; modules import each other). An EASE tutorial cites 563 classes, 352 properties for the whole | V (count) / A (tutorial figure) |
| Modularity | Already split into modules that applications import selectively, which is what our "profiles" propose | V (files) / I |
| Licence | LGPL-3.0 | V |

### IEEE CORA (1872-2015) and 1872.2-2021
Not read (paywalled). Its SUMO basis and scope are **A**. Recommendation unchanged: map a few terms, don't depend on it.

## 1.3 Typed hypergraph knowledge stores

### OpenCog AtomSpace and Hyperon
Sources: [github.com/opencog/atomspace](https://github.com/opencog/atomspace),
[github.com/trueagi-io/hyperon-experimental](https://github.com/trueagi-io/hyperon-experimental).

| Finding | |
|---|---|
| AtomSpace: "the OpenCog (hyper-)graph database and graph rewriting system"; active (last push 2026-02); licence not a single SPDX identifier (GitHub reports NOASSERTION) | V |
| Hyperon: MeTTa language implementation, MIT licence, active | V |
| Truth values (strength, confidence) on atoms | A (not checked this phase) |

**I:** AtomSpace is prior art for "typed hypergraph store", not for a world ontology. It shows the store is not
the hard part.

## 1.4 Dynamic and 3D scene graphs

| System | Verified facts | |
|---|---|---|
| **Hydra** (N. Hughes, Y. Chang, L. Carlone, RSS 2022, [arXiv:2201.13360](https://arxiv.org/abs/2201.13360); [repo](https://github.com/MIT-SPARK/Hydra)) | Real-time layered 3D scene graph from sensor data; **ROS 2 Jazzy is now the default** (ROS 1 archived 07/2025); BSD-2-Clause | V |
| **Khronos** (L. Schmid, M. Abate, Y. Chang, L. Carlone, RSS 2024, [arXiv:2402.13817](https://arxiv.org/abs/2402.13817); [repo](https://github.com/MIT-SPARK/Khronos)) | Spatio-temporal metric-semantic SLAM: short-term dynamics (people, carts) plus **long-term change detection** (a chair removed, a cooler placed and later removed, detected on revisits); "representing the scene state at all times"; ROS 2 release 10/2025, marked unstable; BSD-3-Clause | V |
| **ConceptGraphs** ([repo](https://github.com/concept-graphs/concept-graphs)) | Open-vocabulary 3D scene graphs; MIT licence | V (repo); method A |

**I:** Khronos already answers "what changed in this scene and when" from perception, with geometry. Our layer
should *consume* such outputs (objects, change events, presence intervals) rather than compete with them. The gap
these systems leave (I): persistence beyond a mapping session, provenance per fact, multiple agents' beliefs,
and exchange with non-robotic applications.

## 1.5 Agent memory
| System | Verified facts | |
|---|---|---|
| **Graphiti / Zep** (P. Rasmussen et al., [arXiv:2501.13956](https://arxiv.org/abs/2501.13956); [repo](https://github.com/getzep/graphiti)) | "Explicit bi-temporal tracking with automatic fact invalidation"; facts invalidated, not deleted; backends Neo4j, FalkorDB, Amazon Neptune (Kuzu deprecated); Apache-2.0; very active | V (README) |
| **GUPI** ([repo](https://github.com/Calhem/typedb-gupi-agent-memory)) | Bitemporal claims, evidence spans, review; research paused; findings in section 5 | V |

**I:** Bitemporal agent memory is already a product category. GUPI's distinguishing features are review,
disputes, allegations and three-valued answers, not bitemporality.

## 1.6 RDF/OWL and other implementation alternatives
| Option | Verified state | Relevance |
|---|---|---|
| **RDF 1.2** (triple terms: a triple as the object of another, for statements about statements) | W3C Candidate Recommendation Snapshot 2026-04-07 ([spec](https://www.w3.org/TR/rdf12-concepts/)); I did not confirm whether it has since become a Recommendation | V (CR) / A (current) | Reduces the reification cost that Phase 1 used as a TypeDB advantage |
| **Oxigraph** (SPARQL store) | Apache-2.0, active ([repo](https://github.com/oxigraph/oxigraph)); embeddable as a library | V (licence, activity) / A (embedding) | Candidate strong baseline B; small footprint |
| **PostgreSQL 18 temporal constraints** | `PRIMARY KEY (id, valid_at WITHOUT OVERLAPS)` and `FOREIGN KEY (..., PERIOD valid_at)` ([feature matrix](https://www.postgresql.org/about/featurematrix/detail/temporal-constraints)) | V (feature matrix, test output) | Candidate strong baseline B for valid time |
| **SOSA/SSN, PROV-O, OWL-Time, GeoSPARQL** | Not re-read this phase | A | Unchanged from Phase 1 |
| **OpenUSD** | Licence reported as NOASSERTION by GitHub (Pixar's modified Apache licence) | V (GitHub) / A (terms) | SOMA already has a USD ontology module |

## 1.7 Genuine research gaps (interpretation)
After checking, these are the gaps I can still defend. Each is **I** until an experiment shows it.
1. **Cross-application sharing.** I found no system shared by a robot, a video pipeline and a conversational agent
   memory through one core with measured information loss. KnowRob/SOMA is robotics-centred; Graphiti is
   chat-centred; scene graphs are perception-centred.
2. **Governed evidence over perception.** Per-fact provenance down to the sensor message, reviewable identity and
   corrections with transaction time, for robot and video facts. KnowRob has belief and confidence, but not (in
   what I read) review and supersession history.
3. **Open-world, three-valued historical answers over sensor data** that never invent continuity, compared against
   the persistence assumptions robots normally make.
4. **Measured cost** of such a semantic layer next to a robot stack (no figures found in the material read).
5. **A typed-hypergraph implementation** of these, compared fairly with RDF 1.2 and relational temporal baselines.
   This is a database question, and it is not the main research question.

**What is not a gap:** an upper ontology (DOLCE, BFO), modular robot ontologies (SOMA), robot belief and episodic
memory (KnowRob), dynamic scene graphs (Hydra, Khronos), and bitemporal agent memory (Graphiti, GUPI).
