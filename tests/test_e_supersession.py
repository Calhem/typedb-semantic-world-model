"""Supersession and acceptance across perspectives (found in Stage D; World Ontology v0.2 §5.2-5.3, E3-E4).

Source A asserts P; perspective B ("lead") accepts A's attestation; A then ends, retracts or corrects it. Intended:
- a source's revision does not count as B's acceptance; B keeps its accepted evidence (possibly outdated) until B
  accepts the revision, and the answer shows that the source has revised it;
- once B accepts the revision, B follows it; if B rejects it, B keeps the original;
- the source's own view follows its revision immediately; everything stays reproducible at earlier knowledge times;
- a hypothetical world branched before the revision is unaffected.
"""

import pytest

from conftest import T
from worldmodel.semantics import Status

LOC = {"located": "box", "place": "shelf-3"}


@pytest.fixture
def setup(wm):
    w = wm.create_world("actual", id="actual")
    for kind, n in (("physical-object", "box"), ("place", "shelf-3"), ("place", "shelf-4"), ("physical-object", "A"),
                    ("social-object", "lead")):
        wm.add_entity(kind, n, id=n)
    a = wm.attest(w, "located-at", LOC, start=T("10:00"), until_superseded=True, attester="A")
    wm.accept(a, holder="lead")
    accepted = wm.clock.now
    return w, a, accepted


def view(wm, w, t, as_of=None, who="lead"):
    ans = wm.value_at(w, "located-at", "box", t, as_of=as_of, perspective=who)
    return ans.status, ans.values


def test_ending_does_not_erase_another_perspectives_accepted_evidence(wm, setup):
    w, a, accepted = setup
    b = wm.end(w, a, T("11:00"))                                         # A: it was there only until 11:00
    assert view(wm, w, T("10:30")) == (Status.ASSERTED, ("shelf-3",))     # both versions agree at 10:30
    assert view(wm, w, T("11:30")) == (Status.ASSERTED, ("shelf-3",))     # B keeps its outdated belief...
    (e,) = wm.value_at(w, "located-at", "box", T("11:30"), perspective="lead").evidence
    assert e["attestation"] == a and e["superseded_by_source"] == [b]     # ...visibly revised by its source
    assert view(wm, w, T("11:30"), who="A")[0] == Status.UNKNOWN          # A's own view follows the revision
    assert view(wm, w, T("11:30"), as_of=accepted) == (Status.ASSERTED, ("shelf-3",))


def test_accepting_the_replacement_follows_it(wm, setup):
    w, a, _ = setup
    b = wm.end(w, a, T("11:00"))
    wm.accept(b, holder="lead")
    assert view(wm, w, T("10:30")) == (Status.ASSERTED, ("shelf-3",))
    assert view(wm, w, T("11:30"))[0] == Status.UNKNOWN
    assert wm.holds(w, "located-at", LOC, T("11:30"), perspective="lead").holds is False


def test_rejecting_the_replacement_keeps_the_original(wm, setup):
    w, a, _ = setup
    b = wm.end(w, a, T("11:00"))
    wm.accept(b, "rejected", holder="lead", reason="the camera still shows it")
    assert view(wm, w, T("11:30")) == (Status.ASSERTED, ("shelf-3",))


def test_explicit_retraction_by_the_source_is_not_anothers_decision(wm, setup):
    w, a, accepted = setup
    wm.accept(a, "retracted", holder="A", reason="I was wrong")         # A withdraws its own claim
    assert view(wm, w, T("10:30"), who="A")[0] == Status.UNKNOWN
    assert view(wm, w, T("10:30")) == (Status.ASSERTED, ("shelf-3",))     # B decided for itself
    wm.accept(a, "rejected", holder="lead", reason="A withdrew it")
    assert view(wm, w, T("10:30"))[0] == Status.UNKNOWN
    assert view(wm, w, T("10:30"), as_of=accepted) == (Status.ASSERTED, ("shelf-3",))


def test_correction_of_an_erroneous_historical_assertion(wm, setup):
    w, a, accepted = setup
    c = wm.attest(w, "located-at", {"located": "box", "place": "shelf-4"}, start=T("10:00"), until_superseded=True,
                  attester="A", supersedes=a)                              # A: it was shelf-4 all along
    assert view(wm, w, T("10:30"), who="A") == (Status.ASSERTED, ("shelf-4",))
    lead = wm.value_at(w, "located-at", "box", T("10:30"), perspective="lead")
    assert (lead.status, lead.values, lead.alternatives) == (Status.ASSERTED, ("shelf-3",), (c,))
    wm.accept(c, holder="lead")
    assert view(wm, w, T("10:30")) == (Status.ASSERTED, ("shelf-4",))     # not DISPUTED: the original is superseded
    assert view(wm, w, T("10:30"), as_of=accepted) == (Status.ASSERTED, ("shelf-3",))


def test_supersession_must_be_by_the_same_attester(wm, setup):
    w, a, _ = setup
    with pytest.raises(ValueError):
        wm.attest(w, "located-at", {"located": "box", "place": "shelf-4"}, start=T("10:00"), supersedes=a)  # system


def test_hypothetical_branched_before_the_revision_is_unaffected(wm, setup):
    w, a, _ = setup
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("12:00"))
    b = wm.end(w, a, T("11:00"))
    wm.accept(b, holder="lead")
    assert view(wm, w, T("11:30"))[0] == Status.UNKNOWN                    # actual: B follows the revision
    assert view(wm, h, T("11:30")) == (Status.ASSERTED, ("shelf-3",))      # plan: snapshot before it


def test_both_query_paths_agree_for_every_perspective(wm, setup):
    from worldmodel import WorldModel
    w, a, accepted = setup
    wm.add_entity("social-object", "auditor", id="auditor")
    wm.accept(a, holder="auditor")
    b = wm.end(w, a, T("11:00"))
    mid = wm.clock.now
    c = wm.attest(w, "located-at", {"located": "box", "place": "shelf-4"}, start=T("11:00"), until_superseded=True,
                  attester="A", supersedes=b)
    wm.accept(b, holder="lead")
    wm.accept(c, "rejected", holder="auditor")
    full = WorldModel.open(wm.database, driver=wm.driver)
    full.selective = False
    wm.selective = True
    for who in ("A", "lead", "auditor", "system"):
        for t in (T("10:30"), T("11:30")):
            for as_of in (accepted, mid, None):
                assert wm.value_at(w, "located-at", "box", t, as_of, who) == full.value_at(w, "located-at", "box", t, as_of, who)
                assert wm.holds(w, "located-at", LOC, t, as_of, who) == full.holds(w, "located-at", LOC, t, as_of, who)
