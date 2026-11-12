"""LABS-1.030 item 1: recursive sampling probe (no implementation change). Usage: python -I this.py <repo>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, laboratory as lb  # noqa: E402
from worldmodel.examples.lab import T  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.model import READ  # noqa: E402

DB = "wm-probe-recursive-sampling"
wm = WorldModel.create(DB, modules=CORE_MODULES, replace=True)
ok = []
def check(label, cond):
    ok.append(cond); print(("PASS " if cond else "FAIL ") + label)
try:
    wm.install_profile("laboratory")
    w = wm.create_world("Probe", id="p")
    for i in ("core-1", "ana", "bo", "tom"):
        wm.add_entity("physical-object", i, id=i)
    for i in ("s1", "s2", "s2b", "s3", "s4"):
        wm.add_entity("sample", i, id=i)
    for i in ("o1", "o2", "o4"):
        wm.add_entity("occurrence", i, id=i)
    def acc(ids):
        for a in wm.account_attestations(w, ids["event"]): wm.accept(a)
        for a in ids["effects"]: wm.accept(a)
    # level 1: a sample from a specimen; level 2: a sample from a sample, twice (siblings)
    acc(lb.take_sample(wm, w, "ana", "core-1", "s1", T(9), occurrence="o1", attester="ana", id="ev1"))
    wm.accept(wm.attest(w, "constitution", {"constituted": "s1", "constituent": "core-1"}, start=T(9), until_superseded=True, attester="ana"))
    wm.declare_existence(w, "s1", start=T(9), end=T(10))
    wm.declare_existence(w, "o1", start=T(9), end=T(9, 10))
    for s in ("s2", "s2b"):
        acc(lb.take_sample(wm, w, "bo", "s1", s, T(10), occurrence="o2" if s == "s2" else None, attester="bo", id=f"ev-{s}"))
        wm.attest(w, "constitution", {"constituted": s, "constituent": "s1"}, start=T(10), until_superseded=True)
        wm.declare_existence(w, s, start=T(10))
    # level 3a: an accepted account with no attested constitution; level 3b: a fully attested split of s2
    acc(lb.take_sample(wm, w, "bo", "s2", "s3", T(11), attester="bo", id="ev-s3"))
    acc(lb.take_sample(wm, w, "bo", "s2", "s4", T(12), occurrence="o4", attester="bo", id="ev-s4"))
    wm.attest(w, "constitution", {"constituted": "s4", "constituent": "s2"}, start=T(12), until_superseded=True)
    wm.declare_existence(w, "o4", start=T(12), end=T(12, 5))
    # a cycle, claimed by tom and not accepted: s1 made from s4
    wm.attest(w, "constitution", {"constituted": "s1", "constituent": "s4"}, start=T(9), until_superseded=True, attester="tom")

    p4 = lb.provenance(wm, w, "s4", T(13))
    links = [(c["sample"], c["from"], c["judgement"]) for c in p4["chain"]]
    print("s4 chain:", links)
    check("depth-3 chain s4 <- s2 <- s1 <- core-1, every link established",
          [(a, b) for a, b, j in links if j == "established"] == [("s4", "s2"), ("s2", "s1"), ("s1", "core-1")])
    check("the cycle (tom: s1 <- s4) is listed with its own judgement, not established, and the walk terminates",
          ("s1", "s4", "not established") in links and len(links) == 4)
    check("sampling accounts listed for every sample in the chain",
          set(p4["sampling"]) == {"s4", "s2", "s1", "core-1"} and all(p4["sampling"][x] for x in ("s4", "s2", "s1")))
    occ = {acc_["event"]: [(o["occurrence"], o["status"]) for o in acc_["occurrences"]]
           for x in ("s4", "s2", "s1") for acc_ in p4["sampling"][x]}
    print("occurrences:", occ)
    check("accounts distinct from occurrences: o4 and o1 attested (accepted); o2 not attested (not established)",
          occ["ev-s4"] == [("o4", "accepted")] and occ["ev-s2"] == [("o2", "not established")]
          and occ["ev1"] == [("o1", "accepted")])
    p3 = lb.provenance(wm, w, "s3", T(13))
    print("s3 chain:", p3["chain"], "account:", [(a["event"], a["account"]) for a in p3["sampling"]["s3"]])
    check("accepted account + accepted claimed effects, but no attested constitution: chain empty, account still listed",
          p3["chain"] == [] and [a["account"] for a in p3["sampling"]["s3"]] == ["accepted"])
    check("s3's existence not attested (the account's claimed effect is not evidence of the state)",
          p3["existence"]["attested"]["judgement"] == "not established")
    check("s1 (a portion) has ended at 13:00; s2 and s2b still exist",
          lb.provenance(wm, w, "s1", T(13))["existence"]["attested"]["judgement"] == "expired"
          and all(lb.provenance(wm, w, s, T(13))["existence"]["attested"]["judgement"] == "established" for s in ("s2", "s2b")))
    sib = lb.provenance(wm, w, "s2b", T(13)); print("s2b chain:", [(c["sample"], c["from"], c["judgement"]) for c in sib["chain"]], "sampling keys:", sorted(sib["sampling"]))
    check("sibling s2b shares s1 and core-1 as sources but not s2's descendants",
          [(c["sample"], c["from"]) for c in sib["established"]] == [("s2b", "s1"), ("s1", "core-1")]
          and {(c["sample"], c["from"]): c["ancestry"] for c in sib["chain"]}[("s4", "s2")] == "not established")
    with wm.driver.transaction(wm.database, READ) as tx:
        samples = sorted(q.opt(r, "i") for r in q.rows(tx, "match $x isa sample, has wm-id $i;"))
        specimen_is_sample = list(q.rows(tx, 'match $x isa sample, has wm-id "core-1";'))
        per_id = [len(list(q.rows(tx, 'match $x isa entity, has wm-id $i;', {"i": s}))) for s in samples] if False else None
        sampled_samples = sorted({q.opt(r, "i") for r in q.rows(tx, "match $e isa sampling (sampled: $x); $x isa sample, has wm-id $i;")})
    check("five distinct sample particulars; the specimen is not a sample", samples == ["s1", "s2", "s2b", "s3", "s4"] and not specimen_is_sample)
    check("samples play the 'sampled' role (sampling from an existing sample)", sampled_samples == ["s1", "s2"])
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
finally:
    wm.driver.databases.get(DB).delete()
sys.exit(0 if all(ok) else 1)
