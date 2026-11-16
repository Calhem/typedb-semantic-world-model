# Pre-Stage E correction, increment B: one canonical per-content judgement (DI-1, DI-11, DI-5)

**Status: approved and merged into `main` at `d9d873a` (LABS-1.039), from the reviewed head `e44f1af`.** Implemented
under LABS-1.038.
Approved design: [pre-e-increment-b-design.md](pre-e-increment-b-design.md) at `a1bb840`, with Q1 to Q6. Increment C
(DI-6) is at its design gate ([pre-e-increment-c-design.md](pre-e-increment-c-design.md)); increment D (DI-2) and
Stage E have not begun. The foundational ontology and the schema are unchanged.

## What changed
**One mechanism** (`src/worldmodel/judgement.py`, new). For each content (proposition) in one context (world, valid
time, knowledge time, perspective), the core builds one record, `ContentJudgement`. It is built from the attestations
the reader has already loaded. The record keeps apart the five things LABS-1.038 names:

| LABS-1.038 | In the record |
|---|---|
| the proposition evaluated | `key`: type, canonical players, parameters; `roles`, `stated_roles` |
| the individual claims stating or denying it | `attestations`: every claim, never merged with another; `claims()` gives each one's attester, polarity, stance and basis |
| each claim's acceptance, provenance and temporal applicability | in `claims()`: acceptance state for the perspective (accepted, unreviewed, rejected, retracted, superseded); each claim keeps its interval, world and depth; `support` is the deciding claims, `assertion_ids`/`denial_ids` each side, `pending` the unreviewed claims that would decide t |
| applicable declared or established attested constraints | `constraints`: every declared constraint (functional slot), and each attested constraint evaluated (with its own judgement and whether it applies); `conflicts`: the rival claims |
| the contextual judgement and its explanation | `judgement` (established, disputed, not holding, pending, unknown) with `reasons`, `status`, `support_status` |

Valid time, knowledge time, perspective and hypothetical worlds use the same semantics for every reader, because
every reader goes through the same polarity layer (`_judge`, unchanged) and the same constraint layer.

**One labelling rule.** `claim_label` and `holding_label` replace `_verdict_label` and `_holding_label`; `_claims` is
retired. Every former `_claims` reader reads records through `_contents`.

**Readers.**
- `holds` is a projection of the record. Its answers are unchanged, except where an attested constraint now applies
  (section "Answer changes").
- Listings show content disputed by polarity, marked DISPUTED, citing both sides (DI-1): `facts_about`, `roles_of`,
  `poses`, `frame_info` and `process_steps`. Each `facts_about` entry gains `judgement`, `assertions` and `denials`;
  each process step gains `judgement` and `status`.
- Every former `_claims` report applies single-value conflicts (DI-11).
- Undecided labels follow the reason (DI-5); pending counter-claims never outrank an accepted claim.
- Plain-id answers keep their answers (Q1). `parts`, `dependencies` and `materials` take `report=True` for the links
  or classifications they did not follow; `composition` and `contents` add `not_traversed` to each node.
- Traversals follow established links only (Q3).
- Frame chains apply the `frame-transform` slot (Q5).
- **Office exclusivity** (Q4, choice A): the organisation profile declares its scope (`EXCLUSIVE_OFFICE`); the core
  applies it. `office_holders` and `offices_of` keep their public semantics: each appointment's own judgement before
  the constraint, the conflict beside it.

**DI-12** is registered and deferred, with an executable reproduction and an impact estimate (none in the reference
worlds): [deferred-issues.md](deferred-issues.md).

## How the answers were checked
1. **Frozen before implementation.** `probes/pre_e_b_snapshot.py` builds the review's reference worlds once into a
   kept database and records every reader whose answer comes from content judgement:
   - 11 worlds (3 actual, 8 hypothetical);
   - every subject, by kind; 5 valid times per world;
   - every attester's perspective and an earlier knowledge time for `facts_about`, `holds` and `capable`.

   The code before increment B (`a1bb840`) gave **106,752 answers**.
2. **Compared after.** The same probe, with the increment B code, on the same database. `probes/pre_e_b_diff.py`
   separates answers that are identical, answers that only gained fields (approved under Q1) and answers that changed.

| | Answers |
|---|---:|
| identical | 97,112 |
| only fields added (Q1: `judgement`, `assertions`, `denials`, `not_traversed`, per-step `status`) | 9,514 |
| changed | 126 |

Every changed answer was examined; each belongs to one of the authorised causes below. None is unexplained. The
frozen snapshots and their comparison are in `probes/` (`pre_e_b_snapshot.before.json.gz`,
`pre_e_b_snapshot.after.json.gz`, `pre_e_b_diff.out.txt` and `.json`). The performance changes made during the work
(section "Cost") were checked the same way: the final code gives exactly the same 106,752 answers as the first
version.

## Answer changes
| Cause | Answers | What changes |
|---|---:|---|
| **DI-1** | 46 | `facts_about` lists five polarity-disputed contents, exactly the review's prediction: `causes(o-relubrication, o-test-run)` in the gearbox world and two plans, `calibration-of(balance-b7, cert-b7)` in the laboratory world and one plan |
| **DI-5** | 36 | Cal's site-manager appointment (accepted from day 8, an unreviewed denial): "not yet effective", was "not established" / "unreviewed", in `capable`, `office_holders` (that appointment's entry only) and `offices_of`, Acme and its plan; `classified-as(sample-12, hydrated)` for bo's and qa's perspectives, laboratory world and plan |
| **DI-11, office exclusivity** | 44 | Bea and Cal both hold site-manager in depot-7 on days 8 to 10 under an established exclusive office. `office_holders` and `offices_of` already said DISPUTED; now `holds`, `facts_about`, `roles_of`, `capable` (and its `only_in`) and `changes` say so too |

In the test suite, two tests changed on purpose:
- `test_m_d2_organisation.py`: `roles_of` now lists the polarity-disputed role (DI-1);
- the LABS-1.026 `capable()` baseline: one of its 1,242 answers changes (DI-5). For the system perspective, Cy's
  only applicable content is the system's own accepted *denial* that begins after t. It was "not yet effective",
  the label `capable` reserves for an accepted holding that begins after t; it is now "not established".

## Points decided in implementation
These refine the approved design. Each keeps an existing answer or follows directly from an approved decision.
1. **PENDING** is "no accepted claim bears on the content, and an unreviewed claim exists". The design said "would
   decide t". The change keeps the existing label ("unreviewed") for an unreviewed claim that says nothing about t.
   `pending` still lists only the claims that would decide t.
2. **"Not yet effective" comes only from an accepted assertion.** An accepted denial that begins after t says
   nothing about t (reason `silent`, label "not established"). This is the one changed baseline answer above.
3. **NOT_HOLDING with reason `excluded` or `overridden`.** An undecided content whose single-value slot holds another
   value (or a nearer world's value) does not hold, INFERRED, exactly as `holds` has always answered. Records and
   `holds` agree. No listing shows these.
4. **Exclusivity in the core readers** (the 44 answers above). LABS-1.038 asks for one mechanism used by every
   relevant reader, with office exclusivity moved into it. Applying it only in `office_holders` would have left
   `holds`, `facts_about` and `capable` contradicting `offices_of`, as they did before.
5. **When an attested constraint is evaluated.** Only where it could change a judgement: two or more different
   holders under one key. Rivals are loaded only where the constraint is established at t; the constraint is
   judged once per report from one load (a memo), without attested constraints of its own. So evaluation stops
   after one level and never recurses. An attested constraint appears in a record's `constraints` only when it was
   evaluated.
6. **Frame chains and same-as.** Frames cannot be declared the same (same-as relates particulars only), so DI-12
   concerns `parts` and `dependencies` only.
7. **The DI-5 "begun, end unknown" case** is not present in the reference data at the sampled times: both claims of
   `sample-12 hydrated` run until superseded, and the review's count used a coarser criterion. The case is covered
   by the new tests and by the review's reproduction ("DI-5 wider").

## Tests
**New:** `tests/test_q_judgement.py`, 17 tests:
- DI-1: `facts_about` cites both sides; a dispute is listed only while it is one (another perspective, an earlier
  knowledge time); closures keep their answer and report disputed and pending links; `composition`, `contents`,
  `materials`, `roles_of` and `process_steps`;
- DI-11: a declared slot on a profile type is applied by `connections`, `holds` and the record alike;
- DI-5: every undecided reason and its label in both vocabularies and through `capable`; a pending counter-claim
  never outranks an accepted holding, and stays listed;
- office exclusivity:
  - applied where established, with `office_holders` and `offices_of` unchanged; another context is unaffected;
  - not applied before the constraint starts or before it is known;
  - not applied by a perspective that has not accepted it, nor while the constraint is disputed;
  - judged once per report, never more than one level deep;
- hypothetical worlds: an inherited dispute, then the plan's own claim deciding; frame chains (Q5); every reader
  giving the same judgement as the record and `holds`, on both query paths.

**Reproductions** (`probes/pre_e_review_reproductions.py`): DI-1, DI-5 and DI-11 now assert the corrected behaviour.
Every other case behaves as recorded.

**Full suite:** 487 tests (470 existing, 17 new). Every configuration was run twice at `034a4ec`: both query paths (selective and full load), each with and without core protection, which installs all three profiles. 487 passed in each of the 8 runs (10 to 15 minutes each), and no test database was left over.

## Cost
`probes/pre_e_b_read_bench.py`, on the same reference database. The old code (`a1bb840`) and the new code were run
alternately, two runs each, 5 rounds per case; the cases include the provenance-heavy laboratory reports and the
hypothetical worlds. Output: `probes/pre_e_b_read_bench.out.json`.

| Reader | Cases | Queries per round, before → after | Sum of median ms, before → after |
|---|---:|---|---|
| `facts_about` | 33 | 915 → 968 | 3,563 / 3,465 → 4,118 / 4,110 |
| `parts` | 33 | 303 → 303 | 665 / 655 → 618 / 614 |
| `occurrence_status` | 14 | 1,052 → 1,052 | 1,593 / 1,533 → 1,525 / 1,519 |
| `causes_of` | 14 | 1,571 → 1,571 | 2,522 / 2,497 → 2,560 / 2,490 |
| `capable` | 33 | 774 → 774 | 1,021 / 1,022 → 1,029 / 1,011 |
| `interpretations` | 12 | 374 → 374 | 748 / 736 → 828 / 813 |
| `provenance` | 4 | 1,087 → 1,087 | 2,747 / 2,732 → 2,946 / 2,860 |
| `calibration_status` | 4 | 91 → 91 | 130 / 133 → 140 / 137 |
| `office_holders` | 4 | 172 → 218 | 624 / 563 → 480 / 558 |
| `offices_of` | 4 | 227 → 328 | 646 / 610 → 871 / 848 |

- **Unchanged query counts everywhere except where office exclusivity now applies.** Traversals, provenance,
  causes, calibration, interpretations and `capable` make exactly the same queries. Their time differences are
  within run-to-run variation (up to about 10% here).
- **The extra queries** are confined to the subjects with an appointment under an established exclusive office
  (Bea, Cal and depot-7, in Acme and its plan). They pay for one constraint load and, where the constraint is
  established, one load of the other holders: that is what applying exclusivity costs. For the slowest such case,
  `facts_about(cal)` in the plan: about 78 ms against 41 ms, when warm.
- **Kept down during the work.** The first version cost up to 3.8 times the queries and up to 10 times the time on
  those subjects, and its per-content work was visible on large subjects. Three changes brought it to the figures
  above:
  1. pending claims and claim detail are computed only when asked for;
  2. records are built only for the contents a reader reports, and a listing builds no undecided records;
  3. constraints are judged in one load per report, and rivals are loaded only where a constraint is established
     (and not at all where the subject is a key player, or for contents a reader does not report).

## Limitations
- **DI-12** (registered, deferred): `parts` and `dependencies` judge without same-as identity. A related, smaller
  point: the former `_claims` reports select contents by the subject's own id.
- **Aggregates are unchanged** (`_combine`, `_overall`): increment C. Their answers changed only where a per-content
  label changed.
- **The merged occurrence view** (`occurrence`) is unchanged: increment D.
- An attested constraint is evaluated under the reading's identity, as every other content is.
- `changes` evaluates attested constraints at each boundary of the subject's timeline, with a memo for the call.

## Not changed
DI-2, DI-3, DI-4, DI-6, DI-7, DI-9 and DI-10. The aggregation rules (increment C) and event-role constraints
(increment D) are untouched. The foundational ontology and the schema are unchanged. Stage E has not begun.

## After the merge (LABS-1.039)
- **Merge.** The approved head `e44f1af` was unchanged and its tracked files clean; merged with `--no-ff` into `main`
  at `d9d873a`, whose files are identical to `e44f1af`. Verified on GitHub (`git ls-remote`).
- **Regression on merged `main`.** 487 passed in each of the four configurations (both query paths, `WM_SELECTIVE=1`
  and `0`, each without and with `WM_PROFILES=1`, which installs all three profiles); no test databases left behind.
- **The 106,752-answer comparison is reproducible.** The reference database was rebuilt from merged `main` and every
  reader re-read (`pre_e_b_snapshot.py --build`, then all 11 worlds). The new snapshot equals the frozen
  after-snapshot in all 106,752 answers once the three things a rebuild always changes are masked: random
  attestation ids, system-clock times, and the order of the two sides of a measurement comparison reason, which
  follows the ids (`probes/pre_e_b_repro_check.py`, output `pre_e_b_repro_check.out.txt`). The frozen comparison
  with the code before increment B (`pre_e_b_diff.out.txt`: 126 changed answers) therefore stands as recorded.
- **Performance: the mechanism and exclusivity measured apart.** `pre_e_b_read_bench.py` gained `--no-attested`,
  which reads with every profile's attested constraints removed, so office exclusivity is not applied. On the two
  organisation worlds (`org` and its plan `org-plan-reorg`), four alternating rounds of: the code before increment B
  (`a1bb840`), the merged code, and the merged code with `--no-attested` (n = 5; query counts were identical in every
  round; `pre_e_b_perf_split.out.txt`, raw figures `.out.json`). Selected rows, median milliseconds:

  | Reader, world, subject | Queries before / after / after without exclusivity | ms before | ms after | ms without exclusivity |
  |---|---|---|---|---|
  | `facts_about`, plan, cal | 27 / 47 / 27 | 41.2 | 82.7 | 39.0 |
  | `facts_about`, org, bea | 14 / 24 / 14 | 25.4 | 43.5 | 23.7 |
  | `office_holders`, plan, safety-officer | 57 / 75 / 57 | 114.3 | 108.7 | 82.0 |
  | `offices_of`, plan, cal | 84 / 122 / 84 | 140.8 | 187.7 | 125.0 |
  | `offices_of`, org, cal | 15 / 25 / 15 | 22.9 | 37.0 | 22.4 |
  | `capable`, plan, bea | 27 / 27 / 27 | 37.8 | 34.8 | 34.9 |

  - **The canonical judgement mechanism costs nothing measurable.** Without exclusivity the merged code makes exactly
    the queries the old code made, on every subject and reader, and is as fast or slightly faster.
  - **All of the added cost is contextual exclusivity**, and only on the 12 measured reader and subject pairs where it applies (an
    appointment under an exclusive office): 5 to 38 more queries per call, one constraint load and, where the
    constraint is established, one load of the rival holders. The 41 ms to 78 ms regression first reported for
    `facts_about(cal)` in the plan is confirmed (41.2 to 82.7 ms here, 27 to 47 queries).
  - Retained as a Stage E performance investigation under DI-9 (see the register). Not a correctness issue: the
    answers are the approved ones.
- **Limitations kept.** DI-12 stays deferred with its reproduction; same-as traversal behaviour is unchanged.
