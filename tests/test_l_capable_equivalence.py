"""LABS-1.026: extracting capable()'s judgement into shared helpers (_holding_label, _combine) changes no answer.

The baseline was written by the code before the refactor (acba95f) over a fixed grid of 1,242 capable() / is_agent()
answers (tests/capable_grid.py: 9 holders x 3 capabilities x 3 contexts x 5 times x 3 perspectives, plus agency, a
knowledge-time view and a hypothetical world), covering all six judgement cases.

Updated once, by approval (LABS-1.038, increment B, DI-5): one answer changes. For the system perspective, Cy's
only applicable content is the system's own accepted denial of can-weigh in lab-1, which begins after the time
asked. It was "not yet effective", the label reserved for an accepted holding that begins after t; it is now "not
established" (the denial says nothing about that time). Every other answer is identical.
"""

import json
import uuid
from pathlib import Path

import capable_grid as G
from conftest import FakeClock
from worldmodel import QUALITY_MODULES, WorldModel

BASELINE = Path(__file__).resolve().parent / "fixtures" / "capable_baseline.json"


def test_capable_answers_match_the_approved_baseline(driver):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    wm = WorldModel.create(name, driver=driver, modules=QUALITY_MODULES, clock=FakeClock())
    try:
        now = json.loads(json.dumps(G.grid(wm, G.build(wm)), sort_keys=True))
    finally:
        driver.databases.get(name).delete()
    before = json.loads(BASELINE.read_text())
    assert len(now) == len(before) == 1242
    assert {r[-1]["judgement"] for r in before} == {"established", "denied", "expired", "not yet effective",
                                                     "disputed", "not established"}
    assert now == before
