"""Stage E2 harness: the question format and its checker (no reader is called).

A question (one JSON object per line in a .jsonl file):

    {"id": "S-001", "family": "S", "class": "H", "scenario": "<fixture id>",
     "subset": null,                         # "identity" for the identity-conflict questions (family X only, F-4)
     "gap": null,                            # class G: the gap id, e.g. "GAP-FRAME-3"
     "plan": [{"step": "s1", "reader": "transform_between",
               "params": {"world": "w", "source": "A", "target": "C", "t": "T5"},
               "expected": {"status": "INFERRED", "transform.t": [1.0, 2.0, 0.0]},
               "tolerance": {"transform.t": 1e-9, "transform.q": {"rad": 1e-6}},
               "ordered": []}],
     "required_evidence": ["ab", "bc"], "admissible_evidence": ["ab", "bc"], "forbidden_evidence": ["old-ab"],
     "probe": {"accept": ["UNKNOWN", "NOT_YET_KNOWN", "refusal"], "path": "status"},   # class G only
     ...optional: question, justification, spec, uncertainty, adversarial, difficulty, notes}

- Classes: A and H are scored; G is a gap probe (never scored for conformance, rule G-1). A probe may have an empty
  plan (no reader can be called).
- A step parameter {"from": "<earlier step>", "path": "<answer path>"} takes its value from an earlier answer.
- `expected` maps answer paths to values; a scored question's last step must have one. A step expecting a refusal
  says {"refused": true}.
- Evidence names are fixture step ids. Required evidence is admissible; nothing is both forbidden and required or
  admissible.
"""

import json
from pathlib import Path

from evaluation.e2.readers import allowed_params, required_params, READERS
from evaluation.e2.values import PathError, parse_path

FAMILIES = {"S", "F", "M", "C", "P", "X"}
CLASSES = {"A", "H", "G"}
SUBSETS = {"identity"}
REQUIRED = {"id", "family", "class", "scenario", "plan"}
OPTIONAL = {"subset", "gap", "required_evidence", "admissible_evidence", "forbidden_evidence", "probe", "question",
            "justification", "spec", "uncertainty", "adversarial", "difficulty", "notes"}
STEP_KEYS = {"step", "reader", "params", "expected", "tolerance", "ordered"}
PROBE_ACCEPT = {"UNKNOWN", "NOT_YET_KNOWN", "refusal"}


def read_questions(paths):
    for f in paths:
        for n, line in enumerate(Path(f).read_text().splitlines(), 1):
            if line.strip():
                yield str(f), n, json.loads(line)


def read_fixtures(directory):
    return {json.loads(f.read_text())["id"]: json.loads(f.read_text()) for f in sorted(Path(directory).glob("*.json"))}


def _refs(v):
    if isinstance(v, dict) and set(v) == {"from", "path"}:
        yield v
    elif isinstance(v, dict):
        for w in v.values():
            yield from _refs(w)
    elif isinstance(v, list):
        for w in v:
            yield from _refs(w)


def problems_of(q, fixtures, seen, selftest=False):
    out = []
    missing, extra = REQUIRED - set(q), set(q) - REQUIRED - OPTIONAL
    if missing:
        return [f"missing fields {sorted(missing)}"]
    if extra:
        out.append(f"unknown fields {sorted(extra)}")
    if q["id"] in seen:
        out.append(f"duplicate id {q['id']}")
    seen.add(q["id"])
    if q["family"] not in FAMILIES:
        out.append(f"unknown family {q['family']!r}")
    if q["class"] not in CLASSES:
        out.append(f"unknown class {q['class']!r}")
    if (q["class"] == "G") != bool(q.get("gap")):
        out.append("a gap id is given exactly when the class is G")
    if q.get("subset") is not None and (q["subset"] not in SUBSETS or q["family"] != "X"):
        out.append(f"subset {q['subset']!r}: only 'identity', in family X (F-4)")
    if q["class"] == "G":
        acc = set((q.get("probe") or {}).get("accept", PROBE_ACCEPT))
        if acc - PROBE_ACCEPT:
            out.append(f"probe accepts {sorted(acc - PROBE_ACCEPT)}: a probe accepts only {sorted(PROBE_ACCEPT)}")
    elif "probe" in q:
        out.append("only a class G question has a probe")
    fx = fixtures.get(q["scenario"])
    if fx is None:
        return out + [f"unknown scenario {q['scenario']!r}"]
    step_ids = {s.get("id") for s in fx["steps"]}
    marks = {s["name"] for s in fx["steps"] if s.get("op") == "mark"}
    worlds = {s["id"] for s in fx["steps"] if s.get("op") == "world"}
    plan = q["plan"]
    if not isinstance(plan, list) or (not plan and q["class"] != "G"):
        out.append("a scored question needs a plan with at least one step")
        plan = plan if isinstance(plan, list) else []
    names = set()
    for i, st in enumerate(plan):
        where = f"step {i + 1} ({st.get('step')!r})"
        if set(st) - STEP_KEYS:
            out.append(f"{where}: unknown keys {sorted(set(st) - STEP_KEYS)}")
        if not st.get("step") or st["step"] in names:
            out.append(f"{where}: needs a unique step name")
        name = st.get("reader", "")
        if name.startswith("selftest_") and not selftest:
            out.append(f"{where}: self-test reader {name!r} outside a self-test run")
            continue
        r = READERS.get(name)
        if r is None and selftest:
            from evaluation.e2.selftest import READERS as extra
            r = extra.get(name)
        if r is None:
            out.append(f"{where}: unknown reader {name!r}")
            continue
        p = st.get("params", {})
        if required_params(r) - set(p):
            out.append(f"{where}: params missing {sorted(required_params(r) - set(p))}")
        if set(p) - allowed_params(r):
            out.append(f"{where}: unknown params {sorted(set(p) - allowed_params(r))}")
        for ref in _refs(p):
            if ref["from"] not in names:
                out.append(f"{where}: parameter refers to {ref['from']!r}, not an earlier step")
            try:
                parse_path(ref["path"])
            except PathError as e:
                out.append(f"{where}: {e}")
        if isinstance(p.get("world"), str) and p["world"] not in worlds:
            out.append(f"{where}: world {p['world']!r} not in the fixture")
        if isinstance(p.get("as_of"), str) and p["as_of"].startswith("@") and p["as_of"][1:] not in marks:
            out.append(f"{where}: as_of {p['as_of']!r} names no mark")
        for key in ("expected", "tolerance"):
            for path in st.get(key, {}) or {}:
                try:
                    parse_path(path)
                except PathError as e:
                    out.append(f"{where}: {key}: {e}")
        for path, tol in (st.get("tolerance") or {}).items():
            ok = (isinstance(tol, (int, float)) and not isinstance(tol, bool) and tol >= 0) or (
                isinstance(tol, dict) and set(tol) == {"rad"} and isinstance(tol["rad"], (int, float)) and tol["rad"] >= 0)
            if not ok:
                out.append(f"{where}: tolerance for {path!r} must be a number >= 0 or {{\"rad\": number}}")
        names.add(st.get("step"))
    if plan and q["class"] != "G" and not plan[-1].get("expected"):
        out.append("the last step of a scored question needs an expected answer")
    req, adm, forb = (set(q.get(k, [])) for k in ("required_evidence", "admissible_evidence", "forbidden_evidence"))
    for k, v in (("required_evidence", req), ("admissible_evidence", adm), ("forbidden_evidence", forb)):
        if v - step_ids:
            out.append(f"{k} names no fixture step: {sorted(v - step_ids)}")
    if "admissible_evidence" in q and req - adm:
        out.append(f"required evidence must be admissible: {sorted(req - adm)}")
    if forb & (req | adm):
        out.append(f"evidence both forbidden and required or admissible: {sorted(forb & (req | adm))}")
    return out


def check(paths, fixtures, selftest=False):
    """[(file, line, id, problem)] for every problem in the questions."""
    seen, out = set(), []
    for f, n, q in read_questions(paths):
        out += [(f, n, q.get("id"), p) for p in problems_of(q, fixtures, seen, selftest)]
    return out
