# 2. Detailed semantic review

This sets out precise semantics for the four open areas: persistence, observed absence, time and identity, and
confidence. Each part has definitions, rules, counterexamples (**CE**) that break naive approaches, and development
competency questions (**DQ**). It closes with a comparison against KnowRob's implemented semantics.

Notation is plain. *t* is a valid time, *τ* a transaction time, *p* a perspective (an agent), *w* a world
(actual, simulated, hypothetical), *π* a persistence policy. Evidence labels: **V** verified (source or run), **I**
interpretation, **A** assumption.

## 2.1 Time and clock domains

### Clock domains
Every time value is a pair **(clock, value)**. The clocks used in v1:

| Clock | Meaning | Examples |
|---|---|---|
| `wall` | UTC wall-clock time | dated chat sessions; real robot logs |
| `sim` | simulator time | ROS `use_sim_time`, Gazebo `/clock` |
| `media:<video>` | seconds from the start of one video | VWE frames |
| `seq:<conversation>` | position in a conversation with no timestamps | undated chat turns |
| `mission:<id>` | mission elapsed time | L |

Values from different clocks are **incomparable** unless an **alignment** record links them. An alignment holds
`(from clock, to clock, offset, scale, uncertainty, valid range, evidence)`. A query across clocks without an
alignment answers UNKNOWN, never a guess.

**CE-T1.** A video starts at `media` 0. A claim says "the person picked up the box at 00:42". Without an alignment,
"was the box picked up before the robot arrived at 10:05 UTC?" is UNKNOWN. A system that treats 00:42 as 00:00:42
UTC answers FALSE, wrongly.

### The three time dimensions
1. **Valid time** of a claim *φ*: the interval [*s*, *e*) on which *φ* holds, according to that claim. Each bound
   is a window: *s* ∈ [*s⁻*, *s⁺*], *e* ∈ [*e⁻*, *e⁺*]. A missing *e⁻* means the end is **not known to be later
   than the start of evidence**, and a missing *e⁺* means it is unbounded above. **A missing end never means "still
   true".**
   - *φ* certainly holds at *t* iff *s⁺* ≤ *t* < *e⁻*.
   - *φ* certainly does not hold at *t* iff *t* < *s⁻* or *e⁺* ≤ *t*.
   - Otherwise its truth at *t* is undetermined **by this claim**.
2. **Observation time** of an observation *o*: the phenomenon interval [*o_s*, *o_e*] in *o*'s clock (ROS
   `header.stamp`; a video frame span; a chat turn's date). Optional **result time**: when the result became
   available.
3. **Transaction time** *τ(x)*: assigned by the writer when record *x* is committed. It is monotonic per writer,
   never supplied by callers and never edited. The **knowledge state at τ** is every record with *τ(x)* ≤ *τ*,
   plus the decisions in force at *τ*.

Event time is the valid time of an occurrence claim. Belief time is the valid time of an attribution (another
agent's belief) or the transaction time of the system's own decisions.

### Spatial frame corrections
REP 105: poses in `map` can jump when localisation corrects (V). Rules:
- An observation stores its pose **in the sensor frame** plus the id of the transform estimate used (`tf` chain
  and localisation estimate version *E_k*).
- A map-frame pose or a symbolic location ("on shelf 3") is a **derived claim** citing *E_k*.
- When *E_k* is replaced (relocalisation, loop closure), derived claims citing it are **re-derived**. Changed
  results supersede the old ones at a new *τ*. Their **valid time does not change**: the box was always where it
  was; our account of it is what changed.
- Places belong to a **map version**. A new map version needs a place-correspondence record, or old places become
  incomparable.

**CE-F1.** At 10:03 the robot places the box on shelf 3 (map estimate *E_1*). At 10:20 a loop closure shifts the map
by 0.6 m, and the box was actually on shelf 4. "Where was the box at 10:03?" asked at τ = 10:10 gives shelf 3
(believed then). Asked at τ = 10:25 it gives shelf 4. "What did we believe at 10:10 about 10:03?" still gives shelf
3. A store that overwrites poses loses the second answer; a store that never re-derives keeps a wrong first answer.

## 2.2 Answer statuses
An answer to "does *φ* hold at *t*, in perspective *p* and world *w*, as known at *τ*, under policies *Π*?" is one of:

| Status | Meaning | Basis cited |
|---|---|---|
| **OBSERVED** (true / false) | an accepted observation-backed claim covers *t* directly: positive detection, or **evidence of absence** (2.4) | the observations |
| **ASSERTED** (true / false) | an accepted claim from testimony or a document states an interval covering *t* | the source and its claim |
| **INFERRED** (true / false) | derived by a declared rule from OBSERVED or ASSERTED claims | the rule and its inputs |
| **PRESUMED** (true / false) | only a persistence policy carries an earlier supported state to *t* | the policy (id, version) and the supported claim it extends |
| **DISPUTED** | incompatible answers of equal standing at *t* (see ordering below) | all of them |
| **UNKNOWN** | records exist about *φ* by *τ*, but none determine *t* | — |
| **NOT_YET_KNOWN** | nothing about *φ* recorded by *τ* | — |

OBSERVED, ASSERTED and INFERRED together are **supported**. **Standing order:** supported > presumed. A presumption
never disputes a supported answer; it yields. DISPUTED arises only between answers of the same standing:
supported vs supported, or presumed vs presumed. This answers the requirement that historical queries separate
supported truth from presumed continuity: every answer carries its status, and a client can ask "supported only".

## 2.3 Persistence and continuity

### Persistence policy
A policy *π* is a named, versioned, **defeasible** rule:

| Field | Meaning | W example |
|---|---|---|
| scope | claim type + participant kinds + world + profile | `located-at`, object kind *static-object*, world actual, `wop-robotics-1` |
| anchor | which support starts it: the **last positive support** of an accepted claim | last detection on the shelf |
| horizon | maximum duration *d* (finite, or ∞ by explicit choice) | 8 h |
| defeaters | what ends it early: incompatible supported claims; evidence of absence; named events | box seen elsewhere; shelf scanned and empty; "shelf cleared" event |
| renewal | what extends it | a new positive detection |

**No policy, no presumption.** There is no global default. Kinds without a policy answer UNKNOWN between
observations. Affect, intentions and people's locations get no policy in v1, or very short horizons.

### Lifecycle (precise)
Let *u* be the time of the last positive support of claim *φ* known at *τ* (the latest *o_e* of its supporting
observations, or *e⁻* for an asserted interval).
- **Begins** at *u*. PRESUMED covers (*u*, *u* + *d*).
- **Renewed** when a new positive support at *u′* > *u* arrives: the anchor moves to *u′*.
- **Expires** at *u* + *d*. After that the status is UNKNOWN.
- **Superseded (defeated)** at the **earliest certain start** *s⁻* of a defeater's support. Between *s⁻* and the
  defeater's *s⁺*, the status is UNKNOWN. From *s⁺* onwards the defeater's own status applies.
- **Disputed** when a defeater is of insufficient standing to defeat: a negative observation below the policy's
  reliability threshold (2.4), or a second presumption of an incompatible value (two stale sightings in different
  places). Status DISPUTED, both cited.
- **Not stored.** Presumptions are computed at query time from the knowledge state at *τ*. They are never written
  as claims. So evidence arriving later changes historical presumptions *as seen from a later τ*, and the earlier
  view stays reproducible.

**CE-P1 (stale certainty).** Box seen on shelf 3 at 10:03, policy 8 h, no later data. At 10:15: PRESUMED shelf-3.
Event-log baseline A answers "shelf-3" with no status. PostgreSQL with an open range `[10:03,)` answers shelf 3 as
plain truth (V, smoke test: an open range returned *dock* at 10:15). Both conflate presumption with observation.

**CE-P2 (late defeater).** At 10:40 the system learns, from a person's report recorded at τ = 10:40, that the box
was taken to the dock at 10:06. Asked at τ = 10:30, "where at 10:10?" gives PRESUMED shelf-3. Asked at τ = 10:45, it
gives ASSERTED dock. Both are correct for their τ.

**CE-P3 (two stale sightings).** Robot R1 saw the box on shelf 3 at 10:03; robot R2 saw a box it matched to the
same referent at the dock at 10:05. With the same policy, at 10:10 both presumptions run and are incompatible.
Since the dock sighting is later, a **recency** tie-break is tempting. It is not sound: R2's identity match may be
wrong. The answer is DISPUTED with both cited, unless a policy explicitly declares recency precedence.

**CE-P4 (presumption against people).** S: B said at 09:00 "I'm in the office today". A policy for people's
locations with an 8 h horizon would answer PRESUMED office at 16:00, after B has gone home. That is why
person-location policies are short or absent.

## 2.4 Observed absence

### Coverage
A **coverage** record states what an observer could have detected:
`(observer, sensor or reader, scope, interval, target kinds, detection model, reliability, conditions)`.
- **Scope:** a region in a frame (W: the shelf 3 volume), a set of entities ("the people in room 2"), or a text
  scope (M: "sessions 4-9 read in full").
- **Target kinds:** what the detector can detect at all. A person detector covers no boxes.
- **Reliability *ρ*:** the probability of detecting a target of that kind in scope under the stated conditions.
  It is **only usable as a probability with a calibration record** (2.6). Otherwise it is an ordinal grade
  (`high`, `medium`, `low`) set by policy.
- **Conditions:** occlusion, lighting, range, speed; anything that lowers *ρ*.

### Negative observation and evidence of absence
A negative observation of target *x* (or kind *k*) in region *R* at *t* exists when coverage includes *R* at *t* for
kind *k*, and no detection matched *x* (or *k*). It is **evidence of absence** only when *ρ* meets the profile's
threshold for that kind and those conditions. Otherwise it is a weak negative: it **disputes** a presumption but
cannot defeat it.

**Failure to observe** means *R* was not in coverage at *t*. It is **no evidence** either way.

### Interaction of positive and negative observations
| Case | Result |
|---|---|
| Positive at *t₁*, evidence of absence at *t₂* > *t₁* | OBSERVED true at *t₁*; OBSERVED false at *t₂*; between them, PRESUMED true (if a policy applies) until the defeater, then UNKNOWN; **where *x* went is not implied** |
| Positive and evidence of absence for the same *x*, *R* and overlapping time, from different observers | DISPUTED (both supported), unless a policy orders the observers' reliability |
| Positive at *t₁*, weak negative at *t₂* | presumption continues, but is DISPUTED from *t₂* |
| Several weak negatives | **not combined** into strong evidence unless the observers are calibrated and independence is justified (correlated sensors fail together) |
| Absence of *x* in *R* at *t* | says nothing about *x* elsewhere. "Not on shelf 3" ≠ "at the dock" |

**CE-A1 (occlusion).** At 10:06 a person stands in front of shelf 3. The camera's frustum covers the shelf, but the
box is occluded. A coverage model without occlusion produces evidence of absence, and the box "vanishes". With the
occlusion condition, *ρ* falls below threshold and the result is a weak negative: still PRESUMED on shelf 3,
DISPUTED from 10:06. Khronos also handles removal only when the robot revisits the scene (V, README).

**CE-A2 (wrong detector).** The person detector ran over shelf 3 at 10:09 and saw no person. That is evidence of no
*person* there, and **no evidence about the box**.

**CE-A3 (text coverage, M).** The user never mentions Sam after March in the sessions retrieved. If only 3 of 9
sessions were read, "Sam is still in Berlin" is PRESUMED at best. The coverage record says which sessions were read.

## 2.5 Identity

### Definitions
- A **referent** is minted by the system when a profile's **minting rule** is met (W: a track confirmed by ≥ *n*
  detections over ≥ *Δ* seconds). Detections that don't meet it stay **unresolved observations**.
- `refers-to(o, r)` links an observation to a referent: a claim with a method (tracker continuity, appearance
  match, human), a score and evidence.
- `same-as(r₁, r₂)` is a claim, reviewable and reversible (GUPI, V). **Only accepted `same-as` claims are used**
  when answering. Proposed ones appear as alternatives.
- **No transitive auto-merge.** Accepted `same-as` claims are closed transitively at query time (they are an
  equivalence). **Proposed** ones are never chained.
- **Splitting** a wrongly merged referent: retract the `same-as`. Its observations' `refers-to` claims are reviewed
  individually. History stays.

### Rules for uncertain detections
- A detection's class hypotheses (`ObjectHypothesisWithPose[]`, V) become competing `classified-as` claims. They
  never set the referent's type (one type per instance, no re-typing: probe P1B-B, V).
- `Detection3D.id` (optional, per detector, V) supports `refers-to` only within that detector's stream and only
  across gaps shorter than the tracker's documented re-identification window.

**CE-I1 (swap under occlusion).** Two identical boxes, *b₁* on shelf 3 and *b₂* on shelf 4, are swapped while
occluded. After the swap, the tracker continues ids by position. A system that trusts tracker continuity answers
"*b₁* never moved", wrongly. Under these rules, the re-acquisition after an occlusion longer than the window gives
proposed `refers-to` claims only. "Which box is on shelf 3?" then answers DISPUTED between *b₁* and *b₂*.

**CE-I2 (two Sams, M).** "Sam moved to Berlin" and "Sam's back in London" refer to two people. With mention-level
`refers-to` claims and no forced merge, the second statement does not end the first Sam's Berlin claim unless its
mention is resolved to the same referent.

**CE-I3 (sampling, L).** Sample 12 is a new referent created by the sampling event and constituted from material of
rock R (DOLCE constitution, V). Classifying sample 12 as basalt is a claim about sample 12, not about R. Inheritance
of the classification back to R needs an explicit rule.

## 2.6 Confidence

Four different quantities. Phase 1 had one.

| Quantity | Belongs to | Meaning | May be compared across sources? |
|---|---|---|---|
| **Model score** | observation | raw output of a detector or extractor (vision_msgs `score`, V) | **No**, unless calibrated |
| **Measurement uncertainty** | measurement (on an observation) | spread of a measured value with units (covariance, fit error) | yes, as physical quantities |
| **Credence** | attribution (agent + attitude + claim) | how strongly an agent holds the claim; for the system's own perspective, on its acceptance decision | only for the same agent and method, unless calibrated |
| **Derivation strength** | inferred claim | produced by the inference rule from its inputs | only if the rule is declared and validated |

**Claims carry no free-floating confidence.** "How sure" is always someone's credence about a claim. The same claim
can be held strongly by A and doubted by B.

**Calibration rule.** A number is treated as a probability only when it cites a **calibration record**: data,
method, error measure (for example, expected calibration error) and validity scope. Without one:
- comparisons are allowed only **within the same source and model version** (ordinal);
- **no thresholds across sources**;
- no arithmetic combination (products, Bayesian updates).

Inference does not propagate credence by default. A rule may declare a combination (minimum, product, learned),
and the answer cites it.

**CE-C1.** Detector A says *box* 0.9; detector B says *bin* 0.6. Choosing *box* because 0.9 > 0.6 is invalid
without calibration: the two scales may differ. Correct: two competing `classified-as` claims, DISPUTED unless a
policy ranks the detectors.

**CE-C2.** A pose with 3 cm standard deviation (measurement uncertainty) on a box that the system is only 50% sure
is *the* box it tracked (identity credence). Collapsing these into one "confidence 0.5 at 3 cm" loses which part
is uncertain.

**CE-C3 (L).** Spectrometer fits: basalt 0.7, anorthosite 0.6 (model scores, different models). Not
probabilities, not comparable. CONTESTED classification of R unless the science team's accepted review says
otherwise (ASSERTED by the team).

## 2.7 Development competency questions added
These extend the 22 Phase 1 development questions. They are development material, not evaluation evidence.

| DQ | Question | Expected status |
|---|---|---|
| DQ-23 | (CE-P1) Where was the box at 10:15, and on what basis? | PRESUMED shelf-3, policy *static-object/v1*, anchor 10:03 |
| DQ-24 | (CE-P2) Same question, asked as of τ 10:30 and τ 10:45 | PRESUMED shelf-3; ASSERTED dock |
| DQ-25 | (CE-P3) Where was the box at 10:10? | DISPUTED shelf-3 / dock |
| DQ-26 | (CE-A1) Was the box on shelf 3 at 10:07? | PRESUMED true, DISPUTED by a weak negative |
| DQ-27 | (CE-A2) Is there evidence the box was absent at 10:09? | No: person detector, wrong target kind |
| DQ-28 | (CE-F1) Where was the box at 10:03, as known at τ 10:10 and τ 10:25? | shelf-3 (superseded later); shelf-4 |
| DQ-29 | (CE-T1) Was the box picked up before 10:05 UTC? | UNKNOWN (no clock alignment) |
| DQ-30 | (CE-I1) Which box is on shelf 3 after the swap? | DISPUTED b₁ / b₂ |
| DQ-31 | (CE-I2) Where does each Sam live now? | per referent, with PRESUMED and coverage stated |
| DQ-32 | (CE-C1) What is the object? | DISPUTED box / bin; no ranking by raw score |
| DQ-33 | (CE-I3) What is sample 12, and what does that say about rock R? | sample 12 classified; R unchanged unless a rule applies |
| DQ-34 | Which answers in this session depended on a presumption? | list with policies |

## 2.8 Comparison with KnowRob's implemented semantics
Read from KnowRob's `dev` branch source on 2026-11-09 (V unless marked).

| Topic | KnowRob (as implemented) | Proposed here | Consequence |
|---|---|---|---|
| Time interval | `TimeInterval` holds optional `since` and `until` points; a missing bound means unbounded (`anytime()` = both missing) | windows on both bounds; missing end = unknown, not unbounded | KnowRob's default **assumes continuity** where ours answers UNKNOWN or PRESUMED |
| Interval intersection | `intersectWith` takes `max` of starts and `min` of ends over `std::optional`. An empty optional compares lower than any value, so `min(unbounded, t)` appears to yield *unbounded* (I: from reading the code; not run) | explicit window arithmetic | if confirmed, an intersection with an open-ended interval loses the bound; we should test our own arithmetic for the same mistake |
| Belief | B = "best guess... only one best guess at a time which is materialized" (comment in `ModalStage.cpp`), evaluated over facts marked certain or uncertain | competing claims kept; DISPUTED surfaced | KnowRob resolves before storing; we keep alternatives |
| Knowledge | K = grounded only in facts marked "certain" | supported statuses with evidence | similar intent; we cite evidence per answer |
| Confidence | a minimum-confidence **threshold** on statements; combined selectors take the smaller (more restrictive) value (`GraphSelector`) | no cross-source thresholds without calibration | KnowRob compares scores across sources by default |
| Perspective | an "ego" perspective (the agent running the KB) plus other agents' IRIs | the system as one agent; others via attribution | **equivalent idea**; no novelty claimed |
| Past | P ("at some point in the past") and H ("at any time in the past") over materialised episodes (NEEMs) | valid time with three-valued and presumed answers | KnowRob has temporal modalities; we add explicit presumption status |
| Revision history | no transaction-time model found in the files read (I) | transaction time on every record; queries "as known at τ" | needed for CE-F1, CE-P2 |
| Observed absence | none found in the files read (I; a full-text search of the code base was not done) | coverage + reliability | needed for CE-A1, CE-A2 |
| Persistence policies | none found (I) | named, versioned, defeasible | needed for CE-P1 to CE-P4 |

**What we must not claim as new:** perspectives, belief vs knowledge, temporal modal queries, robot episodic
memory, confidence on statements. **What remains to be shown useful:** keeping alternatives instead of a best guess,
transaction-time revision of spatial history, presumption status with defeasible policies, and coverage-based
absence. These are claims for the evaluation, not results.

## 2.9 Open semantic questions
1. Default horizons per kind (W objects, S people, L samples, M facts about people). Proposal: set by the profile
   author before evaluation, never tuned on sealed data.
2. Whether DISPUTED between presumptions should ever be broken by recency (CE-P3). Proposal: only by explicit,
   cited policy.
3. Coverage granularity for robots (frustum vs voxel set). Proposal: named regions in v1, geometry later.
4. How reliability grades map to thresholds without calibration data. Proposal: ordinal grades in v1.
5. Whether INFERRED should be split by rule type (definitional vs empirical). Deferred.
