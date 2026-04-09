"""
Perplexity Integration Validator.

Validates that all Perplexity-integrated tools have proper feature flag checking,
logging, and error handling. Used for testing and validation purposes.
"""

from __future__ import annotations

import inspect
from typing import Any

from finwiz.config.features.flags import get_feature_flags
from finwiz.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool
from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool
from finwiz.tools.enhanced_sentiment_tool import EnhancedSentimentAnalysisTool
from finwiz.tools.enhanced_technical_analyzer_tool import EnhancedTechnicalAnalyzerTool
from finwiz.tools.logger import get_logger
from finwiz.tools.twelve_data_tool import TwelveDataIndicatorTool

logger = get_logger(__name__)


class PerplexityIntegrationValidator:
    """Validator for Perplexity integration across all tools."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self.integrated_tools = [
            EnhancedSentimentAnalysisTool,
            TwelveDataIndicatorTool,
            EnhancedTechnicalAnalyzerTool,
            EnhancedSECAnalysisTool,
            AlphaVantageCompanyOverviewTool,
        ]
        self.feature_flags = get_feature_flags()

    def validate_all_integrations(self) -> dict[str, Any]:
        """
        Validate all Perplexity integrations.

        Returns:
            Validation results for all tools

        """
        results = {
            "overall_status": "pass",
            "feature_flag_status": self.feature_flags.get_flag_status("perplexity_research"),
            "tool_validations": {},
            "summary": {
                "total_tools": len(self.integrated_tools),
                "passed": 0,
                "failed": 0,
                "issues": [],
            },
        }

        for tool_class in self.integrated_tools:
            tool_name = tool_class.__name__
            logger.info(f"Validating {tool_name}")

            validation_result = self._validate_tool_integration(tool_class)
            results["tool_validations"][tool_name] = validation_result

            if validation_result["status"] == "pass":
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1
                results["overall_status"] = "fail"
                results["summary"]["issues"].extend(validation_result["issues"])

        return results

    def _validate_tool_integration(self, tool_class: type) -> dict[str, Any]:
        """
        Validate a single tool's Perplexity integration.

        Args:
            tool_class: Tool class to validate

        Returns:
            Validation results for the tool

        """
        result = {
            "status": "pass",
            "issues": [],
            "checks": {
                "has_init_method": False,
                "has_feature_flags": False,
                "has_perplexity_integration": False,
                "has_initialization_method": False,
                "has_feature_flag_checking": False,
                "has_success_failure_recording": False,
                "has_proper_logging": False,
            },
        }

        try:
            # Check if tool has __init__ method
            if hasattr(tool_class, "__init__"):
                result["checks"]["has_init_method"] = True
            else:
                result["issues"].append("Missing __init__ method")

            # Try to instantiate the tool
            try:
                tool_instance = tool_class()

                # Check for perplexity integration method (new pattern)
                if hasattr(tool_instance, "_get_perplexity_integration"):
                    result["checks"]["has_perplexity_integration"] = True
                    result["checks"]["has_feature_flags"] = True  # Implied by the method
                    result["checks"]["has_initialization_method"] = True  # New pattern
                else:
                    result["issues"].append("Missing _get_perplexity_integration method")

            except Exception as e:
                result["issues"].append(f"Failed to instantiate tool: {e!s}")

            # Check source code for feature flag checking patterns
            source_code = inspect.getsource(tool_class)

            if 'feature_flags.is_enabled("perplexity_research")' in source_code:
                result["checks"]["has_feature_flag_checking"] = True
            else:
                result["issues"].append("Missing feature flag checking in source code")

            if "record_success" in source_code and "record_failure" in source_code:
                result["checks"]["has_success_failure_recording"] = True
            else:
                result["issues"].append("Missing success/failure recording")

            if "logger.info" in source_code and "logger.warning" in source_code:
                result["checks"]["has_proper_logging"] = True
            else:
                result["issues"].append("Missing proper logging statements")

        except Exception as e:
            result["issues"].append(f"Validation error: {e!s}")

        # Determine overall status
        if result["issues"]:
            result["status"] = "fail"

        return result

    def get_feature_flag_status(self) -> dict[str, Any]:
        """Get current feature flag status."""
        return self.feature_flags.get_flag_status("perplexity_research")

    def validate_feature_flag_configuration(self) -> dict[str, Any]:
        """
        Validate feature flag configuration.

        Returns:
            Feature flag validation results

        """
        status = self.get_feature_flag_status()

        validation = {
            "status": "pass",
            "issues": [],
            "configuration": status,
        }

        # Check if feature flag exists
        if "error" in status:
            validation["status"] = "fail"
            validation["issues"].append("Feature flag 'perplexity_research' not found")
            return validation

        # Check configuration
        if status.get("strategy") != "circuit_breaker":
            validation["issues"].append("Expected circuit_breaker strategy for perplexity_research")

        if status.get("fallback_strategy") != "cached_only":
            validation["issues"].append("Expected cached_only fallback strategy")

        # Check circuit breaker configuration
        circuit_breaker = status.get("circuit_breaker", {})
        if not isinstance(circuit_breaker, dict):
            validation["issues"].append("Missing circuit breaker configuration")
        else:
            if circuit_breaker.get("threshold", 0) != 5:
                validation["issues"].append("Expected circuit breaker threshold of 5")

        if validation["issues"]:
            validation["status"] = "fail"

        return validation

    def generate_validation_report(self) -> str:
        """
        Generate a comprehensive validation report.

        Returns:
            Formatted validation report

        """
        results = self.validate_all_integrations()
        flag_validation = self.validate_feature_flag_configuration()

        report = "# Perplexity Integration Validation Report\n\n"

        # Overall Status
        report += f"## Overall Status: {results['overall_status'].upper()}\n\n"

        # Feature Flag Status
        report += "## Feature Flag Configuration\n"
        report += f"**Status**: {flag_validation['status'].upper()}\n"
        if flag_validation["issues"]:
            report += "**Issues**:\n"
            for issue in flag_validation["issues"]:
                report += f"- {issue}\n"
        report += "\n"

        # Summary
        summary = results["summary"]
        report += "## Integration Summary\n"
        report += f"- **Total Tools**: {summary['total_tools']}\n"
        report += f"- **Passed**: {summary['passed']}\n"
        report += f"- **Failed**: {summary['failed']}\n\n"

        # Tool Details
        report += "## Tool Validation Details\n\n"
        for tool_name, validation in results["tool_validations"].items():
            status_emoji = "✅" if validation["status"] == "pass" else "❌"
            report += f"### {status_emoji} {tool_name}\n"
            report += f"**Status**: {validation['status'].upper()}\n\n"

            # Checks
            report += "**Checks**:\n"
            for check, passed in validation["checks"].items():
                check_emoji = "✅" if passed else "❌"
                check_name = check.replace("_", " ").title()
                report += f"- {check_emoji} {check_name}\n"

            # Issues
            if validation["issues"]:
                report += "\n**Issues**:\n"
                for issue in validation["issues"]:
                    report += f"- {issue}\n"

            report += "\n"

        # Recommendations
        if results["overall_status"] == "fail" or flag_validation["status"] == "fail":
            report += "## Recommendations\n"
            report += "1. Fix all identified issues before deploying Perplexity integration\n"
            report += "2. Ensure all tools have consistent feature flag checking\n"
            report += "3. Verify proper error handling and logging across all tools\n"
            report += "4. Test feature flag enable/disable functionality\n\n"

        return report


def validate_perplexity_integrations() -> str:
    """
    Run full validation and return report.

    Returns:
        Validation report string

    """
    validator = PerplexityIntegrationValidator()
    return validator.generate_validation_report()


if __name__ == "__main__":
    # Run validation when script is executed directly
    print(validate_perplexity_integrations())
