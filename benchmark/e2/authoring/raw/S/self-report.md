# Self-report, author S (spatial transformations)

## Files read
All inside WORKDIR = `<work>`:
- `WORKDIR/ASSIGNMENT.md`
- `WORKDIR/pack/README.md`
- `WORKDIR/pack/MANIFEST.json`
- `WORKDIR/pack/question-format.md`
- `WORKDIR/pack/fixture-format.md`
- `WORKDIR/pack/gaps.md`
- `WORKDIR/pack/competency-questions.md`
- `WORKDIR/pack/reader-contracts-author-edition.md`: §0 (0.1 to 0.11) and Part B in full; the Part A preamble and
  the holds / value_at evidence-role section; the list of headings for Parts C and D
- `WORKDIR/pack/world-ontology-v0.2.md`: §1 (start), §3.5, §4, §5, §6, and a keyword search for frame/transform
- my own output files under `WORKDIR/out/`, to check them

I read, listed and searched nothing outside WORKDIR, used no web access, ran no project program and spawned no agents.
My only commands were `python3 -I -c` (standard library only), used to compute and check quaternion arithmetic, to
write and parse the JSON / JSONL outputs and calculation sheets, and to cross-check every expected transform by
mapping random points edge by edge through each chain. Plus `ls`, `sed`, `grep` and `cat` on WORKDIR files.

## Outputs
- `out/fixtures/e2-s-gantry.json`, `out/fixtures/e2-s-survey.json`, `out/fixtures/e2-s-mesh.json`
- `out/questions.jsonl`: S-001 to S-025, all class H
- `out/probes.jsonl`: G-S-01 to G-S-05
- `out/calc/S-001, -002, -003, -005, -006, -007, -008, -017, -018, -020, -023 .md`: every question with a numeric expected value
- `out/slots.json`: T-S1 -> S-023, T-S2 -> S-014, T-S3 -> S-024
- `out/ambiguities.md` (A1 to A9)

## Counts
- case_type: positive 11, negative 3, disputed 6, unknown 5, refusal 0.
- Competencies: S1 5 (S-001 to S-005), S2 4 (S-006 to S-009), S3 4 (S-010 to S-013), S4 3 (S-014 to S-016),
  S5 3 (S-017 to S-019), S6 3 (S-020 to S-022), frame to itself 1 (S-023), truncated 2 (S-024, S-025).
- as_of: 3 (S-014, S-021, S-022). Non-system perspective: 3 (S-004, S-017, S-018); S-019 passes `system` explicitly.
  Variant world: 1 (S-003; S-016 is its actual-world counterpart). Numeric with rotation: 8 (S-001, -002, -003, -005,
  -006, -007, -008, -020). Adversarial: 19 of 25.

## How I used the case types (my interpretation; the pack gives no definitions)
- **positive:** a definite transform (INFERRED).
- **disputed:** DISPUTED (inconsistent chains, rival accepted transforms, accepted denials, truncated with a disputed edge).
- **negative:** a transform is recorded for the needed link, but it does not hold for the question's context (rejected
  by the perspective, not yet started at t, unreviewed by the system), so the answer is UNKNOWN with no transform.
- **unknown:** no chain recorded or reachable at all (NOT_YET_KNOWN, a completed search with no link, a chain only in
  another world or invisible at `as_of`, truncation before the target).

## Points I was unsure of
- **Evidence for DISPUTED answers.** The contract names conflicting evidence only for inconsistent edges, so all
  required conflicting sets are empty and the admissible sets list the legitimate sides (A2, A3). Supporting
  admissible sets are empty for DISPUTED answers, because the evidence table gives a supporting role to chain support
  only when the answer is INFERRED (or a truncated-but-reached UNKNOWN).
- **Admissible premises.** For INFERRED answers I listed every `frame-transform` step that is visible, usable for the
  perspective and `as_of`, holding at t and not disputed (TB-21, §0.7), not only the chain's own steps. Steps of the
  inconsistent triangles are included, because their contents are not themselves disputed. Positions are excluded,
  since TB-21 names `frame-transform` steps for this reader. Non-INFERRED answers have empty premises and derivation "none".
- **`search.complete: true`** is expected on INFERRED and completed-UNKNOWN answers (TB-11; the default limit of
  100,000 is far above any fixture's size). **`search.truncated: true`** on S-024 depends on how examinations are
  counted (A5).
- **The denial's content.** It is written with the same seven parameters as the asserting `relate_frames` step. I
  assume this names the same proposition (v0.2 §4.2 canonical key, 12 significant digits).
- **Quaternion values** are given to about 15 to 16 significant digits, with tolerance {rad: 1e-9}. Translations are
  rounded to 12 decimals, with tolerance 1e-9 m.
