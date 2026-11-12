"""Schema export (LABS-1.024, approved under LABS-1.032 and LABS-1.033): fidelity of the exported schema.

Increments 1 and 2: the canonical schema text is parsed with every character accounted for, and the parse is checked
two independent ways (TypeDB's query answers, and an exact round trip into an empty database). Every mismatch fails.
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
from worldmodel.schema_export.introspect import snapshot

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
