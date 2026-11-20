# Stage E1 architectural reconciliation: report (LABS-1.052)

**Status: at the reconciliation review gate. Not merged.** Branch `feature/stage-e1-reconciliation` from `main`
`6809e4c`, which holds the merged Stage E1 benchmark. Contract written before the code:
[e1-reconciliation-design.md](e1-reconciliation-design.md) (R1 to R4). No foundational ontology semantics changed;
Stage E2 has not begun.

**In plain terms.** Five changes:
- Occurrence views now say separately *who took part according to the accounts the perspective accepts* (new), and
  *who is said to have taken part, by whom*. The second listing is kept exactly as before.
- Asking about a role a fact type does not have is now refused with a clear message, instead of a silent "not yet
  known".
- Two documents that described one rule differently now agree.
- The benchmark's own rules are clarified. A revised evaluation applies the clarifications without touching the
  original questions or results: all 272 questions now pass.
- One small new provenance gap surfaced for review.

## 1. Commits
| Commit | What |
|---|---|
| `6809e4c` | `main`: the Stage E1 benchmark merged (`--no-ff`; tree identical to the validated branch head `105ecdf`; no library or schema change) |
| `1d47ff8` | the output contract and compatibility specification (R1 to R4), before any code |
| `90427fc` | R1: the resolved role-player set, `tests/test_w_resolved_roles.py` |
| `184aa80` | R2: role-name validation; organisation and agency notes corrected; R3 pinned, `tests/test_w_role_names.py` |
| `d1d2863` | R3: the functional-exclusivity addendum to the increment B design; the older-notation note |
| `80c3ea3` | R4: benchmark clarifications, the revised-evaluation mode and overlay, harness tests |
| `c5861f8` | the revised evaluation's results |
| this report's commit | this report and the validation records |

## 2. What changed
| | Change | Compatibility |
|---|---|---|
| R1 | Every `occurrence()` role entry gains `resolved`: `judgement` (`established`, `disputed`, `union`, `none`), `players` (from compared accounts only; empty when disputed), `compared`, `overridden`, `not_compared` (with why), `constraint`, `support`. ER-5's `players`, `constraints`, `accounts` are unchanged. A union is never `established`; resolving says nothing about whether the occurrence happened | additive field; no schema change, no new query |
| R2 | `holds`, `judgement` (and `explain`), `value_at` (`key_role`, `value_role`), `value_of` (`key`) refuse role names the type does not have (`UnknownRoleError`, a `ValueError`, naming the valid core names and pointing a profile's stored name to its core name). New `role_names(type)`, `check_roles(type, names)`. Organisation and agency module notes give the stored roles | questions with valid names answer as before; invalid ones raise instead of answering NOT_YET_KNOWN; one schema query per model (cached) |
| R3 | Addendum to increment B design 2.4: functional exclusivity, as v0.2 4.4 states it (not holding, INFERRED false; before pending; a disputed slot decides nothing). Behaviour unchanged, now pinned by tests | documentation |
| R4 | `benchmark/e1/CLARIFICATIONS.md` (C1 to C5, R1); `evaluation.run --revised` with `benchmark/e1/revised/overlay.json`; E1 recorded as development-tier, external sealed evaluation deferred, all 272 questions kept | the frozen gold `d0f0aa2` and `results/` unchanged |

Older approved documents (stage-d2 design, stage C, the plan) and a comment in `schema/core/core-0.4-c2.tql` keep the
positional notation `office-holding(holder, office, context)` as descriptive labels; they are historical and were not
edited (noted in the design, R2).

## 3. Tests
| File | Tests | Covers |
|---|---:|---|
| `tests/test_w_resolved_roles.py` | 18 | accepted, unreviewed, rejected and unlinked accounts; a role named only by an unaccepted account; an established one and set; disputed one and conflicting sets (nothing resolved, candidates kept); identity grouping; a plan's own account overriding the inherited one; perspectives; ER-5 fields unchanged; both paths |
| `tests/test_w_role_names.py` | 16 | the stored office-holding roles answer; the old documented names refused by holds, judgement and explain; a stored profile role pointing to its core name; value_at and value_of; functional exclusivity with a pending claim; a disputed slot deciding nothing; both paths |
| `tests/test_v_evaluation_harness.py` | 21 (+2) | the overlay revises copies only; the revised adapters on both paths; restatement mapping only adds names |

## 4. Regression and baselines
From a separate worktree at `c5861f8`. Records: [e1-reconciliation/](e1-reconciliation/).

| Check | Result |
|---|---|
| full suite, four configurations | **744 passed** in each (708 at E1 + 18 resolved-role, 16 role-name and 2 revised-harness tests); only the driver's known `SyntaxWarning`, first run |
| 106,752 answers on `wm-probe-pre-e-mp-u`, against the approved snapshot (the format-3 merge code) | **106,752 identical**, 0 extended, 0 changed; no answer raised `UnknownRoleError`: no reader call in the reference worlds used an invalid role name |
| 398 views against the frozen baseline | 398 views, 0 field changes, 0 judgement changes, the same 8 presentation changes |
| full `occurrence()` answers (356 views at the latest knowledge time) against the approved code | the only difference: `resolved` added to every role entry (1,180 entries); no other field changes |
| `resolved` in the reference worlds | 217 `union`, 12 `established`, 951 `none` (mostly views from perspectives that accept none of the accounts naming the role); in **9** entries the resolved players differ from ER-5's listing, because a non-compared account names someone else: the R1 case |
| query counts (readers, 234 calls; 398 views; one round) | identical: 13,597 queries and 1,820 transactions; 34,477 view queries. `role_names` adds one cached schema query per model, outside these counts |

No existing test, baseline or reference database was changed; the frozen benchmark gold and the original results are
untouched.

## 5. The original and the revised evaluation
| | Original (`results/`, harness `4ce343e`) | Revised (`results-revised/`, `80c3ea3`) |
|---|---:|---:|
| Correct | 267 / 272 | **272 / 272** |
| Paths agree | 272 | 272 |
| Errors | 0 | 0 |
| Evidence shortfalls | 2 (LAB-034, X-003) | 1 (ORG-011) |
| Forbidden evidence cited | 0 | 0 |

| Question | Original | Revised, and why |
|---|---|---|
| LAB-010 | expected not established, got established | expected established (C2: the `calibrate` writer's documented default) |
| TEMP-017 | expected pending, got not holding / INFERRED | expected not holding / INFERRED (C5, R3: v0.2 4.4) |
| ORG-011 | expected disputed, got NOT_YET_KNOWN (wrong role names, silently answered) | re-asked with stored role names: disputed, correct (C4, R2); the old names are now refused |
| LAB-025, LAB-026 | union listed an unaccepted account's player | union from `resolved`: correct, no forbidden evidence (R1) |
| LAB-034 | evidence: the restatement was not mapped | mapped (C3) |
| X-003 | evidence: the explanatory claim was required | explanatory (C1) |

**New finding (ORG-011, revised):** `holds()` on a content disputed under an attested constraint (two holders of an
exclusive office) cites the content's own support and the rival content (`conflicts`). It does **not** cite the
constraint attestation it applied (`exclusive-office`). That attestation is recorded in the judgement
(`constraints[].judgement`) and `office_holders` reports it, but the `Answer` does not surface it. This is a
provenance gap, not a wrong answer. It is proposed for review (an additive `constraint_support` on the Answer).

## 6. Decisions requested at the review gate
1. Approve R1 to R4 and merge `feature/stage-e1-reconciliation` into `main` (`--no-ff`).
2. Confirm `UnknownRoleError` for invalid role names (a question that used to answer NOT_YET_KNOWN now raises).
3. The ORG-011 provenance gap: add the applied constraint's support to `holds()` answers (additive), defer it, or keep
   it as documented.
4. Whether the historical documents should gain a short pointer to the stored role names (they were left unedited).
