"""
Define JSON Output Tool for generating structured data output.

This module provides a specialized tool for producing JSON-formatted output
from crew analyses. It's designed to standardize the output format across
different crews (Stock, ETF, Crypto) to make it easier for the Report Crew
to consume and process the data without complex parsing.
"""

import json
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class JSONOutputToolInput(BaseModel):
    """Input schema for JSONOutputTool."""

    data: dict[str, Any] = Field(
        ...,
        description="Data to be converted to JSON format. Should include recommendations, tickers, analysis, etc."
    )
    output_path: str | None = Field(
        None,
        description="Optional path to save the JSON output. If not provided, returns the JSON as string."
    )


class JSONOutputTool(BaseTool):
    """
    Tool for generating standardized JSON output from crew analyses.

    Creates structured JSON data that can be easily consumed by the Report Crew
    without complex parsing. Provides a consistent format for recommendations,
    tickers, analysis details, and other relevant information.
    """

    name: str = "JSON Output Tool"
    description: str = (
        "Generates standardized JSON output from analysis data. Can save to file or return as string. "
        "Useful for creating structured data that can be easily consumed by other crews."
    )
    args_schema: type[BaseModel] = JSONOutputToolInput

    def _run(self, data: dict[str, Any], output_path: str | None = None) -> str:
        """
        Generate JSON output from the provided data.

        Args:
            data: Dictionary containing analysis data (recommendations, tickers, etc.)
            output_path: Optional path to save the JSON output

        Returns:
            JSON string or confirmation message if saved to file

        """
        # Ensure the data has a standardized structure
        standardized_data = self._standardize_data(data)

        # Convert to JSON
        json_output = json.dumps(standardized_data, indent=2)

        # Save to file if path is provided
        if output_path:
            with open(output_path, 'w') as f:
                f.write(json_output)
            return f"JSON output saved to {output_path}"

        # Otherwise return the JSON string
        return json_output

    def _standardize_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Ensure the data follows a standardized structure.

        This helps maintain consistency across different crews.

        Args:
            data: Original data dictionary

        Returns:
            Standardized data dictionary

        """
        # Define required keys for standardized output
        required_keys = [
            "crew_type",         # e.g., "stock", "etf", "crypto"
            "analysis_date",     # ISO format date
            "recommendations",   # List of recommendation objects
            "tickers_analyzed",  # List of all tickers that were analyzed
        ]

        # Add any missing required keys with empty values
        for key in required_keys:
            if key not in data:
                if key == "recommendations":
                    data[key] = []
                elif key == "tickers_analyzed":
                    data[key] = []
                else:
                    data[key] = ""

        # Ensure recommendations have a standard structure if they exist
        if "recommendations" in data and isinstance(data["recommendations"], list):
            standardized_recommendations = []
            for rec in data["recommendations"]:
                if isinstance(rec, dict):
                    # Ensure each recommendation has required fields
                    standard_rec = {
                        "ticker": rec.get("ticker", ""),
                        "name": rec.get("name", ""),
                        "action": rec.get("action", ""),
                        "price": rec.get("price", 0),
                        "currency": rec.get("currency", "CHF"),
                        "allocation": rec.get("allocation", 0),
                        "rationale": rec.get("rationale", ""),
                        "risk_level": rec.get("risk_level", ""),
                        "expected_return": rec.get("expected_return", ""),
                        "timeframe": rec.get("timeframe", ""),
                    }
                    # Preserve any additional fields that might be specific to a crew type
                    for k, v in rec.items():
                        if k not in standard_rec:
                            standard_rec[k] = v
                    standardized_recommendations.append(standard_rec)
            data["recommendations"] = standardized_recommendations

        return data
