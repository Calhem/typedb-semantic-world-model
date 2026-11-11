# Stage C: qualities, measurement and capabilities in two domains

Databases `wm-reference-gearbox-c` (workshop) and `wm-reference-lab` (laboratory). Everything below is printed by `scripts/show_qualities_agency.py`.

## Part 1: judged answers (WorldModel API)

### Q1 What is the mass, and on what evidence? (each attestation with its own records)
**Workshop: housing mass, 11-06 12:00**
- status ASSERTED
  - measurements (usable): att:1eb62187a81747d4 by technician (observation, accepted) SI [12.350 .. 12.450] <- record m-housing-scale-3-result: 12.4 kg u=0.025 k=2.0 conditions ['bench scale on bench-1', 'temperature=19C'] instrument ['scale-3']
  - measurements (usable): att:32b5c19c22ad4167 by technician (observation, accepted) SI [12.370 .. 12.450] <- record m-housing-scale-9-result: 12410.0 g u=20.0 k=2.0 conditions ['bench scale on bench-1', 'temperature=19C'] instrument ['scale-9']
  - statements (no record): att:31d3df6e1d3f4263 by design-office (testimony, accepted) SI [12.500 .. 12.500] 
  - statements (no record): att:def15787b16e4448 by scale-3 (observation, accepted) SI [12.350 .. 12.450] 
  - pair att:1eb62187a81747d4 / att:32b5c19c22ad4167: possibly compatible
**Laboratory: sample-12 mass, 11-10 15:00**
- status ASSERTED
  - measurements (usable): att:3bd9ddb532d14e69 by bo (observation, accepted) SI [3.460 .. 3.520] <- record m-bo-b7-result: 3490.0 u-g u=15.0 k=2.0 conditions ['humidity=40%', 'temperature=20C'] instrument ['balance-b7']
  - measurements (usable): att:447f813de2bd446f by ana (observation, accepted) SI [3.490 .. 3.570] <- record m-ana-b9-result: 3.53 u-kg u=0.02 k=2.0 conditions ['humidity=40%', 'temperature=35C'] instrument ['balance-b9']
  - measurements (usable): att:5e9107f334314f98 by bo (observation, accepted) SI [3.470 .. 3.530] <- record m-bo-k3-result: 3.5 u-kg u=0.01 k=3.0 conditions ['humidity=40%', 'temperature=20C'] instrument ['balance-b7']
  - measurements (usable): att:64996c4601814625 by ana (observation, accepted) SI [3.490 .. 3.570] <- record m-ana-b3-corr-result: 3.53 u-kg u=0.02 k=2.0 conditions ['humidity=40%', 'temperature=20C'] instrument ['balance-b3']
  - alternatives: att:b94e4a31617c4768 by lab-2 (observation, unreviewed) SI [3.660 .. 3.740] <- record m-lab2-result: 3.7 u-kg u=0.02 k=2.0 conditions ['humidity=40%', 'temperature=20C'] instrument []
  - alternatives: att:fc2d51b06a084449 by ana (observation, superseded) SI [3.470 .. 3.550] <- record m-ana-b3-result: 3.51 u-kg u=0.02 k=2.0 conditions ['humidity=40%', 'temperature=20C'] instrument ['balance-b3']
  - statements (no record): att:7c089b7e1dc446b2 by qa (testimony, accepted) SI [3.500 .. 3.500] 
  - pair att:3bd9ddb532d14e69 / att:447f813de2bd446f: incomparable (different measurement conditions ([('humidity=40%', 'temperature=20C')] vs [('humidity=40%', 'temperature=35C')]))
  - pair att:3bd9ddb532d14e69 / att:5e9107f334314f98: incomparable (different coverage levels (0.9544997361036416 vs 0.9973002039367398))
  - pair att:3bd9ddb532d14e69 / att:64996c4601814625: possibly compatible
  - pair att:447f813de2bd446f / att:5e9107f334314f98: incomparable (different coverage levels (0.9544997361036416 vs 0.9973002039367398))
  - pair att:447f813de2bd446f / att:64996c4601814625: incomparable (different measurement conditions ([('humidity=40%', 'temperature=35C')] vs [('humidity=40%', 'temperature=20C')]))
  - pair att:5e9107f334314f98 / att:64996c4601814625: incomparable (different coverage levels (0.9973002039367398 vs 0.9544997361036416))

### Q2 Units: the same conversion rules in both worlds
- workshop: 12410 g = 12.410 kg; lab: 3490 g = 3.490 kg; 20 degC = 293.15 K
- refused across dimensions: cannot convert mass (u-kg) to length (u-m)

### Q3 Who can do what, and where? (capabilities are contextual and timed)
- workshop 11-05 13:50: technician can-replace-bearing in workshop: established: holds True [ASSERTED] applicable [('workshop', 'accepted')]
- workshop 11-05 13:50: technician can-replace-bearing in None: not established: holds None [UNKNOWN] applicable [], held only in ['workshop']
- workshop 11-05 13:50: apprentice can-replace-bearing in workshop: not established: holds None [NOT_YET_KNOWN] applicable []
- workshop 11-05 13:50: inspector can-sign-off in bay-1: established: holds True [ASSERTED] applicable [(None, 'accepted')]
- workshop 11-05 13:50: bearing-press can-press-bearing in None: established: holds True [ASSERTED] applicable [(None, 'accepted')]
- lab 09:00: ana can-weigh in lab-1: established: holds True [ASSERTED] applicable [('lab-1', 'accepted')]
- lab 09:00: ana can-weigh in lab-2: not established: holds None [UNKNOWN] applicable [], held only in ['lab-1']
- lab 11:00: bo can-weigh in lab-1: established: holds True [ASSERTED] applicable [('lab-1', 'accepted')]
- lab 13:00: bo can-weigh in lab-1: expired: holds False [ASSERTED] applicable [('lab-1', 'expired')]
- lab 14:00: tom can-weigh in lab-1: not established: holds None [NOT_YET_KNOWN] applicable []
- lab 09:00: balance-b3 can-measure-mass in None: established: holds True [ASSERTED] applicable [(None, 'accepted')]

### Q4 Agency and roles (classifications, not types)
- apprentice: agent True; roles [('fitter', 'workshop')]
- bearing-press: agent None; roles []
- tom: agent True; roles []
- balance-b3: agent None; roles []

### Q5 Actions: what the records say, without concluding that anything happened or was allowed
- workshop ev-worklog-replacement: account accepted, kinds ['action', 'replacement'], occurrences [('o-bearing-replacement', 'not established')]; technician: agent True, can-replace-bearing in workshop True
- workshop ev-apprentice-fits: account not accepted, kinds [], occurrences none claimed; apprentice: agent None, can-replace-bearing in workshop None
- lab ev-tom-weighs: account accepted, kinds ['action', 'measurement'], occurrences none claimed; tom: agent True, can-weigh in lab-1 None
- capability without action: the inspector can sign off on 11-06, and has no action that day: []

### Q6 Perspectives, knowledge time and hypothetical worlds
**Laboratory, the external lab's perspective:**
- status ASSERTED
  - measurements (usable): att:b94e4a31617c4768 by lab-2 (observation, accepted) SI [3.660 .. 3.740] <- record m-lab2-result: 3.7 u-kg u=0.02 k=2.0 conditions ['humidity=40%', 'temperature=20C'] instrument []
  - alternatives: att:3bd9ddb532d14e69 by bo (observation, unreviewed) SI [3.460 .. 3.520] <- record m-bo-b7-result: 3490.0 u-g u=15.0 k=2.0 conditions ['humidity=40%', 'temperature=20C'] instrument ['balance-b7']
  - alternatives: att:447f813de2bd446f by ana (observation, unreviewed) SI [3.490 .. 3.570] <- record m-ana-b9-result: 3.53 u-kg u=0.02 k=2.0 conditions ['humidity=40%', 'temperature=35C'] instrument ['balance-b9']
  - alternatives: att:5e9107f334314f98 by bo (observation, unreviewed) SI [3.470 .. 3.530] <- record m-bo-k3-result: 3.5 u-kg u=0.01 k=3.0 conditions ['humidity=40%', 'temperature=20C'] instrument ['balance-b7']
  - alternatives: att:64996c4601814625 by ana (observation, unreviewed) SI [3.490 .. 3.570] <- record m-ana-b3-corr-result: 3.53 u-kg u=0.02 k=2.0 conditions ['humidity=40%', 'temperature=20C'] instrument ['balance-b3']
  - alternatives: att:fc2d51b06a084449 by ana (observation, unreviewed) SI [3.470 .. 3.550] <- record m-ana-b3-result: 3.51 u-kg u=0.02 k=2.0 conditions ['humidity=40%', 'temperature=20C'] instrument ['balance-b3']
  - statements (no record): att:7c089b7e1dc446b2 by qa (testimony, unreviewed) SI [3.500 .. 3.500] 
**Laboratory, as known before the correction:**
- status ASSERTED
  - measurements (usable): att:3bd9ddb532d14e69 by bo (observation, accepted) SI [3.460 .. 3.520] <- record m-bo-b7-result: 3490.0 u-g u=15.0 k=2.0 conditions ['humidity=40%', 'temperature=20C'] instrument ['balance-b7']
  - measurements (usable): att:447f813de2bd446f by ana (observation, accepted) SI [3.490 .. 3.570] <- record m-ana-b9-result: 3.53 u-kg u=0.02 k=2.0 conditions ['humidity=40%', 'temperature=35C'] instrument ['balance-b9']
  - measurements (usable): att:5e9107f334314f98 by bo (observation, accepted) SI [3.470 .. 3.530] <- record m-bo-k3-result: 3.5 u-kg u=0.01 k=3.0 conditions ['humidity=40%', 'temperature=20C'] instrument ['balance-b7']
  - measurements (usable): att:fc2d51b06a084449 by ana (observation, accepted) SI [3.470 .. 3.550] <- record m-ana-b3-result: 3.51 u-kg u=0.02 k=2.0 conditions ['humidity=40%', 'temperature=20C'] instrument ['balance-b3']
  - alternatives: att:b94e4a31617c4768 by lab-2 (observation, unreviewed) SI [3.660 .. 3.740] <- record m-lab2-result: 3.7 u-kg u=0.02 k=2.0 conditions ['humidity=40%', 'temperature=20C'] instrument []
  - statements (no record): att:7c089b7e1dc446b2 by qa (testimony, accepted) SI [3.500 .. 3.500] 
  - pair att:3bd9ddb532d14e69 / att:447f813de2bd446f: incomparable (different measurement conditions ([('humidity=40%', 'temperature=20C')] vs [('humidity=40%', 'temperature=35C')]))
  - pair att:3bd9ddb532d14e69 / att:5e9107f334314f98: incomparable (different coverage levels (0.9544997361036416 vs 0.9973002039367398))
  - pair att:3bd9ddb532d14e69 / att:fc2d51b06a084449: possibly compatible
  - pair att:447f813de2bd446f / att:5e9107f334314f98: incomparable (different coverage levels (0.9544997361036416 vs 0.9973002039367398))
  - pair att:447f813de2bd446f / att:fc2d51b06a084449: incomparable (different measurement conditions ([('humidity=40%', 'temperature=35C')] vs [('humidity=40%', 'temperature=20C')]))
  - pair att:5e9107f334314f98 / att:fc2d51b06a084449: incomparable (different coverage levels (0.9973002039367398 vs 0.9544997361036416))
- lab plan 'lab-plan-tom': tom can-weigh in lab-1 at 14:00: established: holds True [STIPULATED] applicable [('lab-1', 'accepted')]; actual: not established: holds None [NOT_YET_KNOWN] applicable []
- workshop plan 'plan-apprentice': apprentice can-replace-bearing in workshop: established: holds True [STIPULATED] applicable [('workshop', 'accepted')]; actual: not established: holds None [NOT_YET_KNOWN] applicable []

## Part 2: raw TypeQL against the stored records (not judged)

### workshop

#### R1 rests-on: each attestation and the record it rests on, with the record's own raw value, unit and conditions
```
match $l isa rests-on (attestation: $a, record: $r); $a has wm-id $aid; $a links (attester: $who); $who has wm-id $by;
      $r has wm-id $rid, has raw-value $v; expressed-in (record: $r, unit: $u); $u has wm-id $uid;
fetch { "attestation": $aid, "by": $by, "record": $rid, "raw": $v, "unit": $uid, "conditions": [ $r.condition ] };
```
  {"attestation": "att:1eb62187a81747d4", "by": "technician", "conditions": ["bench scale on bench-1", "temperature=19C"], "raw": 12.4, "record": "m-housing-scale-3-result", "unit": "kg"}
  {"attestation": "att:32b5c19c22ad4167", "by": "technician", "conditions": ["bench scale on bench-1", "temperature=19C"], "raw": 12410.0, "record": "m-housing-scale-9-result", "unit": "g"}

#### R2 produced: which activity produced which record (a proposition, attested)
```
match $p isa produced (activity: $e, result: $r); $e has wm-id $eid; $r has wm-id $rid;
      $a isa attestation (content: $p, attester: $who); $who has wm-id $by;
fetch { "activity": $eid, "record": $rid, "by": $by };
```
  {"activity": "m-housing-scale-3-activity", "by": "technician", "record": "m-housing-scale-3-result"}
  {"activity": "m-housing-scale-9-activity", "by": "technician", "record": "m-housing-scale-9-result"}

#### R3 capability and role grants: classified-as with a capability or social role, its context and interval
```
match $c isa classified-as (classified: $h, class: $k); $h has wm-id $hid; $k has wm-id $kid;
      { $k isa capability; } or { $k isa social-role; } or { $k isa category, has wm-id "agent"; };
      $a isa attestation (content: $c, attester: $who, context: $w), has polarity $pol,
         has valid-from-earliest $from; $who has wm-id $by; $w has wm-id $wid;
fetch { "holder": $hid, "class": $kid, "context": [ match $c links (context: $x); $x has wm-id $xid; fetch { "id": $xid }; ],
        "polarity": $pol, "from": $from, "until": $a.valid-to-earliest, "by": $by, "world": $wid };
```
  {"by": "system", "class": "agent", "context": [], "from": "2026-11-02T08:00:00.000000000+00:00", "holder": "apprentice", "polarity": true, "until": null, "world": "actual"}
  {"by": "system", "class": "agent", "context": [], "from": "2026-11-02T08:00:00.000000000+00:00", "holder": "inspector", "polarity": true, "until": null, "world": "actual"}
  {"by": "system", "class": "agent", "context": [], "from": "2026-11-02T08:00:00.000000000+00:00", "holder": "technician", "polarity": true, "until": null, "world": "actual"}
  {"by": "system", "class": "can-press-bearing", "context": [], "from": "2026-11-02T08:00:00.000000000+00:00", "holder": "bearing-press", "polarity": true, "until": null, "world": "actual"}
  {"by": "system", "class": "can-replace-bearing", "context": [{"id": "workshop"}], "from": "2026-11-02T08:00:00.000000000+00:00", "holder": "technician", "polarity": true, "until": null, "world": "actual"}
  {"by": "system", "class": "can-replace-bearing", "context": [{"id": "workshop"}], "from": "2026-11-07T09:00:00.000000000+00:00", "holder": "apprentice", "polarity": true, "until": null, "world": "plan-apprentice"}
  {"by": "system", "class": "can-sign-off", "context": [], "from": "2026-11-02T08:00:00.000000000+00:00", "holder": "inspector", "polarity": true, "until": null, "world": "actual"}
  {"by": "system", "class": "fitter", "context": [{"id": "workshop"}], "from": "2026-11-02T08:00:00.000000000+00:00", "holder": "apprentice", "polarity": true, "until": null, "world": "actual"}
  {"by": "system", "class": "fitter", "context": [{"id": "workshop"}], "from": "2026-11-02T08:00:00.000000000+00:00", "holder": "technician", "polarity": true, "until": null, "world": "actual"}

### laboratory

#### R1 rests-on: each attestation and the record it rests on, with the record's own raw value, unit and conditions
```
match $l isa rests-on (attestation: $a, record: $r); $a has wm-id $aid; $a links (attester: $who); $who has wm-id $by;
      $r has wm-id $rid, has raw-value $v; expressed-in (record: $r, unit: $u); $u has wm-id $uid;
fetch { "attestation": $aid, "by": $by, "record": $rid, "raw": $v, "unit": $uid, "conditions": [ $r.condition ] };
```
  {"attestation": "att:3bd9ddb532d14e69", "by": "bo", "conditions": ["humidity=40%", "temperature=20C"], "raw": 3490.0, "record": "m-bo-b7-result", "unit": "u-g"}
  {"attestation": "att:447f813de2bd446f", "by": "ana", "conditions": ["humidity=40%", "temperature=35C"], "raw": 3.53, "record": "m-ana-b9-result", "unit": "u-kg"}
  {"attestation": "att:5e9107f334314f98", "by": "bo", "conditions": ["humidity=40%", "temperature=20C"], "raw": 3.5, "record": "m-bo-k3-result", "unit": "u-kg"}
  {"attestation": "att:64996c4601814625", "by": "ana", "conditions": ["humidity=40%", "temperature=20C"], "raw": 3.53, "record": "m-ana-b3-corr-result", "unit": "u-kg"}
  {"attestation": "att:b94e4a31617c4768", "by": "lab-2", "conditions": ["humidity=40%", "temperature=20C"], "raw": 3.7, "record": "m-lab2-result", "unit": "u-kg"}
  {"attestation": "att:fc2d51b06a084449", "by": "ana", "conditions": ["humidity=40%", "temperature=20C"], "raw": 3.51, "record": "m-ana-b3-result", "unit": "u-kg"}

#### R2 produced: which activity produced which record (a proposition, attested)
```
match $p isa produced (activity: $e, result: $r); $e has wm-id $eid; $r has wm-id $rid;
      $a isa attestation (content: $p, attester: $who); $who has wm-id $by;
fetch { "activity": $eid, "record": $rid, "by": $by };
```
  {"activity": "m-ana-b3-activity", "by": "ana", "record": "m-ana-b3-result"}
  {"activity": "m-ana-b3-corr-activity", "by": "ana", "record": "m-ana-b3-corr-result"}
  {"activity": "m-ana-b9-activity", "by": "ana", "record": "m-ana-b9-result"}
  {"activity": "m-bo-b7-activity", "by": "bo", "record": "m-bo-b7-result"}
  {"activity": "m-bo-k3-activity", "by": "bo", "record": "m-bo-k3-result"}
  {"activity": "m-lab2-activity", "by": "lab-2", "record": "m-lab2-result"}

#### R3 capability and role grants: classified-as with a capability or social role, its context and interval
```
match $c isa classified-as (classified: $h, class: $k); $h has wm-id $hid; $k has wm-id $kid;
      { $k isa capability; } or { $k isa social-role; } or { $k isa category, has wm-id "agent"; };
      $a isa attestation (content: $c, attester: $who, context: $w), has polarity $pol,
         has valid-from-earliest $from; $who has wm-id $by; $w has wm-id $wid;
fetch { "holder": $hid, "class": $kid, "context": [ match $c links (context: $x); $x has wm-id $xid; fetch { "id": $xid }; ],
        "polarity": $pol, "from": $from, "until": $a.valid-to-earliest, "by": $by, "world": $wid };
```
  {"by": "system", "class": "agent", "context": [], "from": "2026-11-10T07:00:00.000000000+00:00", "holder": "ana", "polarity": true, "until": null, "world": "lab"}
  {"by": "system", "class": "agent", "context": [], "from": "2026-11-10T07:00:00.000000000+00:00", "holder": "bo", "polarity": true, "until": null, "world": "lab"}
  {"by": "system", "class": "agent", "context": [], "from": "2026-11-10T07:00:00.000000000+00:00", "holder": "tom", "polarity": true, "until": null, "world": "lab"}
  {"by": "system", "class": "analyst", "context": [{"id": "lab-1"}], "from": "2026-11-10T07:00:00.000000000+00:00", "holder": "ana", "polarity": true, "until": null, "world": "lab"}
  {"by": "system", "class": "analyst", "context": [{"id": "lab-1"}], "from": "2026-11-10T07:00:00.000000000+00:00", "holder": "bo", "polarity": true, "until": null, "world": "lab"}
  {"by": "system", "class": "can-measure-mass", "context": [], "from": "2026-11-10T07:00:00.000000000+00:00", "holder": "balance-b3", "polarity": true, "until": null, "world": "lab"}
  {"by": "system", "class": "can-measure-mass", "context": [], "from": "2026-11-10T07:00:00.000000000+00:00", "holder": "balance-b7", "polarity": true, "until": null, "world": "lab"}
  {"by": "system", "class": "can-measure-mass", "context": [], "from": "2026-11-10T07:00:00.000000000+00:00", "holder": "balance-b9", "polarity": true, "until": null, "world": "lab"}
  {"by": "system", "class": "can-weigh", "context": [{"id": "lab-1"}], "from": "2026-11-10T07:00:00.000000000+00:00", "holder": "ana", "polarity": true, "until": null, "world": "lab"}
  {"by": "system", "class": "can-weigh", "context": [{"id": "lab-1"}], "from": "2026-11-10T07:00:00.000000000+00:00", "holder": "bo", "polarity": true, "until": "2026-11-10T12:00:00.000000000+00:00", "world": "lab"}
  {"by": "system", "class": "can-weigh", "context": [{"id": "lab-1"}], "from": "2026-11-10T13:00:00.000000000+00:00", "holder": "tom", "polarity": true, "until": null, "world": "lab-plan-tom"}
