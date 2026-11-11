"""The organisational reference world (Core 0.4 Stage D-2, LABS-1.026): Acme and its depot 7, November 2026.

An invented organisation; names are illustrative. Needs CORE_MODULES and the organisation profile.

- structure and people: depot-7 and hr are units of acme (core part-of); bea, cal, dan, eve, fay are people;
  employment by acme (reported by hr); membership of depot-7 (core member-of);
- offices: site manager of depot-7 is exclusive (acme's constraint); bea holds it [1, 10), cal from day 8, so days 8-10
  are an exclusivity conflict; the auditor denies cal's appointment (its own view; not accepted by the system);
  safety officer of depot-7 is not exclusive and has two holders (dan, eve);
- authority: acme conferred can-sign-off within depot-7 on bea and on dan, each reported by hr (the source is not the
  grantor); dan has the authority but not the ability; eve has the ability (a capability classification) but no
  authority;
- acts in office: bea signs off on day 5 as site manager (account accepted, no occurrence claimed); cal signs off on
  day 9, inside the conflict, describing an occurrence nobody attests existed;
- an appointment event (acme appoints fay safety officer, with an accepted "initiates" claim) without any appointment
  claim: it makes fay no office holder;
- knowledge time: everything recorded before cal's appointment is marked; a hypothetical reorganisation in which dan
  replaces cal from day 11.
"""

from datetime import datetime, timezone


def T(day, h=9):
    return datetime(2026, 11, day, h, 0, tzinfo=timezone.utc)


def build_organisation(wm):
    """Write the Acme world into `wm`. Ids that already exist (shared vocabulary such as `agent` or `can-sign-off`,
    which the gearbox's Stage C extension also defines) are reused, so the world composes with the others."""
    from .. import organisation as o
    from .. import typeql as q
    from ..model import READ
    w = wm.create_world("Acme, actual", id="org")
    wanted = [*(("organisation", n, i) for i, n in (("acme", "Acme"), ("depot-7", "Depot 7"), ("hr", "Acme HR"),
                                                    ("auditor", "External auditor"))),
              *(("person", i.capitalize(), i) for i in ("bea", "cal", "dan", "eve", "fay")),
              ("social-role", "site manager", "site-manager"), ("social-role", "safety officer", "safety-officer"),
              ("capability", "can sign off", "can-sign-off"), ("category", "agent", "agent")]
    with wm.driver.transaction(wm.database, READ) as tx:
        present = {i for _, _, i in wanted if q.rows(tx, "match $x has wm-id == $id;", {"id": i})}
    for kind, n, i in wanted:
        if i not in present:
            wm.add_entity(kind, n, id=i)
    for unit in ("depot-7", "hr"):
        wm.attest(w, "part-of", {"part": unit, "whole": "acme"}, start=T(1), until_superseded=True)
    for x in ("acme", "hr", "auditor", "bea", "cal", "dan", "eve", "fay"):
        wm.grant(w, x, "agent", start=T(1))
    ids = {"world": w}
    # employment (reported by hr) and membership
    ids["employment"] = {p: o.employ(wm, w, "acme", p, start=T(1), attester="hr", **({"end": T(20)} if p == "eve" else {}))
                         for p in ("bea", "cal", "dan", "eve")}
    for a in ids["employment"].values():
        wm.accept(a)
    for p in ("bea", "cal"):
        wm.attest(w, "member-of", {"member": p, "group": "depot-7"}, start=T(1), until_superseded=True)
    # offices
    ids["exclusive"] = o.declare_exclusive(wm, w, "site-manager", "depot-7", start=T(1), attester="acme")
    wm.accept(ids["exclusive"])
    ids["bea_site"] = o.appoint(wm, w, "bea", "site-manager", "depot-7", start=T(1), end=T(10), attester="acme")
    wm.accept(ids["bea_site"])
    ids["known_before_cal"] = wm._now()
    ids["cal_site"] = o.appoint(wm, w, "cal", "site-manager", "depot-7", start=T(8), attester="acme")
    wm.accept(ids["cal_site"])
    ids["auditor_denial"] = o.appoint(wm, w, "cal", "site-manager", "depot-7", polarity=False, start=T(8),
                                      attester="auditor")
    ids["safety"] = {p: o.appoint(wm, w, p, "safety-officer", "depot-7", start=T(d), attester="acme")
                     for p, d in (("dan", 1), ("eve", 3))}
    for a in ids["safety"].values():
        wm.accept(a)
    # authority (granted by acme, reported by hr) and ability, kept apart
    ids["auth_bea"] = o.authorise(wm, w, "acme", "bea", "can-sign-off", "depot-7", attester="hr", start=T(2))
    ids["auth_dan"] = o.authorise(wm, w, "acme", "dan", "can-sign-off", "depot-7", attester="hr", start=T(2))
    for a in (ids["auth_bea"], ids["auth_dan"]):
        wm.accept(a)
    ids["eve_ability"] = wm.grant(w, "eve", "can-sign-off", context="depot-7", start=T(1))
    # acts in office
    ids["act_bea"] = o.act_in_office(wm, w, "bea", "site-manager", "depot-7", T(5), attester="bea", id="ev-bea-signs")
    wm.add_entity("occurrence", "sign-off on day 9", id="o-signoff-9")
    ids["act_cal"] = o.act_in_office(wm, w, "cal", "site-manager", "depot-7", T(9), occurrence="o-signoff-9",
                                     attester="cal", id="ev-cal-signs")
    for ev, by in (("ev-bea-signs", "bea"), ("ev-cal-signs", "cal")):
        for a in wm.account_attestations(w, ev, attester=by):
            wm.accept(a)
    # an appointment event alone (no appointment claim): it does not make fay a safety officer
    ids["fay_event"] = wm.account(w, {"actor": "acme", "patient": "fay"}, T(6), kind="organisation:appointment",
                                  attester="acme", id="ev-appoint-fay")
    ids["fay_effect"] = wm.claim_effect(w, "ev-appoint-fay", "initiates", "office-holding",
                                        {"classified": "fay", "class": "safety-officer", "context": "depot-7"},
                                        attester="acme")
    for a in wm.account_attestations(w, "ev-appoint-fay", attester="acme") + [ids["fay_effect"]]:
        wm.accept(a)
    # a hypothetical reorganisation: dan replaces cal as site manager from day 11
    ids["plan"] = wm.create_world("Plan: reorganisation", kind="hypothetical", base=w, branch_at=T(11),
                                  id="org-plan-reorg")
    o.appoint(wm, ids["plan"], "cal", "site-manager", "depot-7", polarity=False, start=T(11))
    o.appoint(wm, ids["plan"], "dan", "site-manager", "depot-7", start=T(11))
    return ids
