"""Increment D (LABS-1.044, DI-9): where the TypeDB queries of one occurrence() call are made, for the views of the
frozen baseline that judge no constraint (latest knowledge time), with a checkout's own code.

    uv run python -I probes/pre_e_d_occurrence_queries.py <checkout> [--db wm-probe-pre-e-d-u]

Counts every query by the stack of WorldModel methods it is made under (_event_roles, identity, _load, _contents,
judgement); prints the mean per call. Output: probes/pre_e_d_occurrence_bench.out.txt (with the timing summary).
"""
import argparse
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("checkout"); ap.add_argument("--db", default="wm-probe-pre-e-d-u")
a = ap.parse_args()
BASELINE = Path(__file__).resolve().parent / "pre_e_d_occurrence_baseline.json.gz"
import sys, json, gzip, collections
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import WorldModel, connect
from worldmodel import dynamics, model
c = collections.Counter(); stack = []
class Tx:
    def __init__(s, t): s.t = t
    def query(s, *a, **k):
        c["/".join(stack) or "other"] += 1; return s.t.query(*a, **k)
    def __enter__(s): s.t.__enter__(); return s
    def __exit__(s, *e): return s.t.__exit__(*e)
    def __getattr__(s, n): return getattr(s.t, n)
class D:
    def __init__(s, d): s.d = d
    def transaction(s, *a, **k): return Tx(s.d.transaction(*a, **k))
    def __getattr__(s, n): return getattr(s.d, n)
wm = WorldModel(D(connect()), a.db)
def wrap(name):
    f = getattr(WorldModel, name)
    def g(self, *a, **k):
        stack.append(name)
        try: return f(self, *a, **k)
        finally: stack.pop()
    setattr(WorldModel, name, g)
for n in ("_event_roles", "identity", "_load", "_contents", "judgement"):
    if hasattr(WorldModel, n):        # the code before increment D has no _event_roles
        wrap(n)
frozen = json.load(gzip.open(BASELINE, "rt"))["views"]
keys = [json.loads(k) for k, v in sorted(frozen.items()) if not v["proposed"]["judgement"] and json.loads(k)[3] == "latest"]
tot = collections.Counter(); n = 0
for w, occ, p, _ in keys:
    wm.occurrence(w, occ, perspective=p)
    c.clear(); wm.occurrence(w, occ, perspective=p); tot.update(c); n += 1
print(n, "unconstrained latest views; queries per call, mean, by where they are made:")
for k, v in tot.most_common(): print(f"  {k:32} {v/n:6.1f}")
