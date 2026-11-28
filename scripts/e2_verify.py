"""LABS-1.065: blind verification of the E2 gold (no fixture is loaded and no reader is called).

    python3 scripts/e2_verify.py blind <author out dir> <verifier work dir>
    python3 scripts/e2_verify.py compare <author out dir> <verifier out dir> > comparison.json

`blind` copies the author's fixtures and writes `questions-blind.jsonl`:
- every question with its expected **values** replaced by null (the paths stay, so both answers address the same
  fields);
- its evidence sets, premises, derivation, calculation, justification, citations and uncertainty removed;
- every probe with its acceptable outcomes and prohibited conclusion removed.

The verifier derives all of them again from the pack alone.

`compare` matches the two versions field by field, with the harness's own comparison rules and the author's
tolerances (evaluation/e2/values.py):
- expected values;
- each evidence set, as a set;
- admissible premises;
- the probe acceptance set;
- the verifier's own flags (`ill_posed`, `contract_ambiguity`).

Every difference becomes a disagreement for adjudication against the contracts.
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.e2.values import matches  # noqa: E402  (comparison only; no reader, no database)

SETS = ("required_evidence", "admissible_evidence", "required_conflict_evidence", "admissible_conflict_evidence",
        "forbidden_evidence", "admissible_premises")
KEEP = ("id", "family", "class", "subset", "scenario", "question", "competency", "case_type", "convention", "gap")


def read(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()] if Path(p).exists() else []


def blind(author, ver):
    author, ver = Path(author), Path(ver)
    (ver / "fixtures").mkdir(parents=True, exist_ok=True)
    for f in (author / "fixtures").glob("*.json"):
        shutil.copy(f, ver / "fixtures" / f.name)
    out = []
    for q in read(author / "questions.jsonl") + read(author / "probes.jsonl"):
        b = {k: q[k] for k in KEEP if k in q}
        b["plan"] = []
        for st in q.get("plan", []):
            s = {k: st[k] for k in ("step", "reader", "params") if k in st}
            if "expected" in st:
                s["expected"] = {p: None for p in st["expected"]}
            if "tolerance" in st:
                s["tolerance"] = st["tolerance"]
            if "ordered" in st:
                s["ordered"] = st["ordered"]
            b["plan"].append(s)
        if q.get("class") == "G":
            b["probe"] = {"path": (q.get("probe") or {}).get("path", "status"), "accept": None}
            b["prohibited"] = None
        out.append(b)
    (ver / "questions-blind.jsonl").write_text("".join(json.dumps(x) + "\n" for x in out))
    return len(out)


def compare(author, ver):
    a = {q["id"]: q for q in read(Path(author) / "questions.jsonl") + read(Path(author) / "probes.jsonl")}
    v = {q["id"]: q for q in read(Path(ver) / "verified.jsonl")}
    rows, stats = [], {}

    def tally(kind, ok):
        s = stats.setdefault(kind, [0, 0])
        s[0] += ok
        s[1] += 1
    for qid, q in sorted(a.items()):
        w = v.get(qid)
        if w is None:
            rows.append({"id": qid, "field": "*", "why": "not verified"})
            tally("question", False)
            continue
        diffs = []
        for flag in ("ill_posed", "contract_ambiguity"):
            if w.get(flag):
                diffs.append({"field": flag, "verifier": w[flag]})
        if q.get("class") == "G":
            aa = set((q.get("probe") or {}).get("accept", ["UNKNOWN", "NOT_YET_KNOWN", "refusal"]))
            va = set((w.get("probe") or {}).get("accept") or [])
            tally("probe acceptance", aa == va)
            if aa != va:
                diffs.append({"field": "probe.accept", "author": sorted(aa), "verifier": sorted(va)})
        else:
            vsteps = {s.get("step"): s for s in w.get("plan", [])}
            for st in q.get("plan", []):
                ws = vsteps.get(st.get("step"), {})
                for path, val in (st.get("expected") or {}).items():
                    wv = (ws.get("expected") or {}).get(path, "__missing__")
                    tol = (st.get("tolerance") or {}).get(path)
                    ok = wv != "__missing__" and matches(val, wv, tol, path in set(st.get("ordered", [])))
                    kind = "numeric value" if isinstance(val, (int, float, list)) and tol is not None else \
                        "status" if path.endswith("status") else "other value"
                    tally(kind, ok)
                    if not ok:
                        diffs.append({"field": f"{st.get('step')}:{path}", "author": val,
                                      "verifier": None if wv == "__missing__" else wv})
            for k in SETS:
                if k in q or k in w:
                    ok = set(q.get(k) or []) == set(w.get(k) or [])
                    tally("evidence set" if k != "admissible_premises" else "premises", ok)
                    if not ok:
                        diffs.append({"field": k, "author": sorted(q.get(k) or []), "verifier": sorted(w.get(k) or [])})
        tally("question", not diffs)
        rows += [{"id": qid, **d} for d in diffs]
    agreement = {k: {"agree": s[0], "of": s[1], "rate": round(s[0] / s[1], 4) if s[1] else None}
                 for k, s in stats.items()}
    return {"agreement": agreement, "disagreements": rows}


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "blind":
        print(blind(sys.argv[2], sys.argv[3]), "items blinded")
    elif cmd == "compare":
        print(json.dumps(compare(sys.argv[2], sys.argv[3]), indent=1))
