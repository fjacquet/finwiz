"""Perplexity Sonar API client with native JSON-schema structured output.

Calls Perplexity's chat completions endpoint with ``response_format: json_schema``
and returns a Pydantic-validated instance directly. Use this instead of wrapping
Perplexity in a CrewAI agent when the work is just "research + format" with no
intermediate reasoning.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from finwiz.config.endpoints import PERPLEXITY_CHAT
from finwiz.tools.api_key_validation import validate_api_key
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "sonar-pro"
DEFAULT_TIMEOUT = 60.0


async def perplexity_structured[T: BaseModel](
    *,
    prompt: str,
    schema: type[T],
    system: str = "You are a financial research assistant. Provide concise, evidence-grounded answers with citations.",
    model: str = DEFAULT_MODEL,
    search_recency_filter: str | None = "month",
    timeout: float = DEFAULT_TIMEOUT,
    api_key: str | None = None,
) -> T | None:
    """Call Perplexity Sonar with JSON schema structured output.

    Args:
        prompt: User prompt describing the research task.
        schema: Pydantic model class. Its ``model_json_schema()`` is sent to the API.
        system: System instruction for the model.
        model: Perplexity model ID (default: sonar-pro).
        search_recency_filter: One of ``hour``, ``day``, ``week``, ``month``, ``year`` or None.
            Maps to the Perplexity API's ``search_recency_filter`` field (the wrong
            ``search_recency`` was silently ignored, returning unfiltered results).
        timeout: HTTP timeout in seconds.
        api_key: Override PPLX_API_KEY for testing.

    Returns:
        Validated Pydantic instance, or None if the call or parse failed.
    """
    key = api_key or validate_api_key("PPLX_API_KEY", "perplexity_structured")
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"schema": schema.model_json_schema()},
        },
        "return_citations": True,
    }
    if search_recency_filter:
        payload["search_recency_filter"] = search_recency_filter

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(PERPLEXITY_CHAT, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(f"Perplexity HTTP {exc.response.status_code} for {schema.__name__}: {exc.response.text[:200]}")
        return None
    except (TimeoutError, httpx.HTTPError) as exc:
        logger.warning(f"Perplexity transport error for {schema.__name__}: {exc}")
        return None
    except ValueError as exc:
        logger.warning(f"Perplexity returned non-JSON for {schema.__name__}: {exc}")
        return None

    content = _extract_content(data)
    if content is None:
        logger.warning(f"Perplexity response missing content for {schema.__name__}")
        return None

    try:
        return schema.model_validate_json(content)
    except ValidationError as exc:
        logger.warning(f"Perplexity output failed {schema.__name__} validation: {exc.error_count()} errors")
        try:
            return schema.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError) as exc2:
            logger.warning(f"Perplexity output unrecoverable for {schema.__name__}: {exc2}")
            return None


def _extract_content(payload: dict[str, Any]) -> str | None:
    """Pull the first message content out of a chat completions response."""
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None
