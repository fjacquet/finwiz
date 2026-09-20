"""Perplexity gap-fill support (v5.2) — demoted from primary fetcher.

Until Task 8, this module was the sole source of a fact pack: ``fetch_fact_pack``
built a flat ``FactPack`` from a single Perplexity call. `compose_fact_pack`
(``analysis/fact_pack/composer.py``) replaced that: facts now come from free
structured sources (yfinance, a curated expense-ratio table), and Perplexity is
consulted only as ``analysis.fact_pack.sources.research_source.fetch_missing_events``
— a narrow gap-filler for equities with neither SEC filings nor allowlisted wire
news. `fetch_fact_pack`/`fetch_fact_pack_sync` are gone: they built a shape
(top-level `corporate_structure`/`leadership`/... kwargs) the current
discriminated-union `FactPack` schema rejects outright (`extra="forbid"`).

What remains here is what `research_source` still needs: the retry-wrapped
request schema (`_FactPackRaw`), the system prompt (`_SYSTEM_FR`), and
the sync/async bridge (`_run_coroutine_sync`) extracted from the old
`fetch_fact_pack_sync` body.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from collections.abc import Coroutine
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

logger = logging.getLogger(__name__)


_EVENT_MAX_CHARS = 200
_LEADERSHIP_MAX_CHARS = 1000
_CORPORATE_STRUCTURE_MAX_CHARS = 2000
_PLACEHOLDER = "Information indisponible"


class _FactPackRaw(BaseModel):
    """Subset of FactPack returned by the research provider (Python adds freshness + fetched_at).

    Mirrors FactPack but excludes Python-controlled fields. AI cannot supply
    `fetched_at` or `freshness` — Python is authoritative.

    Round-2 fix (2026-04-29): the validators below used to *raise* when the
    LLM returned overlong events (200-char cap) or non-http(s) citation URLs,
    which made the deterministic Perplexity fetch fail intermittently and
    short-circuited the whole pipeline to "Analyse en attente". The new
    validators are *truncating / filtering* — they normalize the LLM's output
    and log a warning, but never raise. The canonical :class:`FactPack`
    schema keeps strict validation; this bridging schema is lenient.
    """

    corporate_structure: str = Field(
        default=_PLACEHOLDER,
        max_length=_CORPORATE_STRUCTURE_MAX_CHARS,
        description=(
            "Structure corporate actuelle en 2000 caractères maximum : maison mère, filiales, acquisitions et cessions des "
            "24 derniers mois, vérifiées sur le web. Écris « Information indisponible » si aucune source fiable."
        ),
    )
    recent_events: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Au plus 10 événements des 12 derniers mois, une phrase de 200 caractères maximum chacun, datés, tirés de pages web consultées.",
    )
    leadership: str = Field(
        default=_PLACEHOLDER,
        max_length=_LEADERSHIP_MAX_CHARS,
        description=(
            "Dirigeants actuels (PDG, directeur financier, président du conseil) avec leur date de prise de fonction, "
            "1000 caractères maximum. Écris « Information indisponible » si aucune source fiable."
        ),
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confiance entre 0 et 1 fondée sur la qualité et la fraîcheur des sources consultées.",
    )
    source_citations: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="URLs http(s) exactes des pages consultées, au plus 20.",
    )

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @staticmethod
    def _normalize_prose_field(data: dict[str, Any], field: str, max_chars: int) -> None:
        """Map a null / non-string / empty / overlong prose value in-place.

        A non-string value (including ``None``) or a blank string becomes the
        French placeholder rather than raising; an overlong one is truncated
        with a warning. Shared by ``leadership`` and ``corporate_structure``,
        which the LLM sometimes returns as ``null`` when it found no source
        (2026-09-20 run: 8 validation failures, 39 field errors, all retried).
        """
        value = data.get(field)
        if not isinstance(value, str):
            if value is not None:
                logger.debug(f"{field} was {type(value).__name__}, using placeholder")
            data[field] = _PLACEHOLDER
            return
        stripped = value.strip()
        if not stripped:
            data[field] = _PLACEHOLDER
        elif len(stripped) > max_chars:
            logger.warning(f"{field} truncated from {len(stripped)} to {max_chars} chars")
            data[field] = stripped[:max_chars].rstrip()
        else:
            data[field] = stripped

    @model_validator(mode="before")
    @classmethod
    def _normalize_llm_payload(cls, data: object) -> object:
        """Truncate / filter LLM output instead of raising.

        - Truncates ``recent_events[i]`` to 200 chars (logs warning per truncation).
        - Drops empty / whitespace-only entries from ``recent_events``.
        - Truncates ``leadership`` to 1000 chars and ``corporate_structure``
          to 2000 chars.
        - Drops non-http(s) URLs from ``source_citations``.
        - Substitutes a French placeholder when prose fields are null, a
          non-string, or empty.
        """
        if not isinstance(data, dict):
            return data

        events = data.get("recent_events")
        if isinstance(events, list):
            normalized: list[str] = []
            for i, ev in enumerate(events):
                if not isinstance(ev, str):
                    continue
                stripped = ev.strip()
                if not stripped:
                    continue
                if len(stripped) > _EVENT_MAX_CHARS:
                    logger.debug(
                        f"recent_events[{i}] truncated from {len(stripped)} to {_EVENT_MAX_CHARS} chars",
                    )
                    stripped = stripped[:_EVENT_MAX_CHARS].rstrip()
                normalized.append(stripped)
            data["recent_events"] = normalized

        cls._normalize_prose_field(data, "leadership", _LEADERSHIP_MAX_CHARS)
        cls._normalize_prose_field(data, "corporate_structure", _CORPORATE_STRUCTURE_MAX_CHARS)

        citations = data.get("source_citations")
        if isinstance(citations, list):
            kept: list[str] = []
            dropped = 0
            for url in citations:
                if not isinstance(url, str):
                    dropped += 1
                    continue
                if not (url.startswith("http://") or url.startswith("https://")):
                    dropped += 1
                    continue
                kept.append(url)
            if dropped:
                logger.warning(f"Dropped {dropped} non-http(s) entries from source_citations")
            data["source_citations"] = kept

        return data


_SYSTEM_FR = (
    "Tu es un assistant de recherche financière strict. Tu réponds UNIQUEMENT "
    "au format JSON conforme au schéma fourni. Tu cites tes sources via les URLs "
    "des pages web consultées. Tu auto-évalues ta confidence dans [0.0, 1.0]. Tu ne dois "
    "JAMAIS inventer des faits ; si tu n'as pas de source fiable, dis-le."
)


def _run_coroutine_sync[T](coro: Coroutine[Any, Any, T], *, timeout: float) -> T | None:
    """Run a coroutine from sync code. Inside a running loop, use a worker thread.

    Extracted from the old `fetch_fact_pack_sync` body (Task 8) so
    `research_source.fetch_missing_events` can share the same event-loop
    juggling without depending on the fetcher it replaced.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an event loop — run in a worker thread to avoid nested-loop errors.
        # Use shutdown(wait=False, cancel_futures=True) so a timeout doesn't block on
        # the worker thread during executor shutdown.
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(asyncio.run, coro)
            try:
                return future.result(timeout=timeout + 5.0)
            except concurrent.futures.TimeoutError:
                future.cancel()
                return None
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    return asyncio.run(coro)
