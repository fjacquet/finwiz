"""
Define JSON Parser Tool for extracting structured information from JSON content.

This module provides a specialized tool for parsing JSON content from crew reports
and extracting structured information like ticker symbols, recommendations,
and key points. It's designed to help the Report Crew efficiently analyze outputs from
other specialized crews without complex HTML parsing.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class JSONParserToolInput(BaseModel):
    """Input schema for JSONParserTool."""

    json_content: Optional[str] = Field(
        None,
        description="JSON content to parse as a string."
    )
    json_file_path: Optional[str] = Field(
        None,
        description="Path to JSON file to parse."
    )
    extraction_type: Optional[str] = Field(
        "all",
        description="Type of information to extract (e.g., 'tickers', 'recommendations', 'all')."
    )


class JSONParserTool(BaseTool):
    """
    Tool for parsing JSON content from other crews' reports.

    Extracts structured information like ticker symbols, recommendations,
    and key points from JSON content. Designed specifically to analyze
    outputs from Stock, ETF, and Crypto crews efficiently without
    complex HTML parsing.
    """

    name: str = "JSON Parser Tool"
    description: str = (
        "Extracts structured information from JSON content including ticker symbols, "
        "recommendations, allocation details, and other financial analysis data."
    )
    args_schema: type[BaseModel] = JSONParserToolInput

    def _run(
        self, 
        json_content: Optional[str] = None, 
        json_file_path: Optional[str] = None, 
        extraction_type: str = "all"
    ) -> Dict[str, Any]:
        """
        Parse JSON content and extract structured information.

        Args:
            json_content: JSON content as a string
            json_file_path: Path to a JSON file
            extraction_type: Type of information to extract (tickers, recommendations, all)

        Returns:
            Dictionary containing extracted information

        """
        # Load JSON data
        data = None
        
        if json_content:
            try:
                data = json.loads(json_content)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON content provided"}
        
        elif json_file_path:
            if not os.path.exists(json_file_path):
                return {"error": f"File not found: {json_file_path}"}
            
            try:
                with open(json_file_path, 'r') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {"error": f"Invalid JSON file: {json_file_path}"}
        
        else:
            return {"error": "Either json_content or json_file_path must be provided"}
        
        # Extract requested information
        result = {}
        
        if extraction_type == "all":
            # Return everything
            return data
        
        elif extraction_type == "tickers":
            # Extract all ticker symbols
            tickers = set()
            
            # From tickers_analyzed list
            if "tickers_analyzed" in data and isinstance(data["tickers_analyzed"], list):
                tickers.update(data["tickers_analyzed"])
            
            # From recommendations
            if "recommendations" in data and isinstance(data["recommendations"], list):
                for rec in data["recommendations"]:
                    if isinstance(rec, dict) and "ticker" in rec:
                        tickers.add(rec["ticker"])
            
            result["tickers"] = list(tickers)
        
        elif extraction_type == "recommendations":
            # Extract just the recommendations
            if "recommendations" in data and isinstance(data["recommendations"], list):
                result["recommendations"] = data["recommendations"]
            else:
                result["recommendations"] = []
        
        elif extraction_type == "allocation":
            # Extract allocation information
            allocations = []
            if "recommendations" in data and isinstance(data["recommendations"], list):
                for rec in data["recommendations"]:
                    if isinstance(rec, dict) and "ticker" in rec and "allocation" in rec:
                        allocations.append({
                            "ticker": rec["ticker"],
                            "allocation": rec["allocation"],
                            "currency": rec.get("currency", "CHF")
                        })
            result["allocations"] = allocations
        
        elif extraction_type == "summary":
            # Create a summary of the data
            summary = {
                "crew_type": data.get("crew_type", "unknown"),
                "analysis_date": data.get("analysis_date", ""),
                "total_tickers_analyzed": len(data.get("tickers_analyzed", [])),
                "total_recommendations": len(data.get("recommendations", [])),
            }
            
            # Add allocation totals if available
            total_allocation = 0
            if "recommendations" in data and isinstance(data["recommendations"], list):
                for rec in data["recommendations"]:
                    if isinstance(rec, dict) and "allocation" in rec:
                        try:
                            total_allocation += float(rec["allocation"])
                        except (ValueError, TypeError):
                            pass
            
            summary["total_allocation"] = total_allocation
            summary["currency"] = data.get("currency", "CHF")
            
            result = summary
        
        return result
