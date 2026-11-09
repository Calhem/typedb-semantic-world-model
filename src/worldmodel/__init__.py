"""A small, evidence-aware semantic world model on TypeDB 3 (Core 0.3: World Ontology v0.2)."""

from .keys import proposition_key
from .model import SYSTEM, WorldModel, connect
from .semantics import Window

__all__ = ["WorldModel", "connect", "Window", "SYSTEM", "proposition_key"]
