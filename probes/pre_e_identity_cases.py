"""Identity design evidence (LABS-1.046, DI-12 / DI-15 / DI-16): how same-as identity behaves today, case by case.

    uv run python -I probes/pre_e_identity_cases.py [<checkout>]

Builds one throwaway database (wm-probe-ident-*, deleted afterwards) and, for each case of the identity design
(docs/core-0.4/pre-e-identity-design.md, section 4) prints, with the code unchanged:
- whether the perspective's identity (`wm.identity`) makes the two names one thing today, and whether the design would;
- the canonical judgement of the same-as content today (`wm.judgement`), which is itself taken through identity, and
  the same link judged by its stated names without identity (the design's building block).
Every line marked `changes` is a place the correction changes. Output: probes/pre_e_identity_cases.out.txt.
"""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, connect  # noqa: E402
from worldmodel.semantics import Identity  # noqa: E402
from worldmodel import organisation as org  # noqa: E402


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


def T(day):
    return datetime(2026, 11, day, 9, tzinfo=timezone.utc)


def legacy_interval(wm, aid, start, end):
    """Give an existing attestation an exact stated interval in storage, as same-as attestations written before
    LABS-1.048 can have one (the library no longer writes it)."""
    from worldmodel import typeql as q
    with wm._writing() as tx:
        q.run(tx, """match $a isa attestation, has wm-id == $id, has end-basis $eb; delete has $eb of $a;""",
              {"id": aid})
        q.run(tx, """match $a isa attestation, has wm-id == $id;
            insert $a has end-basis "stated", has valid-from-earliest == $s, has valid-from-latest == $s,
            has valid-to-earliest == $e, has valid-to-latest == $e;""", {"id": aid, "s": start, "e": end})


driver = connect()
DB = f"wm-probe-ident-{uuid.uuid4().hex[:8]}"
clock = Clock()
wm = WorldModel.create(DB, driver=driver, modules=CORE_MODULES, clock=clock)
rows = []


def same(x, y, world="w", **kw):
    return wm.attest(world, "same-as", {"same": [x, y]}, until_superseded=True, **kw)


def pair(world, x, y, t, as_of, perspective):
    """The same-as link judged by its stated names, without any identity (the design's building block, section 3.1)."""
    atts = wm._load(world, as_of, types=["same-as"], perspective=perspective)
    recs = wm._records(list(atts.values()), Identity([], perspective, as_of), t, perspective, as_of, world=world)
    for cls, rec in recs.items():
        if sorted(dict(cls[1]).get("same", ())) == sorted((x, y)):
            return rec
    return None


def label(rec):
    if rec is None:
        return "no record"
    return rec.judgement.value + (f" ({','.join(rec.reasons)})" if rec.reasons else "")


def check(case, x, y, expect, world="w", t=T(15), as_of=None, perspective="system"):
    merged = y in wm.identity(world, as_of=as_of, perspective=perspective).members(x)
    today = wm.judgement(world, "same-as", {"same": [x, y]}, t, as_of=as_of, perspective=perspective)
    flag = "" if merged == expect else "   <-- changes"
    rows.append((case, merged, expect))
    print(f"  {case:56} merged today {str(merged):5} design {str(expect):5}{flag}")
    print(f"  {'':56}   judgement today (through identity): {label(today):26} by stated names: "
          f"{label(pair(world, x, y, t, as_of, perspective))}")


try:
    wm.install_profile("organisation")
    wm.create_world("actual", id="w")
    names = [f"{p}{i}" for p in "abcdefghjkmnpqrsuvxyz" for i in (1, 2, 3)]
    for p in names + ["bea", "b-smith", "matcher", "clerk", "hr", "registry"]:
        wm.add_entity("person", p, id=p)
    for o in ("o-1", "o-1-alias"):
        wm.add_entity("occurrence", o, id=o)
    wm.add_entity("organisation", "depot", id="depot")
    wm.add_entity("social-role", "site-manager", id="site-manager")

    print("== Acceptance and polarity (actual world, system perspective)")
    wm.accept(same("a1", "a2", attester="matcher"))
    check("I1 accepted assertion", "a1", "a2", True)
    same("b1", "b2", attester="matcher")
    check("I2 unreviewed assertion (pending)", "b1", "b2", False)
    wm.accept(same("c1", "c2", attester="matcher"))
    wm.accept(wm.deny("w", "same-as", {"same": ["c1", "c2"]}, until_superseded=True, attester="clerk"))
    check("I3 accepted assertion + accepted denial (DI-16)", "c1", "c2", False)
    wm.accept(wm.deny("w", "same-as", {"same": ["d1", "d2"]}, until_superseded=True, attester="clerk"))
    check("I4 accepted denial only", "d1", "d2", False)
    wm.accept(same("e1", "e2", attester="matcher"), verdict="rejected")
    check("I5 rejected assertion", "e1", "e2", False)
    old = same("f1", "f2", attester="matcher")
    wm.accept(old)
    wm.accept(wm.attest("w", "same-as", {"same": ["f1", "f2"]}, polarity=False, until_superseded=True,
                        attester="matcher", supersedes=old))
    check("I6 assertion superseded by its source's denial", "f1", "f2", False)
    wm.accept(same("g1", "g2", attester="matcher"))
    wm.accept(same("g1", "g2", attester="registry"))
    wm.accept(wm.deny("w", "same-as", {"same": ["g1", "g2"]}, until_superseded=True, attester="clerk"),
              verdict="rejected")
    check("I7 two accepted assertions, a rejected denial", "g1", "g2", True)

    print("\n== Knowledge time (as_of)")
    h = same("h1", "h2", attester="matcher")
    before_accept = clock.now
    wm.accept(h)
    check("I8 as known before the acceptance", "h1", "h2", False, as_of=before_accept)
    check("I8 as known after the acceptance", "h1", "h2", True)
    wm.accept(same("j1", "j2", attester="matcher"))
    before_denial = clock.now
    wm.accept(wm.deny("w", "same-as", {"same": ["j1", "j2"]}, until_superseded=True, attester="clerk"))
    check("I9 as known before an accepted denial", "j1", "j2", True, as_of=before_denial)
    check("I9 as known after it (DI-16)", "j1", "j2", False)

    print("\n== Valid time (a same-as attested over an interval)")
    try:
        k = wm.attest("w", "same-as", {"same": ["k1", "k2"]}, start=T(10), end=T(20), attester="matcher")
    except ValueError:                  # refused since LABS-1.048 (ID-3): write the interval as older data has it
        k = wm.attest("w", "same-as", {"same": ["k1", "k2"]}, attester="matcher")
        legacy_interval(wm, k, T(10), T(20))
    wm.accept(k)
    for day, when in ((5, "before the interval"), (15, "inside it"), (25, "after its stated end")):
        check(f"I10 interval [10th, 20th), asked at the {day}th ({when})", "k1", "k2", True, t=T(day))
    print("    (identity has no valid time, today or under the design: same-as is judged timelessly, section 3.3)")

    print("\n== Perspective")
    same("m1", "m2", attester="hr")
    for p in ("hr", "system", "clerk"):
        check(f"I11 hr's own link, perspective {p}", "m1", "m2", p == "hr", perspective=p)

    print("\n== Hypothetical worlds")
    wm.accept(same("n1", "n2", attester="matcher"))
    wm.create_world("plan-split", kind="hypothetical", base="w", branch_at=T(1), id="plan-split")
    wm.deny("plan-split", "same-as", {"same": ["n1", "n2"]}, until_superseded=True)       # a stipulated denial
    check("I12 base link, plan stipulates the denial: in the plan", "n1", "n2", False, world="plan-split")
    check("I12 the same, in the base world", "n1", "n2", True)
    wm.create_world("plan-join", kind="hypothetical", base="w", branch_at=T(1), id="plan-join")
    same("p1", "p2", world="plan-join")                                                        # stipulated in the plan
    check("I13 link stipulated in a plan: in the plan", "p1", "p2", True, world="plan-join")
    check("I13 the same, in the base world", "p1", "p2", False)
    early = clock.now
    wm.accept(same("q1", "q2", attester="matcher"))
    wm.create_world("plan-early", kind="hypothetical", base="w", branch_at=T(1), knowledge_at=early, id="plan-early")
    check("I14 plan whose base knowledge ends before the link", "q1", "q2", False, world="plan-early")

    print("\n== Transitivity and conflicting evidence")
    wm.accept(same("r1", "r2", attester="matcher"))
    wm.accept(same("r2", "r3", attester="matcher"))
    check("I15 chain r1~r2~r3: r1 and r3 (no direct record)", "r1", "r3", True)
    wm.accept(same("s1", "s2", attester="matcher"))
    wm.accept(same("s2", "s3", attester="matcher"))
    wm.accept(wm.deny("w", "same-as", {"same": ["s1", "s3"]}, until_superseded=True, attester="clerk"))
    check("I16 chain s1~s2~s3, s1 != s3 denied: s1 and s3", "s1", "s3", False)
    check("I16 the same component: s1 and s2", "s1", "s2", False)
    wm.accept(same("u1", "u2", attester="matcher"))
    same("u2", "u3", attester="matcher")
    check("I17 chain u1~u2 accepted, u2~u3 pending: u1 and u3", "u1", "u3", False)
    wm.accept(same("v1", "v2", attester="matcher"))
    wm.accept(same("v2", "v3", attester="matcher"))
    wm.accept(wm.deny("w", "same-as", {"same": ["v2", "v3"]}, until_superseded=True, attester="clerk"))
    check("I18 chain v1~v2~v3 with v2~v3 disputed: v1 and v3", "v1", "v3", False)
    check("I18 the same: v1 and v2 (established link)", "v1", "v2", True)

    print("\n== Occurrence aliases (DI-15), event roles")
    for who, occ, src in (("bea", "o-1", "hr"), ("b-smith", "o-1-alias", "clerk")):
        for a in wm.account_attestations("w", org.act_in_office(wm, "w", who, "site-manager", "depot", T(5),
                                                                occurrence=occ, attester=src, id=f"act-{src}")):
            wm.accept(a)
    wm.accept(same("o-1", "o-1-alias", attester="hr"))
    wm.accept(same("bea", "b-smith", attester="hr"))
    for occ in ("o-1", "o-1-alias"):
        v = wm.occurrence("w", occ)
        role = v["roles"].get("official-act:official", {})
        print(f"  occurrence({occ}): descriptions {v['descriptions']}; accounts "
              f"{[(a['description'], a['describes']) for a in v['accounts']]}; official "
              f"{[(c['judgement'], [p['names'] for p in c['players']]) for c in role.get('constraints', [])]}")
    print("    (design: both names give one view: both accounts compared, one official under two names, established)")

    changed = [c for c, m, p in rows if m != p]
    print(f"\nTotals: {len(rows)} checks; identity differs from the design in {len(changed)}:")
    for c in changed:
        print("  -", c)
finally:
    driver.databases.get(DB).delete()
