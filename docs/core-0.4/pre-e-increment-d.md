# Pre-Stage E correction, increment D: event roles in the merged occurrence view (DI-2)

**Status: implemented under LABS-1.043 and validated under LABS-1.044 on `feature/pre-e-d-event-roles`; awaiting
review, not merged.** Approved design: [pre-e-increment-d-design.md](pre-e-increment-d-design.md) at `4596507`,
decisions ER-1 to ER-8. Stage E has not begun; DI-13 and DI-14 are not implemented. The foundational ontology and the
canonical judgement mechanism are unchanged.

## 1. Branch head and history
Branch head: the commit that adds this report, on top of `87f8310` (pushed and verified on the remote). Based on `main` `bf8bb34` (increments A, B and C).

| Commit | What |
|---|---|
| `2489ba8` … `db9a887` | design (LABS-1.041/1.042): executable examples, impact probe, reproductions, the frozen 398-view baseline |
| `4596507` | the clarified design, approved under LABS-1.043 |
| `c208f39` | the `core-0.4-event-roles` module and `upgrade_to_event_roles()` |
| `60b4b7b` | profile declarations (organisation 0.2, mechanical 0.2) and `upgrade_profile()` |
| `72543b7` | event roles judged in `occurrence()` (new fields `accounts` and `roles`) |
| `e452fdb` | the design's examples as permanent regression tests |
| `cbd6b64` | schema export format 2 with `event-role-constraint` records |
| `2c1874d` | occurrence benchmark (first version) |
| `de28aaf` | issue register: DI-13; DI-2 corrected, awaiting review |
| `87f8310` | compatibility comparisons and the occurrence benchmark (LABS-1.044) |
| (this commit) | this report, the not-upgraded database test, the register (LABS-1.044) |

## 2. What changed
- **Storage (ER-7).** A new additive core module, `core-0.4-event-roles` (`schema/core/core-0.4-event-roles.tql`):
  one entity, `event-role-constraint` (id, event type, core role, optional kind, declaring module). New databases get
  it at creation. Nothing in the existing schema changes.
- **Declarations (ER-1, ER-6).** A profile may declare constraints on its own event types only, and subtypes inherit
  them. organisation 0.2: `official-act` actor (stored as `official`), `office` and `office-context`,
  unconditionally. mechanical 0.2: `replacement` patient (stored as `removed`) and `fitted`, only for an occurrence
  established as `mechanical:one-for-one` (a new vocabulary category). The laboratory profile and the core declare none.
  Invalid declarations (the core `event` type, a role that is not a core role, a kind outside the profile's
  vocabulary) are refused with nothing installed.
- **Judgement (ER-2 to ER-4).** In `occurrence()`, by the canonical mechanism: a description is compared when its
  `describes` link is ESTABLISHED (canonical record at the account's start) and its account is accepted; the nearest
  world decides and deeper accounts are listed as `overridden`; players are grouped by the perspective's identity
  (same-as). A kind-scoped constraint applies only where `wm.judgement(classified-as(occurrence, kind))` is
  ESTABLISHED at the occurrence's start. Two or more players: DISPUTED, every player cited; one: established, with
  status and support from the core rule; otherwise a union with no judgement.
- **Output (ER-5).** `occurrence()` adds `accounts` and `roles` (keyed by stored role label, with the core role,
  players citing their accounts, and each constraint: whether it applies and why, the classification, judgement,
  status, support, overridden accounts). `descriptions` and `participants` are unchanged.
- **Upgrades (ER-7).** `upgrade_to_event_roles()`, `upgrade_profile(name)` and `upgrades_available()`: explicit, each
  one schema transaction, idempotent, refused with nothing written when a precondition fails. No downgrade.
- **Schema export.** Format `wm-schema-export/2` adds the record kind `event-role-constraint`; format 1 still
  validates against its own schema and still renders in the offline explorer.

## 3. Compatibility comparisons (LABS-1.044 item 1)
One reference database (`wm-probe-pre-e-d-u`) was built by the code before increment D (`bf8bb34`) and read four
ways; then a second database was built by the new code. Old code `bf8bb34`; new code `2c1874d`, whose library is
identical to the branch head. Output: `probes/pre_e_d_compat.out.txt`.

| Reading | 106,752 answers against S0 | 398 views against the frozen baseline |
|---|---|---|
| S0: old code, not upgraded | (the baseline) | existing fields 0, judgements 0, presentation 0 differences |
| S1: new code, not upgraded | 106,752 identical | existing fields 0; judgements: 10 views judge nothing (expected, see below) |
| upgrade | first run applies the module, organisation 0.1→0.2, mechanical 0.1→0.2; laboratory untouched; second run writes nothing; `upgrades_available()` then empty | |
| S2: old code, upgraded | 106,752 identical | existing fields 0, judgements 0, presentation 0 |
| S3: new code, upgraded | 106,752 identical | existing fields 0, judgements 0, presentation 0 |
| C: database built by the new code | 106,752 identical once attestation ids and clock times are masked | existing fields 0, judgements 0, presentation 0 |

- **Upgrades preserve existing answers:** S2 and S3 equal S0 answer for answer (no masking needed: same database).
- **An unupgraded database keeps its original behaviour:** S1 equals S0 on all 106,752 answers and on every existing
  field of the 398 views. Its 10 judgement differences are the views whose baseline judges a constraint (12 roles in
  10 views: `o-bearing-replacement` in `actual` and `plan-rig-control`, `o-signoff-9` in `org` and `org-plan-reorg`); with no constraint stored, the new code judges nothing
  there, as design section 8.4 states. No view is DISPUTED in any reading.
- **A fresh build reproduces the baseline:** the database built by the new code, read by the new code, gives the same
  106,752 answers as S0 once the build's random attestation ids and clock times are masked, and the same 398 views.
- **No unexpected difference was found.** One probe counter differs between the prototype and the library and is not
  a difference in answers: "description listed without an account in the world" is 18 with the prototype and 0 with
  the library, because the library reports such an account as `none` (ER-5: `occurrence_status`'s vocabulary) and the
  probe looks for the prototype's wording "none in this world". Checked directly: `lab-plan-recal`/`o-split-b` lists
  `ev-split-b` with account `none`. The 18 accounts are still reported (DI-14, unchanged).

## 4. The 398 views and the 106,752 answers (item 2)
- **398 views** (`probes/pre_e_d_occurrence_baseline.json.gz`, frozen at `db9a887` from the approved prototype): on
  the upgraded database (S3) and on the database built by the new code (C): **0** changes to `descriptions` and
  `participants`, **0** changes to judgements (12 roles judged, 12 constraints not applying because the kind is not
  established, 0 DISPUTED), and the **8** authorised role-presentation changes exactly (the views where `roles` keeps
  apart what `participants` merges under the core role `patient`: `o-bearing-replacement` for the system, `cmms`,
  `inspector` and `technician`, in `actual` and `plan-rig-control`; the replacement's `removed` and the core event's
  `patient`). No other change; the list of authorised changes was not broadened.
- **106,752 answers** (`probes/pre_e_b_snapshot.py`, every reader over the reference worlds): identical in S1, S2 and
  S3 against S0, the old code's reading of the same database. `occurrence()` is not one of these readers (its
  baseline is the 398 views); the readers that share changed code with it, `occurrence_status` (whose account-state
  logic is now a helper shared with `occurrence()`) and the profile readers (whose profiles moved to 0.2), are among
  them, unchanged.
- **Nondeterminism.** Comparisons on one database need no masking: ids and recording times are the database's own.
  Across databases (C), attestation ids are random and recording times are clock times of the build, so the 398-view
  comparison uses only ids the reference worlds fix, and the 106,752-answer comparison masks attestation ids and
  system-clock times (`probes/pre_e_b_repro_check.py`). List order is fixed by the code; the permanent tests shuffle
  and reverse query results and the judgement does not change (`test_query_result_order_cannot_change_a_judgement`).

## 5. Schema upgrades and export (item 3)
Compatibility guarantees and the evidence for each (tests are permanent, run in the matrix; probes were run once
for this report):

| Guarantee | Evidence |
|---|---|
| A new database has the module and no constraints | `test_a_new_database_has_the_module_and_no_constraints` |
| `upgrade_to_event_roles()` adds the module once; a second run returns False and writes nothing | `test_upgrade_adds_the_module_once`; S-upgrade in `pre_e_d_compat.out.txt` |
| It is refused, nothing written, without the rest of the core | `test_upgrade_is_refused_without_the_rest_of_the_core` |
| A failure inside it leaves no type and no record (rollback) | `test_a_failing_upgrade_leaves_nothing` (injected failure) |
| `upgrade_profile()` needs the module first, refused with nothing written | `test_upgrade_profile_needs_the_core_module_first` |
| It adds data only (schema byte-identical), once; a second run writes nothing | `test_upgrade_profile_adds_only_data_once` |
| It is refused, nothing written, for another installed version, a schema differing from the files, a conflicting concept | `test_upgrade_profile_refuses_another_installed_version`, `..._a_schema_that_differs_from_the_files`, `..._a_conflicting_concept` |
| A failure inside it leaves the previous version exactly | `test_a_failing_profile_upgrade_leaves_nothing` (injected failure after two writes, then a clean retry) |
| A database without the module still installs profiles that declare no event roles | `test_a_database_without_the_module_still_installs_profiles_without_event_roles` |
| New code on a database not upgraded: `accounts` and `roles` listed, nothing judged; after the upgrades the judgement appears and no existing field or account changes | `test_a_database_not_upgraded_reads_as_before_until_upgraded` (added for this report); S1 and S3 |
| Old code reads an upgraded database with unchanged answers | S2 (106,752 answers and 398 views); not a permanent test, since it needs the old code |
| Format-1 exports remain readable | `test_format_1_exports_are_still_read`: the committed `bf8bb34` export validates against format 1 and renders in the explorer; format 1 refuses the new record kind |
| Format 2 contains exactly the five constraint records, attributed to their profiles, and re-creatable | `test_event_role_constraints_are_exported_attributed_and_recreatable` |
| Format-2 export is deterministic, and the schema round trip is exact | `test_the_export_is_deterministic`, `test_round_trip_is_exact`, `test_two_exports_of_one_schema_differ_only_in_volatile_fields` |
| Schema attribution and the offline explorer | the existing attribution tests (`test_attribution_per_declaration_on_extended_core_types`, `test_module_data_is_attributed_by_replay`, …) and explorer tests (`test_the_explorer_embeds_exactly_the_export`, `test_the_explorer_needs_no_network`), all on format 2 |

**What is not guaranteed:** no downgrade (a committed upgrade is not reversed by the library); declarations carry no
valid or knowledge time, so once installed they also apply to readings at an earlier `as_of` (design 8.4); old code
cannot install a profile at 0.1 into a database that records 0.2 (the existing "another version is refused" rule).

## 6. Test matrix (item 5)
**Full suite: 597 tests** (529 after increment C, 68 new: `tests/test_s_event_roles.py` 16,
`tests/test_s_occurrence_roles.py` 48, `tests/test_o_schema_export.py` 4 net), run twice in each of four
configurations at `87f8310`, one run at a time from a separate worktree:

| Configuration | Run 1 | Run 2 |
|---|---|---|
| selective query path | 597 passed (8 min 37 s) | 597 passed (8 min 59 s) |
| selective, core protection (all three profiles installed) | 597 passed (9 min 40 s) | 597 passed (11 min 35 s) |
| full-load query path | 597 passed (8 min 52 s) | 597 passed (10 min 29 s) |
| full-load, core protection | 597 passed (11 min 40 s) | 597 passed (11 min 4 s) |

- **No failures, no leftover databases** (`wm-test-*` and the upgrade check's `wm-upgrade-tmp-*` counted after every
  run: none), no failed cleanup.
- **Warnings:** one, in the first run only: a `SyntaxWarning` from a docstring in the TypeDB driver package
  (`typedb/common/promise.py`), printed once when Python first compiles that file in a freshly installed environment.
  It does not come from this project's code (the same warning as after increment C).
- **The 25 permanent examples** pass on both query paths in every run: the design's 22 cases X1 to X7d4 (section 6),
  X5 (a core event account's `actor` listed apart from `official`), sampling and core roles never exclusive, and
  existence and per-account reports unaffected by a dispute. They are 12 test functions in
  `tests/test_s_occurrence_roles.py` (the one-for-one cases X2c, X2d, X6d, X7a to X7d4 as 11 parameters of one), plus
  a 13th checking that query-result order (reversed, shuffled) changes no judgement: 24 items per query path, 48 in
  all.
- **Added afterwards:** `test_a_database_not_upgraded_reads_as_before_until_upgraded` (section 5), a test only; its
  file (17 tests) was run twice in all four configurations at the branch head: 17 passed each time, no leftover
  database. The rest of the code is unchanged since `87f8310`.

## 7. Performance (item 4)
`probes/pre_e_d_occurrence_bench.py`, three alternating rounds of old code (`bf8bb34`) and new code, 5 timed calls per
view after a warm-up, on a quiet machine; summary `probes/pre_e_d_occurrence_bench_summary.py`; output
`probes/pre_e_d_occurrence_bench.out.txt` and `.json`. Time: the sum over the views of each view's median ms, given as
the median over rounds [lowest, highest round]. Query counts are deterministic (identical in every round).

**Reference worlds** (the 398 views, upgraded database; categories from the baseline judgement; the reference worlds
hold no disputed role):

| Views | n | Queries old → new | ms old | ms new |
|---|---|---|---|---|
| all | 398 | 7,755 → 34,351 | 9,065 [9,032, 9,136] | 39,873 [39,253, 42,479] |
| unconstrained | 388 | 7,530 → 33,188 | 8,766 [8,736, 8,830] | 38,568 [37,944, 41,053] |
| constraint applies, established | 4 | 90 → 314 | 103 [103, 109] | 346 [344, 362] |
| constraint not applying (kind not established) | 6 | 135 → 849 | 196 [193, 197] | 966 [959, 1,065] |
| hypothetical worlds | 271 | 6,290 → 27,299 | 7,248 [7,191, 7,330] | 31,178 [30,757, 33,449] |
| other perspectives | 314 | 5,655 → 27,051 | 6,147 [6,129, 6,215] | 30,931 [30,499, 32,992] |
| actual world, system, latest | 13 | 190 → 736 | 279 [274, 283] | 958 [932, 989] |

**Design examples** (20 views in the kept examples database; includes the disputed cases):

| Views | n | Queries old → new | ms old | ms new |
|---|---|---|---|---|
| all | 20 | 375 → 1,926 | 593 [592, 652] | 2,291 [2,114, 2,498] |
| disputed | 6 | 120 → 634 | 196 [194, 212] | 757 [701, 824] |
| established | 6 | 120 → 513 | 181 [180, 207] | 583 [550, 654] |
| not applying | 8 | 135 → 779 | 216 [216, 233] | 952 [863, 1,021] |
| hypothetical worlds | 5 | 150 → 773 | 239 [236, 256] | 896 [828, 966] |
| other perspectives | 3 | 45 → 210 | 66 [64, 75] | 237 [221, 270] |

**Reading.** The overhead is real, not noise: every difference is many times the spread between rounds, and the
query counts alone grow 4 to 6 times. Per view on the reference worlds: about 19 queries and 23 ms before, about 86
queries and 100 ms after. It is paid by every view, constrained or not, because every view now lists its accounts and
roles (ER-5). Where the queries go, for the 346 unconstrained views at the latest knowledge time
(`probes/pre_e_d_occurrence_queries.py`): the existing part is unchanged (18.7 per call), and the new part adds 66.7:
identity of the occurrence and its players 32.5, judging each description's `describes` link at its account's start
18, loading the `describes` claims 15, reading each description's roles 1.2. Where a kind-scoped constraint is
evaluated, the classification's judgement adds about 55 more (141 per view in that category, against 86). The constraint judgement itself is
cheap. Added to **DI-9**; nothing was optimised in this increment.

## 8. Remaining limitations and deferred issues
- **DI-9 (performance), extended:** the `occurrence()` overhead above. Candidates for Stage E: reuse the identity the
  view already computed (and compute player identity only for judged roles), judge the `describes` links of all
  accounts in one batched reading, and read every description's roles in one query.
- **DI-13 (one player per role per account), unchanged:** TypeDB's default `@card(0..1)`; a multi-part operation is
  recorded as several accounts, which increment D treats as a union unless an applicable constraint applies.
- **DI-14 (descriptions listed in a variant without an account there), unchanged:** not corrected; the new `accounts`
  field reports such an account as `none`, which is a report of the existing state.
- DI-3 and DI-4 are to be reassessed after this increment, as the design says; not done here (no new functionality
  under LABS-1.044).
- Declarations are timeless (section 5). No downgrade.

## 9. Deviations from ER-1 to ER-8
None found. Points decided in implementation, for review:
- **Account state wording.** ER-5 fixes `occurrence_status`'s vocabulary, so an account the world does not hold is
  `none`; the design's prose (section 13, item 4, and DI-14) called it "none in this world". The code follows ER-5; the
  register's wording is updated.
- **Installing a profile that declares constraints needs the module.** A new database has it; an existing database
  must run `upgrade_to_event_roles()` before installing organisation 0.2 or mechanical 0.2 fresh (installing the
  laboratory profile, which declares none, is unaffected). The design states this for `upgrade_profile` (8.3), not
  for a first installation; it follows from ER-7 ("existing databases receive them only through explicit
  operations"). `tests/test_k_d1_mechanical.py` was updated to call the upgrade first.
- **Constraints per stored role.** Each entry in `roles` carries a list `constraints` (one per applicable declaration
  on that core role), so a subtype adding a constraint to an inherited one is shown, never merged.
