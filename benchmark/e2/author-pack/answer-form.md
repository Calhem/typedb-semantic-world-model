# E2 answer form (author pack v1.1 addendum)

How an answer looks when the evaluation compares it with `expected`. These rules concern **notation only**. They
change no semantics.

## Values

| Kind | Form in an answer |
|---|---|
| a time | an ISO 8601 UTC string: `T13h16` in a fixture is `"2026-11-13T16:00:00+00:00"` in an answer. `T<d>` alone is 09:00 |
| a window (uncertain time) | `{"earliest": <time>, "latest": <time or null>}`. An exact time has equal bounds |
| a `changes` transition `window` | a two-item list `[<earliest time>, <latest time>]` |
| a status | its name: `"INFERRED"`, `"DISPUTED"`, `"UNKNOWN"`, `"NOT_YET_KNOWN"`, `"ASSERTED"`, `"STIPULATED"` |
| a transform | `{"q": [w, x, y, z], "t": [x, y, z]}` |
| ids of things, frames, worlds, descriptions | the fixture ids |
| attestation ids in answer fields | the step id for a step that writes one attestation directly (`attest`, `deny`, `position`, `relate_frames`, `claim_cause`, `claim_effect`, `appoint`, `calibrate`, …); never expect the ids of parts the library writes (`<step>/kind:…`, `<step>/activity`, …) as values. Name evidence in the evidence sets instead |
| sets and lists | lists, compared as multisets unless `ordered` |

## Readers with wrapped answers

| Reader | Answer |
|---|---|
| `before` | `{"before": true \| false \| null}`; expect the path `before` |
| `interval` | `{"start": <window>, "end": <window or null>, "attestation": <id>}`, or `null` when there is no usable account; expect `null` with the path `"."` |
| `convert` | `{"value": <number>}`; `convert` takes no `world` parameter |
| `measurements`, `poses`, `facts_about`, `causes_of`, `effects_of`, `process_steps` | a list of entries; address entries by `[field=value]` |

## Fixture steps added in v1.1

| op | parameters (besides `id`) | writes |
|---|---|---|
| `account_again` | `world`, `description` (an earlier `account` or `record_event` step), `start`, `end`, `attester` | another account of the **same** event description over its own interval. Two `account` steps always create two descriptions, even with identical roles |
