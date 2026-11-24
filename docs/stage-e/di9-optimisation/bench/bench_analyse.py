"""Summarise LABS-1.056 benchmarks: versions base / o1 / o2, passes A, B (and repeats R1-R3)."""
import json, statistics, sys, re
from pathlib import Path

B = Path(sys.argv[1])
V = ["base", "o1", "o2"]
DBS = ["worlds-1", "worlds-5", "worlds-10", "perspectives-5", "perspectives-10"]
out = []
status = (B / "status.txt").read_text().splitlines()
invalid = [l for l in status if "sleep-events=" in l and "sleep-events=0" not in l]
out.append(f"## run log: {len(status)} lines; steps with sleep events: {len(invalid)}; not on AC power: "
           f"{sum(1 for l in status if 'rc=' in l and 'AC Power' not in l)}; failed steps: {sum(1 for l in status if 'rc=' in l and 'rc=0' not in l)}")
for l in invalid:
    out.append(f"- INVALID: {l}")


def load(p):
    return json.loads(p.read_text()) if p.exists() else None


def med(xs):
    return statistics.median(xs)


# Core 0.3 selective
out.append("\n## Core 0.3 selective, 60 questions: median ms (p95) [queries/question] per pass")
out.append("| scale | " + " | ".join(V) + " |")
out.append("|---|---|---|---|")
for k in (1, 5, 10):
    cells = []
    for v in V:
        rs = [load(B / f"{p}-{v}-core03-{k}.json") for p in ("A", "B", "R1", "R2", "R3")]
        rs = [r for r in rs if r]
        cells.append(" / ".join(f"{r['selective']['latency']['p50']:.1f} ({r['selective']['latency']['p95']:.0f})" for r in rs)
                     + f" [{rs[0]['selective']['queries_per_question']}]" if rs else "-")
    out.append(f"| {k}x | " + " | ".join(cells) + " |")

# scale reads: per reader p50 pooled over the two passes
def per_call(p, v, db):
    r = load(B / f"{p}-{v}-read-wm-probe-scale-{db}.json")
    return r["per_call"] if r else None


def reader_p50(v, db):
    xs = {}
    for p in ("A", "B"):
        pc = per_call(p, v, db)
        for call, d in (pc or {}).items():
            xs.setdefault(call.split(" ")[0], []).extend(d["ms"])
    return {rd: med(x) for rd, x in xs.items()}


out.append("\n## scale reads: per-reader p50 ms (both passes pooled); o2 vs base ratio")
rp = {(v, db): reader_p50(v, db) for v in V for db in DBS}
readers = sorted(rp[("base", "worlds-1")])
out.append("| reader | " + " | ".join(f"{db} base / o1 / o2 (o2/base)" for db in ("worlds-1", "worlds-10", "perspectives-10")) + " |")
out.append("|---|---|---|---|")
for rd in readers:
    cells = []
    for db in ("worlds-1", "worlds-10", "perspectives-10"):
        b, o1, o2 = (rp[(v, db)].get(rd) for v in V)
        cells.append(f"{b:.0f} / {o1:.0f} / {o2:.0f} (x{o2 / b:.2f})")
    out.append(f"| {rd} | " + " | ".join(cells) + " |")

out.append("\n## scale growth: reader p50 at 10x worlds / 1x worlds, per version")
for v in V:
    g = {rd: rp[(v, "worlds-10")][rd] / rp[(v, "worlds-1")][rd] for rd in readers}
    out.append(f"- {v}: " + ", ".join(f"{rd} x{x:.2f}" for rd, x in sorted(g.items(), key=lambda kv: -kv[1])))
out.append("\n## scale growth: reader p50 at 10x perspectives / 1x, per version")
for v in V:
    g = {rd: rp[(v, "perspectives-10")][rd] / rp[(v, "worlds-1")][rd] for rd in readers}
    out.append(f"- {v}: " + ", ".join(f"{rd} x{x:.2f}" for rd, x in sorted(g.items(), key=lambda kv: -kv[1])))

out.append("\n## totals per round (sum of per-call medians, s) and queries per round, pass A / pass B")
for db in DBS:
    cells = []
    for v in V:
        t = []
        for p in ("A", "B"):
            pc = per_call(p, v, db)
            t.append(sum(d["median_ms"] for d in pc.values()) / 1000 if pc else float("nan"))
        q = sum(d["queries"] for d in per_call("A", v, db).values())
        cells.append(f"{v} {t[0]:.1f}/{t[1]:.1f} s, {q} q")
    out.append(f"- {db}: " + "; ".join(cells))

out.append("\n## 1x (worlds-1) readers slower than base by more than 10 % (o2, pooled p50), with per-pass values")
for rd in readers:
    b, o = rp[("base", "worlds-1")][rd], rp[("o2", "worlds-1")][rd]
    if o > 1.1 * b:
        out.append(f"- {rd}: base {b:.1f} ms, o2 {o:.1f} ms (x{o / b:.2f})")

out.append("\n## query counts per reader per call at worlds-1 (base -> o1 -> o2)")
for rd in readers:
    qs = []
    for v in V:
        pc = per_call("A", v, "worlds-1")
        calls = [d["queries"] for c, d in pc.items() if c.split(" ")[0] == rd]
        qs.append(sum(calls) / len(calls))
    out.append(f"- {rd}: {qs[0]:.1f} -> {qs[1]:.1f} -> {qs[2]:.1f}")

out.append("\n## answers identical to base (masked), per database and version")
for db in DBS:
    a0 = load(B / f"A-base-answers-wm-probe-scale-{db}.json")
    cells = []
    for p, v in (("A", "o1"), ("A", "o2"), ("B", "o1"), ("B", "o2"), ("B", "base")):
        a = load(B / f"{p}-{v}-answers-wm-probe-scale-{db}.json")
        cells.append(f"{p}-{v} {sum(1 for k in a0 if a and a0[k] == a.get(k))}/{len(a0)}" if a else f"{p}-{v} -")
    out.append(f"- {db}: " + ", ".join(cells))

# instrumented: where and DI-9 calls
out.append("\n## instrumented (n=7): median total ms per call, pass A / pass B")
for call in ("where actual gbx-100 f-workshop", "parts actual bay-1", "occurrence actual o-repair", "value_at actual gbx-100",
             "effects_of actual ev-worklog-replacement", "provenance lab s12-b"):
    cells = []
    for v in V:
        vals = []
        for p in ("A", "B"):
            r = load(B / f"{p}-{v}-instrumented.json")
            vals.append("/".join(f"{r['raw'][f'wm-probe-scale-{db}']['calls'][call]['total']:.0f}" for db in ("worlds-1", "worlds-10")) if r else "-")
        cells.append(f"{v} " + " ; ".join(vals))
    out.append(f"- {call} (worlds-1/worlds-10): " + " | ".join(cells))
out.append("\n## where at 92 worlds / 11 worlds (instrumented + repeats)")
for v in V:
    ratios = []
    for p in ("A", "B", "R1", "R2", "R3"):
        r = load(B / (f"{p}-{v}-instrumented.json" if p in ("A", "B") else f"{p}-{v}-repeat.json"))
        if r:
            c = {db: r["raw"][f"wm-probe-scale-{db}"]["calls"]["where actual gbx-100 f-workshop"]["total"] for db in ("worlds-1", "worlds-10")}
            ratios.append(f"{p}: {c['worlds-1']:.0f} -> {c['worlds-10']:.0f} ms (x{c['worlds-10'] / c['worlds-1']:.2f})")
    out.append(f"- {v}: " + "; ".join(ratios))
print("\n".join(out))
