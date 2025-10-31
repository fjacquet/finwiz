"""
Portfolio rebalancing orchestrator for FinWiz.

This module provides the main orchestration class that coordinates all components
of the portfolio rebalancing system including price data retrieval, portfolio
analysis, optimization, and report generation.
"""

from datetime import datetime, timedelta
from typing import Any

from finwiz.orchestrators.rebalancing_calculations import RebalancingCalculator
from finwiz.orchestrators.rebalancing_constraints import RebalancingConstraintManager
from finwiz.orchestrators.rebalancing_optimization import OptimizationFailedError, RebalancingOptimizer
from finwiz.orchestrators.rebalancing_reporting import RebalancingReportGenerator
from finwiz.orchestrators.rebalancing_utils import InsufficientPriceDataError, PortfolioRebalancingError, RebalancingUtils
from finwiz.quantitative.rebalancing_engine import RebalancingEngine
from finwiz.quantitative.risk_manager import RiskManager
from finwiz.schemas.portfolio_rebalancing import (
    PortfolioConfiguration,
    RebalancingRecommendation,
    RebalancingResult,
)
from finwiz.tools.html_report_generator import HTMLReportGenerator
from finwiz.tools.logger import get_logger
from finwiz.tools.portfolio_price_service import PortfolioPriceService

logger = get_logger(__name__)


class PortfolioRebalancingOrchestrator:
    """
    Main orchestrator for portfolio rebalancing operations.

    Coordinates price data retrieval, portfolio analysis, trade optimization,
    and report generation to provide comprehensive rebalancing recommendations.
    """

    def __init__(
        self,
        price_service: PortfolioPriceService | None = None,
        rebalancing_engine: RebalancingEngine | None = None,
        report_generator: HTMLReportGenerator | None = None,
        risk_manager: RiskManager | None = None,
    ) -> None:
        """
        Initialize the portfolio rebalancing orchestrator.

        Args:
            price_service: Price data service instance
            rebalancing_engine: Rebalancing optimization engine instance
            report_generator: HTML report generator instance
            risk_manager: Risk management and safeguards instance

        """
        # Initialize specialized components
        self.utils = RebalancingUtils(price_service)
        self.optimizer = RebalancingOptimizer(rebalancing_engine)
        self.constraint_manager = RebalancingConstraintManager(risk_manager)
        self.report_generator_service = RebalancingReportGenerator(report_generator)
        self.calculator = RebalancingCalculator()

        logger.info("Portfolio rebalancing orchestrator initialized with specialized components")

    async def rebalance_portfolio(self, portfolio_config: PortfolioConfiguration, portfolio_id: str | None = None) -> RebalancingResult:
        """
        Execute complete portfolio rebalancing workflow.

        Args:
            portfolio_config: Portfolio configuration with holdings and targets
            portfolio_id: Optional portfolio identifier

        Returns:
            RebalancingResult: Complete rebalancing analysis and recommendations

        Raises:
            PortfolioRebalancingError: If rebalancing workflow fails
            InsufficientPriceDataError: If price data is unavailable
            OptimizationFailedError: If optimization fails

        """
        logger.info(f"Starting portfolio rebalancing workflow for {len(portfolio_config.holdings)} holdings")

        try:
            # Step 1: Retrieve current market prices
            logger.info("Step 1: Retrieving current market prices")
            symbols = [holding.symbol for holding in portfolio_config.holdings]
            price_data = await self.utils.get_portfolio_prices(symbols)

            # Step 2: Analyze current portfolio
            logger.info("Step 2: Analyzing current portfolio composition")
            current_analysis = await self.utils.analyze_current_portfolio(portfolio_config, price_data)

            # Step 3: Identify rebalancing needs
            logger.info("Step 3: Identifying rebalancing needs")
            rebalancing_needs = self.utils.identify_rebalancing_needs(portfolio_config, current_analysis)

            # Step 4: Generate enhanced trade recommendations
            logger.info("Step 4: Generating enhanced trade recommendations")
            enhanced_recommendations, validation_errors = await self.optimizer.generate_enhanced_recommendations(portfolio_config, current_analysis, rebalancing_needs, price_data)

            if validation_errors:
                logger.warning(f"Trade validation errors: {validation_errors}")

            # Create optimized trades structure
            optimized_trades = self.optimizer.create_optimized_trades_from_recommendations(enhanced_recommendations)

            # Step 5: Calculate projected portfolio state
            logger.info("Step 5: Calculating projected portfolio state")
            projected_analysis = await self.calculator.calculate_projected_portfolio(portfolio_config, current_analysis, optimized_trades.trades, price_data)

            # Step 6: Perform cost analysis
            logger.info("Step 6: Performing cost analysis")
            cost_analysis = self.calculator.calculate_cost_analysis(optimized_trades, current_analysis.total_value)

            # Step 7: Calculate risk metrics
            logger.info("Step 7: Calculating risk metrics")
            current_risk_score, projected_risk_score = self.calculator.calculate_risk_scores(current_analysis, projected_analysis)

            # Step 8: Generate execution summary
            logger.info("Step 8: Generating execution summary")
            execution_summary = self.calculator.generate_execution_summary(optimized_trades, portfolio_config)

            # Step 9: Create preliminary result for risk assessment
            preliminary_result = RebalancingResult(
                analysis_timestamp=datetime.now(),
                portfolio_id=portfolio_id,
                current_portfolio=current_analysis,
                trade_recommendations=optimized_trades.trades,
                projected_portfolio=projected_analysis,
                cost_analysis=cost_analysis,
                current_risk_score=current_risk_score,
                projected_risk_score=projected_risk_score,
                risk_improvement=current_risk_score - projected_risk_score,
                execution_summary=execution_summary,
                overall_recommendation=RebalancingRecommendation.REBALANCE_NOW,  # Temporary
                next_review_date=datetime.now() + timedelta(days=30),  # Temporary
            )

            # Step 10: Perform risk assessment and determine final recommendation
            logger.info("Step 9: Performing risk assessment and determining recommendation")
            risk_assessment = await self.constraint_manager.assess_rebalancing_risks(portfolio_config, preliminary_result)
            is_safe, blocking_issues = await self.constraint_manager.validate_rebalancing_safety(portfolio_config, preliminary_result)

            if not is_safe:
                logger.warning(f"Rebalancing blocked due to safety concerns: {blocking_issues}")
                overall_recommendation = RebalancingRecommendation.MONITOR
                next_review_date = datetime.now() + timedelta(days=7)
            else:
                overall_recommendation, next_review_date = self.constraint_manager.determine_overall_recommendation(
                    rebalancing_needs, cost_analysis, current_risk_score, risk_assessment
                )

            # Create final result
            result = RebalancingResult(
                analysis_timestamp=datetime.now(),
                portfolio_id=portfolio_id,
                current_portfolio=current_analysis,
                trade_recommendations=optimized_trades.trades,
                projected_portfolio=projected_analysis,
                cost_analysis=cost_analysis,
                current_risk_score=current_risk_score,
                projected_risk_score=projected_risk_score,
                risk_improvement=current_risk_score - projected_risk_score,
                execution_summary=execution_summary,
                overall_recommendation=overall_recommendation,
                next_review_date=next_review_date,
            )

            logger.info(
                f"Portfolio rebalancing complete: {len(optimized_trades.trades)} trades, ${cost_analysis.total_transaction_costs:.2f} cost, {overall_recommendation} recommendation"
            )

            return result

        except Exception as e:
            if isinstance(e, (PortfolioRebalancingError, InsufficientPriceDataError, OptimizationFailedError)):
                raise
            logger.error(f"Unexpected error in rebalancing workflow: {e}")
            raise PortfolioRebalancingError(f"Rebalancing workflow failed: {e}") from e

    async def assess_rebalancing_risks(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
        market_volatility: float | None = None,
    ) -> Any:
        """Assess rebalancing risks for a given portfolio and rebalancing result."""
        return await self.constraint_manager.assess_rebalancing_risks(portfolio_config, rebalancing_result, market_volatility)

    async def validate_rebalancing_safety(
        self,
        portfolio_config: PortfolioConfiguration,
        rebalancing_result: RebalancingResult,
        market_volatility: float | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate if rebalancing is safe to proceed."""
        return await self.constraint_manager.validate_rebalancing_safety(portfolio_config, rebalancing_result, market_volatility)

    async def analyze_current_portfolio(self, portfolio_config: PortfolioConfiguration) -> Any:
        """Analyze current portfolio without generating trade recommendations."""
        logger.info("Analyzing current portfolio composition")

        try:
            symbols = [holding.symbol for holding in portfolio_config.holdings]
            price_data = await self.utils.get_portfolio_prices(symbols)
            analysis = await self.utils.analyze_current_portfolio(portfolio_config, price_data)

            logger.info(f"Portfolio analysis complete: ${analysis.total_value:,.2f} total value")
            return analysis

        except Exception as e:
            logger.error(f"Portfolio analysis failed: {e}")
            raise PortfolioRebalancingError(f"Portfolio analysis failed: {e}") from e

    async def generate_rebalancing_report(self, result: RebalancingResult, language: str = "en") -> str:
        """Generate comprehensive HTML rebalancing report."""
        return await self.report_generator_service.generate_rebalancing_report(result, language)
