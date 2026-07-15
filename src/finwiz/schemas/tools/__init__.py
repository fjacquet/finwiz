"""
Tool input schemas for FinWiz tools.

This module contains Pydantic models for tool inputs and configurations.
"""

from .inputs import (
    APlusScore,
    APlusScoringInput,
    BacktestingInput,
    # CoinMarketCap inputs
    CoinInfoInput,
    CompanyOverviewInput,
    CriteriaOptimizationInput,
    CryptocurrencyHistoricalInput,
    CryptocurrencyListInput,
    CryptocurrencyNewsInput,
    # Crypto analysis inputs
    EnhancedCryptoAnalysisInput,
    # ETF analysis inputs
    EnhancedETFAnalysisInput,
    # SEC analysis inputs
    EnhancedSECAnalysisInput,
    FeedbackCollectionInput,
    GetCompanyInfoInput,
    GetETFHoldingsInput,
    # Yahoo Finance inputs
    GetTickerHistoryInput,
    GetTickerInfoInput,
    GetTickerNewsInput,
    MarketRegime,
    MarketScreeningInput,
    MarketScreeningResult,
    # Other tool inputs
    MyCustomToolInput,
    OptimizationInput,
    PerformanceTrackingInput,
    PerplexitySearchWrapperInput,
    PortfolioAnalysisInput,
    PortfolioRebalancingInput,
    QuantitativeAnalysisInput,
    RiskAssessmentInput,
    ScoringCriteria,
    StandardizedSentimentInput,
    TwelveDataIndicatorInput,
    TwelveDataMultiIndicatorInput,
)

__all__ = [
    # CoinMarketCap inputs
    "CoinInfoInput",
    "CryptocurrencyListInput",
    "CryptocurrencyHistoricalInput",
    "CryptocurrencyNewsInput",
    # Alpha Vantage inputs
    "CompanyOverviewInput",
    # Technical analysis inputs
    "TwelveDataIndicatorInput",
    "TwelveDataMultiIndicatorInput",
    # Sentiment analysis inputs
    "StandardizedSentimentInput",
    # Crypto analysis inputs
    "EnhancedCryptoAnalysisInput",
    # ETF analysis inputs
    "EnhancedETFAnalysisInput",
    # SEC analysis inputs
    "EnhancedSECAnalysisInput",
    # Yahoo Finance inputs
    "GetTickerHistoryInput",
    "GetETFHoldingsInput",
    # Other tool inputs
    "MyCustomToolInput",
    "BacktestingInput",
    "MarketScreeningInput",
    "MarketScreeningResult",
    "OptimizationInput",
    "PortfolioRebalancingInput",
    "APlusScoringInput",
    "MarketRegime",
    "ScoringCriteria",
    "APlusScore",
    "FeedbackCollectionInput",
    "PerformanceTrackingInput",
    "CriteriaOptimizationInput",
    "GetCompanyInfoInput",
    "GetTickerInfoInput",
    "GetTickerNewsInput",
    "PortfolioAnalysisInput",
    "RiskAssessmentInput",
    "QuantitativeAnalysisInput",
    "PerplexitySearchWrapperInput",
]
