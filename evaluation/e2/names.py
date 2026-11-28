"""Stage E2 harness: deterministic fixture-level names for every attestation a loaded fixture recorded (H-1, P-2,
approved LABS-1.063).

Evidence is named by fixture step, never by attestation id. After loading, every attestation a step wrote is named
from the step and from the record's own structure. Nothing here depends on a run, on a reader or on random ids:

| Attestation | Name |
|---|---|
| the step's own single claim | `<step>` |
| an event description's occurrence interval (account, record_event, act_in_office, replace_part, take_sample, move) | `<step>` |
| the activity of a measurement | `<step>/activity` |
| the reported content of a measurement | `<step>` |
| a classification of an event description | `<step>/kind:<category>` |
| a describes link written with an account | `<step>/describes` |
| `produced`, `reports` of a measurement | `<step>/produced`, `<step>/reports` |
| an effect written by the step | `<step>/effect:<n>` (n from 0, in the order the writer returned them) |
| a denial written by `destroy` of another attester's claim, step X | `<step>/denied:<X>` |
| a restatement of step X by the library (same attester, content, start and world: end(), move(), destroy()) | `X` (E1 C3, approved LABS-1.053); also listed in `restatements` as `<step>/ended:<X>` |

Any attestation that still has no name is **unattributed**. `recorded` is every attestation visible in the fixture's
worlds to any of its attesters, which is used to tell an unattributed id from one the scenario never recorded.
"""

EVENT_OPS = {"account", "record_event", "act_in_office", "replace_part", "take_sample", "move"}


def _records(L, fixture):
    worlds = [s["id"] for s in fixture["steps"] if s.get("op") == "world"]
    who = {s.get("attester", "system") for s in fixture["steps"]} | {"system"}
    who |= {h for s in fixture["steps"] for h in s.get("accepted_by", [])}
    recs = {}
    for w in worlds:
        for p in sorted(who):
            try:
                recs.update(L.wm.visible(w, perspective=p))
            except Exception:                                 # a perspective with nothing to see
                continue
    return recs


def fixture_names(L, fixture):
    """(names: attestation id -> fixture-level name, restatements: id -> '<step>/ended:<X>', recorded: set of ids)."""
    recs = _records(L, fixture)
    ops = {s.get("id"): s.get("op") for s in fixture["steps"]}
    names = {}
    for sid, ids in L.written.items():
        op = ops.get(sid)
        if op == "destroy":                                  # named below: restatements and denials
            continue
        if len(ids) == 1 and op not in EVENT_OPS | {"measure"}:
            names[ids[0]] = sid                              # includes end and correct: their own step (P-2)
            continue
        effects = 0
        for a in ids:
            r = recs.get(a)
            kind = r.kind if r is not None else None
            if kind == "event":
                name = f"{sid}/activity" if op == "measure" else sid
            elif op == "measure" and kind == "has-quality":
                name = sid
            elif kind == "classified-as":
                name = f"{sid}/kind:{(r.roles.get('class') or ['?'])[0]}"
            elif kind == "describes":
                name = f"{sid}/describes"
            elif op == "measure" and kind in ("produced", "reports"):
                name = f"{sid}/{kind}"
            else:
                name = f"{sid}/effect:{effects}"
                effects += 1
            while name in names.values():                    # never two attestations under one name
                name += "+"
            names[a] = name
    # library restatements (C3: same attester, content, start and world as a named claim), then destroy's denials
    sig = lambda r: (r.attester, r.content, r.start, r.world)
    by_sig = {sig(recs[a]): n for a, n in names.items() if a in recs and "/" not in n}
    by_content = {}
    for a, n in names.items():
        if a in recs and "/" not in n:
            by_content.setdefault(recs[a].content, n)
    writer = {a: sid for sid, ids in L.written.items() for a in ids}
    restatements = {}
    for a, r in sorted(recs.items()):
        if a in names:
            continue
        if sig(r) in by_sig:
            names[a] = by_sig[sig(r)]
            if a in writer:
                restatements[a] = f"{writer[a]}/ended:{by_sig[sig(r)]}"
        elif ops.get(writer.get(a)) == "destroy" and r.content in by_content:
            names[a] = f"{writer[a]}/denied:{by_content[r.content]}"
    return names, restatements, set(recs)
