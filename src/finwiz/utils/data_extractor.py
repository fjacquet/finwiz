"""
Crew Data Extractor for FinWiz.

This module provides utilities for extracting and validating data from
CrewAI crew outputs, ensuring that required fields are present and properly
formatted before being used in scoring and analysis.
"""

import json
import logging
from typing import Any

from finwiz.exceptions.data_quality import MissingRequiredFieldError

logger = logging.getLogger(__name__)


class CrewDataExtractor:
    """
    Extract and validate data from crew outputs.

    This class provides methods to safely extract quantitative metrics,
    grades, scores, and other data from crew outputs, with proper validation
    and error handling.
    """

    def __init__(self, lineage_tracker: Any = None) -> None:
        """
        Initialize the CrewDataExtractor.

        Args:
            lineage_tracker: Optional DataLineage object to track data sources (Task 9.3)

        """
        self.logger = logger
        self.lineage_tracker = lineage_tracker

    def extract_quantitative_metrics(self, crew_output: str | dict, ticker: str, crew_name: str = "unknown_crew") -> dict[str, Any]:
        """
        Extract quantitative metrics from crew output.

        This method parses crew output and extracts critical quantitative
        metrics like volatility, max_drawdown, and beta. It validates that
        required fields are present and raises errors if critical data is missing.

        Args:
            crew_output: Crew output as string (JSON) or dict
            ticker: Ticker symbol being analyzed (for error messages)

        Returns:
            Dictionary with extracted quantitative metrics

        Raises:
            MissingRequiredFieldError: If critical metrics are missing
            ValueError: If crew output cannot be parsed

        Example:
            >>> extractor = CrewDataExtractor()
            >>> metrics = extractor.extract_quantitative_metrics(crew_output='{"performance_metrics": {"volatility": 0.25, "max_drawdown": -0.15}}', ticker="AAPL")
            >>> print(metrics["volatility"])
            0.25

        """
        # Parse JSON if string
        if isinstance(crew_output, str):
            try:
                data = json.loads(crew_output)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse crew output JSON for {ticker}: {e}")
                raise ValueError(f"Invalid JSON in crew output for {ticker}: {e}") from e
        else:
            data = crew_output

        # Extract performance metrics section
        perf_metrics = data.get("performance_metrics", {})

        if not perf_metrics:
            self.logger.warning(f"No performance_metrics section found in crew output for {ticker}. Available keys: {list(data.keys())}")
            # Try alternative locations
            perf_metrics = data.get("quantitative_analysis", {})
            if not perf_metrics:
                perf_metrics = data.get("risk_metrics", {})

        # Define required fields
        required_fields = ["volatility", "max_drawdown"]

        # Check for missing required fields
        missing_fields = []
        for field in required_fields:
            if field not in perf_metrics or perf_metrics[field] is None:
                missing_fields.append(field)

        if missing_fields:
            self.logger.error(f"Missing required metrics for {ticker}: {missing_fields}. Available keys in performance_metrics: {list(perf_metrics.keys())}")
            raise MissingRequiredFieldError(
                ticker=ticker,
                field=", ".join(missing_fields),
                context={
                    "source": "quantitative_analysis",
                    "available_keys": list(perf_metrics.keys()),
                    "missing_count": len(missing_fields),
                },
            )

        # Extract metrics with type conversion
        try:
            from datetime import datetime

            extraction_timestamp = datetime.now().isoformat()

            extracted_metrics = {
                "volatility": float(perf_metrics["volatility"]),
                "max_drawdown": float(perf_metrics["max_drawdown"]),
                "beta": float(perf_metrics["beta"]) if "beta" in perf_metrics and perf_metrics["beta"] is not None else None,
                "sharpe_ratio": (float(perf_metrics["sharpe_ratio"]) if "sharpe_ratio" in perf_metrics and perf_metrics["sharpe_ratio"] is not None else None),
                "sortino_ratio": (float(perf_metrics["sortino_ratio"]) if "sortino_ratio" in perf_metrics and perf_metrics["sortino_ratio"] is not None else None),
            }

            # Track data sources in lineage (Task 9.3)
            if self.lineage_tracker:
                for field_name, value in extracted_metrics.items():
                    if value is not None:
                        self.lineage_tracker.add_source(
                            source_id=f"{crew_name}_{field_name}",
                            source_type="api",  # From crew which calls APIs
                            source_name=crew_name,
                            field_name=field_name,
                            raw_value=perf_metrics.get(field_name),
                            timestamp=extraction_timestamp,
                            metadata={"crew": crew_name, "section": "performance_metrics"},
                        )

                        # Track type conversion transformation if needed
                        raw_value = perf_metrics.get(field_name)
                        if raw_value is not None and type(raw_value) != type(value):
                            self.lineage_tracker.add_transformation(
                                transformation_id=f"convert_{field_name}",
                                operation="type_conversion",
                                input_values={field_name: raw_value},
                                output_value=value,
                                formula=f"float({field_name})",
                            )

            self.logger.info(
                f"Successfully extracted quantitative metrics for {ticker}: volatility={extracted_metrics['volatility']:.3f}, max_drawdown={extracted_metrics['max_drawdown']:.3f}"
            )

            return extracted_metrics

        except (ValueError, TypeError) as e:
            self.logger.error(f"Failed to convert metrics to float for {ticker}: {e}")
            raise ValueError(f"Invalid metric values for {ticker}: {e}") from e

    def extract_grade_and_score(self, crew_output: str | dict, ticker: str, crew_name: str = "unknown_crew") -> dict[str, Any]:
        """
        Extract grade and composite score from crew output.

        Args:
            crew_output: Crew output as string (JSON) or dict
            ticker: Ticker symbol being analyzed (for error messages)

        Returns:
            Dictionary with 'grade' and 'composite_score' keys

        Raises:
            MissingRequiredFieldError: If grade or composite_score is missing

        Example:
            >>> extractor = CrewDataExtractor()
            >>> result = extractor.extract_grade_and_score(crew_output='{"grade": "A", "composite_score": 0.85}', ticker="AAPL")
            >>> print(result["grade"])
            'A'

        """
        # Parse JSON if string
        if isinstance(crew_output, str):
            try:
                data = json.loads(crew_output)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse crew output JSON for {ticker}: {e}")
                raise ValueError(f"Invalid JSON in crew output for {ticker}: {e}") from e
        else:
            data = crew_output

        # Check for grade
        if "grade" not in data or data["grade"] is None:
            self.logger.error(f"Missing grade for {ticker}. Available keys: {list(data.keys())}")
            raise MissingRequiredFieldError(ticker=ticker, field="grade", context={"source": "crew_output", "available_keys": list(data.keys())})

        # Check for composite_score
        if "composite_score" not in data or data["composite_score"] is None:
            self.logger.error(f"Missing composite_score for {ticker}. Available keys: {list(data.keys())}")
            raise MissingRequiredFieldError(ticker=ticker, field="composite_score", context={"source": "crew_output", "available_keys": list(data.keys())})

        try:
            from datetime import datetime

            extraction_timestamp = datetime.now().isoformat()

            result = {"grade": str(data["grade"]), "composite_score": float(data["composite_score"])}

            # Track data sources in lineage (Task 9.3)
            if self.lineage_tracker:
                self.lineage_tracker.add_source(
                    source_id=f"{crew_name}_grade",
                    source_type="api",
                    source_name=crew_name,
                    field_name="grade",
                    raw_value=data["grade"],
                    timestamp=extraction_timestamp,
                    metadata={"crew": crew_name, "section": "crew_output"},
                )

                self.lineage_tracker.add_source(
                    source_id=f"{crew_name}_composite_score",
                    source_type="api",
                    source_name=crew_name,
                    field_name="composite_score",
                    raw_value=data["composite_score"],
                    timestamp=extraction_timestamp,
                    metadata={"crew": crew_name, "section": "crew_output"},
                )

                # Track type conversion for composite_score if needed
                if type(data["composite_score"]) != float:
                    self.lineage_tracker.add_transformation(
                        transformation_id="convert_composite_score",
                        operation="type_conversion",
                        input_values={"composite_score": data["composite_score"]},
                        output_value=result["composite_score"],
                        formula="float(composite_score)",
                    )

            self.logger.info(f"Successfully extracted grade and score for {ticker}: grade={result['grade']}, score={result['composite_score']:.3f}")

            return result

        except (ValueError, TypeError) as e:
            self.logger.error(f"Failed to convert grade/score for {ticker}: {e}")
            raise ValueError(f"Invalid grade or score values for {ticker}: {e}") from e

    def validate_grade_score_consistency(self, grade: str, composite_score: float, ticker: str) -> bool:
        """
        Validate that grade matches composite score according to grading scale.

        Grading scale:
        - A+: >= 0.85
        - A:  >= 0.75
        - B:  >= 0.65
        - C:  >= 0.55
        - D:  >= 0.45
        - F:  < 0.45

        Args:
            grade: Letter grade
            composite_score: Composite score (0.0-1.0)
            ticker: Ticker symbol (for logging)

        Returns:
            True if grade matches score, False otherwise

        Example:
            >>> extractor = CrewDataExtractor()
            >>> extractor.validate_grade_score_consistency("A", 0.80, "AAPL")
            True
            >>> extractor.validate_grade_score_consistency("A+", 0.65, "AAPL")
            False

        """
        # Define grade thresholds
        grade_thresholds = {"A+": 0.85, "A": 0.75, "B": 0.65, "C": 0.55, "D": 0.45, "F": 0.0}

        # Determine expected grade from score
        expected_grade = "F"
        for threshold_grade, threshold_score in grade_thresholds.items():
            if composite_score >= threshold_score:
                expected_grade = threshold_grade
                break

        # Check if grades match
        is_consistent = grade == expected_grade

        if not is_consistent:
            self.logger.warning(f"Grade-score mismatch for {ticker}: grade={grade}, score={composite_score:.3f}, expected={expected_grade}")

        return is_consistent
