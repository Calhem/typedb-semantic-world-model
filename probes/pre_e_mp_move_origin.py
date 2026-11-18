"""DI-13 review (LABS-1.047): does `move()` fail when the mover's own records place the thing in two places?

    uv run python -I probes/pre_e_mp_move_origin.py [<checkout>]

`WorldModel.move` records the movement with `origin` = every place where the attester's own location attestations
hold the thing just before the move (a list), while `event:origin` is single-valued (`@card(0..1)`, kept single by
MP-1). One throwaway database (wm-probe-mp-*, deleted afterwards), the core only, the library code unchanged:
1. a thing located at one place, then moved: the control;
2. a thing the same attester locates at two places at once (its own functional conflict), then moved.
Prints what happens in each case. Output: .out.txt beside this file.
"""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve() / "src"))
from worldmodel import WorldModel, connect  # noqa: E402

T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)
driver = connect()
name = f"wm-probe-mp-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(name, driver=driver)
try:
    w = wm.create_world("actual")
    place = {p: wm.add_entity("place", p) for p in ("p1", "p2", "p3")}
    for label, at in (("1 control: located at p1 only", ["p1"]), ("2 located at p1 and at p2 by the same attester",
                                                                     ["p1", "p2"])):
        thing = wm.add_entity("physical-object", f"thing-{label[0]}")
        for p in at:
            wm.attest(w, "located-at", {"located": thing, "place": place[p]}, start=T0, until_superseded=True)
        try:
            wm.move(w, thing, place["p3"], T0 + timedelta(days=1))
            out = "move recorded"
        except Exception as e:                                                      # noqa: BLE001
            out = f"refused: {type(e).__name__}: {' '.join(str(e).split())[:400]}"
        print(f"{label}: {out}")
finally:
    driver.databases.get(name).delete()
