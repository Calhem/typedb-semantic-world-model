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
        """The occurrence interval a description's usable attestation gives (start Window, end Window), or None."""
        recs = [a for a in self._load(world, as_of, types=["event"], perspective=perspective).values()
                if a.content == description]
        recs.sort(key=lambda a: (not usable(a, perspective, as_of), a.id))
        return (recs[0].start, recs[0].end, recs[0]) if recs else None

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
