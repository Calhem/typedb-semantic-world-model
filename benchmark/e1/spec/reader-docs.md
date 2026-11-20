# Documented semantics of the readers used by the Stage E1 benchmark

Extracted verbatim from the library's documentation strings (main `6364fdf`). These are the documented
semantics a question author may rely on, together with the specification documents listed in
../README.md. They are not implementation code and not system output.

## `WorldModel.holds(world, type, roles, t, as_of=None, perspective='system')`

```text
Does this content hold at t for the perspective? Evidence-backed status with polarity: the canonical
judgement (`judgement`) as an Answer.
```

## `WorldModel.value_at(world, type, subject, t, as_of=None, perspective='system', key_role=None, value_role=None)`

```text
The value(s) of a relationship for `subject` at valid time t, for a perspective, as known at `as_of`.
```

## `WorldModel.judgement(world, type, roles, t, as_of=None, perspective='system', attested=True, _memo=None)`

```text
The canonical judgement (a ContentJudgement) of the content holds() asks about: `type` or a subtype, with
the given players among its own. Nothing recorded at all: UNKNOWN with reason no_evidence. attested False:
only declared constraints apply (how an attested constraint is itself judged: never recursively).
```

## `WorldModel.exists(world, thing, t, as_of=None, perspective='system')`

```text
ASSERTED/STIPULATED from existence attestations (before creation and after destruction: false); INFERRED
true if the thing takes part in content holding at t; otherwise UNKNOWN, or NOT_YET_KNOWN.

An occurrence (LABS-1.012) is judged only from attestations of its own existence: taking part in holding
content (an accepted describes link, a causal claim, part-of a process) never establishes that it happened,
so without an existence judgement the answer is UNKNOWN (records about it are visible) or NOT_YET_KNOWN.
Other things keep the Core 0.3 rule. occurrence_status() reads its status from this answer.
```

## `WorldModel.identity(world, as_of=None, perspective='system', ids=None)`

```text
Identity closure for the perspective. With `ids`, only same-as links touching the growing group are loaded.
```

## `WorldModel.parts(world, whole, t, as_of=None, perspective='system', report=False)`

```text
Transitive parts at t (application closure over the part-of content established for the perspective).
report True: {"reached": the same ids, "not_traversed": the part-of links from reached things that were not
followed (disputed, pending or unknown at t), each with its judgement and evidence}.
```

## `WorldModel.direct_dependencies(world, dependent, t, as_of=None, perspective='system')`

```text
What `dependent` directly depends on at t, one entry per dependency content that holds (or is disputed):
dependee, kind (a category id, or "unspecified" when the content names none), status and support. Asserted
dependencies only: nothing is inferred (no transitivity, no failure propagation).
```

## `WorldModel.occurrence(world, occurrence, as_of=None, perspective='system')`

```text
A merged view of an occurrence. Conflicts stay visible and traceable; nothing is merged in storage.

- `descriptions`: the descriptions the perspective accepts as describing it (as `descriptions()`);
- `participants`: the core-role projection, unchanged since Core 0.3: for each core role name (a profile's own
  new role keeps its name) every participant with the descriptions and sources that name it;
- `accounts` (LABS-1.043, ER-5): every description linked to it by a visible describes claim, accepted or not,
  with its event type, sources, link judgement (`describes`, the canonical record's claim label at the
  account's start), account state (occurrence_status's vocabulary), world depth and roles by stored label;
- `roles` (ER-5): keyed by stored role label (`replacement:removed`), with its own name and core role, every
  player and the accounts naming it, and `constraints`: each applicable event-role constraint (ER-1, ER-2)
  with whether it applies and why, and the role's judgement by rule Q (ER-4): DISPUTED for two or more
  distinct players under the perspective's identity, established for one, with status and support. Several
  players of a role without an applicable, established constraint are a union, never a dispute.
  LABS-1.049 (DI-13): each constraint also gives its `multiplicity` ("one" or "set"), the `reason` for a
  dispute, and for "set" each compared account's set (`sets`); see `_event_roles`.
```

## `WorldModel.occurrence_status(world, occurrence, t, as_of=None, perspective='system', details=True, _memo=None)`

```text
Whether the occurrence happened, for the perspective (LABS-1.011): judged only from attestations of its own
existence (existence(existent: occurrence)), never from accepted descriptions, describes links or causal
claims. `status` is accepted, denied, disputed or "not established". Each description that some source links
to it is reported separately: its source, whether the perspective accepts the account (the description's own
attestation) and the describes link. An accepted account of a denied occurrence is representable and reported
as such.
```

## `WorldModel.descriptions(world, occurrence, as_of=None, perspective='system')`

```text
Event descriptions that the perspective accepts as describing `occurrence` (or anything accepted as the
same occurrence). Without such links a description describes no known occurrence.
```

## `WorldModel.capable(world, holder, capability, t, context=None, as_of=None, perspective='system')`

```text
Does `holder` hold `capability` at t, in `context` (or in general when context is None)? A general holding
(no context) applies in every context; a contextual one only in its own. Holdings that apply only in other
contexts are listed in `only_in`; every applicable holding is listed with its evidence in `applicable`.

holds and status are the core judgement (no new statuses), combined over the applicable holdings by rule Q
(judgement.combine, increment C): the status rests on the union of the deciding claims, listed in `support`;
`judgement` names the case (LABS-1.019):
  established        holds True    an applicable holding is accepted at t
  denied             holds False   an accepted denial (polarity false) covers t
  expired            holds False   an accepted holding ended before t (no denial), as holds() treats any end
  not yet effective  holds None    an accepted holding begins after t
  disputed           holds None    DISPUTED: accepted grant and denial, or rival accepted attestations
  not established    holds None    nothing applicable is accepted (none at all, unreviewed or rejected ones,
                                   or holdings only in other contexts)
A capability never establishes an action, and an action never establishes a capability.
```

## `WorldModel.roles_of(world, holder, t, as_of=None, perspective='system')`

```text
The social roles `holder` is accepted as holding at t, each with its context.
```

## `WorldModel.move(world, thing, to, at, actor=None, kind=None, as_of=None, attester='system')`

```text
The thing was moved to `to` at `at`: ends the attester's location attestations holding just before, and
records the movement (origin, destination) with the new location as its effect. One operation.

A movement has one thing, one destination and at most one origin (LABS-1.049; origin and destination stay
single-valued under MP-1). The origin is the place the attester's own records hold the thing at just before.
If they hold it at several places, the movement is refused with MovementConflict, naming the places and the
attestations, and nothing is written: the conflicting records are not chosen between, ended or turned into
several origins. `actor` may be one agent or several (a joint move, MP-1).
```

## `WorldModel.attest(world, type=None, roles=None, *, event=None, params=None, start=None, end=None, until_superseded=False, polarity=True, stance=None, basis=None, attester='system', credence=None, clock=None, supersedes=None, id=None, evidence=None, batch=None)`

```text
Record that `attester` takes a stance on a content in `world` over a valid interval. Returns its id.

Content: a proposition (`type`, `roles`, `params`; stored once) or an event description (`event` id).
start/end: datetime, (earliest, latest) or Window; start None = from the start of the world. A missing end is
UNKNOWN unless `until_superseded` (the attester commits that it holds until it records otherwise).
Defaults: stance `stipulates` in hypothetical and simulated worlds, `asserts` otherwise; basis follows stance.
supersedes: the id of an earlier attestation by the same attester that this one replaces (a correction).
evidence (Stage C, D-C-2): functions f(tx) -> record id that create the evidence records this attestation rests
on, run in the attestation's own transaction; each record is linked by rests-on(attestation, record), so the
attestation, its records and the links are written atomically.
batch (LABS-1.020): write into a shared transaction (see _batch) with its transaction time; not committed here.
```

## `WorldModel.accept(attestation, verdict='accepted', holder='system', reason=None)`

```text
A perspective's decision about an attestation (accepted, rejected, retracted). World-independent.
```

## `WorldModel.end(world, attestation, at, reason=None)`

```text
The attester's claim now has an end: a new attestation of the same content by the same attester, with a
stated end at `at`, in `world`, superseding the old one (E3). In a variant world this never affects the base,
because the new attestation is visible only there.
```

## `WorldModel.create_world(name, kind='actual', base=None, branch_at=None, knowledge_at=None, id=None)`

```text
A world (actual, hypothetical or simulated). A variant names its base, the valid time it branches at, and
the base knowledge it inherits (`knowledge_at`, a transaction time; default now; never in the future).
```

## `WorldModel.account(world, roles, start, end=None, kind=None, occurrence=None, attester='system', id=None, type='event', **attest)`

```text
A source's account of a happening: an event description with its participants, attested by `attester`
over [start, end] (an instant when end is None), optionally classified (`kind`: a category or list) and
linked to an `occurrence` by a describes claim of the same source. Returns the description id.
```

## `WorldModel.grant(world, holder, concept, context=None, polarity=True, **attest)`

```text
Attest that `holder` holds the capability, role or category `concept` (optionally only in `context`), from
`start` to `end` or until superseded. polarity False: a denial (revocation is an ended or superseded grant).
```

## `WorldModel.depend(world, dependent, dependee, kind=None, **attest)`

```text
Attest that `dependent` depends on `dependee`, of a dependency kind (a category, e.g. dependency:functional)
or of none (kind unspecified). Requires the core-0.4-d module for a kind. Returns the attestation id.
```

## `WorldModel.changes(world, subject, t1, t2, as_of=None, perspective='system')`

```text
State transitions of `subject` whose valid time intersects (t1, t2], judged for the world, perspective and
knowledge time (LABS-1.015 contract).

The subject's records are loaded once. Every start and end bound of their windows is a boundary; the judged
state is constant between boundaries, so judging at each boundary gives the whole timeline (no extra queries).
Tracks: each functional slot whose key includes the subject (values judged as in value_at, conflicts
included), and each other content involving the subject (holds / does not hold / UNKNOWN / DISPUTED).
- category "world-state": between two accepted states; "judgement": into or out of UNKNOWN or DISPUTED, never
  presented as proof of physical change. Accepted A, then only UNKNOWN, then accepted B != A is one world-state
  transition whose window is the UNKNOWN gap: the instant is never invented.
- window [earliest, latest] and `within`: "certain" if inside (t1, t2], "possible" if it overlaps it;
  transitions outside are not returned.
- explanations: only accepted initiates / terminates claims about a content that began / ended in the
  transition, and only if the event did not certainly start after the transition. A claim that fits several
  activations of the same content is listed on each as "ambiguous"; never chosen, never inferred from
  proximity. `began` / `ended` are views over the returned transitions.
```

## `WorldModel.causes_of(world, effect, t, as_of=None, perspective='system', _memo=None)`

```text
Every causal claim about what caused `effect` (an occurrence or an event description), judged for the
perspective. Claims stated about the effect itself are direct; claims stated about another description of the
same happening (or about the occurrence a description describes) are lifted, but only through describes links
the perspective accepts, and they keep their own provenance (plan 9.3). Each claim is reported with its level
(description / occurrence / mixed), the occurrences its cause is accepted as, its judgement (accepted,
disputed, denied, unreviewed, rejected) and its sources. Nothing is inferred from order or chained.

Occurrence check (LABS-1.011): each claim also reports the status (occurrence_status) of every occurrence it
involves, and `applies`: False when one of them is denied, None when one is disputed, True otherwise. A claim
about a denied occurrence stays visible as its source's account (its own judgement is unchanged), but it does
not answer what caused the happening, and a lifted claim never makes a denied occurrence accepted.
```

## `WorldModel.effects_of(world, event, t, as_of=None, perspective='system')`

```text
The effects claimed for an event description: for each initiates / terminates claim, who claims it and the
perspective's judgement of the claim (accepted, unreviewed, rejected, denied, disputed), and separately the
judged state of the outcome just before the event starts and when it ends: the accepted world-state change.
A claim can be accepted while the state change is not (and the reverse); neither implies the other.
```

## `organisation.office_holders(wm, world, office, context, t, as_of=None, perspective='system')`

```text
Who holds `office` in `context` at t, for the perspective.
- appointments: every appointment content for this office and context, each with its own judgement and evidence
  (established, denied, expired, not yet effective, disputed, not established);
- holders: the established ones;
- exclusive: the single-holder constraint's own judgement at t;
- conflict: when the constraint holds and more than one appointment is established: the constraint's support and
  each conflicting appointment's accepted attestations;
- status (rule C, increment C): DISPUTED on a conflict or a disputed appointment; None when holders are
  established without conflict (there is no single support status for several people, or for the office: each
  appointment keeps its own status); UNKNOWN when appointments exist but none is established; NOT_YET_KNOWN when
  there are none.
Nothing is inferred about anyone not mentioned.
```

## `organisation.offices_of(wm, world, person, t, as_of=None, perspective='system')`

```text
Every office appointment naming `person`, each with its own judgement and evidence at t. An established
appointment to an exclusive office that others also hold at t is DISPUTED, with the conflict cited. No entry
means no evidence either way (never a denial).
```

## `organisation.authorised(wm, world, holder, power, scope, t, as_of=None, perspective='system')`

```text
Is `holder` authorised to exercise `power` within exactly `scope` at t (D-D-4: no containment)?
holds / status / judgement as capable() (same six cases, combined over the grants by rule Q; `support`: the
deciding claims the status rests on); grants: each authorisation content for that power and
scope, with its grantor and its reporting sources as separate fields and its own judgement and evidence; only_in:
scopes where the power is established instead; grantor_entitlement: always "not assessed" (D-D-3).
```

## `organisation.official_act(wm, world, event, power=None, as_of=None, perspective='system')`

```text
Report an official act for the perspective, as separate fields, concluding nothing beyond them:
account (accepted or not, interval); occurrences with their own status; at the act's start: the official's office
appointment (its judgement, and DISPUTED with the conflict if contested), and, for `power`, authority in the
office's context (authorised) and practical capability there (capable), and agency. Without an accepted account
there is no time, so nothing at the act's time is judged (None).

Several officials (a co-signed act, organisation 0.3, LABS-1.049): `officials` lists every official named and
`by_official` gives each one's office_held, authority, capability and agent. With exactly one official the
top-level fields are that official's, as before; with several, `official` and the four top-level judgement
fields are None (no official is chosen over another). Whether several officials are co-signatories or
conflicting evidence is judged by `occurrence()`, not here.
```

## `organisation.appoint(wm, world, holder, office, context, polarity=True, **attest)`

```text
Attest that `holder` holds `office` in `context` (a claim by its attester, over its interval). Never refused
because the office is held already. polarity False: an explicit denial of that appointment.
```

## `organisation.declare_exclusive(wm, world, office, context, **attest)`

```text
Attest a single-holder constraint on `office` within `context`, over its valid time.
```

## `organisation.authorise(wm, world, grantor, holder, power, scope, attester='system', polarity=True, **attest)`

```text
Attest, as `attester` (the reporting source), that `grantor` conferred `power` (a capability concept) on `holder`
within `scope`. The grantor and the attester are separate arguments; neither defaults to the other.
```

## `organisation.act_in_office(wm, world, official, office, context, start, end=None, occurrence=None, attester='system', id=None, kind=None)`

```text
A source's account of `official` acting in `office` within `context` (an `official-act` description).
```

## `mechanical.replace_part(wm, world, assembly, removed, fitted, start, end=None, actor=None, instrument=None, location=None, occurrence=None, attester='system', id=None)`

```text
A source's account of replacing `removed` by `fitted` in `assembly`: a `replacement` description (attested
over [start, end], optionally describing `occurrence`) and the effects the source claims for it: it terminates
part-of(removed, assembly) and initiates part-of(fitted, assembly). Claims only: nothing here establishes that
the replacement happened or that the parts changed. Returns the ids.
One operation (DI-8): the account and its effect claims are written together or not at all; inside a caller's
`wm.operation()` it joins that operation (e.g. with the creation of the sample or part).
`removed` and `fitted` may each be one part or several (a multi-part replacement, mechanical 0.3, LABS-1.049): one
account names them all, and one part-of effect is claimed per part (terminations first, then initiations).
```

## `mechanical.replacement(wm, world, event, t, as_of=None, perspective='system')`

```text
Report a replacement description for the perspective, concluding nothing beyond it:
- the account: accepted or not, its interval, the removed and fitted parts it names;
- the occurrences it is accepted as describing, each with its own status (not the account's);
- the part-of effects claimed for it, each with the claim's judgement and the state before and after (effects_of).
```

## `mechanical.connect(wm, world, a, b, joint_kind=None, **attest)`

```text
Attest a mechanical connection between parts a and b (order irrelevant), optionally of a joint kind.
```

## `laboratory.take_sample(wm, world, sampler, specimen, sample, start, end=None, occurrence=None, attester='system', id=None, kind=None)`

```text
A source's account of `sampler` taking `sample` (a `sample` particular) from `specimen`: a `sampling`
description attested over [start, end], optionally describing `occurrence`, and the effects the source claims for
it: it initiates existence(sample) and constitution(sample, specimen). Claims only: nothing here establishes that
the sampling happened, that the sample exists or what it is made of. Returns the ids.
One operation (DI-8): the account and its effect claims are written together or not at all; inside a caller's
`wm.operation()` it joins that operation (e.g. with the creation of the sample or part).
```

## `laboratory.calibrate(wm, world, certificate, instrument, start=None, end=None, attester='system', polarity=True, **attest)`

```text
Attest, as `attester`, that `certificate` calibrates `instrument` from `start` to `end` (or until superseded),
resting on the certificate (rests-on, written in the same transaction). polarity False: an explicit denial that
the certificate establishes the calibration (e.g. a quality office disputing it).
```

## `laboratory.calibration_status(wm, world, instrument, t, as_of=None, perspective='system')`

```text
Is `instrument` calibrated at t, for the perspective? holds / status / judgement as capable() (established,
expired, denied, disputed, not yet effective, not established; no new statuses; combined over the certificates
by rule Q, with the deciding claims in `support`), and every certificate whose
calibration content names the instrument, with its reference number, its own judgement and its evidence.
"not established" with no certificates means that no calibration is recorded at all.
```

## `laboratory.provenance(wm, world, sample, t, as_of=None, perspective='system')`

```text
Where `sample` came from, for the perspective at t, as separate fields that conclude nothing beyond them:
- chain: every constitution content met by following "constituted from" links back from `sample`, each once (the
  sample, what it is said to be made from, and that link's own judgement and evidence). A listing of attested
  links, not an inference: an unaccepted, disputed or denied link is listed with its judgement, never dropped, and
  followed. Each link also carries (LABS-1.031):
  - paths: every distinct route from `sample` to and including the link (as [sample, from] steps), with
    `established` (every step on the route is established at t in this world, perspective and knowledge time),
    `blocked_by` (each step that is not, with its own judgement and evidence) and `closes_cycle` (the link leads
    back to a material already on the route, so the route stops there);
  - ancestry: "established" when at least one of its paths is established, else "not established". A link that
    is itself established, but reached only through an unestablished step, is not established ancestry;
- established: the established-provenance view: only the links with an established path, with those paths;
- materials: every material reached (other than `sample`), with each route to it and whether that route is
  established. Converging routes to one material are kept apart;
- sampling: for each material reached, the sampling accounts naming it as product: the account's acceptance,
  the occurrences it describes with their own status, and the effects it claims with the claim's judgement;
- existence: the sample's attested existence (its own judgement), and the core `exists` answer beside it (which
  also infers existence from participation in holding content);
- locations: every location attestation of the sample (place, source, interval, acceptance), and where it is at t.
Routes are simple (no material twice), so cyclic claims terminate; their number can grow with converging
lineages. Each material's claims are read once.
```

## Module notes

### worldmodel.organisation

```text
Profile organisation-0.1 (Core 0.4 Stage D-2, LABS-1.026): employment, offices, authority and acts in office.

Four independent things, with no implication between any of them:
- **office-holding**: `office-holding(holder, office, context)`, a position in a context;
- **practical capability**: `classified-as(holder, capability, context?)`, read by the core `capable()`;
- **conferred authority**: `authorisation(grantor, holder, power, scope)`; the reporting source is the attestation's
  attester, never the grantor; the grantor's own entitlement is never assessed; no delegation chains;
- **actual action**: an `official-act` description; its occurrence is judged apart (`occurrence_status`).

**Single-holder offices.** An office is exclusive only where an `exclusive-office(office, context)` constraint holds
at t (attested, over its own valid time). Then, if several accepted appointments overlap at t, the reports say
DISPUTED, citing the appointments and the constraint. Appointments are never rejected on writing; each keeps its own
judgement and evidence. Nothing is inferred about anyone no appointment mentions: absence of evidence stays absence
("not established"), distinct from an explicit, accepted denial ("denied").

**Disputes are visible.** The reports read each content's canonical judgement (as `capable()` does), so content
disputed by polarity is listed as DISPUTED, never dropped; so does core `roles_of` (DI-1, LABS-1.038).

**Exclusivity is the core's.** The profile declares the scope of `exclusive-office` (EXCLUSIVE_OFFICE); the core's
canonical judgement applies it, only where the constraint is itself established in the same world, time, knowledge
time and perspective, in every reader (`holds`, `facts_about`, `capable`). `office_holders` and `offices_of` keep their
public answers (LABS-1.038, choice A): each appointment's own judgement is reported before the constraint, and the
conflict, read from the canonical judgement, is reported beside it.

Functions take the WorldModel, as in `worldmodel.mechanical`.
```

### worldmodel.mechanical

```text
Profile mechanical-0.1 (Core 0.4 Stage D-1, LABS-1.023): connections and part replacement, over the core.

Uses only core concepts: assemblies are core `part-of`; dependencies are core `depends-on` with core kinds
(`depends_on` / `direct_dependencies` on WorldModel); this module adds the profile's two contents and reporting:
- `connect` / `connections`: a mechanical connection between two parts, with its joint kind; never parthood;
- `replace_part` / `replacement`: a replacement account (removed and fitted parts told apart) with the part-of effects
  its source claims. The report keeps the account, the occurrence's own status and the claimed effects apart:
  an accepted account does not establish that the replacement occurred, and a claimed effect is not a state change.
No failure propagation or dependency inference.
```

### worldmodel.laboratory

```text
Profile laboratory-0.1 (Core 0.4 Stage D-3, LABS-1.028): samples, sampling, calibration and interpretations.

Over the core and the Stage C measurement model (activity, result record, proposition, judgement), this module adds:
- **samples and sampling**: a `sample` is a portion of matter (splitting it gives new particulars); `take_sample`
  records a source's `sampling` account and the effects it claims; `provenance` lists, separately, the attested
  constitution chain, the sampling accounts and their occurrences' own status, the claimed effects, existence and
  location history. An account establishes neither its occurrence nor the sample's existence or constitution.
- **calibration**: `calibration-of(certificate, instrument)`, attested over the certificate's valid time and resting
  on the certificate. `calibration_status` judges it at a time (established, expired, denied, disputed, not yet
  effective, not established); `measurement_calibration` judges it at each measurement activity's start and puts
  the record's **stated** reference beside the **attested** calibration, with an exact-text reference check. Nothing
  here changes a measurement's acceptance, usability or comparison.
- **interpretations**: `interpret` records an analyst's conclusion as testimony, or as a hypothesis (stance
  `hypothesises`, never supporting an answer), resting on its result record; `interpretations` lists everything
  resting on a record, each content judged on its own. Basis `inference` is reserved for rule-derived attestations
  (D-D3-4): `interpret` refuses it, and `interpretations` flags any such attestation as recorded inference without
  derivation structure. Formal derivation provenance (named rule and premises) is a Stage E requirement (DI-7).
  Competing interpretations are judged independently: no incompatibility is assumed (D-D3-6).

Specimens and experiments are classifications (`laboratory:specimen`, `laboratory:experiment`); an experiment's
steps are core `part-of` (read with `process_steps`). Judgement uses the shared helpers (`_judgement`, `judgement.combine`).
Functions take the WorldModel, as in `worldmodel.mechanical` and `worldmodel.organisation`.
```

## The canonical judgement (`worldmodel.judgement`)

```text
The canonical per-content judgement (increment B: DI-1, DI-11, DI-5; LABS-1.036 to 1.038).

One record per content (proposition) in one context: the content judged, every claim that states or denies it (each
kept separately with its own acceptance, provenance and interval), the constraints that apply, and the resulting
judgement with its reason. Every core and profile reader takes its facts from these records; nothing else judges
content, applies a constraint or names a judgement. Design: docs/core-0.4/pre-e-increment-b-design.md.

Layers, in order:
1. polarity (`_judge`, unchanged): world precedence, acceptance, supersession, valid time and polarity give, per
   content, holds / does not hold / disputed (an accepted assertion against an accepted denial), with the deciding
   attestations;
2. constraints: a holding content that gives a single-value constraint a different value than another holding content
   is disputed. Declared constraints (functional slots, data) always apply. Attested constraints (a constraint that is
   itself a claim, such as an exclusive office) apply only where their own judgement in the same context is
   ESTABLISHED; they are judged without attested constraints of their own, so evaluation never recurses further;
3. the judgement and its reason, including why an undecided content is undecided (DI-5).

Cost: the core judgement is computed from the attestations the reader already loaded. Per-claim detail (`claims()`)
is expanded only when a reader asks for it. An attested constraint is judged only where it could change a judgement
(two or more different values held under it), once per report through a memo.
```

Judgement labels: `established`, `disputed`, `not holding`, `pending`, `unknown`.

Answer statuses (`worldmodel.semantics.Status`): `OBSERVED`, `ASSERTED`, `STIPULATED`, `INFERRED`, `PRESUMED`, `DISPUTED`, `UNKNOWN`, `NOT_YET_KNOWN`.

```text
Answer classification (v0.2 §5.6, layer 3). OBSERVED and PRESUMED need observations and persistence policies,
which Core 0.3 does not implement yet (attestations with basis observation are reported as ASSERTED, with the basis
visible in the evidence).
```

