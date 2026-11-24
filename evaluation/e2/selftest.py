"""Stage E2 harness self-test readers (LABS-1.061): synthetic readers that misbehave on purpose, so that the harness
tests can show each failure is detected and kept distinct. They are available only when a run is started with
`selftest=True` (tests, `--selftest`); the question checker refuses them otherwise. They never touch the model's
semantics: each returns what its parameters tell it to.

- `selftest_echo`: returns {"value": params["value"]}, citing params["cite"] as supporting evidence and presenting
  params["derivations"] ([{"rule", "premises"}]) as its derivations.
- `selftest_sleep`: sleeps params["seconds"] (only on the path params["on"] names: "selective", "full" or "both",
  the default), then returns {"slept": seconds}.
- `selftest_path`: returns {"selective": <the path's flag>}, so the two paths always disagree.
- `selftest_raise`: raises the exception named by params["kind"] ("refusal": ValueError, anything else: RuntimeError).
"""

import time

from evaluation.e2.readers import Reader


def _echo(wm, p):
    return {"value": p.get("value"), "cite": p.get("cite", []), "derivations": p.get("derivations", [])}


def _sleep(wm, p):
    on = p.get("on", "both")
    if on == "both" or (on == "selective") == wm.selective:
        time.sleep(float(p["seconds"]))
    return {"slept": p["seconds"]}


def _raise(wm, p):
    if p.get("kind") == "refusal":
        raise ValueError("refused on purpose (self-test)")
    raise RuntimeError("failed on purpose (self-test)")


READERS = {r.name: r for r in [
    Reader("selftest_echo", (), ("value", "cite", "derivations"), _echo, lambda a: set(a.get("cite", [])),
           lambda a: [{"rule": d.get("rule"), "premises": list(d.get("premises", [])), "at": f"derivations[{i}]"}
                      for i, d in enumerate(a.get("derivations", []))], timeless=True, worldless=True),
    Reader("selftest_sleep", ("seconds",), ("on",), _sleep, lambda a: set(), timeless=True, worldless=True),
    Reader("selftest_path", (), (), lambda wm, p: {"selective": wm.selective}, lambda a: set(), timeless=True, worldless=True),
    Reader("selftest_raise", (), ("kind",), _raise, timeless=True, worldless=True),
]}
