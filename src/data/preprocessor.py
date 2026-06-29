"""
Data Preprocessor — normalizes raw Zomato data into the canonical schema.

Handles column mapping, type coercion, cuisine parsing, location
normalization, and budget-tier derivation.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Column mapping: raw dataset column → canonical name.
# Adjust if the upstream schema changes.
# ------------------------------------------------------------------
_COLUMN_MAP: dict[str, str] = {
    "name": "name",
    "online_order": "online_order",
    "book_table": "book_table",
    "rate": "rating",
    "votes": "votes",
    "approx_cost(for two people)": "cost_for_two",
    "listed_in(type)": "rest_type",
    "listed_in(city)": "listed_in_city",
    "cuisines": "cuisines",
    "rest_type": "rest_type_detail",
}


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full preprocessing pipeline on the raw DataFrame.

    Steps:
        1. Rename columns to canonical names.
        2. Parse rating strings to float.
        3. Coerce cost to int.
        4. Parse cuisine strings into lists.
        5. Normalize location strings.
        6. Derive budget_tier.
        7. Assign stable IDs.
        8. Drop rows with critical missing data.

    Args:
        df: Raw DataFrame from the loader.

    Returns:
        Cleaned pd.DataFrame ready for the repository.
    """
    logger.info("Starting preprocessing on %d rows…", len(df))

    # 1. Rename columns (keep only those present in the raw data)
    rename_map = {k: v for k, v in _COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # We no longer overwrite 'location' with 'listed_in_city' to ensure all granular locations are available.
    if "listed_in_city" in df.columns:
        df = df.drop(columns=["listed_in_city"], errors="ignore")

    # 2. Parse rating
    df["rating"] = df["rating"].apply(_parse_rating)

    # 3. Coerce cost
    df["cost_for_two"] = df["cost_for_two"].apply(_parse_cost)

    # 4. Parse cuisines
    df["cuisines"] = df["cuisines"].apply(_parse_cuisines)

    # 5. Normalize location
    df["location"] = df["location"].apply(_normalize_location)

    # 6. Parse votes
    if "votes" in df.columns:
        df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)

    # 7. Assign stable IDs
    df["id"] = [str(i) for i in range(len(df))]

    # 8. Derive budget tier
    df["budget_tier"] = df["cost_for_two"].apply(_derive_budget_tier)

    # 9. Drop rows missing critical fields
    before = len(df)
    df = df.dropna(subset=["name", "location"])
    df = df[df["rating"] >= 0]
    df = df[df["cost_for_two"] > 0]
    after = len(df)
    if before != after:
        logger.info("Dropped %d invalid rows (%d → %d).", before - after, before, after)

    # 10. Select canonical columns
    canonical_cols = [
        "id", "name", "location", "cuisines", "cost_for_two",
        "rating", "votes", "rest_type", "budget_tier",
    ]
    # Only keep columns that exist after processing
    canonical_cols = [c for c in canonical_cols if c in df.columns]
    df = df[canonical_cols].reset_index(drop=True)

    logger.info("Preprocessing complete — %d clean rows.", len(df))
    return df


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _parse_rating(value: Any) -> float:
    """Extract a numeric rating from strings like '4.1/5' or 'NEW'."""
    if pd.isna(value):
        return 0.0
    s = str(value).strip()
    # Handle common non-numeric markers
    if s.lower() in ("new", "-", "", "nan", "none"):
        return 0.0
    # Strip trailing "/5" if present
    s = re.sub(r"\s*/\s*5\s*$", "", s)
    try:
        rating = float(s)
        return max(0.0, min(rating, 5.0))  # clamp to [0, 5]
    except ValueError:
        return 0.0


def _parse_cost(value: Any) -> int:
    """Coerce cost values to int, stripping commas and currency symbols."""
    if pd.isna(value):
        return 0
    s = str(value).strip().replace(",", "").replace("₹", "").replace("$", "")
    try:
        return max(0, int(float(s)))
    except ValueError:
        return 0


def _parse_cuisines(value: Any) -> list[str]:
    """Split comma-separated cuisine string into a cleaned list."""
    if pd.isna(value) or str(value).strip() == "":
        return ["Unknown"]
    parts = [c.strip().title() for c in str(value).split(",") if c.strip()]
    return parts if parts else ["Unknown"]


def _normalize_location(value: Any) -> str:
    """Trim whitespace and apply title-case to location strings."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (ValueError, TypeError):
        pass
    return str(value).strip().title()


def _derive_budget_tier(cost: int) -> str:
    """Map cost_for_two to a budget tier using configured thresholds."""
    if cost <= settings.BUDGET_LOW_MAX:
        return "low"
    elif cost <= settings.BUDGET_MEDIUM_MAX:
        return "medium"
    else:
        return "high"
