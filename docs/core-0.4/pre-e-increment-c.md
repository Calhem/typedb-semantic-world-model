# Pre-Stage E correction, increment C: one aggregation rule (DI-6)

**Status: implemented under LABS-1.040 on `feature/pre-e-c-aggregate-status`; awaiting review, not merged.**
Approved design: [pre-e-increment-c-design.md](pre-e-increment-c-design.md) at `b1c45c4`, decisions C-1 to C-6.
Increment D (DI-2) and Stage E have not begun. The foundational ontology, the schema and the per-content judgement of
increment B are unchanged.

## What changed
**Two core rules** (`src/worldmodel/judgement.py`), both over canonical records (`ContentJudgement`), never over
status labels:
- **`combine(records, any_found)`: rule Q**, for one question answered by several holdings:
  1. DISPUTED if any holding is disputed, or if one is established while another is denied by an accepted denial
     (`support` empty: precedence is never applied across a conflict);
  2. otherwise, if any holding is established: holds, and the status is the core rule (`answer_status`) over the
     **union of the deciding claims of every established holding**;
  3. otherwise, if any is denied or expired: does not hold ("denied" if any is denied, else "expired"), and the status
     is the core rule over the union of the denied and expired holdings' deciding claims;
  4. otherwise undecided: UNKNOWN if anything was found, NOT_YET_KNOWN if nothing was; "not yet effective" if a
     holding is, else "not established".
  The union is keyed by attestation id, and the rule depends only on the set of bases, so neither the order of the
  records nor a claim passed twice can change the answer. Each holding keeps its own judgement, reasons and
  pending claims in the answer.
- **`collection_status(items, conflict)`: rule C**, for a report over distinct items: DISPUTED on a conflict or a
  disputed item; **None** when items are established without conflict; UNKNOWN when items exist but none is
  established; NOT_YET_KNOWN when there are none.

**Temporal distinctions are those of increment B, unchanged.** An explicit denial is "denied"; an established end is
"expired"; an unreviewed or pending claim is undecided; a holding whose end is unknown (no end, no commitment to hold
until superseded) is never expired: it is "not established" (UNKNOWN), or "not yet effective" before it begins.

**Readers.**
- `capable`, `authorised`, `calibration_status`: rule Q replaces `_combine` (which copied the first holding's
  status). Each gains **`support`**: the sorted ids of the claims its status rests on. No field is removed.
- `office_holders`: rule C replaces `_overall`. `holders`, `exclusive`, `conflict` and each appointment's own status
  in `appointments` are unchanged.
- `changes`: a single-value slot's state takes its status from the claims deciding the **values held** (as
  `value_of`), no longer also from accepted denials of other values (`dynamics.py`, `state_at`).
- Inheriting readers change only through the reader they call: `is_agent`, `check_action` and
  `measurement_calibration` embed the whole answer (so they gain `support`); `agency_report` and `official_act` copy
  selected fields (unchanged).
- The internal record a holding is built from (`_record`) is never returned: every path to output drops keys that
  begin with `_`.

## How the answers were checked
1. **Before and after on one database.** The reference database (`wm-probe-pre-e-b`, rebuilt from merged `main`) was
   read by every reader with the merged `main` code (`d9d873a`) and with the new code: 106,752 answers each, over 11
   worlds, every perspective and knowledge time the snapshot holds (`probes/pre_e_b_snapshot.py`). Same database, so
   no masking is needed.
2. **Compared** with `probes/pre_e_b_diff.py`. Output: `probes/pre_e_c_diff.out.txt`.

## Answer changes
**Exactly as forecast at the design gate.** Every changed answer is one of the 14 forecast `office_holders` answers.

| Reader | Answers | Identical | Fields only added | Changed |
|---|---:|---:|---:|---:|
| `office_holders` | 20 | 6 | 0 | **14**: 13 ASSERTED → None, 1 STIPULATED → None (7 in `org`, 7 in `org-plan-reorg`) |
| `capable` (every perspective) | 17,605 | 0 | 17,605 (`support`) | 0 |
| `authorised` | 20 | 0 | 20 (`support`) | 0 |
| `calibration_status` | 3,575 | 0 | 3,575 (`support`) | 0 |
| `check_action` | 74 | 19 | 55 (an actor's `support`) | 0 |
| `measurement_calibration` | 80 | 62 | 18 (`support` in `attested`) | 0 |
| every other reader, `changes` included | 85,378 | all | 0 | 0 |

The 6 unchanged `office_holders` answers are 4 with no holder (UNKNOWN) and 2 DISPUTED. As forecast, the reference
worlds never give one question established holdings with different statuses, and hold no accepted denial of a
single-value slot value, so rule Q and the `changes` correction change no status there: the executed examples (E1 to
E10) are what exercise them, and they are now permanent tests.

## Points decided in implementation
1. **Duplicate representations.** Two attestations of one content (the same claim recorded twice) are two claims of
   one holding. Both are listed in `support` (each once), and since the rule depends on the set of bases they cannot
   change the status. Passing the same record twice, or the records in any order, gives an identical answer
   (`combine`, tested directly).
2. **`support` is empty** for DISPUTED and undecided answers: no status rests on deciding claims there. The evidence
   stays in the listed holdings.
3. **Held values only in `changes`.** A disputed slot is DISPUTED whatever its support, so only the values held
   (judgement true) contribute to a slot's status, as in `value_of`.

## Tests
**New:** `tests/test_r_aggregate.py`, 42 tests (each on both query paths):
- the 12 executed examples of the design (E1 to E10 and E7b), including the E1 mirror cases, at the plan and in the
  actual world, for the system and audit perspectives;
- mixed STIPULATED, ASSERTED and INFERRED support; explicit denials and expired holdings (together and alone);
  conflicts staying DISPUTED; pending and unreviewed holdings listed but never folded in; an unknown end never an
  expiry; an earlier knowledge time; hypothetical worlds;
- `support` checked against the claims it lists (the status is the core rule over exactly those);
- **order and naming cannot change an answer**: renamed certificates (E7/E7b), records passed twice or shuffled,
  and every reader with the query results reversed and shuffled;
- `office_holders` invents no collective status (several holders, mixed or equal statuses, a single holder); UNKNOWN
  and NOT_YET_KNOWN unchanged; `offices_of` and `employment` keep each item's status;
- `changes` and `value_of` agree on a slot (E10);
- the inheriting readers (`is_agent`, `check_action`, `official_act`, `measurement_calibration`, `agency_report`)
  report exactly what the reader they call says.

**Changed expectations** (intentional, rule C): `office_holders` status None in `tests/test_m_d2_organisation.py`
(5 assertions) and `tests/test_q_judgement.py` (3). The executed examples (`probes/pre_e_c_examples.py`) now assert
the new behaviour.

**Full suite:** 529 tests (487 after increment B, 42 new). Every configuration was run twice at `90bf4d3`: both
query paths (selective and full load), each with and without core protection, which installs all three profiles.
529 passed in each of the 8 runs (9 to 16 minutes each), and no test database was left over.

## Cost
`probes/pre_e_b_read_bench.py --more` (now also `changes` and `authorised`), on the same reference database; three
alternating rounds of the code before increment C (`d9d873a`), the new code, and the new code with attested
constraints removed (`--no-attested`), 5 calls per case. Summary: `probes/pre_e_c_perf_summary.py`; output
`probes/pre_e_c_perf.out.txt` and `.json`. Since `d9d873a` already applies office exclusivity, old → new is the
aggregation alone, and no-exclusivity → new is the exclusivity cost.

| Reader | Cases | Queries: old / new / new without exclusivity | Sum of median ms: old / new / new without exclusivity |
|---|---:|---|---|
| `capable` | 33 | 774 / 774 / 774 | 1,033 / 1,012 / 1,001 |
| `authorised` | 4 | 86 / 86 / 86 | 120 / 116 / 117 |
| `calibration_status` | 4 | 91 / 91 / 91 | 136 / 135 / 131 |
| `office_holders` | 4 | 218 / 218 / 172 | 402 / 309 / 566 |
| `offices_of` | 4 | 328 / 328 / 227 | 794 / 786 / 619 |
| `changes` | 33 | 2,768 / 2,768 / 2,644 | 6,323 / 6,018 / 5,058 |
| `facts_about` | 33 | 968 / 968 / 915 | 4,885 / 4,775 / 3,690 |
| `parts`, `occurrence_status`, `causes_of`, `interpretations`, `provenance` | 77 | 4,387 / 4,387 / 4,387 | 8,945 / 8,612 / 8,022 |

- **The aggregation costs nothing measurable.** Not one query is added on any reader or subject; the old and new
  times agree within run-to-run variation. The deciding claims were already in each record.
- **Every extra query is office exclusivity** (recorded under DI-9 in LABS-1.039), confined to the subjects with an
  appointment under an exclusive office (Bea, Cal and depot-7, in Acme and its plan). Newly measured: `changes`
  pays it too, at each boundary of the subject's timeline: 10 to 66 queries per call, the largest
  `changes(depot-7)` in the plan (209 → 275 queries). Added to DI-9.
- **Times are noisy.** In this session the exclusivity subjects were slower than in LABS-1.039 for the old and the
  new code alike (for example `facts_about(bea)`: about 133 ms both, against 25 ms without exclusivity; the query
  counts are the same as before), and `office_holders` without exclusivity came out slower despite fewer queries.
  The query counts, identical in every round, are the reliable comparison.

## Limitations
- `support` lists claim ids. A reader that needs each claim's detail reads it from the holdings or `explain`.
- A slot's status in `changes` and `value_of` rests on held values only: an accepted denial of another value is
  visible through the content tracks and the evidence, not through the slot's status (by design, C-6).
- The office-exclusivity cost (DI-9) is unchanged by this increment.

## Not changed
Per-content judgement (increment B), `holds`, `value_of`, every collection's per-item statuses, `offices_of`,
`employment`, `provenance`, `interpretations`. DI-2 (increment D), DI-3, DI-4, DI-7, DI-9, DI-10 and DI-12. The
foundational ontology and the schema. Stage E has not begun.

## After the merge (LABS-1.041)
- **Merge.** The approved head `cc14034` was unchanged, local and remote, and the tracked files clean; merged with
  `--no-ff` into `main` as `bf8bb34` (pushed and verified on the remote).
- **Regression on merged `main`.** 529 passed in each of the four configurations (both query paths, with and without
  core protection, which installs all three profiles), and no test database was left over. Each run reports one
  warning: a `SyntaxWarning` from a docstring in the TypeDB driver package, printed when Python first compiles that
  file in a freshly installed environment; it does not come from this project's code, and the package versions are
  the same as in the development checkout.
- **Reproducibility.** The reference database was rebuilt from merged `main` (`wm-probe-pre-e-d`) and every reader
  re-read: compared with the increment C snapshot (`wm-probe-pre-e-b`, new code), 106,752 of 106,752 answers are
  identical once attestation ids and system-clock times are masked (`probes/pre_e_b_repro_check.py`, output
  `probes/pre_e_c_repro_check.out.txt`). The older probe database was then dropped; `wm-probe-pre-e-d` is kept as the
  baseline for increment D.
- **Performance findings** stay under DI-9 unchanged (the office-exclusivity overhead, including `changes`); nothing
  was optimised and the canonical judgement mechanism was not changed.
