"""
Integration tests for enhanced consolidated reporter input.

Tests that the get_consolidated_reporter_input method properly includes
backtesting metrics, market context, methodology, and performance report.
"""

from datetime import datetime
from pathlib import Path

import pytest

from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.manager import CrewDataIntegrationManager


class TestConsolidatedReporterInputEnhanced:
    """Test suite for enhanced consolidated reporter input."""

    @pytest.fixture
    def integration_manager(self, tmp_path: Path) -> CrewDataIntegrationManager:
        """Create integration manager instance with temp directory."""
        return CrewDataIntegrationManager(output_dir=tmp_path)

    @pytest.fixture
    def data_accessor(self, integration_manager: CrewDataIntegrationManager) -> CrewDataAccessor:
        """Create data accessor instance."""
        return CrewDataAccessor(integration_manager)

    @pytest.fixture
    def mock_discovery_data_with_validation(self, tmp_path: Path) -> dict:
        """Create mock discovery data with validation results."""
        # Create mock validation result as plain dict
        validation_result = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "validation_passed": True,
            "validation_details": [
                {
                    "criterion": "backtesting_return",
                    "passed": True,
                    "value": 0.12,
                    "threshold": 0.08,
                    "weight": 0.25,
                }
            ],
            "overall_score": 0.85,
            "grade": "A+",
            "backtesting_metrics": {
                "annualized_return": 0.12,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.15,
                "win_rate": 0.55,
                "backtest_period_years": 5,
            },
            "market_regimes_tested": {
                "bull": {"annualized_return": 0.18, "sharpe_ratio": 1.8, "max_drawdown": -0.10, "win_rate": 0.65},
                "bear": {"annualized_return": 0.05, "sharpe_ratio": 0.8, "max_drawdown": -0.25, "win_rate": 0.45},
                "sideways": {
                    "annualized_return": 0.08,
                    "sharpe_ratio": 1.2,
                    "max_drawdown": -0.12,
                    "win_rate": 0.50,
                },
            },
            "regime_consistency_score": 0.75,
            "recommendation": "STRONG_BUY",
            "confidence_level": 0.85,
            "validation_timestamp": datetime.now().isoformat(),
        }

        # Create mock discovery result as plain dict
        discovery_result = {
            "asset_type": "stock",
            "total_screened": 500,
            "candidates_found": 10,
            "a_plus_candidates": [
                {
                    "candidate": {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "asset_type": "stock",
                        "current_price": 150.0,
                        "preliminary_score": 0.85,
                        "final_score": 0.85,
                        "grade": "A+",
                        "grade_description": "Exceptional quality",
                        "recommended_action": "BUY",
                        "discovery_date": datetime.now().isoformat(),
                        "data_source": "Yahoo Finance",
                    },
                    "fundamental_score": 0.90,
                    "technical_score": 0.85,
                    "quality_score": 0.88,
                    "risk_score": 0.20,
                    "composite_score": 0.85,
                    "confidence_level": 0.85,
                    "is_a_plus_candidate": True,
                    "rationale": ["Strong fundamentals", "Excellent technical setup"],
                    "key_metrics": {},
                    "competitive_advantages": [],
                    "risk_factors": [],
                }
            ],
            "market_context": {
                "regime_type": "bull",
                "vix_level": 15.5,
                "inflation_rate": 2.5,
                "interest_rate_trend": "stable",
                "market_stress_level": "low",
            },
            "discovery_criteria": {
                "stock_min_roe": 0.20,
                "stock_min_revenue_growth": 0.15,
                "stock_max_debt_to_equity": 0.3,
                "stock_min_market_cap": 1e9,
            },
            "screening_efficiency": 0.02,
            "discovery_timestamp": datetime.now().isoformat(),
        }

        return {
            "validation_results": [validation_result],
            "discovery_result": discovery_result,
        }

    def test_should_include_backtesting_summary_when_available(self, data_accessor: CrewDataAccessor, mock_discovery_data_with_validation: dict, mocker) -> None:
        """Test that backtesting summary is included in consolidated reporter input."""
        # Arrange
        base_reporter_input = {
            "consolidated_crew_data": {"discovery": mock_discovery_data_with_validation},
            "core_analysis_summary": {},
            "aplus_opportunities": None,
            "aplus_availability_status": {"available": False},
            "portfolio_allocation_updates": [],
            "data_freshness_hours": 24,
            "report_generation_timestamp": datetime.now().isoformat(),
            "data_sources": ["discovery"],
            "total_data_points": 1,
        }
        mocker.patch.object(data_accessor.cache, "get_consolidated_reporter_input", return_value=base_reporter_input)
        mocker.patch.object(data_accessor, "get_discovery_data", return_value=mock_discovery_data_with_validation)

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24)

        # Assert
        assert "backtesting_summary" in result
        assert result["backtesting_summary"] is not None
        assert "total_candidates_tested" in result["backtesting_summary"]
        assert result["backtesting_summary"]["total_candidates_tested"] == 1

    def test_should_include_market_context_summary_when_available(self, data_accessor: CrewDataAccessor, mock_discovery_data_with_validation: dict, mocker) -> None:
        """Test that market context summary is included in consolidated reporter input."""
        # Arrange
        base_reporter_input = {
            "consolidated_crew_data": {"discovery": mock_discovery_data_with_validation},
            "core_analysis_summary": {},
        }
        mocker.patch.object(data_accessor.cache, "get_consolidated_reporter_input", return_value=base_reporter_input)
        mocker.patch.object(data_accessor, "get_discovery_data", return_value=mock_discovery_data_with_validation)

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24)

        # Assert
        assert "market_context_summary" in result
        assert result["market_context_summary"] is not None
        assert "market_regime" in result["market_context_summary"]
        assert result["market_context_summary"]["market_regime"]["regime_type"] == "bull"

    def test_should_include_methodology_summary_when_available(self, data_accessor: CrewDataAccessor, mock_discovery_data_with_validation: dict, mocker) -> None:
        """Test that methodology summary is included in consolidated reporter input."""
        # Arrange
        base_reporter_input = {
            "consolidated_crew_data": {"discovery": mock_discovery_data_with_validation},
            "core_analysis_summary": {},
        }
        mocker.patch.object(data_accessor.cache, "get_consolidated_reporter_input", return_value=base_reporter_input)
        mocker.patch.object(data_accessor, "get_discovery_data", return_value=mock_discovery_data_with_validation)

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24)

        # Assert
        assert "methodology_summary" in result
        assert result["methodology_summary"] is not None
        assert "screening_criteria" in result["methodology_summary"]
        assert "validation_statistics" in result["methodology_summary"]

    def test_should_include_performance_report_when_available(self, data_accessor: CrewDataAccessor, mock_discovery_data_with_validation: dict, mocker) -> None:
        """Test that performance report is included in consolidated reporter input."""
        # Arrange
        base_reporter_input = {
            "consolidated_crew_data": {"discovery": mock_discovery_data_with_validation},
            "core_analysis_summary": {},
        }
        mocker.patch.object(data_accessor.cache, "get_consolidated_reporter_input", return_value=base_reporter_input)
        mocker.patch.object(data_accessor, "get_discovery_data", return_value=mock_discovery_data_with_validation)

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24, current_portfolio_grade=0.70)

        # Assert
        assert "performance_report" in result
        assert result["performance_report"] is not None
        assert "total_candidates_analyzed" in result["performance_report"]
        assert "portfolio_impact" in result["performance_report"]

    def test_should_handle_missing_discovery_data_gracefully(self, data_accessor: CrewDataAccessor, mocker) -> None:
        """Test that missing discovery data doesn't break consolidated reporter input."""
        # Arrange
        base_reporter_input = {
            "consolidated_crew_data": {},
            "core_analysis_summary": {},
        }
        mocker.patch.object(data_accessor.cache, "get_consolidated_reporter_input", return_value=base_reporter_input)
        mocker.patch.object(data_accessor, "get_discovery_data", return_value=None)

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24)

        # Assert
        assert "backtesting_summary" in result
        assert result["backtesting_summary"] is None
        assert "market_context_summary" in result
        assert result["market_context_summary"] is None
        assert "methodology_summary" in result
        assert result["methodology_summary"] is None
        assert "performance_report" in result
        assert result["performance_report"] is None

    def test_should_pass_current_portfolio_grade_to_performance_report(self, data_accessor: CrewDataAccessor, mock_discovery_data_with_validation: dict, mocker) -> None:
        """Test that current_portfolio_grade is passed to performance report generation."""
        # Arrange
        base_reporter_input = {
            "consolidated_crew_data": {"discovery": mock_discovery_data_with_validation},
            "core_analysis_summary": {},
        }
        mocker.patch.object(data_accessor.cache, "get_consolidated_reporter_input", return_value=base_reporter_input)

        mock_get_performance_report = mocker.patch.object(data_accessor, "get_performance_report", return_value={"test": "data"})

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24, current_portfolio_grade=0.65)

        # Assert
        mock_get_performance_report.assert_called_once_with(24, 0.65)
        assert result["performance_report"] == {"test": "data"}

    def test_should_return_base_input_when_enhanced_extraction_fails(self, data_accessor: CrewDataAccessor, mocker) -> None:
        """Test that base reporter input is returned even if enhanced extraction fails."""
        # Arrange
        base_input = {"consolidated_crew_data": {}, "core_analysis_summary": {}}
        mocker.patch.object(data_accessor.cache, "get_consolidated_reporter_input", return_value=base_input)
        mocker.patch.object(data_accessor, "get_backtesting_metrics", side_effect=Exception("Extraction failed"))

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24)

        # Assert
        assert result is not None
        assert "consolidated_crew_data" in result
        # Enhanced data should be None due to exception
        assert result.get("backtesting_summary") is None

    def test_should_log_enhanced_data_status(self, data_accessor: CrewDataAccessor, mock_discovery_data_with_validation: dict, mocker, caplog) -> None:
        """Test that enhanced data inclusion status is logged."""
        # Arrange
        import logging

        caplog.set_level(logging.INFO)
        base_reporter_input = {
            "consolidated_crew_data": {"discovery": mock_discovery_data_with_validation},
            "core_analysis_summary": {},
        }
        mocker.patch.object(data_accessor.cache, "get_consolidated_reporter_input", return_value=base_reporter_input)
        mocker.patch.object(data_accessor, "get_discovery_data", return_value=mock_discovery_data_with_validation)

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24)

        # Assert
        assert any("Enhanced reporter input generated with additional data" in record.message for record in caplog.records)

    def test_should_include_all_enhanced_data_fields_in_result(self, data_accessor: CrewDataAccessor, mock_discovery_data_with_validation: dict, mocker) -> None:
        """Test that all enhanced data fields are present in the result."""
        # Arrange
        base_reporter_input = {
            "consolidated_crew_data": {"discovery": mock_discovery_data_with_validation},
            "core_analysis_summary": {},
        }
        mocker.patch.object(data_accessor.cache, "get_consolidated_reporter_input", return_value=base_reporter_input)
        mocker.patch.object(data_accessor, "get_discovery_data", return_value=mock_discovery_data_with_validation)

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24)

        # Assert - All enhanced fields should be present
        assert "backtesting_summary" in result
        assert "market_context_summary" in result
        assert "methodology_summary" in result
        assert "performance_report" in result

        # Base fields should still be present
        assert "consolidated_crew_data" in result
        assert "core_analysis_summary" in result

    def test_should_maintain_backward_compatibility_with_existing_fields(self, data_accessor: CrewDataAccessor, mocker) -> None:
        """Test that existing fields in reporter input are not affected by enhanced data."""
        # Arrange
        base_input = {
            "consolidated_crew_data": {"stock": {"test": "data"}},
            "core_analysis_summary": {"summary": "test"},
            "aplus_opportunities": None,
            "aplus_availability_status": {"available": False},
            "portfolio_allocation_updates": [],
            "data_freshness_hours": 24,
            "report_generation_timestamp": datetime.now().isoformat(),
            "data_sources": ["stock"],
            "total_data_points": 1,
        }
        mocker.patch.object(data_accessor.cache, "get_consolidated_reporter_input", return_value=base_input)
        mocker.patch.object(data_accessor, "get_discovery_data", return_value=None)

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24)

        # Assert - All original fields should still be present
        assert "consolidated_crew_data" in result
        assert "core_analysis_summary" in result
        assert "aplus_opportunities" in result
        assert "aplus_availability_status" in result
        assert "portfolio_allocation_updates" in result
        assert "data_freshness_hours" in result
        assert "report_generation_timestamp" in result
        assert "data_sources" in result
        assert "total_data_points" in result

        # Enhanced fields should be added
        assert "backtesting_summary" in result
        assert "market_context_summary" in result
        assert "methodology_summary" in result
        assert "performance_report" in result
