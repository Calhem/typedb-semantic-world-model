# Adjudicator self-report (family M packet, 19 items)

## Files read (all inside WORKDIR)
- pack/README.md, pack/MANIFEST.json, pack/question-format.md, pack/answer-form.md, pack/gaps.md,
  pack/fixture-format.md, pack/competency-questions.md
- pack/reader-contracts-author-edition.md: §0 (0.1 to 0.12) in full; Part A (holds, value_at, facts_about) and
  Part C (measurements, compare_measurements, convert, calibration_status, measurement_calibration) in full
- pack/world-ontology-v0.2.md: searched with grep for the status table (UNKNOWN / NOT_YET_KNOWN), usability and
  denials; not read in full
- fixtures/e2-m-thermal-1.json, e2-m-length-1.json, e2-m-mass-1.json, e2-m-calib-1.json
- packet.jsonl

## Isolation statement
I read no file outside WORKDIR. I used no web access, ran no project program and spawned no agents. The only code I
ran was `python3 -I` with the standard library, to print the JSON files and to build and check out/resolutions.jsonl
(one line per packet id, and the final keys equal to the differing fields). I consulted no program output.

## Outcome
author 6, verifier 9, merged 4, quarantine 0. I resolved every verifier flag (ill_posed on M-002 and M-029;
contract_ambiguity on M-003, M-008, M-020, M-022 and M-027) by keeping the item. The reasons are in each line's
"reason".

## Residual note
For M-002 I judged near-duplication only against items in this packet (M-001). The verifier's comparison with M-009
concerns an item outside the packet, and I could not check it.
