import sys, time, statistics
sys.path.insert(0, sys.argv[1] + "/src")
from worldmodel import WorldModel, connect, typeql as q
from typedb.driver import TransactionType as T
d = connect(); db = sys.argv[2]
wm = WorldModel(d, db)
ids = sorted(wm.visible("actual"))
tail = """ $su isa supersession (old: $a, new: $n), has recorded-at $srec; $n has wm-id $nid, has stance $nst;
 $n isa attestation (context: $nwo, attester: $nwho); $nwo has wm-id $nw; $nwho has wm-id $nwid; try { $n has valid-from-earliest $nse; };"""
def given(chunk):
    with d.transaction(db, T.READ) as tx:
        t = time.perf_counter()
        out = list(tx.query("given $i: string;\nmatch $a isa attestation (content: $c), has wm-id == $i; $a has wm-id $aid;" + tail,
                            given_rows=[{"i": q.to_driver(x)} for x in chunk]).resolve().as_concept_rows())
        return time.perf_counter() - t, len(out)
def disj(chunk):
    with d.transaction(db, T.READ) as tx:
        alts = " or ".join(f"{{ $a has wm-id == $a{j}; }}" for j in range(len(chunk)))
        t = time.perf_counter()
        out = q.rows(tx, f"match $a isa attestation (content: $c), has wm-id $aid; {alts};" + tail, {f"a{j}": x for j, x in enumerate(chunk)})
        return time.perf_counter() - t, len(out)
for n in (1, 10, 25, 50, 100, len(ids)):
    for name, f in (("given", given), ("disj", disj)):
        if name == "disj" and n > 100: continue
        ts = []; rows = 0
        for _ in range(5):
            s, rows = f(ids[:n]); ts.append(s)
        print(db, name, n, "ids", rows, "rows", round(statistics.median(ts) * 1000, 1), "ms")
