# Core 0.4 Stage D: domain generalisation review (LABS-1.021)

**Status (2026-11-11): reviewed; decisions D-D-1 to D-D-11 approved under LABS-1.022 with the qualifications in
section 8a.** Review branch `feature/core-0.4-d-review` (b9fa45a) from `main` at 18003bc. Groundwork (D-0) on
`feature/core-0.4-d0-groundwork`; domain implementations (D-1 to D-3) not yet authorised.

The evidence in this review comes from three sources:
- the exploratory profile drafts (`docs/core-0.4/stage-d/drafts/*.tql`);
- the probe `probes/core04_d_review.py` (output `probes/core04_d_review.out.json`), which loads the drafts into a
  throwaway database on top of the full Core 0.4 schema and exercises them through the existing API;
- the cross-domain TypeQL in section 6, run unchanged against both reference worlds (`wm-reference-gearbox-c` and
  `wm-reference-lab`).

**Question.** Can Core 0.4 represent substantially different domains with its existing foundational concepts?
**Short answer: yes. No foundational ontology change is needed for mechanical systems, organisations or scientific
investigation.**
- Most of what remains is **domain vocabulary**: profile sortals, proposition and event subtypes, and concepts.
- There are **five general-purpose API extensions**. Each is small and none changes semantics.
- One is a **core conformance addition** that frozen v0.2 already specifies: the kind of a dependency.
- The review also found **one existing defect**: `roles_of()` drops profile subtypes, and two other code paths have
  the same pattern.
- It recorded **one TypeDB constraint** that shapes profile design.

---

## 1. What the existing ontology already provides
| Foundation (v0.2 / Core 0.4) | Supports, in any domain |
|---|---|
| Four kinds (physical-object, social-object, place, information-object), `occurrence`; profile sortals through the type lattice (A0.2) | entity identity fixed at minting; profile subtypes behave as their core type in every query (probe D0) |
| `classified-as(classified, class, context?)` with concepts (`category`, `social-role`, `quality-kind`, `capability`) | kinds-as-described, materials, roles in context, capabilities, agency, part types, seat positions, all changing over time |
| `part-of`, `member-of`, `constitution`, `depends-on` | assemblies, organisational structure, membership, samples taken from specimens, dependencies |
| `located-at`, `positioned-in`, frames and transforms | symbolic and metric location, frames attached to things |
| Event descriptions with six participant roles, profile event subtypes with specialised roles, `describes`, `initiates`/`terminates`, `causes` | maintenance, appointments, sampling, measurement activities; several accounts of one occurrence; state transitions; asserted causation |
| Stage C: units and dimensions, result records, `rests-on`, `produced`, `reports`, comparability | measurements with provenance in every domain; specifications kept apart from measurements |
| Attestation, acceptance, worlds and knowledge time | conflicting accounts, perspectives, corrections and supersession, hypothetical reorganisations or redesigns, history as known at any time |
| Functional slots as data (A0.3), with subtypes inheriting or overriding a slot | "one value at a time" rules declared by a profile, not hard-coded |
| `install_module(name, files=…)` | loading a profile's schema after the core (probe D0: all four drafts together, no collision) |

## 2. Coverage matrix
Classification codes:
- **S**: supported by the existing ontology and API.
- **V**: supported by the ontology, but needs domain vocabulary (profile sortals, subtypes, relations or concepts).
- **X**: supported by the ontology, but needs a general-purpose API extension.
- **F**: needs a foundational ontology change.
- **Df**: intentionally deferred.

"Probe" names the evidence in `probes/core04_d_review.out.json`.

### D1 Mechanical systems (reusing the gearbox world)
| Requirement | Class | How, and evidence |
|---|---|---|
| Assemblies and components | S | `part-of`, `parts()`, `composition()` (A1). Part kinds such as bearing and gear are categories (V vocabulary only). "Component" is a role in an assembly, not a kind |
| A part's position in an assembly (input-bearing seat) | V | `classified-as(bearing-3, input-bearing-seat, context: shaft-asm-in)`: the same contextual-role mechanism as organisational roles |
| Mechanical connections and joints | V | `connected-to(endpoint ×2, joint-kind)` (draft `mechanical-0.1`) |
| Material constitution | S | `constitution`, `materials()`; materials as categories (A1) |
| Location and reference frames | S | `located-at`, `positioned-in`, `where()`, `transform_between()` (A1, A2) |
| Maintenance and state transitions | S | accounts, `claim_effect`, `changes()`, `explain()`, occurrence status (B) |
| Replacement with removed and fitted parts told apart | V | draft `replacement sub event, relates removed as patient, relates fitted` (probe D1c). Today both are a generic `patient`, so two accounts that name different patients look like a disagreement |
| Qualities and measurements; specification vs measured value | S | Stage C, unchanged API (housing weighed on two scales; the design value is a statement) |
| Functional dependencies | **X** (core conformance) | v0.2 §3.4 gives `depends-on` a dependency-kind concept; Core does not have it. Adding `relates kind` is additive: existing keys are unchanged (probe D1b). `dependencies()` must take a kind filter. Today it mixes kinds: `dependencies(pump)` = [manual, motor] |
| "What stops working if the motor fails?" | Df (inference); listing is X | listing the asserted functional dependents is a query (the inverse closure). Concluding failure states is inference and needs an explicit rule and evidence model, so it is not in Stage D |
| A capability held in a context, used in a sub-context (technician can replace bearings in the workshop; asked about bay-1, which is part of the workshop) | **X** (decision D-D-4) | contexts are matched exactly: "established" in the workshop, "not established" in bay-1 (probe D1a). Containment would be a named query-time rule |
| Part types vs part instances (bearing type 6204) | V | type = category; design data = information object or design-office statements (Stage C statements) |

### D2 Organisations
| Requirement | Class | How, and evidence |
|---|---|---|
| People and organisations | V | sortals `person sub physical-object`, `organisation sub social-object` (draft; lattice maps them, probe D0). An organisation can be an agent (probe D2d: "established") |
| Membership | S | `member-of(member, group)` |
| Organisational structure (department within company) | S | `part-of` between social objects |
| Employment | V | `employment(employer, employee)` (v0.2 §3.4's own example; draft) |
| Contextual appointments | S, with one defect | `classified-as(person, role, context)`. **Defect:** `roles_of()` compares the exact label `classified-as`, so a profile subtype (`office-holding`) is dropped. `roles_of(bea)` lists only `analyst` (probe D2a). `capable()` uses the lattice and sees it |
| Single-holder offices (one site manager per depot) | V | `office-holding sub classified-as` with a slot (class, context) → classified, declared as data. Two accepted holders give DISPUTED; ordinary roles stay non-exclusive (probe D2a). A slot on `classified-as` itself would wrongly make every classification exclusive |
| Changes of role over time | S | intervals, appointment events with `initiates`/`terminates`, `changes()` (probe D2d: employment, office and authorisation transitions) |
| Conflicting accounts of organisational relationships | S | polarity, perspectives, acceptance. Acme grants, the auditor denies: the system says ASSERTED/holds; the auditor's own view says ASSERTED/does not hold; once the system accepts both, DISPUTED (probe D2b) |
| Capabilities (ability) | S | `capable()` (C2) |
| **Authority to act, distinct from occupying a role** | **V + X** (decision D-D-3) | see section 3, G1. Holding the office was ASSERTED while authorisation was NOT_YET_KNOWN (probe D2b). Draft `authorisation(grantor, holder, power, scope)`; a reporting query `authorised()` is needed |
| Acting in the capacity of an office (signing as site manager) | V (+ X to check) | draft `decision sub event, relates decider as actor, relates capacity` with a `social-role` as the capacity player: accepted, and found through the lattice (probe D2c). `check_action` would need to report whether the actor held that office and authority at the time |
| Responsibilities | V; Df for reasoning | `responsible-for(holder, matter, scope)` as profile content. Whether an obligation was met or breached is deontic reasoning, deferred |
| Delegation chains (authority to grant authority) | Df | needs rules over authorisations |
| Where an organisation is | V | social objects cannot be `located-at` (by design: "its premises are not it", v0.2 §3.1); a profile relation `seated-at(organisation, place)` |

### D3 Scientific investigation (reusing the laboratory world)
| Requirement | Class | How, and evidence |
|---|---|---|
| Samples and specimens | V + S | sortal `sample`; `constitution(sample, specimen)` (S); `sampling` event subtype with specialised roles (probe D3a) |
| Experiments | S | an `occurrence` classified `experiment`; its measurements and steps `part-of` it (`process_steps`). The protocol is an information object (V) |
| Measurement activities | S | Stage C `measure()`, atomic |
| Instruments | S | the `instrument` event role and categories; no instrument kind is needed |
| Calibration | V (+ X to report) | today a text `calibration-ref` on the record (D-C-1). Draft `calibration-of(certificate, calibrated)` is attested content resting on the certificate through `rests-on` (probe D3b: holds 5 Nov, does not hold 9 Nov). Reporting "was the instrument's calibration in force when it measured?" is a small query. Invalidating results automatically is not proposed |
| Experimental conditions | S on records (exact text, D-C-7); Df for structure | linking a record's conditions to attested states of the set-up (chamber temperature) is deferred |
| Observations and results | S | results are records; a qualitative observation can back any attestation through `attest(evidence=…)`. v0.2's `observation` type stays deferred (U-1) |
| Conflicting measurements | S | `compare_measurements` (C1) |
| Corrections, provenance and uncertainty | S | supersession per perspective, `rests-on`, u/k on records, coverage on content (C1, D-C-2, D-C-8) |
| Same physical quality across measurements (quality instances) | Df (decision D-D-8) | a v0.2 extension point. No scenario here needs it, since the slot (bearer, quality kind) suffices |
| Which conditions or calibration states matter for comparability (profile-specific) | Df | v0.2 §3.3 lets a profile say so; D-C-7 approved exact text for now |
| Reconciliation of measurements | Df | only through named policies (v0.2) |

## 3. Material gaps, with concrete examples
| # | Gap | Class | Concrete example (probe) | Smallest remedy |
|---|---|---|---|---|
| G1 | **Occupying a role is not having authority**, and `capability` currently stands for both ability and authority | V + X | Bea holds the site-manager office at depot-7 (ASSERTED), but nothing says she may sign off. `capable(bea, can-sign-off, depot-7)` is "not established" before and after acme's authorisation, because authority is a different content (D2b) | profile relation `authorisation(grantor, holder, power, scope)`: who conferred which power, on whom, within what. The grantor is the conferring party, not the attester (a clerk may record acme's grant). New query `authorised(world, holder, power, scope, t)`, reported like `capable()` (judgement, evidence). `capable()` keeps meaning ability |
| G2 | **Context containment** | X | can-replace-bearing in workshop is established; in bay-1, part of the workshop, it is not (D1a) | keep exact matching by default. Optionally a named query-time rule (`context-within/v1`) whose answers are INFERRED and cite the `part-of` premises (decision D-D-4) |
| G3 | **Dependency kind** missing from `depends-on` | X (core conformance) | `dependencies(pump)` = [manual, motor]: an informational and a functional dependency, mixed (D1b) | `relation depends-on, relates kind; category plays depends-on:kind;` (additive; kind-less keys unchanged). `dependencies(..., kind=None)` filter |
| G4 | **Exact-label checks** drop profile subtypes | X (defect) | `roles_of(bea)` omits her `office-holding` (D2a). The same pattern is in `account_attestations` (dynamics.py:117) and `process_steps` (dynamics.py:545) | use the lattice (`is_a`), as A0.2 requires everywhere. A bug fix with tests |
| G5 | **Two specialisations of one core role in one event** are rejected by TypeDB 3.14.1 | V (design rule) | `relates out-part as patient, relates in-part as patient` with both played fails at commit: `@card(0..1)` on `event:patient` (D1c-alt) | a profile specialises a core role at most once per event type. Further participants are the profile's own roles (`fitted`), which events and the lattice still handle (D1c) |
| G6 | **Calibration in force at measurement time** | V + X | the certificate covers 1–8 Nov; a result on 9 Nov carries only the text reference (D3b) | `calibration-of` as attested content resting on the certificate; `measurements()` reports the calibration status at the activity's time. Report only, no invalidation |
| G7 | **Acting in an office's capacity** is not checked | V + X | a sign-off described with `capacity: site-manager` is stored and found (D2c), but nothing reports whether Bea held the office and the authority then | `check_action(..., office=, power=)` reports both, separately, concluding nothing (as for capabilities) |

## 4. Foundational gaps
**None required.** Candidates considered and rejected as foundational changes:
- **Authority or deontic modality as a new foundational category.** Authority is a social fact: someone confers a
  power within a scope, and others may dispute it. That is attested, n-ary content, which v0.2 §3.4 places in profiles
  ("social and operational relations are profile proposition types"). Reasoning about obligations (met or breached) is
  deferred, not foundational.
- **Context hierarchy.** Containment between contexts is already `part-of`. Using it for applicability is a query-time
  rule (v0.2 §5.6 allows INFERRED from a declared rule), not a new concept.
- **Quality instances.** v0.2 already provides the extension point. It is deferred because no scenario requires it.
- **Observation type (U-1).** Remains deferred: result records with `rests-on` cover Stage D's needs.
- **Raising the core `event:patient` cardinality** (G5) would be a core schema change. A profile design rule avoids
  it.

**Core conformance (not a change of ontology):** the `depends-on` kind (G3) is in frozen v0.2 and missing from the
implementation.

## 5. Proposed minimal domain vocabulary
The schema drafts are in `docs/core-0.4/stage-d/drafts/`. All load together after the core (probe D0) and add only:
- sortals;
- proposition subtypes and relations;
- event subtypes with roles;
- player declarations.

They add no new foundational kinds.

| Profile | Schema (draft) | Concepts (data, seeded by the profile) | Slot metadata |
|---|---|---|---|
| **mechanical-0.1** | `connected-to(endpoint ×2, joint-kind)`; `replacement sub event` (`removed as patient`, `fitted`) | part kinds (gearbox, bearing, gear, shaft), materials, joint kinds (bolted, pressed, welded), seat roles (input-bearing-seat), categories `system`, `maintenance`, `inspection`; dependency kinds `functional`, `informational`, `existential` | none new (existing `located-at`, `positioned-in`, frame slots) |
| **organisation-0.1** | `person`, `organisation`; `employment(employer, employee)`; `office-holding sub classified-as`; `authorisation(grantor, holder, power, scope)`; `decision sub event` (`decider as actor`, `capacity`) | offices (site-manager, deputy), powers (can-sign-off, can-approve-spend), event kinds (appointment, dismissal, meeting) | `office-holding`: (class, context) → classified |
| **laboratory-0.1** | `sample`; `sampling sub event` (`sampler as actor`, `sampled as origin`, `product as destination`); `calibration-of(certificate, calibrated)` | categories experiment, measurement, sampling, calibration; quality kinds and units in use | none new |

Kept deliberately small: no employment contract terms, no bill of materials, no laboratory information management
schema. **Deviation from plan §1 (Stage D table):**
- `component` and `instrument` are proposed as categories or roles, not sortals. Being a component, or being used as
  an instrument, is a role something plays, and v0.2 §3.1 reserves kinds for identity criteria.
- `vehicle` (a genuine sortal) is not needed by the gearbox world.

## 6. Cross-domain questions
| Question | Genuinely general? | Existing API | Domain-specific interpretation |
|---|---|---|---|
| What is this entity? | yes | kind via the lattice; `facts_about` → `classified-as` | which categories matter (material, part kind, office, sample type) |
| What is it part of? | yes (mechanism) | `part-of` (query below); `parts()` for the other direction | whether membership counts: a person is a **member** of a team (`member-of`), a department is **part** of a company (`part-of`). Answers must keep them apart |
| Where is it, or what context does it occupy? | partly | physical: `located-at`, `where()`; contexts: the context of its classifications | social objects have no location; "context" means a place, an organisation, an assembly or an occurrence depending on the profile |
| What changed during a period? | yes | `changes()` | none |
| What evidence supports a claim? | yes | `holds`/`value_of` support, attestations (attester, basis, acceptance), `evidence_of` (`rests-on`) | none |
| Which measurements or qualities are associated with it? | yes | `measurements()`, `compare_measurements()`, `facts_about` → `has-quality` | which conditions matter for comparability (deferred, D-C-7) |
| What capabilities or responsibilities does it have? | ability: yes. Authority and responsibility: no | `capable()`, `roles_of()` (after the G4 fix) | authority (G1) and responsibility are profile content; whether an office confers a power is a domain rule |
| What is disputed or unknown? | yes (statuses) | every judged answer: DISPUTED / UNKNOWN / NOT_YET_KNOWN | what counts as a conflict depends on the slot metadata a profile declares |

**Raw TypeQL, verified unchanged on both reference worlds** (parameter `$id`; results in the probe notes below):
```
# What is it classified as, by whom, in which context? (technician: agent, fitter in workshop...; ana: agent, analyst in lab-1...)
match $x isa particular, has wm-id == $id; $c isa classified-as (classified: $x, class: $k);
  $k has wm-id $kid; $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "class": $kid, "by": $by,
        "context": [ match $c links (context: $ctx); $ctx has wm-id $cid; fetch { "id": $cid }; ] };

# What is it part of, according to whom, from when? (bearing-3: shaft-asm-in from 11-05 14:00; sample-12: none)
match $x isa particular, has wm-id == $id; $c isa part-of (part: $x, whole: $w); $w has wm-id $wid;
  $a isa attestation (content: $c, attester: $who); $who has wm-id $by;
fetch { "whole": $wid, "by": $by, "from": $a.valid-from-earliest, "until": $a.valid-to-earliest };

# What evidence backs its quality claims? attestation -> record -> activity (housing: 2; sample-12: 6)
match $x isa particular, has wm-id == $id; $p isa has-quality (bearer: $x);
  $a isa attestation (content: $p); rests-on (attestation: $a, record: $r); $r has wm-id $rid;
  produced (activity: $e, result: $r); $e has wm-id $eid;
fetch { "attestation": $a.wm-id, "record": $rid, "activity": $eid, "conditions": [ $r.condition ] };

# Which event descriptions name it, in which role (profile roles included)? (technician: 4; ana: 3)
match $x isa particular, has wm-id == $id; $e isa event, links ($role: $x), has wm-id $eid;
  $a isa attestation (content: $e, attester: $who); $who has wm-id $by;
fetch { "event": $eid, "role": $role, "by": $by };
```
These return stored records, unjudged. The judged answer to each question is the API call in the table, which applies
acceptance, perspective, knowledge time and worlds. Two profile-level queries (drafts; run in the probe, results
under "raw TypeQL" in its output):
```
# Who has authority to sign off at depot-7, conferred by whom? (G1)
# -> bea, granted by acme (attested by acme, polarity true) and the same grant denied by the auditor (polarity false):
#    the grantor and the source of a statement are different parties
match $x isa authorisation (grantor: $g, holder: $h, power: $p, scope: $s);
  $p has wm-id "can-sign-off"; $s has wm-id "depot-7"; $a isa attestation (content: $x, attester: $who), has polarity $pol;
  $g has wm-id $gid; $h has wm-id $hid; $who has wm-id $by;
fetch { "holder": $hid, "grantor": $gid, "polarity": $pol, "by": $by };

# Functional dependencies only (G3) -> pump depends on motor (the informational dependency on the manual is excluded)
match $d isa depends-on (dependent: $x, dependee: $y, kind: $k); $k has wm-id "functional";
  $x has wm-id $xid; $y has wm-id $yid;
fetch { "dependent": $xid, "dependee": $yid };
```

## 7. Recommended implementation sequence (each step committed, pushed and gated as before)
1. **D-0 groundwork (general, small).**
   - Fix the G4 exact-label defect in three places, with profile-subtype tests.
   - Profile packaging: `schema/profiles/<name>.tql`, plus a Python registry of each profile's slots and seed
     vocabulary, installed through `install_module`.
   - Core-protection test: the whole suite with all profiles installed.
   - Label-collision test.
2. **D-1 mechanical.**
   - The `depends-on` kind (core conformance) and `dependencies(kind=)`.
   - `mechanical-0.1` (`connected-to`, `replacement`).
   - Extend the gearbox world: seat roles, a functional dependency chain, a replacement with removed and fitted parts.
3. **D-2 organisations.**
   - `organisation-0.1` and the `authorised()` query.
   - `check_action` reports office and authority at the time.
   - A depot scenario covering: appointment and dismissal; conflicting accounts; perspectives; a knowledge-time view;
     a hypothetical reorganisation.
4. **D-3 laboratory.**
   - `laboratory-0.1`: sampling, and calibration as content.
   - `measurements()` reports the calibration in force.
   - Extend the lab world.
5. **D-4 cross-domain suite.**
   - The eight questions of section 6 over the three worlds, on both query paths.
   - Benchmark against the Stage C numbers.
   - Measure profile installation time against the plan's ceiling (≤ 5 s).

Deferred (not in Stage D):
- failure propagation;
- delegation chains;
- obligations;
- reconciliation policies;
- quality instances;
- structured conditions;
- the observation type;
- context containment, if D-D-4 is declined.

## 8. Decisions requiring approval
| # | Decision | Recommendation (all approved, LABS-1.022; see 8a) |
|---|---|---|
| D-D-1 | Stage D needs **no foundational change**. Profiles may add only sortals, proposition and event subtypes, roles, concepts and slot metadata | approve |
| D-D-2 | Add the dependency `kind` to core `depends-on` (v0.2 §3.4 conformance; additive) and a kind filter to `dependencies()` | approve |
| D-D-3 | **Authority is separate from role and from ability.** Profile relation `authorisation(grantor, holder, power, scope)`; new query `authorised()`; `capable()` keeps meaning ability. "An office confers a power" is **not** inferred in Stage D. If wanted later, it becomes a named query-time rule with INFERRED answers citing both premises | approve without the rule |
| D-D-4 | Context containment for capabilities and authority | keep exact matching (conservative) in Stage D; defer the named rule `context-within/v1` |
| D-D-5 | Single-holder offices as a proposition subtype (`office-holding sub classified-as`) with its own slot, not slot conditions on concepts | approve |
| D-D-6 | Profile design rule: specialise a core event role at most once per event type; further participants get profile roles (G5) | approve; no core cardinality change |
| D-D-7 | Calibration as attested content (`calibration-of`) resting on a certificate, alongside the record's text reference (D-C-1 unchanged); `measurements()` reports calibration status at the activity's time; no automatic invalidation | approve |
| D-D-8 | Quality instances (v0.2 extension point) deferred beyond Stage D | approve |
| D-D-9 | Profile packaging: one schema file plus a Python registry of slots and seed vocabulary per profile; profiles are never uninstalled; labels must not collide | approve (resolves U-4) |
| D-D-10 | Fix the G4 exact-label defect as Stage D groundwork, not as a separate Stage C patch | approve |
| D-D-11 | `component` and `instrument` are categories or roles, not sortals (deviation from the plan's Stage D table) | approve |

## 8a. Rulings (LABS-1.022)
All of D-D-1 to D-D-11 are **approved**. Qualifications, binding on the implementation:

| # | Qualification |
|---|---|
| D-D-2 | Dependency kinds must preserve historical untyped dependencies as **unspecified**. A `depends-on` with no kind is never read as functional, or as any other kind. A kind filter excludes it, and reports it apart as "kind unspecified" |
| D-D-3 | **Authority, capability, role occupancy and action remain distinct.** An authorisation claim does not establish that its grantor was entitled to confer the power. Whether the grantor held authority to grant is a separate question, about separate content |
| D-D-5 | Single-holder offices are **exclusive within their defined organisational and temporal scope**. Conflicting appointments remain representable and are **judged** (DISPUTED), not rejected at write time |
| D-D-6 | Event-role specialisation at most once per event type is a **TypeDB modelling constraint** (3.14.1 role cardinality), not an ontological universal |
| D-D-9 | Profiles must be **independently installable and composable, without implicit cross-profile dependencies** |
| D-D-10 | **Generic APIs must recognise profile subtypes** |
| D-D-1, 4, 7, 8, 11 | approved as recommended |

## 9. Risks
| Kind | Risk | Mitigation |
|---|---|---|
| Generality | `classified-as` carries categories, materials, roles, offices, capabilities, seats and agency. Readers that do not filter by concept subtype mix them | queries filter by concept subtype (`capability`, `social-role`, `category`); tests per subtype |
| Generality | "context" means a place, an organisation, an assembly or an occurrence; questions such as "where is it?" need a domain reading | answers report the context's kind; no cross-domain merging of location and context |
| Generality | vocabulary creep towards an industry ontology | profiles capped at the scenarios' needs; new terms only with a test that uses them |
| Correctness | conflating occupying a role with having authority, or ability with authority | D-D-3; separate queries and tests where they diverge (an office without authority, authority without the office) |
| Correctness | exact context matching gives conservative "not established" answers where a person would expect containment | documented; D-D-4 named rule if wanted |
| Correctness | a slot declared on a broad predicate (`classified-as`) silently makes every subtype exclusive (U-5 inheritance) | slots only on profile subtypes; a test that `classified-as` has no slot |
| Correctness | further exact-label code paths dropping profile subtypes | D-0 audit fix plus a test that every profile subtype appears in each general query |
| Correctness | a "general" capability applies in every context. That is acceptable for ability, dangerous for authority | authority always has a scope in the draft (`scope` role) |
| Performance | `roles_of()` opens one transaction per class; measurement reads are N+1 (D-C-6); data-volume growth slows unchanged queries (Stage C bench) | measure in D-4 against Stage C; batching stays deferred unless thresholds are breached |
| Performance | more types and roles enlarge lattice introspection and profile installation | measure installation time (plan ceiling ≤ 5 s for three profiles) |

## 10. Probe results (summary of `probes/core04_d_review.out.json`)
| Probe | Result |
|---|---|
| D0 | the four drafts install together after the core; the lattice maps person, organisation, sample → core kinds, `office-holding` → `classified-as`, `replacement`/`decision`/`sampling` → `event`; specialised roles map to `patient`, `actor`, `origin` |
| D1a | capability: workshop established; bay-1 (part of workshop) not established |
| D1b | the kind-less `depends-on` key is unchanged; `dependencies(pump)` = [manual, motor] (kinds mixed); the functional dependency holds (ASSERTED) |
| D1c-alt | two specialisations of `patient` in one event: rejected at commit (`@card(0..1)`) |
| D1c | `replacement` with `removed` (as patient) and `fitted` (own role): stored, found by `events(participant=b1)` |
| D2a | two accepted site managers at depot-7: DISPUTED [bea, cal]; analysts not exclusive (ASSERTED); `roles_of(bea)` = [analyst] only (defect G4); `capable` sees the office |
| D2b | office ASSERTED with authorisation NOT_YET_KNOWN; after acme's accepted grant, ASSERTED/holds (system), ASSERTED/does not hold (auditor's own denial); after the system accepts the denial, DISPUTED; `capable(can-sign-off)` "not established" throughout |
| D2c | a `decision` with `capacity: site-manager` (a concept as participant) is stored and found by participant |
| D2d | `changes(bea)` lists employment (world-state), office and authorisation transitions; acme (organisation) is an agent |
| D3a | `sampling` found by `events(participant=rock)` (origin); `constitution(s12, rock)` |
| D3b | `calibration-of` rests on cert-1; holds 5 Nov (ASSERTED); does not hold 9 Nov (ASSERTED, holds False) |
