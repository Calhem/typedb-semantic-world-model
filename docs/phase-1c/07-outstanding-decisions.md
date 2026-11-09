# 7. Outstanding decisions and summary

## What was verified in Phase 1C
- **Semantics are precise enough to implement and test** for persistence, observed absence, clocks, frame
  corrections, identity and confidence, with 15 counterexamples and 12 new development questions (02).
- **KnowRob's semantics, read from its source,** differ in testable ways: one materialised best guess, unbounded
  missing interval ends, and cross-source confidence thresholds. Perspectives and belief vs knowledge are not new
  and are not claimed (02 §2.8).
- **Environments installed and smoke-tested,** isolated and pinned: PostgreSQL 18.6, a separate TypeDB 3.14.1, and
  ROS 2 Lyrical with Gazebo Jetty and Nav2. A real navigation goal succeeded headless, and an MCAP bag was recorded
  ([environments/README.md](../../environments/README.md)).
- **PostgreSQL's open-ended ranges read as "still true"** (smoke test). Baseline B has to encode unknown ends, which
  is a concrete instance of the invented-continuity risk.
- **GUPI has no existing LongMemEval answer evaluation,** and its main branch forms no claims on that dataset. The
  free retrieval stages were run under a protocol committed beforehand (03, results in 03a).

## What remains uncertain
- Default persistence horizons and reliability grades: set by judgement, untested.
- Whether keeping alternatives (instead of a best guess) helps answers or only adds DISPUTED noise.
- Latency targets on real robot hardware (only a Mac container so far).
- Whether independent authors can be found for the withheld sets (GUPI could not).
- GUPI answer accuracy: needs the paid stage.
- Image reproducibility beyond the ROS apt repository's current versions (pins fail loudly when replaced).

## Decisions required to begin Phase 2
| # | Decision | Recommendation |
|---|---|---|
| 1 | Approve the semantics in 02 (answer statuses AD18, persistence AD6, observed absence AD6a, frames AD5a, identity AD7, confidence AD8) | approve, with default horizons left to profile authors and frozen before sealed runs |
| 2 | Approve or change the **thresholds** (04 §4.4); they are then frozen as `preregistration-v1` | approve as proposed |
| 3 | **Withheld material:** who authors, how many authors, where sealed packages live, whether model-authored material is allowed (05 §5.6) | two human authors; packages in a private location you control; model-authored only as a disclosed, weaker tier |
| 4 | **GUPI paid stage:** approve about **$1.75 (cap $5)** for `gpt-4o-mini` answers and `gpt-4o` judging on 447 held-out + 53 development questions, and provide `OPENAI_API_KEY` | approve; optionally add `gpt-4o` answers (about $8 more) |
| 5 | Re-run all probes on **TypeDB 3.14.2** before Phase 2 (AD16) | yes |
| 6 | Phase 2 scope: specification document + neutral fixture format + A, B and C for the core only, on development questions | yes; no ROS adapter until Phase 2's core passes |
| 7 | Still open from Phase 1: D2 name, D5 licence, D8 outage spool | decide before publishing a specification |
