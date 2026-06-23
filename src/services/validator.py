"""
Preference Validator — enforces input constraints and normalizes values.

Validates required fields, enum values, rating bounds, and performs
fuzzy location matching against the dataset's known locations.
"""

from __future__ import annotations

import logging
from difflib import get_close_matches
from typing import Any

from src.models.preferences import (
    MAX_RATING_BOUND,
    MIN_RATING_BOUND,
    VALID_BUDGETS,
    UserPreferences,
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when user input fails validation."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class PreferenceValidator:
    """Validates and normalizes raw user input into a UserPreferences object.

    Args:
        known_locations: Set of valid location strings from the dataset.
        known_cuisines: Set of valid cuisine strings from the dataset.
    """

    def __init__(
        self,
        known_locations: list[str] | None = None,
        known_cuisines: list[str] | None = None,
    ) -> None:
        self._known_locations = [loc.lower() for loc in (known_locations or [])]
        self._known_locations_original = known_locations or []
        self._known_cuisines = [c.lower() for c in (known_cuisines or [])]
        self._known_cuisines_original = known_cuisines or []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, raw_input: dict[str, Any]) -> UserPreferences:
        """Validate raw input and return a clean UserPreferences instance.

        Args:
            raw_input: Dictionary with keys matching UserPreferences fields.

        Returns:
            Validated UserPreferences object.

        Raises:
            ValidationError: If any field fails validation.
        """
        location = self._validate_location(raw_input.get("location", ""))
        budget = self._validate_budget(raw_input.get("budget", ""))
        cuisine = self._validate_cuisine(raw_input.get("cuisine"))
        min_rating = self._validate_min_rating(raw_input.get("min_rating", 0.0))
        additional = self._normalize_additional(raw_input.get("additional"))

        return UserPreferences(
            location=location,
            budget=budget,
            cuisine=cuisine,
            min_rating=min_rating,
            additional=additional,
        )

    # ------------------------------------------------------------------
    # Field validators
    # ------------------------------------------------------------------

    def _validate_location(self, value: Any) -> str:
        """Validate location: must be non-empty, fuzzy-matched against known list."""
        if not value or not str(value).strip():
            raise ValidationError("location", "Location is required.")

        location = str(value).strip().title()

        # If we have known locations, try to match
        if self._known_locations:
            location_lower = location.lower()

            # Exact match (case-insensitive)
            if location_lower in self._known_locations:
                idx = self._known_locations.index(location_lower)
                return self._known_locations_original[idx]

            # Fuzzy match
            close = get_close_matches(
                location_lower, self._known_locations, n=3, cutoff=0.6
            )
            if close:
                # Use the best match
                idx = self._known_locations.index(close[0])
                matched = self._known_locations_original[idx]
                logger.info(
                    "Fuzzy-matched location '%s' → '%s'", value, matched
                )
                return matched

            # No match found — build suggestion message
            suggestions = get_close_matches(
                location_lower, self._known_locations, n=5, cutoff=0.4
            )
            if suggestions:
                suggestion_names = [
                    self._known_locations_original[self._known_locations.index(s)]
                    for s in suggestions
                ]
                raise ValidationError(
                    "location",
                    f"Location '{value}' not found. Did you mean: "
                    f"{', '.join(suggestion_names)}?",
                )
            raise ValidationError(
                "location",
                f"Location '{value}' not found in the dataset. "
                f"Available locations include: "
                f"{', '.join(self._known_locations_original[:10])}.",
            )

        # No known locations loaded — accept as-is
        return location

    def _validate_budget(self, value: Any) -> str:
        """Validate budget: must be one of low / medium / high."""
        if not value or not str(value).strip():
            raise ValidationError("budget", "Budget is required.")

        budget = str(value).strip().lower()
        if budget not in VALID_BUDGETS:
            raise ValidationError(
                "budget",
                f"Invalid budget '{value}'. Must be one of: "
                f"{', '.join(VALID_BUDGETS)}.",
            )
        return budget

    def _validate_min_rating(self, value: Any) -> float:
        """Validate min_rating: must be a float in [0.0, 5.0]."""
        try:
            rating = float(value)
        except (TypeError, ValueError):
            raise ValidationError(
                "min_rating",
                f"Invalid rating '{value}'. Must be a number between "
                f"{MIN_RATING_BOUND} and {MAX_RATING_BOUND}.",
            )

        if rating < MIN_RATING_BOUND or rating > MAX_RATING_BOUND:
            raise ValidationError(
                "min_rating",
                f"Rating {rating} is out of range. "
                f"Must be between {MIN_RATING_BOUND} and {MAX_RATING_BOUND}.",
            )
        return rating

    def _validate_cuisine(self, value: Any) -> str | None:
        """Validate cuisine: optional, fuzzy-matched against known cuisines."""
        if not value or not str(value).strip():
            return None

        cuisine = str(value).strip().title()

        if not self._known_cuisines:
            return cuisine

        cuisine_lower = cuisine.lower()

        # Exact match
        if cuisine_lower in self._known_cuisines:
            idx = self._known_cuisines.index(cuisine_lower)
            return self._known_cuisines_original[idx]

        # Fuzzy match
        close = get_close_matches(
            cuisine_lower, self._known_cuisines, n=1, cutoff=0.6
        )
        if close:
            idx = self._known_cuisines.index(close[0])
            matched = self._known_cuisines_original[idx]
            logger.info("Fuzzy-matched cuisine '%s' → '%s'", value, matched)
            return matched

        # No match — accept as-is (the filter will handle zero results)
        logger.warning(
            "Cuisine '%s' not found in dataset vocabulary; accepting as-is.",
            value,
        )
        return cuisine

    def _normalize_additional(self, value: Any) -> str | None:
        """Normalize additional free-text preferences."""
        if not value or not str(value).strip():
            return None
        return str(value).strip()
