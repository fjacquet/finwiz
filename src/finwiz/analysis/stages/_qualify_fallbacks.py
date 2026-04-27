"""Qualify fallback builders: Python-template and error-fallback QualitativeInsights.

Split from qualify.py to stay within the 300-line new-file limit.
These two functions are the largest in the qualify stage and are cohesive —
both produce QualitativeInsights without calling the AI crew.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal, cast

from finwiz.schemas.hybrid_analysis import QualitativeInsights, QuantitativeAnalysis
from finwiz.schemas.hybrid_analysis.qualitative import (
    ActionPlan,
    ContextualRiskInsights,
    FundamentalContextInsights,
    InvestmentSynthesis,
    ScenarioProbabilities,
    SecAnalysisInsights,
    TechnicalStrategyInsights,
)

if TYPE_CHECKING:
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext


def _create_python_qualitative(ctx: AnalysisContext, quant: QuantitativeAnalysis) -> QualitativeInsights:
    """Generate qualitative insights using Python templates (no AI).

    This is used in MAXIMUM_SPEED mode to avoid slow AI calls.
    Content is derived from quantitative metrics using rule-based templates.
    """
    ticker = ctx.ticker
    grade = quant.grade
    score = quant.composite_score
    rec = quant.preliminary_recommendation
    fund_score = quant.fundamental_score
    tech_score = quant.technical_score
    risk_score = quant.risk_score
    rationale = quant.python_rationale

    # Determine sentiment based on scores
    is_strong = score >= 0.7
    is_weak = score < 0.4
    sentiment = "positif" if is_strong else ("négatif" if is_weak else "neutre")

    # Build business model from metrics
    fund_metrics = quant.fundamental_metrics
    roe = fund_metrics.get("roe", 0)
    debt_ratio = fund_metrics.get("debt_to_equity", 0)
    revenue_growth = fund_metrics.get("revenue_growth", 0)

    business_model = (
        f"{ticker} présente un profil fondamental avec un score de {fund_score:.2f}. "
        f"Le rendement sur capitaux propres (ROE) est de {roe:.1%}, "
        f"avec un ratio dette/capitaux propres de {debt_ratio:.2f}. "
        f"La croissance des revenus est de {revenue_growth:.1%}. "
        f"Ces métriques suggèrent un modèle d'affaires {'solide' if fund_score >= 0.6 else 'modéré' if fund_score >= 0.4 else 'à surveiller'}. "
        f"{rationale} "
        f"L'analyse quantitative Python a attribué la note {grade} avec un score composite de {score:.2f}."
    )

    # Build technical analysis from indicators
    tech_indicators = quant.technical_indicators
    rsi = tech_indicators.get("rsi", 50)
    macd = tech_indicators.get("macd", 0)

    support_resistance = (
        f"Analyse technique avec score {tech_score:.2f}. "
        f"RSI actuel: {rsi:.1f} ({'suracheté' if rsi > 70 else 'survendu' if rsi < 30 else 'neutre'}). "
        f"MACD: {macd:.3f} ({'signal haussier' if macd > 0 else 'signal baissier'}). "
        f"Les niveaux de support et résistance sont déterminés par l'analyse des moyennes mobiles."
    )

    entry_exit = (
        f"Stratégie d'entrée basée sur le score technique de {tech_score:.2f}. "
        f"Recommandation: {rec}. "
        f"{'Accumuler sur les replis' if rec == 'BUY' else 'Attendre confirmation' if rec == 'HOLD' else 'Réduire exposition'} "
        f"avec gestion du risque appropriée. "
        f"Le score de risque de {risk_score:.2f} suggère une volatilité {'élevée' if risk_score < 0.4 else 'modérée' if risk_score < 0.7 else 'faible'}."
    )

    # Build investment thesis
    risk_metrics = quant.risk_metrics
    volatility = risk_metrics.get("volatility", 0)
    beta = risk_metrics.get("beta", 1)
    max_drawdown = risk_metrics.get("max_drawdown", 0)

    investment_thesis = (
        f"Analyse quantitative complète pour {ticker} ({ctx.asset_class}). "
        f"Note finale: {grade} avec score composite {score:.2f}. "
        f"Recommandation Python: {rec}. "
        f"Score fondamental: {fund_score:.2f} - ROE {roe:.1%}, ratio dette {debt_ratio:.2f}, croissance {revenue_growth:.1%}. "
        f"Score technique: {tech_score:.2f} - RSI {rsi:.1f}, MACD {macd:.3f}. "
        f"Score risque: {risk_score:.2f} - Volatilité {volatility:.1%}, Beta {beta:.2f}, Drawdown max {max_drawdown:.1%}. "
        f"Justification: {rationale} "
        f"Cette analyse est générée en mode MAXIMUM_SPEED sans appel AI pour optimiser les performances. "
        f"Pour une analyse qualitative approfondie avec contexte sectoriel et analyse des filings SEC, "
        f"désactivez le mode MAXIMUM_SPEED dans la configuration."
    )

    bull_case = (
        f"Scénario haussier: Si les fondamentaux s'améliorent au-delà du score actuel de {fund_score:.2f}, "
        f"et que les indicateurs techniques confirment avec RSI > 50 et MACD positif, "
        f"{ticker} pourrait surperformer. Catalyseurs potentiels: amélioration du ROE, réduction de la dette, "
        f"momentum technique positif. Probabilité estimée basée sur le grade {grade}."
    )

    base_case = (
        f"Scénario de base: Maintien du profil actuel avec score {score:.2f} et grade {grade}. "
        f"Les métriques fondamentales restent stables, les indicateurs techniques oscillent autour des niveaux actuels. "
        f"Performance alignée avec le secteur. Recommandation {rec} reste appropriée."
    )

    bear_case = (
        f"Scénario baissier: Détérioration des fondamentaux en dessous du score {fund_score:.2f}, "
        f"signaux techniques négatifs avec RSI < 30 et MACD négatif, "
        f"augmentation de la volatilité au-delà de {volatility:.1%}. "
        f"Risque de drawdown supérieur à {max_drawdown:.1%}."
    )

    # Scenario probabilities based on score
    if score >= 0.7:
        probs = ScenarioProbabilities(bull=0.40, base=0.45, bear=0.15)
    elif score >= 0.5:
        probs = ScenarioProbabilities(bull=0.25, base=0.50, bear=0.25)
    else:
        probs = ScenarioProbabilities(bull=0.15, base=0.45, bear=0.40)

    return QualitativeInsights(
        sec_insights=SecAnalysisInsights(
            business_model=business_model,
            competitive_advantages=[f"Score fondamental {fund_score:.2f}", f"Grade {grade}"],
            risk_factors=[f"Volatilité {volatility:.1%}", f"Beta {beta:.2f}", f"Drawdown max {max_drawdown:.1%}"],
            strategic_initiatives=["Analyse Python MAXIMUM_SPEED mode"],
        ),
        fundamental_context=FundamentalContextInsights(
            industry_analysis=f"Analyse sectorielle basée sur métriques quantitatives. Score fondamental: {fund_score:.2f}. {rationale}",
            growth_drivers=[f"ROE: {roe:.1%}", f"Croissance revenus: {revenue_growth:.1%}"],
            competitive_positioning=f"Position basée sur score {score:.2f} et grade {grade}. {sentiment.capitalize()} par rapport au marché.",
            management_assessment=f"Évaluation basée sur métriques quantitatives: ratio dette {debt_ratio:.2f}, ROE {roe:.1%}.",
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=[f"RSI: {rsi:.1f}", f"MACD: {macd:.3f}"],
            support_resistance=support_resistance,
            entry_exit_strategy=entry_exit,
            timing_assessment=f"Score technique {tech_score:.2f}. {'Timing favorable' if tech_score >= 0.6 else 'Attendre confirmation'}.",
        ),
        contextual_risks=ContextualRiskInsights(
            regulatory_risks=["Non évalué en mode MAXIMUM_SPEED"],
            geopolitical_risks=["Non évalué en mode MAXIMUM_SPEED"],
            competitive_risks=["Non évalué en mode MAXIMUM_SPEED"],
            operational_risks=[f"Volatilité: {volatility:.1%}"],
            stress_scenarios=[f"Drawdown max historique: {max_drawdown:.1%}"],
        ),
        investment_synthesis=InvestmentSynthesis(
            investment_thesis=investment_thesis,
            bull_case=bull_case,
            base_case=base_case,
            bear_case=bear_case,
            scenario_probabilities=probs,
            final_recommendation=cast(Literal["BUY", "HOLD", "SELL"], rec),
            recommendation_confidence="MEDIUM",
            action_plan=ActionPlan(
                immediate_actions=[f"Suivre recommandation {rec}", "Surveiller indicateurs techniques"],
                monitoring_points=["RSI", "MACD", "Volatilité"],
                exit_triggers=[f"Drawdown > {abs(max_drawdown) * 1.5:.1%}", "RSI > 80 ou < 20"],
            ),
        ),
        analysis_timestamp=datetime.now(),
        ai_confidence=0.7,  # Python analysis confidence
    )


def _create_fallback_qualitative(ctx: AnalysisContext, quant: QuantitativeAnalysis, error: str) -> QualitativeInsights:
    """Create fallback QualitativeInsights when AI fails."""
    fallback_text = f"Analysis unavailable due to AI failure: {error}. " * 5

    return QualitativeInsights(
        sec_insights=SecAnalysisInsights(
            business_model=fallback_text,
            competitive_advantages=["Unavailable due to AI failure"],
            risk_factors=["AI analysis failed - rely on Python metrics"],
            strategic_initiatives=[],
        ),
        fundamental_context=FundamentalContextInsights(
            industry_analysis=fallback_text,
            growth_drivers=["Unavailable"],
            competitive_positioning=fallback_text,
            management_assessment=fallback_text,
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=["Unavailable"],
            support_resistance=fallback_text,
            entry_exit_strategy=fallback_text,
            timing_assessment=fallback_text,
        ),
        contextual_risks=ContextualRiskInsights(
            regulatory_risks=["Analyse indisponible (echec AI)"],
            geopolitical_risks=["Analyse indisponible (echec AI)"],
            competitive_risks=["Analyse indisponible (echec AI)"],
            operational_risks=["Analyse indisponible (echec AI)"],
            stress_scenarios=["Analyse indisponible (echec AI)"],
        ),
        investment_synthesis=InvestmentSynthesis(
            investment_thesis=(
                f"FALLBACK: AI analysis failed for {ctx.ticker}. "
                f"Python analysis: Grade {quant.grade}, Score {quant.composite_score:.2f}, "
                f"Recommendation {quant.preliminary_recommendation}. "
                f"{quant.python_rationale} " * 3
            ),
            bull_case="Unavailable due to AI failure. " * 10,
            base_case="Unavailable due to AI failure. " * 10,
            bear_case="Unavailable due to AI failure. " * 10,
            scenario_probabilities=ScenarioProbabilities(bull=0.0, base=1.0, bear=0.0),
            final_recommendation=cast(Literal["BUY", "HOLD", "SELL"], quant.preliminary_recommendation),
            recommendation_confidence="LOW",
            action_plan=ActionPlan(
                immediate_actions=["Review Python metrics manually"],
                monitoring_points=["Re-run analysis when AI is available"],
                exit_triggers=["Significant price movement"],
            ),
        ),
        analysis_timestamp=datetime.now(),
        ai_confidence=0.0,
    )
