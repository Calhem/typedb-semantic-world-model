"""Checks that the illustrative TypeQL in docs/architecture/world-ontology-v0.1.md (section 8.2) is accepted by TypeDB
3.14.1, with the minimal surrounding definitions it needs. Throwaway database. Not a schema proposal."""
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from typedb.driver import TransactionType as T
from worldmodel import connect
from worldmodel import typeql as q

SCHEMA = """define
  attribute wm-id, value string; attribute unit, value string; attribute credence, value double;
  attribute magnitude @abstract; attribute magnitude-number sub magnitude, value double;
  attribute magnitude-text sub magnitude, value string; attribute magnitude-flag sub magnitude, value boolean;
  attribute time-point @abstract, value datetime-tz;
  attribute valid-from-earliest sub time-point; attribute valid-from-latest sub time-point;
  attribute valid-to-earliest sub time-point; attribute valid-to-latest sub time-point; attribute recorded-at sub time-point;
  entity physical-object, owns wm-id @key, plays located-at:located, plays has-quality:bearer;
  entity place, owns wm-id @key, plays located-at:place;
  entity agent, owns wm-id @key, plays attestation:attester;
  entity concept, owns wm-id @key, plays has-quality:quality, plays has-quality:value;
  entity world, owns wm-id @key, plays attestation:context;
  relation acceptance, relates accepted; relation evidence, relates supported; relation supersession, relates old, relates new;

  attribute proposition-key, value string;
  attribute stance, value string @values("asserts", "believes", "doubts", "hypothesises", "stipulates");
  attribute polarity, value boolean;
  attribute basis, value string @values("observation", "testimony", "inference", "stipulation");
  relation proposition @abstract, owns proposition-key @key, plays attestation:content;
  relation located-at sub proposition, relates located, relates place;
  relation has-quality sub proposition, relates bearer, relates quality, relates value,
    owns magnitude-number, owns magnitude-text, owns magnitude-flag, owns unit;
  relation attestation,
    relates attester @card(1..1), relates content @card(1..1), relates context @card(1..1),
    owns wm-id @key, owns stance, owns polarity, owns basis, owns credence,
    owns valid-from-earliest, owns valid-from-latest, owns valid-to-earliest, owns valid-to-latest,
    owns recorded-at,
    plays acceptance:accepted, plays evidence:supported, plays supersession:old, plays supersession:new;
"""
DATA = """insert $b isa physical-object, has wm-id "box-17"; $s isa place, has wm-id "shelf-3";
  $r isa agent, has wm-id "robot-1"; $w isa world, has wm-id "actual";
  $p isa located-at (located: $b, place: $s), has proposition-key "located-at|located=box-17|place=shelf-3";
  attestation (attester: $r, content: $p, context: $w), has wm-id "a1", has stance "asserts", has polarity true,
    has basis "observation", has valid-from-earliest 2026-11-09T10:03:00Z, has valid-from-latest 2026-11-09T10:03:00Z,
    has recorded-at 2030-01-01T00:00:00Z;"""
QUERY = """match
  $box isa physical-object, has wm-id "box-17";
  $p isa located-at (located: $box, place: $place);
  $a isa attestation (content: $p, context: $w, attester: $who), has recorded-at $rec, has polarity true;
  $w isa world, has wm-id "actual";
  $rec <= $tau;
  { not { $a has valid-from-latest $s0; }; } or { $a has valid-from-latest $s1; $s1 <= $t; };
  not { $a has valid-to-latest $e0; $e0 <= $t; };"""
DUPLICATE = """match $b isa physical-object, has wm-id "box-17"; $s isa place, has wm-id "shelf-3";
  insert $p isa located-at (located: $b, place: $s), has proposition-key "located-at|located=box-17|place=shelf-3";"""

d = connect(); db = "wm-arch-snippet"
if d.databases.contains(db): d.databases.get(db).delete()
d.databases.create(db)
try:
    with d.transaction(db, T.SCHEMA) as tx: tx.query(SCHEMA).resolve(); tx.commit()
    with d.transaction(db, T.WRITE) as tx: tx.query(DATA).resolve(); tx.commit()
    with d.transaction(db, T.READ) as tx:
        rows = q.rows(tx, QUERY, {"tau": datetime(2031, 1, 1, tzinfo=timezone.utc), "t": datetime(2026, 11, 9, 10, 15, tzinfo=timezone.utc)})
        print("schema accepted; query rows:", len(rows))
    try:
        with d.transaction(db, T.WRITE) as tx: tx.query(DUPLICATE).resolve(); tx.commit()
        print("duplicate proposition: ACCEPTED (unexpected)")
    except Exception as e:
        print("duplicate proposition rejected:", " ".join(str(e).split())[:120])
finally:
    d.databases.get(db).delete()
