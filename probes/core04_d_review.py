"""Stage D design review probes (LABS-1.021). Exploratory: throwaway databases only; nothing in schema/ or src/ changes.

    uv run python -I probes/core04_d_review.py > probes/core04_d_review.out.json

Loads the exploratory profile drafts (docs/core-0.4/stage-d/drafts/*.tql) on top of the full Core 0.4 schema and checks,
against the existing API, what each domain requirement needs. Each probe records what happened, not what was hoped.
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from worldmodel import QUALITY_MODULES, WorldModel  # noqa: E402
from worldmodel.keys import proposition_key  # noqa: E402
from worldmodel.model import SCHEMA  # noqa: E402

DRAFTS = ROOT / "docs/core-0.4/stage-d/drafts"


def T(day, h=9):
    return datetime(2026, 11, day, h, 0, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.now = datetime(2026, 12, 1, tzinfo=timezone.utc)

    def __call__(self):
        from datetime import timedelta
        self.now += timedelta(seconds=1)
        return self.now


def status(a):
    """status, and for holds() answers whether the content holds (True / False / None)."""
    return [a.status.value, a.holds] if hasattr(a, "holds") else a.status.value


out = {}
name = f"wm-d-probe-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(name, modules=QUALITY_MODULES, clock=Clock())
try:
    # ---- D0: the drafts install after the core, together, with no collision ---------------------------------------
    before = set(wm.proposition_types())
    for f in ("core-dependency-kind", "mechanical-0.1", "organisation-0.1", "laboratory-0.1"):
        wm.install_module(f"draft-{f}", files=[str(DRAFTS / f"{f}.tql")], version="0.0-draft")
    added = sorted(set(wm.proposition_types()) - before)
    out["D0 install"] = {
        "installed": [m for m in wm.modules() if str(m).startswith("draft-")] if isinstance(wm.modules(), list)
        else sorted(k for k in wm.modules() if k.startswith("draft-")),
        "new proposition types": added,
        "lattice": {x: wm.core_type(x) for x in ("person", "organisation", "sample", "office-holding", "replacement",
                                                 "decision", "sampling")},
        "specialised roles": {r: wm.core_role(r) for r in ("replacement:removed", "replacement:fitted",
                                                           "decision:decider", "sampling:sampled")},
    }

    w = wm.create_world("actual", id="w")
    for i, kind in (("workshop", "place"), ("bay-1", "place"), ("depot-7", "place"), ("pump", "physical-object"),
                    ("motor", "physical-object"), ("manual", "information-object"), ("b1", "physical-object"),
                    ("b3", "physical-object"), ("tech", "physical-object"), ("acme", "organisation"),
                    ("auditor", "organisation"), ("bea", "person"), ("cal", "person"), ("rock", "physical-object"),
                    ("arm", "physical-object"), ("s12", "sample"), ("balance", "physical-object"),
                    ("cert-1", "information-object")):
        wm.add_entity(kind, i, id=i)
    for c in ("functional", "informational", "agent"):
        wm.add_entity("category", c, id=c)
    for r in ("site-manager", "analyst"):
        wm.add_entity("social-role", r, id=r)
    for c in ("can-replace-bearing", "can-sign-off"):
        wm.define_capability(c, id=c)

    # ---- D1a: capability contexts are matched exactly; part-of between contexts is not used -----------------------
    wm.attest(w, "part-of", {"part": "bay-1", "whole": "workshop"}, until_superseded=True)
    wm.grant(w, "tech", "can-replace-bearing", context="workshop", start=T(1))
    out["D1a context scope"] = {
        "in workshop": wm.capable(w, "tech", "can-replace-bearing", T(5), "workshop")["judgement"],
        "in bay-1 (part of workshop)": wm.capable(w, "tech", "can-replace-bearing", T(5), "bay-1")["judgement"],
    }

    # ---- D1b: depends-on with a kind; existing kind-less content unchanged ----------------------------------------
    plain = proposition_key("depends-on", {"dependent": "pump", "dependee": "motor"}, {})
    wm.attest(w, "depends-on", {"dependent": "pump", "dependee": "motor", "kind": "functional"}, until_superseded=True)
    wm.attest(w, "depends-on", {"dependent": "pump", "dependee": "manual", "kind": "informational"},
              until_superseded=True)
    out["D1b dependency kind"] = {
        "kind-less key unchanged by the draft": plain == "depends-on|dependee=motor|dependent=pump",
        "dependencies(pump) mixes kinds": wm.dependencies(w, "pump", T(5)),
        "functional only (via holds)": status(wm.holds(w, "depends-on", {"dependent": "pump", "dependee": "motor",
                                                                          "kind": "functional"}, T(5))),
    }

    # ---- D1c-alt: two specialisations of one core role in one event (TypeDB behaviour) ------------------------------
    with wm.driver.transaction(wm.database, SCHEMA) as tx:
        tx.query("""define relation swap-alt sub event, relates out-part as patient, relates in-part as patient;
            physical-object plays swap-alt:out-part, plays swap-alt:in-part;""").resolve()
        tx.commit()
    wm._types = wm._lattice = None
    try:
        wm.describe_event({"out-part": "b1", "in-part": "b3"}, type="swap-alt", id="ev-alt")
        out["D1c-alt two specialisations of patient"] = "accepted"
    except Exception as e:  # noqa: BLE001
        out["D1c-alt two specialisations of patient"] = "rejected: " + " ".join(str(e).split())[:160]

    # ---- D1c: replacement with distinguished removed / fitted parts ------------------------------------------------
    rep = wm.account(w, {"actor": "tech", "removed": "b1", "fitted": "b3"}, T(5), T(5, 10), type="replacement",
                     id="ev-rep")
    out["D1c replacement roles"] = {
        "content roles": wm.content(rep)["roles"],
        "core view": wm.content(rep).get("core"),
        "events naming b1 (lattice)": [e["event"] for e in wm.events(w, participant="b1")],
    }

    # ---- D2a: a single-holder office vs an ordinary role ------------------------------------------------------------
    wm.declare_slot("office-holding", ["class", "context"], "classified")
    a1 = wm.attest(w, "office-holding", {"classified": "bea", "class": "site-manager", "context": "depot-7"},
                   start=T(1), until_superseded=True, attester="acme")
    a2 = wm.attest(w, "office-holding", {"classified": "cal", "class": "site-manager", "context": "depot-7"},
                   start=T(3), until_superseded=True, attester="auditor")
    for a in (a1, a2):
        wm.accept(a)
    for p in ("bea", "cal"):
        wm.attest(w, "classified-as", {"classified": p, "class": "analyst", "context": "depot-7"}, start=T(1),
                  until_superseded=True)
    office = wm.value_of(w, "office-holding", {"class": "site-manager", "context": "depot-7"}, T(5))
    out["D2a single-holder office"] = {
        "who is site manager at depot-7 (two accepted accounts)": [status(office), list(office.values)],
        "analysts are not exclusive": [f["status"].value for f in wm.facts_about(w, "cal", T(5))
                                       if f["roles"].get("class") == ["analyst"]],
        "roles_of(bea) sees the office": [(r["role"], r["context"]) for r in wm.roles_of(w, "bea", T(5))],
        "capable(bea, site-manager) sees it (is_a)": wm.capable(w, "bea", "site-manager", T(5), "depot-7")["judgement"],
    }

    # ---- D2b: holding an office is not having authority ------------------------------------------------------------
    wm.end(w, a2, T(3, 10), reason="test retraction for D2b")          # leave bea as the only holder from here
    auth = {"grantor": "acme", "holder": "bea", "power": "can-sign-off", "scope": "depot-7"}
    out["D2b office vs authority"] = {"before any authorisation": {
        "bea holds the office": status(wm.holds(w, "office-holding", {"classified": "bea", "class": "site-manager",
                                                                      "context": "depot-7"}, T(2))),
        "authorisation": status(wm.holds(w, "authorisation", auth, T(2))),
        "capable(bea, can-sign-off, depot-7)": wm.capable(w, "bea", "can-sign-off", T(2), "depot-7")["judgement"]}}
    g = wm.attest(w, "authorisation", auth, start=T(4), until_superseded=True, attester="acme")
    wm.accept(g)
    d = wm.deny(w, "authorisation", auth, start=T(4), until_superseded=True, attester="auditor")
    out["D2b office vs authority"]["after acme's grant (accepted) and the auditor's denial (unreviewed)"] = {
        "authorisation": status(wm.holds(w, "authorisation", auth, T(5))),
        "auditor's perspective": status(wm.holds(w, "authorisation", auth, T(5), perspective="auditor")),
        "capable(bea, can-sign-off, depot-7) (classification only)":
            wm.capable(w, "bea", "can-sign-off", T(5), "depot-7")["judgement"]}
    wm.accept(d)
    out["D2b office vs authority"]["after the system also accepts the denial"] = status(
        wm.holds(w, "authorisation", auth, T(5)))

    # ---- D2c: an act in the capacity of an office (a concept as an event participant) ------------------------------
    try:
        dec = wm.account(w, {"decider": "bea", "capacity": "site-manager", "location": "depot-7"}, T(6), type="decision",
                         id="ev-sign")
        out["D2c capacity"] = {"content roles": wm.content(dec)["roles"],
                               "events naming bea": [e["event"] for e in wm.events(w, participant="bea")]}
    except Exception as e:  # noqa: BLE001
        out["D2c capacity"] = {"error": f"{type(e).__name__}: {e}"}

    # ---- D2d: employment changes over time; an organisation as an agent ------------------------------------------
    e1 = wm.attest(w, "employment", {"employer": "acme", "employee": "bea"}, start=T(1), end=T(10), attester="acme")
    wm.accept(e1)
    wm.grant(w, "acme", "agent", start=T(1))
    ch = wm.changes(w, "bea", T(2), T(12))
    out["D2d employment"] = {
        "transitions of bea (2-12 Nov)": sorted({(tr["track"]["type"], tr["category"]) for tr in ch["transitions"]}),
        "acme is an agent (social object)": wm.is_agent(w, "acme", T(5))["judgement"],
    }

    # ---- D3a: sampling: sampled origin and product, with constitution -------------------------------------------
    smp = wm.account(w, {"sampler": "arm", "sampled": "rock", "product": "s12"}, T(2), type="sampling", id="ev-smp")
    wm.attest(w, "constitution", {"constituted": "s12", "constituent": "rock"}, start=T(2), until_superseded=True)
    out["D3a sampling"] = {"events naming the rock": [e["event"] for e in wm.events(w, participant="rock")],
                           "s12 facts": sorted(f["type"] for f in wm.facts_about(w, "s12", T(5)))}

    # ---- D3b: calibration as attested content resting on a certificate --------------------------------------------
    cal = wm.attest(w, "calibration-of", {"certificate": "cert-1", "calibrated": "balance"}, start=T(1), end=T(8),
                    evidence=[lambda tx: "cert-1"])
    out["D3b calibration"] = {
        "rests on the certificate": wm.evidence_of(cal),
        "calibrated on 5 Nov": status(wm.holds(w, "calibration-of", {"certificate": "cert-1", "calibrated": "balance"},
                                               T(5))),
        "calibrated on 9 Nov": status(wm.holds(w, "calibration-of", {"certificate": "cert-1", "calibrated": "balance"},
                                               T(9))),
    }

    # ---- raw TypeQL quoted in docs/core-0.4/stage-d-review.md, section 6 (profile-level drafts) ---------------------
    from worldmodel import typeql as q
    from worldmodel.model import READ
    raw = {
        "authority at depot-7": """match $x isa authorisation (grantor: $g, holder: $h, power: $p, scope: $s);
  $p has wm-id "can-sign-off"; $s has wm-id "depot-7"; $a isa attestation (content: $x, attester: $who), has polarity $pol;
  $g has wm-id $gid; $h has wm-id $hid; $who has wm-id $by;
fetch { "holder": $hid, "grantor": $gid, "polarity": $pol, "by": $by };""",
        "functional dependencies only": """match $d isa depends-on (dependent: $x, dependee: $y, kind: $k); $k has wm-id "functional";
  $x has wm-id $xid; $y has wm-id $yid;
fetch { "dependent": $xid, "dependee": $yid };""",
    }
    with wm.driver.transaction(wm.database, READ) as tx:
        out["raw TypeQL (review section 6)"] = {k: sorted((q.documents(tx, v)), key=lambda d: json.dumps(d, sort_keys=True))
                                                 for k, v in raw.items()}
finally:
    wm.driver.databases.get(name).delete()

print(json.dumps(out, indent=1, default=str, sort_keys=False))
