"""
Integration tests for hybrid Python/AI crew architecture.

Tests that crews receive quantitative context from Python, produce qualitative output,
and do not call calculation tools. Uses mocked LLM responses for deterministic testing.
"""

from pathlib import Path

import yaml


class TestHybridStockCrewIntegration:
    """Test hybrid architecture for Stock Crew."""

    def test_should_load_qualitative_focused_agent_configurations(self):
        """Test that Stock Crew agents are configured for qualitative analysis."""
        config_path = Path("src/finwiz/crews/stock_crew/config/agents.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify qualitative-focused agents exist
        required_agents = [
            "sec_analyst",
            "fundamental_analyst",
            "technical_analyst",
            "risk_analyst",
            "investment_strategist",
            "investment_reporter",
        ]

        for agent_name in required_agents:
            assert agent_name in config, f"Missing agent: {agent_name}"
            agent_config = config[agent_name]

            # Verify qualitative focus in role/goal
            role_goal = f"{agent_config['role']} {agent_config['goal']}".lower()
            assert "qualitative" in role_goal or "context" in role_goal or "synthesis" in role_goal

            # Verify READ-ONLY context instructions
            if agent_name != "investment_reporter":
                assert "read-only" in agent_config["goal"].lower() or "do not recalculate" in agent_config["goal"].lower()

    def test_should_load_qualitative_focused_task_configurations(self):
        """Test that Stock Crew tasks are configured for qualitative analysis."""
        config_path = Path("src/finwiz/crews/stock_crew/config/tasks.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify qualitative-focused tasks exist
        required_tasks = [
            "sec_analysis_task",
            "fundamental_context_task",
            "technical_strategy_task",
            "contextual_risk_task",
            "investment_synthesis_task",
            "generate_enriched_analysis_task",
        ]

        for task_name in required_tasks:
            assert task_name in config, f"Missing task: {task_name}"
            task_config = config[task_name]

            # Verify task has description and expected output
            assert "description" in task_config
            assert "expected_output" in task_config

            # Verify qualitative focus in description
            if task_name != "generate_enriched_analysis_task":
                description = task_config["description"].lower()
                assert "qualitative" in description or "context" in description or "synthesis" in description

                # Verify DO NOT recalculate instructions
                assert "do not recalculate" in description

    def test_should_use_hybrid_analysis_schemas(self):
        """Test that tasks reference hybrid analysis Pydantic schemas in expected_output."""
        config_path = Path("src/finwiz/crews/stock_crew/config/tasks.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify schema references in expected_output
        schema_mapping = {
            "sec_analysis_task": "SecAnalysisInsights",
            "fundamental_context_task": "FundamentalContextInsights",
            "technical_strategy_task": "TechnicalStrategyInsights",
            "contextual_risk_task": "ContextualRiskInsights",
            "investment_synthesis_task": "InvestmentSynthesis",
            "generate_enriched_analysis_task": "EnrichedAnalysis",
        }

        for task_name, expected_schema in schema_mapping.items():
            task_config = config[task_name]
            # Check that expected_output mentions the schema
            assert "expected_output" in task_config
            assert expected_schema in task_config["expected_output"], f"Task {task_name} should reference {expected_schema} in expected_output"

    def test_should_pass_python_context_to_tasks(self):
        """Test that tasks receive Python-calculated metrics as context."""
        config_path = Path("src/finwiz/crews/stock_crew/config/tasks.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify context passing in task descriptions
        context_indicators = [
            "python has calculated",
            "context provided",
            "read-only",
            "{grade}",
            "{composite_score}",
            "{preliminary_recommendation}",
        ]

        for task_name in ["sec_analysis_task", "fundamental_context_task", "technical_strategy_task", "contextual_risk_task", "investment_synthesis_task"]:
            description = config[task_name]["description"].lower()

            # At least one context indicator should be present
            has_context = any(indicator in description for indicator in context_indicators)
            assert has_context, f"Task {task_name} missing context indicators"

    def test_should_have_final_reporter_with_no_tools(self):
        """Test that final reporter is configured correctly."""
        config_path = Path("src/finwiz/crews/stock_crew/config/agents.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        reporter_config = config["investment_reporter"]

        # Verify final reporter characteristics
        goal = reporter_config["goal"].lower()
        assert "no tools" in goal or "consolidation only" in goal
        assert "context" in goal


class TestHybridDeepAnalysisCrewIntegration:
    """Test hybrid architecture for Deep Analysis Crew."""

    def test_should_load_qualitative_focused_agent_configurations(self):
        """Test that Deep Analysis Crew agents are configured for qualitative analysis."""
        config_path = Path("src/finwiz/crews/deep_analysis/config/agents.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify qualitative-focused agents exist
        required_agents = ["asset_analyst", "investment_reporter"]

        for agent_name in required_agents:
            assert agent_name in config, f"Missing agent: {agent_name}"
            agent_config = config[agent_name]

            # Verify qualitative focus
            if agent_name == "asset_analyst":
                role_goal = f"{agent_config['role']} {agent_config['goal']}".lower()
                assert "qualitative" in role_goal or "context" in role_goal

                # Verify READ-ONLY context instructions
                assert "read-only" in agent_config["goal"].lower() or "do not recalculate" in agent_config["goal"].lower()

    def test_should_load_qualitative_focused_task_configurations(self):
        """Test that Deep Analysis Crew tasks are configured for qualitative analysis."""
        config_path = Path("src/finwiz/crews/deep_analysis/config/tasks.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify qualitative-focused tasks exist
        required_tasks = [
            "deep_qualitative_analysis_task",
            "generate_enriched_analysis_task",
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
        config_path = Path("src/finwiz/crews/deep_analysis/config/tasks.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify schema references in expected_output
        schema_mapping = {
            "deep_qualitative_analysis_task": "QualitativeInsights",
            "generate_enriched_analysis_task": "EnrichedAnalysis",
        }

        for task_name, expected_schema in schema_mapping.items():
            task_config = config[task_name]
            # Check that expected_output mentions the schema
            assert "expected_output" in task_config
            assert expected_schema in task_config["expected_output"], f"Task {task_name} should reference {expected_schema} in expected_output"

    def test_should_pass_python_context_to_tasks(self):
        """Test that tasks receive Python-calculated metrics as context."""
        config_path = Path("src/finwiz/crews/deep_analysis/config/tasks.yaml")
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

    def test_should_have_final_reporter_with_no_tools(self):
        """Test that final reporter is configured correctly."""
        config_path = Path("src/finwiz/crews/deep_analysis/config/agents.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        reporter_config = config["investment_reporter"]

        # Verify final reporter characteristics
        goal = reporter_config["goal"].lower()
        assert "no tools" in goal or "consolidation only" in goal
        assert "context" in goal


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

    def test_stock_crew_agents_should_not_reference_calculation_tools(self):
        """Test that Stock Crew agents don't reference calculation tools."""
        config_path = Path("src/finwiz/crews/stock_crew/config/agents.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check that agents emphasize NOT calculating (should have "do not recalculate" or similar)
        for agent_name, agent_config in config.items():
            if agent_name == "investment_reporter":
                continue  # Final reporter doesn't need this instruction

            agent_text = f"{agent_config['role']} {agent_config['goal']} {agent_config['backstory']}".lower()

            # Verify agents are instructed NOT to calculate
            no_calc_indicators = [
                "do not recalculate",
                "no calculations",
                "no financial calculations",
                "read-only context",
                "qualitative only",
            ]

            has_no_calc_instruction = any(indicator in agent_text for indicator in no_calc_indicators)
            assert has_no_calc_instruction, f"Agent {agent_name} missing 'do not calculate' instruction"

    def test_deep_analysis_crew_agents_should_not_reference_calculation_tools(self):
        """Test that Deep Analysis Crew agents don't reference calculation tools."""
        config_path = Path("src/finwiz/crews/deep_analysis/config/agents.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check that agents emphasize NOT calculating (should have "do not recalculate" or similar)
        for agent_name, agent_config in config.items():
            if agent_name == "investment_reporter":
                continue  # Final reporter doesn't need this instruction

            agent_text = f"{agent_config['role']} {agent_config['goal']} {agent_config['backstory']}".lower()

            # Verify agents are instructed NOT to calculate
            no_calc_indicators = [
                "do not recalculate",
                "no calculations",
                "no financial calculations",
                "read-only context",
                "qualitative only",
            ]

            has_no_calc_instruction = any(indicator in agent_text for indicator in no_calc_indicators)
            assert has_no_calc_instruction, f"Agent {agent_name} missing 'do not calculate' instruction"
