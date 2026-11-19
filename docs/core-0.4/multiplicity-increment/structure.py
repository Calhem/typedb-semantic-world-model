"""Structural equivalence of two databases with a checkout's code: schema facts (annotations included), module records,
module data (concepts, slots, event-role constraints with multiplicity), and the type and role lattice."""
import json, sys
sys.path.insert(0, sys.argv[1] + "/src")
from worldmodel import WorldModel, connect
from worldmodel.schema_export.parse import facts, parse_schema
from worldmodel.schema_export.introspect import read_answers, read_module_data
from worldmodel.model import READ
drv = connect()
def state(db):
    text = drv.databases.get(db).schema()
    with drv.transaction(db, READ) as tx:
        answers = read_answers(tx)
        data = read_module_data(tx, answers["kinds"])
    wm = WorldModel.open(db, driver=drv)
    return {"facts": facts(parse_schema(text)), "text": text, "modules": wm.modules(),
            "data": data, "constraints": wm.event_role_constraints(),
            "answers": {k: (sorted(map(str, v)) if isinstance(v, (set, frozenset)) else v) for k, v in answers.items()}}
a, b = state(sys.argv[2]), state(sys.argv[3])
out = {"schema_text_identical": a["text"] == b["text"],
       "schema_facts": {"a": len(a["facts"]), "b": len(b["facts"]),
                        "only_a": sorted(set(a["facts"]) - set(b["facts"])), "only_b": sorted(set(b["facts"]) - set(a["facts"])),
                        "differing": sorted(k for k in set(a["facts"]) & set(b["facts"]) if a["facts"][k] != b["facts"][k])},
       "modules_identical": a["modules"] == b["modules"], "modules": a["modules"],
       "module_data": {"a": len(a["data"]), "b": len(b["data"]), "only_a": sorted(map(str, a["data"] - b["data"])),
                       "only_b": sorted(map(str, b["data"] - a["data"]))},
       "event_role_constraints_identical": a["constraints"] == b["constraints"],
       "query_answers_identical": a["answers"] == b["answers"]}
print(json.dumps(out, indent=1, sort_keys=True, default=str))
