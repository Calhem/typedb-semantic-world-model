"""Safe TypeQL construction (adapted from GUPI's gupi/typeql.py, same author).

Values never go into query text: they are passed as parameters with a `given` header. Only type, role and attribute
labels are written into query text, and they must match LABEL.
"""

import re
from datetime import datetime, timezone

from typedb.driver import Datetime

LABEL = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
VARIABLE = re.compile(r"^[a-z][a-z0-9_]*$")
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def label(name):
    if not isinstance(name, str) or not LABEL.match(name):
        raise ValueError(f"not a valid TypeQL label: {name!r}")
    return name


def _value_type(value):
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "double"
    if isinstance(value, str):
        return "string"
    if isinstance(value, datetime):
        return "datetime-tz"
    raise TypeError(f"unsupported parameter type: {type(value).__name__}")


def to_driver(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("datetimes must be timezone-aware")
        delta = value.astimezone(timezone.utc) - EPOCH
        return Datetime.fromtimestamp(delta.days * 86400 + delta.seconds, delta.microseconds * 1000, offset_seconds=0)
    return value


def from_driver(value):
    """Driver values to Python: datetime-tz arrives as typedb Datetime (microsecond precision kept)."""
    if isinstance(value, Datetime):
        return value.datetime_without_nanos.astimezone(timezone.utc)
    return value


def run(tx, body, params=None):
    params = {k: v for k, v in (params or {}).items()}
    for name in params:
        if not VARIABLE.match(name):
            raise ValueError(f"not a valid parameter name: {name!r}")
    header = ("given " + ", ".join(f"${k}: {_value_type(v)}" for k, v in params.items()) + ";\n") if params else ""
    rows = [{k: to_driver(v) for k, v in params.items()}] if params else None
    return tx.query(header + body, given_rows=rows).resolve()


def rows(tx, body, params=None):
    return list(run(tx, body, params).as_concept_rows())


def opt(row, var):
    """Value of an optional variable in a concept row (None if the `try` block did not match)."""
    concept = row.get(var)
    if concept is None:
        return None
    if concept.is_attribute():
        return from_driver(concept.get_value())
    return concept
