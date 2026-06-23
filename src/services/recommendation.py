"""
Recommendation Service — top-level orchestrator.

Brings together the filter, prompt builder, LLM client, and parser
to produce a complete RecommendationResponse from raw user input.
Includes a heuristic fallback when the LLM is unavailable.
"""

from __future__ import annotations

import logging

from src.config import settings
from src.data.repository import RestaurantRepository
from src.models.preferences import UserPreferences
from src.models.recommendation import Recommendation, RecommendationResponse
from src.models.restaurant import Restaurant
from src.services.filter import RestaurantFilter, FilterResult
from src.services.llm_client import LLMClient, LLMClientError
from src.services.parser import ParseError, parse_llm_response
from src.services.prompt_builder import build_prompts

logger = logging.getLogger(__name__)


class RecommendationService:
    """Orchestrates the full recommendation pipeline.

    Usage::

        repo = RestaurantRepository()
        repo.load()
        service = RecommendationService(repo)
        response = service.recommend(user_preferences)
    """

    def __init__(
        self,
        repository: RestaurantRepository,
        llm_client: LLMClient | None = None,
        restaurant_filter: RestaurantFilter | None = None,
    ) -> None:
        self._repo = repository
        self._llm = llm_client  # may be None if API key is missing
        self._filter = restaurant_filter or RestaurantFilter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend(self, preferences: UserPreferences) -> RecommendationResponse:
        """Run the full recommendation pipeline.

        Steps:
            1. Retrieve all restaurants from the repository.
            2. Apply deterministic filters.
            3. Build the LLM prompt.
            4. Call the LLM and parse the response.
            5. Enrich parsed recommendations with full restaurant data.
            6. Fall back to heuristic ranking on any LLM failure.

        Args:
            preferences: Validated user preferences.

        Returns:
            RecommendationResponse with ranked recommendations.
        """
        # 1. Get all restaurants
        all_restaurants = self._repo.get_all()
        logger.info("Starting recommendation for: %s", preferences)

        # 2. Filter
        filter_result: FilterResult = self._filter.filter(all_restaurants, preferences)
        candidates = filter_result.candidates

        if not candidates:
            logger.warning("No candidates after filtering — returning empty response.")
            return RecommendationResponse(
                summary="No restaurants found matching your criteria. "
                        "Try broadening your search.",
                recommendations=[],
                metadata=self._build_metadata(filter_result, None),
            )

        # 3–5. Try LLM path
        if self._llm:
            try:
                return self._llm_recommend(preferences, candidates, filter_result)
            except Exception as exc:
                logger.error("LLM pipeline failed: %s — using fallback.", exc)

        # 6. Fallback
        logger.info("Using heuristic fallback ranking.")
        return self._fallback_recommend(preferences, candidates, filter_result)

    # ------------------------------------------------------------------
    # LLM-powered path
    # ------------------------------------------------------------------

    def _llm_recommend(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
        filter_result: FilterResult,
    ) -> RecommendationResponse:
        """Build prompt → call LLM → parse → enrich."""
        assert self._llm is not None

        system_prompt, user_prompt = build_prompts(preferences, candidates)
        raw_response = self._llm.complete(system_prompt, user_prompt)

        summary, parsed_recs = parse_llm_response(raw_response, candidates)

        # Enrich with full restaurant data
        candidates_by_id = {r.id: r for r in candidates}
        recommendations = self._enrich(parsed_recs, candidates_by_id)

        return RecommendationResponse(
            summary=summary,
            recommendations=recommendations,
            metadata=self._build_metadata(filter_result, self._llm.model_name),
        )

    # ------------------------------------------------------------------
    # Heuristic fallback
    # ------------------------------------------------------------------

    def _fallback_recommend(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
        filter_result: FilterResult,
    ) -> RecommendationResponse:
        """Return the top-K candidates ranked by rating with generic explanations."""
        top_k = settings.TOP_K_RECOMMENDATIONS
        top_candidates = candidates[:top_k]

        recommendations = [
            Recommendation(
                rank=i + 1,
                name=r.name,
                cuisine=r.cuisines_display,
                rating=r.rating,
                estimated_cost=r.cost_for_two,
                explanation=(
                    f"Highly rated {r.cuisines_display} restaurant in "
                    f"{r.location} with a rating of {r.rating}."
                ),
                restaurant_id=r.id,
            )
            for i, r in enumerate(top_candidates)
        ]

        return RecommendationResponse(
            summary=(
                "These recommendations are ranked by rating. "
                "AI-powered explanations are currently unavailable."
            ),
            recommendations=recommendations,
            metadata=self._build_metadata(filter_result, "heuristic-fallback"),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _enrich(
        parsed_recs: list[dict],
        candidates_by_id: dict[str, Restaurant],
    ) -> list[Recommendation]:
        """Merge LLM rankings/explanations with full restaurant records."""
        enriched: list[Recommendation] = []
        for rec in parsed_recs:
            restaurant = candidates_by_id.get(rec["id"])
            if not restaurant:
                continue
            enriched.append(
                Recommendation(
                    rank=rec["rank"],
                    name=restaurant.name,
                    cuisine=restaurant.cuisines_display,
                    rating=restaurant.rating,
                    estimated_cost=restaurant.cost_for_two,
                    explanation=rec["explanation"],
                    restaurant_id=restaurant.id,
                )
            )
        return enriched

    @staticmethod
    def _build_metadata(
        filter_result: FilterResult,
        model: str | None,
    ) -> dict:
        """Assemble the metadata dictionary for the response."""
        meta: dict = {
            "candidates_considered": len(filter_result.candidates),
            "total_restaurants": filter_result.total_before_filter,
            "filters_applied": filter_result.filters_applied,
        }
        if filter_result.constraints_relaxed:
            meta["constraints_relaxed"] = filter_result.constraints_relaxed
        if model:
            meta["model"] = model
        return meta
