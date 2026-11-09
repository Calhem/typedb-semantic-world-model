"""Stage B, live: attestations, denials, perspective-specific acceptance, worlds and time (TypeDB 3.14.1)."""

import pytest
from typedb.driver import TypeDBDriverException

from conftest import T
from worldmodel import SYSTEM
from worldmodel import typeql as q
from worldmodel.model import WRITE
from worldmodel.semantics import Status


@pytest.fixture
def depot(wm):
    w = wm.create_world("actual", id="actual")
    for kind, name in (("physical-object", "box"), ("place", "shelf-3"), ("place", "dock"), ("physical-object", "A"),
                       ("physical-object", "B"), ("social-object", "lead"), ("physical-object", "person-b"),
                       ("social-object", "acme"), ("social-role", "site-manager"), ("place", "depot-7")):
        wm.add_entity(kind, name, id=name)
    return w


def test_one_proposition_many_attestations_corroborate(wm, depot):
    a1 = wm.attest(depot, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_superseded=True)
    a2 = wm.attest(depot, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:05"), until_superseded=True,
                   attester="A")
    assert wm.count("located-at") == 1 and wm.count("attestation") == 2
    ans = wm.value_at(depot, "located-at", "box", T("10:30"))
    assert (ans.status, ans.values, ans.support, ans.alternatives) == (Status.ASSERTED, ("shelf-3",), (a1,), (a2,))
    wm.accept(a2)
    ans = wm.value_at(depot, "located-at", "box", T("10:30"))
    assert ans.support == tuple(sorted((a1, a2)))                                  # corroborated
    assert {e["attester"] for e in ans.evidence} == {SYSTEM, "A"}                  # evidence is returned


def test_explicit_denial_shares_the_content_and_is_disputed_only_when_accepted(wm, depot):
    roles = {"classified": "person-b", "class": "site-manager", "context": "depot-7"}
    claim = wm.attest(depot, "classified-as", roles, start=T("09:00"), until_superseded=True, attester="A")
    denial = wm.deny(depot, "classified-as", roles, start=T("09:00"), until_superseded=True, attester="B")
    assert wm.count("classified-as") == 1                                           # one content, two stances
    sys_view = wm.holds(depot, "classified-as", roles, T("10:00"))
    assert sys_view.status == Status.UNKNOWN and set(sys_view.alternatives) == {claim, denial}
    assert wm.holds(depot, "classified-as", roles, T("10:00"), perspective="A").holds is True
    assert wm.holds(depot, "classified-as", roles, T("10:00"), perspective="B").holds is False
    wm.accept(claim)
    wm.accept(denial)
    assert wm.holds(depot, "classified-as", roles, T("10:00")).status == Status.DISPUTED


def test_perspectives_accept_differently_and_neither_is_truth(wm, depot):
    roles = {"classified": "person-b", "class": "site-manager", "context": "depot-7"}
    claim = wm.attest(depot, "classified-as", roles, start=T("09:00"), until_superseded=True, attester="A")
    wm.deny(depot, "classified-as", roles, start=T("09:00"), until_superseded=True, attester="B")
    wm.accept(claim, holder=SYSTEM)
    wm.accept(claim, "rejected", holder="lead", reason="B knows better")
    assert wm.holds(depot, "classified-as", roles, T("10:00")).holds is True
    assert wm.holds(depot, "classified-as", roles, T("10:00"), perspective="lead").status == Status.UNKNOWN


def test_stipulation_only_in_hypothetical_or_simulated_worlds(wm, depot):
    with pytest.raises(ValueError):
        wm.attest(depot, "located-at", {"located": "box", "place": "dock"}, stance="stipulates")
    h = wm.create_world("plan", kind="hypothetical", base=depot, branch_at=T("12:00"))
    s = wm.attest(h, "located-at", {"located": "box", "place": "dock"}, start=T("12:30"), until_superseded=True)
    ans = wm.value_at(h, "located-at", "box", T("13:00"))
    assert (ans.status, ans.values, ans.support) == (Status.STIPULATED, ("dock",), (s,))
    assert wm.value_at(depot, "located-at", "box", T("13:00")).status == Status.NOT_YET_KNOWN


def test_end_supersedes_and_history_keeps_both(wm, depot):
    a = wm.attest(depot, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_superseded=True)
    before = wm.clock.now
    b = wm.end(depot, a, T("10:10"))
    assert wm.value_at(depot, "located-at", "box", T("10:20"), as_of=before).values == ("shelf-3",)
    assert wm.value_at(depot, "located-at", "box", T("10:20")).status == Status.UNKNOWN
    assert wm.holds(depot, "located-at", {"located": "box", "place": "shelf-3"}, T("10:20")).holds is False
    hist = wm.history(depot, "box")
    assert [(h["attestation"], h["superseded"]) for h in hist] == [(a, True), (b, False)]


def test_typedb_rejects_an_attestation_without_a_world(wm, depot):
    key = wm.proposition("located-at", {"located": "box", "place": "dock"})
    with pytest.raises(TypeDBDriverException):
        with wm.driver.transaction(wm.database, WRITE) as tx:
            q.run(tx, """match $c isa located-at, has proposition-key == $k; $s isa social-object, has wm-id "system";
                insert attestation (attester: $s, content: $c), has wm-id "x", has stance "asserts", has polarity true,
                has basis "testimony", has end-basis "unknown";""", {"k": key})
            tx.commit()


def test_world_snapshots_and_knowledge_time(wm, depot):
    a = wm.attest(depot, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_superseded=True)
    h = wm.create_world("plan", kind="hypothetical", base=depot, branch_at=T("12:00"))
    wm.accept(a, "rejected")                                                     # a later correction in the base
    wm.attest(depot, "located-at", {"located": "box", "place": "dock"}, start=T("10:00"), until_superseded=True)
    assert wm.value_at(depot, "located-at", "box", T("10:30")).values == ("dock",)
    assert wm.value_at(h, "located-at", "box", T("10:30")).values == ("shelf-3",)  # snapshot at branching


def test_evidence_shows_basis_and_stance(wm, depot):
    wm.attest(depot, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_superseded=True,
              basis="observation", credence=0.9)
    (e,) = wm.value_at(depot, "located-at", "box", T("10:30")).evidence
    assert (e["basis"], e["stance"], e["polarity"], e["attester"]) == ("observation", "asserts", True, SYSTEM)
