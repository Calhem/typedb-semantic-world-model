"""Pre-Stage E consolidation (LABS-1.045): evidence for the review of the open deferred issues, on merged `main`.

    uv run python -I probes/pre_e_consolidation.py [<checkout>]

Builds one throwaway database (wm-probe-cons-*, deleted afterwards) with the core and the three profiles, and prints,
without changing any code or semantics:
- DI-3: whether a functional slot keyed by `connected-to`'s two endpoints (one role played twice) would make two
  joint kinds of one pair DISPUTED, i.e. whether the existing slot mechanism could correct DI-3 (declared here in the
  probe database only, never in a profile);
- DI-4: whether an unseeded dependency kind is still accepted;
- same-as identity and event roles: two occurrence ids made the same occurrence; players named by a disputed same-as
  link; a same-as link accepted after the knowledge time; and a role whose players are the same thing under two names;
- DI-13: one description with two players of a role (refused by the database), a co-signed official act recorded as
  two accounts (each official in one), and a two-technician job recorded the same way.
Output: probes/pre_e_consolidation.out.txt.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, connect  # noqa: E402
from worldmodel import mechanical as mech, organisation as org  # noqa: E402


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        from datetime import timedelta
        self.now += timedelta(seconds=1)
        return self.now


def T(day):
    return datetime(2026, 11, day, 9, tzinfo=timezone.utc)


def accept_account(wm, world, event, holder="system"):
    for a in wm.account_attestations(world, event):
        wm.accept(a, holder=holder)


def official(view):
    r = view["roles"].get("official-act:official", {})
    cs = r.get("constraints", [])
    return {"players": r.get("players"), "judgement": [(c["applies"], c["judgement"], [p["names"] for p in c["players"]])
                                                        for c in cs]}


driver = connect()
DB = f"wm-probe-cons-{uuid.uuid4().hex[:8]}"
clock = Clock()
wm = WorldModel.create(DB, driver=driver, modules=CORE_MODULES, clock=clock)
try:
    for p in ("mechanical", "organisation", "laboratory"):
        wm.install_profile(p)
    w = wm.create_world("actual", id="w")
    for p in ("bea", "b-smith", "cal", "dan", "eve", "hr", "clerk", "office", "insp"):
        wm.add_entity("person", p, id=p)
    for i in ("housing", "cover", "pump", "motor"):
        wm.add_entity("physical-object", i, id=i)
    wm.add_entity("organisation", "depot", id="depot")
    wm.add_entity("social-role", "site-manager", id="site-manager")
    for o in ("o-1", "o-1-alias", "o-2", "o-3", "o-4", "o-cosign", "o-team"):
        wm.add_entity("occurrence", o, id=o)

    print("== DI-3: joint kinds of one connection")
    wm.accept(mech.connect(wm, w, "cover", "housing", "mechanical:bolted", attester="office"))
    wm.accept(wm.attest(w, "connected-to", {"endpoint": ["cover", "housing"], "joint-kind": "mechanical:pressed"},
                        until_superseded=True, attester="insp"))
    before = mech.connections(wm, w, "cover", T(12))
    print("  without a slot:", [(c["joint_kind"], c["status"]) for c in before])
    try:
        wm.declare_slot("connected-to", ["endpoint"], "joint-kind")
        after = mech.connections(wm, w, "cover", T(12))
        print("  with slot (endpoint -> joint-kind), probe database only:", [(c["joint_kind"], c["status"]) for c in after])
    except Exception as e:                                                      # noqa: BLE001
        print("  slot refused:", type(e).__name__, str(e)[:200])

    print("\n== DI-4: an unseeded dependency kind")
    wm.add_entity("category", "steel", id="steel")
    try:
        att = wm.depend(w, "pump", "motor", kind="steel")
        print("  depend(kind='steel') accepted:", bool(att))
    except Exception as e:                                                      # noqa: BLE001
        print("  refused:", type(e).__name__, str(e)[:200])

    print("\n== same-as identity and event roles")
    # 1. two occurrence ids, one account each, made the same occurrence by an accepted same-as link
    accept_account(wm, w, org.act_in_office(wm, w, "bea", "site-manager", "depot", T(5), occurrence="o-1",
                                            attester="hr", id="act-1-hr"))
    accept_account(wm, w, org.act_in_office(wm, w, "cal", "site-manager", "depot", T(5), occurrence="o-1-alias",
                                            attester="clerk", id="act-1-clerk"))
    print("  o-1 before same-as(o-1, o-1-alias):", official(wm.occurrence("w", "o-1")))
    wm.accept(wm.attest(w, "same-as", {"same": ["o-1", "o-1-alias"]}, until_superseded=True, attester="hr"))
    v = wm.occurrence("w", "o-1")
    print("  o-1 after:", official(v))
    print("    accounts (description, describes judgement, account):",
          [(a["description"], a["describes"], a["account"]) for a in v["accounts"]])
    print("    describes(act-1-clerk, o-1-alias):",
          wm.judgement("w", "describes", {"description": "act-1-clerk", "occurrence": "o-1-alias"}, T(5)).judgement.value)
    print("  o-1-alias (the other name):", official(wm.occurrence("w", "o-1-alias")))
    # 2. two names of one official linked by a same-as that is itself disputed (asserted, and denied by an accepted denial)
    accept_account(wm, w, org.act_in_office(wm, w, "bea", "site-manager", "depot", T(5), occurrence="o-2",
                                            attester="hr", id="act-2-hr"))
    accept_account(wm, w, org.act_in_office(wm, w, "b-smith", "site-manager", "depot", T(5), occurrence="o-2",
                                            attester="clerk", id="act-2-clerk"))
    print("  o-2 (bea / b-smith), no same-as:", official(wm.occurrence("w", "o-2")))
    wm.accept(wm.attest(w, "same-as", {"same": ["bea", "b-smith"]}, until_superseded=True, attester="hr"))
    known_before_denial = clock.now
    print("  o-2, same-as accepted:", official(wm.occurrence("w", "o-2")))
    wm.accept(wm.deny(w, "same-as", {"same": ["bea", "b-smith"]}, until_superseded=True, attester="clerk"))
    print("  o-2, same-as also denied (accepted denial):", official(wm.occurrence("w", "o-2")))
    print("    canonical judgement of same-as(bea, b-smith) now:",
          wm.judgement("w", "same-as", {"same": ["bea", "b-smith"]}, T(5)).judgement.value,
          "| identity merges them:", "b-smith" in wm.identity("w").members("bea"))
    print("  o-2, as known before the denial:", official(wm.occurrence("w", "o-2", as_of=known_before_denial)))
    # 3. an identity known to one perspective only
    print("  o-2 for the perspective 'hr' (accepts nothing itself):", official(wm.occurrence("w", "o-2", perspective="hr")))

    print("\n== DI-13: several players of one role")
    try:
        wm.account(w, {"actor": ["dan", "eve"], "patient": "pump"}, T(6), occurrence="o-team", id="ev-team-both")
        print("  one description with two actors: written")
    except Exception as e:                                                      # noqa: BLE001
        print("  one description with two actors: refused,", type(e).__name__, str(e).splitlines()[0][:160])
    for who in ("dan", "eve"):
        accept_account(wm, w, wm.account(w, {"actor": who, "patient": "pump"}, T(6), occurrence="o-team",
                                         attester="office", id=f"ev-team-{who}"))
    v = wm.occurrence("w", "o-team")
    print("  two-technician job as two accounts by one source: actor players", v["roles"]["event:actor"]["players"],
          "constraints", v["roles"]["event:actor"]["constraints"], "| accounts", len(v["accounts"]))
    for who in ("bea", "cal"):                 # a co-signed act: both officials sign, one source records it
        accept_account(wm, w, org.act_in_office(wm, w, who, "site-manager", "depot", T(7), occurrence="o-cosign",
                                                attester="hr", id=f"act-cosign-{who}"))
    print("  co-signed act as two accounts by one source:", official(wm.occurrence("w", "o-cosign")))
finally:
    driver.databases.get(DB).delete()
