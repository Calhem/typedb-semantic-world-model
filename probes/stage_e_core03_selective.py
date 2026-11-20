"""Stage E DI-9 investigation (LABS-1.055): the Core 0.3 workload on the SELECTIVE path, with per-query instrumentation.

    uv run python -I probes/stage_e_core03_selective.py <checkout> --scale K --db NAME [--keep] [--reuse]
                                                                   [--queries 60] [--full-sample 0] [--out FILE]

Builds exactly the dataset of scripts/bench_query_paths.py (seed 11; 200 K objects, 30 K places, 1,000 K moves, a
hypothetical variant with moves / 20 moves) and asks the same `value_at` questions in the same order, but on the
selective path only (the full load at 10x is about 3-4 minutes per question; `--full-sample N` asks the first N
questions on the full load as well, to check answers and record its rows). `--reuse` skips the build when the
database exists (the questions are regenerated identically from the seed); `--keep` keeps the database afterwards.

For every question, every read query is split into time to first response, time to stream (and decode) its rows, and
rows returned; read transactions are timed when opened; the rest is Python. Prints JSON: ingestion, per-question
latency distribution, per-question medians of each part, queries / transactions / rows per question, per query shape
(rows per execution, first and stream ms), database bytes and the TypeDB container's memory (docker stats) before
and after the questions.
"""

import argparse
import json
import random
import re
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--scale", type=int, default=1)
ap.add_argument("--db", required=True)
ap.add_argument("--queries", type=int, default=60)
ap.add_argument("--seed", type=int, default=11)
ap.add_argument("--keep", action="store_true")
ap.add_argument("--reuse", action="store_true")
ap.add_argument("--full-sample", type=int, default=0)
ap.add_argument("--out")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import WorldModel, connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402

DOCKER = str(Path.home() / ".docker" / "bin" / "docker")
START = datetime(2026, 11, 9, 8, 0, tzinfo=timezone.utc)
LIT = re.compile(r'"(?:[^"\\]|\\.)*"|\b\d{4}-\d\d-\d\dT[\d:.]+(?:Z|[+-]\d\d:\d\d)?|\b\d+(?:\.\d+)?\b')
SPACE = re.compile(r"\s+")
log, opens = [], []


def _instrumented(kind):
    def f(tx, body, params=None):
        t0 = time.perf_counter()
        ans = q.run(tx, body, params)
        t1 = time.perf_counter()
        out = list(ans.as_concept_rows() if kind == "rows" else ans.as_concept_documents())
        log.append((SPACE.sub(" ", LIT.sub("?", body)).strip(), t1 - t0, time.perf_counter() - t1, len(out)))
        return out
    return f


q.rows, q.documents = _instrumented("rows"), _instrumented("documents")


class TimedDriver:
    def __init__(self, real):
        self._real = real

    def transaction(self, *x, **k):
        t0 = time.perf_counter()
        tx = self._real.transaction(*x, **k)

        class Tx:
            def __enter__(s):
                r = tx.__enter__()
                opens.append(time.perf_counter() - t0)
                return r

            def __exit__(s, *e):
                return tx.__exit__(*e)
        return Tx()

    def __getattr__(self, n):
        return getattr(self._real, n)


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]


def dist(xs):
    xs = [x * 1000 for x in xs]
    return {"n": len(xs), "min": round(min(xs), 1), "p10": round(pct(xs, .1), 1), "p50": round(statistics.median(xs), 1),
            "p90": round(pct(xs, .9), 1), "p95": round(pct(xs, .95), 1), "p99": round(pct(xs, .99), 1),
            "max": round(max(xs), 1), "mean": round(statistics.fmean(xs), 1)}


def docker(*args):
    r = subprocess.run([DOCKER, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def mem():
    return docker("stats", "--no-stream", "--format", "{{.MemUsage}} cpu {{.CPUPerc}}", "wm-typedb")


k = a.scale
n_obj, n_pl, n_mv = 200 * k, 30 * k, 1000 * k
rnd = random.Random(a.seed)
real = connect()
out = {"dataset": {"scale": k, "objects": n_obj, "places": n_pl, "moves": n_mv, "queries": a.queries, "seed": a.seed},
       "db": a.db}
exists = real.databases.contains(a.db)
if exists and not a.reuse:
    sys.exit(f"{a.db} exists: pass --reuse to read it, or drop it first")
t0 = time.perf_counter()
if not exists:
    wm = WorldModel.create(a.db, driver=real)
    w = wm.create_world("actual")
    objs = [wm.add_entity("physical-object", f"o{i}") for i in range(n_obj)]
    pls = [wm.add_entity("place", f"p{i}") for i in range(n_pl)]
    for o in objs:
        wm.attest(w, "located-at", {"located": o, "place": rnd.choice(pls)}, start=START, until_superseded=True)
    t, move_s = START, []
    for _ in range(n_mv):
        t += timedelta(seconds=rnd.randint(5, 60))
        s = time.perf_counter()
        wm.move(w, rnd.choice(objs), rnd.choice(pls), t)
        move_s.append(time.perf_counter() - s)
    h = wm.create_world("plan", kind="hypothetical", base=w, branch_at=t)
    for _ in range(n_mv // 20):
        t += timedelta(seconds=30)
        wm.move(h, rnd.choice(objs), rnd.choice(pls), t)
    out["ingest"] = {"seconds": round(time.perf_counter() - t0, 1), "move_ms_median": round(statistics.median(move_s) * 1000, 1),
                     "move_ms_p95": round(pct(move_s, .95) * 1000, 1)}
else:   # regenerate the same ids and times without writing: replay the random sequence
    wm = WorldModel(real, a.db)
    with wm._reading() as tx:
        ids = {q.opt(r, "n"): q.opt(r, "i") for r in q.rows(tx, "match $x isa particular, has name $n, has wm-id $i;")}
        worlds = {q.opt(r, "n"): q.opt(r, "i") for r in q.rows(tx, "match $x isa world, has name $n, has wm-id $i;")}
    w, h = worlds["actual"], worlds["plan"]
    objs = [ids[f"o{i}"] for i in range(n_obj)]
    pls = [ids[f"p{i}"] for i in range(n_pl)]
    for o in objs:
        rnd.choice(pls)
    t = START
    for _ in range(n_mv):
        t += timedelta(seconds=rnd.randint(5, 60))
        rnd.choice(objs); rnd.choice(pls)
    for _ in range(n_mv // 20):
        t += timedelta(seconds=30)
        rnd.choice(objs); rnd.choice(pls)
    out["ingest"] = "reused"
questions = [(rnd.choice([w, h]), rnd.choice(objs), START + (t - START) * rnd.random()) for _ in range(a.queries)]
db_bytes = docker("exec", "wm-typedb", "du", "-sb", f"/var/lib/typedb/data/{a.db}")
out["database_bytes"] = int(db_bytes.split()[0]) if db_bytes else None
sel = WorldModel(TimedDriver(real), a.db)
sel.selective = True
out["typedb_memory_before"] = mem()
per = defaultdict(list)
shapes = defaultdict(lambda: {"first": [], "stream": [], "rows": []})
answers = []
sel.value_at(questions[0][0], "located-at", questions[0][1], questions[0][2])           # warm-up
for world, o, when in questions:
    log.clear(); opens.clear()
    s = time.perf_counter()
    answers.append(sel.value_at(world, "located-at", o, when))
    tot = time.perf_counter() - s
    fi, st = sum(x[1] for x in log), sum(x[2] for x in log)
    per["total"].append(tot); per["open"].append(sum(opens)); per["first"].append(fi); per["stream"].append(st)
    per["python"].append(tot - sum(opens) - fi - st)
    per["queries"].append(len(log)); per["transactions"].append(len(opens)); per["rows"].append(sum(x[3] for x in log))
    for sh, f1, s1, n in log:
        shapes[sh]["first"].append(f1); shapes[sh]["stream"].append(s1); shapes[sh]["rows"].append(n)
out["typedb_memory_after"] = mem()
out["selective"] = {"latency": dist(per["total"]),
                    "median_ms": {m: round(statistics.median(per[m]) * 1000, 2) for m in ("total", "open", "first", "stream", "python")},
                    "mean_ms": {m: round(statistics.fmean(per[m]) * 1000, 2) for m in ("total", "open", "first", "stream", "python")},
                    "queries_per_question": round(statistics.fmean(per["queries"]), 2),
                    "transactions_per_question": round(statistics.fmean(per["transactions"]), 2),
                    "rows_per_question": round(statistics.fmean(per["rows"]), 1),
                    "shapes": sorted(({"shape": sh[:300], "executions": len(d["rows"]),
                                       "rows_per_execution": round(statistics.fmean(d["rows"]), 1),
                                       "first_ms": round(statistics.median(d["first"]) * 1000, 2),
                                       "stream_ms": round(statistics.median(d["stream"]) * 1000, 2),
                                       "total_ms": round((sum(d["first"]) + sum(d["stream"])) * 1000, 1)}
                                      for sh, d in shapes.items()), key=lambda x: -x["total_ms"])}
if a.full_sample:
    full = WorldModel(TimedDriver(real), a.db)
    full.selective = False
    fs = []
    for i, (world, o, when) in enumerate(questions[:a.full_sample]):
        log.clear(); opens.clear()
        s = time.perf_counter()
        ok = full.value_at(world, "located-at", o, when) == answers[i]
        tot = time.perf_counter() - s
        fs.append({"ms": round(tot * 1000, 1), "first_ms": round(sum(x[1] for x in log) * 1000, 1),
                   "stream_ms": round(sum(x[2] for x in log) * 1000, 1), "rows": sum(x[3] for x in log),
                   "queries": len(log), "identical": ok})
    out["full_sample"] = fs
    out["typedb_memory_after_full"] = mem()
if not a.keep:
    real.databases.get(a.db).delete()
    out["dropped"] = True
text = json.dumps(out, indent=1)
if a.out:
    Path(a.out).write_text(text)
print(text)
