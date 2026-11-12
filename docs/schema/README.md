# Reference schema export

The schema of a reference database, exported from the live database by `worldmodel.schema_export`
(LABS-1.024; design and decisions in [../schema-export/design.md](../schema-export/design.md)).

The reference database holds the full core (seven modules) and the three domain profiles (mechanical,
organisation, laboratory), installed in their registered order. It is built, exported and deleted by:

    uv run python scripts/export_schema.py --reference

A test (`tests/test_o_schema_export.py`) fails when these files no longer match a fresh export, so they cannot go
stale unnoticed.

| File | What it is |
|---|---|
| `schema-explorer.html` | **Start here.** Open it in a browser (double-click). One file; it needs no internet and makes no network requests. Search, filters, a page per type, role, function and module, and the checks |
| `schema.tql` | The database's schema exactly as TypeDB returns it (`schema()`), byte for byte. It can be defined into an empty database to rebuild the schema |
| `schema.json` | The full export in the versioned format `wm-schema-export/1` (its JSON Schema is `src/worldmodel/schema_export/wm-schema-export-1.schema.json`) |
| `manifest.json` | What was exported and when, the results of every check, the attribution counts, every unresolved item, and a SHA-256 for each file |

## Where each piece of information comes from
Every section of the export says where it comes from, and the explorer shows it as a badge:

- **database**: read from TypeDB, or worked out from what was read (for example "inherited from `particular`");
- **reconstructed**: which module (core layer or profile) contributed each declaration. TypeDB does not record this, so
  the exporter replays the recorded modules from this repository's code into temporary databases and requires an exact
  match with the database before calling anything `attributed`;
- **repository**: comments written in the `.tql` files. Shown separately, never checked against the database.

## What the checks say for this export
- the schema text is parsed with every character accounted for (487 declarations, annotations and functions);
- the parse agrees exactly with TypeDB's own query answers (types, supertypes, owns, plays, relates, role
  specialisations and value types);
- the schema rebuilds identically in an empty database (the only check available for annotations and functions,
  which TypeDB 3.14.1 cannot answer by query);
- the replay matches the database exactly, so all 487 facts are `attributed` and module data is verified.
