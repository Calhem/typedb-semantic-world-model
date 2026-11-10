"""Core 0.4 Stage B (LABS-1.010): dynamics and causality on the v0.2 core. Mixed into WorldModel.

Four distinctions are kept explicit (v0.2 §3.2, plan 9.3):
- an **occurrence** (something that happens: an id only) vs an **event description** (a source's account of it, with
  participants and, on its attestation, an interval); `describes` links them, as a judgement usable per perspective;
- an **asserted effect** (`initiates` / `terminates` claims about a description) vs an **accepted world-state change**
  (the outcome proposition's own attestations, judged before and after the event);
- **temporal succession** (intervals compared with certainly_before) vs **causation** (`causes` claims, asserted by a
  source, never inferred from order or transitively);
- a **source's account** (attestations, each with attester and basis) vs a **perspective's judgement** (acceptance,
  supersession, world and knowledge time).

Writing goes through the ordinary attestation path. Reading uses the core's loading and judgement, so selective and
full-load answers are the same.
"""

from datetime import timedelta

from .semantics import Status, acceptance_state, certainly_before, superseded, usable

SYSTEM = "system"
EPS = timedelta(microseconds=1)


class DynamicsMixin:
    # ---- writing ---------------------------------------------------------------------------------------------------
    def account(self, world, roles, start, end=None, kind=None, occurrence=None, attester=SYSTEM, id=None,
                type="event", **attest):
        """A source's account of a happening: an event description with its participants, attested by `attester`
        over [start, end] (an instant when end is None), optionally classified (`kind`: a category or list) and
        linked to an `occurrence` by a describes claim of the same source. Returns the description id."""
        eid = self.describe_event(roles, id=id, type=type)
        self.attest(world, event=eid, start=start, end=end or start, attester=attester, **attest)
        for k in ([kind] if isinstance(kind, str) else kind or []):
            self.attest(world, "classified-as", {"classified": eid, "class": k}, until_superseded=True,
                        attester=attester)
        if occurrence is not None:
            self.describe_occurrence(world, eid, occurrence, attester=attester)
        return eid

    def describe_occurrence(self, world, description, occurrence, **attest):
        """Claim that an event description describes an occurrence (an identity judgement, usable per perspective)."""
        attest.setdefault("until_superseded", True)
        return self.attest(world, "describes", {"description": description, "occurrence": occurrence}, **attest)

    def claim_effect(self, world, event, kind, type, roles, params=None, polarity=True, **attest):
        """Claim that the event description initiated or terminated (`kind`) the proposition (type, roles, params).
        This is an asserted effect: it says nothing about whether the state actually changed, which is judged from
        the proposition's own attestations. Returns the claim's attestation id."""
        if kind not in ("initiates", "terminates"):
            raise ValueError("kind is 'initiates' or 'terminates'")
        if not self.has_proposition_ids():
            raise ValueError("effects need proposition ids (the core-0.4-a0 module)")
        pid = self.proposition_id(self.proposition(type, roles, params))
        attest.setdefault("until_superseded", True)
        return self.attest(world, kind, {"event": event, "outcome": pid}, polarity=polarity, **attest)

    # ---- reading: helpers ------------------------------------------------------------------------------------------
    def _proposition_by_id(self, pid):
        """{type, roles, params, key} of a stored proposition, by its A0.1 id."""
        from . import typeql as q
        from .model import READ
        with self.driver.transaction(self.database, READ) as tx:
            rows = q.rows(tx, "match $p isa proposition, has wm-id == $id, has proposition-key $k;", {"id": pid})
        if not rows:
            return None
        key = q.opt(rows[0], "k")
        return {**self.content(key), "key": key}

    def interval(self, world, description, as_of=None, perspective=SYSTEM):
        """The occurrence interval given by an attestation of the description that the perspective can use (start
        Window, end Window, record), or None. An unaccepted account's times are never used for a judgement."""
        recs = [a for a in self._load(world, as_of, types=["event"], perspective=perspective).values()
                if a.content == description and a.polarity and usable(a, perspective, as_of)]
        recs.sort(key=lambda a: a.id)
        return (recs[0].start, recs[0].end, recs[0]) if recs else None

    def account_attestations(self, world, description, attester=None, as_of=None):
        """Ids of the attestations that make up an account: of the description itself (its occurrence interval), and
        of its classifications and describes links, optionally only those by `attester` (e.g. to accept them)."""
        out = [a.id for a in self._load(world, as_of, types=["event"]).values() if a.content == description
               and (attester is None or a.attester == attester)]
        out += [h["attestation"] for h in self.history(world, description, as_of=as_of)
                if h["type"] in ("classified-as", "describes") and (attester is None or h["attester"] == attester)]
        return sorted(out)

    def _claims(self, world, subject, types, t, as_of, perspective):
        """Every attestation of a content of `types` involving `subject`, grouped by content, with the perspective's
        judgement of the content at t and each attestation's acceptance state (accepted, unreviewed, rejected,
        retracted, superseded). Nothing is dropped: unaccepted and rejected claims are listed, marked."""
        atts, ident = self._view(world, as_of, perspective, None, [subject])
        mine = [a for a in atts.values() if any(self.is_a(a.ctype, ty) for ty in types)
                and any(subject in ids for ids in a.roles.values())]
        judged = self._judge(mine, ident, t, perspective, as_of)
        out = {}
        for a in mine:
            cls = self._class(a, ident)
            entry = out.setdefault(cls, {"type": a.ctype, "roles": {r: list(v) for r, v in a.roles.items()},
                                         "judged": None, "status": None, "attestations": []})
            state = "superseded" if superseded(a, perspective, as_of) else acceptance_state(a, perspective, as_of)
            entry["attestations"].append({"attestation": a.id, "attester": a.attester, "polarity": a.polarity,
                                          "basis": a.basis, "stance": a.stance, "acceptance": state})
        for cls, entry in out.items():
            if cls in judged:
                val, support, _ = judged[cls]
                entry["judged"] = val
                entry["status"] = Status.DISPUTED if val == "disputed" else self._status(support)
            entry["attestations"].sort(key=lambda x: x["attestation"])
        return sorted(out.values(), key=lambda e: (e["type"], str(e["roles"])))

    @staticmethod
    def _status(support):
        from .semantics import answer_status
        return answer_status(support)

    @staticmethod
    def _verdict_label(entry):
        """accepted / denied / disputed (the perspective's judgement) or the best attestation state when unjudged."""
        if entry["judged"] is True:
            return "accepted"
        if entry["judged"] is False:
            return "denied"
        if entry["judged"] == "disputed":
            return "disputed"
        states = {x["acceptance"] for x in entry["attestations"]}
        return next(s for s in ("unreviewed", "rejected", "retracted", "superseded") if s in states) \
            if states else "unknown"

    # ---- reading: effects and changes (B1) --------------------------------------------------------------------------
    def effects_of(self, world, event, t, as_of=None, perspective=SYSTEM):
        """The effects claimed for an event description: for each initiates / terminates claim, who claims it and the
        perspective's judgement of the claim (accepted, unreviewed, rejected, denied, disputed), and separately the
        judged state of the outcome just before the event starts and when it ends: the accepted world-state change.
        A claim can be accepted while the state change is not (and the reverse); neither implies the other."""
        span = self.interval(world, event, as_of, perspective)
        out = []
        for entry in self._claims(world, event, ("initiates", "terminates"), t, as_of, perspective):
            if event not in entry["roles"].get("event", []):
                continue
            pid = entry["roles"]["outcome"][0]
            outcome = self._proposition_by_id(pid)
            change = None
            if span is not None and span[0] is not None:
                before = self.holds(world, outcome["type"], outcome["roles"], span[0].earliest - EPS, as_of, perspective)
                after = self.holds(world, outcome["type"], outcome["roles"], (span[1] or span[0]).latest, as_of,
                                   perspective)
                kind = self.core_type(entry["type"])
                changed = (before.holds is not True and after.holds is True) if kind == "initiates" else \
                    (before.holds is True and after.holds is not True)
                change = {"before": before, "after": after, "accepted_change": changed}
            out.append({"kind": self.core_type(entry["type"]), "outcome_id": pid,
                        "outcome": {k: outcome[k] for k in ("type", "roles", "params")},
                        "claim": self._verdict_label(entry), "claim_status": entry["status"],
                        "claimed_by": sorted({x["attester"] for x in entry["attestations"]}),
                        "attestations": entry["attestations"], "state": change})
        return out

    def changes(self, world, subject, t1, t2, as_of=None, perspective=SYSTEM):
        """What changed about `subject` between t1 and t2, for the perspective: contents that hold at t2 but not at
        t1 (began) and at t1 but not at t2 (ended), each with the sources of the state, and the events claimed to
        have initiated or terminated it (with each claim's judgement). Accepted state is the answer; claimed events
        are explanations, never the reason a state counts as changed."""
        def key(f):
            return f["type"], tuple(sorted((r, tuple(v)) for r, v in f["roles"].items())), tuple(sorted(f["params"].items()))

        before = {key(f): f for f in self.facts_about(world, subject, t1, as_of, perspective)}
        after = {key(f): f for f in self.facts_about(world, subject, t2, as_of, perspective)}
        hist = {h["attestation"]: h for h in self.history(world, subject, as_of=as_of, perspective=perspective)}

        def entry(f, kind):
            content = f["type"], {r: v for r, v in f["roles"].items()}
            pid = self.proposition_id(self._key_of(f))
            return {"type": f["type"], "roles": f["roles"], "params": f["params"], "status": f["status"],
                    "stated_by": sorted({hist[a]["attester"] for a in f["support"] if a in hist}),
                    "support": f["support"], "outcome_id": pid,
                    "claimed_events": self._events_claiming(world, pid, kind, t2, as_of, perspective) if pid else [],
                    "content": content}

        began = [entry(f, "initiates") for k, f in sorted(after.items()) if k not in before]
        ended = [entry(f, "terminates") for k, f in sorted(before.items()) if k not in after]
        return {"subject": subject, "from": t1, "to": t2, "began": began, "ended": ended,
                "unchanged": len(set(before) & set(after))}

    def _key_of(self, fact):
        from .keys import proposition_key
        return proposition_key(fact["type"], fact["roles"], fact["params"] or None)

    def _events_claiming(self, world, pid, kind, t, as_of, perspective):
        """Event descriptions claimed to have initiated / terminated the proposition `pid`, with claim judgements and
        the occurrences each description is accepted as describing."""
        out = []
        for entry in self._claims(world, pid, (kind,), t, as_of, perspective):
            if pid not in entry["roles"].get("outcome", []):
                continue
            for ev in entry["roles"].get("event", []):
                span = self.interval(world, ev, as_of, perspective)
                out.append({"event": ev, "claim": self._verdict_label(entry), "claim_status": entry["status"],
                            "claimed_by": sorted({x["attester"] for x in entry["attestations"]}),
                            "start": span[0] if span else None, "end": span[1] if span else None,
                            "occurrences": self.occurrences_of(world, ev, as_of, perspective)})
        return out

    def occurrences_of(self, world, description, as_of=None, perspective=SYSTEM):
        """The occurrences a description is accepted (by the perspective) as describing."""
        links = self._load(world, as_of, types=["describes"], subjects=[description], perspective=perspective)
        return sorted({o for a in links.values() if a.polarity and usable(a, perspective, as_of)
                       and description in a.roles.get("description", []) for o in a.roles.get("occurrence", [])})

    def before(self, world, a, b, as_of=None, perspective=SYSTEM):
        """Temporal succession of two descriptions: True if a certainly ends before b starts, False if b certainly
        before a, None if they overlap or cannot be ordered. Succession says nothing about causation."""
        ia, ib = self.interval(world, a, as_of, perspective), self.interval(world, b, as_of, perspective)
        if not ia or not ib:
            return None
        if certainly_before(ia[2], ib[2]):
            return True
        if certainly_before(ib[2], ia[2]):
            return False
        return None

    # ---- writing and reading: causation, processes, actions (B2) -----------------------------------------------------
    def claim_cause(self, world, cause, effect, polarity=True, **attest):
        """A source's claim that `cause` caused `effect` (event descriptions or occurrences, in any mix), or with
        polarity False a denial. Timeless content; its acceptance is per perspective. Never inferred by the model."""
        if cause == effect:
            raise ValueError("a happening does not cause itself")
        attest.setdefault("until_superseded", True)
        return self.attest(world, "causes", {"cause": cause, "effect": effect}, polarity=polarity, **attest)

    def _kind_of_id(self, i):
        from .model import READ
        with self.driver.transaction(self.database, READ) as tx:
            return self._kinds_of(tx, [i])[i]

    def occurrence_status(self, world, occurrence, t, as_of=None, perspective=SYSTEM):
        """Whether the occurrence happened, for the perspective (LABS-1.011): judged only from attestations of its own
        existence (existence(existent: occurrence)), never from accepted descriptions, describes links or causal
        claims. `status` is accepted, denied, disputed or "not established". Each description that some source links
        to it is reported separately: its source, whether the perspective accepts the account (the description's own
        attestation) and the describes link. An accepted account of a denied occurrence is representable and reported
        as such."""
        existence = [e for e in self._claims(world, occurrence, ("existence",), t, as_of, perspective)
                     if occurrence in e["roles"].get("existent", [])]
        verdicts = {self._verdict_label(e) for e in existence}
        status = ("disputed" if "disputed" in verdicts or {"accepted", "denied"} <= verdicts else
                  "accepted" if "accepted" in verdicts else "denied" if "denied" in verdicts else "not established")
        events = [a for a in self._load(world, as_of, types=["event"], perspective=perspective).values()]
        descs = []
        for link in self._claims(world, occurrence, ("describes",), t, as_of, perspective):
            if occurrence not in link["roles"].get("occurrence", []):
                continue
            for d in link["roles"].get("description", []):
                recs = [a for a in events if a.content == d]
                account = ("accepted" if any(a.polarity and usable(a, perspective, as_of) for a in recs) else
                           "unreviewed" if any(acceptance_state(a, perspective, as_of) == "unreviewed" for a in recs)
                           else "rejected" if recs else "none")
                descs.append({"description": d, "account": account,
                              "account_by": sorted({a.attester for a in recs}),
                              "describes": self._verdict_label(link),
                              "describes_by": sorted({x["attester"] for x in link["attestations"]})})
        return {"occurrence": occurrence, "status": status,
                "existence": [{"judgement": self._verdict_label(e), "status": e["status"],
                               "attestations": e["attestations"]} for e in existence],
                "descriptions": sorted(descs, key=lambda x: x["description"])}

    def causes_of(self, world, effect, t, as_of=None, perspective=SYSTEM):
        """Every causal claim about what caused `effect` (an occurrence or an event description), judged for the
        perspective. Claims stated about the effect itself are direct; claims stated about another description of the
        same happening (or about the occurrence a description describes) are lifted, but only through describes links
        the perspective accepts, and they keep their own provenance (plan 9.3). Each claim is reported with its level
        (description / occurrence / mixed), the occurrences its cause is accepted as, its judgement (accepted,
        disputed, denied, unreviewed, rejected) and its sources. Nothing is inferred from order or chained.

        Occurrence check (LABS-1.011): each claim also reports the status (occurrence_status) of every occurrence it
        involves, and `applies`: False when one of them is denied, None when one is disputed, True otherwise. A claim
        about a denied occurrence stays visible as its source's account (its own judgement is unchanged), but it does
        not answer what caused the happening, and a lifted claim never makes a denied occurrence accepted."""
        occurrence = self.is_a(self._kind_of_id(effect), "occurrence")
        statuses = {}

        def status_of(o):
            if o not in statuses:
                statuses[o] = self.occurrence_status(world, o, t, as_of, perspective)["status"]
            return statuses[o]
        lifted = (self.descriptions(world, effect, as_of, perspective) if occurrence
                  else self.occurrences_of(world, effect, as_of, perspective))
        out, seen = [], set()
        for target in [effect, *lifted]:
            for entry in self._claims(world, target, ("causes",), t, as_of, perspective):
                if target not in entry["roles"].get("effect", []):
                    continue
                cause = entry["roles"]["cause"][0]
                if (cause, target) in seen:
                    continue
                seen.add((cause, target))
                cause_is_occ = self.is_a(self._kind_of_id(cause), "occurrence")
                effect_is_occ = self.is_a(self._kind_of_id(target), "occurrence")
                level = ("occurrence" if cause_is_occ and effect_is_occ else
                         "description" if not cause_is_occ and not effect_is_occ else "mixed")
                cause_occs = [cause] if cause_is_occ else self.occurrences_of(world, cause, as_of, perspective)
                effect_occs = [target] if effect_is_occ else self.occurrences_of(world, target, as_of, perspective)
                involved = {o: status_of(o) for o in sorted(set(cause_occs) | set(effect_occs))}
                applies = (False if "denied" in involved.values() else None if "disputed" in involved.values()
                           else True)
                out.append({"cause": cause, "effect": target, "level": level, "lifted": target != effect,
                            "occurrences": involved, "applies": applies,
                            "lifted_via": None if target == effect else
                            ({"description": target, "occurrence": effect} if occurrence
                             else {"description": effect, "occurrence": target}),
                            "cause_occurrences": cause_occs,
                            "judgement": self._verdict_label(entry), "status": entry["status"],
                            "claimed_by": sorted({x["attester"] for x in entry["attestations"]}),
                            "attestations": entry["attestations"]})
        order = {"accepted": 0, "disputed": 1, "denied": 2, "unreviewed": 3, "rejected": 4, "retracted": 5}
        return sorted(out, key=lambda c: (order.get(c["judgement"], 9), c["cause"], c["effect"]))

    def explain(self, world, type, roles, t, as_of=None, perspective=SYSTEM):
        """Why does a content hold at t? The judged answer; the events claimed to have initiated it that ended by t,
        with each claim's judgement; and for each such event, the causal claims about it (causes_of, on its
        description and on the occurrences it is accepted as describing). An explanation is only what was asserted
        and accepted: earlier events without causal claims are not causes."""
        from .keys import proposition_key
        answer = self.holds(world, type, roles, t, as_of, perspective)
        pid = self.proposition_id(proposition_key(type, roles))
        initiators = []
        for ev in (self._events_claiming(world, pid, "initiates", t, as_of, perspective) if pid else []):
            if ev["end"] is None or ev["end"].latest > t:
                continue
            causes, seen = [], set()
            for subject in [ev["event"], *ev["occurrences"]]:
                for c in self.causes_of(world, subject, t, as_of, perspective):
                    if (c["cause"], c["effect"]) not in seen:
                        seen.add((c["cause"], c["effect"]))
                        causes.append(c)
            initiators.append({**ev, "causes": causes})
        return {"content": {"type": type, "roles": roles}, "holds": answer, "initiated_by": initiators}

    def process_steps(self, world, process, t, as_of=None, perspective=SYSTEM):
        """The occurrences accepted as part of a process occurrence at t, ordered by their descriptions' intervals,
        each with its descriptions, interval, kinds and actors (from the perspective's accepted descriptions)."""
        kinds = {e["event"]: e for e in self.events(world, as_of=as_of, perspective=perspective)}
        steps = []
        for f in self.facts_about(world, process, t, as_of, perspective):
            if f["type"] != "part-of" or process not in f["roles"].get("whole", []):
                continue
            for occ in f["roles"]["part"]:
                descs = self.descriptions(world, occ, as_of, perspective)
                spans = [self.interval(world, d, as_of, perspective) for d in descs]
                span = min((s for s in spans if s and s[0]), key=lambda s: s[0].earliest, default=None)
                steps.append({"occurrence": occ, "descriptions": descs, "start": span[0] if span else None,
                              "end": span[1] if span else None,
                              "kinds": sorted({k for d in descs if d in kinds for k in kinds[d]["kinds"]}),
                              "actors": sorted({x for d in descs if d in kinds for x in kinds[d]["roles"].get("actor", [])}),
                              "support": f["support"]})
        far = max((s["start"].earliest for s in steps if s["start"]), default=None)
        return sorted(steps, key=lambda s: (s["start"].earliest if s["start"] else far, s["occurrence"]))

    def actions_of(self, world, agent, as_of=None, perspective=SYSTEM):
        """Event descriptions in which `agent` is the actor and that are classified as actions, for the perspective.
        (v0.2 also requires the actor's agent capacity; capacities are Stage C, so this lists the classification.)"""
        return [{"event": e["event"], "kinds": e["kinds"], "start": e["start"], "end": e["end"],
                 "occurrences": self.occurrences_of(world, e["event"], as_of, perspective), "attester": e["attester"]}
                for e in self.events(world, participant=agent, as_of=as_of, perspective=perspective)
                if "action" in e["kinds"] and agent in e["roles"].get("actor", [])]
