"""Cost of writing measurements with a checkout's own code (LABS-1.020: does an atomic measure() change latency?).

    uv run python -I scripts/measure_write_cost.py <checkout> [--n 40]

Builds the laboratory reference world (lab.build_lab) in a throwaway database (wm-wcost-*, deleted afterwards), then
times `n` further measure() calls (alternating balances, values and conditions). Reports per measurement: median and
mean milliseconds, TypeQL queries, and write/read transactions opened; plus the database size on disk.
"""

import argparse
import json
import statistics
import subprocess
import sys
import time
import uuid
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--n", type=int, default=40)
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
import worldmodel.typeql as typeql  # noqa: E402
from worldmodel import QUALITY_MODULES, WorldModel  # noqa: E402
from worldmodel.examples import lab  # noqa: E402
from typedb.driver import TransactionType  # noqa: E402

count = {"queries": 0, "write": 0, "read": 0}
_run = typeql.run


def counted(tx, body, params=None):
    count["queries"] += 1
    return _run(tx, body, params)


typeql.run = counted
name = f"wm-wcost-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(name, modules=QUALITY_MODULES)
real_driver = wm.driver


class CountingDriver:
    """Counts the transactions the code under test opens (everything else is passed through)."""

    def __init__(self, d):
        self._d = d

    def transaction(self, database, kind, *args, **kw):
        count["write" if kind == TransactionType.WRITE else "read"] += 1
        return self._d.transaction(database, kind, *args, **kw)

    def __getattr__(self, n):
        return getattr(self._d, n)


try:
    ids = lab.build_lab(wm)
    wm.driver = CountingDriver(real_driver)
    w, kg = ids["world"], ids["kg"]
    times, per = [], []
    for i in range(a.n):
        for k in count:
            count[k] = 0
        t = time.perf_counter()
        wm.measure(w, "sample-12", ids["mass"], 3.50 + (i % 7) * 0.01, kg, 0.02, start=lab.T(16, i % 60),
                   end=lab.T(16, i % 60), instrument=("balance-b3", "balance-b7")[i % 2], operator="ana",
                   conditions=["temperature=20C", f"run={i % 3}"], calibration="CAL-B3", attester="ana")
        times.append(time.perf_counter() - t)
        per.append(dict(count))
    size = subprocess.run(["docker", "exec", "wm-typedb", "du", "-sb", f"/var/lib/typedb/data/{name}"],
                          capture_output=True, text=True)
    print(json.dumps({"checkout": Path(a.checkout).resolve().name, "n": a.n,
                      "median_ms": round(statistics.median(times) * 1000, 2),
                      "mean_ms": round(statistics.mean(times) * 1000, 2),
                      "queries_per_measure": sorted({p["queries"] for p in per}),
                      "write_tx_per_measure": sorted({p["write"] for p in per}),
                      "read_tx_per_measure": sorted({p["read"] for p in per}),
                      "database_bytes": int(size.stdout.split()[0]) if size.returncode == 0 else None}, indent=1))
finally:
    wm.driver = real_driver
    real_driver.databases.get(name).delete()
