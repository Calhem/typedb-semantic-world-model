"""Contextually established identity (LABS-1.048: DI-12, DI-15, DI-16 option (a); decisions ID-1 to ID-9 of
docs/core-0.4/pre-e-identity-design.md, with the ID-5 wording of pre-e-decision-gate.md section 1.3).

Permanent tests, on both query paths (WM_SELECTIVE), for:
- established equivalence, and links that are disputed, denied, pending, unknown or superseded (ID-1, ID-2);
- knowledge time, perspective and valid time (ID-3, ID-7), including a same-as interval written by older code;
- hypothetical worlds and their descendants (ID-6);
- transitivity, cycles and components in conflict (ID-4, ID-5), order independence, both paths agreeing;
- one identity for every reader: alias views of an occurrence (DI-15, ID-9), closures and listings (DI-12, ID-8);
- the DI-16 reproduction (probes/pre_e_di16_repro.py) and provenance of the links identity rests on.
"""

import os
import random
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel, organisation as org
from worldmodel import typeql as q
from worldmodel.semantics import AttestationRecord, Identity

pytestmark = pytest.mark.own_profiles


def T(day, h=9):
    return datetime(2026, 11, day, h, tzinfo=timezone.utc)


def legacy_interval(wm, aid, start, end):
    """Give an attestation an exact stated interval in storage, as a same-as written before LABS-1.048 may have."""
    with wm._writing() as tx:
        q.run(tx, "match $a isa attestation, has wm-id == $id, has end-basis $eb; delete has $eb of $a;", {"id": aid})
        q.run(tx, """match $a isa attestation, has wm-id == $id;
            insert $a has end-basis "stated", has valid-from-earliest == $s, has valid-from-latest == $s,
            has valid-to-earliest == $e, has valid-to-latest == $e;""", {"id": aid, "s": start, "e": end})


@pytest.fixture(scope="module")
def ref(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    wm.selective = os.environ.get("WM_SELECTIVE", "1") != "0"
    ids = {}
    try:
        wm.install_profile("organisation")
        wm.create_world("actual", id="w")
        names = [f"{p}{i}" for p in "abcdefghjkmnpqrsuvxyz" for i in (1, 2, 3)]
        for p in names + ["bea", "b-smith", "dan", "eve", "matcher", "clerk", "hr", "registry", "auditor"]:
            wm.add_entity("person", p, id=p)
        for i in ("gearbox", "bracket", "b-alias", "bolt", "pump", "pump-alias", "seal", "motor"):
            wm.add_entity("physical-object", i, id=i)
        for o in ("o-1", "o-1-alias", "o-2", "o-4", "o-4-alias"):
            wm.add_entity("occurrence", o, id=o)
        wm.add_entity("organisation", "depot", id="depot")
        wm.add_entity("social-role", "site-manager", id="site-manager")

        def same(x, y, world="w", **kw):
            return wm.attest(world, "same-as", {"same": [x, y]}, until_superseded=True, **kw)

        def deny(x, y, world="w", **kw):
            return wm.deny(world, "same-as", {"same": [x, y]}, until_superseded=True, **kw)

        def act(occ, official, src):
            e = org.act_in_office(wm, "w", official, "site-manager", "depot", T(5), occurrence=occ, attester=src,
                                  id=f"act-{occ}-{src}")
            for a in wm.account_attestations("w", e):
                wm.accept(a)
            return e

        ids["link_a"] = same("a1", "a2", attester="matcher")
        wm.accept(ids["link_a"])
        same("b1", "b2", attester="matcher")                                               # pending
        wm.accept(same("c1", "c2", attester="matcher"))                                    # disputed
        wm.accept(deny("c1", "c2", attester="clerk"))
        wm.accept(deny("d1", "d2", attester="clerk"))                                      # denied only
        wm.accept(same("e1", "e2", attester="matcher"), verdict="rejected")                # rejected
        old = same("f1", "f2", attester="matcher")                                         # superseded by a denial
        wm.accept(old)
        wm.accept(wm.attest("w", "same-as", {"same": ["f1", "f2"]}, polarity=False, until_superseded=True,
                            attester="matcher", supersedes=old))
        wm.accept(same("g1", "g2", attester="matcher"))                                    # rejected denial
        wm.accept(same("g1", "g2", attester="registry"))
        wm.accept(deny("g1", "g2", attester="clerk"), verdict="rejected")
        h = same("h1", "h2", attester="matcher")                                           # knowledge time
        ids["before_accept"] = wm.clock.now
        wm.accept(h)
        wm.accept(same("j1", "j2", attester="matcher"))
        ids["before_denial"] = wm.clock.now
        wm.accept(deny("j1", "j2", attester="clerk"))
        k = wm.attest("w", "same-as", {"same": ["k1", "k2"]}, attester="matcher")         # legacy interval
        legacy_interval(wm, k, T(10), T(20))
        wm.accept(k)
        same("m1", "m2", attester="hr")                                                    # perspective
        same("m2", "m3", attester="hr")
        deny("m2", "m3", attester="clerk")
        for a in wm._load("w", types=["same-as"], subjects=["m3"]).values():               # auditor: denial only
            if not a.polarity:
                wm.accept(a.id, holder="auditor")
        wm.accept(same("n1", "n2", attester="matcher"))                                    # worlds
        wm.create_world("plan-split", kind="hypothetical", base="w", branch_at=T(1), id="plan-split")
        deny("n1", "n2", world="plan-split")
        wm.create_world("plan-split-child", kind="hypothetical", base="plan-split", branch_at=T(1),
                        id="plan-split-child")
        wm.create_world("plan-join", kind="hypothetical", base="w", branch_at=T(1), id="plan-join")
        same("p1", "p2", world="plan-join")
        wm.accept(same("q1", "q2", attester="matcher"))                                    # part of a chain
        ids["early"] = wm.clock.now
        wm.accept(same("q2", "q3", attester="matcher"))
        wm.accept(deny("q1", "q3", attester="clerk"))
        wm.create_world("plan-early", kind="hypothetical", base="w", branch_at=T(1), knowledge_at=ids["early"],
                        id="plan-early")
        wm.accept(same("r1", "r2", attester="matcher"))                                    # chain
        wm.accept(same("r2", "r3", attester="matcher"))
        wm.accept(same("s1", "s2", attester="matcher"))                                    # conflict (I16)
        wm.accept(same("s2", "s3", attester="matcher"))
        wm.accept(deny("s1", "s3", attester="clerk"))
        wm.accept(same("u1", "u2", attester="matcher"))                                    # pending breaks a chain
        same("u2", "u3", attester="matcher")
        wm.accept(same("v1", "v2", attester="matcher"))                                    # I18
        wm.accept(same("v2", "v3", attester="matcher"))
        wm.accept(deny("v2", "v3", attester="clerk"))
        for x, y in (("x1", "x2"), ("x2", "x3"), ("x3", "x1")):                            # a cycle
            wm.accept(same(x, y, attester="matcher"))
        for x, y in (("y1", "y2"), ("y2", "y3"), ("y3", "y1")):                            # a cycle, one disputed
            wm.accept(same(x, y, attester="matcher"))
        wm.accept(deny("y3", "y1", attester="clerk"))
        # DI-15: one occurrence under two names; officials under two names, merged (bea, b-smith in hr's view) ...
        wm.accept(same("o-1", "o-1-alias", attester="registry"))
        act("o-1", "bea", "hr")
        act("o-1-alias", "b-smith", "clerk")
        ids["bea_link"] = same("bea", "b-smith", attester="hr")
        wm.accept(ids["bea_link"])
        # ... and not merged (dan, eve: no link): DISPUTED from both names
        wm.accept(same("o-4", "o-4-alias", attester="registry"))
        act("o-4", "dan", "hr")
        act("o-4-alias", "eve", "clerk")
        # DI-12: closures through an alias, and an alias link that is disputed
        wm.accept(same("bracket", "b-alias", attester="registry"))
        wm.attest("w", "part-of", {"part": "bracket", "whole": "gearbox"}, start=T(1), until_superseded=True)
        wm.attest("w", "part-of", {"part": "bolt", "whole": "b-alias"}, start=T(1), until_superseded=True)
        wm.accept(same("pump", "pump-alias", attester="registry"))
        wm.accept(deny("pump", "pump-alias", attester="clerk"))
        wm.attest("w", "part-of", {"part": "pump", "whole": "motor"}, start=T(1), until_superseded=True)
        wm.attest("w", "part-of", {"part": "seal", "whole": "pump-alias"}, start=T(1), until_superseded=True)
        wm.depend("w", "gearbox", "b-alias", start=T(1))
        wm.depend("w", "bracket", "seal", start=T(1))                                    # stated on the other name
        yield wm, ids
    finally:
        driver.databases.get(name).delete()


def merged(wm, x, y, **kw):
    return y in wm.identity(kw.pop("world", "w"), **kw).members(x)


# ---- ID-1, ID-2: only an established link merges ---------------------------------------------------------------
def test_established_links_merge_and_report_their_support(ref):
    wm, ids = ref
    assert merged(wm, "a1", "a2") and merged(wm, "g1", "g2")          # a rejected denial does not count
    ident = wm.identity("w")
    link = next(x for x in ident.links if x["same"] == ["a1", "a2"])
    assert link == {"same": ["a1", "a2"], "judgement": "established", "support": [ids["link_a"]], "depth": 0,
                    "merges": True}


@pytest.mark.parametrize("x, y, why", [("b1", "b2", "pending"), ("c1", "c2", "disputed (DI-16)"),
                                       ("d1", "d2", "denied"), ("e1", "e2", "rejected"),
                                       ("f1", "f2", "superseded by its source's denial")])
def test_links_not_established_join_nothing(ref, x, y, why):
    wm, _ = ref
    assert not merged(wm, x, y), why
    assert wm.identity("w").members(x) == [x]


def test_pending_links_are_still_proposed(ref):
    wm, _ = ref
    assert any((x, y) == ("b1", "b2") for _, x, y in wm.identity("w").proposed)


# ---- ID-7: knowledge time and perspective; ID-3: valid time ---------------------------------------------------------
def test_knowledge_time_before_and_after(ref):
    wm, ids = ref
    assert not merged(wm, "h1", "h2", as_of=ids["before_accept"]) and merged(wm, "h1", "h2")
    assert merged(wm, "j1", "j2", as_of=ids["before_denial"])          # earlier views stay reproducible
    assert not merged(wm, "j1", "j2")                                  # separate from the denial's recording on
    before = wm.judgement("w", "same-as", {"same": ["j1", "j2"]}, T(5), as_of=ids["before_denial"])
    assert before.judgement.value == "established"
    assert wm.judgement("w", "same-as", {"same": ["j1", "j2"]}, T(5)).judgement.value == "disputed"


def test_identity_is_timeless(ref):
    wm, _ = ref
    for day in (5, 15, 25):                                            # before, inside and after the old interval
        assert merged(wm, "k1", "k2")
        assert wm.judgement("w", "same-as", {"same": ["k1", "k2"]}, T(day)).judgement.value == "established"


@pytest.mark.parametrize("kw", [{"start": T(10)}, {"end": T(20)}, {"start": T(10), "end": T(20)}])
def test_same_as_with_an_interval_is_refused(ref, kw):
    wm, _ = ref
    with pytest.raises(ValueError, match="identity is timeless"):
        wm.attest("w", "same-as", {"same": ["z1", "z2"]}, **kw)
    assert wm.identity("w").members("z1") == ["z1"]


def test_perspectives(ref):
    wm, _ = ref
    assert merged(wm, "m1", "m2", perspective="hr")                    # hr's own links
    assert not merged(wm, "m1", "m2") and not merged(wm, "m1", "m2", perspective="clerk")
    # hr's own m2~m3 against clerk's unreviewed denial: established for hr
    assert merged(wm, "m1", "m3", perspective="hr")
    # the auditor accepted the denial, not the assertion: denied, so separate
    assert not merged(wm, "m2", "m3", perspective="auditor")
    rec = wm.judgement("w", "same-as", {"same": ["m2", "m3"]}, T(5), perspective="auditor")
    assert rec.judgement.value == "not holding"


# ---- ID-6: worlds ---------------------------------------------------------------------------------------------------
def test_hypothetical_worlds(ref):
    wm, _ = ref
    assert merged(wm, "n1", "n2")                                       # the base keeps its link
    assert not merged(wm, "n1", "n2", world="plan-split")              # the plan's stipulated denial decides
    assert not merged(wm, "n1", "n2", world="plan-split-child")        # and its descendants
    assert merged(wm, "p1", "p2", world="plan-join") and not merged(wm, "p1", "p2")
    assert not any(x["same"] == ["n1", "n2"] for x in wm.identity("plan-split-child").links)


def test_a_plan_inheriting_only_part_of_a_chain(ref):
    wm, _ = ref
    assert wm.identity("w").members("q1") == ["q1"]                     # the base: component in conflict
    assert wm.identity("plan-early").members("q1") == ["q1", "q2"]      # the plan knows only q1~q2
    link = next(x for x in wm.identity("plan-early").links if x["same"] == ["q1", "q2"])
    assert link["depth"] == 1                                           # inherited from the base world


# ---- ID-4, ID-5: transitivity, cycles, conflicts -------------------------------------------------------------------
def test_transitive_chain_and_cycle(ref):
    wm, _ = ref
    assert wm.identity("w").members("r1") == ["r1", "r2", "r3"]
    assert wm.identity("w").members("x2") == ["x1", "x2", "x3"]
    # ID-1: a link is judged by its stated names: the chain gives r1~r3 no record of its own (F-1)
    rec = wm.judgement("w", "same-as", {"same": ["r1", "r3"]}, T(5))
    assert (rec.judgement.value, rec.reasons) == ("unknown", ("no_evidence",))
    assert not merged(wm, "u1", "u3") and merged(wm, "u1", "u2")       # a pending link breaks the chain


@pytest.mark.parametrize("names, against", [(["s1", "s2", "s3"], (["s1", "s3"], "denied")),
                                            (["y1", "y2", "y3"], (["y1", "y3"], "disputed"))])
def test_component_in_conflict_is_not_merged_and_is_reported(ref, names, against):
    wm, _ = ref
    ident = wm.identity("w")
    for x in names:
        assert ident.members(x) == [x]
    conflict = next(c for c in ident.conflicts if c["names"] == names)
    assert [(c["same"], c["judgement"]) for c in conflict["against"]] == [against]
    assert all(link["judgement"] == "established" and link["support"] for link in conflict["links"])
    assert ident.report(names[0])["conflict"] == conflict
    assert all(not link["merges"] for link in ident.links if set(link["same"]) <= set(names))


def test_disputed_neighbour_does_not_split_an_established_link(ref):
    wm, _ = ref
    assert wm.identity("w").members("v1") == ["v1", "v2"]               # v2~v3 disputed: v3 stays apart
    assert wm.judgement("w", "same-as", {"same": ["v1", "v2"]}, T(5)).judgement.value == "established"


def test_selective_identity_agrees_with_the_full_load(ref):
    wm, _ = ref
    full = wm.identity("w")
    for x in ("s1", "s3", "y2", "r3", "v3", "q3", "a1", "c2", "u3"):
        assert wm.identity("w", ids=[x]).members(x) == full.members(x), x


def _rec(i, x, y, polarity=True, attester="system", depth=0):
    return AttestationRecord(id=i, content=f"k-{x}-{y}", ctype="same-as", roles={"same": sorted((x, y))}, params={},
                             attester=attester, world="w", stance="asserts", polarity=polarity, basis="testimony",
                             start=None, end=None, end_basis="until-superseded",
                             recorded_at=datetime(2030, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=int(i[1:])),
                             depth=depth)


def test_conflict_detection_is_order_independent():
    recs = [_rec("a1", "s1", "s2"), _rec("a2", "s2", "s3"), _rec("a3", "s1", "s3", polarity=False),
            _rec("a4", "t1", "t2"), _rec("a5", "t2", "t3"), _rec("a6", "t3", "t4"), _rec("a7", "t9", "t1")]
    first = Identity(recs, "system", None)
    rng = random.Random(7)
    for _ in range(25):
        shuffled = recs[:]
        rng.shuffle(shuffled)
        ident = Identity(shuffled, "system", None)
        assert ident.conflicts == first.conflicts and ident.links == first.links
        chain = ["t1", "t2", "t3", "t4", "t9"]
        assert [ident.members(x) for x in ("s1", "s3", "t1", "t4")] == [["s1"], ["s3"], chain, chain]
        assert ident.canonical("t4") == "t1"


def test_the_nearest_world_decides_a_link():
    base, plan_denial = _rec("a1", "n1", "n2", depth=1), _rec("a2", "n1", "n2", polarity=False, depth=0)
    ident = Identity([base, plan_denial], "system", None)
    assert ident.members("n1") == ["n1"] and ident.judged[("n1", "n2")][0] == "denied"


# ---- ID-8, ID-9: one identity for every reader ------------------------------------------------------------------------
def _official(view):
    """The official judged by the unconditional declaration (organisation 0.2's; organisation 0.3 also lists a `set`
    declaration for co-signed acts, LABS-1.049, which no act here is)."""
    role = view["roles"].get("official-act:official", {})
    return [(c["judgement"], [p["names"] for p in c["players"]]) for c in role.get("constraints", [])
            if c["kind"] is None]


def test_alias_views_of_an_occurrence_are_the_same(ref):
    wm, _ = ref
    one, other = (wm.occurrence("w", o) for o in ("o-1", "o-1-alias"))
    assert {k: v for k, v in one.items() if k != "occurrence"} == {k: v for k, v in other.items() if k != "occurrence"}
    assert one["aliases"] == ["o-1", "o-1-alias"]
    assert [(a["description"], a["describes"]) for a in one["accounts"]] == [("act-o-1-alias-clerk", "accepted"),
                                                                             ("act-o-1-hr", "accepted")]
    assert one["identity"]["links"][0]["same"] == ["o-1", "o-1-alias"] and one["identity"]["conflict"] is None


def test_alias_views_with_merged_officials_are_established(ref):
    wm, _ = ref
    for o in ("o-1", "o-1-alias"):
        assert _official(wm.occurrence("w", o)) == [("established", [["b-smith", "bea"]])]


def test_alias_views_with_different_officials_are_disputed_from_both_names(ref):
    wm, _ = ref
    for o in ("o-4", "o-4-alias"):
        assert _official(wm.occurrence("w", o)) == [("disputed", [["dan"], ["eve"]])]


def test_occurrence_status_lists_the_accounts_of_every_alias(ref):
    wm, _ = ref
    for o in ("o-1", "o-1-alias"):
        descs = wm.occurrence_status("w", o, T(5))["descriptions"]
        assert [d["description"] for d in descs] == ["act-o-1-alias-clerk", "act-o-1-hr"]


def test_closures_follow_aliases_and_stop_at_a_disputed_link(ref):
    wm, _ = ref
    assert wm.parts("w", "gearbox", T(5)) == ["bolt", "bracket"]        # bolt is part of b-alias = bracket
    assert wm.holds("w", "part-of", {"part": "bolt", "whole": "bracket"}, T(5)).holds is True
    assert wm.parts("w", "motor", T(5)) == ["pump"]                     # pump ~ pump-alias is disputed
    assert wm.dependencies("w", "gearbox", T(5)) == ["b-alias", "seal"]
    assert [d["dependee"] for d in wm.direct_dependencies("w", "b-alias", T(5))] == ["seal"]   # by class (ID-8)


# ---- DI-16 (option a): the reproduction, as a permanent test ----------------------------------------------------------
@pytest.fixture(scope="module")
def di16(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    wm.selective = os.environ.get("WM_SELECTIVE", "1") != "0"
    try:
        wm.install_profile("organisation")
        wm.create_world("actual", id="w")
        for p in ("bea", "b-smith", "hr", "clerk"):
            wm.add_entity("person", p, id=p)
        wm.add_entity("organisation", "depot", id="depot")
        wm.add_entity("social-role", "site-manager", id="site-manager")
        wm.add_entity("occurrence", "o-2", id="o-2")
        acts = {}
        for who, src in (("bea", "hr"), ("b-smith", "clerk")):
            acts[src] = wm.account_attestations("w", org.act_in_office(wm, "w", who, "site-manager", "depot", T(5),
                                                                       occurrence="o-2", attester=src,
                                                                       id=f"act-{src}"))
            for a in acts[src]:
                wm.accept(a)
        link = wm.attest("w", "same-as", {"same": ["bea", "b-smith"]}, until_superseded=True, attester="hr")
        wm.accept(link)
        before = wm.clock.now
        denial = wm.deny("w", "same-as", {"same": ["bea", "b-smith"]}, until_superseded=True, attester="clerk")
        wm.accept(denial)
        yield wm, {"before": before, "link": link, "denial": denial, "acts": acts}
    finally:
        driver.databases.get(name).delete()


@pytest.mark.parametrize("ctx, link, merges, official", [
    ("system now", "disputed", False, [("disputed", [["b-smith"], ["bea"]])]),
    ("system before the denial", "established", True, [("established", [["b-smith", "bea"]])]),
    ("hr", "established", True, [("established", [["bea"]])]),
    ("clerk", "not holding", False, [("established", [["b-smith"]])]),
])
def test_di16_reproduction(di16, ctx, link, merges, official):
    wm, ids = di16
    kw = {"system now": {}, "system before the denial": {"as_of": ids["before"]}, "hr": {"perspective": "hr"},
          "clerk": {"perspective": "clerk"}}[ctx]
    assert wm.judgement("w", "same-as", {"same": ["bea", "b-smith"]}, T(5), **kw).judgement.value == link
    assert ("b-smith" in wm.identity("w", **kw).members("bea")) is merges
    view = wm.occurrence("w", "o-2", **kw)
    assert _official(view) == official


def test_di16_dispute_cites_both_accounts(di16):
    wm, ids = di16
    entry = wm.occurrence("w", "o-2")["roles"]["official-act:official"]["constraints"][0]
    assert entry["status"].name == "DISPUTED"
    assert sorted(a["description"] for p in entry["players"] for a in p["accounts"]) == ["act-clerk", "act-hr"]


def test_identity_report_keeps_the_evidence_of_both_sides(di16):
    wm, ids = di16
    ident = wm.identity("w")
    assert ident.links == [] and ident.conflicts == []                   # a disputed link: no merge, no component
    assert ident.judged[("b-smith", "bea")] == ("disputed", tuple(sorted((ids["link"], ids["denial"]))), 0)
    before = wm.identity("w", as_of=ids["before"])
    assert before.links == [{"same": ["b-smith", "bea"], "judgement": "established", "support": [ids["link"]],
                             "depth": 0, "merges": True}]
