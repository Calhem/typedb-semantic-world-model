"""O-3 (LABS-1.057, DI-9 F4): `occurrence()` loads only the event descriptions linked to the occurrence and its
aliases (by content id), not every event in the world, and shares one identity and describes load between
`descriptions` and the accounts.

Every view is compared with the pre-O-3 path (SCOPE_OCCURRENCE = False, every event in the world), over:
- disputed events (two accounts naming different players) and a disputed describes link;
- unaccepted descriptions (another source's account, unreviewed, and one rejected by the reviewer);
- aliases (same-as between occurrences, accepted by one perspective only);
- inherited worlds (a hypothetical branch with its own account and the base world's);
- temporal boundaries (an earlier knowledge time, before the alias and the later accounts were written);
- unrelated events in the same world and the same occurrence in another world;
- an operation's own uncommitted account.
"""

import pytest

from conftest import T
from worldmodel import WorldModel
from worldmodel import typeql as q

PERSPECTIVES = ["system", "src", "rev"]


def canon(x):
    if hasattr(x, "__dataclass_fields__"):
        return canon(vars(x))
    if isinstance(x, dict):
        return {str(k): canon(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [canon(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted((canon(v) for v in x), key=repr)
    return x


def view(wm, scoped, *args, **kw):
    saved = wm.SCOPE_OCCURRENCE
    try:
        wm.SCOPE_OCCURRENCE = scoped
        return canon(wm.occurrence(*args, **kw))
    finally:
        wm.SCOPE_OCCURRENCE = saved


def same_view(wm, *args, **kw):
    ref = view(wm, False, *args, **kw)
    assert view(wm, True, *args, **kw) == ref
    return ref


@pytest.fixture
def story(wm):
    for kind, n in (("physical-object", "box"), ("physical-object", "crate"), ("physical-object", "lid"),
                    ("social-object", "src"), ("social-object", "rev"), ("social-object", "aud")):
        wm.add_entity(kind, n, id=n)
    for o in ("occ", "occ-alias", "occ-other", "occ-none"):
        wm.add_entity("occurrence", o, id=o)
    w = wm.create_world("actual", id="actual")
    o = wm.create_world("other", id="other")
    # occ: a system account (accepted) and a source's account naming another patient (unreviewed by the system)
    wm.account(w, {"patient": "box"}, T("10:00"), occurrence="occ", id="d-sys")
    d_src = wm.account(w, {"patient": "crate"}, T("10:00"), occurrence="occ", attester="src", id="d-src")
    for a in wm.account_attestations(w, d_src):
        wm.accept(a, holder="rev")                                     # the reviewer accepts the source's account
    mid = wm.clock.now
    # a disputed link: a third account whose describes claim the auditor denies (accepted by the system)
    wm.account(w, {"patient": "lid"}, T("10:05"), occurrence="occ", id="d-disputed")
    wm.accept(wm.deny(w, "describes", {"description": "d-disputed", "occurrence": "occ"}, until_superseded=True,
                      attester="aud"))
    # an alias, accepted by the system only; its own account by the source, rejected by the reviewer
    wm.attest(w, "same-as", {"same": ["occ", "occ-alias"]}, until_superseded=True)
    d_alias = wm.account(w, {"patient": "box", "actor": "src"}, T("10:00"), occurrence="occ-alias", attester="src",
                         id="d-alias")
    for a in wm.account_attestations(w, d_alias):
        wm.accept(a, verdict="rejected", holder="rev")
    # unrelated events in the same world, and the same occurrence in another world
    for i in range(6):
        wm.account(w, {"patient": "crate"}, T(f"11:0{i}"), occurrence="occ-other", id=f"d-other-{i}")
    wm.account(w, {"patient": "lid"}, T("11:30"), id="d-unlinked")                 # describes no occurrence
    wm.account(o, {"patient": "lid"}, T("10:00"), occurrence="occ", id="d-elsewhere")
    # an inherited world: the plan branches at 12:00 and adds its own account of occ after it
    p = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("12:00"), id="plan")
    wm.account(p, {"patient": "crate"}, T("12:30"), occurrence="occ", id="d-plan")
    return {"w": w, "o": o, "p": p, "mid": mid}


@pytest.mark.parametrize("who", PERSPECTIVES)
@pytest.mark.parametrize("world", ["actual", "other", "plan"])
@pytest.mark.parametrize("occ", ["occ", "occ-alias", "occ-other", "occ-none"])
def test_views_are_identical(wm, story, who, world, occ):
    same_view(wm, world, occ, perspective=who)


@pytest.mark.parametrize("who", PERSPECTIVES)
def test_earlier_knowledge_time(wm, story, who):
    for world in ("actual", "plan"):
        for occ in ("occ", "occ-alias"):
            before = same_view(wm, world, occ, as_of=story["mid"], perspective=who)
            known = {a["description"] for a in before["accounts"]}
            # before the alias, the later accounts and the plan were written: occ's two first accounts in actual only
            assert known == ({"d-sys", "d-src"} if (world, occ) == ("actual", "occ") else set())


def test_the_view_keeps_every_kind_of_account(wm, story):
    v = same_view(wm, "actual", "occ")
    acc = {a["description"]: a for a in v["accounts"]}
    assert set(acc) == {"d-sys", "d-src", "d-disputed", "d-alias"}          # aliases included, others not
    assert acc["d-src"]["account"] == "unreviewed" and acc["d-sys"]["account"] == "accepted"
    assert acc["d-disputed"]["describes"] != acc["d-sys"]["describes"]      # the denied link is not established
    assert v["aliases"] == ["occ", "occ-alias"]
    rev = {a["description"]: a for a in same_view(wm, "actual", "occ", perspective="rev")["accounts"]}
    assert rev["d-src"]["account"] == "accepted" and "d-alias" not in rev          # rev has no alias
    plan = {a["description"] for a in same_view(wm, "plan", "occ")["accounts"]}
    assert {"d-sys", "d-src", "d-plan"} <= plan                                      # inherited and own


def test_an_operation_sees_its_own_uncommitted_account(wm, story, driver):
    with wm.operation():
        wm.account(story["w"], {"patient": "crate"}, T("10:20"), occurrence="occ-none", id="d-new")
        for scoped in (False, True):
            v = view(wm, scoped, "actual", "occ-none")
            assert [a["description"] for a in v["accounts"]] == ["d-new"] and v["descriptions"] == ["d-new"]
        outside = WorldModel.open(wm.database, driver=driver)
        assert outside.occurrence("actual", "occ-none")["accounts"] == []
    same_view(wm, "actual", "occ-none")


def test_only_the_linked_descriptions_are_loaded(wm, story, monkeypatch):
    seen = []
    real_docs = q.documents
    monkeypatch.setattr(q, "documents", lambda tx, b, p=None: seen.append((b, p)) or real_docs(tx, b, p))
    heads = lambda: [(b, p) for b, p in seen if "$c isa event;" in b and "fetch" in b and '"aid": $aid, "wid"' in b]
    wm.SCOPE_OCCURRENCE = False
    before = wm.stats["attestations"]
    wm.occurrence("actual", "occ")
    old_atts = wm.stats["attestations"] - before
    assert heads() and all("$cid" not in b for b, _ in heads())                      # every event in the world
    seen.clear()
    wm.SCOPE_OCCURRENCE = True
    before = wm.stats["attestations"]
    wm.occurrence("actual", "occ")
    new_atts = wm.stats["attestations"] - before
    assert heads() and all("has wm-id == $cid" in b for b, _ in heads())
    cids = {r["cid"] for _, p in heads() for r in p}
    assert cids == {"d-sys", "d-src", "d-disputed", "d-alias"}                    # the linked ones, nothing else
    assert new_atts < old_atts
    seen.clear()
    wm.occurrence("actual", "occ-none")                                            # no links: no event head at all
    assert heads() == []


def test_load_by_contents_equals_the_filtered_full_load(wm, story):
    for world in ("actual", "plan"):
        for who in PERSPECTIVES:
            full = wm._load(world, types=["event"], perspective=who)
            ids = ["d-sys", "d-src", "d-plan", "d-missing"]
            part = wm._load(world, types=["event"], perspective=who, contents=ids)
            assert canon(part) == canon({k: v for k, v in full.items() if v.content in ids})
    assert wm._load("actual", types=["event"], contents=[]) == {}
    with pytest.raises(ValueError):
        wm._load("actual", types=["located-at"], contents=["d-sys"])
