# tests/unit/analysis/test_helpers.py
from __future__ import annotations

from typing import Any

from finwiz.analysis._helpers import (
    _filter_numeric_values,
    _summarize_metrics,
    _today_french,
    _truncate_text,
)


def test_today_french_returns_long_date_string() -> None:
    out = _today_french()
    assert any(month in out for month in ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"])


def test_filter_numeric_values_drops_non_numeric() -> None:
    assert _filter_numeric_values({"a": 1, "b": "x", "c": 2.5, "d": None}) == {"a": 1.0, "c": 2.5}


def test_truncate_text_caps_length() -> None:
    assert len(_truncate_text("x" * 1000, max_chars=100)) <= 100 + 3  # +3 for "..." ellipsis


def test_summarize_metrics_returns_string() -> None:
    out = _summarize_metrics({"pe_ratio": 18.5, "roe": 0.22}, max_items=10)
    assert "pe_ratio" in out


def _make_quant() -> Any:
    """Build a minimal valid QuantitativeAnalysis for testing."""
    from datetime import datetime

    from finwiz.schemas.hybrid_analysis import QuantitativeAnalysis
    from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics

    return QuantitativeAnalysis(
        composite_score=0.65,
        fundamental_score=0.70,
        technical_score=0.60,
        risk_score=2.5,
        grade="B",
        preliminary_recommendation="HOLD",
        fundamental_metrics={"roe": 0.15},
        technical_indicators={"rsi": 55.0},
        risk_metrics={"volatility": 0.18},
        calculation_timestamp=datetime.now(),
        data_quality=DataQualityMetrics(
            completeness_score=0.9,
            freshness_score=1.0,
            accuracy_confidence=0.85,
            source_reliability=0.85,
            missing_fields=[],
        ),
        confidence_level=0.85,
        python_rationale="Solid fundamentals with stable technical signals",
    )


def test_build_crew_inputs_with_fact_pack() -> None:
    """When fact_pack is provided, all 5 keys flow into the inputs dict."""
    from datetime import UTC, datetime

    from finwiz.analysis._helpers import _build_crew_inputs
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext
    from finwiz.schemas.hybrid_analysis.fact_pack import FactPack

    fetched_at = datetime.now(UTC)
    fp = FactPack(
        corporate_structure="Independent — divested VMware Nov 2021",
        recent_events=["Q4 earnings beat", "New CEO appointed"],
        leadership="Michael Dell (CEO), Yvonne McGill (CFO)",
        fetched_at=fetched_at,
        freshness=FactPack.derive_freshness(fetched_at),
        confidence=0.92,
        source_citations=[],
    )

    ctx = AnalysisContext(ticker="DELL", asset_class="stock", company_name="Dell Technologies")
    quant = _make_quant()
    raw: dict = {"sector": "Tech", "industry": "Hardware"}

    inputs = _build_crew_inputs(ctx, quant, raw, fact_pack=fp)
    assert inputs["corporate_structure"] == "Independent — divested VMware Nov 2021"
    assert "Q4 earnings beat" in inputs["recent_events"]
    assert "New CEO appointed" in inputs["recent_events"]
    assert inputs["leadership"].startswith("Michael Dell")
    assert inputs["fact_pack_freshness"] == "fresh"
    assert inputs["fact_pack_confidence"] == "0.92"


def test_build_crew_inputs_without_fact_pack_substitutes_unknowns() -> None:
    """When fact_pack=None, fallback strings make the absence explicit to the AI."""
    from finwiz.analysis._helpers import _build_crew_inputs
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

    ctx = AnalysisContext(ticker="TEST", asset_class="stock", company_name="Test Corp")
    quant = _make_quant()
    raw: dict = {}

    inputs = _build_crew_inputs(ctx, quant, raw, fact_pack=None)
    assert inputs["corporate_structure"] == "Données non disponibles"
    assert inputs["recent_events"] == "Données non disponibles"
    assert inputs["leadership"] == "Données non disponibles"
    assert inputs["fact_pack_freshness"] == "unknown"
    assert inputs["fact_pack_confidence"] == "unknown"
