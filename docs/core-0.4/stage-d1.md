# Core 0.4 Stage D-1: the mechanical profile (LABS-1.023)

**Status (2026-11-11): merged into `main` (153c2f2) under LABS-1.025. Limitations 1-4 are tracked in
`deferred-issues.md` (DI-1 to DI-4).** Decisions: D-D-1, D-D-2, D-D-6, D-D-9, D-D-11 (`stage-d-review.md`).

## 1. What was added
| Piece | Where | Kind of change |
|---|---|---|
| Dependency kind on `depends-on` (v0.2 §3.4; D-D-2) | core module `core-0.4-d` (`schema/core/core-0.4-d.tql`): `relates kind @card(0..1)`, `category plays depends-on:kind` | core conformance, additive. Profiles may not modify core types, so it is core, not mechanical |
| Core dependency kinds | seeded by `core-0.4-d`: `dependency:physical`, `dependency:functional`, `dependency:informational`, `dependency:control` | core vocabulary (categories) |
| `depend`, `dependencies(..., kind=)`, `direct_dependencies` | `WorldModel` | general-purpose API |
| Profile `mechanical` 0.1 | `schema/profiles/mechanical/mechanical-0.1.tql`, registered in `src/worldmodel/mechanical.py` | profile vocabulary |
| `connected-to(endpoint ×2, joint-kind?)` | profile schema | a mechanical connection: symmetric, timed; not parthood, not dependency |
| `replacement sub event` (`removed as patient`, `fitted`) | profile schema | removed and fitted parts told apart; `fitted` is the profile's own role (D-D-6) |
| Vocabulary | `mechanical:assembly`, `mechanical:component` (D-D-11: categories, not kinds), joint kinds `mechanical:bolted`, `mechanical:pressed`, `mechanical:splined` | seeded at installation |
| `connect`, `connections`, `replace_part`, `replacement` | `worldmodel.mechanical` | profile API (functions taking the WorldModel) |
| Gearbox extension | `gearbox.extend_mechanical` | example data |

Assemblies and components need nothing new: they are the core `part-of` structure, and being an assembly or a
component is a classification.

## 2. Dependency-kind semantics (D-D-2 and its qualification)
- A `depends-on` content without a kind keeps its canonical key (`depends-on|dependee=…|dependent=…`) and its
  attestations. A typed claim for the same pair is a **different proposition**: adding kinds never edits, merges or
  reinterprets the untyped claim.
- `direct_dependencies` reports each dependency with its kind, and the untyped claim as **`unspecified`**.
- `dependencies(..., kind=None)` behaves exactly as before: every dependency, whatever its kind.
- `dependencies(..., kind=K)` follows only dependencies of exactly kind K. An untyped dependency is never counted as K,
  for any K.
- Dependencies are asserted, never inferred: no transitivity in `direct_dependencies`, and no failure propagation.
  `dependencies` is a listing closure, as in Core 0.3.
- **Existing databases:** `install_module("core-0.4-d")` adds the kind role and the four kinds; existing untyped
  claims are untouched. Profiles require the full core, now including `core-0.4-d`.

## 3. Replacement semantics
- `replace_part(...)` writes:
  - a source's `replacement` description: removed, fitted, actor, instrument and location, attested over its
    interval, optionally describing an occurrence;
  - the effects that source claims: `terminates part-of(removed, assembly)` and `initiates part-of(fitted, assembly)`.
- `replacement(...)` reports three things separately, and concludes nothing beyond them:
  - the account: accepted or not, its interval, the parts it names;
  - each occurrence it is accepted as describing, with **that occurrence's own status**;
  - each claimed effect, with the claim's judgement and the state before and after.
- In the gearbox world, the maintenance system's account is accepted, while `o-bearing-replacement` stays
  "not established": no existence attestation exists for it.

## 4. Validation
**Tests:** `tests/test_k_d1_mechanical.py`, 16 tests:
- installation alone, with the fixtures, and the upgrade path from a Stage C database;
- seeded kinds and unchanged untyped keys;
- typed vs unspecified dependencies, including the view as known before kinds were recorded;
- every core kind and kind-filtered closure;
- dependency is not parthood;
- symmetric, timed connections, and a disputed connection;
- replacement roles;
- an accepted account vs the occurrence's own status, and claimed effects vs judged states;
- historical state;
- perspective disagreement, on the replacement and on a dependency, before and after the system accepts the denial;
- a hypothetical control upgrade;
- the full reference chain with the profile;
- core queries;
- selective/full-load agreement.

**Results:**

| Run | Result |
|---|---|
| full suite, selective, twice | 324 passed, 324 passed |
| full suite, full load, twice | 324 passed, 324 passed |
| core-protection (`WM_PROFILES=1`: mechanical plus three fixtures; Stage C databases get `core-0.4-d` first), each path | 324 passed, 324 passed |
| leftover test databases | 0 |
| merged `main` 8c60f04 (D0), clean checkout, each path | 308 passed, 308 passed |

**Demonstration:** `scripts/show_mechanical.py`, output in `docs/core-0.4/mechanical-output.md`. The existing
demonstrations still produce the same answers:
- `show_reference_world` and `show_dynamics` are identical;
- `show_spatial_reasoning` differs only in a printed wall-clock transaction time;
- `show_qualities_agency` differs only in the order within pairs, which depends on random ids.

**Performance:** `docs/core-0.4/bench-d1/README.md`. Query counts are unchanged for existing questions, and the
latency differences come from run order and machine drift (a reversed-order check is included). The D-1 extension adds
10% storage.

## 5. Found while validating
- **`replacement()` crashed for an account that is not accepted:** with no interval, there is no before/after
  state. Fixed: the state is reported as not judged (None).
- **A polarity-disputed content is omitted by `facts_about`,** which lists only holding contents; functional-slot
  conflicts are listed as DISPUTED. The new reports (`direct_dependencies`, `connections`) therefore read the
  per-content judgement and list disputed items as DISPUTED. `facts_about` itself is unchanged (core behaviour).
  Recorded as a limitation.
- **Before a replacement, "is bearing-3 part of the assembly?" is UNKNOWN, not false:** nothing says where it was.
  Open-world semantics, as intended. The report says so instead of implying false.

## 6. Limitations
1. `facts_about` omits contents disputed by an accepted denial (above). Any generic reader built on it has the same
   blind spot. A core change would need its own decision.
2. Single-valued event roles are not implemented (v0.2 D9). Two accepted replacement accounts of one occurrence that
   name different removed parts are each reported per account, not judged DISPUTED at the occurrence level.
3. A connection has no functional slot: two accepted joint kinds for the same pair are two contents, not a conflict.
4. Dependency kinds are an open vocabulary (any category). The core seeds four; nothing checks that a category used as a
   kind is meant as one.
5. Mechanical API functions take the WorldModel as an argument (`mechanical.connect(wm, ...)`) rather than being
   methods, which keeps profile code out of the core class.
