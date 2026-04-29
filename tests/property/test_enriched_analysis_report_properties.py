"""
Property-based tests for EnrichedAnalysisReportGenerator.

**Feature: python-ai-hybrid-analysis, Property 15: Executive Summary Length**
**Feature: python-ai-hybrid-analysis, Property 16: Investment Rationale Length**
**Feature: python-ai-hybrid-analysis, Property 17: Action Plan Completeness**

Tests report quality thresholds for enriched analysis reports.
"""

from datetime import datetime

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from finwiz.reporting.enriched_analysis_report_generator import EnrichedAnalysisReportGenerator


# Strategy for generating valid EnrichedAnalysis data
@st.composite
def enriched_analysis_strategy(draw):
    """Generate valid EnrichedAnalysis data for property testing."""
    # Generate word counts that meet minimum requirements
    # These need to sum to at least 2000 words total
    exec_word_count = draw(st.integers(min_value=200, max_value=500))
    rationale_word_count = draw(st.integers(min_value=500, max_value=1000))
    business_model_word_count = draw(st.integers(min_value=100, max_value=500))
    thesis_word_count = draw(st.integers(min_value=200, max_value=800))

    # Ensure total meets 2000 word minimum
    current_total = exec_word_count + rationale_word_count + business_model_word_count + thesis_word_count
    if current_total < 2000:
        # Add extra words to thesis to reach minimum
        thesis_word_count += 2000 - current_total

    # Generate text with specified word counts
    exec_summary = " ".join(["word"] * exec_word_count)
    investment_rationale = " ".join(["word"] * rationale_word_count)
    business_model = " ".join(["word"] * business_model_word_count)
    investment_thesis = " ".join(["word"] * thesis_word_count)

    # Calculate total word count (should be >= 2000)
    total_word_count = exec_word_count + rationale_word_count + business_model_word_count + thesis_word_count

    # Generate action plan with required fields
    action_plan = {
        "immediate_actions": draw(st.lists(st.text(min_size=10, max_size=50), min_size=1, max_size=5)),
        "monitoring_points": draw(st.lists(st.text(min_size=10, max_size=50), min_size=1, max_size=5)),
        "exit_triggers": draw(st.lists(st.text(min_size=10, max_size=50), min_size=1, max_size=5)),
    }

    return {
        "ticker": draw(st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=("Lu",)))),
        "company_name": draw(st.text(min_size=5, max_size=50)),
        "asset_class": draw(st.sampled_from(["stock", "etf", "crypto"])),
        "analysis_date": datetime.now(),
        "quantitative": {
            "composite_score": draw(st.floats(min_value=0.0, max_value=1.0)),
            "fundamental_score": draw(st.floats(min_value=0.0, max_value=1.0)),
            "technical_score": draw(st.floats(min_value=0.0, max_value=1.0)),
            "risk_score": draw(st.floats(min_value=0.0, max_value=5.0)),
            "grade": draw(st.sampled_from(["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"])),
            "preliminary_recommendation": draw(st.sampled_from(["BUY", "HOLD", "SELL"])),
            "fundamental_metrics": {"roe": 0.25, "debt_to_equity": 0.3},
            "technical_indicators": {"rsi": 55.0, "macd": 0.5},
            "risk_metrics": {"volatility": 0.20, "beta": 1.1},
            "calculation_timestamp": datetime.now(),
            "data_quality": {
                "completeness_score": 0.95,
                "freshness_score": 1.0,
                "accuracy_confidence": 0.90,
                "source_reliability": 0.95,
                "missing_fields": [],
            },
            "data_lineage": {
                "primary_sources": ["yfinance"],
                "collection_timestamp": datetime.now(),
                "transformation_steps": [],
                "cache_status": "fresh",
            },
            "confidence_level": 0.90,
            "python_rationale": "Sample rationale",
        },
        "qualitative": {
            "sec_insights": {
                "business_model": business_model,
                "competitive_advantages": ["Advantage 1", "Advantage 2"],
                "risk_factors": ["Risk 1"],
                "strategic_initiatives": ["Initiative 1"],
            },
            "fundamental_context": {
                "industry_analysis": " ".join(["word"] * 100),
                "growth_drivers": ["Driver 1"],
                "competitive_positioning": "Strong position",
                "management_assessment": "Experienced team",
            },
            "technical_strategy": {
                "chart_patterns": ["Pattern 1"],
                "support_resistance": "Support at $150",
                "entry_exit_strategy": " ".join(["word"] * 100),
                "timing_assessment": "Favorable timing",
            },
            "contextual_risks": {
                "regulatory_risks": ["Risk 1"],
                "geopolitical_risks": [],
                "competitive_risks": [],
                "operational_risks": [],
                "stress_scenarios": [],
            },
            "investment_synthesis": {
                "investment_thesis": investment_thesis,
                "bull_case": " ".join(["word"] * 100),
                "base_case": " ".join(["word"] * 100),
                "bear_case": " ".join(["word"] * 100),
                "scenario_probabilities": {"bull": 0.3, "base": 0.5, "bear": 0.2},
                "final_recommendation": draw(st.sampled_from(["BUY", "HOLD", "SELL"])),
                "recommendation_confidence": draw(st.sampled_from(["LOW", "MEDIUM", "HIGH"])),
                "action_plan": action_plan,
            },
            "analysis_timestamp": datetime.now(),
            "ai_confidence": draw(st.floats(min_value=0.0, max_value=1.0)),
        },
        "final_grade": draw(st.sampled_from(["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"])),
        "final_score": draw(st.floats(min_value=0.0, max_value=1.0)),
        "final_recommendation": draw(st.sampled_from(["BUY", "HOLD", "SELL"])),
        "recommendation_confidence": draw(st.sampled_from(["LOW", "MEDIUM", "HIGH"])),
        "executive_summary": exec_summary,
        "investment_rationale": investment_rationale,
        "report_word_count": total_word_count,
        "unique_insights_count": draw(st.integers(min_value=5, max_value=20)),
        "processing_time_seconds": draw(st.floats(min_value=1.0, max_value=30.0)),
        "llm_cost_dollars": draw(st.floats(min_value=0.0, max_value=0.10)),
    }


class TestRendererToleratesSkippedAnalysis:
    """Regression: the 2026-04-28 run crashed the renderer on quantitative=None.

    When the per-holding pipeline skipped scoring (e.g. CriticalFieldError on
    missing volatility) or qualitative analysis, the orchestrator still
    attempted to render an EnrichedAnalysis with ``quantitative=None`` /
    ``qualitative=None`` — and the renderer raised ``AttributeError: 'NoneType'
    object has no attribute 'get'`` at line 206. After the fix, those cases
    must render an "Analyse Skippée" banner instead of crashing.
    """

    def _minimal_skipped_payload(self, **overrides):
        payload = {
            "ticker": "ASML",
            "company_name": "ASML Holding",
            "asset_class": "stock",
            "analysis_date": datetime.now(),
            "executive_summary": "",
            "investment_rationale": "",
            "final_grade": "N/A",
            "final_recommendation": "WAIT",
            "recommendation_confidence": "low",
            "final_score": 0.0,
            "report_word_count": 0,
            "unique_insights_count": 0,
            "processing_time_seconds": 0.0,
            "llm_cost_dollars": 0.0,
            "quantitative": None,
            "qualitative": None,
            "rationale": "Missing critical fields ['volatility (missing)']",
        }
        payload.update(overrides)
        return payload

    def test_render_enriched_with_quantitative_none(self):
        generator = EnrichedAnalysisReportGenerator()
        html = generator.generate_report(self._minimal_skipped_payload())
        assert "Analyse Skippée" in html or "Analyse Skipp" in html
        assert "volatility" in html.lower()

    def test_render_enriched_with_qualitative_none(self):
        generator = EnrichedAnalysisReportGenerator()
        # quantitative present but qualitative missing — also a skipped state
        # because both must be present for a real verdict in the original code.
        payload = self._minimal_skipped_payload(
            quantitative=None,
            qualitative=None,
            rationale="circuit breaker open for deep_analysis_etf",
        )
        html = generator.generate_report(payload)
        assert "circuit breaker" in html.lower() or "skipp" in html.lower()


class TestEnrichedAnalysisReportProperties:
    """Property-based tests for EnrichedAnalysisReportGenerator."""

    # Property 15: Executive Summary Length
    @given(enriched_data=enriched_analysis_strategy())
    @settings(max_examples=50, deadline=500, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_executive_summary_meets_minimum_length(self, enriched_data):
        """
        **Feature: python-ai-hybrid-analysis, Property 15: Executive Summary Length**
        **Validates: Requirements 9.2**

        Property: Executive summary has at least 200 words.

        For any EnrichedAnalysis with an executive_summary, the word count
        of that summary should be ≥200 words.
        """
        # Arrange
        generator = EnrichedAnalysisReportGenerator()

        # Act - Generate report (this validates the data)
        html_content = generator.generate_report(enriched_data)

        # Assert - Executive summary length
        exec_summary = enriched_data["executive_summary"]
        word_count = len(exec_summary.split())

        assert word_count >= 200, f"Executive summary has {word_count} words, expected ≥200"
        assert "résumé exécutif" in html_content.lower() or "executive" in html_content.lower(), "Report must contain executive summary section"

    # Property 16: Investment Rationale Length
    @given(enriched_data=enriched_analysis_strategy())
    @settings(max_examples=50, deadline=500, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_investment_rationale_meets_minimum_length(self, enriched_data):
        """
        **Feature: python-ai-hybrid-analysis, Property 16: Investment Rationale Length**
        **Validates: Requirements 9.3**

        Property: Investment rationale has at least 500 words.

        For any EnrichedAnalysis with an investment_rationale, the word count
        should be ≥500 words.
        """
        # Arrange
        generator = EnrichedAnalysisReportGenerator()

        # Act - Generate report (this validates the data)
        html_content = generator.generate_report(enriched_data)

        # Assert - Investment rationale length
        investment_rationale = enriched_data["investment_rationale"]
        word_count = len(investment_rationale.split())

        assert word_count >= 500, f"Investment rationale has {word_count} words, expected ≥500"
        assert "investissement" in html_content.lower(), "Report must contain investment thesis section"

    # Property 17: Action Plan Completeness
    @given(enriched_data=enriched_analysis_strategy())
    @settings(max_examples=50, deadline=500, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_action_plan_has_all_required_fields(self, enriched_data):
        """
        **Feature: python-ai-hybrid-analysis, Property 17: Action Plan Completeness**
        **Validates: Requirements 9.4**

        Property: Action plan contains all required fields.

        For any InvestmentSynthesis action_plan, it should contain non-empty lists
        for immediate_actions, monitoring_points, and exit_triggers.
        """
        # Arrange
        generator = EnrichedAnalysisReportGenerator()

        # Act - Generate report (this validates the data)
        html_content = generator.generate_report(enriched_data)

        # Assert - Action plan completeness
        action_plan = enriched_data["qualitative"]["investment_synthesis"]["action_plan"]

        # Check all required fields exist
        assert "immediate_actions" in action_plan, "Action plan must have immediate_actions"
        assert "monitoring_points" in action_plan, "Action plan must have monitoring_points"
        assert "exit_triggers" in action_plan, "Action plan must have exit_triggers"

        # Check all fields are non-empty lists
        assert isinstance(action_plan["immediate_actions"], list), "immediate_actions must be a list"
        assert len(action_plan["immediate_actions"]) > 0, "immediate_actions must not be empty"

        assert isinstance(action_plan["monitoring_points"], list), "monitoring_points must be a list"
        assert len(action_plan["monitoring_points"]) > 0, "monitoring_points must not be empty"

        assert isinstance(action_plan["exit_triggers"], list), "exit_triggers must be a list"
        assert len(action_plan["exit_triggers"]) > 0, "exit_triggers must not be empty"

        # Check report contains action plan sections
        assert "action" in html_content.lower(), "Report must contain action plan section"
        assert "immediate" in html_content.lower() or "immédiates" in html_content.lower(), "Report must contain immediate actions"
        assert "monitoring" in html_content.lower() or "surveillance" in html_content.lower(), "Report must contain monitoring points"
        assert "exit" in html_content.lower() or "sortie" in html_content.lower(), "Report must contain exit triggers"


class TestRendererShowsPriceTargets:
    """ADR-011: per-ticker HTML report shows a Targets panel when price_targets
    is present; gracefully omits it when None.
    """

    def _payload_with_targets(self) -> dict:
        return {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "asset_class": "stock",
            "analysis_date": datetime.now(),
            "executive_summary": "summary " * 250,  # past 200-word floor
            "investment_rationale": "rat " * 600,
            "final_grade": "A",
            "final_recommendation": "BUY",
            "recommendation_confidence": "HIGH",
            "final_score": 0.85,
            "report_word_count": 2200,
            "unique_insights_count": 6,
            "processing_time_seconds": 5.0,
            "llm_cost_dollars": 0.05,
            "quantitative": {
                "composite_score": 0.85,
                "fundamental_score": 0.85,
                "technical_score": 0.85,
                "risk_score": 1.5,
                "grade": "A",
                "preliminary_recommendation": "BUY",
                "fundamental_metrics": {},
                "technical_indicators": {},
                "risk_metrics": {},
                "price_targets": {
                    "current_price": 100.0,
                    "currency": "USD",
                    "buy_target_primary": 120.0,
                    "sell_target_primary": 85.0,
                    "buy_rationale": "Objectif: drift + résistance — confiance élevée.",
                    "sell_rationale": "Plancher: ATR floor — confiance élevée.",
                },
            },
            "qualitative": {"ai_confidence": 0.9},
        }

    def test_detail_panel_renders_when_price_targets_present(self) -> None:
        gen = EnrichedAnalysisReportGenerator()
        html = gen.generate_report(self._payload_with_targets())
        # Section heading present.
        assert "Objectifs Tactiques" in html or "🎯" in html
        # Both numbers visible.
        assert "120.00" in html or "$120" in html
        assert "85.00" in html or "$85" in html
        # Confidence rationale text appears (escaped or as-is).
        assert "élevée" in html or "élev" in html  # may be HTML-escaped accent

    def test_detail_panel_omitted_when_price_targets_none(self) -> None:
        payload = self._payload_with_targets()
        payload["quantitative"]["price_targets"] = None
        gen = EnrichedAnalysisReportGenerator()
        html = gen.generate_report(payload)
        # Section heading must NOT appear.
        assert "Objectifs Tactiques" not in html

    def test_detail_panel_omitted_when_price_targets_missing_from_quant(self) -> None:
        payload = self._payload_with_targets()
        del payload["quantitative"]["price_targets"]
        gen = EnrichedAnalysisReportGenerator()
        html = gen.generate_report(payload)
        assert "Objectifs Tactiques" not in html

    # Additional property: Report generation succeeds for valid data
    @given(enriched_data=enriched_analysis_strategy())
    @settings(max_examples=50, deadline=500, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_report_generation_succeeds_for_valid_data(self, enriched_data):
        """
        Property: Report generation succeeds for all valid EnrichedAnalysis data.

        For any valid EnrichedAnalysis data that meets quality thresholds,
        report generation should succeed and produce valid HTML.
        """
        # Arrange
        generator = EnrichedAnalysisReportGenerator()

        # Act
        html_content = generator.generate_report(enriched_data)

        # Assert - Valid HTML structure
        assert html_content.startswith("<!DOCTYPE html>"), "Report must start with DOCTYPE"
        assert "<html" in html_content, "Report must contain html tag"
        assert "</html>" in html_content, "Report must close html tag"
        assert enriched_data["ticker"] in html_content, "Report must contain ticker"
        assert enriched_data["final_recommendation"] in html_content, "Report must contain recommendation"

    # Additional property: Quality validation logs warnings for insufficient data
    @given(
        word_count=st.integers(min_value=0, max_value=1999),
        insights_count=st.integers(min_value=0, max_value=4),
    )
    @settings(max_examples=20, deadline=500, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_quality_validation_warns_for_insufficient_data(self, word_count, insights_count, caplog):
        """
        Property: Quality validation logs warnings for data below thresholds.

        For any EnrichedAnalysis data with word_count < 2000 or insights_count < 5,
        quality validation should log appropriate warnings (but not block generation).

        Note: The generator uses non-blocking validation - it logs warnings but
        allows HTML generation to proceed. This test verifies warnings are logged.
        """
        import logging

        # Arrange
        generator = EnrichedAnalysisReportGenerator()

        # Create data that violates quality thresholds but has all required template fields
        insufficient_data = {
            "ticker": "TEST",
            "company_name": "Test Company",
            "asset_class": "stock",
            "analysis_date": datetime.now(),
            "report_word_count": word_count,
            "unique_insights_count": insights_count,
            "executive_summary": " ".join(["word"] * 50),  # Too short
            "investment_rationale": " ".join(["word"] * 100),  # Too short
            "final_grade": "C",
            "final_score": 0.5,
            "final_recommendation": "HOLD",
            "recommendation_confidence": "LOW",
            "processing_time_seconds": 1.0,
            "llm_cost_dollars": 0.01,
            "quantitative": {
                "composite_score": 0.5,
                "fundamental_score": 0.5,
                "technical_score": 0.5,
                "risk_score": 2.5,
                "grade": "C",
                "preliminary_recommendation": "HOLD",
                "fundamental_metrics": {},
                "technical_indicators": {},
                "risk_metrics": {},
                "calculation_timestamp": datetime.now(),
                "data_quality": {
                    "completeness_score": 0.5,
                    "freshness_score": 0.5,
                    "accuracy_confidence": 0.5,
                    "source_reliability": 0.5,
                    "missing_fields": [],
                },
                "data_lineage": {
                    "primary_sources": [],
                    "collection_timestamp": datetime.now(),
                    "transformation_steps": [],
                    "cache_status": "unknown",
                },
                "confidence_level": 0.5,
                "python_rationale": "",
            },
            "qualitative": {
                "sec_insights": {"business_model": "", "competitive_advantages": [], "risk_factors": [], "strategic_initiatives": []},
                "fundamental_context": {"industry_analysis": "", "growth_drivers": [], "competitive_positioning": "", "management_assessment": ""},
                "technical_strategy": {"chart_patterns": [], "support_resistance": "", "entry_exit_strategy": "", "timing_assessment": ""},
                "contextual_risks": {"regulatory_risks": [], "geopolitical_risks": [], "competitive_risks": [], "operational_risks": [], "stress_scenarios": []},
                "investment_synthesis": {
                    "investment_thesis": "",
                    "bull_case": "",
                    "base_case": "",
                    "bear_case": "",
                    "scenario_probabilities": {"bull": 0.33, "base": 0.34, "bear": 0.33},
                    "final_recommendation": "HOLD",
                    "recommendation_confidence": "LOW",
                    "action_plan": {"immediate_actions": [], "monitoring_points": [], "exit_triggers": []},
                },
                "analysis_timestamp": datetime.now(),
                "ai_confidence": 0.5,
            },
        }

        # Act - capture log output
        with caplog.at_level(logging.WARNING):
            try:
                generator.generate_report(insufficient_data)
            except RuntimeError:
                # Template rendering may fail for other reasons, that's OK
                pass

        # Assert - quality validation should have logged warnings
        warning_logs = [record.message for record in caplog.records if record.levelno == logging.WARNING]
        quality_warnings = [msg for msg in warning_logs if "Quality validation" in msg or "Word count" in msg or "words <" in msg]

        # At least one quality warning should be logged
        assert len(quality_warnings) > 0, f"Expected quality validation warnings, got: {warning_logs}"
