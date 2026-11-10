"""LABS-1.009: truncated traversals are never authoritative; competing transforms are judged, never discarded.

A search truncated by its resource limit may return the transform it computed, but only as an unverified candidate:
transform_between and where say verification is incomplete, and no unverified candidate can make a where answer
ASSERTED, INFERRED or STIPULATED. Competing transforms (same pair, inverse direction, alternative route) are all kept as
edges and judged, with perspective, time and hypothetical worlds applied as for any content.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from conftest import FakeClock
from worldmodel import PHYSICAL_MODULES, WorldModel
from worldmodel.physical import PhysicalMixin
from worldmodel.semantics import Status
from worldmodel.spatial import Transform

R = PhysicalMixin()
T0 = datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc)
T = T0 + timedelta(hours=2)


def edge(parent, child, t=(1.0, 0.0, 0.0)):
    return {"parent": parent, "child": child, "transform": Transform(t=t), "support": [f"{parent}>{child}"],
            "disputed": False}


@pytest.fixture
def space(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=PHYSICAL_MODULES, clock=FakeClock())
    try:
        w = wm.create_world("actual", id="actual")
        for f in ("A", "B", "C", "D", *[f"L{i}" for i in range(6)]):
            wm.add_entity("spatial-frame", f"frame {f}", id=f)
        for n in ("box", "cam", "tracker"):
            wm.add_entity("physical-object", n, id=n)
        yield wm, w
    finally:
        driver.databases.get(name).delete()


def link(wm, w, parent, child, t, **kw):
    kw.setdefault("start", T0)
    kw.setdefault("until_superseded", "end" not in kw)
    return wm.relate_frames(w, parent, child, t, **kw)


def pos(wm, w, frame, x, **kw):
    kw.setdefault("start", T0)
    kw.setdefault("until_superseded", True)
    return wm.position(w, "box", frame, x, 0.0, 0.0, **kw)


# ---- 1. truncated results ---------------------------------------------------------------------------------------
def test_a_truncated_search_that_reached_the_target_returns_an_unverified_candidate_only():
    star = [edge("hub", f"leaf{i}") for i in range(20)] + [edge("hub", "goal")]
    r = R._resolve(star, "goal", "hub", limit=1)
    assert r["search"]["truncated"] and not r["search"]["verified"]
    assert r["transform"] is not None and r["status"] == Status.UNKNOWN          # a candidate, not an answer
    assert "verification incomplete" in r["reason"]
    missed = R._resolve([edge(f"F{i}", f"F{i + 1}") for i in range(12)], "F0", "F12", limit=5)
    assert (missed["status"], missed["transform"]) == (Status.UNKNOWN, None) and missed["search"]["truncated"]


def test_an_unverified_candidate_cannot_make_where_authoritative(space):
    wm, w = space
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    for i in range(6):                                     # extra edges at A, so a small limit truncates the search
        link(wm, w, "A", f"L{i}", (0.0, float(i), 0.0))
    pos(wm, w, "B", 0.5)                                   # in A: 1.5, derived
    seen = pos(wm, w, "A", (1.4, 1.6), attester="cam")     # in A directly, overlapping
    wm.accept(seen)
    full = wm.where(w, "box", "A", T)
    assert (full["status"], full["verified"]) == (Status.ASSERTED, True)
    cut = wm.where(w, "box", "A", T, limit=1)              # B -> A reached, then the search stops
    derived = next(c for c in cut["candidates"] if not c["direct"])
    assert derived["x"] == pytest.approx((1.5, 1.5)) and derived["status"] == Status.UNKNOWN
    assert derived["verified"] is False and derived["search"]["truncated"]
    assert cut["verified"] is False and cut["status"] == Status.UNKNOWN          # not ASSERTED
    assert "verification incomplete" in cut["reason"]
    tb = wm.transform_between(w, "B", "A", T, limit=1)
    assert (tb["status"], tb["search"]["verified"]) == (Status.UNKNOWN, False) and tb["transform"] is not None


def test_verified_conflicts_still_decide_despite_an_unverified_candidate(space):
    wm, w = space
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    for i in range(6):
        link(wm, w, "A", f"L{i}", (0.0, float(i), 0.0))
    pos(wm, w, "B", 0.5)
    for x, who in (((1.4, 1.6), "cam"), ((9.0, 9.1), "tracker")):  # two direct claims that are disjoint
        wm.accept(pos(wm, w, "A", x, attester=who))
    cut = wm.where(w, "box", "A", T, limit=1)
    assert cut["status"] == Status.DISPUTED and cut["verified"] is False
    assert {d.get("unverified", False) for d in cut["conflict_details"]} == {False, True}


# ---- 2. competing transforms -------------------------------------------------------------------------------------
def test_two_accepted_incompatible_transforms_for_one_pair_are_disputed(space):
    wm, w = space
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    wm.accept(link(wm, w, "A", "B", (1.3, 0.0, 0.0), attester="tracker"))
    r = wm.transform_between(w, "B", "A", T)
    assert (r["status"], r["transform"]) == (Status.DISPUTED, None)
    assert r["search"]["relevant_edges"] == 2 and r["search"]["inconsistent"]     # both kept as edges
    pos(wm, w, "B", 0.0)
    a = wm.where(w, "box", "A", T)
    assert a["status"] == Status.DISPUTED and a["candidates"][0]["x"] is None


def test_a_competing_transform_stated_in_the_inverse_direction_is_kept(space):
    wm, w = space
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    wm.accept(link(wm, w, "B", "A", (-1.0, 0.0, 0.0), attester="tracker"))     # the same relation, inverted: agrees
    assert wm.transform_between(w, "B", "A", T)["status"] == Status.INFERRED
    wm.accept(link(wm, w, "B", "A", (-2.0, 0.0, 0.0), attester="cam"))         # inverted and incompatible
    r = wm.transform_between(w, "B", "A", T)
    assert r["status"] == Status.DISPUTED and r["search"]["relevant_edges"] == 3


def test_a_competing_transform_on_an_alternative_route(space):
    wm, w = space
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    link(wm, w, "B", "C", (1.0, 0.0, 0.0))
    alt = link(wm, w, "A", "D", (0.0, 1.0, 0.0), attester="tracker")
    wm.accept(alt)
    link(wm, w, "D", "C", (2.0, -1.0, 0.0))                                   # A -> D -> C agrees with A -> B -> C
    assert wm.transform_between(w, "C", "A", T)["status"] == Status.INFERRED
    wm.accept(link(wm, w, "D", "C", (2.5, -1.0, 0.0), attester="cam"))        # a competing D -> C on that route
    r = wm.transform_between(w, "C", "A", T)
    assert r["status"] == Status.DISPUTED and r["transform"] is None


def test_competing_transforms_are_judged_per_perspective(space):
    wm, w = space
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    rival = link(wm, w, "A", "B", (1.3, 0.0, 0.0), attester="tracker")
    assert wm.transform_between(w, "B", "A", T)["status"] == Status.INFERRED            # unreviewed by the system
    mine = wm.transform_between(w, "B", "A", T, perspective="tracker")
    assert mine["status"] == Status.INFERRED and mine["transform"].t == (1.3, 0.0, 0.0)
    wm.accept(rival)
    assert wm.transform_between(w, "B", "A", T)["status"] == Status.DISPUTED
    wm.accept(rival, "rejected")
    assert wm.transform_between(w, "B", "A", T)["status"] == Status.INFERRED


def test_competing_transforms_over_time(space):
    wm, w = space
    t1, t2 = T0 + timedelta(hours=3), T0 + timedelta(hours=5)
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    wm.accept(link(wm, w, "A", "B", (1.3, 0.0, 0.0), attester="tracker", start=t1, end=t2))
    assert wm.transform_between(w, "B", "A", T)["status"] == Status.INFERRED           # before the rival
    assert wm.transform_between(w, "B", "A", t1 + timedelta(hours=1))["status"] == Status.DISPUTED
    assert wm.transform_between(w, "B", "A", t2 + timedelta(hours=1))["status"] == Status.INFERRED   # after it ended
    before = wm.clock.now
    wm.accept(link(wm, w, "A", "B", (5.0, 0.0, 0.0), attester="cam"))
    assert wm.transform_between(w, "B", "A", T)["status"] == Status.DISPUTED
    assert wm.transform_between(w, "B", "A", T, as_of=before)["status"] == Status.INFERRED   # knowledge time


def test_competing_transforms_in_hypothetical_worlds(space):
    wm, w = space
    branch = T0 + timedelta(hours=3)
    later = branch + timedelta(hours=1)
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=branch)
    link(wm, h, "A", "B", (4.0, 0.0, 0.0), start=branch)                     # overrides the inherited transform
    r = wm.transform_between(h, "B", "A", later)
    assert r["status"] == Status.INFERRED and r["transform"].t == (4.0, 0.0, 0.0)
    assert wm.transform_between(w, "B", "A", later)["transform"].t == (1.0, 0.0, 0.0)
    link(wm, h, "A", "B", (4.5, 0.0, 0.0), start=branch)                     # two stipulations that disagree
    assert wm.transform_between(h, "B", "A", later)["status"] == Status.DISPUTED
    g = wm.create_world("plan-b", kind="hypothetical", base=w, branch_at=branch)
    wm.accept(link(wm, w, "A", "B", (1.3, 0.0, 0.0), attester="tracker", start=branch))   # base, after the branch
    assert wm.transform_between(g, "B", "A", later)["status"] == Status.INFERRED       # the snapshot excludes it
    assert wm.transform_between(w, "B", "A", later)["status"] == Status.DISPUTED


def test_selective_and_full_load_agree_on_competing_and_truncated_cases(space):
    wm, w = space
    link(wm, w, "A", "B", (1.0, 0.0, 0.0))
    for i in range(6):
        link(wm, w, "A", f"L{i}", (0.0, float(i), 0.0))
    wm.accept(link(wm, w, "A", "B", (1.3, 0.0, 0.0), attester="tracker"))
    pos(wm, w, "B", 0.5)

    def ask():
        return [wm.where(w, "box", "A", T), wm.where(w, "box", "A", T, limit=1),
                wm.transform_between(w, "B", "A", T), wm.transform_between(w, "B", "A", T, limit=1),
                wm.transform_between(w, "B", "A", T, perspective="tracker")]

    wm.selective = True
    selective = ask()
    wm.selective = False
    full = ask()
    wm.selective = True
    assert full == selective
