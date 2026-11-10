# Core 0.4 Stage A0: groundwork (LABS-1.002 to LABS-1.005)

**Status (2026-11-10): A0.1-A0.3 implemented on `feature/core-0.4-a0`; conditionally approved (LABS-1.003), with the
shelf-dispute correction, additive constraint inheritance, the identity-equivalence correction (LABS-1.004) and the
`holds` functional-dispute correction (F-4, LABS-1.005) applied; performance limits accepted as tracked risks
(LABS-1.005). Not merged into `main`; Stage A not started.**
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
| F-4 | `holds` did not report functional conflicts (each of two incompatible facts was ASSERTED) | **fixed (LABS-1.005)**, see below |
| F-5 | Core 0.3 defect: the selective path ignored `same-as` links of value players (see Identity equivalence) | **fixed (LABS-1.004)**; the `xfail` marker is removed |

## `holds` and functional conflicts (LABS-1.005; was F-4)
**Ruling.** When accepted contents give incompatible values to one functional slot, the judgement represents the
dispute consistently: `value_at` reports DISPUTED, and `holds` reports DISPUTED for each content taking part in the
unresolved conflict. Evidence for both sides stays available; nothing is rejected or deleted; the sources'
attestations are unchanged, and the dispute is the perspective's judgement.

**Consistency check (before implementing).** v0.2 §5.6 defines DISPUTED as "answers of equal standing for *p* disagree
at t (5.3)", and §5.3 lists functional conflict among the ways answers disagree; `holds` already returned DISPUTED for
polarity conflicts (documented in the Core 0.3 README). No Core 0.3 test or document gave `holds` a different meaning;
the only test asserting the old behaviour was A0.3's own record of F-4. No conflict.

**Correction.** One functional-dispute check, `_conflicts`, returns which holding contents conflict with which (same
constraint key players, different value players; canonical under identity; every applicable constraint, inherited
ones included). `value_at`/`value_of` use it as before; `holds` now applies it to the contents it already judges
(the peers sharing the slot key), so it needs no extra query. A content that holds but conflicts is answered
`Answer(DISPUTED, holds=None, support=<its own attestations>, conflicts=<the conflicting attestations>, evidence=<both>)`.
`conflicts` is a new optional `Answer` field (default empty), so every other answer is unchanged.

**Unchanged.** A content that does not hold keeps its answer (e.g. INFERRED false by exclusivity); a third value
while the slot is disputed stays UNKNOWN, as in Core 0.3, because no settled value excludes it. Unreviewed rival
claims do not create a dispute until the perspective accepts them.

**Tests** (`tests/test_f_a0_holds.py`, each question on both paths, whole answers compared): incompatible values
(both DISPUTED, support and conflicts split, evidence for both, history intact); compatible facts sharing a
non-functional role (ASSERTED); values made equivalent by an accepted `same-as` (ASSERTED); perspective-specific
acceptance and rejection; history and knowledge time; hypothetical snapshots and variant overrides; the inherited
located-at constraint on `docked-at`. All 7 failed before the correction.

**Performance.** Same number of queries per `holds` call before and after (24.48 on a 30-object world with some
conflicts, 120 questions, two alternating runs each); median 35.2 / 31.8 ms before, 33.2 / 31.4 ms after.

## Identity equivalence of answer values (LABS-1.004; was F-5)
**Defect (Core 0.3, reproduced on `main`).** Answers group contents by the canonical player of every role under the
perspective's identity. Full load builds identity from every `same-as` link visible in the world; the selective path
loaded only links reachable from the question's subject. So when an answer's *value* players were linked (two names
of one place), full load saw one value (ASSERTED) and the selective path two (DISPUTED): the two paths disagreed.

**Minimum extra information.** Only the links reachable from the other players of the candidate attestations the
selective path already loaded. Links that touch none of them cannot change how those players compare.

**Correction (no architectural change).** After the candidates load, one targeted query (`_linked_ids`) asks which of
their other players appear in any stored `same-as` content (any world, 50 ids per query): a necessary condition for
being co-referring. Only for those players, the same world-, knowledge-time- and perspective-aware loading used for
subjects runs (`_identity_links`, transitively). Applied in `_view` (value_at, value_of, exists, facts_about, history,
events) and `holds`. Nothing is merged in storage; identity stays per perspective, knowledge time and world snapshot.

**Tests** (`tests/test_f_a0_identity.py`, every answer compared whole on both paths): accepted equivalence; genuinely
different values stay DISPUTED; unaccepted and rejected links do not merge; perspective-specific links; knowledge-time
boundaries (before recording, accepted, later rejected); hypothetical snapshots (a base link recorded after the branch
is not inherited) and identity stipulated in a variant; several names and a transitive chain through an id that no
answer mentions; subject identity together with value identity. 8 of these fail on the code before the fix.

**Cost, isolated** (`scripts/measure_identity_cost.py`: one database, the same 60 questions, the correction switched on
and off in alternating rounds; records `identity-cost-*.json`):
| World | Median per question, on / off | TypeQL queries per question, on / off | Answers differing from full load, on / off |
|---|---|---|---|
| no `same-as` links | 18.66 / 17.57 ms (+6 %) | 11.73 / 10.72 (+1) | 0 / 0 |
| 10 linked places; half the questions about objects with an account under an alias | 34.98 / 18.86 ms (+85 %) | 21.45 / 10.80 (+10.6) | **0 / 32** |

The cost is one query per selective question when nothing is linked, and grows with the number of linked value
players, because each one's links load through `_load` (one subject at a time, per world level). A batched
multi-subject load would reduce it; that is an optimisation of `_load`, not done here.

## Unresolved decisions (plan 9.7), status after LABS-1.004
| # | Question | Status |
|---|---|---|
| U-1 | result record vs future observation type | open (Stage C) |
| U-2 | status of a lifted causal answer | open (Stage B) |
| U-3 | rounding of continuous parameters in keys | open (Stage A); keys still use 12 significant digits |
| U-4 | where profile metadata lives | constraint declarations stored as data in TypeDB; packaging open (Stage D) |
| U-5 | constraint inheritance | **ruled and implemented:** additive, never weakened implicitly |

## Performance (unchanged Core 0.3 workload; plan 9.4)
Workload: the Core 0.3 benchmark (200 objects, 30 places, 1,000 moves, 60 questions, seed 11) through
`scripts/bench_instrumented.py`; Python 3.13.17; TypeDB 3.14.1 in Docker on one laptop. Every comparison is against
unchanged Core 0.3 (`main`, b64f635) in the same session, runs alternating. **The thresholds are not reported as met:**
the differences are of the same size as the run-to-run variation, so the size of any regression is not established.

### Controlled comparison (LABS-1.003; A0 at e633602, before the identity fix)
One discarded warm-up run, then 10 runs in the order M A A M M A A M M A. Records: [bench-a0-controlled/](bench-a0-controlled/).
| Run | Impl. | Selective median / p95 (ms) | Full median (ms) | Ingest (s) | Move median / p95 (ms) | DB (MB) |
|---|---|---|---|---|---|---|
| 1 | Core 0.3 | 61.6 / 100.7 | 4,119.5 | 79.7 | 62.2 / 117.2 | 12.38 |
| 2 | A0 | 58.1 / 79.1 | 3,996.0 | 74.0 | 59.3 / 105.6 | 12.69 |
| 3 | A0 | 60.2 / 101.1 | 4,121.0 | 67.9 | 51.2 / 93.2 | 12.68 |
| 4 | Core 0.3 | 57.3 / 104.6 | 4,139.3 | 76.6 | 60.1 / 117.2 | 12.38 |
| 5 | Core 0.3 | 53.7 / 76.9 | 4,015.8 | 67.2 | 52.0 / 99.1 | 12.37 |
| 6 | A0 | 59.3 / 133.6 | 4,364.0 | 87.0 | 65.3 / 139.0 | 12.70 |
| 7 | A0 | 53.1 / 85.1 | 4,190.5 | 85.4 | 62.9 / 122.7 | 12.69 |
| 8 | Core 0.3 | 52.0 / 79.0 | 4,115.7 | 71.0 | 54.5 / 105.9 | 12.39 |
| 9 | Core 0.3 | 55.3 / 90.2 | 4,516.1 | 67.6 | 51.2 / 101.1 | 12.39 |
| 10 | A0 | 68.2 / 107.0 | 4,108.3 | 79.3 | 57.8 / 123.2 | 12.71 |

| Measure (five runs each) | Core 0.3 median (min-max, CV) | A0 median (min-max, CV) | A0 vs Core 0.3 | Threshold |
|---|---|---|---|---|
| selective median | 55.3 ms (52.0-61.6, 6.6 %) | 59.3 ms (53.1-68.2, 9.1 %) | +7.2 % | +10 % |
| selective p95 | 90.2 ms (76.9-104.6, 13.8 %) | 101.1 ms (79.1-133.6, 21.1 %) | +12.1 % | +15 % |
| full-load median | 4,119.5 ms (4,015.8-4,516.1, 4.6 %) | 4,121.0 ms (3,996.0-4,364.0, 3.3 %) | 0.0 % | +10 % |
| ingestion | 71.0 s (67.2-79.7, 7.7 %) | 79.3 s (67.9-87.0, 10.1 %) | **+11.7 %** | +10 % |
| database size | 12.38 MB | 12.69 MB | +2.5 % | +5 % |
| selective: queries / attestations per question | 13.5 / 7.1 in every run | 13.5 / 7.1 in every run | equal | — |
| full: queries / attestations per question | 9.4 / 3,283.9 in every run | 9.4 / 3,283.9 in every run | equal | — |
| answers selective = full | 5 of 5 | 5 of 5 | — | identical |

**Write path** (`scripts/profile_write_path.py`, 300 timed moves, four alternating runs, `wprof*.json`): 25.33 queries
per move for both; every query kind's mean time equal within noise; move median 42.9 / 41.5 ms (Core 0.3) and
44.7 / 41.4 ms (A0). The only structurally different query is the proposition insert, which also writes the `wm-id`
key: 0.66 → 0.69-0.75 ms. The +11.7 % ingestion median is not reproduced at the level of single moves.

### Confirmation after the identity fix (LABS-1.004; A0 at 9d33e7a)
Six runs, order A M M A A M. Records: [bench-a0-confirm/](bench-a0-confirm/).
| Run | Impl. | Selective median / p95 (ms) | Full median (ms) | Ingest (s) | DB (MB) |
|---|---|---|---|---|---|
| 1 | A0 | 63.4 / 80.7 | 4,080.8 | 81.5 | 12.69 |
| 2 | Core 0.3 | 58.7 / 92.1 | 4,158.7 | 77.0 | 12.38 |
| 3 | Core 0.3 | 62.0 / 207.2 | 4,631.3 | 78.6 | 12.38 |
| 4 | A0 | 64.9 / 120.7 | 4,165.7 | 92.1 | 12.70 |
| 5 | A0 | 55.0 / 106.2 | 4,041.6 | 82.4 | 12.69 |
| 6 | Core 0.3 | 55.0 / 83.9 | 3,948.4 | 74.3 | 12.38 |

Medians of three, A0 vs Core 0.3: selective median 63.4 vs 58.7 ms (+8.0 %), p95 106.2 vs 92.1 ms (**+15.3 %**),
full load −1.9 %, ingestion 82.4 vs 77.0 s (+7.0 %), database +2.5 %; answers identical in all six runs. The
benchmark's query counter (13.5 per question for both) counts only attestation-loading queries, so it does not show
the identity fix's extra pre-filter query; the isolated measurement above does (+1 query, about +1 ms, without links).

### What is and is not established
- Established: identical answers on both paths in every run; identical query and record counts per question (apart
  from the identity pre-filter); database +2.5 %; no extra queries on the write path.
- Not established: the size of any time regression. Across rounds the selective median was +7 to +13 %, p95 +12 to
  +25 %, ingestion +7 to +19 %, while unchanged Core 0.3's own runs vary by up to 22 % (p95 up to 2.5x).
- Known, structural costs: a second key on every proposition (one extra attribute written and indexed per new
  proposition), memoised Python lattice lookups, and the identity pre-filter (one query per selective question).
