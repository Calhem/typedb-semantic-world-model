"""LABS-1.017 probe for D-C-2, rerun under LABS-1.018 with rests-on(attestation, record): which result record supports
which reported-content attestation, when one source records two results at the same time? Throwaway databases
(wm-dc2-*), deleted afterwards. The LABS-1.017 (heuristic) output is kept in core04_c_dc2_identity.before.json.

    uv run python -I probes/core04_c_dc2_identity.py > probes/core04_c_dc2_identity.out.json
"""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import QUALITY_MODULES, WorldModel  # noqa: E402
from worldmodel.examples import lab  # noqa: E402

T = lab.T


def fresh():
    wm = WorldModel.create(f"wm-dc2-{uuid.uuid4().hex[:8]}", modules=QUALITY_MODULES)
    w = wm.create_world("lab", id="lab")
    for i in ("sample", "ana", "b3", "b7"):
        wm.add_entity("physical-object", i, id=i)
    wm.add_entity("category", "measurement", id="measurement")
    wm.define_unit("kilogram", "mass", id="u-kg")
    wm.define_quality_kind("mass", "mass", id="q-mass")
    return wm, w


def view(wm, w, ids):
    names = {v["result"]: k for k, v in ids.items()}
    out = {}
    for m in wm.measurements(w, "sample", "q-mass"):
        label = next((k for k, v in ids.items() if v["content"] == m["attestation"]), m["attestation"])
        out[label] = [{"record_of": names.get(r["record"], r["record"]), "conditions": r["conditions"]}
                      for r in m["records"]]
    return out


out, dbs = {}, []
try:
    # 1. identical values, same source, same time, two balances (two results, one content)
    wm, w = fresh(); dbs.append(wm)
    ids = {b: wm.measure(w, "sample", "q-mass", 3.51, "u-kg", 0.02, start=T(9), end=T(9, 5), instrument=b,
                         operator="ana", attester="ana", conditions=["T=20C"]) for b in ("b3", "b7")}
    out["1 identical values, same source and time: records each attestation is tied to"] = view(wm, w, ids)
    # 2. identical values, same source and time, different conditions
    wm, w = fresh(); dbs.append(wm)
    ids = {c: wm.measure(w, "sample", "q-mass", 3.51, "u-kg", 0.02, start=T(9), end=T(9, 5), instrument="b3",
                         operator="ana", attester="ana", conditions=[c]) for c in ("T=20C", "T=35C")}
    out["2 identical values, same source and time, different conditions"] = view(wm, w, ids)
    c = wm.compare_measurements(w, "sample", "q-mass")
    out["2b comparison of those two"] = [(p["relation"], p["reason"]) for p in c["pairs"]]
    # 3. different values, same source and time (distinct contents)
    wm, w = fresh(); dbs.append(wm)
    ids = {f"{v}": wm.measure(w, "sample", "q-mass", v, "u-kg", 0.02, start=T(9), end=T(9, 5), instrument="b3",
                              operator="ana", attester="ana") for v in (3.51, 3.60)}
    out["3 different values, same source and time"] = view(wm, w, ids)
finally:
    for m in dbs:
        m.driver.databases.get(m.database).delete()
print(json.dumps(out, indent=1, default=str))
