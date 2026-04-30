"""Schema tests for QuantitativeAnalysis.price_targets (ADR-011)."""

from datetime import UTC, datetime

from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics
from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis
from finwiz.schemas.portfolio_review import PriceTargets


def _build_quant(price_targets: PriceTargets | None = None) -> QuantitativeAnalysis:
    return QuantitativeAnalysis(
        composite_score=0.7,
        fundamental_score=0.7,
        technical_score=0.7,
        risk_score=2.0,
        grade="B",
        preliminary_recommendation="HOLD",
        fundamental_metrics={},
        technical_indicators={},
        risk_metrics={},
        calculation_timestamp=datetime.now(),
        data_quality=DataQualityMetrics(
            completeness_score=0.9,
            freshness_score=1.0,
            accuracy_confidence=0.9,
            source_reliability=0.85,
        ),
        confidence_level=0.9,
        python_rationale="placeholder rationale",
        price_targets=price_targets,
    )


def test_quantitative_analysis_accepts_none_price_targets() -> None:
    quant = _build_quant(price_targets=None)
    assert quant.price_targets is None


def test_quantitative_analysis_accepts_pricetargets_instance() -> None:
    pt = PriceTargets(
        current_price=100.0,
        currency="USD",
        buy_target_primary=120.0,
        sell_target_primary=85.0,
        buy_rationale="r1",
        sell_rationale="r2",
        data_as_of=datetime.now(tz=UTC),
    )
    quant = _build_quant(price_targets=pt)
    assert quant.price_targets is not None
    assert quant.price_targets.buy_target_primary == 120.0
