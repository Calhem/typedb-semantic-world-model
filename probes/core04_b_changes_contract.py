"""LABS-1.014 probe: can `changes` report state transitions whose valid time intersects a requested interval,
unambiguously, from the existing data model? Each case builds a small world (throwaway databases wm-chg-*) and prints
the judged state at the relevant instants and what changes() reports today. No model code is changed.

    uv run python -I probes/core04_b_changes_contract.py > probes/core04_b_changes_contract.out.json
"""

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import DYNAMICS_MODULES, WorldModel  # noqa: E402
from worldmodel.examples import gearbox as g  # noqa: E402


def T(h, m=0, day=9):
    return datetime(2026, 11, day, h, m, tzinfo=timezone.utc)


def fresh():
    wm = WorldModel.create(f"wm-chg-{uuid.uuid4().hex[:8]}", modules=DYNAMICS_MODULES)
    w = wm.create_world("actual", id="actual")
    for kind, n in (("physical-object", "box"), ("place", "a"), ("place", "b"), ("social-object", "cam"),
                    ("physical-object", "tech")):
        wm.add_entity(kind, n, id=n)
    return wm, w


def where(wm, w, t, **kw):
    a = wm.value_at(w, "located-at", "box", t, **kw)
    return f"{a.status.value} {list(a.values)}"


def summary(c):
    return {"began": [x["roles"].get("place") for x in c["began"]], "ended": [x["roles"].get("place") for x in c["ended"]],
            "claimed_events": {str(x["roles"].get("place")): [e["event"] for e in x["claimed_events"]]
                               for x in c["began"] + c["ended"]}}


out = {}
dbs = []
try:
    # 1. a state that begins and ends inside the interval (and a value that returns to its starting value)
    wm, w = fresh(); dbs.append(wm)
    wm.attest(w, "located-at", {"located": "box", "place": "a"}, start=T(9), end=T(10))
    wm.attest(w, "located-at", {"located": "box", "place": "b"}, start=T(10), end=T(11))
    wm.attest(w, "located-at", {"located": "box", "place": "a"}, start=T(11), until_superseded=True)
    out["1 transitions entirely inside [09:30, 12:00]"] = {
        "judged": {t: where(wm, w, T(*map(int, t.split(":")))) for t in ("9:30", "10:30", "12:00")},
        "changes() today": summary(wm.changes(w, "box", T(9, 30), T(12)))}
    # 2. an uncertain start window that straddles the interval's start
    wm, w = fresh(); dbs.append(wm)
    wm.attest(w, "located-at", {"located": "box", "place": "a"}, start=T(8), end=(T(10), T(10, 20)))
    wm.attest(w, "located-at", {"located": "box", "place": "b"}, start=(T(10), T(10, 20)), until_superseded=True)
    out["2 a transition known only within [10:00, 10:20], interval [10:15, 11:00]"] = {
        "judged": {t: where(wm, w, T(*map(int, t.split(":")))) for t in ("9:59", "10:05", "10:15", "10:20")},
        "note": "the move happened at some time in [10:00, 10:20]; it may or may not lie in [10:15, 11:00]"}
    # 3. a state whose end is unknown (no stated end, not until superseded)
    wm, w = fresh(); dbs.append(wm)
    wm.attest(w, "located-at", {"located": "box", "place": "a"}, start=T(9))
    out["3 a state with an unknown end"] = {
        "judged": {t: where(wm, w, T(*map(int, t.split(":")))) for t in ("9:00", "9:01", "12:00")},
        "changes() today [08:00, 12:00]": summary(wm.changes(w, "box", T(8), T(12))),
        "note": "true at its start instant, undecided after: is true -> unknown an 'ended' transition?"}
    # 4. a state that becomes disputed inside the interval (no one ends it)
    wm, w = fresh(); dbs.append(wm)
    wm.attest(w, "located-at", {"located": "box", "place": "a"}, start=T(9), until_superseded=True)
    wm.accept(wm.attest(w, "located-at", {"located": "box", "place": "b"}, start=T(10), until_superseded=True,
                        attester="cam"))
    out["4 a rival claim accepted from 10:00"] = {
        "judged": {t: where(wm, w, T(*map(int, t.split(":")))) for t in ("9:30", "10:30")},
        "changes() today [09:30, 10:30]": summary(wm.changes(w, "box", T(9, 30), T(10, 30))),
        "note": "a -> disputed(a, b): neither 'a ended' nor 'b began' is accepted; is it a transition?"}
    # 5. which event explains which transition: a content that begins twice, with an event for the second only
    wm, w = fresh(); dbs.append(wm)
    for o in ("o-move-1", "o-move-2"):
        wm.add_entity("occurrence", o, id=o)
    wm.attest(w, "located-at", {"located": "box", "place": "a"}, start=T(8), end=T(9))
    wm.attest(w, "located-at", {"located": "box", "place": "b"}, start=T(9), end=T(13))
    wm.attest(w, "located-at", {"located": "box", "place": "a"}, start=T(13), until_superseded=True)
    e2 = wm.account(w, {"actor": "tech", "patient": "box"}, T(12, 50), T(13), occurrence="o-move-2", id="ev-move-2")
    wm.claim_effect(w, e2, "initiates", "located-at", {"located": "box", "place": "a"})
    out["5 'box at a' begins at 08:00 (no event) and again at 13:00 (ev-move-2)"] = {
        "changes() today [07:00, 08:30]": summary(wm.changes(w, "box", T(7), T(8, 30))),
        "note": "ev-move-2 (12:50-13:00) is listed for a transition at 08:00 that it cannot explain"}
    # 6. a delayed effect: the event ends at 10:00, the state it is claimed to initiate starts at 10:45
    wm, w = fresh(); dbs.append(wm)
    wm.add_entity("occurrence", "o-order", id="o-order")
    wm.attest(w, "located-at", {"located": "box", "place": "a"}, start=T(8), end=T(10, 45))
    wm.attest(w, "located-at", {"located": "box", "place": "b"}, start=T(10, 45), until_superseded=True)
    e = wm.account(w, {"actor": "tech", "patient": "box"}, T(9, 50), T(10), occurrence="o-order", id="ev-order")
    wm.claim_effect(w, e, "initiates", "located-at", {"located": "box", "place": "b"})
    out["6 delayed effect: event 09:50-10:00, state from 10:45; interval [10:30, 11:00]"] = {
        "changes() today": summary(wm.changes(w, "box", T(10, 30), T(11))),
        "note": "event before the interval, transition inside: allowed as provenance (supported)"}
finally:
    for m in dbs:
        m.driver.databases.get(m.database).delete()
print(json.dumps(out, indent=1, default=str))
