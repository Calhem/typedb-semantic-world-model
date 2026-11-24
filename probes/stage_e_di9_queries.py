"""Stage E entry (LABS-1.054, step 4): DI-9 in isolation. Which TypeDB queries make a reader slower when OTHER worlds
are in the same database, and how many queries the per-item reports make.

    uv run python -I probes/stage_e_di9_queries.py <checkout> --dbs DB1,DB2[,...] [--n 7]

Use databases built by stage_e_scale.py on the `worlds` axis (the reference worlds plus K - 1 unrelated world
families): the reference data is the same in each, only the amount of other worlds differs.

For a fixed set of calls on the reference worlds (the readers DI-9 names: where, contents, effects_of, value_at,
facts_about in the gearbox world, and the laboratory reports provenance and measurement_calibration), every TypeDB query
is timed and grouped by its shape: the query text with string, number and datetime literals replaced by `?` and given
parameters dropped, so the same TypeQL with different ids is one shape. Per database it reports, per call, the median
time, queries and read transactions; and per query shape, how often it runs per round and its median time per
execution. Comparing the databases shows which shapes slow down with other worlds' data (at equal counts), which is
the evidence DI-9 asks for before choosing a correction (narrow to the world first, or batch).

Query plans are not available through the TypeDB 3.14 driver, so the cause is inferred from which shapes slow down and
what they match, not read from a plan. Read-only.
"""

import argparse
import json
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--dbs", required=True)
ap.add_argument("--n", type=int, default=7)
ap.add_argument("--out")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import WorldModel, connect, laboratory as lab  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import gearbox as gb  # noqa: E402

LIT = re.compile(r'"(?:[^"\\]|\\.)*"|\b\d{4}-\d\d-\d\dT[\d:.]+(?:Z|[+-]\d\d:\d\d)?|\b\d+(?:\.\d+)?\b')
SPACE = re.compile(r"\s+")
log = []                                                    # (shape, seconds) for the call being measured
_run = q.run


def timed_run(tx, body, params=None):
    t0 = time.perf_counter()
    try:
        out = _run(tx, body, params)
        return out
    finally:
        log.append((SPACE.sub(" ", LIT.sub("?", body)).strip(), time.perf_counter() - t0))


q.run = timed_run


class CountingTx:
    def __init__(self, tx, c):
        self._tx, self._c = tx, c

    def query(self, *x, **k):
        self._c["queries"] += 1
        return self._tx.query(*x, **k)

    def __enter__(self):
        self._tx.__enter__()
        return self

    def __exit__(self, *e):
        return self._tx.__exit__(*e)

    def __getattr__(self, n):
        return getattr(self._tx, n)


class Counting:
    def __init__(self, real):
        self._real, self.c = real, {"queries": 0, "transactions": 0}

    def transaction(self, *x, **k):
        self.c["transactions"] += 1
        return CountingTx(self._real.transaction(*x, **k), self.c)

    def __getattr__(self, n):
        return getattr(self._real, n)


def calls(wm):
    t = gb.AFTER
    bounds = sorted({x for at in wm.visible("lab").values() for win in (at.start, at.end) if win is not None
                     for x in (win.earliest, win.latest) if x is not None})
    t_lab = bounds[-1]                                      # the laboratory world's last recorded time
    return {
        "where actual gbx-100 f-workshop": lambda: wm.where("actual", "gbx-100", "f-workshop", t),
        "contents actual bay-1": lambda: wm.contents("actual", "bay-1", t),
        "effects_of actual ev-worklog-replacement": lambda: wm.effects_of("actual", "ev-worklog-replacement", t),
        "value_at actual gbx-100": lambda: wm.value_at("actual", "located-at", "gbx-100", t),
        "facts_about actual gbx-100": lambda: wm.facts_about("actual", "gbx-100", t),
        "provenance lab s12-b": lambda: lab.provenance(wm, "lab", "s12-b", t_lab),
        "measurement_calibration lab sample-12 q-mass": lambda: lab.measurement_calibration(wm, "lab", "sample-12", "q-mass"),
    }


def measure(db):
    driver = Counting(connect())
    wm = WorldModel(driver, db)
    cs = calls(wm)
    ok = {}
    for k, f in cs.items():
        try:
            f()
            ok[k] = f
        except Exception as e:                                                  # noqa: BLE001
            print(f"{db}: skip {k}: {type(e).__name__}: {e}", file=sys.stderr)
    per_call = {k: {"ms": []} for k in ok}
    shapes = defaultdict(lambda: {"seconds": [], "count": 0})
    for _ in range(a.n):
        for k, f in ok.items():
            before = dict(driver.c)
            log.clear()
            t0 = time.perf_counter()
            f()
            per_call[k]["ms"].append((time.perf_counter() - t0) * 1000)
            per_call[k]["queries"] = driver.c["queries"] - before["queries"]
            per_call[k]["transactions"] = driver.c["transactions"] - before["transactions"]
            for shape, s in log:
                shapes[(k, shape)]["seconds"].append(s)
                shapes[(k, shape)]["count"] += 1
    return {
        "calls": {k: {"median_ms": round(statistics.median(v["ms"]), 1), "queries": v["queries"],
                      "transactions": v["transactions"]} for k, v in per_call.items()},
        "shapes": {f"{k} || {shape}": {"per_round": v["count"] / a.n, "median_ms": round(statistics.median(v["seconds"]) * 1000, 2),
                                         "total_ms_per_round": round(sum(v["seconds"]) * 1000 / a.n, 1)}
                   for (k, shape), v in shapes.items()},
    }


dbs = a.dbs.split(",")
res = {db: measure(db) for db in dbs}
base = res[dbs[0]]
summary = {"databases": dbs, "n": a.n, "calls": {}, "slowest_growing_shapes": {}}
for k in base["calls"]:
    summary["calls"][k] = {db: res[db]["calls"].get(k) for db in dbs}
for db in dbs[1:]:
    growth = []
    for key, v in base["shapes"].items():
        w = res[db]["shapes"].get(key)
        if w and v["median_ms"] > 0:
            growth.append({"shape": key, "per_round": v["per_round"], "median_ms_base": v["median_ms"],
                           "median_ms": w["median_ms"], "ratio": round(w["median_ms"] / v["median_ms"], 2),
                           "added_ms_per_round": round(w["total_ms_per_round"] - v["total_ms_per_round"], 1)})
    growth.sort(key=lambda g: -g["added_ms_per_round"])
    summary["slowest_growing_shapes"][db] = growth[:15]
text = json.dumps({"summary": summary, "raw": res}, indent=1)
if a.out:
    Path(a.out).write_text(text)
print(json.dumps(summary, indent=1))
