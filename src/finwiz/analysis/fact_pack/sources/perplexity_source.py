"""Perplexity, narrowed to the one field structured data cannot supply.

Funds and crypto are complete without it. Equities are too, when the company
files with the SEC or a wire service covered it. What remains is a company with
neither — measured at 6 of 67 holdings.
"""

from __future__ import annotations

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_EVENT_MAX_CHARS = 200
_MAX_EVENTS = 10


def fetch_missing_events(ticker: str, company_name: str, sector: str | None, industry: str | None, timeout: float = 15.0) -> tuple[str, ...]:
    """Material events for one company. Any failure returns empty; never raises."""
    from finwiz.analysis._helpers import _today_french
    from finwiz.analysis.fact_pack_research import _SYSTEM_FR, _FactPackRaw, _run_coroutine_sync
    from finwiz.infrastructure.resilience.perplexity_retry import perplexity_with_retry

    prompt = (
        f"Date du jour : {_today_french()}.\n\n"
        f"Recherche UNIQUEMENT les événements matériels des 12 derniers mois pour "
        f"{company_name} ({ticker}, {sector or 'secteur inconnu'} / {industry or 'industrie inconnue'}) : "
        "résultats trimestriels notables, fusions-acquisitions, changements de direction, "
        "décisions réglementaires ou judiciaires majeures. Pas de bavardage marketing, "
        "pas de prévisions. Si tu n'as pas de source fiable, renvoie une liste vide."
    )

    try:
        raw = _run_coroutine_sync(
            perplexity_with_retry(prompt=prompt, schema=_FactPackRaw, system=_SYSTEM_FR, search_recency_filter="month", timeout=timeout),
            timeout=timeout,
        )
    except Exception as e:
        logger.warning(f"fact_pack gap-fill failed for {ticker}: {e}")
        return ()

    if raw is None:
        return ()
    return tuple(event[:_EVENT_MAX_CHARS] for event in raw.recent_events[:_MAX_EVENTS])
