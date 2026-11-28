# Self-report, author XI

## Files read
- `WORKDIR/ASSIGNMENT.md`
- `WORKDIR/pack/README.md`
- `WORKDIR/pack/MANIFEST.json`
- `WORKDIR/pack/question-format.md`
- `WORKDIR/pack/fixture-format.md`
- `WORKDIR/pack/gaps.md`
- `WORKDIR/pack/competency-questions.md`
- `WORKDIR/pack/reader-contracts-author-edition.md`: §0 (0.1 to 0.11) and Part A in full (lines 1 to 670); `where`
  (lines 770 to 869); the rest searched with grep for identity terms (same-as, ID-, identity class, aliases, TI-).
- `WORKDIR/pack/world-ontology-v0.2.md`: §3.1 to §3.2 (lines 94 to 213), §3.4 to §6.3 (lines 264 to 553); the rest
  searched with grep for identity terms.
- `WORKDIR/out/` (my own outputs, to check them).

(WORKDIR = <work>)

## Isolation
I read nothing outside WORKDIR. One exception to report: my first command printed five pack files together
(question-format, fixture-format, gaps, competency-questions, MANIFEST). The tool harness saved that long output to its
own tool-results file outside WORKDIR, and I read that saved file to see the output. It held only the contents of those
WORKDIR pack files. I opened no other path, ran no project program, used no web access and spawned no agents.
The only program I ran was `python3 -I -c` (standard library), to check that the JSON parses and that the evidence sets
agree with the fixtures.

## Outputs
- `out/fixtures/e2-xi-chain-1.json`, `out/fixtures/e2-xi-cycle-1.json`
- `out/questions.jsonl`: 12 scored questions, X-101 to X-112, class H, subset identity
- `out/probes.jsonl`: empty (the assignment asks for no probes)
- `out/slots.json`: `{}` (the assignment lists no slots)
- `out/desirability.jsonl`: 12 lines
- `out/ambiguities.md`
- no `calc/` sheets (no numeric expected values)

## Where I was unsure
- The identity rules (ID-1 to ID-9) are only cited, not stated, in the pack. I relied only on the statements quoted in
  ambiguities.md and left out the cases they do not settle (A1 to A4).
- ID-5 is read as "nothing in the group is merged" (A1). X-102, X-103 and X-105 depend on that reading.
- No step expects `status` for a True or False answer, because the default basis of a fixture claim is not stated (A5).
- In the question-level evidence sets, the evidence of each plan step is merged into one set. The links behind a merge
  appear only as support of the same-as steps that ask about them, never as evidence of the content step (ID-D §3.10).
- That a non-system attester's own claims are usable in its own perspective (X-106) rests on v0.2 §5.3.
