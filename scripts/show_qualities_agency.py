"""Stage C demonstration (LABS-1.018): the same quality, measurement and capability semantics in two domains.

    uv run python -I scripts/show_qualities_agency.py [--drop]

Builds two databases, kept for inspection unless --drop:
  wm-reference-gearbox-c  the gearbox workshop (A1 + B1 + Stage C extension);
  wm-reference-lab        the laboratory (C1 + C2 extension).
Asks each the same questions through the WorldModel API (judged, system perspective unless stated), then shows the
stored records with raw TypeQL (nothing judged: no acceptance, perspective or time applied).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import QUALITY_MODULES, WorldModel  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import gearbox as g  # noqa: E402
from worldmodel.examples import lab  # noqa: E402
from worldmodel.model import READ  # noqa: E402

RAW = {
    "R1 rests-on: each attestation and the record it rests on, with the record's own raw value, unit and conditions": """
match $l isa rests-on (attestation: $a, record: $r); $a has wm-id $aid; $a links (attester: $who); $who has wm-id $by;
      $r has wm-id $rid, has raw-value $v; expressed-in (record: $r, unit: $u); $u has wm-id $uid;
fetch { "attestation": $aid, "by": $by, "record": $rid, "raw": $v, "unit": $uid, "conditions": [ $r.condition ] };""",
    "R2 produced: which activity produced which record (a proposition, attested)": """
match $p isa produced (activity: $e, result: $r); $e has wm-id $eid; $r has wm-id $rid;
      $a isa attestation (content: $p, attester: $who); $who has wm-id $by;
fetch { "activity": $eid, "record": $rid, "by": $by };""",
    "R3 capability and role grants: classified-as with a capability or social role, its context and interval": """
match $c isa classified-as (classified: $h, class: $k); $h has wm-id $hid; $k has wm-id $kid;
      { $k isa capability; } or { $k isa social-role; } or { $k isa category, has wm-id "agent"; };
      $a isa attestation (content: $c, attester: $who, context: $w), has polarity $pol,
         has valid-from-earliest $from; $who has wm-id $by; $w has wm-id $wid;
fetch { "holder": $hid, "class": $kid, "context": [ match $c links (context: $x); $x has wm-id $xid; fetch { "id": $xid }; ],
        "polarity": $pol, "from": $from, "until": $a.valid-to-earliest, "by": $by, "world": $wid };""",
}


def rng(m):
    return "[" + " .. ".join(f"{x:.3f}" for x in m["range"]) + "]" if m.get("range") else "?"


def show_measurements(wm, w, bearer, quality, at, **kw):
    c = wm.compare_measurements(w, bearer, quality, at, **kw)
    print(f"- status {c['status'].value}")
    for label, xs in (("measurements (usable)", c["measurements"]), ("alternatives", c["alternatives"]),
                      ("statements (no record)", c["statements"])):
        for x in xs:
            recs = "; ".join(f"record {r['record']}: {r['raw_value']} {r['raw_unit']} u={r['standard_uncertainty']} "
                             f"k={r['coverage_factor']} conditions {r['conditions']} instrument "
                             f"{[i for a in r['activities'] for i in a['instrument']]}" for r in x["records"])
            print(f"  - {label}: {x['attestation']} by {x['attester']} ({x['basis']}, {x['acceptance']}) "
                  f"SI {rng(x)} {('<- ' + recs) if recs else ''}")
    for p in c["pairs"]:
        print(f"  - pair {p['a']} / {p['b']}: {p['relation']}" + (f" ({p['reason']})" if p["reason"] else ""))


def cap(wm, w, holder, capability, at, context=None, **kw):
    c = wm.capable(w, holder, capability, at, context, **kw)
    judged = [(h["context"], h["judgement"]) for h in c["applicable"]]
    extra = f", held only in {c['only_in']}" if c["only_in"] else ""
    return f"{c['judgement']}: holds {c['holds']} [{c['status'].value}] applicable {judged}{extra}"


def action(wm, w, event, capability, context, **kw):
    c = wm.check_action(w, event, capability, context, **kw)
    actors = "; ".join(f"{a['actor']}: agent {a['agent']['holds'] if a['agent'] else None}, {capability} in {context} "
                       f"{a['capability']['holds'] if a['capability'] else None}" for a in c["actors"])
    occ = [(o["occurrence"], o["status"]) for o in c["occurrences"]]
    return (f"account {c['account']}, kinds {c['kinds']}, occurrences {occ or 'none claimed'}; {actors}")


def gearbox_world(name):
    wm = WorldModel.create(name, modules=QUALITY_MODULES, replace=True)
    ids = g.build(wm)
    g.extend_dynamics(wm, ids)
    return wm, g.extend_qualities_agency(wm, ids)


def lab_world(name):
    wm = WorldModel.create(name, modules=QUALITY_MODULES, replace=True)
    return wm, lab.extend_lab_agency(wm, lab.build_lab(wm))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drop", action="store_true")
    a = ap.parse_args()
    gw, gids = gearbox_world("wm-reference-gearbox-c")
    lw, lids = lab_world("wm-reference-lab")
    try:
        G, L = gids["world"], lids["world"]
        print("# Stage C: qualities, measurement and capabilities in two domains\n")
        print("Databases `wm-reference-gearbox-c` (workshop) and `wm-reference-lab` (laboratory). Everything below is"
              " printed by `scripts/show_qualities_agency.py`.\n")
        print("## Part 1: judged answers (WorldModel API)")

        print("\n### Q1 What is the mass, and on what evidence? (each attestation with its own records)")
        print("**Workshop: housing mass, 11-06 12:00**")
        show_measurements(gw, G, "housing", "mass", g.AFTER)
        print("**Laboratory: sample-12 mass, 11-10 15:00**")
        show_measurements(lw, L, "sample-12", lids["mass"], lab.T(15))

        print("\n### Q2 Units: the same conversion rules in both worlds")
        print(f"- workshop: 12410 g = {gw.convert(12410.0, 'g'):.3f} kg; lab: 3490 g = {lw.convert(3490.0, 'u-g'):.3f}"
              f" kg; 20 degC = {lw.convert(20.0, 'u-degC'):.2f} K")
        try:
            lw.convert(1.0, "u-kg", to="u-m")
        except ValueError as e:
            print(f"- refused across dimensions: {e}")

        print("\n### Q3 Who can do what, and where? (capabilities are contextual and timed)")
        at = g.REPLACEMENT[0]
        for holder, capability, ctx in (("technician", "can-replace-bearing", "workshop"),
                                        ("technician", "can-replace-bearing", None),
                                        ("apprentice", "can-replace-bearing", "workshop"),
                                        ("inspector", "can-sign-off", "bay-1"),
                                        ("bearing-press", "can-press-bearing", None)):
            print(f"- workshop {at:%m-%d %H:%M}: {holder} {capability} in {ctx}: {cap(gw, G, holder, capability, at, ctx)}")
        for holder, capability, ctx, t in (("ana", "can-weigh", "lab-1", lab.T(9)), ("ana", "can-weigh", "lab-2", lab.T(9)),
                                           ("bo", "can-weigh", "lab-1", lab.T(11)), ("bo", "can-weigh", "lab-1", lab.T(13)),
                                           ("tom", "can-weigh", "lab-1", lab.T(14)),
                                           ("balance-b3", "can-measure-mass", None, lab.T(9))):
            print(f"- lab {t:%H:%M}: {holder} {capability} in {ctx}: {cap(lw, L, holder, capability, t, ctx)}")

        print("\n### Q4 Agency and roles (classifications, not types)")
        for wm, w, who, t in ((gw, G, "apprentice", g.T1), (gw, G, "bearing-press", g.T1), (lw, L, "tom", lab.T(14)),
                              (lw, L, "balance-b3", lab.T(14))):
            roles = [(r["role"], r["context"]) for r in wm.roles_of(w, who, t)]
            print(f"- {who}: agent {wm.is_agent(w, who, t)['holds']}; roles {roles}")

        print("\n### Q5 Actions: what the records say, without concluding that anything happened or was allowed")
        print(f"- workshop ev-worklog-replacement: "
              f"{action(gw, G, 'ev-worklog-replacement', 'can-replace-bearing', 'workshop')}")
        print(f"- workshop ev-apprentice-fits: {action(gw, G, 'ev-apprentice-fits', 'can-replace-bearing', 'workshop')}")
        print(f"- lab ev-tom-weighs: {action(lw, L, 'ev-tom-weighs', 'can-weigh', 'lab-1')}")
        print("- capability without action: the inspector can sign off on 11-06, and has no action that day: "
              f"{gw.actions_of(G, 'inspector', g.AFTER, g.AFTER.replace(hour=23))}")

        print("\n### Q6 Perspectives, knowledge time and hypothetical worlds")
        print("**Laboratory, the external lab's perspective:**")
        show_measurements(lw, L, "sample-12", lids["mass"], lab.T(15), perspective="lab-2")
        print("**Laboratory, as known before the correction:**")
        show_measurements(lw, L, "sample-12", lids["mass"], lab.T(15), as_of=lids["known_before_correction"])
        print(f"- lab plan {lids['plan_tom']!r}: tom can-weigh in lab-1 at 14:00: "
              f"{cap(lw, lids['plan_tom'], 'tom', 'can-weigh', lab.T(14), 'lab-1')}; actual: "
              f"{cap(lw, L, 'tom', 'can-weigh', lab.T(14), 'lab-1')}")
        pt = g.PLAN_AT.replace(hour=12)
        print(f"- workshop plan {gids['plan_apprentice']!r}: apprentice can-replace-bearing in workshop: "
              f"{cap(gw, gids['plan_apprentice'], 'apprentice', 'can-replace-bearing', pt, 'workshop')}; actual: "
              f"{cap(gw, G, 'apprentice', 'can-replace-bearing', pt, 'workshop')}")

        print("\n## Part 2: raw TypeQL against the stored records (not judged)")
        for label, wm in (("workshop", gw), ("laboratory", lw)):
            print(f"\n### {label}")
            with wm.driver.transaction(wm.database, READ) as tx:
                for title, query in RAW.items():
                    print(f"\n#### {title}\n```\n{query.strip()}\n```")
                    for line in sorted(json.dumps(d, sort_keys=True, default=str) for d in q.documents(tx, query.strip())):
                        print(f"  {line}")
    finally:
        if a.drop:
            for wm in (gw, lw):
                wm.driver.databases.get(wm.database).delete()


if __name__ == "__main__":
    main()
