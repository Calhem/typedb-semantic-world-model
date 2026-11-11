# Core 0.4 Stage C: qualities, measurements and agency (LABS-1.016 to LABS-1.020)

**Status (2026-11-11): Stage C ontology and API approved (LABS-1.020); full `measure()` atomicity implemented; merged
into `main` after validation (see the merge record at the end). Stage D not started.** Base: `main` at 8963734.

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
| D-C-1 | Raw value, raw unit (`expressed-in`), standard uncertainty, coverage factor, conditions and calibration reference are intrinsic attributes of the result record; conversions are derived; the reported content is in SI | **approved (LABS-1.020, with the Stage C design)** |
| D-C-2 | Each measurement-backed attestation names its own result record(s) through the structural link `rests-on(attestation, record)` (Option A below). No matching by source, time or content; immutable; no one-to-one constraint; it records evidential dependency, not truth or occurrence; `produced` and `reports` keep their meanings | **approved (LABS-1.018), implemented** |
| D-C-3 | Capability reporting: `capable()` keeps the core judgement (`holds`, `status`, no new statuses) and adds `judgement` (established, denied, expired, not yet effective, disputed, not established) | **approved (LABS-1.020)** |
| D-C-4 | An expired capability keeps `holds=False` with `judgement="expired"` (as `holds()` treats any ended fact) | **approved (LABS-1.020)** |
| D-C-5 | UNKNOWN (something is held, but nothing applicable: only elsewhere, unreviewed or rejected) and NOT_YET_KNOWN (nothing at all) stay distinct | **approved (LABS-1.020)** |
| D-C-6 | Batching of measurement reads is deferred (N+1 reads accepted for now) | **approved (LABS-1.020)** |
| D-C-7 | Measurement conditions are compared as exact text: conservative (any difference is incomparable) and documented | **approved (LABS-1.020)** |
| D-C-8 | `measure()` is fully atomic: activity and account, result record with its original value, unit, uncertainty, conditions and calibration reference, content attestation, `rests-on`, `produced` and `reports` commit together in one transaction with one transaction time, or nothing does | **required (LABS-1.020), implemented** |

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
- **Tests:** `tests/test_i_c1_measurements.py` (10) and `tests/test_i_c1b_provenance.py` (22, D-C-2 regressions
  and failure injection).

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

## Atomicity (LABS-1.019, LABS-1.020)
**Transaction boundary (D-C-8).** `measure()` opens one write transaction (`WorldModel._batch()`) and writes into it,
in order:
1. the activity's event description (`describe_event`);
2. its account attestation and its `measurement` classification (`account`), plus a `describes` claim when an
   occurrence is given;
3. the reported content proposition, if new, and the content attestation (with a `supersession` link when
   correcting);
4. the result record, with its raw value, unit (`expressed-in`), standard uncertainty, coverage factor, conditions and
   calibration reference;
5. `rests-on(attestation, record)`;
6. the `produced` and `reports` propositions and attestations.

It commits once. Every attestation in it has the same `recorded-at`, so a knowledge-time (`as_of`) query sees all of
the measurement or none of it.

**Mechanism (the smallest one).**
- A `_Batch` holds the transaction and its transaction time.
- `describe_event`, `attest` and `account` accept an optional `batch` parameter: they then write into that transaction
  and do not commit. Without it they behave exactly as before.
- `measure()` is the only caller. It is not a general transaction API, and no other write API changed.
- The reported content's id is derived from its canonical key (A0.1), so `reports` can name it before it is committed.
- Proposition identity, attestation identity, supersession and knowledge-time semantics are unchanged.

**Failure injection** (`tests/test_i_c1b_provenance.py`):
- `test_measure_is_atomic_at_every_stage` injects a failure at each write stage in turn:
  - activity description, activity account, activity classification;
  - content proposition, content attestation;
  - result record, `rests-on`, `produced`, `reports`;
  - the final commit.
- Each case checks that the failure hit exactly that stage. It then checks that no event, attestation, record,
  `rests-on` link or proposition was added and that neither measurement id exists, and that the next measurement
  succeeds.
- `test_attest_evidence_failures_roll_back` covers `attest()` with evidence directly:
  - a failing record writer;
  - a missing record, which before LABS-1.019 committed the attestation without its link;
  - an unknown attester.
- `test_a_measurement_has_one_transaction_time` checks that the five attestations of one measurement share one
  recorded-at. Querying at that time shows it with its record and activity; one microsecond earlier shows none of it.

## C2: capabilities, contextual roles and agency (implemented)
- **Schema:** `schema/core/core-0.4-c2.tql` in module `core-0.4-c`: `entity capability sub concept;` (nothing else;
  holdings reuse the core `classified-as(classified, class, context?)`).
- **API** (`src/worldmodel/agency.py`, `AgencyMixin`):
  - `define_capability`; `grant(world, holder, concept, context=None, polarity=True, ...)` attests a capability, role
    or category holding (a denial with `polarity=False`);
  - `capable(world, holder, capability, t, context=None, as_of, perspective)`;
  - `is_agent` (agency = the category `agent`, a classification); `roles_of` (social roles with their contexts);
  - `check_action(world, event, capability=None, context=None, ...)`: reports the account's acceptance and interval, its
    kinds, the occurrences it is accepted as describing with **their own** status, and each actor's agency and
    capability at the event's start, separately; it concludes nothing;
  - `agency_report`: diagnostic only (DX-5 report mode), sources not accepted as agents; nothing is rejected.
- **Semantics preserved:**
  - agency is a contextual classification; a balance can have a capability without agency; an apprentice can be an
    agent with a role and without the capability;
  - a capability does not establish an action (the inspector can sign off and has no action that day);
  - participation does not establish capability (Tom's accepted log of weighing gives him no capability);
  - roles are contextual (analyst in lab-1; fitter in the workshop);
  - an accepted account of an action does not establish its occurrence (`check_action` reports the occurrence's own
    status: `o-bearing-replacement` is "not established" although the work log is accepted; Tom's log claims none).
- **Capability judgement (LABS-1.019).** `holds` and `status` are the core judgement; no status was added.
  `judgement` names the case:

  | judgement | holds | status | when |
  |---|---|---|---|
  | established | True | ASSERTED / STIPULATED... | an applicable holding is accepted at t |
  | denied | False | ASSERTED | an accepted denial (polarity false) covers t |
  | expired | False | ASSERTED | an accepted holding ended before t and no accepted denial; as `holds()` treats any ended fact |
  | not yet effective | None | UNKNOWN | an accepted holding begins after t |
  | disputed | None | DISPUTED | accepted grant and accepted denial, or rival accepted attestations |
  | not established | None | UNKNOWN or NOT_YET_KNOWN | nothing applicable is accepted: no holding at all (NOT_YET_KNOWN), only unreviewed or rejected ones, or holdings only in other contexts (`only_in`) |

  Each applicable holding stays listed in `applicable` with its attestations and their acceptance states.
- **Reference worlds:**
  - lab: `lab.extend_lab_agency`;
  - workshop: `gearbox.extend_qualities_agency`, on top of `extend_dynamics`, with:
    - the housing weighed on scale-3 (kg) and scale-9 (g);
    - a technician who may replace bearings only in the workshop;
    - an apprentice who is an agent with a fitter role, but has no capability;
    - an inspector who may sign off;
    - a bearing press with a capability and no agency;
    - a plan world in which the apprentice is qualified.
- **Tests:** `tests/test_i_c2_agency.py` (17), both domains.

## Cross-domain demonstration
`scripts/show_qualities_agency.py`, output in `docs/core-0.4/qualities-agency-output.md`. The same calls (`compare_measurements`,
`convert`, `capable`, `is_agent`, `roles_of`, `check_action`, perspectives, `as_of`, hypothetical worlds) run against
both worlds, followed by raw TypeQL over `rests-on`, `produced` and the capability, role and agent grants.

## Validation (LABS-1.019)
- **Tests:** 271 in the full suite, passed twice on each query path (selective and full load), with no test
  databases left behind. Stage C: `test_i_c1_measurements.py` (10), `test_i_c1b_provenance.py` (11) and
  `test_i_c2_agency.py` (18). The last includes a build of the full chain A1 → A2 → B1 → B2 → C, which found and fixed
  a clash: the `apprentice` id was shared with B2.
- **Performance and storage:** `docs/core-0.4/bench-c/README.md`. In short:
  - no existing-query regression from Stage C code (identical query counts, latencies within noise);
  - the larger world makes some unchanged queries slower (more data per query);
  - the new measurement questions take about 100 queries, because records are loaded one at a time;
  - the Stage C extension adds +8.9% storage.

**LABS-1.020 (full atomicity).**
- 282 tests in the full suite, passed twice on each query path, with no test databases left behind.
- `test_i_c1b_provenance.py` now has 22 tests, including 10 failure-injection cases.
- The cross-domain demo is unchanged apart from random ids (and so the order within pairs).
- Write cost: `docs/core-0.4/bench-c/README.md`, last section. The atomic `measure()` is about 30% faster, with 1
  write transaction instead of 6.

## Remaining limitations
1. **Measurement reads are N+1** (D-C-6, deferred): 100 queries for the housing's 4 values, 2 of them with records.
2. **Conditions are compared as exact text** (D-C-7): no condition ontology, tolerances or units in conditions.
3. **Capabilities are not checked against actions.** `check_action` reports, never enforces. DX-5 stays in report
   mode, and `agency_report` is diagnostic only.
4. **A record without an attestation is not reported as a measurement.** `reports(result, content)` alone does not
   create one.
5. **Only `measure()` is atomic as a whole.** Other multi-step writers (`account()` alone, the reference-world
   builders) still commit step by step, as in Stage B. That is unchanged by design (LABS-1.020: no general
   transaction framework).
