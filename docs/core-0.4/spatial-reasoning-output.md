# Spatial reasoning in the reference world (database 'wm-reference-gearbox')

## Part 1: judged answers (WorldModel API)

### How the gearbox frame sits in the workshop frame at 2026-11-06 12:00
`transform_between('actual', 'f-gearbox', 'f-workshop')` -> **INFERRED**: origin at (3.6, 3.1, 0.92), rotated 90 deg about z, via f-gearbox -> f-bench -> f-workshop

### Q1 Where is the gearbox relative to the workshop?
`where('actual', 'gbx-100', 'f-workshop', 2026-11-06 12:00, perspective='system')` -> **ASSERTED**, judgement: compatible
- candidate 0: x 3.600, y 3.100, z 0.920 m [INFERRED], derived (frame-transform/v1) from a position stated in f-bench; position attestation(s) ['att:1a4e23298b224445']
    via f-bench -> f-workshop (forward): t = (4.0, 2.5, 0.0), rotation 90 deg about z; attestation(s) ['att:12b3c56608f249a5']
- candidate 1: x 3.550..3.650, y 3.050..3.150, z 0.900..0.940 m [ASSERTED], stated in this frame; position attestation(s) ['att:57c358929e4d408e']
- unreviewed alternatives (not part of this perspective's answer): ['att:45426553968f4159']

### Q2 Where is the pinion relative to the workbench?
`where('actual', 'gear-in', 'f-bench', 2026-11-06 12:00, perspective='system')` -> **INFERRED**, judgement: single
- candidate 0: x 0.620, y 0.460, z 1.000 m [INFERRED], derived (frame-transform/v1) from a position stated in f-gearbox; position attestation(s) ['att:3d2dc068a3f64637']
    via f-gearbox -> f-bench (forward): t = (0.6, 0.4, 0.92), rotation 0 deg about z; attestation(s) ['att:602b27e000334119']
- incomparable: a position stated in f-cam-2 (['att:97756caba81b4fee']): no frame chain from f-cam-2 to f-bench

### Q2b ... and relative to the workshop (two hops)?
`where('actual', 'gear-in', 'f-workshop', 2026-11-06 12:00, perspective='system')` -> **INFERRED**, judgement: single
- candidate 0: x 3.540, y 3.120, z 1.000 m [INFERRED], derived (frame-transform/v1) from a position stated in f-gearbox; position attestation(s) ['att:3d2dc068a3f64637']
    via f-gearbox -> f-bench (forward): t = (0.6, 0.4, 0.92), rotation 0 deg about z; attestation(s) ['att:602b27e000334119']
    via f-bench -> f-workshop (forward): t = (4.0, 2.5, 0.0), rotation 90 deg about z; attestation(s) ['att:12b3c56608f249a5']
- incomparable: a position stated in f-cam-2 (['att:97756caba81b4fee']): no frame chain from f-cam-2 to f-workshop

### Q2c Where is the bench relative to the gearbox (inverse chain, with ranges)?
`where('actual', 'bench-1', 'f-gearbox', 2026-11-06 12:00, perspective='system')` -> **INFERRED**, judgement: single
- candidate 0: x -0.650..-0.550, y -0.450..-0.350, z -0.920 m [INFERRED], derived (frame-transform/v1) from a position stated in f-workshop; position attestation(s) ['att:3c79dc6fa8c040e6']
    via f-bench -> f-workshop (inverse): t = (4.0, 2.5, 0.0), rotation 90 deg about z; attestation(s) ['att:12b3c56608f249a5']
    via f-gearbox -> f-bench (inverse): t = (0.6, 0.4, 0.92), rotation 0 deg about z; attestation(s) ['att:602b27e000334119']

### Q3 What changes when the workshop -> bench transform changes (the bench moved at T2)?
`where('actual', 'gbx-100', 'f-workshop', 2026-11-08 12:00, perspective='system')` -> **INFERRED**, judgement: single
- candidate 0: x 6.600, y 1.400, z 0.920 m [INFERRED], derived (frame-transform/v1) from a position stated in f-bench; position attestation(s) ['att:1a4e23298b224445']
    via f-bench -> f-workshop (forward): t = (6.0, 1.0, 0.0), rotation 0 deg about z; attestation(s) ['att:a3339f96a2a9428a']
- unreviewed alternatives (not part of this perspective's answer): ['att:45426553968f4159']

### Q3b ... the pinion relative to the bench does not change
`where('actual', 'gear-in', 'f-bench', 2026-11-08 12:00, perspective='system')` -> **INFERRED**, judgement: single
- candidate 0: x 0.620, y 0.460, z 1.000 m [INFERRED], derived (frame-transform/v1) from a position stated in f-gearbox; position attestation(s) ['att:3d2dc068a3f64637']
    via f-gearbox -> f-bench (forward): t = (0.6, 0.4, 0.92), rotation 0 deg about z; attestation(s) ['att:602b27e000334119']
- incomparable: a position stated in f-cam-2 (['att:97756caba81b4fee']): no frame chain from f-cam-2 to f-bench

### Q3c ... and in the plan world (bench by the door)
`where('plan-move-bench', 'gbx-100', 'f-workshop', 2026-11-08 12:00, perspective='system')` -> **INFERRED**, judgement: single
- candidate 0: x 0.400, y 0.600, z 0.920 m [INFERRED], derived (frame-transform/v1) from a position stated in f-bench; position attestation(s) ['att:1a4e23298b224445']
    via f-bench -> f-workshop (forward): t = (1.0, 1.0, 0.0), rotation 180 deg about z; attestation(s) ['att:3ebe12d103f3406e']
- unreviewed alternatives (not part of this perspective's answer): ['att:45426553968f4159']

### Q4 Which claims agree or conflict? The tag reader's own perspective
`where('actual', 'gbx-100', 'f-workshop', 2026-11-06 12:00, perspective='tag-reader')` -> **ASSERTED**, judgement: single
- candidate 0: x 5.000..5.200, y 3.000..3.200, z 0.800..1.000 m [ASSERTED], stated in this frame; position attestation(s) ['att:45426553968f4159']
- unreviewed alternatives (not part of this perspective's answer): ['att:1a4e23298b224445', 'att:57c358929e4d408e']

### Q4b The system now accepts the tag reader's claim
`accept('att:45426553968f4159')` recorded after 2026-11-10 17:21:09 (transaction time)

### Q4c ... the same question now
`where('actual', 'gbx-100', 'f-workshop', 2026-11-06 12:00, perspective='system')` -> **DISPUTED**, judgement: conflicting
- candidate 0: x 3.600, y 3.100, z 0.920 m [INFERRED], derived (frame-transform/v1) from a position stated in f-bench; position attestation(s) ['att:1a4e23298b224445']
    via f-bench -> f-workshop (forward): t = (4.0, 2.5, 0.0), rotation 90 deg about z; attestation(s) ['att:12b3c56608f249a5']
- candidate 1: x 3.550..3.650, y 3.050..3.150, z 0.900..0.940 m [ASSERTED], stated in this frame; position attestation(s) ['att:57c358929e4d408e']
- candidate 2: x 5.000..5.200, y 3.000..3.200, z 0.800..1.000 m [ASSERTED], stated in this frame; position attestation(s) ['att:45426553968f4159']
- conflict: candidates 0 and 2 are disjoint
- conflict: candidates 1 and 2 are disjoint

### Q4d ... as known before that acceptance
`where('actual', 'gbx-100', 'f-workshop', 2026-11-06 12:00, perspective='system')` -> **ASSERTED**, judgement: compatible
- candidate 0: x 3.600, y 3.100, z 0.920 m [INFERRED], derived (frame-transform/v1) from a position stated in f-bench; position attestation(s) ['att:1a4e23298b224445']
    via f-bench -> f-workshop (forward): t = (4.0, 2.5, 0.0), rotation 90 deg about z; attestation(s) ['att:12b3c56608f249a5']
- candidate 1: x 3.550..3.650, y 3.050..3.150, z 0.900..0.940 m [ASSERTED], stated in this frame; position attestation(s) ['att:57c358929e4d408e']
- unreviewed alternatives (not part of this perspective's answer): ['att:45426553968f4159']

### Q5 Earlier in time, before the observations
`where('actual', 'gbx-100', 'f-workshop', 2026-11-03 12:00, perspective='system')` -> **INFERRED**, judgement: single
- candidate 0: x 3.600, y 3.100, z 0.920 m [INFERRED], derived (frame-transform/v1) from a position stated in f-bench; position attestation(s) ['att:1a4e23298b224445']
    via f-bench -> f-workshop (forward): t = (4.0, 2.5, 0.0), rotation 90 deg about z; attestation(s) ['att:12b3c56608f249a5']

## Part 2: raw TypeQL against the stored records (not judged)

### R1 frames reachable from f-gearbox by the TypeDB function frames_linked (records, actual world)
```
match $f isa spatial-frame, has wm-id "f-gearbox"; $w isa world, has wm-id "actual";
      let $g in frames_linked($f, $w); $g has wm-id $id;
fetch { "frame": $id };
```
  {"frame": "f-bench"}
  {"frame": "f-gearbox"}
  {"frame": "f-workshop"}

### R2 every frame-transform record with its world, source and stated interval
```
match $c isa frame-transform (parent: $p, child: $ch), has tx $tx, has ty $ty, has qw $qw, has qz $qz;
      $p has wm-id $pid; $ch has wm-id $cid;
      $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid; $w has wm-id $wid; $who has wm-id $by;
fetch { "parent": $pid, "child": $cid, "tx": $tx, "ty": $ty, "qw": $qw, "qz": $qz, "world": $wid, "by": $by,
        "attestation": $aid, "from": $a.valid-from-earliest, "until": $a.valid-to-earliest };
```
  {"attestation": "att:12b3c56608f249a5", "by": "system", "child": "f-bench", "from": "2026-11-02T08:00:00.000000000+00:00", "parent": "f-workshop", "qw": 0.7071067811865476, "qz": 0.7071067811865475, "tx": 4.0, "ty": 2.5, "until": "2026-11-08T10:00:00.000000000+00:00", "world": "actual"}
  {"attestation": "att:3ebe12d103f3406e", "by": "system", "child": "f-bench", "from": "2026-11-07T09:00:00.000000000+00:00", "parent": "f-workshop", "qw": 6.123233995736766e-17, "qz": 1.0, "tx": 1.0, "ty": 1.0, "until": null, "world": "plan-move-bench"}
  {"attestation": "att:52f8b764ebdc4ef0", "by": "system", "child": "f-bench", "from": "2026-11-02T08:00:00.000000000+00:00", "parent": "f-workshop", "qw": 0.7071067811865476, "qz": 0.7071067811865475, "tx": 4.0, "ty": 2.5, "until": null, "world": "actual"}
  {"attestation": "att:602b27e000334119", "by": "system", "child": "f-gearbox", "from": "2026-11-02T08:00:00.000000000+00:00", "parent": "f-bench", "qw": 1.0, "qz": 0.0, "tx": 0.6, "ty": 0.4, "until": null, "world": "actual"}
  {"attestation": "att:a3339f96a2a9428a", "by": "system", "child": "f-bench", "from": "2026-11-08T10:00:00.000000000+00:00", "parent": "f-workshop", "qw": 1.0, "qz": 0.0, "tx": 6.0, "ty": 1.0, "until": null, "world": "actual"}

### R3 every position record of gbx-100 (all frames and sources)
```
match $x isa physical-object, has wm-id "gbx-100";
      $c isa positioned-in (positioned: $x, frame: $f), has x-min $x0, has x-max $x1, has y-min $y0, has y-max $y1;
      $f has wm-id $fid; $a isa attestation (content: $c, attester: $who), has wm-id $aid, has basis $b;
      $who has wm-id $by;
fetch { "frame": $fid, "x": $x0, "x_max": $x1, "y": $y0, "y_max": $y1, "by": $by, "basis": $b, "attestation": $aid };
```
  {"attestation": "att:1a4e23298b224445", "basis": "testimony", "by": "system", "frame": "f-bench", "x": 0.6, "x_max": 0.6, "y": 0.4, "y_max": 0.4}
  {"attestation": "att:45426553968f4159", "basis": "observation", "by": "tag-reader", "frame": "f-workshop", "x": 5.0, "x_max": 5.2, "y": 3.0, "y_max": 3.2}
  {"attestation": "att:57c358929e4d408e", "basis": "observation", "by": "cam-2", "frame": "f-workshop", "x": 3.55, "x_max": 3.65, "y": 3.05, "y_max": 3.15}
