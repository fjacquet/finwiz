"""
Stock opportunity extractor implementation.

This module implements stock-specific extraction logic for A+ investment opportunities.
"""

from typing import Any

from finwiz.integration.opportunity_extractors.base import OpportunityExtractor


class StockOpportunityExtractor(OpportunityExtractor):
    """Extract stock opportunities with stock-specific logic."""

    def _should_include(self, candidate: dict[str, Any]) -> bool:
        """
        Stock-specific inclusion logic.

        Includes stocks with:
        - Grade A+ or A
        - Valid symbol and name

        Args:
            candidate: Stock candidate dictionary

        Returns:
            True if stock should be included

        """
        grade = candidate.get("grade", "")
        if grade not in ["A+", "A"]:
            return False

        symbol = candidate.get("symbol", "")
        company_name = candidate.get("name", "")

        return bool(symbol and company_name)

    def _build_opportunity(self, candidate: dict[str, Any], idx: int) -> dict[str, Any] | None:
        """
        Build stock opportunity object.

        Extracts:
        - Fundamental metrics (ROE, revenue growth, debt ratio)
        - Composite score calculation
        - Moat analysis as rationale
        - Risk assessment

        Args:
            candidate: Stock candidate dictionary
            idx: Index for ranking

        Returns:
            Stock opportunity dictionary

        """
        try:
            symbol = candidate.get("symbol", "")
            company_name = candidate.get("name", "")
            grade = candidate.get("grade", "")

            # Use pre-calculated composite score if available, otherwise calculate from fundamentals
            if "composite_score" in candidate:
                composite_score = candidate.get("composite_score", 0.0)
            else:
                # Extract fundamentals for composite score calculation
                fundamentals = candidate.get("fundamentals", {})
                roe = fundamentals.get("roe_3y_avg", 0)
                revenue_growth = fundamentals.get("revenue_cagr_5y", 0)
                debt_ratio = fundamentals.get("debt_to_equity", 0)
                # Calculate composite score from fundamentals
                composite_score = min((roe / 20 * 0.4) + (revenue_growth / 15 * 0.4) + ((1 - min(debt_ratio, 1)) * 0.2), 1.0)

            # Use pre-calculated confidence if available
            if "confidence_level" in candidate:
                confidence = candidate.get("confidence_level", 0.85)
            else:
                confidence = 0.85 if grade == "A+" else 0.75

            # Extract fundamentals for key metrics (may not exist in all data formats)
            fundamentals = candidate.get("fundamentals", {})
            roe = fundamentals.get("roe_3y_avg", 0)
            revenue_growth = fundamentals.get("revenue_cagr_5y", 0)
            debt_ratio = fundamentals.get("debt_to_equity", 0)

            # Extract risk assessment
            risk_assessment = candidate.get("risk_assessment") or {}
            risk_score = risk_assessment.get("score", 5.0)

            # Extract moat analysis as rationale using helper method
            from finwiz.integration.aplus_extractor import APlusDataExtractor

            extractor = APlusDataExtractor()
            moat_analysis = candidate.get("moat_analysis", {})
            moat_type, moat_strength, rationale = extractor._extract_moat_info(moat_analysis)

            # Extract key metrics from fundamentals
            key_metrics = {
                "roe_3y_avg": roe,
                "revenue_cagr_5y": revenue_growth,
                "debt_to_equity": debt_ratio,
                "market_cap_usd": candidate.get("market_cap_usd", 0),
            }

            # Return dict matching APlusOpportunity schema
            return {
                "symbol": symbol,
                "name": company_name,
                "grade": grade,
                "composite_score": composite_score,
                "confidence": confidence,
                "risk_score": risk_score,
                "allocation_recommendation": moat_analysis.get("competitive_advantage", "") if isinstance(moat_analysis, dict) else "",
                "replacement_note": candidate.get("implementation", {}).get("entry_strategy", ""),
                "rationale": rationale,
                "key_metrics": key_metrics,
            }

        except Exception as e:
            self.logger.error(f"Failed to build stock opportunity: {str(e)}", exc_info=True)
            return None
