# 6. Architectural decision register (updated for Phase 1C)

Supersedes the status column of Phase 1B's [register](../phase-1b/06-decision-register.md), which is kept unchanged.
Status: **approved** (by the owner), **provisional** (approved in principle), **proposed** (awaiting approval),
**open**.

| ID | Decision | Status | Phase 1C change | Confidence | Open question |
|---|---|---|---|---|---|
| AD1 | Narrowed research claim; no novelty for KnowRob-demonstrated capabilities | **approved** | KnowRob comparison made concrete (02 §2.8) | high | — |
| AD2 | Minimal core aligned to DUL | provisional | — | medium | mapping test method |
| AD3 | 3D endurants, time on relations | provisional | — | medium-high | — |
| AD4 | Fact relation is the claim; static facts declared | provisional | — | high | per-profile evidence policy |
| AD5 | Three time dimensions + clock domains | provisional | **formalised**: clocks, alignments, bound windows, transaction-time knowledge states (02 §2.1) | high | alignment representation |
| AD5a | Map-frame corrections | **proposed** | new: sensor-frame observations, derived map poses citing the estimate version, re-derivation with supersession (02 §2.1) | medium | map-version correspondence |
| AD6 | Persistence | provisional | **formalised**: answer statuses; policy fields; lifecycle (begin, renew, expire, defeat, dispute); computed at query time, never stored (02 §2.2-2.3) | high (structure) / low (default horizons) | horizons per kind |
| AD6a | Observed absence | **proposed** | new: coverage, target kinds, reliability, weak vs strong negatives, interaction table (02 §2.4) | medium | coverage granularity |
| AD7 | Identity | provisional | **formalised**: minting rule, unresolved observations, accepted-only transitive closure, splitting (02 §2.5) | high | merge review load |
| AD8 | Confidence | provisional | **revised**: four quantities (model score, measurement uncertainty, credence on attribution, derivation strength); calibration rule (02 §2.6) | high | calibration data sources |
| AD9 | Perspectives | provisional | — | medium-high | — |
| AD10 | Profiles at extension points | provisional | — | medium | naming convention |
| AD11 | Specification-first | **approved** | — | medium-high | spec format |
| AD12 | Baselines A / B (PostgreSQL 18) / C (TypeDB) | **approved** | B must encode unknown ends explicitly (environment smoke test) | high | — |
| AD13 | Evaluation design | provisional | contributions separated, ablations, capability attribution (04) | high (design) | **thresholds** (proposed in 04 §4.4); **withheld authors** (05) |
| AD14 | ROS 2 environment | **approved and installed** | Lyrical + Gazebo Jetty + Nav2 verified; image 7.4 GB | high | real robot hardware for latency targets |
| AD15 | GUPI answer baseline | **approved**; free stages run | no existing LongMemEval answer evaluation in GUPI; claims absent on this dataset (03) | high | **paid stage approval** |
| AD16 | TypeDB version for Phase 2 | proposed | unchanged: re-run probes on 3.14.2 before Phase 2 | medium | — |
| AD17 | No struct values | proposed | unchanged | high | — |
| AD18 | Answer statuses (OBSERVED, ASSERTED, INFERRED, PRESUMED, DISPUTED, UNKNOWN, NOT_YET_KNOWN) | **proposed** | new (02 §2.2); replaces GUPI's TRUE/FALSE/... set for the core | medium-high | whether INFERRED splits by rule type |
| AD19 | Thresholds | **proposed** | new (04 §4.4) | medium | approval, then freeze |
