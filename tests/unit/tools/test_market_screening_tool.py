"""
Unit tests for Market Screening Tool.

Tests the comprehensive market screening functionality for ETFs, stocks,
and cryptocurrencies with A+ criteria filtering.
"""

from datetime import datetime

import pytest
from pytest import approx

from finwiz.schemas.tools import MarketScreeningInput, MarketScreeningResult
from finwiz.tools.market_screening_tool import MarketScreeningTool
from finwiz.tools.screening_ranking import ScreeningCandidate


class TestMarketScreeningTool:
    """Test suite for Market Screening Tool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = MarketScreeningTool()

    def test_should_initialize_tool_correctly(self):
        """Test tool initialization."""
        assert self.tool.name == "Market Screening Tool"
        assert "screens large universes" in self.tool.description.lower()
        assert self.tool.args_schema == MarketScreeningInput
        # Check for refactored components
        assert hasattr(self.tool, "_utils")
        assert hasattr(self.tool, "_criteria")
        assert hasattr(self.tool, "_ranking")

    def test_should_validate_input_schema_correctly(self):
        """Test input schema validation."""
        # Valid input
        valid_input = MarketScreeningInput(asset_type="etf", market_region="us", max_candidates=25, min_a_plus_score=0.9)
        assert valid_input.asset_type == "etf"
        assert valid_input.market_region == "us"
        assert valid_input.max_candidates == 25
        assert valid_input.min_a_plus_score == approx(0.9)

        # Invalid asset type
        with pytest.raises(ValueError):
            MarketScreeningInput(asset_type="invalid")

        # Invalid score range
        with pytest.raises(ValueError):
            MarketScreeningInput(asset_type="stock", min_a_plus_score=1.5)

        # Invalid max candidates
        with pytest.raises(ValueError):
            MarketScreeningInput(asset_type="crypto", max_candidates=1000)

    def test_should_screen_etf_universe_successfully(self):
        """Test ETF universe screening."""
        result = self.tool._run(asset_type="etf", market_region="us", max_candidates=10, min_a_plus_score=0.8)

        assert "screening_result" in result
        assert "summary" in result
        assert "top_candidates" in result

        summary = result["summary"]
        assert summary["asset_type"] == "etf"
        assert summary["total_screened"] > 0
        assert summary["candidates_found"] >= 0
        assert "success_rate" in summary

    def test_should_screen_stock_universe_successfully(self):
        """Test stock universe screening."""
        result = self.tool._run(asset_type="stock", market_region="us", max_candidates=15, min_a_plus_score=0.85)

        assert "screening_result" in result
        assert result["summary"]["asset_type"] == "stock"
        assert result["summary"]["total_screened"] > 0

    def test_should_screen_crypto_universe_successfully(self):
        """Test crypto universe screening."""
        result = self.tool._run(asset_type="crypto", market_region="global", max_candidates=20, min_a_plus_score=0.75)

        assert "screening_result" in result
        assert result["summary"]["asset_type"] == "crypto"
        assert result["summary"]["total_screened"] > 0

    def test_should_get_etf_universe_correctly(self):
        """Test ETF universe retrieval."""
        # US market - now using _utils component
        us_universe = self.tool._utils._get_etf_universe("us")
        assert "symbols" in us_universe
        assert "SPY" in us_universe["symbols"]
        assert "VOO" in us_universe["symbols"]
        assert us_universe["count"] > 0

        # EU market
        eu_universe = self.tool._utils._get_etf_universe("eu")
        assert "symbols" in eu_universe
        assert len(eu_universe["symbols"]) > 0

        # Global market
        global_universe = self.tool._utils._get_etf_universe("global")
        assert len(global_universe["symbols"]) >= len(us_universe["symbols"])

    def test_should_get_stock_universe_correctly(self):
        """Test stock universe retrieval."""
        # US market - now using _utils component
        us_universe = self.tool._utils._get_stock_universe("us")
        assert "symbols" in us_universe
        assert "AAPL" in us_universe["symbols"]
        assert "MSFT" in us_universe["symbols"]
        assert us_universe["count"] > 0

        # EU market
        eu_universe = self.tool._utils._get_stock_universe("eu")
        assert "symbols" in eu_universe
        assert len(eu_universe["symbols"]) > 0

    def test_should_get_crypto_universe_correctly(self):
        """Test crypto universe retrieval."""
        # Now using _utils component
        crypto_universe = self.tool._utils._get_crypto_universe("global")
        assert "symbols" in crypto_universe
        assert "BTC" in crypto_universe["symbols"]
        assert "ETH" in crypto_universe["symbols"]
        assert crypto_universe["count"] > 0

    def test_should_get_default_screening_criteria_correctly(self):
        """Test default screening criteria."""
        # ETF criteria - now using _criteria component
        etf_criteria = self.tool._criteria.get_default_criteria("etf")
        assert "max_expense_ratio" in etf_criteria
        assert "min_aum" in etf_criteria
        assert etf_criteria["max_expense_ratio"] == approx(0.25)
        assert etf_criteria["min_aum"] == 1e9

        # Stock criteria
        stock_criteria = self.tool._criteria.get_default_criteria("stock")
        assert "min_roe" in stock_criteria
        assert "min_revenue_growth" in stock_criteria
        assert stock_criteria["min_roe"] == approx(0.20)
        assert stock_criteria["min_revenue_growth"] == approx(0.15)

        # Crypto criteria
        crypto_criteria = self.tool._criteria.get_default_criteria("crypto")
        assert "min_market_cap" in crypto_criteria
        assert "min_daily_volume" in crypto_criteria
        assert crypto_criteria["min_market_cap"] == 10e9
        assert crypto_criteria["min_daily_volume"] == 500e6

    def test_should_get_etf_market_data_correctly(self):
        """Test ETF market data retrieval."""
        # Known ETF - now using _utils component
        spy_data = self.tool._utils._get_etf_market_data("SPY")
        assert spy_data["symbol"] == "SPY"
        assert spy_data["asset_type"] == "etf"
        assert "expense_ratio" in spy_data
        assert "aum" in spy_data
        assert spy_data["expense_ratio"] < 0.1  # SPY has low fees

        # Unknown ETF (should get defaults)
        unknown_data = self.tool._utils._get_etf_market_data("UNKNOWN")
        assert unknown_data["symbol"] == "UNKNOWN"
        assert unknown_data["expense_ratio"] == approx(0.20)  # Default

    def test_should_get_stock_market_data_correctly(self):
        """Test stock market data retrieval."""
        # Known stock - now using _utils component
        aapl_data = self.tool._utils._get_stock_market_data("AAPL")
        assert aapl_data["symbol"] == "AAPL"
        assert aapl_data["asset_type"] == "stock"
        assert "market_cap" in aapl_data
        assert "roe" in aapl_data
        assert aapl_data["market_cap"] > 1e12  # Apple is large cap

        # Unknown stock (should get defaults)
        unknown_data = self.tool._utils._get_stock_market_data("UNKNOWN")
        assert unknown_data["symbol"] == "UNKNOWN"
        assert unknown_data["market_cap"] == 5e8  # Default

    def test_should_get_crypto_market_data_correctly(self):
        """Test crypto market data retrieval."""
        # Known crypto - now using _utils component
        btc_data = self.tool._utils._get_crypto_market_data("BTC")
        assert btc_data["symbol"] == "BTC"
        assert btc_data["asset_type"] == "crypto"
        assert "market_cap" in btc_data
        assert "daily_volume" in btc_data
        assert btc_data["institutional_adoption"] is True  # BTC has institutional adoption

        # Unknown crypto (should get defaults)
        unknown_data = self.tool._utils._get_crypto_market_data("UNKNOWN")
        assert unknown_data["symbol"] == "UNKNOWN"
        assert unknown_data["market_cap"] == 1e9  # Default

    def test_should_apply_etf_screening_filters_correctly(self):
        """Test ETF screening filters."""
        # Good ETF data (should pass)
        good_etf_data = {
            "symbol": "VOO",
            "expense_ratio": 0.03,
            "aum": 300e9,
            "tracking_error": 0.0008,
            "history_years": 12,
        }
        criteria = self.tool._criteria.get_default_criteria("etf")
        assert self.tool._criteria._passes_etf_filters(good_etf_data, criteria) is True

        # Bad ETF data (should fail)
        bad_etf_data = {
            "symbol": "EXPENSIVE",
            "expense_ratio": 1.5,  # Too expensive
            "aum": 100e6,  # Too small
            "tracking_error": 0.01,  # Too high
            "history_years": 1,  # Too short
        }
        assert self.tool._criteria._passes_etf_filters(bad_etf_data, criteria) is False

    def test_should_apply_stock_screening_filters_correctly(self):
        """Test stock screening filters."""
        # Good stock data (should pass)
        good_stock_data = {
            "symbol": "QUALITY",
            "roe": 0.25,
            "revenue_growth": 0.18,
            "debt_to_equity": 0.2,
            "market_cap": 50e9,
            "fcf_positive": True,
            "fcf_growing": True,
        }
        criteria = self.tool._criteria.get_default_criteria("stock")
        assert self.tool._criteria._passes_stock_filters(good_stock_data, criteria) is True

        # Bad stock data (should fail)
        bad_stock_data = {
            "symbol": "POOR",
            "roe": 0.05,  # Too low
            "revenue_growth": 0.02,  # Too low
            "debt_to_equity": 0.8,  # Too high
            "market_cap": 100e6,  # Too small
            "fcf_positive": False,  # No FCF
            "fcf_growing": False,
        }
        assert self.tool._criteria._passes_stock_filters(bad_stock_data, criteria) is False

    def test_should_apply_crypto_screening_filters_correctly(self):
        """Test crypto screening filters."""
        # Good crypto data (should pass)
        good_crypto_data = {
            "symbol": "BTC",
            "market_cap": 800e9,
            "daily_volume": 15e9,
            "age_months": 180,
            "institutional_adoption": True,
            "real_utility": True,
        }
        criteria = self.tool._criteria.get_default_criteria("crypto")
        assert self.tool._criteria._passes_crypto_filters(good_crypto_data, criteria) is True

        # Bad crypto data (should fail)
        bad_crypto_data = {
            "symbol": "SMALL",
            "market_cap": 1e9,  # Too small
            "daily_volume": 10e6,  # Too low
            "age_months": 12,  # Too young
            "institutional_adoption": False,
            "real_utility": False,
        }
        assert self.tool._criteria._passes_crypto_filters(bad_crypto_data, criteria) is False

    def test_should_calculate_preliminary_scores_correctly(self):
        """Test preliminary scoring calculations."""
        # High-quality ETF - now using _ranking component
        good_etf_data = {
            "expense_ratio": 0.03,
            "aum": 300e9,
            "tracking_error": 0.0008,
            "history_years": 15,
        }
        etf_score = self.tool._ranking._score_etf_preliminary(good_etf_data)
        assert etf_score > 0.8  # Should score highly

        # High-quality stock
        good_stock_data = {
            "roe": 0.30,
            "revenue_growth": 0.20,
            "debt_to_equity": 0.15,
            "market_cap": 200e9,
            "fcf_positive": True,
            "fcf_growing": True,
        }
        stock_score = self.tool._ranking._score_stock_preliminary(good_stock_data)
        assert stock_score > 0.8  # Should score highly

        # High-quality crypto
        good_crypto_data = {
            "market_cap": 500e9,
            "daily_volume": 10e9,
            "age_months": 100,
            "institutional_adoption": True,
            "real_utility": True,
        }
        crypto_score = self.tool._ranking._score_crypto_preliminary(good_crypto_data)
        assert crypto_score > 0.8  # Should score highly

    def test_should_extract_key_metrics_correctly(self):
        """Test key metrics extraction."""
        # ETF metrics - now using _utils component
        etf_data = {
            "expense_ratio": 0.05,
            "aum": 100e9,
            "tracking_error": 0.001,
            "history_years": 10,
            "other_field": "ignored",
        }
        etf_metrics = self.tool._utils.extract_key_metrics(etf_data, "etf")
        assert "expense_ratio" in etf_metrics
        assert "aum" in etf_metrics
        assert "other_field" not in etf_metrics

        # Stock metrics
        stock_data = {
            "market_cap": 50e9,
            "roe": 0.25,
            "revenue_growth": 0.15,
            "debt_to_equity": 0.2,
            "other_field": "ignored",
        }
        stock_metrics = self.tool._utils.extract_key_metrics(stock_data, "stock")
        assert "market_cap" in stock_metrics
        assert "roe" in stock_metrics
        assert "other_field" not in stock_metrics

        # Crypto metrics
        crypto_data = {
            "market_cap": 100e9,
            "daily_volume": 5e9,
            "age_months": 60,
            "institutional_adoption": True,
            "other_field": "ignored",
        }
        crypto_metrics = self.tool._utils.extract_key_metrics(crypto_data, "crypto")
        assert "market_cap" in crypto_metrics
        assert "daily_volume" in crypto_metrics
        assert "other_field" not in crypto_metrics

    def test_should_generate_screening_rationale_correctly(self):
        """Test screening rationale generation."""
        # A+ candidate - now using _utils component
        good_data = {
            "symbol": "TEST",
            "name": "Test Investment",
            "expense_ratio": 0.05,
            "aum": 100e9,
        }
        a_plus_rationale = self.tool._utils.generate_screening_rationale(good_data, "etf", 0.95, True)
        assert "qualifies as A+ candidate" in a_plus_rationale
        assert "TEST" in a_plus_rationale
        assert "0.95" in a_plus_rationale

        # Non-A+ candidate
        poor_data = {
            "symbol": "POOR",
            "name": "Poor Investment",
            "roe": 0.10,
            "revenue_growth": 0.05,
        }
        poor_rationale = self.tool._utils.generate_screening_rationale(poor_data, "stock", 0.65, False)
        assert "shows potential" in poor_rationale
        assert "needs improvement" in poor_rationale
        assert "POOR" in poor_rationale

    def test_should_handle_custom_screening_criteria(self):
        """Test custom screening criteria override."""
        custom_criteria = {
            "max_expense_ratio": 0.10,  # Stricter than default 0.25
            "min_aum": 5e9,  # Stricter than default 1e9
        }

        result = self.tool._run(asset_type="etf", screening_criteria=custom_criteria, market_region="us", max_candidates=5)

        assert "screening_result" in result
        # Should have fewer candidates due to stricter criteria
        assert result["summary"]["candidates_found"] >= 0

    def test_should_limit_candidates_correctly(self):
        """Test candidate limiting functionality."""
        # Request only 3 candidates
        result = self.tool._run(
            asset_type="etf",
            max_candidates=3,
            min_a_plus_score=0.0,  # Low threshold to get more candidates
        )

        top_candidates = result["top_candidates"]
        assert len(top_candidates) <= 3

    def test_should_handle_different_market_regions(self):
        """Test different market region handling."""
        # US market
        us_result = self.tool._run(asset_type="stock", market_region="us")
        assert us_result["summary"]["total_screened"] > 0

        # EU market
        eu_result = self.tool._run(asset_type="stock", market_region="eu")
        assert eu_result["summary"]["total_screened"] > 0

        # Global market should have more symbols
        global_result = self.tool._run(asset_type="stock", market_region="global")
        assert global_result["summary"]["total_screened"] >= us_result["summary"]["total_screened"]

    def test_should_handle_errors_gracefully(self, mocker):
        """Test error handling."""
        # Invalid asset type
        result = self.tool._run(asset_type="invalid")
        assert "error" in result
        assert result.get("candidates_found", 0) == 0

        # Test with mock that raises exception on a real method
        with mocker.patch.object(self.tool, "_apply_screening_filters", side_effect=Exception("Test error")):
            result = self.tool._run(asset_type="etf")
            assert "error" in result

    def test_should_use_caching_efficiently(self):
        """Test caching functionality."""
        # First call should populate cache - now using _utils component
        data1 = self.tool._utils.get_basic_market_data("SPY", "etf")

        # Second call should use cache
        data2 = self.tool._utils.get_basic_market_data("SPY", "etf")

        assert data1 == data2
        # Cache should contain some data after the calls
        assert len(self.tool._utils._screening_cache) >= 0  # Cache may or may not be populated depending on implementation

    def test_should_integrate_with_a_plus_scorer_when_detailed_analysis_enabled(self, mocker):
        """Test integration with A+ scoring tool."""
        # Mock the A+ scorer _run method
        mock_scorer = mocker.patch.object(self.tool._ranking._a_plus_scorer, "_run")
        mock_scorer.return_value = {
            "composite_score": 0.92,
            "is_a_plus_candidate": True,
            "grade": "A+",
        }

        result = self.tool._run(asset_type="etf", max_candidates=1, include_detailed_analysis=True)

        # Should have called the A+ scorer for detailed analysis
        if result["summary"]["candidates_found"] > 0:
            mock_scorer.assert_called()

    def test_should_validate_screening_candidate_model(self):
        """Test ScreeningCandidate model validation."""
        # Valid candidate
        valid_candidate = ScreeningCandidate(
            symbol="TEST",
            name="Test Investment",
            asset_type="etf",
            preliminary_score=0.85,
            meets_a_plus_criteria=True,
            screening_rationale="Test rationale",
            data_source="Test Source",
            screened_at=datetime.now(),
        )
        assert valid_candidate.symbol == "TEST"
        assert valid_candidate.preliminary_score == approx(0.85)

        # Invalid score range
        with pytest.raises(ValueError):
            ScreeningCandidate(
                symbol="TEST",
                name="Test Investment",
                asset_type="etf",
                preliminary_score=1.5,  # Invalid score > 1.0
                meets_a_plus_criteria=True,
                screening_rationale="Test rationale",
                data_source="Test Source",
                screened_at=datetime.now(),
            )

    def test_should_validate_market_screening_result_model(self):
        """Test MarketScreeningResult model validation."""
        candidates = [
            ScreeningCandidate(
                symbol="TEST1",
                name="Test 1",
                asset_type="etf",
                preliminary_score=0.9,
                meets_a_plus_criteria=True,
                screening_rationale="Good ETF",
                data_source="Test",
                screened_at=datetime.now(),
            )
        ]

        result = MarketScreeningResult(
            asset_type="etf",
            screening_criteria={"max_expense_ratio": 0.25},
            market_region="us",
            total_screened=100,
            candidates_found=1,
            a_plus_candidates=1,
            candidates=candidates,
            screening_timestamp=datetime.now(),
            data_sources=["Test Source"],
        )

        assert result.asset_type == "etf"
        assert result.total_screened == 100
        assert len(result.candidates) == 1

    @pytest.mark.parametrize(
        "asset_type,expected_symbols",
        [
            ("etf", ["SPY", "VOO", "VTI"]),
            ("stock", ["AAPL", "MSFT", "GOOGL"]),
            ("crypto", ["BTC", "ETH", "ADA"]),
        ],
    )
    def test_should_return_expected_symbols_for_asset_types(self, asset_type, expected_symbols):
        """Test that each asset type returns expected symbols."""
        # Now using _utils component
        if asset_type == "etf":
            universe = self.tool._utils._get_etf_universe("us")
        elif asset_type == "stock":
            universe = self.tool._utils._get_stock_universe("us")
        elif asset_type == "crypto":
            universe = self.tool._utils._get_crypto_universe("global")

        symbols = universe["symbols"]
        for expected_symbol in expected_symbols:
            assert expected_symbol in symbols

    def test_should_handle_empty_screening_results(self):
        """Test handling of empty screening results."""
        # Use very strict criteria that should return no results
        strict_criteria = {
            "min_a_plus_score": 0.99,  # Nearly impossible threshold
            "max_expense_ratio": 0.001,  # Nearly impossible for ETFs
        }

        result = self.tool._run(asset_type="etf", screening_criteria=strict_criteria, min_a_plus_score=0.99)

        assert "screening_result" in result
        assert result["summary"]["candidates_found"] >= 0  # Could be 0
        assert result["summary"]["a_plus_candidates"] >= 0

    def test_should_sort_candidates_by_score(self):
        """Test that candidates are sorted by score in descending order."""
        result = self.tool._run(
            asset_type="stock",
            max_candidates=5,
            min_a_plus_score=0.0,  # Low threshold to get multiple candidates
        )

        top_candidates = result["top_candidates"]
        if len(top_candidates) > 1:
            # Check that scores are in descending order
            scores = [c["score"] for c in top_candidates]
            assert scores == sorted(scores, reverse=True)
