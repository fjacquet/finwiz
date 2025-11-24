"""
Unit tests for ReportingOrchestrator.

Tests report consolidation, HTML generation, and export path management.
"""

import json

import pytest
from pytest import approx

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.reporting_orchestrator import ReportingOrchestrator
from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview


class TestReportingOrchestrator:
    """Test suite for ReportingOrchestrator."""

    @pytest.fixture
    def state(self):
        """Create a FinwizState instance for testing."""
        return FinwizState()

    @pytest.fixture
    def orchestrator(self, state):
        """Create a ReportingOrchestrator instance for testing."""
        return ReportingOrchestrator(state)

    @pytest.fixture
    def sample_portfolio_review(self):
        """Create a sample PortfolioReview for testing."""
        from datetime import datetime

        from finwiz.schemas.common import RiskAssessmentStandardized

        return PortfolioReview(
            as_of=datetime.now(),
            holdings=[
                HoldingDecision(
                    ticker="AAPL",
                    name="Apple Inc.",
                    asset_class="stock",
                    currency="USD",
                    decision="KEEP",
                    grade="A",
                    composite_score=0.85,
                    grade_description="Excellent performance",
                    recommended_action="Keep - Strong fundamentals",
                    risk=RiskAssessmentStandardized(
                        score=2.0,
                        level="Low",
                    ),
                    rationale_bullets=["Strong revenue growth", "High profit margins"],
                ),
                HoldingDecision(
                    ticker="GOOGL",
                    name="Alphabet Inc.",
                    asset_class="stock",
                    currency="USD",
                    decision="KEEP",
                    grade="A",
                    composite_score=0.82,
                    grade_description="Excellent performance",
                    recommended_action="Keep - Market leader",
                    risk=RiskAssessmentStandardized(
                        score=2.0,
                        level="Low",
                    ),
                    rationale_bullets=["Dominant search position", "Growing cloud business"],
                ),
            ],
        )

    def test_should_initialize_with_state(self, state):
        """Test ReportingOrchestrator initializes correctly."""
        # Act
        orch = ReportingOrchestrator(state)

        # Assert
        assert orch.state == state
        assert orch.logger is not None

    def test_should_store_crew_export_paths(self, orchestrator, state):
        """Test storing crew export paths in state."""
        # Arrange
        crew_name = "stock_crew"
        export_paths = ["output/stock/AAPL_default.json", "output/stock/GOOGL_default.json"]

        # Act
        orchestrator.store_crew_export_paths(crew_name, export_paths)

        # Assert
        assert hasattr(state, "crew_export_paths")
        assert crew_name in state.crew_export_paths
        assert state.crew_export_paths[crew_name] == export_paths

    def test_should_calculate_crew_export_path(self, orchestrator, state):
        """Test calculating crew export path."""
        # Arrange
        crew_name = "stock_crew"
        ticker = "AAPL"
        state.session_id = "test_session"

        # Act
        export_path = orchestrator.get_crew_export_path(crew_name, ticker)

        # Assert
        assert export_path == "output/stock_crew/AAPL_test_session.json"

    def test_should_calculate_crew_export_path_with_default_session(self, orchestrator):
        """Test calculating crew export path with default session."""
        # Arrange
        crew_name = "etf_crew"
        ticker = "SPY"

        # Act
        export_path = orchestrator.get_crew_export_path(crew_name, ticker)

        # Assert
        assert export_path == "output/etf_crew/SPY_default.json"

    def test_should_consolidate_reports_from_export_paths(self, orchestrator, tmp_path, mocker):
        """Test consolidating reports from crew export paths."""
        # Arrange
        # Create temporary JSON files
        stock_file = tmp_path / "AAPL_export.json"
        stock_data = {"ticker": "AAPL", "grade": "A", "composite_score": 0.85}
        stock_file.write_text(json.dumps(stock_data))

        etf_file = tmp_path / "SPY_export.json"
        etf_data = {"ticker": "SPY", "grade": "A+", "composite_score": 0.92}
        etf_file.write_text(json.dumps(etf_data))

        crew_export_paths = {
            "stock_crew": [str(stock_file)],
            "etf_crew": [str(etf_file)],
        }

        # Act
        result = orchestrator.consolidate_reports(crew_export_paths)

        # Assert
        assert result["success"] is True
        assert "consolidated_data" in result
        consolidated = result["consolidated_data"]
        assert "stock_crew" in consolidated["crews"]
        assert "etf_crew" in consolidated["crews"]
        assert len(consolidated["crews"]["stock_crew"]) == 1
        assert len(consolidated["crews"]["etf_crew"]) == 1
        assert consolidated["total_reports"] == 2

    def test_should_handle_missing_export_files_gracefully(self, orchestrator):
        """Test consolidation handles missing files gracefully."""
        # Arrange
        crew_export_paths = {
            "stock_crew": ["nonexistent_file.json"],
        }

        # Act
        result = orchestrator.consolidate_reports(crew_export_paths)

        # Assert
        assert result["success"] is True
        assert result["consolidated_data"]["total_reports"] == 0

    def test_should_calculate_grade_distribution(self, orchestrator):
        """Test calculating grade distribution from deep analysis results."""
        # Arrange
        deep_analysis = {
            "AAPL": {"ticker": "AAPL", "grade": "A+", "composite_score": 0.92},
            "GOOGL": {"ticker": "GOOGL", "grade": "A", "composite_score": 0.85},
            "MSFT": {"ticker": "MSFT", "grade": "A", "composite_score": 0.83},
            "TSLA": {"ticker": "TSLA", "grade": "B", "composite_score": 0.75},
            "IBM": {"ticker": "IBM", "grade": "C", "composite_score": 0.65},
        }

        # Act
        distribution = orchestrator._calculate_grade_distribution(deep_analysis)

        # Assert
        assert distribution["A+"] == 1
        assert distribution["A"] == 2
        assert distribution["B"] == 1
        assert distribution["C"] == 1
        assert distribution["D"] == 0
        assert distribution["F"] == 0

    def test_should_convert_dict_to_portfolio_review(self, orchestrator):
        """Test converting dictionary to PortfolioReview object."""
        # Arrange
        from datetime import datetime

        portfolio_dict = {
            "as_of": datetime.now().isoformat(),
            "holdings": [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "asset_class": "stock",
                    "currency": "USD",
                    "decision": "KEEP",
                    "grade": "A",
                    "composite_score": 0.85,
                    "grade_description": "Excellent",
                    "recommended_action": "Keep",
                    "risk": {
                        "score": 2.0,
                        "level": "Low",
                    },
                    "rationale_bullets": ["Strong fundamentals"],
                }
            ],
        }

        # Act
        portfolio_review = orchestrator._convert_to_portfolio_review(portfolio_dict)

        # Assert
        assert isinstance(portfolio_review, PortfolioReview)
        assert len(portfolio_review.holdings) == 1
        assert portfolio_review.holdings[0].ticker == "AAPL"

    def test_should_handle_nested_portfolio_review_structure(self, orchestrator):
        """Test converting nested portfolio review structure."""
        # Arrange
        from datetime import datetime

        nested_dict = {
            "portfolio_review": {
                "as_of": datetime.now().isoformat(),
                "holdings": [
                    {
                        "ticker": "AAPL",
                        "name": "Apple Inc.",
                        "asset_class": "stock",
                        "currency": "USD",
                        "decision": "KEEP",
                        "grade": "A",
                        "composite_score": 0.85,
                        "grade_description": "Excellent",
                        "recommended_action": "Keep",
                        "risk": {
                            "score": 2.0,
                            "level": "Low",
                        },
                        "rationale_bullets": ["Strong fundamentals"],
                    }
                ],
            }
        }

        # Act
        portfolio_review = orchestrator._convert_to_portfolio_review(nested_dict)

        # Assert
        assert isinstance(portfolio_review, PortfolioReview)
        assert len(portfolio_review.holdings) == 1

    def test_should_merge_deep_analysis_into_portfolio(self, orchestrator, sample_portfolio_review):
        """Test merging deep analysis results into portfolio review."""
        # Arrange
        deep_analysis_results = {
            "results_by_ticker": {
                "AAPL": {
                    "ticker": "AAPL",
                    "grade": "A+",
                    "composite_score": 0.95,
                    "recommendation": "BUY",
                    "asset_class": "stock",
                },
                "GOOGL": {
                    "ticker": "GOOGL",
                    "grade": "A",
                    "composite_score": 0.88,
                    "recommendation": "HOLD",
                    "asset_class": "stock",
                },
            }
        }

        # Act
        orchestrator._merge_deep_analysis_into_portfolio(sample_portfolio_review, deep_analysis_results)

        # Assert
        aapl_holding = sample_portfolio_review.holdings[0]
        assert aapl_holding.composite_score == approx(0.95)
        assert aapl_holding.grade == "A+"
        assert aapl_holding.decision == "BUY"
        assert "Score composite: 0.950" in aapl_holding.rationale_bullets[0]

        googl_holding = sample_portfolio_review.holdings[1]
        assert googl_holding.composite_score == approx(0.88)
        assert googl_holding.grade == "A"
        assert googl_holding.decision == "HOLD"

    def test_should_transform_deep_analysis_results(self, orchestrator, state):
        """Test transforming raw deep analysis results."""
        # Arrange
        state.total_holdings = 3
        raw_deep_analysis = {
            "AAPL": {
                "ticker": "AAPL",
                "grade": "A+",
                "composite_score": 0.95,
                "recommendation": "BUY",
                "asset_class": "stock",
            },
            "GOOGL": {
                "ticker": "GOOGL",
                "grade": "A",
                "composite_score": 0.85,
                "recommendation": "HOLD",
                "asset_class": "stock",
            },
        }

        # Act
        transformed = orchestrator._transform_deep_analysis_results(raw_deep_analysis)

        # Assert
        assert transformed["successful_analyses"] == 2
        assert transformed["failed_analyses"] == 1
        assert transformed["total_holdings"] == 3
        # Use approximate comparison for floating point
        assert abs(transformed["performance_metrics"]["average_composite_score"] - 0.90) < 0.01
        assert "AAPL" in transformed["results_by_ticker"]
        assert "GOOGL" in transformed["results_by_ticker"]

    def test_should_generate_html_from_export(self, orchestrator, tmp_path, mocker):
        """Test generating HTML from export data using Jinja2."""
        # Arrange
        # Create a temporary template directory
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create a simple template
        template_file = template_dir / "test_template.html"
        template_file.write_text("<h1>{{ title }}</h1><p>{{ content }}</p>")

        # Mock the template directory path
        mocker.patch("finwiz.orchestrators.reporting_orchestrator.Path", return_value=template_dir)

        export_data = {"title": "Test Report", "content": "This is a test"}

        # Act
        html = orchestrator.generate_html_from_export(export_data, "test_template.html")

        # Assert
        assert "<h1>Test Report</h1>" in html
        assert "<p>This is a test</p>" in html

    def test_should_handle_report_generation_error(self, orchestrator, state, mocker):
        """Test handling report generation errors."""
        # Arrange
        # Mock _get_portfolio_review_from_state to return None
        mocker.patch.object(orchestrator, "_get_portfolio_review_from_state", return_value=None)

        # Act
        result = orchestrator.report()

        # Assert
        assert result["success"] is False
        assert "error" in result
        assert state.report_generation_success is False
        assert state.report_generation_error is not None

    def test_should_read_discovery_results(self, orchestrator, tmp_path, mocker):
        """Test reading discovery results from JSON file."""
        # Arrange
        discovery_data = {
            "timestamp": "2025-11-23T16:18:02.525924",
            "total_opportunities": 8,
            "opportunities": [
                {"ticker": "MSFT", "name": "Microsoft", "grade": "A+", "composite_score": 0.94, "recommendation": "BUY"},
                {"ticker": "NVDA", "name": "NVIDIA", "grade": "A+", "composite_score": 0.91, "recommendation": "BUY"},
            ],
            "by_asset_class": {"stock": 3, "etf": 3, "crypto": 2},
        }

        # Create mock discovery file
        discovery_path = tmp_path / "output" / "discovery" / "consolidated_discovery.json"
        discovery_path.parent.mkdir(parents=True, exist_ok=True)
        import json

        with open(discovery_path, "w") as f:
            json.dump(discovery_data, f)

        # Mock Path to return our temp path
        mocker.patch("finwiz.orchestrators.reporting_orchestrator.Path", return_value=discovery_path)

        # Act
        result = orchestrator._read_discovery_results()

        # Assert
        assert result is not None
        assert result["total_opportunities"] == 8
        assert len(result["opportunities"]) == 2

    def test_should_handle_missing_discovery_results(self, orchestrator, mocker):
        """Test handling when discovery results file doesn't exist."""
        # Arrange
        from pathlib import Path

        fake_path = mocker.Mock(spec=Path)
        fake_path.exists.return_value = False
        mocker.patch("finwiz.orchestrators.reporting_orchestrator.Path", return_value=fake_path)

        # Act
        result = orchestrator._read_discovery_results()

        # Assert
        assert result is None

    def test_should_save_merged_portfolio_review(self, orchestrator, sample_portfolio_review, tmp_path, mocker):
        """Test saving merged portfolio review to disk."""
        # Arrange
        output_path = tmp_path / "output" / "portfolio" / "portfolio_review.json"

        # Mock Path to return our temp path
        mocker.patch("finwiz.orchestrators.reporting_orchestrator.Path", return_value=output_path)

        # Act
        orchestrator._save_merged_portfolio_review(sample_portfolio_review)

        # Assert
        assert output_path.exists()

        # Verify content
        import json

        with open(output_path) as f:
            saved_data = json.load(f)

        assert len(saved_data["holdings"]) == 2
        assert saved_data["holdings"][0]["ticker"] == "AAPL"
        assert saved_data["holdings"][0]["composite_score"] == approx(0.85)

    def test_should_log_score_summary_when_saving(self, orchestrator, sample_portfolio_review, tmp_path, mocker):
        """Test that score summary is logged when saving merged portfolio."""
        # Arrange
        output_path = tmp_path / "output" / "portfolio" / "portfolio_review.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Mock the logger to verify it's called
        mock_logger = mocker.patch.object(orchestrator, "logger")

        # Act
        orchestrator._save_merged_portfolio_review(sample_portfolio_review)

        # Assert - verify logger was called with score summary
        calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Merged portfolio stats" in str(call) for call in calls)
        assert any("2 holdings" in str(call) for call in calls)

    def test_should_read_json_file(self, orchestrator, tmp_path):
        """Test reading JSON file."""
        # Arrange
        json_file = tmp_path / "test.json"
        test_data = {"ticker": "AAPL", "grade": "A"}
        json_file.write_text(json.dumps(test_data))

        # Act
        data = orchestrator._read_json_file(str(json_file))

        # Assert
        assert data["ticker"] == "AAPL"
        assert data["grade"] == "A"

    def test_should_handle_consolidation_error(self, orchestrator, mocker):
        """Test handling consolidation errors."""
        # Arrange
        # Mock _read_json_file to raise an exception
        mocker.patch.object(orchestrator, "_read_json_file", side_effect=Exception("Read error"))

        crew_export_paths = {"stock_crew": ["test.json"]}

        # Act
        result = orchestrator.consolidate_reports(crew_export_paths)

        # Assert
        # Should still succeed but with 0 reports
        assert result["success"] is True
        assert result["consolidated_data"]["total_reports"] == 0
