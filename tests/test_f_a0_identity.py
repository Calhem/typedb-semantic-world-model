"""LABS-1.004: identity equivalence of answer values on the selective path (defect F-5).

A value player (a place) with an accepted same-as link to another place must compare as one value on both query
paths. Identity stays perspective-, knowledge-time- and world-dependent: nothing is merged in storage.
Every question is asked on both paths and the whole answers (status, values, support, evidence) must be equal.
"""

import pytest

from conftest import T
from worldmodel import WorldModel
from worldmodel.semantics import Status


@pytest.fixture
def w(wm):
    world = wm.create_world("actual", id="actual")
    for kind, n in (("physical-object", "box"), ("place", "shelf"), ("place", "cell-12"), ("place", "bay-3"),
                    ("place", "x-ref"), ("place", "dock"), ("social-object", "matcher")):
        wm.add_entity(kind, n, id=n)
    for p in ("shelf", "cell-12"):
        wm.attest(world, "located-at", {"located": "box", "place": p}, start=T("10:00"), until_superseded=True)
    return world


def both(wm, ask):
    """Ask on the selective and the full-load path; the answers must be identical. Returns the answer."""
    full = WorldModel.open(wm.database, driver=wm.driver, clock=wm.clock)
    full.selective = False
    wm.selective = True
    a, b = ask(wm), ask(full)
    assert a == b
    return a


def where(wm, world, t=T("10:30"), **kw):
    return both(wm, lambda m: m.value_at(world, "located-at", "box", t, **kw))


def link(wm, world, x, y, **kw):
    return wm.attest(world, "same-as", {"same": [x, y]}, until_superseded=True, **kw)


def test_accepted_equivalence_between_two_values(wm, w):
    link(wm, w, "shelf", "cell-12")
    a = where(wm, w)
    assert (a.status, a.values, len(a.support)) == (Status.ASSERTED, ("cell-12",), 2)
    held = both(wm, lambda m: m.holds(w, "located-at", {"located": "box", "place": "shelf"}, T("10:30")))
    assert (held.status, held.holds) == (Status.ASSERTED, True)
    facts = both(wm, lambda m: m.facts_about(w, "box", T("10:30")))
    assert [f["roles"]["place"] for f in facts if f["type"] == "located-at"] == [["cell-12"]]


def test_genuinely_different_values_stay_disputed(wm, w):
    link(wm, w, "shelf", "cell-12")
    wm.attest(w, "located-at", {"located": "box", "place": "dock"}, start=T("10:00"), until_superseded=True)
    a = where(wm, w)
    assert (a.status, a.values) == (Status.DISPUTED, ("cell-12", "dock"))


def test_unaccepted_equivalence_does_not_merge(wm, w):
    proposal = link(wm, w, "shelf", "cell-12", attester="matcher")
    a = where(wm, w)
    assert (a.status, a.values) == (Status.DISPUTED, ("cell-12", "shelf"))
    wm.accept(proposal, "rejected")
    assert where(wm, w).status == Status.DISPUTED


def test_equivalence_is_perspective_specific(wm, w):
    link(wm, w, "shelf", "cell-12", attester="matcher")
    mine = where(wm, w, perspective="matcher")          # the matcher's own link is part of its view
    # matcher has not accepted the system's location attestations, so its view has no location yet
    assert mine.status in (Status.UNKNOWN, Status.NOT_YET_KNOWN)
    for p in ("shelf", "cell-12"):
        wm.attest(w, "located-at", {"located": "box", "place": p}, start=T("10:00"), until_superseded=True,
                  attester="matcher")
    mine = where(wm, w, perspective="matcher")
    assert (mine.status, mine.values) == (Status.ASSERTED, ("cell-12",))
    system = where(wm, w)
    assert system.status == Status.DISPUTED                 # the system has not accepted the matcher's link


def test_historical_equivalence_respects_knowledge_time(wm, w):
    before = wm.clock.now
    lk = link(wm, w, "shelf", "cell-12", attester="matcher")
    wm.accept(lk)
    accepted = wm.clock.now
    wm.accept(lk, "rejected", reason="different shelves after all")
    assert where(wm, w, as_of=before).status == Status.DISPUTED      # link not yet recorded
    assert where(wm, w, as_of=accepted).status == Status.ASSERTED    # accepted then
    assert where(wm, w).status == Status.DISPUTED                    # rejected now


def test_hypothetical_snapshot_and_stipulated_identity(wm, w):
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("12:00"))
    link(wm, w, "shelf", "cell-12")                                   # recorded in the base after the branch
    assert where(wm, w).status == Status.ASSERTED
    assert where(wm, h).status == Status.DISPUTED                     # the snapshot does not pull it in
    g = wm.create_world("plan-b", kind="hypothetical", base=w, branch_at=T("12:00"))
    wm.attest(g, "same-as", {"same": ["shelf", "dock"]}, until_superseded=True)   # identity stipulated in a variant
    wm.attest(g, "located-at", {"located": "box", "place": "dock"}, start=T("10:00"), until_superseded=True)
    a = where(wm, g)
    assert (a.status, a.values) == (Status.STIPULATED, ("cell-12",))  # shelf = cell-12 (base) = dock (stipulated)
    assert where(wm, w).values == ("cell-12",)


def test_several_names_and_transitive_chains(wm, w):
    wm.attest(w, "located-at", {"located": "box", "place": "bay-3"}, start=T("10:00"), until_superseded=True)
    link(wm, w, "shelf", "cell-12")
    assert where(wm, w).values == ("bay-3", "cell-12")                # bay-3 not yet linked: disputed
    link(wm, w, "cell-12", "x-ref")                                   # chain through an id no answer mentions
    link(wm, w, "x-ref", "bay-3")
    a = where(wm, w)
    assert (a.status, a.values, len(a.support)) == (Status.ASSERTED, ("bay-3",), 3)
    held = both(wm, lambda m: m.holds(w, "located-at", {"located": "box", "place": "dock"}, T("10:30")))
    assert (held.status, held.holds) == (Status.INFERRED, False)


def test_identity_of_the_subject_still_works(wm, w):
    wm.add_entity("physical-object", "track-9", id="track-9")
    wm.attest(w, "located-at", {"located": "track-9", "place": "dock"}, start=T("10:00"), until_superseded=True)
    link(wm, w, "box", "track-9")
    link(wm, w, "shelf", "cell-12")
    a = where(wm, w)
    assert (a.status, a.values) == (Status.DISPUTED, ("cell-12", "dock"))
