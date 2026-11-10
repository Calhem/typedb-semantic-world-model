# TypeDB modelling best practices (verified)

Practices learned while building the semantic world model on **TypeDB CE 3.14.1** (Python driver 3.14.0). Only
behaviour verified by a probe or a passing test is listed as a practice. Design preferences that are not verified are
in the last section, marked as such. Started 2026-11-09; keep it current as new constraints are verified.

Evidence keys: `P1-n` Phase 1 probes (`probes/typedb_capabilities.py`), `P1B-x` Phase 1B probes
(`probes/phase_1b_probes.py`), `A-n` architecture probes (`probes/architecture_probes.py`,
`probes/architecture_snippet_check.py`), `B-n` v0.2 probes (`probes/architecture_v02_probes.py`), `M1` Milestone 1
code and tests, `C03` Core 0.3 code, tests and Stage D measurements (`docs/core-0.3/`), `C04P` Core 0.4 planning probes
(`probes/core04_feasibility.py`; exploratory schema, throwaway databases), `A0-x` Core 0.4 Stage A0 probes
(`probes/core04_a0_probes.py`) and the A0 code and tests (`tests/test_f_a0_*.py`).

## Types and identity
| Practice | Why (verified behaviour) | Evidence |
|---|---|---|
| Give TypeDB types only to kinds that never change for an instance; express labels, roles and categories as relations to concept instances | an instance has exactly one type, and it cannot be re-typed in place (`INF11`) | P1-3, P1B-B |
| Give every entity and relation you need to reference a stable id attribute with `@key` | uniqueness is enforced on commit; duplicates are rejected | M1 tests |
| If some relation content must be unique, compute a canonical key string and put `@key` on it | TypeDB otherwise allows two relation instances with identical role players | A1, A snippet (`CNT9`) |
| Coordinate attribute and type names across schema modules | there are no namespaces; a second definition of the same name with a different value type is rejected (`DEX14`) | P1-4 |
| Avoid TypeQL reserved words as labels: `alias` and `role` are reserved (so a role concept type needs another name, e.g. `social-role`) | rejected with `DEX31` | M1, Core 0.3 schema |

## Relations and roles
| Practice | Why | Evidence |
|---|---|---|
| Use n-ary relations for facts with several participants, and let relations play roles in other relations (evidence for a fact, attribution of a claim) | both work natively | P1-2, A3 |
| Declare roles a subtype needs to specialise on the supertype; a relation cannot specialise roles it declares itself | `SVL11` | M1 |
| Query "any participant" with a role variable: `$e links ($r: $x)` | works across subtypes | M1 |
| Use `@card(1..1)` on `plays` or `relates` for "exactly one" (e.g. one world per claim); it is checked at commit | `CNT5` on violation | M1 |
| Removing a role from a type is refused while data uses it: plan profile removal as a migration | `SVL51` | P1B-D |
| A role allows **at most one player per relation instance** unless declared otherwise: give symmetric or multi-player roles an explicit `@card` (e.g. `relates same @card(2..2)`) | two players on an undeclared role were rejected with `CNT5` (`@card(0..1)`) | B2, M1 |
| A query on a general role finds players of roles specialised from it: `$e isa event (actor: $x)` returns a profile's `pickup:picker` players | role inheritance works for matching | C04P P3 |
| But labels come back specialised: `isa!` gives the subtype (`pickup`) and `links ($r: $x)` gives `pickup:picker`; application code that compares labels must map them to their core supertype and core role | otherwise profile subtypes are silently missed | C04P P3b, P3c |
| Read a type's supertypes from the schema with `match $t label X; $t sub $s;` (reflexive: X, then each ancestor) | returns e.g. `docked-at`, `located-at`, `proposition` | A0-R1 |
| Read a specialised role's parent with `match $t label X; $t relates $r; $r sub $p;` (reflexive); `relates` also lists roles inherited from supertypes | returns e.g. `pickup:picker -> event:actor` | A0-R2, A0-R3 |
| A type may own a second `@key` attribute (e.g. a proposition's `proposition-key` and `wm-id`), and both are enforced | duplicate second key rejected with `CNT9` | C04P P8 |
| A proposition (relation) can play a role in another proposition (e.g. the outcome of `initiates`) | works | C04P P2 |
| One role can take players of several relation types (a `content` role played by propositions and by event descriptions); filter with `$c isa <type>` in the query | queried by any, by proposition or by event | B2 |

## Attributes and values
| Practice | Why | Evidence |
|---|---|---|
| Put uncertainty, units or provenance of a value on the owning entity or relation, not on the attribute | attributes cannot own attributes (`DEX11`) | P1-5 |
| For values of several types under one name, define an abstract attribute with typed subtypes and have the owner own **each concrete subtype**; query with the abstract parent | owning only the abstract parent is rejected (`INF11`); owning the subtypes works and `has magnitude $v` returns all | A2, A2b |
| Do not rely on struct values for stored data in 3.14.1 | structs can be defined, but no literal form tried could be inserted | P1-6, P1B-A |
| `datetime-tz` keeps sub-second precision; the Python driver returns `Datetime` whose `datetime_without_nanos` carries microseconds | — | P1-11, M1 |

## Queries
| Practice | Why | Evidence |
|---|---|---|
| When a disjunction tells instances apart by which attribute they own (`{ $c has proposition-key $k; } or { $c has wm-id $k; }`), name the type in each branch (`{ $c isa event, has wm-id $k; }`) | once a further type owns the attribute (propositions gaining `wm-id`), an instance owning both matches both branches and the query silently returns each one twice under two ids; 13 of 78 regression tests caught it | A0.1 |
| Pass values as parameters with a `given` header; compare attributes with `has attr == $param` | `has attr $param` declares the variable as an attribute and conflicts with a value parameter (`REP35`) | M1 |
| Never give a parameter the same name as a matched variable (e.g. `$old` as both a thing and a value) | `REP1` | M1, Core 0.3 Stage B |
| Do not reuse one variable name for two different things (e.g. a thing and a value) in one query | `REP1` | M1 |
| Name each role player's type in insert/match patterns when several types own the same key attribute | otherwise type inference may consider an incompatible type and reject the query (`INF4`) | M1 |
| Bind the filtering player positively to make the query start from it: `$s has wm-id == $id; $c links ($r: $s);` | an existence check (`not { not { ... } }`) gave the same answers but was evaluated after scanning all candidates: 515 ms vs 23.8 ms per question on 2,200 claims | M1 bench |
| A second `links` constraint in the same query does not match a player already bound by the first; recover that player's role from the first binding and the others with `try { $c links ($role: $x); }` | the subject's own role disappeared from results | M1 |
| Use different variable names in the positive and negated branches of a disjunction | `REP44` "must be bound" | M1 |
| Optional data: `try { ... };` blocks; absent values come back as `None` | works in reads | M1 |
| When a variable's type is fixed by the query (e.g. `$c isa same-as`), every disjunction branch **and every `try` block** must be possible for that type: build the pattern for the type instead of relying on pruning | an impossible branch (`{ $c has wm-id $x; }` for a proposition) or `try { $c has lower $v; }` for a type that cannot own `lower` is rejected with `INF11`, not skipped | Core 0.3 Stage B |
| In the Python driver, `row.get(var)` raises if `var` is not in the query; wrap optional reads | "Cannot get concept from a concept row by variable" | Core 0.3 Stage B |
| Recursive functions (`fun f(...) -> { ... }` with `let $x in f(...)`) work for transitive closures and can take a scoping argument (e.g. a world) | — | P1-7, M1 |
| A function's declared return type must cover every type that can play the returned role; when a role is played by unrelated types (e.g. `causes:effect` by events and occurrences), narrow inside the match (`$x isa event;`) | otherwise the schema commit fails (`FIN4`) | C04P P5 |
| Compare attributes of two matched instances directly for interval logic, e.g. range overlap `$la <= $ub; $lb <= $ua;` | finds exactly the overlapping pairs | B3 |

## Content and stance (proposition / attestation) patterns
| Practice | Why | Evidence |
|---|---|---|
| Store content as a keyed relation and each stance as a separate n-ary relation (`attestation (attester, content, context)`) pointing at it | one content, many holders; denials share content; selection through the two hops measured at about 2 ms per query on 2,200 facts | B1, C03 experiment |
| Pick the content-id pattern by content type (`proposition-key` for propositions, `wm-id` for event descriptions) rather than a disjunction | with a fixed type, the impossible branch is rejected (`INF11`) | C03 Stage B |
| Bind the subject positively and recover its role from that binding; read other players with `try { $c links ($role: $x); }` | two `links` constraints never match the same player | M1, C03 |
| When a revision record links an old stance record to a new one (supersession), judge the link **per perspective**: hide the old record only for perspectives that accept the new one | otherwise an unaccepted record changes other perspectives' answers; 5 regression tests failed before this rule | C03 D14 (`test_e_supersession.py`); architectural recommendation, not database behaviour |

## Query selectivity and temporal filtering
| Practice | Why | Evidence |
|---|---|---|
| Read many optional attributes of matched instances with a `fetch` stage, not one `try` block each | on the same selection and results: five `try` blocks 7.6 ms per query vs `fetch` 2.5 ms (ids alone 1.9 ms); applied in Core 0.3, the main query went from 8.8 to 2.9 ms per call | C03 experiment (`experiment-main-query.json`), `bench-instrumented-core03-fetch.json` |
| In `fetch`, `$x.attr` must be ownable by **every** possible type of `$x`; fetch optional attributes of a subtype in a separate query restricted to it | `QUA8` "attribute 'lower' cannot be when '$c' has type 'existence'" | C03 Stage D |
| `fetch` returns datetimes as ISO strings with nanoseconds and offset, types as `{"kind", "label"}`, absent attributes as `null` | parse to the same Python values as concept rows (test compares both) | C03 (`test_d_fetch.py`) |
| When timing, wrap every read helper (rows **and** documents): an unwrapped `fetch` path is silently counted as Python time | the first optimised measurement showed Python 13.5 ms, which was really `fetch` time | C03 Stage D |
| Measure where time goes before optimising: wrap the read helper and split TypeDB time from Python time | Core 0.3's 2× regression was 91 % TypeDB reads; the main query was 51 % of read time | C03 (`bench-instrumented-*.json`, `profile-query-kinds.json`) |
| **Do not pre-filter in TypeQL by "ended before t"** when an end carries meaning: an attestation that ended says the content stopped holding, which can dispute other accounts | dropping such rows changed answers on the selective path only; the equivalence test caught it; a regression test fails with the old filter | C03 D6 (`test_c_time_semantics.py`) |
| Pre-filtering "starts after t" is safe: such rows say nothing about t | equivalence tests pass on both paths | C03 |
| Keep a full-load reference path and an equivalence test comparing whole answers (including evidence) with the selective path | it found both D6 and the ended-interval defect D5 | M1, C03 |
| Count queries per question as well as latency: in tiny worlds, many small selective queries can be slower than one full load | test suite: selective about 62 s vs full about 48 s on small worlds; on 2,200 facts selective is 80× faster | C03 |

## Operations
| Practice | Why | Evidence |
|---|---|---|
| Run tests in throwaway databases with unique names and delete them in `finally`, plus a session-end sweep | repeated runs left nothing behind | M1 |
| Treat timings as indicative unless repeated; record runs and machine | single-laptop Docker runs vary | Phase 1, M1 |
| To make an attribute a `@key` of a type that already has instances, migrate in three steps: `define T owns A;` (schema tx), write `A` for every instance (write tx), then `define T owns A @key;` | adding `owns A @key` directly while instances lack `A` is rejected with `CNT5`; after step 3, new instances without `A` are rejected | A0-M1..M4b, A0.1 upgrade test |
| Build a query branch that depends on an optional schema module only when that module is installed (e.g. `{ $x isa proposition; }` in an id lookup) | on a database without the module the branch is impossible and the whole query is rejected (`INF11`) | A0.1 upgrade test |

## Design trade-offs observed (not yet best practice)
These are preferences supported by analysis, not verified rules.
- Keeping content (propositions) separate from stance (attestations) adds one hop per question. Measured once on
  1,200 location facts (B1, two runs): median 20.6 ms (one hop) vs 22.9 ms (two hops), identical answers; p95 noisy
  (one-hop showed outliers of ~300 ms in both runs). Indicative only; larger worlds untested.
- In Core 0.3 the hop itself is cheap. The cost is per-row attribute reading and the extra rows a stance layer keeps
  (superseded attestations and their restatements). Whether a lighter "end" record would halve those rows is untested.
- Application code still decides review status, precedence and time windows. TypeQL can express the certain-interval
  cases (P1B-C), but moving more logic into functions is untested at scale.
