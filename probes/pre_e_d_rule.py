"""Increment D design (LABS-1.041, DI-2): the proposed event-role rule for the merged occurrence view, computed from
public readers only (no library change). Shared by probes/pre_e_d_examples.py and probes/pre_e_d_impact.py.
See docs/core-0.4/pre-e-increment-d-design.md, section 3.
"""

from worldmodel import typeql as q
from worldmodel.judgement import Judgement
from worldmodel.semantics import usable

ONE_FOR_ONE = "mechanical:one-for-one"
# (event type, core role, event kind or None): the proposed profile declarations (design section 6)
DECLARED = (("official-act", "actor", None), ("official-act", "office", None), ("official-act", "office-context", None),
            ("replacement", "patient", ONE_FOR_ONE), ("replacement", "fitted", ONE_FOR_ONE))


def scoped_roles(wm, d):
    """{stored role label: (core role, [players])} of a description (e.g. replacement:removed -> patient)."""
    out = {}
    with wm._reading() as tx:
        for r in q.rows(tx, "match $e isa event, has wm-id == $id; $e links ($role: $x); $x has wm-id $xid;",
                        {"id": d}):
            label = r.get("role").get_label()
            out.setdefault(label, (wm.core_role(label), []))[1].append(q.opt(r, "xid"))
    return {k: (c, sorted(v)) for k, (c, v) in out.items()}


def state(recs, perspective, as_of):
    """'accepted', 'disputed', 'denied' or 'not accepted', at the nearest depth with a usable claim (as `_judge`)."""
    use = [a for a in recs if usable(a, perspective, as_of)]
    if not use:
        return "not accepted", None
    depth = min(a.depth for a in use)
    pol = {a.polarity for a in use if a.depth == depth}
    return ("disputed" if len(pol) > 1 else "accepted" if True in pol else "denied"), depth


def proposed_view(wm, world, occ, as_of=None, perspective="system"):
    atts = wm.visible(world, as_of, perspective)
    ident = wm.identity(world, as_of, perspective)
    members = set(ident.members(occ))
    links = {}
    for a in atts.values():
        if a.kind == "describes" and members & set(a.roles.get("occurrence", [])):
            for d in a.roles.get("description", []):
                links.setdefault(d, []).append(a)
    descs = []
    for d, recs in sorted(links.items()):
        link, _ = state(recs, perspective, as_of)
        accounts = [a for a in atts.values() if a.kind == "event" and a.content == d]
        account, depth = state(accounts, perspective, as_of) if accounts else ("none in this world", None)
        starts = [a.start.earliest for a in accounts if usable(a, perspective, as_of) and a.polarity and a.start]
        descs.append({"description": d, "type": wm.content(d)["type"],
                      "attesters": sorted({a.attester for a in accounts}),
                      "link": link, "account": account, "depth": depth, "start": min(starts) if starts else None,
                      "roles": scoped_roles(wm, d)})
    roles = {}
    for x in descs:
        for label, (core, players) in x["roles"].items():
            e = roles.setdefault(label, {"name": label.split(":")[-1], "core_role": core, "players": {}})
            for p in players:
                e["players"].setdefault(p, []).append(x["description"])
    compared = [x for x in descs if x["link"] == "accepted" and x["account"] == "accepted"]
    starts = [x["start"] for x in compared if x["start"] is not None]
    at = min(starts) if starts else None
    judged = {}
    for etype, core, kind in DECLARED:
        group = [x for x in compared if wm.is_a(x["type"], etype)
                 and any(c == core for c, _ in x["roles"].values())]
        if not group:
            continue
        classification = None
        if kind is not None:
            # the kind-scoped constraint applies only where the classification is ESTABLISHED: its canonical record
            # (increment B), for this world, perspective and knowledge time, at the occurrence's start
            rec = wm.judgement(world, "classified-as", {"classified": occ, "class": kind}, at, as_of, perspective) \
                if at is not None else None
            classification = {"at": at.isoformat() if at else None,
                              "judgement": rec.judgement.value if rec else "not judged (no accepted account)",
                              "reasons": list(rec.reasons) if rec else []}
            if rec is None or rec.judgement is not Judgement.ESTABLISHED:
                judged[f"{etype}.{core}"] = {"constraint": f"only as {kind}", "applies": False,
                                             "classification": classification}
                continue
        depth = min(x["depth"] for x in group)
        near = [x for x in group if x["depth"] == depth]
        players = {}
        for x in near:
            for c, ps in x["roles"].values():
                if c == core:
                    for p in ps:
                        players.setdefault(ident.canonical(p), {}).setdefault(p, []).append(
                            (x["description"], x["attesters"]))
        judged[f"{etype}.{core}"] = {
            "constraint": kind or "declared", "applies": True, "classification": classification,
            "judgement": "disputed" if len(players) > 1 else "established",
            "players": [{"names": sorted(names), "cited": sorted({c for v in names.values() for c, _ in v})}
                        for _, names in sorted(players.items())],
            "overridden": sorted(x["description"] for x in group if x["depth"] != depth)}
    return {"descriptions": [{k: v for k, v in x.items() if k not in ("roles", "start")} for x in descs],
            "roles": dict(sorted(roles.items())),
            "judged": judged}
