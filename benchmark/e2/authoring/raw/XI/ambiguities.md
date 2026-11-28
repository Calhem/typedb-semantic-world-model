# Ambiguities recorded by author XI

The pack states the identity rules only by reference (ID-1 to ID-9; the identity design document is not in the pack).
What is fixed: contracts §0.2 ("readers that take an id judge it with its established same-as group ... A group
containing a disputed or denied pair is not merged (ID-5)"); `holds` §1 (a same-as question is judged by its stated
names, ID-1, and is timeless, ID-3), §4 (links relied on are not added to the evidence, ID-D §3.10); `occurrence` §4
(same-as merges only where ESTABLISHED, ID-2); v0.2 §3.1 (only accepted same-as merge, transitively; proposed links
are never chained; a rejected acceptance splits the group from that recording time on) and §4.2. Every question was
built so that it depends only on these statements.

## A1. What "not merged" and "group" mean in ID-5
- Passage: contracts §0.2, "A group containing a disputed or denied pair is not merged (ID-5)."
- Reading 1 (used): the group is the closure of established same-as links; if any two of its members form a denied or
  disputed pair, nothing in it is merged and each id is judged alone.
- Reading 2: the merge is broken only at the offending pair (or the group is split into sub-groups), or "group" means
  the closure over all same-as records, including denied and unreviewed ones.
- What I did: in every ID-5 question the denied or disputed pair joins two members already connected by established
  links (chain d1=d2=d3=d4 with d1-d4 denied; cycle e1=e2=e3 with e3-e1 disputed). There, reading 2's "split at the
  pair" is undefined (removing the pair leaves the group connected), so I took reading 1. **Left out:** a chain whose
  only connection is the denied pair (A=B, B-C denied, C=D: is {A,B} merged?), and a denial reaching outside the
  established group (k1=k2=k3 with k1-k9 denied: is {k1,k2,k3} merged?). The two readings answer these differently.
  X-102, X-103 and X-105 still rest on reading 1 (each id judged alone, not a split into sub-groups); their
  `uncertainty` field says so.

## A2. A same-as question about an unstated pair inside a group
- Passage: `holds` §1, "A `same-as` question is judged by its stated names (ID-1)".
- Reading 1: only attestations of exactly that pair count, so same-as(d1,d3) with no direct claim is NOT_YET_KNOWN.
- Reading 2: the established closure answers it (True by transitivity).
- **Left out:** every holds(same-as) step on a pair that has no attestation of its own.

## A3. A same-as pair with only unreviewed claims
- Passage: v0.2 §5.6 (UNKNOWN: records visible, none decides; NOT_YET_KNOWN: nothing visible) and §6.2 (unreviewed
  claims are alternatives).
- Whether an unreviewed claim counts as a "visible record" for the status (UNKNOWN) or not (NOT_YET_KNOWN) is not
  fixed for same-as. **Left out:** holds(same-as f5,f6) for the system, and holds(same-as d1,d4) for fleet-desk.

## A4. A member of an unmerged group with no claims of its own
- After ID-5 refuses the merge, d3 and e2 have no claims of their own, but their unmerged aliases do. Whether that is
  NOT_YET_KNOWN (nothing about d3's content) or UNKNOWN is not fixed, and the assignment asks for no unknown cases.
  **Left out.**

## A5. Status of an established or denied answer
- The pack does not state the default basis of an `attest` / `deny` step, so the status (ASSERTED for testimony)
  is not fixed. **What I did:** no holds True / holds False step expects `status`; only DISPUTED (independent of basis)
  is expected.

## A6. Alternatives under identity
- Whether `alternatives` lists unreviewed claims about an alias's equivalent content (for example m1d for fleet-desk in
  X-104) is not fixed. **What I did:** `alternatives` is never expected; those claims are listed as forbidden (never
  cited), following question-format ("another perspective's unaccepted claim").

## Fixture notes (not gold ambiguities)
- Same-as steps carry no `start` / `end`: identity is timeless content (v0.2 §3.4) and SD-CAU-7 judges timeless claims
  independently of valid time. The fixture format does not say how a timeless attestation is written. If the loader
  needs an interval, give same-as steps an open start before T2 (for example `"start": "T1", "until_superseded": true`);
  no gold changes, because every question asks at T10.
- Non-system attesters (harbour-office, auditor-r, survey-lead, archive-clerk, intake-bot) are declared as
  `social-object` entities. The fixture format does not say whether they must be classified as agents.
- The assignment lists no boundary-condition slots, so `slots.json` is `{}`. No question has a numeric expected value,
  so there are no calculation sheets.
