"""Core 0.4 Stage D-2 (LABS-1.026): the organisational profile on the Acme reference world.

Single-holder offices (attested constraint, appointments never rejected, conflicts DISPUTED with appointments and
constraint cited, no inference about unmentioned people, denial distinct from absence, an appointment event alone
establishes nothing); four independent concepts (office, capability, authority, action); grantor and reporting
source apart; perspectives, knowledge time, valid time, hypothetical worlds; both query paths; coexistence.
"""

import uuid

import pytest

import profile_fixtures as F
from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel, mechanical as m, organisation as o
from worldmodel.examples import gearbox as g, organisation as ex
from worldmodel.model import READ
from worldmodel import typeql as q
from worldmodel.semantics import Status

T = ex.T
pytestmark = pytest.mark.own_profiles
SITE = ("site-manager", "depot-7")


@pytest.fixture(scope="module")
def ref(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=FakeClock())
    try:
        wm.install_profile("organisation")
        yield wm, ex.build_organisation(wm)
    finally:
        driver.databases.get(name).delete()


@pytest.fixture
def world(ref):
    wm, ids = ref
    wm.selective = True
    yield wm, ids["world"], ids
    wm.selective = True


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


def holders(wm, w, day, *office, **kw):
    v = o.office_holders(wm, w, *(office or SITE), T(day), **kw)
    return v["holders"], v["status"], {a["holder"]: a["judgement"] for a in v["appointments"]}


# ---- installation -------------------------------------------------------------------------------------------------------
def test_installs_alone_with_mechanical_and_with_the_fixtures(make):
    alone = make()
    assert alone.install_profile("organisation") == ["authorisation", "employment", "exclusive-office",
                                                     "office-holding", "official-act", "organisation", "person"]
    everything = make()
    for p in ("mechanical", "organisation", *F.ALL):
        everything.install_profile(p)
    assert set(everything.profiles()) == {"mechanical", "organisation", *(p.name for p in F.ALL)}
    reverse = make()
    for p in ("organisation", "mechanical"):
        reverse.install_profile(p)
    with everything.driver.transaction(everything.database, READ) as tx:
        from worldmodel.profiles import schema_snapshot
        a = schema_snapshot(tx)
    with reverse.driver.transaction(reverse.database, READ) as tx:
        b = schema_snapshot(tx)
    org_and_mech = {"person", "organisation", "employment", "office-holding", "exclusive-office", "authorisation",
                    "official-act", "connected-to", "replacement"}
    assert org_and_mech <= a["types"] and org_and_mech <= b["types"]
    assert not [s for s in everything.slots() if s in ("office-holding", "exclusive-office")]   # no slot: no inference


# ---- single-holder offices ----------------------------------------------------------------------------------------------
def test_sequential_holders(world):
    wm, w, ids = world
    assert holders(wm, w, 5)[:2] == (["bea"], Status.ASSERTED)
    assert holders(wm, w, 12) == (["cal"], Status.ASSERTED, {"bea": "expired", "cal": "established"})


def test_overlapping_accepted_appointments_are_a_cited_conflict(world):
    wm, w, ids = world
    v = o.office_holders(wm, w, *SITE, T(9))
    assert (v["holders"], v["status"]) == (["bea", "cal"], Status.DISPUTED)
    assert v["conflict"]["constraint"]["support"] == [ids["exclusive"]]                     # the constraint cited
    assert {a["holder"]: a["attestations"] for a in v["conflict"]["appointments"]} == \
        {"bea": [ids["bea_site"]], "cal": [ids["cal_site"]]}                               # each appointment cited
    assert {a["holder"]: a["judgement"] for a in v["appointments"]} == {"bea": "established", "cal": "established"}
    (cal,) = o.offices_of(wm, w, "cal", T(9))
    assert (cal["judgement"], cal["status"], bool(cal["conflict"])) == ("established", Status.DISPUTED, True)


def test_without_the_constraint_several_holders_are_no_conflict(world):
    wm, w, ids = world
    v = o.office_holders(wm, w, "safety-officer", "depot-7", T(5))
    assert (v["holders"], v["status"], v["conflict"], v["exclusive"]["holds"]) == \
        (["dan", "eve"], Status.ASSERTED, None, None)


def test_appointments_are_never_rejected_and_keep_their_own_evidence(world):
    wm, w, ids = world
    with wm.driver.transaction(wm.database, READ) as tx:
        stored = q.rows(tx, """match $c isa office-holding (classified: $p); $p has wm-id "cal";
            $w isa world, has wm-id "org"; $a isa attestation (content: $c, context: $w), has wm-id $aid;""")
    assert len(stored) == 2                         # acme's claim and the auditor's denial (the plan adds its own)
    (cal,) = [a for a in o.office_holders(wm, w, *SITE, T(9))["appointments"] if a["holder"] == "cal"]
    assert {(e["attester"], e["polarity"], e["acceptance"]) for e in cal["evidence"]} == \
        {("acme", True, "accepted"), ("auditor", False, "unreviewed")}


def test_explicit_denial_is_not_absence_and_nobody_unmentioned_is_inferred(world):
    wm, w, ids = world
    assert holders(wm, w, 9, perspective="auditor")[2]["cal"] == "denied"                  # its own accepted denial
    assert o.offices_of(wm, w, "eve", T(9)) and \
        not [x for x in o.offices_of(wm, w, "eve", T(9)) if x["office"] == "site-manager"]  # eve: no site claim at all
    assert "eve" not in holders(wm, w, 9)[2]                                               # not listed, not denied
    unmentioned = wm.holds(w, "office-holding", {"classified": "eve", "class": "site-manager", "context": "depot-7"},
                           T(5))
    assert (unmentioned.status, unmentioned.holds) == (Status.NOT_YET_KNOWN, None)        # not INFERRED false


def test_an_unfilled_office_is_unknown_not_vacant(make):
    wm = make()
    wm.install_profile("organisation")
    w = wm.create_world("w", id="w")
    wm.add_entity("organisation", "Unit", id="unit")
    wm.add_entity("social-role", "chair", id="chair")
    o.declare_exclusive(wm, w, "chair", "unit", start=T(1))
    v = o.office_holders(wm, w, "chair", "unit", T(5))
    assert (v["holders"], v["status"], v["appointments"]) == ([], Status.NOT_YET_KNOWN, [])


def test_an_appointment_event_alone_establishes_nothing(world):
    wm, w, ids = world
    assert o.offices_of(wm, w, "fay", T(7)) == []
    (effect,) = wm.effects_of(w, "ev-appoint-fay", T(7))
    assert effect["claim"] == "accepted" and effect["state"]["after"].holds is None       # claimed, not established


def test_perspectives_knowledge_time_and_worlds(world):
    wm, w, ids = world
    assert holders(wm, w, 9, as_of=ids["known_before_cal"])[:2] == (["bea"], Status.ASSERTED)
    assert holders(wm, ids["plan"], 12) == (["dan"], Status.STIPULATED,
                                            {"bea": "expired", "cal": "denied", "dan": "established"})
    assert holders(wm, w, 12)[0] == ["cal"]                                                # the plan stays in its world


def test_a_polarity_dispute_is_listed_not_dropped(make):
    wm = make()
    wm.install_profile("organisation")
    w = wm.create_world("w", id="w")
    wm.add_entity("person", "Bea", id="bea")
    wm.add_entity("organisation", "Unit", id="unit")
    wm.add_entity("organisation", "Auditor", id="aud")
    wm.add_entity("social-role", "chair", id="chair")
    o.appoint(wm, w, "bea", "chair", "unit", start=T(1))
    wm.accept(o.appoint(wm, w, "bea", "chair", "unit", polarity=False, start=T(1), attester="aud"))
    (entry,) = o.offices_of(wm, w, "bea", T(5))
    assert (entry["judgement"], entry["status"]) == ("disputed", Status.DISPUTED)
    assert o.office_holders(wm, w, "chair", "unit", T(5))["status"] == Status.DISPUTED
    assert wm.roles_of(w, "bea", T(5)) == []                       # core roles_of unchanged (DI-1), as instructed


# ---- four independent concepts ------------------------------------------------------------------------------------------
def test_authority_capability_office_and_action_are_independent(world):
    wm, w, ids = world
    def auth(p):
        return o.authorised(wm, w, p, "can-sign-off", "depot-7", T(5))["judgement"]

    def able(p):
        return wm.capable(w, p, "can-sign-off", T(5), "depot-7")["judgement"]
    assert (auth("dan"), able("dan")) == ("established", "not established")               # authority, no capability
    assert (auth("eve"), able("eve")) == ("not established", "established")               # capability, no authority
    assert holders(wm, w, 5)[0] == ["bea"] and auth("bea") == "established"                # office and authority ...
    assert o.authorised(wm, w, "cal", "can-sign-off", "depot-7", T(12))["judgement"] == "not established"  # ... apart
    assert holders(wm, w, 5, "safety-officer", "depot-7")[0] == ["dan", "eve"]             # an office gives no power


def test_grantor_and_reporting_source_are_independent(world):
    wm, w, ids = world
    a = o.authorised(wm, w, "bea", "can-sign-off", "depot-7", T(5))
    (grant,) = a["grants"]
    assert (grant["grantor"], grant["reported_by"]) == ("acme", ["hr"])
    assert a["grantor_entitlement"] == "not assessed"
    acme = o.authorised(wm, w, "acme", "can-sign-off", "depot-7", T(5))
    assert (acme["judgement"], acme["status"]) == ("not established", Status.NOT_YET_KNOWN)   # nothing inferred
    assert o.authorised(wm, w, "bea", "can-sign-off", "acme", T(5))["judgement"] == "not established"  # exact scope
    assert o.authorised(wm, w, "bea", "can-sign-off", "acme", T(5))["only_in"] == ["depot-7"]


def test_acts_in_office_report_without_concluding(world):
    wm, w, ids = world
    bea = o.official_act(wm, w, "ev-bea-signs", power="can-sign-off")
    assert (bea["account"], bea["occurrences"], bea["office_held"]["judgement"], bea["authority"]["judgement"],
            bea["capability"]["judgement"]) == ("accepted", [], "established", "established", "not established")
    cal = o.official_act(wm, w, "ev-cal-signs", power="can-sign-off")
    assert cal["occurrences"] == [{"occurrence": "o-signoff-9", "status": "not established"}]
    assert (cal["office_held"]["status"], cal["authority"]["judgement"]) == (Status.DISPUTED, "not established")
    unaccepted = o.official_act(wm, w, "ev-cal-signs", power="can-sign-off", perspective="auditor")
    assert (unaccepted["account"], unaccepted["office_held"], unaccepted["authority"]) == ("not accepted", None, None)


def test_employment_and_membership(world):
    wm, w, ids = world
    assert [(e["employee"], e["judgement"]) for e in o.employment(wm, w, "acme", T(5))] == \
        [("bea", "established"), ("cal", "established"), ("dan", "established"), ("eve", "established")]
    assert [(e["employer"], e["judgement"]) for e in o.employment(wm, w, "eve", T(25))] == [("acme", "expired")]
    assert o.employment(wm, w, "fay", T(5)) == []
    assert wm.holds(w, "member-of", {"member": "bea", "group": "depot-7"}, T(5)).holds is True


# ---- cross-domain and query paths ---------------------------------------------------------------------------------------
def test_profiles_compose_in_one_database(make):
    wm = make()
    for p in ("mechanical", "organisation"):
        wm.install_profile(p)
    gids = g.extend_mechanical(wm, g.extend_qualities_agency(wm, g.extend_causality(
        wm, g.extend_dynamics(wm, g.extend_spatial(wm, g.build(wm))))))         # the full gearbox chain first ...
    ids = ex.build_organisation(wm)                                             # ... then Acme, sharing vocabulary
    assert holders(wm, ids["world"], 9)[1] == Status.DISPUTED
    assert m.replacement(wm, gids["world"], "ev-cmms-replacement", g.AFTER)["account"] == "accepted"
    assert wm.direct_dependencies(gids["world"], "test-rig", g.AFTER)[0]["kind"] == "dependency:control"
    assert wm.capable(gids["world"], "inspector", "can-sign-off", g.T1)["judgement"] == "established"   # shared id
    assert o.authorised(wm, ids["world"], "bea", "can-sign-off", "depot-7", T(5))["judgement"] == "established"


def test_selective_and_full_load_agree(world):
    wm, w, ids = world

    def answers():
        return [o.office_holders(wm, w, *SITE, T(d), perspective=p) for d in (5, 9, 12) for p in ("system", "auditor")] + \
               [o.offices_of(wm, w, x, T(9)) for x in ("bea", "cal", "eve", "fay")] + \
               [o.authorised(wm, w, x, "can-sign-off", "depot-7", T(5)) for x in ("bea", "dan", "eve", "acme")] + \
               [o.official_act(wm, w, e, power="can-sign-off") for e in ("ev-bea-signs", "ev-cal-signs")] + \
               [o.employment(wm, w, "acme", T(5)), o.office_holders(wm, ids["plan"], *SITE, T(12))]
    wm.selective = True
    a = answers()
    wm.selective = False
    assert answers() == a
