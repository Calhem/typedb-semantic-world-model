# Self-report, author P (process steps)

## Files read (all inside the work directory)
- ASSIGNMENT.md
- pack/README.md
- pack/MANIFEST.json
- pack/question-format.md
- pack/fixture-format.md
- pack/competency-questions.md
- pack/gaps.md
- pack/reader-contracts-author-edition.md (§0 in full including §0.11; Part A `holds` to `office_holders`; Part D in
  full: shared Stage B rules, `causes_of`, `effects_of`, `explain`, `changes`, `process_steps`, `before`, `interval`;
  Parts B and C only through a text search for "account")
- pack/world-ontology-v0.2.md (§3.2 events and processes, §3.3 in part, §4 propositions and time, §5 epistemic
  architecture, §6 worlds; other sections through text search only)

I read nothing outside the work directory, ran no project program, used no web access and spawned no agents. I used
`python3 -I` (standard library only) to generate the JSON files from my own definitions and to check that they
parse and meet the counts. I deleted those helper scripts afterwards.

## Outputs
- fixtures/e2-p-batch.json, fixtures/e2-p-timing.json, fixtures/e2-p-accounts.json
- questions.jsonl (25 scored, class H, P-001 to P-025), probes.jsonl (6, G-P-01 to G-P-06), slots.json
  (T-P1 P-013, T-P2 P-024, T-P3 P-014), ambiguities.md, this file.
- calc/: empty. No question expects a numeric value (the answers are step lists, judgements, statuses, time windows
  and booleans), so no calculation sheet is needed.

## Counts
- case_type: positive 10, negative 5, disputed 5, unknown 5, refusal 0.
- competency: P1 5 (P-001 to P-005), P2 4 (P-006 to P-009), P3 8 (P-010 to P-017), P4 4 (P-018 to P-021),
  P5 2 (P-022, P-023), several accounts 2 (P-024, P-025).
- variation: as_of 5 (P-002, P-003, P-007, P-017, P-022); perspective 3 (P-003, P-009, P-020); windows 5+
  (P-011, P-013, P-017, P-021, P-024); instantaneous events 7 (P-001, P-012 to P-015, P-017, P-023); variant world 1
  (P-004); adversarial 18 of 25.

## What I was unsure of
- Case-type labels: the pack does not define them. I used positive = a definite affirmative answer; negative = a
  definite "no" (before False, a claimed step not listed, no usable interval); disputed = the answer's subject is
  DISPUTED and kept; unknown = no order follows (before None).
- Notation of times, windows and bare answers (see ambiguities.md, Notation).
- The several-accounts fixture relies on identical account content being one description with two accounts
  (v0.2 4.2 structural identity; the `accounts[*].attesters` field and SD-CAU-10 presuppose such descriptions).
  If the fixture loader made two descriptions instead, P-024's gold (None) would still be what the approved
  semantics gives for the fixture's stated content, but the fixture would not exercise SD-CAU-10.
- Evidence for `process_steps`: the contract names only `[i].support`; I added the accepted accounts that give the
  steps' times and order to the admissible supporting sets (never required), on the basis of D-B-6 and P-IV-1.
