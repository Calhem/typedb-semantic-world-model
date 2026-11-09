"""Architecture v0.1 probes (TypeDB 3.14.1): questions that decide the claim and quality representation.
Throwaway databases (wm-arch-*), deleted afterwards. Run: uv run python -I probes/architecture_probes.py"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import connect
from typedb.driver import TransactionType as T

d = connect()

def run(n, steps):
    db = f"wm-arch-{n}"
    if d.databases.contains(db): d.databases.get(db).delete()
    d.databases.create(db)
    out = []
    try:
        for kind, query in steps:
            try:
                with d.transaction(db, kind) as tx:
                    ans = tx.query(query).resolve()
                    if kind == T.READ:
                        out.append(("rows", len(list(ans.as_concept_rows()))))
                    else:
                        tx.commit(); out.append(("ok", None))
            except Exception as e:
                out.append(("rejected", " ".join(str(e).split())[:220])); break
    finally:
        d.databases.get(db).delete()
    return out

R = {}
R["A1 two instances of one relation type with identical role players"] = run("a", [
    (T.SCHEMA, "define entity thing, owns name; attribute name, value string; relation located-at, relates located, relates place; thing plays located-at:located, plays located-at:place;"),
    (T.WRITE, 'insert $a isa thing, has name "box"; $b isa thing, has name "shelf"; located-at (located: $a, place: $b); located-at (located: $a, place: $b);'),
    (T.READ, 'match $r isa located-at;')])
R["A2 abstract attribute with subtypes of different value types, owned polymorphically"] = run("b", [
    (T.SCHEMA, "define attribute magnitude @abstract; attribute magnitude-number sub magnitude, value double; attribute magnitude-text sub magnitude, value string; attribute magnitude-flag sub magnitude, value boolean; relation measurement, relates measured, owns magnitude; entity thing, plays measurement:measured;"),
    (T.WRITE, 'insert $t isa thing; measurement (measured: $t), has magnitude-number 3.5; measurement (measured: $t), has magnitude-text "red"; measurement (measured: $t), has magnitude-flag true;'),
    (T.READ, 'match $m isa measurement, has magnitude $v;')])
R["A3 relation (claim) as role player of another relation (attribution of a claim)"] = run("c", [
    (T.SCHEMA, "define entity agent; relation located-at, relates located, relates place, plays attribution:content; entity thing, plays located-at:located, plays located-at:place; relation attribution, relates holder, relates content; agent plays attribution:holder;"),
    (T.WRITE, 'insert $a isa thing; $b isa thing; $r isa located-at (located: $a, place: $b); $x isa agent; $y isa agent; attribution (holder: $x, content: $r); attribution (holder: $y, content: $r);'),
    (T.READ, 'match $r isa located-at; attribution (content: $r, holder: $h);')])
R["A4 an entity type playing a role defined on an abstract supertype relation, queried via the supertype"] = run("d", [
    (T.SCHEMA, "define relation claim @abstract; relation located-at sub claim, relates located, relates place; relation has-state sub claim, relates bearer, relates state; entity thing, plays located-at:located, plays located-at:place, plays has-state:bearer, plays has-state:state;"),
    (T.WRITE, 'insert $a isa thing; $b isa thing; located-at (located: $a, place: $b); has-state (bearer: $a, state: $b);'),
    (T.READ, 'match $c isa claim, links ($r: $x);')])
R["A2b same, but owning each concrete subtype; query through the abstract parent"] = run("e", [
    (T.SCHEMA, "define attribute magnitude @abstract; attribute magnitude-number sub magnitude, value double; attribute magnitude-text sub magnitude, value string; attribute magnitude-flag sub magnitude, value boolean; relation measurement, relates measured, owns magnitude-number, owns magnitude-text, owns magnitude-flag; entity thing, plays measurement:measured;"),
    (T.WRITE, 'insert $t isa thing; measurement (measured: $t), has magnitude-number 3.5; measurement (measured: $t), has magnitude-text "red"; measurement (measured: $t), has magnitude-flag true;'),
    (T.READ, 'match $m isa measurement, has magnitude $v;')])
print(json.dumps(R, indent=1))
