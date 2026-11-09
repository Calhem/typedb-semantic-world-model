# 6. Architectural decision register

Each entry: the recommendation, the evidence for it, the strongest counterargument, a confidence level, and what is
still unresolved. **Confidence:** *high* = verified evidence and no serious counterargument; *medium* = evidence
plus a credible counterargument; *low* = mostly judgement, to be settled by experiment.
Phase 1 decisions D1-D10 are mapped at the end.

| ID | Decision | Recommendation | Evidence | Strongest counterargument | Confidence | Unresolved |
|---|---|---|---|---|---|---|
| **AD1** | What the project claims | A **domain-neutral core with profiles**, not a universal ontology; the research claim is *cross-application sharing with measured loss and cost* | Prior art covers upper ontologies, robot belief and memory, scene graphs and bitemporal agent memory (01, V); the cross-application gap survives checking (01 §1.7, I) | The gap may be a gap because nobody needs it: robot and chat teams rarely share memory | medium | Whether a real user needs robot ↔ video ↔ memory exchange |
| **AD2** | Foundation | **Minimal independent core, aligned to DUL** with a tested mapping; BFO mapping for scientific modules only | DOLCE time-indexes the relations we need, including classification (V); KnowRob uses DUL (V); SOMA is LGPL and robotics-centred (V) | Use SOMA directly and avoid reinventing; or BFO for ISO standing | medium | Mapping test method; whether to publish an OWL rendering |
| **AD3** | 3D vs 4D | **3D** endurants, time on relations | DOLCE (V); every application asks about one object id | 4D fits tracking and video (temporal parts) | medium-high | — |
| **AD4** | Changeable facts | Every **contingent** fact is a subtype of the abstract `claim` **relation** (the relation is the claim); static facts allowed when declared; recording agent is the default attributor; evidence required where a profile's questions need it | GUPI's schema already does this (V); cost drops to 1 relation + time per fact (I) | Optional evidence erodes "evidence before assertion" | high (pattern) / medium (optional evidence) | Per-profile evidence policy |
| **AD5** | Time axes | **Three primitives:** valid time, observation (phenomenon) time, transaction time; optional result time; every value names its **time reference system** (wall, sim, media, sequence, mission) | Event and belief time reduce to valid time of event and attribution claims (I); ROS sim time and video media time verified to differ from wall time (V: `use_sim_time`, REP 105 context) | One time is enough for most systems; extra axes burden queries | high (collapse) / medium (reference systems) | Clock alignment representation |
| **AD6** | Gaps and continuity | No continuity by default; **persistence policies** per module and kind giving **PRESUMED** answers; **observed absence** via coverage records | Probe P1B-C: strict semantics leave the present UNKNOWN (V); Khronos detects removal on revisit (V) | Policies reintroduce exactly the assumptions we wanted to avoid | high (need) / low (defaults) | Default policies per kind; coverage granularity |
| **AD7** | Identity | Minted referents; sensor ids are observations with `refers-to` claims; reviewable `same-as`; **no transitive auto-merge**; type only by **robust coarse kind** | `Detection3D.id` optional and per-detector (V); no re-typing in TypeDB (P1B-B, V); DOLCE classification (V) | Coarse typing loses schema checking | high | Merge thresholds; human review load |
| **AD8** | Uncertainty | Separate **belief confidence** (on claims) from **measurement uncertainty** (on measurements); keep competing hypotheses | vision_msgs carries several scored hypotheses each with covariance (V) | Two notions double the attributes | high | Calibration of model scores |
| **AD9** | Perspectives | No privileged "reality"; the system is one agent; CONTESTED only within a perspective; cross-perspective disagreement kept | KnowRob's `agent` and BELIEF operators (V); GUPI's semantics (V) | Applications want one answer | medium-high | — |
| **AD10** | Profiles | Extend only at **declared extension points**; core-protection tests; removal is a migration | Profiles can alter core types (P1-10, V); profile roles can't be removed once used (P1B-D, V); no namespaces (P1-4, V) | Extension points will be wrong in advance | medium | Naming convention |
| **AD11** | Method | **Specification-first:** store-independent spec + executable competency suite; TypeDB is one implementation | Needed to separate ontology from database effects (04 §4.2, I) | Doubles implementation work | medium-high | Spec format (Markdown + JSON proposed) |
| **AD12** | Baselines | **A** event log + dictionary; **B** PostgreSQL 18 temporal implementing the same spec; **C** TypeDB; RDF export for interoperability | PostgreSQL 18 enforces non-overlapping valid time (V); RDF 1.2 triple terms at CR (V) | RDF (approach 2) is the more natural semantic baseline | medium | **Your approval** to download PostgreSQL 18 and use it as a comparator |
| **AD13** | Evaluation | Seven hypotheses with explicit failure conditions (04 §4.3); sealed, independent and held-out sets; preregistration | GUPI's lesson: developer-written results were never independent (V) | Independent authors may not be found, as with GUPI | high (design) / low (staffing) | Who authors the withheld sets; thresholds |
| **AD14** | First integration | **ROS 2 Lyrical in Docker, headless Gazebo Jetty + TB3 sim**, after a one-day environment trial; consume Hydra/Khronos-style outputs, don't rebuild them | All packages verified for arm64 (V); simulator gives independent ground truth (I) | Docker on a Mac may be too slow for Gazebo; KnowRob+SOMA already serves robotics | medium | **Your approval** for image downloads (~2-3 GB, A) |
| **AD15** | GUPI | Measure **answer correctness** on LongMemEval (independent gold) under four conditions, within the subscription; parity separately | LongMemEval MIT (V); GUPI never measured answers (V) | Chat memory is where structure already failed to help retrieval | medium | Scale under $0 budget; who spot-checks |
| **AD16** | TypeDB version | Run Phase 2 on **3.14.2** (released 2026-11-04, V) after re-running all probes; record differences | Newer patch release exists (V) | Other projects here pin 3.14.1 | medium | — |
| **AD17** | Struct values | **Don't depend on structs**; coordinates as attributes | No insert syntax accepted in 3.14.1 (P1B-A, V) | A later release may fix it | high | Re-test on 3.14.2 |

## Phase 1 decisions mapped
| Phase 1 | Status after 1B |
|---|---|
| D1 repository and visibility | Decided: public (2026-11-09) |
| D2 name | Open. Prior art makes "semantic world model" acceptable; avoid "universal" (AD1) |
| D3 foundational stance | Refined into AD2 + AD3 |
| D4 every fact a claim | Refined into AD4 |
| D5 licence | Open. Reuse constraints found: DUL CC BY 4.0, BFO CC BY 4.0, SOMA LGPL-3.0, SUMO GPL with attribution (V). Apache-2.0 + CC BY 4.0 remains compatible with mapping to DUL and BFO (I) |
| D6 annotators | Refined into AD13 (and simulator truth in AD14) |
| D7 ROS 2 environment | Refined into AD14 |
| D8 outage spool | Open, unchanged |
| D9 GUPI | Changed: answer-quality test proposed (AD15), not parity only |
| D10 scope | Unchanged: three synthetic + ROS 2; plus two held-out domains (AD13) |

## Decisions needed from you before Phase 2
1. AD1: accept the narrowed research claim.
2. AD2-AD10: accept the revised core semantics (02 §2.9).
3. AD11-AD13: accept specification-first, the three baselines and the hypotheses. **Set the thresholds.**
4. AD12, AD14: approve, or refuse, the PostgreSQL and ROS 2 downloads.
5. AD13: who authors the withheld sets.
6. AD15: whether the GUPI answer test runs, and when.
