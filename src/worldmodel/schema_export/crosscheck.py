"""Check the parsed schema text against the database (LABS-1.024, E-1; LABS-1.033 schema fidelity).

Two independent checks, both required:
1. **Query cross-check.** The declarations parsed from the text, inherited down the supertype graph, must equal
   TypeDB's own query answers exactly: types and kinds, direct supertypes, owns, plays, relates, role
   specialisations and value types. Any difference fails the export.
2. **Round trip.** The rendered text, defined into an empty temporary database, must give back exactly the target's
   `schema()`. This is the only check on annotations and functions, which TypeDB cannot answer by query.
"""

import uuid

from typedb.driver import TransactionType

from .introspect import READ, read_answers
from .parse import SchemaExportError, render_schema

SCHEMA = TransactionType.SCHEMA


class Lattice:
    """Declared and inherited capabilities computed from the parsed text alone. Each inherited capability names the
    type that declares it (`from`)."""

    def __init__(self, parsed):
        self.parsed = parsed
        self.kind = {t.label: t.kind for t in parsed.types.values()}
        self.parent = {}
        for t in parsed.types.values():
            subs = [d.target for d in t.declarations if d.keyword == "sub"]
            if len(subs) > 1:
                raise SchemaExportError("a type has two supertypes", [t.label])
            if subs:
                self.parent[t.label] = subs[0]
        missing = sorted({p for p in self.parent.values() if p not in self.kind})
        if missing:
            raise SchemaExportError("supertypes missing from the schema", missing)

    def chain(self, label):
        """The supertypes of a type, nearest first."""
        out, seen = [], {label}
        while label in self.parent:
            label = self.parent[label]
            if label in seen:
                raise SchemaExportError("a cycle in the supertype graph", [label])
            seen.add(label)
            out.append(label)
        return out

    def declared(self, label, keyword):
        return [d for d in self.parsed.types[label].declarations if d.keyword == keyword]

    def capabilities(self, label, keyword):
        """[(target, from_type, declaration)] for owns / plays, nearest declaration first; for relates the target is
        the scoped role `relation:role`."""
        out, seen = [], set()
        for owner in [label] + self.chain(label):
            for d in self.declared(owner, keyword):
                target = f"{owner}:{d.target}" if keyword == "relates" else d.target
                if target not in seen:
                    seen.add(target)
                    out.append((target, owner, d))
        return out

    def role_parent(self, relation, d):
        """The scoped role a `relates x as y` specialises: role y of the nearest supertype relation declaring it."""
        for ancestor in self.chain(relation):
            if any(x.target == d.specialises for x in self.declared(ancestor, "relates")):
                return f"{ancestor}:{d.specialises}"
        raise SchemaExportError("a specialised role has no parent in the supertype chain",
                                [f"{relation} relates {d.target} as {d.specialises}"])

    def value_type(self, label):
        for owner in [label] + self.chain(label):
            vs = self.declared(owner, "value")
            if vs:
                return vs[0].target, owner
        return None, None

    def as_answers(self):
        """The same shape as introspect.read_answers, computed from the text."""
        labels = list(self.kind)
        out = {"kinds": dict(self.kind), "sub": set(self.parent.items()), "owns": set(), "plays": set(),
               "relates": set(), "role_parents": set(), "value_types": {}}
        for label in labels:
            out["owns"] |= {(label, a) for a, _, _ in self.capabilities(label, "owns")}
            out["plays"] |= {(label, r) for r, _, _ in self.capabilities(label, "plays")}
            if self.kind[label] == "relation":
                out["relates"] |= {(label, r) for r, _, _ in self.capabilities(label, "relates")}
                for d in self.declared(label, "relates"):
                    if d.specialises:
                        out["role_parents"].add((f"{label}:{d.target}", self.role_parent(label, d)))
            if self.kind[label] == "attribute":
                vt, _ = self.value_type(label)
                if vt:
                    out["value_types"][label] = [vt]
        return out


def compare_answers(from_text, from_queries):
    """Every difference between two answer sets, as readable lines (empty: they agree exactly)."""
    problems = []
    for key in ("kinds", "sub", "owns", "plays", "relates", "role_parents", "value_types"):
        a, b = from_text[key], from_queries[key]
        if isinstance(a, dict):
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k):
                    problems.append(f"{key} {k}: schema text {a.get(k)!r}, query {b.get(k)!r}")
        else:
            problems += [f"{key} {x}: in the schema text only" for x in sorted(a - b)]
            problems += [f"{key} {x}: in the query answers only" for x in sorted(b - a)]
    return problems


def cross_check(lattice, answers):
    """Raise unless the text, with inheritance, equals the database's query answers exactly. Returns counts."""
    computed = lattice.as_answers()
    problems = compare_answers(computed, answers)
    if problems:
        raise SchemaExportError("the schema text and the database's query answers disagree", problems)
    return {k: len(v) for k, v in computed.items()}


def temporary_name(prefix):
    return f"{prefix}{uuid.uuid4().hex[:10]}"


def round_trip(driver, parsed, expected_text, prefix="wm-export-tmp-"):
    """Define the rendered schema into an empty temporary database (always deleted) and require that its schema()
    equals `expected_text` exactly, and that its query answers equal those of the text. Returns a summary."""
    text = render_schema(parsed)
    name = temporary_name(prefix)
    driver.databases.create(name)
    try:
        if text.strip() not in ("", "define"):
            with driver.transaction(name, SCHEMA) as tx:
                tx.query(text).resolve()
                tx.commit()
        again = driver.databases.get(name).schema()
        if again != expected_text:
            at = next((k for k, (a, b) in enumerate(zip(again, expected_text)) if a != b),
                      min(len(again), len(expected_text)))
            raise SchemaExportError("round trip: the exported TypeQL does not reproduce the database's schema",
                                    [f"first difference at character {at}: "
                                     f"exported {again[max(0, at - 30):at + 30]!r}, "
                                     f"database {expected_text[max(0, at - 30):at + 30]!r}"])
        with driver.transaction(name, READ) as tx:
            copy_answers = read_answers(tx)
        problems = compare_answers(Lattice(parsed).as_answers(), copy_answers)
        if problems:
            raise SchemaExportError("round trip: the copy's query answers differ", problems)
        return {"identical_schema_text": True, "characters": len(again)}
    finally:
        if driver.databases.contains(name):
            driver.databases.get(name).delete()
