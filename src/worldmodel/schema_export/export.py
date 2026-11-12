"""Build and write the schema export (LABS-1.024): `wm-schema-export/1`.

The export is a JSON document whose top-level sections each have one source (LABS-1.032 requirement 1):

- `source`, `verification`, `schema`: **database**. Read from TypeDB, or computed by the exporter from those reads
  alone (the computed fields are listed in `schema.computed_fields`).
- `attribution`: **reconstructed**. Core and profile attribution by verified replay (attribution.py); its
  `repository_notes` part is **repository** evidence.
- `documentation`: **repository**. Comments from the module files, never checked against the database.
- `module_data`: the records are **database**; which module wrote each is **reconstructed**.
- `export`: about the export itself (time, exporter, the code commit used for the replay and the comments).

The export fails (SchemaExportError) unless the parse accounts for every character of the schema text, the query
cross-check agrees exactly, and the round trip is identical. Attribution never fails the export: its result, verified
or not, is reported.
"""

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from ..model import SCHEMA_DIR
from .attribution import SETUP, attribute
from .crosscheck import Lattice, cross_check, round_trip
from .docs import documentation, module_data
from .introspect import snapshot
from .parse import facts, parse_schema, render_type

FORMAT = "wm-schema-export/1"
EXPORTER = "worldmodel.schema_export 1.0.0"
PROVENANCE = {
    "database": "Read from the TypeDB database (schema() text, query answers, records), or computed by the exporter "
                "from those reads alone.",
    "reconstructed": "Needs this repository's code as well as the database: core and profile attribution by replaying "
                     "the recorded modules into temporary databases and comparing with the database. Checked against "
                     "the database, not stored in it.",
    "repository": "Taken from this repository's files only (comments in .tql module files). Never checked against "
                  "the database.",
}
STATUSES = {
    "attributed": "Proven by a complete matching replay: exactly one module adds it.",
    "shared": "Proven by a complete matching replay: more than one module adds it. All are listed; none is the owner.",
    "consistent_unverified": "Replay steps add it (the candidates are listed), but the complete replay did not match "
                             "the database, so nothing is proven.",
    "unresolved": "Attribution cannot be established: no replay step adds it.",
}
SINGLE_SOURCE = {
    "annotations": "From the schema() text only: TypeDB 3.14.1 cannot query annotations (REP254). Checked by the "
                   "exact parse and the round trip, not by a query.",
    "functions": "From the schema() text only: TypeDB 3.14.1 has no query that lists functions. Checked by the exact "
                 "parse and the round trip; signatures are parsed, bodies are kept as text.",
}
COMPUTED_FIELDS = [
    "types.*.supertypes", "types.*.subtypes", "types.*.owns[].from", "types.*.plays[].from", "types.*.relates[].from",
    "types.*.owns[].declared", "types.*.plays[].declared", "types.*.relates[].declared", "types.*.value_type.from",
    "types.*.statement", "types.*.facts", "types.*.functions", "roles", "attributes_owned_by",
    "functions.*.params", "functions.*.return_types", "functions.*.types_named", "facts",
]
VOLATILE = (("export", "exported_at"), ("export", "code_commit"), ("export", "code_dirty"), ("source", "database"))


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _git(*args):
    try:
        out = subprocess.run(["git", *args], cwd=SCHEMA_DIR.parent, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def code_state():
    """The git commit of this repository's code (used for the replay and the comments), and whether src/ or schema/
    has uncommitted changes."""
    commit = _git("rev-parse", "HEAD")
    dirty = _git("status", "--porcelain", "--", "src", "schema")
    return commit, (bool(dirty) if dirty is not None else None)


def _schema_section(parsed, lattice, fact_map):
    labels = set(parsed.types)
    subtypes = defaultdict(list)
    for child, parent in lattice.parent.items():
        subtypes[parent].append(child)
    functions = {}
    for f in parsed.functions.values():
        words = set(re.findall(r"(?<![\w$-])[A-Za-z_][A-Za-z0-9_-]*", f.text))
        functions[f.name] = {"name": f.name, "params": [{"variable": v, "type": t} for v, t in f.params],
                             "returns": f.returns, "stream": f.stream, "return_types": list(f.return_types),
                             "types_named": sorted(labels & words), "text": f.text}
    named_by = defaultdict(list)
    for f in functions.values():
        for t in f["types_named"]:
            named_by[t].append(f["name"])
    facts_of = defaultdict(list)
    for fid, v in fact_map.items():
        if v["kind"] != "function":
            facts_of[v["subject"]].append(fid)

    def caps(label, keyword, key):
        out = []
        for target, frm, d in lattice.capabilities(label, keyword):
            row = {key: target, "annotations": list(d.annotations), "from": frm, "declared": frm == label}
            if keyword == "relates":
                row = {"role": target, "name": d.target,
                       "specialises": lattice.role_parent(frm, d) if d.specialises else None,
                       "annotations": list(d.annotations), "from": frm, "declared": frm == label}
            out.append(row)
        return sorted(out, key=lambda r: r[key])

    types = {}
    for label in sorted(labels):
        t = parsed.types[label]
        entry = {"label": label, "kind": t.kind, "annotations": list(t.annotations),
                 "abstract": "@abstract" in t.annotations,
                 "supertype": lattice.parent.get(label), "supertypes": lattice.chain(label),
                 "subtypes": sorted(subtypes.get(label, [])),
                 "value_type": None,
                 "owns": caps(label, "owns", "attribute"), "plays": caps(label, "plays", "role"),
                 "relates": caps(label, "relates", "role") if t.kind == "relation" else [],
                 "statement": render_type(t), "facts": sorted(facts_of[label]),
                 "functions": sorted(named_by.get(label, []))}
        if t.kind == "attribute":
            vt, frm = lattice.value_type(label)
            if vt:
                decl = lattice.declared(frm, "value")[0]
                entry["value_type"] = {"type": vt, "from": frm, "declared": frm == label,
                                       "annotations": list(decl.annotations)}
        types[label] = entry

    roles = {}
    for label in sorted(labels):
        if parsed.types[label].kind != "relation":
            continue
        for d in lattice.declared(label, "relates"):
            scoped = f"{label}:{d.target}"
            roles[scoped] = {"role": scoped, "relation": label, "name": d.target,
                             "specialises": lattice.role_parent(label, d) if d.specialises else None,
                             "annotations": list(d.annotations), "specialised_by": [],
                             "related_by": sorted(x for x in labels if any(r["role"] == scoped for r in types[x]["relates"])),
                             "played_by_declared": sorted(x for x in labels if any(
                                 p["role"] == scoped and p["declared"] for p in types[x]["plays"])),
                             "played_by": sorted(x for x in labels if any(p["role"] == scoped for p in types[x]["plays"]))}
    for scoped, r in roles.items():
        if r["specialises"] in roles:
            roles[r["specialises"]]["specialised_by"].append(scoped)
    owned_by = defaultdict(list)
    for label, t in types.items():
        for o in t["owns"]:
            owned_by[o["attribute"]].append(label)
    catalog = {}
    for fid in sorted(fact_map):
        v = {k: x for k, x in fact_map[fid].items() if k != "text"}
        catalog[fid] = v
    return {"provenance": "database", "computed_fields": COMPUTED_FIELDS, "single_source": SINGLE_SOURCE,
            "counts": {"types": len(types), "entity": sum(t["kind"] == "entity" for t in types.values()),
                       "relation": sum(t["kind"] == "relation" for t in types.values()),
                       "attribute": sum(t["kind"] == "attribute" for t in types.values()),
                       "roles": len(roles), "functions": len(functions), "facts": len(catalog)},
            "types": types, "roles": roles,
            "attributes_owned_by": {a: sorted(ts) for a, ts in sorted(owned_by.items())},
            "functions": functions, "facts": catalog, "typeql": parsed.text}


def _attribution_section(attr, parsed, fact_map):
    types = {}
    for label, t in sorted(parsed.types.items()):
        intro = attr.facts[f"{t.kind} {label}"]
        contributions, unresolved = defaultdict(list), []
        for fid, v in fact_map.items():
            if v["kind"] == "function" or v["subject"] != label:
                continue
            mods = attr.facts[fid]["modules"]
            if not mods:
                unresolved.append(fid)
            for m in mods:
                contributions[m].append(fid)
        types[label] = {"introduced_by": {"status": intro["status"], "modules": intro["modules"]},
                        "extended_by": sorted(m for m in contributions if m not in intro["modules"]),
                        "contributions": {m: sorted(fs) for m, fs in sorted(contributions.items())},
                        "unresolved": sorted(unresolved)}
    counts = Counter(v["status"] for v in attr.facts.values())
    return {
        "provenance": "reconstructed",
        "method": "The modules recorded in the database are replayed from this repository's code into temporary "
                  "databases: the core one module at a time, each profile alone on the core, and all together. The "
                  "complete replay must equal the database's schema facts and module records exactly.",
        "verification": "verified" if attr.verified else "failed",
        "problems": attr.problems,
        "statuses": STATUSES,
        "counts": {s: counts.get(s, 0) for s in STATUSES},
        "modules": attr.modules,
        "facts": {fid: {"status": v["status"], "modules": v["modules"]} for fid, v in sorted(attr.facts.items())},
        "types": types,
        "functions": {name: {"status": attr.facts[f"fun {name}"]["status"],
                             "modules": attr.facts[f"fun {name}"]["modules"]} for name in parsed.functions},
        "unresolved": sorted(fid for fid, v in attr.facts.items() if v["status"] == "unresolved"),
        "limitations": [
            "A declaration that repeats one already in the schema leaves no trace in a replay; it is attributed to "
            "the module that first adds it. Repeats found in module source text are listed under repository_notes.",
            "Core modules are replayed in their canonical order; profiles are replayed each alone on the core.",
            f"'{SETUP}' is the setup step after the core modules (the system agent and the core functional slots).",
        ],
        "repository_notes": {
            "provenance": "repository",
            "also_declared_in_source": {fid: v["also_declared_in_source"] for fid, v in sorted(attr.facts.items())
                                        if v.get("also_declared_in_source")},
            "scan": attr.source,
        },
    }


def build_export(driver, database, profiles=None, prefix="wm-export-tmp-", now=None):
    """Read, check, attribute and model the schema of `database`. Returns (document, schema text, timings)."""
    import time
    t0 = time.perf_counter()
    snap = snapshot(driver, database)
    t1 = time.perf_counter()
    parsed = parse_schema(snap.text)
    fact_map = facts(parsed)
    lattice = Lattice(parsed)
    compared = cross_check(lattice, snap.answers)
    t2 = time.perf_counter()
    trip = round_trip(driver, parsed, snap.text, prefix=prefix)
    t3 = time.perf_counter()
    attr = attribute(driver, snap, fact_map, profiles=profiles, prefix=prefix)
    t4 = time.perf_counter()
    commit, dirty = code_state()
    doc = {
        "format": FORMAT,
        "provenance": PROVENANCE,
        "source": {"provenance": "database", "database": database, "server_version": snap.server_version,
                   "schema_sha256": sha256(snap.text), "schema_characters": len(snap.text),
                   "modules": dict(sorted(snap.modules.items()))},
        "export": {"exporter": EXPORTER, "exported_at": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
                   "code_commit": commit, "code_dirty": dirty},
        "verification": {"provenance": "database",
                         "parse": {"passed": True, "exact": True, "facts": len(fact_map)},
                         "query_cross_check": {"passed": True, "compared": compared},
                         "round_trip": {"passed": True, **trip},
                         "single_source": SINGLE_SOURCE},
        "schema": _schema_section(parsed, lattice, fact_map),
        "attribution": _attribution_section(attr, parsed, fact_map),
        "documentation": documentation(list(snap.modules), {t.label: t.kind for t in parsed.types.values()},
                                       set(parsed.functions), profiles=profiles),
        "module_data": module_data(attr),
    }
    timings = {"read": t1 - t0, "parse_and_cross_check": t2 - t1, "round_trip": t3 - t2, "replay": t4 - t3,
               "model": time.perf_counter() - t4}
    return doc, snap.text, attr, timings


def dumps(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def manifest(doc, files):
    """The manifest: what was exported, from where, the verification results, and a SHA-256 for each file."""
    a = doc["attribution"]
    out = {"format": "wm-schema-export-manifest/1", "source": doc["source"], "export": doc["export"],
           "schema_sha256": doc["source"]["schema_sha256"],
           "verification": {"parse": doc["verification"]["parse"]["passed"],
                            "query_cross_check": doc["verification"]["query_cross_check"]["passed"],
                            "round_trip": doc["verification"]["round_trip"]["passed"]},
           "replay_verification": a["verification"], "replay_problems": a["problems"],
           "attribution_counts": a["counts"], "unresolved": a["unresolved"],
           "files": {name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                     for name, data in sorted(files.items())}}
    out["module_data_verification"] = doc["module_data"]["verification"]
    out["module_data_unresolved"] = doc["module_data"]["unresolved"]
    out["documentation"] = {"provenance": "repository", "types_documented": len(doc["documentation"]["types"]),
                            "unknown_labels": [u["label"] for u in doc["documentation"]["unknown_labels"]]}
    return out


def write_export(doc, text, out_dir, extra_files=None):
    """Write schema.tql (exactly schema()), schema.json, any extra files, and manifest.json into out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {"schema.tql": text.encode(), "schema.json": dumps(doc).encode(), **(extra_files or {})}
    for name, data in files.items():
        (out_dir / name).write_bytes(data)
    (out_dir / "manifest.json").write_text(dumps(manifest(doc, files)))
    return sorted(list(files) + ["manifest.json"])


def masked(doc):
    """A copy of an export with the fields that change on every run (time, code commit, database name) blanked, for
    comparing two exports of the same schema."""
    out = json.loads(json.dumps(doc))
    for section, key in VOLATILE:
        if section in out and key in out[section]:
            out[section][key] = None
    return out


def export_to(driver, database, out_dir, profiles=None, prefix="wm-export-tmp-", now=None):
    """Export `database` into `out_dir`. Returns (document, files written, timings). Nothing is written if the
    export is refused."""
    doc, text, _, timings = build_export(driver, database, profiles=profiles, prefix=prefix, now=now)
    written = write_export(doc, text, out_dir)
    return doc, written, timings
