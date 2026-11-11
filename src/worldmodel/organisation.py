"""Profile organisation-0.1 (Core 0.4 Stage D-2, LABS-1.026): employment, offices, authority and acts in office.

Four independent things, with no implication between any of them:
- **office-holding**: `office-holding(holder, office, context)`, a position in a context;
- **practical capability**: `classified-as(holder, capability, context?)`, read by the core `capable()`;
- **conferred authority**: `authorisation(grantor, holder, power, scope)`; the reporting source is the attestation's
  attester, never the grantor; the grantor's own entitlement is never assessed; no delegation chains;
- **actual action**: an `official-act` description; its occurrence is judged apart (`occurrence_status`).

**Single-holder offices.** An office is exclusive only where an `exclusive-office(office, context)` constraint holds
at t (attested, over its own valid time). Then, if several accepted appointments overlap at t, the reports say
DISPUTED, citing the appointments and the constraint. Appointments are never rejected on writing; each keeps its own
judgement and evidence. Nothing is inferred about anyone no appointment mentions: absence of evidence stays absence
("not established"), distinct from an explicit, accepted denial ("denied").

**Disputes are visible.** The reports read each content's judgement (as `capable()` does), so content disputed by
polarity is listed as DISPUTED, never dropped. Core `roles_of` is unchanged (DI-1).

Functions take the WorldModel, as in `worldmodel.mechanical`.
"""

from .model import SCHEMA_DIR, SYSTEM
from .profiles import PROFILES, Profile
from .semantics import Status

NAME = "organisation"
PROFILE = Profile(NAME, "0.1", (str(SCHEMA_DIR / "profiles" / "organisation" / "organisation-0.1.tql"),),
                  vocabulary=(("category", "organisation:appointment", "appointment"),
                              ("category", "organisation:dismissal", "dismissal")))
PROFILES[NAME] = PROFILE
NOT_ASSESSED = "not assessed"


def _require(wm):
    if NAME not in wm.profiles():
        raise ValueError("the organisation profile is not installed (wm.install_profile('organisation'))")


def _until(attest):
    if "end" not in attest:
        attest.setdefault("until_superseded", True)
    return attest


def _public(rows):
    """Drop the internal per-content label from report rows."""
    return [{k: v for k, v in r.items() if k != "_label"} for r in rows]


def _judged(wm, entry):
    """One content's judgement, in the capable() vocabulary, with its evidence."""
    label = wm._holding_label(entry)
    holds, status, judgement = wm._combine([{"judgement": label, "status": entry["status"]}], True)
    return {"judgement": judgement, "holds": holds, "status": status, "evidence": entry["attestations"],
            "_label": label}


# ---- employment ----------------------------------------------------------------------------------------------------------
def employ(wm, world, employer, employee, polarity=True, **attest):
    """Attest that `employer` (an organisation) employs `employee` (a person). polarity False: a denial."""
    _require(wm)
    return wm.attest(world, "employment", {"employer": employer, "employee": employee}, polarity=polarity,
                     **_until(attest))


def employment(wm, world, x, t, as_of=None, perspective=SYSTEM):
    """Every employment content naming x (as employer or employee) with its judgement at t, evidence included:
    established, denied, expired, not yet effective, disputed, or not established (only unreviewed/rejected claims)."""
    out = []
    for e in wm._claims(world, x, ("employment",), t, as_of, perspective):
        if x in e["roles"].get("employer", []) + e["roles"].get("employee", []):
            out.append({"employer": e["roles"]["employer"][0], "employee": e["roles"]["employee"][0],
                        **_judged(wm, e)})
    return _public(sorted(out, key=lambda r: (r["employer"], r["employee"])))


# ---- offices -------------------------------------------------------------------------------------------------------------
def appoint(wm, world, holder, office, context, polarity=True, **attest):
    """Attest that `holder` holds `office` in `context` (a claim by its attester, over its interval). Never refused
    because the office is held already. polarity False: an explicit denial of that appointment."""
    _require(wm)
    return wm.attest(world, "office-holding", {"classified": holder, "class": office, "context": context},
                     polarity=polarity, **_until(attest))


def declare_exclusive(wm, world, office, context, **attest):
    """Attest a single-holder constraint on `office` within `context`, over its valid time."""
    _require(wm)
    return wm.attest(world, "exclusive-office", {"office": office, "context": context}, **_until(attest))


def _constraint(wm, world, office, context, t, as_of, perspective):
    a = wm.holds(world, "exclusive-office", {"office": office, "context": context}, t, as_of, perspective)
    return {"holds": a.holds, "status": a.status, "support": list(a.support)}


def _appointments(wm, world, office, context, t, as_of, perspective):
    out = []
    for e in wm._claims(world, context, ("office-holding",), t, as_of, perspective):
        if office in e["roles"].get("class", []) and context in e["roles"].get("context", []):
            out.append({"holder": e["roles"]["classified"][0], **_judged(wm, e)})
    return sorted(out, key=lambda r: r["holder"])


def _overall(entries, conflict):
    established = [h for h in entries if h["judgement"] == "established"]
    if conflict or any(h["judgement"] == "disputed" for h in entries):
        return Status.DISPUTED
    if established:
        statuses = sorted({h["status"] for h in established}, key=lambda s: s.value)
        return statuses[0] if len(statuses) == 1 else Status.ASSERTED      # per-holder statuses are authoritative
    return Status.UNKNOWN if entries else Status.NOT_YET_KNOWN


def office_holders(wm, world, office, context, t, as_of=None, perspective=SYSTEM):
    """Who holds `office` in `context` at t, for the perspective.
    - appointments: every appointment content for this office and context, each with its own judgement and evidence
      (established, denied, expired, not yet effective, disputed, not established);
    - holders: the established ones;
    - exclusive: the single-holder constraint's own judgement at t;
    - conflict: when the constraint holds and more than one appointment is established: the constraint's support and
      each conflicting appointment's accepted attestations; the status is then DISPUTED.
    Nothing is inferred about anyone not mentioned."""
    _require(wm)
    entries = _appointments(wm, world, office, context, t, as_of, perspective)
    holders = [h["holder"] for h in entries if h["judgement"] == "established"]
    exclusive = _constraint(wm, world, office, context, t, as_of, perspective)
    conflict = None
    if exclusive["holds"] is True and len(holders) > 1:
        conflict = {"constraint": {"office": office, "context": context, "support": exclusive["support"]},
                    "appointments": [{"holder": h["holder"],
                                      "attestations": [a["attestation"] for a in h["evidence"]
                                                       if a["acceptance"] == "accepted"]}
                                     for h in entries if h["judgement"] == "established"]}
    return {"office": office, "context": context, "holders": holders, "status": _overall(entries, conflict),
            "exclusive": exclusive, "conflict": conflict, "appointments": _public(entries)}


def offices_of(wm, world, person, t, as_of=None, perspective=SYSTEM):
    """Every office appointment naming `person`, each with its own judgement and evidence at t. An established
    appointment to an exclusive office that others also hold at t is DISPUTED, with the conflict cited. No entry
    means no evidence either way (never a denial)."""
    _require(wm)
    out = []
    for e in wm._claims(world, person, ("office-holding",), t, as_of, perspective):
        if person not in e["roles"].get("classified", []):
            continue
        office, context = e["roles"]["class"][0], e["roles"]["context"][0]
        entry = {"office": office, "context": context, **_judged(wm, e), "conflict": None}
        if entry["judgement"] == "established":
            view = office_holders(wm, world, office, context, t, as_of, perspective)
            if view["conflict"]:
                entry.update(status=Status.DISPUTED, conflict=view["conflict"])
        out.append(entry)
    return _public(sorted(out, key=lambda r: (r["office"], r["context"])))


# ---- authority -----------------------------------------------------------------------------------------------------------
def authorise(wm, world, grantor, holder, power, scope, attester=SYSTEM, polarity=True, **attest):
    """Attest, as `attester` (the reporting source), that `grantor` conferred `power` (a capability concept) on `holder`
    within `scope`. The grantor and the attester are separate arguments; neither defaults to the other."""
    _require(wm)
    return wm.attest(world, "authorisation", {"grantor": grantor, "holder": holder, "power": power, "scope": scope},
                     polarity=polarity, attester=attester, **_until(attest))


def authorised(wm, world, holder, power, scope, t, as_of=None, perspective=SYSTEM):
    """Is `holder` authorised to exercise `power` within exactly `scope` at t (D-D-4: no containment)?
    holds / status / judgement as capable() (same six cases); grants: each authorisation content for that power and
    scope, with its grantor and its reporting sources as separate fields and its own judgement and evidence; only_in:
    scopes where the power is established instead; grantor_entitlement: always "not assessed" (D-D-3)."""
    _require(wm)
    found = []
    for e in wm._claims(world, holder, ("authorisation",), t, as_of, perspective):
        if holder in e["roles"].get("holder", []) and power in e["roles"].get("power", []):
            found.append({"grantor": e["roles"]["grantor"][0], "scope": e["roles"]["scope"][0],
                          "reported_by": sorted({a["attester"] for a in e["attestations"]}), **_judged(wm, e)})
    grants = sorted((g for g in found if g["scope"] == scope), key=lambda g: g["grantor"])
    holds, status, judgement = wm._combine([{"judgement": g["_label"], "status": g["status"]} for g in grants],
                                           bool(found))
    return {"holder": holder, "power": power, "scope": scope, "holds": holds, "status": status,
            "judgement": judgement, "grants": _public(grants),
            "only_in": sorted({g["scope"] for g in found if g["scope"] != scope and g["judgement"] == "established"}),
            "grantor_entitlement": NOT_ASSESSED}


# ---- acts in office ------------------------------------------------------------------------------------------------------
def act_in_office(wm, world, official, office, context, start, end=None, occurrence=None, attester=SYSTEM, id=None,
                  kind=None):
    """A source's account of `official` acting in `office` within `context` (an `official-act` description)."""
    _require(wm)
    return wm.account(world, {"official": official, "office": office, "office-context": context}, start, end or start,
                      type="official-act", kind=kind, occurrence=occurrence, attester=attester, id=id)


def official_act(wm, world, event, power=None, as_of=None, perspective=SYSTEM):
    """Report an official act for the perspective, as separate fields, concluding nothing beyond them:
    account (accepted or not, interval); occurrences with their own status; at the act's start: the official's office
    appointment (its judgement, and DISPUTED with the conflict if contested), and, for `power`, authority in the
    office's context (authorised) and practical capability there (capable), and agency. Without an accepted account
    there is no time, so nothing at the act's time is judged (None)."""
    _require(wm)
    content = wm.content(event)
    if content is None or not wm.is_a(content["type"], "official-act"):
        raise ValueError(f"{event!r} is not an official-act description")
    official, office = content["roles"]["official"][0], content["roles"]["office"][0]
    context = content["roles"]["office-context"][0]
    span = wm.interval(world, event, as_of, perspective)
    at = span[0].earliest if span and span[0] else None
    report = {"event": event, "official": official, "office": office, "context": context,
              "account": "accepted" if span else "not accepted", "start": span[0] if span else None,
              "end": span[1] if span else None,
              "occurrences": [{"occurrence": o, "status": wm.occurrence_status(world, o, at, as_of, perspective,
                                                                              details=False)["status"]
                               if at is not None else None}
                              for o in wm.occurrences_of(world, event, as_of, perspective)],
              "office_held": None, "authority": None, "capability": None, "agent": None}
    if at is None:
        return report
    held = [o for o in offices_of(wm, world, official, at, as_of, perspective)
            if o["office"] == office and o["context"] == context]
    report["office_held"] = ({"judgement": held[0]["judgement"], "status": held[0]["status"],
                              "conflict": held[0]["conflict"]} if held
                             else {"judgement": "not established", "status": None, "conflict": None})
    if power is not None:
        a = authorised(wm, world, official, power, context, at, as_of, perspective)
        c = wm.capable(world, official, power, at, context, as_of, perspective)
        report["authority"] = {"judgement": a["judgement"], "status": a["status"],
                               "grantors": [g["grantor"] for g in a["grants"] if g["judgement"] == "established"],
                               "grantor_entitlement": NOT_ASSESSED}
        report["capability"] = {"judgement": c["judgement"], "status": c["status"]}
    report["agent"] = wm.is_agent(world, official, at, as_of, perspective)["judgement"]
    return report
