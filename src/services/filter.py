"""
Restaurant Filter — deterministic pre-filtering pipeline.

Applies hard constraints (location, budget, rating, cuisine) in sequence
to narrow the full restaurant list down to a bounded candidate set for the LLM.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.config import settings
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    """Encapsulates the output of the filtering pipeline.

    Attributes:
        candidates: Final list of candidate restaurants.
        total_before_filter: Count of restaurants before any filtering.
        filters_applied: Dictionary describing which filters ran and their effect.
        constraints_relaxed: List of constraints that were relaxed (if any).
    """

    candidates: list[Restaurant] = field(default_factory=list)
    total_before_filter: int = 0
    filters_applied: dict[str, str] = field(default_factory=dict)
    constraints_relaxed: list[str] = field(default_factory=list)


class RestaurantFilter:
    """Executes the sequential filter pipeline against a list of restaurants.

    Usage::

        flt = RestaurantFilter(max_candidates=20)
        result = flt.filter(all_restaurants, user_prefs)
    """

    def __init__(self, max_candidates: int | None = None) -> None:
        self._max_candidates = max_candidates or settings.MAX_CANDIDATES_FOR_LLM

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter(
        self,
        restaurants: list[Restaurant],
        preferences: UserPreferences,
    ) -> FilterResult:
        """Run the full filter pipeline with automatic fallback on zero results.

        Filter order:
            1. Location (case-insensitive exact match)
            2. Budget tier
            3. Min rating
            4. Cuisine (if specified)

        If zero candidates remain, constraints are relaxed in reverse order
        (cuisine → budget → min_rating) until at least some results appear.

        Args:
            restaurants: Full list of restaurants from the repository.
            preferences: Validated user preferences.

        Returns:
            FilterResult with candidates sorted by rating (desc), votes (desc).
        """
        result = FilterResult(total_before_filter=len(restaurants))
        candidates = list(restaurants)

        # --- 1. Location filter (always applied, never relaxed) ---
        candidates = self._filter_by_location(candidates, preferences.location)
        result.filters_applied["location"] = preferences.location
        logger.info(
            "After location filter ('%s'): %d candidates",
            preferences.location,
            len(candidates),
        )

        if not candidates:
            # Location is a hard requirement — cannot relax
            result.candidates = []
            return result

        # --- Try strict filtering first ---
        strict = self._apply_soft_filters(
            candidates, preferences, result
        )

        if strict:
            result.candidates = self._select_top(strict)
            return result

        # --- Fallback: relax constraints sequentially ---
        logger.info("Zero strict matches — relaxing constraints…")
        result.candidates = self._relax_and_retry(
            candidates, preferences, result
        )
        return result

    # ------------------------------------------------------------------
    # Individual filters
    # ------------------------------------------------------------------

    @staticmethod
    def _filter_by_location(
        restaurants: list[Restaurant], location: str
    ) -> list[Restaurant]:
        """Case-insensitive exact match on location."""
        loc_lower = location.lower()
        return [r for r in restaurants if r.location.lower() == loc_lower]

    @staticmethod
    def _filter_by_budget(
        restaurants: list[Restaurant], budget: str
    ) -> list[Restaurant]:
        """Match restaurants whose budget_tier equals the requested tier."""
        return [r for r in restaurants if r.budget_tier == budget]

    @staticmethod
    def _filter_by_min_rating(
        restaurants: list[Restaurant], min_rating: float
    ) -> list[Restaurant]:
        """Keep restaurants with rating ≥ min_rating."""
        return [r for r in restaurants if r.rating >= min_rating]

    @staticmethod
    def _filter_by_cuisine(
        restaurants: list[Restaurant], cuisine: str
    ) -> list[Restaurant]:
        """Keep restaurants whose cuisines list contains the target cuisine."""
        cuisine_lower = cuisine.lower()
        return [
            r
            for r in restaurants
            if any(c.lower() == cuisine_lower for c in r.cuisines)
        ]

    # ------------------------------------------------------------------
    # Sorting & selection
    # ------------------------------------------------------------------

    def _select_top(self, candidates: list[Restaurant]) -> list[Restaurant]:
        """Sort by rating (desc), votes (desc), name (asc), deduplicate by name, and cap at max."""
        sorted_candidates = sorted(
            candidates,
            key=lambda r: (-r.rating, -r.votes, r.name),
        )
        
        seen_names = set()
        unique_candidates = []
        for r in sorted_candidates:
            name_lower = r.name.lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique_candidates.append(r)
                
        return unique_candidates[: self._max_candidates]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _apply_soft_filters(
        self,
        candidates: list[Restaurant],
        preferences: UserPreferences,
        result: FilterResult,
    ) -> list[Restaurant]:
        """Apply budget, rating, and cuisine filters strictly."""
        # Budget
        candidates = self._filter_by_budget(candidates, preferences.budget)
        result.filters_applied["budget"] = preferences.budget
        logger.info("After budget filter ('%s'): %d", preferences.budget, len(candidates))

        if not candidates:
            return []

        # Min rating
        candidates = self._filter_by_min_rating(candidates, preferences.min_rating)
        result.filters_applied["min_rating"] = str(preferences.min_rating)
        logger.info("After rating filter (≥%.1f): %d", preferences.min_rating, len(candidates))

        if not candidates:
            return []

        # Cuisine (optional)
        if preferences.cuisine:
            candidates = self._filter_by_cuisine(candidates, preferences.cuisine)
            result.filters_applied["cuisine"] = preferences.cuisine
            logger.info(
                "After cuisine filter ('%s'): %d",
                preferences.cuisine,
                len(candidates),
            )

        return candidates

    def _relax_and_retry(
        self,
        location_filtered: list[Restaurant],
        preferences: UserPreferences,
        result: FilterResult,
    ) -> list[Restaurant]:
        """Progressively relax constraints to find at least some candidates.

        Relaxation order:
            1. Drop cuisine constraint
            2. Drop budget constraint
            3. Lower min_rating to 0
        """
        candidates = list(location_filtered)

        # Try: budget + rating (no cuisine)
        if preferences.cuisine:
            attempt = self._filter_by_budget(candidates, preferences.budget)
            attempt = self._filter_by_min_rating(attempt, preferences.min_rating)
            if attempt:
                result.constraints_relaxed.append("cuisine")
                logger.info("Relaxed cuisine — %d candidates.", len(attempt))
                return self._select_top(attempt)

        # Try: rating only (no cuisine, no budget)
        attempt = self._filter_by_min_rating(candidates, preferences.min_rating)
        if attempt:
            result.constraints_relaxed.append("budget")
            if preferences.cuisine:
                result.constraints_relaxed.append("cuisine")
            logger.info("Relaxed budget — %d candidates.", len(attempt))
            return self._select_top(attempt)

        # Try: no filters except location
        result.constraints_relaxed.append("min_rating")
        result.constraints_relaxed.append("budget")
        if preferences.cuisine:
            result.constraints_relaxed.append("cuisine")
        logger.info("Relaxed all soft constraints — %d candidates.", len(candidates))
        return self._select_top(candidates)
