# Multiplicity increment validation records (LABS-1.049, DI-13)

Old code `main` `dd58b25` ("main", "old"); new code `ef230d4` ("mp", "new"). See
[pre-e-multiplicity-increment.md](../pre-e-multiplicity-increment.md), sections 5 to 8a.

Databases: `wm-probe-pre-e-mp-u` (built by the old code, then upgraded), `wm-probe-pre-e-mp-new` (built by the new
code), `wm-probe-pre-e-d-new` (built under increment D, never upgraded).

| File | What |
|---|---|
| `suite-matrix.out.txt` | the full suite, twice, in the four configurations |
| `upgrade.json` | the explicit upgrade of `wm-probe-pre-e-mp-u`, and the same calls again (idempotent) |
| `snapshot-*.out.txt` | `probes/pre_e_b_diff.py` on the 106,752-answer snapshots: S0 old code before the upgrade, S1 new code before, S2 new code after, S3 old code after |
| `views-*.out.txt` | `probes/pre_e_d_impact.py --library` totals and the comparison with the frozen 398-view baseline (V1: not upgraded; V-new-u: upgraded; V-new-new: fresh; V-old-u: old code on the upgraded database) |
| `full-views-*-old-vs-new.out.txt` | complete `occurrence()` answers compared field by field (`dump_views.py`, `viewdiff.py`) |
| `structure.json` | fresh against upgraded installation: schema text and facts, modules, module data, constraints, schema query answers (`structure.py`) |
| `format-check.txt` | the regenerated reference export validated against the format-2 JSON Schema before and after this change |
| `read-bench-*.json`, `occurrence-bench-*.json`, `core03-*.json` | query counts, one round each (`probes/pre_e_b_read_bench.py`, `probes/pre_e_d_occurrence_bench.py`, `probes/pre_e_core03_baseline.py`) |
| `move-count.jsonl` | queries and transactions per `move()` (`move_count.py`) |
| `*.py` | the helper scripts used for these records; each takes a checkout and database names as arguments |

Timings in these files were taken while other validation ran on the same machine; only counts and answers are compared.
The 106,752-answer snapshot of a freshly built database was not taken (approved; see section 6.5 of the report).
