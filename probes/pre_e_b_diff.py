"""Increment B (LABS-1.038): compare two reader snapshots (pre_e_b_snapshot.py) of the same database.

    uv run python -I probes/pre_e_b_diff.py BEFORE.json AFTER.json [--show N] [--json OUT]

Snapshots may be gzipped (.json.gz). The frozen ones are probes/pre_e_b_snapshot.before.json.gz (code at a1bb840)
and probes/pre_e_b_snapshot.after.json.gz (increment B); their comparison is probes/pre_e_b_diff.out.txt / .json.

Every answer is classified:
- identical;
- extended: every value the old answer had is unchanged and only new fields (dictionary keys) were added (approved
  under Q1: "fields are only added");
- changed: some old value differs, or an entry was added to or removed from a list. These are the answer changes to
  account for, one by one, against the authorised list (DI-1, DI-11, DI-5) in the increment B report.
Prints a count per reader and category, then up to N changed answers per reader with the paths that differ.
"""

import argparse
import gzip
import json
from collections import Counter, defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("before")
ap.add_argument("after")
ap.add_argument("--show", type=int, default=3)
ap.add_argument("--json")
a = ap.parse_args()


def load(f):
    return json.load(gzip.open(f, "rt") if f.endswith(".gz") else open(f))


old, new = load(a.before)["answers"], load(a.after)["answers"]


def compare(x, y, path="", out=None):
    """(changed paths, added paths) from x (old) to y (new)."""
    out = out if out is not None else ([], [])
    if isinstance(x, dict) and isinstance(y, dict):
        for k in x:
            if k not in y:
                out[0].append(f"{path}.{k} removed")
            else:
                compare(x[k], y[k], f"{path}.{k}", out)
        for k in y:
            if k not in x:
                out[1].append(f"{path}.{k}")
    elif isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            out[0].append(f"{path} length {len(x)} -> {len(y)}")
        else:
            for i, (u, v) in enumerate(zip(x, y)):
                compare(u, v, f"{path}[{i}]", out)
    elif x != y:
        out[0].append(f"{path}: {json.dumps(x)[:120]} -> {json.dumps(y)[:120]}")
    return out


counts = defaultdict(Counter)
examples = defaultdict(list)
added_fields = defaultdict(Counter)
for key in sorted(set(old) | set(new)):
    reader = json.loads(key)[2] if json.loads(key)[1] not in ("changes", "official_act", "check_action", "agency_report") \
        else json.loads(key)[1]
    if key not in new:
        counts[reader]["missing after"] += 1
        continue
    if key not in old:
        counts[reader]["new after"] += 1
        continue
    changed, added = compare(old[key], new[key])
    for p in added:
        added_fields[reader][p.split(".")[-1]] += 1
    cat = "changed" if changed else "extended" if added else "identical"
    counts[reader][cat] += 1
    if changed and len(examples[reader]) < a.show:
        examples[reader].append({"answer": json.loads(key), "differences": changed[:8]})

print(f"{'reader':32} identical extended  changed  other")
for reader in sorted(counts):
    c = counts[reader]
    other = sum(v for k, v in c.items() if k not in ("identical", "extended", "changed"))
    print(f"{reader:32} {c['identical']:9} {c['extended']:8} {c['changed']:8} {other:6}")
for reader in sorted(added_fields):
    print(f"added fields, {reader}: {dict(added_fields[reader])}")
for reader, ex in sorted(examples.items()):
    print(f"\n== {reader}: changed answers (first {len(ex)} of {counts[reader]['changed']})")
    for e in ex:
        print("  ", e["answer"])
        for d in e["differences"]:
            print("      ", d)
if a.json:
    changed_keys = [k for k in sorted(set(old) & set(new)) if compare(old[k], new[k])[0]]
    json.dump({"counts": {r: dict(c) for r, c in counts.items()}, "added_fields": {r: dict(c) for r, c in added_fields.items()},
               "changed": {k: compare(old[k], new[k])[0] for k in changed_keys}}, open(a.json, "w"), indent=1)
