# Stage E2 authoring and isolation protocol

**LABS-1.064, 28 November 2026. Proposal for review.** This protocol governs how the E2 questions, fixtures, calculation
sheets and gold will be written. Nothing here has been authored yet. Authoring starts only after the owner approves
this protocol and merges the contracts.

**What kind of evaluation this is.** E2 is a **development-tier** evaluation (E2-D7). The authors, the design owner and
the implementation belong to one project, and the isolation below is **procedural**: it controls what each author
is given. It is **not** an externally independent or sealed evaluation, and no report may describe it as one. The
external sealed evaluation stays deferred.

## 1. What this protocol builds on

| Rule | Source |
|---|---|
| Scope, about 180 scored, about 12 identity, about 25 gap probes | E2-D1 (`docs/stage-e/stage-e2-decisions.md`) |
| A/H/G classified before gold, rule G-1 | E2-D2 |
| Gold from approved contracts written from design documents | E2-D3; `reader-contracts.md` (final, §0.11) |
| Numeric gold by independent calculation sheets, recomputed | E2-D4 |
| Thresholds | E2-D6 as amended (unchanged) |
| Allocation and coverage | [coverage-matrix.md](coverage-matrix.md) |
| Question format and checks | `evaluation/e2/check.py` |

## 2. Roles

| Role | Who | Does | Never |
|---|---|---|---|
| **Design owner** | the project owner | approves the protocol, the classification and the fixture specifications; adjudicates disagreements | writes gold |
| **Fixture specifier** | one author per family pair | writes fixture **specifications** in approved-semantics terms (entities, worlds, claims, times, acceptances), then the fixture files | sees reader outputs |
| **Question author** | three authors, one per two families (S+F, M+C, P+X); the identity subset is written by the X author | writes questions, expected answers and evidence sets | calls readers, loads fixtures, reads `src/`, `tests/`, `probes/` |
| **Second author** | a different author for each family | recomputes every numeric answer independently; answers a blind random 20 % of non-numeric fields | sees the first author's calculation before recomputing |
| **Harness operator** | separate from the authors | runs the checker, freezes, runs the evaluation, publishes results | edits gold after the freeze |

**Separate sessions.** When AI agents author, each author is a fresh session that is given only its author pack
(section 3), with no access to the repository beyond the pack. Independence between authors needs separate fresh
sessions, never one session acting as two authors.

## 3. What authors receive and what they do not

**The author pack (given).** It is generated once, before authoring, and committed, so what the authors saw can be
audited:
- the **final reader contracts**, in an **author edition**:
  - §0, including the §0.10 approvals and §0.11 decisions;
  - each reader's sections 1 to 9, with the "Decided" notes;
  - **removed:** every [D] statement and every "Local items" block, because they describe what the implementation
    does;
- the **semantic decision record**, sections 1 to 3 and 5. Its "current behaviour" sentences are removed, and so is
  section 4, which describes defects;
- the **ontology and design documents** the contracts cite:
  - `docs/architecture/world-ontology-v0.2.md`;
  - the Core 0.3 and 0.4 design documents (stage-a1, stage-a2, stage-b, stage-c, stage-d3-design, and the increment
    and identity designs);
- the **question format** (the `check.py` module docstring), the fixture step reference, and the **coverage matrix**;
- the capability inventory's **gap list** (gap ids and what is missing). Its code line references are removed;
- the author's **allocation**: families, CQ forms, case types, the targeted situations (section 5) and the gap ids.

**Leak check.** The pack is scanned for implementation material. Each hit is removed or replaced by hand, and the scan
result is committed with the pack. The scan looks for:
- the words "code", "docstring", "implementation", "currently", "reproduced";
- file names under `src/` and module abbreviations (DYN, phys, qualities.py);
- diagnostic ids (DX-n) and observed values.

**Not given:**
- `src/`, `tests/`, `probes/`, `evaluation/` code;
- `benchmark/e2/spec/reader-docs.md`: implementation docstrings;
- the adjudication register (its "implementation behaviour" and "reproduced" columns);
- `docs/stage-e/e2-contract-adjudication/diagnostics.json` and every diagnostic output;
- the evidence records under `docs/stage-e/e2-reader-contracts/` (they cite code lines);
- the deferred-issue register entries for DI-24 to DI-36;
- any reader execution result, harness result, E1 result or benchmark output;
- the other authors' gold, before their own is committed.

## 4. Writing a question

1. **Classification first.** The design owner classifies each planned question as A, H or G from the contracts, the
   decision record and the gap inventory, **before** gold is written:
   - eligible approved semantics: A/H;
   - an approved but unimplemented capability: G, under its DI;
   - a gap: G.

   A reclassification during adjudication is reported with its evidence (G-1).
2. **Fixture.** The fixture is written from its specification. Fixture conventions from the decisions:
   - an explicit instantaneous measurement is `measure` with a start and no end, never `end` equal to `start`
     (SD-MEA-2);
   - causal and effect claims carry no valid interval, except in targeted SD-CAU-7 questions;
   - no input relies on self-causation (ONT-SC-1);
   - an occurrence reader is given an occurrence (SD-CORE-4).
3. **Expected answer.** The author derives the answer **from the approved semantics alone**, field by field, with the
   contract citation for each field.
   - The author never adjusts an answer towards what an implementation might produce.
   - A question whose contract answer the author cannot derive unambiguously is **not** authored. It is raised with
     the design owner as a contract question.
4. **Numbers.** Every numeric field is computed in a calculation sheet in `benchmark/e2/calc/<question id>`.
   - The sheet uses only formulas from the design documents and standard mathematics. It never imports the library
     or any project module.
   - A second author recomputes every number independently. Any difference beyond the stated tolerance is adjudicated
     before the freeze.
   - Tolerances are stated per question before any run (for example 1e-9 m for exact translations, 1e-6 rad for
     rotations).
5. **Evidence, written explicitly for every scored question:**
   - `required_evidence` and `admissible_evidence` (supporting);
   - `required_conflict_evidence` and `admissible_conflict_evidence` (conflicting), whenever the reader can cite
     conflicting evidence;
   - `forbidden_evidence`;
   - `admissible_premises` for `where` and `transform_between`, honouring visibility, usability and applicability
     (common §0.7);
   - `"convention": "frame-identity"`, with empty evidence and premise sets, for a frame to itself (SD-SPA-2).

   All are named by fixture step (common §0.5). Admissible sets list **every** admissible attestation, not only the
   required ones. Evidence is never inferred from what a run cites.
6. **Attribution.** A `changes` question that inspects an explanation fixes its `attribution` (H-9).
7. **Plan steps.** Each X question writes every intermediate step's expected answer, so a failure is located at its
   step.
8. **Metadata.** Each question also records:
   - its CQ form;
   - its justification and citations;
   - its uncertainty;
   - the adversarial flag;
   - its difficulty;
   - `targets` for targeted defect coverage;
   - `depends_on` only for ONT-SC-1, and so in practice never.
9. **Identity subset.** After writing the conformance gold, the X author records the desirability note: the answer
   they would expect without ID-5, and what ID-5 hides. It is never scored (DI-17).

## 5. Targeted defect coverage without defect knowledge

The design owner chooses the targeted situations from the deferred-issue register. They are given to authors only as
**situations in the approved semantics**, never as defects or outputs. For example:
- "the position is stated under an alias; ask by the canonical name";
- "the start of the activity is a window in which the certificate lapses".

The author derives the gold from the contracts, as for any other question.

**Limits:**
- targeted questions stay at about 15 % of the scored corpus (28 of 192), and no family exceeds 20 %;
- the diagnostic fixtures and their shapes are not reused;
- the report summarises targeted and competency questions apart (`report.py`).

## 6. Checks and freeze

1. The harness operator runs the checker on the authored files. It calls no reader. The operator returns only the
   problems found, and authors correct them.
2. **Agreement.** The second author answers a blind random 20 % of each family's non-numeric fields. Agreement is
   reported per field type (Cohen's kappa). Disagreements go to the design owner; a corrected gold value is recorded
   with its reason.
3. **Freeze.** Questions, fixtures, calculation sheets, the author pack and its leak-check result are committed in one
   **freeze commit** before any fixture is loaded or any reader is called. Results name that commit.
4. **After the freeze:**
   - fixtures are load-checked. A fixture that fails to load is corrected as a recorded post-freeze clarification;
     the frozen gold is never edited;
   - the evaluation runs on both query paths;
   - every failure is adjudicated in writing, using the categories implementation defect, specification ambiguity,
     gold error, gap (reclassified to G with evidence) and harness error;
   - clarifications go to a clarifications file, and a revised evaluation is reported **beside** the original, as in
     E1.

## 7. What a report must say

- The tier: development-tier, procedurally isolated, not externally independent or sealed.
- The freeze commit and the author-pack commit.
- Correctness per family, against the E2-D6 thresholds, on the original frozen evaluation. Also correctness on the
  identity subset, and on targeted versus competency questions.
- Evidence recall and precision per role, the unattributed count, and "no evidence returned" counts.
- The two kinds of probe results, kept apart:
  - gap probes, with the new gaps named;
  - approved-but-unimplemented probes.
- Path agreement, latency (the selective p95 and the 5 s budget), and the E1 history (267/272 original, 272/272
  revised).
