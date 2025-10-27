"""
Unit tests for template schema compatibility.

Tests that Jinja2 templates handle both old CrewAI schemas and new Python schemas.
"""

import pytest
from jinja2 import Environment, Template

from finwiz.schemas.python_analysis import PythonDeepAnalysisResult


class TestTemplateSchemaCompatibility:
    """Test template rendering with different schema types."""

    @pytest.fixture
    def risk_display_template(self) -> Template:
        """Create template for risk display section."""
        template_str = """
        <div class="metric-card">
            <h4>Risque</h4>
            {% if analysis.risk_assessment is defined and analysis.risk_assessment %}
            <div class="metric-value risk-{{ 'low' if analysis.risk_assessment.risk_score <= 3 else ('medium' if analysis.risk_assessment.risk_score <= 6 else 'high') }}">
                {{ analysis.risk_assessment.risk_score }}/10
            </div>
            {% elif analysis.risk_score is defined and analysis.risk_score is not none %}
            <div class="metric-value risk-{{ 'low' if analysis.risk_score <= 0.3 else ('medium' if analysis.risk_score <= 0.6 else 'high') }}">
                {{ "%.1f"|format(analysis.risk_score * 10) }}/10
            </div>
            {% else %}
            <div class="metric-value">N/A</div>
            {% endif %}
        </div>
        """
        env = Environment()
        return env.from_string(template_str)

    def test_should_render_python_analysis_result_with_direct_risk_score(self, risk_display_template: Template) -> None:
        """Test rendering PythonDeepAnalysisResult with direct risk_score field."""
        # Arrange
        analysis = PythonDeepAnalysisResult(
            crew_name="PythonDeepAnalyzer",
            execution_id="test-123",
            ticker="AAPL",
            asset_class="stock",
            analysis_timestamp="2025-10-27T12:00:00",
            composite_score=0.85,
            grade="A",
            fundamental_score=0.90,
            technical_score=0.80,
            risk_score=0.25,  # 0-1 scale (low risk)
            recommendation="BUY",
            confidence=0.85,
            rationale="Strong fundamentals and technical indicators",
        )

        # Act
        rendered = risk_display_template.render(analysis=analysis)

        # Assert
        assert "2.5/10" in rendered  # 0.25 * 10 = 2.5
        assert "risk-low" in rendered  # 0.25 <= 0.3 = low risk

    def test_should_render_python_analysis_result_with_medium_risk(self, risk_display_template: Template) -> None:
        """Test rendering with medium risk score."""
        # Arrange
        analysis = PythonDeepAnalysisResult(
            crew_name="PythonDeepAnalyzer",
            execution_id="test-456",
            ticker="TSLA",
            asset_class="stock",
            analysis_timestamp="2025-10-27T12:00:00",
            composite_score=0.70,
            grade="B",
            fundamental_score=0.75,
            technical_score=0.65,
            risk_score=0.50,  # 0-1 scale (medium risk)
            recommendation="HOLD",
            confidence=0.70,
            rationale="Moderate fundamentals with some concerns",
        )

        # Act
        rendered = risk_display_template.render(analysis=analysis)

        # Assert
        assert "5.0/10" in rendered  # 0.50 * 10 = 5.0
        assert "risk-medium" in rendered  # 0.3 < 0.50 <= 0.6 = medium risk

    def test_should_render_python_analysis_result_with_high_risk(self, risk_display_template: Template) -> None:
        """Test rendering with high risk score."""
        # Arrange
        analysis = PythonDeepAnalysisResult(
            crew_name="PythonDeepAnalyzer",
            execution_id="test-789",
            ticker="GME",
            asset_class="stock",
            analysis_timestamp="2025-10-27T12:00:00",
            composite_score=0.45,
            grade="C",
            fundamental_score=0.50,
            technical_score=0.40,
            risk_score=0.85,  # 0-1 scale (high risk)
            recommendation="SELL",
            confidence=0.75,
            rationale="High volatility and weak fundamentals",
        )

        # Act
        rendered = risk_display_template.render(analysis=analysis)

        # Assert
        assert "8.5/10" in rendered  # 0.85 * 10 = 8.5
        assert "risk-high" in rendered  # 0.85 > 0.6 = high risk

    def test_should_render_na_when_risk_score_is_none(self, risk_display_template: Template) -> None:
        """Test rendering when risk_score is None."""
        # Arrange - Create mock object without risk_score
        class MockAnalysisWithoutRisk:
            ticker = "UNKNOWN"
            asset_class = "stock"
            composite_score = 0.60
            grade = "C+"
            recommendation = "HOLD"
            confidence = 0.50
            rationale = "Insufficient data for complete analysis"
            # No risk_score or risk_assessment attributes

        analysis = MockAnalysisWithoutRisk()

        # Act
        rendered = risk_display_template.render(analysis=analysis)

        # Assert
        assert "N/A" in rendered
        assert "/10" not in rendered  # No numeric score displayed

    def test_should_render_crewai_schema_with_nested_risk_assessment(self, risk_display_template: Template) -> None:
        """Test rendering with old CrewAI schema (nested risk_assessment)."""
        # Arrange - Mock object with nested risk_assessment
        class MockRiskAssessment:
            risk_score = 7  # 0-10 scale

        class MockCrewAIAnalysis:
            risk_assessment = MockRiskAssessment()
            risk_score = None  # Not used in CrewAI schema

        analysis = MockCrewAIAnalysis()

        # Act
        rendered = risk_display_template.render(analysis=analysis)

        # Assert
        assert "7/10" in rendered
        assert "risk-high" in rendered  # 7 > 6 = high risk


class TestFlowStateErrorsField:
    """Test that FinwizState has errors field."""

    def test_should_have_errors_field_in_finwiz_state(self) -> None:
        """Test that FinwizState model has errors field."""
        from finwiz.flow_state import FinwizState

        # Arrange & Act
        state = FinwizState()

        # Assert
        assert hasattr(state, "errors")
        assert isinstance(state.errors, list)
        assert len(state.errors) == 0

    def test_should_allow_appending_to_errors_field(self) -> None:
        """Test that errors field can be appended to."""
        from finwiz.flow_state import FinwizState

        # Arrange
        state = FinwizState()

        # Act
        state.errors.append("Test error message")
        state.errors.append("Another error")

        # Assert
        assert len(state.errors) == 2
        assert "Test error message" in state.errors
        assert "Another error" in state.errors
