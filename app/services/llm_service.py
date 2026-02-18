"""
Gemini LLM client with retry logic for rate limits.
"""

import re
import time
from typing import Optional

from google import genai
from google.genai import types

from app.config import (
    DEFAULT_MODEL,
    INITIAL_RETRY_DELAY_SECONDS,
    MAX_RETRIES,
)


class GeminiClient:
    """Thin wrapper around Gemini API with retry on rate limit."""

    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)

    def generate(
        self,
        prompt: str,
        *,
        max_output_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text with automatic retry on 429 / quota errors.

        Returns:
            Generated text (strip() applied).

        Raises:
            Exception: On quota exceeded after retries, or other API errors.
        """
        retry_delay = INITIAL_RETRY_DELAY_SECONDS
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.models.generate_content(
                    model=DEFAULT_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                    ),
                )
                return response.text.strip() if response.text else ""
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                # Check for rate limit errors (SDK specific or generic 429)
                if "429" not in error_str and "quota" not in error_str and "rate limit" not in error_str:
                    raise

                if attempt >= MAX_RETRIES - 1:
                    raise Exception(
                        f"Quota/Rate limit exceeded after {MAX_RETRIES} attempts. "
                        "Free tier allows 20 requests per day per model. "
                        "Please wait or upgrade at https://ai.google.dev/gemini-api/docs/rate-limits"
                    ) from e

                delay_match = re.search(r"retry in ([\d.]+)s", error_str)
                if delay_match:
                    retry_delay = int(float(delay_match.group(1))) + 2
                else:
                    retry_delay = retry_delay * (attempt + 1)

                time.sleep(retry_delay)

        raise last_error  # type: ignore[misc]

    def generate_graceful(
        self,
        prompt: str,
        *,
        max_output_tokens: int = 200,
        temperature: float = 0.8,
    ) -> Optional[str]:
        """
        Like generate(), but returns None on quota/rate limit instead of raising.
        Used for follow-up questions so the interview can continue.
        """
        try:
            return self.generate(
                prompt,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "rate limit" in str(e).lower():
                return None
            raise
