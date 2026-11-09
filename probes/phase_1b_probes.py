"""Phase 1B probes: four specific uncertainties from Phase 1, each in a throwaway database (`wm-1b-<n>`) that is
deleted afterwards. Type names are throwaway, not the proposed ontology.

    docker exec -i noodlelab-api python - < probes/phase_1b_probes.py > probes/phase_1b_probes.out.json

A. Struct values: can a struct-typed attribute be inserted at all in 3.14.1, and with which literal syntax?
B. Re-typing: if a detector's label is used as the instance's type, can a later correction change the type
   without creating a new instance (which would break identity)?
C. Temporal reasoning in TypeQL: can "where was X at time t" over claims with optional, uncertain bounds be a
   TypeQL function, rather than Python (GUPI kept it in Python)?
D. Profile coupling: once data uses a role a profile added to a core type, can the profile be removed?
"""

import json
import os
import time

from typedb.driver import Credentials, DriverOptions, DriverTlsConfig, TransactionType, TypeDB

SCHEMA, WRITE, READ = TransactionType.SCHEMA, TransactionType.WRITE, TransactionType.READ
driver = TypeDB.driver(os.environ.get("TYPEDB_ADDRESS", "127.0.0.1:1729"),
                       Credentials("admin", "password"), DriverOptions(DriverTlsConfig.disabled()))


def attempt(db, kind, q):
    """Run one query; return ('accepted', rows or None) or ('rejected', message)."""
    try:
        with driver.transaction(db, kind) as tx:
            ans = tx.query(q).resolve()
            rows = None
            if kind == READ:
                rows = [r for r in ans.as_concept_rows()]
            else:
                tx.commit()
            return "accepted", rows
    except Exception as e:  # noqa: BLE001
        return "rejected", " ".join(str(e).split())[:300]


def fresh(name):
    if driver.databases.contains(name):
        driver.databases.get(name).delete()
    driver.databases.create(name)
    return name


out = []

# A. structs
db = fresh("wm-1b-a")
out.append({"probe": "A0 define struct-valued attribute", "result": attempt(db, SCHEMA,
    "define struct point3: x value double, y value double, z value double; "
    "attribute position, value point3; entity thing, owns position;")[0]})
for label, lit in [("A1 one-brace literal", "{x: 1.0, y: 2.0, z: 0.5}"),
                   ("A2 single-field literal", "{x: 1.0}"),
                   ("A3 constructor literal", "point3(x: 1.0, y: 2.0, z: 0.5)")]:
    res = attempt(db, WRITE, f"insert $t isa thing, has position {lit};")
    out.append({"probe": label, "result": res[0], "detail": res[1] if res[0] == "rejected" else None})
driver.databases.get(db).delete()

# B. re-typing an instance
db = fresh("wm-1b-b")
attempt(db, SCHEMA, "define attribute wm-id, value string; entity item @abstract, owns wm-id @key; "
                    "entity box sub item; entity package sub item;")
attempt(db, WRITE, 'insert $x isa box, has wm-id "obj-1";')
res = attempt(db, WRITE, 'match $x isa box, has wm-id "obj-1"; insert $x isa package;')
out.append({"probe": "B1 change an instance's type from box to package in place", "result": res[0],
            "detail": res[1] if res[0] == "rejected" else None})
res = attempt(db, READ, 'match $x isa! $t, has wm-id "obj-1";')
out.append({"probe": "B2 type of obj-1 afterwards", "result": res[0],
            "types": [str(r.get("t").get_label()) for r in res[1]] if res[0] == "accepted" else None})
driver.databases.get(db).delete()

# C. temporal query in TypeQL over claims with optional, uncertain bounds
db = fresh("wm-1b-c")
attempt(db, SCHEMA, """define
attribute wm-id, value string;
attribute valid-from-latest, value datetime-tz;   # the claim certainly holds from here
attribute valid-to-earliest, value datetime-tz;   # ... and certainly until here
attribute valid-to-latest, value datetime-tz;     # it has certainly ended by here
entity thing, owns wm-id @key, plays located-at:located, plays located-at:place;
relation located-at, relates located, relates place, owns wm-id @key,
  owns valid-from-latest, owns valid-to-earliest, owns valid-to-latest;
# TRUE at $t: started for sure by $t, and either known to last past $t or ... no end recorded is NOT enough.
fun certainly_at($x: thing, $t: datetime-tz) -> { thing }:
  match $c isa located-at (located: $x, place: $p), has valid-from-latest $s, has valid-to-earliest $e;
        $s <= $t; $t < $e;
  return { $p };
# FALSE at $t: the claim had certainly ended by $t.
fun certainly_not_at($x: thing, $t: datetime-tz) -> { thing }:
  match $c isa located-at (located: $x, place: $p), has valid-to-latest $l; $l <= $t;
  return { $p };
""")
attempt(db, WRITE, """insert
$box isa thing, has wm-id "box"; $s3 isa thing, has wm-id "shelf-3"; $dock isa thing, has wm-id "dock";
located-at (located: $box, place: $s3), has wm-id "c1", has valid-from-latest 2026-11-09T10:00:00Z,
  has valid-to-earliest 2026-11-09T10:06:00Z, has valid-to-latest 2026-11-09T10:09:00Z;
located-at (located: $box, place: $dock), has wm-id "c2", has valid-from-latest 2026-11-09T10:12:00Z;
""")
cases = {}
for t in ["10:03", "10:07", "10:10", "10:15"]:
    ts = f"2026-11-09T{t}:00Z"
    yes = attempt(db, READ, f'match $b isa thing, has wm-id "box"; let $p in certainly_at($b, {ts}); $p has wm-id $id;')
    no = attempt(db, READ, f'match $b isa thing, has wm-id "box"; let $p in certainly_not_at($b, {ts}); $p has wm-id $id;')
    cases[t] = {"TRUE at": sorted(r.get("id").get_value() for r in yes[1]) if yes[0] == "accepted" else yes[1],
                "FALSE at": sorted(r.get("id").get_value() for r in no[1]) if no[0] == "accepted" else no[1]}
out.append({"probe": "C1 where was the box, three-valued, in TypeQL", "cases": cases,
            "expected": {"10:03": "TRUE shelf-3", "10:07": "neither (end window)", "10:10": "FALSE shelf-3",
                         "10:15": "neither: dock claim has no certain end-start pair, so UNKNOWN, not TRUE"}})
driver.databases.get(db).delete()

# D. removing a profile once data uses the role it added to a core type
db = fresh("wm-1b-d")
attempt(db, SCHEMA, "define attribute wm-id, value string; entity endurant, owns wm-id @key;")
attempt(db, SCHEMA, "define relation stored-in, relates stored, relates store; entity endurant plays stored-in:stored, plays stored-in:store;")
attempt(db, WRITE, 'insert $a isa endurant, has wm-id "a"; $b isa endurant, has wm-id "b"; stored-in (stored: $a, store: $b);')
res = attempt(db, SCHEMA, "undefine plays stored-in:stored from endurant; plays stored-in:store from endurant; stored-in;")
out.append({"probe": "D1 remove the profile's role from the core type while data uses it", "result": res[0],
            "detail": res[1] if res[0] == "rejected" else None})
driver.databases.get(db).delete()

out.append({"leftover_probe_databases": [d.name for d in driver.databases.all() if d.name.startswith("wm-")]})
print(json.dumps(out, indent=1, default=str))
