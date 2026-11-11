# Core 0.4 Stage D0: groundwork and profile architecture (LABS-1.022)

**Status (2026-11-11): merged into `main` under LABS-1.023, after atomic installation was added. No domain profile is
part of D0.** Decisions: `stage-d-review.md`, sections 8 and 8a (D-D-1 to D-D-11, approved with qualifications under
LABS-1.022).

## 1. Subtype-aware generic APIs (D-D-10)
**Cause.** Three generic queries compared a content's stored type label with a core label, so a profile subtype was
silently dropped:

| Function | Before | After |
|---|---|---|
| `roles_of` (agency.py) | `f["type"] != "classified-as"` | `not self.is_a(f["type"], "classified-as")` |
| `account_attestations` (dynamics.py) | `h["type"] in ("classified-as", "describes")` | `self.is_a_any(h["type"], ("classified-as", "describes"))` |
| `process_steps` (dynamics.py) | `f["type"] != "part-of"` | `not self.is_a(f["type"], "part-of")` |

**Shared mechanism.** `WorldModel.is_a_any(label, types)` sits beside the existing `is_a`. Both use the A0.2 lattice,
which is read from the schema (`sub!`), so they work at any depth, with no hard-coded lists.
- **Audit:** every other type test in `src/` already used the lattice (`AttestationRecord.kind` is the nearest core
  type), and the `isa!` queries only read a type's own label for mapping.
- **Unchanged:** roles in records were already core role names. No foundational schema category changed.

**Tests** (`tests/test_j_d0_profiles.py`):
- **Depths:** each function is tested with the core type, a profile subtype and a deeper subtype:
  - `classified-as`, `office-holding`, `acting-appointment`;
  - `classified-as`, `maintenance-kind`, `scheduled-maintenance-kind`, plus `describes`;
  - `part-of`, `step-of`, `protocol-step-of`.
- **Judgement intact:**
  - perspective: another source's unreviewed claim is hidden from the system but visible to that source;
  - valid time: an office that ended is excluded, as is a step that ended;
  - knowledge time: `as_of` before the claim excludes it;
  - worlds: a plan's snapshot does not see an acceptance recorded after its creation;
  - the attester filter still applies;
  - selective and full-load paths agree.
- **Inherited constraints:** the deeper subtype inherits its parent's slot. Two holders of one office give DISPUTED,
  judged and not refused at write time (D-D-5).

## 2. Profile packaging (D-D-9)
The smallest convention on top of the existing module mechanism. It is not a plugin framework, and has no
configuration files:
- **A profile** is a `Profile(name, version, schema, slots=(), vocabulary=())` registered in
  `worldmodel.profiles.PROFILES`, and installed with `WorldModel.install_profile(profile_or_name)`.
  - Its schema files live in `schema/profiles/<name>/`.
  - Its example worlds go in `src/worldmodel/examples/`, and its tests in `tests/`.
  - It is recorded like a core module, as `schema-module` `profile:<name>`. `profiles()` lists the installed profiles.
- **Requires** the full core (`CORE_MODULES`) and nothing else. A profile cannot name another profile's types, so
  there are no implicit cross-profile dependencies: it would fail when installed alone (tested).
- **Refused before commit** (the schema is defined and introspected inside its own uncommitted schema transaction).
  Refused profiles:
  - redeclare or extend any existing type: a core type, or another profile's (a collision is refused, never merged);
  - add a role or an attribute to an existing type;
  - let an existing type play an existing role;
  - declare slots on predicates they do not own;
  - use vocabulary ids not prefixed `<name>:`;
  - specialise one core role twice in one event type (D-D-6, a TypeDB 3.14.1 constraint);
  - are rejected by TypeDB itself (for example, a change that breaks a stored function's types).
- **What a profile may add:**
  - new types;
  - `plays` for the roles of its own relations;
  - `owns` on its own types;
  - slots on its own predicates;
  - prefixed seed concepts.
- **Consequences:**
  - core semantics are unchanged (tested on the full reference world);
  - each profile installs alone;
  - all profiles install together;
  - installation order cannot change meaning: the same schema, slots and lattice result in either order (tested);
  - a collision fails loudly.
- **Re-installing** the same version is a no-op; another version is refused (profiles are not replaced in place).
- **Atomic installation (LABS-1.023).**
  - Schema, seed vocabulary, slot declarations and the module record are written in **one schema transaction**:
    TypeDB 3.14.1 schema transactions also write data (verified). It commits only after every check passes.
  - A failure at any point (a refusal, a vocabulary id collision, an invalid slot, or the commit itself) leaves the
    database unchanged, and the profile is never reported as installed (all tested).
  - This replaces the D0 sequence, in which vocabulary, slots and the record were written after the schema commit.
    The D0 report's statement that "TypeDB cannot commit schema and data together" was wrong.

### Incomplete installation: detection and recovery
- `profiles()` lists only profiles with a module record. `profile_status(p)` returns:
  - "installed" when the record exists;
  - "absent" when none of the profile's declared types is in the schema;
  - "conflict" when some are present without a record.
- Since installation is atomic, `install_profile` never produces "conflict". It arises only from schema changed
  outside it (a manual `define`), or from another profile owning the same labels. `install_profile` then refuses
  with the colliding labels (tested).
- **Manual recovery** (no tool, by design):
  1. Find which types are present:
     `match { entity $t; } or { relation $t; } or { attribute $t; };`, compared with the profile's schema files.
  2. If they belong to another profile, the two profiles collide: rename the labels in the new profile. Profiles are
     never merged.
  3. If they came from a manual define of this profile's schema, and no data uses them, remove them in a schema
     transaction (`undefine` the `plays`/`owns` lines, then the types), and install again.
  4. If data already uses them, do not undefine. Record the decision before writing anything: there is no migration
     tool, and profiles are never replaced in place.
- Profiles still may not modify existing core types; the restriction is unchanged.

**Fixtures** (`tests/fixtures/profiles/`, registered in `tests/profile_fixtures.py`) are minimal schemas for the
installation and subtype tests only. They are not the D-1 to D-3 profiles. No domain profile is registered in
`PROFILES` yet.

## 3. Validation
- `tests/test_j_d0_profiles.py` (26 tests; 4 added in LABS-1.023 for atomic installation) covers:
  - each profile alone over the full core;
  - all together, in both orders, with the same snapshot, slots and lattice;
  - seven refusal cases with the schema unchanged;
  - a cross-profile collision;
  - a cross-profile dependency;
  - full-core requirement, re-install and version change;
  - core answers on the full gearbox reference world identical before and after installing all three profiles
    (`facts_about`, `roles_of`, `capable`, `process_steps`, `account_attestations`, `compare_measurements`, `where`,
    `changes`);
  - the subtype tests of section 1;
  - unchanged cardinality for core and profile events.
- **Core-protection run:** with `WM_PROFILES=1`, `tests/conftest.py` installs all three fixture profiles into every
  test database created with the full core, before the test writes anything. The whole suite then runs against
  profile-bearing databases.
- Results: section 4.

## 4. Results
| Run | Result |
|---|---|
| full suite, selective path, twice | 304 passed, 304 passed |
| full suite, full-load path, twice | 304 passed, 304 passed |
| core-protection (`WM_PROFILES=1`), selective | 304 passed |
| core-protection (`WM_PROFILES=1`), full load | 304 passed |
| leftover test databases | 0 |

In the first core-protection run, 5 failures were all in `test_j_d0_profiles.py` itself. Those tests check
installation on a bare core, so they cannot run on databases that already hold the profiles. They are now marked
`own_profiles`, and the switch leaves them alone. All 299 other tests passed with the profiles installed in that run
too.

**Performance** (`docs/core-0.4/bench-d0/README.md`):
- no material impact: identical query counts for every generic question, and latencies within noise;
- profiles add about 1% database size (schema);
- installing three profiles takes about 0.4 s (plan ceiling 5 s).
