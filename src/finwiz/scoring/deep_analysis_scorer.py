"""
Deep Analysis Scoring Engine.

Python-based scoring engine for deep analysis that replaces AI-based scoring
with deterministic, testable calculations. Provides composite scoring based on
fundamental, technical, and risk factors.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Literal

# Import the correct DeepAnalysisResult from flow_state
from finwiz.flow_state import DeepAnalysisResult

logger = logging.getLogger(__name__)


class DeepAnalysisScorer:
    """
    Python-based scoring engine for deep analysis.

    Replaces AI-based scoring with deterministic calculations:
    - 40% fundamental analysis (ROE, debt, growth)
    - 30% technical analysis (RSI, trend, momentum)
    - 30% risk assessment (volatility, drawdown, beta)
    """

    # Grade thresholds based on composite score (MORE DISCRIMINATING)
    # Changed from lenient scale (B at 65%) to stricter scale (B at 70%)
    # This ensures only truly exceptional investments get A+ grades
    GRADE_THRESHOLDS = {0.90: "A+", 0.80: "A", 0.70: "B", 0.60: "C", 0.50: "D", 0.0: "F"}

    # Recommendation thresholds (adjusted for new scale)
    BUY_THRESHOLD = 0.80  # A or better (raised from 0.70)
    SELL_THRESHOLD = 0.60  # Below C (raised from 0.50)

    def __init__(self) -> None:
        """Initialize the scoring engine."""
        self.logger = logger
        # Data quality tracking (Task 3.2)
        self._data_quality_metrics = None
        self._current_ticker = None
        # Data lineage tracking (Task 9.2)
        self._lineage_tracker = None

    def calculate_composite_score(self, ticker: str, asset_class: str, data: dict[str, Any]) -> DeepAnalysisResult:
        """
        Calculate composite score from fundamental, technical, and risk factors.

        Args:
            ticker: Asset ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            data: Dictionary containing all analysis data

        Returns:
            DeepAnalysisResult with scores, grade, and recommendation

        Raises:
            CriticalFieldError: If critical fields are missing (fail fast)

        """
        from finwiz.config.critical_fields_config import (
            CriticalFieldError,
            validate_critical_fields,
        )
        from finwiz.schemas.data_lineage import DataLineage
        from finwiz.utils.data_quality_metrics import DataQualityMetrics

        try:
            # Initialize data quality tracking (Task 3.2)
            self._data_quality_metrics = DataQualityMetrics()
            self._current_ticker = ticker

            # Initialize data lineage tracking (Task 9.2)
            self._lineage_tracker = DataLineage(
                ticker=ticker,
                asset_class=asset_class,
                scorer_version="1.0.0",  # TODO: Get from package version
                formula_version="1.0.0",
            )

            # CRITICAL: Validate all critical fields are present BEFORE scoring
            # This will raise CriticalFieldError if any critical field is missing
            try:
                validate_critical_fields(ticker, asset_class, data)
                self.logger.info(f"✅ All critical fields present for {ticker}")
            except CriticalFieldError as e:
                self.logger.error(
                    f"❌ CRITICAL FIELDS MISSING for {ticker}: {e.missing_fields}\n"
                    f"   Cannot proceed with analysis - would be based on assumptions.\n"
                    f"   Recommendation: Check API connectivity and data sources."
                )
                raise

            # Define expected fields based on asset class
            expected_fields = self._get_expected_fields(asset_class)
            self._data_quality_metrics.set_expected_fields(expected_fields)

            # Calculate component scores (with data quality tracking)
            fundamental_score, fundamental_details = self.calculate_fundamental_score(asset_class, data)
            technical_score, technical_details = self.calculate_technical_score(data)
            risk_score, risk_details = self.calculate_risk_score(data)

            # Calculate weighted composite score (40% + 30% + 30%)
            composite_score = 0.40 * fundamental_score + 0.30 * technical_score + 0.30 * risk_score

            # Track composite score calculation in lineage (Task 9.2)
            self._lineage_tracker.add_calculation(
                step_id="composite_score",
                step_name="composite_score",
                inputs={
                    "fundamental_score": fundamental_score,
                    "technical_score": technical_score,
                    "risk_score": risk_score,
                },
                calculation="Weighted average of component scores",
                formula="0.40 * fundamental + 0.30 * technical + 0.30 * risk",
                output=composite_score,
                metadata={"weights": {"fundamental": 0.40, "technical": 0.30, "risk": 0.30}},
            )

            # Assign grade and recommendation
            grade = self.assign_grade(composite_score)

            # Track grade assignment in lineage (Task 9.2)
            self._lineage_tracker.add_calculation(
                step_id="grade_assignment",
                step_name="grade",
                inputs={"composite_score": composite_score},
                calculation="Grade assignment based on composite score",
                formula=f"grading_scale[{composite_score:.3f}]",
                output=grade,
                metadata={"grading_scale": self.GRADE_THRESHOLDS},
            )
            recommendation = self.generate_recommendation(composite_score, grade)
            confidence = self._calculate_confidence(fundamental_score, technical_score, risk_score, data)
            rationale = self.generate_rationale(ticker, asset_class, composite_score, grade, fundamental_details, technical_details, risk_details)

            # Get data quality summary
            data_quality_summary = self._data_quality_metrics.get_summary()

            # Log data quality warnings if needed
            quality_level = data_quality_summary["quality_level"]
            if quality_level == "low":
                self.logger.warning(
                    f"⚠️ Low data quality for {ticker}: completeness={data_quality_summary['completeness_score']:.1%}, quality={data_quality_summary['quality_score']:.1%}"
                )

            # Finalize lineage with final values (Task 9.2)
            self._lineage_tracker.final_values = {
                "composite_score": composite_score,
                "grade": grade,
                "recommendation": recommendation,
                "fundamental_score": fundamental_score,
                "technical_score": technical_score,
                "risk_score": risk_score,
            }

            result = DeepAnalysisResult(
                ticker=ticker,
                asset_class=asset_class,
                crew_name="python_scorer",
                composite_score=composite_score,
                grade=grade,
                recommendation=recommendation,
                rationale=rationale,
                risk_details=risk_details,
                fundamental_score=fundamental_score,
                technical_score=technical_score,
                risk_score=risk_score,
                fundamental_details=fundamental_details,  # Include breakdown for debugging
                technical_details=technical_details,  # Include breakdown for debugging
                data_freshness_hours=0.0,  # Fresh data from Python calculation
                confidence_level=confidence,
                warnings=[],
                cached=False,
                data_quality=data_quality_summary,  # Task 2.1: Include data quality metrics
                lineage=self._lineage_tracker.model_dump(),  # Task 9.2: Include complete data lineage
            )

            # Log successful scoring with data quality info
            self.logger.info(
                f"✅ Python scoring completed for {ticker}: "
                f"Grade {grade} ({composite_score:.3f}), "
                f"Recommendation {recommendation} ({confidence:.1%} confidence), "
                f"Quality: {quality_level} ({data_quality_summary['completeness_score']:.1%} complete)"
            )

            return result

        except CriticalFieldError as e:
            # Critical field missing - DO NOT return fallback result
            # Re-raise to let caller handle (should skip this holding)
            self.logger.error(
                f"❌ ANALYSIS FAILED for {ticker}: Missing critical fields {e.missing_fields}\n"
                f"   This holding will be SKIPPED to avoid decisions based on assumptions."
            )
            raise
        except Exception as e:
            self.logger.error(f"Error calculating composite score for {ticker}: {e}")
            # Return default low score on error (non-critical errors only)
            return self._create_error_result(ticker, asset_class, str(e))

    def analyze_and_export(self, ticker: str, asset_class: str, collected_data: dict[str, Any], session_id: str = "default") -> tuple[DeepAnalysisResult, dict[str, Any]]:
        """
        Complete analysis pipeline: scoring + detailed analysis + crew export.

        This is the main entry point for the Python scoring approach.

        Args:
            ticker: Asset ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            collected_data: Raw data from data collection task
            session_id: Session identifier for file paths

        Returns:
            Tuple of (DeepAnalysisResult, crew_export_dict)

        """
        import time

        start_time = time.time()

        try:
            # Step 1: Calculate scores using Python algorithms
            result = self.calculate_composite_score(ticker, asset_class, collected_data)

            # Step 2: Create comprehensive detailed analysis preserving all data
            detailed_analysis = self.create_detailed_analysis(ticker, asset_class, collected_data, result)

            # Step 3: Create crew export dict
            crew_export_dict = self.create_crew_export(result, detailed_analysis, session_id)

            # Calculate performance metrics
            execution_time = time.time() - start_time

            # Log performance achievements
            self.logger.info(
                f"🚀 PYTHON SCORING PERFORMANCE for {ticker}:\n"
                f"  ✅ Execution time: {execution_time:.2f}s (target: 10-30s)\n"
                f"  ✅ LLM calls: 0 (target: 0)\n"
                f"  ✅ Cost: $0.00 (target: $0.00)\n"
                f"  ✅ Data preservation: ALL raw metrics preserved\n"
                f"  ✅ Deterministic: Same input = same output"
            )

            return result, crew_export_dict

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error in analyze_and_export for {ticker}: {e}")

            # Create error result and export
            error_result = self._create_error_result(ticker, asset_class, str(e))
            error_detailed_analysis = {
                "error": str(e),
                "execution_time": execution_time,
                "ticker": ticker,
                "asset_class": asset_class,
            }
            error_export = self.create_crew_export(error_result, error_detailed_analysis, session_id)

            return error_result, error_export

    def calculate_fundamental_score(self, asset_class: str, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate fundamental score based on asset class.

        For stocks: ROE, debt/equity, revenue growth, profit margins
        For ETFs: expense ratio, tracking error, AUM, diversification
        For crypto: market cap, volume, adoption metrics, tokenomics

        Returns:
            Tuple of (score, details_dict)

        """
        details = {}

        if asset_class == "stock":
            return self._calculate_stock_fundamental_score(data, details)
        elif asset_class == "etf":
            return self._calculate_etf_fundamental_score(data, details)
        elif asset_class == "crypto":
            return self._calculate_crypto_fundamental_score(data, details)
        else:
            self.logger.warning(f"Unknown asset class: {asset_class}")
            return 0.5, {"error": f"Unknown asset class: {asset_class}"}

    def _calculate_stock_fundamental_score(self, data: dict[str, Any], details: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """Calculate fundamental score for stocks."""
        score = 0.5  # Base score

        # ROE (Return on Equity) - target 15%+
        roe = self._safe_get_float(data, "roe", 0.0)
        if roe >= 0.20:  # 20%+
            roe_score = 1.0
        elif roe >= 0.15:  # 15-20%
            roe_score = 0.8
        elif roe >= 0.10:  # 10-15%
            roe_score = 0.6
        elif roe >= 0.05:  # 5-10%
            roe_score = 0.4
        else:  # <5%
            roe_score = 0.2

        details["roe"] = roe
        details["roe_score"] = roe_score

        # Debt-to-Equity ratio - lower is better
        debt_equity = self._safe_get_float(data, "debt_to_equity", 1.0)
        if debt_equity <= 0.3:  # Very low debt
            debt_score = 1.0
        elif debt_equity <= 0.5:  # Low debt
            debt_score = 0.8
        elif debt_equity <= 1.0:  # Moderate debt
            debt_score = 0.6
        elif debt_equity <= 2.0:  # High debt
            debt_score = 0.4
        else:  # Very high debt
            debt_score = 0.2

        details["debt_to_equity"] = debt_equity
        details["debt_score"] = debt_score

        # Revenue growth - target 10%+
        revenue_growth = self._safe_get_float(data, "revenue_growth", 0.0)
        if revenue_growth >= 0.25:  # 25%+
            growth_score = 1.0
        elif revenue_growth >= 0.15:  # 15-25%
            growth_score = 0.8
        elif revenue_growth >= 0.10:  # 10-15%
            growth_score = 0.6
        elif revenue_growth >= 0.05:  # 5-10%
            growth_score = 0.4
        else:  # <5%
            growth_score = 0.2

        details["revenue_growth"] = revenue_growth
        details["growth_score"] = growth_score

        # Profit margin
        profit_margin = self._safe_get_float(data, "profit_margin", 0.0)
        if profit_margin >= 0.20:  # 20%+
            margin_score = 1.0
        elif profit_margin >= 0.15:  # 15-20%
            margin_score = 0.8
        elif profit_margin >= 0.10:  # 10-15%
            margin_score = 0.6
        elif profit_margin >= 0.05:  # 5-10%
            margin_score = 0.4
        else:  # <5%
            margin_score = 0.2

        details["profit_margin"] = profit_margin
        details["margin_score"] = margin_score

        # Weighted average (ROE 40%, Debt 30%, Growth 20%, Margin 10%)
        fundamental_score = 0.40 * roe_score + 0.30 * debt_score + 0.20 * growth_score + 0.10 * margin_score

        details["fundamental_score"] = fundamental_score
        return fundamental_score, details

    def _calculate_etf_fundamental_score(self, data: dict[str, Any], details: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """Calculate fundamental score for ETFs."""
        # Expense ratio - lower is better
        expense_ratio = self._safe_get_float(data, "expense_ratio", 1.0)
        
        # Log the actual value for debugging
        self.logger.info(f"ETF {self._current_ticker}: expense_ratio = {expense_ratio} (raw value)")
        
        # Thresholds for expense ratio (as decimal: 0.001 = 0.10%)
        if expense_ratio <= 0.001:  # 0.10% or less (excellent)
            expense_score = 1.0
        elif expense_ratio <= 0.0025:  # 0.10-0.25% (very good)
            expense_score = 0.8
        elif expense_ratio <= 0.005:  # 0.25-0.50% (good)
            expense_score = 0.6
        elif expense_ratio <= 0.01:  # 0.50-1.00% (acceptable)
            expense_score = 0.4
        else:  # >1.00% (high/poor)
            expense_score = 0.2

        details["expense_ratio"] = expense_ratio
        details["expense_score"] = expense_score
        
        self.logger.info(f"ETF {self._current_ticker}: expense_score = {expense_score}")

        # Tracking error - lower is better (optional field)
        # Use None as default to properly detect missing data
        tracking_error_raw = data.get("tracking_error")
        tracking_available = tracking_error_raw is not None
        
        if tracking_available:
            try:
                tracking_error = float(tracking_error_raw)
                # Log the actual value for debugging
                self.logger.info(f"ETF {self._current_ticker}: tracking_error = {tracking_error} (raw value)")
                
                # Thresholds for tracking error (as decimal: 0.002 = 0.20%)
                if tracking_error <= 0.002:  # 0.20% or less (excellent)
                    tracking_score = 1.0
                elif tracking_error <= 0.005:  # 0.20-0.50% (very good)
                    tracking_score = 0.8
                elif tracking_error <= 0.01:  # 0.50-1.00% (good)
                    tracking_score = 0.6
                elif tracking_error <= 0.02:  # 1.00-2.00% (acceptable)
                    tracking_score = 0.4
                else:  # >2.00% (high/poor)
                    tracking_score = 0.2
                
                self.logger.info(f"ETF {self._current_ticker}: tracking_score = {tracking_score}")
            except (ValueError, TypeError) as e:
                # Invalid tracking error value - use neutral score
                tracking_score = 0.5
                tracking_available = False
                self.logger.warning(f"⚠️ ETF {self._current_ticker}: Invalid tracking_error value '{tracking_error_raw}': {e}, using neutral score")
        else:
            # Tracking error not available - use neutral score
            tracking_error = None
            tracking_score = 0.5  # Neutral score when data unavailable
            self.logger.info(f"ETF {self._current_ticker}: tracking_error not available, using neutral score")

        details["tracking_error"] = tracking_error
        details["tracking_error_available"] = tracking_available
        details["tracking_score"] = tracking_score

        # AUM (Assets Under Management) - higher is better for liquidity (optional field)
        aum = self._safe_get_float(data, "aum", None)
        aum_available = aum is not None and aum > 0
        
        if aum_available:
            if aum >= 5e9:  # $5B+
                aum_score = 1.0
            elif aum >= 1e9:  # $1-5B
                aum_score = 0.8
            elif aum >= 500e6:  # $500M-1B
                aum_score = 0.6
            elif aum >= 100e6:  # $100-500M
                aum_score = 0.4
            else:  # <$100M
                aum_score = 0.2
        else:
            # AUM not available - use neutral score
            aum_score = 0.5  # Neutral score when data unavailable
            self.logger.warning(f"⚠️ ETF {self._current_ticker}: AUM not available, using neutral score")

        details["aum"] = aum
        details["aum_available"] = aum_available
        details["aum_score"] = aum_score

        # Weighted average - adjust weights based on data availability
        # Base: Expense 60%, Tracking 30%, AUM 10%
        # If tracking unavailable: Expense 70%, AUM 30%
        # If AUM unavailable: Expense 60%, Tracking 40%
        # If both unavailable: Expense 100%
        if tracking_available and aum_available:
            fundamental_score = 0.60 * expense_score + 0.30 * tracking_score + 0.10 * aum_score
        elif tracking_available:
            fundamental_score = 0.60 * expense_score + 0.40 * tracking_score
            self.logger.info(f"ETF {self._current_ticker}: AUM unavailable, adjusted weights (Expense 60%, Tracking 40%)")
        elif aum_available:
            fundamental_score = 0.70 * expense_score + 0.30 * aum_score
            self.logger.info(f"ETF {self._current_ticker}: Tracking error unavailable, adjusted weights (Expense 70%, AUM 30%)")
        else:
            fundamental_score = expense_score
            self.logger.warning(f"⚠️ ETF {self._current_ticker}: Only expense_ratio available, using 100% weight")

        details["fundamental_score"] = fundamental_score
        return fundamental_score, details

    def _calculate_crypto_fundamental_score(self, data: dict[str, Any], details: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """Calculate fundamental score for crypto."""
        # Market cap - higher is better for stability
        market_cap = self._safe_get_float(data, "market_cap", 0.0)
        if market_cap >= 100e9:  # $100B+
            cap_score = 1.0
        elif market_cap >= 10e9:  # $10-100B
            cap_score = 0.8
        elif market_cap >= 1e9:  # $1-10B
            cap_score = 0.6
        elif market_cap >= 100e6:  # $100M-1B
            cap_score = 0.4
        else:  # <$100M
            cap_score = 0.2

        details["market_cap"] = market_cap
        details["cap_score"] = cap_score

        # Daily volume - higher is better for liquidity
        volume_24h = self._safe_get_float(data, "volume_24h", 0.0)
        if volume_24h >= 1e9:  # $1B+
            volume_score = 1.0
        elif volume_24h >= 500e6:  # $500M-1B
            volume_score = 0.8
        elif volume_24h >= 100e6:  # $100-500M
            volume_score = 0.6
        elif volume_24h >= 10e6:  # $10-100M
            volume_score = 0.4
        else:  # <$10M
            volume_score = 0.2

        details["volume_24h"] = volume_24h
        details["volume_score"] = volume_score

        # Age/maturity - older is more stable
        age_years = self._safe_get_float(data, "age_years", 0.0)
        if age_years >= 5:  # 5+ years
            age_score = 1.0
        elif age_years >= 3:  # 3-5 years
            age_score = 0.8
        elif age_years >= 2:  # 2-3 years
            age_score = 0.6
        elif age_years >= 1:  # 1-2 years
            age_score = 0.4
        else:  # <1 year
            age_score = 0.2

        details["age_years"] = age_years
        details["age_score"] = age_score

        # Weighted average (Market Cap 50%, Volume 30%, Age 20%)
        fundamental_score = 0.50 * cap_score + 0.30 * volume_score + 0.20 * age_score

        details["fundamental_score"] = fundamental_score
        return fundamental_score, details

    def calculate_technical_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate technical score based on RSI, trend analysis, and momentum.

        Returns:
            Tuple of (score, details_dict)

        """
        details = {}

        # RSI (Relative Strength Index) - target 30-70 range
        rsi = self._safe_get_float(data, "rsi", 50.0)
        if 40 <= rsi <= 60:  # Neutral zone
            rsi_score = 1.0
        elif 30 <= rsi <= 70:  # Good range
            rsi_score = 0.8
        elif 20 <= rsi <= 80:  # Acceptable range
            rsi_score = 0.6
        elif 10 <= rsi <= 90:  # Warning range
            rsi_score = 0.4
        else:  # Extreme overbought/oversold
            rsi_score = 0.2

        details["rsi"] = rsi
        details["rsi_score"] = rsi_score

        # Trend analysis (moving averages)
        price = self._safe_get_float(data, "current_price", 100.0)
        ma_50 = self._safe_get_float(data, "moving_avg_50", price)
        ma_200 = self._safe_get_float(data, "moving_avg_200", price)

        # Price vs moving averages
        if price > ma_50 > ma_200:  # Strong uptrend
            trend_score = 1.0
            trend_direction = "strong_uptrend"
        elif price > ma_50 and price > ma_200:  # Uptrend
            trend_score = 0.8
            trend_direction = "uptrend"
        elif price > ma_200:  # Weak uptrend
            trend_score = 0.6
            trend_direction = "weak_uptrend"
        elif price < ma_50 and price < ma_200 and ma_50 < ma_200:  # Strong downtrend
            trend_score = 0.2
            trend_direction = "strong_downtrend"
        elif price < ma_50 or price < ma_200:  # Downtrend
            trend_score = 0.4
            trend_direction = "downtrend"
        else:  # Sideways
            trend_score = 0.5
            trend_direction = "sideways"

        details["current_price"] = price
        details["moving_avg_50"] = ma_50
        details["moving_avg_200"] = ma_200
        details["trend_score"] = trend_score
        details["trend_direction"] = trend_direction

        # MACD momentum
        macd = self._safe_get_float(data, "macd", 0.0)
        macd_signal = self._safe_get_float(data, "macd_signal", 0.0)
        macd_diff = macd - macd_signal

        if macd_diff > 0 and macd > 0:  # Strong bullish momentum
            momentum_score = 1.0
        elif macd_diff > 0:  # Bullish momentum
            momentum_score = 0.8
        elif abs(macd_diff) < 0.1:  # Neutral momentum
            momentum_score = 0.6
        elif macd_diff < 0:  # Bearish momentum
            momentum_score = 0.4
        else:  # Strong bearish momentum
            momentum_score = 0.2

        details["macd"] = macd
        details["macd_signal"] = macd_signal
        details["macd_diff"] = macd_diff
        details["momentum_score"] = momentum_score

        # Weighted average (RSI 40%, Trend 40%, Momentum 20%)
        technical_score = 0.40 * rsi_score + 0.40 * trend_score + 0.20 * momentum_score

        details["technical_score"] = technical_score
        return technical_score, details

    def calculate_risk_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate risk score (0-5 scale converted to 0-1, where 1 = low risk).

        Based on volatility, maximum drawdown, and beta.

        Returns:
            Tuple of (score, details_dict)

        """
        details = {}

        # Volatility - lower is better (annual volatility)
        volatility = self._safe_get_float(data, "volatility", 0.20)
        if volatility <= 0.10:  # 10% or less
            vol_score = 1.0
        elif volatility <= 0.15:  # 10-15%
            vol_score = 0.8
        elif volatility <= 0.25:  # 15-25%
            vol_score = 0.6
        elif volatility <= 0.40:  # 25-40%
            vol_score = 0.4
        else:  # >40%
            vol_score = 0.2

        details["volatility"] = volatility
        details["volatility_score"] = vol_score

        # Maximum drawdown - lower is better (negative values)
        max_drawdown = self._safe_get_float(data, "max_drawdown", -0.20)
        max_drawdown = abs(max_drawdown)  # Convert to positive for comparison

        if max_drawdown <= 0.10:  # 10% or less
            drawdown_score = 1.0
        elif max_drawdown <= 0.20:  # 10-20%
            drawdown_score = 0.8
        elif max_drawdown <= 0.35:  # 20-35%
            drawdown_score = 0.6
        elif max_drawdown <= 0.50:  # 35-50%
            drawdown_score = 0.4
        else:  # >50%
            drawdown_score = 0.2

        details["max_drawdown"] = -max_drawdown  # Store as negative
        details["drawdown_score"] = drawdown_score

        # Beta - closer to 1.0 is better for most assets
        beta = self._safe_get_float(data, "beta", 1.0)
        beta_deviation = abs(beta - 1.0)

        if beta_deviation <= 0.20:  # 0.8-1.2 range
            beta_score = 1.0
        elif beta_deviation <= 0.40:  # 0.6-1.4 range
            beta_score = 0.8
        elif beta_deviation <= 0.60:  # 0.4-1.6 range
            beta_score = 0.6
        elif beta_deviation <= 1.00:  # 0.0-2.0 range
            beta_score = 0.4
        else:  # >2.0 or negative
            beta_score = 0.2

        details["beta"] = beta
        details["beta_deviation"] = beta_deviation
        details["beta_score"] = beta_score

        # Weighted average (Volatility 50%, Drawdown 30%, Beta 20%)
        risk_score = 0.50 * vol_score + 0.30 * drawdown_score + 0.20 * beta_score

        details["risk_score"] = risk_score
        return risk_score, details

    def assign_grade(self, composite_score: float) -> str:
        """
        Assign letter grade based on composite score.

        Args:
            composite_score: Composite score (0.0 to 1.0)

        Returns:
            Letter grade (A+, A, B, C, D, F)

        """
        for threshold, grade in self.GRADE_THRESHOLDS.items():
            if composite_score >= threshold:
                return grade
        return "F"

    def generate_recommendation(self, composite_score: float, grade: str) -> Literal["BUY", "HOLD", "SELL"]:
        """
        Generate investment recommendation based on composite score and grade.

        Args:
            composite_score: Composite score (0.0 to 1.0)
            grade: Letter grade

        Returns:
            Investment recommendation

        """
        if composite_score >= self.BUY_THRESHOLD:  # A- or better
            return "BUY"
        elif composite_score <= self.SELL_THRESHOLD:  # Below C
            return "SELL"
        else:  # B to C range
            return "HOLD"

    def generate_rationale(
        self,
        ticker: str,
        asset_class: str,
        composite_score: float,
        grade: str,
        fundamental_details: dict[str, Any],
        technical_details: dict[str, Any],
        risk_details: dict[str, Any],
    ) -> str:
        """
        Generate template-based rationale for the recommendation.

        Args:
            ticker: Asset ticker
            asset_class: Asset class
            composite_score: Composite score
            grade: Letter grade
            fundamental_details: Fundamental analysis details
            technical_details: Technical analysis details
            risk_details: Risk analysis details

        Returns:
            Detailed rationale string

        """
        # Start with overall assessment
        rationale_parts = [f"{ticker} receives a {grade} grade with a composite score of {composite_score:.2f}."]

        # Fundamental analysis summary
        fund_score = fundamental_details.get("fundamental_score", 0.5)
        if asset_class == "stock":
            roe = fundamental_details.get("roe", 0.0)
            debt_equity = fundamental_details.get("debt_to_equity", 1.0)
            growth = fundamental_details.get("revenue_growth", 0.0)
            rationale_parts.append(
                f"Fundamental analysis (score: {fund_score:.2f}) shows ROE of {roe:.1%}, debt-to-equity of {debt_equity:.2f}, and revenue growth of {growth:.1%}."
            )
        elif asset_class == "etf":
            expense = fundamental_details.get("expense_ratio", 1.0)
            tracking = fundamental_details.get("tracking_error", None)
            tracking_available = fundamental_details.get("tracking_error_available", False)
            
            if tracking_available and tracking is not None:
                rationale_parts.append(
                    f"Fundamental analysis (score: {fund_score:.2f}) shows expense ratio of {expense:.2%} and tracking error of {tracking:.2%}."
                )
            else:
                rationale_parts.append(
                    f"Fundamental analysis (score: {fund_score:.2f}) shows expense ratio of {expense:.2%}. "
                    f"Note: Tracking error data not available for this ETF."
                )
        elif asset_class == "crypto":
            market_cap = fundamental_details.get("market_cap", 0.0)
            volume = fundamental_details.get("volume_24h", 0.0)
            rationale_parts.append(f"Fundamental analysis (score: {fund_score:.2f}) shows market cap of ${market_cap / 1e9:.1f}B and 24h volume of ${volume / 1e6:.0f}M.")

        # Technical analysis summary
        tech_score = technical_details.get("technical_score", 0.5)
        rsi = technical_details.get("rsi", 50.0)
        trend = technical_details.get("trend_direction", "sideways")
        rationale_parts.append(f"Technical analysis (score: {tech_score:.2f}) indicates {trend} trend with RSI at {rsi:.1f}.")

        # Risk assessment summary
        risk_score = risk_details.get("risk_score", 0.5)
        volatility = risk_details.get("volatility", 0.20)
        max_dd = risk_details.get("max_drawdown", -0.20)
        rationale_parts.append(f"Risk assessment (score: {risk_score:.2f}) shows {volatility:.1%} volatility and maximum drawdown of {max_dd:.1%}.")

        # Recommendation rationale
        if composite_score >= self.BUY_THRESHOLD:
            rationale_parts.append("Strong fundamentals, favorable technical indicators, and manageable risk profile support a BUY recommendation.")
        elif composite_score <= self.SELL_THRESHOLD:
            rationale_parts.append("Weak fundamentals, unfavorable technical setup, or elevated risk profile warrant a SELL recommendation.")
        else:
            rationale_parts.append("Mixed signals across fundamental, technical, and risk factors suggest a HOLD recommendation pending further developments.")

        return " ".join(rationale_parts)

    def create_detailed_analysis(self, ticker: str, asset_class: str, data: dict[str, Any], result: DeepAnalysisResult) -> dict[str, Any]:
        """
        Create comprehensive detailed_analysis dict preserving ALL raw data.

        Requirements 18.21-18.25: Preserve all raw metrics, sentiment data,
        technical indicators, fundamental data, and calculation results.

        Args:
            ticker: Asset ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            data: Raw collected data from tools
            result: DeepAnalysisResult with calculated scores

        Returns:
            Comprehensive dict with all preserved data

        """
        detailed_analysis = {
            # Basic information
            "ticker": ticker,
            "asset_class": asset_class,
            "analysis_timestamp": data.get("collection_timestamp", ""),
            # Raw metrics preservation (Requirement 18.21)
            "raw_metrics": {
                "volatility": self._safe_get_float(data, "volatility", 0.0),
                "beta": self._safe_get_float(data, "beta", 1.0),
                "max_drawdown": self._safe_get_float(data, "max_drawdown", -0.20),
                "sharpe_ratio": self._safe_get_float(data, "sharpe_ratio", 0.0),
                "current_price": self._safe_get_float(data, "current_price", 0.0),
                "moving_avg_50": self._safe_get_float(data, "moving_avg_50", 0.0),
                "moving_avg_200": self._safe_get_float(data, "moving_avg_200", 0.0),
                "rsi": self._safe_get_float(data, "rsi", 50.0),
                "macd": self._safe_get_float(data, "macd", 0.0),
                "macd_signal": self._safe_get_float(data, "macd_signal", 0.0),
            },
            # Asset-specific raw metrics
            "asset_specific_metrics": self._extract_asset_specific_metrics(asset_class, data),
            # Sentiment data preservation (Requirement 18.22)
            "sentiment_data": {
                "sentiment_score": self._safe_get_float(data, "sentiment_score", 0.0),
                "trending_topics": data.get("trending_topics", []),
                "article_count": data.get("article_count", 0),
                "news_sources": data.get("news_sources", []),
                "sentiment_breakdown": data.get("sentiment_breakdown", {}),
                "social_sentiment": data.get("social_sentiment", {}),
            },
            # Technical indicators preservation (Requirement 18.23)
            "technical_indicators": {
                "rsi": self._safe_get_float(data, "rsi", 50.0),
                "macd": self._safe_get_float(data, "macd", 0.0),
                "macd_signal": self._safe_get_float(data, "macd_signal", 0.0),
                "macd_histogram": self._safe_get_float(data, "macd_histogram", 0.0),
                "bollinger_upper": self._safe_get_float(data, "bollinger_upper", 0.0),
                "bollinger_lower": self._safe_get_float(data, "bollinger_lower", 0.0),
                "bollinger_middle": self._safe_get_float(data, "bollinger_middle", 0.0),
                "support_levels": data.get("support_levels", []),
                "resistance_levels": data.get("resistance_levels", []),
                "trend_direction": result.technical_details.get("trend_direction", "sideways"),
                "momentum_indicators": data.get("momentum_indicators", {}),
                "volume_indicators": data.get("volume_indicators", {}),
            },
            # Fundamental data preservation (Requirement 18.24)
            "fundamental_data": self._extract_fundamental_data(asset_class, data),
            # Calculation results preservation (Requirement 18.25)
            "calculation_results": {
                "composite_score": result.composite_score,
                "fundamental_score": result.fundamental_score,
                "technical_score": result.technical_score,
                "risk_score": result.risk_score,
                "grade": result.grade,
                "recommendation": result.recommendation,
                "confidence": result.confidence,
                "rationale": result.rationale,
                # Component details
                "fundamental_details": result.fundamental_details,
                "technical_details": result.technical_details,
                "risk_details": result.risk_details,
            },
            # Additional context
            "data_quality": {
                "missing_fields": self._identify_missing_fields(data),
                "data_freshness": data.get("data_freshness", {}),
                "source_reliability": data.get("source_reliability", {}),
            },
            # Raw tool outputs (preserve everything)
            "raw_tool_outputs": {
                "ticker_validation": data.get("ticker_validation", {}),
                "quantitative_analysis": data.get("quantitative_analysis", {}),
                "sentiment_analysis": data.get("sentiment_analysis", {}),
                "sec_analysis": data.get("sec_analysis", {}),
                "etf_analysis": data.get("etf_analysis", {}),
                "crypto_analysis": data.get("crypto_analysis", {}),
            },
        }

        return detailed_analysis

    def _extract_asset_specific_metrics(self, asset_class: str, data: dict[str, Any]) -> dict[str, Any]:
        """Extract asset-specific metrics based on asset class."""
        if asset_class == "stock":
            return {
                "roe": self._safe_get_float(data, "roe", 0.0),
                "debt_to_equity": self._safe_get_float(data, "debt_to_equity", 1.0),
                "revenue_growth": self._safe_get_float(data, "revenue_growth", 0.0),
                "profit_margin": self._safe_get_float(data, "profit_margin", 0.0),
                "earnings_per_share": self._safe_get_float(data, "earnings_per_share", 0.0),
                "price_to_earnings": self._safe_get_float(data, "price_to_earnings", 0.0),
                "price_to_book": self._safe_get_float(data, "price_to_book", 0.0),
                "free_cash_flow": self._safe_get_float(data, "free_cash_flow", 0.0),
                "current_ratio": self._safe_get_float(data, "current_ratio", 1.0),
                "quick_ratio": self._safe_get_float(data, "quick_ratio", 1.0),
            }
        elif asset_class == "etf":
            return {
                "expense_ratio": self._safe_get_float(data, "expense_ratio", 1.0),
                "tracking_error": self._safe_get_float(data, "tracking_error", 1.0),
                "aum": self._safe_get_float(data, "aum", 0.0),
                "dividend_yield": self._safe_get_float(data, "dividend_yield", 0.0),
                "top_holdings": data.get("top_holdings", []),
                "sector_allocation": data.get("sector_allocation", {}),
                "geographic_allocation": data.get("geographic_allocation", {}),
            }
        elif asset_class == "crypto":
            return {
                "market_cap": self._safe_get_float(data, "market_cap", 0.0),
                "volume_24h": self._safe_get_float(data, "volume_24h", 0.0),
                "age_years": self._safe_get_float(data, "age_years", 0.0),
                "circulating_supply": self._safe_get_float(data, "circulating_supply", 0.0),
                "max_supply": self._safe_get_float(data, "max_supply", 0.0),
                "total_supply": self._safe_get_float(data, "total_supply", 0.0),
                "market_cap_rank": data.get("market_cap_rank", 0),
                "all_time_high": self._safe_get_float(data, "all_time_high", 0.0),
                "all_time_low": self._safe_get_float(data, "all_time_low", 0.0),
            }
        else:
            return {}

    def _extract_fundamental_data(self, asset_class: str, data: dict[str, Any]) -> dict[str, Any]:
        """Extract fundamental data based on asset class."""
        base_data = {
            "revenue": self._safe_get_float(data, "revenue", 0.0),
            "earnings": self._safe_get_float(data, "earnings", 0.0),
            "cash_flow": self._safe_get_float(data, "cash_flow", 0.0),
            "total_assets": self._safe_get_float(data, "total_assets", 0.0),
            "total_liabilities": self._safe_get_float(data, "total_liabilities", 0.0),
            "shareholders_equity": self._safe_get_float(data, "shareholders_equity", 0.0),
        }

        # Add asset-specific fundamental data
        if asset_class == "stock":
            base_data.update(
                {
                    "sec_filings": data.get("sec_filings", {}),
                    "financial_statements": data.get("financial_statements", {}),
                    "business_description": data.get("business_description", ""),
                    "risk_factors": data.get("risk_factors", []),
                    "competitive_advantages": data.get("competitive_advantages", []),
                }
            )
        elif asset_class == "etf":
            base_data.update(
                {
                    "fund_objective": data.get("fund_objective", ""),
                    "benchmark_index": data.get("benchmark_index", ""),
                    "fund_family": data.get("fund_family", ""),
                    "inception_date": data.get("inception_date", ""),
                    "holdings_count": data.get("holdings_count", 0),
                }
            )
        elif asset_class == "crypto":
            base_data.update(
                {
                    "whitepaper_url": data.get("whitepaper_url", ""),
                    "consensus_mechanism": data.get("consensus_mechanism", ""),
                    "use_cases": data.get("use_cases", []),
                    "development_activity": data.get("development_activity", {}),
                    "community_metrics": data.get("community_metrics", {}),
                }
            )

        return base_data

    def _identify_missing_fields(self, data: dict[str, Any]) -> list[str]:
        """Identify missing or null fields in the data."""
        missing_fields = []
        key_fields = [
            "current_price",
            "volatility",
            "rsi",
            "macd",
            "beta",
            "sentiment_score",
            "volume_24h" if "crypto" in str(data.get("asset_class", "")) else "volume",
        ]

        for field in key_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        return missing_fields

    def create_crew_export(self, result: DeepAnalysisResult, detailed_analysis: dict[str, Any], session_id: str = "default") -> dict[str, Any]:
        """
        Create DeepAnalysisCrewExport dict from DeepAnalysisResult.

        Args:
            result: DeepAnalysisResult from scoring
            detailed_analysis: Comprehensive analysis dict
            session_id: Session identifier for file paths

        Returns:
            Dict ready for DeepAnalysisCrewExport validation

        """
        from finwiz.schemas.common import RiskAssessmentStandardized

        # Create risk assessment from result data
        risk_assessment = RiskAssessmentStandardized(
            score=float((1.0 - result.risk_score) * 5),  # Convert 0-1 to 5-0 scale
            level=self._map_risk_level(result.risk_score),
            risk_factors=self._extract_risk_factors(result.risk_details),
        )

        # Determine data sources based on asset class
        data_sources = self._determine_data_sources(result.asset_class, detailed_analysis)

        return {
            "crew_name": "deep_analysis_crew",
            "ticker": result.ticker,
            "asset_class": result.asset_class,
            "analysis_date": datetime.now(),
            "session_id": session_id,
            # Analysis results
            "detailed_analysis": detailed_analysis,
            "risk_assessment": risk_assessment,
            # Scores and grades
            "composite_score": result.composite_score,
            "grade": result.grade,
            # Recommendations
            "recommendation": result.recommendation,
            "confidence": result.confidence,
            "rationale": result.rationale,
            # Metadata
            "data_sources": data_sources,
            "report_html_path": f"output/reports/{session_id}/deep_analysis_crew/{result.ticker}_report.html",
            "report_json_path": f"output/reports/{session_id}/deep_analysis_crew/{result.ticker}_export.json",
        }

    def _map_risk_level(self, risk_score: float) -> str:
        """Map risk score (0-1, where 1=low risk) to risk level."""
        # Convert to 0-5 scale where 5=high risk
        risk_5_scale = (1.0 - risk_score) * 5

        if risk_5_scale <= 1.5:
            return "Low"
        elif risk_5_scale <= 2.5:
            return "Medium"
        elif risk_5_scale <= 4.0:
            return "High"
        else:
            return "Very High"

    def _extract_risk_factors(self, risk_details: dict[str, Any]) -> list[str]:
        """Extract risk factors from risk analysis details."""
        risk_factors = []

        volatility = risk_details.get("volatility", 0.20)
        if volatility > 0.30:
            risk_factors.append(f"High volatility ({volatility:.1%})")

        max_drawdown = risk_details.get("max_drawdown", -0.20)
        if max_drawdown < -0.25:
            risk_factors.append(f"Significant drawdown risk ({max_drawdown:.1%})")

        beta = risk_details.get("beta", 1.0)
        if beta > 1.5:
            risk_factors.append(f"High market sensitivity (beta: {beta:.2f})")
        elif beta < 0.5:
            risk_factors.append(f"Low market correlation (beta: {beta:.2f})")

        return risk_factors[:10]  # Limit to 10 factors

    def _generate_mitigation_strategies(self, asset_class: str, risk_details: dict[str, Any]) -> list[str]:
        """Generate risk mitigation strategies based on asset class and risk profile."""
        strategies = []

        volatility = risk_details.get("volatility", 0.20)
        if volatility > 0.25:
            strategies.append("Consider position sizing to limit exposure")
            strategies.append("Use stop-loss orders to limit downside risk")

        if asset_class == "stock":
            strategies.append("Diversify across sectors and market caps")
            strategies.append("Monitor earnings reports and guidance updates")
        elif asset_class == "etf":
            strategies.append("Review underlying holdings concentration")
            strategies.append("Monitor tracking error vs benchmark")
        elif asset_class == "crypto":
            strategies.append("Limit allocation to small percentage of portfolio")
            strategies.append("Monitor regulatory developments closely")

        return strategies[:5]  # Limit to 5 strategies

    def _determine_data_sources(self, asset_class: str, detailed_analysis: dict[str, Any]) -> list[str]:
        """Determine data sources used based on asset class and available data."""
        sources = ["Yahoo Finance API"]  # Always used for price data

        if asset_class == "stock":
            sources.extend(["SEC EDGAR Database", "Alpha Vantage API"])
        elif asset_class == "etf":
            sources.extend(["ETF.com", "Morningstar"])
        elif asset_class == "crypto":
            sources.extend(["CoinMarketCap API", "CoinGecko API"])

        # Add sources based on available data
        raw_outputs = detailed_analysis.get("raw_tool_outputs", {})
        if raw_outputs.get("sentiment_analysis"):
            sources.append("News Sentiment Analysis")
        if raw_outputs.get("quantitative_analysis"):
            sources.append("TwelveData API")

        return list(set(sources))  # Remove duplicates

    def _calculate_confidence(self, fundamental_score: float, technical_score: float, risk_score: float, data: dict[str, Any]) -> float:
        """Calculate confidence level based on data quality and score consistency."""
        # Base confidence from score consistency
        scores = [fundamental_score, technical_score, risk_score]
        score_std = (sum((s - sum(scores) / 3) ** 2 for s in scores) / 3) ** 0.5

        # Lower standard deviation = higher confidence
        consistency_confidence = max(0.5, 1.0 - score_std * 2)

        # Data quality confidence (check for missing key metrics)
        data_quality = 1.0
        key_fields = ["current_price", "volatility", "rsi"]
        missing_fields = sum(1 for field in key_fields if field not in data or data[field] is None)
        data_quality -= missing_fields * 0.1

        # Combined confidence
        confidence = min(1.0, max(0.3, consistency_confidence * data_quality))
        return confidence

    def _create_error_result(self, ticker: str, asset_class: str, error_msg: str) -> DeepAnalysisResult:
        """Create a default result for error cases."""
        # Ensure asset_class is valid for Pydantic validation
        valid_asset_class = asset_class if asset_class in ["stock", "etf", "crypto"] else "stock"

        return DeepAnalysisResult(
            ticker=ticker,
            asset_class=valid_asset_class,
            crew_name="python_scorer",
            composite_score=0.3,
            grade="D",
            recommendation="HOLD",
            rationale=f"Analysis failed due to error: {error_msg}",
            risk_details={"error": 1.0},
            fundamental_score=0.3,
            technical_score=0.3,
            risk_score=0.3,
            data_freshness_hours=0.0,
            confidence_level=0.1,
            warnings=[f"Analysis failed: {error_msg}"],
            cached=False,
        )

    def _get_expected_fields(self, asset_class: str) -> list[str]:
        """
        Get list of expected fields based on asset class.

        Args:
            asset_class: Asset class (stock, etf, crypto)

        Returns:
            List of expected field names

        """
        common_fields = ["current_price", "volatility", "max_drawdown", "beta", "rsi", "macd", "macd_signal"]

        if asset_class == "stock":
            return common_fields + ["roe", "debt_to_equity", "revenue_growth", "profit_margin"]
        elif asset_class == "etf":
            return common_fields + ["expense_ratio", "tracking_error", "aum"]
        elif asset_class == "crypto":
            return common_fields + ["market_cap", "volume_24h", "age_years"]
        else:
            return common_fields

    def _safe_get_float(self, data: dict[str, Any], key: str, default: float | None = None) -> float:
        """
        Safely extract float value from data dictionary with critical field validation.

        CRITICAL CHANGE: If field is critical and missing, raises CriticalFieldError
        instead of silently using a default value.

        Args:
            data: Data dictionary
            key: Key to extract
            default: Default value if key is missing (only for OPTIONAL fields)

        Returns:
            Float value from data

        Raises:
            CriticalFieldError: If critical field is missing (no default allowed)

        """
        from finwiz.config.critical_fields_config import (
            CriticalFieldError,
            get_safe_default,
            is_critical_field,
        )

        try:
            value = data.get(key)

            if value is None:
                # Check if this is a critical field
                asset_class = data.get("asset_class", self._current_ticker)
                if is_critical_field(key, asset_class):
                    # CRITICAL FIELD MISSING - FAIL FAST
                    if self._data_quality_metrics:
                        self._data_quality_metrics.record_missing_field(key)

                    raise CriticalFieldError(
                        ticker=self._current_ticker,
                        asset_class=asset_class,
                        missing_fields=[key],
                    )

                # Optional field - use safe default
                safe_default = default if default is not None else get_safe_default(key)
                if safe_default is None:
                    # No safe default available
                    self.logger.error(f"❌ No safe default for optional field '{key}'")
                    safe_default = 0.0

                # Track defaulted field
                if self._data_quality_metrics:
                    self._data_quality_metrics.record_defaulted_field(key, safe_default)

                # Track default value in lineage (Task 9.2)
                if self._lineage_tracker:
                    self._lineage_tracker.add_source(
                        source_id=f"default_{key}",
                        source_type="default",
                        source_name="Safe Default (Optional Field)",
                        field_name=key,
                        raw_value=safe_default,
                        metadata={"reason": "optional_field_missing", "is_critical": False},
                    )

                self.logger.warning(
                    f"⚠️ Optional field '{key}' missing for {self._current_ticker}, "
                    f"using safe default {safe_default}"
                )
                return safe_default

            # Field exists - track as calculated
            float_value = float(value)
            if self._data_quality_metrics:
                self._data_quality_metrics.record_calculated_field(key)

            # Track data source in lineage (Task 9.2)
            if self._lineage_tracker:
                self._lineage_tracker.add_source(
                    source_id=f"data_{key}",
                    source_type="calculation",  # From crew output/calculation
                    source_name="Real Data",
                    field_name=key,
                    raw_value=value,
                    metadata={"data_type": type(value).__name__, "is_critical": is_critical_field(key, data.get("asset_class", "stock"))},
                )

            return float_value

        except (ValueError, TypeError) as e:
            # Field exists but invalid value
            asset_class = data.get("asset_class", "stock")
            if is_critical_field(key, asset_class):
                # CRITICAL FIELD INVALID - FAIL FAST
                if self._data_quality_metrics:
                    self._data_quality_metrics.record_missing_field(key)

                raise CriticalFieldError(
                    ticker=self._current_ticker,
                    asset_class=asset_class,
                    missing_fields=[key],
                )

            # Optional field with invalid value - use safe default
            safe_default = default if default is not None else get_safe_default(key)
            if safe_default is None:
                safe_default = 0.0

            if self._data_quality_metrics:
                self._data_quality_metrics.record_defaulted_field(key, safe_default)

            self.logger.warning(
                f"⚠️ Invalid value for optional field '{key}' for {self._current_ticker}: "
                f"{data.get(key)} ({e}), using safe default {safe_default}"
            )
            return safe_default
