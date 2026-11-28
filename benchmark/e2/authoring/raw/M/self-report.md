# Self-report, author M (measurements)

## Files read
All paths are under <work>/:
- ASSIGNMENT.md
- pack/README.md
- pack/question-format.md
- pack/fixture-format.md
- pack/competency-questions.md
- pack/gaps.md
- pack/MANIFEST.json (printed together with the other pack files, not used)
- pack/reader-contracts-author-edition.md: §0 (lines 1-222), Part A (holds, value_at, facts_about, occurrence,
  occurrence_status, office_holders) and all of Part C (measurement and calibration). I also searched it with grep for
  headings, identity/same-as and measurement terms. I did not read Part B (spatial) or Part D (causation) beyond the
  grep hits.
- pack/world-ontology-v0.2.md: §3.1 (from identity uncertainty), §3.2, §3.3, §4.4, §4.5, §5 and §6, plus §7 C1-C7;
  I also searched it with grep for headings.
- My own output files under out/, read only to check them.

I read nothing outside this work directory. I did not list, open or search any other path, ran no project program,
used no web access and spawned no agents. The only programs I ran were python3 -I -c (standard library only, for
arithmetic and JSON parsing) and shell commands (cat, ls, grep, wc) inside the work directory.

## Output
- fixtures: e2-m-thermal-1, e2-m-mass-1, e2-m-calib-1, e2-m-length-1
- questions.jsonl: 35 scored questions (M-001 to M-035, class H); probes.jsonl: 7 probes (G-M-01 to G-M-07)
- calc/: 15 sheets, one for each question with a numeric expected value
- slots.json, ambiguities.md (A-1 to A-12), this file

## Things I was unsure of
- Status ASSERTED for basis-observation measurement contents and for the system's calibration claims (CM §3
  "observation gives ASSERTED"; OBSERVED is not produced).
- Reading the "supporting or alternative" row for statements as supporting for "values stated" questions (M-001,
  M-003).
- M-018: `attested` as a CS answer when the instrument has no certificate (A-10).
- M-022 (T-M5): the label "not established" is reached by elimination under SD-MEA-6 and SD-CAU-10.
- M-030 (T-M2): it depends on the fixture's deny matching l16's content exactly (A-2). DISPUTED follows the contract's
  adjudication in CM §3.
- Path syntax: I used `[field=value]` on top-level lists (for example `[attestation=t1].range`), following the
  `records[record=...]` form and the contracts' own `[*].attestation` notation.
