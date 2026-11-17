# Pre-Stage E consolidation: deferred issues and Stage E entry criteria

**Status: proposal under LABS-1.045, at architectural review.** Branch `feature/pre-e-consolidation`, from merged
`main` `9464403` (increments A to D). No deferred correction is implemented here, and Stage E has not begun. Evidence
that is new in this review comes from `probes/pre_e_consolidation.py` (output `.out.txt`), run on a throwaway database.

Stage E is the plan's **final validation** ([core-0.4-plan.md](../plans/core-0.4-plan.md), section 5): a cross-domain
suite green on both paths twice with no leftover databases; equivalence (whole answers, evidence included) for every
new query; the performance thresholds of section 9.4, kept separate for unchanged Core 0.3 workloads and new Core 0.4
workloads; a records-per-change table across the three domains. An issue therefore **blocks Stage E** when Stage E's
suite would have to record a wrong or unstable answer as expected, or when a Stage E measurement would be meaningless
without it.

## 1. Recommendations
| # | Issue | Recommendation | Why, in one line |
|---|---|---|---|
| DI-1, DI-5, DI-8, DI-11 | corrected in increments A and B | **close with evidence** | merged; permanent tests; 106,752-answer baseline |
| DI-6 | aggregate status | **close with evidence** | merged in increment C; rule Q and rule C tested |
| DI-2 | single-valued event roles | **close with evidence**, except the residual DI-15 | merged in increment D (`9464403`); 398 views; 25 examples |
| DI-3 | conflicting joint kinds | **close with evidence** (mechanism); the domain choice stays documented | the existing slot mechanism already disputes them if declared (probe) |
| DI-4 | open dependency-kind vocabulary | **defer beyond Stage E** | unchanged by increment D; a vocabulary policy, not a correctness defect |
| DI-7 | no formal derivation provenance | **investigate during Stage E** (first design item) | a Stage E requirement; Stage E's evaluation must flag INFERRED answers meanwhile |
| DI-9 | performance | **investigate during Stage E**; baseline before entry | the thresholds are a Stage E deliverable; the Core 0.3 workload is unmeasured since A0 |
| DI-10 | explorer browser tests | **defer beyond Stage E** | maintenance; no answer depends on it |
| DI-12 | traversals ignore same-as | **correct before Stage E**, with DI-15 and DI-16 | same root cause as DI-15; equivalence under identity is a Stage E criterion |
| DI-13 | one player per role per account | **correct before Stage E (decision first)** | common joint events cannot be recorded faithfully; a co-signed act is falsely DISPUTED |
| DI-14 | variant lists descriptions without accounts | **investigate during Stage E** | reporting only; no judgement affected; `accounts` now says `none` |
| **DI-15 (new)** | an occurrence's aliases are listed but never compared | **correct before Stage E** | the merged view gives contradictory answers for two names of one occurrence |
| **DI-16 (new)** | identity merges on a disputed same-as | **decide before Stage E** | identity ignores the canonical judgement every other content follows |

Proposed order: one **identity increment** (DI-15, then DI-16's decision, then DI-12, which shares the code path),
and one **cardinality decision** (DI-13), each with its own design gate. Then the Stage E entry check (section 4).

## 2. The open issues
### DI-3: conflicting mechanical joint kinds: close with evidence
- **Still relevant after increment D?** Not as a missing mechanism. Increment D's constraints are for event roles and
  do not apply to `connected-to`, a proposition. But the existing functional slots (A0.3, judged canonically since
  increment B) already cover it: declared in the probe database, a slot keyed by `connected-to`'s two endpoints (one
  role played twice) with value `joint-kind` turns "bolted" against "pressed" for one pair from two ASSERTED answers
  into two DISPUTED ones (`pre_e_consolidation.out.txt`, DI-3). The register's open question ("needs slot support for
  a multi-player key role, not verified") is answered: it works.
- **What remains** is a domain choice, not a defect: whether a pair of parts has at most one joint kind. Often it
  does not (bolted *and* sealed). Declaring the slot would be a mechanical profile change (0.3, through
  `upgrade_profile`), to be decided only if a scenario needs it.

### DI-4: open dependency-kind vocabulary: defer beyond Stage E
`depend(kind="steel")` is still accepted (probe). Increment D does not touch dependencies. The remedy (classify
kinds as `dependency-kind` and check on write) is a vocabulary policy; no answer is wrong today, since an unseeded kind
is reported as written. Stage E's extensibility checks may record it as a known limitation.

### DI-7: no formal derivation provenance: investigate during Stage E
Unchanged: an attestation with basis `inference` is reported INFERRED without a named rule or premises. It is a Stage E
design item by the register's own terms. Until it is designed, Stage E's reasoning evaluation must not count INFERRED
answers from basis alone as derivations (entry criterion R-3).

### DI-9: performance: investigate during Stage E, baseline before entry
- **Retained (LABS-1.045):** `occurrence()` after increment D costs about **19 → 86 queries** and **23 → 100 ms** per
  view, about **4.4×**, on every view (`probes/pre_e_d_occurrence_bench.out.txt`); the query breakdown is
  `probes/pre_e_d_occurrence_queries.py`. Not optimised.
- **Earlier findings:** D-3 reports of 336 and 411 queries; cross-world slowdown ×1.6–2.8 at equal query counts;
  office exclusivity +5 to 66 queries on the subjects it concerns, including `changes`.
- **Cost of the canonical judgement itself:** measured twice as zero added queries (increment B mechanism split;
  increment C aggregation). The cost is in what is judged per call (exclusivity, identity, per-account link judgement),
  not in the judgement rule.
- **Gap:** the unchanged Core 0.3 workload (plan 9.4, `scripts/bench_instrumented.py`) was last measured at A0, and
  its thresholds were never demonstrated because run-to-run variation was as large as the differences. Increments B
  to D changed every reader's judgement path since then. Stage E cannot report against 9.4 without a fresh baseline
  (entry criterion P-1).

### DI-10: explorer browser tests: defer beyond Stage E
Maintenance; the explorer's data, escaping and offline behaviour are tested, and format 2 renders.

### DI-12, DI-15 and DI-16: identity: correct before Stage E, as one increment
- **DI-15 (new): an occurrence's aliases are listed but never compared.** v0.2 (section 3.2): an occurrence's
  descriptions are those linked "to *o* (or to anything accepted as `same-as` *o*)", and a declared single-valued role
  with different players is DISPUTED. Probe: `act-1-hr` describes `o-1` (official bea), `act-1-clerk` describes
  `o-1-alias` (official cal), both accepted, and `same-as(o-1, o-1-alias)` accepted. `occurrence(o-1)` lists both
  accounts and both players, but judges the official **established: bea**; `occurrence(o-1-alias)` judges it
  **established: cal**. The alias's account has `describes: None`, although its link's canonical judgement is
  established. Cause: `_event_roles` judges the links through `_contents(world, occurrence, …)`, which selects contents
  by the occurrence's own id, the "related, smaller difference" DI-12 records. The 398-view baseline did not show it:
  no reference world has an accepted same-as link. Expected after correction: DISPUTED from both names, both cited.
- **DI-16 (new): identity merges on a disputed same-as.** `Identity` unions every usable same-as assertion and ignores
  denials. With `same-as(bea, b-smith)` asserted and accepted, then denied by an accepted denial, the canonical
  judgement of that content is DISPUTED, yet `identity()` still merges bea and b-smith, so a role with bea in one
  account and b-smith in another is **established** rather than DISPUTED. This predates increment D (the Core 0.3 rule
  "only accepted ones merge" is satisfied to the letter); since increment B every other content is judged by its
  canonical record, and identity is the exception. Options: (a) merge only on an ESTABLISHED same-as (a disputed
  identity splits the group, so dependent judgements become disputes); (b) keep accepted-merges and report the
  dispute beside each merged answer; (c) keep and document. Recommended: (a), with the same reproducibility rule as
  rejection (from the denial's recording time on). This is a core semantic change: it needs its own decision.
- **DI-12: traversals ignore same-as.** Unchanged (no reference world affected), but it is the same code path as DI-15
  (selection by own id), and Stage E's equivalence criterion is defined under the perspective's identity
  (v0.2 section 4.2, semantic equivalence). Correcting DI-15 without DI-12 would leave two identity rules in the core.

### DI-13: one player per role per account: correct before Stage E, decision first
- **Does it prevent faithful representation of common events?** Yes. One description cannot name two players of a
  role (refused by TypeDB, `[CNT5]`), so a joint action has to be recorded as several accounts from one source:
  - a two-technician job becomes two accounts from one source (probe): the union is right, but one source's single
    account is misrepresented as two, and the account count (and any "accounts agree" reasoning) is distorted;
  - a **co-signed official act** (two officials sign, one source records it) becomes two accounts, and ER-6's
    unconditional official constraint makes it **DISPUTED**: a false conflict (probe);
  - the same holds for multi-part replacements (only safe because ER-6 scopes `removed` to one-for-one), meetings with
    several participants, team sampling and several aliquots.
- **Options:** (a) declare `@card(0..)` on the event roles whose multiplicity depends on the operation (core `actor`,
  `patient`, `participant`-like roles; profile roles such as `removed`, `fitted`), then judge constraints over
  accounts with per-account sets (a constrained role is DISPUTED when the established accounts name different
  *sets*); (b) keep one player per account and add an explicit "joint" or "co-signed" kind that scopes the constraint
  off (ER-2 already supports kinds); (c) keep and document. (a) changes core schema annotations and needs a migration
  like ER-7; (b) needs no schema change but leaves multi-agent accounts split.
- **Recommended:** decide before Stage E, because Stage E's records-per-change table and cross-domain suite would
  otherwise fix today's representation as the expected one. A minimal path is (b) for the official act now and (a) as
  a designed increment.

### DI-14: variant lists descriptions without accounts: investigate during Stage E
Hypothetical-world inheritance is as specified (a link with no start is inherited whole; an account after the branch
point is not), and every judging reader finds no account. Since increment D, `occurrence()`'s `accounts` reports such
an account as `none`, but `descriptions`, `occurrence().descriptions` and `process_steps` still list it unmarked.
Stage E's hypothetical-world cases should include it; the remedy (mark, or write links from the event's start) can be
chosen with them. Not blocking: no answer's judgement is affected (18 reference views, all checked).

## 3. Focus questions (LABS-1.045)
- **DI-3 and DI-4 after increment D:** DI-3 no longer needs a mechanism (slot keyed by the endpoint pair works); DI-4
  is unaffected and remains a vocabulary policy.
- **Same-as identity and event-role judgements:** players are grouped correctly under accepted identity, including per
  perspective and knowledge time (X3; probe). Two gaps: occurrence aliases are listed but not compared (DI-15), and a
  disputed identity still merges players (DI-16).
- **Account-level cardinality:** prevents faithful representation of joint actions and causes a false dispute for
  co-signed acts (DI-13).
- **Hypothetical-world inheritance and reporting:** inheritance is consistent and the nearest world decides role
  judgements (X6b, X6c, X7d to X7d4); the reporting gap is DI-14.
- **Computational cost:** the judgement rule is free; what it is applied to is not. Event-role reporting costs about
  4.4× on every occurrence view; identity and per-account link judgement dominate. Recorded in DI-9.

## 4. Proposed Stage E entry criteria
Each is measurable, checked on the `main` commit that opens Stage E, and reported in one entry report.

**Semantic correctness**
- S-1. Every issue marked "correct before Stage E" (DI-12, DI-13, DI-15, DI-16) is resolved by an approved, merged
  increment, or explicitly re-classified by an approved decision.
- S-2. Each such resolution adds permanent tests reproducing its probe case (for DI-15: both names of the occurrence
  give the same DISPUTED judgement; for DI-16: per the chosen option).
- S-3. The 106,752-answer baseline and the 398-view baseline are re-frozen on the entry commit; every difference from
  the previous freeze is listed and attributed to an approved change (0 unexplained differences).
- S-4. The register lists no issue without a recommendation and owner decision.

**Regression stability**
- T-1. The full suite passes in all four configurations, twice, on the entry commit (8 of 8 runs), with 0 leftover
  `wm-test-*` or `wm-upgrade-tmp-*` databases and no warning from the project's own code.
- T-2. Reproducibility: a reference database rebuilt from the entry commit gives 106,752 of 106,752 answers identical
  to the re-frozen baseline once attestation ids and clock times are masked.
- T-3. Order independence: the permanent result-order tests pass (shuffled and reversed query results).

**Performance benchmarking**
- P-1. A fresh baseline of the unchanged Core 0.3 workload (`scripts/bench_instrumented.py`) on the entry commit
  against `b64f635`, alternating, at least 10 runs each, reporting median, p95 and the coefficient of variation. If
  the variation exceeds the section 9.4 tolerance (10 %), the noise is reduced (quiet machine, pinned resources)
  before any threshold is judged; thresholds are reported as met, missed or not demonstrable, never inferred.
- P-2. The Core 0.4 benchmarks (`bench-d3`, `pre_e_b_read_bench.py`, `pre_e_d_occurrence_bench.py`) re-run on the
  entry commit, three alternating rounds, with query counts (deterministic) and time spreads; this is the reference
  for DI-9 work inside Stage E.
- P-3. Agreed budgets before Stage E starts: for example `occurrence()` ≤ 100 queries per view on the reference
  worlds, and no report above 500 queries. Stage E then measures against them.

**Reasoning evaluation**
- R-1. A fixed evaluation set of questions with expected answers, written before Stage E's implementation and frozen:
  the section 3 scenarios of the plan, the design examples of increments A to D, and cross-domain questions (each
  question: world, perspective, knowledge time, expected judgement, status and cited support).
- R-2. Coverage: every judgement (ESTABLISHED, DISPUTED, denied, expired, pending, unknown, not yet known) and every
  context dimension (perspective, knowledge time, valid time, hypothetical world, identity) appears in at least one
  question.
- R-3. INFERRED answers from basis alone are scored separately from derivations until DI-7 is designed.
- R-4. Scoring is exact on judgement and status and set-based on support; an answer counts as correct only if its
  evidence is the expected evidence.

**What blocks Stage E:** S-1 (DI-15, DI-16, DI-12, DI-13 decisions), S-3, T-1, T-2 and P-1. **Investigated within
Stage E:** DI-7, DI-9 (against P-2 and P-3), DI-14. **Beyond Stage E:** DI-4, DI-10.

## 5. Decisions requested
1. Accept the classification in section 1, including the two new issues DI-15 and DI-16.
2. Approve designing the identity increment (DI-15, DI-16, DI-12), with DI-16's option to be decided at its design gate.
3. Choose DI-13's direction ((a), (b), or (b) now and (a) designed later), for its own design gate.
4. Approve the entry criteria in section 4, or amend them (in particular the budgets in P-3).
