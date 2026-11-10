"""How the Stage B dynamics questions scale with the number of events (LABS-1.011). Characterisation only.

    uv run python -I scripts/measure_dynamics_scaling.py [--cycles 0 4 16 64] [--rounds 5]

For each size, builds the reference world (A1 + B1 + B2 + the second repair) plus N synthetic repair cycles on later
days (each: a replacement and a test-run occurrence, the technician's accepted accounts with kinds and describes
links, an accepted effect claim with its state, an accepted causal claim), in a throwaway database (wm-dscale-*,
deleted afterwards). Then asks the same questions about the first repair and reports, per question: median latency,
TypeQL queries, attestation records retrieved, and how often the same kind of load repeats within one question.
"""

import argparse
import json
import statistics
import sys
import time
import uuid
from collections import Counter
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import worldmodel.typeql as typeql  # noqa: E402
from worldmodel import DYNAMICS_MODULES, WorldModel  # noqa: E402
from worldmodel.examples import gearbox as g  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cycles", type=int, nargs="+", default=[0, 4, 16, 64])
ap.add_argument("--rounds", type=int, default=5)
a = ap.parse_args()

count = [0]
_run = typeql.run


def counted(tx, body, params=None):
    count[0] += 1
    return _run(tx, body, params)


def add_cycles(wm, ids, n):
    w = ids["world"]
    for i in range(n):
        day = g.TEST_RUN_2[1] + timedelta(days=i + 1)
        rep, test = f"o-rep-x{i}", f"o-test-x{i}"
        wm.add_entity("occurrence", f"replacement {i}", id=rep)
        wm.add_entity("occurrence", f"test run {i}", id=test)
        e1 = wm.account(w, {"actor": "technician", "patient": "bearing-4", "instrument": "bearing-press"},
                        day, day + timedelta(minutes=15), kind=["replacement", "action"], occurrence=rep,
                        attester="technician", id=f"ev-rep-x{i}")
        e2 = wm.account(w, {"actor": "technician", "patient": "gbx-100", "instrument": "test-rig"},
                        day + timedelta(minutes=30), day + timedelta(minutes=60), kind=["test", "action"],
                        occurrence=test, attester="technician", id=f"ev-test-x{i}")
        for e in (e1, e2):
            for x in wm.account_attestations(w, e, attester="technician"):
                wm.accept(x)
        wm.accept(wm.claim_effect(w, e2, "initiates", "has-quality",
                                  {"bearer": "gbx-100", "quality": "condition", "value": "operational"},
                                  attester="technician"))
        wm.accept(wm.claim_cause(w, rep, test, attester="technician"))


rows = []
for n in a.cycles:
    name = f"wm-dscale-{uuid.uuid4().hex[:8]}"
    wm = WorldModel.create(name, modules=DYNAMICS_MODULES)
    try:
        ids = g.extend_second_repair(wm, g.extend_causality(wm, g.extend_dynamics(wm, g.build(wm))))
        add_cycles(wm, ids, n)
        w = ids["world"]
        sizes = {k: wm.count(k) for k in ("event", "occurrence", "proposition", "attestation", "causes")}
        cond = {"bearer": "gbx-100", "quality": "condition"}
        questions = {
            "effects_of(ev-worklog-replacement)": lambda: wm.effects_of(w, "ev-worklog-replacement", g.AFTER),
            "changes(gbx-100, repair)": lambda: wm.changes(w, "gbx-100", g.REPAIR[0], g.AFTER),
            "causes_of(o-test-run)": lambda: wm.causes_of(w, "o-test-run", g.AFTER),
            "explain(operational)": lambda: wm.explain(w, "has-quality", {**cond, "value": "operational"}, g.AFTER),
            "process_steps(o-repair)": lambda: wm.process_steps(w, "o-repair", g.AFTER),
            "actions_of(technician)": lambda: wm.actions_of(w, "technician"),
            "occurrence_status(o-bearing-replacement)": lambda: wm.occurrence_status(w, "o-bearing-replacement", g.AFTER),
            "value_of(condition)": lambda: wm.value_of(w, "has-quality", cond, g.AFTER),
        }
        typeql.run = counted
        real_load = wm._load
        loads = Counter()

        def tallied(world, as_of=None, types=None, subjects=None, at=None, perspective="system"):
            loads[(tuple(types) if types else ("*",), "subjects" if subjects else "all")] += 1
            return real_load(world, as_of, types, subjects, at, perspective)

        wm._load = tallied
        result = {}
        for q, f in questions.items():
            times = []
            for _ in range(a.rounds):
                count[0] = 0
                wm.stats = {"queries": 0, "attestations": 0}
                loads.clear()
                start = time.perf_counter()
                f()
                times.append(time.perf_counter() - start)
            repeated = {f"{'/'.join(k[0])} ({k[1]})": v for k, v in loads.most_common() if v > 1}
            result[q] = {"median_ms": round(statistics.median(times) * 1000, 1), "typeql_queries": count[0],
                         "records_retrieved": wm.stats["attestations"], "repeated_loads": repeated}
        wm._load = real_load
        typeql.run = _run
        rows.append({"extra_cycles": n, "sizes": sizes, "questions": result})
    finally:
        typeql.run = _run
        wm.driver.databases.get(name).delete()
print(json.dumps(rows, indent=1))
