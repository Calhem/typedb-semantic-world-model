"""LABS-1.065: assemble the E2 corpus from the raw author outputs (benchmark/e2/authoring/raw/), applying only
recorded notation rules and coordinator metadata. No answer value is changed in meaning.

    python3 -I scripts/e2_normalise.py              (from the repository root)

Rules (each change is logged in benchmark/e2/authoring/normalisation-log.json):
- N1: a time written in fixture notation ("T13h16") inside an expected value becomes the ISO 8601 string the answer
  form uses (answer-form.md). Applied only to values, never to parameters, which take fixture notation.
- N2: `before`'s bare answer addressed as `answer` is addressed as `before` (its wrapped answer).
- N3: `interval`'s null answer addressed as `answer` is addressed as the whole answer, `.`.
- N4: `targets` is set by the coordinator from the slot mapping (slots.json -> coordination.json DI); authors never
  saw DI ids. A slot label an author put in `targets` is replaced.
- N5: `convert` takes no `world` parameter.
- R1: fixture repairs to the author's stated intent where the v1.0 fixture format could not express it (listed in
  REPAIRS, with their reason). The verifier checks the repaired fixture blind.
Outputs: benchmark/e2/fixtures/*.json, benchmark/e2/questions/<role>.jsonl, benchmark/e2/calc/author/*.md,
benchmark/e2/authoring/desirability.jsonl.
"""
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
E2 = REPO / "benchmark" / "e2"
RAW = E2 / "authoring" / "raw"
TN = re.compile(r"^T(\d+)(?:h(\d\d))?$")
ROLES = ["S", "F", "M", "C", "P", "X", "XI"]
REPAIRS = {
    # P: the two accounts of the flush were written as two `account` steps, which create two descriptions; the
    # author's questions (P-024, P-025) treat acc-x and acc-y as one description with two accounts (SD-CAU-10).
    "e2-p-accounts": {"reason": "two accounts of one description need `account_again` (v1.1 step)",
                      "steps": {"acc-y": lambda s: {"op": "account_again", "id": "acc-y", "world": s["world"],
                                                    "description": "acc-x", "start": s["start"], "end": s["end"],
                                                    "attester": s["attester"], "accepted_by": s["accepted_by"]}},
                      "params": {"P-025": {"s1": {"b": "acc-x"}}}},
}


def iso(m):
    return datetime(2026, 11, int(m.group(1)), int(m.group(2) or 9), tzinfo=timezone.utc).isoformat()


def times(v, log, where):
    if isinstance(v, str) and TN.match(v):
        log.append({"rule": "N1", "at": where, "from": v, "to": iso(TN.match(v))})
        return iso(TN.match(v))
    if isinstance(v, list):
        return [times(x, log, where) for x in v]
    if isinstance(v, dict):
        return {k: times(x, log, where) for k, x in v.items()}
    return v


def read(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def main():
    coord = json.loads((E2 / "authoring" / "coordination.json").read_text())["families"]
    log = []
    for d in ("fixtures", "questions", "calc/author"):
        shutil.rmtree(E2 / d, ignore_errors=True)
        (E2 / d).mkdir(parents=True)
    desir = []
    for role in ROLES:
        raw = RAW / role
        for f in sorted((raw / "fixtures").glob("*.json")):
            fx = json.loads(f.read_text())
            rep = REPAIRS.get(fx["id"])
            if rep:
                for i, s in enumerate(fx["steps"]):
                    if s.get("id") in rep["steps"]:
                        new = rep["steps"][s["id"]](s)
                        log.append({"rule": "R1", "at": f"{fx['id']}:{s['id']}", "from": s, "to": new,
                                    "reason": rep["reason"]})
                        fx["steps"][i] = new
            (E2 / "fixtures" / f"{fx['id']}.json").write_text(json.dumps(fx, indent=1) + "\n")
        for f in (raw / "calc").glob("*.md"):
            shutil.copy(f, E2 / "calc" / "author" / f.name)
        slots = json.loads((raw / "slots.json").read_text()) if (raw / "slots.json").exists() else {}
        di = {s: d for s, d, _ in coord[role]["targeted"]}
        qs = read(raw / "questions.jsonl") + read(raw / "probes.jsonl")
        out = []
        for q in qs:
            for st in q.get("plan", []):
                where = f"{q['id']}:{st.get('step')}"
                if st.get("reader") == "convert" and "world" in st.get("params", {}):
                    st["params"].pop("world")
                    log.append({"rule": "N5", "at": where})
                exp = st.get("expected")
                if exp:
                    new = {}
                    for path, val in exp.items():
                        p2 = path
                        if path == "answer" and st["reader"] == "before":
                            p2 = "before"
                        elif path == "answer" and st["reader"] == "interval":
                            p2 = "."
                        if p2 != path:
                            log.append({"rule": "N2" if p2 == "before" else "N3", "at": where, "from": path, "to": p2})
                        new[p2] = times(val, log, f"{where}:{p2}")
                    st["expected"] = new
                for qid, by_step in (REPAIRS.get(q.get("scenario"), {}).get("params") or {}).items():
                    if qid == q["id"] and st.get("step") in by_step:
                        for k, v in by_step[st["step"]].items():
                            log.append({"rule": "R1", "at": where, "from": {k: st["params"].get(k)}, "to": {k: v}})
                            st["params"][k] = v
            want = sorted(di[s] for s, qid in slots.items() if qid == q["id"])
            if q.get("targets") != (want or None) and (q.get("targets") or want):
                log.append({"rule": "N4", "at": q["id"], "from": q.get("targets"), "to": want})
            q.pop("targets", None)
            if want:
                q["targets"] = want
            out.append(q)
        (E2 / "questions" / f"{role}.jsonl").write_text("".join(json.dumps(q) + "\n" for q in out))
        desir += read(raw / "desirability.jsonl")
    (E2 / "authoring" / "desirability.jsonl").write_text("".join(json.dumps(x) + "\n" for x in desir))
    (E2 / "authoring" / "normalisation-log.json").write_text(json.dumps(log, indent=1) + "\n")
    from collections import Counter
    print(dict(Counter(x["rule"] for x in log)))


if __name__ == "__main__":
    main()
