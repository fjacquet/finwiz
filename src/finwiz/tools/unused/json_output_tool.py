"""
Define JSON Output Tool for generating structured data output.

This module provides a specialized tool for producing JSON-formatted output
from crew analyses. It's designed to standardize the output format across
different crews (Stock, ETF, Crypto) to make it easier for the Report Crew
to consume and process the data without complex parsing.

The tool includes validation to ensure the output is clean, valid JSON
without HTML or emojis that belong in the HTML reports.
"""

import json
import logging
import re
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Set up logging
logger = logging.getLogger(__name__)

class JSONOutputError(Exception):
    """Exception raised for errors in the JSON output."""
    pass


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
    
    Includes validation to ensure the output is clean, valid JSON without HTML
    or emojis that belong in the HTML reports.
    """

    name: str = "JSON Output Tool"
    description: str = (
        "Generates standardized JSON output from analysis data. Can save to file or return as string. "
        "Validates and cleans the data to ensure it's proper machine-readable JSON without HTML or emojis. "
        "Useful for creating structured data that can be easily consumed by other crews."
    )
    args_schema: type[BaseModel] = JSONOutputToolInput

    def _validate_and_clean_data(self, data: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """
        Validate that the data is proper for JSON output and clean it if needed.
        
        Args:
            data: Data dictionary to validate and clean
            
        Returns:
            Tuple of (is_valid, error_message, cleaned_data)
        """
        # Deep copy to avoid modifying the original
        cleaned_data = json.loads(json.dumps(data))
        issues = []
        
        # Check for HTML content in string values
        def clean_html_and_emojis(obj: Any) -> Any:
            if isinstance(obj, str):
                # Check for HTML tags
                has_html = bool(re.search(r'<\/?[a-z][\w\-]*[^<]*>', obj))
                if has_html:
                    # Remove HTML tags for JSON output
                    cleaned = re.sub(r'<[^>]*>', '', obj)
                    issues.append("Removed HTML tags from string")
                    return cleaned.strip()
                
                # Check for common emoji patterns in unicode ranges
                emoji_pattern = re.compile(
                    "["
                    "\U0001F600-\U0001F64F"  # emoticons
                    "\U0001F300-\U0001F5FF"  # symbols & pictographs
                    "\U0001F680-\U0001F6FF"  # transport & map symbols
                    "\U0001F700-\U0001F77F"  # alchemical symbols
                    "\U0001F780-\U0001F7FF"  # Geometric Shapes
                    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                    "\U0001FA00-\U0001FA6F"  # Chess Symbols
                    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                    "\U00002702-\U000027B0"  # Dingbats
                    "\U000024C2-\U0001F251" 
                    "]")
                
                if emoji_pattern.search(obj):
                    cleaned = emoji_pattern.sub('', obj)
                    issues.append("Removed emojis from string")
                    return cleaned.strip()
                
                return obj
            elif isinstance(obj, dict):
                return {k: clean_html_and_emojis(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_html_and_emojis(item) for item in obj]
            else:
                return obj
        
        # Clean the data recursively
        cleaned_data = clean_html_and_emojis(cleaned_data)
        
        # Check if the cleaned data can be properly serialized
        try:
            json.dumps(cleaned_data)
            is_valid = True
            error_message = "" if not issues else "; ".join(issues)
        except (TypeError, ValueError) as e:
            is_valid = False
            error_message = f"JSON serialization error: {str(e)}"
            logger.error(error_message)
        
        return is_valid, error_message, cleaned_data
        
    def _run(self, data: dict[str, Any], output_path: str | None = None) -> str:
        """
        Generate JSON output from the provided data.

        Args:
            data: Dictionary containing analysis data (recommendations, tickers, etc.)
            output_path: Optional path to save the JSON output

        Returns:
            JSON string or confirmation message if saved to file

        Raises:
            JSONOutputError: If data cannot be properly converted to JSON
        """
        # Validate and clean the data first
        is_valid, error_message, cleaned_data = self._validate_and_clean_data(data)
        if not is_valid:
            raise JSONOutputError(f"Invalid JSON data: {error_message}")
        elif error_message:
            logger.warning(f"JSON data was cleaned: {error_message}")
            
        # Ensure the data has a standardized structure
        standardized_data = self._standardize_data(cleaned_data)

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


def get_json_tools():
    """
    Return a list of JSON output tools.
    
    This function is used to easily import all JSON output tools at once.
    
    Returns:
        list: A list of JSON output tool instances.
    """
    return [JSONOutputTool()]
