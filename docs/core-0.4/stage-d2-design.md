# Core 0.4 Stage D-2: organisational profile, design (LABS-1.025)

**Status (2026-11-11): design for approval. No D-2 implementation code is written.** Branch
`feature/core-0.4-d2-organisation` from `main` 153c2f2 (D-1 merged).
- Evidence: the draft schema `docs/core-0.4/stage-d2/organisation-0.1.draft.tql`, and `probes/core04_d2_design.py`
  (output `probes/core04_d2_design.out.json`).
- The probe installs the draft as a profile next to `mechanical` in a throwaway database, and checks every claim below
  with the **existing** API.
- Approved basis: D-D-1, D-D-3, D-D-4, D-D-5, D-D-6, D-D-9, D-D-10 (`stage-d-review.md` §8, §8a). Deferred issues:
  `deferred-issues.md`.

## 1. Proposed schema (profile `organisation` 0.1; additive only)
| Type | Definition | Why |
|---|---|---|
| `person sub physical-object` | sortal | a person's identity criteria (v0.2 §3.1). Agency stays a classification (`agent`) |
| `organisation sub social-object` | sortal; organisations and their units | units are organisations `part-of` the parent (core) |
| `employment(employer, employee)` | proposition; employer: organisation, employee: person | v0.2 §3.4's own example of a social relation |
| `office-holding sub classified-as` | proposition: holder (`classified`), office (`class`, a `social-role`), context (`context`, the organisation or unit) | single-holder offices: the slot (class, context) → classified is declared for this subtype only (D-D-5) |
| `authorisation(grantor, holder, power, scope)` | proposition; grantor, holder, scope: particulars; power: a `capability` concept | conferred authority (D-D-3) |
| `official-act sub event` | `official as actor` (the one specialisation, D-D-6), `office` (a social-role), `office-context` (a particular) | an act undertaken in an office |

**Reused from the core, with nothing added:**
- membership: `member-of`;
- organisational structure: `part-of`;
- ordinary (multi-holder) roles: `classified-as(person, role, context)`;
- abilities: `capability` concepts held through `classified-as`;
- agency: `classified-as(x, agent)`;
- appointment and dismissal events: core accounts classified `organisation:appointment` or `organisation:dismissal`,
  with `initiates`/`terminates office-holding` effect claims.

**Seed vocabulary** (prefixed): `organisation:appointment`, `organisation:dismissal` (event kinds).
Offices and powers are domain data, not profile vocabulary.

**Slot metadata:** `office-holding`: (class, context) → classified.

The probe installed the draft with `mechanical` and nothing collided (P1). Writing it found a missing
`plays official-act:official`, now fixed: a specialised role needs its own `plays`.

## 2. Proposed API (`worldmodel.organisation`, functions taking the WorldModel, like `worldmodel.mechanical`)
| Function | Does | Reads |
|---|---|---|
| `employ(wm, world, employer, employee, **attest)` / `employment(wm, world, x, t, …)` | attest; report employments of x with status (disputed listed, not dropped) | per-content judgement |
| `appoint(wm, world, holder, office, context, **attest)` | attest an `office-holding` claim by its source (attester); never refused because the office is held | — |
| `office_holders(wm, world, office, context, t, …)` | who holds the office at t: holders, status (ASSERTED / DISPUTED / INFERRED / UNKNOWN / NOT_YET_KNOWN), and for each holder the attestations with source and acceptance; unaccepted claims as alternatives | `value_of` on the slot, plus per-content judgement |
| `offices_of(wm, world, person, t, …)` | the offices a person holds or is disputed in at t, each with status | per-content judgement, plus the slot check |
| `authorise(wm, world, grantor, holder, power, scope, attester=…, **attest)` | attest an `authorisation`; `grantor` and `attester` are separate arguments, with no default linking them | — |
| `authorised(wm, world, holder, power, scope, t, …)` | is the holder authorised at t? `holds`, `status`, `judgement` (the same six cases as `capable`), and each grant with **grantor and reporting source as separate fields**; `grantor_entitlement: "not assessed"`, always | per-content judgement |
| `act_in_office(wm, world, official, office, context, start, end=None, occurrence=None, attester=…, id=None)` | an `official-act` account | — |
| `official_act(wm, world, event, power=None, …)` | report, concluding nothing: the account (accepted, interval); occurrences with **their own** status; the office at the act's start (`office_holders`: is the official among them, and with what status); authority (`authorised` for `power` in `office-context`); capability (`capable`); agency (`is_agent`). Each is a separate field | the above |

No helper infers anything. In particular, no function concludes authority from an office, an office from an act, or an
act from authority.

## 3. Conflicting appointments: representation and judgement
- **Representation.** Every appointment claim is an attestation of `office-holding(holder, office, context)` by its
  source, over its interval. Write time never refuses a claim because the office is already held (D-D-5): conflicting
  appointments are representable.
- **Judgement: functional (slot).** For each (office, context), at each valid time t, for a perspective:
  - one accepted holder gives that holder (ASSERTED);
  - two or more accepted holders whose intervals both cover t give **DISPUTED**, citing every holder and attestation;
  - an unaccepted claim is an alternative, never support;
  - a person not accepted as holder, when another is, is **INFERRED** not to hold it (exclusivity, v0.2 §5.6).
- **Probe results (P2, P6):**

  | Day | Answer |
  |---|---|
  | 5 | Bea, ASSERTED |
  | 9 (Bea [1, 10) and Cal from 8 both accepted) | DISPUTED, [Bea, Cal] |
  | 12 | Cal, ASSERTED |

  Dan on day 12 is INFERRED not to hold the office.
- **Judgement: polarity.** An accepted denial of an accepted appointment gives DISPUTED (probe P4: `holds` and
  `value_of` say DISPUTED). In the auditor's own perspective, the appointment is ASSERTED as not holding.
- **Scope of exclusivity.** It is per (office, context) and per valid time:
  - the same office in another unit is independent;
  - succession (non-overlapping intervals) is not a conflict;
  - contexts are matched exactly, with no containment (D-D-4).
- **Knowledge time and worlds.** As known before Cal's appointment was recorded, day 9 is Bea alone (P2). A
  reorganisation plan that stipulates Dan and denies Cal answers Dan, STIPULATED, while the actual world still answers
  Cal (P10).
- **Not dropped (DI-1).** Probe P4 shows that core `roles_of` returns nothing for Bea's polarity-disputed appointment
  (DI-1). The D-2 reports (`offices_of`, `office_holders`, `authorised`, `employment`) read the per-content judgement and
  list such cases as DISPUTED, as the D-1 reports do. `roles_of` itself is unchanged until DI-1 is resolved.

## 4. Authority vs capability vs office-holding vs action
| Concept | Representation | Means | Does not establish |
|---|---|---|---|
| office-holding | `office-holding(holder, office, context)` | occupies a position in a context | any authority or ability |
| capability (ability) | `classified-as(holder, capability, context?)` | is able to | authority, an office, or any act |
| authority | `authorisation(grantor, holder, power, scope)` | the grantor conferred the power on the holder within the scope | that the grantor was entitled to confer it; ability; an office; any act |
| action in office | `official-act(official, office, office-context)` | a source's account of an act in that capacity | that it occurred (occurrence status is separate), that the official held the office, or that they were authorised |

**Evidence** (P5 to P8):
- Bea holds the office (ASSERTED) while `capable(bea, can-sign-off)` is not established; capability and authority are
  separate content.
- Cal holds the office with authority NOT_YET_KNOWN; Dan has authority (ASSERTED) without the office.
- The authorisation granted by acme is **reported by hr**: the raw record keeps grantor = acme and source = hr apart.
- "Was acme authorised to grant?" is NOT_YET_KNOWN: nothing is inferred from the grant.
- Bea's sign-off account is accepted; the report gives the office and the authority at its time as separate answers,
  and it describes no occurrence.

**Powers are capability concepts.** The same concept (can-sign-off) can be held as an ability (`classified-as`) or
conferred as a power (`authorisation`); the relation, not the concept, says which. This adds no concept type.

## 5. Required changes to existing core semantics
**None.** D-2 needs only the profile (additive vocabulary) and functions in `worldmodel.organisation`. Interactions to
note:
1. **DI-1** (`facts_about` omits polarity-disputed content) makes core `roles_of` drop a disputed appointment. D-2 works
   around it in its own reports, and does not change `roles_of`. Resolving DI-1 (recommended option (a)) would fix
   `roles_of` too.
2. **DI-2** (single-valued event participants) applies to official acts: two accepted accounts of one act naming
   different officials are not judged DISPUTED at the occurrence level. D-2 reports per account.
3. **Shared judgement logic.** `authorised()` uses the same six-case judgement as `capable()`. The plan is to move
   that judgement into one internal helper used by both: a refactor with no change in behaviour, guarded by the
   existing capability tests.
4. **Test fixture rename.** The D0 fixture `organisation-fixture` defines `person`, `organisation` and
   `office-holding`, which collide with the real profile. Its labels will be renamed (test-only), as was done for the
   mechanical fixture in D-1.
5. **`capable()` accepts any concept.** `capable(bea, site-manager)` reports the office as "established", because it
   is a generic "classification held" check. D-2 documentation directs office questions to `offices_of` and
   `office_holders`. Unchanged.

## 6. Decisions requested
| # | Decision | Recommendation |
|---|---|---|
| D-D2-1 | The schema in section 1 (six types), and appointment/dismissal as core accounts plus effect claims (no appointment event type) | approve |
| D-D2-2 | Exclusivity only through `office-holding`'s slot (class, context); multi-holder roles use plain `classified-as` | approve |
| D-D2-3 | Powers are `capability` concepts; no `power` type | approve |
| D-D2-4 | `authorised()`: exact scope (D-D-4); grantor and reporting source as separate fields; grantor entitlement always "not assessed"; the same judgement cases as `capable` | approve |
| D-D2-5 | D-2 reports list disputed items (polarity or slot) as DISPUTED; core `roles_of` is unchanged pending DI-1 | approve |
| D-D2-6 | Employment: employer an organisation, employee a person (no organisation-to-organisation employment) | approve; widen later if a scenario needs it |
| D-D2-7 | Rename the D0 organisation fixture's labels (test-only) | approve |

## 7. Out of scope (as instructed)
- delegation chains;
- inferred authority (from offices, or from a grantor's authority);
- obligations and responsibilities as deontic content;
- context containment;
- new foundational kinds.
