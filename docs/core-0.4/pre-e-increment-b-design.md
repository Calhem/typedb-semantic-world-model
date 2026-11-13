# Pre-Stage E correction, increment B: one canonical per-content judgement (DI-1, DI-11, DI-5)

**Status: interface design and migration inventory, at the architectural review gate (LABS-1.037). No semantic change
has been made.** Branch `feature/pre-e-b-canonical-judgement`, from `main` at `7654587` (increment A merged).
Decisions: R-2, R-3 and R-4 with choices B, C and D, and the LABS-1.036 qualifications
([pre-stage-e-correctness-review.md](pre-stage-e-correctness-review.md), sections 1, 2 and 6). Increments C (DI-6)
and D (DI-2) and Stage E have not begun. The foundational ontology and the schema are unchanged by this design.

## 1. The problem, in the code
The core judges content in one place, `_judge` (model.py). It applies precedence between worlds, acceptance,
supersession, valid time and polarity, and returns per content class: holds, does not hold, or disputed, with the
deciding attestations. Everything after that is done by each reader on its own:

| Step after `_judge` | Done by |
|---|---|
| functional (single-value) conflicts | `_conflicts`, called by `_value`, `holds`, `facts_about` and `changes` only |
| conflicts under an *attested* constraint (an exclusive office) | `organisation.office_holders` and `offices_of`, by hand |
| naming the judgement | `_verdict_label` (dynamics), `_holding_label` and `_combine` (agency), each report's own vocabulary |
| why an undecided content is undecided | nobody: `_verdict_label` falls back to "not yet effective" (DI-5) |
| pending counter-claims | `_alternatives`, used by `holds` and `value_at` only |
| which judged contents a listing shows | `facts_about`: holding only (DI-1); `_claims`: all, without functional conflicts (DI-11) |
| which edges a traversal follows | `_closure`: holding only, disputed ones passed over silently; `_frame_edges`: holding and polarity-disputed (marked); `laboratory.provenance`: "established" via `_claims` |

Eight functions call `_judge` themselves (besides `_claims`), fifteen call `_claims`, and about ten more read their
output.
Section 6 lists every one.

## 2. The canonical record
One function in the core builds, for each content, one **content judgement** record. Every reader gets its facts from
these records. Nothing else judges content, names a judgement, or applies a constraint.

The record is a plain frozen data object (`ContentJudgement`, new module `src/worldmodel/judgement.py`), built from
the attestations a reader has already loaded, so it adds no database reads except for attested constraints
(section 2.3). Its fields fall into the six groups LABS-1.037 asks to keep apart.

### 2.1 Context: valid time, knowledge time, perspective and world
`context = (world, t, as_of, perspective)`. Every other field is true only for this context; two records are
comparable only when their contexts are equal.
- **t, valid time:** when the content is said to hold. A record is a judgement *at t*.
- **as_of, knowledge time:** only attestations, acceptances and supersessions recorded by `as_of` count (None: now).
- **perspective:** whose acceptances count (`acceptance_state`, `usable`, `superseded`, unchanged).
- **world:** the world asked about. A hypothetical or plan world sees its ancestors' attestations. A nearer world's
  deciding attestations override inherited ones for the same content (`_judge`'s depth rule, unchanged), and for
  functional types, a holding in the nearer world overrides inherited holdings for the same key. Each evidence item
  carries its `world` and `depth`, so a report can say "inherited" or "this world's own".

### 2.2 Evidence and claim polarity
- `content`: type, roles (canonical under the perspective's identity: co-referring names are one player), params.
- `evidence`: every visible attestation of the content, each with attester, polarity (assertion or denial), stance,
  basis, interval, world and depth, its acceptance state (accepted, unreviewed, rejected, retracted, superseded), what
  it says at t (holds, does not hold, silent) and its part in the judgement:
  `deciding` | `overridden` (a nearer world decides) | `restarted` (an ended holding re-attested later) | `silent`
  at t | `not usable` for the perspective.
- `assertions`, `denials`: the deciding accepted attestations on each side. Both non-empty means a **polarity
  dispute**.
- `pending`: unreviewed, not superseded attestations that would decide t if accepted (today's `alternatives`). They
  never decide, and never outrank an accepted attestation (choice D).

This layer is `_judge`, unchanged. No truth value changes in increment B.

### 2.3 Applicable single-value constraints
A constraint says: for the same players in its key roles, at most one value in its value role at a time (one place
per thing; one holder per exclusive office). Two kinds exist, and both go through the same check (`_conflicts`).
- **Declared constraints:** functional slots, stored as data (A0.3). They apply unconditionally, in every world and
  at every time. Installed today: `located-at` (located → place), `anchored-to` (frame → anchor), `positioned-in`
  (frame and positioned → position), `frame-transform` (child and parent → transform). No profile declares one.
- **Attested constraints:** a constraint that is itself a claim, such as `exclusive-office(office, context)`. Its
  scope is fixed by the profile: an exclusive office constrains `office-holding` keyed by class and context, with
  the holder as the value. **It applies only where its own content judgement, in the same context, is
  established.** It is judged by this same mechanism. If it is pending, unknown, denied or disputed, it is reported
  but never disputes holdings that are otherwise compatible (LABS-1.036).

The record lists `constraints`: every applicable constraint, each with its kind, key, value role, whether it applies
(and, for an attested one, its own judgement and support), and the rival contents it puts this content in conflict
with, by id and support. A rival counts only if it holds at the polarity layer, as today. Holdings with the same value
never conflict. Co-referring values are one value. Parameter values conflict only when they cannot both be true.

### 2.4 Established, disputed, not holding, pending and unknown
One judgement per record, decided in this order:

| `judgement` | When | `reason` |
|---|---|---|
| `DISPUTED` | a polarity dispute, or holding but in conflict under an applied constraint | `polarity`, `constraint`, or both |
| `ESTABLISHED` | holds at t, with no dispute | none |
| `NOT_HOLDING` | does not hold at t | `denied` (an accepted denial covers t) or `ended` (an accepted holding ended before t, with no denial) |
| `PENDING` | nothing accepted decides t, and a pending attestation would | none (the attestations are in `pending`) |
| `UNKNOWN` | nothing decides t | `not_yet_effective` (an accepted assertion begins after t), `end_unknown` (an accepted assertion has begun, with an unknown end: nothing is assumed to continue), `unaccepted` (only rejected, retracted or superseded attestations), `no_evidence` |

**This is the DI-5 correction.** An accepted attestation's reason always comes first: a pending counter-claim never
turns `not_yet_effective` or `end_unknown` into `PENDING`, and it stays listed in `pending`. Begun with an unknown end
is `end_unknown`, not "not yet effective" (choice C).

The record also keeps both statuses, as `facts_about` does today:
- `support_status`: the core rule (`answer_status`: STIPULATED > ASSERTED > INFERRED) over the deciding attestations,
  before any constraint;
- `status`: DISPUTED for a dispute, otherwise `support_status`.

**One labelling function** (`label(record)`) maps the record to the existing report vocabulary, so labels change only
where DI-5 says they must:

| Record | Label (claims vocabulary, `effects_of`, `causes_of`, …) | Label (holdings vocabulary, `capable`, profiles) |
|---|---|---|
| ESTABLISHED | accepted | established |
| DISPUTED | disputed | disputed |
| NOT_HOLDING / denied | denied | denied |
| NOT_HOLDING / ended | denied | expired |
| PENDING | unreviewed | not established |
| UNKNOWN / not_yet_effective | not yet effective | not yet effective |
| UNKNOWN / end_unknown | **not established** (was "not yet effective") | **not established** (was "not yet effective") |
| UNKNOWN / unaccepted | rejected, retracted or superseded (unchanged order) | not established |
| UNKNOWN / no_evidence | unknown | not established |

Registered DI-5 case: an accepted holding from day 8 with an unreviewed denial, asked on day 5, was "unreviewed" ("not
established" in `capable`). It becomes "not yet effective", with the denial in `pending`.

### 2.5 One content versus a report about many
The record is about **one content in one context** and carries nothing aggregated. Questions answered from several
contents (`capable`, `authorised`, `calibration_status`, `office_holders.status`, a closure's result) are separate
functions that read records. In increment B they keep their current aggregation rules (`_combine`, `_overall`)
unchanged, and only the per-content labels they read change (DI-5). Increment C replaces those rules (DI-6). When a
B label change alters an aggregate answer, the change is listed in section 7.

### 2.6 Established edges versus disputed or blocked edges
For traversals, a record gives one edge state:
- `traversable`: the judgement is ESTABLISHED;
- otherwise not traversed, reported with its judgement: DISPUTED (a **disputed edge**) or any other judgement (a
  **blocked edge**: pending, unknown, not holding).

Every closure follows traversable edges only, so its established answer is unchanged (choice B). It lists the edges
it reached but did not follow separately, each with its judgement and evidence. This is the rule
`laboratory.provenance` adopted in LABS-1.031 (`established`, `blocked_by`), made general.

## 3. The interface
In `WorldModel` (core). Each function takes `(world, …, t, as_of=None, perspective=SYSTEM)`, and selective and full
load give identical records.

| Function | Returns |
|---|---|
| `judgement(world, type, roles, t, …)` | the record of one content (NOT_YET_KNOWN context: an empty record with `no_evidence`) |
| `judgements_about(world, subject, t, types=None, …)` | the records of every content of `types` (all non-event, non-identity types by default) that involves `subject`, including rivals it needs for constraints, sorted as today |
| `judgements_of(world, type, t, …)` | the records of every content of a type, for traversals |
| `label(record, vocabulary="claims" or "holdings")` | the one labelling function |

Internally:
- `_records(atts, ident, ctx)` builds records from loaded attestations: `_judge`, then the constraint check, then the
  undecided reason;
- attested constraints are found through a small registry filled by profiles, mapping a constraint type to the
  content type it constrains, its key roles and its value role (section 8, Q2);
- `holds`, `value_at`, `value_of` and `exists` become projections of records into an `Answer`, with identical output.

**Retired:** `_claims`, `_verdict_label`, `_holding_label`, the per-reader calls to `_judge` and `_conflicts`,
and organisation's hand-built conflict. Every call site moves to the records in increment B. No adapter is left
behind, so no second path remains. `_judgement` (the profiles' shared helper) becomes `label` plus the record.

## 4. How listings and traversals use records
**Listings that return entries** gain disputed contents in place, each marked DISPUTED, citing the assertions,
the denials and any constraint rivals. Fields are only added, never removed or renamed:
`facts_about`, `roles_of`, `poses`, `frame_info`, `process_steps` (each step gains its own `status`).

**Answers that are sets of ids** keep exactly their established answer. They gain the disputed and blocked items as
a separate, opt-in report, so existing callers see no change:
- `parts`, `dependencies`: `report=True` returns `{"reached": [...], "not_traversed": [edges]}`;
- `materials`: `report=True` returns `{"materials": [...], "disputed": [...]}`;
- `composition`, `contents`: each node gains `not_traversed` (direct parts not followed, with their judgement), and
  the established tree is unchanged.

**Readers that already list everything** (`direct_dependencies`, `connections`, `effects_of`, `causes_of`, the
organisation and laboratory reports) read the record. They gain functional and attested-constraint conflicts (DI-11)
and the corrected labels (DI-5).

## 5. What is preserved
These answers do not change in increment B, and the reference worlds and the existing tests check that:
- `holds`, `value_at`, `value_of`, `exists`, `history`, `events`, `occurrence_status(...)["status"]`, `changes`;
- the merged `occurrence()` view (DI-2, increment D);
- the aggregation rules `_combine` and `_overall` (DI-6, increment C);
- `office_holders`: every field (choice A), now computed by the shared attested-constraint mechanism;
- the established answers of `parts`, `dependencies`, `materials`, `composition`, `contents` and `provenance`;
- `destroy`, which is a writer, not a report: it keeps ending what holds at the polarity layer.

## 6. Migration inventory
Every function that judges content or reads a judgement today. "F": through `facts_about`; "C": through `_claims`;
"J": calls `_judge` itself.

| Reader | Module | Today | Consumes | Change in B |
|---|---|---|---|---|
| `holds` | model | J + `_conflicts` | `judgement` → Answer | none (projection) |
| `value_at`, `value_of` | model | J + `_conflicts` | records of the slot → Answer | none |
| `exists` | model | J (existence; participation) | records → Answer | none |
| `facts_about` | model | J + `_conflicts`, holding only | `judgements_about` | **DI-1**: lists DISPUTED (polarity) |
| `direct_dependencies` | model | C | records | DI-11 (latent: no slot on `depends-on`) |
| `parts`, `dependencies` (`_closure`) | model | J, holding only | `judgements_of` | traversable = ESTABLISHED; `report=True` (B) |
| `destroy` | model | J | unchanged (writer) | none |
| `occurrence` (merged view) | model | merges accepted accounts (no content judgement) | unchanged | none (increment D) |
| `effects_of`, `_events_claiming`, `explain` | dynamics | C + `_verdict_label` | records + `label` | DI-5 labels |
| `changes` | dynamics | J + `_conflicts` per boundary | records per boundary | none |
| `occurrence_status` (details) | dynamics | `exists`; C for existence and describes | records + `label` | DI-5 labels |
| `causes_of` | dynamics | C | records + `label` | DI-5 labels |
| `process_steps` | dynamics | F | records | **DI-1**: disputed steps; per-step `status` |
| `capable`, `is_agent`, `_holdings` | agency | C + `_holding_label` + `_combine` | records + `label` + `_combine` | DI-5 labels; DI-11 |
| `roles_of` | agency | F | records | **DI-1**: disputed roles listed |
| `check_action` | agency | via `capable` | — | follows `capable` |
| `poses`, `frame_info` | physical | F | records | **DI-1**; constraint conflicts (already) |
| `composition`, `contents`, `materials` | physical | F | records | **DI-1**: `not_traversed` / `report=True` |
| `_frame_edges` (frame chains) | physical | J, holding and polarity-disputed | `judgements_of` | **DI-11**: an edge in a `frame-transform` slot conflict is DISPUTED (section 8, Q5) |
| `measurements` (report label) | qualities | C + `_verdict_label` | records + `label` | DI-5 labels |
| `connections` | mechanical | C | records | DI-11 (latent) |
| `employment`, `offices_of`, `authorised` | organisation | C + `_judgement` (+ `_combine`) | records + `label` | DI-5 labels; DI-11 |
| `office_holders`, `_constraint`, `_appointments` | organisation | C + `holds` + hand-built conflict | records (attested constraint) + `_overall` | none (choice A) |
| `provenance` (constitution chain, existence) | laboratory | C + `_judgement`, established paths | records; traversable | DI-5 labels; DI-11 |
| `calibration_status` | laboratory | C + `_judgement` + `_combine` | records + `label` + `_combine` | DI-5 labels; DI-11 |
| `interpretations` (`content_judgement`, `supports_answer`) | laboratory | C + `_judgement` | records + `label` | DI-5 labels |
| sampling accounts | laboratory | `occurrence_status`, `effects_of` | — | follows them |

Outside the library: `examples/` call public functions only. Two review probes (`probes/core04_d_review.py`)
read `facts_about` and will show DI-1. Their recorded outputs are historical and are not regenerated.

## 7. Intentional answer changes (authorised)
From the review's impact baseline on the reference worlds, to be re-run on merged `main` before implementation:
- **DI-1:** five contents newly listed by `facts_about` (`causes(o-relubrication, o-test-run)` in the gearbox world and
  two plans; `calibration-of(balance-b7, cert-b7)` in the laboratory world and one plan). `roles_of`, `composition`,
  `contents`, `materials` and `process_steps` are unaffected there. In tests, `test_m_d2_organisation.py` line 173 (an
  empty `roles_of` for a disputed role, kept "as instructed") changes on purpose.
- **DI-5:** 41 contents with a pending or superseded claim ranked before an accepted holding (shown today: Cal's
  appointment as site manager, Acme and its plan). Two contents that have begun with an unknown end
  (`classified-as(sample-12, hydrated)`, laboratory world and plan). `capable` answers change in these cases, so the
  LABS-1.026 equivalence baseline needs an approved update.
- **DI-11:** no reference-world change is expected for `_claims` readers (no slot on a type they read). Frame chains
  are checked by the new baseline (Q5).

Every other answer must be identical. An old-against-new equivalence probe compares every reader on every reference
world at every boundary time and lists each difference. Any difference outside this list stops the work.

## 8. Questions for the architectural review
| # | Question | Recommended |
|---|---|---|
| Q1 | Shapes: entry listings gain disputed entries in place; id-set answers keep their answer and gain an opt-in `report=True` (section 4) | approve |
| Q2 | Where attested-constraint scopes live: in the profile definition (like its schema), with the constraint instances attested as data. No schema change. The alternative, storing the scope as data, needs new attributes on `functional-slot` | profile definition |
| Q3 | Traversals follow ESTABLISHED edges only, so an edge in a constraint conflict is not followed. Today `_closure` would follow it; no installed slot is on `part-of` or `depends-on`, so no answer changes | approve |
| Q4 | Office exclusivity moves to the shared mechanism in increment B (choice A), answers unchanged, because it is the attested-constraint path of the canonical record | approve |
| Q5 | `_frame_edges` applies the `frame-transform` and `anchored-to` slots like every other reader (DI-11). Two accepted different transforms for one frame pair become disputed edges, so chains through them are DISPUTED | approve, subject to the baseline |
| Q6 | A newly found difference, not corrected: `_closure` and `_frame_edges` judge without the perspective's `same-as` identity, while every other reader uses it. Register it as **DI-12** (a deferred issue) rather than correct it in B | register |

## 9. Implementation plan (after approval)
1. Reproductions first: DI-1, DI-11 and DI-5 cases (the review's, plus each listing and traversal reader), and the
   impact baseline and the old-against-new equivalence probe on merged `main`.
2. Build `judgement.py` and `_records`. Make `holds`, `value_at`, `value_of` and `exists` projections, with output
   identical across the whole suite.
3. Migrate readers module by module (core, dynamics, agency, physical, qualities, then the profiles), running the
   equivalence probe after each: differences only where section 7 allows.
4. Remove `_claims`, `_verdict_label` and `_holding_label`.
5. Tests:
   - each judgement and reason;
   - each label in both vocabularies;
   - pending never outranks an accepted reason;
   - attested constraints: established applies; pending, unknown or disputed does not;
   - polarity and constraint conflicts together;
   - every listing reader shows a disputed content, citing both sides;
   - every closure keeps its answer and reports what it did not traverse;
   - contexts: perspective, knowledge time, inherited and hypothetical worlds;
   - selective and full load agree.
6. Full matrix on both query paths with all three profiles, benchmark of the main readers (records must add no
   reads except attested constraints), report, review gate.
