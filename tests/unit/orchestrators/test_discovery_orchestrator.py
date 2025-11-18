"""
Unit tests for DiscoveryOrchestrator.

Tests cover:
- Crypto discovery execution
- Stock discovery execution
- ETF discovery execution
- Discovery result consolidation
- Error handling for failed discoveries
"""

import pytest

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.discovery_orchestrator import DiscoveryOrchestrator


class TestDiscoveryOrchestrator:
    """Test suite for DiscoveryOrchestrator."""

    @pytest.fixture
    def state(self):
        """Create a FinwizState instance for testing."""
        state = FinwizState()
        state.session_id = "test_session"
        return state

    @pytest.fixture
    def orchestrator(self, state, mocker):
        """Create a DiscoveryOrchestrator instance with mocked dependencies."""
        availability_tracker = mocker.Mock()
        return DiscoveryOrchestrator(
            state,
            availability_tracker=availability_tracker,
        )

    def test_should_execute_crypto_discovery_successfully(self, orchestrator, mocker):
        """Test successful crypto discovery execution."""
        # Arrange
        mock_analyze = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze.return_value = {
            "analysis_summary": "Crypto analysis completed",
            "opportunities": [{"ticker": "BTC", "grade": "A+"}],
            "performance_metrics": {"sharpe_ratio": 1.5},
        }

        # Act
        result = orchestrator.check_crypto()

        # Assert
        assert result["crypto_analysis_complete"] is True
        assert "Crypto analysis completed" in result["crypto_result"]
        assert orchestrator.state.crypto_analysis_success is True
        assert len(orchestrator.state.crypto_opportunities) == 1
        assert orchestrator.state.crypto_opportunities[0]["ticker"] == "BTC"
        mock_analyze.assert_called_once_with("test_session")
        orchestrator.availability_tracker.track_data_source.assert_called_once()

    def test_should_handle_crypto_discovery_failure(self, orchestrator, mocker):
        """Test crypto discovery error handling."""
        # Arrange
        mock_analyze = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze.side_effect = Exception("Crypto analysis failed")

        # Act
        result = orchestrator.check_crypto()

        # Assert
        assert result["crypto_analysis_complete"] is True
        assert "Crypto analysis failed" in result["crypto_result"]
        assert orchestrator.state.crypto_analysis_success is False
        assert orchestrator.state.crypto_analysis_error == "Crypto analysis failed"
        orchestrator.availability_tracker.track_data_source.assert_called_once()

    def test_should_execute_stock_discovery_successfully(self, orchestrator, mocker):
        """Test successful stock discovery execution."""
        # Arrange
        mock_analyze = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
        mock_analyze.return_value = {
            "analysis_summary": "Stock analysis completed",
            "opportunities": [{"ticker": "AAPL", "grade": "A+"}, {"ticker": "GOOGL", "grade": "A"}],
            "performance_metrics": {"sharpe_ratio": 1.8},
        }

        # Act
        result = orchestrator.check_stock()

        # Assert
        assert result["stock_analysis_complete"] is True
        assert "Stock analysis completed" in result["stock_result"]
        assert orchestrator.state.stock_analysis_success is True
        assert len(orchestrator.state.stock_opportunities) == 2
        assert orchestrator.state.stock_opportunities[0]["ticker"] == "AAPL"
        mock_analyze.assert_called_once_with("test_session")
        orchestrator.availability_tracker.track_data_source.assert_called_once()

    def test_should_handle_stock_discovery_failure(self, orchestrator, mocker):
        """Test stock discovery error handling."""
        # Arrange
        mock_analyze = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
        mock_analyze.side_effect = Exception("Stock analysis failed")

        # Act
        result = orchestrator.check_stock()

        # Assert
        assert result["stock_analysis_complete"] is True
        assert "Stock analysis failed" in result["stock_result"]
        assert orchestrator.state.stock_analysis_success is False
        assert orchestrator.state.stock_analysis_error == "Stock analysis failed"
        orchestrator.availability_tracker.track_data_source.assert_called_once()

    def test_should_execute_etf_discovery_successfully(self, orchestrator, mocker):
        """Test successful ETF discovery execution."""
        # Arrange
        mock_analyze = mocker.patch("finwiz.scoring.etf_analyzer.analyze_etf_opportunities")
        mock_analyze.return_value = {
            "analysis_summary": "ETF analysis completed",
            "opportunities": [{"ticker": "SPY", "grade": "A+"}],
            "performance_metrics": {"sharpe_ratio": 1.2},
        }

        # Act
        result = orchestrator.check_etf()

        # Assert
        assert result["etf_analysis_complete"] is True
        assert "ETF analysis completed" in result["etf_result"]
        assert orchestrator.state.etf_analysis_success is True
        assert len(orchestrator.state.etf_opportunities) == 1
        assert orchestrator.state.etf_opportunities[0]["ticker"] == "SPY"
        mock_analyze.assert_called_once_with("test_session")
        orchestrator.availability_tracker.track_data_source.assert_called_once()

    def test_should_handle_etf_discovery_failure(self, orchestrator, mocker):
        """Test ETF discovery error handling."""
        # Arrange
        mock_analyze = mocker.patch("finwiz.scoring.etf_analyzer.analyze_etf_opportunities")
        mock_analyze.side_effect = Exception("ETF analysis failed")

        # Act
        result = orchestrator.check_etf()

        # Assert
        assert result["etf_analysis_complete"] is True
        assert "ETF analysis failed" in result["etf_result"]
        assert orchestrator.state.etf_analysis_success is False
        assert orchestrator.state.etf_analysis_error == "ETF analysis failed"
        orchestrator.availability_tracker.track_data_source.assert_called_once()

    def test_should_consolidate_discovery_results_successfully(self, orchestrator):
        """Test successful discovery result consolidation."""
        # Arrange
        orchestrator.state.crypto_opportunities = [{"ticker": "BTC", "grade": "A+"}]
        orchestrator.state.stock_opportunities = [{"ticker": "AAPL", "grade": "A+"}, {"ticker": "GOOGL", "grade": "A"}]
        orchestrator.state.etf_opportunities = [{"ticker": "SPY", "grade": "A+"}]

        # Act
        result = orchestrator.check_investment_discovery()

        # Assert
        assert result["investment_discovery_complete"] is True
        assert result["discovery_available"] is True
        assert result["total_opportunities"] == 4
        assert orchestrator.state.investment_discovery_available is True
        assert len(orchestrator.state.all_discovery_opportunities) == 4

    def test_should_handle_empty_discovery_results(self, orchestrator):
        """Test consolidation with no opportunities found."""
        # Arrange
        orchestrator.state.crypto_opportunities = []
        orchestrator.state.stock_opportunities = []
        orchestrator.state.etf_opportunities = []

        # Act
        result = orchestrator.check_investment_discovery()

        # Assert
        assert result["investment_discovery_complete"] is True
        assert result["discovery_available"] is False
        assert result["total_opportunities"] == 0
        assert orchestrator.state.investment_discovery_available is False
        assert len(orchestrator.state.all_discovery_opportunities) == 0

    def test_should_handle_partial_discovery_results(self, orchestrator):
        """Test consolidation with only some asset classes having opportunities."""
        # Arrange
        orchestrator.state.crypto_opportunities = None  # Not set
        orchestrator.state.stock_opportunities = [{"ticker": "AAPL", "grade": "A+"}]
        orchestrator.state.etf_opportunities = []  # Empty

        # Act
        result = orchestrator.check_investment_discovery()

        # Assert
        assert result["investment_discovery_complete"] is True
        assert result["discovery_available"] is True
        assert result["total_opportunities"] == 1
        assert orchestrator.state.investment_discovery_available is True
        assert len(orchestrator.state.all_discovery_opportunities) == 1

    def test_should_work_without_availability_tracker(self, state, mocker):
        """Test that orchestrator works when availability_tracker is None."""
        # Arrange
        orchestrator = DiscoveryOrchestrator(state, availability_tracker=None)

        mock_analyze = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_analyze.return_value = {
            "analysis_summary": "Crypto analysis completed",
            "opportunities": [{"ticker": "BTC", "grade": "A+"}],
            "performance_metrics": {},
        }

        # Act
        result = orchestrator.check_crypto()

        # Assert
        assert result["crypto_analysis_complete"] is True
        assert orchestrator.state.crypto_analysis_success is True

    def test_property_discovery_error_handling_graceful_degradation(self, state, mocker):
        """
        Property 17: Discovery Error Handling.

        For any discovery crew failure, the DiscoveryOrchestrator should handle the error
        gracefully and continue with other crews. This test validates the property using
        pytest-mock (unit test.mock is BANNED).
        """
        # Arrange
        state.session_id = "test_session"
        availability_tracker = mocker.Mock()
        orchestrator = DiscoveryOrchestrator(state, availability_tracker=availability_tracker)

        # Mock the analyzer functions - crypto fails, stock succeeds, etf fails
        mock_crypto = mocker.patch("finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities")
        mock_stock = mocker.patch("finwiz.scoring.stock_analyzer.analyze_stock_opportunities")
        mock_etf = mocker.patch("finwiz.scoring.etf_analyzer.analyze_etf_opportunities")

        mock_crypto.side_effect = Exception("Crypto analysis failed")
        mock_stock.return_value = {
            "analysis_summary": "Stock completed",
            "opportunities": [{"ticker": "AAPL", "grade": "A+"}],
            "performance_metrics": {},
        }
        mock_etf.side_effect = Exception("ETF analysis failed")

        # Act - Execute all discovery methods
        crypto_result = orchestrator.check_crypto()
        stock_result = orchestrator.check_stock()
        etf_result = orchestrator.check_etf()

        # Assert - All methods should complete (not raise exceptions)
        assert crypto_result["crypto_analysis_complete"] is True
        assert stock_result["stock_analysis_complete"] is True
        assert etf_result["etf_analysis_complete"] is True

        # Verify error handling - crypto failed
        assert state.crypto_analysis_success is False
        assert "Crypto analysis failed" in state.crypto_analysis_error

        # Verify success - stock succeeded
        assert state.stock_analysis_success is True

        # Verify error handling - etf failed
        assert state.etf_analysis_success is False
        assert "ETF analysis failed" in state.etf_analysis_error

        # Verify availability tracker was called for each discovery
        assert availability_tracker.track_data_source.call_count == 3
