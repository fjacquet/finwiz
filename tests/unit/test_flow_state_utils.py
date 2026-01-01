"""Tests for flow_state_utils.py and flow_state_analysis.py modules."""

import logging

import pytest

from finwiz.flow_state_analysis import (
    _determine_market_sentiment,
    _determine_risk_level,
    _extract_insights_from_tasks,
    _extract_opportunities,
    _extract_risk_factors,
    prepare_core_analysis_summary,
)
from finwiz.flow_state_models import FinwizState
from finwiz.flow_state_utils import (
    check_core_analysis_availability,
    extract_market_conditions,
    extract_market_context_from_core_analysis,
    get_degraded_functionality_summary,
)


@pytest.fixture
def logger():
    """Provide a test logger."""
    return logging.getLogger("test_flow_state_utils")


@pytest.fixture
def base_state():
    """Provide a base FinwizState for testing."""
    return FinwizState()


class TestCheckCoreAnalysisAvailability:
    """Tests for check_core_analysis_availability function."""

    def test_should_check_availability_from_integration_manager(self, mocker, logger):
        """Test checking availability through integration manager."""
        mock_manager = mocker.MagicMock()
        mock_manager.get_crew_data_with_freshness_check.side_effect = [
            {"data": "stock"},  # stock available
            None,  # etf not available
            {"data": "crypto"},  # crypto available
        ]
        mocker.patch(
            "finwiz.integration.manager.CrewDataIntegrationManager",
            return_value=mock_manager,
        )

        state = FinwizState()
        result = check_core_analysis_availability(state, logger)

        assert result["stock_available"] is True
        assert result["etf_available"] is False
        assert result["crypto_available"] is True
        assert result["any_available"] is True
        assert "stock" in result["available_crews"]
        assert "crypto" in result["available_crews"]
        assert "etf" not in result["available_crews"]
        assert result["total_available"] == 2

    def test_should_fallback_to_state_flags_on_error(self, mocker, logger):
        """Test fallback to state flags when integration manager fails."""
        mock_manager = mocker.MagicMock()
        mock_manager.get_crew_data_with_freshness_check.side_effect = Exception("Connection error")
        mocker.patch(
            "finwiz.integration.manager.CrewDataIntegrationManager",
            return_value=mock_manager,
        )

        state = FinwizState(
            stock_analysis_success=True,
            etf_analysis_success=False,
            etf_analysis_fallback=True,
            etf_analysis_result={"data": "fallback"},
            crypto_analysis_success=False,
        )
        result = check_core_analysis_availability(state, logger)

        assert result["stock_available"] is True
        assert result["etf_available"] is True  # fallback with result
        assert result["crypto_available"] is False

    def test_should_track_failed_crews(self, mocker, logger):
        """Test tracking of failed crews."""
        mock_manager = mocker.MagicMock()
        mock_manager.get_crew_data_with_freshness_check.return_value = None
        mocker.patch(
            "finwiz.integration.manager.CrewDataIntegrationManager",
            return_value=mock_manager,
        )

        state = FinwizState(
            stock_analysis_error="API error",
            etf_analysis_error=None,
            crypto_analysis_error="Timeout",
        )
        result = check_core_analysis_availability(state, logger)

        assert "stock" in result["failed_crews"]
        assert "crypto" in result["failed_crews"]
        assert "etf" not in result["failed_crews"]
        assert result["total_failed"] == 2

    def test_should_track_disabled_crews(self, mocker, logger):
        """Test tracking of disabled crews."""
        mock_manager = mocker.MagicMock()
        mock_manager.get_crew_data_with_freshness_check.return_value = None
        mocker.patch(
            "finwiz.integration.manager.CrewDataIntegrationManager",
            return_value=mock_manager,
        )

        state = FinwizState(
            stock_analysis_disabled=False,
            etf_analysis_disabled=True,
            crypto_analysis_disabled=True,
        )
        result = check_core_analysis_availability(state, logger)

        assert "etf" in result["disabled_crews"]
        assert "crypto" in result["disabled_crews"]
        assert "stock" not in result["disabled_crews"]
        assert result["total_disabled"] == 2


class TestExtractMarketConditions:
    """Tests for extract_market_conditions function."""

    def test_should_extract_stock_conditions(self):
        """Test extracting conditions when stock analysis available."""
        state = FinwizState(stock_analysis_result={"market": "bullish"})
        result = extract_market_conditions(state)

        assert "stock_market_sentiment" in result
        assert "Available from stock analysis" in result["stock_market_sentiment"]

    def test_should_extract_etf_conditions(self):
        """Test extracting conditions when ETF analysis available."""
        state = FinwizState(etf_analysis_result={"sectors": ["tech", "finance"]})
        result = extract_market_conditions(state)

        assert "sector_trends" in result
        assert "Available from ETF analysis" in result["sector_trends"]

    def test_should_extract_crypto_conditions(self):
        """Test extracting conditions when crypto analysis available."""
        state = FinwizState(crypto_analysis_result={"market": "volatile"})
        result = extract_market_conditions(state)

        assert "crypto_market_dynamics" in result
        assert "Available from crypto analysis" in result["crypto_market_dynamics"]

    def test_should_return_empty_when_no_results(self):
        """Test empty conditions when no analysis results."""
        state = FinwizState()
        result = extract_market_conditions(state)

        assert result == {}

    def test_should_extract_all_conditions(self):
        """Test extracting all conditions when all analyses available."""
        state = FinwizState(
            stock_analysis_result={"market": "bullish"},
            etf_analysis_result={"sectors": ["tech"]},
            crypto_analysis_result={"market": "volatile"},
        )
        result = extract_market_conditions(state)

        assert len(result) == 3
        assert "stock_market_sentiment" in result
        assert "sector_trends" in result
        assert "crypto_market_dynamics" in result


class TestExtractMarketContextFromCoreAnalysis:
    """Tests for extract_market_context_from_core_analysis function."""

    def test_should_return_default_context_for_empty_data(self, logger):
        """Test default context is returned for empty data."""
        result = extract_market_context_from_core_analysis({}, logger)

        assert result["overall_sentiment"] == "neutral"
        assert result["market_trends"] == []
        assert result["risk_factors"] == []
        assert result["opportunities"] == []
        assert result["sector_analysis"] == {}

    def test_should_extract_stock_sentiments_positive(self, logger):
        """Test extracting positive sentiment from stock data."""
        core_data = {
            "stock_analysis": {
                "market_sentiments": [
                    {"sentiment": "positive"},
                    {"sentiment": "bullish"},
                    {"sentiment": "negative"},
                ]
            }
        }
        result = extract_market_context_from_core_analysis(core_data, logger)

        assert result["overall_sentiment"] == "positive"

    def test_should_extract_stock_sentiments_negative(self, logger):
        """Test extracting negative sentiment from stock data."""
        core_data = {
            "stock_analysis": {
                "market_sentiments": [
                    {"sentiment": "negative"},
                    {"sentiment": "bearish"},
                    {"sentiment": "bearish"},
                    {"sentiment": "positive"},
                ]
            }
        }
        result = extract_market_context_from_core_analysis(core_data, logger)

        assert result["overall_sentiment"] == "negative"

    def test_should_extract_sector_analysis(self, logger):
        """Test extracting sector analysis from stock data."""
        core_data = {"stock_analysis": {"sector_analysis": {"tech": "bullish", "finance": "neutral"}}}
        result = extract_market_context_from_core_analysis(core_data, logger)

        assert result["sector_analysis"] == {"tech": "bullish", "finance": "neutral"}

    def test_should_extract_etf_trends(self, logger):
        """Test extracting sector trends from ETF data."""
        core_data = {"etf_analysis": {"sector_trends": ["tech growth", "bond decline"]}}
        result = extract_market_context_from_core_analysis(core_data, logger)

        assert "tech growth" in result["market_trends"]
        assert "bond decline" in result["market_trends"]

    def test_should_extract_crypto_dynamics(self, logger):
        """Test extracting market dynamics from crypto data."""
        core_data = {"crypto_analysis": {"market_dynamics": "high volatility"}}
        result = extract_market_context_from_core_analysis(core_data, logger)

        assert "Crypto: high volatility" in result["market_trends"]

    def test_should_extract_common_risk_factors(self, logger):
        """Test extracting risk factors from multiple analyses."""
        core_data = {
            "stock_analysis": {"risk_factors": ["rate hikes", "inflation"]},
            "etf_analysis": {"risk_factors": ["market correction"]},
        }
        result = extract_market_context_from_core_analysis(core_data, logger)

        assert "rate hikes" in result["risk_factors"]
        assert "inflation" in result["risk_factors"]
        assert "market correction" in result["risk_factors"]

    def test_should_extract_common_opportunities(self, logger):
        """Test extracting opportunities from multiple analyses."""
        core_data = {
            "stock_analysis": {"opportunities": ["AI stocks"]},
            "crypto_analysis": {"opportunities": ["DeFi projects"]},
        }
        result = extract_market_context_from_core_analysis(core_data, logger)

        assert "AI stocks" in result["opportunities"]
        assert "DeFi projects" in result["opportunities"]

    def test_should_handle_exception_gracefully(self, logger, mocker):
        """Test graceful exception handling."""
        # Passing a non-dict value that will cause issues
        core_data = {"stock_analysis": "invalid_data"}
        result = extract_market_context_from_core_analysis(core_data, logger)

        # Should return default context
        assert result["overall_sentiment"] == "neutral"


class TestGetDegradedFunctionalitySummary:
    """Tests for get_degraded_functionality_summary function."""

    def test_should_return_clean_summary_when_no_degradation(self):
        """Test clean summary when no degradation."""
        state = FinwizState()
        result = get_degraded_functionality_summary(state)

        assert result["has_degraded_functionality"] is False
        assert result["degraded_crews"] == []
        assert result["fallback_strategies_used"] == []
        assert result["missing_features"] == []
        assert result["data_quality_issues"] == []

    def test_should_track_stock_degraded_functionality(self):
        """Test tracking stock degraded functionality."""
        state = FinwizState(stock_degraded_functionality=["real_time_quotes", "options_data"])
        result = get_degraded_functionality_summary(state)

        assert result["has_degraded_functionality"] is True
        assert "stock" in result["degraded_crews"]
        assert "real_time_quotes" in result["missing_features"]
        assert "options_data" in result["missing_features"]

    def test_should_track_etf_degraded_functionality(self):
        """Test tracking ETF degraded functionality."""
        state = FinwizState(etf_degraded_functionality=["holdings_breakdown"])
        result = get_degraded_functionality_summary(state)

        assert result["has_degraded_functionality"] is True
        assert "etf" in result["degraded_crews"]
        assert "holdings_breakdown" in result["missing_features"]

    def test_should_track_crypto_degraded_functionality(self):
        """Test tracking crypto degraded functionality."""
        state = FinwizState(crypto_degraded_functionality=["on_chain_metrics"])
        result = get_degraded_functionality_summary(state)

        assert result["has_degraded_functionality"] is True
        assert "crypto" in result["degraded_crews"]
        assert "on_chain_metrics" in result["missing_features"]

    def test_should_track_fallback_strategies(self):
        """Test tracking fallback strategies used."""
        state = FinwizState(
            stock_fallback_strategy="cached_data",
            etf_fallback_strategy="partial_analysis",
            crypto_fallback_strategy=None,
        )
        result = get_degraded_functionality_summary(state)

        assert "stock: cached_data" in result["fallback_strategies_used"]
        assert "etf: partial_analysis" in result["fallback_strategies_used"]
        assert len(result["fallback_strategies_used"]) == 2

    def test_should_track_stale_data_warning(self):
        """Test tracking stale data warnings."""
        state = FinwizState(stale_data_warnings=["Data older than 24 hours"])
        result = get_degraded_functionality_summary(state)

        assert "stale_data" in result["data_quality_issues"]

    def test_should_track_integration_error(self):
        """Test tracking integration errors."""
        state = FinwizState(integrated_data_error="Failed to merge data")
        result = get_degraded_functionality_summary(state)

        assert "integration_error" in result["data_quality_issues"]

    def test_should_track_all_degradation_types(self):
        """Test tracking all types of degradation."""
        state = FinwizState(
            stock_degraded_functionality=["feature1"],
            etf_degraded_functionality=["feature2"],
            crypto_degraded_functionality=["feature3"],
            stock_fallback_strategy="strategy1",
            stale_data_warnings=["warning"],
            integrated_data_error="error",
        )
        result = get_degraded_functionality_summary(state)

        assert result["has_degraded_functionality"] is True
        assert len(result["degraded_crews"]) == 3
        assert len(result["missing_features"]) == 3
        assert len(result["fallback_strategies_used"]) == 1
        assert len(result["data_quality_issues"]) == 2


class TestPrepareCoreAnalysisSummary:
    """Tests for prepare_core_analysis_summary function."""

    def test_should_return_default_summary_for_empty_data(self, logger):
        """Test default summary for empty consolidated data."""
        result = prepare_core_analysis_summary({}, logger)

        assert result["available_analyses"] == []
        assert result["total_recommendations"] == 0
        assert result["overall_market_sentiment"] == "neutral"
        assert result["key_insights"] == []
        assert result["risk_assessment"]["overall_risk_level"] == "low"
        assert result["investment_opportunities"]["stocks"] == []

    def test_should_track_available_analyses(self, logger):
        """Test tracking of available analyses."""
        consolidated_data = {
            "stock": {"raw_output": "Analysis complete"},
            "etf": {"raw_output": "ETF analysis done"},
        }
        result = prepare_core_analysis_summary(consolidated_data, logger)

        assert "stock" in result["available_analyses"]
        assert "etf" in result["available_analyses"]
        assert "crypto" not in result["available_analyses"]

    def test_should_count_buy_recommendations(self, logger):
        """Test counting buy recommendations from raw output."""
        consolidated_data = {
            "stock": {"raw_output": "Buy AAPL, Strong buy MSFT, Hold GOOG"},
            "etf": {"raw_output": "Buy VTI"},
        }
        result = prepare_core_analysis_summary(consolidated_data, logger)

        # "Buy" appears 3 times total (case insensitive)
        assert result["total_recommendations"] >= 3

    def test_should_extract_from_consolidated_crew_data(self, logger):
        """Test extraction from nested consolidated_crew_data."""
        consolidated_data = {
            "consolidated_crew_data": {
                "stock": {"raw_output": "Buy recommendation"},
                "crypto": {"raw_output": "Hold position"},
            }
        }
        result = prepare_core_analysis_summary(consolidated_data, logger)

        assert "stock" in result["available_analyses"]
        assert "crypto" in result["available_analyses"]

    def test_should_handle_exception_gracefully(self, logger, mocker):
        """Test graceful exception handling."""
        # Create a mock object that raises an exception when accessed
        bad_crew_data = mocker.MagicMock()
        bad_crew_data.__getitem__.side_effect = Exception("Test exception")

        # Create data structure that will cause issues
        consolidated_data = {"stock": bad_crew_data}
        result = prepare_core_analysis_summary(consolidated_data, logger)

        # Should return summary with just "stock" in available_analyses
        # The exception handling catches errors during data extraction
        assert "stock" in result["available_analyses"]
        assert result["overall_market_sentiment"] == "neutral"


class TestExtractInsightsFromTasks:
    """Tests for _extract_insights_from_tasks helper function."""

    def test_should_extract_insights_from_tasks_output(self):
        """Test extracting insights from task outputs."""
        crew_data = {
            "tasks_output": [
                {"raw": "A" * 150},  # Long enough to be included
                {"raw": "Short"},  # Too short
            ]
        }
        summary = {"key_insights": []}

        _extract_insights_from_tasks(crew_data, "stock", summary)

        assert len(summary["key_insights"]) == 1
        assert summary["key_insights"][0]["source"] == "stock"

    def test_should_truncate_long_insights(self):
        """Test that long insights are truncated."""
        crew_data = {"tasks_output": [{"raw": "A" * 300}]}
        summary = {"key_insights": []}

        _extract_insights_from_tasks(crew_data, "stock", summary)

        assert len(summary["key_insights"][0]["insight"]) <= 203  # 200 + "..."

    def test_should_handle_non_dict_tasks(self):
        """Test handling of non-dict task entries."""
        crew_data = {"tasks_output": ["string_task", {"raw": "A" * 150}]}
        summary = {"key_insights": []}

        _extract_insights_from_tasks(crew_data, "stock", summary)

        assert len(summary["key_insights"]) == 1


class TestExtractOpportunities:
    """Tests for _extract_opportunities helper function."""

    def test_should_extract_stock_opportunities(self):
        """Test extracting stock opportunities."""
        crew_data = {"pydantic": {"opportunities": ["AAPL", "MSFT", "GOOG", "NVDA"]}}
        summary = {"investment_opportunities": {"stocks": [], "etfs": [], "cryptos": []}}

        _extract_opportunities(crew_data, "stock", summary)

        assert len(summary["investment_opportunities"]["stocks"]) == 3  # Limited to 3

    def test_should_extract_etf_opportunities(self):
        """Test extracting ETF opportunities."""
        crew_data = {"pydantic": {"opportunities": ["VTI", "VOO"]}}
        summary = {"investment_opportunities": {"stocks": [], "etfs": [], "cryptos": []}}

        _extract_opportunities(crew_data, "etf", summary)

        assert len(summary["investment_opportunities"]["etfs"]) == 2

    def test_should_extract_crypto_opportunities(self):
        """Test extracting crypto opportunities."""
        crew_data = {"pydantic": {"opportunities": ["BTC", "ETH"]}}
        summary = {"investment_opportunities": {"stocks": [], "etfs": [], "cryptos": []}}

        _extract_opportunities(crew_data, "crypto", summary)

        assert len(summary["investment_opportunities"]["cryptos"]) == 2

    def test_should_handle_missing_pydantic_data(self):
        """Test handling when pydantic data is missing."""
        crew_data = {"raw_output": "No pydantic data"}
        summary = {"investment_opportunities": {"stocks": [], "etfs": [], "cryptos": []}}

        _extract_opportunities(crew_data, "stock", summary)

        assert summary["investment_opportunities"]["stocks"] == []

    def test_should_handle_empty_opportunities(self):
        """Test handling empty opportunities list."""
        crew_data = {"pydantic": {"opportunities": []}}
        summary = {"investment_opportunities": {"stocks": [], "etfs": [], "cryptos": []}}

        _extract_opportunities(crew_data, "stock", summary)

        assert summary["investment_opportunities"]["stocks"] == []


class TestDetermineMarketSentiment:
    """Tests for _determine_market_sentiment helper function."""

    def test_should_determine_positive_sentiment(self):
        """Test determining positive market sentiment."""
        consolidated_data = {"market_sentiment": {"aggregated_scores": {"positive": 0.6, "negative": 0.3}}}
        summary = {"overall_market_sentiment": "neutral"}

        _determine_market_sentiment(consolidated_data, summary)

        assert summary["overall_market_sentiment"] == "positive"

    def test_should_determine_negative_sentiment(self):
        """Test determining negative market sentiment."""
        consolidated_data = {"market_sentiment": {"aggregated_scores": {"positive": 0.2, "negative": 0.7}}}
        summary = {"overall_market_sentiment": "neutral"}

        _determine_market_sentiment(consolidated_data, summary)

        assert summary["overall_market_sentiment"] == "negative"

    def test_should_remain_neutral_when_close(self):
        """Test neutral sentiment when scores are close."""
        consolidated_data = {"market_sentiment": {"aggregated_scores": {"positive": 0.45, "negative": 0.45}}}
        summary = {"overall_market_sentiment": "neutral"}

        _determine_market_sentiment(consolidated_data, summary)

        assert summary["overall_market_sentiment"] == "neutral"

    def test_should_handle_missing_sentiment_data(self):
        """Test handling missing sentiment data."""
        consolidated_data = {}
        summary = {"overall_market_sentiment": "neutral"}

        _determine_market_sentiment(consolidated_data, summary)

        assert summary["overall_market_sentiment"] == "neutral"


class TestExtractRiskFactors:
    """Tests for _extract_risk_factors helper function."""

    def test_should_extract_risk_keywords(self):
        """Test extracting risk-related keywords."""
        consolidated_data = {"stock": {"raw_output": "High risk due to volatility and uncertainty"}}
        summary = {"risk_assessment": {"major_risk_factors": []}}

        _extract_risk_factors(consolidated_data, summary)

        assert len(summary["risk_assessment"]["major_risk_factors"]) >= 2

    def test_should_extract_from_multiple_crews(self):
        """Test extracting risks from multiple crew analyses."""
        consolidated_data = {
            "stock": {"raw_output": "Risk warning issued"},
            "etf": {"raw_output": "Concern about volatility"},
        }
        summary = {"risk_assessment": {"major_risk_factors": []}}

        _extract_risk_factors(consolidated_data, summary)

        assert len(summary["risk_assessment"]["major_risk_factors"]) >= 3

    def test_should_handle_no_risk_keywords(self):
        """Test handling when no risk keywords found."""
        consolidated_data = {"stock": {"raw_output": "All clear, positive outlook"}}
        summary = {"risk_assessment": {"major_risk_factors": []}}

        _extract_risk_factors(consolidated_data, summary)

        assert summary["risk_assessment"]["major_risk_factors"] == []


class TestDetermineRiskLevel:
    """Tests for _determine_risk_level helper function."""

    def test_should_determine_high_risk(self):
        """Test determining high risk level."""
        summary = {
            "risk_assessment": {
                "major_risk_factors": ["r1", "r2", "r3", "r4", "r5"],
                "overall_risk_level": "medium",
            }
        }

        _determine_risk_level(summary)

        assert summary["risk_assessment"]["overall_risk_level"] == "high"

    def test_should_determine_medium_risk(self):
        """Test determining medium risk level."""
        summary = {
            "risk_assessment": {
                "major_risk_factors": ["r1", "r2", "r3"],
                "overall_risk_level": "low",
            }
        }

        _determine_risk_level(summary)

        assert summary["risk_assessment"]["overall_risk_level"] == "medium"

    def test_should_determine_low_risk(self):
        """Test determining low risk level."""
        summary = {
            "risk_assessment": {
                "major_risk_factors": ["r1"],
                "overall_risk_level": "medium",
            }
        }

        _determine_risk_level(summary)

        assert summary["risk_assessment"]["overall_risk_level"] == "low"

    def test_should_determine_low_risk_with_no_factors(self):
        """Test determining low risk level with no factors."""
        summary = {
            "risk_assessment": {
                "major_risk_factors": [],
                "overall_risk_level": "high",
            }
        }

        _determine_risk_level(summary)

        assert summary["risk_assessment"]["overall_risk_level"] == "low"


class TestIntegration:
    """Integration tests for flow state utilities."""

    def test_should_process_complete_analysis_workflow(self, mocker, logger):
        """Test complete analysis workflow with all utilities."""
        # Mock the integration manager
        mock_manager = mocker.MagicMock()
        mock_manager.get_crew_data_with_freshness_check.return_value = {"data": "available"}
        mocker.patch(
            "finwiz.integration.manager.CrewDataIntegrationManager",
            return_value=mock_manager,
        )

        # Create a state with analysis results
        state = FinwizState(
            stock_analysis_result={"market": "bullish"},
            etf_analysis_result={"sectors": ["tech"]},
            crypto_analysis_result={"market": "volatile"},
            stock_analysis_success=True,
            etf_analysis_success=True,
            crypto_analysis_success=True,
        )

        # Check availability
        availability = check_core_analysis_availability(state, logger)
        assert availability["any_available"] is True

        # Extract market conditions
        conditions = extract_market_conditions(state)
        assert len(conditions) == 3

        # Get degraded functionality summary
        degraded = get_degraded_functionality_summary(state)
        assert degraded["has_degraded_functionality"] is False

    def test_should_handle_partial_analysis_results(self, mocker, logger):
        """Test handling partial analysis results."""
        mock_manager = mocker.MagicMock()
        mock_manager.get_crew_data_with_freshness_check.side_effect = [
            {"data": "stock"},
            None,
            None,
        ]
        mocker.patch(
            "finwiz.integration.manager.CrewDataIntegrationManager",
            return_value=mock_manager,
        )

        state = FinwizState(
            stock_analysis_result={"market": "bullish"},
            stock_analysis_success=True,
            etf_analysis_error="API timeout",
            crypto_analysis_disabled=True,
        )

        availability = check_core_analysis_availability(state, logger)

        assert availability["stock_available"] is True
        assert availability["etf_available"] is False
        assert availability["crypto_available"] is False
        assert "etf" in availability["failed_crews"]
        assert "crypto" in availability["disabled_crews"]

    def test_should_prepare_summary_from_core_analysis(self, logger):
        """Test preparing summary from core analysis data."""
        consolidated_data = {
            "consolidated_crew_data": {
                "stock": {
                    "raw_output": "Buy AAPL with high risk. Market shows volatility.",
                    "tasks_output": [{"raw": "A" * 150}],
                    "pydantic": {"opportunities": ["AAPL", "MSFT"]},
                },
                "etf": {
                    "raw_output": "Buy VTI. Low concern.",
                    "pydantic": {"opportunities": ["VTI"]},
                },
            },
            "market_sentiment": {"aggregated_scores": {"positive": 0.6, "negative": 0.2}},
        }

        summary = prepare_core_analysis_summary(consolidated_data, logger)

        assert "stock" in summary["available_analyses"]
        assert "etf" in summary["available_analyses"]
        assert summary["total_recommendations"] >= 2
        assert summary["overall_market_sentiment"] == "positive"
        assert len(summary["key_insights"]) >= 1
        assert len(summary["investment_opportunities"]["stocks"]) >= 1
        assert summary["risk_assessment"]["overall_risk_level"] in ["low", "medium", "high"]
