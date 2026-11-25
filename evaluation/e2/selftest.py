"""Stage E2 harness self-test readers (LABS-1.061): synthetic readers that misbehave on purpose, so that the harness
tests can show each failure is detected and kept distinct. They are available only when a run is started with
`selftest=True` (tests, `--selftest`); the question checker refuses them otherwise. They never touch the model's
semantics: each returns what its parameters tell it to.

- `selftest_echo`: returns {"value": params["value"]}, citing params["cite"] as supporting evidence and presenting
  params["derivations"] ([{"rule", "premises"}]) as its derivations.
- `selftest_sleep`: sleeps params["seconds"] (only on the path params["on"] names: "selective", "full" or "both",
  the default), then returns {"slept": seconds}.
- `selftest_path`: returns {"selective": <the path's flag>}, so the two paths always disagree.
- `selftest_raise`: raises by params["kind"]: "documented" a ValueError listed as an established refusal, "proposed" a
  ValueError listed as a refusal whose source is not approved, "undocumented" a ValueError listed nowhere, anything
  else a RuntimeError.
"""

import time

from evaluation.e2.readers import Reader, Refusal


def _echo(wm, p):
    return {"value": p.get("value"), "cite": p.get("cite", []), "derivations": p.get("derivations", [])}


def _sleep(wm, p):
    on = p.get("on", "both")
    if on == "both" or (on == "selective") == wm.selective:
        time.sleep(float(p["seconds"]))
    return {"slept": p["seconds"]}


def _raise(wm, p):
    kind = p.get("kind")
    if kind == "documented":
        raise ValueError("self-test documented refusal")
    if kind == "proposed":
        raise ValueError("self-test proposed refusal")
    if kind == "undocumented":
        raise ValueError("refused on purpose, but not documented (self-test)")
    raise RuntimeError("failed on purpose (self-test)")


REFUSALS = (Refusal("selftest-documented", ValueError, "^self-test documented refusal$", "self-test", True),
            Refusal("selftest-proposed", ValueError, "^self-test proposed refusal$", "self-test", False))


READERS = {r.name: r for r in [
    Reader("selftest_echo", (), ("value", "cite", "derivations"), _echo, lambda a: set(a.get("cite", [])),
           lambda a: [{"rule": d.get("rule"), "premises": list(d.get("premises", [])), "at": f"derivations[{i}]"}
                      for i, d in enumerate(a.get("derivations", []))], timeless=True, worldless=True),
    Reader("selftest_sleep", ("seconds",), ("on",), _sleep, lambda a: set(), timeless=True, worldless=True),
    Reader("selftest_path", (), (), lambda wm, p: {"selective": wm.selective}, lambda a: set(), timeless=True, worldless=True),
    Reader("selftest_raise", (), ("kind",), _raise, refusals=REFUSALS, timeless=True, worldless=True),
]}
