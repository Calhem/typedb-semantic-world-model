# Dynamics and causality in the reference world (database 'wm-reference-gearbox')

## Part 1: judged answers (WorldModel API)

### Q1 What happened to the gearbox? (accepted event descriptions naming gbx-100, in time order)
- 11-04 09:00..11-04 09:30 ev-inspection-report [action, inspection] by inspector; describes ['o-inspection']
- 11-05 13:00..11-05 13:45 ev-disassembly [action, disassembly] by technician; describes ['o-disassembly']
- 11-05 13:00..11-05 16:00 ev-repair [process, repair] by technician; describes ['o-repair']
- 11-05 14:15..11-05 15:15 ev-reassembly [action, reassembly] by technician; describes ['o-reassembly']
- 11-05 15:30..11-05 16:00 ev-test-run [action, test] by technician; describes ['o-test-run']
- 11-05 16:00..11-05 16:00 ev-sign-off [sign-off] by inspector; describes ['o-sign-off']
  The repair process, step by step (part-of among occurrences):
  - 11-05 13:00..11-05 13:45 o-disassembly [action, disassembly] actor ['technician']
  - 11-05 13:50..11-05 14:00 o-bearing-replacement [action, replacement] actor ['technician']
  - 11-05 14:05..11-05 14:20 o-relubrication [action, lubrication] actor ['technician']
  - 11-05 14:15..11-05 15:15 o-reassembly [action, reassembly] actor ['technician']
  - 11-05 15:30..11-05 16:00 o-test-run [action, test] actor ['technician']

### Q2 Which component was replaced?
- o-bearing-replacement has 2 accepted descriptions ['ev-maintenance-record', 'ev-worklog-replacement']; patients named: {'bearing-3': [('ev-worklog-replacement', 'technician')], 'bearing-1': [('ev-maintenance-record', 'system')]}
- claimed initiates part-of{'whole': ['shaft-asm-in'], 'part': ['bearing-3']} by ['technician']: claim accepted; state before UNKNOWN/None, after ASSERTED/True; accepted change: True
- claimed initiates has-quality{'bearer': ['gbx-100'], 'value': ['low'], 'quality': ['vibration']} by ['technician']: claim unreviewed; state before UNKNOWN/None, after UNKNOWN/None; accepted change: False
- claimed terminates part-of{'whole': ['shaft-asm-in'], 'part': ['bearing-1']} by ['technician']: claim accepted; state before ASSERTED/True, after ASSERTED/False; accepted change: True
- changes to shaft-asm-in 11-03 12:00 -> 11-06 12:00: began [['bearing-3']], ended [['bearing-1']]

### Q3 What state existed before and after the repair?
- condition before the inspection (11-03 12:00): ASSERTED ['operational']
- condition after the inspection (11-04 09:30): ASSERTED ['faulty']
- condition as the repair starts (11-05 13:00): ASSERTED ['faulty']
- condition after the repair (11-05 16:01): ASSERTED ['operational']
- began: has-quality {'bearer': ['gbx-100'], 'quality': ['condition'], 'value': ['operational']} [ASSERTED] stated by ['technician']; claimed events: [('ev-test-run', 'accepted', ['technician'])]
- began: positioned-in {'frame': ['f-workshop'], 'positioned': ['gbx-100']} [ASSERTED] stated by ['cam-2']; claimed events: []
- ended: has-quality {'bearer': ['gbx-100'], 'quality': ['condition'], 'value': ['faulty']} [ASSERTED] stated by ['inspector']; claimed events: [('ev-test-run', 'accepted', ['technician'])]
- all transitions of gbx-100 in (11-03 12:00, 11-06 12:00] (LABS-1.015 contract):
  - has-quality{'bearer': ['gbx-100'], 'quality': ['condition']}: ASSERTED [['operational']] -> ASSERTED [['faulty']]; world-state transition at 11-04 09:30 (certain); explained by no accepted effect claim
  - has-quality{'bearer': ['gbx-100'], 'quality': ['condition']}: ASSERTED [['faulty']] -> ASSERTED [['operational']]; world-state transition at 11-05 16:00 (certain); explained by ['ev-test-run (initiates, unique)', 'ev-test-run (terminates, unique)']
  - positioned-in{'frame': ['f-workshop'], 'positioned': ['gbx-100']}: UNKNOWN [] -> ASSERTED [{'x-max': 3.65, 'x-min': 3.55, 'y-max': 3.15, 'y-min': 3.05, 'z-max': 0.94, 'z-min': 0.9}]; judgement transition at 11-06 11:00 (certain); explained by no accepted effect claim

### Q4 Who performed the relevant actions?
- technician: ev-disassembly [action, disassembly] 11-05 13:00..11-05 13:45 -> ['o-disassembly']
- technician: ev-worklog-replacement [action, replacement] 11-05 13:50..11-05 14:00 -> ['o-bearing-replacement']
- technician: ev-relubrication [action, lubrication] 11-05 14:05..11-05 14:20 -> ['o-relubrication']
- technician: ev-reassembly [action, reassembly] 11-05 14:15..11-05 15:15 -> ['o-reassembly']
- technician: ev-test-run [action, test] 11-05 15:30..11-05 16:00 -> ['o-test-run']
- inspector: ev-inspection-report [action, inspection] 11-04 09:00

### Q5 What caused the gearbox to become operational again?
- operational at 11-06 12:00: ASSERTED, support ['att:f353010dc4124e4c']
- initiated by ev-test-run (claim accepted, by ['technician']), ended 11-05 16:00, describing ['o-test-run']
    cause: ev-worklog-replacement -> ev-test-run (description-level): accepted [ASSERTED], claimed by ['technician']
    cause: o-bearing-replacement -> o-test-run (occurrence-level, lifted via {'description': 'ev-test-run', 'occurrence': 'o-test-run'}): accepted [ASSERTED], claimed by ['technician']

### Q6 Which explanations are disputed, rejected or unreviewed?
- o-relubrication -> o-test-run: disputed; inspector (asserts, testimony, accepted); cm-1 (denies, inference, accepted)
- o-reassembly -> o-test-run: unreviewed; cm-1 (asserts, inference, unreviewed)
- o-inspection -> o-test-run: rejected; apprentice (asserts, testimony, rejected)
- not a cause by succession: the inspection ended before the test run (before = True), and the only claim that it caused it was rejected; the disassembly precedes it too and no one claimed it as a cause

### Q7 How do the answers differ between perspectives, knowledge times and hypothetical worlds?
- causes of o-test-run, technician's perspective: [('ev-worklog-replacement', 'accepted'), ('o-bearing-replacement', 'accepted'), ('o-inspection', 'unreviewed'), ('o-reassembly', 'unreviewed'), ('o-relubrication', 'unreviewed')]
- causes of o-test-run, inspector's perspective: [('o-relubrication', 'accepted'), ('o-bearing-replacement', 'unreviewed'), ('o-inspection', 'unreviewed'), ('o-reassembly', 'unreviewed')]
- causes of o-test-run, system, as known before the denial was accepted: [('ev-worklog-replacement', 'accepted'), ('o-bearing-replacement', 'accepted'), ('o-relubrication', 'accepted'), ('o-inspection', 'unreviewed'), ('o-reassembly', 'unreviewed')]
- causes of o-test-run, hypothetical world 'plan-relubricate-only': [('ev-worklog-replacement', 'accepted'), ('o-relubrication', 'accepted'), ('o-bearing-replacement', 'denied'), ('o-reassembly', 'unreviewed'), ('o-inspection', 'rejected')]
- condition after the repair time in 'plan-no-repair' (knowledge before the repair was recorded): ASSERTED ['faulty']
- condition after the repair, inspector's perspective: UNKNOWN []

## Part 2: raw TypeQL against the stored records (not judged)

### R1 event descriptions with gbx-100 as a participant: role, source and stated interval
```
match $x isa physical-object, has wm-id "gbx-100"; $e isa event, has wm-id $eid; $e links ($r: $x);
      $a isa attestation (content: $e, attester: $who), has valid-from-earliest $from; $who has wm-id $by;
fetch { "event": $eid, "role": $r, "by": $by, "from": $from, "until": $a.valid-to-earliest };
```
  {"by": "inspector", "event": "ev-inspection-report", "from": "2026-11-04T09:00:00.000000000+00:00", "role": {"kind": "relation:role", "label": "event:patient"}, "until": "2026-11-04T09:30:00.000000000+00:00"}
  {"by": "inspector", "event": "ev-sign-off", "from": "2026-11-05T16:00:00.000000000+00:00", "role": {"kind": "relation:role", "label": "event:patient"}, "until": "2026-11-05T16:00:00.000000000+00:00"}
  {"by": "technician", "event": "ev-disassembly", "from": "2026-11-05T13:00:00.000000000+00:00", "role": {"kind": "relation:role", "label": "event:patient"}, "until": "2026-11-05T13:45:00.000000000+00:00"}
  {"by": "technician", "event": "ev-reassembly", "from": "2026-11-05T14:15:00.000000000+00:00", "role": {"kind": "relation:role", "label": "event:patient"}, "until": "2026-11-05T15:15:00.000000000+00:00"}
  {"by": "technician", "event": "ev-repair", "from": "2026-11-05T13:00:00.000000000+00:00", "role": {"kind": "relation:role", "label": "event:patient"}, "until": "2026-11-05T16:00:00.000000000+00:00"}
  {"by": "technician", "event": "ev-test-run", "from": "2026-11-05T15:30:00.000000000+00:00", "role": {"kind": "relation:role", "label": "event:patient"}, "until": "2026-11-05T16:00:00.000000000+00:00"}

### R2 describes records: which description is said to describe which occurrence, by whom
```
match $c isa describes (description: $e, occurrence: $o); $e has wm-id $eid; $o has wm-id $oid;
      $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "description": $eid, "occurrence": $oid, "by": $by };
```
  {"by": "inspector", "description": "ev-inspection-report", "occurrence": "o-inspection"}
  {"by": "inspector", "description": "ev-sign-off", "occurrence": "o-sign-off"}
  {"by": "system", "description": "ev-maintenance-record", "occurrence": "o-bearing-replacement"}
  {"by": "technician", "description": "ev-disassembly", "occurrence": "o-disassembly"}
  {"by": "technician", "description": "ev-reassembly", "occurrence": "o-reassembly"}
  {"by": "technician", "description": "ev-relubrication", "occurrence": "o-relubrication"}
  {"by": "technician", "description": "ev-repair", "occurrence": "o-repair"}
  {"by": "technician", "description": "ev-test-run", "occurrence": "o-test-run"}
  {"by": "technician", "description": "ev-worklog-replacement", "occurrence": "o-bearing-replacement"}

### R3 effect claims (initiates / terminates) with the outcome proposition's canonical key
```
match $c isa! $t, links (event: $e, outcome: $p); { $c isa initiates; } or { $c isa terminates; };
      $e has wm-id $eid; $p has proposition-key $key;
      $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "claim": $t, "event": $eid, "outcome": $key, "by": $by };
```
  {"by": "technician", "claim": {"kind": "relation", "label": "initiates"}, "event": "ev-test-run", "outcome": "has-quality|bearer=gbx-100|quality=condition|value=operational"}
  {"by": "technician", "claim": {"kind": "relation", "label": "initiates"}, "event": "ev-worklog-replacement", "outcome": "has-quality|bearer=gbx-100|quality=vibration|value=low"}
  {"by": "technician", "claim": {"kind": "relation", "label": "initiates"}, "event": "ev-worklog-replacement", "outcome": "part-of|part=bearing-3|whole=shaft-asm-in"}
  {"by": "technician", "claim": {"kind": "relation", "label": "terminates"}, "event": "ev-test-run", "outcome": "has-quality|bearer=gbx-100|quality=condition|value=faulty"}
  {"by": "technician", "claim": {"kind": "relation", "label": "terminates"}, "event": "ev-worklog-replacement", "outcome": "part-of|part=bearing-1|whole=shaft-asm-in"}

### R4 causal claim records: polarity, source, basis (and any acceptance verdicts recorded about them)
```
match $c isa causes (cause: $x, effect: $y); $x has wm-id $xid; $y has wm-id $yid;
      $a isa attestation (content: $c, attester: $who, context: $w), has wm-id $aid, has polarity $pol, has basis $b;
      $who has wm-id $by; $w has wm-id $wid;
fetch { "cause": $xid, "effect": $yid, "polarity": $pol, "by": $by, "basis": $b, "world": $wid, "attestation": $aid,
        "verdicts": [ match $v isa acceptance (accepted: $a, holder: $h), has verdict $vd; $h has wm-id $hid;
                      fetch { "holder": $hid, "verdict": $vd }; ] };
```
  {"attestation": "att:17a060df1560467c", "basis": "testimony", "by": "technician", "cause": "o-disassembly", "effect": "o-bearing-replacement", "polarity": true, "verdicts": [{"holder": "system", "verdict": "accepted"}], "world": "actual"}
  {"attestation": "att:66c316032c514d11", "basis": "testimony", "by": "inspector", "cause": "o-relubrication", "effect": "o-test-run", "polarity": true, "verdicts": [{"holder": "system", "verdict": "accepted"}], "world": "actual"}
  {"attestation": "att:6f361a91a95e433a", "basis": "testimony", "by": "technician", "cause": "o-bearing-replacement", "effect": "o-test-run", "polarity": true, "verdicts": [{"holder": "system", "verdict": "accepted"}], "world": "actual"}
  {"attestation": "att:74c31e08781f482a", "basis": "testimony", "by": "technician", "cause": "ev-worklog-replacement", "effect": "ev-test-run", "polarity": true, "verdicts": [{"holder": "system", "verdict": "accepted"}], "world": "actual"}
  {"attestation": "att:7fd4d5c06aa94131", "basis": "stipulation", "by": "system", "cause": "o-relubrication", "effect": "o-test-run", "polarity": true, "verdicts": [], "world": "plan-relubricate-only"}
  {"attestation": "att:8261a220880e4b40", "basis": "inference", "by": "cm-1", "cause": "o-relubrication", "effect": "o-test-run", "polarity": false, "verdicts": [{"holder": "system", "verdict": "accepted"}], "world": "actual"}
  {"attestation": "att:8daf4502adb34a9f", "basis": "inference", "by": "cm-1", "cause": "o-reassembly", "effect": "o-test-run", "polarity": true, "verdicts": [], "world": "actual"}
  {"attestation": "att:8fa40a21f52e468d", "basis": "stipulation", "by": "system", "cause": "o-bearing-replacement", "effect": "o-test-run", "polarity": false, "verdicts": [], "world": "plan-relubricate-only"}
  {"attestation": "att:afdaced0131f4d6d", "basis": "testimony", "by": "apprentice", "cause": "o-inspection", "effect": "o-test-run", "polarity": true, "verdicts": [{"holder": "system", "verdict": "rejected"}], "world": "actual"}

### R5 process membership: occurrences recorded as part of o-repair
```
match $p isa occurrence, has wm-id "o-repair"; $c isa part-of (whole: $p, part: $s); $s has wm-id $sid;
      $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "step": $sid, "by": $by };
```
  {"by": "technician", "step": "o-bearing-replacement"}
  {"by": "technician", "step": "o-disassembly"}
  {"by": "technician", "step": "o-reassembly"}
  {"by": "technician", "step": "o-relubrication"}
  {"by": "technician", "step": "o-test-run"}
