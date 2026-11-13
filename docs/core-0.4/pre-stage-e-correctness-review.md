# Pre-Stage E correctness review (LABS-1.034)

**Status: analysis for review. No semantic change has been made.** Stage E does not begin until the correction
decisions below are approved. Branch: `feature/pre-stage-e-correctness-review`, from `main` at `a8c4b44`.

**Evidence.** Two probes, run against `main` as merged. Each builds its own throwaway database and deletes it.
- `probes/pre_e_review_reproductions.py`: an executable reproduction of DI-1 to DI-6, DI-8 and the newly found DI-11.
  Each case prints the current behaviour and asserts it, so the probe fails once a correction changes that behaviour.
  Output: `probes/pre_e_review_reproductions.out.txt`.
- `probes/pre_e_review_impact.py`: what each correction would change in the three reference worlds (gearbox with
  every extension, Acme, laboratory, and their variant worlds). It reads every content's judgement for every subject,
  at every time an attestation starts or ends. Output: `probes/pre_e_review_impact.out.json` (11 worlds,
  24,120 content reads, 35 minutes; the time is itself evidence for DI-9).

## 1. The common causes
The issues are not independent. Three architectural causes explain all of them.

**C1. Two reporting paths, each with its own blind spot, plus per-report labels and folds.** The core judges each
content correctly once (`_judge`: holds, does not hold, or disputed between an accepted assertion and an accepted
denial). Each reader then decides, on its own, what to show and how to name it:

| Path | Used by | Polarity disputes | Functional (slot) conflicts | Labels and folds |
|---|---|---|---|---|
| F: `facts_about` | `roles_of`, `composition`, `contents`, `materials`, `poses`, `frame_info`, `process_steps` | **dropped** (DI-1) | applied | none |
| C: `_claims` | `capable`, `direct_dependencies`, `effects_of`, `occurrence_status`, every profile report | kept | **ignored** (DI-11, new) | `_verdict_label` falls back to "not yet effective" (DI-5); `_combine` takes the first accepted status, `_overall` folds to ASSERTED (DI-6) |
| `holds`, `value_of` | direct questions | kept | applied | the core rule (`answer_status`) |

Only `holds` and `value_of` get everything right, and they answer one content at a time. DI-1, DI-5, DI-6 and DI-11 are
four symptoms of one missing piece: **a single, complete, per-content record** (judgement, polarity and functional
conflicts, pending counter-claims, status, support and evidence), built once by the core and read by every report,
with one labelling rule and one aggregation rule. The recursive-provenance defect fixed under LABS-1.031 was the same
pattern in a traversal: a report presenting a link without its full judgement.

**C2. Cardinality is expressed in three unrelated ways, and not at all for event roles.** "These cannot both be true"
is known to the core only through functional slots on propositions (A0.3). The organisation profile has a separate
mechanism (the `exclusive-office` content). Event descriptions have none (DI-2), and a value role such as a joint kind
has none (DI-3). Vocabulary is untyped (DI-4), so "a different value" means only "a different id".

**C3. Composite writes have no default unit of work.** A single transaction for several writes exists (`_batch`), but
only `measure()` uses it. Helpers also write outside it: `claim_effect` commits its outcome content in a transaction
of its own. Hence DI-8, which is wider than registered.

## 2. The issues

### DI-1: polarity-disputed content omitted from generic reports (C1)
**Current behaviour** (reproduction "DI-1 current"). Bea's analyst role is asserted by HR and denied by the auditor,
and the system accepts both. Then:
- `holds` says DISPUTED, and `capable` says "disputed";
- `facts_about(bea)` lists nothing, and `roles_of(bea)` is empty.

The same happens to a disputed `part-of`: `composition(wheel)` has no parts, and `process_steps(proc)` has no steps.
`direct_dependencies` (path C) lists its own disputed case correctly, as DISPUTED. The register named `roles_of`,
`process_steps`, `poses` and `frame_info`. The review adds **`composition`, `contents` and `materials`**, and notes
that `process_steps` gives no per-step status at all.

**Expected semantics** (v0.2 §5.3, "never silent"): a listing reader lists every content involving the subject whose
judgement at t is "holds" or "disputed". A disputed content is marked DISPUTED, and cites the accepted assertions and
the accepted denials. Closure readers (`parts`, `dependencies`) keep traversing established edges only, as the
LABS-1.031 provenance rule does. They should report a disputed edge they meet, rather than pass over it silently.

**Placement:** foundational core (`facts_about` and the core readers). The profile reports already comply.

**Impact on existing judgements:** no judgement changes, because `_judge` is untouched. Listings change: they gain
the disputed entries. Reference worlds (11 worlds, 24,120 content reads): **5 contents** would newly be listed:
`causes(o-relubrication, o-test-run)` in the actual gearbox world and two of its plans, and
`calibration-of(balance-b7, cert-b7)` in the laboratory world and one plan. Neither type is read by `roles_of`,
`composition`, `contents`, `materials` or `process_steps`, so only `facts_about` itself changes there. The profile
reports that read them already show them as disputed. Tests that assert an empty `roles_of` for a disputed role change
on purpose: `test_m_d2_organisation.py` line 173 asserts the current behaviour "as instructed".

**Regression tests:**
- each listing reader lists a polarity-disputed content as DISPUTED, citing both sides;
- an entry is listed only while the content is disputed (before the denial, and in a perspective that accepts only
  one side, the plain answer is unchanged);
- functional and polarity conflicts on one content together;
- closures do not traverse a disputed edge, and say so;
- `process_steps` gives each step's status;
- selective and full load agree.

**Complexity:** medium. It depends on the shared per-content record (C1), and goes in the same change as DI-11 and DI-5.

### DI-2: conflicting single-valued event participants (C2)
**Current behaviour** ("DI-2 current"):
- two accepted replacement accounts of one occurrence name different removed parts (b1, b2). The merged
  `occurrence()` view lists both under the role, with no DISPUTED;
- two accepted sampling accounts of one occurrence name different products (s-a, s-b), with the same result;
- each account's own report is correct.

The review also found that **the merged view mixes two role vocabularies**. A specialised profile role is listed
under its core role name (`removed` as `patient`, `product` as `destination`), while an unspecialised one keeps its
profile name (`fitted`).

**Expected semantics** (v0.2 §3.2, D9). A profile can declare a role of an event type single-valued, for example
"a replacement removes one part". In the merged view, two or more distinct players of such a role, compared under the
perspective's identity (two co-referring names are one player), make that role DISPUTED, citing each description and
its source. Roles not declared single-valued stay as today. The account-level reports, and whether the occurrence
happened, are unaffected.

**Placement:**
- the mechanism is core: single-valued event roles stored as data, like functional slots (A0.3). They are named by
  core role names, inherited by subtypes, and need no schema change;
- the declarations belong to profiles: replacement `removed` and `fitted`, sampling `product`, the official in an
  official act. Each is a domain decision, because a replacement may remove two parts, and a sampling may produce
  several aliquots.

**Impact:** only the merged occurrence view, and only for occurrences whose accepted accounts name different players
in a declared role. Reference worlds: **one occurrence**, `o-bearing-replacement`, whose accepted
accounts name different removed parts (bearing-1 and bearing-3). It appears in the actual gearbox world and two plans
that inherit it. If the replacement profile declares `removed` single-valued, it becomes DISPUTED there. That is the
intended reference conflict of D-1.

**Regression tests:**
- a declared single-valued role with two players across two accepted accounts gives DISPUTED, citing both;
- the same across perspectives (one account accepted) and knowledge times;
- co-referring players (`same-as`) are not a dispute;
- an undeclared role stays a union;
- a declaration in one profile applies to the subtypes of that event type;
- the role vocabulary of the merged view is consistent (one naming rule, decided with this issue).

**Complexity:** medium to high: a new declaration kind, the merged-view judgement and the profile declarations. It
depends on C1, which gives the DISPUTED entry its shape. It should follow DI-8, so accounts are written whole.

### DI-3: conflicting joint kinds (C2, interacts with DI-11 and DI-4)
**Current behaviour** ("DI-3 current"). The design office says the cover is bolted, and an inspection says bonded.
Both are accepted, and both are ASSERTED.

**Feasibility, newly verified** ("DI-3 feasibility"). A functional slot keyed by the two-player `endpoint` role
(`declare_slot("connected-to", ("endpoint",), "joint-kind")`) is accepted. With it, `holds` and `facts_about` report
the two joints DISPUTED with each other. **But `mechanical.connections` still reports both ASSERTED** (DI-11). The
register's "not verified" question is answered: the core supports it, and the profile report does not.

**Expected semantics:** a domain decision. Parts can genuinely have several joints (bolted *and* sealed), so a slot
over all joint kinds would invent disputes. A slot is right only for a family of mutually exclusive kinds. That needs
the kinds to be typed (DI-4).

**Placement:** the mechanical profile (its declaration and its vocabulary), once DI-11 is fixed in the core.

**Impact:** none until a declaration is made. **Recommendation:** keep as an accepted limitation. Revisit after DI-11
and DI-4, if a mutually exclusive joint-kind family is wanted.

### DI-4: dependency-kind vocabulary not validated (C2)
**Current behaviour** ("DI-4 current"). `depend(..., kind="steel")` is accepted. `direct_dependencies` reports kind
`steel`, and `dependencies(kind="steel")` follows it.

**Expected semantics:** a dependency kind is a category marked as one, for example
`classified-as(k, dependency-kind)` (as materials are marked). A dependency naming an unmarked kind should still be
recorded, because refusing evidence loses information. It should be reported with its kind flagged "not a recognised
dependency kind", and never counted as one of the recognised kinds.

**Placement:** core. The dependency kinds are core vocabulary (core-0.4-d). The same vocabulary-typing pattern would
serve profile vocabularies (joint kinds, DI-3).

**Impact:** reports gain a flag. No judgement changes. Reference worlds: every dependency kind used is a seeded one.

**Regression tests:** a seeded kind is unflagged; an unmarked kind is recorded and flagged; a kind-filtered closure
ignores unmarked kinds; a marking that is itself disputed.

**Complexity:** low. **Recommendation:** keep as an accepted limitation before Stage E. If the read-time flag is
wanted, it is independent of everything else and can be done at any point.

### DI-5: the "not yet effective" label (C1), wider than registered
**Current behaviour:**
- **the registered case** ("DI-5 current"): Cal's accepted holding from day 8, with the auditor's unreviewed denial,
  is "not established" on day 5. Dan's identical holding, without a counter-claim, is "not yet effective";
- **wider, newly found** ("DI-5 wider"): an accepted holding that began on day 1 with no stated end is reported
  **"not yet effective" on day 5**. It has begun. Its continuation is unknown, because nothing is assumed to continue
  (`holds`: UNKNOWN).

The cause is one fallback in `_verdict_label`. An undecided content with an accepted attestation is labelled by the
first attestation state found, and failing that, "not yet effective", whatever the reason it is undecided.

**Expected semantics.** The label follows *why* the accepted attestation does not decide t:
- if it begins after t, "not yet effective";
- if it has begun and its end is unknown, "not established" (as `holds` says UNKNOWN);
- unreviewed or rejected counter-claims never outrank an accepted attestation. They are listed as pending
  alternatives (as `holds` lists `alternatives`).

**Placement:** core (`_verdict_label` and `_holding_label`, used by `capable` and every profile report).

**Impact:** labels only. `holds`, `status` and the truth value are unchanged. Reference worlds:
- **603** accepted contents are undecided at a sampled time because they have not begun: correctly "not yet effective";
- **41** have a pending or superseded claim ranked before the accepted holding (the registered case). Most are
  gearbox contents that no labelled report shows today. Shown today: Cal's appointment as site manager (Acme and its
  plan);
- **2** are labelled "not yet effective" although they have begun with an unknown end (the wider case):
  `classified-as(sample-12, hydrated)` in the laboratory world and its plan.

Once C1 gives every report the same per-content record, the corrected labels apply to all of these.
`capable()` answers change in these cases, so the LABS-1.026 equivalence baseline needs an approved update.

**Regression tests:**
- each undecided reason gets its label: begins after t; begun with end unknown; only unreviewed claims; only rejected
  claims;
- a pending counter-claim alongside an accepted not-yet-effective holding;
- the same through `capable`, `office_holders`, `authorised` and the laboratory reports;
- across perspectives and knowledge times.

**Complexity:** low, but it changes a shared label, so it belongs in the C1 change.

### DI-6: folding several statuses into one (C1)
**Current behaviour** ("DI-6 current"):
- **`office_holders`:** Bea (inherited, ASSERTED) and Cal (the plan's, STIPULATED) both hold the office in the plan.
  The office's overall status is ASSERTED;
- **`capable`, newly found:** two mirror-image cases disagree. Dan holds the role generally (inherited, ASSERTED) and
  in the depot (stipulated): STIPULATED + ASSERTED, answered ASSERTED. Cal holds it generally (stipulated) and in the
  depot (inherited): answered STIPULATED. `_combine` takes the status of whichever holding sorts first (the general
  one), not a rule.

There are three aggregation rules in use:
- `answer_status`, the core rule: STIPULATED > ASSERTED > INFERRED, all evidence listed;
- `_combine`: first in list order;
- `_overall`: one status if all agree, else ASSERTED.

**Expected semantics.** Two cases, both defined in the core:
- **one question answered by several contents** (`capable`, `authorised`): the status is the core rule applied to
  the union of the applicable accepted support, exactly as `holds` does for one content. Every holding stays listed;
- **a report over distinct items** (`office_holders`: several holders): no folded support status. Each item keeps its
  own status. The overall field keeps only what is well defined for the set: DISPUTED (a conflict), UNKNOWN or
  NOT_YET_KNOWN. This is the register's option (b).

**Placement:** core (`_combine`, and a shared helper for reports). The organisation profile adopts it (`_overall`).

**Impact:**
- `capable` and `authorised` status in mixed-support cases only;
- `office_holders.status` whenever holders are established: it no longer gives a support status;
- reference worlds: **none**. No `capable()` or `office_holders()` answer there folds different statuses (checked at
  eight times per world). The defect is shown only by the constructed cases above.

**Regression tests:**
- the two mirror cases give the same status;
- the status equals `holds` on the union of support;
- `office_holders` with mixed holders gives no folded status;
- DISPUTED, UNKNOWN and NOT_YET_KNOWN are unchanged;
- across worlds (inherited and stipulated).

**Complexity:** low to medium. It changes an API field's meaning, so it needs a decision and an inventory of changed
answers.

### DI-8: non-atomic composite writes (C3), wider than registered
**Current behaviour** ("DI-8 current"). A failure before `take_sample`'s second effect claim leaves the account with
one of its two claimed effects, and nothing marks it incomplete.

**Wider, newly found:**
- core composite writers are not atomic either: `account` without a batch (up to four transactions), `record_event`
  (Core 0.3), `create_thing` (entity, then existence) and `destroy` (several ends and denials: a failure leaves a
  thing half destroyed). `replace_part` is as registered;
- **the registered option (a) does not work with today's API** ("DI-8 batch feasibility"):
  - **case a:** with batch passed through `account` and `claim_effect`, a sampling whose outcome contents already
    exist is written whole, in one transaction;
  - **case b, a new sample:** `claim_effect` fails inside the batch. It first commits the outcome content in a
    transaction of its own (`WorldModel.proposition`), which the batch's earlier transaction cannot see. Nothing of
    the batch is written, but the outcome content is left behind;
  - **case c:** a failure in the middle of a batch leaves nothing.

**Expected semantics:** every function that records one source's statement as several writes writes all of them or
none. Content written as a side effect (an outcome proposition) is written in the same unit.

**Placement:**
- core: `claim_effect` writes its outcome content in the caller's batch; `account` always runs as one unit;
  `record_event`, `create_thing` and `destroy` likewise;
- profiles: `take_sample` and `replace_part` call these in one batch.

**Impact:** none on judgements. Every answer is unchanged when no failure occurs. The existing suite is the
regression baseline.

**Regression tests:** fault injection at every write step of each composite writer. After the failure, no attestation,
no description and no orphan content remain. Success paths give identical ids and answers. A batch read sees its own
writes.

**Complexity:** low to medium. The traps are reads made outside the batch's transaction (snapshot isolation, shown by
case b) and id minting. It has no dependencies.

### DI-11 (new): `_claims`-based reports ignore functional conflicts (C1)
**Current behaviour** ("DI-3 feasibility and DI-11"). With a slot declared, `holds` and `facts_about` say DISPUTED, and
`connections` says ASSERTED for both. This is latent today, because no installed slot is on a type that a `_claims`
report reads. It blocks DI-3 and any future profile slot on a reported type.

**Expected semantics:** every report applies the same functional-conflict judgement as `holds`.

**Placement:** core (the shared per-content record).

**Impact:** none on today's reference worlds. Regression tests and complexity are as DI-1 (one change).

## 3. Interactions with DI-3, DI-4 and DI-5
- **DI-3 needs DI-11 and DI-4.** A joint-kind slot only becomes visible in `connections` once DI-11 is fixed. It is
  only correct for a mutually exclusive family of kinds, which needs typed vocabulary (DI-4).
- **DI-4 is a vocabulary question shared with DI-3 and DI-2.** "Different value" is decided by ids. A typed vocabulary
  would let a profile say which kinds exclude each other. Not needed for DI-2: the participants are particulars,
  compared under identity.
- **DI-5 is a C1 issue, wider than registered.** It sits in the same labelling function as DI-1's and DI-11's
  conflicts, and DI-6's fold reads its labels. All four should be corrected in one coordinated change, with one
  inventory of changed answers.
- **DI-2 builds on C1 and DI-8.** Its DISPUTED entry should have the same shape as every other dispute. Its accounts
  should be written whole before they are compared.

## 4. Recommended correction sequence
Each step is its own decision, branch, tests and review gate.

| Step | Issues | Why this order | Changes judgements? |
|---|---|---|---|
| 1 | **DI-8** (all composite writers; `claim_effect` inside the batch) | independent; makes every later fixture and test write whole records | no |
| 2 | **C1: one per-content record and one labelling rule**: DI-1, DI-11, DI-5 (with its wider case) | one shared function; one inventory of changed answers | listings gain disputed entries; labels change; no truth value changes |
| 3 | **DI-6**: one aggregation rule (one question; a report over distinct items) | reads step 2's labels | statuses in mixed-support cases; `office_holders.status` |
| 4 | **DI-2**: single-valued event roles as data, profile declarations, one role vocabulary for the merged view | needs step 2's DISPUTED shape and step 1's whole accounts | merged occurrence view only |
| 5 | **DI-3, DI-4**: stay accepted limitations; revisit once steps 2 and 4 exist | profile and vocabulary decisions | none until decided |

Steps 1 to 4 resolve everything the register requires before Stage E: DI-1, DI-2 and DI-8, the DI-6 review, and
DI-11 as proposed here. The foundational ontology is unchanged by all of them. No schema change is expected: the new
declarations are data, as functional slots are.

## 5. Decisions for approval
| # | Decision | Recommended |
|---|---|---|
| R-1 | The correction sequence of section 4 | approve |
| R-2 | DI-1: listing readers list polarity-disputed content as DISPUTED, citing both sides; closures traverse established edges only and report disputed ones | approve |
| R-3 | Register DI-11, and correct it with DI-1 (one per-content record for every report) | approve |
| R-4 | DI-5: label by why the content is undecided; pending counter-claims never outrank an accepted attestation; widen to "begun, end unknown" | approve |
| R-5 | DI-6: the core rule over the union of support for one question; no folded support status for reports over distinct items | approve |
| R-6 | DI-2: core mechanism (single-valued event roles as data); declarations by profiles; one naming rule for roles in the merged view | approve |
| R-7 | DI-8: all-or-nothing composite writers, including the core ones, with `claim_effect` writing inside the batch | approve |
| R-8 | DI-3 and DI-4 stay accepted limitations until steps 2 and 4 are done | approve |
