"""Canonical proposition keys: the structural identity of content (World Ontology v0.2 §4.2).

A key identifies stored content so that it is stored once. It does NOT establish semantic equivalence: two keys that
differ only by co-referring ids are equivalent for a perspective that accepts the identity link, and keys are never
rewritten when identity changes. This module is the only place keys are computed.
"""

import re

ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_.\-]*$")       # no '|', ',', '=' or spaces: they delimit keys


def check_id(value):
    if not isinstance(value, str) or not ID.match(value):
        raise ValueError(f"not a valid id (letters, digits, ':', '_', '.', '-'): {value!r}")
    return value


def as_ids(value):
    return [value] if isinstance(value, str) else list(value)


def number(value):
    """Numbers in keys: 12 significant digits, so 3.5 and 3.50000000000001 are the same parameter (U3 in v0.2)."""
    return format(float(value), ".12g")


def proposition_key(type, roles, params=None):
    """type|role=id,id|...|param=value: roles and multi-player ids sorted, parameters sorted and normalised."""
    parts = [type]
    for role in sorted(roles):
        ids = sorted(check_id(i) for i in as_ids(roles[role]))
        parts.append(f"{role}={','.join(ids)}")
    for name in sorted(params or {}):
        v = params[name]
        parts.append(f"{name}={number(v) if isinstance(v, (int, float)) else v}")
    return "|".join(parts)
