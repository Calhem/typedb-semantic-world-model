# Stage E1 reasoning benchmark (LABS-1.051)

Competency questions for the world model's public reasoning API, each with an expected answer specified from the
documented semantics, **never from system output**. Format adapted from the withheld-evaluation specification
([docs/phase-1c/05-withheld-evaluation-spec.md](../../docs/phase-1c/05-withheld-evaluation-spec.md)).

## Evidence tier (read first)
This is a **development-tier** benchmark, not the sealed, withheld set that specification describes:
- the questions and expected answers are **model-authored** inside this project;
- authors worked from the specification documents and documented reader semantics only (below), with instructions not
  to read the implementation, tests or any system output, and the gold was **committed before the harness first ran
  a question** (see the git history of `questions/` and `fixtures/` against `results/`);
- no two-author agreement (kappa) was measured, and nothing is sealed outside the repository.
Results show where the implementation and its own specification agree; they are not evidence of generalisation.

**Recorded under LABS-1.052:** E1 is development-tier evidence; the external sealed evaluation is deferred; all 272
questions are kept. Clarifications and the revised evaluation, which leave this frozen benchmark unchanged, are in
[CLARIFICATIONS.md](CLARIFICATIONS.md) (`results-revised/`). Results are reported in pairs: the original frozen
evaluation, **267/272** (`results/`), and the revised one, **272/272**, labelled reconciled development-specification
conformance (`results-revised/`) (LABS-1.053).

## Layout
| Path | What |
|---|---|
| `TEMPLATES.md` | the question templates: what each asks, its parameters and its outcome vocabulary |
| `spec/reader-docs.md` | the documented semantics of every reader the templates use (verbatim documentation strings) |
| `fixtures/<scenario>.json` | scenario fixtures: what was said and by whom, in a neutral step format (below) |
| `questions/<category>.jsonl` | one question per line (below) |
| `results/` | harness outputs (machine- and human-readable), written only by `evaluation/run.py` |

## Specification sources (what gold may rest on)
1. `docs/architecture/world-ontology-v0.2.md` (frozen baseline), especially sections 4 to 7.
2. `docs/core-0.3/README.md` (deviations D1 to D14) and `docs/core-0.3/supersession-and-endings.md`.
3. Approved decision documents: `docs/core-0.4/pre-e-increment-b-design.md` (canonical judgement, section 2.4 labels),
   `pre-e-increment-c-design.md` (rule Q), `pre-e-increment-d-design.md` (event roles ER-1 to ER-8),
   `pre-e-identity-design.md` and `pre-e-di16-clarification.md` (ID-1 to ID-9), `pre-e-multiplicity-design.md` with the
   restriction in `pre-e-decision-gate.md` section 3.2 (MP-1 to MP-5), `docs/plans/core-0.4-plan.md`.
4. `benchmark/e1/spec/reader-docs.md`.
Not allowed: `src/`, `tests/`, `probes/` and their outputs, `docs/core-0.4/*-output.md`, benchmark results, or calling
any reader.

## Fixture format
```json
{"id": "org-1", "description": "...", "profiles": ["organisation"],
 "steps": [
   {"op": "entity", "kind": "person", "id": "bea"},
   {"op": "world", "id": "w", "kind": "actual"},
   {"op": "attest", "id": "a-bea-1", "world": "w", "type": "located-at", "roles": {"located": "box", "place": "dock"},
    "start": "T1", "until_superseded": true, "attester": "hr", "accepted_by": ["system"]},
   {"op": "mark", "name": "before-review"}
 ]}
```
- **Times:** `"T<d>"` is 2026-11-`<d>` 09:00 UTC; `"T<d>h<hh>"` sets the hour. Valid times only.
- **Knowledge times:** `{"op": "mark", "name": N}` names the moment between two steps (every write advances the clock).
  Questions and worlds refer to it as `"@N"`.
- **Ids:** every step that creates something takes the id given; attestations get exactly the `id` of their step, so
  questions name evidence by these ids. An account's id is its description's id.
- `accepted_by` (any attesting step): each listed perspective accepts the attestation(s) the step wrote (for an
  account: its own attestation, classifications and describes link). `{"op": "accept", "target": id, "holder": p,
  "verdict": "accepted" | "rejected"}` does it separately.

| op | parameters (besides `id`) | writes |
|---|---|---|
| `entity` | `kind` (core kind, `person`, `organisation`, `sample`, `capability`), `name` | a particular or concept |
| `world` | `kind` (`actual`, `hypothetical`), `base`, `branch_at` (T), `knowledge_at` (@mark) | a world |
| `attest`, `deny` | `world`, `type`, `roles`, `start`, `end`, `until_superseded`, `attester`, `stance` | an attestation (deny: polarity false) |
| `end` | `world`, `target`, `at` | the attester's own claim gets an end (a superseding restatement) |
| `correct` | `world`, `target`, then as `attest` | a correction by the same attester (`supersedes`) |
| `accept` | `target`, `holder`, `verdict` | an acceptance decision |
| `account` | `world`, `roles`, `start`, `end`, `type` (event type), `kind`, `occurrence`, `attester` | an event description, its attestation, optional classification and describes link |
| `move` | `world`, `thing`, `to`, `at`, `actor`, `attester` | a movement (fixtures use only moves that are recordable) |
| `grant` | `world`, `holder`, `concept`, `context`, `polarity`, interval, `attester` | a classification (capability, role, category) |
| `depend` | `world`, `dependent`, `dependee`, `kind`, interval, `attester` | a dependency |
| `appoint` | `world`, `holder`, `office`, `context`, `polarity`, interval, `attester` | an office holding (organisation) |
| `declare_exclusive` | `world`, `office`, `context`, interval, `attester` | a single-holder office constraint |
| `authorise` | `world`, `grantor`, `holder`, `power`, `scope`, interval, `attester` | conferred authority |
| `employ` | `world`, `employer`, `employee`, interval, `attester` | employment |
| `act_in_office` | `world`, `official` (one or a list), `office`, `context`, `start`, `occurrence`, `kind`, `attester` | an official-act account |
| `connect` | `world`, `a`, `b`, `joint_kind`, interval, `attester` | a mechanical connection |
| `replace_part` | `world`, `assembly`, `removed`, `fitted` (one or a list), `start`, `occurrence`, `attester` | a replacement account and its claimed part-of effects |
| `take_sample` | `world`, `sampler` (one or a list), `specimen`, `sample`, `start`, `occurrence`, `attester` | a sampling account and its claimed effects |
| `certificate` | `name`, `reference` | a calibration certificate (laboratory) |
| `calibrate` | `world`, `certificate`, `instrument`, interval, `attester`, `polarity` | a calibration claim |

Intervals: `start`, `end` (T), `until_superseded` (true: holds until its attester records otherwise; without it and
without `end`, the end is UNKNOWN). Attester default: `system`.

## Question format (one JSON object per line)
```json
{"id": "ORG-007", "category": "organisation", "scenario": "org-1",
 "question": "Who holds the site-manager office at Acme on 10 November?",
 "template": "office_holders", "params": {"world": "w", "office": "site-manager", "context": "acme", "t": "T10"},
 "expected": {"holders": ["bea", "cal"], "conflict": true},
 "required_evidence": ["appt-bea", "appt-cal", "excl"], "forbidden_evidence": [],
 "justification": "Both appointments are accepted and overlap at T10; the exclusive-office constraint is accepted, so the office is DISPUTED and both holders are listed (organisation module notes; increment B 2.4).",
 "spec": ["organisation module notes", "pre-e-increment-b-design 2.4"],
 "uncertainty": "none", "adversarial": false, "difficulty": "medium"}
```
Every field is required. `expected` holds only the fields the template defines (TEMPLATES.md); a field left out is
not scored. `uncertainty` says what is uncertain in the expected answer itself (or "none").

## Scoring
- **Correct** (0/1): every expected field matches the actual answer (lists compared as sets unless the template says
  ordered). No partial credit.
- **Evidence:** recall over `required_evidence` and any cited `forbidden_evidence`, reported separately.
- **Failure category** for every incorrect item: `wrong-judgement`, `wrong-values`, `missing-evidence`,
  `forbidden-evidence`, `error` (the reader raised), `unsupported` (no public reader answers the template), and,
  after adjudication only, `gold-suspect` (the expected answer may misread the specification). Expected answers are
  never edited to make a question pass.
- Every question runs on both query paths (selective and full load); the two answers must also agree.
