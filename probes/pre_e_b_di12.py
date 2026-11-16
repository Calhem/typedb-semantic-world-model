"""DI-12 (registered LABS-1.038, deferred): traversals judge without the perspective's same-as identity.

    uv run python -I probes/pre_e_b_di12.py <checkout> [--db wm-probe-pre-e-b]

1. Reproduction, in a throwaway database (wm-probe-di12-*, deleted afterwards). With `b-alias` accepted as the same
   thing as `bracket`:
   - `parts(gearbox)` misses the bolt attached to the bracket under its other name, although `holds` (which uses
     identity) says the bolt is part of the bracket's whole;
   - an assertion part-of(p, gearbox) and an accepted denial part-of(p-alias, gearbox) are DISPUTED for `holds`, but
     `parts(gearbox)` follows the link as if undisputed;
   Frame chains are not affected: same-as relates particulars only, so two frames (reference systems) can never be
   declared the same (the schema refuses it), and frame-transform links name frames only.
   Each case prints the current behaviour and asserts it, so the probe fails once DI-12 is corrected.
2. Impact estimate on the reference worlds (the kept database of pre_e_b_snapshot.py): the accepted same-as links in
   each world, and how many part-of, depends-on and frame-transform contents name a thing that has another name.
"""

import argparse
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--db", default="wm-probe-pre-e-b")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.semantics import Identity, Status, usable  # noqa: E402


def T(d):
    return datetime(2026, 11, d, 9, tzinfo=timezone.utc)


driver = connect()
name = f"wm-probe-di12-{uuid.uuid4().hex[:8]}"
wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES)
try:
    w = wm.create_world("w", id="w")
    for i in ("gearbox", "bracket", "b-alias", "bolt", "p", "p-alias", "auditor"):
        wm.add_entity("physical-object", i, id=i)
    wm.attest(w, "same-as", {"same": ["bracket", "b-alias"]}, until_superseded=True)
    wm.attest(w, "same-as", {"same": ["p", "p-alias"]}, until_superseded=True)
    wm.attest(w, "part-of", {"part": "bracket", "whole": "gearbox"}, start=T(1), until_superseded=True)
    wm.attest(w, "part-of", {"part": "bolt", "whole": "b-alias"}, start=T(1), until_superseded=True)
    wm.attest(w, "part-of", {"part": "p", "whole": "gearbox"}, start=T(1), until_superseded=True)
    wm.accept(wm.attest(w, "part-of", {"part": "p-alias", "whole": "gearbox"}, polarity=False, start=T(1),
                        until_superseded=True, attester="auditor"))
    parts = wm.parts(w, "gearbox", T(5))
    via_alias = wm.holds(w, "part-of", {"part": "bolt", "whole": "bracket"}, T(5))
    disputed = wm.holds(w, "part-of", {"part": "p", "whole": "gearbox"}, T(5))
    print("DI-12 current (closures):")
    print(f"  parts(gearbox) = {parts}")
    print(f"  holds(part-of(bolt, bracket)) = {via_alias.status.name} {via_alias.holds}   (identity: b-alias = bracket)")
    print(f"  holds(part-of(p, gearbox)) = {disputed.status.name}   (p-alias = p, and its part-of is denied)")
    assert via_alias.holds is True and "bolt" not in parts          # the alias link is not followed
    assert disputed.status == Status.DISPUTED and "p" in parts       # the dispute is not seen by the closure
    print("  every case reproduces as recorded")
finally:
    driver.databases.get(name).delete()

print("\nDI-12 impact on the reference worlds:")
ref = WorldModel(driver, a.db)
with ref._reading() as tx:
    worlds = sorted({q.opt(r, "id") for r in q.rows(tx, "match $w isa world, has wm-id $id;")})
total = 0
for w in worlds:
    atts = ref.visible(w)
    same = [x for x in atts.values() if x.kind == "same-as" and usable(x, "system", None)]
    ident = Identity(same, "system", None)
    aliased = {x for s in same for ids in s.roles.values() for x in ids}
    touched = [x for x in atts.values() if any(ref.is_a(x.ctype, ty) for ty in ("part-of", "depends-on"))
               and aliased & {i for ids in x.roles.values() for i in ids}]
    total += len(touched)
    print(f"  {w}: {len(same)} accepted same-as links; {len(touched)} traversal contents name an aliased thing")
print(f"  total traversal contents affected: {total}")
