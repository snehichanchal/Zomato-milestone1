"""
User Preferences data model.

Defines the validated input structure that users provide to request
restaurant recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# Valid budget tier values
VALID_BUDGETS = ("low", "medium", "high")

# Rating bounds
MIN_RATING_BOUND = 0.0
MAX_RATING_BOUND = 5.0


@dataclass
class UserPreferences:
    """Represents validated user preferences for restaurant recommendations.

    Attributes:
        location: Required. City or locality name.
        budget: Required. One of "low", "medium", "high".
        cuisine: Optional. Primary cuisine preference (e.g. "Italian").
        min_rating: Minimum acceptable rating on a 0.0–5.0 scale.
        additional: Optional free-text for soft preferences
                    (e.g. "family-friendly, outdoor seating").
    """

    location: str
    budget: str
    cuisine: str | None = None
    min_rating: float = 0.0
    additional: str | None = None

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary (useful for prompt building)."""
        return {
            "location": self.location,
            "budget": self.budget,
            "cuisine": self.cuisine,
            "min_rating": self.min_rating,
            "additional": self.additional,
        }

    def __repr__(self) -> str:
        parts = [
            f"location={self.location!r}",
            f"budget={self.budget!r}",
        ]
        if self.cuisine:
            parts.append(f"cuisine={self.cuisine!r}")
        parts.append(f"min_rating={self.min_rating}")
        if self.additional:
            parts.append(f"additional={self.additional!r}")
        return f"UserPreferences({', '.join(parts)})"
