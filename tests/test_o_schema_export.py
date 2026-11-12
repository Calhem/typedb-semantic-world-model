"""Schema export (LABS-1.024, approved under LABS-1.032 and LABS-1.033): fidelity of the exported schema.

Increments 1 and 2: the canonical schema text is parsed with every character accounted for, and the parse is checked
two independent ways (TypeDB's query answers, and an exact round trip into an empty database). Every mismatch fails.
Increment 3: attribution of every fact to modules by verified replay, and the four statuses.
"""

import dataclasses
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
from worldmodel.schema_export.introspect import snapshot
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
