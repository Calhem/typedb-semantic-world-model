# Core 0.4 Stage A0: groundwork (LABS-1.002)

**Status (2026-11-10): A0.1-A0.3 implemented on `feature/core-0.4-a0`, awaiting review. Not merged into `main`.**
Baseline: Core 0.3 (`b64f635`). Plan: [core-0.4-plan.md](../plans/core-0.4-plan.md) (LABS-1.001, refined under
LABS-1.002 in section 9). Stage A0 adds no new world concepts: it removes three code constraints that would block
Stages A-D (plan section 0). Stages A-D are not started.

## What A0 adds
| Increment | What | Where |
|---|---|---|
| A0.1 proposition ids | every proposition owns an immutable `wm-id` key: `p:` + 24 hex characters (96 bits) of the SHA-256 of its canonical key. Same content, same id, in every database. A collision (two keys, one id) raises `PropositionIdCollision`; nothing is merged. Ids of that form are reserved for propositions. | `schema/core/core-0.4-a0.tql`, `keys.proposition_id`, `WorldModel.proposition_id`, `upgrade_to_a0` |
| A0.2 type and role lattice | supertypes and parent roles are read from the schema (`sub!` queries, cached). A record keeps its concrete type (`ctype`, e.g. `docked-at`) and stored role names (`concrete_roles`); answers use its core type (`kind`) and core role names (`pickup:picker` answers as `actor`). Questions by a type include its subtypes. | `WorldModel.ancestors`, `is_a`, `core_type`, `core_role`; `AttestationRecord.kind`, `concrete_roles` |
| A0.3 functional slots as data | "one value at a time" is declared per proposition type in TypeDB (`functional-slot`: key roles, value role), not in a Python constant; a slot may have several key roles. Subtypes inherit the nearest declaration; their own declaration replaces it. | `schema/core/core-0.4-a0-slots.tql`, `declare_slot`, `slots`, `value_of` |

All three are one schema module, `core-0.4-a0` (version `0.4.0-a0`), installed by default after `core` 0.3.0.

```python
wm = WorldModel.create("demo", replace=True)                 # core 0.3.0 + core-0.4-a0
wm.slots()                                                     # {'located-at': (('located',), 'place')}
key = wm.proposition("located-at", {"located": box, "place": shelf})
wm.proposition_id(key)                                         # 'p:…' (24 hex), = worldmodel.proposition_id(key)
wm.install_module("my-profile", files=["/abs/path/profile.tql"], version="1")
wm.declare_slot("seat-assignment", ["venue", "seat"], "occupant")
wm.value_of(w, "seat-assignment", {"venue": "hall", "seat": "A1"}, t)
wm.record_event(w, {"picker": alice, "picked": box}, start=t, type="pickup")   # a profile event subtype
```

Upgrading a Core 0.3 database in place: `WorldModel.open(name).upgrade_to_a0()` (three steps, because TypeDB rejects
adding `@key` while propositions lack the attribute: own the attribute, write the ids, add the key; then the module
is recorded and the located-at slot declared). Tested: answers are unchanged after the upgrade.

## Writing and asking with profile types
- **Write** a profile relation with its own role names: `pickup (picker, picked)`. TypeDB rejects the parent's names
  (`actor`) for a specialised relation (`INF11`, probe A0-R5).
- **Ask** with core role names: records, `value_at`, `holds` and `events()` key roles by core role (`actor`), and keep
  the stored names in `concrete_roles`. A profile's own new roles (no core parent) keep their names.
- `content()` adds `core_type` and `core_roles` only for profile types, so its Core 0.3 output is unchanged.

## Deviations from the plan and from "unchanged"
| # | Deviation | Why | Review |
|---|---|---|---|
| V-1 | Two Core 0.3 test assertions changed: `wm.modules() == {"core": "0.3.0"}` now also expects `"core-0.4-a0": "0.4.0-a0"` (`tests/test_a_content.py:12`, `tests/test_m1_core.py:30`) | the registry correctly lists the new module; every other Core 0.3 test is unchanged and passes. The plan said the 78 tests keep passing "unchanged". Alternative: not install A0 by default, which would leave A0 out of the regression run | please confirm |
| V-2 | Thresholds applied to a same-session Core 0.3 baseline (median of three alternating runs), not the absolute figures in plan 9.4: unchanged Core 0.3 itself exceeded those today | machine drift and a run-order effect; see Performance. Selective p95 and ingestion are over threshold even on this basis | please rule on the method and on the result |
| V-3 | Slot inheritance and override (U-5) implemented as the plan's stated default; its consequences are now visible (below) | needed for A0.2 subtypes to behave as their core types | U-5 stays open |
| V-4 | Composite slots count several values as a dispute only when the question names the whole key; one-role slots keep the Core 0.3 rule exactly | composite slots are new; the Core 0.3 rule (any role asked) is kept to avoid changing dispute semantics | see F-2 |

## Findings for review (not changed by A0)
- **F-1, defect fixed in A0.1 (exposed by the regression suite).** Disjunctions that told propositions from events by
  "owns `wm-id`" matched propositions twice once propositions owned `wm-id` (13 of 78 tests failed). Each branch now
  names its type. Recorded as a best practice.
- **F-2, Core 0.3 behaviour kept, candidate defect.** For a type with a slot, `value_at` reports DISPUTED whenever
  more than one value is found, whichever role is asked: "what is on the shelf?" with two boxes on it is DISPUTED.
  Reproduced on `main` (b64f635) and on A0. Suggested correction (not applied): count several values as a dispute
  only when the asked key role is the slot's key, as A0.3 already does for composite slots.
- **F-3, U-5 consequence.** When a subtype declares its own slot (e.g. one boat per berth), its facts stop competing
  in the parent's slot for exclusivity, but they are still instances of the parent, so asking the parent question
  ("where is the boat?") still sees them, and two places are DISPUTED. Whether a subtype's declaration should
  replace or add to the inherited slot is the open U-5 question.
- **F-4.** `holds` judges one content at a time: with two conflicting located-at facts, each one `holds` (ASSERTED),
  and `value_at` shows the conflict. Unchanged from Core 0.3.

## Unresolved decisions (plan 9.7), status after A0
| # | Question | After A0 |
|---|---|---|
| U-1 | result record vs future observation type | open (Stage C) |
| U-2 | status of a lifted causal answer | open (Stage B) |
| U-3 | rounding of continuous parameters in keys | open (Stage A); keys still use 12 significant digits |
| U-4 | where profile metadata lives | A0.3 stores slot declarations as data in TypeDB, as planned; packaging open (Stage D) |
| U-5 | slot inheritance vs a subtype's own slot | default implemented (inherit; a declaration replaces); F-3 shows the trade-off; open |

## Performance (unchanged Core 0.3 workload; plan 9.4)
Workload: the Core 0.3 benchmark (200 objects, 30 places, 1,000 moves, 60 questions, seed 11), through
`scripts/bench_instrumented.py`, Python 3.13.17, TypeDB 3.14.1 in Docker on one laptop. Because the absolute
baseline (recorded on another day) was exceeded by unchanged Core 0.3 itself, A0 is compared with Core 0.3 (`main`,
b64f635) measured in the same session, three runs each in alternating order. Medians of three. Records:
[bench-a0-final/](bench-a0-final/).

| Measure | Core 0.3, same session | A0 round 1 (f1424b8) | A0 round 2 (558ad5c) | Threshold | Round 2 vs Core 0.3 |
|---|---|---|---|---|---|
| selective question, median | 47.0 · 55.6 ms | 52.0 ms (+10.6 %) | 62.6 ms | +10 % | **+12.6 %, not met** |
| selective question, p95 | 66.9 · 97.0 ms | 81.2 ms (+21 %) | 121.6 ms | +15 % | **+25 %, not met** |
| full-load question, median | 3,763 · 4,004 ms | 3,828 ms (+1.7 %) | 4,097 ms | +10 % | +2.3 %, met |
| ingestion, 1,000 moves | 64.2 · 73.4 s | 76.4 s (+19 %) | 83.4 s | +10 % | **+13.6 %, not met** |
| database size | 12.37 · 12.38 MB | 12.69 MB | 12.69 MB | +5 % | +2.5 %, met |
| answers selective = full | identical | identical | identical | identical | met (12 of 12 runs) |

Core 0.3 column: round 1 · round 2 medians. How to read this:
- **The noise is as large as the differences.** Core 0.3's own runs ranged from 46.4 to 60.8 ms (round 1) and 53.9 to
  65.8 ms (round 2); ingestion from 57.3 to 81.6 s. Whichever implementation ran first in a session was slower.
- **The question path issues the same queries.** A per-kind profile (`profile-*.json`) shows identical query kinds,
  counts and row counts per question for A0 and Core 0.3; in that pair A0 was faster (54.5 vs 58.2 ms). A0 changes
  no question-path query for a typed question; it adds Python lookups (memoised) and a second key on propositions.
- **The write path does more work, by design:** each new proposition stores and indexes a second key (`wm-id`). The
  first A0 version also ran a separate collision query; 558ad5c folds it into one lookup.
- **Conclusion: not demonstrated within thresholds.** The selective p95 and ingestion are over threshold in both
  rounds, the selective median in both rounds by a margin smaller than the noise. A quieter measurement (machine
  idle, more runs) is needed before Stage A to tell a real cost from drift.
