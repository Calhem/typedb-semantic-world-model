"""Increment B (LABS-1.038): the canonical per-content judgement (DI-1, DI-11, DI-5).

One record per content and context, read by every core and profile reader:
- DI-1: content disputed by polarity is listed by every listing reader, marked DISPUTED, citing both sides;
- DI-11: a single-value conflict (a declared slot, or an established attested constraint) is applied by every reader;
- DI-5: an undecided content is labelled by why it is undecided; pending counter-claims never outrank an accepted
  claim, and are listed;
- attested office exclusivity: applied only where the constraint is established, in the same world, time, knowledge
  time and perspective; office_holders' and offices_of' public answers unchanged (choice A);
- traversals follow established links only and report the others separately (choice B), with unchanged answers;
- frame chains apply the frame-transform slot (Q5);
- hypothetical-world inheritance, perspectives and knowledge time; selective and full load agree.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel, mechanical as m, organisation as o
from worldmodel.judgement import (END_UNKNOWN, NOT_YET_EFFECTIVE, Judgement, claim_label, holding_label)
from worldmodel.semantics import Status

pytestmark = pytest.mark.own_profiles


def T(d, h=9):
    return datetime(2026, 11, d, h, tzinfo=timezone.utc)


@pytest.fixture
def wm(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    model = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    try:
        for p in ("mechanical", "organisation"):
            model.install_profile(p)
        yield model
    finally:
        driver.databases.get(name).delete()


def entities(wm, kind, *ids):
    for i in ids:
        wm.add_entity(kind, i, id=i)


def disputed_part(wm, w, part, whole):
    """part-of(part, whole) asserted by the system and denied by an auditor whose denial the system accepts."""
    a = wm.attest(w, "part-of", {"part": part, "whole": whole}, start=T(1), until_superseded=True)
    d = wm.attest(w, "part-of", {"part": part, "whole": whole}, polarity=False, start=T(1), until_superseded=True,
                  attester="auditor")
    wm.accept(d)
    return a, d


@pytest.fixture
def shop(wm):
    w = wm.create_world("w", id="w")
    entities(wm, "physical-object", "gearbox", "housing", "shaft", "cover", "bolt", "auditor", "ana", "box")
    wm.attest(w, "part-of", {"part": "housing", "whole": "gearbox"}, start=T(1), until_superseded=True)
    wm.attest(w, "part-of", {"part": "bolt", "whole": "shaft"}, start=T(1), until_superseded=True)
    ids = disputed_part(wm, w, "shaft", "gearbox")
    return w, ids


# ---- DI-1: polarity-disputed content is listed ------------------------------------------------------------------------------
def test_facts_about_lists_a_polarity_dispute_citing_both_sides(wm, shop):
    w, (a, d) = shop
    facts = {f["roles"]["part"][0]: f for f in wm.facts_about(w, "gearbox", T(5)) if f["type"] == "part-of"}
    assert facts["housing"]["judgement"] == "established" and facts["housing"]["status"] == Status.ASSERTED
    f = facts["shaft"]
    assert (f["judgement"], f["status"]) == ("disputed", Status.DISPUTED)
    assert f["assertions"] == [a] and f["denials"] == [d] and sorted(f["support"]) == sorted([a, d])
    assert wm.holds(w, "part-of", {"part": "shaft", "whole": "gearbox"}, T(5)).status == Status.DISPUTED


def test_a_dispute_is_listed_only_while_it_is_one(wm, shop):
    w, (a, d) = shop
    assert [f["judgement"] for f in wm.facts_about(w, "shaft", T(5)) if f["type"] == "part-of"
            and "gearbox" in f["roles"]["whole"]] == ["disputed"]
    # the auditor's own perspective accepts only its denial: no dispute, and nothing listed for the content
    assert not [f for f in wm.facts_about(w, "shaft", T(5), perspective="auditor") if "gearbox" in f["roles"].get("whole", [])]
    # before the auditor's denial was accepted (knowledge time), the plain answer stands
    early = next(h["recorded_at"] for h in wm.history(w, "shaft") if h["attestation"] == d)   # before its acceptance
    plain = [f for f in wm.facts_about(w, "shaft", T(5), as_of=early) if "gearbox" in f["roles"].get("whole", [])]
    assert [(f["judgement"], f["status"]) for f in plain] == [("established", Status.ASSERTED)]


def test_closures_keep_their_answer_and_report_what_they_did_not_follow(wm, shop):
    w, (a, d) = shop
    assert wm.parts(w, "gearbox", T(5)) == ["housing"]                  # unchanged: established links only
    r = wm.parts(w, "gearbox", T(5), report=True)
    assert r["reached"] == ["housing"]
    (link,) = r["not_traversed"]
    assert (link["whole"], link["part"], link["judgement"], link["status"]) == ("gearbox", ["shaft"], "disputed",
                                                                               Status.DISPUTED)
    assert sorted(link["support"]) == sorted([a, d])
    # a pending link (only an unreviewed claim) is blocked, and listed as such
    wm.attest(w, "part-of", {"part": "cover", "whole": "housing"}, start=T(1), until_superseded=True, attester="ana")
    r = wm.parts(w, "gearbox", T(5), report=True)
    assert r["reached"] == ["housing"]
    assert {(x["part"][0], x["judgement"]) for x in r["not_traversed"]} == {("shaft", "disputed"), ("cover", "pending")}


def test_composition_contents_and_process_steps(wm, shop):
    w, _ = shop
    tree = wm.composition(w, "gearbox", T(5))
    assert [p["id"] for p in tree["parts"]] == ["housing"]               # the established tree is unchanged
    assert [(x["id"], x["judgement"]) for x in tree["not_traversed"]] == [("shaft", "disputed")]
    entities(wm, "occurrence", "repair", "step-1", "step-2")
    wm.attest(w, "part-of", {"part": "step-1", "whole": "repair"}, start=T(1), until_superseded=True)
    disputed_part(wm, w, "step-2", "repair")
    steps = {s["occurrence"]: s for s in wm.process_steps(w, "repair", T(5))}
    assert (steps["step-1"]["judgement"], steps["step-1"]["status"]) == ("established", Status.ASSERTED)
    assert (steps["step-2"]["judgement"], steps["step-2"]["status"]) == ("disputed", Status.DISPUTED)


def test_materials_keeps_its_answer_and_reports_a_disputed_one(wm):
    w = wm.create_world("w", id="w")
    entities(wm, "physical-object", "cover", "auditor")
    entities(wm, "category", "material", "steel", "aluminium")
    for c in ("steel", "aluminium"):
        wm.attest(w, "classified-as", {"classified": c, "class": "material"}, until_superseded=True)
    wm.attest(w, "classified-as", {"classified": "cover", "class": "steel"}, start=T(1), until_superseded=True)
    wm.attest(w, "classified-as", {"classified": "cover", "class": "aluminium"}, start=T(1), until_superseded=True)
    wm.accept(wm.attest(w, "classified-as", {"classified": "cover", "class": "aluminium"}, polarity=False, start=T(1),
                        until_superseded=True, attester="auditor"))
    assert wm.materials(w, "cover", T(5)) == ["steel"]
    r = wm.materials(w, "cover", T(5), report=True)
    assert r["materials"] == ["steel"] and [x["material"] for x in r["disputed"]] == ["aluminium"]


def test_roles_of_lists_a_disputed_role(wm):
    w = wm.create_world("w", id="w")
    entities(wm, "person", "bea")
    entities(wm, "physical-object", "auditor")
    entities(wm, "social-role", "analyst")
    wm.grant(w, "bea", "analyst", start=T(1))
    wm.accept(wm.grant(w, "bea", "analyst", polarity=False, start=T(1), attester="auditor"))
    (r,) = wm.roles_of(w, "bea", T(5))
    assert (r["role"], r["status"]) == ("analyst", Status.DISPUTED)
    assert wm.capable(w, "bea", "analyst", T(5))["judgement"] == "disputed"


# ---- DI-11: single-value conflicts in every reader ---------------------------------------------------------------------
def test_a_declared_slot_on_a_profile_type_is_applied_by_its_report(wm):
    w = wm.create_world("w", id="w")
    entities(wm, "physical-object", "cover", "housing", "inspector")
    entities(wm, "category", "bolted", "bonded")
    wm.declare_slot("connected-to", ("endpoint",), "joint-kind")
    a = m.connect(wm, w, "cover", "housing", joint_kind="bolted", start=T(1))
    b = m.connect(wm, w, "cover", "housing", joint_kind="bonded", start=T(1), attester="inspector")
    wm.accept(b)
    conns = m.connections(wm, w, "cover", T(5))
    assert [c["status"] for c in conns] == [Status.DISPUTED, Status.DISPUTED]       # was ASSERTED, ASSERTED (DI-11)
    rec = next(r for r in wm._contents(w, "cover", ("connected-to",), T(5)) if "bolted" in r.stated_roles["joint-kind"])
    assert rec.judgement is Judgement.DISPUTED and rec.conflict_ids == [b] and rec.support_status == Status.ASSERTED
    assert wm.holds(w, "connected-to", {"endpoint": ["cover", "housing"], "joint-kind": "bolted"}, T(5)).status \
        == Status.DISPUTED
    assert a in rec.support_ids


# ---- DI-5: why an undecided content is undecided ---------------------------------------------------------------------------
@pytest.fixture
def labels(wm):
    w = wm.create_world("w", id="w")
    entities(wm, "person", "cal", "dan", "eve", "fay", "gus")
    entities(wm, "physical-object", "auditor")
    entities(wm, "capability", "can-sign")
    wm.grant(w, "cal", "can-sign", start=T(8))                                     # accepted, from day 8
    deny = wm.grant(w, "cal", "can-sign", polarity=False, start=T(1), attester="auditor")   # unreviewed counter-claim
    wm.grant(w, "dan", "can-sign", start=T(8))                                     # accepted, from day 8, alone
    wm.attest(w, "classified-as", {"classified": "eve", "class": "can-sign"}, start=T(1))   # begun, end unknown
    wm.grant(w, "fay", "can-sign", start=T(1), attester="auditor")                 # only an unreviewed claim
    wm.accept(wm.grant(w, "gus", "can-sign", start=T(1), attester="auditor"), verdict="rejected")   # only rejected
    return w, deny


def record(wm, w, who):
    (r,) = [r for r in wm._contents(w, who, ("classified-as",), T(5)) if who in r.stated_roles["classified"]]
    return r


def test_each_undecided_reason_has_its_label(wm, labels):
    w, deny = labels
    cal, dan, eve, fay, gus = (record(wm, w, x) for x in ("cal", "dan", "eve", "fay", "gus"))
    assert (cal.judgement, cal.reasons, cal.pending) == (Judgement.UNKNOWN, (NOT_YET_EFFECTIVE,), (deny,))
    assert claim_label(cal) == claim_label(dan) == "not yet effective"            # was "unreviewed" for cal (DI-5)
    assert (eve.judgement, eve.reasons, claim_label(eve)) == (Judgement.UNKNOWN, (END_UNKNOWN,), "not established")
    assert (fay.judgement, claim_label(fay)) == (Judgement.PENDING, "unreviewed")
    assert claim_label(gus) == holding_label(gus) == "rejected"
    for who, want in (("cal", "not yet effective"), ("dan", "not yet effective"), ("eve", "not established"),
                      ("fay", "not established"), ("gus", "not established")):
        c = wm.capable(w, who, "can-sign", T(5))
        assert (c["judgement"], c["holds"]) == (want, None), who
    assert wm.holds(w, "classified-as", {"classified": "eve", "class": "can-sign"}, T(5)).status == Status.UNKNOWN


def test_a_pending_counter_claim_never_outranks_but_is_listed(wm, labels):
    w, deny = labels
    assert wm.holds(w, "classified-as", {"classified": "cal", "class": "can-sign"}, T(5)).alternatives == (deny,)
    assert record(wm, w, "cal").pending == (deny,)
    after = [r for r in wm._contents(w, "cal", ("classified-as",), T(9))][0]
    assert after.judgement is Judgement.ESTABLISHED and after.pending == (deny,)   # still pending, still not deciding


# ---- attested office exclusivity -------------------------------------------------------------------------------------------
@pytest.fixture
def offices(wm):
    w = wm.create_world("w", id="w")
    entities(wm, "person", "bea", "cal")
    entities(wm, "organisation", "acme", "depot-7", "depot-9", "auditor")
    entities(wm, "social-role", "site-manager")
    apps = {}
    for who, ctx in (("bea", "depot-7"), ("cal", "depot-7"), ("bea", "depot-9"), ("cal", "depot-9")):
        apps[who, ctx] = o.appoint(wm, w, who, "site-manager", ctx, start=T(1), attester="acme")
        wm.accept(apps[who, ctx])
    c = o.declare_exclusive(wm, w, "site-manager", "depot-7", start=T(3), attester="acme")   # recorded last
    wm.accept(c)
    return w, c, apps


def test_exclusivity_applies_where_established_and_reports_keep_their_answers(wm, offices):
    w, c, apps = offices
    v = o.office_holders(wm, w, "site-manager", "depot-7", T(5))
    assert v["holders"] == ["bea", "cal"] and v["status"] == Status.DISPUTED and v["conflict"] is not None
    assert {a["judgement"] for a in v["appointments"]} == {"established"}            # unchanged (choice A)
    (mine,) = [e for e in o.offices_of(wm, w, "bea", T(5)) if e["context"] == "depot-7"]
    assert (mine["judgement"], mine["status"]) == ("established", Status.DISPUTED) and mine["conflict"]
    # the same judgement in every core reader (DI-11): holds, facts_about, capable
    assert wm.holds(w, "office-holding", {"classified": "bea", "class": "site-manager", "context": "depot-7"},
                    T(5)).status == Status.DISPUTED
    f = [f for f in wm.facts_about(w, "bea", T(5)) if f["type"] == "office-holding" and "depot-7" in f["roles"]["context"]]
    assert [x["status"] for x in f] == [Status.DISPUTED] and f[0]["conflicts"]
    assert wm.capable(w, "bea", "site-manager", T(5), context="depot-7")["judgement"] == "disputed"
    # another context has no constraint: two holders are compatible
    assert o.office_holders(wm, w, "site-manager", "depot-9", T(5))["status"] == Status.ASSERTED
    assert wm.capable(w, "bea", "site-manager", T(5), context="depot-9")["judgement"] == "established"


def test_exclusivity_does_not_apply_before_it_starts_or_before_it_is_known(wm, offices):
    w, c, apps = offices
    assert wm.holds(w, "office-holding", {"classified": "bea", "class": "site-manager", "context": "depot-7"},
                    T(2)).status == Status.ASSERTED                                   # the constraint starts on day 3
    rec = next(h["recorded_at"] for h in wm.history(w, "depot-7") if h["attestation"] == c)
    before = rec - timedelta(microseconds=1)                 # every appointment known and accepted, the constraint not
    v = o.office_holders(wm, w, "site-manager", "depot-7", T(5), as_of=before)
    assert v["holders"] == ["bea", "cal"] and v["conflict"] is None and v["status"] == Status.ASSERTED
    assert o.office_holders(wm, w, "site-manager", "depot-7", T(5))["conflict"] is not None


def test_an_unestablished_or_disputed_constraint_never_disputes_compatible_holdings(wm, offices):
    w, c, apps = offices
    # the auditor's perspective accepts the appointments but not the constraint (acme's claim): it does not apply
    for who in ("bea", "cal"):
        wm.accept(apps[who, "depot-7"], holder="auditor")
    assert wm.holds(w, "office-holding", {"classified": "bea", "class": "site-manager", "context": "depot-7"}, T(5),
                    perspective="auditor").status == Status.ASSERTED
    # a disputed constraint (the system accepts the auditor's denial of it) does not apply either
    wm.accept(wm.attest(w, "exclusive-office", {"office": "site-manager", "context": "depot-7"}, polarity=False,
                        start=T(3), until_superseded=True, attester="auditor"))
    assert wm.holds(w, "exclusive-office", {"office": "site-manager", "context": "depot-7"}, T(5)).status \
        == Status.DISPUTED
    v = o.office_holders(wm, w, "site-manager", "depot-7", T(5))
    assert v["conflict"] is None and v["status"] == Status.ASSERTED
    assert wm.holds(w, "office-holding", {"classified": "bea", "class": "site-manager", "context": "depot-7"},
                    T(5)).status == Status.ASSERTED


def test_an_attested_constraint_is_judged_once_and_not_recursively(wm, offices, monkeypatch):
    w, c, apps = offices
    calls, depth = [], {"now": 0, "max": 0}
    original = WorldModel._records

    def spy(self, atts, *a, attested=True, **k):
        depth["now"] += 1
        depth["max"] = max(depth["max"], depth["now"])
        calls.append(({x.ctype for x in atts}, attested, depth["now"]))
        try:
            return original(self, atts, *a, attested=attested, **k)
        finally:
            depth["now"] -= 1
    monkeypatch.setattr(WorldModel, "_records", spy)
    o.office_holders(wm, w, "site-manager", "depot-7", T(5))
    # the report evaluates the constraint once (one load, shared by its rivals check and the appointments'
    # judgement), without attested constraints of its own; the separate `exclusive` field is the constraint's own
    # holds(). Nothing nests deeper than one constraint level: no recursion
    shared = [att for types, att, d in calls if types == {"exclusive-office"} and att is False]
    assert shared == [False]
    assert depth["max"] <= 2 and all(not att for types, att, d in calls if d == 2)


# ---- worlds, frames, consistency ---------------------------------------------------------------------------------------------
def test_hypothetical_worlds_inherit_and_override(wm, shop):
    w, (a, d) = shop
    plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(4), id="plan")
    pick = lambda world: [f["judgement"] for f in wm.facts_about(world, "shaft", T(5)) if "gearbox" in f["roles"].get("whole", [])]
    assert pick(plan) == ["disputed"]                                              # inherited dispute
    wm.attest(plan, "part-of", {"part": "shaft", "whole": "gearbox"}, start=T(4), until_superseded=True)
    assert pick(plan) == ["established"] and pick(w) == ["disputed"]               # the plan's own claim decides
    assert wm.parts(plan, "gearbox", T(5)) == ["bolt", "housing", "shaft"] and wm.parts(w, "gearbox", T(5)) == ["housing"]


def test_two_different_transforms_for_one_frame_pair_are_disputed(wm):
    w = wm.create_world("w", id="w")
    entities(wm, "spatial-frame", "f1", "f2")
    entities(wm, "physical-object", "surveyor")
    wm.relate_frames(w, "f1", "f2", (1.0, 0.0, 0.0), start=T(1), until_superseded=True)
    assert wm.transform_between(w, "f2", "f1", T(5))["status"] == Status.INFERRED
    wm.accept(wm.relate_frames(w, "f1", "f2", (2.0, 0.0, 0.0), start=T(1), until_superseded=True, attester="surveyor"))
    assert wm.transform_between(w, "f2", "f1", T(5))["status"] == Status.DISPUTED     # Q5


@pytest.mark.parametrize("selective", [True, False], ids=["selective", "full-load"])
def test_every_reader_gives_the_same_judgement(wm, offices, selective):
    w, c, apps = offices
    wm.selective = selective
    disputed_part(wm, w, "bea", "acme")                       # a polarity dispute among the same subject's facts
    t = T(5)
    for f in wm.facts_about(w, "bea", t):
        rec = wm.judgement(w, f["type"], f["roles"], t)
        assert rec.status == f["status"] and rec.judgement.value == f["judgement"]
        assert wm.holds(w, f["type"], f["roles"], t).status == f["status"]
        mine = [r for r in wm._contents(w, "bea", (f["type"],), t) if r.roles == f["roles"]]
        assert [r.status for r in mine] == [f["status"]]
