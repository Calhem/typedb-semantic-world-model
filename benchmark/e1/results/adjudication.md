# Adjudication of the Stage E1 discrepancies

Seven questions differ from their expected answers in the final run: five incorrect, two with an evidence shortfall.
Each was read against the specification sources the authors were given. **No expected answer was changed.** The
classification says where the difference comes from; it does not overrule the gold.

| Id | Difference | Classification | Basis |
|---|---|---|---|
| LAB-010 | expected `not established`; actual `established` | **gold-suspect, from the benchmark's own documentation** | The calibration step has no `end` and no `until_superseded`. The benchmark README says that then "the end is UNKNOWN", and the author followed it. But the documented `laboratory.calibrate` writer says it attests the calibration "from `start` to `end` (or until superseded)": its default is until-superseded, so the claim holds on T15. The README overgeneralised the core `attest` rule to every writer. |
| ORG-011 | expected `disputed`; actual `unknown` / NOT_YET_KNOWN | **system finding: documentation mismatch and a silent answer** | The question uses the roles the organisation module notes give, `office-holding(holder, office, context)`. The schema's roles are `classified`, `class` and `context` (office-holding is a sub-type of classified-as). `holds` and `judgement` accept role names the type does not have and answer NOT_YET_KNOWN, with no refusal, so a misspelt question looks like an answer. Two defects: the notation in the module notes, and no validation of role names in readers. |
| TEMP-017 | expected `pending` / UNKNOWN; actual `not holding` / INFERRED | **specification gap; the system follows v0.2** | The system accepts the parcel at another place, so v0.2 section 4.4 answers "false, INFERRED by functional exclusivity" (its own worked example), and the status table lists functional exclusivity under INFERRED. The author applied the increment B design 2.4 table, whose `PENDING` row does not mention functional exclusivity (the same author recorded this tension, ambiguity 6, for a related case). The two documents need one sentence of reconciliation. |
| LAB-025, LAB-026 | expected players of the accepted accounts only; actual players of every linked account (including an unaccepted one) | **specification conflict between two approved decisions** | MP-2: with no constraint, "the role's players are every player of every **compared** account" (accepted, describes link established). ER-5: the view's `roles` lists "its players citing their accounts" over `accounts`, which holds **every** linked description, accepted or not. The implementation follows ER-5 and offers no field for MP-2's union; a reader cannot tell co-participants from players named only by unaccepted accounts without cross-reading `accounts`. Needs a decision. |
| LAB-034 | evidence: expects `loc-12-fridge`; the answer cites a restatement of it | **harness limitation** | When the sample was moved, `move()` ended the system's location claim by a superseding restatement with an end (E3, D14). The answer correctly cites that restatement, whose id the system mints; the harness maps only fixture ids. Not a system defect. |
| X-003 | evidence: expects the stipulated denial of Bea's appointment as well as Dan's; the answer cites Dan's | **evidence definition** | The harness counts, for `office_holders`, the evidence of the established holders and of the conflict. The author also counts the claim that removes Bea from the holders. Both are defensible readings of "required evidence"; the benchmark should define it for list answers. |

## Summary
- **Confirmed reasoning defects in the implementation:** none.
- **System findings:** 1 (ORG-011: unvalidated role names give a silent NOT_YET_KNOWN; the organisation notes use role
  names the schema does not have).
- **Specification issues:** 2 (LAB-025/026: MP-2 against ER-5; TEMP-017: v0.2 4.4 against increment B 2.4).
- **Benchmark issues:** 3 (LAB-010: the README's end rule; LAB-034: restatement ids; X-003: evidence for list answers).
