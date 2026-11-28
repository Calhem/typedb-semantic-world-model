# Verifier self-report (ver-M)

## Files read (all inside WORKDIR)
- pack/README.md
- pack/question-format.md
- pack/answer-form.md
- pack/fixture-format.md
- pack/MANIFEST.json
- pack/gaps.md
- pack/competency-questions.md
- pack/reader-contracts-author-edition.md: lines 1-530 (section 0 in full, Part A holds / value_at / facts_about) and lines 985-1339 (Part C in full). Part B (spatial) and Part D (causation) were not needed for these M-family items and were read only as headings.
- pack/world-ontology-v0.2.md: lines 213-512 (3.3 to 6.2) and the heading list
- fixtures/e2-m-calib-1.json, fixtures/e2-m-length-1.json, fixtures/e2-m-mass-1.json, fixtures/e2-m-thermal-1.json
- questions-blind.jsonl

I listed WORKDIR with `find .` from WORKDIR itself. I read nothing outside WORKDIR, used no web access, spawned no agents and ran no project program. The only program I ran was `python3 -I -c` with the standard library: for arithmetic (SI ranges and conversions), to write the calculation sheets, and to check that out/verified.jsonl parses and matches the blind file's ids, steps, parameters, expected paths, tolerances and orderings.

## Outputs
- out/verified.jsonl: 42 lines (35 scored H items, 7 G probes)
- out/calc/*.md: 18 sheets, one for every item with a numeric expected value
- out/self-report.md: this file

## Flags
- ill_posed (2): M-002 is a near-duplicate of M-001 and M-009. In M-029, case_type 'unknown' fits only step s2.
- contract_ambiguity (5): M-003 (the evidence role of a usable statement entry; the gold sets are not affected), M-008 (whether 'held' in CM 3 means visible records; gold uses UNKNOWN per section 0.3), M-020 (the status of an 'expired' calibration judgement), M-022 (the judgement label under SD-MEA-6; gold uses 'not established'), M-027 (d1.usable: ME 6 lists denials as usable=false, but section 0.12 says an accepted denial is usable).
