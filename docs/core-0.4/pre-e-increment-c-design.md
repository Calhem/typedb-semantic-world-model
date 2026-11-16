# Pre-Stage E correction, increment C: one aggregation rule (DI-6), design

**Status: design for architectural review (LABS-1.039), not implemented.** Branch `feature/pre-e-c-aggregate-status`,
from `main` at `d9d873a` (increment B merged). No aggregation code has changed. Increment D (DI-2) and Stage E have
not begun. The foundational ontology and the schema are unchanged, and nothing here changes them.

Approved direction: R-5 and choice E ([pre-stage-e-correctness-review.md](pre-stage-e-correctness-review.md), sections
5 and 6), and LABS-1.039:
- **one proposition or question supported by several holdings:** combine support with the core rule, independent of
  iteration order;
- **several distinct propositions or items:** keep each one's status; invent no single support status for the
  collection;
- **conflicting evidence:** keep the dispute and the uncertainty; support precedence never hides them.

Executable examples: `probes/pre_e_c_examples.py`, output `probes/pre_e_c_examples.out.txt` (section 5).

## 1. The defect (DI-6)
The core judges each content once (increment B's canonical record): its judgement, and a **support status** from the
core rule, `answer_status`: STIPULATED if any deciding claim is a stipulation, else ASSERTED if any is testimony or
observation, else INFERRED. Every claim stays listed as evidence.

Some reports then put several contents together, and three different rules are in use:

| Rule | Where | What it does | Defect |
|---|---|---|---|
| `answer_status` | `holds`, `value_of`, `exists`, `compare_measurements`, `where` | the core rule over the union of the deciding support | none: the reference |
| `_combine` (agency) | `capable`, `authorised`, `calibration_status` | the status of **whichever holding comes first** in the list (sorted by context, grantor or certificate name) | depends on order: mirror cases disagree; an INFERRED holding can outrank an ASSERTED one |
| `_overall` (organisation) | `office_holders` | one status if every established holder agrees, **else ASSERTED** | invents a support status for a set of different people |

A fourth fold was found while preparing this design (section 3.3, example E10): in `changes`, the state of a
single-value slot (such as a location) takes its status from the support of the values held **and of the values
denied**. `value_of` uses only the values held. The two readers then disagree about the same state.

## 2. Terms
- **Holding:** one content that bears on a report's question, with its own canonical record (judgement, status,
  support, evidence). For `capable(dan, analyst, depot)`, the general holding `classified-as(dan, analyst)` and the
  contextual one `classified-as(dan, analyst, depot)` are two holdings.
- **Deciding support** of a holding: the accepted claims that decide its judgement (`record.support`). For an
  established holding these are the accepted assertions in force; for a denied one, the accepted denials; for an
  expired one, the accepted assertion that has ended.
- **One question:** a report whose answer is a single holds / does-not-hold for one subject, however many holdings
  bear on it: `capable`, `is_agent`, `authorised`, `calibration_status`. Also a single-value slot's value at t.
- **Collection:** a report that lists distinct items, each a proposition of its own: the holders of an office, the
  employments of a person, the links of a provenance chain, the facts about a subject.

## 3. Proposed semantics
### 3.1 One question answered by several holdings (rule Q)
The reader chooses the applicable holdings exactly as now (`capable`: the general holding and the one in the asked
context; `authorised`: the grants for exactly that power and scope; `calibration_status`: every certificate naming
the instrument). Then, in this order:
1. **Conflict first (unchanged).** DISPUTED if any applicable holding is itself DISPUTED (by polarity or by a
   constraint), or if one is established while another is denied by an accepted denial. Precedence is never applied
   across a conflict. Every holding stays listed with its own judgement and evidence.
2. **Holds (true).** If any applicable holding is established: `holds` True, judgement "established", and the status
   is the core rule over the **union of the deciding support of every established holding**. A union of sets and a
   rule over bases do not depend on order, so the mirror cases agree by construction.
3. **Does not hold.** Otherwise, if any is denied or expired: `holds` False, judgement "denied" if any is denied, else
   "expired", and the status is the core rule over the union of the deciding support of the denied and expired
   holdings (both decide "not at t").
4. **Undecided (unchanged).** Otherwise `holds` None, status UNKNOWN if anything was found, NOT_YET_KNOWN if nothing
   was; judgement "not yet effective" if an applicable holding is, else "not established".

**Uncertainty stays visible.** An established answer beside other holdings that are undecided (unreviewed, pending,
not yet effective, rejected) is still established: an undecided holding does not contradict it. Those holdings stay
in `applicable` (or `grants`, `certificates`) with their own judgement, reasons and pending claims. They are never
merged into the status. An expired holding beside an established one is not a conflict either (it has ended).

**New field (fields only added):** `support`, the sorted ids of the deciding claims the status rests on, so that a
reader can check the status against the evidence without recomputing it.

**Placement.** One core function over canonical records (in `judgement.py`), used by `capable` and by the profiles.
It replaces `_combine`, which reads labels and copies one holding's status. The per-content helper `_judgement` is
unchanged. No new queries: the deciding support is already in each record.

### 3.2 A report over distinct items (rule C)
`office_holders.status` (choice E):
- DISPUTED if an established exclusive-office constraint puts established appointments in conflict, or if any
  appointment is itself disputed (unchanged);
- **None** when holders are established without conflict: there is no single support status for several people.
  Each appointment keeps its own status in `appointments`;
- UNKNOWN when appointments exist but none is established; NOT_YET_KNOWN when none exists (unchanged).

`holders`, `exclusive`, `conflict` and `appointments` are unchanged. `offices_of`, `employment` and the other
collections already keep per-item statuses and fold nothing (section 4). The rule is a small core helper; the
organisation profile's `_overall` is retired.

### 3.3 A single-value slot in `changes` (rule Q for a slot's value)
A slot track's state takes its status from the core rule over the support of the **values held (or disputed) at
the sample time**, exactly as `value_of` does. An accepted denial of another value is not support for the value held:
it stays visible through the content tracks and the evidence, as now. DISPUTED, UNKNOWN and the transition categories
are unchanged; only the status can change, and only where a denial of another value in the same slot is accepted at
the same time.

## 4. Inventory: every report that combines several judgements
Each public reader was read for where its answer's status or judgement comes from. "Inherits" means it calls one of
the readers above and adds no fold of its own.

| Reader | Module | Kind | Current rule | Proposed | Changes? |
|---|---|---|---|---|---|
| `capable` | core (agency) | one question | `_combine`: first holding's status | rule Q | status in mixed-support cases; `support` added |
| `is_agent` | core (agency) | one question | `capable` | rule Q (inherits) | as `capable` |
| `check_action` | core (agency) | separate fields | `is_agent`, `capable` per actor | inherits | as `capable` |
| `agency_report` | core (agency) | per attester | `is_agent` status | inherits | as `capable` |
| `authorised` | organisation | one question | `_combine` | rule Q | status in mixed-support cases; `support` added |
| `office_holders` | organisation | collection | `_overall`: one status if all agree, else ASSERTED | rule C | `status` None when holders are established without conflict |
| `offices_of` | organisation | collection | each appointment's own judgement; DISPUTED under an exclusive conflict | unchanged | no |
| `employment` | organisation | collection | each employment content's own judgement | unchanged | no |
| `official_act` | organisation | separate fields | `offices_of`, `authorised`, `capable`, `is_agent` | inherits | as `authorised` and `capable` |
| `calibration_status` | laboratory | one question | `_combine` | rule Q | status in mixed-support cases; `support` added |
| `measurement_calibration` | laboratory | per measurement | `calibration_status` | inherits | as `calibration_status` |
| `provenance` | laboratory | collection | each link's own judgement; a path is established only if every step is (a conjunction, not a support status) | unchanged | no |
| `interpretations` | laboratory | collection | each attestation, and its content's own judgement | unchanged | no |
| `changes` | core (dynamics) | per track | slot track: core rule over held **and denied** values | rule Q over held values (3.3) | status where a denial of another value is accepted |
| `holds`, `judgement`, `explain` | core | one content | the canonical record | reference | no |
| `value_of` | core | one question (slot) | core rule over the values held | reference | no |
| `exists`, `occurrence_status` | core | one question | existence content; else INFERRED from participation (union) | already rule Q | no |
| `compare_measurements` | core (qualities) | one question | DISPUTED on an incompatible pair, else core rule over the union | already rule Q | no |
| `where` | core (spatial) | one question | DISPUTED on a verified conflict; UNKNOWN if unverified; else most direct status among direct candidates (= core rule over their union); INFERRED when only derived | already rule Q | no |
| `transform_between` | core (spatial) | derived answer | INFERRED by rule over a chain; DISPUTED if a link is disputed | unchanged (a derivation, not a fold) | no |
| `facts_about`, `roles_of`, `poses`, `frame_info`, `process_steps`, `composition`, `contents`, `materials`, `parts`, `dependencies`, `connections`, `measurements`, `effects_of`, `causes_of`, `history` | core and mechanical | collections | each content's own record | unchanged | no |

## 5. Examples (executed)
From `probes/pre_e_c_examples.py` (a throwaway database). The actual world holds HR's and the laboratory's claims
(ASSERTED, or INFERRED where written with basis inference), accepted by the system perspective; the **audit**
perspective has accepted none of them. The plan (a hypothetical world branching on day 2) inherits them and adds its
own stipulations, which are constitutive of the plan and so accepted for every perspective. All answers at day 5.

| # | Case | Perspective | Holdings (own status) | Current | Proposed |
|---|---|---|---|---|---|
| E1 | `capable(dan, analyst, depot)`, plan | system | general ASSERTED (inherited); depot STIPULATED (plan) | established, **ASSERTED** | established, STIPULATED |
| E1 | `capable(cal, analyst, depot)`, the mirror | system | general STIPULATED (plan); depot ASSERTED (inherited) | established, **STIPULATED** | established, STIPULATED |
| E1 | both of the above | audit | the inherited holding unreviewed; the plan's STIPULATED | established, STIPULATED | established, STIPULATED |
| E2 | `capable(dan, analyst, depot)`, actual world | system | general ASSERTED | established, ASSERTED | unchanged |
| E3 | `capable(eve, analyst, depot)`, plan | system | general INFERRED; depot ASSERTED (both inherited) | established, **INFERRED** | established, ASSERTED |
| E3 | the same | audit | both unreviewed | not established, UNKNOWN | unchanged |
| E4 | `capable(fay, analyst, depot)`, plan | system | general expired (ASSERTED); depot denied (STIPULATED) | denied, **ASSERTED** | denied, STIPULATED |
| E5 | `capable(gus, analyst, depot)`, plan | system | general established (ASSERTED); depot denied (STIPULATED) | DISPUTED | DISPUTED (precedence never hides the conflict) |
| E5 | the same | audit | general unreviewed; depot denied (STIPULATED) | denied, STIPULATED | unchanged |
| E6 | `authorised(bea, can-sign, depot)`, plan | system | acme's grant ASSERTED (inherited); the board's STIPULATED | established, **ASSERTED** | established, STIPULATED |
| E6 | the same | audit | acme's unreviewed; the board's STIPULATED | established, STIPULATED | unchanged |
| E7 | `calibration_status(balance)`, plan | system | cert-1 STIPULATED; cert-2 INFERRED; cert-3 ASSERTED | established, STIPULATED (cert-1 sorts first) | established, STIPULATED (by the rule, not by order) |
| E7b | the same in a second plan, the stipulated certificate named cert-4 | system | cert-2 INFERRED; cert-3 ASSERTED; cert-4 STIPULATED | established, **INFERRED** (cert-2 sorts first) | established, STIPULATED |
| E8 | `office_holders(office-x, depot)`, plan | system | bea ASSERTED (inherited); cal STIPULATED | holders bea and cal, **ASSERTED** | holders bea and cal, **None**; each keeps its status |
| E8 | the same | audit | bea unreviewed; cal STIPULATED | holder cal, STIPULATED | holder cal, **None** |
| E8 | the same, actual world | system | bea ASSERTED | holder bea, ASSERTED | holder bea, **None** |
| E9 | `employment(acme)`, plan | system | bea ASSERTED; cal STIPULATED | two rows, each its own status | unchanged (no aggregate) |
| E10 | `located-at(box)`, actual world | system | room-1 then room-3 INFERRED; room-2 denied, ASSERTED | `value_of` INFERRED; `changes` **ASSERTED** | both INFERRED |

E7 and E7b show why "currently right" is not enough: with the same three bases, the current answer is STIPULATED
only because the stipulated certificate's name sorts first; named `cert-4`, it sorts last and the answer becomes
INFERRED (cert-2's status). E8 in the actual world shows that rule C also changes single-holder
answers: a one-holder office reports the status on its appointment, not on the office.

## 6. Impact on the reference worlds
Estimated with `probes/pre_e_c_impact.py` (output `probes/pre_e_c_impact.out.txt`), before any code changes:

1. From the frozen reader snapshot after increment B (`probes/pre_e_b_snapshot.after.json.gz`, every perspective and
   knowledge time it holds), the status each rule would give, computed from each answer's own holdings:

   | Report | Answers | Would change | How |
   |---|---|---|---|
   | `capable` | 17,605 | 0 | |
   | `authorised` | 20 | 0 | |
   | `calibration_status` | 3,575 | 0 | |
   | `office_holders` | 20 | 14 | 13 ASSERTED → None, 1 STIPULATED → None (7 in `org`, 7 in `org-plan-reorg`); each holder keeps its own status |

   The reference worlds never give one question established holdings with different statuses, so rule Q changes
   none of their answers: the defect is real (section 5) but not yet exercised by the reference data. The 14
   `office_holders` answers are choice E, already approved in LABS-1.036. The 6 that do not change are DISPUTED or
   have no holder.
2. From the reference database rebuilt from merged `main`: accepted denials of a single-value slot value that share
   a key with an attested value, the only situation in which rule Q for a slot (C-6) can change a `changes` status.
   There are none in any of the 11 worlds (the reference worlds hold two accepted denials in all, neither on a
   single-value slot), so C-6 changes no reference answer; E10 is the only case that shows it.

Readers that inherit (`is_agent`, `check_action`, `agency_report`, `official_act`, `measurement_calibration`)
change only where these do, so not at all in the reference worlds. The exact inventory is made after implementation,
as for increment B: re-read the snapshot with the new code and compare (`pre_e_b_diff.py`); every changed answer
must be one of these 14, plus any the implementation's tests add.

## 7. Tests (to be written with the implementation)
- rule Q is independent of order: the E1 mirror cases agree; permuting the holdings (renamed contexts, grantors,
  certificates) never changes the status;
- the status equals `answer_status` over the union of the established holdings' support, and `support` lists exactly
  those claims, for `capable`, `authorised` and `calibration_status`;
- E3 (an INFERRED holding never outranks an ASSERTED one), E4 (denied and expired combine), E5 (a conflict stays
  DISPUTED), each across the actual world, a plan and the two perspectives, and at an earlier knowledge time;
- an established answer with undecided holdings beside it: the status ignores them, and they stay listed with their
  own judgement and pending claims;
- `office_holders`: None for established holders without conflict (one holder or several, mixed or equal statuses);
  DISPUTED, UNKNOWN and NOT_YET_KNOWN unchanged; `offices_of` and `official_act` unchanged;
- `changes`: the E10 slot state agrees with `value_of` at every boundary; tracks and categories unchanged;
- the readers that inherit (`is_agent`, `check_action`, `agency_report`, `official_act`, `measurement_calibration`)
  agree with the reader they call.

**Answer changes** will be inventoried as for increment B: the frozen 106,752-answer reference snapshot is
re-read with the new code and every changed answer is accounted for against this design.

## 8. Not changed
Per-content judgement (increment B). `holds`, `value_of` and every collection's per-item statuses. The merged
occurrence view and event-role cardinality (DI-2, increment D). Same-as in traversals (DI-12, deferred). The
foundational ontology and the schema.

## 9. Decisions for approval
| # | Decision | Recommended |
|---|---|---|
| C-1 | Rule Q for `capable`, `authorised` and `calibration_status` (and the readers that inherit): conflict first; then the core rule over the union of the established holdings' deciding support | approve |
| C-2 | When the answer is "does not hold": the core rule over the union of the denied and expired holdings' support | approve |
| C-3 | Undecided holdings beside an established one: the answer stays established; they stay listed with their own judgement, never folded into the status | approve |
| C-4 | Add `support` (the deciding claims) to the three one-question reports; fields only added | approve |
| C-5 | Rule C for `office_holders`: `status` None when holders are established without conflict (choice E), including a single holder | approve |
| C-6 | Include the `changes` slot status (E10, found in this design): the core rule over the values held, as `value_of` | approve |
