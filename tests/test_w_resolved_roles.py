"""Stage E1 reconciliation R1 (LABS-1.052): the resolved role-player set (MP-2) beside ER-5's complete listing.

docs/stage-e/e1-reconciliation-design.md, R1. Every role entry of `occurrence()` keeps `players` (every linked
account's players, accepted or not: ER-5) and gains `resolved`: the players of the compared accounts only, with its
judgement and provenance. Players of unaccepted accounts are never resolved; an accepted account is not an
established conclusion (a union is `union`, never `established`).
"""

import uuid
from datetime import datetime, timezone

import pytest

from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel, organisation as org
from worldmodel.organisation import CO_SIGNED
from worldmodel.semantics import Status

pytestmark = pytest.mark.own_profiles


def T(day):
    return datetime(2026, 11, day, 9, tzinfo=timezone.utc)


def accept(wm, world, description, holder="system"):
    for a in wm.account_attestations(world, description):
        wm.accept(a, holder=holder)


@pytest.fixture(scope="module")
def ref(driver):
    wm = WorldModel.create(f"wm-test-{uuid.uuid4().hex[:10]}", driver=driver, modules=CORE_MODULES, clock=FakeClock())
    try:
        wm.install_profile("organisation")
        w = wm.create_world("actual", id="w")
        for p in ("dan", "eve", "fay", "gus", "hal", "bea", "cal", "dee", "b-smith", "hr", "clerk", "cmms", "qa"):
            wm.add_entity("person", p, id=p)
        wm.add_entity("organisation", "acme", id="acme")
        wm.add_entity("social-role", "manager", id="manager")
        wm.add_entity("place", "depot", id="depot")
        for o in ("o-job", "o-none", "o-one", "o-split", "o-cosign", "o-sets", "o-alias", "o-plan"):
            wm.add_entity("occurrence", o, id=o)

        def job(occ, actor, src, did, accepted=True, world=w, holder="system"):
            d = wm.account(world, {"actor": actor, "location": "depot"}, T(5), occurrence=occ, attester=src, id=did)
            if accepted:
                accept(wm, world, d, holder)
            return d

        # a union: two accepted accounts, one unreviewed, one rejected, one whose describes link is disputed
        job("o-job", "dan", "cmms", "job-dan")
        job("o-job", "eve", "hr", "job-eve")
        job("o-job", "fay", "clerk", "job-fay", accepted=False)
        rej = job("o-job", "gus", "qa", "job-gus", accepted=False)
        for a in wm.account_attestations(w, rej):
            wm.accept(a, verdict="rejected")
        link = job("o-job", "hal", "clerk", "job-hal")
        wm.accept(wm.deny(w, "describes", {"description": link, "occurrence": "o-job"}, until_superseded=True,
                          attester="qa"))
        job("o-none", "fay", "clerk", "none-fay", accepted=False)        # only an unaccepted account names it

        def act(occ, officials, src, did, world=w):
            e = org.act_in_office(wm, world, officials, "manager", "acme", T(5), occurrence=occ, attester=src, id=did)
            accept(wm, world, e)
            return e
        act("o-one", "bea", "hr", "one-hr")                                # established one
        act("o-split", "bea", "hr", "split-hr")                            # disputed one: accounts disagree
        act("o-split", "cal", "clerk", "split-clerk")
        act("o-cosign", ["bea", "cal"], "hr", "cosign-hr")                 # established set
        act("o-sets", ["bea", "cal"], "hr", "sets-hr")                     # conflicting sets
        act("o-sets", ["bea", "dee"], "clerk", "sets-clerk")
        for occ in ("o-cosign", "o-sets"):
            wm.attest(w, "classified-as", {"classified": occ, "class": CO_SIGNED}, start=T(5), until_superseded=True)
        job("o-alias", "bea", "hr", "alias-hr")                            # one player under identity
        job("o-alias", "b-smith", "clerk", "alias-clerk")
        wm.accept(wm.attest(w, "same-as", {"same": ["bea", "b-smith"]}, until_superseded=True, attester="hr"))
        job("o-plan", "dan", "cmms", "plan-base")                          # a plan overrides the inherited account
        plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(10), id="plan")
        job("o-plan", "eve", "system", "plan-own", world=plan)
        job("o-job", "fay", "clerk", "job-fay-hr", accepted=True, holder="hr")    # hr accepts a third account
        yield wm
    finally:
        wm.driver.databases.get(wm.database).delete()


@pytest.fixture(params=[True, False], ids=["selective", "full-load"])
def wm(ref, request):
    ref.selective = request.param
    yield ref
    ref.selective = True


def role(wm, occ, label, world="w", **kw):
    return wm.occurrence(world, occ, **kw)["roles"][label]


def names(resolved):
    return [p["names"] for p in resolved["players"]]


def test_a_union_resolves_only_the_compared_accounts_players(wm):
    r = role(wm, "o-job", "event:actor")
    assert sorted(r["players"]) == ["dan", "eve", "fay", "gus", "hal"]           # ER-5: every account, unchanged
    res = r["resolved"]
    assert (res["judgement"], names(res), res["constraint"]) == ("union", [["dan"], ["eve"]], None)
    assert res["compared"] == ["job-dan", "job-eve"] and res["overridden"] == []
    assert {x["description"]: x["why"] for x in res["not_compared"]} == {
        "job-fay": "account unreviewed", "job-fay-hr": "account unreviewed", "job-gus": "account rejected",
        "job-hal": "describes disputed"}
    assert [p["status"] for p in res["players"]] == [Status.ASSERTED, Status.ASSERTED]
    accounts = {a for d in ("job-dan", "job-eve") for a in wm.account_attestations("w", d)}
    assert res["support"] and set(res["support"]) <= accounts                   # provenance: the compared accounts
    others = {a for d in ("job-fay", "job-gus", "job-hal") for a in wm.account_attestations("w", d)}
    assert not set(res["support"]) & others


def test_a_role_named_only_by_an_unaccepted_account_resolves_nothing(wm):
    r = role(wm, "o-none", "event:actor")
    assert r["players"] == {"fay": ["none-fay"]}
    assert (r["resolved"]["judgement"], r["resolved"]["players"], r["resolved"]["compared"]) == ("none", [], [])
    assert r["resolved"]["not_compared"] == [{"description": "none-fay", "why": "account unreviewed"}]


def test_a_constraint_that_holds_resolves_its_players(wm):
    res = role(wm, "o-one", "official-act:official")["resolved"]
    assert (res["judgement"], names(res)) == ("established", [["bea"]])
    assert res["constraint"] == {"event_type": "official-act", "role": "actor", "kind": None, "multiplicity": "one"}
    res = role(wm, "o-cosign", "official-act:official")["resolved"]
    assert (res["judgement"], names(res), res["constraint"]["multiplicity"]) == ("established", [["bea"], ["cal"]],
                                                                               "set")
    assert res["support"]


@pytest.mark.parametrize("occ,multiplicity", [("o-split", "one"), ("o-sets", "set")])
def test_a_violated_constraint_resolves_no_player(wm, occ, multiplicity):
    r = role(wm, occ, "official-act:official")
    res = r["resolved"]
    assert (res["judgement"], res["players"], res["support"]) == ("disputed", [], [])
    assert res["constraint"]["multiplicity"] == multiplicity
    applying = [c for c in r["constraints"] if c["applies"]]
    assert applying[0]["judgement"] == "disputed" and len(applying[0]["players"]) >= 2   # candidates stay listed


def test_identity_groups_the_resolved_players(wm):
    res = role(wm, "o-alias", "event:actor")["resolved"]
    assert (res["judgement"], names(res)) == ("union", [["b-smith", "bea"]])
    res = role(wm, "o-alias", "event:actor", perspective="qa")["resolved"]          # qa accepts neither account
    assert (res["judgement"], res["players"]) == ("none", [])


def test_a_plan_s_own_account_overrides_the_inherited_one(wm):
    res = role(wm, "o-plan", "event:actor", world="plan")["resolved"]
    assert (res["judgement"], names(res), res["compared"], res["overridden"]) == ("union", [["eve"]], ["plan-own"],
                                                                                ["plan-base"])
    base = role(wm, "o-plan", "event:actor")["resolved"]
    assert (names(base), base["compared"]) == ([["dan"]], ["plan-base"])


def test_each_perspective_resolves_from_its_own_acceptances(wm):
    res = role(wm, "o-job", "event:actor", perspective="hr")["resolved"]
    assert names(res) == [["eve"], ["fay"]]                  # hr's own account and the one it accepted
    assert "job-dan" in {x["description"] for x in res["not_compared"]}


def test_existing_fields_are_unchanged_by_the_new_one(wm):
    view = wm.occurrence("w", "o-job")
    entry = view["roles"]["event:actor"]
    assert set(entry) == {"name", "core_role", "players", "constraints", "resolved"}
    assert entry["players"]["fay"] == ["job-fay", "job-fay-hr"] and entry["constraints"] == []
    assert {a["description"] for a in view["accounts"]} >= {"job-fay", "job-gus", "job-hal"}
