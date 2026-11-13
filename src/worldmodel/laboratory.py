"""Profile laboratory-0.1 (Core 0.4 Stage D-3, LABS-1.028): samples, sampling, calibration and interpretations.

Over the core and the Stage C measurement model (activity, result record, proposition, judgement), this module adds:
- **samples and sampling**: a `sample` is a portion of matter (splitting it gives new particulars); `take_sample`
  records a source's `sampling` account and the effects it claims; `provenance` lists, separately, the attested
  constitution chain, the sampling accounts and their occurrences' own status, the claimed effects, existence and
  location history. An account establishes neither its occurrence nor the sample's existence or constitution.
- **calibration**: `calibration-of(certificate, instrument)`, attested over the certificate's valid time and resting
  on the certificate. `calibration_status` judges it at a time (established, expired, denied, disputed, not yet
  effective, not established); `measurement_calibration` judges it at each measurement activity's start and puts
  the record's **stated** reference beside the **attested** calibration, with an exact-text reference check. Nothing
  here changes a measurement's acceptance, usability or comparison.
- **interpretations**: `interpret` records an analyst's conclusion as testimony, or as a hypothesis (stance
  `hypothesises`, never supporting an answer), resting on its result record; `interpretations` lists everything
  resting on a record, each content judged on its own. Basis `inference` is reserved for rule-derived attestations
  (D-D3-4): `interpret` refuses it, and `interpretations` flags any such attestation as recorded inference without
  derivation structure. Formal derivation provenance (named rule and premises) is a Stage E requirement (DI-7).
  Competing interpretations are judged independently: no incompatibility is assumed (D-D3-6).

Specimens and experiments are classifications (`laboratory:specimen`, `laboratory:experiment`); an experiment's
steps are core `part-of` (read with `process_steps`). Judgement uses the shared helpers (`_judgement`, `_combine`).
Functions take the WorldModel, as in `worldmodel.mechanical` and `worldmodel.organisation`.
"""

from .operations import atomic
from . import typeql as q
from .keys import check_new_id
from .model import READ, SCHEMA_DIR, SYSTEM
from .profiles import PROFILES, Profile

NAME = "laboratory"
PROFILE = Profile(NAME, "0.1", (str(SCHEMA_DIR / "profiles" / "laboratory" / "laboratory-0.1.tql"),),
                  vocabulary=(("category", "laboratory:specimen", "specimen"),
                              ("category", "laboratory:experiment", "experiment"),
                              ("category", "laboratory:calibration", "calibration")))
PROFILES[NAME] = PROFILE
SPECIMEN, EXPERIMENT, CALIBRATION = "laboratory:specimen", "laboratory:experiment", "laboratory:calibration"
NO_DERIVATION = "not a formal derivation: no named rule or premises are recorded (Stage E, DI-7)"
MODES = {"observation": "observation", "testimony": "testimony", "stipulation": "stipulation",
         "inference": "recorded as inference without derivation structure (G-1)"}


def _require(wm):
    if NAME not in wm.profiles():
        raise ValueError("the laboratory profile is not installed (wm.install_profile('laboratory'))")


def _until(attest):
    if "end" not in attest:
        attest.setdefault("until_superseded", True)
    return attest


def _public(rows):
    return [{k: v for k, v in r.items() if k != "_label"} for r in rows]


# ---- samples and sampling ----------------------------------------------------------------------------------------------
@atomic
def take_sample(wm, world, sampler, specimen, sample, start, end=None, occurrence=None, attester=SYSTEM, id=None,
                kind=None):
    """A source's account of `sampler` taking `sample` (a `sample` particular) from `specimen`: a `sampling`
    description attested over [start, end], optionally describing `occurrence`, and the effects the source claims for
    it: it initiates existence(sample) and constitution(sample, specimen). Claims only: nothing here establishes that
    the sampling happened, that the sample exists or what it is made of. Returns the ids.
    One operation (DI-8): the account and its effect claims are written together or not at all; inside a caller's
    `wm.operation()` it joins that operation (e.g. with the creation of the sample or part)."""
    _require(wm)
    event = wm.account(world, {"sampler": sampler, "sampled": specimen, "product": sample}, start, end or start,
                       type="sampling", kind=kind, occurrence=occurrence, attester=attester, id=id)
    effects = [wm.claim_effect(world, event, "initiates", "existence", {"existent": sample}, attester=attester),
               wm.claim_effect(world, event, "initiates", "constitution",
                               {"constituted": sample, "constituent": specimen}, attester=attester)]
    return {"event": event, "effects": effects}


def _sampling_accounts(wm, world, sample, t, as_of, perspective):
    with wm._reading() as tx:
        events = sorted({q.opt(r, "eid") for r in q.rows(tx, """match $p has wm-id == $id;
            $e isa sampling (product: $p), has wm-id $eid;""", {"id": sample})})
    out = []
    for e in events:
        if not wm.account_attestations(world, e, as_of=as_of):
            continue                                   # a description no source gives in this world (or its bases)
        roles = wm.content(e)["roles"]
        span = wm.interval(world, e, as_of, perspective)
        at = span[0].earliest if span and span[0] else None
        out.append({"event": e, "sampler": roles.get("sampler", []), "sampled": roles.get("sampled", []),
                    "account": "accepted" if span else "not accepted",
                    "start": span[0] if span else None, "end": span[1] if span else None,
                    "occurrences": [{"occurrence": o,
                                     "status": wm.occurrence_status(world, o, at, as_of, perspective,
                                                                    details=False)["status"] if at else None}
                                    for o in wm.occurrences_of(world, e, as_of, perspective)],
                    "claimed_effects": [{"kind": x["kind"], "outcome": x["outcome"]["type"], "claim": x["claim"],
                                         "claimed_by": x["claimed_by"],
                                         "after": x["state"]["after"].holds if x["state"] else None}
                                        for x in wm.effects_of(world, e, t, as_of, perspective)]})
    return out


def provenance(wm, world, sample, t, as_of=None, perspective=SYSTEM):
    """Where `sample` came from, for the perspective at t, as separate fields that conclude nothing beyond them:
    - chain: every constitution content met by following "constituted from" links back from `sample`, each once (the
      sample, what it is said to be made from, and that link's own judgement and evidence). A listing of attested
      links, not an inference: an unaccepted, disputed or denied link is listed with its judgement, never dropped, and
      followed. Each link also carries (LABS-1.031):
      - paths: every distinct route from `sample` to and including the link (as [sample, from] steps), with
        `established` (every step on the route is established at t in this world, perspective and knowledge time),
        `blocked_by` (each step that is not, with its own judgement and evidence) and `closes_cycle` (the link leads
        back to a material already on the route, so the route stops there);
      - ancestry: "established" when at least one of its paths is established, else "not established". A link that
        is itself established, but reached only through an unestablished step, is not established ancestry;
    - established: the established-provenance view: only the links with an established path, with those paths;
    - materials: every material reached (other than `sample`), with each route to it and whether that route is
      established. Converging routes to one material are kept apart;
    - sampling: for each material reached, the sampling accounts naming it as product: the account's acceptance,
      the occurrences it describes with their own status, and the effects it claims with the claim's judgement;
    - existence: the sample's attested existence (its own judgement), and the core `exists` answer beside it (which
      also infers existence from participation in holding content);
    - locations: every location attestation of the sample (place, source, interval, acceptance), and where it is at t.
    Routes are simple (no material twice), so cyclic claims terminate; their number can grow with converging
    lineages. Each material's claims are read once."""
    _require(wm)
    claims, links, materials, order = {}, {}, {}, [sample]

    def claims_of(x):
        if x not in claims:
            claims[x] = [(src, wm._judgement(e)) for e in wm._claims(world, x, ("constitution",), t, as_of, perspective)
                         if x in e["roles"].get("constituted", []) for src in e["roles"].get("constituent", [])]
        return claims[x]

    todo = [(sample, [], (sample,))]                     # breadth first: (material, route so far, materials on it)
    while todo:
        x, route, on_route = todo.pop(0)
        for source, j in claims_of(x):
            key = (x, source)
            link = links.setdefault(key, {"sample": x, "from": source, **j, "paths": []})
            steps = route + [key]
            blocked = [{"sample": a, "from": b, **{k: links[(a, b)][k] for k in ("judgement", "status", "evidence")}}
                       for a, b in steps if links[(a, b)]["judgement"] != "established"]
            cycle = source in on_route
            link["paths"].append({"path": [list(k) for k in steps], "established": not blocked,
                                  "blocked_by": blocked, "closes_cycle": cycle})
            if not cycle:
                materials.setdefault(source, []).append({"path": [list(k) for k in steps], "established": not blocked})
                if source not in order:
                    order.append(source)
                todo.append((source, steps, on_route + (source,)))
    chain = list(links.values())
    for link in chain:
        link["ancestry"] = "established" if any(p["established"] for p in link["paths"]) else "not established"
    established = [{"sample": c["sample"], "from": c["from"], "judgement": c["judgement"], "status": c["status"],
                    "evidence": c["evidence"], "paths": [p["path"] for p in c["paths"] if p["established"]]}
                   for c in chain if c["ancestry"] == "established"]
    existence = [wm._judgement(e) for e in wm._claims(world, sample, ("existence",), t, as_of, perspective)
                 if sample in e["roles"].get("existent", [])]
    core = wm.exists(world, sample, t, as_of, perspective)
    here = wm.value_of(world, "located-at", {"located": sample}, t, as_of, perspective)
    return {"sample": sample, "t": t, "chain": _public(chain), "established": established,
            "materials": {x: {"established": any(p["established"] for p in ps), "paths": ps} for x, ps in materials.items()},
            "sampling": {x: _sampling_accounts(wm, world, x, t, as_of, perspective) for x in order},
            "existence": {"attested": _public(existence)[0] if existence else
                          {"judgement": "not established", "holds": None, "status": None, "evidence": []},
                          "core_exists": {"status": core.status, "holds": core.holds}},
            "locations": [{"place": h["roles"]["place"][0], "attester": h["attester"], "start": h["start"],
                           "end": h["end"], "acceptance": h["state"], "superseded": h["superseded"]}
                          for h in wm.history(world, sample, type="located-at", as_of=as_of, perspective=perspective)
                          if sample in h["roles"].get("located", [])],
            "location_at_t": {"status": here.status, "places": list(here.values)}}


# ---- calibration -------------------------------------------------------------------------------------------------------
def register_certificate(wm, name, reference=None, id=None):
    """A calibration certificate: an information object with its own reference number (`calibration-ref`, exact text),
    written in one transaction. The certificate is a document; what it says is attested with `calibrate`."""
    _require(wm)
    cid = check_new_id(id or wm._mint("information-object"))
    params = {"id": cid, "n": name}
    extra = ""
    if reference is not None:
        extra, params["r"] = ", has calibration-ref == $r", reference
    with wm._writing(None) as tx:
        q.run(tx, f"insert $x isa information-object, has wm-id == $id, has name == $n{extra};", params)
    return cid


def calibrate(wm, world, certificate, instrument, start=None, end=None, attester=SYSTEM, polarity=True, **attest):
    """Attest, as `attester`, that `certificate` calibrates `instrument` from `start` to `end` (or until superseded),
    resting on the certificate (rests-on, written in the same transaction). polarity False: an explicit denial that
    the certificate establishes the calibration (e.g. a quality office disputing it)."""
    _require(wm)
    if end is not None:
        attest["end"] = end
    return wm.attest(world, "calibration-of", {"certificate": certificate, "calibrated": instrument}, start=start,
                     polarity=polarity, attester=attester, evidence=[lambda tx: certificate], **_until(attest))


def _references(wm, certificates):
    if not certificates:
        return {}
    out = {}
    with wm._reading() as tx:
        for c in certificates:
            rows = q.rows(tx, "match $x isa information-object, has wm-id == $id, has calibration-ref $r;", {"id": c})
            out[c] = q.opt(rows[0], "r") if rows else None
    return out


def calibration_status(wm, world, instrument, t, as_of=None, perspective=SYSTEM):
    """Is `instrument` calibrated at t, for the perspective? holds / status / judgement as capable() (established,
    expired, denied, disputed, not yet effective, not established; no new statuses), and every certificate whose
    calibration content names the instrument, with its reference number, its own judgement and its evidence.
    "not established" with no certificates means that no calibration is recorded at all."""
    _require(wm)
    found = []
    for e in wm._claims(world, instrument, ("calibration-of",), t, as_of, perspective):
        if instrument in e["roles"].get("calibrated", []):
            found.append({"certificate": e["roles"]["certificate"][0], **wm._judgement(e)})
    refs = _references(wm, [c["certificate"] for c in found])
    for c in found:
        c["reference"] = refs[c["certificate"]]
    found.sort(key=lambda c: c["certificate"])
    holds, status, judgement = wm._combine([{"judgement": c["_label"], "status": c["status"]} for c in found],
                                           bool(found))
    return {"instrument": instrument, "t": t, "holds": holds, "status": status, "judgement": judgement,
            "in_force": [c["certificate"] for c in found if c["judgement"] == "established"],
            "certificates": _public(found)}


def _reference_check(stated, instrument, attested):
    """The record's stated reference against the instrument's certificates' own numbers: exact text, reported, never
    reconciled (G-6)."""
    if instrument is None:
        return {"check": "no instrument recorded", "certificates": []}
    if stated is None:
        return {"check": "no reference stated", "certificates": []}
    if not attested["certificates"]:
        return {"check": "no certificate recorded for the instrument", "certificates": []}
    matching = [{"certificate": c["certificate"], "judgement": c["judgement"]} for c in attested["certificates"]
                if c["reference"] == stated]
    if matching:
        return {"check": "matches a certificate", "certificates": matching}
    return {"check": "no certificate with the stated reference", "certificates": []}


def measurement_calibration(wm, world, bearer, quality, t=None, as_of=None, perspective=SYSTEM):
    """For each measurement of `quality` of `bearer` (wm.measurements), each result record and each activity
    instrument: the record's **stated** calibration reference, the **attested** calibration judged at the activity's
    start (calibration_status), and the exact-text check of one against the other. The measurement's own acceptance
    and usability are copied from wm.measurements unchanged: calibration never invalidates, discards or downgrades a
    measurement, and an activity without an accepted account has no time, so its calibration is not judged (None)."""
    _require(wm)
    rows = []
    for m in wm.measurements(world, bearer, quality, t, as_of, perspective):
        for r in m["records"]:
            for act in r.get("activities") or [{"activity": None, "start": None, "instrument": []}]:
                at = act["start"].earliest if act["start"] else None
                for instrument in act["instrument"] or [None]:
                    attested = (calibration_status(wm, world, instrument, at, as_of, perspective)
                                if instrument is not None and at is not None else None)
                    rows.append({"record": r["record"], "attestation": m["attestation"],
                                 "acceptance": m["acceptance"], "usable": m["usable"], "activity": act["activity"],
                                 "at": at, "instrument": instrument, "stated_reference": r.get("calibration"),
                                 "attested": attested,
                                 "reference_check": _reference_check(r.get("calibration"), instrument,
                                                                     attested or {"certificates": []})})
    return sorted(rows, key=lambda x: (x["record"], x["instrument"] or ""))


# ---- interpretations ---------------------------------------------------------------------------------------------------
def interpret(wm, world, record, type, roles, attester, tentative=False, polarity=True, params=None, **attest):
    """Record a source's interpretation of a result record: content (type, roles) attested by `attester`, resting on
    the record. tentative True: a hypothesis (stance `hypothesises`: kept, never supporting an answer); otherwise the
    source's testimony. Basis `inference` is refused here (D-D3-4): it is reserved for attestations derived under a
    named rule from named premises, which the model does not yet record (Stage E, DI-7)."""
    _require(wm)
    if attest.get("basis") == "inference":
        raise ValueError("an interpretation by a source is testimony or a hypothesis; basis 'inference' is reserved "
                         "for rule-derived attestations (D-D3-4)")
    if tentative:
        attest["stance"] = "hypothesises"
    attest.setdefault("basis", "testimony")
    return wm.attest(world, type, roles, params=params, polarity=polarity, attester=attester,
                     evidence=[lambda tx: record], **_until(attest))


def interpretations(wm, world, record, t, as_of=None, perspective=SYSTEM):
    """Every attestation resting on `record` (rests-on; any content, including the measurement it reports), each
    with its source, stance, basis and acceptance, a plain `mode` (hypothesis, doubt, testimony, observation,
    stipulation, or recorded inference without derivation structure), `supports_answer` (whether the content's
    judgement at t rests on this attestation: accepted is not enough, since its stance must support, its interval
    must apply at t and it must not be superseded; a hypothesis never does), and its content's own judgement at t
    (which other sources' attestations of the same content can establish). Each
    content is judged on its own: rival interpretations are not judged against each other (D-D3-6). `derivation` is
    always the NO_DERIVATION note: no attestation here carries a named rule and premises."""
    _require(wm)
    with wm._reading() as tx:
        aids = sorted({q.opt(r, "aid") for r in q.rows(tx, """match $r isa information-object, has wm-id == $id;
            rests-on (attestation: $a, record: $r); $a has wm-id $aid;""", {"id": record})})
    out = []
    for aid in aids:
        a = wm._attestation(aid)
        if a["is_event"]:
            continue
        content = wm.content(a["content"])
        subject = next(ids[0] for ids in content["roles"].values() if ids)
        entry = next((e for e in wm._claims(world, subject, (content["type"],), t, as_of, perspective)
                      if any(x["attestation"] == aid for x in e["attestations"])), None)
        if entry is None:
            continue                                   # not visible in this world or at this knowledge time
        mine = next(x for x in entry["attestations"] if x["attestation"] == aid)
        mode = ("hypothesis" if a["stance"] == "hypothesises" else "doubt" if a["stance"] == "doubts"
                else MODES[a["basis"]])
        judged = wm._judgement(entry)
        out.append({"attestation": aid, "attester": a["attester"], "type": content["type"], "roles": content["roles"],
                    "params": content.get("params") or {}, "polarity": a["polarity"], "stance": a["stance"],
                    "basis": a["basis"], "mode": mode, "acceptance": mine["acceptance"],
                    "supports_answer": aid in entry["support"],
                    "content_judgement": {k: judged[k] for k in ("judgement", "holds", "status")},
                    "derivation": NO_DERIVATION})
    return sorted(out, key=lambda x: (x["type"], str(x["roles"]), x["attestation"]))
