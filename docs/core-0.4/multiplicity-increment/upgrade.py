import sys, json
sys.path.insert(0, sys.argv[1] + "/src")
from worldmodel import WorldModel
wm = WorldModel.open(sys.argv[2])
before = wm.modules()
steps = {"upgrade_to_event_multiplicity": wm.upgrade_to_event_multiplicity()}
for p in ("organisation", "mechanical", "laboratory"):
    steps[f"upgrade_profile({p})"] = wm.upgrade_profile(p)
again = {"again_module": wm.upgrade_to_event_multiplicity(),
         **{f"again_{p}": wm.upgrade_profile(p) for p in ("organisation", "mechanical", "laboratory")}}
print(json.dumps({"database": sys.argv[2], "before": before, "steps": steps, "idempotent": again,
                  "after": wm.modules()}, indent=1, sort_keys=True))
