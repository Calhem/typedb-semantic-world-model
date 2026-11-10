"""Stage A2 demonstration (LABS-1.007): derived spatial relationships in the gearbox reference world.

    uv run python -I scripts/show_spatial_reasoning.py [--database wm-reference-gearbox] [--drop]

Builds the reference world with its A2 extensions in TypeDB (the database is kept for inspection unless --drop),
then prints:
  Part 1, judged answers (WorldModel API): positions derived through frame chains, with every transform used, and the
          judgement of position claims, across time, perspectives and a hypothetical world;
  Part 2, raw TypeQL: the stored records the answers were judged from (no time, acceptance or perspective applied).
At the end the system accepts the tag reader's claim, to show a conflict appear (and not appear for earlier knowledge).
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import PHYSICAL_MODULES, WorldModel  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import gearbox as g  # noqa: E402
from worldmodel.model import READ  # noqa: E402
from worldmodel.spatial import angle_about_z  # noqa: E402

RAW = {
    "R1 frames reachable from f-gearbox by the TypeDB function frames_linked (records, actual world)": """
match $f isa spatial-frame, has wm-id "f-gearbox"; $w isa world, has wm-id "actual";
      let $g in frames_linked($f, $w); $g has wm-id $id;
fetch { "frame": $id };""",
    "R2 every frame-transform record with its world, source and stated interval": """
match $c isa frame-transform (parent: $p, child: $ch), has tx $tx, has ty $ty, has qw $qw, has qz $qz;
      $p has wm-id $pid; $ch has wm-id $cid;
      $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid; $w has wm-id $wid; $who has wm-id $by;
fetch { "parent": $pid, "child": $cid, "tx": $tx, "ty": $ty, "qw": $qw, "qz": $qz, "world": $wid, "by": $by,
        "attestation": $aid, "from": $a.valid-from-earliest, "until": $a.valid-to-earliest };""",
    "R3 every position record of gbx-100 (all frames and sources)": """
match $x isa physical-object, has wm-id "gbx-100";
      $c isa positioned-in (positioned: $x, frame: $f), has x-min $x0, has x-max $x1, has y-min $y0, has y-max $y1;
      $f has wm-id $fid; $a isa attestation (content: $c, attester: $who), has wm-id $aid, has basis $b;
      $who has wm-id $by;
fetch { "frame": $fid, "x": $x0, "x_max": $x1, "y": $y0, "y_max": $y1, "by": $by, "basis": $b, "attestation": $aid };""",
}


def rng(r):
    return f"{r[0]:.3f}" if abs(r[0] - r[1]) < 1e-9 else f"{r[0]:.3f}..{r[1]:.3f}"


def box(c):
    return f"x {rng(c['x'])}, y {rng(c['y'])}, z {rng(c['z'])}"


def show_where(wm, world, thing, frame, t, label, **kw):
    a = wm.where(world, thing, frame, t, **kw)
    who = kw.get("perspective", "system")
    print(f"\n### {label}\n`where({world!r}, {thing!r}, {frame!r}, {t:%Y-%m-%d %H:%M}, perspective={who!r})`"
          f" -> **{a['status'].value}**, judgement: {a['judgement']}")
    for i, c in enumerate(a["candidates"]):
        how = "stated in this frame" if c["direct"] else f"derived ({c['rule']}) from a position stated in {c['stated_in']}"
        print(f"- candidate {i}: {box(c)} m [{c['status'].value}], {how}; position attestation(s) {c['position_support']}")
        for s in c["chain"]:
            print(f"    via {s['child']} -> {s['parent']} ({s['direction']}): t = {tuple(round(v, 4) for v in s['translation'])},"
                  f" rotation {math.degrees(angle_about_z(s['rotation'])):.0f} deg about z; attestation(s) {s['support']}")
        if c["chains"] > 1:
            print(f"    ({c['chains']} chains, all agreeing within 1e-9 m)")
    for i, j in a["conflicts"]:
        print(f"- conflict: candidates {i} and {j} are disjoint")
    for inc in a["incomparable"]:
        print(f"- incomparable: a position stated in {inc['frame']} ({inc['support']}): {inc['reason']}")
    if a["alternatives"]:
        print(f"- unreviewed alternatives (not part of this perspective's answer): {list(a['alternatives'])}")
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--database", default="wm-reference-gearbox")
    ap.add_argument("--drop", action="store_true")
    a = ap.parse_args()
    wm = WorldModel.create(a.database, modules=PHYSICAL_MODULES, replace=True)
    try:
        ids = g.extend_spatial(wm, g.build(wm))
        w, plan = ids["world"], ids["bench_plan"]
        print(f"# Spatial reasoning in the reference world (database {a.database!r})\n")
        print("## Part 1: judged answers (WorldModel API)")
        r = wm.transform_between(w, "f-gearbox", "f-workshop", g.AFTER)
        print(f"\n### How the gearbox frame sits in the workshop frame at {g.AFTER:%Y-%m-%d %H:%M}\n"
              f"`transform_between('actual', 'f-gearbox', 'f-workshop')` -> **{r['status'].value}**: origin at "
              f"{tuple(round(v, 4) for v in r['transform'].t)}, rotated "
              f"{math.degrees(angle_about_z(r['transform'].q)):.0f} deg about z, via {' -> '.join(r['chains'][0]['frames'])}")
        show_where(wm, w, "gbx-100", "f-workshop", g.AFTER, "Q1 Where is the gearbox relative to the workshop?")
        show_where(wm, w, "gear-in", "f-bench", g.AFTER, "Q2 Where is the pinion relative to the workbench?")
        show_where(wm, w, "gear-in", "f-workshop", g.AFTER, "Q2b ... and relative to the workshop (two hops)?")
        show_where(wm, w, "bench-1", "f-gearbox", g.AFTER,
                   "Q2c Where is the bench relative to the gearbox (inverse chain, with ranges)?")
        show_where(wm, w, "gbx-100", "f-workshop", g.LATER,
                   "Q3 What changes when the workshop -> bench transform changes (the bench moved at T2)?")
        show_where(wm, w, "gear-in", "f-bench", g.LATER, "Q3b ... the pinion relative to the bench does not change")
        show_where(wm, plan, "gbx-100", "f-workshop", g.LATER, "Q3c ... and in the plan world (bench by the door)")
        show_where(wm, w, "gbx-100", "f-workshop", g.AFTER,
                   "Q4 Which claims agree or conflict? The tag reader's own perspective", perspective="tag-reader")
        print("\n### Q4b The system now accepts the tag reader's claim")
        before = wm.clock()
        wm.accept(ids["tag_position"])
        print(f"`accept({ids['tag_position']!r})` recorded after {before:%Y-%m-%d %H:%M:%S} (transaction time)")
        show_where(wm, w, "gbx-100", "f-workshop", g.AFTER, "Q4c ... the same question now")
        show_where(wm, w, "gbx-100", "f-workshop", g.AFTER, "Q4d ... as known before that acceptance", as_of=before)
        show_where(wm, w, "gbx-100", "f-workshop", g.BEFORE, "Q5 Earlier in time, before the observations")
        print("\n## Part 2: raw TypeQL against the stored records (not judged)")
        with wm.driver.transaction(wm.database, READ) as tx:
            for label, query in RAW.items():
                print(f"\n### {label}\n```\n{query.strip()}\n```")
                for line in sorted(json.dumps(d, sort_keys=True) for d in q.documents(tx, query.strip())):
                    print(f"  {line}")
    finally:
        if a.drop:
            wm.driver.databases.get(a.database).delete()


if __name__ == "__main__":
    main()
