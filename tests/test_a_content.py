"""Stage A: foundational schema and the proposition model (World Ontology v0.2 §3-4), against TypeDB 3.14.1."""

import pytest
from typedb.driver import TypeDBDriverException

from worldmodel import SYSTEM, proposition_key
from worldmodel import typeql as q
from worldmodel.model import WRITE


def test_schema_installed_and_system_agent_registered(wm):
    assert wm.modules() == {"core": "0.3.0", "core-0.4-a0": "0.4.0-a0"}      # Core 0.3 plus the additive A0 module (LABS-1.002)
    assert {"existence", "located-at", "part-of", "member-of", "depends-on", "classified-as", "has-quality",
            "same-as", "describes", "initiates", "terminates"} == wm.proposition_types()
    assert wm.find("system reasoner") == [SYSTEM]


def test_canonical_keys_ignore_order_and_sort_multi_player_roles():
    a = proposition_key("located-at", {"place": "shelf-3", "located": "box-17"})
    b = proposition_key("located-at", {"located": "box-17", "place": "shelf-3"})
    assert a == b == "located-at|located=box-17|place=shelf-3"
    assert proposition_key("same-as", {"same": ["b", "a"]}) == proposition_key("same-as", {"same": ["a", "b"]})
    assert proposition_key("has-quality", {"bearer": "r"}, {"lower": 3.5, "upper": 3.50000000000001}) == \
        proposition_key("has-quality", {"bearer": "r"}, {"lower": 3.5, "upper": 3.5})
    with pytest.raises(ValueError):
        proposition_key("located-at", {"located": "box|17", "place": "s"})      # delimiter in an id


def test_proposition_is_stored_once(wm):
    wm.add_entity("physical-object", "box-17", id="box-17")
    wm.add_entity("place", "shelf-3", id="shelf-3")
    k1 = wm.proposition("located-at", {"located": "box-17", "place": "shelf-3"})
    k2 = wm.proposition("located-at", {"place": "shelf-3", "located": "box-17"})
    assert k1 == k2 and wm.count("located-at") == 1
    assert wm.content(k1) == {"type": "located-at", "roles": {"located": ["box-17"], "place": ["shelf-3"]},
                              "params": {}}


def test_typedb_rejects_a_duplicate_key_written_directly(wm):
    wm.add_entity("physical-object", "b", id="b")
    wm.add_entity("place", "p", id="p")
    wm.proposition("located-at", {"located": "b", "place": "p"})
    with pytest.raises(TypeDBDriverException):
        with wm.driver.transaction(wm.database, WRITE) as tx:
            q.run(tx, """match $b isa physical-object, has wm-id "b"; $p isa place, has wm-id "p";
                insert located-at (located: $b, place: $p), has proposition-key "located-at|located=b|place=p";""")
            tx.commit()


def test_parameters_are_part_of_content(wm):
    wm.add_entity("physical-object", "rock", id="rock")
    wm.add_entity("quality-kind", "mass", id="mass")
    wm.add_entity("unit", "kilogram", id="kg")
    a = wm.proposition("has-quality", {"bearer": "rock", "quality": "mass", "unit": "kg"},
                       {"lower": 3.47, "upper": 3.55, "coverage-level": 0.95})
    b = wm.proposition("has-quality", {"bearer": "rock", "quality": "mass", "unit": "kg"},
                       {"lower": 3.45, "upper": 3.53, "coverage-level": 0.95})
    assert a != b and wm.count("has-quality") == 2
    assert wm.content(a)["params"] == {"lower": 3.47, "upper": 3.55, "coverage-level": 0.95}


def test_event_descriptions_are_identified_not_keyed(wm):
    wm.add_entity("physical-object", "bob", id="bob")
    wm.add_entity("physical-object", "box", id="box")
    e1 = wm.describe_event({"actor": "bob", "patient": "box"})
    e2 = wm.describe_event({"actor": "bob", "patient": "box"})
    assert e1 != e2 and wm.count("event") == 2                    # two accounts, even with identical participants
    assert wm.content(e1)["roles"] == {"actor": ["bob"], "patient": ["box"]}


def test_typedb_enforces_kinds_and_roles(wm):
    wm.add_entity("category", "justice", id="justice")
    wm.add_entity("place", "p", id="p")
    with pytest.raises(TypeDBDriverException):
        wm.proposition("located-at", {"located": "justice", "place": "p"})         # a concept cannot be located
    wm.add_entity("physical-object", "a", id="dup")
    with pytest.raises(TypeDBDriverException):
        wm.add_entity("place", "b", id="dup")                                      # ids are unique
    with pytest.raises(TypeDBDriverException):
        wm.create_world("w", kind="dream")                                         # allowed values
    with pytest.raises(ValueError):
        wm.proposition("teleported-to", {"a": "dup"})                               # unknown content type
    with pytest.raises(ValueError):
        wm.proposition("located-at", {"located": "nobody", "place": "p"})           # unknown player


def test_find_returns_every_match(wm):
    wm.add_entity("physical-object", "Sam", id="sam-1")
    wm.add_entity("physical-object", "Samantha", alt_names=("Sam",), id="sam-2")
    assert wm.find("Sam") == ["sam-1", "sam-2"]
