"""
Risk management and safeguards system for portfolio rebalancing.

This module provides comprehensive risk management functionality including
concentration limits, turnover monitoring, volatility-based recommendations,
tax-loss harvesting awareness, and position size validation.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from finwiz.schemas.portfolio_rebalancing import (
    PortfolioConfiguration,
    RebalancingResult,
)

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk level enumeration."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskWarningType(str, Enum):
    """Risk warning type enumeration."""

    CONCENTRATION = "CONCENTRATION"
    TURNOVER = "TURNOVER"
    VOLATILITY = "VOLATILITY"
    TAX_IMPLICATIONS = "TAX_IMPLICATIONS"
    POSITION_SIZE = "POSITION_SIZE"
    MARKET_IMPACT = "MARKET_IMPACT"


class RiskWarning(BaseModel):
    """Individual risk warning."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    warning_type: RiskWarningType = Field(..., description="Type of risk warning")
    risk_level: RiskLevel = Field(..., description="Severity level of the risk")
    symbol: str | None = Field(None, description="Affected symbol (if applicable)")
    message: str = Field(..., min_length=10, description="Detailed warning message")
    recommendation: str = Field(..., min_length=10, description="Recommended action")
    impact_score: float = Field(..., ge=0, le=10, description="Impact score (0=minimal, 10=severe)")


class ConcentrationLimits(BaseModel):
    """Concentration limit configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    max_single_position: float = Field(default=0.20, gt=0, le=1, description="Maximum weight for single position")
    max_sector_concentration: float = Field(default=0.30, gt=0, le=1, description="Maximum sector concentration")
    max_top_5_positions: float = Field(default=0.60, gt=0, le=1, description="Maximum weight of top 5 positions")
    min_number_positions: int = Field(default=5, ge=1, description="Minimum number of positions")


class TurnoverLimits(BaseModel):
    """Portfolio turnover limit configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    max_annual_turnover: float = Field(default=1.0, gt=0, description="Maximum annual turnover ratio")
    max_monthly_turnover: float = Field(default=0.25, gt=0, description="Maximum monthly turnover ratio")
    warning_threshold: float = Field(default=0.5, gt=0, description="Turnover warning threshold")


class VolatilityThresholds(BaseModel):
    """Market volatility threshold configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    low_volatility_threshold: float = Field(default=0.15, gt=0, description="Low volatility threshold (15%)")
    high_volatility_threshold: float = Field(default=0.30, gt=0, description="High volatility threshold (30%)")
    extreme_volatility_threshold: float = Field(default=0.50, gt=0, description="Extreme volatility threshold (50%)")


class TaxLossHarvestingConfig(BaseModel):
    """Tax-loss harvesting configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    enable_tax_awareness: bool = Field(default=True, description="Enable tax-loss harvesting awareness")
    short_term_threshold_days: int = Field(default=365, ge=1, description="Short-term capital gains threshold")
    minimum_loss_threshold: float = Field(default=0.05, gt=0, description="Minimum loss threshold for harvesting")
    wash_sale_period_days: int = Field(default=30, ge=1, description="Wash sale rule period")


class RiskManagerConfig(BaseModel):
    """Risk manager configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    concentration_limits: ConcentrationLimits = Field(default_factory=ConcentrationLimits)
    turnover_limits: TurnoverLimits = Field(default_factory=TurnoverLimits)
    volatility_thresholds: VolatilityThresholds = Field(default_factory=VolatilityThresholds)
    tax_config: TaxLossHarvestingConfig = Field(default_factory=TaxLossHarvestingConfig)
    enable_position_size_warnings: bool = Field(default=True, description="Enable position size warnings")
    enable_market_impact_warnings: bool = Field(default=True, description="Enable market impact warnings")


class RiskAssessment(BaseModel):
    """Comprehensive risk assessment result."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    overall_risk_score: float = Field(..., ge=0, le=10, description="Overall risk score")
    warnings: list[RiskWarning] = Field(default_factory=list, description="Risk warnings")
    concentration_risk: float = Field(..., ge=0, le=10, description="Concentration risk score")
    turnover_risk: float = Field(..., ge=0, le=10, description="Turnover risk score")
    volatility_risk: float = Field(..., ge=0, le=10, description="Volatility risk score")
    tax_efficiency_score: float = Field(..., ge=0, le=10, description="Tax efficiency score")
    recommended_tolerance_adjustment: float | None = Field(None, description="Recommended tolerance adjustment")
    rebalancing_frequency_recommendation: str = Field(..., description="Recommended rebalancing frequency")


class RiskManager:
    """
    Risk management and safeguards system for portfolio rebalancing.

    Provides comprehensive risk assessment including concentration limits,
    turnover monitoring, volatility-based recommendations, tax implications,
    and position size validation.
    """

    def __init__(self, config: RiskManagerConfig | None = None) -> None:
        """Initialize risk manager with configuration."""
        self.config = config or RiskManagerConfig()
        self.logger = logging.getLogger(__name__)

    def assess_rebalancing_risks(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
        market_volatility: float | None = None,
    ) -> RiskAssessment:
        """
        Perform comprehensive risk assessment of rebalancing recommendations.

        Args:
            portfolio_config: Portfolio configuration
            rebalancing_result: Rebalancing analysis result
            market_volatility: Current market volatility (optional)

        Returns:
            Comprehensive risk assessment

        """
        warnings: list[RiskWarning] = []

        # Check concentration limits
        concentration_warnings = self._check_concentration_limits(portfolio_config, rebalancing_result)
        warnings.extend(concentration_warnings)

        # Check turnover limits
        turnover_warnings = self._check_turnover_limits(rebalancing_result)
        warnings.extend(turnover_warnings)

        # Check volatility-based recommendations
        if market_volatility is not None:
            volatility_warnings = self._check_volatility_risks(portfolio_config, market_volatility)
            warnings.extend(volatility_warnings)

        # Check tax implications
        tax_warnings = self._check_tax_implications(portfolio_config, rebalancing_result)
        warnings.extend(tax_warnings)

        # Check position size warnings
        position_warnings = self._check_position_size_warnings(portfolio_config, rebalancing_result)
        warnings.extend(position_warnings)

        # Calculate risk scores
        concentration_risk = self._calculate_concentration_risk(rebalancing_result)
        turnover_risk = self._calculate_turnover_risk(rebalancing_result)
        volatility_risk = self._calculate_volatility_risk(market_volatility or 0.20)
        tax_efficiency = self._calculate_tax_efficiency_score(portfolio_config, rebalancing_result)

        # Calculate overall risk score
        overall_risk = concentration_risk * 0.3 + turnover_risk * 0.25 + volatility_risk * 0.25 + (10 - tax_efficiency) * 0.20

        # Generate recommendations
        tolerance_adjustment = self._recommend_tolerance_adjustment(warnings, market_volatility)
        frequency_recommendation = self._recommend_rebalancing_frequency(warnings, market_volatility)

        return RiskAssessment(
            overall_risk_score=min(overall_risk, 10.0),
            warnings=warnings,
            concentration_risk=concentration_risk,
            turnover_risk=turnover_risk,
            volatility_risk=volatility_risk,
            tax_efficiency_score=tax_efficiency,
            recommended_tolerance_adjustment=tolerance_adjustment,
            rebalancing_frequency_recommendation=frequency_recommendation,
        )

    def _check_concentration_limits(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
    ) -> list[RiskWarning]:
        """Check for concentration limit violations."""
        warnings: list[RiskWarning] = []

        # Check projected weights after rebalancing
        projected_weights = rebalancing_result.projected_portfolio.weightings

        # Check single position limits
        for symbol, weight in projected_weights.items():
            if weight > self.config.concentration_limits.max_single_position:
                warnings.append(
                    RiskWarning(
                        warning_type=RiskWarningType.CONCENTRATION,
                        risk_level=RiskLevel.HIGH if weight > 0.30 else RiskLevel.MEDIUM,
                        symbol=symbol,
                        message=f"Position {symbol} would represent {weight:.1%} of portfolio, exceeding {self.config.concentration_limits.max_single_position:.1%} limit",
                        recommendation=f"Consider reducing target weight for {symbol} or increasing portfolio diversification",
                        impact_score=min(weight * 20, 10.0),
                    )
                )

        # Check top 5 positions concentration
        sorted_weights = sorted(projected_weights.values(), reverse=True)
        top_5_weight = sum(sorted_weights[:5])
        if top_5_weight > self.config.concentration_limits.max_top_5_positions:
            warnings.append(
                RiskWarning(
                    warning_type=RiskWarningType.CONCENTRATION,
                    risk_level=RiskLevel.MEDIUM,
                    symbol=None,
                    message=f"Top 5 positions would represent {top_5_weight:.1%} of portfolio, exceeding {self.config.concentration_limits.max_top_5_positions:.1%} limit",
                    recommendation="Consider increasing diversification across more positions",
                    impact_score=min((top_5_weight - 0.6) * 25, 10.0),
                )
            )

        # Check minimum number of positions
        num_positions = len([w for w in projected_weights.values() if w > 0.01])
        if num_positions < self.config.concentration_limits.min_number_positions:
            warnings.append(
                RiskWarning(
                    warning_type=RiskWarningType.CONCENTRATION,
                    risk_level=RiskLevel.HIGH,
                    symbol=None,
                    message=f"Portfolio has only {num_positions} significant positions, below minimum of {self.config.concentration_limits.min_number_positions}",
                    recommendation="Consider adding more positions to improve diversification",
                    impact_score=8.0,
                )
            )

        return warnings

    def _check_turnover_limits(self, rebalancing_result: RebalancingResult) -> list[RiskWarning]:
        """Check for excessive portfolio turnover."""
        warnings: list[RiskWarning] = []

        # Calculate turnover from trade recommendations
        total_trade_value = sum(abs(trade.trade_value) for trade in rebalancing_result.trade_recommendations)
        portfolio_value = rebalancing_result.current_portfolio.total_value
        turnover_ratio = total_trade_value / (2 * portfolio_value)  # Divide by 2 for one-way turnover

        # Check against limits
        if turnover_ratio > self.config.turnover_limits.max_monthly_turnover:
            risk_level = RiskLevel.HIGH if turnover_ratio > 0.5 else RiskLevel.MEDIUM
            warnings.append(
                RiskWarning(
                    warning_type=RiskWarningType.TURNOVER,
                    risk_level=risk_level,
                    symbol=None,
                    message=f"Rebalancing would result in {turnover_ratio:.1%} portfolio turnover, exceeding {self.config.turnover_limits.max_monthly_turnover:.1%} monthly limit",
                    recommendation="Consider phased rebalancing over multiple periods or increasing tolerance bands to reduce turnover",
                    impact_score=min(turnover_ratio * 20, 10.0),
                )
            )
        elif turnover_ratio > self.config.turnover_limits.warning_threshold:
            warnings.append(
                RiskWarning(
                    warning_type=RiskWarningType.TURNOVER,
                    risk_level=RiskLevel.LOW,
                    symbol=None,
                    message=f"Rebalancing would result in {turnover_ratio:.1%} portfolio turnover, above {self.config.turnover_limits.warning_threshold:.1%} warning threshold",
                    recommendation="Monitor turnover frequency to avoid excessive trading costs",
                    impact_score=turnover_ratio * 10,
                )
            )

        return warnings

    def _check_volatility_risks(
        self,
        portfolio_config: PortfolioConfiguration,
        market_volatility: float,
    ) -> list[RiskWarning]:
        """Check volatility-based rebalancing risks."""
        warnings: list[RiskWarning] = []

        if market_volatility > self.config.volatility_thresholds.extreme_volatility_threshold:
            warnings.append(
                RiskWarning(
                    warning_type=RiskWarningType.VOLATILITY,
                    risk_level=RiskLevel.CRITICAL,
                    symbol=None,
                    message=f"Market volatility is extremely high at {market_volatility:.1%}, above {self.config.volatility_thresholds.extreme_volatility_threshold:.1%} threshold",
                    recommendation="Consider delaying rebalancing until volatility subsides or using wider tolerance bands to avoid whipsaw trading",
                    impact_score=9.0,
                )
            )
        elif market_volatility > self.config.volatility_thresholds.high_volatility_threshold:
            warnings.append(
                RiskWarning(
                    warning_type=RiskWarningType.VOLATILITY,
                    risk_level=RiskLevel.HIGH,
                    symbol=None,
                    message=f"Market volatility is high at {market_volatility:.1%}, above {self.config.volatility_thresholds.high_volatility_threshold:.1%} threshold",
                    recommendation="Consider using wider tolerance bands or phased rebalancing to reduce timing risk",
                    impact_score=6.0,
                )
            )

        return warnings

    def _check_tax_implications(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
    ) -> list[RiskWarning]:
        """Check for significant tax implications."""
        warnings: list[RiskWarning] = []

        if not self.config.tax_config.enable_tax_awareness:
            return warnings

        current_date = datetime.now()

        for trade in rebalancing_result.trade_recommendations:
            if trade.action.value == "SELL":
                # Find corresponding holding
                holding = next((h for h in portfolio_config.holdings if h.symbol == trade.symbol), None)

                if holding and holding.cost_basis and holding.acquisition_date:
                    # Calculate potential gain/loss
                    cost_basis_total = holding.cost_basis * trade.quantity
                    current_value = trade.current_price * trade.quantity
                    gain_loss = current_value - cost_basis_total

                    # Check holding period
                    holding_days = (current_date - holding.acquisition_date).days
                    is_short_term = holding_days < self.config.tax_config.short_term_threshold_days

                    if gain_loss > 0 and is_short_term:
                        warnings.append(
                            RiskWarning(
                                warning_type=RiskWarningType.TAX_IMPLICATIONS,
                                risk_level=RiskLevel.MEDIUM,
                                symbol=trade.symbol,
                                message=f"Selling {trade.symbol} would trigger short-term capital gains of ${gain_loss:,.2f} (held {holding_days} days)",
                                recommendation="Consider waiting until long-term holding period or using tax-loss harvesting opportunities",
                                impact_score=min(gain_loss / 1000, 8.0),
                            )
                        )
                    elif gain_loss < -self.config.tax_config.minimum_loss_threshold * cost_basis_total:
                        # Tax-loss harvesting opportunity
                        warnings.append(
                            RiskWarning(
                                warning_type=RiskWarningType.TAX_IMPLICATIONS,
                                risk_level=RiskLevel.LOW,
                                symbol=trade.symbol,
                                message=f"Selling {trade.symbol} would realize tax loss of ${abs(gain_loss):,.2f}",
                                recommendation="Consider tax-loss harvesting benefits and wash sale rule implications",
                                impact_score=2.0,
                            )
                        )

        return warnings

    def _check_position_size_warnings(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
    ) -> list[RiskWarning]:
        """Check for position size and market impact warnings."""
        warnings: list[RiskWarning] = []

        if not self.config.enable_position_size_warnings:
            return warnings

        portfolio_value = rebalancing_result.current_portfolio.total_value

        for trade in rebalancing_result.trade_recommendations:
            trade_percentage = abs(trade.trade_value) / portfolio_value

            # Large trade warning
            if trade_percentage > 0.10:  # 10% of portfolio
                warnings.append(
                    RiskWarning(
                        warning_type=RiskWarningType.POSITION_SIZE,
                        risk_level=RiskLevel.MEDIUM,
                        symbol=trade.symbol,
                        message=f"Trade in {trade.symbol} represents {trade_percentage:.1%} of total portfolio value (${trade.trade_value:,.2f})",
                        recommendation="Consider splitting large trades across multiple periods to reduce market impact",
                        impact_score=min(trade_percentage * 50, 8.0),
                    )
                )

            # Market impact warning for large trades
            if self.config.enable_market_impact_warnings and abs(trade.quantity) > 1000:
                warnings.append(
                    RiskWarning(
                        warning_type=RiskWarningType.MARKET_IMPACT,
                        risk_level=RiskLevel.LOW,
                        symbol=trade.symbol,
                        message=f"Large quantity trade in {trade.symbol} ({trade.quantity:,.0f} shares) may have market impact",
                        recommendation="Consider using limit orders or splitting into smaller blocks",
                        impact_score=3.0,
                    )
                )

        return warnings

    def _calculate_concentration_risk(self, rebalancing_result: RebalancingResult) -> float:
        """Calculate concentration risk score."""
        weights = list(rebalancing_result.projected_portfolio.weightings.values())

        # Herfindahl-Hirschman Index for concentration
        hhi = sum(w**2 for w in weights)

        # Convert to risk score (0-10 scale)
        # HHI ranges from 1/n (perfectly diversified) to 1 (single asset)
        # Higher HHI = higher concentration = higher risk
        risk_score = min(hhi * 10, 10.0)

        return risk_score

    def _calculate_turnover_risk(self, rebalancing_result: RebalancingResult) -> float:
        """Calculate turnover risk score."""
        total_trade_value = sum(abs(trade.trade_value) for trade in rebalancing_result.trade_recommendations)
        portfolio_value = rebalancing_result.current_portfolio.total_value
        turnover_ratio = total_trade_value / (2 * portfolio_value)

        # Convert to risk score (0-10 scale)
        risk_score = min(turnover_ratio * 20, 10.0)

        return risk_score

    def _calculate_volatility_risk(self, market_volatility: float) -> float:
        """Calculate volatility risk score."""
        # Normalize volatility to 0-10 scale
        # 15% volatility = low risk (2), 30% = medium risk (5), 50%+ = high risk (8+)
        if market_volatility <= 0.15:
            return 2.0
        elif market_volatility <= 0.30:
            return 2.0 + (market_volatility - 0.15) * 20  # Scale from 2 to 5
        else:
            return 5.0 + min((market_volatility - 0.30) * 15, 5.0)  # Scale from 5 to 10

    def _calculate_tax_efficiency_score(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
    ) -> float:
        """Calculate tax efficiency score."""
        if not self.config.tax_config.enable_tax_awareness:
            return 5.0  # Neutral score if tax awareness disabled

        total_tax_impact = 0.0
        total_trade_value = 0.0

        current_date = datetime.now()

        for trade in rebalancing_result.trade_recommendations:
            if trade.action.value == "SELL":
                holding = next((h for h in portfolio_config.holdings if h.symbol == trade.symbol), None)

                if holding and holding.cost_basis and holding.acquisition_date:
                    cost_basis_total = holding.cost_basis * trade.quantity
                    current_value = trade.current_price * trade.quantity
                    gain_loss = current_value - cost_basis_total

                    holding_days = (current_date - holding.acquisition_date).days
                    is_short_term = holding_days < self.config.tax_config.short_term_threshold_days

                    # Penalize short-term gains, reward tax-loss harvesting
                    if gain_loss > 0 and is_short_term:
                        total_tax_impact += gain_loss * 0.3  # Assume 30% short-term rate
                    elif gain_loss > 0:
                        total_tax_impact += gain_loss * 0.15  # Assume 15% long-term rate
                    else:
                        total_tax_impact += gain_loss * 0.25  # Tax benefit from losses

                    total_trade_value += abs(current_value)

        if total_trade_value == 0:
            return 10.0  # Perfect score if no taxable trades

        # Calculate tax efficiency (higher is better)
        tax_rate = abs(total_tax_impact) / total_trade_value
        efficiency_score = max(10.0 - tax_rate * 50, 0.0)

        return efficiency_score

    def _recommend_tolerance_adjustment(
        self,
        warnings: list[RiskWarning],
        market_volatility: float | None,
    ) -> float | None:
        """Recommend tolerance band adjustment based on risk assessment."""
        high_risk_warnings = [w for w in warnings if w.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]

        if not high_risk_warnings:
            return None

        # Check for volatility warnings
        volatility_warnings = [w for w in high_risk_warnings if w.warning_type == RiskWarningType.VOLATILITY]
        if volatility_warnings and market_volatility:
            if market_volatility > 0.40:
                return 0.15  # Suggest 15% tolerance in extreme volatility
            elif market_volatility > 0.25:
                return 0.10  # Suggest 10% tolerance in high volatility

        # Check for turnover warnings
        turnover_warnings = [w for w in high_risk_warnings if w.warning_type == RiskWarningType.TURNOVER]
        if turnover_warnings:
            return 0.08  # Suggest 8% tolerance to reduce turnover

        return None

    def _recommend_rebalancing_frequency(
        self,
        warnings: list[RiskWarning],
        market_volatility: float | None,
    ) -> str:
        """Recommend rebalancing frequency based on risk assessment."""
        high_risk_count = len([w for w in warnings if w.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])

        if high_risk_count >= 3:
            return "Delay rebalancing until risks subside"
        elif high_risk_count >= 2:
            return "Quarterly rebalancing with careful monitoring"
        elif market_volatility and market_volatility > 0.30:
            return "Semi-annual rebalancing during high volatility periods"
        elif any(w.warning_type == RiskWarningType.TURNOVER for w in warnings):
            return "Quarterly rebalancing to manage turnover"
        else:
            return "Monthly rebalancing with standard monitoring"

    def validate_rebalancing_safety(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
        market_volatility: float | None = None,
    ) -> tuple[bool, list[str]]:
        """
        Validate if rebalancing is safe to proceed.

        Args:
            portfolio_config: Portfolio configuration
            rebalancing_result: Rebalancing analysis result
            market_volatility: Current market volatility (optional)

        Returns:
            Tuple of (is_safe, list_of_blocking_issues)

        """
        risk_assessment = self.assess_rebalancing_risks(portfolio_config, rebalancing_result, market_volatility)

        blocking_issues: list[str] = []

        # Check for critical warnings
        critical_warnings = [w for w in risk_assessment.warnings if w.risk_level == RiskLevel.CRITICAL]
        for warning in critical_warnings:
            blocking_issues.append(f"CRITICAL: {warning.message}")

        # Check overall risk score
        if risk_assessment.overall_risk_score > 8.0:
            blocking_issues.append(f"Overall risk score too high: {risk_assessment.overall_risk_score:.1f}/10")

        # Check concentration risk
        if risk_assessment.concentration_risk > 8.0:
            blocking_issues.append(f"Concentration risk too high: {risk_assessment.concentration_risk:.1f}/10")

        # Check turnover risk
        if risk_assessment.turnover_risk > 8.0:
            blocking_issues.append(f"Turnover risk too high: {risk_assessment.turnover_risk:.1f}/10")

        is_safe = len(blocking_issues) == 0

        self.logger.info(
            f"Rebalancing safety validation: {'SAFE' if is_safe else 'UNSAFE'}, Risk score: {risk_assessment.overall_risk_score:.1f}/10, Warnings: {len(risk_assessment.warnings)}"
        )

        return is_safe, blocking_issues
