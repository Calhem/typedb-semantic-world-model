# Verifier self-report (ver-F)

Files read (all inside WORKDIR):
- pack/README.md, pack/question-format.md, pack/answer-form.md, pack/fixture-format.md, pack/gaps.md, pack/MANIFEST.json, pack/competency-questions.md
- pack/reader-contracts-author-edition.md (§0 in full; Part A holds, value_at, facts_about; Part B in full)
- pack/world-ontology-v0.2.md (headings; §3.5, §5, §6, §7 C6-C10, via grep/sed)
- fixtures/e2-f-anchor-assembly.json, fixtures/e2-f-disputes.json, fixtures/e2-f-variant.json, fixtures/e2-f-workshop.json
- questions-blind.jsonl

Files written: out/verified.jsonl, out/calc/*.md (23 sheets), out/self-report.md.

I read nothing outside WORKDIR, ran no project program, used no web access and spawned no agents. The only
program run was python3 -I with the standard library, for arithmetic, generating the output files and checking
that the JSON parses.
