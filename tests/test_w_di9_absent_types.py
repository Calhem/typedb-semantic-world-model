"""O-2 (LABS-1.056, DI-9 F3): a subject-bound `_load` skips a (content type, subject) when the subject plays a role in
no stored content of the type, so the loading path never runs the per-world queries whose cost grows with the data
when the type is empty. The check is asked inside the load's own transaction and remembered only for that one load,
so it can never be stale.

Every test compares the answers with the check on (the default) and off (SKIP_ABSENT = False, no skipping):
- absent types: no `same-as` content at all (identity loads), and a type the subject has no content of;
- mixed worlds: `same-as` exists in an unrelated world only, and in the asked world for another subject;
- newly written attestations: the first content of a type written after earlier reads is seen at once;
- transaction visibility: inside an operation, a read sees the operation's own uncommitted same-as and part-of;
- several perspectives (system, a source, a reviewer who rejects), and earlier knowledge times.
"""

import pytest

from conftest import T
from worldmodel import WorldModel
from worldmodel import typeql as q

CHECKS = [False, True]          # SKIP_ABSENT: the reference path first


def canon(x):
    if hasattr(x, "__dataclass_fields__"):
        return canon(vars(x))
    if isinstance(x, dict):
        return {str(k): canon(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, list):
        return sorted((canon(v) for v in x), key=repr)
    if isinstance(x, (tuple, set, frozenset)):
        return tuple(sorted((canon(v) for v in x), key=repr)) if isinstance(x, (set, frozenset)) else tuple(canon(v) for v in x)
    return x


def under(wm, check, f):
    saved = wm.SKIP_ABSENT
    try:
        wm.SKIP_ABSENT = check
        return canon(f())
    finally:
        wm.SKIP_ABSENT = saved


def same_under_every_check(wm, f):
    ref = under(wm, False, f)
    for c in CHECKS[1:]:
        assert under(wm, c, f) == ref, c
    return ref


def readers(wm, world, who="system", as_of=None):
    """The answers that pass through identity and per-type loads."""
    return {
        "value_at": wm.value_at(world, "located-at", "box", T("11:00"), as_of=as_of, perspective=who),
        "holds": wm.holds(world, "located-at", {"located": "box", "place": "shelf"}, T("11:00"), as_of=as_of,
                          perspective=who),
        "facts": wm.facts_about(world, "box", T("11:00"), as_of=as_of, perspective=who),
        "parts": wm.parts(world, "box", T("11:00"), as_of=as_of, perspective=who),
        "identity": wm.identity(world, as_of, who, ids=["box", "crate"]).members("box"),
    }


@pytest.fixture
def base(wm):
    for kind, n in (("physical-object", "box"), ("physical-object", "crate"), ("physical-object", "lid"),
                    ("place", "shelf"), ("place", "bay"), ("social-object", "src"), ("social-object", "rev")):
        wm.add_entity(kind, n, id=n)
    w = wm.create_world("actual", id="actual")
    o = wm.create_world("other", id="other")
    a = wm.attest(w, "located-at", {"located": "box", "place": "shelf"}, start=T("10:00"), until_superseded=True,
                  attester="src")
    wm.accept(a, holder="rev")
    wm.attest(w, "located-at", {"located": "crate", "place": "bay"}, start=T("10:00"), until_superseded=True)
    return w, o


@pytest.mark.parametrize("who", ["system", "src", "rev"])
def test_absent_types(wm, base, who):
    w, _ = base                                     # no same-as and no part-of content anywhere
    ref = same_under_every_check(wm, lambda: readers(wm, w, who))
    assert ref["identity"] == ["box"] and ref["parts"] == []
    same_under_every_check(wm, lambda: wm._load(w, types=["same-as", "part-of"], subjects=["box", "crate"]))


def test_mixed_worlds(wm, base):
    w, o = base
    wm.attest(o, "same-as", {"same": ["box", "crate"]}, until_superseded=True)        # an unrelated world only
    ref = same_under_every_check(wm, lambda: readers(wm, w))
    assert ref["identity"] == ["box"]
    assert same_under_every_check(wm, lambda: readers(wm, o))["identity"] == ["box", "crate"]
    wm.attest(w, "same-as", {"same": ["crate", "lid"]}, until_superseded=True)         # the asked world, other names
    assert same_under_every_check(wm, lambda: readers(wm, w))["identity"] == ["box"]
    same_under_every_check(wm, lambda: wm._load(w, types=["same-as"], subjects=["box", "crate", "lid"]))


def test_newly_written_attestations_are_seen_at_once(wm, base):
    w, _ = base
    before = wm.clock.now
    for c in CHECKS:
        wm.SKIP_ABSENT = c
        assert wm.identity(w, None, "system", ids=["box"]).members("box") == ["box"]
    wm.attest(w, "same-as", {"same": ["box", "lid"]}, until_superseded=True)
    wm.attest(w, "part-of", {"part": "lid", "whole": "box"}, start=T("09:00"), until_superseded=True)
    for c in CHECKS:
        wm.SKIP_ABSENT = c                       # no state survives from the reads before the writes
        assert wm.identity(w, None, "system", ids=["box"]).members("box") == ["box", "lid"]
        assert wm.parts(w, "box", T("11:00")) == ["lid"]
    wm.SKIP_ABSENT = True
    same_under_every_check(wm, lambda: readers(wm, w))
    same_under_every_check(wm, lambda: readers(wm, w, as_of=before))     # earlier knowledge: still absent


@pytest.mark.parametrize("check", CHECKS)
def test_an_operation_sees_its_own_uncommitted_writes(wm, base, driver, check):
    w, _ = base
    wm.SKIP_ABSENT = check
    with wm.operation():
        assert wm.parts(w, "box", T("11:00")) == []                          # read first: part-of absent
        assert wm.identity(w, None, "system", ids=["lid"]).members("lid") == ["lid"]
        assert wm.holds(w, "part-of", {"part": "lid", "whole": "box"}, T("11:00")).holds is not True
        wm.attest(w, "part-of", {"part": "lid", "whole": "box"}, start=T("09:00"), until_superseded=True)
        wm.attest(w, "same-as", {"same": ["crate", "lid"]}, until_superseded=True)
        assert wm.parts(w, "box", T("11:00")) == ["lid"]                     # the same transaction, now present
        assert wm.holds(w, "part-of", {"part": "lid", "whole": "box"}, T("11:00")).holds is True
        assert wm.identity(w, None, "system", ids=["lid"]).members("lid") == ["crate", "lid"]
        outside = WorldModel.open(wm.database, driver=driver)
        outside.SKIP_ABSENT = check
        assert outside.parts(w, "box", T("11:00")) == []                     # not committed: absent outside
        assert outside.identity(w, None, "system", ids=["lid"]).members("lid") == ["lid"]
    assert wm.parts(w, "box", T("11:00")) == ["lid"]


def test_the_check_is_skipped_when_content_exists_and_asked_once_per_load(wm, base, monkeypatch):
    w, _ = base
    seen = []
    real_rows, real_docs = q.rows, q.documents
    monkeypatch.setattr(q, "rows", lambda tx, b, p=None: seen.append(b) or real_rows(tx, b, p))
    monkeypatch.setattr(q, "documents", lambda tx, b, p=None: seen.append(b) or real_docs(tx, b, p))
    wm._load(w, types=["same-as"], subjects=["box", "crate"])                # same-as absent: no head query at all
    assert not any("isa attestation" in b for b in seen)
    assert sum("limit 1" in b for b in seen) == 2                            # one check per subject
    seen.clear()
    p = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T("12:00"), id="plan")
    wm._load(p, types=["same-as", "located-at"], subjects=["box"])          # two worlds in the chain
    assert sum("limit 1" in b for b in seen) == 2                            # once per (type, subject), not per world
    assert sum("isa attestation" in b and "isa located-at" in b for b in seen) == 2   # located-at: both worlds read
    seen.clear()
    wm.SKIP_ABSENT = False
    wm._load(w, types=["same-as"], subjects=["box"])
    assert not any("limit 1" in b for b in seen)                             # off: no check, the head form runs
