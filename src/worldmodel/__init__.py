"""A small, evidence-aware semantic world model on TypeDB 3 (Core 0.3: World Ontology v0.2)."""

from .keys import proposition_id, proposition_key
from .model import DYNAMICS_MODULES, PHYSICAL_MODULES, QUALITY_MODULES, SYSTEM, PropositionIdCollision, WorldModel, connect
from .profiles import PROFILES, Profile, ProfileError
from .semantics import Window

__all__ = ["WorldModel", "connect", "Window", "SYSTEM", "proposition_key", "proposition_id", "PropositionIdCollision", "PHYSICAL_MODULES", "DYNAMICS_MODULES", "QUALITY_MODULES", "Profile", "ProfileError", "PROFILES"]
