# Core 0.4 Stage D-2: the organisational profile (LABS-1.026)

**Status (2026-11-11): implemented on `feature/core-0.4-d2-organisation` from `main` 153c2f2, at the review gate. Not
merged; D-3 not started.** Design: `stage-d2-design.md` (D-D2-1 to D-D2-7, approved with the LABS-1.026
qualifications). Next on the roadmap after D-2: **LABS-1.024**, the explorable schema export.

## 1. Schema (`schema/profiles/organisation/organisation-0.1.tql`; additive only)
| Type | Roles | Notes |
|---|---|---|
| `person sub physical-object` | | sortal |
| `organisation sub social-object` | | sortal; units are organisations `part-of` the parent (core) |
| `employment` | employer (organisation), employee (person) | |
| `office-holding sub classified-as` | classified (holder), class (office: a social-role), context | no functional slot |
| `exclusive-office` | office (social-role), context | the single-holder constraint, attested over its own valid time |
| `authorisation` | grantor, holder, power (capability), scope | the reporting source is the attestation's attester |
| `official-act sub event` | official (as actor), office, office-context | |

Seed vocabulary: `organisation:appointment` and `organisation:dismissal` (event kinds).

**Reused from the core, unchanged:** membership (`member-of`), structure (`part-of`), ordinary roles and abilities
(`classified-as`), agency, and appointment events (core accounts with effect claims).

**Change from the approved design (D-D2-2), required by the LABS-1.026 qualifications.** The design put exclusivity in
a functional slot on `office-holding`. That made every office exclusive, and the core's exclusivity rule infers that
anyone else does *not* hold the office (the design probe showed Dan INFERRED false). The qualifications require:
- a constraint declared per office, in a context, over a valid time;
- no inference about unmentioned people.

So exclusivity is the attested content `exclusive-office(office, context)`, checked by the profile's reports, and no
slot is declared. Core `holds()` on an unmentioned person therefore answers NOT_YET_KNOWN, not INFERRED false (tested).

## 2. API (`worldmodel.organisation`; functions taking the WorldModel)
| Function | Returns |
|---|---|
| `employ` / `employment(wm, world, x, t)` | each employment naming x, with its judgement (established, denied, expired, not yet effective, disputed, not established) and evidence |
| `appoint(wm, world, holder, office, context, polarity=True)` | an appointment claim (or an explicit denial); never refused |
| `declare_exclusive(wm, world, office, context)` | a single-holder constraint |
| `office_holders(wm, world, office, context, t)` | holders (established); every appointment with its own judgement and evidence; the constraint's judgement; the conflict (constraint support plus each appointment's accepted attestations) when it applies; overall status |
| `offices_of(wm, world, person, t)` | each appointment naming the person, with its judgement; DISPUTED with the conflict when an established appointment to an exclusive office is contested |
| `authorise(wm, world, grantor, holder, power, scope, attester=…)` | an authorisation claim; grantor and attester are separate arguments |
| `authorised(wm, world, holder, power, scope, t)` | holds / status / judgement (the capable() cases); grants, each with grantor, reported_by, judgement and evidence; only_in; grantor_entitlement "not assessed" |
| `act_in_office` / `official_act(wm, world, event, power=None)` | the account; occurrences with their own status; at the act's start, separately: the office (judgement, status, conflict), authority, capability and agency |

Shared judgement: `_holding_label` and `_combine` were extracted from `capable()` in increment 1 (82eb442). Equivalence
is shown by 1,242 `capable()` / `is_agent()` answers that are identical to the baseline recorded before the refactor
(`tests/test_l_capable_equivalence.py`).

## 3. Conflict semantics and evidence preservation
- **Appointments are stored as claims and never rejected.** The stored records (demo R2, and a test) show Cal's appointment
  content with both acme's claim and the auditor's denial, each with its own source, polarity and acceptance.
- **Each appointment keeps its own judgement.** For example, Bea "expired" and Cal "established" on day 12.
- **Exclusivity conflict.** Where the constraint holds at t and more than one appointment is established, the status is
  DISPUTED, citing the constraint's attestations and each appointment's accepted attestations. On day 9, the conflict
  cites `exclusive-office` and the attestations of both Bea and Cal.
- **No constraint, no conflict.** The safety office has two holders and is ASSERTED.
- **No inference about the unmentioned.** Eve is never mentioned for the site office: `office_holders` does not list
  her, `offices_of` has no such entry, and core `holds` answers NOT_YET_KNOWN.
- **Denial is distinct from absence.** In the auditor's perspective, Cal is "denied"; Eve is simply absent.
- **An appointment event alone establishes nothing.** Acme's appointment event for Fay, with an accepted `initiates`
  claim, leaves `offices_of(fay)` empty, and the state after it is unknown.
- **Disputes are visible.** A polarity-disputed appointment is listed as DISPUTED by `offices_of` and
  `office_holders`. Core `roles_of` still drops it (DI-1, unchanged as instructed; tested).
- **Perspectives, knowledge time and worlds:**
  - the auditor's view;
  - the view as known before Cal's appointment was recorded (Bea alone);
  - a reorganisation plan (Dan STIPULATED, Cal denied in the plan, Cal in the actual world).

## 4. Authority, capability, office and action: independent
- **Bea** holds the office and has authority, but no capability.
- **Dan** has authority (granted by acme, reported by hr) without capability.
- **Eve** has capability without authority.
- **Cal** holds the office (from day 8) without authority.
- **The safety officers** hold an office that confers no power.
- **Grantor vs source:** each grant reports `grantor: acme` and `reported_by: [hr]`. "Was acme authorised to grant?" is
  NOT_YET_KNOWN, and nothing is inferred.
- **Exact scope:** authority within depot-7 does not answer for acme (`only_in: [depot-7]`).
- **Acts in office:**
  - Bea's sign-off: account accepted, no occurrence claimed, office established, authority established, capability
    not established;
  - Cal's sign-off on day 9: its occurrence "not established", its office DISPUTED, and no authority.

## 5. Found while building
- The organisation world and the gearbox's Stage C extension both define `can-sign-off` (and `agent`). The benchmark,
  which builds them into one database, failed. The world now reuses existing ids, and a test builds the full gearbox
  chain with both profiles and then Acme.
- The D0 fixture's organisation labels (`person`, `organisation`, `office-holding`) were renamed (test-only), so the
  real profile and the fixtures coexist.

## 6. Limitations
1. DI-1 (`roles_of` and `facts_about` drop polarity-disputed content) and DI-2 (conflicting single-valued participants
   of an act) remain open, to be resolved before Stage E. The D-2 reports work around DI-1; DI-2 applies to official
   acts.
2. **DI-5 (new).** An accepted appointment that has not started yet is reported "not established" rather than "not
   yet effective" when an unreviewed counter-claim exists for the same content: the shared label ranks the
   attestation state first. Changing it would change `capable()`'s answers, which must stay equivalent. Tracked in
   `deferred-issues.md`.
3. Exclusivity is per exact (office, context); there is no containment between units (D-D-4).
4. When holders have mixed support statuses (ASSERTED and STIPULATED), `office_holders`' overall status is ASSERTED.
   The per-holder statuses are authoritative.
5. No delegation chains, no inferred authority, and no obligations (out of scope).

## 7. Validation
**Tests:**
- `tests/test_m_d2_organisation.py` (16 tests):
  - installation alone, with mechanical, with the fixtures, and in both orders;
  - no slot declared;
  - sequential holders;
  - a cited overlap conflict;
  - no conflict without the constraint;
  - appointments stored with their own evidence;
  - denial vs absence, and no inference about the unmentioned;
  - an unfilled office is NOT_YET_KNOWN;
  - an appointment event alone establishes nothing;
  - perspectives, knowledge time and a plan world;
  - a polarity dispute listed, while `roles_of` is unchanged;
  - the four concepts independent;
  - grantor vs source, entitlement not assessed, exact scope;
  - acts in office;
  - employment and membership;
  - all worlds composed in one database;
  - selective/full-load agreement.
- `tests/test_l_capable_equivalence.py`: 1,242 `capable()` answers identical to the pre-refactor baseline.

| Run | Increment 1 (82eb442, refactor) | Increment 2 (6a7bc56, profile) |
|---|---|---|
| full suite, selective | 325 passed | 341 passed, 341 passed |
| full suite, full load | 325 passed | 341 passed, 341 passed |
| core-protection (`WM_PROFILES=1`: mechanical, organisation, three fixtures), each path | — | 341 passed, 341 passed |
| leftover test databases | 0 | 0 |

Every run used a clean checkout of the exact commit.

**Demonstration:** `scripts/show_organisation.py`, output in `docs/core-0.4/organisation-output.md` (judged answers
and raw TypeQL).

**Performance:** `docs/core-0.4/bench-d2/README.md`:
- query counts are identical for every existing question;
- latencies are within noise (rounds in both orders);
- the new reports cost 14–115 queries;
- storage grows 11% for the profile and the Acme world.
