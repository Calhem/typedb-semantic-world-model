"""Core 0.3 clarifications found while porting (documented in docs/core-0.3/README.md).

1. A stated end implies the content stopped holding only until it is attested to start again: returning to an earlier
   place is not a dispute.
2. Ended accounts still count against other accounts: the v0.2 employment example stays DISPUTED.
"""

from datetime import datetime, timezone

import pytest

from conftest import T
from worldmodel.semantics import Status


def M(month, day=1):
    return datetime(2025, month, day, tzinfo=timezone.utc)


@pytest.fixture
def world(wm):
    w = wm.create_world("actual", id="actual")
    for kind, n in (("physical-object", "box"), ("place", "shelf-3"), ("place", "dock"), ("physical-object", "A"),
                    ("physical-object", "B"), ("social-object", "acme"), ("social-role", "employee")):
        wm.add_entity(kind, n, id=n)
    return w


def test_returning_to_an_earlier_place_is_not_a_dispute(wm, world):
    wm.attest(world, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_superseded=True)
    wm.move(world, "box", "dock", T("10:10"))
    wm.move(world, "box", "shelf-3", T("10:20"))
    a = wm.holds(world, "located-at", {"located": "box", "place": "shelf-3"}, T("10:30"))
    assert (a.status, a.holds) == (Status.ASSERTED, True)
    assert wm.holds(world, "located-at", {"located": "box", "place": "shelf-3"}, T("10:15")).holds is False
    assert wm.value_at(world, "located-at", "box", T("10:30")).values == ("shelf-3",)


def test_an_ended_account_disputes_an_ongoing_one_begun_earlier(wm, world):
    roles = {"classified": "B", "class": "employee", "context": "acme"}
    a = wm.attest(world, "classified-as", roles, start=M(1), end=M(6), attester="A")
    b = wm.attest(world, "classified-as", roles, start=M(2), end=(M(8), None), attester="B")
    wm.accept(a)
    wm.accept(b)
    assert wm.holds(world, "classified-as", roles, M(3)).holds is True               # both say so
    assert wm.holds(world, "classified-as", roles, M(7)).status == Status.DISPUTED    # A: ended in June; B: until Aug


def test_ended_accounts_are_not_dropped_by_the_selective_filter(wm, world):
    """Regression for defect D6: the TypeQL pre-filter once skipped attestations that ended before t, which removed
    their "does not hold" and turned a dispute into an assertion on the selective path only."""
    from worldmodel import WorldModel
    for kind, n in (("physical-object", "track-9"), ("social-object", "matcher")):
        wm.add_entity(kind, n, id=n)
    wm.attest(world, "located-at", {"located": "box", "place": "shelf-3"}, start=T("08:00"), end=T("08:30"))
    a = wm.attest(world, "located-at", {"located": "track-9", "place": "shelf-3"}, start=T("07:00"),
                  until_superseded=True, attester="A")
    wm.accept(a)
    link = wm.attest(world, "same-as", {"same": ["box", "track-9"]}, until_superseded=True, attester="matcher")
    wm.accept(link)
    full = WorldModel.open(wm.database, driver=wm.driver)
    full.selective = False
    wm.selective = True
    roles = {"located": "box", "place": "shelf-3"}
    for model in (wm, full):
        assert model.holds(world, "located-at", roles, T("09:00")).status == Status.DISPUTED
    assert wm.holds(world, "located-at", roles, T("09:00")) == full.holds(world, "located-at", roles, T("09:00"))
    assert wm.value_at(world, "located-at", "box", T("09:00")) == full.value_at(world, "located-at", "box", T("09:00"))
