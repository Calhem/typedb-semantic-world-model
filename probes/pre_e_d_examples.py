"""Increment D design (LABS-1.041, DI-2): executable examples of event-role exclusivity in the merged occurrence view.

    uv run python -I probes/pre_e_d_examples.py <checkout>

Builds one throwaway database (wm-probe-pre-e-d-*, deleted afterwards) with the core and the three profiles, writes the
cases of docs/core-0.4/pre-e-increment-d-design.md, section "Examples", and prints for each the current merged view
(`wm.occurrence`) and the view under the proposed rule. The proposed rule is computed here, in the probe
(`proposed_view`), from public readers only; nothing in the library is changed. Each case asserts the current answer
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
from worldmodel import typeql as q  # noqa: E402
from worldmodel.semantics import usable  # noqa: E402

OUT = {}
ONE_FOR_ONE = "mechanical:one-for-one"
# (event type, core role, event kind or None): the proposed profile declarations
DECLARED = (("official-act", "actor", None), ("official-act", "office", None), ("official-act", "office-context", None),
            ("replacement", "patient", ONE_FOR_ONE), ("replacement", "fitted", ONE_FOR_ONE))


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


def scoped_roles(wm, d):
    """{own role name: (core role, [players])} of a description, from its stored (scoped) role labels."""
    out = {}
    with wm._reading() as tx:
        for r in q.rows(tx, "match $e isa event, has wm-id == $id; $e links ($role: $x); $x has wm-id $xid;",
                        {"id": d}):
            label = r.get("role").get_label()
            out.setdefault(label.split(":")[-1], (wm.core_role(label), []))[1].append(q.opt(r, "xid"))
    return {k: (c, sorted(v)) for k, (c, v) in out.items()}


def state(recs, perspective, as_of):
    """'accepted', 'disputed', 'denied' or 'not accepted', at the nearest depth with a usable claim (as `_judge`)."""
    use = [a for a in recs if usable(a, perspective, as_of)]
    if not use:
        return "not accepted", None
    depth = min(a.depth for a in use)
    pol = {a.polarity for a in use if a.depth == depth}
    return ("disputed" if len(pol) > 1 else "accepted" if True in pol else "denied"), depth


def proposed_view(wm, world, occ, as_of=None, perspective="system"):
    atts = wm.visible(world, as_of, perspective)
    ident = wm.identity(world, as_of, perspective)
    members = set(ident.members(occ))
    links = {}
    for a in atts.values():
        if a.kind == "describes" and members & set(a.roles.get("occurrence", [])):
            for d in a.roles.get("description", []):
                links.setdefault(d, []).append(a)
    descs = []
    for d, recs in sorted(links.items()):
        link, _ = state(recs, perspective, as_of)
        accounts = [a for a in atts.values() if a.kind == "event" and a.content == d]
        account, depth = state(accounts, perspective, as_of) if accounts else ("none in this world", None)
        starts = [a.start.earliest for a in accounts if usable(a, perspective, as_of) and a.polarity and a.start]
        descs.append({"description": d, "type": wm.content(d)["type"],
                      "attesters": sorted({a.attester for a in accounts}),
                      "link": link, "account": account, "depth": depth, "start": min(starts) if starts else None,
                      "roles": scoped_roles(wm, d)})
    roles = {}
    for x in descs:
        for own, (core, players) in x["roles"].items():
            e = roles.setdefault(own, {"core_role": core, "players": {}})
            for p in players:
                e["players"].setdefault(p, []).append(x["description"])
    compared = [x for x in descs if x["link"] == "accepted" and x["account"] == "accepted"]
    starts = [x["start"] for x in compared if x["start"] is not None]
    at = min(starts) if starts else None
    judged = {}
    for etype, core, kind in DECLARED:
        group = [x for x in compared if wm.is_a(x["type"], etype)
                 and any(c == core for c, _ in x["roles"].values())]
        if not group:
            continue
        if kind is not None:
            cls = wm.holds(world, "classified-as", {"classified": occ, "class": kind}, at, as_of, perspective) \
                if at is not None else None
            if cls is None or cls.holds is not True:
                judged[f"{etype}.{core}"] = {"constraint": f"only as {kind}", "applies": False}
                continue
        depth = min(x["depth"] for x in group)
        near = [x for x in group if x["depth"] == depth]
        players = {}
        for x in near:
            for c, ps in x["roles"].values():
                if c == core:
                    for p in ps:
                        players.setdefault(ident.canonical(p), {}).setdefault(p, []).append(
                            (x["description"], x["attesters"]))
        judged[f"{etype}.{core}"] = {
            "constraint": kind or "declared", "applies": True,
            "judgement": "disputed" if len(players) > 1 else "established",
            "players": [{"names": sorted(names), "cited": sorted({c for v in names.values() for c, _ in v})}
                        for _, names in sorted(players.items())],
            "overridden": sorted(x["description"] for x in group if x["depth"] != depth)}
    return {"descriptions": [{k: v for k, v in x.items() if k not in ("roles", "start")} for x in descs],
            "roles": {r: {"core_role": e["core_role"], "players": e["players"]} for r, e in sorted(roles.items())},
            "judged": judged}


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
              "o-swap-late", "o-swap-plan"):
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
    # X6: a plan stipulating its own account of the inherited act
    plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(2), id="plan")
    act("o-act", "cal", "system", world=plan)
    late = wm.create_world("plan-late", kind="hypothetical", base=w, branch_at=T(6), id="plan-late")
    act("o-act", "bea", "system", world=late)

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
    assert set(prop["roles"]) == {"actor", "location", "official", "office", "office-context"}   # X5: own names
    assert prop["roles"]["official"]["core_role"] == "actor" and list(prop["roles"]["actor"]["players"]) == ["dan"]

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
    assert set(prop["roles"]["removed"]["players"]) == {"b1", "b2"}

    cur, prop = both("X2b two sources disagree about the removed part; occurrence not classified", "o-swap")
    assert prop["judged"]["replacement.patient"]["applies"] is False
    assert set(cur["participants"]["patient"]) == {"b1", "b2", "b3"}        # current: core and profile names merged
    assert set(prop["roles"]["patient"]["players"]) == {"b3"}
    assert set(prop["roles"]["removed"]["players"]) == {"b1", "b2"}

    _, prop = both("X2c the same occurrence established as one-for-one at its start", "o-swap-1for1")
    assert prop["judged"]["replacement.patient"]["judgement"] == "disputed"
    assert prop["judged"]["replacement.fitted"]["judgement"] == "established"
    _, prop = both("X2d the same, as the inspector sees it: it has not accepted the one-for-one classification",
                   "o-swap-1for1", perspective="insp")
    assert prop["judged"]["replacement.patient"]["applies"] is False          # the constraint is judged per perspective

    _, prop = both("X6d classified one-for-one only from after the swap began: the constraint does not apply",
                   "o-swap-late")
    assert prop["judged"]["replacement.patient"]["applies"] is False
    print("\nall cases behave as recorded")
finally:
    driver.databases.get(DB).delete()
