# Core 0.4 Stage D-3: the scientific (laboratory) profile (LABS-1.028)

**Status (2026-11-11): implemented on `feature/core-0.4-d3-science`, at the review gate; not merged.**
- Design: `stage-d3-design.md` (D-D3-1 to D-D3-6, approved under LABS-1.028 with its qualifications).
- Formal derivation provenance is registered as DI-7 (`deferred-issues.md`), a Stage E requirement.
- **Next cross-cutting deliverable:** LABS-1.024, the explorable schema export, before Stage E.

## 1. Schema (`schema/profiles/laboratory/laboratory-0.1.tql`; additive only)
| Type | Roles | Notes |
|---|---|---|
| `sample sub physical-object` | | a sortal whose identity is its portion of matter: splitting or consuming a sample ends it, and each sub-sample is a new particular |
| `sampling sub event` | `sampler` as actor (a particular), `sampled` as origin (a physical object), `product` as destination (a **sample**) | one specialisation per core role (D-D-6) |
| `calibration-of sub proposition` | `certificate` (an information object), `calibrated` (a physical object) | attested over the certificate's valid time, resting on the certificate |

**Seed vocabulary:** `laboratory:specimen` and `laboratory:experiment` (classifications), and `laboratory:calibration`
(an event kind, for calibration activities).

**Refinement of the approved draft.** The draft let any particular be a sampling's specimen or product. Now the
specimen must be a physical object and the product a `sample`: a test shows that an instrument is refused as a
product, with nothing written. Nothing else changes.

**Reused from the core, unchanged:**
- material provenance: `constitution`;
- custody: `located-at`;
- existence: `existence`;
- experiments: an occurrence classified `laboratory:experiment`, with its steps `part-of` it;
- protocols and certificates: information objects. A certificate's own number is the core `calibration-ref`
  attribute;
- the Stage C measurement model: activity, result record, proposition and judgement; `rests-on`; units; corrections;
  comparison.

## 2. API (`worldmodel.laboratory`; functions taking the WorldModel)
| Function | Returns |
|---|---|
| `take_sample(wm, world, sampler, specimen, sample, start, end=None, occurrence=None, attester=…)` | a `sampling` account, and the effects its source claims (`initiates existence(sample)` and `initiates constitution(sample, specimen)`). Claims only |
| `provenance(wm, world, sample, t)` | as separate fields: **chain** (every constitution link back to the specimen, each with its own judgement and evidence, and, since LABS-1.031, each route reaching it, whether that route is established, what blocks it, and its `ancestry`); **established** (only links on an established route); **materials** (each material reached, each route kept apart); **sampling** (per material reached: each account, its acceptance, its occurrences with their own status, and its claimed effects with each claim's judgement); **existence** (the attested judgement, beside the core `exists` answer); **locations** (history and location at t) |
| `register_certificate(wm, name, reference=None, id=None)` | a certificate (an information object with its reference number), in one transaction |
| `calibrate(wm, world, certificate, instrument, start, end=None, attester=…, polarity=True)` | a `calibration-of` attestation resting on the certificate. polarity False is an explicit denial |
| `calibration_status(wm, world, instrument, t)` | holds / status / judgement, using the capable() cases; each certificate with its reference, its own judgement and evidence; `in_force` |
| `measurement_calibration(wm, world, bearer, quality, t=None)` | per measurement record and activity instrument: the **stated** reference, the **attested** calibration judged at the activity's start, an exact-text reference check, and the measurement's own acceptance and usability (copied unchanged) |
| `interpret(wm, world, record, type, roles, attester, tentative=False)` | an interpretation resting on its record: testimony, or a hypothesis (stance `hypothesises`). It refuses basis `inference` |
| `interpretations(wm, world, record, t)` | everything resting on the record: source, stance, basis, acceptance, `mode`, `supports_answer`, the content's own judgement, and the derivation note |

**Shared judgement.** The per-content judgement that the organisation reports used is now
`AgencyMixin._judgement`, used by both profiles. It is a move with no behaviour change: the D-2 tests and the 1,242
`capable()` equivalence answers pass unchanged. No reasoning is duplicated:
- calibration is a content, judged like a capability;
- occurrences, effects, existence, location and comparison are the core's own readers.

### 2a. Recursive provenance: marked routes (LABS-1.031)
A probe under LABS-1.030 found that `provenance` followed every constitution link, established or not, and reported
each link with only its own judgement. A sibling's lineage, reached only through a rejected claim, looked like
established ancestry. The correction (12b2e84) keeps every claim and changes only how routes are reported:
- **Every link is still listed and followed**, including disputed, denied and unestablished links, with its own
  judgement and evidence (the core's, unchanged).
- **Each link lists every route** from the queried sample to it (as [sample, from] steps). A route is established
  only when every step on it is established at t, in the same world, perspective and knowledge time. `blocked_by`
  names each step that is not, with its judgement and evidence.
- **Ancestry:** a link is established ancestry only when at least one of its routes is established. A link that is
  itself established, but reached only through an unestablished step, is not.
- **`established`** is the unambiguous view: only links with an established route, with those routes.
- **Converging routes are kept apart** (a pooled sample made from two siblings reaches their common source twice).
  `materials` lists each route to each material.
- **Cycles terminate:** a route never repeats a material. The link that would close a cycle is listed and marked
  `closes_cycle`, and not followed. A sample is never its own ancestor.
- **Cost:** each material's claims are still read once, so query counts are unchanged. The number of routes can grow
  with heavily converging lineages (listed in section 8).

The tests are in `tests/test_n_d3_provenance.py` (15). They cover:
- four levels of recursive sampling;
- siblings;
- unestablished and disputed ancestral links;
- converging routes;
- cycles;
- three perspectives;
- knowledge and valid time;
- a hypothetical world;
- both query paths.

Each route is checked against the core's own judgement of each link in the same context. With route judgement
reduced to the last link (the old behaviour), 9 of the 15 fail. No ontology change was needed, and no existing
judgement changed: the 25 earlier D-3 tests pass, and the demo output only gains its established-ancestry line.

## 3. Calibration semantics
`calibration_status` judges the calibration at a time. `measurement_calibration` judges it at each measurement
activity's start. Its cases are the capable() cases, with no new statuses. For example, on the laboratory reference
world:

| Case | Judgement | Example |
|---|---|---|
| accepted calibration in force | established (ASSERTED) | B3 at 09:00 |
| expired | expired (holds False; no denial) | B3 at 15:00: certificate B3 ended at 10:00 |
| disputed | disputed (DISPUTED) | B7: cal-lab's calibration and the quality office's denial, both accepted |
| explicitly denied | denied | B7 in the quality office's own perspective |
| no established calibration | not established, with no certificates (NOT_YET_KNOWN) | B9; also an unreviewed calibration (UNKNOWN) |
| not yet effective | not yet effective | B3 before its certificate's start |

**Reference checks.** The record's stated reference is compared with the certificates' own numbers as exact text. It
is reported, never reconciled (G-6):

| Check | Example |
|---|---|
| matches a certificate (with that certificate's judgement) | the 15:00 weighing states CAL-B3-2026-10: it matches certificate B3, which is **expired** at that time |
| no certificate with the stated reference (inconsistent) | Bo's B7 record states CAL-B7-2026-09; certificate B7 is CAL-B7-2026-08 |
| no reference stated | the k=3 result on B7, which is still reported as disputed |
| no certificate recorded for the instrument | a stated reference where the instrument has no calibration content |
| no instrument recorded | lab 2's external result |

A certificate without a number has reference None and never matches.

**Never invalidating.** Several tests show that calibration leaves measurements alone:
- `measurement_calibration` copies each measurement's acceptance and usability from `measurements()`. They are equal
  in three perspectives;
- the 15:00 weighing, on an expired calibration, is still compared;
- the B7 result, on a disputed calibration, is still usable;
- writing calibrations and denials for every balance leaves `measurements()` and `compare_measurements()` identical.

**Perspectives, knowledge time, worlds.**
- **Perspective:** B7 is disputed for the system and denied for the quality office.
- **Knowledge time:** before the quality office's denial was recorded, B7 is established.
- **Hypothetical world:** a plan, branching at 15:30, stipulates a renewed B3 certificate (CAL-B3-2026-11) from
  09:30. There, the 15:00 weighing's calibration is established (STIPULATED). The certificates are listed as B3
  expired and B3-r established. In the actual world it is still expired.

## 4. Interpretation semantics
| Case | How it is recorded | How it is judged |
|---|---|---|
| **Testimony**: an analyst asserts a conclusion | `interpret(...)`: stance `asserts`, basis `testimony`, resting on the record | like any assertion. Lab 2's "anhydrous" is unreviewed for the system (UNKNOWN) and ASSERTED in lab 2's perspective |
| **Hypothesis**: proposed, not established | `interpret(..., tentative=True)`: stance `hypothesises` | kept, but never supporting. Ana's accepted hypothesis alone gives UNKNOWN in her perspective; `supports_answer` is False |
| **Formal derivation**: named premises under a named rule | **not recorded** (DI-7, Stage E) | `interpret` refuses basis `inference`. `interpretations` flags a basis-`inference` attestation written directly as "recorded as inference without derivation structure" (the core still says INFERRED, as tested). Every row carries the derivation note |

**Competing interpretations are judged independently.** The system sees "hydrated" as ASSERTED (Bo's testimony) and
"anhydrous" as UNKNOWN. The quality office accepts both: both are ASSERTED, and neither is DISPUTED. Lab 2 sees the
reverse of the system. No incompatibility between categories is assumed. A profile could later declare one (G-2).

The `interpretations` report also lists the measurement a record reports (mode "observation"), so a record's
dependants are complete.

## 5. Scientific demonstration
- **Code:** `src/worldmodel/examples/laboratory.py` (`build_laboratory`: the Stage C laboratory, then the D-3
  extension). `scripts/show_laboratory.py` prints judged answers (Part 1) and raw TypeQL (Part 2, R1 to R5).
- **Output:** `laboratory-output.md`.
- **Contents:**
  - sample splitting: s12-a taken from sample-12; s12-a split into s12-b and s12-c; s12-a's existence ends at the
    split;
  - material provenance: s12-b ← s12-a ← sample-12;
  - sampling accounts distinct from occurrences:
    - Ana's account is accepted, but its occurrence is not established;
    - the s12-b split is attested by the lab log;
    - Bo's s12-c account is unreviewed. Even in Bo's own perspective, where his claimed effects are accepted, s12-c's
      existence and constitution are not established;
  - an experiment (o-exp-1, classified as an experiment, resting on protocol P-7), with three documented steps;
  - an expired certificate (B3), a disputed certificate (B7), and an instrument without a certificate (B9);
  - a hypothesis (Ana: hydrated) and competing testimony (lab 2: anhydrous; Bo: hydrated);
  - measurements whose stated references differ from the established calibration state:
    - a matching reference on an expired certificate;
    - a reference no certificate carries;
    - a disputed calibration with no reference stated;
  - the hypothetical recalibration plan.

## 6. Cross-domain compatibility
- **Install independently:** each profile on a bare core.
- **Together, in every order:** all six orders of mechanical, organisation and laboratory give the same schema.
- **With the renamed fixtures:** all six (three profiles and three fixtures) install together.
- **No collisions or ambiguous type identity:** every new label belongs to exactly one profile.
  - `sample` (real) and `aliquot` (fixture) are unrelated subtypes of `physical-object`;
  - each specialised role maps to one core role: sampler → actor, sampled → origin, product → destination.
- **Core behaviour preserved:** the core laboratory answers are identical before and after installing all three
  profiles. These answers are:
  - `compare_measurements` in two perspectives;
  - `measurements`;
  - `capable`;
  - `check_action`.

  The core-protection runs (`WM_PROFILES=1`) install every profile and fixture into every test database built on the Stage C core.
- **One database, three worlds:** gearbox (through D-1), Acme (D-2) and the laboratory (D-3) build in one database. The
  laboratory answers match those from its own database. Shared concepts are reused: `build_lab` now reuses an
  existing `measurement` category, as the gearbox world does.
- **Fixture rename (D-D3-5):** in the D0 laboratory fixture, `sample` → `aliquot`, `core-sample` → `core-aliquot` and
  `sampling` → `aliquoting`. These are test-only.

## 6a. Deviations from the approved design, and a defect found in validation
| # | What | Why | Effect on approved semantics |
|---|---|---|---|
| 1 | `sampling`'s product must be a `sample`, and its specimen a physical object (the draft allowed any particular) | sample identity is the profile's point; a non-sample product would be ambiguous | narrower; nothing approved is lost |
| 2 | two functions beyond the six approved: `register_certificate` (a certificate with its number) and `interpret` (testimony or hypothesis; refuses basis `inference`) | the reference checks need the certificate's own number, and D-D3-4 needs a writing path that follows the convention | none: they enforce D-D3-4 and support G-6 reporting |
| 3 | reference checks are exact text (match, inconsistent, none stated, no certificate, no instrument) | LABS-1.028 asks for missing or inconsistent references | reporting only; G-6 stands: nothing is reconciled |
| 4 | **defect, fixed in f96aee9:** the first `interpretations` marked any accepted attestation with a supporting stance as supporting, even outside its valid time | found by a probe under LABS-1.029 | now `supports_answer`: true only when the content's judgement at t rests on that attestation. A test checks it against `holds()` support at two times. Core `_claims` entries gain a `support` field (additive; no answer changes) |
| 5 | `build_lab` reuses an existing `measurement` category | so the laboratory world can share a database with the gearbox world | none standalone |
| 6 | **defect, fixed in 12b2e84 (LABS-1.031):** `provenance` judged each link alone, so a link reached only through an unestablished step looked like established ancestry | found by the LABS-1.030 recursive-sampling probe | routes are marked (section 2a); every claim is still listed; the links' own judgements are unchanged |

## 7. Tests and performance
**Test matrix.** The full suite ran eight times per increment, in a clean checkout, one run at a time: selective and
full load (`WM_SELECTIVE=0`), each also as the core-protection run (`WM_PROFILES=1`: every profile and fixture
installed into every test database), each twice. Every run passed, and no test database was left over.

| Increment | Tests | Selective | Full load | Profiles, selective | Profiles, full load |
|---|---:|---|---|---|---|
| 0e6dbcf (three worlds in one database) | 365 | 2/2 passed | 2/2 passed | 2/2 passed | 2/2 passed |
| f96aee9 (the `supports_answer` fix and its regression test) | 366 | 2/2 passed | 2/2 passed | 2/2 passed | 2/2 passed |
| 12b2e84 (path-marked provenance and its 15 regression tests) | 381 | 2/2 passed | 2/2 passed | 2/2 passed | 2/2 passed |

The D-3 file (`tests/test_n_d3_laboratory.py`) has 25 tests: installation (alone, six orders, with the fixtures),
core answers unchanged, three worlds in one database, provenance and sample identity, accounts against occurrences,
calibration (every case, by perspective, knowledge time and world, never invalidating), the reference checks,
interpretations (testimony, hypothesis, rivals, `supports_answer`, refusal of `inference`), and selective against full
load.

**Performance** (`bench-d3/README.md`: four interleaved rounds against `main` 8461e23):
- **D-3 code, no regression:** identical query counts on all 33 existing questions, and medians within noise.
- **D-3 + the laboratory world in the same database:**
  - the database grows by 24% (the profile alone adds 1%);
  - build time grows by about 1.5 s;
  - some gearbox questions are slower at identical query counts (`where` ×2.5–2.8; `effects_of`, `contents` and
    `value_of` ×1.6–1.7). A probe shows the profile alone causes none of this: the cost is the other world's data.
    Answers are unchanged. Recorded as a Stage E scaling finding (section 8).
- **New reports:** `calibration_status` 16 queries (about 24 ms); `interpretations` 41 (94 ms);
  `provenance(s12-b)` 336 (638 ms); `measurement_calibration(sample-12)` 411 (610 ms).

## 8. Remaining limitations and Stage E issues
- **Before Stage E:**
  - DI-1 and DI-2 must be resolved; DI-6 must be reviewed. DI-2 also covers rival sampling accounts naming different
    products (G-5).
  - DI-8 must be resolved (below).
  - **DI-7**, formal derivation provenance (new), is a Stage E requirement.
- **Calibration aggregates follow capable().** An instrument with one disputed certificate and another in force is
  DISPUTED overall, while each certificate keeps its own judgement in the report. This is the same aggregation as
  capabilities and offices, and belongs with the DI-6 review of aggregate statuses.
- **Text, not links (accepted):** the stated reference (G-6), experimental conditions (G-4, D-C-7).
- **Deferred:**
  - an evidence relation with "undermines" (G-3); counter-evidence is a denial resting on its record;
  - declared incompatibility between interpretations (G-2).
- **DI-8, not atomic (resolve before Stage E):** `take_sample` writes the account and its two effect claims in
  separate transactions, as `replace_part` does. A failure part-way leaves an account with fewer claims and nothing
  marking it incomplete. `register_certificate` and `calibrate` are each atomic: the attestation and its `rests-on`
  link are written together. Left unchanged at the merge (LABS-1.030).
- **DI-9, performance (tracked into Stage E):**
  - `provenance(s12-b)` costs 336 queries and `measurement_calibration(sample-12)` 411 (N+1 reads through the core
    readers);
  - with the laboratory world in the same database, some gearbox questions take 1.6–2.8 times as long at the same
    query counts (`bench-d3/README.md`); answers are unchanged. The likely cause, queries matching by type across
    all worlds before narrowing to one, is not yet verified;
  - provenance routes (section 2a) grow with heavily converging lineages; they add no queries.
