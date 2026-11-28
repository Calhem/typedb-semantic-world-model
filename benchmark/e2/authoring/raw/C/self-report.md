# Author C self-report

## Files read (all inside WORKDIR)
WORKDIR = `<work>`

- `WORKDIR/ASSIGNMENT.md` (whole)
- `WORKDIR/pack/README.md` (whole)
- `WORKDIR/pack/MANIFEST.json` (whole)
- `WORKDIR/pack/question-format.md` (whole)
- `WORKDIR/pack/fixture-format.md` (whole)
- `WORKDIR/pack/gaps.md` (whole)
- `WORKDIR/pack/competency-questions.md` (whole)
- `WORKDIR/pack/reader-contracts-author-edition.md`: lines 1-624 (§0 including §0.11; Part A holds, value_at,
  facts_about, occurrence, occurrence_status) and lines 1318-1740 (Part D in full). I listed the headings of the whole
  file. I did not read Parts B and C (spatial, measurement), which are outside family C.
- `WORKDIR/pack/world-ontology-v0.2.md`: headings and a keyword search (causes / initiates / describes / lift), then
  §3.2 (lines 163-212) and §4 to §7 (lines 316-654).
- Directory listings of `WORKDIR`, `WORKDIR/pack` and `WORKDIR/out`.
- My own output files in `WORKDIR/out/`, which I re-parsed with `python3 -I -c` (standard library only) to check that
  the JSON parses and that the counts, evidence ids and step ids are consistent.

I opened, listed and searched nothing outside WORKDIR, used no web access, ran no project program and spawned no agent.
One process note: my first combined `cat` of several pack files produced more output than the tool shows, so the
harness saved it automatically to its own tool-results file outside WORKDIR. I did not open that file. I re-read the
same pack files directly inside WORKDIR instead.

## Outputs
- `out/fixtures/e2-c-plant.json`: causal claims, lifting, describes links, occurrence statuses (C1, C2).
- `out/fixtures/e2-c-press.json`: effect claims and explanations (C3, C4).
- `out/fixtures/e2-c-yard.json`: state histories for `changes` (C5, t1/t2).
- `out/questions.jsonl`: 30 scored class-H questions, C-001 to C-030.
- `out/probes.jsonl`: 9 class-G probes, G-C-01 to G-C-09.
- `out/calc/C-022.md`, `out/calc/C-024.md`, `out/calc/C-025.md`: time-window arithmetic sheets. No question expects
  a numeric field. These sheets show the window and B-time comparisons behind C-022, C-024 and C-025.
- `out/slots.json`, `out/ambiguities.md` (A-01 to A-17), this file.

## Counts
- Case types: positive 12, negative 6, disputed 6, unknown 4, refusal 2.
- Competencies: C1 6 (C-001, C-002, C-004 to C-007), C2 4 (C-003, C-008 to C-010), C3 6 (C-011 to C-016),
  C4 5 (C-017 to C-021), C5 7 (C-022 to C-028), t1 > t2 / t1 = t2 2 (C-029, C-030).
- as_of: C-003, C-011, C-026. Perspective: C-006 (inspector), C-014 and C-028 (contractor). Ambiguous attribution:
  C-026, C-027. B-time boundary examples: C-024 (consistent at equality), C-025 (unresolved). Also C-018 (explain
  exclusion against an uncertain start window).
- Adversarial: 26 of 30.
- Slots: T-C1 C-002, T-C2 C-003, T-C3 C-001, T-C4 C-012, T-C5 C-013, T-C6 C-007.

## What I was unsure of (details in ambiguities.md)
- T-C3: the slot asks for the describes links as required evidence, but causes_of cites only the claim's own
  attestations. I required the links through explicit `holds` steps on the `describes` contents (A-05).
- Requiring the initiating claims' attestations (ce-*) in explain questions. The contract says a question "may" require
  them, and that no field carries them yet (A-09).
- The role of the assertion on a polarity-disputed state side inside effects_of and explain: it is admissible in both
  roles and required in neither (A-08).
- How windows are serialised (two-item lists of fixture time strings) (A-15). Several status values (ASSERTED) are not
  expected because the default basis is unfixed (A-01).
- Some contract sentences in the author edition are cut off (causes_of §4 "What counts as an accepted link is",
  explain §6 "and stays", changes §3 and §6). Where they mattered, I designed the fixtures so that the gold does not
  depend on the missing text, or relied on the overriding §0.11 decisions (SD-CAU-2, SD-CAU-8).
- The `targets` field: the assignment names slots but gives no explicit `targets` value. I put the slot id in `targets`
  on the six slot questions, and `slots.json` holds the authoritative mapping.
