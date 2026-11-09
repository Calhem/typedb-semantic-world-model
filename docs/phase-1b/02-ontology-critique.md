# 2. Architectural critique of the proposed upper ontology

This document tests the Phase 1 core ([upper-ontology-proposal.md](../phase-1/upper-ontology-proposal.md)) without
assuming it is right. Labels: **V** verified (source or probe), **I** interpretation, **A** untested assumption.
Probe references: `P1-n` = Phase 1 probe n; `P1B-x` = Phase 1B probe x (`probes/phase_1b_probes.out.json`).

Four running examples are used throughout:
- **W (warehouse):** a robot's tracker sees box *track 17* on shelf 3 at 10:03. The box is occluded at 10:06. A
  person carries it to the dock. *Track 42* appears at the dock at 10:12.
- **S (social):** A tells the robot "B is the new site manager". B later says "I'm only covering this week". A
  sounds annoyed.
- **L (lunar):** a rover's spectrometer X classifies rock R as basalt (0.7); instrument Y says anorthosite (0.6).
  The rover collects a fragment of R as sample 12.
- **M (memory):** in chat, a user says "Sam moved to Berlin in March". Two weeks later: "Sam's back in London".
  There are two people called Sam.

## 2.1 Is a DOLCE-style, descriptive, 3D foundation appropriate?

**Recommendation: yes, with time on relations.** Things (endurants) are wholly present at each moment and change.
Changeable facts are relations with a time index.

- **Evidence.** DOLCE time-indexes parthood, participation, constitution and classification (V, Borgo et al. 2022).
  That is the "fact with valid time" pattern. Our application needs beliefs, hypotheses and simulated worlds, which
  a descriptive ontology admits and a realist one (BFO) does not centre (I). KnowRob, the closest working system,
  uses DUL, the lightweight OWL version of DOLCE (V).
- **Strongest counterargument.** A 4D (perdurantist) model makes video and tracking more natural. A tracked object
  becomes a space-time worm, and "track 17 from 10:03 to 10:06" is literally a temporal part of the box. Identity
  across occlusion becomes "are these two temporal parts of one worm?" rather than a same-as claim. BFO is also an
  ISO standard with large scientific reuse (V, ISO/IEC 21838-2).
- **Why 3D still wins here.** Every application asks about *the box* (one id) and about what agents believe about
  it. 4D multiplies entities per object. Track segments can still be stored as observations (W: *track 17* is an
  observation series, not the box). For L, a mapping to BFO can be published for the scientific modules. Confidence:
  **medium-high**.

## 2.2 Adopt, align, or define a minimal independent core?

| Option | For | Against |
|---|---|---|
| **Adopt DUL/SOMA wholesale** | Mature; robotics-tested; modular (SOMA's 12 modules, V) | ~79 DUL classes before SOMA (V, count); OWL semantics (open world, inference) don't execute in TypeDB; SOMA is LGPL-3.0 (V); Descriptions-and-Situations is heavy; robotics-centred, not chat |
| **Align: minimal core with a published, tested mapping to DUL (and BFO for science)** | Small; terms traceable to standards; reuse is a mapping, not a dependency | The mapping can rot unless tested; risk of "alignment as decoration" |
| **Independent with no alignment** | Fastest | Repeats solved problems; no interoperability; hard to defend in review |

**Recommendation: align.** Define a deliberately minimal core whose every concept names its DUL counterpart
(and SOSA/PROV/OWL-Time where relevant). The mapping is checked by exporting a fixture to RDF and validating it
against DUL's class and property hierarchy. **Strongest counterargument:** KnowRob + SOMA already does robotics
better than we will in v1; we should *use* it there and only add what is missing. That is a real alternative,
and it is included as approach 1 in [03-alternative-architectures.md](03-alternative-architectures.md). Confidence:
**medium**.

## 2.3 Does every changeable fact need to be a claim?

Phase 1 counted about 4-5 concepts per fact (claim, time attributes, evidence relation, observation, attribution).

**Correction (I, from GUPI's verified schema).** In GUPI, `claim` is an abstract *relation*, and every domain fact is
a subtype of it. The fact relation **is** the claim; there is no separate wrapper. So the minimum cost of "a
changeable fact as a claim" is **one relation plus its time attributes**. Evidence and attribution links are extra
and can be optional.

| Example | What is stored | Concepts |
|---|---|---|
| W: box on shelf 3 from 10:03 | `located-at (located: box, place: shelf-3)` with valid-from window | 1 relation + attributes |
| W, with provenance | + `evidence (supported: that relation, support: observation-881)`; observation-881 references the bag message | +2 |
| S: A says B is site manager | `has-role` claim + `attribution (holder: A, attitude: asserts)` + evidence to utterance | 3-4 |
| Vehicle design: the brake disc is part of the corner assembly | static `part-of`, no time | 1 |

**Recommendation.** Every **contingent** fact (one that can change, or that someone could dispute) is a subtype of
the abstract `claim` relation, with valid time. The recording agent is the default attributor, so no attribution
link is needed for the system's own claims. Evidence links are **required by profile** where the competency
questions need provenance, and are otherwise optional. Facts that are true by definition in a world (a design's
part-of hierarchy, a map version's room adjacency) may be **static** relations, declared as such in the module.

**Strongest counterargument.** "Optional provenance" erodes "evidence before assertion": a profile that skips
evidence produces unauditable facts. Mitigation: the competency question "which claims have no evidence?" (CQ 18)
runs in every profile's test suite, and a profile must state its allowed exceptions. Confidence: **high** for
"the relation is the claim"; **medium** for "optional evidence".

## 2.4 Reality, observation, belief and assertion without excessive reification

| Layer | Representation | W example | S example |
|---|---|---|---|
| Observation | entity: a record that a source produced, with a reference to the raw data | detection message in a bag | A's utterance (audio span, transcript) |
| Claim | relation (fact) with valid time | box located-at shelf 3 | B has-role site-manager |
| Attribution | relation: agent + attitude (asserts, believes, doubts, hypothesises) + claim | (implicit: robot) | A asserts; robot believes; B denies |
| Acceptance | review decisions by the system (accepted, rejected, retracted) | accepted automatically by policy | pending review |
| "Reality" | **not represented.** "True" always means *accepted in a perspective and world* | — | — |

**I:** this needs no reification beyond what TypeDB gives natively: relations can play roles in other relations
(P1-2), so attribution and evidence point at the fact relation directly. It costs one relation per extra layer
used, and only when used.

**Counterargument:** users and applications want "what is true", not "what the system accepts". Answer: the
system's perspective *is* the application's best account. What we refuse is a second, privileged "reality" layer
that would hide disagreement. Confidence: **medium-high**.

## 2.5 Are five temporal dimensions necessary?

**No. Three primitive times, each with a time reference system, plus one optional time.** Phase 1's five collapse
as follows:

| Phase 1 time | Phase 1B treatment | Reason |
|---|---|---|
| valid time | **kept** (primitive 1) | when the proposition holds |
| event time | = valid time of the event's occurrence | an event is a claim too (GUPI ADR 0010 already treats it so, V) |
| observation time | **kept** (primitive 2), = SOSA *phenomenon time* | when the observed thing happened (ROS `header.stamp`, video frame time) |
| received / recorded time | **kept** (primitive 3), = transaction time | when this system committed it; never supplied by callers (GUPI ADR 0003, V) |
| belief time | for the system: transaction time of its review decisions. For another agent: the **valid time of the attribution claim** ("A believed X from Monday") | not a separate axis |
| *(new, optional)* result time | when an observation's result became available (SOSA *result time*); ROS processing delay, a lab result returned days later (L) | needed only where latency matters |

**Time reference systems (new).** Every time value names its clock: `wall` (UTC), `sim` (ROS `use_sim_time`),
`media` (seconds into a video whose wall-clock start may be unknown), `sequence` (turn order in a chat with no
timestamps), `mission` (L: mission elapsed time). Comparisons across systems need an explicit, recorded alignment.
Without this, a video's "00:42" or a sim's "t = 12 s" is silently treated as UTC (I).

**Precise semantics (proposed).** Valid time is a half-open interval [start, end). Each bound is a window
[earliest, latest] (GUPI ADR 0003, V). A missing end is UNKNOWN, never "still true". Observation time is an
instant or interval in the observation's clock. Transaction time is assigned by the database writer, is
monotonic per writer, and is never edited.

**Strongest counterargument.** Most robotics and video systems run with one time. Three axes plus reference systems
add attributes to every record and burden every query. Mitigation: transaction time is set by the writer, and
observation time lives on observations, not facts. So a fact carries only valid time. Confidence: **high** for the
collapse; **medium** for reference systems being needed in v1 (no running example has shown the failure yet).

## 2.6 Identity, uncertainty, contradiction and gaps

### Identity
- The system mints a stable id per **referent**. Sensor-local ids (W: `Detection3D.id`, documented as "may be
  empty" and consistent only across one detector's messages, V vision_msgs) are observations that *refer*.
- Linking is a `refers-to` claim (observation → referent) with evidence and a method (tracker continuity,
  appearance match, human review). Merging two referents is a reviewable `same-as` claim (GUPI, V).
- **No transitive auto-merge.** If *track 17* matches the box at 0.8 and *track 42* matches *track 17* at 0.8, the
  system does not conclude *track 42* is the box. It records two claims and asks.
- **M:** two people named Sam are two referents; each mention gets a `refers-to` claim, or competing alternatives
  when ambiguous.
- **L:** sample 12 is a **new endurant** created by the sampling event, constituted from material of rock R
  (DOLCE constitution, V). It is not "rock R relabelled".

### Uncertainty: two different things that Phase 1 blurred
| | Meaning | Where |
|---|---|---|
| **Belief confidence** | how strongly an agent holds a claim | attribute on the claim or attribution |
| **Measurement uncertainty** | spread of a measured value (ROS covariance; L: spectral fit error) | on the measurement |

A pose with 5 cm covariance can be believed with confidence 1.0. Conflating them makes "how sure are we?"
meaningless. **L:** basalt 0.7 and anorthosite 0.6 are **two competing classification claims**, both kept, each
with confidence. So are the `ObjectHypothesisWithPose` results in one detection (V, vision_msgs).

### Contradiction
- **Within one perspective:** accepted claims that cannot both hold → the answer is CONTESTED (GUPI semantics, V).
  **L:** if the rover's science team accepts both classifications, R's class at that time is CONTESTED.
- **Across perspectives:** not a contradiction. **S:** A asserts B is site manager; B asserts she is only covering.
  Both attributions stand. The robot's own acceptance is a separate decision.

### Temporal gaps: the largest semantic problem found
Probe P1B-C (V) implemented "where was the box at t?" in TypeQL with three-valued answers. At 10:15, after the box
was observed at the dock at 10:12 with no end recorded, the correct open-world answer is **UNKNOWN**, not "at the
dock". Under strict no-continuity semantics, **a robot would know almost nothing about the present**, since every
fact ends at its last observation.

Two additions are needed, and Phase 1 had neither:
1. **Persistence policies, declared per module and per kind.** For example: a static object on a shelf persists
   until it is observed to have moved or to be absent, up to N hours. Answers derived this way are labelled
   **PRESUMED** with the policy name (GUPI already returns PRESUMED, V). Persons get short or no persistence.
2. **Observed absence (coverage).** "Looked at shelf 3 at 10:09; the box was not there" is evidence; "did not look
   at shelf 3" is not. Without recording *what was observed* (field of view, scanned region, conversation covered),
   the system cannot tell absence of evidence from evidence of absence. Khronos detects removed objects on revisit
   (V, README), which is exactly this.

**S:** whether A is still annoyed an hour later is UNKNOWN unless a policy says otherwise, and affect should have
no persistence policy. **M:** "Sam's back in London" ends the Berlin claim *for the Sam it refers to*, which needs
identity resolution first.

Confidence: **high** that both are needed; **low** on the right default policies (to be tested in Experiment 2).

## 2.7 Can profiles extend the ontology without changing core semantics?

Verified behaviour: a profile can add roles to core types (P1-10). Once data uses such a role, the profile cannot
be removed without migrating the data (P1B-D, rejected with SVL51). Names share one space (P1-4).

**Operational definition (proposed).** A profile *preserves core semantics* when (a) every core competency question
gives identical answers on the core fixture with and without the profile, and (b) the profile's own data, viewed
only through core types, gives answers a core-only application would accept (substitutability).

**Rules.** Profiles may subtype core types, specialise core roles, and add `plays` **only at declared extension
points** (abstract core roles marked for extension). They may not redefine, undefine or rename core types, attributes
or functions. Removal is a migration, not an uninstall.

**Strongest counterargument:** declared extension points will be wrong in advance, and every miss forces a core
release. That is acceptable: a core release is the honest signal that the core was incomplete, and Experiment 1
counts these releases. Confidence: **medium**.

## 2.8 Consequences of TypeDB's single-type restriction

Verified: one type per instance (P1-3); no in-place re-typing (P1B-B, rejected with INF11; the instance stays a
`box`).

| Situation | Consequence | Rule |
|---|---|---|
| A detector's label as the type (W: `box`) | A later correction ("it's a bin") needs a new instance, breaking identity | **Never type by uncertain labels.** Labels are `classified-as` claims (also DOLCE's own pattern, V) |
| Roles (W: "package" = a thing being delivered; S: "site manager") | Roles change over time | Roles are claims (`has-role`), never types |
| Coarse kind wrong (video: person or mannequin?) | Must mint a new referent, and a supersession links them | Type only at a **robust** level: physical-object, agent, place, information-object |
| Co-located entities (L: sample vs rock material) | Two instances plus constitution | Natural in TypeDB |

**Trade-off.** If everything is typed only at the coarse level, TypeDB's schema checking protects less (any
physical object can play any physical role). That loses part of the advantage Phase 1 claimed. **I:** the gain
is honesty. Kinds that are themselves uncertain must not be enforced by schema.

**Where TypeDB shaped the design rather than semantics.** Relations for roles is driven by semantics; DOLCE does
the same. A measurement as a relation (because attributes cannot own attributes, P1-5) is a TypeDB workaround. A
DOLCE quale would be a value in a quality space. Struct values cannot be inserted in 3.14.1 with any syntax tried
(P1B-A, three forms rejected), so coordinates are separate attributes. Both are implementation details and must
not leak into the specification.

## 2.9 Revised core (for review, still no TypeQL)
Changes from Phase 1: `state-change` dropped (it is an event whose participants include a claim); `world`
retained; added `coverage` (observed region or scope, for observed absence) and `persistence-policy`;
`measurement` kept separate from belief confidence; five times reduced to three plus reference systems. Count:
about 18 types plus attributes, within the Phase 1 cap.
