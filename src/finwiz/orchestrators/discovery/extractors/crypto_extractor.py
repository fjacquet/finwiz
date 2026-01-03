"""
Crypto opportunity extractor implementation.

This module implements crypto-specific extraction logic for A+ investment opportunities.
"""

from typing import Any

from finwiz.orchestrators.discovery.extractors.base import OpportunityExtractor


class CryptoOpportunityExtractor(OpportunityExtractor):
    """Extract crypto opportunities with crypto-specific logic."""

    def _should_include(self, candidate: dict[str, Any]) -> bool:
        """
        Crypto-specific inclusion logic.

        Includes cryptocurrencies with:
        - Grade A+ or A
        - Valid symbol and name
        - Market cap >= $10B

        Args:
            candidate: Crypto candidate dictionary

        Returns:
            True if crypto should be included

        """
        grade = candidate.get("grade", "")
        if grade not in ["A+", "A"]:
            return False

        symbol = candidate.get("symbol", "")
        crypto_name = candidate.get("name", "")

        if not (symbol and crypto_name):
            return False

        # Check market cap threshold
        # Try market_cap_usd first, then market_cap (for test data compatibility)
        market_cap = candidate.get("market_cap_usd", candidate.get("market_cap", 0))

        return bool(market_cap >= 10_000_000_000)  # $10B minimum

    def _build_opportunity(self, candidate: dict[str, Any], idx: int) -> dict[str, Any] | None:
        """
        Build crypto opportunity object.

        Extracts:
        - Market metrics (market cap, volume)
        - Composite score calculation
        - Technology as rationale
        - Risk assessment

        Args:
            candidate: Crypto candidate dictionary
            idx: Index for ranking

        Returns:
            Crypto opportunity dictionary

        """
        try:
            symbol = candidate.get("symbol", "")
            crypto_name = candidate.get("name", "")
            grade = candidate.get("grade", "")

            # Use pre-calculated composite score if available, otherwise calculate from market metrics
            if "composite_score" in candidate:
                composite_score = candidate.get("composite_score", 0.0)
            else:
                # Extract market metrics for composite score calculation
                market_cap = candidate.get("market_cap_usd", 0)
                volume_24h = candidate.get("volume_24h_usd", 0)
                # Calculate composite score from market metrics
                # Higher market cap and volume = higher score
                market_cap_score = min(market_cap / 100e9, 1.0)  # Normalize to $100B
                volume_score = min(volume_24h / 10e9, 1.0)  # Normalize to $10B daily volume
                composite_score = (market_cap_score * 0.6 + volume_score * 0.4) * 0.9  # Max 0.9 for crypto

            # Use pre-calculated confidence if available
            if "confidence_level" in candidate:
                confidence = candidate.get("confidence_level", 0.85)
            else:
                confidence = 0.85 if grade == "A+" else 0.75

            # Extract market metrics for key metrics (may not exist in all data formats)
            market_cap = candidate.get("market_cap_usd", 0)
            volume_24h = candidate.get("volume_24h_usd", 0)

            # Extract risk assessment
            risk_assessment = candidate.get("risk_assessment") or {}
            risk_score = risk_assessment.get("score", 6.0)  # Crypto typically higher risk

            # Extract technology as rationale using helper method
            from finwiz.orchestrators.extraction.aplus import APlusDataExtractor

            extractor = APlusDataExtractor()
            technology = candidate.get("technology", {})
            consensus, use_case, rationale = extractor._extract_technology_info(technology)

            # Build key metrics
            key_metrics = {
                "market_cap_usd": market_cap,
                "volume_24h_usd": volume_24h,
                "consensus_mechanism": consensus,
            }

            # Return dict matching APlusOpportunity schema
            return {
                "symbol": symbol.replace("-USD", ""),  # Clean symbol
                "name": crypto_name,
                "grade": grade,
                "composite_score": composite_score,
                "confidence": confidence,
                "risk_score": risk_score,
                "allocation_recommendation": technology.get("competitive_advantage", "") if isinstance(technology, dict) else "",
                "replacement_note": candidate.get("implementation", {}).get("entry_strategy", ""),
                "rationale": rationale,
                "key_metrics": key_metrics,
            }

        except Exception as e:
            self.logger.error(f"Failed to build crypto opportunity: {str(e)}", exc_info=True)
            return None
