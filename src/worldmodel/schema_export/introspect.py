"""Read a database's schema (LABS-1.024): the canonical text, and the independent answers TypeDB gives by query.

Nothing here writes to the target database. The text and the query answers are two views of one schema:
- the text (`schema()`) is declared-only and carries annotations and functions;
- the queries include inherited capabilities and carry no annotations (TypeDB 3.14.1 refuses to query annotations,
  REP254, and has no query for functions).
"""

from dataclasses import dataclass

from typedb.driver import TransactionType

from .. import typeql as q
from .parse import SchemaExportError

READ = TransactionType.READ
VALUE_TYPES = ("boolean", "integer", "double", "decimal", "string", "date", "datetime", "datetime-tz", "duration")


@dataclass
class Snapshot:
    database: str
    server_version: str
    text: str                  # schema(), exactly
    modules: dict              # module-name -> module-version, from the schema-module records (data)
    answers: dict              # the query reader's answers (see read_answers)
    data: frozenset = frozenset()   # module-data candidates: concept and functional-slot records (read_module_data)


def _label(row, var):
    return row.get(var).get_label()


def _rows(tx, query):
    return list(tx.query(query).resolve().as_concept_rows())


def read_answers(tx):
    """The schema as TypeDB answers it by query, as sets of labels (inherited capabilities included)."""
    kinds = {k: {_label(r, "t") for r in _rows(tx, f"match {k} $t;")} for k in ("entity", "relation", "attribute")}
    labels = set().union(*kinds.values())
    value_types = {}
    for vt in VALUE_TYPES:
        for r in _rows(tx, f"match attribute $a value {vt};"):
            value_types.setdefault(_label(r, "a"), set()).add(vt)
    return {
        "kinds": {label: k for k, ls in kinds.items() for label in ls},
        "sub": {(_label(r, "t"), _label(r, "s")) for r in _rows(tx, "match $t sub! $s;") if _label(r, "t") in labels},
        "owns": {(_label(r, "t"), _label(r, "a")) for r in _rows(tx, "match $t owns $a;")},
        "plays": {(_label(r, "t"), _label(r, "r")) for r in _rows(tx, "match $t plays $r;")},
        "relates": {(_label(r, "t"), _label(r, "r")) for r in _rows(tx, "match relation $t; $t relates $r;")},
        "role_parents": {(_label(r, "r"), _label(r, "p"))
                         for r in _rows(tx, "match relation $t; $t relates $r; $r sub! $p;")},
        "value_types": {a: sorted(v) for a, v in value_types.items()},
    }


def read_modules(tx, kinds):
    """The schema-module records, if the database has the type."""
    if kinds.get("schema-module") != "entity":
        return {}
    out = {}
    for r in _rows(tx, "match $m isa schema-module, has module-name $n, has module-version $v;"):
        name, version = q.opt(r, "n"), q.opt(r, "v")
        if name in out and out[name] != version:
            raise SchemaExportError("a module is recorded twice with different versions", [name])
        out[name] = version
    return out


def read_module_data(tx, kinds):
    """Every concept record (kind, id, name) and functional-slot record (id, predicate, key roles, value role), as
    hashable tuples. Which of them a module wrote is decided by replay (attribution.py), never from ids or names."""
    out = set()
    if kinds.get("concept") == "entity":
        for r in _rows(tx, "match $c isa concept, has wm-id $id, has name $n; $c isa! $t;"):
            out.add(("concept", _label(r, "t"), q.opt(r, "id"), q.opt(r, "n")))
    if kinds.get("functional-slot") == "entity":
        slots = {}
        for r in _rows(tx, """match $s isa functional-slot, has slot-id $id, has slot-predicate $p,
                has value-role $v;"""):
            slots[q.opt(r, "id")] = [q.opt(r, "p"), q.opt(r, "v"), set()]
        for r in _rows(tx, "match $s isa functional-slot, has slot-id $id, has slot-role $k;"):
            slots[q.opt(r, "id")][2].add(q.opt(r, "k"))
        out |= {("slot", i, p, tuple(sorted(k)), v) for i, (p, v, k) in slots.items()}
    return frozenset(out)


def snapshot(driver, database):
    """Read the schema text, the query answers and the module records of one database, consistently: the text is
    read before and after the read transaction, and must not change."""
    if not driver.databases.contains(database):
        raise SchemaExportError(f"database {database!r} does not exist")
    db = driver.databases.get(database)
    before = db.schema()
    with driver.transaction(database, READ) as tx:
        answers = read_answers(tx)
        modules = read_modules(tx, answers["kinds"])
        data = read_module_data(tx, answers["kinds"])
    if db.schema() != before:
        raise SchemaExportError("the schema changed while it was being read; export again")
    return Snapshot(database, str(driver.server_version()), before, modules, answers, data)
