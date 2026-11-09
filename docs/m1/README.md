# Milestone 1: executable foundational core

**Status (2026-11-09): implemented and reviewed. 41 tests pass against TypeDB CE 3.14.1 on both query paths. Core module 0.2.0.**
The architectural review (worlds, existence, query architecture) is [below](#architectural-review-2026-11-09).

## Run it
```bash
docker compose -f environments/compose.yaml up -d typedb      # isolated TypeDB 3.14.1 on 127.0.0.1:1735
uv sync
uv run pytest -q                                               # throwaway wm-test-* databases, deleted afterwards
```

```python
from datetime import datetime, timezone
from worldmodel import WorldModel

t = lambda h, m: datetime(2026, 11, 9, h, m, tzinfo=timezone.utc)
wm = WorldModel.create("demo", replace=True)
w = wm.create_world("warehouse", kind="actual")
box = wm.add_entity("physical-object", "box-17", alt_names=("parcel 17",))
shelf, dock = wm.add_entity("place", "shelf-3"), wm.add_entity("place", "dock")
wm.assert_fact(w, "located-at", {"located": box, "place": shelf}, start=t(10, 0), until_ceased=True)
wm.move(w, box, dock, t(10, 10))
wm.value_at(w, "located-at", box, t(10, 5))    # Answer(status=ASSERTED, values=(shelf,), ...)
wm.value_at(w, "located-at", box, t(10, 15))   # ASSERTED, (dock,)
```

## What exists
| Area | Implemented |
|---|---|
| **Things** | `referent` (abstract) with robust coarse kinds `physical-object`, `agent`, `place`, `concept`; names and alternative names; lookup returns every match |
| **Relationships** | abstract `claim` relation; core claim types `located-at`, `part-of`, `member-of`, `depends-on`, `classified-as`, `has-state`, `same-as` |
| **Events** | `event` (a claim whose valid time is when it happened) with roles actor, patient, instrument, location, origin, destination; kinds via `classified-as` to a concept; effects linked by `consequence`; `move()` convenience |
| **Time** | valid-time windows on both bounds; `end-basis` stated / unknown / until-ceased; `cessation` records instead of edits; transaction time (`recorded-at`) on claims, cessations, reviews, branchings; every read can ask "as known at" |
| **Worlds** | actual, simulated, hypothetical; a variant inherits a **fixed snapshot** of its base (see the review); its own claims take precedence for functional types; its cessations and reviews never affect the base |
| **Existence** | `existence` claims per world: creation, destruction, uncertain creation time, uncertain existence; INFERRED existence from taking part in a holding fact; `create_thing`, `destroy`, `exists`, `find(world=...)` |
| **Identity** | `same-as` claims (proposed by default); only accepted links merge (transitively); proposed links are never chained; reviews can undo a merge, and earlier transaction times still show it |
| **Decisions** | `review` (accepted, rejected, retracted), made in a world; the latest review by the transaction time decides; rejections win ties |
| **Answers** | `ASSERTED`, `INFERRED` (functional exclusivity), `DISPUTED`, `UNKNOWN`, `NOT_YET_KNOWN`, with supporting claims and proposed alternatives |
| **Modules** | schema files per module, installed in order and recorded (`schema-module`); claim types discovered by introspection |

Code: `schema/core/0001-core.tql` (≈130 lines), `src/worldmodel/` (`model.py`, `semantics.py`, `typeql.py`), tests in
`tests/`.

## Who does what (kept explicit)
| Layer | Responsibilities |
|---|---|
| **Ontology semantics** (documented, Phase 1C) | what a claim, a world, a cessation, an identity link mean |
| **TypeDB enforces** | kinds of thing and which roles they may play (a concept cannot be *located*); every claim, cessation and review belongs to exactly one world (`@card(1..1)`, tested); unique ids; allowed values (`world-kind`, `end-basis`, `verdict`); `same-as` has exactly two players |
| **TypeDB computes** | selection of the claims a question needs (type, role player, world, transaction-time and branch-time limits, valid time: see the review); the recursive functions `parts_in` and `dependencies_in` (world-scoped; time and status ignored) |
| **Python decides** (`semantics.py`) | valid-time truth, status at a transaction time, identity closure, world inheritance and precedence, functional exclusivity, answer statuses, event ordering from windows |

## Assumptions made to keep moving (simplest defensible option)
1. **`alt-name`**, not `alias`: `alias` is a reserved word in TypeQL.
2. **Event roles are plain roles** of `event`. TypeDB 3.14 does not let a relation specialise its own roles, so
   "any participant" is a role variable, and profiles specialise roles (`relates picker as actor`).
3. **Things are world-independent; facts are world-scoped.** A thing that exists only hypothetically is still one
   referent; it simply has facts only in that world.
4. **`until_ceased`** is an author's explicit statement that a fact lasts until a cessation is recorded. It fits
   *defined* worlds (a simulation, a scenario, a design). Without it, a missing end is UNKNOWN. Milestone 2 will
   restrict it for observation-derived facts, where persistence policies take over.
5. **A missing start** means "from the start of the world". **Before its start, a claim is silent**, not false.
6. **Variant precedence** applies to functional types only (one value at a time): the nearest world's claim wins.
   Other inherited facts stay until the variant ceases them.
7. **Functional claim types** (one value at a time) are declared in Python (`FUNCTIONAL`, currently `located-at`).
8. **Identity links are world-scoped claims.** The canonical id of a merged group is its smallest id.
9. **Transaction time** comes from the writer's clock and must not go backwards per `WorldModel` instance.

## Limitations and unsupported behaviour (known)
- Precedence across worlds is by depth only; there is no per-fact "override" record.
- **Not yet:** observations, sources, evidence, provenance chains, OBSERVED and PRESUMED statuses, persistence
  policies, coverage and observed absence, measurements and uncertainty, perspectives and attribution (Milestone 2);
  domain profiles (Milestone 3); synthetic worlds and performance (Milestone 4).
- Clock domains are stored (`clock`) but **not compared**: mixing clocks is not yet refused.
- Adding a thing is not versioned in transaction time (only facts, cessations, reviews and branchings are).
- `value_at`, `holds`, `move` and identity use the selective path. `facts_about`, `history`, `events`, `exists`,
  `destroy`, `parts`, `dependencies` and `find(world=...)` still load whole worlds (see the review).
- The TypeDB functions ignore time and review status; the Python closure is authoritative. They agree on the
  tested case.
- Monotonic transaction time is enforced per process, not across concurrent writers.
- Valid-time truth uses the earliest recorded cessation; conflicting cessations are not yet reported as disputes.

## Architectural review (2026-11-09)
Three decisions were reviewed before merging. Each fix is a separate commit on `feature/m1-foundational-core`.

### 1. World inheritance and isolation
**Found:** inheritance was *live*. A correction recorded in the base after a branch reached the variant, and a review
made in a variant changed the base. `value_at` and `holds` applied different precedence rules.

**Semantics now (core 0.2.0):**
| Rule | Meaning |
|---|---|
| **Branch time** (`branch-at`, valid time) | the variant inherits base claims that start before it, and base cessations that fall before it |
| **Knowledge snapshot** (`knowledge-at`, transaction time; default: when the branch was made; never in the future) | the variant inherits only base claims, cessations and reviews **recorded by then**. Later base knowledge, including corrections about the time before the branch, is never pulled in. To adopt it, branch again |
| **Nested variants** | the tightest limits along the path apply (earliest branch time, earliest snapshot) |
| **Isolation** | claims, cessations and reviews all belong to the world that recorded them. Nothing done in a variant is visible in its base |
| **Overrides** | functional types: a nearer world's holding claim overrides inherited ones (`holds` and `value_at` agree). Other types: inherited facts stay until the variant ceases them |
| **Contradictions** | accepted claims of the same world that disagree are DISPUTED, as in any world |
| **History** | `as_of` applies on top: as known at τ, the variant shows its own records by τ, and the snapshot only if the branching itself was recorded by τ |

Regression tests (`tests/test_worlds.py`, 9): a correction after the branch about the past; an explicit earlier
snapshot; variant reviews and cessations; `holds`/`value_at` agreement; contradictions; history; nested variants;
hypothetical things; non-functional inheritance.

### 2. Identity and existence
**Decision:** identity is global (one register of ids and names); **existence is per world**.
| Case | Answer of `exists(world, thing, t)` |
|---|---|
| Accepted `existence` claim holds at t | ASSERTED true |
| Before the creation window, or after destruction | ASSERTED false |
| Inside an uncertain creation window | UNKNOWN |
| No existence claim, but the thing takes part in a fact holding at t | INFERRED true |
| Only a proposed existence claim | UNKNOWN, with the proposal as an alternative |
| The world says nothing about the thing | NOT_YET_KNOWN |

`destroy()` ends the thing's existence and its holding facts in that world only. `find(name, world=...)` returns only
things the world mentions, so a thing created in a hypothetical world never appears in actual-world answers
(`tests/test_existence.py`, 6 tests). Not modelled: kinds of creation (manufacture, birth), and existence that is
not tied to time. Facts asserted directly about a thing that no longer exists are not refused (see limitations).

### 3. Query architecture
**Which work runs where:**
| Work | Where | Why |
|---|---|---|
| Select by claim type, role player, world scope | **TypeQL** | typed pattern matching is what TypeDB is for |
| Transaction-time limits (each world's snapshot), branch-time limit for inherited claims | **TypeQL** (comparisons on `recorded-at`, `valid-from-earliest`) | plain value filters |
| Valid-time pre-filter: drop claims that start after t or certainly ended before t | **TypeQL** (disjunction with negation) | plain value filters |
| Transitive part-of / depends-on within a world | **TypeQL functions** (`parts_in`, `dependencies_in`) | recursion in the database |
| Review status at τ (latest review, rejection wins ties) | Python | needs ordering across records; expressible in TypeQL with `reduce`, but not worth it yet |
| Cessations deciding truth, three-valued truth from windows | Python | small; probe P1B-C showed TypeQL can do the certain cases |
| Identity closure over accepted links only | Python, with **selective** loading of the links that touch the subject | closure depends on review status |
| Precedence across worlds, answer statuses | Python | semantic policy, best kept in one readable place |

**Selective path:** `value_at`, `holds`, `move` and identity load only claims of the asked type that involve the
subject's identity group, can hold at t, and pass each world's limits. The full load remains as the reference
(`WM_SELECTIVE=0`), and the whole suite passes on both paths. `tests/test_selective.py` checks that 336 answers are
identical on a seeded world with moves, a variant, an identity link, a conflict and a cessation.

**TypeQL lessons:**
- A second `links` constraint in the same query does not match a role player already bound by the first. The first
  version therefore filtered by subject with an existence check (`not { not { ... } }`). That gave correct answers,
  but TypeDB evaluated it after scanning every claim in the world (v1 below). The subject is now bound positively, so
  the query starts from it. Its own role comes from that binding, and the other players come from an optional block.
- Variables cannot be shared between a negated branch and a positive branch of a disjunction.

**Measured** (`scripts/bench_query_paths.py`, `docs/m1/bench-query-paths.json`; one run, this Mac, TypeDB in Docker):
Synthetic world: 200 objects, 30 places, 1,000 moves (2,200 claims in the actual world, plus events, cessations
and a hypothetical variant with 50 moves); 60 random `value_at` questions across both worlds; answers identical on
both paths.

| | Selective v1 (existence-check filter) | **Selective (subject bound)** | Full load (reference) |
|---|---|---|---|
| Median / p95 latency per question | 515 / 622 ms | **23.8 / 32.5 ms** | 1,822 / 1,963 ms |
| Claims materialised in Python per question | 3.7 | **3.7** | 2,256 |
| TypeQL queries per question | 12.5 | 12.5 | 6.3 |
| Building the world (1,000 `move` calls) | 392 s (335 ms median per move) | **42 s (33 ms)** | — |

Storage: about 9.0 MB on disk for this database, about 4.1 KB per claim. That includes events, cessations and
TypeDB's indexes, so it is an upper bound per fact, not a tuned figure. Raw outputs: `bench-query-paths-v1.json`,
`bench-query-paths.json`.

**Trade-offs:** the selective path makes several small TypeQL queries per question (per world in the chain, per
identity member, per claim type), so its cost grows with identity groups and world depth rather than with world
size. The full path's cost grows with everything in the world. Not yet selective: whole-world listings (`events`,
`history`, `facts_about`, `exists`, `destroy`, closures, `find(world=...)`). They can use the same filters when
needed. No caching, batching or indexing work was done (deliberately).
