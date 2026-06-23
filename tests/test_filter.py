"""
Unit tests for the RestaurantFilter and PreferenceValidator.

Uses a frozen set of mock restaurants for deterministic results.
"""

import pytest

from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.filter import RestaurantFilter, FilterResult
from src.services.validator import PreferenceValidator, ValidationError


# ------------------------------------------------------------------
# Fixtures — frozen mock data
# ------------------------------------------------------------------

@pytest.fixture
def mock_restaurants() -> list[Restaurant]:
    """A small fixed set of restaurants covering various filter scenarios."""
    return [
        Restaurant(
            id="1", name="Pasta Palace", location="Bangalore",
            cuisines=["Italian", "Continental"], cost_for_two=1000,
            rating=4.5, votes=320, rest_type="Casual Dining", budget_tier="medium",
        ),
        Restaurant(
            id="2", name="Dragon Wok", location="Bangalore",
            cuisines=["Chinese", "Thai"], cost_for_two=600,
            rating=4.2, votes=150, rest_type="Casual Dining", budget_tier="medium",
        ),
        Restaurant(
            id="3", name="Street Bites", location="Bangalore",
            cuisines=["North Indian", "Street Food"], cost_for_two=300,
            rating=3.8, votes=500, rest_type="Quick Bites", budget_tier="low",
        ),
        Restaurant(
            id="4", name="Royal Biryani", location="Delhi",
            cuisines=["North Indian", "Mughlai"], cost_for_two=800,
            rating=4.7, votes=1200, rest_type="Casual Dining", budget_tier="medium",
        ),
        Restaurant(
            id="5", name="Le Jardin", location="Bangalore",
            cuisines=["French", "Continental"], cost_for_two=2500,
            rating=4.8, votes=90, rest_type="Fine Dining", budget_tier="high",
        ),
        Restaurant(
            id="6", name="Cafe Mocha", location="Bangalore",
            cuisines=["Cafe", "Italian"], cost_for_two=700,
            rating=4.0, votes=210, rest_type="Cafe", budget_tier="medium",
        ),
        Restaurant(
            id="7", name="Tandoori Nights", location="Bangalore",
            cuisines=["North Indian"], cost_for_two=900,
            rating=3.5, votes=80, rest_type="Casual Dining", budget_tier="medium",
        ),
        Restaurant(
            id="8", name="Sushi Express", location="Bangalore",
            cuisines=["Japanese", "Sushi"], cost_for_two=1800,
            rating=4.3, votes=60, rest_type="Fine Dining", budget_tier="high",
        ),
    ]


@pytest.fixture
def known_locations() -> list[str]:
    return ["Bangalore", "Delhi", "Banashankari", "Btm"]


@pytest.fixture
def known_cuisines() -> list[str]:
    return [
        "Italian", "Continental", "Chinese", "Thai", "North Indian",
        "Street Food", "Mughlai", "French", "Cafe", "Japanese", "Sushi",
    ]


# ==================================================================
# PreferenceValidator Tests
# ==================================================================


class TestPreferenceValidator:
    """Tests for input validation and normalization."""

    def test_valid_input(self, known_locations, known_cuisines):
        validator = PreferenceValidator(known_locations, known_cuisines)
        prefs = validator.validate({
            "location": "Bangalore",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
            "additional": "family-friendly",
        })
        assert prefs.location == "Bangalore"
        assert prefs.budget == "medium"
        assert prefs.cuisine == "Italian"
        assert prefs.min_rating == 4.0
        assert prefs.additional == "family-friendly"

    def test_location_required(self, known_locations, known_cuisines):
        validator = PreferenceValidator(known_locations, known_cuisines)
        with pytest.raises(ValidationError, match="location"):
            validator.validate({"location": "", "budget": "low"})

    def test_location_fuzzy_match(self, known_locations, known_cuisines):
        validator = PreferenceValidator(known_locations, known_cuisines)
        prefs = validator.validate({
            "location": "bangalor",  # typo
            "budget": "low",
        })
        assert prefs.location == "Bangalore"

    def test_location_not_found(self, known_locations, known_cuisines):
        validator = PreferenceValidator(known_locations, known_cuisines)
        with pytest.raises(ValidationError, match="not found"):
            validator.validate({"location": "zzzzz", "budget": "low"})

    def test_budget_invalid(self, known_locations, known_cuisines):
        validator = PreferenceValidator(known_locations, known_cuisines)
        with pytest.raises(ValidationError, match="budget"):
            validator.validate({"location": "Bangalore", "budget": "ultra"})

    def test_budget_case_insensitive(self, known_locations, known_cuisines):
        validator = PreferenceValidator(known_locations, known_cuisines)
        prefs = validator.validate({"location": "Bangalore", "budget": "HIGH"})
        assert prefs.budget == "high"

    def test_rating_out_of_range(self, known_locations, known_cuisines):
        validator = PreferenceValidator(known_locations, known_cuisines)
        with pytest.raises(ValidationError, match="min_rating"):
            validator.validate({
                "location": "Bangalore", "budget": "low", "min_rating": 6.0,
            })

    def test_rating_negative(self, known_locations, known_cuisines):
        validator = PreferenceValidator(known_locations, known_cuisines)
        with pytest.raises(ValidationError, match="min_rating"):
            validator.validate({
                "location": "Bangalore", "budget": "low", "min_rating": -1.0,
            })

    def test_cuisine_optional_none(self, known_locations, known_cuisines):
        validator = PreferenceValidator(known_locations, known_cuisines)
        prefs = validator.validate({"location": "Bangalore", "budget": "low"})
        assert prefs.cuisine is None

    def test_cuisine_fuzzy_match(self, known_locations, known_cuisines):
        validator = PreferenceValidator(known_locations, known_cuisines)
        prefs = validator.validate({
            "location": "Bangalore", "budget": "low", "cuisine": "italan",
        })
        assert prefs.cuisine == "Italian"

    def test_additional_whitespace_trimmed(self, known_locations, known_cuisines):
        validator = PreferenceValidator(known_locations, known_cuisines)
        prefs = validator.validate({
            "location": "Bangalore", "budget": "low",
            "additional": "  outdoor seating  ",
        })
        assert prefs.additional == "outdoor seating"


# ==================================================================
# RestaurantFilter Tests
# ==================================================================


class TestRestaurantFilter:
    """Tests for the deterministic filtering pipeline."""

    def test_filter_by_location(self, mock_restaurants):
        flt = RestaurantFilter(max_candidates=20)
        prefs = UserPreferences(location="Bangalore", budget="medium")
        result = flt.filter(mock_restaurants, prefs)
        # Should exclude Delhi restaurant (id=4)
        assert all(r.location == "Bangalore" for r in result.candidates)
        assert not any(r.id == "4" for r in result.candidates)

    def test_filter_by_budget(self, mock_restaurants):
        flt = RestaurantFilter(max_candidates=20)
        prefs = UserPreferences(location="Bangalore", budget="low")
        result = flt.filter(mock_restaurants, prefs)
        # Only "Street Bites" (id=3) is budget=low in Bangalore
        assert len(result.candidates) == 1
        assert result.candidates[0].id == "3"

    def test_filter_by_min_rating(self, mock_restaurants):
        flt = RestaurantFilter(max_candidates=20)
        prefs = UserPreferences(location="Bangalore", budget="medium", min_rating=4.0)
        result = flt.filter(mock_restaurants, prefs)
        assert all(r.rating >= 4.0 for r in result.candidates)
        # Tandoori Nights (3.5) should be excluded
        assert not any(r.id == "7" for r in result.candidates)

    def test_filter_by_cuisine(self, mock_restaurants):
        flt = RestaurantFilter(max_candidates=20)
        prefs = UserPreferences(
            location="Bangalore", budget="medium", cuisine="Italian",
        )
        result = flt.filter(mock_restaurants, prefs)
        assert all(
            any(c.lower() == "italian" for c in r.cuisines)
            for r in result.candidates
        )

    def test_sorted_by_rating_desc(self, mock_restaurants):
        flt = RestaurantFilter(max_candidates=20)
        prefs = UserPreferences(location="Bangalore", budget="medium")
        result = flt.filter(mock_restaurants, prefs)
        ratings = [r.rating for r in result.candidates]
        assert ratings == sorted(ratings, reverse=True)

    def test_max_candidates_cap(self, mock_restaurants):
        flt = RestaurantFilter(max_candidates=2)
        prefs = UserPreferences(location="Bangalore", budget="medium")
        result = flt.filter(mock_restaurants, prefs)
        assert len(result.candidates) <= 2

    def test_zero_results_location(self, mock_restaurants):
        """Unknown location → empty results, no relaxation possible."""
        flt = RestaurantFilter(max_candidates=20)
        prefs = UserPreferences(location="Mumbai", budget="medium")
        result = flt.filter(mock_restaurants, prefs)
        assert len(result.candidates) == 0

    def test_zero_results_relaxes_cuisine(self, mock_restaurants):
        """Overly specific cuisine should get relaxed automatically."""
        flt = RestaurantFilter(max_candidates=20)
        prefs = UserPreferences(
            location="Bangalore", budget="low", cuisine="French",
        )
        # No low-budget French in Bangalore → relaxes cuisine
        result = flt.filter(mock_restaurants, prefs)
        assert len(result.candidates) > 0
        assert "cuisine" in result.constraints_relaxed

    def test_zero_results_relaxes_budget(self, mock_restaurants):
        """If even dropping cuisine doesn't help, budget gets relaxed too."""
        flt = RestaurantFilter(max_candidates=20)
        prefs = UserPreferences(
            location="Bangalore", budget="low", min_rating=4.5,
        )
        # Only Le Jardin (4.8, high) and Pasta Palace (4.5, medium) ≥ 4.5
        # Neither is low budget → should relax budget
        result = flt.filter(mock_restaurants, prefs)
        assert len(result.candidates) > 0
        assert "budget" in result.constraints_relaxed

    def test_filters_applied_tracking(self, mock_restaurants):
        flt = RestaurantFilter(max_candidates=20)
        prefs = UserPreferences(
            location="Bangalore", budget="medium", cuisine="Italian", min_rating=3.0,
        )
        result = flt.filter(mock_restaurants, prefs)
        assert "location" in result.filters_applied
        assert "budget" in result.filters_applied
        assert "cuisine" in result.filters_applied
        assert "min_rating" in result.filters_applied

    def test_total_before_filter(self, mock_restaurants):
        flt = RestaurantFilter(max_candidates=20)
        prefs = UserPreferences(location="Bangalore", budget="medium")
        result = flt.filter(mock_restaurants, prefs)
        assert result.total_before_filter == len(mock_restaurants)
