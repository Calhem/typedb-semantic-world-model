"""Increment A (DI-8, LABS-1.036): atomicity of every composite writer, measured by fault injection.

For each writer: one successful call counts its write queries, the distinct recorded times it writes, and its time;
then, for every write query k, the k-th write is made to fail (a simulated connection loss) and the probe records what
persisted: new attestations, events, propositions, things, worlds, acceptances, slots, module records, records,
supersessions and schema text, the database itself (for create), and whether the model's recorded-time watermark
moved. Run before and after the change; the same probe is the impact baseline and the check.

Usage: uv run python -I probes/pre_e_a_atomicity.py <repo> [--out FILE]
Throwaway databases wm-probe-atom-* are deleted afterwards.
"""

import json
import re
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve() / "src"))
from typedb.driver import TransactionType  # noqa: E402
from worldmodel import CORE_MODULES, WorldModel, connect, laboratory as lb, mechanical as mech  # noqa: E402
from worldmodel import typeql as q  # noqa: E402

WRITE_Q = re.compile(r"\b(insert|delete|define|undefine|redefine|put|update)\b")
COUNTED = ("attestation", "event", "proposition", "particular", "concept", "reference-system", "world", "acceptance",
           "functional-slot", "schema-module", "information-object", "supersession", "rests-on", "branching")


def T(day, h=9):
    return datetime(2026, 11, day, h, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


class Injected(ConnectionError):
    pass


class FaultyTx:
    def __init__(self, tx, driver, kind):
        self._tx, self._d, self._kind = tx, driver, kind

    def query(self, text, *a, **k):
        if self._kind != TransactionType.READ and WRITE_Q.search(text):
            self._d.writes += 1
            if self._d.fail_at == self._d.writes:
                raise Injected(f"injected failure at write {self._d.writes}")
        return self._tx.query(text, *a, **k)

    def __enter__(self):
        self._tx.__enter__()
        return self

    def __exit__(self, *exc):
        return self._tx.__exit__(*exc)

    def __getattr__(self, name):
        return getattr(self._tx, name)


class FaultyDriver:
    def __init__(self, real):
        self._real, self.fail_at, self.writes, self.armed, self.before = real, None, 0, None, None

    def transaction(self, db, kind, *a, **k):
        return FaultyTx(self._real.transaction(db, kind, *a, **k), self, kind)

    def __getattr__(self, name):
        return getattr(self._real, name)


def fingerprint(driver, db):
    if not driver.databases.contains(db):
        return {"database": False}
    out = {"database": True, "schema": hash(driver.databases.get(db).schema())}
    with driver.transaction(db, TransactionType.READ) as tx:
        for t in COUNTED:
            try:
                out[t] = len(q.rows(tx, f"match $x isa {t};"))
            except Exception:
                out[t] = None
        try:
            out["ownerships"] = len(q.rows(tx, "match $x has $a;"))
        except Exception:
            out["ownerships"] = None
        try:
            out["recorded-times"] = len({q.opt(r, "r") for r in q.rows(tx, "match $x has recorded-at $r;")})
        except Exception:
            out["recorded-times"] = None
    return out


def diff(a, b):
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


real = connect()
made = []


def new_db(modules=CORE_MODULES, profiles=("mechanical", "laboratory")):
    name = f"wm-probe-atom-{uuid.uuid4().hex[:8]}"
    made.append(name)
    wm = WorldModel.create(name, driver=real, modules=modules, clock=Clock())
    for p in profiles:
        wm.install_profile(p)
    return wm


def setup(wm):
    w = wm.create_world("w", id="w")
    for i in ("ana", "bo", "core-1", "housing", "b1", "b2", "box"):
        wm.add_entity("physical-object", i, id=i)
    wm.add_entity("place", "shelf", id="shelf")
    wm.add_entity("category", "inspection", id="inspection")
    wm.add_entity("category", "measurement", id="measurement")
    wm.add_entity("occurrence", "occ", id="occ")
    wm.define_quality_kind("mass", dimension="mass", id="mass")
    wm.define_unit("kilogram", "mass", id="kg")
    return w


def tag():
    return uuid.uuid4().hex[:6]


def arm(wm):
    """Setup is done: from here the scenario's logical operation runs. Take the before-picture, start counting writes
    and arm the injected failure."""
    d = wm.driver
    d.before, d.mark = fingerprint(d._real, wm.database), wm._last_recorded
    d.writes, d.fail_at = 0, d.armed


# each scenario: (name, needs-fresh-database, function(wm, w) performing one logical operation)
def s_account(wm, w):
    arm(wm)
    wm.account(w, {"actor": "ana", "patient": "box"}, T(2), T(2), kind="inspection", occurrence="occ", attester="ana")


def s_claim_effect(wm, w):
    x = f"thing-{tag()}"
    wm.add_entity("physical-object", x, id=x)
    e = wm.account(w, {"actor": "ana"}, T(2), T(2), attester="ana")
    arm(wm)
    wm.claim_effect(w, e, "initiates", "existence", {"existent": x}, attester="ana")


def s_take_sample(wm, w):
    s = f"s-{tag()}"
    wm.add_entity("sample", s, id=s)
    arm(wm)
    lb.take_sample(wm, w, "ana", "core-1", s, start=T(3), attester="ana")


def s_replace_part(wm, w):
    arm(wm)
    mech.replace_part(wm, w, "housing", "b1", "b2", start=T(3), attester="bo")


def s_record_event(wm, w):
    old = wm.attest(w, "located-at", {"located": "box", "place": "shelf"}, start=T(1), until_superseded=True)
    arm(wm)
    wm.record_event(w, {"actor": "bo", "patient": "box"}, T(4), kind="inspection", ends=[old],
                    effects=[{"type": "part-of", "roles": {"part": "box", "whole": "housing"}}], attester="bo")


def s_create_thing(wm, w):
    arm(wm)
    wm.create_thing(w, "physical-object", "widget", T(2), id=f"widget-{tag()}")


def s_destroy(wm, w):
    x = f"crate-{tag()}"
    wm.create_thing(w, "physical-object", "crate", T(1), id=x)
    wm.attest(w, "located-at", {"located": x, "place": "shelf"}, start=T(1), until_superseded=True)
    other = wm.attest(w, "part-of", {"part": x, "whole": "housing"}, start=T(1), until_superseded=True, attester="bo")
    wm.accept(other)
    arm(wm)
    wm.destroy(w, x, T(5))


def s_measure(wm, w):
    arm(wm)
    wm.measure(w, "box", "mass", 2.0, "kg", 0.1, start=T(2), operator="ana", attester="ana")


def s_define_unit(wm, w):
    arm(wm)
    wm.define_unit("gram", "mass", si_factor=0.001, id=f"g-{tag()}")


def s_end(wm, w):
    a = wm.attest(w, "part-of", {"part": "b1", "whole": "housing"}, start=T(1), until_superseded=True)
    arm(wm)
    wm.end(w, a, T(6))


SCENARIOS = [("account (kind + occurrence)", s_account), ("claim_effect (new outcome)", s_claim_effect),
             ("take_sample", s_take_sample), ("replace_part", s_replace_part), ("record_event", s_record_event),
             ("create_thing", s_create_thing), ("destroy", s_destroy), ("measure", s_measure),
             ("define_unit", s_define_unit), ("end", s_end)]


def run(wm, fn, w, fail_at):
    """Run one scenario; its operation fails at its write `fail_at` (None: no failure). Returns (error, persisted,
    watermark moved), measured from the scenario's arm point."""
    drv = wm.driver
    drv.armed, drv.fail_at = fail_at, None
    err = None
    try:
        fn(wm, w)
    except Injected as e:
        err = str(e)
    finally:
        drv.fail_at = drv.armed = None
    return err, diff(drv.before, fingerprint(real, wm.database)), wm._last_recorded != drv.mark


results = {}
try:
    wm = new_db()
    wm.driver = FaultyDriver(real)
    w = setup(wm)
    for name, fn in SCENARIOS:
        t0 = time.perf_counter()
        _, ok_diff, _ = run(wm, fn, w, None)
        seconds = time.perf_counter() - t0
        writes = wm.driver.writes
        rows = []
        for k in range(1, writes + 1):
            err, persisted, moved = run(wm, fn, w, k)
            rows.append({"fail_at": k, "raised": bool(err), "persisted": persisted, "watermark_moved": moved})
        r = ok_diff.get("recorded-times")
        results[name] = {"writes": writes, "seconds": round(seconds, 3),
                         "recorded_times_written": (r[1] - r[0]) if r else 0, "failures": rows}

    # module installation, upgrade and database creation, each on fresh databases
    def module_case(name, prepare, op):
        wm0 = prepare()
        drv = FaultyDriver(real)
        wm0.driver = drv
        drv.fail_at, drv.writes = None, 0
        t0 = time.perf_counter()
        op(wm0)
        secs = time.perf_counter() - t0
        writes = drv.writes
        rows = []
        for k in range(1, writes + 1):
            wmk = prepare()
            dk = FaultyDriver(real)
            wmk.driver = dk
            b, mark = fingerprint(real, wmk.database), wmk._last_recorded
            dk.fail_at, dk.writes = k, 0
            try:
                op(wmk)
                err = None
            except Injected as e:
                err = str(e)
            a = fingerprint(real, wmk.database)
            rows.append({"fail_at": k, "raised": bool(err), "persisted": diff(b, a),
                         "watermark_moved": wmk._last_recorded != mark})
        results[name] = {"writes": writes, "seconds": round(secs, 3), "failures": rows}

    module_case("install_module (core-0.4-a: schema, record, slot)",
                lambda: new_db(modules=("core", "core-0.4-a0"), profiles=()),
                lambda m: m.install_module("core-0.4-a"))

    def core03():
        m = new_db(modules=("core",), profiles=())
        w0 = m.create_world("w", id="w")
        m.add_entity("physical-object", "x", id="x")
        m.add_entity("place", "p", id="p")
        m.attest(w0, "located-at", {"located": "x", "place": "p"}, start=T(1), until_superseded=True)
        return m
    module_case("upgrade_to_a0", core03, lambda m: m.upgrade_to_a0())
    module_case("install_profile (control: atomic since LABS-1.023)",
                lambda: new_db(profiles=()), lambda m: m.install_profile("laboratory"))

    # WorldModel.create: a failure part-way through; is a database left behind?
    created = []
    drv = FaultyDriver(real)
    total = None
    for k in [None] + list(range(1, 40)):
        name = f"wm-probe-atom-create-{uuid.uuid4().hex[:6]}"
        made.append(name)
        drv.fail_at, drv.writes = k, 0
        try:
            WorldModel.create(name, driver=drv, modules=CORE_MODULES, clock=Clock())
            err = None
        except Injected as e:
            err = str(e)
        if k is None:
            total = drv.writes
            continue
        if k > total:
            break
        left = fingerprint(real, name)
        created.append({"fail_at": k, "raised": bool(err), "database_left": left.get("database"),
                        "modules_left": left.get("schema-module")})
    results["WorldModel.create (all core modules)"] = {"writes": total, "failures": created}

    summary = {}
    for name, r in results.items():
        failed = [f for f in r["failures"] if f["raised"]]
        partial = [f["fail_at"] for f in failed if f.get("persisted") or f.get("database_left")]
        moved = [f["fail_at"] for f in failed if f.get("watermark_moved")]
        summary[name] = {"writes": r["writes"], "failure points": len(r["failures"]),
                         "failed": len(failed), "partial at": partial, "watermark moved at": moved,
                         "recorded times per call": r.get("recorded_times_written"), "seconds": r.get("seconds")}
    out = {"summary": summary, "detail": results}
    text = json.dumps(out, indent=1, default=str)
    if "--out" in sys.argv:
        Path(sys.argv[sys.argv.index("--out") + 1]).write_text(text + "\n")
    print(json.dumps(summary, indent=1, default=str))
finally:
    for n in made:
        if real.databases.contains(n):
            real.databases.get(n).delete()
