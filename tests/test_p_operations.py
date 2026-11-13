"""Increment A of the pre-Stage E corrections (DI-8, LABS-1.036): atomic logical operations.

Every write belonging to one logical operation shares one transaction and one recorded time; reads inside it see its
own writes; nested writers join it; a failure at any point (any write, an error caught inside, a schema change inside a
data operation, the commit) leaves no data, no schema change, no database (for create) and no advance of the model's
recorded-time watermark. Failures are injected at every write of every composite writer.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from typedb.driver import TransactionType

import conftest
from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel, laboratory as lb, mechanical as mech
from worldmodel import typeql as q
from worldmodel.model import DEFAULT_MODULES
from worldmodel.operations import OperationError

pytestmark = pytest.mark.own_profiles
WRITE_Q = re.compile(r"\b(insert|delete|define|undefine|redefine|put|update)\b")
COUNTED = ("attestation", "event", "proposition", "particular", "concept", "reference-system", "world", "acceptance",
           "functional-slot", "schema-module", "information-object", "supersession", "rests-on", "branching")


def T(day, h=9):
    return datetime(2026, 11, day, h, tzinfo=timezone.utc)


class Injected(ConnectionError):
    """A simulated connection loss."""


class FaultyTx:
    def __init__(self, tx, driver, kind):
        self._tx, self._d, self._kind = tx, driver, kind

    def query(self, text, *a, **k):
        if self._kind != TransactionType.READ and WRITE_Q.search(text):
            self._d.writes += 1
            if self._d.fail_at == self._d.writes:
                raise Injected(f"injected failure at write {self._d.writes}")
        return self._tx.query(text, *a, **k)

    def commit(self):
        if self._d.fail_commit:
            raise Injected("injected failure at commit")
        return self._tx.commit()

    def __enter__(self):
        self._tx.__enter__()
        return self

    def __exit__(self, *exc):
        return self._tx.__exit__(*exc)

    def __getattr__(self, name):
        return getattr(self._tx, name)


class FaultyDriver:
    def __init__(self, real):
        self._real, self.fail_at, self.writes, self.fail_commit = real, None, 0, False

    def transaction(self, db, kind, *a, **k):
        return FaultyTx(self._real.transaction(db, kind, *a, **k), self, kind)

    def __getattr__(self, name):
        return getattr(self._real, name)


def fingerprint(driver, db):
    if not driver.databases.contains(db):
        return {"database": False}
    out = {"database": True, "schema": driver.databases.get(db).schema()}
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
    return out


def make(driver, modules=CORE_MODULES, profiles=("mechanical", "laboratory")):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    saved, conftest.AUTO_PROFILES["on"] = conftest.AUTO_PROFILES["on"], False
    try:
        wm = WorldModel.create(name, driver=driver, modules=modules, clock=FakeClock())
    finally:
        conftest.AUTO_PROFILES["on"] = saved
    for p in profiles:
        wm.install_profile(p)
    return wm


def drop(wm):
    if wm.driver.databases.contains(wm.database):
        wm.driver.databases.get(wm.database).delete()


def world(wm):
    w = wm.create_world("w", id="w")
    for i in ("ana", "bo", "core-1", "housing", "b1", "b2", "box"):
        wm.add_entity("physical-object", i, id=i)
    wm.add_entity("place", "shelf", id="shelf")
    for c in ("inspection", "measurement"):
        wm.add_entity("category", c, id=c)
    wm.add_entity("occurrence", "occ", id="occ")
    wm.define_quality_kind("mass", dimension="mass", id="mass")
    wm.define_unit("kilogram", "mass", id="kg")
    return w


def recorded_times(wm, ids):
    with wm._reading() as tx:
        return {q.opt(r, "r") for i in ids for r in q.rows(tx, "match $x has wm-id == $id, has recorded-at $r;",
                                                           {"id": i})}


@pytest.fixture(scope="module")
def base(driver):
    wm = make(driver)
    try:
        yield wm, world(wm)
    finally:
        drop(wm)


def tag():
    return uuid.uuid4().hex[:6]


# ---- every composite writer: rollback at each of its writes -------------------------------------------------------------
def op_account(wm, w, setup):
    if not setup:
        return wm.account(w, {"actor": "ana", "patient": "box"}, T(2), T(2), kind="inspection", occurrence="occ",
                          attester="ana")


def op_claim_effect(wm, w, setup, state={}):
    if setup:
        x = state["x"] = f"thing-{tag()}"
        wm.add_entity("physical-object", x, id=x)
        state["e"] = wm.account(w, {"actor": "ana"}, T(2), T(2), attester="ana")
        return
    return wm.claim_effect(w, state["e"], "initiates", "existence", {"existent": state["x"]}, attester="ana")


def op_take_sample(wm, w, setup, state={}):
    if setup:
        state["s"] = f"s-{tag()}"
        wm.add_entity("sample", state["s"], id=state["s"])
        return
    return lb.take_sample(wm, w, "ana", "core-1", state["s"], start=T(3), attester="ana")


def op_replace_part(wm, w, setup):
    if not setup:
        return mech.replace_part(wm, w, "housing", "b1", "b2", start=T(3), attester="bo")


def op_record_event(wm, w, setup, state={}):
    if setup:
        state["old"] = wm.attest(w, "located-at", {"located": "box", "place": "shelf"}, start=T(1),
                                 until_superseded=True)
        return
    return wm.record_event(w, {"actor": "bo", "patient": "box"}, T(4), kind="inspection", ends=[state["old"]],
                           effects=[{"type": "part-of", "roles": {"part": "box", "whole": "housing"}}], attester="bo")


def op_create_thing(wm, w, setup):
    if not setup:
        return wm.create_thing(w, "physical-object", "widget", T(2), id=f"widget-{tag()}")


def op_destroy(wm, w, setup, state={}):
    if setup:
        x = state["x"] = f"crate-{tag()}"
        wm.create_thing(w, "physical-object", "crate", T(1), id=x)
        wm.attest(w, "located-at", {"located": x, "place": "shelf"}, start=T(1), until_superseded=True)
        wm.accept(wm.attest(w, "part-of", {"part": x, "whole": "housing"}, start=T(1), until_superseded=True,
                            attester="bo"))
        return
    return wm.destroy(w, state["x"], T(5))


def op_measure(wm, w, setup):
    if not setup:
        return wm.measure(w, "box", "mass", 2.0, "kg", 0.1, start=T(2), operator="ana", attester="ana")


def op_define_unit(wm, w, setup):
    if not setup:
        return wm.define_unit("gram", "mass", si_factor=0.001, id=f"g-{tag()}")


def op_end(wm, w, setup, state={}):
    if setup:
        state["a"] = wm.attest(w, "part-of", {"part": "b1", "whole": "housing"}, start=T(1), until_superseded=True)
        return
    return wm.end(w, state["a"], T(6))


WRITERS = [op_account, op_claim_effect, op_take_sample, op_replace_part, op_record_event, op_create_thing, op_destroy,
           op_measure, op_define_unit, op_end]


@pytest.mark.parametrize("op", WRITERS, ids=lambda f: f.__name__[3:])
def test_a_failure_at_any_write_leaves_nothing(base, driver, op):
    wm, w = base
    faulty = FaultyDriver(driver)
    real, wm.driver = wm.driver, faulty
    try:
        op(wm, w, True)
        faulty.writes = 0
        op(wm, w, False)                                    # a clean run: how many writes the operation makes
        writes = faulty.writes
        assert writes >= 1
        failed = 0
        for k in range(1, writes + 1):
            op(wm, w, True)
            before, mark = fingerprint(driver, wm.database), wm._last_recorded
            faulty.writes, faulty.fail_at = 0, k
            try:
                op(wm, w, False)
            except Injected:
                failed += 1
                assert fingerprint(driver, wm.database) == before, f"partial data after a failure at write {k}"
                assert wm._last_recorded == mark, f"the recorded-time watermark moved after a failure at write {k}"
            finally:
                faulty.fail_at = None
        assert failed >= 1
        # and at commit
        op(wm, w, True)
        before, mark = fingerprint(driver, wm.database), wm._last_recorded
        faulty.fail_commit = True
        with pytest.raises(Injected):
            op(wm, w, False)
        faulty.fail_commit = False
        assert fingerprint(driver, wm.database) == before and wm._last_recorded == mark
    finally:
        wm.driver = real


# ---- module installation, upgrade, profile installation and database creation ------------------------------------------
def failing_everywhere(driver, prepare, run):
    faulty = FaultyDriver(driver)
    wm = prepare()
    wm.driver, faulty.writes = faulty, 0
    run(wm)
    writes = faulty.writes
    drop(wm)
    for k in range(1, writes + 1):
        wm = prepare()
        wm.driver = faulty
        before, mark = fingerprint(driver, wm.database), wm._last_recorded
        faulty.writes, faulty.fail_at = 0, k
        try:
            with pytest.raises(Exception):
                run(wm)
            assert fingerprint(driver, wm.database) == before, f"partial installation after a failure at write {k}"
            assert wm._last_recorded == mark
        finally:
            faulty.fail_at = None
            wm.driver = driver
            drop(wm)
    return writes


def test_install_module_is_one_operation(driver):
    prepare = lambda: make(driver, modules=DEFAULT_MODULES, profiles=())
    assert failing_everywhere(driver, prepare, lambda m: m.install_module("core-0.4-a")) == 3


def test_upgrade_to_a0_is_one_operation(driver):
    def prepare():
        m = make(driver, modules=("core",), profiles=())
        w = m.create_world("w", id="w")
        m.add_entity("physical-object", "x", id="x")
        m.add_entity("place", "p", id="p")
        m.attest(w, "located-at", {"located": "x", "place": "p"}, start=T(1), until_superseded=True)
        return m
    assert failing_everywhere(driver, prepare, lambda m: m.upgrade_to_a0()) >= 4
    m = prepare()                                       # and the upgrade itself still works, in one operation
    try:
        assert m.upgrade_to_a0() == 1 and m.has_proposition_ids()
        assert m.holds("w", "located-at", {"located": "x", "place": "p"}, T(2)).holds is True
    finally:
        drop(m)


def test_install_profile_is_one_operation(driver):
    prepare = lambda: make(driver, profiles=())
    assert failing_everywhere(driver, prepare, lambda m: m.install_profile("laboratory")) >= 3


def test_a_failed_create_leaves_no_database(driver):
    faulty = FaultyDriver(driver)
    names = []
    for k in (1, 8, 20):
        name = f"wm-test-{uuid.uuid4().hex[:10]}"
        names.append(name)
        faulty.writes, faulty.fail_at = 0, k
        saved, conftest.AUTO_PROFILES["on"] = conftest.AUTO_PROFILES["on"], False
        try:
            with pytest.raises(Injected):
                WorldModel.create(name, driver=faulty, modules=CORE_MODULES, clock=FakeClock())
        finally:
            conftest.AUTO_PROFILES["on"] = saved
            faulty.fail_at = None
        assert not driver.databases.contains(name)


# ---- the operation API: nesting, own reads, one recorded time, isolation --------------------------------------------------
def test_a_caller_groups_object_creation_and_its_account(base, driver):
    """Requirement 2: the sample itself and the account of taking it are one operation."""
    wm, w = base
    s = f"s-{tag()}"
    with wm.operation() as op:
        wm.add_entity("sample", s, id=s)
        assert wm.find(s) == [s]                                       # reads see the operation's own writes
        out = lb.take_sample(wm, w, "ana", "core-1", s, start=T(3), attester="ana")
        assert wm.content(out["event"])["roles"]["product"] == [s]
        other = WorldModel.open(wm.database, driver=driver)
        assert other.find(s) == []                                     # isolation: nothing visible outside yet
        assert op.recorded_at is not None
    assert WorldModel.open(wm.database, driver=driver).find(s) == [s]
    ids = [out["event"], *out["effects"], *wm.account_attestations(w, out["event"])]
    assert recorded_times(wm, [i for i in ids if i.startswith("att")]) == {op.recorded_at}


def test_a_user_error_inside_an_operation_writes_nothing(base, driver):
    wm, w = base
    before, mark = fingerprint(driver, wm.database), wm._last_recorded
    with pytest.raises(RuntimeError, match="changed my mind"):
        with wm.operation():
            wm.add_entity("physical-object", "ghost", id=f"ghost-{tag()}")
            mech.replace_part(wm, w, "housing", "b1", "b2", start=T(4), attester="bo")
            raise RuntimeError("changed my mind")
    assert fingerprint(driver, wm.database) == before and wm._last_recorded == mark


def local_size(wm):
    """Ownerships visible to the current operation's transaction (its own uncommitted writes included)."""
    with wm._reading() as tx:
        return len(q.rows(tx, "match $x has $a;"))


def test_a_caught_inner_failure_still_writes_nothing(base, driver):
    """A nested writer fails after it has made transaction-local changes, and the caller catches the error: the
    enclosing operation is marked for rollback, so nothing persists and the recorded-time watermark does not move."""
    wm, w = base
    # a validation error, raised before the nested writer writes anything
    before, mark = fingerprint(driver, wm.database), wm._last_recorded
    with pytest.raises(OperationError, match="caught"):
        with wm.operation():
            wm.add_entity("physical-object", "ghost", id=f"ghost-{tag()}")
            try:
                wm.attest(w, "part-of", {"part": "no-such-thing", "whole": "housing"}, start=T(1))
            except ValueError:
                pass                                                   # swallowed: the operation must not commit
    assert fingerprint(driver, wm.database) == before and wm._last_recorded == mark

    # a connection failure at each of the nested writer's own writes after its first
    faulty = FaultyDriver(driver)
    real, wm.driver = wm.driver, faulty
    try:
        op_take_sample(wm, w, True)
        faulty.writes = 0
        op_take_sample(wm, w, False)                                   # a clean run: the nested writer's writes
        nested = faulty.writes
        assert nested >= 2
        for k in range(2, nested + 1):
            s = f"s-{tag()}"
            before, mark = fingerprint(driver, wm.database), wm._last_recorded
            caught = False
            with pytest.raises(OperationError, match="caught"):
                with wm.operation():
                    wm.add_entity("sample", s, id=s)
                    outer = local_size(wm)
                    faulty.writes, faulty.fail_at = 0, k               # k - 1 nested writes made before the failure
                    try:
                        lb.take_sample(wm, w, "ana", "core-1", s, start=T(3), attester="ana")
                    except Injected:
                        caught = True
                        assert faulty.writes == k
                        assert local_size(wm) > outer                  # the nested writes are in the transaction
                        at = wm._op.recorded_at                        # and the nested writer took the operation's time
                        assert at is not None and at > mark
                    finally:
                        faulty.fail_at = None
            assert caught
            assert fingerprint(driver, wm.database) == before, f"partial data after a caught failure at nested write {k}"
            assert wm._last_recorded == mark, f"the watermark moved after a caught failure at nested write {k}"
    finally:
        wm.driver = real


def test_a_schema_change_cannot_join_a_data_operation(driver):
    wm = make(driver, modules=DEFAULT_MODULES, profiles=())
    try:
        before = fingerprint(driver, wm.database)
        with pytest.raises(OperationError, match="schema change"):
            with wm.operation():
                wm.add_entity("physical-object", "x", id="x")
                wm.install_module("core-0.4-a")
        assert fingerprint(driver, wm.database) == before
        with wm.operation(schema=True):                                 # a schema operation takes both
            wm.install_module("core-0.4-a")
            wm.add_entity("physical-object", "x", id="x")
        assert "core-0.4-a" in wm.modules() and wm.find("x") == ["x"]
    finally:
        drop(wm)


def test_one_recorded_time_per_operation_and_monotonic_after_a_rollback(base, driver):
    wm, w = base
    out = mech.replace_part(wm, w, "housing", "b1", "b2", start=T(5), attester="bo")
    first = recorded_times(wm, [*out["effects"], *wm.account_attestations(w, out["event"])])
    assert len(first) == 1
    with pytest.raises(RuntimeError):
        with wm.operation():
            wm.attest(w, "part-of", {"part": "b2", "whole": "housing"}, start=T(5), until_superseded=True)
            raise RuntimeError("abandon")
    second = wm.attest(w, "part-of", {"part": "b2", "whole": "housing"}, start=T(5), until_superseded=True)
    assert recorded_times(wm, [second]).pop() > first.pop()


def test_the_registered_di8_case_is_gone(base, driver):
    """LABS-1.030: a connection lost before take_sample's second effect claim kept the account with one claim."""
    wm, w = base
    s = f"s-{tag()}"
    wm.add_entity("sample", s, id=s)
    real = wm.claim_effect.__func__
    calls = {"n": 0}

    def failing(self, *a, **k):
        calls["n"] += 1
        if calls["n"] == 2:
            raise ConnectionError("lost before the second effect claim")
        return real(self, *a, **k)
    before = fingerprint(driver, wm.database)
    WorldModel.claim_effect, saved = failing, WorldModel.claim_effect
    try:
        with pytest.raises(ConnectionError):
            lb.take_sample(wm, w, "ana", "core-1", s, start=T(6), attester="ana", id=f"sampling-{tag()}")
    finally:
        WorldModel.claim_effect = saved
    assert fingerprint(driver, wm.database) == before


def test_rollback_forgets_cached_schema_reads(driver):
    wm = make(driver, modules=("core",), profiles=())
    try:
        assert wm.has_proposition_ids() is False
        with pytest.raises(RuntimeError):
            with wm.operation(schema=True):
                wm.upgrade_to_a0()
                assert wm.has_proposition_ids() is True                # seen inside the operation
                raise RuntimeError("abandon the upgrade")
        assert wm.has_proposition_ids() is False and "core-0.4-a0" not in wm.modules()
    finally:
        drop(wm)
