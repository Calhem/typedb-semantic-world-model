"""Core 0.4 Stage C2 (LABS-1.016): capabilities, contextual roles and agency. Mixed into WorldModel.

Plan 9.5 (DX-3) and World Ontology v0.2 §3.1:
- a capability (`capability` concept: can-weigh) and a role (`social-role` concept: analyst) are held through
  classified-as(holder, concept, context?) over an attested interval; a contextual one applies only in its context, a
  general one (no context) everywhere;
- agency is the category `agent`, held the same way: an entity can be an agent without a given capability, and have a
  capability (a balance can weigh) without being an agent;
- roles occupied within a particular event are its participant roles (actor, instrument...).
Classification never proves that an action was possible or performed: check_action() reports the account, the
occurrence's own status, the actor's agency and the capability separately, and concludes nothing beyond them. No
planning or prediction.
"""

from .semantics import Status

SYSTEM = "system"
AGENT = "agent"


class AgencyMixin:
    def define_capability(self, name, id=None):
        return self.add_entity("capability", name, id=id)

    def grant(self, world, holder, concept, context=None, polarity=True, **attest):
        """Attest that `holder` holds the capability, role or category `concept` (optionally only in `context`), from
        `start` to `end` or until superseded. polarity False: a denial (revocation is an ended or superseded grant)."""
        roles = {"classified": holder, "class": concept}
        if context is not None:
            roles["context"] = context
        if "end" not in attest:
            attest.setdefault("until_superseded", True)
        return self.attest(world, "classified-as", roles, polarity=polarity, **attest)

    def _holding_label(self, entry):
        """One content's judgement for the perspective: accepted, denied, expired (an accepted holding whose interval
        ended, with no accepted denial), disputed, not yet effective, or an attestation state (unreviewed...)."""
        label = self._verdict_label(entry)
        if label == "denied" and all(x["polarity"] for x in entry["attestations"] if x["acceptance"] == "accepted"):
            label = "expired"
        return label

    def _judgement(self, entry):
        """One content's judgement (a _claims entry) in the capable() vocabulary, with its evidence: the shared
        per-content report of the profiles (organisation, LABS-1.026; laboratory, LABS-1.028)."""
        label = self._holding_label(entry)
        holds, status, judgement = self._combine([{"judgement": label, "status": entry["status"]}], True)
        return {"judgement": judgement, "holds": holds, "status": status, "evidence": entry["attestations"],
                "_label": label}

    @staticmethod
    def _combine(applicable, any_found):
        """(holds, status, judgement) for a set of applicable holdings, each {"judgement", "status"} (LABS-1.019 cases;
        shared by capable() and the organisation profile's reports, LABS-1.026). any_found: whether anything at all was
        found (UNKNOWN rather than NOT_YET_KNOWN when nothing applies)."""
        labels = {h["judgement"] for h in applicable}
        if "disputed" in labels or {"accepted", "denied"} <= labels:
            holds, status = None, Status.DISPUTED
        elif "accepted" in labels:
            holds = True
            status = next(h["status"] for h in applicable if h["judgement"] == "accepted")
        elif labels & {"denied", "expired"}:
            holds = False                        # denied, or an accepted holding that has ended (as in holds())
            status = next(h["status"] for h in applicable if h["judgement"] in ("denied", "expired"))
        else:
            holds, status = None, Status.UNKNOWN if any_found else Status.NOT_YET_KNOWN
        judgement = ("disputed" if status == Status.DISPUTED else "established" if holds else
                     ("denied" if "denied" in labels else "expired") if holds is False else
                     "not yet effective" if "not yet effective" in labels else "not established")
        return holds, status, judgement

    def _holdings(self, world, holder, concept, t, as_of, perspective, types=("classified-as",)):
        """Every classified-as content (or of `types`) of `holder` under `concept`, with its context and the
        perspective's judgement."""
        out = []
        for e in self._claims(world, holder, types, t, as_of, perspective):
            if holder in e["roles"].get("classified", []) and concept in e["roles"].get("class", []):
                ctx = e["roles"].get("context", [None])[0]
                out.append({"context": ctx, "judgement": self._holding_label(e), "status": e["status"],
                            "attestations": e["attestations"]})
        return sorted(out, key=lambda x: (x["context"] or "", x["judgement"]))

    def capable(self, world, holder, capability, t, context=None, as_of=None, perspective=SYSTEM):
        """Does `holder` hold `capability` at t, in `context` (or in general when context is None)? A general holding
        (no context) applies in every context; a contextual one only in its own. Holdings that apply only in other
        contexts are listed in `only_in`; every applicable holding is listed with its evidence in `applicable`.

        holds and status are the core judgement (no new statuses); `judgement` names the case (LABS-1.019):
          established        holds True    an applicable holding is accepted at t
          denied             holds False   an accepted denial (polarity false) covers t
          expired            holds False   an accepted holding ended before t (no denial), as holds() treats any end
          not yet effective  holds None    an accepted holding begins after t
          disputed           holds None    DISPUTED: accepted grant and denial, or rival accepted attestations
          not established    holds None    nothing applicable is accepted (none at all, unreviewed or rejected ones,
                                           or holdings only in other contexts)
        A capability never establishes an action, and an action never establishes a capability."""
        found = self._holdings(world, holder, capability, t, as_of, perspective)
        applicable = [h for h in found if h["context"] is None or h["context"] == context]
        holds, status, judgement = self._combine(applicable, bool(found))
        return {"holder": holder, "capability": capability, "context": context, "holds": holds, "status": status,
                "judgement": judgement,
                "applicable": applicable,
                "only_in": sorted({h["context"] for h in found if h["context"] not in (None, context)
                                   and h["judgement"] == "accepted"})}

    def is_agent(self, world, x, t, as_of=None, perspective=SYSTEM):
        """Whether `x` is accepted as an agent at t (classified-as(x, agent)); agency is a classification."""
        return self.capable(world, x, AGENT, t, None, as_of, perspective)

    def roles_of(self, world, holder, t, as_of=None, perspective=SYSTEM):
        """The social roles `holder` is accepted as holding at t, each with its context."""
        from . import typeql as q
        from .model import READ
        out = []
        for f in self.facts_about(world, holder, t, as_of, perspective):
            if not self.is_a(f["type"], "classified-as") or holder not in f["roles"].get("classified", []):
                continue
            for c in f["roles"].get("class", []):
                with self._reading() as tx:
                    if q.rows(tx, "match $c isa social-role, has wm-id == $id;", {"id": c}):
                        out.append({"role": c, "context": f["roles"].get("context", [None])[0],
                                    "status": f["status"], "support": f["support"]})
        return sorted(out, key=lambda r: (r["role"], r["context"] or ""))

    def check_action(self, world, event, capability=None, context=None, as_of=None, perspective=SYSTEM):
        """A structured check of an event description as an action, for the perspective. Reports separately: whether
        its account is accepted (and its occurrence interval), its kinds (is it classified `action`), the occurrences
        it is accepted as describing and their own status, and for each actor whether it is accepted as an agent and
        (if `capability` is given) whether it held the capability in `context` when the event started. It does not
        conclude that the action was possible or performed: an accepted agent classification and a capability are
        not evidence that the event happened, and an accepted account is not an established occurrence."""
        span = self.interval(world, event, as_of, perspective)
        kinds = sorted({k for e in self.events(world, as_of=as_of, perspective=perspective) if e["event"] == event
                        for k in e["kinds"]})
        content = self.content(event) or {"roles": {}}
        at = span[0].earliest if span and span[0] else None
        occs = self.occurrences_of(world, event, as_of, perspective)
        actors = []
        for actor in content["roles"].get("actor", []):
            entry = {"actor": actor, "agent": None, "capability": None}
            if at is not None:
                entry["agent"] = self.is_agent(world, actor, at, as_of, perspective)
                if capability:
                    entry["capability"] = self.capable(world, actor, capability, at, context, as_of, perspective)
            actors.append(entry)
        return {"event": event, "account": "accepted" if span else "not accepted",
                "start": span[0] if span else None, "end": span[1] if span else None,
                "kinds": kinds, "classified_action": "action" in kinds,
                "occurrences": [{"occurrence": o, "status": self.occurrence_status(world, o, at, as_of, perspective,
                                                                                   details=False)["status"]}
                                for o in occs] if at is not None else [{"occurrence": o, "status": None} for o in occs],
                "participants": content["roles"], "actors": actors, "capability": capability, "context": context}

    def agency_report(self, world, as_of=None, perspective=SYSTEM):
        """Diagnostic (DX-5, report mode): sources of attestations in `world` that the perspective does not accept as
        agents at the time they recorded them. Nothing is rejected or changed; Core 0.3 behaviour is unaffected."""
        atts = self.visible(world, as_of, perspective)
        by = {}
        for a in atts.values():
            if a.attester != SYSTEM:
                by.setdefault(a.attester, []).append(a)
        out = []
        for who, recs in sorted(by.items()):
            first = min(a.recorded_at for a in recs)
            agent = self.is_agent(world, who, first, as_of, perspective)
            if agent["holds"] is not True:
                out.append({"attester": who, "attestations": len(recs), "agent": agent["status"],
                            "first_recorded": first})
        return out
