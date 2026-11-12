# Core 0.4 Stage D-3: scientific (laboratory) profile, design review (LABS-1.027)

**Status (2026-11-11): approved (LABS-1.028) and implemented: see `stage-d3.md`.** Originally the design for approval. Branch
`feature/core-0.4-d3-science` from `main` 8461e23 (D-2 merged).
- Evidence: the draft `docs/core-0.4/stage-d3/laboratory-0.1.draft.tql`, and the executed probe
  `probes/core04_d3_design.py` (output `probes/core04_d3_design.out.json`).
- The probe runs on the Stage C laboratory world, with the mechanical and organisation profiles and the draft
  installed together.
- **Next cross-cutting deliverable after D-3:** LABS-1.024, the explorable schema export. It is kept apart from
  Stage E.

## 1. Coverage matrix
Codes:
- **S:** supported now (core and Stage C);
- **V:** needs profile vocabulary;
- **X:** needs a small general or profile API;
- **F:** needs a foundational change;
- **Df:** deferred.

Probe references are to the output file.

| Requirement | Class | How, and evidence |
|---|---|---|
| Specimens | S | any physical object, classified `laboratory:specimen` (vocabulary); the Stage C `sample-12` stays a physical object and serves as the specimen |
| Samples | V | sortal `sample sub physical-object`. Its identity is its portion of matter, so splitting or consuming it ends it (v0.2 §3.1 "portion") and sub-samples are new particulars |
| Sampling activity | V | `sampling sub event`: sampler as actor, sampled as origin, product as destination (one specialisation each, D-D-6). P3: stored, and found by `events(participant=specimen)` |
| Sample provenance | S | core `constitution(sample, source)`, attested; chains of sub-samples (P3: s12-b → s12-a → sample-12); custody through `located-at` (P3: s12-a in freezer-2) |
| Account vs occurrence vs effects | S | P3: the sampling account is accepted, its occurrence "not established", its claimed effects accepted; yet s12-a's **existence is NOT_YET_KNOWN**, because a claimed effect is not evidence of the state |
| Experiments | S | an `occurrence` classified `laboratory:experiment`, with its steps `part-of` it; `process_steps` lists them (P8) |
| Experimental protocol | S | an information object |
| Experimental conditions | S (records, exact text, D-C-7); Df (structure) | conditions as attested states of the set-up, linked to records, are deferred (G-4) |
| Instruments | S | the core `instrument` event role; kinds of instrument are categories |
| Calibration | V | `calibration-of(certificate, calibrated)`, attested over its valid time and resting on the certificate (`rests-on`) (D-D-7). P4 |
| Temporal validity of calibration | S | the attestation's interval. P4: the B3 certificate ends at 10:00; at the 15:00 activity it no longer holds (ASSERTED, false) |
| Calibration at measurement time | X | read per measurement: the activity's instrument, and `calibration-of` judged at the activity's start (P4, done with core `holds`). A profile report is proposed (§3) |
| Calibration never invalidates | S | P4: the measurement after expiry is still compared; P5: a disputed B7 calibration (DISPUTED for the system, "does not hold" for QA) leaves Bo's B7 result usable. The stated `calibration-ref` and the attested calibration are reported side by side; they can differ (P4: a B7 result states no reference, yet a certificate covers it) |
| Observations and results | S | result records with `rests-on` (Stage C). A qualitative observation can back any attestation through `attest(evidence=…)` (P7) |
| Measurement layers | S | P6: activity (event description), record (information object: 3490 g), proposition (SI content key), and judgement (system: accepted; lab-2: unreviewed) are four things |
| Corrections, conflicts, uncertainty | S | Stage C: supersession per perspective, `compare_measurements`, u and k on records, coverage on content |
| Scientific claims | S | ordinary propositions (classification, quality, `causes`) attested by their sources |
| Competing interpretations | S, plus a gap (G-1) | P7: a hypothesis (stance `hypothesises`) is recorded and resting on its record, but never supports (UNKNOWN); a rival claim is judged on its own; rival contents are not a conflict unless a profile declares one. Reverse lookup ("what rests on this record?") is raw TypeQL (P7) |
| Coexistence with the other profiles | S | P1: mechanical, organisation and the draft install together; P2: core laboratory answers are identical before and after |
| Quality instances | not introduced | excluded by instruction |

## 2. Proposed schema (profile `laboratory` 0.1; additive only)
| Type | Definition |
|---|---|
| `sample sub physical-object` | sortal (portion identity) |
| `sampling sub event` | `sampler as actor`, `sampled as origin`, `product as destination` |
| `calibration-of(certificate, calibrated)` | proposition; certificate: an information object; calibrated: a physical object |

**Vocabulary** (prefixed `laboratory:`):
- `specimen`, `experiment` (categories);
- `calibration` (event kind, for calibration activities).

**Unchanged:** nothing else changes. Measurement, record, `rests-on`, `produced`, `reports`, comparability, units and
corrections are core (Stage C).

## 3. Proposed API (`worldmodel.laboratory`; functions taking the WorldModel, as in D-1 and D-2)
| Function | Returns |
|---|---|
| `take_sample(wm, world, sampler, specimen, sample, start, end=None, occurrence=None, attester=…)` | a `sampling` account, plus the effects its source claims (`initiates existence(sample)`, `initiates constitution(sample, specimen)`); claims only |
| `provenance(wm, world, sample, t)` | the asserted constitution chain (listing, not inference), each link with its judgement; the sampling accounts naming it as product, with account acceptance and occurrence status; its location history |
| `calibrate(wm, world, certificate, instrument, start, end=None, attester=…)` | a `calibration-of` attestation resting on the certificate |
| `calibration_status(wm, world, instrument, t)` | each certificate's calibration content at t, with its judgement (established, expired, denied, disputed, not yet effective, not established) and evidence |
| `measurement_calibration(wm, world, bearer, quality, t)` | for each measurement record: its activity's instrument, its **stated** calibration reference, and the **attested** calibration judged at the activity's start. A report beside the measurement: it never changes usability or comparison |
| `interpretations(wm, world, record)` | the attestations resting on a record (any content), with stance, basis, attester and judgement |

Shared judgement: the `capable()` helpers (`_holding_label`, `_combine`), as in D-2.

## 4. Executed probes (summary; full output in the probe file)
| Probe | Result |
|---|---|
| P1 | mechanical, organisation and the laboratory draft installed together; the D0 laboratory **test fixture** is refused alongside the draft (it also defines `sample` and `sampling`), so its labels will be renamed (test-only), as for the other fixtures |
| P2 | `compare_measurements` (two perspectives), `measurements` and `capable` on the laboratory world are identical before and after installing all three profiles |
| P3 | sampling account accepted; occurrence "not established"; claimed `existence` effect accepted while existence stays NOT_YET_KNOWN; constitution chain and custody recorded |
| P4 | B3 calibration holds at 09:00 and does not hold at 15:00 (expired); the 15:00 result is still compared; the stated reference and the attested calibration are reported side by side |
| P5 | B7 calibration disputed (system) / does not hold (QA's own denial); the B7 result is still usable |
| P6 | the four layers of one measurement are distinct, and judged per perspective |
| P7 | hypothesis: UNKNOWN (non-supporting stance); the rival assertion with basis "inference": unreviewed (UNKNOWN), and **INFERRED** once accepted, or in its source's own view (see G-1) |
| P8 | an experiment occurrence lists its sampling step |
| DI-6 | confirmed by execution: holders ASSERTED, ASSERTED, STIPULATED give "ASSERTED" overall |

## 5. Semantic gaps
| # | Gap | Example | Class | Proposal |
|---|---|---|---|---|
| G-1 | **Human interpretation with basis "inference" is reported INFERRED.** v0.2 E6 reserves derived (INFERRED) attestations for ones that name a rule and premises; an analyst's interpretation names neither (`rests-on` gives premises, not a rule) | P7: lab-2's "anhydrous" becomes INFERRED once accepted | decision (no code) | interpretations by people or labs use basis `testimony` (their stated conclusion) or stance `hypothesises` (tentative), resting on their records; basis `inference` is reserved for rule-derived attestations. Document it; validating it on write is optional (decision D-D3-4) |
| G-2 | Competing interpretations are not judged as rivals | "hydrated" and "anhydrous" can both be ASSERTED | by design | keep: rival hypotheses may coexist. A profile can declare exclusivity later (a slot on a profile proposition type) if a scenario needs it |
| G-3 | No "undermines" link: `rests-on` records support only; v0.2's evidence construct (supports/undermines, with a method) is deferred | a record that counts against a claim | Df | counter-evidence is a denial attestation resting on its record (works now). A general evidence relation is a later core decision |
| G-4 | Conditions are text on records and not linked to attested states of the set-up | "temperature=20C" vs an attested chamber temperature | Df (D-C-7) | defer |
| G-5 | Sampling accounts with conflicting participants (two accounts naming different products) | as DI-2 | DI-2 | resolved with DI-2 before Stage E |
| G-6 | The stated calibration reference is text, not a link | `CAL-B3-2026-10` vs certificate `cert-b3` | accepted (D-C-1) | the profile reports both; it does not reconcile them |

**No foundational gap.** No new foundational category, no automatic scientific inference, and no quality instances.

## 6. Decisions requiring approval
| # | Decision | Recommendation |
|---|---|---|
| D-D3-1 | The schema in §2: `sample` (portion sortal), `sampling` (three specialised roles), `calibration-of`; specimens and experiments as categories | approve |
| D-D3-2 | Calibration at measurement time is computed from the activity's instrument and time (no new link from record to certificate). The stated reference and the attested calibration are both reported, never reconciled, and never change usability | approve |
| D-D3-3 | The API in §3, including `interpretations(record)` as a profile function. The reverse `rests-on` lookup could later become core, if other profiles need it | approve |
| D-D3-4 | G-1 convention: interpretations by people or organisations use basis `testimony` or stance `hypothesises`; basis `inference` only for rule-derived attestations (documented, not enforced) | approve |
| D-D3-5 | Rename the D0 laboratory fixture's labels (test-only) | approve |
| D-D3-6 | No exclusivity between competing interpretations by default (G-2) | approve |

## 7. Recommended implementation scope (D-3)
1. The profile (§2), registered as `laboratory` 0.1, and the fixture rename.
2. `worldmodel.laboratory` (§3), using the shared judgement helpers. Every report lists disputed and expired
   calibrations, and never drops or invalidates.
3. A laboratory reference extension on top of the Stage C world:
   - sub-samples;
   - a sampling account with its occurrence unestablished;
   - certificates (one expiring, one disputed);
   - a hypothesis and a rival interpretation;
   - an experiment occurrence.
4. A demonstration with raw TypeQL; tests covering every probe claim, both query paths, and coexistence of all three
   profiles.
5. Benchmark against D-2 (both run orders).

**Deferred:** G-3 (an evidence relation), G-4 (structured conditions), reconciliation policies, quality instances.

## 8. Cross-domain generality: what needed vocabulary vs what the core already had
| Domain | Needed profile vocabulary | Already in the core |
|---|---|---|
| Mechanical (D-1) | `connected-to`, `replacement` | part-of, constitution, frames, dependency (with kinds, core), events, qualities |
| Organisational (D-2) | `person`, `organisation`, `employment`, `office-holding`, `exclusive-office`, `authorisation`, `official-act` | membership, structure, roles, capabilities, agency, events |
| Scientific (D-3) | `sample`, `sampling`, `calibration-of` | measurement (activity, record, proposition), comparability, corrections, `rests-on`, constitution, location, hypotheses (stance), events, processes |

Each profile is a handful of types. The core interpretation is unchanged by all three together (P2, and the D-1 and D-2
core-protection runs).
