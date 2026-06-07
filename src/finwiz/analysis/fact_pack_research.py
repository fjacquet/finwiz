"""Fact pack fetcher (v5.2) — verified corporate facts via Perplexity.

Mirrors strategic_research.py's pattern: direct httpx call via
perplexity_structured(), sync wrapper for non-async callers.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, model_validator

from finwiz.analysis._helpers import _today_french
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack
from finwiz.tools.perplexity_structured import perplexity_structured

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


_EVENT_MAX_CHARS = 200
_LEADERSHIP_MAX_CHARS = 1000
_CORPORATE_STRUCTURE_MAX_CHARS = 2000
_PLACEHOLDER = "Information indisponible"


class _FactPackRaw(BaseModel):
    """Subset of FactPack returned by Perplexity (Python adds freshness + fetched_at).

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

    corporate_structure: str = Field(default=_PLACEHOLDER, max_length=_CORPORATE_STRUCTURE_MAX_CHARS)
    recent_events: list[str] = Field(default_factory=list, max_length=10)
    leadership: str = Field(default=_PLACEHOLDER, max_length=_LEADERSHIP_MAX_CHARS)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_citations: list[str] = Field(default_factory=list, max_length=20)

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @model_validator(mode="before")
    @classmethod
    def _normalize_llm_payload(cls, data: object) -> object:
        """Truncate / filter LLM output instead of raising.

        - Truncates ``recent_events[i]`` to 200 chars (logs warning per truncation).
        - Drops empty / whitespace-only entries from ``recent_events``.
        - Truncates ``leadership`` to 1000 chars and ``corporate_structure``
          to 2000 chars.
        - Drops non-http(s) URLs from ``source_citations``.
        - Substitutes a French placeholder when prose fields are empty.
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

        leadership = data.get("leadership")
        if isinstance(leadership, str):
            stripped = leadership.strip()
            if not stripped:
                data["leadership"] = _PLACEHOLDER
            elif len(stripped) > _LEADERSHIP_MAX_CHARS:
                logger.warning(
                    f"leadership truncated from {len(stripped)} to {_LEADERSHIP_MAX_CHARS} chars",
                )
                data["leadership"] = stripped[:_LEADERSHIP_MAX_CHARS].rstrip()
            else:
                data["leadership"] = stripped

        corporate = data.get("corporate_structure")
        if isinstance(corporate, str):
            stripped = corporate.strip()
            if not stripped:
                data["corporate_structure"] = _PLACEHOLDER
            elif len(stripped) > _CORPORATE_STRUCTURE_MAX_CHARS:
                logger.warning(
                    f"corporate_structure truncated from {len(stripped)} to {_CORPORATE_STRUCTURE_MAX_CHARS} chars",
                )
                data["corporate_structure"] = stripped[:_CORPORATE_STRUCTURE_MAX_CHARS].rstrip()
            else:
                data["corporate_structure"] = stripped

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
    "au format JSON conforme au schéma fourni. Tu cites tes sources via URLs "
    "Perplexity. Tu auto-évalues ta confidence dans [0.0, 1.0]. Tu ne dois "
    "JAMAIS inventer des faits ; si tu n'as pas de source fiable, dis-le."
)


def _build_prompt(ticker: str, company_name: str, sector: str | None, industry: str | None) -> str:
    today = _today_french()
    sector_str = sector or "secteur inconnu"
    industry_str = industry or "industrie inconnue"
    return (
        f"Date du jour : {today}.\n\n"
        f"Recherche les faits VÉRIFIÉS et ACTUELS sur {company_name} ({ticker}, "
        f"{sector_str} / {industry_str}).\n\n"
        "1. **corporate_structure** (≤2000 chars) : structure actuelle de l'entité — "
        "société-mère, filiales, divisions, et toute cession ou acquisition majeure "
        "des 24 derniers mois. Exemple type : "
        "'Independent — divested VMware November 2021. Subsidiary of Dell Technologies."
        "'\n\n"
        "2. **recent_events** (liste de 0 à 10 strings, ≤200 chars chacun) : "
        f"événements matériels des 12 derniers mois (par rapport à {today}) — "
        "résultats trimestriels notables, M&A, changements de direction, "
        "événements réglementaires/légaux majeurs. Pas de bavardage marketing.\n\n"
        "3. **leadership** (≤1000 chars) : CEO et CFO actuels avec dates de prise "
        "de fonction si récents (<24 mois), plus tout changement d'équipe "
        "exécutive matériel récent.\n\n"
        "4. **confidence** : auto-évaluation [0.0-1.0] de la fiabilité de tes "
        "réponses (sources multiples = haut, sources rares ou contradictoires = bas).\n\n"
        "5. **source_citations** : URLs Perplexity utilisées (max 20).\n\n"
        "Si tu n'as PAS de source fiable pour un champ, écris une description "
        "courte expliquant l'incertitude — ne pas inventer."
    )


async def fetch_fact_pack(
    ticker: str,
    company_name: str,
    sector: str | None = None,
    industry: str | None = None,
    *,
    timeout: float = 15.0,
) -> FactPack | None:
    """Fetch verified corporate facts via Perplexity.

    Returns None on Perplexity failure (caller decides FAILED vs cache fallback).
    """
    prompt = _build_prompt(ticker, company_name, sector, industry)
    try:
        raw = await perplexity_structured(
            prompt=prompt,
            schema=_FactPackRaw,
            system=_SYSTEM_FR,
            search_recency_filter="month",
            timeout=timeout,
        )
    except Exception as e:
        logger.warning(f"fact_pack fetch failed for {ticker}: {e}")
        return None
    if raw is None:
        logger.warning(f"fact_pack fetch returned None for {ticker}")
        return None
    fetched_at = datetime.now(UTC)
    return FactPack(
        corporate_structure=raw.corporate_structure,
        recent_events=raw.recent_events,
        leadership=raw.leadership,
        fetched_at=fetched_at,
        freshness=FactPack.derive_freshness(fetched_at),
        confidence=raw.confidence,
        source_citations=raw.source_citations,
    )


def fetch_fact_pack_sync(
    ticker: str,
    company_name: str,
    sector: str | None = None,
    industry: str | None = None,
    *,
    timeout: float = 15.0,
) -> FactPack | None:
    """Sync wrapper. Inside a running event loop, runs the coroutine via thread executor."""
    coro = fetch_fact_pack(ticker, company_name, sector, industry, timeout=timeout)
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
