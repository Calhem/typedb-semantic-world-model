"""Stage D-3 demonstration (LABS-1.028): the laboratory profile on the laboratory reference world.

    uv run python -I scripts/show_laboratory.py [--database wm-reference-laboratory] [--drop]

Builds the laboratory world (examples/lab.py, then examples/laboratory.py) with all three domain profiles installed,
kept for inspection unless --drop, then prints judged answers (WorldModel API and worldmodel.laboratory) and the stored
records (raw TypeQL, unjudged).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import CORE_MODULES, WorldModel, laboratory as lb  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import laboratory as ex  # noqa: E402
from worldmodel.model import READ  # noqa: E402

T = ex.T
RAW = {
    "R1 samples and what each is said to be made from (source, interval, acceptance verdicts)": """
match $x isa sample, has wm-id $xid; $c isa constitution (constituted: $x, constituent: $y); $y has wm-id $yid;
  $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "sample": $xid, "from": $yid, "by": $by, "valid from": $a.valid-from-earliest,
        "verdicts": [ match $v isa acceptance (accepted: $a, holder: $h), has verdict $vd; $h has wm-id $hid;
                      fetch { "holder": $hid, "verdict": $vd }; ] };""",
    "R2 sampling accounts: sampler, specimen, product, source, and the occurrences they are said to describe": """
match $e isa sampling (sampler: $s, sampled: $f, product: $p), has wm-id $eid; $s has wm-id $sid;
  $f has wm-id $fid; $p has wm-id $pid; $a isa attestation (content: $e, attester: $who); $who has wm-id $by;
fetch { "account": $eid, "sampler": $sid, "from": $fid, "product": $pid, "by": $by,
        "describes": [ match describes (description: $e, occurrence: $o); $o has wm-id $oid; fetch { "id": $oid }; ] };""",
    "R3 calibration attestations: certificate (and its own reference), instrument, source, polarity, valid time": """
match $c isa calibration-of (certificate: $k, calibrated: $i); $k has wm-id $kid; $i has wm-id $iid;
  $a isa attestation (content: $c, attester: $who, context: $w), has polarity $pol; $who has wm-id $by;
  $w has wm-id $wid;
fetch { "certificate": $kid, "reference": $k.calibration-ref, "instrument": $iid, "by": $by, "polarity": $pol,
        "world": $wid, "from": $a.valid-from-earliest, "until": $a.valid-to-earliest,
        "rests on": [ match rests-on (attestation: $a, record: $r); $r has wm-id $rid; fetch { "id": $rid }; ] };""",
    "R4 result records: the calibration reference each states, and the instrument of the activity that produced it": """
match $r isa information-object, has wm-id $rid, has raw-value $v; $p isa produced (activity: $act, result: $r);
  $act has wm-id $aid; try { $act links (instrument: $i); $i has wm-id $iid; };
fetch { "record": $rid, "value": $v, "stated reference": $r.calibration-ref, "activity": $aid, "instrument": $iid };""",
    "R5 interpretations resting on result records: content, source, stance, basis": """
match $r isa information-object, has wm-id $rid; rests-on (attestation: $a, record: $r);
  $a isa attestation (content: $c, attester: $who), has stance $st, has basis $bs; $who has wm-id $by;
  $c isa classified-as (classified: $x, class: $k); $x has wm-id $xid; $k has wm-id $kid;
fetch { "record": $rid, "classified": $xid, "as": $kid, "by": $by, "stance": $st, "basis": $bs };""",
}


def s(x):
    return x.value if hasattr(x, "value") else x


def cal_line(wm, w, instrument, t, **kw):
    v = lb.calibration_status(wm, w, instrument, t, **kw)
    certs = ", ".join(f"{c['certificate']} ({c['reference']}) {c['judgement']}" for c in v["certificates"])
    return f"{v['judgement']} [{s(v['status'])}]; certificates: {certs or 'none recorded'}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--database", default="wm-reference-laboratory")
    ap.add_argument("--drop", action="store_true")
    a = ap.parse_args()
    wm = WorldModel.create(a.database, modules=CORE_MODULES, replace=True)
    try:
        for p in ("mechanical", "organisation", "laboratory"):
            wm.install_profile(p)
        ids = ex.build_laboratory(wm)
        w, mass, plan = ids["world"], ids["mass"], ids["plan_recal"]
        print(f"# Laboratory profile: sample 12, its sub-samples, calibration and interpretations (database {a.database!r})\n")
        print(f"Profiles installed: {wm.profiles()}\n")
        print("## Part 1: judged answers (system perspective unless stated)")

        print("\n### Q1 Samples: provenance, accounts, occurrences, existence (16:00)")
        pr = lb.provenance(wm, w, "s12-b", T(16))
        print(f"- s12-b is made from: {[(c['sample'], c['from'], c['judgement'], s(c['status'])) for c in pr['chain']]}")
        print(f"- s12-b's established ancestry (routes on which every link is established): "
              f"{[(c['sample'], c['from'], c['paths']) for c in pr['established']]}")
        for sample, accounts in pr["sampling"].items():
            for acc in accounts:
                print(f"- account {acc['event']} (product {sample}, by {acc['sampler']}): {acc['account']}; occurrences "
                      f"{[(o['occurrence'], o['status']) for o in acc['occurrences']]}; claimed effects "
                      f"{[(e['outcome'], e['claim']) for e in acc['claimed_effects']]}")
        c = lb.provenance(wm, w, "s12-c", T(16))
        print(f"- s12-c: accounts {[(x['event'], x['account'], [e['claim'] for e in x['claimed_effects']]) for x in c['sampling']['s12-c']]};"
              f" made from {c['chain'] or 'nothing attested'}; existence attested: {c['existence']['attested']['judgement']}")
        for t in (T(15), T(16)):
            e = lb.provenance(wm, w, "s12-a", t)["existence"]["attested"]
            print(f"- s12-a exists at {t:%H:%M}: {e['judgement']} [{s(e['status'])}] (a portion: the 15:30 split ends it)")
        print(f"- s12-b location at 16:00: {pr['location_at_t']['places']} [{s(pr['location_at_t']['status'])}]")

        print("\n### Q2 The experiment and its documented steps")
        print(f"- o-exp-1 is an experiment: {s(wm.holds(w, 'classified-as', {'classified': 'o-exp-1', 'class': lb.EXPERIMENT}, T(16)).status)}"
              f"; steps rest on {sorted({r for h in wm.history(w, 'o-exp-1') for r in wm.evidence_of(h['attestation'])})}")
        for st in wm.process_steps(w, "o-exp-1", T(16)):
            print(f"  - {st['occurrence']}: {st['descriptions']} by {st['actors']} from {st['start'].earliest:%H:%M}; "
                  f"occurred (at its start): {wm.occurrence_status(w, st['occurrence'], st['start'].earliest, details=False)['status']}")

        print("\n### Q3 Calibration status over time, by perspective, knowledge time and world")
        for inst, t in (("balance-b3", T(9)), ("balance-b3", T(15)), ("balance-b7", T(10)), ("balance-b9", T(12))):
            print(f"- {inst} at {t:%H:%M}: {cal_line(wm, w, inst, t)}")
        print(f"- balance-b7 at 10:00, the quality office's perspective: {cal_line(wm, w, 'balance-b7', T(10), perspective='qa')}")
        print(f"- balance-b7 at 10:00, as known before the quality office's denial: "
              f"{cal_line(wm, w, 'balance-b7', T(10), as_of=ids['known_before_qa'])}")
        print(f"- balance-b3 at 15:00 in {plan!r}: {cal_line(wm, plan, 'balance-b3', T(15))}")

        print("\n### Q4 Each measurement: stated reference beside the attested calibration (nothing is invalidated)")
        for r in lb.measurement_calibration(wm, w, "sample-12", mass):
            att = r["attested"]
            print(f"- {r['record']}: {r['instrument'] or 'no instrument'} at {r['at']:%H:%M}; stated "
                  f"{r['stated_reference']!r}; attested {att['judgement'] if att else '-'}; reference check: "
                  f"{r['reference_check']['check']} {[(x['certificate'], x['judgement']) for x in r['reference_check']['certificates']]};"
                  f" acceptance {r['acceptance']}, usable {r['usable']}" if r["at"] else
                  f"- {r['record']}: {r['instrument'] or 'no instrument'}; acceptance {r['acceptance']}, usable {r['usable']}")
        cmp = wm.compare_measurements(w, "sample-12", mass, T(16))
        compared = {m["attestation"] for m in cmp["measurements"]}
        print(f"- compared at 16:00: {len(compared)} measurements; the 15:00 weighing on an expired calibration is among "
              f"them: {ids['late']['content'] in compared} (calibration plays no part in comparison)")

        print("\n### Q5 Interpretations: testimony, hypothesis, rivals (each judged on its own)")
        for rec in (ids["measurements"]["ana-b9-35C"]["result"], ids["measurements"]["lab2"]["result"],
                    ids["measurements"]["bo-b7-k3"]["result"]):
            for i in lb.interpretations(wm, w, rec, T(16)):
                if i["type"] == "classified-as":
                    print(f"- {rec}: {i['attester']} says {i['roles']['classified'][0]} is {i['roles']['class'][0]}: "
                          f"{i['mode']}, {i['acceptance']}, supports answer {i['supports_answer']}; content "
                          f"{i['content_judgement']['judgement']} [{s(i['content_judgement']['status'])}]")
        print(f"- formal derivation: {lb.NO_DERIVATION}")
        for persp in ("system", "qa", "lab-2"):
            print(f"- {persp}: " + ", ".join(
                f"{c} {s(wm.holds(w, 'classified-as', {'classified': 'sample-12', 'class': c}, T(16), perspective=persp).status)}"
                for c in ("hydrated", "anhydrous")))

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
