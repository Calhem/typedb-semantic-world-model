"""Increment B (LABS-1.038): read cost of the readers the canonical judgement touches, with a checkout's own code.

    uv run python -I probes/pre_e_b_read_bench.py <checkout> [--n 5] [--db wm-probe-pre-e-b] [--worlds w1,w2]
                                                  [--no-attested] [--more]

Reads the kept reference database built by pre_e_b_snapshot.py --build (the same data before and after). For each
reader, on fixed subjects in an actual world and in a variant (plan) world that inherits from it, it reports the
median and mean milliseconds per call over `n` rounds (interleaved) and the TypeDB queries and read transactions one
call makes. Prints JSON. Run it for the code before and after increment B, alternately, on a quiet machine.

--worlds limits the run to some worlds. --no-attested (LABS-1.039) reads with every profile's attested constraints
removed (office exclusivity is then not applied), so that, on the same subjects, the cost of the canonical judgement
mechanism itself can be told apart from the cost of applying contextual exclusivity. It has no effect on code before
increment B, which has no attested constraints.

--more (LABS-1.040) also reads changes (over the world's whole span) for the three most-mentioned particulars and
authorised for two grants, the other readers increment C touches. Off by default, so earlier runs stay comparable.
"""

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--n", type=int, default=5)
ap.add_argument("--db", default="wm-probe-pre-e-b")
ap.add_argument("--worlds")
ap.add_argument("--no-attested", action="store_true")
ap.add_argument("--more", action="store_true")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import WorldModel, connect, laboratory as lab, organisation as org  # noqa: E402
from worldmodel import profiles as profiles_  # noqa: E402

if a.no_attested:
    import dataclasses
    for name_, p_ in list(profiles_.PROFILES.items()):
        if getattr(p_, "attested_constraints", ()):
            profiles_.PROFILES[name_] = dataclasses.replace(p_, attested_constraints=())


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
        self._real, self.c = real, {"queries": 0, "transactions": 0}

    def transaction(self, *x, **k):
        self.c["transactions"] += 1
        return CountingTx(self._real.transaction(*x, **k), self.c)

    def __getattr__(self, n):
        return getattr(self._real, n)


driver = Counting(connect())
wm = WorldModel(driver, a.db)
from worldmodel import typeql as q  # noqa: E402
with wm._reading() as tx:
    ids = sorted(q.opt(r, "id") for r in q.rows(tx, "match $w isa world, has wm-id $id;"))
if a.worlds:
    ids = [w for w in ids if w in a.worlds.split(",")]
calls = {}                                   # (reader, world, subject) -> thunk
for w in ids:
    atts = wm.visible(w)
    mention = Counter(x for at in atts.values() for v in at.roles.values() for x in v)
    with wm._reading() as tx:
        kinds = wm._kinds_of(tx, sorted(mention))
    bounds = sorted({x for at in atts.values() for win in (at.start, at.end) if win is not None
                     for x in (win.earliest, win.latest) if x is not None})
    t = bounds[len(bounds) // 2]

    def top(label, k=2):
        return [x for x, _ in mention.most_common() if kinds.get(x) and wm.is_a(kinds[x], label)][:k]

    for x in top("particular", 3):
        calls[("facts_about", w, x)] = (wm.facts_about, (w, x, t), {})
        calls[("parts", w, x)] = (wm.parts, (w, x, t), {})
        if a.more:
            calls[("changes", w, x)] = (wm.changes, (w, x, bounds[0], bounds[-1]), {})
    for x in top("occurrence"):
        calls[("occurrence_status", w, x)] = (wm.occurrence_status, (w, x, t), {})
        calls[("causes_of", w, x)] = (wm.causes_of, (w, x, t), {})
    holdings = sorted({(at.roles["classified"][0], at.roles["class"][0], (at.roles.get("context") or [None])[0])
                       for at in atts.values() if wm.is_a(at.ctype, "classified-as")}, key=str)[:3]
    for h, c, ctx in holdings:
        calls[("capable", w, f"{h}/{c}")] = (wm.capable, (w, h, c, t), {"context": ctx})
    if "organisation" in wm.profiles():
        for office, ctx in sorted({(at.roles["class"][0], at.roles["context"][0]) for at in atts.values()
                                   if wm.is_a(at.ctype, "office-holding")})[:2]:
            calls[("office_holders", w, office)] = (org.office_holders, (wm, w, office, ctx, t), {})
        for x in sorted({at.roles["classified"][0] for at in atts.values() if wm.is_a(at.ctype, "office-holding")})[:2]:
            calls[("offices_of", w, x)] = (org.offices_of, (wm, w, x, t), {})
        if a.more:
            for h, p, sc in sorted({(at.roles["holder"][0], at.roles["power"][0], at.roles["scope"][0])
                                    for at in atts.values() if wm.is_a(at.ctype, "authorisation")})[:2]:
                calls[("authorised", w, f"{h}/{p}")] = (org.authorised, (wm, w, h, p, sc, t), {})
    if "laboratory" in wm.profiles():
        for x in top("sample", 3):
            calls[("provenance", w, x)] = (lab.provenance, (wm, w, x, t), {})
        for x in sorted({at.roles["calibrated"][0] for at in atts.values() if wm.is_a(at.ctype, "calibration-of")})[:2]:
            calls[("calibration_status", w, x)] = (lab.calibration_status, (wm, w, x, t), {})
        for x in top("information-object", 2):
            calls[("interpretations", w, x)] = (lab.interpretations, (wm, w, x, t), {})
results = {}
for key, (fn, args, kw) in calls.items():
    try:
        fn(*args, **kw)
        results[key] = {"ms": []}
    except Exception as e:
        print(f"skip {key}: {type(e).__name__}", file=sys.stderr)
for _ in range(a.n):
    for key in results:
        fn, args, kw = calls[key]
        before = dict(driver.c)
        t0 = time.perf_counter()
        fn(*args, **kw)
        results[key]["ms"].append((time.perf_counter() - t0) * 1000)
        results[key]["queries"] = driver.c["queries"] - before["queries"]
        results[key]["transactions"] = driver.c["transactions"] - before["transactions"]
by_reader = {}
for (reader, w, x), v in results.items():
    by_reader.setdefault(reader, {})[f"{w} {x}"] = {"median_ms": round(statistics.median(v["ms"]), 1),
                                                   "queries": v["queries"], "transactions": v["transactions"]}
print(json.dumps(by_reader, indent=1))
