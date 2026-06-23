"""
Response Parser — safely parses and validates LLM JSON output.

Extracts the recommendations array and summary from the raw LLM text,
validates IDs against the candidate list, and handles malformed output.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Raised when the LLM response cannot be parsed into valid recommendations."""
    pass


def parse_llm_response(
    raw_text: str,
    candidates: list[Restaurant],
) -> tuple[str | None, list[dict]]:
    """Parse and validate the LLM JSON response.

    Args:
        raw_text: Raw JSON string from the LLM.
        candidates: The candidate restaurants that were sent to the LLM.

    Returns:
        Tuple of (summary, list_of_recommendation_dicts).
        Each dict has keys: id, rank, explanation.

    Raises:
        ParseError: If JSON is invalid or structure is unexpected.
    """
    # Build a lookup of valid IDs
    valid_ids = {r.id for r in candidates}

    # 1. Parse JSON
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ParseError(f"Invalid JSON from LLM: {exc}") from exc

    if not isinstance(data, dict):
        raise ParseError(f"Expected JSON object, got {type(data).__name__}.")

    # 2. Extract summary
    summary = data.get("summary")
    if summary and not isinstance(summary, str):
        summary = str(summary)

    # 3. Extract recommendations
    recs_raw = data.get("recommendations")
    if not isinstance(recs_raw, list):
        raise ParseError(
            "Missing or invalid 'recommendations' array in LLM response."
        )

    # 4. Validate each recommendation
    validated: list[dict] = []
    for i, item in enumerate(recs_raw):
        if not isinstance(item, dict):
            logger.warning("Skipping non-dict recommendation at index %d.", i)
            continue

        rec_id = str(item.get("id", "")).strip()
        if rec_id not in valid_ids:
            logger.warning(
                "LLM recommended id='%s' which is not in candidates — skipping.",
                rec_id,
            )
            continue

        explanation = item.get("explanation", "")
        if not isinstance(explanation, str):
            explanation = str(explanation)

        rank = item.get("rank", i + 1)
        try:
            rank = int(rank)
        except (TypeError, ValueError):
            rank = i + 1

        validated.append({
            "id": rec_id,
            "rank": rank,
            "explanation": explanation.strip(),
        })

    if not validated:
        raise ParseError(
            "LLM response contained no valid recommendations matching candidates."
        )

    # Sort by rank
    validated.sort(key=lambda r: r["rank"])

    # Re-assign sequential ranks (1-based)
    for idx, rec in enumerate(validated):
        rec["rank"] = idx + 1

    logger.info(
        "Parsed %d valid recommendations from LLM response.", len(validated)
    )
    return summary, validated
