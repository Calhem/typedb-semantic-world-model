"""Clarification A (v0.2 §3.2): occurrences vs event descriptions. No premature identification; descriptions stay
traceable; identity judgements can be revised."""

import pytest

from conftest import T


@pytest.fixture
def scene(wm):
    w = wm.create_world("actual", id="actual")
    for kind, n in (("physical-object", "bob"), ("physical-object", "carol"), ("physical-object", "box"),
                    ("physical-object", "A"), ("physical-object", "B"), ("social-object", "matcher"),
                    ("occurrence", "o-7")):
        wm.add_entity(kind, n, id=n)
    e1 = wm.describe_event({"actor": "bob", "patient": "box"}, id="e1")
    wm.attest(w, event=e1, start=(T("10:04"), T("10:06")), attester="A")
    e2 = wm.describe_event({"actor": "carol", "patient": "box"}, id="e2")
    wm.attest(w, event=e2, start=T("10:06"), attester="B")
    links = [wm.attest(w, "describes", {"description": e, "occurrence": "o-7"}, until_superseded=True,
                       attester="matcher") for e in (e1, e2)]
    return w, links


def test_descriptions_are_not_identified_before_acceptance(wm, scene):
    w, _ = scene
    assert wm.descriptions(w, "o-7") == []                              # proposed by the matcher only
    assert {e["event"] for e in wm.events(w, participant="box", perspective="A")} == {"e1"}


def test_accepted_links_give_a_merged_view_with_traceable_conflict(wm, scene):
    w, links = scene
    for link in links:
        wm.accept(link)
    view = wm.occurrence(w, "o-7")
    assert view["descriptions"] == ["e1", "e2"]
    assert view["participants"]["actor"] == {"bob": [("e1", "A")], "carol": [("e2", "B")]}   # both, each traceable
    assert wm.content("e1")["roles"]["actor"] == ["bob"]                # descriptions never edited


def test_identity_judgement_can_be_revised_and_history_kept(wm, scene):
    w, links = scene
    for link in links:
        wm.accept(link)
    both = wm.clock.now
    wm.accept(links[1], "rejected", reason="different pickup")
    assert wm.descriptions(w, "o-7") == ["e1"]
    assert wm.descriptions(w, "o-7", as_of=both) == ["e1", "e2"]
