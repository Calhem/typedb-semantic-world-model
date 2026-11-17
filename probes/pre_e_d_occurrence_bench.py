"""Increment D (LABS-1.043/1.044): read cost of the merged occurrence view, by kind of view, with a checkout's own code.

    uv run python -I probes/pre_e_d_occurrence_bench.py <checkout> --db wm-probe-pre-e-d-u --reference [--n 5]
    uv run python -I probes/pre_e_d_occurrence_bench.py <checkout> --db wm-probe-pre-e-d-x --examples [--n 5]

--reference: the 398 views of the frozen baseline (probes/pre_e_d_occurrence_baseline.json.gz), each categorised from
the baseline's own judgement: `unconstrained` (no constraint evaluated), `established` (a constraint applies and the
role is established), `disputed` (a constraint applies and the role is DISPUTED) or `inapplicable` (a constraint is
evaluated but its kind is not established), and flagged `variant` (a hypothetical world) and `perspective` (not the
system's). The earlier-knowledge-time views are read with no knowledge time (the earlier time is a clock time of the
build); they are flagged `earlier` and counted separately.
--examples: the cases of probes/pre_e_d_examples.py in a database kept by `pre_e_d_examples.py <checkout> <db>`,
each with the category the design gives it (the reference worlds hold no disputed role).
Calls are interleaved over `n` rounds; per view, the median ms of its calls and the TypeDB queries one call makes.
Prints JSON. Run it for the code before increment D (bf8bb34) and after, alternately, on a quiet machine.
"""

import argparse
import gzip
import json
import statistics
import sys
import time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--db", required=True)
ap.add_argument("--n", type=int, default=5)
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument("--reference", action="store_true")
g.add_argument("--examples", action="store_true")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import WorldModel, connect  # noqa: E402

HERE = Path(__file__).resolve().parent
# (world, occurrence, perspective, category, flags): the design's examples, with the category section 6 gives them
EXAMPLES = [
    ("w", "o-act", "system", "disputed", []), ("w", "o-act", "auditor", "established", ["perspective"]),
    ("w", "o-act-alias", "system", "established", []), ("w", "o-act-alias", "qa", "disputed", ["perspective"]),
    ("w", "o-act-pending", "system", "established", []), ("w", "o-act-link", "system", "established", []),
    ("plan", "o-act", "system", "established", ["variant"]), ("plan-late", "o-act", "system", "established", ["variant"]),
    ("w", "o-job", "system", "inapplicable", []), ("w", "o-swap", "system", "inapplicable", []),
    ("w", "o-swap-1for1", "system", "disputed", []), ("w", "o-swap-1for1", "insp", "inapplicable", ["perspective"]),
    ("w", "o-swap-late", "system", "inapplicable", []), ("w", "o-k-disputed", "system", "inapplicable", []),
    ("w", "o-k-ended", "system", "inapplicable", []), ("w", "o-k-pending", "system", "disputed", []),
    ("plan-late", "o-swap-1for1", "system", "disputed", ["variant"]),
    ("plan-deny", "o-swap-1for1", "system", "inapplicable", ["variant"]),
    ("plan-classify", "o-swap-plan", "system", "disputed", ["variant"]),
    ("w", "o-swap-plan", "system", "inapplicable", []),
]


class CountingTx:
    def __init__(self, tx, c):
        self._tx, self._c = tx, c

    def query(self, *x, **k):
        self._c["queries"] += 1
        return self._tx.query(*x, **k)

    def __enter__(self):
        self._tx.__enter__()
        return self

    def __exit__(self, *e):
        return self._tx.__exit__(*e)

    def __getattr__(self, n):
        return getattr(self._tx, n)


class Counting:
    def __init__(self, real):
        self._real, self.c = real, {"queries": 0}

    def transaction(self, *x, **k):
        return CountingTx(self._real.transaction(*x, **k), self.c)

    def __getattr__(self, n):
        return getattr(self._real, n)


def category(view):
    j = view["proposed"]["judgement"]
    if not j:
        return "unconstrained"
    if any(x["applies"] and x["judgement"] == "disputed" for x in j.values()):
        return "disputed"
    if any(x["applies"] and x["judgement"] == "established" for x in j.values()):
        return "established"
    return "inapplicable"


driver = Counting(connect())
wm = WorldModel(driver, a.db)
views = []
if a.reference:
    frozen = json.load(gzip.open(HERE / "pre_e_d_occurrence_baseline.json.gz", "rt"))["views"]
    kinds = {}
    for key, v in sorted(frozen.items()):
        w, occ, perspective, knowledge = json.loads(key)
        if w not in kinds:
            kinds[w] = wm.world_kind(w)
        flags = (["variant"] if kinds[w] != "actual" else []) + (["perspective"] if perspective != "system" else []) \
            + (["earlier"] if knowledge == "earlier" else [])
        views.append((w, occ, perspective, category(v), flags))
else:
    views = EXAMPLES
results = {}
for view in views:
    w, occ, perspective = view[:3]
    wm.occurrence(w, occ, perspective=perspective)                 # warm-up
    results[view[:3] + (tuple(view[4]),)] = {"category": view[3], "flags": view[4], "ms": []}
for _ in range(a.n):
    for (w, occ, perspective, flags), r in results.items():
        before = driver.c["queries"]
        t0 = time.perf_counter()
        wm.occurrence(w, occ, perspective=perspective)
        r["ms"].append((time.perf_counter() - t0) * 1000)
        r["queries"] = driver.c["queries"] - before
out = [{"world": k[0], "occurrence": k[1], "perspective": k[2], "flags": list(k[3]), "category": r["category"],
        "queries": r["queries"], "median_ms": round(statistics.median(r["ms"]), 2)} for k, r in results.items()]
print(json.dumps(out, indent=0))
