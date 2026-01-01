"""
Tests for CrewFactory module.

Tests cover:
- Initialization with caching options
- Crew execution methods for all asset types
- Error handling and fallback strategies
- Crew input preparation methods
- Market context extraction utilities
- Cache data wrapping
"""

import pytest
from faker import Faker

fake = Faker()


@pytest.fixture
def mock_integration_manager(mocker):
    """Create a mock integration manager."""
    manager = mocker.MagicMock()
    manager.store_crew_output = mocker.MagicMock()
    return manager


@pytest.fixture
def mock_error_handler(mocker):
    """Create a mock error handler."""
    handler = mocker.MagicMock()
    # Set up fallback response
    fallback_response = mocker.MagicMock()
    fallback_response.success = True
    fallback_response.data = {"fallback": "data"}
    fallback_response.message = "Using fallback"
    fallback_response.fallback_strategy = "cached_data"
    fallback_response.degraded_functionality = ["live_data"]
    handler.handle_crew_failure = mocker.MagicMock(return_value=fallback_response)
    return handler


@pytest.fixture
def crew_factory(mock_integration_manager, mock_error_handler, mocker):
    """Create a CrewFactory instance with mocks."""
    # Mock the crew output cache
    mocker.patch(
        "finwiz.crew_factory.get_crew_output_cache",
        return_value=mocker.MagicMock(),
    )
    # Mock feature flags - all enabled by default
    mocker.patch(
        "finwiz.crew_factory.is_feature_enabled",
        return_value=True,
    )
    # Mock environment variables for cache
    mocker.patch.dict("os.environ", {
        "CREW_CACHE_ENABLED": "true",
        "CREW_CACHE_MAX_AGE_HOURS": "24",
    })

    from finwiz.crew_factory import CrewFactory
    return CrewFactory(
        integration_manager=mock_integration_manager,
        error_handler=mock_error_handler,
    )


class TestCrewFactoryInitialization:
    """Tests for CrewFactory initialization."""

    def test_should_initialize_with_caching_enabled(self, mocker, mock_integration_manager, mock_error_handler):
        """Test initialization with caching enabled."""
        mocker.patch.dict("os.environ", {
            "CREW_CACHE_ENABLED": "true",
            "CREW_CACHE_MAX_AGE_HOURS": "12",
        })
        mock_cache = mocker.MagicMock()
        mocker.patch(
            "finwiz.crew_factory.get_crew_output_cache",
            return_value=mock_cache,
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        assert factory.cache_enabled is True
        assert factory.output_cache == mock_cache

    def test_should_initialize_with_caching_disabled(self, mocker, mock_integration_manager, mock_error_handler):
        """Test initialization with caching disabled."""
        mocker.patch.dict("os.environ", {
            "CREW_CACHE_ENABLED": "false",
            "CREW_CACHE_MAX_AGE_HOURS": "24",
        })

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        assert factory.cache_enabled is False
        assert factory.output_cache is None


class TestExecuteCryptoCrew:
    """Tests for execute_crypto_crew method."""

    def test_should_return_disabled_when_feature_flag_off(self, mocker, mock_integration_manager, mock_error_handler):
        """Test that crypto crew returns disabled when feature flag is off."""
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=False,
        )
        mocker.patch.dict("os.environ", {"CREW_CACHE_ENABLED": "false"})

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_crypto_crew({"ticker": "BTC"})

        assert result == {"crypto_analysis_disabled": True}

    def test_should_return_cached_data_when_available(self, mocker, mock_integration_manager, mock_error_handler):
        """Test that cached data is returned when available."""
        cached_data = {
            "ticker": "BTC",
            "analysis": "cached",
            "_cache_metadata": {"cache_age_hours": 2},
        }
        mock_cache = mocker.MagicMock()
        mock_cache.get_cached_crew_output = mocker.MagicMock(return_value=cached_data)

        mocker.patch(
            "finwiz.crew_factory.get_crew_output_cache",
            return_value=mock_cache,
        )
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=True,
        )
        mocker.patch.dict("os.environ", {
            "CREW_CACHE_ENABLED": "true",
            "CREW_CACHE_MAX_AGE_HOURS": "24",
        })

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_crypto_crew({"ticker": "BTC"})

        assert result["crypto_analysis_cached"] is True
        assert result["crypto_analysis_success"] is True
        assert result["cache_age_hours"] == 2

    def test_should_execute_crew_successfully(self, mocker, mock_integration_manager, mock_error_handler):
        """Test successful crew execution."""
        mock_cache = mocker.MagicMock()
        mock_cache.get_cached_crew_output = mocker.MagicMock(return_value=None)

        mocker.patch(
            "finwiz.crew_factory.get_crew_output_cache",
            return_value=mock_cache,
        )
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=True,
        )
        mocker.patch.dict("os.environ", {
            "CREW_CACHE_ENABLED": "true",
            "CREW_CACHE_MAX_AGE_HOURS": "24",
        })

        # Mock CryptoCrew
        mock_crew_instance = mocker.MagicMock()
        mock_crew = mocker.MagicMock()
        mock_crew_result = mocker.MagicMock()
        mock_crew_result.raw = '{"analysis": "complete"}'
        mock_crew.kickoff = mocker.MagicMock(return_value=mock_crew_result)
        mock_crew_instance.crew = mocker.MagicMock(return_value=mock_crew)

        mocker.patch(
            "finwiz.crew_factory.CryptoCrew",
            return_value=mock_crew_instance,
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_crypto_crew({"ticker": "BTC"})

        assert result["crypto_analysis_success"] is True
        assert result["crypto_analysis_cached"] is False
        assert result["core_analysis_completed"] is True

    def test_should_handle_crew_failure_with_fallback(self, mocker, mock_integration_manager, mock_error_handler):
        """Test error handling with fallback strategy."""
        mock_cache = mocker.MagicMock()
        mock_cache.get_cached_crew_output = mocker.MagicMock(return_value=None)

        mocker.patch(
            "finwiz.crew_factory.get_crew_output_cache",
            return_value=mock_cache,
        )
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=True,
        )
        mocker.patch.dict("os.environ", {
            "CREW_CACHE_ENABLED": "true",
            "CREW_CACHE_MAX_AGE_HOURS": "24",
        })

        # Mock CryptoCrew to raise exception
        mocker.patch(
            "finwiz.crew_factory.CryptoCrew",
            side_effect=Exception("Crew failed"),
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_crypto_crew({"ticker": "BTC"})

        assert result["crypto_analysis_success"] is False
        assert result["crypto_analysis_fallback"] is True
        assert "crypto_analysis_error" in result


class TestExecuteStockCrew:
    """Tests for execute_stock_crew method."""

    def test_should_return_disabled_when_feature_flag_off(self, mocker, mock_integration_manager, mock_error_handler):
        """Test that stock crew returns disabled when feature flag is off."""
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=False,
        )
        mocker.patch.dict("os.environ", {"CREW_CACHE_ENABLED": "false"})

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_stock_crew({"ticker": "AAPL"})

        assert result == {"stock_analysis_disabled": True}

    def test_should_execute_crew_successfully(self, mocker, mock_integration_manager, mock_error_handler):
        """Test successful stock crew execution."""
        mock_cache = mocker.MagicMock()
        mock_cache.get_cached_crew_output = mocker.MagicMock(return_value=None)

        mocker.patch(
            "finwiz.crew_factory.get_crew_output_cache",
            return_value=mock_cache,
        )
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=True,
        )
        mocker.patch.dict("os.environ", {
            "CREW_CACHE_ENABLED": "true",
            "CREW_CACHE_MAX_AGE_HOURS": "24",
        })

        # Mock StockCrew
        mock_crew_instance = mocker.MagicMock()
        mock_crew = mocker.MagicMock()
        mock_crew_result = mocker.MagicMock()
        mock_crew_result.raw = '{"analysis": "complete"}'
        mock_crew.kickoff = mocker.MagicMock(return_value=mock_crew_result)
        mock_crew_instance.crew = mocker.MagicMock(return_value=mock_crew)

        mocker.patch(
            "finwiz.crew_factory.StockCrew",
            return_value=mock_crew_instance,
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_stock_crew({"ticker": "AAPL"})

        assert result["stock_analysis_success"] is True
        assert result["stock_analysis_cached"] is False


class TestExecuteEtfCrew:
    """Tests for execute_etf_crew method."""

    def test_should_return_disabled_when_feature_flag_off(self, mocker, mock_integration_manager, mock_error_handler):
        """Test that ETF crew returns disabled when feature flag is off."""
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=False,
        )
        mocker.patch.dict("os.environ", {"CREW_CACHE_ENABLED": "false"})

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_etf_crew({"ticker": "SPY"})

        assert result == {"etf_analysis_disabled": True}

    def test_should_execute_crew_successfully(self, mocker, mock_integration_manager, mock_error_handler):
        """Test successful ETF crew execution."""
        mock_cache = mocker.MagicMock()
        mock_cache.get_cached_crew_output = mocker.MagicMock(return_value=None)

        mocker.patch(
            "finwiz.crew_factory.get_crew_output_cache",
            return_value=mock_cache,
        )
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=True,
        )
        mocker.patch.dict("os.environ", {
            "CREW_CACHE_ENABLED": "true",
            "CREW_CACHE_MAX_AGE_HOURS": "24",
        })

        # Mock EtfCrew
        mock_crew_instance = mocker.MagicMock()
        mock_crew = mocker.MagicMock()
        mock_crew_result = mocker.MagicMock()
        mock_crew_result.raw = '{"analysis": "complete"}'
        mock_crew.kickoff = mocker.MagicMock(return_value=mock_crew_result)
        mock_crew_instance.crew = mocker.MagicMock(return_value=mock_crew)

        mocker.patch(
            "finwiz.crew_factory.EtfCrew",
            return_value=mock_crew_instance,
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_etf_crew({"ticker": "SPY"})

        assert result["etf_analysis_success"] is True


class TestExecutePortfolioRebalancingCrew:
    """Tests for execute_portfolio_rebalancing_crew method."""

    def test_should_return_disabled_when_feature_flag_off(self, mocker, mock_integration_manager, mock_error_handler):
        """Test that rebalancing crew returns disabled when feature flag is off."""
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=False,
        )
        mocker.patch.dict("os.environ", {"CREW_CACHE_ENABLED": "false"})

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_portfolio_rebalancing_crew({})

        assert result == {"portfolio_rebalancing_available": False}

    def test_should_execute_crew_successfully(self, mocker, mock_integration_manager, mock_error_handler):
        """Test successful portfolio rebalancing crew execution."""
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=True,
        )
        mocker.patch.dict("os.environ", {"CREW_CACHE_ENABLED": "false"})

        # Mock PortfolioRebalancingCrew
        mock_crew_instance = mocker.MagicMock()
        mock_crew = mocker.MagicMock()
        mock_crew_result = mocker.MagicMock()
        mock_crew_result.raw = '{"rebalancing": "complete"}'
        mock_crew.kickoff = mocker.MagicMock(return_value=mock_crew_result)
        mock_crew_instance.crew = mocker.MagicMock(return_value=mock_crew)

        mocker.patch(
            "finwiz.crew_factory.PortfolioRebalancingCrew",
            return_value=mock_crew_instance,
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_portfolio_rebalancing_crew({})

        assert result["portfolio_rebalancing_available"] is True

    def test_should_handle_crew_failure(self, mocker, mock_integration_manager, mock_error_handler):
        """Test error handling in portfolio rebalancing crew."""
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=True,
        )
        mocker.patch.dict("os.environ", {"CREW_CACHE_ENABLED": "false"})

        # Mock crew to raise exception
        mocker.patch(
            "finwiz.crew_factory.PortfolioRebalancingCrew",
            side_effect=Exception("Rebalancing failed"),
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_portfolio_rebalancing_crew({})

        assert result["portfolio_rebalancing_available"] is False
        assert "portfolio_rebalancing_error" in result


class TestExecuteInvestmentDiscoveryCrew:
    """Tests for execute_investment_discovery_crew method."""

    def test_should_return_disabled_when_feature_flag_off(self, mocker, mock_integration_manager, mock_error_handler):
        """Test that discovery crew returns disabled when feature flag is off."""
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=False,
        )
        mocker.patch.dict("os.environ", {"CREW_CACHE_ENABLED": "false"})

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_investment_discovery_crew({})

        assert result == {"investment_discovery_available": False}

    def test_should_execute_crew_successfully(self, mocker, mock_integration_manager, mock_error_handler):
        """Test successful investment discovery crew execution."""
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=True,
        )
        mocker.patch.dict("os.environ", {"CREW_CACHE_ENABLED": "false"})

        # Mock InvestmentDiscoveryCrew
        mock_crew_instance = mocker.MagicMock()
        mock_crew = mocker.MagicMock()
        mock_crew_result = mocker.MagicMock()
        mock_crew_result.raw = '{"discovery": "complete"}'
        mock_crew.kickoff = mocker.MagicMock(return_value=mock_crew_result)
        mock_crew_instance.crew = mocker.MagicMock(return_value=mock_crew)

        mocker.patch(
            "finwiz.crew_factory.InvestmentDiscoveryCrew",
            return_value=mock_crew_instance,
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_investment_discovery_crew({})

        assert result["investment_discovery_available"] is True


class TestExecuteReportCrew:
    """Tests for execute_report_crew method."""

    def test_should_execute_crew_successfully(self, mocker, mock_integration_manager, mock_error_handler):
        """Test successful report crew execution."""
        mocker.patch.dict("os.environ", {"CREW_CACHE_ENABLED": "false"})

        # Mock ReportCrew
        # NOTE: The code calls report_crew.context_manager.prepare_crew_context()
        mock_crew_instance = mocker.MagicMock()
        mock_crew = mocker.MagicMock()
        mock_crew.kickoff = mocker.MagicMock()
        mock_crew_instance.crew = mocker.MagicMock(return_value=mock_crew)
        mock_context_manager = mocker.MagicMock()
        mock_context_manager.prepare_crew_context = mocker.MagicMock(return_value={
            "ticker_count": 5,
            "insufficient_tickers": False,
            "portfolio_review": {},
        })
        mock_crew_instance.context_manager = mock_context_manager

        mocker.patch(
            "finwiz.crew_factory.ReportCrew",
            return_value=mock_crew_instance,
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_report_crew({"portfolio_review": {}})

        assert result["report_generation_success"] is True

    def test_should_handle_context_preparation_failure(self, mocker, mock_integration_manager, mock_error_handler):
        """Test error handling when context preparation fails."""
        mocker.patch.dict("os.environ", {"CREW_CACHE_ENABLED": "false"})

        # Mock ReportCrew with failing context preparation
        # NOTE: The code calls report_crew.context_manager.prepare_crew_context()
        mock_crew_instance = mocker.MagicMock()
        mock_context_manager = mocker.MagicMock()
        mock_context_manager.prepare_crew_context = mocker.MagicMock(
            side_effect=Exception("Context preparation failed")
        )
        mock_crew_instance.context_manager = mock_context_manager

        mocker.patch(
            "finwiz.crew_factory.ReportCrew",
            return_value=mock_crew_instance,
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_report_crew({})

        assert result["report_generation_success"] is False
        assert "Context preparation failed" in result["report_generation_error"]

    def test_should_handle_crew_execution_failure(self, mocker, mock_integration_manager, mock_error_handler):
        """Test error handling when crew execution fails."""
        mocker.patch.dict("os.environ", {"CREW_CACHE_ENABLED": "false"})

        # Mock ReportCrew
        # NOTE: The code calls report_crew.context_manager.prepare_crew_context()
        mock_crew_instance = mocker.MagicMock()
        mock_crew = mocker.MagicMock()
        mock_crew.kickoff = mocker.MagicMock(side_effect=Exception("Report generation failed"))
        mock_crew_instance.crew = mocker.MagicMock(return_value=mock_crew)
        mock_context_manager = mocker.MagicMock()
        mock_context_manager.prepare_crew_context = mocker.MagicMock(return_value={"ticker_count": 5})
        mock_crew_instance.context_manager = mock_context_manager

        mocker.patch(
            "finwiz.crew_factory.ReportCrew",
            return_value=mock_crew_instance,
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_report_crew({})

        assert result["report_generation_success"] is False
        assert "report_generation_error" in result


class TestCreateCrewInputsForPortfolioRebalancing:
    """Tests for create_crew_inputs_for_portfolio_rebalancing method."""

    def test_should_create_inputs_with_core_analysis_available(self, crew_factory):
        """Test input creation when core analysis is available."""
        base_inputs = {
            "portfolio_review": {"holdings": []},
            "target_allocations": {"AAPL": 0.3},
            "tolerance_bands": {"equity": 0.05},
            "available_capital": 10000.0,
            "stock_analysis_result": '{"analysis": "stock"}',
            "etf_analysis_result": '{"analysis": "etf"}',
            "crypto_analysis_result": '{"analysis": "crypto"}',
        }
        core_analysis_status = {
            "any_available": True,
            "available_crews": ["stock", "etf", "crypto"],
            "stock_available": True,
            "etf_available": True,
            "crypto_available": True,
        }

        result = crew_factory.create_crew_inputs_for_portfolio_rebalancing(
            base_inputs, core_analysis_status
        )

        assert "full_date" in result
        assert result["portfolio_data"] == {"holdings": []}
        assert result["stock_analysis"] == '{"analysis": "stock"}'
        assert result["etf_analysis"] == '{"analysis": "etf"}'
        assert result["crypto_analysis"] == '{"analysis": "crypto"}'
        assert "degraded_mode" not in result

    def test_should_create_degraded_inputs_when_no_core_analysis(self, crew_factory):
        """Test input creation when no core analysis is available."""
        base_inputs = {
            "portfolio_review": {"holdings": []},
            "target_allocations": {},
            "tolerance_bands": {},
            "available_capital": 5000.0,
        }
        core_analysis_status = {
            "any_available": False,
            "available_crews": [],
            "stock_available": False,
            "etf_available": False,
            "crypto_available": False,
        }

        result = crew_factory.create_crew_inputs_for_portfolio_rebalancing(
            base_inputs, core_analysis_status
        )

        assert result["degraded_mode"] is True
        assert result["available_capital"] == 5000.0


class TestCreateCrewInputsForInvestmentDiscovery:
    """Tests for create_crew_inputs_for_investment_discovery method."""

    def test_should_create_complete_inputs(self, crew_factory, mocker):
        """Test input creation with all data."""
        base_inputs = {
            "portfolio_review": {"holdings": []},
            "portfolio_review_json": "{}",
            "has_existing_session": True,
            "session_id": "test-session",
            "analysis_count": 5,
            "report_language": "en",
            "portfolio_rebalancing_result": "{}",
            "portfolio_rebalancing_available": True,
            "stock_analysis_error": None,
            "etf_analysis_error": None,
            "crypto_analysis_error": None,
        }
        core_analysis_status = {
            "any_available": True,
            "available_crews": ["stock"],
        }
        upstream_data = mocker.MagicMock()
        upstream_data.available_data = {"stock": {}}
        upstream_data.stale_data = []
        upstream_data.missing_data = []

        core_analysis_data = {
            "stock_data": {"ticker": "AAPL"},
        }

        result = crew_factory.create_crew_inputs_for_investment_discovery(
            base_inputs, core_analysis_status, upstream_data, core_analysis_data
        )

        assert "full_date" in result
        assert result["session_id"] == "test-session"
        assert result["core_analysis_available"] is True
        assert "market_context" in result


class TestExtractMarketConditionsFromInputs:
    """Tests for _extract_market_conditions_from_inputs method."""

    def test_should_extract_stock_conditions(self, crew_factory):
        """Test extraction of stock market conditions."""
        inputs = {"stock_analysis_result": '{"data": "stock"}'}

        result = crew_factory._extract_market_conditions_from_inputs(inputs)

        assert "stock_market_sentiment" in result

    def test_should_extract_etf_conditions(self, crew_factory):
        """Test extraction of ETF conditions."""
        inputs = {"etf_analysis_result": '{"data": "etf"}'}

        result = crew_factory._extract_market_conditions_from_inputs(inputs)

        assert "sector_trends" in result

    def test_should_extract_crypto_conditions(self, crew_factory):
        """Test extraction of crypto conditions."""
        inputs = {"crypto_analysis_result": '{"data": "crypto"}'}

        result = crew_factory._extract_market_conditions_from_inputs(inputs)

        assert "crypto_market_dynamics" in result

    def test_should_return_empty_for_no_data(self, crew_factory):
        """Test that empty dict is returned when no data available."""
        inputs = {}

        result = crew_factory._extract_market_conditions_from_inputs(inputs)

        assert result == {}


class TestExtractMarketContextFromCoreAnalysis:
    """Tests for _extract_market_context_from_core_analysis method."""

    def test_should_extract_opportunities(self, crew_factory):
        """Test extraction of opportunities from core analysis."""
        core_data = {
            "stock_analysis": {
                "opportunities": ["AAPL buy opportunity", "MSFT growth potential"],
            },
        }

        result = crew_factory._extract_market_context_from_core_analysis(core_data)

        assert len(result["opportunities"]) == 2
        assert "AAPL buy opportunity" in result["opportunities"]

    def test_should_handle_empty_data(self, crew_factory):
        """Test handling of empty core analysis data."""
        result = crew_factory._extract_market_context_from_core_analysis({})

        assert result["overall_sentiment"] == "neutral"
        assert result["opportunities"] == []

    def test_should_handle_malformed_data(self, crew_factory):
        """Test handling of malformed data."""
        core_data = {
            "stock_analysis": "not a dict",
        }

        # Should not raise exception
        result = crew_factory._extract_market_context_from_core_analysis(core_data)

        assert "overall_sentiment" in result


class TestWrapCachedDataForStorage:
    """Tests for _wrap_cached_data_for_storage method."""

    def test_should_wrap_cached_data_correctly(self, crew_factory):
        """Test that cached data is wrapped with correct structure."""
        cached_data = {
            "ticker": "AAPL",
            "score": 0.85,
            "_cache_metadata": {"cache_age_hours": 2},
        }

        result = crew_factory._wrap_cached_data_for_storage(cached_data, "stock")

        assert "raw_output" in result
        assert "json_dict" in result
        assert result["json_dict"] == cached_data
        assert result["pydantic"] == cached_data
        assert result["tasks_output"] == []
        assert result["metadata"]["crew_name"] == "stock"
        assert result["metadata"]["data_source"] == "cache"
        assert result["metadata"]["data_freshness"]["age_hours"] == 2

    def test_should_handle_missing_cache_metadata(self, crew_factory):
        """Test wrapping when cache metadata is missing."""
        cached_data = {"ticker": "BTC", "analysis": "complete"}

        result = crew_factory._wrap_cached_data_for_storage(cached_data, "crypto")

        assert result["metadata"]["data_freshness"]["age_hours"] == 0


class TestCacheIntegration:
    """Integration tests for caching behavior."""

    def test_should_skip_cache_when_disabled(self, mocker, mock_integration_manager, mock_error_handler):
        """Test that cache is skipped when disabled."""
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=True,
        )
        mocker.patch.dict("os.environ", {
            "CREW_CACHE_ENABLED": "false",
        })

        # Mock successful crew execution
        mock_crew_instance = mocker.MagicMock()
        mock_crew = mocker.MagicMock()
        mock_crew_result = mocker.MagicMock()
        mock_crew_result.raw = '{"analysis": "fresh"}'
        mock_crew.kickoff = mocker.MagicMock(return_value=mock_crew_result)
        mock_crew_instance.crew = mocker.MagicMock(return_value=mock_crew)

        mocker.patch(
            "finwiz.crew_factory.CryptoCrew",
            return_value=mock_crew_instance,
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_crypto_crew({"ticker": "BTC"})

        assert result["crypto_analysis_cached"] is False


class TestFallbackBehavior:
    """Tests for fallback behavior when errors occur."""

    def test_should_use_fallback_data_on_error(self, mocker, mock_integration_manager, mock_error_handler):
        """Test that fallback data is used when crew fails."""
        mock_cache = mocker.MagicMock()
        mock_cache.get_cached_crew_output = mocker.MagicMock(return_value=None)

        mocker.patch(
            "finwiz.crew_factory.get_crew_output_cache",
            return_value=mock_cache,
        )
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=True,
        )
        mocker.patch.dict("os.environ", {
            "CREW_CACHE_ENABLED": "true",
            "CREW_CACHE_MAX_AGE_HOURS": "24",
        })

        # Mock crew to fail
        mocker.patch(
            "finwiz.crew_factory.StockCrew",
            side_effect=Exception("API timeout"),
        )

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_stock_crew({"ticker": "AAPL"})

        assert result["stock_analysis_success"] is False
        assert result["stock_analysis_fallback"] is True
        assert result["stock_fallback_strategy"] == "cached_data"

        # Verify fallback data was stored
        mock_integration_manager.store_crew_output.assert_called()

    def test_should_handle_complete_failure(self, mocker, mock_integration_manager, mock_error_handler):
        """Test handling when both crew and fallback fail."""
        mock_cache = mocker.MagicMock()
        mock_cache.get_cached_crew_output = mocker.MagicMock(return_value=None)

        mocker.patch(
            "finwiz.crew_factory.get_crew_output_cache",
            return_value=mock_cache,
        )
        mocker.patch(
            "finwiz.crew_factory.is_feature_enabled",
            return_value=True,
        )
        mocker.patch.dict("os.environ", {
            "CREW_CACHE_ENABLED": "true",
            "CREW_CACHE_MAX_AGE_HOURS": "24",
        })

        # Mock crew to fail
        mocker.patch(
            "finwiz.crew_factory.EtfCrew",
            side_effect=Exception("Complete failure"),
        )

        # Configure error handler to return failed fallback
        fallback_response = mocker.MagicMock()
        fallback_response.success = False
        fallback_response.data = None
        fallback_response.message = "All fallbacks exhausted"
        fallback_response.fallback_strategy = "none"
        fallback_response.degraded_functionality = ["all"]
        mock_error_handler.handle_crew_failure = mocker.MagicMock(return_value=fallback_response)

        from finwiz.crew_factory import CrewFactory
        factory = CrewFactory(mock_integration_manager, mock_error_handler)

        result = factory.execute_etf_crew({"ticker": "SPY"})

        assert result["etf_analysis_success"] is False
        assert result["etf_analysis_result"] is None
