# Adjudicator self-report (adj-X)

## Files read (all inside WORKDIR)
- pack/README.md, pack/question-format.md, pack/answer-form.md, pack/gaps.md, pack/fixture-format.md, pack/MANIFEST.json
- pack/reader-contracts-author-edition.md (in full, including §0, §0.11, §0.12)
- fixtures/e2-x-lab-1.json, fixtures/e2-x-plant-1.json, fixtures/e2-x-proc-1.json
- packet.jsonl (all 27 items)

Not opened: pack/world-ontology-v0.2.md, pack/competency-questions.md, fixtures/e2-x-core-1.json (no disputed item needed them).

## Isolation statement
I read only files inside WORKDIR. I used no web access, ran no project program and spawned no agents. The only
code I ran was python3 -I with the standard library, to print the packet and fixtures, check JSON and write
out/resolutions.jsonl. Two small helper scripts for that sit in the parent scratchpad folder (show.py, mkres.py);
they read only WORKDIR files. No program output was consulted: every decision rests on the contracts and the fixture facts.

## Outcome
27 items: author 1, verifier 15, merged 10, quarantine 1 (X-021).
