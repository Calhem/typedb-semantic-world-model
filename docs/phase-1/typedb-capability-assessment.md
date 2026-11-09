# TypeDB 3.14.1 capability assessment

**Question:** does TypeDB give this project a material advantage, and where will it fight us?
Evidence comes from three sources, and each row says which one:
- **probe:** run for this assessment by `probes/typedb_capabilities.py` against a TypeDB 3.14.1 server, in throwaway
  databases (`wm-probe-*`) that were deleted afterwards. Raw output: `probes/typedb_capabilities.out.json`.
- **GUPI:** measured in ../typedb-gupi-agent-memory (final report, Phase 4 performance).
- **explorer:** the vehicle explorer (this machine's typedb-noodlelab-visual-explorer).

## Probe results

| # | What was tried | Result | What it means for the design |
|---|---|---|---|
| 1 | A profile defined in a second `define` on top of a core schema, with a relation whose roles specialise a core role (`relates picker as participant`) | accepted | Profiles can be layered additively, and domain relations can refine core roles natively. **The main structural advantage.** |
| 2 | A relation (part-of) playing a role in another relation (supported by an observation, with a confidence) | accepted | Evidence and provenance can attach to a *fact*, not just to a thing, without RDF-style reification. |
| 3 | One instance with two unrelated types (`isa physical-object, isa agent`) | **rejected** (INF11) | **No multiple classification.** Every instance has exactly one type. Anything an entity can be "also" (a role, a detector's label, a domain view) must be a relation, not a type. |
| 4 | Two profiles defining `attribute mass` with different value types | **rejected** (DEX14) | **No namespaces.** All profiles share one name space in a database. Profiles need a naming rule and a collision test. |
| 5 | An attribute owning an attribute (confidence on a measured value) | **rejected** (DEX11) | Uncertainty or units on a single value need the value to be a relation or entity (a "measurement"), which costs more concepts per fact. |
| 6 | Defining a `struct` (3D point) | accepted | Structs can be defined... |
| 13 | ...and used as an attribute value with `point3(x: ..., ...)` | rejected (syntax error) | **Inconclusive:** the literal syntax I tried is wrong or unsupported. Until shown otherwise, assume coordinates are separate double attributes. To check in Phase 2. |
| 7 | A recursive function (transitive part-of) defined by a profile | accepted, 2 rows | Profiles can ship reasoning as functions. TypeDB 3.x has no rules: functions run at query time. |
| 8 | Listing a profile's types by query (`match $t sub endurant;`) | accepted | Profile conformance can be checked by introspection, in tests. |
| 9 | Removing a profile's type again (`undefine`) | accepted (when no data uses it) | Profiles can be uninstalled from an empty database; with data, removal is a migration. |
| 10 | A profile adding a role to a *core* type (`entity endurant plays located-in:located`) | accepted | Works, but the profile **changes the core type** in that database. "Same core" must mean "core types keep their meaning", tested, not "core types are byte-identical". |
| 11 | `datetime-tz` with nanoseconds, and a `duration` | accepted | Sensor time stamps fit. |
| 12 | Ingest 2,000 small records (an observation, two objects, a part-of and a support relation: 5 concepts), 100 per transaction; 50 point lookups | **1,198 and 1,585 records/s** in two runs; lookup median 1.4-1.5 ms, p95 2.1-3.4 ms | Indicative only (one laptop, Docker, local network). Ample for semantic events (tens per second), far too slow and too heavy for raw sensor streams. |

Resource figures (explorer machine, Docker): the TypeDB 3.14.1 image is 218 MB; the explorer's server with its
vehicle model used 211 MiB of memory at rest; GUPI's server, after its research runs, 1.66 GiB. These are server
footprints before any application load, and they vary with cached data.

## What TypeDB offers that matters here

| Capability | Advantage over | Evidence |
|---|---|---|
| **N-ary relations with named roles** (an event with a picker, a picked thing, a place, an instrument) | RDF/OWL needs reification patterns for n-ary facts; property graphs flatten roles into edge properties | probe 1; GUPI claims; explorer dependencies |
| **Relations as role players** (a fact supported by evidence, a belief about a fact) | RDF-star / named graphs, or extra join tables in SQL | probe 2; GUPI review, supersession |
| **Type hierarchy with role specialisation and polymorphic queries** ("every agent", "every participation") | SQL needs hand-written unions | probe 1; explorer Types tab |
| **A checked schema** (role players, cardinality, value ranges) | OWL's open world does not reject bad data, it infers | probes 3-5 (they reject); GUPI |
| **Recursive functions** (part-of closure, dependency chains) | Recursive SQL is possible but less readable | probe 7; explorer `functions.tql` |

## Where TypeDB costs us

| Limitation | Consequence | Mitigation |
|---|---|---|
| No multiple classification (probe 3) | Clashes with ontologies like DOLCE where one thing is classified many ways | Keep types for what a thing *is* (rigid kinds); put roles, labels and domain views in relations. This is also good epistemics: a detector's "person" label is a claim, not a type |
| No namespaces (probe 4) | Profile name collisions | A naming convention and a collision test over all published profiles |
| Profiles mutate core types (probe 10) | "Shared core" is weaker than it sounds | Conformance tests that core queries give the same answers with and without each profile |
| No attribute metadata (probe 5) | Measurements with uncertainty cost a relation each | Store uncertainty only where an application uses it |
| No geometry type, spatial index, vector index or full-text index (GUPI; 3.14.1 docs) | Spatial and similarity queries run in application code or by linear scans | Keep geometry in ROS / USD / the scene system; store references and coarse regions |
| No embedded mode: a separate server process (≈0.2-1.7 GB here) | Not suitable for microcontrollers; marginal on small companion computers | Run on the robot's main computer, a base station, or remotely; measure |
| No rules (3.x): reasoning is query-time functions, much of it ends up in Python (GUPI) | Inference cost is paid per query; logic splits between TypeQL and code | Say where each step runs (the explorer already labels this) |
| No OWL / RDF import or export | Interoperability with SOSA, PROV, OWL-Time, SOMA is a mapping job, not a load | Write mappings for the few concepts we reuse, tested in both directions |
| Planner bug QPL1 (explorer) and other 3.14.1 friction (cyber-intel notes) | Some query shapes need workarounds | Keep logging friction in ../typedb-cyber-intel/notes/typedb-feedback.md |

## Honest summary
TypeDB's advantage here is **modelling fidelity**: n-ary events, facts about facts, typed roles and a checked schema
fit a world model with evidence much better than triples or tables. GUPI's final report found that this fidelity
did **not** turn into measurably better answers on chat data, and that most temporal reasoning ended up in Python.
The open question is whether it pays off where relationships are dense and explicit (robotics state, engineering
models), which GUPI marked as the most promising untested direction. This project should test exactly that, against
a simpler baseline, before claiming an advantage.
