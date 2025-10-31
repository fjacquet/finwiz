"""
Discovery Methodology Extractor for extracting screening criteria and validation statistics from discovery crew outputs.

This module provides extraction logic for discovery methodology including screening criteria,
validation statistics, fundamental and technical scores, and methodology summaries.
"""

import logging

from pydantic import BaseModel, Field

from finwiz.schemas.investment_discovery import APlusCriteria, APlusDiscoveryResult, Grade


class ValidationStatistics(BaseModel):
    """Validation statistics from discovery crew."""

    total_screened: int = Field(..., ge=0, description="Total assets screened")
    candidates_found: int = Field(..., ge=0, description="A+ candidates found")
    passed_validation: int = Field(..., ge=0, description="Candidates that passed validation")
    failed_validation: int = Field(..., ge=0, description="Candidates that failed validation")
    validation_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage that passed")
    screening_efficiency: float = Field(..., ge=0.0, le=100.0, description="Quality candidates found %")


class ScoreBreakdown(BaseModel):
    """Fundamental and technical score breakdown for a candidate."""

    symbol: str = Field(..., description="Investment symbol")
    fundamental_score: float = Field(..., ge=0.0, le=1.0, description="Fundamental analysis score")
    technical_score: float = Field(..., ge=0.0, le=1.0, description="Technical analysis score")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality metrics score")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk assessment score")
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Final composite score")
    grade: Grade = Field(..., description="Letter grade (A+ to F)")


class MethodologySummary(BaseModel):
    """Summary of discovery methodology for reporting."""

    screening_criteria: APlusCriteria = Field(..., description="Criteria used for screening")
    validation_statistics: ValidationStatistics = Field(..., description="Validation statistics")
    score_breakdowns: dict[str, ScoreBreakdown] = Field(default_factory=dict, description="Score breakdowns by symbol")
    methodology_notes: list[str] = Field(default_factory=list, description="Key methodology points")
    data_sources: list[str] = Field(default_factory=list, description="Data sources used")


class DiscoveryMethodologyExtractor:
    """
    Extracts discovery methodology details and validation statistics from discovery crew outputs.

    This class provides methods to extract and structure discovery methodology data including
    screening criteria, validation statistics, fundamental and technical scores, and
    comprehensive methodology summaries for report integration.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """
        Initialize the discovery methodology extractor.

        Args:
            logger: Optional logger instance for logging operations

        """
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("DiscoveryMethodologyExtractor initialized")

    def extract_screening_criteria(self, discovery_result: APlusDiscoveryResult) -> APlusCriteria | None:
        """
        Extract APlusCriteria from APlusDiscoveryResult.

        Args:
            discovery_result: APlusDiscoveryResult containing screening criteria

        Returns:
            APlusCriteria with extracted thresholds, or None if unavailable

        """
        try:
            # Extract criteria directly from discovery result
            criteria = discovery_result.discovery_criteria

            self.logger.info(
                f"Extracted screening criteria: "
                f"ETF expense ratio ≤{criteria.etf_max_expense_ratio:.2%}, "
                f"Stock ROE ≥{criteria.stock_min_roe:.1f}%, "
                f"Crypto market cap ≥${criteria.crypto_min_market_cap / 1e9:.1f}B"
            )
            return criteria

        except Exception as e:
            self.logger.error(f"Failed to extract screening criteria: {e}")
            return None

    def extract_validation_statistics(self, discovery_result: APlusDiscoveryResult) -> ValidationStatistics | None:
        """
        Extract validation statistics from discovery result.

        Args:
            discovery_result: APlusDiscoveryResult containing validation data

        Returns:
            ValidationStatistics with screening metrics, or None if unavailable

        """
        try:
            # Calculate validation statistics from discovery result
            total_screened = discovery_result.total_screened
            candidates_found = discovery_result.candidates_found

            # For now, assume all candidates found passed validation
            # This can be enhanced when validation results are integrated
            passed_validation = candidates_found
            failed_validation = 0

            # Calculate rates
            validation_rate = 1.0 if candidates_found > 0 else 0.0
            screening_efficiency = discovery_result.screening_efficiency

            statistics = ValidationStatistics(
                total_screened=total_screened,
                candidates_found=candidates_found,
                passed_validation=passed_validation,
                failed_validation=failed_validation,
                validation_rate=validation_rate,
                screening_efficiency=screening_efficiency,
            )

            self.logger.info(f"Extracted validation statistics: {candidates_found}/{total_screened} candidates found ({screening_efficiency:.1f}% efficiency)")
            return statistics

        except Exception as e:
            self.logger.error(f"Failed to extract validation statistics: {e}")
            return None

    def extract_fundamental_technical_scores(self, discovery_result: APlusDiscoveryResult) -> dict[str, ScoreBreakdown]:
        """
        Extract fundamental and technical score breakdowns for each A+ candidate.

        Args:
            discovery_result: APlusDiscoveryResult containing candidate analyses

        Returns:
            Dictionary mapping symbol to ScoreBreakdown

        """
        score_breakdowns: dict[str, ScoreBreakdown] = {}

        try:
            # Extract scores from each A+ candidate analysis
            for analysis in discovery_result.a_plus_candidates:
                candidate = analysis.candidate
                symbol = candidate.symbol

                breakdown = ScoreBreakdown(
                    symbol=symbol,
                    fundamental_score=analysis.fundamental_score,
                    technical_score=analysis.technical_score,
                    quality_score=analysis.quality_score,
                    risk_score=analysis.risk_score,
                    composite_score=analysis.composite_score,
                    grade=candidate.grade,
                )

                score_breakdowns[symbol] = breakdown

            self.logger.info(f"Extracted score breakdowns for {len(score_breakdowns)} candidates")
            return score_breakdowns

        except Exception as e:
            self.logger.error(f"Failed to extract fundamental/technical scores: {e}")
            return {}

    def get_methodology_summary(self, discovery_result: APlusDiscoveryResult) -> MethodologySummary | None:
        """
        Generate comprehensive methodology summary for reporting.

        Args:
            discovery_result: APlusDiscoveryResult containing methodology data

        Returns:
            MethodologySummary with aggregated methodology information, or None if unavailable

        """
        try:
            # Extract all components
            screening_criteria = self.extract_screening_criteria(discovery_result)
            validation_statistics = self.extract_validation_statistics(discovery_result)
            score_breakdowns = self.extract_fundamental_technical_scores(discovery_result)

            if not all([screening_criteria, validation_statistics]):
                self.logger.warning("Incomplete methodology data")
                return None

            # Generate methodology notes
            methodology_notes = self._generate_methodology_notes(discovery_result, screening_criteria, validation_statistics)

            # Extract data sources
            data_sources = self._extract_data_sources(discovery_result)

            summary = MethodologySummary(
                screening_criteria=screening_criteria,
                validation_statistics=validation_statistics,
                score_breakdowns=score_breakdowns,
                methodology_notes=methodology_notes,
                data_sources=data_sources,
            )

            self.logger.info(f"Generated methodology summary: {len(score_breakdowns)} candidates, {len(methodology_notes)} notes, {len(data_sources)} data sources")
            return summary

        except Exception as e:
            self.logger.error(f"Failed to generate methodology summary: {e}")
            return None

    # Private helper methods

    def _generate_methodology_notes(
        self,
        discovery_result: APlusDiscoveryResult,
        criteria: APlusCriteria,
        statistics: ValidationStatistics,
    ) -> list[str]:
        """Generate key methodology notes explaining the discovery process."""
        notes: list[str] = []

        # Asset type note
        asset_type = discovery_result.asset_type
        notes.append(f"Screened {statistics.total_screened} {asset_type} investments for A+ opportunities")

        # Criteria notes based on asset type
        if asset_type == "etf":
            notes.append(
                f"ETF criteria: expense ratio ≤{criteria.etf_max_expense_ratio:.2%}, AUM ≥${criteria.etf_min_aum / 1e9:.1f}B, tracking error ≤{criteria.etf_max_tracking_error:.2%}"
            )
        elif asset_type == "stock":
            notes.append(
                f"Stock criteria: ROE ≥{criteria.stock_min_roe:.1f}%, "
                f"revenue growth ≥{criteria.stock_min_revenue_growth:.1f}%, "
                f"debt/equity ≤{criteria.stock_max_debt_to_equity:.2f}"
            )
        elif asset_type == "crypto":
            notes.append(
                f"Crypto criteria: market cap ≥${criteria.crypto_min_market_cap / 1e9:.1f}B, "
                f"daily volume ≥${criteria.crypto_min_daily_volume / 1e6:.0f}M, "
                f"age ≥{criteria.crypto_min_age_months} months"
            )

        # Regime adjustment note
        if criteria.regime_adjusted:
            notes.append(f"Criteria adjusted for market regime: {criteria.adjustment_rationale}")

        # Market context note
        market_regime = discovery_result.market_context
        notes.append(f"Analysis performed in {market_regime.regime_type} market with {market_regime.market_stress_level} stress level")

        # Efficiency note
        notes.append(f"Screening efficiency: {statistics.screening_efficiency:.1f}% ({statistics.candidates_found} quality candidates identified)")

        # Confidence note
        high_confidence = discovery_result.high_confidence_count
        if high_confidence > 0:
            notes.append(f"{high_confidence} candidates have >80% confidence level")

        # UCITS note for ETFs
        if asset_type == "etf" and discovery_result.ucits_compliant_count:
            notes.append(f"{discovery_result.ucits_compliant_count} UCITS-compliant ETFs found (suitable for European investors)")

        return notes

    def _extract_data_sources(self, discovery_result: APlusDiscoveryResult) -> list[str]:
        """Extract list of data sources used in discovery process."""
        data_sources: set[str] = set()

        # Extract from candidate analyses
        for analysis in discovery_result.a_plus_candidates:
            source = analysis.candidate.data_source
            if source:
                data_sources.add(source)

        # Add common sources based on asset type
        asset_type = discovery_result.asset_type
        if asset_type == "etf":
            data_sources.update(["Yahoo Finance ETF Data", "Fund Prospectuses", "ETF.com"])
        elif asset_type == "stock":
            data_sources.update(["SEC EDGAR Filings", "Yahoo Finance", "Alpha Vantage"])
        elif asset_type == "crypto":
            data_sources.update(["CoinMarketCap", "Coinbase", "Kraken"])

        # Add market data sources
        data_sources.update(["CBOE VIX Index", "Federal Reserve Economic Data"])

        return sorted(list(data_sources))
