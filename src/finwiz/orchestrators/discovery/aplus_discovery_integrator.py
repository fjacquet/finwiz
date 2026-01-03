#!/usr/bin/env python
"""
A+ Discovery Integrator - Integrates A+ discovery with deep analysis results.

This module fixes the "0 opportunities found" issue by properly reading
deep analysis JSON exports and identifying A+ holdings.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def integrate_aplus_discovery_with_deep_analysis(session_id: str) -> dict[str, Any]:
    """
    Integrate A+ discovery with deep analysis results.

    This fixes Requirements 0.13-0.17: A+ discovery integration with deep analysis results.

    Args:
        session_id: Session identifier for finding analysis files

    Returns:
        Dictionary containing discovery integration results

    """
    logger.info("🔍 Integrating A+ discovery with deep analysis results")

    try:
        # Look for deep analysis JSON exports in output directories
        output_dirs = [Path("output/stock"), Path("output/etf"), Path("output/crypto")]

        aplus_holdings = []
        total_analyzed = 0

        # Scan each output directory for analysis results
        for output_dir in output_dirs:
            if not output_dir.exists():
                logger.debug(f"Output directory does not exist: {output_dir}")
                continue

            # Find JSON files for this session
            json_files = list(output_dir.glob(f"*_{session_id}.json"))
            logger.debug(f"Found {len(json_files)} analysis files in {output_dir}")

            for json_file in json_files:
                try:
                    # Load analysis result
                    with open(json_file, encoding="utf-8") as f:
                        analysis_data = json.load(f)

                    total_analyzed += 1

                    # Check if this is an A+ or A grade holding
                    grade = analysis_data.get("grade", "")
                    ticker = analysis_data.get("ticker", "")

                    if grade in ["A+", "A"]:
                        aplus_holdings.append(
                            {
                                "ticker": ticker,
                                "grade": grade,
                                "composite_score": analysis_data.get("composite_score", 0.0),
                                "asset_class": analysis_data.get("asset_class", ""),
                                "recommendation": analysis_data.get("recommendation", ""),
                                "analysis_file": str(json_file),
                            }
                        )
                        logger.info(f"   Found A+ opportunity: {ticker} (Grade: {grade})")

                except Exception as e:
                    logger.warning(f"Failed to process analysis file {json_file}: {e}")
                    continue

        # Also check consolidated export
        consolidated_path = Path(f"output/deep_analysis_consolidated_{session_id}.json")
        if consolidated_path.exists():
            try:
                with open(consolidated_path, encoding="utf-8") as f:
                    consolidated_data = json.load(f)

                # Extract A+ opportunities from consolidated data
                for ticker, analysis in consolidated_data.items():
                    if isinstance(analysis, dict):
                        grade = analysis.get("grade", "")
                        if grade in ["A+", "A"] and ticker not in [h["ticker"] for h in aplus_holdings]:
                            aplus_holdings.append(
                                {
                                    "ticker": ticker,
                                    "grade": grade,
                                    "composite_score": analysis.get("composite_score", 0.0),
                                    "asset_class": analysis.get("asset_class", ""),
                                    "recommendation": analysis.get("recommendation", ""),
                                    "analysis_file": str(consolidated_path),
                                }
                            )

            except Exception as e:
                logger.warning(f"Failed to process consolidated file {consolidated_path}: {e}")

        # Determine if we have A+ analysis
        has_aplus_analysis = len(aplus_holdings) > 0
        total_opportunities = len(aplus_holdings)

        results = {
            "has_a_plus_analysis": has_aplus_analysis,
            "total_opportunities_found": total_opportunities,
            "aplus_holdings": aplus_holdings,
            "total_analyzed": total_analyzed,
            "session_id": session_id,
            "integration_timestamp": datetime.now().isoformat(),
        }

        if has_aplus_analysis:
            logger.info(f"✅ A+ Discovery Integration: Found {total_opportunities} A+ opportunities")
            for holding in aplus_holdings:
                logger.info(f"   - {holding['ticker']}: Grade {holding['grade']} ({holding['asset_class']})")
        else:
            logger.info("ℹ️ A+ Discovery Integration: No A+ opportunities found")

        return results

    except Exception as e:
        logger.error(f"A+ discovery integration failed: {e}")
        return {
            "has_a_plus_analysis": False,
            "total_opportunities_found": 0,
            "aplus_holdings": [],
            "total_analyzed": 0,
            "session_id": session_id,
            "integration_timestamp": datetime.now().isoformat(),
            "error": str(e),
        }
