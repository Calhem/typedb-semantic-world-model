# 5. Independent (withheld) evaluation material: format, rubric and process

**No withheld questions were generated or inspected in this phase.** This document defines what an independent
author produces and how it is scored. The 22 Phase 1 questions and the 12 Phase 1C development questions (DQ-23 to
DQ-34) stay as **development tests**.

## 5.1 What an author delivers
A **scenario package** per scenario:
```
scenario/
  manifest.json      id, domain, profile, author, date, clocks, worlds, perspectives, policies used
  fixture.json       observations, coverage records, claims stated by sources, events, alignments (neutral format)
  questions.jsonl    one item per line (5.2)
  rationale.md       why each expected answer is right (for adjudication only; never given to implementers)
```
The neutral fixture format contains **what was observed or said**, never the system's conclusions. For example, a
detection with its score and frame, or an utterance with its speaker. Policies are referenced by id and version
from the specification, so authors cannot invent private rules.

## 5.2 Item format
```json
{
  "id": "X-W-PER-0007",
  "scenario": "warehouse-3",
  "family": "temporal-continuity",
  "question": "Where was the red crate at 14:20 on day 2?",
  "query": {"template": "location-at", "params": {"referent_hint": "red crate", "t": {"clock": "wall", "value": "2026-03-02T14:20:00Z"}}},
  "perspective": "robot-1",
  "world": "actual",
  "as_of": {"clock": "wall", "value": "2026-03-02T18:00:00Z"},
  "policies": ["static-object/v1"],
  "expected": {"status": "PRESUMED", "polarity": true, "binding": {"place": "bay-4"}},
  "acceptable_alternatives": [],
  "required_evidence": ["obs-221"],
  "forbidden_evidence": ["obs-305"],
  "difficulty": "medium",
  "adversarial": false
}
```
`referent_hint` is natural language. The system must resolve it, and resolution errors count against it.

## 5.3 Scoring rubric
| Score | Rule |
|---|---|
| **Primary: correct** (0/1) | `status` and `polarity` match, and `binding` matches when a binding is expected. No partial credit |
| Evidence precision / recall | over `required_evidence`; citing a `forbidden_evidence` id is an error |
| **Unsupported assertion** (flag) | a definitive status (OBSERVED, ASSERTED, INFERRED) without the required evidence, or any definitive status where the gold is UNKNOWN, PRESUMED or DISPUTED |
| Status confusion matrix | reported per family (e.g. how often PRESUMED was given as OBSERVED) |

An item with `acceptable_alternatives` is correct if it matches any listed alternative exactly.

## 5.4 Dataset requirements
| Requirement | Value |
|---|---|
| Items per family (temporal continuity, observed absence, identity, uncertainty, conflicting beliefs, provenance, clocks and frames) | ≥ 120 on the sealed set |
| Domains | ≥ 3, including ≥ 1 **held-out domain** chosen after the core is frozen |
| Status balance | ≥ 30% of items have gold UNKNOWN, PRESUMED or DISPUTED, so that "always answer" cannot score well |
| Adversarial items | ≥ 20%: distractors, swapped look-alikes, stale presumptions, cross-clock traps |
| Scenario size | ≥ 50 observations per scenario; ≥ 3 agents in conflicting-belief scenarios |
| Independence | no author has seen B or C, their code or their development results |

## 5.5 Authoring and evaluation process
1. **Brief.** Authors receive only the specification (Phase 1C semantic review and this format) and the policy
   catalogue. They do not see implementations.
2. **Two authors per scenario**, working separately on the expected answers for the same fixture. Agreement on
   `status` is measured with Cohen's kappa. **Target ≥ 0.7** before freezing. Disagreements are adjudicated by a third
   person, using `rationale.md`, and the adjudication is recorded.
3. **Seal.** Packages are kept outside this repository, in a private location you control. Only SHA-256 hashes are
   committed here, before implementation begins.
4. **Run once.** A scoring script, run by you or a third party, loads the package, queries A, B and C, and writes
   aggregate scores and per-item outputs. Implementers see aggregates and the confusion matrix, then per-item
   results only after the report is frozen.
5. **Model-authored material** is allowed only if disclosed, written in fresh sessions **started outside this
   project's folder**. Sessions started inside it automatically receive this project's memory notes, a
   contamination route GUPI found (V, GUPI 8G). Even then, it counts as a separate, weaker evidence tier from
   human-authored material.

## 5.6 What remains for you
Who authors, how many people, where sealed packages live, and whether model-authored material is acceptable.
