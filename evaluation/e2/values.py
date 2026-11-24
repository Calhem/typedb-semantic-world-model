"""Stage E2 harness: answer normalisation, the answer path language and comparison.

Normalisation turns any reader answer into plain JSON, so that both query paths, the child process and the gold use
one form: dataclasses become dicts, enums their names, datetimes ISO 8601 strings, tuples and sets lists (sets
sorted), and keys starting with "_" are dropped (private reader material).

Paths address parts of a normalised answer: "status", "transform.t", "candidates[0].x", "candidates[*].stated_in"
("[*]" maps over a list, giving a list), and "records[record=m1-result].raw_value" ("[field=value]" picks the one
item of a list whose field, as text, equals value: none or several is an error, so a plan never depends on the order
a reader lists things in). A path that does not exist raises PathError.

Comparison (`matches`): numbers within a tolerance when the question states one for that path (absolute, applied to
every number below it), rotations as unit quaternions within an angle ({"rad": tol}; q and -q are the same rotation),
lists as multisets unless the path is listed as ordered, dicts key by key (the same keys), everything else exactly.
A tolerance is stated by the question, never chosen by the harness.
"""

import dataclasses
import enum
import json
import math
import re
from datetime import date, datetime


class PathError(LookupError):
    """An answer path names something the answer does not have."""


def normalise(x):
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return {f.name: normalise(getattr(x, f.name)) for f in dataclasses.fields(x) if not f.name.startswith("_")}
    if isinstance(x, enum.Enum):
        return x.name
    if isinstance(x, (datetime, date)):
        return x.isoformat()
    if isinstance(x, dict):
        return {str(k): normalise(v) for k, v in x.items() if not str(k).startswith("_")}
    if isinstance(x, (set, frozenset)):
        return sorted((normalise(v) for v in x), key=canonical)
    if isinstance(x, (list, tuple)):
        return [normalise(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x):
        return repr(x)
    if x is None or isinstance(x, (str, int, float, bool)):
        return x
    return repr(x)


def canonical(v):
    return json.dumps(v, sort_keys=True, default=str)


_SEG = re.compile(r"([^.\[\]]+)|\[(\*|-?\d+|[^\[\]=]+=[^\[\]]*)\]")


def parse_path(path):
    if path in ("", "."):
        return []
    out, pos = [], 0
    for m in _SEG.finditer(path):
        gap = path[pos:m.start()]
        if gap not in ("", "."):
            raise PathError(f"malformed path {path!r}")
        g = m.group(2)
        if m.group(1) is not None:
            out.append(m.group(1))
        elif g == "*":
            out.append("*")
        elif "=" in g:
            k, _, v = g.partition("=")
            out.append(("=", k, v))
        else:
            out.append(int(g))
        pos = m.end()
    if pos != len(path):
        raise PathError(f"malformed path {path!r}")
    return out


def select(obj, path):
    """The value at `path` in a normalised answer."""
    def walk(v, segs, where):
        if not segs:
            return v
        s, rest = segs[0], segs[1:]
        if s == "*":
            if not isinstance(v, list):
                raise PathError(f"{where}: [*] needs a list, found {type(v).__name__}")
            return [walk(w, rest, f"{where}[{i}]") for i, w in enumerate(v)]
        if isinstance(s, tuple):
            _, k, want = s
            if not isinstance(v, list):
                raise PathError(f"{where}: [{k}={want}] needs a list, found {type(v).__name__}")
            hits = [i for i, w in enumerate(v) if isinstance(w, dict) and k in w and
                    (w[k] if isinstance(w[k], str) else canonical(w[k])) == want]
            if len(hits) != 1:
                raise PathError(f"{where}: [{k}={want}] matches {len(hits)} items, not one")
            return walk(v[hits[0]], rest, f"{where}[{k}={want}]")
        if isinstance(s, int):
            if not isinstance(v, list) or not -len(v) <= s < len(v):
                raise PathError(f"{where}: no item [{s}]")
            return walk(v[s], rest, f"{where}[{s}]")
        if not isinstance(v, dict) or s not in v:
            raise PathError(f"{where or 'answer'}: no field {s!r}")
        return walk(v[s], rest, f"{where}.{s}" if where else s)
    return walk(obj, parse_path(path), "")


def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _quat_close(e, a, tol):
    if not (isinstance(e, list) and isinstance(a, list) and len(e) == len(a) == 4 and all(map(_number, e + a))):
        return False
    ne, na = math.sqrt(sum(c * c for c in e)), math.sqrt(sum(c * c for c in a))
    if ne == 0 or na == 0:
        return False
    dot = min(1.0, abs(sum(x * y for x, y in zip(e, a))) / (ne * na))
    return 2 * math.acos(dot) <= tol


def matches(expected, actual, tol=None, ordered=False):
    """Whether `actual` matches `expected`. tol: None (exact), a number (absolute, every number below), or
    {"rad": x} (a rotation). ordered: whether lists at this level keep their order."""
    if isinstance(tol, dict) and "rad" in tol:
        return _quat_close(expected, actual, tol["rad"])
    if _number(expected) and _number(actual):
        return expected == actual if tol is None else abs(expected - actual) <= tol
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return False
        if ordered:
            return all(matches(e, a, tol, ordered) for e, a in zip(expected, actual))
        return _multiset(expected, actual, tol)
    if isinstance(expected, dict) and isinstance(actual, dict):
        return set(expected) == set(actual) and all(matches(expected[k], actual[k], tol, ordered) for k in expected)
    return type(expected) is type(actual) and expected == actual


def _multiset(expected, actual, tol):
    """A one-to-one matching of expected to actual items (backtracking; lists in answers are small)."""
    used = [False] * len(actual)

    def place(i):
        if i == len(expected):
            return True
        for j, a in enumerate(actual):
            if not used[j] and matches(expected[i], a, tol, False):
                used[j] = True
                if place(i + 1):
                    return True
                used[j] = False
        return False
    return place(0)


def wrong_fields(expected, answer, tolerance=None, ordered=()):
    """The expected paths whose value in `answer` differs (a missing path is wrong). Returns [(path, reason)]."""
    tolerance = tolerance or {}
    out = []
    for path, exp in expected.items():
        try:
            act = select(answer, path)
        except PathError as e:
            out.append((path, f"missing: {e}"))
            continue
        if not matches(exp, act, tolerance.get(path), path in ordered):
            out.append((path, "different"))
    return out
