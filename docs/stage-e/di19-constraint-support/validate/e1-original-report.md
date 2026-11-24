# Stage E1 benchmark results

Run 2026-11-24T11:25:15+00:00 on commit `7cb348d`; 272 questions, both query paths. Expected answers were frozen at commit `(not given)` before this run.

| Category | Questions | Correct | % | Wrong judgement | Wrong values | Missing evidence | Forbidden evidence | Error | Paths disagree |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| conflict-provenance | 30 | 30 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| cross-domain | 33 | 33 | 100 | 0 | 0 | 1 | 0 | 0 | 0 |
| identity | 42 | 42 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| laboratory | 36 | 33 | 92 | 1 | 2 | 1 | 0 | 0 | 0 |
| mechanical | 33 | 33 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| organisation | 31 | 30 | 97 | 0 | 0 | 0 | 0 | 1 | 0 |
| temporal | 37 | 36 | 97 | 1 | 0 | 0 | 0 | 0 | 0 |
| worlds-perspectives | 30 | 30 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| **all** | 272 | 267 | 98 | 2 | 2 | 2 | 0 | 1 | 0 |

## Incorrect items

| Id | Template | Failure | Expected | Actual (selective path) |
|---|---|---|---|---|
| LAB-010 | calibrated | wrong-judgement | `{"judgement": "not established"}` | `{"judgement": "established"}` |
| LAB-025 | event_role | wrong-values | `{"judgement": "union", "players": [["ana"], ["ben"], ["cy"]]}` | `{"judgement": "union", "players": [["ana"], ["ben"], ["cy"], ["dan"]]}` |
| LAB-026 | event_role | wrong-values | `{"judgement": "union", "players": [["ana"], ["ben"]]}` | `{"judgement": "union", "players": [["ana"], ["ben"], ["cy"], ["dan"]]}` |
| LAB-034 | value_at | missing-evidence | `{"status": "ASSERTED", "values": ["fridge-2"]}` | `{"status": "ASSERTED", "values": ["fridge-2"]}` |
| ORG-011 | holds | error | `{"judgement": "disputed", "status": "DISPUTED"}` | `"UnknownRoleError: 'office-holding' has no role 'holder', 'office': readers take its core role names ['class', 'classified', 'context'] (nothing answered)"` |
| TEMP-017 | holds | wrong-judgement | `{"judgement": "pending", "status": "UNKNOWN"}` | `{"judgement": "not holding", "status": "INFERRED"}` |
| X-003 | office_holders | missing-evidence | `{"holders": ["dan"], "conflict": false}` | `{"holders": ["dan"], "conflict": false}` |
