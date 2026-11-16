"""Increment B (LABS-1.038): a frozen snapshot of every reader the canonical judgement touches, on the reference worlds.

    uv run python -I probes/pre_e_b_snapshot.py <checkout> --build          # build the data once (kept database)
    uv run python -I probes/pre_e_b_snapshot.py <checkout> --out FILE        # read it with <checkout>'s code
    uv run python -I probes/pre_e_b_snapshot.py <checkout> --drop            # delete the kept database

The data are the review's reference worlds (gearbox with its spatial, dynamics, causality, qualities-agency and
mechanical extensions; Acme; the laboratory), built once into `wm-probe-pre-e-b` so that the code before and after
increment B reads exactly the same database. The reading pass calls every public reader whose answer comes from
content judgement, for every world (actual and variant), for every subject the world's attestations mention, chosen
by the subject's kind, at `--times` valid times spread over the world's attestation boundaries, for the system
perspective and, for facts_about, holds and capable, also for each attester's perspective and an earlier knowledge
time. Every answer is normalised to JSON (errors included, as text). Compare two snapshots with pre_e_b_diff.py.
"""

import argparse
import dataclasses
import enum
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--build", action="store_true")
ap.add_argument("--drop", action="store_true")
ap.add_argument("--out")
ap.add_argument("--times", type=int, default=5)
ap.add_argument("--db", default="wm-probe-pre-e-b")
ap.add_argument("--worlds", help="comma-separated world ids (default: every world); merge parts with --merge")
ap.add_argument("--merge", nargs="*", help="merge snapshot parts into --out")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, connect  # noqa: E402
from worldmodel import laboratory as lab, mechanical as mech, organisation as org  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.model import READ  # noqa: E402

if a.merge:
    parts = [json.loads(Path(f).read_text()) for f in a.merge]
    merged = {"database": parts[0]["database"], "worlds": sorted(w for p in parts for w in p["worlds"]),
              "times": parts[0]["times"], "calls": sum(p["calls"] for p in parts),
              "seconds": round(sum(p["seconds"] for p in parts), 1),
              "answers": {k: v for p in parts for k, v in p["answers"].items()}}
    Path(a.out).write_text(json.dumps(merged, indent=0, sort_keys=True))
    print(f"merged {len(parts)} parts: {merged['calls']} answers -> {a.out}", file=sys.stderr)
    sys.exit(0)
driver = connect()
if a.drop:
    if driver.databases.contains(a.db):
        driver.databases.get(a.db).delete()
    sys.exit(0)
if a.build:
    from worldmodel.examples import gearbox as g, laboratory as lab_ex, organisation as org_ex
    wm = WorldModel.create(a.db, driver=driver, modules=CORE_MODULES, replace=True)
    for p in ("mechanical", "organisation", "laboratory"):
        wm.install_profile(p)
    gids = g.build(wm)
    g.extend_mechanical(wm, g.extend_qualities_agency(wm, g.extend_causality(wm, g.extend_dynamics(
        wm, g.extend_spatial(wm, gids)))))
    org_ex.build_organisation(wm)
    lab_ex.build_laboratory(wm)
    print(f"built {a.db}")
    sys.exit(0)


def norm(x):
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return {f.name: norm(getattr(x, f.name)) for f in dataclasses.fields(x)}
    if isinstance(x, enum.Enum):
        return x.name
    if isinstance(x, (datetime, date)):
        return x.isoformat()
    if isinstance(x, dict):
        return {str(k): norm(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted((norm(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    if hasattr(x, "__dict__"):
        return {k: norm(v) for k, v in sorted(vars(x).items()) if not k.startswith("_")}
    return repr(x)


import os
wm = WorldModel(driver, a.db, selective=os.environ.get("WM_SELECTIVE", "1") != "0")
out, calls, t0 = {}, 0, time.perf_counter()


cost = {}


def call(key, fn, *args, **kw):
    global calls
    calls += 1
    t1 = time.perf_counter()
    try:
        out[key] = norm(fn(*args, **kw))
    except Exception as e:                       # an error is an answer too: it must not change unnoticed
        out[key] = {"error": f"{type(e).__name__}: {e}"}
    c = cost.setdefault(key[2] if len(key) > 2 else key[1], [0, 0.0])
    c[0] += 1
    c[1] += time.perf_counter() - t1


with wm._reading() as tx:
    worlds = sorted({q.opt(r, "id") for r in q.rows(tx, "match $w isa world, has wm-id $id;")})
if a.worlds:
    worlds = [w for w in worlds if w in a.worlds.split(",")]
profiles = wm.profiles()
for w in worlds:
    atts = wm.visible(w)
    ids = sorted({x for at in atts.values() for v in at.roles.values() for x in v})
    with wm._reading() as tx:
        kinds = wm._kinds_of(tx, ids)
    bounds = sorted({x for at in atts.values() for win in (at.start, at.end) if win is not None
                     for x in (win.earliest, win.latest) if x is not None})
    near = sorted({b for x in bounds for b in (x, x - timedelta(seconds=1))})
    times = sorted({near[round(i * (len(near) - 1) / max(1, a.times - 1))] for i in range(a.times)}) if near else []
    attesters = sorted({at.attester for at in atts.values()} - {"system"})
    knowledge = sorted({at.recorded_at for at in atts.values() if at.recorded_at is not None})
    early = knowledge[len(knowledge) // 2] if knowledge else None

    def kind(x, *labels):
        k = kinds.get(x)
        return bool(k) and any(wm.is_a(k, lab_) for lab_ in labels)

    contents = {}
    for at in atts.values():
        if at.kind in ("event", "same-as"):
            continue
        contents.setdefault(json.dumps([at.ctype, {r: sorted(v) for r, v in at.roles.items()}], sort_keys=True),
                            (at.ctype, {r: list(v) for r, v in at.roles.items()}))
    descriptions = sorted({at.content for at in atts.values() if at.kind == "event"})
    holdings = sorted({(at.roles["classified"][0], at.roles["class"][0], (at.roles.get("context") or [None])[0])
                       for at in atts.values() if wm.is_a(at.ctype, "classified-as")
                       and at.roles.get("classified") and at.roles.get("class")}, key=str)
    qualities = sorted({(at.roles["bearer"][0], at.roles["quality"][0]) for at in atts.values()
                        if wm.is_a(at.ctype, "has-quality") and at.roles.get("bearer") and at.roles.get("quality")})
    frames = [x for x in ids if kind(x, "spatial-frame")]
    for t in times:
        T = t.isoformat()
        for x in ids:
            call((w, T, "facts_about", x), wm.facts_about, w, x, t)
            call((w, T, "exists", x), wm.exists, w, x, t)
            call((w, T, "parts", x), wm.parts, w, x, t)
            call((w, T, "dependencies", x), wm.dependencies, w, x, t)
            call((w, T, "direct_dependencies", x), wm.direct_dependencies, w, x, t)
            call((w, T, "composition", x), wm.composition, w, x, t)
            call((w, T, "materials", x), wm.materials, w, x, t)
            call((w, T, "roles_of", x), wm.roles_of, w, x, t)
            call((w, T, "poses", x), wm.poses, w, x, t)
            if kind(x, "place"):
                call((w, T, "contents", x), wm.contents, w, x, t)
            if kind(x, "spatial-frame"):
                call((w, T, "frame_info", x), wm.frame_info, w, x, t)
            if kind(x, "occurrence"):
                call((w, T, "occurrence_status", x), wm.occurrence_status, w, x, t)
                call((w, T, "causes_of", x), wm.causes_of, w, x, t)
                call((w, T, "process_steps", x), wm.process_steps, w, x, t)
            if "mechanical" in profiles:
                call((w, T, "connections", x), mech.connections, wm, w, x, t)
            if "organisation" in profiles:
                call((w, T, "employment", x), org.employment, wm, w, x, t)
                call((w, T, "offices_of", x), org.offices_of, wm, w, x, t)
            if "laboratory" in profiles:
                if kind(x, "sample"):
                    call((w, T, "provenance", x), lab.provenance, wm, w, x, t)
                if kind(x, "information-object"):
                    call((w, T, "interpretations", x), lab.interpretations, wm, w, x, t)
                call((w, T, "calibration_status", x), lab.calibration_status, wm, w, x, t)
        for d in descriptions:
            call((w, T, "effects_of", d), wm.effects_of, w, d, t)
            call((w, T, "causes_of", d), wm.causes_of, w, d, t)
            if "mechanical" in profiles:
                call((w, T, "replacement", d), mech.replacement, wm, w, d, t)
        for k, (ty, roles) in sorted(contents.items()):
            call((w, T, "holds", k), wm.holds, w, ty, roles, t)
            if wm._constraints(ty):
                try:
                    keyrole = sorted({ks for _, ks, _ in wm._constraints(ty)})[0]
                    call((w, T, "value_of", k, str(keyrole)), wm.value_of, w, ty,
                         {r: roles[r][0] for r in keyrole if roles.get(r)}, t)
                except Exception as e:
                    out[(w, T, "value_of", k)] = {"error": f"{type(e).__name__}: {e}"}
            if wm.is_a(ty, "initiates") or wm.is_a(ty, "terminates"):
                pass
        for holder, concept, ctx in holdings:
            for c in sorted({None, ctx}, key=str):
                call((w, T, "capable", holder, concept, str(c)), wm.capable, w, holder, concept, t, context=c)
        for bearer, quality in qualities:
            call((w, T, "measurements", bearer, quality), wm.measurements, w, bearer, quality, t)
            call((w, T, "compare_measurements", bearer, quality), wm.compare_measurements, w, bearer, quality, t)
            if "laboratory" in profiles:
                call((w, T, "measurement_calibration", bearer, quality), lab.measurement_calibration, wm, w, bearer,
                     quality, t)
        for i, f1 in enumerate(frames):
            for f2 in frames[i + 1:]:
                call((w, T, "transform_between", f1, f2), wm.transform_between, w, f1, f2, t)
        if "organisation" in profiles:
            offices = sorted({(at.roles["class"][0], at.roles["context"][0]) for at in atts.values()
                              if wm.is_a(at.ctype, "office-holding")})
            for office, ctx in offices:
                call((w, T, "office_holders", office, ctx), org.office_holders, wm, w, office, ctx, t)
            grants = sorted({(at.roles["holder"][0], at.roles["power"][0], at.roles["scope"][0]) for at in atts.values()
                             if wm.is_a(at.ctype, "authorisation")})
            for holder, power, scope in grants:
                call((w, T, "authorised", holder, power, scope), org.authorised, wm, w, holder, power, scope, t)
        # other perspectives and an earlier knowledge time, for the core readers
        for p in attesters:
            for x in ids:
                call((w, T, "facts_about@" + p, x), wm.facts_about, w, x, t, perspective=p)
            for holder, concept, ctx in holdings:
                call((w, T, "capable@" + p, holder, concept, str(ctx)), wm.capable, w, holder, concept, t, context=ctx,
                     perspective=p)
        if early is not None:
            for x in ids:
                call((w, T, "facts_about@as_of", x), wm.facts_about, w, x, t, as_of=early)
            for k, (ty, roles) in sorted(contents.items()):
                call((w, T, "holds@as_of", k), wm.holds, w, ty, roles, t, as_of=early)
    for x in ids:
        if times:
            call((w, "changes", x), wm.changes, w, x, times[0], times[-1])
    for d in descriptions:
        if kind(d, "official-act") and "organisation" in profiles:
            call((w, "official_act", d), org.official_act, wm, w, d)
        call((w, "check_action", d), wm.check_action, w, d)
    call((w, "agency_report"), wm.agency_report, w)
    print(f"{w}: {calls} calls, {time.perf_counter() - t0:.0f} s", file=sys.stderr, flush=True)
    print("  slowest:", sorted(((round(v[1]), v[0], k) for k, v in cost.items()), reverse=True)[:8], file=sys.stderr,
          flush=True)

result = {"database": a.db, "worlds": worlds, "times": a.times, "calls": calls,
          "seconds": round(time.perf_counter() - t0, 1), "answers": {json.dumps(k): v for k, v in sorted(out.items(), key=str)}}
Path(a.out).write_text(json.dumps(result, indent=0, sort_keys=True))
print(f"{calls} answers in {result['seconds']} s -> {a.out}", file=sys.stderr)
