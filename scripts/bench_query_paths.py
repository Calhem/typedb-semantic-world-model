"""Compare the selective query path (filters in TypeDB) with the full-load reference on a synthetic world.

    uv run python -I scripts/bench_query_paths.py --objects 200 --places 30 --moves 1000 --queries 60

Builds a throwaway database (wm-bench-*), runs the same random value_at() questions through both paths, checks the
answers are identical, prints JSON (ingestion, latency, claims and TypeQL queries per question, database size) and
deletes the database. Indicative only: one machine, TypeDB in Docker.
"""

import argparse
import json
import random
import statistics
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import WorldModel, connect  # noqa: E402

START = datetime(2026, 11, 9, 8, 0, tzinfo=timezone.utc)


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objects", type=int, default=200)
    ap.add_argument("--places", type=int, default=30)
    ap.add_argument("--moves", type=int, default=1000)
    ap.add_argument("--queries", type=int, default=60)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    driver = connect()
    name = f"wm-bench-{uuid.uuid4().hex[:8]}"
    wm = WorldModel.create(name, driver=driver)
    out = {"dataset": vars(a)}
    try:
        t0 = time.perf_counter()
        w = wm.create_world("actual")
        objs = [wm.add_entity("physical-object", f"o{i}") for i in range(a.objects)]
        pls = [wm.add_entity("place", f"p{i}") for i in range(a.places)]
        for o in objs:
            wm.assert_fact(w, "located-at", {"located": o, "place": rnd.choice(pls)}, start=START, until_ceased=True)
        t = START
        move_seconds = []
        for _ in range(a.moves):
            t += timedelta(seconds=rnd.randint(5, 60))
            s = time.perf_counter()
            wm.move(w, rnd.choice(objs), rnd.choice(pls), t)
            move_seconds.append(time.perf_counter() - s)
        h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=t)
        for _ in range(a.moves // 20):
            t += timedelta(seconds=30)
            wm.move(h, rnd.choice(objs), rnd.choice(pls), t)
        out["ingest"] = {"seconds": round(time.perf_counter() - t0, 1),
                         "move_ms_median": round(statistics.median(move_seconds) * 1000, 1),
                         "move_ms_p95": round(pct(move_seconds, 0.95) * 1000, 1)}
        full = WorldModel.open(name, driver=driver)
        full.selective = False
        total = len(full.visible_claims(w))
        out["claims_in_actual_world"] = total
        questions = [(rnd.choice([w, h]), rnd.choice(objs), START + (t - START) * rnd.random()) for _ in range(a.queries)]
        for label, model in (("selective", wm), ("full", full)):
            model.stats = {"queries": 0, "claims": 0}
            lat, answers = [], []
            for world, o, when in questions:
                s = time.perf_counter()
                answers.append(model.value_at(world, "located-at", o, when))
                lat.append(time.perf_counter() - s)
            out[label] = {"ms_median": round(statistics.median(lat) * 1000, 1), "ms_p95": round(pct(lat, 0.95) * 1000, 1),
                          "claims_per_question": round(model.stats["claims"] / a.queries, 1),
                          "typeql_queries_per_question": round(model.stats["queries"] / a.queries, 1)}
            out[label + "_answers"] = answers
        same = out.pop("selective_answers") == out.pop("full_answers")
        out["identical_answers"] = same
        size = subprocess.run(["docker", "exec", "wm-typedb", "du", "-sb", f"/var/lib/typedb/data/{name}"],
                              capture_output=True, text=True)
        out["database_bytes"] = int(size.stdout.split()[0]) if size.returncode == 0 else None
        if out["database_bytes"]:
            out["bytes_per_claim"] = round(out["database_bytes"] / total)
    finally:
        driver.databases.get(name).delete()
    print(json.dumps(out, indent=1))
    if not out.get("identical_answers"):
        sys.exit("answers differ between the paths")


if __name__ == "__main__":
    main()
