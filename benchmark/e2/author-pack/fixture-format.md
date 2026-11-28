# E2 fixture format (author pack)

A fixture is a JSON object listing **what was said, by whom and when**, as steps in order. It describes the
represented world's records only. It never says what any reader answers.

```json
{"id": "s-chain-1", "description": "...", "profiles": ["organisation", "laboratory"],
 "steps": [
   {"op": "entity", "kind": "spatial-frame", "id": "A"},
   {"op": "world", "id": "w", "kind": "actual"},
   {"op": "relate_frames", "id": "ab", "world": "w", "parent": "A", "child": "B", "translation": [1.0, 0.0, 0.0],
    "start": "T1", "until_superseded": true},
   {"op": "mark", "name": "after-ab"}
 ]}
```

## Times, knowledge times, ids

- **Valid times:** `"T<d>"` is 2026-11-`<d>` 09:00 UTC (d = 1 to 30). `"T<d>h<hh>"` sets the hour (00 to 23). A
  two-item list `["T3", "T5"]` is an **uncertain instant** known to lie in the closed window [T3, T5]. A window may be
  used wherever a step takes a time (`start`, `end`, `at`).
- **Intervals:** `start`, `end`, `until_superseded`. With `until_superseded: true` the content holds until its
  attester records otherwise. With neither `end` nor `until_superseded`, the end is unknown. Valid-time intervals are
  half-open (SD-CAU-5).
- **Knowledge times:** `{"op": "mark", "name": N}` names the moment between two steps. Every write advances the
  recording clock. A question passes `"as_of": "@N"`. A step written after the mark is invisible at `@N`, and so is an
  acceptance or supersession written after it.
- **Ids:** every step that creates something takes its `id`. Evidence is named by step id (reader contracts §0.5,
  including the `<step>/<part>` names for library-written parts).
- **Attesters and acceptance:** the attester defaults to `system`, which accepts its own claims. `accepted_by`
  (any attesting step) makes each listed perspective accept everything the step wrote.
  `{"op": "accept", "target": <step>, "holder": <perspective>, "verdict": "accepted" | "rejected"}` does it separately.
  A claim by another attester that nobody accepted is **unreviewed** for the system perspective.
- **Profiles:** `organisation` (persons, organisations, offices) and `laboratory` (certificates, calibration,
  sampling) are installed by listing them. `mechanical` adds connections and replacement. Kinds such as `person` and
  `organisation` need the organisation profile.

## Entity kinds (`{"op": "entity", "kind": K, "id": X, "name": optional}`)

`physical-object`, `place`, `occurrence`, `information-object`, `social-object`, `spatial-frame`, `category`,
`social-role`, `capability`; with the organisation profile, `person` and `organisation`; with the laboratory profile,
`sample`. Units and quality kinds are defined by their own ops.

## Worlds

`{"op": "world", "id": "w", "kind": "actual"}`; a variant is
`{"op": "world", "id": "v", "kind": "hypothetical", "base": "w", "branch_at": "T5", "knowledge_at": "@mark"}`. A
variant sees its base up to its branch point (contracts §0.2).

## Content types and their roles (for `attest`, `deny`, `correct`, `claim_effect` and question parameters)

| Type | Roles | Parameters |
|---|---|---|
| `existence` | `existent` | |
| `located-at` | `located`, `place` | |
| `part-of` | `part`, `whole` | |
| `member-of` | `member`, `group` | |
| `depends-on` | `dependent`, `dependee` (optional `kind`) | |
| `classified-as` | `classified`, `class`, optional `context` | |
| `office-holding` (organisation; a kind of `classified-as`) | `classified` (holder), `class` (office), `context` | |
| `exclusive-office` (organisation) | `office`, `context` | |
| `employment`, `authorisation` (organisation) | `employer`, `employee`; `grantor`, `holder`, `power`, `scope` | |
| `has-quality` | `bearer`, `quality`, `value`, `unit` | `lower`, `upper`, `coverage-level` |
| `same-as` | `same` (two players) | |
| `describes` | `description`, `occurrence` | |
| `initiates`, `terminates` | `event`, `outcome` | |
| `causes` | `cause`, `effect` | |
| `positioned-in` | `positioned`, `frame` | `x-min`, `x-max`, `y-min`, `y-max`, `z-min`, `z-max`, `qw`, `qx`, `qy`, `qz` |
| `frame-transform` | `parent`, `child` | `tx`, `ty`, `tz`, `qw`, `qx`, `qy`, `qz` |
| `anchored-to` | `frame`, `anchor` | |
| `calibration-of` (laboratory) | `certificate`, `calibrated` | |
| `connected-to` (mechanical) | `endpoint` (two players), `joint-kind` | |

Event descriptions (`account`, `record_event` and the profile acts) take the event roles `actor`, `patient`,
`instrument`, `location`, `origin` and `destination`.

## Steps

**General steps (as in E1):**

| op | parameters (besides `id`) | writes |
|---|---|---|
| `attest`, `deny` | `world`, `type`, `roles`, `params`, `start`, `end`, `until_superseded`, `attester`, `stance` | an attestation (`deny`: polarity false) |
| `correct` | `world`, `target` (step), then as `attest` | the same attester's correction, superseding the target |
| `end` | `world`, `target` (step), `at` | the attester's own claim given an end |
| `accept` | `target`, `holder`, `verdict` | an acceptance decision |
| `account` | `world`, `roles`, `start`, `end`, `type`, `kind`, `occurrence`, `attester` | an event description and its attestation; `kind`: a category classifying it (`<step>/kind:<kind>`); `occurrence`: a describes link (`<step>/describes`) |
| `move` | `world`, `thing`, `to`, `at`, `actor`, `attester` | a movement account and its location effects |
| `grant` | `world`, `holder`, `concept`, `context`, `polarity`, interval, `attester` | a classification |
| `depend` | `world`, `dependent`, `dependee`, `kind`, interval, `attester` | a dependency |
| `appoint` | `world`, `holder`, `office`, `context`, `polarity`, interval, `attester` | an office holding (organisation) |
| `declare_exclusive` | `world`, `office`, `context`, interval, `attester` | a single-holder office constraint (organisation) |
| `act_in_office` | `world`, `official`, `office`, `context`, `start`, `end`, `occurrence`, `kind`, `attester` | an official-act account (organisation) |
| `certificate` | `name`, `reference` | a calibration certificate (laboratory; no attestation) |
| `calibrate` | `world`, `certificate`, `instrument`, interval, `attester`, `polarity` | a `calibration-of` claim (laboratory) |
| `connect`, `replace_part`, `take_sample`, `employ`, `authorise` | as E1 | profile acts |

**E2 steps:**

| op | parameters (besides `id`) | writes |
|---|---|---|
| `position` | `world`, `thing`, `frame`, `x`, `y`, `z` (each a number, exact, or `[lower, upper]` in metres), `orientation` (unit quaternion `[w, x, y, z]`, optional), interval, `attester` | `positioned-in(thing, frame)` with those ranges |
| `relate_frames` | `world`, `parent`, `child`, `translation` `[x, y, z]` m, `rotation` `[w, x, y, z]` (default identity), interval, `attester` | `frame-transform(parent, child)`: the child's origin is at `translation` in the parent and its axes are rotated by `rotation`, so that p_parent = R(q) p_child + t. Parent and child must differ. |
| `anchor_frame` | `world`, `frame`, `anchor`, interval, `attester` | `anchored-to` |
| `define_unit` | `name`, `dimension`, `si_factor` (default 1), `si_offset` (default 0) | a unit: SI value = value × si_factor + si_offset (no attestation) |
| `define_quality_kind` | `name`, `dimension` | a quality kind (no attestation) |
| `measure` | `world`, `bearer`, `quality`, `value`, `unit`, `uncertainty` (standard uncertainty u, in `unit`), `k` (coverage factor, default 2), `start`, `end`, `instrument`, `operator`, `conditions` (list of strings), `calibration` (reference text), `occurrence`, `persists`, `supersedes` (step), `attester` | the reported content `has-quality` with the SI range [v − k·u, v + k·u] (converted to SI) and its coverage level (`<step>`); the measurement activity's account (`<step>/activity`, `<step>/kind:measurement`); the result record links (`<step>/produced`, `<step>/reports`). The content is attested over the activity's interval, or from its start until superseded with `persists: true`. |
| `claim_cause` | `world`, `cause`, `effect` (event descriptions or occurrences), `polarity`, interval, `attester` | a `causes` claim |
| `claim_effect` | `world`, `event` (description step), `kind` (`initiates` or `terminates`), `type`, `roles`, `params`, `polarity`, interval, `attester` | an effect claim about the content named by type and roles |
| `describe_occurrence` | `world`, `description`, `occurrence`, `polarity`, interval, `attester` | a `describes` link |
| `record_event` | `world`, `roles`, `start`, `end`, `kind`, `ends` (steps whose claims the event ends), `effects` (list of `{type, roles}`), `type`, `attester` | an event description and its attestation over [start, end]; each effect holds from the event's end until superseded (`<step>/effect:<n>`) |
| `declare_existence` | `world`, `thing`, `start`, `end`, `attester` | `existence(thing)` |
| `create_thing` | `world`, `kind`, `name`, `at`, `alt_names`, `attester` | a new particular and its existence from `at` |
| `destroy` | `world`, `thing`, `at`, `reason` | the thing ends at `at`: the system's own claims about it are ended, and other attesters' accepted claims are denied by the system from `at` |

## Conventions binding on E2 fixtures (LABS-1.064 and 1.065)

1. **Explicit instantaneous measurement:** write `measure` with a `start` and **no `end`**, and without `persists`.
   Never write `end` equal to `start`.
   - **What this means for gold:** the gold follows the approved semantics (SD-MEA-2, SD-CAU-5): an explicit
     instantaneous measurement holds at its instant. An instantaneous event is an account with a `start` and no
     `end`; it is treated as an instant in `before`, per the SD-CAU-5 examples.
2. **Causal and effect claims carry no valid interval.** The exception is a question assigned to test SD-CAU-7, which
   says so.
3. **Never rely on self-causation** (ONT-SC-1). No `claim_cause` has the same cause and effect.
4. **Occurrence readers are given occurrences.** An occurrence is an `entity` of kind `occurrence`, or the
   `occurrence` of an account.
5. **Writer validations** (the step is invalid and the fixture would not load):
   - `claim_effect` with a kind other than `initiates` or `terminates`;
   - `relate_frames` with the same parent and child, or with a non-unit rotation;
   - units of the wrong dimension for the quality;
   - non-finite values;
   - a negative uncertainty.
6. **One fixture per scenario family situation.** Several questions share a fixture. A fixture is synthetic: invented
   names, no real organisations.
