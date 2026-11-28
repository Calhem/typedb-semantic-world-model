# Ambiguities recorded (LABS-1.065 replacement questions X-031, X-113)

No question was left out. In each case below the field the contract does not fix is simply not expected.

## A1. Default basis of `attest` / `deny` steps (status of undisputed answers)
- Passage: fixture-format.md lists `stance` but no `basis` for `attest`/`deny`; ontology v0.2 §5.3 maps basis to status
  (testimony -> ASSERTED, inference -> INFERRED); holds §3 "Status is the core rule over the deciding attestations".
- Readings: (a) a default `attest` has basis testimony, so established answers are ASSERTED; (b) the basis is
  unspecified by the pack, so the status is not fixed.
- Effect: `status` is not expected in X-031 s3 or in X-113 s1/s2. `holds`, `values` and `support` are expected; DISPUTED
  statuses (X-031 s1, s2) do not depend on basis and are expected.

## A2. Which `holds` field carries a declared-slot rival (X-031 s2)
- Passage: holds §3 lists three ways to DISPUTED (polarity, declared-slot conflict, attested-constraint conflict); the
  evidence table and field table speak only of reasons "polarity" and "constraint" and say `conflicts` is filled "only
  in a constraint dispute".
- Readings: (a) a declared-slot conflict is a "constraint dispute" (its source A0 F-4 is the functional shelf case), so
  the rival claim lb is in `conflicts`; (b) "constraint dispute" means only an attested constraint, and the field used
  for a declared-slot rival is not fixed.
- Effect: the path `conflicts` is not expected. lb is still required conflicting evidence, because §0.4 [E] says a
  DISPUTED holds answer rests on its own claims, the rivals and the constraint, and P-1 makes rivals conflicting,
  whichever field reports them. The `reason` value is not an Answer field and is not expected.

## A3. `alternatives` in X-031 s2 and s3
- Passage: holds/value_at `alternatives`: "unreviewed, not superseded (keyed) attestations with a verdict at t".
- Readings for holds (s2): (a) only unreviewed attestations of the content asked about (none); (b) also unreviewed
  rival contents of the slot (lc). For value_at at T3 (s3): whether lc (start T5) has a "verdict" at T3 (does-not-hold)
  or is silent (SD-MEA-1 speaks of verdicts that are "silent").
- Effect: `alternatives` is expected only in X-031 s1 (lc holds at T6, keyed by located=c-7, unreviewed: fixed) and in
  X-113 (no unreviewed attestation exists at all, so empty under every reading).

## A4. located-at as a declared one-role functional slot
- Passage: the pack does not list the declared slots; ontology v0.2 §4.4 ("INFERRED by functional exclusivity" for two
  places) and §5.3 item 2 ("two places") treat located-at as functional on `located`; the assignment names it.
- Effect: relied on for X-031; key_role and value_role are passed explicitly so no-single-slot cannot arise.
