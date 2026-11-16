"""Increment C design (LABS-1.039, DI-6): impact estimate of the proposed aggregation rules on the reference worlds.

    uv run python -I probes/pre_e_c_impact.py <checkout> [--snapshot probes/pre_e_b_snapshot.after.json.gz]
                                                         [--db wm-probe-pre-e-b]

1. From the frozen reader snapshot (pre_e_b_snapshot.py, code as merged after increment B), for every answer of the
   one-question reports (capable, authorised, calibration_status, with every perspective and knowledge time the
   snapshot holds) and of office_holders, the status the proposed rules would give, computed from the answer's own
   holdings:
   - rule Q: unchanged where DISPUTED or undecided; established: the most direct status among the established
     holdings (each holding's status is the core rule over its own deciding support, so this equals the core rule
     over their union); does not hold: the same over the denied and expired holdings;
   - rule C (office_holders): None when holders are established without conflict.
   Prints how many answers would change, per reader, and each changed answer.
2. From the kept reference database: the accepted denials of a single-value slot that share a key with a value
   held at some time (the only situation in which the `changes` slot status, rule Q for a slot, can differ), per
   world, for the system perspective (the snapshot's `changes` perspective).
The exact inventory is made after implementation, by re-reading the snapshot with the new code (pre_e_b_diff.py).
"""

import argparse
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--snapshot", default="probes/pre_e_b_snapshot.after.json.gz")
ap.add_argument("--db", default="wm-probe-pre-e-b")
a = ap.parse_args()

ORDER = ("STIPULATED", "ASSERTED", "INFERRED")
YES, NO = {"accepted", "established"}, {"denied", "expired"}


def direct(statuses):
    return next((s for s in ORDER if s in statuses), None)


def rule_q(answer, items):
    if answer["status"] == "DISPUTED" or answer["holds"] is None:
        return answer["status"]
    chosen = [h["status"] for h in items if h["judgement"] in (YES if answer["holds"] else NO)]
    return direct(set(chosen)) or answer["status"]


snap = json.load(gzip.open(a.snapshot, "rt") if a.snapshot.endswith(".gz") else open(a.snapshot))["answers"]
seen, changed = Counter(), []
for key, ans in snap.items():
    k = json.loads(key)
    reader = k[2] if len(k) > 2 else k[1]
    base = reader.split("@")[0]
    if not isinstance(ans, dict) or "status" not in ans:
        continue
    if base in ("capable", "authorised", "calibration_status"):
        items = ans.get("applicable") or ans.get("grants") or ans.get("certificates") or []
        new = rule_q(ans, items)
    elif base == "office_holders":
        new = None if ans["holders"] and ans["status"] != "DISPUTED" else ans["status"]
    else:
        continue
    seen[base] += 1
    if new != ans["status"]:
        changed.append((base, k, ans["status"], new))
print("1. Snapshot answers of the aggregate reports, and how many the proposed rules would change:")
for base in sorted(seen):
    n = sum(1 for c in changed if c[0] == base)
    print(f"  {base:20} {seen[base]:6} answers, {n} would change")
for base, k, old, new in changed:
    print(f"    {base}: {k[0]} {k[1]} {k[3:]}: {old} -> {new}")

sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import WorldModel, connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.semantics import usable  # noqa: E402

wm = WorldModel(connect(), a.db)
with wm._reading() as tx:
    worlds = sorted({q.opt(r, "id") for r in q.rows(tx, "match $w isa world, has wm-id $id;")})
print("\n2. Accepted denials of a single-value slot value sharing a key with an attested value (system perspective):")
total = 0
for w in worlds:
    atts = list(wm.visible(w).values())
    n = 0
    for d in atts:
        if d.polarity or d.kind in ("event", "same-as") or not usable(d, "system", None):
            continue
        for _, ks, v in wm._constraints(d.ctype):
            key = tuple(tuple(d.roles.get(r, ())) for r in ks)
            if any(x.polarity and x is not d and wm.is_a(x.ctype, d.ctype) and
                   tuple(tuple(x.roles.get(r, ())) for r in ks) == key and usable(x, "system", None) for x in atts):
                n += 1
                break
    total += n
    print(f"  {w}: {n}")
print(f"  total: {total}")
