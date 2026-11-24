# Stage E2 harness: review

**LABS-1.061, 24 November 2026.** Branch `feature/e2-harness`, from `main` 612bc6e (DI-19 merged).
Records: [e2-harness/](e2-harness/).

| Commit | Content |
|---|---|
| ee5ed38 | E2 decisions finalised (F-1 to F-4, [stage-e2-decisions.md](stage-e2-decisions.md) section 7) |
| 38c7b41 | the harness: GAP-HARNESS-1 to 4, with 47 tests |
| (this commit) | this review and its records; a fix in `worker.py` so that a failed reload after a stopped question is recorded as a `harness-error` on that question and doesn't abort the run |

**At review. Not merged.**

**Not written:**
- the E2 reader contracts;
- E2 questions, fixtures, calculation sheets or gold answers.

**Unchanged:** no reader, ontology or identity semantics changed. `src/` is untouched.

## 1. What was built

| Gap | What it was | What the harness now does | Where |
|---|---|---|---|
| GAP-HARNESS-1 | `attest` / `deny` / `correct` steps took no `params` | they accept `params`, so a fixture can write positions, frame transforms and quality ranges directly | `evaluation/loader.py` |
| GAP-HARNESS-2 | no fixture steps for the E2 writers | 14 new steps (listed after this table) | `evaluation/loader.py` (`E2_OPS`) |
| GAP-HARNESS-3 | no templates or extractors for the new readers | 22 reader templates, the plan runner, comparison, scoring and reporting (section 2) | `evaluation/e2/` |
| GAP-HARNESS-4 | reader-docs.md lacked the new readers | `benchmark/e2/spec/reader-docs.md`, generated from the docstrings, with a `--check` mode and a test that keeps it current | `evaluation/e2/reader_docs.py` |

**The 14 new fixture steps:** `position`, `relate_frames`, `anchor_frame`, `define_unit`, `define_quality_kind`,
`measure`, `claim_cause`, `claim_effect`, `describe_occurrence`, `record_event`, `declare_existence`,
`create_thing`, `destroy` and `interpret`.

**How the new steps behave:**
- Each step calls the public writer of the same name.
- An effect claim names its proposition **by content** (type, roles, params), so a fixture never needs a proposition
  id. This closes the "initiates/terminates need a proposition id" part of GAP-HARNESS-2.
- A step that refers to an earlier claim (`supersedes`, `ends`) names the earlier step.
- A measurement's attestations (content, activity account, `produced`, `reports`) are all named after its step.
- E1 fixtures use none of these steps, so they load exactly as before (section 4).

**The 22 reader templates:**
- **Spatial and frames (S, F):** `transform_between`, `where`, `poses`, `frame_info`.
- **Measurement (M):** `measurements`, `compare_measurements`, `measurement_calibration`, `calibration_status`,
  `convert`.
- **Causation (C):** `causes_of`, `effects_of`, `explain`, `changes`.
- **Process (P):** `process_steps`, `before`, `interval`.
- **E1 readers, for multi-step (X) plans:** `holds`, `value_at`, `facts_about`, `occurrence`, `occurrence_status`,
  `office_holders`.

That covers every reader in design 5.4, plus `interval` and `calibration_status` (design section 2).

## 2. How the approved requirements are met

| Requirement (LABS-1.061 item 11) | Implementation |
|---|---|
| Multi-step reader execution | `plan.py`: a question's `plan` is a list of steps that run in order on one loaded scenario and one path. See the notes after this table. |
| Numeric answer comparison | `values.matches`: absolute tolerance per answer path, applied to every number below it; rotations as unit quaternions within an angle (`{"rad": tol}`; q and −q are equal). Without a stated tolerance, numbers must be exactly equal: the harness never picks a tolerance. |
| Required, admissible and forbidden evidence | `score.evidence`, on the supporting evidence the reader template extracts (section 5.1). See the notes after this table. |
| Separate A/H/G classification and reporting | the class is checked before a run (a gap id exactly when G). The report summarises A and H apart. G probes never enter a family's scores and have their own section: each probe's gap, reader(s), what was returned, and the result. |
| Question-level latency and budget | `worker.py` runs each scenario in a child process. The parent stops a selective-path question at the **5 s budget** (it kills the child, deletes the child's database, and loads a fresh child for the next question) and records `timeout`. Latency is the readers' own time over all steps of the plan; a stopped question counts at the budget. |
| Selective and reference-path comparison | every scored question runs on the selective path, then on the full-load path under a separate **reference limit** (default 60 s, no target). Agreement is `agree`, `disagree` or `unverified`, with the reason (section 3). |

**Multi-step plans.**
- A parameter can come from an earlier step's answer: `{"from": "<step>", "path": "<answer path>"}`.
- The path language covers fields, indices, `[*]` (map over a list) and `[field=value]` (the one list item whose field
  equals the value, so a plan never depends on the order a reader lists things in).
- Every step's answer is recorded with its own expected fields, and `first_wrong_step` names where a wrong answer began.

**Evidence scoring.**
- **Recall:** required ∩ cited / required.
- **Precision:** admissible ∩ cited / cited. Required evidence always counts as admissible; a cited id that names no
  fixture step is never admissible.
- **Forbidden:** citing a forbidden attestation is its own failure.

**Item 12: the failure kinds stay distinguishable.** `score.py` records each kind separately:
- `timeout`;
- `harness-error`;
- `execution-error` (a reader exception);
- `plan-error` (a reference that cannot be resolved);
- `unexpected-refusal`;
- `incorrect`;
- `fabricated-derivation`;
- `forbidden-evidence`, `inadmissible-evidence` and `missing-evidence`.

How they combine:
- `failures` lists every kind present, so one never hides another; `failure` is the first in that order.
- `correct` is false only for the answer failures (the first six). Evidence and derivation failures are reported
  beside correctness, because E2-D6 scores them as separate criteria.

**Fabricated derivations (E2-D6).** A reader template lists the derivations an answer presents. Today these are the
`frame-transform/v1` derivations of `where` and `transform_between`; a generic detector also finds any
`{"rule", "premises"}` object. A derivation is fabricated if:
- its rule is not one the model records;
- it has no premises; or
- a premise is not an attestation recorded in the scenario.

## 3. Decisions F-1 to F-4, as applied

| Decision | Harness behaviour |
|---|---|
| F-1: 1 s p95 and 5 s budget on the selective path only | the budget applies only to the selective run. The p95 is over all scheduled questions, with a stopped question at the budget, and is marked as a lower bound (`+`) when anything timed out. |
| F-2: full-load latency recorded apart; agreement mandatory; incomplete reference runs are unverified | the full-load p50 and p95 are reported in their own columns. A reference run that passes its limit, fails in the harness, or is not run (because the selective path timed out) gives `unverified` with the reason, never `agree`. |
| F-3: two ways of reporting correctness | **% of completed:** correct / questions that finished within the budget. **% within budget:** correct / all scheduled A and H questions, so a timeout stays in the denominator. The per-family correctness criterion uses the second. |
| F-4: identity questions in X, reported separately | `subset: "identity"` is allowed only in family X. Those questions count in X and are summarised again as "X, identity subset". |

An execution error **completes** (it finished within the budget) but is not correct. On both paths at the same step,
it agrees; on one path only, it disagrees.

## 4. Validation

Run from a separate worktree at 38c7b41 (records in [e2-harness/](e2-harness/); the script is `validate-e2h.sh`).

| Check | Result |
|---|---|
| Full suite: 877 existing + 15 DI-19 + **47 new = 939**, four configurations (selective on and off × profiles on and off) | **939 passed** in each of the 4 runs (`suite-summary.txt`). The one warning is the TypeDB driver's own `SyntaxWarning`. |
| After the `worker.py` fix (this commit): harness and E1 harness tests, four configurations | 68 passed in each |
| E1 format check, with every fixture loaded through the extended loader | 272 questions, 30 fixtures, **0 problems** |
| **E1 original evaluation** | **267/272**, identical in every scored field to the same evaluation on `main` (`e1-compare-original.txt`) |
| **E1 revised evaluation** | **272/272**, identical in every scored field to the DI-19 validation run (`e1-compare-revised.txt`) |
| `src/` and `schema/` unchanged since `main` 612bc6e | `git diff --stat 612bc6e -- src schema` is empty |

**About the committed E1 results.** Both committed result files predate later approved changes, and each differs from
today's run on ORG-011 only:
- `benchmark/e1/results/` (original): frozen before R2 (LABS-1.053). ORG-011 fails there as `wrong-judgement`; today
  it fails as `error` (R2 refuses its role names). The score is 267/272 either way.
- `benchmark/e1/results-revised/`: from before DI-19. ORG-011 was `missing-evidence` there; since DI-19 its recall is
  1.0.

Neither difference comes from the harness, and the committed files are left as they are (frozen history).

The 106,752 reference answers and 398 occurrence views were not re-run: no reader or library code changed, and the
loader change only adds fixture steps that the reference databases never use.

## 5. Limitations (for the reader-contract review)

### 5.1 Provisional extractors: the contracts must confirm them
The supporting evidence each template cites is the harness's reading of the documented outputs. The contracts
(E2-D3) must confirm or correct each one before questions are authored. Precision at 100 % depends on it.

| Reader | Cited as supporting evidence |
|---|---|
| `holds` | `support`, `conflicts`, and `constraint_support[].support` (as E1, with DI-19) |
| `value_at` | `support` |
| `where` | each candidate's `position_support` and the `support` of every transform on its chain. **Not cited:** `alternatives`, `incomparable` |
| `transform_between` | the `support` of every transform on the shortest chain |
| `poses` | each pose's `support` |
| `frame_info` | the `support` of the parent and child transforms |
| `process_steps` | each step's `support` |
| `facts_about` | each entry's `support` |
| `measurements` | the attestation of each **usable** value |
| `compare_measurements` | the attestations of the compared measurements. **Not cited:** alternatives, statements |
| `measurement_calibration` | the usable measurement, and the calibration's deciding support (as E1's `calibrated`) |
| `calibration_status` | the calibration's deciding support (as E1's `calibrated`) |
| `causes_of` | the usable attestations of **accepted** claims |
| `effects_of` | the usable attestations of accepted claims, and the `support` of the judged state before and after |
| `explain` | the answer's `support`, and the accepted causal claims about each initiating event |
| `changes` | the `support` of both sides of each transition |
| `occurrence_status` | its answer's `support` |
| `office_holders` | as E1 |
| `interval` | the account attestation it uses |
| `occurrence`, `before`, `convert` | nothing |

Questions for the contracts:
- Should `where` also cite the alternatives it shows?
- Do `changes` transitions rest on both sides?
- Should `explain` cite the initiates claims themselves? (It doesn't report their ids today.)

### 5.2 Other limitations
- **Derivation check is structural.**
  - The harness checks that a presented derivation names a recorded rule and recorded premises. It doesn't recompute
    the conclusion; that is the numeric gold's job (E2-D4).
  - Until DI-7, only `frame-transform/v1` is a recorded rule.
- **Plans are linear.**
  - A step can take an earlier answer's value but cannot compute a new one (no arithmetic or set operations between
    steps).
  - A question that needs a computed intermediate is a gap (GAP-MULTI-1), not harness work.
- **Write templates.** E1's `move` (a write on a fresh copy) has no E2 equivalent. The design's E2 families need none.
- **Names of library-written attestations.**
  - Evidence is named through E1's restatement rule (C3): an `end()` or `move()` record is named after the step it
    restates.
  - An attestation the library writes that restates no step (for example the system's denials in `destroy`) has no
    name, so citing it counts as inadmissible. The contracts should say whether that is right.
- **Timing.**
  - The budget is enforced on the parent's wall clock, from sending the plan to receiving the answer. That includes a
    few milliseconds of inter-process overhead.
  - The reported latency is the readers' own time.
  - Process start-up and fixture loading are outside both. A fixture is loaded again after every stopped question.
- **Probes** run on the selective path only. They accept `UNKNOWN`, `NOT_YET_KNOWN` or an explicit refusal (a
  `ValueError` from the reader), at the answer path the probe names (default `status`).
- **Refusals.** Any `ValueError` (including `UnknownRoleError`) counts as an explicit refusal. A question expecting an
  answer reports it as `unexpected-refusal`; one expecting a refusal says `{"refused": true}`.
- **Intermediate answers count.** A multi-step question is correct only if every step that states expected fields
  matches, not just the last.
- **Not implemented here:** the authoring-phase tools. These are two-author agreement (kappa), the calculation-sheet
  recomputation, and the check that gold was frozen before the first run (E1 checked this by commit order). They
  belong to authoring and to the run report.

## 6. Tests (47; synthetic fixture and self-test readers only)

`tests/fixtures/e2/harness-synthetic.json` uses every new step once:
- frames A→B→C, with C rotated 90° and anchored, and an unrelated frame Z;
- a derived pose and a disputed pose, plus a raw `params` attestation;
- two measurements in kg and g;
- unit definitions, including an affine (°C) unit;
- two process steps with a causal claim and an effect claim.

The self-test readers (`evaluation/e2/selftest.py`, available only with `selftest=True`) misbehave on purpose: they
echo evidence and derivations, sleep (on one path or both), raise, or answer differently on each path.

| Area | Tests |
|---|---|
| Normalisation, paths (including `[field=value]`), comparison (tolerances, quaternion sign, multisets, ordering, strict types) | 3 |
| Question checker: a valid plan and a probe accepted; 17 malformed questions refused; a probe accepting a definite answer refused; a template exists for every E2 reader | 20 |
| Scoring without a database: correct; **incorrect**; evidence failures listed together; **fabricated derivations** (unknown rule, unrecorded premise, no premises); **timeout**, execution error, plan error, refusal (expected and unexpected), harness error; agreement states; probe outcomes | 7 |
| Reporting: **timeouts in the denominator**, both correctness rates, censored p95, identity subset, probes apart, criteria verdicts; nearest-rank percentile | 2 |
| Loader and plans on the database: every new step loads and is named; attest `params` reach the model; `where` evidence and derivation extraction on a derived pose; transform numbers and rotations; a three-step plan fed by `[record=...]`; plan errors (no item, not a time); both paths answer alike; malformed step refused | 8 |
| **End to end through child processes** (budget 3 s): every failure kind detected (15 scored questions); the budget **stops** a 6 s question and the next question is answered by a fresh child; reference-path timeout gives unverified; disagreement detected; probes pass, fail and not-callable; report; a run refuses questions with problems | 5 |
| reader-docs current; command line writes results.json and report.md | 2 |

## 7. Readiness for reader-contract approval

The harness is ready for the contracts step (E2-D3). It can express every H-class fixture and answer in design
section 3 once the contracts fix the details. **The contracts need to settle the following for each reader:**
1. the output fields a question may expect, and their vocabulary;
2. which output lists are ordered (use `ordered`) and which are not (compared as multisets or picked by
   `[field=value]`);
3. what is cited as supporting evidence (section 5.1);
4. what counts as a derivation it presents;
5. which errors are explicit refusals.

After approval, in order:
1. confirm or correct the template table (a harness-only change, re-tested);
2. author the fixtures, questions, calculation sheets and gold, as design 5.3 says;
3. freeze them;
4. run.

## 8. Not done (per LABS-1.061)

- The E2 reader contracts, questions, fixtures, calculation sheets and gold answers.
- Any reader, ontology or identity change.
- The merge of `feature/e2-harness`.
