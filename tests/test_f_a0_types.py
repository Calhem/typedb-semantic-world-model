"""Core 0.4 Stage A0.2 (LABS-1.002): polymorphic type and role resolution.

Profile subtypes and specialised roles are read from the schema (`sub!` queries), never assumed from exact labels.
A record keeps its concrete type (`ctype`, e.g. docked-at) and its stored role names (`concrete_roles`) while answers
use its core type (`kind`) and core role names, so a profile fact answers a core question and stays itself.
"""

from pathlib import Path

import pytest

from conftest import T
from worldmodel.model import CORE_LABELS
from worldmodel.semantics import Status

PROFILE = str(Path(__file__).resolve().parent / "fixtures" / "profile-a0.tql")


@pytest.fixture
def world(wm):
    wm.install_module("test-profile-a0", files=[PROFILE], version="0")
    w = wm.create_world("actual", id="actual")
    for kind, n in (("person", "alice"), ("organisation", "acme"), ("physical-object", "box"), ("place", "shelf-3"),
                    ("dock", "dock-2"), ("social-object", "cam")):
        wm.add_entity(kind, n, id=n)
    return w


def test_the_lattice_is_read_from_the_schema(wm, world):
    assert wm.ancestors("docked-at") == ["docked-at", "located-at", "proposition"]
    assert wm.ancestors("person") == ["person", "physical-object", "particular"]
    assert (wm.core_type("dock"), wm.core_type("pickup"), wm.core_type("employment")) == ("place", "event", "proposition")
    assert (wm.core_role("pickup:picker"), wm.core_role("pickup:picked"), wm.core_role("event:actor")) == \
        ("actor", "patient", "actor")
    assert wm.core_role("employment:employer") == "employer"            # a profile's own role keeps its name
    assert wm.is_a("docked-at", "located-at") and not wm.is_a("located-at", "docked-at")
    assert not {"person", "pickup", "docked-at", "employment", "dock"} & CORE_LABELS
    assert {"docked-at", "employment"} <= wm.proposition_types()


def test_a_subtype_fact_answers_the_core_question_and_keeps_its_type(wm, world):
    wm.attest(world, "docked-at", {"located": "box", "place": "dock-2"}, start=T("10:00"), until_superseded=True)
    for asked in ("located-at", "docked-at"):
        a = wm.value_at(world, asked, "box", T("10:30"))
        assert (a.status, a.values) == (Status.ASSERTED, ("dock-2",)), asked
    assert wm.holds(world, "located-at", {"located": "box", "place": "dock-2"}, T("10:30")).holds is True
    (fact,) = wm.facts_about(world, "box", T("10:30"))
    assert fact["type"] == "docked-at"                                  # the concrete subtype is not lost
    assert wm.exists(world, "box", T("10:30")).status == Status.INFERRED     # participation implies existence
    assert wm.history(world, "box", type="located-at")[0]["type"] == "docked-at"


def test_a_subtype_shares_its_parents_functional_slot(wm, world):
    """U-5 default (inherit): docked-at is a located-at, so one thing has one location across both."""
    wm.attest(world, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_superseded=True)
    wm.attest(world, "docked-at", {"located": "box", "place": "dock-2"}, start=T("10:00"), until_superseded=True)
    a = wm.value_at(world, "located-at", "box", T("10:30"))
    assert (a.status, a.values) == (Status.DISPUTED, ("dock-2", "shelf-3"))


def test_a_subtype_fact_in_a_variant_overrides_the_inherited_slot(wm, world):
    wm.attest(world, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_superseded=True)
    h = wm.create_world("plan", kind="hypothetical", base=world, branch_at=T("12:00"))
    wm.attest(h, "docked-at", {"located": "box", "place": "dock-2"}, start=T("12:30"), until_superseded=True)
    a = wm.value_at(h, "located-at", "box", T("13:00"))
    assert (a.status, a.values) == (Status.STIPULATED, ("dock-2",))
    assert wm.holds(h, "docked-at", {"located": "box", "place": "shelf-3"}, T("13:00")).holds is False
    assert wm.holds(h, "located-at", {"located": "box", "place": "shelf-3"}, T("13:00")).holds is False
    assert wm.value_at(world, "located-at", "box", T("13:00")).values == ("shelf-3",)


def test_specialised_event_roles_answer_as_core_roles(wm, world):
    eid, _ = wm.record_event(world, {"picker": "alice", "picked": "box"}, start=T("10:00"), type="pickup",
                             id="pick-1")
    (ev,) = wm.events(world, participant="alice")
    assert (ev["event"], ev["type"], ev["roles"]) == ("pick-1", "pickup", {"actor": ["alice"], "patient": ["box"]})
    assert ev["record"].kind == "event" and ev["record"].concrete_roles == {"picker": ["alice"], "picked": ["box"]}
    assert [e["event"] for e in wm.events(world, participant="box")] == ["pick-1"]
    c = wm.content("pick-1")
    assert (c["type"], c["core_type"], c["roles"], c["core_roles"]) == \
        ("pickup", "event", {"picked": ["box"], "picker": ["alice"]}, {"actor": ["alice"], "patient": ["box"]})
    with pytest.raises(ValueError, match="not an event type"):
        wm.describe_event({"located": "box"}, type="docked-at")


def test_a_profile_predicate_with_its_own_roles(wm, world):
    wm.attest(world, "employment", {"employer": "acme", "employee": "alice"}, start=T("09:00"), until_superseded=True)
    assert wm.holds(world, "employment", {"employer": "acme", "employee": "alice"}, T("10:00")).holds is True
    a = wm.value_at(world, "employment", "alice", T("10:00"), key_role="employee", value_role="employer")
    assert (a.status, a.values) == (Status.ASSERTED, ("acme",))
    assert wm.value_at(world, "employment", "alice", T("08:00"), key_role="employee", value_role="employer").status \
        == Status.UNKNOWN


def test_destroying_a_thing_ends_subtype_facts_with_their_own_roles(wm, world):
    wm.attest(world, "docked-at", {"located": "box", "place": "dock-2"}, start=T("10:00"), until_superseded=True)
    wm.attest(world, "docked-at", {"located": "box", "place": "dock-2"}, start=T("10:00"), until_superseded=True,
              attester="cam")
    wm.accept(wm.history(world, "box", type="docked-at")[-1]["attestation"], "accepted")
    ended = wm.destroy(world, "box", T("11:00"))
    assert len(ended) == 2
    after = wm.value_at(world, "docked-at", "box", T("11:30"))
    assert after.status == Status.DISPUTED          # the system's denial (re-attested with docked-at's roles) vs cam's
    assert wm.value_at(world, "docked-at", "box", T("10:30")).values == ("dock-2",)


def test_a_person_subtype_attests_and_holds_a_perspective(wm, world):
    a = wm.attest(world, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), attester="alice",
                  until_superseded=True)
    assert wm.value_at(world, "located-at", "box", T("10:30"), perspective="alice").support == (a,)
    assert wm.value_at(world, "located-at", "box", T("10:30")).status == Status.UNKNOWN      # unreviewed by system


def test_selective_and_full_load_agree_on_profile_questions(wm, world):
    wm.attest(world, "located-at", {"located": "box", "place": "shelf-3"}, start=T("09:00"), until_superseded=True)
    wm.move(world, "box", "dock-2", T("10:00"), actor="alice")
    wm.attest(world, "docked-at", {"located": "box", "place": "dock-2"}, start=T("10:05"), until_superseded=True)
    wm.record_event(world, {"picker": "alice", "picked": "box"}, start=T("10:30"), type="pickup", id="pick-2")
    wm.attest(world, "employment", {"employer": "acme", "employee": "alice"}, start=T("09:00"), until_superseded=True)

    def answers():
        out = [wm.value_at(world, ty, "box", t) for ty in ("located-at", "docked-at")
               for t in (T("09:30"), T("10:02"), T("10:30"))]
        out += [wm.holds(world, "docked-at", {"located": "box", "place": "shelf-3"}, T("10:30")),
                wm.exists(world, "alice", T("10:30")), wm.facts_about(world, "box", T("10:30")),
                wm.value_at(world, "employment", "alice", T("10:00"), key_role="employee", value_role="employer"),
                [(e["event"], e["type"], e["roles"]) for e in wm.events(world, participant="alice")]]
        return out

    wm.selective = True
    selective = answers()
    wm.selective = False
    assert answers() == selective
