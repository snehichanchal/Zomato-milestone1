"""
FastAPI routes for the recommendation engine.

Exposes endpoints for fetching recommendations and dropdown options
(locations, cuisines). All heavy lifting is delegated to the service layer.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.api.schemas import (
    RecommendationRequest,
    RecommendationResponseModel,
    LocationsResponse,
    CuisinesResponse,
)
from src.data.repository import RestaurantRepository
from src.models.preferences import UserPreferences
from src.services.llm_client import LLMClient, LLMClientError
from src.services.recommendation import RecommendationService
from src.services.validator import ValidationError, PreferenceValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["recommendations"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_repo(request: Request) -> RestaurantRepository:
    """Extract the loaded restaurant repository from app state, or 503."""
    repo: RestaurantRepository = request.app.state.repo
    if not repo.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Restaurant data is still loading. Please try again in a moment.",
        )
    return repo


# ---------------------------------------------------------------------------
# POST /api/v1/recommend
# ---------------------------------------------------------------------------

@router.post(
    "/recommend",
    response_model=RecommendationResponseModel,
    responses={
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
        503: {"description": "Repository not loaded"},
    },
)
async def recommend_restaurants(
    request: Request, payload: RecommendationRequest
) -> Any:
    """
    Fetch restaurant recommendations based on user preferences.

    Pipeline: validate → filter → LLM rank → respond.
    """
    repo = _get_repo(request)

    # 1. Validate input using PreferenceValidator (fuzzy location matching etc.)
    validator = PreferenceValidator(
        known_locations=repo.get_locations(),
        known_cuisines=repo.get_cuisines(),
    )
    try:
        preferences: UserPreferences = validator.validate(payload.model_dump())
    except ValidationError as exc:
        logger.warning("Validation error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": [
                    {
                        "loc": ["body", exc.field],
                        "msg": exc.message,
                        "type": "value_error",
                    }
                ]
            },
        )

    # 2. Run the recommendation service
    #    LLMClient may fail if GROQ_API_KEY is missing — that's handled by
    #    the RecommendationService's fallback path.
    try:
        llm_client: LLMClient | None = LLMClient()
    except LLMClientError:
        llm_client = None
        logger.warning("LLM client unavailable — will use heuristic fallback.")

    service = RecommendationService(repository=repo, llm_client=llm_client)
    try:
        response = service.recommend(preferences)
        return response.to_dict()
    except Exception as exc:
        logger.exception("Error generating recommendations.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating recommendations.",
        )


# ---------------------------------------------------------------------------
# GET /api/v1/locations
# ---------------------------------------------------------------------------

@router.get("/locations", response_model=LocationsResponse)
async def get_locations(request: Request) -> dict:
    """Fetch distinct locations for populating dropdowns."""
    repo = _get_repo(request)
    return {"locations": repo.get_locations()}


# ---------------------------------------------------------------------------
# GET /api/v1/cuisines
# ---------------------------------------------------------------------------

@router.get("/cuisines", response_model=CuisinesResponse)
async def get_cuisines(request: Request) -> dict:
    """Fetch distinct cuisines for populating dropdowns."""
    repo = _get_repo(request)
    return {"cuisines": repo.get_cuisines()}
