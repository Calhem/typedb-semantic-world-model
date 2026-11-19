"""Compare two pre_e_d_impact.py --out files view by view: added keys, changed values, list changes (paths)."""
import gzip, json, sys
from collections import Counter
def load(p):
    d = json.load(gzip.open(p, "rt"))
    return d["views"]
def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in b.keys() - a.keys(): out["added " + path + "/" + k] += 1
        for k in a.keys() - b.keys(): out["REMOVED " + path + "/" + k] += 1
        for k in a.keys() & b.keys(): walk(a[k], b[k], path + "/" + k, out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for x, y in zip(a, b): walk(x, y, path + "[]", out)
    elif a != b:
        out["CHANGED " + path] += 1
A, B = load(sys.argv[1]), load(sys.argv[2])
print("views", len(A), len(B), "same keys", A.keys() == B.keys())
out, differ = Counter(), 0
for k in A.keys() & B.keys():
    c = Counter(); walk(A[k], B[k], "", c); out.update(c); differ += bool(c)
print("views differing:", differ)
import re
agg = Counter()
for p, n in out.items(): agg[re.sub(r"/roles/[^/]+/", "/roles/<label>/", p)] += n
for p, n in sorted(agg.items()): print(f"{n:6} {p}")
