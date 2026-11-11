"""The laboratory reference world, Stage D-3 extension (LABS-1.028): samples, an experiment, calibration and
interpretations, on top of the Stage C laboratory (examples/lab.py: build_lab, extend_lab_agency).

Invented, generic data: masses, instruments, certificates and reference numbers are illustrative, not real.
- **Samples:** Ana takes sub-sample s12-a from the specimen sample-12 at 14:00. Her account and its claimed effects
  are accepted, but nobody attests that the sampling occurred. Bo splits s12-a into s12-b and s12-c at 15:30. The lab
  log attests that the s12-b split occurred; Bo's s12-c account is unreviewed. s12-a ends with the split.
- **Experiment:** o-exp-1, documented by protocol P-7, with three steps (the sampling, the s12-b split and a late
  weighing).
- **Calibration:**
  - certificate B3 (CAL-B3-2026-10) is valid until 10:00 day 10, so the 15:00 weighing on B3 states a matching but
    expired reference;
  - certificate B7 (CAL-B7-2026-08) is disputed by the quality office, while Bo's B7 record states CAL-B7-2026-09, a
    reference no certificate carries;
  - balance B9 has no certificate.

  A hypothetical world, branching at 15:30, stipulates a renewed B3 certificate from 09:30.
- **Interpretations:** Ana hypothesises that sample 12 is hydrated (from her 35 °C result). Lab 2 testifies that it
  is anhydrous (from its own result). Bo testifies that it is hydrated (from his k=3 result). The system accepts Ana's
  and Bo's interpretations. The quality office accepts both rivals.
"""

from .. import laboratory as lb
from . import lab

T = lab.T


def build_laboratory(wm):
    """The full laboratory world (Stage C1, C2 and D-3) in a database with the core and the laboratory profile."""
    return extend_laboratory(wm, lab.extend_lab_agency(wm, lab.build_lab(wm)))


def _accept_account(wm, w, ids):
    for a in wm.account_attestations(w, ids["event"]):
        wm.accept(a)
    for a in ids["effects"]:
        wm.accept(a)


def extend_laboratory(wm, ids):
    """Add the D-3 contents to a laboratory world from lab.extend_lab_agency. Returns ids, extended."""
    w, mass, M = ids["world"], ids["mass"], ids["measurements"]
    for i, n in (("s12-a", "Sub-sample 12a"), ("s12-b", "Sub-sample 12b"), ("s12-c", "Sub-sample 12c")):
        wm.add_entity("sample", n, id=i)
    wm.add_entity("place", "Freezer 2", id="freezer-2")
    wm.add_entity("social-object", "Calibration laboratory", id="cal-lab")
    wm.add_entity("information-object", "Protocol P-7", id="protocol-7")
    for i, n in (("o-exp-1", "experiment 1"), ("o-sampling-1", "sampling of s12-a"), ("o-split-b", "split: s12-b"),
                 ("o-split-c", "split: s12-c"), ("o-weigh-late", "late weighing")):
        wm.add_entity("occurrence", n, id=i)
    for c in ("hydrated", "anhydrous"):
        wm.add_entity("category", c, id=c)
    wm.attest(w, "classified-as", {"classified": "sample-12", "class": lb.SPECIMEN}, start=T(8),
              until_superseded=True)

    # ---- samples: an account, its claimed effects, and the states attested apart ---------------------------------
    s1 = lb.take_sample(wm, w, "ana", "sample-12", "s12-a", T(14), T(14, 10), occurrence="o-sampling-1",
                        attester="ana", id="ev-sampling-1")
    _accept_account(wm, w, s1)                         # accepted account; nobody attests the occurrence itself
    for a in (wm.attest(w, "constitution", {"constituted": "s12-a", "constituent": "sample-12"}, start=T(14, 10),
                        until_superseded=True, attester="ana"),
              wm.attest(w, "located-at", {"located": "s12-a", "place": "freezer-2"}, start=T(14, 20), end=T(15, 30),
                        attester="ana")):
        wm.accept(a)
    wm.declare_existence(w, "s12-a", start=T(14, 10), end=T(15, 30))     # a portion: the split ends it
    split_b = lb.take_sample(wm, w, "bo", "s12-a", "s12-b", T(15, 30), T(15, 40), occurrence="o-split-b",
                             attester="bo", id="ev-split-b")
    _accept_account(wm, w, split_b)
    split_c = lb.take_sample(wm, w, "bo", "s12-a", "s12-c", T(15, 30), T(15, 40), occurrence="o-split-c",
                             attester="bo", id="ev-split-c")                # unreviewed
    wm.declare_existence(w, "o-split-b", start=T(15, 30), end=T(15, 40))    # the lab log: this split occurred
    wm.declare_existence(w, "s12-b", start=T(15, 40))
    wm.attest(w, "constitution", {"constituted": "s12-b", "constituent": "s12-a"}, start=T(15, 40),
              until_superseded=True)
    wm.attest(w, "located-at", {"located": "s12-b", "place": "freezer-2"}, start=T(15, 40), until_superseded=True)

    # ---- calibration: certificates, attested calibrations, a disputed one, and a late weighing --------------------
    for cid, n, ref in (("cert-b3", "Certificate B3", "CAL-B3-2026-10"), ("cert-b7", "Certificate B7", "CAL-B7-2026-08")):
        lb.register_certificate(wm, n, ref, id=cid)
    cal_event = wm.account(w, {"actor": "cal-lab", "patient": "balance-b3"}, T(8, day=1), T(9, day=1),
                           kind=lb.CALIBRATION, attester="cal-lab", id="ev-cal-b3")
    for a in wm.account_attestations(w, cal_event):
        wm.accept(a)
    cal = {"b3": lb.calibrate(wm, w, "cert-b3", "balance-b3", start=T(0, day=1), end=T(10), attester="cal-lab"),
           "b7": lb.calibrate(wm, w, "cert-b7", "balance-b7", start=T(0, day=1), attester="cal-lab")}
    for a in cal.values():
        wm.accept(a)
    late = wm.measure(w, "sample-12", mass, 3.52, ids["kg"], 0.02, start=T(15), end=T(15, 5), instrument="balance-b3",
                      operator="ana", conditions=["temperature=20C", "humidity=40%"], calibration="CAL-B3-2026-10",
                      attester="ana", occurrence="o-weigh-late", persists=True, id="m-ana-b3-late")
    lab.accept_measurement(wm, w, late)
    known_before_qa = wm._now()
    cal["b7-qa-denial"] = lb.calibrate(wm, w, "cert-b7", "balance-b7", start=T(0, day=1), attester="qa",
                                       polarity=False)
    wm.accept(cal["b7-qa-denial"])                     # accepted: the system now has both, so B7 is disputed

    # ---- the experiment and its documented steps ------------------------------------------------------------------
    wm.attest(w, "classified-as", {"classified": "o-exp-1", "class": lb.EXPERIMENT}, until_superseded=True,
              evidence=[lambda tx: "protocol-7"])
    for step in ("o-sampling-1", "o-split-b", "o-weigh-late"):
        wm.attest(w, "part-of", {"part": step, "whole": "o-exp-1"}, start=T(14), until_superseded=True,
                  evidence=[lambda tx: "protocol-7"])

    # ---- interpretations: a hypothesis and rival testimony, each resting on its record ----------------------------
    interp = {
        "ana-hydrated": lb.interpret(wm, w, M["ana-b9-35C"]["result"], "classified-as",
                                     {"classified": "sample-12", "class": "hydrated"}, "ana", tentative=True,
                                     start=T(12, 10)),
        "lab2-anhydrous": lb.interpret(wm, w, M["lab2"]["result"], "classified-as",
                                       {"classified": "sample-12", "class": "anhydrous"}, "lab-2", start=T(11, 10)),
        "bo-hydrated": lb.interpret(wm, w, M["bo-b7-k3"]["result"], "classified-as",
                                    {"classified": "sample-12", "class": "hydrated"}, "bo", start=T(13, 10))}
    for key in ("ana-hydrated", "bo-hydrated"):
        wm.accept(interp[key])
    for key in ("bo-hydrated", "lab2-anhydrous"):
        wm.accept(interp[key], holder="qa")            # the quality office accepts both rivals

    # ---- a hypothetical world: B3 recalibrated at 09:30 -----------------------------------------------------------
    # The plan inherits what the actual world says from before 15:30 (its branch time), the late weighing included
    plan = wm.create_world("Plan: B3 recalibrated", kind="hypothetical", base=w, branch_at=T(15, 30),
                           id="lab-plan-recal")
    lb.register_certificate(wm, "Certificate B3 (renewed)", "CAL-B3-2026-11", id="cert-b3-r")
    cal["plan-b3-r"] = lb.calibrate(wm, plan, "cert-b3-r", "balance-b3", start=T(9, 30))
    ids.update({"late": late, "sampling": s1, "split_b": split_b, "split_c": split_c, "calibrations": cal,
                "calibration_event": cal_event, "interpretations": interp, "plan_recal": plan,
                "known_before_qa": known_before_qa, "experiment": "o-exp-1"})
    return ids
