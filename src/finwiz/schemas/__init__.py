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
"""

# Core domain schemas
# Organized schema modules
from . import (
    api,  # noqa: F401
    integration,  # noqa: F401
    quantitative,  # noqa: F401
    tools,  # noqa: F401
)
from .common import RiskAssessmentStandardized, RiskLevel  # noqa: F401
from .crypto import CryptoRisk, CryptoThesis  # noqa: F401
from .etf import ETFFactsheet, ETFTopHolding  # noqa: F401
from .investment_discovery import (  # noqa: F401
    APlusAnalysis,
    APlusDiscoveryResult,
    InvestmentCandidate,
    OptimizationResult,
    PortfolioImprovement,
    ValidationResult,
)
from .perplexity import (  # noqa: F401
    PerplexityConfig,
    PerplexitySearchRequest,
    PerplexitySearchResponse,
    SonarArticle,
    SonarSearchResult,
)
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
from .quantitative import (  # noqa: F401
    BacktestResult,
    PerformanceMetrics,
    TechnicalAnalysisResult,
)
from .report import ReporterInput  # noqa: F401
from .session import AnalysisRecord, ClientProfile, FinancialPlan, SessionMetadata  # noqa: F401
from .stock import MarketSentiment, SentimentItem, TenKInsight  # noqa: F401
from .validation import ValidatedTicker  # noqa: F401
