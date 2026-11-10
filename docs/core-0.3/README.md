# Core 0.3: World Ontology v0.2 implemented (Stages A-D)

**Status (2026-11-10): Stages A-D complete on branch `feature/core-0.3`, with the `fetch` optimisation and the
supersession fix; merge paused for review of the fix; not merged.**
Baseline: [World Ontology v0.2](../architecture/world-ontology-v0.2.md) (frozen). Milestone 1 stays on `main`.

## Run it
```bash
docker compose -f environments/compose.yaml up -d typedb        # TypeDB 3.14.1, 127.0.0.1:1735
uv sync
uv run pytest -q                                                 # selective path (default)
WM_SELECTIVE=0 uv run pytest -q                                  # full-load reference path
uv run python -I scripts/bench_query_paths.py                    # selective vs full on a 2,200-attestation world
```

```python
from datetime import datetime, timezone
from worldmodel import WorldModel
t0, t1 = datetime(2026, 11, 9, 10, 0, tzinfo=timezone.utc), datetime(2026, 11, 9, 10, 30, tzinfo=timezone.utc)
wm = WorldModel.create("demo", replace=True)
w = wm.create_world("depot")
box, shelf, dock = (wm.add_entity(k, n) for k, n in (("physical-object", "box"), ("place", "shelf-3"), ("place", "dock")))
a = wm.attest(w, "located-at", {"located": box, "place": shelf}, start=t0, until_superseded=True)   # system's claim
wm.add_entity("physical-object", "A", id="A")
d = wm.deny(w, "located-at", {"located": box, "place": shelf}, start=t0, until_superseded=True,
            attester="A")                                                                           # A's denial
wm.value_at(w, "located-at", box, t1)                    # ASSERTED shelf (A's denial is an unreviewed alternative)
wm.accept(d)                                              # the system accepts A's denial
wm.holds(w, "located-at", {"located": box, "place": shelf}, t1)   # DISPUTED, with both as evidence
wm.holds(w, "located-at", {"located": box, "place": shelf}, t1, perspective="A")   # A's view: false
```

## What is implemented
| v0.2 element | Core 0.3 | Where |
|---|---|---|
| Kinds `physical-object`, `social-object`, `place`, `information-object`; `occurrence`; concepts `category`, `social-role`, `quality-kind`; reference systems `clock`, `spatial-frame`, `unit`; `world` | schema types | `schema/core/core-0.3.tql` |
| Timeless keyed propositions: `existence`, `located-at`, `part-of`, `member-of`, `depends-on`, `classified-as` (with context), `has-quality` (value category or `lower`/`upper`/`coverage-level`, unit), `same-as`, `describes`, `initiates`, `terminates` | stored once per canonical key; TypeDB `@key` enforces it | `keys.py`, `model.proposition` |
| Event descriptions (content identified by id) and occurrences; identity only by accepted `describes` links | `describe_event`, `record_event`, `descriptions`, `occurrence` | `model.py` |
| Attestations: attester, content, world (arity enforced), stance, polarity, basis, interval windows, end basis, credence, optional clock | `attest`, `deny` | `model.py` |
| Supersession by the same attester | `end` | `model.py` |
| Acceptance per perspective, world-independent; own attestations are part of the attester's view; stipulations constitutive | `accept`; `semantics.acceptance_state` | `semantics.py` |
| Worlds with snapshot inheritance (branch time, knowledge time, nested limits); per-perspective inheritance | `create_world`; `_world_chain`, `_load` | `model.py` |
| Answers with statuses and evidence: ASSERTED, STIPULATED, INFERRED, DISPUTED, UNKNOWN, NOT_YET_KNOWN | `value_at`, `holds`, `exists`, `facts_about`, `history`, `events` | `model.py`, `semantics.py` |
| Selective retrieval in TypeQL (content type, bound subject, world, knowledge limit, branch limit, start ≤ t), full load as reference | `_filters`, `_load`, `selective` flag | `model.py` |

## Deviations from v0.2 and clarifications (none changes the baseline's meaning)
| # | Item | What Core 0.3 does | Why |
|---|---|---|---|
| D1 | OBSERVED and PRESUMED | not produced; attestations with basis observation are labelled ASSERTED, with `basis: observation` in the evidence | observations, coverage and persistence policies are deferred (baseline §12) |
| D2 | `initiates` / `terminates` | in the schema, not yet written by `record_event` | their outcome role is played by a proposition, which needs player lookup by key; deferred |
| D3 | End basis `until-superseded` | the attester commits that the content holds until it records otherwise; allowed in any world | v0.2 mentioned a "stipulated" end basis for defined worlds; Milestone 1's actual-world tests need the testimony form; stipulation remains its own stance |
| D4 | Status for mixed support | STIPULATED > ASSERTED > INFERRED, by the most direct basis; all evidence is listed | v0.2 sets no order between supported kinds; one label is needed |
| D5 | Ended intervals | a stated end implies "does not hold" only until a later attestation of the same content starts; ended accounts still dispute accounts that began before the end | found while porting: returning to an earlier place was being disputed (`tests/test_c_time_semantics.py`) |
| D6 | Valid-time pre-filter | TypeQL skips only attestations that start after t | dropping attestations that ended before t lost their "does not hold" and changed dispute answers (found by the equivalence test) |
| D7 | Attester agency (E2) | TypeDB restricts attesters to physical or social objects; the agency classification is **not checked yet** | validation deferred |
| D8 | Derivations (E6) | no derivation records; INFERRED comes only from query-time functional exclusivity and existence by participation | rules and reasoners are later work |
| D9 | Single-valued roles | `FUNCTIONAL` (located-at) is a Python constant; occurrence views list every participant per role with its descriptions and sources, without a dispute label | profile metadata is deferred |
| D10 | `destroy` on others' claims | the system's own attestations are ended; others' accepted ones are denied by the system (so they become disputed, not overruled) | the system cannot supersede another attester's claim |
| D11 | `social-role` | the role concept type is named `social-role` | `role` is reserved in TypeQL |
| D12 | Measurements, clocks, frames | stored (ranges, coverage level, clock role) but not reasoned about | deferred (baseline §12) |
| D14 | Supersession across perspectives (**defect, fixed**) | a source's replacement hides the original only for perspectives whose view includes the replacement; others keep it, marked `superseded_by_source`; corrections via `attest(supersedes=…)` | previously an unaccepted replacement erased other perspectives' accepted evidence, contrary to v0.2 §6.2 ([supersession-and-endings.md](supersession-and-endings.md)) |
| D13 | v0.2 core proposition types not yet in the schema | `constitution`, `causes`, `positioned-in`, `frame-transform`, `clock-alignment`, `absence-of`, `anchored-to` | Core 0.3's first increment covered the types Milestone 1's behaviour needed; the rest are specified but unimplemented |

## Regression results
**78 tests**, against TypeDB CE 3.14.1 in throwaway databases:
| Group | Tests | File |
|---|---|---|
| Stage A: schema, keys, proposition uniqueness, event descriptions | 8 | `test_a_content.py` |
| Stage B: pure semantics (polarity, acceptance, supersession, identity) | 6 | `test_b_semantics.py` |
| Stage B: attestations, corroboration, denials, perspectives, stipulation, snapshots, evidence | 8 | `test_b_stance.py` |
| **Milestone 1 regression requirements, ported** (same names and expectations) | **41** | `test_m1_core.py` 19, `test_m1_worlds.py` 9, `test_m1_existence.py` 6, `test_m1_semantics.py` 6, `test_m1_selective.py` 1 |
| Occurrences vs descriptions (clarification A) | 3 | `test_c_occurrences.py` |
| Defects found in Stage C (D5, D6), each shown to fail without its fix | 3 | `test_c_time_semantics.py` |
| `fetch` reads match row-based reads (Stage D optimisation) | 1 | `test_d_fetch.py` |
| Supersession across perspectives (D14): ends, corrections, retraction, acceptance and rejection of replacements, hypothetical worlds, path equivalence for every perspective; 5 of 8 failed before the fix | 8 | `test_e_supersession.py` |

Every test runs on both paths (selective, and `WM_SELECTIVE=0` full load). The equivalence test and the benchmark compare
whole answers (status, values, support, alternatives **and evidence**) between the paths: identical. Validation runs
are recorded at the end of this document.

## Performance against Milestone 1
Same workload as Milestone 1's benchmark (200 objects, 30 places, 1,000 moves, a hypothetical variant with 50 moves,
60 random `value_at` questions, seed 11), same TypeDB server, same session, **same Python (3.13.17)**. Every
implementation ran through `scripts/bench_instrumented.py`, which wraps each one's own read helpers without changing its
code, to split TypeDB time from Python time. One run each, except Milestone 1 (two runs, for drift); indicative.

| Measure | Milestone 1 (run 1 · run 2) | Core 0.3 original | **Core 0.3 + `fetch`** |
|---|---|---|---|
| Selective question, median / p95 | 26.9 / 39.9 · 24.9 / 34.2 ms | 49.8 / 98.7 ms | **43.5 / 60.3 ms** |
| — TypeDB reads (median) | 23.3 · 21.6 ms | 45.5 ms | **40.2 ms** |
| — Python (median) | 3.5 · 3.2 ms | 4.2 ms | **3.3 ms** |
| Main attestation query, per call | — | 8.8 ms | **2.9 ms** |
| Full-load question, median | 2,022 · 1,903 ms | 4,115 ms | **2,234 ms** |
| Records retrieved per selective question | 3.7 claims | 7.1 attestations | 7.1 attestations |
| TypeQL queries per selective question | 12.5 | 12.5 | 12.5 |
| Building the world (1,000 moves) | 46.9 · 42.7 s | 74.1 s | **56.0 s** |
| Database size on disk | 9.06 · 9.07 MB | 12.40 MB | 12.34 MB |
| Stored records | 2,200 claims + 1,000 cessations | 3,200 attestations, 1,140 propositions, 1,000 event descriptions, 1,000 supersessions | same |
| Answers identical on both paths | yes | yes | yes |

Raw outputs: `bench-instrumented-m1.json`, `bench-instrumented-m1-run2.json`, `bench-instrumented-core03.json`,
`bench-instrumented-core03-fetch.json`; profiles `profile-query-kinds.json`, `profile-query-kinds-fetch.json`. An
earlier uninstrumented pair (Milestone 1 on Python 3.15) gave the same picture (`bench-m1-same-session.json`,
`bench-core03.json`). The supersession fix (D14) adds one query per world level only when supersessions exist and was
not re-benchmarked separately; the suite runs in similar time.

**Cause of the original regression (investigated before optimising):**
1. *Where:* TypeDB reads, not Python.
2. *Which query:* the main attestation query was 51 % of read time: 8.8 ms for about 2.3 rows
   (`profile-query-kinds.json`).
3. *Which part of it* (`experiment-main-query.json`; one world, the same 80 questions, identical result ids):

| Main-query variant | Mean |
|---|---|
| as implemented | 7.6 ms |
| subject bound first | 7.7 ms |
| without the attester role | 8.6 ms |
| without the exact-type lookup (`isa!`) | 8.0 ms |
| without the valid-time filter | 6.5 ms |
| **without the five optional `try` blocks** | **2.8 ms** |
| **same selection, attributes read with a `fetch` stage** | **2.5 ms** |
| selection only (ids) | 1.9 ms |

**Applied:** the main query reads its attributes with one `fetch` stage; quality parameters use a separate `fetch` only
where the content can be `has-quality`. Effect: main query 8.8 → 2.9 ms per call; selective median −13 %, p95 −39 %;
full load −46 %; ingestion −24 %; answers unchanged.

**Remaining gap to Milestone 1 (about 1.7× median):** the role-player and supersession queries (about 3 ms each,
three times per question, `profile-query-kinds-fetch.json`) and twice the rows per question (superseded originals and
their restatements; ended attestations kept for correctness, D6). The content/stance architecture itself remains cheap
(selection about 2 ms). Not optimised further; see section 4 of
[supersession-and-endings.md](supersession-and-endings.md) for the write-amplification question.

## TypeDB modelling lessons from this work
Recorded with evidence in [typedb-modelling-best-practices.md](../typedb-modelling-best-practices.md):
- `role` is reserved, like `alias`.
- When a variable's type is fixed, every disjunction branch and every `try` block must be possible for that type,
  or the query is rejected (`INF11`): patterns have to be built for the type.
- `row.get` raises for variables that are not in the query.
- Parameter names must not clash with matched variables (`REP1`).
- Content uniqueness needs a computed key with `@key`, since TypeDB allows duplicate relation instances.
- Optional attributes read through `try` blocks cost about 1 ms each per query here; a `fetch` stage read the same
  attributes 3× faster. `fetch` of `$c.lower` is rejected unless every possible type of `$c` can own `lower`.
- Supersession must be judged per perspective: a replacement nobody else accepted must not hide their evidence.
- A valid-time pre-filter must not drop attestations that ended before t: an end is evidence that the content does
  not hold.

## Remaining limitations and risks
- **Performance:** after the `fetch` change, selective questions are about 1.7× slower than Milestone 1 (median 43.5
  vs 24.9-26.9 ms). p95 60.3 ms still exceeds the 50 ms ROS target proposed in Phase 1C, which was never approved.
- **Supersession semantics** were wrong until D14; the fix awaits review. Endings still cost a restatement plus a
  supersession; a lighter form would need an ontology amendment (acceptance of terminations).
- **Record volume:** each change writes about 5-6 records (Milestone 1: 4). The restatement-plus-supersession pattern
  for ends doubles the attestations a history holds.
- All deviations D1-D13 above, notably D7 (agency not checked), D8 (no derivations) and D13 (seven v0.2 types missing).
- Single runs on one laptop with TypeDB in Docker; a hypothetical world with only 50 moves; no larger scales.
- No profile module exists yet, so extensibility is untested.

## Architectural alignment assessment
Objective: a general-purpose, DOLCE-influenced, event-aware, evidence-aware world ontology.

**1. Foundational ontology capabilities implemented**
- Particular kinds with identity criteria (physical, social, place, information object) and **occurrences**.
- Concepts (category, social role, quality kind); reference-system and world types.
- Timeless, keyed, n-ary content: existence, location, composition, membership, dependency, classification with
  context, categorical qualities, identity, `describes`.
- Event descriptions with participant roles, distinct from occurrences.
- Creation and destruction per world; transitive composition, in both Python and TypeDB.

**2. Epistemic and temporal infrastructure implemented**
- Attestations: stance, polarity, basis, credence, windows, end basis.
- Supersession by the same attester; perspective acceptance; stipulation.
- Snapshot inheritance through nested worlds; transaction-time queries.
- Six answer statuses with evidence; identity closure; occurrence identity by accepted links.
- Selective retrieval checked against the full load.

**3. Specified in v0.2, not yet implemented**
- Agency as a checked capacity.
- Constitution and transformation.
- Causes, and the `initiates`/`terminates` links in use.
- Metric space: `positioned-in`, frames, `frame-transform`, `anchored-to`.
- Clocks with alignment.
- Quantitative qualities: interval semantics, comparability, units canonicalisation.
- Process and action conventions; single-valued event roles.
- `absence-of`; observations and coverage; OBSERVED and PRESUMED; persistence and resolution policies; derivations.

**4. Domain extensibility not yet demonstrated**
- No profile module.
- No sortal subtypes; no role specialisation (`picker as actor`).
- No extension-point metadata; no core-protection tests; no identified quality instances.

**Divergences from v0.2:** D1-D13 above. None changes v0.2's meaning; D5 and D6 sharpen it.

**Is the epistemic machinery outgrowing the world representation? Yes, measurably:**
- About 58 % of the Python (≈610 of 1,057 lines: visibility, stance, judgement, answers, `semantics.py`) is epistemic.
- Only about 200 lines represent the world itself (content, events, existence, listings).
- The exercised world vocabulary is still thin: symbolic location, categorical qualities, composition, membership,
  dependency.
- At runtime, the epistemic layer doubles the records per change and dominates query cost.

None of this is wasted (it delivers the denials, perspectives and snapshots v0.2 requires). But the next increments
should **add world representation, not epistemic features**. Concretely:
- validate physical, social and scientific worlds on the same foundation with the missing v0.2 world types
  (constitution, causes and state changes, metric space and frames, quantities with units, agency, one profile);
- keep the epistemic layer frozen apart from the `fetch` optimisation;
- reconsider whether an end needs a full restatement plus a supersession, or whether a lighter "end" record would do.

That last one is an open question, not a change.

## Validation record (2026-11-09)
| Run | Selective path | Full-load path |
|---|---|---|
| 1 | 69 passed (54.8 s) | 69 passed (47.6 s) |
| 2 | 69 passed (58.3 s) | 69 passed (44.6 s) |

After all runs, no test or benchmark databases remained on the server. The benchmarks also reported identical answers
on both paths. The D5 and D6 regression tests were each shown to fail with their fix removed and to pass with it
restored.

## Validation record (2026-11-10, after the `fetch` change and the supersession fix)
| Run | Selective path | Full-load path |
|---|---|---|
| fetch only, before D14 (commit `03a8ba9`) | 70 passed (46.2 s) | 70 passed (37.5 s) |
| with D14, run 1 | 78 passed (75.6 s) | 78 passed (54.5 s) |
| with D14, run 2 | 78 passed (59.4 s) | 78 passed (54.9 s) |

The supersession tests failed (5 of 8) against commit `03a8ba9` and pass with the fix. No test or benchmark databases
remained on the server after the runs.
