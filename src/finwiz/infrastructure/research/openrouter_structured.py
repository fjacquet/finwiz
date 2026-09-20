"""One web-grounded, schema-constrained call to OpenRouter.

OpenRouter exposes web search for any model through the ``web`` plugin and
returns the exact cost of every request in ``usage.cost``. Combined with a
strict ``json_schema`` response format this is a single HTTP call that does
what a Perplexity Sonar call did, on the model the rest of FinWiz already runs
(``google/gemini-3.8-flash``), for roughly a third of the price. No CrewAI
``LLM`` wrapper: it would hide the citations and the cost (see memory rule
"CrewAI only for reasoning").

Failure policy mirrors the vendored Perplexity client so the retry wrapper can
treat both providers alike: every HTTP, transport, JSON or Pydantic failure is
logged at WARNING and returned as ``None``; only a missing API key raises,
before any request is made, so a misconfiguration fails fast instead of
burning the attempt budget. The prompt body and the key are never logged.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import httpx
from pydantic import BaseModel

from finwiz.config.endpoints import OPENROUTER_CHAT
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_MODEL = "google/gemini-3.8-flash"
_DEFAULT_WEB_MAX_RESULTS = 8
_MAX_TOKENS = 4000

# The Exa engine has no recency parameter on OpenRouter, so the window is
# expressed in the prompt. Keys match perplexity_with_retry's
# search_recency_filter values so call sites pass the same string to either.
_RECENCY_SENTENCES: dict[str, str] = {
    "month": "Ne retiens que des sources publiées au cours du dernier mois.",
    "week": "Ne retiens que des sources publiées au cours de la dernière semaine.",
}

_HEADERS_STATIC = {
    "Content-Type": "application/json",
    # OpenRouter asks for these so the app shows up in its activity views.
    "HTTP-Referer": "https://github.com/fjacquet/finwiz",
    "X-Title": "FinWiz",
}


def _web_max_results() -> int:
    return max(1, int(os.getenv("RESEARCH_WEB_MAX_RESULTS", str(_DEFAULT_WEB_MAX_RESULTS))))


@dataclass(frozen=True)
class Citation:
    """One ``url_citation`` annotation from the response."""

    url: str
    title: str = ""
    content: str = ""


@dataclass(frozen=True)
class SearchOptions:
    """Web plugin settings. ``None`` in place of an instance disables search."""

    engine: str = "exa"
    max_results: int = field(default_factory=_web_max_results)
    recency_hint: str | None = None


@dataclass(frozen=True)
class ResearchResult[T: BaseModel]:
    """Validated data plus what the provider told us about the call."""

    data: T
    citations: tuple[Citation, ...]
    cost_usd: float | None
    prompt_tokens: int
    completion_tokens: int


def _build_client(timeout: float) -> httpx.AsyncClient:
    """Test seam: unit tests return a client on an ``httpx.MockTransport``."""
    return httpx.AsyncClient(timeout=timeout)


def _extract_citations(annotations: list[dict[str, Any]]) -> tuple[Citation, ...]:
    seen: set[str] = set()
    out: list[Citation] = []
    for annotation in annotations:
        if not isinstance(annotation, dict):
            continue
        cite = annotation.get("url_citation") or {}
        url = str(cite.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(Citation(url=url, title=str(cite.get("title") or ""), content=str(cite.get("content") or "")))
    return tuple(out)


def _build_payload(*, prompt: str, schema: type[BaseModel], system: str, search: SearchOptions | None) -> dict[str, Any]:
    user = prompt
    if search is not None and search.recency_hint in _RECENCY_SENTENCES:
        user = f"{prompt}\n\n{_RECENCY_SENTENCES[search.recency_hint]}"
    payload: dict[str, Any] = {
        "model": os.getenv("RESEARCH_MODEL", _DEFAULT_MODEL),
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_schema", "json_schema": {"name": schema.__name__, "strict": True, "schema": schema.model_json_schema()}},
        "max_tokens": _MAX_TOKENS,
    }
    if search is not None:
        payload["plugins"] = [{"id": "web", "engine": search.engine, "max_results": search.max_results}]
    return payload


async def openrouter_structured[T: BaseModel](
    *,
    prompt: str,
    schema: type[T],
    system: str,
    search: SearchOptions | None = SearchOptions(),  # noqa: B008 -- frozen dataclass, safe as a default
    timeout: float = 60.0,
    api_key: str | None = None,
) -> ResearchResult[T] | None:
    """POST one chat completion and validate the reply against ``schema``.

    Args:
        prompt: User turn. A recency sentence is appended when ``search`` has a hint.
        schema: Pydantic model the reply must validate against; its class name is
            the ``json_schema.name`` OpenRouter requires.
        system: System turn.
        search: Web plugin options, or ``None`` for a plain completion.
        timeout: httpx timeout in seconds for the whole request.
        api_key: Overrides ``OPENROUTER_API_KEY``.

    Returns:
        A :class:`ResearchResult`, or ``None`` on any failure after the request
        was attempted.

    Raises:
        ValueError: when no API key is available (checked before any request).
    """
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not set")

    payload = _build_payload(prompt=prompt, schema=schema, system=system, search=search)
    headers = {**_HEADERS_STATIC, "Authorization": f"Bearer {key}"}

    try:
        async with _build_client(timeout) as client:
            response = await client.post(OPENROUTER_CHAT, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        logger.warning(f"OpenRouter call for {schema.__name__} failed in transport: {type(exc).__name__}")
        return None

    if response.status_code != 200:
        logger.warning(f"OpenRouter call for {schema.__name__} returned HTTP {response.status_code}")
        return None

    try:
        body = response.json()
        message = body["choices"][0]["message"]
        data = schema.model_validate_json(message.get("content") or "")
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        # pydantic.ValidationError and json.JSONDecodeError are both ValueError subclasses.
        logger.warning(f"OpenRouter reply for {schema.__name__} did not validate: {type(exc).__name__}")
        return None

    usage = body.get("usage") or {}
    raw_cost = usage.get("cost")
    return ResearchResult(
        data=data,
        citations=_extract_citations(message.get("annotations") or []),
        cost_usd=float(raw_cost) if raw_cost is not None else None,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
    )
