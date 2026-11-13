# Deferred correctness issues (register)

**Opened 2026-11-11 under LABS-1.025; DI-5 added under LABS-1.026, DI-6 under LABS-1.027, DI-7 under LABS-1.028, DI-8 and DI-9 under LABS-1.030, DI-10 and DI-11 under LABS-1.034.** These are known correctness issues (DI-1 to DI-8, DI-11), one
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

Each entry gives a concrete case, what it affects, and the options. A resolution needs its own approved decision and
tests.

| # | Issue | Found | Must be resolved | Status |
|---|---|---|---|---|
| DI-1 | disputed content omitted from generic fact and role reports (`facts_about`, `roles_of`) | D-1 (LABS-1.023) | before Stage E | open |
| DI-2 | conflicting event participants are not judged together (single-valued roles) | D-1 (v0.2 D9) | before Stage E | open |
| DI-3 | conflicting mechanical joint kinds are not judged | D-1 | no deadline | open (limitation) |
| DI-4 | dependency-kind vocabulary is not validated | D-1 | no deadline | open (limitation) |
| DI-5 | a future-effective appointment (or holding) with an unreviewed counter-claim is labelled "not established" | D-2 (LABS-1.026) | no deadline | open (limitation) |
| DI-6 | aggregate organisational reports can return ASSERTED despite mixed constituent statuses | D-2 (LABS-1.026) | review before Stage E | open |
| DI-7 | formal derivation provenance: no record of a named rule and named premises, yet basis "inference" gives INFERRED | D-3 (LABS-1.027 G-1, LABS-1.028) | Stage E requirement | open |
| DI-8 | `take_sample` (and `replace_part`) write an account and its claimed effects in separate transactions | D-3 (LABS-1.028; registered LABS-1.030) | before Stage E | corrected in increment A, awaiting review (not merged) |
| DI-9 | performance: high query counts in the D-3 reports, and questions slowing as other worlds' data grows | D-3 benchmark (LABS-1.029; registered LABS-1.030) | tracked into Stage E | open (performance) |
| DI-10 | the schema explorer has no automated browser regression tests (search, filters, navigation were checked by hand) | LABS-1.024 gate (registered LABS-1.034) | no deadline (maintenance) | open (non-blocking) |
| DI-11 | reports built on `_claims` (capable, the profile reports) ignore functional-slot conflicts; the mirror image of DI-1 | pre-Stage E review (LABS-1.034) | proposed: before Stage E | open (latent) |

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

**Correction, increment A (LABS-1.036), awaiting review.** On `feature/pre-e-a-atomic-operations`: a public
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
