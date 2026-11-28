"""Stage E2 harness: score one question from its two path runs.

Scored questions (classes A and H). Each failure kind is recorded separately, so none can hide another:
- `timeout`: the selective path did not finish within the hard budget (it was stopped); not completed.
- `harness-error`: the harness itself failed (never a reader's answer).
- `execution-error`: a reader raised an exception that is not a refusal.
- `plan-error`: a plan step's parameter could not be resolved from an earlier answer.
- `unexpected-refusal`: a reader refused where the question expects an answer.
- `incorrect`: an expected field (on any step) differs.
- `fabricated-derivation`: the answer presents a derivation that is not valid (P-4 as amended, LABS-1.063). Its rule
  is not one the model records, it has no premises, or a premise is not **visible** (its fixture step is in a world
  outside the question world's lineage), not **applicable** (not a content type the rule takes) or not **admissible**
  (not in the question's authored `admissible_premises`, which encode usability for the question's perspective,
  `as_of` and t). Existence of the attestation alone never makes a premise admissible. A question whose expected
  answer is **convention-derived** (`convention`, SD-SPA-2, LABS-1.064) admits no derivation at all: any derivation it
  presents is fabricated, whatever its premises, because a mathematical convention rests on no attestation.
- `forbidden-evidence`: the answer cites a forbidden attestation, in any role.
- `alternative-as-support`: an attestation the answer lists as an alternative is also cited as supporting in the same
  component.
- `inadmissible-evidence` / `inadmissible-conflict-evidence`: a supporting / conflicting citation outside that role's
  authored admissible set.
- `missing-evidence` / `missing-conflict-evidence`: a required supporting / conflicting attestation is not cited in that
  role. A missing required attestation is a failure whether or not precision is defined (P-3 as amended).
- `unattributed-evidence`: a supporting or conflicting citation has no fixture-level name. It prevents a verified
  precision pass until it is resolved; it is not an answer failure.

**Evidence roles (P-1 as amended).** Supporting and conflicting evidence are scored apart, each against its own
independently authored sets: `required_evidence` / `admissible_evidence` (supporting) and
`required_conflict_evidence` / `admissible_conflict_evidence` (conflicting). `forbidden_evidence` applies to every role.
Recall and precision are reported per role. `undetermined` evidence (a role depending on an unresolved decision) counts
in no role: it can neither find a required attestation nor improve precision.

`correct` means completed, no execution, plan or harness error, no unexpected refusal, and every expected field on
every step matches. Evidence and derivation failures are reported beside it, as separate criteria (E2-D6).
`failure` is the first kind present in the order above; `failures` lists them all.

Path agreement (F-2, corrected under LABS-1.062):
- `agree`: both paths **answered** (a documented refusal is an answer) and every step's answer is the same. Only this
  satisfies the semantic agreement criterion.
- `consistent-failure`: both paths failed in the same way (an execution or plan error at the same step, of the same
  exception type). Recorded, but it is **not** agreement: no answer was compared.
- `disagree`: the answers differ, or only one path failed, or they failed differently.
- `unverified`: the reference (full-load) run timed out, failed in the harness, or was not run (for example because the
  selective run timed out).

Gap probes (class G) are scored apart (`probe`). A probe passes only when (a) no derivation in any step's answer is
fabricated, whatever the status, and (b) the answer is a status the probe accepts (UNKNOWN-like) or an **established**
documented refusal of the reader, or (when the probe accepts `absent`, LABS-1.064) the probed field is absent: the
approved capability is not implemented, and nothing is fabricated in its place. An undocumented exception is an execution error, and a refusal whose source is not an
approved decision is `unestablished-refusal`: neither passes. A probe with no plan is `not-callable` (listed, not run).
"""

from evaluation.e2.readers import KNOWN_RULES
from evaluation.e2.values import canonical, select, PathError, wrong_fields

ORDER = ["timeout", "harness-error", "execution-error", "plan-error", "unexpected-refusal", "incorrect",
         "fabricated-derivation", "forbidden-evidence", "alternative-as-support", "inadmissible-evidence",
         "inadmissible-conflict-evidence", "missing-evidence", "missing-conflict-evidence", "unattributed-evidence"]
# the content types each recorded rule takes as premises (applicability, P-4)
RULE_INPUTS = {"frame-transform/v1": {"positioned-in", "frame-transform"}}
OP_TYPE = {"position": "positioned-in", "relate_frames": "frame-transform", "anchor_frame": "anchored-to",
           "measure": "has-quality", "claim_cause": "causes", "describe_occurrence": "describes", "connect": "connection",
           "declare_existence": "existence", "create_thing": "existence"}
ANSWER_FAILURES = {"timeout", "harness-error", "execution-error", "plan-error", "unexpected-refusal", "incorrect"}


def base(q):
    return {"id": q["id"], "family": q["family"], "subset": q.get("subset"), "class": q["class"],
            "gap": q.get("gap"), "scenario": q["scenario"], "adversarial": q.get("adversarial"),
            "difficulty": q.get("difficulty"), "targets": q.get("targets") or []}


def step_info(fixture):
    """Fixture step name -> {"op", "type", "world"}, and world -> its base lineage (itself first)."""
    info, base = {}, {}
    for s in (fixture or {}).get("steps", []):
        op = s.get("op")
        if op == "world":
            base[s["id"]] = s.get("base")
        if s.get("id") is None:
            continue
        typ = s.get("type") if op in ("attest", "deny", "correct") else s.get("kind") if op == "claim_effect" \
            else OP_TYPE.get(op, "event" if op in ("account", "record_event", "act_in_office") else op)
        info[s["id"]] = {"op": op, "type": typ, "world": s.get("world")}
    lineage = {}
    for w in base:
        chain, x = [], w
        while x is not None and x not in chain:
            chain.append(x)
            x = base.get(x)
        lineage[w] = chain
    return info, lineage


def fabricated(q, steps, names, fixture=None):
    """Presented derivations that are not valid (P-4 as amended): [{"step", "at", "rule", "why"}]."""
    info, lineage = step_info(fixture)
    admissible = set(q.get("admissible_premises", []))
    out = []
    for st in steps:
        world = (st.get("params") or {}).get("world")
        for d in st.get("derivations", []):
            why = []
            rule = d.get("rule")
            if q.get("convention"):
                why.append(f"a {q['convention']} result is a declared convention: it presents no derivation (SD-SPA-2)")
            if rule not in KNOWN_RULES:
                why.append(f"rule {rule!r} is not a rule the model records")
            premises = d.get("premises") or []
            if not premises:
                why.append("no premises")
            for p in premises:
                name = names.get(p) if p in names else (p if p in info else None)
                if name is None:
                    why.append(f"premise {p} is unattributed (no fixture step recorded it)")
                    continue
                si = info.get(name.split("/")[0])
                if si is None:
                    why.append(f"premise {name}: no fixture step")
                    continue
                if world is not None and si["world"] not in lineage.get(world, [world]):
                    why.append(f"premise {name} is not visible in world {world!r} (recorded in {si['world']!r})")
                if rule in RULE_INPUTS and si["type"] not in RULE_INPUTS[rule]:
                    why.append(f"premise {name} ({si['type']}) is not applicable to {rule}")
                if name not in admissible:
                    why.append(f"premise {name} is not an admissible premise of this question")
            if why:
                out.append({"step": st["step"], "at": d.get("at"), "rule": rule, "why": "; ".join(why)})
    return out


def _check_steps(q, run):
    """(wrong [(step, path, reason)], unexpected refusals [step], first wrong step)."""
    expected = {st["step"]: st for st in q["plan"]}
    wrong, refused, first = [], [], None
    for st in run["steps"]:
        spec = expected[st["step"]]
        exp = spec.get("expected")
        if not exp or "answer" not in st:
            continue
        ans = st["answer"]
        if isinstance(ans, dict) and ans.get("refused") is True and "refused" not in exp:
            refused.append(st["step"])
            first = first or st["step"]
            continue
        bad = wrong_fields(exp, ans, spec.get("tolerance"), set(spec.get("ordered", [])))
        if bad:
            wrong += [(st["step"], p, r) for p, r in bad]
            first = first or st["step"]
    return wrong, refused, first


ROLE_FIELDS = {"supporting": ("required_evidence", "admissible_evidence"),
               "conflicting": ("required_conflict_evidence", "admissible_conflict_evidence")}


def _role(q, role, cited_ids, names):
    req_key, adm_key = ROLE_FIELDS[role]
    required = set(q.get(req_key, []))
    named = {names[a] for a in cited_ids if a in names}
    unattributed = sorted(a for a in cited_ids if a not in names)
    out = {"cited": sorted(named), "unattributed": unattributed, "required": sorted(required),
           "found": sorted(required & named),
           # P-3 as amended: recall is defined whenever something is required; nothing cited gives 0, never n/a
           "recall": round(len(required & named) / len(required), 3) if required else None}
    if adm_key in q:
        admissible = set(q[adm_key]) | required
        inadmissible = sorted(named - admissible)
        out.update(admissible=sorted(admissible), inadmissible=inadmissible,
                   # undefined (None) when nothing named is cited, never 1.0; unverified while anything is unattributed
                   precision=round(1 - len(inadmissible) / len(named), 3) if named else None,
                   precision_verified=not unattributed)
    return out


def evidence(q, steps, names):
    """Evidence by role over every step of the plan (each id counted once per role)."""
    from evaluation.e2.evidence import alternatives_as_support
    cited = {r: set() for r in ("supporting", "conflicting", "alternative", "undetermined")}
    misplaced = []
    for st in steps:
        c = st.get("cited") or {}
        if isinstance(c, list):                              # an old-style (single role) record: supporting
            c = {"supporting": c}
        for r in cited:
            cited[r] |= set(c.get(r, []))
        misplaced += [[st["step"], comp, names.get(i, i)] for comp, i in alternatives_as_support(c)]
    forbidden = set(q.get("forbidden_evidence", []))
    keys = ("required_evidence", "admissible_evidence", "required_conflict_evidence", "admissible_conflict_evidence",
            "forbidden_evidence")
    if not any(k in q for k in keys):
        return None
    ev = {role: _role(q, role, cited[role], names) for role in ROLE_FIELDS}
    named_all = {names[a] for r in ROLE_FIELDS for a in cited[r] if a in names}
    ev.update(forbidden_cited=sorted(forbidden & named_all), alternative_as_support=misplaced,
              undetermined=sorted(names.get(a, a) for a in cited["undetermined"]),
              alternatives=sorted(names.get(a, a) for a in cited["alternative"]))
    return ev


def agreement(sel, full, reason=None):
    if full is None:
        return "unverified", reason or "the reference path was not run"
    if "timeout" in full:
        return "unverified", f"the reference path did not finish within its limit ({full['timeout']} s)"
    if "harness_error" in full:
        return "unverified", f"the reference path failed in the harness: {full['harness_error']}"
    if "run" not in sel:
        return "unverified", "the selective path has no result"
    a, b = sel["run"], full["run"]
    if "error" in a or "error" in b or "plan_error" in a or "plan_error" in b:
        def failure(r):
            if "error" in r:
                return ("execution", r["error"]["step"], r["error"]["message"].split(":", 1)[0])
            if "plan_error" in r:
                return ("plan", r["plan_error"]["step"])
            return None
        fa, fb = failure(a), failure(b)
        if fa is not None and fa == fb:
            return "consistent-failure", f"both paths failed the same way ({fa[0]} error at step {fa[1]!r}); " \
                                         "no answer was compared"
        return "disagree", "an error on one path only, or different errors"
    ans = lambda r: [canonical(s.get("answer")) for s in r["steps"]]
    return ("agree", None) if ans(a) == ans(b) else ("disagree", "the answers differ")


def latency(sel, budget):
    """Selective-path question latency in ms: the readers' own time; a stopped question counts at the budget."""
    if "timeout" in sel:
        return round(budget * 1000, 1), True
    if "run" in sel:
        return sel["run"]["ms"], False
    return None, False


def score(q, sel, full, names, recorded, budget, full_reason=None, fixture=None):
    if q["class"] == "G":
        return probe(q, sel, names, recorded, fixture)
    rec = base(q)
    failures, steps = [], []
    if "timeout" in sel:
        failures.append("timeout")
    elif "harness_error" in sel:
        failures.append("harness-error")
        rec["harness_error"] = sel["harness_error"]
    else:
        run = sel["run"]
        steps = run["steps"]
        if "error" in run:
            failures.append("execution-error")
            rec["error"] = run["error"]
        if "plan_error" in run:
            failures.append("plan-error")
            rec["plan_error"] = run["plan_error"]
        wrong, refused, first = _check_steps(q, run)
        if refused:
            failures.append("unexpected-refusal")
            rec["refused_at"] = refused
        if wrong:
            failures.append("incorrect")
        rec.update(wrong_fields=[{"step": s, "path": p, "reason": r} for s, p, r in wrong], first_wrong_step=first)
        fab = fabricated(q, steps, names, fixture)
        if fab:
            failures.append("fabricated-derivation")
            rec["fabricated"] = fab
        ev = evidence(q, steps, names)
        rec["evidence"] = ev
        if ev:
            sup, con = ev["supporting"], ev["conflicting"]
            if ev["forbidden_cited"]:
                failures.append("forbidden-evidence")
            if ev["alternative_as_support"]:
                failures.append("alternative-as-support")
            if sup.get("inadmissible"):
                failures.append("inadmissible-evidence")
            if con.get("inadmissible"):
                failures.append("inadmissible-conflict-evidence")
            if sup["required"] and sup["recall"] < 1:
                failures.append("missing-evidence")
            if con["required"] and con["recall"] < 1:
                failures.append("missing-conflict-evidence")
            if sup["unattributed"] or con["unattributed"]:
                failures.append("unattributed-evidence")
    failures.sort(key=ORDER.index)
    ms, censored = latency(sel, budget)
    status, why = agreement(sel, full, full_reason)
    rec.update(completed="timeout" not in failures and "harness-error" not in failures,
               correct=not (set(failures) & ANSWER_FAILURES), failure=failures[0] if failures else None,
               failures=failures, latency_ms=ms, latency_censored=censored,
               full_ms=(full or {}).get("run", {}).get("ms"), agreement=status, agreement_reason=why,
               steps=[{k: v for k, v in s.items() if k != "trace"} for s in steps])
    if status == "disagree" and full and "run" in full:
        rec["full_steps"] = [{"step": s["step"], "answer": s.get("answer"), "error": s.get("error")}
                             for s in full["run"]["steps"]]
    return rec


def probe(q, sel, names, recorded, fixture=None):
    """A gap probe: never part of a family's scores."""
    rec = base(q)
    spec = q.get("probe") or {}
    accept = set(spec.get("accept", ["UNKNOWN", "NOT_YET_KNOWN", "refusal"]))
    if not q.get("plan"):
        rec.update(probe="not-callable", passed=None, returned=None,
                   note="no existing reader answers this question; listed with its gap")
        return rec
    if "timeout" in sel:
        rec.update(probe="timeout", passed=False, returned=None)
        return rec
    if "harness_error" in sel:
        rec.update(probe="harness-error", passed=False, returned=sel["harness_error"])
        return rec
    run = sel["run"]
    steps = run["steps"]
    rec["steps"] = [{k: v for k, v in s.items() if k != "trace"} for s in steps]
    rec["latency_ms"] = run["ms"]
    fab = fabricated(q, steps, names, fixture)
    if "error" in run or "plan_error" in run:
        rec.update(probe="execution-error" if "error" in run else "plan-error", passed=False,
                   returned=(run.get("error") or run.get("plan_error"))["message"])
        return rec
    last = steps[-1]["answer"]
    if isinstance(last, dict) and last.get("refused") is True:
        returned = f"refusal: {last.get('refusal')}"
        if not last.get("established"):
            rec.update(probe="fabricated-derivation" if fab else "unestablished-refusal", passed=False,
                       returned=returned, fabricated=fab)
            return rec
        ok = "refusal" in accept
    else:
        try:
            returned = select(last, spec.get("path", "status"))
        except PathError as e:
            if "absent" in accept:
                returned, ok = "absent", True                  # the capability is not there; nothing fabricated
            else:
                returned, ok = f"(no {spec.get('path', 'status')!r}: {e})", False
        else:
            ok = returned in accept
    if fab:
        rec.update(probe="fabricated-derivation", passed=False, returned=returned, fabricated=fab)
    else:
        rec.update(probe="pass" if ok else "fabricated-answer", passed=ok, returned=returned)
    return rec
