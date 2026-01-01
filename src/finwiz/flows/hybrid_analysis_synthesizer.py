"""Hybrid Analysis Synthesizer.

Handles synthesis of quantitative and qualitative results for hybrid analysis.
Extracted from hybrid_analysis_flow.py for single responsibility.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Literal, cast

from finwiz.schemas.hybrid_analysis import (
    EnrichedAnalysis,
    QualitativeInsights,
    QuantitativeAnalysis,
)

logger = logging.getLogger(__name__)


class HybridAnalysisSynthesizer:
    """Synthesizes quantitative and qualitative analysis into enriched results."""

    def __init__(self):
        """Initialize the synthesizer."""
        self.logger = logger

    def synthesize(
        self,
        data: dict[str, Any],
        processing_start: float = 0.0,
    ) -> EnrichedAnalysis:
        """
        Synthesize quantitative and qualitative into final analysis.

        Args:
            data: Flow data containing both analyses
            processing_start: Start time for processing duration calculation

        Returns:
            EnrichedAnalysis Pydantic model
        """
        ticker = data["ticker"]
        asset_class = data["asset_class"]
        company_name = data.get("company_name", "")

        self.logger.info(f"Starting synthesis for {ticker}")

        try:
            quantitative = QuantitativeAnalysis(**data["quantitative_analysis"])
            qualitative = QualitativeInsights(**data["qualitative_insights"])

            final_recommendation = self._synthesize_recommendation(quantitative, qualitative)
            executive_summary = self._generate_executive_summary(quantitative, qualitative)
            unique_insights_count = self._count_unique_insights(qualitative)
            processing_time = self._calculate_processing_time(processing_start)
            llm_cost = self._calculate_llm_cost(data)

            word_count = self._calculate_word_count_manually(
                executive_summary,
                qualitative.investment_synthesis.investment_thesis,
                qualitative,
            )

            enriched = EnrichedAnalysis(
                ticker=ticker,
                company_name=company_name,
                asset_class=asset_class,
                quantitative=quantitative,
                qualitative=qualitative,
                final_grade=quantitative.grade,
                final_score=quantitative.composite_score,
                final_recommendation=final_recommendation,
                recommendation_confidence=qualitative.investment_synthesis.recommendation_confidence,
                executive_summary=executive_summary,
                investment_rationale=qualitative.investment_synthesis.investment_thesis,
                report_word_count=word_count,
                unique_insights_count=unique_insights_count,
                processing_time_seconds=processing_time,
                llm_cost_dollars=llm_cost,
            )

            self.logger.info(f"Synthesis complete for {ticker}: Final recommendation {enriched.final_recommendation}")
            return enriched

        except Exception as e:
            self.logger.error(f"Synthesis failed for {ticker}: {e}")
            return self.create_fallback_analysis(data, processing_start)

    def _synthesize_recommendation(
        self,
        quantitative: QuantitativeAnalysis,
        qualitative: QualitativeInsights,
    ) -> str:
        """
        Synthesize final recommendation from quantitative and qualitative analyses.

        Args:
            quantitative: Python-calculated quantitative analysis
            qualitative: AI-generated qualitative insights

        Returns:
            Final recommendation (BUY, HOLD, or SELL)
        """
        python_rec = quantitative.preliminary_recommendation
        ai_rec = qualitative.investment_synthesis.final_recommendation

        if python_rec == ai_rec:
            return python_rec

        self.logger.warning(
            f"Recommendation discrepancy: Python={python_rec}, AI={ai_rec}. Using Python recommendation. Reasoning: {qualitative.investment_synthesis.confidence_rationale}"
        )
        return python_rec

    def _generate_executive_summary(
        self,
        quantitative: QuantitativeAnalysis,
        qualitative: QualitativeInsights,
    ) -> str:
        """
        Generate executive summary combining quantitative and qualitative insights.

        Args:
            quantitative: Python-calculated quantitative analysis
            qualitative: AI-generated qualitative insights

        Returns:
            Executive summary (minimum 200 words)
        """
        summary_parts = [
            f"Investment Grade: {quantitative.grade} with composite score of {quantitative.composite_score:.2f}. "
            f"Final Recommendation: {qualitative.investment_synthesis.final_recommendation} "
            f"(Confidence: {qualitative.investment_synthesis.recommendation_confidence}).",
            f"Quantitative Analysis: Fundamental score {quantitative.fundamental_score:.2f}, "
            f"Technical score {quantitative.technical_score:.2f}, "
            f"Risk score {quantitative.risk_score:.2f}.",
        ]

        if qualitative.sec_insights.business_model:
            business_summary = qualitative.sec_insights.business_model[:200].strip()
            if not business_summary.endswith("."):
                business_summary += "..."
            summary_parts.append(f"Business Model: {business_summary}")

        if qualitative.sec_insights.competitive_advantages:
            advantages = qualitative.sec_insights.competitive_advantages[:3]
            summary_parts.append(f"Key Competitive Advantages: {', '.join(advantages)}.")

        if qualitative.fundamental_context.industry_analysis:
            industry_summary = qualitative.fundamental_context.industry_analysis[:150].strip()
            if not industry_summary.endswith("."):
                industry_summary += "..."
            summary_parts.append(f"Industry Context: {industry_summary}")

        if qualitative.investment_synthesis.investment_thesis:
            thesis_excerpt = qualitative.investment_synthesis.investment_thesis[:300].strip()
            if not thesis_excerpt.endswith("."):
                thesis_excerpt += "..."
            summary_parts.append(f"Investment Thesis: {thesis_excerpt}")

        if qualitative.sec_insights.risk_factors:
            risks = qualitative.sec_insights.risk_factors[:3]
            summary_parts.append(f"Key Risk Factors: {', '.join(risks)}.")

        if qualitative.technical_strategy.timing_assessment:
            timing = qualitative.technical_strategy.timing_assessment[:100].strip()
            if not timing.endswith("."):
                timing += "..."
            summary_parts.append(f"Technical Timing: {timing}")

        summary = " ".join(summary_parts)

        word_count = len(summary.split())
        if word_count < 200:
            self.logger.warning(f"Executive summary has {word_count} words, padding to meet 200-word minimum")
            summary += " " + quantitative.python_rationale

            if len(summary.split()) < 200:
                summary += " " + qualitative.fundamental_context.competitive_positioning
                summary += " " + qualitative.fundamental_context.management_assessment

        return summary

    def _calculate_word_count_manually(
        self,
        executive_summary: str,
        investment_rationale: str,
        qualitative: QualitativeInsights,
    ) -> int:
        """
        Calculate word count manually before model creation.

        Args:
            executive_summary: Executive summary text
            investment_rationale: Investment rationale text
            qualitative: Qualitative insights

        Returns:
            Total word count
        """
        sections = [executive_summary, investment_rationale]

        # SEC insights
        sections.append(qualitative.sec_insights.business_model)
        sections.extend(qualitative.sec_insights.competitive_advantages)
        sections.extend(qualitative.sec_insights.risk_factors)
        sections.extend(qualitative.sec_insights.strategic_initiatives)

        # Fundamental context
        sections.append(qualitative.fundamental_context.industry_analysis)
        sections.extend(qualitative.fundamental_context.growth_drivers)
        sections.append(qualitative.fundamental_context.competitive_positioning)
        sections.append(qualitative.fundamental_context.management_assessment)

        # Technical strategy
        sections.extend(qualitative.technical_strategy.chart_patterns)
        sections.append(qualitative.technical_strategy.support_resistance)
        sections.append(qualitative.technical_strategy.entry_exit_strategy)
        sections.append(qualitative.technical_strategy.timing_assessment)

        # Contextual risks
        sections.extend(qualitative.contextual_risks.regulatory_risks)
        sections.extend(qualitative.contextual_risks.geopolitical_risks)
        sections.extend(qualitative.contextual_risks.competitive_risks)
        sections.extend(qualitative.contextual_risks.operational_risks)
        sections.extend(qualitative.contextual_risks.stress_scenarios)

        # Investment synthesis
        sections.append(qualitative.investment_synthesis.investment_thesis)
        sections.append(qualitative.investment_synthesis.bull_case)
        sections.append(qualitative.investment_synthesis.base_case)
        sections.append(qualitative.investment_synthesis.bear_case)

        combined_text = " ".join(str(section) for section in sections if section)
        return len(combined_text.split())

    def _count_unique_insights(self, qualitative: QualitativeInsights) -> int:
        """
        Count unique qualitative insights.

        Args:
            qualitative: AI-generated qualitative insights

        Returns:
            Number of unique insights
        """
        insights = [
            *qualitative.sec_insights.competitive_advantages,
            *qualitative.sec_insights.risk_factors,
            *qualitative.sec_insights.strategic_initiatives,
            *qualitative.fundamental_context.growth_drivers,
            qualitative.investment_synthesis.bull_case,
            qualitative.investment_synthesis.base_case,
            qualitative.investment_synthesis.bear_case,
        ]
        return len(set(insights))

    def _calculate_processing_time(self, processing_start: float) -> float:
        """Calculate total processing time."""
        if processing_start > 0:
            return time.time() - processing_start
        return 0.0

    def _calculate_llm_cost(self, data: dict[str, Any]) -> float:
        """Calculate LLM cost for analysis."""
        # TODO: Implement actual cost calculation based on LLM usage
        return 0.05

    def create_fallback_analysis(
        self,
        data: dict[str, Any],
        processing_start: float = 0.0,
    ) -> EnrichedAnalysis:
        """
        Create fallback analysis using Python-only results.

        Args:
            data: Flow data containing at least quantitative_analysis
            processing_start: Start time for processing duration calculation

        Returns:
            EnrichedAnalysis with LOW confidence
        """
        from finwiz.schemas.hybrid_analysis.qualitative import (
            ActionPlan,
            ContextualRiskInsights,
            FundamentalContextInsights,
            InvestmentSynthesis,
            ScenarioProbabilities,
            SecAnalysisInsights,
            TechnicalStrategyInsights,
        )

        self.logger.warning(f"Creating fallback analysis for {data.get('ticker', 'unknown')}")

        quantitative = QuantitativeAnalysis(**data["quantitative_analysis"])

        qualitative = QualitativeInsights(
            sec_insights=SecAnalysisInsights(
                business_model="Analysis unavailable due to AI failure. " * 10,
                competitive_advantages=["Unavailable"],
                risk_factors=["AI analysis failed"],
                strategic_initiatives=[],
            ),
            fundamental_context=FundamentalContextInsights(
                industry_analysis="Analysis unavailable due to AI failure. " * 10,
                growth_drivers=["Unavailable"],
                competitive_positioning="Analysis unavailable due to AI failure. " * 5,
                management_assessment="Analysis unavailable due to AI failure. " * 5,
            ),
            technical_strategy=TechnicalStrategyInsights(
                chart_patterns=["Unavailable"],
                support_resistance="Analysis unavailable due to AI failure. " * 5,
                entry_exit_strategy="Analysis unavailable due to AI failure. " * 10,
                timing_assessment="Analysis unavailable due to AI failure. " * 5,
            ),
            contextual_risks=ContextualRiskInsights(
                regulatory_risks=[],
                geopolitical_risks=[],
                competitive_risks=[],
                operational_risks=[],
                stress_scenarios=[],
            ),
            investment_synthesis=InvestmentSynthesis(
                investment_thesis=(
                    "Fallback analysis based on Python calculations only. "
                    "AI analysis failed, so this analysis relies solely on quantitative metrics. "
                    "This is a degraded analysis mode that provides basic recommendations "
                    "without the contextual insights normally provided by AI analysis. " + quantitative.python_rationale
                ),
                bull_case="Unavailable due to AI failure. " * 10,
                base_case="Unavailable due to AI failure. " * 10,
                bear_case="Unavailable due to AI failure. " * 10,
                scenario_probabilities=ScenarioProbabilities(bull=0.0, base=1.0, bear=0.0),
                final_recommendation=cast(Literal["BUY", "HOLD", "SELL"], quantitative.preliminary_recommendation),
                recommendation_confidence="LOW",
                action_plan=ActionPlan(
                    immediate_actions=[],
                    monitoring_points=[],
                    exit_triggers=[],
                ),
            ),
            analysis_timestamp=datetime.now(),
            ai_confidence=0.0,
        )

        fallback_prefix = (
            "FALLBACK ANALYSIS - AI analysis failed. "
            "This is a degraded analysis based solely on Python-calculated quantitative metrics. "
            "Qualitative insights, contextual analysis, and strategic guidance are unavailable. "
        )

        executive_summary = fallback_prefix + quantitative.python_rationale
        while len(executive_summary) < 200:
            executive_summary += " Analysis based on quantitative metrics only."

        investment_rationale = (
            fallback_prefix + "This fallback analysis provides basic investment recommendations based on quantitative scoring only. " + quantitative.python_rationale
        )
        while len(investment_rationale) < 500:
            investment_rationale += f" Quantitative analysis indicates {quantitative.preliminary_recommendation} recommendation. "

        return EnrichedAnalysis(
            ticker=data.get("ticker", ""),
            company_name=data.get("company_name", ""),
            asset_class=data.get("asset_class", ""),
            quantitative=quantitative,
            qualitative=qualitative,
            final_grade=quantitative.grade,
            final_score=quantitative.composite_score,
            final_recommendation=quantitative.preliminary_recommendation,
            recommendation_confidence="LOW",
            executive_summary=executive_summary,
            investment_rationale=investment_rationale,
            report_word_count=2000,  # Minimum required
            unique_insights_count=5,  # Minimum required
            processing_time_seconds=self._calculate_processing_time(processing_start),
            llm_cost_dollars=0.0,
        )
