"""Increment D design (LABS-1.041, DI-2): impact of the proposed event-role rule on the reference worlds.

    uv run python -I probes/pre_e_d_impact.py <checkout> [--db wm-probe-pre-e-d]

Reads the kept reference database (built by pre_e_b_snapshot.py --build from merged main). For every world, every
occurrence that some `describes` claim names, and every perspective the 106,752-answer snapshot uses (the system,
each attester of the world) at the latest knowledge time, plus the system at the snapshot's earlier knowledge time:
- the current merged view (`wm.occurrence`) and the proposed one (probes/pre_e_d_rule.py, from public readers only);
- every role the proposed declarations judge, and whether it would be DISPUTED (the only judgement change possible);
- where the current view differs from the proposed listing without any judgement: players merged under a core role
  name from descriptions of different types (the role-vocabulary issue, choice F), players taken from an account the
  perspective has not accepted, and descriptions listed whose account is not in the world.
The occurrence view is not part of the 106,752-answer snapshot (pre_e_b_snapshot.py does not call it), so this probe
is its baseline. Output: probes/pre_e_d_impact.out.txt.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--db", default="wm-probe-pre-e-d")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from worldmodel import WorldModel, connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from pre_e_d_rule import DECLARED, proposed_view  # noqa: E402

wm = WorldModel(connect(), a.db)
with wm._reading() as tx:
    worlds = sorted({q.opt(r, "id") for r in q.rows(tx, "match $w isa world, has wm-id $id;")})
print("Declarations evaluated:", ", ".join(f"{t}.{r}" + (f" (only as {k})" if k else "") for t, r, k in DECLARED))
totals = Counter()
for w in worlds:
    atts = wm.visible(w)
    occs = sorted({x for at in atts.values() if at.kind == "describes" for x in at.roles.get("occurrence", [])})
    attesters = sorted({at.attester for at in atts.values()} - {"system"})
    knowledge = sorted({at.recorded_at for at in atts.values() if at.recorded_at is not None})
    early = knowledge[len(knowledge) // 2] if knowledge else None
    contexts = [("system", None)] + [(p, None) for p in attesters] + ([("system", early)] if early else [])
    print(f"\n{w}: {len(occs)} occurrences, {len(contexts)} contexts (system, {len(attesters)} attesters, "
          f"system at an earlier knowledge time)")
    for occ in occs:
        for perspective, as_of in contexts:
            totals["views"] += 1
            cur = wm.occurrence(w, occ, as_of, perspective)
            prop = proposed_view(wm, w, occ, as_of, perspective)
            ctx = f"{occ} [{perspective}{', earlier' if as_of else ''}]"
            for name, j in prop["judged"].items():
                if not j["applies"]:
                    totals["constraint not applying (kind not established)"] += 1
                    continue
                totals["role judged"] += 1
                if j["judgement"] == "disputed":
                    totals["DISPUTED (judgement change)"] += 1
                    print(f"  {ctx}: {name} DISPUTED {[p['names'] for p in j['players']]}")
                if j["overridden"]:
                    totals["overridden by a nearer world"] += 1
            # listing differences, no judgement involved
            linked = {x["description"]: x for x in prop["descriptions"]}
            for core, players in cur["participants"].items():
                own = {r for r, e in prop["roles"].items() if e["core_role"] == core}
                if len(own) > 1:
                    totals["core role merging differently named roles"] += 1
                    print(f"  {ctx}: current `{core}` merges roles {sorted(own)}")
                for x, cites in players.items():
                    for d, _ in cites:
                        if linked.get(d, {}).get("account") != "accepted":
                            totals["player from an account not accepted"] += 1
                            print(f"  {ctx}: current `{core}` lists {x} from {d}, account "
                                  f"{linked.get(d, {}).get('account')}")
            for d in cur["descriptions"]:
                if linked[d]["account"] == "none in this world":
                    totals["description listed without an account in the world"] += 1
                    print(f"  {ctx}: current descriptions list {d} (no account in {w})")
print("\nTotals:")
for k, v in sorted(totals.items()):
    print(f"  {k}: {v}")
