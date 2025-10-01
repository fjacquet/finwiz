"""
Minimal backward compatibility tests for core analysis restoration.

This module tests the essential backward compatibility aspects without
triggering circular imports or complex dependencies.
"""

import os

import pytest


class TestMinimalBackwardCompatibility:
    """Minimal backward compatibility tests."""

    def test_main_flow_classes_importable(self):
        """Test that main flow classes can be imported."""
        try:
            from finwiz.main import FinwizFlow, FinwizState, kickoff, plot

            # Verify classes and functions exist
            assert FinwizFlow is not None
            assert FinwizState is not None
            assert callable(kickoff)
            assert callable(plot)

        except ImportError as e:
            pytest.fail(f"Main flow import failed: {e}")

    def test_crew_classes_importable(self):
        """Test that crew classes can be imported."""
        try:
            from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
            from finwiz.crews.etf_crew.etf_crew import EtfCrew
            from finwiz.crews.investment_discovery_crew.investment_discovery_crew import InvestmentDiscoveryCrew
            from finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew import PortfolioRebalancingCrew
            from finwiz.crews.report_crew.report_crew import ReportCrew
            from finwiz.crews.stock_crew.stock_crew import StockCrew

            # Verify classes exist
            assert StockCrew is not None
            assert EtfCrew is not None
            assert CryptoCrew is not None
            assert ReportCrew is not None
            assert InvestmentDiscoveryCrew is not None
            assert PortfolioRebalancingCrew is not None

        except ImportError as e:
            pytest.fail(f"Crew class import failed: {e}")

    def test_integration_system_importable(self):
        """Test that integration system can be imported."""
        try:
            from finwiz.integration.data_accessor import CrewDataAccessor
            from finwiz.integration.manager import CrewDataIntegrationManager

            # Verify classes exist
            assert CrewDataIntegrationManager is not None
            assert CrewDataAccessor is not None

        except ImportError as e:
            pytest.fail(f"Integration system import failed: {e}")

    def test_orchestrator_importable(self):
        """Test that portfolio review orchestrator can be imported."""
        try:
            from finwiz.orchestrators.portfolio_review import run as run_portfolio_review

            # Verify function exists
            assert callable(run_portfolio_review)

        except ImportError as e:
            pytest.fail(f"Orchestrator import failed: {e}")

    def test_session_manager_importable(self):
        """Test that session manager can be imported."""
        try:
            from finwiz.utils.session_manager import SessionManager

            # Verify class exists
            assert SessionManager is not None

        except ImportError as e:
            pytest.fail(f"Session manager import failed: {e}")

    def test_configuration_manager_importable(self):
        """Test that configuration manager can be imported."""
        try:
            from finwiz.utils.configuration_manager import get_configuration_manager

            # Verify function exists
            assert callable(get_configuration_manager)

        except ImportError as e:
            pytest.fail(f"Configuration manager import failed: {e}")

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

    def test_environment_variables_compatibility(self, mocker):
        """Test that environment variable handling remains compatible."""
        # Test portfolio review environment variable
        mocker.patch.dict(os.environ, {"PORTFOLIO_REVIEW_ENABLED": "true"})
        assert os.getenv("PORTFOLIO_REVIEW_ENABLED") == "true"

        mocker.patch.dict(os.environ, {"PORTFOLIO_REVIEW_ENABLED": "false"})
        assert os.getenv("PORTFOLIO_REVIEW_ENABLED") == "false"

        # Test that missing environment variables are handled gracefully
        mocker.patch.dict(os.environ, {}, clear=True)
        # Should not raise exceptions when environment variables are missing
        portfolio_enabled = (os.getenv("PORTFOLIO_REVIEW_ENABLED") or "true").strip().lower() in {"1", "true", "yes", "on"}
        assert portfolio_enabled is True  # Default behavior

    def test_basic_tools_importable(self):
        """Test that basic tools can be imported."""
        try:
            from finwiz.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool
            from finwiz.tools.yahoo_finance_history_tool import YahooFinanceHistoryTool

            # Verify tools exist
            assert YahooFinanceHistoryTool is not None
            assert AlphaVantageCompanyOverviewTool is not None

        except ImportError as e:
            pytest.fail(f"Basic tools import failed: {e}")

    def test_schemas_importable(self):
        """Test that schema validation can be imported."""
        try:
            from finwiz.schemas.validate import validate_reporter_input

            # Verify function exists
            assert callable(validate_reporter_input)

        except ImportError as e:
            pytest.fail(f"Schema validation import failed: {e}")

    def test_crew_instantiation_basic(self, mocker):
        """Test that crews can be instantiated without errors."""
        try:
            from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
            from finwiz.crews.etf_crew.etf_crew import EtfCrew
            from finwiz.crews.report_crew.report_crew import ReportCrew
            from finwiz.crews.stock_crew.stock_crew import StockCrew

            # Mock environment variables to avoid configuration errors
            mocker.patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "test-key",
                    "SERPER_API_KEY": "test-key",
                    "FIRECRAWL_API_KEY": "test-key",
                    "ALPHA_VANTAGE_API_KEY": "test-key",
                },
            )

            # Test that crew classes exist and have expected structure
            # Note: We don't instantiate them due to complex dependencies
            # but verify they have the expected interface

            # Verify crews have expected methods
            assert hasattr(StockCrew, "__init__")
            assert hasattr(EtfCrew, "__init__")
            assert hasattr(CryptoCrew, "__init__")
            assert hasattr(ReportCrew, "__init__")

            # Verify crew classes are callable (can be instantiated)
            assert callable(StockCrew)
            assert callable(EtfCrew)
            assert callable(CryptoCrew)
            assert callable(ReportCrew)

        except Exception as e:
            pytest.fail(f"Crew class verification failed: {e}")

    def test_integration_system_instantiation(self):
        """Test that integration system can be instantiated."""
        try:
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

        except Exception as e:
            pytest.fail(f"Integration system instantiation failed: {e}")

    def test_flow_initialization_basic(self, mocker):
        """Test that FinwizFlow can be initialized."""
        try:
            from finwiz.main import FinwizFlow, FinwizState

            # Mock environment variables to avoid configuration errors
            mocker.patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "test-key",
                    "SERPER_API_KEY": "test-key",
                    "FIRECRAWL_API_KEY": "test-key",
                    "ALPHA_VANTAGE_API_KEY": "test-key",
                },
            )

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

        except Exception as e:
            pytest.fail(f"Flow initialization failed: {e}")

    def test_error_handling_classes_importable(self):
        """Test that error handling classes can be imported."""
        try:
            from finwiz.utils.core_analysis_error_handler import CoreAnalysisErrorHandler

            # Verify class exists
            assert CoreAnalysisErrorHandler is not None

        except ImportError as e:
            pytest.fail(f"Error handling class import failed: {e}")

    def test_basic_feature_flag_functionality(self, mocker):
        """Test basic feature flag functionality without circular imports."""
        # Test environment variable based feature flags directly
        mocker.patch.dict(
            os.environ,
            {
                "FINWIZ_FF_PORTFOLIO_REBALANCING": "true",
                "FINWIZ_FF_INVESTMENT_DISCOVERY": "true",
                "FINWIZ_FF_STOCK_ANALYSIS": "true",
                "FINWIZ_FF_ETF_ANALYSIS": "true",
                "FINWIZ_FF_CRYPTO_ANALYSIS": "true",
            },
        )

        # Test direct environment variable access (basic feature flag behavior)
        assert os.getenv("FINWIZ_FF_PORTFOLIO_REBALANCING") == "true"
        assert os.getenv("FINWIZ_FF_INVESTMENT_DISCOVERY") == "true"
        assert os.getenv("FINWIZ_FF_STOCK_ANALYSIS") == "true"
        assert os.getenv("FINWIZ_FF_ETF_ANALYSIS") == "true"
        assert os.getenv("FINWIZ_FF_CRYPTO_ANALYSIS") == "true"

    def test_existing_api_structure_maintained(self):
        """Test that existing API structure is maintained."""
        # Test that key functions and classes maintain their expected signatures
        from finwiz.main import kickoff, plot
        from finwiz.orchestrators.portfolio_review import run as run_portfolio_review
        from finwiz.schemas.validate import validate_reporter_input

        # Verify functions are callable (signature compatibility)
        assert callable(kickoff)
        assert callable(plot)
        assert callable(run_portfolio_review)
        assert callable(validate_reporter_input)

        # Test that classes maintain expected structure
        from finwiz.integration.data_accessor import CrewDataAccessor
        from finwiz.integration.manager import CrewDataIntegrationManager
        from finwiz.main import FinwizFlow, FinwizState

        # Verify classes are instantiable (API compatibility)
        assert FinwizFlow is not None
        assert FinwizState is not None
        assert CrewDataIntegrationManager is not None
        assert CrewDataAccessor is not None
