"""LABS-1.058: which part of the single-query supersession lookup (SUPERSESSION_TWO_STEP = False) grows with the
database? Read-only.

    uv run python -I probes/stage_e_f6_ablate.py <checkout> --dbs DB1,DB2 [--set 1|2]

--set 1: the new attestation's attributes and roles added one at a time to the pairs query;
--set 2: role pairs, `links` forms, typed role players, and the same pair of roles on the anchored (old) side.
Anchors: the first 4 attestations by id in the world named `actual` that are the old side of a supersession (the
same rule at every scale). Per variant: median ms of 15 runs (after 3 warm-up runs) in one read transaction, and rows.
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--dbs", required=True)
ap.add_argument("--set", type=int, default=1, choices=[1, 2])
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from typedb.driver import TransactionType  # noqa: E402

ANCHOR = "match $a isa attestation (content: $c), has wm-id == $anchor; $a has wm-id $aid;"
SU = " $su isa supersession (old: $a, new: $n), has recorded-at $srec; $n has wm-id $nid;"
SETS = {
    1: {
        "C full": SU + """ $n has stance $nst; $n isa attestation (context: $nwo, attester: $nwho); $nwo has wm-id $nw;
            $nwho has wm-id $nwid; try { $n has valid-from-earliest $nse; };""",
        "pairs": SU,
        "+stance": SU + " $n has stance $nst;",
        "+start (try)": SU + " try { $n has valid-from-earliest $nse; };",
        "+context": SU + " $n isa attestation (context: $nwo); $nwo has wm-id $nw;",
        "+attester": SU + " $n isa attestation (attester: $nwho); $nwho has wm-id $nwid;",
        "+context, attester (no ids)": SU + " $n isa attestation (context: $nwo, attester: $nwho);",
        "+context, attester": SU + " $n isa attestation (context: $nwo, attester: $nwho); $nwo has wm-id $nw; $nwho has wm-id $nwid;",
        "+links context": SU + " $n links (context: $nwo); $nwo has wm-id $nw;",
    },
    2: {
        "pairs": SU,
        "isa (context, attester)": SU + " $n isa attestation (context: $nwo, attester: $nwho);",
        "links (context), links (attester)": SU + " $n links (context: $nwo), links (attester: $nwho);",
        "links (context); links (attester)": SU + " $n links (context: $nwo); $n links (attester: $nwho);",
        "isa (context, attester), typed": SU + """ $n isa attestation (context: $nwo, attester: $nwho); $nwo isa world;
            $nwho isa social-object;""",
        "isa (content, context)": SU + " $n isa attestation (content: $x, context: $nwo);",
        "isa (content, attester)": SU + " $n isa attestation (content: $x, attester: $nwho);",
        "isa (context bound to $a's world)": SU + """ $a isa attestation (context: $wa);
            $n isa attestation (context: $wa, attester: $nwho);""",
        "old side (context, attester)": SU + " $a isa attestation (context: $owo, attester: $owho);",
    },
}

V = SETS[a.set]
driver = connect()
out = {}
for db in a.dbs.split(","):
    with driver.transaction(db, TransactionType.READ) as tx:
        olds = sorted({q.opt(r, "i") for r in q.rows(tx, """match $w isa world, has name "actual";
            $o isa attestation (context: $w), has wm-id $i; supersession (old: $o);""")})[:4]
        res = {}
        p = [{"anchor": x} for x in olds]
        for name, body in V.items():
            for _ in range(3):
                q.rows(tx, ANCHOR + body, p)
            ts = []
            for _ in range(15):
                s = time.perf_counter()
                n = len(q.rows(tx, ANCHOR + body, p))
                ts.append((time.perf_counter() - s) * 1000)
            res[name] = (round(statistics.median(ts), 2), n)
        out[db] = res
for name in V:
    print(f"{name:36s}", " | ".join(f"{db.split('-', 2)[-1]}: {out[db][name][0]:6.2f} ms {out[db][name][1]} rows"
                                    for db in out))
