# Ambiguities recorded by author S

Each entry: the passage, the two readings, and what I did (left out, or designed around and left a field unexpected).

## A1. "Visible" in SD-SPA-2 for a perspective that cannot use the visible transforms
- Passage: SD-SPA-2 "No chain between distinct frames: NOT_YET_KNOWN when no `frame-transform` involving either is
  visible, UNKNOWN otherwise." Common §0.2 defines visibility by world and `as_of`; the perspective decides usability.
- Readings: (a) visible = recorded in the question world by `as_of` (an unreviewed or rejected claim counts), so the
  answer is UNKNOWN; (b) visible = usable for the perspective, so the answer would be NOT_YET_KNOWN.
- Done: left out every question where the readings differ. In S-004, S-009 and S-019 a transform involving one of the
  two frames is also usable for the perspective, so both readings give UNKNOWN.

## A2. Where a DISPUTED `transform_between` answer cites rival claims or an accepted denial
- Passage: the transform_between evidence table names conflicting evidence only as `search.inconsistent[*].support`
  ("status DISPUTED by an inconsistent edge"). TB-9 (two accepted different transforms for one pair) and polarity
  disputes (an accepted denial, v0.2 §5.3) also make the answer DISPUTED, but no field is named for their evidence.
- Readings: (a) the rival claims or the denial are cited as conflicting evidence in some field; (b) they are not
  cited at all.
- Done: in S-012, S-013, S-022 and S-024 the status and `transform: None` are expected. The rival claims or the
  denial and assertion are listed as admissible conflicting evidence (§0.4 role), and nothing is required.

## A3. Which edges of an inconsistent cycle are reported in `search.inconsistent`
- Passage: TB-7 / TB-8 "An inconsistent edge on a route: DISPUTED"; the output table says `search.inconsistent` holds
  "each inconsistent edge with its sources".
- Readings: the edge found inconsistent depends on the search order (any edge of the triangle can be the one checked
  against the composition of the others), and "its sources" may or may not include the composed path's transforms.
- Done: S-010 and S-011 list all three triangle edges as admissible conflicting evidence and require none.

## A4. Inherited content in a variant after its branch point, and the override rule
- Passage: v0.2 §6.2 "restricted to valid times before β (their starts before β; their endings counted only before
  β)"; TB-13 "A variant's own transform overrides the inherited one".
- Readings: (a) an inherited claim holds in the variant only at valid times before β; (b) an inherited claim that
  started before β continues past β unless the variant overrides it.
- Done: the only variant question (S-003) asks at T4, before branch_at T6, where both readings agree. No question
  tests the override of an inherited transform for the same pair, since an override at t >= β depends on this reading.

## A5. What counts as one "edge examination" under `limit`
- Passage: TB-2 "`limit`: the maximum number of edge examinations of one search"; TB-6 breadth-first search.
- Readings: the order in which a frame's edges are examined is not fixed, and it is not stated whether an edge is
  counted once per content or once per attestation, or whether verification checks share the budget.
- Done: designed around it. In S-024 the source has exactly two edges, so with limit 2 breadth-first search reaches
  the target whatever the order, and status DISPUTED / `transform: None` holds even if the search had completed
  (TB-8). `search.truncated: true` is expected but marked in `uncertainty`. S-025 uses a target three hops from a
  source of degree 1, so one examination cannot reach it whatever the counting. `reason` texts (which contain N)
  are not expected anywhere.

## A6. A later different transform by the same attester under `until_superseded`, and `end` evidence names
- Passage: fixture-format "With `until_superseded: true` the content holds until its attester records otherwise";
  §0.5 gives `end` the name `<step>` but also says a restatement of X by `end()` counts as X.
- Readings: a later different claim for the same pair could end the earlier one automatically, or be its rival (TB-9).
  An `end` step's attestation could be cited as `<end step>` or as the restated step.
- Done: designed around both. The hall-gantry change uses an explicit `end: T10` on `hg` and a new claim `hg2` from T10
  (S-020, S-021, S-006). No `end` op is used.

## A7. A claim with neither `end` nor `until_superseded` (end unknown) as a chain edge
- Readings: after its start the edge is undecided and so unusable (no chain), or it counts as holding.
- Done: left out. Every fixture transform has an exact end or `until_superseded`.

## A8. `frames` field contents and order; `verified` on DISPUTED answers
- The `frames` field is named but neither its order nor whether it includes the endpoints is fixed, so it is not
  expected. `search.verified` is fixed only for INFERRED (TB-8) and for truncated-but-reached UNKNOWN (TB-11), so it is
  not expected for DISPUTED answers, including the truncated S-024.

## A9. Probe acceptance for SD-SPA-1 / SD-SPA-2
- The assignment says to accept `absent`. If the approved field were present with its approved value (1e-9 rad;
  basis convention), that is neither in `accept` nor fabricated. `prohibited` names only values that contradict the
  approved decision.
