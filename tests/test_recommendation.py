"""
Unit tests for Phase 3: Prompt Builder, Response Parser, and
Recommendation Service (with mocked LLM).
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.models.recommendation import Recommendation, RecommendationResponse
from src.services.prompt_builder import build_prompts
from src.services.parser import parse_llm_response, ParseError
from src.services.recommendation import RecommendationService
from src.services.filter import RestaurantFilter


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def sample_preferences() -> UserPreferences:
    return UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
        additional="family-friendly",
    )


@pytest.fixture
def sample_candidates() -> list[Restaurant]:
    return [
        Restaurant(
            id="1", name="Pasta Palace", location="Bangalore",
            cuisines=["Italian", "Continental"], cost_for_two=1000,
            rating=4.5, votes=320, rest_type="Casual Dining", budget_tier="medium",
        ),
        Restaurant(
            id="2", name="Cafe Mocha", location="Bangalore",
            cuisines=["Cafe", "Italian"], cost_for_two=700,
            rating=4.0, votes=210, rest_type="Cafe", budget_tier="medium",
        ),
        Restaurant(
            id="3", name="Dragon Wok", location="Bangalore",
            cuisines=["Chinese", "Thai"], cost_for_two=600,
            rating=4.2, votes=150, rest_type="Casual Dining", budget_tier="medium",
        ),
    ]


# ==================================================================
# Prompt Builder Tests
# ==================================================================


class TestPromptBuilder:
    """Tests for prompt construction."""

    def test_returns_two_strings(self, sample_preferences, sample_candidates):
        system, user = build_prompts(sample_preferences, sample_candidates)
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_system_prompt_contains_json_instruction(self, sample_preferences, sample_candidates):
        system, _ = build_prompts(sample_preferences, sample_candidates)
        assert "JSON" in system
        assert "CANDIDATES" in system

    def test_user_prompt_contains_preferences(self, sample_preferences, sample_candidates):
        _, user = build_prompts(sample_preferences, sample_candidates)
        assert "Bangalore" in user
        assert "Italian" in user
        assert "family-friendly" in user

    def test_user_prompt_contains_all_candidates(self, sample_preferences, sample_candidates):
        _, user = build_prompts(sample_preferences, sample_candidates)
        for c in sample_candidates:
            assert c.name in user

    def test_top_k_capped_to_candidates(self, sample_preferences, sample_candidates):
        system, user = build_prompts(sample_preferences, sample_candidates, top_k=100)
        # Should mention 3 (number of candidates), not 100
        assert "top 3" in user.lower()


# ==================================================================
# Response Parser Tests
# ==================================================================


class TestResponseParser:
    """Tests for LLM response parsing and validation."""

    def test_valid_response(self, sample_candidates):
        raw = json.dumps({
            "summary": "Great Italian options in Bangalore.",
            "recommendations": [
                {"id": "1", "rank": 1, "explanation": "Top rated Italian."},
                {"id": "2", "rank": 2, "explanation": "Good cafe with Italian."},
            ]
        })
        summary, recs = parse_llm_response(raw, sample_candidates)
        assert summary == "Great Italian options in Bangalore."
        assert len(recs) == 2
        assert recs[0]["id"] == "1"
        assert recs[0]["rank"] == 1

    def test_invalid_json_raises(self, sample_candidates):
        with pytest.raises(ParseError, match="Invalid JSON"):
            parse_llm_response("not json {{{", sample_candidates)

    def test_missing_recommendations_raises(self, sample_candidates):
        raw = json.dumps({"summary": "test"})
        with pytest.raises(ParseError, match="recommendations"):
            parse_llm_response(raw, sample_candidates)

    def test_hallucinated_id_skipped(self, sample_candidates):
        raw = json.dumps({
            "summary": "test",
            "recommendations": [
                {"id": "999", "rank": 1, "explanation": "Fake restaurant."},
                {"id": "1", "rank": 2, "explanation": "Real restaurant."},
            ]
        })
        summary, recs = parse_llm_response(raw, sample_candidates)
        assert len(recs) == 1
        assert recs[0]["id"] == "1"
        # Rank should be re-sequenced to 1
        assert recs[0]["rank"] == 1

    def test_all_hallucinated_raises(self, sample_candidates):
        raw = json.dumps({
            "summary": "test",
            "recommendations": [
                {"id": "999", "rank": 1, "explanation": "Fake."},
            ]
        })
        with pytest.raises(ParseError, match="no valid recommendations"):
            parse_llm_response(raw, sample_candidates)

    def test_ranks_resequenced(self, sample_candidates):
        raw = json.dumps({
            "summary": "test",
            "recommendations": [
                {"id": "2", "rank": 5, "explanation": "Second."},
                {"id": "1", "rank": 3, "explanation": "First."},
            ]
        })
        _, recs = parse_llm_response(raw, sample_candidates)
        assert recs[0]["rank"] == 1
        assert recs[1]["rank"] == 2


# ==================================================================
# Recommendation Service Tests (mocked LLM)
# ==================================================================


class TestRecommendationService:
    """Integration tests with a mocked LLM client."""

    def _mock_repo(self, restaurants: list[Restaurant]) -> MagicMock:
        repo = MagicMock()
        repo.get_all.return_value = restaurants
        repo.is_loaded = True
        return repo

    def _mock_llm(self, response_json: dict) -> MagicMock:
        llm = MagicMock()
        llm.complete.return_value = json.dumps(response_json)
        llm.model_name = "test-model"
        return llm

    def test_full_pipeline_with_mock_llm(self, sample_candidates, sample_preferences):
        repo = self._mock_repo(sample_candidates)
        llm = self._mock_llm({
            "summary": "Great picks for you.",
            "recommendations": [
                {"id": "1", "rank": 1, "explanation": "Best Italian."},
                {"id": "2", "rank": 2, "explanation": "Good cafe."},
            ]
        })

        service = RecommendationService(repo, llm_client=llm)
        response = service.recommend(sample_preferences)

        assert isinstance(response, RecommendationResponse)
        assert response.summary == "Great picks for you."
        assert len(response.recommendations) == 2
        assert response.recommendations[0].name == "Pasta Palace"
        assert response.recommendations[0].rank == 1
        assert response.metadata["model"] == "test-model"

    def test_fallback_on_llm_failure(self, sample_candidates, sample_preferences):
        repo = self._mock_repo(sample_candidates)
        llm = MagicMock()
        llm.complete.side_effect = Exception("API down")
        llm.model_name = "test-model"

        service = RecommendationService(repo, llm_client=llm)
        response = service.recommend(sample_preferences)

        assert isinstance(response, RecommendationResponse)
        assert len(response.recommendations) > 0
        assert response.metadata["model"] == "heuristic-fallback"

    def test_fallback_when_no_llm_client(self, sample_candidates, sample_preferences):
        repo = self._mock_repo(sample_candidates)

        service = RecommendationService(repo, llm_client=None)
        response = service.recommend(sample_preferences)

        assert isinstance(response, RecommendationResponse)
        assert len(response.recommendations) > 0
        assert "heuristic" in response.metadata.get("model", "")

    def test_empty_candidates_returns_no_results(self, sample_preferences):
        # No restaurants match location
        repo = self._mock_repo([])
        llm = self._mock_llm({"summary": "x", "recommendations": []})

        service = RecommendationService(repo, llm_client=llm)
        response = service.recommend(sample_preferences)

        assert len(response.recommendations) == 0
        assert "no restaurants" in response.summary.lower()

    def test_enrichment_fills_restaurant_fields(self, sample_candidates, sample_preferences):
        repo = self._mock_repo(sample_candidates)
        llm = self._mock_llm({
            "summary": "test",
            "recommendations": [
                {"id": "1", "rank": 1, "explanation": "Great spot."},
            ]
        })

        service = RecommendationService(repo, llm_client=llm)
        response = service.recommend(sample_preferences)

        rec = response.recommendations[0]
        assert rec.name == "Pasta Palace"
        assert rec.cuisine == "Italian, Continental"
        assert rec.rating == 4.5
        assert rec.estimated_cost == 1000
        assert rec.explanation == "Great spot."
        assert rec.restaurant_id == "1"
