"""Tests for flow_state.py module."""

import pytest

from finwiz.flow_state import (
    DeepAnalysisResult,
    FinwizState,
    FlowStateManager,
)


class TestFlowStateModuleExports:
    """Tests for module exports and imports."""

    def test_should_export_deep_analysis_result(self):
        """Test that DeepAnalysisResult is exported."""
        assert DeepAnalysisResult is not None

    def test_should_export_finwiz_state(self):
        """Test that FinwizState is exported."""
        assert FinwizState is not None

    def test_should_export_flow_state_manager(self):
        """Test that FlowStateManager is exported."""
        assert FlowStateManager is not None


class TestFlowStateManagerInit:
    """Tests for FlowStateManager initialization."""

    def test_should_initialize_successfully(self):
        """Test successful initialization."""
        manager = FlowStateManager()
        assert manager is not None
        assert manager.logger is not None

    def test_should_have_logger(self):
        """Test that logger is properly configured."""
        manager = FlowStateManager()
        assert hasattr(manager, "logger")


class TestCreateInitialState:
    """Tests for create_initial_state method."""

    def test_should_create_initial_state_without_session(self, mocker):
        """Test creating initial state without existing session."""
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_HAS_EXISTING_SESSION": "false",
                "FINWIZ_SESSION_ID": "",
                "FINWIZ_ANALYSIS_COUNT": "0",
            },
        )

        manager = FlowStateManager()
        state = manager.create_initial_state()

        assert isinstance(state, FinwizState)
        assert state.has_existing_session is False
        assert state.session_id == ""
        assert state.analysis_count == 0

    def test_should_create_initial_state_with_session(self, mocker):
        """Test creating initial state with existing session."""
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_HAS_EXISTING_SESSION": "true",
                "FINWIZ_SESSION_ID": "test-session-123",
                "FINWIZ_ANALYSIS_COUNT": "5",
            },
        )

        manager = FlowStateManager()
        state = manager.create_initial_state()

        assert state.has_existing_session is True
        assert state.session_id == "test-session-123"
        assert state.analysis_count == 5

    def test_should_have_timestamp(self, mocker):
        """Test that state includes timestamp."""
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_HAS_EXISTING_SESSION": "false",
                "FINWIZ_SESSION_ID": "",
                "FINWIZ_ANALYSIS_COUNT": "0",
            },
        )

        manager = FlowStateManager()
        state = manager.create_initial_state()

        assert state.timestamp is not None
        assert len(state.timestamp) > 0

    def test_should_handle_missing_env_vars(self, mocker):
        """Test handling of missing environment variables."""
        mocker.patch.dict("os.environ", {}, clear=True)

        manager = FlowStateManager()
        state = manager.create_initial_state()

        # Should use defaults when env vars are missing
        assert state.has_existing_session is False
        assert state.session_id == ""
        assert state.analysis_count == 0


class TestCheckCoreAnalysisAvailability:
    """Tests for check_core_analysis_availability method."""

    def test_should_delegate_to_utility_function(self, mocker):
        """Test that method delegates to utility function."""
        mock_check = mocker.patch(
            "finwiz.flow_state.check_core_analysis_availability",
            return_value={
                "any_available": True,
                "stock_available": True,
                "etf_available": False,
                "crypto_available": False,
                "available_crews": ["stock"],
                "failed_crews": [],
                "disabled_crews": [],
                "total_available": 1,
                "total_failed": 0,
                "total_disabled": 0,
            },
        )

        manager = FlowStateManager()
        state = FinwizState()
        result = manager.check_core_analysis_availability(state)

        mock_check.assert_called_once_with(state, manager.logger)
        assert result["any_available"] is True
        assert result["stock_available"] is True

    def test_should_return_availability_dict(self, mocker):
        """Test that result contains expected keys."""
        mock_check = mocker.patch(
            "finwiz.flow_state.check_core_analysis_availability",
            return_value={
                "any_available": False,
                "stock_available": False,
                "etf_available": False,
                "crypto_available": False,
                "available_crews": [],
                "failed_crews": ["stock", "etf", "crypto"],
                "disabled_crews": [],
                "total_available": 0,
                "total_failed": 3,
                "total_disabled": 0,
            },
        )

        manager = FlowStateManager()
        state = FinwizState()
        result = manager.check_core_analysis_availability(state)

        assert "any_available" in result
        assert "stock_available" in result
        assert "etf_available" in result
        assert "crypto_available" in result
        assert "available_crews" in result
        assert "failed_crews" in result


class TestExtractMarketConditions:
    """Tests for extract_market_conditions method."""

    def test_should_delegate_to_utility_function(self, mocker):
        """Test that method delegates to utility function."""
        mock_extract = mocker.patch(
            "finwiz.flow_state.extract_market_conditions",
            return_value={"stock_market_sentiment": "bullish"},
        )

        manager = FlowStateManager()
        state = FinwizState()
        result = manager.extract_market_conditions(state)

        mock_extract.assert_called_once_with(state)
        assert "stock_market_sentiment" in result

    def test_should_return_empty_dict_when_no_results(self, mocker):
        """Test empty conditions when no analysis results."""
        mock_extract = mocker.patch(
            "finwiz.flow_state.extract_market_conditions",
            return_value={},
        )

        manager = FlowStateManager()
        state = FinwizState()
        result = manager.extract_market_conditions(state)

        assert result == {}


class TestExtractMarketContextFromCoreAnalysis:
    """Tests for extract_market_context_from_core_analysis method."""

    def test_should_delegate_to_utility_function(self, mocker):
        """Test that method delegates to utility function."""
        mock_extract = mocker.patch(
            "finwiz.flow_state.extract_market_context_from_core_analysis",
            return_value={
                "overall_sentiment": "positive",
                "market_trends": ["tech sector bullish"],
                "risk_factors": [],
                "opportunities": [],
                "sector_analysis": {},
            },
        )

        manager = FlowStateManager()
        core_data = {"stock_analysis": {"market_sentiments": []}}
        result = manager.extract_market_context_from_core_analysis(core_data)

        mock_extract.assert_called_once_with(core_data, manager.logger)
        assert result["overall_sentiment"] == "positive"

    def test_should_return_default_context_on_empty_data(self, mocker):
        """Test default context is returned for empty data."""
        mock_extract = mocker.patch(
            "finwiz.flow_state.extract_market_context_from_core_analysis",
            return_value={
                "overall_sentiment": "neutral",
                "market_trends": [],
                "risk_factors": [],
                "opportunities": [],
                "sector_analysis": {},
            },
        )

        manager = FlowStateManager()
        result = manager.extract_market_context_from_core_analysis({})

        assert result["overall_sentiment"] == "neutral"
        assert result["market_trends"] == []


class TestPrepareCoreAnalysisSummary:
    """Tests for prepare_core_analysis_summary method."""

    def test_should_delegate_to_utility_function(self, mocker):
        """Test that method delegates to utility function."""
        mock_prepare = mocker.patch(
            "finwiz.flow_state.prepare_core_analysis_summary",
            return_value={
                "stocks_analyzed": 5,
                "etfs_analyzed": 3,
                "crypto_analyzed": 2,
                "total_analyzed": 10,
            },
        )

        manager = FlowStateManager()
        consolidated_data = {"stock_results": [], "etf_results": []}
        result = manager.prepare_core_analysis_summary(consolidated_data)

        mock_prepare.assert_called_once_with(consolidated_data, manager.logger)
        assert result["total_analyzed"] == 10

    def test_should_handle_empty_consolidated_data(self, mocker):
        """Test handling of empty consolidated data."""
        mock_prepare = mocker.patch(
            "finwiz.flow_state.prepare_core_analysis_summary",
            return_value={
                "stocks_analyzed": 0,
                "etfs_analyzed": 0,
                "crypto_analyzed": 0,
                "total_analyzed": 0,
            },
        )

        manager = FlowStateManager()
        result = manager.prepare_core_analysis_summary({})

        assert result["total_analyzed"] == 0


class TestGetDegradedFunctionalitySummary:
    """Tests for get_degraded_functionality_summary method."""

    def test_should_delegate_to_utility_function(self, mocker):
        """Test that method delegates to utility function."""
        mock_get = mocker.patch(
            "finwiz.flow_state.get_degraded_functionality_summary",
            return_value={
                "has_degraded_functionality": True,
                "degraded_crews": ["stock"],
                "fallback_strategies_used": ["stock: cached_data"],
                "missing_features": ["real_time_quotes"],
                "data_quality_issues": [],
            },
        )

        manager = FlowStateManager()
        state = FinwizState()
        result = manager.get_degraded_functionality_summary(state)

        mock_get.assert_called_once_with(state)
        assert result["has_degraded_functionality"] is True

    def test_should_return_clean_summary_when_no_degradation(self, mocker):
        """Test clean summary when no degradation."""
        mock_get = mocker.patch(
            "finwiz.flow_state.get_degraded_functionality_summary",
            return_value={
                "has_degraded_functionality": False,
                "degraded_crews": [],
                "fallback_strategies_used": [],
                "missing_features": [],
                "data_quality_issues": [],
            },
        )

        manager = FlowStateManager()
        state = FinwizState()
        result = manager.get_degraded_functionality_summary(state)

        assert result["has_degraded_functionality"] is False
        assert result["degraded_crews"] == []


class TestDeepAnalysisResultModel:
    """Tests for DeepAnalysisResult model."""

    def test_should_create_valid_result(self):
        """Test creating a valid DeepAnalysisResult."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Strong fundamentals",
            data_freshness_hours=2.5,
            confidence_level=0.9,
        )

        assert result.ticker == "AAPL"
        assert result.composite_score == 0.85
        assert result.grade == "A"

    def test_should_validate_composite_score_range(self):
        """Test that composite_score must be 0.0-1.0."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=1.5,  # Invalid
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=1.0,
                confidence_level=0.9,
            )

    def test_should_have_quality_level_property(self):
        """Test quality_level property."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.9,
            data_quality={"quality_level": "high"},
        )

        assert result.quality_level == "high"

    def test_should_return_unknown_quality_level_when_missing(self):
        """Test quality_level returns 'unknown' when not set."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.9,
        )

        assert result.quality_level == "unknown"

    def test_should_have_completeness_score_property(self):
        """Test completeness_score property."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.9,
            data_quality={"completeness_score": 0.95},
        )

        assert result.completeness_score == 0.95

    def test_should_return_default_completeness_when_missing(self):
        """Test completeness_score returns 0.5 when not set."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.9,
        )

        assert result.completeness_score == 0.5


class TestFinwizStateModel:
    """Tests for FinwizState model."""

    def test_should_create_default_state(self):
        """Test creating a default FinwizState."""
        state = FinwizState()

        assert state.id is not None
        assert state.has_existing_session is False
        assert state.analysis_count == 0

    def test_should_have_date_fields(self):
        """Test that state has date fields."""
        state = FinwizState()

        assert state.current_day is not None
        assert state.current_month is not None
        assert state.current_year is not None
        assert state.current_date is not None
        assert state.timestamp is not None

    def test_should_allow_extra_fields(self):
        """Test that extra fields are allowed (model_config)."""
        state = FinwizState(custom_field="test")
        assert state.model_extra.get("custom_field") == "test"

    def test_should_track_deep_analysis_results(self):
        """Test deep analysis results tracking."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.9,
        )

        state = FinwizState(deep_analysis_results={"AAPL": result})

        assert "AAPL" in state.deep_analysis_results
        assert state.deep_analysis_results["AAPL"].grade == "A"

    def test_should_track_errors(self):
        """Test error tracking fields."""
        state = FinwizState(
            errors=["Error 1", "Error 2"],
            failed_holdings=["FAIL1", "FAIL2"],
        )

        assert len(state.errors) == 2
        assert len(state.failed_holdings) == 2

    def test_should_track_progress(self):
        """Test progress tracking fields."""
        state = FinwizState(
            total_holdings=10,
            holdings_processed=5,
            holdings_remaining=5,
            progress_percentage=50.0,
        )

        assert state.total_holdings == 10
        assert state.progress_percentage == 50.0


class TestIntegration:
    """Integration tests for flow_state module."""

    def test_should_create_manager_and_state(self, mocker):
        """Test complete workflow of creating manager and state."""
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_HAS_EXISTING_SESSION": "false",
                "FINWIZ_SESSION_ID": "",
                "FINWIZ_ANALYSIS_COUNT": "0",
            },
        )

        manager = FlowStateManager()
        state = manager.create_initial_state()

        assert manager is not None
        assert state is not None
        assert isinstance(state, FinwizState)

    def test_state_can_store_deep_analysis(self, mocker):
        """Test that state can store deep analysis results."""
        mocker.patch.dict(
            "os.environ",
            {
                "FINWIZ_HAS_EXISTING_SESSION": "false",
                "FINWIZ_SESSION_ID": "",
                "FINWIZ_ANALYSIS_COUNT": "0",
            },
        )

        manager = FlowStateManager()
        state = manager.create_initial_state()

        # Add deep analysis result
        result = DeepAnalysisResult(
            ticker="MSFT",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.78,
            grade="B+",
            recommendation="HOLD",
            rationale="Stable performer",
            data_freshness_hours=1.5,
            confidence_level=0.85,
        )

        state.deep_analysis_results["MSFT"] = result
        state.deep_analysis_success = True
        state.deep_analysis_count = 1

        assert state.deep_analysis_success is True
        assert state.deep_analysis_count == 1
        assert "MSFT" in state.deep_analysis_results
