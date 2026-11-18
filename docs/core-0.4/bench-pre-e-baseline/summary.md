## Runs (after one discarded warm-up)
| Run | Impl. | Selective median / p95 (ms) | Full median (ms) | Ingest (s) | Move median / p95 (ms) | DB (MB) |
|---|---|---|---|---|---|---|
| 1 | entry commit | 44.7 / 62.5 | 3,484.5 | 43.7 | 35.3 / 69.0 | 10.37 |
| 2 | Core 0.3 | 45.9 / 61.3 | 3,871.5 | 51.5 | 41.6 / 76.3 | 12.33 |
| 3 | Core 0.3 | 47.4 / 65.9 | 3,843.1 | 70.4 | 50.8 / 139.8 | 12.40 |
| 4 | entry commit | 59.2 / 86.6 | 3,827.7 | 67.4 | 49.8 / 122.9 | 10.41 |
| 5 | entry commit | 50.4 / 80.7 | 3,714.2 | 52.2 | 42.4 / 78.3 | 10.35 |
| 6 | Core 0.3 | 48.8 / 71.4 | 3,884.9 | 55.9 | 44.9 / 83.0 | 12.32 |
| 7 | Core 0.3 | 51.3 / 84.3 | 3,881.8 | 68.5 | 52.5 / 114.9 | 12.38 |
| 8 | entry commit | 64.3 / 148.8 | 3,699.9 | 56.8 | 43.7 / 96.3 | 10.35 |
| 9 | entry commit | 52.7 / 108.1 | 3,640.0 | 52.8 | 43.0 / 78.5 | 10.35 |
| 10 | Core 0.3 | 51.5 / 68.1 | 3,688.6 | 59.3 | 48.8 / 85.5 | 12.32 |
| 11 | Core 0.3 | 50.1 / 65.2 | 3,904.8 | 61.2 | 48.9 / 94.6 | 12.36 |
| 12 | entry commit | 59.4 / 120.6 | 4,338.5 | 63.0 | 47.5 / 108.7 | 10.40 |
| 13 | entry commit | 54.7 / 83.5 | 3,700.2 | 63.5 | 47.6 / 108.4 | 10.40 |
| 14 | Core 0.3 | 43.3 / 57.9 | 3,705.8 | 54.3 | 44.0 / 81.8 | 12.32 |
| 15 | Core 0.3 | 52.9 / 83.2 | 3,670.2 | 58.2 | 47.7 / 87.3 | 12.32 |
| 16 | entry commit | 51.7 / 76.5 | 3,674.8 | 50.5 | 39.6 / 80.1 | 10.35 |
| 17 | entry commit | 49.6 / 83.2 | 3,746.3 | 48.0 | 38.4 / 73.0 | 10.35 |
| 18 | Core 0.3 | 44.3 / 58.4 | 3,671.3 | 54.7 | 43.8 / 82.0 | 12.32 |
| 19 | Core 0.3 | 47.0 / 69.9 | 3,651.2 | 51.6 | 41.5 / 77.6 | 12.32 |
| 20 | entry commit | 49.1 / 67.8 | 3,769.6 | 49.9 | 38.3 / 79.8 | 10.37 |

## Per implementation (Core 0.3 (b64f635): 10 runs, entry commit: 10 runs)
| Measure | Core 0.3 (b64f635): median (min-max, CV) | entry commit: median (min-max, CV) |
|---|---|---|
| selective median | 48.1 ms (43.3-52.9, 6.7 %) | 52.2 ms (44.7-64.3, 11.0 %) |
| selective p95 | 67.0 ms (57.9-84.3, 13.4 %) | 83.3 ms (62.5-148.8, 28.8 %) |
| full-load median | 3,774.4 ms (3,651.2-3,904.8, 2.8 %) | 3,707.2 ms (3,484.5-4,338.5, 5.9 %) |
| ingestion | 57.0 s (51.5-70.4, 11.2 %) | 52.5 s (43.7-67.4, 14.0 %) |
| move median | 46.3 ms (41.5-52.5, 8.2 %) | 42.7 ms (35.3-49.8, 11.1 %) |
| move p95 | 84.2 ms (76.3-139.8, 21.7 %) | 79.9 ms (69.0-122.9, 20.4 %) |
| database size | 12.32 MB (12.32-12.40, 0.2 %) | 10.36 MB (10.35-10.41, 0.2 %) |
| selective: queries / attestations per question | 13.5 / 7.1 in every run | 13.5 / 7.1 in every run |
| full: queries / attestations per question | 9.4 / 3283.9 in every run | 9.4 / 3283.9 in every run |
| TypeDB share of selective time (median) | 0.931 | 0.903 |
| TypeDB share of full-load time (median) | 0.946 | 0.944 |
| answers selective = full | 10 of 10 | 10 of 10 |

## Pooled per-question latency (every question of every run, ms)
| Impl. | Path | n | min | p10 | p50 | p90 | p95 | p99 | max | mean |
|---|---|---|---|---|---|---|---|---|---|---|
| Core 0.3 (b64f635) | selective | 600 | 21.5 | 29.7 | 47.4 | 65.8 | 72.4 | 90.4 | 204.8 | 48.2 |
| Core 0.3 (b64f635) | full | 600 | 2,285.8 | 2,408.2 | 3,720.4 | 4,186.4 | 4,494.1 | 5,133.5 | 8,527.3 | 3,380.4 |
| entry commit | selective | 600 | 24.1 | 33.8 | 52.9 | 79.8 | 92.7 | 169.6 | 247.0 | 56.5 |
| entry commit | full | 600 | 2,189.1 | 2,389.9 | 3,707.8 | 4,295.2 | 4,605.2 | 5,755.0 | 6,200.9 | 3,412.5 |

## Entry commit against Core 0.3 (plan 9.4)
| Measure | Core 0.3 | entry commit | difference | threshold | CV Core 0.3 / entry | result |
|---|---|---|---|---|---|---|
| selective median | 48.1 ms | 52.2 ms | +8.5 % | +10 % | 6.7 % / 11.0 % | not demonstrable (CV above 10 %) |
| selective p95 | 67.0 ms | 83.3 ms | +24.4 % | +15 % | 13.4 % / 28.8 % | not demonstrable (CV above 10 %) |
| full-load median | 3,774.4 ms | 3,707.2 ms | -1.8 % | +10 % | 2.8 % / 5.9 % | met |
| ingestion | 57.0 s | 52.5 s | -8.0 % | +10 % | 11.2 % / 14.0 % | not demonstrable (CV above 10 %) |
| move median | 46.3 ms | 42.7 ms | -7.8 % | - | 8.2 % / 11.1 % | no threshold |
| move p95 | 84.2 ms | 79.9 ms | -5.1 % | - | 21.7 % / 20.4 % | no threshold |
| database size | 12.32 MB | 10.36 MB | -15.9 % | +5 % | 0.2 % / 0.2 % | met |

## Selective path, question by question (the same 60 questions in every run)
ratio of per-question medians, entry / Core 0.3: min 0.75, p10 1.03, median 1.11, p90 1.19, max 1.27; questions more than 25 % slower: 1, more than 20 % faster: 1
Core 0.3 (b64f635): questions above 120 ms, per run: [0, 0, 0, 1, 0, 0, 0, 1, 0, 1]
entry commit: questions above 120 ms, per run: [0, 1, 0, 4, 3, 4, 0, 0, 0, 1]
Core 0.3 (b64f635): TypeDB reads median 45.2 ms, Python median 3.0 ms (medians of run medians)
entry commit: TypeDB reads median 47.1 ms, Python median 4.8 ms (medians of run medians)

## Environment
commits: {'c03': ['b64f635'], 'main': ['bf60c1f']}
containers running: [16]
identical in every run:
{"docker_vm_cpus": 10, "docker_vm_memory_gib": 7.7, "host_cpu": "Apple M2 Pro", "host_os": "Darwin 25.5.0", "python": "3.13.17", "typedb_driver": "3.14.0", "typedb_server_image": "typedb/typedb:3.14.1@sha256:d39d4f29eb571ee856cb221e8175b76dcb96dfa39939ebde5360cffa0e5bb680"}
workload: {"objects": 200, "places": 30, "moves": 1000, "queries": 60, "seed": 11} | attestations in the actual world: 3200 | propositions: 1140
