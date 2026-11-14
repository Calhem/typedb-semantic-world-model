"""The canonical per-content judgement (increment B: DI-1, DI-11, DI-5; LABS-1.036 to 1.038).

One record per content (proposition) in one context: the content judged, every claim that states or denies it (each
kept separately with its own acceptance, provenance and interval), the constraints that apply, and the resulting
judgement with its reason. Every core and profile reader takes its facts from these records; nothing else judges
content, applies a constraint or names a judgement. Design: docs/core-0.4/pre-e-increment-b-design.md.

Layers, in order:
1. polarity (`_judge`, unchanged): world precedence, acceptance, supersession, valid time and polarity give, per
   content, holds / does not hold / disputed (an accepted assertion against an accepted denial), with the deciding
   attestations;
2. constraints: a holding content that gives a single-value constraint a different value than another holding content
   is disputed. Declared constraints (functional slots, data) always apply. Attested constraints (a constraint that is
   itself a claim, such as an exclusive office) apply only where their own judgement in the same context is
   ESTABLISHED; they are judged without attested constraints of their own, so evaluation never recurses further;
3. the judgement and its reason, including why an undecided content is undecided (DI-5).

Cost: the core judgement is computed from the attestations the reader already loaded. Per-claim detail (`claims()`)
is expanded only when a reader asks for it. An attested constraint is judged only where it could change a judgement
(two or more different values held under it), once per report through a memo.
"""

import enum
from dataclasses import dataclass, field

from .semantics import Status, acceptance_state, answer_status, superseded, usable, verdict


class Judgement(enum.Enum):
    ESTABLISHED = "established"   # holds at t, undisputed
    DISPUTED = "disputed"         # a polarity dispute, or a conflict under an applied constraint
    NOT_HOLDING = "not holding"   # does not hold at t
    PENDING = "pending"           # nothing accepted bears on it; an unreviewed claim does
    UNKNOWN = "unknown"           # nothing decides t


# reasons
POLARITY, CONSTRAINT = "polarity", "constraint"                       # DISPUTED
DENIED, ENDED, OVERRIDDEN, EXCLUDED = "denied", "ended", "overridden", "excluded"   # NOT_HOLDING
NOT_YET_EFFECTIVE, END_UNKNOWN = "not_yet_effective", "end_unknown"   # UNKNOWN, from an accepted claim
NOT_SUPPORTING, UNACCEPTED, NO_EVIDENCE = "not_supporting", "unaccepted", "no_evidence"   # UNKNOWN, otherwise
SILENT = "silent"                       # UNKNOWN: the only accepted claims are denials that begin after t
STATE_ORDER = ("unreviewed", "rejected", "retracted", "superseded")  # the order states are named in (unchanged)


@dataclass(frozen=True)
class AttestedConstraint:
    """A constraint that is itself attested content. A profile declares its scope: content of type `constraint`
    with players for `key` (constraint role, constrained role) pairs allows at most one `value` player of
    `constrained` content with the same key players at a time. E.g. exclusive-office(office, context) constrains
    office-holding(class = office, context = context) to one `classified` holder."""
    constraint: str
    constrained: str
    key: tuple
    value: str


@dataclass(frozen=True)
class Constraint:
    """A constraint applicable to a content: declared (a functional slot) or attested. `applies` is always True for a
    declared constraint; for an attested one it is whether its own judgement (`judgement`) is ESTABLISHED.
    `rivals`: the content classes it puts this content in conflict with."""
    kind: str
    type: str
    key_roles: tuple
    value_role: str
    key: tuple
    applies: bool = True
    judgement: object = None
    rivals: tuple = ()


@dataclass(eq=False)
class ContentJudgement:
    """One content's judgement in one context (world, t, as_of, perspective)."""
    key: tuple                      # the content class: (type, canonical roles, params)
    context: tuple                  # (world, t, as_of, perspective)
    judgement: Judgement
    reasons: tuple = ()
    value: object = None            # the polarity layer: True, False, "disputed" or None (undecided)
    support: tuple = ()             # the deciding attestation records (for EXCLUDED: the excluding ones)
    status: Status | None = None    # DISPUTED for a dispute, else the support's status (None when undecided)
    support_status: Status | None = None   # the support's status before constraints (None when undecided)
    conflicts: tuple = ()           # attestation records of the contents in conflict under an applied constraint
    constraints: tuple = ()         # Constraint, every declared one and each attested one evaluated
    pending: tuple = ()             # ids of unreviewed, not superseded attestations that would decide t
    attestations: tuple = ()        # every attestation of the content in the judged pool, each kept separately
    _claims: list | None = field(default=None, repr=False)

    @property
    def type(self):
        return self.key[0]

    @property
    def roles(self):
        """Canonical players under the perspective's identity."""
        return {r: list(ids) for r, ids in self.key[1]}

    @property
    def stated_roles(self):
        """The players as the first attestation of the content states them (ids as written)."""
        first = self.attestations[0] if self.attestations else None
        return {r: list(v) for r, v in first.roles.items()} if first else self.roles

    @property
    def params(self):
        return dict(self.key[2])

    @property
    def holds(self):
        return {Judgement.ESTABLISHED: True, Judgement.NOT_HOLDING: False}.get(self.judgement)

    @property
    def support_ids(self):
        return sorted(a.id for a in self.support)

    @property
    def conflict_ids(self):
        return sorted({a.id for a in self.conflicts})

    @property
    def assertion_ids(self):
        return sorted(a.id for a in self.support if a.polarity)

    @property
    def denial_ids(self):
        return sorted(a.id for a in self.support if not a.polarity)

    def claims(self):
        """Every claim about the content, each separately: attestation, attester, polarity, basis, stance and its
        acceptance state for the perspective (accepted, unreviewed, rejected, retracted or superseded). Expanded on
        demand, then kept."""
        if self._claims is None:
            _, _, as_of, perspective = self.context
            self._claims = sorted(({"attestation": a.id, "attester": a.attester, "polarity": a.polarity,
                                    "basis": a.basis, "stance": a.stance,
                                    "acceptance": state_of(a, perspective, as_of)} for a in self.attestations),
                                  key=lambda x: x["attestation"])
        return self._claims


def state_of(a, perspective, as_of):
    return "superseded" if superseded(a, perspective, as_of) else acceptance_state(a, perspective, as_of)


def undecided(key, its, context, t, perspective, as_of):
    """The record of a content that nothing decides at t: why (DI-5). An accepted claim's reason comes first; pending
    counter-claims never outrank it and are listed in `pending`."""
    pending = tuple(sorted(a.id for a in its if acceptance_state(a, perspective, as_of) == "unreviewed"
                           and not superseded(a, perspective, as_of) and verdict(a, t) is not None))
    accepted = [a for a in its if usable(a, perspective, as_of)]
    begun = [a for a in accepted if a.start is None or a.start.latest <= t]
    if begun:            # an accepted claim has begun, and nothing says whether it continues to t
        return ContentJudgement(key, context, Judgement.UNKNOWN, (END_UNKNOWN,), pending=pending,
                                attestations=tuple(its))
    if any(a.polarity for a in accepted):        # an accepted assertion begins after t
        return ContentJudgement(key, context, Judgement.UNKNOWN, (NOT_YET_EFFECTIVE,), pending=pending,
                                attestations=tuple(its))
    # otherwise only an accepted denial that begins after t, which says nothing about t: as if none were accepted
    states = {state_of(a, perspective, as_of) for a in its}
    if "unreviewed" in states:
        return ContentJudgement(key, context, Judgement.PENDING, pending=pending, attestations=tuple(its))
    if states & set(STATE_ORDER):
        return ContentJudgement(key, context, Judgement.UNKNOWN, (UNACCEPTED,), pending=pending,
                                attestations=tuple(its))
    if accepted:
        reason = SILENT                                 # only accepted denials that begin after t
    else:
        reason = NOT_SUPPORTING if its else NO_EVIDENCE  # accepted, but a doubt or hypothesis: it never decides
    return ContentJudgement(key, context, Judgement.UNKNOWN, (reason,), pending=pending, attestations=tuple(its))


def decided(key, its, context, val, support, rivals, constraints, perspective, as_of, t):
    pending = tuple(sorted(a.id for a in its if acceptance_state(a, perspective, as_of) == "unreviewed"
                           and not superseded(a, perspective, as_of) and verdict(a, t) is not None))
    base = dict(value=val, support=tuple(support), constraints=tuple(constraints), pending=pending,
                attestations=tuple(its))
    if val == "disputed":
        return ContentJudgement(key, context, Judgement.DISPUTED, (POLARITY,), status=Status.DISPUTED,
                                support_status=Status.DISPUTED, **base)
    status = answer_status(support)
    if val is True:
        if rivals:
            return ContentJudgement(key, context, Judgement.DISPUTED, (CONSTRAINT,), status=Status.DISPUTED,
                                    support_status=status, conflicts=tuple(rivals), **base)
        return ContentJudgement(key, context, Judgement.ESTABLISHED, status=status, support_status=status, **base)
    accepted = [a for a in its if state_of(a, perspective, as_of) == "accepted"]
    reason = ENDED if all(a.polarity for a in accepted) else DENIED
    return ContentJudgement(key, context, Judgement.NOT_HOLDING, (reason,), status=status, support_status=status,
                            **base)


# ---- the one labelling rule ---------------------------------------------------------------------------------------------
def claim_label(r):
    """The claims vocabulary (effects_of, causes_of, occurrence_status, measurements): accepted, denied, disputed,
    not yet effective, not established, unknown, or the claims' best state (unreviewed, rejected, retracted,
    superseded) when nothing accepted bears on the content."""
    j = r.judgement
    if j is Judgement.ESTABLISHED:
        return "accepted"
    if j is Judgement.DISPUTED:
        return "disputed"
    if j is Judgement.NOT_HOLDING:
        return "denied" if r.reasons[0] in (DENIED, ENDED) else "not established"
    if j is Judgement.PENDING:
        return "unreviewed"
    reason = r.reasons[0]
    if reason == NOT_YET_EFFECTIVE:
        return "not yet effective"
    if reason == UNACCEPTED:
        states = {c["acceptance"] for c in r.claims()}
        return next(s for s in STATE_ORDER if s in states)
    if reason == NO_EVIDENCE:
        return "unknown"
    return "not established"                            # END_UNKNOWN, NOT_SUPPORTING, SILENT


def holding_label(r):
    """The holdings vocabulary (capable, the organisation and laboratory reports): the claims label, with an accepted
    holding that has ended (no accepted denial) named `expired`."""
    if r.judgement is Judgement.NOT_HOLDING and r.reasons[0] == ENDED:
        return "expired"
    return claim_label(r)


def parse_scopes(profiles, installed):
    return [s for name in installed if name in profiles for s in getattr(profiles[name], "attested_constraints", ())]


# ---- building records -----------------------------------------------------------------------------------------------------
class JudgementMixin:
    """Builds records from attestations a reader has loaded. Uses the model's `_judge`, `_class`, `_constraints` and
    `_conflicts`; nothing here reads the database except an attested constraint's own judgement."""

    def _attested_scopes(self, ctype):
        """The attested constraints (AttestedConstraint) of installed profiles that apply to a content type."""
        if self._scopes is None:
            from .profiles import PROFILES
            self._scopes = {"*": parse_scopes(PROFILES, sorted(self.profiles())), "by": {}}
        by = self._scopes["by"]
        if ctype not in by:
            by[ctype] = [s for s in self._scopes["*"] if self.is_a(ctype, s.constrained)]
        return by[ctype]

    def _attested_conflicts(self, world, holding, t, as_of, perspective, memo):
        """{class: [Constraint]} for holding classes under an attested constraint whose members give it two or more
        values. The constraint is judged (once per key, through `memo`) only there, without attested constraints of
        its own; it applies only when ESTABLISHED (LABS-1.036)."""
        groups = {}
        for cls in holding:
            scopes = self._attested_scopes(cls[0])
            if not scopes:
                continue
            players = dict(cls[1])
            for s in scopes:
                key = tuple(players.get(cr) for _, cr in s.key)
                if all(key):
                    groups.setdefault((s, key), []).append(cls)
        out = {}
        for (s, key), members in groups.items():
            values = {dict(c[1]).get(s.value) for c in members}
            if len(values) < 2:
                continue
            mk = (s.constraint, key, world, t, as_of, perspective)
            rec = memo.get(mk) if memo is not None else None
            if rec is None:
                rec = self.judgement(world, s.constraint, {kr: list(k) for (kr, _), k in zip(s.key, key)}, t, as_of,
                                     perspective, attested=False)
                if memo is not None:
                    memo[mk] = rec
            applies = rec.judgement is Judgement.ESTABLISHED
            for c in members:
                mine = dict(c[1]).get(s.value)
                rivals = tuple(o for o in members if dict(o[1]).get(s.value) != mine) if applies else ()
                out.setdefault(c, []).append(Constraint("attested", s.constraint, tuple(kr for kr, _ in s.key),
                                                        s.value, key, applies, rec, rivals))
        return out

    def _records(self, atts, ident, t, perspective, as_of, world=None, attested=True, memo=None):
        """{class: ContentJudgement} for every content in `atts` (the pool must include the rivals a constraint
        needs). Judged classes first, in `_judge` order, then undecided ones. attested False: only declared
        constraints (an attested constraint's own judgement; office_holders' per-appointment entries)."""
        from .model import PARAMS_VALUE
        atts = list(atts)
        ctx = (world, t, as_of, perspective)
        dropped = set()
        judged = self._judge(atts, ident, t, perspective, as_of, dropped=dropped)
        holding = [c for c, (v, _, _) in judged.items() if v is True]
        declared = self._conflicts(holding)
        attested_c = (self._attested_conflicts(world, holding, t, as_of, perspective, {} if memo is None else memo)
                      if attested and world is not None else {})
        by_class = {}
        for a in atts:
            by_class.setdefault(self._class(a, ident), []).append(a)
        # single-valued slots with an undisputed value: what excludes an undecided content of the same slot
        slot_values, slot_disputed = {}, set()
        for cls, (val, sup, _) in judged.items():
            players = dict(cls[1])
            for decl, ks, v in self._constraints(cls[0]):
                slot = (decl, ks, v, tuple(players.get(r) for r in ks))
                if val == "disputed" or cls in declared:
                    slot_disputed.add(slot)
                elif val is True:
                    slot_values.setdefault(slot, []).append((cls, sup))
        out = {}
        for cls in list(judged) + [c for c in by_class if c not in judged]:
            its = by_class.get(cls, [])
            players = dict(cls[1])
            constraints = [Constraint("declared", decl, ks, v, tuple(players.get(r) for r in ks),
                                      rivals=tuple(declared.get(cls, ())))
                           for decl, ks, v in self._constraints(cls[0])]
            constraints += attested_c.get(cls, [])
            if cls in judged:
                val, sup, _ = judged[cls]
                rival_classes = set(declared.get(cls, ())) | {r for c in attested_c.get(cls, ()) for r in c.rivals}
                rivals = sorted({a.id: a for r in rival_classes for a in judged[r][1]}.values(), key=lambda a: a.id)
                out[cls] = decided(cls, its, ctx, val, sup, rivals, constraints, perspective, as_of, t)
                continue
            excluding = None
            for decl, ks, v in self._constraints(cls[0]):
                slot = (decl, ks, v, tuple(players.get(r) for r in ks))
                if v == PARAMS_VALUE or slot in slot_disputed or slot not in slot_values:
                    continue
                held = slot_values[slot]
                if not any(dict(c[1]).get(v) == players.get(v) for c, _ in held):
                    excluding = [a for _, sup in held for a in sup]
                    break
            if excluding is not None:
                out[cls] = ContentJudgement(cls, ctx, Judgement.NOT_HOLDING,
                                            (OVERRIDDEN if cls in dropped else EXCLUDED,),
                                            support=tuple(sorted(excluding, key=lambda a: a.id)),
                                            status=Status.INFERRED, support_status=Status.INFERRED,
                                            constraints=tuple(constraints), attestations=tuple(its))
                continue
            out[cls] = undecided(cls, its, ctx, t, perspective, as_of)
            if constraints:
                out[cls].constraints = tuple(constraints)
        return out

    def _scope_rivals(self, world, as_of, perspective, recs, ident, pool=None, at=None):
        """Attestations of content under the same attested-constraint key as `recs` that `recs` lack (the other
        holders of an exclusive office, seen from one holder). Selective: one load per constrained type, only for
        types an installed profile constrains; full load: taken from `pool`."""
        have = {a.id for a in recs}

        def key_of(a, s):
            return tuple(tuple(sorted({ident.canonical(x) for x in a.roles.get(cr, [])})) for _, cr in s.key)

        wanted = {}
        for a in recs:
            for s in self._attested_scopes(a.ctype):
                key = key_of(a, s)
                if all(key):
                    wanted.setdefault(s, set()).add(key)
        extra = {}
        for s, keys in wanted.items():
            members = sorted({m for key in keys for x in key[0] for m in ident.members(x)})
            found = (pool if pool is not None else
                     self._load(world, as_of, types=[s.constrained], subjects=members, at=at, perspective=perspective))
            for k, a in found.items():
                if k not in have and k not in extra and self.is_a(a.ctype, s.constrained) and key_of(a, s) in keys:
                    extra[k] = a
        return list(extra.values())


def without_attested(r):
    """The record as it stands before attested constraints: a content disputed only under an attested constraint is
    ESTABLISHED, with the support's status. For reports whose per-item entries are defined before the constraint
    (office_holders' appointments, choice A); the conflict itself is read from the record's constraints."""
    import dataclasses
    if r.judgement is not Judgement.DISPUTED or POLARITY in r.reasons:
        return r
    if any(c.kind == "declared" and c.rivals for c in r.constraints):
        return r
    return dataclasses.replace(r, judgement=Judgement.ESTABLISHED, reasons=(), status=r.support_status, conflicts=(),
                               _claims=r._claims)


def attested_conflict(r, constraint, key_players):
    """The applied attested constraint of type `constraint` whose key includes each of `key_players` (one id per key
    role, in order) and puts `r` in conflict, or None."""
    for c in r.constraints:
        if (c.kind == "attested" and c.type == constraint and c.applies and c.rivals
                and all(p in k for p, k in zip(key_players, c.key))):
            return c
    return None
