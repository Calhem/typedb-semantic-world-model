"""WorldModel (Core 0.3): World Ontology v0.2 on TypeDB 3.

Division of labour (v0.2 §8.1):
- TypeDB: kinds and the roles they may play; arity of attestations and acceptances; unique ids and proposition keys;
  allowed values; selective retrieval from a bound subject; transitive part-of (function `parts_in`).
- Python (semantics.py): canonical keys (keys.py), acceptance ordering, perspective views, world inheritance, truth at a
  time, identity closure, answer statuses.
"""

import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from typedb.driver import Credentials, DriverOptions, DriverTlsConfig, TransactionType, TypeDB

from . import typeql as q
from . import keys
from .keys import as_ids, check_new_id, proposition_key
from .semantics import (Answer, AttestationRecord, Identity, Replacement, Status, Window, acceptance_state,
                        answer_status, certainly_before, superseded, usable, verdict)

READ, WRITE, SCHEMA = TransactionType.READ, TransactionType.WRITE, TransactionType.SCHEMA
SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schema"
MODULES = {"core": ("0.3.0", ["core/core-0.3.tql"]),
           "core-0.4-a0": ("0.4.0-a0", ["core/core-0.4-a0.tql"])}      # Stage A0 groundwork (LABS-1.002)
DEFAULT_MODULES = ("core", "core-0.4-a0")
CORE_MODULES = ("core", "core-0.4-a0")       # their types are the foundational (core) types; the rest are profiles


def _core_labels():
    """Labels of the types the core modules define, read from the schema files (the single source of truth)."""
    labels = set()
    for name in CORE_MODULES:
        for f in MODULES[name][1]:
            labels |= set(re.findall(r"^\s*(?:entity|relation|attribute)\s+([a-z][a-z0-9-]*)",
                                     (SCHEMA_DIR / f).read_text(), re.M))
    return frozenset(labels)


CORE_LABELS = _core_labels()
SYSTEM = "system"                     # the system's own agent: the default attester and perspective
KINDS = ("physical-object", "social-object", "place", "information-object", "occurrence",
         "category", "social-role", "quality-kind", "clock", "spatial-frame", "unit")
QUALITY_PARAMS = ("lower", "upper", "coverage-level")
FUNCTIONAL = {"located-at": ("located", "place")}   # one value at a time per key role (profile metadata in v0.2)
VARIANT_KINDS = ("hypothetical", "simulated")


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


class PropositionIdCollision(ValueError):
    """Two different canonical keys derived the same proposition id. Raised instead of merging their content."""

    def __init__(self, pid, key, existing):
        super().__init__(f"proposition id {pid} already belongs to {existing!r}; refusing {key!r}")
        self.pid, self.key, self.existing = pid, key, existing


class WorldModel:
    def __init__(self, driver, database, clock=utcnow, selective=True):
        self.driver, self.database, self.clock = driver, database, clock
        self.selective = selective
        self.stats = {"queries": 0, "attestations": 0}
        self._last_recorded = None
        self._types = None
        self._prop_ids = None
        self._lattice = None

    # ---- setup -----------------------------------------------------------------------------------------------------
    @classmethod
    def create(cls, database, driver=None, modules=DEFAULT_MODULES, clock=utcnow, replace=False):
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
                tx.query((Path(f) if Path(f).is_absolute() else SCHEMA_DIR / f).read_text()).resolve()
            tx.commit()
        with self.driver.transaction(self.database, WRITE) as tx:
            q.run(tx, "insert $m isa schema-module, has module-name == $n, has module-version == $v;",
                  {"n": name, "v": version})
            tx.commit()
        self._types = None
        self._prop_ids = None
        self._lattice = None

    def has_proposition_ids(self):
        """True when the A0 module is installed (propositions own a `wm-id` key)."""
        if self._prop_ids is None:
            self._prop_ids = "core-0.4-a0" in self.modules()
        return self._prop_ids

    def upgrade_to_a0(self):
        """Upgrade an existing Core 0.3 database in place: give every proposition its deterministic id, then make the
        id a key. Three steps, because TypeDB rejects adding @key while instances lack the attribute (CNT5)."""
        if self.has_proposition_ids():
            return 0
        with self.driver.transaction(self.database, SCHEMA) as tx:
            tx.query("define proposition owns wm-id;").resolve()
            tx.commit()
        with self.driver.transaction(self.database, READ) as tx:
            pending = [q.opt(r, "k") for r in q.rows(tx, """match $p isa proposition, has proposition-key $k;
                not { $p has wm-id $i; };""")]
        with self.driver.transaction(self.database, WRITE) as tx:
            for key in pending:
                q.run(tx, "match $p isa proposition, has proposition-key == $k; insert $p has wm-id == $id;",
                      {"k": key, "id": keys.proposition_id(key)})
            tx.commit()
        version, files = MODULES["core-0.4-a0"]
        self.install_module("core-0.4-a0", files=files, version=version)
        return len(pending)

    def modules(self):
        with self.driver.transaction(self.database, READ) as tx:
            return {q.opt(r, "n"): q.opt(r, "v") for r in
                    q.rows(tx, "match $m isa schema-module, has module-name $n, has module-version $v;")}

    # ---- the type and role lattice (A0.2) ---------------------------------------------------------------------------
    def _schema_lattice(self):
        """(direct supertype of each type, direct parent of each specialised role), read from the schema by query
        (`sub!`) once per installed schema. Profiles add subtypes and specialised roles; nothing is hard-coded."""
        if self._lattice is None:
            parents, role_parents = {}, {}
            with self.driver.transaction(self.database, READ) as tx:
                for kind in ("entity", "relation"):
                    for r in q.rows(tx, f"match {kind} $t; $t sub! $s;"):
                        parents[r.get("t").get_label()] = r.get("s").get_label()
                for r in q.rows(tx, "match relation $t; $t relates $r; $r sub! $p;"):
                    role_parents[r.get("r").get_label()] = r.get("p").get_label()
            self._lattice = (parents, role_parents, {}, {})      # + memo of ancestors and core roles
        return self._lattice

    def ancestors(self, label):
        """The type and its supertypes, nearest first (e.g. docked-at, located-at, proposition)."""
        parents, _, memo, _ = self._schema_lattice()
        if label not in memo:
            out = [label]
            while out[-1] in parents:
                out.append(parents[out[-1]])
            memo[label] = tuple(out)
        return list(memo[label])

    def is_a(self, label, ancestor):
        return ancestor in self.ancestors(label)

    def core_type(self, label):
        """The nearest core (foundational) type of a label: itself for a core type, else its nearest core supertype."""
        return next((t for t in self.ancestors(label) if t in CORE_LABELS), label)

    def core_role(self, scoped):
        """The core role name for a scoped role label: `pickup:picker` (picker as actor) -> `actor`; a role of a core
        type -> its own name; a profile's own new role (no core parent) -> its own name."""
        _, role_parents, _, memo = self._schema_lattice()
        if scoped not in memo:
            r = scoped
            while r.split(":")[0] not in CORE_LABELS and r in role_parents:
                r = role_parents[r]
            memo[scoped] = (r if r.split(":")[0] in CORE_LABELS else scoped).split(":")[-1]
        return memo[scoped]

    def _slot(self, label):
        """(declaring type, key role, value role) of the functional slot a content type takes part in, or None. A subtype
        inherits its nearest ancestor's declaration (U-5 default: inherit), so docked-at shares located-at's slot."""
        return next(((t, *FUNCTIONAL[t]) for t in self.ancestors(label) if t in FUNCTIONAL), None)

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
        rid = check_new_id(id or self._mint(kind))
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
        wid = check_new_id(id or self._mint("world"))
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
        """Exact type of each id among particulars, concepts, reference systems, event descriptions and (A0.1) propositions."""
        out = {}
        # The proposition branch exists only once propositions own wm-id: an infeasible branch is an error (INF11).
        extra = " or { $x isa proposition; }" if self.has_proposition_ids() else ""
        for i in sorted(set(ids)):
            for r in q.rows(tx, """match $x has wm-id == $id; $x isa! $t;
                { $x isa particular; } or { $x isa concept; } or { $x isa reference-system; } or { $x isa event; }"""
                            + extra + ";", {"id": i}):
                out[i] = r.get("t").get_label()
        missing = set(ids) - set(out)
        if missing:
            raise ValueError(f"no particular, concept, reference system, event description or proposition with id "
                             f"{sorted(missing)}")
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
        if self.has_proposition_ids():
            pid = keys.proposition_id(key)
            clash = q.rows(tx, "match $p isa proposition, has wm-id == $id, has proposition-key $k;", {"id": pid})
            if clash:      # same id, different content: never merge silently
                raise PropositionIdCollision(pid, key, q.opt(clash[0], "k"))
            attrs += ", has wm-id == $pid"
            values["pid"] = pid
        q.run(tx, f"match {patterns} insert $p isa {q.label(type)} ({links}), has proposition-key == $key{attrs};",
              values)
        return key

    def proposition_id(self, key):
        """The stored proposition's immutable id (A0.1), read from the database; None if absent."""
        with self.driver.transaction(self.database, READ) as tx:
            rows = q.rows(tx, "match $p isa proposition, has proposition-key == $k, has wm-id $id;", {"k": key})
        return q.opt(rows[0], "id") if rows else None

    def proposition(self, type, roles, params=None):
        """Store the content (once) and return its canonical key. Content alone asserts nothing."""
        with self.driver.transaction(self.database, WRITE) as tx:
            key = self._ensure_proposition(tx, type, roles, params)
            tx.commit()
        return key

    def describe_event(self, roles, description=None, id=None, type="event"):
        """An event description: one account of an occurrence, with its participants. Identified by id, not by
        content: two descriptions with the same participants are two descriptions. Asserts nothing by itself.
        `type` may be a profile subtype of `event` (A0.2); roles are then that type's own role names."""
        if not self.is_a(type, "event"):
            raise ValueError(f"{type!r} is not an event type")
        eid = check_new_id(id or self._mint("event"))
        with self.driver.transaction(self.database, WRITE) as tx:
            patterns, links, values = self._players(tx, roles)
            values["id"] = eid
            extra = ""
            if description:
                extra, values["d"] = ", has description == $d", description
            q.run(tx, f"match {patterns} insert $e isa {q.label(type)} ({links}), has wm-id == $id{extra};", values)
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
            scoped = {}
            for r in q.rows(tx, """match { $c isa proposition, has proposition-key == $k; } or
                { $c isa event, has wm-id == $k; }; $c links ($role: $x); $x has wm-id $xid;""", {"k": key_or_id}):
                out["roles"].setdefault(r.get("role").get_label().split(":")[-1], []).append(q.opt(r, "xid"))
                scoped.setdefault(r.get("role").get_label(), set()).add(q.opt(r, "xid"))
            core_roles = self._role_maps(scoped)[0]
            for name in QUALITY_PARAMS:
                for r in q.rows(tx, f"match $c isa proposition, has proposition-key == $k, has {name} $v;",
                                {"k": key_or_id}):
                    out["params"][name] = q.opt(r, "v")
        out["roles"] = {k: sorted(v) for k, v in out["roles"].items()}
        if out["type"] not in CORE_LABELS:          # a profile subtype: also say what it is in core terms (A0.2)
            out["core_type"], out["core_roles"] = self.core_type(out["type"]), core_roles
        return out

    def count(self, type):
        with self.driver.transaction(self.database, READ) as tx:
            return len(q.rows(tx, f"match $x isa {q.label(type)};"))

    # ---- writing: stance and judgement -----------------------------------------------------------------------------
    def world_kind(self, world):
        with self.driver.transaction(self.database, READ) as tx:
            rows = q.rows(tx, "match $w isa world, has wm-id == $id, has world-kind $k;", {"id": world})
        if not rows:
            raise ValueError(f"no world {world!r}")
        return q.opt(rows[0], "k")

    def attest(self, world, type=None, roles=None, *, event=None, params=None, start=None, end=None,
               until_superseded=False, polarity=True, stance=None, basis=None, attester=SYSTEM, credence=None,
               clock=None, supersedes=None, id=None):
        """Record that `attester` takes a stance on a content in `world` over a valid interval. Returns its id.

        Content: a proposition (`type`, `roles`, `params`; stored once) or an event description (`event` id).
        start/end: datetime, (earliest, latest) or Window; start None = from the start of the world. A missing end is
        UNKNOWN unless `until_superseded` (the attester commits that it holds until it records otherwise).
        Defaults: stance `stipulates` in hypothetical and simulated worlds, `asserts` otherwise; basis follows stance.
        supersedes: the id of an earlier attestation by the same attester that this one replaces (a correction).
        """
        if supersedes is not None and self._attestation(supersedes)["attester"] != attester:
            raise ValueError("an attestation can only be superseded by its own attester (E3)")
        kind = self.world_kind(world)
        stance = stance or ("stipulates" if kind in VARIANT_KINDS else "asserts")
        if stance == "stipulates" and kind not in VARIANT_KINDS:
            raise ValueError("stipulation is allowed only in hypothetical and simulated worlds (E7)")
        basis = basis or ("stipulation" if stance == "stipulates" else "testimony")
        start, end = _window(start), _window(end)
        if start is not None and start.latest is None:
            raise ValueError("a start window needs both bounds (a missing start means: from the start of the world)")
        if end is not None and until_superseded:
            raise ValueError("give either an end or until_superseded, not both")
        end_basis = "stated" if end is not None else ("until-superseded" if until_superseded else "unknown")
        aid = check_new_id(id or self._mint("att"))
        values = {"world": world, "attester": attester, "id": aid, "st": stance, "pol": polarity, "bs": basis,
                  "eb": end_basis, "rec": self._now()}
        attrs = ""
        for name, w in (("valid-from", start), ("valid-to", end)):
            if w is not None:
                v = name.replace("-", "_")
                attrs += f", has {name}-earliest == ${v}_e"
                values[f"{v}_e"] = w.earliest
                if w.latest is not None:
                    attrs += f", has {name}-latest == ${v}_l"
                    values[f"{v}_l"] = w.latest
        if credence is not None:
            attrs += ", has credence == $cr"
            values["cr"] = float(credence)
        with self.driver.transaction(self.database, WRITE) as tx:
            if event is not None:
                content = "$c isa event, has wm-id == $content;"
                values["content"] = event
            else:
                values["content"] = self._ensure_proposition(tx, type, roles, params)
                content = "$c isa proposition, has proposition-key == $content;"
            clock_match, clock_link = "", ""
            if clock is not None:
                clock_match, clock_link = "$k isa clock, has wm-id == $clock;", ", clock: $k"
                values["clock"] = clock
            old_match, old_link = "", ""
            if supersedes is not None:
                old_match = "$old isa attestation, has wm-id == $old_id;"
                old_link = " supersession (old: $old, new: $n), has recorded-at == $rec;"
                values["old_id"] = supersedes
            rows = list(q.run(tx, f"""match $w isa world, has wm-id == $world; {content} {clock_match} {old_match}
                $who has wm-id == $attester; {{ $who isa physical-object; }} or {{ $who isa social-object; }};
                insert $n isa attestation (attester: $who, content: $c, context: $w{clock_link}), has wm-id == $id,
                has stance == $st, has polarity == $pol, has basis == $bs, has end-basis == $eb,
                has recorded-at == $rec{attrs};{old_link}""", values).as_concept_rows())
            if not rows:
                raise ValueError(f"world {world!r}, attester {attester!r}, content or clock not found")
            tx.commit()
        return aid

    def deny(self, world, type=None, roles=None, **kw):
        """An explicit denial: the same content, polarity false."""
        return self.attest(world, type, roles, polarity=False, **kw)

    def accept(self, attestation, verdict="accepted", holder=SYSTEM, reason=None):
        """A perspective's decision about an attestation (accepted, rejected, retracted). World-independent."""
        values = {"a_id": attestation, "h_id": holder, "id": self._mint("acceptance"), "v": verdict, "rec": self._now()}
        extra = ""
        if reason:
            extra, values["why"] = ", has reason == $why", reason
        with self.driver.transaction(self.database, WRITE) as tx:
            rows = list(q.run(tx, f"""match $a isa attestation, has wm-id == $a_id; $h has wm-id == $h_id;
                {{ $h isa physical-object; }} or {{ $h isa social-object; }};
                insert acceptance (holder: $h, accepted: $a), has wm-id == $id, has verdict == $v,
                has recorded-at == $rec{extra};""", values).as_concept_rows())
            if not rows:
                raise ValueError(f"attestation {attestation!r} or holder {holder!r} not found")
            tx.commit()

    def _attestation(self, aid):
        with self.driver.transaction(self.database, READ) as tx:
            rows = q.rows(tx, """match $a isa attestation (content: $c, attester: $who), has wm-id == $id,
                has stance $st, has polarity $pol, has basis $bs; $who has wm-id $wid; $c isa! $t;
                { $c has proposition-key $ck; } or { $c isa event, has wm-id $ck; };
                try { $a has valid-from-earliest $se; }; try { $a has valid-from-latest $sl; };
                try { $a has credence $cr; };""", {"id": aid})
        if not rows:
            raise ValueError(f"no attestation {aid!r}")
        r = rows[0]
        return {"content": q.opt(r, "ck"), "is_event": self.is_a(r.get("t").get_label(), "event"), "attester": q.opt(r, "wid"),
                "stance": q.opt(r, "st"), "polarity": q.opt(r, "pol"), "basis": q.opt(r, "bs"),
                "start": Window(q.opt(r, "se"), q.opt(r, "sl")) if q.opt(r, "se") else None, "credence": q.opt(r, "cr")}

    def end(self, world, attestation, at, reason=None):
        """The attester's claim now has an end: a new attestation of the same content by the same attester, with a
        stated end at `at`, in `world`, superseding the old one (E3). In a variant world this never affects the base,
        because the new attestation is visible only there."""
        old = self._attestation(attestation)
        kind = self.world_kind(world)
        stance = "stipulates" if kind in VARIANT_KINDS else old["stance"]     # variants change content by stipulation
        values = {"world": world, "content": old["content"], "attester": old["attester"], "id": self._mint("att"),
                  "st": stance, "pol": old["polarity"], "bs": "stipulation" if stance == "stipulates" else old["basis"],
                  "rec": self._now(), "old_id": attestation}
        at = _window(at)
        attrs = ", has valid-to-earliest == $te"
        values["te"] = at.earliest
        if at.latest is not None:
            attrs += ", has valid-to-latest == $tl"
            values["tl"] = at.latest
        if old["start"] is not None:
            attrs += ", has valid-from-earliest == $se, has valid-from-latest == $sl"
            values.update({"se": old["start"].earliest, "sl": old["start"].latest})
        if reason:
            attrs += ", has description == $why"
            values["why"] = reason
        content = ("$c isa event, has wm-id == $content;" if old["is_event"]
                   else "$c isa proposition, has proposition-key == $content;")
        with self.driver.transaction(self.database, WRITE) as tx:
            q.run(tx, f"""match $w isa world, has wm-id == $world; {content} $who has wm-id == $attester;
                {{ $who isa physical-object; }} or {{ $who isa social-object; }};
                $old isa attestation, has wm-id == $old_id;
                insert $n isa attestation (attester: $who, content: $c, context: $w), has wm-id == $id,
                has stance == $st, has polarity == $pol, has basis == $bs, has end-basis "stated",
                has recorded-at == $rec{attrs};
                supersession (old: $old, new: $n), has recorded-at == $rec;""", values)
            tx.commit()
        return values["id"]

    # ---- reading: visibility -----------------------------------------------------------------------------------
    def _world_chain(self, tx, world, as_of):
        """[(world, valid-time limit, knowledge limit)] from the world up through its bases (tightest limits apply)."""
        chain, vlim, klim, current = [(world, None, as_of)], None, as_of, world
        while True:
            rows = [r for r in q.rows(tx, """match $v isa world, has wm-id == $world;
                $br isa branching (base: $b, variant: $v), has branch-at $at, has knowledge-at $kat, has recorded-at $rec;
                $b has wm-id $bid;""", {"world": current}) if klim is None or q.opt(r, "rec") <= klim]
            if not rows:
                return chain
            at, kat = q.opt(rows[0], "at"), q.opt(rows[0], "kat")
            vlim = at if vlim is None else min(vlim, at)
            klim = kat if klim is None else min(klim, kat)
            current = q.opt(rows[0], "bid")
            chain.append((current, vlim, klim))

    @staticmethod
    def _filters(world, type, subject, klim, vlim, at):
        """TypeQL selecting attestations in `world` (and their content) by content type, a role player of the
        content, transaction-time limit, inherited branch-time limit and valid time `at`."""
        parts = ["$w isa world, has wm-id == $world;",
                 "$a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec;"]
        params = {"world": world}
        if type is not None:
            parts.append(f"$c isa {q.label(type)};")
        if subject is not None:
            # Bound positively, so the query starts from the subject (see best practices).
            parts.append("$subj has wm-id == $sid; $c links ($kr: $subj);")
            params["sid"] = subject
        if klim is not None:
            parts.append("$rec <= $klim;")
            params["klim"] = klim
        if vlim is not None:
            parts.append("{ not { $a has valid-from-earliest $v0; }; } or { $a has valid-from-earliest $v1; $v1 < $vlim; };")
            params["vlim"] = vlim
        if at is not None:
            # Only attestations that start after t are skipped: they say nothing about t. Attestations that ended
            # before t are kept, because an end says the content does not hold, which can dispute other accounts.
            parts.append("{ not { $a has valid-from-latest $s0; }; } or { $a has valid-from-latest $s1; $s1 <= $at; };")
            params["at"] = at
        return "match " + " ".join(parts), params

    def _level(self, tx, world, depth, vlim, klim, type, subject, at, perspective):
        head, params = self._filters(world, type, subject, klim, vlim, at)
        # Type inference rejects a disjunction branch that cannot apply to a fixed type, so pick the content id pattern.
        recs = {}
        if type is not None and self.is_a(type, "event"):
            content_id = "$c has wm-id $ck;"
        elif type is not None:
            content_id = "$c has proposition-key $ck;"
        else:
            content_id = "{ $c has proposition-key $ck; } or { $c isa event, has wm-id $ck; };"
        # Attributes are read with one `fetch` stage rather than one `try` block each: same values, about 3x faster
        # (docs/core-0.3, experiment-main-query.json). Absent attributes come back as null.
        for d in q.documents(tx, head + f""" $who has wm-id $wid; $c isa! $t; {content_id}
            fetch {{ "aid": $aid, "wid": $wid, "t": $t, "ck": $ck, "rec": $rec, "st": $a.stance, "pol": $a.polarity,
                     "bs": $a.basis, "eb": $a.end-basis, "sfe": $a.valid-from-earliest, "sfl": $a.valid-from-latest,
                     "tte": $a.valid-to-earliest, "ttl": $a.valid-to-latest, "cr": $a.credence }};""", params):
            sfe, sfl, tte, ttl = (q.parse_datetime(d[k]) for k in ("sfe", "sfl", "tte", "ttl"))
            ctype = d["t"]["label"]
            recs[d["aid"]] = AttestationRecord(
                id=d["aid"], content=d["ck"], ctype=ctype, base=None if ctype in CORE_LABELS else self.core_type(ctype),
                roles={}, params={}, attester=d["wid"],
                world=world, stance=d["st"], polarity=d["pol"], basis=d["bs"],
                start=Window(sfe, sfl) if sfe is not None else None,
                end=Window(tte, ttl) if tte is not None else None, end_basis=d["eb"],
                recorded_at=q.parse_datetime(d["rec"]), credence=d["cr"], depth=depth)
        # Fetching `$c.lower` is rejected unless every possible type of $c can own it, so quality parameters are
        # fetched separately, only when the content can be has-quality.
        if type is None or self.is_a(type, "has-quality") or self.is_a("has-quality", type):
            for d in q.documents(tx, head + """ $c isa has-quality;
                fetch { "aid": $aid, "lower": $c.lower, "upper": $c.upper, "coverage-level": $c.coverage-level };""",
                                 params):
                if d["aid"] in recs:
                    recs[d["aid"]].params = {k: d[k] for k in ("lower", "upper", "coverage-level") if d[k] is not None}
            self.stats["queries"] += 1
        roles = {}
        if subject is None:
            role_q = head + " $c links ($role: $x); $x has wm-id $xid;"
        else:   # the subject's own role comes from $kr; a second `links` cannot match it again
            role_q = head + " try { $c links ($role: $x); $x has wm-id $xid; };"
        for r in q.rows(tx, role_q, params):           # scoped role label -> ids
            mine = roles.setdefault(q.opt(r, "aid"), {})
            if subject is not None:
                mine.setdefault(r.get("kr").get_label(), set()).add(subject)
            if r.get("role") is not None:
                mine.setdefault(r.get("role").get_label(), set()).add(q.opt(r, "xid"))
        for aid, rs in roles.items():
            if aid in recs:
                recs[aid].roles, recs[aid].concrete_roles = self._role_maps(rs)
        for r in q.rows(tx, head + """ $acc isa acceptance (holder: $h, accepted: $a), has verdict $vd,
            has recorded-at $vrec; $h has wm-id == $persp;""", {**params, "persp": perspective}):
            if klim is None or q.opt(r, "vrec") <= klim:
                recs[q.opt(r, "aid")].acceptances.append((perspective, q.opt(r, "vd"), q.opt(r, "vrec")))
        supers = [(q.opt(r, "aid"), q.opt(r, "nid"), q.opt(r, "srec"), q.opt(r, "nw"), q.opt(r, "nse"),
                   q.opt(r, "nwid"), q.opt(r, "nst"))
                  for r in q.rows(tx, head + """ $su isa supersession (old: $a, new: $n), has recorded-at $srec;
                  $n has wm-id $nid, has stance $nst; $n isa attestation (context: $nwo, attester: $nwho);
                  $nwo has wm-id $nw; $nwho has wm-id $nwid;
                  try { $n has valid-from-earliest $nse; };""", params)]
        new_acc = [(q.opt(r, "nid"), q.opt(r, "vd"), q.opt(r, "vrec"))
                   for r in q.rows(tx, head + """ $su isa supersession (old: $a, new: $n); $n has wm-id $nid;
                   $nacc isa acceptance (holder: $nh, accepted: $n), has verdict $vd, has recorded-at $vrec;
                   $nh has wm-id == $persp;""", {**params, "persp": perspective})] if supers else []
        self.stats["queries"] += 4 + (1 if supers else 0)
        supers = [(*row, [(perspective, v, rec) for nid, v, rec in new_acc if nid == row[1]]) for row in supers]
        return recs, supers

    def _load(self, world, as_of=None, types=None, subjects=None, at=None, perspective=SYSTEM):
        """Attestations visible in `world` as known at `as_of`, with the perspective's acceptances and visible
        supersessions. Filters (types, subjects, at) run in TypeDB; with none, everything visible is loaded."""
        visible, supers = {}, []
        with self.driver.transaction(self.database, READ) as tx:
            chain = self._world_chain(tx, world, as_of)
            levels = {w: (depth, vlim, klim) for depth, (w, vlim, klim) in enumerate(chain)}
            for depth, (w, vlim, klim) in enumerate(chain):
                for type in (types or [None]):
                    for subj in (subjects or [None]):
                        recs, sup = self._level(tx, w, depth, vlim, klim, type, subj, at, perspective)
                        for aid, rec in recs.items():
                            if aid not in visible:
                                visible[aid] = rec
                            else:
                                for acc in rec.acceptances:
                                    if acc not in visible[aid].acceptances:
                                        visible[aid].acceptances.append(acc)
                        supers.extend(sup)
        seen = set()
        for old, new, rec, new_world, new_start, new_attester, new_stance, accs in supers:
            if (old, new) in seen or old not in visible or new_world not in levels:
                continue
            seen.add((old, new))
            _, vlim, klim = levels[new_world]
            if (klim is None or rec <= klim) and (vlim is None or new_start is None or new_start < vlim):
                visible[old].superseded_by.append(Replacement(
                    new, rec, new_attester, new_stance,
                    [acc for acc in accs if klim is None or acc[2] <= klim]))
        self.stats["attestations"] += len(visible)
        return visible

    def visible(self, world, as_of=None, perspective=SYSTEM):
        """Every attestation visible in `world` at `as_of` (the full, unfiltered load)."""
        return self._load(world, as_of, perspective=perspective)

    def identity(self, world, as_of=None, perspective=SYSTEM, ids=None):
        """Identity closure for the perspective. With `ids`, only same-as links touching the growing group are loaded."""
        if ids is None or not self.selective:
            same = self._load(world, as_of, types=["same-as"], perspective=perspective)
            return Identity(same.values(), perspective, as_of)
        known, frontier, same = set(ids), sorted(set(ids)), {}
        while frontier:
            same.update(self._load(world, as_of, types=["same-as"], subjects=frontier, perspective=perspective))
            ident = Identity(same.values(), perspective, as_of)
            group = {m for i in ids for m in ident.members(i)}
            frontier = sorted(group - known)
            known |= group
        return Identity(same.values(), perspective, as_of)

    def _role_maps(self, scoped):
        """{scoped role label: ids} -> (roles by core role name, roles by stored name or None when they agree)."""
        core, concrete = {}, {}
        for label, ids in scoped.items():
            core.setdefault(self.core_role(label), set()).update(ids)
            concrete.setdefault(label.split(":")[-1], set()).update(ids)
        core = {r: sorted(v) for r, v in core.items()}
        concrete = {r: sorted(v) for r, v in concrete.items()}
        return core, (None if concrete == core else concrete)

    def _view(self, world, as_of, perspective, type, subject_ids, at=None):
        """(attestations, identity) for a question about `subject_ids`: selective by default, else the full load."""
        if not self.selective:
            atts = self.visible(world, as_of, perspective)
            ident = Identity([a for a in atts.values() if a.kind == "same-as"], perspective, as_of)
            return atts, ident
        ident = self.identity(world, as_of, perspective, ids=subject_ids)
        members = sorted({m for s in subject_ids for m in ident.members(s)})
        return self._load(world, as_of, types=[type] if type else None, subjects=members, at=at,
                          perspective=perspective), ident

    # ---- reading: answers ----------------------------------------------------------------------------------------
    @staticmethod
    def _class(a, ident):
        """Content equivalence class under the perspective's identity (v0.2 §4.2: semantic, not structural)."""
        return (a.ctype, tuple(sorted((r, tuple(sorted({ident.canonical(x) for x in ids}))) for r, ids in a.roles.items())),
                tuple(sorted(a.params.items())))

    def _judge(self, atts, ident, t, perspective, as_of):
        """Per content class at t: {class: (True/False/'disputed', supporting attestations)} after precedence.

        Within a class, the nearest world's deciding attestations win (a variant overrides what it inherited);
        a usable assertion and a usable denial at the same depth make the class DISPUTED. For functional types, a
        class holding in a nearer world overrides inherited classes for the same subject (exclusivity)."""
        deciding = {}
        for a in atts:
            if not usable(a, perspective, as_of):
                continue
            v = verdict(a, t)
            if v is not None:
                deciding.setdefault(self._class(a, ident), []).append((a, v))
        out = {}
        for cls, items in deciding.items():
            # A stated end says the content stopped holding, but only until the content is attested to start again:
            # drop an ended attestation's "does not hold" when a usable positive attestation of the same content
            # started after that end and by t. Genuine conflicts (an account begun before the end) still dispute.
            restarts = [a.start for a, v in items if a.polarity and a.start is not None]
            items = [(a, v) for a, v in items if not (
                v is False and a.polarity and a.end is not None and a.end.latest is not None
                and any(st.earliest >= a.end.latest and st.latest <= t for st in restarts))]
            if not items:
                continue
            depth = min(a.depth for a, _ in items)
            near = [(a, v) for a, v in items if a.depth == depth]
            vals = {v for _, v in near}
            out[cls] = ("disputed" if len(vals) > 1 else vals.pop(), [a for a, _ in near], depth)
        slot_depth, slots = {}, {}
        for cls, (val, support, depth) in out.items():
            decl = self._slot(cls[0])
            if val is True and decl:
                slots[cls] = slot = (decl[0], dict(cls[1]).get(decl[1]))
                slot_depth[slot] = min(slot_depth.get(slot, depth), depth)
        for cls, slot in slots.items():
            if out[cls][2] > slot_depth[slot]:
                del out[cls]
        return out

    @staticmethod
    def _alternatives(atts, t, perspective, as_of):
        return tuple(sorted(a.id for a in atts if acceptance_state(a, perspective, as_of) == "unreviewed"
                            and not superseded(a, perspective, as_of) and verdict(a, t) is not None))

    def value_at(self, world, type, subject, t, as_of=None, perspective=SYSTEM, key_role=None, value_role=None):
        """The value(s) of a relationship for `subject` at valid time t, for a perspective, as known at `as_of`."""
        slot = self._slot(type)
        if not key_role and not slot:
            raise ValueError(f"{type!r} declares no functional slot: name key_role and value_role")
        key_role, value_role = (key_role, value_role) if key_role else slot[1:]
        atts, ident = self._view(world, as_of, perspective, type, [subject], at=t)
        me = set(ident.members(subject))
        about = [a for a in atts.values() if self.is_a(a.ctype, type) and me & set(a.roles.get(key_role, []))]
        if not about:
            if self.selective:
                anything, _ = self._view(world, as_of, perspective, type, [subject])
                if any(self.is_a(a.ctype, type) and me & set(a.roles.get(key_role, [])) for a in anything.values()):
                    return Answer(Status.UNKNOWN)
            return Answer(Status.NOT_YET_KNOWN)
        judged = self._judge(about, ident, t, perspective, as_of)
        holding = {cls: sup for cls, (val, sup, _) in judged.items() if val is True}
        disputed = {cls: sup for cls, (val, sup, _) in judged.items() if val == "disputed"}
        alternatives = self._alternatives(about, t, perspective, as_of)
        values = sorted({v for cls in list(holding) + list(disputed) for v in dict(cls[1]).get(value_role, ())})
        support = [a for sup in list(holding.values()) + list(disputed.values()) for a in sup]
        evidence = tuple(a.evidence() for a in sorted(support, key=lambda a: a.id))
        ids = tuple(sorted(a.id for a in support))
        if not values:
            return Answer(Status.UNKNOWN, alternatives=alternatives)
        if disputed or (slot and len(values) > 1):
            return Answer(Status.DISPUTED, values=tuple(values), support=ids, alternatives=alternatives, evidence=evidence)
        return Answer(answer_status(support), values=tuple(values), support=ids, alternatives=alternatives,
                      evidence=evidence)

    def holds(self, world, type, roles, t, as_of=None, perspective=SYSTEM):
        """Does this content hold at t for the perspective? Evidence-backed status with polarity."""
        ids = sorted({x for v in roles.values() for x in as_ids(v)})
        slot = self._slot(type)
        key = slot[1] if slot and slot[1] in roles else sorted(roles)[0]
        anchor = as_ids(roles[key])
        if self.selective:
            ident = self.identity(world, as_of, perspective, ids=ids)
            members = sorted({m for x in anchor for m in ident.members(x)})
            # A functional slot is shared with the declaring type's other subtypes, so load the whole slot.
            atts = self._load(world, as_of, types=[slot[0] if slot else type], subjects=members, perspective=perspective)
        else:
            atts, ident = self._view(world, as_of, perspective, None, ids)
        want = {r: {ident.canonical(x) for x in as_ids(v)} for r, v in roles.items()}

        def matches(a):
            return self.is_a(a.ctype, type) and all(want[r] <= {ident.canonical(x) for x in a.roles.get(r, [])} for r in want)

        about = [a for a in atts.values() if matches(a)]
        peers = about
        if slot and slot[1] in want:
            k = slot[1]
            peers = [a for a in atts.values() if self.is_a(a.ctype, slot[0])
                     and want[k] <= {ident.canonical(x) for x in a.roles.get(k, [])}]
        judged = self._judge(peers, ident, t, perspective, as_of)
        mine = {cls: v for cls, v in judged.items() if any(matches(a) for a in v[1])}
        alternatives = self._alternatives(about, t, perspective, as_of)
        for cls, (val, sup, _) in mine.items():
            evidence = tuple(a.evidence() for a in sorted(sup, key=lambda a: a.id))
            ids_ = tuple(sorted(a.id for a in sup))
            if val == "disputed":
                return Answer(Status.DISPUTED, None, support=ids_, alternatives=alternatives, evidence=evidence)
            return Answer(answer_status(sup), val, support=ids_, alternatives=alternatives, evidence=evidence)
        if slot:
            decl, k, v = slot
            if k in roles and v in roles:
                other = self.value_at(world, decl, anchor[0], t, as_of, perspective)
                if other.status in (Status.ASSERTED, Status.STIPULATED, Status.INFERRED) \
                        and not set(other.values) & want[v]:
                    return Answer(Status.INFERRED, False, support=other.support, alternatives=alternatives,
                                  evidence=other.evidence)
        if not about:
            return Answer(Status.NOT_YET_KNOWN, alternatives=alternatives)
        return Answer(Status.UNKNOWN, alternatives=alternatives)

    def history(self, world, subject, type=None, as_of=None, perspective=SYSTEM):
        """Every visible attestation involving the subject (identity-aware), oldest first, with its acceptance state
        for the perspective and whether it has been superseded."""
        atts, ident = self._view(world, as_of, perspective, type, [subject])
        me = set(ident.members(subject))
        rows = []
        for a in atts.values():
            if (type is None or self.is_a(a.ctype, type)) and any(me & set(ids) for ids in a.roles.values()):
                rows.append({**a.evidence(), "content": a.content, "type": a.ctype, "roles": a.roles,
                             "state": acceptance_state(a, perspective, as_of), "superseded": superseded(a, perspective, as_of),
                             "world_depth": a.depth})
        far = datetime.min.replace(tzinfo=timezone.utc)
        return sorted(rows, key=lambda r: (r["start"].earliest if r["start"] else far, r["recorded_at"], r["attestation"]))

    # ---- events, occurrences and moves -----------------------------------------------------------------------------
    def record_event(self, world, roles, start, end=None, kind=None, ends=(), effects=(), attester=SYSTEM, id=None,
                     type="event"):
        """An event description, its occurrence attested by `attester` over [start, end], and how it changed the world.

        kind: optional category classifying the description. ends: attestations it ended (each superseded by its
        attester with an end at the event's end). effects: dicts {type, roles} for new facts from the event's end,
        holding until superseded. type: `event` or a profile subtype (A0.2). Returns (event id, [effect attestation ids])."""
        start = _window(start)
        end = _window(end) or start
        eid = self.describe_event(roles, id=id, type=type)
        self.attest(world, event=eid, start=start, end=end, attester=attester)
        if kind:
            self.attest(world, "classified-as", {"classified": eid, "class": kind}, start=start, until_superseded=True,
                        attester=attester)
        for aid in ends:
            self.end(world, aid, end, reason=f"ended by event {eid}")
        new = [self.attest(world, e["type"], e["roles"], start=end, until_superseded=True, attester=attester)
               for e in effects]
        return eid, new

    def move(self, world, thing, to, at, actor=None, kind=None, as_of=None, attester=SYSTEM):
        """The thing was moved to `to` at `at`: ends the attester's location attestations holding just before, and
        records the movement (origin, destination) with the new location as its effect."""
        just_before = _window(at).earliest - timedelta(microseconds=1)
        atts, ident = self._view(world, as_of, attester, "located-at", [thing], at=just_before)
        me = set(ident.members(thing))
        before = [a for a in atts.values() if a.kind == "located-at" and me & set(a.roles.get("located", []))
                  and a.attester == attester and usable(a, attester, as_of) and verdict(a, just_before) is True]
        origin = sorted({p for a in before for p in a.roles.get("place", [])})
        roles = {"patient": thing, "destination": to}
        if origin:
            roles["origin"] = origin
        if actor:
            roles["actor"] = actor
        return self.record_event(world, roles, start=at, kind=kind, ends=[a.id for a in before], attester=attester,
                                 effects=[{"type": "located-at", "roles": {"located": thing, "place": to}}])

    def events(self, world, participant=None, as_of=None, perspective=SYSTEM):
        """Event descriptions whose occurrence is usable for the perspective, ordered by start window."""
        if participant is not None:
            atts, ident = self._view(world, as_of, perspective, "event", [participant])
            who = set(ident.members(participant))
        else:
            atts, who = self._load(world, as_of, types=["event"], perspective=perspective), None
        evs = [a for a in atts.values() if a.kind == "event" and a.polarity and usable(a, perspective, as_of)
               and (who is None or any(who & set(ids) for ids in a.roles.values()))]
        kinds = {}
        if evs:
            for a in self._load(world, as_of, types=["classified-as"], subjects=sorted({e.content for e in evs}),
                                perspective=perspective).values():
                if usable(a, perspective, as_of) and a.polarity:
                    for x in a.roles.get("classified", []):
                        kinds.setdefault(x, set()).update(a.roles.get("class", []))
        far = datetime.min.replace(tzinfo=timezone.utc)
        evs.sort(key=lambda a: (a.start.earliest if a.start else far, a.start.latest if a.start else far, a.id))
        return [{"event": a.content, "type": a.ctype, "attestation": a.id, "attester": a.attester, "roles": a.roles,
                 "kinds": sorted(kinds.get(a.content, [])), "start": a.start, "end": a.end, "record": a} for a in evs]

    @staticmethod
    def certainly_before(a, b):
        return certainly_before(a["record"], b["record"])

    def descriptions(self, world, occurrence, as_of=None, perspective=SYSTEM):
        """Event descriptions that the perspective accepts as describing `occurrence` (or anything accepted as the
        same occurrence). Without such links a description describes no known occurrence."""
        ident = self.identity(world, as_of, perspective, ids=[occurrence])
        occ = ident.members(occurrence)
        links = self._load(world, as_of, types=["describes"], subjects=occ, perspective=perspective)
        return sorted({d for a in links.values() if a.polarity and usable(a, perspective, as_of)
                       for d in a.roles.get("description", [])})

    def occurrence(self, world, occurrence, as_of=None, perspective=SYSTEM):
        """A merged view of an occurrence: its accepted descriptions, and for each role every participant with the
        descriptions (and sources) that name it. Conflicts stay visible and traceable; nothing is merged in storage."""
        descs = self.descriptions(world, occurrence, as_of, perspective)
        out = {"occurrence": occurrence, "descriptions": descs, "participants": {}}
        if descs:
            for a in self._load(world, as_of, types=["event"], subjects=None, perspective=perspective).values():
                if a.content in descs:
                    for role, ids in a.roles.items():
                        for x in ids:
                            out["participants"].setdefault(role, {}).setdefault(x, set()).add((a.content, a.attester))
        out["participants"] = {r: {x: sorted(v) for x, v in m.items()} for r, m in out["participants"].items()}
        return out

    # ---- existence ---------------------------------------------------------------------------------------------
    def declare_existence(self, world, thing, start=None, end=None, attester=SYSTEM, **kw):
        """The thing exists in `world` from `start` (its creation; None: from the start of the world) until `end` or
        until superseded. By another attester, unreviewed, this is uncertain existence."""
        return self.attest(world, "existence", {"existent": thing}, start=start, end=end,
                           until_superseded=end is None, attester=attester, **kw)

    def create_thing(self, world, kind, name, at, alt_names=(), attester=SYSTEM, id=None):
        """Register a new particular and attest that it came into existence in `world` at `at`."""
        rid = self.add_entity(kind, name, alt_names=alt_names, id=id)
        self.declare_existence(world, rid, start=at, attester=attester)
        return rid

    def destroy(self, world, thing, at, reason=None):
        """The thing stops existing in `world` at `at`. The system's own attestations about it that hold just before
        are ended (superseded); others' accepted ones are denied by the system from `at` (so they are disputed, not
        silently overruled). Returns the attestations ended or denied."""
        t = _window(at).earliest - timedelta(microseconds=1)
        atts, ident = self._view(world, None, SYSTEM, None, [thing], at=t)
        me = set(ident.members(thing))
        touched = []
        for cls, (val, support, _) in self._judge(list(atts.values()), ident, t, SYSTEM, None).items():
            if val is not True or self.core_type(cls[0]) in ("event", "same-as"):
                continue
            for a in support:
                if not any(me & set(ids) for ids in a.roles.values()):
                    continue
                if a.attester == SYSTEM:
                    self.end(world, a.id, at, reason=reason or f"{thing} destroyed")
                else:
                    self.attest(world, a.ctype, a.concrete_roles or a.roles, params=a.params or None, start=at, until_superseded=True,
                                polarity=False)
                touched.append(a.id)
        return sorted(touched)

    def exists(self, world, thing, t, as_of=None, perspective=SYSTEM):
        """ASSERTED/STIPULATED from existence attestations (before creation and after destruction: false); INFERRED
        true if the thing takes part in content holding at t; otherwise UNKNOWN, or NOT_YET_KNOWN."""
        atts, ident = self._view(world, as_of, perspective, None, [thing])
        me = set(ident.members(thing))
        mine = [a for a in atts.values() if a.kind != "same-as" and any(me & set(ids) for ids in a.roles.values())]
        ex = [a for a in mine if a.kind == "existence"]
        alternatives = tuple(sorted(a.id for a in ex if acceptance_state(a, perspective, as_of) == "unreviewed"
                                    and not superseded(a, perspective, as_of)))
        judged = self._judge(ex, ident, t, perspective, as_of)
        for val, support, _ in judged.values():
            ev = tuple(a.evidence() for a in support)
            ids = tuple(sorted(a.id for a in support))
            if val == "disputed":
                return Answer(Status.DISPUTED, None, support=ids, alternatives=alternatives, evidence=ev)
            return Answer(answer_status(support), val, support=ids, alternatives=alternatives, evidence=ev)
        others = [a for cls, (val, sup, _) in self._judge([a for a in mine if a.kind != "existence"], ident, t,
                                                          perspective, as_of).items() if val is True for a in sup]
        if others:
            return Answer(Status.INFERRED, True, support=tuple(sorted(a.id for a in others)),
                          alternatives=alternatives, evidence=tuple(a.evidence() for a in others))
        if not mine:
            return Answer(Status.NOT_YET_KNOWN, alternatives=alternatives)
        return Answer(Status.UNKNOWN, alternatives=alternatives)

    # ---- listings -----------------------------------------------------------------------------------------------
    def facts_about(self, world, subject, t, as_of=None, perspective=SYSTEM):
        """Every content (other than events and identity links) involving the subject that holds at t."""
        atts, ident = self._view(world, as_of, perspective, None, [subject], at=t)
        me = set(ident.members(subject))
        rel = [a for a in atts.values() if a.kind not in ("event", "same-as")
               and any(me & set(ids) for ids in a.roles.values())]
        out = []
        for cls, (val, support, _) in self._judge(rel, ident, t, perspective, as_of).items():
            if val is True:
                out.append({"type": cls[0], "roles": {r: list(ids) for r, ids in cls[1]}, "params": dict(cls[2]),
                            "support": sorted(a.id for a in support), "status": answer_status(support)})
        return sorted(out, key=lambda f: (f["type"], str(f["roles"])))

    def find(self, name, world=None, as_of=None, perspective=SYSTEM):
        """Ids whose name or alt-name equals `name` (every match). With `world`, only things that world's visible
        attestations mention, so hypothetical things never appear in other worlds' answers."""
        with self.driver.transaction(self.database, READ) as tx:
            ids = {q.opt(r, "id") for r in q.rows(tx, """match $x has wm-id $id;
                { $x isa particular; } or { $x isa concept; };
                { $x has name == $n; } or { $x has alt-name == $n; };""", {"n": name})}
        if world is not None:
            ids &= {x for a in self.visible(world, as_of, perspective).values() for v in a.roles.values() for x in v}
        return sorted(ids)

    def parts(self, world, whole, t, as_of=None, perspective=SYSTEM):
        """Transitive parts at t (application closure over the part-of content that holds for the perspective)."""
        return self._closure(world, "part-of", "whole", "part", whole, t, as_of, perspective)

    def dependencies(self, world, dependent, t, as_of=None, perspective=SYSTEM):
        return self._closure(world, "depends-on", "dependent", "dependee", dependent, t, as_of, perspective)

    def _closure(self, world, type, from_role, to_role, start, t, as_of, perspective):
        atts = self._load(world, as_of, types=[type], perspective=perspective)
        ident = Identity([], perspective, as_of)
        edges = {}
        for cls, (val, _, _) in self._judge(list(atts.values()), ident, t, perspective, as_of).items():
            if val is True:
                roles = dict(cls[1])
                for a in roles.get(from_role, ()):
                    edges.setdefault(a, set()).update(roles.get(to_role, ()))
        seen, todo = set(), [start]
        while todo:
            for n in edges.get(todo.pop(), ()):
                if n not in seen:
                    seen.add(n)
                    todo.append(n)
        return sorted(seen)

    def parts_in_database(self, world, whole):
        """Transitive parts computed by the TypeDB function `parts_in` (world-scoped; time and acceptance ignored)."""
        with self.driver.transaction(self.database, READ) as tx:
            return sorted({q.opt(r, "pid") for r in q.rows(tx, """match $x isa particular, has wm-id == $whole;
                $w isa world, has wm-id == $world; let $p in parts_in($x, $w); $p has wm-id $pid;""",
                {"whole": whole, "world": world})})
