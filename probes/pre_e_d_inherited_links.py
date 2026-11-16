"""Increment D clarification (LABS-1.042, item 4): descriptions listed in a plan whose accounts the plan does not
inherit. A minimal reproduction, then every reference case (the 18 views of probes/pre_e_d_impact.out.txt).

    uv run python -I probes/pre_e_d_inherited_links.py <checkout> [--db wm-probe-pre-e-d]

The inheritance rule (`_world_chain`, `_filters`): a variant sees a base world's attestation if it has no stated start
or its start (earliest) is before the branch point, and it was recorded by the branching's knowledge time; an
inherited attestation is kept whole. `account()` writes the description's own attestation over the event's interval
and its `describes` link with no start (until superseded), so a plan branching before the event inherits the link but
not the account. This probe shows that, shows that nothing is judged from the missing account, and checks that every
reference case is this mechanism. Output: probes/pre_e_d_inherited_links.out.txt.
"""

import argparse
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--db", default="wm-probe-pre-e-d")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402


def T(day, h=9):
    return datetime(2026, 11, day, h, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


def start(rec):
    return rec.start.earliest.isoformat() if rec.start else "none (from the start of the world)"


def show_world(wm, world, occ, desc):
    atts = wm.visible(world)
    link = [x for x in atts.values() if x.kind == "describes" and desc in x.roles.get("description", [])]
    acct = [x for x in atts.values() if x.kind == "event" and x.content == desc]
    status = wm.occurrence_status(world, occ, T(5))
    print(f"  {world}:")
    print(f"    describes link visible: {[(x.world, start(x)) for x in link]}")
    print(f"    account visible:        {[(x.world, start(x)) for x in acct]}")
    print(f"    descriptions():         {wm.descriptions(world, occ)}")
    span = wm.interval(world, desc)
    print(f"    interval():             {span[0].earliest.isoformat() if span else None}")
    print(f"    occurrence_status:      status {status['status']!r}; account "
          f"{[d['account'] for d in status['descriptions'] if d['description'] == desc]}")
    print(f"    occurrence() roles:     {wm.occurrence(world, occ)['participants']}")
    return wm.descriptions(world, occ), wm.interval(world, desc), status


print("A. Minimal reproduction (throwaway database)")
driver = connect()
DB = f"wm-probe-pre-e-d-links-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(DB, driver=driver, modules=CORE_MODULES, clock=Clock())
try:
    w = wm.create_world("actual", id="w")
    wm.add_entity("physical-object", "box", id="box")
    wm.add_entity("occurrence", "the pickup", id="o")
    wm.account(w, {"patient": "box"}, T(5), occurrence="o", id="ev-pickup")          # the system's account, day 5
    wm.declare_existence(w, "o", start=T(5), end=T(6))
    early = wm.create_world("plan-early", kind="hypothetical", base=w, branch_at=T(2), id="plan-early")
    late = wm.create_world("plan-late", kind="hypothetical", base=w, branch_at=T(6), id="plan-late")
    # the same, with the link given the event's own start: then it is not inherited by the early plan either
    wm.add_entity("occurrence", "the drop", id="o2")
    wm.account(w, {"patient": "box"}, T(5), id="ev-drop")
    wm.describe_occurrence(w, "ev-drop", "o2", start=T(5))
    early2 = wm.create_world("plan-early-2", kind="hypothetical", base=w, branch_at=T(2), id="plan-early-2")
    print("\n  occurrence o, description ev-pickup (account day 5, link with no start):")
    d_w, i_w, _ = show_world(wm, w, "o", "ev-pickup")
    d_e, i_e, s_e = show_world(wm, early, "o", "ev-pickup")
    d_l, i_l, _ = show_world(wm, late, "o", "ev-pickup")
    print("\n  occurrence o2, description ev-drop (account day 5, link from day 5):")
    d_e2, _, _ = show_world(wm, early2, "o2", "ev-drop")
    assert d_w == d_e == d_l == ["ev-pickup"]                        # the link is inherited by both plans
    assert i_w is not None and i_l is not None and i_e is None       # the account only before the branch
    assert [d["account"] for d in s_e["descriptions"]] == ["none"]
    assert d_e2 == []                                                 # a link with a start follows the account
finally:
    driver.databases.get(DB).delete()

print("\nB. Every reference case (database %s)" % a.db)
wm = WorldModel(connect(), a.db)
with wm._reading() as tx:
    worlds = sorted({q.opt(r, "id") for r in q.rows(tx, "match $w isa world, has wm-id $id;")})
    branch = {q.opt(r, "v"): q.opt(r, "at") for r in q.rows(tx, """match $br isa branching (base: $b, variant: $vw),
        has branch-at $at; $vw has wm-id $v;""")}
cases = 0
for world in worlds:
    atts = wm.visible(world)
    attesters = sorted({x.attester for x in atts.values()} - {"system"})
    knowledge = sorted({x.recorded_at for x in atts.values() if x.recorded_at is not None})
    early_k = knowledge[len(knowledge) // 2] if knowledge else None
    occs = sorted({x for at in atts.values() if at.kind == "describes" for x in at.roles.get("occurrence", [])})
    for occ in occs:
        for perspective, as_of in [("system", None)] + [(p, None) for p in attesters] + [("system", early_k)]:
            for d in wm.descriptions(world, occ, as_of, perspective):
                vis = wm.visible(world, as_of, perspective)
                if any(x.kind == "event" and x.content == d for x in vis.values()):
                    continue
                cases += 1
                links = [x for x in vis.values() if x.kind == "describes" and d in x.roles.get("description", [])]
                with wm._reading() as tx:
                    acct = [q.opt(r, "s") for r in q.rows(tx, """match $e isa event, has wm-id == $d;
                        $a isa attestation (content: $e), has valid-from-earliest $s;""", {"d": d})]
                status = wm.occurrence_status(world, occ, branch[world], as_of, perspective)
                ok = (all(x.start is None for x in links) and acct and min(acct) >= branch[world]
                      and wm.interval(world, d, as_of, perspective) is None
                      and [x["account"] for x in status["descriptions"] if x["description"] == d] == ["none"])
                print(f"  {world} {occ} {d} [{perspective}{', earlier' if as_of else ''}]: link start "
                      f"{[start(x) for x in links]}, account starts {min(acct).isoformat() if acct else None}, "
                      f"branch {branch[world].isoformat()}; interval None, occurrence_status account 'none': {ok}")
                assert ok
print(f"  cases: {cases}; every one is an inherited link with no start whose account starts after the branch point, "
      "and no interval or status is taken from it")
