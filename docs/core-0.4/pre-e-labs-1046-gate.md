# LABS-1.046 review gate: consolidation merge and pre-Stage E corrections (designs only)

**Status:** at architectural review. No correction is implemented, DI-12, DI-13, DI-15 and DI-16 stay open, and
Stage E has not started.

## 1. Consolidation merge
- Approved head `1466433` verified unchanged on `feature/pre-e-consolidation`; merged `--no-ff` into `main` as
  `bf60c1f`, pushed, and the remote verified with `git ls-remote`.
- Full regression suite on `bf60c1f` from a clean worktree: **600 passed** in each of the four configurations
  (selective on / off × profiles on / off), no leftover test databases.
- **398-view baseline** (`probes/pre_e_d_occurrence_baseline.json.gz`, `--compare`) on both reference databases (old-built
  and upgraded, new-built): 398 of 398 views, 0 changes to existing fields, 0 judgement changes; the same 8
  role-presentation differences recorded at increment D.
- **106,752-answer baseline:** a snapshot of the database built by `bf60c1f`: 106,752 of 106,752 answers identical to
  the frozen baseline after masking attestation ids and clock times; and, reader by reader against the snapshot taken
  on the previous `main` (`9464403`), 106,752 identical, 0 extended, 0 changed.

## 2. Deliverables on `feature/pre-e-corrections-design`
| Item | Document | Evidence |
|---|---|---|
| DI-12 and DI-15 (and DI-16's remedy): contextually established identity | [pre-e-identity-design.md](pre-e-identity-design.md), decisions ID-1 to ID-10 | `probes/pre_e_identity_cases.py` (28 checks; 6 change under the design) |
| DI-13: several participants per role in one account | [pre-e-multiplicity-design.md](pre-e-multiplicity-design.md), decisions MP-1 to MP-5 | `probes/pre_e_di13_cardinality.py` (TypeDB behaviour), `probes/pre_e_di13_rule.py` (cases M1 to M12) |
| DI-16 clarification: exact register entry, reproduction, proposed decision | [pre-e-di16-clarification.md](pre-e-di16-clarification.md) | `probes/pre_e_di16_repro.py` |
| Stage E preparation: fresh Core 0.3 workload baseline (P-1) | [pre-e-performance-baseline.md](pre-e-performance-baseline.md) | [bench-pre-e-baseline/](bench-pre-e-baseline/) (20 alternating runs) |

The Stage E entry-criteria framework of [pre-stage-e-consolidation.md](pre-stage-e-consolidation.md) section 4 is
retained unchanged.

## 3. Decisions requested
1. Identity: approve ID-1 to ID-9 (and decide the optional ID-10), or amend.
2. DI-16: adopt option (a) as specified by ID-2, ID-5 and ID-6.
3. Multiplicity: approve MP-1 to MP-5, or amend.
4. Performance: accept the baseline; decide how the noise is to be reduced before the 9.4 thresholds are judged
   (three of them are not demonstrable at the current variation).
