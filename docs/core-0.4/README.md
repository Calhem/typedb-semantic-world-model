# Core 0.4 Stage A0: groundwork (LABS-1.002, LABS-1.003)

**Status (2026-11-10): A0.1-A0.3 implemented on `feature/core-0.4-a0`; conditionally approved (LABS-1.003), with the
shelf-dispute correction and additive constraint inheritance applied. Not merged into `main`; Stage A not started.**
Baseline: Core 0.3 (`b64f635`). Plan: [core-0.4-plan.md](../plans/core-0.4-plan.md) (LABS-1.001, refined under
LABS-1.002 in section 9). Stage A0 adds no new world concepts: it removes three code constraints that would block
Stages A-D (plan section 0). Stages A-D are not started.

## What A0 adds
| Increment | What | Where |
|---|---|---|
| A0.1 proposition ids | every proposition owns an immutable `wm-id` key: `p:` + 24 hex characters (96 bits) of the SHA-256 of its canonical key. Same content, same id, in every database. A collision (two keys, one id) raises `PropositionIdCollision`; nothing is merged. Ids of that form are reserved for propositions. | `schema/core/core-0.4-a0.tql`, `keys.proposition_id`, `WorldModel.proposition_id`, `upgrade_to_a0` |
| A0.2 type and role lattice | supertypes and parent roles are read from the schema (`sub!` queries, cached). A record keeps its concrete type (`ctype`, e.g. `docked-at`) and stored role names (`concrete_roles`); answers use its core type (`kind`) and core role names (`pickup:picker` answers as `actor`). Questions by a type include its subtypes. | `WorldModel.ancestors`, `is_a`, `core_type`, `core_role`; `AttestationRecord.kind`, `concrete_roles` |
| A0.3 functional constraints as data | "one value at a time" is declared per proposition type in TypeDB (`functional-slot`: key roles, value role), not in a Python constant; a constraint may have several key roles and a type several constraints. Subtypes inherit every ancestor constraint and their own declarations add to them (LABS-1.003). | `schema/core/core-0.4-a0-slots.tql`, `declare_slot`, `slots`, `_constraints`, `value_of` |

All three are one schema module, `core-0.4-a0` (version `0.4.0-a0`), installed by default after `core` 0.3.0.

```python
wm = WorldModel.create("demo", replace=True)                 # core 0.3.0 + core-0.4-a0
wm.slots()                                                     # {'located-at': [(('located',), 'place')]}
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

## Functional constraints: semantics (U-5, ruled in LABS-1.003)
- A **functional constraint** on a proposition type says: at most one value-role player holds at a time for each
  combination of key-role players (located-at: one place per located thing).
- **Inheritance is additive.** A subtype inherits every constraint of its ancestors; its own declarations add
  constraints. Nothing replaces or weakens an inherited constraint, and the API offers no way to: weakening a parent
  constraint needs an architectural proposal. Declaring a constraint that already applies is a no-op.
- **Compatibility check (done before implementing; no conflict found).** TypeDB gives each type one supertype, so the
  constraints that apply to a type form one chain (`_constraints`, root first). Every instance of a subtype is an
  instance of its ancestors (`isa` is polymorphic), so an ancestor's constraint must keep applying to it: additive is
  the reading consistent with the hierarchy. Constraints name core roles, which every subtype keeps, possibly under a
  specialised name. v0.2 keeps functional slots as profile metadata (T7) and says nothing about replacement.
- **Scope.** A constraint declared on a subtype applies to that subtype's content only: "one boat per berth" on
  `berthed-at` does not make two things `located-at` one pier a conflict.
- **What uses them.** Exclusivity across worlds (a variant's value for a slot overrides inherited values), the
  functional-conflict check in `value_at`/`value_of`, and `holds` (exclusivity and the inferred "false" when another
  value holds) all use every applicable constraint. `value_at` without `key_role` needs exactly one one-role
  constraint; otherwise the question must say which.

## The shelf dispute (LABS-1.003; was F-2)
Cases, with the v0.2 rule that decides them (§5.3 rule 2: a functional conflict is "incompatible values for a
single-valued slot"), all in `tests/test_f_a0_shelf.py`:
| Case | Answer | Core 0.3 (main) | A0 after the fix |
|---|---|---|---|
| two objects on one shelf ("what is on the shelf?") | compatible: both, ASSERTED | DISPUTED (defect) | ASSERTED |
| one object in two places at once | DISPUTED | DISPUTED | DISPUTED |
| one object moving over time | one place at each time; history has both | correct | correct |
| two place names from different frames, at once | DISPUTED: Core 0.3 places carry no frame, so they are two places unless identity says otherwise; positions in frames are Stage A (`positioned-in`, `frame-transform`), where different frames without a transform are *incomparable* | DISPUTED | DISPUTED |
| a second object on the shelf in a variant | compatible | DISPUTED (defect) | ASSERTED |

**Root cause: answer aggregation, not the constraint's key.** Exclusivity in `_judge` was keyed correctly by the slot's
key role. `value_at` instead counted distinct values of whatever role was asked and called more than one a dispute
whenever the type had a slot. **Fix:** an answer is DISPUTED for a functional reason only when two holding contents
give different value players to the same constraint key (`_functional_conflict`), with players canonical under the
perspective's identity. This also replaced A0.3's composite-slot special case (former V-4). Perspective, temporal,
polarity and variant rules are unchanged; the 78 Core 0.3 tests pass.

## Deviations and findings
| # | Item | Status |
|---|---|---|
| V-1 | Two Core 0.3 test assertions updated to the installed module list | approved (LABS-1.003) |
| V-2 | Performance: thresholds not demonstrated | see Performance; not reported as met |
| F-1 | Defect fixed in A0.1: disjunctions telling propositions from events by owning `wm-id` matched propositions twice (13 of 78 tests failed); each branch now names its type | fixed |
| F-2 | Shelf dispute (Core 0.3 defect) | fixed (above) |
| F-3 | Subtype constraint replacing the inherited one | superseded: additive semantics (above) |
| F-4 | `holds` judges one content at a time: with two conflicting located-at facts at the same depth, each one `holds` (ASSERTED) and only `value_at` shows the DISPUTED conflict. Core 0.3 behaviour; v0.2 §5.3 lists functional conflict under dispute detection, which suggests `holds` should report DISPUTED too | **open: needs a ruling** (changes `holds` answers) |
| F-5 | **Core 0.3 defect, not fixed:** with an accepted `same-as` between two value players (e.g. two names of one place), full load treats them as one value (ASSERTED) but the selective path loads identity only for the subject and reports two values (DISPUTED). Selective/full equivalence is broken in this case on `main` too. Recorded as a strict `xfail` test. A fix needs identity for value players on the selective path: about one extra identity lookup per question | **open: needs approval** (costs selective-path queries) |

## Unresolved decisions (plan 9.7), status after LABS-1.003
| # | Question | Status |
|---|---|---|
| U-1 | result record vs future observation type | open (Stage C) |
| U-2 | status of a lifted causal answer | open (Stage B) |
| U-3 | rounding of continuous parameters in keys | open (Stage A); keys still use 12 significant digits |
| U-4 | where profile metadata lives | constraint declarations stored as data in TypeDB; packaging open (Stage D) |
| U-5 | constraint inheritance | **ruled and implemented:** additive, never weakened implicitly |

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
