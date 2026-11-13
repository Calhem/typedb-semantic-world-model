"""Pre-Stage E correctness review (LABS-1.034): which existing answers in the reference worlds each correction would
change. Read-only analysis on main as merged; nothing is corrected. Usage:
    uv run python -I probes/pre_e_review_impact.py <repo>

Builds the gearbox (all its extensions), Acme and laboratory worlds in one throwaway database (wm-probe-pre-e-impact,
deleted afterwards), then, for every world (actual and variant), every subject its attestations mention, and every
time at which an attestation starts or ends (and just before), reads the per-content judgement (`_claims`) and counts:
- DI-1: contents judged "disputed" by polarity (facts_about leaves them out; holds() reports DISPUTED);
- DI-5: contents with an accepted attestation that are undecided at t, by label: an attestation state ranked first
  (the registered case), or "not yet effective" although the accepted attestation has begun (end unknown);
- DI-2: occurrences whose accepted descriptions name different players in one role;
- DI-6: capable() answers whose applicable accepted holdings have different statuses, and office_holders() answers
  whose established holders have different statuses.
"""

import json
import sys
import time
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, organisation as org  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import gearbox as g, laboratory as lab_ex, organisation as org_ex  # noqa: E402
from worldmodel.model import READ  # noqa: E402

DB = "wm-probe-pre-e-impact"
t0 = time.perf_counter()
wm = WorldModel.create(DB, modules=CORE_MODULES, replace=True)
report = {}
try:
    for p in ("mechanical", "organisation", "laboratory"):
        wm.install_profile(p)
    gids = g.build(wm)
    g.extend_mechanical(wm, g.extend_qualities_agency(wm, g.extend_causality(wm, g.extend_dynamics(
        wm, g.extend_spatial(wm, gids)))))
    org_ex.build_organisation(wm)
    lab_ex.build_laboratory(wm)
    with wm.driver.transaction(wm.database, READ) as tx:
        worlds = sorted({q.opt(r, "id") for r in q.rows(tx, "match $w isa world, has wm-id $id;")})
    built = time.perf_counter() - t0

    di1, di5, di2, di6c, di6o = set(), defaultdict(set), {}, set(), set()
    calls = 0
    for w in worlds:
        atts = wm.visible(w)
        subjects = sorted({x for a in atts.values() for ids in a.roles.values() for x in ids})
        times = set()
        for a in atts.values():
            for win in (a.start, a.end):
                if win is not None and win.latest is not None:
                    times |= {win.latest, win.latest - timedelta(seconds=1)}
        times = sorted(times)
        for x in subjects:
            for t in times:
                calls += 1
                for e in wm._claims(w, x, ("proposition",), t, None, "system"):
                    key = (w, e["type"], json.dumps(e["roles"], sort_keys=True))
                    if e["judged"] == "disputed":
                        di1.add(key)
                    accepted = [s for s in e["attestations"] if s["acceptance"] == "accepted"]
                    if e["judged"] is None and accepted:
                        label = wm._verdict_label(e)
                        recs = [a for a in atts.values() if a.id in {s["attestation"] for s in accepted}]
                        begun = any(a.start is None or a.start.latest <= t for a in recs)
                        di5["state ranked before not-yet-effective" if label != "not yet effective" and not begun
                            else "not yet effective although begun" if label == "not yet effective" and begun
                            else "other: " + label].add(key)
        # DI-2: occurrences with several accepted descriptions naming different players in one role
        occs = sorted({x for a in atts.values() if a.kind == "describes" for x in a.roles.get("occurrence", [])})
        for o in occs:
            v = wm.occurrence(w, o)
            split = {r: sorted(m) for r, m in v["participants"].items() if len(m) > 1 and len(v["descriptions"]) > 1}
            if split:
                di2[(w, o)] = split
        # DI-6: capable() and office_holders() folding different statuses
        for a in atts.values():
            if a.kind == "classified-as" or wm.is_a(a.ctype, "classified-as"):
                holder, concept = a.roles.get("classified", [None])[0], a.roles.get("class", [None])[0]
                ctxs = {None} | {b.roles.get("context", [None])[0] for b in atts.values()
                                 if b.roles.get("classified") == [holder] and b.roles.get("class") == [concept]}
                for t in times[::max(1, len(times) // 8)]:
                    for c in ctxs:
                        r = wm.capable(w, holder, concept, t, context=c)
                        st = {h["status"] for h in r["applicable"] if h["judgement"] == "accepted"}
                        if len(st) > 1:
                            di6c.add((w, holder, concept, c, str(t), r["status"].name,
                                      tuple(sorted(s.name for s in st))))
        if "organisation" in wm.profiles():
            offices = {(a.roles["class"][0], a.roles["context"][0]) for a in atts.values()
                       if wm.is_a(a.ctype, "office-holding")}
            for office, ctx in offices:
                for t in times[::max(1, len(times) // 8)]:
                    r = org.office_holders(wm, w, office, ctx, t)
                    st = {x["status"] for x in r["appointments"] if x["judgement"] == "established"}
                    if len(st) > 1:
                        di6o.add((w, office, ctx, str(t), r["status"].name, tuple(sorted(s.name for s in st))))

    report = {
        "worlds": worlds, "content_reads": calls,
        "DI-1 polarity-disputed contents omitted by facts_about": sorted(map(list, di1)),
        "DI-5 undecided accepted contents, by label": {k: sorted(map(list, v)) for k, v in di5.items()},
        "DI-2 occurrences with differing players": {f"{w} {o}": v for (w, o), v in sorted(di2.items())},
        "DI-6 capable() with mixed statuses": sorted(map(list, di6c)),
        "DI-6 office_holders() with mixed statuses": sorted(map(list, di6o)),
        "seconds": {"build": round(built, 1), "total": round(time.perf_counter() - t0, 1)},
    }
    print(json.dumps(report, indent=1, default=str))
    print("\nsummary:", json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in report.items()
                                    if k.startswith("DI")}), file=sys.stderr)
finally:
    wm.driver.databases.get(DB).delete()
