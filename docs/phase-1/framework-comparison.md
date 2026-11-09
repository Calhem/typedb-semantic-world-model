# Framework comparison

**Basis:** this comparison is written from published knowledge of these frameworks (to mid-2026), not from a fresh
literature search in this session. Licence and version facts marked *(verify)* must be checked against the primary
source before we reuse anything. Nothing was downloaded.

"Upper ontology" means the most general layer of categories (object, event, quality...) that domain ontologies
specialise.

## Foundational (upper) ontologies

| Framework | What it gives us | Limitations for us | Licence | Verdict |
|---|---|---|---|---|
| **DOLCE / DOLCE+DnS Ultralite (DUL)** | Descriptive ("how people and agents carve up the world") categories: endurant / perdurant (things vs happenings), qualities and quality regions, roles and situations via Descriptions and Situations (DnS). Basis of SOMA and of many robotics ontologies | DnS is heavy (description, situation, concept, role as separate reified things). Relies on multiple classification, which TypeDB lacks | DUL OWL: CC BY *(verify)* | **Primary source of core distinctions.** Adopt the endurant / perdurant / quality / role distinctions; do not adopt DnS wholesale |
| **BFO** (ISO/IEC 21838-2:2021) | Realist categories (continuant / occurrent, specifically dependent continuants, roles, dispositions). Dominant in biomedical and scientific ontologies (OBO Foundry, CCO) | Realism: "only what really exists". It has no native place for beliefs, hypotheses or fictional and simulated worlds, which we need | CC BY 4.0 *(verify)* | **Align to, don't build on.** Map our core to BFO for the scientific / lunar domain, so OBO-style ontologies can be reused there |
| **SUMO** | Very large, with formal axioms (SUO-KIF) and mappings to WordNet | Size (tens of thousands of terms), first-order axioms that TypeDB cannot run, uneven quality across domains | Free; IEEE-owned, GPL tooling *(verify)* | **Reference only** for vocabulary checks |
| **Cyc / OpenCyc** | 40 years of common-sense knowledge with microtheories (contexts in which assertions hold) | Proprietary; OpenCyc withdrawn (2017). Shows how far a universal ontology is from done after decades | Proprietary | **A cautionary precedent**, and the idea of microtheories for perspectives |

**Conflicts to examine before combining:**
- **Realist vs descriptive.** BFO models what exists; DOLCE models how a cognitive agent categorises. A world model
  that keeps agent perspectives and hypotheses is descriptive by nature. Choosing DOLCE-style means BFO alignment is
  a mapping with known losses (qualities, roles, information entities differ), not an import.
- **3D vs 4D identity.** Both DOLCE and BFO are "3D": an object exists wholly at each time and changes. 4D
  (perdurantist) models make objects into time-slices. Mixing them breaks identity questions. **Recommend 3D**, with
  time on the *facts* (claims), which matches TypeDB relations and GUPI.
- **Qualities.** DOLCE separates a quality (this cup's colour) from its value region (a colour space); BFO and SOSA
  treat properties differently again. Pick one pattern for measured values and map the others.
- **Time.** OWL-Time intervals, PROV instants and SOSA's phenomenon vs result time overlap but don't align one to one.

## Domain frameworks

| Framework | What it gives us | Limitations | Licence | Verdict |
|---|---|---|---|---|
| **SOSA/SSN** (W3C/OGC 2017) | Observation, sensor, observable property, feature of interest, result, phenomenon time vs result time | Sensor metadata focus; little on identity across observations | W3C document licence *(verify)* | **Adopt the observation pattern** (observation as an n-ary relation is natural in TypeDB) |
| **OWL-Time** | Instants, intervals, Allen relations, temporal reference systems | Intervals with uncertain bounds are awkward | W3C | **Adopt Allen relations as functions**; use GUPI's uncertain-bound windows for intervals |
| **GeoSPARQL 1.1** (OGC) | Feature / geometry split, topological relations (RCC8, DE-9IM), WKT geometries | Needs a spatial engine; TypeDB has no geometry type | OGC | **Adopt the feature / geometry split** and topological relation names; geometry stays outside TypeDB |
| **PROV-O** (W3C 2013) | Entity, activity, agent, derivation, attribution | Generic; not epistemic (no belief, no dispute) | W3C | **Adopt** for provenance; GUPI's claim / evidence / review covers what PROV lacks |
| **IEEE 1872-2015 CORA** (+ 1872.2-2021 autonomous robotics) | Robot, robotic system, environment, positioning, built on SUMO | SUMO-based; little adoption in running systems | IEEE standard (paid) | **Map key terms**; don't depend on it |
| **SOMA** (EASE, Bremen) | Everyday activities, affordances, dispositions, roles, built on DUL; used by KnowRob | Large; OWL-based; DnS-heavy | *(verify)* | **Closest existing match to our ambition.** Study it first; reuse its affordance and action concepts |
| **EmotionML** (W3C 2014) | Markup for emotion annotations with vocabularies | An annotation format, not an ontology of emotion | W3C | **Use for import/export** of affect annotations, always as attributed claims |

## Cognitive and agent architectures

| Work | Relevance | Lesson |
|---|---|---|
| **SOAR, ACT-R** | Working vs long-term memory, procedural vs declarative | A persistent semantic store is the *declarative long-term* part only; control and attention live elsewhere |
| **OpenCog / Hyperon (AtomSpace)** | A typed hypergraph knowledge store for AGI | **Strong overlap with "typed hypergraph world model".** Shows that the store is not the hard part; populating and using it is |
| **BDI architectures** | Belief, desire, intention as first-class | Model beliefs as attributed claims (GUPI already does) |
| **Agent memory systems** (MemGPT/Letta, Zep/Graphiti, Mem0, GUPI) | Temporal knowledge graphs for LLM agents | Graphiti is bitemporal and graph-based; GUPI found text retrieval hard to beat on chat |

## Spatial and visual world representations

| Work | Relevance | Lesson |
|---|---|---|
| **3D scene graphs** (Kimera, Hydra, Khronos; ConceptGraphs) | Hierarchical, real-time object / place / room graphs from robot sensors; Khronos adds time | **Substantial overlap with the ROS 2 and VWE goals.** They run in memory, fast, with geometry; persistence, provenance and cross-application semantics are what they lack |
| **KnowRob + NEEMs** (narrative-enabled episodic memories) | Robot episodic memory over SOMA, with logged experiences and queries | **The most direct prior art** for "robot builds a persistent semantic memory of what happened" |
| **Semantic SLAM** | Object-level maps | Geometry and identity tracking belong to SLAM, not to us |
| **OpenUSD** | Scene description with layers, variants, prims and schemas; strong in VFX and simulation | Its layer and variant composition is a mature answer to "profiles"; link to USD prims by path, don't copy geometry |
| **Learned "world models"** (video prediction models, JEPA-style) | Same name, different meaning: predictive neural models | **Naming risk.** Say "semantic world model" everywhere |

## What already overlaps our ambition
1. **KnowRob / SOMA / NEEMs:** an upper ontology (DUL), an everyday-activity and robotics ontology, and persistent
   episodic memory of robot experiences, queried logically. This covers much of Goals 1-3 for robotics.
2. **3D scene graphs (Hydra, Khronos):** perceptual world representations with persistent identities.
3. **Cyc, SUMO, BFO:** universal or upper ontologies. Decades of work, none universal in practice.
4. **Bitemporal knowledge graphs for agents (Graphiti, GUPI).**

So the novel part is **not** an upper ontology, a scene graph or agent memory. If there is something new, it is
narrower: *one small, typed, evidence-aware core, executed in a typed hypergraph database, shared by a robot, a video
pipeline and an agent memory, with measured costs.* That claim is testable and modest; the larger one is not.
