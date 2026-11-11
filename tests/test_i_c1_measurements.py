"""Core 0.4 Stage C1 (LABS-1.016): qualities, units and measurements, on the laboratory reference world.

Measurement activity vs result record vs reported content; units and dimension checking; uncertainty and coverage;
conditions; possibly compatible, incompatible and incomparable comparisons (never reconciled); measurements vs
statements (a specification); source disagreement per perspective; a historical correction; hypothetical worlds;
selective/full-load equivalence.
"""

import uuid
from datetime import timedelta

import pytest

from conftest import FakeClock
from worldmodel import QUALITY_MODULES, WorldModel
from worldmodel.examples import lab
from worldmodel.model import READ
from worldmodel.semantics import Status

T = lab.T


def build(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=QUALITY_MODULES, clock=FakeClock())
    return wm, lab.build_lab(wm)


@pytest.fixture(scope="module")
def ref(driver):
    wm, ids = build(driver)
    try:
        yield wm, ids
    finally:
        driver.databases.get(wm.database).delete()


@pytest.fixture
def world(ref):
    wm, ids = ref
    wm.selective = True
    yield wm, ids["world"], ids
    wm.selective = True


@pytest.fixture
def fresh(driver):
    wm, ids = build(driver)
    try:
        yield wm, ids["world"], ids
    finally:
        driver.databases.get(wm.database).delete()


def by_name(ids):
    return {v["content"]: k for k, v in ids["measurements"].items()}


def compare(wm, w, ids, t=T(15), **kw):
    c = wm.compare_measurements(w, "sample-12", ids["mass"], t, **kw)
    names = by_name(ids)
    pairs = {frozenset((names[p["a"]], names[p["b"]])): (p["relation"], p["reason"]) for p in c["pairs"]}
    return c, pairs, names


def test_activity_result_and_content_are_three_things(world):
    wm, w, ids = world
    m = ids["measurements"]["bo-b7"]
    with wm.driver.transaction(wm.database, READ) as tx:
        kinds = wm._kinds_of(tx, [m["activity"], m["result"]])
    assert kinds == {m["activity"]: "event", m["result"]: "information-object"}
    assert "measurement" in {k for e in wm.events(w) if e["event"] == m["activity"] for k in e["kinds"]}
    rec = wm._record(m["result"])
    assert (rec["raw_value"], rec["raw_unit"], rec["standard_uncertainty"], rec["coverage_factor"]) == \
        (3490.0, "u-g", 15.0, 2.0)
    assert rec["calibration"] == "CAL-B7-2026-09"
    content = wm.content(wm._content_key(m["content"]))
    assert (content["type"], content["roles"]["unit"], content["params"]["lower"], content["params"]["upper"]) == \
        ("has-quality", ["u-kg"], pytest.approx(3.46), pytest.approx(3.52))     # stored in SI
    (entry,) = [x for x in wm.measurements(w, "sample-12", ids["mass"]) if x["attestation"] == m["content"]]
    (r,) = entry["records"]
    assert (r["report"], r["activities"][0]["operator"], r["activities"][0]["instrument"]) == \
        ("accepted", ["bo"], ["balance-b7"])


def test_units_and_dimensions(world):
    wm, w, ids = world
    assert wm.convert(3490.0, ids["g"]) == pytest.approx(3.49)
    assert wm.convert(20.0, "u-degC") == pytest.approx(293.15)
    assert wm.convert(293.15, "u-K", to="u-degC") == pytest.approx(20.0)
    with pytest.raises(ValueError, match="cannot convert"):
        wm.convert(1.0, ids["kg"], to="u-m")
    with pytest.raises(ValueError, match="does not measure"):
        wm.measure(w, "sample-12", ids["mass"], 1.0, "u-m", 0.1, start=T(16), end=T(16, 1))
    assert wm.si_unit("temperature") == "u-K"


def test_uncertainty_and_coverage(world):
    wm, w, ids = world
    m = ids["measurements"]
    assert m["bo-b7"]["range"] == pytest.approx((3.46, 3.52))                  # 3490 g +- 2 x 15 g
    assert m["bo-b7"]["coverage_level"] == pytest.approx(0.9545, abs=1e-4)
    assert m["bo-b7-k3"]["coverage_level"] == pytest.approx(0.9973, abs=1e-4)


def test_compatible_incomparable_and_never_merged(world):
    wm, w, ids = world
    c, pairs, names = compare(wm, w, ids)
    assert c["status"] == Status.ASSERTED
    assert pairs[frozenset(("bo-b7", "ana-b3-corrected"))] == ("possibly compatible", None)
    assert pairs[frozenset(("bo-b7", "ana-b9-35C"))][0] == "incomparable"
    assert "conditions" in pairs[frozenset(("bo-b7", "ana-b9-35C"))][1]
    assert "coverage" in pairs[frozenset(("bo-b7", "bo-b7-k3"))][1]
    assert sorted(names[x["attestation"]] for x in c["measurements"]) == \
        ["ana-b3-corrected", "ana-b9-35C", "bo-b7", "bo-b7-k3"]               # each keeps its own range
    assert all(x["kind"] == "measurement" for x in c["measurements"])


def test_a_specification_is_a_statement_not_a_measurement(world):
    wm, w, ids = world
    c, _, _ = compare(wm, w, ids)
    (spec,) = c["statements"]
    assert (spec["attestation"], spec["basis"], spec["records"]) == (ids["spec"], "testimony", [])
    assert ids["spec"] not in {x for p in c["pairs"] for x in (p["a"], p["b"])}   # never compared


def test_an_unaccepted_result_and_source_disagreement(fresh):
    wm, w, ids = fresh
    c, _, names = compare(wm, w, ids)
    assert [names[x["attestation"]] for x in c["alternatives"] if x["acceptance"] == "unreviewed"] == ["lab2"]
    own, _, _ = compare(wm, w, ids, perspective="lab-2")
    assert [names[x["attestation"]] for x in own["measurements"]] == ["lab2"]    # its own view
    lab.accept_measurement(wm, w, ids["measurements"]["lab2"])
    c, pairs, _ = compare(wm, w, ids)
    assert c["status"] == Status.DISPUTED
    assert pairs[frozenset(("bo-b7", "lab2"))] == ("incompatible", None)


def test_a_historical_measurement_and_its_correction(world):
    wm, w, ids = world
    now, _, names = compare(wm, w, ids)
    assert "ana-b3-corrected" in {names[x["attestation"]] for x in now["measurements"]}
    assert [(names[x["attestation"]], x["acceptance"]) for x in now["alternatives"] if names.get(x["attestation"])
            == "ana-b3"] == [("ana-b3", "superseded")]
    before, pairs, _ = compare(wm, w, ids, as_of=ids["known_before_correction"])
    assert "ana-b3" in {names[x["attestation"]] for x in before["measurements"]}
    assert "ana-b3-corrected" not in {names.get(x["attestation"]) for x in before["measurements"]}
    assert pairs[frozenset(("ana-b3", "bo-b7"))] == ("possibly compatible", None)


def test_valid_times_that_do_not_overlap_are_incomparable(fresh):
    wm, w, ids = fresh
    a = wm.measure(w, "sample-12", ids["mass"], 3.51, ids["kg"], 0.02, start=T(16), end=T(16, 5), operator="ana",
                   conditions=["temperature=20C", "humidity=40%"], attester="ana")
    b = wm.measure(w, "sample-12", ids["mass"], 3.51, ids["kg"], 0.02, start=T(17), end=T(17, 5), operator="bo",
                   conditions=["temperature=20C", "humidity=40%"], attester="bo")
    for m in (a, b):
        lab.accept_measurement(wm, w, m)
    c = wm.compare_measurements(w, "sample-12", ids["mass"])
    (p,) = [p for p in c["pairs"] if {p["a"], p["b"]} == {a["content"], b["content"]}]
    assert (p["relation"], p["reason"]) == ("incomparable", "valid times do not overlap")


def test_hypothetical_measurement(fresh):
    wm, w, ids = fresh
    plan = wm.create_world("plan: recalibrated B7", kind="hypothetical", base=w, branch_at=T(14), id="lab-plan")
    wm.measure(plan, "sample-12", ids["mass"], 3.60, ids["kg"], 0.01, start=T(14, 30), end=T(14, 35),
               instrument="balance-b7", operator="bo", conditions=["temperature=20C", "humidity=40%"], persists=True)
    in_plan = wm.compare_measurements(plan, "sample-12", ids["mass"], T(15))
    assert in_plan["status"] == Status.DISPUTED                                  # the stipulated result conflicts
    assert any(x["basis"] == "observation" and x["records"] for x in in_plan["measurements"])
    assert wm.compare_measurements(w, "sample-12", ids["mass"], T(15))["status"] == Status.ASSERTED


def test_selective_and_full_load_agree(world):
    wm, w, ids = world

    def answers():
        return [wm.compare_measurements(w, "sample-12", ids["mass"], T(15), perspective=p) for p in ("system", "lab-2")] + \
               [wm.compare_measurements(w, "sample-12", ids["mass"], T(15), as_of=ids["known_before_correction"]),
                wm.measurements(w, "sample-12", ids["mass"])]

    def clean(x):
        return [{k: v for k, v in m.items() if k != "_record"} for m in x] if isinstance(x, list) else x

    wm.selective = True
    a = [clean(x) for x in answers()]
    wm.selective = False
    assert [clean(x) for x in answers()] == a
