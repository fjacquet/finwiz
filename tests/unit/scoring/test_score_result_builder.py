"""Unit tests for ScoreResultBuilder.

Regression coverage for a fundamental_score of None (crypto holdings where no
fundamental component survived — see CryptoAnalyzer.calculate_fundamental_score
and _compute_weighted_score in deep_analysis_scorer.py). build_result must not
crash, and must never substitute a fabricated number for the missing score.
"""

import pytest

from finwiz.scoring.score_result_builder import ScoreResultBuilder
from finwiz.validation.quality_metrics import DataQualityMetrics


@pytest.fixture
def builder():
    return ScoreResultBuilder()


@pytest.fixture
def data_quality_metrics():
    return DataQualityMetrics()


class TestBuildResultWithMissingFundamental:
    """build_result tolerates scores['fundamental_score'] being None."""

    def test_build_result_does_not_raise_when_fundamental_is_none(self, builder, data_quality_metrics):
        scores = {
            "fundamental_score": None,
            "fundamental_details": {"excluded_components": ["market_cap", "volume", "age", "supply"], "market_cap": None, "volume_24h": None},
            "technical_score": 0.8,
            "technical_details": {"technical_score": 0.8, "rsi": 55.0, "trend_direction": "up"},
            "risk_score": 0.6,
            "risk_details": {"risk_score": 0.6, "volatility": 0.30, "max_drawdown": -0.15},
        }

        result = builder.build_result(
            ticker="ZZZ",
            asset_class="crypto",
            composite_score=0.7,
            scores=scores,
            data={},
            data_quality_metrics=data_quality_metrics,
        )

        assert result.fundamental_score is None

    def test_rationale_says_unavailable_not_a_fabricated_number(self, builder, data_quality_metrics):
        scores = {
            "fundamental_score": None,
            "fundamental_details": {"excluded_components": ["market_cap", "volume", "age", "supply"], "market_cap": None, "volume_24h": None},
            "technical_score": 0.8,
            "technical_details": {"technical_score": 0.8, "rsi": 55.0, "trend_direction": "up"},
            "risk_score": 0.6,
            "risk_details": {"risk_score": 0.6, "volatility": 0.30, "max_drawdown": -0.15},
        }

        result = builder.build_result(
            ticker="ZZZ",
            asset_class="crypto",
            composite_score=0.7,
            scores=scores,
            data={},
            data_quality_metrics=data_quality_metrics,
        )

        assert "unavailable" in result.rationale
        assert "score: 0.00" not in result.rationale
        assert "$0.0B" not in result.rationale
        assert "$0M" not in result.rationale

    def test_confidence_is_computed_over_available_scores_only(self, builder, data_quality_metrics):
        scores = {
            "fundamental_score": None,
            "fundamental_details": {"excluded_components": ["market_cap", "volume", "age", "supply"]},
            "technical_score": 0.8,
            "technical_details": {"technical_score": 0.8, "rsi": 55.0, "trend_direction": "up"},
            "risk_score": 0.6,
            "risk_details": {"risk_score": 0.6, "volatility": 0.30, "max_drawdown": -0.15},
        }

        result = builder.build_result(
            ticker="ZZZ",
            asset_class="crypto",
            composite_score=0.7,
            scores=scores,
            data={},
            data_quality_metrics=data_quality_metrics,
        )

        # std over [0.8, 0.6] only (mean 0.7) -> consistency 0.8; data_quality
        # 0.7 (all 3 key_fields missing from data={}) -> 0.8 * 0.7 = 0.56.
        assert result.confidence_level == pytest.approx(0.56)
        # Guards specifically against the rejected "coalesce to 0.0" fix: that
        # would pull the mean down and widen the spread, landing at 0.35 here.
        assert result.confidence_level != pytest.approx(0.35)

    def test_build_result_unaffected_when_fundamental_present(self, builder, data_quality_metrics):
        """Non-crypto / fully-populated crypto path is unchanged."""
        scores = {
            "fundamental_score": 0.9,
            "fundamental_details": {"fundamental_score": 0.9, "market_cap": 500e9, "volume_24h": 20e9},
            "technical_score": 0.8,
            "technical_details": {"technical_score": 0.8, "rsi": 55.0, "trend_direction": "up"},
            "risk_score": 0.6,
            "risk_details": {"risk_score": 0.6, "volatility": 0.30, "max_drawdown": -0.15},
        }

        result = builder.build_result(
            ticker="BTC",
            asset_class="crypto",
            composite_score=0.75,
            scores=scores,
            data={},
            data_quality_metrics=data_quality_metrics,
        )

        assert result.fundamental_score == 0.9
        assert "score: 0.90" in result.rationale
        assert "$500.0B" in result.rationale
        assert "$20000M" in result.rationale


class TestCalculateConfidenceNoneSafety:
    """_calculate_confidence directly, since it's the reported crash site."""

    def test_none_fundamental_does_not_raise(self, builder):
        confidence = builder._calculate_confidence(None, 0.8, 0.6, {})
        assert 0.0 <= confidence <= 1.0

    def test_none_fundamental_excludes_rather_than_coalesces_to_zero(self, builder):
        with_none = builder._calculate_confidence(None, 0.8, 0.6, {})
        coalesced_to_zero = builder._calculate_confidence(0.0, 0.8, 0.6, {})
        assert with_none != pytest.approx(coalesced_to_zero)
        assert with_none == pytest.approx(0.56)


class TestGetFundamentalRationaleNoneSafety:
    """_get_fundamental_rationale directly, for the crypto None-metrics branch."""

    def test_none_score_and_metrics_render_as_unavailable(self, builder):
        rationale = builder._get_fundamental_rationale("crypto", None, {"market_cap": None, "volume_24h": None})
        assert "unavailable" in rationale
        # No numeric stand-in should appear where the score or a metric is missing.
        assert "None" not in rationale

    def test_partial_none_renders_only_the_missing_metric_as_unavailable(self, builder):
        rationale = builder._get_fundamental_rationale("crypto", 0.95, {"market_cap": 1_629_408_510_367.0, "volume_24h": None})
        assert "score: 0.95" in rationale
        assert "$1629.4B" in rationale
        assert "24h volume of unavailable" in rationale
