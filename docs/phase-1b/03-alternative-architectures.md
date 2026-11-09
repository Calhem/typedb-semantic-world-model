# 3. Alternative architectural approaches and trade-offs

Labels: **V** verified (see [01-literature-review.md](01-literature-review.md)), **I** interpretation, **A** assumption.

## 3.1 The approaches
| # | Approach | Ontology | Store and reasoning |
|---|---|---|---|
| 1 | **Use KnowRob + SOMA** for robotics; add only what's missing | SOMA on DUL (OWL) | KnowRob hybrid KB: Prolog, RDF (Redland), MongoDB (V) |
| 2 | **Standards stack in RDF** | Minimal core aligned to DUL; SOSA, PROV, OWL-Time; SHACL for constraints | RDF 1.2 triple store (e.g. Oxigraph, Apache-2.0, V) |
| 3 | **Relational temporal** | The same minimal core as tables | PostgreSQL 18 with `WITHOUT OVERLAPS` temporal keys (V) |
| 4 | **Bitemporal property graph** | Ad hoc, LLM-extracted | Graphiti on Neo4j / FalkorDB / Neptune (V) |
| 5 | **Virtual knowledge base** | Any | Facts computed on demand from live robot data, no persistent copy (KnowRob 2.0's main idea, V) |
| 6 | **Phase 1 proposal** | Minimal core, aligned | TypeDB 3.x |
| 7 | **Specification-first (recommended)** | Minimal core defined independently of any store, with an executable competency-question suite | TypeDB is the *first* implementation; approach 3 is the strong baseline; RDF export for interoperability |

## 3.2 Trade-offs
| | 1 KnowRob+SOMA | 2 RDF | 3 SQL temporal | 4 Graphiti | 5 Virtual | 6 TypeDB |
|---|---|---|---|---|---|---|
| N-ary events with roles | yes (OWL patterns) | verbose (n-ary pattern) | join tables | weak (binary edges) | depends | **native** (P1-1) |
| Facts about facts (evidence, belief) | modal operators (V) | RDF 1.2 triple terms (CR, V) | link tables | edge attributes | — | **native** (P1-2) |
| Schema enforcement | open-world OWL (infers, doesn't reject) | SHACL | strong | weak | — | strong (P1-3,4,5) |
| Valid-time integrity | intervals (V) | manual | **temporal keys enforced by DB** (V) | bitemporal (V) | none | manual in queries (P1B-C) |
| Temporal reasoning location | Prolog | SPARQL + app | SQL + app | app | app | TypeQL functions possible (P1B-C) |
| Standards interoperability | high (OWL) | **highest** | low | low | — | low (no RDF import/export) |
| Footprint on a robot | heavy (A) | small, embeddable (A) | medium server; SQLite option (A) | server + LLM | smallest | server, ~0.2 GB+ (V) |
| Maturity and tooling | research, robotics | high | **highest** | product | research | medium |
| Fit beyond robotics | low (I) | high | high | chat only | robotics only | high |
| Licence | BSD-3 / LGPL-3 (V) | Apache-2.0 (V) | PostgreSQL licence (A) | Apache-2.0 (V) | — | MPL-2.0 (V) |

## 3.3 Assessment
- **Approach 1 is the strongest robotics-only option.** If Experiment R shows that a ROS 2 team only needs robotics,
  KnowRob/SOMA should be recommended over building our own. The research only justifies itself if the
  *cross-application* sharing (robot ↔ video ↔ memory) delivers something.
- **Approach 3 is the strongest general baseline.** It is a competent typed temporal representation with
  database-enforced valid-time integrity, which TypeDB does not have. If TypeDB cannot match it on correctness at
  a comparable cost, the case for TypeDB here fails.
- **Approach 2 is the interoperability benchmark.** Whatever we build should export to it, and losses should be
  measured.
- **Approach 4** is a reference point for agent memory only, not a baseline for the core.
- **Approach 5 is a design lesson, not a competitor.** Don't copy into the semantic layer what ROS can compute on
  demand (current poses, reachability). Persist only what must outlive the live data: history, provenance, beliefs,
  identities.

## 3.4 Recommendation: approach 7, specification-first
1. Write the core as a **store-independent specification**: concepts, roles, time semantics and answer semantics
   in prose and tables, with a DUL mapping.
2. Make the **competency-question suite** the executable definition: fixtures, questions, expected answers and
   required evidence, in a neutral format (JSON).
3. Implement it **twice**: C in TypeDB, B in PostgreSQL 18. A (event log + dictionary) is the floor.
4. Export C to RDF to measure interoperability loss.

**Evidence:** separating specification from implementation is the only way to tell what the ontology contributes
from what the database contributes (section 4 of [04-evaluation-protocol.md](04-evaluation-protocol.md)). It also
stops the ontology being bent around TypeDB features (2.8).

**Strongest counterargument:** two implementations double the work for a small team, and a store-independent spec
gives up TypeDB-specific expressiveness, which is the thing we want to test. Mitigation: B implements only what
the competency questions need, not a full product. Expressiveness is measured as query and schema size per
question, so TypeDB gets credit where it is genuinely more direct. Confidence: **medium-high**.

**Approval needed:** B needs a PostgreSQL 18 Docker image (a download). The "TypeDB is the only database" rule
belongs to the explorer project (its ADR 0001), not to this repository. Using another database here as a research
comparator still needs your explicit agreement.
