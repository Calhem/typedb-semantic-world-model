# Verifier self-report (ver-C)

## Files read (all inside WORKDIR)
- pack/README.md
- pack/question-format.md
- pack/answer-form.md
- pack/fixture-format.md
- pack/MANIFEST.json
- pack/gaps.md
- pack/competency-questions.md
- pack/reader-contracts-author-edition.md (in full)
- pack/world-ontology-v0.2.md (sections 3.2, 4.4-6.3 and 7, plus a search for "describes"/"lift")
- fixtures/e2-c-plant.json, fixtures/e2-c-press.json, fixtures/e2-c-yard.json
- questions-blind.jsonl

I read nothing outside WORKDIR, ran no project program and spawned no agents. I used `python3 -I -c` (standard library)
only to print fixture steps one per line and to check that out/verified.jsonl parses and matches the blind file's ids,
step names, parameters and expected paths.

## Outputs
- out/verified.jsonl: 39 items (30 scored C-001 to C-030, 9 probes G-C-01 to G-C-09).
- out/calc/: empty. No expected value is numeric (they are ids, booleans, status words, judgement words and ISO times
  read directly from the fixture), so no calculation sheet applies.

## Flags
- ill_posed: 1 (G-C-09: the premise "the occurrence it is about" is false, e-jam describes no occurrence).
- contract_ambiguity: 3 (C-008, C-009: the role of an accepted claim with applies false/null when the question asks about
  that claim; C-016: the role of an accepted denial inside a polarity-disputed effects_of state side).
- Limitation noted in justifications (not flagged): the evidence sets are per question, so they cannot express
  per-step restrictions (C-002, C-003, C-011, C-014).
