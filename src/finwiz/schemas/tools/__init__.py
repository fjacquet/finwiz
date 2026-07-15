"""
Tool input schemas for FinWiz tools.

This module contains Pydantic models for tool inputs and configurations.
"""

from .inputs import (
    # Alpha Vantage inputs
    AlphaVantageNewsInput,
    APlusScore,
    APlusScoringInput,
    BacktestingInput,
    # Chart generation inputs
    ChartImgInput,
    # CoinMarketCap inputs
    CoinInfoInput,
    CompanyOverviewInput,
    CriteriaOptimizationInput,
    CrossAssetSentimentComparatorInput,
    CryptocurrencyHistoricalInput,
    CryptocurrencyListInput,
    CryptocurrencyNewsInput,
    DeFiMetricsInput,
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
    # Chart generation inputs
    "ChartImgInput",
    # Alpha Vantage inputs
    "AlphaVantageNewsInput",
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
    "DeFiMetricsInput",
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
