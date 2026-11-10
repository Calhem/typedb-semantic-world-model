"""LABS-1.008: complete, bounded frame traversal and the orientation comparison policy.

Part 1 exercises the resolver on synthetic frame graphs (no database, so graphs can be large): long chains, disconnected
graphs, cycles with valid and with disagreeing paths, a disagreement off the source-target route, and resource limits
(a truncated search is never a silent "no chain"). Part 2 uses TypeDB: orientation comparison by angular separation
(opposite-sign quaternions, small and material differences), overlapping non-identical ranges, chains longer than
eight hops, and selective/full-load equivalence.
"""

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from conftest import FakeClock
from worldmodel import PHYSICAL_MODULES, WorldModel
from worldmodel.physical import PhysicalMixin, yaw
from worldmodel.semantics import Status
from worldmodel.spatial import Transform, angular_separation, params_compatible, qmul, same_rotation

R = PhysicalMixin()          # the resolver needs no database
T0 = datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc)
T = T0 + timedelta(hours=2)


def edge(parent, child, t=(1.0, 0.0, 0.0), q=(1.0, 0.0, 0.0, 0.0), support=None, disputed=False):
    return {"parent": parent, "child": child, "transform": Transform(q, t),
            "support": [support or f"att:{parent}-{child}"], "disputed": disputed}


def chain_edges(n, step=(1.0, 0.0, 0.0), turn=0.0):
    return [edge(f"F{i}", f"F{i + 1}", step, yaw(turn)) for i in range(n)]


def composed(n, step=(1.0, 0.0, 0.0), turn=0.0):
    total = Transform()
    for _ in range(n):
        total = total.then(Transform(yaw(turn), step))
    return total


# ---- part 1: traversal semantics --------------------------------------------------------------------------------
def test_a_valid_chain_longer_than_eight_hops_is_resolved():
    edges = chain_edges(12, turn=math.radians(10))
    r = R._resolve(edges, "F12", "F0")
    assert r["status"] == Status.INFERRED and r["search"]["hops"] == 12 and r["search"]["complete"]
    assert r["transform"].close_to(composed(12, turn=math.radians(10)))
    back = R._resolve(edges, "F0", "F12")
    assert back["transform"].then(r["transform"]).close_to(Transform())
    assert [s["direction"] for s in back["chain"]] == ["inverse"] * 12


def test_a_disconnected_graph_is_a_completed_search_with_no_chain():
    edges = chain_edges(3) + [edge("G0", "G1"), edge("G1", "G2")]
    r = R._resolve(edges, "F0", "G2")
    assert (r["status"], r["transform"]) == (Status.UNKNOWN, None)
    assert r["search"]["complete"] and not r["search"]["truncated"] and r["search"]["frames_reached"] == 4
    assert r["reason"] == "no frame chain from F0 to G2"


def test_cycles_with_valid_paths_terminate_and_are_verified():
    # a hexagon of frames, each turned 60 degrees and 1 m along its own x: it closes exactly; plus two chords
    ring = [edge(f"H{i}", f"H{(i + 1) % 6}", (1.0, 0.0, 0.0), yaw(math.pi / 3)) for i in range(5)]
    h5 = composed(5, turn=math.pi / 3)                                  # H5 in H0
    ring.append(edge("H5", "H0", *_tq(h5.inverse())))                   # H0 in H5: consistent by construction
    chords = [edge("H0", "H3", *_tq(composed(3, turn=math.pi / 3))), edge("H1", "H4", *_tq(composed(3, turn=math.pi / 3)))]
    r = R._resolve(ring + chords, "H4", "H0")
    assert r["status"] == Status.INFERRED and r["search"]["cycle"] and r["search"]["verified"]
    assert r["search"]["relevant_edges"] == 8 and r["search"]["inconsistent"] == []
    expected = composed(4, turn=math.pi / 3)                            # H4 in H0
    assert r["transform"].close_to(expected)


def _tq(transform):
    return transform.t, transform.q


def test_disagreeing_paths_beyond_eight_hops_are_disputed_and_none_is_chosen():
    long = chain_edges(10)                                              # F0 ... F10, 10 m along x
    shortcut = edge("F0", "F10", (10.25, 0.0, 0.0))                     # disagrees by 0.25 m
    r = R._resolve(long + [shortcut], "F10", "F0")
    assert (r["status"], r["transform"]) == (Status.DISPUTED, None)
    assert r["search"]["inconsistent"] and r["search"]["inconsistent"][0]["translation_gap_m"] == pytest.approx(0.25)
    ok = R._resolve(long + [edge("F0", "F10", (10.0, 0.0, 0.0))], "F10", "F0")
    assert ok["status"] == Status.INFERRED and ok["frames"] == ["F10", "F0"]          # shortest chain, verified


def test_a_disagreement_off_the_route_does_not_dispute_the_answer():
    route = chain_edges(3)                                              # F0 - F1 - F2 - F3
    side = [edge("F1", "S1"), edge("S1", "S2"), edge("F1", "S2", (5.0, 0.0, 0.0))]   # inconsistent triangle at F1
    r = R._resolve(route + side, "F3", "F0")
    assert r["status"] == Status.INFERRED and r["search"]["relevant_edges"] == 3 and r["search"]["verified"]
    assert R._resolve(route + side, "S2", "F0")["status"] == Status.DISPUTED          # but it does for S2


def test_a_resource_limit_is_reported_never_a_silent_no_chain():
    edges = chain_edges(12)
    cut = R._resolve(edges, "F0", "F12", limit=5)
    assert cut["status"] == Status.UNKNOWN and cut["search"]["truncated"] and not cut["search"]["complete"]
    assert cut["reason"].startswith("search truncated after 5 edge examinations (limit 5)")
    full = R._resolve(edges, "F0", "F12", limit=1000)
    assert full["status"] == Status.INFERRED and full["search"]["complete"]
    # reached before the limit, but other chains not checked: answered from the shortest chain, marked unverified
    star = [edge("hub", f"leaf{i}") for i in range(20)] + [edge("hub", "goal")]
    full = R._resolve(star, "hub", "goal")
    assert full["search"]["verified"] and full["status"] == Status.INFERRED
    tiny = R._resolve(star, "goal", "hub", limit=1)
    assert tiny["status"] == Status.UNKNOWN and tiny["search"]["truncated"] and not tiny["search"]["verified"]
    assert tiny["transform"] is not None            # an unverified candidate only (LABS-1.009)
    assert tiny["reason"] == "verification incomplete: search truncated, other chains were not checked for agreement"


def test_a_disputed_transform_on_any_route_disputes_the_answer():
    edges = chain_edges(2) + [edge("F0", "F2", (2.0, 0.0, 0.0), disputed=True)]
    assert R._resolve(edges, "F2", "F0")["status"] == Status.DISPUTED


# ---- orientation policy (pure) ------------------------------------------------------------------------------------
def test_angular_separation_policy():
    q = qmul(yaw(0.4), (math.cos(0.15), 0.0, math.sin(0.15), 0.0))
    assert angular_separation(q, tuple(-c for c in q)) == pytest.approx(0.0, abs=1e-12)      # opposite signs
    assert angular_separation(yaw(0.0), yaw(1e-7)) == pytest.approx(1e-7, rel=1e-6)          # tiny angles, accurately
    assert angular_separation(yaw(0.0), yaw(math.pi / 6)) == pytest.approx(math.pi / 6)
    assert not same_rotation(yaw(0.0), yaw(5e-5))       # the old 1-|dot| rule accepted up to 8.9e-5 rad silently
    assert same_rotation(yaw(0.0), yaw(5e-5), tol=1e-4)
    a = dict(zip(("qw", "qx", "qy", "qz"), yaw(0.0)))
    b = dict(zip(("qw", "qx", "qy", "qz"), yaw(2e-6)))
    assert not params_compatible(a, b) and params_compatible(a, b, angle_tol=1e-5)


# ---- part 2: in TypeDB --------------------------------------------------------------------------------------------
@pytest.fixture
def space(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=PHYSICAL_MODULES, clock=FakeClock())
    try:
        w = wm.create_world("actual", id="actual")
        for i in range(13):
            wm.add_entity("spatial-frame", f"frame {i}", id=f"F{i}")
        for n in ("box", "cam", "imu"):
            wm.add_entity("physical-object", n, id=n)
        yield wm, w
    finally:
        driver.databases.get(name).delete()


def claim(wm, w, frame, x, q=None, attester="system", accept=True):
    a = wm.position(w, "box", frame, x, (0.0, 0.0), (0.0, 0.0), orientation=q, start=T0, until_superseded=True,
                    attester=attester)
    if accept and attester != "system":
        wm.accept(a)
    return a


def test_opposite_sign_quaternions_are_the_same_orientation(space):
    wm, w = space
    q = yaw(0.8)
    claim(wm, w, "F0", (1.0, 1.1), q)
    claim(wm, w, "F0", (1.05, 1.2), tuple(-c for c in q), attester="cam")
    a = wm.where(w, "box", "F0", T)
    assert (a["status"], a["judgement"], a["conflict_details"]) == (Status.ASSERTED, "compatible", [])
    assert wm.holds(w, "positioned-in", {"positioned": "box", "frame": "F0"}, T).status != Status.DISPUTED


def test_small_angular_differences_follow_the_stated_policy(space):
    wm, w = space
    claim(wm, w, "F0", (1.0, 1.1), yaw(0.5))
    claim(wm, w, "F0", (1.0, 1.1), yaw(0.5 + 2e-6), attester="imu")
    strict = wm.where(w, "box", "F0", T)
    assert strict["status"] == Status.DISPUTED
    (d,) = strict["conflict_details"]
    assert d["kind"] == "orientations differ" and d["separation_rad"] == pytest.approx(2e-6, rel=1e-3)
    assert d["tolerance_rad"] == 1e-9
    lenient = wm.where(w, "box", "F0", T, angle_tolerance=1e-5)           # e.g. the IMU's stated accuracy
    assert (lenient["status"], lenient["judgement"], lenient["angle_tolerance"]) == (Status.ASSERTED, "compatible", 1e-5)
    assert len(lenient["candidates"]) == 2                                # kept apart, not averaged


def test_materially_conflicting_orientations_are_disputed(space):
    wm, w = space
    claim(wm, w, "F0", (1.0, 1.1), yaw(0.0))
    claim(wm, w, "F0", (1.0, 1.1), yaw(math.pi / 6), attester="cam")
    a = wm.where(w, "box", "F0", T, angle_tolerance=0.01)
    assert a["status"] == Status.DISPUTED
    assert a["conflict_details"][0]["separation_rad"] == pytest.approx(math.pi / 6)
    assert wm.holds(w, "positioned-in", {"positioned": "box", "frame": "F0"}, T).status == Status.DISPUTED


def test_overlapping_but_not_identical_ranges_stay_separate_claims(space):
    wm, w = space
    mine = claim(wm, w, "F0", (1.0, 1.3))
    cams = claim(wm, w, "F0", (1.2, 1.6), attester="cam")
    a = wm.where(w, "box", "F0", T)
    assert (a["status"], a["judgement"]) == (Status.ASSERTED, "compatible")
    assert sorted((c["x"], tuple(c["position_support"])) for c in a["candidates"]) == \
        [((1.0, 1.3), (mine,)), ((1.2, 1.6), (cams,))]                    # each with its own provenance


def test_a_twelve_hop_chain_in_typedb_and_query_path_equivalence(space):
    wm, w = space
    for i in range(12):
        wm.relate_frames(w, f"F{i}", f"F{i + 1}", (1.0, 0.0, 0.0), yaw(math.radians(10)), start=T0,
                         until_superseded=True)
    claim(wm, w, "F12", (0.0, 0.1), yaw(0.3))
    claim(wm, w, "F0", (-50.0, -49.0), attester="cam")                    # far away: a conflict across 12 hops

    def ask():
        return [wm.where(w, "box", "F0", T), wm.where(w, "box", "F6", T), wm.transform_between(w, "F12", "F0", T),
                wm.transform_between(w, "F0", "F12", T, limit=4)]

    wm.selective = True
    selective = ask()
    wm.selective = False
    full = ask()
    wm.selective = True
    assert full == selective
    a, mid, r, cut = selective
    assert r["search"]["hops"] == 12 and r["transform"].close_to(composed(12, turn=math.radians(10)))
    assert a["status"] == Status.DISPUTED and a["conflicts"] == [(0, 1)]
    assert len(mid["candidates"]) == 2 and mid["status"] == Status.DISPUTED
    assert cut["status"] == Status.UNKNOWN and cut["search"]["truncated"]
    assert wm.frames_linked_in_database(w, "F0") == sorted(f"F{i}" for i in range(1, 13))
