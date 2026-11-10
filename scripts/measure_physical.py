"""Latency and size of the physical reference world, for comparing Stage A1 and A2 checkouts (LABS-1.007).

    uv run python -I scripts/measure_physical.py <checkout> [--rounds 5]

Builds the gearbox reference world with the checkout's own code (A1 world; plus the A2 extensions when the checkout
has them) in a throwaway database (wm-phys-*, deleted afterwards), then times a fixed set of A1 questions (poses,
composition, contents, materials, frame_info, facts_about) and, if available, A2 questions (where, transform_between)
over several rounds on the selective path, counting TypeQL queries. Reports build time, database size on disk
(docker exec wm-typedb du), per-question medians and queries per question.
"""

import argparse
import json
import statistics
import subprocess
import sys
import time
import uuid
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--rounds", type=int, default=5)
ap.add_argument("--extended", action="store_true", help="also build the A2 extensions (only for an A2 checkout)")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
import worldmodel.typeql as typeql  # noqa: E402
from worldmodel import PHYSICAL_MODULES, WorldModel  # noqa: E402
from worldmodel.examples import gearbox as g  # noqa: E402

count = [0]
_run = typeql.run


def counted(tx, body, params=None):
    count[0] += 1
    return _run(tx, body, params)


typeql.run = counted
name = f"wm-phys-{uuid.uuid4().hex[:8]}"
s = time.perf_counter()
wm = WorldModel.create(name, modules=PHYSICAL_MODULES)
try:
    ids = g.build(wm)
    if a.extended:
        ids = g.extend_spatial(wm, ids)
    build_s = time.perf_counter() - s
    w = ids["world"]
    questions = {
        "poses(gear-in)": lambda: wm.poses(w, "gear-in", g.AFTER),
        "composition(gbx-100)": lambda: wm.composition(w, "gbx-100", g.AFTER),
        "contents(workshop)": lambda: wm.contents(w, "workshop", g.AFTER),
        "materials(cover)": lambda: wm.materials(w, "cover", g.AFTER),
        "frame_info(f-bench)": lambda: wm.frame_info(w, "f-bench", g.AFTER),
        "facts_about(housing)": lambda: wm.facts_about(w, "housing", g.AFTER),
    }
    if hasattr(wm, "where"):
        questions.update({
            "where(gbx-100, f-workshop)": lambda: wm.where(w, "gbx-100", "f-workshop", g.AFTER),
            "where(gear-in, f-workshop)": lambda: wm.where(w, "gear-in", "f-workshop", g.AFTER),
            "where(bench-1, f-gearbox)": lambda: wm.where(w, "bench-1", "f-gearbox", g.AFTER),
            "transform_between(f-gearbox, f-workshop)": lambda: wm.transform_between(w, "f-gearbox", "f-workshop", g.AFTER),
        })
    times = {k: [] for k in questions}
    queries = {}
    for _ in range(a.rounds):
        for k, f in questions.items():
            count[0] = 0
            t = time.perf_counter()
            f()
            times[k].append(time.perf_counter() - t)
            queries[k] = count[0]
    size = subprocess.run(["docker", "exec", "wm-typedb", "du", "-sb", f"/var/lib/typedb/data/{name}"],
                          capture_output=True, text=True)
    print(json.dumps({"checkout": Path(a.checkout).resolve().name, "extended": a.extended,
                      "build_seconds": round(build_s, 2),
                      "database_bytes": int(size.stdout.split()[0]) if size.returncode == 0 else None,
                      "questions": {k: {"median_ms": round(statistics.median(v) * 1000, 2), "queries": queries[k]}
                                    for k, v in times.items()}}, indent=1))
finally:
    wm.driver.databases.get(name).delete()
