# Ambiguities recorded by author P

Each entry: the passage, the two readings, and what I left out or how I avoided depending on it.

## A1. `interval` on a description with several usable accounts
- Passage: contracts `interval` 2 and 5 ("one result"; `attestation`: "the account used"); §0.11 SD-CAU-10 ("every usable account reported (`usable_accounts`)", G-unimpl).
- Readings: (a) `interval` returns one account's start/end and names that account; (b) it returns a combined window
  over all usable accounts (and either account, or both, as `attestation`).
- Left out: no scored question expects `start`, `end` or `attestation` of `interval` for the two-account flush
  description (acc-x / acc-y). The case is only probed (G-P-06, `usable_accounts` accept `absent`). The scored
  SD-CAU-10 questions (P-024, P-025) use `before`, whose certainty rule SD-CAU-10 fixes.

## A2. The end of an instantaneous event (account with a start and no end)
- Passage: fixture-format convention 1 ("an instantaneous event is an account with a start and no end; it is treated
  as an instant in `before`"); fixture-format Intervals ("With neither `end` nor `until_superseded`, the end is
  unknown"); v0.2 3.2 (instantaneous: start window = end window); `process_steps` 2 / `interval` 2 (`end`: Window or null).
- Readings: the reported `end` is (a) equal to the start window, or (b) null / unknown.
- Left out: no question expects `end` for s2c, s6, ev-i3, ev-j3, ev-i4, ev-j4 or ev-k; only their `start` and their
  `before` results (fixed by SD-CAU-5).

## A3. The status of an established step
- Passage: `process_steps` 2 (`status`: "otherwise the support status"); v0.2 5.6 (status follows the basis).
- Readings: the fixture format does not state the default basis of an `attest` step, so an established step's status
  could be ASSERTED (testimony) or another supported status.
- Left out: no question expects `status` of an established step, except s7 in P-004, whose claim carries the explicit
  stance `stipulates` in a hypothetical world (STIPULATED, v0.2 5.2 E7 and 5.6).

## A4. Inherited claims after the branch point
- Passage: v0.2 6.2 ("restricted to valid times before β (their starts before β; their endings counted only before β)").
- Readings: an inherited until-superseded claim that started before β (a) continues to hold after β in the variant, or
  (b) holds in the variant only for valid times before β.
- Avoided: the variant question P-004 asks at t = T10h15, before β = T10h16, where both readings agree; it expects no
  `end` for s4, whose base end (17h) is after β.

## A5. Position of a step without a usable start, and order with windowed starts
- Passage: `process_steps` 5 ("ordered by interval start"); P-PS-1.
- Readings: a step with `start` null, or with a start window, could be placed first, last, or anywhere; windowed
  starts could be ordered by earliest or latest bound.
- Avoided: every question with `ordered` uses a list in which every step has an exact, distinct start (fixture
  e2-p-batch). Lists of R2 (u3 has no start; u4, u5 have windows) are compared as multisets or by field only, and
  order between steps is asked with `before` (P-PS-1).

## A6. `before` with a description that is not yet recorded at `as_of`
- Passage: common 0.2 (records after `as_of` are invisible); common 0.8 / P-5 (an id that names nothing is an
  execution precondition, not an answer).
- Readings: such a call gives (a) null (no usable account) or (b) an execution error.
- Avoided: P-017 makes the account visible at the mark but not yet accepted (the acceptance is recorded after the
  mark), which `before` 4 fixes as null.

## A7. Description ids in answers
- Passage: `process_steps` 2 (`descriptions`: [id]).
- Readings: a description is named by its account step id, or by a library id.
- Left out: `descriptions` is expected only when it must be empty (P-019).

## Notation (not semantics; recorded in each question's `uncertainty`)
- Times in `expected` use the fixture notation (`T13h16`); a Window is addressed by `.earliest` / `.latest`.
- The bare value returned by `before` (bool or null) and the null answer of `interval` are addressed as `answer`.
- The `before`/`interval` `description` parameters name a description by the account step that wrote it; P-024 and
  P-025 also rely on structural identity (v0.2 4.2): acc-x and acc-y write identical content, hence one description
  with two accounts.
