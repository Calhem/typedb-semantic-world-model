# What is verified, and what is not

Phase 1 mixes three kinds of finding. Review the recommendations with this in mind.

| Kind | Meaning |
|---|---|
| **Measured** | Run in this project against TypeDB 3.14.1; script and output in `probes/` |
| **From earlier projects** | Measured in GUPI or the vehicle explorer, under their conditions |
| **From knowledge** | Written from published knowledge to mid-2026, **not re-checked against primary sources in this phase**. No web research or downloads were done |

## Measured
- Probes 1-11 and 13 (schema behaviour): accepted or rejected as recorded. Each tells us what one query shape does.
  None proves that a pattern works at scale or that there is no other way to do something.
- Probe 12 (ingest and lookup speed): **two runs on one laptop in Docker, 2,000 records.** Only the second run's
  output is saved (1,585 records/s; lookup median 1.4 ms, p95 2.1 ms). The first run's figures (1,198 records/s;
  1.5 / 3.4 ms) were read from the console and not saved. Treat both as indicative.
- Server memory (211 MiB; 1.66 GiB) and image size (218 MB): one `docker stats` reading each, with whatever data
  those servers held. Not a footprint benchmark.

## Inconclusive
- **Struct values** (probe 13): defining a struct worked; inserting one failed with a syntax error. Either our
  syntax is wrong or the feature isn't usable yet. To check before any design depends on it.

## Recommendations that depend on unverified assumptions
| Recommendation or claim | Assumption | How to verify | Risk if wrong |
|---|---|---|---|
| Framework licences (DUL, BFO, SUMO, SOSA, SOMA) | As marked *(verify)* in framework-comparison.md | Read each licence at its source | Reuse blocked or attribution needed |
| "KnowRob / SOMA / NEEMs and 3D scene graphs substantially overlap" | Their current scope matches my knowledge | Read current papers and repositories | Overlap over- or under-stated; novelty claim shifts |
| DOLCE-style, 3D core; BFO by mapping | Mapping losses are acceptable for science domains | A small trial mapping of 10 core concepts to BFO | Lunar/scientific reuse harder |
| Types for kinds, relations for everything else | Workable without multiple classification at our scale | Phase 2 fixtures; count concepts per fact | Model too verbose; Exp. 6 cost high |
| Core of ≈20 types suffices | The 22 competency questions are representative | Held-out scenario (vehicle maintenance) in Exp. 1 | Core changes after v1 |
| Profiles: naming index + core-protection tests are enough | Without namespaces, conventions hold | Load all three profiles together in Phase 3 | Collisions at install time |
| "No embedded mode; no geometry, vector or full-text index in 3.14.1" | From GUPI's findings and TypeDB docs as I know them | Check the 3.14 release notes and docs | We may under-use TypeDB |
| ROS 2 facts: LTS releases, arm64 images and Nav2 binaries, rosbag2 MCAP default, REP 103/105, `vision_msgs` types | As documented to mid-2026 | Check the chosen distribution's docs before Phase R | Environment plan changes |
| ROS 2 runs acceptably in Docker on this Mac, headless | Not tried | A one-hour setup trial (needs approval for downloads) | A Linux machine may be needed |
| Simulator ground truth counts as independent annotation | The simulator's state is not authored by whoever writes the adapter's tests | Preregister which simulator fields are truth | Exp. R results less credible |
| ROS 2 success thresholds (p95 < 50 ms, < 1 GB, no topic-rate effect) | Reasonable for a robot's main computer | Agree with you; measure on target hardware | Thresholds arbitrary |
| ROS 2 before video in the order | Explicit relations remove the extraction bottleneck that hurt GUPI | Experiment R | Order may not matter |
| Baseline B0 = JSON log + dictionary is a fair comparison | A stronger baseline (scene graph, relational store) is not required for v1 | Decide in Phase 2 preregistration | TypeDB looks better than a fair comparison would show |
| Simpler representations win at "where is it now", narrative video QA, chat memory | GUPI evidence (chat) + expectation (others) | Experiments R and 4 | — |

## Incomplete research (named in the brief, not covered in depth)
- **Cognitive architectures** (SOAR, ACT-R, BDI): one line each; no detailed reading.
- **Social, biological and scientific domain ontologies; EmotionML** beyond one line; **Semantic SLAM** and
  **costmaps**: only as boundaries ("stays in ROS 2").
- **Nav2, TF2 and tracking:** concept mapping only; no message-level design.
- **Video understanding baselines** (direct video-to-text models): not surveyed; Experiment 4 is deferred.
- **Experiment protocols** are first drafts: sample sizes, statistics and decision rules need preregistration.
