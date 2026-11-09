"""Stage B, pure semantics: polarity, acceptance by perspective, supersession, identity (no database)."""

from datetime import datetime, timezone

from conftest import T
from worldmodel.semantics import AttestationRecord, Identity, Window, acceptance_state, usable, verdict

REC = datetime(2030, 1, 1, tzinfo=timezone.utc)
LATER = datetime(2031, 1, 1, tzinfo=timezone.utc)


def att(polarity=True, start=None, end=None, basis_end="unknown", attester="system", stance="asserts", ctype="located-at",
        roles=None, id="a"):
    return AttestationRecord(id=id, content="k", ctype=ctype, roles=roles or {}, params={}, attester=attester, world="w",
                             stance=stance, polarity=polarity, basis="testimony", start=start, end=end,
                             end_basis=basis_end, recorded_at=REC)


def test_assertions_and_denials_say_different_things():
    a = att(start=Window.at(T("10:00")), end=Window.at(T("11:00")), basis_end="stated")
    assert (verdict(a, T("09:00")), verdict(a, T("10:30")), verdict(a, T("11:30"))) == (None, True, False)
    d = att(polarity=False, start=Window.at(T("10:00")), end=Window.at(T("11:00")), basis_end="stated")
    assert (verdict(d, T("09:00")), verdict(d, T("10:30")), verdict(d, T("11:30"))) == (None, False, None)


def test_unknown_end_and_until_superseded():
    assert verdict(att(start=Window.at(T("10:00"))), T("12:00")) is None              # no invented continuity
    assert verdict(att(start=Window.at(T("10:00")), basis_end="until-superseded"), T("12:00")) is True


def test_existence_start_is_creation():
    e = att(ctype="existence", start=(Window(T("10:00"), T("10:20"))), basis_end="until-superseded")
    assert (verdict(e, T("09:59")), verdict(e, T("10:10")), verdict(e, T("10:20"))) == (False, None, True)


def test_acceptance_is_per_perspective_and_ordered():
    a = att(attester="A")
    assert acceptance_state(a, "system", None) == "unreviewed"
    assert acceptance_state(a, "A", None) == "accepted"                                 # own attestations
    a.acceptances += [("system", "accepted", REC), ("system", "rejected", LATER), ("lead", "accepted", LATER)]
    assert acceptance_state(a, "system", REC) == "accepted"
    assert acceptance_state(a, "system", None) == "rejected"
    assert acceptance_state(a, "lead", None) == "accepted"
    a.acceptances += [("lead", "accepted", LATER.replace(year=2032)), ("lead", "retracted", LATER.replace(year=2032))]
    assert acceptance_state(a, "lead", None) == "retracted"                              # rejection wins ties


def test_stipulations_are_constitutive_and_supersession_hides():
    s = att(stance="stipulates", attester="planner")
    s.acceptances.append(("system", "rejected", REC))
    assert acceptance_state(s, "system", None) == "accepted"
    a = att()
    a.superseded_by.append(("b", LATER))
    assert usable(a, "system", REC) and not usable(a, "system", None)
    assert not usable(att(stance="hypothesises"), "system", None)


def test_identity_never_chains_unaccepted_links():
    ab = att(id="s1", ctype="same-as", roles={"same": ["a", "b"]})
    bc = att(id="s2", ctype="same-as", roles={"same": ["b", "c"]}, attester="matcher")
    ident = Identity([ab, bc], "system", None)
    assert ident.members("a") == ["a", "b"] and ident.canonical("c") == "c"
    assert ident.proposed == [("s2", "b", "c")]
