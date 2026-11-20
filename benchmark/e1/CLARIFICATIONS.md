# Stage E1 benchmark clarifications (LABS-1.052)

The questions, fixtures and expected answers frozen at `d0f0aa2`, and the original results in `results/`, are
**unchanged**. These clarifications define a **revised evaluation**, kept apart from the original. It is applied only
by `uv run python -m evaluation.run --revised`, through `revised/overlay.json`, and writes `results-revised/`. Each
clarification below says which questions it touches and how.

## C1. Required evidence for list answers
For a template whose answer is a list (`office_holders` holders, `parts`, `dependencies`, `aliases`), **required
evidence** is what supports the listed items, and any conflict the answer reports. A claim that only explains why a
candidate is *not* listed (an expired or denied appointment, a stipulated removal in a plan) is **explanatory**: it may
be cited, but its absence is not a shortfall.
- Applied through the overlay to **X-003**: `s-bea-out`, which removes Bea from the plan's holders, moves from required
  to explanatory evidence.

## C2. Writer-specific interval defaults
The fixture format's rule "without `until_superseded` and without `end`, the end is UNKNOWN" is the core `attest`
rule. A profile writer that documents another default **overrides** it. `laboratory.calibrate` attests "from `start`
to `end` (or until superseded)", so a calibration step with no end holds until superseded. The benchmark README
stated the core rule as if every writer used it.
- Applied through the overlay to **LAB-010**: expected `established`, not `not established`.

## C3. Restatements are the original claim's evidence
When the library ends or corrects a fixture claim (`end()`, or `move()` ending a location claim), it writes a
superseding **restatement** by the same attester, of the same content, from the same start, under a minted id. An
answer citing the restatement cites the original claim.
- Applied to **every question**: the harness maps a restatement to its step's name (same attester, content, start and
  world), reading each attester's own view with the public `visible` reader. This resolves **LAB-034**.

## C4. Role names (reconciliation R2)
Readers take a content type's **core role names**: a profile role is stored under the core role it specialises, and
a profile's own new role under its own name. Other names are refused with `UnknownRoleError`. The organisation module
notes now give `office-holding(classified: holder, class: office, context)`. The frozen
`spec/reader-docs.md` (extracted at `6364fdf`) still shows the old notation `office-holding(holder, office, context)`:
**this file supersedes it.**
- Applied through the overlay to **ORG-011**: re-asked with `classified`, `class` and `context`. Its expected answer
  (`disputed`) is unchanged.

## C5. Functional exclusivity (reconciliation R3)
A content whose single-valued slot holds **another established value** at t does not hold: `not holding`, `holds`
false with status INFERRED (World Ontology v0.2 4.4). This is decided before `pending`. A disputed slot decides
nothing. Recorded as an addendum to the increment B design, 2.4.
- Applied through the overlay to **TEMP-017**: expected `not holding` with INFERRED, not `pending` with UNKNOWN.

## R1. Resolved role players
For a role with no applying constraint, the players are the resolved role-player set: `resolved`, from the compared
accounts only (MP-2). They are not ER-5's listing of every linked account's players, which still includes unaccepted
accounts.
- Applied to **every `event_role` question** whose role has no applying constraint. This resolves **LAB-025** and
  **LAB-026**.

## Evidence tier
E1 is recorded as **development-tier** evidence: model-authored inside the project, with no inter-author agreement
measured and nothing sealed. The external, sealed, human-authored evaluation (`docs/phase-1c/05-withheld-evaluation-spec.md`)
is **deferred**. All 272 development questions are kept (LABS-1.052).
