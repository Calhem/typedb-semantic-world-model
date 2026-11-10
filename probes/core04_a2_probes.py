"""LABS-1.007 Stage A2 probe (TypeDB 3.14.1): can a recursive TypeQL function list the frames reachable from a frame
through frame-transform facts in either direction, and does it terminate when the frame graph has a cycle?
Throwaway database wm-a2-probe, deleted afterwards.

    uv run python -I probes/core04_a2_probes.py > probes/core04_a2_probes.out.json
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from typedb.driver import TransactionType as T  # noqa: E402

from worldmodel import PHYSICAL_MODULES, WorldModel  # noqa: E402

FUN = """define
fun frames_linked($f: spatial-frame, $w: world) -> { spatial-frame }:
  match
    { $c1 isa frame-transform (parent: $f, child: $g); attestation (content: $c1, context: $w); } or
    { $c2 isa frame-transform (child: $f, parent: $g); attestation (content: $c2, context: $w); } or
    { $c3 isa frame-transform (parent: $f, child: $m3); attestation (content: $c3, context: $w);
      let $g in frames_linked($m3, $w); } or
    { $c4 isa frame-transform (child: $f, parent: $m4); attestation (content: $c4, context: $w);
      let $g in frames_linked($m4, $w); };
  return { $g };"""

out = {}
wm = WorldModel.create("wm-a2-probe", modules=PHYSICAL_MODULES, replace=True)
try:
    w = wm.create_world("actual", id="actual")
    for f in "ABCDE":
        wm.add_entity("spatial-frame", f, id=f)
    for p, c in (("A", "B"), ("B", "C"), ("C", "D")):
        wm.relate_frames(w, p, c, (1, 0, 0), until_superseded=True)
    try:
        with wm.driver.transaction(wm.database, T.SCHEMA) as tx:
            tx.query(FUN).resolve()
            tx.commit()
        out["P1 define a recursive two-direction reachability function"] = "accepted"
    except Exception as e:  # noqa: BLE001
        out["P1 define a recursive two-direction reachability function"] = "rejected: " + " ".join(str(e).split())[:400]

    def reach(start):
        s = time.perf_counter()
        with wm.driver.transaction(wm.database, T.READ) as tx:
            rows = list(tx.query(f'match $f isa spatial-frame, has wm-id "{start}"; $w isa world, has wm-id "actual"; '
                                 f'let $g in frames_linked($f, $w); $g has wm-id $id;').resolve().as_concept_rows())
        return sorted({r.get("id").get_value() for r in rows}), round((time.perf_counter() - s) * 1000, 1)

    if out["P1 define a recursive two-direction reachability function"] != "accepted":
        raise SystemExit(print(json.dumps(out, indent=1)))
    out["P2 chain A-B-C-D, from B"] = reach("B")
    wm.relate_frames(w, "D", "A", (0, 1, 0), until_superseded=True)          # close a cycle A-B-C-D-A
    out["P3 after closing a cycle, from B (terminates?)"] = reach("B")
    out["P4 isolated frame E"] = reach("E")
finally:
    wm.driver.databases.get("wm-a2-probe").delete()
print(json.dumps(out, indent=1))
