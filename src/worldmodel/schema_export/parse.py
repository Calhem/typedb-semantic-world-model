"""Parse the schema text TypeDB returns (`database.schema()`) into declarations, and render it back (LABS-1.024, E-1).

TypeDB returns its own normalised form, not the hand-written files. That form is strict:

    define
    <blank line>
    entity|relation|attribute <label>[ @annotation ...](,|;)       one statement per type, its header
     value <value type>[ @annotation ...](,|;)                      one space before `value`
      sub|owns|plays|relates <target>[ as <role>][ @annotation ...](,|;)   two spaces before the others
    fun <name>(<parameters>) -> <returns>:                           functions last, kept as text

The parser accepts exactly this form and refuses anything else (`SchemaParseError`), and `parse_schema` checks that
rendering the parsed schema reproduces the text byte for byte. So every character of the schema is accounted for:
nothing the database returns can be silently dropped (LABS-1.033, schema fidelity).
"""

import re
from dataclasses import dataclass, field

KINDS = ("entity", "relation", "attribute")
LABEL = r"[A-Za-z_][A-Za-z0-9_-]*"
ROLE = rf"{LABEL}:{LABEL}"
# an annotation: @name, optionally with arguments; quoted strings may hold any character
ANNOTATION = re.compile(r'@[a-z]+(?:\((?:[^()"]|"(?:[^"\\]|\\.)*")*\))?')
HEADER = re.compile(rf"^(?P<kind>{'|'.join(KINDS)}) (?P<label>{LABEL})(?P<ann>(?: @.*?)?)(?P<end>[,;])$")
DECL = re.compile(r"^(?P<indent> +)(?P<kw>sub|value|owns|plays|relates) (?P<rest>.+?)(?P<end>[,;])$")
INDENT = {"value": " ", "sub": "  ", "owns": "  ", "plays": "  ", "relates": "  "}
TARGET = {"sub": re.compile(rf"^{LABEL}$"), "value": re.compile(rf"^{LABEL}$"), "owns": re.compile(rf"^{LABEL}$"),
          "plays": re.compile(rf"^{ROLE}$"), "relates": re.compile(rf"^{LABEL}$")}
ALLOWED = {"entity": {"sub", "owns", "plays"}, "relation": {"sub", "relates", "owns", "plays"},
           "attribute": {"sub", "value", "owns", "plays"}}
SIGNATURE = re.compile(rf"^fun (?P<name>{LABEL})\((?P<params>.*)\) -> (?P<returns>.+):$")


class SchemaExportError(Exception):
    """The export was refused: the exporter could not account for the database's schema exactly."""

    def __init__(self, message, problems=()):
        self.problems = list(problems)
        super().__init__(message + ("".join(f"\n  - {p}" for p in self.problems[:50])))


class SchemaParseError(SchemaExportError):
    """The schema text is not in the form the parser accounts for exactly."""


@dataclass(frozen=True)
class Declaration:
    keyword: str                      # sub | value | owns | plays | relates
    target: str                       # a type label, a value type, or a role (`relation:role` for plays)
    specialises: str | None = None    # relates <role> as <parent role>
    annotations: tuple = ()

    def text(self):
        return " ".join([self.keyword, self.target] + (["as", self.specialises] if self.specialises else [])
                        + list(self.annotations))


@dataclass
class TypeStatement:
    kind: str
    label: str
    annotations: tuple = ()
    declarations: list = field(default_factory=list)


@dataclass(frozen=True)
class Function:
    name: str
    text: str                         # the whole definition, exactly as the database returns it
    params: tuple                     # ((variable, type), ...)
    returns: str                      # the return clause as written, e.g. "{ particular }"
    stream: bool                      # True for `{ ... }` (a stream of answers)
    return_types: tuple


@dataclass
class ParsedSchema:
    text: str
    types: dict                       # label -> TypeStatement, in the database's order
    functions: dict                   # name -> Function, in the database's order


def _annotations(text, where):
    """Split ' @a @b(...)' into ('@a', '@b(...)'); anything else is refused."""
    out, pos, text = [], 0, text.strip()
    while pos < len(text):
        m = ANNOTATION.match(text, pos)
        if not m:
            raise SchemaParseError("unrecognised annotation text", [f"{where}: {text[pos:]!r}"])
        out.append(m.group(0))
        pos = m.end()
        if pos < len(text):
            if text[pos] != " ":
                raise SchemaParseError("unrecognised annotation text", [f"{where}: {text[pos:]!r}"])
            pos += 1
    return tuple(out)


def _declaration(m, kind, where):
    kw, rest = m.group("kw"), m.group("rest")
    if m.group("indent") != INDENT[kw]:
        raise SchemaParseError("unexpected indentation", [where])
    if kw not in ALLOWED[kind]:
        raise SchemaParseError(f"`{kw}` is not expected on an {kind}", [where])
    target, _, tail = rest.partition(" ")
    specialises = None
    if kw == "relates" and tail.startswith("as "):
        specialises, _, tail = tail[3:].partition(" ")
        if not re.fullmatch(LABEL, specialises):
            raise SchemaParseError("unrecognised specialisation", [where])
    if not TARGET[kw].match(target):
        raise SchemaParseError(f"unrecognised `{kw}` target", [where])
    return Declaration(kw, target, specialises, _annotations(tail, where) if tail else ())


def _function(lines, where):
    head = SIGNATURE.match(lines[0])
    if not head:
        raise SchemaParseError("unrecognised function signature", [where])
    params = []
    for p in filter(None, (x.strip() for x in head.group("params").split(","))):
        var, sep, typ = p.partition(":")
        if not sep or not re.fullmatch(r"\$[A-Za-z_][A-Za-z0-9_]*", var.strip()):
            raise SchemaParseError("unrecognised function parameter", [f"{where}: {p!r}"])
        params.append((var.strip(), typ.strip()))
    returns = head.group("returns").strip()
    stream = returns.startswith("{") and returns.endswith("}")
    inner = returns[1:-1] if stream else returns
    return Function(head.group("name"), "\n".join(lines), tuple(params), returns, stream,
                    tuple(x.strip() for x in inner.split(",") if x.strip()))


def parse_schema(text):
    """Parse a `schema()` text. Raises SchemaParseError unless every line is accounted for exactly."""
    if text.strip() in ("", "define"):          # an empty database returns `define` alone
        parsed = ParsedSchema(text, {}, {})
    else:
        lines = text.split("\n")
        if lines[:2] != ["define", ""]:
            raise SchemaParseError("the schema text does not start with `define` and a blank line", [repr(lines[:2])])
        types, functions, i, current = {}, {}, 2, None
        while i < len(lines) and not lines[i].startswith("fun "):
            line, where = lines[i], f"line {i + 1}: {lines[i]!r}"
            if current is None:
                m = HEADER.match(line)
                if not m:
                    raise SchemaParseError("unrecognised schema line", [where])
                if m.group("label") in types:
                    raise SchemaParseError("a type has two statements", [where])
                current = TypeStatement(m.group("kind"), m.group("label"), _annotations(m.group("ann"), where))
                types[current.label] = current
            else:
                m = DECL.match(line)
                if not m:
                    raise SchemaParseError("unrecognised schema line", [where])
                current.declarations.append(_declaration(m, current.kind, where))
            if m.group("end") == ";":
                current = None
            i += 1
        if current is not None:
            raise SchemaParseError("the last type statement is not terminated", [current.label])
        starts = [j for j in range(i, len(lines)) if lines[j].startswith("fun ")]
        if i < len(lines) and (not starts or starts[0] != i):
            raise SchemaParseError("unrecognised text after the type statements", [repr(lines[i])])
        for a, b in zip(starts, starts[1:] + [len(lines)]):
            f = _function(lines[a:b], f"line {a + 1}: {lines[a]!r}")
            if f.name in functions:
                raise SchemaParseError("a function is defined twice", [f.name])
            functions[f.name] = f
        parsed = ParsedSchema(text, types, functions)
    again = render_schema(parsed)
    if again != text:
        at = next((k for k, (a, b) in enumerate(zip(again, text)) if a != b), min(len(again), len(text)))
        raise SchemaParseError("the parsed schema does not reproduce the schema text exactly",
                               [f"first difference at character {at}: {text[max(0, at - 40):at + 40]!r}"])
    return parsed


def render_type(t):
    head = " ".join([t.kind, t.label, *t.annotations])
    if not t.declarations:
        return head + ";"
    body = [INDENT[d.keyword] + d.text() for d in t.declarations]
    return ",\n".join([head] + body) + ";"


def render_schema(parsed):
    """The TypeQL text of a parsed schema, in TypeDB's normalised form."""
    if not parsed.types and not parsed.functions:
        return parsed.text if parsed.text.strip() in ("", "define") else "define"
    parts = ["define", "", *(render_type(t) for t in parsed.types.values())]
    parts += [f.text for f in parsed.functions.values()]
    return "\n".join(parts)


def facts(parsed):
    """Every declaration of the schema as one fact, keyed by a readable id in TypeQL words. Annotations and
    specialisations are facts of their own, so attribution can be made per contribution (E-2):

        entity sample                       the type exists, with its kind
        entity particular @abstract         a type annotation
        sample sub physical-object          a supertype
        credence value double               an attribute's value type
        credence value @range(0.0..1.0)     a value annotation
        particular owns wm-id               ownership; `particular owns wm-id @key` is its annotation
        particular plays sampling:sampler   a role played (with annotations likewise)
        sampling relates sampler            a role related; `sampling relates sampler as actor` its specialisation
        fun parts_in                        a function (its payload holds the full text)

    Returns {id: payload}; the payload says what the fact is (`subject`, `kind`, and `of` for annotations)."""
    out = {}

    def add(fid, **payload):
        if fid in out:
            raise SchemaParseError("a declaration appears twice", [fid])
        out[fid] = payload

    for t in parsed.types.values():
        add(f"{t.kind} {t.label}", subject=t.label, kind="type", type_kind=t.kind)
        for a in t.annotations:
            add(f"{t.kind} {t.label} {a}", subject=t.label, kind="annotation", of=f"{t.kind} {t.label}", annotation=a)
        for d in t.declarations:
            base = f"{t.label} {d.keyword} {'' if d.keyword == 'value' else d.target}".rstrip()
            if d.keyword == "value":
                add(f"{t.label} value {d.target}", subject=t.label, kind="value", target=d.target)
            else:
                add(base, subject=t.label, kind=d.keyword, target=d.target)
            if d.specialises:
                add(f"{base} as {d.specialises}", subject=t.label, kind="specialisation", of=base,
                    target=d.target, specialises=d.specialises)
            for a in d.annotations:
                add(f"{base} {a}", subject=t.label, kind="annotation",
                    of=base if d.keyword != "value" else f"{t.label} value {d.target}", annotation=a)
    for f in parsed.functions.values():
        add(f"fun {f.name}", subject=f.name, kind="function", text=f.text)
    return out
