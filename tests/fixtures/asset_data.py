"""
Asset data fixtures for testing.

Provides realistic test data for stocks, ETFs, and cryptocurrencies.
"""

from typing import Any


def create_stock_data(
    roe: float = 0.25,
    revenue_growth: float = 0.20,
    debt_to_equity: float = 0.2,
    market_cap: float = 10e9,
    **overrides: Any,
) -> dict[str, Any]:
    """
    Create sample stock fundamental data.
    
    Args:
        roe: Return on equity (default: 0.25 = 25%)
        revenue_growth: Revenue growth rate (default: 0.20 = 20%)
        debt_to_equity: Debt to equity ratio (default: 0.2)
        market_cap: Market capitalization (default: $10B)
        **overrides: Additional fields or overrides
        
    Returns:
        Dictionary with stock fundamental data

    """
    data = {
        "roe": roe,
        "revenue_growth": revenue_growth,
        "debt_to_equity": debt_to_equity,
        "market_cap": market_cap,
        "fcf_positive": True,
        "fcf_growing": True,
        "profit_margin": 0.25,
        "current_ratio": 2.0,
        "quick_ratio": 1.5,
        "pe_ratio": 20.0,
        "peg_ratio": 1.5,
        "dividend_yield": 0.02,
        "management_quality": 0.8,
        "governance_score": 0.85,
        "competitive_moat": 0.9,
    }
    data.update(overrides)
    return data


def create_etf_data(
    expense_ratio: float = 0.03,
    aum: float = 5e9,
    tracking_error: float = 0.001,
    **overrides: Any,
) -> dict[str, Any]:
    """
    Create sample ETF data.
    
    Args:
        expense_ratio: Annual expense ratio (default: 0.03 = 0.03%)
        aum: Assets under management (default: $5B)
        tracking_error: Tracking error vs benchmark (default: 0.001 = 0.1%)
        **overrides: Additional fields or overrides
        
    Returns:
        Dictionary with ETF data

    """
    data = {
        "expense_ratio": expense_ratio,
        "aum": aum,
        "tracking_error": tracking_error,
        "history_years": 5,
        "holdings_count": 500,
        "top_10_concentration": 0.25,
        "dividend_yield": 0.015,
        "issuer_reputation": 0.9,
        "regulatory_compliance": 0.95,
        "transparency_score": 0.85,
        "liquidity_score": 0.9,
    }
    data.update(overrides)
    return data


def create_crypto_data(
    market_cap: float = 50e9,
    daily_volume: float = 2e9,
    age_months: int = 60,
    **overrides: Any,
) -> dict[str, Any]:
    """
    Create sample cryptocurrency data.
    
    Args:
        market_cap: Market capitalization (default: $50B)
        daily_volume: 24h trading volume (default: $2B)
        age_months: Age in months (default: 60 = 5 years)
        **overrides: Additional fields or overrides
        
    Returns:
        Dictionary with crypto data

    """
    data = {
        "market_cap": market_cap,
        "daily_volume": daily_volume,
        "age_months": age_months,
        "institutional_adoption": True,
        "real_utility": True,
        "circulating_supply": 19e6,
        "max_supply": 21e6,
        "inflation_rate": 0.018,
        "team_quality": 0.8,
        "development_activity": 0.9,
        "community_strength": 0.7,
        "regulatory_clarity": 0.6,
    }
    data.update(overrides)
    return data


def create_technical_data(
    momentum_score: float = 0.7,
    trend_strength: float = 0.8,
    volatility_score: float = 0.6,
    **overrides: Any,
) -> dict[str, Any]:
    """
    Create sample technical analysis data.
    
    Args:
        momentum_score: Momentum indicator score (default: 0.7)
        trend_strength: Trend strength score (default: 0.8)
        volatility_score: Volatility score (default: 0.6)
        **overrides: Additional fields or overrides
        
    Returns:
        Dictionary with technical data

    """
    data = {
        "momentum_score": momentum_score,
        "trend_strength": trend_strength,
        "volatility_score": volatility_score,
        "rsi": 55.0,
        "macd": 0.5,
        "macd_signal": 0.3,
        "sma_20": 150.0,
        "sma_50": 145.0,
        "sma_200": 140.0,
        "bollinger_upper": 160.0,
        "bollinger_lower": 140.0,
    }
    data.update(overrides)
    return data


def create_risk_data(
    volatility: float = 0.20,
    beta: float = 1.0,
    max_drawdown: float = 0.15,
    **overrides: Any,
) -> dict[str, Any]:
    """
    Create sample risk metrics data.
    
    Args:
        volatility: Annualized volatility (default: 0.20 = 20%)
        beta: Beta vs market (default: 1.0)
        max_drawdown: Maximum drawdown (default: 0.15 = 15%)
        **overrides: Additional fields or overrides
        
    Returns:
        Dictionary with risk metrics

    """
    data = {
        "volatility": volatility,
        "beta": beta,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": 1.5,
        "sortino_ratio": 2.0,
        "calmar_ratio": 1.2,
        "var_95": 0.05,
        "cvar_95": 0.08,
        "downside_deviation": 0.12,
    }
    data.update(overrides)
    return data
