"""LABS-1.005, F-4: holds() reports a functional conflict as DISPUTED, consistently with value_at.

When accepted contents give incompatible values to one functional slot (one thing in two places), each of them is
DISPUTED for the perspective (v0.2 §5.3 rule 2, §5.6). The answer keeps the asked content's own support apart from
the conflicting attestations (`conflicts`), with evidence for both. Nothing is rejected or deleted, and the sources'
attestations are unchanged: the dispute is the perspective's judgement. Every question is asked on both paths.
"""

from pathlib import Path

import pytest

from conftest import T
from worldmodel import WorldModel
from worldmodel.semantics import Status

PROFILE = str(Path(__file__).resolve().parent / "fixtures" / "profile-a0.tql")


@pytest.fixture
def w(wm):
    world = wm.create_world("actual", id="actual")
    for kind, n in (("physical-object", "box"), ("physical-object", "crate"), ("place", "shelf"), ("place", "dock"),
                    ("place", "cell-12"), ("place", "yard"), ("social-object", "cam")):
        wm.add_entity(kind, n, id=n)
    return world


def both(wm, ask):
    full = WorldModel.open(wm.database, driver=wm.driver, clock=wm.clock)
    full.selective = False
    wm.selective = True
    a, b = ask(wm), ask(full)
    assert a == b
    return a


def at(wm, world, thing, place, start=T("10:00"), **kw):
    return wm.attest(world, "located-at", {"located": thing, "place": place}, start=start, until_superseded=True, **kw)


def holds(wm, world, thing, place, t=T("10:30"), type="located-at", **kw):
    return both(wm, lambda m: m.holds(world, type, {"located": thing, "place": place}, t, **kw))


def test_two_incompatible_values_are_both_disputed(wm, w):
    s, d = at(wm, w, "box", "shelf"), at(wm, w, "box", "dock")
    for place, own, other in (("shelf", s, d), ("dock", d, s)):
        a = holds(wm, w, "box", place)
        assert (a.status, a.holds, a.support, a.conflicts) == (Status.DISPUTED, None, (own,), (other,))
        assert {e["attestation"] for e in a.evidence} == {own, other}        # both sides' evidence is available
    assert both(wm, lambda m: m.value_at(w, "located-at", "box", T("10:30"))).status == Status.DISPUTED
    assert {h["attestation"] for h in wm.history(w, "box")} == {s, d}           # nothing rejected or deleted


def test_compatible_facts_sharing_a_non_functional_role_stay_asserted(wm, w):
    at(wm, w, "box", "shelf")
    at(wm, w, "crate", "shelf")
    a = holds(wm, w, "box", "shelf")
    assert (a.status, a.holds, a.conflicts) == (Status.ASSERTED, True, ())


def test_values_made_equivalent_by_accepted_identity_do_not_conflict(wm, w):
    at(wm, w, "box", "shelf")
    at(wm, w, "box", "cell-12")
    assert holds(wm, w, "box", "shelf").status == Status.DISPUTED
    wm.attest(w, "same-as", {"same": ["shelf", "cell-12"]}, until_superseded=True)
    a = holds(wm, w, "box", "shelf")
    assert (a.status, a.holds, a.conflicts) == (Status.ASSERTED, True, ())


def test_perspective_specific_acceptance_and_rejection(wm, w):
    at(wm, w, "box", "shelf")
    cams = at(wm, w, "box", "dock", attester="cam")
    a = holds(wm, w, "box", "shelf")
    assert (a.status, a.holds, a.conflicts) == (Status.ASSERTED, True, ())   # unreviewed: no conflict yet
    assert holds(wm, w, "box", "dock", perspective="cam").holds is True               # cam's own view
    wm.accept(cams)
    assert holds(wm, w, "box", "shelf").status == Status.DISPUTED
    assert holds(wm, w, "box", "dock", perspective="cam").status == Status.ASSERTED   # cam never accepted shelf
    wm.accept(cams, "rejected")
    assert holds(wm, w, "box", "shelf").status == Status.ASSERTED


def test_history_and_knowledge_time(wm, w):
    wm.attest(w, "located-at", {"located": "box", "place": "shelf"}, start=T("09:00"), end=T("10:00"))
    at(wm, w, "box", "dock")
    assert holds(wm, w, "box", "dock").status == Status.ASSERTED                      # moved: not a conflict
    assert holds(wm, w, "box", "shelf", t=T("09:30")).holds is True
    before = wm.clock.now
    at(wm, w, "box", "yard")
    assert holds(wm, w, "box", "dock").status == Status.DISPUTED
    assert holds(wm, w, "box", "dock", as_of=before).status == Status.ASSERTED         # not yet known then


def test_hypothetical_snapshots(wm, w):
    at(wm, w, "box", "shelf")
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("12:00"))
    at(wm, w, "box", "dock")                                   # recorded in the base after the branch
    assert holds(wm, w, "box", "shelf").status == Status.DISPUTED
    assert holds(wm, h, "box", "shelf").status == Status.ASSERTED                     # the snapshot excludes it
    at(wm, h, "box", "yard", start=T("12:30"))                 # a variant's own value overrides the inherited one
    a = holds(wm, h, "box", "yard", t=T("13:00"))
    assert (a.status, a.holds) == (Status.STIPULATED, True)
    old = holds(wm, h, "box", "shelf", t=T("13:00"))
    assert (old.status, old.holds) == (Status.INFERRED, False)
    at(wm, h, "box", "dock", start=T("12:30"))                 # two stipulated values in the variant
    assert holds(wm, h, "box", "yard", t=T("13:00")).status == Status.DISPUTED


def test_inherited_constraint_on_subtype_propositions(wm, w):
    wm.install_module("test-profile-a0", files=[PROFILE], version="0")
    wm.add_entity("dock", "dock-2", id="dock-2")
    at(wm, w, "box", "shelf")
    d = wm.attest(w, "docked-at", {"located": "box", "place": "dock-2"}, start=T("10:00"), until_superseded=True)
    a = holds(wm, w, "box", "dock-2", type="docked-at")
    assert (a.status, a.support) == (Status.DISPUTED, (d,))
    assert holds(wm, w, "box", "shelf").status == Status.DISPUTED
    assert holds(wm, w, "box", "dock-2").status == Status.DISPUTED                    # asked as located-at
