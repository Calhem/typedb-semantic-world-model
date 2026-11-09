"""WorldModel: define worlds, things, facts and events in TypeDB, and ask about them.

Division of labour (kept explicit, see docs/m1/README.md):
- TypeDB: storage; kinds of thing and the roles they may play; one world per claim; unique ids; value ranges;
  matching typed role players; transitive part-of / depends-on within a world (functions parts_in, dependencies_in).
- Python (semantics.py): valid-time truth, status at a transaction time, identity closure, world inheritance,
  answer statuses.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from typedb.driver import Credentials, DriverOptions, DriverTlsConfig, TransactionType, TypeDB

from . import typeql as q
from .semantics import Answer, ClaimRecord, Identity, Status, Window, certainly_before, status_at, truth_at

READ, WRITE, SCHEMA = TransactionType.READ, TransactionType.WRITE, TransactionType.SCHEMA
SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schema"
MODULES = {"core": ("0.2.0", ["core/0001-core.tql"])}
FUNCTIONAL = {"located-at": ("located", "place")}       # claim type -> (key role, value role): one value at a time
ENTITY_KINDS = ("physical-object", "agent", "place", "concept")


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
        self.selective = selective             # filter questions in TypeDB (False: load whole worlds, the reference)
        self.stats = {"queries": 0, "claims": 0}
        self._last_recorded = None
        self._claim_types = None

    # ---- setup ---------------------------------------------------------------------------------------------------
    @classmethod
    def create(cls, database, driver=None, modules=("core",), clock=utcnow, replace=False):
        """Create the database and load schema modules in order. Refuses to overwrite unless replace=True."""
        driver = driver or connect()
        if driver.databases.contains(database):
            if not replace:
                raise ValueError(f"database {database!r} exists (use replace=True)")
            driver.databases.get(database).delete()
        driver.databases.create(database)
        wm = cls(driver, database, clock)
        for name in modules:
            wm.install_module(name)
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
        self._claim_types = None

    def modules(self):
        with self.driver.transaction(self.database, READ) as tx:
            return {q.opt(r, "n"): q.opt(r, "v") for r in
                    q.rows(tx, "match $m isa schema-module, has module-name $n, has module-version $v;")}

    def claim_types(self):
        """Every concrete claim type in the installed schema (core and profiles), by introspection."""
        if self._claim_types is None:
            with self.driver.transaction(self.database, READ) as tx:
                self._claim_types = {r.get("t").get_label() for r in q.rows(tx, "match relation $t; $t sub claim;")}
            self._claim_types.discard("claim")
        return self._claim_types

    # ---- writing -----------------------------------------------------------------------------------------------
    def _now(self):
        now = self.clock()
        if self._last_recorded is not None and now < self._last_recorded:
            raise ValueError("the clock went backwards: transaction time must not decrease")
        self._last_recorded = now
        return now

    @staticmethod
    def _mint(prefix):
        return f"{prefix}:{uuid.uuid4().hex[:16]}"

    def create_world(self, name, kind="actual", base=None, branch_at=None, knowledge_at=None, id=None):
        """A world (actual, simulated or hypothetical).

        A variant world names its base, the valid time it branches at (`branch_at`) and the base-world knowledge it
        inherits (`knowledge_at`, a transaction time; default: now). It sees a fixed snapshot: base claims, cessations
        and reviews recorded by `knowledge_at`, restricted to valid time before `branch_at`. Later corrections in the
        base are never pulled in; to adopt them, branch again.
        """
        wid = id or self._mint("world")
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
                             has recorded-at == $rec;""",
                      {"b_id": base, "v_id": wid, "at": branch_at, "kat": knowledge_at or rec, "rec": rec})
            tx.commit()
        return wid

    def add_entity(self, kind, name, alt_names=(), description=None, id=None):
        """A thing: physical-object, agent, place, concept (or a profile's subtype of these)."""
        rid = id or self._mint(kind)
        attrs = ", has name == $n" + "".join(f", has alt-name == $a{i}" for i in range(len(alt_names)))
        params = {"id": rid, "n": name, **{f"a{i}": a for i, a in enumerate(alt_names)}}
        if description:
            attrs += ", has description == $d"
            params["d"] = description
        with self.driver.transaction(self.database, WRITE) as tx:
            q.run(tx, f"insert $x isa {q.label(kind)}, has wm-id == $id{attrs};", params)
            tx.commit()
        return rid

    def assert_fact(self, world, type, roles, start=None, end=None, until_ceased=False, status="accepted",
                    clock="wall", description=None, caused_by=None, id=None):
        """Record a claim. `roles` maps role -> id or list of ids (referents, or events for classified-as).

        start/end: datetime (exact), (earliest, latest) or Window; start=None means "from the start of the world".
        until_ceased=True: the author states the fact lasts until a recorded cessation (otherwise a missing end is
        UNKNOWN). status "proposed" records a hypothesis that answers ignore until it is accepted by a review.
        """
        if type not in self.claim_types():
            raise ValueError(f"{type!r} is not a claim type in the installed schema")
        start, end = _window(start), _window(end)
        if start is not None and start.latest is None:
            raise ValueError("a start window needs both bounds (a missing start means: from the start of the world)")
        if end is not None and until_ceased:
            raise ValueError("give either an end or until_ceased, not both")
        basis = "stated" if end is not None else ("until-ceased" if until_ceased else "unknown")
        cid = id or self._mint("claim")
        params = {"world": world, "id": cid, "basis": basis, "clock": clock, "status": status, "rec": self._now()}
        kinds = self._kinds_of({x for ids in roles.values() for x in ([ids] if isinstance(ids, str) else ids)})
        players, links = [], []
        for i, (role, ids) in enumerate(sorted(roles.items())):
            for j, rid in enumerate([ids] if isinstance(ids, str) else list(ids)):
                v = f"p{i}_{j}"
                if rid not in kinds:
                    raise ValueError(f"no thing or claim with id {rid!r}")
                players.append(f"${v} isa {q.label(kinds[rid])}, has wm-id == ${v}_id;")
                links.append(f"{q.label(role)}: ${v}")
                params[f"{v}_id"] = rid
        attrs = ""
        for attr, w in (("valid-from", start), ("valid-to", end)):
            if w is not None:
                attrs += f", has {attr}-earliest == ${attr.replace('-', '_')}_e"
                params[f"{attr.replace('-', '_')}_e"] = w.earliest
                if w.latest is not None:
                    attrs += f", has {attr}-latest == ${attr.replace('-', '_')}_l"
                    params[f"{attr.replace('-', '_')}_l"] = w.latest
        if description:
            attrs += ", has description == $desc"
            params["desc"] = description
        body = (f"match $w isa world, has wm-id == $world; {' '.join(players)}\n"
                f"insert $c isa {q.label(type)} ({', '.join(links)}), has wm-id == $id, has end-basis == $basis, "
                f"has clock == $clock, has initial-status == $status, has recorded-at == $rec{attrs};\n"
                f"scope (world: $w, member: $c);")
        with self.driver.transaction(self.database, WRITE) as tx:
            answer = q.run(tx, body, params)
            if not list(answer.as_concept_rows()):
                raise ValueError(f"world or role player not found for {type} {roles}")
            if caused_by:
                q.run(tx, """match $e isa event, has wm-id == $e_id; $c isa claim, has wm-id == $c_id;
                             insert consequence (cause: $e, result: $c);""", {"e_id": caused_by, "c_id": cid})
            tx.commit()
        return cid

    def _kinds_of(self, ids):
        """Exact type label of each referent or claim id (worlds are excluded)."""
        out = {}
        with self.driver.transaction(self.database, READ) as tx:
            for i in sorted(ids):
                for r in q.rows(tx, """match $x has wm-id == $id; $x isa! $t; not { $x isa world; };""", {"id": i}):
                    out[i] = r.get("t").get_label()
        return out

    def cease(self, world, claim_id, at, reason=None):
        """Record that a claim stopped holding at `at` (a datetime or window), in `world`. Claims are never edited."""
        at = _window(at)
        sid = self._mint("cessation")
        params = {"world": world, "c_id": claim_id, "id": sid, "e": at.earliest, "rec": self._now()}
        attrs = ", has valid-to-earliest == $e"
        if at.latest is not None:
            attrs += ", has valid-to-latest == $l"
            params["l"] = at.latest
        if reason:
            attrs += ", has reason == $why"
            params["why"] = reason
        with self.driver.transaction(self.database, WRITE) as tx:
            rows = list(q.run(tx, f"""match $w isa world, has wm-id == $world; $c isa claim, has wm-id == $c_id;
                insert $s isa cessation (ended: $c), has wm-id == $id, has recorded-at == $rec{attrs};
                scope (world: $w, member: $s);""", params).as_concept_rows())
            if not rows:
                raise ValueError(f"world {world!r} or claim {claim_id!r} not found")
            tx.commit()
        return sid

    def review(self, world, claim_id, verdict, decided_by, reason=None):
        """Accept, reject or retract a claim, in `world`. Recorded at the current transaction time; never edited.
        A review made in a variant world applies there (and in its own variants), never in the base world."""
        params = {"world": world, "c_id": claim_id, "id": self._mint("review"), "v": verdict, "by": decided_by,
                  "rec": self._now()}
        extra = ""
        if reason:
            extra, params["why"] = ", has reason == $why", reason
        with self.driver.transaction(self.database, WRITE) as tx:
            rows = list(q.run(tx, f"""match $w isa world, has wm-id == $world; $c isa claim, has wm-id == $c_id;
                insert $rv isa review (reviewed: $c), has wm-id == $id, has verdict == $v, has decided-by == $by,
                has recorded-at == $rec{extra}; scope (world: $w, member: $rv);""", params).as_concept_rows())
            if not rows:
                raise ValueError(f"world {world!r} or claim {claim_id!r} not found")
            tx.commit()

    def record_event(self, world, roles, start, end=None, kind=None, ends=(), effects=(), id=None):
        """Record that an event happened, and how it changed the world.

        kind: optional concept id classifying the event. ends: claim ids the event ended (ceased at the event's end).
        effects: dicts {type, roles, until_ceased=True} for new facts starting at the event's end, linked to the event.
        """
        start = _window(start)
        end = _window(end) or start
        eid = self.assert_fact(world, "event", roles, start=start, end=end, id=id)
        if kind:
            self.assert_fact(world, "classified-as", {"classified": eid, "class": kind}, start=start, until_ceased=True)
        for cid in ends:
            self.cease(world, cid, end, reason=f"ended by event {eid}")
        new = [self.assert_fact(world, e["type"], e["roles"], start=end, until_ceased=e.get("until_ceased", True),
                                caused_by=eid) for e in effects]
        return eid, new

    def move(self, world, thing, to, at, actor=None, kind=None, as_of=None):
        """Convenience: the thing was moved to `to` at `at`. Ends the location(s) holding just before and records the
        movement event with origin/destination and the new location as its consequence."""
        just_before = _window(at).earliest - timedelta(microseconds=1)
        before = self._accepted_holding(world, "located-at", "located", thing, just_before, as_of)
        origin = sorted({p for c in before for p in c.roles.get("place", [])})
        roles = {"patient": thing, "destination": to}
        if origin:
            roles["origin"] = origin
        if actor:
            roles["actor"] = actor
        return self.record_event(world, roles, start=at, kind=kind, ends=[c.id for c in before],
                                 effects=[{"type": "located-at", "roles": {"located": thing, "place": to}}])

    # ---- existence ---------------------------------------------------------------------------------------------
    def declare_existence(self, world, thing, start=None, end=None, status="accepted"):
        """The thing exists in `world` from `start` (its creation; None: from the start of the world) until `end` or
        a recorded destruction. status="proposed" records uncertain existence (a hypothesis)."""
        return self.assert_fact(world, "existence", {"existent": thing}, start=start, end=end,
                                until_ceased=end is None, status=status)

    def create_thing(self, world, kind, name, at, alt_names=(), status="accepted", id=None):
        """Register a new thing and record that it came into existence in `world` at `at` (a time or window)."""
        rid = self.add_entity(kind, name, alt_names=alt_names, id=id)
        self.declare_existence(world, rid, start=at, status=status)
        return rid

    def destroy(self, world, thing, at, reason=None):
        """The thing stops existing in `world` at `at`. Ends its existence and every accepted fact about it that
        holds just before `at` in that world (identity links excepted). Returns the ended claim ids."""
        just_before = _window(at).earliest - timedelta(microseconds=1)
        claims = self.visible_claims(world)
        ident = self.identity(world, None, claims)
        me = set(ident.members(thing))
        ended = [c.id for c in self._effective(claims.values(), ident, just_before, None)
                 if c.type not in ("same-as", "event") and any(me & set(ids) for ids in c.roles.values())]
        for cid in ended:
            self.cease(world, cid, at, reason=reason or f"{thing} destroyed")
        return sorted(ended)

    def exists(self, world, thing, t, as_of=None):
        """Does the thing exist in `world` at t? ASSERTED from existence claims (before creation and after destruction:
        false); INFERRED true if it takes part in a fact holding at t; otherwise UNKNOWN, or NOT_YET_KNOWN when the
        world holds nothing about it. Proposed existence claims are returned as alternatives."""
        claims = self.visible_claims(world, as_of)
        ident = self.identity(world, as_of, claims)
        me = set(ident.members(thing))
        mine = [c for c in claims.values() if c.type != "same-as" and any(me & set(ids) for ids in c.roles.values())]
        ex = [c for c in mine if c.type == "existence"]
        alternatives = tuple(sorted(c.id for c in ex if status_at(c, as_of) == "proposed"))
        accepted = [c for c in ex if status_at(c, as_of) == "accepted"]
        yes = tuple(sorted(c.id for c in accepted if truth_at(c, t, as_of) is True))
        no = tuple(sorted(c.id for c in accepted if truth_at(c, t, as_of) is False))
        if yes and no:
            return Answer(Status.DISPUTED, None, support=yes + no, alternatives=alternatives)
        if yes or no:
            return Answer(Status.ASSERTED, bool(yes), support=yes or no, alternatives=alternatives)
        involved = tuple(sorted(c.id for c in self._effective(mine, ident, t, as_of) if c.type != "existence"))
        if involved:
            return Answer(Status.INFERRED, True, support=involved, alternatives=alternatives)
        if not mine:
            return Answer(Status.NOT_YET_KNOWN, alternatives=alternatives)
        return Answer(Status.UNKNOWN, alternatives=alternatives)

    # ---- reading -------------------------------------------------------------------------------------------------
    def _world_chain(self, tx, world, as_of):
        """[(world id, valid-time limit, knowledge limit)] from the world itself up through its base worlds.

        Limits are cumulative: a grandparent is seen through the parent's snapshot and then the variant's, so the
        earliest branch time and the earliest knowledge time along the path apply.
        """
        chain, vlim, klim, current = [(world, None, as_of)], None, as_of, world
        while True:
            rows = q.rows(tx, """match $v isa world, has wm-id == $world; $br isa branching (base: $b, variant: $v),
                has branch-at $at, has knowledge-at $kat, has recorded-at $rec; $b has wm-id $bid;""", {"world": current})
            rows = [r for r in rows if klim is None or q.opt(r, "rec") <= klim]
            if not rows:
                return chain
            at, kat = q.opt(rows[0], "at"), q.opt(rows[0], "kat")
            vlim = at if vlim is None else min(vlim, at)
            klim = kat if klim is None else min(klim, kat)
            current = q.opt(rows[0], "bid")
            chain.append((current, vlim, klim))

    @staticmethod
    def _claim_filter(type=None, subject=None, at=None, var="c"):
        """TypeQL patterns that select claims `$<var>` in the database: by type, by a role player, and (with `at`) only
        claims that could hold at valid time `at` (started by then and not certainly ended before it)."""
        c = f"${var}"
        parts, params = [f"{c} isa {q.label(type)};" if type else f"{c} isa claim;"], {}
        if subject is not None:
            # An existence check (double negation): binding the player here would stop a second `links` in the same
            # query from matching it again, because TypeDB matches distinct role players per `links` constraint.
            parts.append(f"not {{ not {{ {c} links ($kr: $subj); $subj has wm-id == $sid; }}; }};")
            params["sid"] = subject
        if at is not None:
            parts.append(f"{{ not {{ {c} has valid-from-latest $asl0; }}; }} or "
                         f"{{ {c} has valid-from-latest $asl1; $asl1 <= $at; }};")
            parts.append(f"not {{ {c} has valid-to-latest $ael; $ael <= $at; }};")
            params["at"] = at
        return " ".join(parts), params

    def _claims_in(self, tx, world, type=None, subject=None, klim=None, vlim=None, at=None):
        """Claims scoped to `world`, filtered in TypeQL by type, role player, transaction-time limit `klim`,
        inherited valid-time limit `vlim` (the claim must start before it) and valid time `at`."""
        filt, params = self._claim_filter(type, subject, at)
        params["world"] = world
        extra = ""
        if klim is not None:
            extra += " $c has recorded-at $krec; $krec <= $klim;"
            params["klim"] = klim
        if vlim is not None:
            extra += (" { not { $c has valid-from-earliest $vse0; }; } or"
                      " { $c has valid-from-earliest $vse1; $vse1 < $vlim; };")
            params["vlim"] = vlim
        head = f"match $w isa world, has wm-id == $world; scope (world: $w, member: $c); {filt}{extra}"
        claims = {}
        for r in q.rows(tx, head + """
            $c isa! $t, has wm-id $cid, has recorded-at $rec, has initial-status $ist, has end-basis $eb;
            try { $c has valid-from-earliest $sfe; }; try { $c has valid-from-latest $sfl; };
            try { $c has valid-to-earliest $tte; }; try { $c has valid-to-latest $ttl; };
            try { $c has clock $clk; }; try { $c has description $desc; };""", params):
            sfe, sfl, tte, ttl = (q.opt(r, v) for v in ("sfe", "sfl", "tte", "ttl"))
            cid = q.opt(r, "cid")
            claims[cid] = ClaimRecord(
                id=cid, type=r.get("t").get_label(), world=world, roles={},
                start=Window(sfe, sfl) if sfe is not None else None,
                end=Window(tte, ttl) if tte is not None else None, end_basis=q.opt(r, "eb"),
                recorded_at=q.opt(r, "rec"), initial_status=q.opt(r, "ist"), clock=q.opt(r, "clk") or "wall",
                description=q.opt(r, "desc"))
        roles = {}
        for r in q.rows(tx, head + " $c has wm-id $cid; $c links ($role: $x); $x has wm-id $xid;", params):
            roles.setdefault(q.opt(r, "cid"), {}).setdefault(r.get("role").get_label().split(":")[-1], set()).add(
                q.opt(r, "xid"))
        for cid, rs in roles.items():
            if cid in claims:
                claims[cid].roles = {role: sorted(ids) for role, ids in rs.items()}
        self.stats["queries"] += 2
        return claims

    def _cessations_in(self, tx, world, type=None, subject=None, at=None):
        filt, params = self._claim_filter(type, subject, at)
        params["world"] = world
        self.stats["queries"] += 1
        return [(q.opt(r, "cid"), Window(q.opt(r, "e"), q.opt(r, "l")), q.opt(r, "rec")) for r in q.rows(tx, f"""
            match $w isa world, has wm-id == $world; scope (world: $w, member: $s); {filt}
            $s isa cessation (ended: $c), has recorded-at $rec, has valid-to-earliest $e; $c has wm-id $cid;
            try {{ $s has valid-to-latest $l; }};""", params)]

    def _reviews_in(self, tx, world, type=None, subject=None, at=None):
        """Reviews made in `world` (of claims from this world or any base world)."""
        filt, params = self._claim_filter(type, subject, at)
        params["world"] = world
        self.stats["queries"] += 1
        return [(q.opt(r, "cid"), q.opt(r, "vd"), q.opt(r, "rec")) for r in q.rows(tx, f"""
            match $w isa world, has wm-id == $world; scope (world: $w, member: $v); {filt}
            $v isa review (reviewed: $c), has verdict $vd, has recorded-at $rec; $c has wm-id $cid;""", params)]

    def _load(self, world, as_of=None, types=None, subjects=None, at=None):
        """Claims visible in `world` as known at `as_of`, optionally only those of `types`, involving one of
        `subjects`, and able to hold at valid time `at`. All filters run in TypeDB; with none, every claim is loaded.

        Visibility: own records count if recorded by `as_of`. Records of each base world count if recorded by that
        level's knowledge limit; base claims must also start before the valid-time limit and base cessations fall
        before it. Reviews apply from the world that made them and from the worlds it inherits.
        """
        visible = {}
        with self.driver.transaction(self.database, READ) as tx:
            chain = self._world_chain(tx, world, as_of)
            for depth, (w, vlim, klim) in enumerate(chain):
                for type in (types or [None]):
                    for subj in (subjects or [None]):
                        for cid, c in self._claims_in(tx, w, type, subj, klim, vlim, at).items():
                            c.depth = depth
                            visible.setdefault(cid, c)
            for depth, (w, vlim, klim) in enumerate(chain):
                for type in (types or [None]):
                    for subj in (subjects or [None]):
                        for cid, win, rec in self._cessations_in(tx, w, type, subj, at):
                            entry = (win, rec, w)
                            if (cid in visible and (klim is None or rec <= klim) and (vlim is None or win.earliest < vlim)
                                    and entry not in visible[cid].cessations):
                                visible[cid].cessations.append(entry)
                        for cid, verdict, rec in self._reviews_in(tx, w, type, subj, at):
                            if cid in visible and (klim is None or rec <= klim) and (verdict, rec) not in visible[cid].reviews:
                                visible[cid].reviews.append((verdict, rec))
        self.stats["claims"] += len(visible)
        return visible

    def visible_claims(self, world, as_of=None):
        """Every claim visible in `world` as known at `as_of` (the full, unfiltered load)."""
        return self._load(world, as_of)

    def identity(self, world, as_of=None, claims=None):
        claims = claims if claims is not None else self._load(world, as_of, types=["same-as"])
        return Identity([c for c in claims.values() if c.type == "same-as"], as_of)

    def _identity_of(self, world, ids, as_of):
        """Identity closure for `ids`, loading only the same-as claims that touch the growing group (selective)."""
        known, frontier, same = set(ids), sorted(set(ids)), {}
        while frontier:
            same.update(self._load(world, as_of, types=["same-as"], subjects=frontier))
            ident = Identity(same.values(), as_of)
            group = {m for i in ids for m in ident.members(i)}
            frontier = sorted(group - known)
            known |= group
        return Identity(same.values(), as_of)

    def _view(self, world, as_of, type, subject_ids, at=None):
        """(claims, identity) for a question about `subject_ids`: selective by default, the full load otherwise."""
        if not self.selective:
            claims = self.visible_claims(world, as_of)
            return claims, self.identity(world, as_of, claims)
        ident = self._identity_of(world, subject_ids, as_of)
        members = sorted({m for s in subject_ids for m in ident.members(s)})
        return self._load(world, as_of, types=[type], subjects=members, at=at), ident

    def _accepted_holding(self, world, type, key_role, subject, t, as_of):
        """Accepted claims of `type` about the subject (identity-aware) that certainly hold at t."""
        claims, ident = self._view(world, as_of, type, [subject], at=t)
        subjects = set(ident.members(subject))
        return [c for c in claims.values() if c.type == type and subjects & set(c.roles.get(key_role, []))
                and status_at(c, as_of) == "accepted" and truth_at(c, t, as_of) is True]

    @staticmethod
    def _effective(claims, ident, t, as_of):
        """Accepted claims that certainly hold at t, after world precedence: for a functional type, a claim from a
        nearer world (the variant itself before its base) overrides inherited claims about the same subject."""
        holding = [c for c in claims if status_at(c, as_of) == "accepted" and truth_at(c, t, as_of) is True]
        nearest = {}
        for c in holding:
            if c.type in FUNCTIONAL:
                for x in c.roles.get(FUNCTIONAL[c.type][0], []):
                    k = (c.type, ident.canonical(x))
                    nearest[k] = min(nearest.get(k, c.depth), c.depth)
        def kept(c):
            if c.type not in FUNCTIONAL:
                return True
            return all(c.depth == nearest[(c.type, ident.canonical(x))] for x in c.roles.get(FUNCTIONAL[c.type][0], []))
        return [c for c in holding if kept(c)]

    def value_at(self, world, type, subject, t, as_of=None, key_role=None, value_role=None):
        """The value(s) of a relationship for `subject` at valid time t, as known at transaction time `as_of`.

        For functional types (located-at) more than one value is DISPUTED, and a nearer world's claim overrides
        inherited ones. Other types can hold several values; a variant removes an inherited one by ceasing it.
        """
        key_role, value_role = (key_role, value_role) if key_role else FUNCTIONAL[type]
        claims, ident = self._view(world, as_of, type, [subject], at=t)
        subjects = set(ident.members(subject))
        about = [c for c in claims.values() if c.type == type and subjects & set(c.roles.get(key_role, []))]
        if not about:
            if self.selective:     # nothing could hold at t; was anything about the subject recorded at all?
                anything, _ = self._view(world, as_of, type, [subject])
                if any(c.type == type and subjects & set(c.roles.get(key_role, [])) for c in anything.values()):
                    return Answer(Status.UNKNOWN)
            return Answer(Status.NOT_YET_KNOWN)
        holding = self._effective(about, ident, t, as_of)      # precedence applies to functional types only
        alternatives = tuple(sorted(c.id for c in about if status_at(c, as_of) == "proposed"
                                    and truth_at(c, t, as_of) is True))
        values = sorted({ident.canonical(v) for c in holding for v in c.roles.get(value_role, [])})
        support = tuple(sorted(c.id for c in holding))
        if not values:
            return Answer(Status.UNKNOWN, alternatives=alternatives)
        if type in FUNCTIONAL and len(values) > 1:
            return Answer(Status.DISPUTED, values=tuple(values), support=support, alternatives=alternatives)
        return Answer(Status.ASSERTED, values=tuple(values), support=support, alternatives=alternatives)

    def holds(self, world, type, roles, t, as_of=None):
        """Does this relationship hold at t? ASSERTED true/false from claims and cessations; INFERRED false when a
        functional relationship certainly has another value; DISPUTED when accepted claims disagree."""
        ids = sorted({x for v in roles.values() for x in ([v] if isinstance(v, str) else v)})
        key = FUNCTIONAL[type][0] if type in FUNCTIONAL and FUNCTIONAL[type][0] in roles else next(iter(sorted(roles)))
        anchor = sorted([roles[key]] if isinstance(roles[key], str) else roles[key])
        if self.selective:
            ident = self._identity_of(world, ids, as_of)
            members = sorted({m for a in anchor for m in ident.members(a)})
            claims = self._load(world, as_of, types=[type], subjects=members)
        else:
            claims = self.visible_claims(world, as_of)
            ident = self.identity(world, as_of, claims)
        want = {r: {ident.canonical(x) for x in ([v] if isinstance(v, str) else v)} for r, v in roles.items()}

        def matches(c):
            return all(want[r] <= {ident.canonical(x) for x in c.roles.get(r, [])} for r in want)

        about = [c for c in claims.values() if c.type == type and matches(c)]
        if type in FUNCTIONAL:                       # include the subject's other values, for precedence
            key = FUNCTIONAL[type][0]
            peers = [c for c in claims.values() if c.type == type and key in want
                     and want[key] <= {ident.canonical(x) for x in c.roles.get(key, [])}]
        else:
            peers = about
        effective = {c.id for c in self._effective(peers, ident, t, as_of)}
        accepted = [c for c in about if status_at(c, as_of) == "accepted"]
        yes = tuple(sorted(c.id for c in accepted if c.id in effective))
        no = tuple(sorted(c.id for c in accepted if truth_at(c, t, as_of) is False))
        alternatives = tuple(sorted(c.id for c in about if status_at(c, as_of) == "proposed"))
        if yes and no:
            return Answer(Status.DISPUTED, None, support=yes + no, alternatives=alternatives)
        if yes:
            return Answer(Status.ASSERTED, True, support=yes, alternatives=alternatives)
        if no:
            return Answer(Status.ASSERTED, False, support=no, alternatives=alternatives)
        if type in FUNCTIONAL:
            key, val = FUNCTIONAL[type]
            if key in roles and val in roles:
                other = self.value_at(world, type, next(iter(want[key])), t, as_of)
                if other.status == Status.ASSERTED and not set(other.values) & want[val]:
                    return Answer(Status.INFERRED, False, support=other.support, alternatives=alternatives)
        if not about:
            return Answer(Status.NOT_YET_KNOWN, alternatives=alternatives)
        return Answer(Status.UNKNOWN, alternatives=alternatives)

    def facts_about(self, world, subject, t, as_of=None):
        """Every accepted, non-event claim involving the subject (in any role) that certainly holds at t."""
        claims = self.visible_claims(world, as_of)
        ident = self.identity(world, as_of, claims)
        subjects = set(ident.members(subject))
        out = []
        for c in sorted(claims.values(), key=lambda c: c.id):
            if c.type in ("event", "same-as") or status_at(c, as_of) != "accepted":
                continue
            if any(subjects & set(ids) for ids in c.roles.values()) and truth_at(c, t, as_of) is True:
                out.append({"claim": c.id, "type": c.type, "roles": {r: sorted(v) for r, v in c.roles.items()}})
        return out

    def history(self, world, subject, type=None, as_of=None):
        """All visible claims involving the subject, oldest first, with their status at `as_of` and endings."""
        claims = self.visible_claims(world, as_of)
        subjects = set(self.identity(world, as_of, claims).members(subject))
        rows = []
        for c in claims.values():
            if (type is None or c.type == type) and any(subjects & set(ids) for ids in c.roles.values()):
                rows.append({"claim": c.id, "type": c.type, "roles": {r: sorted(v) for r, v in c.roles.items()},
                             "start": c.start, "end": c.end, "end_basis": c.end_basis,
                             "ceased": sorted((w.earliest for w, _, _ in c.cessations)),
                             "status": status_at(c, as_of), "recorded_at": c.recorded_at, "world_depth": c.depth})
        far_past = datetime.min.replace(tzinfo=timezone.utc)
        return sorted(rows, key=lambda r: (r["start"].earliest if r["start"] else far_past, r["claim"]))

    def events(self, world, participant=None, as_of=None):
        """Accepted events in the world, ordered by start window, with roles and kinds (concept ids)."""
        claims = self.visible_claims(world, as_of)
        ident = self.identity(world, as_of, claims)
        who = set(ident.members(participant)) if participant else None
        kinds = {}
        for c in claims.values():
            if c.type == "classified-as" and status_at(c, as_of) == "accepted":
                for x in c.roles.get("classified", []):
                    kinds.setdefault(x, []).extend(c.roles.get("class", []))
        evs = [c for c in claims.values() if c.type == "event" and status_at(c, as_of) == "accepted"
               and (who is None or any(who & set(ids) for ids in c.roles.values()))]
        evs.sort(key=lambda c: (c.start.earliest, c.start.latest, c.id))
        return [{"event": c.id, "roles": {r: sorted(v) for r, v in c.roles.items()}, "kinds": sorted(kinds.get(c.id, [])),
                 "start": c.start, "end": c.end, "record": c} for c in evs]

    @staticmethod
    def certainly_before(a, b):
        return certainly_before(a["record"], b["record"])

    def find(self, name, world=None, as_of=None):
        """Referent ids whose name or alt-name equals `name`. Several matches are returned, never resolved.

        Without `world`, this searches the global identity register. With `world`, only things the world says
        anything about (an existence claim or any fact visible there) are returned, so things from other worlds
        never appear in its answers."""
        with self.driver.transaction(self.database, READ) as tx:
            ids = {q.opt(r, "id") for r in q.rows(tx, """match $x isa referent, has wm-id $id;
                { $x has name == $n; } or { $x has alt-name == $n; };""", {"n": name})}
        if world is not None:
            mentioned = {x for c in self.visible_claims(world, as_of).values() for v in c.roles.values() for x in v}
            ids &= mentioned
        return sorted(ids)

    def parts(self, world, whole, t, as_of=None):
        """Transitive parts of `whole` at valid time t (application closure over holding part-of claims)."""
        return self._closure(world, "part-of", "whole", "part", whole, t, as_of)

    def dependencies(self, world, dependent, t, as_of=None):
        return self._closure(world, "depends-on", "dependent", "dependee", dependent, t, as_of)

    def _closure(self, world, type, from_role, to_role, start, t, as_of):
        claims = self.visible_claims(world, as_of)
        edges = {}
        for c in claims.values():
            if c.type == type and status_at(c, as_of) == "accepted" and truth_at(c, t, as_of) is True:
                for a in c.roles.get(from_role, []):
                    edges.setdefault(a, set()).update(c.roles.get(to_role, []))
        seen, todo = set(), [start]
        while todo:
            for n in edges.get(todo.pop(), ()):
                if n not in seen:
                    seen.add(n)
                    todo.append(n)
        return sorted(seen)

    def parts_in_database(self, world, whole):
        """Transitive parts computed by the TypeDB function `parts_in` (world-scoped; ignores time and status)."""
        with self.driver.transaction(self.database, READ) as tx:
            return sorted({q.opt(r, "pid") for r in q.rows(tx, """match $x isa referent, has wm-id == $whole;
                $w isa world, has wm-id == $world; let $p in parts_in($x, $w); $p has wm-id $pid;""",
                {"whole": whole, "world": world})})
