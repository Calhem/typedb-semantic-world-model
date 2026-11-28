"""LABS-1.063: reproduce the material potential defects found by the E2 reader-contract review, each on a minimal,
isolated diagnostic fixture. Read-only on the library: it loads each fixture into its own throwaway database (through
the harness loader's public writers), calls the reader, and records what it returned.

    uv run python -m probes.e2_contract_diagnostics [--json OUT.json]

**Diagnostic only.**
- These fixtures are not E2 evaluation fixtures, and nothing observed here may become an E2 gold answer.
- The "expected" side of each case is the approved contract (benchmark/e2/spec/reader-contracts.md and its design
  sources), written before the run.
- A case is **reproduced** when the observed behaviour shows the discrepancy the review described; **not reproduced**
  when the reader behaves as the contract says.
"""

import argparse
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from evaluation.loader import T, drop, load  # noqa: E402
from evaluation.e2.values import normalise  # noqa: E402
from worldmodel import laboratory as lab, organisation as org  # noqa: E402

FRAMES = [{"op": "entity", "kind": "spatial-frame", "id": f} for f in ("A", "C")]
OBJ = lambda *ids: [{"op": "entity", "kind": "physical-object", "id": i} for i in ids]
W = ([{"op": "entity", "kind": "physical-object", "id": a} for a in ("inspector", "auditor", "gossip")] +
     [{"op": "world", "id": "w", "kind": "actual"}])
POS = {"x-min": 1.0, "x-max": 1.0, "y-min": 0.0, "y-max": 0.0, "z-min": 0.0, "z-max": 0.0}
MASS = [{"op": "entity", "kind": "category", "id": "measurement"}, {"op": "define_unit", "id": "kg", "dimension": "mass"},
        {"op": "define_quality_kind", "id": "mass", "dimension": "mass"}]
CASES = []


def case(cid, items, expected):
    def deco(fn):
        CASES.append({"id": cid, "items": items, "expected": expected, "fn": fn})
        return fn
    return deco


def fx(name, steps, profiles=("organisation",)):
    return {"id": f"diag-{name}", "profiles": list(profiles), "steps": steps}


# ---- spatial -------------------------------------------------------------------------------------------------------
@case("DX-1", ["D-WH-3"], "A2 Provenance / v0.2 §5.2 E6: a derived pose rests on its position statement as a premise; "
      "a premise disputed by an accepted denial cannot yield an INFERRED (undisputed) candidate or answer")
def dx1(L):
    out = normalise(L.wm.where("w", "box", "A", T("T3")))
    poses = normalise(L.wm.poses("w", "box", T("T3")))
    return ({"poses_status": [p["status"] for p in poses], "where_status": out["status"],
             "candidate_status": [c["status"] for c in out["candidates"]]},
            out["status"] == "INFERRED" or "INFERRED" in [c["status"] for c in out["candidates"]])


dx1.fixture = fx("wh3", FRAMES + OBJ("box") + W + [
    {"op": "relate_frames", "id": "ac", "world": "w", "parent": "A", "child": "C", "translation": [1.0, 0.0, 0.0],
     "start": "T1", "until_superseded": True},
    {"op": "position", "id": "pos", "world": "w", "thing": "box", "frame": "C", "x": 1.0, "y": 0.0, "z": 0.0,
     "start": "T2", "until_superseded": True},
    {"op": "deny", "id": "pos-denied", "world": "w", "type": "positioned-in",
     "roles": {"positioned": "box", "frame": "C"}, "params": POS, "start": "T2", "until_superseded": True,
     "attester": "inspector", "accepted_by": ["system"]}])


@case("DX-2", ["D-WH-5", "D-PO-3"], "ID-8 (pre-e-identity-design §9): a reader judges the subject with its "
      "established same-as group, so a position stated under an alias is a candidate for the canonical thing")
def dx2(L):
    w = normalise(L.wm.where("w", "box", "C", T("T3")))
    p = normalise(L.wm.poses("w", "box", T("T3")))
    w_alias = normalise(L.wm.where("w", "box-alias", "C", T("T3")))
    p_alias = normalise(L.wm.poses("w", "box-alias", T("T3")))
    ident = L.wm.identity("w")
    return ({"canonical": ident.canonical("box"), "same group": ident.canonical("box") == ident.canonical("box-alias"),
             "where(box).candidates": len(w["candidates"]), "poses(box)": len(p),
             "where(box-alias).candidates": len(w_alias["candidates"]), "poses(box-alias)": len(p_alias)},
            0 in (len(w["candidates"]), len(p), len(w_alias["candidates"]), len(p_alias)))


dx2.fixture = fx("alias-pos", [{"op": "entity", "kind": "spatial-frame", "id": "C"}] + OBJ("box", "box-alias") + W + [
    {"op": "attest", "id": "same", "world": "w", "type": "same-as", "roles": {"same": ["box", "box-alias"]},
     "until_superseded": True},
    {"op": "position", "id": "pos", "world": "w", "thing": "box-alias", "frame": "C", "x": 1.0, "y": 0.0, "z": 0.0,
     "start": "T2", "until_superseded": True}])


# ---- measurement -----------------------------------------------------------------------------------------------------
@case("DX-3", ["D-ME-5"], "v0.2 §4.2 and the identity increment: measurements of an alias are measurements of the "
      "same bearer")
def dx3(L):
    m = normalise(L.wm.measurements("w", "box", "mass"))
    m_alias = normalise(L.wm.measurements("w", "box-alias", "mass"))
    return ({"canonical": L.wm.identity("w").canonical("box"), "measurements(box)": len(m),
             "measurements(box-alias)": len(m_alias)}, 0 in (len(m), len(m_alias)))


dx3.fixture = fx("alias-meas", OBJ("box", "box-alias") + MASS + W + [
    {"op": "attest", "id": "same", "world": "w", "type": "same-as", "roles": {"same": ["box", "box-alias"]},
     "until_superseded": True},
    {"op": "measure", "id": "m1", "world": "w", "bearer": "box-alias", "quality": "mass", "value": 1.5, "unit": "kg",
     "uncertainty": 0.01, "start": "T3", "end": "T3h10"}])


def _deny_measured(L, attester="auditor"):
    """Deny exactly the content m1 reported (its stored key is read back, then denied through the public writer)."""
    a = [m for m in L.wm.measurements("w", "box", "mass") if m["attestation"] in L.written["m1"]][0]
    lo, hi = a["range"]
    params = {"lower": lo, "upper": hi, "coverage-level": a["coverage_level"]}
    den = L.wm.deny("w", "has-quality", {"bearer": "box", "quality": "mass", "unit": "kg"}, params=params,
                    start=T("T3"), until_superseded=True, attester=attester)
    L.wm.accept(den, holder="system")
    return a["content"], den


@case("DX-4", ["D-CM-6"], "v0.2 §5.3 and stage-c 'Disputes': an accepted denial of a measured content disputes it; "
      "compare_measurements is DISPUTED, with or without t")
def dx4(L):
    content, den = _deny_measured(L)
    same = L.wm._attestation(den)["content"] == content          # diagnostic check only (private accessor)
    c_all = normalise(L.wm.compare_measurements("w", "box", "mass"))
    c_t = normalise(L.wm.compare_measurements("w", "box", "mass", T("T3h05")))
    return ({"compare.status": c_all["status"], "compare(t).status": c_t["status"],
             "denial listed as alternative": den in [m["attestation"] for m in c_all["alternatives"]],
             "denial visible with t": den in json.dumps(c_t), "measurements": len(c_all["measurements"]),
             "denied content == measured content": bool(same)},
            c_all["status"] != "DISPUTED" or c_t["status"] != "DISPUTED")


dx4.fixture = fx("meas-denial", OBJ("box") + MASS + W + [
    {"op": "measure", "id": "m1", "world": "w", "bearer": "box", "quality": "mass", "value": 1.5, "unit": "kg",
     "uncertainty": 0.01, "start": "T3", "end": "T3h10"},
    {"op": "measure", "id": "m2", "world": "w", "bearer": "box", "quality": "mass", "value": 1.5, "unit": "kg",
     "uncertainty": 0.01, "start": "T3", "end": "T3h10"}])


@case("DX-5", ["D-ME-6"], "plan §9.2 / stage-c: a measurement over an instant (no end, no persists) holds at that "
      "instant, and two measurements at the same instant are comparable")
def dx5(L):
    at = normalise(L.wm.measurements("w", "box", "mass", T("T3")))
    allm = normalise(L.wm.measurements("w", "box", "mass"))
    c = normalise(L.wm.compare_measurements("w", "box", "mass"))
    return ({"measurements(t=T3)": len(at), "measurements(no t)": len(allm),
             "valid": [m["valid"] for m in allm][:1], "pairs": [(p["relation"], p["reason"]) for p in c["pairs"]]},
            len(at) == 0 or any(p["relation"] == "incomparable" for p in c["pairs"]))


dx5.fixture = fx("point-meas", OBJ("box") + MASS + W + [
    {"op": "measure", "id": "m1", "world": "w", "bearer": "box", "quality": "mass", "value": 1.5, "unit": "kg",
     "uncertainty": 0.01, "start": "T3"},
    {"op": "measure", "id": "m2", "world": "w", "bearer": "box", "quality": "mass", "value": 1.51, "unit": "kg",
     "uncertainty": 0.01, "start": "T3"}])


# ---- organisation: exclusive office ------------------------------------------------------------------------------------
OFFICE = ([{"op": "entity", "kind": "person", "id": p} for p in ("bea", "cal")] +
          [{"op": "entity", "kind": "organisation", "id": "acme"}, {"op": "entity", "kind": "social-role", "id": "sm"},
           {"op": "entity", "kind": "place", "id": "depot-7"}] + W +
          [{"op": "appoint", "id": "a-bea", "world": "w", "holder": "bea", "office": "sm", "context": "depot-7",
            "start": "T1", "until_superseded": True},
           {"op": "appoint", "id": "a-cal", "world": "w", "holder": "cal", "office": "sm", "context": "depot-7",
            "start": "T1", "until_superseded": True},
           {"op": "declare_exclusive", "id": "x-sm", "world": "w", "office": "sm", "context": "depot-7",
            "start": "T1", "until_superseded": True}])


@case("DX-6", ["D-VA-3"], "DI-19 report §1 and A0: value readers apply declared slots only and refuse a type with no "
      "declared slot; they never report an exclusive office's holders as undisputed")
def dx6(L):
    try:
        v = normalise(L.wm.value_at("w", "office-holding", "sm", T("T3"), key_role="class", value_role="classified"))
        obs = {"value_at.status": v["status"], "values": v["values"]}
    except ValueError as e:
        return {"value_at": f"refused: {e}"[:200]}, False
    oh = org.office_holders(L.wm, "w", "sm", "depot-7", T("T3"))
    obs["office_holders.conflict"] = oh["conflict"] is not None
    return obs, v["status"] != "DISPUTED"


dx6.fixture = fx("office", OFFICE, ["organisation"])


@case("DX-7", ["D-FA-1"], "DI-19 / increment B §4: a listing of a content disputed under an attested constraint cites "
      "the constraint's deciding attestation, as holds() does")
def dx7(L):
    f = [e for e in normalise(L.wm.facts_about("w", "bea", T("T3"))) if "office-holding" in e["type"]]
    h = normalise(L.wm.holds("w", "office-holding", {"classified": "bea", "class": "sm", "context": "depot-7"},
                             T("T3")))
    cites = "x-sm" in json.dumps(f)
    return ({"facts_about.status": [e["status"] for e in f], "facts_about cites x-sm": cites,
             "holds.constraint_support": [c["support"] for c in h["constraint_support"]]}, not cites)


dx7.fixture = fx("office-fa", OFFICE, ["organisation"])


# ---- causation -----------------------------------------------------------------------------------------------------
EV = ([{"op": "entity", "kind": "occurrence", "id": o} for o in ("o-a", "o-b")] +
      [{"op": "entity", "kind": "person", "id": "tech"}] + W)


@case("DX-8", ["D-CO-1"], "plan §9.3: a claim stated about another description is lifted only through accepted "
      "describes links for both descriptions; a cause description with no accepted link does not apply as a cause of "
      "the occurrence")
def dx8(L):
    c = normalise(L.wm.causes_of("w", "o-b", T("T9")))
    lifted = [x for x in c if x["lifted"]]
    return ({"claims": [(x["cause"], x["effect"], x["lifted"], x["applies"], x["cause_occurrences"]) for x in c]},
            any(x["applies"] is True and not x["cause_occurrences"] for x in lifted))


dx8.fixture = fx("lift-one-side", EV + [
    {"op": "account", "id": "ev-a", "world": "w", "roles": {"actor": "tech"}, "start": "T2"},
    {"op": "account", "id": "ev-b", "world": "w", "roles": {"actor": "tech"}, "start": "T3", "occurrence": "o-b"},
    {"op": "claim_cause", "id": "a-causes-b", "world": "w", "cause": "ev-a", "effect": "ev-b"}])


@case("DX-9", ["D-CO-2"], "plan §9.3 / stage-b 'Lifting': a lifted claim cites the describes links it was lifted "
      "through")
def dx9(L):
    c = normalise(L.wm.causes_of("w", "o-b", T("T9")))
    lifted = [x for x in c if x["lifted"]]
    link = L.written["ev-b"]
    cited = any(a in json.dumps(lifted) for a in link if a not in json.dumps([x["attestations"] for x in lifted]))
    return ({"lifted_via": [x["lifted_via"] for x in lifted], "describes ids of ev-b": len(link)},
            bool(lifted) and all(set(x["lifted_via"] or {}) <= {"description", "occurrence"} for x in lifted))


dx9.fixture = fx("lift-cite", EV + [
    {"op": "account", "id": "ev-a", "world": "w", "roles": {"actor": "tech"}, "start": "T2", "occurrence": "o-a"},
    {"op": "account", "id": "ev-b", "world": "w", "roles": {"actor": "tech"}, "start": "T3", "occurrence": "o-b"},
    {"op": "claim_cause", "id": "a-causes-b", "world": "w", "cause": "ev-a", "effect": "ev-b"}])


@case("DX-10", ["D-CO-3"], "stage-b U-2: lifting uses an accepted describes link; a link disputed by an accepted "
      "denial does not lift")
def dx10(L):
    c = normalise(L.wm.causes_of("w", "o-b", T("T9")))
    return ({"claims": [(x["cause"], x["effect"], x["lifted"], x["applies"]) for x in c]},
            any(x["lifted"] for x in c))


dx10.fixture = fx("lift-disputed", EV + [
    {"op": "account", "id": "ev-a", "world": "w", "roles": {"actor": "tech"}, "start": "T2", "occurrence": "o-a"},
    {"op": "account", "id": "ev-b", "world": "w", "roles": {"actor": "tech"}, "start": "T3"},
    {"op": "describe_occurrence", "id": "link", "world": "w", "description": "ev-b", "occurrence": "o-b"},
    {"op": "describe_occurrence", "id": "link-denied", "world": "w", "description": "ev-b", "occurrence": "o-b",
     "polarity": False, "attester": "auditor", "accepted_by": ["system"]},
    {"op": "claim_cause", "id": "a-causes-b", "world": "w", "cause": "ev-a", "effect": "ev-b"}])


PLACE = [{"op": "entity", "kind": "place", "id": p} for p in ("shelf", "dock")]


@case("DX-11", ["D-EX-1", "D-EX-4"], "stage-b 'Schema and API': explain lists the content's accepted initiating "
      "events; B0: every claim lists its attestations")
def dx11(L):
    e = normalise(L.wm.explain("w", "located-at", {"located": "box", "place": "shelf"}, T("T9")))
    inits = e["initiated_by"]
    return ({"initiated_by": [(i["event"], i["claim"]) for i in inits],
             "fields": sorted(inits[0]) if inits else []},
            any(i["claim"] != "accepted" for i in inits) or any("attestations" not in i for i in inits))


dx11.fixture = fx("explain-init", OBJ("box") + PLACE + EV + [
    {"op": "attest", "id": "on-shelf", "world": "w", "type": "located-at", "roles": {"located": "box", "place": "shelf"},
     "start": "T5", "until_superseded": True},
    {"op": "account", "id": "ev-ok", "world": "w", "roles": {"actor": "tech"}, "start": "T4", "end": "T4h12"},
    {"op": "claim_effect", "id": "ok-puts", "world": "w", "event": "ev-ok", "kind": "initiates", "type": "located-at",
     "roles": {"located": "box", "place": "shelf"}},
    {"op": "account", "id": "ev-rumour", "world": "w", "roles": {"actor": "tech"}, "start": "T4", "end": "T4h12"},
    {"op": "claim_effect", "id": "rumour-puts", "world": "w", "event": "ev-rumour", "kind": "initiates",
     "type": "located-at", "roles": {"located": "box", "place": "shelf"}, "attester": "gossip"}])


@case("DX-12", ["D-EX-3"], "stage-b B-time: an explanation whose event time is unavailable is kept as "
      "timing 'unresolved', not dropped")
def dx12(L):
    e = normalise(L.wm.explain("w", "located-at", {"located": "box", "place": "shelf"}, T("T9")))
    return ({"initiated_by": [(i["event"], i["claim"]) for i in e["initiated_by"]]},
            not any(i["event"] == "ev-untimed" for i in e["initiated_by"]))


dx12.fixture = fx("explain-untimed", OBJ("box") + PLACE + EV + [
    {"op": "attest", "id": "on-shelf", "world": "w", "type": "located-at", "roles": {"located": "box", "place": "shelf"},
     "start": "T5", "until_superseded": True},
    {"op": "account", "id": "ev-untimed", "world": "w", "roles": {"actor": "tech"}, "start": "T4", "end": "T4h12",
     "attester": "gossip"},
    {"op": "claim_effect", "id": "untimed-puts", "world": "w", "event": "ev-untimed", "kind": "initiates",
     "type": "located-at", "roles": {"located": "box", "place": "shelf"}}])


@case("DX-13", ["D-CH-1"], "stage-b Q-B1.2 and the contract schema: each side of a transition has its own support; "
      "an accepted 'does not hold' side cites the attestation it rests on")
def dx13(L):
    ch = normalise(L.wm.changes("w", "box", T("T1"), T("T9")))
    rows = [(tr["track"]["kind"], tr["category"], tr["before"].get("holds"), tr["before"]["support"],
             tr["after"].get("holds"), tr["after"]["support"]) for tr in ch["transitions"]]
    h = normalise(L.wm.holds("w", "depends-on", {"dependent": "box", "dependee": "pump"}, T("T7")))
    neg = [r for r in rows if r[0] == "content" and r[4] is False]
    return ({"transitions (track, category, before.holds, before.support, after.holds, after.support)": rows,
             "holds at T7": (h["status"], h["holds"], h["support"])},
            bool(neg) and any(not r[5] for r in neg))


dx13.fixture = fx("neg-side", OBJ("box", "pump") + W + [
    {"op": "attest", "id": "dep", "world": "w", "type": "depends-on", "roles": {"dependent": "box", "dependee": "pump"},
     "start": "T2", "end": "T5"},
    {"op": "deny", "id": "not-dep", "world": "w", "type": "depends-on",
     "roles": {"dependent": "box", "dependee": "pump"}, "start": "T5", "until_superseded": True, "attester": "auditor",
     "accepted_by": ["system"]}])


@case("DX-14", ["D-EF-1"], "stage-b Q-B1.2: a move from UNKNOWN to held is a judgement transition, never presented "
      "as physical change; whether effects_of's accepted_change is bound by Q-B1 is not ruled")
def dx14(L):
    e = normalise(L.wm.effects_of("w", "ev-c", T("T9")))
    ch = normalise(L.wm.changes("w", "box", T("T1"), T("T9")))
    cats = [(tr["category"], tr["before"]["status"], tr["after"]["status"]) for tr in ch["transitions"]
            if tr["track"]["type"] == "located-at"]
    st = e[0]["state"]
    return ({"effects_of.accepted_change": st["accepted_change"], "before": st["before"]["status"],
             "after": st["after"]["status"], "changes categories": cats},
            st["accepted_change"] is True and st["before"]["status"] in ("UNKNOWN", "NOT_YET_KNOWN"))


dx14.fixture = fx("effect-unknown", OBJ("box") + PLACE + EV + [
    {"op": "account", "id": "ev-c", "world": "w", "roles": {"actor": "tech"}, "start": "T4", "end": "T4h12"},
    {"op": "claim_effect", "id": "c-puts", "world": "w", "event": "ev-c", "kind": "initiates", "type": "located-at",
     "roles": {"located": "box", "place": "dock"}},
    {"op": "attest", "id": "at-dock", "world": "w", "type": "located-at", "roles": {"located": "box", "place": "dock"},
     "start": "T4h12", "until_superseded": True}])

for c in CASES:
    c["fixture"] = c["fn"].fixture


def _rerun_dx4(L):
    """DX-4 on the full-load path without writing a second denial (the first is already recorded)."""
    den = [a for a in L.wm.visible("w", perspective="auditor") if a not in L.evidence_names()]
    c_all = normalise(L.wm.compare_measurements("w", "box", "mass"))
    c_t = normalise(L.wm.compare_measurements("w", "box", "mass", T("T3h05")))
    obs = {"compare.status": c_all["status"], "compare(t).status": c_t["status"],
           "denial listed as alternative": any(d in [m["attestation"] for m in c_all["alternatives"]] for d in den),
           "denial visible with t": any(d in json.dumps(c_t) for d in den), "measurements": len(c_all["measurements"]),
           "denied content == measured content": True}
    return obs, c_all["status"] != "DISPUTED" or c_t["status"] != "DISPUTED"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    out = []
    for c in CASES:
        rec = {"id": c["id"], "items": c["items"], "expected": c["expected"], "fixture": c["fixture"]["id"]}
        L = None
        try:
            L = load(c["fixture"])
            paths = {}
            for name, selective in (("selective", True), ("full", False)):
                L.wm.selective = selective
                paths[name] = c["fn"](L) if name == "selective" or c["id"] != "DX-4" else _rerun_dx4(L)
            L.wm.selective = True
            obs, reproduced = paths["selective"]
            rec.update(observed=obs, reproduced=bool(reproduced),
                       paths_agree=json.dumps(paths["selective"], sort_keys=True, default=str) ==
                       json.dumps(paths["full"], sort_keys=True, default=str),
                       full_path=None if paths["selective"] == paths["full"] else paths["full"])
        except Exception as e:
            rec.update(error=f"{type(e).__name__}: {e}"[:600], trace=traceback.format_exc(limit=4)[-1200:],
                       reproduced=None)
        finally:
            if L is not None:
                drop(L)
        out.append(rec)
        print(f"{rec['id']} {','.join(rec['items'])}: "
              f"{'REPRODUCED' if rec['reproduced'] else 'not reproduced' if rec['reproduced'] is False else 'ERROR'}"
              f" paths agree: {rec.get('paths_agree')} | {json.dumps(rec.get('observed', rec.get('error')), default=str)[:300]}")
    if a.json:
        a.json.write_text(json.dumps({"cases": out}, indent=1, default=str) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
