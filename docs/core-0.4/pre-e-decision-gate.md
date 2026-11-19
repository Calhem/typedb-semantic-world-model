# Pre-Stage E architectural decision gate (LABS-1.047)

**Status:** for decision. Nothing here is implemented: DI-12, DI-13, DI-15 and DI-16 stay open, the correction designs
stay on `feature/pre-e-corrections-design`, and Stage E has not started. `main` is `bf60c1f`.

Sources: [pre-e-identity-design.md](pre-e-identity-design.md) (identity), [pre-e-di16-clarification.md](pre-e-di16-clarification.md),
[pre-e-multiplicity-design.md](pre-e-multiplicity-design.md) (multiplicity), [pre-e-performance-baseline.md](pre-e-performance-baseline.md)
(the 60-question baseline, kept as the original) and section 4 below (the controlled repeat).

## 1. Identity: ID-1 to ID-10

### 1.1 The decisions (verbatim from the identity design, section 9)
> - **ID-1.** An identity link is judged by its stated names with the canonical polarity layer, never through identity.
> - **ID-2.** Two names are one thing only where a link between them is ESTABLISHED in the context; disputed, denied,
>   pending, unknown and contextually inapplicable links join nothing. (Resolves DI-16 by its option (a).)
> - **ID-3.** Identity is timeless: valid time does not enter; stated intervals on same-as are ignored, and new same-as
>   attestations with an interval are refused.
> - **ID-4.** Identity classes are the connected components of established links.
> - **ID-5.** A component containing two names whose own link is disputed or denied is not merged at all, and the
>   conflict is reported.
> - **ID-6.** The nearest world decides each link; a variant's denial or stipulated link applies in it and its
>   descendants only.
> - **ID-7.** Identity is per perspective and knowledge time (unchanged).
> - **ID-8.** Every reader uses this identity and selects contents by the subject's class (DI-12 options (a) and the
>   selection difference), except frame chains and `parts_in_database`.
> - **ID-9.** `occurrence()` gives one view for every name of an occurrence (DI-15), with additive `aliases` and
>   `identity` fields.
> - **ID-10 (optional).** `descriptions()` lists by the describes link's canonical judgement, as `occurrence()`'s
>   `accounts` does.

### 1.2 What each decides
"Cases" are the executed checks of `probes/pre_e_identity_cases.out.txt` (28 checks; 6 change under the design).
Impact on the reference worlds is **none** for every decision: they hold no same-as content (0 in the rebuilt
reference database), so the 106,752-answer and 398-view baselines cannot change.

| | Precise rule | Addresses | Impact on existing behaviour (outside the reference worlds) | Essential? |
|---|---|---|---|---|
| ID-1 | A same-as link's judgement uses only the attestations naming that pair, keyed by the names as written | F-1: today a link is judged through identity itself (I15 reads established with no record; I18's established v1~v2 reads disputed) | `judgement("same-as", ...)` answers change in chains (I15, I16, I18); merges are unaffected by ID-1 alone | **Essential**: ID-2 builds identity from link judgements, which must not depend on identity |
| ID-2 | A link merges only when ESTABLISHED in (world, as_of, perspective) | DI-16; LABS-1.046 item 2 | Merges stop where an accepted denial disputes the link (I3, I9 after the denial); answers that compared players under that merge become DISPUTED or separate | **Essential** (DI-16; required for DI-15's alias views to be correct) |
| ID-3 | Identity is one per context, for all valid times; intervals on same-as are ignored; a new same-as with `start`/`end` is refused | A time-indexed identity would break content classes keyed by canonical names | Merges unchanged (already timeless, I10); `judgement("same-as")` stops saying "not yet effective"/"ended"; the write refusal is new | Timelessness **essential** once ID-2 ties identity to a judgement (which needs a time); the write refusal is a guard, separable |
| ID-4 | Classes = connected components of established links | Transitivity requirement | None (today's union-find, restricted by ID-2) | **Essential** (defines the classes) |
| ID-5 | If two members of a component have their own link DISPUTED or NOT_HOLDING by denial, no member of the component is merged; `identity()` reports the conflict | Conflicting-evidence requirement; I16 (a chain would override a denial) | I16: s1, s2, s3 all separate; roles they play become DISPUTED where single-valued | **Essential** (without it transitivity defeats ID-2) |
| ID-6 | The nearest world's judgement of a link decides; variant denials/stipulations apply to that variant and its descendants | F-2: I12, a plan's stipulated denial is ignored today | Plans that deny an inherited link separate the names in the plan only | **Essential** (hypothetical-world requirement) |
| ID-7 | Per perspective and knowledge time | Temporal and perspective requirements | None (as today; I8, I9 before, I11) | **Essential** (restated, unchanged) |
| ID-8 | Every reader takes the context's identity and selects by class; `parts`/`dependencies` traverse classes | DI-12 | Readers that selected by own id (office holders, appointments, dependency listing, `occurrence_status` records, closures) now see aliases' contents | **Essential** (it is DI-12) |
| ID-9 | `occurrence(x)` is the same view for every member `x`; additive `aliases` and `identity` | DI-15 | Alias views include every account and judge roles once | **Essential** (it is DI-15) |
| ID-10 | `descriptions()` lists a description only when its describes link is canonically established | Two listings of one occurrence disagree where a link is disputed | A description with a disputed link stops being listed by `descriptions()` | **Optional** (see 1.5) |

### 1.3 Treatment of same-as evidence that is not established (ID-2)
| Link judgement in the context | Example | Treatment |
|---|---|---|
| **DISPUTED** (accepted assertion and accepted denial in the deciding world) | I3, I9 after the denial, DI-16 | joins nothing; if the pair is also connected through other established links, the component is in conflict (ID-5) |
| **Denied** (NOT_HOLDING: an accepted denial, or the source's own denial superseding its assertion) | I4, I6, I12 in the plan | joins nothing; counts as conflict evidence under ID-5 |
| **Pending** (only unreviewed assertions) | I2, I11 for other perspectives, I17 | joins nothing; breaks a chain; **not** conflict evidence (no one has said the names differ) |
| **Unknown** (rejected or retracted assertions, no evidence) | I5 | joins nothing; not conflict evidence |
| **Contextually inapplicable** (another world's own links, a base's links after a variant's knowledge limit, decisions after `as_of`, other perspectives' acceptances) | I13 base, I14, I8 before, I11 | never seen by the judgement, so joins nothing |

Wording to settle before implementation: ID-5 says "disputed or denied"; section 3.5 of the design says "DISPUTED or
NOT_HOLDING by denial". Recommended exact wording: *"whose own link judgement is DISPUTED or NOT_HOLDING"* (a source
withdrawing its own assertion by a denial, I6, is a denial).

### 1.4 Where transitive identity could still establish a wrong equivalence
The design is conservative against recorded negative evidence (ID-5), but transitivity itself remains a source of
equivalences no one stated. Cases, with what the design does:
- **TI-1. Chains no source asserted.** a~b by one source and b~c by another, both accepted, make a and c one thing
  (I15), although no attestation names a with c. If b is a homonym (one name used for two things), a and c are wrongly
  merged. Nothing detects it unless someone records a ≠ c. The design reports the links used (`identity()`'s `links`,
  `occurrence()`'s `identity`), but answers do not flag that their identity was derived. *Recommendation:* accept as
  inherent to transitivity; add, in the implementation, a per-pair `derived` marker (merged only through a chain) in
  `identity()`'s report. Not a semantic change.
- **TI-2. Contradictions that are not denials.** If a and c are merged by a chain but have incompatible properties
  (different places at one time, different kinds), ID-5 does not fire: only same-as denials count. The contradiction
  surfaces as a DISPUTED value (functional conflict), not as an identity conflict. Not silently established, but
  reported as a property dispute rather than its cause. *Recommendation:* accept for now; register as a limitation.
- **TI-3. Intervals ignored (ID-3).** A same-as stated for a period (two records naming one thing only during it)
  merges at every time, also outside the period. Today's behaviour is the same (I10); the reference worlds hold none.
  The write refusal stops new cases; existing ones remain. *Recommendation:* approve with the refusal, so the risk is
  limited to data written before the increment (none known).
- **TI-4. Selective path completeness.** ID-5 needs every denial among a component's members. The selective path
  grows the component through established links and loads both polarities for every reached name, so the denial is
  found, but this must be tested on both paths with shuffled loads (gate in the design, section 7). A missed denial
  would merge wrongly on one path only.
- Over-separation, not wrong equivalence: ID-5 unmerges the **whole** component, so one denied pair at the far end of a
  large component separates every name in it. Conservative by design (alternative (c), a minimal cut, is not unique).

### 1.5 Recommendation on ID-10 (separate; not assumed approved)
- **What it changes:** `descriptions()` would list a description only when its describes link is canonically
  established, as `occurrence()`'s `accounts` already judges it. Today it lists by a *usable* link, so a disputed link
  still lists its description.
- **Measured impact on the reference worlds: none.** Across the 398 frozen views, 433 account entries: the 93 listed
  by `descriptions()` all have an established ("accepted") link, the 340 not listed all have a non-accepted link
  (computed from `probes/pre_e_d_occurrence_baseline.json.gz`; no disputed describes link exists there).
- **Not needed** for DI-12 or DI-15 correctness: ID-9 makes `occurrence()` correct whether or not ID-10 is adopted.
- **Recommendation: approve, as the last, separately reviewed step of the identity increment** (its own commit, its
  own before/after count), because it removes a contradiction between two readers of one occurrence on the same
  principle as increment B. If it is not approved, the difference is documented in the README as known behaviour and
  `descriptions()` is unchanged.

## 2. DI-16 for decision

### 2.1 Register entry (exact, as at `bf60c1f`)
> | DI-16 | identity merges on a same-as whose canonical judgement is DISPUTED (accepted denials are ignored) | consolidation (LABS-1.045) | proposed: decide before Stage E | open (decision needed) |

> **Classification.** Predates increment D and satisfies the Core 0.3 rule as written ("only accepted ones merge"), but
> since increment B every other content is judged by its canonical record; identity is the exception. Options: (a) merge
> only on an ESTABLISHED same-as, from the denial's recording time on (earlier views stay reproducible); (b) keep, and
> report the dispute beside merged answers; (c) keep and document. **Recommended:** decide before Stage E (a core
> semantic change, with its own design gate).

(The register row of `deferred-issues.md` on the design branch now reads "open: … designed, at review"; the section
above is unchanged.)

### 2.2 Reproduction and expected results
`uv run python -I probes/pre_e_di16_repro.py` (one throwaway database; code unchanged; output
`probes/pre_e_di16_repro.out.txt`). hr asserts `same-as(bea, b-smith)`, clerk denies it, the system accepts both; two
accepted official acts describe `o-2`, one naming bea, one b-smith; the official is single-valued (organisation 0.2).

| Context | Today (executed) | After option (a) (expected; becomes a permanent test) |
|---|---|---|
| system, now | same-as DISPUTED; merges **yes**; official **established** {bea, b-smith} as one player | same-as DISPUTED; merges **no**; official **DISPUTED**, both accounts cited |
| system, as known before the denial | same-as established; merges yes; official established, one player | unchanged |
| hr (own assertion only) | established; merges yes; official established: bea | unchanged |
| clerk (own denial only) | not holding; merges no; official established: b-smith | unchanged |

### 2.3 How option (a) works with ID-2, ID-5 and ID-6
- **ID-2 is option (a)'s rule:** the DISPUTED link joins nothing, so bea and b-smith are two players and the
  single-official constraint makes the role DISPUTED (row 1).
- **ID-5 extends it to chains:** if bea and b-smith were also connected through a third name by established links, the
  whole component would stay unmerged and the conflict would be reported, so the denial cannot be bypassed (I16, I18).
- **ID-6 places it in worlds:** the denial decides in the world where it is the nearest evidence; a plan that stipulates
  a denial separates the names in that plan only (I12), and a base denial recorded after a plan's knowledge limit does
  not reach the plan.
- **ID-7 keeps it reproducible:** views at a knowledge time before the denial are unchanged (row 2).

### 2.4 Consequences
- **Semantic:** answers become more conservative: established → DISPUTED (or two separate things) wherever a merge
  rested on a disputed link; a single accepted denial is enough to split, by the acceptance model the perspective
  chose. Identity can now change over knowledge time from merged to separate.
- **Compatibility:** no schema change, no data migration; the reference baselines are unaffected (no same-as). A view
  frozen by the old code after a denial differs from the corrected code exactly where DI-16 applied. `identity()`
  gains `conflicts` and `links` (additive).
- **Not done:** DI-16 is not implemented and not closed; it would close only with the merged identity increment, with
  this reproduction as a permanent test.
- **Recommendation:** adopt option (a), as specified by ID-2, ID-5 and ID-6.

## 3. Multiplicity: MP-1 to MP-5

### 3.1 The decisions (verbatim from the multiplicity design, section 9)
> - **MP-1.** A core module `core-0.4-event-multiplicity` opens `event:actor`, `event:patient`, `event:instrument` and
>   `event:destination` to several players per account; profiles open their own specialised roles only in their next
>   versions: organisation 0.3 `official`; mechanical 0.3 `removed`, `fitted`; laboratory 0.2 `sampler`, `product`.
> - **MP-2.** Several players of a role in compared accounts are judged per account set: a union without a constraint;
>   under `one`, DISPUTED with the reason "several players in one account" or "accounts name different players"; under
>   `set`, established when every compared account states the same set, otherwise DISPUTED.
> - **MP-3.** Event-role constraints gain an optional `role-multiplicity` (`one` when absent); an applicable kind-scoped
>   declaration wins over an unconditional one; conflicting kind-scoped declarations are refused when declared.
> - **MP-4.** Organisation 0.3 adds the category `organisation:co-signed` and the `set` declaration for its official;
>   mechanical and laboratory declare no new constraint.
> - **MP-5.** Existing databases upgrade explicitly (`upgrade_to_event_multiplicity()`, then `upgrade_profile`), with an
>   actionable error when the order is wrong; the upgrade is documented as one-way once used.

### 3.2 Roles, one by one
A specialised profile role can hold several players only if its core role is open as well (TypeDB counts the
specialising players against the parent's cardinality: `probes/pre_e_di13_cardinality.out.txt`, C3, C4). Opening a
core role therefore also opens it for **plain events**, which is how `move()` records movements (patient = the thing,
destination, origin, optional actor: `src/worldmodel/model.py`, `move`).

| Role | Recorded in | Design | Justification on record | Recommendation |
|---|---|---|---|---|
| `event:actor` | movements, replacements, any event | open | two-technician job recorded as two accounts (LABS-1.045 probe) | **open** |
| `official-act:official` (as actor) | organisation | open in 0.3 | co-signed act falsely DISPUTED (LABS-1.045 probe) | **open**; stays `one` unless the act is established as `organisation:co-signed` |
| `sampling:sampler` (as actor) | laboratory | open in 0.2 | team sampling (DI-13 register) | **open** (union; no constraint) |
| `event:patient` | movements (the thing moved), replacements | open | needed by `removed`; several things acted on at once | **open** (a movement of several things to one destination is coherent; each thing's location is its own effect) |
| `replacement:removed` (as patient), `replacement:fitted` | mechanical | open in 0.3 | multi-part replacement (DI-13 register) | **open**; one-for-one replacements keep `one` on both (M10) |
| `event:destination` | movements, `sampling:product` | open | several aliquots (DI-13 register) | **defer**: opening it lets one movement account name two destinations as a silent union (no constraint applies to plain events), and a `one` declaration on `event` to guard movements would also constrain `product`, because constraints are additive along subtypes by an approved increment D rule (`_event_constraints`: "a subtype never loses an inherited constraint") |
| `sampling:product` (as destination) | laboratory | open in 0.2 | several aliquots | **defer with `event:destination`** |
| `event:instrument` | replacements, events (e.g. one press in the reference world) | open | **none recorded**: no case, probe or register entry needs several instruments | **do not open** (not justified) |
| `event:location` | any event | single | one place an account is about | single |
| `event:origin` | movements, `sampling:sampled` | single | pooled samples left for a later decision | single; see the observation below |
| `official-act:office`, `office-context`; `sampling:sampled` | profiles | single | an act is under one office; one sampled source | single |

**Observation from reading `move()` (probe `probes/pre_e_mp_move_origin.py`, section 3.6).** `move()` writes `origin`
as a list of every place the mover's own records hold the thing just before; if they hold two, the write meets the
single-valued origin.

### 3.3 Co-participation against conflicting accounts (MP-2), and exclusivity
- **Co-participation** is several players **inside one account**: one source, one description, one attestation. Without
  a constraint it is a union (M1, M11, M12). Under a `set` declaration it is judged as a whole: established when every
  compared account states the same set (M2, M5).
- **Conflict** is different evidence **across accounts**: under `one`, two accounts naming different players are
  DISPUTED, "accounts name different players" (M4, unchanged from increment D); under `set`, accounts stating different
  sets are DISPUTED, each set cited (M6, M7). A shorter account is never assumed to be merely incomplete (M6).
- **Exclusivity stays as established:** a role declared `one` stays single-valued in meaning. An account naming two
  players of it is DISPUTED with the reason "several players in one account" (M3, M9, M10), never established. Office
  exclusivity (an attested constraint on office holding) is a different content and is untouched. Which accounts are
  compared (accepted, describes link established, nearest world, kind classification, identity) is unchanged.
- **Identity:** sets are taken under the corrected identity, so two names count once only where their link is
  established (M8, M9).

### 3.4 Schema, migration and export, per decision
| | Schema change | Data migration | Export format | Recommendation |
|---|---|---|---|---|
| MP-1 | yes: `@card(0..)` on the opened roles (new core module; profile next versions) | none; existing descriptions have one player per role, which the wider cardinality accepts (C2) | none: annotations already exported from the schema text | **approve, amended**: open `actor`, `patient` and the profile roles `official`, `sampler`, `removed`, `fitted`; defer `destination`/`product`; do not open `instrument` |
| MP-2 | none | none | none | **approve** |
| MP-3 | yes: optional attribute `role-multiplicity` | none (absent = `one`, today's meaning) | the attribute appears as any attribute | **approve**; opening `destination` later needs its own design (a movement guard compatible with additive inheritance, e.g. a `movement` event type or kind) |
| MP-4 | profile data: category `organisation:co-signed` and one declaration | none | none | **approve**. Note: the design's section 3.4, headed "MP-4: reading and reporting", describes the additive output fields (`multiplicity`, the two `one` reasons); no decision's wording covers them. Recommended: approve them as part of MP-2 |
| MP-5 | the upgrade transaction | none rewritten; explicit and idempotent; refused without the event-role module | none | **approve** |

### 3.5 Existing accounts and provenance
Confirmed by the design and the TypeDB probe: an existing description reads exactly as before after a role is opened
(C2); nothing is rewritten; one description stays one account, with one attestation, one describes link and one
source. Old code on an upgraded database reads several players as lists and judges a co-signed act DISPUTED, never
wrongly established (conservative). The only irreversible step is narrowing a role once data uses several players (C5),
documented as one-way.

### 3.6 Probe result: `move()` and a single-valued origin
Probe `probes/pre_e_mp_move_origin.py` (output `probes/pre_e_mp_move_origin.out.txt`; one throwaway database, deleted;
library code of `bf60c1f` unchanged):

| Case | Result |
|---|---|
| 1. the thing located at `p1` only, then moved to `p3` (control) | move recorded |
| 2. the same attester locates the thing at `p1` and at `p2` over the same interval, then moves it to `p3` | **refused at commit** by TypeDB: `[CNT5] Constraint '@card(0..1)' has been violated: found 2 instances` on `event:origin` |

So `move()` fails, with a raw database error rather than an explanation, whenever the mover's own records already hold
a functional conflict about the thing's location. Nothing is half-written (the whole transaction is rolled back), but
the movement cannot be recorded at all. This is a defect in `move()`, **not a reason to open `origin`**: an origin
naming two places would assert that the thing left both, which no source said. It belongs with DI-13 and is
recommended as part of the multiplicity increment: `move()` should take the origin only when the mover's records
agree on one place, and otherwise record the movement without an origin (or refuse with an explanatory error), with a
permanent test of case 2. It does not change MP-1 to MP-5.

## 4. Controlled performance results
Records: [bench-pre-e-controlled/](bench-pre-e-controlled/) (one JSON per run, `runs.log`, the container records);
summary: `python3 -I probes/pre_e_core03_baseline_summary.py docs/core-0.4/bench-pre-e-controlled --first 60`
([summary.md](bench-pre-e-controlled/summary.md)). The 60-question baseline
([bench-pre-e-baseline/](bench-pre-e-baseline/)) is kept unchanged as the original.

### 4.1 Conditions
- **Same as the original:** TypeDB `3.14.1` (same image digest), Python 3.13.17, driver 3.14.0, the same two
  implementations (`bf60c1f` entry, `b64f635` Core 0.3) from their own worktrees and environments, workload
  `scripts/bench_query_paths.py` unchanged (200 objects, 30 places, 1,000 moves, seed 11), the same wrapper.
- **Changed:** 180 selective questions per run (`--queries 180`; with the fixed seed the first 60 are exactly the
  original 60); two discarded warm-ups (one per implementation); 20 alternating runs M C C M M C ... (10 each),
  13:24 to 17:31 UTC on 2026-11-18. Every run exited 0 with no error output; selective and full answers were identical
  in 20 of 20 runs.
- **Containers:** 10 unrelated services were stopped at 13:24:21 UTC and restarted at 17:30:45 to 17:31:07, none deleted
  (gupi-typedb, noodlelab-api, noodlelab-typedb, apex-web, apex-api, apex-typedb, newslens-worker, newslens-api,
  newslens-web, newslens-typedb; all `restart=unless-stopped`, all running again afterwards). Kept running by the
  owner's decision: the four `crm-*` development services, used by another active session (its API restarted once
  during the window), and `wm-typedb` itself. So the machine was quieter than before (6 running containers instead of
  16), **not quiet**; CPUs were not pinned.

### 4.2 Results (10 runs each; median of run values, min-max, CV)
| Measure | Core 0.3 `b64f635` | Entry `bf60c1f` | Difference | 9.4 threshold | Result |
|---|---|---|---|---|---|
| selective median (180 q.) | 46.6 ms (43.6-52.7, 6.0 %) | 44.0 ms (41.5-69.9, **18.6 %**) | -5.8 % | +10 % | **not demonstrable** |
| selective p95 (180 q.) | 76.8 ms (66.2-94.4, **10.7 %**) | 70.8 ms (64.7-116.5, **22.9 %**) | -7.9 % | +15 % | **not demonstrable** |
| full-load median | 3,830.8 ms (2.0 %) | 3,781.1 ms (2.3 %) | -1.3 % | +10 % | **met** |
| ingestion (1,000 moves) | 59.3 s (**12.4 %**) | 48.4 s (**16.4 %**) | -18.5 % | +10 % | **not demonstrable** |
| database size | 12.36 MB (0.3 %) | 10.37 MB (0.2 %) | -16.1 % | +5 % | **met** |
| answers identical, selective = full | 10 of 10 | 10 of 10 | - | identical | **met** |
| selective: queries / attestations per question | 13.1 / 7.0, every run | 13.1 / 7.0, every run | equal | - | - |
| full: queries / attestations per question | 9.1 / 3,276.5, every run | 9.1 / 3,276.5, every run | equal | - | - |
| first 60 questions only: selective median / p95 | 49.4 / 69.9 ms (CV 7.2 / 14.8 %) | 48.5 / 68.1 ms (CV 17.3 / 20.0 %) | -2.0 / -2.7 % | +10 / +15 % | not demonstrable |
| original baseline (60 q., for comparison) | 48.1 / 67.0 ms | 52.2 / 83.3 ms | +8.5 / +24.4 % | | not demonstrable |

**Question by question** (each of the 180 questions against itself, median of 10 runs): entry / Core 0.3 = min 0.65,
p10 0.91, **median 0.95**, p90 1.02, max 1.10; no question more than 25 % slower. TypeDB time per question 43.5 → 40.0
ms, Python 3.0 → 4.0 ms (medians of run medians).

**Tail:** questions above 120 ms per run: Core 0.3 [1, 2, 1, 0, 0, 0, 0, 1, 0, 1] (6 of 1,800), entry
[2, 9, 7, 2, 3, 2, 0, 0, 0, 2] (27 of 1,800); pooled p99 98.7 → 128.2 ms. The high CVs come from a few slow runs, most
of them early in the window (entry runs 4 and 5, 14:21 to 14:45 UTC; Core 0.3's slowest runs 2, 3 and 6 fall in the
same period). No run was excluded.

### 4.3 Reading the results, kept apart
1. **Regression against Core 0.3.** The original baseline's typical-question slowdown (ratio 1.11) **does not
   reproduce**: on 180 questions under quieter conditions it is 0.95, at equal query counts. Full load and storage meet
   their thresholds; ingestion is faster in this session but noisy. The selective median, selective p95 and ingestion
   thresholds remain **not demonstrable**: the variation still exceeds the 10 % tolerance, so none is reported met or
   missed. **Unexplained:** the entry commit's heavier tail (27 against 6 slow questions, in 3 of its runs). Whether
   that is the implementation or the machine is not established by these runs.
2. **Absolute latency and throughput** (this machine, one connection, not judged against any agreed budget because
   none exists yet, P-3): about 44 ms per selective `value_at` question (some 20 questions a second; p95 about 70 to 77
   ms); about 3.8 s per question on the full load; about 48 s per 1,000 moves (median move 38 ms, some 20 moves a
   second). The selective path is about 85 times faster than the full load on this workload.
3. **Query amplification in `occurrence()`** (not part of the Core 0.3 workload, so not measured by these runs):
   recorded at increment D on the 398 reference views, about 19 → 86 queries and 23 → 100 ms per view (x4.4), 7,755 →
   34,351 queries in all. Query counts are deterministic; they were not re-measured for this gate, and P-2 re-measures them on the entry commit. This is DI-9, to be judged against P-2 and the P-3 budgets, not against the 9.4 thresholds.
4. **Measurement uncertainty.** Two sessions on the same day disagree on the direction of the selective difference
   (+8.5 % and -5.8 % on the run-level median), which is the clearest sign that this machine's noise is larger than
   the effect being measured. Further reduction needs a genuinely quiet machine (all other services stopped, no other
   session active) or pinned CPUs for the TypeDB container; more runs alone would narrow the medians but not the
   tail.

## 5. Outstanding Stage E blockers
Section 4 of [pre-stage-e-consolidation.md](pre-stage-e-consolidation.md), status on the current `main` (`bf60c1f`).
**Stage E is not ready.** The regression suite passing (600 x 4) is not sufficient and is not claimed as readiness.

| Criterion | Status | What remains |
|---|---|---|
| S-1: DI-12, DI-13, DI-15, DI-16 resolved | **open** | the identity increment (DI-12, DI-15, DI-16) and the multiplicity increment (DI-13, with the `move()` origin defect, section 3.6), each approved and merged |
| S-2: permanent tests per resolution | open | with each increment (identity: the 6 changed cases of `pre_e_identity_cases.py`, DI-16 repro; multiplicity: M1 to M12 and the `move()` case) |
| S-3: re-freeze the 106,752-answer and 398-view baselines, 0 unexplained differences | open | after both increments |
| S-4: every register issue has a recommendation and owner decision | open | DI-12, DI-13, DI-15, DI-16 await the decisions requested below |
| T-1: full suite x 4 configurations, twice (8 of 8) | open | on the entry commit (today: once, 4 of 4, on `bf60c1f`) |
| T-2: reference database rebuilt, 106,752 identical | open | on the entry commit, after S-3 |
| T-3: result-order tests | passing on `bf60c1f` | re-check on the entry commit |
| P-1: Core 0.3 workload baseline, thresholds judged | **partly met**: baseline done twice; full load and size met; three thresholds not demonstrable | repeat on the entry commit on a quiet machine or with pinned CPUs; the tail (section 4.3) to be explained or bounded |
| P-2: Core 0.4 benchmarks re-run | open | on the entry commit, three alternating rounds |
| P-3: agreed budgets (e.g. `occurrence()` at most 100 queries per view, no report above 500) | **open: an owner decision** | to be agreed before Stage E starts |
| R-1 to R-4: frozen evaluation set | open | to be written and frozen before Stage E's implementation |

## 6. Proposed implementation order and review gates
Each step is its own branch from `main`, reviewed and merged only on approval; nothing starts before the decisions
below.

1. **Identity increment** (DI-12, DI-15, DI-16 option (a)): ID-1 to ID-9, with the ID-5 wording of section 1.3;
   permanent tests from the identity cases and the DI-16 reproduction; full suite x 4; 398-view and 106,752-answer
   comparisons with every difference attributed. **Gate 1.**
2. **ID-10**, if approved, as a separate small step after gate 1 (0 of 433 reference accounts change). **Gate 1a**
   (can be combined with gate 2 if the owner prefers).
3. **Multiplicity increment** (DI-13): MP-1 as amended (section 3.2), MP-2 to MP-5, the MP-4 output fields, and the
   `move()` origin fix with its test; upgrade path tested on the reference databases. **Gate 2.**
4. **Entry checks on the resulting `main`:** re-freeze the baselines (S-3), T-1 (8 of 8), T-2, T-3, P-1 repeated
   under quiet or pinned conditions, P-2; the owner agrees the P-3 budgets; the R-1 evaluation set written and
   frozen. **Gate 3: Stage E entry report**, which states each criterion met, missed or not demonstrable.
5. Stage E begins only on approval at gate 3.

### Decisions requested at this gate
1. Identity: approve ID-1 to ID-9 with the ID-5 wording of section 1.3, or amend; decide ID-10 (recommended: approve as
   a separate last step).
2. DI-16: adopt option (a) (recommended).
3. Multiplicity: approve MP-1 as amended (no `instrument`; `destination` and `product` deferred), MP-2 to MP-5 and the
   MP-4 output fields; include the `move()` origin fix in that increment.
4. Performance: accept the controlled repeat; decide whether P-1 is to be repeated at gate 3 on a fully quiet machine
   or with pinned CPUs, and agree the P-3 budgets.
5. Approve the implementation order above.
