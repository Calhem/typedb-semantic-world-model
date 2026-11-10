"""LABS-1.003: the shelf dispute. Which location answers are compatible, disputed or incomparable (v0.2 §4.2, §5.3).

v0.2 §5.3 rule 2: a functional conflict is "incompatible values for a single-valued slot". located-at's slot is
(located -> place): one place per thing at a time. Nothing says one thing per place, so two things on one shelf are
compatible, whichever role the question is asked by.
"""

import pytest

from conftest import T
from worldmodel.semantics import Status


def setup(wm):
    w = wm.create_world("actual", id="actual")
    for kind, n in (("physical-object", "b1"), ("physical-object", "b2"), ("place", "shelf"), ("place", "dock"),
                    ("place", "cell-12")):
        wm.add_entity(kind, n, id=n)
    return w


def at(wm, w, thing, place, start, **kw):
    return wm.attest(w, "located-at", {"located": thing, "place": place}, start=start, until_superseded=True, **kw)


def test_two_objects_on_one_shelf_are_compatible(wm):
    w = setup(wm)
    at(wm, w, "b1", "shelf", T("10:00"))
    at(wm, w, "b2", "shelf", T("10:00"))
    on_shelf = wm.value_at(w, "located-at", "shelf", T("10:30"), key_role="place", value_role="located")
    assert (on_shelf.status, on_shelf.values) == (Status.ASSERTED, ("b1", "b2"))
    for b in ("b1", "b2"):
        assert wm.value_at(w, "located-at", b, T("10:30")).values == ("shelf",)


def test_one_object_in_two_places_at_once_is_disputed(wm):
    w = setup(wm)
    at(wm, w, "b1", "shelf", T("10:00"))
    at(wm, w, "b1", "dock", T("10:00"))
    a = wm.value_at(w, "located-at", "b1", T("10:30"))
    assert (a.status, a.values) == (Status.DISPUTED, ("dock", "shelf"))
    # Asked from the place side, each place holds one thing; the conflict is about b1's slot, so the answer that
    # contains both of b1's places is the one that is disputed, and a single place is not.
    on_shelf = wm.value_at(w, "located-at", "shelf", T("10:30"), key_role="place", value_role="located")
    assert (on_shelf.status, on_shelf.values) == (Status.ASSERTED, ("b1",))


def test_an_object_moving_over_time_is_not_a_dispute(wm):
    w = setup(wm)
    wm.attest(w, "located-at", {"located": "b1", "place": "shelf"}, start=T("10:00"), end=T("11:00"))
    at(wm, w, "b1", "dock", T("11:00"))
    assert wm.value_at(w, "located-at", "b1", T("10:30")).values == ("shelf",)
    a = wm.value_at(w, "located-at", "b1", T("11:30"))
    assert (a.status, a.values) == (Status.ASSERTED, ("dock",))
    assert [h["roles"]["place"] for h in wm.history(w, "b1")] == [["shelf"], ["dock"]]


def test_two_places_named_in_different_frames_are_still_two_places(wm):
    """Core 0.3 places carry no frame (frames and poses are Stage A: positioned-in, frame-transform). Two places at
    once are a functional conflict unless the perspective accepts that they are the same place."""
    w = setup(wm)
    at(wm, w, "b1", "shelf", T("10:00"))
    at(wm, w, "b1", "cell-12", T("10:00"))          # e.g. a map cell named in another frame
    assert wm.value_at(w, "located-at", "b1", T("10:30")).status == Status.DISPUTED


@pytest.mark.xfail(strict=True, reason="Core 0.3 defect F-5 (LABS-1.003), not corrected: the selective path loads "
                   "identity only for the subject, so co-referring value players stay two values; full load merges them")
def test_co_referring_place_names_answer_alike_on_both_paths(wm):
    w = setup(wm)
    at(wm, w, "b1", "shelf", T("10:00"))
    at(wm, w, "b1", "cell-12", T("10:00"))
    wm.attest(w, "same-as", {"same": ["shelf", "cell-12"]}, until_superseded=True)
    wm.selective = False
    full = wm.value_at(w, "located-at", "b1", T("10:30"))
    wm.selective = True
    assert full.status == Status.ASSERTED                            # one place under two names: no conflict
    assert wm.value_at(w, "located-at", "b1", T("10:30")) == full


def test_one_slot_two_objects_in_a_variant(wm):
    w = setup(wm)
    at(wm, w, "b1", "shelf", T("10:00"))
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("12:00"))
    at(wm, h, "b2", "shelf", T("12:30"))
    on_shelf = wm.value_at(h, "located-at", "shelf", T("13:00"), key_role="place", value_role="located")
    assert on_shelf.values == ("b1", "b2") and on_shelf.status != Status.DISPUTED
