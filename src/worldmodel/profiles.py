"""Domain profiles (Core 0.4 Stage D groundwork, LABS-1.022; decisions D-D-1, D-D-6, D-D-9).

A profile is domain vocabulary installed after the full core, through the existing module mechanism:
- **schema**: TypeQL files that only *add*: new types (sortals, proposition and event subtypes, relations, attributes),
  `plays` declarations for the roles of the profile's own relations, and `owns` on the profile's own types;
- **slots**: functional constraints, declared as data, on the profile's own proposition types only;
- **vocabulary**: seed concepts (categories, roles, capabilities...), with ids prefixed `<profile>:`.

Rules, checked by `install_profile` before anything is committed:
- the profile requires the full core (CORE_MODULES) and nothing else: **no cross-profile dependencies**, so every
  profile installs on its own, and any set of profiles installs in any order;
- it must not redeclare or extend any existing type (core or another profile's). A collision is refused, never merged,
  so **installation order cannot silently change meaning**;
- it must not add roles or attributes to existing types, or declare slots on existing predicates, so **core semantics
  are unchanged**;
- an event type may specialise a given core role at most once (D-D-6: a TypeDB 3.14.1 cardinality constraint, not an
  ontological rule).

Ownership: a profile's schema lives in `schema/profiles/<name>/`; its registry entry is in PROFILES below; its example
worlds are in `src/worldmodel/examples/`; its tests are in `tests/`. No domain profile is registered yet (Stage D
domain work is not authorised); the tests use minimal fixtures under `tests/fixtures/profiles/`.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from typedb.driver import TypeDBDriverException

from . import typeql as q

PROFILE_PREFIX = "profile:"


@dataclass(frozen=True)
class Profile:
    name: str                        # lower-case; the module is recorded as "profile:<name>"
    version: str
    schema: tuple                    # TypeQL files owned by the profile
    slots: tuple = ()                # (predicate, key roles, value role): predicates must be the profile's own types
    vocabulary: tuple = ()           # (concept kind, id, name): ids must start with "<name>:"

    @property
    def module(self):
        return PROFILE_PREFIX + self.name


PROFILES = {}                        # name -> Profile; domain profiles are registered here (none yet)


class ProfileError(ValueError):
    """A profile was refused; nothing was committed."""


_DECLARED = re.compile(r"(?:^|;|\bdefine\b)\s*(?:entity|relation|attribute)\s+([a-z][a-z0-9-]*)", re.M)


def _declared_labels(text):
    """Type labels a TypeQL schema text declares (`entity x`, `relation x`, `attribute x`), comments removed."""
    return set(_DECLARED.findall(re.sub(r"#[^\n]*", "", text)))


def schema_snapshot(tx):
    """The schema as sets: types, (relation, role) pairs, (type, role) plays, (type, attribute) owns, and the parent
    of each role (for specialisations). Inherited capabilities are included, as TypeDB reports them."""
    def lab(r, v):
        return r.get(v).get_label()
    return {
        "types": frozenset(lab(r, "t") for r in q.rows(tx, "match { entity $t; } or { relation $t; } or { attribute $t; };")),
        "relates": frozenset((lab(r, "t"), lab(r, "r")) for r in q.rows(tx, "match relation $t; $t relates $r;")),
        "plays": frozenset((lab(r, "t"), lab(r, "r")) for r in q.rows(tx, "match $t plays $r;")),
        "owns": frozenset((lab(r, "t"), lab(r, "a")) for r in q.rows(tx, "match $t owns $a;")),
        "role_parents": frozenset((lab(r, "r"), lab(r, "p")) for r in q.rows(tx, "match relation $t; $t relates $r; $r sub! $p;")),
    }


def _violations(profile, declared, before, after):
    """Why a profile's schema change is not purely additive vocabulary of its own (empty: acceptable)."""
    new = after["types"] - before["types"]
    out = []
    if before["types"] - after["types"]:
        out.append(f"removes types {sorted(before['types'] - after['types'])}")
    existing = sorted(declared - new)
    if existing:
        out.append(f"redeclares existing types {existing} (core or another profile's; profiles never extend them)")
    for t, r in sorted(after["relates"] - before["relates"]):
        if t not in new:
            out.append(f"adds role {r} to existing relation {t}")
    for t, r in sorted(after["plays"] - before["plays"]):
        if t not in new and r.split(":")[0] not in new:
            out.append(f"lets existing type {t} play existing role {r}")
    for t, a in sorted(after["owns"] - before["owns"]):
        if t not in new:
            out.append(f"adds attribute {a} to existing type {t}")
    own_roles = {}
    for role, parent in after["role_parents"] - before["role_parents"]:
        rel = role.split(":")[0]
        if rel in new:
            own_roles.setdefault((rel, parent), []).append(role)
    for (rel, parent), roles in sorted(own_roles.items()):
        if len(roles) > 1:
            out.append(f"{rel} specialises {parent} {len(roles)} times ({sorted(roles)}): in TypeDB 3.14.1 they share "
                       f"its cardinality, so an event naming both is rejected (D-D-6); give the extra participant a "
                       f"role of its own")
    return new, out


class ProfileMixin:
    def profiles(self):
        """{profile name: version} of the profiles installed in this database."""
        return {m[len(PROFILE_PREFIX):]: v for m, v in self.modules().items() if m.startswith(PROFILE_PREFIX)}

    def install_profile(self, profile):
        """Install a profile after the full core (see the module docstring for the rules). Re-installing the same
        version is a no-op; another version is refused. Returns the profile's new type labels. The schema is checked
        in its own uncommitted schema transaction and refused (ProfileError) before anything is committed. TypeDB
        cannot commit schema and data together, so vocabulary, slots and finally the module record follow; the
        profile counts as installed only once its record exists, and a retry after a failure there is refused as a
        partial install."""
        from .model import CORE_MODULES, READ, SCHEMA, WRITE
        if isinstance(profile, str):
            profile = PROFILES[profile]
        installed = self.modules()
        if profile.module in installed:
            if installed[profile.module] == profile.version:
                return []
            raise ProfileError(f"profile {profile.name!r} {installed[profile.module]} is installed; "
                               f"{profile.version} would change it (profiles are never replaced in place)")
        missing = [m for m in CORE_MODULES if m not in installed]
        if missing:
            raise ProfileError(f"profile {profile.name!r} needs the full core; missing modules {missing}")
        bad_ids = [i for _, i, _ in profile.vocabulary if not i.startswith(profile.name + ":")]
        if bad_ids:
            raise ProfileError(f"vocabulary ids must start with {profile.name + ':'!r}: {bad_ids}")
        text = "\n".join(Path(f).read_text() for f in profile.schema)
        declared = _declared_labels(text)
        with self.driver.transaction(self.database, READ) as tx:
            before = schema_snapshot(tx)
        with self.driver.transaction(self.database, SCHEMA) as tx:
            try:
                for f in profile.schema:
                    tx.query(Path(f).read_text()).resolve()
                after = schema_snapshot(tx)          # TypeDB re-checks stored functions here as well
            except TypeDBDriverException as e:
                raise ProfileError(f"profile {profile.name!r} refused: TypeDB rejected its schema: "
                                   + " ".join(str(e).split())[:400]) from None
            new, problems = _violations(profile, declared, before, after)
            if not new and not problems:
                problems = ["adds no types: its schema is already present without its module record "
                            "(a partial install) or it is empty"]
            stray = sorted({p for p, _, _ in profile.slots} - new)
            if stray:
                problems.append(f"declares slots on types it does not own: {stray}")
            if problems:
                raise ProfileError(f"profile {profile.name!r} refused: " + "; ".join(problems))
            tx.commit()
        self._types = self._prop_ids = self._lattice = self._slots = None
        for kind, cid, name in profile.vocabulary:
            self.add_entity(kind, name, id=cid)
        for predicate, key_roles, value_role in profile.slots:
            self.declare_slot(predicate, key_roles, value_role)
        with self.driver.transaction(self.database, WRITE) as tx:      # last: installed only when complete
            q.run(tx, "insert $m isa schema-module, has module-name == $n, has module-version == $v;",
                  {"n": profile.module, "v": profile.version})
            tx.commit()
        return sorted(new)
