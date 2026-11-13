"""Increment A (DI-8): cost of the composite writers with a checkout's own code, before and after atomic operations.

    uv run python -I probes/pre_e_a_write_bench.py <checkout> [--n 25]

Builds a small world (core and the mechanical and laboratory profiles) in a throwaway database (wm-probe-wbench-*,
deleted afterwards) and times `n` calls of each writer, interleaved round by round. Reports per call: median and mean
milliseconds, and the transactions opened (write, schema and read). Prints JSON.
"""

import argparse
import json
import statistics
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--n", type=int, default=25)
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from typedb.driver import TransactionType  # noqa: E402
from worldmodel import CORE_MODULES, WorldModel, connect, laboratory as lb, mechanical as mech  # noqa: E402


def T(day, h=9):
    return datetime(2026, 11, day, h, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


class Counting:
    def __init__(self, real):
        self._real, self.counts = real, {"write": 0, "schema": 0, "read": 0}

    def transaction(self, db, kind, *x, **k):
        self.counts[{TransactionType.READ: "read", TransactionType.WRITE: "write"}.get(kind, "schema")] += 1
        return self._real.transaction(db, kind, *x, **k)

    def __getattr__(self, name):
        return getattr(self._real, name)


real = connect()
name = f"wm-probe-wbench-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(name, driver=real, modules=CORE_MODULES, clock=Clock())
try:
    for p in ("mechanical", "laboratory"):
        wm.install_profile(p)
    w = wm.create_world("w", id="w")
    for i in ("ana", "bo", "core-1", "housing", "b1", "b2", "box"):
        wm.add_entity("physical-object", i, id=i)
    wm.add_entity("place", "shelf", id="shelf")
    for c in ("inspection", "measurement"):
        wm.add_entity("category", c, id=c)
    wm.define_quality_kind("mass", dimension="mass", id="mass")
    wm.define_unit("kilogram", "mass", id="kg")
    counting = Counting(real)
    wm.driver = counting
    n = {"i": 0}

    def fresh(prefix, kind="physical-object"):
        n["i"] += 1
        x = f"{prefix}-{n['i']}"
        wm.driver = real
        wm.add_entity(kind, x, id=x)
        wm.driver = counting
        return x

    writers = {
        "attest (single)": lambda: wm.attest(w, "located-at", {"located": fresh("x"), "place": "shelf"}, start=T(1),
                                             until_superseded=True),
        "account": lambda: wm.account(w, {"actor": "ana", "patient": "box"}, T(2), T(2), kind="inspection",
                                      attester="ana"),
        "take_sample": lambda: lb.take_sample(wm, w, "ana", "core-1", fresh("s", "sample"), start=T(3), attester="ana"),
        "replace_part": lambda: mech.replace_part(wm, w, "housing", "b1", fresh("p"), start=T(3), attester="bo"),
        "record_event": lambda: wm.record_event(w, {"actor": "bo", "patient": "box"}, T(4), kind="inspection",
                                                effects=[{"type": "part-of", "roles": {"part": fresh("q"),
                                                                                       "whole": "housing"}}]),
        "create_thing": lambda: wm.create_thing(w, "physical-object", "widget", T(2), id=f"widget-{uuid.uuid4().hex[:8]}"),
        "measure": lambda: wm.measure(w, "box", "mass", 2.0 + n["i"] / 100, "kg", 0.1, start=T(2), operator="ana",
                                      attester="ana"),
    }
    times = {k: [] for k in writers}
    txs = {k: [] for k in writers}
    for _ in range(a.n):
        for k, f in writers.items():
            before = dict(counting.counts)
            t0 = time.perf_counter()
            f()
            times[k].append((time.perf_counter() - t0) * 1000)
            txs[k].append({t: counting.counts[t] - before[t] for t in before})
    out = {k: {"median_ms": round(statistics.median(v), 1), "mean_ms": round(statistics.mean(v), 1),
               "transactions": txs[k][-1]} for k, v in times.items()}
    print(json.dumps(out, indent=1))
finally:
    real.databases.get(name).delete()
