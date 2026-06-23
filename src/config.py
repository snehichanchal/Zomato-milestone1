"""
Centralized configuration for the Zomato Restaurant Recommendation System.

Reads settings from environment variables (via .env file) and provides
typed, validated configuration values to all modules.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Settings:
    """Application settings loaded from environment variables."""

    # --- Groq LLM ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.3"))

    # --- Hugging Face Dataset ---
    HF_DATASET_NAME: str = os.getenv(
        "HF_DATASET_NAME", "ManikaSaini/zomato-restaurant-recommendation"
    )

    # --- Application ---
    MAX_CANDIDATES_FOR_LLM: int = int(os.getenv("MAX_CANDIDATES_FOR_LLM", "20"))
    TOP_K_RECOMMENDATIONS: int = int(os.getenv("TOP_K_RECOMMENDATIONS", "5"))
    DATA_CACHE_PATH: Path = Path(
        os.getenv("DATA_CACHE_PATH", str(_PROJECT_ROOT / "data" / "restaurants_cache.csv"))
    )

    # --- Budget Thresholds (INR) ---
    BUDGET_LOW_MAX: int = int(os.getenv("BUDGET_LOW_MAX", "500"))
    BUDGET_MEDIUM_MAX: int = int(os.getenv("BUDGET_MEDIUM_MAX", "1500"))

    @property
    def budget_thresholds(self) -> dict[str, tuple[int, int]]:
        """Return budget tier ranges derived from threshold settings."""
        return {
            "low": (0, self.BUDGET_LOW_MAX),
            "medium": (self.BUDGET_LOW_MAX + 1, self.BUDGET_MEDIUM_MAX),
            "high": (self.BUDGET_MEDIUM_MAX + 1, 999999),
        }


# Singleton settings instance used across the application
settings = Settings()
