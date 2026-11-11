"""LABS-1.018: explicit measurement provenance, rests-on(attestation, record) (D-C-2).

Each measurement-backed attestation names its own result record; nothing is matched by source, time or content.
Proposition identity (one content for identical results), attestation identity and evidence-record identity stay
distinct; conditions never leak between records; links are written atomically with the attestation and never change
through corrections and supersession; they record evidential dependency, not truth or occurrence.
"""

import uuid

import pytest

from conftest import FakeClock
from worldmodel import QUALITY_MODULES, WorldModel
from worldmodel.examples import lab
from datetime import timedelta

from worldmodel.model import READ, WRITE
from worldmodel import typeql as q
from worldmodel.semantics import Status

T = lab.T
AT20, AT35 = ["T=20C"], ["T=35C"]


@pytest.fixture
def space(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=QUALITY_MODULES, clock=FakeClock())
    try:
        w = wm.create_world("lab", id="lab")
        for i in ("sample", "ana", "b3", "b7"):
            wm.add_entity("physical-object", i, id=i)
        for i in ("qa", "lab-2"):
            wm.add_entity("social-object", i, id=i)
        wm.add_entity("category", "measurement", id="measurement")
        wm.define_unit("kilogram", "mass", id="u-kg")
        wm.define_quality_kind("mass", "mass", id="q-mass")
        yield wm, w
    finally:
        driver.databases.get(name).delete()


def weigh(wm, w, value=3.51, instrument="b3", conditions=AT20, start=T(9), attester="ana", accept=True, **kw):
    m = wm.measure(w, "sample", "q-mass", value, "u-kg", 0.02, start=start, end=start.replace(minute=5),
                   instrument=instrument, operator=attester, conditions=conditions, attester=attester, persists=True,
                   **kw)
    if accept:
        lab.accept_measurement(wm, w, m)
    return m


def records(wm, w, **kw):
    """{attestation: [(record, conditions, instrument)]} as measurements() reports it."""
    return {m["attestation"]: [(r["record"], tuple(r["conditions"]), tuple(r["activities"][0]["instrument"])
                                if r["activities"] else ()) for r in m["records"]]
            for m in wm.measurements(w, "sample", "q-mass", **kw)}


def test_identical_values_from_different_instruments(space):
    wm, w = space
    a, b = weigh(wm, w, instrument="b3"), weigh(wm, w, instrument="b7")
    assert wm._content_key(a["content"]) == wm._content_key(b["content"])      # one proposition (v0.2 4.2) ...
    assert a["content"] != b["content"] and a["result"] != b["result"]          # ... two attestations, two records
    got = records(wm, w)
    assert got[a["content"]] == [(a["result"], tuple(AT20), ("b3",))]
    assert got[b["content"]] == [(b["result"], tuple(AT20), ("b7",))]
    c = wm.compare_measurements(w, "sample", "q-mass")
    assert [(p["relation"], p["reason"]) for p in c["pairs"]] == [("possibly compatible", None)]


def test_identical_values_under_different_conditions_never_leak(space):
    wm, w = space
    a, b = weigh(wm, w, conditions=AT20), weigh(wm, w, conditions=AT35)
    got = records(wm, w)
    assert [x[1] for x in got[a["content"]]] == [tuple(AT20)]
    assert [x[1] for x in got[b["content"]]] == [tuple(AT35)]
    (p,) = wm.compare_measurements(w, "sample", "q-mass")["pairs"]
    assert p["relation"] == "incomparable" and "conditions" in p["reason"]


def test_several_measurements_from_one_source_at_one_time(space):
    wm, w = space
    ms = [weigh(wm, w, value=v, instrument=i) for v, i in ((3.51, "b3"), (3.51, "b3"), (3.52, "b7"))]
    got = records(wm, w)
    assert [got[m["content"]] for m in ms] == [[(m["result"], tuple(AT20), (i,))]
                                              for m, i in zip(ms, ("b3", "b3", "b7"))]
    assert len({m["result"] for m in ms}) == 3


def test_corrections_keep_both_links_and_supersession_is_per_perspective(space):
    wm, w = space
    original = weigh(wm, w, value=3.51)
    wm.accept(original["content"], holder="qa")                     # QA accepted the original
    known = wm.clock.now
    corrected = weigh(wm, w, value=3.53, supersedes=original["content"])
    assert wm.evidence_of(original["content"]) == [original["result"]]          # immutable: still its own record
    assert wm.evidence_of(corrected["content"]) == [corrected["result"]]
    now = {m["attestation"]: m for m in wm.measurements(w, "sample", "q-mass")}
    assert (now[original["content"]]["acceptance"], now[corrected["content"]]["acceptance"]) == \
        ("superseded", "accepted")
    qa = {m["attestation"]: m for m in wm.measurements(w, "sample", "q-mass", perspective="qa")}
    assert qa[original["content"]]["usable"] and qa[original["content"]]["records"][0]["record"] == original["result"]
    before = {m["attestation"]: m for m in wm.measurements(w, "sample", "q-mass", as_of=known)}
    assert corrected["content"] not in before and before[original["content"]]["usable"]


def test_disputed_and_unreviewed_statements_keep_their_own_records(space):
    wm, w = space
    mine = weigh(wm, w, value=3.51)
    theirs = weigh(wm, w, value=3.70, attester="lab-2", accept=False, conditions=["T=20C", "lab-2 method"])
    c = wm.compare_measurements(w, "sample", "q-mass")
    (alt,) = c["alternatives"]
    assert (alt["attestation"], alt["acceptance"], alt["records"][0]["conditions"]) == \
        (theirs["content"], "unreviewed", ["T=20C", "lab-2 method"])
    assert c["status"] == Status.ASSERTED
    lab.accept_measurement(wm, w, theirs)
    (p,) = wm.compare_measurements(w, "sample", "q-mass")["pairs"]
    assert p["relation"] == "incomparable"                          # its own conditions differ; nothing leaked
    same = weigh(wm, w, value=3.80, attester="lab-2")               # same conditions as mine: comparable
    pairs = {frozenset((p["a"], p["b"])): p["relation"] for p in wm.compare_measurements(w, "sample", "q-mass")["pairs"]}
    assert pairs[frozenset((mine["content"], same["content"]))] == "incompatible"


def test_perspectives_see_the_same_links(space):
    wm, w = space
    a = weigh(wm, w, attester="lab-2", accept=False)
    own = {m["attestation"]: m for m in wm.measurements(w, "sample", "q-mass", perspective="lab-2")}
    sys_ = {m["attestation"]: m for m in wm.measurements(w, "sample", "q-mass")}
    assert own[a["content"]]["usable"] and not sys_[a["content"]]["usable"]     # acceptance differs ...
    (mine,), (sys_r,) = own[a["content"]]["records"], sys_[a["content"]]["records"]
    assert (mine["report"], sys_r["report"]) == ("accepted", "unreviewed")      # the report is judged per view ...

    assert mine["activities"][0]["start"] and sys_r["activities"][0]["start"] is None   # ... so is the account's time

    def provenance(r):                                                          # ... the link itself is not
        judged = ("report",)
        return {**{k: v for k, v in r.items() if k not in judged and k != "activities"},
                "activities": [{k: v for k, v in x.items() if k not in ("start", "end", "occurrences")}
                               for x in r["activities"]]}
    assert provenance(mine) == provenance(sys_r) and mine["record"] == a["result"]


def test_hypothetical_worlds_inherit_attestations_with_their_records(space):
    wm, w = space
    base = weigh(wm, w)
    plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(10), id="lab-plan")
    own = weigh(wm, plan, value=3.60, instrument="b7", start=T(11), accept=False)
    got = records(wm, plan)
    assert got[base["content"]] == [(base["result"], tuple(AT20), ("b3",))]     # inherited, with its record
    assert got[own["content"]] == [(own["result"], tuple(AT20), ("b7",))]
    assert own["content"] not in records(wm, w)
    stip = {m["attestation"]: m for m in wm.measurements(plan, "sample", "q-mass")}[own["content"]]
    assert stip["acceptance"] == "accepted" and stip["records"][0]["record"] == own["result"]


def counts(wm):
    """How many event descriptions, attestations, records, rests-on links and propositions are stored."""
    with wm.driver.transaction(wm.database, READ) as tx:
        return {k: len(q.rows(tx, f"match $x isa {k};"))
                for k in ("event", "attestation", "information-object", "rests-on", "proposition")}


MASS = {"bearer": "sample", "quality": "q-mass", "unit": "u-kg"}


def test_attest_evidence_failures_roll_back(space):
    """attest() with evidence: the record writer, the link and the attestation each fail without a trace."""
    wm, w = space
    weigh(wm, w)
    before = counts(wm)

    def boom(tx):
        raise RuntimeError("record writer failed")
    with pytest.raises(RuntimeError):
        wm.attest(w, "has-quality", MASS, params={"lower": 1.0, "upper": 2.0}, start=T(9), until_superseded=True,
                  evidence=[boom], id="att-x")
    assert counts(wm) == before
    with pytest.raises(ValueError, match="not found"):           # the link's record does not exist
        wm.attest(w, "has-quality", MASS, params={"lower": 1.0, "upper": 2.0}, start=T(9), until_superseded=True,
                  evidence=[lambda tx: "no-such-record"], id="att-y")
    assert counts(wm) == before
    with pytest.raises(ValueError):                               # unknown attester
        wm.attest(w, "has-quality", MASS, params={"lower": 1.0, "upper": 2.0}, start=T(9), until_superseded=True,
                  attester="nobody", evidence=[lambda tx: pytest.fail("evidence written before the attestation")])
    assert counts(wm) == before


def _attestation_of(prefix):
    return lambda body, params: "insert $n isa attestation" in body and str(params.get("content", "")).startswith(prefix)


# Each write stage of measure(), in the order it runs (LABS-1.020). The activity's id is "m-fail-activity".
STAGES = {
    "activity description": lambda b, p: "isa event" in b and p.get("id") == "m-fail-activity",
    "activity account": lambda b, p: "insert $n isa attestation" in b and p.get("content") == "m-fail-activity",
    "activity classification": _attestation_of("classified-as|"),
    "content proposition": lambda b, p: "insert $p isa has-quality" in b,
    "content attestation": _attestation_of("has-quality|"),
    "result record": lambda b, p: "insert $r isa information-object" in b,
    "rests-on": lambda b, p: "insert rests-on" in b,
    "produced": _attestation_of("produced|"),
    "reports": _attestation_of("reports|"),
}


@pytest.mark.parametrize("stage", [*STAGES, "final commit"])
def test_measure_is_atomic_at_every_stage(space, monkeypatch, stage):
    """LABS-1.020: a failure at any write stage of measure(), or of its commit, leaves no partial measurement."""
    wm, w = space
    weigh(wm, w)                                                  # existing data: unchanged by the failure
    before = counts(wm)
    real, hit = q.run, []

    def failing(tx, body, params=None):
        if stage in STAGES and STAGES[stage](body, params or {}):
            hit.append(stage)
            raise RuntimeError(f"injected failure: {stage}")
        return real(tx, body, params)
    monkeypatch.setattr(q, "run", failing)
    if stage == "final commit":
        driver = wm.driver

        class FailingCommit:
            def __init__(self, tx):
                self._tx = tx

            def __enter__(self):
                self._tx.__enter__()
                return self

            def __exit__(self, *exc):
                return self._tx.__exit__(*exc)

            def commit(self):
                hit.append(stage)
                raise RuntimeError("injected failure: final commit")

            def __getattr__(self, name):
                return getattr(self._tx, name)

        class Driver:
            databases = driver.databases

            def transaction(self, database, kind):
                tx = driver.transaction(database, kind)
                return FailingCommit(tx) if kind == WRITE else tx
        monkeypatch.setattr(wm, "driver", Driver())
    with pytest.raises(RuntimeError, match="injected"):
        wm.measure(w, "sample", "q-mass", 9.99, "u-kg", 0.02, start=T(11), end=T(11, 5), instrument="b7",
                   operator="ana", conditions=AT20, attester="ana", persists=True, id="m-fail")
    monkeypatch.undo()
    assert hit == [stage]                                         # the failure happened where intended
    assert counts(wm) == before                                   # nothing of the measurement remains
    with wm.driver.transaction(wm.database, READ) as tx:
        assert not q.rows(tx, 'match $x has wm-id $i; { $i == "m-fail-activity"; } or { $i == "m-fail-result"; };')
    ok = weigh(wm, w, value=3.52, instrument="b7")                # the next measurement is unaffected
    assert wm.evidence_of(ok["content"]) == [ok["result"]]


def test_a_measurement_has_one_transaction_time(space):
    """All parts share one recorded-at, so no knowledge time sees part of a measurement."""
    wm, w = space
    m = weigh(wm, w, accept=False)                                # the world's only attestations by ana
    mine = [a for a in wm.visible(w).values() if a.attester == "ana"]
    assert len(mine) == 5                                         # account, classification, content, produced, reports
    assert {m["content"], m["produced"], m["reports"]} <= {a.id for a in mine}
    (t,) = {a.recorded_at for a in mine}
    seen = {x["attestation"]: x for x in wm.measurements(w, "sample", "q-mass", as_of=t, perspective="ana")}
    assert seen[m["content"]]["records"][0]["record"] == m["result"]
    assert seen[m["content"]]["records"][0]["activities"][0]["activity"] == m["activity"]
    earlier = wm.measurements(w, "sample", "q-mass", as_of=t - timedelta(microseconds=1), perspective="ana")
    assert m["content"] not in {x["attestation"] for x in earlier}


def test_not_one_to_one(space):
    wm, w = space
    a = weigh(wm, w)
    both = wm.attest(w, "has-quality", MASS, params={"lower": 3.49, "upper": 3.53}, start=T(9), until_superseded=True,
                     attester="ana", evidence=[lambda tx: a["result"]])     # a second statement, same record
    assert wm.evidence_of(both) == [a["result"]] and wm.evidence_of(a["content"]) == [a["result"]]
    with wm.driver.transaction(wm.database, READ) as tx:
        assert len(q.rows(tx, "match $l isa rests-on;")) == 2


def test_provenance_establishes_neither_truth_nor_occurrence(space):
    wm, w = space
    m = weigh(wm, w, attester="lab-2", accept=False)
    (entry,) = [x for x in wm.measurements(w, "sample", "q-mass") if x["attestation"] == m["content"]]
    assert entry["records"] and not entry["usable"]                               # linked, still not accepted
    assert wm._kind_of_id(m["activity"]) == "event"                               # the activity is a description
    assert wm.interval(w, m["activity"]) is None                                  # its account is not accepted


def test_selective_and_full_load_agree(space):
    wm, w = space
    weigh(wm, w)
    weigh(wm, w, conditions=AT35)
    weigh(wm, w, attester="lab-2", accept=False)

    def answers():
        def clean(xs):
            return [{k: v for k, v in x.items() if k != "_record"} for x in xs]
        return [clean(wm.measurements(w, "sample", "q-mass", perspective=p)) for p in ("system", "lab-2")] + \
               [wm.compare_measurements(w, "sample", "q-mass")["pairs"]]

    wm.selective = True
    a = answers()
    wm.selective = False
    assert answers() == a
