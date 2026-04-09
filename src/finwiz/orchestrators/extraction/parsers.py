"""
Data parsers for A+ opportunity extraction.

This module provides utilities for parsing and cleaning JSON data from discovery
crew outputs, including handling of malformed JSON and extracting specific fields.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any


class DataParser:
    """Utilities for parsing and cleaning JSON data from discovery outputs."""

    def __init__(self) -> None:
        """Initialize the data parser."""
        self.logger = logging.getLogger(__name__)

    def clean_json_content(self, content: str) -> str:
        """
        Clean JSON content to fix common formatting issues.

        Fixes:
        - Python-style numeric literals with underscores (e.g., 1_000_000 -> 1000000)
        - Trailing commas in arrays and objects
        - Multiple consecutive commas

        Args:
            content: Raw JSON content string

        Returns:
            Cleaned JSON content string

        """
        # Remove underscores from numeric literals
        # Match numbers with underscores: 1_000_000, 20_000_000_000, etc.
        content = re.sub(r"(\d)_(\d)", r"\1\2", content)

        # Remove trailing commas before closing brackets/braces
        # Fix: ,] -> ]
        content = re.sub(r",\s*]", "]", content)
        # Fix: ,} -> }
        content = re.sub(r",\s*}", "}", content)

        # Remove multiple consecutive commas
        # Fix: ,, -> ,
        content = re.sub(r",\s*,", ",", content)

        # Remove stray characters after closing braces/brackets
        # Fix: }% -> }, ]% -> ]
        content = re.sub(r"([}\]])\s*[^,\s}\]]+\s*$", r"\1", content, flags=re.MULTILINE)

        # Fix incomplete JSON - add missing closing braces/brackets
        open_braces = content.count("{")
        close_braces = content.count("}")
        open_brackets = content.count("[")
        close_brackets = content.count("]")

        # Add missing closing braces
        if open_braces > close_braces:
            content = content.rstrip() + "\n" + ("}" * (open_braces - close_braces))

        # Add missing closing brackets
        if open_brackets > close_brackets:
            content = content.rstrip() + "\n" + ("]" * (open_brackets - close_brackets))

        return content

    def load_and_parse_json(self, file_path: Path, asset_type: str) -> list[dict[str, Any]]:
        """
        Load and parse JSON file with comprehensive error handling.

        This helper method consolidates duplicate JSON parsing logic across
        stock, ETF, and crypto extraction methods.

        Args:
            file_path: Path to the JSON file to load
            asset_type: Type of asset for logging (stock, etf, crypto)

        Returns:
            List of candidate dictionaries, or empty list if file missing/invalid

        """
        # Check if file exists
        if not file_path.exists():
            self.logger.warning(f"{asset_type.capitalize()} A+ file not found: {file_path}")
            return []

        try:
            # Read file content
            content = file_path.read_text(encoding="utf-8")

            # Check if file is empty
            if not content or content.strip() == "":
                self.logger.warning(f"{asset_type.capitalize()} A+ file is empty: {file_path}")
                return []

            # Clean JSON content (fix Python-style numeric literals, trailing commas, etc.)
            content = self.clean_json_content(content)

            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                # Log the problematic area for debugging
                lines = content.split("\n")
                error_line = e.lineno - 1 if e.lineno <= len(lines) else len(lines) - 1
                context_start = max(0, error_line - 2)
                context_end = min(len(lines), error_line + 3)
                context = "\n".join(f"{i + 1}: {lines[i]}" for i in range(context_start, context_end))
                self.logger.error(f"JSON parsing error in {file_path.name} at line {e.lineno}, column {e.colno}:\n{context}")
                raise

            # Handle different data structures
            candidates: list[Any]
            # Case 1: data is already a list of candidates
            if isinstance(data, list):
                candidates = data
            # Case 2: data is a dict with "candidates" or "a_plus_candidates" key
            elif isinstance(data, dict):
                candidates = data.get("candidates") or data.get("a_plus_candidates") or []
            else:
                self.logger.error(f"Unexpected data type in {file_path.name}: {type(data)}")
                return []

            # Unwrap nested "candidate" objects if present
            # Some data formats have: [{"candidate": {...}, "composite_score": ...}, ...]
            # We need to merge the wrapper fields with the inner candidate object
            unwrapped_candidates = []
            for item in candidates:
                if isinstance(item, dict) and "candidate" in item:
                    # Nested structure - merge wrapper fields with inner candidate
                    inner_candidate = item["candidate"].copy()
                    # Add wrapper-level fields to the candidate (if not already present)
                    for key, value in item.items():
                        if key != "candidate" and key not in inner_candidate:
                            inner_candidate[key] = value
                    unwrapped_candidates.append(inner_candidate)
                else:
                    # Flat structure - use as is
                    unwrapped_candidates.append(item)

            return unwrapped_candidates

        except Exception as e:
            self.logger.error(f"Failed to load {asset_type} opportunities from {file_path}: {e!s}", exc_info=True)
            return []

    def extract_moat_info(self, moat_analysis: Any) -> tuple[str, str, list[str]]:
        """
        Extract moat information with guard clauses for different data types.

        Handles:
        - String type: Returns empty moat type/strength, uses string as rationale
        - Dict type: Extracts moat_type, moat_strength, builds rationale
        - Other types: Returns empty values

        Args:
            moat_analysis: Moat analysis data (string, dict, or other)

        Returns:
            Tuple of (moat_type, moat_strength, rationale_list)

        """
        # Guard: Handle None or empty
        if not moat_analysis:
            return "", "", []

        # Guard: Handle string type
        if isinstance(moat_analysis, str):
            return "", "", [moat_analysis]

        # Guard: Handle non-dict types
        if not isinstance(moat_analysis, dict):
            return "", "", []

        # Extract from dict
        moat_type = moat_analysis.get("moat_type", "")
        moat_strength = moat_analysis.get("moat_strength", "")
        rationale = [f"Moat: {moat_type}", f"Strength: {moat_strength}"] if moat_type else []

        return moat_type, moat_strength, rationale

    def extract_diversification_info(self, diversification: Any) -> tuple[int, float, list[str]]:
        """
        Extract diversification information with guard clauses for different data types.

        Handles:
        - String type: Returns zero values, uses string as rationale
        - Dict type: Extracts holdings_count, top_10_concentration, builds rationale
        - Other types: Returns zero values

        Args:
            diversification: Diversification data (string, dict, or other)

        Returns:
            Tuple of (holdings_count, top_10_concentration, rationale_list)

        """
        # Guard: Handle None
        if diversification is None:
            return 0, 0.0, []

        # Guard: Handle string type
        if isinstance(diversification, str):
            # Empty string should return empty rationale
            if not diversification:
                return 0, 0.0, []
            return 0, 0.0, [diversification]

        # Guard: Handle non-dict types
        if not isinstance(diversification, dict):
            return 0, 0.0, []

        # Extract from dict (even if empty, return rationale with zero values)
        holdings_count = diversification.get("holdings_count", 0)
        top_10_concentration = diversification.get("top_10_concentration_pct", 0.0)
        rationale = [f"Holdings: {holdings_count}", f"Top 10 concentration: {top_10_concentration}%"]

        return holdings_count, top_10_concentration, rationale

    def extract_technology_info(self, technology: Any) -> tuple[str, str, list[str]]:
        """
        Extract technology information with guard clauses for different data types.

        Handles:
        - String type: Returns empty values, uses string as rationale
        - Dict type: Extracts consensus_mechanism, use_case, builds rationale
        - Other types: Returns empty values

        Args:
            technology: Technology data (string, dict, or other)

        Returns:
            Tuple of (consensus_mechanism, use_case, rationale_list)

        """
        # Guard: Handle None or empty
        if not technology:
            return "", "", []

        # Guard: Handle string type
        if isinstance(technology, str):
            return "", "", [technology]

        # Guard: Handle non-dict types
        if not isinstance(technology, dict):
            return "", "", []

        # Extract from dict
        consensus = technology.get("consensus_mechanism", "")
        use_case = technology.get("primary_use_case", "")
        rationale = [f"Consensus: {consensus}", f"Use case: {use_case}"] if consensus else []

        return consensus, use_case, rationale
