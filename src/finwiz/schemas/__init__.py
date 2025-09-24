"""
Typed data contracts for FinWiz inter-agent communication and reporter inputs.

Modules:
- common: shared enums and standardized risk model
- stock: Ten-K insights and market sentiment models
- report: aggregate input for the final tool-less reporter
"""

from .common import RiskAssessmentStandardized, RiskLevel  # noqa: F401
from .crypto import CryptoRisk, CryptoThesis  # noqa: F401
from .etf import ETFFactsheet, ETFTopHolding  # noqa: F401
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
    EnhancedCryptoAnalysis,
    EnhancedETFAnalysis,
    EnhancedStockAnalysis,
    QuantitativeBacktestResult,
    QuantitativePerformanceMetrics,
    QuantitativeRecommendation,
    QuantitativeTechnicalAnalysis,
)
from .report import ReporterInput  # noqa: F401
from .session import AnalysisRecord, ClientProfile, FinancialPlan, SessionMetadata  # noqa: F401
from .stock import MarketSentiment, SentimentItem, TenKInsight  # noqa: F401
from .validation import ValidatedTicker  # noqa: F401
