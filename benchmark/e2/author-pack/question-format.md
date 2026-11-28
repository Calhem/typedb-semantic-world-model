# E2 question format (author pack)

One JSON object per line in a `.jsonl` file. A question asks one or more **reader steps** about one fixture, and states
the answer the approved contracts give: field by field, with its evidence.

```json
{"id": "S-007", "family": "S", "class": "H", "scenario": "s-chain-1",
 "competency": "S1 composition of two forward transforms", "case_type": "positive",
 "question": "What transform maps frame C coordinates into frame A at T5?",
 "plan": [{"step": "s1", "reader": "transform_between",
           "params": {"world": "w", "source": "C", "target": "A", "t": "T5"},
           "expected": {"status": "INFERRED", "transform.t": [1.0, 2.0, 0.0], "transform.q": [1.0, 0.0, 0.0, 0.0]},
           "tolerance": {"transform.t": 1e-9, "transform.q": {"rad": 1e-9}}}],
 "required_evidence": ["ab", "bc"], "admissible_evidence": ["ab", "bc"],
 "required_conflict_evidence": [], "admissible_conflict_evidence": [], "forbidden_evidence": ["old-ab"],
 "admissible_premises": ["ab", "bc"],
 "derivation": {"rule": "frame-transform/v1", "premises": ["ab", "bc"], "applicability": "both transforms hold at T5 for system"},
 "calc": "calc/S-007.md",
 "justification": "...", "spec": ["contracts transform_between TB-8", "Plan 9.6 conventions"],
 "uncertainty": "none", "adversarial": false, "difficulty": "easy"}
```

## Fields

**Required:** `id`, `family` (S F M C P X), `class` (A, H or G, as your assignment says), `scenario` (fixture id),
`plan`.

**Always also give:** `competency` (the CQ form and what this question tests), `case_type` (`positive`, `negative`,
`disputed`, `unknown`, `refusal`), `question` (plain English), `justification` (why each expected field follows, with
contract citations), `spec` (citations), `uncertainty`, `adversarial` (true or false), and `difficulty` (easy, medium
or hard).

**`uncertainty` records uncertainty in the evaluation specification**, meaning what you are unsure the contract
fixes, or "none". Uncertainty *in the represented world* (a window, a dispute) is part of the expected answer, not of
this field.

**Optional:**
- `subset: "identity"`: the X identity-conflict questions only.
- `gap`: class G only; the gap id or the decision's capability, as assigned.
- `probe`: class G only (below).
- `targets`: copy exactly the value your assignment gives, if any.
- `convention: "frame-identity"`: a frame asked about itself.
- `derivation`: the derivation the answer presents: rule, premises, applicability, or `"none"`.
- `calc`: a calculation sheet path.
- `ordered`: per step.
- `tolerance`: per step.
- `notes`.

## Plan steps

`{"step": "s1", "reader": R, "params": {...}, "expected": {...}, "tolerance": {...}, "ordered": [...]}`.

- **Parameters:** `world` (required), `t` (valid time), `as_of` (`"@mark"`) and `perspective` (default `system`), plus
  each reader's own parameters from its contract heading. `value_at` also takes `key_role` and `value_role`.
  `changes` takes `t1` and `t2` instead of `t`.
- **Earlier answers:** a parameter may take its value from an earlier step: `{"from": "s1", "path": "start.earliest"}`.
- **Expected answers:**
  - Every step of an X question has its own `expected` answer, so a wrong intermediate judgement fails even when the
    final answer is right.
  - The last step of every scored question has one.
  - A step expecting a refusal says `{"refused": true}`. Expect a refusal only where the contract establishes it.

## Answer paths in `expected`

| Syntax | Meaning |
|---|---|
| `"status"`, `"transform.t"` | a field, or a field of a field |
| `"candidates[0].x"` | an item by position. Use only for a list the contract orders |
| `"candidates[*].stated_in"` | the field mapped over a list, giving a list |
| `"records[record=m1-result].raw_value"` | the one item whose field equals the value. Prefer this over positions |

**How values are compared:**
- Lists are compared as multisets unless the step lists the path in `ordered`.
- Dicts are compared key by key, with the same keys.
- Numbers are compared exactly unless a tolerance is stated for the path: an absolute tolerance, or `{"rad": x}` for
  a quaternion (q and −q are the same rotation).
- Expect only fields and values the contracts fix. A field the contract does not fix is not expected.

**`changes` explanations (rule H-9).** If you expect anything inside a `changes` explanation entry, you must also fix
that entry's `attribution`, either directly or by expecting the whole entry or list.

## Evidence (scored questions)

Evidence is named by **fixture step** (contracts §0.5: `<step>` and `<step>/<part>`). For every scored question,
write each set **explicitly**:
- `required_evidence` and `admissible_evidence`: supporting evidence (what the answer rests on). The admissible set
  lists **every** admissible supporting attestation, and includes the required ones.
- `required_conflict_evidence` and `admissible_conflict_evidence`: conflicting evidence (the other side of a dispute).
  Always give both when the reader can cite conflicting evidence. An empty list is allowed.
- `forbidden_evidence`: attestations the answer must not cite in any role. Typical examples: a superseded claim, a
  claim invisible at `as_of`, another world's claim, or another perspective's unaccepted claim.
- `admissible_premises`: for `where` and `transform_between`. These are the fixture steps a derivation may rest on:
  visible in the question world, usable for its perspective, `as_of` and `t`, and of a content type the rule takes
  (`positioned-in`, `frame-transform`).
- A frame asked about itself is a declared convention. Mark the question `"convention": "frame-identity"`, and give
  empty `admissible_evidence` and `admissible_premises` and no required evidence.

Role meanings follow contracts §0.4. An attestation may be supporting in one component and conflicting in another.
Never list an alternative (an unaccepted, superseded or incomparable claim) as supporting.

## Gap probes (class G)

```json
{"id": "G-S-01", "family": "S", "class": "G", "gap": "GAP-SPATIAL-1", "scenario": "s-chain-1",
 "competency": "S7 transform with propagated uncertainty", "question": "...",
 "plan": [{"step": "s1", "reader": "transform_between", "params": {"world": "w", "source": "C", "target": "A", "t": "T5"}}],
 "probe": {"accept": ["UNKNOWN", "NOT_YET_KNOWN", "refusal", "absent"], "path": "transform_uncertainty"},
 "prohibited": "any stated uncertainty on the transform: the model has none, so a value would be fabricated",
 "justification": "...", "spec": [...]}
```

- `probe.accept` lists the **safe outcomes**:
  - `UNKNOWN` and `NOT_YET_KNOWN`: statuses at `probe.path`;
  - `refusal`: an established refusal;
  - `absent`: the probed field does not exist, so nothing is fabricated in its place. This is the usual outcome for
    an approved but unimplemented field.
- `probe.path` is the answer path checked. The default is `status`.
- `prohibited`: say in words which **definite answer or derivation** would be fabricated. These are always failures:
  - an execution error;
  - a timeout;
  - an unestablished refusal;
  - any presented derivation without admissible premises.
- A probe may have an empty plan when no reader can even be asked. It is then listed as not callable.

## Calculation sheets

Every numeric expected value has a sheet `calc/<question id>.md`. Give the formula, the inputs taken from the
fixture, each intermediate value and the result to at least 12 significant digits. Use standard mathematics and the
conventions of the contracts (Plan 9.6 frames; the SI conversion `SI = value × si_factor + si_offset`; the measurement
range `[v − k·u, v + k·u]` converted to SI). Never use any library from the project.
