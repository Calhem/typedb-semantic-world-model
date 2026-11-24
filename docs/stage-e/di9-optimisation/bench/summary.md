## run log: 74 lines; steps with sleep events: 0; not on AC power: 0; failed steps: 0

## Core 0.3 selective, 60 questions: median ms (p95) [queries/question] per pass
| scale | base | o1 | o2 |
|---|---|---|---|
| 1x | 68.2 (181) / 50.8 (73) / 48.6 (68) / 49.8 (67) / 52.9 (77) [17.65] | 29.2 (52) / 24.3 (36) [11.3] | 19.8 (34) / 29.0 (80) / 19.3 (32) / 19.7 (32) / 21.5 (33) [11.73] |
| 5x | 160.4 (374) / 131.9 (181) [17.0] | 67.3 (125) / 83.2 (132) [11.15] | 54.5 (98) / 71.1 (180) [11.65] |
| 10x | 260.4 (404) / 259.1 (348) / 242.6 (308) / 259.2 (368) / 262.0 (361) [17.17] | 113.0 (191) / 113.5 (202) [11.22] | 71.3 (146) / 83.7 (169) / 65.3 (142) / 66.3 (137) / 68.6 (154) [11.7] |

## scale reads: per-reader p50 ms (both passes pooled); o2 vs base ratio
| reader | worlds-1 base / o1 / o2 (o2/base) | worlds-10 base / o1 / o2 (o2/base) | perspectives-10 base / o1 / o2 (o2/base) |
|---|---|---|---|
| authorised | 34 / 19 / 18 (x0.52) | 46 / 24 / 19 (x0.41) | 44 / 24 / 19 (x0.42) |
| calibration_status | 40 / 20 / 20 (x0.50) | 60 / 24 / 22 (x0.37) | 50 / 26 / 21 (x0.42) |
| capable | 34 / 16 / 16 (x0.47) | 54 / 20 / 16 (x0.29) | 50 / 20 / 16 (x0.32) |
| causes_of | 133 / 47 / 58 (x0.44) | 160 / 64 / 50 (x0.31) | 149 / 63 / 56 (x0.37) |
| changes | 127 / 40 / 41 (x0.32) | 195 / 54 / 41 (x0.21) | 185 / 53 / 41 (x0.22) |
| facts_about | 97 / 24 / 26 (x0.27) | 102 / 32 / 28 (x0.28) | 95 / 32 / 28 (x0.29) |
| interpretations | 82 / 33 / 35 (x0.42) | 94 / 40 / 38 (x0.40) | 86 / 40 / 37 (x0.43) |
| occurrence | 122 / 54 / 51 (x0.42) | 222 / 82 / 51 (x0.23) | 232 / 101 / 72 (x0.31) |
| occurrence_status | 117 / 58 / 61 (x0.53) | 178 / 71 / 60 (x0.34) | 182 / 91 / 81 (x0.45) |
| office_holders | 94 / 51 / 49 (x0.52) | 192 / 79 / 55 (x0.29) | 164 / 77 / 56 (x0.34) |
| offices_of | 241 / 88 / 77 (x0.32) | 352 / 133 / 106 (x0.30) | 298 / 114 / 105 (x0.35) |
| parts | 33 / 15 / 17 (x0.51) | 73 / 23 / 27 (x0.36) | 58 / 23 / 24 (x0.42) |
| provenance | 703 / 256 / 262 (x0.37) | 818 / 351 / 270 (x0.33) | 1132 / 392 / 370 (x0.33) |
| value_at | 39 / 16 / 12 (x0.32) | 68 / 25 / 12 (x0.18) | 65 / 24 / 12 (x0.19) |

## scale growth: reader p50 at 10x worlds / 1x worlds, per version
- base: parts x2.22, office_holders x2.04, occurrence x1.83, value_at x1.77, capable x1.60, changes x1.54, occurrence_status x1.52, calibration_status x1.49, offices_of x1.46, authorised x1.33, causes_of x1.20, provenance x1.16, interpretations x1.15, facts_about x1.06
- o1: parts x1.57, value_at x1.55, office_holders x1.54, occurrence x1.51, offices_of x1.51, causes_of x1.37, provenance x1.37, changes x1.34, facts_about x1.33, capable x1.28, authorised x1.26, occurrence_status x1.23, interpretations x1.19, calibration_status x1.19
- o2: parts x1.56, offices_of x1.38, office_holders x1.12, calibration_status x1.11, interpretations x1.08, facts_about x1.07, authorised x1.05, provenance x1.03, changes x1.02, occurrence x1.01, capable x1.00, value_at x0.99, occurrence_status x0.98, causes_of x0.86

## scale growth: reader p50 at 10x perspectives / 1x, per version
- base: occurrence x1.91, parts x1.75, office_holders x1.74, value_at x1.68, provenance x1.61, occurrence_status x1.56, capable x1.48, changes x1.46, authorised x1.30, calibration_status x1.26, offices_of x1.24, causes_of x1.12, interpretations x1.05, facts_about x0.98
- o1: occurrence x1.85, parts x1.58, occurrence_status x1.56, provenance x1.53, value_at x1.51, office_holders x1.50, causes_of x1.35, changes x1.33, facts_about x1.31, offices_of x1.30, calibration_status x1.29, capable x1.26, authorised x1.24, interpretations x1.21
- o2: parts x1.42, provenance x1.42, occurrence x1.40, offices_of x1.36, occurrence_status x1.33, office_holders x1.14, interpretations x1.06, facts_about x1.06, calibration_status x1.06, authorised x1.04, changes x1.01, capable x1.00, value_at x0.98, causes_of x0.95

## totals per round (sum of per-call medians, s) and queries per round, pass A / pass B
- worlds-1: base 36.4/25.9 s, 14601 q; o1 10.7/9.9 s, 8349 q; o2 10.2/10.4 s, 8054 q
- worlds-5: base 33.0/35.8 s, 14601 q; o1 12.5/11.5 s, 8349 q; o2 10.8/10.0 s, 8054 q
- worlds-10: base 44.2/45.6 s, 14601 q; o1 14.6/13.6 s, 8349 q; o2 11.5/10.5 s, 8054 q
- perspectives-5: base 36.0/33.8 s, 14601 q; o1 14.1/12.6 s, 8349 q; o2 11.6/11.3 s, 8054 q
- perspectives-10: base 41.0/41.7 s, 14601 q; o1 16.7/15.5 s, 8349 q; o2 14.6/12.5 s, 8054 q

## 1x (worlds-1) readers slower than base by more than 10 % (o2, pooled p50), with per-pass values

## query counts per reader per call at worlds-1 (base -> o1 -> o2)
- authorised: 21.5 -> 15.5 -> 15.0
- calibration_status: 22.8 -> 16.8 -> 16.2
- capable: 23.5 -> 14.1 -> 13.4
- causes_of: 112.2 -> 71.3 -> 68.9
- changes: 83.9 -> 41.6 -> 40.0
- facts_about: 29.3 -> 18.5 -> 18.4
- interpretations: 31.2 -> 22.2 -> 21.5
- occurrence: 87.9 -> 46.0 -> 43.7
- occurrence_status: 75.1 -> 48.4 -> 46.4
- office_holders: 54.5 -> 33.5 -> 33.0
- offices_of: 82.0 -> 56.5 -> 57.2
- parts: 17.8 -> 10.2 -> 10.2
- provenance: 271.8 -> 187.0 -> 190.5
- value_at: 30.4 -> 13.7 -> 12.0

## answers identical to base (masked), per database and version
- worlds-1: A-o1 267/267, A-o2 267/267, B-o1 267/267, B-o2 267/267, B-base 267/267
- worlds-5: A-o1 267/267, A-o2 267/267, B-o1 267/267, B-o2 267/267, B-base 267/267
- worlds-10: A-o1 267/267, A-o2 267/267, B-o1 267/267, B-o2 267/267, B-base 267/267
- perspectives-5: A-o1 267/267, A-o2 267/267, B-o1 267/267, B-o2 267/267, B-base 267/267
- perspectives-10: A-o1 267/267, A-o2 267/267, B-o1 267/267, B-o2 267/267, B-base 267/267

## instrumented (n=7): median total ms per call, pass A / pass B
- where actual gbx-100 f-workshop (worlds-1/worlds-10): base 363/569 ; 354/687 | o1 65/87 ; 58/75 | o2 67/74 ; 58/76
- parts actual bay-1 (worlds-1/worlds-10): base 30/309 ; 17/52 | o1 14/25 ; 14/22 | o2 16/22 ; 14/24
- occurrence actual o-repair (worlds-1/worlds-10): base 72/132 ; 67/126 | o1 45/64 ; 45/61 | o2 53/48 ; 44/50
- value_at actual gbx-100 (worlds-1/worlds-10): base 15/30 ; 15/26 | o1 11/14 ; 10/12 | o2 12/10 ; 10/11
- effects_of actual ev-worklog-replacement (worlds-1/worlds-10): base 268/578 ; 280/541 | o1 166/278 ; 162/252 | o2 196/210 ; 165/228
- provenance lab s12-b (worlds-1/worlds-10): base 532/844 ; 481/768 | o1 346/483 ; 338/415 | o2 388/355 ; 340/396

## where at 92 worlds / 11 worlds (instrumented + repeats)
- base: A: 363 -> 569 ms (x1.57); B: 354 -> 687 ms (x1.94); R1: 210 -> 557 ms (x2.65); R2: 102 -> 429 ms (x4.19); R3: 87 -> 431 ms (x4.97)
- o1: A: 65 -> 87 ms (x1.34); B: 58 -> 75 ms (x1.30)
- o2: A: 67 -> 74 ms (x1.11); B: 58 -> 76 ms (x1.31); R1: 58 -> 70 ms (x1.21); R2: 67 -> 75 ms (x1.12); R3: 68 -> 79 ms (x1.16)
