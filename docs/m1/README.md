# Milestone 1: executable foundational core

**Status (2026-11-09): implemented, 25 tests passing against TypeDB CE 3.14.1. Stopped for architectural review.**

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
| **Worlds** | actual, simulated, hypothetical; a variant world inherits its base's claims that began before `branch-at`; its own claims take precedence; ceasing an inherited fact in a variant does not affect the base |
| **Identity** | `same-as` claims (proposed by default); only accepted links merge (transitively); proposed links are never chained; reviews can undo a merge, and earlier transaction times still show it |
| **Decisions** | `review` (accepted, rejected, retracted); the latest review by the transaction time decides; rejections win ties |
| **Answers** | `ASSERTED`, `INFERRED` (functional exclusivity), `DISPUTED`, `UNKNOWN`, `NOT_YET_KNOWN`, with supporting claims and proposed alternatives |
| **Modules** | schema files per module, installed in order and recorded (`schema-module`); claim types discovered by introspection |

Code: `schema/core/0001-core.tql` (≈120 lines), `src/worldmodel/` (`model.py`, `semantics.py`, `typeql.py`), tests in
`tests/`.

## Who does what (kept explicit)
| Layer | Responsibilities |
|---|---|
| **Ontology semantics** (documented, Phase 1C) | what a claim, a world, a cessation, an identity link mean |
| **TypeDB enforces** | kinds of thing and which roles they may play (a concept cannot be *located*); every claim and cessation belongs to exactly one world (`@card(1..1)`, tested); unique ids; allowed values (`world-kind`, `end-basis`, `verdict`); `same-as` has exactly two players |
| **TypeDB computes** | typed matching of role players, world scoping, the recursive functions `parts_in` and `dependencies_in` (world-scoped; time and status ignored) |
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
6. **Variant precedence:** at a given time, claims from the nearest world win over inherited ones, for any claim
   type (not only functional ones).
7. **Functional claim types** (one value at a time) are declared in Python (`FUNCTIONAL`, currently `located-at`).
8. **Identity links are world-scoped claims.** The canonical id of a merged group is its smallest id.
9. **Transaction time** comes from the writer's clock and must not go backwards per `WorldModel` instance.

## Limitations and unsupported behaviour (known)
- **Not yet:** observations, sources, evidence, provenance chains, OBSERVED and PRESUMED statuses, persistence
  policies, coverage and observed absence, measurements and uncertainty, perspectives and attribution (Milestone 2);
  domain profiles (Milestone 3); synthetic worlds and performance (Milestone 4).
- Clock domains are stored (`clock`) but **not compared**: mixing clocks is not yet refused.
- Adding a thing is not versioned in transaction time (only facts, cessations, reviews and branchings are).
- Reads load all claims of a world (and its bases) per question. That is fine for small worlds; it is not yet measured.
- The TypeDB functions ignore time and review status; the Python closure is authoritative. They agree on the
  tested case.
- Monotonic transaction time is enforced per process, not across concurrent writers.
- Valid-time truth uses the earliest recorded cessation; conflicting cessations are not yet reported as disputes.
