## per call: median ms of the two passes averaged: total | open | first | stream | python ; queries, transactions, rows
### parts actual bay-1
| db | total | open | first | stream | python | queries | tx | rows |
|---|---|---|---|---|---|---|---|---|
| worlds-1 | 18.5 | 1.3 | 7.0 | 7.3 | 2.8 | 11 | 2 | 75 |
| worlds-5 | 147.5 | 1.7 | 8.9 | 133.2 | 3.2 | 11 | 2 | 75 |
| worlds-10 | 171.6 | 1.5 | 15.7 | 153.2 | 3.3 | 11 | 2 | 75 |
| perspectives-5 | 35.7 | 1.6 | 15.5 | 15.4 | 3.0 | 11 | 2 | 75 |
| perspectives-10 | 91.1 | 3.1 | 54.6 | 26.6 | 4.5 | 11 | 2 | 75 |

### parts actual gbx-100
| db | total | open | first | stream | python | queries | tx | rows |
|---|---|---|---|---|---|---|---|---|
| worlds-1 | 19.8 | 1.5 | 7.5 | 7.5 | 2.8 | 11 | 2 | 75 |
| worlds-5 | 155.4 | 1.8 | 8.6 | 139.6 | 3.2 | 11 | 2 | 75 |
| worlds-10 | 52.8 | 1.7 | 16.3 | 31.5 | 3.1 | 11 | 2 | 75 |
| perspectives-5 | 27.2 | 1.5 | 7.4 | 15.2 | 2.9 | 11 | 2 | 75 |
| perspectives-10 | 63.5 | 3.1 | 16.3 | 29.5 | 4.2 | 11 | 2 | 75 |

### parts plan-relubricate-only gbx-100
| db | total | open | first | stream | python | queries | tx | rows |
|---|---|---|---|---|---|---|---|---|
| worlds-1 | 97.0 | 1.6 | 72.6 | 15.7 | 3.6 | 21 | 2 | 74 |
| worlds-5 | 204.7 | 1.6 | 109.0 | 91.0 | 3.9 | 21 | 2 | 74 |
| worlds-10 | 301.6 | 1.9 | 111.5 | 75.2 | 4.1 | 21 | 2 | 74 |
| perspectives-5 | 133.2 | 1.6 | 99.7 | 27.0 | 3.8 | 21 | 2 | 74 |
| perspectives-10 | 272.4 | 3.2 | 211.3 | 53.9 | 5.2 | 21 | 2 | 74 |

### occurrence actual o-repair
| db | total | open | first | stream | python | queries | tx | rows |
|---|---|---|---|---|---|---|---|---|
| worlds-1 | 74.6 | 7.0 | 34.3 | 24.4 | 9.3 | 53 | 10 | 106 |
| worlds-5 | 112.0 | 8.6 | 41.4 | 50.7 | 11.1 | 53 | 10 | 106 |
| worlds-10 | 163.7 | 8.7 | 50.1 | 93.3 | 11.7 | 53 | 10 | 106 |
| perspectives-5 | 152.0 | 8.1 | 42.9 | 80.1 | 20.4 | 53 | 10 | 842 |
| perspectives-10 | 322.6 | 16.5 | 85.9 | 184.9 | 41.5 | 53 | 10 | 1762 |

### occurrence actual o-test-run
| db | total | open | first | stream | python | queries | tx | rows |
|---|---|---|---|---|---|---|---|---|
| worlds-1 | 81.2 | 7.3 | 39.1 | 26.6 | 9.7 | 57 | 10 | 110 |
| worlds-5 | 112.1 | 7.2 | 38.9 | 54.5 | 10.3 | 57 | 10 | 110 |
| worlds-10 | 160.0 | 8.8 | 46.6 | 91.8 | 11.3 | 57 | 10 | 110 |
| perspectives-5 | 160.6 | 9.0 | 45.8 | 85.9 | 20.7 | 57 | 10 | 846 |
| perspectives-10 | 486.9 | 16.1 | 96.2 | 265.4 | 44.4 | 57 | 10 | 1766 |

### occurrence lab o-split-b
| db | total | open | first | stream | python | queries | tx | rows |
|---|---|---|---|---|---|---|---|---|
| worlds-1 | 73.3 | 6.9 | 34.6 | 21.1 | 9.1 | 53 | 10 | 76 |
| worlds-5 | 99.6 | 7.1 | 36.5 | 46.1 | 9.4 | 53 | 10 | 76 |
| worlds-10 | 137.3 | 8.0 | 42.2 | 76.2 | 10.4 | 53 | 10 | 76 |
| perspectives-5 | 127.4 | 8.2 | 40.4 | 64.0 | 14.7 | 53 | 10 | 444 |
| perspectives-10 | 299.8 | 15.4 | 96.5 | 156.6 | 32.6 | 53 | 10 | 904 |

### where actual gbx-100 f-workshop
| db | total | open | first | stream | python | queries | tx | rows |
|---|---|---|---|---|---|---|---|---|
| worlds-1 | 286.2 | 6.0 | 222.8 | 47.6 | 10.2 | 39 | 8 | 159 |
| worlds-5 | 223.0 | 6.0 | 133.1 | 72.8 | 10.5 | 39 | 8 | 159 |
| worlds-10 | 547.8 | 7.6 | 110.4 | 444.8 | 14.2 | 39 | 8 | 159 |
| perspectives-5 | 206.2 | 6.7 | 116.8 | 74.5 | 10.8 | 39 | 8 | 159 |
| perspectives-10 | 335.9 | 9.4 | 178.9 | 118.2 | 19.9 | 39 | 8 | 159 |

### value_at actual gbx-100
| db | total | open | first | stream | python | queries | tx | rows |
|---|---|---|---|---|---|---|---|---|
| worlds-1 | 16.6 | 2.2 | 7.9 | 3.9 | 2.1 | 11 | 3 | 3 |
| worlds-5 | 21.4 | 2.3 | 8.4 | 8.9 | 2.3 | 11 | 3 | 3 |
| worlds-10 | 30.7 | 2.6 | 10.6 | 14.4 | 2.3 | 11 | 3 | 3 |
| perspectives-5 | 23.4 | 2.4 | 10.3 | 8.5 | 2.3 | 11 | 3 | 3 |
| perspectives-10 | 40.4 | 4.0 | 17.3 | 17.1 | 4.1 | 11 | 3 | 3 |

### effects_of actual ev-worklog-replacement
| db | total | open | first | stream | python | queries | tx | rows |
|---|---|---|---|---|---|---|---|---|
| worlds-1 | 303.7 | 24.7 | 144.7 | 101.0 | 34.1 | 197 | 33 | 304 |
| worlds-5 | 408.0 | 25.2 | 145.7 | 209.1 | 32.2 | 197 | 33 | 304 |
| worlds-10 | 635.0 | 29.8 | 185.9 | 378.6 | 39.5 | 197 | 33 | 304 |
| perspectives-5 | 449.3 | 24.7 | 150.3 | 230.9 | 43.2 | 197 | 33 | 1040 |
| perspectives-10 | 953.5 | 50.2 | 352.6 | 466.7 | 86.7 | 197 | 33 | 1960 |

### provenance lab s12-b
| db | total | open | first | stream | python | queries | tx | rows |
|---|---|---|---|---|---|---|---|---|
| worlds-1 | 518.1 | 59.4 | 235.8 | 149.7 | 70.5 | 336 | 80 | 657 |
| worlds-5 | 670.0 | 60.9 | 243.2 | 288.6 | 72.8 | 336 | 80 | 657 |
| worlds-10 | 946.0 | 68.2 | 306.1 | 489.7 | 86.4 | 336 | 80 | 657 |
| perspectives-5 | 792.2 | 60.4 | 262.6 | 374.1 | 102.3 | 336 | 80 | 2865 |
| perspectives-10 | 1677.4 | 119.8 | 518.1 | 819.0 | 200.7 | 336 | 80 | 5625 |

## pass agreement: total ms pass1 / pass2
- parts actual bay-1: worlds-1 20/17; worlds-5 148/147; worlds-10 302/41; perspectives-5 44/28; perspectives-10 146/36
- parts actual gbx-100: worlds-1 21/18; worlds-5 151/160; worlds-10 64/42; perspectives-5 27/28; perspectives-10 87/40
- parts plan-relubricate-only gbx-100: worlds-1 149/45; worlds-5 351/58; worlds-10 508/95; perspectives-5 216/50; perspectives-10 444/101
- occurrence actual o-repair: worlds-1 83/66; worlds-5 114/110; worlds-10 163/165; perspectives-5 154/150; perspectives-10 421/225
- occurrence actual o-test-run: worlds-1 85/78; worlds-5 118/106; worlds-10 175/145; perspectives-5 157/164; perspectives-10 738/235
- occurrence lab o-split-b: worlds-1 79/68; worlds-5 103/96; worlds-10 148/127; perspectives-5 131/124; perspectives-10 425/175
- where actual gbx-100 f-workshop: worlds-1 165/408; worlds-5 136/310; worlds-10 480/616; perspectives-5 130/282; perspectives-10 351/321
- value_at actual gbx-100: worlds-1 17/16; worlds-5 22/21; worlds-10 29/33; perspectives-5 21/26; perspectives-10 56/25
- effects_of actual ev-worklog-replacement: worlds-1 331/276; worlds-5 425/391; worlds-10 625/645; perspectives-5 438/460; perspectives-10 1290/617
- provenance lab s12-b: worlds-1 574/462; worlds-5 697/644; worlds-10 1047/845; perspectives-5 780/805; perspectives-10 2190/1164

## experiments (rows, median ms; pass1 / pass2)
| query | worlds-1 | worlds-5 | worlds-10 | perspectives-5 | perspectives-10 |
|---|---|---|---|---|---|
| attestations in the database | 322 rows, 5.3/6.0 ms | 1633 rows, 33.2/25.2 ms | 3272 rows, 54.1/57.7 ms | 1522 rows, 26.7/23.6 ms | 3022 rows, 72.4/61.0 ms |
| attestations in world actual | 198 rows, 3.6/3.9 ms | 198 rows, 5.0/3.6 ms | 198 rows, 4.3/13.2 ms | 798 rows, 14.8/13.3 ms | 1548 rows, 30.5/30.3 ms |
| part-of attestations in the database (any world) | 28 rows, 1.0/0.9 ms | 28 rows, 1.9/1.7 ms | 28 rows, 3.0/5.8 ms | 28 rows, 2.0/1.6 ms | 28 rows, 2.8/2.6 ms |
| part-of head as written (world, attestation, type) | 23 rows, 1.2/1.1 ms | 23 rows, 4.1/2.0 ms | 23 rows, 3.5/3.6 ms | 23 rows, 3.5/2.0 ms | 23 rows, 3.2/3.0 ms |
| part-of head, world's attestations first | 23 rows, 1.1/1.1 ms | 23 rows, 1.5/0.9 ms | 23 rows, 1.1/1.0 ms | 23 rows, 2.9/1.2 ms | 23 rows, 1.6/1.8 ms |
| part-of head, part-of contents first | 23 rows, 1.0/0.9 ms | 23 rows, 1.0/0.7 ms | 23 rows, 1.2/0.8 ms | 23 rows, 1.7/1.4 ms | 23 rows, 1.9/1.6 ms |
| part-of head + role players (as _level's role query) | 46 rows, 2.0/1.9 ms | 46 rows, 2.9/2.9 ms | 46 rows, 4.1/3.9 ms | 46 rows, 5.1/2.6 ms | 46 rows, 3.8/3.8 ms |
| same-as head (identity load) in actual | 0 rows, 0.9/0.8 ms | 0 rows, 1.9/1.8 ms | 0 rows, 3.0/2.6 ms | 0 rows, 4.0/1.6 ms | 0 rows, 2.8/2.6 ms |
| describes head in actual | 11 rows, 1.1/1.0 ms | 11 rows, 2.1/1.9 ms | 11 rows, 2.9/2.8 ms | 11 rows, 3.8/1.7 ms | 11 rows, 3.8/2.9 ms |
| event accounts in actual | 14 rows, 1.0/0.7 ms | 14 rows, 0.9/0.9 ms | 14 rows, 0.9/0.7 ms | 198 rows, 8.2/4.9 ms | 428 rows, 11.4/10.0 ms |

## per shape for parts actual bay-1 and occurrence actual o-repair (pass1): rows/exec, first ms, stream ms per db
### parts actual bay-1
- x1 [0.0r 0.8+0.2 | 0.0r 0.9+116.4 | 0.0r 14.8+252.1 | 0.0r 13.4+0.7 | 0.0r 27.2+0.5] +w10 212.4 +p10 27.7 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa part-of; $su isa supersession (old: $a, new: $n); $n has wm-id $nid; $nacc isa acceptance (holder: $nh, accepte
- x1 [0.0r 0.7+0.3 | 0.0r 0.8+1.2 | 0.0r 0.8+2.2 | 0.0r 0.7+1.1 | 0.0r 30.1+1.7] +w10 4.8 +p10 35.2 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $su isa supersession (old: $a, new: $n), has recorded-at $srec; $n has wm-id $nid, has stance $nst; $n
- x1 [1.0r 0.7+1.0 | 1.0r 0.8+3.2 | 1.0r 0.9+5.5 | 1.0r 0.7+2.8 | 1.0r 3.6+5.3] +w10 6.9 +p10 20.5 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa part-of; $su isa supersession (old: $a, new: $n), has recorded-at $srec; $n has wm-id $nid, has stance $nst; $n
- x1 [0.0r 0.7+0.4 | 0.0r 0.7+1.1 | 0.0r 0.9+2.1 | 0.0r 0.7+1.1 | 0.0r 13.7+2.4] +w10 2.6 +p10 19.7 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $acc isa acceptance (holder: $h, accepted: $a), has verdict $vd, has recorded-at $vrec; $h has wm-id =
- x1 [0.0r 0.6+0.3 | 0.0r 0.8+1.1 | 0.0r 0.9+2.0 | 0.0r 0.7+1.1 | 0.0r 5.7+1.9] +w10 2.4 +p10 9.5 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $c links ($role: $x); $x has wm-id $xid;
- x1 [46.0r 0.7+1.9 | 46.0r 0.9+2.9 | 46.0r 0.8+3.5 | 46.0r 0.9+2.6 | 46.0r 3.3+3.2] +w10 3.2 +p10 6.9 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa part-of; $c links ($role: $x); $x has wm-id $xid;
- x1 [23.0r 0.6+2.1 | 23.0r 0.7+3.2 | 23.0r 0.8+4.2 | 23.0r 0.6+2.9 | 23.0r 3.0+4.5] +w10 6.6 +p10 5.8 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa part-of; $who has wm-id $wid; $c isa! $t; $c has proposition-key $ck; fetch { ?: $aid, ?: $wid, ?: $t, ?: $ck, 
- x1 [5.0r 0.8+0.7 | 5.0r 0.9+1.4 | 5.0r 0.9+2.4 | 5.0r 0.9+1.5 | 5.0r 2.6+2.5] +w10 3.1 +p10 5.4 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa part-of; $acc isa acceptance (holder: $h, accepted: $a), has verdict $vd, has recorded-at $vrec; $h has wm-id =

### occurrence actual o-repair
- x1 [46.0r 0.6+1.9 | 46.0r 0.6+1.7 | 46.0r 0.7+2.0 | 598.0r 0.9+19.4 | 1288.0r 1.8+51.8] +w10 3.9 +p10 72.5 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa event; $c links ($role: $x); $x has wm-id $xid;
- x1 [14.0r 0.7+1.6 | 14.0r 0.6+1.7 | 14.0r 0.8+1.8 | 198.0r 0.6+13.8 | 428.0r 4.9+51.5] +w10 3.0 +p10 56.7 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa event; $who has wm-id $wid; $c isa! $t; $c has wm-id $ck; fetch { ?: $aid, ?: $wid, ?: $t, ?: $ck, ?: $rec, ?: 
- x6 [0.0r 0.6+0.4 | 0.0r 0.7+1.2 | 0.0r 1.0+2.4 | 0.0r 0.8+1.2 | 0.0r 2.3+2.8] +w10 17.2 +p10 40.1 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $su isa supersession (old: $a, new: $n), has recorded-
- x6 [0.0r 0.6+0.4 | 0.0r 0.7+1.1 | 0.0r 0.9+2.2 | 0.0r 0.7+1.1 | 0.0r 1.9+3.3] +w10 15.5 +p10 37.0 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $acc isa acceptance (holder: $h, accepted: $a), has ve
- x6 [0.0r 0.7+0.3 | 0.0r 0.7+1.2 | 0.0r 0.9+2.2 | 0.0r 0.7+1.1 | 0.0r 1.9+2.7] +w10 14.9 +p10 30.5 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); try { $c links ($role: $x); $x has wm-id $xid; };
- x6 [0.0r 0.7+0.3 | 0.0r 0.7+1.2 | 0.0r 0.9+2.5 | 0.0r 0.7+1.2 | 0.0r 1.9+2.6] +w10 19.7 +p10 29.1 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $who has wm-id $wid; $c isa! $t; $c has proposition-ke
- x8 [0.0r 0.7+0.1 | 0.0r 0.7+0.1 | 0.0r 0.9+0.2 | 0.0r 0.7+0.1 | 0.0r 1.9+0.2] +w10 7.1 +p10 15.6 ms/round :: match $v isa world, has wm-id == $world; $br isa branching (base: $b, variant: $v), has branch-at $at, has knowledge-at $kat, has recorded-at $rec; $b has wm-id $bid;
- x2 [1.0r 0.6+0.9 | 1.0r 0.8+1.6 | 1.0r 0.8+2.8 | 1.0r 0.7+1.5 | 1.0r 2.5+2.8] +w10 6.4 +p10 10.9 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa describes; $subj has wm-id == $sid; $c links ($kr: $subj); $acc isa acceptance (holder: $h, accepted: $a), has 

### where actual gbx-100 f-workshop
- x1 [0.0r 0.9+0.4 | 0.0r 0.8+2.4 | 0.0r 1.3+289.3 | 0.0r 0.8+8.7 | 0.0r 1.8+5.2] +w10 312.4 +p10 8.3 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa frame-transform; { not { $a has valid-from-latest $s0; }; } or { $a has valid-from-latest $s1; $s1 <= $at; }; $
- x1 [2.0r 0.8+2.2 | 2.0r 1.1+4.6 | 2.0r 1.3+8.3 | 2.0r 0.8+4.3 | 2.0r 4.0+17.6] +w10 8.2 +p10 35.9 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $subj has wm-id == $sid; $c links ($kr: $subj); { not { $a has valid-from-latest $s0; }; } or { $a has valid-from-late
- x1 [11.0r 0.8+4.3 | 11.0r 0.9+4.2 | 11.0r 2.8+5.2 | 11.0r 0.9+4.3 | 11.0r 3.9+10.4] +w10 3.1 +p10 17.0 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $subj has wm-id == $sid; $c links ($kr: $subj); { not { $a has valid-from-latest $s0; }; } or { $a has valid-from-late
- x1 [76.0r 0.6+12.3 | 76.0r 0.7+12.9 | 76.0r 1.3+20.3 | 76.0r 1.1+12.7 | 76.0r 2.0+24.3] +w10 13.5 +p10 14.0 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $subj has wm-id == $sid; $c links ($kr: $subj); { not { $a has valid-from-latest $s0; }; } or { $a has valid-from-late
- x1 [31.0r 0.7+9.9 | 31.0r 0.7+10.2 | 31.0r 0.9+11.2 | 31.0r 0.9+9.9 | 31.0r 5.6+12.8] +w10 5.4 +p10 13.4 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $subj has wm-id == $sid; $c links ($kr: $subj); { not { $a has valid-from-latest $s0; }; } or { $a has valid-from-late
- x2 [0.0r 0.6+0.4 | 0.0r 0.7+1.3 | 0.0r 0.7+2.4 | 0.0r 0.6+1.2 | 0.0r 2.1+3.1] +w10 4.2 +p10 13.2 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $who has wm-id $wid; $c isa! $t; $c has proposition-ke
- x6 [0.0r 0.7+0.1 | 0.0r 0.7+0.1 | 0.0r 0.8+0.1 | 0.0r 0.7+0.1 | 0.0r 1.6+0.2] +w10 1.6 +p10 11.5 ms/round :: match $v isa world, has wm-id == $world; $br isa branching (base: $b, variant: $v), has branch-at $at, has knowledge-at $kat, has recorded-at $rec; $b has wm-id $bid;
- x2 [0.0r 0.7+0.3 | 0.0r 0.8+1.2 | 0.0r 0.7+2.2 | 0.0r 0.8+1.2 | 0.0r 1.9+2.8] +w10 4.3 +p10 8.9 ms/round :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $su isa supersession (old: $a, new: $n), has recorded-

## core03 1x: ingest {'seconds': 45.6, 'move_ms_median': 35.9, 'move_ms_p95': 73.8}; size 3742318; mem 291.1MiB / 7.748GiB cpu 35.54% -> 291MiB / 7.748GiB cpu 29.31%
latency {'n': 60, 'min': 25.4, 'p10': 28.8, 'p50': 44.8, 'p90': 57.6, 'p95': 59.4, 'p99': 67.3, 'max': 70.6, 'mean': 43.4}
median parts {'total': 44.8, 'open': 1.87, 'first': 12.54, 'stream': 27.86, 'python': 2.17}; mean {'total': 43.41, 'open': 1.89, 'first': 10.88, 'stream': 28.37, 'python': 2.26}; q/question 17.65 tx 3.0 rows 25.9
  - 34 exec, 3.0 rows, first 0.66 stream 11.11 total 374.5 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa located-at; $subj has wm-id == $sid; $c links ($kr: $subj); $rec <= $kl
  - 60 exec, 1.7 rows, first 0.62 stream 0.95 total 304.4 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa located-at; $subj has wm-id == $sid; $c links ($kr: $subj); { not { $a 
  - 34 exec, 12.5 rows, first 0.6 stream 4.1 total 179.2 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa located-at; $subj has wm-id == $sid; $c links ($kr: $subj); $rec <= $kl
  - 60 exec, 0.0 rows, first 0.63 stream 2.1 total 163.7 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $who has wm-id
  - 60 exec, 7.1 rows, first 0.57 stream 0.72 total 155.1 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa located-at; $subj has wm-id == $sid; $c links ($kr: $subj); { not { $a 
  - 60 exec, 0.0 rows, first 0.55 stream 1.97 total 154.6 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); try { $c links
full sample: [{'ms': 2545.2, 'first_ms': 83.0, 'stream_ms': 2268.9, 'rows': 11725, 'queries': 14, 'identical': True}, {'ms': 2195.4, 'first_ms': 7.6, 'stream_ms': 2014.9, 'rows': 11649, 'queries': 7, 'identical': True}, {'ms': 3343.2, 'first_ms': 121.9, 'stream_ms': 3040.6, 'rows': 12144, 'queries': 14, 'identical': True}] mem 303.2MiB / 7.748GiB cpu 39.47%

## core03 5x: ingest {'seconds': 343.4, 'move_ms_median': 55.9, 'move_ms_p95': 104.2}; size 49229964; mem 345.7MiB / 7.748GiB cpu 33.56% -> 346.2MiB / 7.748GiB cpu 26.37%
latency {'n': 60, 'min': 57.5, 'p10': 71.9, 'p50': 123.5, 'p90': 166.4, 'p95': 185.5, 'p99': 219.7, 'max': 338.0, 'mean': 121.5}
median parts {'total': 123.52, 'open': 1.91, 'first': 11.25, 'stream': 106.98, 'python': 2.34}; mean {'total': 121.54, 'open': 2.06, 'first': 11.37, 'stream': 105.65, 'python': 2.46}; q/question 17.0 tx 3.0 rows 29.8
  - 30 exec, 4.1 rows, first 0.64 stream 37.3 total 1293.1 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa located-at; $subj has wm-id == $sid; $c links ($kr: $subj); $rec <= $kl
  - 60 exec, 1.9 rows, first 0.59 stream 9.14 total 1277.7 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa located-at; $subj has wm-id == $sid; $c links ($kr: $subj); { not { $a 
  - 60 exec, 0.0 rows, first 0.58 stream 11.19 total 723.2 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $who has wm-id
  - 60 exec, 0.0 rows, first 0.57 stream 10.3 total 666.8 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); try { $c links
  - 60 exec, 0.0 rows, first 0.6 stream 9.38 total 618.4 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $su isa supers
  - 30 exec, 0.0 rows, first 0.66 stream 11.18 total 397.2 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $rec <= $klim;
full sample: [{'ms': 49411.9, 'first_ms': 193.7, 'stream_ms': 48180.6, 'rows': 60815, 'queries': 21, 'identical': True}, {'ms': 56221.0, 'first_ms': 33.5, 'stream_ms': 55113.6, 'rows': 60739, 'queries': 14, 'identical': True}, {'ms': 58925.8, 'first_ms': 16.2, 'stream_ms': 57897.8, 'rows': 58220, 'queries': 7, 'identical': True}] mem 394.9MiB / 7.748GiB cpu 25.01%

## core03 10x: ingest {'seconds': 1160.0, 'move_ms_median': 90.8, 'move_ms_p95': 192.2}; size 101748828; mem 541.3MiB / 7.748GiB cpu 45.12% -> 541.2MiB / 7.748GiB cpu 33.82%
latency {'n': 60, 'min': 112.0, 'p10': 138.4, 'p50': 233.5, 'p90': 279.3, 'p95': 293.6, 'p99': 315.5, 'max': 332.2, 'mean': 217.2}
median parts {'total': 233.52, 'open': 2.16, 'first': 13.75, 'stream': 215.94, 'python': 2.59}; mean {'total': 217.19, 'open': 2.23, 'first': 11.99, 'stream': 200.33, 'python': 2.63}; q/question 17.17 tx 3.0 rows 25.0
  - 60 exec, 1.7 rows, first 0.65 stream 8.19 total 2085.3 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa located-at; $subj has wm-id == $sid; $c links ($kr: $subj); { not { $a 
  - 31 exec, 3.3 rows, first 0.68 stream 57.9 total 2075.5 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa located-at; $subj has wm-id == $sid; $c links ($kr: $subj); $rec <= $kl
  - 60 exec, 0.0 rows, first 0.61 stream 22.17 total 1370.5 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $who has wm-id
  - 60 exec, 0.0 rows, first 0.69 stream 20.31 total 1265.9 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); try { $c links
  - 60 exec, 0.0 rows, first 0.73 stream 20.18 total 1255.4 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $acc isa accep
  - 60 exec, 0.0 rows, first 0.71 stream 18.21 total 1134.8 :: match $w isa world, has wm-id == $world; $a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec; $c isa same-as; $subj has wm-id == $sid; $c links ($kr: $subj); $su isa supers

