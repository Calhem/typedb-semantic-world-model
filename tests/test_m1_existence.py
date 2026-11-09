"""Milestone 1 regression requirements, ported to Core 0.3 (from main: tests/test_existence.py, 6 tests).
Uncertain existence is now an existence attestation by another agent that the system has not accepted."""

import pytest

from conftest import T
from worldmodel.semantics import Status


@pytest.fixture
def worlds(wm):
    w = wm.create_world("actual", id="actual")
    wm.add_entity("place", "bench", id="bench")
    wm.add_entity("physical-object", "witness", id="witness")
    return w


def status(answer):
    return answer.status, answer.holds


def test_a_registered_identity_alone_does_not_exist_anywhere(wm, worlds):
    wm.add_entity("physical-object", "widget", id="widget")
    assert status(wm.exists(worlds, "widget", T("10:00"))) == (Status.NOT_YET_KNOWN, None)


def test_creation_and_destruction(wm, worlds):
    vase = wm.create_thing(worlds, "physical-object", "vase", at=T("10:00"), id="vase")
    loc = wm.attest(worlds, "located-at", {"located": vase, "place": "bench"}, start=T("10:00"), until_superseded=True)
    assert status(wm.exists(worlds, vase, T("09:00"))) == (Status.ASSERTED, False)
    assert status(wm.exists(worlds, vase, T("10:30"))) == (Status.ASSERTED, True)
    ended = wm.destroy(worlds, vase, T("11:00"), reason="dropped")
    assert loc in ended and len(ended) == 2
    assert status(wm.exists(worlds, vase, T("11:30"))) == (Status.ASSERTED, False)
    assert wm.value_at(worlds, "located-at", vase, T("11:30")).status == Status.UNKNOWN
    assert wm.value_at(worlds, "located-at", vase, T("10:30")).values == ("bench",)


def test_uncertain_creation_time_and_uncertain_existence(wm, worlds):
    pot = wm.create_thing(worlds, "physical-object", "pot", at=(T("10:00"), T("10:20")), id="pot")
    assert status(wm.exists(worlds, pot, T("09:59"))) == (Status.ASSERTED, False)
    assert wm.exists(worlds, pot, T("10:10")).status == Status.UNKNOWN
    assert status(wm.exists(worlds, pot, T("10:20"))) == (Status.ASSERTED, True)
    wm.add_entity("physical-object", "intruder", id="intruder")
    maybe = wm.declare_existence(worlds, "intruder", start=T("10:00"), attester="witness")
    a = wm.exists(worlds, "intruder", T("10:30"))
    assert a.status == Status.UNKNOWN and a.alternatives == (maybe,)


def test_participation_implies_existence_by_inference(wm, worlds):
    wm.add_entity("physical-object", "crate", id="crate")
    wm.attest(worlds, "located-at", {"located": "crate", "place": "bench"}, start=T("10:00"), until_superseded=True)
    assert status(wm.exists(worlds, "crate", T("10:30"))) == (Status.INFERRED, True)
    assert wm.exists(worlds, "crate", T("09:30")).status == Status.UNKNOWN


def test_hypothetical_things_do_not_leak_into_the_actual_world(wm, worlds):
    h = wm.create_world("what-if", kind="hypothetical", base=worlds, branch_at=T("12:00"))
    robot = wm.create_thing(h, "physical-object", "spare robot", at=T("12:30"), id="spare-robot")
    wm.attest(h, "located-at", {"located": robot, "place": "bench"}, start=T("12:30"), until_superseded=True)
    assert status(wm.exists(h, robot, T("13:00"))) == (Status.STIPULATED, True)
    assert status(wm.exists(worlds, robot, T("13:00"))) == (Status.NOT_YET_KNOWN, None)
    assert wm.find("spare robot") == ["spare-robot"]
    assert wm.find("spare robot", world=worlds) == []
    assert wm.find("spare robot", world=h) == ["spare-robot"]


def test_a_variant_can_destroy_an_inherited_thing_without_touching_the_base(wm, worlds):
    lamp = wm.create_thing(worlds, "physical-object", "lamp", at=T("09:00"), id="lamp")
    h = wm.create_world("what-if", kind="hypothetical", base=worlds, branch_at=T("12:00"))
    wm.destroy(h, lamp, T("12:30"))
    assert status(wm.exists(h, lamp, T("13:00"))) == (Status.STIPULATED, False)
    assert status(wm.exists(worlds, lamp, T("13:00"))) == (Status.ASSERTED, True)
