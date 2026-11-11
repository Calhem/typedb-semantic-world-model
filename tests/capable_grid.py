"""A fixed grid of capable() / is_agent() answers on the laboratory world (LABS-1.026).

Used to show that extracting capable()'s judgement into a shared helper changes no answer: the baseline
(tests/fixtures/capable_baseline.json) was written by the code before the refactor (acba95f); the test recomputes the
grid and compares. Attestation ids are random per build, so each attestation is described by its attester, polarity,
basis and acceptance instead.
"""

from worldmodel.examples import lab

T = lab.T
HOLDERS = ("ana", "bo", "tom", "cy", "di", "ed", "balance-b3", "lab-2", "qa")
CAPABILITIES = ("can-weigh", "can-measure-mass", "agent")
CONTEXTS = (None, "lab-1", "lab-2")
TIMES = (T(6), T(9), T(11), T(13), T(16))
PERSPECTIVES = ("system", "qa", "tom")


def build(wm):
    """The lab world with C2 agency, plus the LABS-1.019 five-case additions."""
    ids = lab.extend_lab_agency(wm, lab.build_lab(wm))
    w = ids["world"]
    for i in ("cy", "di", "ed"):
        wm.add_entity("physical-object", i, id=i)
    ids["cy_denial"] = wm.grant(w, "cy", "can-weigh", context="lab-1", polarity=False, start=T(7))
    wm.grant(w, "di", "can-weigh", context="lab-1", start=T(16))
    wm.grant(w, "ed", "can-weigh", context="lab-1", start=T(7))
    contra = wm.grant(w, "ed", "can-weigh", context="lab-1", polarity=False, start=T(7), attester="qa")
    wm.accept(contra)
    wm.grant(w, "tom", "can-weigh", context="lab-1", start=T(7), attester="qa")
    return ids


def _describe(answer):
    return {"holds": answer["holds"], "status": answer["status"].value, "judgement": answer["judgement"],
            "only_in": answer["only_in"],
            "applicable": [[h["context"], h["judgement"], h["status"].value if h["status"] else None,
                            sorted([a["attester"], a["polarity"], a["basis"], a["acceptance"]]
                                   for a in h["attestations"])] for h in answer["applicable"]]}


def grid(wm, ids):
    w = ids["world"]
    out = []
    for p in PERSPECTIVES:
        for h in HOLDERS:
            for c in CAPABILITIES:
                for ctx in CONTEXTS:
                    for t in TIMES:
                        out.append([p, h, c, ctx, t.isoformat(), _describe(wm.capable(w, h, c, t, ctx, perspective=p))])
    for h in HOLDERS:
        out.append(["is_agent", h, _describe(wm.is_agent(w, h, T(9)))])
        out.append(["as_of", h, _describe(wm.capable(w, h, "can-weigh", T(9), "lab-1",
                                                     as_of=ids["known_before_correction"]))])
        out.append(["plan", h, _describe(wm.capable(ids["plan_tom"], h, "can-weigh", T(14), "lab-1"))])
    return out
