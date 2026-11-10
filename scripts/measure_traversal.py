"""Scaling of frame-graph traversal (LABS-1.008): the resolver alone, then through TypeDB.

    uv run python -I scripts/measure_traversal.py [--typedb]

Part 1 (no database) resolves the far end of synthetic graphs of increasing size and depth: chains (one route),
ladders (two rails with rungs: many cycles, exponentially many simple routes) and random connected graphs, all
consistent, plus a ladder with one inconsistent rung and a run under a small resource limit. For small ladders the
number of simple routes is counted too, to show what path enumeration would face. Part 2 (--typedb) stores chains and
ladders as frame-transform attestations in throwaway databases (wm-trav-*, deleted afterwards) and times
transform_between with its TypeQL query count. Prints JSON.
"""

import argparse
import json
import math
import random
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import worldmodel.typeql as typeql  # noqa: E402
from worldmodel import PHYSICAL_MODULES, WorldModel  # noqa: E402
from worldmodel.physical import PhysicalMixin, yaw  # noqa: E402
from worldmodel.spatial import Transform  # noqa: E402

R = PhysicalMixin()
T0 = datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc)
T = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)


def e(p, c, tr):
    return {"parent": p, "child": c, "transform": tr, "support": [f"{p}>{c}"], "disputed": False}


def chain(n):
    return [e(f"n{i}", f"n{i + 1}", Transform(yaw(0.01), (1.0, 0.0, 0.0))) for i in range(n)], "n0", f"n{n}"


def ladder(n, bad=False):
    """Rails a0..an and b0..bn (b_i is 1 m along y from a_i), rungs a_i - b_i; all consistent unless `bad`."""
    edges = [e(f"a{i}", f"a{i + 1}", Transform(t=(1.0, 0.0, 0.0))) for i in range(n)]
    edges += [e(f"b{i}", f"b{i + 1}", Transform(t=(1.0, 0.0, 0.0))) for i in range(n)]
    edges += [e(f"a{i}", f"b{i}", Transform(t=(0.0, 1.0 + (0.3 if bad and i == n // 2 else 0.0), 0.0)))
              for i in range(n + 1)]
    return edges, "a0", f"b{n}"


def random_graph(v, extra, seed=7):
    """A random spanning tree with consistent absolute poses, plus `extra` consistent cross edges."""
    rnd = random.Random(seed)
    pose = {"r0": Transform()}
    edges = []
    for i in range(1, v):
        parent = f"r{rnd.randrange(i)}"
        pose[f"r{i}"] = pose[parent].then(Transform(yaw(rnd.uniform(-1, 1)), (rnd.uniform(-2, 2), rnd.uniform(-2, 2), 0)))
        edges.append(e(parent, f"r{i}", pose[parent].inverse().then(pose[f"r{i}"])))
    for _ in range(extra):
        a, b = rnd.sample(sorted(pose), 2)
        edges.append(e(a, b, pose[a].inverse().then(pose[b])))
    return edges, "r0", f"r{v - 1}"


def simple_paths(edges, s, t, cap=2_000_000):
    adj = {}
    for i, x in enumerate(edges):
        adj.setdefault(x["parent"], []).append((i, x["child"]))
        adj.setdefault(x["child"], []).append((i, x["parent"]))
    count, stack = 0, [(s, {s})]
    while stack and count < cap:
        node, seen = stack.pop()
        if node == t:
            count += 1
            continue
        for _, nxt in adj.get(node, ()):
            if nxt not in seen:
                stack.append((nxt, seen | {nxt}))
    return count if count < cap else f">={cap}"


def run(name, edges, s, t, limit=None, count_paths=False, repeats=5):
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        r = R._resolve(edges, s, t, limit)
        times.append(time.perf_counter() - start)
    se = r["search"]
    out = {"graph": name, "frames": len({x["parent"] for x in edges} | {x["child"] for x in edges}), "edges": len(edges),
           "status": r["status"].value, "hops": se["hops"], "chains_composed": 1 if r["chain"] else 0,
           "edges_examined": se["edges_examined"], "edges_checked": se["relevant_edges"], "complete": se["complete"],
           "truncated": se["truncated"], "verified": se["verified"], "inconsistent": len(se["inconsistent"]),
           "median_ms": round(statistics.median(times) * 1000, 3)}
    if count_paths:
        out["simple_routes"] = simple_paths(edges, s, t)
    return out


def part1():
    rows = [run(f"chain {n}", *chain(n)) for n in (8, 9, 16, 64, 256, 1024, 4096)]
    rows += [run(f"ladder {n}", *ladder(n), count_paths=n <= 16) for n in (4, 8, 12, 16, 64, 256, 1024)]
    rows += [run(f"random v={v} cross={x}", *random_graph(v, x)) for v, x in ((100, 100), (1000, 1000), (1000, 5000),
                                                                              (10000, 10000))]
    rows.append(run("ladder 64, one inconsistent rung", *ladder(64, bad=True)))
    rows.append(run("chain 256, limit 100", *chain(256), limit=100))
    rows.append(run("ladder 1024, limit 1000", *ladder(1024), limit=1000))
    return rows


def part2():
    count = [0]
    real = typeql.run

    def counted(tx, body, params=None):
        count[0] += 1
        return real(tx, body, params)

    rows = []
    for name, (edges, s, t) in (("chain 8", chain(8)), ("chain 32", chain(32)), ("chain 128", chain(128)),
                                ("ladder 32", ladder(32))):
        db = f"wm-trav-{uuid.uuid4().hex[:8]}"
        wm = WorldModel.create(db, modules=PHYSICAL_MODULES)
        try:
            w = wm.create_world("actual", id="actual")
            for f in sorted({x["parent"] for x in edges} | {x["child"] for x in edges}):
                wm.add_entity("spatial-frame", f, id=f)
            b = time.perf_counter()
            for x in edges:
                wm.relate_frames(w, x["parent"], x["child"], x["transform"].t, x["transform"].q, start=T0,
                                 until_superseded=True)
            build = time.perf_counter() - b
            typeql.run = counted
            times = []
            for _ in range(5):
                count[0] = 0
                start = time.perf_counter()
                r = wm.transform_between(w, t, s, T)
                times.append(time.perf_counter() - start)
            typeql.run = real
            rows.append({"graph": name, "edges": len(edges), "write_s": round(build, 1), "status": r["status"].value,
                         "hops": r["search"]["hops"], "complete": r["search"]["complete"],
                         "verified": r["search"]["verified"], "typeql_queries": count[0],
                         "median_ms": round(statistics.median(times) * 1000, 1)})
        finally:
            typeql.run = real
            wm.driver.databases.get(db).delete()
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--typedb", action="store_true")
    a = ap.parse_args()
    print(json.dumps({"resolver": part1(), "typedb": part2() if a.typedb else None}, indent=1))
