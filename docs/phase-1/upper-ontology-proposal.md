# Design principles and upper ontology proposal

**Status: proposal for review. No TypeQL is written.** Type names are working names.

## Design principles (refining the brief's twelve)
1. **Types for what a thing is; relations for everything that can change or be disputed.** A thing's kind (object,
   agent, event) is a type. Its role, location, classification by a detector, membership, state and emotion are
   claims. Forced by TypeDB (no multiple classification, probe 3), and it is what "evidence before assertion" needs.
2. **Every contingent fact is a claim with provenance and time,** unless a profile declares a fact *static*
   (a vehicle's part-of hierarchy in the explorer). The cost is measured in Experiment 6.
3. **No privileged "reality".** The system's own account is one perspective (the system as an agent). Layers 3 and 4
   of the brief become one mechanism: claims attributed to an agent.
4. **Absence is not falsity.** Open-world answers (TRUE, FALSE, UNKNOWN, NOT_YET_KNOWN, CONTESTED), from GUPI ADR 0003.
5. **Geometry, pixels and raw signals stay outside.** The model holds references (a ROS frame, a USD prim path, a
   video time range, a bag message), coarse values and derived facts.
6. **A core concept enters only when two of the three reference applications need it,** with competency questions
   that fail without it.
7. **Core size cap:** about 25 types (entities + relations) and 25 attributes in v1. Exceeding it needs a recorded
   decision.
8. **Reuse names and definitions** from SOSA, PROV, OWL-Time, GeoSPARQL and DUL where they fit, with a mapping table.

## Proposed core (about 20 types)

Plain-English definitions; the "from" column says where the concept is borrowed.

### Things that endure (entities)
| Concept | Definition | From |
|---|---|---|
| `endurant` (abstract) | Something that exists as a whole at each moment it exists and can change | DOLCE |
| `physical-object` | A bounded material thing: a box, a rock, a robot's body | DOLCE |
| `agent` | Something that can act and hold beliefs: a person, a robot, a software agent, an organisation | PROV, DUL |
| `place` | A region used as a location: a room, a shelf, a crater. Geometry is referenced, not stored | GeoSPARQL feature |
| `information-object` | Content: a message, a video, a map, a document | DUL |
| `quantity-kind` (attribute set) | Measured values with unit and optional uncertainty, as a `measurement` relation | SOSA result, QUDT units |

**Not core in v1:** substance, system, capability, process-as-entity. *System* is a part-of whole with a function
(a profile can add it). *Substance* (sand, water) is deferred to the physical profile.

### Things that happen (relations, because they have participants)
| Concept | Definition | From |
|---|---|---|
| `event` (abstract) | Something that happens over a time span, with participants in roles. Profiles specialise it (`pickup`, `utterance`, `drive`) | DOLCE perdurant, SOMA action |
| `participation` (roles of `event`) | Who or what took part, and how: agent, patient, instrument, location | DUL, SOMA |
| `state-change` | An event whose point is that a claim begins or ends to hold | OWL-Time + GUPI events |

### Facts and their support (the epistemic layer, from GUPI)
| Concept | Definition | From |
|---|---|---|
| `claim` (abstract relation) | One attestation that a proposition holds over a valid-time interval. All contingent facts are claim subtypes: `located-at`, `part-of`, `classified-as`, `has-state`, `has-role`, `same-as` | GUPI ADR 0001 |
| `observation` | A record produced by a sensor, a person or a model at an observation time, with a source and a raw reference (bag message, video frame range, chat turn) | SOSA, GUPI |
| `evidence` | Links a claim to the observations or claims supporting it, with method and confidence | GUPI, PROV derivation |
| `attribution` | An agent holds a claim, with an attitude: asserts, believes, doubts, hypothesises, simulates | BDI, GUPI |
| `review` | A decision (accept, reject, retract) about a claim, recorded at a time | GUPI |
| `supersession` | A claim replaces another (a correction) | GUPI |
| `world` | A context in which claims hold: actual, hypothetical, simulated, a plan. Claims belong to exactly one world | Cyc microtheory, OpenUSD layer |

### The five times (answering the brief's "Time" problem)
| Time | Where | Meaning |
|---|---|---|
| valid time | claim, with uncertain bounds | when the proposition holds |
| event time | event | when it happened |
| observation time | observation | when the sensor or source captured it (ROS `header.stamp`, video timestamp) |
| received / recorded time | observation, claim, review | when the system ingested and committed it (transaction time) |
| belief time | attribution, review | when an agent came to hold or drop it (recorded time of the attribution) |

**Gaps without invented continuity:** a claim's end is unknown unless stated or observed. "Last seen at" is a
derived question, never a stored end. A profile may define a *presumption* (an object on a shelf stays there for up
to N minutes), and answers say PRESUMED, as in GUPI.

### Identity
- Every endurant is a **referent** with a stable id that the system mints. Sensor-local ids (a tracker's track id, a
  face cluster id, a chat name) are observations that *refer*; linking them to a referent is a `same-as` / `refers-to`
  claim with evidence, reviewable and reversible.
- Identity persists through change because change is in claims, not in the referent.
- Different representations of one thing (a USD prim, a ROS frame, a database record) link to the referent through
  `represented-by` with the external system and key.

### What this deliberately leaves out of v1
Emotion, goals and intentions as core types: they are claims with an attitude, defined in the social profile,
always attributed. Causality: a `causes` claim distinct from temporal order, but only in a profile, with explicit
evidence, and never inferred from succession. Capabilities and affordances: a profile relation between an agent or
object type and an event type, with conditions as text in v1.

## Cost of this design (to measure, not to assume)
A single "box is on shelf 3 since 10:02" becomes: a `located-at` claim, its valid-time attributes, an evidence
relation to an observation, and an attribution. About 4-5 concepts instead of 1 edge. Probe 12 ingested such
5-concept records at 1,200-1,600 per second on a laptop, so this is affordable for semantic events, not for
per-frame data. Experiment 6 measures it against a plain state table.
