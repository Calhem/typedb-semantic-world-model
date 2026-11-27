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
- Evidence names are fixture-level names (evaluation/e2/names.py): a step id, or `<step>/<part>`. Required evidence is
  admissible; nothing is both forbidden and required or admissible.

**Evidence and premises (H-3, LABS-1.063).** A scored question whose plan calls a reader that cites evidence must
author that role's admissible set: `admissible_evidence` (supporting) always, and `admissible_conflict_evidence`
(conflicting) when the reader can cite conflicting evidence. Either may be []. Each role may also have a required set
(`required_evidence`, `required_conflict_evidence`). A question calling a reader that presents derivations (`where`,
`transform_between`) authors `admissible_premises`.

**Blocked dependencies (H-8 as amended, LABS-1.063).** `benchmark/e2/spec/blocked.json` lists the unresolved semantic
decisions. An entry may name a reader with the answer paths (a prefix, or `*<field>` for a field anywhere; optionally
with a value) or the parameters whose meaning waits for the decision. A question is refused when one of its steps
expects such a path or passes such a parameter, or when its `depends_on` names a blocked decision. Decisions that no
path or parameter can detect (a fixture shape, an interval boundary) are listed without a reader: an author whose
question depends on one must declare it in `depends_on`. A discrepancy against an **established** contract is never blocked: such a question stays
eligible, even when the current implementation is expected to fail it.
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
            "justification", "spec", "uncertainty", "adversarial", "difficulty", "notes", "required_conflict_evidence",
            "admissible_conflict_evidence", "admissible_premises", "depends_on"}
BLOCKED = Path(__file__).resolve().parents[2] / "benchmark" / "e2" / "spec" / "blocked.json"
DERIVING = {"where", "transform_between"}


def load_blocked(path=BLOCKED):
    return json.loads(Path(path).read_text())["blocked"] if Path(path).exists() else []


def _path_matches(path, pattern):
    """`pattern` is an answer path prefix ("judgement", "initiated_by"), or "*<segment>" for a field anywhere."""
    if pattern.startswith("*"):
        try:
            return pattern[1:] in [seg for seg in parse_path(path) if isinstance(seg, str)]
        except PathError:
            return False
    return path == pattern or path.startswith(pattern + ".") or path.startswith(pattern + "[")


def _blocked_hits(q, blocked):
    """Each entry: id, question; optionally reader, paths (with optional `when` values), params. A question is blocked
    when it names the entry in `depends_on`, or a step of that reader expects a listed path (with the listed value, if
    any) or passes a listed parameter."""
    hits = []
    dep = set(q.get("depends_on") or [])
    for b in blocked:
        if b["id"] in dep:
            hits.append(f"depends on {b['id']} ({b['question']}), an unresolved decision")
            continue
        for st in q.get("plan", []):
            if not b.get("reader") or st.get("reader") != b["reader"]:
                continue
            for pname in b.get("params", []):
                if pname in (st.get("params") or {}):
                    hits.append(f"step {st.get('step')!r} passes {pname!r} to {b['reader']}, which waits for "
                                f"{b['id']} ({b['question']})")
            for path, value in (st.get("expected") or {}).items():
                for bp in b.get("paths", []):
                    want = b.get("when", {}).get(bp, "__any__")
                    if _path_matches(path, bp) and (want == "__any__" or value == want):
                        hits.append(f"step {st.get('step')!r} expects {path!r} from {b['reader']}, which waits for "
                                    f"{b['id']} ({b['question']})")
    return hits


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


def problems_of(q, fixtures, seen, selftest=False, blocked=None):
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
    from evaluation.e2.evidence import CITES, CONFLICT_ROLE
    sets = {k: set(q.get(k, [])) for k in ("required_evidence", "admissible_evidence", "required_conflict_evidence",
                                             "admissible_conflict_evidence", "forbidden_evidence", "admissible_premises")}
    for k, v in sets.items():
        bad = sorted(n for n in v if n.split("/")[0] not in step_ids)
        if bad:
            out.append(f"{k} names no fixture step: {bad}")
    for req_k, adm_k in (("required_evidence", "admissible_evidence"),
                         ("required_conflict_evidence", "admissible_conflict_evidence")):
        if adm_k in q and sets[req_k] - sets[adm_k]:
            out.append(f"{req_k} must be in {adm_k}: {sorted(sets[req_k] - sets[adm_k])}")
    allowed = sets["required_evidence"] | sets["admissible_evidence"] | sets["required_conflict_evidence"] | \
        sets["admissible_conflict_evidence"]
    if sets["forbidden_evidence"] & allowed:
        out.append(f"evidence both forbidden and required or admissible: {sorted(sets['forbidden_evidence'] & allowed)}")
    readers = {st.get("reader") for st in plan}
    if q["class"] != "G":
        if readers & CITES and "admissible_evidence" not in q:
            out.append("a scored question citing evidence must author admissible_evidence (may be []) (H-3)")
        if readers & CONFLICT_ROLE and "admissible_conflict_evidence" not in q:
            out.append("a scored question whose reader can cite conflicting evidence must author "
                       "admissible_conflict_evidence (may be []) (H-3)")
        if readers & DERIVING and "admissible_premises" not in q:
            out.append("a question calling a reader that presents derivations must author admissible_premises (H-3)")
    for hit in _blocked_hits(q, load_blocked() if blocked is None else blocked):
        out.append(f"blocked: {hit} (H-8)")
    return out


def check(paths, fixtures, selftest=False, blocked=None):
    """[(file, line, id, problem)] for every problem in the questions."""
    seen, out = set(), []
    for f, n, q in read_questions(paths):
        out += [(f, n, q.get("id"), p) for p in problems_of(q, fixtures, seen, selftest, blocked)]
    return out
