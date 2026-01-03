"""Tests for data_flow_validator.py module."""

from datetime import datetime

import pytest

from finwiz.validation.flow import (
    CrewDataContract,
    DataFlowTrace,
    DataFlowValidator,
    DataFlowViolation,
    ReporterContextValidator,
)


class TestDataFlowViolation:
    """Tests for DataFlowViolation exception."""

    def test_should_create_with_crew_name_and_violation(self):
        """Test exception creation with attributes."""
        exc = DataFlowViolation("stock_crew", "Missing required input")
        assert exc.crew_name == "stock_crew"
        assert exc.violation == "Missing required input"
        assert "stock_crew" in str(exc)
        assert "Missing required input" in str(exc)

    def test_should_format_error_message(self):
        """Test formatted error message."""
        exc = DataFlowViolation("report_crew", "External API call detected")
        assert str(exc) == "Data flow violation in report_crew: External API call detected"


class TestCrewDataContract:
    """Tests for CrewDataContract model."""

    def test_should_create_with_required_fields(self):
        """Test creating contract with required fields."""
        contract = CrewDataContract(crew_name="test_crew")
        assert contract.crew_name == "test_crew"
        assert contract.required_inputs == set()
        assert contract.provided_outputs == set()
        assert contract.allowed_external_calls is True

    def test_should_create_with_all_fields(self):
        """Test creating contract with all fields."""
        contract = CrewDataContract(
            crew_name="stock_crew",
            required_inputs={"ticker", "analysis_type"},
            provided_outputs={"stock_analysis", "risk_score"},
            allowed_external_calls=True,
        )
        assert contract.crew_name == "stock_crew"
        assert contract.required_inputs == {"ticker", "analysis_type"}
        assert contract.provided_outputs == {"stock_analysis", "risk_score"}
        assert contract.allowed_external_calls is True

    def test_should_create_reporter_contract_without_external_calls(self):
        """Test reporter contract disallowing external calls."""
        contract = CrewDataContract(
            crew_name="report_crew",
            required_inputs={"upstream_data"},
            provided_outputs={"final_report"},
            allowed_external_calls=False,
        )
        assert contract.allowed_external_calls is False


class TestDataFlowTrace:
    """Tests for DataFlowTrace model."""

    def test_should_create_with_defaults(self):
        """Test creating trace with defaults."""
        trace = DataFlowTrace(crew_name="stock_crew")
        assert trace.crew_name == "stock_crew"
        assert trace.input_keys == set()
        assert trace.output_keys == set()
        assert trace.external_calls_made == []
        assert isinstance(trace.timestamp, datetime)

    def test_should_create_with_all_fields(self):
        """Test creating trace with all fields."""
        trace = DataFlowTrace(
            crew_name="etf_crew",
            input_keys={"etf_symbol", "analysis_type"},
            output_keys={"etf_analysis", "holdings"},
            external_calls_made=["yfinance_api", "sec_api"],
        )
        assert trace.crew_name == "etf_crew"
        assert trace.input_keys == {"etf_symbol", "analysis_type"}
        assert trace.output_keys == {"etf_analysis", "holdings"}
        assert trace.external_calls_made == ["yfinance_api", "sec_api"]


class TestDataFlowValidatorInit:
    """Tests for DataFlowValidator initialization."""

    def test_should_initialize_with_crew_contracts(self):
        """Test validator initializes with crew contracts."""
        validator = DataFlowValidator()
        assert "stock_crew" in validator.crew_contracts
        assert "etf_crew" in validator.crew_contracts
        assert "crypto_crew" in validator.crew_contracts
        assert "report_crew" in validator.crew_contracts

    def test_should_initialize_with_empty_traces(self):
        """Test validator starts with empty traces."""
        validator = DataFlowValidator()
        assert validator.flow_traces == []

    def test_should_have_report_crew_disallowing_external_calls(self):
        """Test report_crew contract disallows external calls."""
        validator = DataFlowValidator()
        report_contract = validator.crew_contracts["report_crew"]
        assert report_contract.allowed_external_calls is False

    def test_should_have_stock_crew_allowing_external_calls(self):
        """Test stock_crew contract allows external calls."""
        validator = DataFlowValidator()
        stock_contract = validator.crew_contracts["stock_crew"]
        assert stock_contract.allowed_external_calls is True


class TestValidateCrewInput:
    """Tests for validate_crew_input method."""

    def test_should_validate_known_crew_input(self):
        """Test validating input for known crew."""
        validator = DataFlowValidator()
        input_data = {"ticker": "AAPL", "analysis_type": "deep"}

        # Should not raise
        validator.validate_crew_input("stock_crew", input_data)

        # Should create trace
        assert len(validator.flow_traces) == 1
        assert validator.flow_traces[0].crew_name == "stock_crew"
        assert validator.flow_traces[0].input_keys == {"ticker", "analysis_type"}

    def test_should_warn_for_unknown_crew(self):
        """Test warning for unknown crew."""
        validator = DataFlowValidator()

        # Should not raise, just warn
        validator.validate_crew_input("unknown_crew", {"data": "value"})

        # Should not create trace for unknown crew
        assert len(validator.flow_traces) == 0

    def test_should_warn_for_missing_required_inputs(self):
        """Test warning for missing required inputs."""
        validator = DataFlowValidator()
        input_data = {"ticker": "AAPL"}  # Missing analysis_type

        # Should not raise (graceful degradation)
        validator.validate_crew_input("stock_crew", input_data)

        # Should still create trace
        assert len(validator.flow_traces) == 1

    def test_should_record_all_input_keys(self):
        """Test recording all input keys."""
        validator = DataFlowValidator()
        input_data = {"ticker": "AAPL", "analysis_type": "quick", "extra_field": "value"}

        validator.validate_crew_input("stock_crew", input_data)

        assert validator.flow_traces[0].input_keys == {"ticker", "analysis_type", "extra_field"}


class TestValidateCrewOutput:
    """Tests for validate_crew_output method."""

    def test_should_validate_known_crew_output(self):
        """Test validating output for known crew."""
        validator = DataFlowValidator()

        # First create input trace
        validator.validate_crew_input("stock_crew", {"ticker": "AAPL"})

        # Then validate output
        output_data = {"stock_analysis": {"score": 0.85}, "risk_score_standardized": 0.3}
        validator.validate_crew_output("stock_crew", output_data)

        # Should update trace with output keys
        assert validator.flow_traces[0].output_keys == {"stock_analysis", "risk_score_standardized"}

    def test_should_warn_for_unknown_crew(self):
        """Test warning for unknown crew."""
        validator = DataFlowValidator()

        # Should not raise
        validator.validate_crew_output("unknown_crew", {"data": "value"})

    def test_should_not_update_trace_if_crew_mismatch(self):
        """Test not updating trace if crew name doesn't match."""
        validator = DataFlowValidator()

        # Create trace for stock_crew
        validator.validate_crew_input("stock_crew", {"ticker": "AAPL"})

        # Try to validate output for different crew
        validator.validate_crew_output("etf_crew", {"etf_analysis": "data"})

        # stock_crew trace should not have etf_crew output
        assert validator.flow_traces[0].output_keys == set()


class TestValidateReporterIsolation:
    """Tests for validate_reporter_isolation method."""

    def test_should_pass_when_no_external_calls(self):
        """Test passing when reporter makes no external calls."""
        validator = DataFlowValidator()

        # Create trace first
        validator.validate_crew_input("report_crew", {"upstream_data": "value"})

        # Should not raise
        validator.validate_reporter_isolation("report_crew", [])

    def test_should_raise_when_reporter_makes_external_calls(self):
        """Test raising when reporter makes external calls."""
        validator = DataFlowValidator()

        with pytest.raises(DataFlowViolation) as exc_info:
            validator.validate_reporter_isolation("report_crew", ["yfinance_api"])

        assert exc_info.value.crew_name == "report_crew"
        assert "external calls" in exc_info.value.violation.lower()

    def test_should_allow_external_calls_for_stock_crew(self):
        """Test allowing external calls for stock crew."""
        validator = DataFlowValidator()

        # Create trace first
        validator.validate_crew_input("stock_crew", {"ticker": "AAPL"})

        # Should not raise for stock_crew
        validator.validate_reporter_isolation("stock_crew", ["yfinance_api", "sec_api"])

        # Should update trace
        assert validator.flow_traces[0].external_calls_made == ["yfinance_api", "sec_api"]

    def test_should_skip_unknown_crew(self):
        """Test skipping unknown crew."""
        validator = DataFlowValidator()

        # Should not raise for unknown crew
        validator.validate_reporter_isolation("unknown_crew", ["some_api"])


class TestValidateEndToEndFlow:
    """Tests for validate_end_to_end_flow method."""

    def test_should_report_no_reporter_execution(self):
        """Test reporting when no reporter execution found."""
        validator = DataFlowValidator()

        # Only add stock_crew trace
        validator.validate_crew_input("stock_crew", {"ticker": "AAPL"})

        result = validator.validate_end_to_end_flow()

        assert result["is_valid"] is False
        assert any("reporter" in issue.lower() for issue in result["issues"])

    def test_should_validate_complete_flow(self):
        """Test validating complete flow with all crews."""
        validator = DataFlowValidator()

        # Simulate full flow
        validator.validate_crew_input("stock_crew", {"ticker": "AAPL", "analysis_type": "deep"})
        validator.validate_crew_output("stock_crew", {"ten_k_insights": {}, "stock_analysis": {}, "risk_score_standardized": 0.3})

        validator.validate_crew_input("etf_crew", {"etf_symbol": "SPY", "analysis_type": "deep"})
        validator.validate_crew_output("etf_crew", {"etf_factsheet": {}, "etf_analysis": {}, "top_holdings": []})

        validator.validate_crew_input("crypto_crew", {"crypto_symbol": "BTC", "analysis_type": "deep"})
        validator.validate_crew_output("crypto_crew", {"crypto_thesis": {}, "crypto_analysis": {}, "market_sentiment": {}})

        # Reporter receives upstream data
        reporter_input = {
            "ten_k_insights": {},
            "market_sentiment": {},
            "risk_score_standardized": 0.3,
            "portfolio_allocation": {},
            "risk_assessment": {},
            "etf_factsheet": {},
            "crypto_thesis": {},
            "stock_analysis": {},
            "etf_analysis": {},
            "crypto_analysis": {},
        }
        validator.validate_crew_input("report_crew", reporter_input)
        validator.validate_crew_output("report_crew", {"final_report": "report", "html_output": "<html>"})

        result = validator.validate_end_to_end_flow()

        assert result["flow_traces"] == 4

    def test_should_detect_missing_upstream_data(self):
        """Test detecting missing upstream data for reporter."""
        validator = DataFlowValidator()

        # Reporter with incomplete input
        validator.validate_crew_input("report_crew", {"ten_k_insights": {}})

        result = validator.validate_end_to_end_flow()

        assert any("missing" in issue.lower() for issue in result["issues"])

    def test_should_detect_reporter_external_calls(self):
        """Test detecting reporter external calls."""
        validator = DataFlowValidator()

        # Reporter with full input but makes external call
        validator.validate_crew_input(
            "report_crew",
            {
                "ten_k_insights": {},
                "market_sentiment": {},
                "risk_score_standardized": 0.3,
            },
        )
        # Manually add external call to trace
        validator.flow_traces[-1].external_calls_made = ["yfinance_api"]

        result = validator.validate_end_to_end_flow()

        assert any("external calls" in issue.lower() for issue in result["issues"])


class TestGetFlowSummary:
    """Tests for get_flow_summary method."""

    def test_should_return_empty_summary_for_no_traces(self):
        """Test empty summary when no traces."""
        validator = DataFlowValidator()

        summary = validator.get_flow_summary()

        assert summary["total_traces"] == 0
        assert summary["crews_executed"] == []
        assert summary["crew_details"] == {}

    def test_should_summarize_single_crew_execution(self):
        """Test summarizing single crew execution."""
        validator = DataFlowValidator()

        validator.validate_crew_input("stock_crew", {"ticker": "AAPL"})
        validator.validate_crew_output("stock_crew", {"stock_analysis": {}})

        summary = validator.get_flow_summary()

        assert summary["total_traces"] == 1
        assert "stock_crew" in summary["crews_executed"]
        assert summary["crew_details"]["stock_crew"]["executions"] == 1

    def test_should_aggregate_multiple_executions(self):
        """Test aggregating multiple executions of same crew."""
        validator = DataFlowValidator()

        # Execute stock_crew twice
        validator.validate_crew_input("stock_crew", {"ticker": "AAPL"})
        validator.validate_crew_input("stock_crew", {"ticker": "MSFT"})

        summary = validator.get_flow_summary()

        assert summary["total_traces"] == 2
        assert summary["crew_details"]["stock_crew"]["executions"] == 2

    def test_should_convert_sets_to_lists(self):
        """Test that sets are converted to lists for JSON serialization."""
        validator = DataFlowValidator()

        validator.validate_crew_input("stock_crew", {"ticker": "AAPL"})
        validator.validate_crew_output("stock_crew", {"stock_analysis": {}})

        summary = validator.get_flow_summary()

        # Should be lists, not sets
        assert isinstance(summary["crew_details"]["stock_crew"]["total_inputs"], list)
        assert isinstance(summary["crew_details"]["stock_crew"]["total_outputs"], list)


class TestClearTraces:
    """Tests for clear_traces method."""

    def test_should_clear_all_traces(self):
        """Test clearing all traces."""
        validator = DataFlowValidator()

        # Add some traces
        validator.validate_crew_input("stock_crew", {"ticker": "AAPL"})
        validator.validate_crew_input("etf_crew", {"etf_symbol": "SPY"})

        assert len(validator.flow_traces) == 2

        validator.clear_traces()

        assert len(validator.flow_traces) == 0


class TestReporterContextValidatorInit:
    """Tests for ReporterContextValidator initialization."""

    def test_should_have_required_context_keys(self):
        """Test having required context keys."""
        validator = ReporterContextValidator()

        assert "ten_k_insights" in validator.required_context_keys
        assert "market_sentiment" in validator.required_context_keys
        assert "risk_score_standardized" in validator.required_context_keys

    def test_should_have_optional_context_keys(self):
        """Test having optional context keys."""
        validator = ReporterContextValidator()

        assert "portfolio_allocation" in validator.optional_context_keys
        assert "etf_factsheet" in validator.optional_context_keys
        assert "crypto_thesis" in validator.optional_context_keys


class TestValidateReporterContext:
    """Tests for validate_reporter_context method."""

    def test_should_validate_complete_context(self):
        """Test validating complete context."""
        validator = ReporterContextValidator()

        context = {
            "ten_k_insights": {"data": "value"},
            "market_sentiment": {"bullish": True},
            "risk_score_standardized": 0.3,
            "portfolio_allocation": {},
            "etf_factsheet": {},
        }

        result = validator.validate_reporter_context(context)

        assert result["is_valid"] is True
        assert result["has_required_context"] is True
        assert len(result["warnings"]) == 0

    def test_should_warn_for_missing_required_keys(self):
        """Test warning for missing required keys."""
        validator = ReporterContextValidator()

        context = {"portfolio_allocation": {}}  # Missing required keys

        result = validator.validate_reporter_context(context)

        assert result["has_required_context"] is False
        assert len(result["warnings"]) > 0
        assert any("missing" in warning.lower() for warning in result["warnings"])

    def test_should_warn_for_none_required_values(self):
        """Test warning for None values in required keys."""
        validator = ReporterContextValidator()

        context = {
            "ten_k_insights": None,  # None value
            "market_sentiment": {},
            "risk_score_standardized": 0.3,
        }

        result = validator.validate_reporter_context(context)

        assert any("None" in warning for warning in result["warnings"])

    def test_should_accept_additional_keys(self):
        """Test accepting additional context keys."""
        validator = ReporterContextValidator()

        context = {
            "ten_k_insights": {},
            "market_sentiment": {},
            "risk_score_standardized": 0.3,
            "custom_data": "extra",  # Additional key
        }

        result = validator.validate_reporter_context(context)

        assert result["is_valid"] is True
        assert "custom_data" in result["context_keys"]

    def test_should_return_context_keys(self):
        """Test returning context keys."""
        validator = ReporterContextValidator()

        context = {"ten_k_insights": {}, "market_sentiment": {}}

        result = validator.validate_reporter_context(context)

        assert "ten_k_insights" in result["context_keys"]
        assert "market_sentiment" in result["context_keys"]


class TestIntegration:
    """Integration tests for data flow validation."""

    def test_should_validate_complete_pipeline(self):
        """Test validating a complete analysis pipeline."""
        validator = DataFlowValidator()

        # Step 1: Stock crew
        validator.validate_crew_input("stock_crew", {"ticker": "AAPL", "analysis_type": "deep"})
        validator.validate_crew_output(
            "stock_crew",
            {
                "ten_k_insights": {"summary": "Strong fundamentals"},
                "stock_analysis": {"score": 0.85},
                "risk_score_standardized": 0.25,
            },
        )
        validator.validate_reporter_isolation("stock_crew", ["yfinance", "sec"])

        # Step 2: Report crew
        reporter_context = {
            "ten_k_insights": {"summary": "Strong fundamentals"},
            "market_sentiment": {"overall": "bullish"},
            "risk_score_standardized": 0.25,
            "stock_analysis": {"score": 0.85},
        }
        validator.validate_crew_input("report_crew", reporter_context)
        validator.validate_reporter_isolation("report_crew", [])  # No external calls
        validator.validate_crew_output("report_crew", {"final_report": "report"})

        # Validate end-to-end
        result = validator.validate_end_to_end_flow()
        summary = validator.get_flow_summary()

        assert result["reporter_isolated"] is True
        assert summary["total_traces"] == 2
        assert "stock_crew" in summary["crews_executed"]
        assert "report_crew" in summary["crews_executed"]

    def test_should_detect_reporter_isolation_violation(self):
        """Test detecting reporter isolation violation in pipeline."""
        validator = DataFlowValidator()

        # Reporter making external call
        validator.validate_crew_input("report_crew", {"upstream_data": "value"})

        with pytest.raises(DataFlowViolation):
            validator.validate_reporter_isolation("report_crew", ["unauthorized_api_call"])
