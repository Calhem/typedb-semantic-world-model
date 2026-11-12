"""LABS-1.024 design probe 2: the shape of schema() text, and parse/query agreement. Usage: python -I this.py <repo>"""
import re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel  # noqa
from worldmodel.model import READ  # noqa
from worldmodel.profiles import PROFILES, _declared_labels  # noqa
DB = "wm-probe-schema2"
wm = WorldModel.create(DB, modules=CORE_MODULES, replace=True)
try:
    core_only = wm.driver.databases.get(DB).schema()
    for p in ("mechanical", "organisation", "laboratory"):
        wm.install_profile(p)
    text = wm.driver.databases.get(DB).schema()
    body = text[:text.index("fun ")] if "fun " in text else text
    stmts = [s.strip() for s in body.replace("define", "", 1).split(";") if s.strip()]
    print("statements:", len(stmts), "| first words:", Counter(s.split()[0] for s in stmts))
    print("annotations used:", sorted(Counter(re.findall(r"@[a-z]+(?:\([^)]*\))?", body)).items()))
    for label in ("schema-module", "particular", "sampling", "sample", "coverage-level", "event"):
        s = next((x for x in stmts if re.match(rf"(entity|relation|attribute) {label}\b", x)), None)
        print(f"--- {label}:\n  " + (s or "(none)").replace("\n", "\n  "))
    repo_funs = sorted(set(re.findall(r"^\s*fun\s+([a-z_]+)", "\n".join(f.read_text() for f in Path(sys.argv[1], "schema").rglob("*.tql")), re.M)))
    db_funs = sorted(set(re.findall(r"^\s*fun\s+([a-z_]+)", text, re.M)))
    print("functions in repository .tql files:", repo_funs, "| in the database:", db_funs)
    # declared-vs-inherited from text: does a type statement repeat inherited owns?
    sam = next(x for x in stmts if x.startswith("entity sample"))
    print("sample statement repeats inherited 'owns wm-id':", "owns wm-id" in sam)
    # profile attribution from the module files, checked against the database
    with wm.driver.transaction(DB, READ) as tx:
        db_types = {r.get("t").get_label() for k in ("entity", "relation", "attribute")
                    for r in tx.query(f"match {k} $t;").resolve().as_concept_rows()}
    core_types = _declared_labels(core_only)
    prof = {n: _declared_labels("\n".join(Path(f).read_text() for f in PROFILES[n].schema)) for n in ("mechanical", "organisation", "laboratory")}
    attributed = core_types.union(*prof.values())
    print("types:", len(db_types), "| core (from a core-only schema()):", len(core_types),
          "| per profile:", {k: len(v) for k, v in prof.items()},
          "| unattributed:", sorted(db_types - attributed), "| attributed but absent:", sorted(attributed - db_types),
          "| in two modules:", sorted(set.intersection(*[set(v) for v in prof.values()]) | (core_types & set().union(*prof.values()))))
    # profiles that only extend core types (plays/owns added to core types): visible?
    core_stmt = next(x for x in stmts if x.startswith("entity physical-object"))
    print("--- physical-object after profiles (core type extended by profiles):\n  " + core_stmt.replace("\n", "\n  "))
finally:
    wm.driver.databases.get(DB).delete()
