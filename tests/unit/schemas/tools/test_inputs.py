"""
Comprehensive pytest tests for tool input schemas.

This module tests all Pydantic models in finwiz.schemas.tools.inputs.
Tests verify:
- Model instantiation with required fields
- Default values work correctly
- Field validation (min/max, ge/le constraints)
- Invalid inputs raise ValidationError
- Optional fields can be None
"""

import pytest
from faker import Faker
from pydantic import ValidationError

from finwiz.schemas.tools.inputs import (
    # Alpha Vantage
    AlphaVantageNewsInput,
    APlusScore,
    # A+ Scoring
    APlusScoringInput,
    # Backtesting
    BacktestingInput,
    # Chart Generation
    ChartImgInput,
    # CoinMarketCap
    CoinInfoInput,
    CompanyOverviewInput,
    CriteriaOptimizationInput,
    CrossAssetSentimentComparatorInput,
    CryptocurrencyHistoricalInput,
    CryptocurrencyListInput,
    CryptocurrencyNewsInput,
    # DeFi Metrics
    DeFiMetricsInput,
    # Crypto Analysis
    EnhancedCryptoAnalysisInput,
    # ETF Analysis
    EnhancedETFAnalysisInput,
    # SEC Analysis
    EnhancedSECAnalysisInput,
    # Feedback
    FeedbackCollectionInput,
    GetCompanyInfoInput,
    GetETFHoldingsInput,
    # Yahoo Finance
    GetTickerHistoryInput,
    GetTickerInfoInput,
    GetTickerNewsInput,
    # Market Regime
    MarketRegime,
    # Market Screening
    MarketScreeningInput,
    # Custom Tool
    MyCustomToolInput,
    # Optimization
    OptimizationInput,
    PerformanceTrackingInput,
    # Perplexity
    PerplexitySearchWrapperInput,
    PortfolioAnalysisInput,
    # Portfolio Rebalancing
    PortfolioRebalancingInput,
    # Quantitative Analysis
    QuantitativeAnalysisInput,
    # Regulatory Compliance
    RegulatoryComplianceInput,
    # Risk Assessment
    RiskAssessmentInput,
    # Scoring
    ScoringCriteria,
    StandardizedRiskScoringInput,
    StandardizedSentimentInput,
    TwelveDataIndicatorInput,
    TwelveDataMultiIndicatorInput,
)


@pytest.fixture
def fake():
    """Faker instance for generating test data."""
    return Faker()


# ============================================================================
# CoinMarketCap Tool Tests
# ============================================================================


class TestCoinInfoInput:
    """Tests for CoinInfoInput model."""

    def test_required_symbol(self, fake):
        """Test instantiation with required symbol field."""
        symbol = fake.random_element(["BTC", "ETH", "SOL"])
        model = CoinInfoInput(symbol=symbol)

        assert model.symbol == symbol

    def test_missing_required_symbol(self):
        """Test ValidationError when required symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CoinInfoInput()
        assert "symbol" in str(exc_info.value)

    def test_symbol_as_string(self, fake):
        """Test symbol field accepts strings."""
        model = CoinInfoInput(symbol="DOGE")
        assert isinstance(model.symbol, str)


class TestCryptocurrencyListInput:
    """Tests for CryptocurrencyListInput model."""

    def test_default_values(self):
        """Test default values are set correctly."""
        model = CryptocurrencyListInput()

        assert model.limit == 25
        assert model.sort == "market_cap"

    def test_custom_limit(self, fake):
        """Test instantiation with custom limit."""
        limit = fake.random_int(min=1, max=100)
        model = CryptocurrencyListInput(limit=limit)

        assert model.limit == limit

    def test_custom_sort(self):
        """Test instantiation with custom sort."""
        sorts = ["market_cap", "volume_24h", "price", "percent_change_24h"]
        for sort in sorts:
            model = CryptocurrencyListInput(sort=sort)
            assert model.sort == sort

    def test_all_fields(self, fake):
        """Test instantiation with all fields."""
        limit = 50
        sort = "volume_24h"
        model = CryptocurrencyListInput(limit=limit, sort=sort)

        assert model.limit == 50
        assert model.sort == "volume_24h"


class TestCryptocurrencyHistoricalInput:
    """Tests for CryptocurrencyHistoricalInput model."""

    def test_required_symbol(self, fake):
        """Test instantiation with required symbol."""
        symbol = "BTC"
        model = CryptocurrencyHistoricalInput(symbol=symbol)

        assert model.symbol == symbol
        assert model.time_period == "30d"

    def test_time_period_default(self):
        """Test time_period default value."""
        model = CryptocurrencyHistoricalInput(symbol="ETH")

        assert model.time_period == "30d"

    def test_time_period_options(self):
        """Test various time period options."""
        periods = ["24h", "7d", "30d", "3m", "1y", "ytd"]
        for period in periods:
            model = CryptocurrencyHistoricalInput(symbol="BTC", time_period=period)
            assert model.time_period == period

    def test_missing_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CryptocurrencyHistoricalInput()
        assert "symbol" in str(exc_info.value)


class TestCryptocurrencyNewsInput:
    """Tests for CryptocurrencyNewsInput model."""

    def test_optional_symbol_none(self):
        """Test symbol can be None (optional)."""
        model = CryptocurrencyNewsInput(symbol=None)

        assert model.symbol is None

    def test_symbol_with_value(self):
        """Test symbol with actual value."""
        model = CryptocurrencyNewsInput(symbol="BTC")

        assert model.symbol == "BTC"

    def test_default_limit(self):
        """Test default limit value."""
        model = CryptocurrencyNewsInput()

        assert model.limit == 10

    def test_custom_limit(self, fake):
        """Test custom limit value."""
        limit = fake.random_int(min=1, max=100)
        model = CryptocurrencyNewsInput(limit=limit)

        assert model.limit == limit

    def test_no_arguments(self):
        """Test instantiation with no arguments (all defaults/optional)."""
        model = CryptocurrencyNewsInput()

        assert model.symbol is None
        assert model.limit == 10


# ============================================================================
# Chart Generation Tool Tests
# ============================================================================


class TestChartImgInput:
    """Tests for ChartImgInput model."""

    def test_required_symbol(self, fake):
        """Test instantiation with required symbol."""
        symbol = "AAPL"
        model = ChartImgInput(symbol=symbol)

        assert model.symbol == symbol

    def test_default_values(self):
        """Test all default values."""
        model = ChartImgInput(symbol="SPY")

        assert model.interval == "1day"
        assert model.range == "6mo"
        assert model.width == 900
        assert model.height == 500
        assert model.theme == "light"

    def test_custom_interval(self):
        """Test custom interval values."""
        intervals = ["1min", "5min", "1h", "1day"]
        for interval in intervals:
            model = ChartImgInput(symbol="AAPL", interval=interval)
            assert model.interval == interval

    def test_custom_range(self):
        """Test custom range values."""
        ranges = ["1mo", "3mo", "6mo", "1y", "5y", "max"]
        for range_val in ranges:
            model = ChartImgInput(symbol="AAPL", range=range_val)
            assert model.range == range_val

    def test_custom_dimensions(self, fake):
        """Test custom width and height."""
        width = fake.random_int(min=300, max=2000)
        height = fake.random_int(min=200, max=1500)
        model = ChartImgInput(symbol="AAPL", width=width, height=height)

        assert model.width == width
        assert model.height == height

    def test_theme_literal_constraint(self):
        """Test theme field literal constraint."""
        # Valid values
        model_light = ChartImgInput(symbol="AAPL", theme="light")
        assert model_light.theme == "light"

        model_dark = ChartImgInput(symbol="AAPL", theme="dark")
        assert model_dark.theme == "dark"

        # Invalid value
        with pytest.raises(ValidationError) as exc_info:
            ChartImgInput(symbol="AAPL", theme="invalid")
        assert "theme" in str(exc_info.value)

    def test_missing_required_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            ChartImgInput()
        assert "symbol" in str(exc_info.value)


# ============================================================================
# Alpha Vantage Tool Tests
# ============================================================================


class TestAlphaVantageNewsInput:
    """Tests for AlphaVantageNewsInput model."""

    def test_required_tickers(self, fake):
        """Test instantiation with required tickers."""
        tickers = "AAPL,GOOGL,MSFT"
        model = AlphaVantageNewsInput(tickers=tickers)

        assert model.tickers == tickers

    def test_default_values(self):
        """Test default values."""
        model = AlphaVantageNewsInput(tickers="AAPL")

        assert model.sort == "LATEST"
        assert model.time_from is None
        assert model.time_to is None
        assert model.limit == 50
        assert model.topics is None

    def test_optional_time_from_none(self):
        """Test time_from can be None."""
        model = AlphaVantageNewsInput(tickers="AAPL", time_from=None)

        assert model.time_from is None

    def test_optional_time_from_value(self):
        """Test time_from with ISO8601 value."""
        time_from = "20250101T0930"
        model = AlphaVantageNewsInput(tickers="AAPL", time_from=time_from)

        assert model.time_from == time_from

    def test_optional_topics_none(self):
        """Test topics can be None."""
        model = AlphaVantageNewsInput(tickers="AAPL", topics=None)

        assert model.topics is None

    def test_optional_topics_value(self):
        """Test topics with comma-separated values."""
        topics = "technology,financial_markets"
        model = AlphaVantageNewsInput(tickers="AAPL", topics=topics)

        assert model.topics == topics

    def test_sort_options(self):
        """Test various sort options."""
        sorts = ["LATEST", "EARLIEST", "RELEVANCE"]
        for sort in sorts:
            model = AlphaVantageNewsInput(tickers="AAPL", sort=sort)
            assert model.sort == sort

    def test_missing_required_tickers(self):
        """Test ValidationError when tickers is missing."""
        with pytest.raises(ValidationError) as exc_info:
            AlphaVantageNewsInput()
        assert "tickers" in str(exc_info.value)


class TestCompanyOverviewInput:
    """Tests for CompanyOverviewInput model."""

    def test_required_ticker(self, fake):
        """Test instantiation with required ticker."""
        ticker = "AAPL"
        model = CompanyOverviewInput(ticker=ticker)

        assert model.ticker == ticker

    def test_default_include_perplexity(self):
        """Test default include_perplexity value."""
        model = CompanyOverviewInput(ticker="AAPL")

        assert model.include_perplexity is True

    def test_custom_include_perplexity(self):
        """Test custom include_perplexity value."""
        model_false = CompanyOverviewInput(ticker="AAPL", include_perplexity=False)
        assert model_false.include_perplexity is False

        model_true = CompanyOverviewInput(ticker="AAPL", include_perplexity=True)
        assert model_true.include_perplexity is True

    def test_missing_required_ticker(self):
        """Test ValidationError when ticker is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CompanyOverviewInput()
        assert "ticker" in str(exc_info.value)


# ============================================================================
# Technical Analysis Tool Tests
# ============================================================================


class TestTwelveDataIndicatorInput:
    """Tests for TwelveDataIndicatorInput model."""

    def test_required_fields(self, fake):
        """Test instantiation with required fields."""
        symbol = "AAPL"
        indicator = "rsi"
        model = TwelveDataIndicatorInput(symbol=symbol, indicator=indicator)

        assert model.symbol == symbol
        assert model.indicator == indicator

    def test_default_values(self):
        """Test default values."""
        model = TwelveDataIndicatorInput(symbol="AAPL", indicator="rsi")

        assert model.interval == "1day"
        assert model.length is None
        assert model.fast_period is None
        assert model.slow_period is None
        assert model.signal_period is None
        assert model.outputsize == 100

    def test_indicator_literal_constraint(self):
        """Test indicator field literal constraint."""
        indicators = ["rsi", "macd", "bbands"]
        for indicator in indicators:
            model = TwelveDataIndicatorInput(symbol="AAPL", indicator=indicator)
            assert model.indicator == indicator

        with pytest.raises(ValidationError) as exc_info:
            TwelveDataIndicatorInput(symbol="AAPL", indicator="invalid")
        assert "indicator" in str(exc_info.value)

    def test_optional_parameters_none(self):
        """Test optional parameters can be None."""
        model = TwelveDataIndicatorInput(
            symbol="AAPL",
            indicator="rsi",
            length=None,
            fast_period=None,
            slow_period=None,
            signal_period=None,
        )

        assert model.length is None
        assert model.fast_period is None
        assert model.slow_period is None
        assert model.signal_period is None

    def test_optional_parameters_values(self, fake):
        """Test optional parameters with values."""
        length = fake.random_int(min=5, max=50)
        model = TwelveDataIndicatorInput(symbol="AAPL", indicator="rsi", length=length)

        assert model.length == length

    def test_missing_required_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            TwelveDataIndicatorInput(indicator="rsi")
        assert "symbol" in str(exc_info.value)

    def test_missing_required_indicator(self):
        """Test ValidationError when indicator is missing."""
        with pytest.raises(ValidationError) as exc_info:
            TwelveDataIndicatorInput(symbol="AAPL")
        assert "indicator" in str(exc_info.value)


class TestTwelveDataMultiIndicatorInput:
    """Tests for TwelveDataMultiIndicatorInput model."""

    def test_required_fields(self, fake):
        """Test instantiation with required fields."""
        symbol = "AAPL"
        indicators = ["rsi", "macd"]
        model = TwelveDataMultiIndicatorInput(symbol=symbol, indicators=indicators)

        assert model.symbol == symbol
        assert model.indicators == indicators

    def test_default_values(self):
        """Test default values."""
        model = TwelveDataMultiIndicatorInput(symbol="AAPL", indicators=["rsi"])

        assert model.interval == "1day"
        assert model.rsi_period == 14
        assert model.macd_fast == 12
        assert model.macd_slow == 26
        assert model.macd_signal == 9
        assert model.bbands_period == 20
        assert model.bbands_stddev == 2
        assert model.outputsize == 100

    def test_all_indicators(self):
        """Test with all indicator options."""
        indicators = ["rsi", "macd", "bbands"]
        model = TwelveDataMultiIndicatorInput(symbol="AAPL", indicators=indicators)

        assert model.indicators == indicators

    def test_custom_periods(self, fake):
        """Test custom period values."""
        rsi_period = fake.random_int(min=5, max=30)
        macd_fast = fake.random_int(min=5, max=15)

        model = TwelveDataMultiIndicatorInput(
            symbol="AAPL",
            indicators=["rsi", "macd"],
            rsi_period=rsi_period,
            macd_fast=macd_fast,
        )

        assert model.rsi_period == rsi_period
        assert model.macd_fast == macd_fast

    def test_missing_required_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            TwelveDataMultiIndicatorInput(indicators=["rsi"])
        assert "symbol" in str(exc_info.value)

    def test_missing_required_indicators(self):
        """Test ValidationError when indicators is missing."""
        with pytest.raises(ValidationError) as exc_info:
            TwelveDataMultiIndicatorInput(symbol="AAPL")
        assert "indicators" in str(exc_info.value)


# ============================================================================
# Sentiment Analysis Tool Tests
# ============================================================================


class TestStandardizedSentimentInput:
    """Tests for StandardizedSentimentInput model."""

    def test_required_fields(self, fake):
        """Test instantiation with required fields."""
        symbol = "AAPL"
        asset_class = "stock"
        model = StandardizedSentimentInput(symbol=symbol, asset_class=asset_class)

        assert model.symbol == symbol
        assert model.asset_class == asset_class

    def test_default_values(self):
        """Test default values."""
        model = StandardizedSentimentInput(symbol="AAPL", asset_class="stock")

        assert model.max_articles == 50
        assert model.days_back == 30
        assert model.include_trending is True

    def test_max_articles_constraint(self):
        """Test max_articles ge/le constraints (10-100)."""
        # Valid: 10
        model_min = StandardizedSentimentInput(symbol="AAPL", asset_class="stock", max_articles=10)
        assert model_min.max_articles == 10

        # Valid: 100
        model_max = StandardizedSentimentInput(symbol="AAPL", asset_class="stock", max_articles=100)
        assert model_max.max_articles == 100

        # Invalid: below 10
        with pytest.raises(ValidationError) as exc_info:
            StandardizedSentimentInput(symbol="AAPL", asset_class="stock", max_articles=5)
        assert "max_articles" in str(exc_info.value)

        # Invalid: above 100
        with pytest.raises(ValidationError) as exc_info:
            StandardizedSentimentInput(symbol="AAPL", asset_class="stock", max_articles=150)
        assert "max_articles" in str(exc_info.value)

    def test_days_back_constraint(self):
        """Test days_back ge/le constraints (7-90)."""
        # Valid: 7
        model_min = StandardizedSentimentInput(symbol="AAPL", asset_class="stock", days_back=7)
        assert model_min.days_back == 7

        # Valid: 90
        model_max = StandardizedSentimentInput(symbol="AAPL", asset_class="stock", days_back=90)
        assert model_max.days_back == 90

        # Invalid: below 7
        with pytest.raises(ValidationError) as exc_info:
            StandardizedSentimentInput(symbol="AAPL", asset_class="stock", days_back=3)
        assert "days_back" in str(exc_info.value)

        # Invalid: above 90
        with pytest.raises(ValidationError) as exc_info:
            StandardizedSentimentInput(symbol="AAPL", asset_class="stock", days_back=100)
        assert "days_back" in str(exc_info.value)

    def test_asset_class_literal(self):
        """Test asset_class literal constraint."""
        classes = ["stock", "etf", "crypto"]
        for asset_class in classes:
            model = StandardizedSentimentInput(symbol="AAPL", asset_class=asset_class)
            assert model.asset_class == asset_class

        with pytest.raises(ValidationError) as exc_info:
            StandardizedSentimentInput(symbol="AAPL", asset_class="invalid")
        assert "asset_class" in str(exc_info.value)

    def test_include_trending_boolean(self):
        """Test include_trending boolean field."""
        model_true = StandardizedSentimentInput(symbol="AAPL", asset_class="stock", include_trending=True)
        assert model_true.include_trending is True

        model_false = StandardizedSentimentInput(symbol="AAPL", asset_class="stock", include_trending=False)
        assert model_false.include_trending is False

    def test_missing_required_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            StandardizedSentimentInput(asset_class="stock")
        assert "symbol" in str(exc_info.value)

    def test_missing_required_asset_class(self):
        """Test ValidationError when asset_class is missing."""
        with pytest.raises(ValidationError) as exc_info:
            StandardizedSentimentInput(symbol="AAPL")
        assert "asset_class" in str(exc_info.value)


class TestCrossAssetSentimentComparatorInput:
    """Tests for CrossAssetSentimentComparatorInput model."""

    def test_required_fields(self, fake):
        """Test instantiation with required fields."""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        asset_classes = ["stock", "stock", "stock"]
        model = CrossAssetSentimentComparatorInput(symbols=symbols, asset_classes=asset_classes)

        assert model.symbols == symbols
        assert model.asset_classes == asset_classes

    def test_single_asset(self):
        """Test with single asset."""
        model = CrossAssetSentimentComparatorInput(symbols=["AAPL"], asset_classes=["stock"])

        assert len(model.symbols) == 1
        assert len(model.asset_classes) == 1

    def test_multiple_asset_types(self):
        """Test with multiple asset types."""
        symbols = ["AAPL", "VTI", "BTC"]
        asset_classes = ["stock", "etf", "crypto"]
        model = CrossAssetSentimentComparatorInput(symbols=symbols, asset_classes=asset_classes)

        assert model.symbols == symbols
        assert model.asset_classes == asset_classes

    def test_missing_required_symbols(self):
        """Test ValidationError when symbols is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CrossAssetSentimentComparatorInput(asset_classes=["stock"])
        assert "symbols" in str(exc_info.value)

    def test_missing_required_asset_classes(self):
        """Test ValidationError when asset_classes is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CrossAssetSentimentComparatorInput(symbols=["AAPL"])
        assert "asset_classes" in str(exc_info.value)


# ============================================================================
# Crypto Analysis Tool Tests
# ============================================================================


class TestEnhancedCryptoAnalysisInput:
    """Tests for EnhancedCryptoAnalysisInput model."""

    def test_required_symbol(self, fake):
        """Test instantiation with required symbol."""
        symbol = "BTC"
        model = EnhancedCryptoAnalysisInput(symbol=symbol)

        assert model.symbol == symbol

    def test_default_values(self):
        """Test default values."""
        model = EnhancedCryptoAnalysisInput(symbol="BTC")

        assert model.include_thesis is True
        assert model.include_risk_assessment is True
        assert model.max_thesis_bullets == 10
        assert model.include_perplexity is True

    def test_max_thesis_bullets_constraint(self):
        """Test max_thesis_bullets ge/le constraints (3-20)."""
        # Valid: 3
        model_min = EnhancedCryptoAnalysisInput(symbol="BTC", max_thesis_bullets=3)
        assert model_min.max_thesis_bullets == 3

        # Valid: 20
        model_max = EnhancedCryptoAnalysisInput(symbol="BTC", max_thesis_bullets=20)
        assert model_max.max_thesis_bullets == 20

        # Invalid: below 3
        with pytest.raises(ValidationError) as exc_info:
            EnhancedCryptoAnalysisInput(symbol="BTC", max_thesis_bullets=1)
        assert "max_thesis_bullets" in str(exc_info.value)

        # Invalid: above 20
        with pytest.raises(ValidationError) as exc_info:
            EnhancedCryptoAnalysisInput(symbol="BTC", max_thesis_bullets=25)
        assert "max_thesis_bullets" in str(exc_info.value)

    def test_boolean_fields(self):
        """Test boolean fields."""
        model = EnhancedCryptoAnalysisInput(
            symbol="BTC",
            include_thesis=False,
            include_risk_assessment=False,
            include_perplexity=False,
        )

        assert model.include_thesis is False
        assert model.include_risk_assessment is False
        assert model.include_perplexity is False

    def test_missing_required_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            EnhancedCryptoAnalysisInput()
        assert "symbol" in str(exc_info.value)


# ============================================================================
# ETF Analysis Tool Tests
# ============================================================================


class TestEnhancedETFAnalysisInput:
    """Tests for EnhancedETFAnalysisInput model."""

    def test_required_ticker(self, fake):
        """Test instantiation with required ticker."""
        ticker = "SPY"
        model = EnhancedETFAnalysisInput(ticker=ticker)

        assert model.ticker == ticker

    def test_default_values(self):
        """Test default values."""
        model = EnhancedETFAnalysisInput(ticker="SPY")

        assert model.include_holdings is True
        assert model.include_risk_assessment is True
        assert model.max_holdings == 10
        assert model.include_perplexity is True

    def test_max_holdings_constraint(self):
        """Test max_holdings ge/le constraints (1-50)."""
        # Valid: 1
        model_min = EnhancedETFAnalysisInput(ticker="SPY", max_holdings=1)
        assert model_min.max_holdings == 1

        # Valid: 50
        model_max = EnhancedETFAnalysisInput(ticker="SPY", max_holdings=50)
        assert model_max.max_holdings == 50

        # Invalid: below 1
        with pytest.raises(ValidationError) as exc_info:
            EnhancedETFAnalysisInput(ticker="SPY", max_holdings=0)
        assert "max_holdings" in str(exc_info.value)

        # Invalid: above 50
        with pytest.raises(ValidationError) as exc_info:
            EnhancedETFAnalysisInput(ticker="SPY", max_holdings=100)
        assert "max_holdings" in str(exc_info.value)

    def test_boolean_fields(self):
        """Test boolean fields."""
        model = EnhancedETFAnalysisInput(
            ticker="SPY",
            include_holdings=False,
            include_risk_assessment=False,
            include_perplexity=False,
        )

        assert model.include_holdings is False
        assert model.include_risk_assessment is False
        assert model.include_perplexity is False

    def test_missing_required_ticker(self):
        """Test ValidationError when ticker is missing."""
        with pytest.raises(ValidationError) as exc_info:
            EnhancedETFAnalysisInput()
        assert "ticker" in str(exc_info.value)


# ============================================================================
# SEC Analysis Tool Tests
# ============================================================================


class TestEnhancedSECAnalysisInput:
    """Tests for EnhancedSECAnalysisInput model."""

    def test_required_ticker(self, fake):
        """Test instantiation with required ticker."""
        ticker = "AAPL"
        model = EnhancedSECAnalysisInput(ticker=ticker)

        assert model.ticker == ticker

    def test_default_values(self):
        """Test default values."""
        model = EnhancedSECAnalysisInput(ticker="AAPL")

        assert model.form_type == "10-K"
        assert model.sections == ["Item 1", "Item 1A", "Item 7"]
        assert model.risk_assessment is True
        assert model.include_perplexity is True

    def test_form_type_literal(self):
        """Test form_type literal constraint."""
        # Valid: 10-K
        model_10k = EnhancedSECAnalysisInput(ticker="AAPL", form_type="10-K")
        assert model_10k.form_type == "10-K"

        # Valid: 10-Q
        model_10q = EnhancedSECAnalysisInput(ticker="AAPL", form_type="10-Q")
        assert model_10q.form_type == "10-Q"

        # Invalid
        with pytest.raises(ValidationError) as exc_info:
            EnhancedSECAnalysisInput(ticker="AAPL", form_type="8-K")
        assert "form_type" in str(exc_info.value)

    def test_custom_sections(self):
        """Test custom sections selection."""
        sections = ["Item 1", "Item 8"]
        model = EnhancedSECAnalysisInput(ticker="AAPL", sections=sections)

        assert model.sections == sections

    def test_missing_required_ticker(self):
        """Test ValidationError when ticker is missing."""
        with pytest.raises(ValidationError) as exc_info:
            EnhancedSECAnalysisInput()
        assert "ticker" in str(exc_info.value)


class TestStandardizedRiskScoringInput:
    """Tests for StandardizedRiskScoringInput model."""

    def test_required_fields(self, fake):
        """Test instantiation with required fields."""
        symbol = "AAPL"
        asset_class = "stock"
        model = StandardizedRiskScoringInput(symbol=symbol, asset_class=asset_class)

        assert model.symbol == symbol
        assert model.asset_class == asset_class

    def test_default_risk_factors(self):
        """Test default risk_factors (empty list)."""
        model = StandardizedRiskScoringInput(symbol="AAPL", asset_class="stock")

        assert model.risk_factors == []

    def test_custom_risk_factors(self):
        """Test custom risk_factors."""
        risk_factors = ["market_risk", "liquidity_risk", "regulatory_risk"]
        model = StandardizedRiskScoringInput(symbol="AAPL", asset_class="stock", risk_factors=risk_factors)

        assert model.risk_factors == risk_factors

    def test_missing_required_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            StandardizedRiskScoringInput(asset_class="stock")
        assert "symbol" in str(exc_info.value)

    def test_missing_required_asset_class(self):
        """Test ValidationError when asset_class is missing."""
        with pytest.raises(ValidationError) as exc_info:
            StandardizedRiskScoringInput(symbol="AAPL")
        assert "asset_class" in str(exc_info.value)


# ============================================================================
# Yahoo Finance Tool Tests
# ============================================================================


class TestGetTickerHistoryInput:
    """Tests for GetTickerHistoryInput model."""

    def test_required_ticker(self, fake):
        """Test instantiation with required ticker."""
        ticker = "AAPL"
        model = GetTickerHistoryInput(ticker=ticker)

        assert model.ticker == ticker

    def test_default_values(self):
        """Test default values."""
        model = GetTickerHistoryInput(ticker="AAPL")

        assert model.period == "1y"
        assert model.interval == "1d"

    def test_period_options(self):
        """Test various period options."""
        periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        for period in periods:
            model = GetTickerHistoryInput(ticker="AAPL", period=period)
            assert model.period == period

    def test_interval_options(self):
        """Test various interval options."""
        intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
        for interval in intervals:
            model = GetTickerHistoryInput(ticker="AAPL", interval=interval)
            assert model.interval == interval

    def test_missing_required_ticker(self):
        """Test ValidationError when ticker is missing."""
        with pytest.raises(ValidationError) as exc_info:
            GetTickerHistoryInput()
        assert "ticker" in str(exc_info.value)


class TestGetETFHoldingsInput:
    """Tests for GetETFHoldingsInput model."""

    def test_required_ticker(self, fake):
        """Test instantiation with required ticker."""
        ticker = "VTI"
        model = GetETFHoldingsInput(ticker=ticker)

        assert model.ticker == ticker

    def test_missing_required_ticker(self):
        """Test ValidationError when ticker is missing."""
        with pytest.raises(ValidationError) as exc_info:
            GetETFHoldingsInput()
        assert "ticker" in str(exc_info.value)


class TestGetCompanyInfoInput:
    """Tests for GetCompanyInfoInput model."""

    def test_required_ticker(self, fake):
        """Test instantiation with required ticker."""
        ticker = "MSFT"
        model = GetCompanyInfoInput(ticker=ticker)

        assert model.ticker == ticker

    def test_missing_required_ticker(self):
        """Test ValidationError when ticker is missing."""
        with pytest.raises(ValidationError) as exc_info:
            GetCompanyInfoInput()
        assert "ticker" in str(exc_info.value)


class TestGetTickerInfoInput:
    """Tests for GetTickerInfoInput model."""

    def test_required_ticker(self, fake):
        """Test instantiation with required ticker."""
        ticker = "BTC-USD"
        model = GetTickerInfoInput(ticker=ticker)

        assert model.ticker == ticker

    def test_various_ticker_formats(self):
        """Test various ticker formats."""
        tickers = ["AAPL", "VTI", "BTC-USD", "SPY"]
        for ticker in tickers:
            model = GetTickerInfoInput(ticker=ticker)
            assert model.ticker == ticker

    def test_missing_required_ticker(self):
        """Test ValidationError when ticker is missing."""
        with pytest.raises(ValidationError) as exc_info:
            GetTickerInfoInput()
        assert "ticker" in str(exc_info.value)


class TestGetTickerNewsInput:
    """Tests for GetTickerNewsInput model."""

    def test_required_ticker(self, fake):
        """Test instantiation with required ticker."""
        ticker = "AAPL"
        model = GetTickerNewsInput(ticker=ticker)

        assert model.ticker == ticker

    def test_default_limit(self):
        """Test default limit value."""
        model = GetTickerNewsInput(ticker="AAPL")

        assert model.limit == 5

    def test_custom_limit(self, fake):
        """Test custom limit value."""
        limit = fake.random_int(min=1, max=20)
        model = GetTickerNewsInput(ticker="AAPL", limit=limit)

        assert model.limit == limit

    def test_missing_required_ticker(self):
        """Test ValidationError when ticker is missing."""
        with pytest.raises(ValidationError) as exc_info:
            GetTickerNewsInput()
        assert "ticker" in str(exc_info.value)


class TestPortfolioAnalysisInput:
    """Tests for PortfolioAnalysisInput model."""

    def test_required_holdings(self, fake):
        """Test instantiation with required holdings."""
        holdings = [
            {"symbol": "AAPL", "shares": 100},
            {"symbol": "GOOGL", "shares": 50},
        ]
        model = PortfolioAnalysisInput(holdings=holdings)

        assert model.holdings == holdings

    def test_default_values(self):
        """Test default values."""
        holdings = [{"symbol": "AAPL", "shares": 100}]
        model = PortfolioAnalysisInput(holdings=holdings)

        assert model.benchmark == "SPY"
        assert model.analysis_period == "1y"
        assert model.include_risk_metrics is True
        assert model.include_diversification is True

    def test_custom_benchmark(self):
        """Test custom benchmark."""
        holdings = [{"symbol": "AAPL", "shares": 100}]
        model = PortfolioAnalysisInput(holdings=holdings, benchmark="QQQ")

        assert model.benchmark == "QQQ"

    def test_custom_analysis_period(self):
        """Test custom analysis period."""
        holdings = [{"symbol": "AAPL", "shares": 100}]
        model = PortfolioAnalysisInput(holdings=holdings, analysis_period="5y")

        assert model.analysis_period == "5y"

    def test_boolean_fields(self):
        """Test boolean fields."""
        holdings = [{"symbol": "AAPL", "shares": 100}]
        model = PortfolioAnalysisInput(
            holdings=holdings,
            include_risk_metrics=False,
            include_diversification=False,
        )

        assert model.include_risk_metrics is False
        assert model.include_diversification is False

    def test_missing_required_holdings(self):
        """Test ValidationError when holdings is missing."""
        with pytest.raises(ValidationError) as exc_info:
            PortfolioAnalysisInput()
        assert "holdings" in str(exc_info.value)


# ============================================================================
# RAG Tool Tests
# ============================================================================


class TestRiskAssessmentInput:
    """Tests for RiskAssessmentInput model."""

    def test_required_assets(self, fake):
        """Test instantiation with required assets."""
        assets = ["AAPL", "GOOGL", "MSFT"]
        model = RiskAssessmentInput(assets=assets)

        assert model.assets == assets

    def test_default_values(self):
        """Test default values."""
        model = RiskAssessmentInput(assets=["AAPL"])

        assert model.portfolio_weights is None
        assert model.assessment_type == "comprehensive"
        assert model.risk_horizon == "1y"
        assert model.confidence_level == 0.95
        assert model.include_stress_testing is True
        assert model.market_regime == "normal"

    def test_optional_portfolio_weights_none(self):
        """Test portfolio_weights can be None."""
        model = RiskAssessmentInput(assets=["AAPL"], portfolio_weights=None)

        assert model.portfolio_weights is None

    def test_optional_portfolio_weights_dict(self):
        """Test portfolio_weights with dictionary."""
        weights = {"AAPL": 0.5, "GOOGL": 0.3, "MSFT": 0.2}
        model = RiskAssessmentInput(assets=["AAPL", "GOOGL", "MSFT"], portfolio_weights=weights)

        assert model.portfolio_weights == weights

    def test_custom_assessment_type(self):
        """Test custom assessment_type."""
        types = ["individual", "portfolio", "comprehensive"]
        for assessment_type in types:
            model = RiskAssessmentInput(assets=["AAPL"], assessment_type=assessment_type)
            assert model.assessment_type == assessment_type

    def test_custom_confidence_level(self, fake):
        """Test custom confidence_level."""
        confidence = fake.pyfloat(min_value=0.0, max_value=1.0)
        model = RiskAssessmentInput(assets=["AAPL"], confidence_level=confidence)

        assert model.confidence_level == confidence

    def test_missing_required_assets(self):
        """Test ValidationError when assets is missing."""
        with pytest.raises(ValidationError) as exc_info:
            RiskAssessmentInput()
        assert "assets" in str(exc_info.value)


# ============================================================================
# Quantitative Analysis Tool Tests
# ============================================================================


class TestQuantitativeAnalysisInput:
    """Tests for QuantitativeAnalysisInput model."""

    def test_required_fields(self, fake):
        """Test instantiation with required fields."""
        symbol = "AAPL"
        asset_class = "stock"
        model = QuantitativeAnalysisInput(symbol=symbol, asset_class=asset_class)

        assert model.symbol == symbol
        assert model.asset_class == asset_class

    def test_default_values(self):
        """Test default values."""
        model = QuantitativeAnalysisInput(symbol="AAPL", asset_class="stock")

        assert model.analysis_type == "comprehensive"
        assert model.timeframe == "1y"
        assert model.strategy == "sma_crossover"

    def test_custom_analysis_type(self):
        """Test custom analysis_type."""
        types = ["technical", "backtest", "performance", "comprehensive"]
        for analysis_type in types:
            model = QuantitativeAnalysisInput(symbol="AAPL", asset_class="stock", analysis_type=analysis_type)
            assert model.analysis_type == analysis_type

    def test_custom_strategy(self):
        """Test custom strategy."""
        model = QuantitativeAnalysisInput(symbol="AAPL", asset_class="stock", strategy="momentum")

        assert model.strategy == "momentum"

    def test_missing_required_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            QuantitativeAnalysisInput(asset_class="stock")
        assert "symbol" in str(exc_info.value)

    def test_missing_required_asset_class(self):
        """Test ValidationError when asset_class is missing."""
        with pytest.raises(ValidationError) as exc_info:
            QuantitativeAnalysisInput(symbol="AAPL")
        assert "asset_class" in str(exc_info.value)


# ============================================================================
# Perplexity Tool Tests
# ============================================================================


class TestPerplexitySearchWrapperInput:
    """Tests for PerplexitySearchWrapperInput model."""

    def test_required_query(self, fake):
        """Test instantiation with required query."""
        query = "financial market analysis"
        model = PerplexitySearchWrapperInput(query=query)

        assert model.query == query

    def test_missing_required_query(self):
        """Test ValidationError when query is missing."""
        with pytest.raises(ValidationError) as exc_info:
            PerplexitySearchWrapperInput()
        assert "query" in str(exc_info.value)


# ============================================================================
# Custom Tool Tests
# ============================================================================


class TestMyCustomToolInput:
    """Tests for MyCustomToolInput model."""

    def test_required_argument(self, fake):
        """Test instantiation with required argument."""
        argument = "sample argument value"
        model = MyCustomToolInput(argument=argument)

        assert model.argument == argument

    def test_missing_required_argument(self):
        """Test ValidationError when argument is missing."""
        with pytest.raises(ValidationError) as exc_info:
            MyCustomToolInput()
        assert "argument" in str(exc_info.value)


# ============================================================================
# DeFi Metrics Tool Tests
# ============================================================================


class TestDeFiMetricsInput:
    """Tests for DeFiMetricsInput model."""

    def test_required_symbol(self, fake):
        """Test instantiation with required symbol."""
        symbol = "UNI"
        model = DeFiMetricsInput(symbol=symbol)

        assert model.symbol == symbol

    def test_default_values(self):
        """Test default values."""
        model = DeFiMetricsInput(symbol="UNI")

        assert model.include_tvl_analysis is True
        assert model.include_yield_metrics is True
        assert model.include_governance_analysis is True

    def test_boolean_fields(self):
        """Test boolean fields."""
        model = DeFiMetricsInput(
            symbol="AAVE",
            include_tvl_analysis=False,
            include_yield_metrics=False,
            include_governance_analysis=False,
        )

        assert model.include_tvl_analysis is False
        assert model.include_yield_metrics is False
        assert model.include_governance_analysis is False

    def test_missing_required_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            DeFiMetricsInput()
        assert "symbol" in str(exc_info.value)


# ============================================================================
# Backtesting Tool Tests
# ============================================================================


class TestBacktestingInput:
    """Tests for BacktestingInput model."""

    def test_required_symbol(self, fake):
        """Test instantiation with required symbol."""
        symbol = "AAPL"
        model = BacktestingInput(symbol=symbol)

        assert model.symbol == symbol

    def test_default_values(self):
        """Test default values."""
        model = BacktestingInput(symbol="AAPL")

        assert model.strategy == "sma_crossover"
        assert model.backtest_period_years == 5
        assert model.benchmark_symbol == "SPY"
        assert model.initial_capital == 100000.0
        assert model.include_regime_analysis is True
        assert model.strategy_params == {}

    def test_backtest_period_constraint(self):
        """Test backtest_period_years ge/le constraints (1-10)."""
        # Valid: 1
        model_min = BacktestingInput(symbol="AAPL", backtest_period_years=1)
        assert model_min.backtest_period_years == 1

        # Valid: 10
        model_max = BacktestingInput(symbol="AAPL", backtest_period_years=10)
        assert model_max.backtest_period_years == 10

        # Invalid: below 1
        with pytest.raises(ValidationError) as exc_info:
            BacktestingInput(symbol="AAPL", backtest_period_years=0)
        assert "backtest_period_years" in str(exc_info.value)

        # Invalid: above 10
        with pytest.raises(ValidationError) as exc_info:
            BacktestingInput(symbol="AAPL", backtest_period_years=15)
        assert "backtest_period_years" in str(exc_info.value)

    def test_initial_capital_gt_zero(self):
        """Test initial_capital must be > 0."""
        # Valid: positive
        model_valid = BacktestingInput(symbol="AAPL", initial_capital=50000.0)
        assert model_valid.initial_capital == 50000.0

        # Invalid: zero or negative
        with pytest.raises(ValidationError) as exc_info:
            BacktestingInput(symbol="AAPL", initial_capital=0.0)
        assert "initial_capital" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            BacktestingInput(symbol="AAPL", initial_capital=-1000.0)
        assert "initial_capital" in str(exc_info.value)

    def test_custom_strategy_params(self):
        """Test custom strategy_params."""
        params = {"fast_window": 20, "slow_window": 50}
        model = BacktestingInput(symbol="AAPL", strategy_params=params)

        assert model.strategy_params == params

    def test_missing_required_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestingInput()
        assert "symbol" in str(exc_info.value)


# ============================================================================
# Market Screening Tool Tests
# ============================================================================


class TestMarketScreeningInput:
    """Tests for MarketScreeningInput model."""

    def test_required_asset_type(self, fake):
        """Test instantiation with required asset_type."""
        asset_type = "stock"
        model = MarketScreeningInput(asset_type=asset_type)

        assert model.asset_type == asset_type

    def test_asset_type_literal(self):
        """Test asset_type literal constraint."""
        types = ["etf", "stock", "crypto"]
        for asset_type in types:
            model = MarketScreeningInput(asset_type=asset_type)
            assert model.asset_type == asset_type

        with pytest.raises(ValidationError) as exc_info:
            MarketScreeningInput(asset_type="invalid")
        assert "asset_type" in str(exc_info.value)

    def test_default_values(self):
        """Test default values."""
        model = MarketScreeningInput(asset_type="stock")

        assert model.screening_criteria == {}
        assert model.market_region == "global"
        assert model.max_candidates == 50
        assert model.min_a_plus_score == 0.85
        assert model.include_detailed_analysis is False

    def test_max_candidates_constraint(self):
        """Test max_candidates ge/le constraints (1-500)."""
        # Valid: 1
        model_min = MarketScreeningInput(asset_type="stock", max_candidates=1)
        assert model_min.max_candidates == 1

        # Valid: 500
        model_max = MarketScreeningInput(asset_type="stock", max_candidates=500)
        assert model_max.max_candidates == 500

        # Invalid: below 1
        with pytest.raises(ValidationError) as exc_info:
            MarketScreeningInput(asset_type="stock", max_candidates=0)
        assert "max_candidates" in str(exc_info.value)

        # Invalid: above 500
        with pytest.raises(ValidationError) as exc_info:
            MarketScreeningInput(asset_type="stock", max_candidates=1000)
        assert "max_candidates" in str(exc_info.value)

    def test_min_a_plus_score_constraint(self):
        """Test min_a_plus_score ge/le constraints (0.0-1.0)."""
        # Valid: 0.0
        model_min = MarketScreeningInput(asset_type="stock", min_a_plus_score=0.0)
        assert model_min.min_a_plus_score == 0.0

        # Valid: 1.0
        model_max = MarketScreeningInput(asset_type="stock", min_a_plus_score=1.0)
        assert model_max.min_a_plus_score == 1.0

        # Valid: 0.5
        model_mid = MarketScreeningInput(asset_type="stock", min_a_plus_score=0.5)
        assert model_mid.min_a_plus_score == 0.5

        # Invalid: below 0.0
        with pytest.raises(ValidationError) as exc_info:
            MarketScreeningInput(asset_type="stock", min_a_plus_score=-0.1)
        assert "min_a_plus_score" in str(exc_info.value)

        # Invalid: above 1.0
        with pytest.raises(ValidationError) as exc_info:
            MarketScreeningInput(asset_type="stock", min_a_plus_score=1.1)
        assert "min_a_plus_score" in str(exc_info.value)

    def test_custom_screening_criteria(self):
        """Test custom screening_criteria."""
        criteria = {"min_market_cap": 1e9, "max_pe_ratio": 30}
        model = MarketScreeningInput(asset_type="stock", screening_criteria=criteria)

        assert model.screening_criteria == criteria

    def test_missing_required_asset_type(self):
        """Test ValidationError when asset_type is missing."""
        with pytest.raises(ValidationError) as exc_info:
            MarketScreeningInput()
        assert "asset_type" in str(exc_info.value)


# ============================================================================
# Optimization Tool Tests
# ============================================================================


class TestOptimizationInput:
    """Tests for OptimizationInput model."""

    def test_required_assets(self, fake):
        """Test instantiation with required assets."""
        assets = ["AAPL", "GOOGL", "MSFT"]
        model = OptimizationInput(assets=assets)

        assert model.assets == assets

    def test_default_values(self):
        """Test default values."""
        model = OptimizationInput(assets=["AAPL"])

        assert model.expected_returns is None
        assert model.risk_tolerance == 0.5
        assert model.optimization_method == "mean_variance"
        assert model.constraints is None
        assert model.target_return is None
        assert model.max_weight == 0.4
        assert model.min_weight == 0.0

    def test_optional_expected_returns_dict(self):
        """Test optional expected_returns with dictionary."""
        returns = {"AAPL": 0.15, "GOOGL": 0.18}
        model = OptimizationInput(assets=["AAPL", "GOOGL"], expected_returns=returns)

        assert model.expected_returns == returns

    def test_optional_expected_returns_none(self):
        """Test optional expected_returns as None."""
        model = OptimizationInput(assets=["AAPL"], expected_returns=None)

        assert model.expected_returns is None

    def test_risk_tolerance_range(self, fake):
        """Test risk_tolerance value."""
        tolerance = fake.pyfloat(min_value=0.0, max_value=1.0)
        model = OptimizationInput(assets=["AAPL"], risk_tolerance=tolerance)

        assert model.risk_tolerance == tolerance

    def test_weight_constraints(self):
        """Test max_weight and min_weight constraints (0.0-1.0)."""
        # Valid: min_weight < max_weight
        model = OptimizationInput(assets=["AAPL"], min_weight=0.1, max_weight=0.5)
        assert model.min_weight == 0.1
        assert model.max_weight == 0.5

        # Valid: boundary values
        model_boundary = OptimizationInput(assets=["AAPL"], min_weight=0.0, max_weight=1.0)
        assert model_boundary.min_weight == 0.0
        assert model_boundary.max_weight == 1.0

    def test_optional_target_return(self, fake):
        """Test optional target_return."""
        target = fake.pyfloat(min_value=0.05, max_value=0.3)
        model = OptimizationInput(assets=["AAPL"], target_return=target)

        assert model.target_return == target

    def test_optional_constraints(self):
        """Test optional constraints."""
        constraints = {"sector_max": 0.3, "country_max": 0.4}
        model = OptimizationInput(assets=["AAPL"], constraints=constraints)

        assert model.constraints == constraints

    def test_missing_required_assets(self):
        """Test ValidationError when assets is missing."""
        with pytest.raises(ValidationError) as exc_info:
            OptimizationInput()
        assert "assets" in str(exc_info.value)


# ============================================================================
# Portfolio Rebalancing Tool Tests
# ============================================================================


class TestPortfolioRebalancingInput:
    """Tests for PortfolioRebalancingInput model."""

    def test_required_fields(self, fake):
        """Test instantiation with required fields."""
        holdings = [
            {"symbol": "AAPL", "shares": 100},
            {"symbol": "GOOGL", "shares": 50},
        ]
        target_weights = {"AAPL": 0.6, "GOOGL": 0.4}
        model = PortfolioRebalancingInput(holdings=holdings, target_weights=target_weights)

        assert model.holdings == holdings
        assert model.target_weights == target_weights

    def test_default_values(self):
        """Test default values."""
        holdings = [{"symbol": "AAPL", "shares": 100}]
        target_weights = {"AAPL": 1.0}
        model = PortfolioRebalancingInput(holdings=holdings, target_weights=target_weights)

        assert model.tolerance_bands is None
        assert model.available_capital == 0.0
        assert model.global_tolerance == 0.05

    def test_optional_tolerance_bands_dict(self):
        """Test optional tolerance_bands with dictionary."""
        holdings = [{"symbol": "AAPL", "shares": 100}]
        target_weights = {"AAPL": 1.0}
        bands = {"AAPL": 0.05}
        model = PortfolioRebalancingInput(holdings=holdings, target_weights=target_weights, tolerance_bands=bands)

        assert model.tolerance_bands == bands

    def test_optional_tolerance_bands_none(self):
        """Test optional tolerance_bands as None."""
        holdings = [{"symbol": "AAPL", "shares": 100}]
        target_weights = {"AAPL": 1.0}
        model = PortfolioRebalancingInput(holdings=holdings, target_weights=target_weights, tolerance_bands=None)

        assert model.tolerance_bands is None

    def test_available_capital_custom(self, fake):
        """Test custom available_capital."""
        capital = fake.pyfloat(min_value=0, max_value=100000)
        holdings = [{"symbol": "AAPL", "shares": 100}]
        target_weights = {"AAPL": 1.0}
        model = PortfolioRebalancingInput(
            holdings=holdings,
            target_weights=target_weights,
            available_capital=capital,
        )

        assert model.available_capital == capital

    def test_missing_required_holdings(self):
        """Test ValidationError when holdings is missing."""
        with pytest.raises(ValidationError) as exc_info:
            PortfolioRebalancingInput(target_weights={"AAPL": 1.0})
        assert "holdings" in str(exc_info.value)

    def test_missing_required_target_weights(self):
        """Test ValidationError when target_weights is missing."""
        with pytest.raises(ValidationError) as exc_info:
            PortfolioRebalancingInput(holdings=[{"symbol": "AAPL", "shares": 100}])
        assert "target_weights" in str(exc_info.value)


# ============================================================================
# A+ Scoring Tool Tests
# ============================================================================


class TestAPlusScoringInput:
    """Tests for APlusScoringInput model."""

    def test_required_fields(self, fake):
        """Test instantiation with required fields."""
        symbol = "AAPL"
        asset_type = "stock"
        model = APlusScoringInput(symbol=symbol, asset_type=asset_type)

        assert model.symbol == symbol
        assert model.asset_type == asset_type

    def test_asset_type_literal(self):
        """Test asset_type literal constraint."""
        types = ["etf", "stock", "crypto"]
        for asset_type in types:
            model = APlusScoringInput(symbol="AAPL", asset_type=asset_type)
            assert model.asset_type == asset_type

        with pytest.raises(ValidationError) as exc_info:
            APlusScoringInput(symbol="AAPL", asset_type="invalid")
        assert "asset_type" in str(exc_info.value)

    def test_default_values(self):
        """Test default values (empty dicts)."""
        model = APlusScoringInput(symbol="AAPL", asset_type="stock")

        assert model.fundamental_data == {}
        assert model.market_context == {}
        assert model.custom_criteria == {}

    def test_custom_fundamental_data(self):
        """Test custom fundamental_data."""
        data = {"roe": 0.25, "debt_to_equity": 0.3}
        model = APlusScoringInput(symbol="AAPL", asset_type="stock", fundamental_data=data)

        assert model.fundamental_data == data

    def test_custom_market_context(self):
        """Test custom market_context."""
        context = {"vix": 15.0, "interest_rate": 0.05}
        model = APlusScoringInput(symbol="AAPL", asset_type="stock", market_context=context)

        assert model.market_context == context

    def test_custom_criteria(self):
        """Test custom_criteria."""
        criteria = {"quality": 0.3, "momentum": 0.2}
        model = APlusScoringInput(symbol="AAPL", asset_type="stock", custom_criteria=criteria)

        assert model.custom_criteria == criteria

    def test_missing_required_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            APlusScoringInput(asset_type="stock")
        assert "symbol" in str(exc_info.value)

    def test_missing_required_asset_type(self):
        """Test ValidationError when asset_type is missing."""
        with pytest.raises(ValidationError) as exc_info:
            APlusScoringInput(symbol="AAPL")
        assert "asset_type" in str(exc_info.value)


class TestAPlusScore:
    """Tests for APlusScore model."""

    def test_required_fields(self, fake):
        """Test instantiation with required fields."""
        # Note: APlusScore has complex nested fields, testing minimal required
        score = APlusScore(
            symbol="AAPL",
            asset_type="stock",
            composite_score=0.85,
            grade_info={},
            fundamental_score=0.8,
            technical_score=0.85,
            quality_score=0.9,
            risk_score=0.7,
            market_regime=MarketRegime(),
            scoring_criteria=ScoringCriteria(),
            analysis_timestamp=None,
        )

        assert score.symbol == "AAPL"
        assert score.asset_type == "stock"

    def test_score_constraints(self):
        """Test score constraints (0.0-1.0)."""
        with pytest.raises(ValidationError) as exc_info:
            APlusScore(
                symbol="AAPL",
                asset_type="stock",
                composite_score=1.5,  # Invalid: > 1.0
                grade_info={},
                fundamental_score=0.8,
                technical_score=0.85,
                quality_score=0.9,
                risk_score=0.7,
                market_regime=MarketRegime(),
                scoring_criteria=ScoringCriteria(),
                analysis_timestamp=None,
            )
        assert "composite_score" in str(exc_info.value)

    def test_asset_type_literal(self):
        """Test asset_type literal constraint."""
        score = APlusScore(
            symbol="BTC",
            asset_type="crypto",
            composite_score=0.75,
            grade_info={},
            fundamental_score=0.7,
            technical_score=0.8,
            quality_score=0.7,
            risk_score=0.75,
            market_regime=MarketRegime(),
            scoring_criteria=ScoringCriteria(),
            analysis_timestamp=None,
        )

        assert score.asset_type == "crypto"


# ============================================================================
# Regulatory Compliance Tool Tests
# ============================================================================


class TestRegulatoryComplianceInput:
    """Tests for RegulatoryComplianceInput model."""

    def test_required_symbol(self, fake):
        """Test instantiation with required symbol."""
        symbol = "BTC"
        model = RegulatoryComplianceInput(symbol=symbol)

        assert model.symbol == symbol

    def test_default_jurisdictions(self):
        """Test default jurisdictions list."""
        model = RegulatoryComplianceInput(symbol="BTC")

        assert model.jurisdictions == ["US", "EU", "Switzerland", "UK", "Singapore"]

    def test_custom_jurisdictions(self):
        """Test custom jurisdictions."""
        jurisdictions = ["US", "Japan"]
        model = RegulatoryComplianceInput(symbol="BTC", jurisdictions=jurisdictions)

        assert model.jurisdictions == jurisdictions

    def test_default_boolean_fields(self):
        """Test default boolean fields."""
        model = RegulatoryComplianceInput(symbol="BTC")

        assert model.include_risk_assessment is True
        assert model.include_compliance_status is True

    def test_custom_boolean_fields(self):
        """Test custom boolean fields."""
        model = RegulatoryComplianceInput(
            symbol="BTC",
            include_risk_assessment=False,
            include_compliance_status=False,
        )

        assert model.include_risk_assessment is False
        assert model.include_compliance_status is False

    def test_missing_required_symbol(self):
        """Test ValidationError when symbol is missing."""
        with pytest.raises(ValidationError) as exc_info:
            RegulatoryComplianceInput()
        assert "symbol" in str(exc_info.value)


# ============================================================================
# Feedback Integration Tool Tests
# ============================================================================


class TestFeedbackCollectionInput:
    """Tests for FeedbackCollectionInput model."""

    def test_required_fields(self, fake):
        """Test instantiation with required fields."""
        user_id = fake.uuid4()
        recommendation_id = fake.uuid4()
        symbol = "AAPL"
        asset_type = "stock"
        outcome = "accepted"
        sentiment = "positive"
        confidence_rating = 4

        model = FeedbackCollectionInput(
            user_id=user_id,
            recommendation_id=recommendation_id,
            symbol=symbol,
            asset_type=asset_type,
            outcome=outcome,
            sentiment=sentiment,
            confidence_rating=confidence_rating,
        )

        assert model.user_id == user_id
        assert model.recommendation_id == recommendation_id
        assert model.symbol == symbol

    def test_default_values(self):
        """Test default values."""
        model = FeedbackCollectionInput(
            user_id="user123",
            recommendation_id="rec456",
            symbol="AAPL",
            asset_type="stock",
            outcome="accepted",
            sentiment="positive",
            confidence_rating=4,
        )

        assert model.reasons == []
        assert model.user_comments == ""

    def test_confidence_rating_constraint(self):
        """Test confidence_rating ge/le constraints (1-5)."""
        # Valid: 1
        model_min = FeedbackCollectionInput(
            user_id="user123",
            recommendation_id="rec456",
            symbol="AAPL",
            asset_type="stock",
            outcome="accepted",
            sentiment="positive",
            confidence_rating=1,
        )
        assert model_min.confidence_rating == 1

        # Valid: 5
        model_max = FeedbackCollectionInput(
            user_id="user123",
            recommendation_id="rec456",
            symbol="AAPL",
            asset_type="stock",
            outcome="accepted",
            sentiment="positive",
            confidence_rating=5,
        )
        assert model_max.confidence_rating == 5

        # Invalid: below 1
        with pytest.raises(ValidationError) as exc_info:
            FeedbackCollectionInput(
                user_id="user123",
                recommendation_id="rec456",
                symbol="AAPL",
                asset_type="stock",
                outcome="accepted",
                sentiment="positive",
                confidence_rating=0,
            )
        assert "confidence_rating" in str(exc_info.value)

        # Invalid: above 5
        with pytest.raises(ValidationError) as exc_info:
            FeedbackCollectionInput(
                user_id="user123",
                recommendation_id="rec456",
                symbol="AAPL",
                asset_type="stock",
                outcome="accepted",
                sentiment="positive",
                confidence_rating=6,
            )
        assert "confidence_rating" in str(exc_info.value)

    def test_custom_reasons(self):
        """Test custom reasons list."""
        reasons = ["strong_fundamentals", "technical_breakout"]
        model = FeedbackCollectionInput(
            user_id="user123",
            recommendation_id="rec456",
            symbol="AAPL",
            asset_type="stock",
            outcome="accepted",
            sentiment="positive",
            confidence_rating=4,
            reasons=reasons,
        )

        assert model.reasons == reasons

    def test_missing_required_fields(self):
        """Test ValidationError when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            FeedbackCollectionInput(
                user_id="user123",
                recommendation_id="rec456",
                symbol="AAPL",
            )
        # Should fail due to missing required fields


class TestPerformanceTrackingInput:
    """Tests for PerformanceTrackingInput model."""

    def test_required_fields(self, fake):
        """Test instantiation with required fields."""
        recommendation_id = fake.uuid4()
        symbol = "AAPL"
        holding_period_days = 30
        absolute_return = 10.5
        benchmark_return = 5.2
        current_grade = "A"
        grade_maintained = True

        model = PerformanceTrackingInput(
            recommendation_id=recommendation_id,
            symbol=symbol,
            holding_period_days=holding_period_days,
            absolute_return=absolute_return,
            benchmark_return=benchmark_return,
            current_grade=current_grade,
            grade_maintained=grade_maintained,
        )

        assert model.recommendation_id == recommendation_id
        assert model.symbol == symbol
        assert model.holding_period_days == holding_period_days

    def test_holding_period_constraint(self):
        """Test holding_period_days ge constraint (>=1)."""
        # Valid: 1
        model_min = PerformanceTrackingInput(
            recommendation_id="rec123",
            symbol="AAPL",
            holding_period_days=1,
            absolute_return=5.0,
            benchmark_return=2.0,
            current_grade="A",
            grade_maintained=True,
        )
        assert model_min.holding_period_days == 1

        # Invalid: 0
        with pytest.raises(ValidationError) as exc_info:
            PerformanceTrackingInput(
                recommendation_id="rec123",
                symbol="AAPL",
                holding_period_days=0,
                absolute_return=5.0,
                benchmark_return=2.0,
                current_grade="A",
                grade_maintained=True,
            )
        assert "holding_period_days" in str(exc_info.value)


class TestCriteriaOptimizationInput:
    """Tests for CriteriaOptimizationInput model."""

    def test_required_current_criteria(self, fake):
        """Test instantiation with required current_criteria."""
        criteria = {"min_roe": 0.20, "max_debt": 0.3}
        model = CriteriaOptimizationInput(current_criteria=criteria)

        assert model.current_criteria == criteria

    def test_default_values(self):
        """Test default values."""
        criteria = {"min_roe": 0.20}
        model = CriteriaOptimizationInput(current_criteria=criteria)

        assert model.analysis_period_days == 90
        assert model.force_adjustment is False

    def test_custom_analysis_period(self, fake):
        """Test custom analysis_period_days."""
        period = fake.random_int(min=1, max=365)
        criteria = {"min_roe": 0.20}
        model = CriteriaOptimizationInput(current_criteria=criteria, analysis_period_days=period)

        assert model.analysis_period_days == period

    def test_force_adjustment_boolean(self):
        """Test force_adjustment boolean field."""
        criteria = {"min_roe": 0.20}

        model_true = CriteriaOptimizationInput(current_criteria=criteria, force_adjustment=True)
        assert model_true.force_adjustment is True

        model_false = CriteriaOptimizationInput(current_criteria=criteria, force_adjustment=False)
        assert model_false.force_adjustment is False

    def test_missing_required_current_criteria(self):
        """Test ValidationError when current_criteria is missing."""
        with pytest.raises(ValidationError) as exc_info:
            CriteriaOptimizationInput()
        assert "current_criteria" in str(exc_info.value)


# ============================================================================
# Additional Integration Tests
# ============================================================================


class TestToolInputsIntegration:
    """Integration tests for multiple tool inputs."""

    def test_create_multiple_inputs(self, fake):
        """Test creating multiple tool inputs in sequence."""
        inputs = [
            CoinInfoInput(symbol="BTC"),
            ChartImgInput(symbol="AAPL"),
            GetTickerHistoryInput(ticker="MSFT"),
            RiskAssessmentInput(assets=["AAPL", "GOOGL"]),
            BacktestingInput(symbol="SPY"),
        ]

        assert len(inputs) == 5
        assert all(hasattr(inp, "__class__") for inp in inputs)

    def test_validation_error_messages(self):
        """Test that validation errors have informative messages."""
        with pytest.raises(ValidationError) as exc_info:
            StandardizedSentimentInput(symbol="AAPL", asset_class="stock", max_articles=200)
        error_msg = str(exc_info.value)
        assert "max_articles" in error_msg

    def test_constraint_boundaries(self):
        """Test models at constraint boundaries."""
        # Test lower boundary
        model_min = BacktestingInput(symbol="AAPL", backtest_period_years=1)
        assert model_min.backtest_period_years == 1

        # Test upper boundary
        model_max = BacktestingInput(symbol="AAPL", backtest_period_years=10)
        assert model_max.backtest_period_years == 10

        # Test middle value
        model_mid = BacktestingInput(symbol="AAPL", backtest_period_years=5)
        assert model_mid.backtest_period_years == 5

    def test_optional_vs_required_fields(self):
        """Test distinguishing optional vs required fields."""
        # Optional symbol in CryptocurrencyNewsInput
        model_with_none = CryptocurrencyNewsInput(symbol=None)
        assert model_with_none.symbol is None

        # Required symbol in CoinInfoInput
        with pytest.raises(ValidationError):
            CoinInfoInput(symbol=None)
