"""Fresh baseline of the unchanged Core 0.3 workload (LABS-1.046, Stage E entry criterion P-1): one run.

    uv run --python 3.13 --project <checkout> python -I probes/pre_e_core03_baseline.py <checkout> [bench args...]

Runs `scripts/bench_instrumented.py` (unchanged; it runs the checkout's own `scripts/bench_query_paths.py`: 200
objects, 30 places, 1,000 moves, 60 value_at questions on the selective path and the full load, seed 11) and adds what
the instrumented summary leaves out:
- every question's latency on both paths, in question order (ms), with min, p10, p50, p90, p95, p99 and max;
- the environment: implementation commit, Python, TypeDB driver, TypeDB server image, the Docker VM's CPUs and
  memory, the number of running containers, the host's CPU model and OS version (nothing personal: no host or user
  names, no paths).
The bench's own figures (ingestion, move median / p95, per-path median / p95, queries and attestations per question,
database size, identical answers) are kept as the bench prints them. Prints one JSON object.
"""

import contextlib
import io
import json
import platform
import runpy
import statistics
import subprocess
import sys
import time
from pathlib import Path

here = Path(__file__).resolve().parents[1]
checkout = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(checkout / "src"))
import worldmodel.model as model  # noqa: E402

lat = {True: [], False: []}
_value_at = model.WorldModel.value_at


def timed_value_at(self, *a, **kw):
    t0 = time.perf_counter()
    out = _value_at(self, *a, **kw)
    lat[bool(self.selective)].append((time.perf_counter() - t0) * 1000)
    return out


model.WorldModel.value_at = timed_value_at          # outermost wrapper; bench_instrumented adds its own inside
buf = io.StringIO()
argv = sys.argv
sys.argv = [str(here / "scripts" / "bench_instrumented.py"), str(checkout)] + argv[2:]
with contextlib.redirect_stdout(buf):
    runpy.run_path(sys.argv[0], run_name="__main__")
sys.argv = argv
result = json.loads(buf.getvalue())


def dist(xs):
    s = sorted(xs)
    pct = lambda p: round(s[min(len(s) - 1, int(round(p * (len(s) - 1))))], 1)
    return {"n": len(s), "min": round(s[0], 1), "p10": pct(0.10), "p50": round(statistics.median(s), 1),
            "p90": pct(0.90), "p95": pct(0.95), "p99": pct(0.99), "max": round(s[-1], 1),
            "mean": round(statistics.fmean(s), 1), "latencies_ms": [round(x, 2) for x in xs]}


def sh(*cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:                                                           # noqa: BLE001
        return None


def driver_version():
    try:
        from importlib.metadata import version
        return version("typedb-driver")
    except Exception:                                                           # noqa: BLE001
        return None


docker = str(Path.home() / ".docker" / "bin" / "docker")
info = sh(docker, "info", "--format", "{{.NCPU}} {{.MemTotal}} {{.ContainersRunning}}")
ncpu, mem, running = (info.split() if info else (None, None, None))
result["distribution"] = {"selective": dist(lat[True]), "full": dist(lat[False])}
result["environment"] = {
    "commit": sh("git", "-C", str(checkout), "rev-parse", "--short", "HEAD"),
    "python": sys.version.split()[0],
    "typedb_driver": driver_version(),
    "typedb_server_image": sh(docker, "inspect", "--format", "{{.Config.Image}}", "wm-typedb"),
    "docker_vm_cpus": int(ncpu) if ncpu else None,
    "docker_vm_memory_gib": round(int(mem) / 2 ** 30, 1) if mem else None,
    "containers_running": int(running) if running else None,
    "host_cpu": sh("sysctl", "-n", "machdep.cpu.brand_string"),
    "host_os": f"{platform.system()} {platform.release()}",
}
print(json.dumps(result, indent=1))
