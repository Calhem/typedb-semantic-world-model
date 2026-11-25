"""Stage E2 harness: reader templates (GAP-HARNESS-3).

Each template names a public reader, the parameters a question gives it, how it is called, and two extractors that
work on the reader's normalised answer (values.normalise):
- `evidence`: the attestation ids the answer cites as **supporting** evidence. Material the answer lists without
  resting on it (alternatives, pending or unreviewed claims, incomparable statements, unaccepted measurements) is not
  supporting, so it is never cited.
- `derivations`: the derivations the answer **presents**: a named rule with its premises (for example a pose derived
  through a frame chain under `frame-transform/v1`). The scorer checks that every one is recorded (rule known,
  premises recorded attestations): a derivation that is not is fabricated (E2-D6, "no fabricated derivations").

**Provisional:** these extractors are the harness's reading of the readers' documented outputs. The E2 reader
contracts (E2-D3, not written yet) must confirm or correct each one before any question is authored; a change there is
a change to this table, not to a reader.

Common parameters: `world` (required, except `convert`), `t`, `as_of`, `perspective`. Times are 'T<d>[h<hh>]'
fixture times, or ISO 8601 strings (as earlier plan steps give them); `as_of` is '@mark' or an ISO string.

**Refusals (LABS-1.062).** Only a reader's **documented** refusals are refusals: each template lists them (`refusals`),
each with the exception it raises, the message it matches, its source and whether that source is an approved design
decision (`established`). A documented refusal gives the answer {"refused": true, "refusal": <name>, "established":
bool, "message": ...}. Any other exception, including an undocumented ValueError, is an execution error. A gap probe
accepts only an established refusal (score.probe).
"""

import re

from dataclasses import dataclass, field

from worldmodel import laboratory as lab, organisation as org
from worldmodel.physical import RULE as FRAME_RULE

KNOWN_RULES = {FRAME_RULE}                    # the derivation rules the model records (DI-7: no general rule record)
COMMON = ("world", "t", "as_of", "perspective")
@dataclass(frozen=True)
class Refusal:
    name: str                                  # e.g. "unknown-role"
    exception: type
    pattern: str                               # regex the message must match (search)
    source: str                                # where the refusal is documented
    established: bool                          # an approved design decision (True) or documented only by the reader


def documented_refusal(r, exc):
    """The template's Refusal that `exc` is, or None (then it is an execution error)."""
    for ref in r.refusals:
        if isinstance(exc, ref.exception) and re.search(ref.pattern, str(exc)):
            return ref
    return None
# keys under which an answer lists material it does not rest on (as E1's usable_evidence, plus E2's readers)
NOT_SUPPORT = {"pending", "alternatives", "only_in", "not_traversed", "accounts", "descriptions",
               "superseded_by_source", "incomparable", "statements"}
UNUSABLE = {"unreviewed", "rejected", "retracted", "superseded"}


@dataclass(frozen=True)
class Reader:
    name: str
    required: tuple
    optional: tuple
    call: object                               # (wm, p) -> raw answer; p holds the coerced parameters
    evidence: object = None                    # normalised answer -> set of attestation ids
    derivations: object = None                 # normalised answer -> [{"rule", "premises", "at"}]
    refusals: tuple = ()                       # documented refusals (Refusal)
    timeless: bool = False                     # no t parameter
    worldless: bool = False                    # no world parameter (convert)
    notes: str = ""
    extra: dict = field(default_factory=dict)


def _ctx(p):
    return {"as_of": p.get("as_of"), "perspective": p.get("perspective", "system")}


def _ids(v):
    return {x for x in (v or []) if isinstance(x, str)}


def usable_evidence(x):
    """Evidence entries ({"attestation": id, "acceptance": ...}) a perspective can use, anywhere under x, except under
    keys that list non-supporting material."""
    out = set()

    def walk(v, key=None):
        if key in NOT_SUPPORT:
            return
        if isinstance(v, dict):
            if isinstance(v.get("attestation"), str) and v.get("acceptance") not in UNUSABLE:
                out.add(v["attestation"])
            for k, w in v.items():
                walk(w, k)
        elif isinstance(v, list):
            for w in v:
                walk(w, key)
    walk(x)
    return out


def deciding(r, entries_key):
    """As E1: an applicability answer's `support`, or the usable evidence of the entries it reports as applicable."""
    if r.get("support"):
        return set(r["support"])
    return set().union(set(), *(usable_evidence(e) for e in r.get(entries_key, [])))


def generic_derivations(x, at=""):
    """Any object presenting {"rule": <name>, "premises": [...]} (the shape a recorded derivation would take)."""
    out = []
    if isinstance(x, dict):
        if isinstance(x.get("rule"), str) and isinstance(x.get("premises"), list):
            out.append({"rule": x["rule"], "premises": [str(p) for p in x["premises"]], "at": at or "answer"})
        for k, v in x.items():
            out += generic_derivations(v, f"{at}.{k}" if at else k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            out += generic_derivations(v, f"{at}[{i}]")
    return out


# ---- evidence and derivation extractors ------------------------------------------------------------------------------
def ev_answer(a):                             # an Answer: holds()
    return _ids(a.get("support")) | _ids(a.get("conflicts")) | {
        x for c in a.get("constraint_support") or [] for x in c.get("support", [])}


def ev_support(a):
    return _ids(a.get("support"))


def ev_list_support(a):
    return {x for e in a for x in e.get("support", [])}


def ev_where(a):
    return {x for c in a["candidates"] for x in c.get("position_support", [])} | {
        x for c in a["candidates"] for s in c.get("chain") or [] for x in s.get("support", [])}


def dv_where(a):
    out = []
    for i, c in enumerate(a["candidates"]):
        if c.get("rule"):
            out.append({"rule": c["rule"], "at": f"candidates[{i}]",
                        "premises": sorted(set(c.get("position_support", [])) |
                                           {x for s in c.get("chain") or [] for x in s.get("support", [])})})
    return out


def ev_chain(a):
    return {x for s in a.get("chain") or [] for x in s.get("support", [])}


def dv_transform(a):
    if a.get("transform") is None or not a.get("chain"):
        return []
    return [{"rule": a.get("rule"), "at": "transform", "premises": sorted(ev_chain(a))}]


def ev_frame_info(a):
    return {x for k in ("parents", "children") for e in a.get(k, []) for x in e.get("support", [])}


def ev_measurements(a):
    return {m["attestation"] for m in a if m.get("usable")}


def ev_compare(a):
    return {m["attestation"] for m in a.get("measurements", [])}


def ev_measurement_calibration(rows):
    out = set()
    for r in rows:
        if r.get("usable"):
            out.add(r["attestation"])
        if r.get("attested"):
            out |= deciding(r["attested"], "certificates")
    return out


def ev_claims(claims, accepted="judgement"):
    return set().union(set(), *(usable_evidence(c.get("attestations", [])) for c in claims
                                if c.get(accepted) == "accepted"))


def ev_effects(a):
    out = ev_claims(a, "claim")
    for e in a:
        for side in ("before", "after"):
            out |= _ids(((e.get("state") or {}).get(side) or {}).get("support"))
    return out


def ev_explain(a):
    return _ids((a.get("holds") or {}).get("support")) | set().union(
        set(), *(ev_claims(i.get("causes", [])) for i in a.get("initiated_by", [])))


def ev_changes(a):
    return {x for tr in a.get("transitions", []) for side in ("before", "after")
            for x in (tr.get(side) or {}).get("support", [])}


def ev_occurrence_status(a):
    return _ids((a.get("answer") or {}).get("support"))


def ev_office_holders(r):
    cited = set().union(set(), *(usable_evidence(a) for a in r.get("appointments", [])
                                 if a.get("judgement") == "established"))
    for a in (r.get("conflict") or {}).get("appointments", []):
        cited |= _ids(a.get("attestations"))
    cited |= _ids(((r.get("conflict") or {}).get("constraint") or {}).get("support"))
    return cited


def ev_interval(a):
    return {a["attestation"]} if a and a.get("attestation") else set()


def _interval(wm, p):
    r = wm.interval(p["world"], p["description"], **_ctx(p))
    return None if r is None else {"start": r[0], "end": r[1], "attestation": r[2].id}


def _t(p):
    return p.get("t")


from worldmodel import UnknownRoleError  # noqa: E402

UNKNOWN_ROLE = Refusal("unknown-role", UnknownRoleError, "", "e1-reconciliation-design.md R2 (approved LABS-1.053)",
                       True)
CROSS_DIMENSION = Refusal("cross-dimension", ValueError, r"^cannot convert ", "stage-c.md (convert: refused across "
                          "dimensions)", True)
UNKNOWN_UNIT = Refusal("not-a-unit", ValueError, r"is not a unit with a dimension$", "convert docstring and qualities "
                       "implementation only (no design statement found)", False)
NO_SINGLE_SLOT = Refusal("no-single-slot", ValueError, r"one-role functional constraints",
                         "value_at implementation (message); A0.3 slots design to confirm", False)


READERS = {r.name: r for r in [
    # family S, F
    Reader("transform_between", ("source", "target", "t"), ("limit",),
           lambda wm, p: wm.transform_between(p["world"], p["source"], p["target"], _t(p), limit=p.get("limit"),
                                              **_ctx(p)), ev_chain, dv_transform),
    Reader("where", ("thing", "frame", "t"), ("angle_tolerance", "limit"),
           lambda wm, p: wm.where(p["world"], p["thing"], p["frame"], _t(p), limit=p.get("limit"), **_ctx(p),
                                  **({"angle_tolerance": p["angle_tolerance"]} if "angle_tolerance" in p else {})),
           ev_where, dv_where),
    Reader("poses", ("thing", "t"), (), lambda wm, p: wm.poses(p["world"], p["thing"], _t(p), **_ctx(p)),
           ev_list_support),
    Reader("frame_info", ("frame", "t"), (), lambda wm, p: wm.frame_info(p["world"], p["frame"], _t(p), **_ctx(p)),
           ev_frame_info),
    # family M
    Reader("measurements", ("bearer", "quality"), ("t",),
           lambda wm, p: wm.measurements(p["world"], p["bearer"], p["quality"], _t(p), **_ctx(p)), ev_measurements),
    Reader("compare_measurements", ("bearer", "quality"), ("t",),
           lambda wm, p: wm.compare_measurements(p["world"], p["bearer"], p["quality"], _t(p), **_ctx(p)), ev_compare),
    Reader("measurement_calibration", ("bearer", "quality"), ("t",),
           lambda wm, p: lab.measurement_calibration(wm, p["world"], p["bearer"], p["quality"], _t(p), **_ctx(p)),
           ev_measurement_calibration),
    Reader("calibration_status", ("instrument", "t"), (),
           lambda wm, p: lab.calibration_status(wm, p["world"], p["instrument"], _t(p), **_ctx(p)),
           lambda a: deciding(a, "certificates")),
    Reader("convert", ("value", "unit"), ("to",), lambda wm, p: {"value": wm.convert(p["value"], p["unit"], p.get("to"))},
           refusals=(CROSS_DIMENSION, UNKNOWN_UNIT), timeless=True, worldless=True),
    # family C
    Reader("causes_of", ("effect", "t"), (), lambda wm, p: wm.causes_of(p["world"], p["effect"], _t(p), **_ctx(p)),
           ev_claims),
    Reader("effects_of", ("event", "t"), (), lambda wm, p: wm.effects_of(p["world"], p["event"], _t(p), **_ctx(p)),
           ev_effects),
    Reader("explain", ("type", "roles", "t"), (),
           lambda wm, p: wm.explain(p["world"], p["type"], p["roles"], _t(p), **_ctx(p)), ev_explain,
           refusals=(UNKNOWN_ROLE,)),
    Reader("changes", ("subject", "t1", "t2"), (),
           lambda wm, p: wm.changes(p["world"], p["subject"], p["t1"], p["t2"], **_ctx(p)), ev_changes, timeless=True),
    # family P
    Reader("process_steps", ("process", "t"), (),
           lambda wm, p: wm.process_steps(p["world"], p["process"], _t(p), **_ctx(p)), ev_list_support),
    Reader("before", ("a", "b"), (), lambda wm, p: {"before": wm.before(p["world"], p["a"], p["b"], **_ctx(p))},
           timeless=True),
    Reader("interval", ("description",), (), _interval, ev_interval, timeless=True),
    # readers E1 already covers, for multi-step plans (X)
    Reader("holds", ("type", "roles", "t"), (),
           lambda wm, p: wm.holds(p["world"], p["type"], p["roles"], _t(p), **_ctx(p)), ev_answer,
           refusals=(UNKNOWN_ROLE,)),
    Reader("value_at", ("type", "subject", "t"), (),
           lambda wm, p: wm.value_at(p["world"], p["type"], p["subject"], _t(p), **_ctx(p)), ev_support,
           refusals=(UNKNOWN_ROLE, NO_SINGLE_SLOT)),
    Reader("facts_about", ("subject", "t"), (),
           lambda wm, p: wm.facts_about(p["world"], p["subject"], _t(p), **_ctx(p)), ev_list_support),
    Reader("occurrence", ("occurrence",), (), lambda wm, p: wm.occurrence(p["world"], p["occurrence"], **_ctx(p)),
           lambda a: set(), timeless=True,
           notes="the merged occurrence view (event roles); E1 scores roles through it; cites nothing by default"),
    Reader("occurrence_status", ("occurrence", "t"), (),
           lambda wm, p: wm.occurrence_status(p["world"], p["occurrence"], _t(p), **_ctx(p)), ev_occurrence_status),
    Reader("office_holders", ("office", "context", "t"), (),
           lambda wm, p: org.office_holders(wm, p["world"], p["office"], p["context"], _t(p), **_ctx(p)),
           ev_office_holders),
]}
TIME_PARAMS = {"t", "t1", "t2"}


def reader(name, extra=None):
    """The template called `name`, from READERS or from `extra` (harness self-test readers)."""
    r = (extra or {}).get(name) or READERS.get(name)
    if r is None:
        raise KeyError(f"no reader template {name!r}; known: {sorted(READERS)}")
    return r


def allowed_params(r):
    common = () if r.worldless else ("world", "as_of", "perspective") + (() if r.timeless else ("t",))
    return set(r.required) | set(r.optional) | set(common)


def required_params(r):
    return set(r.required) | (set() if r.worldless else {"world"})
