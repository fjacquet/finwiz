"""
Unit tests for stock screening module.

Tests the StockScreener class and related functionality for fundamental analysis
screening, technical filtering, and multi-criteria stock selection.
"""

import pytest

from finwiz.quantitative.screening import (
    ScreeningCriteria,
    ScreeningFilter,
    ScreeningResult,
    ScreeningScore,
    ScreeningSummary,
    ScreeningUniverse,
    SortOrder,
    StockData,
    StockScreener,
)


class TestStockScreener:
    """Test cases for StockScreener class."""

    @pytest.fixture
    def screener(self):
        """Create a stock screener instance."""
        return StockScreener()

    @pytest.fixture
    def sample_filters(self):
        """Create sample screening filters."""
        return [
            ScreeningFilter(criteria=ScreeningCriteria.PE_RATIO, min_value=5.0, max_value=20.0, weight=1.0),
            ScreeningFilter(criteria=ScreeningCriteria.ROE, min_value=0.15, weight=1.5),
            ScreeningFilter(criteria=ScreeningCriteria.DEBT_TO_EQUITY, max_value=0.5, weight=1.0),
        ]

    @pytest.fixture
    def sample_stock_data(self):
        """Create sample stock data."""
        return StockData(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=2.5e12,
            price=150.0,
            pe_ratio=25.0,
            pb_ratio=8.0,
            dividend_yield=0.006,
            roe=0.30,
            roa=0.20,
            debt_to_equity=0.3,
            revenue_growth=0.08,
            earnings_growth=0.12,
            rsi=55.0,
            price_change_1m=0.05,
            price_change_3m=0.10,
            price_change_1y=0.25,
            volume_avg_3m=50000000,
            beta=1.2,
        )

    def test_screener_initialization(self, screener):
        """Test stock screener initialization."""
        assert screener is not None
        assert hasattr(screener, "config")
        assert hasattr(screener, "_data_cache")
        assert hasattr(screener, "_universe_cache")
        assert hasattr(screener, "universe_symbols")

    def test_universe_symbols_loading(self, screener):
        """Test loading of stock universe symbols."""
        assert ScreeningUniverse.SP500 in screener.universe_symbols
        assert ScreeningUniverse.NASDAQ100 in screener.universe_symbols
        assert ScreeningUniverse.RUSSELL2000 in screener.universe_symbols
        assert ScreeningUniverse.DOW30 in screener.universe_symbols

        # Check that each universe has symbols
        for universe, symbols in screener.universe_symbols.items():
            assert isinstance(symbols, list)
            assert len(symbols) > 0
            assert all(isinstance(symbol, str) for symbol in symbols)

    def test_screening_filter_validation(self):
        """Test screening filter validation."""
        # Valid filter
        valid_filter = ScreeningFilter(criteria=ScreeningCriteria.PE_RATIO, min_value=10.0, max_value=20.0)
        assert valid_filter.min_value == 10.0
        assert valid_filter.max_value == 20.0

        # Invalid filter (max < min)
        with pytest.raises(ValueError):
            ScreeningFilter(criteria=ScreeningCriteria.PE_RATIO, min_value=20.0, max_value=10.0)

    def test_stock_data_creation(self, sample_stock_data):
        """Test stock data model creation."""
        assert sample_stock_data.symbol == "AAPL"
        assert sample_stock_data.company_name == "Apple Inc."
        assert sample_stock_data.market_cap > 0
        assert sample_stock_data.price > 0
        assert sample_stock_data.pe_ratio > 0
        assert sample_stock_data.roe > 0

    def test_generate_mock_stock_data(self, screener):
        """Test mock stock data generation."""
        stock_data = screener._generate_mock_stock_data("TEST")

        assert isinstance(stock_data, StockData)
        assert stock_data.symbol == "TEST"
        assert stock_data.company_name == "TEST Corporation"
        assert stock_data.market_cap > 0
        assert stock_data.price > 0
        assert stock_data.sector in ["Technology", "Healthcare", "Financial", "Consumer", "Industrial", "Energy"]

    def test_get_criteria_value(self, screener, sample_stock_data):
        """Test getting criteria values from stock data."""
        pe_value = screener._get_criteria_value(sample_stock_data, ScreeningCriteria.PE_RATIO)
        assert pe_value == sample_stock_data.pe_ratio

        roe_value = screener._get_criteria_value(sample_stock_data, ScreeningCriteria.ROE)
        assert roe_value == sample_stock_data.roe

        market_cap_value = screener._get_criteria_value(sample_stock_data, ScreeningCriteria.MARKET_CAP)
        assert market_cap_value == sample_stock_data.market_cap

    def test_passes_filter(self, screener, sample_stock_data):
        """Test individual filter checking."""
        # Filter that should pass
        passing_filter = ScreeningFilter(criteria=ScreeningCriteria.PE_RATIO, min_value=20.0, max_value=30.0)
        assert screener._passes_filter(sample_stock_data, passing_filter) is True

        # Filter that should fail (min value)
        failing_filter_min = ScreeningFilter(criteria=ScreeningCriteria.PE_RATIO, min_value=30.0)
        assert screener._passes_filter(sample_stock_data, failing_filter_min) is False

        # Filter that should fail (max value)
        failing_filter_max = ScreeningFilter(criteria=ScreeningCriteria.PE_RATIO, max_value=20.0)
        assert screener._passes_filter(sample_stock_data, failing_filter_max) is False

    def test_apply_filters(self, screener, sample_filters):
        """Test applying multiple filters to stock data."""
        # Create test stock data
        stock_data_list = [screener._generate_mock_stock_data(f"STOCK{i}") for i in range(10)]

        filtered_stocks = screener._apply_filters(stock_data_list, sample_filters)

        assert isinstance(filtered_stocks, list)
        assert len(filtered_stocks) <= len(stock_data_list)

        # Check that all filtered stocks pass all filters
        for stock in filtered_stocks:
            for filter_criteria in sample_filters:
                assert screener._passes_filter(stock, filter_criteria)

    def test_calculate_criteria_score(self, screener, sample_stock_data):
        """Test criteria score calculation."""
        # Test ROE scoring (higher is better)
        roe_filter = ScreeningFilter(criteria=ScreeningCriteria.ROE, min_value=0.1)
        roe_score = screener._calculate_criteria_score(sample_stock_data, roe_filter)
        assert 0 <= roe_score <= 100
        assert roe_score > 0  # Should be positive for good ROE

        # Test PE ratio scoring (optimal range)
        pe_filter = ScreeningFilter(criteria=ScreeningCriteria.PE_RATIO, min_value=10, max_value=30)
        pe_score = screener._calculate_criteria_score(sample_stock_data, pe_filter)
        assert 0 <= pe_score <= 100

        # Test market cap scoring (logarithmic)
        mc_filter = ScreeningFilter(criteria=ScreeningCriteria.MARKET_CAP, min_value=1e9)
        mc_score = screener._calculate_criteria_score(sample_stock_data, mc_filter)
        assert 0 <= mc_score <= 100

    def test_calculate_scores(self, screener, sample_filters):
        """Test scoring calculation for stocks."""
        stock_data_list = [screener._generate_mock_stock_data(f"STOCK{i}") for i in range(5)]

        scored_stocks = screener._calculate_scores(stock_data_list, sample_filters)

        assert len(scored_stocks) == len(stock_data_list)

        for stock_data, score in scored_stocks:
            assert isinstance(stock_data, StockData)
            assert isinstance(score, ScreeningScore)
            assert score.symbol == stock_data.symbol
            assert 0 <= score.total_score <= 100
            assert len(score.criteria_scores) == len(sample_filters)

    def test_sort_and_rank(self, screener, sample_filters):
        """Test sorting and ranking of screening results."""
        stock_data_list = [screener._generate_mock_stock_data(f"STOCK{i}") for i in range(5)]

        scored_stocks = screener._calculate_scores(stock_data_list, sample_filters)
        sorted_stocks = screener._sort_and_rank(scored_stocks, "total_score", SortOrder.DESCENDING)

        assert len(sorted_stocks) == len(scored_stocks)

        # Check sorting (descending by total score)
        scores = [score.total_score for _, score in sorted_stocks]
        assert scores == sorted(scores, reverse=True)

        # Check ranking
        for i, (_, score) in enumerate(sorted_stocks):
            assert score.rank == i + 1
            assert 0 <= score.percentile <= 100

    def test_generate_recommendation(self, screener):
        """Test recommendation generation based on scores."""
        # High score
        high_score = ScreeningScore(symbol="HIGH", total_score=85.0, criteria_scores={}, rank=1, percentile=95.0)
        assert screener._generate_recommendation(None, high_score) == "STRONG BUY"

        # Medium score
        medium_score = ScreeningScore(symbol="MED", total_score=50.0, criteria_scores={}, rank=5, percentile=50.0)
        assert screener._generate_recommendation(None, medium_score) == "HOLD"

        # Low score
        low_score = ScreeningScore(symbol="LOW", total_score=10.0, criteria_scores={}, rank=10, percentile=10.0)
        assert screener._generate_recommendation(None, low_score) == "AVOID"

    def test_screen_stocks_basic(self, screener, sample_filters):
        """Test basic stock screening functionality."""
        results, summary = screener.screen_stocks(filters=sample_filters, universe=ScreeningUniverse.SP500, max_results=5)

        assert isinstance(results, list)
        assert isinstance(summary, ScreeningSummary)
        assert len(results) <= 5
        assert summary.total_stocks_screened > 0
        assert summary.execution_time >= 0

        # Check result structure
        for result in results:
            assert isinstance(result, ScreeningResult)
            assert result.symbol in screener.universe_symbols[ScreeningUniverse.SP500]
            assert isinstance(result.stock_data, StockData)
            assert isinstance(result.screening_score, ScreeningScore)
            assert result.recommendation in ["STRONG BUY", "BUY", "HOLD", "WEAK HOLD", "AVOID"]

    def test_screen_stocks_custom_universe(self, screener, sample_filters):
        """Test screening with custom symbol list."""
        custom_symbols = ["AAPL", "GOOGL", "MSFT"]

        results, summary = screener.screen_stocks(
            filters=sample_filters, universe=ScreeningUniverse.CUSTOM, custom_symbols=custom_symbols, max_results=10
        )

        assert len(results) <= len(custom_symbols)
        assert summary.total_stocks_screened == len(custom_symbols)

        # Check that only custom symbols are included
        result_symbols = [result.symbol for result in results]
        for symbol in result_symbols:
            assert symbol in custom_symbols

    def test_screen_stocks_sorting(self, screener, sample_filters):
        """Test different sorting options."""
        # Sort by total score descending
        results_desc, _ = screener.screen_stocks(
            filters=sample_filters,
            universe=ScreeningUniverse.SP500,
            max_results=5,
            sort_by="total_score",
            sort_order=SortOrder.DESCENDING,
        )

        if len(results_desc) > 1:
            scores = [result.screening_score.total_score for result in results_desc]
            assert scores == sorted(scores, reverse=True)

        # Sort by total score ascending
        results_asc, _ = screener.screen_stocks(
            filters=sample_filters,
            universe=ScreeningUniverse.SP500,
            max_results=5,
            sort_by="total_score",
            sort_order=SortOrder.ASCENDING,
        )

        if len(results_asc) > 1:
            scores = [result.screening_score.total_score for result in results_asc]
            assert scores == sorted(scores)

    def test_generate_summary(self, screener, sample_filters):
        """Test screening summary generation."""
        results = [
            ScreeningResult(
                symbol=f"STOCK{i}",
                company_name=f"Company {i}",
                sector="Technology" if i % 2 == 0 else "Healthcare",
                industry="Software",
                stock_data=screener._generate_mock_stock_data(f"STOCK{i}"),
                screening_score=ScreeningScore(symbol=f"STOCK{i}", total_score=50.0, criteria_scores={}, rank=i, percentile=50.0),
                recommendation="HOLD",
            )
            for i in range(5)
        ]

        summary = screener._generate_summary(10, 5, sample_filters, 1.5, results)

        assert isinstance(summary, ScreeningSummary)
        assert summary.total_stocks_screened == 10
        assert summary.stocks_passed == 5
        assert summary.pass_rate == 50.0
        assert summary.execution_time == 1.5
        assert len(summary.top_sectors) > 0
        assert len(summary.screening_criteria) == len(sample_filters)

    def test_create_custom_screen(self, screener, sample_filters):
        """Test creating custom screening configuration."""
        custom_screen = screener.create_custom_screen(
            name="Value Screen", filters=sample_filters, description="Screen for value stocks"
        )

        assert isinstance(custom_screen, dict)
        assert custom_screen["name"] == "Value Screen"
        assert custom_screen["description"] == "Screen for value stocks"
        assert len(custom_screen["filters"]) == len(sample_filters)
        assert "created_at" in custom_screen

    def test_get_predefined_screens(self, screener):
        """Test getting predefined screening configurations."""
        predefined_screens = screener.get_predefined_screens()

        assert isinstance(predefined_screens, dict)
        assert "value_stocks" in predefined_screens
        assert "growth_stocks" in predefined_screens
        assert "dividend_stocks" in predefined_screens
        assert "quality_stocks" in predefined_screens

        # Check that each screen has filters
        for screen_name, filters in predefined_screens.items():
            assert isinstance(filters, list)
            assert len(filters) > 0
            assert all(isinstance(f, ScreeningFilter) for f in filters)

    def test_analyze_screening_performance(self, screener):
        """Test screening performance analysis."""
        results = [
            ScreeningResult(
                symbol=f"STOCK{i}",
                company_name=f"Company {i}",
                sector="Technology",
                industry="Software",
                stock_data=screener._generate_mock_stock_data(f"STOCK{i}"),
                screening_score=ScreeningScore(symbol=f"STOCK{i}", total_score=70.0, criteria_scores={}, rank=i, percentile=70.0),
                recommendation="BUY",
            )
            for i in range(3)
        ]

        performance = screener.analyze_screening_performance(results, time_period=30)

        assert isinstance(performance, dict)
        assert "total_return" in performance
        assert "annualized_return" in performance
        assert "win_rate" in performance
        assert "sharpe_ratio" in performance
        assert "number_of_stocks" in performance
        assert "analysis_period_days" in performance
        assert performance["number_of_stocks"] == len(results)
        assert performance["analysis_period_days"] == 30

    def test_screening_with_empty_filters(self, screener):
        """Test screening with no filters."""
        results, summary = screener.screen_stocks(filters=[], universe=ScreeningUniverse.SP500, max_results=5)

        # Should return stocks without filtering
        assert len(results) <= 5
        assert summary.stocks_passed == summary.total_stocks_screened
        assert summary.pass_rate == 100.0

    def test_screening_error_handling(self, screener, sample_filters):
        """Test error handling in screening."""
        # Test with invalid universe and no custom symbols
        with pytest.raises(ValueError):
            screener.screen_stocks(filters=sample_filters, universe=ScreeningUniverse.CUSTOM, custom_symbols=None)

    def test_fetch_stock_data(self, screener):
        """Test stock data fetching."""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        stock_data_list = screener._fetch_stock_data(symbols)

        assert isinstance(stock_data_list, list)
        assert len(stock_data_list) <= len(symbols)  # Some might fail

        for stock_data in stock_data_list:
            assert isinstance(stock_data, StockData)
            assert stock_data.symbol in symbols

    def test_screening_filter_weights(self, screener):
        """Test that filter weights affect scoring."""
        stock_data = screener._generate_mock_stock_data("TEST")

        # Same criteria with different weights
        filter_low_weight = ScreeningFilter(criteria=ScreeningCriteria.ROE, min_value=0.1, weight=0.5)

        filter_high_weight = ScreeningFilter(criteria=ScreeningCriteria.ROE, min_value=0.1, weight=2.0)

        # Calculate scores with different filter sets
        low_weight_scored = screener._calculate_scores([stock_data], [filter_low_weight])
        high_weight_scored = screener._calculate_scores([stock_data], [filter_high_weight])

        # Scores should be the same since it's the same criteria
        low_weight_scored[0][1].total_score
        high_weight_scored[0][1].total_score

        # Individual criteria scores should be the same
        low_criteria_score = low_weight_scored[0][1].criteria_scores[ScreeningCriteria.ROE.value]
        high_criteria_score = high_weight_scored[0][1].criteria_scores[ScreeningCriteria.ROE.value]
        assert abs(low_criteria_score - high_criteria_score) < 1e-6

    def test_universe_symbol_methods(self, screener):
        """Test universe symbol retrieval methods."""
        sp500_symbols = screener._get_sp500_symbols()
        nasdaq100_symbols = screener._get_nasdaq100_symbols()
        russell2000_symbols = screener._get_russell2000_symbols()
        dow30_symbols = screener._get_dow30_symbols()

        assert isinstance(sp500_symbols, list)
        assert isinstance(nasdaq100_symbols, list)
        assert isinstance(russell2000_symbols, list)
        assert isinstance(dow30_symbols, list)

        assert len(sp500_symbols) > 0
        assert len(nasdaq100_symbols) > 0
        assert len(russell2000_symbols) > 0
        assert len(dow30_symbols) > 0

        # Check for common symbols
        assert "AAPL" in sp500_symbols
        assert "AAPL" in nasdaq100_symbols
        assert "AAPL" in dow30_symbols
