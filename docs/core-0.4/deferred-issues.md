# Deferred correctness issues (register)

**Opened 2026-11-11 under LABS-1.025.** These are known correctness issues, tracked apart from the stage documents.
None of them has had its semantics changed yet.

- **DI-1** and **DI-2** must be resolved **before Stage E** (final validation).
- **DI-3** and **DI-4** are accepted limitations until a decision says otherwise.

Each entry gives a concrete case, what it affects, and the options. A resolution needs its own approved decision and
tests.

| # | Issue | Found | Must be resolved | Status |
|---|---|---|---|---|
| DI-1 | `facts_about` omits content disputed by polarity | D-1 (LABS-1.023) | before Stage E | open |
| DI-2 | conflicting accounts of single-valued event participants are not judged | D-1 (v0.2 D9) | before Stage E | open |
| DI-3 | conflicting mechanical joint kinds are not judged | D-1 | no deadline | open (limitation) |
| DI-4 | dependency-kind vocabulary is not validated | D-1 | no deadline | open (limitation) |

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
