# Verifier self-report (ver-P)

## Files read (all inside WORKDIR)
- pack/README.md, pack/question-format.md, pack/answer-form.md, pack/MANIFEST.json, pack/gaps.md
- pack/fixture-format.md, pack/competency-questions.md
- pack/reader-contracts-author-edition.md: §0 (0.1-0.12) and Part D in full (shared Stage B rules, causes_of, effects_of, explain, changes, process_steps, before, interval); Part A head (lines 249-340); heading list of the rest
- pack/world-ontology-v0.2.md: §3.2, §4, §5, §6 (and its heading list)
- fixtures/e2-p-batch.json, fixtures/e2-p-timing.json, fixtures/e2-p-accounts.json
- questions-blind.jsonl

## Files written
- out/verified.jsonl (31 lines: 25 scored H items, 6 G probes)
- out/calc/*.md: time-comparison sheets for P-010..P-018, P-020, P-021, P-024, P-025. No item has a numeric expected value (all expected values are ids, windows/ISO times, statuses, booleans or null), so no numeric calculation sheet is strictly required.
- out/self-report.md

## Isolation
I read nothing outside WORKDIR, ran no project program, used no web access and spawned no agents. Only python3 -I -c (standard library) was used, to assemble and parse-check the JSON and write the sheets.

## Flags
- ill_posed: none.
- contract_ambiguity: none recorded. Two points I judged fixed: (1) P-004: process_steps orders by "interval start" = the step's accepted account interval ([i].start; "an event's times are its accepted occurrence interval"), not the part-of membership start; s7 (membership 10h12, account 10h16) is therefore last. A reading by membership start would give s1, s2, s7, s3, s4. (2) process_steps evidence: only [i].support is cited (contract table), so accounts and describes links are not listed as admissible supporting evidence for process_steps steps.
