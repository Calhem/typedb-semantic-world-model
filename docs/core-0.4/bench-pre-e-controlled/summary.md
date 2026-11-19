## Runs (warm-ups discarded)
| Run | Impl. | Selective median / p95 (ms) | Full median (ms) | Ingest (s) | Move median / p95 (ms) | DB (MB) |
|---|---|---|---|---|---|---|
| 1 | entry commit | 44.3 / 68.4 | 3,683.4 | 48.5 | 37.7 / 78.2 | 10.39 |
| 2 | Core 0.3 | 46.0 / 80.4 | 3,945.7 | 65.8 | 52.4 / 94.9 | 12.41 |
| 3 | Core 0.3 | 51.4 / 94.4 | 3,933.9 | 64.5 | 51.9 / 92.3 | 12.41 |
| 4 | entry commit | 69.9 / 116.5 | 3,921.9 | 71.9 | 54.0 / 119.1 | 10.44 |
| 5 | entry commit | 55.1 / 100.0 | 3,816.3 | 59.7 | 45.3 / 103.5 | 10.37 |
| 6 | Core 0.3 | 52.7 / 81.4 | 3,807.0 | 69.7 | 56.0 / 105.8 | 12.40 |
| 7 | Core 0.3 | 43.6 / 66.2 | 3,687.8 | 52.7 | 42.3 / 78.7 | 12.34 |
| 8 | entry commit | 54.2 / 90.7 | 3,934.3 | 60.0 | 46.1 / 92.4 | 10.41 |
| 9 | entry commit | 43.8 / 73.2 | 3,773.1 | 46.2 | 36.5 / 74.2 | 10.37 |
| 10 | Core 0.3 | 45.7 / 72.4 | 3,791.6 | 56.0 | 45.0 / 80.6 | 12.34 |
| 11 | Core 0.3 | 44.7 / 68.4 | 3,797.8 | 54.1 | 44.9 / 78.3 | 12.34 |
| 12 | entry commit | 43.8 / 73.2 | 3,757.4 | 47.4 | 36.7 / 73.2 | 10.37 |
| 13 | entry commit | 43.1 / 64.8 | 3,883.2 | 48.2 | 37.2 / 75.9 | 10.37 |
| 14 | Core 0.3 | 47.6 / 72.6 | 3,857.8 | 57.8 | 47.7 / 86.6 | 12.34 |
| 15 | Core 0.3 | 47.1 / 81.3 | 3,854.6 | 60.8 | 46.8 / 96.5 | 12.38 |
| 16 | entry commit | 44.1 / 66.5 | 3,732.7 | 48.8 | 38.7 / 78.2 | 10.37 |
| 17 | entry commit | 41.5 / 64.7 | 3,697.5 | 45.5 | 36.1 / 69.4 | 10.37 |
| 18 | Core 0.3 | 46.3 / 81.7 | 3,768.4 | 51.4 | 41.5 / 74.0 | 12.34 |
| 19 | Core 0.3 | 47.0 / 73.3 | 3,858.2 | 73.5 | 49.8 / 143.0 | 12.40 |
| 20 | entry commit | 42.7 / 65.6 | 3,789.2 | 48.0 | 38.4 / 75.4 | 10.37 |

## Per implementation (Core 0.3 (b64f635): 10 runs, entry commit: 10 runs)
| Measure | Core 0.3 (b64f635): median (min-max, CV) | entry commit: median (min-max, CV) |
|---|---|---|
| selective median | 46.6 ms (43.6-52.7, 6.0 %) | 44.0 ms (41.5-69.9, 18.6 %) |
| selective p95 | 76.8 ms (66.2-94.4, 10.7 %) | 70.8 ms (64.7-116.5, 22.9 %) |
| full-load median | 3,830.8 ms (3,687.8-3,945.7, 2.0 %) | 3,781.1 ms (3,683.4-3,934.3, 2.3 %) |
| ingestion | 59.3 s (51.4-73.5, 12.4 %) | 48.4 s (45.5-71.9, 16.4 %) |
| move median | 47.2 ms (41.5-56.0, 9.8 %) | 38.0 ms (36.1-54.0, 14.5 %) |
| move p95 | 89.4 ms (74.0-143.0, 21.7 %) | 77.1 ms (69.4-119.1, 19.1 %) |
| database size | 12.36 MB (12.34-12.41, 0.3 %) | 10.37 MB (10.37-10.44, 0.2 %) |
| selective: queries / attestations per question | 13.1 / 7.0 in every run | 13.1 / 7.0 in every run |
| full: queries / attestations per question | 9.1 / 3276.5 in every run | 9.1 / 3276.5 in every run |
| TypeDB share of selective time (median) | 0.936 | 0.905 |
| TypeDB share of full-load time (median) | 0.946 | 0.943 |
| answers selective = full | 10 of 10 | 10 of 10 |

## Pooled per-question latency (every question of every run, ms)
| Impl. | Path | n | min | p10 | p50 | p90 | p95 | p99 | max | mean |
|---|---|---|---|---|---|---|---|---|---|---|
| Core 0.3 (b64f635) | selective | 1800 | 22.8 | 30.2 | 46.8 | 70.7 | 79.2 | 98.7 | 284.2 | 49.7 |
| Core 0.3 (b64f635) | full | 1800 | 2,324.7 | 2,469.4 | 3,794.9 | 4,146.2 | 4,320.9 | 4,833.5 | 6,372.2 | 3,345.3 |
| entry commit | selective | 1800 | 22.6 | 30.5 | 47.2 | 74.0 | 88.4 | 128.2 | 292.5 | 51.2 |
| entry commit | full | 1800 | 2,263.0 | 2,413.5 | 3,751.4 | 4,277.0 | 4,536.7 | 5,296.6 | 8,702.7 | 3,363.4 |

## Entry commit against Core 0.3 (plan 9.4)
| Measure | Core 0.3 | entry commit | difference | threshold | CV Core 0.3 / entry | result |
|---|---|---|---|---|---|---|
| selective median | 46.6 ms | 44.0 ms | -5.8 % | +10 % | 6.0 % / 18.6 % | not demonstrable (CV above 10 %) |
| selective p95 | 76.8 ms | 70.8 ms | -7.9 % | +15 % | 10.7 % / 22.9 % | not demonstrable (CV above 10 %) |
| full-load median | 3,830.8 ms | 3,781.1 ms | -1.3 % | +10 % | 2.0 % / 2.3 % | met |
| ingestion | 59.3 s | 48.4 s | -18.5 % | +10 % | 12.4 % / 16.4 % | not demonstrable (CV above 10 %) |
| move median | 47.2 ms | 38.0 ms | -19.5 % | - | 9.8 % / 14.5 % | no threshold |
| move p95 | 89.4 ms | 77.1 ms | -13.9 % | - | 21.7 % / 19.1 % | no threshold |
| database size | 12.36 MB | 10.37 MB | -16.1 % | +5 % | 0.3 % / 0.2 % | met |

## Selective path, question by question (the same 180 questions in every run)
ratio of per-question medians, entry / Core 0.3: min 0.65, p10 0.91, median 0.95, p90 1.02, max 1.10; questions more than 25 % slower: 0, more than 20 % faster: 1
Core 0.3 (b64f635): questions above 120 ms, per run: [1, 2, 1, 0, 0, 0, 0, 1, 0, 1]
entry commit: questions above 120 ms, per run: [2, 9, 7, 2, 3, 2, 0, 0, 0, 2]
Core 0.3 (b64f635): TypeDB reads median 43.5 ms, Python median 3.0 ms (medians of run medians)
entry commit: TypeDB reads median 40.0 ms, Python median 4.0 ms (medians of run medians)

## The first 60 questions only (the original question set; run-level medians and p95 recomputed)
| Measure | Core 0.3 (b64f635): median (min-max, CV) | entry commit: median (min-max, CV) | difference |
|---|---|---|---|
| selective median | 49.4 ms (45.4-56.8, 7.2 %) | 48.5 ms (44.9-74.3, 17.3 %) | -2.0 % |
| selective p95 | 69.9 ms (59.9-92.9, 14.8 %) | 68.1 ms (62.6-108.1, 20.0 %) | -2.7 % |
| full median | 3,884.8 ms (3,722.8-4,124.2, 3.0 %) | 3,830.4 ms (3,714.8-4,101.1, 3.0 %) | -1.4 % |
| full p95 | 4,303.9 ms (3,894.1-5,019.4, 8.3 %) | 4,527.7 ms (4,003.1-5,587.9, 11.3 %) | +5.2 % |

## Environment
commits: {'c03': ['b64f635'], 'main': ['bf60c1f']}
containers running: [6]
identical in every run:
{"docker_vm_cpus": 10, "docker_vm_memory_gib": 7.7, "host_cpu": "Apple M2 Pro", "host_os": "Darwin 25.5.0", "python": "3.13.17", "typedb_driver": "3.14.0", "typedb_server_image": "typedb/typedb:3.14.1@sha256:d39d4f29eb571ee856cb221e8175b76dcb96dfa39939ebde5360cffa0e5bb680"}
workload: {"objects": 200, "places": 30, "moves": 1000, "queries": 180, "seed": 11} | attestations in the actual world: 3200 | propositions: 1140
