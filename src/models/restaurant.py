"""
Canonical Restaurant data model.

Defines the standardized schema that all raw dataset records are mapped to
after preprocessing. This is the single source of truth for restaurant
attributes used across filtering, prompt building, and display layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Restaurant:
    """Represents a single restaurant in the canonical schema.

    Attributes:
        id: Stable identifier (dataset index or generated).
        name: Restaurant name.
        location: City or locality (normalized).
        cuisines: List of cuisine types, e.g. ["Italian", "Continental"].
        cost_for_two: Approximate cost for two people (INR).
        rating: Aggregate rating on a 0.0–5.0 scale.
        votes: Number of user votes (popularity signal).
        rest_type: Establishment type, e.g. "Casual Dining", "Cafe".
        budget_tier: Derived tier — "low", "medium", or "high".
    """

    id: str
    name: str
    location: str
    cuisines: list[str] = field(default_factory=list)
    cost_for_two: int = 0
    rating: float = 0.0
    votes: int = 0
    rest_type: str = ""
    budget_tier: str = ""

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def cuisines_display(self) -> str:
        """Return cuisines as a comma-separated string for display."""
        return ", ".join(self.cuisines) if self.cuisines else "Unknown"

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary (useful for JSON / prompt building)."""
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "cuisines": self.cuisines,
            "cost_for_two": self.cost_for_two,
            "rating": self.rating,
            "votes": self.votes,
            "rest_type": self.rest_type,
            "budget_tier": self.budget_tier,
        }

    def to_compact_dict(self) -> dict:
        """Minimal representation sent to the LLM to save tokens."""
        return {
            "id": self.id,
            "name": self.name,
            "cuisines": self.cuisines_display,
            "cost_for_two": self.cost_for_two,
            "rating": self.rating,
        }

    def __repr__(self) -> str:
        return (
            f"Restaurant(id={self.id!r}, name={self.name!r}, "
            f"location={self.location!r}, rating={self.rating}, "
            f"cost={self.cost_for_two}, cuisines={self.cuisines_display!r})"
        )
