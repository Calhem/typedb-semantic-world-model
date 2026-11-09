# 4. Revised evaluation protocol and baseline definitions

This replaces Phase 1's [experiment-protocols.md](../phase-1/experiment-protocols.md) as the proposal for review.
The Phase 1 file is kept unchanged. The three invented scenarios and 22 competency questions are re-classed as
**development material**: useful for building, never evidence of generalisation.

## 4.1 The three approaches compared
| | A. Minimal baseline | B. Strong baseline | C. Proposed |
|---|---|---|---|
| Representation | Append-only JSON event log + a current-state dictionary | The same ontology specification as relational tables: one table per claim type, valid time as a range with `WITHOUT OVERLAPS` keys, transaction-time columns, evidence and attribution link tables | The same specification as modular TypeDB schema |
| Store | Files + Python | PostgreSQL 18 (needs approval to download) | TypeDB 3.14.x |
| Reasoning | Python | SQL (views, recursive CTEs) + Python | TypeQL functions + Python |
| Built by | Same team, honest effort, time-boxed | Same team, **competent** effort: indexes, constraints, a reviewed schema | Same team |

**Fairness rules.** B and C implement the **same specification and the same answer semantics** (three-valued
answers, persistence policies, observed absence). Each gets the same time box. Each is reviewed once for obvious
inefficiency before the sealed run. A is deliberately naive, but it must answer every question it can.

## 4.2 What we are trying to separate
Every result is attributed to one of three sources by **ablation**, not by opinion.

| Comparison | Isolates |
|---|---|
| A vs B | the value of a **typed ontology and temporal model** (B and C share it; A doesn't) |
| B vs C | the value of **TypeDB** as the store, with the ontology held constant |
| C with TypeQL functions vs C with the same logic in Python | what the **database reasoning** contributes inside C |
| Per question: which layer produced each part of the answer (schema, database query or function, application code) | a **capability matrix**, published with the results |

## 4.3 Hypotheses, success criteria and failure conditions
Thresholds are proposals for you to set before any run. "Points" are percentage points of correct answers on the
sealed set, with 95% paired bootstrap intervals.

| H | Hypothesis | Success | Failure (published as such) |
|---|---|---|---|
| H1 | A typed ontology improves historical and provenance answers over a naive log | B and C beat A by ≥ 10 points on the temporal, identity and provenance families, interval above 0 | A within 5 points of both: **the ontology adds nothing measurable** |
| H2 | TypeDB is at least as correct as a strong relational baseline | C ≥ B − 2 points on every family | C < B − 2 on any family: **TypeDB is worse** |
| H3 | TypeDB makes the model materially simpler to express and keep valid | C needs ≥ 30% less query and schema text per question than B, **and** rejects ≥ as many invalid writes (schema violation suite) | No difference: **no expressiveness benefit** |
| H4 | The cost is acceptable | C's p95 latency ≤ 2× B and ≤ the application budget (ROS: 50 ms proposed); storage ≤ 3× B; ingest ≥ the application's semantic event rate × 10 | Any bound exceeded: **too costly for that use** |
| H5 | One core serves different domains | The core is unchanged across ≥ 2 held-out domains; module-only additions | A core change that alters an existing concept's meaning: **portability fails** |
| H6 | Profiles exchange knowledge without silent loss | Every dropped or transformed fact is reported; round-trip preserves ≥ 95% of the answers to shared-type questions | Any silent loss, or < 80%: **interoperability fails** |
| H7 | No invented continuity | 0 unsupported definitive answers (TRUE/FALSE given where the gold says UNKNOWN or needs a PRESUMED label) in C | Any: **the core semantics are not delivered** |

Because B is a real competitor, **C can lose on H2, H3 and H4 and the protocol says so.** If C loses H2 or H4
while A loses H1, the result is "the ontology is useful, TypeDB is not the right store for it". That is a valid
and publishable outcome.

## 4.4 Data: development, withheld and independent
| Set | Author | Use | Sealed? |
|---|---|---|---|
| **Dev** | the implementer (W, S, L, M; the 22 Phase 1 questions plus 2.x examples) | building and debugging | no |
| **Withheld synthetic** | a separate author who never sees the implementation, writing from the specification only (a person; or a blind model session in a **fresh** app session, given the GUPI lesson that subagents inherit memory) | final scoring | yes, hashed and committed before implementation |
| **Simulation ground truth** | the simulator's own state (ROS 2: Gazebo model poses, spawned or removed objects, scripted events); preregistered *which* fields count as truth | robotics scoring | the scenario scripts are written before the adapter |
| **External annotated** | existing datasets with gold answers: **LongMemEval** (memory; MIT licence, V) for answers; **Action Genome** (video; repository MIT, V; the underlying Charades video licence is A) for spatio-temporal relations | memory and video scoring | not used in development |
| **Held-out domains** | at least two domains chosen **after the core is frozen**, by you: candidates are vehicle maintenance (from the explorer model, as input data) and a domain neither of us has discussed | H5 | chosen late |

**Minimum sizes (proposal):** 120 scored questions per family on sealed sets (enough for an interval of about ±9
points at 50% accuracy). Fewer, if you accept wider intervals, but the report states them.

## 4.5 Question specification (every scored item)
```json
{"id": "W-T-014", "family": "temporal-gap", "world": "actual", "perspective": "robot",
 "question": "Where was obj-box-1 at 2026-11-09T10:15:00Z?",
 "answer": {"value": "PRESUMED", "binding": {"place": "dock"}, "policy": "static-object-persistence"},
 "required_evidence": ["obs-881"], "forbidden_evidence": ["obs-640"],
 "notes": "last seen at dock 10:12; no later observation of the dock"}
```
**Scoring per item:** answer value correct (TRUE/FALSE/UNKNOWN/NOT_YET_KNOWN/CONTESTED/PRESUMED); binding correct;
evidence precision and recall against `required_evidence`; **unsupported assertion** if a definitive value is
given without the required evidence, or where the gold is UNKNOWN. Plain-text explanations are not scored here.

## 4.6 Test families
| Family | Cases (each in W, S, L, M where meaningful) |
|---|---|
| **Temporal continuity** | gaps; observed absence vs not observed; reappearance; reinstatement of a past relation; presumption expiry; map-frame relocalisation jumps (ROS) |
| **Identity** | track id reuse; empty tracker ids; split and merge; reappearance after occlusion; same name, different people (M); new entity from a sampling event (L) |
| **Uncertainty** | competing classifications with scores; measurement covariance vs belief confidence; low-confidence claims excluded or included by policy |
| **Conflicting beliefs** | within-perspective contradiction (CONTESTED); cross-perspective disagreement preserved; a belief later corrected (belief time vs valid time) |
| **Provenance** | every claim traceable; retraction of an observation and what changes; derived claims' chains |
| **Schema validity** (H3) | 50 invalid writes (wrong role player, missing time bound, a value out of range, a duplicate key); count which each of B and C rejects |

## 4.7 Portability and information loss
- **Schema portability:** core changes per held-out domain (by kind: additive, meaning-changing); module types added;
  CQs answered without new core concepts.
- **Information loss:** export each profile's data to another profile and to RDF (DUL-aligned). Re-run the
  shared-type questions; loss = answers changed or lost. Every dropped fact is listed by category.
- **Specification loss:** facts in the spec that B or C cannot represent, counted.

## 4.8 Cost measurements (all three approaches, same machine, same data)
Schema size (types, attributes, functions, lines); concepts and bytes per fact (on disk, after a checkpoint);
ingest rate at 1×, 10×, 100× the application rate; p50 and p95 latency per question family, warm and cold; server
and client memory (RSS) and CPU; start-up time. Each figure reports runs, machine and spread. Single runs are
labelled indicative.

## 4.9 Process
1. Preregister hypotheses, thresholds and sets (hashes) in a commit **before** implementation of B and C.
2. Build on dev; freeze; run sealed sets once; publish everything, including failures.
3. Any later change to thresholds is a new, labelled preregistration. Old results stay.
