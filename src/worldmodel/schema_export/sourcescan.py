"""Read the repository's hand-written `.tql` module files (LABS-1.024). Everything here is **repository** evidence:
it is never checked against the database, and never decides attribution or any database fact (E-2, E-4).

It is used for two things:
- the comments written next to each declaration (E-4(b): documentation from the repository);
- the declarations a module's source text repeats although an earlier module already made them. TypeDB accepts
  such a repeat silently, so a replay cannot see it; the export reports it as a repository note (section 10).

The scanner is tolerant, not exact: what it cannot read it reports (`unread`), and the attribution checks which
replayed declarations the scan did not find (`missing_from_scan`).
"""

import re
from dataclasses import dataclass, field

KINDS = ("entity", "relation", "attribute")
KEYWORDS = ("sub", "value", "owns", "plays", "relates")


@dataclass
class SourceStatement:
    file: str
    line: int                          # 1-based line of the statement's first character
    end: int = 0                       # 1-based line of its terminating `;`
    text: str = ""                     # the statement, whitespace collapsed, comments removed
    comments: list = field(default_factory=list)   # comment lines written before it, inside it, or after it on its last line
    subject: str | None = None         # the type label, or the function name
    kind: str | None = None            # entity | relation | attribute | fun | None (kind not written)
    facts: list = field(default_factory=list)      # fact ids in the export's form (parse.facts)


@dataclass
class SourceFile:
    file: str
    header: list                       # comment lines before the first statement (the module's own description)
    statements: list
    unread: list                       # statements the scanner could not read, as (line, text)


def normalise_annotation(a):
    """`@values("a","b")` -> `@values("a", "b")`: the spacing TypeDB uses in schema()."""
    m = re.match(r"^(@[a-z]+)(?:\((.*)\))?$", a, re.S)
    if not m or m.group(2) is None:
        return a
    out, in_str = [], False
    for ch in m.group(2):
        if ch == '"':
            in_str = not in_str
        if not in_str and ch.isspace():
            continue
        out.append(ch)
        if not in_str and ch == ",":
            out.append(" ")
    return f"{m.group(1)}({''.join(out)})"


def _split(text, sep):
    """Split at `sep` outside quotes and brackets."""
    parts, depth, in_str, cur = [], 0, False, []
    for ch in text:
        if ch == '"':
            in_str = not in_str
        elif not in_str and ch in "({[":
            depth += 1
        elif not in_str and ch in ")}]":
            depth -= 1
        if ch == sep and depth == 0 and not in_str:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def _tokens(text):
    return [t for t in re.findall(r'@[a-z]+(?:\((?:[^()"]|"[^"]*")*\))?|[^\s,]+', text)]


def _clause_facts(label, tokens, kinds):
    """Facts of one clause (`owns x @key`, `relates r as p`, ...) of type `label`. None if unreadable."""
    if not tokens:
        return []
    if all(t.startswith("@") for t in tokens):                          # type annotations
        kind = kinds.get(label)
        return [f"{kind} {label} {normalise_annotation(t)}" for t in tokens] if kind else None
    kw, rest = tokens[0], tokens[1:]
    if kw not in KEYWORDS or not rest:
        return None
    target, rest = rest[0], rest[1:]
    if kw == "value":
        return [f"{label} value {target}"] + [f"{label} value {normalise_annotation(a)}" for a in rest
                                              if a.startswith("@")]
    base = f"{label} {kw} {target}"
    out = [base]
    if kw == "relates" and len(rest) >= 2 and rest[0] == "as":
        out.append(f"{base} as {rest[1]}")
        rest = rest[2:]
    if any(not a.startswith("@") for a in rest):
        return None
    return out + [f"{base} {normalise_annotation(a)}" for a in rest]


def _statement(file, line, text, comments, kinds):
    st = SourceStatement(file, line, text=text, comments=comments)
    words = text.split()
    if words and words[0] == "fun":
        m = re.match(r"^fun\s+([A-Za-z_][A-Za-z0-9_-]*)\s*\(", text)
        if not m:
            return st, False
        st.subject, st.kind, st.facts = m.group(1), "fun", [f"fun {m.group(1)}"]
        return st, True
    clauses = _split(text, ",")
    head = _tokens(clauses[0])
    if head and head[0] in KINDS:
        st.kind, head = head[0], head[1:]
    if not head:
        return st, False
    st.subject, head = head[0], head[1:]
    kinds = {**kinds, **({st.subject: st.kind} if st.kind else {})}
    if st.kind:
        st.facts.append(f"{st.kind} {st.subject}")
    annotations = []
    while head and head[0].startswith("@"):
        annotations.append(head.pop(0))
    if annotations:
        st.facts += _clause_facts(st.subject, annotations, kinds) or []
    for tokens in [head] + [_tokens(c) for c in clauses[1:]]:
        f = _clause_facts(st.subject, tokens, kinds)
        if f is None:
            return st, False
        st.facts += f
    return st, True


def _code_and_comments(text):
    """Per line: the code, and the comment (text after `#` outside a string), if any."""
    code, comments = [], []
    for n, raw in enumerate(text.split("\n"), 1):
        in_str, cut = False, None
        for i, ch in enumerate(raw):
            if ch == '"':
                in_str = not in_str
            elif ch == "#" and not in_str:
                cut = i
                break
        code.append(raw if cut is None else raw[:cut])
        if cut is not None:
            comments.append((n, raw[cut + 1:].strip()))
    return code, comments


def _segments(code):
    """(first line, last line, text) of each `;`-terminated piece of code, outside strings and brackets."""
    out, cur, start, depth, in_str = [], [], None, 0, False
    for n, line in enumerate(code, 1):
        for ch in line + "\n":
            if ch == '"':
                in_str = not in_str
            elif not in_str and ch in "({[":
                depth += 1
            elif not in_str and ch in ")}]":
                depth -= 1
            if ch == ";" and depth == 0 and not in_str:
                out.append((start, n, " ".join("".join(cur).split())))
                cur, start = [], None
                continue
            if start is None and not ch.isspace():
                start = n
            cur.append(ch)
    rest = " ".join("".join(cur).split())
    return out, (start, rest) if rest else None


def scan(text, file, kinds=None):
    """Statements of a TypeQL module file with their comments and facts. `kinds` (label -> kind, from the database)
    fills in the kind for statements that do not write it (`particular plays x:y;`)."""
    kinds = kinds or {}
    code, comments = _code_and_comments(text)
    segments, tail = _segments(code)
    define_line = None
    merged = []                                   # (first line, last line, text), functions joined
    for first, last, body in segments:
        if body.startswith("define"):
            if define_line is None:
                define_line = first
            body = body[len("define"):].strip()
            first = next((n for n in range(first, last + 1) if code[n - 1].strip() not in ("", "define")), first)
        if merged and merged[-1][2].startswith("fun ") and not merged[-1][3]:
            f, _, t, _ = merged[-1]
            merged[-1] = (f, last, f"{t}; {body}", body.startswith("return"))
            continue
        if body:
            merged.append((first, last, body, not body.startswith("fun ")))
    statements, unread = [], []
    for first, last, body, complete in merged:
        st, ok = _statement(file, first, body, [], kinds)
        st.end = last
        if ok and complete:
            statements.append(st)
        else:
            unread.append((first, body))
    if tail:
        unread.append(tail)
    header = []
    for n, c in comments:
        if define_line is not None and n < define_line:
            header.append(c)
            continue
        owner = next((st for st in statements if st.line <= n <= st.end), None)
        if owner is None:
            owner = next((st for st in statements if st.line > n), None)
        if owner is not None:
            owner.comments.append(c)
        elif not statements or n < statements[0].line:
            header.append(c)
    return SourceFile(file, header, statements, unread)
