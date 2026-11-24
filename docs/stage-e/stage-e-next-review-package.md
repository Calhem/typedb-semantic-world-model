# Next review package: DI-19, DI-17, DI-7 and the Stage E2 evaluation design

**Status:** for review (LABS-1.059), 24 November 2026. **Nothing here is implemented.** This package gathers the
decisions still open before Stage E2 can start, now that the performance phase is closed
([stage-e-performance-closure.md](stage-e-performance-closure.md)). No semantic, ontology or reader change is proposed
beyond what each option describes, and none starts without its own approval.

**Sources:**
- the deferred-issue register: [deferred-issues.md](../core-0.4/deferred-issues.md), DI-7, DI-17 and DI-19;
- the isolated reproductions: [stage-e-entry-report.md](stage-e-entry-report.md), section 4
  (`probes/stage_e_entry_di.py` → `.out.txt`);
- the design: [stage-e2-evaluation-design.md](stage-e2-evaluation-design.md), with its
  [capability inventory](stage-e-entry/e2-capability-inventory.md).

## 1. Where the earlier gate decisions stand

| ID | Decision (entry report, section 8) | Status |
|---|---|---|
| D-1 | Accept the Stage E entry baseline | approved for correctness (LABS-1.055). The performance baseline is now superseded by the closure report |
| D-2 | DI-9 next steps | done: O-1, O-2, O-3 and F6, LABS-1.056 to 1.059 |
| D-3 | DI-19: implement `constraint_support` before E2, or name the evidence location in the E2 specification | **open** (section 2) |
| D-4 | DI-7: derivation questions stay E2 gaps until the derivation record is designed | **open** (section 4) |
| D-5 | DI-17: add identity-conflict cases to E2; no semantic change | **open** (section 3) |
| D-6 | Core 0.3 10× | done: the selective path was measured in LABS-1.055, and again in every later benchmark |
| D-7 | Keep `wm-probe-stage-e` and drop the scale databases | kept. The scale databases were rebuilt for DI-9 and are dropped at closure (LABS-1.059) |
| D-8 to D-14 | E2-D1 to E2-D7 | **open** (section 5) |

## 2. DI-19: a constraint dispute through `holds()` does not cite the constraint

**Measured** (entry report 4.3):
- `holds()` on one of two accepted appointments to an exclusive office answers DISPUTED.
- It cites `support [a-bea]` and `conflicts [a-cal]`. The constraint attestation `x-sm` appears nowhere in the answer.
- The canonical judgement (`constraints[].judgement.support`) and `organisation.office_holders`
  (`conflict.constraint.support`) both carry `x-sm`.
- E1 ORG-011 (revised) has the correct judgement, with evidence recall 0.667.

**Why it matters for E2.** E2 acceptance criterion 4 asks for evidence recall of at least 0.9 per family.
- Any E2 question whose answer is a dispute under an attested constraint is affected. The design does not yet count
  how many such questions there are: most likely X-family questions composed over offices.
- Without a correction, these questions either lose recall on a known, documented gap or need the E2 specification to
  point at `office_holders` and the judgement instead.

**Options:**

| | Option | Effect on answers | Cost |
|---|---|---|---|
| (a) | **Additive `constraint_support` on `holds()` answers**: the deciding attestations of each applied attested constraint; empty for a declared functional slot | existing fields keep their values; the 106,752 baseline gains the field on constraint disputes only | small: one reader, tests, a new snapshot diff limited to that field |
| (b) | Specification only: E2 reader contracts name where constraint evidence lives | none | an E2 contract change; the answer itself stays incomplete |
| (c) | Count it as a known gap in E2 scoring | none | recall loss is attributed to DI-19 in the report |

**Recommendation: (a) before E2, as its own small increment.** It is additive, it makes E2's evidence measure
meaningful on constrained questions, and its validation is cheap: a field-limited diff of the 106,752 answers, plus
the 398 views and E1. The increment would need:
- the exact field name and placement (`Answer.constraint_support`, one list per applied constraint);
- the rule for declared slots (empty, because the slot is schema data);
- whether `value_at` and `value_of` gain it too. Proposed: yes, wherever the same judgement is projected.

## 3. DI-17: conflict-group identity may be over-restrictive

**Measured** (entry report 4.2):
- **Case:** s1~s2 and s2~s3 are established, and s1~s3 is denied. Nothing merges, so the sound s1~s2 equivalence is
  set aside too, and one conflict group is reported.
- **This is the approved ID-5 behaviour.**
- **Reference data:** 0 same-as attestations and 0 conflict groups in 78 contexts, so no current evaluation can show
  whether it matters.

**Options:**

| | Option | Nature |
|---|---|---|
| (a) | **Make the risk measurable: identity-conflict questions in E2** (chains with one denial, cycles with one dispute, groups of 3–6 names), scored against what an independent author expects | evaluation only; no semantic change |
| (b) | Keep the links not on a path to the disputed pair | semantic change; needs a rule when several paths exist |
| (c) | Merge maximal consistent subgroups | semantic change; may not be unique |
| (d) | Merge, and flag answers that relied on the group | semantic change; affects every identity-using reader |

**Recommendation: (a) only, with no semantic change now.** Proposed size: about 12 questions, inside the X family or
as a small identity sub-family (I). Gold is written from the ID-1 to ID-9 contract, not from the code.

What to report:
- how often authors expect a merge that ID-5 refuses;
- what each refusal hides.

Only if that rate is material does a design for (b)–(d) follow, under its own approval.

**Decision needed:** whether these questions are scored as A/H (conformance to ID-5) or as gap probes (G). Proposed:
A/H. ID-5 is the approved contract, so the questions test conformance. The "would an author expect more" judgement
is collected separately as an annotation, not scored.

## 4. DI-7: formal derivation provenance is not recorded

**Measured** (entry report 4.1):
- The core `wm.attest(..., basis='inference')` is accepted and answers INFERRED, with only a `rests-on` record.
- The laboratory profile refuses the same write.
- The schema has no rule, derivation or premise type.

**Expected** (ontology v0.2 E6): INFERRED only for an attestation that names its rule and premises, whose attester is
the reasoner, and which is usable only while every premise is.

**Options** (from the register): (a) a derivation record; (b) refuse `basis=inference` without one; (c)
documentation only. The register recommends (a) + (b).

**Why it matters for E2.** The X family (multi-step) and parts of C need derivations they can cite. Until (a)
exists, those questions are gaps: GAP-MULTI-6, GAP-CAUSE-7 and GAP-MEAS-11, all "no derivation record" (capability
inventory).

**Recommendation:**
- Keep D-4: derivation questions stay G (gap probes) in E2.
- The DI-7 design, (a) + (b), is a **separate ontology increment after E2**, so E2 measures the model as it is.
- The gap probes check one thing now: no reader fabricates a derivation. For example, a basis-`inference`
  attestation is never presented as derived from named premises.

**Not recommended:** doing DI-7 before E2. It is an ontology change (new types and roles) with export and upgrade
consequences. It would also move E2's baseline, and E2's gaps would no longer describe the released model.

## 5. Stage E2 evaluation design: decisions still open

The design is unchanged since LABS-1.054 (941146d).
- **Size:** about 180 scored questions in six families (S, F, M, C, P, X), plus about 25 gap probes.
- **Classification:** A/H/G before authoring, under rule G-1.
- **Gold:** independent of the implementation, from approved reader contracts.

| # | Decision | Recommendation | Note after the performance phase |
|---|---|---|---|
| E2-D1 | Scope: six families, about 180 scored questions, about 25 gap probes | approve | plus about 12 identity-conflict questions if DI-17 (a) is approved |
| E2-D2 | A/H/G classification before authoring; rule G-1 | approve | DI-7 questions are G; DI-17 questions are A/H |
| E2-D3 | Reader contracts from design documents, approved before authoring | approve | if DI-19 (a) is approved, the `holds()` contract includes `constraint_support` |
| E2-D4 | Numeric gold by independent calculation sheets, recomputed by a second author | approve | — |
| E2-D5 | Harness extensions (GAP-HARNESS-1..4) as the first E2 step; harness only | approve | — |
| E2-D6 | Acceptance thresholds: 95 % conformance, 0.9 evidence recall, 5 s budget | **owner sets** | the corrected code is far inside 5 s. The slowest reader call, `provenance`, is about 0.3 s p50 at perspectives-10. A tighter budget (e.g. 1 s) is now realistic; questions over it are listed under DI-9's residuals (DI-20 to DI-22) |
| E2-D7 | E2 stays development-tier; the external sealed evaluation stays deferred | confirm | — |

## 6. Proposed order (for approval)

1. Approve or adjust D-3 (DI-19), D-4 (DI-7), D-5 (DI-17) and E2-D1 to E2-D7, including the thresholds.
2. If D-3 is approved, the DI-19 additive increment comes next. It needs its own branch and validation: 106,752
   answers with a field-limited diff, 398 views and E1, then a review gate.
3. E2 step 1 is the harness extensions only (E2-D5), with no reader change.
4. Then the E2 reader contracts (E2-D3), followed by authoring under the frozen-gold protocol.

**Out of scope until approved:**
- any semantic or ontology change, including DI-7, DI-17 (b)–(d) and DI-19;
- the DI-20 to DI-23 optimisations;
- starting Stage E2.
