"""
Individual deep analysis report generation using Jinja2 templates.

This module handles generation of individual HTML reports for each
holding's deep analysis using the enriched_analysis_report.html template.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _get_jinja_env() -> Environment:
    """Get configured Jinja2 environment."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )


def _prepare_enriched_context(ticker: str, result: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare context variables for the enriched analysis template.

    Maps the result dict to the template's expected variables with defaults.
    """
    # Extract scores (support multiple key formats)
    composite_score = result.get("composite_score") or result.get("final_score") or 0
    fundamental_score = result.get("fundamental_score", 0)
    technical_score = result.get("technical_score", 0)
    risk_score = result.get("risk_score", 0)

    # Extract grade and recommendation
    grade = result.get("grade") or result.get("final_grade") or "N/A"
    recommendation = (
        result.get("recommendation") or result.get("final_recommendation") or "HOLD"
    )

    # Extract details dicts (these become the metric tables)
    fundamental_metrics = result.get("fundamental_details") or result.get(
        "fundamental_metrics", {}
    )
    technical_indicators = result.get("technical_details") or result.get(
        "technical_indicators", {}
    )
    risk_metrics = result.get("risk_details") or result.get("risk_metrics", {})

    # Build SEC insights structure
    sec_insights = result.get("sec_insights", {})
    if not isinstance(sec_insights, dict):
        sec_insights = {}

    # Build fundamental context structure
    fundamental_context = result.get("fundamental_context", {})
    if not isinstance(fundamental_context, dict):
        fundamental_context = {}

    # Build technical strategy structure
    technical_strategy = result.get("technical_strategy", {})
    if not isinstance(technical_strategy, dict):
        technical_strategy = {}

    # Build contextual risks structure
    contextual_risks = result.get("contextual_risks", {})
    if not isinstance(contextual_risks, dict):
        contextual_risks = {}

    # Build investment synthesis structure
    investment_synthesis = result.get("investment_synthesis", {})
    if not isinstance(investment_synthesis, dict):
        investment_synthesis = {}

    # Ensure nested structures exist
    if "scenario_probabilities" not in investment_synthesis:
        investment_synthesis["scenario_probabilities"] = {
            "bull": 0.25,
            "base": 0.50,
            "bear": 0.25,
        }
    if "action_plan" not in investment_synthesis:
        investment_synthesis["action_plan"] = {
            "immediate_actions": [],
            "monitoring_points": [],
            "exit_triggers": [],
        }

    # Build qualitative metrics with required ai_confidence
    qualitative = result.get("qualitative", {})
    if not isinstance(qualitative, dict):
        qualitative = {}
    if "ai_confidence" not in qualitative:
        qualitative["ai_confidence"] = 0.85

    # Return complete context
    return {
        # Header info
        "ticker": ticker,
        "company_name": result.get("company_name", ticker),
        "asset_class": result.get("asset_class", "stock"),
        "analysis_date": result.get("analysis_date") or datetime.now(),
        "processing_time_seconds": result.get("processing_time_seconds", 0),
        "llm_cost_dollars": result.get("llm_cost_dollars", 0),
        # Executive summary
        "executive_summary": result.get(
            "executive_summary",
            f"Analyse approfondie de {ticker} avec score composite de {composite_score:.0%}.",
        ),
        # Recommendation
        "final_recommendation": recommendation.upper(),
        "final_grade": grade,
        "recommendation_confidence": result.get("recommendation_confidence", "Medium"),
        "final_score": composite_score,
        # Quantitative scores
        "composite_score": composite_score,
        "fundamental_score": fundamental_score,
        "technical_score": technical_score,
        "risk_score": risk_score if risk_score > 1 else risk_score * 5,
        # Metric tables
        "fundamental_metrics": fundamental_metrics,
        "technical_indicators": technical_indicators,
        "risk_metrics": risk_metrics,
        # Investment thesis
        "investment_rationale": result.get(
            "investment_rationale",
            result.get(
                "rationale",
                f"Basé sur l'analyse quantitative, {ticker} présente un profil {_grade_to_profile(grade)}.",
            ),
        ),
        # SEC insights
        "sec_insights": {
            "business_model": sec_insights.get(
                "business_model", "Information non disponible dans les données actuelles."
            ),
            "competitive_advantages": sec_insights.get("competitive_advantages", []),
            "strategic_initiatives": sec_insights.get("strategic_initiatives", []),
        },
        # Fundamental context
        "fundamental_context": {
            "industry_analysis": fundamental_context.get(
                "industry_analysis", "Analyse sectorielle non disponible."
            ),
            "growth_drivers": fundamental_context.get("growth_drivers", []),
            "competitive_positioning": fundamental_context.get(
                "competitive_positioning", "Information non disponible."
            ),
            "management_assessment": fundamental_context.get(
                "management_assessment", "Évaluation non disponible."
            ),
        },
        # Technical strategy
        "technical_strategy": {
            "chart_patterns": technical_strategy.get("chart_patterns", []),
            "support_resistance": technical_strategy.get(
                "support_resistance", "Niveaux non calculés."
            ),
            "entry_exit_strategy": technical_strategy.get(
                "entry_exit_strategy", "Stratégie non définie."
            ),
            "timing_assessment": technical_strategy.get(
                "timing_assessment", "Évaluation du timing non disponible."
            ),
        },
        # Contextual risks
        "contextual_risks": {
            "regulatory_risks": contextual_risks.get("regulatory_risks", []),
            "geopolitical_risks": contextual_risks.get("geopolitical_risks", []),
            "competitive_risks": contextual_risks.get("competitive_risks", []),
            "operational_risks": contextual_risks.get("operational_risks", []),
            "stress_scenarios": contextual_risks.get("stress_scenarios", []),
        },
        # Investment synthesis
        "investment_synthesis": {
            "scenario_probabilities": investment_synthesis["scenario_probabilities"],
            "bull_case": investment_synthesis.get(
                "bull_case", "Scénario haussier non défini."
            ),
            "base_case": investment_synthesis.get(
                "base_case", "Scénario de base non défini."
            ),
            "bear_case": investment_synthesis.get(
                "bear_case", "Scénario baissier non défini."
            ),
            "action_plan": investment_synthesis["action_plan"],
        },
        # Quality metrics
        "report_word_count": result.get("report_word_count", 0),
        "unique_insights_count": result.get("unique_insights_count", 0),
        "qualitative": qualitative,
        # Footer
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _grade_to_profile(grade: str) -> str:
    """Convert grade to French profile description."""
    grade_profiles = {
        "A+": "d'investissement exceptionnel",
        "A": "d'investissement favorable",
        "B": "modéré avec potentiel",
        "C": "neutre à surveiller",
        "D": "défavorable avec risques",
        "F": "à éviter",
    }
    return grade_profiles.get(grade, "en cours d'évaluation")


def generate_individual_report_html(ticker: str, result: dict[str, Any]) -> str:
    """
    Generate HTML for individual deep analysis report using Jinja2 template.

    Args:
        ticker: The stock/asset ticker symbol
        result: Analysis result dictionary with scores and details

    Returns:
        Rendered HTML string
    """
    env = _get_jinja_env()
    template = env.get_template("enriched_analysis_report.html")
    context = _prepare_enriched_context(ticker, result)
    return template.render(**context)


def generate_individual_deep_analysis_reports(
    results_by_ticker: dict[str, Any],
    output_dir: Path,
) -> list[str]:
    """
    Generate individual HTML reports for each deep analysis.

    Args:
        results_by_ticker: Dictionary mapping tickers to analysis results
        output_dir: Base output directory

    Returns:
        List of paths to generated reports
    """
    logger.info(
        f"Generating individual HTML reports for {len(results_by_ticker)} deep analyses..."
    )
    generated_paths: list[str] = []

    for ticker, result in results_by_ticker.items():
        try:
            # Generate individual report using Jinja2 template
            individual_html = generate_individual_report_html(ticker, result)

            # Determine output path based on asset class
            asset_class = result.get("asset_class", "unknown")
            report_dir = output_dir / f"deep_analysis_{asset_class}"
            report_dir.mkdir(parents=True, exist_ok=True)

            report_path = report_dir / f"{ticker}_deep_analysis.html"

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(individual_html)

            generated_paths.append(str(report_path))
            logger.info(f"Generated individual report for {ticker}: {report_path}")

        except Exception as e:
            logger.error(f"Failed to generate individual report for {ticker}: {e}")

    return generated_paths
