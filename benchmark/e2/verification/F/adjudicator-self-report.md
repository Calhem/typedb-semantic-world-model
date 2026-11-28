# Adjudicator self-report (adj-F)

## Files read (all inside WORKDIR)
- pack/README.md, pack/MANIFEST.json, pack/question-format.md, pack/answer-form.md, pack/gaps.md, pack/fixture-format.md
- pack/competency-questions.md (F family table)
- pack/reader-contracts-author-edition.md: §0 (0.1-0.12 in full), Part A introduction, holds evidence roles and holds contract, Part B in full (transform_between, where, poses, frame_info)
- pack/world-ontology-v0.2.md: §3.5, §5.2-§5.6, §6.1-§6.2, part of §7 (C2)
- fixtures/e2-f-anchor-assembly.json, e2-f-disputes.json, e2-f-variant.json, e2-f-workshop.json
- packet.jsonl (all 23 items)

## Isolation statement
I read only files inside WORKDIR. I used no web access, spawned no agents, and ran no project program. I ran only
`python3 -I` with the standard library to print the packet and fixtures, check one angle (2·atan2(0.28, 0.96)), and
write and check out/resolutions.jsonl. The helper script was kept in a sibling scratch directory (adj-F-tools) and
read nothing outside WORKDIR. No program output was consulted.

## Outcome
23 items: 11 author, 10 verifier, 2 merged, 0 quarantine. Every verifier flag (ill_posed or contract_ambiguity:
F-002, F-009, F-010, F-011, F-012, F-025, F-033) was resolved as well-posed, with the reason recorded.

## Principles applied consistently
- Supporting admissibility for where follows evidence-table row 1 (every positioned candidate) together with §0.4 Components, so conflict-pair members are admissible (not required) as supporting.
- admissible_premises follow the §0.7 definition (visible, usable, applicable), with no extra relevance filter.
- Forbidden only where the text states a never-cite rule: alternatives (unaccepted, incomparable), claims invisible at as_of, superseded claims, another world's claims. A visible claim that merely does not hold at t is inadmissible but not forbidden.
- G probes accept any non-fabricating no-answer status (gaps.md).
