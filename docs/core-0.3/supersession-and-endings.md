# Supersession across perspectives, and the cost of ending a fact

**Status (2026-11-10):** the defect described here is fixed on `feature/core-0.3` and covered by
`tests/test_e_supersession.py` (8 tests). The write-amplification question in section 4 is recorded for later
evaluation; nothing was changed for it.

## 1. The defect, reproduced
Scenario: source A asserts P ("box on shelf-3 from 10:00, until superseded"); perspective B (the operations lead)
accepts A's attestation; A then revises it. Before the fix, Core 0.3 behaved as follows (5 of the 8 tests failed):

| Case | Before the fix | Intended (v0.2 §5.3, §6.2) |
|---|---|---|
| A ends its claim at 11:00 (restatement + supersession); B has not reviewed the revision | B's view became **UNKNOWN**, even at 10:30 where both versions agree | B keeps its accepted evidence (now outdated for 11:00 onwards); the answer shows the source revised it |
| B **rejects** A's revision | B still lost the original | B keeps the original |
| A corrects an erroneous historical assertion ("shelf-4 all along") | not expressible (no correction link) | B keeps shelf-3 with A's correction as an alternative until B accepts it; then shelf-4, not DISPUTED |
| B accepts the revision | correct | B follows the revision |
| A retracts its claim outright (A's own acceptance: retracted) | correct: only A's view changed | the same |
| Hypothetical world branched before the revision | correct: snapshot unaffected | the same |

**Cause.** A supersession hid the original attestation for every perspective, whether or not that perspective had
accepted the replacement. In effect, an attestation no one else had accepted changed their answers. v0.2 §6.2 says
unaccepted attestations by others are alternatives, never support. The defect is in the implementation, not the
frozen ontology.

## 2. Intended semantics (now implemented)
An attestation is **superseded for perspective p** only when a supersession of it is recorded by the knowledge time
**and** its replacement is part of p's view: p's own attestation, accepted by p, or a stipulation. Consequences:
- **Traceability:** attestations and acceptances are never edited; every revision is a separate, linked record.
- **No automatic acceptance:** a source's correction is not another perspective's acceptance.
- **No silent erasure:** a perspective keeps evidence it accepted until it accepts the replacement. Answers list
  `superseded_by_source` in the evidence, so an outdated belief is visibly outdated.
- **Validity vs learning:** when the content held (valid time) stays separate from when the source revised it and
  when a perspective accepted the revision (transaction time). Each is reproducible at any knowledge time.
- **Not truth:** a perspective may retain an outdated belief. Its answers are labelled as that perspective's.
- **Hypothetical worlds:** a revision recorded after a variant's knowledge snapshot is invisible there (unchanged).

Corrections use `attest(…, supersedes=old_id)`: a new attestation by the same attester (enforced) linked to the one it
replaces. Endings use `end()`, which is the same mechanism with the original content and a stated end.

## 3. The fix
- `semantics.superseded(a, perspective, as_of)` checks the replacement's acceptance state for the perspective.
  `usable`, `Identity`, alternatives and `history` all use it.
- The loader reads, for each visible supersession, the replacement's attester and stance and the perspective's
  acceptances of it (one extra query per world level, only when supersessions exist).
- `attest(supersedes=…)` writes the supersession in the same transaction, and refuses a different attester (E3).
- No change to the schema, the ontology, or the content/stance architecture.

## 4. Write amplification: why ending a fact costs two records, and whether a lighter form would do
**Why it is done this way now.** Attestations are immutable (v0.2 E3), so an end learned later cannot be written onto
the original. Editing it would rewrite what was known earlier. Instead the attester's new attestation restates the
content with the end, and a supersession links the two with its own recording time. Each move therefore writes about
5-6 records (event description, its occurrence attestation, the restatement, the supersession, the new location),
against 4 in Milestone 1. On the benchmark, about half of the attestation rows read per question are superseded
originals or their restatements.

**A lighter alternative**, for later evaluation: a `termination` record (attester, the ended attestation, end window,
world, recorded-at), similar to Milestone 1's cessation but attributed and world-scoped. Assessment against the
required properties:

| Property | Restatement + supersession (current) | Termination record |
|---|---|---|
| Historical validity (valid time) | yes | yes: the effective end is the earliest usable termination |
| Transaction-time knowledge | yes | yes: `recorded-at` on the termination |
| Explicit denials | unaffected | unaffected (denials remain attestations) |
| Source provenance | yes: same attester enforced | yes, if the termination has an attester role restricted to the original's attester |
| Perspective-specific acceptance | yes: the replacement is an attestation, so it can be accepted or rejected (section 2) | **needs acceptance of terminations.** v0.2 lets acceptance target attestations only, so this would be an **ontology amendment** (or terminations would have to be modelled as a kind of attestation, which brings back much of the current cost) |
| Hypothetical snapshot semantics | yes | yes, if world-scoped (as Milestone 1's cessations were) |
| Corrections of content (not just ends) | the same mechanism | still need supersession |
| Records per end | 2 relations, about 10 attributes, 5 role links | 1 relation, about 3 attributes, 2-3 role links |

**Recommendation (not implemented):** keep the current mechanism, which is now correct across perspectives. Evaluate
terminations only together with an explicit decision on whether acceptance may target them. Measure the benefit on the
same benchmark first; the stored-row saving is real, but the semantic cost is an amendment to v0.2.
