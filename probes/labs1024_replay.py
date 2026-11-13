"""LABS-1.024 design probe 3: attribution by replay, and server metadata. Usage: python -I this.py <repo>"""
import hashlib, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel  # noqa
from worldmodel.profiles import PROFILES  # noqa

def decls(text):
    """(subject, declaration) pairs of a schema() text: one per line inside each type statement, plus functions."""
    body, out = text.split("\nfun ", 1)[0], set()
    for st in body.replace("define", "", 1).split(";"):
        lines = [l.strip().rstrip(",") for l in st.strip().splitlines() if l.strip()]
        if not lines:
            continue
        head = lines[0].split()
        subject = head[1]
        out.add((subject, " ".join(head[0:1] + head[2:])))          # kind (+ type annotations)
        out |= {(subject, l) for l in lines[1:]}
    out |= {("fun", m) for m in re.findall(r"^fun\s+([a-z_]+)", text, re.M)}
    return out

drv = None
names = []
try:
    t0 = time.perf_counter()
    target = WorldModel.create("wm-probe-target", modules=CORE_MODULES, replace=True); names.append("wm-probe-target")
    drv = target.driver
    for p in ("laboratory", "mechanical", "organisation"):     # a different order from the replay
        target.install_profile(p)
    full = drv.databases.get("wm-probe-target").schema()
    for attr in ("server_version", "version"):
        print(f"driver.{attr}:", getattr(drv, attr, "absent") if not callable(getattr(drv, attr, None)) else getattr(drv, attr)())
    core = WorldModel.create("wm-probe-core", modules=CORE_MODULES, driver=drv, replace=True); names.append("wm-probe-core")
    core_d = decls(drv.databases.get("wm-probe-core").schema())
    by_profile = {}
    for p in ("mechanical", "organisation", "laboratory"):
        n = f"wm-probe-{p}"; names.append(n)
        wm = WorldModel.create(n, modules=CORE_MODULES, driver=drv, replace=True); wm.install_profile(p)
        by_profile[p] = decls(drv.databases.get(n).schema()) - core_d
    full_d = decls(full)
    union = core_d.union(*by_profile.values())
    print("declarations: target", len(full_d), "| core", len(core_d), "| per profile",
          {k: len(v) for k, v in by_profile.items()})
    print("target == core + profiles (as declaration sets):", full_d == union,
          "| missing:", sorted(union - full_d)[:5], "| extra:", sorted(full_d - union)[:5])
    clash = [(a, b, sorted(by_profile[a] & by_profile[b])) for a, b in (("mechanical", "organisation"), ("mechanical", "laboratory"), ("organisation", "laboratory"))]
    print("declared by two profiles:", [c for c in clash if c[2]])
    print("laboratory's declarations on core types:", sorted(d for d in by_profile["laboratory"] if d[0] in {x for x, _ in core_d}))
    print("schema sha256:", hashlib.sha256(full.encode()).hexdigest()[:16], "| total probe time %.1f s" % (time.perf_counter() - t0))
finally:
    if drv:
        for n in names:
            if drv.databases.contains(n):
                drv.databases.get(n).delete()
