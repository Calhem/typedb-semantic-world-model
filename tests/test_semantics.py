"""Pure semantics (no database): valid-time truth, status at a transaction time, identity closure."""

from datetime import datetime, timezone

from conftest import T
from worldmodel.semantics import ClaimRecord, Identity, Window, status_at, truth_at

REC = datetime(2030, 1, 1, tzinfo=timezone.utc)


def claim(start=None, end=None, basis="unknown", **kw):
    return ClaimRecord(id=kw.get("id", "c"), type=kw.get("type", "located-at"), world="w", roles=kw.get("roles", {}),
                       start=start, end=end, end_basis=basis, recorded_at=REC, initial_status=kw.get("status", "accepted"))


def test_until_ceased_holds_after_start_and_is_silent_before():
    c = claim(Window.at(T("10:00")), basis="until-ceased")
    assert truth_at(c, T("09:59"), None) is None          # silent before its start, not false
    assert truth_at(c, T("10:00"), None) is True
    assert truth_at(c, T("23:00"), None) is True


def test_unknown_end_decides_nothing_after_start():
    c = claim(Window.at(T("10:00")), basis="unknown")
    assert truth_at(c, T("10:05"), None) is None          # no invented continuity


def test_stated_end_window():
    c = claim(Window.at(T("10:00")), Window(T("10:06"), T("10:09")), basis="stated")
    assert truth_at(c, T("10:05"), None) is True
    assert truth_at(c, T("10:07"), None) is None          # inside the end window: undecided
    assert truth_at(c, T("10:09"), None) is False


def test_cessation_counts_only_once_recorded():
    c = claim(Window.at(T("10:00")), basis="until-ceased")
    c.cessations.append((Window.at(T("10:30")), REC.replace(year=2031), "w"))
    assert truth_at(c, T("11:00"), REC) is True           # as known before the cessation was recorded
    assert truth_at(c, T("11:00"), None) is False


def test_status_latest_review_wins_and_rejection_wins_ties():
    c = claim(status="proposed")
    assert status_at(c, None) == "proposed"
    c.reviews += [("accepted", REC.replace(year=2031)), ("rejected", REC.replace(year=2032))]
    assert status_at(c, REC.replace(year=2031, month=6)) == "accepted"
    assert status_at(c, None) == "rejected"
    c.reviews.append(("accepted", REC.replace(year=2033)))
    c.reviews.append(("retracted", REC.replace(year=2033)))
    assert status_at(c, None) == "retracted"


def test_identity_uses_accepted_links_only_and_never_chains_proposed():
    a_b = claim(id="s1", type="same-as", roles={"same": ["a", "b"]})
    b_c = claim(id="s2", type="same-as", roles={"same": ["b", "c"]}, status="proposed")
    ident = Identity([a_b, b_c], None)
    assert ident.members("a") == ["a", "b"]
    assert ident.canonical("c") == "c"
    assert ident.proposed == [("s2", "b", "c")]
