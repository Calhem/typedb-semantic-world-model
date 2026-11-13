"""LABS-1.024 design probe: what TypeDB 3.14.1 exposes about its schema. Usage: python -I this.py <repo>"""
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel  # noqa
from worldmodel.model import READ, SCHEMA  # noqa
DB, DB2 = "wm-probe-schema", "wm-probe-schema-copy"
wm = WorldModel.create(DB, modules=CORE_MODULES, replace=True)
drv = wm.driver
def q(text, tx=None):
    own = tx is None
    tx = tx or drv.transaction(DB, READ)
    try:
        ans = tx.query(text).resolve()
        if ans.is_concept_rows():
            return list(ans.as_concept_rows())
        if ans.is_concept_documents():
            return list(ans.as_concept_documents())
        return ans
    except Exception as e:
        return "ERROR: " + " ".join(str(e).split())[:220]
    finally:
        if own: tx.close()
def lab(r, v):
    c = r.get(v); return c.get_label() if c is not None else None
try:
    for p in ("mechanical", "organisation", "laboratory"):
        wm.install_profile(p)
    db = drv.databases.get(DB)
    full, types_only = db.schema(), db.type_schema()
    print("1. schema(): chars", len(full), "| type_schema(): chars", len(types_only),
          "| functions in schema():", len(re.findall(r"^\s*fun ", full, re.M)), "in type_schema():",
          len(re.findall(r"^\s*fun ", types_only, re.M)))
    print("   comments kept:", "#" in full, "| deterministic:", full == db.schema())
    print("   first lines:\n     " + "\n     ".join(full.splitlines()[:6]))
    sample = [l for l in full.splitlines() if "sampling" in l][:4]
    print("   lines mentioning sampling:\n     " + "\n     ".join(sample))
    print("   one function:\n     " + "\n     ".join(full[full.index("fun "):].splitlines()[:6]))
    # round trip
    if drv.databases.contains(DB2): drv.databases.get(DB2).delete()
    drv.databases.create(DB2)
    with drv.transaction(DB2, SCHEMA) as tx:
        tx.query(full).resolve(); tx.commit()
    again = drv.databases.get(DB2).schema()
    print("2. round trip: define schema() into an empty database -> identical schema():", again == full)
    drv.databases.get(DB2).delete()
    # query introspection
    probes = {
      "entity types": "match entity $t;", "relation types": "match relation $t;", "attribute types": "match attribute $t;",
      "role types (relates)": "match relation $r; $r relates $role;",
      "direct supertypes (sub!)": "match $t sub! $s;",
      "owns (incl. inherited?)": "match $t owns $a;",
      "plays (incl. inherited?)": "match $t plays $r;",
      "role specialisation ($role sub! $p)": "match relation $t; $t relates $r; $r sub! $p;",
      "relates ... as": "match $t relates $r as $p;",
      "owns @key filter": "match $t owns $a @key;",
      "owns @card filter": "match $t owns $a @card(0..1);",
      "abstract filter": "match $t @abstract;",
      "entity abstract filter": "match entity $t @abstract;",
      "value type filter": "match attribute $a value string;",
      "value type binding": "match attribute $a; $a value $v;",
      "label binding": "match $t label sample;",
      "fetch labels": 'match entity $t; fetch { "t": $t };',
      "function listing": "match fun $f;",
    }
    with drv.transaction(DB, READ) as tx:
        for name, text in probes.items():
            r = q(text, tx)
            if isinstance(r, str):
                print(f"3. {name}: {r}")
            elif r and hasattr(r[0], "get"):
                try:
                    vars_ = list(r[0].column_names())
                except Exception:
                    vars_ = []
                print(f"3. {name}: {len(r)} rows; e.g. {[(v, lab(r[0], v)) for v in vars_]}")
            else:
                print(f"3. {name}: {len(r)} answers; e.g. {r[:1]}")
        own = {(lab(r, "t"), lab(r, "a")) for r in q("match $t owns $a;", tx)}
        direct_owns_particular = ("particular", "wm-id") in own; inherited = ("sample", "wm-id") in own
        print("4. owns includes inherited: particular owns wm-id:", direct_owns_particular, "| sample owns wm-id:", inherited)
        plays = {(lab(r, "t"), lab(r, "r")) for r in q("match $t plays $r;", tx)}
        print("   plays includes inherited: sample plays sampling:sampled:", ("sample", "sampling:sampled") in plays)
        rel = {(lab(r, "t"), lab(r, "r")) for r in q("match relation $t; $t relates $r;", tx)}
        print("   relates includes inherited roles: sampling relates event:actor:", ("sampling", "event:actor") in rel,
              "| sampling:sampler:", ("sampling", "sampling:sampler") in rel)
        try:
            ow = q("match $t owns! $a;", tx)
            print("   owns! (declared only):", "ERROR" if isinstance(ow, str) else f"{len(ow)} rows", ow if isinstance(ow, str) else "")
        except Exception as e:
            print("   owns!:", e)
        n = {k: len(q(f"match {k} $t;", tx)) for k in ("entity", "relation", "attribute")}
        print("5. counts:", n, "| modules:", wm.modules())
    t = time.perf_counter(); db.schema(); print(f"6. schema() time: {(time.perf_counter()-t)*1000:.0f} ms")
finally:
    drv.databases.get(DB).delete()
