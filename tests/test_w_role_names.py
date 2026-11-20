"""Stage E1 reconciliation R2 and R3 (LABS-1.052; docs/stage-e/e1-reconciliation-design.md).

R2: readers take a content type's core role names (inherited ones included) and refuse any other with
UnknownRoleError, naming the valid ones; a profile's stored role name points to its core name. Answers to questions
with valid names are unchanged.
R3: functional exclusivity as World Ontology v0.2 4.4 states it: where a single-valued slot holds another value,
established for the perspective, a content does not hold (`not holding`, INFERRED false), citing the established
value, even when an unreviewed attestation of the content itself exists; a disputed slot decides nothing.
"""

import uuid
from datetime import datetime, timezone

import pytest

from conftest import FakeClock
from worldmodel import CORE_MODULES, UnknownRoleError, WorldModel, organisation as org
from worldmodel.semantics import Status

pytestmark = pytest.mark.own_profiles


def T(day):
    return datetime(2026, 11, day, 9, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def ref(driver):
    wm = WorldModel.create(f"wm-test-{uuid.uuid4().hex[:10]}", driver=driver, modules=CORE_MODULES, clock=FakeClock())
    try:
        wm.install_profile("organisation")
        w = wm.create_world("actual", id="w")
        for p in ("bea", "robot", "hr"):
            wm.add_entity("person", p, id=p)
        wm.add_entity("organisation", "acme", id="acme")
        wm.add_entity("social-role", "manager", id="manager")
        for x in ("parcel", "crate"):
            wm.add_entity("physical-object", x, id=x)
        for pl in ("shelf-a", "shelf-b", "shelf-c", "bay-1", "bay-2"):
            wm.add_entity("place", pl, id=pl)
        org.appoint(wm, w, "bea", "manager", "acme", start=T(1), until_superseded=True, id="appt")
        wm.attest(w, "located-at", {"located": "parcel", "place": "shelf-a"}, start=T(1), until_superseded=True,
                  id="loc-a")
        wm.attest(w, "located-at", {"located": "parcel", "place": "shelf-b"}, start=T(1), until_superseded=True,
                  attester="robot", id="loc-b-robot")                         # unreviewed by the system
        for place, aid in (("bay-1", "crate-1"), ("bay-2", "crate-2")):    # a disputed slot
            wm.attest(w, "located-at", {"located": "crate", "place": place}, start=T(1), until_superseded=True, id=aid)
        wm.attest(w, "located-at", {"located": "crate", "place": "shelf-c"}, start=T(1), until_superseded=True,
                  attester="robot", id="crate-robot")
        yield wm
    finally:
        wm.driver.databases.get(wm.database).delete()


@pytest.fixture(params=[True, False], ids=["selective", "full-load"])
def wm(ref, request):
    ref.selective = request.param
    yield ref
    ref.selective = True


# ---- R2: role names ----------------------------------------------------------------------------------------------------
def test_the_documented_office_holding_roles_answer(wm):
    roles = {"classified": "bea", "class": "manager", "context": "acme"}
    assert wm.holds("w", "office-holding", roles, T(5)).status == Status.ASSERTED
    assert wm.judgement("w", "office-holding", roles, T(5)).judgement.value == "established"
    assert set(wm.role_names("office-holding")) == {"classified", "class", "context"}     # inherited roles


@pytest.mark.parametrize("reader", ["holds", "judgement", "explain"])
def test_role_names_a_type_does_not_have_are_refused(wm, reader):
    """Stage E1 ORG-011: the names the organisation notes used to give answered NOT_YET_KNOWN silently."""
    with pytest.raises(UnknownRoleError) as e:
        getattr(wm, reader)("w", "office-holding", {"holder": "bea", "office": "manager", "context": "acme"}, T(5))
    assert (e.value.type, e.value.unknown, e.value.valid) == ("office-holding", ["holder", "office"],
                                                              ["class", "classified", "context"])
    assert "nothing answered" in str(e.value)


def test_a_profile_s_stored_role_name_points_to_its_core_name(wm):
    with pytest.raises(UnknownRoleError, match="'official' is stored as 'actor'"):
        wm.holds("w", "official-act", {"official": "bea"}, T(5))


def test_functional_readers_check_their_role_names(wm):
    with pytest.raises(UnknownRoleError, match="'thing'"):
        wm.value_at("w", "located-at", "parcel", T(5), key_role="thing", value_role="place")
    with pytest.raises(UnknownRoleError, match="'object'"):
        wm.value_of("w", "located-at", {"object": "parcel"}, T(5))
    assert wm.value_at("w", "located-at", "parcel", T(5), key_role="located", value_role="place").values == ("shelf-a",)


# ---- R3: functional exclusivity ----------------------------------------------------------------------------------------
def test_another_established_value_makes_a_content_not_hold(wm):
    """Stage E1 TEMP-017: v0.2 4.4, 'false, INFERRED by functional exclusivity', also with a pending claim of it."""
    roles = {"located": "parcel", "place": "shelf-b"}
    ans = wm.holds("w", "located-at", roles, T(5))
    assert (ans.status, ans.holds, ans.support) == (Status.INFERRED, False, ("loc-a",))
    assert wm.judgement("w", "located-at", roles, T(5)).judgement.value == "not holding"
    robot = wm.holds("w", "located-at", roles, T(5), perspective="robot")       # the robot's own view: it holds
    assert (robot.status, robot.holds) == (Status.ASSERTED, True)


def test_a_disputed_slot_decides_nothing_about_another_value(wm):
    ans = wm.holds("w", "located-at", {"located": "crate", "place": "shelf-c"}, T(5))
    assert ans.status != Status.INFERRED and ans.holds is None
    assert wm.value_at("w", "located-at", "crate", T(5)).status == Status.DISPUTED
