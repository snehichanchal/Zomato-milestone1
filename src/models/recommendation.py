"""
Recommendation data models.

Defines the output structures returned by the RecommendationService
to the presentation layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Recommendation:
    """A single ranked restaurant recommendation with an AI-generated explanation.

    Attributes:
        rank: Position in the ranking (1-based).
        name: Restaurant name.
        cuisine: Joined cuisine string for display.
        rating: Aggregate rating (0.0–5.0).
        estimated_cost: cost_for_two in INR.
        explanation: LLM-generated rationale for this pick.
        restaurant_id: Links back to the canonical Restaurant.id.
    """

    rank: int
    name: str
    cuisine: str
    rating: float
    estimated_cost: int
    explanation: str
    restaurant_id: str = ""


@dataclass
class RecommendationResponse:
    """Full response returned by the recommendation engine.

    Attributes:
        summary: Optional LLM-generated summary paragraph.
        recommendations: Ordered list of Recommendation objects.
        metadata: Contextual information about the request.
    """

    summary: str | None = None
    recommendations: list[Recommendation] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize the full response to a plain dictionary."""
        return {
            "summary": self.summary,
            "recommendations": [
                {
                    "rank": r.rank,
                    "name": r.name,
                    "cuisine": r.cuisine,
                    "rating": r.rating,
                    "estimated_cost": r.estimated_cost,
                    "explanation": r.explanation,
                    "restaurant_id": r.restaurant_id,
                }
                for r in self.recommendations
            ],
            "metadata": self.metadata,
        }
