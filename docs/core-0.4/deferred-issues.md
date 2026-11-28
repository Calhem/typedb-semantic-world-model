# Deferred correctness issues (register)

**Opened 2026-11-11 under LABS-1.025; DI-5 added under LABS-1.026, DI-6 under LABS-1.027, DI-7 under LABS-1.028, DI-8 and DI-9 under LABS-1.030, DI-10 and DI-11 under LABS-1.034, DI-12 under LABS-1.038, DI-14 under LABS-1.042, DI-13 under LABS-1.043, DI-15 and DI-16 under LABS-1.045, DI-17 under LABS-1.049, DI-18 under LABS-1.050, DI-19 under LABS-1.053, DI-20 to DI-23 under LABS-1.059, DI-24 to DI-36 under LABS-1.064.** The pre-Stage E consolidation ([pre-stage-e-consolidation.md](pre-stage-e-consolidation.md), LABS-1.045, at review) recommends a disposition for every open issue. These are known correctness issues (DI-1 to DI-8, DI-11), one
tracked performance concern (DI-9) and one maintenance item (DI-10), kept apart from the stage documents.
None of them has had its semantics changed yet. The pre-Stage E correctness review
([pre-stage-e-correctness-review.md](pre-stage-e-correctness-review.md), LABS-1.034) reproduces DI-1 to DI-6 and DI-8,
widens the scope of DI-5 and DI-8, and found DI-11.

- **DI-1**, **DI-2**, **DI-6** and **DI-8** must be **reviewed before Stage E** (final validation); DI-1, DI-2 and
  DI-8 must be resolved.
- **DI-7** is a general semantic requirement to be designed **in Stage E**.
- **DI-9** is a performance concern tracked **into Stage E**.
- **DI-3**, **DI-4** and **DI-5** are accepted limitations until a decision says otherwise.
- **DI-10** is non-blocking maintenance. **DI-11** (found by the review) is proposed for review before Stage E.
- **DI-12** (found in the increment B design) is registered and deferred: no deadline, correction not scheduled.
- **LABS-1.049:** DI-12, DI-15 and DI-16 are **closed** (identity increment merged, `main` `dd58b25`). **DI-17** (possible
  over-restriction of conflict-group identity) is registered for **Stage E evaluation**. ID-10 and the TI-1 `derived`
  marker stay deferred (see DI-17).
- **LABS-1.050:** DI-13 is **closed** (multiplicity increment, with schema export format 3, approved and merged into
  `main`). **DI-18** (module data the replay does not reproduce is absent from the export) is registered.
- **LABS-1.053:** the Stage E1 reconciliation (R1 to R4, including `UnknownRoleError` for invalid role names) is
  approved and merged into `main`. **DI-19** (a constraint dispute through `holds()` does not cite the constraint's
  attestation) is registered as a Stage E issue; its correction is not implemented.
- **LABS-1.059 (performance phase closure):** DI-9's corrections O-1, O-2, O-3 and F6 are approved (F6 under
  LABS-1.059; DI9-D11, the `where` target, closed). The residual performance items are registered as **DI-20 to
  DI-23**, deferred, with no optimisation scheduled. See
  [stage-e-performance-closure.md](../stage-e/stage-e-performance-closure.md).
- **LABS-1.060:** the performance closure is approved, and DI-20 to DI-23 stay deferred.
  - **DI-19:** implemented as the additive `Answer.constraint_support` (branch `feature/di19-constraint-support`, at
    review).
  - **DI-17:** evaluation only, through about 12 E2 identity-conflict questions; identity semantics unchanged.
  - **DI-7:** deferred until after E2. Derivation questions are E2 gap probes.
  - Decisions are recorded in [stage-e2-decisions.md](../stage-e/stage-e2-decisions.md).

- **LABS-1.064 (E2 semantic decision closure):** DI-24 to DI-30 (from the E2 contract adjudication) and DI-31 to
  DI-36 (implementation consequences of the 25 approved semantic decisions) are **registered, not implemented**.
  **DI-25 and DI-28 are critical architectural priorities.** E2 questions on them stay eligible where the reader
  provides the capability, and are G probes where it does not (decision record:
  [stage-e2-semantic-decisions.md](../stage-e/stage-e2-semantic-decisions.md)). Each entry separates reproduced
  defects, inspection-only findings and newly established requirements.
Each entry gives a concrete case, what it affects, and the options. A resolution needs its own approved decision and
tests.

| # | Issue | Found | Must be resolved | Status |
|---|---|---|---|---|
| DI-1 | disputed content omitted from generic fact and role reports (`facts_about`, `roles_of`) | D-1 (LABS-1.023) | before Stage E | corrected in increment B, approved and merged (LABS-1.039, `main` d9d873a) |
| DI-2 | conflicting event participants are not judged together (single-valued roles) | D-1 (v0.2 D9) | before Stage E | corrected in increment D, approved and merged (LABS-1.045, `main` 9464403); residual: DI-15 |
| DI-3 | conflicting mechanical joint kinds are not judged | D-1 | no deadline | open (limitation) |
| DI-4 | dependency-kind vocabulary is not validated | D-1 | no deadline | open (limitation) |
| DI-5 | a future-effective appointment (or holding) with an unreviewed counter-claim is labelled "not established" | D-2 (LABS-1.026) | no deadline | corrected in increment B, approved and merged (LABS-1.039, `main` d9d873a) |
| DI-6 | aggregate organisational reports can return ASSERTED despite mixed constituent statuses | D-2 (LABS-1.026) | review before Stage E | corrected in increment C, approved and merged (LABS-1.041, `main` bf8bb34) |
| DI-7 | formal derivation provenance: no record of a named rule and named premises, yet basis "inference" gives INFERRED | D-3 (LABS-1.027 G-1, LABS-1.028) | Stage E requirement | open (deferred until after E2; LABS-1.060) |
| DI-8 | `take_sample` (and `replace_part`) write an account and its claimed effects in separate transactions | D-3 (LABS-1.028; registered LABS-1.030) | before Stage E | corrected in increment A, approved and merged (LABS-1.037, `main` 7654587) |
| DI-9 | performance: high query counts in the D-3 reports, and questions slowing as other worlds' data grows | D-3 benchmark (LABS-1.029; registered LABS-1.030) | tracked into Stage E | corrected (O-1, O-2, O-3, F6; LABS-1.056 to 1.059); residuals in DI-20 to DI-23 |
| DI-10 | the schema explorer has no automated browser regression tests (search, filters, navigation were checked by hand) | LABS-1.024 gate (registered LABS-1.034) | no deadline (maintenance) | open (non-blocking) |
| DI-11 | reports built on `_claims` (capable, the profile reports) ignore functional-slot conflicts; the mirror image of DI-1 | pre-Stage E review (LABS-1.034) | proposed: before Stage E | corrected in increment B, approved and merged (LABS-1.039, `main` d9d873a) |
| DI-12 | the transitive traversals (`parts`, `dependencies`) judge their links without the perspective's same-as identity | increment B design (LABS-1.037, registered LABS-1.038) | before Stage E (LABS-1.046) | **closed**: corrected by the identity increment (ID-8), approved and merged (LABS-1.049, `main` dd58b25; [report](pre-e-identity-increment.md)) |
| DI-13 | every event role holds at most one player per account (TypeDB's default `@card(0..1)`), a universal per-account cardinality the domain does not always have | increment D design (LABS-1.041; registered LABS-1.043, ER-8) | before Stage E (LABS-1.046) | **closed**: corrected by the multiplicity increment (MP-1 as restricted, MP-2 to MP-5, the `move()` origin defect) with the four approved additions and schema export format 3; approved and merged into `main` (LABS-1.050; [report](pre-e-multiplicity-increment.md)) |
| DI-14 | in a variant world, descriptions whose account is not inherited are listed (their `describes` link is) without saying the world holds no account of them | increment D design (registered LABS-1.042) | no deadline (deferred) | open (reporting; no judgement affected) |
| DI-15 | an occurrence's aliases (accepted same-as) are listed in `occurrence()` but their accounts are never compared, so two names of one occurrence give different role judgements | consolidation (LABS-1.045) | before Stage E (LABS-1.046) | **closed**: corrected by the identity increment (ID-9), approved and merged (LABS-1.049, `main` dd58b25; [report](pre-e-identity-increment.md)) |
| DI-16 | identity merges on a same-as whose canonical judgement is DISPUTED (accepted denials are ignored) | consolidation (LABS-1.045) | before Stage E (LABS-1.046) | **closed**: option (a), corrected by the identity increment (ID-2, ID-5, ID-6), reproduction a permanent test; approved and merged (LABS-1.049, `main` dd58b25; [report](pre-e-identity-increment.md)) |
| DI-17 | a group of names joined by established same-as links that contains one disputed or denied pair is not merged at all (ID-5), so its established equivalences are set aside too: possibly over-restrictive | identity increment (LABS-1.048; registered LABS-1.049) | Stage E evaluation | open (evaluation only in E2; LABS-1.060) |
| DI-18 | the export's `module_data` lists only the records the replay reproduces: a record held by a module version this code cannot replay is absent from the export (the attribution reports the replay as unverified) | schema export format 3 (LABS-1.050) | no deadline (export completeness) | open (non-blocking; format 2 refusal already reads the database's own records) |
| DI-19 | `holds()` on a content disputed under an attested constraint (two holders of an exclusive office) cites the content's support and its rivals (`conflicts`), but not the attestation of the constraint it applied | Stage E1 revised evaluation, ORG-011 (LABS-1.052; registered LABS-1.053) | Stage E (provenance) | **closed** (additive `constraint_support`, LABS-1.060; merged LABS-1.061) |
| DI-20 | readers that still load a whole world (`occurrence_status`, `causes_of`, `effects_of`, `provenance`) grow with perspectives | DI-9 closure (LABS-1.058; registered LABS-1.059) | no deadline (DI9-D17 deferred) | deferred (performance) |
| DI-21 | H1: transient slow states between fresh processes, cause unknown | DI-9 optimisation (LABS-1.056; registered LABS-1.059) | no deadline | deferred (performance) |
| DI-22 | cross-world growth in head and parameter fetches (`where` +3.2 ms from 11 to 92 worlds; `parts`, `office_holders`) | DI-9 closure (LABS-1.058; registered LABS-1.059) | no deadline | deferred (performance) |
| DI-23 | performance depends on TypeDB 3.14.1's planner; the first query after a bulk load may not finish | F6 (LABS-1.058; registered LABS-1.059) | recheck on any TypeDB upgrade | deferred (engine; private handover at review, DI9-D18) |
| DI-24 | subject-keyed readers (`where`, `poses`, `measurements`) ignore the subject's same-as group | E2 contract adjudication (LABS-1.063; registered LABS-1.064) | after E2 baseline | open, high (not implemented) |
| DI-25 | a derived pose can be INFERRED from a disputed position premise; a truncated search through a disputed transform returns a transform | E2 contract adjudication (LABS-1.063; registered LABS-1.064); SD-SPA-3 | after E2 baseline | open, **critical architectural priority** (not implemented) |
| DI-26 | accepted denials of measured content are not judged; the measurement `t` filter drops the other side of a dispute | E2 contract adjudication (LABS-1.063; registered LABS-1.064); SD-MEA-1 | after E2 baseline | open, high (not implemented) |
| DI-27 | value readers answer for roles that form no declared slot; `value_at` does not separate dispute sides; `key_role` without `value_role` is not refused | E2 contract adjudication (LABS-1.063; registered LABS-1.064); SD-CORE-2 | after E2 baseline | open, high / medium (not implemented) |
| DI-28 | causal claims lift through missing or disputed describes links and do not cite the links; effect claims and `changes` explanations carry no occurrence applicability | E2 contract adjudication (LABS-1.063; registered LABS-1.064); SD-CAU-9 | after E2 baseline | open, **critical architectural priority** (not implemented) |
| DI-29 | provenance completeness: dispute sides, initiating claims, transition sides, alternatives, listing constraint support, explanation attestations | E2 contract adjudication (LABS-1.063; registered LABS-1.064); SD-CORE-3, SD-CAU-2, SD-CAU-4 | after E2 baseline | open, medium (not implemented) |
| DI-30 | measurement reporting: (a) canonical units, (b) the calibration reference check when the activity has no accepted time | E2 contract adjudication (LABS-1.063; registered LABS-1.064) | after E2 baseline | open, medium; parts a and b independently testable (not implemented) |
| DI-31 | `holds()` matches a subset of roles and picks the first record in load order, instead of addressing exact content | E2 semantic decisions (LABS-1.064), SD-CORE-1 | after E2 baseline | open, medium (not implemented) |
| DI-32 | frame-chain answer conventions: chain tolerance not reported, identity presented as a premise-less derivation, NOT_YET_KNOWN never given, count-based `where` label | E2 semantic decisions (LABS-1.064), SD-SPA-1, -2, -4 | after E2 baseline | open, medium (not implemented) |
| DI-33 | an explicit instantaneous measurement holds at no instant: the writer cannot represent an instant (representation and migration) | E2 semantic decisions (LABS-1.064), SD-MEA-2 | after E2 baseline | open, high (not implemented) |
| DI-34 | calibration is judged at the earliest bound of an uncertain activity start, not throughout the window | E2 semantic decisions (LABS-1.064), SD-MEA-6 | after E2 baseline | open, medium (not implemented) |
| DI-35 | `effects_of`, `explain` and `changes` do not follow the approved change, inclusion, timing and claim-time semantics | E2 semantic decisions (LABS-1.064), SD-CAU-1, -2, -7, -8 | after E2 baseline | open, high (not implemented) |
| DI-36 | temporal ordering under uncertainty: instantaneous events in `before`; one account picked by id instead of every account | E2 semantic decisions (LABS-1.064), SD-CAU-5, -10 | after E2 baseline | open, medium (not implemented) |

## DI-1: `facts_about` omits content disputed by polarity
**What happens.** `facts_about(world, subject, t)` lists only content whose judgement at t is "holds". Two kinds of
conflict are treated differently:
- **Functional conflict** (two places in a one-place slot): both contents hold, and both are listed as DISPUTED. This
  is correct.
- **Polarity conflict** (one source asserts a content, another denies the same content, and the perspective accepts
  both): the content's judgement is "disputed", not "holds", so it is **left out**.

**Concrete case** (`tests/test_k_d1_mechanical.py`, perspective test):
- the technician asserts `depends-on(gear-out, bearing-2, functional)`, and the inspector denies it;
- once the system accepts the denial, `holds()` says DISPUTED, but `facts_about(gear-out)` no longer mentions the
  dependency at all.

**Affected.**
- **Readers built on `facts_about`:**
  - `roles_of` (agency.py), so a disputed role silently disappears;
  - `process_steps` (dynamics.py);
  - `poses` and `frame_info` (physical.py).
- **Not affected (they already list disputed items as DISPUTED):** `holds`, `value_of`, and the D-1 reports
  `direct_dependencies` and `connections`, which read the per-content judgement.
- **D-2 relevance:** an appointment disputed by a denial would vanish from `roles_of`.

**Options.**
- **(a)** `facts_about` lists polarity-disputed content with status DISPUTED, citing both sides. This changes core
  answers: any test or demo with an accepted denial changes.
- **(b)** Keep `facts_about` as "what holds", and add a separate general reader for "what is disputed". Every caller
  then has to choose.
- **(c)** Leave as is, and document per API.
- **Recommendation:** (a), with an inventory of changed answers before approval. Silent omission conflicts with v0.2
  §5.3 ("never silent").

**Correction, increment B (LABS-1.038), approved and merged (LABS-1.039, `main` d9d873a).** Made on
`feature/pre-e-b-canonical-judgement`: one canonical
per-content judgement for every reader; DI-1: every listing reader lists polarity-disputed content as DISPUTED, citing both sides ([pre-e-increment-b.md](pre-e-increment-b.md)).

## DI-2: conflicting accounts of single-valued event participants
**What happens.** v0.2 §3.2 (D9) says that roles a profile declares single-valued for an event kind make different
players DISPUTED in the merged view of an occurrence. This is not implemented: `occurrence()` unions the participants of
all usable descriptions.

**Concrete case** (gearbox D-1 world):
- the maintenance system's replacement account names removed = bearing-1, and the inspector's names removed =
  bearing-2;
- both describe `o-bearing-replacement`;
- if one perspective accepted both accounts and both links, the occurrence's removed part would be reported as
  {bearing-1, bearing-2}, not as DISPUTED.

**Affected.**
- the merged occurrence view (`occurrence`, `descriptions`);
- `replacement` (it reports per account, so it is correct per description but has no occurrence-level judgement);
- D-2 official acts: two accounts of one act naming different officers.

**Options.**
- **(a)** Single-valued event roles as metadata, like functional slots (`declare_single_valued(event type, role)`),
  judged in the merged occurrence view, with DISPUTED and both accounts cited.
- **(b)** Defer. This would block Stage E.
- **Recommendation:** (a). It reuses the slot-as-data pattern (A0.3) and needs no schema change.

**Increment D design (LABS-1.041), at review.** [pre-e-increment-d-design.md](pre-e-increment-d-design.md). Two of
this entry's premises were corrected while preparing it:
- each event role already holds **at most one player per account** (TypeDB's default `@card(0..1)`), so several
  players of a role arise only across accounts of one occurrence, and a two-part job can only be recorded that way;
  whether a replacement's `removed` is single-valued therefore depends on the operation (proposed: constrained only for
  occurrences established as one-for-one; proposed DI-13 for the per-account cardinality);
- the review's reference count (bearing-1 against bearing-3 at `o-bearing-replacement`) merged two different roles
  under the core name `patient`: the CMMS replacement's removed part and the technician's work-log patient. Measured on
  the reference worlds, the proposed rule changes no judgement (`probes/pre_e_d_impact.out.txt`).

**Correction, increment D (LABS-1.043), validated under LABS-1.044, approved and merged (LABS-1.045, `main`
9464403).** Made on `feature/pre-e-d-event-roles` under the
approved design (ER-1 to ER-8): event-role constraints stored as data (`core-0.4-event-roles`), declared by profiles
(official-act official, office and office context; replacement removed and fitted only for an occurrence established
as `mechanical:one-for-one`), judged in `occurrence()` (new fields `accounts` and `roles`) by the canonical mechanism
([pre-e-increment-d.md](pre-e-increment-d.md)). Validation: the 106,752 answers unchanged by the new code and by the
upgrades (and old code on an upgraded database); the 398 views with 0 changes to existing fields or judgements and the
8 authorised role-presentation additions; the full suite twice in four configurations.

## DI-3: conflicting mechanical joint kinds
**What happens.** `connected-to(a, b, bolted)` and `connected-to(a, b, welded)` are two contents. Both can hold, so they
are never in conflict.

**Example:** the design office says the cover is bolted to the housing, and a later inspection says it is bonded. Both
are reported, and neither is DISPUTED.

**Options:**
- a functional slot keyed by the endpoint pair with value joint-kind, which needs slot support for a multi-player key
  role (not verified);
- or accept that parts can have several joints (often true: bolted *and* sealed).
- **Current:** accepted limitation. The profile documents it.

**Consolidation (LABS-1.045): the mechanism exists.** Declared in a probe database only, a slot keyed by the two
endpoints (`declare_slot("connected-to", ["endpoint"], "joint-kind")`, one role played twice) makes "bolted" against
"pressed" for one pair DISPUTED (`probes/pre_e_consolidation.out.txt`). What remains is the domain choice (whether a
pair has one joint kind), to be made in the mechanical profile if a scenario needs it. Recommended: close with evidence.

## DI-4: dependency-kind vocabulary is not validated
**What happens.** Any category can be a dependency's `kind`. The core seeds four (`dependency:physical`, `functional`,
`informational`, `control`), but `depend(..., kind="steel")` is accepted.

**Options:**
- mark kinds by classification, `classified-as(k, dependency-kind)` (as materials are marked), and check them on
  write;
- or accept an open vocabulary.
- **Current:** accepted limitation (open vocabulary, documented).

## DI-5: a not-yet-effective holding is labelled by a pending counter-claim
**What happens.** The shared per-content label (`_holding_label`, from `capable()`) ranks attestation states
(unreviewed, rejected...) before "not yet effective". An accepted appointment or capability that begins after t is
therefore reported "not established" instead of "not yet effective" whenever an unreviewed claim exists for the same
content.

**Concrete case** (Acme world): on day 5, Cal's site-manager appointment (accepted, from day 8) shows "not established",
because the auditor's unreviewed denial ranks first.

**Why not fixed in D-2.** The label is shared with `capable()`, whose answers had to stay identical (LABS-1.026
equivalence test).

**Option:** rank "not yet effective" before attestation states when an accepted attestation begins after t. This changes
`capable()` answers in such cases, and needs a decision and an updated baseline.

**Wider scope (LABS-1.034 review).** The same label falls back to "not yet effective" for *any* accepted content that is
undecided at t, including one that has begun but whose end is unknown (no invented continuity): an accepted holding
from day 1 with no stated end is reported "not yet effective" on day 5. See the review, DI-5.


**Correction, increment B (LABS-1.038), approved and merged (LABS-1.039, `main` d9d873a).** Made on
`feature/pre-e-b-canonical-judgement`: one canonical
per-content judgement for every reader; DI-5: an undecided content is labelled by why it is undecided, and pending counter-claims never outrank an accepted claim ([pre-e-increment-b.md](pre-e-increment-b.md)).

## DI-6: aggregate reports can return ASSERTED despite mixed constituent statuses
**What happens.** `organisation.office_holders` reports one overall status for the office. When the established
holders have different support statuses, it returns ASSERTED, and only the per-holder statuses tell the truth. The
same can arise wherever a report folds several judged contents into one status.

**Concrete case:** a hypothetical plan stipulates a second holder of a non-exclusive office whose first holder is
inherited from the actual world. The holders are then ASSERTED (inherited) and STIPULATED (the plan's), and the office
is reported as ASSERTED overall.

**Affected:** `office_holders` (overall `status`); any future aggregate report.

**Options:**
- **(a)** A defined aggregation rule, for example "the weakest standing among the constituents", or a status set rather
  than one value.
- **(b)** Report no overall support status, only per-constituent statuses, plus DISPUTED/UNKNOWN as appropriate.
- **(c)** Keep it, and document.
- **Recommendation:** (b) for support statuses. It removes a summary that can mislead, and keeps DISPUTED, UNKNOWN and
  NOT_YET_KNOWN, which are well defined for the set. To be reviewed before Stage E. Semantics unchanged until decided.

**Correction, increment C (LABS-1.040), awaiting review, not merged.** Made on `feature/pre-e-c-aggregate-status`
under the approved design ([pre-e-increment-c-design.md](pre-e-increment-c-design.md), C-1 to C-6): one question
answered by several holdings (`capable`, `authorised`, `calibration_status`) takes the core rule over the union of the
deciding claims (rule Q, listed in a new `support` field); `office_holders` reports no status of its own when holders
are established without conflict (rule C, option (b) above); a `changes` slot state rests on the values held, as
`value_of` ([pre-e-increment-c.md](pre-e-increment-c.md)).

## DI-7: formal derivation provenance is not recorded
**What happens.** v0.2 (E6) reserves derived answers (INFERRED) for attestations derived under a **named rule** from
**named premises**. The model records neither. Any attestation written with basis `inference` is reported INFERRED
by the core judgement, whether or not a rule produced it. `rests-on` records evidence (premises, in effect), but not a
rule.

**Concrete case** (`tests/test_n_d3_laboratory.py`, `test_interpret_refuses_basis_inference_and_flags_it_where_recorded`):
lab 2's conclusion "sample 12 is anhydrous", written directly with basis `inference` and accepted, is INFERRED. That
is an analyst's conclusion, not a formal derivation.

**What D-3 does (D-D3-4, LABS-1.028), without changing the core:**
- the profile's writing function, `laboratory.interpret`, records an interpretation as **testimony**, or as a
  **hypothesis** (stance `hypothesises`), and refuses basis `inference`;
- the profile's report, `laboratory.interpretations`, flags any attestation with basis `inference` as "recorded as
  inference without derivation structure". Every row carries the note that no formal derivation is recorded;
- the core judgement is unchanged (it still says INFERRED).

The convention is not enforced outside the laboratory profile.

**Affected.** Every reader that reports INFERRED from an attestation's basis (`holds`, `value_of`, and everything
built on `_claims`). This does not include the Core 0.3 existence inference (`exists`: INFERRED from participation in
holding content), which is a rule the model applies itself.

**Options (Stage E):**
- (a) a derivation record: an attestation names its rule (a concept) and its premises (attestations). Only such
  attestations are reported INFERRED; others with basis `inference` are reported as testimony;
- (b) refuse basis `inference` on write unless a derivation record is given;
- (c) keep it as documentation only.

Recommended: (a), with (b) as its write-time check. No inference engine is implied: derivations would be recorded,
not computed.

## DI-8: `take_sample` is not atomic
**What happens.** `laboratory.take_sample` writes the `sampling` account, then each claimed effect (`initiates
existence(sample)`, `initiates constitution(sample, specimen)`) in its own transaction, as `mechanical.replace_part`
does. If a write fails part-way, the database keeps an account with fewer claimed effects than its source gave.

**Concrete case.** If the TypeDB connection drops after the account is written, Ana's sampling account for s12-a
exists with one claimed effect, or none. Nothing is judged wrongly (each claim is judged on its own, and a missing
claim establishes nothing), but the record no longer says everything the source said, and nothing marks it as
incomplete.

**Affected.** `take_sample` and `replace_part`. Unaffected: `register_certificate`, `calibrate`, `interpret` and
`measure()` (atomic since Stage C, D-C-8).

**Options:**
- (a) write the account and its effect claims in one transaction, with the `batch=` mechanism `measure()` uses;
- (b) keep separate writes, but record the intended number of claims, so an incomplete account can be reported.

Recommended: (a), applied to both functions. **Must be resolved before Stage E.** The behaviour was left unchanged
when D-3 was merged (LABS-1.030).

**Wider scope (LABS-1.034 review).**
- Core composite writers are not atomic either: `account` without a batch (up to four transactions), `record_event`,
  `create_thing` and `destroy`.
- Option (a) is not possible with today's API alone. `claim_effect` stores its outcome content in its own committed
  transaction (`WorldModel.proposition`). Inside a batch, a new outcome is not visible to the batch's transaction, so
  the claim fails (reproduced), and the outcome content is left behind. Option (a) needs `claim_effect` to write its
  outcome inside the batch.

**Correction, increment A (LABS-1.036), approved and merged (LABS-1.037).** From `feature/pre-e-a-atomic-operations`: a public
`WorldModel.operation()`; every composite writer, including module installation, upgrades and database creation, is
one operation; `claim_effect` writes its outcome inside it. A failure injected at any write leaves nothing and moves
no recorded time. See [pre-e-increment-a.md](pre-e-increment-a.md). The issue stays open until the increment is
approved and merged.

## DI-9: report query counts and cross-world scaling (performance)
**What was measured** (`stage-d3.md` section 7, `bench-d3/README.md`; four interleaved rounds):
- `provenance(s12-b)` costs **336 queries** (about 640 ms), and `measurement_calibration(sample-12)` **411** (about
  610 ms). Each composes core readers per link, per account, per record and per instrument (N+1 reads, as in the
  Stage C measurement readers);
- **cross-world slowdown:** with the laboratory world in the same database as the gearbox and Acme worlds, some
  gearbox questions take 1.6–2.8 times as long at identical query counts: `where` ×2.5–2.8; `effects_of`, `contents`
  and `value_of` ×1.6–1.7. Installing the profile alone (no laboratory world) causes none of it, so the cost is the
  other world's data. The likely cause (queries matching by type across every world before narrowing to one) is not
  verified.

**Not a correctness issue:** answers are identical (tests: three worlds in one database).

**Options (Stage E):**
- (a) batch the per-item reads in the reports;
- (b) narrow queries to the world (and its bases) first;
- (c) accept the cost and set a budget for each report.

Recommended: first verify the cause of the cross-world slowdown with query plans, then (b) and (a), measured against
`bench-d3`.

**Investigated (LABS-1.054, LABS-1.055; still open):** [stage-e-di9-investigation.md](../stage-e/stage-e-di9-investigation.md).
Query plans are not available through the 3.14 driver, so the cause was established by instrumentation and replay
instead:
- row decoding and Python are not the cause;
- supersession and acceptance joins are not narrowed to the world's attestations (F2);
- subject-bound queries about an empty type cost in proportion to the data (F3);
- `occurrence()` loads every event in the world (F4).

Proposed corrections O-1 to O-3 are at the DI-9 review gate; none is implemented.

**Corrected (LABS-1.056 to LABS-1.059).** O-1 (144be5b), O-2 (92da365), O-3 (4ce7933) and F6 (75dd89b) are
implemented, each behind a switch to the earlier path, with no change to any answer:
- 877 tests in four configurations, each run twice;
- 106,752 reference answers unchanged, 398 views identical, E1 272/272.

Results from the entry code to F6:
- Core 0.3 selective 10×: 259 → 17.5 ms per question;
- scale read round at 92 worlds: 44–46 → 9.3 s;
- `where` at 92 against 11 worlds: median ×1.05, the 1.2× target met in 7 of 7 runs.

[stage-e-performance-closure.md](../stage-e/stage-e-performance-closure.md) has the details. The residual items
are DI-20 to DI-23 below.

**Added to the Stage E investigation (LABS-1.039): the cost of contextual office exclusivity** (increment B). Measured
apart from the canonical judgement mechanism (`probes/pre_e_b_perf_split.out.txt`, four alternating rounds, see
[pre-e-increment-b.md](pre-e-increment-b.md), "After the merge"):
- the mechanism alone adds no queries and no measurable time on any subject;
- applying exclusivity adds 5 to 38 queries per call on the subjects it concerns (appointments under an exclusive
  office), with time to match; the largest relative cost is `facts_about(cal)` in the plan world: 27 to 47 queries,
  about 41 to 83 ms. Readers and subjects without such appointments are unaffected.
Options to examine with the rest of DI-9: load the attested constraints once per reading rather than per report, and
load rival holders in one batched query.

**Added (LABS-1.040): exclusivity in `changes`, and increment C's cost.** `changes` applies the same constraint at each
boundary of a subject's timeline, so it pays the exclusivity cost too (not measured before): on the subjects concerned
10 to 66 extra queries per call, the largest `changes(depot-7)` in the plan world (209 to 275 queries). Increment C's
aggregation adds no query on any reader or subject (`probes/pre_e_c_perf.out.txt`, three alternating rounds).

**Added (LABS-1.044): the cost of increment D's occurrence view.** `occurrence()` now lists every account and role
(ER-5) and judges constrained roles. Measured against `bf8bb34` (`probes/pre_e_d_occurrence_bench.out.txt`, three
alternating rounds, the 398 reference views and the 20 design examples): about 19 queries and 23 ms per view before,
86 queries and 100 ms after (×4.4 in both, far outside the spread between rounds, at most about 10 %), paid by every view whether a
constraint applies or not; where a kind-scoped constraint is evaluated, about 141 queries per view. Of the 66.7 queries
the new part adds to an unconstrained view (`probes/pre_e_d_occurrence_queries.py`): identity of the occurrence and its
players 32.5, judging each `describes` link at its account's start 18, loading the `describes` claims 15, each
description's roles 1.2. Options to examine with the rest of DI-9: reuse the identity the view already computed and
compute player identity only for judged roles; judge every account's link in one batched reading; read all roles in
one query. Not optimised in increment D.
Retained under LABS-1.045 (merge of increment D): about 19 → 86 queries and 23 → 100 ms per view, about 4.4×. The
benchmark (`probes/pre_e_d_occurrence_bench.py`, summary `pre_e_d_occurrence_bench_summary.py`) and the query
breakdown (`probes/pre_e_d_occurrence_queries.py`) are kept for Stage E. Also noted by the consolidation: the
unchanged Core 0.3 workload (plan 9.4) has not been measured since A0.


## DI-10: automated browser regression coverage for the schema explorer (maintenance)
**What exists.** The explorer's search, filters, navigation, themes and narrow layout were checked by hand in a browser
at the LABS-1.024 gate. Tests check its data, its lack of external references and its escaping, but run no browser.

**Item.** Add an automated browser check (headless) of the reference explorer: no console errors, no network requests,
search ranking, each filter, hash navigation and the back button, and a narrow layout without sideways scroll.
Non-blocking: no deadline; it guards against regressions in the page template.

## DI-11: `_claims`-based reports ignore functional conflicts
**What happens.** The core has two reporting paths over the same per-content judgement:
- `facts_about` / `value_at` / `holds` apply functional-slot conflicts (DISPUTED with rivals), but `facts_about` drops
  polarity-disputed content (DI-1);
- `_claims` and everything built on it (`capable`, `direct_dependencies`, `effects_of`, and every profile report) keep
  polarity disputes, but never apply functional-slot conflicts.

**Concrete case** (review probe): a mechanical joint-kind slot keyed by the two endpoints is declared (DI-3's
option). `holds` and `facts_about` then report the bolted and bonded joints as DISPUTED with each other, while
`mechanical.connections` still reports both ASSERTED.

**Affected.** Latent today: no installed slot is on a type that a `_claims` report reads (the installed slots are
`located-at`, `anchored-to`, `positioned-in` and `frame-transform`). It blocks DI-3's slot option and any future
profile slot on a reported type. See the review for the common cause it shares with DI-1, DI-5 and DI-6.


**Correction, increment B (LABS-1.038), approved and merged (LABS-1.039, `main` d9d873a).** Made on
`feature/pre-e-b-canonical-judgement`: one canonical
per-content judgement for every reader; DI-11: every reader applies declared and established attested single-value constraints ([pre-e-increment-b.md](pre-e-increment-b.md)).

## DI-12: traversals judge without same-as identity
**Registered LABS-1.038; correction deferred.** Found while designing increment B
([pre-e-increment-b-design.md](pre-e-increment-b-design.md), Q6).

**What happens** (`probes/pre_e_b_di12.py`, output `probes/pre_e_b_di12.out.txt`). `parts` and `dependencies` judge
their links with an empty identity, while every other reader uses the perspective's accepted same-as links. With
`b-alias` accepted as the same thing as `bracket`:
- `parts(gearbox)` misses a bolt that is part of `b-alias`, although `holds(part-of(bolt, bracket))` is ASSERTED;
- an assertion part-of(p, gearbox) and an accepted denial part-of(p-alias, gearbox) are DISPUTED for `holds`, but the
  closure follows the link as established.

Frame chains are not affected: same-as relates particulars only, so two frames can never be declared the same.
A related, smaller difference: the reports that select contents by their subject (formerly through `_claims`, now
`_contents`) match the subject's own id, not its other names (they group co-referring names correctly once found).

**Impact on the reference worlds:** none. No reference world has an accepted same-as link (all 11 worlds checked), so
no traversal content names an aliased thing.

**Options.** (a) Judge closures under the perspective's identity, traversing equivalence classes, as `holds` does;
(b) keep id-level traversal and report links that name an aliased thing. Either needs its own decision and tests; the
selection difference would be decided with it.

**LABS-1.046: correction designed** with DI-15 and DI-16 as one identity increment, not implemented: [pre-e-identity-design.md](pre-e-identity-design.md) (ID-8: option (a), traversal between identity classes, and selection by class).

**LABS-1.049: closed.** Corrected by the identity increment (ID-8: `parts` and `dependencies` traverse identity classes and stop at a disputed link; reports select contents by the subject's class), approved and merged at `main` `dd58b25` ([pre-e-identity-increment.md](pre-e-identity-increment.md)). Permanent tests: `tests/test_t_identity.py`. `probes/pre_e_b_di12.py` is kept unchanged as the historical record of the defect and now fails on purpose.

## DI-13: one player per event role per account
**What happens.** In TypeDB 3.14.1 a role with no cardinality annotation is `@card(0..1)`, and no event role (core or
profile) declares another, so one event description can name at most one actor, patient, removed part, product and
so on. Writing a description with two is refused by the database (`[CNT5]`).

**Consequence.** An operation with several participants in one role (a two-part replacement, a team sampling, several
aliquots) can only be recorded as several accounts of one occurrence. Increment D handles that correctly: several
players across accounts are a union unless an applicable, established constraint makes the role exclusive.

**Options (later).** (a) Keep it, and document (current); (b) declare `@card(0..)` on the event roles whose
cardinality depends on the operation, which changes the core and profile schemas and needs its own decision.

**Consolidation (LABS-1.045): faithful representation.** A joint action can only be recorded as several accounts from
one source: a two-technician job becomes two accounts (the union is right, the account count is not), and a
co-signed official act becomes two accounts that organisation 0.2's unconditional `official` constraint judges
**DISPUTED**, a false conflict (`probes/pre_e_consolidation.out.txt`). Recommended: decide before Stage E (see the
consolidation, section 2).

**LABS-1.046: additive correction designed**, not implemented: [pre-e-multiplicity-design.md](pre-e-multiplicity-design.md). Selected event roles open to several players per account (core module `core-0.4-event-multiplicity`, profile next versions), and rule Q compares each account's set of players (union without a constraint; `one`: DISPUTED for several players in one account or across accounts; new `set`: established when every account states the same set). TypeDB evidence: `probes/pre_e_di13_cardinality.out.txt` (a role opens on live data; a specialised role must be opened itself; narrowing back is refused once used); rule prototype: `probes/pre_e_di13_rule.out.txt`.

**LABS-1.050: closed.** Architecturally approved under LABS-1.050, including the four implementation additions (the
domain error at commit, version-chain profile upgrades, `official_act()`'s `officials`/`by_official`, one part-of
effect per part) and laboratory 0.2's dependency on both upgrades; the multiplicity is exported in schema export format
3 (format 2 is still read, and written only where it can represent the database). Merged into `main` with
`feature/pre-e-multiplicity`. Kept open elsewhere: destination and product stay single (a later design); DI-14 and
DI-9 unchanged; DI-18 new.

**LABS-1.049: corrected on `feature/pre-e-multiplicity`, at the review gate; not closed.** Actor, patient and the
profile roles official, sampler, removed and fitted accept several players per account; origin, destination, location,
instrument, product and sampled stay single. Several players are judged per account set (MP-2) under a declared
multiplicity (MP-3, MP-4); existing databases upgrade explicitly (MP-5). The `move()` defect (two origins refused with
a raw database error, LABS-1.047) is corrected: a domain-level `MovementConflict`, nothing written. Report:
[pre-e-multiplicity-increment.md](pre-e-multiplicity-increment.md).

## DI-14: descriptions listed in a variant without an account there
**What happens.** `account()` writes a description's own attestation over the event's interval, and its `describes`
link with no start (until superseded). A variant world inherits a base attestation when it has no start or starts
before the branch point, and keeps it whole. So in a plan branching before an event, the link is inherited and the
account is not: `descriptions()` lists the description, `occurrence()` lists it under `descriptions` (with no
participants from it), and `process_steps` lists it among a step's descriptions, without saying that the plan holds no
account of it.

**Reproduction:** `probes/pre_e_d_inherited_links.py` (output `.out.txt`): a minimal case, and the 18 reference views
(`plan-relubricate-only`: 15; `lab-plan-recal`: 3, whose accounts start exactly at the branch instant).

**Classification.** Expected visibility under the inheritance rule as specified, not incorrect inheritance. No
judgement is affected: every reader that judges from an account (`interval`, `occurrence_status`, the occurrence
checks of `causes_of`) finds none, and `occurrence_status` reports the account as "none".

**Options (later).** (a) `account()` writes the link from the event's start, so a variant inherits link and account
together (new data only; existing links unchanged); (b) the listing readers mark, or omit, descriptions with no account
in the world; (c) keep, and document. Increment D does not correct it; its `accounts` field reports such an account as `none`
(`occurrence_status`'s vocabulary, ER-5; the design's prose called it "none in this world").

## DI-15: an occurrence's aliases are listed but not compared
**What happens** (`probes/pre_e_consolidation.py`). `act-1-hr` describes `o-1` (official bea) and `act-1-clerk`
describes `o-1-alias` (official cal); both accounts are accepted, and `same-as(o-1, o-1-alias)` is accepted.
`occurrence(o-1)` lists both accounts and both players, but its `official` role is **established: bea**;
`occurrence(o-1-alias)` gives **established: cal**. The alias's account is listed with `describes: None`, though the
canonical judgement of `describes(act-1-clerk, o-1-alias)` is established, so it is never compared.

**Cause.** `_event_roles` judges the accounts' links through `_contents(world, occurrence, ...)`, which selects
contents by the occurrence's own id: the selection difference recorded under DI-12. v0.2 (section 3.2) counts
descriptions linked to anything accepted as `same-as` the occurrence, and requires DISPUTED for different players of a
declared single-valued role.

**Impact.** None on the reference worlds (no accepted same-as link), so the 398-view baseline is unaffected.
**Recommended:** correct before Stage E, with DI-12 and DI-16, as one identity increment (consolidation, section 2).

**LABS-1.046: correction designed**, not implemented: [pre-e-identity-design.md](pre-e-identity-design.md) (ID-9: one view from every name of an occurrence). Reproduced again in `probes/pre_e_identity_cases.out.txt`.

**LABS-1.049: closed.** Corrected by the identity increment (ID-9: one view from every name, additive `aliases` and `identity` fields), approved and merged at `main` `dd58b25` ([pre-e-identity-increment.md](pre-e-identity-increment.md)); permanent tests in `tests/test_t_identity.py`.

## DI-16: identity merges on a disputed same-as
**What happens** (`probes/pre_e_consolidation.py`). `same-as(bea, b-smith)` is asserted and accepted, then denied by
an accepted denial. Its canonical judgement is DISPUTED, but `Identity` unions every usable same-as assertion and
ignores denials, so `identity()` still merges bea and b-smith, and an official act naming bea in one account and
b-smith in another is **established**, not DISPUTED.

**Classification.** Predates increment D and satisfies the Core 0.3 rule as written ("only accepted ones merge"), but
since increment B every other content is judged by its canonical record; identity is the exception. Options: (a) merge
only on an ESTABLISHED same-as, from the denial's recording time on (earlier views stay reproducible); (b) keep, and
report the dispute beside merged answers; (c) keep and document. **Recommended:** decide before Stage E (a core
semantic change, with its own design gate).

**LABS-1.046: clarified, not implemented or closed:** [pre-e-di16-clarification.md](pre-e-di16-clarification.md) (exact entry, minimal reproduction `probes/pre_e_di16_repro.py`, proposed decision: option (a)). Further forms found (`probes/pre_e_identity_cases.out.txt`): a chain merging two names whose own link is denied or disputed (I16, I18); a plan world's stipulated denial of an inherited link ignored (I12). Recorded here with them, as it has the same remedy: the same-as content is itself judged through identity, so a neighbouring link's dispute can make an established link read disputed (I18) and a link with no record read established (I15) (finding F-1 of the identity design).

**LABS-1.049: closed.** Option (a), corrected by the identity increment (ID-2, ID-5, ID-6), approved and merged at
`main` `dd58b25` ([pre-e-identity-increment.md](pre-e-identity-increment.md)). The reproduction is a permanent test
(`tests/test_t_identity.py`): with the assertion and the denial both accepted, the official is DISPUTED and both
accounts are cited; the other three rows are unchanged. **Approved interpretation (LABS-1.049):** the "temporal
context" of identity is **knowledge time**. Identity is timeless in valid time (ID-3), so two names are one thing at
every valid time or at none; it changes only with what is known, so a denial applies from its recording time on and
views at an earlier knowledge time are reproduced unchanged.

## DI-17: conflict-group identity may be over-restrictive (Stage E evaluation)
**Registered LABS-1.049**, from the identity increment (LABS-1.048). Not a defect in the approved semantics: a
recorded risk that they are stricter than needed.

**What happens.** Under ID-5, a group of names connected by established same-as links that contains a pair whose own
link is DISPUTED or denied is not merged at all, and the conflict is reported (`identity()`'s `conflicts`). Example
(`tests/test_t_identity.py`, case I16 of `probes/pre_e_identity_cases.py`): s1~s2 and s2~s3 are established, s1~s3 is
denied. None of s1, s2 and s3 is merged, so the established s1~s2 equivalence is set aside together with the chain
that contradicts the denial. Answers about s1 and s2 are then given separately, never wrongly merged. The `y` group
(a three-name cycle with one denied link) behaves the same way.

**Why it may be too strict.** A group with one disputed pair may hold many sound equivalences; with ID-5 one dispute
switches all of them off. Alternatives that keep more: merge every established link except those that would join
the disputed pair (needs a rule for which link to drop when several would); merge maximal consistent subgroups; or
merge and flag the answers that relied on the group. Each is a semantic change with its own design.

**Impact today:** none on the reference worlds (no same-as content). **Disposition:** evaluate in Stage E. Count how
often conflict groups arise in the evaluation data, and whether separating them hides answers an evaluator expects.
Change only by a new approved design.

**Related deferrals kept (LABS-1.049):**
- **ID-10** (`descriptions()` listing by the describes link's canonical judgement) is not implemented; it needs its
  own approval.
- **TI-1 `derived` marker** (flag pairs joined only through a chain) is not added; `identity()`'s `links` already show
  which links joined a group.

## DI-18: module data the replay does not reproduce is absent from the export
**Registered LABS-1.050**, found while adding schema export format 3. `module_data` is built from the records each
replay step writes (attribution.py) and marks each as found in the database or not. A record in the database that no
replayed module writes, for example a constraint of a profile version this code does not have (attribution
`version-mismatch`), or one written by hand, is **not listed at all**. The export still says the replay did not
verify, so the omission is not silent at the document level, but the record cannot be read from the export.

**Impact:** none on the reference export (every record is reproduced; attribution verified). A format-2 export is
not affected in meaning: its refusal of set-valued constraints reads the database's own records
(`tests/test_o_schema_export.py`, `test_format_2_refuses_a_set_valued_constraint_the_replay_does_not_list`).
**Options:** list such records with status `unresolved` and source `database` (additive in format 3's record
shape); or keep, documented. No deadline; non-blocking.

## DI-19: a constraint dispute through `holds()` does not cite the constraint
**Registered LABS-1.053**, found by the Stage E1 revised evaluation (ORG-011, `benchmark/e1/results-revised/`).
**What happens.** Two accepted appointments to an office whose `exclusive-office` constraint is established are
DISPUTED under the constraint. `holds()` on one appointment answers DISPUTED and cites that appointment (`support`)
and the rival (`conflicts`, with both in `evidence`), but not the constraint attestation that made them conflict. The
canonical judgement keeps it (`constraints[].judgement.support`), and `organisation.office_holders` reports it
(`conflict.constraint.support`); only the `Answer` does not surface it.

**Impact.** No answer is wrong; the provenance of a constraint dispute is incomplete through `holds()`, so a reader
cannot see from the answer alone which rule caused the dispute. None in the 106,752-answer baseline changes until a
correction is made.

**Proposed correction (not implemented; needs approval).** An additive `constraint_support` on `holds()` answers:
the attestation ids supporting each applied constraint (for an attested constraint, its own deciding attestations;
empty for a declared functional slot, which is schema data). Additive, so existing fields keep their values; the
106,752-answer baseline would gain the field on constraint disputes only.

**Implemented (LABS-1.060); approved and merged (LABS-1.061, merge 7769ba1).** Commit 7cb348d:
`Answer.constraint_support`, one entry for each applied attested constraint (type, key, value role, deciding attestation
ids, evidence); always empty for declared functional slots, and so for `value_at()` and `value_of()`.
- 15 new tests.
- 892 tests pass × 4 configurations × 2.
- 106,752 reference answers: 0 changed, and only 4 non-empty entries (the office-holding disputes).
- 398 views unchanged.
- E1 272/272 revised, 267/272 original.
- ORG-011 recall 0.667 → 1.0.

See [stage-e-di19-constraint-support.md](../stage-e/stage-e-di19-constraint-support.md).

## DI-20: readers that still load a whole world (performance, deferred)
**Registered LABS-1.059**, from the DI-9 closure. DI9-D17 is deferred. These readers still build the unscoped memo
or load whole worlds: `occurrence_status`, `causes_of`, `effects_of` and `provenance`. They are now the readers that
grow most with perspectives.

Measured (pooled p50, F6 code, `di9-f6-correction/bench-summary.txt`), worlds-1 → perspectives-10:

| Reader | worlds-1 | perspectives-10 | Growth |
|---|---|---|---|
| `occurrence_status` | 52 ms | 71 ms | ×1.37 |
| `provenance` | 235 ms | 320 ms | ×1.36 |

**Not a correctness issue.** **Option:** the O-3 pattern, scoping the memo to the descriptions the reader already
knows. Do it as an isolated increment, compared against the unscoped path. Not scheduled.

## DI-21: H1, transient slow states (performance, deferred)
**Registered LABS-1.059** (DI9-D5). Identical code and databases varied widely between fresh processes in one quiet
session. For example, base `where` at 11 worlds took 363, 354, 210, 102 and 87 ms (LABS-1.056). The corrected code
is much steadier, and every LABS-1.058 step was steady, but the cause is not identified.
- **Candidates (unverified):** TypeDB caches, planner statistics, Docker VM contention.
- **Option:** fresh-server repeats with the VM otherwise idle, once that is approved. Benchmarks keep interleaving
  passes and fresh-process repeats until then.

## DI-22: cross-world growth in head and parameter fetches (performance, deferred)
**Registered LABS-1.059.** After F6, `where`'s remaining growth from 11 to 92 worlds is in the head and parameter
fetches: +3.2 ms, about 23 → 27 ms per call (`di9-f6-correction/bench-summary.txt`, query time by kind).

The readers that still grow most from worlds-1 to worlds-10 are:
- `parts`: 14 → 20 ms (×1.43);
- `office_holders`: 40 → 55 ms (×1.38). It also measured 11–15 % slower with F6 than with O-3 at worlds-10 and
  perspectives-10, within its spread and not explained.

Not investigated. **Option:** instrument the head fetch per world in the chain before any change.

## DI-23: performance depends on TypeDB 3.14.1's planner (engine, deferred)
**Registered LABS-1.059**, from F6.

**Planner sensitivity.** The single-query supersession lookup grows with the number of supersessions in the database
when it matches two role players that have several possible types. A minimal schema reproduces this: 6 → 47 ms for
×10 data, against about 2 ms in two queries or with concrete types. F6 relies on the two-query form staying flat.

**First query after a bulk load (unverified).** It did not finish within 60 s in 4 of 4 fresh builds of the
reproduction. It answered in milliseconds a few minutes later. This could affect a newly seeded deployment.

**Action:**
- Rerun `probes/stage_e_f6_ablate.py` and `probes/stage_e_f6_supersession.py` on any TypeDB upgrade.
- The private reproduction and an engineering handover are at review (DI9-D18). Nothing has been reported to TypeDB.

## DI-24 to DI-36: E2 contract defects and decision consequences (LABS-1.064)

**Registered LABS-1.064.** DI-24 to DI-30 consolidate the semantic and provenance defects of the E2 contract
adjudication ([stage-e2-contract-adjudication.md](../stage-e/stage-e2-contract-adjudication.md) §4). DI-31 to DI-36
are the implementation consequences of the 25 approved semantic decisions
([stage-e2-semantic-decisions.md](../stage-e/stage-e2-semantic-decisions.md)), consolidated with the earlier entries
where they share a mechanism.

**None is implemented.** Each needs its own approved increment, with tests and an E1 and reference-answer regression
check. Until then, E2 questions on these issues are **eligible** where the reader reports the governed field (the
reader is expected to fail them, and the failure is adjudicated as this DI), and **G probes** where the field,
parameter or representation does not exist yet.

**Kinds of component:**
- **reproduced:** reproduced on an isolated diagnostic fixture (`docs/stage-e/e2-contract-adjudication/diagnostics.json`,
  `probes/e2_contract_diagnostics.py`). Diagnostic outputs never become E2 gold.
- **inspection:** found by reading code against the design; not reproduced.
- **new requirement:** follows from a LABS-1.064 decision. The previous behaviour was not wrong against an approved
  text, because no text decided the case.

## DI-24: subject-keyed readers ignore the subject's same-as group
**Priority: high.** Items D-WH-5, D-PO-3, D-ME-5 (notes: D-OH-2, D-CS-2).

| Component | Kind | Evidence |
|---|---|---|
| `where` and `poses` by an alias find nothing for a position stated under the canonical name, and the reverse | reproduced | DX-2 |
| `measurements` of an alias are not the bearer's | reproduced | DX-3 |

**Correction (later):** apply ID-8 to subject selection in `where`, `poses` and `measurements`, as DI-12 did for
traversals. ID-5 groups (a disputed or denied pair) stay unmerged.

## DI-25: derivations resting on disputed premises or edges (critical architectural priority)
**Priority: critical (architectural).** Items D-WH-3, D-TB-8.

| Component | Kind | Evidence |
|---|---|---|
| a derived pose is INFERRED from a position premise disputed by an accepted denial | reproduced | DX-1 |
| a truncated search whose reached chain has a disputed transform returns UNKNOWN with a transform; SD-SPA-3 requires DISPUTED and no transform | new requirement | SD-SPA-3 (inspection: D-TB-8) |

**Why it is architectural:** a derivation's status must never be better than the worst of its premises and edges (v0.2
E6; A2 "Outcomes"). Both components break that invariant at the point where `frame-transform/v1` composes; any later
derivation rule (DI-7) needs the same rule.

**Correction (later):** a derived candidate takes the worse of its chain's and its position's status; a disputed edge on
a found route decides DISPUTED whatever the search's completeness.

## DI-26: measured content and its denials
**Priority: high.** Items D-CM-6, D-ME-3, D-ME-1, D-MC-1 (related: D-CM-2).

| Component | Kind | Evidence |
|---|---|---|
| an accepted denial of the measured content leaves `compare_measurements` ASSERTED, the denial unlisted | reproduced | DX-4 |
| with `t` given, the measurement disappears | reproduced | DX-4 |
| `t` keeps only positive verdicts of each attestation's own interval; SD-MEA-1 makes it valid time with denials kept | new requirement | SD-MEA-1 (inspection: D-ME-1, D-MC-1) |

**Correction (later):** judge the reported content with its denials (DISPUTED or not holding), list the denial, and
read `t` as valid time for every attestation whose verdict at `t` is not silent.

## DI-27: value readers and their slots
**Priority: high (D-VA-3) / medium.** Items D-VA-3, D-VA-1, D-VA-2.

| Component | Kind | Evidence |
|---|---|---|
| `value_at` with explicit roles forming no declared slot reports an exclusive office's two holders as ASSERTED | reproduced | DX-6 |
| `value_at` does not separate the sides of a value dispute | inspection | D-VA-1 |
| `key_role` without `value_role` answers UNKNOWN; SD-CORE-2 requires a malformed-question refusal | new requirement | SD-CORE-2 (inspection: D-VA-2) |

**Correction (later):** refuse explicit roles that form no declared slot (DI-19 report §1); report rivals apart from
support; refuse a half-specified role pair. The refusals are added to the reader's documented, established refusals.

## DI-28: causal claim applicability (critical architectural priority)
**Priority: critical (architectural).** Items D-CO-1, D-CO-3, D-CO-2, D-EF-5, D-CH-9.

| Component | Kind | Evidence |
|---|---|---|
| a claim lifts through a description with no describes link (`applies: true`, no occurrence) | reproduced | DX-8 |
| a claim lifts through a describes link disputed by an accepted denial | reproduced | DX-10 |
| a lifted claim does not cite the describes links it used | reproduced | DX-9 |
| effect claims and `changes` explanations carry no occurrence status or `applies` | new requirement | SD-CAU-9 (inspection: D-EF-5, D-CH-9) |

**Why it is architectural:** whether a claim about a description applies to an occurrence is the one bridge between
accounts and what happened (SB Occ-2, U-2). Every causal reader crosses it, so it needs one implementation, applied in
`causes_of`, `effects_of`, `explain` and `changes`, rather than four.

**Correction (later):** require accepted (ESTABLISHED) describes links on both sides; cite the links; add each
occurrence's status and `applies` to effect claims and explanations (additive fields).

## DI-29: provenance completeness
**Priority: medium.** Items D-EX-4, D-CH-1, D-TB-3, D-PO-2, D-FI-1, D-TB-7, D-FA-1, D-CH-2 and the `alternatives` part
of D-EX-1.

| Component | Kind | Evidence |
|---|---|---|
| `explain` initiating claims list no attestations | reproduced | DX-11 |
| a negative transition side has an empty `support` while its status rests on a denial | reproduced | DX-13 |
| off-chain disputed edges, both dispute sides in listings, unaccepted transforms as alternatives | inspection | D-TB-3, D-PO-2, D-FI-1, D-TB-7 |
| `facts_about` entries cite the constraint behind a constraint dispute (`constraint_support`) | new requirement | SD-CORE-3 |
| `changes` explanations list their claims' attestations | new requirement | SD-CAU-4 |
| `explain` lists unaccepted initiating claims as `alternatives`, never as explanations | new requirement | SD-CAU-2 |

**Correction (later):** additive fields only, as DI-19: no existing field changes value.

## DI-30: measurement reporting
**Priority: medium.** Items D-ME-10, D-MC-5. The two parts are **independently testable** and may be corrected in
separate increments.

| Part | Component | Kind | Evidence |
|---|---|---|---|
| DI-30a | generic statements are not normalised to SI (canonical units) | inspection | D-ME-10 |
| DI-30b | the calibration reference check reports "no certificate" instead of "time unknown" when the activity has no accepted time | inspection | D-MC-5 |

## DI-31: `holds()` addresses exact content
**Priority: medium.** Items D-HO-1, D-HO-2. Decision SD-CORE-1.

| Component | Kind | Evidence |
|---|---|---|
| given roles are a subset filter; omitted optional roles match contents that have them | inspection; new requirement | D-HO-1; SD-CORE-1 |
| several matching contents: the first decided record in load order is returned | inspection | D-HO-2 |
| a question missing a mandatory role is answered, not refused as malformed | new requirement | SD-CORE-1 |

**Correction (later):** exact content identity (type, given role bindings, parameters); a missing mandatory role is an
established refusal; no load-order selection. Parameterised content stays GAP-SPATIAL-8.

## DI-32: frame-chain answer conventions
**Priority: medium.** Items D-TB-1, D-WH-1, D-TB-2, D-WH-2. Decisions SD-SPA-1, SD-SPA-2, SD-SPA-4.

| Component | Kind | Evidence |
|---|---|---|
| the chain-agreement tolerance (1e-9 rad) is applied but not reported | new requirement | SD-SPA-1 |
| `source == target` presents a premise-less derivation; it must be a declared convention with no derivation and no supporting evidence, given a valid, visible frame | inspection; new requirement | D-TB-2; SD-SPA-2 |
| NOT_YET_KNOWN is never returned when nothing about either frame is visible | inspection | D-TB-2 |
| the `where` judgement label is count-based (`compatible` for uncompared pairs) | inspection | D-WH-2; SD-SPA-4 |

**Correction (later):** report the chain tolerance; mark identity results as convention-derived (a field such as a
basis) and drop the derivation; apply v0.2 §5.6's visible / not-visible distinction; label by compared pairs.

## DI-33: explicit instantaneous measurements
**Priority: high.** Item D-ME-6. Decision SD-MEA-2.

| Component | Kind | Evidence |
|---|---|---|
| a measurement written at an instant is attested over `[s, s)`, so `measurements(t=s)` omits it and two at one instant are "incomparable" | reproduced | DX-5 |
| the writer stores `measure(start=s)` and `measure(start=s, end=s)` identically (`end = end or start`), so no reader can tell an explicit instant from an empty interval | inspection (representation) | qualities.py `measure` |

**Correction (later):**
- **Representation:** an explicit instant marker on the reported content of a measurement (or the stored observation
  instant). Empty half-open intervals elsewhere keep their meaning; this is not a global change to `in_interval`.
- **Migration:** existing measurement contents written without an end become explicit instants; measurement contents
  with an explicit end equal to the start, and all other attestations, are not migrated. The migration is reported per
  record, and the 106,752 reference answers are rechecked.
- **Reader:** an instant content holds at its instant; two observations at one instant are compared subject to the
  other comparability conditions.

## DI-34: calibration judged throughout the start window
**Priority: medium.** Item D-MC-3. Decision SD-MEA-6.

| Component | Kind | Evidence |
|---|---|---|
| `measurement_calibration` judges at the earliest bound of an uncertain activity start | inspection; new requirement | D-MC-3; SD-MEA-6 |

**Correction (later):** established only if established throughout the whole window, considering every internal
validity and judgement transition; never an arbitrary instant; otherwise report the judgements found and any dispute.

## DI-35: change, inclusion, timing and claim-time semantics of the causal readers
**Priority: high.** Items D-EF-1, D-EF-2, D-EX-1, D-EX-2, D-EX-3, D-CH-5, D-EF-6, D-CH-8. Decisions SD-CAU-1, SD-CAU-2,
SD-CAU-7, SD-CAU-8.

| Component | Kind | Evidence |
|---|---|---|
| `effects_of` counts UNKNOWN → held as an accepted change | reproduced | DX-14 |
| `effects_of` samples two instants and misses delayed effects; it must use `changes()` world-state transitions with attribution | inspection; new requirement | D-EF-2; SD-CAU-1 |
| `effects_of` reports no attribution (unique / ambiguous) | new requirement | SD-CAU-1 |
| `explain` lists unreviewed initiating claims | reproduced | DX-11 |
| `explain` drops an initiator with no accepted account instead of keeping it as `timing: unresolved` | reproduced | DX-12 |
| `explain` filters by "ended by t" instead of B-time | inspection | D-EX-2 |
| claims are judged at the reader's `t` / `t2` instead of independently of valid time | inspection; new requirement | D-CH-5, D-EF-6; SD-CAU-7 |
| `changes` with t1 > t2 is not refused | inspection; new requirement | D-CH-8; SD-CAU-8 |

**Correction (later):** one definition of change for every reader (`changes`), keeping the established outcome change,
the accepted claim and the causal attribution apart; B-time inclusion in `explain`; timeless claim judgement with
knowledge time, acceptance, perspective, world and supersession still applied; an established refusal for t1 > t2.

## DI-36: temporal ordering under uncertainty
**Priority: medium.** Items D-BE-2, D-CH-3, D-IV-1, D-EF-3, D-PS-3. Decisions SD-CAU-5, SD-CAU-10.

| Component | Kind | Evidence |
|---|---|---|
| `before` treats touching windows of instantaneous events as certain precedence, discarding a shared possible instant | new requirement | SD-CAU-5 (inspection: D-BE-2; the writer has no explicit instant marker for accounts, as DI-33) |
| one account is picked by lowest id; the others are not reported, and certainty is read from the representative | inspection; new requirement | D-IV-1, D-EF-3, D-PS-3; SD-CAU-10 |

**Correction (later):** strict precedence never discards a shared possible instant; certainty only across every
admissible account and combination; every usable account reported with its attestation. Touching durative intervals
stay "before" and B-time touching stays "consistent" (current behaviour conforms there).
