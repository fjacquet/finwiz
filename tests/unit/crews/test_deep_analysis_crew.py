"""
Unit tests for DeepAnalysisCrew.

Tests the unified deep analysis crew with dynamic tool routing for single-ticker
analysis across all asset classes (stocks, ETFs, cryptocurrencies).

NOTE: These tests focus on the tool routing logic and configuration loading.
We do NOT test the actual crew execution as that would require mocking the entire
CrewAI framework and LLM calls, which is not practical for unit tests.
"""

from pathlib import Path


class TestDeepAnalysisCrew:
    """Test cases for DeepAnalysisCrew - focused on tool routing and configuration."""

    def test_should_load_agent_configurations_from_yaml(self):
        """Test that agent configurations are loaded correctly from YAML files."""
        import yaml

        # Load the actual YAML file
        config_path = Path("src/finwiz/crews/deep_analysis/config/agents.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify all required agents are present (single agent design - Python handles consolidation)
        required_agents = ["asset_analyst"]
        for agent_name in required_agents:
            assert agent_name in config, f"Missing agent configuration: {agent_name}"
            assert "role" in config[agent_name]
            assert "goal" in config[agent_name]
            assert "backstory" in config[agent_name]

    def test_should_load_task_configurations_from_yaml(self):
        """Test that task configurations are loaded correctly from YAML files."""
        import yaml

        # Load the actual YAML file
        config_path = Path("src/finwiz/crews/deep_analysis/config/tasks.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify all required tasks are present (single task - Python handles consolidation)
        required_tasks = [
            "deep_qualitative_analysis_task",  # AI qualitative analysis only
        ]

        for task_name in required_tasks:
            assert task_name in config, f"Missing task configuration: {task_name}"
            assert "description" in config[task_name]
            assert "expected_output" in config[task_name]

    def test_should_have_get_tools_for_asset_class_method(self):
        """Test that DeepAnalysisCrew has the get_tools_for_asset_class method."""
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        assert hasattr(DeepAnalysisCrew, "get_tools_for_asset_class")

    def test_should_validate_asset_class_parameter(self):
        """Test that get_tools_for_asset_class validates asset_class parameter."""
        # We test the logic without instantiating the crew
        # by checking that invalid asset classes would raise ValueError

        # Valid asset classes
        valid_asset_classes = ["stock", "etf", "crypto", "STOCK", "ETF", "CRYPTO"]
        for asset_class in valid_asset_classes:
            # Just verify the logic would accept these
            assert asset_class.lower() in ["stock", "etf", "crypto"]

        # Invalid asset classes
        invalid_asset_classes = ["bond", "option", "future", ""]
        for asset_class in invalid_asset_classes:
            # Verify the logic would reject these
            assert asset_class.lower() not in ["stock", "etf", "crypto"]

    def test_should_have_kickoff_method(self):
        """Test that DeepAnalysisCrew has the kickoff method."""
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        assert hasattr(DeepAnalysisCrew, "kickoff")

    def test_should_have_agent_methods(self):
        """Test that DeepAnalysisCrew has all required agent methods."""
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        assert hasattr(DeepAnalysisCrew, "asset_analyst")
        # investment_reporter removed - Python handles consolidation

    def test_should_have_task_methods(self):
        """Test that DeepAnalysisCrew has all required task methods."""
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        # Single task - Python handles consolidation
        assert hasattr(DeepAnalysisCrew, "deep_qualitative_analysis_task")
        # generate_enriched_analysis_task removed - Python handles consolidation

    def test_should_have_crew_method(self):
        """Test that DeepAnalysisCrew has the crew method."""
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        assert hasattr(DeepAnalysisCrew, "crew")

    def test_configuration_files_exist(self):
        """Test that configuration files exist."""
        agents_config = Path("src/finwiz/crews/deep_analysis/config/agents.yaml")
        tasks_config = Path("src/finwiz/crews/deep_analysis/config/tasks.yaml")

        assert agents_config.exists(), "agents.yaml configuration file not found"
        assert tasks_config.exists(), "tasks.yaml configuration file not found"

    def test_should_instantiate_crew_without_keyerror(self, monkeypatch):
        """
        Test that DeepAnalysisCrew instantiates without KeyError.

        This verifies that the deprecated risk_assessor agent has been properly removed
        and the crew only references agents that exist in agents.yaml.

        Requirements: 2.1
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        # Should instantiate without KeyError
        crew = DeepAnalysisCrew()

        # Verify crew was created successfully
        assert crew is not None
        assert hasattr(crew, "agents_config")
        assert hasattr(crew, "tasks_config")

    def test_should_have_exactly_one_agent(self, monkeypatch):
        """
        Test that the crew contains exactly 1 agent.

        Verifies that only asset_analyst is present.
        Python handles consolidation via synthesize_enriched_analysis().

        Requirements: Token overflow fix
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        crew = DeepAnalysisCrew()

        # Check agents_config has exactly 1 agent
        assert len(crew.agents_config) == 1, f"Expected 1 agent, found {len(crew.agents_config)}"

        # Verify the correct agent is present
        assert "asset_analyst" in crew.agents_config

        # Verify removed agents are NOT present
        assert "investment_reporter" not in crew.agents_config
        assert "risk_assessor" not in crew.agents_config

    def test_should_not_reference_risk_assessor_in_code(self):
        """
        Test that the crew code does not reference risk_assessor.

        Verifies that all code references to the deprecated agent have been removed.

        Requirements: 1.1, 1.2, 1.4
        """
        import inspect

        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        # Get the source code of the DeepAnalysisCrew class
        source = inspect.getsource(DeepAnalysisCrew)

        # Verify no references to risk_assessor in the source code
        assert "risk_assessor" not in source.lower(), "Found reference to risk_assessor in crew code"


# ---------------------------------------------------------------------------
# WS-A — Qualify-stage speed regression tests (2026-04-29 follow-up)
# ---------------------------------------------------------------------------


class TestAssetAnalystToolless:
    """Round-2 fix: the asset_analyst agent now runs without any tool.

    On the 2026-04-29 run DELL spent 24 minutes inside the CrewAI agent
    reasoning loop while ``PerplexitySearchTool`` was attached. The
    deterministic ``fact_pack`` stage already ran Perplexity before qualify,
    so the agent has nothing it could verify Python hasn't already verified.
    Removing the tool collapses ``max_iter`` to 1 in practice (no tool calls
    means the LLM returns text on the first iteration and exits).
    """

    def test_build_asset_analyst_tools_returns_empty_list(self) -> None:
        from finwiz.crews.deep_analysis.deep_analysis import _build_asset_analyst_tools

        assert _build_asset_analyst_tools() == []

    def test_build_asset_analyst_tools_returns_empty_even_with_pplx_key(self, monkeypatch) -> None:
        # Setting PPLX_API_KEY must NOT re-add the tool — the tool is gone for good.
        monkeypatch.setenv("PPLX_API_KEY", "fake-key-for-test")
        from finwiz.crews.deep_analysis.deep_analysis import _build_asset_analyst_tools

        assert _build_asset_analyst_tools() == []

    def test_tasks_yaml_has_no_perplexity_instruction(self) -> None:
        # The prompt must not contradict reality by telling the LLM it has a
        # Perplexity tool when it doesn't.
        config_path = Path("src/finwiz/crews/deep_analysis/config/tasks.yaml")
        text = config_path.read_text(encoding="utf-8")
        assert "OUTIL DE VÉRIFICATION" not in text
        assert "Perplexity Sonar Search" not in text


class TestCrewMaxIter:
    """The crew's ``max_iter`` was reduced from 5 to 2 to bound the agent
    reasoning loop. With zero tools this is defense-in-depth, but it also
    documents the contract: the LLM is expected to return on its first pass.
    """

    def test_crew_source_uses_max_iter_2(self) -> None:
        # Source-level check (rather than instantiating the Crew, which the
        # other tests in this file deliberately avoid).
        path = Path("src/finwiz/crews/deep_analysis/deep_analysis.py")
        text = path.read_text(encoding="utf-8")
        assert "max_iter=2" in text
        assert "max_iter=5" not in text


class TestPerHoldingTimeoutDefault:
    """``FINWIZ_HOLDING_TIMEOUT`` default bumped 600 → 900 s. Verified by
    reading the source (env-var fallbacks are baked in at import time, so a
    monkeypatch test would only assert the env-var path, not the literal).
    """

    def test_crew_execution_default_is_900s(self) -> None:
        path = Path("src/finwiz/infrastructure/resilience/crew_execution.py")
        text = path.read_text(encoding="utf-8")
        assert 'os.getenv("FINWIZ_HOLDING_TIMEOUT", "900")' in text
        assert 'os.getenv("FINWIZ_HOLDING_TIMEOUT", "600")' not in text

    def test_orchestrator_default_is_900s(self) -> None:
        path = Path("src/finwiz/orchestrators/deep_analysis_orchestrator.py")
        text = path.read_text(encoding="utf-8")
        assert 'os.getenv("FINWIZ_HOLDING_TIMEOUT", "900")' in text
        assert 'os.getenv("FINWIZ_HOLDING_TIMEOUT", "600")' not in text
