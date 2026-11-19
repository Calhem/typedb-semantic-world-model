"""Logical operations (DI-8, LABS-1.036): the unit of atomicity of the world model's writes.

`WorldModel.operation()` opens one; this module holds its record and the decorators that make a writer one operation
(joining the caller's, if any). Kept apart from model.py so the mixins can use it without a circular import.
"""

import functools
import re

from typedb.driver import TransactionType

SCHEMA, WRITE = TransactionType.SCHEMA, TransactionType.WRITE


class OperationError(RuntimeError):
    """An operation could not run or commit as one unit; nothing it wrote is kept."""


class RoleCardinalityError(OperationError):
    """A write named more players of a role than the schema allows in one relation (TypeDB's `@card`, checked when the
    operation commits): refused, nothing written (LABS-1.049). `role` is the role type, `limit` the cardinality and
    `found` the number of players given. Raised instead of the raw database error, which it chains."""

    def __init__(self, role, limit, found, detail):
        self.role, self.limit, self.found = role, limit, found
        super().__init__(f"refused: the role {role} takes {limit} player(s) per description or relation, and {found} "
                         f"were given; nothing was written ({detail})")


_CARD = re.compile(r"Constraint '@card\(([^)]*)\)' has been violated: found (\d+) instances.*?role type '([^']+)'", re.S)


def cardinality_error(exc):
    """The RoleCardinalityError for a TypeDB `[CNT5]` role cardinality violation, or None for any other error."""
    text = " ".join(str(exc).split())
    m = _CARD.search(text) if "CNT5" in text else None
    if not m or "relates constraint violation" not in text:
        return None
    return RoleCardinalityError(m.group(3), m.group(1), int(m.group(2)), text[:300])


class Operation:
    """One logical operation (DI-8, LABS-1.036): every write in it shares one transaction and one recorded time, and
    every read in it sees its own writes. Committed only when the outermost operation ends without an error; any
    failure, at any depth or at commit, leaves nothing written and the recorded-time watermark where it was.
    Obtained with `WorldModel.operation()`; writers called inside one join it instead of opening their own."""
    __slots__ = ("tx", "kind", "recorded_at", "failed")

    def __init__(self, tx, kind):
        self.tx, self.kind, self.recorded_at, self.failed = tx, kind, None, False

    @property
    def schema(self):
        return self.kind == SCHEMA


def atomic(fn):
    """Run a writer as one operation (joining the caller's operation if there is one). For methods of WorldModel and
    for profile functions whose first argument is the model."""
    @functools.wraps(fn)
    def wrapper(model, *args, **kwargs):
        with model.operation():
            return fn(model, *args, **kwargs)
    return wrapper


def atomic_schema(fn):
    """As `atomic`, for a writer that changes the schema: it runs in a schema operation (which can write data too)."""
    @functools.wraps(fn)
    def wrapper(model, *args, **kwargs):
        with model.operation(schema=True):
            return fn(model, *args, **kwargs)
    return wrapper
