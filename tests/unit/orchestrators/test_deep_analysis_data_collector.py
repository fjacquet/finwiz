"""Tests for DeepAnalysisDataCollector ETF branch and expense_ratio fallback."""

import pytest

from finwiz.orchestrators.deep_analysis_data_collector import DeepAnalysisDataCollector


class TestCollectAssetSpecificDataETF:
    """Tests for the ETF branch in _collect_asset_specific_data."""

    @pytest.fixture
    def collector(self, mocker):
        return DeepAnalysisDataCollector(state=mocker.MagicMock())

    def test_etf_branch_routes_correctly(self, collector, mocker):
        """asset_class='etf' should invoke _collect_etf_data."""
        mock_etf = mocker.patch.object(collector, "_collect_etf_data", return_value={"expense_ratio": 0.001})
        collector._collect_asset_specific_data("VUSA.L", "etf", {})
        mock_etf.assert_called_once_with("VUSA.L", {})

    def test_etf_branch_case_insensitive(self, collector, mocker):
        """Should handle 'ETF' uppercase."""
        mock_etf = mocker.patch.object(collector, "_collect_etf_data", return_value={})
        collector._collect_asset_specific_data("VUSA.L", "ETF", {})
        mock_etf.assert_called_once()


class TestCollectEtfData:
    """Tests for _collect_etf_data method."""

    @pytest.fixture
    def collector(self, mocker):
        return DeepAnalysisDataCollector(state=mocker.MagicMock())

    def test_should_extract_expense_ratio_from_ticker_info(self, collector):
        """Should get expense_ratio from yfinance ticker_info when available."""
        collected = {"ticker_info": {"expense_ratio": 0.0007}}
        result = collector._collect_etf_data("VUSA.L", collected)
        assert result["expense_ratio"] == 0.0007

    def test_should_fallback_to_yaml_for_european_etfs(self, collector, mocker):
        """Should use YAML fallback when yfinance lacks expense_ratio."""
        mocker.patch(
            "finwiz.quantitative.etf.etf_expense_fallback.get_fallback_expense_ratio",
            return_value=0.001,
        )
        collected = {"ticker_info": {}}
        result = collector._collect_etf_data("ZSIL.SW", collected)
        assert result["expense_ratio"] == 0.001

    def test_should_prefer_yfinance_over_fallback(self, collector, mocker):
        """yfinance expense_ratio should take precedence over YAML fallback."""
        mocker.patch(
            "finwiz.quantitative.etf.etf_expense_fallback.get_fallback_expense_ratio",
            return_value=0.999,
        )
        collected = {"ticker_info": {"expense_ratio": 0.0007}}
        result = collector._collect_etf_data("VUSA.L", collected)
        assert result["expense_ratio"] == 0.0007

    def test_should_handle_missing_expense_ratio_gracefully(self, collector, mocker):
        """Should not set expense_ratio when neither source has data."""
        mocker.patch(
            "finwiz.quantitative.etf.etf_expense_fallback.get_fallback_expense_ratio",
            return_value=None,
        )
        collected = {"ticker_info": {}}
        result = collector._collect_etf_data("UNKNOWN", collected)
        assert "expense_ratio" not in result

    def test_should_skip_na_string_from_ticker_info(self, collector, mocker):
        """Should ignore 'N/A' string values from yfinance."""
        mocker.patch(
            "finwiz.quantitative.etf.etf_expense_fallback.get_fallback_expense_ratio",
            return_value=0.002,
        )
        collected = {"ticker_info": {"expense_ratio": "N/A"}}
        result = collector._collect_etf_data("XB0T.DE", collected)
        assert result["expense_ratio"] == 0.002


class TestFlattenBetaHandling:
    """Tests for beta handling in flatten_collected_data."""

    @pytest.fixture
    def collector(self, mocker):
        return DeepAnalysisDataCollector(state=mocker.MagicMock())

    def test_should_use_calculated_beta_1_0_when_yfinance_absent(self, collector):
        """Calculated beta=1.0 should be accepted, not skipped."""
        data = {
            "ticker": "GOOGL",
            "ticker_info": {},
            "quantitative_analysis": {
                "performance_metrics": {"beta": 1.0, "volatility": 0.25},
            },
        }
        result = collector.flatten_collected_data(data)
        assert result["beta"] == 1.0

    def test_should_prefer_yfinance_beta_over_calculated(self, collector):
        """yfinance beta takes priority over calculated beta."""
        data = {
            "ticker": "AAPL",
            "ticker_info": {"beta": 1.23},
            "quantitative_analysis": {
                "performance_metrics": {"beta": 1.0},
            },
        }
        result = collector.flatten_collected_data(data)
        assert result["beta"] == 1.23
