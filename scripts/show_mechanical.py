"""Stage D-1 demonstration (LABS-1.023): the mechanical profile on the gearbox world.

    uv run python -I scripts/show_mechanical.py [--database wm-reference-gearbox-d1] [--drop]

Builds the gearbox world (A1 + B1 dynamics) with the core dependency kinds and the mechanical profile, kept for
inspection unless --drop, then prints judged answers (WorldModel API) and the stored records (raw TypeQL, unjudged).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import CORE_MODULES, WorldModel, mechanical as m  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import gearbox as g  # noqa: E402
from worldmodel.model import READ  # noqa: E402

RAW = {
    "R1 part-of: the assembly structure as stored (whole, part, source, interval)": """
match $c isa part-of (whole: $w, part: $p); $w has wm-id $wid; $p has wm-id $pid;
  { $w has wm-id "gbx-100"; } or { $w has wm-id "shaft-asm-in"; };
  $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "whole": $wid, "part": $pid, "by": $by, "from": $a.valid-from-earliest, "until": $a.valid-to-earliest };""",
    "R2 connected-to: connections with their joint kind and interval": """
match $c isa connected-to; $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "endpoints": [ match $c links (endpoint: $e); $e has wm-id $eid; fetch { "id": $eid }; ],
        "joint": [ match $c links (joint-kind: $k); $k has wm-id $kid; fetch { "id": $kid }; ],
        "by": $by, "from": $a.valid-from-earliest, "until": $a.valid-to-earliest };""",
    "R3 depends-on: every dependency, typed or not, with its source and polarity": """
match $c isa depends-on (dependent: $x, dependee: $y); $x has wm-id $xid; $y has wm-id $yid;
  $a isa attestation (content: $c, attester: $who, context: $w), has polarity $pol; $who has wm-id $by;
  $w has wm-id $wid;
fetch { "dependent": $xid, "dependee": $yid, "polarity": $pol, "by": $by, "world": $wid,
        "kind": [ match $c links (kind: $k); $k has wm-id $kid; fetch { "id": $kid }; ] };""",
    "R4 replacement descriptions: removed and fitted parts, source, occurrence links": """
match $e isa replacement (removed: $r, fitted: $f), has wm-id $eid; $r has wm-id $rid; $f has wm-id $fid;
  $a isa attestation (content: $e, attester: $who); $who has wm-id $by;
fetch { "event": $eid, "removed": $rid, "fitted": $fid, "by": $by,
        "describes": [ match $d isa describes (description: $e, occurrence: $o); $o has wm-id $oid;
                       fetch { "occurrence": $oid }; ] };""",
}


def s(x):
    return x.value if hasattr(x, "value") else x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--database", default="wm-reference-gearbox-d1")
    ap.add_argument("--drop", action="store_true")
    a = ap.parse_args()
    wm = WorldModel.create(a.database, modules=CORE_MODULES, replace=True)
    try:
        wm.install_profile("mechanical")
        ids = g.extend_mechanical(wm, g.extend_dynamics(wm, g.build(wm)))
        w = ids["world"]
        print(f"# Mechanical profile on the gearbox (database {a.database!r})\n")
        print(f"Profiles installed: {wm.profiles()}\n")
        print("## Part 1: judged answers (WorldModel API, system perspective unless stated)")

        print("\n### Q1 Assembly structure (core part-of; classification as assembly is vocabulary)")
        for x in ("gbx-100", "shaft-asm-in"):
            kinds = sorted(c for f in wm.facts_about(w, x, g.AFTER) if f["type"] == "classified-as"
                           for c in f["roles"]["class"])
            print(f"- {x} classified {kinds}; parts after the repair: {wm.parts(w, x, g.AFTER)}")
        print(f"- shaft-asm-in parts before the repair: {wm.parts(w, 'shaft-asm-in', g.BEFORE)}")

        print("\n### Q2 Connections (symmetric, typed, timed; not parthood)")
        for when, t in (("before the repair", g.BEFORE), ("after the repair", g.AFTER)):
            got = [(c["other"], c["joint_kind"], s(c["status"])) for c in m.connections(wm, w, "input-shaft", t)]
            print(f"- input-shaft, {when}: {got}")
        print(f"- cover: {[(c['other'], c['joint_kind']) for c in m.connections(wm, w, 'cover', g.AFTER)]}")

        print("\n### Q3 Typed dependencies; an untyped (historical) claim stays unspecified")
        for x in ("output-shaft", "gear-in", "gbx-100", "test-rig", "gear-out"):
            print(f"- {x} depends on: {[(d['dependee'], d['kind'], s(d['status'])) for d in wm.direct_dependencies(w, x, g.AFTER)]}")
        print(f"- output-shaft, as known before kinds were recorded: "
              f"{[(d['dependee'], d['kind']) for d in wm.direct_dependencies(w, 'output-shaft', g.AFTER, as_of=ids['known_before_kinds'])]}")
        for kind in (None, "dependency:functional", "dependency:physical"):
            print(f"- dependencies(output-shaft, kind={kind}): {wm.dependencies(w, 'output-shaft', g.AFTER, kind=kind)}")
        print(f"- dependency vs parthood: gear-in depends on input-shaft physically; parts(gear-in) = "
              f"{wm.parts(w, 'gear-in', g.AFTER)}, and both are parts of shaft-asm-in")

        print("\n### Q4 Component replacement: account, occurrence and claimed effects kept apart")
        r = m.replacement(wm, w, "ev-cmms-replacement", g.AFTER)
        print(f"- ev-cmms-replacement (by cmms): account {r['account']}, removed {r['removed']}, fitted {r['fitted']},"
              f" occurrences {[(o['occurrence'], o['status']) for o in r['occurrences']]}")
        for e in r["effects"]:
            print(f"  - claimed {e['kind']} part-of{e['outcome']} by {e['claimed_by']}: claim {e['claim']}; holds"
                  f" before {e['before']}, after {e['after']}")

        print("\n### Q5 Historical state before and after the replacement")
        for part in ("bearing-1", "bearing-3"):
            for when, t in (("before", g.BEFORE), ("after", g.AFTER)):
                h = wm.holds(w, "part-of", {"part": part, "whole": "shaft-asm-in"}, t)
                print(f"- part-of({part}, shaft-asm-in) {when}: {s(h.status)} {h.holds}")

        print("\n### Q6 Perspective disagreement")
        for p in ("system", "inspector"):
            r = m.replacement(wm, w, "ev-inspector-replacement", g.AFTER, perspective=p)
            print(f"- {p}: inspector's replacement account {r['account']} (removed {r['removed']})")
            key = {"dependent": "gear-out", "dependee": "bearing-2", "kind": "dependency:functional"}
            h = wm.holds(w, "depends-on", key, g.AFTER, perspective=p)
            print(f"  gear-out functionally depends on bearing-2: {s(h.status)} {h.holds}")

        later = g.PROFILE_AT.replace(hour=12)
        print(f"\n### Q7 Hypothetical control upgrade (plan stipulated from {g.PROFILE_AT:%m-%d %H:%M}; asked at {later:%m-%d %H:%M})")
        for label, world in (("actual", w), (ids["plan_rig_control"], ids["plan_rig_control"])):
            print(f"- {label}: test-rig depends on "
                  f"{[(d['dependee'], d['kind'], s(d['status'])) for d in wm.direct_dependencies(world, 'test-rig', later)]}")

        print("\n## Part 2: raw TypeQL against the stored records (not judged)")
        with wm.driver.transaction(wm.database, READ) as tx:
            for label, query in RAW.items():
                print(f"\n### {label}\n```\n{query.strip()}\n```")
                for line in sorted(json.dumps(d, sort_keys=True, default=str) for d in q.documents(tx, query.strip())):
                    print(f"  {line}")
    finally:
        if a.drop:
            wm.driver.databases.get(a.database).delete()


if __name__ == "__main__":
    main()
