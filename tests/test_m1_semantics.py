"""Milestone 1 regression requirements, ported to Core 0.3 (from main: tests/test_semantics.py, 6 tests).
until_ceased is now `until-superseded`; cessations are supersessions; reviews are a perspective's acceptances."""

from datetime import datetime, timezone

from conftest import T
from worldmodel.semantics import AttestationRecord, Identity, Replacement, Window, acceptance_state, usable, verdict

REC = datetime(2030, 1, 1, tzinfo=timezone.utc)


def att(start=None, end=None, basis="unknown", **kw):
    return AttestationRecord(id=kw.get("id", "a"), content="k", ctype=kw.get("ctype", "located-at"),
                             roles=kw.get("roles", {}), params={}, attester=kw.get("attester", "system"), world="w",
                             stance="asserts", polarity=True, basis="testimony", start=start, end=end, end_basis=basis,
                             recorded_at=REC)


def test_until_ceased_holds_after_start_and_is_silent_before():
    a = att(Window.at(T("10:00")), basis="until-superseded")
    assert (verdict(a, T("09:59")), verdict(a, T("10:00")), verdict(a, T("23:00"))) == (None, True, True)


def test_unknown_end_decides_nothing_after_start():
    assert verdict(att(Window.at(T("10:00"))), T("10:05")) is None


def test_stated_end_window():
    a = att(Window.at(T("10:00")), Window(T("10:06"), T("10:09")), basis="stated")
    assert (verdict(a, T("10:05")), verdict(a, T("10:07")), verdict(a, T("10:09"))) == (True, None, False)


def test_cessation_counts_only_once_recorded():
    a = att(Window.at(T("10:00")), basis="until-superseded")
    a.superseded_by.append(Replacement("b", REC.replace(year=2031), "system", "asserts"))
    assert usable(a, "system", REC) and not usable(a, "system", None)


def test_status_latest_review_wins_and_rejection_wins_ties():
    a = att(attester="detector")
    assert acceptance_state(a, "system", None) == "unreviewed"
    a.acceptances += [("system", "accepted", REC.replace(year=2031)), ("system", "rejected", REC.replace(year=2032))]
    assert acceptance_state(a, "system", REC.replace(year=2031, month=6)) == "accepted"
    assert acceptance_state(a, "system", None) == "rejected"
    a.acceptances += [("system", "accepted", REC.replace(year=2033)), ("system", "retracted", REC.replace(year=2033))]
    assert acceptance_state(a, "system", None) == "retracted"


def test_identity_uses_accepted_links_only_and_never_chains_proposed():
    ab = att(id="s1", ctype="same-as", roles={"same": ["a", "b"]})
    bc = att(id="s2", ctype="same-as", roles={"same": ["b", "c"]}, attester="matcher")
    ident = Identity([ab, bc], "system", None)
    assert ident.members("a") == ["a", "b"] and ident.canonical("c") == "c"
    assert ident.proposed == [("s2", "b", "c")]
