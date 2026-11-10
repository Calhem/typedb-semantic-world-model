"""Which part of Core 0.3's main attestation query costs time? One benchmark world, the same questions, variants.

    uv run python -I scripts/experiment_main_query.py

Builds the benchmark world (throwaway database, deleted afterwards), then times variants of the main selective query
(content type located-at, bound subject, world, valid time; actual world only) over the same 80 questions. Every
variant must return the same attestation ids as the baseline. Diagnostic only; nothing here changes the implementation.
"""

import json
import random
import statistics
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldmodel import WorldModel, connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402
from worldmodel.model import READ  # noqa: E402

START = datetime(2026, 11, 9, 8, 0, tzinfo=timezone.utc)
SUBJ = "$subj has wm-id == $sid; $c links ($kr: $subj);"
WORLD = "$w isa world, has wm-id == $world;"
ATT = "$a isa attestation (content: $c, context: $w, attester: $who), has wm-id $aid, has recorded-at $rec;"
AT = "{ not { $a has valid-from-latest $s0; }; } or { $a has valid-from-latest $s1; $s1 <= $at; };"
ATTRS = """$who has wm-id $wid; $c isa! $t; $c has proposition-key $ck;
  $a has stance $st, has polarity $pol, has basis $bs, has end-basis $eb;
  try { $a has valid-from-earliest $sfe; }; try { $a has valid-from-latest $sfl; };
  try { $a has valid-to-earliest $tte; }; try { $a has valid-to-latest $ttl; }; try { $a has credence $cr; };"""
VARIANTS = {
    "baseline (as implemented)": f"match {WORLD} {ATT} $c isa located-at; {SUBJ} {AT} {ATTRS}",
    "subject first": f"match {SUBJ} $c isa located-at; {ATT} {WORLD} {AT} {ATTRS}",
    "no valid-time filter": f"match {WORLD} {ATT} $c isa located-at; {SUBJ} {ATTRS}",
    "no try blocks": f"match {WORLD} {ATT} $c isa located-at; {SUBJ} {AT} $who has wm-id $wid; $c isa! $t; "
                     "$c has proposition-key $ck; $a has stance $st, has polarity $pol, has basis $bs, has end-basis $eb;",
    "no exact type (isa!)": f"match {WORLD} {ATT} $c isa located-at; {SUBJ} {AT} " + ATTRS.replace("$c isa! $t; ", ""),
    "ids only (no attributes)": f"match {WORLD} {ATT} $c isa located-at; {SUBJ} {AT}",
    "fetch stage for attributes": f"match {WORLD} {ATT} $c isa located-at; {SUBJ} {AT} $who has wm-id $wid; "
        "$c has proposition-key $ck; fetch { \"aid\": $aid, \"attester\": $wid, \"content\": $ck, "
        "\"stance\": $a.stance, \"polarity\": $a.polarity, \"basis\": $a.basis, \"end-basis\": $a.end-basis, "
        "\"sfe\": $a.valid-from-earliest, \"sfl\": $a.valid-from-latest, \"tte\": $a.valid-to-earliest, "
        "\"ttl\": $a.valid-to-latest, \"credence\": $a.credence };",
    "attestation pattern without attester": f"match {WORLD} " + ATT.replace(", attester: $who", "") +
                                            f" $c isa located-at; {SUBJ} {AT} " + ATTRS.replace("$who has wm-id $wid; ", ""),
}


def main(objects=200, places=30, moves=1000, questions=80, seed=11):
    rnd = random.Random(seed)
    driver = connect()
    name = f"wm-bench-{uuid.uuid4().hex[:8]}"
    wm = WorldModel.create(name, driver=driver)
    try:
        w = wm.create_world("actual")
        objs = [wm.add_entity("physical-object", f"o{i}") for i in range(objects)]
        pls = [wm.add_entity("place", f"p{i}") for i in range(places)]
        for o in objs:
            wm.attest(w, "located-at", {"located": o, "place": rnd.choice(pls)}, start=START, until_superseded=True)
        t = START
        for _ in range(moves):
            t += timedelta(seconds=rnd.randint(5, 60))
            wm.move(w, rnd.choice(objs), rnd.choice(pls), t)
        asks = [(rnd.choice(objs), START + (t - START) * rnd.random()) for _ in range(questions)]
        out, reference = {}, None
        with driver.transaction(name, READ) as tx:
            for label, query in VARIANTS.items():
                warm = {"world": w, "sid": asks[0][0], "at": asks[0][1]}
                (list(q.run(tx, query, warm).as_concept_documents()) if "fetch {" in query else q.rows(tx, query, warm))
                lat, ids = [], []
                for o, when in asks:
                    params = {"world": w, "sid": o}
                    if "$at" in query:
                        params["at"] = when
                    s = time.perf_counter()
                    if "fetch {" in query:
                        docs = list(q.run(tx, query, params).as_concept_documents())
                        lat.append(time.perf_counter() - s)
                        ids.append(sorted({d["aid"] for d in docs}))
                    else:
                        rows = q.rows(tx, query, params)
                        lat.append(time.perf_counter() - s)
                        ids.append(sorted({q.opt(r, "aid") for r in rows}))
                if label.startswith("baseline"):
                    reference = ids
                same = ids == reference if "valid-time" not in label else None
                out[label] = {"mean_ms": round(statistics.mean(lat) * 1000, 2),
                              "median_ms": round(statistics.median(lat) * 1000, 2), "same_ids_as_baseline": same}
        print(json.dumps(out, indent=1))
    finally:
        driver.databases.get(name).delete()


if __name__ == "__main__":
    main()
