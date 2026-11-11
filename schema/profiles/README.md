# Domain profiles

One directory per profile, `schema/profiles/<name>/`, holding the TypeQL the profile owns. The profile's registry
entry (`Profile`: name, version, schema files, slots, seed vocabulary) is in `src/worldmodel/profiles.py`, its
example worlds are in `src/worldmodel/examples/`, and its tests are in `tests/`. Install with
`WorldModel.install_profile(name)` after the full core.

A profile only adds vocabulary of its own; `install_profile` refuses anything else before committing. See the
docstring of `src/worldmodel/profiles.py` and `docs/core-0.4/stage-d0.md` for the rules.

No domain profile is registered yet: Stage D domain work (D-1 to D-3) awaits authorisation. Minimal test fixtures are
in `tests/fixtures/profiles/`.
