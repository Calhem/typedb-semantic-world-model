# TypeDB modelling best practices (verified)

Practices learned while building the semantic world model on **TypeDB CE 3.14.1** (Python driver 3.14.0). Only
behaviour verified by a probe or a passing test is listed as a practice. Design preferences that are not verified are
in the last section, marked as such. Started 2026-11-09; keep it current as new constraints are verified.

Evidence keys: `P1-n` Phase 1 probes (`probes/typedb_capabilities.py`), `P1B-x` Phase 1B probes
(`probes/phase_1b_probes.py`), `A-n` architecture probes (`probes/architecture_probes.py`,
`probes/architecture_snippet_check.py`), `B-n` v0.2 probes (`probes/architecture_v02_probes.py`), `M1` Milestone 1
code and tests.

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
| Pass values as parameters with a `given` header; compare attributes with `has attr == $param` | `has attr $param` declares the variable as an attribute and conflicts with a value parameter (`REP35`) | M1 |
| Do not reuse one variable name for two different things (e.g. a thing and a value) in one query | `REP1` | M1 |
| Name each role player's type in insert/match patterns when several types own the same key attribute | otherwise type inference may consider an incompatible type and reject the query (`INF4`) | M1 |
| Bind the filtering player positively to make the query start from it: `$s has wm-id == $id; $c links ($r: $s);` | an existence check (`not { not { ... } }`) gave the same answers but was evaluated after scanning all candidates: 515 ms vs 23.8 ms per question on 2,200 claims | M1 bench |
| A second `links` constraint in the same query does not match a player already bound by the first; recover that player's role from the first binding and the others with `try { $c links ($role: $x); }` | the subject's own role disappeared from results | M1 |
| Use different variable names in the positive and negated branches of a disjunction | `REP44` "must be bound" | M1 |
| Optional data: `try { ... };` blocks; absent values come back as `None` | works in reads | M1 |
| Recursive functions (`fun f(...) -> { ... }` with `let $x in f(...)`) work for transitive closures and can take a scoping argument (e.g. a world) | — | P1-7, M1 |
| Compare attributes of two matched instances directly for interval logic, e.g. range overlap `$la <= $ub; $lb <= $ua;` | finds exactly the overlapping pairs | B3 |

## Operations
| Practice | Why | Evidence |
|---|---|---|
| Run tests in throwaway databases with unique names and delete them in `finally`, plus a session-end sweep | repeated runs left nothing behind | M1 |
| Treat timings as indicative unless repeated; record runs and machine | single-laptop Docker runs vary | Phase 1, M1 |

## Design trade-offs observed (not yet best practice)
These are preferences supported by analysis, not verified rules.
- Keeping content (propositions) separate from stance (attestations) adds one hop per question. Measured once on
  1,200 location facts (B1, two runs): median 20.6 ms (one hop) vs 22.9 ms (two hops), identical answers; p95 noisy
  (one-hop showed outliers of ~300 ms in both runs). Indicative only; larger worlds untested.
- Application code still decides review status, precedence and time windows. TypeQL can express the certain-interval
  cases (P1B-C), but moving more logic into functions is untested at scale.
