# Mechanical profile on the gearbox (database 'wm-reference-gearbox-d1')

Profiles installed: {'mechanical': '0.1'}

## Part 1: judged answers (WorldModel API, system perspective unless stated)

### Q1 Assembly structure (core part-of; classification as assembly is vocabulary)
- gbx-100 classified ['gearbox', 'mechanical:assembly']; parts after the repair: ['bearing-2', 'bearing-3', 'bolt-1', 'bolt-2', 'bolt-3', 'bolt-4', 'cover', 'gasket', 'gear-in', 'gear-out', 'housing', 'input-shaft', 'output-shaft', 'shaft-asm-in']
- shaft-asm-in classified ['mechanical:assembly', 'sub-assembly']; parts after the repair: ['bearing-3', 'gear-in', 'input-shaft']
- shaft-asm-in parts before the repair: ['bearing-1', 'gear-in', 'input-shaft']

### Q2 Connections (symmetric, typed, timed; not parthood)
- input-shaft, before the repair: [('bearing-1', 'mechanical:pressed', 'ASSERTED'), ('gear-in', 'mechanical:splined', 'ASSERTED')]
- input-shaft, after the repair: [('bearing-3', 'mechanical:pressed', 'ASSERTED'), ('gear-in', 'mechanical:splined', 'ASSERTED')]
- cover: [('housing', 'mechanical:bolted')]

### Q3 Typed dependencies; an untyped (historical) claim stays unspecified
- output-shaft depends on: [('input-shaft', 'dependency:functional', 'ASSERTED'), ('input-shaft', 'unspecified', 'ASSERTED')]
- gear-in depends on: [('input-shaft', 'dependency:physical', 'ASSERTED')]
- gbx-100 depends on: [('manual-gbx', 'dependency:informational', 'ASSERTED')]
- test-rig depends on: [('rig-controller', 'dependency:control', 'ASSERTED')]
- gear-out depends on: [('bearing-2', 'dependency:functional', 'ASSERTED')]
- output-shaft, as known before kinds were recorded: [('input-shaft', 'unspecified')]
- dependencies(output-shaft, kind=None): ['input-shaft']
- dependencies(output-shaft, kind=dependency:functional): ['input-shaft']
- dependencies(output-shaft, kind=dependency:physical): []
- dependency vs parthood: gear-in depends on input-shaft physically; parts(gear-in) = [], and both are parts of shaft-asm-in

### Q4 Component replacement: account, occurrence and claimed effects kept apart
- ev-cmms-replacement (by cmms): account accepted, removed ['bearing-1'], fitted ['bearing-3'], occurrences [('o-bearing-replacement', 'not established')]
  - claimed initiates part-of{'whole': ['shaft-asm-in'], 'part': ['bearing-3']} by ['cmms']: claim accepted; holds before None, after True
  - claimed terminates part-of{'whole': ['shaft-asm-in'], 'part': ['bearing-1']} by ['cmms']: claim accepted; holds before True, after False

### Q5 Historical state before and after the replacement
- part-of(bearing-1, shaft-asm-in) before: ASSERTED True
- part-of(bearing-1, shaft-asm-in) after: ASSERTED False
- part-of(bearing-3, shaft-asm-in) before: UNKNOWN None
- part-of(bearing-3, shaft-asm-in) after: ASSERTED True

### Q6 Perspective disagreement
- system: inspector's replacement account not accepted (removed ['bearing-2'])
  gear-out functionally depends on bearing-2: ASSERTED True
- inspector: inspector's replacement account accepted (removed ['bearing-2'])
  gear-out functionally depends on bearing-2: ASSERTED False

### Q7 Hypothetical control upgrade (plan stipulated from 11-08 09:00; asked at 11-08 12:00)
- actual: test-rig depends on [('rig-controller', 'dependency:control', 'ASSERTED')]
- plan-rig-control: test-rig depends on [('plc-2', 'dependency:control', 'STIPULATED'), ('rig-controller', 'dependency:control', 'ASSERTED')]

## Part 2: raw TypeQL against the stored records (not judged)

### R1 part-of: the assembly structure as stored (whole, part, source, interval)
```
match $c isa part-of (whole: $w, part: $p); $w has wm-id $wid; $p has wm-id $pid;
  { $w has wm-id "gbx-100"; } or { $w has wm-id "shaft-asm-in"; };
  $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "whole": $wid, "part": $pid, "by": $by, "from": $a.valid-from-earliest, "until": $a.valid-to-earliest };
```
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "bearing-1", "until": "2026-11-05T14:00:00.000000000+00:00", "whole": "shaft-asm-in"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "bearing-1", "until": null, "whole": "shaft-asm-in"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "bearing-2", "until": null, "whole": "gbx-100"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "bolt-1", "until": null, "whole": "gbx-100"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "bolt-2", "until": null, "whole": "gbx-100"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "bolt-3", "until": null, "whole": "gbx-100"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "bolt-4", "until": null, "whole": "gbx-100"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "cover", "until": null, "whole": "gbx-100"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "gasket", "until": null, "whole": "gbx-100"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "gear-in", "until": null, "whole": "shaft-asm-in"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "gear-out", "until": null, "whole": "gbx-100"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "housing", "until": null, "whole": "gbx-100"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "input-shaft", "until": null, "whole": "shaft-asm-in"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "output-shaft", "until": null, "whole": "gbx-100"}
  {"by": "system", "from": "2026-11-02T08:00:00.000000000+00:00", "part": "shaft-asm-in", "until": null, "whole": "gbx-100"}
  {"by": "system", "from": "2026-11-05T14:00:00.000000000+00:00", "part": "bearing-3", "until": null, "whole": "shaft-asm-in"}

### R2 connected-to: connections with their joint kind and interval
```
match $c isa connected-to; $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "endpoints": [ match $c links (endpoint: $e); $e has wm-id $eid; fetch { "id": $eid }; ],
        "joint": [ match $c links (joint-kind: $k); $k has wm-id $kid; fetch { "id": $kid }; ],
        "by": $by, "from": $a.valid-from-earliest, "until": $a.valid-to-earliest };
```
  {"by": "design-office", "endpoints": [{"id": "housing"}, {"id": "cover"}], "from": "2026-11-02T08:00:00.000000000+00:00", "joint": [{"id": "mechanical:bolted"}], "until": null}
  {"by": "design-office", "endpoints": [{"id": "input-shaft"}, {"id": "gear-in"}], "from": "2026-11-02T08:00:00.000000000+00:00", "joint": [{"id": "mechanical:splined"}], "until": null}
  {"by": "design-office", "endpoints": [{"id": "output-shaft"}, {"id": "bearing-2"}], "from": "2026-11-02T08:00:00.000000000+00:00", "joint": [{"id": "mechanical:pressed"}], "until": null}
  {"by": "design-office", "endpoints": [{"id": "output-shaft"}, {"id": "gear-out"}], "from": "2026-11-02T08:00:00.000000000+00:00", "joint": [{"id": "mechanical:splined"}], "until": null}
  {"by": "technician", "endpoints": [{"id": "input-shaft"}, {"id": "bearing-1"}], "from": "2026-11-02T08:00:00.000000000+00:00", "joint": [{"id": "mechanical:pressed"}], "until": "2026-11-05T14:00:00.000000000+00:00"}
  {"by": "technician", "endpoints": [{"id": "input-shaft"}, {"id": "bearing-3"}], "from": "2026-11-05T14:00:00.000000000+00:00", "joint": [{"id": "mechanical:pressed"}], "until": null}

### R3 depends-on: every dependency, typed or not, with its source and polarity
```
match $c isa depends-on (dependent: $x, dependee: $y); $x has wm-id $xid; $y has wm-id $yid;
  $a isa attestation (content: $c, attester: $who, context: $w), has polarity $pol; $who has wm-id $by;
  $w has wm-id $wid;
fetch { "dependent": $xid, "dependee": $yid, "polarity": $pol, "by": $by, "world": $wid,
        "kind": [ match $c links (kind: $k); $k has wm-id $kid; fetch { "id": $kid }; ] };
```
  {"by": "design-office", "dependee": "input-shaft", "dependent": "gear-in", "kind": [{"id": "dependency:physical"}], "polarity": true, "world": "actual"}
  {"by": "design-office", "dependee": "input-shaft", "dependent": "output-shaft", "kind": [], "polarity": true, "world": "actual"}
  {"by": "design-office", "dependee": "input-shaft", "dependent": "output-shaft", "kind": [{"id": "dependency:functional"}], "polarity": true, "world": "actual"}
  {"by": "design-office", "dependee": "manual-gbx", "dependent": "gbx-100", "kind": [{"id": "dependency:informational"}], "polarity": true, "world": "actual"}
  {"by": "inspector", "dependee": "bearing-2", "dependent": "gear-out", "kind": [{"id": "dependency:functional"}], "polarity": false, "world": "actual"}
  {"by": "system", "dependee": "plc-2", "dependent": "test-rig", "kind": [{"id": "dependency:control"}], "polarity": true, "world": "plan-rig-control"}
  {"by": "technician", "dependee": "bearing-2", "dependent": "gear-out", "kind": [{"id": "dependency:functional"}], "polarity": true, "world": "actual"}
  {"by": "technician", "dependee": "rig-controller", "dependent": "test-rig", "kind": [{"id": "dependency:control"}], "polarity": true, "world": "actual"}

### R4 replacement descriptions: removed and fitted parts, source, occurrence links
```
match $e isa replacement (removed: $r, fitted: $f), has wm-id $eid; $r has wm-id $rid; $f has wm-id $fid;
  $a isa attestation (content: $e, attester: $who); $who has wm-id $by;
fetch { "event": $eid, "removed": $rid, "fitted": $fid, "by": $by,
        "describes": [ match $d isa describes (description: $e, occurrence: $o); $o has wm-id $oid;
                       fetch { "occurrence": $oid }; ] };
```
  {"by": "cmms", "describes": [{"occurrence": "o-bearing-replacement"}], "event": "ev-cmms-replacement", "fitted": "bearing-3", "removed": "bearing-1"}
  {"by": "inspector", "describes": [{"occurrence": "o-bearing-replacement"}], "event": "ev-inspector-replacement", "fitted": "bearing-3", "removed": "bearing-2"}
