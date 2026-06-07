"""
Typed data contracts for FinWiz inter-agent communication and reporter inputs.

Modules:
- common: shared enums and standardized risk model
- stock: Ten-K insights and market sentiment models
- crypto: cryptocurrency analysis models
- etf: ETF analysis models
- report: aggregate input for the final tool-less reporter
- quantitative: quantitative analysis and backtesting models
- integration: system integration and validation models
- tools: tool input validation schemas
- investment_discovery: A+ investment discovery schemas
- newcomer_discovery: newcomer discovery pipeline schemas
- portfolio_rebalancing: portfolio rebalancing and optimization schemas
- perplexity: Perplexity API integration schemas
- validation: ticker validation schemas
"""

# Core domain schemas
# Organized schema modules
from . import (
    integration,  # noqa: F401
    quantitative,  # noqa: F401
    tools,  # noqa: F401
)

# Common schemas
from .common import RiskAssessmentStandardized, RiskLevel

# Crypto crew schemas
from .crypto import (
    CryptoCandidate,
    CryptoInvestmentStrategy,
    CryptoMarketAnalysis,
    CryptoQuantitativeMetrics,
    CryptoRisk,
    CryptoRiskProfile,
    CryptoTechnicalAnalysis,
    CryptoTechnicalIndicators,
    CryptoThesis,
)

# Economic calendar schemas (v4 Phase 16)
from .economic_calendar import EarningsEvent, EconomicCalendar, EconomicEvent

# ETF crew schemas
from .etf import (
    ETFCandidate,
    ETFFactsheet,
    ETFMarketTrend,
    ETFQuantitativeMetrics,
    ETFRiskProfile,
    ETFScreeningResult,
    ETFTechnicalAnalysis,
    ETFTechnicalIndicators,
    ETFTopHolding,
)

# Investment discovery crew schemas
from .investment_discovery import (
    APlusAnalysis,
    APlusDiscoveryResult,
    InvestmentCandidate,
    OptimizationResult,
    PortfolioImprovement,
    ValidationResult,
)

# Sentiment & macro schemas (v4)
from .macro import MacroScore, MacroSnapshot, YieldCurveRegime

# Newcomer discovery schemas
from .newcomer_discovery import (
    EnrichmentResult,
    NewcomerCandidate,
    NewcomerDiscoveryResult,
)

# Perplexity integration schemas
from .perplexity import (
    PerplexityConfig,
    PerplexitySearchRequest,
    PerplexitySearchResponse,
    SonarArticle,
    SonarSearchResult,
)

# Portfolio rebalancing crew schemas
from .portfolio_rebalancing import (
    AlternativeScenario,
    CostAnalysis,
    ExecutionSummary,
    Holding,
    PortfolioAnalysis,
    PortfolioConfiguration,
    PortfolioMetrics,
    PriceData,
    RebalancingMethod,
    RebalancingNeed,
    RebalancingRecommendation,
    RebalancingResult,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)

# Portfolio review schemas
from .portfolio_review import (
    Alternative,
    APlusImprovementSuggestion,
    APlusOpportunitySection,
    AssetClass,
    Decision,
    Grade,
    HoldingDecision,
    ImprovementType,
    PortfolioReview,
    PositionSizeRecommendation,
    PriceTargets,
    Priority,
)

# Quantitative analysis schemas
from .quantitative import (
    BacktestResult,
    PerformanceMetrics,
    TechnicalAnalysisResult,
)

# Report crew schemas
from .report import ReporterInput
from .sentiment import NewsArticle, NewsSentimentResult

# Stock crew schemas
from .stock import (
    MarketSentiment,
    MarketTrend,
    QuantitativeMetrics,
    SentimentItem,
    StockCandidate,
    StockRiskProfile,
    StockScreeningResult,
    StockTechnicalAnalysis,
    TechnicalIndicators,
    TenKInsight,
)

# Validation schemas
from .validation import ValidatedTicker

# Explicit exports for better IDE support and documentation
__all__ = [
    # Common schemas
    "RiskAssessmentStandardized",
    "RiskLevel",
    # Crypto crew schemas
    "CryptoCandidate",
    "CryptoInvestmentStrategy",
    "CryptoMarketAnalysis",
    "CryptoQuantitativeMetrics",
    "CryptoRisk",
    "CryptoRiskProfile",
    "CryptoTechnicalAnalysis",
    "CryptoTechnicalIndicators",
    "CryptoThesis",
    # ETF crew schemas
    "ETFCandidate",
    "ETFFactsheet",
    "ETFMarketTrend",
    "ETFQuantitativeMetrics",
    "ETFRiskProfile",
    "ETFScreeningResult",
    "ETFTechnicalAnalysis",
    "ETFTechnicalIndicators",
    "ETFTopHolding",
    # Investment discovery crew schemas
    "APlusAnalysis",
    "APlusDiscoveryResult",
    "InvestmentCandidate",
    "OptimizationResult",
    "PortfolioImprovement",
    "ValidationResult",
    # Newcomer discovery schemas
    "EnrichmentResult",
    "NewcomerCandidate",
    "NewcomerDiscoveryResult",
    # Perplexity integration schemas
    "PerplexityConfig",
    "PerplexitySearchRequest",
    "PerplexitySearchResponse",
    "SonarArticle",
    "SonarSearchResult",
    # Portfolio rebalancing crew schemas
    "AlternativeScenario",
    "CostAnalysis",
    "ExecutionSummary",
    "Holding",
    "PortfolioAnalysis",
    "PortfolioConfiguration",
    "PortfolioMetrics",
    "PriceData",
    "RebalancingMethod",
    "RebalancingNeed",
    "RebalancingRecommendation",
    "RebalancingResult",
    "TradeAction",
    "TradeRecommendation",
    "UrgencyLevel",
    # Portfolio review schemas
    "Alternative",
    "APlusImprovementSuggestion",
    "APlusOpportunitySection",
    "AssetClass",
    "Decision",
    "Grade",
    "HoldingDecision",
    "ImprovementType",
    "PortfolioReview",
    "PositionSizeRecommendation",
    "PriceTargets",
    "Priority",
    # Quantitative analysis schemas
    "BacktestResult",
    "PerformanceMetrics",
    "TechnicalAnalysisResult",
    # Report crew schemas
    "ReporterInput",
    # Stock crew schemas
    "MarketSentiment",
    "MarketTrend",
    "QuantitativeMetrics",
    "SentimentItem",
    "StockCandidate",
    "StockRiskProfile",
    "StockScreeningResult",
    "StockTechnicalAnalysis",
    "TechnicalIndicators",
    "TenKInsight",
    # Economic calendar schemas (v4 Phase 16)
    "EarningsEvent",
    "EconomicCalendar",
    "EconomicEvent",
    # Sentiment & macro schemas (v4)
    "MacroScore",
    "MacroSnapshot",
    "NewsArticle",
    "NewsSentimentResult",
    "YieldCurveRegime",
    # Validation schemas
    "ValidatedTicker",
]
