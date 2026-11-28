# Self-report: author X

## Files read
All inside the work directory <work>:
- ASSIGNMENT.md
- pack/README.md
- pack/MANIFEST.json
- pack/question-format.md
- pack/fixture-format.md
- pack/gaps.md
- pack/competency-questions.md
- pack/reader-contracts-author-edition.md (all of it, §0 and §0.11 included)
- pack/world-ontology-v0.2.md (§3.2 to §3.5, §5 and §6, plus its heading list)
- out/ (my own outputs, and listing the empty out/calc and out/fixtures directories given)

I read, listed or searched nothing outside the work directory, used no web access, ran no project program and spawned no agents. The only programs run were `python3 -I -c` (standard library) for arithmetic and JSON parsing checks, plus shell commands to write and list files inside out/.

## Files written (out/)
- fixtures/e2-x-lab-1.json, fixtures/e2-x-plant-1.json, fixtures/e2-x-proc-1.json, fixtures/e2-x-core-1.json
- questions.jsonl (30 scored, X-001 to X-030, class H)
- probes.jsonl (4 class G, G-X-01 to G-X-04)
- calc/X-001.md, X-002.md, X-004.md, X-009.md, X-027.md, X-028.md, X-029.md
- slots.json, ambiguities.md, self-report.md

## Counts
- Case types: positive 10, negative 5, disputed 6, unknown 5, refusal 4.
- Competencies: X1 4 (X-001 to X-004); X2 4 (X-005 to X-008); X3 3 (X-009 to X-011); X4 4 (X-012 to X-015); X5 3 (X-016 to X-018); X6 4 (X-019 to X-022); holds/value_at refusals and exact content 4 (X-023 to X-026); cross-domain chained measurement and frames 4 (X-027 to X-030).
- Variation: as_of in X-003, X-007, X-016, X-017, X-020; non-default perspective in X-004, X-008, X-014, X-029; variant worlds in X-010, X-015, X-016, X-017, X-018; plans of 3 or more steps in 14 questions; 24 of 30 adversarial.

## Things I was unsure of
- The ambiguities in ambiguities.md (A-1 to A-12); in each case I left the unfixed field out or designed around it.
- Representation assumptions recorded in the `uncertainty` fields: the description id in `explain.initiated_by[*].event` is the account's step id; a system `attest`/`deny` with `stance: "stipulates"` in a hypothetical world has basis stipulation (STIPULATED); `conflict.constraint.support` lists the declare_exclusive step; convert's bare float answer is addressed as `value`; office-holding has no declared slot keyed on `class` alone (consistent with the value_at no-single-slot refusal).
- Times in `params` are written in the fixture notation (T<d>, T<d>h<hh>); remember T<d> is 09:00, so for example T12h12 is noon on the 12th.
- `targets` carries the assignment's slot id for the six slot questions.
