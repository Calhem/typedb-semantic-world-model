# Stage E1 benchmark results

Run 2026-11-20T01:10:00+00:00 on commit `d0f0aa2`; 272 questions, both query paths. Expected answers were frozen at commit `d0f0aa2` before this run.

| Category | Questions | Correct | % | Wrong judgement | Wrong values | Missing evidence | Forbidden evidence | Error | Paths disagree |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| conflict-provenance | 30 | 30 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| cross-domain | 33 | 33 | 100 | 0 | 0 | 2 | 0 | 0 | 0 |
| identity | 42 | 42 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| laboratory | 36 | 33 | 92 | 1 | 2 | 2 | 0 | 0 | 0 |
| mechanical | 33 | 33 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| organisation | 31 | 30 | 97 | 1 | 0 | 4 | 0 | 0 | 0 |
| temporal | 37 | 36 | 97 | 1 | 0 | 0 | 0 | 0 | 0 |
| worlds-perspectives | 30 | 30 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| **all** | 272 | 267 | 98 | 3 | 2 | 8 | 0 | 0 | 0 |

## Incorrect items

| Id | Template | Failure | Expected | Actual (selective path) |
|---|---|---|---|---|
| LAB-003 | calibrated | missing-evidence | `{"judgement": "not yet effective"}` | `{"judgement": "not yet effective"}` |
| LAB-010 | calibrated | wrong-judgement | `{"judgement": "not established"}` | `{"judgement": "established"}` |
| LAB-025 | event_role | wrong-values | `{"judgement": "union", "players": [["ana"], ["ben"], ["cy"]]}` | `{"judgement": "union", "players": [["ana"], ["ben"], ["cy"], ["dan"]]}` |
| LAB-026 | event_role | wrong-values | `{"judgement": "union", "players": [["ana"], ["ben"]]}` | `{"judgement": "union", "players": [["ana"], ["ben"], ["cy"], ["dan"]]}` |
| LAB-034 | value_at | missing-evidence | `{"status": "ASSERTED", "values": ["fridge-2"]}` | `{"status": "ASSERTED", "values": ["fridge-2"]}` |
| ORG-017 | authorised | missing-evidence | `{"judgement": "disputed"}` | `{"judgement": "disputed"}` |
| ORG-023 | capable | missing-evidence | `{"judgement": "disputed"}` | `{"judgement": "disputed"}` |
| ORG-002 | office_holders | missing-evidence | `{"holders": ["bea", "cal"], "conflict": true}` | `{"holders": ["bea", "cal"], "conflict": true}` |
| ORG-006 | office_holders | missing-evidence | `{"holders": ["bea", "eve"], "conflict": true}` | `{"holders": ["bea", "eve"], "conflict": true}` |
| ORG-011 | holds | wrong-judgement | `{"judgement": "disputed", "status": "DISPUTED"}` | `{"judgement": "unknown", "status": "NOT_YET_KNOWN"}` |
| TEMP-017 | holds | wrong-judgement | `{"judgement": "pending", "status": "UNKNOWN"}` | `{"judgement": "not holding", "status": "INFERRED"}` |
| X-001 | office_holders | missing-evidence | `{"holders": ["bea", "cal"], "conflict": true}` | `{"holders": ["bea", "cal"], "conflict": true}` |
| X-003 | office_holders | missing-evidence | `{"holders": ["dan"], "conflict": false}` | `{"holders": ["dan"], "conflict": false}` |
