"""
Unit tests for DeepAnalysisReportGenerator.

Tests the Python-based HTML report generation using Jinja2 templates.
Validates template rendering, performance, and French terminology.
"""

import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from finwiz.reporting.deep_analysis_report_generator import (
    DeepAnalysisReportGenerator,
    generate_deep_analysis_report,
)


class TestDeepAnalysisReportGenerator:
    """Test suite for DeepAnalysisReportGenerator."""

    @pytest.fixture
    def generator(self) -> DeepAnalysisReportGenerator:
        """Create DeepAnalysisReportGenerator instance."""
        return DeepAnalysisReportGenerator()

    @pytest.fixture
    def sample_stock_data(self) -> dict[str, Any]:
        """Create sample stock analysis data."""
        return {
            "ticker": "AAPL",
            "asset_class": "stock",
            "composite_score": 0.85,
            "grade": "A+",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Apple présente des fondamentaux solides avec une croissance soutenue et une position de marché dominante.",
            "fundamental_score": 0.88,
            "technical_score": 0.82,
            "risk_score": 0.85,
            "fundamental_details": {"roe": 0.25, "debt_to_equity": 0.35, "revenue_growth": 0.15, "profit_margin": 0.22},
            "technical_details": {
                "rsi": 55.0,
                "trend_direction": "uptrend",
                "current_price": 150.0,
                "moving_avg_50": 145.0,
                "moving_avg_200": 140.0,
                "macd_diff": 0.5,
            },
            "risk_details": {"volatility": 0.18, "max_drawdown": -0.12, "beta": 1.1, "beta_deviation": 0.1},
            "analysis_date": datetime.now(),
            "session_id": "test_session",
            "data_sources": ["Yahoo Finance API", "SEC EDGAR", "Alpha Vantage API"],
            "report_json_path": "output/reports/test_session/deep_analysis/AAPL_export.json",
            "report_html_path": "output/reports/test_session/deep_analysis/AAPL_report.html",
        }

    @pytest.fixture
    def sample_etf_data(self) -> dict[str, Any]:
        """Create sample ETF analysis data."""
        return {
            "ticker": "SPY",
            "asset_class": "etf",
            "composite_score": 0.75,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.85,
            "rationale": "SPY offre une exposition diversifiée au marché américain avec des frais réduits.",
            "fundamental_score": 0.80,
            "technical_score": 0.70,
            "risk_score": 0.75,
            "fundamental_details": {"expense_ratio": 0.09, "tracking_error": 0.05, "aum": 400e9},
            "technical_details": {"rsi": 60.0, "trend_direction": "strong_uptrend", "current_price": 420.0, "moving_avg_50": 415.0},
            "risk_details": {"volatility": 0.15, "max_drawdown": -0.08, "beta": 1.0},
            "analysis_date": datetime.now(),
            "session_id": "test_session",
            "data_sources": ["Yahoo Finance API", "ETF.com", "Morningstar"],
        }

    @pytest.fixture
    def sample_crypto_data(self) -> dict[str, Any]:
        """Create sample crypto analysis data."""
        return {
            "ticker": "BTC",
            "asset_class": "crypto",
            "composite_score": 0.65,
            "grade": "B",
            "recommendation": "HOLD",
            "confidence": 0.75,
            "rationale": "Bitcoin maintient sa position de leader mais présente une volatilité élevée.",
            "fundamental_score": 0.70,
            "technical_score": 0.60,
            "risk_score": 0.65,
            "fundamental_details": {"market_cap": 800e9, "volume_24h": 25e9, "age_years": 14},
            "technical_details": {"rsi": 45.0, "trend_direction": "sideways"},
            "risk_details": {"volatility": 0.45, "max_drawdown": -0.35, "beta": 1.8},
            "analysis_date": datetime.now(),
            "session_id": "test_session",
            "data_sources": ["CoinMarketCap API", "CoinGecko API"],
        }

    def test_should_initialize_generator_successfully(self, generator: DeepAnalysisReportGenerator):
        """Test that generator initializes with correct template."""
        assert generator.template is not None
        assert generator.template_dir.exists()
        assert generator.env is not None

    def test_should_validate_template_successfully(self, generator: DeepAnalysisReportGenerator):
        """Test template validation with sample data."""
        is_valid = generator.validate_template()
        assert is_valid is True

    def test_should_generate_stock_report_successfully(self, generator: DeepAnalysisReportGenerator, sample_stock_data: dict[str, Any]):
        """Test HTML report generation for stock data."""
        html_content = generator.generate_report(sample_stock_data)

        # Verify HTML structure
        assert "<!DOCTYPE html>" in html_content
        assert '<html lang="fr">' in html_content
        assert "AAPL" in html_content
        assert "A+" in html_content
        assert "BUY" in html_content

        # Verify French terminology
        assert "Analyse Approfondie" in html_content
        assert "Recommandation" in html_content
        assert "Score Composite" in html_content
        assert "Métriques Clés" in html_content

        # Verify stock-specific content
        assert "ROE" in html_content
        assert "Dette/Capitaux" in html_content
        assert "25.0%" in html_content  # ROE value

    def test_should_generate_etf_report_successfully(self, generator: DeepAnalysisReportGenerator, sample_etf_data: dict[str, Any]):
        """Test HTML report generation for ETF data."""
        html_content = generator.generate_report(sample_etf_data)

        # Verify ETF-specific content
        assert "SPY" in html_content
        assert "Ratio de Frais" in html_content
        assert "Erreur de Suivi" in html_content
        assert "Actifs Sous Gestion" in html_content
        assert "400.0B" in html_content  # AUM value

    def test_should_generate_crypto_report_successfully(self, generator: DeepAnalysisReportGenerator, sample_crypto_data: dict[str, Any]):
        """Test HTML report generation for crypto data."""
        html_content = generator.generate_report(sample_crypto_data)

        # Verify crypto-specific content
        assert "BTC" in html_content
        assert "Capitalisation Boursière" in html_content
        assert "Volume 24h" in html_content
        assert "800.0B" in html_content  # Market cap value

    def test_should_generate_all_grade_levels(self, generator: DeepAnalysisReportGenerator):
        """Test report generation for all grade levels (A+ to F)."""
        grades = ["A+", "A", "B", "C", "D", "F"]

        for grade in grades:
            data = {
                "ticker": "TEST",
                "asset_class": "stock",
                "composite_score": 0.5,
                "grade": grade,
                "recommendation": "HOLD",
                "confidence": 0.7,
                "rationale": f"Test rationale for grade {grade}",
                "fundamental_score": 0.5,
                "technical_score": 0.5,
                "risk_score": 0.5,
                "fundamental_details": {},
                "technical_details": {},
                "risk_details": {},
            }

            html_content = generator.generate_report(data)
            assert f"Grade {grade}" in html_content

    def test_should_generate_all_recommendation_types(self, generator: DeepAnalysisReportGenerator):
        """Test report generation for all recommendation types (BUY, HOLD, SELL)."""
        recommendations = ["BUY", "HOLD", "SELL"]

        for recommendation in recommendations:
            data = {
                "ticker": "TEST",
                "asset_class": "stock",
                "composite_score": 0.5,
                "grade": "C",
                "recommendation": recommendation,
                "confidence": 0.7,
                "rationale": f"Test rationale for {recommendation}",
                "fundamental_score": 0.5,
                "technical_score": 0.5,
                "risk_score": 0.5,
                "fundamental_details": {},
                "technical_details": {},
                "risk_details": {},
            }

            html_content = generator.generate_report(data)
            assert recommendation in html_content

    def test_should_complete_generation_under_100ms(self, generator: DeepAnalysisReportGenerator, sample_stock_data: dict[str, Any]):
        """Test that report generation completes in <100ms."""
        start_time = time.time()
        html_content = generator.generate_report(sample_stock_data)
        execution_time = time.time() - start_time

        # Verify performance target (<100ms)
        assert execution_time < 0.1, f"Report generation took {execution_time * 1000:.1f}ms (target: <100ms)"
        assert len(html_content) > 1000  # Ensure substantial content was generated

    def test_should_generate_well_formed_html(self, generator: DeepAnalysisReportGenerator, sample_stock_data: dict[str, Any]):
        """Test that generated HTML is well-formed."""
        html_content = generator.generate_report(sample_stock_data)

        # Basic HTML structure validation
        assert html_content.count("<html") == 1
        assert html_content.count("</html>") == 1
        assert html_content.count("<head") == 1
        assert html_content.count("</head>") == 1
        assert html_content.count("<body") == 1
        assert html_content.count("</body>") == 1

        # Verify UTF-8 encoding declaration
        assert 'charset="UTF-8"' in html_content or "charset=UTF-8" in html_content

    def test_should_validate_required_fields(self, generator: DeepAnalysisReportGenerator):
        """Test validation of required fields."""
        # Missing ticker
        invalid_data = {
            "asset_class": "stock",
            "composite_score": 0.5,
            "grade": "C",
            "recommendation": "HOLD",
            "confidence": 0.7,
            "rationale": "Test",
        }

        with pytest.raises(RuntimeError, match="Missing required fields"):
            generator.generate_report(invalid_data)

    def test_should_validate_asset_class(self, generator: DeepAnalysisReportGenerator):
        """Test validation of asset class."""
        invalid_data = {
            "ticker": "TEST",
            "asset_class": "invalid",
            "composite_score": 0.5,
            "grade": "C",
            "recommendation": "HOLD",
            "confidence": 0.7,
            "rationale": "Test",
        }

        with pytest.raises(RuntimeError, match="Invalid asset_class"):
            generator.generate_report(invalid_data)

    def test_should_validate_grade(self, generator: DeepAnalysisReportGenerator):
        """Test validation of grade."""
        invalid_data = {
            "ticker": "TEST",
            "asset_class": "stock",
            "composite_score": 0.5,
            "grade": "Z",
            "recommendation": "HOLD",
            "confidence": 0.7,
            "rationale": "Test",
        }

        with pytest.raises(RuntimeError, match="Invalid grade"):
            generator.generate_report(invalid_data)

    def test_should_validate_recommendation(self, generator: DeepAnalysisReportGenerator):
        """Test validation of recommendation."""
        invalid_data = {
            "ticker": "TEST",
            "asset_class": "stock",
            "composite_score": 0.5,
            "grade": "C",
            "recommendation": "INVALID",
            "confidence": 0.7,
            "rationale": "Test",
        }

        with pytest.raises(RuntimeError, match="Invalid recommendation"):
            generator.generate_report(invalid_data)

    def test_should_generate_and_save_report(self, generator: DeepAnalysisReportGenerator, sample_stock_data: dict[str, Any]):
        """Test generating and saving report to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.html"

            html_content = generator.generate_and_save_report(sample_stock_data, output_path)

            # Verify file was created
            assert output_path.exists()

            # Verify file content matches returned content
            saved_content = output_path.read_text(encoding="utf-8")
            assert saved_content == html_content

            # Verify content quality
            assert "AAPL" in saved_content
            assert "A+" in saved_content

    def test_should_handle_missing_optional_fields(self, generator: DeepAnalysisReportGenerator):
        """Test handling of missing optional fields."""
        minimal_data = {
            "ticker": "TEST",
            "asset_class": "stock",
            "composite_score": 0.5,
            "grade": "C",
            "recommendation": "HOLD",
            "confidence": 0.7,
            "rationale": "Minimal test data",
            "fundamental_score": 0.5,
            "technical_score": 0.5,
            "risk_score": 0.5,
        }

        html_content = generator.generate_report(minimal_data)

        # Should generate successfully with defaults
        assert "TEST" in html_content
        assert "Grade C" in html_content
        assert "HOLD" in html_content

    def test_should_use_default_data_sources(self, generator: DeepAnalysisReportGenerator):
        """Test that default data sources are used when not provided."""
        data_without_sources = {
            "ticker": "TEST",
            "asset_class": "stock",
            "composite_score": 0.5,
            "grade": "C",
            "recommendation": "HOLD",
            "confidence": 0.7,
            "rationale": "Test without sources",
            "fundamental_score": 0.5,
            "technical_score": 0.5,
            "risk_score": 0.5,
        }

        html_content = generator.generate_report(data_without_sources)

        # Should include default sources
        assert "Yahoo Finance API" in html_content
        assert "Moteur de scoring Python FinWiz" in html_content

    def test_convenience_function(self, sample_stock_data: dict[str, Any]):
        """Test the convenience function for direct usage."""
        html_content = generate_deep_analysis_report(sample_stock_data)

        assert "AAPL" in html_content
        assert "A+" in html_content
        assert "BUY" in html_content

    def test_should_handle_string_analysis_date(self, generator: DeepAnalysisReportGenerator):
        """Test handling of analysis_date as string."""
        data_with_string_date = {
            "ticker": "TEST",
            "asset_class": "stock",
            "composite_score": 0.5,
            "grade": "C",
            "recommendation": "HOLD",
            "confidence": 0.7,
            "rationale": "Test with string date",
            "analysis_date": "2025-01-25T10:30:00Z",
            "fundamental_score": 0.5,
            "technical_score": 0.5,
            "risk_score": 0.5,
        }

        html_content = generator.generate_report(data_with_string_date)
        assert "TEST" in html_content

    def test_should_verify_french_terminology(self, generator: DeepAnalysisReportGenerator, sample_stock_data: dict[str, Any]):
        """Test that French terminology is correctly used throughout the report."""
        html_content = generator.generate_report(sample_stock_data)

        # Key French terms that should be present
        french_terms = [
            "Analyse Approfondie",
            "Résumé Exécutif",
            "Recommandation",
            "Métriques Clés",
            "Analyse Fondamentale",
            "Analyse Technique",
            "Évaluation des Risques",
            "Sources de Données",
            "Score Composite",
            "Niveau de Confiance",
        ]

        for term in french_terms:
            assert term in html_content, f"French term '{term}' not found in report"

    def test_should_handle_performance_regression(self, generator: DeepAnalysisReportGenerator):
        """Test performance regression detection."""
        # Generate multiple reports and measure average time
        data = {
            "ticker": "PERF",
            "asset_class": "stock",
            "composite_score": 0.5,
            "grade": "C",
            "recommendation": "HOLD",
            "confidence": 0.7,
            "rationale": "Performance test",
            "fundamental_score": 0.5,
            "technical_score": 0.5,
            "risk_score": 0.5,
        }

        times = []
        for _ in range(10):
            start_time = time.time()
            generator.generate_report(data)
            execution_time = time.time() - start_time
            times.append(execution_time)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        # Performance regression check
        assert avg_time < 0.05, f"Average generation time {avg_time * 1000:.1f}ms exceeds 50ms"
        assert max_time < 0.1, f"Maximum generation time {max_time * 1000:.1f}ms exceeds 100ms"
