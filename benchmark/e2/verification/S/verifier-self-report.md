# Verifier self-report (ver-S)

## Files read (all inside WORKDIR)
- pack/README.md, pack/question-format.md, pack/answer-form.md, pack/fixture-format.md, pack/gaps.md, pack/MANIFEST.json (in full)
- pack/competency-questions.md (sections 3.1 to 3.6 table text)
- pack/reader-contracts-author-edition.md: heading list; lines 1-409 (§0 including §0.11 and §0.12, Part A evidence roles and `holds`); lines 695-894 (Part B conventions, `transform_between`, `where`)
- pack/world-ontology-v0.2.md: heading list; §3.5; §5 (5.1-5.6); §6 (6.1-6.3)
- questions-blind.jsonl (all 30 items)
- fixtures/e2-s-gantry.json, fixtures/e2-s-survey.json, fixtures/e2-s-mesh.json (in full)

## Isolation statement
I read nothing outside WORKDIR. I did not list, open or search any parent directory, home directory or repository,
used no web access, ran no project program and spawned no agents. Computations used `python3 -I` with the standard
library only (quaternion composition, inverses, angle gaps, JSON checks). One early shell output was large and the
tool harness saved a copy of it to its own tool-results file outside WORKDIR; I did not open that file and re-read the
data from WORKDIR instead.

## Outputs
- out/verified.jsonl (30 lines: 25 scored, 5 probes)
- out/calc/S-001, S-002, S-003, S-005, S-006, S-007, S-008, S-017, S-018, S-020, S-023 (numeric expected values);
  S-010 and S-011 (supporting arithmetic for the DISPUTED judgements)
