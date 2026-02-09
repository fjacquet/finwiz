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
- api: FastAPI request/response models
- investment_discovery: A+ investment discovery schemas
- newcomer_discovery: newcomer discovery pipeline schemas
- portfolio_rebalancing: portfolio rebalancing and optimization schemas
- perplexity: Perplexity API integration schemas
- validation: ticker validation schemas
"""

# Core domain schemas
# Organized schema modules
from . import (
    api,  # noqa: F401
    integration,  # noqa: F401
    quantitative,  # noqa: F401
    tools,  # noqa: F401
)

# Common schemas
from .common import RiskAssessmentStandardized, RiskLevel  # noqa: F401

# Crypto crew schemas
from .crypto import (  # noqa: F401
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

# ETF crew schemas
from .etf import (  # noqa: F401
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
from .investment_discovery import (  # noqa: F401
    APlusAnalysis,
    APlusDiscoveryResult,
    InvestmentCandidate,
    OptimizationResult,
    PortfolioImprovement,
    ValidationResult,
)

# Sentiment & macro schemas (v4)
from .macro import MacroSnapshot  # noqa: F401

# Newcomer discovery schemas
from .newcomer_discovery import (  # noqa: F401
    EnrichmentResult,
    NewcomerCandidate,
    NewcomerDiscoveryResult,
)

# Perplexity integration schemas
from .perplexity import (  # noqa: F401
    PerplexityConfig,
    PerplexitySearchRequest,
    PerplexitySearchResponse,
    SonarArticle,
    SonarSearchResult,
)

# Portfolio rebalancing crew schemas
from .portfolio_rebalancing import (  # noqa: F401
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
from .portfolio_review import (  # noqa: F401
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
from .quantitative import (  # noqa: F401
    BacktestResult,
    PerformanceMetrics,
    TechnicalAnalysisResult,
)

# Report crew schemas
from .report import ReporterInput  # noqa: F401
from .sentiment import NewsArticle, NewsSentimentResult  # noqa: F401

# Stock crew schemas
from .stock import (  # noqa: F401
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
from .validation import ValidatedTicker  # noqa: F401

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
    # Sentiment & macro schemas (v4)
    "MacroSnapshot",
    "NewsArticle",
    "NewsSentimentResult",
    # Validation schemas
    "ValidatedTicker",
]
