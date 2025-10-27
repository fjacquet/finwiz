"""
Pydantic-validated JSON loading utilities.

This module provides utilities for loading JSON data with automatic Pydantic validation
to ensure type safety and data integrity at all boundaries.
"""

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class PydanticValidationError(Exception):
    """Raised when Pydantic validation fails during JSON loading."""

    def __init__(self, message: str, validation_errors: list | None = None):
        """Initialize with message and optional validation errors."""
        super().__init__(message)
        self.validation_errors = validation_errors or []


def load_json_with_validation(
    file_path: str | Path,
    model: type[T],
    strict: bool = True,
) -> T:
    """
    Load JSON file and validate against Pydantic model.

    Args:
        file_path: Path to JSON file
        model: Pydantic model class to validate against
        strict: If True, raise exception on validation errors. If False, log warnings.

    Returns:
        Validated Pydantic model instance

    Raises:
        PydanticValidationError: If validation fails and strict=True
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is malformed

    Example:
        >>> from finwiz.schemas.portfolio_review import PortfolioReview
        >>> portfolio = load_json_with_validation("output/portfolio/portfolio_review.json", PortfolioReview)

    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    logger.debug(f"Loading JSON from {file_path} with {model.__name__} validation")

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Validate with Pydantic
        validated_model = model.model_validate(data)

        logger.debug(f"Successfully validated {file_path} against {model.__name__}")
        return validated_model

    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in {file_path}: {e}"
        logger.error(error_msg)
        raise

    except ValidationError as e:
        error_msg = f"Pydantic validation failed for {file_path} against {model.__name__}"
        logger.error(f"{error_msg}: {e}")

        if strict:
            raise PydanticValidationError(error_msg, validation_errors=e.errors())
        else:
            logger.warning("Continuing with unvalidated data due to strict=False")
            # Return unvalidated data wrapped in model (best effort)
            return model.model_construct(**data)  # type: ignore


def load_json_string_with_validation(
    json_string: str,
    model: type[T],
    strict: bool = True,
) -> T:
    """
    Load JSON string and validate against Pydantic model.

    Args:
        json_string: JSON string to parse
        model: Pydantic model class to validate against
        strict: If True, raise exception on validation errors. If False, log warnings.

    Returns:
        Validated Pydantic model instance

    Raises:
        PydanticValidationError: If validation fails and strict=True
        json.JSONDecodeError: If JSON is malformed

    Example:
        >>> from finwiz.schemas.common import RiskAssessmentStandardized
        >>> risk = load_json_string_with_validation(
        ...     '{"scale": "0_5", "score": 3.5, "level": "High", "risk_factors": []}', RiskAssessmentStandardized
        ... )

    """
    logger.debug(f"Parsing JSON string with {model.__name__} validation")

    try:
        data = json.loads(json_string)

        # Validate with Pydantic
        validated_model = model.model_validate(data)

        logger.debug(f"Successfully validated JSON string against {model.__name__}")
        return validated_model

    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON string: {e}"
        logger.error(error_msg)
        raise

    except ValidationError as e:
        error_msg = f"Pydantic validation failed against {model.__name__}"
        logger.error(f"{error_msg}: {e}")

        if strict:
            raise PydanticValidationError(error_msg, validation_errors=e.errors())
        else:
            logger.warning("Continuing with unvalidated data due to strict=False")
            # Return unvalidated data wrapped in model (best effort)
            return model.model_construct(**data)  # type: ignore


def load_json_dict_with_validation(
    data: dict[str, Any],
    model: type[T],
    strict: bool = True,
) -> T:
    """
    Validate dictionary data against Pydantic model.

    Args:
        data: Dictionary data to validate
        model: Pydantic model class to validate against
        strict: If True, raise exception on validation errors. If False, log warnings.

    Returns:
        Validated Pydantic model instance

    Raises:
        PydanticValidationError: If validation fails and strict=True

    Example:
        >>> from finwiz.schemas.portfolio_review import HoldingDecision
        >>> holding = load_json_dict_with_validation(
        ...     {"ticker": "AAPL", "name": "Apple Inc.", ...},
        ...     HoldingDecision
        ... )

    """
    logger.debug(f"Validating dictionary against {model.__name__}")

    try:
        # Validate with Pydantic
        validated_model = model.model_validate(data)

        logger.debug(f"Successfully validated dictionary against {model.__name__}")
        return validated_model

    except ValidationError as e:
        error_msg = f"Pydantic validation failed against {model.__name__}"
        logger.error(f"{error_msg}: {e}")

        if strict:
            raise PydanticValidationError(error_msg, validation_errors=e.errors())
        else:
            logger.warning("Continuing with unvalidated data due to strict=False")
            # Return unvalidated data wrapped in model (best effort)
            return model.model_construct(**data)  # type: ignore


def save_json_with_validation(
    file_path: str | Path,
    model_instance: BaseModel,
    indent: int = 2,
) -> None:
    """
    Save Pydantic model instance to JSON file with validation.

    Args:
        file_path: Path to save JSON file
        model_instance: Pydantic model instance to save
        indent: JSON indentation level

    Raises:
        ValidationError: If model instance is invalid

    Example:
        >>> from finwiz.schemas.portfolio_review import PortfolioReview
        >>> portfolio = PortfolioReview(...)
        >>> save_json_with_validation("output/portfolio/portfolio_review.json", portfolio)

    """
    file_path = Path(file_path)

    logger.debug(f"Saving {model_instance.__class__.__name__} to {file_path}")

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Serialize with Pydantic (validates on serialization)
    json_data = model_instance.model_dump_json(indent=indent)

    # Write to file
    file_path.write_text(json_data, encoding="utf-8")

    logger.debug(f"Successfully saved validated data to {file_path}")


def validate_crew_output(
    crew_output: Any,
    expected_model: type[T],
    crew_name: str,
) -> T:
    """
    Validate crew output against expected Pydantic model.

    Args:
        crew_output: Raw crew output (dict, string, or model instance)
        expected_model: Expected Pydantic model class
        crew_name: Name of crew for logging

    Returns:
        Validated Pydantic model instance

    Raises:
        PydanticValidationError: If validation fails

    Example:
        >>> from finwiz.schemas.stock import StockScreeningResult
        >>> result = validate_crew_output(crew_output_data, StockScreeningResult, "stock_crew")

    """
    logger.debug(f"Validating {crew_name} output against {expected_model.__name__}")

    try:
        # If already a model instance, validate it
        if isinstance(crew_output, BaseModel):
            # Re-validate to ensure it matches expected model
            return expected_model.model_validate(crew_output.model_dump())

        # If string, parse as JSON
        if isinstance(crew_output, str):
            return load_json_string_with_validation(crew_output, expected_model)

        # If dict, validate directly
        if isinstance(crew_output, dict):
            return load_json_dict_with_validation(crew_output, expected_model)

        # Unsupported type
        raise PydanticValidationError(f"Unsupported crew output type for {crew_name}: {type(crew_output)}")

    except PydanticValidationError:
        raise
    except Exception as e:
        error_msg = f"Failed to validate {crew_name} output against {expected_model.__name__}: {e}"
        logger.error(error_msg)
        raise PydanticValidationError(error_msg)
