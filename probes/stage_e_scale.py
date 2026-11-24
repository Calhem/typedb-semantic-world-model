"""Stage E entry (LABS-1.054, step 3): read and write cost of the reference worlds at 1x, 5x and 10x dataset scale.

    uv run python -I probes/stage_e_scale.py <checkout> --build --axis worlds|perspectives --scale K --db NAME
    uv run python -I probes/stage_e_scale.py <checkout> --read --db NAME [--n 5] [--out FILE]
    uv run python -I probes/stage_e_scale.py <checkout> --drop --db NAME

The reference database (the 11 reference worlds of pre_e_b_snapshot.py --build: 322 attestations) is scale 1. Scale K
adds (K - 1) filler units, each about the size of the reference data, written BEFORE the reference worlds so that
ingestion of the reference worlds is measured into a database that already holds the extra data. Two axes, kept apart
so that their effects can be told apart:

- worlds: each unit is a family of NEW worlds with no link to the reference worlds: 3 actual worlds (written with
  68, 28 and 14 writes, in the proportions of `actual`, `lab` and `org`) and 2 hypothetical variants of each (3
  stipulated moves each): about 330 attestations per unit (a move writes about three). Reference answers cannot
  change; only cost can (the DI-9 cross-world question).
- perspectives: each unit adds 4 NEW attesters (perspectives) that write about 75 attestations each INTO the reference
  actual worlds (`actual`, `lab`, `org`), about new objects and places only. Reference subjects are not mentioned, so
  reference answers about them cannot change, but every reader that loads a whole world (or a whole perspective
  list) sees more data.

Filler is synthetic: `located-at` facts (until superseded) and `move` events among filler objects, ids prefixed
`zf-`, valid times in 2025 (before the reference worlds' times).

--build prints JSON: seconds and attestations written for the filler and for the reference worlds (ingestion
throughput, attestations per second), total attestations, database bytes (du inside the wm-typedb container).

--read runs a FIXED call set on the reference worlds only: the readers of pre_e_b_read_bench.py (--more and
--occurrence) with subjects chosen from reference attestations only (filler excluded), so the same calls are made at
every scale. Each call is made once to warm up, then `n` interleaved rounds. For every call: every latency (ms),
TypeDB queries and read transactions (deterministic: the same in every round). Prints JSON with per-reader latency
distributions (p50, p90, p95, p99, max over all samples) and the per-call data.
"""

import argparse
import json
import random
import re
import statistics
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--db", required=True)
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument("--build", action="store_true")
g.add_argument("--read", action="store_true")
g.add_argument("--drop", action="store_true")
ap.add_argument("--axis", choices=("worlds", "perspectives"), default="worlds")
ap.add_argument("--scale", type=int, default=1)
ap.add_argument("--n", type=int, default=5)
ap.add_argument("--seed", type=int, default=54)
ap.add_argument("--out")
ap.add_argument("--answers", help="--read: also write every call's answer (ids and clock times masked) to this file")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, connect, laboratory as lab, organisation as org  # noqa: E402
from worldmodel import typeql as q  # noqa: E402

DOCKER = str(Path.home() / ".docker" / "bin" / "docker")
FILLER_START = datetime(2025, 1, 1, 8, 0, tzinfo=timezone.utc)
REFERENCE_WORLDS = ["actual", "lab", "lab-plan-recal", "lab-plan-tom", "org", "org-plan-reorg", "plan-apprentice",
                    "plan-move-bench", "plan-relubricate-only", "plan-rig-control", "plan-steel-cover"]


class CountingTx:
    def __init__(self, tx, c):
        self._tx, self._c = tx, c

    def query(self, *x, **k):
        self._c["queries"] += 1
        return self._tx.query(*x, **k)

    def __enter__(self):
        self._tx.__enter__()
        return self

    def __exit__(self, *e):
        return self._tx.__exit__(*e)

    def __getattr__(self, n):
        return getattr(self._tx, n)


class Counting:
    def __init__(self, real):
        self._real, self.c = real, {"queries": 0, "transactions": 0}

    def transaction(self, *x, **k):
        self.c["transactions"] += 1
        return CountingTx(self._real.transaction(*x, **k), self.c)

    def __getattr__(self, n):
        return getattr(self._real, n)


def db_bytes(name):
    r = subprocess.run([DOCKER, "exec", "wm-typedb", "du", "-sb", f"/var/lib/typedb/data/{name}"],
                       capture_output=True, text=True)
    return int(r.stdout.split()[0]) if r.returncode == 0 else None


def dist(xs):
    s = sorted(xs)
    pct = lambda p: round(s[min(len(s) - 1, int(round(p * (len(s) - 1))))], 1)
    return {"n": len(s), "min": round(s[0], 1), "p50": round(statistics.median(s), 1), "p90": pct(0.90),
            "p95": pct(0.95), "p99": pct(0.99), "max": round(s[-1], 1), "mean": round(statistics.fmean(s), 1)}


def filler_family(wm, rnd, unit, counter):
    """A family of new worlds (axis `worlds`): 3 actual worlds and 2 variants each."""
    t_end = FILLER_START
    for j, size in enumerate((68, 28, 14)):
        w = wm.create_world(f"filler {unit}.{j}", id=f"zf-{unit}-w{j}")
        objs = [wm.add_entity("physical-object", f"zf {unit}.{j} o{i}", id=f"zf-{unit}-{j}-o{i}") for i in range(size // 4)]
        pls = [wm.add_entity("place", f"zf {unit}.{j} p{i}", id=f"zf-{unit}-{j}-p{i}") for i in range(max(3, size // 20))]
        for o in objs:
            wm.attest(w, "located-at", {"located": o, "place": rnd.choice(pls)}, start=FILLER_START, until_superseded=True)
            counter[0] += 1
        t = FILLER_START
        for _ in range(size - len(objs)):
            t += timedelta(seconds=rnd.randint(5, 60))
            wm.move(w, rnd.choice(objs), rnd.choice(pls), t)
            counter[0] += 1
        t_end = max(t_end, t)
        for v in range(2):
            h = wm.create_world(f"filler {unit}.{j} plan {v}", kind="hypothetical", base=w, branch_at=t,
                                id=f"zf-{unit}-w{j}-v{v}")
            tv = t
            for _ in range(3):
                tv += timedelta(seconds=30)
                wm.move(h, rnd.choice(objs), rnd.choice(pls), tv)
                counter[0] += 1


def filler_perspectives(wm, rnd, unit, counter):
    """New attesters writing into the reference actual worlds about new things only (axis `perspectives`)."""
    for j, world in enumerate(("actual", "lab", "org", "actual")):
        agent = wm.add_entity("social-object", f"zf observer {unit}.{j}", id=f"zf-{unit}-a{j}")
        objs = [wm.add_entity("physical-object", f"zf {unit}.{j} o{i}", id=f"zf-{unit}-{j}-o{i}") for i in range(6)]
        pls = [wm.add_entity("place", f"zf {unit}.{j} p{i}", id=f"zf-{unit}-{j}-p{i}") for i in range(4)]
        for o in objs:
            wm.attest(world, "located-at", {"located": o, "place": rnd.choice(pls)}, start=FILLER_START,
                      until_superseded=True, attester=agent)
            counter[0] += 1
        t = FILLER_START
        for _ in range(23):
            t += timedelta(seconds=rnd.randint(5, 60))
            wm.move(world, rnd.choice(objs), rnd.choice(pls), t, attester=agent)
            counter[0] += 1


def build():
    from worldmodel.examples import gearbox as gb, laboratory as lab_ex, organisation as org_ex
    driver = connect()
    rnd = random.Random(a.seed)
    wm = WorldModel.create(a.db, driver=driver, modules=CORE_MODULES, replace=True)
    for p in ("mechanical", "organisation", "laboratory"):
        wm.install_profile(p)
    out = {"axis": a.axis, "scale": a.scale, "db": a.db}

    def reference():
        gids = gb.build(wm)
        gb.extend_mechanical(wm, gb.extend_qualities_agency(wm, gb.extend_causality(wm, gb.extend_dynamics(
            wm, gb.extend_spatial(wm, gids)))))
        org_ex.build_organisation(wm)
        lab_ex.build_laboratory(wm)

    counter = [0]
    t0 = time.perf_counter()
    if a.axis == "perspectives" and a.scale > 1:
        # the perspectives write into the reference worlds, so those worlds must exist first: build the reference
        # worlds, then the filler (the reference ingestion is then measured into the scale-1 database)
        before = wm.count("attestation")
        r0 = time.perf_counter()
        reference()
        out["reference"] = {"seconds": round(time.perf_counter() - r0, 2), "attestations": wm.count("attestation") - before}
        t0 = time.perf_counter()
        for u in range(1, a.scale):
            filler_perspectives(wm, rnd, u, counter)
        out["filler"] = {"seconds": round(time.perf_counter() - t0, 2), "writes": counter[0],
                         "attestations": wm.count("attestation") - out["reference"]["attestations"]}
    else:
        for u in range(1, a.scale):
            filler_family(wm, rnd, u, counter)
        out["filler"] = {"seconds": round(time.perf_counter() - t0, 2), "writes": counter[0],
                         "attestations": wm.count("attestation")}
        before = wm.count("attestation")
        r0 = time.perf_counter()
        reference()
        out["reference"] = {"seconds": round(time.perf_counter() - r0, 2), "attestations": wm.count("attestation") - before}
    for part in ("filler", "reference"):
        p = out[part]
        p["attestations_per_second"] = round(p["attestations"] / p["seconds"], 1) if p["seconds"] else None
    out["attestations"] = wm.count("attestation")
    with wm._reading() as tx:
        out["worlds"] = len(q.rows(tx, "match $w isa world;"))
    out["database_bytes"] = db_bytes(a.db)
    return out


ATT = re.compile(r"att:[0-9a-f]{16}")
CLOCK = re.compile(r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d\.\d{6}\+00:00")


def mask(x):
    """An answer as canonical text with attestation ids and system-clock times masked (they differ between builds);
    lists are sorted by their text, since they are ordered by attestation id."""
    def walk(v):
        if isinstance(v, dict):
            return {str(k): walk(w) for k, w in v.items()}
        if isinstance(v, (list, tuple, set, frozenset)):
            return sorted((walk(w) for w in v), key=lambda w: json.dumps(w, sort_keys=True, default=str))
        if hasattr(v, "__dataclass_fields__"):
            return {f: walk(getattr(v, f)) for f in v.__dataclass_fields__}
        if hasattr(v, "_asdict"):
            return walk(v._asdict())
        return CLOCK.sub("<clock>", ATT.sub("att:*", str(v))) if v is not None else None
    return walk(x)


def calls_for(wm):
    """The fixed call set of pre_e_b_read_bench.py (--more --occurrence), on reference attestations only."""
    calls = {}
    for w in REFERENCE_WORLDS:
        atts = {k: at for k, at in wm.visible(w).items()
                if not any(x.startswith("zf-") for v in at.roles.values() for x in v) and not str(at.attester).startswith("zf-")}
        mention = Counter(x for at in atts.values() for v in at.roles.values() for x in v)
        with wm._reading() as tx:
            kinds = wm._kinds_of(tx, sorted(mention))
        bounds = sorted({x for at in atts.values() for win in (at.start, at.end) if win is not None
                         for x in (win.earliest, win.latest) if x is not None})
        t = bounds[len(bounds) // 2]

        def top(label, k=2):
            return [x for x, _ in mention.most_common() if kinds.get(x) and wm.is_a(kinds[x], label)][:k]

        for x in top("particular", 3):
            calls[("facts_about", w, x)] = (wm.facts_about, (w, x, t), {})
            calls[("parts", w, x)] = (wm.parts, (w, x, t), {})
            calls[("changes", w, x)] = (wm.changes, (w, x, bounds[0], bounds[-1]), {})
            calls[("value_at", w, x)] = (wm.value_at, (w, "located-at", x, t), {})
        for x in sorted({o for at in atts.values() if at.kind == "describes" for o in at.roles.get("occurrence", [])}):
            calls[("occurrence", w, x)] = (wm.occurrence, (w, x), {})
        for x in top("occurrence"):
            calls[("occurrence_status", w, x)] = (wm.occurrence_status, (w, x, t), {})
            calls[("causes_of", w, x)] = (wm.causes_of, (w, x, t), {})
        holdings = sorted({(at.roles["classified"][0], at.roles["class"][0], (at.roles.get("context") or [None])[0])
                           for at in atts.values() if wm.is_a(at.ctype, "classified-as")}, key=str)[:3]
        for h, c, ctx in holdings:
            calls[("capable", w, f"{h}/{c}")] = (wm.capable, (w, h, c, t), {"context": ctx})
        for office, ctx in sorted({(at.roles["class"][0], at.roles["context"][0]) for at in atts.values()
                                   if wm.is_a(at.ctype, "office-holding")})[:2]:
            calls[("office_holders", w, office)] = (org.office_holders, (wm, w, office, ctx, t), {})
        for x in sorted({at.roles["classified"][0] for at in atts.values() if wm.is_a(at.ctype, "office-holding")})[:2]:
            calls[("offices_of", w, x)] = (org.offices_of, (wm, w, x, t), {})
        for h, p, sc in sorted({(at.roles["holder"][0], at.roles["power"][0], at.roles["scope"][0])
                                for at in atts.values() if wm.is_a(at.ctype, "authorisation")})[:2]:
            calls[("authorised", w, f"{h}/{p}")] = (org.authorised, (wm, w, h, p, sc, t), {})
        for x in top("sample", 3):
            calls[("provenance", w, x)] = (lab.provenance, (wm, w, x, t), {})
        for x in sorted({at.roles["calibrated"][0] for at in atts.values() if wm.is_a(at.ctype, "calibration-of")})[:2]:
            calls[("calibration_status", w, x)] = (lab.calibration_status, (wm, w, x, t), {})
        for x in top("information-object", 2):
            calls[("interpretations", w, x)] = (lab.interpretations, (wm, w, x, t), {})
    return calls


def read():
    driver = Counting(connect())
    wm = WorldModel(driver, a.db)
    calls = calls_for(wm)
    results, answers = {}, {}
    for key, (fn, args, kw) in calls.items():
        try:
            answers[" ".join(key)] = mask(fn(*args, **kw))
            results[key] = {"ms": []}
        except Exception as e:                                                  # noqa: BLE001
            print(f"skip {key}: {type(e).__name__}: {e}", file=sys.stderr)
    for _ in range(a.n):
        for key in results:
            fn, args, kw = calls[key]
            before = dict(driver.c)
            t0 = time.perf_counter()
            fn(*args, **kw)
            results[key]["ms"].append((time.perf_counter() - t0) * 1000)
            results[key]["queries"] = driver.c["queries"] - before["queries"]
            results[key]["transactions"] = driver.c["transactions"] - before["transactions"]
    by_reader = {}
    for (reader, w, x), v in results.items():
        r = by_reader.setdefault(reader, {"samples": [], "queries": 0, "transactions": 0, "calls": 0})
        r["samples"] += v["ms"]
        r["queries"] += v["queries"]
        r["transactions"] += v["transactions"]
        r["calls"] += 1
    if a.answers:
        Path(a.answers).write_text(json.dumps(answers, indent=0, sort_keys=True))
    every = [x for v in results.values() for x in v["ms"]]
    return {
        "db": a.db, "n": a.n, "calls": len(results),
        "all": dist(every) | {"queries_per_round": sum(v["queries"] for v in results.values()),
                              "transactions_per_round": sum(v["transactions"] for v in results.values()),
                              "seconds_per_round": round(sum(every) / a.n / 1000, 1)},
        "by_reader": {k: dist(v["samples"]) | {"calls": v["calls"], "queries_per_call": round(v["queries"] / v["calls"], 1),
                                               "transactions_per_call": round(v["transactions"] / v["calls"], 1)}
                      for k, v in sorted(by_reader.items())},
        "per_call": {f"{r} {w} {x}": {"median_ms": round(statistics.median(v["ms"]), 1), "ms": [round(m, 2) for m in v["ms"]],
                                      "queries": v["queries"], "transactions": v["transactions"]}
                     for (r, w, x), v in results.items()},
    }


if a.drop:
    d = connect()
    if d.databases.contains(a.db):
        d.databases.get(a.db).delete()
    sys.exit(0)
res = build() if a.build else read()
text = json.dumps(res, indent=1)
if a.out:
    Path(a.out).write_text(text)
print(text if a.build else json.dumps({"all": res["all"], "calls": res["calls"]}, indent=1))
