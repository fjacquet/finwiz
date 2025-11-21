"""Test that DeepAnalysisOrchestrator stores crew outputs correctly."""

import pytest
from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator
from finwiz.flow_state import FinwizState, DeepAnalysisResult


class TestDeepAnalysisCrewOutputStorage:
    """Test crew output storage in DeepAnalysisOrchestrator."""

    @pytest.fixture
    def mock_state(self):
        """Create mock FinwizState."""
        state = FinwizState()
        state.current_day = "18"
        state.current_month = "November"
        state.current_year = "2025"
        state.current_date = "2025-11-18"
        state.full_date = "November 18, 2025"
        state.timestamp = "2025-11-18T19:26:19"
        state.report_language = "en"
        state.session_id = "test_session"
        return state

    @pytest.fixture
    def mock_integration_manager(self, mocker):
        """Create mock integration manager."""
        mock = mocker.Mock()
        mock.store_crew_output = mocker.Mock(return_value=True)
        return mock

    @pytest.fixture
    def mock_crew_factory(self, mocker):
        """Create mock crew factory."""
        return mocker.Mock()

    @pytest.fixture
    def mock_cache_manager(self, mocker):
        """Create mock cache manager."""
        mock = mocker.Mock()
        mock.get_cached_analysis = mocker.Mock(return_value=None)
        mock.cache_analysis = mocker.Mock()
        mock.log_cache_stats = mocker.Mock()
        return mock

    @pytest.fixture
    def orchestrator(self, mock_state, mock_integration_manager, mock_crew_factory, mocker):
        """Create DeepAnalysisOrchestrator instance."""
        return DeepAnalysisOrchestrator(
            state=mock_state,
            integration_manager=mock_integration_manager,
            crew_factory=mock_crew_factory,
            batch_prefetch_config=mocker.Mock(enabled=False, min_holdings_for_batch=10),
            cache_service=None,
            cache_enabled=False,
            error_handler=None,
        )

    def test_should_store_crew_output_after_execution(
        self, orchestrator, mock_integration_manager, mock_cache_manager, mocker
    ):
        """Test that crew output is stored to disk after execution."""
        # Arrange
        ticker = "AAPL"
        asset_class = "stock"

        # Mock DeepAnalysisCrew
        mock_crew_instance = mocker.Mock()
        mock_crew_result = mocker.Mock()
        mock_pydantic = mocker.Mock()
        mock_pydantic.model_dump = mocker.Mock(return_value={
            "grade": "A+",
            "composite_score": 0.95,
            "fundamental_score": 0.90,
            "technical_score": 0.85,
            "risk_score": 0.80,
        })
        # Set attributes directly for getattr() calls
        mock_pydantic.fundamental_score = 0.90
        mock_pydantic.technical_score = 0.85
        mock_pydantic.risk_score = 0.80
        mock_crew_result.pydantic = mock_pydantic
        mock_crew_instance.crew().kickoff = mocker.Mock(return_value=mock_crew_result)

        mock_deep_analysis_crew = mocker.patch(
            "finwiz.crews.deep_analysis.deep_analysis.DeepAnalysisCrew",
            return_value=mock_crew_instance
        )

        # Mock cache manager
        mocker.patch(
            "finwiz.cache.analysis_cache_manager.get_analysis_cache_manager",
            return_value=mock_cache_manager
        )

        # Act
        result = orchestrator._process_single_holding(
            ticker=ticker,
            asset_class=asset_class,
            cache_mgr=mock_cache_manager,
            cache_ttl=24,
            batch_enabled=False
        )

        # Assert
        assert result is not None
        assert result.ticker == ticker
        assert result.asset_class == asset_class

        # Verify store_crew_output was called
        mock_integration_manager.store_crew_output.assert_called_once()
        call_args = mock_integration_manager.store_crew_output.call_args

        # Check crew name format
        assert call_args[0][0] == f"deep_analysis_{asset_class}"
        # Check DeepAnalysisResult object was passed (Python-first architecture)
        stored_result = call_args[0][1]
        assert isinstance(stored_result, DeepAnalysisResult)
        assert stored_result.ticker == ticker
        assert stored_result.asset_class == asset_class

    def test_should_store_crew_output_for_different_asset_classes(
        self, orchestrator, mock_integration_manager, mock_cache_manager, mocker
    ):
        """Test that crew outputs are stored with correct names for different asset classes."""
        # Arrange
        test_cases = [
            ("AAPL", "stock", "deep_analysis_stock"),
            ("SPY", "etf", "deep_analysis_etf"),
            ("BTC", "crypto", "deep_analysis_crypto"),
        ]
        
        # Mock DeepAnalysisCrew
        mock_crew_instance = mocker.Mock()
        mock_crew_result = mocker.Mock()
        mock_pydantic = mocker.Mock()
        mock_pydantic.model_dump = mocker.Mock(return_value={
            "grade": "A",
            "composite_score": 0.85,
            "fundamental_score": 0.80,
            "technical_score": 0.75,
            "risk_score": 0.70,
        })
        # Set attributes directly for getattr() calls
        mock_pydantic.fundamental_score = 0.80
        mock_pydantic.technical_score = 0.75
        mock_pydantic.risk_score = 0.70
        mock_crew_result.pydantic = mock_pydantic
        mock_crew_instance.crew().kickoff = mocker.Mock(return_value=mock_crew_result)
        
        mocker.patch(
            "finwiz.crews.deep_analysis.deep_analysis.DeepAnalysisCrew",
            return_value=mock_crew_instance
        )
        
        mocker.patch(
            "finwiz.cache.analysis_cache_manager.get_analysis_cache_manager",
            return_value=mock_cache_manager
        )
        
        # Act & Assert
        for ticker, asset_class, expected_crew_name in test_cases:
            mock_integration_manager.store_crew_output.reset_mock()
            
            result = orchestrator._process_single_holding(
                ticker=ticker,
                asset_class=asset_class,
                cache_mgr=mock_cache_manager,
                cache_ttl=24,
                batch_enabled=False
            )
            
            assert result is not None
            mock_integration_manager.store_crew_output.assert_called_once()
            call_args = mock_integration_manager.store_crew_output.call_args
            assert call_args[0][0] == expected_crew_name

    def test_should_handle_storage_failure_gracefully(
        self, orchestrator, mock_integration_manager, mock_cache_manager, mocker
    ):
        """Test that storage failures don't break the analysis flow."""
        # Arrange
        ticker = "AAPL"
        asset_class = "stock"

        # Mock store_crew_output to raise exception
        mock_integration_manager.store_crew_output.side_effect = Exception("Storage failed")

        # Mock DeepAnalysisCrew
        mock_crew_instance = mocker.Mock()
        mock_crew_result = mocker.Mock()
        mock_pydantic = mocker.Mock()
        mock_pydantic.model_dump = mocker.Mock(return_value={
            "grade": "B",
            "composite_score": 0.75,
            "fundamental_score": 0.70,
            "technical_score": 0.65,
            "risk_score": 0.60,
        })
        # Set attributes directly for getattr() calls
        mock_pydantic.fundamental_score = 0.70
        mock_pydantic.technical_score = 0.65
        mock_pydantic.risk_score = 0.60
        mock_crew_result.pydantic = mock_pydantic
        mock_crew_instance.crew().kickoff = mocker.Mock(return_value=mock_crew_result)

        mocker.patch(
            "finwiz.crews.deep_analysis.deep_analysis.DeepAnalysisCrew",
            return_value=mock_crew_instance
        )

        mocker.patch(
            "finwiz.cache.analysis_cache_manager.get_analysis_cache_manager",
            return_value=mock_cache_manager
        )

        # Act - should not raise exception
        result = orchestrator._process_single_holding(
            ticker=ticker,
            asset_class=asset_class,
            cache_mgr=mock_cache_manager,
            cache_ttl=24,
            batch_enabled=False
        )

        # Assert - analysis should still complete despite storage failure
        assert result is not None
        assert result.ticker == ticker
        # Grade may vary based on Python scorer calculation - just check it's valid
        assert result.grade in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]

        # Verify storage was attempted (and failed gracefully)
        mock_integration_manager.store_crew_output.assert_called_once()

    def test_should_not_store_cached_results(
        self, orchestrator, mock_integration_manager, mock_cache_manager, mocker
    ):
        """Test that cached results are not stored again."""
        # Arrange
        ticker = "AAPL"
        asset_class = "stock"
        
        # Create a mock crew output that looks like a cached result
        mock_crew_output = mocker.Mock()
        mock_crew_output.pydantic = mocker.Mock()
        mock_crew_output.pydantic.model_dump = mocker.Mock(return_value={
            "grade": "A",
            "composite_score": 0.85,
            "fundamental_score": 0.80,
            "technical_score": 0.75,
            "risk_score": 0.70,
        })
        mock_crew_output.pydantic.grade = "A"
        mock_crew_output.pydantic.composite_score = 0.85
        mock_crew_output.pydantic.fundamental_score = 0.80
        mock_crew_output.pydantic.technical_score = 0.75
        mock_crew_output.pydantic.risk_score = 0.70
        
        # Mock cached result
        cached_result = DeepAnalysisResult(
            ticker=ticker,
            asset_class=asset_class,
            crew_name="DeepAnalysisCrew",
            analysis_timestamp="2025-11-18T19:00:00",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Cached analysis",
            risk_details={},
            fundamental_score=0.80,
            technical_score=0.75,
            risk_score=0.70,
            data_freshness_hours=1.0,
            confidence_level=0.9,
            warnings=[],
            cached=True,
        )
        
        mock_cached_analysis = mocker.Mock()
        mock_cached_analysis.is_fresh = mocker.Mock(return_value=True)
        mock_cached_analysis.analysis = mock_crew_output
        mock_cached_analysis.analysis.crew_name = "DeepAnalysisCrew"
        
        mock_cache_manager.get_cached_analysis = mocker.Mock(return_value=mock_cached_analysis)
        
        # Act
        result = orchestrator._process_single_holding(
            ticker=ticker,
            asset_class=asset_class,
            cache_mgr=mock_cache_manager,
            cache_ttl=24,
            batch_enabled=False
        )
        
        # Assert
        assert result is not None
        assert result.cached is True
        
        # Verify store_crew_output was NOT called for cached results
        mock_integration_manager.store_crew_output.assert_not_called()
