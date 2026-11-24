"""Stage E2 harness: run a scenario's questions in a child process, so that a hard execution budget can stop one.

A Python call cannot be interrupted safely from inside its own process. So each scenario gets a child process
(multiprocessing, "spawn"), which loads the fixture into its own database and answers one plan at a time. The parent
waits for each answer for at most its limit:
- the **selective path** under the hard execution budget (E2-D6: 5 s);
- the **full-load (reference) path** under the reference limit (default 60 s; it has no budget, F-1).
When a limit passes, the parent kills the child, deletes the child's database, and records a timeout. The next
question gets a fresh child with the fixture loaded again, so a stopped question cannot affect the answers that
follow. The parent's wall-clock time (sending the plan to receiving its answer) is what the limits apply to; the child
also reports the readers' own time.
"""

import multiprocessing as mp
import time
import traceback

from worldmodel import connect

CTX = mp.get_context("spawn")


def _recorded(L, fixture):
    """attestation id -> step name for every attestation a reader can cite (as E1's restatement_names: a library-written
    restatement, such as an end() or move() record, is named after the step whose claim it restates), and the set of
    every attestation id recorded in the scenario's worlds."""
    from evaluation.run import restatement_names
    names = restatement_names(L, fixture)
    recorded = set(names)
    worlds = [s["id"] for s in fixture["steps"] if s.get("op") == "world"]
    who = {s.get("attester", "system") for s in fixture["steps"]} | {"system"}
    for w in worlds:
        for p in sorted(who):
            try:
                recorded |= set(L.wm.visible(w, perspective=p))
            except Exception:                                  # a perspective with nothing to see
                continue
    return names, recorded


def child_main(conn, selftest):
    from evaluation.loader import drop, load
    from evaluation.e2.plan import run_plan
    extra = None
    if selftest:
        from evaluation.e2.selftest import READERS as extra
    L = None
    try:
        while True:
            msg = conn.recv()
            kind = msg[0]
            if kind == "load":
                fixture = msg[1]
                t0 = time.perf_counter()
                try:
                    L = load(fixture)
                    names, recorded = _recorded(L, fixture)
                    conn.send(("loaded", {"database": L.wm.database, "names": names, "recorded": sorted(recorded),
                                          "ms": round((time.perf_counter() - t0) * 1000, 1)}))
                except Exception as e:
                    conn.send(("load-error", f"{type(e).__name__}: {' '.join(str(e).split())[:600]}",
                               traceback.format_exc(limit=4)[-1200:]))
            elif kind == "ask":
                _, question, selective = msg
                try:
                    conn.send(("answer", run_plan(L, question, selective, extra)))
                except Exception as e:                         # a harness defect, never a reader's answer
                    conn.send(("harness-error", f"{type(e).__name__}: {e}", traceback.format_exc(limit=6)[-1500:]))
            elif kind == "stop":
                break
    finally:
        if L is not None:
            try:
                drop(L)
            except Exception:
                pass
        conn.close()


class Worker:
    """One child process for one scenario; restarted (and the fixture reloaded) after a timeout."""

    def __init__(self, fixture, selftest=False, load_limit=900.0):
        self.fixture, self.selftest, self.load_limit = fixture, selftest, load_limit
        self.proc = self.conn = self.database = None
        self.names, self.recorded, self.load_ms, self.restarts = {}, set(), [], 0

    def start(self):
        parent, child = CTX.Pipe()
        self.proc = CTX.Process(target=child_main, args=(child, self.selftest), daemon=True)
        self.proc.start()
        child.close()
        self.conn = parent
        self.conn.send(("load", self.fixture))
        if not self.conn.poll(self.load_limit):
            self.kill()
            raise RuntimeError(f"loading fixture {self.fixture['id']!r} took more than {self.load_limit} s")
        reply = self.conn.recv()
        if reply[0] != "loaded":
            self.kill()
            raise RuntimeError(f"fixture {self.fixture['id']!r} did not load: {reply[1]}")
        info = reply[1]
        self.database, self.names, self.recorded = info["database"], info["names"], set(info["recorded"])
        self.load_ms.append(info["ms"])

    def ask(self, question, selective, limit):
        """{"run": plan result, "wall_ms"} or {"timeout": limit} or {"harness_error": ...}."""
        if self.proc is None:
            self.start()
            self.restarts += 1
        t0 = time.perf_counter()
        self.conn.send(("ask", question, selective))
        if not self.conn.poll(limit):
            waited = round((time.perf_counter() - t0) * 1000, 1)
            self.kill()
            return {"timeout": limit, "wall_ms": waited}
        reply = self.conn.recv()
        wall = round((time.perf_counter() - t0) * 1000, 1)
        if reply[0] == "answer":
            return {"run": reply[1], "wall_ms": wall}
        return {"harness_error": reply[1], "trace": reply[2], "wall_ms": wall}

    def kill(self):
        """Stop the child at once and delete its database (from this process, as the child cannot)."""
        if self.proc is not None:
            self.proc.kill()
            self.proc.join(10)
        if self.conn is not None:
            self.conn.close()
        self.proc = self.conn = None
        if self.database:
            d = connect()
            try:
                if d.databases.contains(self.database):
                    d.databases.get(self.database).delete()
            finally:
                d.close()
            self.database = None

    def stop(self):
        if self.proc is not None:
            try:
                self.conn.send(("stop",))
                self.proc.join(60)
            except (BrokenPipeError, OSError):
                pass
            if self.proc.is_alive():
                self.kill()
                return
        self.proc = self.conn = None
        self.database = None
