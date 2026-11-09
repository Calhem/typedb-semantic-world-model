# Competency questions

A competency question is a question the model must be able to answer correctly; it is how we test an ontology.
Each has an expected answer on a fixture written in Phase 2. **Fixtures must be authored by someone other than the
person who implements the queries** for the results to count (the GUPI lesson: every favourable result there came
from developer-written material).

Scenarios: **W** warehouse (a robot and a person; a package is collected and removed), **S** social (a robot talks
with two people, one corrects the other), **L** lunar (a rover samples rocks; two instruments disagree).

| # | Scenario | Question | Tests |
|---|---|---|---|
| 1 | W | Where was package P at 10:05? | located-at valid time |
| 2 | W | Where was P after it left the camera's view at 10:07, and on what evidence? | gaps; UNKNOWN vs last seen |
| 3 | W | Who picked up P, when, and from where? | n-ary event roles |
| 4 | W | Is track 17 at 10:03 and track 42 at 10:09 the same package? On what evidence? | identity claim |
| 5 | W | List everything that happened on shelf 3 between 10:00 and 10:10 in order | events, Allen ordering |
| 6 | W | What did the robot believe about P's location at 10:06, and what was later corrected? | belief time vs valid time |
| 7 | W | Which shelf locations are reachable from the dock without passing the restricted zone? | spatial topology, recursion |
| 8 | W | What could the robot do with P (carry, scan) and what prevents it now? | affordance + state |
| 9 | S | What did person A say about person B's job, and does B agree? | attributed claims, dispute |
| 10 | S | Did A seem frustrated, according to whom, and how confident? | affect only as attributed claim |
| 11 | S | Who was in the room when the robot introduced itself? | participation, location over time |
| 12 | S | What does the robot currently believe A's name is, and why did it change? | supersession |
| 13 | S | Which claims about B come only from A? | provenance filter |
| 14 | L | Which samples came from crater C, and in what order were they collected? | part-of place, event order |
| 15 | L | Instrument X says rock R is basalt, Y says anorthosite: what is R's classification? | CONTESTED |
| 16 | L | What was measured at site S, in what units, with what uncertainty? | measurement pattern |
| 17 | L | In the planned (hypothetical) traverse, where does the rover sample next, and how does it differ from what happened? | worlds |
| 18 | all | Which claims have no evidence? (must be zero for v1 acceptance) | provenance integrity |
| 19 | all | Which facts would change if observation O were retracted? | evidence dependency |
| 20 | all | What does each agent know about object X that the others don't? | multi-agent perspectives |
| 21 | W+S | A box the robot saw (W) is the one person A mentions in conversation (S): link and answer "where is the box A asked about?" | cross-profile identity |
| 22 | all | What is the state of X at time t in the simulated world vs the actual world? | world separation |

Questions 1-20 make the brief's "at least 20 competency questions"; 21-22 test interoperability.
**Every question is also answered by the simpler baseline** (see experiment-protocols.md) so we learn which ones
need the typed model.
