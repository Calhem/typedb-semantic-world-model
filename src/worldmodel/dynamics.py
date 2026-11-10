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


class _Memo:
    """World-wide loads reused within one question (LABS-1.012): the event attestations (for intervals and accounts)
    and the describes links (for occurrences_of), each loaded at most once for one world, knowledge time and
    perspective. Created by a read operation and passed down; it never outlives the question, so nothing is cached
    across writes."""

    def __init__(self, wm, world, as_of, perspective):
        self.wm, self.world, self.as_of, self.perspective = wm, world, as_of, perspective
        self._events = self._occurrences = None

    def events(self):
        """{description id: [attestation records of it]} for every event description visible in the world."""
        if self._events is None:
            self._events = {}
            for a in self.wm._load(self.world, self.as_of, types=["event"], perspective=self.perspective).values():
                self._events.setdefault(a.content, []).append(a)
        return self._events

    def occurrences(self, description):
        """The occurrences the description is accepted (by the perspective) as describing."""
        if self._occurrences is None:
            self._occurrences = {}
            links = self.wm._load(self.world, self.as_of, types=["describes"], perspective=self.perspective)
            for a in links.values():
                if a.polarity and usable(a, self.perspective, self.as_of):
                    for d in a.roles.get("description", []):
                        self._occurrences.setdefault(d, set()).update(a.roles.get("occurrence", []))
        return sorted(self._occurrences.get(description, ()))


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

    def interval(self, world, description, as_of=None, perspective=SYSTEM, _memo=None):
        """The occurrence interval given by an attestation of the description that the perspective can use (start
        Window, end Window, record), or None. An unaccepted account's times are never used for a judgement."""
        found = (_memo.events().get(description, []) if _memo else
                 [a for a in self._load(world, as_of, types=["event"], perspective=perspective).values()
                  if a.content == description])
        recs = [a for a in found if a.polarity and usable(a, perspective, as_of)]
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
        """State transitions of `subject` whose valid time intersects (t1, t2], judged for the world, perspective and
        knowledge time (LABS-1.015 contract).

        The subject's records are loaded once. Every start and end bound of their windows is a boundary; the judged
        state is constant between boundaries, so judging at each boundary gives the whole timeline (no extra queries).
        Tracks: each functional slot whose key includes the subject (values judged as in value_at, conflicts
        included), and each other content involving the subject (holds / does not hold / UNKNOWN / DISPUTED).
        - category "world-state": between two accepted states; "judgement": into or out of UNKNOWN or DISPUTED, never
          presented as proof of physical change. Accepted A, then only UNKNOWN, then accepted B != A is one world-state
          transition whose window is the UNKNOWN gap: the instant is never invented.
        - window [earliest, latest] and `within`: "certain" if inside (t1, t2], "possible" if it overlaps it;
          transitions outside are not returned.
        - explanations: only accepted initiates / terminates claims about a content that began / ended in the
          transition, and only if the event did not certainly start after the transition. A claim that fits several
          activations of the same content is listed on each as "ambiguous"; never chosen, never inferred from
          proximity. `began` / `ended` are views over the returned transitions."""
        from .keys import proposition_id
        from .model import PARAMS_VALUE
        from .semantics import answer_status
        atts, ident = self._view(world, as_of, perspective, None, [subject])
        me = set(ident.members(subject))
        mine = {ident.canonical(x) for x in me}
        recs = [a for a in atts.values() if a.kind not in ("event", "same-as") and any(me & set(ids) for ids in
                                                                                     a.roles.values())]
        slot_rivals = self._slot_rivals(world, as_of, perspective, recs, me, ident,
                                   pool=None if self.selective else atts)          # Q-B2: slot rivals
        attester = {a.id: a.attester for a in recs}
        contents = {}
        for a in recs:
            contents.setdefault(self._class(a, ident), set()).add(a.content)
        tracks, member = {}, {}
        for cls in contents:
            players = dict(cls[1])
            keys_ = []
            for decl, ks, v in self._constraints(cls[0]):
                if any(mine & set(players.get(r, ())) for r in ks):
                    key = ("slot", decl, ks, v, tuple(players.get(r) for r in ks))
                    tracks[key] = {"kind": "slot", "type": decl, "key": {r: list(players.get(r, ())) for r in ks},
                                   "value_role": v}
                    keys_.append(key)
            if not keys_:
                key = ("content", cls)
                tracks[key] = {"kind": "content", "type": cls[0], "roles": {r: list(i) for r, i in cls[1]},
                               "params": dict(cls[2])}
                keys_.append(key)
            member[cls] = keys_
        bounds = sorted({x for a in recs + slot_rivals for w in (a.start, a.end) if w is not None
                         for x in (w.earliest, w.latest) if x is not None})
        samples = ([bounds[0] - EPS] if bounds else []) + bounds

        def state_at(s):
            judged = self._judge(recs + slot_rivals, ident, s, perspective, as_of)
            conf = self._conflicts([c for c, (val, _, _) in judged.items() if val is True])
            out = {}
            for key, info in tracks.items():
                classes = [c for c in member if key in member[c] and c in judged]
                held = {c for c in classes if judged[c][0] is True}
                support = sorted({a.id for c in classes if judged[c][0] in (True, "disputed") for a in judged[c][1]})
                rivals = sorted({a.id for c in classes for r in conf.get(c, ()) for a in judged[r][1]})
                disputed = any(judged[c][0] == "disputed" or c in conf for c in classes)
                sup = [a for c in classes if judged[c][0] in (True, False) for a in judged[c][1]]
                if info["kind"] == "slot":
                    v = info["value_role"]
                    values = sorted((dict(c[2]) if v == PARAMS_VALUE else list(dict(c[1]).get(v, ())))
                                    for c in classes if judged[c][0] in (True, "disputed"))
                    values = [x for i, x in enumerate(values) if x not in values[:i]]
                    status = Status.DISPUTED if disputed else answer_status(sup) if values else Status.UNKNOWN
                    sig = ("disputed" if disputed else "accepted" if values else "unknown", str(values))
                    state = {"status": status, "values": values}
                else:
                    c = key[1]
                    val = judged[c][0] if c in judged else None
                    holds = None if disputed or val is None else val
                    status = (Status.DISPUTED if disputed else Status.UNKNOWN if val is None else
                              answer_status(judged[c][1]))
                    sig = ("disputed" if disputed else "unknown" if val is None else "accepted", holds)
                    state = {"status": status, "holds": holds}
                out[key] = (sig, {**state, "support": support, "conflicts": rivals}, held)
            return out

        timeline = [(s, state_at(s)) for s in samples]
        found = []                                          # every transition on the whole timeline
        for key, info in tracks.items():
            segs = []
            for s, st in timeline:
                if not segs or segs[-1][1][0] != st[key][0]:
                    segs.append((s, st[key]))
            i = 0
            while i + 1 < len(segs):
                prev, nxt = segs[i], segs[i + 1]
                if prev[1][0][0] == "accepted" and nxt[1][0][0] == "unknown":
                    j = i + 1
                    while j < len(segs) and segs[j][1][0][0] == "unknown":
                        j += 1
                    if j < len(segs) and segs[j][1][0][0] == "accepted" and segs[j][1][0] != prev[1][0]:
                        found.append((key, prev[1], segs[j][1], nxt[0], segs[j][0], "world-state"))
                        i = j
                        continue
                cat = "world-state" if prev[1][0][0] == nxt[1][0][0] == "accepted" else "judgement"
                found.append((key, prev[1], nxt[1], nxt[0], nxt[0], cat))
                i += 1
        # explanations: accepted effect claims, attributed only to compatible activations of the claimed content
        memo = _Memo(self, world, as_of, perspective)
        claims = {}

        def claims_for(cls, kind):
            if (cls, kind) not in claims:
                claims[(cls, kind)] = [e for k in sorted(contents[cls]) for e in self._events_claiming(
                    world, proposition_id(k), kind, t2, as_of, perspective, memo) if e["claim"] == "accepted"]
            return claims[(cls, kind)]

        def compatible(ev, latest):
            return ev["start"] is None or ev["start"].earliest <= latest

        activations = {}
        for n, (key, before, after, early, late, cat) in enumerate(found):
            for cls in after[2] - before[2]:
                activations.setdefault((cls, "initiates"), []).append((n, late))
            for cls in before[2] - after[2]:
                activations.setdefault((cls, "terminates"), []).append((n, late))
        explained = {}
        for (cls, kind), acts in activations.items():
            for ev in claims_for(cls, kind):
                fits = [n for n, late in acts if compatible(ev, late)]
                for n in fits:
                    explained.setdefault(n, []).append({
                        "event": ev["event"], "effect": kind, "content": {"type": cls[0], "roles": dict(cls[1])},
                        "class": cls, "claim": ev["claim"], "claim_status": ev["claim_status"],
                        "claimed_by": ev["claimed_by"], "start": ev["start"], "end": ev["end"],
                        "occurrences": ev["occurrences"], "attribution": "unique" if len(fits) == 1 else "ambiguous"})

        def describe(cls):
            return {"type": cls[0], "roles": {r: list(i) for r, i in cls[1]}, "params": dict(cls[2])}

        transitions, began, ended = [], [], []
        for n, (key, before, after, early, late, cat) in enumerate(found):
            if late <= t1 or early > t2:
                continue
            within = "certain" if early > t1 and late <= t2 else "possible"
            exps = sorted(explained.get(n, []), key=lambda e: (e["effect"], e["event"]))
            tr = {"track": tracks[key], "category": cat, "before": before[1], "after": after[1],
                  "window": (early, late), "within": within,
                  "began": [describe(c) for c in sorted(after[2] - before[2])],
                  "ended": [describe(c) for c in sorted(before[2] - after[2])],
                  "explanations": [{k: v for k, v in e.items() if k != "class"} for e in exps]}
            transitions.append(tr)
            for kind, side, lst in (("initiates", after, began), ("terminates", before, ended)):
                changed = (after[2] - before[2]) if kind == "initiates" else (before[2] - after[2])
                for cls in sorted(changed):
                    sup = [i for i in side[1]["support"]]
                    lst.append({**describe(cls), "status": side[1]["status"],
                                "stated_by": sorted({attester[i] for i in sup if i in attester}),
                                "support": sup, "outcome_id": proposition_id(sorted(contents[cls])[0]),
                                "category": cat, "within": within, "window": (early, late),
                                "claimed_events": [{k: v for k, v in e.items() if k not in ("class", "content")}
                                                   for e in exps if e["class"] == cls and e["effect"] == kind],
                                "content": (cls[0], {r: list(i) for r, i in cls[1]})})
        transitions.sort(key=lambda x: (x["window"][0], x["window"][1], str(x["track"])))
        moved = {str(tr["track"]) for tr in transitions}
        return {"subject": subject, "from": t1, "to": t2,
                "context": {"world": world, "perspective": perspective, "as_of": as_of},
                "transitions": transitions, "began": began, "ended": ended,
                "unchanged": sum(1 for info in tracks.values() if str(info) not in moved)}

    def _key_of(self, fact):
        from .keys import proposition_key
        return proposition_key(fact["type"], fact["roles"], fact["params"] or None)

    def _events_claiming(self, world, pid, kind, t, as_of, perspective, _memo=None):
        """Event descriptions claimed to have initiated / terminated the proposition `pid`, with claim judgements and
        the occurrences each description is accepted as describing."""
        memo = _memo or _Memo(self, world, as_of, perspective)
        out = []
        for entry in self._claims(world, pid, (kind,), t, as_of, perspective):
            if pid not in entry["roles"].get("outcome", []):
                continue
            for ev in entry["roles"].get("event", []):
                span = self.interval(world, ev, as_of, perspective, _memo=memo)
                out.append({"event": ev, "claim": self._verdict_label(entry), "claim_status": entry["status"],
                            "claimed_by": sorted({x["attester"] for x in entry["attestations"]}),
                            "start": span[0] if span else None, "end": span[1] if span else None,
                            "occurrences": self.occurrences_of(world, ev, as_of, perspective, _memo=memo)})
        return out

    def occurrences_of(self, world, description, as_of=None, perspective=SYSTEM, _memo=None):
        """The occurrences a description is accepted (by the perspective) as describing."""
        if _memo is not None:
            return _memo.occurrences(description)
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

    def occurrence_status(self, world, occurrence, t, as_of=None, perspective=SYSTEM, details=True, _memo=None):
        """Whether the occurrence happened, for the perspective (LABS-1.011): judged only from attestations of its own
        existence (existence(existent: occurrence)), never from accepted descriptions, describes links or causal
        claims. `status` is accepted, denied, disputed or "not established". Each description that some source links
        to it is reported separately: its source, whether the perspective accepts the account (the description's own
        attestation) and the describes link. An accepted account of a denied occurrence is representable and reported
        as such."""
        # One judgement for both APIs (LABS-1.012): the status is read from exists(), which judges an occurrence only
        # from its own existence attestations.
        answer = self.exists(world, occurrence, t, as_of, perspective)
        status = ("disputed" if answer.status == Status.DISPUTED else "accepted" if answer.holds is True else
                  "denied" if answer.holds is False else "not established")
        if not details:
            return {"occurrence": occurrence, "status": status, "answer": answer}
        existence = [e for e in self._claims(world, occurrence, ("existence",), t, as_of, perspective)
                     if occurrence in e["roles"].get("existent", [])]
        memo = _memo or _Memo(self, world, as_of, perspective)
        descs = []
        for link in self._claims(world, occurrence, ("describes",), t, as_of, perspective):
            if occurrence not in link["roles"].get("occurrence", []):
                continue
            for d in link["roles"].get("description", []):
                recs = memo.events().get(d, [])
                account = ("accepted" if any(a.polarity and usable(a, perspective, as_of) for a in recs) else
                           "unreviewed" if any(acceptance_state(a, perspective, as_of) == "unreviewed" for a in recs)
                           else "rejected" if recs else "none")
                descs.append({"description": d, "account": account,
                              "account_by": sorted({a.attester for a in recs}),
                              "describes": self._verdict_label(link),
                              "describes_by": sorted({x["attester"] for x in link["attestations"]})})
        return {"occurrence": occurrence, "status": status, "answer": answer,
                "existence": [{"judgement": self._verdict_label(e), "status": e["status"],
                               "attestations": e["attestations"]} for e in existence],
                "descriptions": sorted(descs, key=lambda x: x["description"])}

    def causes_of(self, world, effect, t, as_of=None, perspective=SYSTEM, _memo=None):
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
        memo = _memo or _Memo(self, world, as_of, perspective)
        statuses = {}

        def status_of(o):
            if o not in statuses:
                statuses[o] = self.occurrence_status(world, o, t, as_of, perspective, details=False)["status"]
            return statuses[o]
        lifted = (self.descriptions(world, effect, as_of, perspective) if occurrence
                  else self.occurrences_of(world, effect, as_of, perspective, _memo=memo))
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
                cause_occs = [cause] if cause_is_occ else self.occurrences_of(world, cause, as_of, perspective, _memo=memo)
                effect_occs = [target] if effect_is_occ else self.occurrences_of(world, target, as_of, perspective,
                                                                                 _memo=memo)
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
        memo = _Memo(self, world, as_of, perspective)            # events and describes loaded once (LABS-1.012)
        initiators = []
        for ev in (self._events_claiming(world, pid, "initiates", t, as_of, perspective, memo) if pid else []):
            if ev["end"] is None or ev["end"].latest > t:
                continue
            causes, seen = [], set()
            for subject in [ev["event"], *ev["occurrences"]]:
                for c in self.causes_of(world, subject, t, as_of, perspective, _memo=memo):
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
