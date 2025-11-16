"""
Portfolio rebalancing constraint handling utilities.

This module contains constraint validation, risk assessment, and safety
validation logic for portfolio rebalancing operations.
"""

from datetime import datetime, timedelta
from typing import Any

from finwiz.quantitative.risk_manager import RiskManager
from finwiz.schemas.portfolio_rebalancing import (
    CostAnalysis,
    PortfolioConfiguration,
    RebalancingRecommendation,
    RebalancingResult,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PortfolioRebalancingError(Exception):
    """Base exception for portfolio rebalancing constraint errors."""

    pass


class RebalancingConstraintManager:
    """Handles constraint validation and risk assessment for portfolio rebalancing."""

    def __init__(self, risk_manager: RiskManager | None = None) -> None:
        """
        Initialize the constraint manager.

        Args:
            risk_manager: Risk management and safeguards instance

        """
        self.risk_manager = risk_manager or RiskManager()
        self.logger = logger

    async def assess_rebalancing_risks(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
        market_volatility: float | None = None,
    ) -> Any:
        """
        Assess rebalancing risks for a given portfolio and rebalancing result.

        Args:
            portfolio_config: Portfolio configuration
            rebalancing_result: Rebalancing analysis result
            market_volatility: Current market volatility (optional)

        Returns:
            Risk assessment result

        """
        self.logger.info("Performing comprehensive risk assessment")
        return self.risk_manager.assess_rebalancing_risks(portfolio_config, rebalancing_result, market_volatility)

    async def validate_rebalancing_safety(
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
        self.logger.info("Validating rebalancing safety")
        return self.risk_manager.validate_rebalancing_safety(portfolio_config, rebalancing_result, market_volatility)

    def determine_overall_recommendation(
        self, rebalancing_needs: list[Any], cost_analysis: CostAnalysis, current_risk_score: float, risk_assessment: Any = None
    ) -> tuple[RebalancingRecommendation, datetime]:
        """
        Determine overall rebalancing recommendation with risk assessment.

        Args:
            rebalancing_needs: List of rebalancing needs
            cost_analysis: Cost analysis results
            current_risk_score: Current portfolio risk score
            risk_assessment: Risk assessment results (optional)

        Returns:
            Tuple of (recommendation, next_review_date)

        """
        try:
            # Count positions needing action
            positions_needing_action = sum(1 for need in rebalancing_needs if need.needs_rebalancing)

            # Check for high urgency positions
            high_urgency_positions = sum(1 for need in rebalancing_needs if need.urgency_score >= 0.7)

            # Consider risk assessment if available
            high_risk_warnings = 0
            if risk_assessment:
                from finwiz.quantitative.risk_manager import RiskLevel

                high_risk_warnings = len([w for w in risk_assessment.warnings if w.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])

            # Determine recommendation based on multiple factors including risk
            if positions_needing_action == 0:
                recommendation = RebalancingRecommendation.NO_ACTION
                next_review = datetime.now() + timedelta(days=30)
            elif high_risk_warnings >= 2:  # Multiple high-risk warnings
                recommendation = RebalancingRecommendation.MONITOR
                next_review = datetime.now() + timedelta(days=7)
            elif high_urgency_positions > 0 or current_risk_score >= 8.0:
                recommendation = RebalancingRecommendation.REBALANCE_NOW
                next_review = datetime.now() + timedelta(days=7)
            elif cost_analysis.cost_as_percentage > 1.0:  # High cost relative to portfolio
                recommendation = RebalancingRecommendation.MONITOR
                next_review = datetime.now() + timedelta(days=14)
            elif positions_needing_action >= 3:
                recommendation = RebalancingRecommendation.REBALANCE_SOON
                next_review = datetime.now() + timedelta(days=7)
            else:
                recommendation = RebalancingRecommendation.MONITOR
                next_review = datetime.now() + timedelta(days=14)

            # Adjust based on risk assessment frequency recommendation
            if risk_assessment and hasattr(risk_assessment, "rebalancing_frequency_recommendation"):
                if "Delay" in risk_assessment.rebalancing_frequency_recommendation:
                    recommendation = RebalancingRecommendation.MONITOR
                    next_review = datetime.now() + timedelta(days=30)

            return recommendation, next_review

        except Exception as e:
            self.logger.warning(f"Error determining recommendation, using default: {e}")
            return RebalancingRecommendation.MONITOR, datetime.now() + timedelta(days=14)

    def validate_portfolio_constraints(self, portfolio_config: PortfolioConfiguration, current_analysis: Any) -> tuple[bool, list[str]]:
        """
        Validate portfolio configuration constraints.

        Args:
            portfolio_config: Portfolio configuration
            current_analysis: Current portfolio analysis

        Returns:
            Tuple of (is_valid, list_of_violations)

        """
        violations = []

        try:
            # Validate target weights sum to 1.0
            total_target_weight = sum(portfolio_config.target_weights.values())
            if abs(total_target_weight - 1.0) > 0.01:  # Allow 1% tolerance
                violations.append(f"Target weights sum to {total_target_weight:.3f}, should be 1.0")

            # Validate minimum trade size is reasonable
            if portfolio_config.min_trade_size <= 0:
                violations.append("Minimum trade size must be positive")
            elif portfolio_config.min_trade_size > current_analysis.total_value * 0.1:
                violations.append("Minimum trade size is too large relative to portfolio value")

            # Validate tolerance bands
            for symbol, tolerance in portfolio_config.tolerance_bands.items():
                if tolerance <= 0 or tolerance > 0.5:  # 0-50% range
                    violations.append(f"Invalid tolerance band for {symbol}: {tolerance:.1%}")

            # Validate global tolerance
            if portfolio_config.global_tolerance <= 0 or portfolio_config.global_tolerance > 0.2:
                violations.append(f"Invalid global tolerance: {portfolio_config.global_tolerance:.1%}")

            # Check for missing symbols in target weights
            holding_symbols = {holding.symbol for holding in portfolio_config.holdings}
            target_symbols = set(portfolio_config.target_weights.keys())

            missing_targets = holding_symbols - target_symbols
            if missing_targets:
                violations.append(f"Missing target weights for symbols: {', '.join(missing_targets)}")

            extra_targets = target_symbols - holding_symbols
            if extra_targets:
                violations.append(f"Target weights for non-held symbols: {', '.join(extra_targets)}")

            is_valid = len(violations) == 0
            return is_valid, violations

        except Exception as e:
            self.logger.error(f"Error validating portfolio constraints: {e}")
            return False, [f"Constraint validation error: {str(e)}"]

    def validate_trade_constraints(self, trades: list[Any], portfolio_config: PortfolioConfiguration, current_analysis: Any) -> tuple[bool, list[str]]:
        """
        Validate trade-specific constraints.

        Args:
            trades: List of proposed trades
            portfolio_config: Portfolio configuration
            current_analysis: Current portfolio analysis

        Returns:
            Tuple of (is_valid, list_of_violations)

        """
        violations = []

        try:
            # Check individual trade constraints
            for trade in trades:
                # Validate trade size
                if hasattr(trade, "trade_value") and abs(trade.trade_value) < portfolio_config.min_trade_size:
                    if trade.action.value != "HOLD":  # Only flag non-hold trades
                        violations.append(f"Trade for {trade.symbol} below minimum size: ${abs(trade.trade_value):.2f}")

                # Validate position limits
                if hasattr(trade, "projected_weight_after_trade"):
                    if trade.projected_weight_after_trade > 0.3:  # 30% maximum position
                        violations.append(f"Trade would create oversized position in {trade.symbol}: {trade.projected_weight_after_trade:.1%}")

            # Check portfolio-level constraints
            total_trade_value = sum(abs(trade.trade_value) for trade in trades if hasattr(trade, "trade_value"))
            portfolio_turnover = total_trade_value / current_analysis.total_value if current_analysis.total_value > 0 else 0

            if portfolio_turnover > 0.75:  # 75% maximum turnover
                violations.append(f"Excessive portfolio turnover: {portfolio_turnover:.1%}")

            # Check available capital constraint
            if portfolio_config.available_capital != 0:
                required_capital = sum(max(0, trade.trade_value) for trade in trades if hasattr(trade, "trade_value"))
                if required_capital > abs(portfolio_config.available_capital):
                    violations.append(f"Insufficient capital: need ${required_capital:,.2f}, have ${abs(portfolio_config.available_capital):,.2f}")

            is_valid = len(violations) == 0
            return is_valid, violations

        except Exception as e:
            self.logger.error(f"Error validating trade constraints: {e}")
            return False, [f"Trade constraint validation error: {str(e)}"]

    def assess_market_timing_constraints(self, portfolio_config: PortfolioConfiguration, market_volatility: float | None = None) -> tuple[bool, list[str]]:
        """
        Assess market timing and volatility constraints.

        Args:
            portfolio_config: Portfolio configuration
            market_volatility: Current market volatility (optional)

        Returns:
            Tuple of (is_favorable, list_of_concerns)

        """
        concerns = []

        try:
            # Check market volatility if provided
            if market_volatility is not None:
                if market_volatility > 0.3:  # 30% volatility threshold
                    concerns.append(f"High market volatility detected: {market_volatility:.1%}")
                elif market_volatility > 0.2:  # 20% volatility warning
                    concerns.append(f"Elevated market volatility: {market_volatility:.1%}")

            # Check time-based constraints
            current_time = datetime.now()

            # Avoid rebalancing on Fridays (weekend risk)
            if current_time.weekday() == 4:  # Friday
                concerns.append("Friday rebalancing carries weekend risk")

            # Avoid rebalancing near market close
            if current_time.hour >= 15:  # After 3 PM
                concerns.append("Late-day rebalancing may face liquidity issues")

            # Check for recent rebalancing
            # This would require tracking last rebalancing date
            # For now, we'll skip this check

            is_favorable = len(concerns) == 0
            return is_favorable, concerns

        except Exception as e:
            self.logger.error(f"Error assessing market timing constraints: {e}")
            return False, [f"Market timing assessment error: {str(e)}"]

    def calculate_constraint_compliance_score(self, portfolio_config: PortfolioConfiguration, trades: list[Any], current_analysis: Any) -> dict[str, Any]:
        """
        Calculate overall constraint compliance score.

        Args:
            portfolio_config: Portfolio configuration
            trades: List of proposed trades
            current_analysis: Current portfolio analysis

        Returns:
            Dictionary with compliance scores and details

        """
        try:
            compliance_score = {
                "overall_score": 0.0,
                "portfolio_constraints": 0.0,
                "trade_constraints": 0.0,
                "risk_constraints": 0.0,
                "timing_constraints": 0.0,
                "violations": [],
                "warnings": [],
            }

            # Portfolio constraints (25% weight)
            portfolio_valid, portfolio_violations = self.validate_portfolio_constraints(portfolio_config, current_analysis)
            compliance_score["portfolio_constraints"] = 100.0 if portfolio_valid else max(0, 100 - len(portfolio_violations) * 20)
            compliance_score["violations"].extend(portfolio_violations)

            # Trade constraints (35% weight)
            trade_valid, trade_violations = self.validate_trade_constraints(trades, portfolio_config, current_analysis)
            compliance_score["trade_constraints"] = 100.0 if trade_valid else max(0, 100 - len(trade_violations) * 15)
            compliance_score["violations"].extend(trade_violations)

            # Risk constraints (25% weight) - simplified assessment
            risk_score = 100.0
            if current_analysis.risk_metrics.get("concentration_risk", 5.0) > 8.0:
                risk_score -= 30
                compliance_score["warnings"].append("High concentration risk detected")
            compliance_score["risk_constraints"] = risk_score

            # Timing constraints (15% weight)
            timing_favorable, timing_concerns = self.assess_market_timing_constraints(portfolio_config)
            compliance_score["timing_constraints"] = 100.0 if timing_favorable else max(0, 100 - len(timing_concerns) * 25)
            compliance_score["warnings"].extend(timing_concerns)

            # Calculate overall weighted score
            compliance_score["overall_score"] = (
                compliance_score["portfolio_constraints"] * 0.25
                + compliance_score["trade_constraints"] * 0.35
                + compliance_score["risk_constraints"] * 0.25
                + compliance_score["timing_constraints"] * 0.15
            )

            return compliance_score

        except Exception as e:
            self.logger.error(f"Error calculating compliance score: {e}")
            return {
                "overall_score": 0.0,
                "portfolio_constraints": 0.0,
                "trade_constraints": 0.0,
                "risk_constraints": 0.0,
                "timing_constraints": 0.0,
                "violations": [f"Compliance calculation error: {str(e)}"],
                "warnings": [],
            }

    def suggest_constraint_adjustments(self, portfolio_config: PortfolioConfiguration, violations: list[str]) -> list[str]:
        """
        Suggest adjustments to resolve constraint violations.

        Args:
            portfolio_config: Portfolio configuration
            violations: List of constraint violations

        Returns:
            List of suggested adjustments

        """
        suggestions = []

        try:
            for violation in violations:
                if "Target weights sum" in violation:
                    suggestions.append("Normalize target weights to sum to 1.0")
                elif "Minimum trade size" in violation:
                    if "too large" in violation:
                        suggestions.append("Reduce minimum trade size to 1-2% of portfolio value")
                    else:
                        suggestions.append("Set minimum trade size to at least $100")
                elif "tolerance band" in violation or "tolerance" in violation:
                    suggestions.append("Set tolerance bands between 1-10% for individual positions")
                elif "Missing target weights" in violation:
                    suggestions.append("Add target weights for all held positions")
                elif "Excessive portfolio turnover" in violation:
                    suggestions.append("Consider phased rebalancing or wider tolerance bands")
                elif "Insufficient capital" in violation:
                    suggestions.append("Increase available capital or reduce trade sizes")
                elif "oversized position" in violation:
                    suggestions.append("Implement position size limits (max 20-25% per position)")

            # Add general suggestions if no specific ones found
            if not suggestions:
                suggestions.append("Review portfolio configuration parameters")
                suggestions.append("Consider consulting with a financial advisor")

            return suggestions

        except Exception as e:
            self.logger.error(f"Error generating constraint suggestions: {e}")
            return ["Error generating suggestions - review constraints manually"]
