"""
Property-based tests for ValidationOrchestrator.

Tests verify universal properties using Hypothesis with minimum 100 iterations.
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.validation_orchestrator import ValidationOrchestrator


class TestValidationOrchestratorProperties:
    """Property-based tests for ValidationOrchestrator."""

    @given(
        required_fields=st.lists(
            st.sampled_from(["portfolio_review", "deep_analysis_results", "aplus_opportunities"]),
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_validation_data_availability_check(self, required_fields, mocker):
        """
        Property 18: Validation Data Availability Check.

        For any reporter input validation, the ValidationOrchestrator should verify
        presence of required data fields.
        """
        # Arrange
        state = FinwizState()
        mock_integration_manager = mocker.Mock()
        mock_data_accessor = mocker.Mock()

        orchestrator = ValidationOrchestrator(
            state,
            integration_manager=mock_integration_manager,
            data_accessor=mock_data_accessor,
        )

        # Create consolidated data with the required fields
        consolidated_data = {field: {"data": "test"} for field in required_fields}
        consolidated_data["consolidated_crew_data"] = {}

        mock_data_accessor.get_consolidated_reporter_input.return_value = consolidated_data
        mock_integration_manager.get_crew_data_with_freshness_check.return_value = None

        # Act
        result = orchestrator.pre_validate_reporter_input()

        # Assert - Should verify presence of data fields
        assert result["success"] is True
        assert "consolidated_data" in result
        for field in required_fields:
            assert field in result["consolidated_data"]

    @given(
        stock_available=st.booleans(),
        etf_available=st.booleans(),
        crypto_available=st.booleans(),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_core_analysis_verification(self, stock_available, etf_available, crypto_available, mocker):
        """
        Property 19: Core Analysis Verification.

        For any core analysis availability check, the ValidationOrchestrator should
        verify all required analyses exist.
        """
        # Arrange
        state = FinwizState()
        mock_integration_manager = mocker.Mock()

        orchestrator = ValidationOrchestrator(
            state,
            integration_manager=mock_integration_manager,
        )

        # Mock integration manager responses
        def mock_get_crew_data(crew_type, **kwargs):
            availability_map = {
                "stock": stock_available,
                "etf": etf_available,
                "crypto": crypto_available,
            }
            return {"data": "test"} if availability_map.get(crew_type) else None

        mock_integration_manager.get_crew_data_with_freshness_check.side_effect = mock_get_crew_data

        # Act
        result = orchestrator.check_core_analysis_availability()

        # Assert - Should correctly identify available analyses
        assert result["stock_available"] == stock_available
        assert result["etf_available"] == etf_available
        assert result["crypto_available"] == crypto_available

        expected_available = sum([stock_available, etf_available, crypto_available])
        assert result["total_available"] == expected_available
        assert result["any_available"] == (expected_available > 0)

    @given(
        has_stock=st.booleans(),
        has_etf=st.booleans(),
        has_crypto=st.booleans(),
    )
    @settings(max_examples=100)
    def test_property_market_context_structure(self, has_stock, has_etf, has_crypto):
        """
        Property 20: Market Context Structure.

        For any extracted market context, it should contain overall_sentiment,
        market_trends, and risk_factors fields.
        """
        # Arrange
        state = FinwizState()
        orchestrator = ValidationOrchestrator(state)

        # Build core analysis data based on flags
        core_analysis_data = {}
        if has_stock:
            core_analysis_data["stock_analysis"] = {
                "market_sentiments": [{"sentiment": "positive"}],
                "risk_factors": ["stock risk"],
            }
        if has_etf:
            core_analysis_data["etf_analysis"] = {
                "sector_trends": ["tech growth"],
                "risk_factors": ["etf risk"],
            }
        if has_crypto:
            core_analysis_data["crypto_analysis"] = {
                "market_dynamics": "bullish",
                "risk_factors": ["crypto risk"],
            }

        # Act
        result = orchestrator.extract_market_context_from_core_analysis(core_analysis_data)

        # Assert - Required fields must always be present
        assert "overall_sentiment" in result
        assert "market_trends" in result
        assert "risk_factors" in result
        assert isinstance(result["overall_sentiment"], str)
        assert isinstance(result["market_trends"], list)
        assert isinstance(result["risk_factors"], list)
