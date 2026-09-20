"""Web research, narrowed to the one field structured data cannot supply.

Funds and crypto are complete without it. Equities are too, when the company
files with the SEC or a wire service covered it. What remains is a company with
neither — measured at 6 of 67 holdings. The call goes through
``research_with_retry`` (OpenRouter web plugin, Perplexity as fallback).
"""

from __future__ import annotations

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_EVENT_MAX_CHARS = 200
_MAX_EVENTS = 10

_GAP_FILL_ATTEMPTS = 3
"""OpenRouter attempts research_with_retry gets, passed explicitly so the outer
timeout below can be computed from the same number rather than assumed."""

_BACKOFF_ALLOWANCE = 10.0
"""Slack added to the outer cap for the exponential backoff research_with_retry
sleeps between attempts (on top of each attempt's own `timeout`)."""


def fetch_missing_events(ticker: str, company_name: str, sector: str | None, industry: str | None, timeout: float = 15.0) -> tuple[str, ...]:
    """Material events for one company. Any failure returns empty; never raises."""
    from finwiz.analysis._helpers import _today_french
    from finwiz.analysis.fact_pack_research import _SYSTEM_FR, _FactPackRaw, _run_coroutine_sync
    from finwiz.infrastructure.resilience.research_retry import research_with_retry

    prompt = (
        f"Date du jour : {_today_french()}.\n\n"
        f"Recherche UNIQUEMENT les événements matériels des 12 derniers mois pour "
        f"{company_name} ({ticker}, {sector or 'secteur inconnu'} / {industry or 'industrie inconnue'}) : "
        "résultats trimestriels notables, fusions-acquisitions, changements de direction, "
        "décisions réglementaires ou judiciaires majeures. Pas de bavardage marketing, "
        "pas de prévisions. Si tu n'as pas de source fiable, renvoie une liste vide."
    )

    # The inner budget is up to _GAP_FILL_ATTEMPTS OpenRouter attempts at
    # `timeout` each, plus one Perplexity fallback attempt of `timeout`, plus
    # exponential backoff between attempts (~_BACKOFF_ALLOWANCE seconds). The
    # outer _run_coroutine_sync cap must exceed that inner budget, or it cuts
    # the coroutine off mid-retry and discards work already paid for while the
    # thread keeps spending (the PR #66 timeout-layering lesson).
    outer_timeout = timeout * (_GAP_FILL_ATTEMPTS + 1) + _BACKOFF_ALLOWANCE
    try:
        result = _run_coroutine_sync(
            research_with_retry(
                prompt=prompt, schema=_FactPackRaw, system=_SYSTEM_FR, search_recency_filter="month", timeout=timeout, max_attempts=_GAP_FILL_ATTEMPTS, kind="factpack"
            ),
            timeout=outer_timeout,
        )
    except Exception as e:
        logger.warning(f"fact_pack gap-fill failed for {ticker}: {e}")
        return ()

    if result is None:
        return ()
    return tuple(event[:_EVENT_MAX_CHARS] for event in result.data.recent_events[:_MAX_EVENTS])
