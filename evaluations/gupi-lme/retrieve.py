"""Stage 1-2 of the GUPI LongMemEval answer baseline (docs/phase-1c/03-gupi-baseline-protocol.md): retrieval only.

Runs GUPI's own code, exported read-only from its `main`, against a throwaway database on the isolated TypeDB:

    GUPI_TYPEDB_ADDRESS=127.0.0.1:1735 uv run --project <gupi-export> python -I evaluations/gupi-lme/retrieve.py \
        --split dev --out evaluations/gupi-lme/results/retrieval-dev.json

Writes, per question: the top-10 observation ids from GUPI's keyword retriever, and recall@10 against the gold evidence
ids. Never reads or writes gold answers. Free and local; no model calls.
"""

import argparse
import json
import time

from gupi import evidence
from gupi.benchmarks import common as bcommon
from gupi.benchmarks import longmemeval
from gupi.benchmarks.e2e import common as ecommon
from gupi.memory import Memory
from gupi.typedb.connection import connect

TOP = 10


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=("dev", "heldout"), required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    driver = connect()
    db, clock = ecommon.database_name("wm-lme-baseline"), ecommon.Clock()
    memory = Memory.open(db, packs=("core", "people"), driver=driver, create=True, clock=clock)
    timings = {}
    try:
        items = longmemeval.load(args.split)
        t0 = time.perf_counter()
        by_context = longmemeval.ingest(memory, clock, items)
        timings["ingest_seconds"] = round(time.perf_counter() - t0, 1)
        qs = longmemeval.questions(items, by_context)
        clock.now = clock.now.replace(year=2030)
        rows, t0 = [], time.perf_counter()
        for q in qs:
            s = time.perf_counter()
            ranked = evidence.keyword(memory, q.text, q.contexts, bcommon.DEPTH).ids
            rows.append({
                "question_id": q.id, "category": q.category, "seconds": round(time.perf_counter() - s, 4),
                "top_ids": ranked[:TOP],
                "turn_recall@10": bcommon.metrics(ranked, q.gold["turn"])["recall@10"] if q.gold["turn"] else None,
                "session_recall@10": bcommon.metrics(bcommon.rank_units(ranked, q.unit_of["session"]),
                                                     q.gold["session"])["recall@10"] if q.gold["session"] else None,
            })
        timings["retrieval_seconds"] = round(time.perf_counter() - t0, 1)
        timings["database_bytes"] = ecommon.size(memory)
        timings["peak_python_rss_bytes"] = bcommon.peak_rss_bytes()
        out = {"split": args.split, "questions": len(rows), "retriever": "gupi.evidence.keyword (BM25)",
               "depth": bcommon.DEPTH, "top": TOP, "gupi_git": ecommon.git_state(), "timings": timings, "rows": rows}
        with open(args.out, "w") as f:
            json.dump(out, f, indent=1)
        print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    finally:
        driver.databases.get(db).delete()


if __name__ == "__main__":
    main()
