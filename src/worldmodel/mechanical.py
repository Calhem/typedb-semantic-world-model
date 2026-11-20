"""Profile mechanical-0.1 (Core 0.4 Stage D-1, LABS-1.023): connections and part replacement, over the core.

Uses only core concepts: assemblies are core `part-of`; dependencies are core `depends-on` with core kinds
(`depends_on` / `direct_dependencies` on WorldModel); this module adds the profile's two contents and reporting:
- `connect` / `connections`: a mechanical connection between two parts, with its joint kind; never parthood;
- `replace_part` / `replacement`: a replacement account (removed and fitted parts told apart) with the part-of effects
  its source claims. The report keeps the account, the occurrence's own status and the claimed effects apart:
  an accepted account does not establish that the replacement occurred, and a claimed effect is not a state change.
No failure propagation or dependency inference.
"""

from .operations import atomic
from .judgement import Judgement
from .model import SCHEMA_DIR, SYSTEM
from .profiles import PROFILES, EventRole, Profile

NAME = "mechanical"
# A one-for-one replacement swaps one part for one part. Whether a replacement removed or fitted several parts depends
# on the operation (a pair of bearings, a gasket set, two seals replaced by one), so the removed (patient) and fitted
# parts are single-valued only for an occurrence established as `mechanical:one-for-one` at its start (LABS-1.043,
# ER-6); without that, several accounts naming different parts are a union, never a dispute.
ONE_FOR_ONE = "mechanical:one-for-one"
# 0.2 (LABS-1.043) adds data only to 0.1: the one-for-one category and the two kind-scoped event-role constraints; the
# schema file is unchanged. 0.3 (LABS-1.049, DI-13, MP-1) opens removed and fitted to several parts per account (a
# multi-part replacement); no new constraint (MP-4): a one-for-one replacement keeps one part each (multiplicity
# `one`), any other replacement is a union. upgrade_profile("mechanical") brings an installed 0.1 or 0.2 to 0.3.
_SCHEMA_01 = (str(SCHEMA_DIR / "profiles" / "mechanical" / "mechanical-0.1.tql"),)
_VOCAB_01 = (("category", "mechanical:assembly", "assembly"),
             ("category", "mechanical:component", "component"),
             ("category", "mechanical:bolted", "bolted joint"),
             ("category", "mechanical:pressed", "press fit"),
             ("category", "mechanical:splined", "splined joint"))
_VOCAB_02 = _VOCAB_01 + (("category", ONE_FOR_ONE, "one-for-one replacement"),)
_ROLES_02 = (EventRole("replacement", "patient", ONE_FOR_ONE), EventRole("replacement", "fitted", ONE_FOR_ONE))
PROFILE_01 = Profile(NAME, "0.1", _SCHEMA_01, vocabulary=_VOCAB_01)
PROFILE_02 = Profile(NAME, "0.2", _SCHEMA_01, vocabulary=_VOCAB_02, event_roles=_ROLES_02, upgrades_from="0.1",
                     previous=PROFILE_01)
PROFILE = Profile(NAME, "0.3", _SCHEMA_01 + (str(SCHEMA_DIR / "profiles" / "mechanical" / "mechanical-0.3.tql"),),
                  vocabulary=_VOCAB_02, event_roles=_ROLES_02, upgrades_from="0.2",
                  opens=("replacement:removed", "replacement:fitted"), previous=PROFILE_02)
PROFILES[NAME] = PROFILE


def _require(wm):
    if NAME not in wm.profiles():
        raise ValueError("the mechanical profile is not installed (wm.install_profile('mechanical'))")


def connect(wm, world, a, b, joint_kind=None, **attest):
    """Attest a mechanical connection between parts a and b (order irrelevant), optionally of a joint kind."""
    _require(wm)
    roles = {"endpoint": sorted({a, b})}
    if joint_kind is not None:
        roles["joint-kind"] = joint_kind
    if "end" not in attest:
        attest.setdefault("until_superseded", True)
    return wm.attest(world, "connected-to", roles, **attest)


def connections(wm, world, part, t, as_of=None, perspective=SYSTEM):
    """The connections of `part` that hold, or are disputed, at t: the other part, joint kind, status, support."""
    out = []
    for e in wm._contents(world, part, ("connected-to",), t, as_of, perspective):
        if e.about("endpoint") and e.judgement in (Judgement.ESTABLISHED, Judgement.DISPUTED):
            others = [x for x in e.stated_roles["endpoint"] if x not in e.subject]
            out.append({"other": others[0] if others else part,
                        "joint_kind": (e.stated_roles.get("joint-kind") or [None])[0], "status": e.status,
                        "support": [a["attestation"] for a in e.claims() if a["acceptance"] == "accepted"]})
    return sorted(out, key=lambda c: (c["other"], c["joint_kind"] or ""))


@atomic
def replace_part(wm, world, assembly, removed, fitted, start, end=None, actor=None, instrument=None, location=None,
                 occurrence=None, attester=SYSTEM, id=None):
    """A source's account of replacing `removed` by `fitted` in `assembly`: a `replacement` description (attested
    over [start, end], optionally describing `occurrence`) and the effects the source claims for it: it terminates
    part-of(removed, assembly) and initiates part-of(fitted, assembly). Claims only: nothing here establishes that
    the replacement happened or that the parts changed. Returns the ids.
    One operation (DI-8): the account and its effect claims are written together or not at all; inside a caller's
    `wm.operation()` it joins that operation (e.g. with the creation of the sample or part).
    `removed` and `fitted` may each be one part or several (a multi-part replacement, mechanical 0.3, LABS-1.049): one
    account names them all, and one part-of effect is claimed per part (terminations first, then initiations)."""
    _require(wm)
    roles = {"removed": removed, "fitted": fitted}
    for role, who in (("actor", actor), ("instrument", instrument), ("location", location)):
        if who is not None:
            roles[role] = who
    event = wm.account(world, roles, start, end or start, type="replacement", occurrence=occurrence,
                       attester=attester, id=id)
    def parts(x):
        return [x] if isinstance(x, str) else list(x)
    effects = ([wm.claim_effect(world, event, "terminates", "part-of", {"part": p, "whole": assembly},
                                attester=attester) for p in parts(removed)] +
               [wm.claim_effect(world, event, "initiates", "part-of", {"part": p, "whole": assembly},
                                attester=attester) for p in parts(fitted)])
    return {"event": event, "effects": effects}


def replacement(wm, world, event, t, as_of=None, perspective=SYSTEM):
    """Report a replacement description for the perspective, concluding nothing beyond it:
    - the account: accepted or not, its interval, the removed and fitted parts it names;
    - the occurrences it is accepted as describing, each with its own status (not the account's);
    - the part-of effects claimed for it, each with the claim's judgement and the state before and after (effects_of)."""
    content = wm.content(event)
    if content is None or not wm.is_a(content["type"], "replacement"):
        raise ValueError(f"{event!r} is not a replacement description")
    span = wm.interval(world, event, as_of, perspective)
    at = span[0].earliest if span and span[0] else None
    occs = wm.occurrences_of(world, event, as_of, perspective)
    return {"event": event, "account": "accepted" if span else "not accepted",
            "start": span[0] if span else None, "end": span[1] if span else None,
            "removed": content["roles"].get("removed", []), "fitted": content["roles"].get("fitted", []),
            "participants": content["roles"],
            "occurrences": [{"occurrence": o, "status": wm.occurrence_status(world, o, at, as_of, perspective,
                                                                            details=False)["status"]
                             if at is not None else None} for o in occs],
            "effects": [{"kind": e["kind"], "outcome": e["outcome"]["roles"], "claim": e["claim"],
                         "claimed_by": e["claimed_by"],
                         # no accepted account, no interval: the state around it is not judged (None)
                         "before": e["state"]["before"].holds if e["state"] else None,
                         "after": e["state"]["after"].holds if e["state"] else None,
                         "accepted_change": e["state"]["accepted_change"] if e["state"] else None}
                        for e in wm.effects_of(world, event, t, as_of, perspective)]}
