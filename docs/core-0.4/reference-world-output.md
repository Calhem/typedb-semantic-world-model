# Reference world in database 'wm-reference-gearbox', world 'actual'

## Composition of gbx-100 at 2026-11-03 12:00 (before the bearing replacement)
- gbx-100 (Gearbox GBX-100)
  - bearing-2 (Bearing 2)
  - bolt-1 (Cover bolt 1)
  - bolt-2 (Cover bolt 2)
  - bolt-3 (Cover bolt 3)
  - bolt-4 (Cover bolt 4)
  - cover (Cover)
  - gasket (Cover gasket)
  - gear-out (Gear, 54 teeth)
  - housing (Housing)
  - output-shaft (Output shaft)
  - shaft-asm-in (Input shaft assembly)
    - bearing-1 (Bearing 1)
    - gear-in (Pinion, 18 teeth)
    - input-shaft (Input shaft)

## Composition of gbx-100 at 2026-11-06 12:00 (after it)
- gbx-100 (Gearbox GBX-100)
  - bearing-2 (Bearing 2)
  - bolt-1 (Cover bolt 1)
  - bolt-2 (Cover bolt 2)
  - bolt-3 (Cover bolt 3)
  - bolt-4 (Cover bolt 4)
  - cover (Cover)
  - gasket (Cover gasket)
  - gear-out (Gear, 54 teeth)
  - housing (Housing)
  - output-shaft (Output shaft)
  - shaft-asm-in (Input shaft assembly)
    - bearing-3 (Bearing 3)
    - gear-in (Pinion, 18 teeth)
    - input-shaft (Input shaft)

## Containment (workshop, at AFTER)
- workshop: (nothing located directly)
  - bay-1: bench-1, gbx-100, scale-3 [ASSERTED]
  - store-shelf: bearing-1 [ASSERTED]

## Materials (system perspective, AFTER)
- housing: cast-iron
- cover: aluminium
- gasket: rubber
- input-shaft: steel
- bench-1: steel
- cover, inspector's perspective: magnesium
- cover, plan world 'plan-steel-cover' at the plan time: steel

## Frames (AFTER)
- f-workshop (Workshop frame): anchored to ['workshop']
    positioned in it: bench-1
- f-bench (Bench frame): anchored to ['bench-1']
    in f-workshop: translation (4.0, 2.5, 0.0), rotation (0.707107, 0.0, 0.0, 0.707107) [ASSERTED]
    positioned in it: gbx-100
- f-gearbox (Gearbox frame): anchored to ['gbx-100']
    in f-bench: translation (0.6, 0.4, 0.92), rotation (1.0, 0.0, 0.0, 0.0) [ASSERTED]
    positioned in it: bearing-2, bearing-3, bolt-1, bolt-2, bolt-3, bolt-4, cover, gasket, gear-in, gear-out, housing, input-shaft, output-shaft

## Positions of selected things (AFTER)
- bench-1 in f-workshop: x (3.95, 4.05), y (2.45, 2.55), z (0.0, 0.0), orientation (0.7071067811865476, 0.0, 0.0, 0.7071067811865475) [ASSERTED]
- gbx-100 in f-bench: x (0.6, 0.6), y (0.4, 0.4), z (0.92, 0.92), orientation None [ASSERTED]
- gear-in in f-gearbox: x (0.02, 0.02), y (0.06, 0.06), z (0.08, 0.08), orientation None [ASSERTED]
- bearing-1: no position holds
- bearing-3 in f-gearbox: x (-0.05, -0.05), y (0.06, 0.06), z (0.08, 0.08), orientation None [ASSERTED]

## Housing mass (AFTER)
- value_at(has-quality, housing): ASSERTED, support ['att:0082c239131e4da5', 'att:0b4ab9276bc04d15']
- range {'lower': 12.35, 'upper': 12.45} [ASSERTED] from ['att:0b4ab9276bc04d15']
- range {'lower': 12.5, 'upper': 12.5} [ASSERTED] from ['att:0082c239131e4da5']

## Raw TypeQL queries against the stored records

### Q1 components of the gearbox (direct part-of contents, any world)
```
match $g isa physical-object, has wm-id "gbx-100";
      $c isa part-of (whole: $g, part: $p); $p has wm-id $pid, has name $pn;
fetch { "part": $pid, "name": $pn };
```
  {"name": "Bearing 2", "part": "bearing-2"}
  {"name": "Cover bolt 1", "part": "bolt-1"}
  {"name": "Cover bolt 2", "part": "bolt-2"}
  {"name": "Cover bolt 3", "part": "bolt-3"}
  {"name": "Cover bolt 4", "part": "bolt-4"}
  {"name": "Cover gasket", "part": "gasket"}
  {"name": "Cover", "part": "cover"}
  {"name": "Gear, 54 teeth", "part": "gear-out"}
  {"name": "Housing", "part": "housing"}
  {"name": "Input shaft assembly", "part": "shaft-asm-in"}
  {"name": "Output shaft", "part": "output-shaft"}

### Q2 transitive parts by the TypeDB function parts_in (actual world)
```
match $g isa physical-object, has wm-id "gbx-100"; $w isa world, has wm-id "actual";
      let $p in parts_in($g, $w); $p has wm-id $pid;
fetch { "part": $pid };
```
  {"part": "bearing-1"}
  {"part": "bearing-2"}
  {"part": "bearing-3"}
  {"part": "bolt-1"}
  {"part": "bolt-2"}
  {"part": "bolt-3"}
  {"part": "bolt-4"}
  {"part": "cover"}
  {"part": "gasket"}
  {"part": "gear-in"}
  {"part": "gear-out"}
  {"part": "housing"}
  {"part": "input-shaft"}
  {"part": "output-shaft"}
  {"part": "shaft-asm-in"}

### Q3 material classification records (every world and source: raw records, not judged answers)
```
match $m isa category, has wm-id "material";
      $k isa classified-as (classified: $mat, class: $m); $mat has wm-id $mid;
      $c isa classified-as (classified: $x, class: $mat); $x isa physical-object, has wm-id $xid;
fetch { "thing": $xid, "material": $mid };
```
  {"material": "aluminium", "thing": "alu-blank-7"}
  {"material": "aluminium", "thing": "cover"}
  {"material": "cast-iron", "thing": "housing"}
  {"material": "magnesium", "thing": "cover"}
  {"material": "rubber", "thing": "gasket"}
  {"material": "steel", "thing": "bearing-1"}
  {"material": "steel", "thing": "bearing-2"}
  {"material": "steel", "thing": "bearing-3"}
  {"material": "steel", "thing": "bench-1"}
  {"material": "steel", "thing": "bolt-1"}
  {"material": "steel", "thing": "bolt-2"}
  {"material": "steel", "thing": "bolt-3"}
  {"material": "steel", "thing": "bolt-4"}
  {"material": "steel", "thing": "cover"}
  {"material": "steel", "thing": "gear-in"}
  {"material": "steel", "thing": "gear-out"}
  {"material": "steel", "thing": "input-shaft"}
  {"material": "steel", "thing": "output-shaft"}

### Q4 positions in the gearbox frame, with the attesting source and interval
```
match $f isa spatial-frame, has wm-id "f-gearbox";
      $c isa positioned-in (positioned: $x, frame: $f), has x-min $x0, has y-min $y0, has z-min $z0;
      $x has wm-id $xid;
      $a isa attestation (content: $c, attester: $who), has valid-from-earliest $from; $who has wm-id $wid;
fetch { "thing": $xid, "x": $x0, "y": $y0, "z": $z0, "attester": $wid, "from": $from, "until": $a.valid-to-earliest };
```
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "bearing-1", "until": "2026-11-05T14:00:00.000000000+00:00", "x": -0.05, "y": 0.06, "z": 0.08}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "bearing-1", "until": null, "x": -0.05, "y": 0.06, "z": 0.08}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "bearing-2", "until": null, "x": -0.05, "y": -0.06, "z": 0.08}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "bolt-1", "until": null, "x": -0.07, "y": 0.09, "z": 0.16}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "bolt-2", "until": null, "x": 0.07, "y": 0.09, "z": 0.16}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "bolt-3", "until": null, "x": -0.07, "y": -0.09, "z": 0.16}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "bolt-4", "until": null, "x": 0.07, "y": -0.09, "z": 0.16}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "cover", "until": null, "x": 0.0, "y": 0.0, "z": 0.16}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "gasket", "until": null, "x": 0.0, "y": 0.0, "z": 0.155}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "gear-in", "until": null, "x": 0.02, "y": 0.06, "z": 0.08}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "gear-out", "until": null, "x": 0.02, "y": -0.06, "z": 0.08}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "housing", "until": null, "x": 0.0, "y": 0.0, "z": 0.0}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "input-shaft", "until": null, "x": 0.0, "y": 0.06, "z": 0.08}
  {"attester": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "thing": "output-shaft", "until": null, "x": 0.0, "y": -0.06, "z": 0.08}
  {"attester": "system", "from": "2026-11-05T14:00:00.000000000+00:00", "thing": "bearing-3", "until": null, "x": -0.05, "y": 0.06, "z": 0.08}

### Q5 frame transforms and anchors
```
match $c isa frame-transform (parent: $p, child: $ch), has tx $tx, has ty $ty, has tz $tz, has qw $qw, has qz $qz;
      $p has wm-id $pid; $ch has wm-id $cid;
fetch { "parent": $pid, "child": $cid, "tx": $tx, "ty": $ty, "tz": $tz, "qw": $qw, "qz": $qz };
```
  {"child": "f-bench", "parent": "f-workshop", "qw": 0.7071067811865476, "qz": 0.7071067811865475, "tx": 4.0, "ty": 2.5, "tz": 0.0}
  {"child": "f-gearbox", "parent": "f-bench", "qw": 1.0, "qz": 0.0, "tx": 0.6, "ty": 0.4, "tz": 0.92}

### Q6 what each frame is anchored to
```
match $c isa anchored-to (frame: $f, anchor: $x); $f has wm-id $fid; $x has wm-id $xid;
fetch { "frame": $fid, "anchor": $xid };
```
  {"anchor": "bench-1", "frame": "f-bench"}
  {"anchor": "gbx-100", "frame": "f-gearbox"}
  {"anchor": "workshop", "frame": "f-workshop"}

### Q7 containment: things located at places that are part of the workshop
```
match $ws isa place, has wm-id "workshop";
      $p1 isa part-of (whole: $ws, part: $pl); $pl has wm-id $plid;
      $c isa located-at (place: $pl, located: $x); $x has wm-id $xid;
fetch { "place": $plid, "thing": $xid };
```
  {"place": "bay-1", "thing": "bench-1"}
  {"place": "bay-1", "thing": "gbx-100"}
  {"place": "bay-1", "thing": "scale-3"}
  {"place": "store-shelf", "thing": "bearing-1"}
  {"place": "store-shelf", "thing": "bearing-3"}

### Q8 the housing's mass: two attestations, a measurement and a design value
```
match $h isa physical-object, has wm-id "housing";
      $c isa has-quality (bearer: $h), has lower $lo, has upper $hi;
      $a isa attestation (content: $c, attester: $who), has basis $b; $who has wm-id $wid;
fetch { "attester": $wid, "basis": $b, "lower": $lo, "upper": $hi };
```
  {"attester": "design-office", "basis": "testimony", "lower": 12.5, "upper": 12.5}
  {"attester": "scale-3", "basis": "observation", "lower": 12.35, "upper": 12.45}
