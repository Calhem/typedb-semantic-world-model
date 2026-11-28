# E2 evaluation baseline (LABS-1.065)

| Item | Value |
|---|---|
| Contracts branch verified on the remote | `feature/e2-reader-contracts` at `05e08e0` |
| `main` before the merge | `5ded39a` |
| Merge (pushed and verified with `git ls-remote`) | `d06316c`, a `--no-ff` merge; its tree is identical to `05e08e0` |
| **E2 evaluation baseline** | **`d06316c`** |
| Executable production implementation | **unchanged from `5ded39a`** (`probes/src_semantics_unchanged.py 5ded39a`: no executable or schema difference; only the docstring and comment change in `src/worldmodel/physical.py`). No change under `schema/` or `docs/architecture/` |
| Authoring branch | `feature/stage-e2-authoring`, from `d06316c` |

**Harness prerequisite added on the authoring branch (evaluation code only, not production):**
- **Fixture time windows.** `evaluation/loader.py` `T()` accepts `["T3", "T5"]`, an uncertain instant in a closed
  window, and passes the writers the `(earliest, latest)` pair they already take.
  - **Why it is needed:** without it, the approved window cases (SD-MEA-6, the SD-CAU-5 examples, SD-CAU-10) cannot
    be written as fixtures.
  - **E1 is unaffected:** E1 fixtures use single times only.
- **Authoring metadata fields** are accepted by the checker (`competency`, `case_type`, `derivation`, `calc`,
  `prohibited`). They are not scored.
