"""Run an implementation's own bench_query_paths.py with timing instrumentation, without changing its code.

    uv run --python 3.13 --project <checkout> python -I scripts/bench_instrumented.py <checkout> [bench args...]

Wraps `worldmodel.typeql.rows` and, where present, `typeql.documents` (every read query, including streaming the answers) and `WorldModel.value_at` in the
checkout's own package, then runs its `scripts/bench_query_paths.py`. For each question it records total time and the
time spent inside TypeDB reads (query execution, network and driver decoding); the rest is Python processing.
Prints the bench's JSON followed by an `instrumented` JSON object. Used to compare Milestone 1 (main) and Core 0.3 under
the same Python version, server and methodology.
"""

import contextlib
import io
import json
import runpy
import statistics
import sys
import time
from pathlib import Path

checkout = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(checkout / "src"))
import worldmodel.model as model  # noqa: E402
import worldmodel.typeql as typeql  # noqa: E402

db_time = [0.0]
calls = {True: [], False: []}
_rows = typeql.rows


def timed_rows(*a, **kw):
    t = time.perf_counter()
    try:
        return _rows(*a, **kw)
    finally:
        db_time[0] += time.perf_counter() - t


typeql.rows = timed_rows
model.q.rows = timed_rows
if hasattr(typeql, "documents"):            # Core 0.3 reads attributes through `fetch` documents: a TypeDB read too
    _documents = typeql.documents

    def timed_documents(*a, **kw):
        t = time.perf_counter()
        try:
            return _documents(*a, **kw)
        finally:
            db_time[0] += time.perf_counter() - t

    typeql.documents = timed_documents
    model.q.documents = timed_documents
_value_at = model.WorldModel.value_at


def timed_value_at(self, *a, **kw):
    d0, t0 = db_time[0], time.perf_counter()
    out = _value_at(self, *a, **kw)
    calls[bool(self.selective)].append((time.perf_counter() - t0, db_time[0] - d0))
    return out


model.WorldModel.value_at = timed_value_at
sys.argv = [str(checkout / "scripts" / "bench_query_paths.py")] + sys.argv[2:]
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    try:
        runpy.run_path(sys.argv[0], run_name="__main__")
    except SystemExit as e:
        if e.code not in (None, 0):
            print(buf.getvalue())
            raise
bench = json.loads(buf.getvalue())


def summary(xs):
    xs = sorted(xs)
    pct = lambda p: xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]
    return {"median_ms": round(statistics.median(xs) * 1000, 1), "p95_ms": round(pct(0.95) * 1000, 1)}


inst = {"python": sys.version.split()[0]}
for selective, label in ((True, "selective"), (False, "full")):
    tot = [t for t, _ in calls[selective]]
    db = [d for _, d in calls[selective]]
    py = [t - d for t, d in calls[selective]]
    inst[label] = {"questions": len(tot), "total": summary(tot), "typedb_reads": summary(db), "python": summary(py),
                   "typedb_share_of_total": round(sum(db) / sum(tot), 3)}
print(json.dumps({"bench": bench, "instrumented": inst}, indent=1))
