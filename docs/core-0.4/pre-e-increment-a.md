# Pre-Stage E correction, increment A: atomic logical operations (DI-8)

**Status: implemented on `feature/pre-e-a-atomic-operations`, at the review gate, not merged** (LABS-1.036). Decisions:
R-7 with choices I and J, and the LABS-1.036 qualification that composite writes are atomic, including nested
operations, claimed effects, related objects and events, with no partial data and no logical-time advance on failure
([pre-stage-e-correctness-review.md](pre-stage-e-correctness-review.md), section 6).

## What changed
**A public operation.** `WorldModel.operation()` groups writes into one logical operation:

```python
with wm.operation():
    wm.add_entity("sample", "s-14", id="s-14")
    laboratory.take_sample(wm, w, "ana", "core-1", "s-14", start=t)
```

- Everything written inside is committed together, when the outermost operation ends, or not at all.
- Writers called inside **join** it. Nested operations share its one transaction and its one recorded time.
- Reads inside it see its own writes.
- A failure anywhere leaves nothing written and puts the model's recorded-time watermark back where it was. That
  covers a failed write, an error caught inside the block, a schema change attempted inside a data operation, and a
  failed commit. Cached schema reads are forgotten.
- `operation(schema=True)` is a schema operation (schema changes and data together). A schema writer cannot join a
  data operation: it raises `OperationError`, and nothing is written.

**Every composite writer is one operation:**
- core writers: `attest`, `accept`, `end`, `create_world`, `declare_slot`, `create_thing`, `destroy`, `record_event`,
  `account`, `claim_effect` (its outcome content is now written inside the operation), `measure`, `define_unit`,
  `define_quality_kind`;
- profile writers: `take_sample`, `replace_part`;
- schema writers: `install_module`, `upgrade_to_a0` (all three steps in one schema transaction) and `install_profile`;
- `WorldModel.create` runs every module, the system agent and the core slots as one schema operation, and deletes
  the database if that fails;
- single writes (`add_entity`, `describe_event`, `proposition`, `register_certificate`) join the current operation.

Accepting another source's claim stays its own operation (choice I).

**Every read** goes through one helper. Inside an operation it uses the operation's transaction; otherwise it opens a
read transaction. This covers the core, the profiles and the examples. The writers' `batch=` argument and `_batch()`
remain, as the operation.

Code: `src/worldmodel/operations.py` (new), `model.py`, `dynamics.py`, `qualities.py`, `profiles.py`,
`laboratory.py`, `mechanical.py`, and the readers converted in `agency.py`, `physical.py` and `examples/`.

## Evidence
**Fault injection** (`probes/pre_e_a_atomicity.py`). A failure is injected at every write of 14 composite writers, and
part-way through `WorldModel.create`; the probe records what persisted.

| Writer | Writes | Before (`a8211c4`): failure points leaving partial data | After |
|---|---:|---:|---:|
| `account` (kind and occurrence) | 6 | 5 of 6 | 0 |
| `claim_effect` (new outcome) | 3 | 2 of 3 | 0 |
| `take_sample` | 8 | 7 of 8 | 0 |
| `replace_part` | 8 | 5 of 6 | 0 |
| `record_event` | 7 | 5 of 6 | 0 |
| `create_thing` | 3 | 2 of 3 | 0 |
| `destroy` | 3 | 2 of 3 | 0 |
| `define_unit` | 2 | 1 of 2 | 0 |
| `install_module` | 3 | 2 of 3 | 0 |
| `upgrade_to_a0` | 6 | 5 of 6 | 0 |
| `WorldModel.create` | 25 | 25 of 25 (a database was always left) | 0 (no database left) |
| `measure`, `end`, `install_profile` | 12, 1, 5 | 0 | 0 |

Two more results:
- **Watermark:** before, most writers moved the model's recorded-time watermark on failure. After: never.
- **Recorded times:** before, a composite writer wrote up to four different recorded times. After: exactly one per
  operation.

**Reproductions** (`probes/pre_e_review_reproductions.py`). Only the DI-8 cases changed; every other case behaves as
recorded:
- the registered case: a connection lost before `take_sample`'s second effect claim left the account with one claim.
  Now nothing is written;
- the batched sampling of a *new* sample failed before, because the outcome content was committed outside the batch.
  It now succeeds in one operation.

**Cost** (`probes/pre_e_a_write_bench.py`, two runs each, n = 25). Each operation now opens one write transaction and
no separate read transactions. Before, `take_sample` opened 6 write and 6 read transactions.

| Writer | Median before (ms) | Median after (ms) |
|---|---|---|
| `attest` | 11.4 to 13.6 | 9.4 to 12.7 |
| `account` | 18.3 to 21.7 | 9.1 to 12.2 |
| `take_sample` | 42.7 to 55.7 | 23.2 to 29.7 |
| `replace_part` | 40.8 to 47.9 | 20.8 to 27.6 |
| `record_event` | 28.6 to 33.5 | 17.2 to 20.7 |
| `create_thing` | 10.0 to 11.3 | 6.0 to 7.6 |
| `measure` | 42.6 to 51.1 | 28.8 to 37.4 |

## Tests
**New:** `tests/test_p_operations.py`, 21 tests:
- a failure injected at every write, and at commit, of ten composite writers;
- module installation, upgrade, profile installation and create, failed at every write;
- a caller grouping the creation of a sample with its sampling account: own reads, isolation from other readers, one
  recorded time;
- a user error, and a schema change inside a data operation;
- a caught nested failure (LABS-1.037): `take_sample`, called inside a caller's operation, fails at each of its own
  writes after the first (so it has always made transaction-local changes, which are visible inside the operation),
  and the caller catches the error. The operation is marked for rollback: ending it raises `OperationError`, nothing
  persists and the watermark does not move. With the marking disabled, this test fails;
- recorded time stays monotonic after a rollback;
- the registered DI-8 case;
- cached schema reads after a rollback.

Removing atomicity from `take_sample` makes two of them fail.

**Full suite** at `af028ee`, two runs of each of the four configurations (selective and full load, each with and
without core protection): **470 passed in every run** (449 existing and 21 new). No temporary export, reference or probe
databases were left behind.

One run was repeated. During the second matrix pass, Docker stopped the TypeDB container for lack of memory: it had run
for four days, sharing the Docker machine's 7.7 GB with fifteen other containers. Every test after that point failed to
connect. After a restart, both affected configurations were rerun and passed 470 of 470, with TypeDB's memory sampled
every 30 seconds. It levelled off at about 210 MB across both runs, so the operation mechanism is not accumulating
memory.

## Intentional changes to existing behaviour
1. A composite writer writes **one recorded time** instead of several. No existing test or answer depended on the
   difference (the existing suite passes unchanged), because acceptances, supersessions and knowledge times compare
   different operations.
2. A schema writer called inside a data operation raises `OperationError`, and nothing is written. Before, there was no
   operation to be inside.
3. A failed `WorldModel.create` leaves no database.
4. Writers' `batch=` is accepted but no longer needed: writers join the current operation whether or not it is passed.

No judgement changed. DI-1 to DI-6 and DI-11 reproduce exactly as before.

## Limitations
- **The external clock is not rewound.** After a rollback the model's watermark is restored and nothing is recorded,
  but the clock object itself (a test's fake clock, or the wall clock) has moved on. The next operation's time is
  still later than any committed one.
- **`create(replace=True)`** deletes the existing database before building the new one (as before). If the build then
  fails, no database remains.
- **One operation holds one transaction open** for its whole duration. A schema operation (including `create`) blocks
  other writers to that database while it runs, and a very long operation is subject to TypeDB's transaction timeout.
- **A `WorldModel` is not thread-safe.** One instance runs one operation at a time.
- **Scripts that open TypeDB transactions themselves** (benchmarks, probes) are outside this mechanism. All library
  code goes through it.

## Not changed
DI-1, DI-2, DI-5, DI-6 and DI-11 (increments B to D), DI-3, DI-4, DI-7, DI-9 and DI-10. The foundational ontology and
the schema are unchanged. Stage E has not begun.
