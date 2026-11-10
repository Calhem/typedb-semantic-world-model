# Core 0.4 Stage C: qualities, measurements and agency (LABS-1.016, LABS-1.017)

**Status (2026-11-10): C1 implemented on `feature/core-0.4-c-qualities-agency`; D-C-2 (how a measurement result is
tied to its supporting attestation) is under review (LABS-1.017). C2 is written but not integrated. Not merged; Stage
D not started.** Base: `main` at 8963734.

## C0: architecture review (no foundational change)
| Need | v0.2 / plan | Representation |
|---|---|---|
| a quality and its identity | v0.2 §3.3, clarification C | the slot (bearer, quality kind) of `has-quality`; no quality particular is minted (a profile may add one) |
| quality kinds, dimensions | §3.3 | `quality-kind` concept, now owning `dimension` |
| units and comparable quantities | §3.3; plan Stage C | `unit` reference system owning `dimension`, `si-factor`, `si-offset`; reported content stored in the dimension's SI unit |
| measurement activity | plan 9.2 (DX-2 amended) | an event description classified `measurement` (operator: actor, bearer: patient, instrument: instrument), optionally describing an `occurrence` |
| measurement result | plan 9.2 | an `information-object` (the result record) owning raw value, standard uncertainty, coverage factor, conditions and calibration reference; `expressed-in(record, unit)` for its raw unit |
| reported content | §3.3, plan 9.2 | `has-quality` range [v − ku, v + ku] in SI with its coverage level, attested by the source with basis observation |
| links | plan 9.2 | `produced(activity, result)` and `reports(result, content)`, ordinary attested propositions |
| comparability | v0.2 clarification B | possibly compatible / incompatible / incomparable with the reason; never reconciled |
| capabilities, roles | plan 9.5 (DX-3) | `capability` concepts and `social-role` concepts held through `classified-as(holder, concept, context?)` (C2) |
| agency | v0.2 §3.1 | the category `agent`, a classification, not a type; checked in report mode (DX-5) (C2) |

Measurement, observation, assertion and acceptance stay separate:
- a **measurement** has a result record and an activity;
- an **observation** is the basis of an attestation;
- a **statement** with no result record (a specification) is listed apart and never compared with measurements;
- **acceptance** is per perspective.

## Decisions
| # | Decision | Status |
|---|---|---|
| D-C-1 | Raw value, raw unit (`expressed-in`), standard uncertainty, coverage factor, conditions and calibration reference are intrinsic attributes of the result record; conversions are derived; the reported content is in SI | **provisionally approved (LABS-1.017)** |
| D-C-2 | Associating a reported-content attestation with the result record(s) behind it | **under review (LABS-1.017):** the C1 implementation matches by source and activity start, which is a heuristic; see the proposal below |

## C1 (implemented)
- **Schema:** module `core-0.4-c`, file `schema/core/core-0.4-c1.tql`. Installed by `QUALITY_MODULES` (opt-in).
- **API** (`src/worldmodel/qualities.py`):
  - reference data: `define_unit`, `define_quality_kind`, `si_unit`;
  - `convert` (refused across dimensions);
  - `measure`: refuses a unit of the wrong dimension, writes the activity, record, content and links, and takes an
    optional `supersedes` for corrections;
  - `measurements`: every stated value, with judgement and provenance, kind measurement or statement;
  - `compare_measurements`.
- **Laboratory reference world** (`src/worldmodel/examples/lab.py`, `build_lab`):
  - two analysts and three balances, with readings in kg and in g;
  - an external lab's unaccepted result;
  - a result at 35 °C, and one at k = 3;
  - a specification;
  - a later correction.
- **Tests:** `tests/test_i_c1_measurements.py`, 10. Full suite: 242 passed on each path.
