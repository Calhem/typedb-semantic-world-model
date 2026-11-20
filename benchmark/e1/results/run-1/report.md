# Stage E1 benchmark results

Run 2026-11-20T01:03:54+00:00 on commit `d0f0aa2`; 272 questions, both query paths. Expected answers were frozen at commit `d0f0aa2` before this run.

| Category | Questions | Correct | % | Wrong judgement | Wrong values | Missing evidence | Forbidden evidence | Error | Paths disagree |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| conflict-provenance | 30 | 30 | 100 | 0 | 0 | 3 | 0 | 0 | 0 |
| cross-domain | 33 | 33 | 100 | 0 | 0 | 6 | 0 | 0 | 0 |
| identity | 42 | 42 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| laboratory | 36 | 33 | 92 | 1 | 2 | 3 | 0 | 0 | 0 |
| mechanical | 33 | 33 | 100 | 0 | 0 | 2 | 0 | 0 | 0 |
| organisation | 31 | 30 | 97 | 1 | 0 | 9 | 0 | 0 | 0 |
| temporal | 37 | 36 | 97 | 1 | 0 | 0 | 0 | 0 | 0 |
| worlds-perspectives | 30 | 30 | 100 | 0 | 0 | 0 | 0 | 0 | 0 |
| **all** | 272 | 267 | 98 | 3 | 2 | 23 | 0 | 0 | 0 |

## Incorrect items

| Id | Template | Failure | Expected | Actual (selective path) |
|---|---|---|---|---|
| CONF-026 | occurrence_status | missing-evidence | `{"status": "disputed"}` | `{"status": "disputed"}` |
| CONF-027 | occurrence_status | missing-evidence | `{"status": "denied"}` | `{"status": "denied"}` |
| CONF-028 | occurrence_status | missing-evidence | `{"status": "accepted"}` | `{"status": "accepted"}` |
| LAB-003 | calibrated | missing-evidence | `{"judgement": "not yet effective"}` | `{"judgement": "not yet effective"}` |
| LAB-004 | calibrated | missing-evidence | `{"judgement": "disputed"}` | `{"judgement": "disputed"}` |
| LAB-010 | calibrated | wrong-judgement | `{"judgement": "not established"}` | `{"judgement": "established"}` |
| LAB-025 | event_role | wrong-values | `{"judgement": "union", "players": [["ana"], ["ben"], ["cy"]]}` | `{"judgement": "union", "players": [["ana"], ["ben"], ["cy"], ["dan"]]}` |
| LAB-026 | event_role | wrong-values | `{"judgement": "union", "players": [["ana"], ["ben"]]}` | `{"judgement": "union", "players": [["ana"], ["ben"], ["cy"], ["dan"]]}` |
| LAB-034 | value_at | missing-evidence | `{"status": "ASSERTED", "values": ["fridge-2"]}` | `{"status": "ASSERTED", "values": ["fridge-2"]}` |
| MECH-021 | event_role | missing-evidence | `{"judgement": "disputed", "players": [["old-a1"], ["old-a2"]], "reason": "several players in one account", "multiplicity": "one"}` | `{"judgement": "disputed", "players": [["old-a1"], ["old-a2"]], "reason": "several players in one account", "multiplicity": "one"}` |
| MECH-024 | event_role | missing-evidence | `{"judgement": "disputed", "players": [["old-c1"], ["old-c2"]], "reason": "accounts name different players", "multiplicity": "one"}` | `{"judgement": "disputed", "players": [["old-c1"], ["old-c2"]], "reason": "accounts name different players", "multiplicity": "one"}` |
| ORG-017 | authorised | missing-evidence | `{"judgement": "disputed"}` | `{"judgement": "disputed"}` |
| ORG-023 | capable | missing-evidence | `{"judgement": "disputed"}` | `{"judgement": "disputed"}` |
| ORG-001 | office_holders | missing-evidence | `{"holders": ["bea"], "conflict": false}` | `{"holders": ["bea"], "conflict": false}` |
| ORG-002 | office_holders | missing-evidence | `{"holders": ["bea", "cal"], "conflict": true}` | `{"holders": ["bea", "cal"], "conflict": true}` |
| ORG-003 | office_holders | missing-evidence | `{"holders": ["bea"], "conflict": false}` | `{"holders": ["bea"], "conflict": false}` |
| ORG-004 | office_holders | missing-evidence | `{"holders": ["dan", "eve"], "conflict": false}` | `{"holders": ["dan", "eve"], "conflict": false}` |
| ORG-005 | office_holders | missing-evidence | `{"holders": ["bea", "eve"], "conflict": false}` | `{"holders": ["bea", "eve"], "conflict": false}` |
| ORG-006 | office_holders | missing-evidence | `{"holders": ["bea", "eve"], "conflict": true}` | `{"holders": ["bea", "eve"], "conflict": true}` |
| ORG-008 | office_holders | missing-evidence | `{"holders": ["cal"], "conflict": false}` | `{"holders": ["cal"], "conflict": false}` |
| ORG-011 | holds | wrong-judgement | `{"judgement": "disputed", "status": "DISPUTED"}` | `{"judgement": "unknown", "status": "NOT_YET_KNOWN"}` |
| TEMP-017 | holds | wrong-judgement | `{"judgement": "pending", "status": "UNKNOWN"}` | `{"judgement": "not holding", "status": "INFERRED"}` |
| X-001 | office_holders | missing-evidence | `{"holders": ["bea", "cal"], "conflict": true}` | `{"holders": ["bea", "cal"], "conflict": true}` |
| X-002 | office_holders | missing-evidence | `{"holders": ["bea", "cal"], "conflict": false}` | `{"holders": ["bea", "cal"], "conflict": false}` |
| X-003 | office_holders | missing-evidence | `{"holders": ["dan"], "conflict": false}` | `{"holders": ["dan"], "conflict": false}` |
| X-011 | event_role | missing-evidence | `{"judgement": "disputed", "players": [["b1"], ["b2"]], "reason": "accounts name different players", "multiplicity": "one"}` | `{"judgement": "disputed", "players": [["b1"], ["b2"]], "reason": "accounts name different players", "multiplicity": "one"}` |
| X-015 | event_role | missing-evidence | `{"judgement": "disputed", "players": [["b5"], ["b6"]], "reason": "several players in one account", "multiplicity": "one"}` | `{"judgement": "disputed", "players": [["b5"], ["b6"]], "reason": "several players in one account", "multiplicity": "one"}` |
| X-019 | capable | missing-evidence | `{"judgement": "disputed"}` | `{"judgement": "disputed"}` |
