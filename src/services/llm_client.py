"""
LLM Client — thin adapter over the Groq chat completions API.

Handles API communication, retry logic with temperature reduction,
rate-limit backoff, and latency/token-usage logging.
"""

from __future__ import annotations

import logging
import time

from groq import Groq, APIStatusError, RateLimitError

from src.config import settings

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Raised when the LLM call fails after all retries."""
    pass


class LLMClient:
    """Wraps the Groq Python SDK for chat completions.

    Usage::

        client = LLMClient()
        text = client.complete(system_prompt, user_prompt)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_retries: int = 2,
    ) -> None:
        self._api_key = api_key or settings.GROQ_API_KEY
        if not self._api_key:
            raise LLMClientError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )
        self._model = model or settings.GROQ_MODEL
        self._temperature = temperature if temperature is not None else settings.GROQ_TEMPERATURE
        self._max_retries = max_retries
        self._client = Groq(api_key=self._api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request with retry and backoff.

        On parse-related failures the temperature is reduced and the
        request is retried. On rate-limit (429) errors, exponential
        backoff is applied.

        Args:
            system_prompt: The system-level instruction.
            user_prompt: The user-level message with preferences + candidates.

        Returns:
            Raw text content from the LLM response.

        Raises:
            LLMClientError: If all retries are exhausted.
        """
        temperature = self._temperature
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 2):  # +1 for initial try
            try:
                logger.info(
                    "LLM request attempt %d/%d (model=%s, temp=%.2f)",
                    attempt,
                    self._max_retries + 1,
                    self._model,
                    temperature,
                )

                start = time.time()
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                elapsed = time.time() - start

                # Log usage
                usage = response.usage
                if usage:
                    logger.info(
                        "LLM response in %.2fs — prompt_tokens=%d, "
                        "completion_tokens=%d, total_tokens=%d",
                        elapsed,
                        usage.prompt_tokens,
                        usage.completion_tokens,
                        usage.total_tokens,
                    )

                content = response.choices[0].message.content
                if not content:
                    raise LLMClientError("LLM returned empty content.")

                return content

            except RateLimitError as exc:
                last_error = exc
                wait = 2 ** attempt  # exponential backoff
                logger.warning(
                    "Rate limited (429). Waiting %ds before retry…", wait
                )
                time.sleep(wait)

            except APIStatusError as exc:
                last_error = exc
                logger.error("Groq API error: %s", exc)
                # Reduce temperature on non-rate-limit errors (possibly bad JSON)
                temperature = max(0.1, temperature - 0.1)

            except Exception as exc:
                last_error = exc
                logger.error("Unexpected error during LLM call: %s", exc)
                temperature = max(0.1, temperature - 0.1)

        raise LLMClientError(
            f"LLM call failed after {self._max_retries + 1} attempts. "
            f"Last error: {last_error}"
        )

    @property
    def model_name(self) -> str:
        """Return the configured model identifier."""
        return self._model
