"""DI-13 design evidence (LABS-1.046): what TypeDB 3.14.1 does when one event role is opened to several players.

    uv run python -I probes/pre_e_di13_cardinality.py [<checkout>]

Builds one throwaway database (wm-probe-card-*, deleted afterwards) with the core and the organisation profile, and,
with the library code unchanged, records:
- C1: one description naming two players of a role is refused (the default cardinality, @card(0..1));
- C2/C3: opening one role (event:actor) with `define ... @card(0..)` on a database that already holds data, and what
  that does to a profile's specialised role (official-act:official, `as actor`);
- C4: whether the specialised role has to be opened separately, and whether that works;
- C5: whether narrowing a role back is refused while data uses the wider cardinality (the migration cannot be undone
  silently);
- C6: how today's rule Q (increment D) reads one accepted account naming two officials: it counts two players
  from one account as a conflict, which is why a design needs a multiplicity rule and not only a schema change.
Output: probes/pre_e_di13_cardinality.out.txt.
"""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve() / "src"))
from typedb.driver import TransactionType  # noqa: E402
from worldmodel import CORE_MODULES, WorldModel, connect  # noqa: E402
from worldmodel import organisation as org  # noqa: E402


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


T5 = datetime(2026, 11, 5, 9, tzinfo=timezone.utc)
driver = connect()
DB = f"wm-probe-card-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(DB, driver=driver, modules=CORE_MODULES, clock=Clock())


def schema(label, typeql):
    try:
        with driver.transaction(DB, TransactionType.SCHEMA) as tx:
            tx.query(typeql).resolve()
            tx.commit()
        print(f"  {label}: accepted")
    except Exception as e:                                                      # noqa: BLE001
        print(f"  {label}: refused, {type(e).__name__}: {first(e)}")


def first(e):
    lines = [x.strip() for x in str(e).splitlines() if x.strip()]
    return " | ".join(lines[:2])[:220]


def write(label, fn):
    try:
        out = fn()
        print(f"  {label}: written ({out})")
        return out
    except Exception as e:                                                      # noqa: BLE001
        print(f"  {label}: refused, {type(e).__name__}: {first(e)}")


try:
    wm.install_profile("organisation")
    wm.create_world("actual", id="w")
    for p in ("bea", "cal", "dan", "eve", "hr"):
        wm.add_entity("person", p, id=p)
    wm.add_entity("physical-object", "pump", id="pump")
    wm.add_entity("organisation", "depot", id="depot")
    wm.add_entity("social-role", "site-manager", id="site-manager")
    wm.add_entity("occurrence", "o-cosign", id="o-cosign")
    write("existing data: an event with one actor", lambda: wm.describe_event({"actor": "dan", "patient": "pump"},
                                                                             id="ev-one"))

    print("== C1: the default cardinality")
    write("event with two actors", lambda: wm.describe_event({"actor": ["dan", "eve"], "patient": "pump"}, id="ev-two"))
    write("official-act with two officials", lambda: wm.describe_event(
        {"official": ["bea", "cal"], "office": "site-manager", "office-context": "depot"}, type="official-act",
        id="act-two"))

    print("\n== C2: open event:actor only (define on a database holding data)")
    schema("define relation event relates actor @card(0..)", "define relation event relates actor @card(0..);")
    write("event with two actors", lambda: wm.describe_event({"actor": ["dan", "eve"], "patient": "pump"}, id="ev-two"))
    print("  the existing one-actor event reads:", wm.content("ev-one")["roles"])
    print("  the two-actor event reads:", wm.content("ev-two")["roles"])

    print("\n== C3: a specialised role (official-act:official as actor) after C2")
    write("official-act with two officials", lambda: wm.describe_event(
        {"official": ["bea", "cal"], "office": "site-manager", "office-context": "depot"}, type="official-act",
        id="act-two"))

    print("\n== C4: open official-act:official itself")
    schema("define relation official-act relates official @card(0..)",
           "define relation official-act relates official @card(0..);")
    write("official-act with two officials", lambda: wm.describe_event(
        {"official": ["bea", "cal"], "office": "site-manager", "office-context": "depot"}, type="official-act",
        id="act-two"))

    print("\n== C5: narrowing back while data uses the wider cardinality")
    schema("redefine relation event relates actor @card(0..1)", "redefine relation event relates actor @card(0..1);")

    print("\n== C6: today's rule Q reading one accepted account that names two officials (a co-signed act)")
    if wm.content("act-two"):
        for a in wm.account_attestations("w", "act-two"):
            wm.accept(a)
        wm.accept(wm.attest("w", event="act-two", start=T5, end=T5, attester="hr"))
        wm.accept(wm.describe_occurrence("w", "act-two", "o-cosign", attester="hr"))
        role = wm.occurrence("w", "o-cosign")["roles"].get("official-act:official", {})
        print("  players:", role.get("players"))
        print("  constraints:", [(c["applies"], c["judgement"], [p["names"] for p in c["players"]])
                                 for c in role.get("constraints", [])])
        print("  (one account, one source, two officials: today DISPUTED, the same as two conflicting accounts)")
finally:
    driver.databases.get(DB).delete()
