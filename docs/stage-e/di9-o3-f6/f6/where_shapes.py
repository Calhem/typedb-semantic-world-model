"""LABS-1.057: where's query time by query kind at 11 and 92 worlds, from the LABS-1.056 o2 runs (passes A, B and
repeats R1-R3; docs/stage-e/di9-optimisation/bench/*.json.gz).   python3 -I where_shapes.py <bench dir>"""
import gzip, json, sys
from collections import defaultdict
from pathlib import Path
B = Path(sys.argv[1])
files = [B / "A-o2-instrumented.json.gz", B / "B-o2-instrumented.json.gz"] + [B / f"R{i}-o2-repeat.json.gz" for i in (1, 2, 3)]
call = "where actual gbx-100 f-workshop"
agg, tot = defaultdict(lambda: defaultdict(list)), defaultdict(list)
for f in files:
    r = json.load(gzip.open(f))["raw"]
    for db in ("worlds-1", "worlds-10"):
        R = r[f"wm-probe-scale-{db}"]
        tot[db].append(R["calls"][call])
        for k, v in R["shapes"].items():
            c, s = k.split(" || ", 1)
            if c != call:
                continue
            cls = ("supersession" if "supersession (old" in s and "nacc" not in s else
                   "superseder acceptance" if "nacc" in s else "acceptance" if "acceptance (holder" in s else
                   "roles" if "links ($role" in s else "head and parameters (fetch)" if "fetch" in s else
                   "world chain" if "branching" in s else "other")
            agg[cls][db].append((v["per_round"], v["total_ms_per_round"]))
for db in ("worlds-1", "worlds-10"):
    t = tot[db]
    print(db, {m: [round(x[m]) for x in t] for m in ("total", "open", "first", "stream", "python", "queries", "rows")})
for cls, d in sorted(agg.items()):
    print(f"{cls:28s}", " | ".join(f"{db}: {sum(x[0] for x in d[db]) / 5:.0f} q, {sum(x[1] for x in d[db]) / 5:.1f} ms"
                                    for db in ("worlds-1", "worlds-10")))
