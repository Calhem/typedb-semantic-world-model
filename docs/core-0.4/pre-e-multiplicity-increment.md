# Pre-Stage E correction: several participants per role in one account (DI-13)

**Status: implemented under LABS-1.049 on `feature/pre-e-multiplicity`; approved under LABS-1.050, with schema export
format 3 added (section 12), and merged into `main`.** Approved design: [pre-e-multiplicity-design.md](pre-e-multiplicity-design.md), MP-2 to MP-5,
with MP-1 restricted by LABS-1.048 (section 3.2 of [pre-e-decision-gate.md](pre-e-decision-gate.md)). The `move()`
defect found under LABS-1.047 is corrected here. ID-10 is not implemented; Stage E has not begun. The foundational
ontology is unchanged.

**In plain terms.** One record of an event (an *account*) can now name two technicians, two co-signing officials,
two removed parts or two samplers, where the domain allows it. Whether several names in one role are people working
together or a disagreement between sources is decided by a declared rule: by default they are a dispute, and only an
act established as co-signed treats its officials as a team. Places (origin, destination, location), instruments and
products still take one each, and a movement can no longer be recorded with two origins: it is refused with an
explanation, and nothing is written.

## 1. Branch and history
Branch `feature/pre-e-multiplicity`, from `main` `dd58b25` (the merged identity increment).

| Commit | What |
|---|---|
| `ba4ac21` | register: DI-12, DI-15, DI-16 closed; DI-17 registered; ID-10 and the TI-1 marker kept deferred |
| `ef230d4` | the multiplicity increment and the `move()` correction, with tests and the regenerated reference export |
| this report's commit | this report, the register, documentation strings and the validation records |

## 2. What changed, by decision
| Decision | Change |
|---|---|
| MP-1 (restricted) | New core module `core-0.4-event-multiplicity` (`schema/core/core-0.4-event-multiplicity.tql`) opens `event:actor` and `event:patient` (`@card(0..)`). Profile versions open their own roles in small schema files that only widen cardinalities: organisation 0.3 `official-act:official`; mechanical 0.3 `replacement:removed`, `replacement:fitted`; laboratory 0.2 `sampling:sampler`. **Kept single:** `origin`, `destination`, `location`, `instrument`, `sampling:product`, `sampling:sampled`, `official-act:office`, `official-act:office-context`. New databases get the module with the rest of the core. |
| MP-2 | `_event_roles` compares each compared account's **set** of players under the perspective's identity. `one`: DISPUTED for more than one player, `reason` "several players in one account" and/or "accounts name different players"; `set`: established when every compared account names the same set, otherwise DISPUTED ("accounts name different sets of players"), each account's set in `sets`. Which accounts are compared is unchanged (ER-1 to ER-5). |
| MP-3 | Optional attribute `role-multiplicity` (`one`, `set`) on `event-role-constraint`, written only for `set` (absent = `one`, so every earlier constraint is stored as it was). For one event type and role, an applicable kind-scoped declaration overrides an unconditional one (reported with `applies` False and why). Two kind-scoped declarations for one event type and role with different multiplicities, or an unknown multiplicity, are refused when declared. |
| MP-4 | Organisation 0.3 adds the category `organisation:co-signed` and `official-act / actor / kind organisation:co-signed / set`; it keeps the unconditional `one` (ER-6). Mechanical and laboratory declare no new constraint. Constraint entries in `occurrence()` gain `multiplicity`, `reason` and `sets` (additive). |
| MP-5 | Explicit `upgrade_to_event_multiplicity()`: one schema transaction, idempotent, refused without the event-role module (the error says to run `upgrade_to_event_roles()` first), documented as one-way once used. `upgrade_profile` now brings any earlier version of a profile to the code's version in one transaction (version chains, `Profile.previous`), applying schema steps that may only widen cardinalities, then the data. Installing or upgrading a profile without the modules it needs names the upgrades to run, in order. `upgrades_available()` reports the new module. |
| `move()` | Checks before writing: one thing, one destination, at most one origin. If the mover's own records hold the thing at several places just before, it raises `MovementConflict` (a `ValueError`) naming the places and the attestations; nothing is written, and the conflicting records are not chosen between, ended or turned into several origins. It is now one operation, so a refusal inside a caller's operation rolls the whole operation back. A joint move (several actors) is accepted. |
| Domain error at commit | Any TypeDB role cardinality violation (`[CNT5] ... @card`) at commit is raised as `RoleCardinalityError` (an `OperationError`) naming the role, its cardinality and the number of players, with the raw error chained; nothing is written. |

**Readers adjusted so that no player is silently dropped:**
- `organisation.official_act()` read only the first official. It now adds `officials` (all of them) and `by_official`
  (each official's office, authority, capability and agency). With one official the top-level fields are unchanged;
  with several, `official` and the four top-level judgement fields are `None`.
- `mechanical.replace_part()` accepts several removed or fitted parts and claims one `part-of` effect per part (with one
  part each it writes exactly what it wrote before). Every other reader already handled lists.

**Schema export.** Event-role-constraint records carry `multiplicity` (`"set"`, or `null` when none is stored), so a
re-created record reads back identically; `wm-schema-export-2.schema.json` allows the field. The format name is still
`wm-schema-export/2` on this branch; section 8a assesses that it should become format 3 (decision 4, section 11). The reference export in `docs/schema`
is regenerated; its schema diff is exactly the six opened roles, the new attribute and its ownership.

## 3. Consistency with the approved decisions
| LABS-1.048 / 1.049 requirement | Where it is met | Test |
|---|---|---|
| MP-1 only for actor, patient, official, sampler, removed, fitted | module and profile schema files | reference export diff; `test_single_valued_roles_refuse_a_second_player_and_write_nothing` |
| destination, product, instrument, location, origin single | not opened | the same test (7 cases, nothing written) |
| exclusivity preserved | `one` stays DISPUTED for several players; office exclusivity untouched | M3, M4, M9, M10; `test_a_co_signed_act_does_not_relax_office_exclusivity` |
| provenance preserved | one description, one attestation, one source | `test_one_account_with_several_players_keeps_one_source_one_description_one_attestation` |
| contradictory accounts never valid because a role is open | MP-2 compares sets; open roles carry no constraint of their own | M4, M6, M7 |
| `move()`: no silent multiple origins or destinations, domain-level error, atomic | `MovementConflict`, `@atomic` | four `move` tests |
| idempotent upgrade | `upgrade_to_event_multiplicity`, `upgrade_profile` | upgrade tests; section 6 |

## 4. Permanent tests
`tests/test_u_multiplicity.py`, 45 tests (both query paths where reading):

| Area | Tests |
|---|---|
| Design cases M1 to M12 (section 5) | M1 two-technician job (one account, union); M2 co-signed act established as a set; M3 the same without the kind (DISPUTED, several in one account); M4 different officials in two accounts (DISPUTED, unchanged); M5 same set twice (established); M6 subset and M7 different second official (DISPUTED, each set cited); M8/M9 identity decides (one player only where the same-as link is established); M10 one-for-one replacement of two parts (DISPUTED); M11 other replacement (union, four part-of claims); M12 team sampling (union of three samplers) |
| Co-participation, provenance, reports | one source, one description, one attestation; `official_act()` reports every official; a co-signed act does not relax office exclusivity |
| Roles kept single | origin, destination, location, instrument, office context, product and sampled each refuse a second player with `RoleCardinalityError`, nothing written |
| Declarations | multiplicities stored (only `set` written); conflicting kind-scoped and unknown multiplicities refused, nothing installed |
| Upgrade (MP-5) | an existing database keeps every answer through the module upgrade, then the profile upgrades add fields only, then accept several players; idempotent; one-way once used; refused without the event-role module; a failing upgrade leaves nothing |
| `move()` | one origin recorded (with a joint move); several origins refused with `MovementConflict`, nothing written, both location records kept; several destinations or things refused; a refusal inside an operation rolls back the whole operation |

None of the 45 can run on `main` `dd58b25`: the file imports `MovementConflict`, `RoleCardinalityError`,
`CO_SIGNED` and the multiplicity module, none of which exist there.

Existing tests that changed, all because of intended behaviour:
- `tests/test_s_event_roles.py`: increment D's checks now use the versions it shipped (`PROFILE_01`, `PROFILE_02`),
  which still behave as before; new checks cover the current versions (both upgrades named, in order), upgrades from
  0.1 straight to 0.3, the step-by-step path 0.1 → 0.2 → 0.3, and the stored multiplicities.
- `tests/test_s_occurrence_roles.py` and `tests/test_t_identity.py`: the official now lists two declarations; the
  helpers select increment D's unconditional one, and X1 checks the co-signed one is listed, does not apply and says so.
- `tests/test_k_d1_mechanical.py`, `tests/test_n_d3_laboratory.py`: the current profile versions need the new module.
- `tests/test_o_schema_export.py`: the exported records include the multiplicity and re-create it.

## 5. Test suite, four configurations, twice
`uv run python -m pytest -q -p no:cacheprovider tests`, from a separate worktree at `ef230d4`, WM_SELECTIVE 1/0 and
WM_PROFILES 0/1, the whole matrix twice:

| Configuration | Run 1 | Run 2 |
|---|---|---|
| WM_SELECTIVE=1, WM_PROFILES=0 | 682 passed (14 min 58 s) | 682 passed (11 min 47 s) |
| WM_SELECTIVE=1, WM_PROFILES=1 | 682 passed (16 min 22 s) | 682 passed (15 min 23 s) |
| WM_SELECTIVE=0, WM_PROFILES=0 | 682 passed (10 min 49 s) | 682 passed (14 min 0 s) |
| WM_SELECTIVE=0, WM_PROFILES=1 | 682 passed (11 min 55 s) | 682 passed (16 min 0 s) |

682 = the 633 tests on `main` + 45 in `tests/test_u_multiplicity.py` + 4 new upgrade checks in
`tests/test_s_event_roles.py`. The only warning (first run) is the known `SyntaxWarning` from the TypeDB driver
package. Times are longer than usual because the baseline snapshots ran on the same machine at the same time; they
are not performance measurements. No test database was left behind (checked after the matrix).

## 6. Upgrade, compatibility and baselines
Records: [multiplicity-increment/](multiplicity-increment/). Old code: `main` `dd58b25`. New code: `ef230d4`.

**Method.** A reference database was built with the old code (`wm-probe-pre-e-mp-u`: organisation 0.2, mechanical
0.2, laboratory 0.1, no multiplicity module) and read by both codes. It was then upgraded explicitly
(`upgrade_to_event_multiplicity()`, then `upgrade_profile` for each profile) and read again by both codes. A second
database was built by the new code (`wm-probe-pre-e-mp-new`) to compare a fresh installation with the upgraded one.
Readings on one database need no masking; readings across the two databases mask attestation ids (they are random
per build).

### 6.1 The upgrade
| Step | Result |
|---|---|
| `upgrade_to_event_multiplicity()` | True: module `core-0.4-event-multiplicity` 0.4.0-mp recorded |
| `upgrade_profile` organisation, mechanical, laboratory | True each: 0.2 → 0.3, 0.2 → 0.3, 0.1 → 0.2 |
| the same four calls again | False each: nothing written (idempotent) |

### 6.2 Fresh and upgraded installations are structurally the same
`structure.py` (in the records) compares the two databases with the new code:

| Compared | Result |
|---|---|
| schema text (`schema()`) | **byte-identical** |
| schema facts (types, roles, plays, owns, annotations; the export's parser) | 519 and 519, 0 differing |
| module records and versions | identical (12 modules) |
| module data: concepts, slots, event-role constraints with multiplicity | 76 and 76, 0 differing |
| `event_role_constraints()` | identical |
| every schema query answer (kinds, sub, owns, plays, relates, role parents, value types) | identical |
| full `occurrence()` answers, 356 views at the latest knowledge time | identical once attestation ids are masked (356 of 356) |

### 6.3 The 398 occurrence views
Against the frozen baseline (`probes/pre_e_d_occurrence_baseline.json.gz`, `pre_e_d_impact.py --library --compare`):

| Database and code | Views | Existing fields changed | Judgements changed | Role-presentation changes |
|---|---:|---:|---:|---:|
| not upgraded (`wm-probe-pre-e-d-new`), new code | 398 | 0 | 0 | same 8 |
| upgraded, new code | 398 | 0 | 0 | same 8 |
| fresh, new code | 398 | 0 | 0 | same 8 |
| upgraded, old code | 398 | n/a | 0 (no constrained role DISPUTED) | 8 |

Full answers, field by field (356 views at the latest knowledge time, the same database for both codes):
- **Not upgraded** (`wm-probe-pre-e-d-new`): 10 views differ, and only by fields added to constraint entries: `multiplicity`, `reason` and
  `sets` on each of 24 entries. No value changes.
- **Upgraded** (`wm-probe-pre-e-mp-u`): 10 views differ: the same three fields added to 28 entries (24 as on the
  database that was not upgraded, and the 4 co-signed declarations of the official), and in those 4 co-signed entries `why` reads "... (unknown): this declaration does
  not apply" where the old code says "... the role is a union" (section 10, wording). No judgement, status, support or
  player changes.

### 6.4 The 106,752 answers
Every reader of `probes/pre_e_b_snapshot.py` on `wm-probe-pre-e-mp-u` (11 worlds, every perspective and knowledge
time the snapshot holds), compared with `probes/pre_e_b_diff.py` (same database: no masking):

| Snapshot A | Snapshot B | Identical | Fields only added | Changed |
|---|---|---:|---:|---:|
| S0: old code, before the upgrade | S3: old code, after the upgrade | **106,752** | 0 | 0 |
| S1: new code, before the upgrade | S2: new code, after the upgrade | **106,752** | 0 | 0 |
| S0: old code, before the upgrade | S1: new code, before the upgrade | 106,750 | 2 | 0 |
| S3: old code, after the upgrade | S2: new code, after the upgrade | 106,750 | 2 | 0 |

So the upgrade changes no answer for either code (the old code reads an upgraded database exactly as before), and
the new code changes no answer on either database. The only difference is the two `official_act` answers, which
gain `officials` and `by_official` (section 2); no existing value changes.

### 6.5 Omitted: a 106,752-answer snapshot of a freshly built database
Approved under LABS-1.049 (continuation). The planned fourth snapshot, the new code reading a database it built itself,
was not taken (it would have taken about 75 minutes). **Rationale:** that database is shown to be structurally the
same as the upgraded one (section 6.2: byte-identical schema, identical module data and constraints), and its 398
views equal the upgraded database's once attestation ids are masked. The upgraded database's 106,752 answers are
compared with both codes (6.4). The data both databases hold are written by the same example builders through the
same writers; only the recorded ids and times differ. **What remains unmeasured:** the answers of readers outside the
398 views on a freshly built database; any difference there would have to come from data written differently by the
new code, which the permanent tests on fresh databases (682, both paths) exercise but do not compare answer for
answer. The Stage E entry checks (LABS-1.048 item 4) re-freeze the baselines on the merged `main` and rebuild the
reference database, which covers it.

## 7. Query counts
TypeDB queries and transactions, old code (`dd58b25`) against new (`ef230d4`), on the same upgraded database
(`wm-probe-pre-e-mp-u`), one round each. Counts do not depend on timing; timings in the records were taken while the
baseline snapshots ran and are not comparisons.

| Measurement | Old | New | Change |
|---|---:|---:|---|
| readers (`pre_e_b_read_bench.py --more --occurrence`): 13 readers, 234 calls, queries | 13,597 | 13,597 | none, reader by reader |
| the same, read transactions | 1,820 | 1,820 | none |
| 398 occurrence views (`pre_e_d_occurrence_bench.py --reference`), queries | 34,477 | 34,477 | none, view by view |
| Core 0.3 workload (60 `value_at` questions), queries per question, selective / full | 13.5 / 9.4 | 13.5 / 9.4 | none; answers identical on both paths |
| `move()`, queries per call (15 moves, `move_count.py`) | 26–27 | 26–27 | none |
| `move()`, transactions per call | 4 | **1** | fewer: the origin is now read inside the move's own operation |

**No material performance regression was found.** The multiplicity is read in the same query as the constraints it
belongs to (no added query per view), the per-account set comparison is in memory, and `move()`'s new checks use the
records it already read. The cost of the `occurrence()` view itself (DI-9) is unchanged.

## 8. Intentional baseline differences
Every difference found against the baselines, each intended; nothing unexplained remains.

| Where | Difference | Count | Why |
|---|---|---:|---|
| 106,752 answers | `official_act` gains `officials` and `by_official` | 2 answers | the reader must report every official of a co-signed act (section 2); with one official the existing fields are unchanged |
| 398 views, constraint entries | gain `multiplicity`, `reason`, `sets` | 24 entries (not upgraded), 28 (upgraded) | MP-4 reporting; additive |
| 398 views, upgraded | each official-act official lists the co-signed `set` declaration, not applying | 4 entries | MP-4: organisation 0.3's declaration, listed with why, as increment D lists every considered declaration |
| 398 views, upgraded, old against new code | `why` of those 4 entries: "this declaration does not apply" instead of "the role is a union" | 4 | corrected wording: the unconditional `one` still applies (section 10) |
| reference schema export | six roles widened, `role-multiplicity` and its ownership, module and profile versions, constraint records with `multiplicity` | 1 export | MP-1, MP-3, MP-5; regenerated, not hand-edited |
| Core 0.3 workload, readers, views | none | 0 | |

The baselines themselves are not re-frozen here: re-freezing belongs to the Stage E entry checks, on the merged `main`
(LABS-1.048 item 4).

## 8a. Schema export: does the multiplicity field need a new format version?
**Assessment: yes. The field should be released as `wm-schema-export/3`, not inside format 2.** Measured on the
regenerated reference export (`format-check.txt` in the records):

| Consumer | Result |
|---|---|
| a reader validating with the format-2 JSON Schema as published on `main` (`dd58b25`) | **rejects every new export**: 6 errors, `unexpected 'multiplicity'` on each event-role-constraint record. The published schema is closed (`additionalProperties: false`, 31 places), so any added field is a breaking change for a validating consumer |
| a reader validating with the updated format-2 schema (this branch) | accepts the new export (0 errors) and every earlier format-2 export (0 errors) |
| a reader that ignores unknown fields | accepts it, but would read the co-signed `set` declaration as a `one` declaration (the meaning of every format-2 constraint), so it would treat co-signatories as a dispute: a silent change of meaning, worse than a refusal |
| this repository's explorer (`schema-explorer.html`) | renders it, but does not show the multiplicity: it describes the co-signed record only as "only for occurrences established as organisation:co-signed" |

Both tests of compatibility point the same way: an existing strict consumer breaks, and a lenient one misreads. The
project's own precedent agrees: adding event-role-constraint records (increment D) moved the format from 1 to 2.
Changing the meaning of format 2 in place would make "format 2" ambiguous between two schema files.

**Recommended change (not made here, for decision):** `FORMAT = "wm-schema-export/3"`; a new
`wm-schema-export-3.schema.json` (format 2's file restored unchanged, so format-2 exports keep validating against
the file they were written for); the validator maps both; the explorer shows the multiplicity; the reference export
regenerated; a test that a format-2 export is still read (as `test_format_1_exports_are_still_read` does for format
1). A small, mechanical change; the export's content is otherwise identical.

## 9. Risks and limitations
- **One-way once used.** After a description names several players of an opened role, TypeDB refuses to narrow the
  role back (tested). A database may stay on the earlier versions indefinitely; the old profile versions still
  install and work.
- **Laboratory now needs the new modules.** Laboratory 0.1 installed on a database created before increment D; 0.2
  opens the sampler and needs both upgrades first (the refusal says so). 0.1 is still available as `PROFILE_01`.
- **`destination` and `product` stay single** (LABS-1.048): several aliquots of one sampling still need separate
  accounts. Opening them needs a design for guarding movements (gate report, 3.4).
- **Origin conflicts must be resolved by the user.** `move()` refuses rather than guessing; the error names the
  records to end or supersede.
- **TypeDB names a specialised role or its parent in the same violation, not always the same one** (for example
  `sampling:sampled` or `event:origin`); `RoleCardinalityError.role` repeats what TypeDB reports.
- **Old code on an upgraded database** reads several players as lists and judges a co-signed act DISPUTED, never
  wrongly established (design 6); it ignores `role-multiplicity`. Measured on the reference worlds (which hold no
  co-signed act): its 106,752 answers and 398 views on the upgraded database are exactly as before the upgrade.
- DI-14 (descriptions listed in a variant without an account there) and ID-10 are unchanged and not addressed.

## 10. Deviations from the design
- **`one` reason with both causes.** The prototype reported only "several players in one account" when one account
  names several players *and* the accounts differ; the implementation reports both, joined by "; ".
- **Override scope.** MP-3's "kind-scoped wins over unconditional" is applied per declaring event type and core role,
  as the design states; declarations on different event types (a subtype's) are not compared with each other.
- **Wording.** A kind-scoped declaration that does not apply while another one does says "this declaration does not
  apply", not increment D's "the role is a union" (which is kept where no other declaration applies).
- **Additions the design did not list:** `RoleCardinalityError` for every cardinality violation (not only `move()`),
  version chains in `upgrade_profile`, `official_act()`'s `officials`/`by_official`, and one `part-of` effect per part
  in `replace_part()`. Each follows from "no silent loss" and "domain-level errors".

## 11. Decisions requested at the multiplicity gate
1. Approve the increment for merge into `main` (`--no-ff`), closing DI-13.
2. Approve the additions in section 10 (domain error at commit; version-chain upgrades; `official_act()` fields;
   per-part effects).
3. Approve laboratory 0.2 requiring both upgrades on databases created before increment D.
4. Schema export: approve releasing the multiplicity field as format 3 (section 8a; recommended, to be done before
   the merge), or keep it inside format 2 accepting the compatibility break for strict consumers.
5. Then proceed to the Stage E entry validation (LABS-1.048 item 4) as approved.

## 12. After review (LABS-1.050)
**Decisions.** DI-13 architecturally approved, including the four additions of section 10 and laboratory 0.2's
dependency on both upgrades (decisions 1 to 3). Decision 4: the multiplicity is released as schema export format 3.

**Schema export format 3** (commit `45f6712`; [implementation notes](../schema-export/implementation.md), "Format 3"):
- `wm-schema-export/3`: every event-role-constraint record states its multiplicity (`"set"`, `"one"`, or `null` for
  none stored, which means `"one"`); `validate()` refuses a format-3 record without it; the explorer shows it.
- Format 2's JSON Schema file is restored byte for byte to the one published at `dd58b25`; format-2 exports (fixture:
  the reference export committed then) still validate and render.
- Format 2 is still written on request (`format="wm-schema-export/2"`, CLI `--format 2`) where it represents the
  database, and **refused** otherwise, naming each set-valued constraint, nothing written. The refusal also reads the
  database's own records, because `module_data` omits records the replay does not reproduce (registered as DI-18).
- A fresh database and an upgraded one export the same document apart from the database name (schema text,
  schema section, attribution, module data with multiplicities).
- Tests: seven in `tests/test_o_schema_export.py`, section "format 3"; three existing assertions moved from format 2
  to format 3.

**Validation of the export change** (commit `45f6712`, from a separate worktree):

| Check | Result |
|---|---|
| full suite, four configurations | **689 passed** in each (682 + 7 format-3 tests); only the known driver `SyntaxWarning`, first run |
| 106,752 answers on the upgraded reference database, against the snapshot of `ef230d4` (S2) | **106,752 identical**, 0 extended, 0 changed |
| 398 views against the frozen baseline | 398 views, 0 field changes, 0 judgement changes, the same 8 presentation changes |
| full `occurrence()` answers (356 views), against `ef230d4` | 0 views differ |
| reference export | regenerated as format 3; schema text unchanged; attribution verified (519 facts) |

Records: `suite-matrix-format3.out.txt`, `snapshot-S2-new-up--S5-format3-up.out.txt` and
`views-format3-upgraded.out.txt` in [multiplicity-increment/](multiplicity-increment/).

**Remaining compatibility limitations.**
- A consumer pinned to format 2 cannot read a database with a co-signed (`set`) constraint: such exports exist only
  in format 3. By design: format 2 would misstate the constraint.
- DI-18: records the replay does not reproduce are absent from `module_data` in every format.
- Opened roles cannot be narrowed once used (section 9), and old code reads a `set` constraint as `one`
  (conservative: DISPUTED, never wrongly established).

