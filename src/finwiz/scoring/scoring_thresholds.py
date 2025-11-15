"""
Scoring Thresholds Configuration.

Centralized configuration for all scoring thresholds used in FinWiz.
Extracted from hardcoded values in Phase 2A.3 refactoring.

This module provides a single source of truth for all scoring thresholds,
making it easy to tune scoring parameters and maintain consistency.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoringThresholds:
    """
    Centralized scoring thresholds for all asset classes and metrics.

    All thresholds are organized by category and metric type.
    Values are stored as floats (e.g., 0.20 = 20%).

    Usage:
        thresholds = ScoringThresholds()
        if roe >= thresholds.roe_excellent:
            score = 1.0
    """

    # ============================================================================
    # GRADE THRESHOLDS (Composite Score → Letter Grade)
    # ============================================================================
    grade_a_plus: float = 0.90  # A+ grade threshold
    grade_a: float = 0.80  # A grade threshold
    grade_b: float = 0.70  # B grade threshold
    grade_c: float = 0.60  # C grade threshold
    grade_d: float = 0.50  # D grade threshold
    # Below 0.50 = F grade

    # ============================================================================
    # RECOMMENDATION THRESHOLDS
    # ============================================================================
    buy_threshold: float = 0.80  # BUY recommendation (A or better)
    sell_threshold: float = 0.60  # SELL recommendation (below C)
    # Between 0.60-0.80 = HOLD recommendation

    # ============================================================================
    # STOCK FUNDAMENTAL THRESHOLDS
    # ============================================================================

    # ROE (Return on Equity) - Higher is better
    roe_excellent: float = 0.20  # 20%+ (score: 1.0)
    roe_very_good: float = 0.15  # 15-20% (score: 0.8)
    roe_good: float = 0.10  # 10-15% (score: 0.6)
    roe_acceptable: float = 0.05  # 5-10% (score: 0.4)
    # Below 5% (score: 0.2)

    # Debt-to-Equity Ratio - Lower is better
    debt_very_low: float = 0.3  # ≤0.3 (score: 1.0)
    debt_low: float = 0.5  # 0.3-0.5 (score: 0.8)
    debt_moderate: float = 1.0  # 0.5-1.0 (score: 0.6)
    debt_high: float = 2.0  # 1.0-2.0 (score: 0.4)
    # Above 2.0 (score: 0.2)

    # Revenue Growth - Higher is better
    growth_excellent: float = 0.25  # 25%+ (score: 1.0)
    growth_very_good: float = 0.15  # 15-25% (score: 0.8)
    growth_good: float = 0.10  # 10-15% (score: 0.6)
    growth_acceptable: float = 0.05  # 5-10% (score: 0.4)
    # Below 5% (score: 0.2)

    # Profit Margin - Higher is better
    margin_excellent: float = 0.20  # 20%+ (score: 1.0)
    margin_very_good: float = 0.15  # 15-20% (score: 0.8)
    margin_good: float = 0.10  # 10-15% (score: 0.6)
    margin_acceptable: float = 0.05  # 5-10% (score: 0.4)
    # Below 5% (score: 0.2)

    # ============================================================================
    # ETF FUNDAMENTAL THRESHOLDS
    # ============================================================================

    # Expense Ratio - Lower is better (as decimal: 0.001 = 0.10%)
    expense_excellent: float = 0.001  # ≤0.10% (score: 1.0)
    expense_very_good: float = 0.0025  # 0.10-0.25% (score: 0.8)
    expense_good: float = 0.005  # 0.25-0.50% (score: 0.6)
    expense_acceptable: float = 0.01  # 0.50-1.00% (score: 0.4)
    # Above 1.00% (score: 0.2)

    # Tracking Error - Lower is better (as decimal: 0.002 = 0.20%)
    tracking_excellent: float = 0.002  # ≤0.20% (score: 1.0)
    tracking_very_good: float = 0.005  # 0.20-0.50% (score: 0.8)
    tracking_good: float = 0.01  # 0.50-1.00% (score: 0.6)
    tracking_acceptable: float = 0.02  # 1.00-2.00% (score: 0.4)
    # Above 2.00% (score: 0.2)

    # Assets Under Management (AUM) - Higher is better
    aum_excellent: float = 5e9  # $5B+ (score: 1.0)
    aum_very_good: float = 1e9  # $1-5B (score: 0.8)
    aum_good: float = 500e6  # $500M-1B (score: 0.6)
    aum_acceptable: float = 100e6  # $100M-500M (score: 0.4)
    # Below $100M (score: 0.2)

    # ============================================================================
    # CRYPTO FUNDAMENTAL THRESHOLDS
    # ============================================================================

    # Market Capitalization - Higher is better
    market_cap_mega: float = 100e9  # $100B+ (score: 1.0)
    market_cap_large: float = 10e9  # $10-100B (score: 0.8)
    market_cap_mid: float = 1e9  # $1-10B (score: 0.6)
    market_cap_small: float = 100e6  # $100M-1B (score: 0.4)
    # Below $100M (score: 0.2)

    # 24h Trading Volume - Higher is better
    volume_very_high: float = 10e9  # $10B+ (score: 1.0)
    volume_high: float = 1e9  # $1-10B (score: 0.8)
    volume_good: float = 100e6  # $100M-1B (score: 0.6)
    volume_moderate: float = 10e6  # $10-100M (score: 0.4)
    # Below $10M (score: 0.2)

    # Age in Years - Older is better
    age_very_established: float = 5.0  # 5+ years (score: 1.0)
    age_established: float = 3.0  # 3-5 years (score: 0.8)
    age_maturing: float = 2.0  # 2-3 years (score: 0.6)
    age_young: float = 1.0  # 1-2 years (score: 0.4)
    # Below 1 year (score: 0.2)

    # Supply Circulation Ratio - Higher is better
    circulation_high: float = 0.90  # 90%+ (score: 1.0)
    circulation_good: float = 0.70  # 70-90% (score: 0.8)
    circulation_moderate: float = 0.50  # 50-70% (score: 0.6)
    circulation_early: float = 0.30  # 30-50% (score: 0.4)
    # Below 30% (score: 0.2)

    # ============================================================================
    # TECHNICAL ANALYSIS THRESHOLDS
    # ============================================================================

    # RSI (Relative Strength Index) - Target 30-70 range
    rsi_neutral_min: float = 40.0  # Neutral zone minimum
    rsi_neutral_max: float = 60.0  # Neutral zone maximum (score: 1.0)
    rsi_good_min: float = 30.0  # Good range minimum
    rsi_good_max: float = 70.0  # Good range maximum (score: 0.8)
    rsi_acceptable_min: float = 20.0  # Acceptable range minimum
    rsi_acceptable_max: float = 80.0  # Acceptable range maximum (score: 0.6)
    rsi_warning_min: float = 10.0  # Warning range minimum
    rsi_warning_max: float = 90.0  # Warning range maximum (score: 0.4)
    # Outside 10-90 range (score: 0.2)

    # MACD Momentum - Threshold for neutral momentum
    macd_neutral_threshold: float = 0.1  # |MACD diff| < 0.1 = neutral

    # ============================================================================
    # RISK ASSESSMENT THRESHOLDS
    # ============================================================================

    # Volatility (Annual) - Lower is better
    volatility_very_low: float = 0.10  # ≤10% (score: 1.0)
    volatility_low: float = 0.15  # 10-15% (score: 0.8)
    volatility_moderate: float = 0.25  # 15-25% (score: 0.6)
    volatility_high: float = 0.40  # 25-40% (score: 0.4)
    # Above 40% (score: 0.2)

    # Maximum Drawdown - Lower is better (stored as positive for comparison)
    drawdown_very_low: float = 0.10  # ≤10% (score: 1.0)
    drawdown_low: float = 0.20  # 10-20% (score: 0.8)
    drawdown_moderate: float = 0.35  # 20-35% (score: 0.6)
    drawdown_high: float = 0.50  # 35-50% (score: 0.4)
    # Above 50% (score: 0.2)

    # Beta Deviation - Closer to 1.0 is better
    beta_excellent: float = 0.20  # |beta - 1.0| ≤ 0.20 (score: 1.0)
    beta_very_good: float = 0.40  # |beta - 1.0| ≤ 0.40 (score: 0.8)
    beta_good: float = 0.60  # |beta - 1.0| ≤ 0.60 (score: 0.6)
    beta_acceptable: float = 1.00  # |beta - 1.0| ≤ 1.00 (score: 0.4)
    # |beta - 1.0| > 1.00 (score: 0.2)

    # ============================================================================
    # RISK LEVEL MAPPING THRESHOLDS
    # ============================================================================

    # Risk level thresholds (for 0-5 scale where 5 = high risk)
    risk_low_threshold: float = 1.5  # ≤1.5 = Low risk
    risk_medium_threshold: float = 2.5  # 1.5-2.5 = Medium risk
    risk_high_threshold: float = 4.0  # 2.5-4.0 = High risk
    # Above 4.0 = Very High risk

    # Risk factor thresholds (for identifying specific risks)
    risk_volatility_high: float = 0.30  # Volatility > 30% = high risk
    risk_drawdown_significant: float = 0.25  # Drawdown < -25% = significant risk
    risk_beta_high: float = 1.5  # Beta > 1.5 = high market sensitivity
    risk_beta_low: float = 0.5  # Beta < 0.5 = low market correlation

    # ============================================================================
    # COMPONENT WEIGHTS
    # ============================================================================

    # Composite score weights
    weight_fundamental: float = 0.40  # 40% fundamental
    weight_technical: float = 0.30  # 30% technical
    weight_risk: float = 0.30  # 30% risk

    # Stock fundamental weights
    weight_stock_roe: float = 0.40  # 40% ROE
    weight_stock_debt: float = 0.30  # 30% debt
    weight_stock_growth: float = 0.20  # 20% growth
    weight_stock_margin: float = 0.10  # 10% margin

    # ETF fundamental weights
    weight_etf_expense: float = 0.50  # 50% expense ratio
    weight_etf_tracking: float = 0.30  # 30% tracking error
    weight_etf_aum: float = 0.20  # 20% AUM

    # Crypto fundamental weights
    weight_crypto_market_cap: float = 0.40  # 40% market cap
    weight_crypto_volume: float = 0.30  # 30% volume
    weight_crypto_age: float = 0.20  # 20% age
    weight_crypto_supply: float = 0.10  # 10% supply metrics

    # Technical analysis weights
    weight_technical_rsi: float = 0.40  # 40% RSI
    weight_technical_trend: float = 0.40  # 40% trend
    weight_technical_momentum: float = 0.20  # 20% momentum

    # Risk assessment weights
    weight_risk_volatility: float = 0.50  # 50% volatility
    weight_risk_drawdown: float = 0.30  # 30% drawdown
    weight_risk_beta: float = 0.20  # 20% beta


# Global instance for easy access
DEFAULT_THRESHOLDS = ScoringThresholds()


def get_thresholds() -> ScoringThresholds:
    """
    Get the default scoring thresholds.

    Returns:
        ScoringThresholds instance with default values

    """
    return DEFAULT_THRESHOLDS
