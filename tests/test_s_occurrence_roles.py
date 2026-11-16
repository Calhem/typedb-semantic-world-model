"""Increment D (DI-2; LABS-1.041/1.042 design, LABS-1.043 approval): event roles in the merged occurrence view.

The design's executed examples (docs/core-0.4/pre-e-increment-d-design.md, section 6; probes/pre_e_d_examples.py),
X1 to X7d4, as permanent tests on both query paths, read from the library's own `occurrence()`:
- multiplicity is not conflict: a role is exclusive only under an applicable, established constraint (ER-1, ER-2);
- official acts: official, office and office context, unconditionally (ER-6);
- replacements: removed and fitted only for an occurrence established as one-for-one at its start, judged by the
  canonical record of the classification (perspective, knowledge time, polarity, valid time, hypothetical worlds);
- same-as identity; unreviewed accounts and disputed links listed, never compared; the nearest world decides;
- `accounts` and `roles` keyed by stored role label (ER-5); `descriptions` and `participants` unchanged.
"""

import random
import uuid
from datetime import datetime, timezone

import pytest

from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel, mechanical as mech, organisation as org
from worldmodel.mechanical import ONE_FOR_ONE
from worldmodel.semantics import Status

pytestmark = pytest.mark.own_profiles


def T(day, h=9):
    return datetime(2026, 11, day, h, tzinfo=timezone.utc)


def accept_account(wm, world, event, holder="system"):
    for a in wm.account_attestations(world, event):
        wm.accept(a, holder=holder)


@pytest.fixture(scope="module")
def ref(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    try:
        for p in ("mechanical", "organisation", "laboratory"):
            wm.install_profile(p)
        w = wm.create_world("actual", id="w")
        for p in ("bea", "cal", "b-smith", "dan", "hr", "clerk", "cmms", "insp", "auditor", "qa"):
            wm.add_entity("person", p, id=p)
        for i in ("housing", "b1", "b2", "b3", "b4"):
            wm.add_entity("physical-object", i, id=i)
        wm.add_entity("organisation", "depot", id="depot")
        wm.add_entity("social-role", "site-manager", id="site-manager")
        for o in ("o-act", "o-act-alias", "o-act-pending", "o-act-link", "o-job", "o-swap", "o-swap-1for1",
                  "o-swap-late", "o-swap-plan", "o-k-pending", "o-k-disputed", "o-k-ended", "o-sample"):
            wm.add_entity("occurrence", o, id=o)
        ids = {}

        def act(occ, official, attester, world=w, accept=True):
            e = org.act_in_office(wm, world, official, "site-manager", "depot", T(5), occurrence=occ,
                                  attester=attester, id=f"act-{occ[2:]}-{world}-{attester}")
            if accept and attester != "system":
                accept_account(wm, world, e)
            return e

        def swap(occ, removed, fitted, attester, world=w):
            r = mech.replace_part(wm, world, "housing", removed, fitted, T(5), occurrence=occ, attester=attester,
                                  id=f"rep-{occ[2:]}-{attester}-{removed}")
            accept_account(wm, world, r["event"])
            return r["event"]

        ids["a_hr"] = act("o-act", "bea", "hr")                                   # X1
        ids["a_clerk"] = act("o-act", "cal", "clerk", accept=False)
        ids["known_before_clerk_accepted"] = wm.clock.now
        accept_account(wm, w, ids["a_clerk"])
        accept_account(wm, w, wm.account(w, {"actor": "dan", "location": "depot"}, T(5), occurrence="o-act",
                                         attester="hr", id="ev-act-generic"))     # X5: a core event account
        accept_account(wm, w, ids["a_hr"], holder="auditor")                       # X1b
        for acct in (act("o-act-alias", "bea", "hr"), act("o-act-alias", "b-smith", "clerk")):   # X3
            accept_account(wm, w, acct, holder="qa")
        wm.accept(wm.attest(w, "same-as", {"same": ["bea", "b-smith"]}, until_superseded=True, attester="hr"))
        act("o-act-pending", "bea", "hr")                                          # X4a
        act("o-act-pending", "cal", "clerk", accept=False)
        act("o-act-link", "bea", "hr")                                             # X4b
        ids["disputed_link"] = act("o-act-link", "cal", "clerk")
        wm.accept(wm.deny(w, "describes", {"description": ids["disputed_link"], "occurrence": "o-act-link"},
                          until_superseded=True, attester="auditor"))
        swap("o-job", "b1", "b3", "cmms")                                          # X2: a two-bearing job
        swap("o-job", "b2", "b4", "cmms")
        for occ in ("o-swap", "o-swap-1for1", "o-swap-late"):                     # X2b
            swap(occ, "b1", "b3", "cmms")
            swap(occ, "b2", "b3", "insp")
            wm.account(w, {"actor": "dan", "patient": "b3"}, T(5), occurrence=occ, id=f"ev-{occ[2:]}-worklog")
        ids["one_for_one"] = wm.attest(w, "classified-as", {"classified": "o-swap-1for1", "class": ONE_FOR_ONE},
                                       start=T(5), until_superseded=True)          # X2c
        wm.attest(w, "classified-as", {"classified": "o-swap-late", "class": ONE_FOR_ONE}, start=T(6),
                  until_superseded=True)                                           # X6d
        for occ in ("o-k-pending", "o-k-disputed", "o-k-ended", "o-swap-plan"):   # X7
            swap(occ, "b1", "b3", "cmms")
            swap(occ, "b2", "b3", "insp")
        pending_k = wm.attest(w, "classified-as", {"classified": "o-k-pending", "class": ONE_FOR_ONE}, start=T(5),
                              until_superseded=True, attester="cmms")
        ids["known_before_k_accepted"] = wm.clock.now
        wm.accept(pending_k)
        wm.attest(w, "classified-as", {"classified": "o-k-disputed", "class": ONE_FOR_ONE}, start=T(5),
                  until_superseded=True)
        wm.accept(wm.deny(w, "classified-as", {"classified": "o-k-disputed", "class": ONE_FOR_ONE}, start=T(5),
                          until_superseded=True, attester="insp"))
        wm.attest(w, "classified-as", {"classified": "o-k-ended", "class": ONE_FOR_ONE}, start=T(1), end=T(4))
        # sampling: several accepted accounts with different products, samplers and specimens: never a dispute
        for who, spec, prod in (("bea", "b1", "s-a"), ("cal", "b2", "s-b")):
            wm.add_entity("sample", prod, id=prod)
        from worldmodel import laboratory as lb
        for who, spec, prod in (("bea", "b1", "s-a"), ("cal", "b2", "s-b")):
            accept_account(wm, w, lb.take_sample(wm, w, who, spec, prod, T(5), occurrence="o-sample",
                                                 attester=who)["event"])
        plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(2), id="plan")          # X6b
        act("o-act", "cal", "system", world=plan)
        late = wm.create_world("plan-late", kind="hypothetical", base=w, branch_at=T(6), id="plan-late")  # X6c
        act("o-act", "bea", "system", world=late)
        deny = wm.create_world("plan-deny", kind="hypothetical", base=w, branch_at=T(6), id="plan-deny")  # X7d2
        wm.deny(deny, "classified-as", {"classified": "o-swap-1for1", "class": ONE_FOR_ONE}, start=T(5),
                until_superseded=True)
        cls = wm.create_world("plan-classify", kind="hypothetical", base=w, branch_at=T(6), id="plan-classify")
        wm.attest(cls, "classified-as", {"classified": "o-swap-plan", "class": ONE_FOR_ONE}, start=T(5),
                  until_superseded=True)                                                                # X7d3
        yield wm, ids
    finally:
        driver.databases.get(name).delete()


@pytest.fixture(params=[True, False], ids=["selective", "full-load"])
def m(ref, request):
    wm, ids = ref
    wm.selective = request.param
    yield wm, ids
    wm.selective = True


def con(view, label, role=None):
    """The constraint evaluated for a stored role label (the only one, or the one for `role`)."""
    cs = [c for c in view["roles"][label]["constraints"] if role is None or c["role"] == role]
    assert len(cs) == 1, cs
    return cs[0]


def names(c):
    return [p["names"] for p in c["players"]]


def accounts(view):
    return {a["description"]: (a["describes"], a["account"]) for a in view["accounts"]}


# ---- official acts: unconditional constraints ------------------------------------------------------------------------
def test_x1_conflicting_officials_are_disputed_each_cited(m):
    wm, ids = m
    v = wm.occurrence("w", "o-act")
    c = con(v, "official-act:official")
    assert (c["applies"], c["judgement"], c["status"], c["support"]) == (True, "disputed", Status.DISPUTED, [])
    assert names(c) == [["bea"], ["cal"]]
    assert [[a["description"] for a in p["accounts"]] for p in c["players"]] == [[ids["a_hr"]], [ids["a_clerk"]]]
    assert [p["status"] for p in c["players"]] == [Status.ASSERTED, Status.ASSERTED]
    assert con(v, "official-act:office")["judgement"] == "established"
    assert con(v, "official-act:office-context")["judgement"] == "established"
    # X5: a core event account's `actor` is listed apart and never compared with `official`
    assert v["roles"]["event:actor"]["players"] == {"dan": ["ev-act-generic"]}
    assert v["roles"]["event:actor"]["constraints"] == [] and v["roles"]["official-act:official"]["core_role"] == "actor"
    # existing fields keep their meaning: the core-role projection merges them
    assert set(v["participants"]["actor"]) == {"bea", "cal", "dan"}


def test_x1b_x6a_a_perspective_or_knowledge_time_with_one_account(m):
    wm, ids = m
    for v in (wm.occurrence("w", "o-act", perspective="auditor"),
              wm.occurrence("w", "o-act", as_of=ids["known_before_clerk_accepted"])):
        c = con(v, "official-act:official")
        assert (c["judgement"], names(c), c["status"]) == ("established", [["bea"]], Status.ASSERTED)
        assert c["support"] and accounts(v)[ids["a_clerk"]][1] != "accepted"


def test_x3_same_as_names_are_one_player_unless_the_perspective_lacks_the_link(m):
    wm, ids = m
    c = con(wm.occurrence("w", "o-act-alias"), "official-act:official")
    assert (c["judgement"], names(c)) == ("established", [["b-smith", "bea"]])
    c = con(wm.occurrence("w", "o-act-alias", perspective="qa"), "official-act:official")
    assert (c["judgement"], names(c)) == ("disputed", [["b-smith"], ["bea"]])


def test_x4_unreviewed_accounts_and_disputed_links_are_listed_never_compared(m):
    wm, ids = m
    v = wm.occurrence("w", "o-act-pending")
    assert sorted(accounts(v).values()) == [("accepted", "accepted"), ("unreviewed", "unreviewed")]
    assert con(v, "official-act:official")["judgement"] == "established"
    v = wm.occurrence("w", "o-act-link")
    assert accounts(v)[ids["disputed_link"]] == ("disputed", "accepted")
    c = con(v, "official-act:official")
    assert (c["judgement"], names(c)) == ("established", [["bea"]])
    assert set(v["participants"]["actor"]) == {"bea", "cal"}                     # unchanged existing field


# ---- multiplicity without a constraint -------------------------------------------------------------------------------
def test_x2_a_two_part_job_is_a_union(m):
    wm, ids = m
    v = wm.occurrence("w", "o-job")
    c = con(v, "replacement:removed")
    assert (c["applies"], c["judgement"], c["classification"]["judgement"]) == (False, None, "unknown")
    assert set(v["roles"]["replacement:removed"]["players"]) == {"b1", "b2"}
    assert set(v["participants"]["patient"]) == {"b1", "b2"}


def test_x2b_disagreeing_sources_without_one_for_one_stay_a_union_with_roles_apart(m):
    wm, ids = m
    v = wm.occurrence("w", "o-swap")
    assert con(v, "replacement:removed")["applies"] is False
    assert set(v["roles"]["replacement:removed"]["players"]) == {"b1", "b2"}
    assert v["roles"]["event:patient"]["players"] == {"b3": ["ev-swap-worklog"]}        # presentation: apart
    assert set(v["participants"]["patient"]) == {"b1", "b2", "b3"}                       # existing field: merged


def test_sampling_and_core_roles_are_never_exclusive(m):
    wm, ids = m
    v = wm.occurrence("w", "o-sample")
    assert all(r["constraints"] == [] for r in v["roles"].values())
    assert set(v["roles"]["sampling:product"]["players"]) == {"s-a", "s-b"}
    assert set(v["roles"]["sampling:sampler"]["players"]) == {"bea", "cal"}


# ---- the one-for-one classification, judged canonically ------------------------------------------------------------
@pytest.mark.parametrize("world,occ,perspective,as_of,applies,classification,judgement", [
    ("w", "o-swap-1for1", "system", None, True, "established", "disputed"),            # X2c
    ("w", "o-swap-1for1", "insp", None, False, "pending", None),                       # X2d perspective
    ("w", "o-swap-late", "system", None, False, "unknown", None),                      # X6d not yet effective
    ("w", "o-k-pending", "system", "known_before_k_accepted", False, "pending", None),  # X7a knowledge time
    ("w", "o-k-pending", "system", None, True, "established", "disputed"),             # X7a2
    ("w", "o-k-disputed", "system", None, False, "disputed", None),                    # X7b polarity
    ("w", "o-k-ended", "system", None, False, "not holding", None),                    # X7c valid time
    ("plan-late", "o-swap-1for1", "system", None, True, "established", "disputed"),    # X7d inherited
    ("plan-deny", "o-swap-1for1", "system", None, False, "not holding", None),         # X7d2 the plan denies it
    ("plan-classify", "o-swap-plan", "system", None, True, "established", "disputed"),  # X7d3 the plan's own
    ("w", "o-swap-plan", "system", None, False, "unknown", None),                      # X7d4 actual world
])
def test_one_for_one_applies_only_where_its_classification_is_established(m, world, occ, perspective, as_of,
                                                                          applies, classification, judgement):
    wm, ids = m
    v = wm.occurrence(world, occ, ids[as_of] if as_of else None, perspective)
    c = con(v, "replacement:removed")
    assert (c["applies"], c["classification"]["judgement"], c["judgement"]) == (applies, classification, judgement)
    assert c["classification"]["at"] == T(5)
    if judgement == "disputed":
        assert names(c) == [["b1"], ["b2"]] and con(v, "replacement:fitted")["judgement"] == "established"
    else:
        assert c["players"] == [] and len(v["roles"]["replacement:removed"]["players"]) >= 1


def test_x6d_and_x7_reasons_come_from_the_canonical_record(m):
    wm, ids = m
    reasons = {occ: con(wm.occurrence("w", occ), "replacement:removed")["classification"]["reasons"]
               for occ in ("o-swap-late", "o-k-disputed", "o-k-ended")}
    assert reasons == {"o-swap-late": ["not_yet_effective"], "o-k-disputed": ["polarity"], "o-k-ended": ["ended"]}
    c = con(wm.occurrence("w", "o-swap-1for1"), "replacement:removed")
    assert c["classification"]["support"] == [ids["one_for_one"]]


# ---- hypothetical worlds -------------------------------------------------------------------------------------------
def test_x6b_a_plan_branching_before_the_act_has_only_its_own_account(m):
    wm, ids = m
    v = wm.occurrence("plan", "o-act")
    c = con(v, "official-act:official")
    assert (c["judgement"], names(c), c["overridden"]) == ("established", [["cal"]], [])
    assert sorted(a["account"] for a in v["accounts"]).count("none") == 3        # DI-14: listed, not judged
    assert len(v["descriptions"]) == 4 and set(v["participants"]["actor"]) == {"cal"}   # unchanged existing fields


def test_x6c_the_plan_s_own_account_overrides_the_inherited_ones(m):
    wm, ids = m
    v = wm.occurrence("plan-late", "o-act")
    c = con(v, "official-act:official")
    assert (c["judgement"], names(c), c["status"]) == ("established", [["bea"]], Status.STIPULATED)
    assert c["overridden"] == sorted([ids["a_hr"], ids["a_clerk"]])


# ---- invariants ------------------------------------------------------------------------------------------------------
def test_existence_and_per_account_reports_are_unaffected_by_a_dispute(m):
    wm, ids = m
    status = wm.occurrence_status("w", "o-act", T(5))
    assert [d["account"] for d in status["descriptions"]] == ["accepted"] * 3
    assert org.official_act(wm, "w", ids["a_hr"])["official"] == "bea"
    assert org.official_act(wm, "w", ids["a_clerk"])["official"] == "cal"


@pytest.mark.parametrize("order", ["reversed", "shuffled"])
def test_query_result_order_cannot_change_a_judgement(m, order, monkeypatch):
    wm, ids = m
    cases = [("w", "o-act", "system"), ("w", "o-act-alias", "qa"), ("w", "o-swap-1for1", "system"),
             ("plan-late", "o-act", "system")]
    before = [wm.occurrence(w, o, perspective=p) for w, o, p in cases]
    real = wm._load

    def reordered(*a, **k):
        out = real(*a, **k)
        keys = list(out)[::-1] if order == "reversed" else random.Random(3).sample(list(out), len(out))
        return {key: out[key] for key in keys}
    monkeypatch.setattr(wm, "_load", reordered)
    assert [wm.occurrence(w, o, perspective=p) for w, o, p in cases] == before
