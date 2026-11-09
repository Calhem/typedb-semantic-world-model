# Initial experiment protocols

Shared rules for every experiment:
- **Preregister** the hypothesis, data, metrics and decision rule in a commit before running (GUPI practice).
- **Baseline B0** for every experiment: a deliberately simple representation answering the same questions.
  Default B0 is an append-only JSON event log plus a current-state dictionary, queried by Python functions.
  (A different database as baseline would need an owner decision, since TypeDB is the only database in the
  explorer project; B0 needs none.)
- **Independent fixtures and annotations.** Anything that scores "correctness" needs material not written by the
  implementer. If none can be found, the experiment is reported as *development only*, as GUPI's were.
- **Held-out data:** at least one scenario per experiment is sealed until the final run.
- Report negative results. Every number comes from a script in the repository.

| # | Hypothesis (brief) | Minimal protocol | Data | Primary metrics | Decision rule (proposal) |
|---|---|---|---|---|---|
| 1 | Portability | Encode W, S, L (competency-questions.md) on one core; count core changes needed per scenario | 3 synthetic scenarios + 1 held-out (vehicle maintenance, from the explorer's model as *input data*) | core changes (target 0 after W), module types per scenario, CQs answered | Fail if the held-out scenario needs a core change that alters an existing meaning |
| 2 | Temporal consistency | Scripted histories: move, disappear, contradict, reappear, reinstate | ~40 timed histories, half sealed | historical query accuracy; **unsupported assertions** (claims of truth with no evidence at that time) | Pass: 0 unsupported definitive answers; accuracy ≥ B0 |
| 3 | Multi-agent knowledge | 3 agents with partial, contradictory, differently sourced knowledge of the same objects | scripted, 30 questions | belief attribution accuracy, wrongful merges | Pass: 0 merges of distinct agents' beliefs |
| 4 | Video understanding | Deferred to Phase 6 | 20-60 s videos with independent annotation | brief's list | Not designed further until the core is reviewed |
| 5 | GUPI integration | Map GUPI's core onto `wop-memory-1`; rerun GUPI's existing retrieval benchmarks and D1 | GUPI's frozen sets | parity on existing tests; schema size; maintainability | Pass: parity. An *improvement* claim needs the independent answer pack GUPI never obtained |
| 6 | Resource efficiency | Same event streams into core-profile TypeDB and B0 | W at 1×, 10×, 100× | concepts/fact, bytes/fact, ingest rate, p50/p95 latency, server RSS, client CPU | Report; no pass mark until baselines exist |
| 7 | Interoperability | Export claims from `wop-robotics-1`, import into `wop-memory-1`, answer CQ 21 | W+S | claims preserved / dropped / transformed | Pass: every drop is reported, none silent |
| R | ROS 2 (ros2-reference-application.md) | rosbag replay through the adapter vs a ROS-native B0 | simulated warehouse bags | see that document | see that document |

**Order:** 1, 2, 3 and 6 need only synthetic data and can run in Phase 2-4. R comes next because the data is dense
in explicit relations (GUPI's most promising untested direction). 5 is a parity check, not a win condition. 4 last.
