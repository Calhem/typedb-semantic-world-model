"""Stage 3 of the GUPI LongMemEval answer baseline (docs/phase-1c/03-gupi-baseline-protocol.md).

    python -I evaluations/gupi-lme/answer.py estimate --split heldout     # free: real token counts and cost
    python -I evaluations/gupi-lme/answer.py run --split dev --condition K10 --cap-usd 5   # PAID: needs approval

`estimate` builds every prompt from the retrieval output and the dataset and counts tokens; it reads no gold answers.
`run` calls OpenAI (answerer, then LongMemEval's official judge prompt) and refuses to start without OPENAI_API_KEY,
an explicit --cap-usd, and the confirmation flag --i-have-approval. It stops before any call that could exceed the cap.
Standard library only.
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUPI_DATA = Path(os.environ.get("GUPI_DATA", HERE.parents[2] / "typedb-gupi-agent-memory" / ".data" / "longmemeval"))
ANSWERER, JUDGE = "gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06"
PRICE = {ANSWERER: (0.15, 0.60), JUDGE: (2.50, 10.00)}       # USD per million tokens (input, output); confirm before running
MAX_ANSWER_TOKENS = 256

# Frozen answer prompt (protocol 3.2). Changes must be committed before the held-out run.
SYSTEM = ("You are a helpful assistant answering a question about the user's past conversations with you. "
          "Use only the chat history provided. If the history does not contain the answer, say that the "
          "information is not available. Answer concisely.")
USER = "Chat history (oldest first):\n{history}\n\nCurrent date: {date}\nQuestion: {question}\nAnswer:"


def tokens(text):
    """Approximate token count (4 characters per token). The paid run records the provider's exact counts."""
    return (len(text) + 3) // 4


def load(split):
    data = {q["question_id"]: q for q in json.loads((GUPI_DATA / "longmemeval_s_cleaned.json").read_text())}
    oracle = {q["question_id"]: q for q in json.loads((GUPI_DATA / "longmemeval_oracle.json").read_text())}
    retrieval = json.loads((HERE / "results" / f"retrieval-{split}.json").read_text())
    return data, oracle, retrieval


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def obs_id(record_key, content):
    """GUPI main's Observation.id: stable_id("obs", source_id, record_key, content_hash) (gupi/ids.py, gupi/records.py)."""
    parts = ["src:longmemeval", record_key, _sha(content)]
    return "obs:" + _sha(json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=False))[:32]


def turn_index(q):
    """GUPI observation id -> (date, position, role, text), rebuilt exactly as gupi.benchmarks.longmemeval.ingest does."""
    out = {}
    for sid, date, turns in zip(q["haystack_session_ids"], q["haystack_dates"], q["haystack_sessions"]):
        cid = f"lme:{sid}:" + _sha(json.dumps([date, [(t["role"], t["content"]) for t in turns]]))[:12]
        for i, t in enumerate(turns):
            out[obs_id(f"{cid}:{i}", t["content"])] = (date, i, t["role"], t["content"])
    return out


def context(q, oracle_q, condition, top_ids):
    if condition == "O":
        lines = [f"[{d}] {t['role']}: {t['content']}" for d, s in zip(oracle_q["haystack_dates"], oracle_q["haystack_sessions"]) for t in s]
        return "\n".join(lines)
    idx = turn_index(q)
    rows = sorted(idx[oid] for oid in top_ids)          # KeyError here means the id rebuild disagrees with GUPI
    return "\n".join(f"[{d}] {role}: {text}" for d, _, role, text in rows)


def prompts(split, condition):
    data, oracle, retrieval = load(split)
    for row in retrieval["rows"]:
        q = data[row["question_id"]]
        history = context(q, oracle[q["question_id"]], condition, row["top_ids"])
        yield q, USER.format(history=history, date=q["question_date"], question=q["question"])


def estimate(split):
    out = {}
    for cond in ("K10", "O"):
        n, tin = 0, 0
        for _, p in prompts(split, cond):
            n, tin = n + 1, tin + tokens(SYSTEM) + tokens(p)
        tout = n * 100                                     # assumed average answer length
        jin, jout = n * 400, n * 5                         # judge prompt with question, gold and response
        cost = (tin * PRICE[ANSWERER][0] + tout * PRICE[ANSWERER][1] + jin * PRICE[JUDGE][0] + jout * PRICE[JUDGE][1]) / 1e6
        out[cond] = {"questions": n, "answer_input_tokens": tin, "answer_input_tokens_mean": round(tin / max(n, 1)),
                     "assumed_answer_output_tokens": tout, "judge_input_tokens_est": jin, "usd_est": round(cost, 2)}
    out["total_usd_est"] = round(sum(v["usd_est"] for v in out.values()), 2)
    print(json.dumps(out, indent=1))
    return out


def call(model, messages, max_tokens):
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", method="POST",
                                 headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"},
                                 data=json.dumps({"model": model, "messages": messages, "temperature": 0, "max_tokens": max_tokens}).encode())
    with urllib.request.urlopen(req, timeout=120) as r:
        body = json.loads(r.read())
    return body["choices"][0]["message"]["content"], body["usage"]


def judge_prompt(q, response):
    """LongMemEval's official evaluate_qa.py prompts, loaded from a local copy whose hash is checked (not vendored here)."""
    raise SystemExit("Fetch LongMemEval's evaluate_qa.py at a pinned commit into .data and wire get_anscheck_prompt here "
                     "before the paid run (protocol 3.2). Not done: stage 3 has not been approved.")


def run(split, condition, cap):
    if "--i-have-approval" not in sys.argv or not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Refusing: paid stage needs owner approval (--i-have-approval) and OPENAI_API_KEY.")
    raise SystemExit("Paid stage not enabled in this commit.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("estimate", "run"))
    ap.add_argument("--split", choices=("dev", "heldout"), required=True)
    ap.add_argument("--condition", choices=("K10", "O"))
    ap.add_argument("--cap-usd", type=float)
    ap.add_argument("--i-have-approval", action="store_true")
    a = ap.parse_args()
    estimate(a.split) if a.mode == "estimate" else run(a.split, a.condition, a.cap_usd)
