# Deferred correctness issues (register)

**Opened 2026-11-11 under LABS-1.025; DI-5 added under LABS-1.026, DI-6 under LABS-1.027.** These are known correctness issues, tracked apart from the stage documents.
None of them has had its semantics changed yet.

- **DI-1**, **DI-2** and **DI-6** must be **reviewed before Stage E** (final validation); DI-1 and DI-2 must be
  resolved.
- **DI-3**, **DI-4** and **DI-5** are accepted limitations until a decision says otherwise.

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
