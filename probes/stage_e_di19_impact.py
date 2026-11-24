"""DI-19 (LABS-1.060): the only authorised difference between two reader snapshots (pre_e_b_snapshot.py) of the same
database is the additive `constraint_support` field. Read-only.

    uv run python -I probes/stage_e_di19_impact.py BEFORE.json AFTER.json

1. With every `constraint_support` key removed (at any depth) from AFTER, every answer must equal BEFORE.
2. Every non-empty `constraint_support` is listed, and must be on a holds() answer that is DISPUTED with conflicts
   (a dispute under an applied attested constraint), each entry citing at least one attestation.
Exit status 0 only when both hold.
"""

import gzip
import json
import sys

FIELD = "constraint_support"


def load(f):
    return json.load(gzip.open(f, "rt") if f.endswith(".gz") else open(f))["answers"]


def strip(x, found, path=""):
    if isinstance(x, dict):
        if FIELD in x and x[FIELD]:
            found.append((path, x))
        return {k: strip(v, found, f"{path}.{k}") for k, v in x.items() if k != FIELD}
    if isinstance(x, list):
        return [strip(v, found, f"{path}[{i}]") for i, v in enumerate(x)]
    return x


old, new = load(sys.argv[1]), load(sys.argv[2])
missing, extra = sorted(set(old) - set(new)), sorted(set(new) - set(old))
different, cited, bad = [], [], []
for key in sorted(set(old) & set(new)):
    found = []
    if strip(new[key], found) != old[key]:
        different.append(key)
    for path, ans in found:
        cited.append((key, path, ans))
        ok = (ans.get("status") == "DISPUTED" and ans.get("conflicts")
              and all(e.get("support") for e in ans[FIELD]))
        if not ok:
            bad.append((key, path))
print(f"answers: {len(old)} before, {len(new)} after; missing {len(missing)}, extra {len(extra)}")
print(f"different once {FIELD} is removed: {len(different)}")
for k in different[:10]:
    print("  DIFFERENT", k)
print(f"answers with a non-empty {FIELD}: {len(cited)}; not a constraint dispute: {len(bad)}")
for key, path, ans in cited:
    entries = "; ".join(f"{e['constraint']} {e['key']} support {e['support']}" for e in ans[FIELD])
    print(f"  {key}{path}: {ans['status']}, conflicts {ans['conflicts']} | {entries}")
for k in bad:
    print("  BAD", k)
sys.exit(0 if not (missing or extra or different or bad) else 1)
