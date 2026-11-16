"""Increment D design (LABS-1.041, DI-2): executable examples of event-role exclusivity in the merged occurrence view.

    uv run python -I probes/pre_e_d_examples.py <checkout>

Builds one throwaway database (wm-probe-pre-e-d-*, deleted afterwards) with the core and the three profiles, writes the
cases of docs/core-0.4/pre-e-increment-d-design.md, section "Examples", and prints for each the current merged view
(`wm.occurrence`) and the view under the proposed rule. The proposed rule is computed here, in the probe
(`proposed_view`, in probes/pre_e_d_rule.py), from public readers only; nothing in the library is changed.
Each case asserts the current answer
and the proposed one, so the output records both. Output: probes/pre_e_d_examples.out.txt.

Proposed rule (design section 3), in short:
- the merged view lists every description linked to the occurrence, each with its own role names (as stored), the
  core role each specialises, its link's and its account's judgement, and its world depth;
- an event-role constraint (event type, core role), declared by a profile, or scoped by the profile to occurrences
  established as of an event kind (here `mechanical:one-for-one`), compares the players of that role among the
  descriptions of that type (or a subtype) whose link and account are both accepted, under the perspective's
  identity (same-as); the nearest world with such a description decides (deeper ones are `overridden`);
- two or more distinct players: DISPUTED, each player citing its descriptions and sources; one: established;
- roles without a constraint stay a union, each player citing its descriptions.
Declarations used here (the proposed profile declarations, design section 6): official-act `actor` (official),
`office` and `office-context`, unconditionally; replacement `patient` (removed) and `fitted` only for an occurrence
established as `mechanical:one-for-one` at its start.
"""

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, connect, mechanical as mech, organisation as org  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pre_e_d_rule import ONE_FOR_ONE, proposed_view  # noqa: E402

OUT = {}


def T(day, h=9):
    return datetime(2026, 11, day, h, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


def show(case, **values):
    OUT[case] = values
    print(f"\n=== {case}")
    for k, v in values.items():
        print(f"  {k}: {json.dumps(v, default=str)}")


def accept_account(wm, world, event, holder="system", attester=None):
    for a in wm.account_attestations(world, event, attester=attester):
        wm.accept(a, holder=holder)


driver = connect()
DB = f"wm-probe-pre-e-d-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(DB, driver=driver, modules=CORE_MODULES, clock=Clock())
try:
    for p in ("mechanical", "organisation", "laboratory"):
        wm.install_profile(p)
    w = wm.create_world("actual", id="w")
    for p in ("bea", "cal", "b-smith", "dan", "hr", "clerk", "cmms", "insp", "auditor", "qa"):
        wm.add_entity("person", p, id=p)
    for i in ("housing", "b1", "b2", "b3", "b4"):
        wm.add_entity("physical-object", i, id=i)
    for kind, i in (("organisation", "depot"), ("social-role", "site-manager"), ("category", ONE_FOR_ONE)):
        wm.add_entity(kind, i, id=i)
    for o in ("o-act", "o-act-alias", "o-act-pending", "o-act-link", "o-job", "o-swap", "o-swap-1for1",
              "o-swap-late", "o-swap-plan", "o-k-pending", "o-k-disputed", "o-k-ended"):
        wm.add_entity("occurrence", o, id=o)

    def act(occ, official, attester, world=w, accept=True, **kw):
        e = org.act_in_office(wm, world, official, "site-manager", "depot", T(5), occurrence=occ, attester=attester,
                              id=f"act-{occ[2:]}-{world}-{attester}", **kw)
        if accept and attester != "system":
            accept_account(wm, world, e)
        return e

    def swap(occ, removed, fitted, attester, world=w, accept=True):
        r = mech.replace_part(wm, world, "housing", removed, fitted, T(5), occurrence=occ, attester=attester,
                              id=f"rep-{occ[2:]}-{attester}-{removed}")
        if accept and attester != "system":
            accept_account(wm, world, r["event"])
        return r["event"]

    # X1: one official act, two accepted accounts naming different officials
    a_hr = act("o-act", "bea", "hr")
    a_clerk = act("o-act", "cal", "clerk", accept=False)
    known_before_clerk_accepted = wm.clock.now
    accept_account(wm, w, a_clerk)
    # X5: a core event account of the same act (a generic `actor`), accepted: listed, never compared with `official`
    gen = wm.account(w, {"actor": "dan", "location": "depot"}, T(5), occurrence="o-act", attester="hr",
                     id="ev-act-generic")
    accept_account(wm, w, gen)
    accept_account(wm, w, a_hr, holder="auditor")                  # the auditor accepts the HR account only
    # X3: two names for one person
    for acct in (act("o-act-alias", "bea", "hr"), act("o-act-alias", "b-smith", "clerk")):
        accept_account(wm, w, acct, holder="qa")                   # qa accepts both accounts, not the same-as link
    same = wm.attest(w, "same-as", {"same": ["bea", "b-smith"]}, until_superseded=True, attester="hr")
    wm.accept(same)
    # X4: an unreviewed account; a disputed link
    act("o-act-pending", "bea", "hr")
    act("o-act-pending", "cal", "clerk", accept=False)
    act("o-act-link", "bea", "hr")
    disputed_link = act("o-act-link", "cal", "clerk")
    wm.accept(wm.deny(w, "describes", {"description": disputed_link, "occurrence": "o-act-link"}, until_superseded=True,
                      attester="auditor"))
    # X2: a two-bearing job, as two one-for-one accounts of one occurrence: legitimate, never disputed
    swap("o-job", "b1", "b3", "cmms")
    swap("o-job", "b2", "b4", "cmms")
    # X2b: two sources disagree about the removed part, the reference case of DI-2 (same fitted part)
    for occ in ("o-swap", "o-swap-1for1", "o-swap-late"):
        swap(occ, "b1", "b3", "cmms")
        swap(occ, "b2", "b3", "insp")
        wm.account(w, {"actor": "dan", "patient": "b3"}, T(5), occurrence=occ, attester="system",
                   id=f"ev-{occ[2:]}-worklog")                          # core naming: the fitted part as patient
    wm.attest(w, "classified-as", {"classified": "o-swap-1for1", "class": ONE_FOR_ONE}, start=T(5),
              until_superseded=True)
    wm.attest(w, "classified-as", {"classified": "o-swap-late", "class": ONE_FOR_ONE}, start=T(6),
              until_superseded=True)                                       # X6: only after the swap began
    # X7: the one-for-one classification judged canonically (the same two conflicting swaps on each occurrence)
    for occ in ("o-k-pending", "o-k-disputed", "o-k-ended", "o-swap-plan"):
        swap(occ, "b1", "b3", "cmms")
        swap(occ, "b2", "b3", "insp")
    pending_k = wm.attest(w, "classified-as", {"classified": "o-k-pending", "class": ONE_FOR_ONE}, start=T(5),
                          until_superseded=True, attester="cmms")           # X7a: by the CMMS, not yet accepted
    known_before_k_accepted = wm.clock.now
    wm.accept(pending_k)
    wm.attest(w, "classified-as", {"classified": "o-k-disputed", "class": ONE_FOR_ONE}, start=T(5),
              until_superseded=True)
    wm.accept(wm.deny(w, "classified-as", {"classified": "o-k-disputed", "class": ONE_FOR_ONE}, start=T(5),
                      until_superseded=True, attester="insp"))              # X7b: an accepted denial: DISPUTED
    wm.attest(w, "classified-as", {"classified": "o-k-ended", "class": ONE_FOR_ONE}, start=T(1),
              end=T(4))                                                     # X7c: held, but ended before day 5
    # X6: a plan stipulating its own account of the inherited act
    plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(2), id="plan")
    act("o-act", "cal", "system", world=plan)
    late = wm.create_world("plan-late", kind="hypothetical", base=w, branch_at=T(6), id="plan-late")
    act("o-act", "bea", "system", world=late)
    # X7d: plans branching after the swaps: one denies the inherited classification, one classifies its own
    deny_plan = wm.create_world("plan-deny", kind="hypothetical", base=w, branch_at=T(6), id="plan-deny")
    wm.deny(deny_plan, "classified-as", {"classified": "o-swap-1for1", "class": ONE_FOR_ONE}, start=T(5),
            until_superseded=True)
    class_plan = wm.create_world("plan-classify", kind="hypothetical", base=w, branch_at=T(6), id="plan-classify")
    wm.attest(class_plan, "classified-as", {"classified": "o-swap-plan", "class": ONE_FOR_ONE}, start=T(5),
              until_superseded=True)

    def both(case, occ, world=w, perspective="system", as_of=None, **extra):
        cur = wm.occurrence(world, occ, as_of, perspective)
        prop = proposed_view(wm, world, occ, as_of, perspective)
        show(case, current_descriptions=cur["descriptions"], current_participants=cur["participants"],
             proposed_descriptions=prop["descriptions"], proposed_roles=prop["roles"], proposed_judged=prop["judged"],
             **extra)
        return cur, prop

    cur, prop = both("X1 official act, two accepted accounts, different officials", "o-act")
    assert set(cur["participants"]["actor"]) == {"bea", "cal", "dan"}           # current: one union, no dispute
    assert prop["judged"]["official-act.actor"]["judgement"] == "disputed"
    assert [p["names"] for p in prop["judged"]["official-act.actor"]["players"]] == [["bea"], ["cal"]]
    assert prop["judged"]["official-act.office"]["judgement"] == "established"
    assert set(prop["roles"]) == {"event:actor", "event:location", "official-act:official", "official-act:office",
                                  "official-act:office-context"}                       # X5: stored labels
    assert prop["roles"]["official-act:official"]["core_role"] == "actor"
    assert list(prop["roles"]["event:actor"]["players"]) == ["dan"]                    # listed apart, never compared

    _, prop = both("X1b the auditor accepts the HR account only", "o-act", perspective="auditor")
    assert prop["judged"]["official-act.actor"]["judgement"] == "established"

    _, prop = both("X6a knowledge time before the clerk's account was accepted", "o-act",
                   as_of=known_before_clerk_accepted)
    assert prop["judged"]["official-act.actor"]["judgement"] == "established"

    cur, prop = both("X6b plan branching (day 2) before the act (day 5): the actual accounts are not in the plan",
                     "o-act", world="plan")
    j = prop["judged"]["official-act.actor"]
    assert j["judgement"] == "established" and j["players"][0]["names"] == ["cal"] and j["overridden"] == []
    assert sorted(x["account"] for x in prop["descriptions"]).count("none in this world") == 3
    assert len(cur["descriptions"]) == 4 and set(cur["participants"]["actor"]) == {"cal"}   # links inherited, roles not

    cur, prop = both("X6c plan branching (day 6) after the act: its own account overrides the inherited ones",
                     "o-act", world="plan-late")
    j = prop["judged"]["official-act.actor"]
    assert j["judgement"] == "established" and j["players"][0]["names"] == ["bea"] and len(j["overridden"]) == 2
    assert set(cur["participants"]["actor"]) == {"bea", "cal", "dan"}

    _, prop = both("X3 two names for one person (same-as accepted)", "o-act-alias")
    j = prop["judged"]["official-act.actor"]
    assert j["judgement"] == "established" and j["players"][0]["names"] == ["b-smith", "bea"]
    _, prop = both("X3b the same, for a perspective that accepts both accounts but not the same-as link (qa)",
                   "o-act-alias", perspective="qa")
    assert prop["judged"]["official-act.actor"]["judgement"] == "disputed"

    _, prop = both("X4a an unreviewed account is listed, never compared", "o-act-pending")
    assert prop["judged"]["official-act.actor"]["judgement"] == "established"
    assert sorted(x["account"] for x in prop["descriptions"]) == ["accepted", "not accepted"]
    cur, prop = both("X4b a disputed link is listed, never compared", "o-act-link")
    assert sorted(x["link"] for x in prop["descriptions"]) == ["accepted", "disputed"]
    assert prop["judged"]["official-act.actor"]["judgement"] == "established"
    assert len(cur["descriptions"]) == 2                                   # current: both listed, both merged

    cur, prop = both("X2 a two-bearing job: two one-for-one accounts, one occurrence", "o-job")
    assert set(cur["participants"]["patient"]) == {"b1", "b2"}
    assert prop["judged"]["replacement.patient"]["applies"] is False       # no dispute: not one-for-one
    assert set(prop["roles"]["replacement:removed"]["players"]) == {"b1", "b2"}

    cur, prop = both("X2b two sources disagree about the removed part; occurrence not classified", "o-swap")
    assert prop["judged"]["replacement.patient"]["applies"] is False
    assert set(cur["participants"]["patient"]) == {"b1", "b2", "b3"}        # current: core and profile names merged
    assert set(prop["roles"]["event:patient"]["players"]) == {"b3"}
    assert set(prop["roles"]["replacement:removed"]["players"]) == {"b1", "b2"}

    _, prop = both("X2c the same occurrence established as one-for-one at its start", "o-swap-1for1")
    assert prop["judged"]["replacement.patient"]["judgement"] == "disputed"
    assert prop["judged"]["replacement.fitted"]["judgement"] == "established"
    _, prop = both("X2d the same, as the inspector sees it: it has not accepted the one-for-one classification",
                   "o-swap-1for1", perspective="insp")
    assert prop["judged"]["replacement.patient"]["applies"] is False          # the constraint is judged per perspective

    _, prop = both("X6d classified one-for-one only from after the swap began: the constraint does not apply",
                   "o-swap-late")
    assert prop["judged"]["replacement.patient"]["applies"] is False

    def k(prop):
        return prop["judged"]["replacement.patient"]

    _, prop = both("X7a classified by the CMMS, before the system accepted it (knowledge time)", "o-k-pending",
                   as_of=known_before_k_accepted)
    assert k(prop)["applies"] is False and k(prop)["classification"]["judgement"] == "pending"
    _, prop = both("X7a2 the same, after the system accepted it", "o-k-pending")
    assert k(prop)["applies"] is True and k(prop)["judgement"] == "disputed"
    _, prop = both("X7b the classification asserted and denied, both accepted: DISPUTED, so it does not apply",
                   "o-k-disputed")
    assert k(prop)["applies"] is False and k(prop)["classification"]["judgement"] == "disputed"
    _, prop = both("X7c the classification held from day 1 to day 4 only (valid time)", "o-k-ended")
    assert k(prop)["applies"] is False and k(prop)["classification"]["judgement"] == "not holding"
    _, prop = both("X7d a plan branching after the swap inherits the classification and the accounts", "o-swap-1for1",
                   world="plan-late")
    assert k(prop)["applies"] is True and k(prop)["judgement"] == "disputed"
    _, prop = both("X7d2 a plan that stipulates the denial of the inherited classification", "o-swap-1for1",
                   world="plan-deny")
    assert k(prop)["applies"] is False and k(prop)["classification"]["judgement"] == "not holding"
    _, prop = both("X7d3 a plan that classifies an occurrence the actual world leaves unclassified", "o-swap-plan",
                   world="plan-classify")
    assert k(prop)["applies"] is True and k(prop)["judgement"] == "disputed"
    _, prop = both("X7d4 the same occurrence in the actual world", "o-swap-plan")
    assert k(prop)["applies"] is False and k(prop)["classification"]["judgement"] == "unknown"
    print("\nall cases behave as recorded")
finally:
    driver.databases.get(DB).delete()
