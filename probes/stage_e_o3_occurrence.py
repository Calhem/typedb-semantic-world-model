"""LABS-1.057, O-3: `occurrence()` with SCOPE_OCCURRENCE off (every event in the world) and on (only the linked
descriptions), on the databases of probes/stage_e_scale.py. Read-only.

    uv run python -I probes/stage_e_o3_occurrence.py <checkout> --dbs DB1,DB2 [--n 5] [--out FILE]

Calls: `occurrence(world, x)` for every occurrence named by a reference describes attestation in each reference world
(filler excluded), as in stage_e_scale.py's read set. The two settings alternate per round (off, on, on, off, ...).
Per call and setting: median ms (client-observed query time plus Python, one call), queries, rows returned by all
queries, event rows (documents returned by `_level` heads of event content: the event attestations retrieved) and
whether the masked answer equals the other setting's.
"""

import argparse
import json
import re
import statistics
import sys
import time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--dbs", required=True)
ap.add_argument("--n", type=int, default=5)
ap.add_argument("--out")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import WorldModel, connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402

REFERENCE_WORLDS = ["actual", "lab", "lab-plan-recal", "lab-plan-tom", "org", "org-plan-reorg", "plan-apprentice",
                    "plan-move-bench", "plan-relubricate-only", "plan-rig-control", "plan-steel-cover"]
ATT = re.compile(r"att:[0-9a-f]{16}")
CLOCK = re.compile(r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d\.\d{6}\+00:00")
log = []


def counted(kind):
    real = q.rows if kind == "rows" else q.documents

    def f(tx, body, params=None):
        out = list(real(tx, body, params))
        event_head = kind == "documents" and "$c isa event;" in body and '"aid": $aid, "wid"' in body
        log.append((len(out), event_head))
        return out
    return f


q.rows, q.documents = counted("rows"), counted("documents")


def mask(x):
    def walk(v):
        if isinstance(v, dict):
            return {str(k): walk(w) for k, w in v.items()}
        if isinstance(v, (list, tuple, set, frozenset)):
            return sorted((walk(w) for w in v), key=lambda w: json.dumps(w, sort_keys=True, default=str))
        if hasattr(v, "__dataclass_fields__"):
            return {f: walk(getattr(v, f)) for f in v.__dataclass_fields__}
        return CLOCK.sub("<clock>", ATT.sub("att:*", str(v))) if v is not None else None
    return walk(x)


driver = connect()
result = {"n": a.n, "dbs": {}}
for db in a.dbs.split(","):
    wm = WorldModel(driver, db)
    calls = []
    for w in REFERENCE_WORLDS:
        atts = wm._load(w, types=["describes"])
        occs = sorted({o for at in atts.values() if not str(at.attester).startswith("zf-")
                       and not any(x.startswith("zf-") for v in at.roles.values() for x in v)
                       for o in at.roles.get("occurrence", [])})
        calls += [(w, o) for o in occs]
    per = {f"{w} {o}": {s: {"ms": [], "queries": None, "rows": None, "event_rows": None, "answer": None}
                        for s in ("off", "on")} for w, o in calls}
    for i in range(a.n):
        for s in (("off", "on") if i % 2 == 0 else ("on", "off")):
            wm.SCOPE_OCCURRENCE = s == "on"
            for w, o in calls:
                log.clear()
                t0 = time.perf_counter()
                ans = wm.occurrence(w, o)
                ms = (time.perf_counter() - t0) * 1000
                d = per[f"{w} {o}"][s]
                d["ms"].append(round(ms, 2))
                d["queries"], d["rows"] = len(log), sum(n for n, _ in log)
                d["event_rows"] = sum(n for n, e in log if e)
                m = json.dumps(mask(ans), sort_keys=True)
                assert d["answer"] in (None, m), f"{db} {w} {o} {s}: answer changed between rounds"
                d["answer"] = m
    summary = {}
    for k, d in per.items():
        summary[k] = {s: {"median_ms": round(statistics.median(d[s]["ms"]), 2), "queries": d[s]["queries"],
                          "rows": d[s]["rows"], "event_rows": d[s]["event_rows"]} for s in ("off", "on")}
        summary[k]["same"] = d["off"]["answer"] == d["on"]["answer"]
    tot = {s: {m: round(sum(v[s][m] for v in summary.values()), 1) for m in ("median_ms", "queries", "rows", "event_rows")}
           for s in ("off", "on")}
    result["dbs"][db] = {"calls": len(calls), "identical": sum(v["same"] for v in summary.values()), "totals": tot,
                         "per_call": summary}
    print(db, len(calls), "calls; identical", result["dbs"][db]["identical"], json.dumps(tot), file=sys.stderr)
text = json.dumps(result, indent=1)
if a.out:
    Path(a.out).write_text(text)
print(text)
