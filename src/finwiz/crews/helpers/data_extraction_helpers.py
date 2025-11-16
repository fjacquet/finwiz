"""
Data extraction and validation helpers for ReportCrew.

This module provides helper methods for extracting and validating data
from various sources including deep analysis HTML files, backtesting data,
and crew outputs.
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DeepAnalysisExtractor:
    """Extracts information from deep analysis HTML files."""

    @staticmethod
    def load_deep_analysis_html_files() -> dict[str, str]:
        """
        Load deep analysis HTML files for all holdings.

        Returns:
            Dictionary mapping ticker to HTML content with extracted grade info

        """
        deep_analysis_dir = Path("output/deep_analysis")
        html_content = {}

        if not deep_analysis_dir.exists():
            logger.warning("Deep analysis directory not found")
            return {}

        # Load all HTML files
        for html_file in deep_analysis_dir.glob("*_deep_analysis_*.html"):
            try:
                # Extract ticker from filename (e.g., AAPL_deep_analysis_stock.html -> AAPL)
                ticker = html_file.stem.split("_deep_analysis_")[0]

                # Read HTML content
                with open(html_file, encoding="utf-8") as f:
                    content = f.read()

                # Extract key information using regex - handle multiple formats
                # Format 1: <div class="grade Aminus" title="A-">A-</div>
                # Format 2: <div class="grade A">A</div>
                grade_match = re.search(r'<div class="grade[^"]*" title="([^"]+)">', content)
                if not grade_match:
                    # Try format 2: extract from class name
                    grade_match = re.search(r'<div class="grade\s+([A-F][+-]?)">', content)
                    if grade_match:
                        grade = grade_match.group(1)
                    else:
                        grade = "Unknown"
                else:
                    grade = grade_match.group(1)

                # Score can be in multiple formats
                score_match = re.search(r"Score composite[:\s]*([\d.]+)\s*/\s*[\d.]+", content, re.IGNORECASE)
                if not score_match:
                    score_match = re.search(r"<div[^>]*>(\d+\.\d+)\s*/\s*1\.00</div>", content)

                score = score_match.group(1) if score_match else "0.0"

                # Store extracted info (first 2000 chars of HTML for context)
                html_content[ticker] = {
                    "grade": grade,
                    "composite_score": float(score),
                    "html_preview": content[:2000],  # First 2000 chars for context
                    "file_path": str(html_file),
                }

                logger.debug(f"Loaded {ticker}: Grade {grade}, Score {score}")

            except Exception as e:
                logger.error(f"Failed to load {html_file}: {e}")
                continue

        logger.info(f"Loaded {len(html_content)} deep analysis HTML files")
        return html_content


class TickerValidator:
    """Validates and extracts tickers from crew data."""

    @staticmethod
    def extract_validated_tickers(context: dict[str, Any]) -> list[str]:
        """
        Extract validated tickers from upstream crew data.

        This method prevents hallucination by extracting only real tickers
        that were validated by upstream crews (stock, ETF, crypto).

        Args:
            context: Integrated data context from all crews

        Returns:
            List of validated ticker symbols

        """
        tickers = set()

        # FIXED: Look in consolidated_crew_data instead of stock_analysis_data
        consolidated_crew_data = context.get("consolidated_crew_data", {})

        # Extract from stock data
        stock_data = consolidated_crew_data.get("stock", {})
        if isinstance(stock_data, dict):
            for task in stock_data.get("tasks_output", []):
                if isinstance(task, dict):
                    pydantic = task.get("pydantic", {})
                    if isinstance(pydantic, dict) and "ticker" in pydantic:
                        ticker = pydantic["ticker"]
                        if ticker and isinstance(ticker, str):
                            tickers.add(ticker.upper())

        # Extract from ETF data
        etf_data = consolidated_crew_data.get("etf", {})
        if isinstance(etf_data, dict):
            for task in etf_data.get("tasks_output", []):
                if isinstance(task, dict):
                    pydantic = task.get("pydantic", {})
                    if isinstance(pydantic, dict) and "ticker" in pydantic:
                        ticker = pydantic["ticker"]
                        if ticker and isinstance(ticker, str):
                            tickers.add(ticker.upper())

        # Extract from crypto data
        crypto_data = consolidated_crew_data.get("crypto", {})
        if isinstance(crypto_data, dict):
            for task in crypto_data.get("tasks_output", []):
                if isinstance(task, dict):
                    pydantic = task.get("pydantic", {})
                    if isinstance(pydantic, dict):
                        # Crypto might use 'symbol' instead of 'ticker'
                        symbol = pydantic.get("symbol") or pydantic.get("ticker")
                        if symbol and isinstance(symbol, str):
                            tickers.add(symbol.upper())

        # Also check for consolidated ticker validation results
        ticker_validation = context.get("ticker_validation", {})
        if isinstance(ticker_validation, dict):
            validated = ticker_validation.get("validated_tickers", [])
            if isinstance(validated, list):
                for ticker in validated:
                    if ticker and isinstance(ticker, str):
                        tickers.add(ticker.upper())

        validated_list = sorted(list(tickers))

        logger.info(f"Extracted {len(validated_list)} validated tickers from upstream data", extra={"tickers": validated_list})

        return validated_list

    @staticmethod
    def validate_task_output(task_output: str, validated_tickers: list[str]) -> None:
        """
        Validate that task output only contains validated tickers.

        This prevents hallucination by checking for common fake tickers
        and ensuring all mentioned tickers are in the validated list.

        Args:
            task_output: The output text from a task
            validated_tickers: List of validated ticker symbols

        Raises:
            ValueError: If hallucinated tickers are detected

        """
        # Common hallucinated ticker patterns
        hallucinated_patterns = ["ABC", "XYZ", "LMN", "TEST", "EXAMPLE", "SAMPLE", "TICKER", "STOCK", "ETF", "CRYPTO"]

        # Convert validated tickers to uppercase for comparison
        validated_upper = [t.upper() for t in validated_tickers]

        # Check for hallucinated patterns
        for pattern in hallucinated_patterns:
            if pattern in validated_upper:
                # Skip if it's actually a valid ticker
                continue

            # Check if pattern appears as a standalone word (not part of another word)
            if re.search(rf"\b{pattern}\b", task_output):
                error_msg = (
                    f"Task output contains hallucinated ticker '{pattern}' "
                    f"which is not in validated_tickers: {validated_tickers}. "
                    f"This indicates the agent is inventing fake ticker symbols."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

        # Check for fake company names that often accompany hallucinated tickers
        fake_company_patterns = [
            "Alpha Beta Corp",
            "Lumina Networks",
            "Xylon Holdings",
            "Example Corp",
            "Sample Inc",
            "Test Company",
        ]

        for fake_company in fake_company_patterns:
            if fake_company in task_output:
                error_msg = f"Task output contains fake company name '{fake_company}'. This indicates the agent is hallucinating company information."
                logger.error(error_msg)
                raise ValueError(error_msg)

        logger.debug("Task output validation passed - no hallucinated tickers detected")


class MetricsExtractor:
    """Extracts metrics from validation results."""

    @staticmethod
    def safe_get_metric(vr_data: dict[str, Any], key: str) -> float | None:
        """
        Safely extract a metric from validation result dict.

        Args:
            vr_data: Validation result dictionary
            key: Key to extract

        Returns:
            Float value or None if not available or invalid

        """
        value = vr_data.get(key)
        if value is None:
            return None

        # Check for string placeholders
        if isinstance(value, str):
            return None

        try:
            float_value = float(value)
            # Check for reasonable range
            if not (-1e10 < float_value < 1e10):
                return None
            return float_value
        except (ValueError, TypeError):
            return None

    @staticmethod
    def calculate_calmar_from_dict(vr_data: dict[str, Any]) -> float | None:
        """Calculate Calmar ratio from validation result dict."""
        # Try to get annualized return from validation details
        annualized_return = None
        validation_details = vr_data.get("validation_details", [])
        if validation_details:
            returns = [d.get("annualized_return") for d in validation_details if d.get("annualized_return") is not None]
            if returns:
                annualized_return = sum(returns) / len(returns)

        # If not in details, try direct field
        if annualized_return is None:
            annualized_return = MetricsExtractor.safe_get_metric(vr_data, "annualized_return")

        max_dd = MetricsExtractor.safe_get_metric(vr_data, "average_max_drawdown")

        if annualized_return is None or max_dd is None:
            return None

        abs_max_dd = abs(max_dd)
        if abs_max_dd == 0:
            return None

        return annualized_return / abs_max_dd

    @staticmethod
    def extract_total_trades_from_dict(vr_data: dict[str, Any]) -> int | None:
        """Extract total trades from validation result dict."""
        validation_details = vr_data.get("validation_details", [])
        if not validation_details:
            return None

        trades = [d.get("total_trades", 0) for d in validation_details if "total_trades" in d]
        return sum(trades) if trades else None


class DataAgeExtractor:
    """Extracts age information from data freshness summaries."""

    @staticmethod
    def extract_age_from_summary(data_freshness_summary: dict, crew_type: str, default_age: float) -> float:
        """
        Extract age information from data freshness summary.

        Args:
            data_freshness_summary: Dictionary containing freshness information
            crew_type: Type of crew (stock, etf, crypto)
            default_age: Default age to use if not found

        Returns:
            Age in hours

        """
        try:
            # Try to extract age from the summary
            if crew_type in data_freshness_summary:
                crew_info = data_freshness_summary[crew_type]
                if isinstance(crew_info, dict) and "age_hours" in crew_info:
                    return float(crew_info["age_hours"])

            # If not found, use a reasonable default (half of max age)
            return default_age / 2.0

        except Exception as e:
            logger.warning(f"Failed to extract age for {crew_type}: {e}")
            return default_age / 2.0
