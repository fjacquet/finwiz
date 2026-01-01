"""Crew Export Generator for Deep Analysis.

Handles creation of crew export formats and detailed analysis structures.
Extracted from deep_analysis_scorer.py for single responsibility.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, cast

from finwiz.flow_state import DeepAnalysisResult
from finwiz.schemas.common import RiskLevel
from finwiz.scoring.scoring_thresholds import ScoringThresholds, get_thresholds

logger = logging.getLogger(__name__)


class CrewExportGenerator:
    """Generates crew export format and detailed analysis structures."""

    def __init__(self, thresholds: ScoringThresholds | None = None) -> None:
        """Initialize with scoring thresholds."""
        self.thresholds = thresholds or get_thresholds()
        self.logger = logger

    def create_crew_export(
        self,
        result: DeepAnalysisResult,
        detailed_analysis: dict[str, Any],
        session_id: str = "default",
    ) -> dict[str, Any]:
        """
        Create DeepAnalysisCrewExport dict from DeepAnalysisResult.

        Args:
            result: DeepAnalysisResult from scoring
            detailed_analysis: Comprehensive analysis dict
            session_id: Session identifier for file paths

        Returns:
            Dict ready for DeepAnalysisCrewExport validation
        """
        from finwiz.schemas.common import RiskAssessmentStandardized

        # Create risk assessment from result data
        # Handle None risk_score with default of 0.5 (mid-range risk)
        risk_score = result.risk_score if result.risk_score is not None else 0.5
        risk_assessment = RiskAssessmentStandardized(
            score=float((1.0 - risk_score) * 5),
            level=cast(RiskLevel, self._map_risk_level(risk_score)),
            risk_factors=self._extract_risk_factors(result.risk_details),
        )

        # Determine data sources based on asset class
        data_sources = self._determine_data_sources(result.asset_class, detailed_analysis)

        return {
            "crew_name": "deep_analysis_crew",
            "ticker": result.ticker,
            "asset_class": result.asset_class,
            "analysis_date": datetime.now(),
            "session_id": session_id,
            # Analysis results
            "detailed_analysis": detailed_analysis,
            "risk_assessment": risk_assessment,
            # Scores and grades
            "composite_score": result.composite_score,
            "grade": result.grade,
            # Recommendations
            "recommendation": result.recommendation,
            "confidence": result.confidence,
            "rationale": result.rationale,
            # Metadata
            "data_sources": data_sources,
            "report_html_path": f"output/reports/{session_id}/deep_analysis_crew/{result.ticker}_report.html",
            "report_json_path": f"output/reports/{session_id}/deep_analysis_crew/{result.ticker}_export.json",
        }

    def create_detailed_analysis(
        self,
        ticker: str,
        asset_class: str,
        data: dict[str, Any],
        result: DeepAnalysisResult,
    ) -> dict[str, Any]:
        """
        Create comprehensive detailed_analysis dict preserving ALL raw data.

        Requirements 18.21-18.25: Preserve all raw metrics, sentiment data,
        technical indicators, fundamental data, and calculation results.

        Args:
            ticker: Asset ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            data: Raw collected data from tools
            result: DeepAnalysisResult with calculated scores

        Returns:
            Comprehensive dict with all preserved data
        """
        return {
            # Basic information
            "ticker": ticker,
            "asset_class": asset_class,
            "analysis_timestamp": data.get("collection_timestamp", ""),
            # Raw metrics preservation (Requirement 18.21)
            "raw_metrics": self._extract_raw_metrics(data),
            # Asset-specific raw metrics
            "asset_specific_metrics": self._extract_asset_specific_metrics(asset_class, data),
            # Sentiment data preservation (Requirement 18.22)
            "sentiment_data": self._extract_sentiment_data(data),
            # Technical indicators preservation (Requirement 18.23)
            "technical_indicators": self._extract_technical_indicators(data, result),
            # Fundamental data preservation (Requirement 18.24)
            "fundamental_data": self._extract_fundamental_data(asset_class, data),
            # Calculation results preservation (Requirement 18.25)
            "calculation_results": self._extract_calculation_results(result),
            # Additional context
            "data_quality": {
                "missing_fields": self._identify_missing_fields(data),
                "data_freshness": data.get("data_freshness", {}),
                "source_reliability": data.get("source_reliability", {}),
            },
            # Raw tool outputs (preserve everything)
            "raw_tool_outputs": {
                "ticker_validation": data.get("ticker_validation", {}),
                "quantitative_analysis": data.get("quantitative_analysis", {}),
                "sentiment_analysis": data.get("sentiment_analysis", {}),
                "sec_analysis": data.get("sec_analysis", {}),
                "etf_analysis": data.get("etf_analysis", {}),
                "crypto_analysis": data.get("crypto_analysis", {}),
            },
        }

    def _extract_raw_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract raw metrics from data."""
        return {
            "volatility": self._safe_get_float(data, "volatility", 0.0),
            "beta": self._safe_get_float(data, "beta", 1.0),
            "max_drawdown": self._safe_get_float(data, "max_drawdown", -0.20),
            "sharpe_ratio": self._safe_get_float(data, "sharpe_ratio", 0.0),
            "current_price": self._safe_get_float(data, "current_price", 0.0),
            "moving_avg_50": self._safe_get_float(data, "moving_avg_50", 0.0),
            "moving_avg_200": self._safe_get_float(data, "moving_avg_200", 0.0),
            "rsi": self._safe_get_float(data, "rsi", 50.0),
            "macd": self._safe_get_float(data, "macd", 0.0),
            "macd_signal": self._safe_get_float(data, "macd_signal", 0.0),
        }

    def _extract_sentiment_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract sentiment data from data."""
        return {
            "sentiment_score": self._safe_get_float(data, "sentiment_score", 0.0),
            "trending_topics": data.get("trending_topics", []),
            "article_count": data.get("article_count", 0),
            "news_sources": data.get("news_sources", []),
            "sentiment_breakdown": data.get("sentiment_breakdown", {}),
            "social_sentiment": data.get("social_sentiment", {}),
        }

    def _extract_technical_indicators(self, data: dict[str, Any], result: DeepAnalysisResult) -> dict[str, Any]:
        """Extract technical indicators from data."""
        return {
            "rsi": self._safe_get_float(data, "rsi", 50.0),
            "macd": self._safe_get_float(data, "macd", 0.0),
            "macd_signal": self._safe_get_float(data, "macd_signal", 0.0),
            "macd_histogram": self._safe_get_float(data, "macd_histogram", 0.0),
            "bollinger_upper": self._safe_get_float(data, "bollinger_upper", 0.0),
            "bollinger_lower": self._safe_get_float(data, "bollinger_lower", 0.0),
            "bollinger_middle": self._safe_get_float(data, "bollinger_middle", 0.0),
            "support_levels": data.get("support_levels", []),
            "resistance_levels": data.get("resistance_levels", []),
            "trend_direction": result.technical_details.get("trend_direction", "sideways"),
            "momentum_indicators": data.get("momentum_indicators", {}),
            "volume_indicators": data.get("volume_indicators", {}),
        }

    def _extract_calculation_results(self, result: DeepAnalysisResult) -> dict[str, Any]:
        """Extract calculation results from DeepAnalysisResult."""
        return {
            "composite_score": result.composite_score,
            "fundamental_score": result.fundamental_score,
            "technical_score": result.technical_score,
            "risk_score": result.risk_score,
            "grade": result.grade,
            "recommendation": result.recommendation,
            "confidence": result.confidence,
            "rationale": result.rationale,
            # Component details
            "fundamental_details": result.fundamental_details,
            "technical_details": result.technical_details,
            "risk_details": result.risk_details,
        }

    def _extract_asset_specific_metrics(self, asset_class: str, data: dict[str, Any]) -> dict[str, Any]:
        """Extract asset-specific metrics based on asset class."""
        if asset_class == "stock":
            return {
                "roe": self._safe_get_float(data, "roe", 0.0),
                "debt_to_equity": self._safe_get_float(data, "debt_to_equity", 1.0),
                "revenue_growth": self._safe_get_float(data, "revenue_growth", 0.0),
                "profit_margin": self._safe_get_float(data, "profit_margin", 0.0),
                "earnings_per_share": self._safe_get_float(data, "earnings_per_share", 0.0),
                "price_to_earnings": self._safe_get_float(data, "price_to_earnings", 0.0),
                "price_to_book": self._safe_get_float(data, "price_to_book", 0.0),
                "free_cash_flow": self._safe_get_float(data, "free_cash_flow", 0.0),
                "current_ratio": self._safe_get_float(data, "current_ratio", 1.0),
                "quick_ratio": self._safe_get_float(data, "quick_ratio", 1.0),
            }
        elif asset_class == "etf":
            return {
                "expense_ratio": self._safe_get_float(data, "expense_ratio", 1.0),
                "tracking_error": self._safe_get_float(data, "tracking_error", 1.0),
                "aum": self._safe_get_float(data, "aum", 0.0),
                "dividend_yield": self._safe_get_float(data, "dividend_yield", 0.0),
                "top_holdings": data.get("top_holdings", []),
                "sector_allocation": data.get("sector_allocation", {}),
                "geographic_allocation": data.get("geographic_allocation", {}),
            }
        elif asset_class == "crypto":
            return {
                "market_cap": self._safe_get_float(data, "market_cap", 0.0),
                "volume_24h": self._safe_get_float(data, "volume_24h", 0.0),
                "age_years": self._safe_get_float(data, "age_years", 0.0),
                "circulating_supply": self._safe_get_float(data, "circulating_supply", 0.0),
                "max_supply": self._safe_get_float(data, "max_supply", 0.0),
                "total_supply": self._safe_get_float(data, "total_supply", 0.0),
                "market_cap_rank": data.get("market_cap_rank", 0),
                "all_time_high": self._safe_get_float(data, "all_time_high", 0.0),
                "all_time_low": self._safe_get_float(data, "all_time_low", 0.0),
            }
        return {}

    def _extract_fundamental_data(self, asset_class: str, data: dict[str, Any]) -> dict[str, Any]:
        """Extract fundamental data based on asset class."""
        base_data = {
            "revenue": self._safe_get_float(data, "revenue", 0.0),
            "earnings": self._safe_get_float(data, "earnings", 0.0),
            "cash_flow": self._safe_get_float(data, "cash_flow", 0.0),
            "total_assets": self._safe_get_float(data, "total_assets", 0.0),
            "total_liabilities": self._safe_get_float(data, "total_liabilities", 0.0),
            "shareholders_equity": self._safe_get_float(data, "shareholders_equity", 0.0),
        }

        # Add asset-specific fundamental data
        if asset_class == "stock":
            base_data.update(
                {
                    "sec_filings": data.get("sec_filings", {}),
                    "financial_statements": data.get("financial_statements", {}),
                    "business_description": data.get("business_description", ""),
                    "risk_factors": data.get("risk_factors", []),
                    "competitive_advantages": data.get("competitive_advantages", []),
                }
            )
        elif asset_class == "etf":
            base_data.update(
                {
                    "fund_objective": data.get("fund_objective", ""),
                    "benchmark_index": data.get("benchmark_index", ""),
                    "fund_family": data.get("fund_family", ""),
                    "inception_date": data.get("inception_date", ""),
                    "holdings_count": data.get("holdings_count", 0),
                }
            )
        elif asset_class == "crypto":
            base_data.update(
                {
                    "whitepaper_url": data.get("whitepaper_url", ""),
                    "consensus_mechanism": data.get("consensus_mechanism", ""),
                    "use_cases": data.get("use_cases", []),
                    "development_activity": data.get("development_activity", {}),
                    "community_metrics": data.get("community_metrics", {}),
                }
            )

        return base_data

    def _identify_missing_fields(self, data: dict[str, Any]) -> list[str]:
        """Identify missing or null fields in the data."""
        key_fields = [
            "current_price",
            "volatility",
            "rsi",
            "macd",
            "beta",
            "sentiment_score",
            "volume_24h" if "crypto" in str(data.get("asset_class", "")) else "volume",
        ]
        return [field for field in key_fields if field not in data or data[field] is None]

    def _map_risk_level(self, risk_score: float) -> str:
        """Map risk score (0-1, where 1=low risk) to risk level."""
        # Convert to 0-5 scale where 5=high risk
        risk_5_scale = (1.0 - risk_score) * 5

        if risk_5_scale <= self.thresholds.risk_low_threshold:
            return "Low"
        elif risk_5_scale <= self.thresholds.risk_medium_threshold:
            return "Medium"
        elif risk_5_scale <= self.thresholds.risk_high_threshold:
            return "High"
        else:
            return "Very High"

    def _extract_risk_factors(self, risk_details: dict[str, Any]) -> list[str]:
        """Extract risk factors from risk analysis details."""
        risk_factors = []

        volatility = risk_details.get("volatility", 0.20)
        if volatility > self.thresholds.risk_volatility_high:
            risk_factors.append(f"High volatility ({volatility:.1%})")

        max_drawdown = risk_details.get("max_drawdown", -0.20)
        if max_drawdown < -self.thresholds.risk_drawdown_significant:
            risk_factors.append(f"Significant drawdown risk ({max_drawdown:.1%})")

        beta = risk_details.get("beta", 1.0)
        if beta > self.thresholds.risk_beta_high:
            risk_factors.append(f"High market sensitivity (beta: {beta:.2f})")
        elif beta < self.thresholds.risk_beta_low:
            risk_factors.append(f"Low market correlation (beta: {beta:.2f})")

        return risk_factors[:10]

    def _determine_data_sources(self, asset_class: str, detailed_analysis: dict[str, Any]) -> list[str]:
        """Determine data sources used based on asset class and available data."""
        sources = ["Yahoo Finance API"]

        if asset_class == "stock":
            sources.extend(["SEC EDGAR Database", "Alpha Vantage API"])
        elif asset_class == "etf":
            sources.extend(["ETF.com", "Morningstar"])
        elif asset_class == "crypto":
            sources.extend(["CoinMarketCap API", "CoinGecko API"])

        # Add sources based on available data
        raw_outputs = detailed_analysis.get("raw_tool_outputs", {})
        if raw_outputs.get("sentiment_analysis"):
            sources.append("News Sentiment Analysis")
        if raw_outputs.get("quantitative_analysis"):
            sources.append("TwelveData API")

        return list(set(sources))

    @staticmethod
    def _safe_get_float(data: dict[str, Any], key: str, default: float) -> float:
        """Safely extract float value from data dictionary."""
        try:
            value = data.get(key)
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
