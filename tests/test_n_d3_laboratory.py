"""Core 0.4 Stage D-3 (LABS-1.028): the laboratory profile on the laboratory reference world.

Samples and sampling (sample identity, constitution, sampling account and occurrence kept apart), an experiment with
documented steps, calibration as evidence-aware content (in force, expired, disputed, denied, not established,
reference checks; never invalidating a measurement) across perspectives, knowledge time and hypothetical worlds,
interpretations (testimony, hypothesis, no formal derivation; rivals judged independently), installation alone and
with the other profiles in every order, unchanged core answers, and both query paths.
"""

import itertools
import json
import uuid
from datetime import datetime, timezone

import pytest

import profile_fixtures as F
from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel, laboratory as lb
from worldmodel.examples import lab, laboratory as ex
from worldmodel import typeql as q
from worldmodel.model import READ
from worldmodel.profiles import schema_snapshot
from worldmodel.semantics import Status

T = ex.T
pytestmark = pytest.mark.own_profiles
LAB_TYPES = ["calibration-of", "sample", "sampling"]


@pytest.fixture(scope="module")
def ref(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    try:
        for p in ("mechanical", "organisation", "laboratory"):
            wm.install_profile(p)
        yield wm, ex.build_laboratory(wm)
    finally:
        driver.databases.get(name).delete()


@pytest.fixture
def world(ref):
    wm, ids = ref
    path = wm.selective
    yield wm, ids["world"], ids
    wm.selective = path


@pytest.fixture
def make(driver):
    made = []

    def _make():
        name = f"wm-test-{uuid.uuid4().hex[:10]}"
        made.append(name)
        return WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    yield _make
    for name in made:
        driver.databases.get(name).delete()


def snapshot(wm):
    """The schema, comparable across databases (sets sorted)."""
    with wm.driver.transaction(wm.database, READ) as tx:
        snap = schema_snapshot(tx)
    return {k: sorted(map(repr, v)) if isinstance(v, (set, frozenset)) else v for k, v in snap.items()}


def cal(wm, w, instrument, t, **kw):
    v = lb.calibration_status(wm, w, instrument, t, **kw)
    return v["judgement"], v["status"], {c["certificate"]: c["judgement"] for c in v["certificates"]}


def rows(wm, w, **kw):
    return {r["record"]: r for r in lb.measurement_calibration(wm, w, "sample-12", "q-mass", **kw)}


# ---- installation and coexistence ---------------------------------------------------------------------------------------
def test_installs_alone_and_refuses_use_without_the_profile(make):
    bare = make()
    with pytest.raises(ValueError, match="laboratory profile is not installed"):
        lb.calibration_status(bare, "lab", "balance-b3", T(9))
    assert bare.install_profile("laboratory") == LAB_TYPES
    assert bare.profile_status("laboratory") == "installed" and bare.profiles() == {"laboratory": "0.1"}
    with bare.driver.transaction(bare.database, READ) as tx:
        seeded = sorted(q.opt(r, "id") for r in q.rows(tx, """match $c isa category, has wm-id $id;
            $id like "^laboratory:";"""))
    assert seeded == sorted((lb.CALIBRATION, lb.EXPERIMENT, lb.SPECIMEN))     # the seeded vocabulary, prefixed
    assert bare.core_type("sample") == "physical-object" and bare.core_type("sampling") == "event"
    assert bare.core_type("calibration-of") == "proposition"
    assert bare.core_role("sampling:sampler") == "actor"
    assert bare.core_role("sampling:sampled") == "origin"
    assert bare.core_role("sampling:product") == "destination"


def test_three_profiles_install_together_in_every_order_with_the_same_schema(make):
    snaps = set()
    for order in itertools.permutations(("mechanical", "organisation", "laboratory")):
        wm = make()
        installed = {p: wm.install_profile(p) for p in order}
        assert installed["laboratory"] == LAB_TYPES
        assert set(wm.profiles()) == set(order)
        snaps.add(json.dumps(snapshot(wm), sort_keys=True, default=str))
    assert len(snaps) == 1                                  # order makes no difference to the resulting schema


def test_no_collisions_or_ambiguous_types_with_the_other_profiles_and_the_fixtures(make):
    wm = make()
    owned = {p: set(wm.install_profile(p)) for p in ("laboratory", "mechanical", "organisation")}
    for fixture in F.ALL:                                   # the renamed fixtures (D-D3-5) install alongside
        owned[fixture.name] = set(wm.install_profile(fixture))
        assert sorted(owned[fixture.name]) == F.NEW_TYPES[fixture.name]
    for (a, x), (b, y) in itertools.combinations(owned.items(), 2):
        assert not x & y, (a, b, x & y)                     # every new label belongs to exactly one profile
    fixtures = {f.name: f for f in F.ALL}
    assert all(wm.profile_status(fixtures.get(p, p)) == "installed" for p in owned)
    assert wm.core_type("aliquot") == "physical-object" and wm.core_type("sample") == "physical-object"
    assert not wm.is_a("aliquot", "sample") and not wm.is_a("sample", "aliquot")


def test_core_answers_are_unchanged_by_installing_the_three_profiles(make):
    wm = make()
    ids = lab.extend_lab_agency(wm, lab.build_lab(wm))
    w, mass = ids["world"], ids["mass"]

    def answers():
        def clean(x):
            return [{k: v for k, v in m.items() if k != "_record"} for m in x] if isinstance(x, list) else x
        return json.dumps([clean(wm.compare_measurements(w, "sample-12", mass, T(15), perspective=p))
                           for p in ("system", "lab-2")] +
                          [clean(wm.measurements(w, "sample-12", mass)),
                           wm.capable(w, "ana", "can-weigh", T(9), "lab-1"),
                           wm.check_action(w, ids["tom_event"], "can-weigh", "lab-1")], sort_keys=True, default=str)
    before = answers()
    for p in ("organisation", "laboratory", "mechanical"):
        wm.install_profile(p)
    assert answers() == before


# ---- samples, sampling and provenance -----------------------------------------------------------------------------------
def test_provenance_lists_the_attested_constitution_chain(world):
    wm, w, ids = world
    pr = lb.provenance(wm, w, "s12-b", T(16))
    assert [(c["sample"], c["from"], c["judgement"], c["status"]) for c in pr["chain"]] == [
        ("s12-b", "s12-a", "established", Status.ASSERTED), ("s12-a", "sample-12", "established", Status.ASSERTED)]
    assert all(c["evidence"] for c in pr["chain"])
    assert wm.holds(w, "classified-as", {"classified": "sample-12", "class": lb.SPECIMEN}, T(16)).holds is True
    assert wm.is_a("sample", "physical-object")


def test_a_sampling_account_is_not_its_occurrence_nor_the_sample_s_state(world):
    wm, w, ids = world
    pr = lb.provenance(wm, w, "s12-b", T(16))
    s1 = pr["sampling"]["s12-a"][0]
    assert (s1["event"], s1["account"]) == ("ev-sampling-1", "accepted")
    assert s1["occurrences"] == [{"occurrence": "o-sampling-1", "status": "not established"}]  # nobody attests it
    assert {e["outcome"]: e["claim"] for e in s1["claimed_effects"]} == {"existence": "accepted",
                                                                          "constitution": "accepted"}
    split = pr["sampling"]["s12-b"][0]
    assert split["occurrences"] == [{"occurrence": "o-split-b", "status": "accepted"}]           # the lab log
    assert pr["sampling"]["sample-12"] == []


def test_a_claimed_effect_is_not_evidence_of_the_state(world):
    wm, w, ids = world
    c = lb.provenance(wm, w, "s12-c", T(16))
    (acc,) = c["sampling"]["s12-c"]
    assert acc["account"] == "not accepted" and [e["claim"] for e in acc["claimed_effects"]] == ["unreviewed"] * 2
    assert c["chain"] == [] and c["existence"]["attested"]["judgement"] == "not established"
    # In Bo's own perspective his account and both claimed effects are accepted, yet nothing attests that s12-c
    # exists or what it is made of: a claimed effect is a claim about the event, not the state itself
    bo = lb.provenance(wm, w, "s12-c", T(16), perspective="bo")
    assert bo["sampling"]["s12-c"][0]["account"] == "accepted"
    assert [e["claim"] for e in bo["sampling"]["s12-c"][0]["claimed_effects"]] == ["accepted"] * 2
    assert bo["chain"] == [] and bo["existence"]["attested"]["judgement"] == "not established"
    assert wm.holds(w, "existence", {"existent": "s12-c"}, T(16), perspective="bo").status == Status.NOT_YET_KNOWN


def test_a_sample_is_a_portion_the_split_ends_it(world):
    wm, w, ids = world
    assert lb.provenance(wm, w, "s12-a", T(15))["existence"]["attested"]["judgement"] == "established"
    after = lb.provenance(wm, w, "s12-a", T(16))
    assert after["existence"]["attested"]["judgement"] == "expired" and after["existence"]["attested"]["holds"] is False
    assert lb.provenance(wm, w, "s12-b", T(16))["existence"]["attested"]["judgement"] == "established"


def test_custody_history_and_location(world):
    wm, w, ids = world
    a = lb.provenance(wm, w, "s12-a", T(15))
    assert [(x["place"], x["attester"], x["acceptance"]) for x in a["locations"]] == [("freezer-2", "ana", "accepted")]
    assert a["location_at_t"]["places"] == ["freezer-2"]
    b = lb.provenance(wm, w, "s12-b", T(16))
    assert b["location_at_t"] == {"status": Status.ASSERTED, "places": ["freezer-2"]}


def test_only_a_sample_can_be_a_sampling_product(world):
    wm, w, ids = world
    before = wm.count("sampling")
    with pytest.raises(Exception):
        lb.take_sample(wm, w, "ana", "sample-12", "balance-b9", T(17))           # an instrument is not a sample
    assert wm.count("sampling") == before


# ---- the experiment ---------------------------------------------------------------------------------------------------
def test_an_experiment_lists_its_documented_steps(world):
    wm, w, ids = world
    assert wm.holds(w, "classified-as", {"classified": "o-exp-1", "class": lb.EXPERIMENT}, T(16)).holds is True
    steps = wm.process_steps(w, "o-exp-1", T(16))
    assert [(s["occurrence"], s["actors"]) for s in steps] == [("o-sampling-1", ["ana"]), ("o-weigh-late", ["ana"]),
                                                               ("o-split-b", ["bo"])]
    documented = {r for h in wm.history(w, "o-exp-1") for r in wm.evidence_of(h["attestation"])}
    assert documented == {"protocol-7"}
    assert "o-split-c" not in [s["occurrence"] for s in steps]                   # no part-of claimed for it


# ---- calibration --------------------------------------------------------------------------------------------------------
def test_calibration_cases_at_a_time(world):
    wm, w, ids = world
    assert cal(wm, w, "balance-b3", T(9)) == ("established", Status.ASSERTED, {"cert-b3": "established"})
    assert cal(wm, w, "balance-b3", T(15)) == ("expired", Status.ASSERTED, {"cert-b3": "expired"})
    assert cal(wm, w, "balance-b7", T(10)) == ("disputed", Status.DISPUTED, {"cert-b7": "disputed"})
    assert cal(wm, w, "balance-b9", T(12)) == ("not established", Status.NOT_YET_KNOWN, {})   # none recorded
    early = datetime(2026, 10, 31, 12, tzinfo=timezone.utc)
    assert cal(wm, w, "balance-b3", early)[0] == "not yet effective"
    v = lb.calibration_status(wm, w, "balance-b3", T(9))
    assert v["in_force"] == ["cert-b3"] and v["certificates"][0]["reference"] == "CAL-B3-2026-10"
    assert [e["attester"] for e in v["certificates"][0]["evidence"]] == ["cal-lab"]


def test_calibration_by_perspective_knowledge_time_and_world(world):
    wm, w, ids = world
    assert cal(wm, w, "balance-b7", T(10), perspective="qa") == ("denied", Status.ASSERTED, {"cert-b7": "denied"})
    assert cal(wm, w, "balance-b7", T(10), as_of=ids["known_before_qa"])[0] == "established"
    plan = ids["plan_recal"]
    assert cal(wm, plan, "balance-b3", T(15)) == ("established", Status.STIPULATED,
                                                 {"cert-b3": "expired", "cert-b3-r": "established"})
    assert cal(wm, w, "balance-b3", T(15))[0] == "expired"                       # the actual world is unchanged


def test_an_unreviewed_calibration_establishes_nothing(make):
    wm = make()
    wm.install_profile("laboratory")
    w = wm.create_world("Lab", id="lab")
    wm.add_entity("physical-object", "Balance", id="bal")
    wm.add_entity("social-object", "Calibrator", id="calibrator")
    lb.register_certificate(wm, "Certificate", None, id="cert")                  # a certificate without a number
    lb.calibrate(wm, w, "cert", "bal", start=T(0, day=1), attester="calibrator")
    v = lb.calibration_status(wm, w, "bal", T(9))
    assert (v["judgement"], v["status"], v["holds"]) == ("not established", Status.UNKNOWN, None)
    assert v["certificates"][0]["reference"] is None
    assert wm.evidence_of(v["certificates"][0]["evidence"][0]["attestation"]) == ["cert"]       # rests on it


def test_stated_reference_and_attested_calibration_are_reported_side_by_side(world):
    wm, w, ids = world
    r = rows(wm, w)
    check = {k: (v["stated_reference"], v["attested"]["judgement"] if v["attested"] else None,
                 v["reference_check"]["check"]) for k, v in r.items()}
    assert check == {
        "m-ana-b3-corr-result": ("CAL-B3-2026-10", "established", "matches a certificate"),
        "m-ana-b3-late-result": ("CAL-B3-2026-10", "expired", "matches a certificate"),      # matches, but expired
        "m-ana-b3-result": ("CAL-B3-2026-10", "established", "matches a certificate"),
        "m-ana-b9-result": (None, "not established", "no reference stated"),
        "m-bo-b7-result": ("CAL-B7-2026-09", "disputed", "no certificate with the stated reference"),  # inconsistent
        "m-bo-k3-result": (None, "disputed", "no reference stated"),
        "m-lab2-result": (None, None, "no instrument recorded")}
    assert r["m-ana-b3-late-result"]["reference_check"]["certificates"] == [{"certificate": "cert-b3",
                                                                             "judgement": "expired"}]
    assert r["m-ana-b3-late-result"]["at"] == T(15)                               # judged at the activity's start
    assert wm._record("m-bo-b7-result")["calibration"] == "CAL-B7-2026-09"         # the stated text is kept as is


def test_reference_check_cases():
    attested = {"certificates": [{"certificate": "c1", "reference": "R-1", "judgement": "expired"},
                                 {"certificate": "c2", "reference": None, "judgement": "established"}]}
    assert lb._reference_check("R-1", "i", attested)["certificates"] == [{"certificate": "c1", "judgement": "expired"}]
    assert lb._reference_check("R-2", "i", attested)["check"] == "no certificate with the stated reference"
    assert lb._reference_check("R-1", "i", {"certificates": []})["check"] == "no certificate recorded for the instrument"
    assert lb._reference_check(None, "i", attested)["check"] == "no reference stated"
    assert lb._reference_check("R-1", None, attested)["check"] == "no instrument recorded"


def test_calibration_never_invalidates_discards_or_downgrades_a_measurement(world):
    wm, w, ids = world
    for persp in ("system", "qa", "lab-2"):
        ms = {r["record"]: (m["acceptance"], m["usable"]) for m in wm.measurements(w, "sample-12", "q-mass",
                                                                                     perspective=persp)
              for r in m["records"]}
        assert {k: (v["acceptance"], v["usable"]) for k, v in rows(wm, w, perspective=persp).items()} == ms
    compared = {m["attestation"] for m in wm.compare_measurements(w, "sample-12", "q-mass", T(16))["measurements"]}
    assert ids["late"]["content"] in compared                                    # expired calibration, still compared
    assert rows(wm, w)["m-bo-b7-result"]["usable"] is True                       # disputed calibration, still usable


def test_calibration_writes_leave_measurement_answers_identical(make):
    wm = make()
    ids = lab.build_lab(wm)
    w, mass = ids["world"], ids["mass"]

    def answers():
        return json.dumps([[{k: v for k, v in m.items() if k != "_record"} for m in wm.measurements(w, "sample-12", mass)],
                           {k: v for k, v in wm.compare_measurements(w, "sample-12", mass, T(16)).items()}],
                          sort_keys=True, default=str)
    before = answers()
    wm.install_profile("laboratory")
    wm.add_entity("social-object", "Calibration laboratory", id="cal-lab")
    for b in ("b3", "b7", "b9"):
        lb.register_certificate(wm, f"Certificate {b}", f"CAL-{b}", id=f"cert-{b}")
        wm.accept(lb.calibrate(wm, w, f"cert-{b}", f"balance-{b}", start=T(0, day=1), end=T(9, 30), attester="cal-lab"))
        wm.accept(lb.calibrate(wm, w, f"cert-{b}", f"balance-{b}", start=T(0, day=1), attester="qa", polarity=False))
    assert answers() == before


# ---- interpretations ----------------------------------------------------------------------------------------------------
def test_testimony_and_hypothesis_are_told_apart(world):
    wm, w, ids = world
    M = ids["measurements"]
    found = {(i["attester"], i["roles"]["class"][0]): i for rec in (M["ana-b9-35C"]["result"], M["lab2"]["result"],
                                                                     M["bo-b7-k3"]["result"])
             for i in lb.interpretations(wm, w, rec, T(16)) if i["type"] == "classified-as"}
    ana, lab2, bo = found[("ana", "hydrated")], found[("lab-2", "anhydrous")], found[("bo", "hydrated")]
    assert (ana["mode"], ana["stance"], ana["acceptance"], ana["supporting"]) == ("hypothesis", "hypothesises",
                                                                                  "accepted", False)
    assert (lab2["mode"], lab2["basis"], lab2["acceptance"], lab2["supporting"]) == ("testimony", "testimony",
                                                                                     "unreviewed", False)
    assert (bo["mode"], bo["acceptance"], bo["supporting"]) == ("testimony", "accepted", True)
    assert all(i["derivation"] == lb.NO_DERIVATION for i in found.values())
    measured = [i for i in lb.interpretations(wm, w, M["ana-b9-35C"]["result"], T(16)) if i["type"] == "has-quality"]
    assert [i["mode"] for i in measured] == ["observation"]                       # the measurement it reports


def test_an_accepted_hypothesis_alone_never_supports_an_answer(world):
    wm, w, ids = world
    # Ana's perspective has only her own hypothesis of "hydrated": kept, never support
    assert wm.holds(w, "classified-as", {"classified": "sample-12", "class": "hydrated"}, T(16),
                    perspective="ana").status == Status.UNKNOWN


def test_competing_interpretations_are_judged_independently(world):
    wm, w, ids = world

    def view(p):
        return {c: wm.holds(w, "classified-as", {"classified": "sample-12", "class": c}, T(16), perspective=p).status
                for c in ("hydrated", "anhydrous")}
    assert view("system") == {"hydrated": Status.ASSERTED, "anhydrous": Status.UNKNOWN}
    assert view("qa") == {"hydrated": Status.ASSERTED, "anhydrous": Status.ASSERTED}      # both, and no dispute
    assert view("lab-2") == {"hydrated": Status.UNKNOWN, "anhydrous": Status.ASSERTED}


def test_interpret_refuses_basis_inference_and_flags_it_where_recorded(make):
    wm = make()
    ids = lab.build_lab(wm)
    w, M = ids["world"], ids["measurements"]
    wm.install_profile("laboratory")
    wm.add_entity("category", "anhydrous", id="anhydrous")
    rec = M["lab2"]["result"]
    before = wm.count("attestation")
    with pytest.raises(ValueError, match="reserved for rule-derived"):
        lb.interpret(wm, w, rec, "classified-as", {"classified": "sample-12", "class": "anhydrous"}, "lab-2",
                     basis="inference")
    assert wm.count("attestation") == before                                     # nothing written
    # Recorded directly (G-1): the core still says INFERRED; the profile report flags the missing derivation
    raw = wm.attest(w, "classified-as", {"classified": "sample-12", "class": "anhydrous"}, until_superseded=True,
                    basis="inference", attester="lab-2", evidence=[lambda tx: rec])
    wm.accept(raw)
    (i,) = [x for x in lb.interpretations(wm, w, rec, T(16)) if x["attestation"] == raw]
    assert i["mode"] == "recorded as inference without derivation structure (G-1)"
    assert i["derivation"] == lb.NO_DERIVATION
    assert i["content_judgement"]["status"] == Status.INFERRED                   # core judgement unchanged (DI-7)


# ---- both query paths ---------------------------------------------------------------------------------------------------
def test_selective_and_full_load_agree(world):
    wm, w, ids = world

    def answers():
        return json.dumps([lb.provenance(wm, w, "s12-b", T(16)), lb.provenance(wm, w, "s12-c", T(16), perspective="bo"),
                           [lb.calibration_status(wm, w, i, t) for i, t in (("balance-b3", T(9)), ("balance-b3", T(15)),
                                                                            ("balance-b7", T(10)))],
                           lb.calibration_status(wm, ids["plan_recal"], "balance-b3", T(15)),
                           lb.measurement_calibration(wm, w, "sample-12", "q-mass", perspective="qa"),
                           lb.interpretations(wm, w, ids["measurements"]["lab2"]["result"], T(16))],
                          sort_keys=True, default=str)
    wm.selective = True
    selective = answers()
    wm.selective = False
    assert answers() == selective
