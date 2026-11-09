"""Milestone 1, against a real TypeDB 3.14.1 server: schema, things, relationships, events, worlds, identity."""

import pytest
from typedb.driver import TypeDBDriverException

from conftest import T
from worldmodel import Status
from worldmodel import typeql as q
from worldmodel.model import WRITE


@pytest.fixture
def warehouse(wm):
    w = wm.create_world("warehouse", kind="actual", id="w-actual")
    ids = {
        "robot": wm.add_entity("agent", "robot-1", id="robot-1"),
        "box": wm.add_entity("physical-object", "box-17", alt_names=("parcel 17",), id="box-17"),
        "shelf3": wm.add_entity("place", "shelf-3", id="shelf-3"),
        "dock": wm.add_entity("place", "dock", id="dock"),
        "hall": wm.add_entity("place", "hall-A", id="hall-A"),
        "movement": wm.add_entity("concept", "movement", id="movement"),
    }
    loc = wm.assert_fact(w, "located-at", {"located": "box-17", "place": "shelf-3"}, start=T("10:00"), until_ceased=True)
    wm.assert_fact(w, "part-of", {"part": "shelf-3", "whole": "hall-A"}, until_ceased=True)
    return w, ids, loc


# ---- schema and TypeDB-enforced constraints ----------------------------------------------------------------------
def test_schema_installed_and_introspectable(wm):
    assert wm.modules() == {"core": "0.2.0"}
    assert {"located-at", "part-of", "member-of", "depends-on", "classified-as", "has-state", "same-as",
            "event"} <= wm.claim_types()


def test_typedb_rejects_a_claim_without_a_world(wm):
    wm.add_entity("physical-object", "b", id="b")
    wm.add_entity("place", "p", id="p")
    with pytest.raises(TypeDBDriverException):
        with wm.driver.transaction(wm.database, WRITE) as tx:
            q.run(tx, """match $b isa physical-object, has wm-id "b"; $p isa place, has wm-id "p";
                insert $c isa located-at (located: $b, place: $p), has wm-id "c", has end-basis "unknown",
                has initial-status "accepted";""")
            tx.commit()                                   # @card(1..1) on scope:member is checked at commit


def test_typedb_rejects_a_concept_as_a_located_thing(wm):
    w = wm.create_world("w")
    wm.add_entity("concept", "justice", id="justice")
    wm.add_entity("place", "p", id="p")
    with pytest.raises(TypeDBDriverException):
        wm.assert_fact(w, "located-at", {"located": "justice", "place": "p"}, start=T("10:00"))


def test_typedb_rejects_duplicate_ids_and_bad_values(wm):
    wm.add_entity("agent", "a", id="dup")
    with pytest.raises(TypeDBDriverException):
        wm.add_entity("place", "b", id="dup")
    with pytest.raises(TypeDBDriverException):
        wm.create_world("w", kind="dream")


def test_python_rejects_unknown_claim_types(wm):
    w = wm.create_world("w")
    with pytest.raises(ValueError):
        wm.assert_fact(w, "teleported-to", {"a": "b"})


# ---- things and relationships ----------------------------------------------------------------------------------
def test_find_by_name_or_alt_name_returns_all_matches(wm):
    wm.add_entity("agent", "Sam", id="sam-1")
    wm.add_entity("agent", "Samantha", alt_names=("Sam",), id="sam-2")
    assert wm.find("Sam") == ["sam-1", "sam-2"]              # ambiguous: both, never silently resolved


def test_location_query_and_holds(wm, warehouse):
    w, _, loc = warehouse
    a = wm.value_at(w, "located-at", "box-17", T("10:30"))
    assert (a.status, a.values, a.support) == (Status.ASSERTED, ("shelf-3",), (loc,))
    assert wm.holds(w, "located-at", {"located": "box-17", "place": "shelf-3"}, T("10:30")).holds is True
    neg = wm.holds(w, "located-at", {"located": "box-17", "place": "dock"}, T("10:30"))
    assert (neg.status, neg.holds) == (Status.INFERRED, False)  # functional exclusivity, a declared rule
    assert wm.value_at(w, "located-at", "box-17", T("09:00")).status == Status.UNKNOWN  # before: silent


def test_unknown_end_is_not_invented_continuity(wm):
    w = wm.create_world("w")
    wm.add_entity("physical-object", "rock", id="rock")
    wm.add_entity("place", "crater", id="crater")
    wm.assert_fact(w, "located-at", {"located": "rock", "place": "crater"}, start=T("10:00"))   # end unknown
    assert wm.value_at(w, "located-at", "rock", T("12:00")).status == Status.UNKNOWN


def test_parts_and_dependencies_in_python_and_in_typedb(wm, warehouse):
    w, _, _ = warehouse
    wm.add_entity("physical-object", "bin", id="bin")
    wm.add_entity("physical-object", "conveyor", id="conveyor")
    wm.add_entity("physical-object", "motor", id="motor")
    wm.assert_fact(w, "part-of", {"part": "bin", "whole": "shelf-3"}, until_ceased=True)
    wm.assert_fact(w, "depends-on", {"dependent": "conveyor", "dependee": "motor"}, until_ceased=True)
    assert wm.parts(w, "hall-A", T("10:00")) == ["bin", "shelf-3"]
    assert wm.parts_in_database(w, "hall-A") == ["bin", "shelf-3"]             # same answer from a TypeQL function
    assert wm.dependencies(w, "conveyor", T("10:00")) == ["motor"]


def test_classification_by_concepts_keeps_competing_labels(wm, warehouse):
    w, _, _ = warehouse
    wm.add_entity("concept", "parcel", id="parcel")
    wm.add_entity("concept", "bin", id="bin-concept")
    c1 = wm.assert_fact(w, "classified-as", {"classified": "box-17", "class": "parcel"}, start=T("10:00"),
                        until_ceased=True, status="proposed")
    c2 = wm.assert_fact(w, "classified-as", {"classified": "box-17", "class": "bin-concept"}, start=T("10:00"),
                        until_ceased=True, status="proposed")
    a = wm.holds(w, "classified-as", {"classified": "box-17"}, T("10:30"))
    assert a.status == Status.UNKNOWN and a.alternatives == tuple(sorted((c1, c2)))   # hypotheses, not facts
    wm.review(w, c1, "accepted", decided_by="operator")
    assert wm.holds(w, "classified-as", {"classified": "box-17", "class": "parcel"}, T("10:30")).holds is True


def test_states_are_claims_about_concepts(wm, warehouse):
    w, _, _ = warehouse
    wm.add_entity("concept", "damaged", id="damaged")
    wm.assert_fact(w, "has-state", {"bearer": "box-17", "state": "damaged"}, start=T("10:20"), until_ceased=True)
    facts = wm.facts_about(w, "box-17", T("10:30"))
    assert {f["type"] for f in facts} == {"located-at", "has-state"}


# ---- events and knowledge updates --------------------------------------------------------------------------------
def test_move_updates_location_history_and_events(wm, warehouse):
    w, _, loc = warehouse
    event, (new_loc,) = wm.move(w, "box-17", "dock", T("10:10"), actor="robot-1", kind="movement")
    assert wm.value_at(w, "located-at", "box-17", T("10:05")).values == ("shelf-3",)
    assert wm.value_at(w, "located-at", "box-17", T("10:15")).values == ("dock",)
    assert wm.holds(w, "located-at", {"located": "box-17", "place": "shelf-3"}, T("10:15")).holds is False
    hist = wm.history(w, "box-17", "located-at")
    assert [h["claim"] for h in hist] == [loc, new_loc] and hist[0]["ceased"] == [T("10:10")]
    (ev,) = wm.events(w, participant="robot-1")
    assert ev["event"] == event and ev["kinds"] == ["movement"]
    assert ev["roles"] == {"actor": ["robot-1"], "destination": ["dock"], "origin": ["shelf-3"], "patient": ["box-17"]}


def test_event_order_uses_windows_and_does_not_guess(wm, warehouse):
    w, _, _ = warehouse
    e1, _ = wm.record_event(w, {"actor": "robot-1"}, start=T("10:00"), end=T("10:02"))
    e2, _ = wm.record_event(w, {"actor": "robot-1"}, start=(T("10:01"), T("10:05")))
    e3, _ = wm.record_event(w, {"actor": "robot-1"}, start=T("10:06"))
    evs = {e["event"]: e for e in wm.events(w)}
    assert wm.certainly_before(evs[e1], evs[e3]) and wm.certainly_before(evs[e2], evs[e3])
    assert not wm.certainly_before(evs[e1], evs[e2])                    # windows overlap: order unknown


def test_transaction_time_separates_what_was_known_when(wm, warehouse):
    w, _, _ = warehouse
    before_move = wm.clock.now
    wm.move(w, "box-17", "dock", T("10:10"))
    assert wm.value_at(w, "located-at", "box-17", T("10:15"), as_of=before_move).values == ("shelf-3",)
    assert wm.value_at(w, "located-at", "box-17", T("10:15")).values == ("dock",)
    wm.add_entity("physical-object", "late", id="late")
    t0 = wm.clock.now
    wm.assert_fact(w, "located-at", {"located": "late", "place": "dock"}, start=T("09:00"), until_ceased=True)
    assert wm.value_at(w, "located-at", "late", T("10:00"), as_of=t0).status == Status.NOT_YET_KNOWN


def test_conflicting_accepted_claims_are_disputed_not_resolved(wm, warehouse):
    w, _, loc = warehouse
    other = wm.assert_fact(w, "located-at", {"located": "box-17", "place": "dock"}, start=T("10:00"), until_ceased=True)
    a = wm.value_at(w, "located-at", "box-17", T("10:30"))
    assert a.status == Status.DISPUTED and a.values == ("dock", "shelf-3") and set(a.support) == {loc, other}
    wm.review(w, other, "rejected", decided_by="operator", reason="camera mismatch")
    assert wm.value_at(w, "located-at", "box-17", T("10:30")).values == ("shelf-3",)


# ---- worlds ----------------------------------------------------------------------------------------------------
def test_hypothetical_world_inherits_overrides_and_stays_separate(wm, warehouse):
    w, _, loc = warehouse
    h = wm.create_world("what-if", kind="hypothetical", base=w, branch_at=T("11:00"))
    wm.cease(h, loc, T("11:30"), reason="hypothetically moved")
    wm.assert_fact(h, "located-at", {"located": "box-17", "place": "dock"}, start=T("11:30"), until_ceased=True)
    wm.assert_fact(w, "has-state", {"bearer": "box-17", "state": wm.add_entity("concept", "open", id="open")},
                   start=T("12:00"), until_ceased=True)                  # after the branch: not inherited
    assert wm.value_at(h, "located-at", "box-17", T("10:30")).values == ("shelf-3",)    # inherited
    assert wm.value_at(h, "located-at", "box-17", T("12:00")).values == ("dock",)       # the variant's own
    assert wm.value_at(w, "located-at", "box-17", T("12:00")).values == ("shelf-3",)    # actual untouched
    assert [f["type"] for f in wm.facts_about(h, "box-17", T("12:30"))] == ["located-at"]


def test_variant_claims_take_precedence_over_inherited_ones(wm, warehouse):
    w, _, _ = warehouse
    h = wm.create_world("sim", kind="simulated", base=w, branch_at=T("11:00"))
    wm.assert_fact(h, "located-at", {"located": "box-17", "place": "dock"}, start=T("10:30"), until_ceased=True)
    assert wm.value_at(h, "located-at", "box-17", T("10:45")).values == ("dock",)       # not DISPUTED with base


# ---- identity ------------------------------------------------------------------------------------------------
def test_identity_merges_only_after_acceptance_and_can_be_undone(wm, warehouse):
    w, _, _ = warehouse
    track = wm.add_entity("physical-object", "track-42", id="track-42")
    wm.assert_fact(w, "located-at", {"located": track, "place": "dock"}, start=T("10:12"), until_ceased=True)
    link = wm.assert_fact(w, "same-as", {"same": ["box-17", track]}, status="proposed")
    a = wm.value_at(w, "located-at", "box-17", T("10:30"))
    assert a.values == ("shelf-3",)                                       # proposed link not used
    wm.review(w, link, "accepted", decided_by="operator")
    merged = wm.clock.now
    assert wm.value_at(w, "located-at", "box-17", T("10:30")).status == Status.DISPUTED   # two places, one box
    wm.review(w, link, "rejected", decided_by="operator", reason="different box")
    assert wm.value_at(w, "located-at", "box-17", T("10:30")).values == ("shelf-3",)
    assert wm.value_at(w, "located-at", "box-17", T("10:30"), as_of=merged).status == Status.DISPUTED


def test_proposed_identity_links_are_never_chained(wm, warehouse):
    w, _, _ = warehouse
    for n in ("a", "b", "c"):
        wm.add_entity("physical-object", n, id=n)
    ab = wm.assert_fact(w, "same-as", {"same": ["a", "b"]}, status="proposed")
    wm.assert_fact(w, "same-as", {"same": ["b", "c"]}, status="proposed")
    wm.review(w, ab, "accepted", decided_by="operator")
    ident = wm.identity(w)
    assert ident.members("a") == ["a", "b"] and ident.canonical("c") == "c"
