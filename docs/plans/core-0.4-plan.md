# Core 0.4: World Representation, implementation plan (LABS-1.001)

**Status: PLAN, refined under LABS-1.002 (2026-11-10).** Direction approved subject to the rulings in section 9;
**Stage A0 authorised**; Stages A-E not yet authorised. Branch `planning/core-0.4`, from `main` at `b64f635` (Core 0.3).
LABS-1.001 version: `1741c99`.

**Labels:**
- **[A]** established architecture: frozen [World Ontology v0.2](../architecture/world-ontology-v0.2.md) and
  merged Core 0.3.
- **[V]** verified TypeDB 3.14.1 behaviour: [best practices](../typedb-modelling-best-practices.md), or this plan's
  probes `probes/core04_feasibility.py` (P1-P9; output `probes/core04_feasibility.out.json`).
- **[E]** engineering assumption, not yet tested.
- **[R]** recommendation needing approval.

The draft TypeQL in this document and in the probe is **exploratory**. It was loaded only into throwaway databases;
`schema/` and `src/` are unchanged.

---

## 0. Starting point and what the plan must not change
- **Keep:** the proposition-attestation-acceptance layers, perspective-specific supersession (D14), snapshot
  inheritance, occurrences vs descriptions, answer statuses, and the selective/full-load equivalence [A]. All 78 Core
  0.3 tests must keep passing unchanged.
- **Core 0.3 already has** (schema `core-0.3.tql`):
  - kinds `physical-object`, `social-object`, `place`, `information-object`, `occurrence`;
  - concepts `category`, `social-role`, `quality-kind`;
  - reference systems `clock`, `spatial-frame`, `unit`;
  - propositions `existence`, `located-at`, `part-of`, `member-of`, `depends-on`, `classified-as` (with context),
    `has-quality` (value or `lower`/`upper`/`coverage-level`, unit), `same-as`, `describes`, `initiates`,
    `terminates`;
  - event descriptions with six participant roles [A].
- **Three code constraints found while planning** [V, from reading `src/worldmodel/model.py`]:
  1. **Exact type labels.** The code compares exact labels (`ctype == "event"`, `"same-as"`, `"existence"`). TypeDB's
     `isa event` already includes subtypes, but `isa!` returns the subtype's label (`pickup`) and specialised roles
     come back as `pickup:picker` (P3b, P3c). Profile subtypes would be silently dropped.
  2. **One-role functional slots.** "One value at a time" is a Python constant keyed by one role (`located-at`:
     `located`). Frame transforms need a two-role slot (parent, child).
  3. **Propositions cannot be role players yet.** Keys contain `|`, which ids may not, so `initiates`/`terminates`
     outcomes cannot be bound (the cause of deferral D2).

## 1. Proposed schema additions by stage
All are additive to `core-0.3.tql`. None changes an existing type's meaning. The draft loads on top of the merged
schema (P1) [V].

### Stage A0: groundwork (no new world concepts; unblocks A-D)
| Addition | TypeDB | Purpose | Label |
|---|---|---|---|
| Proposition ids | `proposition owns wm-id @key` (second key); value `p:` + 24 hex chars of SHA-256 of the canonical key, deterministic | propositions can be role players (`initiates`, `terminates`, and quality instances later); uniform player lookup | **[R]**; second key enforced (P8) [V]; propositions as players (P2) [V] |
| Type and role lattice | Python, from schema introspection: each label maps to its core supertype, each specialised role to its core role | replaces exact-label checks, so profile subtypes behave as their core types | **[R]**; needed because of P3b/P3c [V] |
| Slot metadata | data, not schema: per proposition type, the roles that form the slot (one value at a time) and what counts as the value | generalises `FUNCTIONAL`; declared by core and profiles | **[R]**; implements v0.2's "profile metadata" [A] |

### Stage A: physical structure
| Addition | TypeDB (draft) | Notes | Label |
|---|---|---|---|
| `constitution` | `relation constitution sub proposition, relates constituted, relates constituent` | what something is made from (sample from rock; a crate from boards); v0.2 core [A] | [A] type, [V] loads |
| Material | no type: materials are categories (`classified-as(x, steel)`); amounts of matter are a profile sortal (`portion`) with constitution | avoids a material taxonomy in the core | **[R]** |
| `positioned-in` | `relates positioned, relates frame`; owns `x-min`/`x-max`, `y-min`/`y-max`, `z-min`/`z-max` (metres), optional `qw qx qy qz` | metric pose, per-axis ranges (v0.2 §3.5 [A]); slot (positioned, frame) | [V] loads, range query works (P6) |
| `anchored-to` | `relates frame, relates anchor` | a frame attached to a particular (a rover's base frame) over time; slot (frame) | [A], [V] |
| `frame-transform` | `relates parent, relates child`; owns `tx ty tz`, `qw qx qy qz` | how frames relate over time; slot (parent, child) | [A], [V]; chain traversal by function (P4) [V] |
| Frame reasoning | TypeQL function `frames_reachable(frame, world)` finds the chain; Python composes transforms and propagates ranges conservatively (box around the rotated box); derived poses are INFERRED citing the transforms (rule `frame-transform/v1`) | no derivation records (D8 stays deferred) | **[R]**; function [V], composition [E] |
| Identity vs composition vs location | no new types: identity = particular id; composition = `part-of`/`constitution`; location = `located-at`/`positioned-in` | tests make the separation explicit | [A] |

### Stage B: dynamics
| Addition | TypeDB (draft) | Notes | Label |
|---|---|---|---|
| `initiates` / `terminates` in use | existing types; `record_event` writes them for its effects and endings (closes D2) | needs A0 proposition ids | [A], [V] (P2) |
| `causes` | `relates cause, relates effect`; players: event descriptions **and** occurrences | asserted, never inferred from succession [A]. Causation between occurrences is judged through accepted `describes` links, per perspective | **[R]** on players; [V] loads; chain function (P5) needs narrowing, because a function's return type must cover every possible player (FIN4) [V] |
| Processes and actions | no types: core vocabulary categories `process`, `action`; action = event classified `action` whose actor has the agency capacity | v0.2 §3.2 [A] | [A] |
| State transitions | an event with `initiates`/`terminates` links; a query lists them | [A] | [A] |
| Single-valued event roles | metadata (A0), used by `occurrence()` to report DISPUTED participants (closes D9) | | **[R]** |
| `depends-on` kind | add optional `relates kind` (category) | v0.2 §3.4 [A]; additive, keys of existing propositions unchanged | [A], [E] |

### Stage C: qualities, quantities and agency
| Addition | TypeDB (draft) | Notes | Label |
|---|---|---|---|
| Units | `unit owns dimension, owns si-factor, owns si-offset`; content stored in the canonical SI unit per dimension; originals kept on the measurement | v0.2 §3.3 [A] | [V] loads |
| Measurements | **amended under DX-2, see section 9.2:** three distinct things: the measuring **activity** (an event description classified `measurement`), the **result record** (an `information-object` carrying raw value, unit, standard uncertainty, coverage factor and conditions), and the **reported content** (a `has-quality` range), linked by `produced(activity, result)` and `reports(result, content)` | no change to the epistemic layer | **[R]**, section 9.2 |
| Comparability | Python: `compare(range a, range b)` → possibly compatible / incompatible / incomparable, with the reason (dimension, coverage level, conditions); **no reconciliation** | v0.2 clarification B [A]; overlap test in TypeQL [V B3] | [A] |
| Roles | existing `classified-as(x, social-role, context)`; domain relations (`employment`) in profiles | v0.2 §3.4 [A] | [A], [V] (P7b) |
| Capabilities | `capability sub concept`, held via `classified-as(x, capability, context?)`, no new relation (DX-3, approved provisionally); see section 9.5 | | [A] by ruling |
| Agency check (E2, D7) | `classified-as(x, agent)` checked on `attest()`: report mode by default (a warning listed in a validation report), strict mode optional | strict by default would require every Core 0.3 test fixture to classify its attesters | **[R]** |

### Stage D: domain extensions (profiles)
A profile is a schema module (`schema/profiles/<name>.tql`) plus a metadata file (slots, single-valued roles,
vocabulary seeds). It is installed after the core and is never removed while data uses it (P9) [V].

| Profile | Sortals and relations | Shows |
|---|---|---|
| **Mechanical** (`mechanical-0.1`) | `component sub physical-object`, `vehicle sub physical-object`; `connected-to(endpoint ×2)` with joint-kind category; `replacement sub event, relates removed as patient, relates fitted as instrument` | part replacement with identity kept (C3 of v0.2), frames anchored to the body, wheel pose in the vehicle frame, tyre pressure ranges in kPa (canonical Pa) |
| **Organisational** (`organisation-0.1`) | `person sub physical-object`, `organisation sub social-object`; `employment(employer, employee)`; `meeting sub event, relates chair as actor` | roles in context, disagreement between perspectives (A asserts, B denies), agency as a capacity |
| **Laboratory** (`laboratory-0.1`) | `sample sub physical-object`, `instrument sub physical-object`; `sampling sub event, relates sampler as actor, relates sampled as origin, relates product as destination`; **identified quality instances** (`quality-instance sub particular`, `inheres-in`) | constitution, measurement series with comparability, quality identity across repeated measurements (v0.2 clarification C) |

**Genuinely domain-specific** (profiles, not core): sortals; specialised event roles; domain relations (`employment`,
`connected-to`); vocabularies (joint kinds, materials, quality kinds, units in use); single-valued roles; comparability
conditions; quality instances. **Foundational** (core): everything in A-C.

### Stage E: validation (section 5)

## 2. Stage dependencies and milestones
```
A0 groundwork ──► A physical ──► B dynamics ──► C qualities & agency ──► D profiles ──► E final validation
      │                                 ▲                                    ▲
      └── lattice + slot metadata ──────┴──── (B needs proposition ids) ─────┘ (D needs the lattice)
```
| Milestone | Testable on its own by | Depends on |
|---|---|---|
| A0 | all 78 tests unchanged; new tests: proposition ids deterministic, a `pickup sub event` instance answers through every event query | — |
| A | physical-structure tests (section 5) | A0 (slot metadata) |
| B | dynamics tests | A0 (proposition ids), A (constitution for transformations) |
| C | quantity and agency tests | A0, B (measurement is an event) |
| D | one profile per milestone (D1 mechanical, D2 organisational, D3 laboratory), each with its scenario tests | A-C |
| E | cross-domain suite, equivalence, benchmarks, extensibility checks | D |

Each milestone is committed and pushed separately on its own branch, and stops for review if the plan says so.

## 3. Representative examples
**Physical: rover battery swap and camera pose.**
- Rover `rover` with battery `b1`. The rover's frame `rover-base` is `anchored-to` the rover; `rover-cam` relates to
  it by a `frame-transform` (0.2, 0, 1.1); `rover-base` relates to `map` by (10, 5, 0).
- At sol 12 a `replacement` event ends `part-of(b1, rover)` (`terminates`) and starts `part-of(b2, rover)`
  (`initiates`). `b1` keeps its identity and `existence`.
- A box is observed at x ∈ [1.9, 2.1] in `rover-cam`.
- Expected answers:
  - the rover is the same particular before and after;
  - its battery at sol 11 is `b1` and at sol 13 is `b2`;
  - the box in `map` is INFERRED at x ∈ [12.1, 12.3], y ∈ [4.9, 5.1], z ∈ [1.1, 1.3], citing both transforms;
  - after a relocalisation supersedes `map → rover-base`, derived poses change from that knowledge time only.

**Social: depot management.**
- `person` B, `organisation` acme.
- A asserts `classified-as(B, site-manager, context: depot-7)`; B denies it; the system accepts A's claim; the
  operations lead accepts B's.
- `employment(acme, B)` is attested from January.
- A `meeting` (chair B) on Tuesday initiates `classified-as(C, deputy, depot-7)`.
- Expected answers:
  - system: B is site manager (ASSERTED, B's denial an alternative); lead: not;
  - C is deputy from Tuesday, with its initiating event;
  - B is an agent, by classification, not by kind.

**Scientific: rock sampling and mass.**
- A `sampling` event (sampler: the rover arm; sampled: rock R; product: sample-12) initiates `existence(sample-12)`
  and `constitution(sample-12, R)`.
- Two `measurement` events on balance B-3: 3.51 ± 0.02 kg and 3.49 ± 0.02 kg (k = 2). Each yields
  `has-quality(sample-12, mass, [3.47, 3.55] kg)` and `[3.45, 3.53] kg`, linked by `result-of`.
- A third measurement at k = 3 gives `[3.43, 3.61]`.
- Expected answers:
  - both k = 2 ranges are returned, labelled *possibly compatible*, with no intersection;
  - the k = 3 range is *incomparable* with them (different coverage level);
  - with the laboratory profile's `quality-instance`, the three measurements refer to the same quality instance of
    sample-12.

## 4. Query capabilities (representative)
Queries marked [V] were run on the probe's data, with the results shown. Others are expected [E].
| Question | TypeQL (core of it) | Expected result |
|---|---|---|
| What frames can be reached from `map`? | `let $g in frames_reachable($map, $w);` | `rover-base`, `rover-cam` [V P4] |
| What did e1 cause, transitively? | `let $x in effects_of($e1, $w);` | `e2`, `e3` [V P5] |
| What is within x ∈ [1.5, 2.5] in `rover-cam`? | `$p isa positioned-in (positioned: $x, frame: $f), has x-min $a, has x-max $b; $a >= 1.5; $b <= 2.5; attestation (content: $p);` | `box` [V P6] |
| Which events have an actor (including profile roles)? | `$e isa event (actor: $x);` | finds `pickup` pickers too [V P3] |
| What did the sampling event initiate? | `$i isa initiates (event: $e, outcome: $o); $o has proposition-key $k;` | the constitution proposition [V P2] |
| Who does acme employ? | `$p isa employment (employer: $o, employee: $x);` | `bob` [V P7b] |
| What can the rover do? (option 2) | `has-capability (bearer: $r, capability: $c);` | `can-drive` [V P7] |
| Box pose in `map` at t (system view, as known at τ) | Python: select transforms and pose (selective path), compose, propagate ranges | INFERRED ranges citing both transforms [E] |
| Are these mass measurements comparable? | TypeQL overlap (`$la <= $ub; $lb <= $ua;`) + Python comparability rules | possibly compatible / incomparable as above [V B3 for overlap; E for rules] |

All of these go through the existing selective and full-load paths, and must give identical answers [A].

## 5. Acceptance criteria
| Stage | Completion conditions |
|---|---|
| **A0** | 78 Core 0.3 tests pass unchanged on both paths; proposition ids deterministic and unique (test); a profile subtype of `event`, and a specialised role, behave as `event`/`actor` in `events`, `history`, `occurrence` and judgements (tests); slot metadata reproduces today's `located-at` behaviour exactly (equivalence on the Core 0.3 benchmark world) |
| **A** | tests for constitution, positions and frames: identity unchanged by composition changes; transform chains; derived poses with correct ranges (numerical tolerance 1e-9); relocalisation supersession visible only from its knowledge time; hypothetical world unaffected by later transforms; equivalence on both paths |
| **B** | tests for `initiates`/`terminates` written by `record_event`; state transitions listed; causal chains asserted, not inferred (succession alone gives none); occurrence-level causation through accepted `describes` only; single-valued participant disputes |
| **C** | unit conversion round trips; canonical storage; comparability labels for overlap, disjoint and incomparable cases, with reasons; no reconciliation without a named policy; measurement uncertainty and credence stored separately (test); agency report lists unclassified attesters |
| **D** | each profile installs after the core, adds only subtypes, specialised roles, new proposition types and metadata; **core-protection test**: every core test passes with all three profiles installed; **collision test**: no label collisions across core and profiles; each profile's scenario (section 3) answers as expected |
| **E** | cross-domain suite green on both paths, twice, no leftover databases; equivalence (whole answers, evidence included) for every new query; performance thresholds in section 9.4, kept separate for unchanged Core 0.3 workloads and for new Core 0.4 workloads; records-per-change table across the three domains |

## 6. Technical risks
| Risk | Why | Mitigation |
|---|---|---|
| **Proposition growth for continuous values** | v0.2 puts values into content, so every new pose or measured range is a new proposition (plus attestation) [A] | measure in E; a rounding/quantisation policy per frame or quantity is a later option; values on attestations would contradict v0.2 (rejected) |
| **A0 touches many code paths** | the type/role lattice replaces exact-label checks throughout | do A0 alone, behaviour-neutral, with the 78 tests as the gate |
| **Slot metadata enters judgement** | `_judge` uses it for exclusivity and precedence | equivalence test reproducing Core 0.3 answers exactly; no change to acceptance or supersession code |
| **Measurement as an event (deviation)** | v0.2 says observation; observations are deferred epistemic records | approval needed; if refused, Stage C stores measurement metadata only after observations are designed (larger change) |
| **Frame mathematics** | quaternion composition and conservative range propagation are easy to get subtly wrong | property tests (identity, inverse, associativity), fixed tolerances |
| **Function typing** | recursive functions must declare return types that cover every possible role player (FIN4) [V] | narrow matches inside functions; keep functions to selection, with time and acceptance in Python as today |
| **Query performance** | more types and roles; frame chains add queries | benchmarks in E against the Core 0.3 baseline (statistically thin; repeat runs) |
| **Profile coupling** | profile roles on core types cannot be removed while used (P9, P1B-D) [V] | profiles are installed, not uninstalled; removal is a migration |
| **Semantic ambiguity** | capability vs classification; causation between descriptions vs occurrences | explicit decisions below |

## 7. Alignment with frozen v0.2
| v0.2 element | Core 0.3 | Core 0.4 plan |
|---|---|---|
| `constitution`, `positioned-in`, `frame-transform`, `anchored-to`, `causes` (D13) | missing | **added** (A, B) |
| `initiates` / `terminates` in use (D2) | schema only | **used** (B) |
| single-valued event roles, functional slots as profile metadata (D9) | Python constant | **metadata** (A0) |
| quantities with units, comparability (D12 part) | stored, not reasoned | **canonical units, comparability** (C) |
| agency as a checked capacity (D7) | not checked | **report mode** (C) [R] |
| process / action conventions | — | vocabulary (B) |
| profiles, extension points | none | **three profiles** (D) |
| quality instances as an extension (clarification C) | — | **laboratory profile** (D) |
| `clock-alignment`, `absence-of` (D13), observations and coverage, OBSERVED/PRESUMED (D1), persistence and resolution policies, derivations (D8) | deferred | **still deferred**: outside LABS-1.001's stages; epistemic or temporal machinery |

**Proposed deviations and missing specifications (need approval):**
- **DX-1:** propositions get a second key `wm-id` (implementation; no meaning change).
- **DX-2:** a measurement is an event description, not an observation (deviation from v0.2 §3.3).
- **DX-3:** capability representation (missing in v0.2; option 1 recommended).
- **DX-4:** `causes` accepts occurrences as well as descriptions (clarifies v0.2's "events").
- **DX-5:** agency check in report mode (a softening of E2's wording, which says it is checked).

**Simpler alternatives considered:**
- *Symbolic location only, no metric frames*: simpler, but cannot represent poses, frames attached to objects, or
  corrections of transforms, which Stage A requires.
- *Capability as a relation*: more expressive later (conditions), but `classified-as` already provides time, context,
  perspectives and disputes, so option 1 delivers the same now with no new type.
- *Measurement metadata on the `has-quality` attestation*: one record fewer, but it would put measurement
  uncertainty on a stance record, contradicting v0.2's separation of measurement uncertainty from credence.

## 8. Decisions requested under LABS-1.001 (see section 9.1 for the rulings)
1. **A0 groundwork** as the first milestone, behaviour-neutral (proposition ids, type and role lattice, slot
   metadata).
2. **DX-1 to DX-5** above.
3. Material as categories plus constitution; **no material or system type**.
4. Three profiles (mechanical, organisational, laboratory) as the generality demonstration, and the profile format
   (schema module plus metadata file).
5. Stage E thresholds: +10 % on the Core 0.3 benchmark; measured growth per pose update, with no threshold until a
   first measurement exists.
6. `clock-alignment` and `absence-of` remain deferred beyond Core 0.4.

---

## 9. Refinements under LABS-1.002

### 9.1 Rulings recorded
| Decision | Ruling (LABS-1.002) | Consequence for the plan |
|---|---|---|
| DX-1 proposition `wm-id` | approved conditionally: deterministic, immutable; existing identity and key semantics preserved; uniqueness, collision and migration tested | A0.1 |
| DX-2 measurement | **amended**: separate the measuring activity from the observation/result; smallest v0.2-consistent form; no epistemic change | section 9.2 |
| DX-3 capability | approved provisionally: concepts and classifications, changing over time and in context; no new machinery | section 9.5 |
| DX-4 causes with occurrences | approved conditionally: keep occurrences and descriptions distinct; causation asserted, never inferred | section 9.3 |
| DX-5 agency check | approved: diagnostic/report mode; Core 0.3 behaviour unchanged | Stage C |
| A0 first | approved | implemented under LABS-1.002 |
| Three extension categories | approved for later validation | Stage D |
| Clock alignment, recorded absence | deferred; remain tracked limitations | section 7 |
| Material or system types | not introduced without a demonstrated identity or modelling requirement | Stage A |

### 9.2 Measurement: activity, result, reported content (DX-2 amended)
v0.2 §3.3 treats a measurement as an observing act that yields a result with uncertainty, and a proposition supported
by it. Observations as epistemic records are deferred (D1). The smallest representation that keeps the three apart,
using only existing categories:

| Thing | What it is | Representation | Time |
|---|---|---|---|
| **Measurement activity** (occurrence) | the act of measuring: who measured what with which instrument | an event description classified by the category `measurement` (actor: operator; patient: the measured bearer; instrument: the instrument), its occurrence attested by its source, and optionally linked to an `occurrence` by `describes` | occurrence interval |
| **Result record** (observation/result) | what the act produced: raw value, unit, standard uncertainty *u*, coverage factor *k*, conditions, instrument calibration reference | an `information-object` (a result record) owning those attributes | the result's recorded time |
| **Reported content** | what the result says about the world: "sample-12's mass lies in [3.47, 3.55] kg at k = 2" | a `has-quality` range proposition (canonical SI), attested by the lab with basis observation | the quality's valid time |
| Links | the activity produced the result; the result reports the content | propositions `produced(activity: event, result: information-object)` and `reports(result: information-object, content: proposition)`, each attested | — |

- *Uncertainty kinds stay apart:* measurement uncertainty is on the result record and fixes the range; credence and
  stance are on attestations.
- *No epistemic change:* the links are ordinary content. When v0.2 observations are implemented later, a result record
  can be linked to them by evidence.
- *Unresolved (U-1):* whether a result record should later **be** v0.2's `observation` type (a migration) or remain an
  information object linked to it.

### 9.3 Causal descriptions vs occurrence-level causal claims (DX-4)
- **Description-level:** `causes(cause: e1, effect: e2)` between event descriptions is a source's claim that the
  happenings *as it describes them* stood in a causal relation.
- **Occurrence-level:** `causes(cause: o1, effect: o2)` between occurrences is a claim about the happenings
  themselves, independent of any description.
- **Lifting, per perspective:** a description-level claim answers an occurrence-level question only when both
  descriptions have usable `describes` links (for that perspective) to the occurrences asked about. The answer keeps
  the description-level claim as its support and cites the `describes` links. Mixed forms (description → occurrence)
  are allowed and lift the same way.
- **Never inferred:** not from temporal order, not from co-reference alone, not transitively in answers. A causal
  *chain* query lists asserted links. It does not turn them into new causal claims.
- *Unresolved (U-2):* the status label of a lifted answer: the original claim's status (current lean) or INFERRED.

### 9.4 Performance thresholds (two separate families)
**Unchanged Core 0.3 workloads.** The Core 0.3 benchmark (same workload, same harness, Python 3.13), with the median of
three runs per measure:
| Measure | Baseline (Core 0.3 + fetch) | Threshold after each stage |
|---|---|---|
| selective question median / p95 | 43.5 / 60.3 ms | ≤ 47.9 / 69.3 ms (+10 % / +15 %) |
| full-load question median | 2,234 ms | ≤ 2,460 ms (+10 %) |
| ingestion, 1,000 moves | 56.0 s | ≤ 61.6 s (+10 %) |
| database size | 12.34 MB | ≤ +5 % (only schema additions should change it) |
| answers | — | identical to Core 0.3 on both paths |

**New Core 0.4 workloads** (no baseline exists yet). The first measurement establishes it, under provisional
ceilings; later stages must stay within +10 % of it.
| Workload | Provisional ceiling |
|---|---|
| pose in another frame via a chain of ≤ 4 transforms, p95 | ≤ 100 ms |
| records written per pose update | ≤ 4 |
| measurement series of 100 results: comparability report | ≤ 2 s |
| profile installation (three profiles) | ≤ 5 s |

### 9.5 Changing capabilities and contextual roles (DX-3)
- **Capabilities** are concepts of the subtype `capability` (e.g. *can-drive*, *can-sample*). A particular holds one
  through `classified-as(holder, capability, context?)`, attested over an interval: a rover gains *can-sample* when its
  arm is fitted and loses it when the arm fails. Changes are new attestations or supersessions, and disputes and
  perspectives work exactly as for any classification.
- **Roles** are `social-role` concepts held through `classified-as(holder, role, context)`, where the context is the
  organisation, site or activity in which the role applies.
- **Distinction:** a role is a position assigned within a context (site manager); a capability is what something can
  do (drive). Agency is the category `agent`. All three change without changing identity, because they are
  classifications, never kinds.
- **Not core:** conditions on capabilities ("only when charged"). If needed, they are expressed as the context or as
  separate content in a profile, once a scenario requires it.

### 9.6 Spatial and transformation conventions (Stage A)
- **Frames:** right-handed Cartesian; lengths in metres; angles in radians.
- **Rotations:** unit quaternions (w, x, y, z), Hamilton convention, active rotation, normalised on write. A norm more
  than 1e-9 from 1 is rejected.
- **Transform semantics:** `frame-transform(parent: P, child: C)` gives the pose of C's origin and axes expressed in P,
  so a point p_C expressed in C is p_P = R·p_C + t, with (t, R) owned by the transform.
- **Composition:** T_AC = T_AB ∘ T_BC (R_AC = R_AB·R_BC, t_AC = R_AB·t_BC + t_AB).
- **Inverse:** T_CP = (Rᵀ, −Rᵀ·t). Inverse use is computed, never stored.
- **Uncertainty:** an axis-aligned position range is transformed by mapping its 8 corners and taking their bounding
  box (conservative). Rotations are treated as exact in Core 0.4.
- **Time:** a derived pose holds only where every input attestation certainly holds (intersection of intervals); no
  extrapolation. Its knowledge time is the latest recorded input.
- **Chains:** the shortest chain found by `frames_reachable`; if several chains exist at t, they must agree within
  1e-9 m, otherwise DISPUTED.
- *Unresolved (U-3):* rounding policy for continuous parameters in proposition keys (proposition growth risk).

### 9.7 Unresolved decisions (not resolved by implementation)
| # | Question | Needed by |
|---|---|---|
| U-1 | Result record: an information object linked to future observations, or later migrated to v0.2's `observation` type? | Stage C |
| U-2 | Status of a lifted occurrence-level causal answer: original status or INFERRED? | Stage B |
| U-3 | Rounding or quantisation of continuous parameters in keys (positions, ranges) | Stage A |
| U-4 | Where profile metadata lives: A0.3 stores functional-slot declarations as data in TypeDB (an implementation choice consistent with "TypeDB is the only store"); profile packaging is Stage D | Stage D |
| U-5 | Whether a subtype of a functional predicate always inherits its slot, or may declare its own | A0.3 implements inheritance by default, with a declaration overriding it; review |
