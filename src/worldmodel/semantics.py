"""Application-level semantics of World Ontology v0.2 (pure Python, no database).

Everything here is a decision of the ontology's semantics that TypeDB does not enforce: whether an attestation is
usable for a perspective at a knowledge time, what it says about valid time t, identity closure, and answer statuses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Status(str, Enum):
    """Answer classification (v0.2 §5.6, layer 3). OBSERVED and PRESUMED need observations and persistence policies,
    which Core 0.3 does not implement yet (attestations with basis observation are reported as ASSERTED, with the basis
    visible in the evidence)."""
    OBSERVED = "OBSERVED"
    ASSERTED = "ASSERTED"
    STIPULATED = "STIPULATED"
    INFERRED = "INFERRED"
    PRESUMED = "PRESUMED"
    DISPUTED = "DISPUTED"
    UNKNOWN = "UNKNOWN"
    NOT_YET_KNOWN = "NOT_YET_KNOWN"


SUPPORTING_STANCES = ("asserts", "believes", "stipulates")   # `doubts` and `hypothesises` never support an answer


@dataclass(frozen=True)
class Window:
    """A time known to lie in [earliest, latest]. `latest=None` means unbounded above; equal bounds mean exact."""
    earliest: datetime
    latest: datetime | None

    @staticmethod
    def at(t):
        return Window(t, t)


@dataclass
class Replacement:
    """A visible supersession of an attestation: the replacing attestation's id, when the supersession was recorded,
    and what a perspective needs to judge it (its attester, stance and the perspective's acceptances of it)."""
    id: str
    recorded_at: datetime
    attester: str
    stance: str
    acceptances: list = field(default_factory=list)   # [(holder, verdict, recorded_at)]


@dataclass
class AttestationRecord:
    id: str
    content: str                       # proposition key, or event-description id
    ctype: str                         # content type label
    roles: dict                        # role -> sorted ids
    params: dict
    attester: str
    world: str
    stance: str
    polarity: bool
    basis: str
    start: Window | None               # None: from the start of the world
    end: Window | None                 # stated end window
    end_basis: str                     # "stated", "unknown", "until-superseded"
    recorded_at: datetime
    credence: float | None = None
    depth: int = 0                     # 0: the asked world; n: inherited from the n-th base world
    acceptances: list = field(default_factory=list)   # [(holder, verdict, recorded_at)]
    superseded_by: list = field(default_factory=list)  # [Replacement] visible in this context

    def evidence(self):
        return {"attestation": self.id, "attester": self.attester, "stance": self.stance, "basis": self.basis,
                "polarity": self.polarity, "world": self.world, "start": self.start, "end": self.end,
                "recorded_at": self.recorded_at,
                "superseded_by_source": sorted(r.id for r in self.superseded_by)}


def acceptance_state(a, perspective, as_of):
    """'accepted', 'rejected', 'retracted' or 'unreviewed' for `perspective` at knowledge time `as_of`.

    Stipulations are constitutive of their world: accepted for everyone (E7). Otherwise the perspective's latest
    decision by `as_of` wins, a rejection or retraction winning ties; without one, the perspective's own attestations
    are accepted (they are part of its view) and others' are unreviewed.
    """
    if a.stance == "stipulates":
        return "accepted"
    mine = [(rec, v) for h, v, rec in a.acceptances if h == perspective and (as_of is None or rec <= as_of)]
    if mine:
        latest = max(rec for rec, _ in mine)
        verdicts = {v for rec, v in mine if rec == latest}
        for v in ("retracted", "rejected"):
            if v in verdicts:
                return v
        return "accepted"
    return "accepted" if a.attester == perspective else "unreviewed"


def superseded(a, perspective, as_of):
    """Superseded *for this perspective*: its source has replaced it (a supersession recorded by `as_of`) **and** the
    replacement is part of the perspective's view (its own, accepted by it, or a stipulation). A source's revision is
    not another perspective's acceptance: until a perspective accepts the replacement it keeps the original, and if it
    rejects the replacement it keeps the original for good."""
    return any((as_of is None or r.recorded_at <= as_of) and acceptance_state(r, perspective, as_of) == "accepted"
               for r in a.superseded_by)


def usable(a, perspective, as_of):
    """Supports answers for the perspective: accepted, not superseded for it, and a supporting stance."""
    return (a.stance in SUPPORTING_STANCES and not superseded(a, perspective, as_of)
            and acceptance_state(a, perspective, as_of) == "accepted")


def in_interval(a, t):
    """True: t is certainly inside the attested interval; False: certainly after its end (or, for existence, before
    creation); None: the attestation does not decide t. Half-open [start, end). A missing start means "from the start
    of the world"; end basis "until-superseded" holds until a supersession is recorded; "unknown" decides nothing after
    the start (no invented continuity). Before its start an attestation is silent, except that an existence start is
    a creation."""
    if a.start is not None and t < a.start.latest:
        if a.ctype == "existence" and a.polarity and t < a.start.earliest:
            return False
        return None
    if a.end is not None:
        if t < a.end.earliest:
            return True
        if a.end.latest is not None and t >= a.end.latest:
            return False
        return None
    return True if a.end_basis == "until-superseded" else None


def verdict(a, t):
    """What the attestation says about its content at t: True (holds), False (does not hold), None (nothing).

    A positive attestation says the content holds inside its interval and, with a stated end, no longer holds after it.
    A denial says the content does not hold inside its interval and nothing outside it."""
    inside = in_interval(a, t)
    if a.polarity:
        return inside
    return False if inside is True else None


def certainly_before(a, b):
    """a's interval certainly ends before b's starts (windows; never a guess)."""
    a_end = a.end.latest if a.end is not None else (a.start.latest if a.start else None)
    return a_end is not None and b.start is not None and a_end <= b.start.earliest


def answer_status(support):
    """Status for a set of supporting attestations: STIPULATED > ASSERTED > INFERRED by basis (v0.2 gives no order
    between supported kinds; Core 0.3 reports the most direct basis and lists all evidence)."""
    bases = {a.basis for a in support}
    if "stipulation" in bases:
        return Status.STIPULATED
    if bases & {"testimony", "observation"}:
        return Status.ASSERTED
    return Status.INFERRED


class Identity:
    """Equivalence classes from usable `same-as` attestations for one perspective. Unaccepted links never chain."""

    def __init__(self, same_as, perspective, as_of):
        self.parent, self.proposed = {}, []
        for a in same_as:
            if a.ctype != "same-as" or not a.polarity:
                continue
            x, y = a.roles["same"][:2]
            if usable(a, perspective, as_of):
                self._union(x, y)
            elif acceptance_state(a, perspective, as_of) == "unreviewed" and not superseded(a, perspective, as_of):
                self.proposed.append((a.id, x, y))

    def _find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def _union(self, a, b):
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            keep, drop = sorted((ra, rb))
            self.parent[drop] = keep

    def canonical(self, x):
        return self._find(x)

    def members(self, x):
        root = self._find(x)
        return sorted({y for y in list(self.parent) if self._find(y) == root} | {x})


@dataclass(frozen=True)
class Answer:
    status: Status
    holds: bool | None = None                 # holds(): True / False / None
    values: tuple = ()                        # value_at(): canonical ids
    support: tuple = ()                       # attestation ids the answer rests on
    alternatives: tuple = ()                  # unreviewed attestations bearing on the question
    evidence: tuple = ()                      # one dict per supporting attestation (attester, stance, basis, ...)
