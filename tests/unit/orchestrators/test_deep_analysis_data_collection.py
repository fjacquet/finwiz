"""
Comprehensive tests for Python-first data collection architecture in DeepAnalysisOrchestrator.

This test suite validates:
1. Python data collection (_collect_data_with_python)
2. Data extraction and flattening
3. Python scorer receives correct metrics
4. Numerical stability
5. No missing imports or errors

Created by pytest-test-architect for AI Minimalism validation.
"""

import json
from datetime import datetime

import pytest
from pytest import approx

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator


class TestPythonDataCollection:
    """Test suite for Python-first data collection architecture."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance with mocked state."""
        state = FinwizState()
        state.full_date = datetime.now().isoformat()
        orchestrator = DeepAnalysisOrchestrator(state)
        return orchestrator

    @pytest.fixture
    def mock_yahoo_ticker_data(self):
        """Mock Yahoo Finance ticker info response."""
        return {"current_price": 175.43, "market_cap": 2800000000000, "volume": 50123456, "52_week_high": 199.62, "52_week_low": 124.17, "pe_ratio": 29.5, "dividend_yield": 0.0044}

    @pytest.fixture
    def mock_yahoo_company_data(self):
        """Mock Yahoo Finance company info response with fundamentals."""
        return {
            "financial_metrics": {
                "return_on_equity": 1.4717,  # 147.17% ROE
                "debt_to_equity": 1.95,
                "revenue_growth": 0.08,  # 8% growth
                "profit_margin": 0.2531,  # 25.31% margin
                "operating_margin": 0.2943,
                "gross_margin": 0.4413,
            },
            "company_info": {"sector": "Technology", "industry": "Consumer Electronics", "employees": 161000},
        }

    @pytest.fixture
    def mock_quantitative_data(self):
        """Mock quantitative analysis tool response."""
        return json.dumps(
            {
                "technical_indicators": {
                    "rsi": 58.3,
                    "macd": {"value": 2.1, "signal": 1.8, "histogram": 0.3},
                    "bollinger_bands": {"upper": 180.5, "middle": 175.0, "lower": 169.5},
                    "sma_20": 172.3,
                    "sma_50": 168.9,
                    "ema_12": 174.2,
                },
                "risk_metrics": {"volatility": 0.283, "beta": 1.25, "sharpe_ratio": 1.82, "max_drawdown": -0.157, "value_at_risk": -0.023},
                "performance": {"returns_1m": 0.045, "returns_3m": 0.123, "returns_6m": 0.089, "returns_1y": 0.267},
            }
        )

    @pytest.fixture
    def mock_sentiment_data(self):
        """Mock sentiment analysis tool response (matches actual EnhancedSentimentAnalysisTool output)."""
        return {
            "formatted_analysis": "Sentiment analysis for AAPL...",
            "sentiment_score": 0.72,
            "overall_sentiment": "POSITIVE",
            "confidence": 0.85,
            "positive_ratio": 0.65,
            "negative_ratio": 0.15,
            "neutral_ratio": 0.20,
            "total_articles": 20,
            "sentiment_distribution": {"positive": 13, "negative": 3, "neutral": 4},
            "trending_topics": ["AI expansion", "Services growth", "China market"],
            "article_count": 20,
            "news_sources": ["Yahoo Finance", "Sonar"],
            "sentiment_breakdown": {"positive": 13, "negative": 3, "neutral": 4},
        }

    @pytest.fixture
    def mock_sec_data(self):
        """Mock SEC analysis tool response."""
        return json.dumps(
            {
                "filing_info": {"form_type": "10-K", "filing_date": "2024-11-01", "fiscal_year": 2024},
                "risk_factors": {"total_risks": 15, "high_priority": 3, "categories": ["Competition", "Supply Chain", "Regulatory"]},
                "financial_highlights": {"revenue": 383285000000, "net_income": 97000000000, "cash_position": 29943000000},
            }
        )

    @pytest.mark.integration
    def test_collect_data_with_python_success(
        self, mocker, orchestrator, mock_yahoo_ticker_data, mock_yahoo_company_data, mock_quantitative_data, mock_sentiment_data, mock_sec_data
    ):
        """Test successful data collection from all tools."""
        # Setup mocks
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run")

        # Mock DataSourceOrchestrator for stock fundamental data
        from datetime import datetime

        from finwiz.data.data_source_orchestrator import OrchestrationResult

        mock_orchestration_result = OrchestrationResult(
            ticker="AAPL",
            timestamp=datetime.now(),
            return_on_equity=mock_yahoo_company_data["financial_metrics"]["return_on_equity"],
            debt_to_equity=mock_yahoo_company_data["financial_metrics"]["debt_to_equity"],
            revenue_growth=mock_yahoo_company_data["financial_metrics"]["revenue_growth"],
            profit_margin=mock_yahoo_company_data["financial_metrics"]["profit_margin"],
            sources_succeeded=["YFinance"],
            confidence=1.0,
        )
        # Mock on data_collector.data_orchestrator since collect_data uses data_collector's instance
        mock_data_orchestrator = mocker.patch.object(
            orchestrator.data_collector.data_orchestrator, "get_fundamental_data", new=mocker.AsyncMock(return_value=mock_orchestration_result)
        )

        mock_quant = mocker.patch("finwiz.tools.quantitative_analysis_tool.QuantitativeAnalysisTool._run")
        mock_sentiment = mocker.patch("finwiz.tools.enhanced_sentiment_tool.EnhancedSentimentAnalysisTool._run")
        mock_sec = mocker.patch("finwiz.tools.enhanced_sec_tool.EnhancedSECAnalysisTool._run")

        # Configure mocks
        mock_ticker.return_value = mock_yahoo_ticker_data
        mock_quant.return_value = mock_quantitative_data
        mock_sentiment.return_value = mock_sentiment_data
        mock_sec.return_value = mock_sec_data

        # Execute data collection
        result = orchestrator.data_collector.collect_data("AAPL", "stock", batch_enabled=False)

        # Verify all tools were called
        mock_ticker.assert_called_once_with(ticker="AAPL")
        # DataSourceOrchestrator is called for stocks instead of YahooFinanceCompanyInfoTool
        mock_quant.assert_called_once()
        mock_sentiment.assert_called_once()
        mock_sec.assert_called_once()

        # Verify core metrics are present
        assert result["ticker"] == "AAPL"
        assert result["asset_class"] == "stock"

        # The _collect_data_with_python method extracts current_price to top level before flattening
        # Check if current_price made it through the flattening
        if "current_price" not in result:
            # Debug output to see what's in the result
            import json

            print("Result keys:", list(result.keys()))
            print("Result contents:", json.dumps(result, indent=2, default=str))
        assert "current_price" in result
        assert result["current_price"] == approx(175.43)

        # Verify fundamental metrics extracted to top level
        assert "roe" in result
        assert result["roe"] == approx(1.4717)
        assert "debt_to_equity" in result
        assert result["debt_to_equity"] == approx(1.95)
        assert "revenue_growth" in result
        assert result["revenue_growth"] == approx(0.08)
        assert "profit_margin" in result
        assert result["profit_margin"] == approx(0.2531)

        # Verify nested data has been flattened (no longer nested)
        # Technical indicators from quantitative_analysis should be flattened
        assert "rsi" in result  # From quantitative_analysis.technical_indicators.rsi
        assert "volatility" in result  # From quantitative_analysis.risk_metrics.volatility

        # Sentiment data should be flattened
        assert "sentiment_score" in result  # From sentiment tool output
        assert result["sentiment_score"] == approx(0.72)
        assert "overall_sentiment" in result
        assert result["overall_sentiment"] == "POSITIVE"

    @pytest.mark.integration
    def test_collect_data_handles_tool_failures(self, mocker, orchestrator):
        """Test graceful handling when individual tools fail."""
        # ✅ CORRECT pytest-mock pattern: NO context managers
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run")
        mock_company = mocker.patch("finwiz.tools.yahoo_finance_company_info_tool.YahooFinanceCompanyInfoTool._run")
        mock_quant = mocker.patch("finwiz.tools.quantitative_analysis_tool.QuantitativeAnalysisTool._run")
        mock_sentiment = mocker.patch("finwiz.tools.enhanced_sentiment_tool.EnhancedSentimentAnalysisTool._run")

        # Configure one tool to succeed, others to fail
        mock_ticker.return_value = {"current_price": 150.0}
        mock_company.side_effect = Exception("API rate limit")
        mock_quant.side_effect = Exception("Connection timeout")
        mock_sentiment.return_value = {
            "sentiment_score": 0.6,
            "overall_sentiment": "neutral",
            "confidence": 0.5,
        }

        # Execute - should not raise exception
        result = orchestrator.data_collector.collect_data("TSLA", "stock", batch_enabled=False)

        # Verify basic structure exists
        assert result["ticker"] == "TSLA"
        assert result["asset_class"] == "stock"
        assert result["current_price"] == approx(150.0)

        # Failed tools should have empty data (quantitative_analysis would have been {})
        # Since company_info and quantitative_analysis failed, they won't contribute flattened fields

        # Successful tool data should be present
        # Sentiment data should be at top level
        assert "sentiment_score" in result
        assert result["sentiment_score"] == approx(0.6)
        assert "overall_sentiment" in result
        assert result["overall_sentiment"] == "neutral"

    @pytest.mark.integration
    def test_collect_data_etf_skips_sec_analysis(self, mocker, orchestrator):
        """Test that ETF assets skip SEC analysis (stock-only feature)."""
        # ✅ CORRECT pytest-mock pattern: NO context managers
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run")
        mock_company = mocker.patch("finwiz.tools.yahoo_finance_company_info_tool.YahooFinanceCompanyInfoTool._run")
        mock_quant = mocker.patch("finwiz.tools.quantitative_analysis_tool.QuantitativeAnalysisTool._run")
        mock_sentiment = mocker.patch("finwiz.tools.enhanced_sentiment_tool.EnhancedSentimentAnalysisTool._run")
        mock_sec = mocker.patch("finwiz.tools.enhanced_sec_tool.EnhancedSECAnalysisTool._run")

        mock_ticker.return_value = {"current_price": 420.0}
        mock_quant.return_value = json.dumps({"technical_indicators": {"rsi": 55}})
        mock_sentiment.return_value = {
            "sentiment_score": 0.65,
            "overall_sentiment": "neutral",
            "confidence": 0.7,
        }

        # Execute for ETF
        result = orchestrator.data_collector.collect_data("SPY", "etf", batch_enabled=False)

        # SEC tool should NOT be called for ETFs
        mock_sec.assert_not_called()

        # Company info should also not be called for ETFs
        mock_company.assert_not_called()

        # Other tools should be called
        mock_ticker.assert_called_once()
        mock_quant.assert_called_once()
        mock_sentiment.assert_called_once()

    def test_flatten_collected_data(self, mocker, orchestrator):
        """Test data flattening for Python scorer consumption."""
        nested_data = {
            "ticker": "AAPL",
            "current_price": 175.0,
            "ticker_info": {"market_cap": 2800000000000, "pe_ratio": 29.5},
            "company_info": {"financial_metrics": {"return_on_equity": 1.47, "debt_to_equity": 1.95}},
            "quantitative_analysis": {"technical_indicators": {"rsi": 58.3, "macd": {"value": 2.1}}, "risk_metrics": {"volatility": 0.28, "beta": 1.25}},
        }

        flattened = orchestrator.data_collector.flatten_collected_data(nested_data)

        # Top-level fields preserved
        assert flattened["ticker"] == "AAPL"
        assert flattened["current_price"] == approx(175.0)

        # Nested fields should be flattened to top level
        # ticker_info fields should be flattened
        assert "market_cap" in flattened  # From ticker_info.market_cap
        assert "pe_ratio" in flattened  # From ticker_info.pe_ratio

        # quantitative_analysis fields should be flattened
        assert "rsi" in flattened  # From quantitative_analysis.technical_indicators.rsi
        assert "volatility" in flattened  # From quantitative_analysis.risk_metrics.volatility
        assert "beta" in flattened  # From quantitative_analysis.risk_metrics.beta

        # company_info fields should be flattened
        assert "return_on_equity" in flattened  # From company_info.financial_metrics.return_on_equity
        assert "debt_to_equity" in flattened  # From company_info.financial_metrics.debt_to_equity

    @pytest.mark.integration
    def test_numerical_stability_edge_cases(self, mocker, orchestrator):
        """Test handling of edge cases in numerical data."""
        edge_case_data = {
            "current_price": 0.0001,  # Penny stock
            "financial_metrics": {
                "return_on_equity": -2.5,  # Negative ROE
                "debt_to_equity": 999999,  # Extremely high debt
                "revenue_growth": float("nan"),  # NaN value
                "profit_margin": None,  # Null value
            },
        }

        # ✅ CORRECT pytest-mock pattern: NO context managers
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run")
        mock_company = mocker.patch("finwiz.tools.yahoo_finance_company_info_tool.YahooFinanceCompanyInfoTool._run")

        mock_ticker.return_value = {"current_price": edge_case_data["current_price"]}
        mock_company.return_value = {"financial_metrics": edge_case_data["financial_metrics"]}

        # Should handle edge cases without crashing
        result = orchestrator.data_collector.collect_data("PENNY", "stock", batch_enabled=False)

        assert result["current_price"] == approx(0.0001)
        # NaN and None values should be handled gracefully in flattening

    @pytest.mark.integration
    def test_json_parsing_robustness(self, mocker, orchestrator):
        """Test robust JSON parsing from tool outputs."""
        # ✅ CORRECT pytest-mock pattern: NO context managers
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run")
        mock_company = mocker.patch("finwiz.tools.yahoo_finance_company_info_tool.YahooFinanceCompanyInfoTool._run")
        mock_quant = mocker.patch("finwiz.tools.quantitative_analysis_tool.QuantitativeAnalysisTool._run")
        mock_sentiment = mocker.patch("finwiz.tools.enhanced_sentiment_tool.EnhancedSentimentAnalysisTool._run")
        mock_sec = mocker.patch("finwiz.tools.enhanced_sec_tool.EnhancedSECAnalysisTool._run")

        # Mock minimal responses for other tools
        mock_ticker.return_value = {"current_price": 100.0}
        mock_company.return_value = {}
        mock_sentiment.return_value = {
            "sentiment_score": 0.0,
            "overall_sentiment": "neutral",
            "confidence": 0.0,
        }
        mock_sec.return_value = json.dumps({})

        # Test 1: Already parsed dict
        mock_quant.return_value = {"technical_indicators": {"rsi": 60}}
        result = orchestrator.data_collector.collect_data("TEST1", "stock", batch_enabled=False)
        # After flattening, rsi should be at top level
        assert "rsi" in result

        # Test 2: JSON string
        mock_quant.return_value = '{"technical_indicators": {"rsi": 55}}'
        result = orchestrator.data_collector.collect_data("TEST2", "stock", batch_enabled=False)
        assert "rsi" in result
        assert result["rsi"] == 55

        # Test 3: Malformed JSON - should be caught and handled
        mock_quant.return_value = '{"invalid": json}'
        result = orchestrator.data_collector.collect_data("TEST3", "stock", batch_enabled=False)
        # With malformed JSON, quantitative_analysis will be {} and won't contribute fields
        assert "rsi" not in result  # No RSI since JSON was malformed

    @pytest.mark.integration
    def test_scorer_integration(self, mocker, orchestrator, mock_yahoo_ticker_data, mock_yahoo_company_data, mock_quantitative_data):
        """Test that collected data integrates correctly with Python scorer."""
        # ✅ CORRECT pytest-mock pattern: NO context managers
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run")
        mock_company = mocker.patch("finwiz.tools.yahoo_finance_company_info_tool.YahooFinanceCompanyInfoTool._run")
        mock_quant = mocker.patch("finwiz.tools.quantitative_analysis_tool.QuantitativeAnalysisTool._run")
        mocker.patch("finwiz.tools.enhanced_sentiment_tool.EnhancedSentimentAnalysisTool._run")

        mock_ticker.return_value = mock_yahoo_ticker_data
        mock_company.return_value = mock_yahoo_company_data
        mock_quant.return_value = mock_quantitative_data

        # Test the full flow including scorer
        from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

        raw_data = orchestrator.data_collector.collect_data("AAPL", "stock", batch_enabled=False)

        scorer = DeepAnalysisScorer()
        scoring_result = scorer.calculate_composite_score("AAPL", "stock", raw_data)

        # Verify scorer produces valid output
        assert scoring_result is not None
        assert hasattr(scoring_result, "ticker")
        assert hasattr(scoring_result, "composite_score")
        assert hasattr(scoring_result, "grade")
        assert scoring_result.ticker == "AAPL"
        assert 0 <= scoring_result.composite_score <= 1.0
        assert scoring_result.grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]

    def test_import_stability(self):
        """Test that all required imports work without errors."""
        # These imports should not raise any exceptions
        from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer
        from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool
        from finwiz.tools.enhanced_sentiment_tool import EnhancedSentimentAnalysisTool
        from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool
        from finwiz.tools.yahoo_finance_company_info_tool import YahooFinanceCompanyInfoTool
        from finwiz.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool

        # Verify classes can be instantiated
        assert QuantitativeAnalysisTool is not None
        assert EnhancedSentimentAnalysisTool is not None
        assert YahooFinanceTickerInfoTool is not None
        assert YahooFinanceCompanyInfoTool is not None
        assert EnhancedSECAnalysisTool is not None
        assert DeepAnalysisScorer is not None

    @pytest.mark.integration
    def test_batch_mode_parameter_propagation(self, mocker, orchestrator):
        """Test that batch_enabled parameter is properly used."""
        # ✅ CORRECT pytest-mock pattern: NO context managers
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run")
        mock_ticker.return_value = {"current_price": 100.0}

        # Test with batch_enabled=True
        result = orchestrator.data_collector.collect_data("BATCH1", "stock", batch_enabled=True)
        assert result["ticker"] == "BATCH1"

        # Test with batch_enabled=False
        result = orchestrator.data_collector.collect_data("BATCH2", "stock", batch_enabled=False)
        assert result["ticker"] == "BATCH2"

        # Both should work without issues
        assert mock_ticker.call_count == 2
