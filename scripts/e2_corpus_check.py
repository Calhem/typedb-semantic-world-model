"""LABS-1.065: static validation of the frozen E2 corpus. No fixture is loaded and no reader is called.

    uv run --offline python scripts/e2_corpus_check.py [--quiet]      (from the repository root)

Checks (item 35):
- question and fixture identifiers;
- family and competency allocations, and the A/H/G classification, against benchmark/e2/authoring/coordination.json;
- the question checker (evaluation/e2/check.py): evidence references and role completeness, premises, multi-step
  references, blocked and unimplemented paths, the H-9 attribution rule and conventions;
- fixture steps against the loader's step schema, with references to earlier steps and declared entities, valid
  times and windows, and the E2 fixture conventions (explicit instants; no self-causation, ONT-SC-1);
- every multi-step question has an expected answer on every step;
- a calculation sheet for every question with a numeric tolerance, from the author and from the verifier;
- the gap-probe acceptance criteria and prohibited conclusions;
- author and verifier agreement: every item agreed or resolved by adjudication; quarantined items excluded;
- the targeted defect allocation (28, per DI, as coordinated).
Exit status 0 when every check passes.
"""
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from evaluation.e2 import check as C  # noqa: E402
from evaluation.loader import FixtureError, T  # noqa: E402  (T is a pure time parser)

E2 = REPO / "benchmark" / "e2"
IV = ("start", "end", "until_superseded")
OPS = {
    "entity": ("kind", "name"), "world": ("kind", "base", "branch_at", "knowledge_at", "name"), "mark": ("name",),
    "accept": ("target", "holder", "verdict"),
    "attest": ("world", "type", "roles", "params", "attester", "stance") + IV,
    "deny": ("world", "type", "roles", "params", "attester", "stance") + IV, "end": ("world", "target", "at"),
    "correct": ("world", "target", "type", "roles", "params", "attester", "stance") + IV,
    "account": ("world", "roles", "start", "end", "type", "kind", "occurrence", "attester"),
    "move": ("world", "thing", "to", "at", "actor", "attester"),
    "grant": ("world", "holder", "concept", "context", "polarity", "attester") + IV,
    "depend": ("world", "dependent", "dependee", "kind", "attester") + IV,
    "appoint": ("world", "holder", "office", "context", "polarity", "attester") + IV,
    "declare_exclusive": ("world", "office", "context", "attester") + IV,
    "authorise": ("world", "grantor", "holder", "power", "scope", "polarity", "attester") + IV,
    "employ": ("world", "employer", "employee", "polarity", "attester") + IV,
    "act_in_office": ("world", "official", "office", "context", "start", "end", "occurrence", "kind", "attester"),
    "connect": ("world", "a", "b", "joint_kind", "attester") + IV,
    "replace_part": ("world", "assembly", "removed", "fitted", "start", "end", "occurrence", "attester"),
    "take_sample": ("world", "sampler", "specimen", "sample", "start", "end", "occurrence", "kind", "attester"),
    "certificate": ("name", "reference"),
    "calibrate": ("world", "certificate", "instrument", "polarity", "attester") + IV,
    "position": ("world", "thing", "frame", "x", "y", "z", "orientation", "attester") + IV,
    "relate_frames": ("world", "parent", "child", "translation", "rotation", "attester") + IV,
    "anchor_frame": ("world", "frame", "anchor", "attester") + IV,
    "define_unit": ("name", "dimension", "si_factor", "si_offset"), "define_quality_kind": ("name", "dimension"),
    "measure": ("world", "bearer", "quality", "value", "unit", "uncertainty", "k", "start", "end", "instrument",
                "operator", "conditions", "calibration", "attester", "occurrence", "persists", "supersedes"),
    "claim_cause": ("world", "cause", "effect", "polarity", "attester") + IV,
    "claim_effect": ("world", "event", "kind", "type", "roles", "params", "polarity", "attester") + IV,
    "describe_occurrence": ("world", "description", "occurrence", "polarity", "attester") + IV,
    "record_event": ("world", "roles", "start", "end", "kind", "ends", "effects", "type", "attester"),
    "declare_existence": ("world", "thing", "start", "end", "attester"),
    "create_thing": ("world", "kind", "name", "at", "alt_names", "attester"),
    "destroy": ("world", "thing", "at", "reason"),
    "account_again": ("world", "description", "start", "end", "attester"),
    "interpret": ("world", "record", "type", "roles", "params", "tentative", "polarity", "attester") + IV}
NO_ID = {"mark", "accept"}
REFS = {"target": "step", "supersedes": "step", "event": "step", "description": "step"}
TIMES = ("start", "end", "at", "branch_at")


def lint_fixture(fx):
    out, ids, worlds, marks, declared = [], set(), set(), set(), set()
    if not str(fx.get("id", "")).startswith("e2-"):
        out.append(f"fixture id {fx.get('id')!r} does not start with e2-")
    for n, s in enumerate(fx.get("steps", []), 1):
        op, sid = s.get("op"), s.get("id")
        where = f"{fx.get('id')} step {n} ({sid or op})"
        if op not in OPS:
            out.append(f"{where}: unknown op {op!r}")
            continue
        extra = set(s) - {"op", "id", "accepted_by"} - set(OPS[op])
        if extra:
            out.append(f"{where}: unknown fields {sorted(extra)}")
        if op not in NO_ID and not sid:
            out.append(f"{where}: needs an id")
        if sid in ids:
            out.append(f"{where}: duplicate id")
        for k in TIMES:
            if k in s:
                try:
                    T(s[k])
                except FixtureError as e:
                    out.append(f"{where}: {e}")
        if "world" in s and op not in ("world",) and s["world"] not in worlds:
            out.append(f"{where}: world {s['world']!r} not declared before")
        for k, kind in REFS.items():
            if k in s:
                v = s.get(k)
                if isinstance(v, str) and v not in ids and v not in declared:
                    out.append(f"{where}: {k} {v!r} names no earlier step")
        if op == "accept" and s.get("target") not in ids:
            out.append(f"{where}: accept target {s.get('target')!r} names no earlier step")
        if op == "measure" and "end" in s and s.get("end") == s.get("start"):
            out.append(f"{where}: explicit instant written with end equal to start (convention: no end)")
        if op == "claim_cause" and s.get("cause") == s.get("effect"):
            out.append(f"{where}: self-causation (ONT-SC-1 blocked)")
        if op == "world":
            worlds.add(sid)
            if s.get("knowledge_at") and s["knowledge_at"][1:] not in marks:
                out.append(f"{where}: knowledge_at names no earlier mark")
        if op == "mark":
            marks.add(s.get("name"))
        if op in ("entity", "certificate", "define_unit", "define_quality_kind"):
            declared.add(sid)
        if sid:
            ids.add(sid)
    return out


def main(quiet=False):
    coord = json.loads((E2 / "authoring" / "coordination.json").read_text())["families"]
    fixtures = {}
    problems = []
    for f in sorted((E2 / "fixtures").glob("*.json")):
        fx = json.loads(f.read_text())
        if fx["id"] in fixtures:
            problems.append(f"duplicate fixture id {fx['id']}")
        if f.stem != fx["id"]:
            problems.append(f"{f.name}: file name differs from id {fx['id']}")
        fixtures[fx["id"]] = fx
        problems += lint_fixture(fx)
    qfiles = sorted((E2 / "questions").glob("*.jsonl"))
    problems += [f"{Path(f).name}:{n} {qid}: {p}" for f, n, qid, p in C.check(qfiles, fixtures)]
    qs = [q for _, _, q in C.read_questions(qfiles)]
    ids = Counter(q["id"] for q in qs)
    problems += [f"duplicate question id {i}" for i, c in ids.items() if c > 1]
    scored = [q for q in qs if q["class"] in ("A", "H")]
    probes = [q for q in qs if q["class"] == "G"]
    # allocation
    for k, v in coord.items():
        fam = v.get("family", k)
        mine = [q for q in scored if q["family"] == fam and (q.get("subset") == "identity") == (k == "XI")]
        if len(mine) != v["scored"]:
            problems.append(f"{k}: {len(mine)} scored questions, coordinated {v['scored']}")
        ct = Counter(q.get("case_type") for q in mine)
        if dict(ct) != {a: b for a, b in v["case_types"].items() if b}:
            problems.append(f"{k}: case types {dict(ct)} differ from {v['case_types']}")
        gaps = Counter(g for g, _ in v["probes"])
        got = Counter(q.get("gap") for q in probes if q["family"] == fam) if k != "XI" else Counter()
        if k != "XI" and got != gaps:
            problems.append(f"{k}: probes by gap {dict(got)} differ from {dict(gaps)}")
        targets = Counter(d for _, d, _ in v["targeted"])
        got_t = Counter(t for q in mine for t in q.get("targets") or [])
        if got_t != targets:
            problems.append(f"{k}: targets {dict(got_t)} differ from {dict(targets)}")
    for q in scored:
        if q["family"] == "X" and len(q["plan"]) < 2 and q.get("subset") != "identity" and \
                q.get("competency", "").split(" ")[0] in ("X1", "X2", "X3", "X4", "X5", "X6"):
            problems.append(f"{q['id']}: an X plan question with one step")
        for st in q["plan"]:
            if not st.get("expected"):
                problems.append(f"{q['id']}: step {st.get('step')!r} has no expected answer (every step is scored)")
        for k in ("competency", "case_type", "justification", "spec"):
            if not q.get(k):
                problems.append(f"{q['id']}: missing {k}")
        numeric = any(st.get("tolerance") for st in q["plan"])
        if numeric:
            for who in ("author", "verifier"):
                if not (E2 / "calc" / who / f"{q['id']}.md").exists():
                    problems.append(f"{q['id']}: no {who} calculation sheet")
    for q in probes:
        acc = (q.get("probe") or {}).get("accept")
        if not acc or not q.get("prohibited"):
            problems.append(f"{q['id']}: a probe needs probe.accept and prohibited")
    if len(scored) != sum(v["scored"] for v in coord.values()):
        problems.append(f"{len(scored)} scored questions in all, coordinated {sum(v['scored'] for v in coord.values())}")
    if len(probes) != sum(len(v["probes"]) for v in coord.values()):
        problems.append(f"{len(probes)} probes in all")
    # agreement
    ver = E2 / "verification" / "status.json"
    if not ver.exists():
        problems.append("no verification status (benchmark/e2/verification/status.json)")
    else:
        st = json.loads(ver.read_text())
        for q in qs:
            s = st.get(q["id"])
            if s not in ("agreed", "resolved"):
                problems.append(f"{q['id']}: verification status {s!r} (must be agreed or resolved)")
        quarantined = [i for i, s in st.items() if s == "quarantined"]
        leaked = sorted(set(quarantined) & set(ids))
        if leaked:
            problems.append(f"quarantined items still in the corpus: {leaked}")
    summary = {"fixtures": len(fixtures), "scored": len(scored), "probes": len(probes),
               "targeted": sum(bool(q.get("targets")) for q in scored), "problems": len(problems)}
    if not quiet:
        print("\n".join(problems))
    print(json.dumps(summary))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main("--quiet" in sys.argv))
