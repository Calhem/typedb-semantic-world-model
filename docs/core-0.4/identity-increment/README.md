# Identity increment validation records (LABS-1.048)

Old code `bf60c1f` ("base") against the identity correction `29ee628` ("id"). See
[pre-e-identity-increment.md](../pre-e-identity-increment.md).

| File | What |
|---|---|
| `snapshot-diff.out.txt` | `probes/pre_e_b_diff.py`: the 106,752 answers of `wm-probe-pre-e-d-new`, old against new code (all identical) |
| `repro-check-summary.out.txt` | `probes/pre_e_b_repro_check.py` against the frozen increment B snapshot (differences are increment C's, same for both codes) |
| `read-bench-{base,id}.json` | `probes/pre_e_b_read_bench.py --n 1 --more --occurrence --db wm-probe-pre-e-d` |
| `occurrence-bench-{base,id}.json` | `probes/pre_e_d_occurrence_bench.py --reference --n 1 --db wm-probe-pre-e-d-u` |
| `core03-{base,id}.json` | `probes/pre_e_core03_baseline.py` (default 60 questions), one run each |
| `suite-matrix.out.txt` | the full suite, twice, in the four configurations |

Timings in these files are single runs on a shared machine; only the query and transaction counts are compared.
