"""Contract validator for standardized crew output validation."""

from __future__ import annotations

import logging
from typing import Any

from .result import ValidationResult

logger = logging.getLogger(__name__)


class ContractValidator:
    """
    Validates standardized contract keys between crews and reporter.

    Ensures that crew outputs conform to expected contract keys that
    the reporter depends on for consistent data processing.
    """

    # Standard contract keys expected by the reporter
    STOCK_CONTRACT_KEYS = {
        "ten_k_insights": "list[TenKInsight]",
        "market_sentiment": "list[MarketSentiment]",
        "risk_score_standardized": "list[RiskAssessmentStandardized]",
    }

    ETF_CONTRACT_KEYS = {
        "etf_factsheets": "list[ETFFactsheet]",
        "etf_holdings": "list[ETFTopHolding]",
        "risk_score_standardized": "list[RiskAssessmentStandardized]",
    }

    CRYPTO_CONTRACT_KEYS = {
        "crypto_theses": "list[CryptoThesis]",
        "risk_score_standardized": "list[RiskAssessmentStandardized]",
    }

    # All valid contract keys across crews
    ALL_CONTRACT_KEYS = {
        **STOCK_CONTRACT_KEYS,
        **ETF_CONTRACT_KEYS,
        **CRYPTO_CONTRACT_KEYS,
    }

    def __init__(self) -> None:
        """Initialize the contract validator."""
        pass

    def validate_crew_contract(self, data: dict[str, Any], crew_type: str) -> ValidationResult:
        """
        Validate that crew output contains expected contract keys.

        Args:
            data: Crew output data to validate
            crew_type: Type of crew (stock, etf, crypto, report)

        Returns:
            ValidationResult with contract validation status

        """
        result = ValidationResult(is_valid=True)

        # Get expected contract keys for this crew type
        expected_keys = self._get_expected_keys(crew_type)

        if not expected_keys:
            result.add_warning(
                field_path="crew_type",
                message=f"No contract keys defined for crew type: {crew_type}",
                context={"crew_type": crew_type},
            )
            return result

        # Check for missing required keys
        missing_keys = []
        for key in expected_keys:
            if key not in data:
                missing_keys.append(key)

        if missing_keys:
            result.add_error(
                field_path="contract_keys",
                error_type="missing_required_keys",
                message=f"Missing required contract keys: {missing_keys}",
                context={
                    "crew_type": crew_type,
                    "missing_keys": missing_keys,
                    "expected_keys": list(expected_keys.keys()),
                },
            )

        # Check for unexpected keys (potential schema drift)
        unexpected_keys = []
        for key in data.keys():
            if key not in self.ALL_CONTRACT_KEYS and not key.startswith("_"):
                unexpected_keys.append(key)

        if unexpected_keys:
            result.add_warning(
                field_path="contract_keys",
                message=f"Unexpected keys found (potential schema drift): {unexpected_keys}",
                context={
                    "crew_type": crew_type,
                    "unexpected_keys": unexpected_keys,
                    "all_valid_keys": list(self.ALL_CONTRACT_KEYS.keys()),
                },
            )

        # Validate data types for present keys
        for key, expected_type in expected_keys.items():
            if key in data:
                self._validate_key_type(data[key], key, expected_type, result)

        logger.debug(f"Contract validation completed for {crew_type} crew")
        return result

    def validate_reporter_contract(self, data: dict[str, Any]) -> ValidationResult:
        """
        Validate that reporter input contains all required contract keys.

        Args:
            data: Reporter input data to validate

        Returns:
            ValidationResult with contract validation status

        """
        result = ValidationResult(is_valid=True)

        # Reporter expects all contract keys to be present
        required_keys = [
            "ten_k_insights",
            "stock_sentiments",
            "stock_risks",
            "etf_factsheets",
            "etf_holdings",
            "etf_risks",
            "crypto_theses",
            "crypto_risks",
        ]

        missing_keys = []
        for key in required_keys:
            if key not in data:
                missing_keys.append(key)

        if missing_keys:
            result.add_error(
                field_path="reporter_contract",
                error_type="missing_reporter_keys",
                message=f"Reporter missing required keys: {missing_keys}",
                context={"missing_keys": missing_keys, "required_keys": required_keys},
            )

        logger.debug("Reporter contract validation completed")
        return result

    def _get_expected_keys(self, crew_type: str) -> dict[str, str]:
        """Get expected contract keys for a crew type."""
        crew_contracts = {
            "stock": self.STOCK_CONTRACT_KEYS,
            "etf": self.ETF_CONTRACT_KEYS,
            "crypto": self.CRYPTO_CONTRACT_KEYS,
            "report": {},  # Reporter has no output contract
        }

        return crew_contracts.get(crew_type, {})

    def _validate_key_type(self, value: Any, key: str, expected_type: str, result: ValidationResult) -> None:
        """Validate that a contract key has the expected type."""
        # Basic type validation - more sophisticated validation happens in schema validation
        if expected_type.startswith("list[") and not isinstance(value, list):
            result.add_error(
                field_path=f"contract_keys.{key}",
                error_type="invalid_type",
                message=f"Expected {expected_type} for key '{key}', got {type(value).__name__}",
                input_value=type(value).__name__,
                context={"key": key, "expected_type": expected_type},
            )
        elif expected_type == "dict" and not isinstance(value, dict):
            result.add_error(
                field_path=f"contract_keys.{key}",
                error_type="invalid_type",
                message=f"Expected dict for key '{key}', got {type(value).__name__}",
                input_value=type(value).__name__,
                context={"key": key, "expected_type": expected_type},
            )
