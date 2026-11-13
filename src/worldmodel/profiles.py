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

Installation is atomic: schema, vocabulary, slots and the module record commit in one schema transaction.

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


def _core_role(role, role_parents, core_labels):
    """The core role a scoped role specialises (its own name if it specialises none), as the lattice computes it."""
    parents = dict(role_parents)
    r = role
    while r.split(":")[0] not in core_labels and r in parents:
        r = parents[r]
    return (r if r.split(":")[0] in core_labels else role).split(":")[-1]


def _slot_problems(profile, new, after, core_labels):
    """Slot declarations must name the profile's own proposition types and their (core-named) roles."""
    out = []
    stray = sorted({p for p, _, _ in profile.slots} - new)
    if stray:
        out.append(f"declares slots on types it does not own: {stray}")
    for predicate, key_roles, value_role in profile.slots:
        if predicate in stray:
            continue
        roles = {_core_role(r, after["role_parents"], core_labels) for t, r in after["relates"] if t == predicate}
        keys = set(key_roles)
        if not roles:
            out.append(f"slot predicate {predicate!r} is not a relation")
        elif not keys or (keys | {value_role}) - roles or value_role in keys:
            out.append(f"invalid slot for {predicate!r}: key roles {sorted(keys)}, value role {value_role!r} "
                       f"(roles: {sorted(roles)})")
    return out


class ProfileMixin:
    def profiles(self):
        """{profile name: version} of the profiles installed in this database."""
        return {m[len(PROFILE_PREFIX):]: v for m, v in self.modules().items() if m.startswith(PROFILE_PREFIX)}

    def profile_status(self, profile):
        """"installed" (its module record exists), "absent" (none of its declared types is in the schema), or
        "conflict" (some of its types are in the schema but it has no record). install_profile is atomic, so it never
        leaves the last state; it arises only from schema changed outside install_profile (a manual define), or from
        another profile owning the same labels. See docs/core-0.4/stage-d0.md, "Incomplete installation"."""
        if isinstance(profile, str):
            profile = PROFILES[profile]
        if profile.module in self.modules():
            return "installed"
        declared = _declared_labels("\n".join(Path(f).read_text() for f in profile.schema))
        with self._reading() as tx:
            present = declared & schema_snapshot(tx)["types"]
        return "conflict" if present else "absent"

    def install_profile(self, profile):
        """Install a profile after the full core (see the module docstring for the rules). Re-installing the same
        version is a no-op; another version is refused. Returns the profile's new type labels.

        **Atomic (LABS-1.023).** The schema, its seed vocabulary, its slot declarations and the module record are
        written in **one schema transaction** (TypeDB 3.14.1 schema transactions also write data) and committed only
        after every check passed, so a profile is either completely installed and recorded, or not at all. Refusals
        raise ProfileError; any failure, including at commit, leaves the database unchanged."""
        from .model import CORE_LABELS, CORE_MODULES
        from .keys import check_new_id
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
        for _, i, _ in profile.vocabulary:
            check_new_id(i)
        text = "\n".join(Path(f).read_text() for f in profile.schema)
        declared = _declared_labels(text)
        try:
            with self.operation(schema=True) as op:       # one schema operation (LABS-1.023; DI-8 operations)
                tx = op.tx
                before = schema_snapshot(tx)
                try:
                    for f in profile.schema:
                        tx.query(Path(f).read_text()).resolve()
                    after = schema_snapshot(tx)          # TypeDB re-checks stored functions here as well
                except TypeDBDriverException as e:
                    raise ProfileError(f"profile {profile.name!r} refused: TypeDB rejected its schema: "
                                       + " ".join(str(e).split())[:400]) from None
                new, problems = _violations(profile, declared, before, after)
                if not new and not problems:
                    problems = ["adds no types: its schema is empty"]
                problems += _slot_problems(profile, new, after, CORE_LABELS)
                concepts = {t for t, r in after["plays"] if r == "classified-as:class"}   # concept types, incl. new ones
                bad_kinds = sorted({k for k, _, _ in profile.vocabulary if k not in concepts})
                if bad_kinds:
                    problems.append(f"vocabulary kinds must be concept types: {bad_kinds}")
                if problems:
                    raise ProfileError(f"profile {profile.name!r} refused: " + "; ".join(problems))
                for kind, cid, name in profile.vocabulary:
                    q.run(tx, f"insert $c isa {q.label(kind)}, has wm-id == $id, has name == $n;", {"id": cid, "n": name})
                for predicate, key_roles, value_role in profile.slots:
                    key_roles = tuple(sorted(set(key_roles)))
                    attrs = "".join(f", has slot-role == $k{i}" for i in range(len(key_roles)))
                    q.run(tx, f"""insert $s isa functional-slot, has slot-id == $id, has slot-predicate == $p,
                        has value-role == $v{attrs};""",
                          {"id": f"{predicate}|{','.join(key_roles)}|{value_role}", "p": predicate, "v": value_role,
                           **{f"k{i}": r for i, r in enumerate(key_roles)}})
                q.run(tx, "insert $m isa schema-module, has module-name == $n, has module-version == $v;",
                      {"n": profile.module, "v": profile.version})
        except TypeDBDriverException as e:
            raise ProfileError(f"profile {profile.name!r} not installed (nothing committed): "
                               + " ".join(str(e).split())[:400]) from None
        self._reset_caches()
        return sorted(new)
