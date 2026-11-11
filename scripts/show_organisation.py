"""Stage D-2 demonstration (LABS-1.026): the organisational profile on the Acme reference world.

    uv run python -I scripts/show_organisation.py [--database wm-reference-organisation] [--drop]

Builds the Acme world (examples/organisation.py) with the organisation profile, kept for inspection unless --drop,
then prints judged answers (WorldModel API and worldmodel.organisation) and the stored records (raw TypeQL, unjudged).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import CORE_MODULES, WorldModel, organisation as o  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import organisation as ex  # noqa: E402
from worldmodel.model import READ  # noqa: E402

T = ex.T
RAW = {
    "R1 employment and membership, with source and interval": """
match { $c isa employment (employer: $x, employee: $y); } or { $c isa member-of (group: $x, member: $y); };
  $c isa! $t; $x has wm-id $xid; $y has wm-id $yid;
  $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "type": $t, "of": $xid, "who": $yid, "by": $by, "from": $a.valid-from-earliest, "until": $a.valid-to-earliest };""",
    "R2 office appointments: holder, office, context, source, polarity, interval, acceptance verdicts": """
match $c isa office-holding (classified: $p, class: $k, context: $x); $p has wm-id $pid; $k has wm-id $kid;
  $x has wm-id $xid; $a isa attestation (content: $c, attester: $who, context: $w), has polarity $pol;
  $who has wm-id $by; $w has wm-id $wid;
fetch { "holder": $pid, "office": $kid, "context": $xid, "by": $by, "polarity": $pol, "world": $wid,
        "from": $a.valid-from-earliest, "until": $a.valid-to-earliest,
        "verdicts": [ match $v isa acceptance (accepted: $a, holder: $h), has verdict $vd; $h has wm-id $hid;
                      fetch { "holder": $hid, "verdict": $vd }; ] };""",
    "R3 single-holder constraints": """
match $c isa exclusive-office (office: $k, context: $x); $k has wm-id $kid; $x has wm-id $xid;
  $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "office": $kid, "context": $xid, "by": $by, "from": $a.valid-from-earliest };""",
    "R4 authorisations: grantor and reporting source side by side": """
match $c isa authorisation (grantor: $g, holder: $h, power: $p, scope: $s); $g has wm-id $gid; $h has wm-id $hid;
  $p has wm-id $pid; $s has wm-id $sid; $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "grantor": $gid, "holder": $hid, "power": $pid, "scope": $sid, "reported by": $by };""",
    "R5 official acts and the occurrences they are said to describe": """
match $e isa official-act (official: $p, office: $k, office-context: $x), has wm-id $eid; $p has wm-id $pid;
  $k has wm-id $kid; $x has wm-id $xid; $a isa attestation (content: $e, attester: $who); $who has wm-id $by;
fetch { "act": $eid, "official": $pid, "office": $kid, "context": $xid, "by": $by,
        "describes": [ match describes (description: $e, occurrence: $o); $o has wm-id $oid; fetch { "id": $oid }; ] };""",
}


def s(x):
    return x.value if hasattr(x, "value") else x


def show_office(wm, w, office, context, day, **kw):
    v = o.office_holders(wm, w, office, context, T(day), **kw)
    apps = ", ".join(f"{a['holder']} {a['judgement']}" for a in v["appointments"])
    conflict = ""
    if v["conflict"]:
        conflict = (f"; CONFLICT: constraint {v['conflict']['constraint']['support']}, appointments "
                    f"{[(a['holder'], a['attestations']) for a in v['conflict']['appointments']]}")
    return f"holders {v['holders']} [{s(v['status'])}]; appointments: {apps or 'none'}{conflict}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--database", default="wm-reference-organisation")
    ap.add_argument("--drop", action="store_true")
    a = ap.parse_args()
    wm = WorldModel.create(a.database, modules=CORE_MODULES, replace=True)
    try:
        wm.install_profile("organisation")
        ids = ex.build_organisation(wm)
        w = ids["world"]
        print(f"# Organisational profile: Acme and depot 7 (database {a.database!r})\n")
        print(f"Profiles installed: {wm.profiles()}\n")
        print("## Part 1: judged answers (system perspective unless stated)")

        print("\n### Q1 Employment and membership")
        print(f"- acme employs, day 5: {[(e['employee'], e['judgement'], s(e['status'])) for e in o.employment(wm, w, 'acme', T(5))]}")
        print(f"- eve's employment on day 25 (ended day 20): {[(e['employer'], e['judgement']) for e in o.employment(wm, w, 'eve', T(25))]}")
        for p in ("bea", "cal", "dan"):
            h = wm.holds(w, "member-of", {"member": p, "group": "depot-7"}, T(5))
            print(f"- {p} member of depot-7: {s(h.status)} {h.holds}")

        print("\n### Q2 Contextual appointments: site manager of depot-7 (exclusive) and safety officer (not exclusive)")
        for day in (5, 9, 12):
            print(f"- site manager, day {day}: {show_office(wm, w, 'site-manager', 'depot-7', day)}")
        print(f"- safety officer, day 5: {show_office(wm, w, 'safety-officer', 'depot-7', 5)}")
        print(f"- offices of cal, day 9: {[(x['office'], x['context'], x['judgement'], s(x['status'])) for x in o.offices_of(wm, w, 'cal', T(9))]}")
        print(f"- offices of fay, day 7 (an appointment event exists, no appointment claim): {o.offices_of(wm, w, 'fay', T(7))}")
        h = wm.holds(w, "office-holding", {"classified": "eve", "class": "site-manager", "context": "depot-7"}, T(5))
        print(f"- is eve (never mentioned for it) site manager on day 5? {s(h.status)} {h.holds}: not inferred false")

        print("\n### Q3 Authority, capability and office (independent)")
        for p in ("bea", "dan", "eve", "cal"):
            au = o.authorised(wm, w, p, "can-sign-off", "depot-7", T(5))
            ca = wm.capable(w, p, "can-sign-off", T(5), "depot-7")
            grants = [(g["grantor"], g["reported_by"], g["judgement"]) for g in au["grants"]]
            print(f"- {p}: authority {au['judgement']} (grants: grantor, reported by: {grants}; grantor entitlement "
                  f"{au['grantor_entitlement']}); capability {ca['judgement']}")
        ac = o.authorised(wm, w, "acme", "can-sign-off", "depot-7", T(5))
        print(f"- was acme itself authorised to grant? {ac['judgement']} [{s(ac['status'])}]: not inferred from its grants")

        print("\n### Q4 Acts in office (occurrence judged apart)")
        for ev in ("ev-bea-signs", "ev-cal-signs"):
            r = o.official_act(wm, w, ev, power="can-sign-off")
            print(f"- {ev}: account {r['account']}; occurrences {[(x['occurrence'], x['status']) for x in r['occurrences']] or 'none claimed'};"
                  f" office {r['office_held']['judgement']} [{s(r['office_held']['status'])}]; authority "
                  f"{r['authority']['judgement']}; capability {r['capability']['judgement']}; agent {r['agent']}")

        print("\n### Q5 Perspectives, historical knowledge and a hypothetical reorganisation")
        print(f"- site manager day 9, the auditor's perspective: {show_office(wm, w, 'site-manager', 'depot-7', 9, perspective='auditor')}")
        print(f"- site manager day 9, as known before cal's appointment was recorded: "
              f"{show_office(wm, w, 'site-manager', 'depot-7', 9, as_of=ids['known_before_cal'])}")
        print(f"- site manager day 12 in {ids['plan']!r}: {show_office(wm, ids['plan'], 'site-manager', 'depot-7', 12)}")
        print(f"- site manager day 12, actual: {show_office(wm, w, 'site-manager', 'depot-7', 12)}")

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
