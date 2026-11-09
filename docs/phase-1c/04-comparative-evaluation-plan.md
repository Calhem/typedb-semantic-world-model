# 4. Revised comparative evaluation plan, with proposed thresholds

Builds on Phase 1B [04-evaluation-protocol.md](../phase-1b/04-evaluation-protocol.md), which stays as written.
This plan makes the three contributions separable and **proposes numbers for approval**. No result exists yet, so
none of these numbers was chosen with knowledge of an outcome. Once approved, they are frozen in a preregistration
commit before B and C are built.

## 4.1 Three contributions, three designs
| Contribution | Question | Design | Held constant |
|---|---|---|---|
| **Ontology** | Does a richer semantic model improve correctness, interoperability or maintainability over a simple representation? | **A vs B** and **A vs C**: A (event log + current state) against the full specification | data, questions, scorer, application algorithms where A can use them |
| **Database** | Does TypeDB give measurable benefits over PostgreSQL with equivalent semantics? | **B vs C**: same specification, same application algorithms, same fixtures | everything except the store and its query language |
| **Application** | Which results come from identity resolution, persistence policies, inference and other algorithms? | **Ablations inside B and C**, the same in both (4.3) | store and ontology |

**Identical workloads.** One neutral fixture format (JSON) loaded by thin loaders into A, B and C. One question set.
One scorer (status, binding, evidence; see [05-withheld-evaluation-spec.md](05-withheld-evaluation-spec.md)). Same
machine, same container limits, warm and cold runs, 5 repetitions for timings.

## 4.2 Capability attribution (per question, published)
For every question and every approach, the harness records which layer produced each part of the answer:
`schema` (a constraint or type did the work), `store-query` (a TypeQL or SQL query or function), `app` (Python:
identity resolution, policy evaluation, inference, ranking). A question counts toward the **database contribution**
only if B and C differ in `store-query` work and the difference changes an outcome or a cost.

## 4.3 Application ablations (in both B and C)
| Ablation | Replaces | Expected to affect |
|---|---|---|
| **No identity resolution** | `refers-to` by tracker id only; no review | identity family |
| **No persistence policies** (strict) | all gaps UNKNOWN | temporal continuity family (most answers become UNKNOWN) |
| **Naive continuity** | open-ended facts read as still true (the PostgreSQL open-range default) | temporal continuity; unsupported assertions |
| **No coverage** | absence = no detection | observed-absence cases |
| **No inference rules** | only stored facts | inferred-status questions |
| **Uncalibrated thresholds** | rank hypotheses by raw score across sources | uncertainty family |

Each ablation's effect is reported per family as the change in correct answers and in unsupported assertions.

## 4.4 Proposed thresholds and their justification
Sample-size arithmetic used throughout: with *n* scored items and accuracy near 50%, the 95% half-width of one
proportion is about 0.98/√*n*. At *n* = 120 that is ±9 points; a **paired** comparison on the same items is
narrower, about ±5-7 points, depending on how often the approaches disagree.

### Correctness
| Hypothesis | Threshold | Justification |
|---|---|---|
| H1 ontology > minimal (A vs B, A vs C) | B and C each beat A by **≥ 10 points** on the temporal, identity and provenance families (pooled), with the paired 95% interval above 0 | the smallest effect that 120 items per family can show reliably, and the size at which a developer would choose to adopt a schema |
| H2 TypeDB non-inferior to PostgreSQL | lower 95% bound of C − B ≥ **−5 points** on every family, **and** item-level agreement ≥ **98%**, with every disagreement explained | B and C implement one specification, so they should agree. Any disagreement is a bug or an expressiveness limit. 5 points is half the ontology effect: a store that loses half of what the ontology gains is not acceptable |
| H7 no invented continuity | **0** unsupported definitive answers in B and C | a specification requirement, not a statistical target |
| Abstention honesty | on items whose gold status is UNKNOWN, B and C answer UNKNOWN **≥ 95%** of the time | ≤ 5% leeway for parser or loader faults found during review |

### Portability and interoperability
| Measure | Threshold | Justification |
|---|---|---|
| Meaning-altering core changes on held-out domains | **0** | the definition of a shared core |
| Additive core changes per held-out domain | **≤ 2** | some gaps are expected; more than two means the core was not general |
| Held-out domain questions answered with core + a new module | **≥ 90%** | the rest are expected to need genuinely domain-specific constructs |
| Round-trip answer preservation between profiles (shared types) | **≥ 95%**; silent loss **0** | losses must be explained; 5% allows type mismatches that are reported |

### Maintainability (ontology and database)
| Measure | Threshold | Justification |
|---|---|---|
| Schema + query text per question, C vs B (H3) | C ≤ **0.7 ×** B | a 30% reduction is noticeable to a maintainer; less is within style variation |
| Invalid-write suite (50 cases) rejected by the store | C ≥ B | schema enforcement is TypeDB's claimed advantage |
| Scripted change (add a claim type with time and evidence) | files and lines touched, C ≤ B | the work a maintainer would actually do |

### Latency, storage and resources
| Measure | Threshold | Justification |
|---|---|---|
| ROS named queries, p95 | **≤ 50 ms** on the robot computer (in the container on this Mac until hardware exists) | task-level decisions (behaviour tree conditions, operator questions) tolerate this; it is below a typical camera-to-detection latency (~100 ms, A) |
| Memory retrieval per question, p95 | **≤ 500 ms** | the answering model call takes seconds; retrieval must not dominate |
| C vs B latency | C p95 ≤ **2 ×** B per family | beyond 2×, cost outweighs modelling convenience for most users |
| Storage, bytes per fact on disk | C ≤ **3 ×** B | TypeDB stores indices per role; above 3× it becomes a deployment issue |
| ROS data reduction | semantic records ≤ **1/100** of the raw bag bytes for the same run | the semantic layer must be far smaller than logs, or one would just keep the logs |
| ROS ingestion | sustains **10 ×** the measured semantic event rate without backlog | headroom for busy scenes |
| ROS adapter + TypeDB memory | **≤ 1 GB RSS** for a 1-hour run | ≤ 12% of an 8 GB companion computer |
| ROS adapter CPU | **≤ 1 core** average | leaves the rest for perception and navigation |
| Effect on robot control | control-topic rates and Nav2 goal outcomes change **≤ 1%** with the adapter on vs off, and **0** failures attributable to TypeDB being down | the architectural constraint: the semantic layer is never in the control path |

### GUPI answer baseline (for later comparison)
The world-ontology memory profile is "at least as good" if its accuracy is within **−3 points** (lower 95% bound)
of GUPI K10 on the same 447 questions, and "better" only if the lower bound of the difference is **> 0**. The
justification: the answer pipeline is identical except for retrieval, so differences should be small, and the
claim of improvement must survive the interval.

## 4.5 Failure is publishable
Each threshold has a "fails" reading in Phase 1B 04 §4.3. Combinations to report plainly:
- H1 fails: the ontology adds nothing measurable over a log.
- H1 passes, H2 or the latency/storage limits fail: the ontology is useful; TypeDB is not the right store for it.
- Ablations show the gains come from application algorithms in both B and C: the contribution is algorithmic,
  not ontological or database-related.

## 4.6 Process
1. You approve or change the thresholds. They are committed as `preregistration-v1` **before** B and C exist.
2. Development on the 22 + 12 development questions only.
3. Sealed sets are scored once, by a script, with results published whatever they show.
