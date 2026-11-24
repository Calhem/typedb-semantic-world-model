"""O-1 (LABS-1.056, DI-9 F2): `_level` reads roles, quality parameters, acceptances and supersessions starting from the
attestation ids its filtered head query returned, in bounded chunks, instead of repeating the head and joining it to
those relations. It must read exactly what the head form read.

The ids are passed as given rows, one per id, in chunks of ANCHOR_CHUNK (a disjunction of ids measured superlinear in
its size). Each test loads the same data three ways and compares the records field by field (roles, acceptances, supersessions
and their acceptances included):
- `head`: the pre-O-1 form for every follow-up query (ANCHOR_MAX = -1);
- `anchored`: the default bounds;
- `chunked`: chunks of 2 ids, so every load with more than two attestations is split.
Scenarios: unrelated worlds whose attestations share contents and are superseded; a hypothetical world whose
supersession replaces a base-world attestation; disputed claims with acceptances and rejections by several
perspectives; knowledge-time and valid-time boundaries; quality parameters; subject-bound, type-bound and full loads.
"""

import pytest

from conftest import T
from worldmodel import typeql as q

MODES = {"head": {"ANCHOR_MAX": -1}, "anchored": {}, "chunked": {"ANCHOR_CHUNK": 2, "ANCHOR_MAX": 10_000}}


def norm(recs):
    out = {}
    for aid, r in recs.items():
        d = dict(vars(r))
        d["acceptances"] = sorted(map(str, d["acceptances"]))
        d["superseded_by"] = sorted((x.id, str(x.recorded_at), x.attester, x.stance, tuple(sorted(map(str, x.acceptances))))
                                    for x in d["superseded_by"])
        d["roles"] = {k: sorted(v) for k, v in (d["roles"] or {}).items()}
        d["concrete_roles"] = {k: sorted(v) for k, v in (d["concrete_roles"] or {}).items()}
        out[aid] = d
    return out


def in_mode(wm, mode, f):
    saved = {k: getattr(wm, k) for k in ("ANCHOR_CHUNK", "ANCHOR_MAX")}
    try:
        for k, v in MODES[mode].items():
            setattr(wm, k, v)
        return f()
    finally:
        for k, v in saved.items():
            setattr(wm, k, v)


def same_in_every_mode(wm, f, transform=norm):
    results = {m: transform(in_mode(wm, m, f)) for m in MODES}
    assert results["anchored"] == results["head"]
    assert results["chunked"] == results["head"]
    return results["head"]


@pytest.fixture
def worlds(wm):
    """`actual` (box, crate; three attesters; acceptances and a rejection), an unrelated actual world `other` with the
    SAME contents and its own supersessions, and a hypothetical `plan` branched from `actual` that moves the box."""
    for kind, n in (("physical-object", "box"), ("physical-object", "crate"), ("place", "shelf-3"), ("place", "shelf-4"),
                    ("place", "bay"), ("social-object", "A"), ("social-object", "B"), ("social-object", "lead")):
        wm.add_entity(kind, n, id=n)
    w = wm.create_world("actual", id="actual")
    o = wm.create_world("other", id="other")
    a1 = wm.attest(w, "located-at", {"located": "box", "place": "shelf-3"}, start=T("10:00"), until_superseded=True,
                   attester="A")
    b1 = wm.attest(w, "located-at", {"located": "box", "place": "shelf-4"}, start=T("10:00"), until_superseded=True,
                   attester="B")                                             # disputes A
    wm.accept(a1, holder="lead")
    wm.accept(b1, verdict="rejected", holder="lead")
    mid = wm.clock.now
    e1 = wm.end(w, a1, T("12:00"))                                            # A ends its own claim: a supersession
    wm.accept(e1, holder="lead")
    wm.move(w, "box", "bay", T("12:00"))
    wm.attest(w, "located-at", {"located": "crate", "place": "shelf-3"}, start=T("09:00"), end=T("11:00"))
    for i, (thing, place) in enumerate([("box", "shelf-3"), ("box", "shelf-4"), ("crate", "bay")]):
        x = wm.attest(o, "located-at", {"located": thing, "place": place}, start=T(f"1{i}:30"), until_superseded=True)
        wm.end(o, x, T(f"1{i}:45"))                                          # same contents, other world, superseded
        wm.move(o, thing, "bay", T(f"1{i}:50"))
    p = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("11:00"), id="plan")
    wm.end(p, b1, T("11:30"))                                                # supersedes an inherited attestation
    wm.move(p, "box", "shelf-4", T("11:40"))
    return {"actual": w, "other": o, "plan": p, "a1": a1, "b1": b1, "mid": mid}


@pytest.mark.parametrize("world", ["actual", "other", "plan"])
@pytest.mark.parametrize("perspective", ["system", "lead", "A"])
def test_full_load_reads_the_same(wm, worlds, world, perspective):
    same_in_every_mode(wm, lambda: wm._load(world, perspective=perspective))


@pytest.mark.parametrize("world", ["actual", "plan"])
def test_subject_and_type_loads_read_the_same(wm, worlds, world):
    for subj in ("box", "crate", "bay"):
        same_in_every_mode(wm, lambda: wm._load(world, types=["located-at"], subjects=[subj], perspective="lead"))
        same_in_every_mode(wm, lambda: wm._load(world, subjects=[subj]))
    same_in_every_mode(wm, lambda: wm._load(world, types=["located-at"]))
    same_in_every_mode(wm, lambda: wm._load(world, types=["event"]))


def test_unrelated_world_attestations_and_supersessions_stay_out(wm, worlds):
    recs = same_in_every_mode(wm, lambda: wm._load("actual", types=["located-at"], subjects=["box"]))
    assert recs and all(r["world"] == "actual" for r in recs.values())
    other = same_in_every_mode(wm, lambda: wm._load("other", types=["located-at"], subjects=["box"]))
    assert not set(recs) & set(other)
    replaced = {x[0] for r in recs.values() for x in r["superseded_by"]}
    assert replaced and not replaced & set(other)                           # successors are `actual`'s own


def test_knowledge_and_valid_time_boundaries(wm, worlds):
    mid = worlds["mid"]
    for kw in ({"as_of": mid}, {"at": T("10:00")}, {"at": T("12:00")}, {"at": T("09:59")}, {"as_of": mid, "at": T("12:00")}):
        same_in_every_mode(wm, lambda: wm._load("actual", types=["located-at"], subjects=["box"], **kw))
        same_in_every_mode(wm, lambda: wm._load("plan", types=["located-at"], subjects=["box"], **kw))
    before = same_in_every_mode(wm, lambda: wm._load("actual", as_of=mid))
    assert all(not r["superseded_by"] for r in before.values())              # the move was recorded after `mid`


def test_hypothetical_supersession_of_an_inherited_attestation(wm, worlds):
    recs = same_in_every_mode(wm, lambda: wm._load("plan", types=["located-at"], subjects=["box"]))
    inherited = [r for r in recs.values() if r["depth"] == 1 and r["superseded_by"]]
    assert inherited                                                        # replaced from `plan`


def test_disputed_claims_and_acceptances_read_the_same(wm, worlds):
    recs = same_in_every_mode(wm, lambda: wm._load("actual", types=["located-at"], subjects=["box"], perspective="lead"))
    verdicts = {aid: [a.split(",")[1].strip(" '") for a in r["acceptances"]] for aid, r in recs.items()}
    assert verdicts[worlds["a1"]] == ["accepted"] and verdicts[worlds["b1"]] == ["rejected"]
    for who in ("lead", "A", "B", "system"):
        ans = same_in_every_mode(wm, lambda: wm.value_at("actual", "located-at", "box", T("11:00"), perspective=who),
                                 transform=lambda a: (a.status, a.values, a.support, a.conflicts))
        assert ans is not None


def test_readers_answer_the_same(wm, worlds):
    for world in ("actual", "plan", "other"):
        for t in (T("10:00"), T("11:15"), T("12:30")):
            same_in_every_mode(wm, lambda: wm.value_at(world, "located-at", "box", t),
                               transform=lambda a: (a.status, a.values, a.support, a.conflicts, a.alternatives))
            same_in_every_mode(wm, lambda: wm.facts_about(world, "box", t), transform=repr)
        same_in_every_mode(wm, lambda: wm.changes(world, "box", T("09:00"), T("13:00")), transform=repr)


def test_quality_parameters_read_the_same(wm):
    wm.add_entity("physical-object", "rod", id="rod")
    wm.add_entity("quality-kind", "length", id="length")
    wm.add_entity("unit", "mm", id="mm")
    w = wm.create_world("actual", id="actual")
    for n in ("A", "B"):
        wm.add_entity("social-object", n, id=n)
    for i, (lo, hi) in enumerate([(9.0, 11.0), (10.0, 10.5), (12.0, 12.0)]):
        wm.attest(w, "has-quality", {"bearer": "rod", "quality": "length", "unit": "mm"},
                  params={"lower": lo, "upper": hi}, start=T(f"1{i}:00"), until_superseded=True,
                  attester=["A", "B", "system"][i])
    for kw in ({}, {"types": ["has-quality"], "subjects": ["rod"]}):
        recs = same_in_every_mode(wm, lambda: wm._load(w, **kw))
        assert sorted((r["params"]["lower"], r["params"]["upper"]) for r in recs.values()) == \
            [(9.0, 11.0), (10.0, 10.5), (12.0, 12.0)]


def test_follow_up_queries_are_anchored(wm, worlds, monkeypatch):
    seen = []
    real = q.rows

    def spy(tx, body, params=None):
        seen.append(body)
        return real(tx, body, params)

    monkeypatch.setattr(q, "rows", spy)
    wm._load("actual", types=["located-at"], subjects=["box"])
    anchored = [b for b in seen if b.startswith("match $a isa attestation (content: $c), has wm-id == $anchor;")]
    assert anchored and all("isa world" not in b for b in anchored)


def test_an_empty_head_runs_no_follow_up_query(wm, worlds, monkeypatch):
    seen = []
    real_rows, real_docs = q.rows, q.documents
    monkeypatch.setattr(q, "rows", lambda tx, b, p=None: seen.append(b) or real_rows(tx, b, p))
    monkeypatch.setattr(q, "documents", lambda tx, b, p=None: seen.append(b) or real_docs(tx, b, p))
    assert wm._load("other", types=["located-at"], subjects=["shelf-4"], at=T("00:01")) == {}
    assert not any("acceptance" in b or "supersession" in b for b in seen)


def test_a_query_runs_once_per_given_row(wm, worlds):
    with wm._reading() as tx:
        one = [q.rows(tx, "match $x has wm-id == $i; $x has name $n;", {"i": i}) for i in ("box", "crate", "bay")]
        many = q.rows(tx, "match $x has wm-id == $i; $x has name $n;", [{"i": i} for i in ("box", "crate", "bay")])
        assert sorted(q.opt(r, "n") for r in many) == sorted(q.opt(r, "n") for rs in one for r in rs) == \
            ["bay", "box", "crate"]
        with pytest.raises(ValueError):
            q.rows(tx, "match $x has wm-id == $i;", [{"i": "box"}, {"j": "crate"}])
