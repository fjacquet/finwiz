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
    CrossAssetSentimentComparatorInput,
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
    RegulatoryComplianceInput,
    RiskAssessmentInput,
    ScoringCriteria,
    StandardizedRiskScoringInput,
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
    "CrossAssetSentimentComparatorInput",
    # Crypto analysis inputs
    "EnhancedCryptoAnalysisInput",
    # ETF analysis inputs
    "EnhancedETFAnalysisInput",
    # SEC analysis inputs
    "EnhancedSECAnalysisInput",
    "StandardizedRiskScoringInput",
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
    "RegulatoryComplianceInput",
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
