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
    ctype: str                         # content type label, as stored (a profile subtype stays itself)
    roles: dict                        # core role name -> sorted ids (a specialised role maps to the role it specialises)
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
    base: str | None = None            # nearest core type of ctype (A0.2); None: ctype is a core type
    concrete_roles: dict | None = None  # role name as stored -> sorted ids, when any differs from `roles` (A0.2)

    @property
    def kind(self):
        """The core type this content is an instance of (its foundational type), whatever profile subtype it has."""
        return self.base or self.ctype

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
        if a.kind == "existence" and a.polarity and t < a.start.earliest:
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
    A denial says the content does not hold inside its interval and nothing outside it.

    Identity is timeless (ID-3, LABS-1.048): a same-as attestation says its polarity at every t; any interval stated
    on it (written before the increment) is ignored."""
    if a.kind == "same-as":
        return a.polarity
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


def decide(items, t):
    """The polarity layer for one content class (increment B's first layer, shared by `_judge` and identity links):
    `items` are (usable attestation, its verdict at t) pairs with a verdict. Returns (True / False / "disputed", the
    deciding attestations, their world depth), or None when nothing decides.

    The nearest world's deciding attestations win; an assertion and a denial at that depth are a dispute. A stated end
    says the content stopped holding, but only until the content is attested to start again: an ended attestation's
    "does not hold" is dropped when a usable positive attestation of the same content started after that end and by t.
    Genuine conflicts (an account begun before the end) still dispute."""
    restarts = [a.start for a, v in items if a.polarity and a.start is not None]
    items = [(a, v) for a, v in items if not (
        v is False and a.polarity and a.end is not None and a.end.latest is not None
        and any(st.earliest >= a.end.latest and st.latest <= t for st in restarts))]
    if not items:
        return None
    depth = min(a.depth for a, _ in items)
    near = [(a, v) for a, v in items if a.depth == depth]
    vals = {v for _, v in near}
    return ("disputed" if len(vals) > 1 else vals.pop(), [a for a, _ in near], depth)


class Identity:
    """Identity classes for one context (world, knowledge time, perspective), from the visible `same-as` attestations
    (LABS-1.048, decisions ID-1 to ID-7 of docs/core-0.4/pre-e-identity-design.md):
    - ID-1: each identity link (one unordered pair of stated names) is judged by its stated names with the polarity
      layer (`decide`), never through identity: world precedence, acceptance, supersession and polarity;
    - ID-3: timelessly (valid time does not enter; see `verdict`);
    - ID-2, ID-4: two names are one thing only through links judged ESTABLISHED: the classes are the connected
      components of the established links; disputed, denied, pending and unknown links join nothing;
    - ID-5: a component containing two names whose own link is DISPUTED or NOT_HOLDING is not merged at all (each name
      is its own class) and is reported in `conflicts`;
    - ID-6, ID-7: the nearest world decides each link; the perspective's acceptances at `as_of` apply (via `usable`).

    `links`: every established link, with its support, the world depth that decided it and whether it merges (False
    inside a conflict). `conflicts`: one entry per component in conflict. `proposed`: unreviewed links (unchanged)."""

    def __init__(self, same_as, perspective, as_of):
        self.parent, self.proposed = {}, []
        by_pair = {}
        for a in same_as:
            if a.kind != "same-as":
                continue
            names = a.roles.get("same", [])[:2]
            if len(names) < 2:
                continue
            x, y = names
            by_pair.setdefault(tuple(sorted((x, y))), []).append(a)
            if a.polarity and acceptance_state(a, perspective, as_of) == "unreviewed" \
                    and not superseded(a, perspective, as_of):
                self.proposed.append((a.id, x, y))
        self.judged = {}                  # pair -> ("established" | "disputed" | "denied", support ids, depth)
        for pair, its in sorted(by_pair.items()):
            d = decide([(a, a.polarity) for a in its if usable(a, perspective, as_of)], None)
            if d is None:
                continue                  # pending or unknown: joins nothing, not conflict evidence
            val, support, depth = d
            label = {True: "established", False: "denied", "disputed": "disputed"}[val]
            self.judged[pair] = (label, tuple(sorted(a.id for a in support)), depth)
        reach = {}
        for (x, y), (label, _, _) in self.judged.items():
            if label == "established":
                self._union(reach, x, y)
        self._reach = reach
        comps = {}
        for x in list(reach):
            comps.setdefault(self._root(reach, x), set()).add(x)
        self.conflicts = []
        blocked = set()
        for root, comp in sorted(comps.items()):
            against = [(p, j) for p, j in self.judged.items() if j[0] != "established" and set(p) <= comp]
            if not against:
                continue
            blocked |= comp
            self.conflicts.append({
                "names": sorted(comp),
                "links": [self._link(p, j) for p, j in sorted(self.judged.items())
                          if j[0] == "established" and set(p) <= comp],
                "against": [self._link(p, j) for p, j in sorted(against)]})
        for (x, y), (label, _, _) in sorted(self.judged.items()):
            if label == "established" and x not in blocked:
                self._union(self.parent, x, y)
        self.links = [{**self._link(p, j), "merges": p[0] not in blocked}
                      for p, j in sorted(self.judged.items()) if j[0] == "established"]

    @staticmethod
    def _link(pair, judged):
        label, support, depth = judged
        return {"same": list(pair), "judgement": label, "support": list(support), "depth": depth}

    @staticmethod
    def _root(parent, x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def _union(self, parent, a, b):
        ra, rb = self._root(parent, a), self._root(parent, b)
        if ra != rb:
            keep, drop = sorted((ra, rb))
            parent[drop] = keep

    def _find(self, x):
        return self._root(self.parent, x)

    def canonical(self, x):
        return self._find(x)

    def members(self, x):
        root = self._find(x)
        return sorted({y for y in list(self.parent) if self._find(y) == root} | {x})

    def reach(self, x):
        """Every name connected to x by established links, whether or not the component merges (a conflict does not
        stop the selective path from loading the component's links: TI-4)."""
        root = self._root(self._reach, x)
        return sorted({y for y in list(self._reach) if self._root(self._reach, y) == root} | {x})

    def report(self, x):
        """The identity of x for a reader (ID-6, ID-9): the established links among the names connected to it, each
        with its support and world depth, and the conflict that keeps them apart, if any."""
        names = set(self.reach(x))
        conflict = next((c for c in self.conflicts if x in c["names"]), None)
        return {"links": [link for link in self.links if set(link["same"]) <= names], "conflict": conflict}


@dataclass(frozen=True)
class Answer:
    status: Status
    holds: bool | None = None                 # holds(): True / False / None
    values: tuple = ()                        # value_at(): canonical ids
    support: tuple = ()                       # attestation ids the answer rests on
    alternatives: tuple = ()                  # unreviewed attestations bearing on the question
    evidence: tuple = ()                      # one dict per supporting attestation (attester, stance, basis, ...)
    conflicts: tuple = ()                     # holds(), functional dispute: attestation ids of the conflicting
                                              # contents (their evidence is in `evidence` too) (LABS-1.005)
    constraint_support: tuple = ()            # DI-19 (LABS-1.060): one dict per applied ATTESTED constraint of the
                                              # judgement the answer projects: its type, key players, constrained value
                                              # role, and the ids and evidence of the attestations deciding the
                                              # constraint's own judgement. A declared functional slot is schema data,
                                              # so it never adds an entry. Additive: no other field changes
