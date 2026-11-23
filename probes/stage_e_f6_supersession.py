"""LABS-1.057, F6 investigation (no correction): the anchored supersession lookup of `_level`. Read-only.

    uv run python -I probes/stage_e_f6_supersession.py <checkout> --db NAME (--core03 K | --where) [--questions 30]
                                                         [--n 5] [--out FILE]

1. Capture. Runs the reader with the checkout's code and records every supersession follow-up query `_level` makes
   (`_anchored` with the supersession body): its anchor ids, its head and the head's parameters.
   --core03 K: the Core 0.3 `value_at` questions of probes/stage_e_core03_selective.py (seed 11, scale K; the first
   --questions of them, the same ones in the same order), selective path. --where: `where("actual", "gbx-100",
   "f-workshop", AFTER)` of probes/stage_e_di9_instrumented.py.
2. Replay. Each captured lookup is run in every formulation below, in one read transaction per round, rounds rotating
   the order of formulations; per formulation: median ms per lookup (submit to last row), rows, and whether its rows
   equal the current form's (as sets of (aid, nid, srec, nw, nse, nwid, nst); M is compared on (aid, nid) only).

   C  current (O-1): given rows, `$a isa attestation (content: $c), has wm-id == $anchor`
   N  no content role on the anchor: `$a isa attestation, has wm-id == $anchor`
   L  `links` form: `$su isa supersession; $su links (old: $a); $su links (new: $n);`
   S  two steps: (aid, nid, srec) first, then the new attestations' attributes by id (given rows)
   P  one query per anchor (a plain parameter, no given rows)
   H  the head form (before O-1): the head with its own parameters + the body
   M  minimal: only `$su isa supersession (old: $a, new: $n); $n has wm-id $nid;` (where the cost is)
   R  only the supersession relation's own attribute: `... (old: $a, new: $n), has recorded-at $srec;`

No formulation applies a time or perspective filter: `_level` applies knowledge time, branch time and the new
attestation's world in Python afterwards (`_load`), and acceptances come from separate queries. So identical rows
mean identical temporal and perspective semantics.
Also counts supersessions in the database, in the asked world and old-side rows per anchor.
"""

import argparse
import json
import random
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--db", required=True)
ap.add_argument("--core03", type=int)
ap.add_argument("--where", action="store_true")
ap.add_argument("--questions", type=int, default=30)
ap.add_argument("--n", type=int, default=5)
ap.add_argument("--out")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import WorldModel, connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402

ANCHOR = "match $a isa attestation (content: $c), has wm-id == $anchor; $a has wm-id $aid;"
REST = """ $n has wm-id $nid, has stance $nst; $n isa attestation (context: $nwo, attester: $nwho);
  $nwo has wm-id $nw; $nwho has wm-id $nwid; try { $n has valid-from-earliest $nse; };"""
SUPER = " $su isa supersession (old: $a, new: $n), has recorded-at $srec;" + REST
KEYS = ("aid", "nid", "srec", "nw", "nse", "nwid", "nst")
real_rows = q.rows

driver = connect()
wm = WorldModel(driver, a.db)
captured = []
real_anchored = wm._anchored


def capture(tx, aids, head, params, body, extra):
    if "supersession (old: $a, new: $n), has recorded-at $srec" in body:
        captured.append({"aids": list(aids), "head": head, "params": params})
    return real_anchored(tx, aids, head, params, body, extra)


wm._anchored = capture
if a.core03:
    START = datetime(2026, 11, 9, 8, 0, tzinfo=timezone.utc)
    k = a.core03
    n_obj, n_pl, n_mv = 200 * k, 30 * k, 1000 * k
    rnd = random.Random(11)
    with wm._reading() as tx:
        ids = {q.opt(r, "n"): q.opt(r, "i") for r in q.rows(tx, "match $x isa particular, has name $n, has wm-id $i;")}
        worlds = {q.opt(r, "n"): q.opt(r, "i") for r in q.rows(tx, "match $x isa world, has name $n, has wm-id $i;")}
    w, h = worlds["actual"], worlds["plan"]
    objs = [ids[f"o{i}"] for i in range(n_obj)]
    pls = [ids[f"p{i}"] for i in range(n_pl)]
    for _ in objs:
        rnd.choice(pls)
    t = START
    for _ in range(n_mv):
        t += timedelta(seconds=rnd.randint(5, 60))
        rnd.choice(objs); rnd.choice(pls)
    for _ in range(n_mv // 20):
        t += timedelta(seconds=30)
        rnd.choice(objs); rnd.choice(pls)
    questions = [(rnd.choice([w, h]), rnd.choice(objs), START + (t - START) * rnd.random()) for _ in range(60)]
    wm.selective = True
    for world, o, when in questions[:a.questions]:
        wm.value_at(world, "located-at", o, when)
    asked_world = w
else:
    from worldmodel.examples import gearbox as gb
    wm.where("actual", "gbx-100", "f-workshop", gb.AFTER)
    asked_world = "actual"
wm._anchored = real_anchored


def tuples(rows, keys=KEYS):
    return sorted(tuple(str(q.opt(r, k)) for k in keys) for r in rows)


def F_C(tx, c):
    return tuples(real_rows(tx, ANCHOR + SUPER, [{"anchor": x} for x in c["aids"]]))


def F_N(tx, c):
    return tuples(real_rows(tx, "match $a isa attestation, has wm-id == $anchor; $a has wm-id $aid;" + SUPER,
                            [{"anchor": x} for x in c["aids"]]))


def F_L(tx, c):
    body = " $su isa supersession, has recorded-at $srec; $su links (old: $a); $su links (new: $n);" + REST
    return tuples(real_rows(tx, ANCHOR + body, [{"anchor": x} for x in c["aids"]]))


def F_S(tx, c):
    first = real_rows(tx, ANCHOR + " $su isa supersession (old: $a, new: $n), has recorded-at $srec; $n has wm-id $nid;",
                      [{"anchor": x} for x in c["aids"]])
    pairs = [(q.opt(r, "aid"), q.opt(r, "nid"), q.opt(r, "srec")) for r in first]
    if not pairs:
        return []
    second = real_rows(tx, """match $n isa attestation (context: $nwo, attester: $nwho), has wm-id == $want, has stance $nst;
        $n has wm-id $nid; $nwo has wm-id $nw; $nwho has wm-id $nwid; try { $n has valid-from-earliest $nse; };""",
                       [{"want": x} for x in sorted({p[1] for p in pairs})])
    attrs = {q.opt(r, "nid"): r for r in second}
    out = []
    for aid, nid, srec in pairs:
        r = attrs[nid]
        out.append((str(aid), str(nid), str(srec), str(q.opt(r, "nw")), str(q.opt(r, "nse")), str(q.opt(r, "nwid")),
                    str(q.opt(r, "nst"))))
    return sorted(out)


def F_P(tx, c):
    out = []
    for x in c["aids"]:
        out += tuples(real_rows(tx, ANCHOR + SUPER, {"anchor": x}))
    return sorted(out)


def F_H(tx, c):
    from worldmodel.model import SUBJECT_ROLE
    return tuples(real_rows(tx, c["head"] + SUPER.replace(SUBJECT_ROLE, "", 1), c["params"]))


def F_M(tx, c):
    return tuples(real_rows(tx, ANCHOR + " $su isa supersession (old: $a, new: $n); $n has wm-id $nid;",
                            [{"anchor": x} for x in c["aids"]]), ("aid", "nid"))


def F_R(tx, c):
    return tuples(real_rows(tx, ANCHOR + " $su isa supersession (old: $a, new: $n), has recorded-at $srec; $n has wm-id $nid;",
                            [{"anchor": x} for x in c["aids"]]), ("aid", "nid", "srec"))


FORMS = {"C": F_C, "N": F_N, "L": F_L, "S": F_S, "P": F_P, "H": F_H, "M": F_M, "R": F_R}
times = {f: [[] for _ in captured] for f in FORMS}
answers = {f: [None for _ in captured] for f in FORMS}
order = list(FORMS)
for rnd_i in range(a.n):
    rot = order[rnd_i % len(order):] + order[:rnd_i % len(order)]
    with wm._reading() as tx:
        for f in rot:
            for i, c in enumerate(captured):
                t0 = time.perf_counter()
                ans = FORMS[f](tx, c)
                times[f][i].append((time.perf_counter() - t0) * 1000)
                assert answers[f][i] in (None, ans), (f, i)
                answers[f][i] = ans


def project(rows, n):
    return sorted({r[:n] for r in rows})


res = {"db": a.db, "reader": f"core03-{a.core03} value_at x{a.questions}" if a.core03 else "where actual gbx-100",
       "lookups": len(captured), "anchors_per_lookup": statistics.fmean(len(c["aids"]) for c in captured) if captured else 0,
       "forms": {}}
for f in FORMS:
    width = 2 if f == "M" else 3 if f == "R" else 7
    same = all(answers[f][i] == (answers["C"][i] if width == 7 else project(answers["C"][i], width))
               for i in range(len(captured)))
    med = [statistics.median(ts) for ts in times[f]]
    res["forms"][f] = {"median_ms_per_lookup": round(statistics.median(med), 2) if med else None,
                       "sum_of_medians_ms": round(sum(med), 1), "rows": sum(len(x) for x in answers[f]), "same_rows": same}
with wm._reading() as tx:
    res["supersessions_in_database"] = len(real_rows(tx, "match $su isa supersession;"))
    res["supersessions_in_world"] = len(real_rows(tx, """match $w isa world, has wm-id == $world;
        $o isa attestation (context: $w); $su isa supersession (old: $o);""", {"world": asked_world}))
    res["attestations_in_database"] = len(real_rows(tx, "match $x isa attestation;"))
text = json.dumps(res, indent=1)
if a.out:
    Path(a.out).write_text(text)
print(text)
