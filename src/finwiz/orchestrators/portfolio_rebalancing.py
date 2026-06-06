"""
Portfolio rebalancing orchestrator for FinWiz.

Consolidated module that coordinates all components of the portfolio rebalancing
system including price data retrieval, portfolio analysis, optimization, and
report generation. Uses quantitative modules directly (no wrapper classes).

Consolidates:
- rebalancing_calculations.py
- rebalancing_constraints.py
- rebalancing_optimization.py
- rebalancing_utils.py
- rebalancing_reporting.py
"""

from datetime import datetime, timedelta
from typing import Any

from finwiz.exceptions.orchestrator import InsufficientPriceDataError, PortfolioRebalancingError
from finwiz.quantitative.optimization_algorithms import OptimizedTrades
from finwiz.quantitative.portfolio_analyzer import PortfolioAnalysisError, PortfolioAnalyzer
from finwiz.quantitative.rebalancing_engine import RebalancingEngine
from finwiz.quantitative.risk_manager import RiskLevel, RiskManager
from finwiz.reporting.rebalancing.rebalancing_html_builders import RebalancingHTMLBuilder
from finwiz.schemas.portfolio_rebalancing import (
    CostAnalysis,
    ExecutionSummary,
    PortfolioConfiguration,
    RebalancingRecommendation,
    RebalancingResult,
)
from finwiz.tools.html_report_generator import HTMLReportGenerator
from finwiz.tools.logger import get_logger
from finwiz.tools.portfolio_price_service import PortfolioPriceService, PriceDataUnavailableError

logger = get_logger(__name__)


class OptimizationFailedError(Exception):
    """Raised when portfolio optimization fails."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Portfolio optimization failed: {reason}")
        self.reason = reason


class PortfolioRebalancingOrchestrator:
    """
    Main orchestrator for portfolio rebalancing operations.

    Coordinates price data retrieval, portfolio analysis, trade optimization,
    and report generation using quantitative modules directly.
    """

    def __init__(
        self,
        price_service: PortfolioPriceService | None = None,
        rebalancing_engine: RebalancingEngine | None = None,
        report_generator: HTMLReportGenerator | None = None,
        risk_manager: RiskManager | None = None,
        portfolio_analyzer: PortfolioAnalyzer | None = None,
    ) -> None:
        """Initialize with optional dependency injection."""
        self.price_service = price_service or PortfolioPriceService()
        self.rebalancing_engine = rebalancing_engine or RebalancingEngine()
        self.report_generator = report_generator or HTMLReportGenerator()
        self.risk_manager = risk_manager or RiskManager()
        self.portfolio_analyzer = portfolio_analyzer or PortfolioAnalyzer()
        logger.info("Portfolio rebalancing orchestrator initialized")

    # =========================================================================
    # Main Workflow
    # =========================================================================

    async def rebalance_portfolio(self, portfolio_config: PortfolioConfiguration, portfolio_id: str | None = None) -> RebalancingResult:
        """Execute complete portfolio rebalancing workflow."""
        logger.info(f"Starting rebalancing for {len(portfolio_config.holdings)} holdings")

        try:
            # Step 1: Get prices
            symbols = [h.symbol for h in portfolio_config.holdings]
            price_data = await self._get_portfolio_prices(symbols)

            # Step 2: Analyze current portfolio
            current_analysis = await self._analyze_portfolio(portfolio_config, price_data)

            # Step 3: Identify rebalancing needs
            rebalancing_needs = self._identify_rebalancing_needs(portfolio_config, current_analysis)

            # Step 4: Generate trade recommendations
            recommendations, validation_errors = await self._generate_recommendations(portfolio_config, current_analysis, rebalancing_needs, price_data)
            if validation_errors:
                logger.warning(f"Trade validation errors: {validation_errors}")

            optimized_trades = self._create_optimized_trades(recommendations)

            # Step 5: Calculate projections
            projected_analysis = self._calculate_projected_portfolio(portfolio_config, current_analysis, optimized_trades.trades, price_data)

            # Step 6: Cost analysis
            cost_analysis = self._calculate_cost_analysis(optimized_trades, current_analysis.total_value)

            # Step 7: Risk scores
            current_risk, projected_risk = self._calculate_risk_scores(current_analysis, projected_analysis)

            # Step 8: Execution summary
            execution_summary = self._generate_execution_summary(optimized_trades, portfolio_config)

            # Step 9: Risk assessment and recommendation
            preliminary_result = RebalancingResult(
                analysis_timestamp=datetime.now(),
                portfolio_id=portfolio_id,
                current_portfolio=current_analysis,
                trade_recommendations=optimized_trades.trades,
                projected_portfolio=projected_analysis,
                cost_analysis=cost_analysis,
                current_risk_score=current_risk,
                projected_risk_score=projected_risk,
                risk_improvement=current_risk - projected_risk,
                execution_summary=execution_summary,
                overall_recommendation=RebalancingRecommendation.REBALANCE_NOW,
                next_review_date=datetime.now() + timedelta(days=30),
            )

            risk_assessment = self.risk_manager.assess_rebalancing_risks(portfolio_config, preliminary_result)
            is_safe, blocking_issues = self.risk_manager.validate_rebalancing_safety(portfolio_config, preliminary_result)

            if not is_safe:
                logger.warning(f"Rebalancing blocked: {blocking_issues}")
                recommendation = RebalancingRecommendation.MONITOR
                next_review = datetime.now() + timedelta(days=7)
            else:
                recommendation, next_review = self._determine_recommendation(rebalancing_needs, cost_analysis, current_risk, risk_assessment)

            return RebalancingResult(
                analysis_timestamp=datetime.now(),
                portfolio_id=portfolio_id,
                current_portfolio=current_analysis,
                trade_recommendations=optimized_trades.trades,
                projected_portfolio=projected_analysis,
                cost_analysis=cost_analysis,
                current_risk_score=current_risk,
                projected_risk_score=projected_risk,
                risk_improvement=current_risk - projected_risk,
                execution_summary=execution_summary,
                overall_recommendation=recommendation,
                next_review_date=next_review,
            )

        except (PortfolioRebalancingError, InsufficientPriceDataError, OptimizationFailedError):
            raise
        except Exception as e:
            logger.error(f"Rebalancing failed: {e}")
            raise PortfolioRebalancingError(f"Rebalancing workflow failed: {e}") from e

    # =========================================================================
    # Price Data (uses PortfolioPriceService directly)
    # =========================================================================

    async def _get_portfolio_prices(self, symbols: list[str]) -> dict[str, Any]:
        """Get current prices with fallback for missing symbols."""
        try:
            price_data = await self.price_service.get_current_prices(symbols)
            missing = [s for s in symbols if s not in price_data]

            for symbol in missing:
                try:
                    price_data[symbol] = await self.price_service.get_price_with_fallback(symbol)
                    logger.info(f"Retrieved fallback price for {symbol}")
                except (PriceDataUnavailableError, Exception):
                    logger.error(f"No price for {symbol}")

            still_missing = [s for s in symbols if s not in price_data]
            if still_missing:
                raise InsufficientPriceDataError(still_missing)

            return price_data
        except InsufficientPriceDataError:
            raise
        except Exception as e:
            raise PortfolioRebalancingError(f"Price retrieval failed: {e}") from e

    # =========================================================================
    # Portfolio Analysis (uses PortfolioAnalyzer directly)
    # =========================================================================

    async def _analyze_portfolio(self, config: PortfolioConfiguration, price_data: dict[str, Any]) -> Any:
        """Analyze current portfolio composition."""
        try:
            return self.portfolio_analyzer.analyze_current_portfolio(holdings=config.holdings, prices=price_data, target_weights=config.target_weights)
        except PortfolioAnalysisError as e:
            raise PortfolioRebalancingError(f"Portfolio analysis failed: {e}") from e

    def _identify_rebalancing_needs(self, config: PortfolioConfiguration, current_analysis: Any) -> list[Any]:
        """Identify positions requiring rebalancing."""
        try:
            needs = self.portfolio_analyzer.identify_rebalancing_needs(
                current_weights=current_analysis.weightings,
                target_weights=config.target_weights,
                tolerance_bands=config.tolerance_bands,
                global_tolerance=config.global_tolerance,
            )
            action_count = sum(1 for n in needs if n.needs_rebalancing)
            logger.info(f"Identified {action_count} positions needing rebalancing")
            return needs
        except Exception as e:
            raise PortfolioRebalancingError(f"Failed to identify needs: {e}") from e

    # =========================================================================
    # Optimization (uses RebalancingEngine directly)
    # =========================================================================

    async def _generate_recommendations(
        self,
        config: PortfolioConfiguration,
        current_analysis: Any,
        rebalancing_needs: list[Any],
        price_data: dict[str, Any],
    ) -> tuple[list[Any], list[str]]:
        """Generate trade recommendations using RebalancingEngine."""
        try:
            price_dict = {s: (p.price if hasattr(p, "price") else float(p)) for s, p in price_data.items()}

            recommendations, errors = self.rebalancing_engine.generate_enhanced_trade_recommendations(
                rebalancing_needs=rebalancing_needs,
                current_portfolio=current_analysis,
                target_weights=config.target_weights,
                prices=price_dict,
                config=config,
                holdings=config.holdings,
            )
            logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations, errors
        except Exception as e:
            raise OptimizationFailedError(str(e)) from e

    def _create_optimized_trades(self, recommendations: list[Any]) -> OptimizedTrades:
        """Create OptimizedTrades from recommendations."""
        capital_used = sum(abs(r.trade_value) for r in recommendations if hasattr(r, "trade_value"))
        return OptimizedTrades(
            trades=recommendations,
            total_cost=0.0,
            capital_used=capital_used,
            constraints_violated=[],
            optimization_score=1.0,
            method_used="enhanced_trade_recommendation_system",
        )

    # =========================================================================
    # Calculations
    # =========================================================================

    def _calculate_projected_portfolio(
        self,
        config: PortfolioConfiguration,
        current_analysis: Any,
        trades: list[Any],
        price_data: dict[str, Any],
    ) -> Any:
        """Calculate projected portfolio after trades."""
        try:
            projected = current_analysis.model_copy()
            for trade in trades:
                if trade.symbol in config.target_weights:
                    projected.weightings[trade.symbol] = trade.projected_weight_after_trade

            projected.deviations_from_target = {s: projected.weightings.get(s, 0.0) - config.target_weights.get(s, 0.0) for s in config.target_weights}
            projected.positions_needing_rebalancing = [s for s, d in projected.deviations_from_target.items() if abs(d) > config.tolerance_bands.get(s, config.global_tolerance)]
            return projected
        except Exception as e:
            raise PortfolioRebalancingError(f"Projection failed: {e}") from e

    def _calculate_cost_analysis(self, optimized_trades: OptimizedTrades, portfolio_value: float) -> CostAnalysis:
        """Calculate comprehensive cost analysis."""
        try:
            commission = sum(t.estimated_commission for t in optimized_trades.trades)
            spread = sum(t.estimated_spread_cost for t in optimized_trades.trades)
            total = commission + spread
            pct = (total / portfolio_value * 100) if portfolio_value > 0 else 0.0
            daily_return = 0.07 / 365
            break_even = int(pct / (daily_return * 100)) if daily_return > 0 else None

            return CostAnalysis(
                total_transaction_costs=total,
                commission_costs=commission,
                spread_costs=spread,
                market_impact_costs=0.0,
                cost_as_percentage=pct,
                break_even_days=break_even,
            )
        except Exception as e:
            raise PortfolioRebalancingError(f"Cost analysis failed: {e}") from e

    def _calculate_risk_scores(self, current: Any, projected: Any) -> tuple[float, float]:
        """Calculate risk scores (0-10 scale)."""
        try:
            current_risk = current.risk_metrics.get("concentration_risk", 5.0)
            projected_risk = projected.risk_metrics.get("concentration_risk", 5.0)
            return (
                max(0.0, min(10.0, current_risk)),
                max(0.0, min(10.0, projected_risk)),
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to calculate risk scores, using defaults: {e}")
            return 5.0, 5.0

    def _generate_execution_summary(self, optimized_trades: OptimizedTrades, config: PortfolioConfiguration) -> ExecutionSummary:
        """Generate execution summary."""
        try:
            trades = [t for t in optimized_trades.trades if t.action.value != "HOLD"]
            total_trades = len(trades)
            symbols_with_action = len(set(t.symbol for t in trades))
            within_tolerance = len(config.holdings) - symbols_with_action

            if total_trades == 0:
                time_est = "No trades required"
            elif total_trades <= 3:
                time_est = "5-10 minutes"
            elif total_trades <= 10:
                time_est = "15-30 minutes"
            else:
                time_est = "30-60 minutes"

            return ExecutionSummary(
                total_trades_required=total_trades,
                positions_requiring_action=symbols_with_action,
                positions_within_tolerance=within_tolerance,
                estimated_execution_time=time_est,
                capital_required=optimized_trades.capital_used,
            )
        except Exception as e:
            raise PortfolioRebalancingError(f"Execution summary failed: {e}") from e

    # =========================================================================
    # Risk Assessment (uses RiskManager directly)
    # =========================================================================

    def _determine_recommendation(
        self,
        rebalancing_needs: list[Any],
        cost_analysis: CostAnalysis,
        current_risk: float,
        risk_assessment: Any,
    ) -> tuple[RebalancingRecommendation, datetime]:
        """Determine overall recommendation with risk assessment."""
        try:
            action_count = sum(1 for n in rebalancing_needs if n.needs_rebalancing)
            high_urgency = sum(1 for n in rebalancing_needs if n.urgency_score >= 0.7)

            high_risk_warnings = 0
            if risk_assessment:
                high_risk_warnings = len([w for w in risk_assessment.warnings if w.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])

            if action_count == 0:
                return RebalancingRecommendation.NO_ACTION, datetime.now() + timedelta(days=30)
            elif high_risk_warnings >= 2:
                return RebalancingRecommendation.MONITOR, datetime.now() + timedelta(days=7)
            elif high_urgency > 0 or current_risk >= 8.0:
                return RebalancingRecommendation.REBALANCE_NOW, datetime.now() + timedelta(days=7)
            elif cost_analysis.cost_as_percentage > 1.0:
                return RebalancingRecommendation.MONITOR, datetime.now() + timedelta(days=14)
            elif action_count >= 3:
                return RebalancingRecommendation.REBALANCE_SOON, datetime.now() + timedelta(days=7)
            else:
                return RebalancingRecommendation.MONITOR, datetime.now() + timedelta(days=14)
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            logger.warning(f"Failed to determine recommendation, defaulting to MONITOR: {e}")
            return RebalancingRecommendation.MONITOR, datetime.now() + timedelta(days=14)

    # =========================================================================
    # Reports (uses HTMLReportGenerator directly)
    # =========================================================================

    async def generate_rebalancing_report(self, result: RebalancingResult, language: str = "en") -> str:
        """Generate comprehensive HTML rebalancing report."""
        logger.info("Generating rebalancing report")
        try:
            self.report_generator.clear_sections()

            self.report_generator.add_section("Executive Summary", RebalancingHTMLBuilder.build_executive_summary(result), "summary", order=1)
            self.report_generator.add_section("Current Portfolio", RebalancingHTMLBuilder.build_current_portfolio(result), "portfolio", order=2)
            self.report_generator.add_section("Trade Recommendations", RebalancingHTMLBuilder.build_trade_recommendations(result), "data", order=3)
            self.report_generator.add_section("Cost Analysis", RebalancingHTMLBuilder.build_cost_analysis(result), "financial", order=4)
            self.report_generator.add_section("Risk Analysis", RebalancingHTMLBuilder.build_risk_analysis(result), "risk", order=5)
            self.report_generator.add_section("Projected Portfolio", RebalancingHTMLBuilder.build_projected_portfolio(result), "growth", order=6)

            if language == "fr":
                self.report_generator.add_section("Synthese 10-K", RebalancingHTMLBuilder.build_french_sections(result), "summary", order=7)

            title = f"Portfolio Rebalancing - {result.analysis_timestamp.strftime('%Y-%m-%d')}"
            if hasattr(self.report_generator, "generate_unified_html"):
                return self.report_generator.generate_unified_html(title=title, language=language)
            return self.report_generator.generate_html(title=title, language=language)
        except Exception as e:
            raise PortfolioRebalancingError(f"Report generation failed: {e}") from e

    # =========================================================================
    # Public API (backward compatibility)
    # =========================================================================

    async def analyze_current_portfolio(self, portfolio_config: PortfolioConfiguration) -> Any:
        """Analyze current portfolio without generating trade recommendations."""
        logger.info("Analyzing current portfolio")
        try:
            symbols = [h.symbol for h in portfolio_config.holdings]
            price_data = await self._get_portfolio_prices(symbols)
            analysis = await self._analyze_portfolio(portfolio_config, price_data)
            logger.info(f"Analysis complete: ${analysis.total_value:,.2f}")
            return analysis
        except Exception as e:
            raise PortfolioRebalancingError(f"Portfolio analysis failed: {e}") from e

    async def assess_rebalancing_risks(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
        market_volatility: float | None = None,
    ) -> Any:
        """Assess rebalancing risks."""
        return self.risk_manager.assess_rebalancing_risks(portfolio_config, rebalancing_result, market_volatility)

    async def validate_rebalancing_safety(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
        market_volatility: float | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate if rebalancing is safe to proceed."""
        return self.risk_manager.validate_rebalancing_safety(portfolio_config, rebalancing_result, market_volatility)


# Re-exports for backward compatibility
__all__ = [
    "InsufficientPriceDataError",
    "OptimizationFailedError",
    "PortfolioRebalancingError",
    "PortfolioRebalancingOrchestrator",
]
