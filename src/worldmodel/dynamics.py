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

from .operations import atomic
from .judgement import Judgement, claim_label
from .semantics import Status, acceptance_state, answer_status, certainly_before, superseded, usable

SYSTEM = "system"
EPS = timedelta(microseconds=1)


class _Memo:
    """World-wide loads reused within one question (LABS-1.012): the event attestations (for intervals and accounts)
    and the describes links (for occurrences_of), each loaded at most once for one world, knowledge time and
    perspective. Created by a read operation and passed down; it never outlives the question, so nothing is cached
    across writes.

    `descriptions` (O-3, LABS-1.057) scopes `events()` to those event descriptions: their attestations are loaded by
    content id (with the same world, knowledge-time and perspective rules) instead of every event in the world. A
    scoped memo answers only for those descriptions, so it is created only by a reader that knows its descriptions
    beforehand (`occurrence()`)."""

    def __init__(self, wm, world, as_of, perspective, descriptions=None):
        self.wm, self.world, self.as_of, self.perspective = wm, world, as_of, perspective
        self._events = self._occurrences = None
        self._scope = None if descriptions is None else sorted(set(descriptions))

    def events(self):
        """{description id: [attestation records of it]} for every event description visible in the world (or, when
        scoped, for each of the memo's descriptions that is visible)."""
        if self._events is None:
            self._events = {}
            scope = {} if self._scope is None else {"contents": self._scope}    # unscoped: the call as before O-3
            for a in self.wm._load(self.world, self.as_of, types=["event"], perspective=self.perspective,
                                   **scope).values():
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


def account_state(recs, perspective, as_of):
    """A description's account for the perspective, in occurrence_status's vocabulary: accepted, unreviewed, rejected
    (any other decision against it), or none (no attestation of it in the world)."""
    return ("accepted" if any(a.polarity and usable(a, perspective, as_of) for a in recs) else
            "unreviewed" if any(acceptance_state(a, perspective, as_of) == "unreviewed" for a in recs)
            else "rejected" if recs else "none")


class DynamicsMixin:
    # ---- writing ---------------------------------------------------------------------------------------------------
    @atomic
    def account(self, world, roles, start, end=None, kind=None, occurrence=None, attester=SYSTEM, id=None,
                type="event", **attest):
        """A source's account of a happening: an event description with its participants, attested by `attester`
        over [start, end] (an instant when end is None), optionally classified (`kind`: a category or list) and
        linked to an `occurrence` by a describes claim of the same source. Returns the description id."""
        batch = attest.get("batch")              # measure(): one transaction for the whole measurement
        eid = self.describe_event(roles, id=id, type=type, batch=batch)
        self.attest(world, event=eid, start=start, end=end or start, attester=attester, **attest)
        for k in ([kind] if isinstance(kind, str) else kind or []):
            self.attest(world, "classified-as", {"classified": eid, "class": k}, until_superseded=True,
                        attester=attester, batch=batch)
        if occurrence is not None:
            self.describe_occurrence(world, eid, occurrence, attester=attester, batch=batch)
        return eid

    def describe_occurrence(self, world, description, occurrence, **attest):
        """Claim that an event description describes an occurrence (an identity judgement, usable per perspective)."""
        attest.setdefault("until_superseded", True)
        return self.attest(world, "describes", {"description": description, "occurrence": occurrence}, **attest)

    @atomic
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
        with self._reading() as tx:
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
                if self.is_a_any(h["type"], ("classified-as", "describes"))
                and (attester is None or h["attester"] == attester)]
        return sorted(out)

    # ---- reading: effects and changes (B1) --------------------------------------------------------------------------
    def effects_of(self, world, event, t, as_of=None, perspective=SYSTEM):
        """The effects claimed for an event description: for each initiates / terminates claim, who claims it and the
        perspective's judgement of the claim (accepted, unreviewed, rejected, denied, disputed), and separately the
        judged state of the outcome just before the event starts and when it ends: the accepted world-state change.
        A claim can be accepted while the state change is not (and the reverse); neither implies the other."""
        span = self.interval(world, event, as_of, perspective)
        out = []
        for entry in self._contents(world, event, ("initiates", "terminates"), t, as_of, perspective):
            if not entry.about("event"):
                continue
            pid = entry.stated_roles["outcome"][0]
            outcome = self._proposition_by_id(pid)
            change = None
            if span is not None and span[0] is not None:
                before = self.holds(world, outcome["type"], outcome["roles"], span[0].earliest - EPS, as_of, perspective)
                after = self.holds(world, outcome["type"], outcome["roles"], (span[1] or span[0]).latest, as_of,
                                   perspective)
                kind = self.core_type(entry.type)
                changed = (before.holds is not True and after.holds is True) if kind == "initiates" else \
                    (before.holds is True and after.holds is not True)
                change = {"before": before, "after": after, "accepted_change": changed}
            out.append({"kind": self.core_type(entry.type), "outcome_id": pid,
                        "outcome": {k: outcome[k] for k in ("type", "roles", "params")},
                        "claim": claim_label(entry), "claim_status": entry.status,
                        "claimed_by": sorted({x["attester"] for x in entry.claims()}),
                        "attestations": entry.claims(), "state": change})
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
        slot_rivals += self._scope_rivals(world, as_of, perspective, recs + slot_rivals, ident,
                                          pool=None if self.selective else atts)   # attested constraints
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

        memo_c = {}

        def state_at(s):
            judged = self._judge(recs + slot_rivals, ident, s, perspective, as_of)
            holding = [c for c, (val, _, _) in judged.items() if val is True]
            conf = self._conflicts(holding)
            # the canonical constraint layer: an established attested constraint (e.g. an exclusive office) too
            for c, cs in self._attested_conflicts(world, holding, ident, s, as_of, perspective, memo_c).items():
                for x in cs:
                    if x.rivals:
                        conf.setdefault(c, set()).update(x.rivals)
            out = {}
            for key, info in tracks.items():
                classes = [c for c in member if key in member[c] and c in judged]
                held = {c for c in classes if judged[c][0] is True}
                support = sorted({a.id for c in classes if judged[c][0] in (True, "disputed") for a in judged[c][1]})
                rivals = sorted({a.id for c in classes for r in conf.get(c, ()) for a in judged[r][1]})
                disputed = any(judged[c][0] == "disputed" or c in conf for c in classes)
                # a slot's status: the core rule over the support of the values held, as value_of (increment C,
                # C-6); an accepted denial of another value is not support for the value held
                sup = [a for c in classes if judged[c][0] is True for a in judged[c][1]]
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

        def timing(ev, early, late):
            """The approved Stage B causal rule (LABS-1.016): an event cannot explain a transition that certainly
            precedes the start of its occurrence. Occurrence time is the event's accepted occurrence interval (valid
            time), never the time its account was recorded. None: excluded (the transition is certainly earlier);
            "consistent": the occurrence certainly started by the transition's earliest time; "unresolved": the
            occurrence time is unavailable or overlaps the transition window, so applicability is reported, not
            rejected."""
            if ev["start"] is None:
                return "unresolved"
            if late < ev["start"].earliest:
                return None
            return "consistent" if ev["start"].latest <= early else "unresolved"

        activations = {}
        for n, (key, before, after, early, late, cat) in enumerate(found):
            for cls in after[2] - before[2]:
                activations.setdefault((cls, "initiates"), []).append((n, early, late))
            for cls in before[2] - after[2]:
                activations.setdefault((cls, "terminates"), []).append((n, early, late))
        # Claims are looked up only for contents that change in a returned transition; attribution still counts every
        # activation of the content on the whole timeline.
        returned = {n for n, (key, before, after, early, late, cat) in enumerate(found) if not (late <= t1 or early > t2)}
        explained = {}
        for (cls, kind), acts in activations.items():
            if not any(n in returned for n, _, _ in acts):
                continue
            for ev in claims_for(cls, kind):
                fits = {n: timing(ev, early, late) for n, early, late in acts}
                fits = {n: tm for n, tm in fits.items() if tm is not None}
                for n, tm in fits.items():
                    explained.setdefault(n, []).append({
                        "event": ev["event"], "effect": kind, "content": {"type": cls[0], "roles": dict(cls[1])},
                        "class": cls, "claim": ev["claim"], "claim_status": ev["claim_status"],
                        "claimed_by": ev["claimed_by"], "start": ev["start"], "end": ev["end"],
                        "occurrences": ev["occurrences"], "attribution": "unique" if len(fits) == 1 else "ambiguous",
                        "timing": tm})

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
        for entry in self._contents(world, pid, (kind,), t, as_of, perspective):
            if not entry.about("outcome"):
                continue
            for ev in entry.stated_roles.get("event", []):
                span = self.interval(world, ev, as_of, perspective, _memo=memo)
                out.append({"event": ev, "claim": claim_label(entry), "claim_status": entry.status,
                            "claimed_by": sorted({x["attester"] for x in entry.claims()}),
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
        with self._reading() as tx:
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
        existence = [e for e in self._contents(world, occurrence, ("existence",), t, as_of, perspective)
                     if e.about("existent")]
        memo = _memo or _Memo(self, world, as_of, perspective)
        descs = []
        for link in self._contents(world, occurrence, ("describes",), t, as_of, perspective):
            if not link.about("occurrence"):
                continue
            for d in link.stated_roles.get("description", []):
                recs = memo.events().get(d, [])
                account = account_state(recs, perspective, as_of)
                descs.append({"description": d, "account": account,
                              "account_by": sorted({a.attester for a in recs}),
                              "describes": claim_label(link),
                              "describes_by": sorted({x["attester"] for x in link.claims()})})
        return {"occurrence": occurrence, "status": status, "answer": answer,
                "existence": [{"judgement": claim_label(e), "status": e.status,
                               "attestations": e.claims()} for e in existence],
                "descriptions": sorted(descs, key=lambda x: x["description"])}

    # ---- event roles (LABS-1.043, DI-2: ER-1 to ER-5) -------------------------------------------------------------------
    def _event_roles(self, world, occurrence, memo, as_of=None, perspective=SYSTEM, ident=None, links=None):
        """(accounts, roles) for `occurrence()`. Every description linked to the occurrence (or to anything the
        perspective's identity makes the same occurrence) by a visible describes claim is an account, accepted or not.
        Its link is judged by the canonical record of the describes content at the start of the account (the time it
        is about); its account state is occurrence_status's. Compared accounts (ER-3): link ESTABLISHED and account
        accepted. For each event-role constraint of a compared account's type (ER-1), with its kind's classification
        of the occurrence judged by the canonical record at the occurrence's start (ER-2), the role is judged by rule Q
        (ER-4) over the compared accounts of the nearest world, players under the perspective's identity. Roles are
        keyed by stored role label, with the core role alongside (ER-5).

        Multiplicity (LABS-1.049, DI-13, MP-2/MP-3): each compared account gives a *set* of players. Under a `one`
        declaration the role is DISPUTED when more than one player is named, with `reason` "several players in one
        account" and/or "accounts name different players"; under `set` it is established when every compared account
        names the same set, otherwise DISPUTED ("accounts name different sets of players", each account's set in
        `sets`). For one event type and role, an applicable kind-scoped declaration overrides an unconditional one,
        which is listed with applies False and why."""
        from . import typeql as q
        ident = ident or self.identity(world, as_of, perspective, ids=[occurrence])
        members = set(ident.members(occurrence))
        if links is None:   # occurrence() passes the same load (O-3)
            links = self._load(world, as_of, types=["describes"], subjects=sorted(members), perspective=perspective)
        linked = sorted({d for a in links.values() if members & set(a.roles.get("occurrence", []))
                         for d in a.roles.get("description", [])})
        events = memo.events()
        accounts = []
        with self._reading() as tx:
            for d in linked:
                recs = events.get(d, [])
                use = [a for a in recs if a.polarity and usable(a, perspective, as_of)]
                starts = [a.start.earliest for a in (use or recs) if a.start is not None]
                roles, etype = {}, None
                for r in q.rows(tx, """match $e isa! $t, has wm-id == $id; $e links ($role: $x); $x has wm-id $xid;""",
                                {"id": d}):
                    etype = r.get("t").get_label()
                    label = r.get("role").get_label()
                    roles.setdefault(label, (self.core_role(label), set()))[1].add(q.opt(r, "xid"))
                accounts.append({"description": d, "type": etype or (recs[0].ctype if recs else None),
                                 "attesters": sorted({a.attester for a in recs}),
                                 "account": account_state(recs, perspective, as_of),
                                 "depth": min(a.depth for a in use) if use else None,
                                 "_use": use, "_start": min(starts) if starts else None,
                                 "_roles": {k: (c, sorted(v)) for k, (c, v) in roles.items()}})
        # links: the canonical record of describes(description, occurrence), at the start of each account
        records = {}
        for t in sorted({x["_start"] for x in accounts if x["_start"] is not None}):
            for rec in self._contents(world, occurrence, ("describes",), t, as_of, perspective):
                if members & set(rec.stated_roles.get("occurrence", [])):
                    for d in rec.stated_roles.get("description", []):
                        records.setdefault((d, t), rec)
        for x in accounts:
            rec = records.get((x["description"], x["_start"]))
            x["describes"] = claim_label(rec) if rec is not None else None      # None: no account time to judge it at
            x["describes_by"] = sorted({c["attester"] for c in rec.claims()}) if rec is not None else []
            x["_compared"] = (rec is not None and rec.judgement is Judgement.ESTABLISHED
                              and x["account"] == "accepted")
        compared = [x for x in accounts if x["_compared"]]
        starts = [x["_start"] for x in compared if x["_start"] is not None]
        at = min(starts) if starts else None
        players = sorted({p for x in accounts for _, ids in x["_roles"].values() for p in ids})
        pid = self.identity(world, as_of, perspective, ids=players) if players else ident
        scopes = {}
        for x in compared:
            for decl, role, kind, module, mult in self._event_constraints(x["type"]):
                scopes.setdefault((decl, role, kind), (module, mult))
        judged = []
        for (decl, role, kind), (module, mult) in sorted(scopes.items(),
                                                         key=lambda i: (i[0][0], i[0][1], i[0][2] or "")):
            group = [x for x in compared if self.is_a(x["type"], decl)
                     and any(c == role for c, _ in x["_roles"].values())]
            entry = {"event_type": decl, "role": role, "kind": kind, "declared_by": module, "applies": True,
                     "why": "declared for the event type", "classification": None, "judgement": None, "status": None,
                     "support": [], "players": [], "overridden": [], "multiplicity": mult, "reason": None,
                     "sets": None, "_group": group,
                     "_labels": sorted({lab for x in group for lab, (c, _) in x["_roles"].items() if c == role})}
            if kind is not None:
                rec = self.judgement(world, "classified-as", {"classified": occurrence, "class": kind}, at, as_of,
                                     perspective)
                entry["classification"] = {"at": at, "judgement": rec.judgement.value, "reasons": list(rec.reasons),
                                           "support": rec.support_ids}
                if rec.judgement is Judgement.ESTABLISHED:
                    entry["why"] = f"the occurrence is established as {kind} at its start"
                else:
                    entry.update(applies=False, why=f"the occurrence is not established as {kind} at its start "
                                                    f"({rec.judgement.value}): the role is a union")
            judged.append(entry)
        # MP-3: for one event type and role, an applicable kind-scoped declaration wins over an unconditional one
        winning = {}
        for e in judged:
            if e["kind"] is not None and e["applies"]:
                winning.setdefault((e["event_type"], e["role"]), []).append(e["kind"])
        for e in judged:
            kinds = winning.get((e["event_type"], e["role"]))
            if e["kind"] is None and e["applies"] and kinds:
                e.update(applies=False, why=f"overridden by the declaration for {', '.join(sorted(kinds))}, which "
                                            f"applies to the occurrence (MP-3)")
        applying = {(e["event_type"], e["role"]) for e in judged if e["applies"]}
        for e in judged:      # a kind-scoped declaration that does not apply, while another one does: not a union
            if e["kind"] is not None and not e["applies"] and (e["event_type"], e["role"]) in applying:
                e["why"] = (f"the occurrence is not established as {e['kind']} at its start "
                            f"({e['classification']['judgement']}): this declaration does not apply")
        for entry in judged:
            group, role = entry["_group"], entry["role"]
            if not (entry["applies"] and group):
                continue
            depth = min(x["depth"] for x in group)
            near = [x for x in group if x["depth"] == depth]
            entry["overridden"] = sorted(x["description"] for x in group if x["depth"] != depth)
            by, sets = {}, []
            for x in near:
                mine = set()
                for c, ids in x["_roles"].values():
                    if c != role:
                        continue
                    for p in ids:
                        mine.add(pid.canonical(p))
                        g = by.setdefault(pid.canonical(p), {"names": set(), "accounts": set(), "recs": {}})
                        g["names"].add(p)
                        g["accounts"].add((x["description"], tuple(sorted({a.attester for a in x["_use"]}))))
                        g["recs"].update({a.id: a for a in x["_use"]})
                sets.append((x, frozenset(mine)))
            entry["players"] = [{"names": sorted(g["names"]),
                                 "accounts": [{"description": d, "attesters": list(w)}
                                              for d, w in sorted(g["accounts"])],
                                 "status": answer_status(g["recs"].values())}
                                for _, g in sorted(by.items())]
            recs = {i: a for g in by.values() for i, a in g["recs"].items()}
            # MP-2: each compared account gives a set of players, under the perspective's identity
            if entry["multiplicity"] == "set":
                entry["sets"] = [{"description": x["description"], "attesters": sorted({a.attester for a in x["_use"]}),
                                  "players": sorted(mine)} for x, mine in sorted(sets, key=lambda i: i[0]["description"])]
                if len({mine for _, mine in sets}) == 1:
                    entry.update(judgement="established", status=answer_status(recs.values()), support=sorted(recs))
                else:
                    entry.update(judgement="disputed", status=Status.DISPUTED, support=[],
                                 reason="accounts name different sets of players")
            elif len(by) > 1:
                reasons = []
                if any(len(mine) > 1 for _, mine in sets):
                    reasons.append("several players in one account")
                if len({mine for _, mine in sets}) > 1:
                    reasons.append("accounts name different players")
                entry.update(judgement="disputed", status=Status.DISPUTED, support=[], reason="; ".join(reasons))
            else:
                entry.update(judgement="established", status=answer_status(recs.values()), support=sorted(recs))
        roles = {}
        for x in accounts:
            for label, (core, ids) in x["_roles"].items():
                e = roles.setdefault(label, {"name": label.split(":")[-1], "core_role": core, "players": {}})
                for p in ids:
                    e["players"].setdefault(p, []).append(x["description"])
        for label, e in roles.items():
            e["players"] = {p: sorted(ds) for p, ds in sorted(e["players"].items())}
            e["constraints"] = [{k: v for k, v in j.items() if not k.startswith("_")}
                                for j in judged if label in j["_labels"]]
            e["resolved"] = self._resolved_role(label, judged, accounts, pid)
        public = [{"description": x["description"], "type": x["type"], "attesters": x["attesters"],
                   "describes": x["describes"], "describes_by": x["describes_by"], "account": x["account"],
                   "depth": x["depth"],
                   "roles": {lab: {"name": lab.split(":")[-1], "core_role": c, "players": ids}
                             for lab, (c, ids) in sorted(x["_roles"].items())}}
                  for x in accounts]
        return public, dict(sorted(roles.items()))

    @staticmethod
    def _resolved_role(label, judged, accounts, pid):
        """The resolved role-player set of one stored role label (LABS-1.052, R1 of
        docs/stage-e/e1-reconciliation-design.md): MP-2's players, from the compared accounts only (accepted, describes
        link established, nearest world), beside ER-5's complete listing in `players`. `judgement`: `established` (an
        applying constraint holds), `disputed` (an applying constraint is violated: no player is resolved; the rival
        candidates stay in `constraints`), `union` (no constraint applies: the compared accounts' players, grouped
        under the perspective's identity; nothing is concluded beyond what those accounts state) or `none` (no
        compared account names the role). Never resolved: a player named only by an account that is not compared, or
        only by a farther world's account. Resolving says nothing about whether the occurrence happened
        (occurrence_status) or whether an account's other claims hold."""
        naming = [x for x in accounts if label in x["_roles"]]
        compared = [x for x in naming if x["_compared"]]
        depth = min((x["depth"] for x in compared), default=None)
        near = [x for x in compared if x["depth"] == depth]
        out = {"judgement": "none", "players": [], "compared": sorted(x["description"] for x in near),
               "overridden": sorted(x["description"] for x in compared if x["depth"] != depth),
               "not_compared": [{"description": x["description"],
                                 "why": (f"account {x['account']}" if x["account"] != "accepted"
                                         else f"describes {x['describes']}")}
                                for x in sorted(naming, key=lambda x: x["description"]) if not x["_compared"]],
               "constraint": None, "support": []}
        applying = [j for j in judged if j["applies"] and label in j["_labels"] and j["judgement"] is not None]
        if applying:
            j = next((j for j in applying if j["judgement"] == "disputed"), applying[0])
            out["constraint"] = {k: j[k] for k in ("event_type", "role", "kind", "multiplicity")}
            if j["judgement"] == "disputed":
                out["judgement"] = "disputed"
            else:
                out.update(judgement="established", players=j["players"], support=list(j["support"]))
            return out
        if not near:
            return out
        groups = {}
        for x in near:
            for p in x["_roles"][label][1]:
                g = groups.setdefault(pid.canonical(p), {"names": set(), "accounts": set(), "recs": {}})
                g["names"].add(p)
                g["accounts"].add((x["description"], tuple(sorted({a.attester for a in x["_use"]}))))
                g["recs"].update({a.id: a for a in x["_use"]})
        out.update(judgement="union",
                   players=[{"names": sorted(g["names"]),
                             "accounts": [{"description": d, "attesters": list(w)} for d, w in sorted(g["accounts"])],
                             "status": answer_status(g["recs"].values())} for _, g in sorted(groups.items())],
                   support=sorted({i for g in groups.values() for i in g["recs"]}))
        return out

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
            for entry in self._contents(world, target, ("causes",), t, as_of, perspective):
                if not entry.about("effect"):
                    continue
                cause = entry.stated_roles["cause"][0]
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
                            "judgement": claim_label(entry), "status": entry.status,
                            "claimed_by": sorted({x["attester"] for x in entry.claims()}),
                            "attestations": entry.claims()})
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
        each with its descriptions, interval, kinds and actors (from the perspective's accepted descriptions), and the
        judgement and status of its part-of content: established, or disputed (DI-1: listed, never dropped)."""
        kinds = {e["event"]: e for e in self.events(world, as_of=as_of, perspective=perspective)}
        steps = []
        for f in self.facts_about(world, process, t, as_of, perspective):
            if not self.is_a(f["type"], "part-of") or process not in f["roles"].get("whole", []):
                continue
            for occ in f["roles"]["part"]:
                descs = self.descriptions(world, occ, as_of, perspective)
                spans = [self.interval(world, d, as_of, perspective) for d in descs]
                span = min((s for s in spans if s and s[0]), key=lambda s: s[0].earliest, default=None)
                steps.append({"occurrence": occ, "descriptions": descs, "start": span[0] if span else None,
                              "end": span[1] if span else None,
                              "kinds": sorted({k for d in descs if d in kinds for k in kinds[d]["kinds"]}),
                              "actors": sorted({x for d in descs if d in kinds for x in kinds[d]["roles"].get("actor", [])}),
                              "support": f["support"], "judgement": f["judgement"], "status": f["status"]})
        far = max((s["start"].earliest for s in steps if s["start"]), default=None)
        return sorted(steps, key=lambda s: (s["start"].earliest if s["start"] else far, s["occurrence"]))

    def actions_of(self, world, agent, as_of=None, perspective=SYSTEM):
        """Event descriptions in which `agent` is the actor and that are classified as actions, for the perspective.
        (v0.2 also requires the actor's agent capacity; capacities are Stage C, so this lists the classification.)"""
        return [{"event": e["event"], "kinds": e["kinds"], "start": e["start"], "end": e["end"],
                 "occurrences": self.occurrences_of(world, e["event"], as_of, perspective), "attester": e["attester"]}
                for e in self.events(world, participant=agent, as_of=as_of, perspective=perspective)
                if "action" in e["kinds"] and agent in e["roles"].get("actor", [])]
