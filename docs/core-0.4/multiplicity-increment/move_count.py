"""Queries and transactions per move() with a checkout's code (throwaway database, deleted)."""
import json, sys, uuid
from datetime import datetime, timedelta, timezone
sys.path.insert(0, sys.argv[1] + "/src")
from worldmodel import CORE_MODULES, WorldModel, connect
class CountingTx:
    def __init__(s, tx, c): s._tx, s._c = tx, c
    def query(s, *x, **k): s._c["q"] += 1; return s._tx.query(*x, **k)
    def __enter__(s): s._tx.__enter__(); return s
    def __exit__(s, *e): return s._tx.__exit__(*e)
    def __getattr__(s, n): return getattr(s._tx, n)
class Counting:
    def __init__(s, real): s._real, s.c = real, {"q": 0, "tx": 0}
    def transaction(s, *x, **k): s.c["tx"] += 1; return CountingTx(s._real.transaction(*x, **k), s.c)
    def __getattr__(s, n): return getattr(s._real, n)
real = connect(); name = f"wm-probe-movecount-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(name, driver=real, modules=CORE_MODULES)
try:
    w = wm.create_world("actual", id="w")
    for i in range(5): wm.add_entity("physical-object", f"o{i}", id=f"o{i}")
    for i in range(4): wm.add_entity("place", f"p{i}", id=f"p{i}")
    t0 = datetime(2026, 11, 1, tzinfo=timezone.utc)
    for i in range(5): wm.attest(w, "located-at", {"located": f"o{i}", "place": "p0"}, start=t0, until_superseded=True)
    c = Counting(real); wm.driver = c
    per = []
    for n in range(15):
        before = dict(c.c)
        wm.move(w, f"o{n % 5}", f"p{1 + n % 3}", t0 + timedelta(days=n + 1))
        per.append((c.c["q"] - before["q"], c.c["tx"] - before["tx"]))
    print(json.dumps({"commit": sys.argv[2], "moves": len(per), "queries": [q for q, _ in per],
                      "transactions": [t for _, t in per]}))
finally:
    real.databases.get(name).delete()
