"""Stage E1 evaluation harness (LABS-1.051): the harness's own mechanics, not the benchmark.

The loader writes a fixture through public writers only; every template's adapter answers on both query paths; the
comparison treats lists as sets and players as a set of identity groups; malformed fixtures are refused. Nothing here
reads or checks a benchmark expected answer (those are in benchmark/e1/ and are scored only by evaluation.run).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation import run as R  # noqa: E402
from evaluation.check import TEMPLATES  # noqa: E402
from evaluation.loader import FixtureError, T, drop, load  # noqa: E402

pytestmark = pytest.mark.own_profiles
SMOKE = json.loads((Path(__file__).resolve().parent / "fixtures" / "evaluation-smoke.json").read_text())
PARAMS = {
    "holds": {"world": "w", "type": "located-at", "roles": {"located": "box", "place": "dock"}, "t": "T3"},
    "value_at": {"world": "w", "type": "located-at", "subject": "box", "t": "T7"},
    "exists": {"world": "w", "thing": "box", "t": "T3"},
    "same_thing": {"world": "w", "a": "bea", "b": "cal"},
    "aliases": {"world": "w", "x": "bea"},
    "parts": {"world": "w", "whole": "gbx", "t": "T3"},
    "dependencies": {"world": "w", "dependent": "gbx", "t": "T3"},
    "event_role": {"world": "w", "occurrence": "o1", "role": "official-act:official"},
    "occurrence_status": {"world": "w", "occurrence": "o1", "t": "T5"},
    "office_holders": {"world": "w", "office": "manager", "context": "acme", "t": "T3"},
    "capable": {"world": "w", "holder": "bea", "capability": "sign", "t": "T3", "context": "acme"},
    "authorised": {"world": "w", "holder": "bea", "power": "sign", "scope": "acme", "t": "T3"},
    "calibrated": {"world": "w", "instrument": "scale", "t": "T3"},
    "officials": {"world": "w", "event": "act1"},
    "move": {"world": "w", "thing": "box", "to": "dock", "t": "T9"},
}


@pytest.fixture(scope="module")
def smoke(driver):
    L = load(SMOKE, driver)
    yield L
    drop(L)


def test_times_are_parsed_and_bad_ones_refused():
    assert T("T5") == datetime(2026, 11, 5, 9, tzinfo=timezone.utc)
    assert T("T5h14") == datetime(2026, 11, 5, 14, tzinfo=timezone.utc)
    for bad in ("5", "Tx", "T40"):
        with pytest.raises(FixtureError):
            T(bad)


def test_the_loader_records_every_step_s_attestations_and_marks(smoke):
    assert set(smoke.written) == {s["id"] for s in SMOKE["steps"] if s["op"] not in
                                  ("entity", "world", "mark", "accept", "certificate")}
    assert all(smoke.written.values()) and set(smoke.marks) == {"m1"}
    assert smoke.written["a1"] == ["a1"]                    # attestations keep the fixture's own ids
    names = smoke.evidence_names()
    assert names["a1"] == "a1" and all(names[a] == "ev1" for a in smoke.written["ev1"])


@pytest.mark.parametrize("template", sorted(TEMPLATES))
def test_every_template_answers_on_both_paths(smoke, driver, template):
    assert set(PARAMS) == set(TEMPLATES)
    q = {"id": template, "category": "x", "template": template, "scenario": "smoke", "params": PARAMS[template],
         "expected": {}, "required_evidence": [], "forbidden_evidence": [], "adversarial": False, "difficulty": "x"}
    if template == "move":                                  # a write: its own copy per path
        runs = {}
        for name, selective in R.PATHS:
            L = load(SMOKE, driver)
            try:
                runs[name] = R.ask_one(L, q, R.a_move, selective)
            finally:
                drop(L)
    else:
        runs = R.ask(smoke, q, R.ADAPTERS[template])
    assert all("error" not in r for r in runs.values()), runs
    assert runs["selective"]["answer"] == runs["full"]["answer"]
    fields = TEMPLATES[template][2]
    assert fields <= set(runs["selective"]["answer"])        # every expected field is produced


def test_comparison_uses_sets_and_identity_groups():
    assert R.compare({"values": ["b", "a"]}, {"values": ["a", "b"]}) == []
    assert R.compare({"players": [["b", "a"], ["c"]]}, {"players": [["c"], ["a", "b"]]}) == []
    assert R.compare({"players": [["a"], ["b"]]}, {"players": [["a", "b"]]}) == ["players"]
    assert R.compare({"judgement": "disputed"}, {}) == ["judgement"]
    assert R.category_of("holds", ["status"]) == "wrong-judgement" and R.category_of("parts", ["parts"]) == "wrong-values"


def test_malformed_fixtures_are_refused_and_leave_no_database(driver):
    bad = {"id": "bad", "steps": [{"op": "world", "id": "w"}, {"op": "teleport", "id": "x"}]}
    with pytest.raises(FixtureError, match="unknown op"):
        load(bad, driver)
    with pytest.raises(FixtureError, match="unknown fields"):
        load({"id": "bad2", "steps": [{"op": "world", "id": "w", "colour": "red"}]}, driver)
    assert not [d.name for d in driver.databases.all() if d.name.startswith("wm-eval-bad")]
