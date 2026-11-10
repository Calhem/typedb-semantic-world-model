"""The Stage A1 reference world (LABS-1.006): a two-stage gearbox on a workbench in a workshop bay.

An invented, unbranded concept assembly; dimensions and masses are illustrative, not real specifications. Everything is
written through the ordinary API, so every fact is an attested proposition with a world, an attester, a basis and an
interval. Ids are explicit and stable.

What it exercises:
- identity: every particular has an id, a name and a short description (descriptions are text, not the thing);
- classification: kinds (gearbox, bearing...) and materials as categories; steel, aluminium... are marked as materials;
- composition: part-of with a sub-assembly; constitution (the cover is made from an aluminium blank);
- containment: the workshop contains a bay and a store shelf; the bench and the gearbox are located in the bay;
- frames and positions: workshop, bench and gearbox frames, each anchored to its particular, with stored transforms
  workshop -> bench -> gearbox, and positions (ranges in metres) of the bench, the gearbox and its components;
- measurement vs design: the housing's mass observed by a scale (a range) and stated by the design office (exact);
- time: bearing-1 is replaced by bearing-3 at T1 (part-of, position and location change; history keeps both);
- perspective: an inspector claims the cover is magnesium; the system has not accepted it;
- hypothetical world: a plan in which the cover is steel instead of aluminium.
"""

import math
from datetime import datetime, timezone

from ..physical import yaw

T0 = datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc)      # assembled and placed
T1 = datetime(2026, 11, 5, 14, 0, tzinfo=timezone.utc)     # bearing-1 replaced by bearing-3
BEFORE = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
AFTER = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
PLAN_AT = datetime(2026, 11, 7, 9, 0, tzinfo=timezone.utc)

PLACES = [("workshop", "Workshop W1", "the building's ground-floor workshop"),
          ("bay-1", "Bay 1", "assembly bay in the workshop"),
          ("store-shelf", "Store shelf S2", "spare-parts shelf in the workshop")]
THINGS = [("bench-1", "Workbench 1", "steel-topped assembly bench", "workbench"),
          ("gbx-100", "Gearbox GBX-100", "two-stage spur gearbox, concept assembly", "gearbox"),
          ("shaft-asm-in", "Input shaft assembly", "input shaft with pinion and bearing", "sub-assembly"),
          ("housing", "Housing", "cast housing of GBX-100", "housing-part"),
          ("cover", "Cover", "top cover of GBX-100", "housing-part"),
          ("gasket", "Cover gasket", "gasket between housing and cover", "seal"),
          ("input-shaft", "Input shaft", "20 mm input shaft", "shaft"),
          ("output-shaft", "Output shaft", "30 mm output shaft", "shaft"),
          ("gear-in", "Pinion, 18 teeth", "input pinion", "gear"),
          ("gear-out", "Gear, 54 teeth", "output gear", "gear"),
          ("bearing-1", "Bearing 1", "input shaft bearing, original", "bearing"),
          ("bearing-2", "Bearing 2", "output shaft bearing", "bearing"),
          ("bearing-3", "Bearing 3", "spare bearing, fitted at T1", "bearing"),
          *[(f"bolt-{i}", f"Cover bolt {i}", "M6 cover bolt", "fastener") for i in range(1, 5)],
          ("alu-blank-7", "Aluminium blank 7", "plate the cover was machined from", "stock"),
          ("scale-3", "Scale 3", "bench scale used for weighing", "instrument")]
AGENTS = [("design-office", "Design office"), ("inspector", "Inspector K")]
MATERIALS = ["steel", "cast-iron", "aluminium", "rubber", "magnesium"]
KINDS = sorted({k for *_, k in THINGS})
FRAMES = [("f-workshop", "Workshop frame", "workshop"), ("f-bench", "Bench frame", "bench-1"),
          ("f-gearbox", "Gearbox frame", "gbx-100")]
MADE_OF = {"housing": "cast-iron", "cover": "aluminium", "gasket": "rubber", "input-shaft": "steel",
           "output-shaft": "steel", "gear-in": "steel", "gear-out": "steel", "bearing-1": "steel",
           "bearing-2": "steel", "bearing-3": "steel", "alu-blank-7": "aluminium", "bench-1": "steel",
           **{f"bolt-{i}": "steel" for i in range(1, 5)}}
PARTS = {"gbx-100": ["housing", "cover", "gasket", "shaft-asm-in", "output-shaft", "gear-out", "bearing-2",
                     "bolt-1", "bolt-2", "bolt-3", "bolt-4"],
         "shaft-asm-in": ["input-shaft", "gear-in", "bearing-1"]}
# Component positions in the gearbox frame (metres; exact design positions).
IN_GEARBOX = {"housing": (0.0, 0.0, 0.0), "cover": (0.0, 0.0, 0.16), "gasket": (0.0, 0.0, 0.155),
              "input-shaft": (0.0, 0.06, 0.08), "gear-in": (0.02, 0.06, 0.08), "bearing-1": (-0.05, 0.06, 0.08),
              "output-shaft": (0.0, -0.06, 0.08), "gear-out": (0.02, -0.06, 0.08), "bearing-2": (-0.05, -0.06, 0.08),
              **{f"bolt-{i}": ((-1) ** i * 0.07, (-1) ** (i // 3) * 0.09, 0.16) for i in range(1, 5)}}


def build(wm):
    """Write the reference world into `wm` (a database with PHYSICAL_MODULES). Returns the notable ids."""
    w = wm.create_world("Workshop W1, actual", id="actual")
    for i, n, d in PLACES:
        wm.add_entity("place", n, description=d, id=i)
    for i, n, d, _ in THINGS:
        wm.add_entity("physical-object", n, description=d, id=i)
    for i, n in AGENTS:
        wm.add_entity("social-object", n, id=i)
    for c in ["material", *MATERIALS, *KINDS]:
        wm.add_entity("category", c, id=c)
    wm.add_entity("quality-kind", "mass", id="mass")
    wm.add_entity("unit", "kilogram", id="kg")
    for i, n, _ in FRAMES:
        wm.add_entity("spatial-frame", n, id=i)

    def fact(type, roles, start=T0, **kw):
        return wm.attest(w, type, roles, start=start, until_superseded=True, **kw)

    # containment and classification
    for sub in ("bay-1", "store-shelf"):
        wm.attest(w, "part-of", {"part": sub, "whole": "workshop"}, until_superseded=True)
    for thing in ("bench-1", "gbx-100", "scale-3"):
        fact("located-at", {"located": thing, "place": "bay-1"})
    spare = fact("located-at", {"located": "bearing-3", "place": "store-shelf"})
    taxonomy = [wm.attest(w, "classified-as", {"classified": m, "class": "material"}, until_superseded=True)
                for m in MATERIALS]
    for i, _, _, kind in THINGS:
        fact("classified-as", {"classified": i, "class": kind})
    for thing, m in MADE_OF.items():
        fact("classified-as", {"classified": thing, "class": m})
    # composition
    part = {}
    for whole, parts in PARTS.items():
        for p in parts:
            part[p] = fact("part-of", {"part": p, "whole": whole})
    fact("constitution", {"constituted": "cover", "constituent": "alu-blank-7"})
    # frames: anchors, stored transforms, positions
    for i, _, anchor in FRAMES:
        wm.anchor_frame(w, i, anchor, start=T0, until_superseded=True)
    wm.relate_frames(w, "f-workshop", "f-bench", (4.0, 2.5, 0.0), yaw(math.pi / 2), start=T0, until_superseded=True)
    wm.relate_frames(w, "f-bench", "f-gearbox", (0.60, 0.40, 0.92), start=T0, until_superseded=True)
    wm.position(w, "bench-1", "f-workshop", (3.95, 4.05), (2.45, 2.55), 0.0, yaw(math.pi / 2), start=T0,
                until_superseded=True, basis="observation")                      # tape measure, +-5 cm
    wm.position(w, "gbx-100", "f-bench", 0.60, 0.40, 0.92, start=T0, until_superseded=True)
    pose = {}
    for thing, (x, y, z) in IN_GEARBOX.items():
        pose[thing] = wm.position(w, thing, "f-gearbox", x, y, z, start=T0, until_superseded=True)
    # measurement vs design value
    measured = fact("has-quality", {"bearer": "housing", "quality": "mass", "unit": "kg"},
                    params={"lower": 12.35, "upper": 12.45}, attester="scale-3", basis="observation")
    wm.accept(measured)
    designed = fact("has-quality", {"bearer": "housing", "quality": "mass", "unit": "kg"},
                    params={"lower": 12.5, "upper": 12.5}, attester="design-office", basis="testimony")
    wm.accept(designed)
    # T1: bearing-1 replaced by bearing-3
    wm.end(w, part["bearing-1"], T1, reason="replaced")
    wm.end(w, pose["bearing-1"], T1, reason="removed")
    wm.end(w, spare, T1, reason="fitted")
    fact("part-of", {"part": "bearing-3", "whole": "shaft-asm-in"}, start=T1)
    wm.position(w, "bearing-3", "f-gearbox", *IN_GEARBOX["bearing-1"], start=T1, until_superseded=True)
    fact("located-at", {"located": "bearing-1", "place": "store-shelf"}, start=T1)
    # another source's unaccepted claim
    claim = fact("classified-as", {"classified": "cover", "class": "magnesium"}, attester="inspector")
    for a in taxonomy:                       # the inspector accepts the system's list of materials, nothing else
        wm.accept(a, holder="inspector")
    # a hypothetical design change
    plan = wm.create_world("Plan: steel cover", kind="hypothetical", base=w, branch_at=PLAN_AT, id="plan-steel-cover")
    wm.attest(plan, "classified-as", {"classified": "cover", "class": "steel"}, start=PLAN_AT, until_superseded=True)
    wm.deny(plan, "classified-as", {"classified": "cover", "class": "aluminium"}, start=PLAN_AT, until_superseded=True)
    return {"world": w, "plan": plan, "inspector_claim": claim, "measured_mass": measured, "design_mass": designed}
