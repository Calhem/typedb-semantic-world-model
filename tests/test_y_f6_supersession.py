"""F6 (LABS-1.058, DI9-D16): `_level` reads supersessions in two queries (the pairs, then the new attestations by id)
instead of one. Every result is compared with the single-query form (SUPERSESSION_TWO_STEP = False), over:
- several supersessions: a chain of corrections, one attestation corrected twice, ends and corrections;
- duplicate targets: one new attestation superseding two old ones, and a duplicated supersession relation;
- an optional field missing (a correction with no start) and a superseding attestation in another world;
- disputed acceptances of the new attestation (accepted by one perspective, rejected by another);
- inherited worlds: a branch made before the corrections, and a branch correcting its base;
- temporal boundaries: knowledge times before, exactly at and after each supersession, valid times around the branch;
- empty results: attestations with no supersession and a world with no attestations;
- an operation's uncommitted supersession;
- the anchored chunks and the head-form fallback for many ids.
Raw `_level` rows are compared as multisets (TypeDB's answer order is not part of the result).
"""

import pytest

from conftest import T
from worldmodel import typeql as q

PERSPECTIVES = ["system", "A", "lead", "aud"]
TYPES = [None, "located-at", "existence"]


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


def both(wm, f):
    saved = wm.SUPERSESSION_TWO_STEP
    try:
        out = []
        for two in (False, True):
            wm.SUPERSESSION_TWO_STEP = two
            out.append(f())
        return out
    finally:
        wm.SUPERSESSION_TWO_STEP = saved


def raw(wm, world, type=None, subject=None, perspective="system", klim=None):
    """The supersession rows of one `_level` call, as a sorted multiset."""
    with wm._reading() as tx:
        _, supers = wm._level(tx, world, 0, None, klim, type, subject, None, perspective)
    return sorted((tuple(str(v) for v in row[:7]), tuple(sorted(map(str, row[7])))) for row in supers)


def same_load(wm, world, **kw):
    old, new = both(wm, lambda: canon(wm._load(world, **kw)))
    assert new == old
    return old


def same_raw(wm, *args, **kw):
    old, new = both(wm, lambda: raw(wm, *args, **kw))
    assert new == old
    return old


def insert_supersession(wm, old, new):
    with wm._writing() as tx:
        q.run(tx, """match $o isa attestation, has wm-id == $old; $n isa attestation, has wm-id == $new;
            insert supersession (old: $o, new: $n), has recorded-at == $rec;""",
              {"old": old, "new": new, "rec": wm._now()}).as_concept_rows()


@pytest.fixture
def story(wm):
    for kind, n in (("physical-object", "box"), ("physical-object", "crate"), ("physical-object", "lid"),
                    ("place", "shelf-3"), ("place", "shelf-4"), ("place", "shelf-5"), ("physical-object", "A"),
                    ("social-object", "lead"), ("social-object", "aud")):
        wm.add_entity(kind, n, id=n)
    w = wm.create_world("actual", id="actual")
    wm.create_world("empty", id="empty")
    times = {"start": wm.clock.now}
    # a chain of corrections by A: shelf-3 -> shelf-4 -> shelf-5, each accepted by lead, the last rejected by aud
    a1 = wm.attest(w, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_superseded=True,
                   attester="A")
    wm.accept(a1, holder="lead")
    early = wm.attest(w, "located-at", {"located": "crate", "place": "shelf-3"}, start=T("09:00"),
                      until_superseded=True)
    plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("10:30"), id="plan")
    times["branched"] = wm.clock.now
    a2 = wm.attest(w, "located-at", {"located": "box", "place": "shelf-4"}, start=T("10:00"), until_superseded=True,
                   attester="A", supersedes=a1)
    times["a2"] = wm.clock.now
    wm.accept(a2, holder="lead")
    a3 = wm.attest(w, "located-at", {"located": "box", "place": "shelf-5"}, start=T("10:00"), until_superseded=True,
                   attester="A", supersedes=a2)
    wm.accept(a3, holder="lead")
    wm.accept(a3, verdict="rejected", holder="aud")
    # one attestation corrected twice (two successors), one with no start (an optional field missing)
    c1 = wm.attest(w, "located-at", {"located": "lid", "place": "shelf-3"}, start=T("10:00"), until_superseded=True)
    times["before-c"] = wm.clock.now
    c2 = wm.attest(w, "located-at", {"located": "lid", "place": "shelf-4"}, start=T("10:00"), until_superseded=True,
                   supersedes=c1)
    times["c2"] = wm.clock.now
    c3 = wm.attest(w, "located-at", {"located": "lid", "place": "shelf-5"}, until_superseded=True, supersedes=c1)
    # ends: existence of the crate ends at 11:00, then (later in valid time than the branch) at 12:00
    e1 = wm.attest(w, "existence", {"existent": "crate"}, start=T("08:00"), until_superseded=True)
    wm.end(w, e1, T("11:00"))
    # duplicate targets: one new attestation superseding two old ones, and a duplicated supersession relation
    insert_supersession(wm, early, c2)
    insert_supersession(wm, a1, a2)
    times["dup"] = wm.clock.now
    # the branch corrects its base's account, and a later correction in the base starts after the branch point
    wm.attest(plan, "located-at", {"located": "crate", "place": "shelf-5"}, start=T("09:00"), until_superseded=True,
              supersedes=early)
    late = wm.attest(w, "located-at", {"located": "crate", "place": "shelf-4"}, start=T("11:00"),
                     until_superseded=True, supersedes=early)
    times["end"] = wm.clock.now
    return {"w": w, "plan": plan, "times": times, "ids": {"a1": a1, "a2": a2, "a3": a3, "c1": c1, "c2": c2, "c3": c3,
                                                         "e1": e1, "early": early, "late": late}}


@pytest.mark.parametrize("who", PERSPECTIVES)
@pytest.mark.parametrize("world", ["actual", "plan", "empty"])
@pytest.mark.parametrize("type", TYPES)
def test_loads_are_identical(wm, story, who, world, type):
    same_load(wm, world, types=[type] if type else None, perspective=who)


@pytest.mark.parametrize("when", ["start", "branched", "a2", "before-c", "c2", "dup", "end"])
@pytest.mark.parametrize("world", ["actual", "plan"])
def test_loads_are_identical_at_every_knowledge_time(wm, story, when, world):
    for who in PERSPECTIVES:
        same_load(wm, world, as_of=story["times"][when], perspective=who)


@pytest.mark.parametrize("subject", ["box", "crate", "lid", "shelf-3"])
def test_subject_bound_loads_are_identical(wm, story, subject):
    for world in ("actual", "plan"):
        for who in ("system", "lead"):
            same_load(wm, world, types=["located-at"], subjects=[subject], perspective=who)
            same_load(wm, world, subjects=[subject], at=T("10:15"), perspective=who)


def test_raw_rows_keep_every_supersession(wm, story):
    ids = story["ids"]
    rows = same_raw(wm, "actual", "located-at")
    pairs = [(r[0][0], r[0][1]) for r in rows]
    assert pairs.count((ids["a1"], ids["a2"])) == 2                              # the duplicated relation, twice
    assert (ids["a2"], ids["a3"]) in pairs                                        # the chain
    assert {(ids["c1"], ids["c2"]), (ids["c1"], ids["c3"]), (ids["early"], ids["c2"])} <= set(pairs)  # 2 targets
    assert (ids["early"], ids["late"]) in pairs
    missing = [r for r in rows if r[0][1] == ids["c3"]]
    assert missing and all(r[0][4] == "None" for r in missing)                   # no start: kept, with no value
    plan_rows = [r for r in rows if r[0][3] == "plan"]
    assert len(plan_rows) == 1                                                    # the branch's own correction
    for who in PERSPECTIVES:
        lead = same_raw(wm, "actual", "located-at", perspective=who)
        assert sorted(r[0] for r in lead) == sorted(r[0] for r in rows)         # the same pairs for everyone...
    a3 = {r[1] for r in same_raw(wm, "actual", "located-at", perspective="aud") if r[0][1] == ids["a3"]}
    assert all("rejected" in x for t in a3 for x in t)                            # ...with each one's verdicts
    same_raw(wm, "actual", "existence")
    same_raw(wm, "actual", "located-at", "box")
    same_raw(wm, "plan")


def test_superseded_views_follow_the_knowledge_time(wm, story):
    ids, t = story["ids"], story["times"]
    for when, expected in (("branched", []), ("a2", [ids["a2"]]), ("end", [ids["a2"]])):
        a1 = same_load(wm, "actual", as_of=t[when], perspective="lead").get(ids["a1"])
        assert [r["id"] for r in a1["superseded_by"]] == expected                   # duplicates folded once
    c1 = same_load(wm, "actual")[ids["c1"]]
    assert sorted(r["id"] for r in c1["superseded_by"]) == sorted([ids["c2"], ids["c3"]])
    assert [r["id"] for r in same_load(wm, "actual", as_of=t["c2"])[ids["c1"]]["superseded_by"]] == [ids["c2"]]


def test_inherited_worlds_see_only_what_was_known_and_valid_at_the_branch(wm, story):
    ids = story["ids"]
    plan = same_load(wm, "plan")
    assert ids["a1"] in plan and plan[ids["a1"]]["superseded_by"] == []        # corrected after the branch was made
    early = sorted(r["id"] for r in plan[ids["early"]]["superseded_by"])
    assert ids["late"] not in early and len(early) == 1                          # the branch's own correction only
    actual = same_load(wm, "actual")
    assert ids["late"] in [r["id"] for r in actual[ids["early"]]["superseded_by"]]


def test_readers_give_the_same_answers(wm, story):
    for world in ("actual", "plan"):
        for who in PERSPECTIVES:
            for subj in ("box", "crate", "lid"):
                for t in (T("09:30"), T("10:15"), T("11:30"), T("12:30")):
                    old, new = both(wm, lambda: canon(wm.value_at(world, "located-at", subj, t, perspective=who)))
                    assert new == old
            old, new = both(wm, lambda: canon(wm.facts_about(world, "crate", T("11:30"), perspective=who)))
            assert new == old


def test_empty_results(wm, story, monkeypatch):
    seen = []
    real = q.rows
    monkeypatch.setattr(q, "rows", lambda tx, b, p=None: seen.append(b) or real(tx, b, p))
    assert raw(wm, "empty") == [] and not any("supersession" in b for b in seen)      # an empty world: no follow-up
    seen.clear()
    assert same_raw(wm, "actual", "existence", "box") == []                     # nothing in the head
    wm.add_entity("physical-object", "bin", id="bin")
    wm.attest(story["w"], "existence", {"existent": "bin"}, start=T("08:00"), until_superseded=True)
    seen.clear()
    wm.SUPERSESSION_TWO_STEP = True
    assert raw(wm, "actual", "existence", "bin") == []                           # an attestation, no successor
    assert not any("has wm-id == $want" in b for b in seen)                      # no second query without pairs


def test_an_operation_sees_its_own_uncommitted_supersession(wm, story, driver):
    from worldmodel import WorldModel
    ids = story["ids"]
    with wm.operation():
        new = wm.end(story["w"], ids["a3"], T("12:00"))
        for two in (False, True):
            wm.SUPERSESSION_TWO_STEP = two
            got = wm._load("actual", types=["located-at"], perspective="A")[ids["a3"]]
            assert [r.id for r in got.superseded_by] == [new]
        assert WorldModel.open(wm.database, driver=driver)._load("actual")[ids["a3"]].superseded_by == []
    same_load(wm, "actual")


def test_chunks_and_the_head_form_fallback(wm, story, monkeypatch):
    ref = both(wm, lambda: (canon(wm._load("actual")), raw(wm, "actual")))[0]
    for chunk, most in ((1, 1000), (2, 1000), (1000, 1), (2, 3)):
        monkeypatch.setattr(type(wm), "ANCHOR_CHUNK", chunk)
        monkeypatch.setattr(type(wm), "ANCHOR_MAX", most)
        old, new = both(wm, lambda: (canon(wm._load("actual")), raw(wm, "actual")))
        assert old == ref and new == ref


def test_the_two_step_form_uses_two_queries(wm, story, monkeypatch):
    seen = []
    real = q.rows
    monkeypatch.setattr(q, "rows", lambda tx, b, p=None: seen.append(b) or real(tx, b, p))
    wm.SUPERSESSION_TWO_STEP = True
    raw(wm, "actual", "located-at")
    sup = [b for b in seen if "supersession (old: $a, new: $n), has recorded-at $srec" in b]
    assert len(sup) == 1 and "has stance" not in sup[0]                          # the pairs only
    assert sum("has wm-id == $want" in b for b in seen) == 1                     # then the new attestations by id
