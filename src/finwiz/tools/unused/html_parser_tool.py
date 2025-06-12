"""
Define HTML Parser Tool for extracting structured information from HTML content.

This module provides a specialized tool for parsing HTML content from crew reports
and extracting structured information like ticker symbols, recommendations,
and key points. It's designed to help the Report Crew analyze outputs from
other specialized crews without conducting additional external research.
"""

import re
from typing import Any, Literal

from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class HTMLParserToolInput(BaseModel):
    """Input schema for HTMLParserTool."""

    html_content: str = Field(..., description="HTML content to parse.")
    extraction_type: Literal["all", "tickers", "recommendations"] = Field(
        default="all",
        description="Type of information to extract (tickers, recommendations, all)."
    )


class HTMLParserTool(BaseTool):
    """
    Tool for parsing HTML content from other crews' reports.

    Extracts structured information like ticker symbols, recommendations,
    and key points from HTML content. Designed specifically to analyze
    outputs from Stock, ETF, and Crypto crews without conducting
    additional external research.
    """

    name: str = "HTML Parser Tool"
    description: str = (
        "Extracts structured information from HTML content including ticker symbols, "
        "recommendations, currency values, and contexts containing emojis."
    )
    args_schema: type[BaseModel] = HTMLParserToolInput

    def _run(self, html_content: str, extraction_type: str = "all") -> dict[str, Any]:
        """
        Parse HTML content and extract structured information.

        Args:
            html_content: HTML content to parse
            extraction_type: Type of information to extract (tickers, recommendations, all)

        Returns:
            Dictionary containing extracted information

        """
        soup = BeautifulSoup(html_content, "html.parser")
        result = {}

        # Extract all text content
        text_content = soup.get_text(separator=" ", strip=True)

        if extraction_type in ["all", "tickers"]:
            # Extract ticker symbols (common format: uppercase 1-5 letters, sometimes with numbers)
            # Format: 1-5 uppercase letters, optionally followed by a dot and 1-2 more letters
            ticker_pattern = r"\b[A-Z]{1,5}(?:\.[A-Z]{1,2})?\b"
            tickers = re.findall(ticker_pattern, text_content)
            result["tickers"] = list(set(tickers))

        if extraction_type in ["all", "recommendations"]:
            # Extract sections with recommendation-related keywords
            recommendation_keywords = [
                "recommend",
                "buy",
                "sell",
                "hold",
                "invest",
                "allocation",
            ]
            recommendation_sections = []

            paragraphs = soup.find_all(["p", "div", "li"])
            for p in paragraphs:
                p_text = p.get_text(strip=True)
                if any(
                    keyword in p_text.lower() for keyword in recommendation_keywords
                ):
                    recommendation_sections.append(p_text)

            result["recommendations"] = recommendation_sections

        if extraction_type == "all":
            # Extract any numeric values with currency symbols
            currency_pattern = r"(\$|\u20ac|\u00a3|CHF)\s?[\d,]+(\.[\d]+)?"
            currency_values = re.findall(currency_pattern, text_content)
            result["currency_values"] = [
                f"{symbol}{value}" for symbol, value in currency_values
            ]

            # Extract all emojis and their surrounding context
            # Unicode ranges for common emoji characters
            emoji_pattern = (r"[\U0001F300-\U0001F64F\U0001F680-\U0001F6FF"
                            r"\u2600-\u26FF\u2700-\u27BF]")
            emojis_with_context = []

            for p in paragraphs:
                p_text = p.get_text(strip=True)
                if re.search(emoji_pattern, p_text):
                    emojis_with_context.append(p_text)

            result["emojis_with_context"] = emojis_with_context

        return result
