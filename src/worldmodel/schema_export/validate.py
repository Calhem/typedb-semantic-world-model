"""A small JSON Schema checker for the export format (LABS-1.024, E-7), so no new dependency is needed.

It supports the subset the format's schema uses: `type` (one or a list), `enum`, `const`, `properties`, `required`,
`additionalProperties` (true, false or a schema), `items`, `minItems`, `minimum`, `pattern`, and local `$ref`
(`#/$defs/<name>`). Any other keyword in a schema is refused, so the checker never silently ignores a rule.
"""

import json
import re
from pathlib import Path

FORMAT_SCHEMAS = {"wm-schema-export/1": Path(__file__).with_name("wm-schema-export-1.schema.json"),
                  "wm-schema-export/2": Path(__file__).with_name("wm-schema-export-2.schema.json"),
                  "wm-schema-export/3": Path(__file__).with_name("wm-schema-export-3.schema.json")}
# what the exporter writes (LABS-1.050: format 3 adds the event-role multiplicity); formats 1 and 2 are still read, each
# against the JSON Schema file it was written for (unchanged)
CURRENT = "wm-schema-export/3"
FORMAT_SCHEMA = FORMAT_SCHEMAS[CURRENT]
SUPPORTED = {"$schema", "$id", "$defs", "$ref", "title", "description", "type", "enum", "const", "properties",
             "required", "additionalProperties", "items", "minItems", "minimum", "pattern"}
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def _is(value, t):
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES[t])


def errors(value, schema, root=None, path="$"):
    """Every way `value` breaks `schema`, as readable lines (empty: valid)."""
    root = root if root is not None else schema
    unknown = set(schema) - SUPPORTED
    if unknown:
        return [f"{path}: the checker does not support {sorted(unknown)}"]
    if "$ref" in schema:
        name = schema["$ref"].removeprefix("#/$defs/")
        return errors(value, root["$defs"][name], root, path)
    out = []
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is(value, t) for t in types):
            return [f"{path}: expected {' or '.join(types)}, found {type(value).__name__}"]
    if "const" in schema and value != schema["const"]:
        out.append(f"{path}: must be {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        out.append(f"{path}: {value!r} is not one of {schema['enum']}")
    if "pattern" in schema and isinstance(value, str) and not re.search(schema["pattern"], value):
        out.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if "minimum" in schema and isinstance(value, (int, float)) and value < schema["minimum"]:
        out.append(f"{path}: below {schema['minimum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                out.append(f"{path}: missing {key!r}")
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key, v in value.items():
            if key in props:
                out += errors(v, props[key], root, f"{path}.{key}")
            elif extra is False:
                out.append(f"{path}: unexpected {key!r}")
            elif isinstance(extra, dict):
                out += errors(v, extra, root, f"{path}.{key}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            out.append(f"{path}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for i, v in enumerate(value):
                out += errors(v, schema["items"], root, f"{path}[{i}]")
    return out


def format_schema(fmt=CURRENT):
    return json.loads(FORMAT_SCHEMAS[fmt].read_text())


def validate(doc):
    """Errors of an export document against the JSON Schema of the format it declares (empty: valid): format 3, format
    2 for exports written from LABS-1.043 to LABS-1.049, or format 1 for exports written before LABS-1.043. A document
    declaring another format is checked against the current one, which rejects its `format`.

    Format 3 also requires every event-role-constraint record to state its multiplicity (a rule the JSON Schema subset
    cannot say per record kind), so a record can never be read as single-valued by omission."""
    fmt = doc.get("format") if isinstance(doc, dict) else None
    out = errors(doc, format_schema(fmt if fmt in FORMAT_SCHEMAS else CURRENT))
    if fmt == "wm-schema-export/3" and isinstance(doc.get("module_data"), dict):
        for i, r in enumerate(doc["module_data"].get("records", [])):
            if isinstance(r, dict) and r.get("kind") == "event-role-constraint" and "multiplicity" not in r:
                out.append(f"$.module_data.records[{i}]: an event-role-constraint record must state its multiplicity "
                           f"in format 3")
    return out
