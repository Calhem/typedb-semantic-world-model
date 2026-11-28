# E2 author pack

**LABS-1.065.** This pack is everything an E2 question author or gold verifier receives. It is frozen: `MANIFEST.json`
holds the SHA-256 of every file, and the pack's commit is named in the corpus freeze record.

**What kind of evaluation this is.** E2 is a development-tier, specification-conformance evaluation of a world-model
library's public readers. It is not externally independent or sealed.

## Contents

| File | What |
|---|---|
| `reader-contracts-author-edition.md` | the approved reader contracts, with every statement about how any program behaves removed. §0.11 holds the 25 approved semantic decisions and overrides anything else that seems to differ |
| `world-ontology-v0.2.md` | the approved ontology (the frozen architectural baseline), verbatim |
| `fixture-format.md` | how to write a fixture: times, windows, worlds, acceptance, content types and roles, every step |
| `question-format.md` | how to write a question, its expected answer, its evidence sets, a gap probe and a calculation sheet |
| `competency-questions.md` | the approved competency-question forms per family |
| `gaps.md` | the gap ids, and the approved-but-unimplemented fields (probe only) |

Your **assignment** (a separate file given with this pack) says:
- your families;
- how many questions, of which competency forms and case types;
- which questions are targeted at a boundary condition;
- which are G probes, and under which gap;
- where to write your files.

## Rules for authors and verifiers

1. **Use only this pack and your assignment.** Do not open, search or list any other file or directory, and do not
   run any program from the project. You may run plain arithmetic (for example `python3 -I -c` with the standard
   library only) to check a calculation.
2. **Derive every expected answer from the approved semantics** in these documents and from the facts your fixture
   states. Never adjust an answer towards what some program might output.
3. **Ambiguity:** if the contracts do not fix an answer unambiguously, do not invent semantics.
   - **An author** leaves that question out and records the ambiguity in `ambiguities.md`, with the passage and the
     two readings.
   - **A verifier** records it as a disagreement with reason "contract ambiguity".
4. **Keep the two kinds of uncertainty apart.** Uncertainty in the represented world (windows, disputes, unknowns)
   belongs in the expected answer. Uncertainty about what the specification says belongs in the `uncertainty` field,
   or in an ambiguity record.
5. **Make each question exercise an identifiable competency or boundary condition.** Do not write near-duplicates
   that differ only in names.
6. **Never depend on self-causation** (ONT-SC-1 is blocked).
