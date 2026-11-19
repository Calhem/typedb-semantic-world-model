"""DI-13 design (LABS-1.046): a prototype of the proposed per-account multiplicity rule, on the design's cases.

    uv run python -I probes/pre_e_di13_rule.py

Pure Python, no database and no library code: it executes rule MP-2 of docs/core-0.4/pre-e-multiplicity-design.md
on the cases M1 to M12 of its section 5, so that the table there is computed, not asserted. The real implementation
would replace the player comparison inside increment D's rule Q (`_event_roles`), keeping everything that decides
*which* accounts are compared (acceptance, describes link established, nearest world, kind classification).
Output: probes/pre_e_di13_rule.out.txt.
"""

UNION, ONE, SET = None, "one", "set"


def applicable(declarations, established_kinds):
    """MP-3: the declaration that applies to one (event type, core role): a kind-scoped one whose kind is established
    wins over an unconditional one; none applicable: no constraint (the role is a union)."""
    scoped = [m for k, m in declarations if k is not None and k in established_kinds]
    if len(set(scoped)) > 1:
        raise ValueError("two applicable kind-scoped declarations disagree")   # refused at declaration time
    if scoped:
        return scoped[0]
    plain = [m for k, m in declarations if k is None]
    return plain[0] if plain else UNION


def judge(multiplicity, accounts, same=None):
    """accounts: {description: [players as stated]} (compared accounts only). same: {name: canonical name}.
    Returns (judgement, players or sets, reason)."""
    canon = lambda x: (same or {}).get(x, x)
    sets = {d: frozenset(canon(p) for p in ps) for d, ps in accounts.items()}
    every = frozenset().union(*sets.values()) if sets else frozenset()
    if multiplicity is UNION:
        return "union", sorted(every), "no applicable constraint"
    if multiplicity == ONE:
        if len(every) <= 1:
            return "established", sorted(every), "one player"
        inside = [d for d, s in sets.items() if len(s) > 1]
        return "DISPUTED", sorted(every), ("several players in one account: " + ", ".join(sorted(inside)) if inside
                                           else "accounts name different players")
    distinct = set(sets.values())
    if len(distinct) <= 1:
        return "established", sorted(every), "every account states the same set"
    return "DISPUTED", {d: sorted(s) for d, s in sorted(sets.items())}, "accounts state different sets"


OFFICIAL = [(None, ONE), ("organisation:co-signed", SET)]          # proposed organisation 0.3 declarations
REMOVED = [("mechanical:one-for-one", ONE)]                        # unchanged mechanical declaration (ER-6)
cases = [
    ("M1 two-technician job, one account names both (event:actor, unconstrained)",
     [], set(), {"job": ["dan", "eve"]}, None),
    ("M2 co-signed act, kind co-signed established, one account names both",
     OFFICIAL, {"organisation:co-signed"}, {"act": ["bea", "cal"]}, None),
    ("M3 the same account, kind not established (ordinary act)",
     OFFICIAL, set(), {"act": ["bea", "cal"]}, None),
    ("M4 ordinary act, two accounts, one official each, different",
     OFFICIAL, set(), {"act-hr": ["bea"], "act-clerk": ["cal"]}, None),
    ("M5 co-signed act, two accounts naming the same two officials",
     OFFICIAL, {"organisation:co-signed"}, {"act-hr": ["bea", "cal"], "act-clerk": ["cal", "bea"]}, None),
    ("M6 co-signed act, one account names both, another only one",
     OFFICIAL, {"organisation:co-signed"}, {"act-hr": ["bea", "cal"], "act-clerk": ["bea"]}, None),
    ("M7 co-signed act, accounts disagree on the second official",
     OFFICIAL, {"organisation:co-signed"}, {"act-hr": ["bea", "cal"], "act-clerk": ["bea", "dan"]}, None),
    ("M8 ordinary act, one account names bea and b-smith, established same-as",
     OFFICIAL, set(), {"act": ["bea", "b-smith"]}, {"b-smith": "bea"}),
    ("M9 ordinary act, the same account, same-as not established",
     OFFICIAL, set(), {"act": ["bea", "b-smith"]}, None),
    ("M10 one-for-one replacement, one account removes two parts",
     REMOVED, {"mechanical:one-for-one"}, {"rep": ["p1", "p2"]}, None),
    ("M11 replacement not one-for-one (multi-part), one account removes two parts",
     REMOVED, set(), {"rep": ["p1", "p2"]}, None),
    ("M12 team sampling, two accounts, different samplers (sampling:sampler, unconstrained)",
     [], set(), {"s-1": ["tom", "ana"], "s-2": ["bo"]}, None),
]
print(f"{'case':86} {'rule':5} judgement")
for name, decls, kinds, accounts, same in cases:
    m = applicable(decls, kinds)
    j, players, why = judge(m, accounts, same)
    print(f"{name:86} {str(m or 'union'):5} {j}: {players} ({why})")
