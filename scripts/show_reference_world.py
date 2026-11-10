"""Build the Stage A1 reference world (a gearbox in a workshop) in TypeDB and print it in a readable structure.

    uv run python -I scripts/show_reference_world.py [--database wm-reference-gearbox] [--drop]

The database is kept (for inspection, e.g. in TypeDB Studio) unless --drop is given. Part 1 prints the world through
the WorldModel API (judged answers: perspective, time and world aware). Part 2 runs raw TypeQL queries against the
stored records and prints their actual rows.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import PHYSICAL_MODULES, WorldModel  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import gearbox as g  # noqa: E402
from worldmodel.model import READ  # noqa: E402

QUERIES = {
    "Q1 components of the gearbox (direct part-of contents, any world)": """
match $g isa physical-object, has wm-id "gbx-100";
      $c isa part-of (whole: $g, part: $p); $p has wm-id $pid, has name $pn;
fetch { "part": $pid, "name": $pn };""",
    "Q2 transitive parts by the TypeDB function parts_in (actual world)": """
match $g isa physical-object, has wm-id "gbx-100"; $w isa world, has wm-id "actual";
      let $p in parts_in($g, $w); $p has wm-id $pid;
fetch { "part": $pid };""",
    "Q3 material classification records (every world and source: raw records, not judged answers)": """
match $m isa category, has wm-id "material";
      $k isa classified-as (classified: $mat, class: $m); $mat has wm-id $mid;
      $c isa classified-as (classified: $x, class: $mat); $x isa physical-object, has wm-id $xid;
fetch { "thing": $xid, "material": $mid };""",
    "Q4 positions in the gearbox frame, with the attesting source and interval": """
match $f isa spatial-frame, has wm-id "f-gearbox";
      $c isa positioned-in (positioned: $x, frame: $f), has x-min $x0, has y-min $y0, has z-min $z0;
      $x has wm-id $xid;
      $a isa attestation (content: $c, attester: $who), has valid-from-earliest $from; $who has wm-id $wid;
fetch { "thing": $xid, "x": $x0, "y": $y0, "z": $z0, "attester": $wid, "from": $from, "until": $a.valid-to-earliest };""",
    "Q5 frame transforms and anchors": """
match $c isa frame-transform (parent: $p, child: $ch), has tx $tx, has ty $ty, has tz $tz, has qw $qw, has qz $qz;
      $p has wm-id $pid; $ch has wm-id $cid;
fetch { "parent": $pid, "child": $cid, "tx": $tx, "ty": $ty, "tz": $tz, "qw": $qw, "qz": $qz };""",
    "Q6 what each frame is anchored to": """
match $c isa anchored-to (frame: $f, anchor: $x); $f has wm-id $fid; $x has wm-id $xid;
fetch { "frame": $fid, "anchor": $xid };""",
    "Q7 containment: things located at places that are part of the workshop": """
match $ws isa place, has wm-id "workshop";
      $p1 isa part-of (whole: $ws, part: $pl); $pl has wm-id $plid;
      $c isa located-at (place: $pl, located: $x); $x has wm-id $xid;
fetch { "place": $plid, "thing": $xid };""",
    "Q8 the housing's mass: two attestations, a measurement and a design value": """
match $h isa physical-object, has wm-id "housing";
      $c isa has-quality (bearer: $h), has lower $lo, has upper $hi;
      $a isa attestation (content: $c, attester: $who), has basis $b; $who has wm-id $wid;
fetch { "attester": $wid, "basis": $b, "lower": $lo, "upper": $hi };""",
}


def tree(node, names, depth=0):
    lines = [f"{'  ' * depth}- {node['id']} ({names.get(node['id'], '?')})"]
    for p in node["parts"]:
        lines += tree(p, names, depth + 1)
    return lines


def show_contents(c, depth=0):
    located = f"{', '.join(c['located'])} [{c['status']}]" if c["located"] else "(nothing located directly)"
    lines = [f"{'  ' * depth}- {c['place']}: {located}"]
    for sub in c["places"]:
        lines += show_contents(sub, depth + 1)
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--database", default="wm-reference-gearbox")
    ap.add_argument("--drop", action="store_true")
    a = ap.parse_args()
    wm = WorldModel.create(a.database, modules=PHYSICAL_MODULES, replace=True)
    try:
        ids = g.build(wm)
        w = ids["world"]
        names = wm.names([i for i, *_ in g.THINGS] + [i for i, *_ in g.PLACES] + [i for i, *_ in g.FRAMES])
        print(f"# Reference world in database {a.database!r}, world {w!r}")
        for label, t in (("before the bearing replacement", g.BEFORE), ("after it", g.AFTER)):
            print(f"\n## Composition of gbx-100 at {t:%Y-%m-%d %H:%M} ({label})")
            print("\n".join(tree(wm.composition(w, "gbx-100", t), names)))
        print("\n## Containment (workshop, at AFTER)")
        print("\n".join(show_contents(wm.contents(w, "workshop", g.AFTER))))
        print("\n## Materials (system perspective, AFTER)")
        for thing in ("housing", "cover", "gasket", "input-shaft", "bench-1"):
            print(f"- {thing}: {', '.join(wm.materials(w, thing, g.AFTER))}")
        print(f"- cover, inspector's perspective: {', '.join(wm.materials(w, 'cover', g.AFTER, perspective='inspector'))}")
        print(f"- cover, plan world {ids['plan']!r} at the plan time: "
              f"{', '.join(wm.materials(ids['plan'], 'cover', g.PLAN_AT))}")
        print("\n## Frames (AFTER)")
        for f, *_ in g.FRAMES:
            info = wm.frame_info(w, f, g.AFTER)
            print(f"- {f} ({info['name']}): anchored to {[x['anchor'] for x in info['anchored_to']]}")
            for p in info["parents"]:
                print(f"    in {p['parent']}: translation {p['translation']}, rotation {tuple(round(c, 6) for c in p['rotation'])}"
                      f" [{p['status'].value}]")
            print(f"    positioned in it: {', '.join(info['positioned'])}")
        print("\n## Positions of selected things (AFTER)")
        for thing in ("bench-1", "gbx-100", "gear-in", "bearing-1", "bearing-3"):
            ps = wm.poses(w, thing, g.AFTER)
            for p in ps:
                print(f"- {thing} in {p['frame']}: x {p['x']}, y {p['y']}, z {p['z']}, orientation {p['orientation']}"
                      f" [{p['status'].value}]")
            if not ps:
                print(f"- {thing}: no position holds")
        print("\n## Housing mass (AFTER)")
        mass = wm.value_at(w, "has-quality", "housing", g.AFTER, key_role="bearer", value_role="quality")
        print(f"- value_at(has-quality, housing): {mass.status.value}, support {list(mass.support)}")
        for f in wm.facts_about(w, "housing", g.AFTER):
            if f["type"] == "has-quality":
                print(f"- range {f['params']} [{f['status'].value}] from {f['support']}")
        print("\n## Raw TypeQL queries against the stored records")
        with wm.driver.transaction(wm.database, READ) as tx:
            for label, query in QUERIES.items():
                docs = q.documents(tx, query.strip())
                print(f"\n### {label}\n```\n{query.strip()}\n```")
                for line in sorted(json.dumps(d, sort_keys=True) for d in docs):
                    print(f"  {line}")
    finally:
        if a.drop:
            wm.driver.databases.get(a.database).delete()


if __name__ == "__main__":
    main()
