"""WorldModel (Core 0.3): World Ontology v0.2 on TypeDB 3.

Division of labour (v0.2 §8.1):
- TypeDB: kinds and the roles they may play; arity of attestations and acceptances; unique ids and proposition keys;
  allowed values; selective retrieval from a bound subject; transitive part-of (function `parts_in`).
- Python (semantics.py): canonical keys (keys.py), acceptance ordering, perspective views, world inheritance, truth at a
  time, identity closure, answer statuses.
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from typedb.driver import Credentials, DriverOptions, DriverTlsConfig, TransactionType, TypeDB

from . import typeql as q
from .keys import as_ids, check_id, proposition_key
from .semantics import Window

READ, WRITE, SCHEMA = TransactionType.READ, TransactionType.WRITE, TransactionType.SCHEMA
SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schema"
MODULES = {"core": ("0.3.0", ["core/core-0.3.tql"])}
SYSTEM = "system"                     # the system's own agent: the default attester and perspective
KINDS = ("physical-object", "social-object", "place", "information-object", "occurrence",
         "category", "social-role", "quality-kind", "clock", "spatial-frame", "unit")
QUALITY_PARAMS = ("lower", "upper", "coverage-level")


def connect(address=None):
    return TypeDB.driver(address or os.environ.get("WM_TYPEDB_ADDRESS", "127.0.0.1:1735"),
                         Credentials(os.environ.get("WM_TYPEDB_USERNAME", "admin"),
                                     os.environ.get("WM_TYPEDB_PASSWORD", "password")),
                         DriverOptions(DriverTlsConfig.disabled()))


def utcnow():
    return datetime.now(timezone.utc)


def _window(value):
    if value is None or isinstance(value, Window):
        return value
    if isinstance(value, datetime):
        return Window.at(value)
    if isinstance(value, tuple) and len(value) == 2:
        return Window(*value)
    raise TypeError(f"expected a datetime, a (earliest, latest) tuple or a Window, got {value!r}")


class WorldModel:
    def __init__(self, driver, database, clock=utcnow, selective=True):
        self.driver, self.database, self.clock = driver, database, clock
        self.selective = selective
        self.stats = {"queries": 0, "attestations": 0}
        self._last_recorded = None
        self._types = None

    # ---- setup -----------------------------------------------------------------------------------------------------
    @classmethod
    def create(cls, database, driver=None, modules=("core",), clock=utcnow, replace=False):
        """Create the database, load schema modules in order and register the system agent."""
        driver = driver or connect()
        if driver.databases.contains(database):
            if not replace:
                raise ValueError(f"database {database!r} exists (use replace=True)")
            driver.databases.get(database).delete()
        driver.databases.create(database)
        wm = cls(driver, database, clock)
        for name in modules:
            wm.install_module(name)
        wm.add_entity("social-object", "system reasoner", id=SYSTEM)
        return wm

    @classmethod
    def open(cls, database, driver=None, clock=utcnow):
        return cls(driver or connect(), database, clock)

    def install_module(self, name, files=None, version=None):
        version, files = (version, files) if files else MODULES[name]
        with self.driver.transaction(self.database, SCHEMA) as tx:
            for f in files:
                tx.query((SCHEMA_DIR / f).read_text()).resolve()
            tx.commit()
        with self.driver.transaction(self.database, WRITE) as tx:
            q.run(tx, "insert $m isa schema-module, has module-name == $n, has module-version == $v;",
                  {"n": name, "v": version})
            tx.commit()
        self._types = None

    def modules(self):
        with self.driver.transaction(self.database, READ) as tx:
            return {q.opt(r, "n"): q.opt(r, "v") for r in
                    q.rows(tx, "match $m isa schema-module, has module-name $n, has module-version $v;")}

    def proposition_types(self):
        """Concrete proposition types in the installed schema (core and profiles), by introspection."""
        if self._types is None:
            with self.driver.transaction(self.database, READ) as tx:
                self._types = {r.get("t").get_label() for r in q.rows(tx, "match relation $t; $t sub proposition;")}
            self._types.discard("proposition")
        return self._types

    # ---- writing: things and worlds ---------------------------------------------------------------------------
    def _now(self):
        now = self.clock()
        if self._last_recorded is not None and now < self._last_recorded:
            raise ValueError("the clock went backwards: transaction time must not decrease")
        self._last_recorded = now
        return now

    @staticmethod
    def _mint(prefix):
        return f"{prefix}:{uuid.uuid4().hex[:16]}"

    def add_entity(self, kind, name, alt_names=(), description=None, id=None):
        """A particular (physical-object, social-object, place, information-object, occurrence), a concept (category,
        social-role, quality-kind) or a reference system (clock, spatial-frame, unit). Profiles may add subtypes."""
        rid = check_id(id or self._mint(kind))
        attrs = ", has name == $n" + "".join(f", has alt-name == $a{i}" for i in range(len(alt_names)))
        params = {"id": rid, "n": name, **{f"a{i}": a for i, a in enumerate(alt_names)}}
        if description:
            attrs += ", has description == $d"
            params["d"] = description
        with self.driver.transaction(self.database, WRITE) as tx:
            q.run(tx, f"insert $x isa {q.label(kind)}, has wm-id == $id{attrs};", params)
            tx.commit()
        return rid

    def create_world(self, name, kind="actual", base=None, branch_at=None, knowledge_at=None, id=None):
        """A world (actual, hypothetical or simulated). A variant names its base, the valid time it branches at, and
        the base knowledge it inherits (`knowledge_at`, a transaction time; default now; never in the future)."""
        wid = check_id(id or self._mint("world"))
        with self.driver.transaction(self.database, WRITE) as tx:
            q.run(tx, "insert $w isa world, has wm-id == $id, has name == $n, has world-kind == $k;",
                  {"id": wid, "n": name, "k": kind})
            if base is not None:
                if branch_at is None:
                    raise ValueError("a variant world needs branch_at")
                rec = self._now()
                if knowledge_at is not None and knowledge_at > rec:
                    raise ValueError("knowledge_at cannot be later than now: a snapshot cannot include future knowledge")
                q.run(tx, """match $b isa world, has wm-id == $b_id; $v isa world, has wm-id == $v_id;
                    insert branching (base: $b, variant: $v), has branch-at == $at, has knowledge-at == $kat,
                    has recorded-at == $rec;""", {"b_id": base, "v_id": wid, "at": branch_at,
                                                  "kat": knowledge_at or rec, "rec": rec})
            tx.commit()
        return wid

    def find(self, name):
        """Ids of particulars and concepts whose name or alt-name equals `name`. Every match, never resolved."""
        with self.driver.transaction(self.database, READ) as tx:
            return sorted({q.opt(r, "id") for r in q.rows(tx, """match $x has wm-id $id;
                { $x isa particular; } or { $x isa concept; };
                { $x has name == $n; } or { $x has alt-name == $n; };""", {"n": name})})

    # ---- writing: content --------------------------------------------------------------------------------------
    def _kinds_of(self, tx, ids):
        """Exact type of each id among particulars, concepts, reference systems and event descriptions."""
        out = {}
        for i in sorted(set(ids)):
            for r in q.rows(tx, """match $x has wm-id == $id; $x isa! $t;
                { $x isa particular; } or { $x isa concept; } or { $x isa reference-system; } or { $x isa event; };""",
                            {"id": i}):
                out[i] = r.get("t").get_label()
        missing = set(ids) - set(out)
        if missing:
            raise ValueError(f"no particular, concept, reference system or event description with id {sorted(missing)}")
        return out

    def _players(self, tx, roles, prefix="p"):
        """(match patterns, role links, params) binding every role player by id, with its exact type."""
        kinds = self._kinds_of(tx, [x for v in roles.values() for x in as_ids(v)])
        patterns, links, params = [], [], {}
        for i, (role, ids) in enumerate(sorted(roles.items())):
            for j, rid in enumerate(as_ids(ids)):
                v = f"{prefix}{i}_{j}"
                patterns.append(f"${v} isa {q.label(kinds[rid])}, has wm-id == ${v}_id;")
                links.append(f"{q.label(role)}: ${v}")
                params[f"{v}_id"] = rid
        return " ".join(patterns), ", ".join(links), params

    def _ensure_proposition(self, tx, type, roles, params=None):
        """The proposition for this content, inserted if it does not exist yet. Returns its key."""
        if type not in self.proposition_types():
            raise ValueError(f"{type!r} is not a proposition type in the installed schema")
        params = {k: v for k, v in (params or {}).items() if v is not None}
        unknown = set(params) - set(QUALITY_PARAMS)
        if unknown:
            raise ValueError(f"unknown proposition parameters {sorted(unknown)}")
        key = proposition_key(type, roles, params)
        if q.rows(tx, "match $p isa proposition, has proposition-key == $k;", {"k": key}):
            return key
        patterns, links, values = self._players(tx, roles)
        attrs = "".join(f", has {q.label(name)} == $v_{name.replace('-', '_')}" for name in sorted(params))
        values.update({f"v_{name.replace('-', '_')}": float(v) for name, v in params.items()})
        values["key"] = key
        q.run(tx, f"match {patterns} insert $p isa {q.label(type)} ({links}), has proposition-key == $key{attrs};",
              values)
        return key

    def proposition(self, type, roles, params=None):
        """Store the content (once) and return its canonical key. Content alone asserts nothing."""
        with self.driver.transaction(self.database, WRITE) as tx:
            key = self._ensure_proposition(tx, type, roles, params)
            tx.commit()
        return key

    def describe_event(self, roles, description=None, id=None):
        """An event description: one account of an occurrence, with its participants. Identified by id, not by
        content: two descriptions with the same participants are two descriptions. Asserts nothing by itself."""
        eid = check_id(id or self._mint("event"))
        with self.driver.transaction(self.database, WRITE) as tx:
            patterns, links, values = self._players(tx, roles)
            values["id"] = eid
            extra = ""
            if description:
                extra, values["d"] = ", has description == $d", description
            q.run(tx, f"match {patterns} insert $e isa event ({links}), has wm-id == $id{extra};", values)
            tx.commit()
        return eid

    # ---- reading: content ----------------------------------------------------------------------------------------
    def content(self, key_or_id):
        """{type, roles, params} of a stored proposition (by key) or event description (by id)."""
        with self.driver.transaction(self.database, READ) as tx:
            rows = q.rows(tx, """match { $c isa proposition, has proposition-key == $k; } or
                { $c isa event, has wm-id == $k; }; $c isa! $t;""", {"k": key_or_id})
            if not rows:
                return None
            out = {"type": rows[0].get("t").get_label(), "roles": {}, "params": {}}
            for r in q.rows(tx, """match { $c isa proposition, has proposition-key == $k; } or
                { $c isa event, has wm-id == $k; }; $c links ($role: $x); $x has wm-id $xid;""", {"k": key_or_id}):
                out["roles"].setdefault(r.get("role").get_label().split(":")[-1], []).append(q.opt(r, "xid"))
            for name in QUALITY_PARAMS:
                for r in q.rows(tx, f"match $c isa proposition, has proposition-key == $k, has {name} $v;",
                                {"k": key_or_id}):
                    out["params"][name] = q.opt(r, "v")
        out["roles"] = {k: sorted(v) for k, v in out["roles"].items()}
        return out

    def count(self, type):
        with self.driver.transaction(self.database, READ) as tx:
            return len(q.rows(tx, f"match $x isa {q.label(type)};"))
