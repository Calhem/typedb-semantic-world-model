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
# Stage A2 additions (extend_spatial)
OBSERVED = datetime(2026, 11, 6, 11, 0, tzinfo=timezone.utc)   # camera and tag-reader observations around AFTER
T2 = datetime(2026, 11, 8, 10, 0, tzinfo=timezone.utc)         # the bench is moved and turned
LATER = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
# Stage B additions (extend_dynamics)
INSPECTION = (datetime(2026, 11, 4, 9, 0, tzinfo=timezone.utc), datetime(2026, 11, 4, 9, 30, tzinfo=timezone.utc))
REPLACEMENT = (datetime(2026, 11, 5, 13, 50, tzinfo=timezone.utc), T1)
TEST_RUN = (datetime(2026, 11, 5, 15, 30, tzinfo=timezone.utc), datetime(2026, 11, 5, 16, 0, tzinfo=timezone.utc))
RESTORED = TEST_RUN[1]
REPAIR = (datetime(2026, 11, 5, 13, 0, tzinfo=timezone.utc), RESTORED)
STEPS = {"o-disassembly": (datetime(2026, 11, 5, 13, 0, tzinfo=timezone.utc),
                           datetime(2026, 11, 5, 13, 45, tzinfo=timezone.utc)),
         "o-relubrication": (datetime(2026, 11, 5, 14, 5, tzinfo=timezone.utc),
                             datetime(2026, 11, 5, 14, 20, tzinfo=timezone.utc)),
         "o-reassembly": (datetime(2026, 11, 5, 14, 15, tzinfo=timezone.utc),       # overlaps the relubrication
                          datetime(2026, 11, 5, 15, 15, tzinfo=timezone.utc))}
CAUSAL_PLAN_AT = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)

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


def extend_spatial(wm, ids):
    """Stage A2 additions to the reference world (LABS-1.007): position claims from other sources, an unlinked camera
    frame, a moved bench (the workshop -> bench transform changes at T2) and a plan that moves the bench.
    Returns the notable ids, merged into `ids`."""
    w = ids["world"]
    wm.add_entity("physical-object", "Ceiling camera 2", description="fixed camera over bay 1", id="cam-2")
    wm.add_entity("physical-object", "Tag reader", description="RFID reader at the bay door", id="tag-reader")
    wm.add_entity("spatial-frame", "Camera 2 image frame", id="f-cam-2")
    # cam-2 observes the gearbox in the workshop frame (its own +-5 cm box), accepted by the system
    seen = wm.position(w, "gbx-100", "f-workshop", (3.55, 3.65), (3.05, 3.15), (0.90, 0.94), attester="cam-2",
                       basis="observation", start=OBSERVED, end=datetime(2026, 11, 6, 13, 0, tzinfo=timezone.utc))
    wm.accept(seen)
    # the tag reader puts it 1.5 m away: not accepted by the system
    tag = wm.position(w, "gbx-100", "f-workshop", (5.0, 5.2), (3.0, 3.2), (0.8, 1.0), attester="tag-reader",
                      basis="observation", start=OBSERVED, end=datetime(2026, 11, 6, 13, 0, tzinfo=timezone.utc))
    # cam-2 also reports the pinion in its own image frame, which no transform relates to the others
    pix = wm.position(w, "gear-in", "f-cam-2", (0.41, 0.43), (0.22, 0.24), (2.9, 3.1), attester="cam-2",
                      basis="observation", start=OBSERVED, until_superseded=True)
    wm.accept(pix)
    # T2: the bench is moved to (6.0, 1.0) and no longer turned
    old = [a for a in wm.history(w, "f-bench", type="frame-transform") if a["attester"] == "system"
           and a["roles"]["parent"] == ["f-workshop"]]                       # only workshop -> bench changes
    for a in old:
        wm.end(w, a["attestation"], T2, reason="bench moved")
    bench_pose = [a["attestation"] for a in wm.history(w, "bench-1", type="positioned-in")]
    for a in bench_pose:
        wm.end(w, a, T2, reason="bench moved")
    moved = wm.relate_frames(w, "f-workshop", "f-bench", (6.0, 1.0, 0.0), start=T2, until_superseded=True)
    wm.position(w, "bench-1", "f-workshop", (5.95, 6.05), (0.95, 1.05), 0.0, start=T2, until_superseded=True,
                basis="observation")
    # a plan: the bench at (1.0, 1.0), turned 180 degrees, from the plan time
    plan = wm.create_world("Plan: bench by the door", kind="hypothetical", base=w, branch_at=PLAN_AT,
                           id="plan-move-bench")
    planned = wm.relate_frames(plan, "f-workshop", "f-bench", (1.0, 1.0, 0.0), yaw(math.pi), start=PLAN_AT,
                               until_superseded=True)
    ids.update({"camera_position": seen, "tag_position": tag, "camera_pixel": pix, "moved_transform": moved,
                "bench_plan": plan, "planned_transform": planned})
    return ids


def extend_dynamics(wm, ids):
    """Stage B1 additions (LABS-1.010): the gearbox's condition over time, an inspection that records a fault, the
    bearing replacement as an occurrence with two descriptions and claimed effects, and a test run that restores the
    operational condition. Needs DYNAMICS_MODULES. Returns the notable ids, merged into `ids`."""
    w = ids["world"]
    for i, n in (("technician", "Technician R"), ("vib-meter", "Vibration meter"), ("bearing-press", "Bearing press"),
                 ("test-rig", "Test rig")):
        wm.add_entity("physical-object", n, id=i)
    for c in ("operational", "faulty", "low", "inspection", "replacement", "test", "action", "sign-off"):
        if not wm.find(c):
            wm.add_entity("category", c, id=c)
    for q in ("condition", "vibration"):
        wm.add_entity("quality-kind", q, id=q)
    for o, n in (("o-inspection", "inspection of GBX-100"), ("o-bearing-replacement", "bearing replacement"),
                 ("o-test-run", "test run"), ("o-sign-off", "inspection sign-off")):
        wm.add_entity("occurrence", n, id=o)
    # one condition at a time per thing and quality (data for this world, not a core constraint)
    wm.declare_slot("has-quality", ["bearer", "quality"], "value")
    cond = {"bearer": "gbx-100", "quality": "condition"}
    operational = wm.attest(w, "has-quality", {**cond, "value": "operational"}, start=T0, until_superseded=True)
    # the inspection: the inspector's report, and the fault it records (evidence of the fault, not its cause)
    insp = wm.account(w, {"actor": "inspector", "patient": "gbx-100", "instrument": "vib-meter", "location": "bay-1"},
                      *INSPECTION, kind=["inspection", "action"], occurrence="o-inspection", attester="inspector",
                      id="ev-inspection-report")
    fault = wm.attest(w, "has-quality", {**cond, "value": "faulty"}, start=INSPECTION[1], until_superseded=True,
                      attester="inspector", basis="observation")
    wm.accept(fault)
    wm.end(w, operational, INSPECTION[1], reason="fault recorded by the inspection")
    # the bearing replacement: one occurrence, two descriptions with different details
    log = wm.account(w, {"actor": "technician", "patient": "bearing-3", "instrument": "bearing-press",
                         "location": "bay-1"}, *REPLACEMENT, kind=["replacement", "action"],
                     occurrence="o-bearing-replacement", attester="technician", id="ev-worklog-replacement")
    record = wm.account(w, {"patient": "bearing-1", "location": "bay-1"}, *REPLACEMENT, kind="replacement",
                        occurrence="o-bearing-replacement", id="ev-maintenance-record")
    for a in wm.account_attestations(w, "ev-worklog-replacement", attester="technician"):
        wm.accept(a)                                        # the system accepts the work log, its kinds and its link
    effects = [wm.claim_effect(w, log, "initiates", "part-of", {"part": "bearing-3", "whole": "shaft-asm-in"},
                               attester="technician"),
               wm.claim_effect(w, log, "terminates", "part-of", {"part": "bearing-1", "whole": "shaft-asm-in"},
                               attester="technician")]
    for e in effects:
        wm.accept(e)
    # an asserted effect the system has not accepted (nor the state it claims)
    vib_claim = wm.claim_effect(w, log, "initiates", "has-quality",
                                {"bearer": "gbx-100", "quality": "vibration", "value": "low"}, attester="technician")
    vib_state = wm.attest(w, "has-quality", {"bearer": "gbx-100", "quality": "vibration", "value": "low"},
                          start=REPLACEMENT[1], until_superseded=True, attester="technician", basis="observation")
    known_before_repair = wm._now()        # a transaction time: everything above is recorded, the repair is not
    # the test run restores the operational condition; the inspector signs off and ends the fault
    test = wm.account(w, {"actor": "technician", "patient": "gbx-100", "instrument": "test-rig", "location": "bay-1"},
                      *TEST_RUN, kind=["test", "action"], occurrence="o-test-run", attester="technician", id="ev-test-run")
    restored = wm.attest(w, "has-quality", {**cond, "value": "operational"}, start=RESTORED, until_superseded=True,
                         attester="technician", basis="observation")
    wm.accept(restored)
    restore_claims = [wm.claim_effect(w, test, "initiates", "has-quality", {**cond, "value": "operational"},
                                      attester="technician"),
                      wm.claim_effect(w, test, "terminates", "has-quality", {**cond, "value": "faulty"},
                                      attester="technician")]
    for c in restore_claims:
        wm.accept(c)
    wm.account(w, {"actor": "inspector", "patient": "gbx-100"}, RESTORED, kind="sign-off", occurrence="o-sign-off",
               attester="inspector", id="ev-sign-off")
    signed_off = wm.end(w, fault, RESTORED, reason="signed off after the test run")
    wm.accept(signed_off)                  # the system accepts the inspector's ended restatement (per perspective)
    for ev, by in (("ev-inspection-report", "inspector"), ("ev-sign-off", "inspector"), ("ev-test-run", "technician")):
        for a in wm.account_attestations(w, ev, attester=by):
            wm.accept(a)
    ids.update({"operational_t0": operational, "fault": fault, "fault_signed_off": signed_off,
                "known_before_repair": known_before_repair, "inspection": insp, "worklog": log,
                "maintenance_record": record, "replacement_effects": effects, "vibration_claim": vib_claim,
                "vibration_state": vib_state, "test_run": test, "restored": restored, "restore_claims": restore_claims})
    return ids


def extend_causality(wm, ids):
    """Stage B2 additions (LABS-1.010): the repair as a process of several occurrences, the technician's actions,
    asserted causal claims at the occurrence and the description level, a competing claim that is disputed, a
    rejected one, an unreviewed one, and a hypothetical world with another causal account. After extend_dynamics."""
    w = ids["world"]
    for i, n in (("wrench", "Torque wrench"), ("grease-gun", "Grease gun"), ("cm-1", "Condition monitor 1")):
        wm.add_entity("physical-object", n, id=i)
    wm.add_entity("social-object", "Apprentice J", id="apprentice")
    for c in ("repair", "process", "disassembly", "lubrication", "reassembly"):
        wm.add_entity("category", c, id=c)
    for o, n in (("o-repair", "repair of GBX-100"), ("o-disassembly", "disassembly"),
                 ("o-relubrication", "relubrication"), ("o-reassembly", "reassembly")):
        wm.add_entity("occurrence", n, id=o)

    def tech(roles, span, kind, occurrence, id):
        eid = wm.account(w, roles, *span, kind=kind, occurrence=occurrence, attester="technician", id=id)
        return eid

    tech({"actor": "technician", "patient": "gbx-100", "location": "bay-1"}, REPAIR, ["repair", "process"],
         "o-repair", "ev-repair")
    tech({"actor": "technician", "patient": "gbx-100", "instrument": "wrench"}, STEPS["o-disassembly"],
         ["disassembly", "action"], "o-disassembly", "ev-disassembly")
    tech({"actor": "technician", "patient": "shaft-asm-in", "instrument": "grease-gun"}, STEPS["o-relubrication"],
         ["lubrication", "action"], "o-relubrication", "ev-relubrication")
    tech({"actor": "technician", "patient": "gbx-100", "instrument": "wrench"}, STEPS["o-reassembly"],
         ["reassembly", "action"], "o-reassembly", "ev-reassembly")
    steps = [wm.attest(w, "part-of", {"part": o, "whole": "o-repair"}, until_superseded=True, attester="technician")
             for o in ("o-disassembly", "o-bearing-replacement", "o-relubrication", "o-reassembly", "o-test-run")]
    for e in ("ev-repair", "ev-disassembly", "ev-relubrication", "ev-reassembly"):
        for a in wm.account_attestations(w, e, attester="technician"):
            wm.accept(a)
    for a in steps:
        wm.accept(a)
    # causal claims about the successful test run (asserted by sources; the model infers none)
    claims = {
        "replacement": wm.claim_cause(w, "o-bearing-replacement", "o-test-run", attester="technician",
                                      basis="testimony"),
        "replacement_as_logged": wm.claim_cause(w, "ev-worklog-replacement", "ev-test-run", attester="technician"),
        "relubrication": wm.claim_cause(w, "o-relubrication", "o-test-run", attester="inspector"),
        "relubrication_denied": wm.claim_cause(w, "o-relubrication", "o-test-run", polarity=False, attester="cm-1",
                                               basis="inference"),
        "inspection": wm.claim_cause(w, "o-inspection", "o-test-run", attester="apprentice"),
        "reassembly": wm.claim_cause(w, "o-reassembly", "o-test-run", attester="cm-1", basis="inference"),
    }
    for k in ("replacement", "replacement_as_logged", "relubrication"):
        wm.accept(claims[k])
    known_before_denial = wm._now()
    wm.accept(claims["relubrication_denied"])
    wm.accept(claims["inspection"], "rejected", reason="succession is not causation")
    # a hypothetical account: the plan says relubrication alone would have restored it
    plan = wm.create_world("Plan: relubricate only", kind="hypothetical", base=w, branch_at=CAUSAL_PLAN_AT,
                           id="plan-relubricate-only")
    wm.claim_cause(plan, "o-relubrication", "o-test-run")
    wm.claim_cause(plan, "o-bearing-replacement", "o-test-run", polarity=False)
    # recorded in the base after the plan was made: not part of its snapshot
    late = wm.claim_cause(w, "o-disassembly", "o-bearing-replacement", attester="technician")
    wm.accept(late)
    ids.update({"causal_claims": claims, "known_before_denial": known_before_denial, "causal_plan": plan,
                "late_claim": late, "repair_steps": steps})
    return ids

