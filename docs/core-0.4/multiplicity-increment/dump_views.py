"""Full occurrence() answers for the 398-view keys (latest knowledge time only), with a checkout's own code."""
import dataclasses, enum, gzip, json, sys
from datetime import date, datetime
sys.path.insert(0, sys.argv[1] + "/src")
from worldmodel import WorldModel
keys = json.load(gzip.open(sys.argv[3], "rt"))["views"]
wm = WorldModel.open(sys.argv[2])
def norm(x):
    if dataclasses.is_dataclass(x): return norm(dataclasses.asdict(x))
    if isinstance(x, enum.Enum): return x.name
    if isinstance(x, dict): return {str(k): norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set, frozenset)): return [norm(v) for v in x]
    if isinstance(x, (date, datetime)): return x.isoformat()
    return x
out = {}
for k in keys:
    w, occ, persp, when = json.loads(k)
    if when != "latest":
        continue
    out[k] = {"current": norm(wm.occurrence(w, occ, perspective=persp))}
json.dump({"views": out}, gzip.open(sys.argv[4], "wt"), sort_keys=True)
print(len(out), "views")
