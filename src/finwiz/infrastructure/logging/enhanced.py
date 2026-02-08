"""
Enhanced Logger for FinWiz.

Provides comprehensive error logging with full context for debugging and
troubleshooting. Implements Requirement 18: Comprehensive Error Logging.

This module provides structured logging methods for:
- Crew execution failures
- Data validation failures
- Template interpolation failures
- Portfolio merge operations
- Cache operations
- API call failures
- Flow halt summaries
"""

import json
import traceback
from datetime import datetime
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class EnhancedLogger:
    """
    Enhanced logger with comprehensive error context.

    Provides structured logging methods for common error scenarios in FinWiz,
    ensuring all relevant context is captured for debugging.

    Requirements: 18.1-18.10 (Comprehensive Error Logging)
    """

    def __init__(self, component_name: str):
        """
        Initialize enhanced logger for a specific component.

        Args:
            component_name: Name of the component using this logger

        """
        self.component_name = component_name
        self.logger = get_logger(component_name)

    def log_crew_failure(
        self,
        crew_name: str,
        ticker: str,
        inputs: dict[str, Any],
        exception: Exception,
        asset_class: str | None = None,
    ) -> None:
        """
        Log crew execution failure with full context.

        Args:
            crew_name: Name of the crew that failed
            ticker: Ticker symbol being analyzed
            inputs: Input parameters provided to the crew
            exception: Exception that was raised
            asset_class: Asset class (stock, etf, crypto)

        Requirements: 18.1-18.2 (Crew Failure Logging)

        """
        # Get full traceback
        tb_str = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))

        # Sanitize inputs (remove sensitive data like API keys)
        sanitized_inputs = self._sanitize_inputs(inputs)

        error_context = {
            "timestamp": datetime.now().isoformat(),
            "component": self.component_name,
            "crew_name": crew_name,
            "ticker": ticker,
            "asset_class": asset_class,
            "inputs": sanitized_inputs,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": tb_str,
        }

        self.logger.error(
            f"❌ Crew Execution Failed: {crew_name}\n"
            f"{'=' * 80}\n"
            f"Crew: {crew_name}\n"
            f"Ticker: {ticker}\n"
            f"Asset Class: {asset_class}\n"
            f"Exception: {type(exception).__name__}: {exception}\n"
            f"\nInputs Provided:\n"
            f"{json.dumps(sanitized_inputs, indent=2, default=str)}\n"
            f"\nFull Traceback:\n"
            f"{tb_str}\n"
            f"{'=' * 80}"
        )

        # Log structured data for potential log aggregation
        self.logger.debug(f"Crew failure context: {json.dumps(error_context, indent=2, default=str)}")

    def log_validation_failure(
        self,
        validation_type: str,
        data_sample: dict[str, Any],
        errors: list[str],
        field_path: str | None = None,
    ) -> None:
        """
        Log data validation failure with data samples.

        Args:
            validation_type: Type of validation that failed (e.g., "Pydantic", "Schema")
            data_sample: Sample of the invalid data (truncated if large)
            errors: List of validation error messages
            field_path: Path to the field that failed validation

        Requirements: 18.4-18.5 (Validation Failure Logging)

        """
        # Truncate large data samples
        truncated_sample = self._truncate_data(data_sample, max_size=500)

        error_context = {
            "timestamp": datetime.now().isoformat(),
            "component": self.component_name,
            "validation_type": validation_type,
            "field_path": field_path,
            "errors": errors,
            "data_sample": truncated_sample,
        }

        self.logger.error(
            f"❌ Validation Failed: {validation_type}\n"
            f"{'=' * 80}\n"
            f"Validation Type: {validation_type}\n"
            f"Field Path: {field_path or 'N/A'}\n"
            f"\nValidation Errors:\n" + "\n".join(f"  • {error}" for error in errors) + f"\n\nData Sample (truncated):\n"
            f"{json.dumps(truncated_sample, indent=2, default=str)}\n"
            f"{'=' * 80}"
        )

        # Log structured data
        self.logger.debug(f"Validation failure context: {json.dumps(error_context, indent=2, default=str)}")

    def log_template_interpolation_failure(
        self,
        template_string: str,
        available_variables: dict[str, Any],
        missing_variables: list[str],
        crew_name: str | None = None,
    ) -> None:
        """
        Log template variable interpolation failure.

        Args:
            template_string: The template string that failed
            available_variables: Variables that were available
            missing_variables: Variables that were missing
            crew_name: Name of the crew (if applicable)

        Requirements: 18.3 (Template Interpolation Logging)

        """
        # Sanitize available variables
        sanitized_vars = self._sanitize_inputs(available_variables)

        error_context = {
            "timestamp": datetime.now().isoformat(),
            "component": self.component_name,
            "crew_name": crew_name,
            "template_string": template_string[:200],  # Truncate long templates
            "missing_variables": missing_variables,
            "available_variables": list(sanitized_vars.keys()),
        }

        self.logger.error(
            f"❌ Template Interpolation Failed\n"
            f"{'=' * 80}\n"
            f"Crew: {crew_name or 'N/A'}\n"
            f"Template: {template_string[:200]}{'...' if len(template_string) > 200 else ''}\n"
            f"\nMissing Variables:\n"
            + "\n".join(f"  • {var}" for var in missing_variables)
            + "\n\nAvailable Variables:\n"
            + "\n".join(f"  • {var}" for var in sanitized_vars.keys())
            + f"\n{'=' * 80}"
        )

        # Log structured data
        self.logger.debug(f"Template interpolation failure context: {json.dumps(error_context, indent=2, default=str)}")

    def log_portfolio_merge_operation(
        self,
        holdings_before: int,
        holdings_after: int,
        deep_analysis_count: int,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        """
        Log portfolio merge operation results.

        Args:
            holdings_before: Number of holdings before merge
            holdings_after: Number of holdings after merge
            deep_analysis_count: Number of deep analysis results available
            success: Whether the merge was successful
            error_message: Error message if merge failed

        Requirements: 18.6-18.7 (Portfolio Merge Logging)

        """
        status = "✅ SUCCESS" if success else "❌ FAILED"

        merge_context = {
            "timestamp": datetime.now().isoformat(),
            "component": self.component_name,
            "holdings_before": holdings_before,
            "holdings_after": holdings_after,
            "deep_analysis_count": deep_analysis_count,
            "success": success,
            "error_message": error_message,
        }

        log_message = (
            f"{status}: Portfolio Merge Operation\n"
            f"{'=' * 80}\n"
            f"Holdings Before Merge: {holdings_before}\n"
            f"Holdings After Merge: {holdings_after}\n"
            f"Deep Analysis Results Available: {deep_analysis_count}\n"
        )

        if not success and error_message:
            log_message += f"\nError: {error_message}\n"

        log_message += f"{'=' * 80}"

        if success:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)

        # Log structured data
        self.logger.debug(f"Portfolio merge context: {json.dumps(merge_context, indent=2, default=str)}")

    def log_cache_operation(
        self,
        operation: str,
        ticker: str,
        asset_class: str,
        success: bool,
        cache_path: str | None = None,
        error_message: str | None = None,
        age_hours: float | None = None,
    ) -> None:
        """
        Log cache operation (save, load, miss, stale).

        Args:
            operation: Type of operation (save, load, miss, stale)
            ticker: Ticker symbol
            asset_class: Asset class
            success: Whether the operation was successful
            cache_path: Path to cache file
            error_message: Error message if operation failed
            age_hours: Age of cached data in hours (for load operations)

        Requirements: 18.8 (Cache Operation Logging)

        """
        status = "✅" if success else "❌"

        cache_context = {
            "timestamp": datetime.now().isoformat(),
            "component": self.component_name,
            "operation": operation,
            "ticker": ticker,
            "asset_class": asset_class,
            "success": success,
            "cache_path": cache_path,
            "age_hours": age_hours,
            "error_message": error_message,
        }

        log_message = f"{status} Cache {operation.upper()}: {ticker} ({asset_class})\n  Path: {cache_path or 'N/A'}\n"

        if age_hours is not None:
            log_message += f"  Age: {age_hours:.1f} hours\n"

        if error_message:
            log_message += f"  Error: {error_message}\n"

        if success:
            self.logger.debug(log_message)
        else:
            self.logger.warning(log_message)

        # Log structured data
        self.logger.debug(f"Cache operation context: {json.dumps(cache_context, indent=2, default=str)}")

    def log_api_call_failure(
        self,
        api_name: str,
        endpoint: str,
        status_code: int | None,
        response_body: str | None,
        exception: Exception | None = None,
        request_params: dict[str, Any] | None = None,
    ) -> None:
        """
        Log API call failure with request/response details.

        Args:
            api_name: Name of the API (e.g., "Yahoo Finance", "Alpha Vantage")
            endpoint: API endpoint that was called
            status_code: HTTP status code (if available)
            response_body: Response body (truncated if large)
            exception: Exception that was raised (if any)
            request_params: Request parameters (sanitized)

        Requirements: 18.9 (API Call Failure Logging)

        """
        # Sanitize request params
        sanitized_params = self._sanitize_inputs(request_params or {})

        # Truncate response body
        truncated_response = response_body[:500] if response_body else "N/A"
        if response_body and len(response_body) > 500:
            truncated_response += "... (truncated)"

        api_context = {
            "timestamp": datetime.now().isoformat(),
            "component": self.component_name,
            "api_name": api_name,
            "endpoint": endpoint,
            "status_code": status_code,
            "request_params": sanitized_params,
            "response_body": truncated_response,
            "exception": str(exception) if exception else None,
        }

        log_message = (
            f"❌ API Call Failed: {api_name}\n"
            f"{'=' * 80}\n"
            f"API: {api_name}\n"
            f"Endpoint: {endpoint}\n"
            f"Status Code: {status_code or 'N/A'}\n"
            f"\nRequest Parameters:\n"
            f"{json.dumps(sanitized_params, indent=2, default=str)}\n"
            f"\nResponse Body (truncated):\n"
            f"{truncated_response}\n"
        )

        if exception:
            log_message += f"\nException: {type(exception).__name__}: {exception}\n"

        log_message += f"{'=' * 80}"

        self.logger.error(log_message)

        # Log structured data
        self.logger.debug(f"API call failure context: {json.dumps(api_context, indent=2, default=str)}")

    def log_flow_halt_summary(
        self,
        reason: str,
        succeeded_phases: list[str],
        failed_phases: list[str],
        total_holdings: int,
        successful_holdings: int,
        failed_holdings: list[str],
        execution_time_seconds: float,
    ) -> None:
        """
        Log flow halt summary with execution statistics.

        Args:
            reason: Reason for flow halt
            succeeded_phases: List of phases that completed successfully
            failed_phases: List of phases that failed
            total_holdings: Total number of holdings
            successful_holdings: Number of successfully analyzed holdings
            failed_holdings: List of tickers that failed
            execution_time_seconds: Total execution time

        Requirements: 18.10 (Flow Halt Summary Logging)

        """
        success_rate = (successful_holdings / total_holdings * 100) if total_holdings > 0 else 0

        halt_context = {
            "timestamp": datetime.now().isoformat(),
            "component": self.component_name,
            "reason": reason,
            "succeeded_phases": succeeded_phases,
            "failed_phases": failed_phases,
            "total_holdings": total_holdings,
            "successful_holdings": successful_holdings,
            "failed_holdings": failed_holdings,
            "success_rate": success_rate,
            "execution_time_seconds": execution_time_seconds,
        }

        self.logger.critical(
            f"🛑 FLOW HALTED: {reason}\n"
            f"{'=' * 80}\n"
            f"Reason: {reason}\n"
            f"\nExecution Summary:\n"
            f"  • Total Holdings: {total_holdings}\n"
            f"  • Successful: {successful_holdings} ({success_rate:.1f}%)\n"
            f"  • Failed: {len(failed_holdings)}\n"
            f"  • Execution Time: {execution_time_seconds:.1f}s\n"
            f"\nSucceeded Phases:\n"
            + "\n".join(f"  ✅ {phase}" for phase in succeeded_phases)
            + "\n\nFailed Phases:\n"
            + "\n".join(f"  ❌ {phase}" for phase in failed_phases)
            + "\n\nFailed Holdings:\n"
            + "\n".join(f"  • {ticker}" for ticker in failed_holdings)
            + f"\n{'=' * 80}"
        )

        # Log structured data
        self.logger.debug(f"Flow halt context: {json.dumps(halt_context, indent=2, default=str)}")

    def _sanitize_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize inputs by removing sensitive data like API keys.

        Args:
            inputs: Input dictionary to sanitize

        Returns:
            Sanitized dictionary with sensitive data masked

        """
        sanitized = {}
        sensitive_keys = {"api_key", "apikey", "token", "password", "secret", "auth"}

        for key, value in inputs.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                # Mask sensitive values
                if isinstance(value, str) and len(value) > 8:
                    sanitized[key] = f"{value[:8]}..." + "*" * 8
                else:
                    sanitized[key] = "***MASKED***"
            else:
                sanitized[key] = value

        return sanitized

    def _truncate_data(self, data: Any, max_size: int = 500) -> Any:
        """
        Truncate large data structures for logging.

        Args:
            data: Data to truncate
            max_size: Maximum size in characters

        Returns:
            Truncated data

        """
        try:
            data_str = json.dumps(data, default=str)
            if len(data_str) > max_size:
                return json.loads(data_str[:max_size]) if data_str[:max_size].endswith("}") else data_str[:max_size] + "..."
            return data
        except (json.JSONDecodeError, TypeError, ValueError, OverflowError) as e:
            # If JSON serialization fails, convert to string and truncate
            logger.warning(f"JSON serialization failed during data truncation: {e}")
            data_str = str(data)
            if len(data_str) > max_size:
                return data_str[:max_size] + "..."
            return data_str


def get_enhanced_logger(component_name: str) -> EnhancedLogger:
    """
    Get an enhanced logger instance for a component.

    Args:
        component_name: Name of the component

    Returns:
        EnhancedLogger instance

    """
    return EnhancedLogger(component_name)
