# Domain profiles

One directory per profile, `schema/profiles/<name>/`, holding the TypeQL the profile owns. The profile's registry
entry (`Profile`: name, version, schema files, slots, seed vocabulary) is in `src/worldmodel/profiles.py`, its
example worlds are in `src/worldmodel/examples/`, and its tests are in `tests/`. Install with
`WorldModel.install_profile(name)` after the full core.

A profile only adds vocabulary of its own; `install_profile` refuses anything else before committing. See the
docstring of `src/worldmodel/profiles.py` and `docs/core-0.4/stage-d0.md` for the rules.

Registered profiles: `mechanical` 0.1 (Stage D-1), `organisation` 0.1 (D-2) and `laboratory` 0.1 (D-3). They install
independently and together, in any order. Minimal test fixtures, with labels of their own, are in
`tests/fixtures/profiles/`.
