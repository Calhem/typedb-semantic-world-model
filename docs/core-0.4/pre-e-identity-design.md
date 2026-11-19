# Pre-Stage E correction: contextually established identity (DI-12, DI-15, DI-16), design

**Status:** design only (LABS-1.046). No code is changed; nothing here is implemented until approved.
Branch `feature/pre-e-corrections-design`, from `main` `bf60c1f`.

**In plain terms.** Two names can be recorded as naming one thing (a `same-as` link). Today the model treats two
names as one thing as soon as *any* accepted link says so, even when an accepted denial says they are not, and it
uses that merge in some reports but not in others. This design makes identity follow the same rule as every other
fact since increment B: two names are one thing only where the link between them is **established** in the context
asked about (world, knowledge time, perspective), and then every report uses that one identity.

Evidence (all on throwaway databases, code unchanged):
- `probes/pre_e_identity_cases.py` → `.out.txt`: 28 checks over acceptance, knowledge time, valid time, perspective,
  hypothetical worlds, transitivity and conflicting evidence, with today's answer and the answer under this design;
- `probes/pre_e_di16_repro.py` → `.out.txt`: the minimal DI-16 reproduction (see
  [pre-e-di16-clarification.md](pre-e-di16-clarification.md));
- `probes/pre_e_consolidation.py` (LABS-1.045) for DI-15, and `probes/pre_e_b_di12.py` for DI-12.

## 1. The defects

| Issue | What happens today | Evidence |
|---|---|---|
| **DI-16** | `Identity` unions every *usable* same-as assertion and ignores denials. A link asserted and accepted, then denied by an accepted denial, is DISPUTED as content, but still merges the two names (I3, I9). | identity probe I3, I9; DI-16 reproduction |
| **DI-15** | `occurrence(o-1)` and `occurrence(o-1-alias)` list the same two accounts, but each judges only the accounts linked to its own name: the official is "established: bea" from one name and "established: b-smith" from the other. The other account's `describes` is `None`. | identity probe, last section; consolidation probe |
| **DI-12** | `parts` and `dependencies` traverse links with an empty identity, so a part attached to another name of a thing is missed; reports built on `_contents` select contents by the subject's own id, not by its other names. | `probes/pre_e_b_di12.out.txt` |
| **New: F-1, circular link judgement** | The canonical judgement of a same-as content is itself taken through identity: a link's content class is keyed by *canonical* names, so once r1~r2 and r2~r3 merge, `judgement(same-as(r1, r3))` is "established" with no record of its own (I15), and an established link v1~v2 reads "disputed" because a neighbouring link v2~v3 is disputed (I18). Identity is built from judgements that depend on identity. | identity probe I15, I16, I18 ("judgement today" against "by stated names") |
| **New: F-2, plan worlds** | `Identity` ignores world precedence: a hypothetical world that stipulates the denial of an inherited link still merges the two names (I12), although the link's own judgement in that world is NOT_HOLDING (the nearer world decides). | identity probe I12 |

What already behaves as this design requires (no change): unreviewed, rejected and superseded links never merge
(I2, I5, I6); knowledge time (I8, I9 before the denial); perspective (I11); links only in a plan or only after a
plan's knowledge limit (I13, I14); a pending link breaks a chain (I17).

Impact on the reference worlds: **none expected.** The reference worlds hold no same-as content at all (0 in the
rebuilt reference database `wm-probe-pre-e-d-new`, counted for this design; DI-12 found no accepted link in any of the
11 worlds), so neither the 106,752-answer nor the 398-view baseline can change. Both are acceptance gates
of the implementation (section 7).

## 2. Terms
- **Stated names:** the two ids a same-as attestation names, as written.
- **Identity link:** the same-as content for one unordered pair of stated names.
- **Link judgement:** the canonical judgement (increment B's `ContentJudgement`) of one identity link in a context,
  computed by its stated names (section 3.1).
- **Identity class:** the names the perspective takes as one thing in a context.
- **Context:** (world, knowledge time `as_of`, perspective). Identity does not depend on valid time (section 3.3).

## 3. Proposed semantics

### 3.1 ID-1: an identity link is judged by its stated names
Each identity link is judged by the canonical mechanism's polarity layer exactly as any other content (world
precedence: the nearest world's deciding attestations win; acceptance; supersession; polarity), keyed by its **stated**
names and never through identity. This removes F-1: a link's judgement depends only on the attestations of that pair.
No constraint applies to same-as (none is declared, and none may be: a single-value constraint on identity would make
two names of one thing a conflict).

### 3.2 ID-2: only an ESTABLISHED link merges
An identity link joins two names only where its link judgement is **ESTABLISHED**. Everything else joins nothing:
- **DISPUTED** (an accepted assertion and an accepted denial in the deciding world): DI-16, I3, I9;
- **NOT_HOLDING** (denied; superseded by its source's denial): I4, I6;
- **PENDING** (only unreviewed assertions): I2, I11 for other perspectives;
- **UNKNOWN** (rejected or retracted assertions, no evidence): I5, I13, I14;
- **contextually inapplicable**: attestations not visible in the context, which the judgement never sees: another
  world's own links, a base world's links recorded after a variant's knowledge limit, decisions recorded after `as_of`,
  other perspectives' acceptances.

### 3.3 ID-3: identity is timeless (valid time does not enter)
Identity is decided once per context, the same for every valid time `t`. A same-as attestation's stated interval is
**ignored** for identity, and the link judgement is computed as if each attestation held for the whole timeline (its
verdict is its polarity). Today's `Identity` already ignores intervals (I10: merged at every `t`), so identity answers
do not change; what changes is `judgement("same-as", ...)`, which today says "not yet effective" before a stated start
and "ended" after a stated end (I10), and would answer the same at every `t`.

Why not a time-indexed identity: every content class is keyed by canonical names. If two names were one thing at noon
and two things at one o'clock, the same attestation would belong to different contents at different times, so
`changes()` (a scan over boundaries), the frozen snapshots and `value_at` over a period could not compare contents
across time. "These records named one thing during a period" is a different relation (a register mapping, a role
holding) and belongs in a profile type, not in `same-as`.

Proposed with it (a new write rule): from this increment on, `attest(world, "same-as", ...)` with a `start` or a
stated `end` is refused with a message saying identity is timeless. Existing intervals are kept and ignored as above.

### 3.4 ID-4: transitivity
Identity classes are the connected components of the established links (I15: r1~r2 and r2~r3 established make r1, r2
and r3 one class, although no attestation names r1 with r3). A link that is not established breaks the chain (I17,
I18 for v3).

### 3.5 ID-5: conflicting evidence inside a class
A component is **in conflict** when two of its members are the stated names of a link whose judgement is DISPUTED or
NOT_HOLDING by denial (the evidence explicitly says they are *not* one thing, or is split on it), while established
links connect them through other names. Example I16: s1~s2 and s2~s3 established, s1 ≠ s3 denied and accepted.

Proposed: a component in conflict is **not merged at all**: each of its names is its own class, and `identity()`
reports the conflict (the names, the established links, and the denying or disputed links, each with its evidence).
Consequences: answers about those names are computed as if no link existed among them, and where two of those names
are different players of a single-valued role the role becomes DISPUTED, never silently one player (I16: s1 and s2,
whose own link is established, are not merged either).

Alternatives considered:
- (b) merge the component and report the conflict beside merged answers: the denial would still be overridden, the
  defect DI-16 describes;
- (c) remove a minimal set of links that separates each denied pair: not unique (several cuts of equal size), so the
  answer would depend on an arbitrary choice or on order, against the order-independence criterion (T-3).
Rule (a) is conservative, deterministic and independent of the order links are read in.

### 3.6 ID-6: worlds and hypothetical inheritance
- The nearest world decides a link (ID-1), so a hypothetical world that stipulates the denial of an inherited link
  separates the two names **in that world and its descendants only** (I12; the base world keeps them merged).
- A link stipulated in a variant merges only in the variant and its descendants (I13).
- A variant inherits base links recorded by its knowledge limit (I14), as every other content.
- Reporting: `identity()` and `occurrence()`'s identity section (section 3.8) say, per link, the world it was decided
  in (depth 0: the asked world; n: inherited from the n-th base), so a plan's reader can see that an identity was
  inherited, overridden or added.

### 3.7 ID-7: perspective and knowledge time
Identity is per perspective and knowledge time, as today: a perspective merges only on links established for it
(its own attestations, its acceptances, stipulations). A view at a knowledge time before a denial is unchanged (I9,
reproducible); from the denial's recording time on, the names separate.

### 3.8 ID-8: one identity, used by every reader
Every reader takes its identity from the same function in the same context, and selects contents by the subject's
whole identity class, not its own id:
- the judgement path (`holds`, `value_at`, `facts_about`, `judgement`): unchanged in shape, new identity;
- `_contents` and every report built on it (office holders, appointments, dependencies listing, existence and describes
  records of `occurrence_status`): selection by class members (DI-12's "selection difference");
- `parts` and `dependencies` (DI-12, option (a)): links are judged under identity and the traversal moves between
  classes: from a reached thing, every link naming any member of its class is followed; the reported ids are the ones
  the links state;
- `occurrence()` and `descriptions()` (DI-15): see section 3.9;
- unchanged by design: frame chains (frames cannot be named in same-as; same-as relates particulars only), and the
  TypeDB function `parts_in_database` (documented as world-scoped, ignoring time and acceptance; it stays an
  identity-free storage traversal and says so).

### 3.9 ID-9: occurrence aliases (DI-15)
For any member `x` of an occurrence's identity class, `occurrence(world, x)` gives the same view except its
`occurrence` key:
- `descriptions` and `accounts`: every description linked to any member;
- each account's `describes` is the canonical record of describes(description, *class*): links to `o-1` and to
  `o-1-alias` from one description are one content under identity, judged once;
- `roles`: rule Q (ER-4) over all compared accounts of the class, players under the same identity (bea and b-smith
  are one player only where their own link is established);
- new, additive: `aliases` (the class members) and `identity` (the established links used, each with its world depth,
  and any conflict reported for the class).
`occurrence_status` and `exists` take the class the same way (`exists` already does).

### 3.10 What answers report
Shapes are unchanged except the additive `aliases` and `identity` fields of `occurrence()` and two fields of
`identity()`'s result (`conflicts`, and `links`: the established links with their support). Answers that compared
players under identity keep citing their own support; the identity links they relied on are listed by `identity()`
and `occurrence()`, not added to every answer's evidence (that would change 106,752 answers' shape; it can be
proposed separately if wanted).

## 4. Cases (executed today; expected under the design)

From `probes/pre_e_identity_cases.out.txt` (system perspective in the actual world unless stated):

| Case | Setup | Merged today | Design |
|---|---|---|---|
| I1 | accepted assertion | yes | yes |
| I2 | unreviewed assertion | no | no |
| I3 | accepted assertion + accepted denial (DI-16) | **yes** | **no** |
| I4 | accepted denial only | no | no |
| I5 | rejected assertion | no | no |
| I6 | assertion superseded by its source's denial | no | no |
| I7 | two accepted assertions, a rejected denial | yes | yes |
| I8 | before / after the acceptance (`as_of`) | no / yes | no / yes |
| I9 | before / after an accepted denial (`as_of`) | yes / **yes** | yes / **no** |
| I10 | link stated over [10th, 20th), asked on the 5th, 15th, 25th | yes at all three | yes at all three (timeless; the link's judgement also becomes timeless) |
| I11 | hr's own link: perspectives hr / system / clerk | yes / no / no | yes / no / no |
| I12 | base link; plan stipulates its denial: plan / base | **yes** / yes | **no** / yes |
| I13 | link stipulated in a plan: plan / base | yes / no | yes / no |
| I14 | plan whose base knowledge ends before the link | no | no |
| I15 | r1~r2, r2~r3 accepted: r1 and r3 | yes | yes |
| I16 | s1~s2, s2~s3 accepted, s1 ≠ s3 accepted denial: s1–s3 / s1–s2 | **yes** / **yes** | **no** / **no** (component in conflict) |
| I17 | u1~u2 accepted, u2~u3 pending: u1 and u3 | no | no |
| I18 | v1~v2 accepted, v2~v3 disputed: v1–v3 / v1–v2 | **yes** / yes | **no** / yes |
| DI-15 | accounts under o-1 and o-1-alias, accepted alias link | two different "established" officials | one view from either name |

Cases to add as permanent tests with the implementation, beyond the table: the DI-15 case with bea and b-smith merged
(one official, established) and not merged (DISPUTED from both names); a conflict component in a plan that inherits
only part of the chain; a perspective that accepted the denial but not the assertion; a same-as attested with an
interval being refused (ID-3); `parts`/`dependencies` through an alias (DI-12's probe), and the same with the alias
link disputed (the closure does not cross it); result-order independence of conflict detection (shuffled loads).

## 5. Inventory: where identity is built today
- `WorldModel.identity` (full load, or selective from given ids), `_identity_links` (selective, transitive frontier),
  `_selective_identity` (adds linked players of loaded attestations), `_view`, `_question`: all build `Identity` from
  loaded same-as attestations. **Change:** one constructor that takes the loaded same-as attestations *and* the
  context, judges each link by its stated names (ID-1, ID-3), and builds classes (ID-4, ID-5). The selective frontier
  grows only through established links; the denials and disputes among the names it reaches are already loaded by the
  same subject query (same-as attestations of both polarities name the same subjects).
- `_closure` and `_frame_edges`: an empty identity today. **Change:** `_closure` uses the context's identity (DI-12);
  `_frame_edges` unchanged (frames).
- `_event_roles`, `descriptions`, `occurrence_status`, `_contents`: select by own id in places. **Change:** by class.

## 6. Compatibility and migration
- **Schema and data:** no schema change and no data migration. Existing same-as attestations are read as they are.
- **Behaviour on existing databases:** answers change only where a database has (i) a same-as link that is disputed,
  denied, or overridden in a nearer world while a chain or the link itself was merging names; (ii) a conflict
  component; (iii) an alias whose contents a by-id report did not select. None exists in the reference worlds.
- **Reproducibility:** identity at a knowledge time before a denial is unchanged (I9), so a view frozen then is
  reproduced by the corrected code. A view frozen after a denial by the old code differs from the corrected code
  exactly where DI-16 applied: that is the correction.
- **API:** `Identity`'s constructor changes (internal); `identity()` gains `conflicts` and `links`; `occurrence()` gains
  `aliases` and `identity`. `judgement("same-as", ...)` answers change (F-1 removed; timeless). The write refusal of
  ID-3 is new. Schema export: unaffected (no type changes).
- **Tests that will change:** the `Identity` unit tests (`tests/test_b_semantics.py`, `tests/test_m1_semantics.py`) for
  the new constructor; any test relying on a merge across a denial or a plan denial (none found by search; to be
  confirmed by the suite).

## 7. Acceptance gates for the implementation
1. The permanent tests of section 4 pass on both paths, in all four configurations, twice.
2. The 106,752-answer snapshot and the 398-view comparison show **0** differences (no reference world has an
   accepted same-as link); any difference blocks the merge until explained.
3. `probes/pre_e_identity_cases.py` reports 0 lines where today's merge differs from the design (after the fix the
   "today" column is the corrected code), and the DI-15 views from both names are equal.
4. Performance: query counts of `pre_e_d_occurrence_bench.py`, `pre_e_b_read_bench.py` and the Core 0.3 benchmark
   (P-1 baseline) per question are unchanged or the difference is reported per reader; expected: no added query on
   the selective path (links are already loaded), one same-as load per `parts`/`dependencies` call.

## 8. Not changed
The foundational ontology and the same-as type; the acceptance model; world inheritance; event-role semantics other
than which accounts are compared (ER-1 to ER-8 stand); frame chains; storage.

Related observation, outside this design unless approved: `descriptions()` lists descriptions by a *usable* describes
link, not by the link's canonical judgement (a disputed link still lists its description), while `occurrence()`'s
`accounts` (increment D) judges each link canonically. It could be aligned in the same increment (decision ID-10).

## 9. Decisions for approval (exact wording)
- **ID-1.** An identity link is judged by its stated names with the canonical polarity layer, never through identity.
- **ID-2.** Two names are one thing only where a link between them is ESTABLISHED in the context; disputed, denied,
  pending, unknown and contextually inapplicable links join nothing. (Resolves DI-16 by its option (a).)
- **ID-3.** Identity is timeless: valid time does not enter; stated intervals on same-as are ignored, and new same-as
  attestations with an interval are refused.
- **ID-4.** Identity classes are the connected components of established links.
- **ID-5.** A component containing two names whose own link is disputed or denied is not merged at all, and the
  conflict is reported.
- **ID-6.** The nearest world decides each link; a variant's denial or stipulated link applies in it and its
  descendants only.
- **ID-7.** Identity is per perspective and knowledge time (unchanged).
- **ID-8.** Every reader uses this identity and selects contents by the subject's class (DI-12 options (a) and the
  selection difference), except frame chains and `parts_in_database`.
- **ID-9.** `occurrence()` gives one view for every name of an occurrence (DI-15), with additive `aliases` and
  `identity` fields.
- **ID-10 (optional).** `descriptions()` lists by the describes link's canonical judgement, as `occurrence()`'s
  `accounts` does.
