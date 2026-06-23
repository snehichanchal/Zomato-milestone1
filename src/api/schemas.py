"""
Pydantic schemas for the FastAPI layer.

Defines the request and response structures for the recommendation API,
validating input types before they reach the service layer.

Uses Pydantic v2 conventions (``json_schema_extra`` for examples).
"""

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class RecommendationRequest(BaseModel):
    """Request payload for fetching recommendations."""

    location: str = Field(
        ...,
        min_length=1,
        description="City or locality name",
        json_schema_extra={"examples": ["Bellandur"]},
    )
    budget: str = Field(
        ...,
        description="Budget tier: low, medium, or high",
        json_schema_extra={"examples": ["medium"]},
    )
    cuisine: Optional[str] = Field(
        None,
        description="Primary cuisine preference",
        json_schema_extra={"examples": ["Italian"]},
    )
    min_rating: float = Field(
        0.0,
        ge=0.0,
        le=5.0,
        description="Minimum acceptable rating (0.0–5.0)",
        json_schema_extra={"examples": [4.0]},
    )
    additional: Optional[str] = Field(
        None,
        description="Soft preferences (free text)",
        json_schema_extra={"examples": ["outdoor seating, family-friendly"]},
    )


# ---------------------------------------------------------------------------
# Response — Recommendations
# ---------------------------------------------------------------------------

class RecommendationItem(BaseModel):
    """A single ranked restaurant recommendation."""

    rank: int
    name: str
    cuisine: str
    rating: float
    estimated_cost: int
    explanation: str
    restaurant_id: str


class RecommendationResponseModel(BaseModel):
    """Full response containing ranked recommendations and metadata."""

    summary: Optional[str] = None
    recommendations: List[RecommendationItem]
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# Response — Dropdown Lists
# ---------------------------------------------------------------------------

class LocationsResponse(BaseModel):
    """Response containing a list of available locations."""

    locations: List[str]


class CuisinesResponse(BaseModel):
    """Response containing a list of available cuisines."""

    cuisines: List[str]


# ---------------------------------------------------------------------------
# Response — Errors
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Structured error information for a single validation failure."""

    loc: List[str] = Field(
        ..., description="Path to the field that caused the error"
    )
    msg: str = Field(..., description="Human-readable error message")
    type: str = Field(..., description="Error category identifier")


class ErrorResponse(BaseModel):
    """Standard error envelope returned on validation or server errors."""

    detail: Any = Field(
        ...,
        description="Error detail — string for generic errors, list for validation errors",
    )
