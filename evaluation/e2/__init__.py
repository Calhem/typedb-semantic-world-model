"""Stage E2 evaluation harness (LABS-1.061; design docs/stage-e/stage-e2-evaluation-design.md, decisions
docs/stage-e/stage-e2-decisions.md). Harness only: it calls the public readers and never changes one.

- `values`: JSON normalisation of reader answers, the answer path language, and comparison (sets, ordered lists,
  numeric tolerances, rotations).
- `readers`: the reader templates (GAP-HARNESS-3): how each reader is called, what in its answer is cited as
  supporting evidence, and which derivations it presents.
- `plan`: the multi-step plan runner (one or more reader calls whose parameters may come from earlier answers).
- `worker`: runs one scenario's questions in a child process, so that the hard execution budget can stop a question.
- `score`: correctness, evidence (required, admissible, forbidden), derivations, path agreement, and gap probes.
- `report`: per-family and per-class summaries, the acceptance criteria, and the separate gap-probe section.
- `check`: the question format checker; `run`: the command line.

The question format here is the harness's own (described in check.py). The E2 reader contracts, questions, fixtures
and gold are not written yet: they wait for the owner's approval of the contracts (E2-D3).
"""
