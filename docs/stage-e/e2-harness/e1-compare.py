"""Compare an E1 results.json with reference results: every scored field of every question must be equal (meta,
timings and the run's commit may differ). Usage: e1-compare.py NEW REF [REF2]: REF2, when given, is the authoritative
comparison (a same-code run on main); REF is reported too. Exit 0 only if NEW equals the authoritative reference."""
import json
import sys

FIELDS = ("correct", "wrong_fields", "actual", "evidence", "failure", "paths_agree", "error", "expected", "note")


def load(p):
    return {r["id"]: r for r in json.load(open(p))["results"]}


new = load(sys.argv[1])
refs = sys.argv[2:]
rc = 0
for i, ref in enumerate(refs):
    old = load(ref)
    diff = sorted(k for k in set(new) | set(old) if k not in new or k not in old or
                  any(new[k].get(f) != old[k].get(f) for f in FIELDS))
    authoritative = i == len(refs) - 1
    print(f"{'AUTHORITATIVE ' if authoritative else ''}vs {ref}: {len(new)} vs {len(old)} questions; "
          f"{sum(r['correct'] for r in new.values())} vs {sum(r['correct'] for r in old.values())} correct; "
          f"differ: {diff}")
    for k in diff:
        print("  ", k, {f: (old.get(k, {}).get(f), new.get(k, {}).get(f)) for f in ("correct", "failure")})
    if authoritative and diff:
        rc = 1
sys.exit(rc)
