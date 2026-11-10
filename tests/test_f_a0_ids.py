"""Core 0.4 Stage A0.1 (LABS-1.002): deterministic, immutable proposition identifiers (`wm-id`).

The canonical key keeps its meaning (structural identity of content); the id is derived from it, so the same content
always has the same id, in every database. Collisions are refused, not merged; Core 0.3 databases upgrade in place.
"""

import uuid

import pytest
from typedb.driver import TypeDBDriverException

from conftest import FakeClock, T
from worldmodel import PropositionIdCollision, WorldModel, proposition_id, proposition_key
from worldmodel import keys
from worldmodel import typeql as q
from worldmodel.model import READ, WRITE


def setup(wm):
    w = wm.create_world("actual", id="actual")
    for kind, n in (("physical-object", "box"), ("place", "shelf-3"), ("place", "dock"), ("social-object", "cam")):
        wm.add_entity(kind, n, id=n)
    return w


def test_ids_are_deterministic_and_derived_only_from_the_canonical_key():
    k1 = proposition_key("located-at", {"located": "box", "place": "dock"})
    k2 = proposition_key("located-at", {"place": "dock", "located": "box"})
    assert k1 == k2 and proposition_id(k1) == proposition_id(k2)
    assert proposition_id(k1) == proposition_id(k1) and keys.PROPOSITION_ID.match(proposition_id(k1))
    assert proposition_id(k1) != proposition_id(proposition_key("located-at", {"located": "box", "place": "shelf-3"}))
    assert proposition_id(proposition_key("has-quality", {"bearer": "box"}, {"lower": 3.5})) == \
        proposition_id(proposition_key("has-quality", {"bearer": "box"}, {"lower": 3.50000000000001}))


def test_every_stored_proposition_has_its_id_and_restating_content_reuses_it(wm):
    w = setup(wm)
    a = wm.attest(w, "located-at", {"located": "box", "place": "dock"}, start=T("10:00"), until_superseded=True)
    b = wm.attest(w, "located-at", {"located": "box", "place": "dock"}, start=T("11:00"), attester="cam")
    assert a != b
    key = proposition_key("located-at", {"located": "box", "place": "dock"})
    assert wm.proposition_id(key) == proposition_id(key)
    with wm.driver.transaction(wm.database, READ) as tx:
        rows = q.rows(tx, "match $p isa proposition, has wm-id $i, has proposition-key $k;")
        assert len(rows) == 1 + len(q.rows(tx, "match $p isa existence;"))   # one located-at, plus any existence
        assert all(q.opt(r, "i") == proposition_id(q.opt(r, "k")) for r in rows)
        assert not q.rows(tx, "match $p isa proposition; not { $p has wm-id $i; };")


def test_typedb_enforces_one_id_per_proposition_and_no_proposition_without_one(wm):
    setup(wm)
    wm.proposition("located-at", {"located": "box", "place": "dock"})
    with pytest.raises(TypeDBDriverException):                       # immutability: a second id is a second key
        with wm.driver.transaction(wm.database, WRITE) as tx:
            q.run(tx, "match $p isa located-at; insert $p has wm-id == $i;", {"i": "p:" + "0" * 24})
            tx.commit()
    with pytest.raises(TypeDBDriverException):
        with wm.driver.transaction(wm.database, WRITE) as tx:
            q.run(tx, """match $b isa particular, has wm-id "box"; $s isa particular, has wm-id "shelf-3";
                insert located-at (located: $b, place: $s), has proposition-key "manual";""")
            tx.commit()


def test_an_id_collision_is_refused_and_nothing_is_merged(wm, monkeypatch):
    w = setup(wm)
    monkeypatch.setattr(keys, "proposition_id", lambda key: "p:" + "a" * 24)   # every key now derives the same id
    wm.proposition("located-at", {"located": "box", "place": "dock"})
    wm.proposition("located-at", {"located": "box", "place": "dock"})    # same content, same id: reused, no error
    with pytest.raises(PropositionIdCollision) as err:
        wm.attest(w, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"))
    assert err.value.existing == proposition_key("located-at", {"located": "box", "place": "dock"})
    with wm.driver.transaction(wm.database, READ) as tx:
        assert len(q.rows(tx, "match $p isa located-at;")) == 1
        assert not q.rows(tx, "match $a isa attestation;")


def test_proposition_ids_are_reserved_for_propositions(wm):
    with pytest.raises(ValueError, match="reserved"):
        wm.add_entity("physical-object", "sneaky", id="p:" + "b" * 24)
    with pytest.raises(ValueError, match="reserved"):
        wm.create_world("w", id="p:" + "c" * 24)
    wm.add_entity("physical-object", "fine", id="p:not-hex-form")         # only the exact proposition form is reserved


def test_a_core_0_3_database_upgrades_in_place_with_unchanged_answers(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    legacy = WorldModel.create(name, driver=driver, modules=("core",), clock=FakeClock())
    try:
        assert legacy.modules() == {"core": "0.3.0"} and not legacy.has_proposition_ids()
        w = setup(legacy)
        first = legacy.attest(w, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"),
                              until_superseded=True)
        legacy.attest(w, "located-at", {"located": "box", "place": "dock"}, start=T("11:00"), until_superseded=True,
                      supersedes=first)
        legacy.attest(w, "located-at", {"located": "box", "place": "shelf-3"}, start=T("11:30"), attester="cam")
        legacy.create_thing(w, "physical-object", "lid", at=T("09:00"), id="lid")
        h = legacy.create_world("plan", kind="hypothetical", base=w, branch_at=T("12:00"))

        def answers(m):
            return [m.value_at(w, "located-at", "box", t) for t in (T("10:30"), T("11:15"), T("11:45"))] + \
                   [m.value_at(h, "located-at", "box", T("13:00")), m.exists(w, "lid", T("10:00")),
                    m.history(w, "box")]

        before = answers(legacy)
        with driver.transaction(name, READ) as tx:
            n = len(q.rows(tx, "match $p isa proposition;"))
        assert legacy.upgrade_to_a0() == n and legacy.upgrade_to_a0() == 0          # idempotent
        upgraded = WorldModel.open(name, driver=driver, clock=legacy.clock)
        assert upgraded.modules() == {"core": "0.3.0", "core-0.4-a0": "0.4.0-a0"}
        assert answers(upgraded) == before
        with driver.transaction(name, READ) as tx:
            rows = q.rows(tx, "match $p isa proposition, has wm-id $i, has proposition-key $k;")
            assert len(rows) == n and all(q.opt(r, "i") == proposition_id(q.opt(r, "k")) for r in rows)
        upgraded.attest(w, "located-at", {"located": "lid", "place": "dock"}, start=T("12:00"))  # new content gets an id
        key = proposition_key("located-at", {"located": "lid", "place": "dock"})
        assert upgraded.proposition_id(key) == proposition_id(key)
    finally:
        driver.databases.get(name).delete()
