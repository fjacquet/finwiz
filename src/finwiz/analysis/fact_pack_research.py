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

from pydantic import BaseModel, ConfigDict, Field

from finwiz.analysis._helpers import _today_french
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack
from finwiz.tools.perplexity_structured import perplexity_structured

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class _FactPackRaw(BaseModel):
    """Subset of FactPack returned by Perplexity (Python adds freshness + fetched_at).

    Mirrors FactPack but excludes Python-controlled fields. AI cannot supply
    `fetched_at` or `freshness` — Python is authoritative.
    """

    corporate_structure: str = Field(min_length=1, max_length=2000)
    recent_events: list[str] = Field(default_factory=list, max_length=10)
    leadership: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0.0, le=1.0)
    source_citations: list[str] = Field(default_factory=list, max_length=20)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


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
        "Tu dois remplir EXACTEMENT trois champs :\n\n"
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
        # We're inside an event loop — run in a worker thread to avoid nested-loop errors
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result(timeout=timeout + 5.0)

    return asyncio.run(coro)
