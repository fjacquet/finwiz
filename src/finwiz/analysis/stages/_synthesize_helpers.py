"""Helper functions for the synthesize stage (executive summary, word count, etc.)."""

from __future__ import annotations

from finwiz.schemas.hybrid_analysis import QualitativeInsights, QuantitativeAnalysis


def _generate_executive_summary(quant: QuantitativeAnalysis, qual: QualitativeInsights) -> str:
    """Render the executive summary as a short HTML headline + 3-5 bullets.

    The output is consumed by templates via ``{{ executive_summary | safe }}``. Long
    qualitative content (industry analysis, competitive positioning, full thesis)
    lives in its own sections later in the report — the summary is intentionally
    short and structured, not a wall of prose.
    """
    from html import escape

    rec = quant.preliminary_recommendation
    rec_emoji = "✅" if rec == "BUY" else ("❌" if rec == "SELL" else "⏸️")
    conf_map = {"LOW": "FAIBLE", "MEDIUM": "MOYENNE", "HIGH": "ÉLEVÉE"}
    confidence = conf_map.get(
        qual.investment_synthesis.recommendation_confidence if qual.investment_synthesis else "MEDIUM",
        "MOYENNE",
    )

    headline = f'<p class="exec-headline"><strong>Grade {escape(quant.grade)} ({quant.composite_score:.2f}) · {rec_emoji} {escape(rec)} · Confiance {confidence}</strong></p>'

    bullets: list[str] = []

    # Fundamentals — drivers from real metrics, not prose
    fund_metrics = quant.fundamental_metrics or {}
    fund_drivers: list[str] = []
    if "roe" in fund_metrics:
        fund_drivers.append(f"ROE {fund_metrics['roe'] * 100:.0f}%")
    if "revenue_growth" in fund_metrics:
        fund_drivers.append(f"croissance {fund_metrics['revenue_growth'] * 100:.0f}%")
    if "debt_to_equity" in fund_metrics:
        fund_drivers.append(f"D/E {fund_metrics['debt_to_equity']:.2f}")
    if "expense_ratio" in fund_metrics:
        fund_drivers.append(f"frais {fund_metrics['expense_ratio'] * 100:.2f}%")
    fund_text = f"Fondamentaux {quant.fundamental_score * 100:.0f}%"
    if fund_drivers:
        fund_text += " — " + ", ".join(fund_drivers[:3])
    bullets.append(fund_text)

    # Technical — RSI + trend if available
    tech_metrics = quant.technical_indicators or {}
    tech_drivers: list[str] = []
    if "rsi" in tech_metrics:
        rsi = tech_metrics["rsi"]
        rsi_label = "neutre" if 40 <= rsi <= 60 else ("suracheté" if rsi > 70 else ("survendu" if rsi < 30 else "tendanciel"))
        tech_drivers.append(f"RSI {rsi:.0f} ({rsi_label})")
    if "trend_strength" in tech_metrics:
        tech_drivers.append(f"force tendance {tech_metrics['trend_strength']:.2f}")
    tech_text = f"Technique {quant.technical_score * 100:.0f}%"
    if tech_drivers:
        tech_text += " — " + ", ".join(tech_drivers[:2])
    bullets.append(tech_text)

    # Risk — volatility + drawdown
    risk_metrics = quant.risk_metrics or {}
    risk_drivers: list[str] = []
    if "volatility" in risk_metrics:
        risk_drivers.append(f"vol {risk_metrics['volatility'] * 100:.0f}%")
    if "max_drawdown" in risk_metrics:
        risk_drivers.append(f"drawdown {risk_metrics['max_drawdown'] * 100:.0f}%")
    if "beta" in risk_metrics:
        risk_drivers.append(f"β {risk_metrics['beta']:.2f}")
    risk_text = f"Risque {quant.risk_score:.1f}/5"
    if risk_drivers:
        risk_text += " — " + ", ".join(risk_drivers[:3])
    bullets.append(risk_text)

    # Thesis — first sentence only, never truncated mid-word
    if qual.investment_synthesis and qual.investment_synthesis.investment_thesis:
        thesis = qual.investment_synthesis.investment_thesis.strip()
        first_sentence = thesis.split(".")[0].strip()
        if first_sentence:
            bullets.append(f"Thèse : {first_sentence}.")

    bullets_html = '<ul class="exec-bullets">' + "".join(f"<li>{escape(b)}</li>" for b in bullets) + "</ul>"
    return headline + bullets_html


def _get_investment_rationale(qual: QualitativeInsights) -> str:
    """Get investment rationale from qualitative insights."""
    if qual.investment_synthesis and qual.investment_synthesis.investment_thesis:
        return qual.investment_synthesis.investment_thesis
    return "Investment rationale unavailable."


def _get_confidence(qual: QualitativeInsights) -> str:
    """Get recommendation confidence from qualitative insights."""
    if qual.investment_synthesis and qual.investment_synthesis.recommendation_confidence:
        return qual.investment_synthesis.recommendation_confidence
    return "MEDIUM"


def _calculate_word_count(
    executive_summary: str,
    investment_rationale: str,
    qual: QualitativeInsights,
) -> int:
    """Calculate total word count from all text content."""
    sections = [executive_summary, investment_rationale]

    if qual.sec_insights:
        sections.append(qual.sec_insights.business_model)
        sections.extend(qual.sec_insights.competitive_advantages)
        sections.extend(qual.sec_insights.risk_factors)
        sections.extend(qual.sec_insights.strategic_initiatives)

    if qual.fundamental_context:
        sections.append(qual.fundamental_context.industry_analysis)
        sections.extend(qual.fundamental_context.growth_drivers)
        sections.append(qual.fundamental_context.competitive_positioning)
        sections.append(qual.fundamental_context.management_assessment)

    if qual.technical_strategy:
        sections.extend(qual.technical_strategy.chart_patterns)
        sections.append(qual.technical_strategy.support_resistance)
        sections.append(qual.technical_strategy.entry_exit_strategy)
        sections.append(qual.technical_strategy.timing_assessment)

    if qual.contextual_risks:
        sections.extend(qual.contextual_risks.regulatory_risks)
        sections.extend(qual.contextual_risks.geopolitical_risks)
        sections.extend(qual.contextual_risks.competitive_risks)
        sections.extend(qual.contextual_risks.operational_risks)
        sections.extend(qual.contextual_risks.stress_scenarios)

    if qual.investment_synthesis:
        sections.append(qual.investment_synthesis.investment_thesis)
        sections.append(qual.investment_synthesis.bull_case)
        sections.append(qual.investment_synthesis.base_case)
        sections.append(qual.investment_synthesis.bear_case)

    combined = " ".join(str(s) for s in sections if s)
    return len(combined.split())


def _count_unique_insights(qual: QualitativeInsights) -> int:
    """Count unique qualitative insights."""
    insights: list[str] = []

    if qual.sec_insights:
        insights.extend(qual.sec_insights.competitive_advantages)
        insights.extend(qual.sec_insights.risk_factors)
        insights.extend(qual.sec_insights.strategic_initiatives)

    if qual.fundamental_context:
        insights.extend(qual.fundamental_context.growth_drivers)

    if qual.investment_synthesis:
        insights.append(qual.investment_synthesis.bull_case)
        insights.append(qual.investment_synthesis.base_case)
        insights.append(qual.investment_synthesis.bear_case)

    return len(set(i for i in insights if i))
