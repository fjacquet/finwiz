"""
Qualitative insights schemas for AI-generated contextual analysis.

This module provides Pydantic models for AI-generated qualitative insights
that complement Python-calculated quantitative metrics.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from finwiz.schemas.hybrid_analysis.fact_pack import FactPack
from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis


class SecAnalysisInsights(BaseModel):
    """
    SEC filings analysis insights (AI-generated).

    Qualitative analysis of business model, competitive advantages,
    and risk factors from SEC 10-K and 10-Q filings.
    """

    business_model: str = Field(
        default="",
        description=(
            "Modèle économique en 120-180 mots : comment le holding gagne de l'argent (action), "
            "stratégie de réplication et exposition (fonds), utilité et économie du protocole (crypto)."
        ),
    )
    competitive_advantages: list[str] = Field(
        default_factory=list,
        description="3 à 5 avantages durables, une phrase chacun, avec la preuve tirée du FACT PACK ou de la RECHERCHE STRATÉGIQUE.",
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="3 à 5 risques propres au holding, une phrase chacun, terminée par la gravité entre parenthèses : (faible), (moyenne) ou (élevée).",
    )
    strategic_initiatives: list[str] = Field(
        default_factory=list,
        description="2 à 4 initiatives en cours datées des 12 derniers mois avant la DATE D'ANALYSE, avec l'effet attendu.",
    )

    @field_validator("business_model", mode="before")
    @classmethod
    def coerce_business_model(cls, v: object) -> str:
        """Coerce dict to string (AI sometimes returns a dict for prose fields)."""
        if isinstance(v, dict):
            return " | ".join(f"{k}: {val}" for k, val in v.items())
        return str(v) if v is not None else ""

    @field_validator("risk_factors", mode="before")
    @classmethod
    def coerce_risk_factors(cls, v: list) -> list[str]:
        """Coerce dict entries (e.g. {'risk': '...', 'severity': '...'}) to strings."""
        result = []
        for item in v:
            if isinstance(item, dict):
                risk = item.get("risk", item.get("name", str(item)))
                severity = item.get("severity", "")
                result.append(f"{risk} (Sévérité: {severity})" if severity else str(risk))
            else:
                result.append(str(item))
        return result

    model_config = {
        "str_strip_whitespace": True,
    }


class FundamentalContextInsights(BaseModel):
    """
    Fundamental analysis context (AI-generated).

    Industry context, growth drivers, competitive positioning,
    and management assessment.
    """

    industry_analysis: str = Field(
        default="",
        description="Secteur et tendances en 80-120 mots, cohérents avec la DATE D'ANALYSE ; pas de chiffres déjà fournis par le CONTEXT Python.",
    )
    growth_drivers: list[str] = Field(
        default_factory=list,
        description="3 à 5 moteurs de croissance, un par ligne, sans recopier les métriques Python.",
    )
    competitive_positioning: str = Field(
        default="",
        description="Position concurrentielle en 60-100 mots, appuyée sur les cinq forces de la RECHERCHE STRATÉGIQUE.",
    )
    management_assessment: str = Field(
        default="",
        description=("Direction et gouvernance (action), émetteur et gestion (fonds), équipe et gouvernance du protocole (crypto), 40-80 mots, uniquement des faits du FACT PACK."),
    )

    @field_validator("industry_analysis", "competitive_positioning", "management_assessment", mode="before")
    @classmethod
    def coerce_prose_to_string(cls, v: object) -> str:
        """Coerce dict entries to strings (AI sometimes returns dicts for prose fields)."""
        if isinstance(v, dict):
            return " | ".join(f"{k}: {val}" for k, val in v.items())
        return str(v) if v is not None else ""

    model_config = {
        "str_strip_whitespace": True,
    }


class TechnicalStrategyInsights(BaseModel):
    """
    Technical analysis strategy (AI-generated).

    Chart patterns, support/resistance levels, entry/exit strategy,
    and timing assessment.
    """

    chart_patterns: list[str] = Field(
        default_factory=list,
        description="1 à 3 configurations lisibles dans les indicateurs fournis, nommées en une ligne ; liste vide si aucune.",
    )
    support_resistance: str = Field(
        default="",
        description="Niveaux de support et de résistance déduits des indicateurs fournis, avec la logique en une ou deux phrases.",
    )
    entry_exit_strategy: str = Field(default="", description="Plan d'entrée et de sortie avec des niveaux de prix, 40-80 mots.")
    timing_assessment: str = Field(
        default="",
        description="Momentum et timing en une ou deux phrases, cohérents avec le score technique du CONTEXT.",
    )

    @field_validator("support_resistance", "entry_exit_strategy", "timing_assessment", mode="before")
    @classmethod
    def coerce_prose_to_string(cls, v: object) -> str:
        """Coerce dict entries (e.g. {'support_levels': '...', 'resistance_levels': '...'}) to strings."""
        if isinstance(v, dict):
            return " | ".join(f"{k}: {val}" for k, val in v.items())
        return str(v) if v is not None else ""

    model_config = {
        "str_strip_whitespace": True,
    }


class ContextualRiskInsights(BaseModel):
    """
    Contextual risk analysis (AI-generated).

    Regulatory, geopolitical, competitive, and operational risks
    with stress scenarios.
    """

    regulatory_risks: list[str] = Field(
        default_factory=list,
        description="2 à 4 risques réglementaires ou de conformité propres au holding, datés s'ils tiennent à un événement.",
    )
    geopolitical_risks: list[str] = Field(
        default_factory=list,
        description="2 à 4 risques géopolitiques ou macroéconomiques qui touchent ce holding en particulier.",
    )
    competitive_risks: list[str] = Field(
        default_factory=list,
        description="2 à 4 risques concurrentiels ou de marché, nommant les acteurs concernés.",
    )
    operational_risks: list[str] = Field(
        default_factory=list,
        description="2 à 4 risques opérationnels ou d'exécution propres au holding.",
    )
    stress_scenarios: list[str] = Field(
        default_factory=list,
        description="2 à 3 scénarios de stress, chacun avec l'effet attendu sur le holding en une phrase.",
    )

    model_config = {
        "str_strip_whitespace": True,
    }


class ScenarioProbabilities(BaseModel):
    """Probabilities for bull/base/bear scenarios (must sum to 1.0)."""

    bull: float = Field(..., ge=0.0, le=1.0, description="Probabilité du scénario haussier entre 0 et 1 ; bull + base + bear = 1,0.")
    base: float = Field(..., ge=0.0, le=1.0, description="Probabilité du scénario central entre 0 et 1 ; bull + base + bear = 1,0.")
    bear: float = Field(..., ge=0.0, le=1.0, description="Probabilité du scénario baissier entre 0 et 1 ; bull + base + bear = 1,0.")

    model_config = {
        "str_strip_whitespace": True,
    }

    @model_validator(mode="after")
    def validate_probabilities_sum_to_one(self) -> "ScenarioProbabilities":
        """Ensure probabilities sum to 1.0 (with tolerance for floating point)."""
        total = self.bull + self.base + self.bear
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Probabilities must sum to 1.0, got {total:.4f}")
        return self


class ActionPlan(BaseModel):
    """Actionable steps for investment strategy."""

    immediate_actions: list[str] = Field(default_factory=list, description="2 à 4 actions concrètes et vérifiables à mener maintenant.")
    monitoring_points: list[str] = Field(
        default_factory=list,
        description="2 à 4 métriques ou événements à surveiller, avec le seuil qui compte.",
    )
    exit_triggers: list[str] = Field(default_factory=list, description="2 à 4 conditions précises qui déclencheraient la sortie.")

    model_config = {
        "str_strip_whitespace": True,
    }


class InvestmentSynthesis(BaseModel):
    """
    Investment synthesis and final recommendation (AI-generated).

    Investment thesis, bull/base/bear scenarios, final recommendation,
    and action plan.
    """

    investment_thesis: str = Field(
        default="",
        description="Thèse d'investissement en 150-250 mots qui relie les faits, la recherche stratégique et les scores Python.",
    )
    bull_case: str = Field(default="", description="Scénario haussier en 80-120 mots avec ses catalyseurs.")
    base_case: str = Field(default="", description="Scénario central en 80-120 mots, le plus probable.")
    bear_case: str = Field(default="", description="Scénario baissier en 80-120 mots avec ses risques déclencheurs.")
    scenario_probabilities: ScenarioProbabilities | None = Field(
        default=None,
        description="Probabilités bull, base et bear ; leur somme vaut 1,0.",
    )
    final_recommendation: Literal["BUY", "HOLD", "SELL"] = Field(
        default="HOLD",
        description="Recommandation finale : BUY, HOLD ou SELL.",
    )
    recommendation_confidence: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        default="MEDIUM",
        description="Confiance dans la recommandation : LOW, MEDIUM ou HIGH.",
    )
    action_plan: ActionPlan | None = Field(
        default=None,
        description="Plan d'action : immediate_actions, monitoring_points, exit_triggers.",
    )

    @field_validator("investment_thesis", "bull_case", "base_case", "bear_case", mode="before")
    @classmethod
    def coerce_prose_to_string(cls, v: object) -> str:
        """Coerce dict to string (AI sometimes returns a dict for prose fields)."""
        if isinstance(v, dict):
            return " | ".join(f"{k}: {val}" for k, val in v.items())
        return str(v) if v is not None else ""

    @model_validator(mode="before")
    @classmethod
    def provide_defaults_for_optional_fields(cls, values: object) -> object:
        """Ensure action_plan is never None (empty lists are honest; None hides the section)."""
        if not isinstance(values, dict):
            return values
        if values.get("action_plan") is None:
            values["action_plan"] = {"immediate_actions": [], "monitoring_points": [], "exit_triggers": []}
        return values

    model_config = {
        "str_strip_whitespace": True,
    }


class QualitativeInsights(BaseModel):
    """
    AI-generated qualitative analysis (contextual).

    Comprehensive qualitative insights that complement Python-calculated
    quantitative metrics. Provides context, interpretation, and strategic
    guidance.
    """

    # Investment Strategy — placed FIRST so LLM fills it before token budget runs out
    investment_synthesis: InvestmentSynthesis | None = Field(default=None, description="Synthèse d'investissement et recommandation.")

    # SEC Analysis
    sec_insights: SecAnalysisInsights | None = Field(
        default=None,
        description="Modèle économique, avantages, risques et initiatives du holding.",
    )

    # Fundamental Analysis
    fundamental_context: FundamentalContextInsights | None = Field(
        default=None,
        description="Contexte sectoriel, moteurs de croissance, positionnement, direction.",
    )

    # Technical Analysis
    technical_strategy: TechnicalStrategyInsights | None = Field(
        default=None,
        description="Lecture technique et plan d'entrée/sortie.",
    )

    # Risk Analysis
    contextual_risks: ContextualRiskInsights | None = Field(
        default=None,
        description="Risques réglementaires, géopolitiques, concurrentiels, opérationnels et scénarios de stress.",
    )

    # Strategic Analysis (SWOT + Porter's Five Forces, AI-generated via Perplexity)
    strategic_analysis: StrategicAnalysis | None = Field(default=None, description="Strategic frameworks (SWOT/Porter)")

    # Fact Pack (v5.2 grounded qualitative)
    fact_pack: FactPack | None = Field(
        default=None,
        description="Verified corporate facts (v5.2 fact pack). None when not yet fetched or pipeline pre-v5.2.",
    )

    # Metadata
    analysis_timestamp: datetime | None = Field(default=None, description="When AI analysis was performed (UTC)")
    ai_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confiance globale entre 0 et 1, fondée sur la couverture du FACT PACK et de la RECHERCHE STRATÉGIQUE.",
    )

    model_config = {
        "str_strip_whitespace": True,
    }
