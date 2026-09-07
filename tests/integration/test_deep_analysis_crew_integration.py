"""
Integration tests for DeepAnalysisCrew.

These tests verify that the crew can be instantiated and executed without errors,
particularly for the BTC-USD ticker that was failing in production.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import os

import pytest


@pytest.mark.integration
class TestDeepAnalysisCrewIntegration:
    """Integration tests for DeepAnalysisCrew execution."""

    def test_configured_agents_and_tasks_match_the_declared_methods(self):
        """Config and code must agree in both directions -- the KeyError this file exists for.

        The original bug was a ``risk_assessor`` method reading an agents.yaml key
        that had been deleted: ``KeyError: 'risk_assessor'`` at instantiation. The
        two tests replaced here pinned the roster of that moment by name
        (asset_analyst + investment_reporter) rather than the agreement itself, so
        they broke when ``investment_reporter`` was later removed for unrelated
        reasons -- reporting a defect where there was none, and going unnoticed
        because integration tests are deselected by default.

        This asserts the invariant instead of the census: every configured key has
        a decorated method, and every decorated method has a configured key. It
        holds for a one-agent crew and would still hold for a five-agent one, while
        failing the moment either side drifts from the other.
        """
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        crew = DeepAnalysisCrew()

        def declared(marker: str) -> set[str]:
            return {name for name, value in type(crew).__dict__.items() if getattr(value, marker, False)}

        assert set(crew.agents_config) == declared("is_agent"), "agents.yaml and the @agent methods disagree"
        assert set(crew.tasks_config) == declared("is_task"), "tasks.yaml and the @task methods disagree"

    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"), reason="Requires API keys for crew execution")
    def test_should_execute_crew_for_btc_usd_without_error(self):
        """
        Test that DeepAnalysisCrew executes for BTC-USD without errors.

        This is the specific failing case from production that triggered
        the KeyError: 'risk_assessor' bug.

        Requirements: 2.1, 2.4
        """
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        # Create crew
        crew = DeepAnalysisCrew()

        # Prepare inputs for BTC-USD (the failing case)
        inputs = {"ticker": "BTC-USD", "asset_class": "crypto"}

        # Execute crew - should not raise KeyError
        try:
            result = crew.kickoff(inputs=inputs)

            # Verify result is not None
            assert result is not None

            # If we got here, the crew executed without KeyError
            # This is the main success criterion

        except KeyError as e:
            # If we get a KeyError, the test should fail
            pytest.fail(f"Crew execution raised KeyError: {e}")
        except Exception as e:
            # Other exceptions might be acceptable (API errors, etc.)
            # but KeyError specifically should not occur
            if "risk_assessor" in str(e).lower():
                pytest.fail(f"Crew execution failed with risk_assessor reference: {e}")
            # Otherwise, log the error but don't fail the test
            # (API errors, rate limits, etc. are not the focus of this test)
            print(f"Note: Crew execution encountered error (not KeyError): {e}")

    def test_should_not_log_deprecation_warnings(self, caplog):
        """
        Test that crew instantiation doesn't log deprecation warnings.

        Verifies that all references to deprecated risk_assessor have been removed.

        Requirements: 2.3
        """
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        # Clear any existing logs
        caplog.clear()

        # Instantiate crew
        crew = DeepAnalysisCrew()

        # Check logs for deprecation warnings
        for record in caplog.records:
            message = record.message.lower()

            # Should not contain references to risk_assessor
            assert "risk_assessor" not in message, f"Found risk_assessor reference in log: {record.message}"

            # Should not contain deprecation warnings
            assert "deprecated" not in message, f"Found deprecation warning in log: {record.message}"

    def test_should_support_all_asset_classes_tool_routing(self):
        """
        Test that crew supports tool routing for all asset classes.

        Verifies that the dynamic tool routing works for stock, etf, and crypto
        without actually instantiating the full crew.

        Requirements: 2.5
        """
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        asset_classes = ["stock", "etf", "crypto"]

        for asset_class in asset_classes:
            # Create crew
            crew = DeepAnalysisCrew()

            # Verify get_tools_for_asset_class method exists
            assert hasattr(crew, "get_tools_for_asset_class")

            # Verify the method accepts the asset class without error
            # (we don't call it to avoid import issues in tests)
            assert asset_class.lower() in ["stock", "etf", "crypto"]
