"""Schema export (LABS-1.024, approved under LABS-1.032 and LABS-1.033): fidelity of the exported schema.

Increment 1: the canonical schema text is parsed with every character accounted for.
"""

import uuid

import pytest

import conftest
from conftest import FakeClock
from worldmodel import CORE_MODULES, WorldModel
from worldmodel.model import DEFAULT_MODULES
from worldmodel.schema_export import SchemaExportError, SchemaParseError, facts, parse_schema, render_schema
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
