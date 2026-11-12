# Laboratory profile: sample 12, its sub-samples, calibration and interpretations (database 'wm-reference-laboratory')

Profiles installed: {'mechanical': '0.1', 'organisation': '0.1', 'laboratory': '0.1'}

## Part 1: judged answers (system perspective unless stated)

### Q1 Samples: provenance, accounts, occurrences, existence (16:00)
- s12-b is made from: [('s12-b', 's12-a', 'established', 'ASSERTED'), ('s12-a', 'sample-12', 'established', 'ASSERTED')]
- s12-b's established ancestry (routes on which every link is established): [('s12-b', 's12-a', [[['s12-b', 's12-a']]]), ('s12-a', 'sample-12', [[['s12-b', 's12-a'], ['s12-a', 'sample-12']]])]
- account ev-split-b (product s12-b, by ['bo']): accepted; occurrences [('o-split-b', 'accepted')]; claimed effects [('constitution', 'accepted'), ('existence', 'accepted')]
- account ev-sampling-1 (product s12-a, by ['ana']): accepted; occurrences [('o-sampling-1', 'not established')]; claimed effects [('constitution', 'accepted'), ('existence', 'accepted')]
- s12-c: accounts [('ev-split-c', 'not accepted', ['unreviewed', 'unreviewed'])]; made from nothing attested; existence attested: not established
- s12-a exists at 15:00: established [ASSERTED] (a portion: the 15:30 split ends it)
- s12-a exists at 16:00: expired [ASSERTED] (a portion: the 15:30 split ends it)
- s12-b location at 16:00: ['freezer-2'] [ASSERTED]

### Q2 The experiment and its documented steps
- o-exp-1 is an experiment: ASSERTED; steps rest on ['protocol-7']
  - o-sampling-1: ['ev-sampling-1'] by ['ana'] from 14:00; occurred (at its start): not established
  - o-weigh-late: ['m-ana-b3-late-activity'] by ['ana'] from 15:00; occurred (at its start): not established
  - o-split-b: ['ev-split-b'] by ['bo'] from 15:30; occurred (at its start): accepted

### Q3 Calibration status over time, by perspective, knowledge time and world
- balance-b3 at 09:00: established [ASSERTED]; certificates: cert-b3 (CAL-B3-2026-10) established
- balance-b3 at 15:00: expired [ASSERTED]; certificates: cert-b3 (CAL-B3-2026-10) expired
- balance-b7 at 10:00: disputed [DISPUTED]; certificates: cert-b7 (CAL-B7-2026-08) disputed
- balance-b9 at 12:00: not established [NOT_YET_KNOWN]; certificates: none recorded
- balance-b7 at 10:00, the quality office's perspective: denied [ASSERTED]; certificates: cert-b7 (CAL-B7-2026-08) denied
- balance-b7 at 10:00, as known before the quality office's denial: established [ASSERTED]; certificates: cert-b7 (CAL-B7-2026-08) established
- balance-b3 at 15:00 in 'lab-plan-recal': established [STIPULATED]; certificates: cert-b3 (CAL-B3-2026-10) expired, cert-b3-r (CAL-B3-2026-11) established

### Q4 Each measurement: stated reference beside the attested calibration (nothing is invalidated)
- m-ana-b3-corr-result: balance-b3 at 09:00; stated 'CAL-B3-2026-10'; attested established; reference check: matches a certificate [('cert-b3', 'established')]; acceptance accepted, usable True
- m-ana-b3-late-result: balance-b3 at 15:00; stated 'CAL-B3-2026-10'; attested expired; reference check: matches a certificate [('cert-b3', 'expired')]; acceptance accepted, usable True
- m-ana-b3-result: balance-b3 at 09:00; stated 'CAL-B3-2026-10'; attested established; reference check: matches a certificate [('cert-b3', 'established')]; acceptance superseded, usable False
- m-ana-b9-result: balance-b9 at 12:00; stated None; attested not established; reference check: no reference stated []; acceptance accepted, usable True
- m-bo-b7-result: balance-b7 at 10:00; stated 'CAL-B7-2026-09'; attested disputed; reference check: no certificate with the stated reference []; acceptance accepted, usable True
- m-bo-k3-result: balance-b7 at 13:00; stated None; attested disputed; reference check: no reference stated []; acceptance accepted, usable True
- m-lab2-result: no instrument; acceptance unreviewed, usable False
- compared at 16:00: 5 measurements; the 15:00 weighing on an expired calibration is among them: True (calibration plays no part in comparison)

### Q5 Interpretations: testimony, hypothesis, rivals (each judged on its own)
- m-ana-b9-result: ana says sample-12 is hydrated: hypothesis, accepted, supports answer False; content established [ASSERTED]
- m-lab2-result: lab-2 says sample-12 is anhydrous: testimony, unreviewed, supports answer False; content not established [UNKNOWN]
- m-bo-k3-result: bo says sample-12 is hydrated: testimony, accepted, supports answer True; content established [ASSERTED]
- formal derivation: not a formal derivation: no named rule or premises are recorded (Stage E, DI-7)
- system: hydrated ASSERTED, anhydrous UNKNOWN
- qa: hydrated ASSERTED, anhydrous ASSERTED
- lab-2: hydrated UNKNOWN, anhydrous ASSERTED

## Part 2: raw TypeQL against the stored records (not judged)

### R1 samples and what each is said to be made from (source, interval, acceptance verdicts)
```
match $x isa sample, has wm-id $xid; $c isa constitution (constituted: $x, constituent: $y); $y has wm-id $yid;
  $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "sample": $xid, "from": $yid, "by": $by, "valid from": $a.valid-from-earliest,
        "verdicts": [ match $v isa acceptance (accepted: $a, holder: $h), has verdict $vd; $h has wm-id $hid;
                      fetch { "holder": $hid, "verdict": $vd }; ] };
```
  {"by": "ana", "from": "sample-12", "sample": "s12-a", "valid from": "2026-11-10T14:10:00.000000000+00:00", "verdicts": [{"holder": "system", "verdict": "accepted"}]}
  {"by": "system", "from": "s12-a", "sample": "s12-b", "valid from": "2026-11-10T15:40:00.000000000+00:00", "verdicts": []}

### R2 sampling accounts: sampler, specimen, product, source, and the occurrences they are said to describe
```
match $e isa sampling (sampler: $s, sampled: $f, product: $p), has wm-id $eid; $s has wm-id $sid;
  $f has wm-id $fid; $p has wm-id $pid; $a isa attestation (content: $e, attester: $who); $who has wm-id $by;
fetch { "account": $eid, "sampler": $sid, "from": $fid, "product": $pid, "by": $by,
        "describes": [ match describes (description: $e, occurrence: $o); $o has wm-id $oid; fetch { "id": $oid }; ] };
```
  {"account": "ev-sampling-1", "by": "ana", "describes": [{"id": "o-sampling-1"}], "from": "sample-12", "product": "s12-a", "sampler": "ana"}
  {"account": "ev-split-b", "by": "bo", "describes": [{"id": "o-split-b"}], "from": "s12-a", "product": "s12-b", "sampler": "bo"}
  {"account": "ev-split-c", "by": "bo", "describes": [{"id": "o-split-c"}], "from": "s12-a", "product": "s12-c", "sampler": "bo"}

### R3 calibration attestations: certificate (and its own reference), instrument, source, polarity, valid time
```
match $c isa calibration-of (certificate: $k, calibrated: $i); $k has wm-id $kid; $i has wm-id $iid;
  $a isa attestation (content: $c, attester: $who, context: $w), has polarity $pol; $who has wm-id $by;
  $w has wm-id $wid;
fetch { "certificate": $kid, "reference": $k.calibration-ref, "instrument": $iid, "by": $by, "polarity": $pol,
        "world": $wid, "from": $a.valid-from-earliest, "until": $a.valid-to-earliest,
        "rests on": [ match rests-on (attestation: $a, record: $r); $r has wm-id $rid; fetch { "id": $rid }; ] };
```
  {"by": "cal-lab", "certificate": "cert-b3", "from": "2026-11-01T00:00:00.000000000+00:00", "instrument": "balance-b3", "polarity": true, "reference": "CAL-B3-2026-10", "rests on": [{"id": "cert-b3"}], "until": "2026-11-10T10:00:00.000000000+00:00", "world": "lab"}
  {"by": "cal-lab", "certificate": "cert-b7", "from": "2026-11-01T00:00:00.000000000+00:00", "instrument": "balance-b7", "polarity": true, "reference": "CAL-B7-2026-08", "rests on": [{"id": "cert-b7"}], "until": null, "world": "lab"}
  {"by": "qa", "certificate": "cert-b7", "from": "2026-11-01T00:00:00.000000000+00:00", "instrument": "balance-b7", "polarity": false, "reference": "CAL-B7-2026-08", "rests on": [{"id": "cert-b7"}], "until": null, "world": "lab"}
  {"by": "system", "certificate": "cert-b3-r", "from": "2026-11-10T09:30:00.000000000+00:00", "instrument": "balance-b3", "polarity": true, "reference": "CAL-B3-2026-11", "rests on": [{"id": "cert-b3-r"}], "until": null, "world": "lab-plan-recal"}

### R4 result records: the calibration reference each states, and the instrument of the activity that produced it
```
match $r isa information-object, has wm-id $rid, has raw-value $v; $p isa produced (activity: $act, result: $r);
  $act has wm-id $aid; try { $act links (instrument: $i); $i has wm-id $iid; };
fetch { "record": $rid, "value": $v, "stated reference": $r.calibration-ref, "activity": $aid, "instrument": $iid };
```
  {"activity": "m-ana-b3-activity", "instrument": "balance-b3", "record": "m-ana-b3-result", "stated reference": "CAL-B3-2026-10", "value": 3.51}
  {"activity": "m-ana-b3-corr-activity", "instrument": "balance-b3", "record": "m-ana-b3-corr-result", "stated reference": "CAL-B3-2026-10", "value": 3.53}
  {"activity": "m-ana-b3-late-activity", "instrument": "balance-b3", "record": "m-ana-b3-late-result", "stated reference": "CAL-B3-2026-10", "value": 3.52}
  {"activity": "m-ana-b9-activity", "instrument": "balance-b9", "record": "m-ana-b9-result", "stated reference": null, "value": 3.53}
  {"activity": "m-bo-b7-activity", "instrument": "balance-b7", "record": "m-bo-b7-result", "stated reference": "CAL-B7-2026-09", "value": 3490.0}
  {"activity": "m-bo-k3-activity", "instrument": "balance-b7", "record": "m-bo-k3-result", "stated reference": null, "value": 3.5}
  {"activity": "m-lab2-activity", "instrument": null, "record": "m-lab2-result", "stated reference": null, "value": 3.7}

### R5 interpretations resting on result records: content, source, stance, basis
```
match $r isa information-object, has wm-id $rid; rests-on (attestation: $a, record: $r);
  $a isa attestation (content: $c, attester: $who), has stance $st, has basis $bs; $who has wm-id $by;
  $c isa classified-as (classified: $x, class: $k); $x has wm-id $xid; $k has wm-id $kid;
fetch { "record": $rid, "classified": $xid, "as": $kid, "by": $by, "stance": $st, "basis": $bs };
```
  {"as": "anhydrous", "basis": "testimony", "by": "lab-2", "classified": "sample-12", "record": "m-lab2-result", "stance": "asserts"}
  {"as": "hydrated", "basis": "testimony", "by": "ana", "classified": "sample-12", "record": "m-ana-b9-result", "stance": "hypothesises"}
  {"as": "hydrated", "basis": "testimony", "by": "bo", "classified": "sample-12", "record": "m-bo-k3-result", "stance": "asserts"}
  {"as": "laboratory:experiment", "basis": "testimony", "by": "system", "classified": "o-exp-1", "record": "protocol-7", "stance": "asserts"}
