# DI-19: constraint provenance in answers (`Answer.constraint_support`)

**LABS-1.060, 24 November 2026.** Branch `feature/di19-constraint-support`, from `main` 9fb7bc9.
Implementation commit 7cb348d. **Approved and merged into `main` (LABS-1.061; merge 7769ba1).**
Records: [di19-constraint-support/](di19-constraint-support/).

## 1. What changed

Before this change, `holds()` answered DISPUTED on a content disputed under an attested constraint, such as two
accepted holders of an exclusive office. It cited the content (`support`) and its rival (`conflicts`), but not the
attestation that established the constraint (DI-19, found by E1 ORG-011).

`Answer` gains one **additive** field:

```
constraint_support: tuple   # default ()
```

It has one entry for each **applied attested constraint** in the judgement the answer projects:

| Key | Value |
|---|---|
| `constraint` | the constraint type, e.g. `exclusive-office` |
| `key` | the constrained key, by role, e.g. `{"office": ("site-manager",), "context": ("depot-7",)}` |
| `value_role` | the role the constraint makes functional, e.g. `classified` |
| `support` | the ids of the constraint's **deciding attestations** (its own judgement's `support`), sorted |
| `evidence` | the same attestations' evidence records |

The entries are sorted by constraint and key, so the order is stable across load paths.

- **Applied:** the constraint's own record is ESTABLISHED (`Constraint.applies`). A disputed or unaccepted constraint
  is not applied, so it is not cited.
- **Attested only:** a declared functional slot (`located-at`, `anchored-to`, `positioned-in`, `frame-transform`) is
  schema data, so it adds **no entry**. No attestation evidence is fabricated for it.
- **Same judgement, same field.** One function (`WorldModel._constraint_support`) builds the field from the judged
  record of every `Answer`. *Correction (LABS-1.062, reader contracts D-VA-5):* the original text said `value_at()`
  and `value_of()` project the same record through `_answer`. They do not: they judge with `_judge` and `_conflicts`
  (declared slots only), and their field is the empty default. The answers and the field's value are as described
  below; only that sentence about the code path was wrong.
  - `value_at()` and `value_of()` apply declared slots only (`_value` → `_conflicts`).
  - They refuse a type with no declared slot, such as `office-holding`.
  - So their `constraint_support` is always `()`. This is documented in `_value` and tested.
- **Nothing else changes:** no other field, status, judgement or ordering. The E1 `holds` adapter
  (`evaluation/run.py`, `a_holds`) now also counts `constraint_support[].support` as cited evidence, so a recall can
  see it.

`Constraint.applies` is checked defensively in `holds()`. `_scope_rivals` only loads rivals for keys whose
constraint is established, on both paths, so a constraint that doesn't apply never reaches `holds()`'s record. The
filter is still tested directly on a synthetic record (section 3).

## 2. Tests (`tests/test_z_di19_constraint_support.py`, 15)

| Case | Test |
|---|---|
| established constraint cited, with evidence equal to its own `holds()` support and to `office_holders`' `conflict.constraint.support` | `test_a_constraint_dispute_cites_the_constraint` |
| additive: with the field turned off, every other field is identical | `test_every_other_field_is_unchanged` |
| no entry when there is no rival, or no constraint | `test_no_entry_without_a_conflict_or_without_a_constraint` |
| several accepted constraint attestations: all cited | `test_several_accepted_constraint_attestations_are_all_cited` |
| **disputed** constraint: not applied, not cited (the content is not disputed) | `test_a_disputed_constraint_is_not_applied_and_not_cited` |
| unaccepted constraint: not cited | `test_an_unaccepted_constraint_is_not_cited` |
| **perspective-dependent**: cited where the perspective accepts the constraint, not elsewhere | `test_constraint_support_follows_the_perspective` |
| **temporal visibility**: valid time before the constraint starts, and knowledge time before it was recorded | `test_valid_time_and_knowledge_time` |
| ended constraint: cited while it holds, with the deciding (end) attestation | `test_an_ended_constraint_is_cited_only_while_it_holds` |
| **superseded** constraint: cites its successor, not the superseded attestation | `test_a_superseded_constraint_cites_its_successor` |
| inherited and early-branched variant worlds | `test_an_inherited_constraint_is_cited_in_a_variant_world` |
| selective and full load agree | `test_selective_and_full_load_agree` |
| only applied attested constraints (synthetic record with a non-applying and a declared constraint) | `test_only_applied_attested_constraints_are_cited` |
| **declared functional slot**: no entry from `holds()`, `value_at()` or `value_of()` | `test_a_declared_slot_dispute_cites_no_constraint_attestation` |
| value readers refuse `office-holding`, so they never apply an attested constraint | `test_value_readers_never_apply_attested_constraints` |

**Mutation check** (by hand, then reverted). Each mutant was killed:

| Mutant | Tests failed |
|---|---|
| ignore `applies` | 1 |
| also cite declared constraints | 2 |
| always return `()` | 8 |

## 3. Regression (from the worktree at 7cb348d)

| Check | Result |
|---|---|
| Suite: 877 existing + 15 new = **892**, four configurations (selective on and off × profiles on and off), **twice** | 8/8 runs: 892 passed (`validate/suite-summary.txt`). The one warning is the TypeDB driver's own `SyntaxWarning`. |
| **106,752 reference answers**, kept upgraded (vs S7 and S5) and fresh (vs S8) databases | 92,577 identical, 14,175 **extended** (the new field only), **0 changed, 0 other**, on all three (`validate/diff-*.out.txt`) |
| Impact probe: answers with the field removed vs the baseline | **0 different**, 0 missing, 0 extra, on all three (`validate/impact-*.out.txt`) |
| Non-empty `constraint_support` in the reference answers | **4**, all `holds()` DISPUTED office-holdings (bea and cal at depot-7, in `org` and `org-plan-reorg`), each citing the `exclusive-office` attestation. 0 elsewhere. |
| **398 occurrence views**, upgraded and fresh | 0 differences in fields, judgements and role presentation (`validate/views-*.out.txt`) |
| **E1 revised** | **272/272** |
| E1 original | 267/272, identical to `main` 9fb7bc9 run the same day (`e1-original-main/`) |
| **ORG-011 evidence recall** (revised) | **0.667 → 1.0**: `x-sm` (the constraint attestation) is now found, and the `missing-evidence` failure is gone. Nothing else in E1 changed. |

About the "extended" count: every serialised `Answer` gains the key, including nested ones in `exists`,
`effects_of`, `occurrence_status` and `value_of`. It is empty everywhere except the 4 answers above. This is the
authorised additive difference.

The baselines S5, S7 and S8 are the reference snapshots of the performance phase. The F6 validation reproduced all
106,752 answers exactly against each of them (`di9-f6-correction/validate-f6-full/`).

**A difference that is not DI-19's:** the committed `benchmark/e1/results/` was frozen before R2 (LABS-1.053). There,
ORG-011 fails as `wrong-judgement`. Today, on both `main` and this branch, it fails as `error`, because R2 refuses
its original role names with `UnknownRoleError`. The score is 267/272 either way, and DI-19 changes nothing in the
original evaluation.

## 4. Not done (per LABS-1.060)

- The branch is not merged.
- DI-7 is not implemented.
- Identity semantics and the ontology are unchanged.
- The E2 harness (E2-D5) is not started.
