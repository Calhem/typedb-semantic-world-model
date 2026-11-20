"""DI-13 multiplicity increment (LABS-1.049): several participants in one role of one account.

Approved design: docs/core-0.4/pre-e-multiplicity-design.md, MP-2 to MP-5, with MP-1 restricted by LABS-1.048 to
actor, patient, official, sampler, removed and fitted (destination, product, instrument, location and origin stay
single-valued). Permanent tests, read through the library's own `occurrence()` on both query paths:
- the design's cases M1 to M12 (section 5; prototype probes/pre_e_di13_rule.py);
- co-participation is not conflict, and conflicting accounts never become valid because a role is open (MP-2);
- declarations: multiplicity stored and read, the kind-scoped one winning, conflicting ones refused (MP-3, MP-4);
- the roles that stay single refuse a second player with a domain-level error, nothing written;
- provenance (one source, one description, one attestation) and office exclusivity are unchanged;
- the explicit upgrade of an existing database: idempotent, atomic, one-way once used, answers kept (MP-5);
- move(): never several origins or destinations; a domain-level refusal; atomic (the LABS-1.047 probe, case 2).
"""

import uuid
from datetime import datetime, timezone

import pytest

from conftest import FakeClock
from worldmodel import (CORE_MODULES, MovementConflict, ProfileError, RoleCardinalityError, WorldModel,
                        laboratory as lb, mechanical as mech, organisation as org)
from worldmodel.mechanical import ONE_FOR_ONE
from worldmodel.model import MULTIPLICITY_MODULE, SCHEMA
from worldmodel.organisation import CO_SIGNED
from worldmodel.profiles import EventRole
from worldmodel.semantics import Status

pytestmark = pytest.mark.own_profiles


def T(day, h=9):
    return datetime(2026, 11, day, h, tzinfo=timezone.utc)


def accept_account(wm, world, event, holder="system"):
    for a in wm.account_attestations(world, event):
        wm.accept(a, holder=holder)


def new_db(driver, modules=CORE_MODULES):
    name = f"wm-test-{uuid.uuid4().hex[:10]}"
    return WorldModel.create(name, driver=driver, modules=modules, clock=FakeClock())


def drop(wm):
    if wm.driver.databases.contains(wm.database):
        wm.driver.databases.get(wm.database).delete()


def people(wm):
    for p in ("bea", "cal", "dee", "b-smith", "dan", "eve", "fay", "hr", "clerk", "cmms", "lab"):
        wm.add_entity("person", p, id=p)
    for i in ("housing", "b1", "b2", "b3", "b4", "core-1", "core-2", "thing", "pump"):
        wm.add_entity("physical-object", i, id=i)
    for pl in ("depot", "p1", "p2", "p3"):
        wm.add_entity("place", pl, id=pl)
    wm.add_entity("organisation", "acme", id="acme")
    wm.add_entity("social-role", "site-manager", id="site-manager")


@pytest.fixture(scope="module")
def ref(driver):
    wm = new_db(driver)
    try:
        for p in ("mechanical", "organisation", "laboratory"):
            wm.install_profile(p)
        w = wm.create_world("actual", id="w")
        people(wm)
        occs = ("o-m1", "o-m2", "o-m3", "o-m4", "o-m5", "o-m6", "o-m7", "o-m8", "o-m9", "o-m10", "o-m11", "o-m12")
        for o in occs:
            wm.add_entity("occurrence", o, id=o)
        ids = {}

        def act(occ, officials, attester, kind=None):
            e = org.act_in_office(wm, w, officials, "site-manager", "acme", T(5), occurrence=occ, attester=attester,
                                  id=f"act-{occ[2:]}-{attester}")
            accept_account(wm, w, e)
            return e

        def cosigned(occ):
            ids[f"cosigned-{occ}"] = wm.attest(w, "classified-as", {"classified": occ, "class": CO_SIGNED},
                                                start=T(5), until_superseded=True)

        # M1: a two-technician job, one account names both (event:actor, no constraint)
        ids["m1"] = wm.account(w, {"actor": ["dan", "eve"], "patient": "pump", "location": "depot"}, T(5),
                               occurrence="o-m1", attester="cmms", id="job-m1")
        accept_account(wm, w, ids["m1"])
        # M2 / M3: one account names two officials; co-signed established (M2) or not (M3)
        ids["m2"] = act("o-m2", ["bea", "cal"], "hr")
        cosigned("o-m2")
        ids["m3"] = act("o-m3", ["bea", "cal"], "hr")
        # M4: an ordinary act, two accounts, different officials (increment D, unchanged)
        act("o-m4", "bea", "hr")
        act("o-m4", "cal", "clerk")
        # M5: co-signed, two accounts naming the same two officials (in a different order)
        act("o-m5", ["bea", "cal"], "hr")
        act("o-m5", ["cal", "bea"], "clerk")
        cosigned("o-m5")
        # M6: co-signed, one account names both, another only one (never assumed merely incomplete)
        act("o-m6", ["bea", "cal"], "hr")
        act("o-m6", "bea", "clerk")
        cosigned("o-m6")
        # M7: co-signed, the accounts disagree on the second official
        act("o-m7", ["bea", "cal"], "hr")
        act("o-m7", ["bea", "dee"], "clerk")
        cosigned("o-m7")
        # M8 / M9: an ordinary act naming bea and b-smith; one thing for hr (established), not for clerk's view
        act("o-m8", ["bea", "b-smith"], "hr")
        wm.accept(wm.attest(w, "same-as", {"same": ["bea", "b-smith"]}, until_superseded=True, attester="hr"),
                  holder="hr")
        accept_account(wm, w, f"act-m8-hr", holder="hr")
        act("o-m9", ["dee", "fay"], "hr")
        # M10 / M11: a replacement removing two parts, one-for-one (M10) or not (M11)
        for occ in ("o-m10", "o-m11"):
            r = mech.replace_part(wm, w, "housing", ["b1", "b2"], ["b3", "b4"], T(5), occurrence=occ,
                                  attester="cmms", id=f"rep-{occ[2:]}")
            accept_account(wm, w, r["event"])
            ids[f"rep-{occ}"] = r
        wm.attest(w, "classified-as", {"classified": "o-m10", "class": ONE_FOR_ONE}, start=T(5),
                  until_superseded=True)
        # M12: team sampling, two accounts, three samplers
        for prod in ("s-1", "s-2"):
            wm.add_entity("sample", prod, id=prod)
        for samplers, spec, prod, src in ((["bea", "cal"], "core-1", "s-1", "lab"), ("dee", "core-1", "s-1", "hr")):
            e = lb.take_sample(wm, w, samplers, spec, prod, T(5), occurrence="o-m12", attester=src,
                               id=f"smp-{src}")["event"]
            accept_account(wm, w, e)
        yield wm, ids
    finally:
        drop(wm)


@pytest.fixture(params=[True, False], ids=["selective", "full-load"])
def m(ref, request):
    wm, ids = ref
    wm.selective = request.param
    yield wm, ids
    wm.selective = True


def entries(view, label):
    return {(c["kind"], c["multiplicity"]): c for c in view["roles"][label]["constraints"]}


def judged(view, label):
    """The one applying constraint for a role label, or None when none applies (the role is a union)."""
    applying = [c for c in view["roles"][label]["constraints"] if c["applies"]]
    assert len(applying) <= 1, applying
    return applying[0] if applying else None


def names(c):
    return [p["names"] for p in c["players"]]


# ---- M1 to M12 (design section 5) ------------------------------------------------------------------------------------
def test_m1_a_two_technician_job_is_one_account_and_a_union(m):
    wm, ids = m
    v = wm.occurrence("w", "o-m1")
    assert v["roles"]["event:actor"]["players"] == {"dan": [ids["m1"]], "eve": [ids["m1"]]}
    assert v["roles"]["event:actor"]["constraints"] == []                        # no constraint: never a dispute
    assert [a["description"] for a in v["accounts"]] == [ids["m1"]]             # one account, not two
    assert v["accounts"][0]["roles"]["event:actor"]["players"] == ["dan", "eve"]


def test_m2_a_co_signed_act_is_established_as_a_set(m):
    wm, ids = m
    v = wm.occurrence("w", "o-m2")
    c = judged(v, "official-act:official")
    assert (c["kind"], c["multiplicity"], c["judgement"], c["reason"]) == (CO_SIGNED, "set", "established", None)
    assert names(c) == [["bea"], ["cal"]] and c["status"] == Status.ASSERTED and c["support"]
    assert c["sets"] == [{"description": ids["m2"], "attesters": ["hr"], "players": ["bea", "cal"]}]
    plain = entries(v, "official-act:official")[(None, "one")]
    assert (plain["applies"], plain["judgement"]) == (False, None)
    assert plain["why"] == f"overridden by the declaration for {CO_SIGNED}, which applies to the occurrence (MP-3)"
    assert c["classification"]["support"] == [ids[f"cosigned-o-m2"]]


def test_m3_the_same_account_without_the_kind_is_disputed_several_in_one_account(m):
    wm, ids = m
    v = wm.occurrence("w", "o-m3")
    c = judged(v, "official-act:official")
    assert (c["kind"], c["multiplicity"], c["judgement"], c["status"]) == (None, "one", "disputed", Status.DISPUTED)
    assert c["reason"] == "several players in one account" and names(c) == [["bea"], ["cal"]]
    assert c["support"] == []
    cs = entries(v, "official-act:official")[(CO_SIGNED, "set")]
    assert (cs["applies"], cs["why"]) == (False, "the occurrence is not established as organisation:co-signed at its "
                                                 "start (unknown): this declaration does not apply")


def test_m4_two_accounts_naming_different_officials_stay_disputed(m):
    wm, _ = m
    c = judged(wm.occurrence("w", "o-m4"), "official-act:official")
    assert (c["multiplicity"], c["judgement"], c["reason"]) == ("one", "disputed", "accounts name different players")
    assert names(c) == [["bea"], ["cal"]]


def test_m5_two_accounts_with_the_same_set_agree(m):
    wm, _ = m
    c = judged(wm.occurrence("w", "o-m5"), "official-act:official")
    assert (c["multiplicity"], c["judgement"]) == ("set", "established")
    assert [s["players"] for s in c["sets"]] == [["bea", "cal"], ["bea", "cal"]]
    assert sorted(len(p["accounts"]) for p in c["players"]) == [2, 2]


@pytest.mark.parametrize("occ,sets", [("o-m6", [["bea"], ["bea", "cal"]]), ("o-m7", [["bea", "dee"], ["bea", "cal"]])])
def test_m6_m7_different_sets_are_disputed_each_cited(m, occ, sets):
    wm, _ = m
    c = judged(wm.occurrence("w", occ), "official-act:official")
    assert (c["multiplicity"], c["judgement"], c["status"], c["support"]) == ("set", "disputed", Status.DISPUTED, [])
    assert c["reason"] == "accounts name different sets of players"
    assert [(s["attesters"], s["players"]) for s in c["sets"]] == [(["clerk"], sets[0]), (["hr"], sets[1])]


def test_m8_m9_identity_decides_whether_two_names_are_one_player(m):
    wm, _ = m
    hr = judged(wm.occurrence("w", "o-m8", perspective="hr"), "official-act:official")
    assert (hr["judgement"], names(hr)) == ("established", [["b-smith", "bea"]])         # M8: one under identity
    system = judged(wm.occurrence("w", "o-m8"), "official-act:official")
    assert (system["judgement"], system["reason"]) == ("disputed", "several players in one account")   # no link
    c = judged(wm.occurrence("w", "o-m9"), "official-act:official")
    assert (c["judgement"], c["reason"], names(c)) == ("disputed", "several players in one account",
                                                       [["dee"], ["fay"]])               # M9


def test_m10_a_one_for_one_replacement_removing_two_parts_is_disputed(m):
    wm, ids = m
    v = wm.occurrence("w", "o-m10")
    for label in ("replacement:removed", "replacement:fitted"):
        c = judged(v, label)
        assert (c["kind"], c["multiplicity"], c["judgement"], c["reason"]) == \
            (ONE_FOR_ONE, "one", "disputed", "several players in one account")
    assert v["roles"]["replacement:removed"]["players"] == {"b1": ["rep-m10"], "b2": ["rep-m10"]}


def test_m11_a_replacement_of_another_kind_is_a_union(m):
    wm, ids = m
    v = wm.occurrence("w", "o-m11")
    for label in ("replacement:removed", "replacement:fitted"):
        assert judged(v, label) is None
        (c,) = v["roles"][label]["constraints"]
        assert c["why"] == ("the occurrence is not established as mechanical:one-for-one at its start "
                            "(unknown): the role is a union")                          # increment D's wording
    effects = ids["rep-o-m11"]["effects"]
    assert len(effects) == 4                                    # one part-of claim per part: two ended, two begun
    report = mech.replacement(wm, "w", "rep-m11", T(6))
    assert (report["removed"], report["fitted"]) == (["b1", "b2"], ["b3", "b4"])


def test_m12_team_sampling_is_a_union_of_three_samplers(m):
    wm, _ = m
    v = wm.occurrence("w", "o-m12")
    assert v["roles"]["sampling:sampler"]["players"] == {"bea": ["smp-lab"], "cal": ["smp-lab"], "dee": ["smp-hr"]}
    assert v["roles"]["sampling:sampler"]["constraints"] == []


# ---- co-participation against conflict; provenance; reports -------------------------------------------------------
def test_one_account_with_several_players_keeps_one_source_one_description_one_attestation(m):
    wm, ids = m
    events = [a for a in wm._load("w", types=["event"]).values() if a.content == ids["m2"]]
    assert [a.attester for a in events] == ["hr"]                              # one attestation of one description
    assert len(wm.account_attestations("w", ids["m2"])) == 2                  # it and its one describes link
    assert wm.content(ids["m2"])["roles"]["official"] == ["bea", "cal"]
    (acct,) = wm.occurrence("w", "o-m2")["accounts"]
    assert (acct["attesters"], acct["describes_by"], acct["account"]) == (["hr"], ["hr"], "accepted")


def test_official_act_reports_every_official_never_only_the_first(m):
    wm, ids = m
    r = org.official_act(wm, "w", ids["m2"])
    assert (r["official"], r["officials"]) == (None, ["bea", "cal"])
    assert sorted(r["by_official"]) == ["bea", "cal"]
    assert {o["office_held"]["judgement"] for o in r["by_official"].values()} == {"not established"}
    assert r["office_held"] is None                                 # no official is chosen over another
    single = org.official_act(wm, "w", "act-m4-hr")
    assert (single["official"], single["officials"]) == ("bea", ["bea"])
    assert single["office_held"] == single["by_official"]["bea"]["office_held"]


def test_a_co_signed_act_does_not_relax_office_exclusivity(driver):
    """Office exclusivity is a different content (an attested constraint on office-holding) and is untouched: two
    overlapping appointments to an exclusive office stay DISPUTED although both co-sign an act."""
    wm = new_db(driver)
    try:
        wm.install_profile("organisation")
        w = wm.create_world("actual", id="w")
        people(wm)
        wm.add_entity("occurrence", "o-x", id="o-x")
        org.declare_exclusive(wm, w, "site-manager", "acme", start=T(1))
        for who in ("bea", "cal"):
            org.appoint(wm, w, who, "site-manager", "acme", start=T(1))
        e = org.act_in_office(wm, w, ["bea", "cal"], "site-manager", "acme", T(5), occurrence="o-x", id="act-x")
        wm.attest(w, "classified-as", {"classified": "o-x", "class": CO_SIGNED}, start=T(5), until_superseded=True)
        assert judged(wm.occurrence("w", "o-x"), "official-act:official")["judgement"] == "established"
        holders = org.office_holders(wm, w, "site-manager", "acme", T(5))
        assert holders["conflict"] is not None
        r = org.official_act(wm, w, e)
        assert {o: x["office_held"]["status"] for o, x in r["by_official"].items()} == \
            {"bea": Status.DISPUTED, "cal": Status.DISPUTED}
    finally:
        drop(wm)


# ---- roles that stay single (LABS-1.048) ----------------------------------------------------------------------------
@pytest.mark.parametrize("type,roles,role", [
    ("event", {"patient": "thing", "origin": ["p1", "p2"]}, "event:origin"),
    ("event", {"patient": "thing", "destination": ["p1", "p2"]}, "event:destination"),
    ("event", {"actor": "dan", "location": ["p1", "p2"]}, "event:location"),
    ("event", {"actor": "dan", "instrument": ["b1", "b2"]}, "event:instrument"),
    ("official-act", {"official": "bea", "office": "site-manager", "office-context": ["acme", "depot"]},
     "official-act:office-context"),
    # a specialised role: TypeDB names either it or the core role it specialises (not always the same one)
    ("sampling", {"sampler": "bea", "sampled": "core-1", "product": ["s-1", "s-2"]},
     ("sampling:product", "event:destination")),
    ("sampling", {"sampler": "bea", "sampled": ["core-1", "core-2"], "product": "s-1"},
     ("sampling:sampled", "event:origin")),
])
def test_single_valued_roles_refuse_a_second_player_and_write_nothing(ref, type, roles, role):
    wm, _ = ref
    before = (wm.count("event"), wm.count("attestation"))
    with pytest.raises(RoleCardinalityError) as e:
        wm.account("w", roles, T(7), type=type)
    assert e.value.role in ((role,) if isinstance(role, str) else role)
    assert (e.value.limit, e.value.found) == ("0..1", 2)
    assert "nothing was written" in str(e.value)
    assert (wm.count("event"), wm.count("attestation")) == before


# ---- declarations (MP-3, MP-4) ---------------------------------------------------------------------------------------
def test_constraints_store_their_multiplicity_and_one_is_the_default(ref):
    wm, _ = ref
    official = {(k, u) for r, k, _, u in wm.event_role_constraints()["official-act"] if r == "actor"}
    assert official == {(None, "one"), (CO_SIGNED, "set")}
    from worldmodel import typeql as q
    with wm._reading() as tx:                            # absent means "one": only the set declaration stores a value
        stored = {q.opt(r, "u") for r in q.rows(tx, "match $c isa event-role-constraint, has role-multiplicity $u;")}
    assert stored == {"set"}


def _fixture_profile(*declarations):
    import dataclasses
    import profile_fixtures as F
    vocab = F.MECHANICAL.vocabulary + (("category", "mechanical-fixture:batch", "batch"),)
    return dataclasses.replace(F.MECHANICAL, vocabulary=vocab, event_roles=declarations)


@pytest.mark.parametrize("declarations,why", [
    ((EventRole("part-swap", "patient", "mechanical-fixture:overhaul", "one"),
      EventRole("part-swap", "patient", "mechanical-fixture:batch", "set")), "different multiplicities"),
    ((EventRole("part-swap", "patient", None, "many"),), "multiplicity 'many' is not one of"),
])
def test_conflicting_or_invalid_declarations_are_refused_when_declared(driver, declarations, why):
    wm = new_db(driver)
    try:
        bad = _fixture_profile(*declarations)
        with pytest.raises(ProfileError, match=why):
            wm.install_profile(bad)
        assert bad.module not in wm.modules() and wm.event_role_constraints() == {}
    finally:
        drop(wm)


# ---- upgrade of an existing database (MP-5) ------------------------------------------------------------------------
@pytest.fixture
def before_mp(driver):
    """A database created before LABS-1.049 (no multiplicity module), its profiles at increment D's versions, with an
    official act described by two accounts naming different officials."""
    wm = new_db(driver, CORE_MODULES[:-1])
    try:
        for p in (org.PROFILE_02, mech.PROFILE_02, lb.PROFILE_01):
            wm.install_profile(p)
        w = wm.create_world("actual", id="w")
        people(wm)
        wm.add_entity("occurrence", "o-act", id="o-act")
        for who, src in (("bea", "hr"), ("cal", "clerk")):
            accept_account(wm, w, org.act_in_office(wm, w, who, "site-manager", "acme", T(5), occurrence="o-act",
                                                    attester=src, id=f"act-{src}"))
        yield wm
    finally:
        drop(wm)


def test_the_upgrade_keeps_every_answer_and_then_accepts_several_players(before_mp):
    wm = before_mp
    assert MULTIPLICITY_MODULE not in wm.modules()
    with pytest.raises(RoleCardinalityError):                       # before: one official per account
        org.act_in_office(wm, "w", ["bea", "cal"], "site-manager", "acme", T(6))
    view = wm.occurrence("w", "o-act")
    report = org.official_act(wm, "w", "act-hr")
    assert wm.upgrade_to_event_multiplicity() is True
    assert wm.upgrade_to_event_multiplicity() is False              # idempotent
    assert wm.occurrence("w", "o-act") == view                      # only the module: nothing judged differently
    for p in ("organisation", "mechanical", "laboratory"):
        assert wm.upgrade_profile(p) is True
    upgraded = wm.occurrence("w", "o-act")
    for k in ("descriptions", "participants", "accounts"):
        assert upgraded[k] == view[k]
    old, (new_plain, new_cosigned) = (view["roles"]["official-act:official"]["constraints"],
                                      sorted(upgraded["roles"]["official-act:official"]["constraints"],
                                             key=lambda c: c["kind"] or ""))
    assert len(old) == 1 and {k: v for k, v in new_plain.items() if k in old[0]} == old[0]   # fields only added
    assert (new_plain["multiplicity"], new_plain["reason"]) == ("one", "accounts name different players")
    assert (new_cosigned["kind"], new_cosigned["applies"]) == (CO_SIGNED, False)
    assert org.official_act(wm, "w", "act-hr") == report
    e = org.act_in_office(wm, "w", ["bea", "cal"], "site-manager", "acme", T(6))
    assert wm.content(e)["roles"]["official"] == ["bea", "cal"]


def test_the_upgrade_is_one_way_once_used(before_mp):
    wm = before_mp
    wm.upgrade_to_event_multiplicity()
    wm.account("w", {"actor": ["dan", "eve"]}, T(6))
    with pytest.raises(Exception, match="CNT5"):                     # TypeDB refuses to narrow a role in use (C5)
        with wm.driver.transaction(wm.database, SCHEMA) as tx:
            tx.query("redefine relation event relates actor @card(0..1);").resolve()
            tx.commit()


def test_the_upgrade_is_refused_without_the_event_role_module(driver):
    from worldmodel.model import PROFILE_BASE_MODULES
    wm = new_db(driver, PROFILE_BASE_MODULES)
    try:
        with pytest.raises(ValueError, match=r"run wm\.upgrade_to_event_roles\(\) first"):
            wm.upgrade_to_event_multiplicity()
        assert MULTIPLICITY_MODULE not in wm.modules()
    finally:
        drop(wm)


def test_a_failing_upgrade_leaves_nothing(before_mp, monkeypatch):
    wm = before_mp
    schema = wm.driver.databases.get(wm.database).schema()
    real = wm.install_module

    def install_then_fail(*a, **k):
        real(*a, **k)
        raise RuntimeError("injected failure")
    monkeypatch.setattr(wm, "install_module", install_then_fail)
    with pytest.raises(RuntimeError, match="injected"):
        wm.upgrade_to_event_multiplicity()
    monkeypatch.undo()
    assert MULTIPLICITY_MODULE not in wm.modules() and wm.driver.databases.get(wm.database).schema() == schema
    assert wm.upgrade_to_event_multiplicity() is True


# ---- move(): the LABS-1.047 probe, case 2 ---------------------------------------------------------------------------
@pytest.fixture
def moves(driver):
    wm = new_db(driver)
    try:
        wm.install_profile("organisation")
        w = wm.create_world("actual", id="w")
        people(wm)
        yield wm, w
    finally:
        drop(wm)


def stored(wm):
    """Every stored description and attestation (ending a record writes an attestation, so this sees ends too)."""
    return wm.count("event"), wm.count("attestation")


def test_move_with_one_origin_is_recorded(moves):
    wm, w = moves
    wm.attest(w, "located-at", {"located": "thing", "place": "p1"}, start=T(1), until_superseded=True)
    eid, _ = wm.move(w, "thing", "p3", T(5), actor=["dan", "eve"])            # a joint move (MP-1)
    roles = wm.content(eid)["roles"]
    assert (roles["origin"], roles["destination"], roles["actor"]) == (["p1"], ["p3"], ["dan", "eve"])


def test_move_refuses_several_origins_with_a_domain_error_and_writes_nothing(moves):
    wm, w = moves
    a1 = wm.attest(w, "located-at", {"located": "thing", "place": "p1"}, start=T(1), until_superseded=True)
    a2 = wm.attest(w, "located-at", {"located": "thing", "place": "p2"}, start=T(1), until_superseded=True)
    before = stored(wm)
    with pytest.raises(MovementConflict) as e:
        wm.move(w, "thing", "p3", T(5))
    assert (e.value.role, e.value.places, e.value.records) == ("origin", ["p1", "p2"], sorted([a1, a2]))
    assert "nothing written" in str(e.value) and "CNT5" not in str(e.value)
    assert stored(wm) == before
    located = wm.value_at(w, "located-at", "thing", T(6))           # both records kept, neither ended
    assert located.status == Status.DISPUTED and sorted(located.values) == ["p1", "p2"]


def test_move_refuses_several_destinations_or_things(moves):
    wm, w = moves
    before = stored(wm)
    with pytest.raises(MovementConflict, match="one destination"):
        wm.move(w, "thing", ["p1", "p2"], T(5))
    with pytest.raises(ValueError, match="moves one thing"):
        wm.move(w, ["thing", "pump"], "p1", T(5))
    assert stored(wm) == before


def test_a_refused_move_inside_an_operation_rolls_back_the_whole_operation(moves):
    wm, w = moves
    wm.attest(w, "located-at", {"located": "thing", "place": "p1"}, start=T(1), until_superseded=True)
    wm.attest(w, "located-at", {"located": "thing", "place": "p2"}, start=T(1), until_superseded=True)
    before = stored(wm)
    with pytest.raises(MovementConflict):
        with wm.operation():
            wm.move(w, "pump", "p3", T(5))                      # recorded inside the operation ...
            wm.move(w, "thing", "p3", T(5))                     # ... then refused: nothing of either is kept
    assert stored(wm) == before
