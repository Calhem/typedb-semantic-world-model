"""Increment C design (LABS-1.039, DI-6): executable examples of mixed STIPULATED, ASSERTED and INFERRED support.

    uv run python -I probes/pre_e_c_examples.py <checkout>

Builds one throwaway database (wm-probe-pre-e-c-*, deleted afterwards) with the core and the three profiles, writes the
cases of docs/core-0.4/pre-e-increment-c-design.md, section "Examples", and prints for each the current answer and the
answer under the proposed rule. The proposed rule is computed here, in the probe, from the canonical records
(`wm.judgement`): no source file is changed. Each case asserts both, so the probe fails if the current behaviour
differs from what the design records; after increment C is implemented it is updated to assert the new behaviour.

Proposed rule for one question answered by several holdings (`capable`, `authorised`, `calibration_status`):
- DISPUTED if any applicable holding is disputed, or one is established while another is denied (unchanged);
- holds True: the core rule (answer_status) over the union of the support of the established holdings;
- holds False: the core rule over the union of the support of the denied and expired holdings;
- otherwise UNKNOWN or NOT_YET_KNOWN (unchanged).
For a report over distinct items (`office_holders`): no folded support status; DISPUTED, UNKNOWN, NOT_YET_KNOWN only,
and None when holders are established without conflict (approved choice E, LABS-1.036).
For a slot's value in `changes` (E10): the core rule over the support of the values held, as `value_of` does.
Output: probes/pre_e_c_examples.out.txt.
"""

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, connect, laboratory as lb, organisation as org  # noqa: E402
from worldmodel.judgement import Judgement, ENDED  # noqa: E402
from worldmodel.semantics import Status, answer_status  # noqa: E402

OUT = {}


def T(day, h=9):
    return datetime(2026, 11, day, h, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


def name(s):
    return s.name if isinstance(s, Status) else s


def show(case, **values):
    OUT[case] = values
    print(f"\n=== {case}")
    for k, v in values.items():
        print(f"  {k}: {json.dumps(v, default=name)}")


def proposed(recs):
    """The proposed one-question rule, over canonical records."""
    js = [r.judgement for r in recs]
    est = [r for r in recs if r.judgement is Judgement.ESTABLISHED]
    neg = [r for r in recs if r.judgement is Judgement.NOT_HOLDING and r.reasons[0] in ("denied", ENDED)]
    if Judgement.DISPUTED in js or (est and any(r.reasons[0] == "denied" for r in neg)):
        return Status.DISPUTED
    if est:
        return answer_status([a for r in est for a in r.support])
    if neg:
        return answer_status([a for r in neg for a in r.support])
    return "UNKNOWN or NOT_YET_KNOWN (unchanged)"


driver = connect()
DB = f"wm-probe-pre-e-c-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(DB, driver=driver, modules=CORE_MODULES, clock=Clock())
try:
    for p in ("mechanical", "organisation", "laboratory"):
        wm.install_profile(p)
    w = wm.create_world("actual", id="w")
    for p in ("bea", "cal", "dan", "eve", "fay", "gus", "hr", "audit", "lab"):
        wm.add_entity("person", p, id=p)
    for i in ("balance", "box"):
        wm.add_entity("physical-object", i, id=i)
    for i in ("room-1", "room-2", "room-3"):
        wm.add_entity("place", i, id=i)
    for kind, i in (("organisation", "acme"), ("organisation", "board"), ("organisation", "depot"),
                    ("social-role", "analyst"), ("social-role", "office-x"), ("capability", "can-sign")):
        wm.add_entity(kind, i, id=i)
    for c in ("cert-1", "cert-2", "cert-3", "cert-4"):
        lb.register_certificate(wm, c, reference=c.upper(), id=c)

    # ---- actual world: what the plan inherits (ASSERTED, by HR or the lab, accepted by the system; the audit
    # perspective has accepted none of them) ---------------------------------------------------------------------------
    def hr(att):
        wm.accept(att)
        return att
    hr(wm.grant(w, "dan", "analyst", start=T(1), attester="hr"))                        # E1 general, ASSERTED
    hr(wm.grant(w, "cal", "analyst", context="depot", start=T(1), attester="hr"))       # E1 contextual, ASSERTED
    hr(wm.grant(w, "eve", "analyst", start=T(1), attester="hr", basis="inference"))     # E3 general, INFERRED
    hr(wm.grant(w, "eve", "analyst", context="depot", start=T(1), attester="hr"))       # E3 contextual, ASSERTED
    hr(wm.grant(w, "fay", "analyst", start=T(1), end=T(4), attester="hr"))              # E4 general, ended: expired
    hr(wm.grant(w, "gus", "analyst", start=T(1), attester="hr"))                        # E5 general, ASSERTED
    hr(org.authorise(wm, w, "acme", "bea", "can-sign", "depot", attester="hr", start=T(1)))   # E6 ASSERTED
    hr(org.appoint(wm, w, "bea", "office-x", "depot", start=T(1), attester="hr"))       # E8 ASSERTED
    hr(lb.calibrate(wm, w, "cert-2", "balance", start=T(1), attester="lab", basis="inference"))  # E7 INFERRED
    hr(lb.calibrate(wm, w, "cert-3", "balance", start=T(1), attester="lab"))            # E7 ASSERTED
    # E10 (actual world): the box's locations are INFERRED; another room is denied by an ASSERTED claim
    hr(wm.attest(w, "located-at", {"located": "box", "place": "room-1"}, start=T(1), end=T(4), basis="inference",
                 attester="hr"))
    hr(wm.attest(w, "located-at", {"located": "box", "place": "room-3"}, start=T(4), until_superseded=True,
                 basis="inference", attester="hr"))
    hr(wm.attest(w, "located-at", {"located": "box", "place": "room-2"}, polarity=False, start=T(1),
                 until_superseded=True, attester="audit"))
    hr(org.employ(wm, w, "acme", "bea", start=T(1), attester="hr"))                   # E9 ASSERTED
    plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(2), id="plan")

    # ---- the plan's own claims (STIPULATED: constitutive of the plan, so accepted for every perspective, E7) ------
    wm.grant(plan, "dan", "analyst", context="depot", start=T(3))                       # E1 contextual, STIPULATED
    wm.grant(plan, "cal", "analyst", start=T(3))                                        # E1 general, STIPULATED
    wm.grant(plan, "fay", "analyst", context="depot", polarity=False, start=T(3))       # E4 contextual denial
    wm.grant(plan, "gus", "analyst", context="depot", polarity=False, start=T(3))       # E5 contextual denial
    org.authorise(wm, plan, "board", "bea", "can-sign", "depot", start=T(3))            # E6 STIPULATED
    org.appoint(wm, plan, "cal", "office-x", "depot", start=T(3))                       # E8 STIPULATED
    lb.calibrate(wm, plan, "cert-1", "balance", start=T(3))                             # E7 STIPULATED

    def cap_recs(world, holder, t, context, perspective):
        """The canonical record of each applicable holding, chosen by its exact roles (as capable() chooses them)."""
        return [e for e in wm._contents(world, holder, ("classified-as",), t, None, perspective)
                if e.stated_roles.get("classified") == [holder] and e.stated_roles.get("class") == ["analyst"]
                and e.stated_roles.get("context", [None])[0] in (None, context)]

    def cap(case, holder, perspectives=("system", "audit"), t=T(5)):
        row = {}
        for p in perspectives:
            c = wm.capable(plan, holder, "analyst", t, context="depot", perspective=p)
            row[p] = {"current": [c["status"], c["judgement"]],
                      "holdings": [(h["context"], h["judgement"], h["status"]) for h in c["applicable"]],
                      "proposed": proposed(cap_recs(plan, holder, t, "depot", p))}
        show(case, **row)
        return row

    e1d = cap("E1 capable(dan): general inherited ASSERTED + contextual STIPULATED", "dan")
    e1c = cap("E1 capable(cal): general STIPULATED + contextual inherited ASSERTED (the mirror)", "cal")
    assert name(e1d["system"]["current"][0]) == "ASSERTED" and name(e1c["system"]["current"][0]) == "STIPULATED"
    assert e1d["system"]["proposed"] == e1c["system"]["proposed"] == Status.STIPULATED
    assert name(e1d["audit"]["current"][0]) == name(e1d["audit"]["proposed"]) == "STIPULATED"  # audit: only the plan's

    e3 = cap("E3 capable(eve): general INFERRED + contextual ASSERTED, both inherited", "eve")
    assert name(e3["system"]["current"][0]) == "INFERRED" and e3["system"]["proposed"] == Status.ASSERTED

    e4 = cap("E4 capable(fay): general expired (ASSERTED) + contextual denial STIPULATED", "fay")
    assert e4["system"]["current"][1] == "denied" and e4["system"]["proposed"] == Status.STIPULATED

    e5 = cap("E5 capable(gus): general established ASSERTED + contextual denial STIPULATED (conflict)", "gus")
    assert name(e5["system"]["current"][0]) == "DISPUTED" == name(e5["system"]["proposed"])
    assert e5["audit"]["current"][1] == "denied"         # audit has not accepted HR's grant: only the denial applies

    # E2: the actual world for the same holders: only HR's claims, nothing to combine differently
    a = wm.capable(w, "dan", "analyst", T(5), context="depot")
    show("E2 capable(dan) in the actual world", current=[a["status"], a["judgement"]])
    assert name(a["status"]) == "ASSERTED"

    # E6 authorised: two grantors for one power and scope
    row = {}
    for p in ("system", "audit"):
        r = org.authorised(wm, plan, "bea", "can-sign", "depot", T(5), perspective=p)
        recs = [wm.judgement(plan, "authorisation", {"grantor": g, "holder": "bea", "power": "can-sign",
                                                     "scope": "depot"}, T(5), perspective=p) for g in ("acme", "board")]
        row[p] = {"current": [r["status"], r["judgement"]],
                  "grants": [(g["grantor"], g["judgement"], g["status"]) for g in r["grants"]],
                  "proposed": proposed(recs)}
    show("E6 authorised(bea, can-sign, depot): acme inherited ASSERTED + board STIPULATED", **row)
    assert name(row["system"]["current"][0]) == "ASSERTED" and row["system"]["proposed"] == Status.STIPULATED

    # E7 calibration_status: three certificates in force, three bases
    row = {}
    for p in ("system", "audit"):
        r = lb.calibration_status(wm, plan, "balance", T(5), perspective=p)
        recs = [wm.judgement(plan, "calibration-of", {"certificate": c, "calibrated": "balance"}, T(5), perspective=p)
                for c in ("cert-1", "cert-2", "cert-3")]
        row[p] = {"current": [r["status"], r["judgement"]],
                  "certificates": [(c["certificate"], c["judgement"], c["status"]) for c in r["certificates"]],
                  "proposed": proposed(recs)}
    show("E7 calibration_status(balance): cert-1 STIPULATED, cert-2 INFERRED, cert-3 ASSERTED", **row)
    assert row["system"]["proposed"] == Status.STIPULATED

    # E8 office_holders: two holders of a non-exclusive office, different statuses (DI-6 as registered)
    row = {}
    for world, p in ((plan, "system"), (plan, "audit"), (w, "system")):
        r = org.office_holders(wm, world, "office-x", "depot", T(5), perspective=p)
        row[f"{world}/{p}"] = {"current": r["status"], "holders": r["holders"],
                               "appointments": [(x["holder"], x["judgement"], x["status"]) for x in r["appointments"]],
                               "proposed": None if r["holders"] and name(r["status"]) != "DISPUTED" else r["status"]}
    show("E8 office_holders(office-x, depot): bea inherited ASSERTED + cal STIPULATED", **row)
    assert name(row["plan/system"]["current"]) == "ASSERTED" and row["plan/system"]["proposed"] is None

    # E9 employment: distinct contents, each with its own status; no aggregate exists or is proposed
    org.employ(wm, plan, "acme", "cal", start=T(3))
    rows = org.employment(wm, plan, "acme", T(5))
    show("E9 employment(acme) in the plan", rows=[(r["employee"], r["judgement"], r["status"]) for r in rows])
    assert [name(r["status"]) for r in rows] == ["ASSERTED", "STIPULATED"]

    # E10 one slot, another value denied: value_of and the changes() track disagree on the status
    v = wm.value_of(w, "located-at", {"located": "box"}, T(5))
    ch = wm.changes(w, "box", T(2), T(6))
    tr = [x for x in ch["transitions"] if x["track"]["kind"] == "slot"]
    show("E10 located-at(box), actual world: room-1 then room-3 INFERRED; room-2 denied, ASSERTED",
         value_of_at_day_5=[v.status, list(v.values)],
         changes_transition=[{"category": x["category"], "before": [x["before"]["status"], x["before"]["values"]],
                              "after": [x["after"]["status"], x["after"]["values"]]} for x in tr])
    assert name(v.status) == "INFERRED"
    assert [name(x["after"]["status"]) for x in tr] == ["ASSERTED"]       # the denial of room-2 is folded in
finally:
    driver.databases.get(DB).delete()
