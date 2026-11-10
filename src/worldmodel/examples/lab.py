"""An independent laboratory reference world (LABS-1.016): measuring the mass of a sample, then who may do what.

It uses only the core ontology and the same APIs as the gearbox world: no laboratory-specific type. Invented, generic
data; masses and instruments are illustrative, not real specifications.

Stage C1 (build_lab): a sample weighed on three balances by two analysts, a result from an external lab that the
system has not accepted, a measurement at another temperature, one at another coverage level, a design specification
(a statement, not a measurement), and a later correction of one result.
"""

from datetime import datetime, timedelta, timezone


def T(h, m=0, day=10):
    return datetime(2026, 11, day, h, m, tzinfo=timezone.utc)


def build_lab(wm):
    """The laboratory world in a database with QUALITY_MODULES. Returns the notable ids."""
    w = wm.create_world("Laboratory, actual", id="lab")
    for i, n in (("sample-12", "Sample 12"), ("balance-b3", "Balance B3"), ("balance-b7", "Balance B7"),
                 ("balance-b9", "Balance B9"), ("ana", "Analyst Ana"), ("bo", "Analyst Bo"),
                 ("tom", "Trainee Tom")):
        wm.add_entity("physical-object", n, id=i)
    for i, n in (("lab-1", "Laboratory 1"), ("lab-2", "External laboratory 2"), ("qa", "Quality office")):
        wm.add_entity("social-object", n, id=i)
    wm.add_entity("category", "measurement", id="measurement")
    kg = wm.define_unit("kilogram", "mass", id="u-kg")
    g = wm.define_unit("gram", "mass", 0.001, id="u-g")
    wm.define_unit("metre", "length", id="u-m")
    wm.define_unit("kelvin", "temperature", id="u-K")
    wm.define_unit("degree Celsius", "temperature", 1.0, 273.15, id="u-degC")
    mass = wm.define_quality_kind("mass", "mass", id="q-mass")
    at20, at35 = ["temperature=20C", "humidity=40%"], ["temperature=35C", "humidity=40%"]
    m = {}
    m["ana-b3"] = wm.measure(w, "sample-12", mass, 3.51, kg, 0.02, k=2, start=T(9), end=T(9, 5), instrument="balance-b3",
                             operator="ana", conditions=at20, calibration="CAL-B3-2026-10", attester="ana", persists=True,
                             id="m-ana-b3")
    m["bo-b7"] = wm.measure(w, "sample-12", mass, 3490.0, g, 15.0, k=2, start=T(10), end=T(10, 5),
                            instrument="balance-b7", operator="bo", conditions=at20, calibration="CAL-B7-2026-09",
                            attester="bo", persists=True, id="m-bo-b7")
    m["lab2"] = wm.measure(w, "sample-12", mass, 3.70, kg, 0.02, k=2, start=T(11), end=T(11, 5), operator="lab-2",
                           conditions=at20, attester="lab-2", persists=True, id="m-lab2")
    m["ana-b9-35C"] = wm.measure(w, "sample-12", mass, 3.53, kg, 0.02, k=2, start=T(12), end=T(12, 5),
                                 instrument="balance-b9", operator="ana", conditions=at35, attester="ana", persists=True,
                                 id="m-ana-b9")
    m["bo-b7-k3"] = wm.measure(w, "sample-12", mass, 3.50, kg, 0.01, k=3, start=T(13), end=T(13, 5),
                               instrument="balance-b7", operator="bo", conditions=at20, attester="bo", persists=True,
                               id="m-bo-k3")
    for key in ("ana-b3", "bo-b7", "ana-b9-35C", "bo-b7-k3"):        # the system accepts its analysts' results
        accept_measurement(wm, w, m[key])
    spec = wm.attest(w, "has-quality", {"bearer": "sample-12", "quality": mass, "unit": kg},
                     params={"lower": 3.5, "upper": 3.5}, until_superseded=True, attester="qa", basis="testimony")
    wm.accept(spec)                                                   # a specification: a statement, not a measurement
    known_before_correction = wm._now()
    # a correction: Ana's B3 result had a tare error; the corrected result supersedes her original content
    m["ana-b3-corrected"] = wm.measure(w, "sample-12", mass, 3.53, kg, 0.02, k=2, start=T(9), end=T(9, 5),
                                       instrument="balance-b3", operator="ana", conditions=at20,
                                       calibration="CAL-B3-2026-10", attester="ana", persists=True,
                                       supersedes=m["ana-b3"]["content"], id="m-ana-b3-corr")
    accept_measurement(wm, w, m["ana-b3-corrected"])
    return {"world": w, "measurements": m, "spec": spec, "mass": mass, "kg": kg, "g": g,
            "known_before_correction": known_before_correction}


def accept_measurement(wm, world, ids, holder="system"):
    """The holder accepts a measurement: its activity account, the produced and reports links, and the content."""
    for a in wm.account_attestations(world, ids["activity"]):
        wm.accept(a, holder=holder)
    for key in ("produced", "reports", "content"):
        wm.accept(ids[key], holder=holder)
