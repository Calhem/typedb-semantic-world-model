# Adjudicator C: self-report

## Files read (all inside WORKDIR)
- pack/README.md, pack/question-format.md, pack/answer-form.md, pack/fixture-format.md, pack/gaps.md, pack/MANIFEST.json
- pack/reader-contracts-author-edition.md: §0 (0.1 to 0.12), the Part A holds evidence-role section and the `holds` contract, and all of Part D (causes_of, effects_of, explain, changes, process_steps, before, interval)
- pack/world-ontology-v0.2.md: searched only (grep), for the §3.2 occurrence-identity "Default" and "Revised" lines
- pack/competency-questions.md: searched only (grep), for the C1 to C4 rows
- fixtures/e2-c-plant.json, fixtures/e2-c-press.json, fixtures/e2-c-yard.json
- packet.jsonl (all 16 items)

## Isolation statement
- I read nothing outside WORKDIR. I used no web access and spawned no agents.
- I ran no project program. I used only `python3 -I` with the standard library, to print the JSON files and to write `out/resolutions.jsonl`. The helper script that wrote it is in the session scratchpad, outside WORKDIR. It reads only `packet.jsonl` and writes only `out/`.
- No program output was consulted. Every decision rests on the contract text and the fixture facts.

## Outcome
16 items: 9 decided for the verifier, 6 for the author, 1 merged, 0 quarantined. All four verifier flags were resolved and the items kept (C-008, C-009, C-016, G-C-09).

## Notes for the coordinator
- **Forbidden sets.** I used one principle for every forbidden set. An id may be listed only if it is admissible in no role in any step. It must not be listed if some step legitimately cites it.
- **Per-step limits.** Several items have evidence that is admissible in one step but not in another (C-002, C-003, C-011, C-014). The question-level sets cannot express this. That is a limit of the format, not an ambiguity in the specification.
- **Author pack version.** The authors worked from pack v1.0. Pack v1.1 §0.12 adds the rule that "a lifted answer cites the describes links' attestations", and that rule settles C-002 and C-003.
