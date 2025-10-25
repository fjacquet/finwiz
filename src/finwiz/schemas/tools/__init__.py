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
    CryptoRiskScoringInput,
    CryptoThesisInput,
    DeFiMetricsInput,
    # Crypto analysis inputs
    EnhancedCryptoAnalysisInput,
    # ETF analysis inputs
    EnhancedETFAnalysisInput,
    # SEC analysis inputs
    EnhancedSECAnalysisInput,
    # Sentiment analysis inputs
    EnhancedSentimentInput,
    # Technical analysis inputs
    EnhancedTechnicalAnalysisInput,
    ETFTrackingAnalysisInput,
    FeedbackCollectionInput,
    GetCompanyInfoInput,
    GetETFHoldingsInput,
    # Yahoo Finance inputs
    GetTickerHistoryInput,
    GetTickerInfoInput,
    GetTickerNewsInput,
    KnowledgeBaseInput,
    MarketRegime,
    MarketScreeningInput,
    MarketScreeningResult,
    # Other tool inputs
    MyCustomToolInput,
    OptimizationInput,
    PerformanceTrackingInput,
    PerplexitySearchInput,
    PerplexitySearchWrapperInput,
    PortfolioAnalysisInput,
    PortfolioRebalancingInput,
    QuantitativeAnalysisInput,
    RegulatoryComplianceInput,
    RiskAssessmentInput,
    SaveToRagInput,
    ScoringCriteria,
    SECFilingSearchInput,
    StandardizedRiskScoringInput,
    StandardizedSentimentInput,
    TickerInfoInput,
    # Validation inputs
    TickerValidationInput,
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
    "EnhancedTechnicalAnalysisInput",
    "TwelveDataIndicatorInput",
    "TwelveDataMultiIndicatorInput",
    # Sentiment analysis inputs
    "EnhancedSentimentInput",
    "StandardizedSentimentInput",
    "CrossAssetSentimentComparatorInput",
    # Crypto analysis inputs
    "EnhancedCryptoAnalysisInput",
    "CryptoThesisInput",
    "CryptoRiskScoringInput",
    # ETF analysis inputs
    "EnhancedETFAnalysisInput",
    "ETFTrackingAnalysisInput",
    # SEC analysis inputs
    "EnhancedSECAnalysisInput",
    "StandardizedRiskScoringInput",
    # Yahoo Finance inputs
    "GetTickerHistoryInput",
    "GetETFHoldingsInput",
    # Validation inputs
    "TickerValidationInput",
    # Other tool inputs
    "MyCustomToolInput",
    "TickerInfoInput",
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
    "KnowledgeBaseInput",
    "SaveToRagInput",
    "RiskAssessmentInput",
    "QuantitativeAnalysisInput",
    "SECFilingSearchInput",
    "PerplexitySearchInput",
    "PerplexitySearchWrapperInput",
]
