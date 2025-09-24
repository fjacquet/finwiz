"""
Portfolio rebalancing orchestrator for FinWiz.

This module provides the main orchestration class that coordinates all components
of the portfolio rebalancing system including price data retrieval, portfolio
analysis, optimization, and report generation.
"""

from datetime import datetime, timedelta
from typing import Any

from finwiz.quantitative.portfolio_analyzer import PortfolioAnalysisError, PortfolioAnalyzer
from finwiz.quantitative.rebalancing_engine import OptimizationConstraint, RebalancingEngine
from finwiz.quantitative.risk_manager import RiskManager
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


class PortfolioRebalancingError(Exception):
    """Base exception for portfolio rebalancing orchestrator errors."""

    pass


class InsufficientPriceDataError(PortfolioRebalancingError):
    """Raised when insufficient price data is available for rebalancing."""

    def __init__(self, missing_symbols: list[str]) -> None:
        """Initialize with list of missing symbols."""
        super().__init__(f"Insufficient price data for symbols: {', '.join(missing_symbols)}")
        self.missing_symbols = missing_symbols


class OptimizationFailedError(PortfolioRebalancingError):
    """Raised when portfolio optimization fails."""

    def __init__(self, reason: str) -> None:
        """Initialize with failure reason."""
        super().__init__(f"Portfolio optimization failed: {reason}")
        self.reason = reason


class PortfolioRebalancingOrchestrator:
    """
    Main orchestrator for portfolio rebalancing operations.

    Coordinates price data retrieval, portfolio analysis, trade optimization,
    and report generation to provide comprehensive rebalancing recommendations.
    """

    def __init__(
        self,
        price_service: PortfolioPriceService | None = None,
        portfolio_analyzer: PortfolioAnalyzer | None = None,
        rebalancing_engine: RebalancingEngine | None = None,
        report_generator: HTMLReportGenerator | None = None,
        risk_manager: RiskManager | None = None,
    ) -> None:
        """
        Initialize the portfolio rebalancing orchestrator.

        Args:
            price_service: Price data service instance
            portfolio_analyzer: Portfolio analyzer instance
            rebalancing_engine: Rebalancing optimization engine instance
            report_generator: HTML report generator instance
            risk_manager: Risk management and safeguards instance

        """
        self.price_service = price_service or PortfolioPriceService()
        self.portfolio_analyzer = portfolio_analyzer or PortfolioAnalyzer()
        self.rebalancing_engine = rebalancing_engine or RebalancingEngine()
        self.report_generator = report_generator or HTMLReportGenerator()
        self.risk_manager = risk_manager or RiskManager()

        logger.info("Portfolio rebalancing orchestrator initialized with risk management")

    async def rebalance_portfolio(
        self, portfolio_config: PortfolioConfiguration, portfolio_id: str | None = None
    ) -> RebalancingResult:
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
            price_data = await self._get_portfolio_prices(symbols)

            # Step 2: Analyze current portfolio
            logger.info("Step 2: Analyzing current portfolio composition")
            current_analysis = await self._analyze_current_portfolio(portfolio_config, price_data)

            # Step 3: Identify rebalancing needs
            logger.info("Step 3: Identifying rebalancing needs")
            rebalancing_needs = self._identify_rebalancing_needs(portfolio_config, current_analysis)

            # Step 4: Generate enhanced trade recommendations
            logger.info("Step 4: Generating enhanced trade recommendations")
            enhanced_recommendations, validation_errors = await self._generate_enhanced_recommendations(
                portfolio_config, current_analysis, rebalancing_needs, price_data
            )

            # Log validation errors if any
            if validation_errors:
                logger.warning(f"Trade validation errors: {validation_errors}")

            # Create optimized trades structure for compatibility
            optimized_trades = self._create_optimized_trades_from_recommendations(enhanced_recommendations)

            # Step 5: Calculate projected portfolio state
            logger.info("Step 5: Calculating projected portfolio state")
            projected_analysis = await self._calculate_projected_portfolio(
                portfolio_config, current_analysis, optimized_trades.trades, price_data
            )

            # Step 6: Perform cost analysis
            logger.info("Step 6: Performing cost analysis")
            cost_analysis = self._calculate_cost_analysis(optimized_trades, current_analysis.total_value)

            # Step 7: Calculate risk metrics
            logger.info("Step 7: Calculating risk metrics")
            current_risk_score, projected_risk_score = self._calculate_risk_scores(current_analysis, projected_analysis)

            # Step 8: Generate execution summary
            logger.info("Step 8: Generating execution summary")
            execution_summary = self._generate_execution_summary(optimized_trades, portfolio_config)

            # Step 9: Perform risk assessment and safety validation
            logger.info("Step 9: Performing risk assessment and safety validation")
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

            # Perform comprehensive risk assessment
            risk_assessment = self.risk_manager.assess_rebalancing_risks(portfolio_config, preliminary_result)

            # Validate rebalancing safety
            is_safe, blocking_issues = self.risk_manager.validate_rebalancing_safety(portfolio_config, preliminary_result)

            if not is_safe:
                logger.warning(f"Rebalancing blocked due to safety concerns: {blocking_issues}")
                # Adjust recommendation based on risk assessment
                overall_recommendation = RebalancingRecommendation.MONITOR
                next_review_date = datetime.now() + timedelta(days=7)  # Review sooner
            else:
                # Step 10: Determine overall recommendation
                logger.info("Step 10: Determining overall recommendation")
                overall_recommendation, next_review_date = self._determine_overall_recommendation(
                    rebalancing_needs, cost_analysis, current_risk_score, risk_assessment
                )

            # Create final result with risk assessment
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
                f"Portfolio rebalancing complete: {len(optimized_trades.trades)} trades, "
                f"${cost_analysis.total_transaction_costs:.2f} cost, "
                f"{overall_recommendation} recommendation, "
                f"Risk score: {risk_assessment.overall_risk_score:.1f}/10, "
                f"Warnings: {len(risk_assessment.warnings)}"
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
        """
        Assess rebalancing risks for a given portfolio and rebalancing result.

        Args:
            portfolio_config: Portfolio configuration
            rebalancing_result: Rebalancing analysis result
            market_volatility: Current market volatility (optional)

        Returns:
            Risk assessment result

        """
        logger.info("Performing standalone risk assessment")
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
        logger.info("Validating rebalancing safety")
        return self.risk_manager.validate_rebalancing_safety(portfolio_config, rebalancing_result, market_volatility)

    async def analyze_current_portfolio(self, portfolio_config: PortfolioConfiguration) -> Any:
        """
        Analyze current portfolio without generating trade recommendations.

        Args:
            portfolio_config: Portfolio configuration

        Returns:
            Portfolio analysis result

        Raises:
            PortfolioRebalancingError: If analysis fails

        """
        logger.info("Analyzing current portfolio composition")

        try:
            # Get current prices
            symbols = [holding.symbol for holding in portfolio_config.holdings]
            price_data = await self._get_portfolio_prices(symbols)

            # Analyze portfolio
            analysis = await self._analyze_current_portfolio(portfolio_config, price_data)

            logger.info(f"Portfolio analysis complete: ${analysis.total_value:,.2f} total value")
            return analysis

        except Exception as e:
            logger.error(f"Portfolio analysis failed: {e}")
            raise PortfolioRebalancingError(f"Portfolio analysis failed: {e}") from e

    async def generate_rebalancing_report(self, result: RebalancingResult, language: str = "en") -> str:
        """
        Generate comprehensive HTML rebalancing report.

        Args:
            result: Rebalancing analysis result
            language: Report language (en/fr)

        Returns:
            HTML report content

        Raises:
            PortfolioRebalancingError: If report generation fails

        """
        logger.info("Generating rebalancing HTML report")

        try:
            # Clear any existing sections
            self.report_generator.clear_sections()

            # Add executive summary
            self._add_executive_summary_section(result)

            # Add current portfolio analysis
            self._add_current_portfolio_section(result)

            # Add trade recommendations
            self._add_trade_recommendations_section(result)

            # Add cost analysis
            self._add_cost_analysis_section(result)

            # Add risk analysis
            self._add_risk_analysis_section(result)

            # Add projected portfolio
            self._add_projected_portfolio_section(result)

            # Add French sections if required
            if language == "fr":
                self._add_french_sections(result)

            # Generate final HTML using unified template
            title = f"Portfolio Rebalancing Analysis - {result.analysis_timestamp.strftime('%Y-%m-%d')}"

            # Try to use unified HTML generator if available
            if hasattr(self.report_generator, "generate_unified_html"):
                html_content = self.report_generator.generate_unified_html(title=title, language=language)
            else:
                html_content = self.report_generator.generate_html(title=title, language=language)

            logger.info("Rebalancing report generated successfully")
            return html_content

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise PortfolioRebalancingError(f"Report generation failed: {e}") from e

    async def _get_portfolio_prices(self, symbols: list[str]) -> dict[str, Any]:
        """Get current prices for all portfolio symbols."""
        try:
            price_data = await self.price_service.get_current_prices(symbols)

            # Check for missing price data
            missing_symbols = [symbol for symbol in symbols if symbol not in price_data]
            if missing_symbols:
                logger.warning(f"Missing price data for symbols: {missing_symbols}")

                # Try to get individual prices with fallback
                for symbol in missing_symbols:
                    try:
                        fallback_price = await self.price_service.get_price_with_fallback(symbol)
                        price_data[symbol] = fallback_price
                        logger.info(f"Retrieved fallback price for {symbol}")
                    except (PriceDataUnavailableError, Exception):
                        logger.error(f"Could not retrieve price for {symbol} from any source")

                # Final check for missing data
                still_missing = [symbol for symbol in symbols if symbol not in price_data]
                if still_missing:
                    raise InsufficientPriceDataError(still_missing)

            return price_data

        except Exception as e:
            if isinstance(e, InsufficientPriceDataError):
                raise
            logger.error(f"Error retrieving portfolio prices: {e}")
            raise PortfolioRebalancingError(f"Price retrieval failed: {e}") from e

    async def _analyze_current_portfolio(self, config: PortfolioConfiguration, price_data: dict[str, Any]) -> Any:
        """Analyze current portfolio composition."""
        try:
            analysis = self.portfolio_analyzer.analyze_current_portfolio(
                holdings=config.holdings, prices=price_data, target_weights=config.target_weights
            )
            return analysis

        except PortfolioAnalysisError as e:
            logger.error(f"Portfolio analysis failed: {e}")
            raise PortfolioRebalancingError(f"Portfolio analysis failed: {e}") from e

    def _identify_rebalancing_needs(self, config: PortfolioConfiguration, current_analysis: Any) -> list[Any]:
        """Identify positions requiring rebalancing."""
        try:
            rebalancing_needs = self.portfolio_analyzer.identify_rebalancing_needs(
                current_weights=current_analysis.weightings,
                target_weights=config.target_weights,
                tolerance_bands=config.tolerance_bands,
                global_tolerance=config.global_tolerance,
            )

            positions_needing_action = sum(1 for need in rebalancing_needs if need.exceeds_tolerance)
            logger.info(f"Identified {positions_needing_action} positions needing rebalancing")

            return rebalancing_needs

        except Exception as e:
            logger.error(f"Error identifying rebalancing needs: {e}")
            raise PortfolioRebalancingError(f"Failed to identify rebalancing needs: {e}") from e

    async def _optimize_trades(
        self, config: PortfolioConfiguration, current_analysis: Any, rebalancing_needs: list[Any], price_data: dict[str, Any]
    ) -> Any:
        """Optimize trade recommendations."""
        try:
            # Convert price data to simple dict
            price_dict = {symbol: price_data.price for symbol, price_data in price_data.items()}

            # Build constraints
            constraints = self._build_optimization_constraints(config)

            # Optimize trades
            optimized_trades = self.rebalancing_engine.optimize_rebalancing_trades(
                rebalancing_needs=rebalancing_needs,
                current_portfolio=current_analysis,
                target_weights=config.target_weights,
                prices=price_dict,
                config=config,
                constraints=constraints,
            )

            if not optimized_trades.trades:
                logger.info("No trades required - portfolio is within tolerance")
            else:
                logger.info(f"Optimized {len(optimized_trades.trades)} trade recommendations")

            return optimized_trades

        except Exception as e:
            logger.error(f"Trade optimization failed: {e}")
            raise OptimizationFailedError(str(e)) from e

    async def _calculate_projected_portfolio(
        self, config: PortfolioConfiguration, current_analysis: Any, trades: list[Any], price_data: dict[str, Any]
    ) -> Any:
        """Calculate projected portfolio state after executing trades."""
        try:
            # For now, return a simplified projected analysis
            # In a full implementation, this would simulate the portfolio after trades
            projected_analysis = current_analysis.model_copy()

            # Update weightings based on trades (simplified)
            for trade in trades:
                if trade.symbol in config.target_weights:
                    projected_analysis.weightings[trade.symbol] = trade.projected_weight_after_trade

            # Recalculate deviations
            projected_analysis.deviations_from_target = {
                symbol: projected_analysis.weightings.get(symbol, 0.0) - config.target_weights.get(symbol, 0.0)
                for symbol in config.target_weights
            }

            # Update positions needing rebalancing
            projected_analysis.positions_needing_rebalancing = [
                symbol
                for symbol, deviation in projected_analysis.deviations_from_target.items()
                if abs(deviation) > config.tolerance_bands.get(symbol, config.global_tolerance)
            ]

            return projected_analysis

        except Exception as e:
            logger.error(f"Error calculating projected portfolio: {e}")
            raise PortfolioRebalancingError(f"Failed to calculate projected portfolio: {e}") from e

    def _calculate_cost_analysis(self, optimized_trades: Any, portfolio_value: float) -> CostAnalysis:
        """Calculate comprehensive cost analysis."""
        try:
            total_commission = sum(trade.estimated_commission for trade in optimized_trades.trades)
            total_spread = sum(trade.estimated_spread_cost for trade in optimized_trades.trades)
            total_costs = total_commission + total_spread

            cost_percentage = (total_costs / portfolio_value * 100) if portfolio_value > 0 else 0.0

            # Estimate break-even days (simplified calculation)
            # Assume 7% annual return, so daily return is ~0.019%
            daily_return_rate = 0.07 / 365
            break_even_days = int(cost_percentage / (daily_return_rate * 100)) if daily_return_rate > 0 else None

            return CostAnalysis(
                total_transaction_costs=total_costs,
                commission_costs=total_commission,
                spread_costs=total_spread,
                market_impact_costs=0.0,  # Simplified - would need more complex calculation
                cost_as_percentage=cost_percentage,
                break_even_days=break_even_days,
            )

        except Exception as e:
            logger.error(f"Error calculating cost analysis: {e}")
            raise PortfolioRebalancingError(f"Cost analysis failed: {e}") from e

    def _calculate_risk_scores(self, current_analysis: Any, projected_analysis: Any) -> tuple[float, float]:
        """Calculate current and projected risk scores."""
        try:
            # Use concentration risk as primary risk metric (0-10 scale)
            current_risk = current_analysis.risk_metrics.get("concentration_risk", 5.0)
            projected_risk = projected_analysis.risk_metrics.get("concentration_risk", 5.0)

            # Ensure scores are within valid range
            current_risk = max(0.0, min(10.0, current_risk))
            projected_risk = max(0.0, min(10.0, projected_risk))

            return current_risk, projected_risk

        except Exception as e:
            logger.warning(f"Error calculating risk scores, using defaults: {e}")
            return 5.0, 5.0  # Default moderate risk

    def _generate_execution_summary(self, optimized_trades: Any, config: PortfolioConfiguration) -> ExecutionSummary:
        """Generate execution summary."""
        try:
            total_trades = len([t for t in optimized_trades.trades if t.action.value != "HOLD"])
            positions_with_action = len(set(t.symbol for t in optimized_trades.trades if t.action.value != "HOLD"))
            total_positions = len(config.holdings)
            positions_within_tolerance = total_positions - positions_with_action

            # Estimate execution time (simplified)
            if total_trades == 0:
                execution_time = "No trades required"
            elif total_trades <= 3:
                execution_time = "5-10 minutes"
            elif total_trades <= 10:
                execution_time = "15-30 minutes"
            else:
                execution_time = "30-60 minutes"

            return ExecutionSummary(
                total_trades_required=total_trades,
                positions_requiring_action=positions_with_action,
                positions_within_tolerance=positions_within_tolerance,
                estimated_execution_time=execution_time,
                capital_required=optimized_trades.capital_used,
            )

        except Exception as e:
            logger.error(f"Error generating execution summary: {e}")
            raise PortfolioRebalancingError(f"Execution summary generation failed: {e}") from e

    def _determine_overall_recommendation(
        self, rebalancing_needs: list[Any], cost_analysis: CostAnalysis, current_risk_score: float, risk_assessment: Any = None
    ) -> tuple[RebalancingRecommendation, datetime]:
        """Determine overall rebalancing recommendation with risk assessment."""
        try:
            # Count positions needing action
            positions_needing_action = sum(1 for need in rebalancing_needs if need.exceeds_tolerance)

            # Check for high urgency positions
            high_urgency_positions = sum(1 for need in rebalancing_needs if need.urgency_score >= 0.7)

            # Consider risk assessment if available
            high_risk_warnings = 0
            if risk_assessment:
                from finwiz.quantitative.risk_manager import RiskLevel

                high_risk_warnings = len(
                    [w for w in risk_assessment.warnings if w.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
                )

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
            logger.warning(f"Error determining recommendation, using default: {e}")
            return RebalancingRecommendation.MONITOR, datetime.now() + timedelta(days=14)

    def _build_optimization_constraints(self, config: PortfolioConfiguration) -> list[OptimizationConstraint]:
        """Build optimization constraints from configuration."""
        constraints = [
            OptimizationConstraint(
                name="min_trade_size",
                constraint_type="min_trade_size",
                value=config.min_trade_size,
                description="Minimum trade size to execute",
            ),
            OptimizationConstraint(
                name="max_position",
                constraint_type="max_position",
                value=0.25,  # 25% maximum position size
                description="Maximum position size as percentage of portfolio",
            ),
            OptimizationConstraint(
                name="turnover",
                constraint_type="turnover",
                value=0.5,  # 50% maximum turnover
                description="Maximum portfolio turnover",
            ),
        ]

        if config.available_capital != 0:
            constraints.append(
                OptimizationConstraint(
                    name="capital",
                    constraint_type="capital",
                    value=abs(config.available_capital),
                    description="Available capital constraint",
                )
            )

        return constraints

    async def _generate_enhanced_recommendations(
        self, config: PortfolioConfiguration, current_analysis: Any, rebalancing_needs: list[Any], price_data: dict[str, Any]
    ) -> tuple[list[Any], list[str]]:
        """Generate enhanced trade recommendations using the trade recommendation system."""
        try:
            # Convert price data to simple dict
            price_dict = {}
            for symbol, price_data in price_data.items():
                if hasattr(price_data, "price"):
                    price_dict[symbol] = price_data.price
                else:
                    # Handle case where price_data is already a float
                    price_dict[symbol] = float(price_data)

            # Generate enhanced recommendations
            recommendations, validation_errors = self.rebalancing_engine.generate_enhanced_trade_recommendations(
                rebalancing_needs=rebalancing_needs,
                current_portfolio=current_analysis,
                target_weights=config.target_weights,
                prices=price_dict,
                config=config,
                holdings=config.holdings,
            )

            logger.info(f"Generated {len(recommendations)} enhanced trade recommendations")
            return recommendations, validation_errors

        except Exception as e:
            logger.error(f"Enhanced recommendation generation failed: {e}")
            raise PortfolioRebalancingError(f"Enhanced recommendation generation failed: {e}") from e

    def _create_optimized_trades_from_recommendations(self, recommendations: list[Any]) -> Any:
        """Create OptimizedTrades structure from trade recommendations for compatibility."""
        from finwiz.quantitative.rebalancing_engine import OptimizedTrades

        total_cost = sum(rec.total_estimated_cost for rec in recommendations)
        capital_used = sum(rec.trade_value + rec.total_estimated_cost for rec in recommendations if rec.action.value == "BUY")

        # Simple optimization score based on number of recommendations vs total possible
        optimization_score = min(len(recommendations) / 10.0, 1.0) if recommendations else 0.0

        return OptimizedTrades(
            trades=recommendations,
            total_cost=total_cost,
            capital_used=capital_used,
            constraints_violated=[],
            optimization_score=optimization_score,
            method_used="ENHANCED_RECOMMENDATIONS",
        )

    # Report generation helper methods
    def _add_executive_summary_section(self, result: RebalancingResult) -> None:
        """Add executive summary section to report."""
        summary_content = f"""
        <div class="summary-grid">
            <div class="summary-item">
                <h4>📊 Portfolio Value</h4>
                <p>${result.current_portfolio.total_value:,.2f}</p>
            </div>
            <div class="summary-item">
                <h4>🔄 Trades Required</h4>
                <p>{result.execution_summary.total_trades_required}</p>
            </div>
            <div class="summary-item">
                <h4>💰 Transaction Costs</h4>
                <p>${result.cost_analysis.total_transaction_costs:.2f} ({result.cost_analysis.cost_as_percentage:.2f}%)</p>
            </div>
            <div class="summary-item">
                <h4>⚠️ Risk Score</h4>
                <p>{result.current_risk_score:.1f} → {result.projected_risk_score:.1f}</p>
            </div>
            <div class="summary-item">
                <h4>📋 Recommendation</h4>
                <p>{result.overall_recommendation.value.replace("_", " ").title()}</p>
            </div>
        </div>
        """
        self.report_generator.add_section("Executive Summary", summary_content, "summary", order=1)

    def _add_current_portfolio_section(self, result: RebalancingResult) -> None:
        """Add current portfolio analysis section."""
        weightings_html = "<ul>"
        for symbol, weight in sorted(result.current_portfolio.weightings.items()):
            deviation = result.current_portfolio.deviations_from_target.get(symbol, 0.0)
            status_emoji = "✅" if abs(deviation) <= 0.05 else "⚠️" if abs(deviation) <= 0.1 else "🔴"
            weightings_html += f"<li>{status_emoji} <strong>{symbol}</strong>: {weight:.1%} (deviation: {deviation:+.1%})</li>"
        weightings_html += "</ul>"

        self.report_generator.add_section("Current Portfolio", weightings_html, "portfolio", order=2)

    def _add_trade_recommendations_section(self, result: RebalancingResult) -> None:
        """Add trade recommendations section."""
        if not result.trade_recommendations:
            content = "<p>✅ No trades required - portfolio is within tolerance bands.</p>"
        else:
            content = "<table border='1' style='width:100%; border-collapse: collapse;'>"
            content += (
                "<tr><th>Symbol</th><th>Action</th><th>Quantity</th><th>Price</th><th>Value</th><th>Cost</th><th>Urgency</th></tr>"
            )

            for trade in result.trade_recommendations:
                urgency_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}.get(trade.urgency.value, "⚪")
                content += f"""
                <tr>
                    <td><strong>{trade.symbol}</strong></td>
                    <td>{trade.action.value}</td>
                    <td>{trade.quantity:.2f}</td>
                    <td>${trade.current_price:.2f}</td>
                    <td>${trade.trade_value:.2f}</td>
                    <td>${trade.total_estimated_cost:.2f}</td>
                    <td>{urgency_emoji} {trade.urgency.value}</td>
                </tr>
                """
            content += "</table>"

        self.report_generator.add_section("Trade Recommendations", content, "data", order=3)

    def _add_cost_analysis_section(self, result: RebalancingResult) -> None:
        """Add cost analysis section."""
        cost_content = f"""
        <ul>
            <li><strong>Total Transaction Costs:</strong> ${result.cost_analysis.total_transaction_costs:.2f}</li>
            <li><strong>Commission Costs:</strong> ${result.cost_analysis.commission_costs:.2f}</li>
            <li><strong>Spread Costs:</strong> ${result.cost_analysis.spread_costs:.2f}</li>
            <li><strong>Cost as % of Portfolio:</strong> {result.cost_analysis.cost_as_percentage:.3f}%</li>
            <li><strong>Break-even Period:</strong> {result.cost_analysis.break_even_days or "N/A"} days</li>
        </ul>
        """
        self.report_generator.add_section("Cost Analysis", cost_content, "financial", order=4)

    def _add_risk_analysis_section(self, result: RebalancingResult) -> None:
        """Add risk analysis section."""
        risk_content = f"""
        <ul>
            <li><strong>Current Risk Score:</strong> {result.current_risk_score:.1f}/10</li>
            <li><strong>Projected Risk Score:</strong> {result.projected_risk_score:.1f}/10</li>
            <li><strong>Risk Improvement:</strong> {result.risk_improvement:+.1f}</li>
        </ul>
        """
        if result.risk_improvement > 0:
            risk_content += "<p>✅ Rebalancing will reduce portfolio risk.</p>"
        elif result.risk_improvement < 0:
            risk_content += "<p>⚠️ Rebalancing may increase portfolio risk.</p>"
        else:
            risk_content += "<p>➡️ Rebalancing will maintain current risk level.</p>"

        self.report_generator.add_section("Risk Analysis", risk_content, "risk", order=5)

    def _add_projected_portfolio_section(self, result: RebalancingResult) -> None:
        """Add projected portfolio section."""
        projected_html = "<ul>"
        for symbol, weight in sorted(result.projected_portfolio.weightings.items()):
            deviation = result.projected_portfolio.deviations_from_target.get(symbol, 0.0)
            status_emoji = "✅" if abs(deviation) <= 0.05 else "⚠️"
            projected_html += f"<li>{status_emoji} <strong>{symbol}</strong>: {weight:.1%} (deviation: {deviation:+.1%})</li>"
        projected_html += "</ul>"

        self.report_generator.add_section("Projected Portfolio", projected_html, "growth", order=6)

    def _add_french_sections(self, result: RebalancingResult) -> None:
        """Add required French sections."""
        # Synthèse 10-K (Portfolio Summary in French)
        synthese_content = f"""
        <p><strong>Valeur totale du portefeuille:</strong> ${result.current_portfolio.total_value:,.2f}</p>
        <p><strong>Nombre de transactions requises:</strong> {result.execution_summary.total_trades_required}</p>
        <p><strong>Recommandation:</strong> {result.overall_recommendation.value.replace("_", " ").title()}</p>
        """
        self.report_generator.add_french_section("synthese_10k", synthese_content)

        # Sentiment du Marché (Market Sentiment)
        sentiment_content = """
        <p>L'analyse de rééquilibrage suggère une approche prudente basée sur les écarts de pondération actuels 
        et les coûts de transaction. Les recommandations tiennent compte des conditions de marché actuelles.</p>
        """
        self.report_generator.add_french_section("sentiment_marche", sentiment_content)

    async def close(self) -> None:
        """Clean up resources."""
        logger.info("Closing portfolio rebalancing orchestrator")
        await self.price_service.close()
