"""Profile organisation-0.1 (Core 0.4 Stage D-2, LABS-1.026): employment, offices, authority and acts in office.

Four independent things, with no implication between any of them. Role names below are the stored ones that readers
take (`holds`, `judgement`: core role names, LABS-1.052; other names are refused with UnknownRoleError):
- **office-holding**: `office-holding(classified: holder, class: office, context)`, a position in a context
  (a subtype of classified-as, whose roles it keeps);
- **practical capability**: `classified-as(classified: holder, class: capability, context?)`, read by the core
  `capable()`;
- **conferred authority**: `authorisation(grantor, holder, power, scope)`; the reporting source is the attestation's
  attester, never the grantor; the grantor's own entitlement is never assessed; no delegation chains;
- **actual action**: an `official-act` description (`official` is stored as the core role `actor`); its occurrence is
  judged apart (`occurrence_status`).

**Single-holder offices.** An office is exclusive only where an `exclusive-office(office, context)` constraint holds
at t (attested, over its own valid time). Then, if several accepted appointments overlap at t, the reports say
DISPUTED, citing the appointments and the constraint. Appointments are never rejected on writing; each keeps its own
judgement and evidence. Nothing is inferred about anyone no appointment mentions: absence of evidence stays absence
("not established"), distinct from an explicit, accepted denial ("denied").

**Disputes are visible.** The reports read each content's canonical judgement (as `capable()` does), so content
disputed by polarity is listed as DISPUTED, never dropped; so does core `roles_of` (DI-1, LABS-1.038).

**Exclusivity is the core's.** The profile declares the scope of `exclusive-office` (EXCLUSIVE_OFFICE); the core's
canonical judgement applies it, only where the constraint is itself established in the same world, time, knowledge
time and perspective, in every reader (`holds`, `facts_about`, `capable`). `office_holders` and `offices_of` keep their
public answers (LABS-1.038, choice A): each appointment's own judgement is reported before the constraint, and the
conflict, read from the canonical judgement, is reported beside it.

Functions take the WorldModel, as in `worldmodel.mechanical`.
"""

from .judgement import AttestedConstraint, attested_conflict, collection_status, combine, without_attested
from .model import SCHEMA_DIR, SYSTEM
from .profiles import PROFILES, EventRole, Profile
from .semantics import Status

NAME = "organisation"
# An exclusive office: where exclusive-office(office, context) is established at t, office-holding with that office
# (class) and context has at most one holder (classified). Judged by the core's canonical mechanism (LABS-1.038).
EXCLUSIVE_OFFICE = AttestedConstraint("exclusive-office", "office-holding",
                                      (("office", "class"), ("context", "context")), "classified")
# An official act is one official's act in one office within one context (a joint act is several acts), so for one
# occurrence its official (actor), office and office context are single-valued, unconditionally (LABS-1.043, ER-6).
# 0.2 (LABS-1.043) adds these three event-role constraints to 0.1 (data only; the schema file is unchanged).
# 0.3 (LABS-1.049, DI-13, MP-1, MP-4) opens the official to several players per account and adds the category
# organisation:co-signed: an act established as co-signed at its start has a set of officials (co-participation,
# established when every compared account names the same set); every other act keeps one official (ER-6).
CO_SIGNED = "organisation:co-signed"
_SCHEMA_01 = (str(SCHEMA_DIR / "profiles" / "organisation" / "organisation-0.1.tql"),)
_VOCAB_01 = (("category", "organisation:appointment", "appointment"),
             ("category", "organisation:dismissal", "dismissal"))
_ROLES_02 = (EventRole("official-act", "actor"), EventRole("official-act", "office"),
             EventRole("official-act", "office-context"))
PROFILE_01 = Profile(NAME, "0.1", _SCHEMA_01, vocabulary=_VOCAB_01, attested_constraints=(EXCLUSIVE_OFFICE,))
PROFILE_02 = Profile(NAME, "0.2", _SCHEMA_01, vocabulary=_VOCAB_01, attested_constraints=(EXCLUSIVE_OFFICE,),
                     event_roles=_ROLES_02, upgrades_from="0.1", previous=PROFILE_01)
PROFILE = Profile(NAME, "0.3", _SCHEMA_01 + (str(SCHEMA_DIR / "profiles" / "organisation" / "organisation-0.3.tql"),),
                  vocabulary=_VOCAB_01 + (("category", CO_SIGNED, "co-signed act"),),
                  attested_constraints=(EXCLUSIVE_OFFICE,),
                  event_roles=_ROLES_02 + (EventRole("official-act", "actor", CO_SIGNED, "set"),),
                  upgrades_from="0.2", opens=("official-act:official",), previous=PROFILE_02)
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
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]


def _judged(wm, entry):
    """One content's judgement, in the capable() vocabulary, with its evidence (the shared helper)."""
    return wm._judgement(entry)


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
    for e in wm._contents(world, x, ("employment",), t, as_of, perspective):
        if e.about("employer") or e.about("employee"):
            out.append({"employer": e.stated_roles["employer"][0], "employee": e.stated_roles["employee"][0],
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
    """(each appointment for the office and context with its own judgement, before the exclusivity constraint;
    whether the canonical judgement puts established appointments in conflict under that constraint)."""
    out, conflicted = [], False
    for e in wm._contents(world, context, ("office-holding",), t, as_of, perspective):
        if office in e.stated("class") and e.about("context"):
            # the constraint key holds canonical players: the least name of the class (Identity.canonical)
            conflicted = conflicted or attested_conflict(e, "exclusive-office", (office, min(e.subject))) is not None
            out.append({"holder": e.stated_roles["classified"][0], **_judged(wm, without_attested(e))})
    return sorted(out, key=lambda r: r["holder"]), conflicted


def office_holders(wm, world, office, context, t, as_of=None, perspective=SYSTEM):
    """Who holds `office` in `context` at t, for the perspective.
    - appointments: every appointment content for this office and context, each with its own judgement and evidence
      (established, denied, expired, not yet effective, disputed, not established);
    - holders: the established ones;
    - exclusive: the single-holder constraint's own judgement at t;
    - conflict: when the constraint holds and more than one appointment is established: the constraint's support and
      each conflicting appointment's accepted attestations;
    - status (rule C, increment C): DISPUTED on a conflict or a disputed appointment; None when holders are
      established without conflict (there is no single support status for several people, or for the office: each
      appointment keeps its own status); UNKNOWN when appointments exist but none is established; NOT_YET_KNOWN when
      there are none.
    Nothing is inferred about anyone not mentioned."""
    _require(wm)
    entries, conflicted = _appointments(wm, world, office, context, t, as_of, perspective)
    holders = [h["holder"] for h in entries if h["judgement"] == "established"]
    exclusive = _constraint(wm, world, office, context, t, as_of, perspective)
    conflict = None
    if conflicted:                      # the canonical judgement: the constraint is established, holders differ
        conflict = {"constraint": {"office": office, "context": context, "support": exclusive["support"]},
                    "appointments": [{"holder": h["holder"],
                                      "attestations": [a["attestation"] for a in h["evidence"]
                                                       if a["acceptance"] == "accepted"]}
                                     for h in entries if h["judgement"] == "established"]}
    return {"office": office, "context": context, "holders": holders, "status": collection_status(entries, conflict),
            "exclusive": exclusive, "conflict": conflict, "appointments": _public(entries)}


def offices_of(wm, world, person, t, as_of=None, perspective=SYSTEM):
    """Every office appointment naming `person`, each with its own judgement and evidence at t. An established
    appointment to an exclusive office that others also hold at t is DISPUTED, with the conflict cited. No entry
    means no evidence either way (never a denial)."""
    _require(wm)
    out = []
    for e in wm._contents(world, person, ("office-holding",), t, as_of, perspective):
        if not e.about("classified"):
            continue
        office, context = e.stated_roles["class"][0], e.stated_roles["context"][0]
        entry = {"office": office, "context": context, **_judged(wm, without_attested(e)), "conflict": None}
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
    holds / status / judgement as capable() (same six cases, combined over the grants by rule Q; `support`: the
    deciding claims the status rests on); grants: each authorisation content for that power and
    scope, with its grantor and its reporting sources as separate fields and its own judgement and evidence; only_in:
    scopes where the power is established instead; grantor_entitlement: always "not assessed" (D-D-3)."""
    _require(wm)
    found = []
    for e in wm._contents(world, holder, ("authorisation",), t, as_of, perspective):
        if e.about("holder") and power in e.stated("power"):
            found.append({"grantor": e.stated_roles["grantor"][0], "scope": e.stated_roles["scope"][0],
                          "reported_by": sorted({a["attester"] for a in e.claims()}), **_judged(wm, e)})
    grants = sorted((g for g in found if g["scope"] == scope), key=lambda g: g["grantor"])
    holds, status, judgement, support = combine([g["_record"] for g in grants], bool(found))
    return {"holder": holder, "power": power, "scope": scope, "holds": holds, "status": status,
            "judgement": judgement, "support": list(support), "grants": _public(grants),
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
    there is no time, so nothing at the act's time is judged (None).

    Several officials (a co-signed act, organisation 0.3, LABS-1.049): `officials` lists every official named and
    `by_official` gives each one's office_held, authority, capability and agent. With exactly one official the
    top-level fields are that official's, as before; with several, `official` and the four top-level judgement
    fields are None (no official is chosen over another). Whether several officials are co-signatories or
    conflicting evidence is judged by `occurrence()`, not here."""
    _require(wm)
    content = wm.content(event)
    if content is None or not wm.is_a(content["type"], "official-act"):
        raise ValueError(f"{event!r} is not an official-act description")
    officials, office = sorted(content["roles"]["official"]), content["roles"]["office"][0]
    context = content["roles"]["office-context"][0]
    span = wm.interval(world, event, as_of, perspective)
    at = span[0].earliest if span and span[0] else None
    report = {"event": event, "official": officials[0] if len(officials) == 1 else None, "officials": officials,
              "office": office, "context": context,
              "account": "accepted" if span else "not accepted", "start": span[0] if span else None,
              "end": span[1] if span else None,
              "occurrences": [{"occurrence": o, "status": wm.occurrence_status(world, o, at, as_of, perspective,
                                                                              details=False)["status"]
                               if at is not None else None}
                              for o in wm.occurrences_of(world, event, as_of, perspective)],
              "office_held": None, "authority": None, "capability": None, "agent": None,
              "by_official": {o: {"office_held": None, "authority": None, "capability": None, "agent": None}
                              for o in officials}}
    if at is None:
        return report
    for official in officials:
        mine = report["by_official"][official]
        held = [o for o in offices_of(wm, world, official, at, as_of, perspective)
                if o["office"] == office and o["context"] == context]
        mine["office_held"] = ({"judgement": held[0]["judgement"], "status": held[0]["status"],
                                "conflict": held[0]["conflict"]} if held
                               else {"judgement": "not established", "status": None, "conflict": None})
        if power is not None:
            a = authorised(wm, world, official, power, context, at, as_of, perspective)
            c = wm.capable(world, official, power, at, context, as_of, perspective)
            mine["authority"] = {"judgement": a["judgement"], "status": a["status"],
                                 "grantors": [g["grantor"] for g in a["grants"] if g["judgement"] == "established"],
                                 "grantor_entitlement": NOT_ASSESSED}
            mine["capability"] = {"judgement": c["judgement"], "status": c["status"]}
        mine["agent"] = wm.is_agent(world, official, at, as_of, perspective)["judgement"]
    if len(officials) == 1:
        report.update(report["by_official"][officials[0]])
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
