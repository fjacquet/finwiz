"""End-to-end integration test for complete orchestrator flow."""

from datetime import datetime

import pytest
from finwiz.data.adapters.base_adapter import FundamentalData
from pytest import approx

from finwiz.flows.hybrid_analysis_flow import HybridAnalysisFlow


class TestEndToEndIntegration:
    """Test complete end-to-end integration with real portfolio data."""

    @pytest.mark.asyncio
    async def test_should_process_stock_with_data_orchestrator(self, mocker):
        """Test complete flow for stock analysis using DataSourceOrchestrator."""
        # Arrange
        flow = HybridAnalysisFlow()

        # Mock the data orchestrator to return fundamental data
        mock_adapter = mocker.AsyncMock()
        mock_adapter.source_name = "YFinance"
        mock_adapter.is_available.return_value = True
        mock_adapter.get_fundamental_data = mocker.AsyncMock(
            return_value=FundamentalData(
                ticker="AAPL",
                source="YFinance",
                timestamp=datetime.now(),
                confidence=1.0,
                return_on_equity=0.25,
                debt_to_equity=0.5,
                revenue_growth=0.15,
                profit_margin=0.20,
            )
        )

        flow.data_orchestrator.adapters = [mock_adapter]

        # Set up flow state
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Apple Inc."

        # Act - collect data
        result = flow.collect_data()

        # Assert - verify data collection
        assert result["ticker"] == "AAPL"
        assert result["asset_class"] == "stock"
        assert "raw_data" in result
        assert result["raw_data"]["ticker"] == "AAPL"

        # Verify DataSourceOrchestrator was used
        assert "roe" in result["raw_data"]
        assert result["raw_data"]["roe"] == approx(0.25)
        assert "debt_to_equity" in result["raw_data"]
        assert result["raw_data"]["debt_to_equity"] == approx(0.5)

        # Verify data lineage tracking
        assert "data_lineage" in result["raw_data"]
        assert "data_confidence" in result["raw_data"]
        assert result["raw_data"]["data_confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_should_process_etf_with_enhanced_tool(self, mocker):
        """Test complete flow for ETF analysis."""
        # Arrange
        flow = HybridAnalysisFlow()

        # Mock ETF tool
        mock_etf_tool = mocker.Mock()
        mock_etf_tool._run.return_value = {
            "etf_data": {
                "expense_ratio": 0.003,
                "aum": 500e9,  # $500B
                "tracking_error": 0.005,
                "dividend_yield": 0.015,
            }
        }

        mocker.patch("finwiz.flows.hybrid_analysis_flow.EnhancedETFAnalysisTool", return_value=mock_etf_tool)

        # Set up flow state
        flow.state.ticker = "SPY"
        flow.state.asset_class = "etf"
        flow.state.company_name = "SPDR S&P 500 ETF"

        # Act - collect data
        result = flow.collect_data()

        # Assert - verify ETF data collection
        assert result["ticker"] == "SPY"
        assert result["asset_class"] == "etf"
        assert "raw_data" in result

        # Verify ETF-specific metrics
        assert "expense_ratio" in result["raw_data"]
        assert result["raw_data"]["expense_ratio"] == approx(0.003)
        assert "aum" in result["raw_data"]
        assert result["raw_data"]["aum"] == 500e9

    @pytest.mark.asyncio
    async def test_should_process_crypto_with_enhanced_tool(self, mocker):
        """Test complete flow for crypto analysis."""
        # Arrange
        flow = HybridAnalysisFlow()

        # Mock crypto tool
        mock_crypto_tool = mocker.Mock()
        mock_crypto_tool._run.return_value = {
            "crypto_data": {
                "total_volume": 50e9,  # $50B volume
                "market_cap": 1e12,  # $1T market cap
                "circulating_supply": 19e6,
                "max_supply": 21e6,
            }
        }

        mocker.patch("finwiz.flows.hybrid_analysis_flow.EnhancedCryptoAnalysisTool", return_value=mock_crypto_tool)

        # Set up flow state
        flow.state.ticker = "BTC-USD"
        flow.state.asset_class = "crypto"
        flow.state.company_name = "Bitcoin"

        # Act - collect data
        result = flow.collect_data()

        # Assert - verify crypto data collection
        assert result["ticker"] == "BTC-USD"
        assert result["asset_class"] == "crypto"
        assert "raw_data" in result

        # Verify crypto-specific metrics
        assert "volume_24h" in result["raw_data"]
        assert result["raw_data"]["volume_24h"] == 50e9
        assert "market_cap" in result["raw_data"]
        assert result["raw_data"]["market_cap"] == 1e12
        assert "age_years" in result["raw_data"]
        assert result["raw_data"]["age_years"] == approx(15.0)  # BTC age

    @pytest.mark.asyncio
    async def test_should_handle_mixed_portfolio_with_all_asset_classes(self, mocker):
        """Test processing a mixed portfolio with stocks, ETFs, and crypto."""
        # Arrange
        flow = HybridAnalysisFlow()

        # Mock stock data orchestrator
        mock_adapter = mocker.AsyncMock()
        mock_adapter.source_name = "YFinance"
        mock_adapter.is_available.return_value = True
        mock_adapter.get_fundamental_data = mocker.AsyncMock(
            return_value=FundamentalData(
                ticker="AAPL",
                source="YFinance",
                timestamp=datetime.now(),
                confidence=1.0,
                return_on_equity=0.25,
                debt_to_equity=0.5,
                revenue_growth=0.15,
                profit_margin=0.20,
            )
        )

        flow.data_orchestrator.adapters = [mock_adapter]

        # Mock ETF tool
        mock_etf_tool = mocker.Mock()
        mock_etf_tool._run.return_value = {
            "etf_data": {
                "expense_ratio": 0.003,
                "aum": 500e9,
                "tracking_error": 0.005,
                "dividend_yield": 0.015,
            }
        }
        mocker.patch("finwiz.flows.hybrid_analysis_flow.EnhancedETFAnalysisTool", return_value=mock_etf_tool)

        # Mock crypto tool
        mock_crypto_tool = mocker.Mock()
        mock_crypto_tool._run.return_value = {
            "crypto_data": {
                "total_volume": 50e9,
                "market_cap": 1e12,
                "circulating_supply": 19e6,
                "max_supply": 21e6,
            }
        }
        mocker.patch("finwiz.flows.hybrid_analysis_flow.EnhancedCryptoAnalysisTool", return_value=mock_crypto_tool)

        # Test each asset class
        holdings = [
            {"ticker": "AAPL", "asset_class": "stock", "company_name": "Apple Inc."},
            {"ticker": "SPY", "asset_class": "etf", "company_name": "SPDR S&P 500 ETF"},
            {"ticker": "BTC-USD", "asset_class": "crypto", "company_name": "Bitcoin"},
        ]

        results = []
        for holding in holdings:
            # Reset flow state for each holding
            flow.state.ticker = holding["ticker"]
            flow.state.asset_class = holding["asset_class"]
            flow.state.company_name = holding["company_name"]

            # Act
            result = flow.collect_data()
            results.append(result)

        # Assert - verify all asset classes processed correctly
        assert len(results) == 3

        # Stock
        assert results[0]["ticker"] == "AAPL"
        assert "roe" in results[0]["raw_data"]
        assert "data_lineage" in results[0]["raw_data"]

        # ETF
        assert results[1]["ticker"] == "SPY"
        assert "expense_ratio" in results[1]["raw_data"]
        assert "aum" in results[1]["raw_data"]

        # Crypto
        assert results[2]["ticker"] == "BTC-USD"
        assert "volume_24h" in results[2]["raw_data"]
        assert "age_years" in results[2]["raw_data"]

    @pytest.mark.asyncio
    async def test_should_handle_data_orchestrator_failure_gracefully(self, mocker):
        """Test graceful handling when DataSourceOrchestrator fails."""
        # Arrange
        flow = HybridAnalysisFlow()

        # Mock orchestrator to raise exception
        mocker.patch.object(flow.data_orchestrator, "get_fundamental_data", side_effect=Exception("API unavailable"))

        # Set up flow state
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Apple Inc."

        # Act - collect data (should not raise exception)
        result = flow.collect_data()

        # Assert - verify graceful degradation
        assert result["ticker"] == "AAPL"
        assert result["asset_class"] == "stock"
        assert "raw_data" in result

        # Data collection should continue with partial data
        # (other tools like ticker_info, quantitative_analysis, etc. should still work)
        assert result["raw_data"]["ticker"] == "AAPL"
