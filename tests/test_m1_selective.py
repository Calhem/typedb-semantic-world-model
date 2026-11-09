"""Milestone 1 regression requirement, ported to Core 0.3: the selective path (filters in TypeDB) gives exactly the
answers of the full-load reference path."""

import random
from datetime import timedelta

from conftest import T
from worldmodel import WorldModel


def build(wm, seed=7, objects=12, places=5, moves=6):
    rnd = random.Random(seed)
    w = wm.create_world("actual", id="actual")
    objs = [wm.add_entity("physical-object", f"o{i}", id=f"o{i}") for i in range(objects)]
    pls = [wm.add_entity("place", f"p{i}", id=f"p{i}") for i in range(places)]
    wm.add_entity("social-object", "matcher", id="matcher")
    for o in objs:
        wm.attest(w, "located-at", {"located": o, "place": rnd.choice(pls)}, start=T("08:00"), until_superseded=True)
    t = T("08:00")
    snapshots = [wm.clock.now]
    for step in range(moves * objects // 2):
        t += timedelta(minutes=rnd.randint(1, 9))
        wm.move(w, rnd.choice(objs), rnd.choice(pls), t)
        if step % 7 == 0:
            snapshots.append(wm.clock.now)
    link = wm.attest(w, "same-as", {"same": [objs[0], objs[1]]}, until_superseded=True, attester="matcher")
    wm.accept(link)
    wm.attest(w, "located-at", {"located": objs[2], "place": pls[0]}, start=T("09:00"), until_superseded=True)
    wm.deny(w, "located-at", {"located": objs[5], "place": pls[1]}, start=T("09:00"), until_superseded=True)
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("10:00"))
    wm.move(h, objs[3], pls[4], T("10:30"))
    wm.end(h, wm.history(w, objs[4], "located-at")[0]["attestation"], T("09:30"))
    return [w, h], objs, pls, snapshots, (T("07:30"), t + timedelta(minutes=30))


def test_selective_and_full_paths_agree(wm):
    wm.selective = True
    worlds, objs, pls, snapshots, (lo, hi) = build(wm)
    wm.stats = {"queries": 0, "attestations": 0}
    full = WorldModel.open(wm.database, driver=wm.driver)
    full.selective = False
    rnd = random.Random(1)
    times = [lo + (hi - lo) * i / 6 for i in range(7)]
    checked = 0
    for world in worlds:
        for o in objs:
            for t in times:
                as_of = rnd.choice(snapshots + [None])
                assert wm.value_at(world, "located-at", o, t, as_of) == full.value_at(world, "located-at", o, t, as_of)
                roles = {"located": o, "place": rnd.choice(pls)}
                assert wm.holds(world, "located-at", roles, t, as_of) == full.holds(world, "located-at", roles, t, as_of)
                checked += 2
    assert checked == 2 * 2 * len(objs) * len(times)
    assert wm.stats["attestations"] < full.stats["attestations"] / 5
