"""Attribute Core 0.3's selective value_at() cost to its query kinds, on the benchmark workload.

    uv run python -I scripts/profile_query_kinds.py [--objects 200 --places 30 --moves 1000 --queries 60 --seed 11]

Builds the same world as scripts/bench_query_paths.py (throwaway database, deleted afterwards), then answers the same
kind of random questions with every read tagged by kind: chain (world branching), main (attestations with content and
attributes), roles (role players), acceptances, supersessions. Prints mean ms, mean rows and share of read time per
kind, plus the split between TypeDB reads and Python. Diagnostic only.
"""

import argparse
import json
import random
import statistics
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import worldmodel.model as model  # noqa: E402
import worldmodel.typeql as typeql  # noqa: E402
from worldmodel import WorldModel, connect  # noqa: E402

START = datetime(2026, 11, 9, 8, 0, tzinfo=timezone.utc)
KINDS = (("branching", "chain"), ("acceptance (holder", "acceptances"), ("supersession (old", "supersessions"),
         ("$c links ($role", "roles"), ("has stance $st", "main"))
log = defaultdict(list)
recording = [False]
_rows = typeql.rows


def tagged_rows(tx, body, params=None):
    t = time.perf_counter()
    out = _rows(tx, body, params)
    if recording[0]:
        kind = next((k for marker, k in KINDS if marker in body), "other")
        log[kind].append((time.perf_counter() - t, len(out)))
    return out


typeql.rows = tagged_rows
model.q.rows = tagged_rows


def main():
    ap = argparse.ArgumentParser()
    for name, default in (("objects", 200), ("places", 30), ("moves", 1000), ("queries", 60), ("seed", 11)):
        ap.add_argument(f"--{name}", type=int, default=default)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    driver = connect()
    name = f"wm-bench-{uuid.uuid4().hex[:8]}"
    wm = WorldModel.create(name, driver=driver)
    try:
        w = wm.create_world("actual")
        objs = [wm.add_entity("physical-object", f"o{i}") for i in range(a.objects)]
        pls = [wm.add_entity("place", f"p{i}") for i in range(a.places)]
        for o in objs:
            wm.attest(w, "located-at", {"located": o, "place": rnd.choice(pls)}, start=START, until_superseded=True)
        t = START
        for _ in range(a.moves):
            t += timedelta(seconds=rnd.randint(5, 60))
            wm.move(w, rnd.choice(objs), rnd.choice(pls), t)
        h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=t)
        for _ in range(a.moves // 20):
            t += timedelta(seconds=30)
            wm.move(h, rnd.choice(objs), rnd.choice(pls), t)
        questions = [(rnd.choice([w, h]), rnd.choice(objs), START + (t - START) * rnd.random()) for _ in range(a.queries)]
        recording[0] = True
        totals = []
        for world, o, when in questions:
            s = time.perf_counter()
            wm.value_at(world, "located-at", o, when)
            totals.append(time.perf_counter() - s)
        recording[0] = False
    finally:
        driver.databases.get(name).delete()
    read_total = sum(x for v in log.values() for x, _ in v)
    out = {"questions": a.queries, "value_at_median_ms": round(statistics.median(totals) * 1000, 1),
           "typedb_read_share": round(read_total / sum(totals), 3), "by_kind": {}}
    for kind, items in sorted(log.items()):
        out["by_kind"][kind] = {"queries_per_question": round(len(items) / a.queries, 2),
                                "mean_ms": round(statistics.mean(x for x, _ in items) * 1000, 2),
                                "mean_rows": round(statistics.mean(r for _, r in items), 2),
                                "share_of_read_time": round(sum(x for x, _ in items) / read_total, 3)}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
