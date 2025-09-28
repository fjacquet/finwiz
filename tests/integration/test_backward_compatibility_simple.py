"""
Simple backward compatibility tests for core analysis restoration.

This module tests the essential backward compatibility aspects without
complex mocking or external API calls.
"""

import os
from unittest.mock import patch

import pytest

from finwiz.utils.feature_flags import FeatureFlags


class TestSimpleBackwardCompatibility:
    """Simple backward compatibility tests."""

    def test_existing_imports_remain_stable(self):
        """Test that all existing classes can still be imported."""
        try:
            # Core crews should be importable
            from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
            from finwiz.crews.etf_crew.etf_crew import EtfCrew
            from finwiz.crews.investment_discovery_crew.investment_discovery_crew import InvestmentDiscoveryCrew
            from finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew import PortfolioRebalancingCrew
            from finwiz.crews.report_crew.report_crew import ReportCrew
            from finwiz.crews.stock_crew.stock_crew import StockCrew
            from finwiz.integration.data_accessor import CrewDataAccessor

            # Integration system should be importable
            from finwiz.integration.manager import CrewDataIntegrationManager

            # Main flow should be importable
            from finwiz.main import FinwizFlow, FinwizState, kickoff, plot

            # Orchestrators should be importable
            from finwiz.orchestrators.portfolio_review import run as run_portfolio_review

            # Utils should be importable
            from finwiz.utils.feature_flags import FeatureFlags
            from finwiz.utils.session_manager import SessionManager

            # Verify classes can be instantiated (basic check)
            assert StockCrew is not None
            assert EtfCrew is not None
            assert CryptoCrew is not None
            assert ReportCrew is not None
            assert InvestmentDiscoveryCrew is not None
            assert PortfolioRebalancingCrew is not None
            assert CrewDataIntegrationManager is not None
            assert CrewDataAccessor is not None
            assert FeatureFlags is not None
            assert SessionManager is not None
            assert FinwizFlow is not None
            assert FinwizState is not None
            assert callable(kickoff)
            assert callable(plot)
            assert callable(run_portfolio_review)

        except ImportError as e:
            pytest.fail(f"Import failed, breaking backward compatibility: {e}")

    def test_feature_flags_backward_compatibility(self):
        """Test that existing feature flags continue to work."""
        # Test with existing feature flags
        with patch.dict(
            os.environ,
            {
                "FINWIZ_FF_PORTFOLIO_REBALANCING": "true",
                "FINWIZ_FF_INVESTMENT_DISCOVERY": "true",
            },
        ):
            feature_flags = FeatureFlags()

            # Existing feature flags should still work
            assert feature_flags.is_enabled("portfolio_rebalancing") is True
            assert feature_flags.is_enabled("investment_discovery") is True

    def test_new_feature_flags_available(self):
        """Test that new core analysis feature flags are available."""
        with patch.dict(
            os.environ,
            {
                "FINWIZ_FF_STOCK_ANALYSIS": "true",
                "FINWIZ_FF_ETF_ANALYSIS": "true",
                "FINWIZ_FF_CRYPTO_ANALYSIS": "true",
            },
        ):
            feature_flags = FeatureFlags()

            # New feature flags should be available
            assert feature_flags.is_enabled("stock_analysis") is True
            assert feature_flags.is_enabled("etf_analysis") is True
            assert feature_flags.is_enabled("crypto_analysis") is True

    def test_feature_flags_can_disable_core_analysis(self):
        """Test that core analysis can be disabled via feature flags."""
        with patch.dict(
            os.environ,
            {
                "FINWIZ_FF_STOCK_ANALYSIS": "false",
                "FINWIZ_FF_ETF_ANALYSIS": "false",
                "FINWIZ_FF_CRYPTO_ANALYSIS": "false",
            },
        ):
            feature_flags = FeatureFlags()

            # Core analysis should be disabled
            assert feature_flags.is_enabled("stock_analysis") is False
            assert feature_flags.is_enabled("etf_analysis") is False
            assert feature_flags.is_enabled("crypto_analysis") is False

    def test_flow_state_structure_unchanged(self):
        """Test that FinwizState structure remains unchanged."""
        from finwiz.main import FinwizState

        # Create state instance
        state = FinwizState()

        # Verify existing attributes are still present
        assert hasattr(state, "etf_result")
        assert hasattr(state, "crypto_result")
        assert hasattr(state, "stock_result")

        # Verify default values
        assert state.etf_result == ""
        assert state.crypto_result == ""
        assert state.stock_result == ""

    def test_flow_initialization_backward_compatible(self):
        """Test that FinwizFlow can be initialized without breaking changes."""
        from finwiz.main import FinwizFlow, FinwizState

        # Mock environment variables to avoid configuration errors
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "SERPER_API_KEY": "test-key",
                "FIRECRAWL_API_KEY": "test-key",
                "ALPHA_VANTAGE_API_KEY": "test-key",
            },
        ):
            # Should be able to create flow instance
            state = FinwizState()
            flow = FinwizFlow(state=state)

            # Verify flow has expected attributes
            assert hasattr(flow, "inputs")
            assert hasattr(flow, "integration_manager")
            assert hasattr(flow, "data_accessor")
            assert hasattr(flow, "error_handler")

            # Verify inputs structure contains expected fields
            assert "current_day" in flow.inputs
            assert "current_month" in flow.inputs
            assert "current_year" in flow.inputs
            assert "current_date" in flow.inputs
            assert "full_date" in flow.inputs
            assert "timestamp" in flow.inputs
            assert "report_language" in flow.inputs

    def test_configuration_manager_backward_compatible(self):
        """Test that configuration manager maintains backward compatibility."""
        from finwiz.utils.configuration_manager import get_configuration_manager

        # Mock environment variables
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "SERPER_API_KEY": "test-key",
                "FIRECRAWL_API_KEY": "test-key",
                "ALPHA_VANTAGE_API_KEY": "test-key",
            },
        ):
            # Should be able to get configuration manager
            config_manager = get_configuration_manager()

            # Verify expected methods exist
            assert hasattr(config_manager, "validate_startup_configuration")
            assert hasattr(config_manager, "get_configuration_summary")
            assert hasattr(config_manager, "feature_flags")

            # Verify configuration summary structure
            config_summary = config_manager.get_configuration_summary()
            assert "api_keys_configured" in config_summary
            assert "available_services" in config_summary
            assert isinstance(config_summary["available_services"], list)

    def test_session_manager_backward_compatible(self):
        """Test that session manager maintains backward compatibility."""
        from finwiz.utils.session_manager import SessionManager

        # Should be able to create session manager
        session_manager = SessionManager()

        # Verify expected methods exist
        assert hasattr(session_manager, "load_existing_session")
        assert hasattr(session_manager, "create_new_session")
        assert hasattr(session_manager, "validate_session_integrity")
        assert hasattr(session_manager, "recover_corrupted_session")

    def test_integration_system_backward_compatible(self):
        """Test that integration system maintains backward compatibility."""
        from finwiz.integration.data_accessor import CrewDataAccessor
        from finwiz.integration.manager import CrewDataIntegrationManager

        # Should be able to create integration components
        integration_manager = CrewDataIntegrationManager()
        data_accessor = CrewDataAccessor(integration_manager)

        # Verify expected methods exist on integration manager
        assert hasattr(integration_manager, "store_crew_output")
        assert hasattr(integration_manager, "get_crew_data_with_freshness_check")
        assert hasattr(integration_manager, "get_upstream_data")
        assert hasattr(integration_manager, "get_refresh_recommendations")

        # Verify expected methods exist on data accessor
        assert hasattr(data_accessor, "check_data_availability")
        assert hasattr(data_accessor, "get_stale_data_warnings")
        assert hasattr(data_accessor, "get_aplus_opportunities")
        assert hasattr(data_accessor, "get_consolidated_reporter_input")

    def test_crew_classes_maintain_structure(self):
        """Test that crew classes maintain their expected structure."""
        from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
        from finwiz.crews.etf_crew.etf_crew import EtfCrew
        from finwiz.crews.investment_discovery_crew.investment_discovery_crew import InvestmentDiscoveryCrew
        from finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew import PortfolioRebalancingCrew
        from finwiz.crews.report_crew.report_crew import ReportCrew
        from finwiz.crews.stock_crew.stock_crew import StockCrew

        # Verify crews can be instantiated
        crews = [StockCrew(), EtfCrew(), CryptoCrew(), ReportCrew(), InvestmentDiscoveryCrew(), PortfolioRebalancingCrew()]

        # Verify all crews have expected crew() method
        for crew in crews:
            assert hasattr(crew, "crew")
            assert callable(crew.crew)

    def test_environment_variables_compatibility(self):
        """Test that environment variable handling remains compatible."""
        # Test portfolio review environment variable
        with patch.dict(os.environ, {"PORTFOLIO_REVIEW_ENABLED": "true"}):
            assert os.getenv("PORTFOLIO_REVIEW_ENABLED") == "true"

        with patch.dict(os.environ, {"PORTFOLIO_REVIEW_ENABLED": "false"}):
            assert os.getenv("PORTFOLIO_REVIEW_ENABLED") == "false"

        # Test that missing environment variables are handled gracefully
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise exceptions when environment variables are missing
            portfolio_enabled = (os.getenv("PORTFOLIO_REVIEW_ENABLED") or "true").strip().lower() in {"1", "true", "yes", "on"}
            assert portfolio_enabled is True  # Default behavior

    def test_quantitative_tools_remain_importable(self):
        """Test that quantitative analysis tools remain importable."""
        try:
            from finwiz.tools.backtesting_tool import BacktestingTool
            from finwiz.tools.portfolio_analysis_tool import PortfolioAnalysisTool
            from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

            # Verify tools can be instantiated
            quant_tool = QuantitativeAnalysisTool()
            backtest_tool = BacktestingTool()
            portfolio_tool = PortfolioAnalysisTool()

            # Verify tools have expected methods
            assert hasattr(quant_tool, "_run")
            assert hasattr(backtest_tool, "_run")
            assert hasattr(portfolio_tool, "_run")

        except ImportError as e:
            pytest.fail(f"Quantitative tool import failed: {e}")

    def test_error_handling_classes_available(self):
        """Test that error handling classes are available."""
        try:
            from finwiz.utils.core_analysis_error_handler import CoreAnalysisErrorHandler
            from finwiz.utils.graceful_degradation import GracefulDegradationManager

            # Verify classes can be imported
            assert CoreAnalysisErrorHandler is not None
            assert GracefulDegradationManager is not None

        except ImportError as e:
            pytest.fail(f"Error handling class import failed: {e}")

    def test_data_freshness_components_available(self):
        """Test that data freshness validation components are available."""
        try:
            from finwiz.utils.data_freshness_validator import DataFreshnessValidator
            from finwiz.utils.freshness_validated_tool import FreshnessValidatedTool

            # Verify classes can be imported
            assert DataFreshnessValidator is not None
            assert FreshnessValidatedTool is not None

        except ImportError as e:
            pytest.fail(f"Data freshness component import failed: {e}")
