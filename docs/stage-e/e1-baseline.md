# Stage E1 baseline (LABS-1.051)

**Recorded 2026-11-20 on `main` `6364fdf`** (the merge of DI-13 and schema export format 3; tree `445ca80`, identical
to the validated branch head `215d4ec`). Working branch: `feature/stage-e1-benchmark`. Nothing here changes code or
semantics.

## 1. Versions
| Item | Version |
|---|---|
| TypeDB server | CE 3.14.1 (`typedb/typedb:3.14.1@sha256:d39d4f29eb57...`), container `wm-typedb`, 127.0.0.1:1735 |
| Python / driver | 3.13.17 / typedb-driver 3.14.0 |
| Core modules (all installed in new databases) | `core` 0.3.0, `core-0.4-a0` 0.4.0-a0, `core-0.4-a` 0.4.0-a1, `core-0.4-a2` 0.4.0-a2, `core-0.4-b` 0.4.0-b, `core-0.4-c` 0.4.0-c, `core-0.4-d` 0.4.0-d, `core-0.4-event-roles` 0.4.0-er, `core-0.4-event-multiplicity` 0.4.0-mp |
| Profiles (code version; upgrade chain) | mechanical 0.3 (0.1, 0.2); organisation 0.3 (0.1, 0.2); laboratory 0.2 (0.1) |
| Schema export | writes `wm-schema-export/3` (format 2 on request where representable); reads formats 1, 2, 3; exporter `worldmodel.schema_export 1.0.0` |
| Reference export | `docs/schema/`: 114 types, 78 roles, 2 functions, 519 facts, attribution verified |

## 2. Regression baseline
| Baseline | Value | Where |
|---|---|---|
| Test suite | **689 tests**, passing in all four configurations (WM_SELECTIVE 1/0 × WM_PROFILES 0/1) at `45f6712`; `main` differs from it only in documentation | [multiplicity-increment/suite-matrix-format3.out.txt](../core-0.4/multiplicity-increment/suite-matrix-format3.out.txt) |
| 106,752 reader answers | identical across the DI-13 upgrade and the export change on `wm-probe-pre-e-mp-u` | [multiplicity increment report](../core-0.4/pre-e-multiplicity-increment.md), 6.4 and 12 |
| 398 occurrence views | frozen `probes/pre_e_d_occurrence_baseline.json.gz`: 0 field, 0 judgement changes; 8 presentation changes | the same, 6.3 |
| Query counts | readers 13,597 queries / 1,820 transactions (234 calls); 398 views 34,477 queries; Core 0.3 workload 13.5 / 9.4 per question | the same, section 7 |
| Kept reference databases | `wm-probe-pre-e-mp-u` (old-built, upgraded), `wm-probe-pre-e-mp-new` (new-built), `wm-probe-pre-e-d`, `-d-u`, `-d-new`, `-d-x`, `wm-reference-*` | TypeDB server |

The baselines are **not re-frozen** here: LABS-1.048 item 4 (Stage E entry validation: re-freezing, two suite runs,
DI-9 reassessment, budgets) is a separate step. Stage E1 adds files only; it changes no existing test or baseline.

## 3. Semantics in force (the specification the benchmark is written against)
- World Ontology v0.2 ([architecture/world-ontology-v0.2.md](../architecture/world-ontology-v0.2.md)), frozen
  2026-11-09: content, attestation, acceptance, evidence, answers; statuses (section 5.6); worlds, knowledge time and
  perspectives (section 6).
- Core 0.3 deviations D1 to D14 ([core-0.3/README.md](../core-0.3/README.md)): notably D1 (no OBSERVED or PRESUMED:
  observation-based claims are ASSERTED), D4 (mixed support labelled STIPULATED > ASSERTED > INFERRED), D5 (ended
  intervals), D8 (no derivations), D14 (supersession per perspective).
- Pre-Stage E decisions: increment A (one operation per write, DI-8), B (one canonical judgement per content: rule
  over polarity, nearest world, functional slots, attested constraints), C (aggregation rule Q, `support`), D (event
  roles ER-1 to ER-8), identity ID-1 to ID-9, multiplicity MP-1 (as restricted) to MP-5, the `move()` refusal, schema
  export format 3.

## 4. Public reasoning API (readers)
Signatures and the first paragraph of each documentation string, as the code states them (writers, schema setup and
unit helpers omitted).

| Reader | Documented semantics |
|---|---|
| `WorldModel.actions_of(world, agent, as_of=None, perspective='system')` | Event descriptions in which `agent` is the actor and that are classified as actions, for the perspective. (v0.2 also requires the actor's agent capacity; capacities are Stage C, so this lists the classification.) |
| `WorldModel.agency_report(world, as_of=None, perspective='system')` | Diagnostic (DX-5, report mode): sources of attestations in `world` that the perspective does not accept as agents at the time they recorded them. Nothing is rejected or changed; Core 0.3 behaviour is unaffected. |
| `WorldModel.before(world, a, b, as_of=None, perspective='system')` | Temporal succession of two descriptions: True if a certainly ends before b starts, False if b certainly before a, None if they overlap or cannot be ordered. Succession says nothing about causation. |
| `WorldModel.capable(world, holder, capability, t, context=None, as_of=None, perspective='system')` | Does `holder` hold `capability` at t, in `context` (or in general when context is None)? A general holding (no context) applies in every context; a contextual one only in its own. Holdings that apply only in other contexts are listed in `only_in`; every applic |
| `WorldModel.causes_of(world, effect, t, as_of=None, perspective='system', _memo=None)` | Every causal claim about what caused `effect` (an occurrence or an event description), judged for the perspective. Claims stated about the effect itself are direct; claims stated about another description of the same happening (or about the occurrence a descri |
| `WorldModel.changes(world, subject, t1, t2, as_of=None, perspective='system')` | State transitions of `subject` whose valid time intersects (t1, t2], judged for the world, perspective and knowledge time (LABS-1.015 contract). |
| `WorldModel.check_action(world, event, capability=None, context=None, as_of=None, perspective='system')` | A structured check of an event description as an action, for the perspective. Reports separately: whether its account is accepted (and its occurrence interval), its kinds (is it classified `action`), the occurrences it is accepted as describing and their own s |
| `WorldModel.compare_measurements(world, bearer, quality, t=None, as_of=None, perspective='system')` | Compare the measurements the perspective accepts (v0.2 clarification B). Each pair is "possibly compatible" (comparable and the ranges overlap: one value could explain both, which is not agreement), "incompatible" (comparable and disjoint) or "incomparable" (d |
| `WorldModel.composition(world, whole, t, as_of=None, perspective='system')` | The part-of tree under `whole` at t: {"id", "parts": [subtrees], "not_traversed"} from the direct parts established at t. `not_traversed`: direct parts whose part-of content is disputed at t, each with its status, support, assertions, denials and conflicts; th |
| `WorldModel.descriptions(world, occurrence, as_of=None, perspective='system')` | Event descriptions that the perspective accepts as describing `occurrence` (or anything accepted as the same occurrence). Without such links a description describes no known occurrence. |
| `WorldModel.direct_dependencies(world, dependent, t, as_of=None, perspective='system')` | What `dependent` directly depends on at t, one entry per dependency content that holds (or is disputed): dependee, kind (a category id, or "unspecified" when the content names none), status and support. Asserted dependencies only: nothing is inferred (no trans |
| `WorldModel.effects_of(world, event, t, as_of=None, perspective='system')` | The effects claimed for an event description: for each initiates / terminates claim, who claims it and the perspective's judgement of the claim (accepted, unreviewed, rejected, denied, disputed), and separately the judged state of the outcome just before the e |
| `WorldModel.events(world, participant=None, as_of=None, perspective='system')` | Event descriptions whose occurrence is usable for the perspective, ordered by start window. |
| `WorldModel.evidence_of(attestation)` | The result records an attestation rests on (rests-on links; D-C-2). Structural: not judged. |
| `WorldModel.exists(world, thing, t, as_of=None, perspective='system')` | ASSERTED/STIPULATED from existence attestations (before creation and after destruction: false); INFERRED true if the thing takes part in content holding at t; otherwise UNKNOWN, or NOT_YET_KNOWN. |
| `WorldModel.explain(world, type, roles, t, as_of=None, perspective='system')` | Why does a content hold at t? The judged answer; the events claimed to have initiated it that ended by t, with each claim's judgement; and for each such event, the causal claims about it (causes_of, on its description and on the occurrences it is accepted as d |
| `WorldModel.facts_about(world, subject, t, as_of=None, perspective='system')` | Every content (other than events and identity links) involving the subject that holds or is disputed at t, from the canonical judgement (DI-1, LABS-1.038). Each entry: type, roles, params, `judgement` (established or disputed), `status` (DISPUTED for a dispute |
| `WorldModel.frame_info(world, frame, t, as_of=None, perspective='system')` | What is known about a spatial frame at t: its name, what it is attached to, its transforms to parent and child frames (as stored: translation and rotation), and the things positioned in it. |
| `WorldModel.history(world, subject, type=None, as_of=None, perspective='system')` | Every visible attestation involving the subject (identity-aware), oldest first, with its acceptance state for the perspective and whether it has been superseded. |
| `WorldModel.holds(world, type, roles, t, as_of=None, perspective='system')` | Does this content hold at t for the perspective? Evidence-backed status with polarity: the canonical judgement (`judgement`) as an Answer. |
| `WorldModel.identity(world, as_of=None, perspective='system', ids=None)` | Identity closure for the perspective. With `ids`, only same-as links touching the growing group are loaded. |
| `WorldModel.interval(world, description, as_of=None, perspective='system', _memo=None)` | The occurrence interval given by an attestation of the description that the perspective can use (start Window, end Window, record), or None. An unaccepted account's times are never used for a judgement. |
| `WorldModel.judgement(world, type, roles, t, as_of=None, perspective='system', attested=True, _memo=None)` | The canonical judgement (a ContentJudgement) of the content holds() asks about: `type` or a subtype, with the given players among its own. Nothing recorded at all: UNKNOWN with reason no_evidence. attested False: only declared constraints apply (how an atteste |
| `WorldModel.materials(world, thing, t, as_of=None, perspective='system', material='material', report=False)` | The material categories the thing is classified under at t: classes that are themselves classified as `material` (decision D-A1-1), both classifications established. Materials are categories, not types. report True: {"materials": the same ids, "disputed": clas |
| `WorldModel.occurrence(world, occurrence, as_of=None, perspective='system')` | A merged view of an occurrence. Conflicts stay visible and traceable; nothing is merged in storage. |
| `WorldModel.occurrence_status(world, occurrence, t, as_of=None, perspective='system', details=True, _memo=None)` | Whether the occurrence happened, for the perspective (LABS-1.011): judged only from attestations of its own existence (existence(existent: occurrence)), never from accepted descriptions, describes links or causal claims. `status` is accepted, denied, disputed  |
| `WorldModel.occurrences_of(world, description, as_of=None, perspective='system', _memo=None)` | The occurrences a description is accepted (by the perspective) as describing. |
| `WorldModel.parts(world, whole, t, as_of=None, perspective='system', report=False)` | Transitive parts at t (application closure over the part-of content established for the perspective). report True: {"reached": the same ids, "not_traversed": the part-of links from reached things that were not followed (disputed, pending or unknown at t), each |
| `WorldModel.poses(world, thing, t, as_of=None, perspective='system')` | The thing's positions that hold at t, one per frame statement: frame, per-axis (lower, upper), orientation, status and supporting attestations. Several positions in one frame are all listed (conflicts between positions are not judged in A1). |
| `WorldModel.process_steps(world, process, t, as_of=None, perspective='system')` | The occurrences accepted as part of a process occurrence at t, ordered by their descriptions' intervals, each with its descriptions, interval, kinds and actors (from the perspective's accepted descriptions), and the judgement and status of its part-of content: |
| `WorldModel.roles_of(world, holder, t, as_of=None, perspective='system')` | The social roles `holder` is accepted as holding at t, each with its context. |
| `WorldModel.transform_between(world, source, target, t, as_of=None, perspective='system', limit=None)` | How `source` frame coordinates map into `target` at t: {"status", "transform" (q, t) or None, "chain" (the shortest chain, each step with its direction and supporting attestations), "frames", "reason", "search"}. INFERRED from the transforms that hold for the  |
| `WorldModel.value_at(world, type, subject, t, as_of=None, perspective='system', key_role=None, value_role=None)` | The value(s) of a relationship for `subject` at valid time t, for a perspective, as known at `as_of`. |
| `WorldModel.value_of(world, type, key, t, as_of=None, perspective='system')` | The value(s) in a functional slot at t: `key` names a player for every key role of the type's slot, e.g. value_of(w, "seat-assignment", {"venue": "hall", "seat": "A1"}, t) -> the occupant (A0.3). |
| `WorldModel.where(world, thing, frame, t, as_of=None, perspective='system', angle_tolerance=1e-09, limit=None)` | The thing's position in `frame` at t, judged (A2, LABS-1.008). Every position statement that holds for the perspective is a candidate: stated in `frame` (direct), or mapped into it through the shortest frame chain (derived, INFERRED, citing the position and ev |
| `mechanical.replacement(wm, world, event, t, as_of=None, perspective='system')` | Report a replacement description for the perspective, concluding nothing beyond it: - the account: accepted or not, its interval, the removed and fitted parts it names; - the occurrences it is accepted as describing, each with its own status (not the account's |
| `organisation.office_holders(wm, world, office, context, t, as_of=None, perspective='system')` | Who holds `office` in `context` at t, for the perspective. - appointments: every appointment content for this office and context, each with its own judgement and evidence (established, denied, expired, not yet effective, disputed, not established); - holders:  |
| `organisation.offices_of(wm, world, person, t, as_of=None, perspective='system')` | Every office appointment naming `person`, each with its own judgement and evidence at t. An established appointment to an exclusive office that others also hold at t is DISPUTED, with the conflict cited. No entry means no evidence either way (never a denial). |
| `organisation.official_act(wm, world, event, power=None, as_of=None, perspective='system')` | Report an official act for the perspective, as separate fields, concluding nothing beyond them: account (accepted or not, interval); occurrences with their own status; at the act's start: the official's office appointment (its judgement, and DISPUTED with the  |
| `laboratory.calibration_status(wm, world, instrument, t, as_of=None, perspective='system')` | Is `instrument` calibrated at t, for the perspective? holds / status / judgement as capable() (established, expired, denied, disputed, not yet effective, not established; no new statuses; combined over the certificates by rule Q, with the deciding claims in `s |
| `laboratory.provenance(wm, world, sample, t, as_of=None, perspective='system')` | Where `sample` came from, for the perspective at t, as separate fields that conclude nothing beyond them: - chain: every constitution content met by following "constituted from" links back from `sample`, each once (the sample, what it is said to be made from,  |
| `organisation.authorised(wm, world, holder, power, scope, t, as_of=None, perspective='system')` | Is `holder` authorised to exercise `power` within exactly `scope` at t (D-D-4: no containment)? holds / status / judgement as capable(), combined over the grants by rule Q; grantor_entitlement: always "not assessed" (D-D-3). |

## 5. Unresolved correctness and performance issues (register)
| Issue | Status |
|---|---|
| DI-3 conflicting mechanical joint kinds not judged | open (limitation) |
| DI-4 dependency-kind vocabulary not validated | open (limitation) |
| DI-7 no formal derivation provenance (rule and premises), yet basis inference gives INFERRED | open: Stage E requirement |
| DI-9 performance: high query counts in reports, cross-world slowdown; `occurrence()` about 4.4x | open (performance), into Stage E |
| DI-10 no automated browser tests for the schema explorer | open (maintenance) |
| DI-14 variant world lists descriptions whose account is not inherited | open (reporting; deferred) |
| DI-17 conflict-group identity (ID-5) may be over-restrictive | open: Stage E evaluation |
| DI-18 export omits module data the replay does not reproduce | open (non-blocking) |
| ID-10 (descriptions by canonical describes judgement), TI-1 derived marker | deferred, need approval |
| destination and product single-valued (several aliquots) | deferred to a later design (LABS-1.048) |
| P-1 thresholds not demonstrable (selective median, p95, ingest; CV) | from the LABS-1.047 gate; entry checks |
