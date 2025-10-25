"""
Pydantic schemas for Investment Discovery Crew outputs.

This module defines the data models for A+ investment discovery results,
validation outcomes, and portfolio optimization recommendations.
"""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import RiskAssessmentStandardized
from .portfolio_review import Grade


class MarketRegime(BaseModel):
    """Current market regime assessment for A+ discovery."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    regime_type: Literal["bull", "bear", "sideways", "volatile"] = Field(..., description="Current market regime")
    vix_level: float = Field(..., ge=0.0, le=100.0, description="VIX volatility index level")
    inflation_rate: float = Field(..., ge=-5.0, le=20.0, description="Current inflation rate percentage")
    interest_rate_trend: Literal["rising", "falling", "stable"] = Field(..., description="Interest rate trend")
    market_stress_level: Literal["low", "medium", "high"] = Field(..., description="Overall market stress level")
    assessment_date: datetime = Field(default_factory=datetime.now, description="When regime was assessed")


class APlusCriteria(BaseModel):
    """Dynamic A+ scoring criteria that adapt to market conditions."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # ETF Criteria
    etf_max_expense_ratio: float = Field(
        default=0.15, ge=0.0, le=2.0, description="Maximum expense ratio (decimal, e.g., 0.15 = 15%)"
    )
    etf_min_aum: float = Field(default=1e9, ge=1e6, le=1e12, description="Minimum AUM for ETF liquidity in USD")
    etf_max_tracking_error: float = Field(
        default=0.002, ge=0.0, le=0.1, description="Maximum tracking error (decimal, e.g., 0.002 = 0.2%)"
    )
    etf_min_history_years: int = Field(default=3, ge=1, le=20, description="Minimum operating history in years")

    # Stock Criteria - Accept percentage format (0-100)
    stock_min_roe: float = Field(
        default=20.0, ge=0.0, le=100.0, description="Minimum return on equity (percentage, e.g., 20 = 20%)"
    )
    stock_min_revenue_growth: float = Field(
        default=15.0, ge=-50.0, le=200.0, description="Minimum revenue growth rate (percentage, e.g., 15 = 15%)"
    )
    stock_max_debt_to_equity: float = Field(default=0.3, ge=0.0, le=5.0, description="Maximum debt-to-equity ratio")
    stock_min_market_cap: float = Field(default=1e9, ge=1e6, le=1e13, description="Minimum market capitalization in USD")

    # Crypto Criteria
    crypto_min_market_cap: float = Field(default=10e9, ge=1e6, le=1e13, description="Minimum crypto market cap in USD")
    crypto_min_daily_volume: float = Field(default=500e6, ge=1e5, le=1e12, description="Minimum daily trading volume in USD")
    crypto_min_age_months: int = Field(default=36, ge=1, le=200, description="Minimum age in months")

    # Market regime adjustments applied
    regime_adjusted: bool = Field(default=False, description="Whether criteria were adjusted for market regime")
    adjustment_rationale: str = Field(default="", description="Explanation of any regime-based adjustments")


class InvestmentCandidate(BaseModel):
    """A candidate investment discovered through A+ screening."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Investment symbol (e.g., AAPL, SPY, BTC-USD)")
    name: str = Field(..., description="Full name of the investment")
    asset_type: Literal["etf", "stock", "crypto"] = Field(..., description="Type of asset")
    current_price: float = Field(..., gt=0, description="Current market price")
    market_cap: Optional[float] = Field(None, description="Market capitalization in USD")
    preliminary_score: float = Field(..., ge=0.0, le=1.0, description="Initial A+ score")
    final_score: float = Field(..., ge=0.0, le=1.0, description="Final A+ score after validation")
    grade: Grade = Field(..., description="Letter grade from FinWiz grading system (A+ to F)")
    grade_description: str = Field(..., description="Human-readable grade description")
    recommended_action: str = Field(..., description="Recommended action based on grade")
    discovery_date: datetime = Field(default_factory=datetime.now, description="When the candidate was discovered")
    data_source: str = Field(..., description="Primary data source used for analysis")
    risk_assessment: Optional[RiskAssessmentStandardized] = Field(None, description="Standardized risk assessment")


class APlusAnalysis(BaseModel):
    """Detailed A+ analysis for an investment candidate."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    candidate: InvestmentCandidate
    fundamental_score: float = Field(..., ge=0.0, le=1.0, description="Fundamental analysis score")
    technical_score: float = Field(..., ge=0.0, le=1.0, description="Technical analysis score")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality metrics score")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk assessment score")
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Final composite score")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence in the analysis")
    is_a_plus_candidate: bool = Field(..., description="Whether this qualifies as A+ (score >= 0.95)")
    rationale: list[str] = Field(..., description="Key reasons for A+ classification")
    key_metrics: dict[str, Any] = Field(default_factory=dict, description="Important financial metrics")
    competitive_advantages: list[str] = Field(default_factory=list, description="Competitive moats and advantages")
    risk_factors: list[str] = Field(default_factory=list, description="Key risk considerations")
    market_context: Optional[MarketRegime] = Field(None, description="Market regime during analysis")
    criteria_used: Optional[APlusCriteria] = Field(None, description="Scoring criteria applied")


class APlusDiscoveryResult(BaseModel):
    """Result from A+ investment discovery process."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    asset_type: Literal["etf", "stock", "crypto"] = Field(..., description="Type of assets analyzed")
    total_screened: int = Field(..., ge=0, description="Total number of investments screened")
    candidates_found: int = Field(..., ge=0, description="Number of A+ candidates found")
    discovery_criteria: APlusCriteria = Field(..., description="Criteria used for discovery")
    market_context: MarketRegime = Field(..., description="Market conditions during discovery")
    discovery_timestamp: datetime = Field(default_factory=datetime.now, description="When discovery was performed")

    # A+ candidates with detailed analysis
    a_plus_candidates: list[APlusAnalysis] = Field(default_factory=list, description="Detailed A+ candidate analysis")

    # Summary statistics
    average_score: float = Field(..., ge=0.0, le=1.0, description="Average score of A+ candidates")
    grade_distribution: dict[Grade, int] = Field(default_factory=dict, description="Distribution of grades found")
    a_plus_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of screened investments achieving A+")

    # UCITS compliance for ETFs (European investors)
    ucits_compliant_count: Optional[int] = Field(None, description="Number of UCITS-compliant ETFs found")
    ucits_compliant_symbols: list[str] = Field(default_factory=list, description="UCITS-compliant symbols")

    # Recommendations
    top_recommendations: list[str] = Field(default_factory=list, description="Top 3-5 symbol recommendations")
    implementation_notes: list[str] = Field(default_factory=list, description="Implementation considerations")

    # Quality metrics
    high_confidence_count: int = Field(default=0, description="Number of candidates with >80% confidence")
    screening_efficiency: float = Field(..., ge=0.0, le=100.0, description="Percentage of quality candidates found")


class ValidationResult(BaseModel):
    """Result from A+ candidate validation process."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    total_candidates: int = Field(..., ge=0, description="Total candidates validated")
    passed_validation: int = Field(..., ge=0, description="Candidates that passed validation")
    failed_validation: int = Field(..., ge=0, description="Candidates that failed validation")

    # Validation details for each candidate
    validation_details: list[dict[str, Any]] = Field(default_factory=list, description="Detailed validation results")

    # Backtesting results
    backtest_period_years: int = Field(..., ge=1, description="Years of backtesting data used")
    market_regimes_tested: list[str] = Field(default_factory=list, description="Market regimes included in testing")

    # Performance metrics
    average_sharpe_ratio: float = Field(..., description="Average Sharpe ratio of validated candidates")
    average_max_drawdown: float = Field(..., le=0.0, description="Average maximum drawdown")
    average_sortino_ratio: float = Field(..., description="Average Sortino ratio")

    # Risk metrics
    correlation_analysis: dict[str, Any] = Field(default_factory=dict, description="Correlation with existing holdings")
    stress_test_results: dict[str, Any] = Field(default_factory=dict, description="Stress testing outcomes")

    # Final recommendations
    validated_candidates: list[str] = Field(default_factory=list, description="Symbols that passed validation")
    rejected_candidates: list[dict[str, str]] = Field(default_factory=list, description="Rejected candidates with reasons")


class PortfolioImprovement(BaseModel):
    """A specific portfolio improvement recommendation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    current_holding: Optional[str] = Field(None, description="Current holding to replace (if any)")
    current_grade: Optional[Grade] = Field(None, description="Current holding grade (if replacing)")
    recommended_investment: str = Field(..., description="Recommended A+ investment symbol")
    recommended_grade: Grade = Field(..., description="Grade of recommended investment")
    improvement_type: Literal["replacement", "addition", "rebalancing"] = Field(..., description="Type of improvement")
    expected_grade_improvement: float = Field(..., description="Expected numerical improvement in portfolio grade")
    grade_improvement_description: str = Field(..., description="Human-readable description of grade improvement")
    allocation_percentage: float = Field(..., ge=0.0, le=100.0, description="Recommended allocation percentage")
    implementation_priority: Literal["high", "medium", "low"] = Field(..., description="Implementation priority")
    rationale: str = Field(..., description="Detailed rationale for the improvement")
    risk_impact: RiskAssessmentStandardized = Field(..., description="Impact on portfolio risk profile")
    cost_analysis: dict[str, float] = Field(default_factory=dict, description="Transaction costs and fees")
    expected_annual_benefit: Optional[float] = Field(None, description="Expected annual benefit in percentage points")


class OptimizationResult(BaseModel):
    """Result from portfolio optimization with A+ discoveries."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    current_portfolio_grade: Grade = Field(..., description="Current portfolio letter grade")
    optimized_portfolio_grade: Grade = Field(..., description="Projected portfolio grade after improvements")
    grade_improvement: float = Field(..., description="Numerical improvement in portfolio score")
    grade_improvement_description: str = Field(..., description="Human-readable description of improvement")

    # Specific improvements
    improvements: list[PortfolioImprovement] = Field(default_factory=list, description="Specific improvement recommendations")

    # Portfolio metrics comparison
    current_metrics: dict[str, float] = Field(default_factory=dict, description="Current portfolio metrics")
    projected_metrics: dict[str, float] = Field(default_factory=dict, description="Projected metrics after optimization")

    # Risk analysis
    risk_impact_analysis: dict[str, Any] = Field(default_factory=dict, description="Analysis of risk changes")
    diversification_impact: dict[str, Any] = Field(default_factory=dict, description="Impact on diversification")

    # Implementation plan
    implementation_timeline: dict[str, str] = Field(default_factory=dict, description="Recommended implementation timeline")
    total_transaction_costs: float = Field(..., ge=0.0, description="Estimated total transaction costs")
    expected_annual_benefit: float = Field(..., description="Expected annual benefit from improvements")

    # Constraints and considerations
    constraints_met: list[str] = Field(default_factory=list, description="Portfolio constraints that are satisfied")
    implementation_notes: list[str] = Field(default_factory=list, description="Important implementation considerations")
