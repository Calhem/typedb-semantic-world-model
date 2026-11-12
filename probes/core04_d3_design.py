"""Stage D-3 design probe (LABS-1.027). Exploratory: throwaway databases; nothing in schema/ or src/ changes.

    uv run python -I probes/core04_d3_design.py > probes/core04_d3_design.out.json

Builds the Stage C laboratory world over the full core, then installs the mechanical and organisation profiles and the
laboratory draft (docs/core-0.4/stage-d3/laboratory-0.1.draft.tql), and checks with the EXISTING API: coexistence,
unchanged core answers, sampling and provenance, calibration as evidence-aware content over time (expired and
disputed calibrations invalidate nothing), the four layers of a measurement, competing interpretations, an experiment
as a process, and the DI-6 case.
"""

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
from worldmodel import CORE_MODULES, Profile, ProfileError, WorldModel, organisation as org  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.examples import lab, organisation as orgex  # noqa: E402
from worldmodel.model import READ  # noqa: E402

DRAFT = Profile("laboratory-draft", "0.0-draft", (str(ROOT / "docs/core-0.4/stage-d3/laboratory-0.1.draft.tql"),),
                vocabulary=(("category", "laboratory-draft:specimen", "specimen"),
                            ("category", "laboratory-draft:experiment", "experiment"),
                            ("category", "laboratory-draft:calibration", "calibration")))
T = lab.T


class Clock:
    def __init__(self):
        self.now = datetime(2026, 12, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


def st(a):
    return [a.status.value, list(a.values)] if a.values else [a.status.value, a.holds]


def clean(x):
    """Answers without random ids (for before/after comparison)."""
    return json.loads(json.dumps(x, default=str)) if not isinstance(x, list) else \
        [{k: v for k, v in m.items() if k != "_record"} for m in x]


out = {}
name = f"wm-d3-probe-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(name, modules=CORE_MODULES, clock=Clock())
try:
    ids = lab.extend_lab_agency(wm, lab.build_lab(wm))
    w, mass = ids["world"], ids["mass"]
    M = ids["measurements"]

    def core_answers():
        return [json.dumps(clean(wm.compare_measurements(w, "sample-12", mass, T(15), perspective=p)), sort_keys=True,
                           default=str) for p in ("system", "lab-2")] + \
               [json.dumps(clean(wm.measurements(w, "sample-12", mass)), sort_keys=True, default=str),
                json.dumps(wm.capable(w, "ana", "can-weigh", T(9), "lab-1"), sort_keys=True, default=str)]

    # ---- P1/P2: coexistence, and core answers unchanged by installing all three profiles -------------------------------
    before = core_answers()
    installed = {p if isinstance(p, str) else p.name: wm.install_profile(p) for p in ("mechanical", "organisation", DRAFT)}
    import profile_fixtures as F
    try:
        wm.install_profile(F.LABORATORY)
        fixture = "installed"
    except ProfileError as e:
        fixture = "refused: " + str(e)[:150]
    out["P1 coexistence"] = {"installed": installed, "profiles": wm.profiles(),
                             "D0 laboratory test fixture alongside the draft": fixture}
    out["P2 core answers unchanged after installing three profiles"] = core_answers() == before

    for i, kind, n in (("s12-a", "sample", "Sub-sample 12a"), ("s12-b", "sample", "Sub-sample 12b"),
                       ("freezer-2", "place", "Freezer 2"), ("cert-b3", "information-object", "Certificate B3"),
                       ("cert-b7", "information-object", "Certificate B7"), ("cal-lab", "social-object", "Calibration lab"),
                       ("o-exp-1", "occurrence", "experiment 1"), ("o-sampling-1", "occurrence", "sampling 1")):
        wm.add_entity(kind, n, id=i)
    for c in ("hydrated", "anhydrous"):
        wm.add_entity("category", c, id=c)
    wm.attest(w, "classified-as", {"classified": "sample-12", "class": "laboratory-draft:specimen"}, start=T(8),
              until_superseded=True)

    # ---- P3: sampling and provenance ----------------------------------------------------------------------------------
    smp = wm.account(w, {"sampler": "ana", "sampled": "sample-12", "product": "s12-a"}, T(14), T(14, 10),
                     type="sampling", occurrence="o-sampling-1", attester="ana", id="ev-sampling-1")
    for a in wm.account_attestations(w, smp, attester="ana"):
        wm.accept(a)
    claimed = [wm.claim_effect(w, smp, "initiates", "existence", {"existent": "s12-a"}, attester="ana"),
               wm.claim_effect(w, smp, "initiates", "constitution", {"constituted": "s12-a", "constituent": "sample-12"},
                               attester="ana")]
    for c in claimed:
        wm.accept(c)
    wm.attest(w, "constitution", {"constituted": "s12-a", "constituent": "sample-12"}, start=T(14, 10),
              until_superseded=True, attester="ana")                       # accepted: ana's own, then the system's
    for a in wm.history(w, "s12-a"):
        if a["type"] == "constitution":
            wm.accept(a["attestation"])
    wm.attest(w, "constitution", {"constituted": "s12-b", "constituent": "s12-a"}, start=T(15), until_superseded=True)
    wm.attest(w, "located-at", {"located": "s12-a", "place": "freezer-2"}, start=T(14, 20), until_superseded=True)
    with wm.driver.transaction(wm.database, READ) as tx:
        chain = q.documents(tx, """match $c isa constitution (constituted: $x, constituent: $y); $x has wm-id $xid;
            $y has wm-id $yid; fetch { "sample": $xid, "from": $yid };""")
    out["P3 sampling and provenance"] = {
        "account roles": wm.content(smp)["roles"],
        "events naming the specimen": [e["event"] for e in wm.events(w, participant="sample-12") if e["event"] == smp],
        "occurrence o-sampling-1 status": wm.occurrence_status(w, "o-sampling-1", T(14, 5), details=False)["status"],
        "claimed effects (claim, state after)": [(e["outcome"]["type"], e["claim"], e["state"]["after"].holds)
                                                 for e in wm.effects_of(w, smp, T(16))],
        "s12-a existence (no attestation of it)": st(wm.holds(w, "existence", {"existent": "s12-a"}, T(16))),
        "constitution chain (raw)": sorted((d["sample"], d["from"]) for d in chain),
        "s12-a where, 16:00": st(wm.value_of(w, "located-at", {"located": "s12-a"}, T(16)))}

    # ---- P4/P5: calibration over time; expired and disputed calibrations invalidate nothing ----------------------------
    cb3 = wm.attest(w, "calibration-of", {"certificate": "cert-b3", "calibrated": "balance-b3"}, start=T(0, day=1),
                    end=T(10), attester="cal-lab", evidence=[lambda tx: "cert-b3"])
    cb7 = wm.attest(w, "calibration-of", {"certificate": "cert-b7", "calibrated": "balance-b7"}, start=T(0, day=1),
                    until_superseded=True, attester="cal-lab", evidence=[lambda tx: "cert-b7"])
    for a in (cb3, cb7):
        wm.accept(a)
    late = wm.measure(w, "sample-12", mass, 3.52, ids["kg"], 0.02, start=T(15), end=T(15, 5), instrument="balance-b3",
                      operator="ana", conditions=["temperature=20C", "humidity=40%"], calibration="CAL-B3-2026-10",
                      attester="ana", persists=True, id="m-ana-b3-late")
    lab.accept_measurement(wm, w, late)

    def calibration(instrument, at, **kw):
        cert = {"balance-b3": "cert-b3", "balance-b7": "cert-b7"}.get(instrument)
        if cert is None:
            return "no certificate recorded"
        return st(wm.holds(w, "calibration-of", {"certificate": cert, "calibrated": instrument}, at, **kw))

    def per_measurement(**kw):
        rows = {}
        for x in wm.measurements(w, "sample-12", mass, **kw):
            for r in x["records"]:
                for act in r["activities"]:
                    for instrument in act["instrument"]:
                        rows[r["record"]] = {"instrument": instrument, "stated calibration ref": r["calibration"],
                                             "calibration at activity start": calibration(instrument, act["start"].earliest, **kw),
                                             "usable": x["usable"]}
        return dict(sorted(rows.items()))
    out["P4 calibration at each activity's start (b3 certificate ends at 10:00)"] = per_measurement()
    usable = sorted(x["attestation"] == late["content"] for x in wm.compare_measurements(w, "sample-12", mass, T(16))["measurements"])
    out["P4 the measurement after expiry is still compared (not invalidated)"] = True in usable
    qa_denial = wm.deny(w, "calibration-of", {"certificate": "cert-b7", "calibrated": "balance-b7"}, start=T(0, day=1),
                        until_superseded=True, attester="qa")
    wm.accept(qa_denial)
    out["P5 b7 calibration disputed (qa's denial accepted)"] = {
        "calibration at 10:00": calibration("balance-b7", T(10)),
        "qa's own perspective": calibration("balance-b7", T(10), perspective="qa"),
        "bo's b7 result still usable": [x["usable"] for x in wm.measurements(w, "sample-12", mass)
                                        if x["attestation"] == M["bo-b7"]["content"]]}

    # ---- P6: the four layers of one measurement ----------------------------------------------------------------------
    m = M["bo-b7"]
    key = wm._content_key(m["content"])
    out["P6 activity / record / proposition / judgement"] = {
        "activity (an event description)": [m["activity"], wm.content(m["activity"])["type"]],
        "result record (an information object)": [m["result"], wm._record(m["result"])["raw_value"],
                                                  wm._record(m["result"])["raw_unit"]],
        "proposition (content, SI)": key,
        "judgement, system": [x["acceptance"] for x in wm.measurements(w, "sample-12", mass)
                              if x["attestation"] == m["content"]],
        "judgement, lab-2": [x["acceptance"] for x in wm.measurements(w, "sample-12", mass, perspective="lab-2")
                             if x["attestation"] == m["content"]]}

    # ---- P7: competing interpretations of results ----------------------------------------------------------------------
    hyp = wm.attest(w, "classified-as", {"classified": "sample-12", "class": "hydrated"}, start=T(12),
                    until_superseded=True, stance="hypothesises", basis="inference", attester="ana",
                    evidence=[lambda tx: M["ana-b9-35C"]["result"]])
    rival = wm.attest(w, "classified-as", {"classified": "sample-12", "class": "anhydrous"}, start=T(11),
                      until_superseded=True, basis="inference", attester="lab-2",
                      evidence=[lambda tx: M["lab2"]["result"]])
    wm.accept(hyp)
    with wm.driver.transaction(wm.database, READ) as tx:
        resting = q.documents(tx, """match $r isa information-object, has wm-id $rid;
            rests-on (attestation: $a, record: $r); $a links (content: $c, attester: $who), has stance $s;
            $c isa classified-as (class: $k); $k has wm-id $kid; $who has wm-id $by;
            fetch { "record": $rid, "class": $kid, "by": $by, "stance": $s };""")
    out["P7 competing interpretations"] = {
        "hydrated (ana hypothesises; accepted)": st(wm.holds(w, "classified-as", {"classified": "sample-12",
                                                                                  "class": "hydrated"}, T(16))),
        "anhydrous (lab-2 asserts; unreviewed)": st(wm.holds(w, "classified-as", {"classified": "sample-12",
                                                                                   "class": "anhydrous"}, T(16))),
        "anhydrous, lab-2's perspective": st(wm.holds(w, "classified-as", {"classified": "sample-12",
                                                                           "class": "anhydrous"}, T(16),
                                                      perspective="lab-2")),
        "interpretations resting on result records (raw)": sorted((d["record"], d["class"], d["by"], d["stance"])
                                                                  for d in resting)}
    wm.accept(rival)
    out["P7 competing interpretations"]["both accepted: anhydrous"] = st(wm.holds(
        w, "classified-as", {"classified": "sample-12", "class": "anhydrous"}, T(16)))

    # ---- P8: an experiment as a process --------------------------------------------------------------------------------
    wm.attest(w, "classified-as", {"classified": "o-exp-1", "class": "laboratory-draft:experiment"},
              until_superseded=True)
    wm.attest(w, "part-of", {"part": "o-sampling-1", "whole": "o-exp-1"}, start=T(14), until_superseded=True)
    out["P8 experiment steps"] = [(s["occurrence"], s["descriptions"], s["actors"])
                                  for s in wm.process_steps(w, "o-exp-1", T(16))]
finally:
    wm.driver.databases.get(name).delete()

# ---- DI-6 (register verification, organisation world): mixed constituent statuses folded into ASSERTED ---------------
name = f"wm-d3-probe-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(name, modules=CORE_MODULES, clock=Clock())
try:
    wm.install_profile("organisation")
    oids = orgex.build_organisation(wm)
    org.appoint(wm, oids["plan"], "fay", "safety-officer", "depot-7", start=orgex.T(11))
    v = org.office_holders(wm, oids["plan"], "safety-officer", "depot-7", orgex.T(12))
    out["DI-6 safety officers in the plan, day 12"] = {
        "per holder": {a["holder"]: a["status"].value for a in v["appointments"] if a["judgement"] == "established"},
        "overall": v["status"].value}
finally:
    wm.driver.databases.get(name).delete()

print(json.dumps(out, indent=1, default=str))
