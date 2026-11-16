"""Increment B merge (LABS-1.039): check that a reader snapshot of a rebuilt reference database reproduces the frozen one.

    uv run python -I probes/pre_e_b_repro_check.py FROZEN.json[.gz] REBUILT.json[.gz]

Rebuilding the reference database (pre_e_b_snapshot.py --build) gives every attestation a new random id and new
system-clock times (recorded_at, acceptance and first-recorded times), so a byte comparison of two builds always
differs. This masks exactly those, then compares every answer:
- `att:<16 hex>` ids become `att:*`;
- system-clock times (with microseconds; times in the reference worlds are whole seconds) become `<clock>`;
- list order is ignored (lists are ordered by attestation id), and so is the order of the two sides in a
  compare_measurements reason ("A vs B"), which follows the order of the two ids.
Prints the number of answers, how many are identical after masking, and every one that is not.
"""

import argparse
import gzip
import json
import re

ap = argparse.ArgumentParser()
ap.add_argument("frozen")
ap.add_argument("rebuilt")
a = ap.parse_args()

ATT = re.compile(r"att:[0-9a-f]{16}")
CLOCK = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}\+00:00")
VS = re.compile(r"^(different (?:measurement conditions|coverage levels) \()(.*) vs (.*)\)$")


def load(f):
    return json.load(gzip.open(f, "rt") if f.endswith(".gz") else open(f))["answers"]


def mask(x, key=None):
    if isinstance(x, dict):
        return {k: mask(v, k) for k, v in x.items()}
    if isinstance(x, list):
        return sorted((mask(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(x, str):
        if key == "recorded_at":
            return "<clock>"
        m = VS.match(x)
        if m:
            x = m[1] + " vs ".join(sorted([m[2], m[3]])) + ")"
        return CLOCK.sub("<clock>", ATT.sub("att:*", x))
    return x


f, r = load(a.frozen), load(a.rebuilt)
print(f"answers: frozen {len(f)}, rebuilt {len(r)}; same questions: {set(f) == set(r)}")
diff = [k for k in f if k in r and mask(f[k]) != mask(r[k])]
print(f"identical after masking: {len(f) - len(diff)}; different: {len(diff)}")
for k in diff:
    print("  ", k)
