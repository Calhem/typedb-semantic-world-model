"""LABS-1.056: choose O-1's bounds (ANCHOR_CHUNK, ANCHOR_MAX) and compare O-2's alternatives (ABSENT_CHECK) by
measurement. Read-only.

    uv run python -I probes/stage_e_o1_bounds.py <checkout> --db NAME [--knob o1|o2] [--n 5] [--out FILE]

--knob o2 compares ABSENT_CHECK none / database / subject / both, with O-1 at its defaults.

For a fixed set of calls on the database (reference calls on a stage_e_scale database; value_at questions on a
stage_e_core03_selective database), every call is timed under each setting of (ANCHOR_CHUNK, ANCHOR_MAX), settings
interleaved round by round. "head" (ANCHOR_MAX = -1) is the pre-O-1 form. Answers are compared with the head form's.
Reports per call and setting the median ms and queries (read queries executed), plus the head-query sizes seen
(attestation ids per `_level`), so the bounds can be related to how many ids are anchored.
"""

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--db", required=True)
ap.add_argument("--n", type=int, default=5)
ap.add_argument("--out")
ap.add_argument("--knob", choices=("o1", "o2"), default="o1")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import WorldModel, connect, laboratory as lab  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import gearbox as gb  # noqa: E402

SETTINGS = {"head": (100, -1), "c10": (10, 10 ** 9), "c25": (25, 10 ** 9), "c50": (50, 10 ** 9), "c100": (100, 10 ** 9),
            "c200": (200, 10 ** 9), "c1000": (1000, 10 ** 9), "c100-max200": (100, 200)}
if a.knob == "o2":
    SETTINGS = {m: m for m in ("none", "database", "subject", "both")}
count = [0]
sizes = Counter()
_rows, _docs = q.rows, q.documents
q.rows = lambda tx, b, p=None: (count.__setitem__(0, count[0] + 1), _rows(tx, b, p))[1]
q.documents = lambda tx, b, p=None: (count.__setitem__(0, count[0] + 1), _docs(tx, b, p))[1]
_anch = WorldModel._anchored


def anch(self, tx, aids, *x):
    sizes[len(aids)] += 1
    return _anch(self, tx, aids, *x)


WorldModel._anchored = anch
wm = WorldModel(connect(), a.db)


def calls():
    with wm._reading() as tx:
        worlds = {q.opt(r, "i") for r in q.rows(tx, "match $w isa world, has wm-id $i;")}
    if "lab" in worlds:                                       # a stage_e_scale database
        t_lab = sorted({x for at in wm.visible("lab").values() for win in (at.start, at.end) if win
                        for x in (win.earliest, win.latest) if x})[-1]
        return {
            "visible actual": lambda: wm.visible("actual"),
            "parts actual bay-1": lambda: wm.parts("actual", "bay-1", gb.AFTER),
            "parts plan-relubricate-only gbx-100": lambda: wm.parts("plan-relubricate-only", "gbx-100", gb.AFTER),
            "occurrence actual o-repair": lambda: wm.occurrence("actual", "o-repair"),
            "where actual gbx-100 f-workshop": lambda: wm.where("actual", "gbx-100", "f-workshop", gb.AFTER),
            "value_at actual gbx-100": lambda: wm.value_at("actual", "located-at", "gbx-100", gb.AFTER),
            "effects_of actual ev-worklog-replacement": lambda: wm.effects_of("actual", "ev-worklog-replacement", gb.AFTER),
            "provenance lab s12-b": lambda: lab.provenance(wm, "lab", "s12-b", t_lab),
        }
    with wm._reading() as tx:                                 # a Core 0.3 database
        ids = {q.opt(r, "n"): q.opt(r, "i") for r in q.rows(tx, "match $x isa physical-object, has name $n, has wm-id $i;")}
        names = {q.opt(r, "n"): q.opt(r, "i") for r in q.rows(tx, "match $w isa world, has name $n, has wm-id $i;")}
        ts = sorted(q.opt(r, "t") for r in q.rows(tx, "match $a isa attestation, has valid-from-earliest $t;"))
    out = {}
    for i, frac in enumerate((0.2, 0.5, 0.8)):
        for w in ("actual", "plan"):
            o, t = ids[f"o{(i * 37) % len(ids)}"], ts[int(frac * (len(ts) - 1))]
            out[f"value_at {w} o{(i * 37) % len(ids)} t{frac}"] = (lambda w=names[w], o=o, t=t: wm.value_at(w, "located-at", o, t))
    return out


def canon(x):
    """A comparable form: dataclasses as dicts, lists sorted (row order is not part of an answer)."""
    if hasattr(x, "__dataclass_fields__"):
        return canon(vars(x))
    if isinstance(x, dict):
        return {str(k): canon(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, list):
        return sorted((canon(v) for v in x), key=repr)
    if isinstance(x, tuple):
        return tuple(canon(v) for v in x)
    return x


def apply(setting):
    if a.knob == "o1":
        wm.ANCHOR_CHUNK, wm.ANCHOR_MAX = setting
    else:
        wm.ANCHOR_CHUNK, wm.ANCHOR_MAX = WorldModel.ANCHOR_CHUNK, WorldModel.ANCHOR_MAX
        wm.ABSENT_CHECK = setting


cs = calls()
ref = {}
for k, f in cs.items():
    wm.ANCHOR_CHUNK, wm.ANCHOR_MAX = SETTINGS["head"]
    ref[k] = canon(f())
res = {k: {s: {"ms": [], "queries": None, "same": True} for s in SETTINGS} for k in cs}
for _ in range(a.n):
    for s, setting in SETTINGS.items():
        apply(setting)
        for k, f in cs.items():
            count[0] = 0
            t0 = time.perf_counter()
            out = f()
            res[k][s]["ms"].append((time.perf_counter() - t0) * 1000)
            res[k][s]["queries"] = count[0]
            res[k][s]["same"] &= canon(out) == ref[k]
summary = {k: {s: {"median_ms": round(statistics.median(v["ms"]), 1), "queries": v["queries"], "same": v["same"]}
               for s, v in r.items()} for k, r in res.items()}
totals = {s: round(sum(summary[k][s]["median_ms"] for k in cs), 1) for s in SETTINGS}
text = json.dumps({"db": a.db, "n": a.n, "settings": SETTINGS, "totals_ms": totals, "calls": summary,
                   "anchored_sizes": dict(sorted(sizes.items()))}, indent=1)
if a.out:
    Path(a.out).write_text(text)
print(json.dumps({"db": a.db, "totals_ms": totals,
                  "all_same": all(v["same"] for r in summary.values() for v in r.values())}, indent=1))
