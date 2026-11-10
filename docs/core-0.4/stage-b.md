# Core 0.4 Stage B: dynamics and causality (LABS-1.010, LABS-1.011)

**Status (2026-11-10): B1-B3 implemented; LABS-1.011 semantic verification done; merged into `main` (LABS-1.011).
Stage C not started.** Base: `main` at 322c5c7 (Stages A0-A2 merged). Plan: [core-0.4-plan.md](../plans/core-0.4-plan.md), Stage B
and 9.3. Ontology: World Ontology v0.2 §3.2 (frozen).

## Decision register (LABS-1.014)
Earlier sections keep the history; this register is the current state. Approved decisions are not reopened without a
demonstrated conflict.

### Approved decisions
| # | Decision | Approved |
|---|---|---|
| B-arch | Stage B architecture: module `core-0.4-b` (`causes` between descriptions and occurrences), processes and actions as classifications, process membership as part-of between occurrences, `dynamics.py` read and write operations on the existing attestation model | LABS-1.011 |
| F-B1 | Description-level and occurrence-level claims are distinct contents and never dispute each other automatically | **settled**, LABS-1.012 |
| U-2 | A lifted claim keeps its original attestation status, is identified as lifted through an accepted describes link, and applies only if the occurrences' own existence judgement allows; a denied occurrence never gets an applicable explanation through a lifted description claim | **settled**, LABS-1.012 |
| Occ-1 | An occurrence's existence is judged only from attestations of its own existence; `exists()` and `occurrence_status()` share that judgement; other things keep the Core 0.3 participation rule | LABS-1.012 |
| Occ-2 | An accepted account of a denied occurrence stays visible as its source's account; claims involving a denied occurrence do not apply (`applies: false`) | LABS-1.011 |
| Perf-1 | World-wide event and describes loads are made once per question (per-question memo; no cache across questions) | LABS-1.012 |

Implemented within the approved architecture and recorded for review, but not ruled on individually:
- **D-B-1:** effects are written by `claim_effect` / `account`; `record_event` is unchanged.
- **D-B-2:** causal and effect claims are timeless contents.
- **D-B-4:** actions are classified without an agent-capacity check.
- **D-B-5:** the condition constraint is declared in the reference world only.
- **D-B-6:** `interval()` uses only accounts the perspective accepts.
- **D-B-7:** the dynamics modules are opt-in.

### Deferred capabilities
- **Causal chain queries.** The plan's "list asserted links along a chain"; `explain` stops one step back.
- **Processes as homogeneous, ongoing happenings,** with persistence policies across gaps (v0.2 C9).
- **Agent capacity for actions** (Stage C).
- **Measurement activities, quantities and units** (Stage C).
- **Single-valued event roles,** with dispute labels on participants (D9).
- **Remaining per-description and identity loads** in `actions_of`, `process_steps` and nested `holds`.

### Unresolved architectural questions
| # | Question | Evidence |
|---|---|---|
| **Q-B1** | The temporal contract of `changes` (LABS-1.014): see below. Needs a ruling on four points before it can be implemented without inventing transition times | `probes/core04_b_changes_contract.py` |
| Q-B2 | `facts_about` (and so `changes`) lists each holding content separately, while `value_at` / `holds` report a functional conflict as DISPUTED. The two read paths disagree when a rival value is accepted (F-4 aligned `holds`, not `facts_about`) | probe case 4 |
| D-A1-1, D-A1-3 | material marking; physical and dynamics modules opt-in | Stage A1 |
| U-3 | rounding of continuous parameters in proposition keys | plan 9.7 |
| Perf-A0 | the A0 performance thresholds are not established (tracked risk) | Core 0.4 README |

### Q-B1: the `changes` temporal contract (probe results)
Requested contract: return state transitions whose effective valid time intersects the requested interval, judged for
the knowledge time, perspective and world. Keep event time, transition valid time, knowledge time and explanations
apart. An event outside the interval may explain a transition inside it, but is never itself an in-period change.

**What `changes` does today.** It samples the judged state at two instants, t1 and t2. Whatever holds at t2 and not
at t1 "began"; the reverse "ended". Every event ever claimed to initiate or terminate the content is attached.

| Case (probe) | Today | Supported by the data model? |
|---|---|---|
| 1. box at a, then b (10:00-11:00), then a again; interval 09:30-12:00 | nothing changed | **yes:** transitions with certain times can be found exactly from the attestations' start and end windows; two-instant sampling misses them (a defect to fix once the contract is ruled) |
| 6. delayed effect: event 09:50-10:00, state from 10:45; interval 10:30-11:00 | "b began", explained by the event | **yes:** the event is provenance, not an in-period change |
| 3. a state with no stated end, not until superseded | never holds (UNKNOWN even at its start) | yes: nothing holds, so there is no transition |
| 2. a move known only within 10:00-10:20; interval 10:15-11:00 | judged a, then UNKNOWN (10:00-10:20), then b | **no:** the transition has a window, not an instant, and may or may not lie in the interval. Needs a rule: "possibly in period" (window intersects) vs "certainly in period" (window inside), reported how |
| 4. a rival claim accepted from 10:00 | "b began"; `value_at` says DISPUTED | **no:** the judged state moves to DISPUTED without any state accepted as beginning or ending. Is that a transition, and which read path defines it (Q-B2)? |
| 2 and 4 together | — | **no:** changes of judged status (to UNKNOWN or DISPUTED) are not accepted beginnings or endings. Whether they count as transitions is undefined |
| 5. box at a begins at 08:00 (no event) and again at 13:00 (ev-move-2); interval 07:00-08:30 | ev-move-2 listed as the explanation of the 08:00 transition | **no:** `initiates` links an event to a *content*, not to one occurrence of that content beginning. Tying events to particular transitions needs a time rule, which delayed effects (case 6) make non-trivial. Example rule: "events that ended at or before the transition and after the content's previous transition". That would be a new inference |

**Decisions requested:**
1. the treatment of uncertain transition windows;
2. whether changes to UNKNOWN or DISPUTED are transitions;
3. which read path defines a transition (Q-B2);
4. the rule, if any, for associating claimed events with particular transitions.

With those ruled, the implementation is a boundary scan over the attestation windows of the subject's contents,
judged at each boundary, which can be added without schema changes.

## Run it
```bash
uv run python -I scripts/show_dynamics.py                       # builds wm-reference-gearbox (all extensions)
uv run pytest -q tests/test_h_b1_events.py tests/test_h_b2_causality.py   # 10 + 8 tests
uv run python -I scripts/measure_physical.py . --extended --dynamics
```
Saved output: [dynamics-output.md](dynamics-output.md). Measurements: [bench-b/](bench-b/).

## B0: architecture review (no foundational change)
What v0.2 and Core 0.3 already had:
- **occurrence:** an `occurrence` particular, an id only (v0.2 §3.2).
- **event description:** `event`, with participant roles actor, patient, instrument, location, origin and
  destination; its interval is on its source's attestation.
- **multiple descriptions:** `describes(description, occurrence)`, a judgement usable per perspective.
- **effects on states:** `initiates(event, proposition)` and `terminates(event, proposition)`, in the Core 0.3 schema
  but never written (deferral D2: the outcome is a proposition, which needed A0.1 ids).
- **process and action:** classifications of events (DR-05).
- **causation:** `causes(cause, effect)`, asserted and never inferred from succession; not yet in the schema.

Smallest extension, all within the frozen distinctions:
- **Schema module `core-0.4-b`:** `causes(cause, effect)`, with event descriptions and occurrences as players.
  Occurrences already play `part-of` (they are particulars), so process membership needs nothing new.
- **`dynamics.py`:** writing helpers and queries built on the existing attestation, acceptance and loading code.
  Nothing new is stored as an answer.

The four distinctions, each kept separate in the data and in every answer:
| Distinction | How it is kept |
|---|---|
| Occurrence vs description | different records (`occurrence` id vs `event` relation); `occurrence()` merges participants per description and source without merging storage; `describes` is judged per perspective |
| Asserted effect vs accepted change | an `initiates`/`terminates` claim is content attested by a source; the change is judged separately from the outcome's own attestations before and after the event (`effects_of`: `claim` vs `state.accepted_change`) |
| Succession vs causation | `before()` compares intervals (certainly before, or None if they overlap); `causes_of` lists only asserted claims; nothing is derived from order or chained |
| Source's account vs perspective's judgement | every claim lists its attestations (attester, polarity, basis, acceptance state); the judgement (accepted, disputed, denied, unreviewed, rejected) is computed per perspective, knowledge time and world |

## Schema and API
`schema/core/core-0.4-b.tql` (module `core-0.4-b`, version 0.4.0-b; installed with `DYNAMICS_MODULES` = the physical
modules plus this one; opt-in, like A1):
```
relation causes sub proposition, relates cause, relates effect;
event plays causes:cause, plays causes:effect;
occurrence plays causes:cause, plays causes:effect;
```
API (`src/worldmodel/dynamics.py`, mixed into `WorldModel`).

Writing, through ordinary attestations:
- `account(world, roles, start, end, kind, occurrence, attester)`: an event description with its interval, kinds and
  describes link.
- `describe_occurrence`.
- `claim_effect(world, event, "initiates"|"terminates", type, roles)`: the outcome is the proposition, by its A0.1 id.
- `claim_cause(world, cause, effect, polarity)`.

Reading:
- `effects_of(world, event, t)`: each claimed effect, the claim's judgement, and the accepted state change.
- `changes(world, subject, t1, t2)`: what began and ended, who states it, and the events claimed for it.
- `causes_of(world, effect, t)`: every causal claim, direct or lifted, with level, judgement and sources.
- `explain(world, type, roles, t)`: the judged state, its accepted initiating events, and their causal claims.
- `process_steps(world, process, t)`, `actions_of(world, agent)`.
- `occurrences_of`, `interval`, `before`, `account_attestations`.

Lifting (plan 9.3): a claim about another description of the same happening, or about the occurrence a description
describes, answers a question only through describes links the perspective accepts. Each such claim is marked
`lifted` and says which link it used.

## The reference world (`extend_dynamics`, `extend_causality` in `src/worldmodel/examples/gearbox.py`)
Times are on 2026-11-02 to 2026-11-05. The gearbox is an invented concept assembly.

**Occurrences:**
- o-inspection;
- o-repair, a process, with five steps: o-disassembly, o-bearing-replacement, o-relubrication, o-reassembly
  (overlapping the relubrication) and o-test-run;
- o-sign-off.

**Descriptions:**
- the inspector's inspection report and sign-off;
- the technician's work log for each repair step and the test run;
- the system's own maintenance record of the replacement, which names a different patient (bearing-1 rather than
  bearing-3).

**States:** the gearbox's condition is one value at a time per (bearer, quality), a constraint declared for this
world.
- operational from 11-02 08:00;
- faulty from the inspection, 11-04 09:30, recorded by the inspector. The inspection is the evidence, and nobody
  claims it as an initiator;
- operational again from the test run, 11-05 16:00, stated by the technician and accepted.

**Effect claims, all by the technician:**
- the replacement initiates part-of(bearing-3, shaft-asm-in) and terminates part-of(bearing-1, shaft-asm-in);
  accepted;
- the replacement initiates low vibration; not accepted, and neither is that state;
- the test run initiates operational and terminates faulty; accepted.

**Causal claims about the successful test run:**
| Claim | Level | Source | Judgement (system) |
|---|---|---|---|
| bearing replacement → test run | occurrence | technician | accepted |
| work-log replacement → test-run description | description, lifted | technician | accepted |
| relubrication → test run | occurrence | inspector asserts, condition monitor denies | disputed (both accepted) |
| reassembly → test run | occurrence | condition monitor | unreviewed |
| inspection → test run | occurrence | apprentice | rejected ("succession is not causation") |

**Hypothetical worlds:**
- *plan-relubricate-only:* relubrication is stipulated as the cause, and the replacement is denied;
- *plan-no-repair:* a knowledge snapshot taken before the repair was recorded.

## Demonstrated results (actual output, `dynamics-output.md`)
| Question | Answer (system perspective) |
|---|---|
| What happened to the gearbox? | inspection (inspector, 11-04 09:00-09:30); repair process 13:00-16:00 with steps disassembly, bearing replacement, relubrication, reassembly, test run (technician); sign-off 16:00 |
| Which component was replaced? | o-bearing-replacement has 2 accepted descriptions, naming bearing-3 (technician's work log) and bearing-1 (maintenance record). Claimed effects: part-of(bearing-3) initiated, accepted change; part-of(bearing-1) terminated, accepted change; low vibration claimed, unreviewed, no accepted change |
| State before and after the repair? | operational (11-03), faulty (from 11-04 09:30, still at 11-05 13:00), operational (from 11-05 16:00). Began: operational (stated by technician, claimed by ev-test-run, accepted); ended: faulty |
| Who performed the actions? | technician: disassembly, replacement, relubrication, reassembly, test run; inspector: inspection |
| What caused it to become operational again? | operational is ASSERTED, initiated by ev-test-run (claim accepted). Its accepted causes: o-bearing-replacement (occurrence level) and the work log's replacement description (description level, lifted via describes) |
| Which explanations are disputed? | relubrication: disputed (inspector asserts, testimony; cm-1 denies, inference; both accepted); reassembly: unreviewed; inspection: rejected. The inspection precedes the test run, but succession was not accepted as causation |
| Perspectives, time, worlds | technician: replacement accepted, relubrication unreviewed. Inspector: relubrication accepted, and no lifted claim (it accepts no describes link). Before the denial was accepted: relubrication accepted. plan-relubricate-only: relubrication accepted [STIPULATED], replacement denied. plan-no-repair: still faulty after the repair time. Inspector's view of the condition after the repair: UNKNOWN (it accepted none of the technician's statements) |

Part 2 of the output lists raw TypeQL over the stored records (not judged):
- event descriptions naming the gearbox, with role labels;
- describes records;
- effect claims with the outcome's canonical key;
- causal claim records with polarity, basis and the acceptance verdicts, through a `fetch` sub-query;
- process membership.

## Tests
`tests/test_h_b1_events.py` (10):
- occurrence vs descriptions, and the perspective-dependent describes link;
- claimed vs accepted effects, including the technician's own view of the vibration claim;
- a recorded state with no initiating event;
- what changed, when and by whom;
- order and overlap;
- knowledge time;
- perspectives;
- a knowledge snapshot without the repair;
- selective/full equivalence;
- `record_event` unchanged.

`tests/test_h_b2_causality.py` (8):
- process membership, order and overlap;
- actions and participant roles;
- causal judgements: nothing derived, exactly the 6 causal contents written;
- lifting needs accepted describes links;
- perspectives and knowledge time;
- the hypothetical account and its snapshot;
- explain;
- selective/full equivalence.

Full suite: 199 passed, twice on each path. Only the intentional `wm-reference-gearbox` database remains.

## Performance against A2 (`bench-b/`, three alternating runs each)
**The same A2 world, A2 code (`main` 322c5c7) vs Stage B code.** Identical query counts for every question;
latency within noise. Medians of the three run medians:
| Question | A2 | B |
|---|---|---|
| poses | 21.2 ms | 20.7 ms |
| composition | 324 ms | 316 ms |
| contents | 110 ms | 112 ms |
| where(gbx-100, f-workshop) | 56.2 ms | 55.5 ms |
| transform_between | 10.6 ms | 10.6 ms |

Database: 464.0 KB for both. Build: 1.50 s vs 1.49 s.

**The full Stage B world** (A1 + A2 + B1 + B2): 608.3 KB (+31 % over the A2 world, from the added records) and
2.9 s to build. A2 questions run on it with the same query counts, slightly slower with more data (median
`where(gbx-100)` 73.6 ms).

New questions (median of run medians, TypeQL queries):
| Question | Median | Queries |
|---|---|---|
| value_of(condition) | 42.3 ms | 23 |
| causes_of(o-test-run) | 80.7 ms | 54 |
| actions_of(technician) | 126 ms | 61 |
| process_steps(o-repair) | 187 ms | 136 |
| explain(operational) | 213 ms | 149 |
| changes(gbx-100, repair) | 231 ms | 109 |
| effects_of(ev-worklog-replacement) | 359 ms | 197 |

These compose existing judged reads (`holds` before and after each claimed effect, `facts_about`, event loads). They
are not optimised; no optimisation was authorised.

## Decisions and findings for review
| # | Item | Why | Review |
|---|---|---|---|
| D-B-1 | Effects are written by `claim_effect` / `account`, not by `record_event`, which still writes none | closes D2 without changing Core 0.3 writes (the ingestion benchmark and `move` are unchanged) | please confirm |
| D-B-2 | Causal and effect claims are timeless contents (no valid interval), judged by acceptance, polarity, world and knowledge time | causation is about the happenings, whose times are on their descriptions | please confirm |
| D-B-3 (U-2) | A lifted claim keeps its original claim's status and is marked `lifted` with the describes link used | the plan's current lean; U-2 stays open | please rule |
| F-B1 | Description-level and occurrence-level claims are different contents. A denial at one level does not dispute a lifted claim at the other: in plan-relubricate-only the replacement is denied at the occurrence level while the work log's description-level claim is still accepted | lifting is a read-time link, not identity of content; making them dispute would need a rule comparing lifted contents | **needs a ruling** |
| D-B-4 | `actions_of` lists events classified `action` with the agent as actor, without checking the actor's agent capacity | v0.2 defines an action with the capacity, which is Stage C | known gap until Stage C |
| D-B-5 | The condition's "one value at a time" (has-quality: bearer, quality → value) is declared in the reference world, not in the core | a core constraint on has-quality would change Core 0.3 answers for categorical qualities | please confirm, or make it core |
| D-B-6 | `interval()` uses only an account the perspective can use; a change claimed by an unaccepted account has no timing for that perspective | an unaccepted source's times must not judge a change | — |
| D-B-7 | `DYNAMICS_MODULES` is opt-in, like the physical modules (D-A1-3) | keeps Core 0.3 and A0 tests unchanged | with D-A1-3 |

## LABS-1.011: occurrence vs description semantics, and the scope of causal claims
**The gap.** An occurrence's happening was not judged on its own. Core 0.3's generic `exists()` infers existence from
participation in any holding content, so an accepted `describes` link or causal claim "established" an occurrence.
`causes_of` also presented claims about an occurrence someone had denied without saying so.

**The amendment (read-time only; no schema change).** Occurrences are particulars, so the existing
`existence(existent)` proposition already applies to them.
- `occurrence_status(world, occurrence, t)` judges whether the occurrence happened only from attestations of its own
  existence: accepted, denied, disputed, or **not established**. It never uses descriptions, describes links or
  causal claims for this. It lists every description separately, with its source, the perspective's judgement of
  that account (the description's own attestation) and of its describes link.
- `causes_of` adds, to every claim, the status of each occurrence the claim involves, and `applies`: False if any of
  them is denied, None if any is disputed, True otherwise.

**Verified behaviour (`tests/test_h_b3_semantics.py`).**
| Requirement | Result |
|---|---|
| An accepted description does not establish the occurrence | the replacement has two accepted accounts and accepted describes links, and is "not established" until someone attests its existence (the generic `exists()` still infers it; `occurrence_status` does not) |
| A denied occurrence cannot become accepted through a lifted claim | with the test run's existence denied and accepted, the work log's lifted description-level causal claim is still accepted as an account, but `applies: false`, and the occurrence stays denied |
| Conflicting descriptions stay attributable | the replacement's two accounts (bearing-3 by the technician, bearing-1 by the system) are listed apart, with their own sources and judgements, per perspective |
| A description accepted while the occurrence is denied or disputed | reported directly: account "accepted", occurrence "denied" (or "disputed" when existence is both asserted and denied, both accepted; then `applies: null`) |
| Hypothetical overrides | a plan that stipulates the relubrication did not happen gives "denied" in the plan, keeps the inherited account "accepted", and marks the claim not applying there; the base world is unchanged |

**Clarification: lifted claims about a denied occurrence.** They remain visible, as the source's account. A source
did claim that the happenings, as described, stood in a causal relation, and that record and its judgement are
preserved. They are marked `applies: false`, so they never answer what caused the denied happening. The same holds
for direct occurrence-level claims involving a denied occurrence.

**Scope of causal claims.** No temporal fields were needed: a causal claim names particular occurrences or
descriptions.
- **Two similar repairs.** A second repair on 11-20 has the same kinds, actor and tools as the first, but its own
  occurrences and descriptions. Its causal claim is not among the first test run's causes, and the reverse holds.
- **Over time and by perspective.** The second claim is unreviewed before its acceptance was recorded and accepted
  after. The inspector's denial of it is its own view; the system still accepts it, and the first repair is
  unaffected.
- **Snapshots.** A plan branched before a later claim was recorded does not see it.
- **Descriptions of one occurrence.**
  - A claim about the test-run description lifts to the occurrence.
  - The occurrence-level claim lifts down to the QA log, which is a second description of the same test run.
  - A claim about a *sibling* description is not transferred to the QA log. That would take two hops, which the plan
    does not allow.

**Performance scaling** (`scripts/measure_dynamics_scaling.py`, `dynamics-scaling.json`): the reference world with
0 / 4 / 16 / 64 extra repair cycles, questions about the first repair, median of five.
| Size: events / propositions / attestations | 12 / 141 / 163 | 20 / 173 / 203 | 44 / 269 / 323 | 140 / 653 / 803 |
|---|---|---|---|---|
| effects_of: ms, queries, records | 286, 197, 52 | 304, 197, 60 | 342, 197, 84 | 446, 197, 180 |
| causes_of | 450, 238, 124 | 384, 238, 164 | 398, 238, 284 | 518, 238, 764 |
| occurrence_status | 51, 33, 22 | 49, 33, 30 | 69, 33, 54 | 95, 33, 150 |
| value_of(condition) | 47, 23, 6 | 43, 23, 6 | 66, 23, 6 | 50, 23, 6 |
| process_steps | 244, 153, 130 | 344, 185, 210 | 428, 281, 450 | 1,126, 665, 1,410 |
| actions_of | 155, 79, 31 | 250, 151, 63 | 908, 367, 159 | 2,474, 1,231, 543 |
| changes | 240, 95, 107 | 311, 135, 215 | 780, 255, 923 | 3,466, 736, 9,515 |
| explain | 843, 503, 265 | 928, 543, 441 | 1,335, 663, 1,353 | 5,232, 1,144, 10,761 |

**How costs scale:**
- **Constant query count:** `effects_of`, `causes_of`, `occurrence_status` and `value_of`. Records grow, because
  each loads the world's event attestations once or a few times.
- **Queries linear in the actor's events:** `actions_of` (one describes load per description) and `process_steps`.
- **Superlinear:** `changes` and `explain`, wherever many events claim the same outcome. Every test run claims
  "operational", and each claimed event's `interval()` reloads every event attestation of the world.

**Obvious repeated retrieval**, identified but not optimised (no optimisation was authorised):
- `interval()` loads all event attestations per call: 66 of them in one `changes` question at 64 cycles, and 75 in
  `explain`.
- `occurrences_of()` makes one describes load per description: 135 in `actions_of`.
- `explain` computes intervals for every initiating claim before filtering to the events that ended by t.
- Identity (`same-as`) is loaded 10-28 times per question, by the nested `holds` and `_view` calls.

Loading a world's events once per question would remove most of the growth.

## LABS-1.012: settled decisions and consolidation
### Settled architectural decisions
| # | Decision (settled, LABS-1.012) |
|---|---|
| **F-B1** | Description-level and occurrence-level causal claims are distinct contents. They never dispute each other automatically: a denial at one level leaves an accepted claim at the other level accepted. |
| **U-2** | A lifted claim keeps its original attestation status and is identified as lifted (`lifted: true`, `lifted_via` the accepted describes link). Whether it applies is judged against the occurrences' own existence: `applies` is false if any occurrence involved is denied, null if any is disputed. A denied occurrence never gets an applicable causal explanation through a lifted description claim; the claim stays visible as its source's account. |
| **Occurrence existence** | `exists()` and `occurrence_status()` share one judgement. An occurrence is judged only from attestations of its own existence. Participation (accepted descriptions, describes links, causal claims, process membership) never establishes it. Other things keep the Core 0.3 rule that participation implies existence. |

### One existence judgement
- **`exists(world, occurrence, t)`.** An existence judgement gives ASSERTED or STIPULATED (true, or false before the
  occurrence's existence starts or after it ends) or DISPUTED. Without one, the answer is UNKNOWN when records about
  the occurrence are visible, otherwise NOT_YET_KNOWN. It is never INFERRED from participation. Unreviewed existence
  claims are returned as `alternatives`, and the evidence keeps the sources.
- **`occurrence_status`.** It reads its status from that answer (accepted / denied / disputed / not established) and
  includes the answer itself. With `details=True`, the default, it also lists the existence attestations and every
  description, each with its source.
- **What it costs.** The occurrence check is one kind lookup, made only when `exists()` would otherwise infer
  existence from participation. Non-occurrences answer as before.
- **Semantics preserved.** Valid time, knowledge time, perspective and hypothetical worlds work as before
  (`tests/test_h_b4_consolidation.py`).

### Events loaded once per question
`_Memo` is a per-question memo, created inside one read operation and passed down. It is not a cache: it never
outlives the question. It loads the world's event attestations and describes links at most once for that world,
knowledge time and perspective. `changes`, `explain`, `causes_of`, `_events_claiming`, `interval`, `occurrences_of`
and `occurrence_status` use it. No schema change and no change to any answer: a test compares every answer with and
without it, on both paths.

Same-session scaling (`scripts/measure_dynamics_scaling.py`, median of five).
Before = `main` ff4341b (`dynamics-scaling-before-1.012.json`); after = this branch (`dynamics-scaling.json`).
| Extra cycles (events / propositions / attestations) | changes: ms, queries, records | explain: ms, queries, records |
|---|---|---|
| 0 (12 / 141 / 163) | 188 → 188; 95 → 85; 107 → 105 | 690 → 460; 503 → 298; 265 → 107 |
| 4 (20 / 173 / 203) | 297 → 200; 135 → 85; 215 → 129 | 837 → 545; 543 → 298; 441 → 127 |
| 16 (44 / 269 / 323) | 728 → 222; 255 → 85; 923 → 201 | 1,275 → 445; 663 → 298; 1,353 → 187 |
| 64 (140 / 653 / 803) | 3,516 → 476; 736 → 86; 9,515 → 489 | 4,840 → 637; 1,144 → 299; 10,761 → 427 |

**Effect on `changes` and `explain`.** Their query counts are now constant in world size. The remaining growth is
records: the one event load per question returns every event of the world.

**Effect on other questions.**
| Question | Before → after |
|---|---|
| `causes_of` | 238 → 143 queries at every size; 504 → 399 ms at 64 cycles |
| `occurrence_status` | 33 → 48 queries, +15-20 ms: it now reads its status through `exists()` (one judgement) before listing provenance |
| `effects_of`, `process_steps`, `actions_of`, `value_of` | same query counts; latency within noise |

**Not addressed** (outside this increment's scope):
- `actions_of` still makes one describes load per description;
- identity is still loaded several times per question;
- `effects_of` does not use the memo, because it reads one interval.

## Remaining limitations
- **No causal chains.** There is no chain query yet; the plan's "a chain query lists asserted links" is not
  implemented. `explain` stops at the causes of the initiating event.
- **Processes are not modelled as ongoing.** A process is a classification and a part-of structure. There is no
  persistence policy and no "homogeneous, ongoing" check (v0.2 C9).
- **Participant roles are single-valued per description,** one patient and so on (Core 0.3 `@card`). The occurrence
  view lists every participant per description without a dispute label (D9 stays open).
- **Still slow in places.** The dynamics questions take hundreds of milliseconds. `changes` and `explain` no longer
  grow superlinearly (LABS-1.012), but `actions_of` and `process_steps` still grow linearly in queries.
- **`changes` lists every claimed event.** It lists all events claimed to have initiated or terminated a state that
  changed, including events outside the asked period (for example, later test runs). This behaviour was kept
  unchanged and needs a ruling.
- **Out of scope:** no prediction, simulation, automatic causal inference, measurement ontology, agency or
  capabilities, domain extensions or frontend (by design).
