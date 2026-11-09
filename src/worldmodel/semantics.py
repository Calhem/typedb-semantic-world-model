"""Application-level semantics of World Ontology v0.2 (pure Python, no database).

Stage A: time windows. Later stages add attestation records, perspectives, identity and answer statuses.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Window:
    """A time known to lie in [earliest, latest]. `latest=None` means unbounded above; equal bounds mean exact."""
    earliest: datetime
    latest: datetime | None

    @staticmethod
    def at(t):
        return Window(t, t)
