"""Stage E1 evaluation (LABS-1.051): check the benchmark's format without answering anything.

    uv run python -I -m evaluation.check [--load]

Checks every question line (required fields, a known template, allowed parameters and expected fields, a known
scenario, evidence ids that name fixture steps, at least one expected field) and every fixture (valid steps). With
--load each fixture is also loaded into a throwaway database through the public writers and dropped again: no
reader is called, so nothing here can reveal an answer.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmark" / "e1"
COMMON_PARAMS = {"world", "t", "as_of", "perspective"}
# template -> (required params, optional params, allowed expected fields)
TEMPLATES = {
    "holds": ({"type", "roles", "t"}, set(), {"judgement", "status"}),
    "value_at": ({"type", "subject", "t"}, set(), {"status", "values"}),
    "exists": ({"thing", "t"}, set(), {"status", "holds"}),
    "same_thing": ({"a", "b"}, set(), {"same", "conflict"}),
    "aliases": ({"x"}, set(), {"members"}),
    "parts": ({"whole", "t"}, set(), {"parts"}),
    "dependencies": ({"dependent", "t"}, set(), {"dependees", "disputed"}),
    "event_role": ({"occurrence", "role"}, set(), {"judgement", "players", "reason", "multiplicity"}),
    "occurrence_status": ({"occurrence", "t"}, set(), {"status"}),
    "office_holders": ({"office", "context", "t"}, set(), {"holders", "conflict"}),
    "capable": ({"holder", "capability", "t"}, {"context"}, {"judgement"}),
    "authorised": ({"holder", "power", "scope", "t"}, set(), {"judgement"}),
    "calibrated": ({"instrument", "t"}, set(), {"judgement"}),
    "move": ({"thing", "to", "t"}, {"actor", "attester"}, {"outcome", "origin"}),
    "officials": ({"event"}, set(), {"officials"}),
}
FIELDS = {"id", "category", "scenario", "question", "template", "params", "expected", "required_evidence",
          "forbidden_evidence", "justification", "spec", "uncertainty", "adversarial", "difficulty"}
CATEGORIES = {"mechanical", "organisation", "laboratory", "temporal", "conflict-provenance", "identity",
              "worlds-perspectives", "cross-domain"}
VOCAB = {"judgement": {"holds": {"established", "disputed", "not holding", "pending", "unknown"},
                       "event_role": {"established", "disputed", "union"},
                       "capable": {"established", "denied", "expired", "not yet effective", "disputed",
                                   "not established"}},
         "status": {"ASSERTED", "STIPULATED", "INFERRED", "DISPUTED", "UNKNOWN", "NOT_YET_KNOWN"},
         "occurrence_status": {"accepted", "denied", "disputed", "not established"},
         "outcome": {"recorded", "refused"}}
VOCAB["judgement"]["authorised"] = VOCAB["judgement"]["calibrated"] = VOCAB["judgement"]["capable"]


def questions():
    for f in sorted((BENCH / "questions").glob("*.jsonl")):
        for n, line in enumerate(f.read_text().splitlines(), 1):
            if line.strip():
                yield f.name, n, json.loads(line)


def fixtures():
    return {json.loads(f.read_text())["id"]: json.loads(f.read_text()) for f in sorted((BENCH / "fixtures").glob("*.json"))}


def problems_of(q, fx, seen):
    out = []
    missing, extra = FIELDS - set(q), set(q) - FIELDS
    if missing:
        out.append(f"missing fields {sorted(missing)}")
    if extra:
        out.append(f"unknown fields {sorted(extra)}")
    if q.get("id") in seen:
        out.append(f"duplicate id {q['id']}")
    seen.add(q.get("id"))
    if q.get("category") not in CATEGORIES:
        out.append(f"unknown category {q.get('category')!r}")
    t = TEMPLATES.get(q.get("template"))
    if t is None:
        return out + [f"unknown template {q.get('template')!r}"]
    required, optional, allowed = t
    params = set(q.get("params", {}))
    if required - params:
        out.append(f"params missing {sorted(required - params)}")
    if params - required - optional - COMMON_PARAMS:
        out.append(f"unknown params {sorted(params - required - optional - COMMON_PARAMS)}")
    if "world" not in params:
        out.append("params missing ['world']")
    exp = q.get("expected", {})
    if not exp:
        out.append("expected is empty")
    if set(exp) - allowed:
        out.append(f"expected fields not allowed for {q['template']}: {sorted(set(exp) - allowed)}")
    if "judgement" in exp and exp["judgement"] not in VOCAB["judgement"].get(q["template"], set()):
        out.append(f"judgement {exp['judgement']!r} not in the {q['template']} vocabulary")
    if "status" in exp:
        vocab = VOCAB["occurrence_status"] if q["template"] == "occurrence_status" else VOCAB["status"]
        if exp["status"] not in vocab:
            out.append(f"status {exp['status']!r} not in {sorted(vocab)}")
    if "outcome" in exp and exp["outcome"] not in VOCAB["outcome"]:
        out.append(f"outcome {exp['outcome']!r} not in {sorted(VOCAB['outcome'])}")
    scenario = fx.get(q.get("scenario"))
    if scenario is None:
        return out + [f"unknown scenario {q.get('scenario')!r}"]
    steps = {s.get("id") for s in scenario["steps"]}
    marks = {s["name"] for s in scenario["steps"] if s.get("op") == "mark"}
    for k in ("required_evidence", "forbidden_evidence"):
        bad = [e for e in q.get(k, []) if e not in steps]
        if bad:
            out.append(f"{k} names no step: {bad}")
    if q.get("params", {}).get("as_of") and q["params"]["as_of"].lstrip("@") not in marks:
        out.append(f"as_of {q['params']['as_of']!r} names no mark")
    worlds = {s["id"] for s in scenario["steps"] if s.get("op") == "world"}
    if q.get("params", {}).get("world") and q["params"]["world"] not in worlds:
        out.append(f"world {q['params']['world']!r} not in the fixture")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--load", action="store_true", help="also load every fixture into a throwaway database")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(ROOT / "src"))
    fx = fixtures()
    bad, seen, count, by_cat = 0, set(), 0, {}
    for fname, n, q in questions():
        count += 1
        by_cat[q.get("category")] = by_cat.get(q.get("category"), 0) + 1
        for p in problems_of(q, fx, seen):
            bad += 1
            print(f"{fname}:{n} {q.get('id')}: {p}")
    if a.load:
        from evaluation.loader import drop, load
        for sid, f in fx.items():
            try:
                drop(load(f))
            except Exception as e:                       # report every fixture, not only the first
                bad += 1
                print(f"fixture {sid}: {type(e).__name__}: {' '.join(str(e).split())[:400]}")
    print(f"{count} questions in {len(by_cat)} categories {dict(sorted(by_cat.items()))}; {len(fx)} fixtures; "
          f"{bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
