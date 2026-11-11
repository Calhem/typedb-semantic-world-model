# Organisational profile: Acme and depot 7 (database 'wm-reference-organisation')

Profiles installed: {'organisation': '0.1'}

## Part 1: judged answers (system perspective unless stated)

### Q1 Employment and membership
- acme employs, day 5: [('bea', 'established', 'ASSERTED'), ('cal', 'established', 'ASSERTED'), ('dan', 'established', 'ASSERTED'), ('eve', 'established', 'ASSERTED')]
- eve's employment on day 25 (ended day 20): [('acme', 'expired')]
- bea member of depot-7: ASSERTED True
- cal member of depot-7: ASSERTED True
- dan member of depot-7: NOT_YET_KNOWN None

### Q2 Contextual appointments: site manager of depot-7 (exclusive) and safety officer (not exclusive)
- site manager, day 5: holders ['bea'] [ASSERTED]; appointments: bea established, cal not established
- site manager, day 9: holders ['bea', 'cal'] [DISPUTED]; appointments: bea established, cal established; CONFLICT: constraint ['att:5642585d22504d90'], appointments [('bea', ['att:24b455fe025c4c2e']), ('cal', ['att:7567cdb3373a4099'])]
- site manager, day 12: holders ['cal'] [ASSERTED]; appointments: bea expired, cal established
- safety officer, day 5: holders ['dan', 'eve'] [ASSERTED]; appointments: dan established, eve established
- offices of cal, day 9: [('site-manager', 'depot-7', 'established', 'DISPUTED')]
- offices of fay, day 7 (an appointment event exists, no appointment claim): []
- is eve (never mentioned for it) site manager on day 5? NOT_YET_KNOWN None: not inferred false

### Q3 Authority, capability and office (independent)
- bea: authority established (grants: grantor, reported by: [('acme', ['hr'], 'established')]; grantor entitlement not assessed); capability not established
- dan: authority established (grants: grantor, reported by: [('acme', ['hr'], 'established')]; grantor entitlement not assessed); capability not established
- eve: authority not established (grants: grantor, reported by: []; grantor entitlement not assessed); capability established
- cal: authority not established (grants: grantor, reported by: []; grantor entitlement not assessed); capability not established
- was acme itself authorised to grant? not established [NOT_YET_KNOWN]: not inferred from its grants

### Q4 Acts in office (occurrence judged apart)
- ev-bea-signs: account accepted; occurrences none claimed; office established [ASSERTED]; authority established; capability not established; agent established
- ev-cal-signs: account accepted; occurrences [('o-signoff-9', 'not established')]; office established [DISPUTED]; authority not established; capability not established; agent established

### Q5 Perspectives, historical knowledge and a hypothetical reorganisation
- site manager day 9, the auditor's perspective: holders [] [UNKNOWN]; appointments: bea not established, cal denied
- site manager day 9, as known before cal's appointment was recorded: holders ['bea'] [ASSERTED]; appointments: bea established
- site manager day 12 in 'org-plan-reorg': holders ['dan'] [STIPULATED]; appointments: bea expired, cal denied, dan established
- site manager day 12, actual: holders ['cal'] [ASSERTED]; appointments: bea expired, cal established

## Part 2: raw TypeQL against the stored records (not judged)

### R1 employment and membership, with source and interval
```
match { $c isa employment (employer: $x, employee: $y); } or { $c isa member-of (group: $x, member: $y); };
  $c isa! $t; $x has wm-id $xid; $y has wm-id $yid;
  $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "type": $t, "of": $xid, "who": $yid, "by": $by, "from": $a.valid-from-earliest, "until": $a.valid-to-earliest };
```
  {"by": "hr", "from": "2026-11-01T09:00:00.000000000+00:00", "of": "acme", "type": {"kind": "relation", "label": "employment"}, "until": "2026-11-20T09:00:00.000000000+00:00", "who": "eve"}
  {"by": "hr", "from": "2026-11-01T09:00:00.000000000+00:00", "of": "acme", "type": {"kind": "relation", "label": "employment"}, "until": null, "who": "bea"}
  {"by": "hr", "from": "2026-11-01T09:00:00.000000000+00:00", "of": "acme", "type": {"kind": "relation", "label": "employment"}, "until": null, "who": "cal"}
  {"by": "hr", "from": "2026-11-01T09:00:00.000000000+00:00", "of": "acme", "type": {"kind": "relation", "label": "employment"}, "until": null, "who": "dan"}
  {"by": "system", "from": "2026-11-01T09:00:00.000000000+00:00", "of": "depot-7", "type": {"kind": "relation", "label": "member-of"}, "until": null, "who": "bea"}
  {"by": "system", "from": "2026-11-01T09:00:00.000000000+00:00", "of": "depot-7", "type": {"kind": "relation", "label": "member-of"}, "until": null, "who": "cal"}

### R2 office appointments: holder, office, context, source, polarity, interval, acceptance verdicts
```
match $c isa office-holding (classified: $p, class: $k, context: $x); $p has wm-id $pid; $k has wm-id $kid;
  $x has wm-id $xid; $a isa attestation (content: $c, attester: $who, context: $w), has polarity $pol;
  $who has wm-id $by; $w has wm-id $wid;
fetch { "holder": $pid, "office": $kid, "context": $xid, "by": $by, "polarity": $pol, "world": $wid,
        "from": $a.valid-from-earliest, "until": $a.valid-to-earliest,
        "verdicts": [ match $v isa acceptance (accepted: $a, holder: $h), has verdict $vd; $h has wm-id $hid;
                      fetch { "holder": $hid, "verdict": $vd }; ] };
```
  {"by": "acme", "context": "depot-7", "from": "2026-11-01T09:00:00.000000000+00:00", "holder": "bea", "office": "site-manager", "polarity": true, "until": "2026-11-10T09:00:00.000000000+00:00", "verdicts": [{"holder": "system", "verdict": "accepted"}], "world": "org"}
  {"by": "acme", "context": "depot-7", "from": "2026-11-01T09:00:00.000000000+00:00", "holder": "dan", "office": "safety-officer", "polarity": true, "until": null, "verdicts": [{"holder": "system", "verdict": "accepted"}], "world": "org"}
  {"by": "acme", "context": "depot-7", "from": "2026-11-03T09:00:00.000000000+00:00", "holder": "eve", "office": "safety-officer", "polarity": true, "until": null, "verdicts": [{"holder": "system", "verdict": "accepted"}], "world": "org"}
  {"by": "acme", "context": "depot-7", "from": "2026-11-08T09:00:00.000000000+00:00", "holder": "cal", "office": "site-manager", "polarity": true, "until": null, "verdicts": [{"holder": "system", "verdict": "accepted"}], "world": "org"}
  {"by": "auditor", "context": "depot-7", "from": "2026-11-08T09:00:00.000000000+00:00", "holder": "cal", "office": "site-manager", "polarity": false, "until": null, "verdicts": [], "world": "org"}
  {"by": "system", "context": "depot-7", "from": "2026-11-11T09:00:00.000000000+00:00", "holder": "cal", "office": "site-manager", "polarity": false, "until": null, "verdicts": [], "world": "org-plan-reorg"}
  {"by": "system", "context": "depot-7", "from": "2026-11-11T09:00:00.000000000+00:00", "holder": "dan", "office": "site-manager", "polarity": true, "until": null, "verdicts": [], "world": "org-plan-reorg"}

### R3 single-holder constraints
```
match $c isa exclusive-office (office: $k, context: $x); $k has wm-id $kid; $x has wm-id $xid;
  $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "office": $kid, "context": $xid, "by": $by, "from": $a.valid-from-earliest };
```
  {"by": "acme", "context": "depot-7", "from": "2026-11-01T09:00:00.000000000+00:00", "office": "site-manager"}

### R4 authorisations: grantor and reporting source side by side
```
match $c isa authorisation (grantor: $g, holder: $h, power: $p, scope: $s); $g has wm-id $gid; $h has wm-id $hid;
  $p has wm-id $pid; $s has wm-id $sid; $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "grantor": $gid, "holder": $hid, "power": $pid, "scope": $sid, "reported by": $by };
```
  {"grantor": "acme", "holder": "bea", "power": "can-sign-off", "reported by": "hr", "scope": "depot-7"}
  {"grantor": "acme", "holder": "dan", "power": "can-sign-off", "reported by": "hr", "scope": "depot-7"}

### R5 official acts and the occurrences they are said to describe
```
match $e isa official-act (official: $p, office: $k, office-context: $x), has wm-id $eid; $p has wm-id $pid;
  $k has wm-id $kid; $x has wm-id $xid; $a isa attestation (content: $e, attester: $who); $who has wm-id $by;
fetch { "act": $eid, "official": $pid, "office": $kid, "context": $xid, "by": $by,
        "describes": [ match describes (description: $e, occurrence: $o); $o has wm-id $oid; fetch { "id": $oid }; ] };
```
  {"act": "ev-bea-signs", "by": "bea", "context": "depot-7", "describes": [], "office": "site-manager", "official": "bea"}
  {"act": "ev-cal-signs", "by": "cal", "context": "depot-7", "describes": [{"id": "o-signoff-9"}], "office": "site-manager", "official": "cal"}
