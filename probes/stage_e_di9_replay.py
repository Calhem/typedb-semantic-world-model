"""Stage E DI-9 investigation (LABS-1.055): replay a reader's exact TypeDB queries in isolation, and time alternative
formulations of the slow ones. Read-only.

    uv run python -I probes/stage_e_di9_replay.py <checkout> --db NAME --call CALL [--reps 15] [--out FILE]

CALL is one of: parts-bay-1 (parts actual bay-1), occurrence-o-repair (occurrence actual o-repair),
where-gbx (where actual gbx-100 f-workshop), core03-value-at (value_at on a Core 0.3 benchmark database: the first
question of stage_e_core03_selective.py, actual world, object o5, at the middle of the moves).

1. Capture: the call runs once with `typeql.run` patched to record every query text and its parameters.
2. Replay: each captured query runs `reps` times, each in a new read transaction, timed to the last row (rows or
   documents), so a query's own cost is seen without the reader around it. Reported: rows, median, min, max, and the
   spread (max / min), which shows whether one query's cost is stable or switches between two levels.
3. Variants (same answers, different formulation), for the shapes the instrumented run found slow:
   - supersession queries anchored on the attestation ids the head query already returned (one disjunction of ids),
     instead of re-matching the world head;
   - subject-bound queries written subject first, and without the world/attester join (to see what the subject alone
     narrows to);
   - database-wide counts of the relations those queries join (supersession, acceptance, links of the subject).
   Each variant is checked to return the same rows as the captured query (as sets of the selected values).
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--db", required=True)
ap.add_argument("--call", required=True, choices=("parts-bay-1", "occurrence-o-repair", "where-gbx", "core03-value-at"))
ap.add_argument("--reps", type=int, default=15)
ap.add_argument("--out")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import WorldModel, connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import gearbox as gb  # noqa: E402
from typedb.driver import TransactionType  # noqa: E402

captured = []
_run = q.run


def capturing(tx, body, params=None):
    captured.append((body, dict(params or {})))
    return _run(tx, body, params)


driver = connect()
wm = WorldModel(driver, a.db)


def setup():
    """Arguments for the call, computed before capture so that only the call's own queries are captured."""
    if a.call == "parts-bay-1":
        b = sorted({x for at in wm.visible("actual").values() if not str(at.attester).startswith("zf-")
                    for win in (at.start, at.end) if win is not None for x in (win.earliest, win.latest) if x is not None})
        return {"t": b[len(b) // 2]}
    if a.call == "core03-value-at":
        with wm._reading() as tx:
            ids = {q.opt(r, "n"): q.opt(r, "i") for r in q.rows(tx, 'match $x isa particular, has name $n, has wm-id $i; { $n == "o5"; } or { $n == "p0"; };')}
            world = q.opt(q.rows(tx, 'match $w isa world, has name "actual", has wm-id $i;')[0], "i")
            ts = sorted(q.opt(r, "t") for r in q.rows(tx, "match $a isa attestation, has valid-from-earliest $t;"))
        return {"world": world, "o": ids["o5"], "t": ts[len(ts) // 2]}
    return {}


ARGS = setup()


def the_call():
    if a.call == "parts-bay-1":
        return wm.parts("actual", "bay-1", ARGS["t"])
    if a.call == "occurrence-o-repair":
        return wm.occurrence("actual", "o-repair")
    if a.call == "where-gbx":
        return wm.where("actual", "gbx-100", "f-workshop", gb.AFTER)
    return wm.value_at(ARGS["world"], "located-at", ARGS["o"], ARGS["t"])


the_call()                                   # warm up
q.run = capturing
the_call()
q.run = _run


def execute(body, params):
    with driver.transaction(a.db, TransactionType.READ) as tx:
        t0 = time.perf_counter()
        ans = q.run(tx, body, params)
        out = list(ans.as_concept_documents() if "fetch" in body else ans.as_concept_rows())
        return time.perf_counter() - t0, out


def timed(body, params, reps=None):
    times, n = [], None
    for _ in range((reps or a.reps) + 1):
        s, out = execute(body, params)
        times.append(s)
        n = len(out)
    times = times[1:]
    return {"rows": n, "median_ms": round(statistics.median(times) * 1000, 2), "min_ms": round(min(times) * 1000, 2),
            "max_ms": round(max(times) * 1000, 2), "spread": round(max(times) / max(min(times), 1e-6), 1)}


def values(out, var):
    return sorted(str(q.opt(r, var)) for r in out)


report = {"db": a.db, "call": a.call, "reps": a.reps, "queries": [], "variants": []}
for i, (body, params) in enumerate(captured):
    r = timed(body, params)
    r.update(i=i, query=" ".join(body.split())[:400], params={k: str(v) for k, v in params.items()})
    report["queries"].append(r)
report["queries"].sort(key=lambda r: -r["median_ms"])
report["captured_total_median_ms"] = round(sum(r["median_ms"] for r in report["queries"]), 1)

# --- variants for the slowest captured queries -------------------------------------------------------------------
HEAD_END = "has recorded-at $rec;"


def variant(name, body, params, compare_body=None, compare_params=None, var=None):
    r = timed(body, params)
    r["variant"] = name
    r["query"] = " ".join(body.split())[:400]
    if compare_body is not None:
        _, o1 = execute(compare_body, compare_params)
        _, o2 = execute(body, params)
        r["same_values_as_captured"] = values(o1, var) == values(o2, var)
    report["variants"].append(r)


subject_done = False
for body, params in captured:
    flat = " ".join(body.split())
    # supersession queries: anchor on the head query's attestation ids
    if "$su isa supersession" in flat:
        head = flat[:flat.index("$su isa supersession")]
        _, heads = execute(head.strip() + " select $aid;", params)
        aids = sorted({q.opt(r, "aid") for r in heads})
        tail = flat[flat.index("$su isa supersession"):]
        params2 = {k: v for k, v in params.items() if k not in ("world", "sid", "klim", "vlim", "at")}
        if aids:
            alts = " or ".join(f'{{ $a has wm-id "{x}"; }}' for x in aids)
            anchored = f"match $a isa attestation, has wm-id $aid; {alts}; {tail}"
        else:
            anchored = None
        name = "supersession" + (" + new acceptances" if "$nacc" in flat else "")
        variant(f"{name}: as captured", body, params)
        if anchored:
            variant(f"{name}: anchored on the {len(aids)} head ids", anchored, params2, body, params, "aid")
        else:
            report["variants"].append({"variant": f"{name}: head returns no attestation, so the query is not needed",
                                       "rows": 0, "median_ms": 0.0})
    # subject-bound queries: subject first; and the subject's links alone
    if not subject_done and "$subj has wm-id == $sid" in flat and "isa same-as" in flat and "$who has wm-id $wid" in flat:
        subject_done = True
        sid = params["sid"]
        variant("same-as for the subject: as captured", body, params)
        variant("same-as for the subject: subject first, no world join",
                "match $subj has wm-id == $sid; $c links ($kr: $subj); $c isa same-as; $a isa attestation (content: $c); select $a;",
                {"sid": sid})
        variant("every content the subject plays a role in (any world)",
                "match $subj has wm-id == $sid; $c links ($kr: $subj); select $c;", {"sid": sid})
        variant("the subject's contents of the type only (no attestation join)",
                "match $subj has wm-id == $sid; $c links ($kr: $subj); $c isa same-as; select $c;", {"sid": sid})
        variant("the subject's contents and their attestations (no type)",
                "match $subj has wm-id == $sid; $c links ($kr: $subj); $a isa attestation (content: $c); select $a;",
                {"sid": sid})
        loc = ("match $subj has wm-id == $sid; $c links ($kr: $subj); $c isa located-at; "
               "$c has proposition-key $ck; select $ck;")
        variant("the subject's located-at contents only", loc, {"sid": sid})
        _, keys = execute(loc, {"sid": sid})
        ks = sorted({q.opt(r, "ck") for r in keys})
        if ks and "world" in params:
            alts = " or ".join(f'{{ $c has proposition-key "{k}"; }}' for k in ks)
            step2 = (f"match $w isa world, has wm-id == $world; {alts}; $a isa attestation (content: $c, context: $w), "
                     "has wm-id $aid; select $aid;")
            variant(f"step 2: the world's attestations of those {len(ks)} contents, by key", step2, {"world": params["world"]})
            variant("the same attestations as one subject-bound query (head form)",
                    "match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), "
                    "has wm-id $aid, has recorded-at $rec; $c isa located-at; $subj has wm-id == $sid; "
                    "$c links ($kr: $subj); select $aid;", {"world": params["world"], "sid": sid},
                    step2, {"world": params["world"]}, "aid")

COUNTS = {"supersessions in the database": "match $su isa supersession; select $su;",
          "acceptances in the database": "match $x isa acceptance; select $x;",
          "attestations in the database": "match $a isa attestation; select $a;"}
for n, b in COUNTS.items():
    r = timed(b, None, reps=3)
    r["variant"] = n
    report["variants"].append(r)
text = json.dumps(report, indent=1)
if a.out:
    Path(a.out).write_text(text)
print(json.dumps({"call": a.call, "db": a.db, "captured": len(captured), "captured_total_median_ms": report["captured_total_median_ms"],
                  "slowest": [{k: r[k] for k in ("rows", "median_ms", "min_ms", "max_ms", "spread")} | {"q": r["query"][:160]}
                              for r in report["queries"][:5]],
                  "variants": [{k: v for k, v in r.items() if k != "query"} for r in report["variants"]]}, indent=1))
