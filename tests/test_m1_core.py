"""Milestone 1 regression requirements, ported to Core 0.3 (from main: tests/test_core_live.py, 19 tests).

Same names and semantic expectations. Changed mechanisms: claims are attestations of keyed propositions; "proposed"
means attested by another agent and not yet accepted by the system; reviews are perspective acceptances.
"""

import pytest
from typedb.driver import TypeDBDriverException

from conftest import T
from worldmodel import typeql as q
from worldmodel.model import WRITE
from worldmodel.semantics import Status


@pytest.fixture
def warehouse(wm):
    w = wm.create_world("warehouse", kind="actual", id="w-actual")
    for kind, name, i in (("physical-object", "robot-1", "robot-1"), ("physical-object", "box-17", "box-17"),
                          ("place", "shelf-3", "shelf-3"), ("place", "dock", "dock"), ("place", "hall-A", "hall-A"),
                          ("category", "movement", "movement"), ("social-object", "detector", "detector"),
                          ("social-object", "matcher", "matcher")):
        wm.add_entity(kind, name, alt_names=("parcel 17",) if i == "box-17" else (), id=i)
    loc = wm.attest(w, "located-at", {"located": "box-17", "place": "shelf-3"}, start=T("10:00"), until_superseded=True)
    wm.attest(w, "part-of", {"part": "shelf-3", "whole": "hall-A"}, until_superseded=True)
    return w, loc


def test_schema_installed_and_introspectable(wm):
    assert wm.modules() == {"core": "0.3.0", "core-0.4-a0": "0.4.0-a0"}      # Core 0.3 plus the additive A0 module (LABS-1.002)
    assert {"located-at", "part-of", "member-of", "depends-on", "classified-as", "has-quality", "same-as",
            "existence"} <= wm.proposition_types()


def test_typedb_rejects_a_claim_without_a_world(wm):
    wm.add_entity("physical-object", "b", id="b")
    wm.add_entity("place", "p", id="p")
    key = wm.proposition("located-at", {"located": "b", "place": "p"})
    with pytest.raises(TypeDBDriverException):
        with wm.driver.transaction(wm.database, WRITE) as tx:
            q.run(tx, """match $c isa located-at, has proposition-key == $k; $s isa social-object, has wm-id "system";
                insert attestation (attester: $s, content: $c), has wm-id "c", has stance "asserts",
                has polarity true, has basis "testimony", has end-basis "unknown";""", {"k": key})
            tx.commit()                                    # @card(1..1) on the context role, checked at commit


def test_typedb_rejects_a_concept_as_a_located_thing(wm):
    w = wm.create_world("w")
    wm.add_entity("category", "justice", id="justice")
    wm.add_entity("place", "p", id="p")
    with pytest.raises(TypeDBDriverException):
        wm.attest(w, "located-at", {"located": "justice", "place": "p"}, start=T("10:00"))


def test_typedb_rejects_duplicate_ids_and_bad_values(wm):
    wm.add_entity("physical-object", "a", id="dup")
    with pytest.raises(TypeDBDriverException):
        wm.add_entity("place", "b", id="dup")
    with pytest.raises(TypeDBDriverException):
        wm.create_world("w", kind="dream")


def test_python_rejects_unknown_claim_types(wm):
    w = wm.create_world("w")
    with pytest.raises(ValueError):
        wm.attest(w, "teleported-to", {"a": "b"})


def test_find_by_name_or_alt_name_returns_all_matches(wm):
    wm.add_entity("physical-object", "Sam", id="sam-1")
    wm.add_entity("physical-object", "Samantha", alt_names=("Sam",), id="sam-2")
    assert wm.find("Sam") == ["sam-1", "sam-2"]


def test_location_query_and_holds(wm, warehouse):
    w, loc = warehouse
    a = wm.value_at(w, "located-at", "box-17", T("10:30"))
    assert (a.status, a.values, a.support) == (Status.ASSERTED, ("shelf-3",), (loc,))
    assert wm.holds(w, "located-at", {"located": "box-17", "place": "shelf-3"}, T("10:30")).holds is True
    neg = wm.holds(w, "located-at", {"located": "box-17", "place": "dock"}, T("10:30"))
    assert (neg.status, neg.holds) == (Status.INFERRED, False)
    assert wm.value_at(w, "located-at", "box-17", T("09:00")).status == Status.UNKNOWN


def test_unknown_end_is_not_invented_continuity(wm):
    w = wm.create_world("w")
    wm.add_entity("physical-object", "rock", id="rock")
    wm.add_entity("place", "crater", id="crater")
    wm.attest(w, "located-at", {"located": "rock", "place": "crater"}, start=T("10:00"))
    assert wm.value_at(w, "located-at", "rock", T("12:00")).status == Status.UNKNOWN


def test_parts_and_dependencies_in_python_and_in_typedb(wm, warehouse):
    w, _ = warehouse
    for n in ("bin", "conveyor", "motor"):
        wm.add_entity("physical-object", n, id=n)
    wm.attest(w, "part-of", {"part": "bin", "whole": "shelf-3"}, until_superseded=True)
    wm.attest(w, "depends-on", {"dependent": "conveyor", "dependee": "motor"}, until_superseded=True)
    assert wm.parts(w, "hall-A", T("10:00")) == ["bin", "shelf-3"]
    assert wm.parts_in_database(w, "hall-A") == ["bin", "shelf-3"]
    assert wm.dependencies(w, "conveyor", T("10:00")) == ["motor"]


def test_classification_by_concepts_keeps_competing_labels(wm, warehouse):
    w, _ = warehouse
    wm.add_entity("category", "parcel", id="parcel")
    wm.add_entity("category", "bin", id="bin-concept")
    c1 = wm.attest(w, "classified-as", {"classified": "box-17", "class": "parcel"}, start=T("10:00"),
                   until_superseded=True, attester="detector")
    c2 = wm.attest(w, "classified-as", {"classified": "box-17", "class": "bin-concept"}, start=T("10:00"),
                   until_superseded=True, attester="detector")
    a = wm.holds(w, "classified-as", {"classified": "box-17"}, T("10:30"))
    assert a.status == Status.UNKNOWN and a.alternatives == tuple(sorted((c1, c2)))
    wm.accept(c1)
    assert wm.holds(w, "classified-as", {"classified": "box-17", "class": "parcel"}, T("10:30")).holds is True


def test_states_are_claims_about_concepts(wm, warehouse):
    w, _ = warehouse
    wm.add_entity("category", "damaged", id="damaged")
    wm.add_entity("quality-kind", "condition", id="condition")
    wm.attest(w, "has-quality", {"bearer": "box-17", "quality": "condition", "value": "damaged"}, start=T("10:20"),
              until_superseded=True)
    assert {f["type"] for f in wm.facts_about(w, "box-17", T("10:30"))} == {"located-at", "has-quality"}


def test_move_updates_location_history_and_events(wm, warehouse):
    w, loc = warehouse
    event, (new_loc,) = wm.move(w, "box-17", "dock", T("10:10"), actor="robot-1", kind="movement")
    assert wm.value_at(w, "located-at", "box-17", T("10:05")).values == ("shelf-3",)
    assert wm.value_at(w, "located-at", "box-17", T("10:15")).values == ("dock",)
    assert wm.holds(w, "located-at", {"located": "box-17", "place": "shelf-3"}, T("10:15")).holds is False
    hist = wm.history(w, "box-17", "located-at")
    assert [h["attestation"] for h in hist][0] == loc and hist[0]["superseded"]
    assert hist[1]["end"].earliest == T("10:10") and hist[-1]["attestation"] == new_loc
    (ev,) = wm.events(w, participant="robot-1")
    assert ev["event"] == event and ev["kinds"] == ["movement"]
    assert ev["roles"] == {"actor": ["robot-1"], "destination": ["dock"], "origin": ["shelf-3"], "patient": ["box-17"]}


def test_event_order_uses_windows_and_does_not_guess(wm, warehouse):
    w, _ = warehouse
    e1, _ = wm.record_event(w, {"actor": "robot-1"}, start=T("10:00"), end=T("10:02"))
    e2, _ = wm.record_event(w, {"actor": "robot-1"}, start=(T("10:01"), T("10:05")))
    e3, _ = wm.record_event(w, {"actor": "robot-1"}, start=T("10:06"))
    evs = {e["event"]: e for e in wm.events(w)}
    assert wm.certainly_before(evs[e1], evs[e3]) and wm.certainly_before(evs[e2], evs[e3])
    assert not wm.certainly_before(evs[e1], evs[e2])


def test_transaction_time_separates_what_was_known_when(wm, warehouse):
    w, _ = warehouse
    before_move = wm.clock.now
    wm.move(w, "box-17", "dock", T("10:10"))
    assert wm.value_at(w, "located-at", "box-17", T("10:15"), as_of=before_move).values == ("shelf-3",)
    assert wm.value_at(w, "located-at", "box-17", T("10:15")).values == ("dock",)
    wm.add_entity("physical-object", "late", id="late")
    t0 = wm.clock.now
    wm.attest(w, "located-at", {"located": "late", "place": "dock"}, start=T("09:00"), until_superseded=True)
    assert wm.value_at(w, "located-at", "late", T("10:00"), as_of=t0).status == Status.NOT_YET_KNOWN


def test_conflicting_accepted_claims_are_disputed_not_resolved(wm, warehouse):
    w, loc = warehouse
    other = wm.attest(w, "located-at", {"located": "box-17", "place": "dock"}, start=T("10:00"), until_superseded=True)
    a = wm.value_at(w, "located-at", "box-17", T("10:30"))
    assert a.status == Status.DISPUTED and a.values == ("dock", "shelf-3") and set(a.support) == {loc, other}
    wm.accept(other, "rejected", reason="camera mismatch")
    assert wm.value_at(w, "located-at", "box-17", T("10:30")).values == ("shelf-3",)


def test_hypothetical_world_inherits_overrides_and_stays_separate(wm, warehouse):
    w, loc = warehouse
    h = wm.create_world("what-if", kind="hypothetical", base=w, branch_at=T("11:00"))
    wm.end(h, loc, T("11:30"), reason="hypothetically moved")
    wm.attest(h, "located-at", {"located": "box-17", "place": "dock"}, start=T("11:30"), until_superseded=True)
    wm.add_entity("category", "open", id="open")
    wm.add_entity("quality-kind", "lid", id="lid")
    wm.attest(w, "has-quality", {"bearer": "box-17", "quality": "lid", "value": "open"}, start=T("12:00"),
              until_superseded=True)                                          # after the branch: not inherited
    assert wm.value_at(h, "located-at", "box-17", T("10:30")).values == ("shelf-3",)
    assert wm.value_at(h, "located-at", "box-17", T("12:00")).values == ("dock",)
    assert wm.value_at(w, "located-at", "box-17", T("12:00")).values == ("shelf-3",)
    assert [f["type"] for f in wm.facts_about(h, "box-17", T("12:30"))] == ["located-at"]


def test_variant_claims_take_precedence_over_inherited_ones(wm, warehouse):
    w, _ = warehouse
    h = wm.create_world("sim", kind="simulated", base=w, branch_at=T("11:00"))
    wm.attest(h, "located-at", {"located": "box-17", "place": "dock"}, start=T("10:30"), until_superseded=True)
    a = wm.value_at(h, "located-at", "box-17", T("10:45"))
    assert (a.status, a.values) == (Status.STIPULATED, ("dock",))


def test_identity_merges_only_after_acceptance_and_can_be_undone(wm, warehouse):
    w, _ = warehouse
    wm.add_entity("physical-object", "track-42", id="track-42")
    wm.attest(w, "located-at", {"located": "track-42", "place": "dock"}, start=T("10:12"), until_superseded=True)
    link = wm.attest(w, "same-as", {"same": ["box-17", "track-42"]}, until_superseded=True, attester="matcher")
    assert wm.value_at(w, "located-at", "box-17", T("10:30")).values == ("shelf-3",)
    wm.accept(link)
    merged = wm.clock.now
    assert wm.value_at(w, "located-at", "box-17", T("10:30")).status == Status.DISPUTED
    wm.accept(link, "rejected", reason="different box")
    assert wm.value_at(w, "located-at", "box-17", T("10:30")).values == ("shelf-3",)
    assert wm.value_at(w, "located-at", "box-17", T("10:30"), as_of=merged).status == Status.DISPUTED


def test_proposed_identity_links_are_never_chained(wm, warehouse):
    w, _ = warehouse
    for n in ("a", "b", "c"):
        wm.add_entity("physical-object", n, id=n)
    ab = wm.attest(w, "same-as", {"same": ["a", "b"]}, until_superseded=True, attester="matcher")
    wm.attest(w, "same-as", {"same": ["b", "c"]}, until_superseded=True, attester="matcher")
    wm.accept(ab)
    ident = wm.identity(w)
    assert ident.members("a") == ["a", "b"] and ident.canonical("c") == "c"
