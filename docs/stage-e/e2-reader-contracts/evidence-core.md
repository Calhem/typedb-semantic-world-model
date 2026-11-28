<!-- Evidence record for Part A of benchmark/e2/spec/reader-contracts.md (LABS-1.062): the specification evidence gathered before drafting, with full citations. Supplementary to the contracts. -->

# Reader contract evidence: `holds`, `value_at`, `facts_about`, `occurrence`, `occurrence_status`, `office_holders`

Repository: `typedb-semantic-world-model`, read on branch `feature/e2-harness` (head `e64c83f`; `main` `612bc6e`, which
includes the DI-19 merge `7769ba1`). This was a read-only pass: nothing was changed, no tests ran, TypeDB was not
called.

**Markers.** [ESTABLISHED] means approved design text or a recorded approved decision. [INFERRED] means my reading, or
something that only a docstring or the implementation states. Design documents are authoritative. Code is cited only
to find discrepancies.

**Source abbreviations** (paths relative to the repository root; `L` gives line numbers):

| Tag | File |
|---|---|
| v0.2 | `docs/architecture/world-ontology-v0.2.md` (frozen baseline) |
| C03 | `docs/core-0.3/README.md` (Core 0.3, approved; deviations D1 to D14) |
| SUP | `docs/core-0.3/supersession-and-endings.md` |
| A0 | `docs/core-0.4/README.md` (Stage A0: A0.1 to A0.3, F-4, F-5; approved LABS-1.003 to 1.006) |
| A2 | `docs/core-0.4/stage-a2.md` (D-A2-1 to D-A2-7) |
| SB | `docs/core-0.4/stage-b.md` (decision register, LABS-1.011, LABS-1.012) |
| D2D / D2 | `docs/core-0.4/stage-d2-design.md` / `stage-d2.md` |
| B-D / B | `docs/core-0.4/pre-e-increment-b-design.md` / `pre-e-increment-b.md` |
| C-D / C | `docs/core-0.4/pre-e-increment-c-design.md` / `pre-e-increment-c.md` |
| D-D / D | `docs/core-0.4/pre-e-increment-d-design.md` / `pre-e-increment-d.md` |
| ID-D / ID | `docs/core-0.4/pre-e-identity-design.md` / `pre-e-identity-increment.md` |
| GATE | `docs/core-0.4/pre-e-decision-gate.md` |
| MP-D / MP | `docs/core-0.4/pre-e-multiplicity-design.md` / `pre-e-multiplicity-increment.md` |
| REG | `docs/core-0.4/deferred-issues.md` |
| R | `docs/stage-e/e1-reconciliation-design.md` (R1 to R4, approved LABS-1.053) |
| DI19 | `docs/stage-e/stage-e-di19-constraint-support.md` |
| E2DEC / HR | `docs/stage-e/stage-e2-decisions.md` / `stage-e2-harness-review.md` |
| T / CL | `benchmark/e1/TEMPLATES.md` / `benchmark/e1/CLARIFICATIONS.md` |
| code | `src/worldmodel/model.py`, `judgement.py`, `semantics.py`, `dynamics.py`, `organisation.py`, `agency.py` |

---

## 0. Shared semantics (they apply to every reader below)

### 0.1 Context and visibility
- Every answer is computed for a context ⟨world w, perspective p, knowledge time τ (`as_of`), valid time t⟩ and is never
  stored. [ESTABLISHED] v0.2 §5.1 (query answer), §5.2 E9, §6.1; B-D §2.1 (`context = (world, t, as_of, perspective)`;
  records are comparable only when their contexts are equal).
- **Usable attestations in ⟨w, p, τ⟩:** (1) w's own attestations recorded by τ that p made or accepted by τ (the latest
  decision wins; a rejection wins ties: E4), plus every stipulation of w (constitutive, E7); (2) for a variant with
  branch β and knowledge limit κ, the attestations usable in ⟨base, p, min(τ, κ)⟩, restricted to starts before β (their
  endings counted only before β); (3) nested variants apply this recursively, with the tightest β and κ.
  [ESTABLISHED] v0.2 §6.2; §5.2 E4, E7.
- **Acceptance is world-independent.** A variant changes inherited content only by stipulating (including stipulated
  denials), never by "rejecting" the base's attestation. Each perspective inherits its own view of the base. Later base
  corrections after κ never reach the variant. [ESTABLISHED] v0.2 §5.3, §6.3.
- **Unaccepted attestations by others are alternatives, never support.** [ESTABLISHED] v0.2 §6.2 (L515).
- **Supersession is per perspective.** An attestation is superseded for p only when a supersession is recorded by τ
  **and** p's view includes the replacement. Otherwise p keeps the original, and the answer lists
  `superseded_by_source` in its evidence. [ESTABLISHED] SUP §2; C03 D14.
- **World precedence.** Within one content, the nearest world's deciding attestations win. For a functional type, a
  value holding in a nearer world overrides inherited values for the same key. [ESTABLISHED] B-D §2.1 (L43-46); A0
  "What uses them" (L57-60).
- **Identity** (same-as) is per perspective and knowledge time (ID-7) and timeless in valid time (ID-3). Two names are
  one thing only where their link is ESTABLISHED (ID-2). Classes are connected components (ID-4). A component that
  contains a pair whose own link is DISPUTED or NOT_HOLDING is not merged at all, and the conflict is reported (ID-5, in
  the GATE §1.3 wording). The nearest world decides each link (ID-6). Every reader uses this identity and selects
  contents by the subject's whole class (ID-8). [ESTABLISHED] ID-D §9; GATE §1.1 to 1.3; ID §3 and "After the merge";
  REG DI-16. "Temporal context" of identity means knowledge time. [ESTABLISHED] ID §2 and "After the merge"; REG DI-16.

### 0.2 The canonical per-content record (increment B)
- One record per content per context: content key, every attestation (kept separately, with its acceptance state,
  interval, world and depth), applicable constraints, judgement plus reasons, `status` and `support_status`.
  Nothing else judges content, names a judgement, or applies a constraint. [ESTABLISHED] B-D §2 (L29-35), §2.2 to
  §2.4; B "What changed".
- **Judgement vocabulary:** `established`, `disputed` (reasons `polarity`, `constraint` or both), `not holding`
  (`denied`, `ended`), `pending`, `unknown` (`not_yet_effective`, `end_unknown`, `unaccepted`, `no_evidence`).
  [ESTABLISHED] B-D §2.4 table (L79-92); T L8-16.
  - **Refinements recorded as "points decided in implementation"** in the approved and merged report: PENDING means
    "no accepted claim bears on the content, and an unreviewed claim exists"; "not yet effective" comes only from an
    accepted assertion (an accepted denial that begins after t gives reason `silent`); NOT_HOLDING also has the
    reasons `excluded` and `overridden` (INFERRED). [ESTABLISHED] B L83-93 (approved and merged LABS-1.039).
  - **Functional exclusivity addendum:** a content whose single-valued slot holds another **established** value at t
    is `not holding`, and `holds` answers false with status INFERRED, citing the established value's attestations.
    This is decided before `pending`. A disputed slot decides nothing. [ESTABLISHED] B-D §2.4 addendum (L117-124);
    R R3; CL C5; v0.2 §4.4 (L370); A0 F-4 "Unchanged" (a third value while the slot is disputed stays UNKNOWN).
  - Reason `not_supporting` (an accepted doubt or hypothesis that never decides) appears only in `judgement.py`
    `undecided()`. [INFERRED]
- **Status vocabulary:** ASSERTED, STIPULATED, INFERRED, DISPUTED, UNKNOWN, NOT_YET_KNOWN. OBSERVED and PRESUMED are
  not produced: observations are labelled ASSERTED with `basis: observation` (C03 D1). Mixed support is labelled by
  the core rule STIPULATED > ASSERTED > INFERRED (C03 D4; B-D §2.4 "support_status"). [ESTABLISHED] v0.2 §5.6
  (L468-489), as amended by C03 D1/D4; T L17-19.
  - UNKNOWN: records about the content are visible at τ, but none decides t. NOT_YET_KNOWN: nothing about the content
    is visible at τ. [ESTABLISHED] v0.2 §5.6.
  - DISPUTED: "answers of equal standing for p disagree at t". Detection uses: (1) polarity conflict on equivalent
    contents; (2) functional conflict (incompatible values for a single-valued slot: two places, disjoint ranges, two
    players of a single-valued event role); (3) presumption against presumption (not implemented, C03 D1).
    Resolution happens only through acceptance or a named resolution policy, and is "never silent". [ESTABLISHED]
    v0.2 §5.3 (L436-447).
- **Declared vs attested constraints:**
  - **Declared constraints** (functional slots, stored as data, A0.3) apply unconditionally, in every world and at
    every time. Installed: `located-at` (located → place), `anchored-to`, `positioned-in`, `frame-transform`.
  - **Attested constraints** (e.g. `exclusive-office(office, context)`) apply only where their own canonical
    judgement, in the same context, is ESTABLISHED. They are judged by the same mechanism, without attested
    constraints of their own, so evaluation never recurses.
  - A rival counts only if it holds at the polarity layer. Equal values never conflict, co-referring values are one
    value, and parameter values conflict only when they cannot both be true.
  - [ESTABLISHED] B-D §2.3 (L62-77); B L95-100 (point 5); A0 L18 and "Functional constraints: semantics"; A2 D-A2-1.
- **Inheritance of declared constraints is additive** (a subtype inherits all of them and can only add). A constraint
  declared on a subtype applies to that subtype's content only. [ESTABLISHED] A0 L45-56 (U-5, LABS-1.003).
- **Derivations:** INFERRED is reserved (v0.2 E6) for attestations derived under a named rule from named premises, or
  for a declared query-time rule (functional exclusivity, frame transform, a named reconciliation policy). The model
  records no derivation, so any attestation with basis `inference` is reported INFERRED (DI-7, open; deferred until
  after E2). By convention, people and organisations use testimony or a hypothesis, never `inference` (D-D3-4,
  documented, not enforced outside the laboratory writer). E2 requires "no fabricated derivations". [ESTABLISHED]
  v0.2 §5.2 E6, §5.6 INFERRED row; C03 D8; REG DI-7 (L219-249); `docs/core-0.4/stage-d3-design.md` D-D3-4; E2DEC §1
  and §4.
- **Role names:** readers take the type's **core role names** (a profile role is stored under the core role it
  specialises; a profile's own new role keeps its name). Any other name is refused with `UnknownRoleError`
  (a `ValueError`) naming the type, the unknown names, the valid names and, for a stored profile name, the core name.
  Nothing is answered. [ESTABLISHED] R R2 (L50-80); CL C4; A0 "Writing and asking with profile types" (L38-42).
- **Questions by a type include its subtypes.** [ESTABLISHED] A0 table, A0.2 (L17).

---

## 1. `holds(world, type, roles, t, as_of=None, perspective=SYSTEM)` → `Answer`

### 1.1 Supported question classes and input conditions
- "Does this content hold at t for p?" for one proposition content: type plus role bindings. [ESTABLISHED] B-D §3
  (L144-159: `holds` is a projection of the record of one content); C03 README example (L27-31).
- Role names must be core role names of `type`, inherited roles included; otherwise `UnknownRoleError` (§1.8).
  [ESTABLISHED] R R2.
- **Parameters are not part of `holds`' question.** `where` and `poses` are the position interface. [ESTABLISHED,
  provisionally accepted] A2 D-A2-5 (L232), "Model" limitation (L247).
- The `type` may be a supertype: subtypes are included. [ESTABLISHED] A0 A0.2.
- Partial role bindings are accepted: the docstring of `judgement()` says "with the given players among its own", and
  the code (`model.py` `_question.matches`, `want[r] <= ...`) treats the given roles as a subset filter. No design text
  defines `holds` over partially specified content. [INFERRED] (see Discrepancies H-1, H-2).
- `same-as` questions are judged by the stated names, never through identity (ID-1), and timelessly (ID-3).
  [ESTABLISHED] ID-D §3.1, §3.3; ID §3 and §8 items 3 and 4.

### 1.2 Output fields and vocabulary
`Answer(status, holds, values=(), support, alternatives, evidence, conflicts, constraint_support)`.
- `status` ∈ {ASSERTED, STIPULATED, INFERRED, DISPUTED, UNKNOWN, NOT_YET_KNOWN}; `holds` ∈ {True, False, None}.
  [ESTABLISHED] C03 table (L57); v0.2 §5.6.
- A content that holds but conflicts under a constraint: `Answer(DISPUTED, holds=None, support=<its own
  attestations>, conflicts=<the conflicting attestations>, evidence=<both>)`. [ESTABLISHED] A0 F-4 correction
  (L102-107).
- A polarity dispute: DISPUTED, `holds` None, and the deciding accepted assertions and denials are both cited.
  [ESTABLISHED] C03 example (L30: "DISPUTED, with both as evidence"); v0.2 §5.3.
- `constraint_support` has one entry per **applied attested** constraint: `constraint`, `key`, `value_role`, `support`
  (the constraint's own deciding attestation ids, sorted) and `evidence`. Entries are sorted by constraint and key.
  It is empty for declared slots ("no attestation evidence is fabricated"). The field is additive. [ESTABLISHED] DI19
  §1 (L13-46); E2DEC §1 row DI-19 ("the holds() reader contract includes constraint_support").
- **The canonical judgement word is not a field of `Answer`.** It comes from `judgement()`. E1's `holds` template
  scores `judgement` from `judgement()` and `status` from `holds()`. [ESTABLISHED] T L26; B-D §3 (`judgement` returns
  the record). Projection rules, taken from code (`_answer`, `holds`) [INFERRED]:
  - ESTABLISHED → (support status, True);
  - NOT_HOLDING by denial or end → (support status, False);
  - EXCLUDED or OVERRIDDEN → (INFERRED, False);
  - PENDING and UNKNOWN records both → (UNKNOWN, None), or NOT_YET_KNOWN when no matching attestation is visible.
  - So PENDING is not distinguishable from UNKNOWN through `holds()` alone.

### 1.3 Judgement and uncertainty semantics
- `holds` is a projection of the canonical record, with output identical to before increment B (except where an
  attested constraint now applies). [ESTABLISHED] B-D §3 (L159), §5; B "Readers" and "Answer changes" (the 44 office
  exclusivity answers).
- Rule Q (increment C) is **not** applied to `holds`. `holds` answers one content, and is the reference for rule Q.
  [ESTABLISHED] C-D §4 inventory (L116: "`holds`, `judgement`, `explain` | one content | the canonical record |
  reference").
- Status for an established content: the core rule (`answer_status`) over its deciding attestations: STIPULATED if any
  is a stipulation, else ASSERTED if any is testimony or observation, else INFERRED. [ESTABLISHED] C-D §1 (L20-22);
  C03 D4.
- **How DISPUTED arises:**
  1. polarity: an accepted assertion and an accepted denial at the nearest deciding world depth;
  2. a declared-slot conflict: another holding content gives a different value for the same key;
  3. an attested-constraint conflict: the constraint is ESTABLISHED in the same context, and several holders share
     its key.

  [ESTABLISHED] B-D §2.4 (L84); v0.2 §5.3; A0 F-4; B L40-42 and L93-95 (office exclusivity in `holds`).
- An attested constraint that is pending, unknown, denied or disputed "is reported but never disputes holdings that
  are otherwise compatible". [ESTABLISHED] B-D §2.3 (L70-72); DI19 §1 (disputed or unaccepted constraints are not
  cited); B "Tests" (not applied before the constraint starts or is known, by a perspective that has not accepted it,
  or while it is disputed).
- **Exclusivity (inferred false).** If the slot holds another established value, the content does not hold:
  INFERRED false, citing that value's attestations, decided before PENDING. [ESTABLISHED] B-D §2.4 addendum; R R3;
  v0.2 §4.4. This uses declared slots only: an attested office constraint never infers that an unmentioned person is
  not the holder ("Core holds() on an unmentioned person therefore answers NOT_YET_KNOWN, not INFERRED false").
  [ESTABLISHED] D2 §1 (L22-29).
- Corroboration: the answer holds if any accepted positive attestation certainly holds at t. All of them are cited,
  never combined into a probability. [ESTABLISHED] v0.2 §5.3 (L429-430).
- An ended interval implies "does not hold" only until a later attestation of the same content starts. Ended accounts
  still dispute accounts that began before the end. [ESTABLISHED] C03 D5.
- Unknown end: nothing is assumed to continue (`end_unknown` → UNKNOWN). [ESTABLISHED] B-D §2.4 (choice C).

### 1.4 Temporal, perspective and world visibility
- As in §0.1, and the same for every reader. [ESTABLISHED] B "What changed" (L22-23).
- Knowledge time: only attestations, acceptances and supersessions recorded by `as_of` count. [ESTABLISHED] B-D §2.1.
- An attested constraint is cited only where the perspective accepts it, and only within its valid time and knowledge
  time. A superseded constraint cites its successor. Constraints are inherited in variant worlds. [ESTABLISHED] DI19
  §2 tests table (approved and merged; `main` `7769ba1`).
- Identity: players are compared under p's identity (ID-2 to ID-8). The identity links relied on are **not** added to
  the answer's evidence; they are listed by `identity()`. [ESTABLISHED] ID-D §3.10 (L144-149).
- Selective and full load must give identical answers. [ESTABLISHED] B-D §3 (L145); C03 "Regression results".

### 1.5 Ordering and multiplicity
- `support` ids are sorted, `conflicts` are ids, `evidence` is sorted by attestation id (code). `constraint_support`
  is sorted by constraint and key [ESTABLISHED] DI19 §1. Every other sort order is [INFERRED] from code.
- One answer per question. With partial roles, several contents may match. The code returns the first decided record
  in `_records` order and does not report the others. [INFERRED] (Discrepancy H-2).

### 1.6 Supporting, conflicting and alternative evidence
| Field | What it is | Rests on? |
|---|---|---|
| `support` | the content's own deciding attestations. For a polarity dispute: both the accepted assertions and the accepted denials. For not holding: the deciding denials or the ended assertion. For INFERRED false: the established other value's attestations | **rests on** [ESTABLISHED] A0 F-4; R R3; C-D §2 ("deciding support") |
| `conflicts` | the deciding attestations of rival contents under an applied constraint | **rests on.** A dispute is constituted by both sides: "DISPUTED, citing every holder and attestation" (D2D §3); "the rival contents ... by id and support" (B-D §2.3); "the conflict cites `exclusive-office` and the attestations of both Bea and Cal" (D2 §3) [ESTABLISHED] |
| `constraint_support` | the attestations deciding an applied attested constraint | **rests on**: the constraint is what makes the rivals conflict ("which rule caused the dispute", REG DI-19 L556; DI19 §1). It is empty for declared slots (schema data) [ESTABLISHED] |
| `alternatives` | unreviewed, not superseded attestations of the matching content(s) with a verdict at t | **reported, never rested on.** "never as support" (v0.2 §6.2); `pending` "never decide, and never outrank an accepted attestation" (B-D §2.2) [ESTABLISHED] |
| `evidence` | dicts for `support` (and the rivals, for a constraint dispute) | descriptive detail of the above [ESTABLISHED] A0 F-4 |

**Assessment of the E1 harness (support ∪ conflicts ∪ constraint_support as cited).** This is consistent with the
design. Each of the three sets is part of what a DISPUTED answer rests on, and outside a dispute two of them are empty:
- `conflicts` is non-empty only under a constraint dispute (A0 F-4).
- `constraint_support` is non-empty only for an applied attested constraint. A constraint is evaluated only where two
  or more values are held (B L95-100), so in practice it is non-empty only on a constraint dispute. DI19 §3 found 4
  non-empty entries in the reference answers, all `holds()` DISPUTED.

Excluding `alternatives` is also right (v0.2 §6.2).

Caveats [INFERRED]:
1. The INFERRED-false answer's `support` belongs to **another** content (the excluding value). It is admissible for
   that answer (R3: "citing the established value's attestations"), but gold authors must list it as admissible.
2. Polarity-dispute `support` includes denials. This is admissible (v0.2 §5.3 "both"), but it is not "support for
   the content".
3. "Support" in `holds` DISPUTED differs from rule Q readers, where DISPUTED has `support` empty
   (C L74-75; ER-4). The contracts should define "cited" per reader, not as one word.

### 1.7 Derivations and admissible premises
- `holds` presents no derivation. INFERRED comes from (a) basis `inference` (DI-7: not a recorded derivation) or
  (b) query-time functional exclusivity. A contract must not present (a) as a derivation with premises.
  [ESTABLISHED] REG DI-7; C03 D8; E2DEC §1 (derivation questions are gap probes) and §4 ("no fabricated
  derivations").

### 1.8 Documented refusals
- `UnknownRoleError` (ValueError) for role names the type lacks: nothing answered or written. [ESTABLISHED] R R2;
  HR §9 ("established").
- No other refusal is documented in design. A same-as **write** with an interval is refused (ID-3). That is a writer
  rule, not a `holds` refusal. [ESTABLISHED] ID-D §3.3; ID §3.

### 1.9 Known limitations and DIs
- DI-7: INFERRED from basis inference (open, deferred until after E2). DI-17: ID-5 conflict groups may be
  over-restrictive (evaluation only; about 12 E2 questions). TI-1: chains no one asserted. TI-2: contradictions that
  are not denials surface as property disputes. TI-3: legacy same-as intervals are ignored. [ESTABLISHED] REG DI-7,
  DI-17; ID §10; GATE §1.4; E2DEC §1 and §2.
- D-A2-5: `holds` cannot single out one position or parameter set. C03 D1: no OBSERVED or PRESUMED, and no persistence
  policies (v0.2 §5.4 is not implemented). [ESTABLISHED]
- Performance: DI-9's office exclusivity cost (5 to 38 extra queries); DI-20 to DI-23 residuals. [ESTABLISHED] REG
  DI-9, DI-20 to DI-23.
- Gap probes for derivations: GAP-MULTI-6, GAP-CAUSE-7, GAP-MEAS-11. [ESTABLISHED] E2DEC §1.

---

## 2. `value_at(world, type, subject, t, as_of=None, perspective=SYSTEM, key_role=None, value_role=None)` → `Answer`
(with `value_of(world, type, key, t, ...)`, its composite-key form)

### 2.1 Supported question classes and input conditions
- "What value(s) does `subject` have in a functional slot at t?" Without `key_role`, the type must have **exactly one
  one-role functional constraint**; otherwise the question must name the roles, and composite keys use `value_of`.
  [ESTABLISHED] A0 "What uses them" (L58-60: "`value_at` without `key_role` needs exactly one one-role constraint;
  otherwise the question must say which"); DI19 §1 ("They refuse a type with no declared slot, such as
  `office-holding`") and its test `test_value_readers_never_apply_attested_constraints`.
- With explicit `key_role`/`value_role`, `value_at` answers inverse or non-functional questions too, e.g. "what is on
  shelf 3?" (`key_role="place", value_role="located"`), where several compatible values are ASSERTED, not disputed.
  [ESTABLISHED] A0 "The shelf dispute" table (L62-70: two objects on one shelf: compatible, both ASSERTED).
- `value_of(key)`: `key` names a player for every key role of one constraint (A0.3, e.g. `seat-assignment`).
  [ESTABLISHED] A0 L29 and A0.3 row.
- Role names (`key_role`, `value_role`, `value_of`'s key) are checked as in `holds` (UnknownRoleError). [ESTABLISHED]
  R R2 (L62-63).
- E1 template: `value_at` with `type` and `subject` (a functional slot, e.g. `located-at`); scored fields `status` and
  `values`. [ESTABLISHED as benchmark spec] T L27.

### 2.2 Output fields and vocabulary
- `Answer(status, values, support, alternatives, evidence)`. `holds` is None, and `conflicts` and
  `constraint_support` are always empty. [ESTABLISHED for constraint_support] DI19 §1 ("their `constraint_support` is
  always `()`"). [INFERRED from code for `conflicts`] (§2.6).
- `values`: canonical ids under p's identity ("co-referring values are one value"). [ESTABLISHED] B-D §2.3; A0 F-5
  (L118-136). Which name is canonical (the least name of the class) is [INFERRED] from code.
- Status: ASSERTED, STIPULATED or INFERRED (the core rule over the support of the **values held**), DISPUTED, UNKNOWN
  (values empty, but records visible) or NOT_YET_KNOWN. [ESTABLISHED] C-D §4 (L117: "`value_of` | core rule over the
  values held | reference"), §3.3; C03 table.

### 2.3 Judgement and uncertainty semantics
- One functional-conflict judgement is shared by `value_at`, `holds`, `facts_about` and `changes` (Q-B2, LABS-1.015).
  The answer is DISPUTED for a functional reason only when two holding contents give different value players to the
  same constraint key (players canonical under identity). Parameter values conflict when they cannot both be true
  (D-A2-1). [ESTABLISHED] SB register Q-B2 (L21); A0 shelf root cause (L72-77); A2 D-A2-1.
- A polarity-disputed value makes the answer DISPUTED. [ESTABLISHED] D2D §3 "Judgement: polarity" (`holds` and
  `value_of` say DISPUTED); REG DI-1 "Not affected" list.
- **Only declared slots apply.** `value_at`/`value_of` never apply an attested constraint. [ESTABLISHED] DI19 §1
  (L37-39).
- Rule Q for a slot's value: the status rests on the values held (or disputed) at t. An accepted denial of another
  value is not support. [ESTABLISHED] C-D §3.3 (C-6); C L36-37 and Limitations.
- An unreviewed attestation never creates a dispute. [ESTABLISHED] A0 F-4 "Unchanged" ("Unreviewed rival claims do not
  create a dispute until the perspective accepts them"); C03 example L27.
- Accepted denials only (no value held): values empty → UNKNOWN. This is consistent with v0.2 §5.5 ("absence of x
  from a place says nothing about where x is") by analogy. [INFERRED]

### 2.4 Temporal, perspective and world visibility
- As in §0.1. A nearer world's value overrides inherited values for the same slot key. [ESTABLISHED] A0 L57-58; B-D
  §2.1.
- Identity of value players: full and selective load must agree (F-5 correction). [ESTABLISHED] A0 F-5.
- The ID-8 class selection applies ("the judgement path (`holds`, `value_at`, `facts_about`, `judgement`):
  unchanged in shape, new identity"). [ESTABLISHED] ID-D §3.8.

### 2.5 Ordering and multiplicity
- Several values are possible: compatible values with explicit roles, or every value in a dispute. `values` is sorted;
  `support` and `alternatives` are sorted ids; `evidence` is sorted by id. [INFERRED from code] The values-as-tuple
  shape is in C03 (Answer).

### 2.6 Supporting, conflicting and alternative evidence
- `support`: the deciding attestations of every content that **holds or is polarity-disputed** in the slot (code
  `_value`: `support = holding ∪ disputed`). In a dispute this covers **both sides** (every value's attestations,
  including accepted denials of a polarity-disputed value). There is no separate `conflicts` field. [INFERRED from code]
  The design says only that `value_at` "reports DISPUTED" (A0 F-4), with "evidence for both sides" available. E1
  required evidence for `value_at` is "the deciding attestations" (T L47-48).
- `alternatives`: unreviewed, not superseded attestations of keyed content with a verdict at t. Reported, never
  support. [ESTABLISHED] v0.2 §6.2; C03 L27.
- `constraint_support`: always empty. [ESTABLISHED] DI19 §1.

**Assessment of E1 counting only `support` for `value_at`.** This is consistent with the implementation and does not
contradict the design. Because `value_at` puts every side of a dispute into `support`, and has no `conflicts` and no
attested constraints, `support` is the whole of what the answer rests on. Caveats:
- If a contract wants `value_at` to mirror `holds` (own support vs rivals), that is a design change: no design text
  splits them for `value_at`.
- Rejected and unaccepted claims are excluded from `support` (usable only), so forbidden-evidence checks are sound.

### 2.7 Derivations
- None presented. INFERRED status arises only from basis `inference` (DI-7). [ESTABLISHED] REG DI-7 ("Affected:
  `holds`, `value_of`...").

### 2.8 Documented refusals
| Refusal | Where established | Note |
|---|---|---|
| `UnknownRoleError` for an unknown `key_role`/`value_role`/key role | R R2 [ESTABLISHED] | HR §9 marks it established |
| `ValueError` when `key_role` is omitted and the type does not have exactly one one-role constraint | A0 L58-60; DI19 §1 and §2 test [ESTABLISHED] | **HR §9 marks this "not established; documented only in the implementation". That conflicts with A0 and DI19** (Discrepancy V-1) |
| `value_of`: `ValueError` when `key` does not name exactly the key roles of one functional constraint | DI19 §1 test (`value_of(w, "office-holding", {...})` raises) [ESTABLISHED by test in an approved increment]; message only in code | |
| `value_of`: `ValueError` when the constraint's value is the content's parameters ("ask with where/poses") | consistent with A2 D-A2-5 ("`where` is the position-specific query interface") [INFERRED: the refusal itself is only in code] | |

### 2.9 Known limitations and DIs
- DI-3: no joint-kind slot (two joint kinds never conflict). DI-7. DI-17. D-A1-2 (`docs/core-0.4/stage-a1.md` L104):
  positions were not slot-judged in A1, superseded by A2's `@params` slots. A2: range propagation is conservative
  (a conflict can be missed, never invented). [ESTABLISHED] REG DI-3; A2 limitations (L239).
- No attested constraints in value readers. An exclusive office is visible only through `holds`, `facts_about` and
  `office_holders`. [ESTABLISHED] DI19 §1.

---

## 3. `facts_about(world, subject, t, as_of=None, perspective=SYSTEM)` → list of entries

### 3.1 Supported question classes and input conditions
- "Every content involving `subject` that holds or is disputed at t." Covers all non-event, non-identity types.
  [ESTABLISHED] B-D §3 (`judgements_about`: "all non-event, non-identity types by default", L150); B-D §4 (L166-168);
  REG DI-1 correction.
- Selection by the subject's whole identity class (ID-8). [ESTABLISHED] ID-D §3.8.

### 3.2 Output fields and vocabulary
- Each entry: `type`, `roles`, `params`, `support`, `status`, `conflicts`, `support_status`, plus `judgement`,
  `assertions`, `denials` (added in increment B; "fields are only added, never removed or renamed"). [ESTABLISHED]
  B-D §4 (L166-168); B "Readers" (L31-33).
- `judgement` ∈ {established, disputed} only. Not-holding, pending and unknown contents are never listed ("a listing
  never shows" undecided or excluded records). [ESTABLISHED] B L89-91 (point 3: "No listing shows these"); B "Cost"
  item 2 ("a listing builds no undecided records").
- `status`: DISPUTED for a dispute, otherwise `support_status`. `support_status` is the core rule before constraints
  (DISPUTED for a polarity dispute). [ESTABLISHED] B-D §2.4 (L94-97).

### 3.3 Judgement and uncertainty semantics
- Polarity-disputed content is listed in place, marked DISPUTED, citing the assertions, the denials and any
  constraint rivals (DI-1). [ESTABLISHED] B-D §4; REG DI-1 (option (a), "never silent", v0.2 §5.3).
- Functional (declared) and attested-constraint conflicts are applied (Q-B2; DI-11; office exclusivity: B "Answer
  changes" row DI-11 lists `facts_about`). [ESTABLISHED]
- A dispute is listed only while it is one (another perspective, an earlier knowledge time). [ESTABLISHED] B "Tests".

### 3.4 Temporal, perspective and world visibility
- As in §0.1. A value overridden by a nearer world is not listed (NOT_HOLDING `overridden`). [ESTABLISHED] B L89-91.

### 3.5 Ordering and multiplicity
- One entry per content (content class under identity). Sorted "as today" (B-D §3). The code sorts by
  `(type, str(roles))` [INFERRED].

### 3.6 Supporting, conflicting and alternative evidence
- `support`: the deciding attestations (both sides for a polarity dispute, split into `assertions`/`denials`).
  `conflicts`: the rival contents' attestations under a declared or attested constraint, "including rivals that do
  not mention the subject". [ESTABLISHED] B-D §4 ("citing the assertions, the denials and any constraint rivals"); the
  "including rivals that do not mention the subject" detail is [INFERRED, docstring].
- No `alternatives`, no `pending`, no `constraint_support` per entry. [INFERRED from code] (Discrepancy F-1: E2HR
  cites each entry's `support` only. An attested-constraint dispute in `facts_about` does not cite the constraint,
  the same gap DI-19 closed for `holds`.)

### 3.7 Derivations
- None presented. [INFERRED]

### 3.8 Refusals
- None documented. [INFERRED]

### 3.9 Limitations and DIs
- DI-9: the office exclusivity cost (`facts_about(cal)` in the plan: 27 → 47 queries). DI-7. DI-17. [ESTABLISHED]
  REG DI-9 addenda; B "After the merge".
- Constraint provenance is not cited per entry (DI-19 covered `holds` only). [INFERRED]

---

## 4. `occurrence(world, occurrence, as_of=None, perspective=SYSTEM)` → dict (merged view)

### 4.1 Supported question classes and input conditions
- "Who took part, and according to whom?" for one occurrence, under p at τ. There is no valid-time parameter: "a
  constrained role is not a state at a time". [ESTABLISHED] D-D §3.6 (L133-136).
- The same view is given for any name of the occurrence's identity class, except the `occurrence` key. [ESTABLISHED]
  ID-D §3.9 (ID-9); REG DI-15.

### 4.2 Output fields and vocabulary
- `descriptions`: the descriptions with a usable describes link (v0.2 §3.2). `participants`: the Core 0.3 core-role
  projection. Both are kept unchanged. [ESTABLISHED] D-D §3.3 (L105-109), ER-5. ID-10 (listing by canonical
  judgement) is **not** implemented. [ESTABLISHED] ID "After the merge"; REG DI-17 "Related deferrals".
- `accounts`: one entry per description linked by a visible describes claim: event type, sources, link judgement
  (claim label), account state in `occurrence_status`'s vocabulary (`accepted`, `unreviewed`, `rejected`, `none`) and
  world depth. Roles are given by stored label. [ESTABLISHED] ER-5; D "After the merge" (`none` accepted).
- `roles` is keyed by **stored role label**: `name`, `core_role`, `players` (each citing its accounts) and
  `constraints` (a list: one per applicable declaration). A constrained role has `event_type`, `role`, `kind`,
  `declared_by`, `applies`, `why`, `classification`, `judgement`, `status`, `support`, `players`, `overridden`, plus
  `multiplicity`, `reason` and `sets` (MP-4). [ESTABLISHED] ER-5; D §9 ("Constraints per stored role"); MP §2 MP-4.
- `resolved` (R1): `judgement` ∈ {established, disputed, union, none}, `players` (empty for disputed and none),
  `compared`, `overridden`, `not_compared` (with why: `account <state>` or `describes <judgement>`), `constraint`,
  `support`. [ESTABLISHED] R R1 table (L19-27).
- `aliases` (the class members) and `identity` (the links used, with world depth and any conflict). [ESTABLISHED]
  ID-D §3.9; ID §3 (ID-9).
- Constrained-role judgement words: `established`, `disputed`, or None (not judged). Dispute reasons: `several players
  in one account`, `accounts name different players` (joined by `; `), `accounts name different sets of players`.
  [ESTABLISHED] ER-4; MP-2; T L33.

### 4.3 Judgement and uncertainty semantics
- **Compared accounts:** describes link ESTABLISHED (canonical record) **and** account accepted; the nearest world
  decides; deeper accounts are `overridden`. [ESTABLISHED] ER-3. The link is judged at the account's start.
  [ESTABLISHED] D §2 "Judgement" (approved and merged).
- **Constraints** are declared only by profiles, on their own event types, named by core role, inherited by subtypes
  (ER-1). They are unconditional, or kind-scoped: a kind-scoped constraint applies only where
  `judgement(classified-as(occurrence, kind))` is ESTABLISHED at the occurrence's start, i.e. the earliest start
  among the accepted accounts with an established link (ER-2). [ESTABLISHED]
- **Rule Q** (ER-4, MP-2):
  - Under `one`: two or more distinct players → DISPUTED, support empty; exactly one → established, status the core
    rule over the union of the deciding account attestations.
  - Under `set`: established when every compared account states the same set; otherwise DISPUTED.
  - Without an applicable constraint: a union, with no judgement and no status (rule C).
  - "Multiplicity alone is never a conflict" (§3.7).
  - [ESTABLISHED] D-D §3.2, §3.7, ER-4; MP-D §3.2, MP-2.
- MP-3: an applicable kind-scoped declaration wins over an unconditional one. Conflicting kind-scoped declarations are
  refused at declaration time. [ESTABLISHED] MP-D MP-3; MP §2.
- A dispute about who took part never decides existence (`exists`, `occurrence_status`). [ESTABLISHED] ER-4; D-D §3.2
  (L93-94); R R1 ("no part of `resolved` says the occurrence happened").
- `union` is not `established`. A player's `status` is the evidence status of the naming accounts, "never a
  judgement". [ESTABLISHED] R R1 (L29-34).
- Declarations carry no valid or knowledge time: once installed, they apply to readings at an earlier `as_of` too.
  [ESTABLISHED] D-D §8.4; D §5.

### 4.4 Temporal, perspective and world visibility
- Perspective decides which links and accounts count, which same-as links hold, and whether a kind is established.
  Knowledge time limits everything. A variant inherits up to its branch point; the plan's own account decides and
  inherited ones are `overridden`. [ESTABLISHED] D-D §3.6 (X1 to X7d4 cases, §6).
- Identity: players are grouped under p's identity, and the occurrence is identified the same way. A same-as merges
  only where ESTABLISHED. [ESTABLISHED] D-D §3.4; ID-2, ID-9; MP-D §5 M8/M9.
- DI-14: in a variant, a description whose link is inherited but whose account is not is listed (account `none`),
  without saying the world holds no account of it. [ESTABLISHED as a known limitation] REG DI-14 (L448-466).

### 4.5 Ordering and multiplicity
- Query-result order and identifiers cannot change a judgement (tested by shuffling). [ESTABLISHED] D-D §9; D §4
  ("Nondeterminism"). Specific list orders (accounts by description id, roles by label, players sorted) are
  [INFERRED from code].
- Several players per account are allowed for `event:actor` and `event:patient`, and the profile roles
  `official-act:official`, `replacement:removed`, `replacement:fitted` and `sampling:sampler`. Other roles stay
  single. [ESTABLISHED] MP §2 (MP-1 as restricted); REG DI-13.

### 4.6 Supporting, conflicting and alternative evidence
- An established constrained role: `support` = the deciding account attestations (rests on). A disputed role:
  `support` empty, and every player is cited with its accounts and sources (reported, not rested on). [ESTABLISHED]
  ER-4. `resolved.support`: the attestation ids the resolved set rests on. [ESTABLISHED] R R1.
- Unaccepted and rejected accounts, and accounts whose link is not established, are "listed with their own judgements
  and never compared": reported, never rested on. [ESTABLISHED] ER-3; D-D §3.5.
- The E2 harness cites nothing from `occurrence` by default (HR §5.1). Design evidence suggests `resolved.support` and
  `constraints[].support` (plus the classification support for kind-scoped constraints) are what the role answer rests
  on. [INFERRED]

### 4.7 Derivations
- None. Membership, kind classification and identity are judged contents, not derivations. [INFERRED]

### 4.8 Refusals
- None documented for the reader. An invalid declaration is refused at installation; installing a profile without
  `core-0.4-event-roles` is refused with an actionable message. [ESTABLISHED] D §2, "After the merge"; MP §2 MP-5.
  These are not reader refusals.

### 4.9 Limitations and DIs
- DI-9: the cost of `occurrence()`. About 19 → 86 queries per view; O-3 scoped the load. DI-14. ID-10 not
  implemented. DI-17. TI-1 `derived` marker not added. Destination and product stay single (a later design).
  [ESTABLISHED] D §8; REG DI-13 closure, DI-14, DI-17.

---

## 5. `occurrence_status(world, occurrence, t, as_of=None, perspective=SYSTEM, details=True)` → dict

### 5.1 Supported question classes and input conditions
- "Did the occurrence happen, for p?", judged **only** from attestations of its own existence (`existence(existent:
  occurrence)`). It never uses descriptions, describes links or causal claims. [ESTABLISHED] SB LABS-1.011 (L345-348);
  Occ-1 (L17); LABS-1.012 "Occurrence existence" (L415).
- Alias names: `occurrence_status` and `exists` take the identity class. [ESTABLISHED] ID-D §3.9; ID §4 ("occurrence_status
  of aliases").

### 5.2 Output fields and vocabulary
- `status` ∈ {`accepted`, `denied`, `disputed`, `not established`}. [ESTABLISHED] SB L345-347, L422; T L34.
- `answer`: the `exists()` Answer, which status is read from (one judgement for both APIs). [ESTABLISHED] SB "One
  existence judgement" (L417-424).
- With `details=True` (the default): the existence attestations, and every description some source links to the
  occurrence, each with its source, the account judgement (`accepted`, `unreviewed`, `rejected`, `none`) and the link
  judgement (claim label). [ESTABLISHED] SB L345-348, L422-424; D "After the merge" (`none`); B-D §6 row
  (`occurrence_status` details: DI-5 labels).

### 5.3 Judgement and uncertainty semantics
- `exists()` for an occurrence: ASSERTED or STIPULATED (true, or false before the existence starts or after it ends)
  or DISPUTED. Without an existence judgement: UNKNOWN when records are visible, otherwise NOT_YET_KNOWN. Never
  INFERRED from participation. Unreviewed existence claims are returned as alternatives. [ESTABLISHED] SB "One
  existence judgement" (L419-421).
- Mapping to `status`:
  - holds True → `accepted`;
  - holds False → `denied`;
  - DISPUTED → `disputed`;
  - otherwise → `not established`.

  The mapping is established in outline ("reads its status from that answer"). Its consequence is that `denied` also
  covers "existence ended before t" and "before creation". No design text says that. [INFERRED] (Discrepancy O-2).
- "An accepted description does not establish the occurrence". "A denied occurrence cannot become accepted through a
  lifted claim". An accepted account of a denied occurrence stays visible. [ESTABLISHED] SB LABS-1.011 table; Occ-2.
- A role dispute never decides existence. [ESTABLISHED] ER-4.
- `occurrence_status(...)["status"]` was preserved through increment B. Only the detail labels changed (DI-5).
  [ESTABLISHED] B-D §5, §6.

### 5.4 Temporal, perspective and world visibility
- Valid time t: existence at t. Perspective, knowledge time and hypothetical worlds work as before; a plan can
  stipulate that an event did not happen ("denied" in the plan, base unchanged). [ESTABLISHED] SB LABS-1.011
  "Hypothetical overrides"; LABS-1.012 "Semantics preserved".

### 5.5 Ordering and multiplicity
- Descriptions are listed separately, sorted by description id (code). [INFERRED]

### 5.6 Evidence
- The answer rests on the existence attestations (`answer.support`). Descriptions and links are reported provenance,
  not support. [ESTABLISHED] SB LABS-1.011 ("never uses descriptions ... for this. It lists every description
  separately"). The E2 harness cites `answer.support` (HR §5.1). That is consistent. [INFERRED assessment]

### 5.7 Derivations
- None. Participation inference is explicitly excluded for occurrences. [ESTABLISHED] SB LABS-1.012.

### 5.8 Refusals
- None documented. [INFERRED] (Discrepancy O-1: a non-occurrence id is not refused.)

### 5.9 Limitations and DIs
- DI-20: still loads a whole world (it grows with perspectives: 52 → 71 ms). DI-14 (descriptions without accounts in
  variants). [ESTABLISHED] REG DI-20, DI-14.

---

## 6. `organisation.office_holders(wm, world, office, context, t, as_of=None, perspective=SYSTEM)` → dict

### 6.1 Supported question classes and input conditions
- "Who holds `office` in `context` at t, for p?" Contexts are matched exactly, with no containment (D-D-4).
  [ESTABLISHED] D2D §2, §3 "Scope of exclusivity"; D2 §6 item 3.
- Requires the organisation profile. Appointments are `office-holding(classified: holder, class: office, context)`.
  [ESTABLISHED] R R2 "Documentation"; CL C4.

### 6.2 Output fields and vocabulary
- `office`, `context`, `holders` (the established appointments), `status`, `exclusive` (the constraint's own
  judgement at t), `conflict` (when the constraint holds and more than one appointment is established: the
  constraint's support and each conflicting appointment's accepted attestations), and `appointments` (every
  appointment content for the office and context, with its own judgement and evidence). [ESTABLISHED] D2 §2 (L37); C-D
  §3.2 ("`holders`, `exclusive`, `conflict` and `appointments` are unchanged"); B-D §5 (choice A: "every field").
- Per-appointment judgement in the holdings vocabulary: `established`, `denied`, `expired`, `not yet effective`,
  `disputed`, `not established`. [ESTABLISHED] B-D §2.4 label table (holdings column); D2 §2 (employment row);
  docstring.
- `status` (rule C): DISPUTED on a conflict or a disputed appointment; **None** when holders are established without
  conflict (one or several); UNKNOWN when appointments exist but none is established; NOT_YET_KNOWN when there are
  none. [ESTABLISHED] C-D §3.2, C-5; C "Readers"; REG DI-6.

### 6.3 Judgement and uncertainty semantics
- Each appointment is judged before the exclusivity constraint (choice A), and the conflict is reported beside it,
  computed by the core's shared attested-constraint mechanism. [ESTABLISHED] B L40-42; B-D §8 Q4.
- Exclusivity is the attested content `exclusive-office(office, context)` over its own valid time. It applies only
  where ESTABLISHED in the same context. No slot is declared, so there is **no inference about unmentioned people**.
  [ESTABLISHED] D2 §1 (L22-29, change from D-D2-2); B-D §2.3.
- An unaccepted claim is never support. Denial differs from absence (an accepted denial is `denied`; unmentioned
  people are simply absent). An appointment event alone establishes nothing. [ESTABLISHED] D2D §3; D2 §3.
- Succession (non-overlapping intervals) is not a conflict. The same office in another unit is independent.
  [ESTABLISHED] D2D §3.
- A polarity-disputed appointment is listed as DISPUTED. [ESTABLISHED] D2 §3 "Disputes are visible"; D-D2-5.

### 6.4 Temporal, perspective and world visibility
- Perspectives (the auditor), knowledge time (before Cal's appointment was recorded: Bea alone) and plans (Dan
  STIPULATED, Cal denied in the plan) are as in the core. [ESTABLISHED] D2D §3; D2 §3.
- Selection by identity class (ID-8: "office holders, appointments" now see aliases' contents). [ESTABLISHED] ID-D
  §3.8; GATE §1.2 ID-8 row.

### 6.5 Ordering and multiplicity
- Several holders are possible (a non-exclusive office, or a dispute). There is no collective support status
  (rule C). `holders` and `appointments` sorted by holder: [INFERRED from code].

### 6.6 Evidence
- Rests on: the established appointments' accepted attestations. In a conflict, also the constraint's support
  (`conflict.constraint.support`). [ESTABLISHED] D2 §3 ("citing the constraint's attestations and each appointment's
  accepted attestations"); REG DI-19 (L553-555: `office_holders` reports the constraint's support).
- Reported, not rested on: unaccepted, rejected and denied appointment claims (each appointment's `evidence` lists
  every claim with its acceptance). Per CL C1 they are explanatory, not required. [ESTABLISHED] CL C1 (X-003); D2 §3.
  The D2D design's "unaccepted claims as alternatives" became per-claim acceptance in `evidence` (Discrepancy OH-1).

### 6.7 Derivations
- None. "No helper infers anything": no authority from an office, no office from an act, no act from authority.
  [ESTABLISHED] D2D §2 (L53-54).

### 6.8 Refusals
- `ValueError` "the organisation profile is not installed" (`_require`). It is in code only, and it applies to every
  organisation reader, including `official_act`. [INFERRED]

### 6.9 Limitations and DIs
- DI-9 office exclusivity cost; DI-22 (`office_holders` grows across worlds: 40 → 55 ms); D-D-4 no containment;
  DI-5 and DI-6 corrected; DI-17. [ESTABLISHED] REG DI-9, DI-22; D2 §6.

---

## Discrepancies (docstring or implementation vs design, gaps not covered by design)

| # | Reader | Design says | Docstring or implementation does | Severity |
|---|---|---|---|---|
| V-1 | `value_at` | A0 L58-60 (approved, merged LABS-1.006): "`value_at` without `key_role` needs exactly one one-role constraint; otherwise the question must say which". DI19 §1 (approved, merged `7769ba1`) and its test say `value_at`/`value_of` refuse `office-holding` | HR §9 (LABS-1.062) classes the `no-single-slot` refusal as "**not established**; documented only in the implementation" | The harness classification should be corrected to established (A0 + DI19); the exact message is still implementation-only |
| V-2 | `value_at` | A0: with explicit roles, value_at answers non-functional questions (shelf) | `key_role` given without `value_role` → `_value(..., value_role=None)` → values always empty → **UNKNOWN even when content holds** (`model.py` `value_at`, `_value`) | Silent wrong-shaped answer, not covered by design. Contract should either require both roles or refuse [INFERRED] |
| V-3 | `value_at` | DI19 §1: value readers "refuse a type with no declared slot, such as office-holding", so they "never apply an attested constraint" | With explicit `key_role="class", value_role="classified"`, `value_at(w, "office-holding", office, t, ...)` is accepted (no check that the roles form a constraint) and returns every holder across all contexts, ASSERTED, **never DISPUTED under an established exclusive office** | Contradicts `holds`/`office_holders` for the same facts; not covered by design [INFERRED from code] |
| V-4 | `value_at`, `value_of` | B-D §3 (L159): "`holds`, `value_at`, `value_of` and `exists` become projections of records into an `Answer`"; DI19 §1: "`_answer` builds the field from the record it projects, so `holds()`, `value_at()` and `value_of()` all go through the same code (`WorldModel._constraint_support`)" | `_value` calls `_judge` + `_conflicts` directly, never `_records`/`_answer`/`_constraint_support`; `constraint_support` is empty only by default (`model.py` `_value`, comment at its head) | Behaviour matches the design's answers (B says `value_at` unchanged), but DI19's description of the code path is inaccurate |
| V-5 | `value_at` | `holds` separates own `support` from rival `conflicts` (A0 F-4) | `value_at` DISPUTED puts **all** sides (incl. polarity denials) in `support`, no `conflicts` field | Not contradicted by design but undocumented; affects evidence-precision gold (admissible set = every value's deciding attestations) [INFERRED] |
| H-1 | `holds` | B-D §3: the record "of one content"; D-A2-5: parameters are not part of `holds`' question | `judgement()` docstring: "`type` or a subtype, with the given players among its own"; `_question.matches` uses subset matching, so partially specified roles are accepted | Goes beyond design (under-specified questions) [INFERRED] |
| H-2 | `holds` | Order and identifiers must not change an answer (C-D §7, D-D §9 for their readers) | With partial roles or parameterised types (has-quality ranges), several contents match; `_question` returns the **first** decided record in `_records` order, others unreported | Possible order dependence; not tested for `holds` per the documents read [INFERRED] |
| H-3 | `holds` | B-D §2.4: PENDING is a distinct judgement | `holds()` maps PENDING and UNKNOWN records alike to `Status.UNKNOWN` (only `judgement()` distinguishes) | Consistent with B-D §5 "holds answers unchanged", but a contract must say PENDING is not observable through `holds` [INFERRED] |
| H-4 | `holds` vs rule Q readers | C L74-75 / ER-4: `support` is empty for DISPUTED (no status rests on it) | `holds` DISPUTED carries non-empty `support` (A0 F-4, established) | Two meanings of `support` across readers; contracts must define it per reader [ESTABLISHED both sides] |
| H-5 | `holds` | No design for reason `not_supporting` | `judgement.undecided()` emits UNKNOWN / `not_supporting` (accepted doubt or hypothesis) | Undesigned reason value [INFERRED] |
| F-1 | `facts_about` | DI-19 (REG L548-556) was about `holds()` not citing the constraint | `facts_about` entries for an attested-constraint dispute carry `conflicts` but no constraint provenance | Same gap as DI-19, unregistered for listings [INFERRED] |
| F-2 | `facts_about` | B-D §4: "citing the assertions, the denials and any constraint rivals" | Docstring adds "including rivals that do not mention the subject (seen from a place, the thing's other places)" | Detail beyond design text, consistent with it [INFERRED] |
| O-1 | `occurrence_status` | SB LABS-1.011: judged "only from attestations of its own existence"; participation never establishes an occurrence | Code reads `exists()`, which only skips participation when the id is an occurrence (`model.py` `exists`); for a non-occurrence id `occurrence_status` can say `accepted` from INFERRED participation; no refusal | Input not validated; not covered by design [INFERRED] |
| O-2 | `occurrence_status` | `status` vocabulary accepted/denied/disputed/not established (SB L345) | `denied` = `exists().holds is False`, which includes "before creation" and "after its existence ended" at t, not only an accepted denial | Design implies it (SB L419-422) but never states that `denied` covers temporal non-existence; contract should make it explicit [INFERRED] |
| O-3 | `occurrence_status` vs `occurrence` | D-D §3.2 step 1: each account gets "the link's canonical judgement ... as `occurrence_status` reports it" | `occurrence_status` judges the describes link at the question's t; `occurrence()` judges it at the account's start (D §2) | Usually identical (links have no start), but two different times for "the same" label [INFERRED] |
| OC-1 | `occurrence` | ER-5 / D-D §3.3: `participants` is the core-role projection "unchanged" | `participants` collects (content, attester) from **every** attestation of each listed description, accepted or not (`model.py` `occurrence`); D-D §7 measured 0 such cases in reference data | Matches "unchanged" Core 0.3 behaviour; contract should direct "who took part" to `resolved` (R R1) [INFERRED] |
| OC-2 | `occurrence` | v0.2 §3.2: descriptions are those with **usable** describes links | `descriptions` lists by usable link while `accounts`/`compared` use the ESTABLISHED canonical record (ID-10 deferred) | Known, registered (GATE §1.5; REG DI-17 related deferrals) [ESTABLISHED] |
| OH-1 | `office_holders` | D2D §2 table: status "(ASSERTED / DISPUTED / INFERRED / UNKNOWN / NOT_YET_KNOWN)", "`value_of` on the slot", "unaccepted claims as alternatives"; D2D §3: a person not accepted is "INFERRED not to hold it" | Superseded by D2 §1 (no slot, no inference about the unmentioned) and C-5 (status None); no `alternatives` field: unaccepted claims appear only inside each appointment's `evidence` with their acceptance | Design history superseded by approved later decisions; contract must cite D2/C-5, not D2D §2-3 [ESTABLISHED] |
| OH-2 | `office_holders` | Not specified | Appointment matching uses `office in e.stated("class")` (stated ids) but `about("context")` (identity class); `holder` is the first attestation's stated name | Asymmetric identity handling; harmless for concept offices [INFERRED] |
| OH-3 | `office_holders` | Not specified | `ValueError` when the profile is not installed (`_require`) | Undocumented refusal [INFERRED] |
| S-1 | all | DI19 doc header and E2DEC §1: "At review; not merged" | `main` contains merge `7769ba1` (DI-19); HR L3 says "DI-19 merged" | Stale status text in DI19 and E2DEC; register entry also says "corrected at review" [ESTABLISHED by git history] |
| S-2 | `holds`, `value_at` | E1 TEMPLATES L47-48: required evidence = "the deciding attestations" | E1 adapter counts support ∪ conflicts ∪ constraint_support for `holds`, support only for `value_at` (HR §5.1) | Consistent with design (see 1.6, 2.6), provided gold treats INFERRED-false `support` (another value's claims) and polarity denials as admissible |
