"""LABS-1.002 Stage A0 probes (TypeDB 3.14.1): questions the A0 implementation depends on. Throwaway databases
(wm-a0-*), deleted afterwards.

    uv run python -I probes/core04_a0_probes.py > probes/core04_a0_probes.out.json

M1-M4 (A0.1 migration): can `proposition owns wm-id @key` be added to a database whose propositions have no wm-id?
If not, does "own without key, write ids, then add @key" work, and in which transaction kinds?
R1-R3 (A0.2 lattice): how to read a type's supertypes and a specialised role's parent role from the schema by query.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from typedb.driver import TransactionType as T  # noqa: E402

from worldmodel import connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402

d = connect()
BASE = """define attribute wm-id, value string; attribute proposition-key, value string;
entity thing, owns wm-id @key, plays located-at:located, plays located-at:place;
relation proposition @abstract, owns proposition-key @key;
relation located-at sub proposition, relates located, relates place;
relation event, relates actor, relates patient, owns wm-id @key;
thing plays event:actor, plays event:patient;"""
PROFILE = """define relation pickup sub event, relates picker as actor, relates picked as patient;
entity person sub thing, plays pickup:picker; thing plays pickup:picked;
relation docked-at sub located-at;"""


def fresh(name, *schemas):
    if d.databases.contains(name):
        d.databases.get(name).delete()
    d.databases.create(name)
    for s in schemas:
        with d.transaction(name, T.SCHEMA) as tx:
            tx.query(s).resolve()
            tx.commit()


def step(db, kind, query):
    try:
        with d.transaction(db, kind) as tx:
            ans = tx.query(query).resolve()
            if kind == T.READ:
                return [r for r in ans.as_concept_rows()]
            tx.commit()
        return "accepted"
    except Exception as e:  # noqa: BLE001
        return "rejected: " + " ".join(str(e).split())[:200]


out = {}
db = "wm-a0-m"
fresh(db, BASE)
step(db, T.WRITE, 'insert $a isa thing, has wm-id "a"; $b isa thing, has wm-id "b"; '
                  'located-at (located: $a, place: $b), has proposition-key "k1";')
out["M1 add `owns wm-id @key` to propositions that exist without one"] = step(db, T.SCHEMA, "define proposition owns wm-id @key;")
out["M2 add `owns wm-id` without @key"] = step(db, T.SCHEMA, "define proposition owns wm-id;")
out["M3 write ids for existing propositions (write transaction)"] = step(
    db, T.WRITE, 'match $p isa proposition, has proposition-key "k1"; insert $p has wm-id "p:1";')
out["M4 then add @key to the ownership"] = step(db, T.SCHEMA, "define proposition owns wm-id @key;")
out["M4b a new proposition without wm-id is now rejected"] = step(
    db, T.WRITE, 'match $a isa thing, has wm-id "a"; $b isa thing, has wm-id "b"; '
                 'insert located-at (located: $b, place: $a), has proposition-key "k2";')
d.databases.get(db).delete()

db = "wm-a0-r"
fresh(db, BASE, PROFILE)
rows = step(db, T.READ, "match $t sub proposition; $t label $l;") if False else None
for label, query, show in (
    ("R1 supertypes of a subtype (`$t sub $s`, with `label`)",
     "match $t label docked-at; $t sub $s;", lambda r: r.get("s").get_label()),
    ("R1b supertypes of an entity subtype", "match $t label person; $t sub $s;", lambda r: r.get("s").get_label()),
    ("R2 roles of a relation type (`relates`)", "match $t label pickup; $t relates $r;", lambda r: r.get("r").get_label()),
    ("R3 parent role of a specialised role (`$r sub $p`)", "match $t label pickup; $t relates $r; $r sub $p;",
     lambda r: f'{r.get("r").get_label()} -> {r.get("p").get_label()}'),
    ("R3b all relation types and their direct roles, in one query", "match relation $t; $t relates $r;",
     lambda r: f'{r.get("t").get_label()}: {r.get("r").get_label()}'),
):
    res = step(db, T.READ, query)
    out[label] = sorted({show(r) for r in res}) if isinstance(res, list) else res
d.databases.get(db).delete()
out["leftover"] = [x.name for x in d.databases.all() if x.name.startswith("wm-a0-")]
print(json.dumps(out, indent=1))
