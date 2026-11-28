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

**Approved decisions (LABS-1.064; docs/stage-e/stage-e2-semantic-decisions.md).**
- `blocked.json` `blocked` now holds only the decisions still open (ONT-SC-1).
- `blocked.json` `unimplemented` lists the answer paths whose semantics an approved decision fixes but that no reader
  reports yet. A scored question may not expect them: it is refused with the DI to author it under as a class G probe.
  A probe may expect them; `"accept": ["absent"]` lets a probe pass when the reader presents no such field (nothing is
  fabricated). Approval of a semantics never establishes that the capability exists (item 19).
- `convention` (SD-SPA-2): a question whose expected answer is a convention-derived result (`"frame-identity"`: the
  identity transform of a frame to itself) presents no derivation and cites nothing. It must author empty
  `admissible_evidence` and `admissible_premises` and no required evidence; score.py fails any presented derivation.
- Occurrence inputs (SD-CORE-4, P-5): `occurrence` and `occurrence_status` take an occurrence. A literal id the fixture
  declares as something else is refused (an execution precondition, never authored).
- Attribution (H-9, SD-CAU-1): a `changes` step that expects anything inside an explanation entry must fix that entry's
  `attribution` (directly, or by expecting the whole entry or list), so an answer that drops or misstates an ambiguous
  attribution cannot pass as unique causation.
- `targets` (LABS-1.064 item 26): the DI ids a question deliberately exercises (targeted defect coverage). Reported
  apart from broad competency coverage.
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
            "admissible_conflict_evidence", "admissible_premises", "depends_on", "convention", "targets",
            # LABS-1.065 authoring metadata (author pack question-format.md); not scored
            "competency", "case_type", "derivation", "calc", "prohibited"}
CASE_TYPES = {"positive", "negative", "disputed", "unknown", "refusal"}
CONVENTIONS = {"frame-identity": "transform_between"}           # SD-SPA-2: convention -> the reader it applies to
OCCURRENCE_READERS = {"occurrence", "occurrence_status"}
BLOCKED = Path(__file__).resolve().parents[2] / "benchmark" / "e2" / "spec" / "blocked.json"
DERIVING = {"where", "transform_between"}


def load_blocked(path=BLOCKED):
    return json.loads(Path(path).read_text())["blocked"] if Path(path).exists() else []


def load_unimplemented(path=BLOCKED):
    return json.loads(Path(path).read_text()).get("unimplemented", []) if Path(path).exists() else []


def _segments(path):
    try:
        return [seg for seg in parse_path(path) if isinstance(seg, str)]
    except PathError:
        return None


def _path_matches(path, pattern):
    """`pattern` is an answer path prefix ("judgement", "initiated_by"), "*<segment>" for a field anywhere, or
    "<prefix>*<segment>" for a field anywhere below a prefix."""
    if "*" in pattern:
        prefix, field = pattern.split("*", 1)
        if prefix and not _path_matches(path, prefix):
            return False
        segs = _segments(path)
        return segs is not None and field in segs[1 if prefix else 0:]
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


def _unimplemented_hits(q, entries):
    """Paths an approved decision fixes but no reader provides (LABS-1.064): refused in scored questions."""
    if q.get("class") == "G":
        return []
    hits = []
    for b in entries:
        for st in q.get("plan", []):
            if st.get("reader") != b.get("reader"):
                continue
            for path in st.get("expected") or {}:
                if any(_path_matches(path, bp) for bp in b.get("paths", [])):
                    hits.append(f"step {st.get('step')!r} expects {path!r} from {b['reader']}: approved by {b['id']} "
                                f"({b['question']}) but not implemented ({b['di']}); author it as a class G probe")
    return hits


def _occurrences(fx):
    """Ids the fixture makes occurrences: declared with kind occurrence, or named as an account's occurrence."""
    occ = {s["id"] for s in fx["steps"] if s.get("op") == "entity" and s.get("kind") == "occurrence"}
    occ |= {s["occurrence"] for s in fx["steps"] if isinstance(s.get("occurrence"), str)}
    occ |= {s.get("roles", {}).get("existent") for s in fx["steps"] if s.get("type") == "existence"} - {None}
    return occ


def _declared(fx):
    return {s["id"] for s in fx["steps"] if s.get("op") == "entity"}


def _attribution_problems(st):
    """H-9: every explanation entry a `changes` step looks into has its attribution fixed."""
    exp = st.get("expected") or {}
    covered, needs = set(), {}
    for path in exp:
        try:
            segs = parse_path(path)
        except PathError:
            continue
        if "explanations" not in segs:
            continue
        i = segs.index("explanations")
        entry = segs[:i + 2]                                   # up to the explanation entry selector, if any
        if len(segs) <= i + 2 or segs[-1] == "attribution":
            covered.add(repr(entry))                           # the whole list or entry, or its attribution
        else:
            needs.setdefault(repr(entry), path)
    return [f"step {st.get('step')!r} expects {p!r} inside a changes explanation without fixing its attribution "
            "(H-9, SD-CAU-1: ambiguous attribution must not pass as unique causation)"
            for e, p in needs.items() if e not in covered]


STEP_KEYS = {"step", "reader", "params", "expected", "tolerance", "ordered"}
PROBE_ACCEPT = {"UNKNOWN", "NOT_YET_KNOWN", "refusal", "absent"}


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


def problems_of(q, fixtures, seen, selftest=False, blocked=None, unimplemented=None):
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
        if name in OCCURRENCE_READERS and isinstance(p.get("occurrence"), str):
            oid = p["occurrence"]
            if oid in _declared(fx) and oid not in _occurrences(fx):
                out.append(f"{where}: {oid!r} is not an occurrence in the fixture: an execution precondition "
                           "(SD-CORE-4, P-5), never authored")
        if name == "changes":
            out += [f"{where}: {x}" for x in _attribution_problems(st)]
        if name == "transform_between" and isinstance(p.get("source"), str) and p.get("source") == p.get("target") \
                and q.get("convention") != "frame-identity":
            out.append(f"{where}: a frame to itself is a convention-derived result: the question must say "
                       "\"convention\": \"frame-identity\" (SD-SPA-2)")
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
    conv = q.get("convention")
    if conv is not None:
        if conv not in CONVENTIONS:
            out.append(f"unknown convention {conv!r}; known: {sorted(CONVENTIONS)}")
        elif not any(st.get("reader") == CONVENTIONS[conv] and (st.get("params") or {}).get("source") is not None
                     and (st.get("params") or {}).get("source") == (st.get("params") or {}).get("target")
                     for st in plan):
            out.append(f"convention {conv!r}: no {CONVENTIONS[conv]} step asks for a frame to itself")
        for k in ("admissible_evidence", "admissible_premises"):
            if q.get(k) != []:
                out.append(f"a convention-derived answer cites nothing and presents no derivation: {k} must be [] "
                           "(SD-SPA-2)")
        if q.get("required_evidence") or q.get("required_conflict_evidence"):
            out.append("a convention-derived answer has no required evidence (SD-SPA-2)")
    if "case_type" in q and q["case_type"] not in CASE_TYPES:
        out.append(f"case_type {q['case_type']!r}: one of {sorted(CASE_TYPES)}")
    bad_targets = [x for x in q.get("targets") or [] if not (isinstance(x, str) and x.startswith("DI-"))]
    if bad_targets or ("targets" in q and not isinstance(q["targets"], list)):
        out.append(f"targets must be a list of DI ids: {bad_targets or q['targets']}")
    for hit in _blocked_hits(q, load_blocked() if blocked is None else blocked):
        out.append(f"blocked: {hit} (H-8)")
    for hit in _unimplemented_hits(q, load_unimplemented() if unimplemented is None else unimplemented):
        out.append(f"unimplemented: {hit}")
    return out


def check(paths, fixtures, selftest=False, blocked=None, unimplemented=None):
    """[(file, line, id, problem)] for every problem in the questions."""
    seen, out = set(), []
    for f, n, q in read_questions(paths):
        out += [(f, n, q.get("id"), p) for p in problems_of(q, fixtures, seen, selftest, blocked, unimplemented)]
    return out
