"""Core 0.4 Stage C2 (LABS-1.016, LABS-1.018): capabilities, contextual roles and agency, in two domains.

Agency is a contextual classification (the category `agent`), not a type. A capability does not establish an action;
participation does not establish a capability; roles are contextual; an accepted account of an action does not
establish that it occurred. Laboratory (extend_lab_agency) and gearbox workshop (extend_qualities_agency).
"""

import uuid

import pytest

from conftest import FakeClock
from worldmodel import QUALITY_MODULES, WorldModel
from worldmodel.examples import gearbox, lab
from worldmodel.semantics import Status

T = lab.T


@pytest.fixture(scope="module")
def lab_ref(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=QUALITY_MODULES, clock=FakeClock())
    try:
        yield wm, lab.extend_lab_agency(wm, lab.build_lab(wm))
    finally:
        driver.databases.get(name).delete()


@pytest.fixture(scope="module")
def shop_ref(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=QUALITY_MODULES, clock=FakeClock())
    try:
        ids = gearbox.build(wm)
        gearbox.extend_dynamics(wm, ids)
        yield wm, gearbox.extend_qualities_agency(wm, ids)
    finally:
        driver.databases.get(name).delete()


@pytest.fixture
def fresh_lab(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=QUALITY_MODULES, clock=FakeClock())
    try:
        ids = lab.extend_lab_agency(wm, lab.build_lab(wm))
        yield wm, ids["world"], ids
    finally:
        driver.databases.get(name).delete()


@pytest.fixture
def lab_world(lab_ref):
    wm, ids = lab_ref
    wm.selective = True
    yield wm, ids["world"], ids
    wm.selective = True


@pytest.fixture
def shop(shop_ref):
    wm, ids = shop_ref
    wm.selective = True
    yield wm, ids["world"], ids
    wm.selective = True


# ---- capabilities are contextual and timed ---------------------------------------------------------------------------
def test_a_contextual_capability_applies_only_in_its_context(lab_world):
    wm, w, ids = lab_world
    in_lab = wm.capable(w, "ana", "can-weigh", T(9), context="lab-1")
    assert (in_lab["holds"], in_lab["status"]) == (True, Status.ASSERTED)
    elsewhere = wm.capable(w, "ana", "can-weigh", T(9), context="lab-2")
    assert (elsewhere["holds"], elsewhere["only_in"]) == (None, ["lab-1"])     # not denied: just not held there
    assert wm.capable(w, "ana", "can-weigh", T(9))["holds"] is None             # no general holding


def test_a_capability_can_lapse(lab_world):
    wm, w, ids = lab_world
    assert wm.capable(w, "bo", "can-weigh", T(11), context="lab-1")["holds"] is True
    after = wm.capable(w, "bo", "can-weigh", T(13), context="lab-1")
    assert (after["holds"], after["status"]) == (False, Status.ASSERTED)        # ended, as holds() treats it ...
    assert [h["judgement"] for h in after["applicable"]] == ["expired"]          # ... not denied by anyone
    before = wm.capable(w, "bo", "can-weigh", T(6), context="lab-1")
    assert before["holds"] is None and [h["judgement"] for h in before["applicable"]] == ["not yet effective"]


def test_a_general_capability_applies_everywhere_and_needs_no_agency(lab_world):
    wm, w, ids = lab_world
    for ctx in (None, "lab-1", "lab-2"):
        assert wm.capable(w, "balance-b3", "can-measure-mass", T(9), context=ctx)["holds"] is True
    assert wm.is_agent(w, "balance-b3", T(9))["holds"] is None                  # a capability, no agency


def test_the_same_semantics_in_the_workshop(shop):
    wm, w, ids = shop
    at = gearbox.REPLACEMENT[0]
    assert wm.capable(w, "technician", "can-replace-bearing", at, context="workshop")["holds"] is True
    assert wm.capable(w, "technician", "can-replace-bearing", at)["only_in"] == ["workshop"]
    assert wm.capable(w, "inspector", "can-sign-off", at, context="bay-1")["holds"] is True     # general
    assert wm.capable(w, "bearing-press", "can-press-bearing", at)["holds"] is True
    assert wm.is_agent(w, "bearing-press", at)["holds"] is None


def test_capability_reporting_distinguishes_five_cases(fresh_lab):
    """LABS-1.019: explicit denial, expired, not yet effective, no established capability and disputed are told apart
    by `judgement`, over the existing statuses, with the evidence kept in `applicable`."""
    wm, w, ids = fresh_lab
    wm.add_entity("physical-object", "Cy", id="cy")
    wm.add_entity("physical-object", "Di", id="di")
    wm.add_entity("physical-object", "Ed", id="ed")
    denial = wm.grant(w, "cy", "can-weigh", context="lab-1", polarity=False, start=T(7))      # explicit denial
    wm.grant(w, "di", "can-weigh", context="lab-1", start=T(16))                              # begins later
    grant = wm.grant(w, "ed", "can-weigh", context="lab-1", start=T(7))                       # granted ...
    contra = wm.grant(w, "ed", "can-weigh", context="lab-1", polarity=False, start=T(7), attester="qa")
    wm.accept(contra)                                                                          # ... and denied
    unreviewed = wm.grant(w, "tom", "can-weigh", context="lab-1", start=T(7), attester="qa")  # not accepted
    cases = {"cy": ("denied", False, Status.ASSERTED), "bo": ("expired", False, Status.ASSERTED),
             "di": ("not yet effective", None, Status.UNKNOWN), "tom": ("not established", None, Status.UNKNOWN),
             "ana": ("established", True, Status.ASSERTED), "ed": ("disputed", None, Status.DISPUTED)}
    got = {h: wm.capable(w, h, "can-weigh", T(13), context="lab-1") for h in cases}
    assert {h: (c["judgement"], c["holds"], c["status"]) for h, c in got.items()} == cases
    assert [a["attestation"] for h in got["cy"]["applicable"] for a in h["attestations"]] == [denial]
    assert {a["attestation"] for h in got["ed"]["applicable"] for a in h["attestations"]} == {grant, contra}
    assert [(a["attestation"], a["acceptance"]) for h in got["tom"]["applicable"] for a in h["attestations"]] == \
        [(unreviewed, "unreviewed")]                                                         # evidence preserved
    none = wm.capable(w, "balance-b3", "can-weigh", T(13), context="lab-1")                    # nothing at all
    assert (none["judgement"], none["holds"], none["status"], none["applicable"]) == \
        ("not established", None, Status.NOT_YET_KNOWN, [])
    elsewhere = wm.capable(w, "ana", "can-weigh", T(13), context="lab-2")
    assert (elsewhere["judgement"], elsewhere["only_in"]) == ("not established", ["lab-1"])
    expired_view = wm.capable(w, "bo", "can-weigh", T(11), context="lab-1")
    assert expired_view["judgement"] == "established"                                          # before it expired


# ---- agency is a classification; roles are contextual ------------------------------------------------------------------
def test_agency_is_a_classification_not_a_type(lab_world, shop):
    for wm, w, who, at in ((lab_world[0], lab_world[1], "tom", T(9)), (shop[0], shop[1], "apprentice", gearbox.T1)):
        agent = wm.is_agent(w, who, at)
        assert (agent["holds"], agent["status"]) == (True, Status.ASSERTED)
        assert wm.is_agent(w, who, at.replace(hour=1, day=1))["holds"] is None   # before the grant: not known


def test_roles_are_contextual(lab_world, shop):
    wm, w, ids = lab_world
    assert [(r["role"], r["context"]) for r in wm.roles_of(w, "ana", T(9))] == [("analyst", "lab-1")]
    assert wm.roles_of(w, "tom", T(9)) == []
    wm, w, ids = shop
    assert [(r["role"], r["context"]) for r in wm.roles_of(w, "apprentice", gearbox.T1)] == [("fitter", "workshop")]


def test_a_role_does_not_establish_a_capability(shop):
    wm, w, ids = shop
    assert [r["role"] for r in wm.roles_of(w, "apprentice", gearbox.T1)] == ["fitter"]
    got = wm.capable(w, "apprentice", "can-replace-bearing", gearbox.T1, context="workshop")
    assert (got["holds"], got["status"]) == (None, Status.NOT_YET_KNOWN)


# ---- actions: reported, never concluded ----------------------------------------------------------------------------------
def test_participation_does_not_establish_capability(lab_world):
    wm, w, ids = lab_world
    check = wm.check_action(w, "ev-tom-weighs", capability="can-weigh", context="lab-1")
    (actor,) = check["actors"]
    assert (check["account"], check["classified_action"]) == ("accepted", True)   # the lab log is accepted
    assert actor["agent"]["holds"] is True
    assert (actor["capability"]["holds"], actor["capability"]["status"]) == (None, Status.NOT_YET_KNOWN)


def test_an_unaccepted_account_reports_nothing_about_the_actor(shop):
    wm, w, ids = shop
    check = wm.check_action(w, "ev-apprentice-fits", capability="can-replace-bearing", context="workshop")
    assert (check["account"], check["start"], check["occurrences"]) == ("not accepted", None, [])
    assert check["actors"] == [{"actor": "apprentice", "agent": None, "capability": None}]


def test_an_accepted_account_does_not_establish_occurrence(lab_world):
    wm, w, ids = lab_world
    check = wm.check_action(w, "ev-tom-weighs")
    assert check["account"] == "accepted" and check["occurrences"] == []        # no occurrence is claimed at all


def test_an_action_with_its_occurrence_reported_separately(shop):
    wm, w, ids = shop
    check = wm.check_action(w, "ev-worklog-replacement", capability="can-replace-bearing", context="workshop")
    assert (check["account"], check["classified_action"]) == ("accepted", True)
    assert [o["occurrence"] for o in check["occurrences"]] == ["o-bearing-replacement"]
    occ = wm.occurrence_status(w, "o-bearing-replacement", gearbox.REPLACEMENT[0], details=False)["status"]
    assert check["occurrences"][0]["status"] == occ                              # its own status, not the account's
    (actor,) = check["actors"]
    assert (actor["actor"], actor["agent"]["holds"], actor["capability"]["holds"]) == ("technician", True, True)


def test_a_capability_does_not_establish_an_action(shop):
    wm, w, ids = shop
    assert wm.capable(w, "inspector", "can-sign-off", gearbox.AFTER)["holds"] is True
    assert wm.actions_of(w, "inspector", gearbox.AFTER, gearbox.AFTER.replace(hour=23)) == []


# ---- worlds and perspectives --------------------------------------------------------------------------------------------
def test_hypothetical_grants_stay_in_their_world(lab_world, shop):
    wm, w, ids = lab_world
    assert wm.capable(ids["plan_tom"], "tom", "can-weigh", T(14), context="lab-1")["holds"] is True
    assert wm.capable(w, "tom", "can-weigh", T(14), context="lab-1")["holds"] is None
    assert wm.capable(ids["plan_tom"], "ana", "can-weigh", T(14), context="lab-1")["holds"] is True   # inherited
    wm, w, ids = shop
    at = gearbox.PLAN_AT.replace(hour=12)
    assert wm.capable(ids["plan_apprentice"], "apprentice", "can-replace-bearing", at, context="workshop")["holds"]
    assert wm.capable(w, "apprentice", "can-replace-bearing", at, context="workshop")["holds"] is None


def test_a_denial_and_a_grant_dispute_per_perspective(fresh_lab):
    wm, w, ids = fresh_lab
    denial = wm.grant(w, "bo", "can-weigh", context="lab-1", polarity=False, start=T(7), end=T(12), attester="qa")
    assert wm.capable(w, "bo", "can-weigh", T(11), context="lab-1")["holds"] is True   # not accepted: no dispute
    wm.accept(denial)
    got = wm.capable(w, "bo", "can-weigh", T(11), context="lab-1")
    assert (got["holds"], got["status"]) == (None, Status.DISPUTED)
    qa = wm.capable(w, "bo", "can-weigh", T(11), context="lab-1", perspective="qa")
    assert qa["holds"] is False                                                  # qa accepts only its own denial


def test_agency_report_is_diagnostic(lab_world):
    wm, w, ids = lab_world
    report = {r["attester"] for r in wm.agency_report(w)}
    assert {"ana", "bo", "tom"}.isdisjoint(report)                               # accepted agents
    assert {"lab-2", "qa"} <= report                                             # sources not classified as agents


def test_selective_and_full_load_agree(lab_world, shop):
    def answers(wm, w, ids, cases):
        return [wm.capable(w, h, c, t, context=x) for h, c, t, x in cases] + \
               [wm.check_action(w, e, capability=c, context=x) for e, c, x in ids["_actions"]]

    for wm, w, ids, cases in ((*lab_world, [("ana", "can-weigh", T(9), "lab-1"), ("bo", "can-weigh", T(13), "lab-1"),
                                            ("tom", "agent", T(9), None)]),
                              (*shop, [("technician", "can-replace-bearing", gearbox.T1, "workshop"),
                                       ("apprentice", "can-replace-bearing", gearbox.T1, "workshop")])):
        ids["_actions"] = [("ev-tom-weighs", "can-weigh", "lab-1")] if "plan_tom" in ids else \
            [("ev-worklog-replacement", "can-replace-bearing", "workshop"), ("ev-apprentice-fits", None, None)]
        wm.selective = True
        a = answers(wm, w, ids, cases)
        wm.selective = False
        assert answers(wm, w, ids, cases) == a
