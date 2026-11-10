"""Core 0.4 Stage A0.3 (LABS-1.002): functional-slot metadata as data in TypeDB, with composite keys.

A slot says that one value holds at a time for each combination of key-role players. located-at keeps its Core 0.3
slot (located -> place), now declared as data; a seat assignment has a composite slot (venue, seat -> occupant).
Temporal, perspective and dispute semantics are unchanged: only which attestations compete for a slot is generalised.
"""

import uuid
from pathlib import Path

import pytest

from conftest import FakeClock, T
from worldmodel import WorldModel
from worldmodel import typeql as q
from worldmodel.model import READ
from worldmodel.semantics import Status

PROFILE = str(Path(__file__).resolve().parent / "fixtures" / "profile-a0-slots.tql")
SEAT = "seat-assignment"


@pytest.fixture
def hall(wm):
    wm.install_module("test-profile-a0-slots", files=[PROFILE], version="0")
    wm.declare_slot(SEAT, ["venue", "seat"], "occupant")
    w = wm.create_world("actual", id="actual")
    for kind, n in (("place", "hall"), ("place", "annex"), ("seat", "A1"), ("seat", "A2"), ("guest", "ann"),
                    ("guest", "bo"), ("physical-object", "boat"), ("place", "pier"), ("place", "bay")):
        wm.add_entity(kind, n, id=n)
    return w


def sit(wm, w, venue, seat, who, start, **kw):
    return wm.attest(w, SEAT, {"venue": venue, "seat": seat, "occupant": who}, start=start, until_superseded=True, **kw)


def test_the_core_slot_is_declared_as_data_in_typedb(wm):
    assert wm.slots() == {"located-at": [(("located",), "place")]}
    with wm.driver.transaction(wm.database, READ) as tx:
        rows = q.rows(tx, "match $s isa functional-slot, has slot-predicate $p, has slot-role $k, has value-role $v;")
    assert [(q.opt(r, "p"), q.opt(r, "k"), q.opt(r, "v")) for r in rows] == [("located-at", "located", "place")]


def test_declarations_are_validated(wm, hall):
    assert wm.slots()[SEAT] == [(("seat", "venue"), "occupant")]
    wm.declare_slot(SEAT, ["seat", "venue"], "occupant")                       # the same declaration again: no-op
    wm.declare_slot("vip-assignment", ["venue", "seat"], "occupant")           # already inherited: no-op
    assert "vip-assignment" not in wm.slots()
    for bad in (("vip-assignment", ["venue", "nope"], "occupant"),             # unknown role
                ("vip-assignment", ["venue"], "venue"),                        # value role inside the key
                ("seat", ["venue"], "occupant")):                              # not a proposition type
        with pytest.raises(ValueError):
            wm.declare_slot(*bad)


def test_a_composite_slot_holds_one_value_per_key_combination(wm, hall):
    sit(wm, hall, "hall", "A1", "ann", T("10:00"))
    sit(wm, hall, "hall", "A2", "bo", T("10:00"))
    sit(wm, hall, "annex", "A1", "bo", T("10:00"))          # same seat label, other venue: another slot
    a = wm.value_of(hall, SEAT, {"venue": "hall", "seat": "A1"}, T("10:30"))
    assert (a.status, a.values) == (Status.ASSERTED, ("ann",))
    assert wm.value_of(hall, SEAT, {"venue": "annex", "seat": "A1"}, T("10:30")).values == ("bo",)
    sit(wm, hall, "hall", "A1", "bo", T("10:00"))            # a second occupant for the same seat at the same time
    a = wm.value_of(hall, SEAT, {"venue": "hall", "seat": "A1"}, T("10:30"))
    assert (a.status, a.values) == (Status.DISPUTED, ("ann", "bo"))
    assert wm.value_of(hall, SEAT, {"venue": "hall", "seat": "A2"}, T("10:30")).status == Status.ASSERTED
    assert wm.value_of(hall, SEAT, {"venue": "hall", "seat": "A2"}, T("09:30")).status == Status.UNKNOWN


def test_composite_slots_need_every_key_role(wm, hall):
    with pytest.raises(ValueError, match="one-role functional constraints"):
        wm.value_at(hall, SEAT, "A1", T("10:30"))
    with pytest.raises(ValueError, match="key roles of one functional constraint"):
        wm.value_of(hall, SEAT, {"seat": "A1"}, T("10:30"))


def test_a_variant_overrides_an_inherited_composite_slot_and_holds_infers_the_rest(wm, hall):
    sit(wm, hall, "hall", "A1", "ann", T("10:00"))
    h = wm.create_world("plan", kind="hypothetical", base=hall, branch_at=T("12:00"))
    sit(wm, h, "hall", "A1", "bo", T("12:30"))
    a = wm.value_of(h, SEAT, {"venue": "hall", "seat": "A1"}, T("13:00"))
    assert (a.status, a.values) == (Status.STIPULATED, ("bo",))
    ann = wm.holds(h, SEAT, {"venue": "hall", "seat": "A1", "occupant": "ann"}, T("13:00"))
    assert (ann.status, ann.holds) == (Status.INFERRED, False)
    assert wm.holds(hall, SEAT, {"venue": "hall", "seat": "A1", "occupant": "ann"}, T("13:00")).holds is True
    assert wm.value_of(hall, SEAT, {"venue": "hall", "seat": "A1"}, T("13:00")).values == ("ann",)


def test_an_occupant_may_hold_several_slots(wm, hall):
    """The slot is (venue, seat): nothing says a guest has one seat, so two seats for one guest are not a dispute."""
    sit(wm, hall, "hall", "A1", "ann", T("10:00"))
    sit(wm, hall, "hall", "A2", "ann", T("10:00"))
    a = wm.value_at(hall, SEAT, "ann", T("10:30"), key_role="occupant", value_role="seat")
    assert (a.status, a.values) == (Status.ASSERTED, ("A1", "A2"))


def test_subtypes_inherit_every_constraint(wm, hall):
    sit(wm, hall, "hall", "A1", "ann", T("10:00"))
    wm.attest(hall, "vip-assignment", {"venue": "hall", "seat": "A1", "occupant": "bo"}, start=T("10:00"),
              until_superseded=True)
    a = wm.value_of(hall, SEAT, {"venue": "hall", "seat": "A1"}, T("10:30"))
    assert (a.status, a.values) == (Status.DISPUTED, ("ann", "bo"))          # inherited: they compete for one seat


def test_a_subtype_declaration_adds_a_constraint_and_keeps_the_inherited_one(wm, hall):
    """U-5 (LABS-1.003): berthed-at adds "one boat per berth" and keeps located-at's "one place per thing"."""
    wm.add_entity("physical-object", "skiff", id="skiff")
    wm.declare_slot("berthed-at", ["place"], "located")
    assert wm._constraints("berthed-at") == [("located-at", ("located",), "place"), ("berthed-at", ("place",), "located")]
    wm.attest(hall, "berthed-at", {"located": "boat", "place": "pier"}, start=T("10:00"), until_superseded=True)
    wm.attest(hall, "located-at", {"located": "boat", "place": "bay"}, start=T("10:00"), until_superseded=True)
    loc = wm.value_at(hall, "located-at", "boat", T("10:30"))
    assert (loc.status, loc.values) == (Status.DISPUTED, ("bay", "pier"))     # the inherited constraint still holds
    wm.attest(hall, "berthed-at", {"located": "skiff", "place": "pier"}, start=T("10:00"), until_superseded=True)
    berth = wm.value_at(hall, "berthed-at", "pier", T("10:30"), key_role="place", value_role="located")
    assert (berth.status, berth.values) == (Status.DISPUTED, ("boat", "skiff"))  # the added constraint
    with pytest.raises(ValueError, match="one-role functional constraints"):
        wm.value_at(hall, "berthed-at", "boat", T("10:30"))                 # two apply: the question must say which


def test_an_added_constraint_does_not_reach_the_parent_type(wm, hall):
    wm.add_entity("physical-object", "skiff", id="skiff")
    wm.declare_slot("berthed-at", ["place"], "located")
    wm.attest(hall, "located-at", {"located": "boat", "place": "pier"}, start=T("10:00"), until_superseded=True)
    wm.attest(hall, "located-at", {"located": "skiff", "place": "pier"}, start=T("10:00"), until_superseded=True)
    at_pier = wm.value_at(hall, "located-at", "pier", T("10:30"), key_role="place", value_role="located")
    assert (at_pier.status, at_pier.values) == (Status.ASSERTED, ("boat", "skiff"))   # plain located-at: compatible


def test_an_inherited_constraint_overrides_across_worlds_for_subtype_facts(wm, hall):
    wm.declare_slot("berthed-at", ["place"], "located")
    wm.attest(hall, "berthed-at", {"located": "boat", "place": "pier"}, start=T("10:00"), until_superseded=True)
    h = wm.create_world("plan", kind="hypothetical", base=hall, branch_at=T("12:00"))
    wm.attest(h, "located-at", {"located": "boat", "place": "bay"}, start=T("12:30"), until_superseded=True)
    loc = wm.value_at(h, "located-at", "boat", T("13:00"))
    assert (loc.status, loc.values) == (Status.STIPULATED, ("bay",))       # the variant's place wins the boat's slot
    berthed = wm.holds(h, "berthed-at", {"located": "boat", "place": "pier"}, T("13:00"))
    assert (berthed.status, berthed.holds) == (Status.INFERRED, False)
    assert wm.value_at(hall, "located-at", "boat", T("13:00")).values == ("pier",)


def test_a_type_may_declare_several_constraints(wm, hall):
    wm.declare_slot(SEAT, ["venue", "occupant"], "seat")                    # one seat per guest per venue, too
    assert wm.slots()[SEAT] == [(("occupant", "venue"), "seat"), (("seat", "venue"), "occupant")]
    sit(wm, hall, "hall", "A1", "ann", T("10:00"))
    sit(wm, hall, "hall", "A2", "ann", T("10:00"))
    a = wm.value_of(hall, SEAT, {"venue": "hall", "occupant": "ann"}, T("10:30"))
    assert (a.status, a.values) == (Status.DISPUTED, ("A1", "A2"))
    assert wm.value_of(hall, SEAT, {"venue": "hall", "seat": "A1"}, T("10:30")).values == ("ann",)


def test_located_at_behaves_as_in_core_0_3(wm, hall):
    wm.attest(hall, "located-at", {"located": "boat", "place": "pier"}, start=T("10:00"), until_superseded=True)
    wm.attest(hall, "located-at", {"located": "boat", "place": "bay"}, start=T("10:00"), until_superseded=True)
    assert wm.value_at(hall, "located-at", "boat", T("10:30")).status == Status.DISPUTED
    held = wm.holds(hall, "located-at", {"located": "boat", "place": "pier"}, T("10:30"))
    assert (held.status, held.holds) == (Status.DISPUTED, None)     # the same functional conflict (F-4, LABS-1.005)


def test_selective_and_full_load_agree_on_composite_slots(wm, hall):
    sit(wm, hall, "hall", "A1", "ann", T("10:00"))
    sit(wm, hall, "hall", "A1", "bo", T("11:00"), attester=SEAT_CAM(wm))
    wm.attest(hall, "vip-assignment", {"venue": "hall", "seat": "A2", "occupant": "bo"}, start=T("10:00"),
              until_superseded=True)
    h = wm.create_world("plan", kind="hypothetical", base=hall, branch_at=T("12:00"))
    sit(wm, h, "hall", "A2", "ann", T("12:30"))

    def answers():
        return [wm.value_of(w, SEAT, {"venue": "hall", "seat": s}, t) for w in (hall, h) for s in ("A1", "A2")
                for t in (T("10:30"), T("11:30"), T("13:00"))] + \
               [wm.holds(h, SEAT, {"venue": "hall", "seat": "A2", "occupant": "bo"}, T("13:00")),
                wm.value_at(hall, SEAT, "bo", T("10:30"), key_role="occupant", value_role="seat")]

    wm.selective = True
    selective = answers()
    wm.selective = False
    assert answers() == selective


def SEAT_CAM(wm):
    wm.add_entity("social-object", "usher", id="usher")
    return "usher"


def test_a_core_0_3_upgrade_declares_the_core_slot(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    legacy = WorldModel.create(name, driver=driver, modules=("core",), clock=FakeClock())
    try:
        assert legacy.slots() == {"located-at": [(("located",), "place")]}     # the Core 0.3 constant
        with pytest.raises(ValueError, match="core-0.4-a0"):
            legacy.declare_slot("located-at", ["located"], "place")
        legacy.upgrade_to_a0()
        with driver.transaction(name, READ) as tx:
            assert len(q.rows(tx, "match $s isa functional-slot;")) == 1
        assert WorldModel.open(name, driver=driver).slots() == {"located-at": [(("located",), "place")]}
    finally:
        driver.databases.get(name).delete()
