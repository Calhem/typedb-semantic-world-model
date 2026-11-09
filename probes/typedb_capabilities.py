"""Phase 1 capability probes: what TypeDB 3.14.1 actually does on the points the architecture depends on.

Each probe runs a tiny schema or query in a disposable database (`wm-probe-<n>`), records whether TypeDB
accepted it, and deletes the database. Nothing here is the proposed ontology: the type names are
throwaway. Run against any TypeDB 3.14.1 server, for example through the explorer's API container:

    docker exec -i noodlelab-api python - < probes/typedb_capabilities.py

The printed JSON is copied into docs/phase-1/typedb-capability-assessment.md.
"""

import json
import os
import time

from typedb.driver import Credentials, DriverOptions, DriverTlsConfig, TransactionType, TypeDB

SCHEMA, WRITE, READ = TransactionType.SCHEMA, TransactionType.WRITE, TransactionType.READ
driver = TypeDB.driver(os.environ.get("TYPEDB_ADDRESS", "127.0.0.1:1729"),
                       Credentials("admin", "password"), DriverOptions(DriverTlsConfig.disabled()))

CORE = """define
attribute wm-id, value string;
attribute label, value string;
attribute observed-at, value datetime-tz;
attribute confidence, value double @range(0.0..1.0);
entity endurant @abstract, owns wm-id @key, owns label, plays participation:participant, plays part-of:part, plays part-of:whole;
entity physical-object sub endurant;
entity agent sub endurant;
relation participation @abstract, relates participant, owns wm-id @key;
relation part-of, relates part, relates whole;
entity observation, owns wm-id @key, owns observed-at, plays support:evidence;
relation support, relates evidence, relates supported, owns confidence;
"""


def run(tx, q):
    return tx.query(q).resolve()


def probe(n, name, steps, expect):
    """steps: list of (transaction type, query). Returns accepted / rejected with the first error."""
    db = f"wm-probe-{n}"
    if driver.databases.contains(db):
        driver.databases.get(db).delete()
    driver.databases.create(db)
    out = {"probe": n, "name": name, "expect": expect}
    try:
        for kind, q in steps:
            with driver.transaction(db, kind) as tx:
                ans = run(tx, q)
                if kind != READ:
                    tx.commit()
                else:
                    out["rows"] = len(list(ans.as_concept_rows()))
        out["result"] = "accepted"
    except Exception as e:  # noqa: BLE001 - we want the server's message
        out["result"] = "rejected"
        out["error"] = " ".join(str(e).split())[:400]
    finally:
        driver.databases.get(db).delete()
    out["as_expected"] = out["result"] == expect
    return out


results = [
    probe(1, "a profile defined in a second, separate define on top of the core", [
        (SCHEMA, CORE),
        (SCHEMA, """define entity package sub physical-object;
                   relation pickup sub participation, relates picker as participant, relates picked as participant;
                   entity agent plays pickup:picker; entity package plays pickup:picked;""")], "accepted"),
    probe(2, "a relation playing a role in another relation (evidence for a relation)", [
        (SCHEMA, CORE),
        (SCHEMA, "define relation part-of plays support:supported;"),
        (WRITE, """insert $a isa physical-object, has wm-id "a"; $b isa physical-object, has wm-id "b";
                   $r isa part-of (part: $a, whole: $b); $o isa observation, has wm-id "o1";
                   support (evidence: $o, supported: $r), has confidence 0.7;"""),
        (READ, "match $r isa part-of; support (supported: $r, evidence: $o);")], "accepted"),
    probe(3, "one instance with two unrelated types (multiple classification)", [
        (SCHEMA, CORE),
        (WRITE, 'insert $x isa physical-object, isa agent, has wm-id "x";')], "rejected"),
    probe(4, "two profiles defining the same attribute name with different value types (no namespaces)", [
        (SCHEMA, CORE),
        (SCHEMA, "define attribute mass, value double;"),
        (SCHEMA, "define attribute mass, value string;")], "rejected"),
    probe(5, "an attribute owning an attribute (metadata on a value)", [
        (SCHEMA, CORE),
        (SCHEMA, "define attribute reading, value double, owns confidence;")], "rejected"),
    probe(6, "a struct value type (e.g. a 3D point)", [
        (SCHEMA, "define struct point3: x value double, y value double, z value double;")], "accepted"),
    probe(13, "using a struct as an attribute's value and inserting one", [
        (SCHEMA, "define struct point3: x value double, y value double, z value double; "
                 "attribute position, value point3; entity thing, owns position;"),
        (WRITE, "insert $t isa thing, has position point3(x: 1.0, y: 2.0, z: 0.5);")], "rejected"),
    probe(7, "a recursive function (transitive part-of) defined by a profile", [
        (SCHEMA, CORE),
        (SCHEMA, """define fun parts_of($w: endurant) -> { endurant }:
                     match { part-of (whole: $w, part: $p); } or
                           { part-of (whole: $w, part: $m); let $p in parts_of($m); };
                     return { $p };"""),
        (WRITE, """insert $a isa physical-object, has wm-id "a"; $b isa physical-object, has wm-id "b";
                   $c isa physical-object, has wm-id "c";
                   part-of (part: $b, whole: $a); part-of (part: $c, whole: $b);"""),
        (READ, 'match $a isa physical-object, has wm-id "a"; let $p in parts_of($a);')], "accepted"),
    probe(8, "schema introspection: list a profile's types by query (for conformance checks)", [
        (SCHEMA, CORE),
        (READ, "match $t sub endurant;")], "accepted"),
    probe(9, "removing a profile's types again (undefine)", [
        (SCHEMA, CORE),
        (SCHEMA, "define entity package sub physical-object;"),
        (SCHEMA, "undefine package;")], "accepted"),
    probe(10, "a profile adding a role to a core type (the profile changes the core type)", [
        (SCHEMA, CORE),
        (SCHEMA, "define relation located-in, relates located, relates place; entity endurant plays located-in:located;")],
        "accepted"),
    probe(11, "a datetime-tz with sub-second precision and a duration value", [
        (SCHEMA, "define attribute t, value datetime-tz; attribute d, value duration; entity e, owns t, owns d;"),
        (WRITE, "insert $e isa e, has t 2026-11-09T12:00:00.123456789Z, has d PT0.05S;")], "accepted"),
]

# A rough ingestion figure for small semantic records (one observation + one support relation per record),
# batched 100 per transaction. Indicative only; GUPI's numbers are in its phase-4-performance.md.
db = "wm-probe-ingest"
if driver.databases.contains(db):
    driver.databases.get(db).delete()
driver.databases.create(db)
with driver.transaction(db, SCHEMA) as tx:
    run(tx, CORE); run(tx, "define relation part-of plays support:supported;"); tx.commit()
n, batch = 2000, 100
start = time.perf_counter()
for b in range(n // batch):
    with driver.transaction(db, WRITE) as tx:
        for i in range(batch):
            k = b * batch + i
            run(tx, f'insert $o isa observation, has wm-id "o{k}", has observed-at 2026-11-09T12:00:00Z; '
                    f'$x isa physical-object, has wm-id "x{k}"; $y isa physical-object, has wm-id "y{k}"; '
                    f'$r isa part-of (part: $x, whole: $y); support (evidence: $o, supported: $r), has confidence 0.9;')
        tx.commit()
elapsed = time.perf_counter() - start
lat = []
for k in range(50):
    t = time.perf_counter()
    with driver.transaction(db, READ) as tx:
        list(run(tx, f'match $x isa physical-object, has wm-id "x{k * 37}"; $r isa part-of (part: $x, whole: $y); '
                     f'support (supported: $r, evidence: $o), has confidence $c;').as_concept_rows())
    lat.append((time.perf_counter() - t) * 1000)
driver.databases.get(db).delete()
lat.sort()
results.append({"probe": 12, "name": "ingest 2000 records (5 concepts each), 100 per transaction, then 50 point lookups",
                "records_per_s": round(n / elapsed), "lookup_ms_median": round(lat[25], 1),
                "lookup_ms_p95": round(lat[47], 1)})
print(json.dumps(results, indent=1))
