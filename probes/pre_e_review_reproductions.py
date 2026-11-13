"""Pre-Stage E correctness review (LABS-1.034): executable reproductions of DI-1, DI-2, DI-3, DI-4, DI-5, DI-6, DI-8
and DI-11 (found here), on main as merged (no semantic change). Each case prints the current behaviour and asserts it, so this probe
fails loudly once a correction changes it. Usage: uv run python -I probes/pre_e_review_reproductions.py <repo>

Builds one throwaway database (wm-probe-pre-e, deleted afterwards) with the full core and the three profiles.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, laboratory as lb, mechanical as mech, organisation as org  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.model import READ  # noqa: E402

DB = "wm-probe-pre-e"
OUT = {}


def T(day, h=9):
    return datetime(2026, 11, day, h, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


def show(case, **values):
    OUT[case] = values
    print(f"\n=== {case}")
    for k, v in values.items():
        print(f"  {k}: {json.dumps(v, default=str)}")


def ids_of(wm, world):
    with wm.driver.transaction(wm.database, READ) as tx:
        return {q.opt(r, "a") for r in q.rows(tx, """match $w isa world, has wm-id == $id;
            $x isa attestation (context: $w), has wm-id $a;""", {"id": world})}


wm = WorldModel.create(DB, modules=CORE_MODULES, clock=Clock(), replace=True)
try:
    for p in ("mechanical", "organisation", "laboratory"):
        wm.install_profile(p)
    w = wm.create_world("pre-E review", id="w")
    people = ("bea", "cal", "dan", "eve", "hr", "audit", "tech", "insp", "maint", "design", "ana", "bo")
    for p in people:
        wm.add_entity("person", p.capitalize(), id=p)
    for i in ("wheel", "axle", "housing", "b1", "b2", "b3", "cover", "core-1"):
        wm.add_entity("physical-object", i, id=i)
    for i in ("s-a", "s-b", "s-c"):
        wm.add_entity("sample", i, id=i)
    for i in ("proc", "step-1", "occ-r", "occ-s"):
        wm.add_entity("occurrence", i, id=i)
    for kind, i in (("social-role", "analyst"), ("social-role", "office-x"), ("capability", "cap"),
                    ("category", "joint-bolted"), ("category", "joint-bonded"), ("category", "steel"),
                    ("social-object", "depot")):
        wm.add_entity(kind, i, id=i)

    # ---- DI-1: polarity-disputed content omitted by facts_about and every reader built on it --------------------------
    a = wm.grant(w, "bea", "analyst", start=T(1), attester="hr")
    d = wm.grant(w, "bea", "analyst", polarity=False, start=T(1), attester="audit")
    pa = wm.attest(w, "part-of", {"whole": "wheel", "part": "axle"}, start=T(1), until_superseded=True, attester="tech")
    pd = wm.deny(w, "part-of", {"whole": "wheel", "part": "axle"}, start=T(1), until_superseded=True, attester="insp")
    sa = wm.attest(w, "part-of", {"whole": "proc", "part": "step-1"}, start=T(1), until_superseded=True, attester="tech")
    sd = wm.deny(w, "part-of", {"whole": "proc", "part": "step-1"}, start=T(1), until_superseded=True, attester="insp")
    da = wm.depend(w, "wheel", "axle", attester="tech", start=T(1))
    dd = wm.depend(w, "wheel", "axle", attester="insp", start=T(1), polarity=False)
    for x in (a, d, pa, pd, sa, sd, da, dd):
        wm.accept(x)
    t = T(5)
    h_role = wm.holds(w, "classified-as", {"classified": "bea", "class": "analyst"}, t)
    h_part = wm.holds(w, "part-of", {"whole": "wheel", "part": "axle"}, t)
    fa_bea = [f["type"] for f in wm.facts_about(w, "bea", t)]
    fa_wheel = [(f["type"], f["roles"]) for f in wm.facts_about(w, "wheel", t)]
    show("DI-1 current",
         holds_role=h_role.status.name, holds_part=h_part.status.name,
         facts_about_bea=fa_bea, roles_of_bea=wm.roles_of(w, "bea", t),
         capable_bea_analyst=wm.capable(w, "bea", "analyst", t)["judgement"],
         facts_about_wheel=fa_wheel, composition_wheel=wm.composition(w, "wheel", t),
         process_steps_proc=wm.process_steps(w, "proc", t),
         direct_dependencies_wheel=[(x["dependee"], x["status"].name) for x in wm.direct_dependencies(w, "wheel", t)])
    assert h_role.status.name == "DISPUTED" and h_part.status.name == "DISPUTED"
    assert "classified-as" not in fa_bea and wm.roles_of(w, "bea", t) == []
    assert wm.capable(w, "bea", "analyst", t)["judgement"] == "disputed"          # the _claims path keeps it
    assert not any(ty == "part-of" for ty, _ in fa_wheel)
    assert wm.process_steps(w, "proc", t) == []
    assert [x["status"].name for x in wm.direct_dependencies(w, "wheel", t)] == ["DISPUTED"]

    # ---- DI-2: conflicting single-valued event participants are unioned -------------------------------------------
    r1 = mech.replace_part(wm, w, "housing", "b1", "b3", start=T(3), occurrence="occ-r", attester="maint")
    r2 = mech.replace_part(wm, w, "housing", "b2", "b3", start=T(3), occurrence="occ-r", attester="insp")
    s1 = lb.take_sample(wm, w, "ana", "core-1", "s-a", start=T(3), occurrence="occ-s", attester="ana")
    s2 = lb.take_sample(wm, w, "bo", "core-1", "s-b", start=T(3), occurrence="occ-s", attester="bo")
    for r in (r1, r2, s1, s2):
        for x in wm.account_attestations(w, r["event"]) + r["effects"]:
            wm.accept(x)
    occ_r, occ_s = wm.occurrence(w, "occ-r"), wm.occurrence(w, "occ-s")
    show("DI-2 current",
         replacement_role_names=sorted(occ_r["participants"]), sampling_role_names=sorted(occ_s["participants"]),
         replacement_removed_as_patient=occ_r["participants"]["patient"],
         replacement_fitted=occ_r["participants"]["fitted"],
         sampling_product_as_destination=occ_s["participants"]["destination"],
         per_account_removed=[mech.replacement(wm, w, r["event"], T(5))["removed"] for r in (r1, r2)])
    assert set(occ_r["participants"]["patient"]) == {"b1", "b2"}                   # unioned, nothing DISPUTED
    assert set(occ_s["participants"]["destination"]) == {"s-a", "s-b"}
    # the merged view names specialised roles by their core role (removed -> patient, product -> destination) and
    # keeps a profile's own roles (fitted): two vocabularies in one view
    assert sorted(occ_r["participants"]) == ["fitted", "patient"]

    # ---- DI-3: conflicting joint kinds both hold --------------------------------------------------------------------
    j1 = mech.connect(wm, w, "cover", "housing", "joint-bolted", attester="design", start=T(1))
    j2 = mech.connect(wm, w, "cover", "housing", "joint-bonded", attester="insp", start=T(2))
    wm.accept(j1)
    wm.accept(j2)
    conns = [(c["other"], c["joint_kind"], c["status"].name) for c in mech.connections(wm, w, "cover", t)]
    show("DI-3 current", connections_cover=conns)
    assert conns == [("housing", "joint-bolted", "ASSERTED"), ("housing", "joint-bonded", "ASSERTED")]

    # ---- DI-4: any category is accepted as a dependency kind -----------------------------------------------------
    k = wm.depend(w, "housing", "cover", kind="steel", start=T(1))
    show("DI-4 current", direct_dependencies_housing=[(x["dependee"], x["kind"], x["status"].name)
                                                      for x in wm.direct_dependencies(w, "housing", t)],
         dependencies_of_kind_steel=sorted(wm.dependencies(w, "housing", t, kind="steel")))
    assert [x["kind"] for x in wm.direct_dependencies(w, "housing", t)] == ["steel"]

    # ---- DI-5: a not-yet-effective accepted holding is labelled by an unreviewed counter-claim ----------------------
    wm.grant(w, "cal", "cap", start=T(8))                                        # the system's own: accepted
    wm.grant(w, "cal", "cap", polarity=False, start=T(8), attester="audit")      # unreviewed denial
    wm.grant(w, "dan", "cap", start=T(8))                                        # the same, without a counter-claim
    c_cal, c_dan = wm.capable(w, "cal", "cap", T(5)), wm.capable(w, "dan", "cap", T(5))
    show("DI-5 current", cal=(c_cal["judgement"], c_cal["status"].name), dan=(c_dan["judgement"], c_dan["status"].name),
         cal_at_day_9=wm.capable(w, "cal", "cap", T(9))["judgement"])
    assert c_cal["judgement"] == "not established" and c_dan["judgement"] == "not yet effective"
    # the same fallback mislabels an accepted holding that has begun but whose end is unknown (no invented continuity)
    wm.attest(w, "classified-as", {"classified": "eve", "class": "cap"}, start=T(1))     # the system's own; end unknown
    c_eve = wm.capable(w, "eve", "cap", T(5))
    h_eve = wm.holds(w, "classified-as", {"classified": "eve", "class": "cap"}, T(5))
    show("DI-5 wider", eve_started_day_1_end_unknown=(c_eve["judgement"], c_eve["status"].name),
         holds=(h_eve.status.name, h_eve.holds))
    assert c_eve["judgement"] == "not yet effective" and h_eve.holds is None

    # ---- DI-6: one status folded from constituents with different statuses -----------------------------------------
    o1 = org.appoint(wm, w, "bea", "office-x", "depot", start=T(1), attester="hr")
    wm.accept(o1)
    wm.accept(wm.grant(w, "dan", "analyst", start=T(1), attester="hr"))                  # general, ASSERTED (inherited)
    wm.accept(wm.grant(w, "cal", "analyst", context="depot", start=T(1), attester="hr"))  # contextual, ASSERTED
    # the plan inherits what the actual world knew when it was created (its knowledge time), so it comes last
    plan = wm.create_world("plan", kind="hypothetical", base=w, branch_at=T(2), id="plan")
    org.appoint(wm, plan, "cal", "office-x", "depot", start=T(3))                # stipulated in the plan
    oh = org.office_holders(wm, plan, "office-x", "depot", T(5))
    # capable(): the same two-holding situation, mirrored; the folded status follows list order, not a rule
    wm.grant(plan, "dan", "analyst", context="depot", start=T(3))                         # contextual, STIPULATED
    wm.grant(plan, "cal", "analyst", start=T(3))                                          # general, STIPULATED
    cd, cc = wm.capable(plan, "dan", "analyst", T(5), context="depot"), wm.capable(plan, "cal", "analyst", T(5), context="depot")
    show("DI-6 current",
         office_holders=dict(holders=oh["holders"], status=oh["status"].name,
                             per_holder=[(x["holder"], x["status"].name) for x in oh["appointments"]]),
         capable_dan=(cd["status"].name, [(h["context"], h["status"].name) for h in cd["applicable"]]),
         capable_cal=(cc["status"].name, [(h["context"], h["status"].name) for h in cc["applicable"]]))
    assert oh["status"].name == "ASSERTED" and {x["status"].name for x in oh["appointments"]} == {"ASSERTED", "STIPULATED"}
    assert cd["status"].name == "ASSERTED" and cc["status"].name == "STIPULATED"          # mirror cases disagree

    # ---- DI-8: composite writes are not atomic ------------------------------------------------------------------
    real = wm.claim_effect
    calls = {"n": 0}

    def failing(*args, **kw):
        calls["n"] += 1
        if calls["n"] == 2:
            raise ConnectionError("simulated connection loss before the second effect claim")
        return real(*args, **kw)

    before = ids_of(wm, w)
    wm.claim_effect = failing
    try:
        lb.take_sample(wm, w, "ana", "core-1", "s-a", start=T(6), attester="ana", id="sampling-partial")
    except ConnectionError:
        pass
    wm.claim_effect = real
    written = ids_of(wm, w) - before
    partial_effects = wm.effects_of(w, "sampling-partial", T(7))
    show("DI-8 after increment A", attestations_written=len(written),
         effect_claims_recorded=[(e["kind"], e["outcome"]["type"]) for e in partial_effects],
         note="before increment A (LABS-1.034): the account survived with 1 of its 2 claimed effects; now nothing")
    assert len(partial_effects) == 0 and len(written) == 0

    # DI-8 option (a) with today's API: account() and claim_effect() accept batch=, but claim_effect first stores its
    # outcome content with WorldModel.proposition, in its own committed transaction, outside the batch.
    def batched(sampler, product, at, eid, fail=False):
        before, result = ids_of(wm, w), {}
        try:
            with wm._batch() as b:
                e = wm.account(w, {"sampler": sampler, "sampled": "core-1", "product": product}, at, at,
                               type="sampling", attester=sampler, id=eid, batch=b)
                wm.claim_effect(w, e, "initiates", "existence", {"existent": product}, attester=sampler, batch=b)
                if fail:
                    raise ConnectionError("simulated failure inside the batch")
                wm.claim_effect(w, e, "initiates", "constitution", {"constituted": product, "constituent": "core-1"},
                                attester=sampler, batch=b)
        except ConnectionError:
            result["simulated_failure"] = True
        except Exception as ex:
            result["error"] = " ".join(str(ex).split())[:160]
        result["attestations_written"] = len(ids_of(wm, w) - before)
        with wm.driver.transaction(wm.database, READ) as tx:
            result["description_written"] = bool(q.rows(tx, "match $e isa event, has wm-id == $id;", {"id": eid}))
            result["outcome_content_stored"] = bool(q.rows(tx, """match $x has wm-id == $id;
                $p isa existence (existent: $x);""", {"id": product}))
        return result

    show("DI-8 batch (operation) after increment A",
         a_outcomes_already_stored=batched("ana", "s-b", T(6), "sampling-batched"),
         b_new_outcome=batched("bo", "s-c", T(7), "sampling-batched-new"),
         c_failure_mid_batch=batched("bo", "s-a", T(7), "sampling-batched-fail", fail=True))
    f = OUT["DI-8 batch (operation) after increment A"]
    # before increment A: case b failed (the outcome content was committed outside the batch and left behind)
    assert f["a_outcomes_already_stored"]["attestations_written"] == 3
    assert "error" not in f["b_new_outcome"] and f["b_new_outcome"]["attestations_written"] == 3
    assert f["b_new_outcome"]["outcome_content_stored"] is True        # written inside the operation
    assert f["c_failure_mid_batch"]["attestations_written"] == 0 and not f["c_failure_mid_batch"]["description_written"]
    # ---- DI-3 feasibility: a functional slot keyed by the two-player `endpoint` role (register: "not verified") ----
    feas = {}
    try:
        wm.declare_slot("connected-to", ("endpoint",), "joint-kind")
        feas["declared"] = True
        hb = wm.holds(w, "connected-to", {"endpoint": ["cover", "housing"], "joint-kind": "joint-bolted"}, t)
        feas["holds_bolted"] = (hb.status.name, hb.holds)
        feas["connections_after"] = [(c["other"], c["joint_kind"], c["status"].name)
                                     for c in mech.connections(wm, w, "cover", t)]
        feas["facts_about_cover"] = [(f["type"], f["status"].name, f["conflicts"] != [])
                                     for f in wm.facts_about(w, "cover", t) if f["type"] == "connected-to"]
    except Exception as ex:
        feas["error"] = " ".join(str(ex).split())[:200]
    show("DI-3 feasibility and DI-11 (found by this review)", **feas)
    # the slot works in the core (holds, facts_about: DISPUTED), but the _claims-based profile report ignores it (DI-11)
    assert feas["holds_bolted"][0] == "DISPUTED" and all(st == "DISPUTED" for _, st, _ in feas["facts_about_cover"])
    assert [st for _, _, st in feas["connections_after"]] == ["ASSERTED", "ASSERTED"]
finally:
    wm.driver.databases.get(DB).delete()
print("\nall reproductions behaved as recorded")
