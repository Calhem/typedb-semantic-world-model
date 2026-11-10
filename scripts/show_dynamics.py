"""Stage B demonstration (LABS-1.010): how the gearbox world changes over time, and why, with evidence.

    uv run python -I scripts/show_dynamics.py [--database wm-reference-gearbox] [--drop]

Builds the reference world with all its extensions (A1, A2 spatial, B1 events, B2 causality) in TypeDB, kept for
inspection unless --drop, then prints:
  Part 1, judged answers (WorldModel API, system perspective unless stated): what happened, what was replaced, the
          state before and after the repair, who acted, why the gearbox is operational again, which explanations are
          disputed, and how answers differ by perspective, knowledge time and hypothetical world;
  Part 2, raw TypeQL: the stored records (no acceptance, perspective or time applied).
"""

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import DYNAMICS_MODULES, WorldModel  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import gearbox as g  # noqa: E402
from worldmodel.model import READ  # noqa: E402

COND = {"bearer": "gbx-100", "quality": "condition"}
RAW = {
    "R1 event descriptions with gbx-100 as a participant: role, source and stated interval": """
match $x isa physical-object, has wm-id "gbx-100"; $e isa event, has wm-id $eid; $e links ($r: $x);
      $a isa attestation (content: $e, attester: $who), has valid-from-earliest $from; $who has wm-id $by;
fetch { "event": $eid, "role": $r, "by": $by, "from": $from, "until": $a.valid-to-earliest };""",
    "R2 describes records: which description is said to describe which occurrence, by whom": """
match $c isa describes (description: $e, occurrence: $o); $e has wm-id $eid; $o has wm-id $oid;
      $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "description": $eid, "occurrence": $oid, "by": $by };""",
    "R3 effect claims (initiates / terminates) with the outcome proposition's canonical key": """
match $c isa! $t, links (event: $e, outcome: $p); { $c isa initiates; } or { $c isa terminates; };
      $e has wm-id $eid; $p has proposition-key $key;
      $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "claim": $t, "event": $eid, "outcome": $key, "by": $by };""",
    "R4 causal claim records: polarity, source, basis (and any acceptance verdicts recorded about them)": """
match $c isa causes (cause: $x, effect: $y); $x has wm-id $xid; $y has wm-id $yid;
      $a isa attestation (content: $c, attester: $who, context: $w), has wm-id $aid, has polarity $pol, has basis $b;
      $who has wm-id $by; $w has wm-id $wid;
fetch { "cause": $xid, "effect": $yid, "polarity": $pol, "by": $by, "basis": $b, "world": $wid, "attestation": $aid,
        "verdicts": [ match $v isa acceptance (accepted: $a, holder: $h), has verdict $vd; $h has wm-id $hid;
                      fetch { "holder": $hid, "verdict": $vd }; ] };""",
    "R5 process membership: occurrences recorded as part of o-repair": """
match $p isa occurrence, has wm-id "o-repair"; $c isa part-of (whole: $p, part: $s); $s has wm-id $sid;
      $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "step": $sid, "by": $by };""",
}


def t(w):
    return f"{w.earliest:%m-%d %H:%M}" if w else "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--database", default="wm-reference-gearbox")
    ap.add_argument("--drop", action="store_true")
    a = ap.parse_args()
    wm = WorldModel.create(a.database, modules=DYNAMICS_MODULES, replace=True)
    try:
        ids = g.extend_causality(wm, g.extend_dynamics(wm, g.extend_spatial(wm, g.build(wm))))
        w = ids["world"]
        print(f"# Dynamics and causality in the reference world (database {a.database!r})\n")
        print("## Part 1: judged answers (WorldModel API)")

        print("\n### Q1 What happened to the gearbox? (accepted event descriptions naming gbx-100, in time order)")
        for e in wm.events(w, participant="gbx-100"):
            occ = wm.occurrences_of(w, e["event"])
            print(f"- {t(e['start'])}..{t(e['end'])} {e['event']} [{', '.join(e['kinds'])}] by {e['attester']}; "
                  f"describes {occ or '(no accepted occurrence)'}")
        print("  The repair process, step by step (part-of among occurrences):")
        for s in wm.process_steps(w, "o-repair", g.AFTER):
            print(f"  - {t(s['start'])}..{t(s['end'])} {s['occurrence']} [{', '.join(s['kinds'])}] actor {s['actors']}")

        print("\n### Q2 Which component was replaced?")
        view = wm.occurrence(w, "o-bearing-replacement")
        print(f"- o-bearing-replacement has {len(view['descriptions'])} accepted descriptions {view['descriptions']};"
              f" patients named: {view['participants']['patient']}")
        for e in wm.effects_of(w, "ev-worklog-replacement", g.AFTER):
            st = e["state"]
            print(f"- claimed {e['kind']} {e['outcome']['type']}{e['outcome']['roles']} by {e['claimed_by']}: claim "
                  f"{e['claim']}; state before {st['before'].status.value}/{st['before'].holds}, after "
                  f"{st['after'].status.value}/{st['after'].holds}; accepted change: {st['accepted_change']}")
        ch = wm.changes(w, "shaft-asm-in", g.BEFORE, g.AFTER)
        print(f"- changes to shaft-asm-in {g.BEFORE:%m-%d %H:%M} -> {g.AFTER:%m-%d %H:%M}: began "
              f"{[x['roles']['part'] for x in ch['began']]}, ended {[x['roles']['part'] for x in ch['ended']]}")

        print("\n### Q3 What state existed before and after the repair?")
        for label, at in (("before the inspection", g.BEFORE), ("after the inspection", g.INSPECTION[1]),
                          ("as the repair starts", g.REPAIR[0]), ("after the repair", g.RESTORED + timedelta(minutes=1))):
            c = wm.value_of(w, "has-quality", COND, at)
            print(f"- condition {label} ({at:%m-%d %H:%M}): {c.status.value} {list(c.values)}")
        ch = wm.changes(w, "gbx-100", g.REPAIR[0], g.AFTER)
        for x in ch["began"] + ch["ended"]:
            kind = "began" if x in ch["began"] else "ended"
            evs = [(e["event"], e["claim"], e["claimed_by"]) for e in x["claimed_events"]]
            print(f"- {kind}: {x['type']} {x['roles']} [{x['status'].value}] stated by {x['stated_by']};"
                  f" claimed events: {evs}")

        print("\n### Q4 Who performed the relevant actions?")
        for act in wm.actions_of(w, "technician"):
            print(f"- technician: {act['event']} [{', '.join(act['kinds'])}] {t(act['start'])}..{t(act['end'])}"
                  f" -> {act['occurrences']}")
        for act in wm.actions_of(w, "inspector"):
            print(f"- inspector: {act['event']} [{', '.join(act['kinds'])}] {t(act['start'])}")

        print("\n### Q5 What caused the gearbox to become operational again?")
        e = wm.explain(w, "has-quality", {**COND, "value": "operational"}, g.AFTER)
        print(f"- operational at {g.AFTER:%m-%d %H:%M}: {e['holds'].status.value}, support {list(e['holds'].support)}")
        for init in e["initiated_by"]:
            print(f"- initiated by {init['event']} (claim {init['claim']}, by {init['claimed_by']}), ended "
                  f"{t(init['end'])}, describing {init['occurrences']}")
            for c in init["causes"]:
                if c["judgement"] == "accepted":
                    via = f", lifted via {c['lifted_via']}" if c["lifted"] else ""
                    print(f"    cause: {c['cause']} -> {c['effect']} ({c['level']}-level{via}): accepted "
                          f"[{c['status'].value}], claimed by {c['claimed_by']}")

        print("\n### Q6 Which explanations are disputed, rejected or unreviewed?")
        for c in wm.causes_of(w, "o-test-run", g.AFTER):
            if c["judgement"] != "accepted":
                srcs = "; ".join(f"{x['attester']} ({'asserts' if x['polarity'] else 'denies'}, {x['basis']}, "
                                 f"{x['acceptance']})" for x in c["attestations"])
                print(f"- {c['cause']} -> {c['effect']}: {c['judgement']}; {srcs}")
        print("- not a cause by succession: the inspection ended before the test run "
              f"(before = {wm.before(w, 'ev-inspection-report', 'ev-test-run')}), and the only claim that it caused it"
              " was rejected; the disassembly precedes it too and no one claimed it as a cause")

        print("\n### Q7 How do the answers differ between perspectives, knowledge times and hypothetical worlds?")
        for label, kw, world in (("technician's perspective", {"perspective": "technician"}, w),
                                 ("inspector's perspective", {"perspective": "inspector"}, w),
                                 ("system, as known before the denial was accepted", {"as_of": ids["known_before_denial"]}, w),
                                 (f"hypothetical world {ids['causal_plan']!r}", {}, ids["causal_plan"])):
            got = [(c["cause"], c["judgement"]) for c in wm.causes_of(world, "o-test-run", g.AFTER, **kw)]
            print(f"- causes of o-test-run, {label}: {got}")
        plan = wm.create_world("plan: no repair", kind="hypothetical", base=w, knowledge_at=ids["known_before_repair"],
                               branch_at=g.INSPECTION[1] + timedelta(hours=1), id="plan-no-repair")
        c = wm.value_of(plan, "has-quality", COND, g.AFTER)
        print(f"- condition after the repair time in {plan!r} (knowledge before the repair was recorded): "
              f"{c.status.value} {list(c.values)}")
        c = wm.value_of(w, "has-quality", COND, g.AFTER, perspective="inspector")
        print(f"- condition after the repair, inspector's perspective: {c.status.value} {list(c.values)}")

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
