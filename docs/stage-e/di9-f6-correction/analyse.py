"""LABS-1.058: summarise the F6 correction benchmarks (versions o3 = single query, f6 = two steps; passes A, B and
repeats R1-R5).    python3 -I analyse.py <bench dir>"""
import json, statistics, sys
from collections import defaultdict
from pathlib import Path

B = Path(sys.argv[1])
V = ["o3", "f6"]
DBS = ["worlds-1", "worlds-5", "worlds-10", "perspectives-5", "perspectives-10"]
REP = [f"R{i}" for i in range(1, 6)]
WHERE = "where actual gbx-100 f-workshop"
out = []
status = (B / "status.txt").read_text().splitlines()
steps = [l for l in status if "rc=" in l]
invalid = [l for l in steps if "sleep-events=0" not in l]
out.append(f"## run log: {len(steps)} steps; with sleep events: {len(invalid)}; not on AC power: "
           f"{sum(1 for l in steps if 'AC Power' not in l)}; failed: {sum(1 for l in steps if 'rc=0' not in l)}")
bad = {l.split(":: ")[1] for l in invalid}
for l in invalid:
    out.append(f"- INVALID: {l}")


def load(name, step=None):
    p = B / name
    if step and step in bad:
        return None
    return json.loads(p.read_text()) if p.exists() else None


out.append("\n## Core 0.3 selective, 60 questions: p50 ms (p95) per run [queries/question]")
out.append("| scale | o3 | f6 | f6/o3 (median of p50s) |\n|---|---|---|---|")
for k in (1, 5, 10):
    cells, meds = [], {}
    for v in V:
        rs = [(p, load(f"{p}-{v}-core03-{k}.json", f"{p} {v} core03-{k}")) for p in ["A", "B"] + REP]
        rs = [(p, r) for p, r in rs if r]
        meds[v] = statistics.median(r["selective"]["latency"]["p50"] for _, r in rs)
        cells.append(" / ".join(f"{r['selective']['latency']['p50']:.1f} ({r['selective']['latency']['p95']:.0f})" for _, r in rs)
                     + f" [{rs[0][1]['selective']['queries_per_question']}]")
    out.append(f"| {k}x | " + " | ".join(cells) + f" | x{meds['f6'] / meds['o3']:.2f} |")
r = load("A-f6-core03-10.json")
if r:
    out.append(f"\nlatency keys: {sorted(r['selective']['latency'])}")
    for k in (1, 5, 10):
        for v in V:
            x = load(f"A-{v}-core03-{k}.json")["selective"]["latency"]
            out.append(f"- A {v} {k}x: " + ", ".join(f"{q} {x[q]:.1f}" for q in sorted(x) if isinstance(x[q], (int, float))))


def per_call(p, v, db):
    r = load(f"{p}-{v}-read-wm-probe-scale-{db}.json", f"{p} {v} read wm-probe-scale-{db}")
    return r["per_call"] if r else None


def reader_p50(v, db):
    xs = defaultdict(list)
    for p in ("A", "B"):
        for call, d in (per_call(p, v, db) or {}).items():
            xs[call.split(" ")[0]].extend(d["ms"])
    return {rd: statistics.median(x) for rd, x in xs.items()}


rp = {(v, db): reader_p50(v, db) for v in V for db in DBS}
readers = sorted(rp[("o3", "worlds-1")])
out.append("\n## scale reads: per-reader p50 ms (passes A and B pooled), o3 / f6 (f6/o3)")
out.append("| reader | " + " | ".join(DBS) + " |\n|---|" + "---|" * len(DBS))
for rd in readers:
    out.append(f"| {rd} | " + " | ".join(f"{rp[('o3', db)][rd]:.0f} / {rp[('f6', db)][rd]:.0f} (x{rp[('f6', db)][rd] / rp[('o3', db)][rd]:.2f})"
                                        for db in DBS) + " |")
out.append("\n## totals per round (sum of per-call medians, s, pass A / pass B) and queries per round")
for db in DBS:
    cells = []
    for v in V:
        t = [sum(d["median_ms"] for d in (per_call(p, v, db) or {}).values()) / 1000 for p in ("A", "B")]
        q = sum(d["queries"] for d in per_call("A", v, db).values())
        cells.append(f"{v} {t[0]:.1f}/{t[1]:.1f} s, {q} q")
    out.append(f"- {db}: " + "; ".join(cells))
out.append("\n## readers more than 10 % slower with f6 (pooled p50)")
for db in DBS:
    for rd in readers:
        o, f = rp[("o3", db)][rd], rp[("f6", db)][rd]
        if f > 1.1 * o:
            out.append(f"- {db} {rd}: o3 {o:.1f} ms, f6 {f:.1f} ms (x{f / o:.2f})")
out.append("\n## answers identical to A-o3 (masked)")
for db in DBS:
    a0 = load(f"A-o3-answers-wm-probe-scale-{db}.json")
    cells = []
    for p, v in (("A", "f6"), ("B", "f6"), ("B", "o3")):
        a = load(f"{p}-{v}-answers-wm-probe-scale-{db}.json")
        cells.append(f"{p}-{v} {sum(1 for k in a0 if a and a0[k] == a.get(k))}/{len(a0)}" if a else f"{p}-{v} -")
    out.append(f"- {db}: " + ", ".join(cells))

out.append("\n## where at 92 worlds / 11 worlds, total ms per call (instrumented n=7 in A/B, n=5 in repeats)")
ratios = defaultdict(list)
for v in V:
    cells = []
    for p in ["A", "B"] + REP:
        name, step = (f"{p}-{v}-instrumented.json", f"{p} {v} instrumented") if p in ("A", "B") else (f"{p}-{v}-repeat.json", f"{p} {v} repeat")
        r = load(name, step)
        if r:
            c = {db: r["raw"][f"wm-probe-scale-{db}"]["calls"][WHERE]["total"] for db in ("worlds-1", "worlds-10")}
            x = c["worlds-10"] / c["worlds-1"]
            ratios[v].append(x)
            cells.append(f"{p}: {c['worlds-1']:.0f} -> {c['worlds-10']:.0f} (x{x:.2f})")
    out.append(f"- {v}: " + "; ".join(cells))
    out.append(f"  {v}: {len(ratios[v])} runs, median x{statistics.median(ratios[v]):.2f}, max x{max(ratios[v]):.2f}, "
               f"runs above 1.2: {sum(1 for x in ratios[v] if x > 1.2)}")


def cls(s):
    if "nacc" in s:
        return "superseder acceptance"
    if "has wm-id == $want" in s:
        return "supersession step 2 (new attestations by id)"
    if "supersession (old" in s:
        return "supersession (single query)" if "has stance" in s else "supersession step 1 (pairs)"
    if "acceptance (holder" in s:
        return "acceptance"
    if "links ($role" in s:
        return "roles"
    if "fetch" in s:
        return "head and parameters (fetch)"
    if "branching" in s:
        return "world chain"
    return "other"


out.append("\n## where: query time by kind per round (mean over A, B and repeats), 11 -> 92 worlds")
for v in V:
    agg, tot, n = defaultdict(lambda: defaultdict(lambda: [0, 0.0])), defaultdict(list), 0
    for p in ["A", "B"] + REP:
        r = load(f"{p}-{v}-instrumented.json" if p in ("A", "B") else f"{p}-{v}-repeat.json")
        if not r:
            continue
        n += 1
        for db in ("worlds-1", "worlds-10"):
            R = r["raw"][f"wm-probe-scale-{db}"]
            tot[db].append(R["calls"][WHERE])
            for k, d in R["shapes"].items():
                c, s = k.split(" || ", 1)
                if c == WHERE:
                    agg[cls(s)][db][0] += d["per_round"]
                    agg[cls(s)][db][1] += d["total_ms_per_round"]
    out.append(f"- {v} ({n} runs): " + "; ".join(
        f"{db} total {statistics.median(x['total'] for x in tot[db]):.0f}, stream {statistics.median(x['stream'] for x in tot[db]):.0f}, "
        f"queries {tot[db][0]['queries']}, rows {tot[db][0]['rows']}" for db in ("worlds-1", "worlds-10")))
    for c, d in sorted(agg.items()):
        out.append(f"    {c:46s} " + " | ".join(f"{d[db][0] / n:.0f} q, {d[db][1] / n:.1f} ms" for db in ("worlds-1", "worlds-10"))
                   + f"  (+{(d['worlds-10'][1] - d['worlds-1'][1]) / n:.1f} ms)")
print("\n".join(out))
