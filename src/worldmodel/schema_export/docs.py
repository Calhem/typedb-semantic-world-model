"""Documentation from the repository and module data (LABS-1.024, E-4(b) and E-5).

**Documentation** is the comments written in the `.tql` files of the modules the database records. It is labelled
`repository`: read from this repository's files, never checked against the database, and never used for attribution
or for any database field. Comments on statements whose type the database does not have are reported, not dropped.

**Module data** is the concept and functional-slot records the module replay writes. The records the database holds
are `database`; which module wrote each is `reconstructed` (attribution.py). A record the replay writes but the
database lacks is listed with source `reconstructed` only.
"""

import re
from pathlib import Path

from .attribution import registry
from .sourcescan import scan

DIVIDER = re.compile(r"^[-=]{3,}\s*|\s*[-=]{3,}$")


def _clean(lines):
    out = []
    for line in lines:
        line = DIVIDER.sub("", line).strip()
        if line:
            out.append(line)
    return out


def documentation(modules, kinds, functions, profiles=None):
    """The `documentation` section: per type and function, the comments of the statements that declare it."""
    reg = registry(profiles)
    root = Path(__file__).resolve().parents[3]
    files, types, funs, unknown = {}, {}, {}, []
    for m in modules:
        if m not in reg:
            continue
        header = []
        for f in reg[m]["files"]:
            path = Path(f)
            rel = str(path.resolve().relative_to(root)) if path.resolve().is_relative_to(root) else path.name
            sf = scan(path.read_text(), rel, kinds)
            header += _clean(sf.header)
            for st in sf.statements:
                lines = _clean(st.comments)
                if not lines:
                    continue
                entry = {"module": m, "file": rel, "line": st.line, "comment": " ".join(lines), "declares": st.facts}
                if st.kind == "fun":
                    target = funs if st.subject in functions else None
                else:
                    target = types if st.subject in kinds else None
                if target is None:
                    unknown.append({"label": st.subject, "module": m, "file": rel, "line": st.line})
                else:
                    target.setdefault(st.subject, []).append(entry)
        files[m] = {"files": [str(Path(f).resolve().relative_to(root)) if Path(f).resolve().is_relative_to(root)
                              else Path(f).name for f in reg[m]["files"]],
                    "header": " ".join(header)}
    return {
        "provenance": "repository",
        "description": "Comments from the .tql files of the modules recorded in the database, read from this "
                       "repository (export.code_commit). Not checked against the database; they never affect "
                       "attribution or any database field.",
        "modules": files,
        "types": {k: types[k] for k in sorted(types)},
        "functions": {k: funs[k] for k in sorted(funs)},
        "unknown_labels": unknown,
        "undocumented": sorted(set(kinds) - set(types)),
    }


def module_data(attr):
    """The `module_data` section from the attribution's module-data result."""
    records, unresolved = [], []
    for rec, d in sorted(attr.data.items(), key=lambda x: (x[0][0], str(x[0][1:]))):
        if rec[0] == "concept":
            _, kind, rid, name = rec
            row = {"kind": "concept", "type": kind, "id": rid, "name": name}
        else:
            _, rid, predicate, key_roles, value_role = rec
            row = {"kind": "functional-slot", "id": rid, "predicate": predicate, "key_roles": list(key_roles),
                   "value_role": value_role}
        row["source"] = "database" if d["in_database"] else "reconstructed"
        row["attribution"] = {"status": d["status"], "modules": d["modules"]}
        if d["status"] == "unresolved":
            unresolved.append(rid)
        records.append(row)
    return {
        "provenance": "database",
        "attribution_provenance": "reconstructed",
        "description": "Concept and functional-slot records written by module installation. A record with source "
                       "'database' is read from the database; which module wrote it is reconstructed by replay. A "
                       "record with source 'reconstructed' is written by the replay but absent from the database.",
        "verification": "verified" if attr.data_verified else "failed",
        "problems": attr.data_problems,
        "records": records,
        "unresolved": unresolved,
    }
