"""DI-19 (LABS-1.060): `Answer.constraint_support`, the attested constraint behind a constraint dispute.

holds() on a content disputed under an applied attested constraint (two holders of an exclusive office) cites the
constraint: its type, key players, constrained value role and the attestations deciding the constraint's own
judgement. The field is additive: every other field of every answer is what it was without it. It is empty where
no attested constraint applies:
- an established constraint with one holder, or a context without a constraint;
- an unaccepted, disputed, not yet effective, not yet known, ended or other-perspective constraint;
- declared functional slots (schema data, never cited as attestations), in holds(), value_at() and value_of().
Superseded constraints cite their successor; inherited worlds cite the base world's constraint.
"""

import dataclasses
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel, organisation as o
from worldmodel.semantics import Status

pytestmark = pytest.mark.own_profiles
OFFICE = {"class": "site-manager", "context": "depot-7"}
KEY = {"office": ("site-manager",), "context": ("depot-7",)}


def T(d, h=9):
    return datetime(2026, 11, d, h, tzinfo=timezone.utc)


def entities(wm, kind, *ids):
    for i in ids:
        wm.add_entity(kind, i, id=i)


@pytest.fixture
def wm(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    model = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    try:
        model.install_profile("organisation")
        yield model
    finally:
        driver.databases.get(name).delete()


@pytest.fixture
def offices(wm):
    w = wm.create_world("w", id="w")
    entities(wm, "person", "bea", "cal", "dee")
    entities(wm, "organisation", "acme", "depot-7", "depot-9", "auditor", "lead")
    entities(wm, "social-role", "site-manager")
    apps = {}
    for who, ctx in (("bea", "depot-7"), ("cal", "depot-7"), ("bea", "depot-9"), ("cal", "depot-9")):
        apps[who, ctx] = o.appoint(wm, w, who, "site-manager", ctx, start=T(1), attester="acme")
        wm.accept(apps[who, ctx])
    c = o.declare_exclusive(wm, w, "site-manager", "depot-7", start=T(3), attester="acme")
    wm.accept(c)
    return w, c, apps


def holds(wm, w, who, t, ctx="depot-7", **kw):
    return wm.holds(w, "office-holding", {"classified": who, **OFFICE, "context": ctx}, t, **kw)


def without_field(wm, monkeypatch, f):
    """f() with constraint_support disabled: the answer as before DI-19."""
    with monkeypatch.context() as m:
        m.setattr(WorldModel, "_constraint_support", staticmethod(lambda rec: ()))
        return f()


# ---- established constraint ----------------------------------------------------------------------------------------------
def test_a_constraint_dispute_cites_the_constraint(wm, offices):
    w, c, apps = offices
    a = holds(wm, w, "bea", T(5))
    assert a.status is Status.DISPUTED and a.support == (apps["bea", "depot-7"],)
    assert a.conflicts == (apps["cal", "depot-7"],)
    (entry,) = a.constraint_support
    assert entry["constraint"] == "exclusive-office" and entry["key"] == KEY and entry["value_role"] == "classified"
    assert entry["support"] == (c,)
    # the constraint's evidence is its own holds() evidence; it is not added to the content's `evidence`
    own = wm.holds(w, "exclusive-office", {"office": "site-manager", "context": "depot-7"}, T(5))
    assert entry["evidence"] == own.evidence and own.support == (c,)
    assert c not in {e["attestation"] for e in a.evidence}
    # the same constraint support as office_holders' conflict (the canonical judgement's)
    v = o.office_holders(wm, w, "site-manager", "depot-7", T(5))
    assert list(entry["support"]) == v["conflict"]["constraint"]["support"]
    # both holders cite it
    assert holds(wm, w, "cal", T(5)).constraint_support == a.constraint_support


def test_every_other_field_is_unchanged(wm, offices, monkeypatch):
    w, c, apps = offices
    cases = [lambda who=who, ctx=ctx, t=t: holds(wm, w, who, t, ctx)
             for who in ("bea", "cal", "dee") for ctx in ("depot-7", "depot-9") for t in (T(2), T(5))]
    for f in cases:
        new, old = f(), without_field(wm, monkeypatch, f)
        assert dataclasses.replace(new, constraint_support=()) == old


def test_no_entry_without_a_conflict_or_without_a_constraint(wm, offices):
    w, c, apps = offices
    assert holds(wm, w, "bea", T(5), "depot-9").constraint_support == ()         # no constraint in depot-9
    assert holds(wm, w, "bea", T(5), "depot-9").status is Status.ASSERTED
    wm.accept(apps["cal", "depot-7"], "rejected")                                  # one holder left
    a = holds(wm, w, "bea", T(5))
    assert (a.status, a.constraint_support) == (Status.ASSERTED, ())
    assert holds(wm, w, "dee", T(5)).constraint_support == ()                     # no appointment at all


def test_several_accepted_constraint_attestations_are_all_cited(wm, offices):
    w, c, apps = offices
    c2 = o.declare_exclusive(wm, w, "site-manager", "depot-7", start=T(2), attester="lead")
    wm.accept(c2)
    (entry,) = holds(wm, w, "bea", T(5)).constraint_support
    assert entry["support"] == tuple(sorted((c, c2)))
    assert entry["support"] == wm.holds(w, "exclusive-office", {"office": "site-manager", "context": "depot-7"},
                                        T(5)).support


# ---- not applied: disputed, unaccepted, perspective-dependent ------------------------------------------------------------------
def test_a_disputed_constraint_is_not_applied_and_not_cited(wm, offices):
    w, c, apps = offices
    wm.accept(wm.attest(w, "exclusive-office", {"office": "site-manager", "context": "depot-7"}, polarity=False,
                        start=T(3), until_superseded=True, attester="auditor"))
    assert wm.holds(w, "exclusive-office", {"office": "site-manager", "context": "depot-7"}, T(5)).status \
        is Status.DISPUTED
    a = holds(wm, w, "bea", T(5))
    assert (a.status, a.constraint_support) == (Status.ASSERTED, ())


def test_an_unaccepted_constraint_is_not_cited(wm, offices):
    w, c, apps = offices
    wm.accept(c, "rejected")
    a = holds(wm, w, "bea", T(5))
    assert (a.status, a.constraint_support) == (Status.ASSERTED, ())


def test_constraint_support_follows_the_perspective(wm, offices):
    w, c, apps = offices
    for who in ("bea", "cal"):
        wm.accept(apps[who, "depot-7"], holder="auditor")
        wm.accept(apps[who, "depot-7"], holder="lead")
    wm.accept(c, holder="lead")                       # lead accepts the constraint, the auditor does not
    assert holds(wm, w, "bea", T(5), perspective="auditor").constraint_support == ()
    (entry,) = holds(wm, w, "bea", T(5), perspective="lead").constraint_support
    assert entry["support"] == (c,)
    wm.accept(c, "rejected", holder="lead")           # a later rejection by lead withdraws it for lead only
    assert holds(wm, w, "bea", T(5), perspective="lead").constraint_support == ()
    assert holds(wm, w, "bea", T(5)).constraint_support[0]["support"] == (c,)


# ---- temporal visibility ------------------------------------------------------------------------------------------------------
def test_valid_time_and_knowledge_time(wm, offices):
    w, c, apps = offices
    assert holds(wm, w, "bea", T(2)).constraint_support == ()                    # the constraint starts on day 3
    assert holds(wm, w, "bea", T(3)).constraint_support[0]["support"] == (c,)
    rec = next(h["recorded_at"] for h in wm.history(w, "depot-7") if h["attestation"] == c)
    before = rec - timedelta(microseconds=1)
    a = holds(wm, w, "bea", T(5), as_of=before)                                   # not yet known
    assert (a.status, a.constraint_support) == (Status.ASSERTED, ())
    assert holds(wm, w, "bea", T(5), as_of=rec + timedelta(days=1)).constraint_support[0]["support"] == (c,)


def test_an_ended_constraint_is_cited_only_while_it_holds(wm, offices):
    w, c, apps = offices
    e = wm.end(w, c, T(6))            # a bounded attestation by the same attester, superseding c
    wm.accept(e)
    own = wm.holds(w, "exclusive-office", {"office": "site-manager", "context": "depot-7"}, T(5))
    assert own.support == (e,) and holds(wm, w, "bea", T(5)).constraint_support[0]["support"] == (e,)
    a = holds(wm, w, "bea", T(7))
    assert (a.status, a.constraint_support) == (Status.ASSERTED, ())


def test_a_superseded_constraint_cites_its_successor(wm, offices):
    w, c, apps = offices
    c2 = wm.attest(w, "exclusive-office", {"office": "site-manager", "context": "depot-7"}, start=T(4),
                   until_superseded=True, attester="acme", supersedes=c)
    rec2 = next(h["recorded_at"] for h in wm.history(w, "depot-7") if h["attestation"] == c2)
    wm.accept(c2)
    (entry,) = holds(wm, w, "bea", T(5)).constraint_support
    assert entry["support"] == (c2,)
    assert holds(wm, w, "bea", T(5), as_of=rec2 - timedelta(microseconds=1)).constraint_support[0]["support"] == (c,)
    assert holds(wm, w, "bea", T(3)).constraint_support == ()                     # the successor starts on day 4


# ---- worlds ---------------------------------------------------------------------------------------------------------------------
def test_an_inherited_constraint_is_cited_in_a_variant_world(wm, offices):
    w, c, apps = offices
    plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(10))
    (entry,) = holds(wm, plan, "bea", T(5)).constraint_support
    assert entry["support"] == (c,)
    early = wm.create_world("early", kind="hypothetical", base=w, branch_at=T(2))   # branched before it starts
    assert holds(wm, early, "bea", T(5)).constraint_support == ()


def test_selective_and_full_load_agree(wm, offices):
    w, c, apps = offices
    calls = [(who, t, kw) for who in ("bea", "cal") for t in (T(2), T(5)) for kw in ({}, {"perspective": "auditor"})]
    wm.selective = True
    sel = [holds(wm, w, who, t, **kw) for who, t, kw in calls]
    wm.selective = False
    try:
        full = [holds(wm, w, who, t, **kw) for who, t, kw in calls]
    finally:
        wm.selective = True
    assert sel == full and any(a.constraint_support for a in sel)


def test_only_applied_attested_constraints_are_cited(wm, offices):
    # holds() loads rival holders only where the constraint is established, so its records never carry a
    # non-applying attested constraint; the rule is checked directly on a record that carries one of each kind
    from worldmodel.judgement import Constraint
    w, c, apps = offices
    rec = wm.judgement(w, "office-holding", {"classified": "bea", **OFFICE}, T(5))
    (applied,) = [x for x in rec.constraints if x.kind == "attested"]
    assert applied.applies and WorldModel._constraint_support(rec)[0]["support"] == (c,)
    wm.accept(wm.attest(w, "exclusive-office", {"office": "site-manager", "context": "depot-7"}, polarity=False,
                        start=T(3), until_superseded=True, attester="auditor"))
    disputed = wm.judgement(w, "exclusive-office", {"office": "site-manager", "context": "depot-7"}, T(5))
    assert disputed.support                                       # it has deciding attestations, but does not apply
    others = (dataclasses.replace(applied, applies=False, judgement=disputed),
              Constraint("declared", "located-at", ("located",), "place", (("box",),), rivals=applied.rivals))
    assert WorldModel._constraint_support(dataclasses.replace(rec, constraints=others)) == ()


# ---- declared functional slots: never cited -----------------------------------------------------------------------------------
@pytest.fixture
def two_places(wm):
    w = wm.create_world("w", id="w")
    entities(wm, "physical-object", "box")
    entities(wm, "place", "shelf-3", "shelf-4")
    for p in ("shelf-3", "shelf-4"):
        wm.accept(wm.attest(w, "located-at", {"located": "box", "place": p}, start=T(1), until_superseded=True))
    return w


def test_a_declared_slot_dispute_cites_no_constraint_attestation(wm, two_places, monkeypatch):
    w = two_places
    h = wm.holds(w, "located-at", {"located": "box", "place": "shelf-3"}, T(5))
    assert h.status is Status.DISPUTED and h.conflicts and h.constraint_support == ()
    va = wm.value_at(w, "located-at", "box", T(5))
    vo = wm.value_of(w, "located-at", {"located": "box"}, T(5))
    assert va.status is Status.DISPUTED and va.values == ("shelf-3", "shelf-4")
    assert va.constraint_support == () and vo.constraint_support == () and vo == va
    for f in (lambda: wm.holds(w, "located-at", {"located": "box", "place": "shelf-3"}, T(5)),
              lambda: wm.value_at(w, "located-at", "box", T(5))):
        assert f() == without_field(wm, monkeypatch, f)


def test_value_readers_never_apply_attested_constraints(wm, offices):
    w, c, apps = offices
    # office-holding has no declared slot, so value_at/value_of refuse it, as before: they cannot project the
    # exclusive-office judgement, and their answers never carry constraint_support
    with pytest.raises(ValueError):
        wm.value_at(w, "office-holding", "bea", T(5))
    with pytest.raises(ValueError):
        wm.value_of(w, "office-holding", {"classified": "bea"}, T(5))
