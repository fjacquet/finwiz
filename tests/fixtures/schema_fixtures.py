"""
Schema fixtures for testing.

Provides factory functions to create valid Pydantic model instances.
"""

from datetime import datetime
from typing import Any

from finwiz.schemas.crew_exports import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview


def create_risk_assessment(
    overall_risk_score: int = 3,
    risk_level: str = "MEDIUM",
    **overrides: Any,
) -> RiskAssessmentStandardized:
    """
    Create a valid RiskAssessmentStandardized instance.
    
    Args:
        overall_risk_score: Risk score 0-5 (default: 3)
        risk_level: Risk level string (default: "MEDIUM")
        **overrides: Additional field overrides
        
    Returns:
        RiskAssessmentStandardized instance

    """
    data = {
        "overall_risk_score": overall_risk_score,
        "risk_level": risk_level,
        "systematic_risk": 0.6,
        "idiosyncratic_risk": 0.4,
        "volatility_risk": 3,
        "liquidity_risk": 2,
        "concentration_risk": 2,
        "market_risk": 3,
        "credit_risk": 2,
        "operational_risk": 2,
        "regulatory_risk": 3,
        "key_risks": ["Market volatility", "Regulatory changes"],
        "risk_mitigation_strategies": ["Diversification", "Stop-loss orders"],
        "confidence_level": 0.8,
        "data_quality_score": 0.85,
        "last_updated": datetime.now(),
    }
    data.update(overrides)
    return RiskAssessmentStandardized(**data)


def create_deep_analysis_result(
    ticker: str = "AAPL",
    asset_class: str = "stock",
    composite_score: float = 0.85,
    grade: str = "A",
    **overrides: Any,
) -> dict[str, Any]:
    """
    Create a valid deep analysis result dictionary.
    
    Args:
        ticker: Ticker symbol (default: "AAPL")
        asset_class: Asset class (default: "stock")
        composite_score: Overall score 0-1 (default: 0.85)
        grade: Letter grade (default: "A")
        **overrides: Additional field overrides
        
    Returns:
        Dictionary with deep analysis result

    """
    data = {
        "ticker": ticker,
        "asset_class": asset_class,
        "composite_score": composite_score,
        "grade": grade,
        "recommendation": "BUY",
        "confidence": 0.8,
        "fundamental_score": 0.85,
        "technical_score": 0.80,
        "risk_score": 0.75,
        "sentiment_score": 0.70,
        "risk_assessment": create_risk_assessment().model_dump(),
        "strengths": ["Strong fundamentals", "Positive momentum"],
        "weaknesses": ["High valuation", "Market volatility"],
        "analysis_date": datetime.now().isoformat(),
    }
    data.update(overrides)
    return data


def create_holding_decision(
    ticker: str = "AAPL",
    decision: str = "KEEP",
    **overrides: Any,
) -> HoldingDecision:
    """
    Create a valid HoldingDecision instance.
    
    Args:
        ticker: Ticker symbol (default: "AAPL")
        decision: Decision (KEEP/SELL) (default: "KEEP")
        **overrides: Additional field overrides
        
    Returns:
        HoldingDecision instance

    """
    data = {
        "ticker": ticker,
        "name": f"{ticker} Inc.",
        "asset_class": "stock",
        "decision": decision,
        "grade": "A",
        "composite_score": 0.85,
        "rationale": "Strong fundamentals and positive momentum",
        "confidence": 0.8,
    }
    data.update(overrides)
    return HoldingDecision(**data)


def create_portfolio_review(
    total_holdings: int = 10,
    keep_count: int = 7,
    sell_count: int = 3,
    **overrides: Any,
) -> PortfolioReview:
    """
    Create a valid PortfolioReview instance.
    
    Args:
        total_holdings: Total number of holdings (default: 10)
        keep_count: Number to keep (default: 7)
        sell_count: Number to sell (default: 3)
        **overrides: Additional field overrides
        
    Returns:
        PortfolioReview instance

    """
    decisions = []

    # Create KEEP decisions
    for i in range(keep_count):
        decisions.append(create_holding_decision(
            ticker=f"KEEP{i}",
            decision="KEEP",
        ))

    # Create SELL decisions
    for i in range(sell_count):
        decisions.append(create_holding_decision(
            ticker=f"SELL{i}",
            decision="SELL",
            grade="D",
            composite_score=0.45,
        ))

    data = {
        "decisions": decisions,
        "summary": {
            "total_holdings": total_holdings,
            "keep_count": keep_count,
            "sell_count": sell_count,
            "average_grade": "B+",
        },
        "analysis_date": datetime.now(),
    }
    data.update(overrides)
    return PortfolioReview(**data)
