# LABS-1.024: schema export implementation, review gate (LABS-1.033)

**Status: merged into `main` (LABS-1.034, merge commit `a8c4b44`).** The approved design
is [design.md](design.md) (section 10 holds the approved decisions; the review baseline of sections 1 to 9 is
`ca3aede`). The reference export and its explorer are in [docs/schema](../schema/README.md).

## How to use it
```
uv run python scripts/export_schema.py <database> [--out DIR] [--require-verified]
uv run python scripts/export_schema.py --reference          # rebuilds docs/schema/
```
It writes `schema.tql`, `schema.json`, `schema-explorer.html` and `manifest.json` (default `exports/<database>/`,
git-ignored). Exit status 1 means the export was refused and nothing was written; 2 means it was written but
`--require-verified` was given and the attribution is not verified.

## Increments
| # | Commit | What |
|---|---|---|
| 0 | `4fcf00d` | the approved decisions recorded (design section 10) |
| 1 | `f993ef1` | canonical extraction and an exact parser of `schema()` |
| 2 | `b867281` | independent query cross-check and round trip |
| 3 | `0c56541` | module replay and per-declaration attribution, the four statuses, repository notes |
| 4 | `85d1942` | the versioned JSON export, its JSON Schema and checker, the manifest, the command line |
| 5 | `63021ed` | documentation from the repository's comments, and module data |
| 6 | `50d48f3` | the standalone HTML explorer |
| 7 | `311652d` | the committed reference export, staleness tests, documentation |

Code: `src/worldmodel/schema_export/` (`parse`, `introspect`, `crosscheck`, `attribution`, `sourcescan`, `docs`,
`export`, `validate`, `explorer`, the page template `explorer.html` and the format's JSON Schema
`wm-schema-export-1.schema.json`), `scripts/export_schema.py`, `tests/test_o_schema_export.py`.

## 1. Schema fidelity and coverage
The database's schema is the authority. The export is produced only if all three checks pass; otherwise it is refused
and nothing is written.

| Check | What it proves | Reference result |
|---|---|---|
| **Exact parse** | The parser accepts only TypeDB's normalised `schema()` form and must re-render it byte for byte, so every character (declaration, annotation, role, constraint, function) is accounted for | 10,502 characters; 107 types, 2 functions, **487 facts** |
| **Query cross-check** | The parsed declarations, inherited down the supertype graph, equal TypeDB's own query answers exactly | kinds 107, direct supertypes 49, owns 180, plays 460, relates 99, role specialisations 5, value types 51: no difference |
| **Round trip** | The exported TypeQL, defined into an empty temporary database, gives back an identical `schema()` and identical query answers | identical |

A **fact** is one declaration of the schema: a type, a type annotation, a supertype, a value type, a value annotation,
an `owns`, `plays` or `relates` and each of their annotations, a role specialisation, or a function. The reference has
107 type facts, 86 plays, 78 relates, 73 owns, 49 supertypes, 44 value types, 43 annotations, 5 specialisations and
2 functions.

**Single source, stated in the export.** Annotations and functions come only from the `schema()` text: TypeDB 3.14.1
cannot query annotations (REP254) and has no query listing functions. They are covered by the exact parse and the
round trip, and the export says so (`schema.single_source`, and on the explorer's Checks page). Function bodies are
kept as text; signatures are parsed; the types a body names are found by matching its words against type labels.

**Tests of the failure paths:** nine kinds of text the parser refuses; cross-check failures on a removed `plays`, a
removed supertype and a changed value type; round-trip failures on a missing `@key`, a missing `@abstract` and a
missing function; and an export refused on a query mismatch, with nothing written.

## 2. Attribution verification
The database records which modules are installed, not what each added. The exporter replays the recorded modules
from this repository's code into temporary databases: the core one module at a time, each profile alone on the core,
and everything together. **Verification** needs every recorded module known at its recorded version, every step to
succeed, and the complete replay to equal the database's facts and module records exactly.

**Reproducibility, not history.** A verified attribution establishes that the schema is *reproducible* from the
recorded modules, and which module adds each declaration *in that reproduction*. It is not the database's
installation history: TypeDB keeps none (no install order, no record of an in-place upgrade or of a change later
undone), and the export never claims one. "Introduced by" and "extended by" are to be read in that sense.

| Status | Meaning | Reference |
|---|---|---|
| `attributed` | verified; exactly one module adds it in the reproduction | **487** |
| `shared` | verified; more than one profile adds it in the reproduction | 0 |
| `consistent_unverified` | replay steps add it, but verification failed | 0 |
| `unresolved` | no replay step adds it | 0 |

**Reference: verified.** Facts by module: core 263, core-0.4-a0 19, core-0.4-a 68, core-0.4-a2 1, core-0.4-b 8,
core-0.4-c 54, core-0.4-d 3, laboratory 19, mechanical 15, organisation 37. Module data (18 concept and
functional-slot records) verified.

**Per declaration, never one owner per type.** For example, in the reproduction `particular` is introduced by `core` and extended by
`core-0.4-a`, `profile:laboratory` and `profile:organisation`; the laboratory profile contributes exactly
`particular plays sampling:sampler`. Inherited capabilities keep the attribution of the declaration on the ancestor.

**Repeated declarations.** A repeat leaves no trace in a replay, because TypeDB accepts it silently. The exporter
reads each module's source text (labelled `repository`) and reports repeats separately. It found one real repeat:
`core-0.4-d` declares `relation depends-on` again, which `core` already declares. It stays `attributed` to `core`,
with a repository note. The source scan read every statement of all 12 module files and found every replayed
declaration.

**Partial replay never proves anything** (tested): a version mismatch, an unknown recorded module, schema defined
outside any module, and module code that changed after installation each give `verification: failed`. Facts some
step still explains become `consistent_unverified`, the rest `unresolved`, and every unresolved fact is listed in the
manifest. Missing module data fails the module-data verification only.

**`shared` is not reachable today.** The profile rules (D-D-1) refuse a profile that redeclares another profile's
type or capability, and TypeDB refuses a second definition of a function. So two installed profiles cannot both add
the same fact. The `shared` path is tested with the profile rule relaxed for the test: there, both profiles' facts are
`shared`; with the rule in force the same database is `consistent_unverified` (the complete replay is refused).

**Install order.** All six install orders of the three profiles give identical attribution.

## 3. Export format and validation
`wm-schema-export/1`. Every top-level section states its source: `source`, `verification` and `schema` are
`database` (computed fields are listed in `schema.computed_fields`); `attribution` is `reconstructed`, its
`repository_notes` are `repository`; `documentation` is `repository`; `module_data` records are `database` and their
attribution `reconstructed` (a record only the replay has is marked `reconstructed`). Every attribution has one of the
four statuses.

The JSON Schema (`wm-schema-export-1.schema.json`) requires the source on every section, the status on every
attribution, and forbids unknown fields in the parts that carry facts. The checker (`validate.py`, no new dependency)
supports exactly the JSON Schema keywords the format uses and refuses any other, so no rule is silently ignored.
Tests check the reference export is valid and that eight kinds of mislabelled or unknown content are rejected.

`manifest.json` holds the source, the export details (time, exporter, the code commit used for the replay and the
comments, and whether `src/` or `schema/` had uncommitted changes), the three check results, the replay verification
and its problems, the attribution counts, every unresolved fact, the module-data verification and its unresolved
records, the documentation's unknown labels, and a SHA-256 for every file.

## 4. Explorer
One HTML file (355 KB for the reference) with the export embedded; no external libraries, fonts or requests, and a
Content-Security-Policy (`default-src 'none'`) so the browser refuses any network access. All text is inserted as
text, never as markup, and the embedded data escapes every `<`.

- **Header and legend:** database, server version, schema hash, export time, the attribution result; the three
  sources as text badges.
- **Search** over types, roles and functions, ranked (exact, prefix, word, substring), optionally over repository
  comments; `/` focuses it, arrow keys move through results.
- **Filters:** kind, attribution status, module, core or profiles, annotation, abstract, extended by a profile; the
  type trees keep matching types' ancestors, dimmed.
- **Pages with their own addresses** (`#type/…`, `#role/…`, `#fun/…`, `#module/…`, `#facts`, `#data`, `#checks`),
  so back, forward and bookmarks work. A type page: supertypes, subtypes, value type, a neighbourhood diagram,
  owns/plays/relates each marked declared or inherited (and from where) with the attribution of the declaring fact,
  the exact TypeQL, per-module contributions and repeats (reconstructed), and the repository comments in a separate
  dashed box labelled "not from the database".
- **Light and dark themes**; at phone width the sidebar folds behind a Menu button.

**Checked in a browser** (the in-app browser, on the reference export): no console errors; no network requests;
search ("sampl", "actor", a phrase from a comment); every filter; navigation by links and addresses; both themes; a
375 px wide screen with no sideways page scroll. Tests check the page embeds exactly the export, references nothing
external, escapes markup in data, covers every view and control, and that the committed page is exactly the
rendering of the committed JSON.

## 5. Test results and performance
**New tests:** 68 in `tests/test_o_schema_export.py`, all marked `own_profiles` (they build their own databases), using
temporary databases named `wm-test-*`. Each increment's tests passed before its commit; the complete suite is run
below on the final head.

**Full suite on `311652d`, eight runs** (in a clean checkout, one at a time): selective and full load
(`WM_SELECTIVE=0`), each also as the core-protection run (`WM_PROFILES=1`), each twice. **Every run: 449 passed**
(the 381 existing tests and the 68 new ones). No test database and no exporter temporary database
(`wm-export-tmp-*`, `wm-schema-reference`) was left over. Each run took 9 min 46 s to 12 min 15 s; the new test file
alone takes about 45 s.

**Export time** (reference, core and three profiles): read 0.04 s, parse and cross-check under 0.01 s, round trip
0.15 to 0.22 s, replay 2.5 to 4.0 s, model 0.05 s: **about 3 to 4 s**, almost all of it the replay (one temporary
database per profile, each rebuilding the core). Files: `schema.json` 424 KB, `schema-explorer.html` 355 KB,
`schema.tql` 10.5 KB.

## 6. Known limitations
1. **Annotations and functions have one source** (the schema text), with the exact parse and the round trip as their
   checks, as approved. To revisit when TypeDB can query annotations.
2. **Repeats are invisible to replay.** They are found only by reading module source text (repository evidence).
3. **A replay proves consistency, not history.** Core modules are replayed in their canonical order, so a core fact is
   attributed to the first core layer that produces it, whatever path the target took (for example an in-place
   upgrade to A0).
4. **Profiles are replayed each alone on the core.** A profile that depended on another profile would fail its own
   replay, and the attribution would be reported unverified, not guessed. No current profile does.
5. **`shared` is unreachable** under the current profile rules (section 2).
6. **The setup step.** One module-data record (the core `located-at` functional slot) is written by
   `WorldModel.create` after the core modules, not by a module. It is reported as the setup step `WorldModel.create`.
7. **Attribution needs this repository's code at the recorded module versions** and permission to create temporary
   databases (`wm-export-tmp-*`, always deleted; only a killed process could leave one).
8. **Module data is read in full** (every concept and functional-slot record). Not measured on a large database.
9. **The explorer needs JavaScript.** Its neighbourhood diagram shows declared neighbours, two supertype levels and one
   level otherwise; inherited ones are in the tables. Search lists at most 300 results.
10. **The browser check is by hand** (recorded above), not an automated test. Automated browser regression coverage
    is registered as maintenance item DI-10 (`docs/core-0.4/deferred-issues.md`), not blocking.

## 7. Deviations from the approved design
1. **Code layout.** A package `worldmodel.schema_export` with one module per concern, instead of one
   `schema_export.py`; the page template is `schema_export/explorer.html`; the JSON Schema is
   `wm-schema-export-1.schema.json` (design: `schema-export.schema.json`). Approved E-3 already names
   `worldmodel.schema_export`.
2. **A setup step in the attribution** (`WorldModel.create`), for the record written after the core modules
   (limitation 6). Not in the design.
3. **The neighbourhood diagram** draws one step (two for supertypes); the design said "one or two steps".
4. **The design's browser check** (section 6.5) was done by hand, not automated.
5. **`code_dirty`** is recorded in the export and manifest as well as the code commit (an addition).
