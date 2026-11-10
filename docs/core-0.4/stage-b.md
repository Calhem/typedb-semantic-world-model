# Core 0.4 Stage B: dynamics and causality (LABS-1.010)

**Status (2026-11-10): B1-B3 implemented on `feature/core-0.4-b-dynamics`, awaiting review. Not merged; Stage C not
started.** Base: `main` at 322c5c7 (Stages A0-A2 merged). Plan: [core-0.4-plan.md](../plans/core-0.4-plan.md), Stage B
and 9.3. Ontology: World Ontology v0.2 §3.2 (frozen).

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

## Remaining limitations
- **No causal chains.** There is no chain query yet; the plan's "a chain query lists asserted links" is not
  implemented. `explain` stops at the causes of the initiating event.
- **Processes are not modelled as ongoing.** A process is a classification and a part-of structure. There is no
  persistence policy and no "homogeneous, ongoing" check (v0.2 C9).
- **Participant roles are single-valued per description,** one patient and so on (Core 0.3 `@card`). The occurrence
  view lists every participant per description without a dispute label (D9 stays open).
- **The new questions are slow:** hundreds of milliseconds, as measured above.
- **Out of scope:** no prediction, simulation, automatic causal inference, measurement ontology, agency or
  capabilities, domain extensions or frontend (by design).
