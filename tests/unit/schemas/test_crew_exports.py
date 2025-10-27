"""
Unit tests for Crew Export Pydantic schemas.

Tests validation for all CrewExport schemas with strict validation (extra='forbid').
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from finwiz.schemas.crew_exports import (
    ConsolidatedReportExport,
    CryptoCrewExport,
    DiscoveryCrewExport,
    ETFCrewExport,
    StockCrewExport,
)


class TestStockCrewExport:
    """Test StockCrewExport schema validation."""

    def test_should_validate_valid_stock_export(self):
        """Test validation of valid stock export data."""
        # Arrange
        valid_data = {
            "crew_name": "stock_crew",
            "ticker": "AAPL",
            "asset_class": "stock",
            "session_id": "test-session",
            "analysis_date": datetime.now().isoformat(),
            "fundamental_analysis": {
                "ticker": "AAPL",
                "filing_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193",
                "filed_at": datetime.now(UTC).isoformat(),
                "section": "Item 1A",
                "excerpt": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
                "sec_citation": "10-K (2024), Item 1A, p. 17",
            },
            "risk_assessment": {
                "score": 3.5,
                "level": "Medium",
                "risk_factors": ["Market risk"],
            },
            "technical_indicators": {"rsi": 65},
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Strong fundamentals with excellent growth prospects and solid balance sheet.",
            "data_sources": ["Yahoo Finance"],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act
        export = StockCrewExport(**valid_data)

        # Assert
        assert export.ticker == "AAPL"
        assert export.grade == "A"
        assert export.composite_score == 0.85

    def test_should_reject_invalid_grade(self):
        """Test rejection of invalid grade values."""
        # Arrange
        invalid_data = {
            "crew_name": "stock_crew",
            "ticker": "AAPL",
            "asset_class": "stock",
            "session_id": "test",
            "fundamental_analysis": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "key_insights": [],
                "financial_metrics": {},
                "competitive_position": "Strong",
                "growth_prospects": "Good",
                "management_quality": "Excellent",
                "data_sources": [],
            },
            "risk_assessment": {
                "overall_risk_score": 3.0,
                "risk_factors": [],
                "systematic_risk": 3.0,
                "idiosyncratic_risk": 3.0,
            },
            "composite_score": 0.85,
            "grade": "INVALID_GRADE",  # Invalid
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Strong fundamentals with excellent growth prospects.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            StockCrewExport(**invalid_data)

        assert "grade" in str(exc_info.value)

    def test_should_reject_out_of_range_composite_score(self):
        """Test rejection of composite scores outside [0.0, 1.0] range."""
        # Arrange
        invalid_data = {
            "crew_name": "stock_crew",
            "ticker": "AAPL",
            "asset_class": "stock",
            "session_id": "test",
            "fundamental_analysis": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "key_insights": [],
                "financial_metrics": {},
                "competitive_position": "Strong",
                "growth_prospects": "Good",
                "management_quality": "Excellent",
                "data_sources": [],
            },
            "risk_assessment": {
                "overall_risk_score": 3.0,
                "risk_factors": [],
                "systematic_risk": 3.0,
                "idiosyncratic_risk": 3.0,
            },
            "composite_score": 1.5,  # Invalid: > 1.0
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Strong fundamentals with excellent growth prospects.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            StockCrewExport(**invalid_data)

        assert "composite_score" in str(exc_info.value)

    def test_should_reject_invalid_recommendation(self):
        """Test rejection of invalid recommendation values."""
        # Arrange
        invalid_data = {
            "crew_name": "stock_crew",
            "ticker": "AAPL",
            "asset_class": "stock",
            "session_id": "test",
            "fundamental_analysis": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "key_insights": [],
                "financial_metrics": {},
                "competitive_position": "Strong",
                "growth_prospects": "Good",
                "management_quality": "Excellent",
                "data_sources": [],
            },
            "risk_assessment": {
                "overall_risk_score": 3.0,
                "risk_factors": [],
                "systematic_risk": 3.0,
                "idiosyncratic_risk": 3.0,
            },
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "MAYBE",  # Invalid
            "confidence": 0.90,
            "rationale": "Strong fundamentals with excellent growth prospects.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            StockCrewExport(**invalid_data)

        assert "recommendation" in str(exc_info.value)

    def test_should_enforce_extra_forbid(self):
        """Test that extra='forbid' rejects unknown fields."""
        # Arrange
        invalid_data = {
            "crew_name": "stock_crew",
            "ticker": "AAPL",
            "asset_class": "stock",
            "session_id": "test",
            "fundamental_analysis": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "key_insights": [],
                "financial_metrics": {},
                "competitive_position": "Strong",
                "growth_prospects": "Good",
                "management_quality": "Excellent",
                "data_sources": [],
            },
            "risk_assessment": {
                "overall_risk_score": 3.0,
                "risk_factors": [],
                "systematic_risk": 3.0,
                "idiosyncratic_risk": 3.0,
            },
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Strong fundamentals with excellent growth prospects.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
            "unknown_field": "should be rejected",  # Extra field
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            StockCrewExport(**invalid_data)

        assert "extra" in str(exc_info.value).lower() or "unknown_field" in str(exc_info.value)

    def test_should_reject_short_rationale(self):
        """Test rejection of rationale shorter than 50 characters."""
        # Arrange
        invalid_data = {
            "crew_name": "stock_crew",
            "ticker": "AAPL",
            "asset_class": "stock",
            "session_id": "test",
            "fundamental_analysis": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "key_insights": [],
                "financial_metrics": {},
                "competitive_position": "Strong",
                "growth_prospects": "Good",
                "management_quality": "Excellent",
                "data_sources": [],
            },
            "risk_assessment": {
                "overall_risk_score": 3.0,
                "risk_factors": [],
                "systematic_risk": 3.0,
                "idiosyncratic_risk": 3.0,
            },
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Too short",  # < 50 characters
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            StockCrewExport(**invalid_data)

        assert "rationale" in str(exc_info.value)


class TestETFCrewExport:
    """Test ETFCrewExport schema validation."""

    def test_should_validate_valid_etf_export(self):
        """Test validation of valid ETF export data."""
        # Arrange
        valid_data = {
            "crew_name": "etf_crew",
            "ticker": "SPY",
            "asset_class": "etf",
            "session_id": "test",
            "factsheet": {
                "ticker": "SPY",
                "issuer": "State Street Global Advisors",
                "expense_ratio": 0.09,
                "factsheet_url": "https://www.ssga.com/us/en/individual/etfs/funds/spdr-sp-500-etf-trust-spy",
                "as_of": datetime.now().date().isoformat(),
            },
            "top_holdings": [],
            "risk_assessment": {
                "score": 4.0,
                "level": "High",
                "risk_factors": [],
            },
            "composite_score": 0.78,
            "grade": "B",
            "expense_ratio": 0.09,
            "tracking_error": 0.05,
            "recommendation": "HOLD",
            "confidence": 0.85,
            "rationale": "Solid tracking performance with low expense ratio and good diversification.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act
        export = ETFCrewExport(**valid_data)

        # Assert
        assert export.ticker == "SPY"
        assert export.expense_ratio == 0.09

    def test_should_reject_invalid_expense_ratio(self):
        """Test rejection of expense ratio outside valid range."""
        # Arrange
        invalid_data = {
            "crew_name": "etf_crew",
            "ticker": "SPY",
            "asset_class": "etf",
            "session_id": "test",
            "factsheet": {
                "ticker": "SPY",
                "name": "SPDR S&P 500 ETF",
                "expense_ratio": 0.09,
                "aum": 400000000000.0,
                "inception_date": "1993-01-22",
                "benchmark": "S&P 500",
            },
            "top_holdings": [],
            "risk_assessment": {
                "overall_risk_score": 4.0,
                "risk_factors": [],
                "systematic_risk": 4.0,
                "idiosyncratic_risk": 4.0,
            },
            "composite_score": 0.78,
            "grade": "B",
            "expense_ratio": 10.0,  # Invalid: > 5.0
            "recommendation": "HOLD",
            "confidence": 0.85,
            "rationale": "Solid tracking performance with low expense ratio.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ETFCrewExport(**invalid_data)

        assert "expense_ratio" in str(exc_info.value)


class TestCryptoCrewExport:
    """Test CryptoCrewExport schema validation."""

    def test_should_validate_valid_crypto_export(self):
        """Test validation of valid crypto export data."""
        # Arrange
        valid_data = {
            "crew_name": "crypto_crew",
            "ticker": "BTC",
            "asset_class": "crypto",
            "session_id": "test",
            "thesis": {
                "symbol": "BTC",
                "thesis_bullets": ["Digital gold with strong network effects", "First mover advantage"],
                "references": ["https://bitcoin.org/bitcoin.pdf"],
            },
            "risk_assessment": {
                "score": 5.0,
                "level": "Very High",
                "risk_factors": [],
            },
            "technical_analysis": {},
            "composite_score": 0.72,
            "grade": "C+",
            "volatility_30d": 0.65,
            "max_drawdown": -0.35,
            "recommendation": "HOLD",
            "confidence": 0.75,
            "rationale": "High volatility but strong network effects and institutional adoption.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act
        export = CryptoCrewExport(**valid_data)

        # Assert
        assert export.ticker == "BTC"
        assert export.volatility_30d == 0.65

    def test_should_reject_positive_max_drawdown(self):
        """Test rejection of positive max drawdown (should be negative)."""
        # Arrange
        invalid_data = {
            "crew_name": "crypto_crew",
            "ticker": "BTC",
            "asset_class": "crypto",
            "session_id": "test",
            "thesis": {
                "ticker": "BTC",
                "name": "Bitcoin",
                "investment_thesis": "Digital gold",
                "key_strengths": [],
                "key_risks": [],
                "adoption_metrics": {},
            },
            "risk_assessment": {
                "overall_risk_score": 7.0,
                "risk_factors": [],
                "systematic_risk": 7.0,
                "idiosyncratic_risk": 7.0,
            },
            "technical_analysis": {},
            "composite_score": 0.72,
            "grade": "C+",
            "volatility_30d": 0.65,
            "max_drawdown": 0.35,  # Invalid: should be negative
            "recommendation": "HOLD",
            "confidence": 0.75,
            "rationale": "High volatility but strong network effects.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CryptoCrewExport(**invalid_data)

        assert "max_drawdown" in str(exc_info.value)


class TestDiscoveryCrewExport:
    """Test DiscoveryCrewExport schema validation."""

    def test_should_validate_valid_discovery_export(self):
        """Test validation of valid discovery export data."""
        # Arrange
        valid_data = {
            "crew_name": "discovery_crew",
            "ticker": "N/A",
            "asset_class": "N/A",
            "session_id": "test",
            "opportunities": [
                {
                    "ticker": "MSFT",
                    "name": "Microsoft Corp.",
                    "asset_class": "stock",
                    "composite_score": 0.92,
                    "grade": "A+",
                    "rationale": "Strong cloud growth and excellent fundamentals with market leadership.",
                }
            ],
            "screening_criteria": {"min_score": 0.7},
            "market_context": "Bull market with strong tech sector performance and positive sentiment.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act
        export = DiscoveryCrewExport(**valid_data)

        # Assert
        assert len(export.opportunities) == 1
        assert export.opportunities[0].ticker == "MSFT"

    def test_should_reject_too_many_opportunities(self):
        """Test rejection of more than 10 opportunities."""
        # Arrange
        opportunities = [
            {
                "ticker": f"TICK{i}",
                "name": f"Company {i}",
                "asset_class": "stock",
                "composite_score": 0.75,
                "grade": "A+",
                "rationale": "Strong fundamentals with excellent growth prospects and solid balance sheet.",
            }
            for i in range(11)  # 11 opportunities (> max of 10)
        ]

        invalid_data = {
            "crew_name": "discovery_crew",
            "ticker": "N/A",
            "asset_class": "N/A",
            "session_id": "test",
            "opportunities": opportunities,
            "screening_criteria": {},
            "market_context": "Bull market with strong performance.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DiscoveryCrewExport(**invalid_data)

        assert "opportunities" in str(exc_info.value)

    def test_should_reject_low_score_opportunity(self):
        """Test rejection of opportunities with score < 0.7 (A+ threshold)."""
        # Arrange
        invalid_data = {
            "crew_name": "discovery_crew",
            "ticker": "N/A",
            "asset_class": "N/A",
            "session_id": "test",
            "opportunities": [
                {
                    "ticker": "LOW",
                    "name": "Low Score Co.",
                    "asset_class": "stock",
                    "composite_score": 0.5,  # Invalid: < 0.7
                    "grade": "A+",
                    "rationale": "Should not be A+ with this score.",
                }
            ],
            "screening_criteria": {},
            "market_context": "Market context.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DiscoveryCrewExport(**invalid_data)

        assert "composite_score" in str(exc_info.value)


class TestConsolidatedReportExport:
    """Test ConsolidatedReportExport schema validation."""

    def test_should_validate_valid_consolidated_export(self):
        """Test validation of valid consolidated export data."""
        # Arrange
        valid_data = {
            "session_id": "test-session",
            "consolidation_date": datetime.now().isoformat(),
            "stock_analyses": [],
            "etf_analyses": [],
            "crypto_analyses": [],
            "deep_analyses": [],
            "discovery_results": None,
            "rebalancing_results": None,
            "crew_execution_status": {"stock_crew": "completed"},
            "total_execution_time": 1.234,
            "errors": [],
        }

        # Act
        export = ConsolidatedReportExport(**valid_data)

        # Assert
        assert export.session_id == "test-session"
        assert export.total_execution_time == 1.234

    def test_should_reject_negative_execution_time(self):
        """Test rejection of negative execution time."""
        # Arrange
        invalid_data = {
            "session_id": "test",
            "total_execution_time": -1.0,  # Invalid: negative
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ConsolidatedReportExport(**invalid_data)

        assert "total_execution_time" in str(exc_info.value)

    def test_should_enforce_extra_forbid_on_consolidated(self):
        """Test that extra='forbid' works on consolidated export."""
        # Arrange
        invalid_data = {
            "session_id": "test",
            "total_execution_time": 1.0,
            "unknown_field": "should be rejected",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ConsolidatedReportExport(**invalid_data)

        assert "extra" in str(exc_info.value).lower() or "unknown_field" in str(exc_info.value)
