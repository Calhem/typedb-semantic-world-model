<!-- Evidence record for Part D of benchmark/e2/spec/reader-contracts.md (LABS-1.062): the specification evidence gathered before drafting, with full citations. Supplementary to the contracts. -->

# Specification evidence: causal, change and process readers (E2-D3 input)

Repository: `typedb-semantic-world-model`, read at branch `feature/e2-harness`, head `e64c83f`. Read-only extraction;
nothing was run.

Readers: `causes_of`, `effects_of` (only where it bears on the others), `explain`, `changes`, `process_steps`,
`before`, `interval` (`src/worldmodel/dynamics.py`).

Markers:
- **[ESTABLISHED]**: approved design text or an approved decision.
- **[INFERRED]**: my reading, or a claim supported only by a docstring or the implementation.

Short names for the sources:

| Short name | File |
|---|---|
| SB | `docs/core-0.4/stage-b.md` |
| DO | `docs/core-0.4/dynamics-output.md` (recorded output; an illustration, not a specification) |
| V02 | `docs/architecture/world-ontology-v0.2.md` |
| PLAN | `docs/plans/core-0.4-plan.md` |
| IBD | `docs/core-0.4/pre-e-increment-b-design.md` |
| IB | `docs/core-0.4/pre-e-increment-b.md` |
| ICD | `docs/core-0.4/pre-e-increment-c-design.md` |
| IC | `docs/core-0.4/pre-e-increment-c.md` |
| DI | `docs/core-0.4/deferred-issues.md` |
| E2D | `docs/stage-e/stage-e2-evaluation-design.md` |
| E2DEC | `docs/stage-e/stage-e2-decisions.md` |
| INV | `docs/stage-e/stage-e-entry/e2-capability-inventory.md` (an inventory, partly drawn from code) |
| HR | `docs/stage-e/stage-e2-harness-review.md` |
| R2 | `docs/stage-e/e1-reconciliation-design.md` §R2 |
| DYN | `src/worldmodel/dynamics.py` (supplementary) |
| RD | `benchmark/e2/spec/reader-docs.md` (docstrings; supplementary) |

## 0. Rules shared by every reader

- **Four distinctions kept apart in the data and in every answer** [ESTABLISHED] (SB "B0: architecture review", lines
  174-180; covered by the B-arch approval, SB decision register line 14, LABS-1.011):
  - occurrence vs description;
  - asserted effect vs accepted change;
  - succession vs causation: "`before()` compares intervals (certainly before, or None if they overlap); `causes_of`
    lists only asserted claims; nothing is derived from order or chained";
  - a source's account vs the perspective's judgement: "every claim lists its attestations (attester, polarity, basis,
    acceptance state); the judgement (accepted, disputed, denied, unreviewed, rejected) is computed per perspective,
    knowledge time and world".
- **Causation is asserted, never inferred from succession** [ESTABLISHED] (V02 §3.2, line 188; PLAN Stage B table,
  line 69; PLAN §9.3, lines 277-278: "not from temporal order, not from co-reference alone, not transitively in
  answers").
- **None of these is required** [ESTABLISHED] (V02 §3.2, lines 190-191, and C5, lines 597-601). A state may hold with
  no known initiating event: "What opened it?" is UNKNOWN.
- **Claims are timeless contents** [ESTABLISHED as recorded, not individually ruled] (SB D-B-2, lines 26 and 330).
  Causal and effect claims have no valid interval; they are judged by acceptance, polarity, world and knowledge time.
  V02 §4.4 (lines 357-364) makes all propositions timeless, with time on attestations.
- **Claim vocabulary** [ESTABLISHED] (IBD §2.4, lines 99-112; labelling table approved with increment B, LABS-1.038/1.039):
  accepted, disputed, denied, unreviewed, not yet effective, not established, unknown, and for unaccepted claims
  rejected / retracted / superseded. SB line 180 names only five of these (accepted, disputed, denied, unreviewed,
  rejected); the full set comes from IBD.
- **Answer statuses** [ESTABLISHED] (V02 §5.6, lines 476-487): ASSERTED, STIPULATED, INFERRED, DISPUTED, UNKNOWN,
  NOT_YET_KNOWN (OBSERVED and PRESUMED are defined but never produced: INV line 26 [INFERRED from code]).
- **Context** [ESTABLISHED] (V02 §6.1-6.2, lines 493-515; IBD §2.1, lines 37-46). Every question is asked in
  ⟨world, perspective, knowledge time τ (`as_of`), valid time t⟩:
  - a variant world inherits its base up to `branch-at` / `knowledge-at`;
  - unaccepted attestations by others are alternatives, never support.
- **Occurrence existence** [ESTABLISHED] (SB Occ-1, line 17, LABS-1.012; SB "One existence judgement", lines 417-427).
  An occurrence's existence is judged only from attestations of its own existence. Participation (accepted
  descriptions, describes links, causal claims, process membership) never establishes it.
- **Occ-2** [ESTABLISHED] (SB line 18, LABS-1.011). An accepted account of a denied occurrence stays visible as its
  source's account. Claims involving a denied occurrence do not apply (`applies: false`).
- **Selective and full-load paths agree** [ESTABLISHED] (PLAN §4, line 168; IBD §3, line 145).
- **No optimisation authorised; per-question memo only** [ESTABLISHED] (SB Perf-1, line 19). Loads are per question,
  with no cache across questions. No answer changes because of the memo (SB lines 431-435).
- **Validation for E2** [ESTABLISHED] (E2D §5.2, lines 174-180; E2DEC E2-D3). The contracts come from the design
  documents. Where a docstring differs, the contract records the difference and stops for the owner's decision.

---

## 1. `causes_of(world, effect, t, as_of=None, perspective=SYSTEM)`

### 1.1 Supported question classes and input conditions
- "What caused E, according to the accounts accepted in the world?" (E2D §3.4, C1, line 101) [ESTABLISHED as an H
  question class].
- "A cause is stated against an occurrence whose description is disputed or denied: is that reported with the
  occurrence's own status?" (E2D C2, line 102) [ESTABLISHED].
- **The effect may be an occurrence or an event description** [ESTABLISHED]:
  - `causes` players are event descriptions **and** occurrences (SB "Schema and API", lines 186-188; PLAN line 69;
    PLAN §8 DX-4, line 210);
  - mixed forms (description → occurrence) are allowed (PLAN §9.3, lines 275-276).
- **Keyed on the effect only.** There is no forward "what did X cause?" reader (INV GAP-CAUSE-2, lines 240-243)
  [ESTABLISHED as a gap].
- `t` is a valid time used for judging claims and occurrence statuses [INFERRED: DYN 681, 687]. The claims themselves
  are timeless (D-B-2).

### 1.2 Output fields and permitted vocabulary
- Each claim gives level, judgement and sources [ESTABLISHED]: "every causal claim, direct or lifted, with level,
  judgement and sources" (SB "Schema and API", line 202).
- **Level: description / occurrence / mixed** [ESTABLISHED for description and occurrence]:
  - PLAN §9.3 (lines 269-272) defines description-level and occurrence-level claims;
  - "mixed" is named in PLAN §9.3 (line 275) as the description → occurrence form;
  - the exact label "mixed" is [INFERRED] from the docstring and DYN 696-697.
- **`lifted: true` and `lifted_via`** [ESTABLISHED] (SB U-2, line 16; SB LABS-1.012 table, line 414): `lifted_via` is
  "the accepted describes link".
- **`occurrences`: {occurrence: status}** [ESTABLISHED] (SB LABS-1.011 amendment, lines 349-350). It holds the status
  of each occurrence the claim involves, in occurrence_status's vocabulary: accepted / denied / disputed /
  not established (SB line 345).
- **`applies`: False / None / True** [ESTABLISHED] (SB line 349-350; U-2, line 414):
  - False if any involved occurrence is denied;
  - None (null) if any is disputed;
  - True otherwise.
- **`judgement`** [ESTABLISHED] (SB line 180; IBD §2.4 table): the claim label of the `causes` content in the claims
  vocabulary. A lifted claim keeps its original attestation status (U-2).
- **`status`, `claimed_by`, `attestations`** [ESTABLISHED in substance] (SB line 180: "every claim lists its
  attestations (attester, polarity, basis, acceptance state)"). The field names are [INFERRED] (DYN 710-712).
- **`cause_occurrences`** [INFERRED: docstring "the occurrences its cause is accepted as"; DYN 698, 709]. No design text
  names this field.
- Example of the vocabulary: DO Q6 (lines 54-56) and Q7 (lines 60-63).

### 1.3 Judgement and uncertainty semantics
- **Never inferred** [ESTABLISHED] (PLAN §9.3, lines 277-278; SB line 179). Nothing comes from order, from
  co-reference alone, or transitively. The plan's chain query would list asserted links, not new claims; it is not
  implemented (GAP-CAUSE-1).
- **Lifting** [ESTABLISHED] (PLAN §9.3, lines 273-276; SB "Lifting", lines 207-209; SB U-2):
  - a description-level claim answers an occurrence-level question **only when both descriptions have usable
    `describes` links (for that perspective) to the occurrences asked about**;
  - the answer keeps the description-level claim as its support and **cites the `describes` links**;
  - mixed forms lift the same way.
- **One hop** [ESTABLISHED as verified behaviour] (SB "Scope of causal claims", lines 374-378):
  - a claim about the test-run description lifts to the occurrence;
  - an occurrence-level claim lifts down to a second description of the same occurrence;
  - a claim about a *sibling* description is **not** transferred ("two hops, which the plan does not allow").
- **F-B1** [ESTABLISHED, settled LABS-1.012] (SB line 15 and line 413). Description-level and occurrence-level claims
  are distinct contents and never dispute each other automatically: a denial at one level leaves an accepted claim
  at the other accepted. Illustration: DO Q7, `plan-relubricate-only` (line 63, plus SB line 332).
- **U-2** [ESTABLISHED, settled LABS-1.012] (SB lines 16 and 414):
  - a lifted claim keeps its original status;
  - whether it applies is judged against the occurrences' own existence;
  - a denied occurrence never gets an applicable explanation through a lifted description claim;
  - the claim stays visible as its source's account.
- **A denied occurrence's claims stay visible but do not answer** [ESTABLISHED] (SB "Clarification", lines 361-364).
  They are visible as the source's account with `applies: false`. The same holds for direct occurrence-level claims
  involving a denied occurrence.
- **Disputed occurrence gives `applies: null`** [ESTABLISHED] (SB line 358).
- **Hypothetical override** [ESTABLISHED] (SB line 359). A plan stipulating that the occurrence did not happen gives
  "denied" in the plan, keeps the inherited account "accepted", and marks the claim not applying there. The base
  world is unchanged.
- **Scope of claims** [ESTABLISHED] (SB lines 366-373). A claim names particular occurrences or descriptions, so a
  similar second repair's claims never appear among the first repair's causes, and the reverse.

### 1.4 Temporal, perspective and world visibility
- The judgement is per perspective, knowledge time and world [ESTABLISHED] (SB line 180; SB lines 370-372):
  - unreviewed before its acceptance was recorded, accepted after;
  - one perspective's denial is its own view;
  - a snapshot taken before a later claim does not see it.
- **Lifting needs describes links the perspective accepts** [ESTABLISHED] (SB lines 207-209). Example: the inspector
  accepts no describes link, so it sees no lifted claim (SB line 261; DO Q7, line 61).
- A variant world inherits base claims within its snapshot [ESTABLISHED] (V02 §6.2). DO Q7 line 62 shows the
  pre-denial snapshot.

### 1.5 Ordering and multiplicity
- **Design gives no sort order** [INFERRED: none found in SB, PLAN, E2D].
- DYN 713-714 sorts by judgement rank (accepted, disputed, denied, unreviewed, rejected, retracted; other labels last),
  then cause, then effect [INFERRED]. INV line 28 and line 226 restate this from the code.
- **Duplicates.** One entry per (cause, effect-target) pair (DYN 691-693) [INFERRED].
  - The same claim content reached through two lifting targets is impossible within one call, because targets
    differ.
  - All attestations of one content are in one entry's `attestations` (IBD §2.2: one record per content, every claim
    kept).

### 1.6 Supporting, conflicting and alternative evidence
- **Support.** The claim's own attestations (SB line 180). For a lifted claim, the original description-level claim
  is the support, and the describes links are cited (PLAN §9.3, line 274) [ESTABLISHED].
- **Rival and denying claims** [ESTABLISHED] (IBD §2.2, lines 48-58; SB line 180):
  - a denial is an attestation of the same content with polarity false;
  - accepted assertion plus accepted denial is a polarity dispute (judgement "disputed"), with both sides listed. DO
    Q6 line 54: inspector asserts (testimony, accepted) and cm-1 denies (inference, accepted);
  - unreviewed attestations are pending and never decide (IBD line 57-58).
- **Rivals across levels are not rivals** [ESTABLISHED] (F-B1).
- **Admissible support for E2 scoring.** HR §5.1 (line 156) proposes "the usable attestations of **accepted** claims".
  It is a harness proposal that the contracts must confirm (HR line 140) [INFERRED/proposed]. Two points follow:
  - by U-2 and Occ-2, an accepted claim with `applies: false` "does not answer what caused the happening" (SB line
    363). A contract should therefore treat its attestations as **not** admissible support for "what caused X". The
    HR rule as written does not exclude them [INFERRED: a contract question];
  - for `applies: null` (disputed occurrence), the design gives no admissibility rule [INFERRED: a contract question].
- **Gap: describes-link provenance.** PLAN §9.3 requires the lifted answer to *cite the describes links*. `lifted_via`
  reports only the {description, occurrence} pair, not the describes link's attestations or judgement (DYN 706-708)
  [INFERRED from code; a potential gap against an ESTABLISHED requirement].

### 1.7 Derivation rules and admissible premises
- **None** [ESTABLISHED] (DI-7, DI lines 219-249; E2DEC line 16, "no derivation record, rule or premise type is
  designed or added before E2"; E2DEC line 55, "no fabricated derivations").
  - A claim attested with basis `inference` (DO R4, cm-1) gets status INFERRED from its basis alone. That is not a
    formal derivation (DI-7, GAP-CAUSE-7).
  - Lifting is a read-time link with no new claim (SB line 332 "lifting is a read-time link, not identity of
    content"; plan §9.3). It is not a derivation, and nothing should be presented as `{rule, premises}`.

### 1.8 Refusals
- **Reader-side: no documented refusal** [INFERRED: none in SB, PLAN, E2D, HR's refusal list (HR line 254)].
- **Writer-side.** `claim_cause` refuses `cause == effect` with `ValueError("a happening does not cause itself")`
  (DYN 409-410). This is documented **only in the implementation**: no design text found (grep of docs/ and
  benchmark/e2 for "cause itself" / "self-caus" gives no hits) [INFERRED, not established].

### 1.9 Known limitations and gap ids
- **GAP-CAUSE-1:** no chain query (SB deferred capabilities, line 33; SB line 462).
- **GAP-CAUSE-2:** no forward reader.
- **GAP-CAUSE-3:** no intervention.
- **GAP-CAUSE-4:** no automatic inference.
- **GAP-CAUSE-5:** no strength or mechanism.
- **GAP-CAUSE-6:** no failure propagation.
- **GAP-CAUSE-7:** no derivation record.

Sources: INV lines 237-256; E2D line 155; E2D C6 and C7 (lines 106-107) are G questions. **DI-20:** `causes_of` loads
a whole world (performance only; DI line 59).

---

## 2. `explain(world, type, roles, t, as_of=None, perspective=SYSTEM)`

### 2.1 Supported question classes and input conditions
- "Why does state S hold at t (one step back: the event and claim that explain it)?" (E2D C4, line 104)
  [ESTABLISHED].
- "What explains state S, and was the explaining event's occurrence accepted?" is a **composition**: `explain` →
  `occurrence_status` (E2D X4, line 132). The occurrence check is therefore not expected inside `explain`
  [ESTABLISHED as a question class].
- **Input.** A content (type, roles) and a valid time t. Unknown role names are refused (§2.8).

### 2.2 Output fields and permitted vocabulary
- **Design** [ESTABLISHED] (SB "Schema and API", line 203): "`explain(world, type, roles, t)`: the judged state, its
  **accepted** initiating events, and their causal claims".
- **One step back** [ESTABLISHED] (SB deferred capabilities, line 33: "`explain` stops one step back"; SB line 463:
  "`explain` stops at the causes of the initiating event").
- The fields `content`, `holds` (an Answer with status and support), and `initiated_by` [INFERRED: docstring; DYN 736].
  Each `initiated_by` entry has event, claim, claim_status, claimed_by, start, end, occurrences and `causes` (each a
  `causes_of` entry). INV line 228 restates them from code.
- **Vocabulary.** The Answer statuses (V02 §5.6) and the claim labels (IBD) [ESTABLISHED by the shared rules].
- **Illustration** (DO Q5, lines 47-51):
  - "operational ... ASSERTED, support [att:…]";
  - "initiated by ev-test-run (claim accepted, by ['technician']), ended 11-05 16:00, describing ['o-test-run']";
  - then each causal claim with level, lifted_via, judgement, status and claimed_by.

### 2.3 Judgement and uncertainty semantics
- **An explanation is only what was asserted and accepted** [ESTABLISHED in substance by the never-inferred rule
  (PLAN §9.3; V02 §3.2)]. "Earlier events without causal claims are not causes" is docstring wording [INFERRED];
  DO Q6 line 57 illustrates it.
- **Which initiating events.** The design says "accepted initiating events" (SB line 203). This could mean either:
  - (a) the `initiates` claim is accepted; or
  - (b) the event's account is accepted;
  - or both. The design does not say which [INFERRED: ambiguity to put to the owner].
- **Timing.** The approved causal timing rule B-time (SB line 22, LABS-1.016) is stated generally: "an event cannot
  explain a transition that certainly precedes the start of its occurrence". Its "unresolved" handling (keep the
  explanation, `timing: "unresolved"`) is specified with `changes` in mind (its test file is
  `tests/test_h_b6_causal_timing.py`).
  - Whether B-time governs `explain` is not stated [INFERRED].
  - `explain` instead uses "ended by t" (docstring; DYN 727-728). See Discrepancies D-E2 and D-E3.
- **Lifting, F-B1, U-2, Occ-2** apply to the `causes` part through `causes_of` [ESTABLISHED by §1].
- **Holding judgement.** `holds` is the canonical record's projection (IBD §3, line 159) [ESTABLISHED]. Its status may
  be INFERRED by functional exclusivity (IBD addendum, lines 117-124; V02 §4.4).

### 2.4 Temporal, perspective and world visibility
- The context ⟨w, p, τ, t⟩ applies throughout [ESTABLISHED: V02 §6]. Illustrations: DO Q7 lines 64-65 (state in
  `plan-no-repair`; UNKNOWN for the inspector).
- **Initiating events' times come only from accounts the perspective accepts** [ESTABLISHED as recorded]
  (SB D-B-6, lines 29 and 335). "A change claimed by an unaccepted account has no timing for that perspective."

### 2.5 Ordering and multiplicity
- **Design gives no order** [INFERRED].
- DYN 726-735 [INFERRED]:
  - initiators appear in `_events_claiming` order (records sorted by type and stated roles, DYN/model `_contents`);
  - causes are the concatenation of `causes_of(event)` and then `causes_of(each occurrence)`, deduplicated on
    (cause, effect), first seen kept, and not re-sorted.

### 2.6 Supporting, conflicting and alternative evidence
- **Provenance of the initiating claims** [ESTABLISHED: the general requirement]:
  - SB line 180 (four distinctions, "each kept separate in the data and in every answer"): "every claim lists its
    attestations (attester, polarity, basis, acceptance state)";
  - SB line 178: an `initiates`/`terminates` claim "is content attested by a source"; the change is judged
    separately;
  - an `initiates` claim is a claim. The design therefore requires its attestations (ids, with attester, polarity,
    basis and acceptance state) to be reported. `effects_of` and `causes_of` do so (`attestations`, DYN 168 and 712).
- **What `explain` reports today** [INFERRED from code]: each initiating event's claim label, `claim_status` and
  `claimed_by` (attester names only), with **no attestation ids** (DYN 379-382, 735).
  - **This is a potential gap against an established requirement, not a reason to weaken the contract** (HR line 168
    raises the same question).
  - Also: no stated support for the event's interval (the `interval()` record is not returned).
- **Support for "why S holds."** The answer's `support` [ESTABLISHED: IBD §2.2, deciding attestations]. HR line 158
  proposes that `explain`'s evidence be "the answer's `support`, and the accepted causal claims about each initiating
  event" [proposed]. The same `applies: false` admissibility question as §1.6 arises.
- **Rivals.** Disputed or denied causal claims are listed in `causes` with their judgement (DO Q6). Unaccepted
  initiating claims: see D-E1.

### 2.7 Derivation rules
None [ESTABLISHED: DI-7; E2DEC line 55]. `explain` is a fixed composition (holds → initiating claims → causes_of;
INV line 318), not a derivation, and must not present one (GAP-MULTI-6 for chained answers).

### 2.8 Refusals
- **Unknown role names: `UnknownRoleError`** (a `ValueError`) [ESTABLISHED] (R2, lines 50-62: "Readers affected: ...
  `explain` (`roles`)"; approved LABS-1.053; HR line 254 marks it established).
- No other reader-side refusal documented [INFERRED].

### 2.9 Limitations and gap ids
- **GAP-CAUSE-1:** one step only; no chains (SB lines 33, 462-463).
- **GAP-MULTI-1, GAP-MULTI-4, GAP-MULTI-6.**
- **No occurrence-status check inside `explain`** (E2D X4 composes it) [ESTABLISHED as a composition].
- **Performance:** SB lines 404-405 ("`explain` computes intervals for every initiating claim before filtering to the
  events that ended by t"). This is the one place a design document mentions the "ended by t" filter, as an
  observation in a performance note, not as a decision.

---

## 3. `changes(world, subject, t1, t2, as_of=None, perspective=SYSTEM)`

### 3.1 Supported question classes and input conditions
- "When did S begin and end, and which boundaries are certain or only possible?" (E2D C5, line 105) [ESTABLISHED].
- "What changed during a period?" (stage-d-review line 153: "yes, `changes()`").
- **Q-B1** [ESTABLISHED, LABS-1.015] (SB decision register, line 20; contract, lines 49-63). `changes` reports
  transitions **whose valid time intersects the requested interval**, with:
  - uncertain windows;
  - world-state vs judgement categories;
  - explanations only from accepted effect claims (rulings Q-B1.1, Q-B1.2, Q-B1.4).
- **Interval** (t1, t2], open at t1 [ESTABLISHED] (SB line 59 "relative to (t1, t2]"; line 74-75 "a change at exactly
  t1 is already in effect at t1, so it is outside").
- **Subject: any thing.** Tracks are functional slots keyed by the subject, or any other content involving it
  [ESTABLISHED: SB lines 54-55]. Frames are included (INV line 126, line 146) [INFERRED: inventory].
- **Original requested contract** [ESTABLISHED as the request ruled on] (SB Q-B1, lines 123-125):
  - keep event time, transition valid time, knowledge time and explanations apart;
  - "an event outside the interval may explain a transition inside it, but is never itself an in-period change".

### 3.2 Output fields and permitted vocabulary
- **Contract** [ESTABLISHED] (SB lines 50-63):
  - `subject`, `from`, `to`, `context`: {world, perspective, as_of};
  - `transitions`, each with:
    - `track`: {kind "slot", type, key, value_role} | {kind "content", type, roles, params};
    - `category`: "world-state" | "judgement";
    - `before` and `after`: {status, values | holds, support, conflicts};
    - `window`: (earliest, latest), "possible transition interval; equal when certain";
    - `within`: "certain" | "possible";
    - `began`, `ended`: [contents];
    - `explanations`: [{event, effect, content, claim, claim_status, claimed_by, start, end, occurrences,
      attribution: "unique" | "ambiguous"}];
  - top level: `began` and `ended` (views over the transitions) and `unchanged`: n.
- **`timing`: "consistent" | "unresolved"** on each explanation [ESTABLISHED] (SB B-time, line 22, LABS-1.016). It is
  added after the Q-B1 contract text (the field is not in the line 61-62 schema, but B-time names it).
- **Status values in `before`/`after`** [ESTABLISHED] (V02 §5.6; ICD §3.3): ASSERTED, STIPULATED, INFERRED, DISPUTED,
  UNKNOWN.
- **Fields beyond the contract** [INFERRED: code only]:
  - top-level `began`/`ended` entries carry status, stated_by, support, outcome_id, category, within, window,
    claimed_events and content (DYN 351-357);
  - DO Q3 (lines 31-33) shows `stated_by` and `claimed events`.

### 3.3 Judgement and uncertainty semantics
- **Categories (Q-B1.2)** [ESTABLISHED] (SB lines 70-71):
  - world-state: between two accepted states (a value, or accepted "does not hold");
  - judgement: into or out of UNKNOWN or DISPUTED;
  - "a judgement transition is never presented as physical change".
- **Uncertain times (Q-B1.1)** [ESTABLISHED] (SB lines 72-75):
  - accepted A, then only UNKNOWN, then accepted B ≠ A is **one** world-state transition whose window is the UNKNOWN
    gap. "No instant is invented";
  - relative to (t1, t2]: certain if the window lies inside, possible if it overlaps, omitted if outside.
- **Probe cases** [ESTABLISHED as approved, verified results] (SB table, lines 88-96): cases 1 to 6, including:
  - case 3: a state with no stated end never holds, so there is no transition;
  - case 4: an accepted rival gives a judgement transition ASSERTED a → DISPUTED (a, b);
  - case 5: UNKNOWN → a with no explanation;
  - case 6: a delayed effect is explained, and the event itself is not a change.
- **Explanations (Q-B1.4)** [ESTABLISHED] (SB lines 76-80):
  - only accepted initiates / terminates claims about a content that began or ended in the transition count;
  - a claim is attributed only to activations that its event did not certainly start after: "an effect cannot
    precede the start of its event. That is the one temporal constraint used; **proximity is never evidence**";
  - a claim that fits more than one activation of the same content **on the whole timeline** is listed on each as
    "ambiguous" and never chosen;
  - claims are looked up only for contents that change in a returned transition.
- **B-time** [ESTABLISHED, LABS-1.016] (SB line 22):
  - an event cannot explain a transition that certainly precedes the start of its occurrence;
  - occurrence time is the event's **accepted** occurrence interval (valid time), never the time its account was
    recorded;
  - if the occurrence time is uncertain (its start window overlaps the transition window) or unavailable (no
    accepted account), the explanation is **kept**, with `timing: "unresolved"`; otherwise `timing: "consistent"`.
- **One functional judgement (Q-B2)** [ESTABLISHED, LABS-1.015] (SB line 21 and lines 81-86):
  - `changes` uses `value_at`'s functional-conflict judgement;
  - a content in a functional conflict is DISPUTED, with its own support and the rival attestations, including
    rivals that do not mention the subject.
- **Attested constraints** (an exclusive office) are evaluated at each boundary [ESTABLISHED as implemented and
  approved] (IB line 168; IB line 75: `changes` reports the office dispute).
- **Slot status (C-6)** [ESTABLISHED, LABS-1.040/1.041] (ICD §3.3, lines 89-94; ICD line 214; IC lines 36-37, 76-77,
  134-135):
  - a slot track's state takes its status from the core rule over the support of the **values held (or disputed) at
    the sample time**, exactly as `value_of`;
  - an accepted denial of another value is not support for the value held; it stays visible through the content
    tracks and the evidence;
  - DISPUTED, UNKNOWN and the categories are unchanged.
- **Nothing inferred from order** [ESTABLISHED: Q-B1.4 "proximity is never evidence"; PLAN §9.3].
- **The occurrence-status check (Occ-2 / U-2) for explanations is not addressed by Q-B1** [INFERRED]. No design text
  says whether an explanation whose event describes a denied occurrence should carry `applies`. Occ-2 (SB line 18)
  is worded generally ("claims involving a denied occurrence do not apply"), but effect claims name descriptions, not
  occurrences.

### 3.4 Temporal, perspective and world visibility
- **Judged for the knowledge time, perspective and world** [ESTABLISHED] (SB lines 123-125; SB line 52, `context`).
- **Event time vs transition valid time vs knowledge time are kept apart** [ESTABLISHED] (SB lines 124-125).
- **Occurrence time only from the accepted account** [ESTABLISHED] (B-time; D-B-6).

### 3.5 Ordering and multiplicity
- **Design gives no transition order** [INFERRED].
- DYN 340 and 358 [INFERRED]:
  - explanations are sorted by (effect, event);
  - transitions are sorted by (window earliest, window latest, str(track)).
- **Ambiguous attribution: one claim may appear under several transitions** [ESTABLISHED] (Q-B1.4).
- DO Q3 line 36 shows one event listed twice (initiates and terminates) on one transition: "ev-test-run (initiates,
  unique)", "ev-test-run (terminates, unique)".

### 3.6 Supporting, conflicting and alternative evidence
- **Should a world-state transition rest on both sides?**
  - **Yes, by definition** [ESTABLISHED]. A world-state transition is "between two accepted states" (Q-B1.2), and the
    contract gives `before` and `after` each their own `support` and `conflicts` (SB line 57).
  - So an established world-state transition has an accepted before-state **and** an accepted after-state, each with
    its deciding support.
  - A judgement transition has support on its accepted side only (the other side is UNKNOWN with no deciding claims,
    or DISPUTED with support and conflicts).
  - The design states this structurally, not as an evidence-admissibility rule. HR line 159 proposes "the `support`
    of both sides of each transition" and asks the question (line 167) [the proposal is consistent with the
    design].
- **Possible implementation gap** [INFERRED from code]:
  - for a content track whose accepted state is "does not hold" (an accepted denial), `support` is built only from
    contents judged True or disputed (DYN 239). The side's support list is then empty, while its status is computed
    from the deciding attestations (DYN 257-258);
  - so a world-state transition holds → does-not-hold may show an empty `support` on the after side. Both sides
    would not then be citable, against Q-B1.2's "accepted 'does not hold'".
- **Conflicts.** Rival attestations under functional or attested constraints, in `conflicts` per side
  [ESTABLISHED: Q-B2; SB line 57].
- **Explanations are not support for the transition** [ESTABLISHED: SB line 178, asserted effect vs accepted change;
  V02 C5]. Q-B1.4 counts only accepted claims as explanations. Unaccepted claims are not listed [ESTABLISHED].
- **Explanation provenance.** Each explanation gives `claim`, `claim_status` and `claimed_by` but **no attestation ids**
  (contract schema line 61; DYN 325-330). By SB line 180 ("every claim lists its attestations") this is the same
  potential gap as `explain` [the requirement is ESTABLISHED; the gap is INFERRED].
- **Top-level `began` / `ended` views** carry one side's support only: after for began, before for ended (DYN
  350-353) [INFERRED]. They are views, not the transition record.

### 3.7 Derivation rules
- **None** [ESTABLISHED: DI-7].
- The one temporal constraint (B-time / Q-B1.4) is a filter, not a derivation.
- A slot's other values may be INFERRED by functional exclusivity (IBD addendum) without a rule/premise record
  [ESTABLISHED: V02 §5.6 lists functional exclusivity as a declared query-time rule, not a recorded derivation].

### 3.8 Refusals
- No documented refusal [INFERRED].
- t1 ≥ t2, or an unknown subject: no design text; behaviour unspecified [INFERRED].

### 3.9 Limitations and gap ids
- **GAP-CAUSE-1..4.**
- **GAP-MULTI-2** (no "at the time of event E" helper).
- **DI-9 / DI-20 to DI-22** performance (IC line 124-126: `changes(depot-7)` 209 → 275 queries).
- **Stale design text:** SB "Remaining limitations" (lines 470-472) still says "`changes` lists every claimed event
  ... needs a ruling". That was resolved by Q-B1.4 (LABS-1.015). SB "Schema and API" line 201 describes the pre-Q-B1
  behaviour.

---

## 4. `process_steps(world, process, t, as_of=None, perspective=SYSTEM)`

### 4.1 Supported question classes and input conditions
- P1 "What are the steps of process R, in time order?" [ESTABLISHED] (E2D §3.5, line 112).
- P2 "A step's occurrence is disputed: is it kept and flagged, not silently dropped?" [ESTABLISHED] (line 113).
- P4 "Two steps with overlapping or unknown intervals: is no order asserted?" [ESTABLISHED as a question] (line 115).
- P5 nesting: `parts` or repeated `process_steps`, one level per call [ESTABLISHED] (line 116).
- X5 and X6 compositions (lines 133-134).
- **Process membership is part-of between occurrences; processes and actions are classifications** [ESTABLISHED]
  (SB B-arch, line 14; SB B0, line 170; V02 DR-05, line 711).
- **Input.** A process occurrence and a valid time t.

### 4.2 Output fields and permitted vocabulary
- **Per step: its own `judgement` and `status`** [ESTABLISHED] (IBD §4, line 168: "`process_steps` (each step gains its
  own `status`)"; IB line 32-33: "each process step gains `judgement` and `status`").
- **Judgement: established or disputed (DI-1: listed, never dropped)** [ESTABLISHED] (DI-1, DI line 80; IBD §6 line
  208).
- E2D line 46: "direct `part-of` steps ordered by interval start, disputed steps kept" [ESTABLISHED as the E2 reader
  description].
- **Fields `occurrence`, `descriptions`, `start`, `end`, `kinds`, `actors`, `support`** [INFERRED: docstring; DYN
  751-755; INV line 277]. Illustration: DO Q1 lines 12-17.
- HR line 150 proposes each step's `support` as evidence [proposed].

### 4.3 Judgement and uncertainty semantics
- **Membership judged by the canonical record of part-of at t** [ESTABLISHED: IBD §6 line 208 (F, via facts_about)].
- **Descriptions, kinds and actors come from the perspective's accepted descriptions** [INFERRED: docstring]. This is
  consistent with V02 §3.2 (lines 193-195, 204): "the descriptions of occurrence o are those with usable describes
  links".
- **Intervals use only accepted accounts** [ESTABLISHED as recorded] (D-B-6).
- **Processes are not modelled as ongoing/homogeneous** [ESTABLISHED as a deferred capability] (SB line 34, 464-465;
  GAP-PROC-5).
- **Actions are classifications without an agent-capacity check** [ESTABLISHED as recorded] (SB D-B-4, lines 28 and 333;
  stage C adds capacity).

### 4.4 Visibility
- **Context ⟨w, p, τ, t⟩** [ESTABLISHED].
- **DI-14** [ESTABLISHED as an open issue] (DI lines 448-466). In a variant world branching before an event, the
  describes link is inherited and the account is not. `process_steps` then lists the description among a step's
  descriptions "without saying that the plan holds no account of it". No judgement is affected (no interval:
  `interval` finds none). GAP-MULTI-8 (INV line 351).

### 4.5 Ordering and multiplicity
- **Order by interval start** [ESTABLISHED] (E2D line 46, "ordered by interval start"; docstring "ordered by their
  descriptions' intervals").
  - **Which instant of a Window "start" means is not designed** [INFERRED]. DYN 750 and 757 use `start.earliest`.
  - Ties are broken by occurrence id; `start.latest` is not used (whereas `events()` sorts by earliest, latest, id;
    model.py 1536).
- **Undated steps.** INV line 277 says "undated last" [INFERRED: inventory from code]. DYN 756-757 gives undated steps
  the key `far` = the **latest dated start**, so an undated step ties with the latest-starting step and is ordered
  among them by occurrence id. It is **not** guaranteed last. See D-P2.
- **A step with several descriptions.** Its interval is the description interval with the earliest start (DYN 749-750)
  [INFERRED: no design text].
- **List order is not an assertion of succession** [INFERRED, from SB line 179 and V02]. Certain succession is
  `before()`'s question. P4 asks that no order be asserted for overlapping or unknown intervals; the list still has an
  order. The contract should say what the order means.
- **One level only** (GAP-PROC-6) [ESTABLISHED as a gap].
- **Duplicates.** One entry per part player per part-of content (DYN 744-747) [INFERRED].

### 4.6 Supporting, conflicting and alternative evidence
- **Support** is the part-of content's deciding attestations. For a disputed step, its assertions and denials are
  cited (DI-1: "citing both sides", DI line 97) [ESTABLISHED].
- **Not listed:** pending or unreviewed memberships [INFERRED: facts_about lists established and disputed only;
  facts_about docstring model.py 1677-1683].

### 4.7 Derivation rules
None [ESTABLISHED: DI-7]. Order is derived from intervals (GAP-PROC-1). It is not a derivation, and no explicit order
relation exists.

### 4.8 Refusals
None documented [INFERRED].

### 4.9 Limitations and gap ids
GAP-PROC-1..7 (INV lines 290-304; E2D line 156; E2D P6-P9 are G questions).

---

## 5. `before(world, a, b, as_of=None, perspective=SYSTEM)`

### 5.1 Supported question classes and input conditions
- P3 "Did step a end before step b began (with interval windows)?" [ESTABLISHED] (E2D line 114).
- **Inputs are event descriptions** [ESTABLISHED] (SB line 179, "`before()` compares intervals"; the docstring:
  "Temporal succession of two descriptions").
  - P3 is phrased with *steps* (occurrences); the caller must map steps to descriptions [INFERRED].
  - An occurrence id has no account, so `interval` gives None and `before` answers None [INFERRED: DYN 396-398].

### 5.2 Output and vocabulary
**True / False / None** [ESTABLISHED] (SB line 179: "certainly before, or None if they overlap"):
- True: a certainly ends before b starts;
- False: b certainly before a (docstring);
- None: they overlap or cannot be ordered.

### 5.3 Semantics
- **Succession says nothing about causation** [ESTABLISHED] (SB line 179; V02 line 188; DO Q6 line 57).
- **Windows: never a guess** [ESTABLISHED in substance: V02 §3.2 "uncertain boundaries ... windows"; Q-B1.1 no
  invented instants].
- **Boundary case** [INFERRED]. `certainly_before` uses `a_end.latest <= b.start.earliest` (semantics.py 156-159), so
  touching intervals (a ends 16:00, b starts 16:00) count as "before". The design does not say whether touching
  counts as overlap.
- **Only accounts the perspective can use** [ESTABLISHED as recorded: D-B-6]. Clock alignment (V02 §4.5): times on
  different clocks compare only through an accepted alignment, otherwise UNKNOWN. `before` does not mention clocks
  [INFERRED].

### 5.4 Visibility
Per perspective, knowledge time and world, through `interval` [ESTABLISHED: D-B-6]. No valid-time parameter
(intervals are the valid times).

### 5.5 Ordering and multiplicity
Not applicable. When a description has several usable accounts, see `interval` (§6.5).

### 5.6 Evidence
HR line 163 proposes that it cites nothing [proposed]. The design gives no evidence rule [INFERRED].

### 5.7-5.9 Derivations, refusals, gaps
- No derivation [ESTABLISHED].
- No refusal documented.
- GAP-PROC-1, GAP-PROC-4; GAP-MULTI-2.

---

## 6. `interval(world, description, as_of=None, perspective=SYSTEM)`

### 6.1 Questions and inputs
- P3 with `before` (E2D line 114) [ESTABLISHED].
- Used to choose a time for chained questions (INV lines 331-332; GAP-MULTI-2).
- Input: an event description.

### 6.2 Output
- **The occurrence interval** [ESTABLISHED] (V02 §3.2 table, line 175: an event description's interval is on its
  source's attestation; V02 §4.5: event time = occurrence interval).
- The tuple (start Window, end Window, record) or None [INFERRED: docstring; DYN 122-130].

### 6.3 Semantics
- **"Only an account the perspective can use; a change claimed by an unaccepted account has no timing for that
  perspective"** [ESTABLISHED as recorded, D-B-6] (SB lines 29 and 335).
- **Occurrence time, never record time** [ESTABLISHED: B-time].

### 6.4 Visibility
Per perspective and knowledge time; a variant inherits the base account within its snapshot [ESTABLISHED: V02 §6.2].
DI-14: an account starting after the branch point is not inherited, so the interval is None in the variant
[ESTABLISHED: DI line 459-461].

### 6.5 Multiplicity
- **Several usable accounts of one description: no design rule** [INFERRED].
- DYN 128-130 returns the one with the **lowest attestation id** (arbitrary with respect to time). Other accounts'
  windows are not reported. See D-I1.

### 6.6 Evidence
HR line 162 proposes "the account attestation it uses" [proposed; consistent with D-B-6].

### 6.7-6.9 Derivations, refusals, gaps
- No derivation.
- No refusal.
- GAP-PROC-4 (no duration); GAP-MULTI-2.

---

## 7. `effects_of(world, event, t, as_of=None, perspective=SYSTEM)`

### 7.1 Supported question classes and input conditions
- C3 [ESTABLISHED] (E2D §3.4, line 103): "An event claims an effect: did the claimed change actually follow
  (accepted state change), or not?"
  - It is class H because of GAP-HARNESS-2: initiates/terminates need a proposition id.
  - E2D line 45 describes it as "claimed effect against accepted state change".
- **Stage B reading** [ESTABLISHED] (SB "Schema and API", line 200): "`effects_of(world, event, t)`: each claimed
  effect, the claim's judgement, and the accepted state change".
- **Input: an event description** [ESTABLISHED]:
  - effect claims are `initiates(event, proposition)` / `terminates(event, proposition)` (V02 §3.2, line 189);
  - an asserted effect is a claim "about a description" (SB B0 table, line 178; SB line 163-165);
  - occurrences do not play `initiates`/`terminates` in the Stage B schema (SB lines 186-188 add only `causes` for
    occurrences) [INFERRED from the schema text].
- **Writers** [ESTABLISHED as recorded, D-B-1] (SB lines 25 and 329): effect claims are written by `claim_effect` /
  `account`; `record_event` writes none.
  - PLAN line 68 had planned `record_event` to write them. D-B-1 records the change ("please confirm"), not
    individually ruled.
  - The outcome is a proposition identified by its A0.1 id (SB line 196; PLAN line 50).
- `t`: the valid time at which the claim contents are judged. They are timeless (D-B-2), so t matters only through
  the canonical judgement [INFERRED: DYN 150].

### 7.2 Output fields and permitted vocabulary
- **Design** [ESTABLISHED] (SB B0 line 178): "an `initiates`/`terminates` claim is content attested by a source; the
  change is judged separately from the outcome's own attestations before and after the event (`effects_of`: `claim`
  vs `state.accepted_change`)". So the fields `claim` and `state.accepted_change` are named in design text.
- **Claim label** [ESTABLISHED] (IBD §2.4 table, line 102: "claims vocabulary, `effects_of`, `causes_of`"). The labels
  are accepted, disputed, denied, unreviewed, not yet effective, not established, unknown, rejected, retracted and
  superseded. The docstring lists five (accepted, unreviewed, rejected, denied, disputed).
- **Before and after states** [ESTABLISHED in substance: SB line 178, "judged ... before and after the event"]. They
  are Answers (status and support) [INFERRED: DYN 157-163].
- **Other fields** [INFERRED: docstring and DYN 164-168; INV line 227]: `kind` (initiates / terminates),
  `outcome_id`, `outcome` {type, roles, params}, `claim_status`, `claimed_by`, `attestations`, and `state` = {before,
  after, accepted_change} or None.
- **Illustration** (DO Q2, lines 21-23):
  - "claim accepted; state before UNKNOWN/None, after ASSERTED/True; accepted change: True";
  - "claim unreviewed; ... accepted change: False" (SB line 256 says the same in prose).

### 7.3 Judgement and uncertainty semantics
- **Asserted effect vs accepted change are independent** [ESTABLISHED] (SB B0 line 178; SB line 233-237, reference
  effect claims). The docstring says "A claim can be accepted while the state change is not (and the reverse);
  neither implies the other". SB test list line 273 confirms: "claimed vs accepted effects, including the
  technician's own view of the vibration claim".
- **States are judged from the outcome's own attestations, never derived from the claim** [ESTABLISHED] (SB line
  178; V02 §3.2, line 182: a state transition is "the presence of initiates / terminates propositions" about an
  event, yet "None of these is required", lines 190-191).
  - A state may begin with no initiating claim (V02 C5; SB test list line 274, "a recorded state with no initiating
    event").
  - The inspection is the evidence for "faulty", and "nobody claims it as an initiator" (SB lines 229-230).
- **What an accepted change is.**
  - The design gives no rule for comparing the before-state and after-state [INFERRED].
  - V02 C3 (lines 579-583) gives the expected pattern: `part-of(b1)` attested up to the swap's start and
    `part-of(b2)` from its end, with `terminates`/`initiates` claims.
  - The **Q-B1 rulings** (LABS-1.015) define transitions for `changes`:
    - world-state only between two accepted states;
    - into or out of UNKNOWN or DISPUTED is a judgement transition, "never presented as physical change";
    - delayed effects (probe case 6) are allowed.
  - Whether Q-B1 binds `effects_of` is not stated [INFERRED]. See D-F1 and D-F2.
- **Timing.**
  - The event's times come only from an accepted account (D-B-6, SB line 335) [ESTABLISHED as recorded].
  - Without one, "a change claimed by an unaccepted account has no timing for that perspective". The implementation
    then returns `state: None` (DYN 155-156) [INFERRED].
  - The instants used ("just before the event starts" = start earliest − 1 µs, and "when it ends" = end latest)
    come from the docstring and DYN 157-159 only. INV GAP-MULTI-2 (line 342) records them as implementation choices
    [INFERRED: not designed].
- **B-time (LABS-1.016)** concerns explanations of transitions. `effects_of` attributes nothing to a transition, so
  B-time is not directly applicable [INFERRED].
- **Occurrence status.**
  - The design does not say whether `effects_of` checks the described occurrence's existence [INFERRED].
  - Occ-2's general wording (SB line 18) and the LABS-1.011 amendment (SB lines 349-350) cover `causes_of` only.
  - Profile reports compose `effects_of` with `occurrence_status` (IBD §6 line 222, "sampling accounts:
    `occurrence_status`, `effects_of`"; INV line 232).
- **Canonical judgement and constraints** [ESTABLISHED] (IBD §4, lines 177-179: `effects_of` "read[s] the record" and
  gains "functional and attested-constraint conflicts (DI-11) and the corrected labels (DI-5)"; IBD §6, line 204).
  - A claim content can therefore be DISPUTED by polarity.
  - Effect claims have no declared slot, so DI-11 is latent for them [INFERRED].
- **Answer unchanged by increments C and D** [ESTABLISHED] (ICD line 122; pre-e-increment-d-design.md line 183).

### 7.4 Temporal, perspective and world visibility
- **Claims are judged per perspective, knowledge time and world** [ESTABLISHED] (SB line 180; D-B-2).
  - Illustration: the technician's own view of the vibration claim (SB line 273).
  - Snapshot: a plan branched before the repair was recorded does not see it (SB line 250, `plan-no-repair`).
- **States are judged in the same context** [ESTABLISHED: V02 §6]. The before-state and after-state are `holds`
  answers for the same ⟨w, p, τ⟩ [INFERRED: DYN 157-159].
- **A variant world** inherits claims and accounts per V02 §6.2. Under DI-14, an account not inherited means no
  interval, so `state: None` [INFERRED from DI lines 459-461].

### 7.5 Ordering and multiplicity
- **No design order** [INFERRED].
- Implementation: entries follow `_contents` order, sorted by type and stated roles (model.py 1707-1708), so
  initiates and terminates are grouped by type [INFERRED].
- **One entry per claim content (event, kind, outcome).** All attestations of that content (assertions and denials,
  every source) are in that entry's `attestations` [ESTABLISHED: IBD §2.2, one record per content with every claim
  kept].

### 7.6 Supporting, conflicting and alternative evidence
- **Two separate evidence sets** [ESTABLISHED: SB B0 line 178, "the change is judged separately from the outcome's
  own attestations"]:
  - **(a) For the claim judgement:** the attestations of the `initiates`/`terminates` content itself, each with
    attester, polarity, basis and acceptance state (SB line 180). The deciding ones form the record's support (IBD
    §2.2).
  - **(b) For the judged before/after state:** the attestations of the **outcome proposition**, the `support` of each
    `holds` answer (and `conflicts`/`constraint_support` where a slot or attested constraint applies; Q-B2; DI-19).
  - Neither set supports the other. An accepted claim is not evidence that the state changed, and an accepted state
    is not evidence for the claim [ESTABLISHED: SB line 178; docstring].
- **The event's account attestation** gives the times at which the states are judged (D-B-6). It is provenance for
  the timing. `effects_of` does not report it [INFERRED: DYN 148, `span[2]` unused].
- **Rival and denying effect claims.**
  - A denial is an attestation of the **same** effect content with polarity false (`claim_effect(..., polarity=False)`,
    DYN 98 and 108). It is conflicting evidence **for the claim judgement**: accepted assertion plus accepted denial
    gives "disputed"; an accepted denial alone gives "denied" [ESTABLISHED: IBD §2.2 lines 55-56 and §2.4].
  - An unreviewed counter-claim is `pending` and never outranks an accepted claim [ESTABLISHED: IBD line 57-58 and
    line 90-92].
  - A **different** event's claim about the same outcome is a different content. It is not a rival of this claim and
    is not reported here [INFERRED: one content per (event, outcome); no design text makes claims by different events
    compete].
  - Claims of a different kind (initiates vs terminates) are also distinct contents [INFERRED].
- **Rival states are conflicting evidence only for the state answers.** A functional rival of the outcome (another
  value in the slot) is a conflict in the before/after Answer (Q-B2), not a conflict for the claim [ESTABLISHED by
  the separation; INFERRED as applied].
- **Admissible support for E2.** HR line 157 proposes "the usable attestations of accepted claims, and the `support`
  of the judged state before and after" [proposed]. This is consistent with (a) and (b) above. Whether a
  not-accepted claim's state support is admissible is for the contract to decide [INFERRED].

### 7.7 Derivation rules
- **None** [ESTABLISHED: DI-7; E2DEC lines 16 and 55].
- `accepted_change` is a comparison of two judged answers computed by the reader. It is not a recorded derivation,
  and must not be presented as `{rule, premises}`.
- A state may be INFERRED by functional exclusivity (IBD addendum) or from basis `inference` (DI-7).

### 7.8 Refusals
- **Reader-side:** none documented [INFERRED].
- **Writer-side (`claim_effect`), code only** (DYN 102-105) [INFERRED, not established]:
  - `kind` must be "initiates" or "terminates" (`ValueError`);
  - effects need proposition ids, from the core-0.4-a0 module (`ValueError`).
  - The need for A0.1 ids is designed (SB line 164-165; PLAN line 50), but the refusal message is not.

### 7.9 Known limitations and gap ids
- **GAP-HARNESS-2** (E2D line 103).
- **GAP-MULTI-2** (instants chosen by the reader; INV line 342).
- **GAP-CAUSE-3** [ESTABLISHED: INV lines 244-248]. Denying an event in a variant does not retract its claimed
  effects or later states, because states are judged from their own attestations.
- **DI-20** (whole-world loads; DI line 59, line 579). SB line 459: "`effects_of` does not use the memo".
- **DI9-D17** (memo scoping deferred).

---

## Discrepancies (docstring or implementation vs design)

Each item cites both sides. Per E2D §5.2, each needs the owner's decision; none is resolved here.

### `causes_of`
- **D-C1. Lifting requires describes links for both descriptions.**
  - Design: PLAN §9.3 (lines 273-276), "only when **both** descriptions have usable `describes` links ... to the
    occurrences asked about".
  - Implementation: DYN 683-712 lifts on the effect side only (claims about the effect's descriptions or
    occurrences). A cause description with no accepted describes link is still returned as lifted, with
    `cause_occurrences: []` and `applies: True` (`involved` then covers only the effect's occurrences).
  - Docstring silent.
- **D-C2. Cited describes links.**
  - Design: PLAN §9.3 line 274, "cites the `describes` links"; SB lines 208-209, "says which link it used".
  - Implementation: `lifted_via` = {description, occurrence} ids only. No describes attestation ids or judgement, and
    only the effect-side link (DYN 706-708).
- **D-C3. What "accepted describes link" means.**
  - Design: U-2 (SB line 16), "lifted through an **accepted** describes link".
  - Implementation: `descriptions()` (model.py 1544-1551) and `_Memo.occurrences` (DYN 54-63) treat a link as accepted
    if **any usable positive attestation** exists, not when the canonical judgement is ESTABLISHED. A describes link
    disputed by an accepted denial would still lift.
  - By contrast, `_event_roles` judges links by the canonical record (DYN 506).
  - `_Memo.occurrences` also ignores same-as identity, while `descriptions()` uses it.
- **D-C4. Sort order and vocabulary.**
  - Design: no sort order specified. Claim labels come from IBD (§2.4), which include "not yet effective", "not
    established", "unknown" and "superseded".
  - Implementation: DYN 713 ranks six labels; the others get rank 9.
  - INV line 28 lists only six labels.
- **D-C5. `cause_occurrences` and `level: "mixed"`** are named only in the docstring and code, not in design text
  (PLAN §9.3 describes the mixed form without the label).
- **D-C6. Evidence admissibility for claims with `applies: false` / `null`.**
  - Design: SB lines 361-364 (they "never answer what caused the denied happening").
  - Harness proposal: HR line 156 cites every accepted claim's usable attestations regardless of `applies`; the
    harness extractor `ev_claims` (evaluation/e2/readers.py 181-183) does the same.
- **D-C7. Self-causation refusal** is in code only (DYN 409-410, writer side). There is no design source, so as a
  documented refusal it would be "not established" (HR §9, line 249-252 rule).

### `explain`
- **D-E1. Which initiating events are included.**
  - Design: SB line 203, "its **accepted** initiating events".
  - Docstring: "the events claimed to have initiated it that ended by t, **with each claim's judgement**".
  - Implementation: DYN 726-735 includes initiates claims of **any** judgement (unreviewed, rejected, denied,
    disputed), filtered only by the event's end.
  - The reference world has a single, accepted initiator of "operational", so DO Q5 does not exercise the
    difference.
- **D-E2. The "ended by t" rule.**
  - Docstring and implementation: DYN 727-728 drop an initiator unless its accepted account's end latest ≤ t. This
    rule appears in no decision; SB line 404-405 mentions it only in a performance note.
  - Design: B-time (LABS-1.016) states the approved causal timing rule. That rule is "cannot explain what certainly
    precedes its start", with unresolved times **kept** as `timing: "unresolved"`.
- **D-E3. Initiators without an accepted account.**
  - Implementation: an event with no accepted account has `end` None and is **dropped** (DYN 727).
  - Design: B-time says an explanation whose occurrence time is unavailable is kept, marked unresolved. D-B-6 says an
    unaccepted account has no timing for the perspective (which does not say "omit").
- **D-E4. No attestation ids for the initiating claims.**
  - Design: SB line 180, "every claim lists its attestations"; SB line 178.
  - Implementation: `initiated_by` entries carry `claim`, `claim_status` and `claimed_by` only (DYN 379-382). Neither
    the `initiates` claim's attestations nor the account attestation behind start/end is reported.
  - HR line 168 raises the question. **This is a potential gap; the requirement stands.**
- **D-E5. No check that the content holds.**
  - Implementation: `initiated_by` is computed whatever `holds` says (DYN 722-735): initiators are listed even when
    the content is UNKNOWN, denied or disputed at t.
  - Design: silent; "why does S hold" (E2D C4) presupposes it holds.
- **D-E6. Lifted marking depends on call order.**
  - Implementation: causes are gathered from `causes_of(event)` first and then from `causes_of(occurrence)`,
    deduplicated on (cause, effect) with the first kept (DYN 729-734). A direct occurrence-level claim is therefore
    reported as `lifted` via the event's describes link (DO Q5 line 51: "o-bearing-replacement -> o-test-run
    (occurrence-level, lifted via ...)"), although the occurrence was also asked about directly. The result is not
    re-sorted.
  - Design: U-2 and SB lines 207-209 mark a claim as lifted only when it answers through a describes link.
- **D-E7. No occurrence check.**
  - Implementation: `explain` adds no `occurrence_status`/`applies` for initiating events.
  - Design: E2D X4 treats that check as a composition, so this is consistent. Occ-2's general wording (SB line 18)
    leaves open whether effect claims involving a denied occurrence should be marked.

### `changes`
- **D-X1. Empty support for an accepted "does not hold" side.**
  - Design: Q-B1.2 (SB line 70, world-state includes "accepted 'does not hold'"); contract schema (SB line 57,
    per-side `support`).
  - Implementation: DYN 239 builds `support` only from contents judged True or disputed. A content track's denied
    side has an empty `support`, while its `status` comes from the deciding denial (DYN 257-258).
- **D-X2. No attestation ids in explanations.**
  - Design: SB line 180.
  - Implementation and contract schema: SB line 61 lists `claim_status` and `claimed_by` only; DYN 325-330.
  - The Q-B1 contract itself omits attestation ids, so the two design texts differ. This is for the owner.
- **D-X3. B-time boundary.**
  - Design: SB line 22, "uncertain (its start window **overlaps** the transition window) → unresolved".
  - Implementation: DYN 302-306 gives "consistent" when `start.latest <= early`, so a start window that only touches
    the transition window's earliest point is "consistent", not "unresolved". Exclusion uses the strict
    `late < start.earliest`.
- **D-X4. A → UNKNOWN → A, and gaps through DISPUTED.**
  - Design: Q-B1.1 (SB lines 72-73) covers only accepted A, then UNKNOWN, then accepted B ≠ A.
  - Implementation: DYN 272-284 reports A → UNKNOWN → A as two judgement transitions, and never merges gaps through
    DISPUTED. The design does not cover these.
- **D-X5. Explanation claims judged at t2.**
  - Implementation: DYN 291-292 judges claims at t2.
  - Design: claims are timeless (D-B-2); no valid time is specified for judging them. Knowledge time and perspective
    are specified.
- **D-X6. Fields and order not in the contract schema.**
  - Implementation: top-level `began`/`ended` entries add status, stated_by, support (one side), outcome_id,
    category, within, window, claimed_events and content (DYN 351-357). Transitions and explanations are sorted
    (DYN 340, 358).
  - Design: the contract schema (SB lines 52-63) and no order.
- **D-X7. Stale design text.**
  - SB "Remaining limitations" (lines 470-472) says `changes` lists every claimed event, including those outside the
    period, "needs a ruling".
  - SB "Schema and API" line 201 describes pre-Q-B1 behaviour.
  - Both are superseded by Q-B1.4 (SB line 76-80, LABS-1.015). The design documents contradict each other until
    they are updated.
- **D-X8. Occurrence status for explanations.**
  - Design: not addressed by Q-B1 or B-time (Occ-2's general wording, SB line 18).
  - Implementation: explanations list `occurrences` without status or `applies` (DYN 325-330).

### `process_steps`
- **D-P1. Which start orders the steps.**
  - Design: "ordered by interval start" (E2D line 46).
  - Implementation: DYN 757 uses `start.earliest` and then occurrence id; `start.latest` is ignored. For overlapping
    or uncertain starts, a total order is still produced (P4 asks that no order be asserted).
- **D-P2. Undated steps.**
  - Inventory (INV line 277): "undated last".
  - Implementation: DYN 756-757 gives undated steps the latest dated start as their key, so they tie with that step
    and sort by id. They can precede it.
  - No design text exists.
- **D-P3. Interval of a step with several descriptions.**
  - Implementation: the earliest-starting description's interval (DYN 749-750). Other accepted accounts' intervals
    are not shown.
  - Design: none.
- **D-P4. Descriptions without an account (DI-14).**
  - Design: an open issue (DI lines 448-466).
  - Implementation: `descriptions` lists them without a flag (DYN 748).
- **D-P5. Pending memberships omitted.**
  - Implementation: through `facts_about`, only established and disputed memberships are listed.
  - Design: IBD §4 (line 166-168) requires disputed entries in place; it is silent on pending ones. No conflict, but
    the contract should state it.

### `before` / `interval`
- **D-I1. Several usable accounts of one description.**
  - Implementation: `interval` returns the lowest-id usable attestation (DYN 128-130), and `before` compares those
    records (DYN 396-403). Which account is used does not depend on time or world depth.
  - Design: D-B-6 says only "an account the perspective can use".
- **D-I2. Touching intervals.**
  - Implementation: `certainly_before` uses `<=` (semantics.py 158-159), so touching intervals are "before" (DO Q6
    line 57 uses this: inspection ended 09:30, test run 15:30, not touching).
  - Design: "certainly before, or None if they overlap" (SB line 179), with no ruling on touching.
- **D-I3. Occurrences as inputs.**
  - Design: E2D P3 is phrased with steps (occurrences).
  - Implementation: `before` and `interval` take descriptions only; an occurrence gives None (DYN 393-403).
- **D-I4. Clocks.**
  - Design: V02 §4.5 requires clock alignment for comparisons across clocks, else UNKNOWN.
  - Implementation: `before` has no clock handling (DYN 393-403). Whether accounts on different clocks exist in
    Core 0.4 is not checked here.

### `effects_of`
- **D-F1. `accepted_change` counts a move out of UNKNOWN as a change.**
  - Implementation: DYN 161-162. For initiates, `accepted_change` = before not True and after True; for terminates,
    before True and after not True. "Not True" includes UNKNOWN and DISPUTED, so UNKNOWN → ASSERTED (DO Q2 line 22,
    part-of bearing-3: "before UNKNOWN/None ... accepted change: True") and ASSERTED → UNKNOWN count as accepted
    changes.
  - Design: under Q-B1.2 (SB lines 70-71), `changes` would call these **judgement** transitions, "never presented as
    physical change". The two readers then disagree about the same state.
  - Whether Q-B1 extends to `effects_of` is not ruled.
- **D-F2. The fixed instants miss delayed effects.**
  - Implementation: the state is sampled at start earliest − 1 µs and at end latest only (DYN 157-159). A delayed
    effect (Q-B1 probe case 6: event 09:50-10:00, state from 10:45) gives `accepted_change: False`, while `changes`
    explains the transition by that event.
  - Design: Q-B1 allows delayed effects (SB line 96, line 133). No design text sets `effects_of`'s instants; INV
    GAP-MULTI-2 records them as implementation choices.
- **D-F3. Which account gives the times.**
  - Implementation: the one returned by `interval` (the lowest-id usable account; D-I1). Its attestation is not
    reported (DYN 148).
  - Design: SB line 180 requires claims' provenance, and D-B-6 requires an accepted account. The timing record is
    not required to be shown, but its choice is unspecified.
- **D-F4. Labels.**
  - Docstring: five claim labels.
  - Design: IBD §2.4's claims vocabulary has ten labels, which `effects_of` uses (IBD line 102).
- **D-F5. No occurrence check.**
  - Implementation: no `occurrence_status` or `applies` for the described occurrence (DYN 143-169).
  - Design: Occ-2 is worded generally (SB line 18), while the LABS-1.011 amendment names `causes_of` only. Whether
    an effect claim of a denied occurrence should be marked as not applying is unruled.
- **D-F6. `t` has two different roles.**
  - Implementation: `t` judges only the claim contents. The states are judged at the event's own times, whatever
    `t` is (DYN 150, 157-159).
  - Design: no text defines `t` for `effects_of` beyond the signature (SB line 200).
- **D-F7. Writer refusals** in `claim_effect` (`kind`, proposition ids) are documented only in code (DYN 102-105).

### Refusals summary
| Refusal | Source | Status |
|---|---|---|
| `explain` refuses unknown role names (`UnknownRoleError`) | R2 lines 50-62; HR line 254 | established |
| `claim_cause` refuses `cause == effect` (writer) | code only, DYN 409-410 | not established |
| `claim_effect` refuses a kind other than initiates/terminates, and use without proposition ids (writer) | code only, DYN 102-105 | not established |
| `causes_of`, `effects_of`, `changes`, `process_steps`, `before`, `interval` | none documented | — |
