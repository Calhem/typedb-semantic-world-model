"""Milestone 1 regression requirements, ported to Core 0.3 (from main: tests/test_worlds.py, 9 tests).

A variant now changes inherited content by stipulation (v0.2 DR-14): its own attestations are stipulations, and it
removes an inherited fact with a stipulated denial or an ended restatement, never by rejecting the base's claim.
"""

import pytest

from conftest import T
from worldmodel.semantics import Status


@pytest.fixture
def base(wm):
    w = wm.create_world("actual", id="actual")
    for kind, name in (("physical-object", "box"), ("place", "shelf-3"), ("place", "shelf-4"), ("place", "dock"),
                       ("social-object", "auditor")):
        wm.add_entity(kind, name, id=name)
    loc = wm.attest(w, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_superseded=True)
    return w, loc


def where(wm, world, t, as_of=None):
    a = wm.value_at(world, "located-at", "box", t, as_of=as_of)
    return a.status, a.values


def test_later_correction_in_the_base_does_not_reach_an_earlier_branch(wm, base):
    w, loc = base
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("12:00"))
    wm.accept(loc, "rejected", reason="misread label")
    wm.attest(w, "located-at", {"located": "box", "place": "shelf-4"}, start=T("10:00"), until_superseded=True)
    assert where(wm, w, T("10:30")) == (Status.ASSERTED, ("shelf-4",))
    assert where(wm, h, T("10:30")) == (Status.ASSERTED, ("shelf-3",))      # snapshot: the correction is not pulled in
    h2 = wm.create_world("plan-v2", kind="hypothetical", base=w, branch_at=T("12:00"))
    assert where(wm, h2, T("10:30")) == (Status.ASSERTED, ("shelf-4",))


def test_explicit_earlier_knowledge_snapshot(wm, base):
    w, loc = base
    before = wm.clock.now
    wm.end(w, loc, T("10:20"))
    wm.attest(w, "located-at", {"located": "box", "place": "dock"}, start=T("10:20"), until_superseded=True)
    h = wm.create_world("as-believed", kind="hypothetical", base=w, branch_at=T("12:00"), knowledge_at=before)
    assert where(wm, h, T("10:30")) == (Status.ASSERTED, ("shelf-3",))
    with pytest.raises(ValueError):
        wm.create_world("future", kind="hypothetical", base=w, branch_at=T("12:00"),
                        knowledge_at=wm.clock.now.replace(year=2099))


def test_reviews_and_cessations_in_a_variant_never_change_the_base(wm, base):
    w, loc = base
    h = wm.create_world("what-if", kind="hypothetical", base=w, branch_at=T("12:00"))
    wm.deny(h, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_superseded=True)
    assert where(wm, h, T("10:30")) == (Status.UNKNOWN, ())                   # the variant's denial overrides
    assert where(wm, w, T("10:30")) == (Status.ASSERTED, ("shelf-3",))
    wm.end(h, loc, T("10:15"))
    assert where(wm, w, T("10:30")) == (Status.ASSERTED, ("shelf-3",))


def test_holds_and_value_at_agree_on_local_overrides(wm, base):
    w, _ = base
    h = wm.create_world("sim", kind="simulated", base=w, branch_at=T("12:00"))
    wm.attest(h, "located-at", {"located": "box", "place": "dock"}, start=T("10:30"), until_superseded=True)
    assert where(wm, h, T("11:00")) == (Status.STIPULATED, ("dock",))
    inherited = wm.holds(h, "located-at", {"located": "box", "place": "shelf-3"}, T("11:00"))
    assert (inherited.status, inherited.holds) == (Status.INFERRED, False)
    assert wm.holds(h, "located-at", {"located": "box", "place": "shelf-3"}, T("10:15")).holds is True


def test_contradictions_within_a_variant_are_disputed(wm, base):
    w, _ = base
    h = wm.create_world("sim", kind="simulated", base=w, branch_at=T("12:00"))
    wm.attest(h, "located-at", {"located": "box", "place": "dock"}, start=T("10:30"), until_superseded=True)
    wm.attest(h, "located-at", {"located": "box", "place": "shelf-4"}, start=T("10:30"), until_superseded=True)
    assert where(wm, h, T("11:00")) == (Status.DISPUTED, ("dock", "shelf-4"))


def test_historical_queries_on_a_variant(wm, base):
    w, _ = base
    before_branch = wm.clock.now
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("12:00"))
    assert where(wm, h, T("10:30"), as_of=before_branch) == (Status.NOT_YET_KNOWN, ())
    after_branch = wm.clock.now
    wm.attest(h, "located-at", {"located": "box", "place": "dock"}, start=T("12:30"), until_superseded=True)
    assert where(wm, h, T("13:00"), as_of=after_branch) == (Status.ASSERTED, ("shelf-3",))
    assert where(wm, h, T("13:00")) == (Status.STIPULATED, ("dock",))


def test_nested_variants_apply_the_tightest_limits(wm, base):
    w, _ = base
    p = wm.create_world("parent-plan", kind="hypothetical", base=w, branch_at=T("12:00"))
    for kind, n in (("category", "open"), ("category", "sealed"), ("quality-kind", "lid")):
        wm.add_entity(kind, n, id=n)
    wm.attest(w, "has-quality", {"bearer": "box", "quality": "lid", "value": "open"}, start=T("12:30"),
              until_superseded=True)
    wm.attest(p, "has-quality", {"bearer": "box", "quality": "lid", "value": "sealed"}, start=T("11:00"),
              until_superseded=True)
    v = wm.create_world("child-plan", kind="hypothetical", base=p, branch_at=T("13:00"))
    wm.attest(p, "located-at", {"located": "box", "place": "dock"}, start=T("11:30"), until_superseded=True)

    def states(world):
        return sorted(f["roles"]["value"][0] for f in wm.facts_about(world, "box", T("14:00")) if f["type"] == "has-quality")

    assert states(w) == ["open"]
    assert states(p) == ["sealed"]
    assert states(v) == ["sealed"]
    assert where(wm, p, T("12:00")) == (Status.STIPULATED, ("dock",))
    assert where(wm, v, T("12:00")) == (Status.ASSERTED, ("shelf-3",))


def test_entity_facts_in_a_variant_never_answer_in_the_base(wm, base):
    w, _ = base
    h = wm.create_world("what-if", kind="hypothetical", base=w, branch_at=T("12:00"))
    wm.add_entity("physical-object", "ghost-crate", id="ghost-crate")
    wm.attest(h, "located-at", {"located": "ghost-crate", "place": "dock"}, start=T("12:30"), until_superseded=True)
    assert wm.value_at(w, "located-at", "ghost-crate", T("13:00")).status == Status.NOT_YET_KNOWN
    assert wm.facts_about(w, "ghost-crate", T("13:00")) == []


def test_non_functional_inherited_facts_stay_until_ceased(wm, base):
    w, _ = base
    for kind, c in (("category", "fragile"), ("category", "heavy"), ("quality-kind", "handling")):
        wm.add_entity(kind, c, id=c)
    fragile = wm.attest(w, "has-quality", {"bearer": "box", "quality": "handling", "value": "fragile"},
                        start=T("09:00"), until_superseded=True)
    h = wm.create_world("what-if", kind="hypothetical", base=w, branch_at=T("12:00"))
    wm.attest(h, "has-quality", {"bearer": "box", "quality": "handling", "value": "heavy"}, start=T("12:30"),
              until_superseded=True)
    a = wm.value_at(h, "has-quality", "box", T("13:00"), key_role="bearer", value_role="value")
    assert a.values == ("fragile", "heavy")
    assert wm.holds(h, "has-quality", {"bearer": "box", "value": "fragile"}, T("13:00")).holds is True
    wm.end(h, fragile, T("12:45"))
    a = wm.value_at(h, "has-quality", "box", T("13:00"), key_role="bearer", value_role="value")
    assert a.values == ("heavy",)
    assert wm.value_at(w, "has-quality", "box", T("13:00"), key_role="bearer", value_role="value").values == ("fragile",)
