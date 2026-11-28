# Verifier self-report (ver-X)

## Files read (all inside WORKDIR)
- pack/README.md
- pack/question-format.md
- pack/answer-form.md
- pack/MANIFEST.json
- pack/gaps.md
- pack/fixture-format.md
- pack/competency-questions.md
- pack/reader-contracts-author-edition.md (whole file)
- pack/world-ontology-v0.2.md (sections 1 to 6 read in full; heading list of the rest)
- fixtures/e2-x-core-1.json, fixtures/e2-x-lab-1.json, fixtures/e2-x-plant-1.json, fixtures/e2-x-proc-1.json
- questions-blind.jsonl

I read nothing outside WORKDIR: no parent directory, home directory, repository or web resource was opened, listed
or searched. (When the first full print of questions-blind.jsonl was too long, the tool runner saved a copy of that
output outside WORKDIR; I did not open that copy and re-read the questions from WORKDIR instead.) I ran no project
program; python3 -I -c (standard library) was used only for arithmetic and to check that out/verified.jsonl parses
and matches the blind questions' ids, steps, params and expected paths. No agents were spawned.

## Outputs
- out/verified.jsonl: 34 lines (30 scored X questions, 4 G probes).
- out/calc/: X-001, X-002, X-004, X-009, X-027, X-028, X-029.

## Policies used throughout
- Evidence sets are question-level. Admissible supporting evidence includes everything the reader legitimately
  cites as supporting anywhere in each step's answer (e.g. every usable measurement attestation, P-ME-1 / P-MC-1;
  other rows' attested support; every established process step's support), while required evidence is what the
  asked components rest on. An attestation supporting in one step and conflicting in another appears in both sets
  (§0.4).
- Paths with two [*] mappings (records[*].activities[*].instrument) are written as nested lists ([["gauge-q4"]]);
  the flattened equivalent is ["gauge-q4"]. This is notation only.
- Variant inheritance (v0.2 §6.2): an inherited attestation that starts before the branch point and has no ending
  before it continues past the branch in the variant unless the variant's own claim overrides it.
- Position, calibration and part-of steps with no stated basis are treated as testimony (ASSERTED).

## Flags
- ill_posed: X-021 (competency/case_type presuppose an undisputed value_at answer that §0.12 forbids).
- contract_ambiguity: X-006 (support of a window calibration answer across a certificate handover), X-021
  (value_at §3 / DI19 versus §0.12).
