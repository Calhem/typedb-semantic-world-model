"""Schema export (LABS-1.024, approved under LABS-1.032 and LABS-1.033): fidelity of the exported schema.

Increments 1 and 2: the canonical schema text is parsed with every character accounted for, and the parse is checked
two independent ways (TypeDB's query answers, and an exact round trip into an empty database). Every mismatch fails.
Increment 3: attribution of every fact to modules by verified replay, and the four statuses.
Increment 4: the versioned JSON export, its sources, its JSON Schema, the files and the manifest.
Increment 5: documentation from the repository's comments, and module data.
"""

import copy
import dataclasses
import hashlib
import json
import uuid

import pytest

import conftest
from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel
from worldmodel.model import DEFAULT_MODULES
from worldmodel.schema_export import SchemaExportError, SchemaParseError, facts, parse_schema, render_schema
from worldmodel.schema_export.crosscheck import Lattice, compare_answers, cross_check, round_trip
from worldmodel.profiles import PROFILES, Profile
from worldmodel.schema_export.attribution import SETUP, attribute, classify
from worldmodel.schema_export import export as ex
from worldmodel.schema_export.introspect import snapshot
from worldmodel.schema_export.validate import errors, format_schema, validate
from worldmodel.model import SCHEMA, WRITE

pytestmark = pytest.mark.own_profiles
PROFILES3 = ("mechanical", "organisation", "laboratory")
TMP = "wm-test-xtmp-"         # temporary databases of these tests (the session teardown removes any left over)


def make_db(driver, modules=CORE_MODULES, profiles=PROFILES3):
    """A database with exactly these modules and profiles (the core-protection run's automatic profiles are off)."""
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    saved, conftest.AUTO_PROFILES["on"] = conftest.AUTO_PROFILES["on"], False
    try:
        wm = WorldModel.create(name, driver=driver, modules=modules, clock=FakeClock())
    finally:
        conftest.AUTO_PROFILES["on"] = saved
    for p in profiles:
        wm.install_profile(p)
    return wm


def drop(wm):
    if wm.driver.databases.contains(wm.database):
        wm.driver.databases.get(wm.database).delete()


def leftovers(driver, prefix=TMP):
    return [db.name for db in driver.databases.all() if db.name.startswith(prefix)]


@pytest.fixture(scope="module")
def reference(driver):
    wm = make_db(driver)
    try:
        yield wm, snapshot(driver, wm.database)
    finally:
        drop(wm)


def edit_type(parsed, label, **changes):
    """A copy of a parsed schema with one type statement changed."""
    types = dict(parsed.types)
    types[label] = dataclasses.replace(parsed.types[label], **changes)
    return dataclasses.replace(parsed, types=types)


# ---- increment 1: canonical extraction and parsing -------------------------------------------------------------------
def test_parse_accounts_for_every_character(reference):
    wm, snap = reference
    parsed = parse_schema(snap.text)
    assert render_schema(parsed) == snap.text
    assert set(parsed.types) == set(snap.answers["kinds"])
    assert {t.kind for t in parsed.types.values()} == {"entity", "relation", "attribute"}
    assert list(parsed.functions) == ["parts_in", "frames_linked"]
    assert snap.server_version.startswith("TypeDB")
    assert snap.modules == wm.modules()


def test_facts_split_annotations_and_specialisations(reference):
    _, snap = reference
    f = facts(parse_schema(snap.text))
    assert f["entity particular @abstract"] == {"subject": "particular", "kind": "annotation",
                                                "of": "entity particular", "annotation": "@abstract"}
    assert f["particular owns wm-id @key"]["of"] == "particular owns wm-id"
    assert f["sampling relates sampler as actor"]["of"] == "sampling relates sampler"
    assert f["credence value double"]["kind"] == "value"
    assert f["credence value @range(0.0..1.0)"]["of"] == "credence value double"
    assert f["fun parts_in"]["text"].startswith("fun parts_in($whole: particular, $w: world) -> { particular }:")
    annotations = [v["annotation"] for v in f.values() if v["kind"] == "annotation"]
    assert annotations.count("@abstract") == snap.text.count("@abstract")
    assert sum(a.startswith("@card") for a in annotations) == snap.text.count("@card")


def test_function_signatures(reference):
    _, snap = reference
    fn = parse_schema(snap.text).functions["frames_linked"]
    assert fn.params == (("$f", "spatial-frame"), ("$w", "world"))
    assert fn.stream and fn.return_types == ("spatial-frame",)


@pytest.mark.parametrize("bad, why", [
    ("entity x,\n  owns y,\n  regex z;", "unrecognised schema line"),
    ("entity x,\n  owns y @weird(;", "unrecognised"),
    ("entity x,\n  owns y,", "not terminated"),
    ("entity x,\n  relates y;", "not expected on an entity"),
    ("entity x,\n owns y;", "indentation"),
    ("entity x;\nentity x;", "two statements"),
    ("entity x;\nsomething else;", "unrecognised schema line"),
    ("entity x;\nfun f() -> { x }\n  return { $x };", "function signature"),
    ("attribute a,\n value string @values(\"a\", \"b\") trailing;", "annotation"),
])
def test_parser_refuses_text_it_cannot_account_for(bad, why):
    with pytest.raises(SchemaParseError, match=why):
        parse_schema("define\n\n" + bad)


def test_parser_refuses_a_missing_define_and_accepts_an_empty_schema(driver):
    with pytest.raises(SchemaParseError, match="define"):
        parse_schema("entity x;")
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    driver.databases.create(name)
    try:
        text = driver.databases.get(name).schema()
        parsed = parse_schema(text)
        assert parsed.types == {} and parsed.functions == {} and render_schema(parsed) == text
    finally:
        driver.databases.get(name).delete()


def test_snapshot_reads_without_writing(reference):
    wm, snap = reference
    again = snapshot(wm.driver, wm.database)
    assert again.text == snap.text and again.modules == snap.modules
    with pytest.raises(SchemaExportError, match="does not exist"):
        snapshot(wm.driver, "wm-test-no-such-database")


# ---- increment 2: independent query cross-check and round trip ------------------------------------------------------
def test_cross_check_agrees_exactly_with_the_database(reference):
    _, snap = reference
    counts = cross_check(Lattice(parse_schema(snap.text)), snap.answers)
    assert counts["kinds"] == len(snap.answers["kinds"]) and counts["role_parents"] == 5


def test_cross_check_on_a_core_only_database(driver):
    wm = make_db(driver, modules=DEFAULT_MODULES, profiles=())
    try:
        snap = snapshot(driver, wm.database)
        cross_check(Lattice(parse_schema(snap.text)), snap.answers)
        assert set(snap.modules) == set(DEFAULT_MODULES)
    finally:
        drop(wm)


def test_inherited_capabilities_name_their_declaring_type(reference):
    _, snap = reference
    lattice = Lattice(parse_schema(snap.text))
    owns = {a: frm for a, frm, _ in lattice.capabilities("sample", "owns")}
    assert owns["wm-id"] == "particular"
    plays = {r: frm for r, frm, _ in lattice.capabilities("sample", "plays")}
    assert plays["sampling:product"] == "sample" and plays["sampling:sampled"] == "physical-object"
    assert plays["sampling:sampler"] == "particular"                   # laboratory extends the core `particular`
    relates = {r: frm for r, frm, _ in lattice.capabilities("sampling", "relates")}
    assert relates["sampling:sampler"] == "sampling" and relates["event:actor"] == "event"
    assert lattice.chain("sample") == ["physical-object", "particular"]
    assert lattice.value_type("valid-from-earliest") == ("datetime-tz", "time-point")


@pytest.mark.parametrize("change, expected", [
    (lambda p: edit_type(p, "sample", declarations=[d for d in p.types["sample"].declarations
                                                    if d.keyword != "plays"]), "plays ('sample', 'sampling:product')"),
    (lambda p: edit_type(p, "person", declarations=[d for d in p.types["person"].declarations
                                                    if d.keyword != "sub"]), "sub ('person', 'physical-object')"),
    (lambda p: edit_type(p, "credence", declarations=[dataclasses.replace(d, target="string")
                                                      for d in p.types["credence"].declarations]), "value_types credence"),
])
def test_cross_check_fails_on_any_mismatch(reference, change, expected):
    _, snap = reference
    with pytest.raises(SchemaExportError, match="disagree") as e:
        cross_check(Lattice(change(parse_schema(snap.text))), snap.answers)
    assert any(expected in p for p in e.value.problems)


def test_compare_reports_both_directions():
    a = {"kinds": {"x": "entity"}, "sub": set(), "owns": {("x", "n")}, "plays": set(), "relates": set(),
         "role_parents": set(), "value_types": {}}
    b = {**a, "owns": {("x", "m")}}
    assert compare_answers(a, b) == ["owns ('x', 'n'): in the schema text only", "owns ('x', 'm'): in the query answers only"]


def test_round_trip_is_exact(reference, driver):
    _, snap = reference
    result = round_trip(driver, parse_schema(snap.text), snap.text, prefix=TMP)
    assert result == {"identical_schema_text": True, "characters": len(snap.text)}
    assert leftovers(driver) == []


def test_round_trip_fails_on_a_missing_annotation_or_function(reference, driver):
    _, snap = reference
    parsed = parse_schema(snap.text)
    keyless = [dataclasses.replace(d, annotations=()) if d.keyword == "owns" else d
               for d in parsed.types["schema-module"].declarations]
    with pytest.raises(SchemaExportError, match="round trip"):
        round_trip(driver, edit_type(parsed, "schema-module", declarations=keyless), snap.text, prefix=TMP)
    with pytest.raises(SchemaExportError, match="round trip"):
        round_trip(driver, edit_type(parsed, "particular", annotations=()), snap.text, prefix=TMP)
    no_fun = dataclasses.replace(parsed, functions={k: v for k, v in parsed.functions.items() if k != "parts_in"})
    with pytest.raises(SchemaExportError, match="round trip"):
        round_trip(driver, no_fun, snap.text, prefix=TMP)
    assert leftovers(driver) == []


# ---- increment 3: module replay and contribution-level attribution --------------------------------------------------
@pytest.fixture(scope="module")
def attributed(reference):
    wm, snap = reference
    f = facts(parse_schema(snap.text))
    return f, attribute(wm.driver, snap, f, prefix=TMP)


def run(wm, kind, query):
    with wm.driver.transaction(wm.database, kind) as tx:
        tx.query(query).resolve()
        tx.commit()


def statuses(a):
    return {v["status"] for v in a.facts.values()}


def test_complete_replay_verifies_every_fact(attributed, driver):
    f, a = attributed
    assert a.verified and a.problems == [] and a.data_verified and a.data_problems == []
    assert set(a.facts) == set(f) and statuses(a) == {"attributed"}
    assert all(len(v["modules"]) == 1 for v in a.facts.values())
    assert [r["name"] for r in a.modules][-1] == SETUP
    assert all(r["replay"] == "replayable" and r["recorded_version"] == r["code_version"]
               for r in a.modules if r["kind"] != "setup")
    assert leftovers(driver) == []


def test_attribution_per_declaration_on_extended_core_types(attributed):
    _, a = attributed
    mods = {k: v["modules"] for k, v in a.facts.items()}
    assert mods["entity particular"] == ["core"]
    assert mods["particular plays sampling:sampler"] == ["profile:laboratory"]      # a profile extends a core type
    assert mods["physical-object plays calibration-of:calibrated"] == ["profile:laboratory"]
    assert mods["sampling relates sampler"] == mods["sampling relates sampler as actor"] == ["profile:laboratory"]
    assert mods["particular owns wm-id @key"] == ["core"]
    assert mods["proposition owns wm-id"] == mods["proposition owns wm-id @key"] == ["core-0.4-a0"]
    assert mods["fun parts_in"] == ["core"] and mods["fun frames_linked"] == ["core-0.4-a2"]


def test_a_repeated_declaration_is_a_repository_note_not_ownership(attributed):
    _, a = attributed
    # core-0.4-d's source repeats `relation depends-on`, which core-0.3 declares: the replay cannot see a repeat
    assert a.facts["relation depends-on"] == {"status": "attributed", "modules": ["core"],
                                              "also_declared_in_source": ["core-0.4-d"]}
    assert all(v["unread"] == [] and v["missing_from_scan"] == [] for v in a.source.values())


def test_module_data_is_attributed_by_replay(attributed):
    _, a = attributed
    by_id = {rec[2] if rec[0] == "concept" else rec[1]: d for rec, d in a.data.items()}
    assert by_id["laboratory:specimen"] == {"modules": ["profile:laboratory"], "in_database": True, "status": "attributed"}
    assert by_id["dependency:physical"]["modules"] == ["core-0.4-d"]
    assert by_id["located-at|located|place"]["modules"] == [SETUP]     # declared by WorldModel.create, not a module


def test_install_order_does_not_change_attribution(driver, attributed):
    _, a = attributed
    wm = make_db(driver, profiles=("organisation", "laboratory", "mechanical"))
    try:
        snap = snapshot(driver, wm.database)
        b = attribute(driver, snap, facts(parse_schema(snap.text)), prefix=TMP)
        assert b.verified and b.facts == a.facts
    finally:
        drop(wm)


def test_classify():
    assert classify(True, ["a"]) == "attributed" and classify(True, ["a", "b"]) == "shared"
    assert classify(True, []) == classify(False, []) == "unresolved"
    assert classify(False, ["a"]) == classify(False, ["a", "b"]) == "consistent_unverified"


def test_a_version_mismatch_proves_nothing(driver):
    wm = make_db(driver, profiles=("laboratory",))
    try:
        run(wm, WRITE, """match $m isa schema-module, has module-name "profile:laboratory", has module-version $v;
                         delete has $v of $m;""")
        run(wm, WRITE, """match $m isa schema-module, has module-name "profile:laboratory";
                         insert $m has module-version "0.0-old";""")
        snap = snapshot(driver, wm.database)
        a = attribute(driver, snap, facts(parse_schema(snap.text)), prefix=TMP)
        assert not a.verified and any("0.0-old" in p for p in a.problems)
        assert statuses(a) == {"consistent_unverified", "unresolved"}
        assert a.facts["entity particular"] == {"status": "consistent_unverified", "modules": ["core"]}
        assert a.facts["relation sampling"] == {"status": "unresolved", "modules": []}    # not replayed
        assert {r["name"]: r["replay"] for r in a.modules}["profile:laboratory"] == "version-mismatch"
        assert leftovers(driver) == []
    finally:
        drop(wm)


def test_an_unknown_module_proves_nothing(driver):
    wm = make_db(driver, profiles=("laboratory",))
    try:
        run(wm, WRITE, 'insert $m isa schema-module, has module-name "profile:ghost", has module-version "1";')
        snap = snapshot(driver, wm.database)
        a = attribute(driver, snap, facts(parse_schema(snap.text)), prefix=TMP)
        assert not a.verified and any("ghost" in p and "unknown" in p for p in a.problems)
        assert a.facts["relation sampling"] == {"status": "consistent_unverified", "modules": ["profile:laboratory"]}
        assert "attributed" not in statuses(a) and "shared" not in statuses(a)
    finally:
        drop(wm)


def test_schema_defined_outside_any_module_is_unresolved(driver):
    wm = make_db(driver, profiles=("laboratory",))
    try:
        run(wm, SCHEMA, "define entity gadget sub physical-object; attribute serial, value string; gadget owns serial;")
        snap = snapshot(driver, wm.database)
        a = attribute(driver, snap, facts(parse_schema(snap.text)), prefix=TMP)
        assert not a.verified
        assert "in the database but not in the replay: entity gadget" in a.problems
        for fid in ("entity gadget", "gadget sub physical-object", "gadget owns serial", "serial value string"):
            assert a.facts[fid] == {"status": "unresolved", "modules": []}
        assert a.facts["sampling relates sampler"]["status"] == "consistent_unverified"
    finally:
        drop(wm)


def test_missing_module_data_fails_only_the_data_verification(driver):
    wm = make_db(driver, profiles=("laboratory",))
    try:
        run(wm, WRITE, 'match $c isa category, has wm-id "laboratory:experiment"; delete $c;')
        snap = snapshot(driver, wm.database)
        a = attribute(driver, snap, facts(parse_schema(snap.text)), prefix=TMP)
        assert a.verified and not a.data_verified
        by_id = {rec[2]: d for rec, d in a.data.items() if rec[0] == "concept"}
        assert by_id["laboratory:experiment"]["status"] == "unresolved" and not by_id["laboratory:experiment"]["in_database"]
        assert by_id["laboratory:specimen"]["status"] == "consistent_unverified"
    finally:
        drop(wm)


def two_profiles(tmp_path):
    files = {"alpha": "define entity widget sub physical-object; entity alpha-thing sub physical-object;",
             "beta": "define entity widget sub physical-object; entity beta-thing sub physical-object;"}
    out = {}
    for name, text in files.items():
        (tmp_path / f"{name}.tql").write_text(text)
        out[name] = Profile(name, "1", (str(tmp_path / f"{name}.tql"),))
    return {**PROFILES, **out}


def test_two_profiles_declaring_the_same_type(driver, tmp_path, monkeypatch):
    """Profile rules (D-D-1) refuse a profile that redeclares another's type, so `shared` needs the rule relaxed: then
    both profiles, each replayed on its own, add `entity widget`, and the complete replay matches: proven sharing."""
    import worldmodel.profiles as wp
    profiles = two_profiles(tmp_path)
    in_force = wp._violations
    relaxed = lambda profile, declared, before, after: (after["types"] - before["types"], [])
    monkeypatch.setattr(wp, "_violations", relaxed)
    wm = make_db(driver, profiles=())
    try:
        wm.install_profile(profiles["alpha"])
        wm.install_profile(profiles["beta"])
        snap = snapshot(driver, wm.database)
        f = facts(parse_schema(snap.text))
        a = attribute(driver, snap, f, profiles=profiles, prefix=TMP)
        assert a.verified
        assert a.facts["entity widget"] == {"status": "shared", "modules": ["profile:alpha", "profile:beta"]}
        assert a.facts["widget sub physical-object"]["status"] == "shared"
        assert a.facts["entity alpha-thing"] == {"status": "attributed", "modules": ["profile:alpha"]}
        # with the rule in force, the complete replay refuses beta: the same evidence is no longer proof
        monkeypatch.setattr(wp, "_violations", in_force)
        b = attribute(driver, snap, f, profiles=profiles, prefix=TMP)
        assert not b.verified and any("complete replay failed" in p for p in b.problems)
        assert b.facts["entity widget"] == {"status": "consistent_unverified", "modules": ["profile:alpha", "profile:beta"]}
        assert leftovers(driver) == []
    finally:
        drop(wm)


# ---- increment 4: versioned JSON export and JSON Schema validation --------------------------------------------------
@pytest.fixture(scope="module")
def exported(reference):
    wm, snap = reference
    doc, text, attr, _ = ex.build_export(wm.driver, wm.database, prefix=TMP)
    return doc, text, snap


def test_export_validates_against_its_json_schema(exported):
    doc, _, _ = exported
    assert validate(doc) == []
    assert doc["format"] == "wm-schema-export/1"


def test_every_section_states_its_source(exported):
    doc, _, _ = exported
    assert doc["source"]["provenance"] == doc["verification"]["provenance"] == doc["schema"]["provenance"] == "database"
    assert doc["attribution"]["provenance"] == "reconstructed"
    assert doc["attribution"]["repository_notes"]["provenance"] == "repository"
    assert set(doc["provenance"]) == {"database", "reconstructed", "repository"}
    assert set(doc["schema"]["single_source"]) == {"annotations", "functions"}       # their limitation is stated


@pytest.mark.parametrize("mutate, expected", [
    (lambda d: d["schema"].update(provenance="repository"), "$.schema.provenance: must be 'database'"),
    (lambda d: d["attribution"].update(provenance="database"), "$.attribution.provenance: must be 'reconstructed'"),
    (lambda d: d["attribution"].pop("repository_notes"), "$.attribution: missing 'repository_notes'"),
    (lambda d: d["attribution"]["facts"]["entity sample"].update(status="probable"),
     "$.attribution.facts.entity sample.status: 'probable' is not one of"),
    (lambda d: d["attribution"]["facts"]["entity sample"].pop("status"), "$.attribution.facts.entity sample: missing 'status'"),
    (lambda d: d["schema"]["types"]["sample"].update(owner="profile:laboratory"), "$.schema.types.sample: unexpected 'owner'"),
    (lambda d: d["verification"]["round_trip"].update(passed=False), "$.verification.round_trip.passed: must be True"),
    (lambda d: d.update(format="wm-schema-export/2"), "$.format: must be 'wm-schema-export/1'"),
])
def test_json_schema_rejects_an_unlabelled_or_unknown_export(exported, mutate, expected):
    doc = copy.deepcopy(exported[0])
    mutate(doc)
    assert any(e.startswith(expected) for e in validate(doc)), validate(doc)[:5]


def test_the_checker_refuses_keywords_it_does_not_support():
    assert errors(1, {"type": "integer", "multipleOf": 2}) == ["$: the checker does not support ['multipleOf']"]
    assert errors([1, "x"], {"type": "array", "items": {"type": "integer"}}) == ["$[1]: expected integer, found str"]
    assert errors(True, {"type": "integer"}) == ["$: expected integer, found bool"]
    assert format_schema()["title"] == "wm-schema-export/1"


def test_schema_section_equals_the_database(exported):
    doc, text, snap = exported
    s = doc["schema"]
    a = snap.answers
    assert s["typeql"] == text == snap.text
    assert {k: t["kind"] for k, t in s["types"].items()} == a["kinds"]
    assert {(k, t["supertype"]) for k, t in s["types"].items() if t["supertype"]} == a["sub"]
    assert {(k, o["attribute"]) for k, t in s["types"].items() for o in t["owns"]} == a["owns"]
    assert {(k, p["role"]) for k, t in s["types"].items() for p in t["plays"]} == a["plays"]
    assert {(k, r["role"]) for k, t in s["types"].items() for r in t["relates"]} == a["relates"]
    assert {(r, x["specialises"]) for r, x in s["roles"].items() if x["specialises"]} == a["role_parents"]
    assert {k: [t["value_type"]["type"]] for k, t in s["types"].items() if t["value_type"]} == a["value_types"]
    assert set(s["facts"]) == set(facts(parse_schema(text)))
    assert "".join(t["statement"] for t in s["types"].values()).count("@") == text.split("\nfun ")[0].count("@")


def test_inherited_capabilities_and_contributions(exported):
    doc, _, _ = exported
    sample = doc["schema"]["types"]["sample"]
    wm_id = next(o for o in sample["owns"] if o["attribute"] == "wm-id")
    assert wm_id == {"attribute": "wm-id", "annotations": ["@key"], "from": "particular", "declared": False}
    assert next(p for p in sample["plays"] if p["role"] == "sampling:product")["declared"] is True
    att = doc["attribution"]["types"]
    assert att["sample"]["introduced_by"] == {"status": "attributed", "modules": ["profile:laboratory"]}
    assert att["sample"]["extended_by"] == []
    assert att["particular"]["introduced_by"]["modules"] == ["core"]
    assert "profile:laboratory" in att["particular"]["extended_by"]                 # extended, never owned by it
    assert att["particular"]["contributions"]["profile:laboratory"] == ["particular plays sampling:sampler"]
    role = doc["schema"]["roles"]["event:actor"]
    assert "sampling:sampler" in role["specialised_by"] and "sample" in role["played_by"]
    assert doc["attribution"]["functions"]["frames_linked"]["modules"] == ["core-0.4-a2"]
    assert doc["schema"]["functions"]["parts_in"]["types_named"] == ["attestation", "part-of", "particular", "world"]


def test_two_exports_of_one_schema_differ_only_in_volatile_fields(exported, reference):
    doc, _, _ = exported
    wm, _ = reference
    again, _, _, _ = ex.build_export(wm.driver, wm.database, prefix=TMP)
    assert ex.masked(again) == ex.masked(doc)


def test_write_export_and_manifest(exported, tmp_path):
    doc, text, _ = exported
    written = ex.write_export(doc, text, tmp_path)
    assert written == ["manifest.json", "schema.json", "schema.tql"]
    assert (tmp_path / "schema.tql").read_text() == text
    assert json.loads((tmp_path / "schema.json").read_text()) == doc
    m = json.loads((tmp_path / "manifest.json").read_text())
    for name in ("schema.json", "schema.tql"):
        assert m["files"][name]["sha256"] == hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
    assert m["replay_verification"] == "verified" and m["unresolved"] == [] and m["replay_problems"] == []
    assert m["schema_sha256"] == hashlib.sha256(text.encode()).hexdigest()


def test_manifest_lists_unresolved_contributions(driver, tmp_path):
    wm = make_db(driver, profiles=("laboratory",))
    try:
        run(wm, SCHEMA, "define entity gadget sub physical-object;")
        doc, written, _ = ex.export_to(driver, wm.database, tmp_path, prefix=TMP)
        m = json.loads((tmp_path / "manifest.json").read_text())
        assert m["replay_verification"] == "failed"
        assert m["unresolved"] == ["entity gadget", "gadget sub physical-object"]
        assert m["attribution_counts"]["attributed"] == 0 and m["attribution_counts"]["shared"] == 0
        assert validate(doc) == []
    finally:
        drop(wm)


def test_the_export_is_refused_when_the_queries_disagree(reference, monkeypatch, tmp_path):
    wm, snap = reference
    tampered = dataclasses.replace(snap, answers={**snap.answers, "plays": snap.answers["plays"] - {("sample", "sampling:product")}})
    monkeypatch.setattr(ex, "snapshot", lambda driver, database: tampered)
    with pytest.raises(SchemaExportError, match="disagree"):
        ex.export_to(wm.driver, wm.database, tmp_path / "out", prefix=TMP)
    assert not (tmp_path / "out").exists()


def test_the_command_line(reference, tmp_path, capsys):
    import importlib.util
    spec = importlib.util.spec_from_file_location("export_schema", conftest.__file__.replace("tests/conftest.py", "scripts/export_schema.py"))
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    wm, _ = reference
    assert cli.main([wm.database, "--out", str(tmp_path), "--require-verified"]) == 0
    assert "attribution: verified" in capsys.readouterr().out
    assert sorted(p.name for p in tmp_path.iterdir()) == ["manifest.json", "schema.json", "schema.tql"]
    assert cli.main(["wm-test-no-such-database", "--out", str(tmp_path / "x")]) == 1


# ---- increment 5: repository documentation and module data -----------------------------------------------------------
def test_documentation_is_repository_evidence_with_its_location(exported):
    doc, _, _ = exported
    d = doc["documentation"]
    assert d["provenance"] == "repository" and d["unknown_labels"] == []
    sample = d["types"]["sample"][0]
    assert sample["module"] == "profile:laboratory" and sample["file"] == "schema/profiles/laboratory/laboratory-0.1.tql"
    assert sample["line"] == 8 and sample["comment"].startswith("a sample: a sortal whose identity is its portion")
    assert sample["declares"] == ["entity sample", "sample sub physical-object"]
    alt = d["types"]["alt-name"][0]                                     # a comment after the statement, on its line
    assert alt["comment"] == "`alias` is reserved in TypeQL" and alt["module"] == "core"
    assert d["functions"]["parts_in"][0]["comment"].startswith("database-side reasoning")
    assert d["modules"]["profile:laboratory"]["header"].startswith("Profile laboratory-0.1")
    assert set(d["undocumented"]) <= set(doc["schema"]["types"])


def test_repository_comments_never_enter_database_or_reconstructed_sections(exported):
    doc, _, _ = exported
    phrase = "portion of matter"
    assert phrase in json.dumps(doc["documentation"])
    for section in ("source", "verification", "schema", "attribution", "module_data"):
        assert phrase not in json.dumps(doc[section]), section


def test_module_data_records_and_their_attribution(exported):
    doc, _, _ = exported
    md = doc["module_data"]
    assert md["provenance"] == "database" and md["attribution_provenance"] == "reconstructed"
    assert md["verification"] == "verified" and md["unresolved"] == [] and md["problems"] == []
    rows = {r["id"]: r for r in md["records"]}
    assert rows["laboratory:specimen"] == {"kind": "concept", "type": "category", "id": "laboratory:specimen",
                                           "name": "specimen", "source": "database",
                                           "attribution": {"status": "attributed", "modules": ["profile:laboratory"]}}
    assert rows["located-at|located|place"]["attribution"]["modules"] == [SETUP]
    assert rows["anchored-to|frame|anchor"]["key_roles"] == ["frame"]
    assert all(r["source"] == "database" for r in md["records"])


def test_missing_module_data_is_listed_as_reconstructed(driver, tmp_path):
    wm = make_db(driver, profiles=("laboratory",))
    try:
        run(wm, WRITE, 'match $c isa category, has wm-id "laboratory:calibration"; delete $c;')
        doc, _, _ = ex.export_to(driver, wm.database, tmp_path, prefix=TMP)
        rows = {r["id"]: r for r in doc["module_data"]["records"]}
        assert rows["laboratory:calibration"]["source"] == "reconstructed"
        assert rows["laboratory:calibration"]["attribution"]["status"] == "unresolved"
        assert doc["module_data"]["verification"] == "failed"
        assert doc["attribution"]["verification"] == "verified"         # the schema attribution is unaffected
        m = json.loads((tmp_path / "manifest.json").read_text())
        assert m["module_data_verification"] == "failed" and m["module_data_unresolved"] == ["laboratory:calibration"]
        assert validate(doc) == []
    finally:
        drop(wm)


def test_code_that_drifted_from_the_database(driver, tmp_path):
    """The profile's file changed after installation, at the same version: the replay no longer matches (nothing is
    proven), and the comment on the type the database lacks is reported, not dropped."""
    (tmp_path / "gamma.tql").write_text("define\n# a widget\nentity widget sub physical-object;\n")
    profiles = {**PROFILES, "gamma": Profile("gamma", "1", (str(tmp_path / "gamma.tql"),))}
    wm = make_db(driver, profiles=())
    try:
        wm.install_profile(profiles["gamma"])
        (tmp_path / "gamma.tql").write_text("define\n# a widget\nentity widget sub physical-object;\n"
                                            "# added later\nentity sprocket sub physical-object;\n")
        doc, _, _, _ = ex.build_export(driver, wm.database, profiles=profiles, prefix=TMP)
        a = doc["attribution"]
        assert a["verification"] == "failed"
        assert "in the replay but not in the database: entity sprocket" in a["problems"]
        assert a["facts"]["entity widget"] == {"status": "consistent_unverified", "modules": ["profile:gamma"]}
        d = doc["documentation"]
        assert d["types"]["widget"][0]["comment"] == "a widget"
        assert d["unknown_labels"] == [{"label": "sprocket", "module": "profile:gamma", "file": "gamma.tql", "line": 5}]
        assert validate(doc) == []
    finally:
        drop(wm)
