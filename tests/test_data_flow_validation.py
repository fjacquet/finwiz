"""
Integration tests for data flow validation.

Tests ensure end-to-end data flow validation between crews
and that the reporter only consumes upstream context.
"""

from datetime import datetime

import pytest

from finwiz.validation.data_flow_validator import (
    CrewDataContract,
    DataFlowTrace,
    DataFlowValidator,
    DataFlowViolation,
    ReporterContextValidator,
)


class TestCrewDataContract:
    """Test crew data contract model."""

    def test_should_create_contract_with_defaults(self):
        """Test creating a crew contract with default values."""
        # Act
        contract = CrewDataContract(crew_name="test_crew")

        # Assert
        assert contract.crew_name == "test_crew"
        assert contract.required_inputs == set()
        assert contract.provided_outputs == set()
        assert contract.allowed_external_calls is True

    def test_should_create_contract_with_all_fields(self):
        """Test creating a crew contract with all fields."""
        # Act
        contract = CrewDataContract(
            crew_name="report_crew",
            required_inputs={"input1", "input2"},
            provided_outputs={"output1"},
            allowed_external_calls=False,
        )

        # Assert
        assert contract.crew_name == "report_crew"
        assert contract.required_inputs == {"input1", "input2"}
        assert contract.provided_outputs == {"output1"}
        assert contract.allowed_external_calls is False


class TestDataFlowTrace:
    """Test data flow trace model."""

    def test_should_create_trace_with_defaults(self):
        """Test creating a data flow trace with default values."""
        # Act
        trace = DataFlowTrace(crew_name="test_crew")

        # Assert
        assert trace.crew_name == "test_crew"
        assert isinstance(trace.timestamp, datetime)
        assert trace.input_keys == set()
        assert trace.output_keys == set()
        assert trace.external_calls_made == []


class TestDataFlowValidator:
    """Test data flow validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataFlowValidator()

    def test_should_initialize_with_standard_contracts(self):
        """Test validator initialization with standard crew contracts."""
        # Assert
        assert "stock_crew" in self.validator.crew_contracts
        assert "etf_crew" in self.validator.crew_contracts
        assert "crypto_crew" in self.validator.crew_contracts
        assert "report_crew" in self.validator.crew_contracts

        # Check reporter contract specifically
        reporter_contract = self.validator.crew_contracts["report_crew"]
        assert reporter_contract.allowed_external_calls is False

    def test_should_validate_crew_input_successfully(self, mocker):
        """Test successful crew input validation."""
        # Arrange
        input_data = {"ticker": "AAPL", "analysis_type": "comprehensive"}
        mock_logger = mocker.patch("finwiz.validation.data_flow_validator.logger")

        # Act
        self.validator.validate_crew_input("stock_crew", input_data)

        # Assert
        mock_logger.info.assert_called_with("Input validation passed for stock_crew")
        assert len(self.validator.flow_traces) == 1
        assert self.validator.flow_traces[0].crew_name == "stock_crew"
        assert self.validator.flow_traces[0].input_keys == {"ticker", "analysis_type"}

    def test_should_warn_about_missing_required_inputs(self, mocker):
        """Test warning for missing required inputs."""
        # Arrange
        input_data = {"ticker": "AAPL"}  # Missing analysis_type
        mock_logger = mocker.patch("finwiz.validation.data_flow_validator.logger")

        # Act
        self.validator.validate_crew_input("stock_crew", input_data)

        # Assert
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "missing required inputs" in call_args

    def test_should_validate_crew_output_successfully(self):
        """Test successful crew output validation."""
        # Arrange
        # First add an input trace
        self.validator.validate_crew_input("stock_crew", {"ticker": "AAPL"})

        output_data = {"ten_k_insights": [], "stock_analysis": {}, "risk_score_standardized": {}}

        # Act
        self.validator.validate_crew_output("stock_crew", output_data)

        # Assert
        assert len(self.validator.flow_traces) == 1
        trace = self.validator.flow_traces[0]
        assert trace.output_keys == {"ten_k_insights", "stock_analysis", "risk_score_standardized"}

    def test_should_allow_external_calls_for_upstream_crews(self):
        """Test that upstream crews can make external calls."""
        # Arrange
        external_calls = ["yahoo_finance_api", "alpha_vantage_api"]

        # Act & Assert - Should not raise exception
        self.validator.validate_reporter_isolation("stock_crew", external_calls)

    def test_should_prevent_external_calls_for_reporter(self):
        """Test that reporter crew cannot make external calls."""
        # Arrange
        external_calls = ["yahoo_finance_api"]

        # Act & Assert
        with pytest.raises(DataFlowViolation) as exc_info:
            self.validator.validate_reporter_isolation("report_crew", external_calls)

        assert "Made 1 external calls but should make none" in str(exc_info.value)
        assert exc_info.value.crew_name == "report_crew"

    def test_should_validate_end_to_end_flow_successfully(self):
        """Test successful end-to-end flow validation."""
        # Arrange - Simulate complete flow
        # Stock crew execution
        self.validator.validate_crew_input("stock_crew", {"ticker": "AAPL", "analysis_type": "comprehensive"})
        self.validator.validate_crew_output(
            "stock_crew", {"ten_k_insights": [], "risk_score_standardized": {}, "stock_analysis": {}}
        )
        self.validator.validate_reporter_isolation("stock_crew", ["yahoo_finance"])

        # ETF crew execution
        self.validator.validate_crew_input("etf_crew", {"etf_symbol": "SPY", "analysis_type": "comprehensive"})
        self.validator.validate_crew_output("etf_crew", {"etf_factsheet": {}, "etf_analysis": {}})
        self.validator.validate_reporter_isolation("etf_crew", ["yahoo_finance"])

        # Crypto crew execution
        self.validator.validate_crew_input("crypto_crew", {"crypto_symbol": "BTC", "analysis_type": "comprehensive"})
        self.validator.validate_crew_output("crypto_crew", {"market_sentiment": {}, "crypto_thesis": {}, "crypto_analysis": {}})
        self.validator.validate_reporter_isolation("crypto_crew", ["coinmarketcap"])

        # Reporter execution
        reporter_input = {
            "ten_k_insights": [],
            "market_sentiment": {},
            "risk_score_standardized": {},
            "etf_factsheet": {},
            "crypto_thesis": {},
            "stock_analysis": {},
            "etf_analysis": {},
            "crypto_analysis": {},
            "portfolio_allocation": {},
            "risk_assessment": {},
        }
        self.validator.validate_crew_input("report_crew", reporter_input)
        self.validator.validate_crew_output("report_crew", {"final_report": "", "html_output": ""})
        self.validator.validate_reporter_isolation("report_crew", [])  # No external calls

        # Act
        result = self.validator.validate_end_to_end_flow()

        # Assert
        assert result["is_valid"] is True
        assert result["issues"] == []
        assert result["reporter_isolated"] is True
        assert result["flow_traces"] == 4  # 4 crew executions

    def test_should_detect_reporter_external_calls_violation(self):
        """Test detection of reporter making external calls."""
        # Arrange
        self.validator.validate_crew_input("report_crew", {"ten_k_insights": []})

        # Act & Assert - Should raise exception
        with pytest.raises(DataFlowViolation):
            self.validator.validate_reporter_isolation("report_crew", ["yahoo_finance"])

    def test_should_detect_missing_upstream_data(self):
        """Test detection of missing upstream data for reporter."""
        # Arrange - Reporter with incomplete input
        incomplete_input = {"ten_k_insights": []}  # Missing other required keys
        self.validator.validate_crew_input("report_crew", incomplete_input)
        self.validator.validate_reporter_isolation("report_crew", [])

        # Act
        result = self.validator.validate_end_to_end_flow()

        # Assert
        assert result["is_valid"] is False
        assert any("missing upstream data" in issue for issue in result["issues"])

    def test_should_generate_flow_summary(self):
        """Test generation of data flow summary."""
        # Arrange
        self.validator.validate_crew_input("stock_crew", {"ticker": "AAPL"})
        self.validator.validate_crew_output("stock_crew", {"ten_k_insights": []})
        self.validator.validate_reporter_isolation("stock_crew", ["yahoo_finance"])

        # Act
        summary = self.validator.get_flow_summary()

        # Assert
        assert summary["total_traces"] == 1
        assert "stock_crew" in summary["crews_executed"]
        assert summary["crew_details"]["stock_crew"]["executions"] == 1
        assert "ticker" in summary["crew_details"]["stock_crew"]["total_inputs"]
        assert "ten_k_insights" in summary["crew_details"]["stock_crew"]["total_outputs"]
        assert "yahoo_finance" in summary["crew_details"]["stock_crew"]["external_calls"]

    def test_should_handle_unknown_crew(self):
        """Test handling of unknown crew names."""
        # Act & Assert - Should not raise exception
        self.validator.validate_crew_input("unknown_crew", {"data": "value"})
        self.validator.validate_crew_output("unknown_crew", {"result": "value"})
        self.validator.validate_reporter_isolation("unknown_crew", ["api_call"])

    def test_should_clear_traces(self):
        """Test clearing of flow traces."""
        # Arrange
        self.validator.validate_crew_input("stock_crew", {"ticker": "AAPL"})
        assert len(self.validator.flow_traces) == 1

        # Act
        self.validator.clear_traces()

        # Assert
        assert len(self.validator.flow_traces) == 0


class TestReporterContextValidator:
    """Test reporter context validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ReporterContextValidator()

    def test_should_validate_complete_context_successfully(self):
        """Test validation of complete reporter context."""
        # Arrange
        context = {
            "ten_k_insights": [],
            "market_sentiment": {},
            "risk_score_standardized": {},
            "portfolio_allocation": {},
            "etf_factsheet": {},
        }

        # Act
        result = self.validator.validate_reporter_context(context)

        # Assert
        assert result["is_valid"] is True
        assert result["issues"] == []
        assert result["has_required_context"] is True
        assert set(result["context_keys"]) == set(context.keys())

    def test_should_warn_about_missing_required_context(self):
        """Test warning for missing required context keys."""
        # Arrange
        context = {
            "ten_k_insights": [],
            # Missing market_sentiment and risk_score_standardized
        }

        # Act
        result = self.validator.validate_reporter_context(context)

        # Assert
        assert result["is_valid"] is True  # Warnings don't make it invalid
        assert len(result["warnings"]) > 0
        assert result["has_required_context"] is False
        assert any("Missing required context keys" in warning for warning in result["warnings"])

    def test_should_handle_none_values_in_required_context(self):
        """Test handling of None values in required context."""
        # Arrange
        context = {
            "ten_k_insights": None,  # Should trigger warning
            "market_sentiment": {},
            "risk_score_standardized": {},
        }

        # Act
        result = self.validator.validate_reporter_context(context)

        # Assert
        assert result["is_valid"] is True
        assert len(result["warnings"]) > 0
        assert any("is None" in warning for warning in result["warnings"])

    def test_should_handle_additional_context_keys(self):
        """Test handling of additional unexpected context keys."""
        # Arrange
        context = {
            "ten_k_insights": [],
            "market_sentiment": {},
            "risk_score_standardized": {},
            "unexpected_key": "value",
        }

        # Act
        result = self.validator.validate_reporter_context(context)

        # Assert
        assert result["is_valid"] is True
        assert "unexpected_key" in result["context_keys"]

    def test_should_handle_empty_context(self):
        """Test handling of empty context."""
        # Arrange
        context = {}

        # Act
        result = self.validator.validate_reporter_context(context)

        # Assert
        assert result["is_valid"] is True
        assert result["has_required_context"] is False
        assert len(result["warnings"]) > 0


class TestDataFlowViolation:
    """Test the DataFlowViolation exception."""

    def test_should_create_violation_with_crew_and_message(self):
        """Test creating a data flow violation."""
        # Arrange
        crew_name = "report_crew"
        violation = "Made external API calls"

        # Act
        error = DataFlowViolation(crew_name, violation)

        # Assert
        assert error.crew_name == crew_name
        assert error.violation == violation
        assert crew_name in str(error)
        assert violation in str(error)
