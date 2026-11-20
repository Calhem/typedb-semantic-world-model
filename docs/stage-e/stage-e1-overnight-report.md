# Stage E1 overnight report (LABS-1.051)

**Status: at the Stage E1 review gate.** DI-13 is merged; the Stage E1 benchmark and its evaluation harness are built
and run on `feature/stage-e1-benchmark` (not merged). No ontology, identity, multiplicity or foundational reasoning
semantics were changed, and no existing test or baseline was modified. Stage E2, Stage F and demo work have not begun.

**In plain terms.** 272 test questions about the world model were written, each with the answer the written rules
require, by four separate authors who never saw the code or the system's answers. The system was then asked every
question twice, once on each query path. It gave the expected answer to 267 of 272, the same on both paths, without
a single error. The five misses are not reasoning bugs. They show where the documentation is unclear:
- one place where two approved decisions disagree;
- one place where two specification documents need reconciling;
- one documentation mistake that makes the system give a silent "not yet known" to a mistyped question;
- two mistakes in the benchmark's own instructions.

Because the authors are AI models working inside this project, this is a development-tier result, not the sealed,
independent evaluation the project's evaluation plan calls for.

## 1. Commits
| What | Commit |
|---|---|
| DI-13 branch head, validated (format 3, closure) | `215d4ec` (`feature/pre-e-multiplicity`) |
| **Merge into `main`** (DI-13 + schema export format 3), pushed and verified | **`6364fdf`**; tree `445ca80`, identical to `215d4ec` |
| Stage E1 baseline | `df650f7` |
| Benchmark format, loader, checker | `49f0616` |
| Evaluation harness and its self-test | `5a655c9` |
| **Expected answers frozen** (272 questions, 30 fixtures), before any run | **`d0f0aa2`** |
| Harness evidence correction (after run 1) | `4ce343e` (the final results were produced by this commit) |
| This report, the results and the adjudication | the commit that adds this file, on `feature/stage-e1-benchmark` |

DI-13 merge validation (LABS-1.050):
- 689 tests in four configurations;
- 106,752 answers identical to the approved code's on the upgraded reference database;
- 398 occurrence views unchanged against the frozen baseline;
- the 106,752-answer snapshot of a freshly built database was omitted, as approved, and the omission is documented in
  the multiplicity report, section 6.5.

## 2. Benchmark coverage
`benchmark/e1/` ([README](../../benchmark/e1/README.md), [templates](../../benchmark/e1/TEMPLATES.md)): 272 questions,
30 fixtures, 15 templates over 15 public readers. Stage E baseline: [e1-baseline.md](e1-baseline.md) (versions, the
689-test regression baseline, the reader inventory, open issues).

| Category | Questions | Fixtures | Positive | Negative | Disputed / unknown / pending / not established / union | Adversarial | Templates |
|---|---:|---:|---:|---:|---:|---:|---|
| mechanical | 33 | 4 | 16 | 3 | 14 | 17 | holds 10, event_role 8, exists 6, parts 5, dependencies 4 |
| organisation | 31 | 4 | 16 | 3 | 12 | 13 | office_holders 10, capable 7, authorised 6, event_role 6, holds 1, officials 1 |
| laboratory | 36 | 2 | 15 | 7 | 14 | 19 | calibrated 22, value_at 6, event_role 5, exists 3 |
| temporal | 37 | 6 | 21 | 8 | 8 | 19 | holds 14, value_at 13, move 10 |
| conflict-provenance | 30 | 2 | 16 | 2 | 12 | 10 | value_at 9, holds 9, event_role 8, occurrence_status 4 |
| identity | 42 | 4 | 21 | 15 | 6 | 24 | same_thing 25, event_role 8, value_at 4, aliases 3, holds 2 |
| worlds-perspectives | 30 | 3 | 13 | 4 | 13 | 13 | holds 17, capable 11, value_at 2 |
| cross-domain | 33 | 5 | 17 | 4 | 12 | 17 | event_role 12, capable 5, office_holders 3, value_at 3, authorised 2, calibrated 2, same_thing 2, move 2, parts 1, aliases 1 |
| **all** | **272** | **30** | 135 | 46 | 91 (33%) | 132 (49%) | |

Every question records its expected answer, the evidence it must cite (and must not), a justification citing the
rule, an uncertainty note, difficulty (51 easy, 150 medium, 71 hard) and whether it is adversarial. Expected answers
include established, disputed, not holding / denied, pending, unknown and not established outcomes in every category
where the template allows them. The balance meets the withheld-evaluation specification's thresholds (non-definitive
gold at least 30%; adversarial at least 20%).

**How independence was protected:**
- Four model authors each wrote two categories. They worked only from the specification documents and the
  verbatim reader documentation, with instructions not to read `src/`, `tests/`, `probes/`, implementation reports or
  system output, and not to call any reader. The only command they ran was a format checker that loads fixtures
  through writers.
- Each author recorded its assumptions and ambiguities, and every question it chose not to write because the
  specification did not determine the answer (`benchmark/e1/notes/`, 4 files).
- The gold was committed and pushed (`d0f0aa2`) before the harness answered any question.

**Deviation:** 272 questions, against the requested 150 to 250. Each author wrote somewhat over the "about 25" per
category. None was trimmed, because choosing which to drop would have added a selection of my own on top of
independent work. They can be cut at review.

## 3. Evaluation infrastructure
| Part | What it does |
|---|---|
| `evaluation/loader.py` | loads a fixture into an isolated database (`wm-eval-<scenario>-<random>`, always dropped) through public writers only; 22 step kinds; knowledge-time marks; fixture ids become attestation ids, so evidence is named |
| `evaluation/check.py` | format checker (fields, templates, parameters, vocabularies, evidence ids, marks, worlds); `--load` loads every fixture; calls no reader |
| `evaluation/run.py` | runs every question on both query paths through one public reader per template, normalises answers to the template's fields, scores correctness (no partial credit), evidence recall, forbidden evidence and path agreement, classifies failures; writes `results.json` and `report.md`. Writes (`move`) run on a fresh copy per path |
| `tests/test_v_evaluation_harness.py` | 19 tests of the harness's mechanics (loader, every template's adapter on both paths, comparison rules, refusals) on its own smoke fixture; reads no benchmark gold |
| `benchmark/e1/results/` | final results, three earlier runs kept, the harness corrections between them, and the adjudication |

The run takes about 70 seconds for 272 questions on both paths (median 43 ms per question selective, 21 ms full; these
are timing figures from a shared machine, not benchmarks).

**Harness corrections after the first run** (documented in [results/README.md](../../benchmark/e1/results/README.md)):
- The first run found 23 evidence shortfalls caused by the harness: it read only a top-level `support` field.
- Three corrections taught it where each reader reports what an answer rests on.
- One intermediate rule was too broad. It counted claims a reader merely lists, such as a base-world claim overridden
  by a plan's stipulation, as citations, which produced 5 false "forbidden evidence" flags. It was tightened.
- No question, expected answer or judgement comparison changed. Correct answers were 267 of 272 in every run.

## 4. Results by reasoning category
Final run on `4ce343e`, gold `d0f0aa2` ([report](../../benchmark/e1/results/report.md)):

| Category | Questions | Correct | % | Incorrect | Evidence shortfall | Paths disagree | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| mechanical | 33 | 33 | 100 | 0 | 0 | 0 | 0 |
| organisation | 31 | 30 | 97 | 1 | 0 | 0 | 0 |
| laboratory | 36 | 33 | 92 | 3 | 1 | 0 | 0 |
| temporal | 37 | 36 | 97 | 1 | 0 | 0 | 0 |
| conflict-provenance | 30 | 30 | 100 | 0 | 0 | 0 | 0 |
| identity | 42 | 42 | 100 | 0 | 0 | 0 | 0 |
| worlds-perspectives | 30 | 30 | 100 | 0 | 0 | 0 | 0 |
| cross-domain | 33 | 33 | 100 | 0 | 1 | 0 | 0 |
| **all** | **272** | **267** | **98** | 5 | 2 | **0** | **0** |

- By template: every template is 100% except `holds` 51/53, `event_role` 45/47 and `calibrated` 23/24.
- Adversarial items: 129/132 correct. By difficulty: easy 51/51, medium 149/150, hard 67/71.
- Evidence: 176 of the 179 questions that name required evidence cite all of it. No forbidden evidence is cited.
- The selective and full-load paths agree on all 272 answers.

**How to read 98%:** the specification documents were written alongside the implementation by the same project, and
the questions test conformance to them. A high agreement is expected and shows that the implementation does what its
documentation says. It is not evidence of generalisation to unseen domains or to independently authored questions.

## 5. Correctness and provenance failures
From [adjudication.md](../../benchmark/e1/results/adjudication.md). No expected answer was changed.

| Id | Difference | Classification |
|---|---|---|
| ORG-011 | `holds` on office-holding with the role names the organisation notes give (`holder`, `office`, `context`) answers NOT_YET_KNOWN; the schema's roles are `classified`, `class`, `context` | **system finding:** readers accept role names a type does not have and answer silently; the module notes use the wrong names |
| LAB-025, LAB-026 | an unconstrained role (team sampling) lists the players of an unaccepted account too | **specification conflict:** MP-2 defines the union over *compared* accounts; ER-5's view lists every linked account's players, and no field gives MP-2's union |
| TEMP-017 | expected pending; the system answers not holding, INFERRED, by functional exclusivity | **specification gap:** v0.2 4.4 (its worked example) supports the system; increment B 2.4's table has no functional-exclusivity row |
| LAB-010 | expected not established; the calibration has no end, which the documented `calibrate` writer treats as until superseded | **benchmark documentation:** the benchmark README stated the core `attest` end rule as if every writer used it |
| LAB-034 (evidence) | the answer cites the restatement `move()` wrote to end the original claim | **harness limitation:** system-minted restatement ids are not mapped to fixture ids |
| X-003 (evidence) | the author also expects the claim that removes a holder | **benchmark definition:** "required evidence" for list answers is undefined |

**Confirmed reasoning defects: none.**
- Provenance held. No answer cited a forbidden, unaccepted or rejected claim.
- Both query paths gave identical answers, evidence included.

## 6. Remaining work and estimated effort
| Item | Effort |
|---|---|
| Decide MP-2 against ER-5 (the union of compared accounts), then a small reporting change or a documentation change | design decision; then about half a day |
| Validate role names in `holds`/`judgement` (refuse unknown roles) and correct the organisation module notes | half a day, with tests; changes reader input handling only, so it needs approval |
| Reconcile v0.2 4.4 and increment B 2.4 on functional exclusivity (one sentence and a test) | an hour |
| Benchmark fixes that do not touch gold: state writer-specific end defaults; map restatement ids to their originals; define required evidence for list answers | half a day |
| Trim to 250 or keep 272 | an hour, at review |
| A second author per category and Cohen's kappa on the expected answers | 1 to 2 days of authoring |
| Coverage the templates do not reach: frames and poses (`where`, `transform_between`), qualities and measurements, `changes`, `causes_of`, `effects_of`, process steps; and OBSERVED/PRESUMED and derivations, which are not implemented (D1, DI-7) | 2 to 3 days for templates and questions |
| The sealed, withheld evaluation (human authors outside this project, two per scenario, hashes only in the repository) | weeks; needs people and a decision |
| Stage E entry validation (LABS-1.048 item 4): re-freeze baselines, two suite runs, DI-9, budgets, controlled performance | about a day of runs |

## 7. Decisions requiring architectural review
1. **MP-2 against ER-5:** should the occurrence view report the union of compared accounts for an unconstrained role,
   or should MP-2's wording follow ER-5's listing?
2. **Role-name validation:** may readers refuse role names a type does not have? This changes input handling only,
   not semantics.
3. **Functional exclusivity in the canonical judgement:** confirm v0.2 4.4 (INFERRED false), and add the case to the
   increment B 2.4 table.
4. **Evidence tier:** accept this model-authored benchmark as development material, and decide whether to commission
   the sealed human-authored set (`docs/phase-1c/05-withheld-evaluation-spec.md`, 5.6).
5. **Benchmark size:** keep 272 questions or trim to the requested 250.
6. **Required evidence for list answers** (X-003): include the claims that exclude a candidate, or only those that
   support the listed ones.
7. **Merge `feature/stage-e1-benchmark` into `main`:** it adds files only, and the regression suite passes, figures in
   the addendum below.

### Regression check of this branch
The full suite at `4ce343e`, from a separate worktree, in the four configurations: **708 passed** in each (689 existing
+ 19 harness tests): WM_SELECTIVE=1 with WM_PROFILES 0 and 1, WM_SELECTIVE=0 with WM_PROFILES 0 and 1
([suite-matrix.out.txt](../../benchmark/e1/results/suite-matrix.out.txt)). The only warning is the TypeDB driver's
`SyntaxWarning`, printed when a fresh environment compiles it. No test or evaluation database was left behind. No
existing test, baseline or reference database was changed.
