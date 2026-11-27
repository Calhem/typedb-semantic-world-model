"""Stage E2 harness: evidence extraction by role (H-4, H-5; LABS-1.063).

Each extractor implements part 6 (Evidence) of its reader's contract (benchmark/e2/spec/reader-contracts.md), as
approved under LABS-1.063, and returns the attestation ids of a normalised answer by role:
- `supporting`: what the answer rests on for the value, status or judgement it gives;
- `conflicting`: the other side of a dispute. Conflicting evidence may legitimately establish a DISPUTED judgement.
  The positive claims of mutually exclusive rival values keep their conflicting relationship; polarity alone does not
  decide a role (P-VA-1, P-OH-1 as qualified);
- `alternative`: listed but not rested on (unaccepted, superseded, incomparable, unverified, statements beside
  measurements);
- `undetermined`: listed where the contract's role depends on an unresolved semantic decision. It is scored in no role,
  and questions depending on it are blocked (check.py, H-8).

**Components and cross-role membership (LABS-1.063 supplement, finding 4).** Every extracted id is recorded with the
answer component it came from (an answer path such as `appointments[2]`, `conflict`, `candidates[0]`), so an
attestation may legitimately serve different roles in different components or plan steps. For example, an established
holder's appointment supports that appointment, and the same claims conflict with the rival holder in the office
conflict (P-OH-1 as qualified). Scoring deduplicates per role: an id counts once in each role it holds, wherever it
appears. The one forbidden combination is an id listed as an alternative and as supporting **in the same component**:
score.py reports that as `alternative-as-support`, so extraction never hides an incorrectly presented alternative.

**No permissive defaults (finding 3).** A candidate, chain or search counts as verified only when the answer says
`verified: true`. A missing flag is unverified.
"""

ROLES = ("supporting", "conflicting", "alternative", "undetermined")
USABLE = "accepted"


def _ids(v):
    return {x for x in (v or []) if isinstance(x, str)}


class Ev(dict):
    """{role: set of ids}, plus `entries`: every (component, role, id) as extracted."""

    def __init__(self):
        super().__init__({r: set() for r in ROLES})
        self.entries = set()
        self.component = "answer"

    def at(self, component):
        self.component = component
        return self

    def add(self, role, ids):
        found = {ids} if isinstance(ids, str) else _ids(ids)
        self[role] |= found
        self.entries |= {(self.component, role, i) for i in found}
        return self


def _polarity(answer):
    return {e["attestation"]: e.get("polarity") for e in answer.get("evidence") or [] if "attestation" in e}


def answer_roles(a, ev=None, component="answer"):
    """An Answer (holds, and the Answers inside other readers) under the HO table: support supporting, except in a
    DISPUTED answer, where the accepted denials of a polarity dispute are conflicting; conflicts and the applied
    constraint's support are conflicting; alternatives are alternatives."""
    ev = (ev if ev is not None else Ev()).at(component)
    if not a:
        return ev
    pol = _polarity(a)
    support = _ids(a.get("support"))
    if a.get("status") == "DISPUTED":
        ev.add("supporting", {s for s in support if pol.get(s) is not False})
        ev.add("conflicting", {s for s in support if pol.get(s) is False})
    else:
        ev.add("supporting", support)
    ev.add("conflicting", a.get("conflicts"))
    for c in a.get("constraint_support") or []:
        ev.add("conflicting", c.get("support"))
    ev.add("alternative", a.get("alternatives"))
    return ev


def ev_holds(a):
    return answer_roles(a)


def ev_value_at(a):
    """VA, P-VA-1 as qualified: in a dispute between several values, every value's positive claims are conflicting
    (mutually exclusive rivals); a single polarity-disputed value splits by polarity; otherwise support is supporting."""
    ev = Ev()
    pol = _polarity(a)
    support = _ids(a.get("support"))
    if a.get("status") == "DISPUTED" and len(a.get("values") or []) > 1:
        ev.add("conflicting", support)
    elif a.get("status") == "DISPUTED":
        ev.add("supporting", {s for s in support if pol.get(s) is not False})
        ev.add("conflicting", {s for s in support if pol.get(s) is False})
    else:
        ev.add("supporting", support)
    return ev.add("alternative", a.get("alternatives"))


def ev_facts_about(entries):
    ev = Ev()
    for n, e in enumerate(entries):
        ev.at(f"[{n}]")
        if e.get("judgement") == "established":
            ev.add("supporting", e.get("support"))
        else:
            ev.add("supporting", e.get("assertions"))
            ev.add("conflicting", e.get("denials"))
            ev.add("conflicting", e.get("conflicts"))
    return ev


def ev_occurrence(view):
    ev = Ev()
    for label, role in (view.get("roles") or {}).items():
        ev.at(f"roles[{label}]")
        res = role.get("resolved") or {}
        if res.get("judgement") in ("established", "union"):
            ev.add("supporting", res.get("support"))
        ev.add("alternative", res.get("not_compared"))
        ev.add("alternative", res.get("overridden"))
        for c in role.get("constraints") or []:
            if not c.get("applies"):
                continue
            if c.get("judgement") == "established":
                ev.add("supporting", c.get("support"))
                ev.add("supporting", (c.get("classification") or {}).get("support"))
            elif c.get("judgement") == "disputed":
                ev.add("conflicting", {a.get("description") for g in c.get("players") or []
                                       for a in g.get("accounts") or []})
    return ev


def ev_occurrence_status(r):
    ev = Ev()
    a = r.get("answer") or {}
    pol = _polarity(a)
    support = _ids(a.get("support"))
    if r.get("status") == "disputed":
        ev.add("supporting", {s for s in support if pol.get(s) is not False})
        ev.add("conflicting", {s for s in support if pol.get(s) is False})
    elif r.get("status") in ("accepted", "denied"):
        ev.add("supporting", support)
    return ev.add("alternative", a.get("alternatives"))


def _claim_entries(entries):
    return [e for e in entries or [] if isinstance(e, dict) and "attestation" in e]


def ev_office_holders(r):
    """OH, P-OH-1 as qualified (finding 2): an established appointment's accepted claims support that appointment, always,
    conflict or not. In a conflict, the same holders' claims are also conflicting with each other in the `conflict`
    component (the conflict relationship is preserved), and so is the constraint's support. Unaccepted claims are
    alternatives."""
    ev = Ev()
    for n, a in enumerate(r.get("appointments") or []):
        ev.at(f"appointments[{n}]")
        for e in _claim_entries(a.get("evidence")):
            if e.get("acceptance") != USABLE:
                ev.add("alternative", e["attestation"])
            elif a.get("judgement") == "established":
                ev.add("supporting", e["attestation"])
    conflict = r.get("conflict") or {}
    ev.at("conflict")
    for a in conflict.get("appointments") or []:
        ev.add("conflicting", a.get("attestations"))
    ev.add("conflicting", (conflict.get("constraint") or {}).get("support"))
    return ev


def ev_transform_between(a):
    ev = Ev()
    verified = (a.get("search") or {}).get("verified") is True         # explicit only (finding 3)
    for n, s in enumerate(a.get("chain") or []):
        ev.at(f"chain[{n}]")
        if s.get("disputed") is not False:                              # disputed, or not stated undisputed
            ev.add("conflicting", s.get("support"))
        elif not verified:
            ev.add("alternative", s.get("support"))        # unverified (truncated) candidate: never authoritative
        else:
            ev.add("supporting", s.get("support"))
    ev.at("search")
    for x in (a.get("search") or {}).get("inconsistent") or []:
        ev.add("conflicting", x.get("support"))
    return ev


def ev_where(a):
    """WH: candidates' position and chain support supporting; both candidates of every verified conflict pair
    conflicting (P-WH-1: candidates outside every pair stay supporting); inconsistent chains conflicting; alternatives,
    incomparable statements and unverified candidates alternative."""
    ev = Ev()
    cands = a.get("candidates") or []
    # a pair counts only if it is a reported conflict AND its detail is explicitly verified (finding 3)
    verified_pairs = {tuple(d["pair"]) for d in a.get("conflict_details") or []
                      if d.get("unverified") is False and "pair" in d}
    paired = {i for pair in a.get("conflicts") or [] if tuple(pair) in verified_pairs for i in pair}

    def support_of(c):
        return _ids(c.get("position_support")) | {x for s in c.get("chain") or [] for x in _ids(s.get("support"))}
    for i, c in enumerate(cands):
        ev.at(f"candidates[{i}]")
        if c.get("verified") is not True:
            ev.add("alternative", support_of(c))
        elif i in paired or c.get("x") is None or c.get("status") == "DISPUTED":
            ev.add("conflicting", support_of(c))           # a side of a verified conflict, or chains that disagree
        else:
            ev.add("supporting", support_of(c))
        for x in (c.get("search") or {}).get("inconsistent") or []:
            ev.add("conflicting", x.get("support"))
    ev.at("incomparable")
    for x in a.get("incomparable") or []:
        ev.add("alternative", x.get("support"))
    return ev.at("alternatives").add("alternative", a.get("alternatives"))


def ev_poses(entries):
    ev = Ev()
    for n, e in enumerate(entries):
        ev.at(f"[{n}]").add("conflicting" if e.get("status") == "DISPUTED" else "supporting", e.get("support"))
        ev.add("conflicting", e.get("conflicts"))
    return ev


def ev_frame_info(a):
    ev = Ev()
    for k in ("parents", "children"):
        for n, e in enumerate(a.get(k) or []):
            ev.at(f"{k}[{n}]").add("conflicting" if e.get("status") == "DISPUTED" else "supporting", e.get("support"))
    return ev


def ev_measurements(entries):
    """ME, P-ME-1: usable measurements supporting; statements and unusable values alternative."""
    ev = Ev()
    for n, m in enumerate(entries):
        ev.at(f"[{n}]")
        role = "supporting" if m.get("usable") is True and m.get("kind") == "measurement" else "alternative"
        ev.add(role, m.get("attestation"))
    return ev


def ev_compare_measurements(a):
    """CM, P-CM-1 with the shared role amendment: attestations of incompatible pairs conflicting, the other compared
    measurements supporting; alternatives and statements alternative."""
    ev = Ev()
    clash = {x for p in a.get("pairs") or [] if p.get("relation") == "incompatible" for x in (p.get("a"), p.get("b"))}
    for n, m in enumerate(a.get("measurements") or []):
        ev.at(f"measurements[{n}]").add("conflicting" if m.get("attestation") in clash else "supporting",
                                        m.get("attestation"))
    for k in ("alternatives", "statements"):
        for n, m in enumerate(a.get(k) or []):
            ev.at(f"{k}[{n}]").add("alternative", m.get("attestation"))
    return ev


def _calibration(r, ev, prefix=""):
    j = r.get("judgement")
    if j in ("established", "expired", "denied"):
        ev.at(f"{prefix}support").add("supporting", r.get("support"))
    for n, c in enumerate(r.get("certificates") or []):
        ev.at(f"{prefix}certificates[{n}]")
        for e in _claim_entries(c.get("evidence")):
            if e.get("acceptance") != USABLE:
                ev.add("alternative", e["attestation"])
            elif j == "disputed":
                ev.add("conflicting", e["attestation"])                    # P-CS-1
            elif j == "not yet effective":
                ev.add("undetermined", e["attestation"])                   # D-CS-3: unresolved
    return ev


def ev_calibration_status(r):
    return _calibration(r, Ev())


def ev_measurement_calibration(rows):
    ev = Ev()
    for n, r in enumerate(rows):
        ev.at(f"[{n}]").add("supporting" if r.get("usable") is True else "alternative", r.get("attestation"))
        if r.get("attested"):
            _calibration(r["attested"], ev, f"[{n}].attested.")
    return ev


def _causal_claim(c, ev, cause_question=True):
    """CO table, with P-CO-1 (finding 1): an accepted claim's accepted attestations support it only when the claim
    applies (`applies` is true); an accepted claim that does not apply (`applies` false, or None for a disputed
    occurrence) is listed as its source's account, so its attestations are **alternatives**. A disputed claim's
    accepted attestations conflict. A denied claim's deciding denials support the denial. Unaccepted attestations are
    alternatives. For effect claims (cause_question False) `applies` does not exist, and the judgement alone decides."""
    applies = (not cause_question) or c.get("applies") is True
    for e in _claim_entries(c.get("attestations")):
        if e.get("acceptance") != USABLE:
            ev.add("alternative", e["attestation"])
        elif c.get("judgement") == "disputed":
            ev.add("conflicting", e["attestation"])
        elif c.get("judgement") in ("accepted", "denied"):
            ev.add("supporting" if applies else "alternative", e["attestation"])
        else:                                                  # unreviewed, rejected, retracted: not rested on
            ev.add("alternative", e["attestation"])
    return ev


def ev_causes_of(claims):
    ev = Ev()
    for n, c in enumerate(claims):
        _causal_claim(c, ev.at(f"[{n}]"))
    return ev


def ev_effects_of(entries):
    """EF (P-EF-1, event-specific scope): each claim's accepted attestations by its judgement; the judged before and
    after states as Answers."""
    ev = Ev()
    for n, e in enumerate(entries):
        _causal_claim({"attestations": e.get("attestations"), "judgement": e.get("claim")}, ev.at(f"[{n}].claim"),
                      cause_question=False)
        for side in ("before", "after"):
            answer_roles((e.get("state") or {}).get(side), ev, f"[{n}].state.{side}")
    return ev


def ev_explain(a):
    ev = answer_roles(a.get("holds"), component="holds")
    for n, i in enumerate(a.get("initiated_by") or []):
        for m, c in enumerate(i.get("causes") or []):
            _causal_claim(c, ev.at(f"initiated_by[{n}].causes[{m}]"))
    return ev


def ev_changes(a):
    """CH: a world-state transition rests on both sides' support (both required: authored as required evidence);
    a side that is DISPUTED is conflicting, with its conflicts; explanations are not evidence of the change."""
    ev = Ev()
    for n, tr in enumerate(a.get("transitions") or []):
        for side in ("before", "after"):
            s = tr.get(side) or {}
            ev.at(f"transitions[{n}].{side}")
            if s.get("status") == "DISPUTED":
                ev.add("conflicting", s.get("support"))
                ev.add("conflicting", s.get("conflicts"))
            elif s.get("status") not in ("UNKNOWN", "NOT_YET_KNOWN"):
                ev.add("supporting", s.get("support"))
    return ev


def ev_process_steps(steps):
    ev = Ev()
    for n, s in enumerate(steps):
        ev.at(f"[{n}]").add("supporting" if s.get("judgement") == "established" else "conflicting", s.get("support"))
    return ev


def ev_interval(a):
    return Ev().add("supporting", a.get("attestation")) if a and a.get("attestation") else Ev()


def ev_none(a):
    return Ev()


EXTRACTORS = {
    "holds": ev_holds, "value_at": ev_value_at, "facts_about": ev_facts_about, "occurrence": ev_occurrence,
    "occurrence_status": ev_occurrence_status, "office_holders": ev_office_holders,
    "transform_between": ev_transform_between, "where": ev_where, "poses": ev_poses, "frame_info": ev_frame_info,
    "measurements": ev_measurements, "compare_measurements": ev_compare_measurements, "convert": ev_none,
    "calibration_status": ev_calibration_status, "measurement_calibration": ev_measurement_calibration,
    "causes_of": ev_causes_of, "effects_of": ev_effects_of, "explain": ev_explain, "changes": ev_changes,
    "process_steps": ev_process_steps, "before": ev_none, "interval": ev_interval,
}
# readers whose answers can cite conflicting evidence: their questions author both role sets (LABS-1.063)
CONFLICT_ROLE = {"holds", "value_at", "facts_about", "occurrence", "occurrence_status", "office_holders",
                 "transform_between", "where", "poses", "frame_info", "compare_measurements", "calibration_status",
                 "measurement_calibration", "causes_of", "effects_of", "explain", "changes", "process_steps"}
CITES = set(EXTRACTORS) - {"convert", "before"}


def as_lists(ev):
    """Normalised (JSON) form of an extraction: each role's ids (deduplicated), and every (component, role, id)."""
    return {**{r: sorted(ev.get(r, ())) for r in ROLES},
            "entries": sorted([list(e) for e in getattr(ev, "entries", set())])}


def alternatives_as_support(cited):
    """(component, id) pairs listed both as an alternative and as supporting in the same component."""
    by = {}
    for comp, role, i in cited.get("entries", []):
        by.setdefault((comp, i), set()).add(role)
    return sorted([c, i] for (c, i), roles in by.items() if {"alternative", "supporting"} <= roles)
