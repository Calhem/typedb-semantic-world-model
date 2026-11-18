"""DI-16 reproduction (LABS-1.046): identity merges two names on a same-as link whose canonical judgement is DISPUTED.

    uv run python -I probes/pre_e_di16_repro.py [<checkout>]

Minimal and self-contained: one throwaway database (wm-probe-di16-*, deleted afterwards), the core and the organisation
profile, the library code unchanged. Steps:
1. hr asserts same-as(bea, b-smith); the system accepts it.
2. clerk denies it (same-as, polarity false); the system accepts the denial too.
3. Two accepted official acts describe one occurrence, one naming bea, the other b-smith.
Printed, for the system perspective now, the system as known before step 2, and the perspectives hr and clerk: the
canonical judgement of the same-as content, whether identity merges the two names, and the judgement of the official
role (which a single-official constraint makes DISPUTED for two different people). Output: .out.txt beside this file.
"""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve() / "src"))
from worldmodel import CORE_MODULES, WorldModel, connect  # noqa: E402
from worldmodel import organisation as org  # noqa: E402


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


T5 = datetime(2026, 11, 5, 9, tzinfo=timezone.utc)
driver = connect()
DB = f"wm-probe-di16-{uuid.uuid4().hex[:8]}"
clock = Clock()
wm = WorldModel.create(DB, driver=driver, modules=CORE_MODULES, clock=clock)
try:
    wm.install_profile("organisation")
    wm.create_world("actual", id="w")
    for p in ("bea", "b-smith", "hr", "clerk"):
        wm.add_entity("person", p, id=p)
    wm.add_entity("organisation", "depot", id="depot")
    wm.add_entity("social-role", "site-manager", id="site-manager")
    wm.add_entity("occurrence", "o-2", id="o-2")
    for who, src in (("bea", "hr"), ("b-smith", "clerk")):
        for a in wm.account_attestations("w", org.act_in_office(wm, "w", who, "site-manager", "depot", T5,
                                                                occurrence="o-2", attester=src, id=f"act-{src}")):
            wm.accept(a)
    link = wm.attest("w", "same-as", {"same": ["bea", "b-smith"]}, until_superseded=True, attester="hr")
    wm.accept(link)                                                         # step 1
    before = clock.now
    denial = wm.deny("w", "same-as", {"same": ["bea", "b-smith"]}, until_superseded=True, attester="clerk")
    wm.accept(denial)                                                       # step 2
    print("same-as assertion by hr and denial by clerk, both accepted by the system")
    for label, kw in (("system, now", {}), ("system, as known before the denial", {"as_of": before}),
                      ("hr (accepts its own assertion; has not reviewed the denial)", {"perspective": "hr"}),
                      ("clerk (accepts its own denial; has not reviewed the assertion)", {"perspective": "clerk"})):
        rec = wm.judgement("w", "same-as", {"same": ["bea", "b-smith"]}, T5, **kw)
        merged = "b-smith" in wm.identity("w", **kw).members("bea")
        role = wm.occurrence("w", "o-2", **kw)["roles"].get("official-act:official", {})
        official = [(c["judgement"], [p["names"] for p in c["players"]]) for c in role.get("constraints", [])]
        expected = rec.judgement.value == "established"
        print(f"\n{label}:")
        print(f"  same-as judgement: {rec.judgement.value} {list(rec.reasons)}; identity merges: {merged}"
              f"{'' if merged == expected else '   <-- DI-16: merges on a link that is not established'}")
        print(f"  official role of o-2: {official}")
finally:
    driver.databases.get(DB).delete()
