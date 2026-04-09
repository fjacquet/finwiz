"""
Risk management and safeguards system for portfolio rebalancing.

This module provides comprehensive risk management functionality including
concentration limits, turnover monitoring, volatility-based recommendations,
tax-loss harvesting awareness, and position size validation.
"""

from __future__ import annotations

import logging

from finwiz.quantitative.risk_calculations import (
    calculate_concentration_risk,
    calculate_tax_efficiency_score,
    calculate_turnover_risk,
    calculate_volatility_risk,
)
from finwiz.quantitative.risk_metrics import (
    RiskAssessment,
    RiskLevel,
    RiskManagerConfig,
    RiskWarning,
    RiskWarningType,
)
from finwiz.quantitative.risk_recommendations import (
    recommend_rebalancing_frequency,
    recommend_tolerance_adjustment,
)
from finwiz.quantitative.risk_validators import (
    check_concentration_limits,
    check_position_size_warnings,
    check_tax_implications,
    check_turnover_limits,
    check_volatility_risks,
)
from finwiz.schemas.portfolio_rebalancing import (
    PortfolioConfiguration,
    RebalancingResult,
)

logger = logging.getLogger(__name__)


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
        return check_concentration_limits(
            portfolio_config,
            rebalancing_result,
            max_single_position=self.config.concentration_limits.max_single_position,
            max_top_5_positions=self.config.concentration_limits.max_top_5_positions,
            min_number_positions=self.config.concentration_limits.min_number_positions,
        )

    def _check_turnover_limits(self, rebalancing_result: RebalancingResult) -> list[RiskWarning]:
        """Check for excessive portfolio turnover."""
        return check_turnover_limits(
            rebalancing_result,
            max_monthly_turnover=self.config.turnover_limits.max_monthly_turnover,
            warning_threshold=self.config.turnover_limits.warning_threshold,
        )

    def _check_volatility_risks(
        self,
        portfolio_config: PortfolioConfiguration,
        market_volatility: float,
    ) -> list[RiskWarning]:
        """Check volatility-based rebalancing risks."""
        return check_volatility_risks(
            market_volatility,
            high_volatility_threshold=self.config.volatility_thresholds.high_volatility_threshold,
            extreme_volatility_threshold=self.config.volatility_thresholds.extreme_volatility_threshold,
        )

    def _check_tax_implications(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
    ) -> list[RiskWarning]:
        """Check for significant tax implications."""
        return check_tax_implications(
            portfolio_config,
            rebalancing_result,
            enable_tax_awareness=self.config.tax_config.enable_tax_awareness,
            short_term_threshold_days=self.config.tax_config.short_term_threshold_days,
            minimum_loss_threshold=self.config.tax_config.minimum_loss_threshold,
        )

    def _check_position_size_warnings(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
    ) -> list[RiskWarning]:
        """Check for position size and market impact warnings."""
        return check_position_size_warnings(
            rebalancing_result,
            enable_position_size_warnings=self.config.enable_position_size_warnings,
            enable_market_impact_warnings=self.config.enable_market_impact_warnings,
        )

    def _calculate_concentration_risk(self, rebalancing_result: RebalancingResult) -> float:
        """Calculate concentration risk score."""
        return calculate_concentration_risk(rebalancing_result)

    def _calculate_turnover_risk(self, rebalancing_result: RebalancingResult) -> float:
        """Calculate turnover risk score."""
        return calculate_turnover_risk(rebalancing_result)

    def _calculate_volatility_risk(self, market_volatility: float) -> float:
        """Calculate volatility risk score."""
        return calculate_volatility_risk(market_volatility)

    def _calculate_tax_efficiency_score(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
    ) -> float:
        """Calculate tax efficiency score."""
        return calculate_tax_efficiency_score(
            portfolio_config,
            rebalancing_result,
            enable_tax_awareness=self.config.tax_config.enable_tax_awareness,
            short_term_threshold_days=self.config.tax_config.short_term_threshold_days,
        )

    def _recommend_tolerance_adjustment(
        self,
        warnings: list[RiskWarning],
        market_volatility: float | None,
    ) -> float | None:
        """Recommend tolerance band adjustment based on risk assessment."""
        return recommend_tolerance_adjustment(warnings, market_volatility)

    def _recommend_rebalancing_frequency(
        self,
        warnings: list[RiskWarning],
        market_volatility: float | None,
    ) -> str:
        """Recommend rebalancing frequency based on risk assessment."""
        return recommend_rebalancing_frequency(warnings, market_volatility)

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


# Re-export classes for backward compatibility
from finwiz.quantitative.risk_metrics import (  # noqa: E402
    ConcentrationLimits,
    TaxLossHarvestingConfig,
    TurnoverLimits,
    VolatilityThresholds,
)

__all__ = [
    "ConcentrationLimits",
    "RiskAssessment",
    "RiskLevel",
    "RiskManager",
    "RiskManagerConfig",
    "RiskWarning",
    "RiskWarningType",
    "TaxLossHarvestingConfig",
    "TurnoverLimits",
    "VolatilityThresholds",
]
