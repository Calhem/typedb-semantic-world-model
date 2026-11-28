"""Stage E2 harness: reader templates (GAP-HARNESS-3).

Each template names a public reader, the parameters a question gives it, how it is called, and two extractors that
work on the reader's normalised answer (values.normalise):
- `evidence`: the answer's attestation ids **by role** (supporting, conflicting, alternative, undetermined), built from
  part 6 of the reader's contract (evaluation/e2/evidence.py; H-4, H-5, LABS-1.063).
- `derivations`: the derivations the answer **presents**: a named rule with its premises (for example a pose derived
  through a frame chain under `frame-transform/v1`). The scorer checks that every one is recorded (rule known,
  premises recorded attestations): a derivation that is not is fabricated (E2-D6, "no fabricated derivations").

The extractors follow the E2 reader contracts (benchmark/e2/spec/reader-contracts.md, LABS-1.062/1.063). A change to a
contract's evidence table is a change to evidence.py, never to a reader.

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
@dataclass(frozen=True)
class Reader:
    name: str
    required: tuple
    optional: tuple
    call: object                               # (wm, p) -> raw answer; p holds the coerced parameters
    evidence: object = None                    # normalised answer -> {role: set of attestation ids} (evidence.py)
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


# ---- derivations a reader presents (evidence by role is in evidence.py) ---------------------------------------------
def _chain_support(chain):
    return {x for st in chain or [] for x in _ids(st.get("support"))}


def dv_where(a):
    out = []
    for i, c in enumerate(a["candidates"]):
        if c.get("rule"):
            out.append({"rule": c["rule"], "at": f"candidates[{i}]",
                        "premises": sorted(set(c.get("position_support", [])) | _chain_support(c.get("chain")))})
    return out


def dv_transform(a):
    """A transform the answer gives under a named rule is presented as derived by that rule from its chain. With an
    empty chain (source == target) that is a premise-less derivation, which the approved contract forbids: SD-SPA-2
    (LABS-1.064) makes the identity a declared convention that presents no derivation, so it is extracted and scored
    as fabricated rather than skipped."""
    if a.get("transform") is None or not (a.get("chain") or a.get("rule")):
        return []
    return [{"rule": a.get("rule"), "at": "transform", "premises": sorted(_chain_support(a.get("chain")))}]


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
# not-a-unit is a precondition failure, not a refusal (P-5, P-CV-1, approved LABS-1.063): an execution error (H-6)
NO_SINGLE_SLOT = Refusal("no-single-slot", ValueError, r"one-role functional constraints",
                         "core-0.4/README.md (A0 constraints: value_at without key_role needs exactly one one-role "
                         "constraint; otherwise the question must say which)", True)


READERS = {r.name: r for r in [
    # family S, F
    Reader("transform_between", ("source", "target", "t"), ("limit",),
           lambda wm, p: wm.transform_between(p["world"], p["source"], p["target"], _t(p), limit=p.get("limit"),
                                              **_ctx(p)), None, dv_transform),
    Reader("where", ("thing", "frame", "t"), ("angle_tolerance", "limit"),
           lambda wm, p: wm.where(p["world"], p["thing"], p["frame"], _t(p), limit=p.get("limit"), **_ctx(p),
                                  **({"angle_tolerance": p["angle_tolerance"]} if "angle_tolerance" in p else {})),
           None, dv_where),
    Reader("poses", ("thing", "t"), (), lambda wm, p: wm.poses(p["world"], p["thing"], _t(p), **_ctx(p)),
           None),
    Reader("frame_info", ("frame", "t"), (), lambda wm, p: wm.frame_info(p["world"], p["frame"], _t(p), **_ctx(p)),
           None),
    # family M
    Reader("measurements", ("bearer", "quality"), ("t",),
           lambda wm, p: wm.measurements(p["world"], p["bearer"], p["quality"], _t(p), **_ctx(p)), None),
    Reader("compare_measurements", ("bearer", "quality"), ("t",),
           lambda wm, p: wm.compare_measurements(p["world"], p["bearer"], p["quality"], _t(p), **_ctx(p)), None),
    Reader("measurement_calibration", ("bearer", "quality"), ("t",),
           lambda wm, p: lab.measurement_calibration(wm, p["world"], p["bearer"], p["quality"], _t(p), **_ctx(p)),
           None),
    Reader("calibration_status", ("instrument", "t"), (),
           lambda wm, p: lab.calibration_status(wm, p["world"], p["instrument"], _t(p), **_ctx(p)),
           None),
    Reader("convert", ("value", "unit"), ("to",), lambda wm, p: {"value": wm.convert(p["value"], p["unit"], p.get("to"))},
           refusals=(CROSS_DIMENSION,), timeless=True, worldless=True),
    # family C
    Reader("causes_of", ("effect", "t"), (), lambda wm, p: wm.causes_of(p["world"], p["effect"], _t(p), **_ctx(p)),
           None),
    Reader("effects_of", ("event", "t"), (), lambda wm, p: wm.effects_of(p["world"], p["event"], _t(p), **_ctx(p)),
           None),
    Reader("explain", ("type", "roles", "t"), (),
           lambda wm, p: wm.explain(p["world"], p["type"], p["roles"], _t(p), **_ctx(p)), None,
           refusals=(UNKNOWN_ROLE,)),
    Reader("changes", ("subject", "t1", "t2"), (),
           lambda wm, p: wm.changes(p["world"], p["subject"], p["t1"], p["t2"], **_ctx(p)), None, timeless=True),
    # family P
    Reader("process_steps", ("process", "t"), (),
           lambda wm, p: wm.process_steps(p["world"], p["process"], _t(p), **_ctx(p)), None),
    Reader("before", ("a", "b"), (), lambda wm, p: {"before": wm.before(p["world"], p["a"], p["b"], **_ctx(p))},
           timeless=True),
    Reader("interval", ("description",), (), _interval, None, timeless=True),
    # readers E1 already covers, for multi-step plans (X)
    Reader("holds", ("type", "roles", "t"), (),
           lambda wm, p: wm.holds(p["world"], p["type"], p["roles"], _t(p), **_ctx(p)), None,
           refusals=(UNKNOWN_ROLE,)),
    # key_role / value_role (LABS-1.064, SD-CORE-2): passed only when the question gives them
    Reader("value_at", ("type", "subject", "t"), ("key_role", "value_role"),
           lambda wm, p: wm.value_at(p["world"], p["type"], p["subject"], _t(p), **_ctx(p),
                                     **{k: p[k] for k in ("key_role", "value_role") if k in p}), None,
           refusals=(UNKNOWN_ROLE, NO_SINGLE_SLOT)),
    Reader("facts_about", ("subject", "t"), (),
           lambda wm, p: wm.facts_about(p["world"], p["subject"], _t(p), **_ctx(p)), None),
    Reader("occurrence", ("occurrence",), (), lambda wm, p: wm.occurrence(p["world"], p["occurrence"], **_ctx(p)),
           None, timeless=True,
           notes="the merged occurrence view (event roles); E1 scores roles through it; cites nothing by default"),
    Reader("occurrence_status", ("occurrence", "t"), (),
           lambda wm, p: wm.occurrence_status(p["world"], p["occurrence"], _t(p), **_ctx(p)), None),
    Reader("office_holders", ("office", "context", "t"), (),
           lambda wm, p: org.office_holders(wm, p["world"], p["office"], p["context"], _t(p), **_ctx(p)),
           None),
]}
from dataclasses import replace as _replace  # noqa: E402

from evaluation.e2.evidence import EXTRACTORS  # noqa: E402

READERS = {n: _replace(r, evidence=EXTRACTORS[n]) for n, r in READERS.items()}
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
