"""Stage E1 evaluation (LABS-1.051): load a benchmark fixture into its own TypeDB database through public writers.

A fixture (benchmark/e1/fixtures/<scenario>.json, format in benchmark/e1/README.md) lists what was said and by whom.
`load(fixture)` creates a fresh database (`wm-eval-<scenario>-<random>`, deleted by `drop`), installs the core and
the fixture's profiles, and runs its steps in order with the library's public writer functions. It never calls a
reader. It returns a Loaded record: the model, the knowledge-time marks and the attestation ids of each step.

Stage E2 harness (LABS-1.061, GAP-HARNESS-1 and -2): `attest`, `deny` and `correct` accept `params`, and the steps
position, relate_frames, anchor_frame, define_unit, define_quality_kind, measure, claim_cause, claim_effect,
describe_occurrence, record_event, declare_existence, create_thing, destroy and interpret call the public writers of
the same names. A step that refers to an earlier step's attestation (`supersedes`, `ends`) names that step; an effect
claim names its proposition by content (type, roles, params), so a fixture never needs a proposition id. E1 fixtures
use none of these, so they load exactly as before.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from worldmodel import CORE_MODULES, WorldModel, connect
from worldmodel import laboratory as lab, mechanical as mech, organisation as org

PREFIX = "wm-eval-"
FIXTURES = Path(__file__).resolve().parents[1] / "benchmark" / "e1" / "fixtures"
INTERVAL = ("start", "end", "until_superseded")
COMMON = {"op", "id", "accepted_by"}


class FixtureError(ValueError):
    """A fixture step is malformed or names something that does not exist."""


class Clock:
    """Deterministic transaction time: 2030-01-01 00:00 UTC, one second later on every call."""

    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


def T(spec):
    """'T<d>' -> 2026-11-<d> 09:00 UTC; 'T<d>h<hh>' sets the hour."""
    if not isinstance(spec, str) or not spec.startswith("T"):
        raise FixtureError(f"not a valid time: {spec!r} (use 'T<d>' or 'T<d>h<hh>')")
    day, _, hour = spec[1:].partition("h")
    try:
        return datetime(2026, 11, int(day), int(hour or 9), tzinfo=timezone.utc)
    except ValueError as e:
        raise FixtureError(f"not a valid time: {spec!r}: {e}") from None


@dataclass
class Loaded:
    scenario: str
    wm: WorldModel
    marks: dict = field(default_factory=dict)          # name -> knowledge time
    written: dict = field(default_factory=dict)        # step id -> attestation ids it wrote (evidence names)

    def at(self, spec):
        """A knowledge time: '@mark' -> its time; None -> None."""
        if spec is None:
            return None
        if not (isinstance(spec, str) and spec.startswith("@") and spec[1:] in self.marks):
            raise FixtureError(f"unknown knowledge time {spec!r}; marks: {sorted(self.marks)}")
        return self.marks[spec[1:]]

    def evidence_names(self):
        """attestation id -> the step id that wrote it."""
        return {a: sid for sid, atts in self.written.items() for a in atts}


def read_fixture(path_or_id):
    p = Path(path_or_id)
    if not p.exists():
        p = FIXTURES / f"{path_or_id}.json"
    return json.loads(p.read_text())


def _interval(step, need_start=False):
    out = {}
    if "start" in step:
        out["start"] = T(step["start"])
    elif need_start:
        raise FixtureError(f"step {step.get('id')!r}: needs a start")
    if "end" in step:
        out["end"] = T(step["end"])
    if step.get("until_superseded"):
        out["until_superseded"] = True
    return out


def _one(loaded, step, key):
    """The single attestation written by the step named by step[key]."""
    old = loaded.written.get(step[key])
    if not old or len(old) != 1:
        raise FixtureError(f"step {step.get('id')!r}: {key} {step[key]!r} must name a step that wrote one attestation")
    return old[0]


def _time_or_none(step, key):
    return T(step[key]) if key in step else None


def _check_keys(step, allowed):
    extra = set(step) - COMMON - set(allowed)
    if extra:
        raise FixtureError(f"step {step.get('id')!r} ({step['op']}): unknown fields {sorted(extra)}")


def load(fixture, driver=None):
    """Load a fixture (dict, path or scenario id) into a fresh database. Returns a Loaded record."""
    fx = fixture if isinstance(fixture, dict) else read_fixture(fixture)
    driver = driver or connect()
    name = f"{PREFIX}{fx['id']}-{uuid.uuid4().hex[:8]}"
    wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=Clock())
    loaded = Loaded(fx["id"], wm)
    try:
        for p in fx.get("profiles", []):
            wm.install_profile(p)
        for step in fx["steps"]:
            _run(loaded, step)
    except BaseException:
        drop(loaded)
        raise
    return loaded


def drop(loaded):
    d = loaded.wm.driver
    if d.databases.contains(loaded.wm.database):
        d.databases.get(loaded.wm.database).delete()


def _accept(loaded, step, ids):
    for holder in step.get("accepted_by", []):
        for a in ids:
            loaded.wm.accept(a, holder=holder)


def _account_ids(loaded, world, description):
    return list(loaded.wm.account_attestations(world, description))


def _run(loaded, s):
    wm, op, sid = loaded.wm, s.get("op"), s.get("id")
    attester = s.get("attester", "system")
    if op == "entity":
        _check_keys(s, ("kind", "name"))
        if s["kind"] == "capability":
            wm.define_capability(s.get("name", sid), id=sid)
        else:
            wm.add_entity(s["kind"], s.get("name", sid), id=sid)
        return
    if op == "world":
        _check_keys(s, ("kind", "base", "branch_at", "knowledge_at", "name"))
        kw = {}
        if s.get("base"):
            kw["base"] = s["base"]
        if s.get("branch_at"):
            kw["branch_at"] = T(s["branch_at"])
        if s.get("knowledge_at"):
            kw["knowledge_at"] = loaded.at(s["knowledge_at"])
        wm.create_world(s.get("name", sid), kind=s.get("kind", "actual"), id=sid, **kw)
        return
    if op == "mark":
        _check_keys(s, ("name",))
        loaded.marks[s["name"]] = wm.clock.now
        return
    if op == "accept":
        _check_keys(s, ("target", "holder", "verdict"))
        targets = loaded.written.get(s["target"])
        if not targets:
            raise FixtureError(f"accept: unknown target {s['target']!r}")
        for a in targets:
            wm.accept(a, verdict=s.get("verdict", "accepted"), holder=s.get("holder", "system"))
        return
    ids = []
    if op in ("attest", "deny"):
        _check_keys(s, ("world", "type", "roles", "params", "attester", "stance") + INTERVAL)
        kw = {"attester": attester, **_interval(s)}
        if s.get("stance"):
            kw["stance"] = s["stance"]
        if s.get("params") is not None:
            kw["params"] = s["params"]
        if op == "deny":
            kw["polarity"] = False
        ids = [wm.attest(s["world"], s["type"], s["roles"], id=sid, **kw)]
    elif op == "end":
        _check_keys(s, ("world", "target", "at"))
        old = loaded.written.get(s["target"])
        if not old or len(old) != 1:
            raise FixtureError(f"end: target {s['target']!r} must name one attestation")
        ids = [wm.end(s["world"], old[0], T(s["at"]))]
    elif op == "correct":
        _check_keys(s, ("world", "target", "type", "roles", "params", "attester", "stance") + INTERVAL)
        old = loaded.written.get(s["target"])
        if not old or len(old) != 1:
            raise FixtureError(f"correct: target {s['target']!r} must name one attestation")
        kw = {"attester": attester, **_interval(s)}
        if s.get("params") is not None:
            kw["params"] = s["params"]
        ids = [wm.attest(s["world"], s["type"], s["roles"], id=sid, supersedes=old[0], **kw)]
    elif op == "account":
        _check_keys(s, ("world", "roles", "start", "end", "type", "kind", "occurrence", "attester"))
        wm.account(s["world"], s["roles"], T(s["start"]), T(s["end"]) if "end" in s else None, kind=s.get("kind"),
                   occurrence=s.get("occurrence"), attester=attester, id=sid, type=s.get("type", "event"))
        ids = _account_ids(loaded, s["world"], sid)
    elif op == "move":
        _check_keys(s, ("world", "thing", "to", "at", "actor", "attester"))
        eid, effects = wm.move(s["world"], s["thing"], s["to"], T(s["at"]), actor=s.get("actor"), attester=attester)
        ids = _account_ids(loaded, s["world"], eid) + list(effects)
    elif op == "grant":
        _check_keys(s, ("world", "holder", "concept", "context", "polarity", "attester") + INTERVAL)
        ids = [wm.grant(s["world"], s["holder"], s["concept"], context=s.get("context"),
                        polarity=s.get("polarity", True), attester=attester, id=sid, **_interval(s))]
    elif op == "depend":
        _check_keys(s, ("world", "dependent", "dependee", "kind", "attester") + INTERVAL)
        ids = [wm.depend(s["world"], s["dependent"], s["dependee"], kind=s.get("kind"), attester=attester, id=sid,
                         **_interval(s))]
    elif op == "appoint":
        _check_keys(s, ("world", "holder", "office", "context", "polarity", "attester") + INTERVAL)
        ids = [org.appoint(wm, s["world"], s["holder"], s["office"], s["context"], polarity=s.get("polarity", True),
                           attester=attester, id=sid, **_interval(s))]
    elif op == "declare_exclusive":
        _check_keys(s, ("world", "office", "context", "attester") + INTERVAL)
        ids = [org.declare_exclusive(wm, s["world"], s["office"], s["context"], attester=attester, id=sid,
                                     **_interval(s))]
    elif op == "authorise":
        _check_keys(s, ("world", "grantor", "holder", "power", "scope", "polarity", "attester") + INTERVAL)
        ids = [org.authorise(wm, s["world"], s["grantor"], s["holder"], s["power"], s["scope"], attester=attester,
                             polarity=s.get("polarity", True), id=sid, **_interval(s))]
    elif op == "employ":
        _check_keys(s, ("world", "employer", "employee", "polarity", "attester") + INTERVAL)
        ids = [org.employ(wm, s["world"], s["employer"], s["employee"], polarity=s.get("polarity", True),
                          attester=attester, id=sid, **_interval(s))]
    elif op == "act_in_office":
        _check_keys(s, ("world", "official", "office", "context", "start", "end", "occurrence", "kind", "attester"))
        org.act_in_office(wm, s["world"], s["official"], s["office"], s["context"], T(s["start"]),
                          T(s["end"]) if "end" in s else None, occurrence=s.get("occurrence"), attester=attester,
                          id=sid, kind=s.get("kind"))
        ids = _account_ids(loaded, s["world"], sid)
    elif op == "connect":
        _check_keys(s, ("world", "a", "b", "joint_kind", "attester") + INTERVAL)
        ids = [mech.connect(wm, s["world"], s["a"], s["b"], joint_kind=s.get("joint_kind"), attester=attester, id=sid,
                            **_interval(s))]
    elif op == "replace_part":
        _check_keys(s, ("world", "assembly", "removed", "fitted", "start", "end", "occurrence", "attester"))
        r = mech.replace_part(wm, s["world"], s["assembly"], s["removed"], s["fitted"], T(s["start"]),
                              T(s["end"]) if "end" in s else None, occurrence=s.get("occurrence"), attester=attester,
                              id=sid)
        ids = _account_ids(loaded, s["world"], sid) + list(r["effects"])
    elif op == "take_sample":
        _check_keys(s, ("world", "sampler", "specimen", "sample", "start", "end", "occurrence", "kind", "attester"))
        r = lab.take_sample(wm, s["world"], s["sampler"], s["specimen"], s["sample"], T(s["start"]),
                            T(s["end"]) if "end" in s else None, occurrence=s.get("occurrence"), attester=attester,
                            id=sid, kind=s.get("kind"))
        ids = _account_ids(loaded, s["world"], sid) + list(r["effects"])
    elif op == "certificate":
        _check_keys(s, ("name", "reference"))
        lab.register_certificate(wm, s.get("name", sid), reference=s.get("reference"), id=sid)
        return
    elif op == "calibrate":
        _check_keys(s, ("world", "certificate", "instrument", "polarity", "attester") + INTERVAL)
        iv = _interval(s)
        ids = [lab.calibrate(wm, s["world"], s["certificate"], s["instrument"], start=iv.pop("start", None),
                             end=iv.pop("end", None), attester=attester, polarity=s.get("polarity", True), id=sid,
                             **iv)]
    elif op in E2_OPS:
        ids = E2_OPS[op](loaded, s, attester)
        if ids is None:                                  # a definition: no attestation, nothing to name
            return
    else:
        raise FixtureError(f"unknown op {op!r} in step {sid!r}")
    if sid in loaded.written:
        raise FixtureError(f"duplicate step id {sid!r}")
    loaded.written[sid] = [a for a in ids if a]
    _accept(loaded, s, loaded.written[sid])


# ---- Stage E2 fixture steps (LABS-1.061, GAP-HARNESS-2); each returns the attestation ids it wrote, or None --------
def _axis(v):
    return tuple(v) if isinstance(v, list) else v


def _op_position(L, s, attester):
    _check_keys(s, ("world", "thing", "frame", "x", "y", "z", "orientation", "attester") + INTERVAL)
    o = s.get("orientation")
    return [L.wm.position(s["world"], s["thing"], s["frame"], _axis(s["x"]), _axis(s["y"]), _axis(s["z"]),
                          orientation=tuple(o) if o is not None else None, attester=attester, id=s["id"],
                          **_interval(s))]


def _op_relate_frames(L, s, attester):
    _check_keys(s, ("world", "parent", "child", "translation", "rotation", "attester") + INTERVAL)
    return [L.wm.relate_frames(s["world"], s["parent"], s["child"], tuple(s["translation"]),
                               tuple(s.get("rotation", (1.0, 0.0, 0.0, 0.0))), attester=attester, id=s["id"],
                               **_interval(s))]


def _op_anchor_frame(L, s, attester):
    _check_keys(s, ("world", "frame", "anchor", "attester") + INTERVAL)
    return [L.wm.anchor_frame(s["world"], s["frame"], s["anchor"], attester=attester, id=s["id"], **_interval(s))]


def _op_define_unit(L, s, attester):
    _check_keys(s, ("name", "dimension", "si_factor", "si_offset"))
    L.wm.define_unit(s.get("name", s["id"]), s["dimension"], si_factor=s.get("si_factor", 1.0),
                     si_offset=s.get("si_offset", 0.0), id=s["id"])
    return None


def _op_define_quality_kind(L, s, attester):
    _check_keys(s, ("name", "dimension"))
    L.wm.define_quality_kind(s.get("name", s["id"]), dimension=s.get("dimension"), id=s["id"])
    return None


def _op_measure(L, s, attester):
    _check_keys(s, ("world", "bearer", "quality", "value", "unit", "uncertainty", "k", "start", "end", "instrument",
                    "operator", "conditions", "calibration", "attester", "occurrence", "persists", "supersedes"))
    r = L.wm.measure(s["world"], s["bearer"], s["quality"], s["value"], s["unit"], s["uncertainty"], k=s.get("k", 2.0),
                     start=T(s["start"]), end=_time_or_none(s, "end"), instrument=s.get("instrument"),
                     operator=s.get("operator"), conditions=tuple(s.get("conditions", ())),
                     calibration=s.get("calibration"), attester=attester, occurrence=s.get("occurrence"),
                     persists=s.get("persists", False),
                     supersedes=_one(L, s, "supersedes") if "supersedes" in s else None, id=s["id"])
    # the reported content first: it is what a measurement answer cites; then the activity's account and links
    return [r["content"]] + _account_ids(L, s["world"], r["activity"]) + [r["produced"], r["reports"]]


def _op_claim_cause(L, s, attester):
    _check_keys(s, ("world", "cause", "effect", "polarity", "attester") + INTERVAL)
    return [L.wm.claim_cause(s["world"], s["cause"], s["effect"], polarity=s.get("polarity", True), attester=attester,
                             id=s["id"], **_interval(s))]


def _op_claim_effect(L, s, attester):
    _check_keys(s, ("world", "event", "kind", "type", "roles", "params", "polarity", "attester") + INTERVAL)
    return [L.wm.claim_effect(s["world"], s["event"], s["kind"], s["type"], s["roles"], params=s.get("params"),
                              polarity=s.get("polarity", True), attester=attester, id=s["id"], **_interval(s))]


def _op_describe_occurrence(L, s, attester):
    _check_keys(s, ("world", "description", "occurrence", "polarity", "attester") + INTERVAL)
    return [L.wm.describe_occurrence(s["world"], s["description"], s["occurrence"], polarity=s.get("polarity", True),
                                     attester=attester, id=s["id"], **_interval(s))]


def _op_record_event(L, s, attester):
    _check_keys(s, ("world", "roles", "start", "end", "kind", "ends", "effects", "type", "attester"))
    ends = [_one(L, {"id": s["id"], "e": e}, "e") for e in s.get("ends", [])]
    eid, effects = L.wm.record_event(s["world"], s["roles"], T(s["start"]), _time_or_none(s, "end"), kind=s.get("kind"),
                                     ends=ends, effects=s.get("effects", ()), attester=attester, id=s["id"],
                                     type=s.get("type", "event"))
    return _account_ids(L, s["world"], eid) + list(effects)


def _op_declare_existence(L, s, attester):
    _check_keys(s, ("world", "thing", "start", "end", "attester"))
    return [L.wm.declare_existence(s["world"], s["thing"], start=_time_or_none(s, "start"), end=_time_or_none(s, "end"),
                                   attester=attester, id=s["id"])]


def _op_create_thing(L, s, attester):
    _check_keys(s, ("world", "kind", "name", "at", "alt_names", "attester"))
    rid = L.wm.create_thing(s["world"], s["kind"], s.get("name", s["id"]), T(s["at"]),
                            alt_names=tuple(s.get("alt_names", ())), attester=attester, id=s["id"])
    return [h["attestation"] for h in L.wm.history(s["world"], rid) if L.wm.is_a(h["type"], "existence")]


def _op_destroy(L, s, attester):
    _check_keys(s, ("world", "thing", "at", "reason"))
    return list(L.wm.destroy(s["world"], s["thing"], T(s["at"]), reason=s.get("reason")))


def _op_interpret(L, s, attester):
    _check_keys(s, ("world", "record", "type", "roles", "params", "tentative", "polarity", "attester") + INTERVAL)
    return [lab.interpret(L.wm, s["world"], s["record"], s["type"], s["roles"], attester,
                          tentative=s.get("tentative", False), polarity=s.get("polarity", True), params=s.get("params"),
                          id=s["id"], **_interval(s))]


E2_OPS = {"position": _op_position, "relate_frames": _op_relate_frames, "anchor_frame": _op_anchor_frame,
          "define_unit": _op_define_unit, "define_quality_kind": _op_define_quality_kind, "measure": _op_measure,
          "claim_cause": _op_claim_cause, "claim_effect": _op_claim_effect,
          "describe_occurrence": _op_describe_occurrence, "record_event": _op_record_event,
          "declare_existence": _op_declare_existence, "create_thing": _op_create_thing, "destroy": _op_destroy,
          "interpret": _op_interpret}
