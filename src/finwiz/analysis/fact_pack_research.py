"""Perplexity gap-fill support (v5.2) — demoted from primary fetcher.

Until Task 8, this module was the sole source of a fact pack: ``fetch_fact_pack``
built a flat ``FactPack`` from a single Perplexity call. `compose_fact_pack`
(``analysis/fact_pack/composer.py``) replaced that: facts now come from free
structured sources (yfinance, a curated expense-ratio table), and Perplexity is
consulted only as ``analysis.fact_pack.sources.perplexity_source.fetch_missing_events``
— a narrow gap-filler for equities with neither SEC filings nor allowlisted wire
news. `fetch_fact_pack`/`fetch_fact_pack_sync` are gone: they built a shape
(top-level `corporate_structure`/`leadership`/... kwargs) the current
discriminated-union `FactPack` schema rejects outright (`extra="forbid"`).

What remains here is what `perplexity_source` still needs: the retry-wrapped
request schema (`_FactPackRaw`), the system prompt (`_SYSTEM_FR`), the legacy
full-fact prompt builder (`_build_prompt`, still covered by its own tests), and
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

from finwiz.analysis._helpers import _today_french

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


def _run_coroutine_sync[T](coro: Coroutine[Any, Any, T], *, timeout: float) -> T | None:
    """Run a coroutine from sync code. Inside a running loop, use a worker thread.

    Extracted from the old `fetch_fact_pack_sync` body (Task 8) so
    `perplexity_source.fetch_missing_events` can share the same event-loop
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
