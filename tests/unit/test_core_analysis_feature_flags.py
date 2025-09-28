"""
Unit tests for Core Analysis Feature Flags.

Tests feature flag functionality for controlling core analysis crews
including stock, ETF, and crypto analysis.
"""

from unittest.mock import MagicMock, patch

import pytest

from finwiz.main import FinwizFlow


class TestCoreAnalysisFeatureFlags:
    """Test cases for Core Analysis Feature Flags."""

    @pytest.fixture
    def finwiz_flow(self):
        """Create a FinwizFlow instance for feature flag testing."""
        return FinwizFlow()

    def test_should_execute_stock_crew_when_flag_enabled(self, finwiz_flow):
        """Test that stock crew executes when feature flag is enabled."""
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            mock_feature_enabled.return_value = True

            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                mock_stock_crew = MagicMock()
                mock_result = MagicMock()
                mock_result.raw = "Stock analysis executed"
                mock_stock_crew.crew().kickoff.return_value = mock_result
                mock_stock_crew_class.return_value = mock_stock_crew

                # Execute stock analysis
                finwiz_flow.check_stock()

                # Verify feature flag was checked
                mock_feature_enabled.assert_called_with("stock_analysis")

                # Verify crew was executed
                mock_stock_crew_class.assert_called_once()
                mock_stock_crew.crew().kickoff.assert_called_once()

                # Verify results were stored
                assert "stock_analysis_result" in finwiz_flow.inputs
                assert finwiz_flow.inputs["stock_analysis_success"] is True

    def test_should_skip_stock_crew_when_flag_disabled(self, finwiz_flow):
        """Test that stock crew is skipped when feature flag is disabled."""
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            mock_feature_enabled.return_value = False

            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Execute stock analysis
                finwiz_flow.check_stock()

                # Verify feature flag was checked
                mock_feature_enabled.assert_called_with("stock_analysis")

                # Verify crew was not executed
                mock_stock_crew_class.assert_not_called()

                # Verify disabled flag was set
                assert finwiz_flow.inputs.get("stock_analysis_disabled") is True
                assert "stock_analysis_result" not in finwiz_flow.inputs

    def test_should_execute_etf_crew_when_flag_enabled(self, finwiz_flow):
        """Test that ETF crew executes when feature flag is enabled."""
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            mock_feature_enabled.return_value = True

            with patch("finwiz.main.EtfCrew") as mock_etf_crew_class:
                mock_etf_crew = MagicMock()
                mock_result = MagicMock()
                mock_result.raw = "ETF analysis executed"
                mock_etf_crew.crew().kickoff.return_value = mock_result
                mock_etf_crew_class.return_value = mock_etf_crew

                # Execute ETF analysis
                finwiz_flow.check_etf()

                # Verify feature flag was checked
                mock_feature_enabled.assert_called_with("etf_analysis")

                # Verify crew was executed
                mock_etf_crew_class.assert_called_once()
                mock_etf_crew.crew().kickoff.assert_called_once()

                # Verify results were stored
                assert "etf_analysis_result" in finwiz_flow.inputs
                assert finwiz_flow.inputs["etf_analysis_success"] is True

    def test_should_skip_etf_crew_when_flag_disabled(self, finwiz_flow):
        """Test that ETF crew is skipped when feature flag is disabled."""
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            mock_feature_enabled.return_value = False

            with patch("finwiz.main.EtfCrew") as mock_etf_crew_class:
                # Execute ETF analysis
                finwiz_flow.check_etf()

                # Verify feature flag was checked
                mock_feature_enabled.assert_called_with("etf_analysis")

                # Verify crew was not executed
                mock_etf_crew_class.assert_not_called()

                # Verify disabled flag was set
                assert finwiz_flow.inputs.get("etf_analysis_disabled") is True
                assert "etf_analysis_result" not in finwiz_flow.inputs

    def test_should_execute_crypto_crew_when_flag_enabled(self, finwiz_flow):
        """Test that crypto crew executes when feature flag is enabled."""
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            mock_feature_enabled.return_value = True

            with patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class:
                mock_crypto_crew = MagicMock()
                mock_result = MagicMock()
                mock_result.raw = "Crypto analysis executed"
                mock_crypto_crew.crew().kickoff.return_value = mock_result
                mock_crypto_crew_class.return_value = mock_crypto_crew

                # Execute crypto analysis
                finwiz_flow.check_crypto()

                # Verify feature flag was checked
                mock_feature_enabled.assert_called_with("crypto_analysis")

                # Verify crew was executed
                mock_crypto_crew_class.assert_called_once()
                mock_crypto_crew.crew().kickoff.assert_called_once()

                # Verify results were stored
                assert "crypto_analysis_result" in finwiz_flow.inputs
                assert finwiz_flow.inputs["crypto_analysis_success"] is True

    def test_should_skip_crypto_crew_when_flag_disabled(self, finwiz_flow):
        """Test that crypto crew is skipped when feature flag is disabled."""
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            mock_feature_enabled.return_value = False

            with patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class:
                # Execute crypto analysis
                finwiz_flow.check_crypto()

                # Verify feature flag was checked
                mock_feature_enabled.assert_called_with("crypto_analysis")

                # Verify crew was not executed
                mock_crypto_crew_class.assert_not_called()

                # Verify disabled flag was set
                assert finwiz_flow.inputs.get("crypto_analysis_disabled") is True
                assert "crypto_analysis_result" not in finwiz_flow.inputs

    def test_should_handle_mixed_feature_flag_states(self, finwiz_flow):
        """Test handling of mixed feature flag states (some enabled, some disabled)."""

        def mock_feature_enabled_side_effect(feature_name):
            """Mock feature flags with mixed states."""
            feature_states = {
                "stock_analysis": True,
                "etf_analysis": False,
                "crypto_analysis": True,
            }
            return feature_states.get(feature_name, False)

        with patch("finwiz.main.is_feature_enabled", side_effect=mock_feature_enabled_side_effect):
            with (
                patch("finwiz.main.StockCrew") as mock_stock_crew_class,
                patch("finwiz.main.EtfCrew") as mock_etf_crew_class,
                patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class,
            ):
                # Mock enabled crews
                mock_stock_crew = MagicMock()
                mock_stock_result = MagicMock()
                mock_stock_result.raw = "Stock analysis executed"
                mock_stock_crew.crew().kickoff.return_value = mock_stock_result
                mock_stock_crew_class.return_value = mock_stock_crew

                mock_crypto_crew = MagicMock()
                mock_crypto_result = MagicMock()
                mock_crypto_result.raw = "Crypto analysis executed"
                mock_crypto_crew.crew().kickoff.return_value = mock_crypto_result
                mock_crypto_crew_class.return_value = mock_crypto_crew

                # Execute all crews
                finwiz_flow.check_stock()
                finwiz_flow.check_etf()
                finwiz_flow.check_crypto()

                # Verify enabled crews were executed
                mock_stock_crew_class.assert_called_once()
                mock_crypto_crew_class.assert_called_once()
                assert "stock_analysis_result" in finwiz_flow.inputs
                assert "crypto_analysis_result" in finwiz_flow.inputs

                # Verify disabled crew was skipped
                mock_etf_crew_class.assert_not_called()
                assert finwiz_flow.inputs.get("etf_analysis_disabled") is True
                assert "etf_analysis_result" not in finwiz_flow.inputs

    def test_should_handle_all_crews_disabled(self, finwiz_flow):
        """Test handling when all core analysis crews are disabled."""
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            mock_feature_enabled.return_value = False

            with (
                patch("finwiz.main.StockCrew") as mock_stock_crew_class,
                patch("finwiz.main.EtfCrew") as mock_etf_crew_class,
                patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class,
            ):
                # Execute all crews
                finwiz_flow.check_stock()
                finwiz_flow.check_etf()
                finwiz_flow.check_crypto()

                # Verify no crews were executed
                mock_stock_crew_class.assert_not_called()
                mock_etf_crew_class.assert_not_called()
                mock_crypto_crew_class.assert_not_called()

                # Verify all disabled flags were set
                assert finwiz_flow.inputs.get("stock_analysis_disabled") is True
                assert finwiz_flow.inputs.get("etf_analysis_disabled") is True
                assert finwiz_flow.inputs.get("crypto_analysis_disabled") is True

                # Verify no analysis results were created
                assert "stock_analysis_result" not in finwiz_flow.inputs
                assert "etf_analysis_result" not in finwiz_flow.inputs
                assert "crypto_analysis_result" not in finwiz_flow.inputs

    def test_should_handle_all_crews_enabled(self, finwiz_flow):
        """Test handling when all core analysis crews are enabled."""
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            mock_feature_enabled.return_value = True

            with (
                patch("finwiz.main.StockCrew") as mock_stock_crew_class,
                patch("finwiz.main.EtfCrew") as mock_etf_crew_class,
                patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class,
            ):
                # Mock all crews
                mock_crews = {}
                for crew_name, mock_crew_class in [
                    ("stock", mock_stock_crew_class),
                    ("etf", mock_etf_crew_class),
                    ("crypto", mock_crypto_crew_class),
                ]:
                    mock_crew = MagicMock()
                    mock_result = MagicMock()
                    mock_result.raw = f"{crew_name.title()} analysis executed"
                    mock_crew.crew().kickoff.return_value = mock_result
                    mock_crew_class.return_value = mock_crew
                    mock_crews[crew_name] = mock_crew

                # Execute all crews
                finwiz_flow.check_stock()
                finwiz_flow.check_etf()
                finwiz_flow.check_crypto()

                # Verify all crews were executed
                mock_stock_crew_class.assert_called_once()
                mock_etf_crew_class.assert_called_once()
                mock_crypto_crew_class.assert_called_once()

                # Verify all analysis results were created
                assert "stock_analysis_result" in finwiz_flow.inputs
                assert "etf_analysis_result" in finwiz_flow.inputs
                assert "crypto_analysis_result" in finwiz_flow.inputs

                # Verify success flags
                assert finwiz_flow.inputs["stock_analysis_success"] is True
                assert finwiz_flow.inputs["etf_analysis_success"] is True
                assert finwiz_flow.inputs["crypto_analysis_success"] is True

    def test_should_handle_feature_flag_check_failures(self, finwiz_flow):
        """Test handling when feature flag checks themselves fail."""
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            # Mock feature flag check failure
            mock_feature_enabled.side_effect = Exception("Feature flag system failed")

            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Execute should handle feature flag failure gracefully
                finwiz_flow.check_stock()

                # Verify crew was not executed due to feature flag failure
                mock_stock_crew_class.assert_not_called()

    def test_should_respect_feature_flags_during_errors(self, finwiz_flow):
        """Test that feature flags are respected even when crews fail."""
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            mock_feature_enabled.return_value = True

            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Mock crew that fails
                mock_stock_crew = MagicMock()
                mock_stock_crew.crew().kickoff.side_effect = Exception("Crew failed")
                mock_stock_crew_class.return_value = mock_stock_crew

                # Execute should still check feature flag
                finwiz_flow.check_stock()

                # Verify feature flag was checked
                mock_feature_enabled.assert_called_with("stock_analysis")

                # Verify crew was attempted (and failed)
                mock_stock_crew_class.assert_called_once()
                assert finwiz_flow.inputs["stock_analysis_success"] is False

        # Test with feature flag disabled
        with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
            mock_feature_enabled.return_value = False

            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Execute should skip crew entirely
                finwiz_flow.check_stock()

                # Verify feature flag was checked
                mock_feature_enabled.assert_called_with("stock_analysis")

                # Verify crew was not attempted
                mock_stock_crew_class.assert_not_called()
                assert finwiz_flow.inputs.get("stock_analysis_disabled") is True

    def test_should_handle_dynamic_feature_flag_changes(self, finwiz_flow):
        """Test handling of dynamic feature flag changes during execution."""
        call_count = 0

        def dynamic_feature_enabled(feature_name):
            """Mock dynamic feature flag that changes state."""
            nonlocal call_count
            call_count += 1
            # First call returns True, subsequent calls return False
            return call_count == 1

        with patch("finwiz.main.is_feature_enabled", side_effect=dynamic_feature_enabled):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                mock_stock_crew = MagicMock()
                mock_result = MagicMock()
                mock_result.raw = "Stock analysis executed"
                mock_stock_crew.crew().kickoff.return_value = mock_result
                mock_stock_crew_class.return_value = mock_stock_crew

                # First execution should succeed
                finwiz_flow.check_stock()
                assert "stock_analysis_result" in finwiz_flow.inputs

                # Reset for second execution
                if "stock_analysis_result" in finwiz_flow.inputs:
                    del finwiz_flow.inputs["stock_analysis_result"]
                if "stock_analysis_disabled" in finwiz_flow.inputs:
                    del finwiz_flow.inputs["stock_analysis_disabled"]

                # Second execution should be skipped
                finwiz_flow.check_stock()
                assert finwiz_flow.inputs.get("stock_analysis_disabled") is True

    def test_should_provide_feature_flag_status_information(self, finwiz_flow):
        """Test that feature flag status information is available."""
        feature_states = {
            "stock_analysis": True,
            "etf_analysis": False,
            "crypto_analysis": True,
        }

        def mock_feature_enabled_side_effect(feature_name):
            return feature_states.get(feature_name, False)

        with patch("finwiz.main.is_feature_enabled", side_effect=mock_feature_enabled_side_effect):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class, patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class:
                # Mock enabled crews
                for mock_crew_class in [mock_stock_crew_class, mock_crypto_crew_class]:
                    mock_crew = MagicMock()
                    mock_result = MagicMock()
                    mock_result.raw = "Analysis executed"
                    mock_crew.crew().kickoff.return_value = mock_result
                    mock_crew_class.return_value = mock_crew

                # Execute all crews
                finwiz_flow.check_stock()
                finwiz_flow.check_etf()
                finwiz_flow.check_crypto()

                # Verify feature flag status is reflected in inputs
                # Enabled crews should have results
                assert "stock_analysis_result" in finwiz_flow.inputs
                assert "crypto_analysis_result" in finwiz_flow.inputs

                # Disabled crew should have disabled flag
                assert finwiz_flow.inputs.get("etf_analysis_disabled") is True

    def test_should_handle_feature_flag_environment_variables(self, finwiz_flow):
        """Test that feature flags work with environment variables."""
        with patch.dict(
            "os.environ",
            {
                "FINWIZ_FF_STOCK_ANALYSIS": "true",
                "FINWIZ_FF_ETF_ANALYSIS": "false",
                "FINWIZ_FF_CRYPTO_ANALYSIS": "true",
            },
        ):
            # This test assumes the feature flag system reads from environment variables
            # The actual implementation may vary

            with patch("finwiz.main.is_feature_enabled") as mock_feature_enabled:
                # Mock feature flag system that reads from environment
                def env_feature_enabled(feature_name):
                    env_map = {
                        "stock_analysis": "FINWIZ_FF_STOCK_ANALYSIS",
                        "etf_analysis": "FINWIZ_FF_ETF_ANALYSIS",
                        "crypto_analysis": "FINWIZ_FF_CRYPTO_ANALYSIS",
                    }
                    import os

                    return os.getenv(env_map.get(feature_name, ""), "false").lower() == "true"

                mock_feature_enabled.side_effect = env_feature_enabled

                with (
                    patch("finwiz.main.StockCrew") as mock_stock_crew_class,
                    patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class,
                ):
                    # Mock enabled crews
                    for mock_crew_class in [mock_stock_crew_class, mock_crypto_crew_class]:
                        mock_crew = MagicMock()
                        mock_result = MagicMock()
                        mock_result.raw = "Analysis executed"
                        mock_crew.crew().kickoff.return_value = mock_result
                        mock_crew_class.return_value = mock_crew

                    # Execute crews
                    finwiz_flow.check_stock()
                    finwiz_flow.check_etf()
                    finwiz_flow.check_crypto()

                    # Verify environment-based feature flags work
                    assert "stock_analysis_result" in finwiz_flow.inputs
                    assert finwiz_flow.inputs.get("etf_analysis_disabled") is True
                    assert "crypto_analysis_result" in finwiz_flow.inputs
