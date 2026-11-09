# Changes to Phase 1B findings

Phase 1B documents are kept unchanged. Where they disagree with this list, this list takes precedence.

| # | Phase 1B said | Phase 1C finding | Kind | Where |
|---|---|---|---|---|
| 1 | KnowRob has "fuzzy time intervals whose start and end lie within ranges (`TimeInterval.h`)" (01 §1.2) | The header *comment* says so, but the implementation stores single optional `since` / `until` points; a missing bound means unbounded (`TimeInterval.cpp`, V) | corrected | 02 §2.8 |
| 2 | KnowRob implements BELIEF with a `confidence` parameter | Confirmed, and refined: BELIEF is a single materialised "best guess"; confidence is a minimum threshold on statements (`ModalStage.cpp`, `GraphSelector.cpp`, V) | refined | 02 §2.8 |
| 3 | Answers: TRUE, FALSE, UNKNOWN, NOT_YET_KNOWN, CONTESTED, PRESUMED (from GUPI) | Replaced by statuses OBSERVED, ASSERTED, INFERRED, PRESUMED, DISPUTED, UNKNOWN, NOT_YET_KNOWN, each true/false where relevant | revised | 02 §2.2 |
| 4 | Persistence policies with PRESUMED answers (02 §2.6) | Full lifecycle defined; presumptions are computed at query time and never stored | refined | 02 §2.3 |
| 5 | Belief confidence vs measurement uncertainty (two notions) | Four: model score, measurement uncertainty, credence (on attribution), derivation strength; calibration rule added | refined | 02 §2.6 |
| 6 | PostgreSQL 18 enforces valid-time integrity (03, 04) | Verified on 18.6, with a caveat: an open range `[t,)` reads as "still true", so baseline B must encode unknown ends explicitly | verified, caveat | environments |
| 7 | GUPI answer test on LongMemEval: "raw" vs "GUPI claims" (05 §5.6) | On LongMemEval, GUPI main formed 0 claims in its own Phase 6D run (V), so the "GUPI" condition reduces to keyword retrieval on that dataset | corrected | 03 |
