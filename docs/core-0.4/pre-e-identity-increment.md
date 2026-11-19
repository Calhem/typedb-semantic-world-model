# Pre-Stage E correction: contextually established identity (DI-12, DI-15, DI-16)

**Status: implemented under LABS-1.048 on `feature/pre-e-identity`, at the identity review gate. Not merged.**
Approved design: [pre-e-identity-design.md](pre-e-identity-design.md), decisions ID-1 to ID-9 (ID-5 as clarified in
[pre-e-decision-gate.md](pre-e-decision-gate.md)); DI-16 by option (a) of
[pre-e-di16-clarification.md](pre-e-di16-clarification.md). ID-10 is **not** implemented (optional, separate, needs its
own approval). Multiplicity (DI-13) and Stage E have not begun. No schema change; the foundational ontology is
unchanged.

## 1. Branch and history
Branch `feature/pre-e-identity`, from approved `main` `bf60c1f`.

| Commit | What |
|---|---|
| `daf163c` | merge of the approved designs (`feature/pre-e-corrections-design`, LABS-1.047; no code) |
| `29ee628` | the correction: identity merges only on established same-as links (DI-12, DI-15, DI-16), with 33 permanent tests |
| this report's commit | this report, the deferred-issues register and the validation records |

## 2. Consistency check of the approved designs (LABS-1.048 item 1)
The four documents were read against the decisions as stated in LABS-1.048. No conflict was found, so implementation
went ahead.

| Decision in LABS-1.048 | Where the design says it | Consistent |
|---|---|---|
| Adopt ID-1 to ID-9, ID-5 as clarified | identity design section 9; gate section 1 | yes |
| Equivalence only where contextually established | ID-2 | yes |
| Disputed, denied, pending or inapplicable links do not establish equivalence | ID-2 (pending, unknown and inapplicable join nothing; disputed and denied join nothing) | yes |
| Traversal respects world, perspective and temporal context | ID-6 (world), ID-7 (perspective, knowledge time), ID-8 (traversals) | yes, with one interpretation (below) |
| Event accounts and descriptions resolve names the same way | ID-8, ID-9 | yes |
| Provenance and explainability preserved | design 3.10 (`identity()` `links`, `conflicts`; `occurrence()` `identity`) | yes |
| DI-16 option (a), reproduction a permanent test | clarification section 4 | yes |
| ID-10 optional and separate | design section 9 | yes: not implemented |

**Interpretation recorded.** "Temporal context" is taken as *knowledge time* (`as_of`): ID-3 makes identity timeless
in *valid* time, so two names are one thing at every valid time or at none. Identity therefore changes only with what
is known (a denial recorded later applies from its recording time on, and views at an earlier knowledge time are
reproduced unchanged). If the owner meant valid time, that would reverse ID-3 and needs a new design.

## 3. What changed, by decision
| Decision | Change |
|---|---|
| ID-1 | A same-as link is judged by the two names it states, with the same polarity layer every other content uses (`decide()` in `semantics.py`, shared with `model._judge`). It is no longer judged "through identity", which removes F-1 (a neighbouring dispute making a link read disputed; a link with no record reading established). |
| ID-2 | `Identity` joins two names only through an ESTABLISHED link. Disputed, denied, pending, rejected and superseded links join nothing. |
| ID-3 | `verdict()` ignores intervals on same-as. `attest()` refuses a new same-as with a start or end, with a domain-level message ("identity is timeless (ID-3) ..."). |
| ID-4 | Classes are the connected components (union-find) of established links. |
| ID-5 | A component containing a pair whose own link is DISPUTED or denied is not merged at all; it is reported in `identity()`'s `conflicts` (names, the links, the links against). |
| ID-6 | The nearest world decides each link (the shared polarity layer's depth rule): a plan's denial of an inherited link applies in the plan and its descendants only. |
| ID-7 | Unchanged: identity is built per perspective and knowledge time. |
| ID-8 | Every reader selects contents by the subject's class (`ContentJudgement.about(role)` and `stated(role)`, used in `dynamics`, `agency`, `laboratory`, `organisation`, `mechanical`). `parts` and `dependencies` (DI-12) traverse classes and stop at a disputed link. Frame chains and `parts_in_database` are unchanged, as the design says. |
| ID-9 | `occurrence()` gives the same view for every name of an occurrence (DI-15), with two additive fields: `aliases` (the class) and `identity` (the links used and any conflict, with their support). Identity is built once per call. |

`identity()`'s result gains `links` (every judged link: its names, judgement, support, depth, whether it merges) and
`conflicts`. Nothing is removed.

## 4. Permanent tests (`tests/test_t_identity.py`, 33 tests)
Built in one module database (world `w` and the plans `plan-split`, `plan-split-child`, `plan-join`, `plan-early`),
plus a separate DI-16 database. They pass on the selective and the full path; **23 of them fail on `bf60c1f`**, which
shows they test the correction and not old behaviour.

| Required by LABS-1.048 | Tests |
|---|---|
| Established equivalence | links and their support; merged officials established; selective identity equal to full |
| Disputed and denied equivalence | pending, disputed, denied, rejected and superseded links join nothing; the disputed neighbour; dan/eve disputed from both names; closures stop at the disputed pump link |
| Transitive identity and cycles | a chain and a cycle (and F-1: no evidence, no link); conflict components, one of them a cycle with one disputed link; order independence (25 shuffles) |
| Context: worlds | hypothetical worlds; a plan inheriting part of a chain; the nearest world decides |
| Context: perspectives | per perspective, including an auditor who accepts only the denial |
| Context: time | knowledge time (before and after a denial); timelessness in valid time; the interval refusal (3 cases) |
| Alias consistency, descriptions and event accounts | alias views identical; `occurrence_status` of aliases; closures through an alias; `direct_dependencies` by class |
| Provenance | the dispute cites both accounts; the identity report keeps its evidence |
| DI-16 reproduction | the 4 rows of the clarification (below) |

### DI-16 resolution
`probes/pre_e_di16_repro.py`, now also a permanent test:

| Context | Before (`bf60c1f`) | Now |
|---|---|---|
| system, now (accepts the assertion and the denial) | official established, one player | **DISPUTED**: `[['b-smith'], ['bea']]`, both accounts cited |
| system, as known before the denial | established | established (unchanged) |
| hr | established: bea | unchanged |
| clerk | established: b-smith | unchanged |

### Identity cases probe
`probes/pre_e_identity_cases.py` on the new code: 28 checks, **0** differences from the design; the DI-15 views from
both names are equal. Case I10 stores a legacy same-as with an interval: the probe now writes it with a small storage
helper (`legacy_interval`), because `attest()` refuses it (ID-3).

`probes/pre_e_b_di12.py` asserted the old, defective behaviour and now fails on purpose (`parts(gearbox)` is
`['bolt', 'bracket']`: `p` is dropped because its link is DISPUTED). It is kept unchanged as a historical record of
the defect; the permanent tests replace it.

## 5. Test suite, four configurations
`uv run python -m pytest -q -p no:cacheprovider tests`, with WM_SELECTIVE 1/0 and WM_PROFILES 0/1, from a separate
worktree at `29ee628`:

| Configuration | Run 1 | Run 2 |
|---|---|---|
| WM_SELECTIVE=1, WM_PROFILES=0 | 633 passed (9 min 48 s) | 633 passed (8 min 21 s) |
| WM_SELECTIVE=1, WM_PROFILES=1 | 633 passed (11 min 4 s) | 633 passed (9 min 28 s) |
| WM_SELECTIVE=0, WM_PROFILES=0 | 633 passed (9 min 25 s) | 633 passed (8 min 5 s) |
| WM_SELECTIVE=0, WM_PROFILES=1 | 633 passed (10 min 6 s) | 633 passed (9 min 17 s) |

633 = the 600 tests on `main` plus the 33 new ones; no existing test needed changing. The only warning (run 1) is the
known `SyntaxWarning` printed by the TypeDB driver package when Python first compiles it in a fresh environment. No
test database was left behind.

## 6. Baselines
**106,752 answers.** The reference database `wm-probe-pre-e-d-new` was read by every reader with the old code
(`bf60c1f`) and the new code, side by side: **106,752 identical, 0 extended, 0 changed** (`probes/pre_e_b_diff.py`;
the two files differ only in the recorded run time). Against the committed frozen snapshot
`probes/pre_e_b_snapshot.after.json.gz` (`probes/pre_e_b_repro_check.py`, ids and clock times masked), old and new
code give exactly the same output: 85,465 identical and 21,287 different. All 21,287 are increment C's authorised
changes, because that file was frozen at increment B: `support` added to `capable` (17,605), `calibration_status`
(3,575), `check_action` (55), `authorised` (20) and `measurement_calibration` (18), and the 14 forecast
`office_holders` changes (`probes/pre_e_c_diff.out.txt`). Nothing here comes from identity.

**398 occurrence views** (`probes/pre_e_d_impact.py ... --compare probes/pre_e_d_occurrence_baseline.json.gz`), on
`wm-probe-pre-e-d-u` and `wm-probe-pre-e-d-new`: 398 views, 0 changes to existing fields, 0 judgement changes, the same
8 role-presentation changes as before. A full comparison of the views written by old and new code (`--out`) gives 0 of
398 views differing in any field, including `accounts` and `roles`. (The new `aliases` and `identity` fields are
additive.)

This was expected: the reference worlds hold no same-as content, so identity changes nothing there.

## 7. Query counts
TypeDB queries and read transactions per call, old code (`bf60c1f`) against new, one round each (counts do not
depend on timing). Records: [identity-increment/](identity-increment/).

**Readers (`probes/pre_e_b_read_bench.py --more --occurrence`, database `wm-probe-pre-e-d`), totals over the fixed
subjects:**

| Reader | Calls | Queries old → new | Transactions old → new |
|---|---:|---:|---:|
| `parts` | 33 | 303 → **588** | 33 → **66** |
| `occurrence` | 42 | 3,650 → 3,650 | 401 → 401 |
| `occurrence_status` | 14 | 1,052 → 1,052 | 151 → 151 |
| `facts_about` | 33 | 968 → 968 | 115 → 115 |
| `capable` | 33 | 774 → 774 | 99 → 99 |
| `changes` | 33 | 2,768 → 2,768 | 299 → 299 |
| `causes_of` | 14 | 1,571 → 1,571 | 276 → 276 |
| `provenance` | 4 | 1,087 → 1,087 | 214 → 214 |
| `interpretations` | 12 | 374 → 374 | 84 → 84 |
| `offices_of`, `office_holders`, `authorised`, `calibration_status` | 16 | 723 → 723 | 111 → 111 |

**The 398 occurrence views (`probes/pre_e_d_occurrence_bench.py --reference`, `wm-probe-pre-e-d-u`):** every view
makes exactly the same number of queries as before.

**Only `parts` (and, by the same code, `dependencies`) costs more, as the design forecast:** one extra read
transaction per call, which loads the world's same-as content so the traversal can follow classes. That load is 5
queries per world in the chain: +5 in an actual world, +10 in a plan that inherits from one. Measured in the same
round, the median call went from about 6–49 ms to about 11–64 ms. `occurrence()` builds identity once per call, so it
adds nothing. This is a known cost, not optimised here (DI-9 stays as it is): the load could later be skipped when no
name in the chain takes part in any same-as content (the existing `_linked_ids` pre-filter), which would be a separate,
approved change.

**The Core 0.3 workload (`probes/pre_e_core03_baseline.py`, P-1; 60 `value_at` questions, seed 11), one run each:**

| Path | Queries per question old → new | Attestations per question | Answers |
|---|---:|---:|---|
| selective | 13.5 → 13.5 | 7.1 → 7.1 | identical on both paths |
| full | 9.4 → 9.4 | 3,283.9 → 3,283.9 | |

These runs used the probe's default 60 questions; the controlled P-1 baseline
([bench-pre-e-controlled](bench-pre-e-controlled/summary.md)) used 180, which is why its figures (13.1 and 9.1) differ
from these for the same old code. Medians were 44.4 → 44.7 ms (selective) and 3,394 → 3,395 ms (full). These are single runs on a busy machine, not a
controlled timing comparison; the controlled repeat belongs to the Stage E entry checks.

## 8. Intentional behaviour changes
All follow from the approved decisions; none appears in the reference worlds.
1. No merge on a disputed or denied link, or on a link a nearer world denies (ID-2, ID-6). DI-16's first row becomes
   DISPUTED.
2. A class with a disputed or denied pair inside it is not merged; it is reported in `conflicts` (ID-5).
3. `judgement("same-as", ...)` is judged by the stated names and is timeless (ID-1, ID-3).
4. A new same-as with a start or end is refused (ID-3).
5. Reports built from contents (`_contents`) include the contents of every name in the subject's class (ID-8).
6. `parts` and `dependencies` traverse classes and stop at a disputed link (ID-8, DI-12).
7. `occurrence()` is the same for every name and adds `aliases` and `identity` (ID-9, DI-15).
8. `identity()` adds `links` and `conflicts`.

## 9. Compatibility
- No schema change, no data migration, no change to schema export.
- Existing databases: answers change only where the design said they would (a disputed, denied or nearer-world-denied
  same-as; a conflict component; an alias's contents). A view frozen before a denial is reproduced.
- Existing same-as data with an interval (written before this increment) is still read, with the interval ignored;
  none is known.
- Internal: `Identity`'s constructor keeps its signature. `ContentJudgement` gains `subject`, `stated()` and `about()`.

## 10. Risks and limitations
- **TI-1, chains no one asserted.** a~b and b~c make a and c one thing. The gate report suggested a per-pair `derived`
  marker in `identity()`'s report. It was *not* among the approved decisions, so it is not added; `links` already lets
  a reader see which links joined a class. Decision requested below.
- **TI-2.** A chain merging two things with incompatible properties shows up as a property dispute, not as an
  identity conflict (registered limitation, unchanged).
- **TI-3.** Same-as intervals written before this increment are ignored (none known).
- **ID-10** (descriptions listed by the describes link's canonical judgement) is not implemented.
- `probes/pre_e_b_di12.py` fails on purpose (section 4).
- DI-9 performance is unchanged in scope; see section 7 for the per-reader query counts.

## 11. Decisions requested at the identity review gate
1. Approve the identity increment for merge into `main` (`--no-ff`), closing DI-12, DI-15 and DI-16.
2. Confirm the interpretation of "temporal context" as knowledge time (section 2).
3. TI-1: add the `derived` marker (additive report field) now, later, or not at all.
4. ID-10: still deferred (no change requested).
5. Then proceed to the multiplicity increment (DI-13) as approved.
