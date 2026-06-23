"""
Prompt Builder — constructs structured prompts for the Groq LLM.

Converts UserPreferences and filtered candidate Restaurant objects into
a system prompt + user prompt pair that enforces JSON output and
grounded-only recommendations.
"""

from __future__ import annotations

import json
import logging

from src.config import settings
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# System prompt template
# ------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an expert restaurant recommendation assistant for Indian cities.

RULES:
1. You MUST ONLY recommend restaurants from the CANDIDATES list provided below.
2. Do NOT invent, fabricate, or hallucinate any restaurant that is not in the list.
3. Rank the top {top_k} restaurants that best match the user's preferences.
4. For each recommendation, provide a concise 2-3 sentence explanation of why \
it is a good fit based on the user's preferences.
5. If the user provided additional soft preferences (e.g. "family-friendly", \
"quick service"), use them as ranking signals in your explanation.
6. Return your answer as valid JSON only — no markdown, no extra text.

OUTPUT FORMAT (strict JSON):
{{
  "summary": "A brief 1-2 sentence overview of the recommendations.",
  "recommendations": [
    {{
      "id": "<restaurant id from candidates>",
      "rank": 1,
      "explanation": "<why this restaurant fits the user's preferences>"
    }}
  ]
}}
"""

# ------------------------------------------------------------------
# User prompt template
# ------------------------------------------------------------------

_USER_PROMPT = """\
USER PREFERENCES:
{preferences_json}

CANDIDATES ({count} restaurants):
{candidates_json}

Please rank the top {top_k} restaurants from the CANDIDATES list above \
and return the result as JSON.
"""


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def build_prompts(
    preferences: UserPreferences,
    candidates: list[Restaurant],
    top_k: int | None = None,
) -> tuple[str, str]:
    """Build the (system_prompt, user_prompt) pair for the LLM.

    Args:
        preferences: Validated user preferences.
        candidates: Filtered restaurant candidates.
        top_k: Number of recommendations to request. Defaults to config.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    top_k = top_k or settings.TOP_K_RECOMMENDATIONS

    # Cap top_k to available candidates
    top_k = min(top_k, len(candidates))

    system_prompt = _SYSTEM_PROMPT.format(top_k=top_k)

    preferences_dict = preferences.to_dict()
    candidates_list = [r.to_compact_dict() for r in candidates]

    user_prompt = _USER_PROMPT.format(
        preferences_json=json.dumps(preferences_dict, indent=2),
        candidates_json=json.dumps(candidates_list, indent=2),
        count=len(candidates_list),
        top_k=top_k,
    )

    logger.debug(
        "Built prompt: %d candidates, top_k=%d, prompt length=%d chars",
        len(candidates_list),
        top_k,
        len(system_prompt) + len(user_prompt),
    )

    return system_prompt, user_prompt
