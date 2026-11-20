# Notes: organisation and conflict-provenance questions (Stage E1)

Author: independent question author (model-authored, development tier). Sources read: benchmark/e1/README.md,
TEMPLATES.md, spec/reader-docs.md, world-ontology-v0.2 (sections 4-7), core-0.3 README and supersession-and-endings,
increment B, C and D designs, the multiplicity design and decision-gate section 3, the core-0.4 plan. No source code,
tests, probes, results or system output were read. The only command run was `evaluation.check --load`.

Files: `fixtures/org-offices.json`, `org-authority.json`, `org-capability.json`, `org-acts.json`,
`conf-location.json`, `conf-events.json`; `questions/organisation.jsonl` (ORG-001..031),
`questions/conflict-provenance.jsonl` (CONF-001..030).

## Assumptions
1. **Role names.** `office-holding(holder, office, context)` and `employment(employer, employee)` are taken from the
   organisation module notes and v0.2 4.2; `part-of(part, whole)`, `existence(existent)` and
   `classified-as(classified, class)` (ER-2 wording) are assumed. The format checker loads the fixtures without error,
   but it does not run the `holds` questions, so a wrong role name in a question's `params` (ORG-011, CONF-029/030)
   would show up only at run time as `error`, not as a wrong answer.
2. **Offices, powers, capabilities.** Offices are `social-role` concepts, powers and capabilities are `capability`
   concepts, contexts and scopes are organisations or places. Attesters and perspectives (`hr`, `clerk`, `ops`,
   `audit`, ...) are `social-object` particulars (D7: agency is not checked).
3. **Co-signed classification** is written as an ordinary `classified-as(classified: occurrence, class:
   organisation:co-signed)` attestation, using the category from the organisation profile's vocabulary (MP-4), with
   no entity step for the category.
4. **Describes links** written by `account`/`act_in_office` with `occurrence` are taken to be established once the
   account is accepted (`accepted_by` also accepts the link, README). A link's own interval is not tested.
5. **Kind at the occurrence's start**: the start is T5, the start of every accepted account (ER-2).
6. **`officials`** (ORG-031) lists every official the description names, whatever its acceptance.
7. **Status of `pending`** (CONF-013) is UNKNOWN (v0.2 5.6: records visible, none decides). Status of a
   `not holding` answer decided by an accepted testimony denial (CONF-007) is ASSERTED (v0.2 C6: "ASSERTED false").
8. **Inheritance in a plan** (CONF-014/015/016): attestations starting before the branch and held until superseded
   are inherited past the branch time; for the functional slot, the plan's own stipulation overrides them for the same
   key (increment B 2.1). The plan's knowledge time freezes acceptances (v0.2 6.3, C7).
9. **Employment dispute** (CONF-029): read from v0.2 4.4's worked example plus D5 ("ended accounts still dispute
   accounts that began before the end").
10. **Evidence.** For `event_role`, `required_evidence` lists the account (description) ids naming the players, also
    for disputes (the role's `support` is empty there, but each player cites its accounts). An unaccepted or rejected
    account is `forbidden` (CONF-020, CONF-021). For `occurrence_status` CONF-025 the accepted accounts are forbidden
    as support: the reader reports them separately, but the status must not rest on them. If the harness counts any
    mention, not only support, these forbidden items could be flagged falsely; this is the intended reading of
    "cited as support".
11. **`reason` with both one-declaration cases** was not used (see below).

## Ambiguities found in the specification
- **A1. Both `one` reasons at once.** TEMPLATES says both reasons are "joined by `; `" but does not fix their order,
  so a question where one account names two officials and another names a third was not written.
- **A2. Functional exclusivity in `holds`.** v0.2 4.4 says "shelf-3?" is false at 10:15, INFERRED by functional
  exclusivity, but the judgement reader says that a content with nothing recorded is UNKNOWN (`no_evidence`), and
  increment B lists no "inferred not holding" case. Not written.
- **A3. `officials` and acceptance.** The reader says "every official named", but does not say whether an
  unaccepted account is reported in the same way. Only the accepted case was written (ORG-031).
- **A4. Forbidden evidence and listing fields.** `authorised.only_in`, `capable.only_in` and the `accounts`/
  `appointments` listings name attestations that are not support. It is not specified whether the scorer counts such
  mentions as citations. So no forbidden ids were put on questions whose answer lists them only in those fields
  (ORG-013, ORG-020, ORG-021, ORG-024, office_holders questions).
- **A5. Status of `not holding` from an ended claim.** Increment B gives the reason `ended`, but whether the answer
  status is the ended claim's support status or UNKNOWN is not stated. Not written for `holds` with an end.
- **A6. `end` by another attester.** Whether `accepted_by` on an `end` step accepts the restatement, and how an
  unaccepted end interacts with D14 at times after the end, is clear in principle (the original stands) but the
  fixture semantics of `end` with acceptance are not documented. Corrections (`correct`) were used instead
  (CONF-009/010).
- **A7. Exclusive constraint in `offices_of`.** Not a template; not used.
- **A8. Kind-scoped and unconditional declarations together.** MP-3 says an established kind-scoped declaration
  wins. Where the kind is not established, I read the unconditional `one` as applying (as M3 shows), not a union
  (ORG-028, ORG-029).
- **A9. Grantor/attester and perspective.** Whether the grantor's own perspective counts a grant reported by another
  attester is not specified. Not written.

## Questions deliberately not written
- Office holders where the exclusive-office constraint is itself disputed or denied. Increment B says it "never
  disputes" then, but none was written, to keep the set to the cases the documents walk through. They could be added.
- `capable` with a holding that has begun but has no end and is not `until_superseded` (`end_unknown`): the label is
  "not established" (increment B 2.4). Not written, to keep `until_superseded` throughout as instructed.
- Event roles under identity (same-as) (M8, M9): the fixture format has no documented same-as op, and the role names
  are not documented. Not written.
- An `authorised` answer with mixed-support status (rule Q): the template scores only `judgement`.
- Pickup C1 with a profile single-valued `picker` role: no profile declares one (the core declares none).
