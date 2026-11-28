# Verifier self-report (ver-XI)

## Files read (all inside WORKDIR)
- pack/README.md
- pack/question-format.md
- pack/answer-form.md
- pack/fixture-format.md
- pack/gaps.md
- pack/MANIFEST.json
- pack/competency-questions.md
- pack/reader-contracts-author-edition.md (§0 in full, including §0.11 and §0.12, and Part A in full; the rest searched by keyword: identity, depth, merge, unreviewed and so on)
- pack/world-ontology-v0.2.md (§3.1, §3.4–§4.2, §5.1–§6.3 read; the rest searched by keyword)
- fixtures/e2-xi-chain-1.json
- fixtures/e2-xi-cycle-1.json
- questions-blind.jsonl

I read, listed or searched nothing outside WORKDIR. I used no web access, ran no project program and spawned no agents. The
only program I ran was `python3 -I -c` (standard library), to check that out/verified.jsonl parses and that its step names,
readers, parameters and expected keys match questions-blind.jsonl.

## Outputs
- out/verified.jsonl: 12 items (X-101 to X-112, all class H).
- out/calc/: empty. No item has a numeric expected value: every expected field is a boolean, null, a status or a list of step ids.

## Flags
- ill_posed: 1 (X-112, a near-duplicate of X-102 steps s4, s2 and s3).
- contract_ambiguity: 2 (X-101 and X-107). holds 3 says "a polarity dispute at the nearest deciding depth", and the pack
  never defines "depth" (world nesting or identity hop distance). The gold uses the pooled reading (DISPUTED). The other
  reading gives the asked name's own claim precedence.
