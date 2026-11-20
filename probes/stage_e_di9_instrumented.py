"""Stage E DI-9 investigation (LABS-1.055): where the time of a slow reader goes, per TypeDB query. Read-only.

    uv run python -I probes/stage_e_di9_instrumented.py <checkout> --dbs DB1,DB2,... [--n 5] [--out FILE]
                                                                  [--experiments] [--readers parts,occurrence,...]

Use the databases of probes/stage_e_scale.py (worlds and perspectives axes): the reference data is the same in each.

For each call, every read query (`typeql.rows` and `typeql.documents`, through which every read in `worldmodel` goes)
is split into:
  first   time from submitting the query to the driver's first response (`query(...).resolve()`);
  stream  time to read every answer row or document (the server keeps executing while rows are read; the driver
          decodes each row as it arrives: this is streaming and decoding together; they cannot be told apart from
          Python);
  rows    number of rows or documents returned.
Read transactions are timed from opening to entering (`open`). The rest of the call's wall time is Python
(materialisation, filtering, judgement): python = total - open - sum(first) - sum(stream).

Per database it reports, per call: median total, open, first, stream, python (ms), queries, transactions and rows per
round; and per query shape (literals replaced by `?`): executions per round, rows per execution, median first and
stream per execution.

--experiments also times fixed scope queries in each database (n repetitions each, rows and median ms): how many
attestations the database, the reference world and its part-of contents hold, and the `_level` head for part-of in
`actual` written three ways (as the code writes it; starting from the world's attestations; starting from part-of
contents), to see whether the world predicate restricts the work before rows are produced.
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
ap.add_argument("--n", type=int, default=5)
ap.add_argument("--out")
ap.add_argument("--experiments", action="store_true")
ap.add_argument("--readers", default="parts,occurrence,where,value_at,effects_of,provenance")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import WorldModel, connect, laboratory as lab  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import gearbox as gb  # noqa: E402
from typedb.driver import TransactionType  # noqa: E402

LIT = re.compile(r'"(?:[^"\\]|\\.)*"|\b\d{4}-\d\d-\d\dT[\d:.]+(?:Z|[+-]\d\d:\d\d)?|\b\d+(?:\.\d+)?\b')
SPACE = re.compile(r"\s+")
log = []                      # per query: (shape, first s, stream s, rows)
opens = []                    # per transaction: open s


def shape(body):
    return SPACE.sub(" ", LIT.sub("?", body)).strip()


def _instrumented(kind):
    def f(tx, body, params=None):
        t0 = time.perf_counter()
        ans = q.run(tx, body, params)
        t1 = time.perf_counter()
        out = list(ans.as_concept_rows() if kind == "rows" else ans.as_concept_documents())
        t2 = time.perf_counter()
        log.append((shape(body), t1 - t0, t2 - t1, len(out)))
        return out
    return f


q.rows = _instrumented("rows")
q.documents = _instrumented("documents")


class TimedDriver:
    def __init__(self, real):
        self._real = real

    def transaction(self, *x, **k):
        t0 = time.perf_counter()
        tx = self._real.transaction(*x, **k)
        real_enter = tx.__enter__

        class Tx:
            def __enter__(s):
                r = real_enter()
                opens.append(time.perf_counter() - t0)
                return r

            def __exit__(s, *e):
                return tx.__exit__(*e)
        return Tx()

    def __getattr__(self, n):
        return getattr(self._real, n)


def calls(wm, readers):
    out = {}
    def bounds(w):
        return sorted({x for at in wm.visible(w).values() if not str(at.attester).startswith("zf-")
                       for win in (at.start, at.end) if win is not None for x in (win.earliest, win.latest)
                       if x is not None})
    mid = {w: (lambda b: b[len(b) // 2])(bounds(w)) for w in ("actual", "plan-relubricate-only", "lab")}
    if "parts" in readers:            # the slowest-growing calls of the entry scale run, same arguments
        for w, x in (("actual", "bay-1"), ("actual", "gbx-100"), ("plan-relubricate-only", "gbx-100")):
            out[f"parts {w} {x}"] = (lambda w=w, x=x: wm.parts(w, x, mid[w]))
    if "occurrence" in readers:
        for w, x in (("actual", "o-repair"), ("actual", "o-test-run"), ("lab", "o-split-b")):
            out[f"occurrence {w} {x}"] = (lambda w=w, x=x: wm.occurrence(w, x))
    if "where" in readers:
        out["where actual gbx-100 f-workshop"] = lambda: wm.where("actual", "gbx-100", "f-workshop", gb.AFTER)
    if "value_at" in readers:
        out["value_at actual gbx-100"] = lambda: wm.value_at("actual", "located-at", "gbx-100", gb.AFTER)
    if "effects_of" in readers:
        out["effects_of actual ev-worklog-replacement"] = lambda: wm.effects_of("actual", "ev-worklog-replacement", gb.AFTER)
    if "provenance" in readers:
        t_lab = bounds("lab")[-1]
        out["provenance lab s12-b"] = lambda: lab.provenance(wm, "lab", "s12-b", t_lab)
    return out


EXPERIMENTS = {
    "attestations in the database": "match $a isa attestation; select $a;",
    "attestations in world actual": 'match $w isa world, has wm-id == "actual"; $a isa attestation (context: $w); select $a;',
    "part-of attestations in the database (any world)": "match $a isa attestation (content: $c); $c isa part-of; select $a;",
    "part-of head as written (world, attestation, type)":
        'match $w isa world, has wm-id == "actual"; $a isa attestation (content: $c, context: $w, attester: $who), '
        'has wm-id $aid, has recorded-at $rec; $c isa part-of; select $aid;',
    "part-of head, world's attestations first":
        'match $w isa world, has wm-id == "actual"; $a links (context: $w); $a isa attestation; $a links (content: $c); '
        '$c isa part-of; $a has wm-id $aid; select $aid;',
    "part-of head, part-of contents first":
        'match $c isa part-of; $a isa attestation (content: $c); $a links (context: $w); $w has wm-id == "actual"; '
        '$a has wm-id $aid; select $aid;',
    "part-of head + role players (as _level's role query)":
        'match $w isa world, has wm-id == "actual"; $a isa attestation (content: $c, context: $w, attester: $who), '
        'has wm-id $aid, has recorded-at $rec; $c isa part-of; $c links ($role: $x); $x has wm-id $xid; select $aid, $xid;',
    "same-as head (identity load) in actual":
        'match $w isa world, has wm-id == "actual"; $a isa attestation (content: $c, context: $w, attester: $who), '
        'has wm-id $aid, has recorded-at $rec; $c isa same-as; select $aid;',
    "describes head in actual":
        'match $w isa world, has wm-id == "actual"; $a isa attestation (content: $c, context: $w, attester: $who), '
        'has wm-id $aid, has recorded-at $rec; $c isa describes; select $aid;',
    "event accounts in actual":
        'match $w isa world, has wm-id == "actual"; $a isa attestation (content: $c, context: $w), has wm-id $aid; '
        '$c isa event; select $aid;',
}


def experiments(driver, db):
    res = {}
    for name, body in EXPERIMENTS.items():
        times, rows = [], None
        for _ in range(a.n + 1):
            with driver.transaction(db, TransactionType.READ) as tx:
                t0 = time.perf_counter()
                n = len(list(tx.query(body).resolve().as_concept_rows()))
                times.append(time.perf_counter() - t0)
            rows = n
        res[name] = {"rows": rows, "median_ms": round(statistics.median(times[1:]) * 1000, 2)}
    return res


def med(xs):
    return round(statistics.median(xs) * 1000, 2) if xs else 0.0


def measure(db, readers):
    real = connect()
    driver = TimedDriver(real)
    wm = WorldModel(driver, db)
    cs = calls(wm, readers)
    for f in cs.values():
        f()                                                     # warm up (and fail early)
    per = {k: defaultdict(list) for k in cs}
    shapes = defaultdict(lambda: {"first": [], "stream": [], "rows": [], "count": 0})
    for _ in range(a.n):
        for k, f in cs.items():
            log.clear(); opens.clear()
            t0 = time.perf_counter()
            f()
            total = time.perf_counter() - t0
            first, stream = sum(x[1] for x in log), sum(x[2] for x in log)
            p = per[k]
            p["total"].append(total); p["open"].append(sum(opens)); p["first"].append(first)
            p["stream"].append(stream); p["python"].append(total - sum(opens) - first - stream)
            p["queries"] = len(log); p["transactions"] = len(opens); p["rows"] = sum(x[3] for x in log)
            for s, fi, st, n in log:
                d = shapes[(k, s)]
                d["first"].append(fi); d["stream"].append(st); d["rows"].append(n); d["count"] += 1
    out = {"calls": {}, "shapes": {}}
    for k, p in per.items():
        out["calls"][k] = {m: med(p[m]) for m in ("total", "open", "first", "stream", "python")}
        out["calls"][k].update(queries=p["queries"], transactions=p["transactions"], rows=p["rows"])
    for (k, s), d in shapes.items():
        out["shapes"][f"{k} || {s}"] = {"per_round": d["count"] / a.n, "rows_per_execution": round(statistics.fmean(d["rows"]), 1),
                                         "first_ms": med(d["first"]), "stream_ms": med(d["stream"]),
                                         "total_ms_per_round": round((sum(d["first"]) + sum(d["stream"])) * 1000 / a.n, 1)}
    if a.experiments:
        out["experiments"] = experiments(real, db)
    return out


dbs = a.dbs.split(",")
readers = set(a.readers.split(","))
res = {db: measure(db, readers) for db in dbs}
summary = {"databases": dbs, "n": a.n, "calls": {k: {db: res[db]["calls"][k] for db in dbs} for k in res[dbs[0]]["calls"]}}
base = res[dbs[0]]["shapes"]
growth = {}
for db in dbs[1:]:
    g = []
    for key, v in base.items():
        w = res[db]["shapes"].get(key)
        if w:
            g.append({"shape": key, "per_round": v["per_round"], "rows": [v["rows_per_execution"], w["rows_per_execution"]],
                      "first_ms": [v["first_ms"], w["first_ms"]], "stream_ms": [v["stream_ms"], w["stream_ms"]],
                      "added_ms_per_round": round(w["total_ms_per_round"] - v["total_ms_per_round"], 1)})
    growth[db] = sorted(g, key=lambda x: -x["added_ms_per_round"])[:12]
summary["largest_growing_shapes"] = growth
if a.experiments:
    summary["experiments"] = {db: res[db]["experiments"] for db in dbs}
text = json.dumps({"summary": summary, "raw": res}, indent=1)
if a.out:
    Path(a.out).write_text(text)
print(json.dumps(summary, indent=1))
