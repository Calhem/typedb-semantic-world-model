"""Attribute an implementation's write-path cost (WorldModel.move) to its query kinds, without changing its code.

    uv run python -I scripts/profile_write_path.py <checkout> [--objects 200 --places 30 --moves 300 --seed 11]

Builds the benchmark's world (as scripts/bench_query_paths.py: objects placed, then random moves) in a throwaway
database (wm-wprof-*, deleted afterwards) with the checkout's own `src/worldmodel`, and wraps its `typeql.run`, the
one function every query goes through. For the timed moves it reports, per query kind (the first words of the query,
normalised), queries per move and mean ms; and per move the time inside queries vs everything else (commits, Python).
Diagnostic only (LABS-1.003). Used to compare Core 0.3 and Core 0.4 A0 under the same harness.
"""

import argparse
import json
import random
import re
import statistics
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--objects", type=int, default=200)
ap.add_argument("--places", type=int, default=30)
ap.add_argument("--moves", type=int, default=300)
ap.add_argument("--seed", type=int, default=11)
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
import worldmodel.typeql as typeql  # noqa: E402
from worldmodel import WorldModel, connect  # noqa: E402

START = datetime(2026, 11, 9, 8, 0, tzinfo=timezone.utc)
_run = typeql.run
calls = []            # (kind, seconds) during the current move; None outside timed moves
recording = [False]


def kind_of(body):
    text = " ".join(body.split())
    text = re.sub(r'"[^"]*"', '"…"', text)
    head = re.sub(r"\$[A-Za-z0-9_]+", "$", text)
    return head[:90]


def timed_run(tx, body, params=None):
    s = time.perf_counter()
    try:
        return _run(tx, body, params)
    finally:
        if recording[0]:
            calls.append((kind_of(body), time.perf_counter() - s))


typeql.run = timed_run

rnd = random.Random(a.seed)
driver = connect()
name = f"wm-wprof-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(name, driver=driver)
try:
    w = wm.create_world("actual")
    objs = [wm.add_entity("physical-object", f"o{i}") for i in range(a.objects)]
    pls = [wm.add_entity("place", f"p{i}") for i in range(a.places)]
    for o in objs:
        wm.attest(w, "located-at", {"located": o, "place": rnd.choice(pls)}, start=START, until_superseded=True)
    t = START
    per_move, in_queries, counts = [], [], []
    by_kind = defaultdict(list)
    for _ in range(a.moves):
        t += timedelta(seconds=rnd.randint(5, 60))
        calls.clear()
        recording[0] = True
        s = time.perf_counter()
        wm.move(w, rnd.choice(objs), rnd.choice(pls), t)
        total = time.perf_counter() - s
        recording[0] = False
        per_move.append(total)
        in_queries.append(sum(sec for _, sec in calls))
        counts.append(len(calls))
        for k, sec in calls:
            by_kind[k].append(sec)
    n = a.moves
    out = {"checkout": str(Path(a.checkout).resolve().name), "dataset": {k: v for k, v in vars(a).items() if k != "checkout"},
           "move_ms_median": round(statistics.median(per_move) * 1000, 2),
           "move_ms_mean": round(statistics.mean(per_move) * 1000, 2),
           "queries_per_move": round(statistics.mean(counts), 2),
           "in_queries_ms_mean": round(statistics.mean(in_queries) * 1000, 2),
           "outside_queries_ms_mean": round((statistics.mean(per_move) - statistics.mean(in_queries)) * 1000, 2),
           "by_kind": {k: {"per_move": round(len(v) / n, 2), "mean_ms": round(statistics.mean(v) * 1000, 2)}
                       for k, v in sorted(by_kind.items(), key=lambda kv: -sum(kv[1]))}}
    print(json.dumps(out, indent=1))
finally:
    driver.databases.get(name).delete()
