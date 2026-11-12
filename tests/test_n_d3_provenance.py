"""Stage D-3 correction (LABS-1.031): recursive material provenance with marked paths.

A lineage four levels deep (core-1 -> s1 -> s2 -> s4), sibling branches (s2, s2b), a sample with no attested
constitution (s3), a pooled sample with two converging routes (m <- s2, s2b), a disputed ancestral link (s6 <- s1,
under s7), and an unestablished cyclic claim (tom: s1 <- s4). Every link is listed with its own judgement and each
route to it; only links on an established route are established ancestry. Checked across perspectives, knowledge
times, a hypothetical world and both query paths.
"""

import uuid

import pytest

from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel, laboratory as lb
from worldmodel.examples.lab import T

pytestmark = pytest.mark.own_profiles
AT = T(14)


def build_lineage(wm):
    wm.install_profile("laboratory")
    w = wm.create_world("Lineage", id="lin")
    for i in ("core-1", "ana", "bo", "tom", "qa"):
        wm.add_entity("physical-object", i, id=i)
    for i in ("s1", "s2", "s2b", "s3", "s4", "m", "s6", "s7"):
        wm.add_entity("sample", i, id=i)
    for i in ("o1", "o2", "o4"):
        wm.add_entity("occurrence", i, id=i)
    ids = {"world": w}

    def acc(x):
        for a in wm.account_attestations(w, x["event"]):
            wm.accept(a)
        for a in x["effects"]:
            wm.accept(a)

    def made(x, src, start, attester="system", accept=False):
        a = wm.attest(w, "constitution", {"constituted": x, "constituent": src}, start=start, until_superseded=True,
                      attester=attester)
        if accept:
            wm.accept(a)
        return a
    acc(lb.take_sample(wm, w, "ana", "core-1", "s1", T(9), occurrence="o1", attester="ana", id="ev1"))
    made("s1", "core-1", T(9), "ana", accept=True)
    wm.declare_existence(w, "s1", start=T(9), end=T(10))          # a portion: the split ends it
    wm.declare_existence(w, "o1", start=T(9), end=T(9, 10))
    for s in ("s2", "s2b"):
        acc(lb.take_sample(wm, w, "bo", "s1", s, T(10), occurrence="o2" if s == "s2" else None, attester="bo",
                           id=f"ev-{s}"))
        wm.declare_existence(w, s, start=T(10))
    made("s2b", "s1", T(10))
    acc(lb.take_sample(wm, w, "bo", "s2", "s3", T(11), attester="bo", id="ev-s3"))   # no constitution attested
    acc(lb.take_sample(wm, w, "bo", "s2", "s4", T(12), occurrence="o4", attester="bo", id="ev-s4"))
    made("s4", "s2", T(12))
    wm.declare_existence(w, "o4", start=T(12), end=T(12, 5))
    ids["before_s2"] = wm._now()                       # s4 <- s2 known, s2 <- s1 not yet recorded
    made("s2", "s1", T(10))
    made("m", "s2", T(13))                             # a pooled sample: converging routes to s1 and core-1
    made("m", "s2b", T(13))
    made("s6", "s1", T(10))
    made("s7", "s6", T(11))
    ids["before_denial"] = wm._now()                   # s6 <- s1 still established
    ids["denial"] = wm.attest(w, "constitution", {"constituted": "s6", "constituent": "s1"}, start=T(10),
                              until_superseded=True, attester="qa", polarity=False)
    wm.accept(ids["denial"])                           # the system accepts both: s6 <- s1 is disputed
    ids["tom_cycle"] = made("s1", "s4", T(9), "tom")   # unaccepted by the system
    wm.accept(ids["tom_cycle"], holder="tom")
    ids["plan"] = wm.create_world("Plan: s3 from s2", kind="hypothetical", base=w, branch_at=T(20), id="lin-plan")
    wm.attest(ids["plan"], "constitution", {"constituted": "s3", "constituent": "s2"}, start=T(11),
              until_superseded=True)
    return ids


@pytest.fixture(scope="module")
def lineage(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    try:
        yield wm, build_lineage(wm)
    finally:
        driver.databases.get(name).delete()


@pytest.fixture
def lw(lineage):
    wm, ids = lineage
    path = wm.selective
    yield wm, ids["world"], ids
    wm.selective = path


def links(p):
    return {(c["sample"], c["from"]): c for c in p["chain"]}


def routes(c):
    return {">".join([s for s, _ in x["path"]] + [x["path"][-1][1]]): x for x in c["paths"]}


def established_view(p):
    return [(c["sample"], c["from"]) for c in p["established"]]


def assert_paths_follow_their_links(wm, world, p, t, **kw):
    """Requirement 5: a route is established exactly when every link on it is, each judged in the same world,
    perspective, valid time and knowledge time (by the core, independently of provenance)."""
    own = {}
    for c in p["chain"]:
        key = (c["sample"], c["from"])
        own[key] = wm.holds(world, "constitution", {"constituted": key[0], "constituent": key[1]}, t, **kw)
        assert (c["judgement"] == "established") == (own[key].holds is True), key
    for c in p["chain"]:
        for x in c["paths"]:
            assert x["established"] == all(own[tuple(s)].holds is True for s in x["path"])
            assert [(b["sample"], b["from"]) for b in x["blocked_by"]] == [
                tuple(s) for s in x["path"] if own[tuple(s)].holds is not True]
        assert c["ancestry"] == ("established" if any(x["established"] for x in c["paths"]) else "not established")


def test_four_level_recursive_sampling(lw):
    wm, w, _ = lw
    p = lb.provenance(wm, w, "s4", AT)
    assert established_view(p) == [("s4", "s2"), ("s2", "s1"), ("s1", "core-1")]
    assert routes(links(p)[("s1", "core-1")]) .keys() == {"s4>s2>s1>core-1"}
    assert {x: v["established"] for x, v in p["materials"].items()} == {"s2": True, "s1": True, "core-1": True}
    assert set(p["sampling"]) == {"s4", "s2", "s1", "core-1"}          # sampling from an existing sample, twice
    assert [a["event"] for a in p["sampling"]["s2"]] == ["ev-s2"] and p["sampling"]["s1"][0]["event"] == "ev1"
    assert_paths_follow_their_links(wm, w, p, AT)


def test_accounts_occurrences_and_identity_stay_apart_at_depth(lw):
    wm, w, _ = lw
    p = lb.provenance(wm, w, "s4", AT)
    occ = {a["event"]: [(o["occurrence"], o["status"]) for o in a["occurrences"]]
           for x in ("s4", "s2", "s1") for a in p["sampling"][x]}
    assert occ == {"ev-s4": [("o4", "accepted")], "ev-s2": [("o2", "not established")], "ev1": [("o1", "accepted")]}
    s3 = lb.provenance(wm, w, "s3", AT)               # accepted account and claimed effects, no attested constitution
    assert s3["chain"] == [] and s3["established"] == [] and s3["materials"] == {}
    assert [a["account"] for a in s3["sampling"]["s3"]] == ["accepted"]
    assert s3["existence"]["attested"]["judgement"] == "not established"
    assert lb.provenance(wm, w, "s1", AT)["existence"]["attested"]["judgement"] == "expired"


def test_sibling_branches_do_not_inherit_each_other_s_lineage(lw):
    wm, w, ids = lw
    p = lb.provenance(wm, w, "s2b", AT)
    assert established_view(p) == [("s2b", "s1"), ("s1", "core-1")]
    ln = links(p)
    # every claim is still listed, followed and marked: s4 <- s2 is itself established, but reached only through
    # tom's unestablished claim, so it is not ancestry of s2b
    assert set(ln) == {("s2b", "s1"), ("s1", "core-1"), ("s1", "s4"), ("s4", "s2"), ("s2", "s1")}
    assert ln[("s4", "s2")]["judgement"] == "established" and ln[("s4", "s2")]["ancestry"] == "not established"
    assert ln[("s2", "s1")]["ancestry"] == "not established"
    assert {x: v["established"] for x, v in p["materials"].items()} == {
        "s1": True, "core-1": True, "s4": False, "s2": False}
    via = routes(ln[("s4", "s2")])["s2b>s1>s4>s2"]
    assert [(b["sample"], b["from"], b["judgement"]) for b in via["blocked_by"]] == [("s1", "s4", "not established")]
    assert [e["attestation"] for e in via["blocked_by"][0]["evidence"]] == [ids["tom_cycle"]]
    assert_paths_follow_their_links(wm, w, p, AT)


def test_an_unestablished_ancestral_link_blocks_everything_beyond_it(lw):
    wm, w, ids = lw
    tom = links(lb.provenance(wm, w, "s2b", AT))[("s1", "s4")]
    assert tom["judgement"] == "not established" and tom["ancestry"] == "not established"
    assert [e["acceptance"] for e in tom["evidence"]] == ["unreviewed"]


def test_a_disputed_ancestral_link_is_reported_with_its_evidence(lw):
    wm, w, ids = lw
    p = lb.provenance(wm, w, "s7", AT)
    ln = links(p)
    assert established_view(p) == [("s7", "s6")]
    assert ln[("s6", "s1")]["judgement"] == "disputed"
    assert ln[("s1", "core-1")]["judgement"] == "established" and ln[("s1", "core-1")]["ancestry"] == "not established"
    blk = routes(ln[("s1", "core-1")])["s7>s6>s1>core-1"]["blocked_by"]
    assert [(b["sample"], b["from"], b["judgement"]) for b in blk] == [("s6", "s1", "disputed")]
    assert {(e["attester"], e["polarity"]) for e in blk[0]["evidence"]} == {("system", True), ("qa", False)}
    assert ids["denial"] in {e["attestation"] for e in blk[0]["evidence"]}
    assert_paths_follow_their_links(wm, w, p, AT)


def test_converging_paths_are_kept_apart(lw):
    wm, w, _ = lw
    p = lb.provenance(wm, w, "m", AT)
    ln = links(p)
    assert routes(ln[("s1", "core-1")]).keys() == {"m>s2>s1>core-1", "m>s2b>s1>core-1"}
    assert all(x["established"] for x in ln[("s1", "core-1")]["paths"])
    assert [r["path"] for r in p["materials"]["s1"]["paths"]] == [[["m", "s2"], ["s2", "s1"]],
                                                                  [["m", "s2b"], ["s2b", "s1"]]]
    assert len([c for c in p["established"] if (c["sample"], c["from"]) == ("s1", "core-1")][0]["paths"]) == 2
    assert p["materials"]["s4"]["established"] is False and len(p["materials"]["s4"]["paths"]) == 2
    assert_paths_follow_their_links(wm, w, p, AT)


def test_cyclic_claims_terminate_and_are_marked(lw):
    wm, w, _ = lw
    for sample in ("s4", "s2b", "m", "s7"):
        p = lb.provenance(wm, w, sample, AT)
        for c in p["chain"]:
            for x in c["paths"]:
                steps = [s for s, _ in x["path"]] + [x["path"][-1][1]]
                assert len(set(steps[:-1])) == len(steps) - 1               # a route never repeats a material...
                assert x["closes_cycle"] == (steps[-1] in steps[:-1])       # ...except the one that closes a cycle
    cyc = routes(links(lb.provenance(wm, w, "s4", AT))[("s1", "s4")])["s4>s2>s1>s4"]
    assert cyc["closes_cycle"] and not cyc["established"]
    assert "s4" not in lb.provenance(wm, w, "s4", AT)["materials"]           # a sample is never its own ancestor


@pytest.mark.parametrize("sample", ["s4", "s2b", "m", "s7"])
def test_paths_follow_their_links_in_every_perspective(lw, sample):
    wm, w, _ = lw
    for persp in ("system", "tom", "qa"):
        assert_paths_follow_their_links(wm, w, lb.provenance(wm, w, sample, AT, perspective=persp), AT,
                                        perspective=persp)
    tom = lb.provenance(wm, w, "s2b", AT, perspective="tom")
    ln = links(tom)
    assert ln[("s1", "s4")]["judgement"] == "established"           # tom accepts his own claim...
    assert ln[("s1", "s4")]["ancestry"] == "not established"        # ...but not the system's s2b <- s1 below it
    assert tom["established"] == []


def test_knowledge_time_and_valid_time(lw):
    wm, w, ids = lw
    early = lb.provenance(wm, w, "s4", AT, as_of=ids["before_s2"])
    assert established_view(early) == [("s4", "s2")] and set(early["materials"]) == {"s2"}
    assert_paths_follow_their_links(wm, w, early, AT, as_of=ids["before_s2"])
    known = lb.provenance(wm, w, "s7", AT, as_of=ids["before_denial"])
    assert established_view(known) == [("s7", "s6"), ("s6", "s1"), ("s1", "core-1")]
    assert_paths_follow_their_links(wm, w, known, AT, as_of=ids["before_denial"])
    before = lb.provenance(wm, w, "m", T(12))                        # m's constitution is valid from 13:00
    assert before["established"] == [] and all(not v["established"] for v in before["materials"].values())
    assert_paths_follow_their_links(wm, w, before, T(12))


def test_hypothetical_world(lw):
    wm, w, ids = lw
    plan = lb.provenance(wm, ids["plan"], "s3", AT)
    assert established_view(plan) == [("s3", "s2"), ("s2", "s1"), ("s1", "core-1")]
    assert links(plan)[("s3", "s2")]["status"].value == "STIPULATED"
    assert_paths_follow_their_links(wm, ids["plan"], plan, AT)
    assert lb.provenance(wm, w, "s3", AT)["established"] == []      # the actual world is untouched


def test_own_judgements_are_unchanged_by_path_marking(lw):
    """Requirement 7: the links' own judgements are the core's, whichever route reaches them."""
    wm, w, _ = lw
    for sample in ("s4", "s2b", "m", "s7"):
        for c in lb.provenance(wm, w, sample, AT)["chain"]:
            h = wm.holds(w, "constitution", {"constituted": c["sample"], "constituent": c["from"]}, AT)
            assert c["status"] == h.status


def test_selective_and_full_load_agree(lw):
    wm, w, _ = lw
    out = {}
    for path in (True, False):
        wm.selective = path
        out[path] = [lb.provenance(wm, w, s, AT) for s in ("s4", "s2b", "m", "s7")]
    assert out[True] == out[False]
