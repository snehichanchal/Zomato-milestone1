"""
API tests for Phase 4 Part 1 — FastAPI routes.

Uses ``httpx.AsyncClient`` with ``ASGITransport`` to test all API routes.
All services (repository, LLM client) are mocked so that tests are:
  • Fast (no network calls, no dataset loading)
  • Deterministic (fixed data every run)
  • Isolated (each test gets a clean mock state)
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.data.repository import RestaurantRepository
from src.models.restaurant import Restaurant
from src.models.preferences import UserPreferences
from src.models.recommendation import Recommendation, RecommendationResponse
from src.services.filter import FilterResult


# ---------------------------------------------------------------------------
# Fixtures — Mock data
# ---------------------------------------------------------------------------

MOCK_RESTAURANTS = [
    Restaurant(
        id="r1",
        name="Curry Palace",
        location="Bellandur",
        cuisines=["North Indian", "Chinese"],
        cost_for_two=800,
        rating=4.5,
        votes=320,
        rest_type="Casual Dining",
        budget_tier="medium",
    ),
    Restaurant(
        id="r2",
        name="Pizza Paradise",
        location="Bellandur",
        cuisines=["Italian", "Continental"],
        cost_for_two=1200,
        rating=4.2,
        votes=210,
        rest_type="Casual Dining",
        budget_tier="medium",
    ),
    Restaurant(
        id="r3",
        name="Street Bites",
        location="Bellandur",
        cuisines=["Street Food", "North Indian"],
        cost_for_two=300,
        rating=3.9,
        votes=150,
        rest_type="Quick Bites",
        budget_tier="low",
    ),
    Restaurant(
        id="r4",
        name="Sushi Zen",
        location="Koramangala",
        cuisines=["Japanese", "Sushi"],
        cost_for_two=2500,
        rating=4.7,
        votes=420,
        rest_type="Fine Dining",
        budget_tier="high",
    ),
    Restaurant(
        id="r5",
        name="Biryani House",
        location="Bellandur",
        cuisines=["Mughlai", "Biryani"],
        cost_for_two=600,
        rating=4.0,
        votes=180,
        rest_type="Casual Dining",
        budget_tier="medium",
    ),
]

MOCK_LOCATIONS = sorted({r.location for r in MOCK_RESTAURANTS})
MOCK_CUISINES = sorted(
    {c for r in MOCK_RESTAURANTS for c in r.cuisines}
)


def _build_mock_repo() -> MagicMock:
    """Return a mock RestaurantRepository that behaves like a loaded repo."""
    mock = MagicMock(spec=RestaurantRepository)
    mock.is_loaded = True
    mock.get_all.return_value = list(MOCK_RESTAURANTS)
    mock.get_locations.return_value = MOCK_LOCATIONS
    mock.get_cuisines.return_value = MOCK_CUISINES
    mock.count.return_value = len(MOCK_RESTAURANTS)
    return mock


def _build_mock_recommendation_response() -> RecommendationResponse:
    """Build a fixed RecommendationResponse for testing."""
    return RecommendationResponse(
        summary="Top picks for you in Bellandur.",
        recommendations=[
            Recommendation(
                rank=1,
                name="Curry Palace",
                cuisine="North Indian, Chinese",
                rating=4.5,
                estimated_cost=800,
                explanation="Highly rated with a great variety of Indian and Chinese dishes.",
                restaurant_id="r1",
            ),
            Recommendation(
                rank=2,
                name="Pizza Paradise",
                cuisine="Italian, Continental",
                rating=4.2,
                estimated_cost=1200,
                explanation="Best Italian options in the area with lovely ambience.",
                restaurant_id="r2",
            ),
        ],
        metadata={
            "candidates_considered": 4,
            "total_restaurants": 5,
            "filters_applied": {"location": "Bellandur", "budget": "medium"},
            "model": "llama-3.3-70b-versatile",
        },
    )


@pytest.fixture(autouse=True)
def _inject_mock_repo():
    """Inject a mocked repository into app.state for every test."""
    mock_repo = _build_mock_repo()
    original_repo = getattr(app.state, "repo", None)
    app.state.repo = mock_repo
    yield mock_repo
    app.state.repo = original_repo


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _client() -> AsyncClient:
    """Create a test client pointing at the app."""
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


# ===================================================================
# GET /api/v1/locations
# ===================================================================

@pytest.mark.asyncio
async def test_get_locations_returns_sorted_list():
    """GET /locations returns a sorted list of distinct locations."""
    async with _client() as ac:
        resp = await ac.get("/api/v1/locations")

    assert resp.status_code == 200
    data = resp.json()
    assert "locations" in data
    assert data["locations"] == MOCK_LOCATIONS
    assert isinstance(data["locations"], list)


@pytest.mark.asyncio
async def test_get_locations_returns_503_when_repo_not_loaded():
    """GET /locations returns 503 if the dataset hasn't loaded yet."""
    app.state.repo = MagicMock(spec=RestaurantRepository, is_loaded=False)

    async with _client() as ac:
        resp = await ac.get("/api/v1/locations")

    assert resp.status_code == 503
    assert "loading" in resp.json()["detail"].lower()


# ===================================================================
# GET /api/v1/cuisines
# ===================================================================

@pytest.mark.asyncio
async def test_get_cuisines_returns_sorted_list():
    """GET /cuisines returns a sorted, deduplicated list."""
    async with _client() as ac:
        resp = await ac.get("/api/v1/cuisines")

    assert resp.status_code == 200
    data = resp.json()
    assert "cuisines" in data
    assert data["cuisines"] == MOCK_CUISINES


@pytest.mark.asyncio
async def test_get_cuisines_returns_503_when_repo_not_loaded():
    """GET /cuisines returns 503 if the dataset hasn't loaded yet."""
    app.state.repo = MagicMock(spec=RestaurantRepository, is_loaded=False)

    async with _client() as ac:
        resp = await ac.get("/api/v1/cuisines")

    assert resp.status_code == 503


# ===================================================================
# POST /api/v1/recommend — Happy paths
# ===================================================================

@pytest.mark.asyncio
async def test_recommend_success_with_mocked_service():
    """POST /recommend returns 200 with recommendations when pipeline succeeds."""
    mock_response = _build_mock_recommendation_response()

    with patch(
        "src.api.routes.RecommendationService"
    ) as MockService, patch(
        "src.api.routes.LLMClient"
    ):
        MockService.return_value.recommend.return_value = mock_response

        async with _client() as ac:
            resp = await ac.post(
                "/api/v1/recommend",
                json={
                    "location": "Bellandur",
                    "budget": "medium",
                    "min_rating": 4.0,
                },
            )

    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) == 2
    assert data["recommendations"][0]["name"] == "Curry Palace"
    assert data["summary"] == "Top picks for you in Bellandur."
    assert data["metadata"]["candidates_considered"] == 4


@pytest.mark.asyncio
async def test_recommend_includes_metadata():
    """Response metadata contains expected keys."""
    mock_response = _build_mock_recommendation_response()

    with patch(
        "src.api.routes.RecommendationService"
    ) as MockService, patch(
        "src.api.routes.LLMClient"
    ):
        MockService.return_value.recommend.return_value = mock_response

        async with _client() as ac:
            resp = await ac.post(
                "/api/v1/recommend",
                json={"location": "Bellandur", "budget": "medium"},
            )

    assert resp.status_code == 200
    meta = resp.json()["metadata"]
    assert "candidates_considered" in meta
    assert "total_restaurants" in meta
    assert "filters_applied" in meta


@pytest.mark.asyncio
async def test_recommend_with_optional_cuisine():
    """Providing an optional cuisine field still returns 200."""
    mock_response = _build_mock_recommendation_response()

    with patch(
        "src.api.routes.RecommendationService"
    ) as MockService, patch(
        "src.api.routes.LLMClient"
    ):
        MockService.return_value.recommend.return_value = mock_response

        async with _client() as ac:
            resp = await ac.post(
                "/api/v1/recommend",
                json={
                    "location": "Bellandur",
                    "budget": "medium",
                    "cuisine": "Italian",
                    "min_rating": 4.0,
                    "additional": "Rooftop seating",
                },
            )

    assert resp.status_code == 200
    assert len(resp.json()["recommendations"]) >= 1


@pytest.mark.asyncio
async def test_recommend_fallback_when_llm_unavailable():
    """If LLMClient raises, the route still returns 200 via heuristic fallback."""
    from src.services.llm_client import LLMClientError

    fallback_response = RecommendationResponse(
        summary="Ranked by rating (AI unavailable).",
        recommendations=[
            Recommendation(
                rank=1,
                name="Curry Palace",
                cuisine="North Indian, Chinese",
                rating=4.5,
                estimated_cost=800,
                explanation="Highly rated North Indian, Chinese restaurant in Bellandur.",
                restaurant_id="r1",
            ),
        ],
        metadata={
            "candidates_considered": 4,
            "total_restaurants": 5,
            "filters_applied": {"location": "Bellandur", "budget": "medium"},
            "model": "heuristic-fallback",
        },
    )

    with patch(
        "src.api.routes.LLMClient", side_effect=LLMClientError("No API key")
    ), patch(
        "src.api.routes.RecommendationService"
    ) as MockService:
        MockService.return_value.recommend.return_value = fallback_response

        async with _client() as ac:
            resp = await ac.post(
                "/api/v1/recommend",
                json={"location": "Bellandur", "budget": "medium"},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["model"] == "heuristic-fallback"


# ===================================================================
# POST /api/v1/recommend — Validation failures
# ===================================================================

@pytest.mark.asyncio
async def test_recommend_missing_location():
    """Missing required 'location' returns 422."""
    async with _client() as ac:
        resp = await ac.post(
            "/api/v1/recommend",
            json={"budget": "medium"},
        )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_recommend_missing_budget():
    """Missing required 'budget' returns 422."""
    async with _client() as ac:
        resp = await ac.post(
            "/api/v1/recommend",
            json={"location": "Bellandur"},
        )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_recommend_invalid_budget_value():
    """Invalid budget value returns 422 from the validator."""
    async with _client() as ac:
        resp = await ac.post(
            "/api/v1/recommend",
            json={
                "location": "Bellandur",
                "budget": "super_expensive",
                "min_rating": 4.0,
            },
        )

    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body
    # The error should reference the 'budget' field
    details = body["detail"]
    assert isinstance(details, list)
    budget_errors = [d for d in details if "budget" in str(d.get("loc", []))]
    assert len(budget_errors) >= 1


@pytest.mark.asyncio
async def test_recommend_rating_out_of_range():
    """Rating > 5.0 is rejected by Pydantic schema validation."""
    async with _client() as ac:
        resp = await ac.post(
            "/api/v1/recommend",
            json={
                "location": "Bellandur",
                "budget": "medium",
                "min_rating": 6.5,
            },
        )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_recommend_empty_body():
    """Empty JSON body returns 422."""
    async with _client() as ac:
        resp = await ac.post("/api/v1/recommend", json={})

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_recommend_non_json_body():
    """Non-JSON body returns 422."""
    async with _client() as ac:
        resp = await ac.post(
            "/api/v1/recommend",
            content="this is not json",
            headers={"Content-Type": "application/json"},
        )

    assert resp.status_code == 422


# ===================================================================
# POST /api/v1/recommend — Service-level errors
# ===================================================================

@pytest.mark.asyncio
async def test_recommend_returns_503_when_repo_not_loaded():
    """POST /recommend returns 503 if dataset not loaded."""
    app.state.repo = MagicMock(spec=RestaurantRepository, is_loaded=False)

    async with _client() as ac:
        resp = await ac.post(
            "/api/v1/recommend",
            json={"location": "Bellandur", "budget": "medium"},
        )

    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_recommend_returns_500_on_service_crash():
    """If RecommendationService.recommend() raises, we get 500."""
    with patch(
        "src.api.routes.RecommendationService"
    ) as MockService, patch(
        "src.api.routes.LLMClient"
    ):
        MockService.return_value.recommend.side_effect = RuntimeError("boom")

        async with _client() as ac:
            resp = await ac.post(
                "/api/v1/recommend",
                json={"location": "Bellandur", "budget": "medium"},
            )

    assert resp.status_code == 500
    assert "error" in resp.json()["detail"].lower()


# ===================================================================
# POST /api/v1/recommend — End-to-end pipeline (with mocked LLM)
# ===================================================================

@pytest.mark.asyncio
async def test_recommend_end_to_end_with_mocked_llm():
    """
    Full pipeline: real validator + real filter + mocked LLM.

    Verifies that the entire chain works from HTTP request through to
    response without hitting the real Groq API.
    """
    from src.services.llm_client import LLMClientError

    # LLMClient will fail → RecommendationService should fallback
    with patch(
        "src.api.routes.LLMClient", side_effect=LLMClientError("no key")
    ):
        # Use real RecommendationService (not mocked)
        async with _client() as ac:
            resp = await ac.post(
                "/api/v1/recommend",
                json={
                    "location": "Bellandur",
                    "budget": "medium",
                    "min_rating": 3.5,
                },
            )

    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    # With the mock data, there are medium-budget restaurants in Bellandur
    # rating >= 3.5: Curry Palace (4.5), Pizza Paradise (4.2), Biryani House (4.0)
    assert len(data["recommendations"]) >= 1

    # Verify the fallback summary is present
    assert data["metadata"]["model"] == "heuristic-fallback"

    # Check recommendation structure
    rec = data["recommendations"][0]
    assert "rank" in rec
    assert "name" in rec
    assert "cuisine" in rec
    assert "rating" in rec
    assert "estimated_cost" in rec
    assert "explanation" in rec
    assert "restaurant_id" in rec


@pytest.mark.asyncio
async def test_recommend_end_to_end_no_results():
    """
    End-to-end: request a location that doesn't exist in mock data
    → validator does fuzzy-match but if truly not found, 422.
    """
    from src.services.llm_client import LLMClientError

    with patch(
        "src.api.routes.LLMClient", side_effect=LLMClientError("no key")
    ):
        async with _client() as ac:
            resp = await ac.post(
                "/api/v1/recommend",
                json={
                    "location": "NonExistentPlace12345",
                    "budget": "medium",
                },
            )

    # Validator should reject the location since it's not in known locations
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_recommend_end_to_end_relaxed_constraints():
    """
    End-to-end: request a cuisine that doesn't exist in the location
    → filter should relax constraints and still return results.
    """
    from src.services.llm_client import LLMClientError

    with patch(
        "src.api.routes.LLMClient", side_effect=LLMClientError("no key")
    ):
        async with _client() as ac:
            resp = await ac.post(
                "/api/v1/recommend",
                json={
                    "location": "Bellandur",
                    "budget": "medium",
                    "cuisine": "Japanese",  # No Japanese in Bellandur in mock data
                    "min_rating": 4.0,
                },
            )

    assert resp.status_code == 200
    data = resp.json()
    # Filter should relax cuisine and still return results
    assert "recommendations" in data


# ===================================================================
# Health check
# ===================================================================

@pytest.mark.asyncio
async def test_health_check():
    """GET /health returns status and repo state."""
    async with _client() as ac:
        resp = await ac.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "repo_loaded" in data
