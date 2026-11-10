"""Canonical proposition keys: the structural identity of content (World Ontology v0.2 §4.2).

A key identifies stored content so that it is stored once. It does NOT establish semantic equivalence: two keys that
differ only by co-referring ids are equivalent for a perspective that accepts the identity link, and keys are never
rewritten when identity changes. This module is the only place keys are computed.
"""

import hashlib
import re

ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_.\-]*$")       # no '|', ',', '=' or spaces: they delimit keys


def check_id(value):
    if not isinstance(value, str) or not ID.match(value):
        raise ValueError(f"not a valid id (letters, digits, ':', '_', '.', '-'): {value!r}")
    return value


PROPOSITION_ID = re.compile(r"^p:[0-9a-f]{24}$")


def check_new_id(value):
    """An id for a new world, thing, event description or attestation. Ids in the proposition-id form are reserved so
    that one id never names both a proposition and something else (wm-id keys are per type in TypeDB)."""
    check_id(value)
    if PROPOSITION_ID.match(value):
        raise ValueError(f"ids of the form p:<24 hex> are reserved for propositions: {value!r}")
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


def proposition_id(key):
    """The immutable identifier of the proposition with this canonical key: 'p:' + 24 hex characters (96 bits) of its
    SHA-256. Deterministic, so the same content always has the same id; a collision between different keys is detected
    on write (WorldModel raises) and also rejected by TypeDB's @key."""
    return "p:" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
