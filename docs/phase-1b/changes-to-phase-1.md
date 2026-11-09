# Changes to Phase 1 findings

Phase 1 documents in `docs/phase-1/` are **kept unchanged**. This page lists every Phase 1 statement that Phase 1B
corrects, strengthens or withdraws. Where they disagree, the Phase 1B version takes precedence.

| # | Phase 1 said | Phase 1B finding | Kind | Where |
|---|---|---|---|---|
| 1 | KnowRob/SOMA/NEEMs is "the most direct prior art" for robot episodic memory | Stronger than stated: KnowRob's current C++ version implements BELIEF/KNOWLEDGE modal operators with agent perspective and confidence, plus fuzzy time intervals (source, V) | strengthened | 01 §1.2 |
| 2 | DOLCE "relies on multiple classification, which TypeDB lacks" | Wrong emphasis: DOLCE models roles and classification as a **time-indexed relation** (CF), the same pattern TypeDB forces | corrected | 01 §1.1, 02 §2.8 |
| 3 | DUL licence "CC BY (verify)" | DOLCE repository CC BY 4.0 (V); SOMA, which ships DUL.owl, is LGPL-3.0 (V) | verified / added | 01 |
| 4 | BFO "CC BY 4.0 (verify)" | Verified in the BFO-2020 README | verified | 01 |
| 5 | SUMO "free; IEEE-owned, GPL tooling (verify)" | Repository: GNU GPL with an attribution request; website: free, owned by IEEE | verified, sharpened | 01 |
| 6 | SOMA licence "(verify)" | LGPL-3.0; already modular (12 OWL modules incl. a USD ontology) | verified / added | 01 |
| 7 | "No embedded mode" for TypeDB | Not re-checked; still from knowledge (A) | unchanged, flagged | verification-status (Phase 1) |
| 8 | A contingent fact costs "about 4-5 concepts instead of 1 edge" | Overstated: the fact relation **is** the claim (as in GUPI). Minimum is 1 relation + time attributes; evidence and attribution add 1 each when used | corrected | 02 §2.3 |
| 9 | Five times (valid, event, observation, recorded, belief) | Three primitives plus optional result time, each with a time reference system | revised | 02 §2.5 |
| 10 | "Absence is not falsity" and no invented continuity, with a profile-level presumption as an aside | Insufficient: strict semantics leave the present UNKNOWN (probe P1B-C). Persistence policies and **observed absence (coverage)** are needed in the core | revised | 02 §2.6 |
| 11 | `quantity-kind` / measurement "with optional uncertainty" | Belief confidence and measurement uncertainty must be kept separate | revised | 02 §2.6 |
| 12 | Struct values "inconclusive" | Three literal syntaxes rejected in 3.14.1: treat as unusable for stored values | resolved | probes |
| 13 | Profile removal "is a migration" (from probe 9, empty database) | Verified with data: removing a profile's role from a core type is rejected while data uses it (SVL51) | verified | probes |
| 14 | Baseline B0 = JSON log + dictionary | Now baseline **A**; adds strong baseline **B** (PostgreSQL 18 temporal, same specification) | revised | 04 |
| 15 | Experiment 5 (GUPI): parity only | Answer-correctness test on LongMemEval proposed, plus parity | revised | 05 §5.6 |
| 16 | ROS 2: "Jazzy or the 2026 LTS"; Mac support uncertain; message facts unverified | Lyrical Luth (LTS to 2031) verified; macOS Tier 3; arm64 Tier 1 in Ubuntu 26.04 containers; package availability, REP 105, tf2 10 s cache, MCAP default, `Detection3D` and `NavigateToPose` verified | verified / revised | 05 §5.1 |
| 17 | Spatial claims store "poses in map frame" | `map` poses jump on relocalisation: store the frame and estimate, allow supersession | revised | 05 §5.2 |
| 18 | Six-module, three-profile structure | Kept, with declared extension points and core-protection rules | refined | 02 §2.7 |
| 19 | Probe 12 throughput "1,198 and 1,585 records/s" | Unchanged; still indicative (two runs, one laptop) | unchanged | — |
