"""Stage E2 harness: the multi-step plan runner.

A question's `plan` is a list of steps, each {"step": name, "reader": template, "params": {...}, "expected": {...}}.
Steps run in order on one loaded scenario and one query path. A parameter may come from an earlier step's normalised
answer: {"from": "<step>", "path": "<answer path>"} (values.select). Every step's answer is recorded, so a wrong final
answer can be traced to the step that went wrong.

A step ends the plan early when it cannot give an answer to feed on:
- an execution error (an exception other than a refusal): `error`;
- a parameter reference that names no earlier step or no part of its answer: `plan_error` (a defect of the question
  or of an earlier answer, kept apart from execution errors).
A refusal is an answer ({"refused": true, ...}); a later step that refers into it gets a plan error.
"""

import time
import traceback
from datetime import datetime

from evaluation.loader import T
from evaluation.e2.readers import REFUSALS, TIME_PARAMS, generic_derivations, reader
from evaluation.e2.values import PathError, normalise, select


class PlanError(LookupError):
    """A plan step's parameters cannot be resolved."""


def _time(v):
    if v is None or isinstance(v, datetime):
        return v
    if isinstance(v, str) and v.startswith("T"):
        return T(v)
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v)
        except ValueError:
            pass
    raise PlanError(f"not a time: {v!r}")


def resolve(value, answers):
    if isinstance(value, dict) and set(value) == {"from", "path"}:
        if value["from"] not in answers:
            raise PlanError(f"parameter refers to step {value['from']!r}, which has not run before this one")
        try:
            return select(answers[value["from"]], value["path"])
        except PathError as e:
            raise PlanError(f"step {value['from']!r} has no {value['path']!r}: {e}") from None
    if isinstance(value, dict):
        return {k: resolve(v, answers) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, answers) for v in value]
    return value


def coerce(L, params):
    out = dict(params)
    for k in TIME_PARAMS & set(out):
        out[k] = _time(out[k])
    if out.get("as_of") is not None:
        a = out["as_of"]
        out["as_of"] = L.at(a) if isinstance(a, str) and a.startswith("@") else _time(a)
    return out


def run_plan(L, question, selective, extra_readers=None):
    """Run every step of the question's plan on one path. Returns {"steps": [...], "ms": total reader time}, plus
    "error" or "plan_error" (with the step) when the plan stopped early."""
    L.wm.selective = selective
    answers, steps, total = {}, [], 0.0
    try:
        for st in question["plan"]:
            name = st["step"]
            r = reader(st["reader"], extra_readers)
            rec = {"step": name, "reader": r.name}
            steps.append(rec)
            try:
                raw = resolve(st.get("params", {}), answers)
                params = coerce(L, raw)
            except PlanError as e:
                rec["plan_error"] = str(e)
                return {"steps": steps, "ms": round(total, 1), "plan_error": {"step": name, "message": str(e)}}
            rec["params"] = normalise(raw)
            t0 = time.perf_counter()
            try:
                out = r.call(L.wm, params)
                ans = normalise(out)
            except REFUSALS as e:
                ans = {"refused": True, "refusal": f"{type(e).__name__}: {' '.join(str(e).split())[:400]}"}
            except Exception as e:                                 # an execution error is a result of its own
                ms = (time.perf_counter() - t0) * 1000
                total += ms
                rec.update(ms=round(ms, 1), error=f"{type(e).__name__}: {' '.join(str(e).split())[:400]}",
                           trace=traceback.format_exc(limit=4)[-1200:])
                return {"steps": steps, "ms": round(total, 1), "error": {"step": name, "message": rec["error"]}}
            ms = (time.perf_counter() - t0) * 1000
            total += ms
            refused = isinstance(ans, dict) and ans.get("refused") is True
            rec.update(ms=round(ms, 1), answer=ans,
                       cited=[] if refused or r.evidence is None else sorted(map(str, r.evidence(ans))),
                       derivations=[] if refused else (r.derivations or generic_derivations)(ans))
            answers[name] = ans
        return {"steps": steps, "ms": round(total, 1)}
    finally:
        L.wm.selective = True
