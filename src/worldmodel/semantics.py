"""Application-level semantics: valid-time truth, status at a transaction time, identity closure, answers.

Pure Python, no database. Everything here is a decision of the ontology's *semantics* that TypeDB does not enforce.
Milestone 1 implements the statuses ASSERTED, INFERRED, DISPUTED, UNKNOWN and NOT_YET_KNOWN. OBSERVED and PRESUMED
(observations, persistence policies) arrive in Milestone 2.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Status(str, Enum):
    ASSERTED = "ASSERTED"            # an accepted claim states it (author, source or document)
    INFERRED = "INFERRED"            # derived by a declared rule (M1: functional exclusivity)
    DISPUTED = "DISPUTED"            # accepted claims of equal standing disagree at that time
    UNKNOWN = "UNKNOWN"              # claims exist by the transaction time, none decides the valid time
    NOT_YET_KNOWN = "NOT_YET_KNOWN"  # nothing about it had been recorded by the transaction time


@dataclass(frozen=True)
class Window:
    """A time known to lie in [earliest, latest]. `latest=None` means unbounded above; equal bounds mean exact."""
    earliest: datetime
    latest: datetime | None

    @staticmethod
    def at(t):
        return Window(t, t)


@dataclass
class ClaimRecord:
    id: str
    type: str
    world: str
    roles: dict                       # role label -> list of referent (or claim) ids
    start: Window | None              # None: holds from the start of the world (an author's statement)
    end: Window | None                # stated end window, if any
    end_basis: str                    # "stated", "unknown", "until-ceased"
    recorded_at: datetime
    initial_status: str               # "accepted" or "proposed"
    clock: str = "wall"
    description: str | None = None
    depth: int = 0                    # 0: claim of the queried world; n: inherited from the n-th base world
    cessations: list = field(default_factory=list)   # [(Window, recorded_at, world)]
    reviews: list = field(default_factory=list)      # [(verdict, recorded_at)]


def status_at(claim, as_of):
    """'accepted', 'proposed', 'rejected' or 'retracted' at transaction time `as_of` (None = now / everything).

    The latest review recorded by `as_of` decides; on a tie, a rejection or retraction wins. Without a review, the
    claim's initial status applies.
    """
    reviews = [(rec, v) for v, rec in claim.reviews if as_of is None or rec <= as_of]
    if not reviews:
        return claim.initial_status
    latest = max(rec for rec, _ in reviews)
    verdicts = {v for rec, v in reviews if rec == latest}
    for v in ("retracted", "rejected"):
        if v in verdicts:
            return v
    return "accepted"


def effective_end(claim, as_of):
    """(end window, basis) as known at `as_of`: the earliest cessation recorded by then overrides the stated end."""
    ces = [w for w, rec, _ in claim.cessations if as_of is None or rec <= as_of]
    if ces:
        return min(ces, key=lambda w: (w.earliest, w.latest or datetime.max.replace(tzinfo=w.earliest.tzinfo))), "ceased"
    return claim.end, claim.end_basis


def truth_at(claim, t, as_of):
    """True if the claim certainly holds at t, False if it certainly does not, None if this claim does not decide.

    Half-open valid time [start, end). Holds for certain when start.latest <= t < end.earliest. A missing start means
    "from the start of the world". End basis "until-ceased" with no cessation: holds for every t after the start.
    End basis "unknown" with no stated window: the claim decides nothing after its start (no invented continuity).
    Before the start the claim is silent (it does not say the fact was false earlier).
    """
    if claim.start is not None and t < claim.start.latest:
        return None
    end, basis = effective_end(claim, as_of)
    if end is not None:
        if t < end.earliest:
            return True
        if end.latest is not None and t >= end.latest:
            return False
        return None
    if basis == "until-ceased":
        return True
    return None


def certainly_before(a, b):
    """Event a certainly ended before event b started (both ClaimRecords; uses windows, never guesses)."""
    a_end = a.end.latest if a.end is not None else (a.start.latest if a.start else None)
    return a_end is not None and b.start is not None and a_end <= b.start.earliest


class Identity:
    """Equivalence classes from accepted same-as claims only. Proposed links are never chained."""

    def __init__(self, same_as_claims, as_of):
        self.parent = {}
        self.proposed = []
        for c in same_as_claims:
            a, b = c.roles["same"][:2]
            st = status_at(c, as_of)
            if st == "accepted":
                self._union(a, b)
            elif st == "proposed":
                self.proposed.append((c.id, a, b))

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
    holds: bool | None = None                 # for holds(): True / False / None
    values: tuple = ()                        # for value_at(): canonical referent ids
    support: tuple = ()                       # claim ids the answer rests on
    alternatives: tuple = ()                  # proposed (not accepted) claim ids bearing on the question
