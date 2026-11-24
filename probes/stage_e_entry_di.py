"""Stage E entry: the deferred issues DI-7, DI-17 and DI-19 reproduced in isolation, with the code unchanged.

    uv run python -I probes/stage_e_entry_di.py <checkout> [--reference wm-probe-stage-e]

Each issue gets its own small throwaway database (wm-probe-stage-e-di-*, all deleted at the end of the run). For each
one the report prints the minimal setup (what was written), the observed answer fields, the expected semantics in the
project's own documents (cited by document and section) and the corrections already listed in
docs/core-0.4/deferred-issues.md. Nothing new is proposed here.
- DI-7: an attestation written directly with basis `inference` (no rule, no premises) and accepted is reported
  INFERRED by holds() and by the canonical judgement, while laboratory.interpret refuses basis `inference`. What the
  database records about it: evidence (rests-on) only, no rule and no premises; the schema has no type for either.
- DI-17: s1~s2 and s2~s3 established, s1~s3 denied: identity() merges none of the three and reports the conflict, so
  the established s1~s2 link is set aside. The kept reference database (--reference, READ ONLY) is counted for
  same-as attestations and conflict groups, for every world and every perspective, to state the reference impact.
- DI-19: an exclusive office (constraint established) with two accepted, overlapping appointments (ORG-011 of
  benchmark/e1, revised): holds() answers DISPUTED without citing the constraint; the canonical judgement
  (constraints[].judgement.support) and organisation.office_holders (conflict.constraint.support) do cite it.
Output: probes/stage_e_entry_di.out.txt.
"""

import argparse
import json
import sys
import time
import uuid
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path

warnings.filterwarnings("ignore", category=SyntaxWarning)   # the TypeDB driver's harmless import-time warning

ap = argparse.ArgumentParser()
ap.add_argument("checkout")
ap.add_argument("--reference", default="wm-probe-stage-e", help="kept reference database, read only")
a = ap.parse_args()
sys.path.insert(0, str(Path(a.checkout).resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, connect  # noqa: E402
from worldmodel import laboratory as lb  # noqa: E402
from worldmodel import organisation as org  # noqa: E402
from worldmodel import typeql as q  # noqa: E402

PREFIX = "wm-probe-stage-e-di"


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


def T(day, hour=9, minute=0):
    """As in evaluation/loader.py: 'T<d>' is 2026-11-<d> 09:00 UTC."""
    return datetime(2026, 11, day, hour, minute, tzinfo=timezone.utc)


driver = connect()
made = []


def fresh(issue):
    name = f"{PREFIX}-{issue}-{uuid.uuid4().hex[:8]}"
    made.append(name)
    return WorldModel.create(name, driver=driver, modules=CORE_MODULES, clock=Clock())


def heading(text):
    print("\n" + "=" * 100 + f"\n{text}\n" + "=" * 100)


def section(text):
    print(f"\n-- {text}")


def answer_fields(ans):
    print(f"  status: {ans.status.name}   holds: {ans.holds}   values: {list(ans.values)}")
    print(f"  support: {list(ans.support)}")
    print(f"  conflicts: {list(ans.conflicts)}")
    print(f"  alternatives: {list(ans.alternatives)}")
    for e in ans.evidence:
        print(f"  evidence: {e['attestation']} attester={e['attester']} stance={e['stance']} basis={e['basis']} "
              f"polarity={e['polarity']}")


def judgement_fields(rec):
    print(f"  judgement: {rec.judgement.value}   reasons: {list(rec.reasons)}   status: "
          f"{rec.status.name if rec.status else None}   support_status: "
          f"{rec.support_status.name if rec.support_status else None}")
    print(f"  support: {[x.id for x in rec.support]}")
    print(f"  conflicts: {[x.id for x in rec.conflicts]}")
    for c in rec.constraints:
        j = c.judgement
        js = None if j is None else f"{j.judgement.value}, support {[x.id for x in j.support]}"
        print(f"  constraints[]: kind={c.kind} type={c.type} key_roles={list(c.key_roles)} value_role={c.value_role} "
              f"key={list(c.key)} applies={c.applies} judgement=({js})")


# ---- DI-7 -----------------------------------------------------------------------------------------------------------------
def di7():
    heading("DI-7: formal derivation provenance is not recorded")
    wm = fresh("7")
    wm.install_profile("laboratory")
    w = wm.create_world("Laboratory, actual", id="lab")
    wm.add_entity("physical-object", "Sample 12", id="sample-12")
    wm.add_entity("social-object", "External laboratory 2", id="lab-2")
    wm.add_entity("category", "measurement", id="measurement")
    wm.add_entity("category", "anhydrous", id="anhydrous")
    kg = wm.define_unit("kilogram", "mass", id="u-kg")
    mass = wm.define_quality_kind("mass", "mass", id="q-mass")
    m = wm.measure(w, "sample-12", mass, 3.70, kg, 0.02, k=2, start=T(10, 11), end=T(10, 11, 5), operator="lab-2",
                   attester="lab-2", persists=True, id="m-lab2")
    rec = m["result"]
    section("setup (written)")
    print(f"  world {w}; sample-12, lab-2; category anhydrous; one measurement by lab-2 (result record {rec!r}, "
          f"not accepted)")
    print("  laboratory profile installed")
    content = ("classified-as", {"classified": "sample-12", "class": "anhydrous"})
    before = wm.count("attestation")
    try:
        lb.interpret(wm, w, rec, *content, "lab-2", basis="inference")
        refused = "NOT refused"
    except ValueError as e:
        refused = f"refused: ValueError: {e}"
    print(f"  1. laboratory.interpret(..., classified-as(sample-12, anhydrous), lab-2, basis='inference'): {refused}")
    print(f"     attestations before {before}, after {wm.count('attestation')} (nothing written)")
    raw = wm.attest(w, *content, until_superseded=True, basis="inference", attester="lab-2",
                    evidence=[lambda tx: rec], id="att-anhydrous")
    wm.accept(raw)
    print(f"  2. wm.attest(..., classified-as(sample-12, anhydrous), basis='inference', attester=lab-2, "
          f"evidence=[{rec}]) -> {raw}; accepted by system")
    t = T(10, 16)

    section(f"observed: holds(lab, classified-as, sample-12/anhydrous, {t:%Y-%m-%d %H:%M})")
    answer_fields(wm.holds(w, *content, t))
    section("observed: canonical judgement (wm.judgement)")
    judgement_fields(wm.judgement(w, *content, t))
    section("observed: laboratory.interpretations on the record")
    for i in lb.interpretations(wm, w, rec, t):
        if i["attestation"] == raw:
            print(f"  mode: {i['mode']}")
            print(f"  derivation: {i['derivation']}")
            print(f"  content_judgement: judgement={i['content_judgement']['judgement']} "
                  f"status={i['content_judgement']['status'].name}")

    section(f"observed: what the database records about {raw}")
    with wm._reading() as tx:
        attrs = sorted({(r.get("at").get_label(), str(q.opt(r, "x"))) for r in q.rows(tx, """match
            $a isa attestation, has wm-id == $id; $a has $x; $x isa! $at;""", {"id": raw})})
        rels = sorted({r.get("rt").get_label() for r in q.rows(tx, """match
            $a isa attestation, has wm-id == $id; $r links ($a); $r isa! $rt;""", {"id": raw})})
        rests = sorted({q.opt(r, "rid") for r in q.rows(tx, """match $a isa attestation, has wm-id == $id;
            rests-on (attestation: $a, record: $r); $r has wm-id $rid;""", {"id": raw})})
        labels = set()
        for kind in ("entity", "relation", "attribute"):
            labels |= {r.get("t").get_label() for r in q.rows(tx, f"match {kind} $t;")}
    print(f"  attributes: {', '.join(f'{k}={v}' for k, v in attrs)}")
    print(f"  relations it plays in: {rels}")
    print(f"  rests-on records (evidence): {rests}")
    hits = sorted(x for x in labels if any(s in x for s in ("rule", "deriv", "premise", "reasoner")))
    print(f"  schema types whose label mentions rule / deriv / premise / reasoner: {hits or 'none'}")

    section("expected (project documents)")
    print("  docs/architecture/world-ontology-v0.2.md, 5.2 invariant E6: a derived attestation names its rule (id,")
    print("  version) and premises; its attester is the reasoner that ran the rule; it is usable only while all its")
    print("  premises are usable. INFERRED is reserved for such attestations (deferred-issues.md DI-7, 'What happens').")
    print("  docs/core-0.4/stage-d3-design.md G-1 / D-D3-4: an analyst's interpretation is testimony or a hypothesis.")
    print("  Here the attestation names no rule and no premises (only a rests-on evidence record), yet is INFERRED:")
    print("  the core reads INFERRED from basis alone. laboratory.interpret refuses the same write; the core does not.")
    section("potential corrections (deferred-issues.md DI-7, options for Stage E)")
    print("  (a) a derivation record: the attestation names its rule (a concept) and premises (attestations); only")
    print("      those are INFERRED, others with basis inference are reported as testimony;")
    print("  (b) refuse basis inference on write unless a derivation record is given;")
    print("  (c) keep it as documentation only.  Recommended there: (a) with (b) as its write-time check.")


# ---- DI-17 ----------------------------------------------------------------------------------------------------------------
def di17():
    heading("DI-17: conflict-group identity may be over-restrictive")
    wm = fresh("17")
    wm.install_profile("organisation")                 # for the `person` type, as in pre_e_identity_cases.py
    w = wm.create_world("actual", id="w")
    for p in ("s1", "s2", "s3", "matcher", "clerk"):
        wm.add_entity("person", p, id=p)

    def same(x, y, **kw):
        return wm.attest(w, "same-as", {"same": [x, y]}, until_superseded=True, **kw)

    ids = {}
    ids["s1~s2"] = same("s1", "s2", attester="matcher", id="same-s1-s2")
    wm.accept(ids["s1~s2"])
    ids["s2~s3"] = same("s2", "s3", attester="matcher", id="same-s2-s3")
    wm.accept(ids["s2~s3"])
    ids["s1!~s3"] = wm.deny(w, "same-as", {"same": ["s1", "s3"]}, until_superseded=True, attester="clerk",
                            id="deny-s1-s3")
    wm.accept(ids["s1!~s3"])
    section("setup (written; case I16 of probes/pre_e_identity_cases.py, tests/test_t_identity.py)")
    print("  organisation profile installed (for `person`); world w; persons s1, s2, s3; attesters matcher, clerk")
    print(f"  matcher asserts same-as(s1, s2) [{ids['s1~s2']}] and same-as(s2, s3) [{ids['s2~s3']}]; "
          f"clerk denies same-as(s1, s3) [{ids['s1!~s3']}]; the system accepts all three")

    section("observed: each link's canonical judgement (by its stated names, ID-1)")
    for x, y in (("s1", "s2"), ("s2", "s3"), ("s1", "s3")):
        rec = wm.judgement(w, "same-as", {"same": [x, y]}, T(5))
        print(f"  same-as({x}, {y}): {rec.judgement.value} {list(rec.reasons)} support {[s.id for s in rec.support]}")
    ident = wm.identity(w)
    section("observed: identity(w) for the system")
    for x in ("s1", "s2", "s3"):
        print(f"  members({x}): {ident.members(x)}")
    for link in ident.links:
        print(f"  links[]: same={link['same']} judgement={link['judgement']} support={link['support']} "
              f"merges={link['merges']}")
    for c in ident.conflicts:
        print(f"  conflicts[]: names={c['names']}")
        for link in c["links"]:
            print(f"    links: same={link['same']} judgement={link['judgement']} support={link['support']}")
        for link in c["against"]:
            print(f"    against: same={link['same']} judgement={link['judgement']} support={link['support']}")
    print(f"  report('s2')['conflict'] is the same group: {ident.report('s2')['conflict'] == ident.conflicts[0]}"
          if ident.conflicts else "  no conflict reported")
    kept = "s2" in ident.members("s1")
    print(f"  established s1~s2 kept as a merge: {kept}  (set aside together with the chain that contradicts the "
          f"denial)" if not kept else f"  established s1~s2 kept as a merge: {kept}")

    section("expected (project documents)")
    print("  docs/core-0.4/pre-e-identity-design.md 3.5 ID-5 (approved, LABS-1.049): a component containing two names")
    print("  whose own link is DISPUTED or denied is not merged at all; each name is its own class and identity()")
    print("  reports the conflict. 'I16: s1 and s2, whose own link is established, are not merged either.'")
    print("  So the behaviour is the approved one; DI-17 records the risk that it is stricter than needed (one")
    print("  denial switches off every sound equivalence of the group).")

    section(f"reference impact: {a.reference} (read only)")
    ref = WorldModel(driver, a.reference)
    with ref._reading() as tx:
        worlds = sorted({q.opt(r, "id") for r in q.rows(tx, "match $w isa world, has wm-id $id;")})
        n_same = len({q.opt(r, "aid") for r in q.rows(tx, """match $a isa attestation (content: $c), has wm-id $aid;
            $c isa same-as;""")})
        n_all = len({q.opt(r, "aid") for r in q.rows(tx, "match $a isa attestation, has wm-id $aid;")})
    groups, contexts = 0, 0
    for wid in worlds:
        attesters = sorted({x.attester for x in ref.visible(wid).values()} | {"system"})
        for p in attesters:
            contexts += 1
            groups += len(ref.identity(wid, perspective=p).conflicts)
    print(f"  worlds: {len(worlds)}; attestations: {n_all}; same-as attestations (any world, either polarity): {n_same}")
    print(f"  conflict groups over {contexts} contexts (every world x system and each attester there, now): {groups}")
    section("potential corrections (deferred-issues.md DI-17; each a semantic change needing its own design)")
    print("  merge every established link except those that would join the disputed pair (needs a rule for which")
    print("  link to drop); merge maximal consistent subgroups; or merge and flag the answers that relied on the group.")
    print("  Disposition there: evaluate in Stage E (count conflict groups in the evaluation data); change only by a")
    print("  new approved design.")


# ---- DI-19 ----------------------------------------------------------------------------------------------------------------
def di19():
    heading("DI-19: a constraint dispute through holds() does not cite the constraint")
    wm = fresh("19")
    wm.install_profile("organisation")
    w = wm.create_world("actual", id="w")
    for p in ("bea", "cal"):
        wm.add_entity("person", p, id=p)
    wm.add_entity("organisation", "acme", id="acme")
    wm.add_entity("social-role", "site-manager", id="site-manager")
    for s in ("hr", "clerk"):
        wm.add_entity("social-object", s, id=s)
    a_bea = org.appoint(wm, w, "bea", "site-manager", "acme", start=T(1), attester="hr", id="a-bea")
    wm.accept(a_bea)
    x_sm = org.declare_exclusive(wm, w, "site-manager", "acme", start=T(1), attester="hr", id="x-sm")
    wm.accept(x_sm)
    a_cal = org.appoint(wm, w, "cal", "site-manager", "acme", start=T(8), attester="clerk", id="a-cal")
    wm.accept(a_cal)
    section("setup (written; the site-manager part of benchmark/e1/fixtures/org-offices.json, question ORG-011)")
    print("  world w; persons bea, cal; organisation acme; social-role site-manager; attesters hr, clerk")
    print("  a-bea: hr appoints bea site-manager at acme from T1 (until superseded); accepted by system")
    print("  x-sm: hr declares exclusive-office(site-manager, acme) from T1 (until superseded); accepted by system")
    print("  a-cal: clerk appoints cal site-manager at acme from T8 (until superseded); accepted by system")
    content = ("office-holding", {"classified": "bea", "class": "site-manager", "context": "acme"})
    t = T(10)

    section("observed: holds(w, office-holding, classified=bea class=site-manager context=acme, T10)")
    ans = wm.holds(w, *content, t)
    answer_fields(ans)
    cited = set(ans.support) | set(ans.conflicts) | {e["attestation"] for e in ans.evidence}
    print(f"  x-sm cited anywhere in the answer (support, conflicts, evidence): {x_sm in cited}")
    print(f"  Answer fields: {sorted(ans.__dataclass_fields__)}")
    section("observed: canonical judgement (wm.judgement), same question")
    rec = wm.judgement(w, *content, t)
    judgement_fields(rec)
    in_rec = any(c.judgement is not None and x_sm in [s.id for s in c.judgement.support] for c in rec.constraints)
    print(f"  x-sm in constraints[].judgement.support: {in_rec}")
    section("observed: organisation.office_holders(w, site-manager, acme, T10)")
    oh = org.office_holders(wm, w, "site-manager", "acme", t)
    print(f"  holders: {oh['holders']}   status: {oh['status']}")
    print(f"  exclusive: {oh['exclusive']}")
    print(f"  conflict: {oh['conflict']}")
    print(f"  x-sm in conflict.constraint.support: {x_sm in ((oh['conflict'] or {}).get('constraint') or {}).get('support', [])}")
    section("benchmark record (benchmark/e1/results-revised/results.json, ORG-011)")
    path = Path(a.checkout).resolve() / "benchmark" / "e1" / "results-revised" / "results.json"
    (r,) = [x for x in json.loads(path.read_text())["results"] if x["id"] == "ORG-011"]
    print(f"  expected {r['expected']}, actual {r['actual']}, correct {r['correct']}")
    print(f"  evidence required {r['evidence']['required']}, found {r['evidence']['found']}, recall "
          f"{r['evidence']['recall']}; failure {r['failure']!r}")

    section("expected (project documents)")
    print("  docs/core-0.4/deferred-issues.md DI-19: the judgement is right (DISPUTED under the constraint), but the")
    print("  provenance of a constraint dispute is incomplete through holds(): a reader cannot see from the answer")
    print("  alone which rule caused the dispute. The canonical judgement (constraints[].judgement.support) and")
    print("  organisation.office_holders (conflict.constraint.support) carry the constraint attestation; the")
    print("  benchmark question ORG-011 lists x-sm as required evidence.")
    section("potential correction (deferred-issues.md DI-19, proposed, not implemented, needs approval)")
    print("  an additive `constraint_support` on holds() answers: the attestation ids supporting each applied")
    print("  constraint (for an attested constraint its own deciding attestations; empty for a declared functional")
    print("  slot). Existing fields keep their values; the 106,752-answer baseline gains the field on constraint")
    print("  disputes only.")


started = time.monotonic()
try:
    for run in (di7, di17, di19):
        t0 = time.monotonic()
        run()
        print(f"\n  ({run.__name__}: {time.monotonic() - t0:.1f} s)")
finally:
    for name in made:
        if driver.databases.contains(name):
            driver.databases.get(name).delete()
    left = sorted(x.name for x in driver.databases.all() if x.name.startswith(PREFIX))
    print(f"\nthrowaway databases deleted: {len(made)}; {PREFIX}-* left on the server: {left or 'none'}")
    print(f"total run time: {time.monotonic() - started:.1f} s")
