# LABS-1.065 review package: E2 corpus authoring and gold freeze

**28 November 2026.** Branch `feature/stage-e2-authoring`, not merged.

**Stopped for review** after the freeze. Not yet done:
- loading any E2 fixture;
- executing any E2 question;
- merging the authoring branch;
- implementing any deferred correction.

**What kind of evaluation this is.** E2 is a development-tier specification-conformance and reasoning evaluation. Its
authoring is procedurally isolated (section 4). It is **not** externally independent or sealed.

## 1. Baseline and freeze

| Item | Value |
|---|---|
| Contracts branch, verified on the remote | `feature/e2-reader-contracts` at `05e08e0` |
| `main` before the merge | `5ded39a` |
| Merge into `main` (pushed and verified) | `d06316c`, a `--no-ff` merge; its tree is identical to `05e08e0` |
| **Executable E2 baseline** | **`d06316c`**. Its executable production implementation is unchanged from `5ded39a` (AST check: no executable or schema difference) |
| Authoring branch | `feature/stage-e2-authoring`, from `d06316c` |
| **Freeze commit** | **`1da2020`** (pushed and verified) |
| Freeze manifest | [benchmark/e2/FREEZE.json](../../benchmark/e2/FREEZE.json): SHA-256 of 201 files |
| Corpus hash | `b98c43da95c1538b5fc5d123bf5bc27f717984a229f18c2f3781a7920fa8d4f6` |
| Author pack | v1.0 at `8dafcd5` (authors); v1.1 at `5d04f99` (verifiers, adjudicators, replacement author) |

**What the manifest covers:**
- the fixtures and questions;
- the author and verifier calculation sheets;
- the verification status and resolutions;
- the coverage matrix and coordination record;
- the quarantine and desirability records;
- author pack v1.1;
- the evaluation configuration: `blocked.json`, the contracts, the loader and `evaluation/e2/*.py`.

**Commits** (each pushed and verified):

| Commit | Content |
|---|---|
| `d06316c` | the contracts branch merged into `main` |
| `8dafcd5` | author pack v1.0 frozen; baseline record; fixture time windows |
| `d5e9b1b` | coordinator allocation, assignments and author prompt, with hashes, before authoring |
| `5d04f99` | authored corpus (raw and normalised); pack v1.1; `account_again`; tooling |
| `13c2cdf` | blind verification and adjudication. Its message says "147" adjudicated items; the correct count is 128 (section 6) |
| `1da2020` | replacements merged; corpus frozen |

## 2. Final corpus allocation

| Family | Scored | of which targeted | Identity subset | Probes | Fixtures |
|---|---:|---:|---:|---:|---:|
| S spatial transformations | 25 | 3 | — | 5 | 3 |
| F frames | 35 | 4 | — | 6 | 4 |
| M measurements | 35 | 6 | — | 7 | 4 |
| C causal relationships | 30 | 6 | — | 9 | 3 |
| P process steps | 25 | 3 | — | 6 | 3 |
| X multi-step | 30 + 12 | 6 | 12 | 4 | 5 + 2 identity |
| **total** | **192** | **28** | **12** | **37** | **24** |

**Total: 229 cases.** The classification is:
- every scored question is class H, since no E2 question was expressible by the E1 harness alone (design §3);
- every probe is class G.

**Case types** (scored):

| positive | negative | disputed | unknown | refusal | adversarial |
|---:|---:|---:|---:|---:|---:|
| 75 | 34 | 43 | 33 | 7 | 156 (81 %) |

**Other variation:**
- 65 multi-step questions;
- 32 using `as_of`;
- 22 using a non-system perspective;
- variant worlds in S, F, P and X (none in M, C or the identity subset);
- uncertain windows in M, C, P and X;
- 43 numeric questions.

**Reader steps (scored):**

| Reader | Steps |
|---|---:|
| `holds` | 54 |
| `where` | 45 |
| `transform_between` | 26 |
| `process_steps` | 24 |
| `measurements` | 19 |
| `before` | 16 |
| `measurement_calibration` | 13 |
| `causes_of` | 12 |
| `compare_measurements` | 11 |
| `changes` | 11 |
| `occurrence_status`, `occurrence`, `explain` | 9 each |
| `effects_of` | 8 |
| `convert`, `facts_about`, `value_at` | 6 each |
| `interval` | 5 |
| `office_holders` | 4 |
| `frame_info` | 2 |

**Adjustments to the approved allocation** (recorded in `coordination.json` `amendments`):
1. **Refusals: 7, not the matrix's 12.** The S, F and P readers have no established refusal, so their planned refusal
   cases became positive cases.
2. **Targeted questions by DI, not by decision (28 kept).**

   | DI | Questions | DI | Questions |
   |---|---:|---|---:|
   | DI-24 | 2 | DI-31 | 2 |
   | DI-25 | 3 | DI-32 | 3 |
   | DI-26 | 2 | DI-33 | 1 |
   | DI-27 | 2 | DI-34 | 2 |
   | DI-28 | 3 | DI-35 | 4 |
   | DI-30 | 1 | DI-36 | 3 |

   DI-29 has none: its eligible components are exercised inside other targeted questions.
3. **X-021 quarantined and replaced** by X-031 (slot T-X4, now a declared-slot rival-value situation). X's case types
   shift by one, from positive to disputed.
4. **X-112 quarantined and replaced** by X-113 (identity, positive).

## 3. Coverage

**Competency coverage.** Every competency form in each assignment is met exactly, and the counts are checked
statically:
- **S:** S1–S6, the frame-to-itself convention, truncation.
- **F:** F1–F6, `angle_tolerance`, `poses`/`frame_info`.
- **M:** M1–M6, the `t` filter, explicit instants, disjoint times, categorical scope.
- **C:** C1–C5, t1 vs t2.
- **P:** P1–P5, several accounts.
- **X:** X1–X6, exact content and refusals, cross-domain.
- **Identity:** chains, cycles, groups of 3–6, split or merge by perspective or `as_of`.

**Decision coverage.** Every eligible decision has scored questions. Examples:
- SD-SPA-2 convention and NOT_YET_KNOWN;
- the SD-CAU-5 boundary rows, in P (all six rows) and C;
- SD-MEA-6 windows, in M and X;
- SD-CAU-1 ambiguous attribution under H-9, in C;
- SD-CAU-10 two accounts of one description, via `account_again`, in P.

**Targeted defect coverage:** 28 questions (14.6 %; no family above 20 %), identifiable through `targets`.
- **What authors saw:** each slot was specified only as a situation in the approved semantics. No DI id, observed
  answer or diagnostic was given to any author.
- **How they are reported:** `report.py` summarises targeted and competency questions apart.

**Gap coverage:** 37 probes, matching the plan exactly.

| Kind | Probes |
|---|---:|
| existing gaps | 25 |
| new gaps (GAP-SPATIAL-9, GAP-MEAS-12, GAP-MEAS-13) | 3 |
| approved-but-unimplemented fields (SD-CORE-3, SD-SPA-1, SD-SPA-2, SD-CAU-1, SD-CAU-2 ×2, SD-CAU-4, SD-CAU-9, SD-CAU-10) | 9 |

- **Not callable:** 9 probes have empty plans, because no reader can be asked.
- **Acceptance:**
  - every probe states `probe.accept` and a `prohibited` fabricated conclusion;
  - 33 accept `absent`;
  - none accepts an unestablished refusal.
- **Outcomes the harness keeps apart:**
  - a safe status or refusal;
  - an unsupported (absent) field;
  - an execution error;
  - a timeout;
  - a fabricated answer or derivation.

**Instant convention (item 25):**
- **Fixtures:** an explicit instantaneous measurement is `measure` with a start and no end; an instantaneous event is
  an account with a start and no end.
- **Gold:** follows SD-MEA-2 and SD-CAU-5.
- **Limitation:** the library stores an explicit instant like an empty interval (DI-33) and has no instant marker for
  accounts (DI-36). Questions on instants are therefore expected to fail until those DIs are corrected, and stay
  eligible.

## 4. Authoring and verification method, and isolation

**Roles** (item 14): each role was a separate session.

| Role | Who | What they saw |
|---|---|---|
| **Coordinator** | this session | wrote the allocation, the slot situations and the author pack; never wrote gold |
| **Authors** | 7 fresh sessions (S, F, M, C, P, X, X identity), plus 1 replacement author | author pack v1.0 (replacement: v1.1) and their assignment |
| **Verifiers** | 7 fresh sessions, plus 1 for the replacements | pack v1.1, the fixtures and **blinded** questions: expected values nulled with the paths kept; evidence sets, premises, derivations, calculations, justifications and probe acceptance removed |
| **Adjudicators** | 7 fresh sessions | pack v1.1, the fixtures, and each disputed item's two full versions |

- **Verification method:** every scored question and every probe was re-derived blind. Every numeric value was
  recomputed in a separate verifier calculation sheet.
- **Adjudication:** adjudicators resolved each disagreement against the contracts only. No program output existed.

**Author pack** ([benchmark/e2/author-pack/](../../benchmark/e2/author-pack/), `scripts/e2_author_pack.py`):
- **Contents:**
  - the contracts in an author edition;
  - the v0.2 ontology, verbatim;
  - the fixture and question formats;
  - the competency questions;
  - the gap list.
- **Removed from the contracts:** every [D] statement, local-items block, DI pointer and code citation.
- **Leak scan:** 0 unreviewed hits, plus 10 reviewed architectural lines in the ontology.
- **Not given:**
  - `src/`, `tests/`, `probes/` and `evaluation/` code;
  - the reader documentation;
  - the adjudication register;
  - diagnostics;
  - the DI register;
  - any result.

**v1.0 → v1.1** (for verification), caused by defects that authors reported:
1. **Truncated sentences.** The stripper truncated tables indented inside lists (for example "(the formula is"). Fixed,
   and interrupted sentences are now closed.
2. **Lost established rules.** Removing whole [D] entries also removed **established** expectations: the semantic and
   provenance defects' "expected" column. §0.12 now restates those 18 rules as contract statements, with no item ids
   and no implementation behaviour.
   - **Why it mattered:** this is how X-021's author, working from v1.0, wrote the answer §0.12 forbids. The v1.1
     verifier caught it.
3. **Notation.** `answer-form.md` documents ISO times and wrapped answers.
4. **New step.** `account_again` (below).

**Isolation evidence** (item 13):
- **Audit method.** `scripts/e2_isolation_audit.py` checks every tool call of every session transcript (23 sessions):
  - file paths;
  - absolute and relative paths in shell commands;
  - forbidden commands, outside heredoc bodies and quoted strings;
  - disallowed tools.
- **Audit self-test:** it catches all 6 planted violations and passes the 3 legitimate patterns.
- **Results** (`benchmark/e2/authoring/isolation-audit-*.json`):
  - **All 8 authors and all 8 verifiers: isolated.** Several read a persisted copy of their own oversized tool output.
    The audit allows that only when the same session's own output named the file.
  - **Adjudicators S, P, M and identity: isolated.**
  - **Adjudicators C, F and X: one deviation.** Each wrote and ran a helper script one directory outside its work
    directory. The scripts read only that adjudicator's own packet and fixtures, and wrote only its `out/`. No outside
    material was read.

**Isolation limitations** (item 16 asks for these to be disclosed):
- **One model, one session.** All authors, verifiers and adjudicators are fresh sessions of the same model, started
  from the coordinator's session. Their independence is in context, not in model or organisation.
- **Unverifiable inherited context.** Subagents may inherit environment context (the unrelated project `CLAUDE.md` of
  the session's directory, and the memory index). Neither contains diagnostic or implementation content. This cannot
  be verified from the transcripts.
- **Instruction, not enforcement.** Isolation was instructed and audited after the fact, not enforced by the
  environment: sessions had file-system access.
- **The coordinator had seen the implementation.** It wrote the slot situations and the author pack. The safeguards:
  - slots were phrased as semantic situations;
  - the pack was mechanically stripped and leak-scanned;
  - the coordinator wrote no gold;
  - the coordinator changed gold only by recorded notation rules (below) and by applying adjudications.
- **Missing source texts.** The pack omits the identity design (ID-1 to ID-9 are cited, not included), so the identity
  author and verifier worked from the contracts' restatements. It also omits the default attestation basis: several
  authors avoided expecting ASSERTED for undisputed content, which weakens status coverage there.

## 5. Coordinator processing between authoring and verification

`scripts/e2_normalise.py` changes notation only, and every change is logged in
`benchmark/e2/authoring/normalisation-log.json`:

| Rule | What | Count |
|---|---|---:|
| N1 | fixture-notation times in expected values → ISO 8601 | 46 |
| N2 | `before`'s `answer` path → `before` | 16 |
| N3 | `interval`'s null `answer` → `.` | 1 |
| N4 | `targets` set from the slot mapping | 29 (incl. X-031) |
| R1 | fixture repair to the author's stated intent: `e2-p-accounts` `acc-y` becomes `account_again` of `acc-x`, and P-025 `b` becomes `acc-x` | 2 |

**Harness changes (evaluation code only, no production code):**

| Change | Why |
|---|---|
| fixture time windows `["T3", "T5"]` | the approved window cases were inexpressible |
| `account_again` step | two accounts of one description were inexpressible |
| authoring metadata fields in the checker | they are not scored |
| frame-identity rule not applied to probes | — |
| angle tolerance applied to every quaternion of a `[*]` list | found statically: identical orientation lists compared as different, which would have mis-scored 4 F questions |
| `apply` no longer copies verification flags into questions | — |

Each change has tests (109 E2 harness tests pass).

## 6. Verification results

**Agreement between author and blind verifier**, over all 231 items (229 plus the two quarantined):

| Field type | Agreement |
|---|---|
| statuses | 149/150 (the one difference: X-021) |
| numeric values | **90/90 (100 %)** |
| other expected values | 858/859 |
| evidence sets | 830/970 (85.6 %) |
| admissible premises | 171/190 (90.0 %) |
| probe acceptance | 28/37 |
| items with no difference at all | 103/231 |

**Numerical verification** (item 29):
- 43 numeric questions;
- 59 author and 74 verifier calculation sheets;
- every numeric gold value agrees between the two independent derivations within the stated tolerance;
- authors also cross-checked transforms by mapping points (S: maximum error 3.4e-13).

**Disagreements and resolutions** (item 31): 128 items adjudicated, against the contracts only.

| Family | Author | Verifier | Merged | Quarantined |
|---|---:|---:|---:|---:|
| S | 5 | 8 | 8 | 0 |
| F | 11 | 10 | 2 | 0 |
| M | 6 | 9 | 4 | 0 |
| C | 6 | 9 | 1 | 0 |
| P | 0 | 18 | 1 | 0 |
| X | 1 | 15 | 10 | 1 |
| X identity | 2 | 0 | 0 | 1 |

**Recurring rulings** (each with citations in `verification/<family>/resolutions.jsonl`):
- admissible premises follow §0.7's definition (visible, usable, applicable), whether or not a derivation is presented;
- `process_steps` cites step support, not accounts;
- §0.12 rules apply to v1.0-authored questions (describes links cited; disputed transforms conflicting; denials
  usable conflicting evidence);
- forbidden sets contain only what may never be cited in any role.

The 26 verifier flags (20 contract ambiguity, 6 ill-posed) were each resolved: the item was kept with a reason, or
quarantined.

**Quarantined and replaced** (item 32; `benchmark/e2/authoring/quarantined.jsonl`):

| Quarantined | Why | Replaced by |
|---|---|---|
| X-021 | §0.12 rules out its undisputed answer, but the contracts do not fix the replacement (DISPUTED with both holders, or UNKNOWN). A contract ambiguity | X-031 (DI-27, the same slot) |
| X-112 | a near-duplicate of X-102: every step has the same parameters and answer | X-113 |

The replacements were authored and verified blind by fresh sessions, with full agreement.

**Residual notes, kept and recorded** (the adjudicators kept these items):
- **S-010 and S-011:** which triangle edge is listed as inconsistent is not fixed, so no edge is required (status
  agreed).
- **F-025, C-002, C-003, C-011 and C-014:** evidence sets are per question, not per step, so an attestation admissible
  in one step cannot be forbidden in another. This is a format limitation of the harness, recorded for a later
  increment.
- **M-002:** overlaps M-001 and M-009 heavily (same call; an instrument field M-009 also asks for). The adjudicator
  judged it not a duplicate.
- **M-029:** its `case_type` describes its principal step only.
- **G-C-09:** the question wording assumes an occurrence the fixture lacks. The probe is unaffected.

**Uncertainty kept apart** (item 33). Represented-world uncertainty (windows, disputes, unknowns) is in the gold.
Specification uncertainty is in each question's `uncertainty` field and the ambiguity records, which are:
- `authoring/raw/*/ambiguities.md`;
- the verifier flags;
- the adjudication `ambiguity` fields.

## 7. Static validation (items 34 to 36 and 39)

`scripts/e2_corpus_check.py` reports **0 problems**. It loads no fixture and calls no reader. It checks:
- question and fixture identifiers;
- allocations and case types per family;
- the A/H/G classification;
- the question checker: evidence references and role completeness, premises, multi-step references, blocked and
  unimplemented paths, H-9, conventions;
- fixture steps against the loader schema: earlier references, times and windows, the instant convention, no
  self-causation;
- an expected answer on every step;
- author and verifier calculation sheets for every numeric question;
- probe acceptance and prohibited conclusions;
- the verification status of every item (agreed or resolved; quarantined items excluded);
- the targeted allocation by DI.

**What was not used:**
- No reader output was used to validate or revise any expected answer.
- No E2 fixture has been loaded.

**Validation at the freeze commit `1da2020`** (a separate worktree; records in
[e2-authoring/validation/](e2-authoring/validation/)):

| Check | Result |
|---|---|
| Executable production readers and schema vs `5ded39a` | **no executable or schema difference** (AST check); only the earlier docstring and comment change in `physical.py` |
| `src/`, `schema/` and `docs/architecture/` since the baseline `d06316c` | **no change** (empty diff) |
| E2 harness tests | 109 passed |
| Static corpus validation | 0 problems |
| E1 format check, every fixture loaded | 272 questions, 30 fixtures, 0 problems |
| E1 original | 267/272; identical to the main reference run (`differ: []`) |
| E1 revised | 272/272; identical to the DI-19 reference run (`differ: []`) |

The E1 runs confirm that the loader changes (windows, `account_again`) leave E1 unaffected. The full
four-configuration suite was not rerun: item 39 asks for the harness tests, and no production code changed.

## 8. Readiness for baseline execution

**Ready, subject to the owner's review:**
- the corpus, fixtures, gold, calculations, coverage and evaluation configuration are frozen and hashed;
- the executable baseline is unchanged.

**What to expect at the first run:**
- **Fixture loads.** No fixture has been loaded (as instructed). Static linting covers the step schema, but a writer
  validation could still fail on load. Under the protocol, such a failure is a recorded post-freeze clarification.
  The frozen gold is never edited.
- **Targeted questions** are expected to fail where their DI is not corrected. They are adjudicated as implementation
  defects (DI-24 to DI-36).
- **Answer shapes.** Some expected paths rest on the contracts' documented answer shapes; the first run is their first
  test. A path that does not exist in an answer is scored `incorrect` and adjudicated (gold error vs defect),
  never silently fixed.

**Owner decisions:**
1. Whether to accept the isolation evidence and its limitations (section 4).
2. Whether to accept the allocation amendments (section 2).
3. Approval to run the baseline execution.
