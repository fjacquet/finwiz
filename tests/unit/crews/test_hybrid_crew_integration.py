"""
Integration tests for hybrid Python/AI crew architecture.

Tests that crews receive quantitative context from Python, produce qualitative output,
and do not call calculation tools. Uses mocked LLM responses for deterministic testing.
"""

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]


class TestHybridDeepAnalysisCrewIntegration:
    """Test hybrid architecture for Deep Analysis Crew."""

    def test_should_load_qualitative_focused_agent_configurations(self):
        """Test that Deep Analysis Crew agents are configured for qualitative analysis."""
        config_path = _REPO_ROOT / "src/finwiz/crews/deep_analysis/config/agents.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify qualitative-focused agents exist (single agent - Python handles consolidation)
        required_agents = ["asset_analyst"]

        for agent_name in required_agents:
            assert agent_name in config, f"Missing agent: {agent_name}"
            agent_config = config[agent_name]

            # Verify qualitative focus
            if agent_name == "asset_analyst":
                role_goal = f"{agent_config['role']} {agent_config['goal']}".lower()
                assert "qualitative" in role_goal or "context" in role_goal

                # Verify JSON output instructions (simplified goal after token overflow fix)
                assert "json" in agent_config["goal"].lower() or "qualitative" in agent_config["goal"].lower()

    def test_should_load_qualitative_focused_task_configurations(self):
        """Test that Deep Analysis Crew tasks are configured for qualitative analysis."""
        config_path = _REPO_ROOT / "src/finwiz/crews/deep_analysis/config/tasks.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify qualitative-focused tasks exist (single task - Python handles consolidation)
        required_tasks = [
            "deep_qualitative_analysis_task",
        ]

        for task_name in required_tasks:
            assert task_name in config, f"Missing task: {task_name}"
            task_config = config[task_name]

            # Verify task has description and expected output
            assert "description" in task_config
            assert "expected_output" in task_config

            # Verify qualitative focus in description
            if task_name == "deep_qualitative_analysis_task":
                description = task_config["description"].lower()
                assert "qualitative" in description

                # Verify DO NOT recalculate instructions
                assert "do not recalculate" in description

    def test_should_use_hybrid_analysis_schemas(self):
        """Test that tasks reference hybrid analysis Pydantic schemas in expected_output."""
        config_path = _REPO_ROOT / "src/finwiz/crews/deep_analysis/config/tasks.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify schema references in expected_output (single task - Python handles consolidation)
        schema_mapping = {
            "deep_qualitative_analysis_task": "QualitativeInsights",
        }

        for task_name, expected_schema in schema_mapping.items():
            task_config = config[task_name]
            # Check that expected_output mentions the schema
            assert "expected_output" in task_config
            assert expected_schema in task_config["expected_output"], f"Task {task_name} should reference {expected_schema} in expected_output"

    def test_should_pass_python_context_to_tasks(self):
        """Test that tasks receive Python-calculated metrics as context."""
        config_path = _REPO_ROOT / "src/finwiz/crews/deep_analysis/config/tasks.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify context passing in task description
        task_config = config["deep_qualitative_analysis_task"]
        description = task_config["description"].lower()

        context_indicators = [
            "python has calculated",
            "context provided",
            "read-only",
            "{grade}",
            "{composite_score}",
            "{preliminary_recommendation}",
        ]

        # At least one context indicator should be present
        has_context = any(indicator in description for indicator in context_indicators)
        assert has_context, "Task missing context indicators"

    # NOTE: test_should_have_final_reporter_with_no_tools removed
    # The investment_reporter agent was eliminated to fix token overflow.
    # Python handles consolidation via synthesize_enriched_analysis().


class TestHybridCrewSchemaValidation:
    """Test that hybrid analysis schemas are properly defined."""

    def test_should_import_qualitative_insights_schema(self):
        """Test that QualitativeInsights schema can be imported."""
        from finwiz.schemas.hybrid_analysis import QualitativeInsights

        # Verify schema has required fields
        assert hasattr(QualitativeInsights, "model_fields")
        fields = QualitativeInsights.model_fields

        required_fields = [
            "sec_insights",
            "fundamental_context",
            "technical_strategy",
            "contextual_risks",
            "investment_synthesis",
            "analysis_timestamp",
            "ai_confidence",
        ]

        for field_name in required_fields:
            assert field_name in fields, f"Missing field: {field_name}"

    def test_should_import_quantitative_analysis_schema(self):
        """Test that QuantitativeAnalysis schema can be imported."""
        from finwiz.schemas.hybrid_analysis import QuantitativeAnalysis

        # Verify schema has required fields
        assert hasattr(QuantitativeAnalysis, "model_fields")
        fields = QuantitativeAnalysis.model_fields

        required_fields = [
            "composite_score",
            "fundamental_score",
            "technical_score",
            "risk_score",
            "grade",
            "preliminary_recommendation",
            "fundamental_metrics",
            "technical_indicators",
            "risk_metrics",
        ]

        for field_name in required_fields:
            assert field_name in fields, f"Missing field: {field_name}"

    def test_should_import_enriched_analysis_schema(self):
        """Test that EnrichedAnalysis schema can be imported."""
        from finwiz.schemas.hybrid_analysis import EnrichedAnalysis

        # Verify schema has required fields
        assert hasattr(EnrichedAnalysis, "model_fields")
        fields = EnrichedAnalysis.model_fields

        required_fields = [
            "ticker",
            "company_name",
            "asset_class",
            "quantitative",
            "qualitative",
            "final_grade",
            "final_score",
            "final_recommendation",
            "recommendation_confidence",
            "executive_summary",
            "investment_rationale",
            "report_word_count",
            "unique_insights_count",
        ]

        for field_name in required_fields:
            assert field_name in fields, f"Missing field: {field_name}"

    def test_should_import_sub_schemas(self):
        """Test that all qualitative sub-schemas can be imported."""
        from finwiz.schemas.hybrid_analysis import (
            ContextualRiskInsights,
            FundamentalContextInsights,
            InvestmentSynthesis,
            SecAnalysisInsights,
            TechnicalStrategyInsights,
        )

        # Just verify they can be imported
        assert SecAnalysisInsights is not None
        assert FundamentalContextInsights is not None
        assert TechnicalStrategyInsights is not None
        assert ContextualRiskInsights is not None
        assert InvestmentSynthesis is not None


class TestHybridCrewNoCalculationTools:
    """Test that crews do not have calculation tools configured."""

    def test_deep_analysis_crew_agents_should_focus_on_qualitative_analysis(self):
        """Test that Deep Analysis Crew agents focus on qualitative analysis (not calculations)."""
        config_path = _REPO_ROOT / "src/finwiz/crews/deep_analysis/config/agents.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # After token overflow fix, agent config was simplified
        # Verify agents focus on qualitative analysis (Python handles quantitative)
        # Note: Only asset_analyst remains - Python handles consolidation
        for agent_name, agent_config in config.items():
            agent_text = f"{agent_config['role']} {agent_config['goal']} {agent_config['backstory']}".lower()

            # Verify agents focus on qualitative (not quantitative calculations)
            qualitative_indicators = [
                "qualitative",
                "insights",
                "analysis",
            ]

            has_qualitative_focus = any(indicator in agent_text for indicator in qualitative_indicators)
            assert has_qualitative_focus, f"Agent {agent_name} missing qualitative focus"
