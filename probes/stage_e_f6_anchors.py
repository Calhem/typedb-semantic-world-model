"""LABS-1.058, F6 correction: the supersession lookup's cost against the number of anchor ids, single query against two
steps, in one process (SUPERSESSION_TWO_STEP toggled). Read-only.

    uv run python -I probes/stage_e_f6_anchors.py <checkout> --dbs DB1,DB2 [--n 5] [--out FILE]

Loads: `_load(world)` (no filter: the largest heads) and `_load(world, types=[t])` for every proposition type, in the
worlds `actual`, `lab` and `org` (those present). Two anchoring settings: ANCHOR_MAX as configured (heads above it use
the head form, the pre-O-1 fallback) and ANCHOR_MAX = 10**9 (every head anchored, chunks of ANCHOR_CHUNK ids).
Per lookup: the anchor ids (the head's attestations), ms of `_supersessions` (both queries for two steps), rows.
Lookups are bucketed by anchor count; per bucket and setting: lookups, median and total ms. Each load's result is
compared (canonical form) between the two formulations in every round.
"""

import argparse
import json
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

BUCKETS = [(1, 10), (11, 100), (101, 1000), (1001, 5000), (5001, 10 ** 9)]


def canon(x):
    if hasattr(x, "__dataclass_fields__"):
        return canon(vars(x))
    if isinstance(x, dict):
        return {str(k): canon(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [canon(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted((canon(v) for v in x), key=repr)
    return str(x)


driver = connect()
result = {"n": a.n, "dbs": {}}
for db in a.dbs.split(","):
    wm = WorldModel(driver, db)
    default_max = wm.ANCHOR_MAX
    with wm._reading() as tx:
        worlds = {q.opt(r, "i") for r in q.rows(tx, "match $w isa world, has wm-id $i;")}
    loads = []
    for w in ("actual", "lab", "org"):
        if w in worlds:
            loads.append((w, None))
            loads += [(w, t) for t in sorted(wm.proposition_types())]
    log, last = [], {}
    real_anchored, real_sup = wm._anchored, wm._supersessions

    def anchored(tx, aids, head, params, body, extra):
        if "supersession (old: $a, new: $n), has recorded-at $srec" in body:
            last["n"] = len(aids)
        return real_anchored(tx, aids, head, params, body, extra)

    def supersessions(tx, follow):
        t0 = time.perf_counter()
        out = real_sup(tx, follow)
        log.append((last.pop("n", 0), (time.perf_counter() - t0) * 1000, len(out)))
        return out

    wm._anchored, wm._supersessions = anchored, supersessions
    per = {}
    answers = {}
    for i in range(a.n):
        settings = [(two, mx) for mx in (default_max, 10 ** 9) for two in (False, True)]
        for two, mx in (settings if i % 2 == 0 else settings[::-1]):
            wm.SUPERSESSION_TWO_STEP, wm.ANCHOR_MAX = two, mx
            key = f"{'two-step' if two else 'single'} max={'default' if mx == default_max else 'all'}"
            for w, t in loads:
                log.clear()
                ans = canon(wm._load(w, types=[t] if t else None))
                ref = answers.setdefault((w, t), ans)
                assert ans == ref, f"{db} {w} {t} {key}: load differs"
                for n, ms, rows in log:
                    per.setdefault(key, []).append((n, ms, rows))
    summary = {}
    for key, xs in per.items():
        summary[key] = {}
        for lo, hi in BUCKETS:
            b = [x for x in xs if lo <= x[0] <= hi]
            if b:
                summary[key][f"{lo}-{hi}"] = {"lookups": len(b) // a.n, "median_ms": round(statistics.median(x[1] for x in b), 2),
                                              "total_ms_per_round": round(sum(x[1] for x in b) / a.n, 1),
                                              "rows_per_round": sum(x[2] for x in b) // a.n,
                                              "max_anchors": max(x[0] for x in b)}
    result["dbs"][db] = {"loads": len(loads), "identical": True, "anchor_max_default": default_max, "buckets": summary}
    print(db, json.dumps(summary), file=sys.stderr)
text = json.dumps(result, indent=1)
if a.out:
    Path(a.out).write_text(text)
print(text)
