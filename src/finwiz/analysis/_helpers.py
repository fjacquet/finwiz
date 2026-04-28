"""Internal helpers for the deep-analysis pipeline."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from finwiz.schemas.hybrid_analysis import QuantitativeAnalysis
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack

if TYPE_CHECKING:
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

logger = logging.getLogger(__name__)


def _build_sentiment_summary(raw_data: dict[str, Any]) -> dict[str, Any] | None:
    """Build sentiment summary dict from raw_data for enriched JSON persistence.

    Extracts top headlines, aggregate score, confidence, and article counts
    from the news_sentiment data collected during raw data phase.

    Args:
        raw_data: Raw data dict potentially containing 'news_sentiment'.

    Returns:
        Sentiment summary dict or None if no news sentiment data available.
    """
    ns_raw = raw_data.get("news_sentiment")
    if ns_raw is None:
        return None

    try:
        # news_sentiment may be a dict (from model_dump) or a NewsSentimentResult
        if isinstance(ns_raw, dict):
            aggregate_sentiment = ns_raw.get("aggregate_sentiment", 0.0)
            article_count = ns_raw.get("article_count", 0)
            bullish_count = ns_raw.get("bullish_count", 0)
            bearish_count = ns_raw.get("bearish_count", 0)
            neutral_count = ns_raw.get("neutral_count", 0)
            articles = ns_raw.get("articles", [])
            # Confidence: not stored on NewsSentimentResult, compute from article count
            confidence = min(1.0, article_count / 10.0) if article_count > 0 else 0.0
        else:
            # NewsSentimentResult object
            aggregate_sentiment = getattr(ns_raw, "aggregate_sentiment", 0.0)
            article_count = getattr(ns_raw, "article_count", 0)
            bullish_count = getattr(ns_raw, "bullish_count", 0)
            bearish_count = getattr(ns_raw, "bearish_count", 0)
            neutral_count = getattr(ns_raw, "neutral_count", 0)
            articles = getattr(ns_raw, "articles", []) or []
            confidence = min(1.0, article_count / 10.0) if article_count > 0 else 0.0

        # Top 5 headlines
        top_headlines: list[dict[str, str]] = []
        for article in articles[:5]:
            if isinstance(article, dict):
                top_headlines.append(
                    {
                        "title": article.get("title", ""),
                        "source": article.get("source", ""),
                        "sentiment_label": article.get("sentiment_label", "neutral"),
                    }
                )
            else:
                top_headlines.append(
                    {
                        "title": getattr(article, "title", ""),
                        "source": getattr(article, "source", ""),
                        "sentiment_label": getattr(article, "sentiment_label", "neutral") or "neutral",
                    }
                )

        return {
            "score": aggregate_sentiment,
            "confidence": confidence,
            "article_count": article_count,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "top_headlines": top_headlines,
        }
    except Exception as e:
        logger.warning(f"Failed to build sentiment summary: {e}")
        return None


def _get_analysis_crew(asset_class: str) -> Any:
    """Factory for asset-specific crews."""
    from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

    # DeepAnalysisCrew handles all asset classes
    return DeepAnalysisCrew()


def _summarize_metrics(metrics: dict[str, float] | None, max_items: int = 10) -> str:
    """Summarize metrics dict to a compact string for AI context.

    Instead of passing the full dict (which can be 100K+ tokens),
    we pass a formatted summary of the top metrics.

    NOTE: Filters out None values to prevent format string errors like
    "unsupported format string passed to NoneType.__format__".
    """
    if not metrics:
        return "No data available"

    # Filter out None values BEFORE formatting to prevent format string errors
    valid_metrics = {k: v for k, v in metrics.items() if v is not None}

    if not valid_metrics:
        return "No data available"

    # Sort by absolute value (most significant metrics first)
    sorted_items = sorted(valid_metrics.items(), key=lambda x: abs(x[1]), reverse=True)

    # Take top N items and format compactly
    top_items = sorted_items[:max_items]
    parts = [f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in top_items]

    return ", ".join(parts)


def _truncate_text(text: str | None, max_chars: int = 500) -> str:
    """Truncate text to max_chars, preserving word boundaries.

    Prevents token overflow from large text fields like python_rationale.
    """
    if not text:
        return "Analysis based on available data."
    if len(text) <= max_chars:
        return text
    # Truncate at word boundary
    truncated = text[:max_chars].rsplit(" ", 1)[0]
    return truncated + "..."


_FR_MONTHS = {1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin", 7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"}


def _today_french() -> str:
    """Return today's date in long French form, e.g. ``26 avril 2026``.

    Used to anchor every AI prompt so models stop hallucinating from stale
    training-data corporate facts (mergers, divestitures, partnerships) that
    may have changed since their training cutoff.
    """
    today = datetime.now()
    return f"{today.day} {_FR_MONTHS[today.month]} {today.year}"


def _build_crew_inputs(ctx: AnalysisContext, quant: QuantitativeAnalysis, raw_data: dict[str, Any] | None = None, *, fact_pack: FactPack | None = None) -> dict[str, Any]:
    """Build inputs dict for crew kickoff.

    IMPORTANT: We pass SUMMARIZED metrics, not full dictionaries.
    Full dicts can be 100K+ tokens, causing context overflow errors.
    The AI only needs key metrics for qualitative insights.

    NOTE: All values have None-safe defaults to prevent format string errors
    like "unsupported format string passed to NoneType.__format__".
    """
    # Build inputs with None-safe defaults and size limits
    today = datetime.now()
    inputs = {
        "ticker": ctx.ticker or "UNKNOWN",
        "asset_class": ctx.asset_class or "stock",
        "company_name": ctx.company_name or ctx.ticker or "Unknown",
        # Anchor the AI to today's date so it stops citing pre-training corporate
        # structure (e.g. DELL/VMware integration that ended in Nov 2021).
        "current_date": _today_french(),
        "current_date_iso": today.strftime("%Y-%m-%d"),
        # Numeric defaults prevent "unsupported format string passed to NoneType"
        "grade": quant.grade or "C",
        "composite_score": quant.composite_score if quant.composite_score is not None else 0.5,
        "preliminary_recommendation": quant.preliminary_recommendation or "HOLD",
        "fundamental_score": quant.fundamental_score if quant.fundamental_score is not None else 0.5,
        "technical_score": quant.technical_score if quant.technical_score is not None else 0.5,
        "risk_score": quant.risk_score if quant.risk_score is not None else 0.5,
        # Pass SUMMARIES instead of full dicts to avoid token overflow
        "fundamental_metrics": _summarize_metrics(quant.fundamental_metrics, max_items=12) or "N/A",
        "technical_indicators": _summarize_metrics(quant.technical_indicators, max_items=10) or "N/A",
        "risk_metrics": _summarize_metrics(quant.risk_metrics, max_items=8) or "N/A",
        # Truncate rationale to prevent large text fields causing overflow
        "python_rationale": _truncate_text(quant.python_rationale, max_chars=500),
    }

    # Add company context from raw data to reduce AI hallucination
    if raw_data:
        inputs["sector"] = raw_data.get("sector", "Unknown")
        inputs["industry"] = raw_data.get("industry", "Unknown")
        business_summary = raw_data.get("business_summary", "")
        if business_summary and business_summary != "N/A":
            inputs["company_description"] = _truncate_text(business_summary, max_chars=500)
        else:
            inputs["company_description"] = "No company description available."
    else:
        inputs["sector"] = "Unknown"
        inputs["industry"] = "Unknown"
        inputs["company_description"] = "No company description available."

    # Inject FactPack keys (v5.2 grounded qualitative)
    if fact_pack is not None:
        inputs["corporate_structure"] = fact_pack.corporate_structure
        inputs["recent_events"] = "\n".join(f"- {e}" for e in fact_pack.recent_events) if fact_pack.recent_events else "Aucun événement matériel signalé."
        inputs["leadership"] = fact_pack.leadership
        inputs["fact_pack_freshness"] = fact_pack.freshness  # "fresh" / "recent" / "stale"
        inputs["fact_pack_confidence"] = f"{fact_pack.confidence:.2f}"
    else:
        inputs["corporate_structure"] = "Données non disponibles"
        inputs["recent_events"] = "Données non disponibles"
        inputs["leadership"] = "Données non disponibles"
        inputs["fact_pack_freshness"] = "unknown"
        inputs["fact_pack_confidence"] = "unknown"

    # DIAGNOSTIC: Log sizes of each input field for debugging
    total_chars = sum(len(str(v)) for v in inputs.values() if v is not None)
    estimated_tokens = total_chars // 4
    logger.info(f"Crew inputs for {ctx.ticker}: {total_chars:,} chars (~{estimated_tokens:,} tokens)")

    return inputs


def _filter_numeric_values(data: dict[str, Any] | None) -> dict[str, float]:
    """Filter dictionary to only include numeric values (int/float)."""
    if not data:
        return {}
    return {k: float(v) for k, v in data.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
