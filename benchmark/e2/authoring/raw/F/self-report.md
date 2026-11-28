# Self-report (author F)

## Files read
All inside the work directory `<work>/`:
- `ASSIGNMENT.md`
- `pack/README.md`
- `pack/MANIFEST.json`
- `pack/question-format.md`
- `pack/fixture-format.md`
- `pack/competency-questions.md`
- `pack/gaps.md`
- `pack/reader-contracts-author-edition.md` (§0 in full, Part A in full, Part B in full; Part C and D headings only, plus searches for basis/stipulation terms)
- `pack/world-ontology-v0.2.md` (§3.1 identity, §3.5, §4.1, §4.4, §5, §6, §7; headings and keyword searches elsewhere)
- my own output files under `out/` (to check that they parse)

I listed the work directory (`ls -laR` of WORKDIR) once at the start. I read nothing outside the work directory, did not use web access, did not run any project program and did not spawn agents. The only commands run were shell writes into `out/` and `python3 -I -c` (standard library) for arithmetic and JSON parse and consistency checks.

## Outputs
- `out/fixtures/e2-f-workshop.json`, `e2-f-disputes.json`, `e2-f-variant.json`, `e2-f-anchor-assembly.json` (the last used by probes only)
- `out/questions.jsonl`: 35 scored questions F-001 to F-035, class H
- `out/probes.jsonl`: 6 probes G-F-01 to G-F-06
- `out/calc/F-*.md`: 23 sheets, one for every question with a numeric expected value
- `out/slots.json`, `out/ambiguities.md`, this file

## Counts
- case_type: positive 14, negative 5, disputed 8, unknown 8, refusal 0.
- Competencies: F1 6 (F-001 to F-006), F2 7 (F-007 to F-013), F3 6 (F-014 to F-019), F4 4 (F-020 to F-023), F5 4 (F-024 to F-027), F6 4 (F-028 to F-031), angle_tolerance 2 (F-032, F-033), poses and frame_info 2 (F-034, F-035).
- Variation: as_of 4 (F-028 to F-031); perspective 3 (F-004, F-006, F-011); variant world 4 (F-024 to F-027); alias 2 (F-002, F-009); numeric derived ranges 7 (F-007, F-008, F-009, F-012, F-016, F-024, F-030); adversarial 31 of 35.
- Slots: T-F1 F-002, T-F2 F-010, T-F3 F-011, T-F4 F-012.

## Things I was unsure of
- F-010 and F-011 (T-F2, T-F3): DISPUTED is the reading the contracts support, but not beyond doubt (ambiguities A1); only `status` is expected and all evidence is admissible-only.
- F-012 (T-F4): the judgement None rests on reading "verified conflict" as a conflicting pair (A11).
- F-023: the unknown-end rule comes from the holds contract (A4).
- ASSERTED as the status of actual-world `position` and `relate_frames` steps (A5).
- frame_info id key names `parent` / `child` (A12).
- Whether a forbidden id that is legitimately *listed* as an alternative (for example an unreviewed rival in `alternatives`) counts as "cited": I followed question-format and §0.4 (alternatives are never cited) and forbade only claims that are superseded, invisible at `as_of`, from another world, not holding at t, or unaccepted by the question's perspective. Incomparable statements are not forbidden.
