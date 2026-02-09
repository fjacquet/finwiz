"""Tests for per-holding sentiment section rendering in both report templates."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from finwiz.reporting.deep_analysis_report_generator import DeepAnalysisReportGenerator
from finwiz.reporting.enriched_analysis_report_generator import EnrichedAnalysisReportGenerator

# --- Fixtures ---

SAMPLE_SENTIMENT_DATA: dict[str, Any] = {
    "score": 0.65,
    "confidence": 0.82,
    "article_count": 15,
    "bullish_count": 10,
    "bearish_count": 3,
    "neutral_count": 2,
    "top_headlines": [
        {"title": "Apple lance un nouveau produit", "source": "Reuters", "sentiment_label": "bullish"},
        {"title": "Resultats trimestriels solides", "source": "Bloomberg", "sentiment_label": "bullish"},
    ],
}

BEARISH_SENTIMENT_DATA: dict[str, Any] = {
    "score": -0.45,
    "confidence": 0.70,
    "article_count": 8,
    "bullish_count": 2,
    "bearish_count": 5,
    "neutral_count": 1,
    "top_headlines": [
        {"title": "Chute des ventes trimestrielles", "source": "Reuters", "sentiment_label": "bearish"},
    ],
}

NEUTRAL_SENTIMENT_DATA: dict[str, Any] = {
    "score": 0.05,
    "confidence": 0.60,
    "article_count": 5,
    "bullish_count": 2,
    "bearish_count": 2,
    "neutral_count": 1,
    "top_headlines": [],
}


def _make_enriched_data(sentiment_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build minimal enriched analysis data for template rendering."""
    return {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "asset_class": "stock",
        "analysis_date": datetime.now(),
        "processing_time_seconds": 10.0,
        "llm_cost_dollars": 0.05,
        "executive_summary": " ".join(["Test executive summary sentence."] * 50),
        "investment_rationale": " ".join(["Test investment rationale sentence."] * 120),
        "final_grade": "A",
        "final_score": 0.85,
        "final_recommendation": "BUY",
        "recommendation_confidence": "HIGH",
        "report_word_count": 2500,
        "unique_insights_count": 7,
        "quantitative": {
            "composite_score": 0.85,
            "fundamental_score": 0.88,
            "technical_score": 0.80,
            "risk_score": 2.5,
            "grade": "A",
            "preliminary_recommendation": "BUY",
            "fundamental_metrics": {"roe": 0.25},
            "technical_indicators": {"rsi": 55.0},
            "risk_metrics": {"volatility": 0.20},
        },
        "qualitative": {
            "sec_insights": {
                "business_model": "Test business model.",
                "competitive_advantages": ["Brand strength"],
                "strategic_initiatives": ["Market expansion"],
            },
            "fundamental_context": {
                "industry_analysis": "Test industry.",
                "growth_drivers": ["Innovation"],
                "competitive_positioning": "Leader",
                "management_assessment": "Strong team",
            },
            "technical_strategy": {
                "chart_patterns": ["Bullish flag"],
                "support_resistance": "Support at $150",
                "entry_exit_strategy": "Buy on dips",
                "timing_assessment": "Favorable",
            },
            "contextual_risks": {
                "regulatory_risks": ["Antitrust"],
                "geopolitical_risks": [],
                "competitive_risks": [],
                "operational_risks": [],
                "stress_scenarios": [],
            },
            "investment_synthesis": {
                "bull_case": "Strong growth",
                "base_case": "Steady growth",
                "bear_case": "Slowdown",
                "scenario_probabilities": {"bull": 0.3, "base": 0.5, "bear": 0.2},
                "action_plan": {
                    "immediate_actions": ["Buy"],
                    "monitoring_points": ["Earnings"],
                    "exit_triggers": ["Support break"],
                },
            },
            "ai_confidence": 0.85,
        },
        "sentiment_summary": sentiment_data,
    }


def _make_deep_analysis_data(sentiment_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build minimal deep analysis data for template rendering."""
    return {
        "ticker": "AAPL",
        "asset_class": "stock",
        "composite_score": 0.85,
        "grade": "A",
        "recommendation": "BUY",
        "confidence": 0.90,
        "rationale": "Apple shows strong fundamentals.",
        "fundamental_score": 0.88,
        "technical_score": 0.82,
        "risk_score": 0.85,
        "fundamental_details": {"roe": 0.25, "debt_to_equity": 0.35},
        "technical_details": {"rsi": 55.0, "trend_direction": "uptrend"},
        "risk_details": {"volatility": 0.18, "max_drawdown": -0.12, "beta": 1.1},
        "analysis_date": datetime.now(),
        "session_id": "test_session",
        "sentiment_data": sentiment_data,
    }


class TestEnrichedSentimentRendering:
    """Test sentiment section rendering in enriched analysis template."""

    @pytest.fixture
    def generator(self) -> EnrichedAnalysisReportGenerator:
        """Create enriched analysis report generator."""
        return EnrichedAnalysisReportGenerator()

    def test_enriched_sentiment_section_present(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template shows sentiment section when data is available."""
        data = _make_enriched_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "Sentiment de Marche" in html

    def test_enriched_sentiment_score_displayed(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template shows sentiment score value."""
        data = _make_enriched_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "0.65" in html

    def test_enriched_confidence_displayed(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template shows confidence percentage."""
        data = _make_enriched_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "82%" in html

    def test_enriched_article_count_displayed(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template shows article count."""
        data = _make_enriched_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert ">15<" in html

    def test_enriched_headlines_displayed(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template shows headline titles."""
        data = _make_enriched_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "Apple lance un nouveau produit" in html
        assert "Resultats trimestriels solides" in html

    def test_enriched_headline_sources_displayed(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template shows headline sources."""
        data = _make_enriched_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "Reuters" in html
        assert "Bloomberg" in html

    def test_enriched_no_sentiment_no_section(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template hides sentiment section when data is None."""
        data = _make_enriched_data(None)
        html = generator.generate_report(data)
        assert "Sentiment de Marche" not in html

    def test_enriched_sentiment_color_bullish(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template uses green color for positive sentiment score."""
        data = _make_enriched_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "#22c55e" in html

    def test_enriched_sentiment_color_bearish(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template uses red color for negative sentiment score."""
        data = _make_enriched_data(BEARISH_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "#ef4444" in html

    def test_enriched_sentiment_color_neutral(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template uses neutral color for neutral sentiment score."""
        data = _make_enriched_data(NEUTRAL_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "#64748b" in html

    def test_enriched_sentiment_badges(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template shows sentiment badges for headlines."""
        data = _make_enriched_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "badge-bullish" in html

    def test_enriched_no_headlines_no_list(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template hides headlines list when empty."""
        data = _make_enriched_data(NEUTRAL_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "Sentiment de Marche" in html
        assert "Titres Recents" not in html

    def test_enriched_french_labels(self, generator: EnrichedAnalysisReportGenerator) -> None:
        """Enriched template uses French labels for sentiment section."""
        data = _make_enriched_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "Score de Sentiment" in html
        assert "Confiance" in html
        assert "Articles Analyses" in html
        assert "Titres Recents" in html


class TestDeepAnalysisSentimentRendering:
    """Test sentiment section rendering in deep analysis template."""

    @pytest.fixture
    def generator(self) -> DeepAnalysisReportGenerator:
        """Create deep analysis report generator."""
        return DeepAnalysisReportGenerator()

    def test_deep_analysis_sentiment_section_present(self, generator: DeepAnalysisReportGenerator) -> None:
        """Deep analysis template shows sentiment section when data is available."""
        data = _make_deep_analysis_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "Sentiment de Marche" in html

    def test_deep_analysis_sentiment_score(self, generator: DeepAnalysisReportGenerator) -> None:
        """Deep analysis template shows sentiment score value."""
        data = _make_deep_analysis_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "0.65" in html

    def test_deep_analysis_confidence(self, generator: DeepAnalysisReportGenerator) -> None:
        """Deep analysis template shows confidence percentage."""
        data = _make_deep_analysis_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "82%" in html

    def test_deep_analysis_no_sentiment_no_section(self, generator: DeepAnalysisReportGenerator) -> None:
        """Deep analysis template hides sentiment section when data is None."""
        data = _make_deep_analysis_data(None)
        html = generator.generate_report(data)
        assert "Sentiment de Marche" not in html

    def test_deep_analysis_uses_risk_classes_bullish(self, generator: DeepAnalysisReportGenerator) -> None:
        """Deep analysis template uses risk-low class for positive sentiment."""
        data = _make_deep_analysis_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "risk-low" in html

    def test_deep_analysis_uses_risk_classes_bearish(self, generator: DeepAnalysisReportGenerator) -> None:
        """Deep analysis template uses risk-high class for negative sentiment."""
        data = _make_deep_analysis_data(BEARISH_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "risk-high" in html

    def test_deep_analysis_headlines_displayed(self, generator: DeepAnalysisReportGenerator) -> None:
        """Deep analysis template shows headline titles."""
        data = _make_deep_analysis_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "Apple lance un nouveau produit" in html

    def test_deep_analysis_french_labels(self, generator: DeepAnalysisReportGenerator) -> None:
        """Deep analysis template uses French labels for sentiment section."""
        data = _make_deep_analysis_data(SAMPLE_SENTIMENT_DATA)
        html = generator.generate_report(data)
        assert "Score de Sentiment" in html
        assert "Confiance" in html
        assert "Articles Analyses" in html
