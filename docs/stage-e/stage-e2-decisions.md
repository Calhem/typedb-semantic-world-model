# Stage E2 decisions (record)

**Recorded:** LABS-1.060, 24 November 2026, from the owner's decisions on
[stage-e-next-review-package.md](stage-e-next-review-package.md). This record **amends**
[stage-e2-evaluation-design.md](stage-e2-evaluation-design.md). Where they differ, this record wins.

**Not started:** Stage E2 itself, which includes the harness extensions (E2-D5), the contracts, the questions and
the fixtures.

## 1. Deferred issues

| Issue | Decision | What it means for E2 |
|---|---|---|
| DI-19 | **Approved before E2:** additive `Answer.constraint_support` (implemented on `feature/di19-constraint-support`, at review) | the `holds()` reader contract (E2-D3) includes `constraint_support`; constraint evidence is read from it |
| DI-17 | **Evaluation only.** No change to identity semantics (ID-1 to ID-9, including ID-5) | about 12 identity-conflict questions in E2 (section 2) |
| DI-7 | **Deferred.** No derivation record, rule or premise type is designed or added before E2 | derivation questions are gap probes (G); GAP-MULTI-6, GAP-CAUSE-7, GAP-MEAS-11 |
| D-3, D-4, D-5 (entry report) | settled by the three rows above | — |

## 2. Identity-conflict questions (DI-17)

- **Size and shape:** about 12 questions over identity groups that contain a disputed or denied same-as pair: chains
  with one denial, cycles with one dispute, and groups of 3 to 6 names. They also cover the perspectives and
  knowledge times at which a group splits or merges.
- **Two scores, kept apart:**
  1. **Conformance:** does the model answer as the existing contract says (ID-5: a group with a disputed or denied
     pair is not merged, and its conflict is reported)? These questions are class A or H and count towards the
     family's correctness score, like any other.
  2. **Desirability:** an independent assessment of whether the contract's answer is the one an evaluator would
     want. For each question, the author records separately, after writing the conformance gold, the answer they
     would expect without ID-5 and what ID-5 hides. This is reported as a rate and as a list of cases, and is
     **never scored as a failure**. If the rate is material, it is the evidence for a later DI-17 design. No
     semantic change follows from E2 itself.
- **Where they sit:** inside the X family or as a small identity sub-family (I). That is the design owner's choice
  when classifying, before authoring.

## 3. E2-D1 to E2-D7

| # | Decision | Recorded |
|---|---|---|
| E2-D1 | Scope: six families (S, F, M, C, P, X), about 180 scored questions, about 25 gap probes | **approved**, plus about 12 identity-conflict questions (section 2) |
| E2-D2 | A/H/G classification before authoring; rule G-1 (a gap is never a reasoning failure) | **approved** |
| E2-D3 | Reader contracts written from design documents and approved before authoring | **approved** |
| E2-D4 | Numeric gold by independent calculation sheets, recomputed by a second author | **approved** |
| E2-D5 | Harness extensions as the first E2 step; harness only, no reader change | **approved** (not started) |
| E2-D6 | Acceptance thresholds | **approved as amended** (section 4) |
| E2-D7 | E2 stays development-tier; the external sealed evaluation stays deferred | **approved** |

## 4. Acceptance criteria (E2-D6 as amended; these replace design section 7, items 2, 4, 5 and 6)

| Criterion | Threshold |
|---|---|
| Correctness | at least 95 % of scored (A and H) questions correct **in each family**; every failure adjudicated |
| Evidence recall | at least 90 % **in each applicable family** (families whose questions have required evidence) |
| Evidence precision | **100 % for supporting evidence**: every attestation an answer cites as support is admissible for that question |
| Derivations | **no fabricated derivations**: no answer presents a derivation (named rule and premises) that is not recorded |
| Latency | question latency **p95 below 1 s**, with a **5 s hard execution budget** per question |
| Regressions | **no unintended semantic regression**: E1 (original 267/272, revised 272/272), the 106,752 reference answers and the 398 views unchanged, except for differences authorised beforehand |

These items of design section 7 are kept as they are:
- independence (1);
- path agreement (3);
- gap probes return UNKNOWN or an explicit refusal (5);
- frozen history (7);
- two-author agreement, reported (8).

**What the amended thresholds require of the design**, recorded here so that authoring follows them:
- **Precision needs an admissible set.** Each question's gold lists every admissible supporting attestation, not
  only the required ones, so that precision can be computed against it:
  `precision = |cited ∩ admissible| / |cited|`. `forbidden_evidence` stays a separate hard failure.
- **The hard budget is enforced by the harness.** A question still running at 5 s is stopped and recorded as **over
  budget**. That is a failure of the latency criterion, with its family and reader named. It is not counted as a
  wrong answer, and it is listed under DI-20 to DI-22 where it matches one of them. Section 5.5 of the design
  ("slow is reported, not scored as wrong") stays true for correctness.
- **Latency is measured per question as the harness runs it** (all reader calls of a multi-step plan together), on
  the selective path. The full-load reference path is recorded too.

**For confirmation:** whether the 1 s p95 and the 5 s budget also bind the full-load path. The proposal is that they
don't: full load is the reference path for answer agreement, not a serving path.

## 5. Gap probes

Gap probes (class G, about 25) are **kept apart** from supported-capability conformance:
- They never enter a family's correctness, recall or precision score.
- **Reporting:** the E2 report has its own section for them. It lists every probe with its gap id, the reader called
  (if any), what the reader returned, and pass or fail against the probe's own check: UNKNOWN or an explicit refusal,
  never a fabricated definite answer or derivation.
- **A failed probe** (a reader fabricating an answer) is an implementation finding. It is registered with a
  reproduction, whatever the conformance scores.
- **Reclassification:** a question reclassified to G during adjudication is listed with its evidence in the same
  section, never silently dropped (rule G-1).

## 6. Still out of scope until approved

- implementing DI-7;
- changing identity semantics (DI-17 options b–d) or the ontology;
- the DI-20 to DI-23 optimisations;
- starting the E2 harness implementation (E2-D5).
