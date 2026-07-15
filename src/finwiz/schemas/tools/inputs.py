"""
Tool input schemas for FinWiz tools.

This module contains Pydantic models for validating inputs to various FinWiz tools.
All tool input schemas should be defined here for consistency and maintainability.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


# CoinMarketCap Tool Inputs
class CoinInfoInput(BaseModel):
    """Input schema for CoinMarketCapInfoTool."""

    symbol: str = Field(..., description="Cryptocurrency symbol/ticker (e.g., BTC, ETH, SOL)")


class CryptocurrencyListInput(BaseModel):
    """Input schema for CoinMarketCapListTool."""

    limit: int = Field(25, description="Number of cryptocurrencies to return (default: 25, max: 100)")
    sort: str = Field(
        "market_cap",
        description="Sort cryptocurrencies by: 'market_cap', 'volume_24h', 'price', or 'percent_change_24h'",
    )


class CryptocurrencyHistoricalInput(BaseModel):
    """Input schema for CoinMarketCapHistoricalTool."""

    symbol: str = Field(..., description="Cryptocurrency symbol/ticker (e.g., BTC, ETH, SOL)")
    time_period: str = Field(
        "30d",
        description="Time period for historical data: '24h', '7d', '30d', '3m', '1y', or 'ytd'",
    )


class CryptocurrencyNewsInput(BaseModel):
    """Input schema for CoinMarketCapNewsTool."""

    symbol: str | None = Field(None, description="Cryptocurrency symbol to get news for (optional)")
    limit: int = Field(10, description="Number of news articles to return (default: 10, max: 100)")


# Alpha Vantage Tool Inputs
class CompanyOverviewInput(BaseModel):
    """Input schema for the AlphaVantageCompanyOverviewTool."""

    ticker: str = Field(..., description="The stock ticker symbol to get information for.")
    include_perplexity: bool = Field(default=True, description="Whether to include Perplexity Sonar insights")


class TwelveDataIndicatorInput(BaseModel):
    """Input schema for Twelve Data indicator tool."""

    symbol: str = Field(..., description="Ticker symbol, e.g., AAPL, BTC/USD, SPY")
    interval: str = Field("1day", description="Interval, e.g., 1min, 5min, 1h, 1day")
    indicator: Literal["rsi", "macd", "bbands"] = Field(..., description="Indicator to fetch from Twelve Data")
    length: int | None = Field(None, description="Window length for indicators like RSI/BBANDS")
    fast_period: int | None = Field(None, description="Fast period for MACD")
    slow_period: int | None = Field(None, description="Slow period for MACD")
    signal_period: int | None = Field(None, description="Signal period for MACD")
    outputsize: int | None = Field(100, description="Number of data points to return (max depends on plan)")


class TwelveDataMultiIndicatorInput(BaseModel):
    """Input schema for fetching multiple technical indicators in one call."""

    symbol: str = Field(..., description="Ticker symbol, e.g., AAPL, BTC/USD, SPY")
    interval: str = Field("1day", description="Interval, e.g., 1min, 5min, 1h, 1day")
    indicators: list[Literal["rsi", "macd", "bbands"]] = Field(..., description="List of indicators to fetch (e.g., ['rsi', 'macd', 'bbands'])")
    rsi_period: int = Field(14, description="Period for RSI calculation")
    macd_fast: int = Field(12, description="Fast period for MACD")
    macd_slow: int = Field(26, description="Slow period for MACD")
    macd_signal: int = Field(9, description="Signal period for MACD")
    bbands_period: int = Field(20, description="Period for Bollinger Bands")
    bbands_stddev: int = Field(2, description="Standard deviation for Bollinger Bands")
    outputsize: int = Field(100, description="Number of data points to return (max depends on plan)")


# Sentiment Analysis Tool Inputs
class StandardizedSentimentInput(BaseModel):
    """Input schema for Standardized Sentiment Analysis Tool."""

    symbol: str = Field(..., description="The asset symbol (stock ticker, ETF, or crypto)")
    asset_class: Literal["stock", "etf", "crypto"] = Field(..., description="Type of asset being analyzed")
    max_articles: int = Field(default=50, ge=10, le=100, description="Maximum number of articles to analyze")
    days_back: int = Field(default=30, ge=7, le=90, description="Number of days to look back for news")
    include_trending: bool = Field(default=True, description="Whether to extract trending topics")


# Crypto Analysis Tool Inputs
class EnhancedCryptoAnalysisInput(BaseModel):
    """Input schema for Enhanced Crypto Analysis Tool."""

    symbol: str = Field(..., description="The crypto symbol, e.g., BTC, ETH")
    include_thesis: bool = Field(default=True, description="Whether to generate investment thesis")
    include_risk_assessment: bool = Field(default=True, description="Whether to perform risk assessment")
    max_thesis_bullets: int = Field(default=10, ge=3, le=20, description="Maximum number of thesis bullets")
    include_perplexity: bool = Field(default=True, description="Whether to include Perplexity Sonar insights")


# ETF Analysis Tool Inputs
class EnhancedETFAnalysisInput(BaseModel):
    """Input schema for Enhanced ETF Analysis Tool."""

    ticker: str = Field(..., description="The ETF ticker symbol, e.g., SPY, VTI")
    include_holdings: bool = Field(default=True, description="Whether to extract top holdings")
    include_risk_assessment: bool = Field(default=True, description="Whether to perform risk assessment")
    max_holdings: int = Field(default=10, ge=1, le=50, description="Maximum number of holdings to extract")
    include_perplexity: bool = Field(default=True, description="Whether to include Perplexity Sonar insights")


# SEC Analysis Tool Inputs
class EnhancedSECAnalysisInput(BaseModel):
    """Input schema for Enhanced SEC Analysis Tool."""

    ticker: str = Field(..., description="The stock ticker symbol, e.g., AAPL")
    form_type: Literal["10-K", "10-Q"] = Field(default="10-K", description="SEC form type to analyze")
    sections: list[Literal["Item 1", "Item 1A", "Item 7", "Item 7A", "Item 8"]] = Field(
        default=["Item 1", "Item 1A", "Item 7"], description="SEC sections to extract insights from"
    )
    risk_assessment: bool = Field(default=True, description="Whether to perform standardized risk assessment")
    include_perplexity: bool = Field(default=True, description="Whether to include Perplexity Sonar insights")


# Yahoo Finance Tool Inputs
class GetTickerHistoryInput(BaseModel):
    """Input schema for getting ticker price history."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'VTI', 'BTC-USD')")
    period: str = Field("1y", description="Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max")
    interval: str = Field(
        "1d",
        description="Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo",
    )


class GetETFHoldingsInput(BaseModel):
    """Input schema for getting ETF holdings."""

    ticker: str = Field(..., description="The ETF ticker symbol (e.g., 'VTI', 'SPY').")


class GetCompanyInfoInput(BaseModel):
    """Input schema for getting company information."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'MSFT').")


class GetTickerInfoInput(BaseModel):
    """Input schema for getting ticker information."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'VTI', 'BTC-USD')")


class GetTickerNewsInput(BaseModel):
    """Input schema for getting news for a ticker."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'BTC-USD').")
    limit: int = Field(5, description="Maximum number of news items to return.")


class PortfolioAnalysisInput(BaseModel):
    """Input model for portfolio analysis tool."""

    holdings: list[dict[str, Any]] = Field(..., description="List of portfolio holdings with symbol, shares, and optional cost_basis")
    benchmark: str = Field(default="SPY", description="Benchmark symbol for comparison")
    analysis_period: str = Field(default="1y", description="Analysis period (1y, 2y, 5y)")
    include_risk_metrics: bool = Field(default=True, description="Include risk analysis")
    include_diversification: bool = Field(default=True, description="Include diversification analysis")


# Risk Assessment Tool Inputs
class RiskAssessmentInput(BaseModel):
    """Input model for risk assessment tool."""

    assets: list[str] = Field(..., description="List of asset symbols to assess")
    portfolio_weights: dict[str, float] | None = Field(None, description="Portfolio weights for each asset (if assessing portfolio risk)")
    assessment_type: str = Field(default="comprehensive", description="Type of assessment: 'individual', 'portfolio', or 'comprehensive'")
    risk_horizon: str = Field(default="1y", description="Risk assessment horizon (1m, 3m, 6m, 1y, 2y)")
    confidence_level: float = Field(default=0.95, description="Confidence level for VaR calculations")
    include_stress_testing: bool = Field(default=True, description="Include stress testing scenarios")
    market_regime: str = Field(default="normal", description="Market regime: 'bull', 'bear', 'normal', 'volatile'")


# Quantitative Analysis Tool Inputs
class QuantitativeAnalysisInput(BaseModel):
    """Input schema for quantitative analysis tool."""

    symbol: str = Field(..., description="Symbol to analyze (e.g., AAPL, SPY, BTC-USD)")
    asset_class: str = Field(..., description="Asset class: 'stock', 'etf', or 'crypto'")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis: 'technical', 'backtest', 'performance', or 'comprehensive'")
    timeframe: str = Field(default="1y", description="Analysis timeframe (e.g., '1y', '2y', '5y')")
    strategy: str = Field(default="sma_crossover", description="Strategy for backtesting")


# Perplexity Tool Inputs
class PerplexitySearchWrapperInput(BaseModel):
    """Input schema for PerplexitySearchWrapper."""

    query: str = Field(..., description="Search query for financial research")


# Custom Tool Inputs
class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""

    argument: str = Field(..., description="Description of the argument.")


# Backtesting Tool Inputs
class BacktestingInput(BaseModel):
    """Input schema for backtesting tool."""

    symbol: str = Field(..., description="Symbol to backtest (e.g., AAPL, SPY, BTC-USD)")
    strategy: str = Field(default="sma_crossover", description="Strategy to backtest: 'sma_crossover', 'buy_and_hold', 'momentum'")
    backtest_period_years: int = Field(default=5, ge=1, le=10, description="Backtesting period in years (1-10)")
    benchmark_symbol: str = Field(default="SPY", description="Benchmark symbol for comparison")
    initial_capital: float = Field(default=100000.0, gt=0, description="Initial capital for backtesting")
    include_regime_analysis: bool = Field(default=True, description="Include multi-regime analysis (bull, bear, sideways)")
    strategy_params: dict[str, Any] = Field(default_factory=dict, description="Custom strategy parameters")


# Market Screening Tool Inputs
class MarketScreeningInput(BaseModel):
    """Input schema for Market Screening Tool."""

    asset_type: Literal["etf", "stock", "crypto"] = Field(..., description="Type of assets to screen")
    screening_criteria: dict[str, Any] = Field(default_factory=dict, description="Custom screening criteria (overrides defaults)")
    market_region: str = Field(default="global", description="Market region to screen (global, us, eu, etc.)")
    max_candidates: int = Field(default=50, ge=1, le=500, description="Maximum number of candidates to return")
    min_a_plus_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Minimum A+ score threshold")
    include_detailed_analysis: bool = Field(default=False, description="Whether to include detailed A+ analysis for each candidate")


class MarketScreeningResult(BaseModel):
    """Result from market screening operation."""

    asset_type: Literal["etf", "stock", "crypto"]
    screening_criteria: dict[str, Any]
    market_region: str
    total_screened: int
    candidates_found: int
    a_plus_candidates: int
    candidates: list[Any]  # Will be ScreeningCandidate when imported


# Optimization Tool Inputs
class OptimizationInput(BaseModel):
    """Input model for portfolio optimization tool."""

    assets: list[str] = Field(..., description="List of asset symbols to optimize")
    expected_returns: dict[str, float] | None = Field(None, description="Expected returns for each asset (optional)")
    risk_tolerance: float = Field(default=0.5, description="Risk tolerance (0.0 = risk averse, 1.0 = risk seeking)")
    optimization_method: str = Field(default="mean_variance", description="Optimization method: 'mean_variance', 'risk_parity', 'equal_weight'")
    constraints: dict[str, Any] | None = Field(None, description="Additional constraints")
    target_return: float | None = Field(None, description="Target return for optimization")
    max_weight: float = Field(default=0.4, ge=0.0, le=1.0, description="Maximum weight per asset (0.0-1.0)")
    min_weight: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum weight per asset (0.0-1.0)")


# Portfolio Rebalancing Tool Inputs
class PortfolioRebalancingInput(BaseModel):
    """Input model for portfolio rebalancing tool."""

    holdings: list[dict[str, Any]] = Field(..., description="List of portfolio holdings with symbol and shares")
    target_weights: dict[str, float] = Field(..., description="Target percentage weights for each symbol")
    tolerance_bands: dict[str, float] | None = Field(default=None, description="Tolerance bands for each position")
    available_capital: float = Field(default=0.0, description="Available capital for rebalancing")
    global_tolerance: float = Field(default=0.05, description="Default tolerance band (5% = ±5%)")


# A+ Scoring Tool Inputs
class APlusScoringInput(BaseModel):
    """Input schema for A+ Investment Scoring Tool."""

    symbol: str = Field(..., description="Investment symbol (e.g., AAPL, SPY, BTC-USD)")
    asset_type: Literal["etf", "stock", "crypto"] = Field(..., description="Type of asset to score")
    fundamental_data: dict[str, Any] = Field(default_factory=dict, description="Fundamental data for the investment")
    market_context: dict[str, Any] = Field(default_factory=dict, description="Current market context and conditions")
    custom_criteria: dict[str, float] = Field(default_factory=dict, description="Custom scoring criteria weights")


class MarketRegime(BaseModel):
    """Current market regime assessment."""

    regime_type: Literal["bull", "bear", "sideways", "volatile"] = "sideways"
    vix_level: float = Field(default=20.0, ge=0.0, le=100.0)
    inflation_rate: float = Field(default=3.0, ge=-5.0, le=20.0)
    interest_rate_trend: Literal["rising", "falling", "stable"] = "stable"
    market_stress_level: Literal["low", "medium", "high"] = "medium"


class ScoringCriteria(BaseModel):
    """Dynamic scoring criteria that adapt to market conditions."""

    # ETF Criteria
    etf_max_expense_ratio: float = Field(default=0.15, ge=0.0, le=2.0)
    etf_min_aum: float = Field(default=1e9, ge=1e6, le=1e12)
    etf_max_tracking_error: float = Field(default=0.002, ge=0.0, le=0.1)
    etf_min_history_years: int = Field(default=3, ge=1, le=20)

    # Stock Criteria
    stock_min_roe: float = Field(default=0.20, ge=0.0, le=1.0)
    stock_min_revenue_growth: float = Field(default=0.15, ge=-0.5, le=2.0)
    stock_max_debt_to_equity: float = Field(default=0.3, ge=0.0, le=5.0)
    stock_min_market_cap: float = Field(default=1e9, ge=1e6, le=1e13)

    # Crypto Criteria
    crypto_min_market_cap: float = Field(default=10e9, ge=1e6, le=1e13)
    crypto_min_daily_volume: float = Field(default=500e6, ge=1e6, le=1e12)
    crypto_min_age_months: int = Field(default=36, ge=1, le=200)


class APlusScore(BaseModel):
    """Comprehensive A+ score with detailed breakdown."""

    symbol: str
    asset_type: Literal["etf", "stock", "crypto"]
    composite_score: float = Field(ge=0.0, le=1.0)
    grade_info: Any  # GradeInfo type - will need proper import

    # Component scores
    fundamental_score: float = Field(ge=0.0, le=1.0)
    technical_score: float = Field(ge=0.0, le=1.0)
    quality_score: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)

    # Analysis details
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    a_plus_rationale: str = ""
    confidence_level: float = Field(default=0.5, ge=0.0, le=1.0)

    # Context
    market_regime: MarketRegime
    scoring_criteria: ScoringCriteria
    analysis_timestamp: Any  # datetime


# Feedback Integration Tool Inputs
class FeedbackCollectionInput(BaseModel):
    """Input for collecting user feedback on recommendations."""

    user_id: str = Field(..., description="User identifier")
    recommendation_id: str = Field(..., description="Recommendation ID")
    symbol: str = Field(..., description="Investment symbol")
    asset_type: str = Field(..., description="Asset type (etf, stock, crypto)")
    outcome: str = Field(..., description="User outcome (accepted, rejected, etc.)")
    sentiment: str = Field(..., description="User sentiment (positive, negative, etc.)")
    confidence_rating: int = Field(..., ge=1, le=5, description="User confidence (1-5)")
    reasons: list[str] = Field(default_factory=list, description="Reasons for decision")
    user_comments: str = Field(default="", description="Optional user comments")


class PerformanceTrackingInput(BaseModel):
    """Input for tracking performance of accepted recommendations."""

    recommendation_id: str = Field(..., description="Original recommendation ID")
    symbol: str = Field(..., description="Investment symbol")
    holding_period_days: int = Field(..., ge=1, description="Days since investment")
    absolute_return: float = Field(..., description="Absolute return percentage")
    benchmark_return: float = Field(..., description="Benchmark return")
    current_grade: str = Field(..., description="Current grade")
    grade_maintained: bool = Field(..., description="Whether A+ grade maintained")


class CriteriaOptimizationInput(BaseModel):
    """Input for optimizing A+ criteria based on feedback."""

    current_criteria: dict[str, Any] = Field(..., description="Current A+ criteria")
    analysis_period_days: int = Field(default=90, description="Days to analyze")
    force_adjustment: bool = Field(default=False, description="Force adjustment regardless of timing")
