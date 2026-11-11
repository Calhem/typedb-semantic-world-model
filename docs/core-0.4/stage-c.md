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
| D-C-2 | Each measurement-backed attestation names its own result record(s) through the structural link `rests-on(attestation, record)` (Option A below). No matching by source, time or content; written atomically with the attestation; immutable; no one-to-one constraint; it records evidential dependency, not truth or occurrence; `produced` and `reports` keep their meanings | **approved (LABS-1.018), implemented** |

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
- **Tests:** `tests/test_i_c1_measurements.py` (10) and `tests/test_i_c1b_provenance.py` (10, D-C-2 regressions).

## D-C-2 review (LABS-1.017): tying a result to its supporting attestation
### What the probe shows (`probes/core04_c_dc2_identity.py`)
| Case | C1 behaviour | Correct? |
|---|---|---|
| 1. Ana records two results at 09:00 on two balances, identical values | one content, two attestations; **each attestation is tied to both records** | no: provenance is wrong |
| 2. the same, at 20 °C and at 35 °C | each attestation carries both records, so both condition sets; comparability would mix them | no |
| 3. different values, same source and time | correct, but only because the contents differ | by accident |
| (all) | the source-and-start match needs the activity's account to be accepted by the asking perspective; otherwise it falls back silently to "content only" | no: provenance must not depend on acceptance |

**Why.** `reports(result, content)` links a record to *content*. Content is identical whenever two results state the
same thing, by v0.2's identity rule (§4.2: structural identity of what is said), so it cannot identify *which
statement* a record supports. The statement is the attestation. Nothing in C1 links an attestation to a record.

### Options
| Option | What | Assessment |
|---|---|---|
| A. **`rests-on(attestation, record)`**, a structural link in the stance layer, written in the same transaction as the attestation | each attestation names the result record(s) it rests on; immutable, like the attestation itself | **recommended.** Explicit, stable, independent of acceptance, and the "evidence → the measurement" link v0.2 §3.3 already describes for a measurement-supported proposition. It adds a relation in which `attestation` plays a role, so it is a stance-layer addition: **needs approval** |
| B. Put the record in the content: `has-quality(bearer, quality, unit, record)` | each result gets its own content | rejected: it changes proposition identity (two results stating the same value would no longer be one content, contrary to v0.2 §4.2), and every query by bearer and quality would have to ignore the record |
| C. Store the attestation id as an attribute of the record, or the record id on the attestation | a string reference | rejected as authoritative provenance: no referential integrity in TypeDB; acceptable only as a stop-gap |
| D. Keep heuristic matching (C1) | source + activity start | rejected: the probe shows it is wrong for repeated measurements |

### Correction (Option A): approved and implemented in LABS-1.018
- **Schema** (additive, module `core-0.4-c`):
  ```
  relation rests-on, relates attestation @card(1..1), relates record @card(1..1);
  attestation plays rests-on:attestation;
  information-object plays rests-on:record;
  ```
  It is structural, not a proposition, and is never attested itself. It is written by `measure()` in the same
  transaction as the content attestation, so it has that attestation's recorded time and knowledge-time visibility.
- **Provenance read.** `measurements()` follows attestation → `rests-on` → record → `produced` → activity. It no longer
  uses `reports` or any matching. `reports(result, content)` remains what the record says about the world (useful
  when a record is held but no one has attested its content). It is no longer used to find a statement's evidence.
- **Correction.** A corrected result is a new record (a record's content never changes) and a new content attestation
  that supersedes the old one, with its own `rests-on`. The superseded attestation keeps its link to the original
  record, so the history stays faithful: what was claimed, on what evidence, and when.
- **Supersession** is per perspective (D14). A perspective that has not accepted the correction keeps the original
  attestation and therefore the original record. A perspective that accepted it sees the new attestation and record.
- **Disputes.** Rival attestations, whether a polarity denial or disjoint ranges, each rest on their own records.
  Comparability then reads each attestation's own conditions and coverage, never a merged set.
- **Perspectives.** The link is a fact about an attestation (what its source said it relied on), so it is not judged.
  Which attestations count is acceptance, as now. A perspective that distrusts a record expresses that through the
  attestations: rejecting them, or a `doubts` stance. The link is never edited.
- **Hypothetical worlds.** A variant's own measurements rest on their records; inherited attestations bring their
  links. Snapshots (branch time, knowledge time) filter attestations, and the links follow them.
- **Migration.** Existing C1 data has no `rests-on`. Because C1 is unmerged, the reference worlds would simply be
  rebuilt. For a database that holds C1 data, the link can be added from `measure()`'s own records only where one
  record matches one attestation unambiguously; ambiguous ones stay unlinked and are reported.

### As implemented (LABS-1.018)
- **One link per (attestation, record) pair.** Each `rests-on` relates exactly one attestation and one record. An
  attestation may rest on several records and a record may support several attestations: there is no one-to-one
  constraint (tested).
- **Atomic.** `attest()` takes an `evidence` list of writers that run inside the attestation's own transaction.
  `measure()` uses it to write the result record, its `expressed-in` unit and the `rests-on` link together with the
  content attestation. If a writer fails, nothing is committed: no attestation, no record, no link (tested).
- **Read.** `evidence_of(attestation)` returns the linked records. `measurements()` uses only this. The C1 heuristic
  (and its `match` field) is removed.
- **Judged parts stay judged.** For each record, `report` (whether the `reports` claim is accepted) and the
  activity's times (from its account) depend on the perspective. The link, the record's values and conditions, and
  the activity's operator and instrument do not (tested).
- **Probe rerun.** `probes/core04_c_dc2_identity.out.json` (the C1 output is kept as `.before.json`): each attestation
  now names exactly its own record and conditions in all three cases.
- **Regression tests** (`tests/test_i_c1b_provenance.py`):
  - identical values on two instruments;
  - identical values at 20 °C and 35 °C (no condition leak; the pair is incomparable);
  - three results from one source at one time;
  - correction and supersession: both links kept, supersession per perspective, the `as_of` view before the
    correction;
  - disputed and unreviewed results with their own conditions;
  - perspectives;
  - hypothetical inheritance;
  - atomicity and many-to-many;
  - a link establishes neither acceptance nor occurrence;
  - selective/full-load agreement.
