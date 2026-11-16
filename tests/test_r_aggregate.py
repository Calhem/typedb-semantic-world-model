"""Increment C (DI-6; LABS-1.039 design, LABS-1.040 approval): canonical aggregation of judgements.

The executed examples of docs/core-0.4/pre-e-increment-c-design.md (E1 to E10, E7b; probes/pre_e_c_examples.py) as
permanent tests, plus the approval's additional cases:
- rule Q (`capable`, `authorised`, `calibration_status`): conflict first; otherwise the core rule over the union of
  the deciding claims of the established (or, when it does not hold, the denied and expired) holdings, listed in
  `support`; independent of identifiers, insertion order and query-result order; each claim counted once;
- rule C (`office_holders`): no collection-level support status when holders are established without conflict; each
  appointment keeps its own;
- `changes`: a slot's status rests on the values held, as `value_of`.
Mixed STIPULATED, ASSERTED and INFERRED support, explicit denials, expired holdings, pending and unreviewed claims, an
unknown end (never an expiry), perspectives, knowledge time, hypothetical worlds and both query paths.
"""

import random
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel, laboratory as lb, organisation as org
from worldmodel.judgement import combine
from worldmodel.semantics import Status, answer_status

pytestmark = pytest.mark.own_profiles


def T(day, h=9):
    return datetime(2026, 11, day, h, tzinfo=timezone.utc)


AT = T(5)


@pytest.fixture(scope="module")
def ref(driver):
    """The design's example worlds: an actual world `w` (claims by HR, accepted by the system; the `audit`
    perspective has accepted none of them) and a plan branching from it on day 2 with its own stipulations."""
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    try:
        for p in ("mechanical", "organisation", "laboratory"):
            wm.install_profile(p)
        w = wm.create_world("actual", id="w")
        for p in ("bea", "cal", "dan", "eve", "fay", "gus", "hal", "ivy", "hr", "audit", "lab"):
            wm.add_entity("person", p, id=p)
        for i in ("balance", "box"):
            wm.add_entity("physical-object", i, id=i)
        for i in ("room-1", "room-2", "room-3"):
            wm.add_entity("place", i, id=i)
        for kind, i in (("organisation", "acme"), ("organisation", "board"), ("organisation", "depot"),
                        ("social-role", "analyst"), ("social-role", "office-x"), ("capability", "can-sign")):
            wm.add_entity(kind, i, id=i)
        for c in ("cert-1", "cert-2", "cert-3", "cert-4"):
            lb.register_certificate(wm, c, reference=c.upper(), id=c)
        ids = {}

        def hr(att):
            wm.accept(att)
            return att
        ids["dan_general"] = hr(wm.grant(w, "dan", "analyst", start=T(1), attester="hr"))
        ids["cal_depot"] = hr(wm.grant(w, "cal", "analyst", context="depot", start=T(1), attester="hr"))
        ids["eve_general"] = hr(wm.grant(w, "eve", "analyst", start=T(1), attester="hr", basis="inference"))
        ids["eve_depot"] = hr(wm.grant(w, "eve", "analyst", context="depot", start=T(1), attester="hr"))
        ids["fay_general"] = hr(wm.grant(w, "fay", "analyst", start=T(1), end=T(4), attester="hr"))
        ids["gus_general"] = hr(wm.grant(w, "gus", "analyst", start=T(1), attester="hr"))
        ids["acme_grant"] = hr(org.authorise(wm, w, "acme", "bea", "can-sign", "depot", attester="hr", start=T(1)))
        ids["bea_app"] = hr(org.appoint(wm, w, "bea", "office-x", "depot", start=T(1), attester="hr"))
        ids["cert2"] = hr(lb.calibrate(wm, w, "cert-2", "balance", start=T(1), attester="lab", basis="inference"))
        ids["cert3"] = hr(lb.calibrate(wm, w, "cert-3", "balance", start=T(1), attester="lab"))
        hr(wm.attest(w, "located-at", {"located": "box", "place": "room-1"}, start=T(1), end=T(4),
                     basis="inference", attester="hr"))
        hr(wm.attest(w, "located-at", {"located": "box", "place": "room-3"}, start=T(4), until_superseded=True,
                     basis="inference", attester="hr"))
        hr(wm.attest(w, "located-at", {"located": "box", "place": "room-2"}, polarity=False, start=T(1),
                     until_superseded=True, attester="audit"))
        hr(org.employ(wm, w, "acme", "bea", start=T(1), attester="hr"))
        # hal: an established holding beside an unreviewed one and a rejected one (undecided, never folded in)
        ids["hal_general"] = hr(wm.grant(w, "hal", "analyst", start=T(1), attester="hr"))
        ids["hal_pending"] = wm.grant(w, "hal", "analyst", context="depot", start=T(1), attester="lab",
                                      basis="inference")
        # ivy: begun, end unknown (no end and no commitment to hold until superseded): never an expiry
        ids["ivy_open"] = hr(wm.grant(w, "ivy", "analyst", start=T(1), attester="hr", until_superseded=False))
        # the same claim stated twice (two attestations of one content): each counts once
        ids["dan_general_2"] = hr(wm.grant(w, "dan", "analyst", start=T(1), attester="hr"))
        plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(2), id="plan")
        ids["known_before_plan_claims"] = wm.clock.now
        ids["dan_depot"] = wm.grant(plan, "dan", "analyst", context="depot", start=T(3))
        ids["cal_general"] = wm.grant(plan, "cal", "analyst", start=T(3))
        ids["fay_denial"] = wm.grant(plan, "fay", "analyst", context="depot", polarity=False, start=T(3))
        ids["gus_denial"] = wm.grant(plan, "gus", "analyst", context="depot", polarity=False, start=T(3))
        ids["board_grant"] = org.authorise(wm, plan, "board", "bea", "can-sign", "depot", start=T(3))
        ids["cal_app"] = org.appoint(wm, plan, "cal", "office-x", "depot", start=T(3))
        ids["cert1"] = lb.calibrate(wm, plan, "cert-1", "balance", start=T(3))
        org.employ(wm, plan, "acme", "cal", start=T(3))
        plan2 = wm.create_world("plan-2", kind="hypothetical", base=w, branch_at=T(2), id="plan-2")
        ids["cert4"] = lb.calibrate(wm, plan2, "cert-4", "balance", start=T(3))
        yield wm, ids
    finally:
        driver.databases.get(name).delete()


@pytest.fixture(params=[True, False], ids=["selective", "full-load"])
def m(ref, request):
    wm, ids = ref
    wm.selective = request.param
    yield wm, ids
    wm.selective = True


def cap(wm, world, holder, perspective="system", t=AT, **kw):
    return wm.capable(world, holder, "analyst", t, context="depot", perspective=perspective, **kw)


def rests_on_support(wm, world, answer, perspective="system"):
    """The status is the core rule over exactly the claims listed in `support` (a reader can check it)."""
    vis = wm.visible(world, perspective=perspective)
    assert answer["support"] == sorted(set(answer["support"]))
    return answer_status([vis[i] for i in answer["support"]]) == answer["status"]


# ---- rule Q: capable ------------------------------------------------------------------------------------------------
def test_e1_mirror_cases_agree(m):
    """General ASSERTED (inherited) + contextual STIPULATED, and its mirror: the same status either way."""
    wm, ids = m
    dan, cal = cap(wm, "plan", "dan"), cap(wm, "plan", "cal")
    assert (dan["status"], dan["judgement"]) == (cal["status"], cal["judgement"]) == (Status.STIPULATED,
                                                                                      "established")
    assert set(dan["support"]) == {ids["dan_general"], ids["dan_general_2"], ids["dan_depot"]}
    assert set(cal["support"]) == {ids["cal_depot"], ids["cal_general"]}
    assert rests_on_support(wm, "plan", dan) and rests_on_support(wm, "plan", cal)
    # each holding keeps its own status
    assert {h["context"]: h["status"] for h in dan["applicable"]} == {None: Status.ASSERTED, "depot": Status.STIPULATED}


def test_e1_audit_and_e2_actual_world(m):
    wm, ids = m
    a = cap(wm, "plan", "dan", "audit")          # audit accepts none of HR's claims: only the stipulation decides
    assert (a["status"], a["support"]) == (Status.STIPULATED, [ids["dan_depot"]])
    assert {h["context"]: h["judgement"] for h in a["applicable"]} == {None: "unreviewed", "depot": "accepted"}
    e2 = cap(wm, "w", "dan")
    assert (e2["status"], e2["judgement"]) == (Status.ASSERTED, "established")


def test_e3_an_inferred_holding_never_outranks_an_asserted_one(m):
    wm, ids = m
    e = cap(wm, "plan", "eve")
    assert (e["status"], set(e["support"])) == (Status.ASSERTED, {ids["eve_general"], ids["eve_depot"]})
    assert {h["context"]: h["status"] for h in e["applicable"]} == {None: Status.INFERRED, "depot": Status.ASSERTED}
    assert cap(wm, "plan", "eve", "audit")["status"] == Status.UNKNOWN


def test_e4_denied_and_expired_combine(m):
    """An expired general holding (ASSERTED) and an explicit contextual denial (STIPULATED): denied, STIPULATED."""
    wm, ids = m
    f = cap(wm, "plan", "fay")
    assert (f["holds"], f["judgement"], f["status"]) == (False, "denied", Status.STIPULATED)
    assert set(f["support"]) == {ids["fay_general"], ids["fay_denial"]}
    assert {h["context"]: h["judgement"] for h in f["applicable"]} == {None: "expired", "depot": "denied"}
    # the expired holding alone (actual world, no denial): expired, its own support
    g = cap(wm, "w", "fay")
    assert (g["holds"], g["judgement"], g["status"], g["support"]) == (False, "expired", Status.ASSERTED,
                                                                       [ids["fay_general"]])


def test_e5_a_conflict_stays_disputed(m):
    wm, ids = m
    g = cap(wm, "plan", "gus")
    assert (g["holds"], g["status"], g["judgement"], g["support"]) == (None, Status.DISPUTED, "disputed", [])
    assert {h["context"]: h["judgement"] for h in g["applicable"]} == {None: "accepted", "depot": "denied"}
    a = cap(wm, "plan", "gus", "audit")          # audit has not accepted HR's grant: only the denial applies
    assert (a["judgement"], a["status"], a["support"]) == ("denied", Status.STIPULATED, [ids["gus_denial"]])


def test_pending_and_unreviewed_holdings_are_listed_never_folded_in(m):
    wm, ids = m
    h = cap(wm, "w", "hal")
    assert (h["judgement"], h["status"], h["support"]) == ("established", Status.ASSERTED, [ids["hal_general"]])
    pending = next(x for x in h["applicable"] if x["context"] == "depot")
    assert pending["judgement"] == "unreviewed" and pending["status"] is None
    assert [c["attestation"] for c in pending["attestations"]] == [ids["hal_pending"]]
    # audit has accepted neither: both undecided, so nothing decides (not established)
    only = wm.capable("w", "hal", "analyst", AT, context="depot", perspective="audit")
    assert (only["holds"], only["status"], only["judgement"], only["support"]) == \
        (None, Status.UNKNOWN, "not established", [])


def test_an_unknown_end_is_never_an_expiry(m):
    wm, ids = m
    i = cap(wm, "w", "ivy", t=T(9))
    assert (i["holds"], i["status"], i["judgement"], i["support"]) == (None, Status.UNKNOWN, "not established", [])
    assert [h["judgement"] for h in i["applicable"]] == ["not established"]
    # before it begins: not yet effective, not expired either
    assert cap(wm, "w", "ivy", t=T(1, 0))["judgement"] == "not yet effective"


def test_knowledge_time_before_the_plan_s_claims(m):
    wm, ids = m
    dan = cap(wm, "plan", "dan", as_of=ids["known_before_plan_claims"])
    assert (dan["status"], set(dan["support"])) == (Status.ASSERTED, {ids["dan_general"], ids["dan_general_2"]})


def test_each_claim_counts_once(m):
    """Two attestations of one content are one holding with two deciding claims; passing a record twice, or the same
    records in any order, never changes the answer or repeats a claim."""
    wm, ids = m
    recs = [e for e in wm._contents("plan", "dan", ("classified-as",), AT, None, "system")
            if e.stated_roles.get("context", [None])[0] in (None, "depot")]
    base = combine(recs, True)
    assert base[1] == Status.STIPULATED and len(base[3]) == len(set(base[3])) == 3
    assert combine(recs + recs, True) == base
    for _ in range(5):
        shuffled = random.Random(_).sample(recs, len(recs))
        assert combine(shuffled, True) == base


# ---- rule Q: authorised and calibration_status ---------------------------------------------------------------------
def test_e6_authorised_two_grantors(m):
    wm, ids = m
    r = org.authorised(wm, "plan", "bea", "can-sign", "depot", AT)
    assert (r["status"], set(r["support"])) == (Status.STIPULATED, {ids["acme_grant"], ids["board_grant"]})
    assert {g["grantor"]: g["status"] for g in r["grants"]} == {"acme": Status.ASSERTED, "board": Status.STIPULATED}
    assert rests_on_support(wm, "plan", r)
    a = org.authorised(wm, "plan", "bea", "can-sign", "depot", AT, perspective="audit")
    assert (a["status"], a["support"]) == (Status.STIPULATED, [ids["board_grant"]])


def test_e7_calibration_does_not_depend_on_certificate_names(m):
    """The same three bases (STIPULATED, INFERRED, ASSERTED): the stipulated certificate named cert-1 (sorts first,
    plan) or cert-4 (sorts last, plan-2) gives the same answer."""
    wm, ids = m
    p1 = lb.calibration_status(wm, "plan", "balance", AT)
    p2 = lb.calibration_status(wm, "plan-2", "balance", AT)
    assert p1["status"] == p2["status"] == Status.STIPULATED
    assert set(p1["support"]) == {ids["cert1"], ids["cert2"], ids["cert3"]}
    assert set(p2["support"]) == {ids["cert4"], ids["cert2"], ids["cert3"]}
    assert rests_on_support(wm, "plan", p1) and rests_on_support(wm, "plan-2", p2)
    assert {c["certificate"]: c["status"] for c in p2["certificates"]} == \
        {"cert-2": Status.INFERRED, "cert-3": Status.ASSERTED, "cert-4": Status.STIPULATED}
    actual = lb.calibration_status(wm, "w", "balance", AT)       # INFERRED and ASSERTED only: ASSERTED
    assert (actual["status"], set(actual["support"])) == (Status.ASSERTED, {ids["cert2"], ids["cert3"]})


@pytest.mark.parametrize("order", ["reversed", "shuffled"])
def test_query_result_order_cannot_change_an_answer(m, order, monkeypatch):
    """Every affected reader gives the same answer when the canonical records arrive in another order."""
    wm, ids = m

    def read_all():
        return ([cap(wm, "plan", x, p) for x in ("dan", "cal", "eve", "fay", "gus") for p in ("system", "audit")]
                + [org.authorised(wm, "plan", "bea", "can-sign", "depot", AT),
                   lb.calibration_status(wm, "plan", "balance", AT), lb.calibration_status(wm, "plan-2", "balance", AT),
                   org.office_holders(wm, "plan", "office-x", "depot", AT)])

    def key(a):
        return (a.get("holds"), a["status"], a.get("judgement"), a.get("support"), a.get("holders"))
    before = [key(a) for a in read_all()]
    real = wm._contents

    def reordered(*a, **k):
        out = list(real(*a, **k))
        return out[::-1] if order == "reversed" else random.Random(7).sample(out, len(out))
    monkeypatch.setattr(wm, "_contents", reordered)
    assert [key(a) for a in read_all()] == before


# ---- rule C: office_holders ----------------------------------------------------------------------------------------
@pytest.mark.parametrize("world,perspective,holders,statuses", [
    ("plan", "system", ["bea", "cal"], {"bea": Status.ASSERTED, "cal": Status.STIPULATED}),
    ("plan", "audit", ["cal"], {"bea": Status.UNKNOWN, "cal": Status.STIPULATED}),      # bea: unreviewed
    ("w", "system", ["bea"], {"bea": Status.ASSERTED}),
])
def test_e8_office_holders_invents_no_collective_status(m, world, perspective, holders, statuses):
    wm, ids = m
    r = org.office_holders(wm, world, "office-x", "depot", AT, perspective=perspective)
    assert (r["holders"], r["status"]) == (holders, None)
    assert {a["holder"]: a["status"] for a in r["appointments"]} == statuses


def test_office_holders_without_holders_keeps_unknown_and_not_yet_known(m):
    wm, ids = m
    assert org.office_holders(wm, "w", "office-x", "depot", T(1, 0))["status"] == Status.UNKNOWN
    assert org.office_holders(wm, "w", "office-x", "board", AT)["status"] == Status.NOT_YET_KNOWN


def test_e9_employment_rows_keep_their_own_statuses(m):
    wm, ids = m
    rows = org.employment(wm, "plan", "acme", AT)
    assert [(r["employee"], r["status"]) for r in rows] == [("bea", Status.ASSERTED), ("cal", Status.STIPULATED)]


# ---- changes against value_of --------------------------------------------------------------------------------------
def test_e10_changes_and_value_of_agree_on_a_slot(m):
    """The box's locations are INFERRED; an ASSERTED denial of another room is not support for the room it is in."""
    wm, ids = m
    ch = wm.changes("w", "box", T(2), T(6))
    tr = [x for x in ch["transitions"] if x["track"]["kind"] == "slot"]
    assert [(x["before"]["values"], x["after"]["values"]) for x in tr] == [([["room-1"]], [["room-3"]])]
    for x, at in ((tr[0]["before"], T(3)), (tr[0]["after"], T(5))):
        v = wm.value_of("w", "located-at", {"located": "box"}, at)
        assert x["status"] == v.status == Status.INFERRED
        assert x["values"] == [list(v.values)]
