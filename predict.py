"""
Predict top 5 restaurants for given user preferences.

Input:
    Location : Bellandur
    Rating   : 4.2
    Budget   : 1500 (maps to "medium" tier)

Usage:
    python predict.py
"""

from __future__ import annotations

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-30s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    from src.config import settings
    from src.data.repository import RestaurantRepository
    from src.models.preferences import UserPreferences
    from src.services.filter import RestaurantFilter
    from src.services.llm_client import LLMClient, LLMClientError
    from src.services.recommendation import RecommendationService

    # --- User inputs ---
    LOCATION = "Bellandur"
    MIN_RATING = 4.2
    BUDGET_INR = 1500  # ₹1500 → "medium" tier (≤1500)

    # Map numeric budget to tier using configured thresholds
    if BUDGET_INR <= settings.BUDGET_LOW_MAX:
        budget_tier = "low"
    elif BUDGET_INR <= settings.BUDGET_MEDIUM_MAX:
        budget_tier = "medium"
    else:
        budget_tier = "high"

    preferences = UserPreferences(
        location=LOCATION,
        budget=budget_tier,
        min_rating=MIN_RATING,
    )

    print(f"\n{'='*60}")
    print(f"  🔍 Restaurant Prediction")
    print(f"{'='*60}")
    print(f"  Location   : {LOCATION}")
    print(f"  Min Rating : {MIN_RATING}")
    print(f"  Budget     : ₹{BUDGET_INR} (tier: {budget_tier})")
    print(f"{'='*60}\n")

    # --- Load dataset ---
    logger.info("Loading dataset...")
    repo = RestaurantRepository()
    try:
        repo.load()
    except RuntimeError as exc:
        logger.error("Failed to load dataset: %s", exc)
        sys.exit(1)

    print(f"  ✅ Dataset loaded: {repo.count()} restaurants\n")

    # --- Initialize LLM client ---
    llm_client = None
    if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your_groq_api_key_here":
        try:
            llm_client = LLMClient()
            print(f"  ✅ LLM client ready (model: {llm_client.model_name})\n")
        except LLMClientError as exc:
            logger.warning("LLM client init failed: %s — will use fallback.", exc)
    else:
        print("  ⚠️  GROQ_API_KEY not set — using heuristic fallback.\n")

    # --- Run recommendation pipeline ---
    service = RecommendationService(
        repository=repo,
        llm_client=llm_client,
        restaurant_filter=RestaurantFilter(),
    )

    response = service.recommend(preferences)

    # --- Display results ---
    print(f"\n{'='*60}")
    print(f"  🏆 Top {len(response.recommendations)} Restaurant Recommendations")
    print(f"{'='*60}")

    if response.summary:
        print(f"\n  📋 Summary: {response.summary}\n")

    if not response.recommendations:
        print("  ❌ No restaurants found matching your criteria.")
        print("     Try adjusting location, budget, or rating.\n")
        return

    for rec in response.recommendations:
        print(f"  {'─'*56}")
        print(f"  #{rec.rank}  {rec.name}")
        print(f"       🍽️  Cuisine : {rec.cuisine}")
        print(f"       ⭐ Rating  : {rec.rating}")
        print(f"       💰 Cost    : ₹{rec.estimated_cost} for two")
        print(f"       💬 {rec.explanation}")

    print(f"  {'─'*56}")

    # --- Metadata ---
    meta = response.metadata
    print(f"\n  📊 Metadata:")
    print(f"     Candidates considered : {meta.get('candidates_considered', 'N/A')}")
    print(f"     Total restaurants     : {meta.get('total_restaurants', 'N/A')}")
    print(f"     Filters applied       : {meta.get('filters_applied', {})}")
    if meta.get("constraints_relaxed"):
        print(f"     Constraints relaxed   : {meta['constraints_relaxed']}")
    print(f"     Model used            : {meta.get('model', 'N/A')}")
    print()


if __name__ == "__main__":
    main()
