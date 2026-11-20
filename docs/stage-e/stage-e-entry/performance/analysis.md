## per reader: p50 / p95 ms over all calls and rounds (both passes pooled), ratio of p50 to worlds-1
| reader | calls | worlds-1 | worlds-5 | worlds-10 | perspectives-5 | perspectives-10 |
|---|---|---|---|---|---|---|
| authorised | 4 | 29 / 41 | 39 / 51 (x1.33) | 43 / 60 (x1.48) | 35 / 71 (x1.20) | 52 / 79 (x1.78) |
| calibration_status | 4 | 30 / 43 | 40 / 54 (x1.32) | 49 / 70 (x1.61) | 46 / 53 (x1.52) | 58 / 97 (x1.91) |
| capable | 33 | 29 / 42 | 39 / 51 (x1.34) | 52 / 63 (x1.77) | 39 / 55 (x1.32) | 50 / 95 (x1.70) |
| causes_of | 14 | 84 / 416 | 118 / 496 (x1.41) | 146 / 591 (x1.75) | 111 / 499 (x1.33) | 152 / 622 (x1.82) |
| changes | 33 | 111 / 600 | 145 / 677 (x1.31) | 188 / 800 (x1.70) | 147 / 696 (x1.33) | 185 / 860 (x1.67) |
| facts_about | 33 | 82 / 407 | 84 / 408 (x1.02) | 108 / 431 (x1.32) | 88 / 424 (x1.08) | 105 / 454 (x1.28) |
| interpretations | 12 | 67 / 111 | 77 / 104 (x1.15) | 88 / 125 (x1.32) | 77 / 116 (x1.16) | 93 / 151 (x1.38) |
| occurrence | 42 | 114 / 351 | 161 / 453 (x1.41) | 215 / 458 (x1.88) | 167 / 447 (x1.47) | 237 / 563 (x2.08) |
| occurrence_status | 14 | 111 / 163 | 137 / 191 (x1.24) | 169 / 218 (x1.53) | 140 / 229 (x1.26) | 188 / 289 (x1.70) |
| office_holders | 4 | 92 / 106 | 134 / 162 (x1.45) | 169 / 210 (x1.84) | 130 / 163 (x1.42) | 177 / 251 (x1.93) |
| offices_of | 4 | 209 / 303 | 256 / 371 (x1.23) | 303 / 466 (x1.45) | 271 / 386 (x1.30) | 375 / 648 (x1.80) |
| parts | 33 | 31 / 100 | 72 / 201 (x2.34) | 88 / 369 (x2.87) | 45 / 110 (x1.46) | 57 / 135 (x1.84) |
| provenance | 4 | 641 / 1072 | 675 / 1010 (x1.05) | 816 / 1377 (x1.27) | 878 / 1429 (x1.37) | 1120 / 1637 (x1.75) |
| value_at | 33 | 37 / 55 | 50 / 65 (x1.34) | 66 / 85 (x1.78) | 49 / 77 (x1.32) | 65 / 115 (x1.76) |

## totals: sum over the 267 calls of the per-call median (ms), queries and transactions per round
- worlds-1: 26.0 s per round, x1.00; queries 14601, transactions 1950; all-call p50 61 ms p95 380 p99 644
  calls whose query or transaction count differs from worlds-1: 0 []
- worlds-5: 33.4 s per round, x1.29; queries 14601, transactions 1950; all-call p50 81 ms p95 425 p99 702
  calls whose query or transaction count differs from worlds-1: 0 []
- worlds-10: 41.4 s per round, x1.59; queries 14601, transactions 1950; all-call p50 98 ms p95 466 p99 840
  calls whose query or transaction count differs from worlds-1: 0 []
- perspectives-5: 32.7 s per round, x1.26; queries 14601, transactions 1950; all-call p50 77 ms p95 441 p99 889
  calls whose query or transaction count differs from worlds-1: 0 []
- perspectives-10: 42.1 s per round, x1.62; queries 14601, transactions 1950; all-call p50 97 ms p95 536 p99 1167
  calls whose query or transaction count differs from worlds-1: 0 []

## pass-to-pass agreement (sum of per-call medians, read1 vs read2)
- worlds-1: read1 26.8 s, read2 25.6 s (-5 %)
- worlds-5: read1 34.4 s, read2 32.9 s (-4 %)
- worlds-10: read1 42.3 s, read2 41.1 s (-3 %)
- perspectives-5: read1 35.5 s, read2 31.5 s (-11 %)
- perspectives-10: read1 41.6 s, read2 44.8 s (+8 %)

## answers identical to worlds-1 (masked)
- worlds-5: 267 / 267 identical; different: []
- worlds-10: 267 / 267 identical; different: []
- perspectives-5: 267 / 267 identical; different: []
- perspectives-10: 267 / 267 identical; different: []

## slowest-growing calls at worlds-10 and perspectives-10 (median ms per call, ratio)
- worlds-10: parts actual bay-1 29->307 ms (x10.47); parts actual gbx-100 32->306 ms (x9.66); parts plan-relubricate-only bench-1 34->213 ms (x6.21); parts plan-relubricate-only gbx-100 58->349 ms (x5.97); parts plan-relubricate-only o-test-run 57->343 ms (x5.96); parts plan-apprentice bay-1 62->357 ms (x5.75); parts plan-move-bench gbx-100 62->350 ms (x5.66); parts plan-move-bench bearing-1 62->348 ms (x5.62)
- perspectives-10: occurrence actual o-sign-off 60->193 ms (x3.23); occurrence actual o-repair 65->211 ms (x3.22); occurrence actual o-inspection 67->211 ms (x3.16); occurrence actual o-relubrication 64->202 ms (x3.14); occurrence actual o-test-run 69->215 ms (x3.14); occurrence actual o-reassembly 63->196 ms (x3.12); occurrence actual o-disassembly 65->199 ms (x3.05); occurrence lab-plan-recal o-split-b 99->288 ms (x2.90)
