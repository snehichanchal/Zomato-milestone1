"""
Restaurant Repository — in-memory query interface over preprocessed data.

Provides a high-level API for the rest of the application to query
restaurants without coupling to pandas internals.
"""

from __future__ import annotations

import logging

import pandas as pd

from src.data.loader import load_dataset_df
from src.data.preprocessor import preprocess
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


class RestaurantRepository:
    """In-memory store of preprocessed Restaurant records.

    Typical usage::

        repo = RestaurantRepository()
        repo.load()                       # one-time initialization
        all_restaurants = repo.get_all()
        locations = repo.get_locations()
    """

    def __init__(self) -> None:
        self._df: pd.DataFrame | None = None
        self._restaurants: list[Restaurant] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        """Check whether the dataset has been loaded."""
        return self._df is not None and len(self._restaurants) > 0

    def load(self, force_download: bool = False) -> None:
        """Load and preprocess the dataset into memory.

        Args:
            force_download: If True, bypass the local cache.
        """
        raw_df = load_dataset_df(force_download=force_download)
        self._df = preprocess(raw_df)
        self._restaurants = self._df_to_restaurants(self._df)
        logger.info(
            "Repository ready — %d restaurants loaded.", len(self._restaurants)
        )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_all(self) -> list[Restaurant]:
        """Return all restaurants."""
        self._ensure_loaded()
        return list(self._restaurants)

    def get_locations(self) -> list[str]:
        """Return sorted distinct locations present in the dataset."""
        self._ensure_loaded()
        assert self._df is not None
        return sorted(self._df["location"].dropna().unique().tolist())

    def get_cuisines(self) -> list[str]:
        """Return sorted distinct cuisines across all restaurants."""
        self._ensure_loaded()
        cuisines: set[str] = set()
        for r in self._restaurants:
            cuisines.update(r.cuisines)
        cuisines.discard("Unknown")
        return sorted(cuisines)

    def count(self) -> int:
        """Return the total number of restaurants."""
        self._ensure_loaded()
        return len(self._restaurants)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """Raise if the repository has not been initialized."""
        if not self.is_loaded:
            raise RuntimeError(
                "RestaurantRepository is not loaded. Call .load() first."
            )

    @staticmethod
    def _df_to_restaurants(df: pd.DataFrame) -> list[Restaurant]:
        """Convert a preprocessed DataFrame into a list of Restaurant objects."""
        restaurants: list[Restaurant] = []
        for _, row in df.iterrows():
            cuisines_raw = row.get("cuisines", [])
            # Handle both list (in-memory) and string (from CSV cache) forms
            if isinstance(cuisines_raw, str):
                cuisines_raw = [c.strip() for c in cuisines_raw.split(",") if c.strip()]
            elif not isinstance(cuisines_raw, list):
                cuisines_raw = ["Unknown"]

            restaurants.append(
                Restaurant(
                    id=str(row.get("id", "")),
                    name=str(row.get("name", "")),
                    location=str(row.get("location", "")),
                    cuisines=cuisines_raw,
                    cost_for_two=int(row.get("cost_for_two", 0)),
                    rating=float(row.get("rating", 0.0)),
                    votes=int(row.get("votes", 0)),
                    rest_type=str(row.get("rest_type", "")),
                    budget_tier=str(row.get("budget_tier", "")),
                )
            )
        return restaurants
