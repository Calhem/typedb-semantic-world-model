"""Cost of the selective path's targeted identity retrieval for answer values (F-5 fix, LABS-1.004), isolated.

    uv run python -I scripts/measure_identity_cost.py [--objects 200 --places 30 --moves 300 --links 10 --rounds 5]

Builds one throwaway world (wm-idcost-*, deleted afterwards) like the benchmark's, then adds `--links` accepted
same-as links between existing places and new alias places, with some located-at facts naming the aliases. The same
value_at questions are asked on the selective path in alternating rounds, with the value-identity step on and off
(off = `_linked_ids` returns nothing, which is the pre-fix behaviour). Same database, same questions, so the only
difference is the correction. Reports per-round medians, TypeQL queries per question, and how many answers differ.
"""

import argparse
import json
import random
import statistics
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import worldmodel.typeql as typeql  # noqa: E402
from worldmodel import WorldModel, connect  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--objects", type=int, default=200)
ap.add_argument("--places", type=int, default=30)
ap.add_argument("--moves", type=int, default=300)
ap.add_argument("--links", type=int, default=10)
ap.add_argument("--queries", type=int, default=60)
ap.add_argument("--rounds", type=int, default=5)
ap.add_argument("--seed", type=int, default=11)
a = ap.parse_args()
START = datetime(2026, 11, 9, 8, 0, tzinfo=timezone.utc)
count = [0]
_run = typeql.run


def counted(tx, body, params=None):
    count[0] += 1
    return _run(tx, body, params)


typeql.run = counted
rnd = random.Random(a.seed)
driver = connect()
name = f"wm-idcost-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(name, driver=driver)
try:
    w = wm.create_world("actual")
    objs = [wm.add_entity("physical-object", f"o{i}") for i in range(a.objects)]
    pls = [wm.add_entity("place", f"p{i}") for i in range(a.places)]
    for o in objs:
        wm.attest(w, "located-at", {"located": o, "place": rnd.choice(pls)}, start=START, until_superseded=True)
    t = START
    for _ in range(a.moves):
        t += timedelta(seconds=rnd.randint(5, 60))
        wm.move(w, rnd.choice(objs), rnd.choice(pls), t)
    aliases = []
    for i in range(a.links):
        alias = wm.add_entity("place", f"alias-{i}")
        wm.attest(w, "same-as", {"same": [pls[i], alias]}, until_superseded=True)
        aliases.append(alias)
    for i in range(a.links):          # object i is also said to be at place i's alias (and is moved to place i)
        wm.move(w, objs[i], pls[i], t + timedelta(seconds=1))
        wm.attest(w, "located-at", {"located": objs[i], "place": aliases[i]}, start=t + timedelta(seconds=1),
                  until_superseded=True)
    t += timedelta(seconds=1)
    t_end = t + timedelta(minutes=1)
    # Half the questions ask about the objects with an alias account, after it starts (where the fix matters).
    questions = [(objs[i % max(a.links, 1)], t_end) if i % 2 == 0 and a.links else
                 (rnd.choice(objs), START + (t_end - START) * rnd.random()) for i in range(a.queries)]
    original = wm._linked_ids
    results = {"on": [], "off": []}
    answers = {}
    for r in range(a.rounds):
        for mode in (("on", "off") if r % 2 == 0 else ("off", "on")):
            wm._linked_ids = original if mode == "on" else (lambda ids: set())
            times, queries, got = [], [], []
            for o, qt in questions:
                count[0] = 0
                s = time.perf_counter()
                got.append(wm.value_at(w, "located-at", o, qt))
                times.append(time.perf_counter() - s)
                queries.append(count[0])
            results[mode].append({"median_ms": round(statistics.median(times) * 1000, 2),
                                  "queries_per_question": round(statistics.mean(queries), 2)})
            answers[mode] = got
    wm._linked_ids = original
    full = WorldModel.open(name, driver=driver)
    full.selective = False
    reference = [full.value_at(w, "located-at", o, qt) for o, qt in questions]
    out = {"dataset": vars(a),
           "rounds": results,
           "median_of_rounds_ms": {m: statistics.median(x["median_ms"] for x in v) for m, v in results.items()},
           "queries_per_question": {m: v[0]["queries_per_question"] for m, v in results.items()},
           "answers_differing_from_full_load": {m: sum(x != y for x, y in zip(answers[m], reference)) for m in answers}}
    print(json.dumps(out, indent=1))
finally:
    driver.databases.get(name).delete()
