"""Stage D-2 design probe (LABS-1.025). Exploratory: a throwaway database; nothing in schema/ or src/ changes.

    uv run python -I probes/core04_d2_design.py > probes/core04_d2_design.out.json

Installs the organisation draft (docs/core-0.4/stage-d2/organisation-0.1.draft.tql) as a profile over the full core,
next to the mechanical profile, and checks the D-2 design claims with the EXISTING API only: appointments over time,
overlapping single-holder appointments, a denied appointment (DI-1), authority separate from office and capability,
grantor vs reporting source, an act in office, knowledge time and a hypothetical reorganisation.
"""

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from worldmodel import CORE_MODULES, Profile, WorldModel  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.model import READ  # noqa: E402

DRAFT = Profile("organisation-draft", "0.0-draft",
                (str(ROOT / "docs/core-0.4/stage-d2/organisation-0.1.draft.tql"),),
                slots=(("office-holding", ("class", "context"), "classified"),))


def T(day, h=9):
    return datetime(2026, 11, day, h, 0, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.now = datetime(2026, 12, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


def st(a):
    """status, then the values (value_of) or whether the content holds (holds)."""
    return [a.status.value, list(a.values)] if a.values else [a.status.value, a.holds]


out = {}
name = f"wm-d2-probe-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(name, modules=CORE_MODULES, clock=Clock())
try:
    out["P1 install"] = {"with mechanical": [wm.install_profile("mechanical"), wm.install_profile(DRAFT)],
                         "profiles": wm.profiles()}
    w = wm.create_world("actual", id="w")
    for i, kind in (("acme", "organisation"), ("depot-7", "organisation"), ("hr", "organisation"),
                    ("auditor", "organisation"), ("bea", "person"), ("cal", "person"), ("dan", "person")):
        wm.add_entity(kind, i, id=i)
    wm.add_entity("social-role", "site manager", id="site-manager")
    wm.define_capability("can sign off", id="can-sign-off")
    wm.attest(w, "part-of", {"part": "depot-7", "whole": "acme"}, start=T(1), until_superseded=True)
    office = {"class": "site-manager", "context": "depot-7"}

    # employment and membership (core member-of)
    e = wm.attest(w, "employment", {"employer": "acme", "employee": "bea"}, start=T(1), attester="hr",
                  until_superseded=True)
    wm.accept(e)
    wm.attest(w, "member-of", {"member": "cal", "group": "depot-7"}, start=T(1), until_superseded=True)

    # P2 appointments over time; an overlap of two accepted appointments
    a_bea = wm.attest(w, "office-holding", {**office, "classified": "bea"}, start=T(1), end=T(10), attester="acme")
    wm.accept(a_bea)                                               # accepted when recorded
    known_before_cal = wm._now()
    a_cal = wm.attest(w, "office-holding", {**office, "classified": "cal"}, start=T(8), until_superseded=True,
                      attester="acme")
    wm.accept(a_cal)
    out["P2 who holds the office"] = {f"day {d}": st(wm.value_of(w, "office-holding", office, T(d)))
                                      for d in (5, 9, 12)}
    out["P2 as known before cal's appointment, day 9"] = st(wm.value_of(w, "office-holding", office, T(9),
                                                                        as_of=known_before_cal))
    out["P3 roles_of during the overlap (functional conflict)"] = [
        (r["role"], r["context"], r["status"].value) for r in wm.roles_of(w, "bea", T(9))]

    # P5 authority: granted by acme, reported by hr; the grantor's own entitlement is not established
    auth = {"grantor": "acme", "holder": "bea", "power": "can-sign-off", "scope": "depot-7"}
    g = wm.attest(w, "authorisation", auth, start=T(2), until_superseded=True, attester="hr")
    wm.accept(g)
    with wm.driver.transaction(wm.database, READ) as tx:
        raw = q.documents(tx, """match $x isa authorisation (grantor: $g, holder: $h, power: $p, scope: $s);
            $a isa attestation (content: $x, attester: $who); $g has wm-id $gid; $h has wm-id $hid;
            $who has wm-id $by; fetch { "grantor": $gid, "holder": $hid, "reported by": $by };""")
    out["P5 authorisation"] = {
        "judged (system)": st(wm.holds(w, "authorisation", auth, T(5))),
        "raw: grantor vs reporting source": raw,
        "acme's own authority to grant (asked, not inferred)": st(wm.holds(
            w, "authorisation", {"grantor": "acme", "holder": "acme", "power": "can-sign-off", "scope": "depot-7"},
            T(5)))}

    # P6 office without authority; authority without office; P7 capability is a third thing
    wm.attest(w, "authorisation", {**auth, "holder": "dan"}, start=T(2), until_superseded=True)
    out["P6 office vs authority, day 12"] = {
        "cal holds the office": st(wm.holds(w, "office-holding", {**office, "classified": "cal"}, T(12))),
        "cal authorised": st(wm.holds(w, "authorisation", {**auth, "holder": "cal"}, T(12))),
        "dan holds the office": st(wm.holds(w, "office-holding", {**office, "classified": "dan"}, T(12))),
        "dan authorised": st(wm.holds(w, "authorisation", {**auth, "holder": "dan"}, T(12)))}
    out["P7 capable(bea, can-sign-off, depot-7): classification only"] = \
        wm.capable(w, "bea", "can-sign-off", T(5), "depot-7")["judgement"]

    # P8 an act in office, reported apart from office and authority at its time
    act = wm.account(w, {"official": "bea", "office": "site-manager", "office-context": "depot-7"}, T(5),
                     type="official-act", attester="bea", id="ev-sign-off")
    for a in wm.account_attestations(w, act, attester="bea"):
        wm.accept(a)
    out["P8 official act"] = {"content roles": wm.content(act)["roles"],
                              "account accepted": wm.interval(w, act) is not None,
                              "office at its time": st(wm.value_of(w, "office-holding", office, T(5))),
                              "authority at its time": st(wm.holds(w, "authorisation", auth, T(5))),
                              "occurrences claimed": wm.occurrences_of(w, act)}

    # P4 a denied appointment (polarity dispute): holds/value_of say DISPUTED; roles_of drops it (DI-1)
    d = wm.deny(w, "office-holding", {**office, "classified": "bea"}, start=T(1), end=T(10), attester="auditor")
    wm.accept(d)
    out["P4 bea's appointment denied by the auditor, accepted by the system, day 5"] = {
        "holds": st(wm.holds(w, "office-holding", {**office, "classified": "bea"}, T(5))),
        "value_of": st(wm.value_of(w, "office-holding", office, T(5))),
        "roles_of(bea)": [(r["role"], r["context"], r["status"].value) for r in wm.roles_of(w, "bea", T(5))],
        "auditor's perspective": st(wm.holds(w, "office-holding", {**office, "classified": "bea"}, T(5),
                                             perspective="auditor"))}

    # P10 a hypothetical reorganisation: dan replaces cal from day 11
    plan = wm.create_world("Plan: reorganisation", kind="hypothetical", base=w, branch_at=T(11), id="plan-reorg")
    wm.deny(plan, "office-holding", {**office, "classified": "cal"}, start=T(11), until_superseded=True)
    wm.attest(plan, "office-holding", {**office, "classified": "dan"}, start=T(11), until_superseded=True)
    out["P10 hypothetical reorganisation, day 12"] = {"plan": st(wm.value_of(plan, "office-holding", office, T(12))),
                                                      "actual": st(wm.value_of(w, "office-holding", office, T(12)))}
finally:
    wm.driver.databases.get(name).delete()

print(json.dumps(out, indent=1, default=str))
