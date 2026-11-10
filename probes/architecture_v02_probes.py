"""World Ontology v0.2 feasibility probes (TypeDB 3.14.1). Throwaway databases (wm-v02-*), deleted afterwards.

    uv run python -I probes/architecture_v02_probes.py > probes/architecture_v02_probes.out.json

B1. Selective retrieval through the content/stance split: subject -> proposition -> attestation, filtered by world,
    transaction time and valid time, compared with Milestone 1's one-hop form (time on the fact relation), same data.
B2. Polymorphic content: attestations whose content is a proposition subtype or an event description, queried by
    either kind and through the abstract supertype.
B2 note: a role allows at most one player per relation instance unless @card says otherwise; the first run of B2,
    without @card(2..2) on co-reference:description, was rejected with CNT5.
B3. Interval-valued quantities: two measurements are compatible when their ranges overlap; the overlap test in TypeQL.
"""

import json
import random
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from typedb.driver import TransactionType as T  # noqa: E402

from worldmodel import connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402

d = connect()
START = datetime(2026, 11, 9, 8, 0, tzinfo=timezone.utc)
REC = datetime(2030, 1, 1, tzinfo=timezone.utc)


def fresh(name):
    if d.databases.contains(name):
        d.databases.get(name).delete()
    d.databases.create(name)
    return name


def schema(db, text):
    with d.transaction(db, T.SCHEMA) as tx:
        tx.query(text).resolve()
        tx.commit()


COMMON = """define
  attribute wm-id, value string; attribute proposition-key, value string;
  attribute time-point @abstract, value datetime-tz;
  attribute valid-from-earliest sub time-point; attribute valid-from-latest sub time-point;
  attribute valid-to-earliest sub time-point; attribute valid-to-latest sub time-point; attribute recorded-at sub time-point;
  attribute polarity, value boolean;
  entity object, owns wm-id @key; entity place, owns wm-id @key; entity agent, owns wm-id @key; entity world, owns wm-id @key;
"""


def bench_b1(objects=200, places=30, moves=1000, queries=200, seed=5):
    rnd = random.Random(seed)
    # Generate one history: for each object, a sequence of (place, start, end or None).
    hist = {f"o{i}": [(f"p{rnd.randrange(places)}", START, None)] for i in range(objects)}
    t = START
    for _ in range(moves):
        t += timedelta(seconds=rnd.randint(5, 60))
        o = f"o{rnd.randrange(objects)}"
        place, s, _ = hist[o][-1]
        hist[o][-1] = (place, s, t)
        hist[o].append((f"p{rnd.randrange(places)}", t, None))
    end = t
    results = {}
    for design in ("one-hop", "two-hop"):
        db = fresh(f"wm-v02-b1-{design}")
        try:
            extra = ("""relation located-at, relates located, relates place, owns wm-id @key,
                 owns valid-from-earliest, owns valid-from-latest, owns valid-to-earliest, owns valid-to-latest, owns recorded-at;
               object plays located-at:located; place plays located-at:place; world plays scoping:world;
               relation scoping, relates world, relates member; located-at plays scoping:member;""" if design == "one-hop" else
                     """relation proposition @abstract, owns proposition-key @key, plays attestation:content;
               relation located-at sub proposition, relates located, relates place;
               object plays located-at:located; place plays located-at:place;
               relation attestation, relates attester, relates content, relates context, owns wm-id @key, owns polarity,
                 owns valid-from-earliest, owns valid-from-latest, owns valid-to-earliest, owns valid-to-latest, owns recorded-at;
               agent plays attestation:attester; world plays attestation:context;""")
            schema(db, COMMON + extra)
            t0 = time.perf_counter()
            with d.transaction(db, T.WRITE) as tx:
                q.run(tx, 'insert $w isa world, has wm-id "actual"; $a isa agent, has wm-id "system";')
                for i in range(places):
                    q.run(tx, "insert $p isa place, has wm-id == $id;", {"id": f"p{i}"})
                for o in hist:
                    q.run(tx, "insert $o isa object, has wm-id == $id;", {"id": o})
                tx.commit()
            n, made = 0, set()
            with d.transaction(db, T.WRITE) as tx:
                for o, spans in hist.items():
                    for place, s, e in spans:
                        n += 1
                        p = {"oid": o, "plid": place, "s": s, "rec": REC, "id": f"c{n}", "key": f"located-at|{o}|{place}"}
                        end_attr = ""
                        if e is not None:
                            p["e"] = e
                            end_attr = ", has valid-to-earliest == $e, has valid-to-latest == $e"
                        if design == "one-hop":
                            q.run(tx, f"""match $o isa object, has wm-id == $oid; $pl isa place, has wm-id == $plid;
                                $w isa world, has wm-id "actual";
                                insert $c isa located-at (located: $o, place: $pl), has wm-id == $id,
                                has valid-from-earliest == $s, has valid-from-latest == $s, has recorded-at == $rec{end_attr};
                                scoping (world: $w, member: $c);""", p)
                        else:
                            if p["key"] not in made:
                                made.add(p["key"])
                                q.run(tx, """match $o isa object, has wm-id == $oid; $pl isa place, has wm-id == $plid;
                                    insert $prop isa located-at (located: $o, place: $pl), has proposition-key == $key;""",
                                      {"oid": o, "plid": place, "key": p["key"]})
                            q.run(tx, f"""match $prop isa located-at, has proposition-key == $key;
                                $w isa world, has wm-id "actual"; $a isa agent, has wm-id "system";
                                insert attestation (attester: $a, content: $prop, context: $w), has wm-id == $id,
                                has polarity true, has valid-from-earliest == $s, has valid-from-latest == $s,
                                has recorded-at == $rec{end_attr};""", {k: v for k, v in p.items() if k not in ("oid", "plid")})
                tx.commit()
            ingest = time.perf_counter() - t0
            one = """match $o isa object, has wm-id == $oid; $c isa located-at (located: $o, place: $pl);
                scoping (world: $w, member: $c); $w has wm-id "actual"; $c has recorded-at $rec; $rec <= $tau;
                $c has valid-from-latest $s; $s <= $t; not { $c has valid-to-earliest $e; $e <= $t; };
                $pl has wm-id $pid;"""
            two = """match $o isa object, has wm-id == $oid; $prop isa located-at (located: $o, place: $pl);
                $a isa attestation (content: $prop, context: $w), has polarity true; $w has wm-id "actual";
                $a has recorded-at $rec; $rec <= $tau;
                $a has valid-from-latest $s; $s <= $t; not { $a has valid-to-earliest $e; $e <= $t; };
                $pl has wm-id $pid;"""
            lat, answers = [], []
            qr = random.Random(99)
            asks = [(f"o{qr.randrange(objects)}", START + (end - START) * qr.random()) for _ in range(queries)]
            with d.transaction(db, T.READ) as tx:
                for o, when in asks:
                    s0 = time.perf_counter()
                    rows = q.rows(tx, one if design == "one-hop" else two,
                                  {"oid": o, "tau": REC + timedelta(days=1), "t": when})
                    lat.append(time.perf_counter() - s0)
                    answers.append(sorted(q.opt(r, "pid") for r in rows))
            with d.transaction(db, T.READ) as tx:
                props = len(q.rows(tx, "match $p isa located-at;"))
            results[design] = {"facts": n, "located_at_instances": props, "ingest_s": round(ingest, 1),
                               "ms_median": round(statistics.median(lat) * 1000, 2),
                               "ms_p95": round(sorted(lat)[int(0.95 * len(lat)) - 1] * 1000, 2), "answers": answers}
        finally:
            d.databases.get(db).delete()
    same = results["one-hop"].pop("answers") == results["two-hop"].pop("answers")
    return {"identical_answers": same, **results}


def probe_b2():
    db = fresh("wm-v02-b2")
    try:
        schema(db, COMMON + """
          relation proposition @abstract, owns proposition-key @key, plays attestation:content;
          relation located-at sub proposition, relates located, relates place;
          relation event, relates actor, relates patient, owns wm-id @key, plays attestation:content, plays co-reference:description;
          relation co-reference, relates description @card(2..2);
          object plays located-at:located, plays event:patient; place plays located-at:place; agent plays event:actor;
          relation attestation, relates attester, relates content, relates context, owns wm-id @key, owns polarity;
          agent plays attestation:attester; world plays attestation:context;""")
        with d.transaction(db, T.WRITE) as tx:
            q.run(tx, """insert $w isa world, has wm-id "actual"; $a isa agent, has wm-id "A"; $b isa agent, has wm-id "B";
              $bob isa agent, has wm-id "bob"; $carol isa agent, has wm-id "carol";
              $box isa object, has wm-id "box"; $s isa place, has wm-id "s3";
              $p isa located-at (located: $box, place: $s), has proposition-key "k1";
              $e1 isa event (actor: $bob, patient: $box), has wm-id "e1";
              $e2 isa event (actor: $carol, patient: $box), has wm-id "e2";
              attestation (attester: $a, content: $p, context: $w), has wm-id "a1", has polarity true;
              attestation (attester: $a, content: $e1, context: $w), has wm-id "a2", has polarity true;
              attestation (attester: $b, content: $e2, context: $w), has wm-id "a3", has polarity true;
              co-reference (description: $e1, description: $e2);""")
            tx.commit()
        out = {}
        with d.transaction(db, T.READ) as tx:
            out["any content"] = len(q.rows(tx, "match $x isa attestation (content: $c);"))
            out["proposition content"] = len(q.rows(tx, "match $x isa attestation (content: $c); $c isa proposition;"))
            out["event content"] = len(q.rows(tx, "match $x isa attestation (content: $c); $c isa event;"))
            out["actors of co-referring descriptions"] = sorted(q.opt(r, "aid") for r in q.rows(tx, """
              match $e isa event, has wm-id "e1"; co-reference (description: $e, description: $f);
              { $g is $e; } or { $g is $f; }; $g isa event (actor: $act); $act has wm-id $aid;"""))
        return out
    except Exception as e:  # noqa: BLE001
        return {"error": " ".join(str(e).split())[:300]}
    finally:
        d.databases.get(db).delete()


def probe_b3():
    db = fresh("wm-v02-b3")
    try:
        schema(db, COMMON + """
          attribute lower, value double; attribute upper, value double;
          relation measurement-range, relates bearer, owns wm-id @key, owns lower, owns upper;
          object plays measurement-range:bearer;""")
        with d.transaction(db, T.WRITE) as tx:
            q.run(tx, """insert $r isa object, has wm-id "rock";
              measurement-range (bearer: $r), has wm-id "m1", has lower 3.47, has upper 3.55;
              measurement-range (bearer: $r), has wm-id "m2", has lower 3.45, has upper 3.53;
              measurement-range (bearer: $r), has wm-id "m3", has lower 3.70, has upper 3.74;""")
            tx.commit()
        with d.transaction(db, T.READ) as tx:
            rows = q.rows(tx, """match $r isa object, has wm-id "rock";
              $a isa measurement-range (bearer: $r), has wm-id $ia, has lower $la, has upper $ua;
              $b isa measurement-range (bearer: $r), has wm-id $ib, has lower $lb, has upper $ub;
              $ia < $ib; $la <= $ub; $lb <= $ua;""")
            compatible = sorted(f"{q.opt(r, 'ia')}~{q.opt(r, 'ib')}" for r in rows)
        return {"compatible pairs (ranges overlap)": compatible, "expected": ["m1~m2"]}
    except Exception as e:  # noqa: BLE001
        return {"error": " ".join(str(e).split())[:300]}
    finally:
        d.databases.get(db).delete()


out = {"B2 polymorphic content": probe_b2(), "B3 range compatibility in TypeQL": probe_b3(), "B1 two-hop retrieval": bench_b1()}
out["leftover"] = [x.name for x in d.databases.all() if x.name.startswith("wm-v02-")]
print(json.dumps(out, indent=1))
