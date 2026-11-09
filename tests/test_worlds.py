"""World inheritance and isolation (Milestone 1 review): fixed branch-time snapshots, no leaks into the base."""

import pytest

from conftest import T
from worldmodel import Status


@pytest.fixture
def base(wm):
    w = wm.create_world("actual", id="actual")
    for kind, name in (("physical-object", "box"), ("place", "shelf-3"), ("place", "shelf-4"), ("place", "dock")):
        wm.add_entity(kind, name, id=name)
    loc = wm.assert_fact(w, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_ceased=True)
    return w, loc


def where(wm, world, t, as_of=None):
    a = wm.value_at(world, "located-at", "box", t, as_of=as_of)
    return a.status, a.values


def test_later_correction_in_the_base_does_not_reach_an_earlier_branch(wm, base):
    w, loc = base
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("12:00"))
    # After the branch, the base learns the box was really on shelf 4 from 10:00 (a correction about the past).
    wm.review(w, loc, "rejected", decided_by="auditor", reason="misread label")
    wm.assert_fact(w, "located-at", {"located": "box", "place": "shelf-4"}, start=T("10:00"), until_ceased=True)
    assert where(wm, w, T("10:30")) == (Status.ASSERTED, ("shelf-4",))
    assert where(wm, h, T("10:30")) == (Status.ASSERTED, ("shelf-3",))      # snapshot: the correction is not pulled in
    h2 = wm.create_world("plan-v2", kind="hypothetical", base=w, branch_at=T("12:00"))
    assert where(wm, h2, T("10:30")) == (Status.ASSERTED, ("shelf-4",))     # adopting it means branching again


def test_explicit_earlier_knowledge_snapshot(wm, base):
    w, loc = base
    before = wm.clock.now
    wm.cease(w, loc, T("10:20"))
    wm.assert_fact(w, "located-at", {"located": "box", "place": "dock"}, start=T("10:20"), until_ceased=True)
    h = wm.create_world("as-believed", kind="hypothetical", base=w, branch_at=T("12:00"), knowledge_at=before)
    assert where(wm, h, T("10:30")) == (Status.ASSERTED, ("shelf-3",))
    with pytest.raises(ValueError):
        wm.create_world("future", kind="hypothetical", base=w, branch_at=T("12:00"),
                        knowledge_at=wm.clock.now.replace(year=2099))


def test_reviews_and_cessations_in_a_variant_never_change_the_base(wm, base):
    w, loc = base
    h = wm.create_world("what-if", kind="hypothetical", base=w, branch_at=T("12:00"))
    wm.review(h, loc, "rejected", decided_by="planner")
    assert where(wm, h, T("10:30")) == (Status.UNKNOWN, ())
    assert where(wm, w, T("10:30")) == (Status.ASSERTED, ("shelf-3",))
    wm.cease(h, loc, T("10:15"))
    assert where(wm, w, T("10:30")) == (Status.ASSERTED, ("shelf-3",))


def test_holds_and_value_at_agree_on_local_overrides(wm, base):
    w, _ = base
    h = wm.create_world("sim", kind="simulated", base=w, branch_at=T("12:00"))
    wm.assert_fact(h, "located-at", {"located": "box", "place": "dock"}, start=T("10:30"), until_ceased=True)
    assert where(wm, h, T("11:00")) == (Status.ASSERTED, ("dock",))
    inherited = wm.holds(h, "located-at", {"located": "box", "place": "shelf-3"}, T("11:00"))
    assert (inherited.status, inherited.holds) == (Status.INFERRED, False)   # overridden, not contradictory
    assert wm.holds(h, "located-at", {"located": "box", "place": "shelf-3"}, T("10:15")).holds is True


def test_contradictions_within_a_variant_are_disputed(wm, base):
    w, _ = base
    h = wm.create_world("sim", kind="simulated", base=w, branch_at=T("12:00"))
    wm.assert_fact(h, "located-at", {"located": "box", "place": "dock"}, start=T("10:30"), until_ceased=True)
    wm.assert_fact(h, "located-at", {"located": "box", "place": "shelf-4"}, start=T("10:30"), until_ceased=True)
    assert where(wm, h, T("11:00")) == (Status.DISPUTED, ("dock", "shelf-4"))


def test_historical_queries_on_a_variant(wm, base):
    w, _ = base
    before_branch = wm.clock.now
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("12:00"))
    assert where(wm, h, T("10:30"), as_of=before_branch) == (Status.NOT_YET_KNOWN, ())   # the variant did not exist
    after_branch = wm.clock.now
    wm.assert_fact(h, "located-at", {"located": "box", "place": "dock"}, start=T("12:30"), until_ceased=True)
    assert where(wm, h, T("13:00"), as_of=after_branch) == (Status.ASSERTED, ("shelf-3",))
    assert where(wm, h, T("13:00")) == (Status.ASSERTED, ("dock",))


def test_nested_variants_apply_the_tightest_limits(wm, base):
    w, _ = base
    p = wm.create_world("parent-plan", kind="hypothetical", base=w, branch_at=T("12:00"))
    wm.add_entity("concept", "open", id="open")
    wm.add_entity("concept", "sealed", id="sealed")
    wm.assert_fact(w, "has-state", {"bearer": "box", "state": "open"}, start=T("12:30"), until_ceased=True)
    wm.assert_fact(p, "has-state", {"bearer": "box", "state": "sealed"}, start=T("11:00"), until_ceased=True)
    v = wm.create_world("child-plan", kind="hypothetical", base=p, branch_at=T("13:00"))
    wm.assert_fact(p, "located-at", {"located": "box", "place": "dock"}, start=T("11:30"), until_ceased=True)  # after v's snapshot
    states = lambda world: sorted(f["roles"]["state"][0] for f in wm.facts_about(world, "box", T("14:00"))
                                  if f["type"] == "has-state")
    assert states(w) == ["open"]
    assert states(p) == ["sealed"]                 # the base's 12:30 fact is after p's branch time
    assert states(v) == ["sealed"]                 # inherited through p; the base's fact still excluded
    assert where(wm, p, T("12:00")) == (Status.ASSERTED, ("dock",))
    assert where(wm, v, T("12:00")) == (Status.ASSERTED, ("shelf-3",))   # p's later knowledge is not in v's snapshot


def test_entity_facts_in_a_variant_never_answer_in_the_base(wm, base):
    w, _ = base
    h = wm.create_world("what-if", kind="hypothetical", base=w, branch_at=T("12:00"))
    wm.add_entity("physical-object", "ghost-crate", id="ghost-crate")
    wm.assert_fact(h, "located-at", {"located": "ghost-crate", "place": "dock"}, start=T("12:30"), until_ceased=True)
    assert wm.value_at(w, "located-at", "ghost-crate", T("13:00")).status == Status.NOT_YET_KNOWN
    assert wm.facts_about(w, "ghost-crate", T("13:00")) == []
