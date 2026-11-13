# LABS-1.024: authoritative schema export and explorer, design and fidelity review

**Status: approved** (LABS-1.032, LABS-1.033), with the amended decisions in section 10, which take precedence over
sections 1 to 9 where they differ. The review baseline of sections 1 to 9 is commit `ca3aede`.

**Evidence.** Three executed probes against TypeDB CE 3.14.1. Each builds the full core with all three domain profiles
in a throwaway database, and deletes it afterwards:
- `probes/labs1024_introspection.py`: what the database exposes, and what it refuses;
- `probes/labs1024_schema_text.py`: the shape of the schema text TypeDB returns, and type attribution;
- `probes/labs1024_replay.py`: attribution of every declaration to a module, by replay.

Their recorded output is in the matching `.out.txt` files. Figures below are from those files.

## 1. Goal and fidelity rule
An export of the schema **of a given database**, produced from that database, in three forms:
- the executable TypeQL schema;
- a machine-readable JSON description;
- a standalone interactive HTML explorer built only from that JSON.

**Fidelity rule:**
- **Everything about the schema comes from the database.** The repository's `.tql` files are never read as a
  description of the schema.
- **One question the database cannot answer:** which module added which declaration. For that, the exporter reads
  the module records stored in the database, then replays those modules from the repository into a temporary
  database (section 4).
- **The replay is checked, not trusted.** It must reproduce the target's schema exactly. Otherwise the attribution
  is reported as unverified, and nothing is silently guessed.
- **Nothing is maintained by hand:** no diagram, and no separately written model.

## 2. What TypeDB 3.14.1 exposes (probe results)
| Source | What it gives | Probe finding |
|---|---|---|
| `database.schema()` | the full schema as TypeQL text: types, annotations, functions | 10,502 characters for the core + 3 profiles. **Deterministic** (two calls give the same text). **Round-trips exactly:** defined into an empty database, it gives back an identical `schema()`. Takes about 1 ms. **Comments are not kept** |
| `database.type_schema()` | the same without functions | 9,623 characters; 0 functions (`schema()` has 2: `parts_in`, `frames_linked`) |
| `match entity $t;` (also `relation`, `attribute`) | every type | 21 entity, 35 relation and 51 attribute types (107) |
| `match $t sub! $s;` | direct supertypes | 54 pairs |
| `match $t owns $a;` / `$t plays $r;` / `$t relates $r;` | ownership, roles played, roles related | **include inherited ones** (`sample` owns `wm-id` through `particular`). There is **no declared-only form** (`owns!` is a syntax error) |
| `match relation $t; $t relates $r; $r sub! $p;` | role specialisation (`relates sampler as actor`) | 5 specialisations. The parent role is still reported as related: `sampling relates event:actor` is true. `$t relates $r as $p` also matches each role with itself, so it is not used |
| `match attribute $a value string;` | attributes of one value type | works as a filter only; `$a value $v` (binding the value type) is a syntax error |
| annotations (`@key`, `@card`, `@abstract`, `@values`, `@range`) in a query | none | **refused**: `[REP254] The language feature is not yet implemented: QueryingAnnotations`. `@abstract` as a match constraint is a syntax error |
| functions in a query | none | `match fun $f;` is a syntax error. Functions exist only in `schema()` text |
| `driver.server_version()` | server version | "TypeDB CE 3.14.1" |
| `schema-module` records (data) | installed modules and versions | 7 core modules and 3 profiles, with versions. **No record of which types or declarations each module added, and no install order** |

**The schema text is regular.** `schema()` returns TypeDB's own normalised output, not the hand-written files:
- one statement per type, and one declaration per line (`sub`, `owns`, `plays`, `relates … as …`, `value`), with
  its annotations;
- **declared-only:** `sample` lists `sub physical-object` and `plays sampling:product`, not its inherited `owns
  wm-id`.

So the text and the queries are two independent views of the same schema:
- the text is declared-only and carries the annotations;
- the queries include inherited declarations and carry no annotations.

**Annotations used today:** `@abstract` (5), `@key` (11), `@card` (20, five forms), `@values` (5), `@range` (2).

## 3. Architecture
```
target database ──read tx + schema()──► (A) text parser ──┐
                └──concept queries────► (B) query reader ─┴─► cross-check ─► model ─► schema.tql
schema-module records ─► (C) replay in a temporary database ─► attribution ─┘          schema.json
                                                                                       schema-explorer.html
```
1. **Read**, in one read transaction plus `schema()`. Nothing is written to the target.
2. **(A) The text parser** reads `schema()` (TypeDB's normalised form, section 2) into declarations: a type's kind
   and type annotations, `sub`, `value`, `owns`, `plays` and `relates` (with `as` and annotations), and each
   function (name, signature, full text).
3. **(B) The query reader** reads the type sets, `sub!`, `owns`, `plays`, `relates`, role specialisations and value
   types (one filter query per value type).
4. **Cross-check (required):**
   - A's declarations, inherited down the supertype graph, must equal B's answers exactly: types, supertypes, owns,
     plays, relates, specialisations and value types;
   - any difference **fails the export**, with the differing items listed. A schema is never exported half-checked.

   Annotations have only one source (A), because TypeDB refuses to query them. They are covered instead by the exact
   round trip in the tests (section 6).
5. **(C) Attribution by replay** (section 4).
6. **Model:**
   - every type with its declared and inherited capabilities (each inherited one names the type it comes from);
   - roles, with who relates and who plays them;
   - attributes, with who owns them;
   - functions;
   - modules.
7. **Outputs**, in one directory:
   - `schema.tql`: exactly `schema()`, byte for byte;
   - `schema.json` (section 5);
   - `schema-explorer.html` (section 7);
   - `manifest.json`: the source, the time, and the SHA-256 of each file and of the schema text.

**Code layout (proposed):**
- `src/worldmodel/schema_export.py` (read, parse, cross-check, attribute, model);
- `scripts/export_schema.py <database> [--out DIR]`;
- the explorer page template in `src/worldmodel/schema_explorer.html`;
- no new dependencies.

## 4. Core and profiles: attribution by replay
The database records which modules are installed, but not what each added. The probe also shows that **profiles
extend core types**: the laboratory profile adds `plays sampling:sampler` to the core `particular`, and
`plays sampling:sampled` and `plays calibration-of:calibrated` to `physical-object`. So attribution must be **per
declaration**, not per type.

**Method** (`labs1024_replay.py`: 3.0 s for the core and three profiles):
1. Read the target's `schema-module` records. If a recorded version differs from the code's module version, refuse
   to attribute, and name the module.
2. In a temporary database (`wm-export-tmp-<random>`, always deleted), define the core modules in order. Record the
   declarations each adds (core layers: core-0.3, A0, A, A2, B, C, D).
3. For each recorded profile, the core plus that profile alone, then diff against the core.
4. **Verify:** core plus every profile must equal the target's declarations exactly.
   - **Probe:** 439 = 375 core + 12 mechanical + 36 organisation + 16 laboratory. This holds, although the target
     installed the profiles in a different order; no declaration belongs to two profiles.
   - **If it fails** (for example, schema defined by hand outside `install_profile`), attribution is reported as
     **unverified**. Each declaration that no recorded module explains is labelled `unattributed`.
5. **In the model:**
   - each declaration gets its module;
   - each type gets `defined_by` (the module whose statement declares the type itself) and `extended_by` (other
     modules adding to it);
   - each function gets its module.

## 5. JSON format (`wm-schema-export/1`)
- **`source`:**
  - database name;
  - server version (`driver.server_version()`);
  - export time;
  - SHA-256 of `schema()`;
  - exporter version;
  - the git commit of the code used for the replay.
- **`modules`:** each with name, version, kind (`core` or `profile`) and `attribution` (`verified` or
  `unverified`).
- **`types`:** each with:
  - label, kind, `abstract`, type annotations;
  - `supertype`, `supertypes` (the chain), `subtypes` (direct);
  - `value_type` (attributes) and its annotations (`@values`, `@range`, `@regex`);
  - `owns`: attribute, annotations, and `from` (this type, or the ancestor it is inherited from);
  - `plays`: role and `from`;
  - `relates` (relations): role, `specialises`, annotations and `from`;
  - `defined_by`, `extended_by`;
  - `declarations`: each declared line with its module.
- **`roles`:** scoped label, relation, specialises, `played_by` (declared and inherited).
- **`attributes_owned_by`**, the reverse index.
- **`functions`:** name, parameters and return (parsed from the signature), the full text, the types it names, and
  its module.
- **`typeql`:** the `schema()` text, so the JSON is complete on its own.
- **`checks`:** the cross-check and replay results (counts, and any differences).

A JSON Schema document for the format itself (`schema-export.schema.json`) is shipped with the exporter. Tests
validate exports against it with a small built-in checker, not a new library.

## 6. Fidelity tests (planned)
1. **TypeQL round trip:** `schema.tql`, defined into an empty database, gives an identical `schema()`. This also
   covers every annotation.
2. **JSON against the database:** every owns, plays, relates, supertype and value type in the JSON, inherited ones
   included, matches the query reader. A test also changes one line of the schema text and expects the cross-check
   to fail.
3. **Attribution:**
   - three-profile databases in every install order give the same attribution;
   - a declaration added by hand (a manual `define`) appears as `unattributed`, with attribution `unverified`;
   - a version mismatch refuses attribution.
4. **Determinism:** two exports of one database differ only in the export time.
5. **The explorer's data is the export:**
   - the JSON embedded in `schema-explorer.html` is identical to `schema.json`;
   - the page makes no network requests;
   - a browser check confirms search, filters and navigation on the reference export.
6. **Core and profiles:** for each profile, `defined_by` and `extended_by` match the replay. Core-only types never
   show a profile.

## 7. The explorer (standalone HTML)
- **One file:** the JSON is embedded, there are no external scripts, fonts or network requests, and it opens from
  disk. The estimated size is under 400 KB for today's schema.
- **Header:** database, server version, export time, schema hash, modules, and the attribution result (verified or
  not).
- **Browse:** three trees (entity, relation, attribute), following the supertype graph.
- **Search** over labels, role names and function names, with ranking by match type.
- **Filters** (combinable, counts shown):
  - kind;
  - core only, profiles only, or a single module;
  - abstract;
  - with an annotation (`@key`, `@card`, `@values`, `@range`);
  - extended by a profile.
- **Type page:**
  - the supertype chain and direct subtypes;
  - owns, plays and relates, each marked declared or inherited (and from where), with annotations and module badges;
  - for a relation: its roles and which types can play each;
  - for an attribute: its value type, its constraints and its owners;
  - the functions that name the type;
  - the declarations with their modules;
  - the exact TypeQL statement.
- **Navigation:**
  - every type and role is a link;
  - each page has its own address (`#type/sample`, `#role/sampling:sampler`), so the browser's back and forward
    buttons and bookmarks work;
  - a small neighbourhood diagram (SVG, drawn in the page from the JSON) shows supertypes, subtypes, relations and
    roles to one or two steps.
- **Core and profiles are visually distinct:** a profile colour on each badge, legend in the header, and the same
  distinction in every list.
- **Accessibility:** keyboard navigation, readable at phone width, light and dark themes.

## 8. Limitations
- **Annotations have one source.** TypeDB 3.14.1 cannot query them (REP254). They are read from `schema()` text and
  checked by the exact round trip, but not cross-checked against queries. This will be revisited when TypeDB
  supports annotation queries.
- **No descriptions in the database.** TypeDB does not keep comments, so the explanatory comments in the
  repository's `.tql` files are not in `schema()`. See decision E-4.
- **Specialised roles are reported as TypeDB reports them:** for example, `sampling` also relates the parent role
  `event:actor`. The explorer will show such roles as "related through a specialisation".
- **Function bodies are text.** The exporter parses each signature and the types a body names. It does not
  interpret the body.
- **Install order is not recorded.** It does not matter today: every order gives the same schema (D-3 test), and no
  declaration is shared by two profiles.
- **Profile data is not schema.** A profile's vocabulary concepts (for example `laboratory:specimen`) and
  functional-slot records are data in the database, not schema. See decision E-5.
- **Attribution needs the repository code at the recorded module versions**, and permission to create a temporary
  database. Without either, the export still runs, with attribution `unverified`.

## 9. Decisions for approval
| # | Decision | Recommended |
|---|---|---|
| E-1 | Sources: `schema()` text and concept queries, with a required exact cross-check (section 3) | yes |
| E-2 | Core/profile attribution by verified replay in a temporary database, per declaration, with `unverified` / `unattributed` when the replay does not reproduce the schema | yes |
| E-3 | Outputs and layout: `schema.tql` (exactly `schema()`), `schema.json`, `schema-explorer.html`, `manifest.json`; code in `schema_export.py` and `scripts/export_schema.py`. The export of the reference database (core + three profiles) is committed under `docs/schema/`, with a test that fails when it is stale | yes |
| E-4 | Repository comments as **descriptions**: either (a) none, or (b) included in a separate, clearly labelled "documentation from the repository (not from the database)" field, keyed by label, with labels that no longer exist reported | (b) |
| E-5 | Installed profile data (vocabulary concepts and functional slots) read from the database and shown in a separate "module data" section, never mixed with the schema | yes |
| E-6 | The explorer: a single file with no external libraries or network access | yes |
| E-7 | A versioned JSON format (`wm-schema-export/1`) with its own JSON Schema, checked without a new dependency | yes |

**Out of scope:** exporting data (instances), editing the schema, and Stage E.

## 10. Approved decisions (LABS-1.032, LABS-1.033)
The owner approved the architecture with two requirements, and then E-1 to E-7 in the amended wording below.

**Requirement 1: the live TypeDB schema is authoritative.** Every exported fact is labelled with its source:
- **`database`**: read from TypeDB (the `schema()` text, query answers, module records, server version), or computed by
  the exporter from those reads alone (for example "inherited from X", reverse indexes, parsed function signatures);
- **`reconstructed`**: needs the repository's code as well as the database (core and profile attribution by replay).
  Checked against the database, but not stored in it;
- **`repository`**: taken from the repository only and never checked against the database (comments in `.tql` files).

**Requirement 2: attribution per declaration and per contribution.** Each fact has one of four statuses (LABS-1.033):

| Status | Meaning |
|---|---|
| `attributed` | proven by a complete matching replay: one module contributes it |
| `shared` | proven by a complete matching replay: more than one module contributes it. All are listed; none is the owner |
| `consistent_unverified` | local replay evidence points to a module, but the complete replay did not match the database |
| `unresolved` | attribution cannot be established |

A partial replay never produces `attributed` or `shared`. The manifest records the overall replay verification status
and every unresolved contribution.

**Schema fidelity (LABS-1.033).** If parsing or cross-checking cannot account for every declaration, annotation, role,
constraint and function in the database's schema, the export fails, rather than produce a schema that looks complete
but is not. Annotations and functions have a single database source (the `schema()` text). They are accepted on that
text plus a successful round trip, and the export states that limitation.

| # | Approved decision |
|---|---|
| E-1 | Sources: `schema()` text and concept queries, with a required exact cross-check. Every exported fact is labelled `database`, `reconstructed` or `repository`. Facts with only one database source (annotations, functions) are marked as such |
| E-2 | Attribution by verified replay, labelled `reconstructed`, per declaration and per annotation, with the four statuses above. Types show what introduced them and each addition separately, and are never given a single owner. A partial replay proves nothing (E-2a) |
| E-3 | Outputs and layout: `schema.tql` (exactly `schema()`), `schema.json`, `schema-explorer.html`, `manifest.json`; code in `worldmodel.schema_export` and `scripts/export_schema.py`. The export of the reference database (core and three profiles) is committed under `docs/schema/`, with a test that fails when it is stale. The manifest also records the git commit used for the replay and the comments, the replay verification status, and the counts of attributed, shared, unverified and unresolved facts, with every unresolved one listed |
| E-4 | Option (b): repository comments in a separate field labelled `repository`, with file, line and commit; they never affect attribution or any database field; comments on labels absent from the database are reported |
| E-5 | Installed module data (vocabulary concepts and functional slots) read from the database and shown in a separate "module data" section, never mixed with the schema. The records are `database`; which module they belong to is `reconstructed` |
| E-6 | The explorer: a single file with no external libraries or network access. It shows the three sources and the attribution statuses with text badges and a legend (never colour alone), with filters for both, and repository comments in a separate, labelled box |
| E-7 | A versioned JSON format (`wm-schema-export/1`) with its own JSON Schema, checked without a new dependency. Version 1 requires a source on every section and a status on every attribution |

**Clarification (LABS-1.034): reproducibility, not history.** `attributed` and `shared` mean verified
*reproducibility*: the recorded modules, replayed from this code, reproduce the database's schema exactly, and the
named module adds the declaration in that reproduction. They never describe the database's actual installation
history (install order, in-place upgrades, changes later undone), which TypeDB does not keep. The wording of the
export, the explorer and these documents keeps the two apart.

**Known gap in replay, stated in the export.** TypeDB accepts a declaration that repeats one already in the schema, and
a replay cannot see the repeat. Such a fact is attributed to the module that first introduced it; a repeat found in
another module's source text is reported as a `repository` note, not as shared ownership. Sharing between two
profiles is provable (each is replayed onto the core on its own) and is reported as `shared`.
