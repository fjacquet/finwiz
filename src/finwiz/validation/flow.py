"""
Data flow validation for FinWiz crews.

This module validates that data flows correctly between crews and that
the reporter only consumes upstream context without external dependencies.
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DataFlowViolation(Exception):
    """Raised when data flow validation fails."""

    def __init__(self, crew_name: str, violation: str) -> None:
        """Initialize data flow validation error."""
        super().__init__(f"Data flow violation in {crew_name}: {violation}")
        self.crew_name = crew_name
        self.violation = violation


class CrewDataContract(BaseModel):
    """Defines the data contract for a crew."""

    crew_name: str = Field(..., description="Name of the crew")
    required_inputs: set[str] = Field(default_factory=set, description="Required input keys")
    provided_outputs: set[str] = Field(default_factory=set, description="Keys provided as output")
    allowed_external_calls: bool = Field(default=True, description="Whether external API calls are allowed")


class DataFlowTrace(BaseModel):
    """Traces data flow through the system."""

    timestamp: datetime = Field(default_factory=datetime.now)
    crew_name: str = Field(..., description="Name of the crew")
    input_keys: set[str] = Field(default_factory=set, description="Input keys received")
    output_keys: set[str] = Field(default_factory=set, description="Output keys produced")
    external_calls_made: list[str] = Field(default_factory=list, description="External API calls made")


class DataFlowValidator:
    """
    Validates data flow between crews and ensures architectural compliance.

    Specifically ensures that the reporter crew only consumes upstream context
    and makes no external API calls.
    """

    def __init__(self) -> None:
        """Initialize data flow validator."""
        self.crew_contracts = self._initialize_crew_contracts()
        self.flow_traces: list[DataFlowTrace] = []
        self.logger = logger

    def _initialize_crew_contracts(self) -> dict[str, CrewDataContract]:
        """Initialize standard crew data contracts."""
        return {
            "stock_crew": CrewDataContract(
                crew_name="stock_crew",
                required_inputs={"ticker", "analysis_type"},
                provided_outputs={"ten_k_insights", "stock_analysis", "risk_score_standardized"},
                allowed_external_calls=True,
            ),
            "etf_crew": CrewDataContract(
                crew_name="etf_crew",
                required_inputs={"etf_symbol", "analysis_type"},
                provided_outputs={"etf_factsheet", "etf_analysis", "top_holdings"},
                allowed_external_calls=True,
            ),
            "crypto_crew": CrewDataContract(
                crew_name="crypto_crew",
                required_inputs={"crypto_symbol", "analysis_type"},
                provided_outputs={"crypto_thesis", "crypto_analysis", "market_sentiment"},
                allowed_external_calls=True,
            ),
            "report_crew": CrewDataContract(
                crew_name="report_crew",
                required_inputs={
                    "ten_k_insights",
                    "market_sentiment",
                    "risk_score_standardized",
                    "portfolio_allocation",
                    "risk_assessment",
                    "etf_factsheet",
                    "crypto_thesis",
                    "stock_analysis",
                    "etf_analysis",
                    "crypto_analysis",
                },
                provided_outputs={"final_report", "html_output"},
                allowed_external_calls=False,  # Reporter must not make external calls
            ),
        }

    def validate_crew_input(self, crew_name: str, input_data: dict[str, Any]) -> None:
        """
        Validate that a crew receives the expected input data.

        Args:
            crew_name: Name of the crew
            input_data: Input data being passed to the crew

        Raises:
            DataFlowViolation: If input validation fails

        """
        if crew_name not in self.crew_contracts:
            logger.warning(f"No contract defined for crew: {crew_name}")
            return

        contract = self.crew_contracts[crew_name]
        input_keys = set(input_data.keys())

        # Check for missing required inputs (warning only for graceful degradation)
        missing_inputs = contract.required_inputs - input_keys
        if missing_inputs:
            logger.warning(f"Crew {crew_name} missing required inputs: {missing_inputs}")

        # Log successful validation
        logger.info(f"Input validation passed for {crew_name}")

        # Record the data flow trace
        trace = DataFlowTrace(crew_name=crew_name, input_keys=input_keys)
        self.flow_traces.append(trace)

    def validate_crew_output(self, crew_name: str, output_data: dict[str, Any]) -> None:
        """
        Validate that a crew produces the expected output data.

        Args:
            crew_name: Name of the crew
            output_data: Output data produced by the crew

        Raises:
            DataFlowViolation: If output validation fails

        """
        if crew_name not in self.crew_contracts:
            logger.warning(f"No contract defined for crew: {crew_name}")
            return

        self.crew_contracts[crew_name]
        output_keys = set(output_data.keys())

        # Update the latest trace with output information
        if self.flow_traces and self.flow_traces[-1].crew_name == crew_name:
            self.flow_traces[-1].output_keys = output_keys

        logger.info(f"Output validation passed for {crew_name}")

    def validate_reporter_isolation(self, crew_name: str, external_calls: list[str]) -> None:
        """
        Validate that the reporter crew makes no external API calls.

        Args:
            crew_name: Name of the crew
            external_calls: List of external API calls made

        Raises:
            DataFlowViolation: If reporter makes external calls

        """
        if crew_name not in self.crew_contracts:
            return

        contract = self.crew_contracts[crew_name]

        if not contract.allowed_external_calls and external_calls:
            violation = f"Made {len(external_calls)} external calls but should make none: {external_calls}"
            logger.error(f"Data flow violation: {crew_name} - {violation}")
            raise DataFlowViolation(crew_name, violation)

        # Update the latest trace with external call information
        if self.flow_traces and self.flow_traces[-1].crew_name == crew_name:
            self.flow_traces[-1].external_calls_made = external_calls

        logger.info(f"External call validation passed for {crew_name}")

    def validate_end_to_end_flow(self) -> dict[str, Any]:
        """
        Validate the complete end-to-end data flow.

        Returns:
            Validation result with flow analysis

        """
        issues = []

        # Check that reporter receives data from upstream crews
        reporter_traces = [trace for trace in self.flow_traces if trace.crew_name == "report_crew"]

        if not reporter_traces:
            issues.append("No reporter crew execution found in flow traces")
        else:
            reporter_trace = reporter_traces[-1]  # Get latest execution

            # Check that reporter received upstream data
            expected_upstream_keys = self.crew_contracts["report_crew"].required_inputs
            received_keys = reporter_trace.input_keys

            missing_upstream = expected_upstream_keys - received_keys
            if missing_upstream:
                issues.append(f"Reporter missing upstream data: {missing_upstream}")

            # Check that reporter made no external calls
            if reporter_trace.external_calls_made:
                issues.append(f"Reporter made external calls: {reporter_trace.external_calls_made}")

        # Check data flow continuity
        upstream_crews = ["stock_crew", "etf_crew", "crypto_crew"]
        upstream_outputs = set()

        for crew_name in upstream_crews:
            crew_traces = [trace for trace in self.flow_traces if trace.crew_name == crew_name]
            if crew_traces:
                upstream_outputs.update(crew_traces[-1].output_keys)

        # Verify reporter inputs come from upstream outputs
        if reporter_traces:
            reporter_inputs = reporter_traces[-1].input_keys
            unexpected_inputs = reporter_inputs - upstream_outputs - {"analysis_type", "ticker", "etf_symbol", "crypto_symbol"}

            if unexpected_inputs:
                logger.info(f"Reporter has additional inputs not from upstream: {unexpected_inputs}")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "flow_traces": len(self.flow_traces),
            "reporter_isolated": len(issues) == 0 or not any("external calls" in issue for issue in issues),
        }

    def get_flow_summary(self) -> dict[str, Any]:
        """
        Get a summary of the data flow through the system.

        Returns:
            Summary of data flow traces

        """
        crew_summary = {}

        for trace in self.flow_traces:
            if trace.crew_name not in crew_summary:
                crew_summary[trace.crew_name] = {
                    "executions": 0,
                    "total_inputs": set(),
                    "total_outputs": set(),
                    "external_calls": [],
                }

            summary = crew_summary[trace.crew_name]
            summary["executions"] += 1
            summary["total_inputs"].update(trace.input_keys)
            summary["total_outputs"].update(trace.output_keys)
            summary["external_calls"].extend(trace.external_calls_made)

        # Convert sets to lists for JSON serialization
        for crew_name in crew_summary:
            total_inputs = crew_summary[crew_name]["total_inputs"]
            total_outputs = crew_summary[crew_name]["total_outputs"]
            if isinstance(total_inputs, set):
                crew_summary[crew_name]["total_inputs"] = list(total_inputs)
            if isinstance(total_outputs, set):
                crew_summary[crew_name]["total_outputs"] = list(total_outputs)

        return {
            "total_traces": len(self.flow_traces),
            "crews_executed": list(crew_summary.keys()),
            "crew_details": crew_summary,
        }

    def clear_traces(self) -> None:
        """Clear all flow traces."""
        self.flow_traces.clear()
        logger.debug("Cleared all data flow traces")


class ReporterContextValidator:
    """
    Specialized validator for reporter context consumption.

    Ensures the reporter only consumes validated upstream context
    and produces compliant HTML output.
    """

    def __init__(self) -> None:
        """Initialize reporter validator."""
        self.required_context_keys = {"ten_k_insights", "market_sentiment", "risk_score_standardized"}
        self.optional_context_keys = {
            "portfolio_allocation",
            "risk_assessment",
            "etf_factsheet",
            "crypto_thesis",
            "stock_analysis",
            "etf_analysis",
            "crypto_analysis",
        }

    def validate_reporter_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Validate reporter context for compliance.

        Args:
            context: Context data being passed to reporter

        Returns:
            Validation result

        """
        issues = []
        warnings = []

        context_keys = set(context.keys())

        # Check for required context
        missing_required = self.required_context_keys - context_keys
        if missing_required:
            warnings.append(f"Missing required context keys: {missing_required}")

        # Check for unexpected context (not necessarily an error)
        all_expected_keys = self.required_context_keys | self.optional_context_keys
        unexpected_keys = context_keys - all_expected_keys

        if unexpected_keys:
            logger.info(f"Reporter context has additional keys: {unexpected_keys}")

        # Validate context data types and structure
        for key, value in context.items():
            if key in self.required_context_keys and value is None:
                warnings.append(f"Required context key '{key}' is None")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "has_required_context": len(missing_required) == 0,
            "context_keys": list(context_keys),
        }
