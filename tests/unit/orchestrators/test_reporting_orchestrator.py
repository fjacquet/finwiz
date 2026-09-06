"""
Unit tests for ReportingOrchestrator.

Tests report consolidation, HTML generation, and export path management.
"""

import json
from datetime import UTC, datetime

import pytest
from pytest import approx

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.reporting_orchestrator import ReportingOrchestrator
from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview
from finwiz.scoring.grading_system import count_grade_distribution


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

    def test_should_calculate_grade_distribution(self):
        """Test calculating grade distribution using centralized grading_system.

        Note: This tests the centralized count_grade_distribution function
        which is used by ReportingOrchestrator._transform_deep_analysis_results.
        """
        # Arrange
        deep_analysis = {
            "AAPL": {"ticker": "AAPL", "grade": "A+", "composite_score": 0.92},
            "GOOGL": {"ticker": "GOOGL", "grade": "A", "composite_score": 0.85},
            "MSFT": {"ticker": "MSFT", "grade": "A", "composite_score": 0.83},
            "TSLA": {"ticker": "TSLA", "grade": "B", "composite_score": 0.75},
            "IBM": {"ticker": "IBM", "grade": "C", "composite_score": 0.65},
        }

        # Act - use centralized function directly
        distribution = count_grade_distribution(deep_analysis)

        # Assert
        assert distribution["A+"] == 1
        assert distribution["A"] == 2
        assert distribution["B"] == 1
        assert distribution["C"] == 1

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

        # Point the (package-relative) template dir at our tmp templates
        mocker.patch("finwiz.orchestrators.reporting.crew_html._TEMPLATE_DIR", template_dir)

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
        mocker.patch("finwiz.orchestrators.reporting.enrichment.Path", return_value=discovery_path)

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
        mocker.patch("finwiz.orchestrators.reporting.enrichment.Path", return_value=fake_path)

        # Act
        result = orchestrator._read_discovery_results()

        # Assert
        assert result is None

    def test_should_save_merged_portfolio_review(self, orchestrator, sample_portfolio_review, tmp_path, mocker):
        """Test saving merged portfolio review to disk."""
        # Arrange
        output_path = tmp_path / "output" / "portfolio" / "portfolio_review.json"

        # Mock Path to return our temp path
        mocker.patch("finwiz.orchestrators.reporting.data_loading.Path", return_value=output_path)

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


class TestHoldingsInsightsExtraction:
    """Tests for _extract_holdings_insights (quintessence card distillation)."""

    @pytest.fixture
    def orchestrator(self):
        return ReportingOrchestrator(FinwizState())

    @staticmethod
    def _write_enriched(base, ticker: str, qualitative: dict, final_grade: str = "A") -> None:
        base.mkdir(parents=True, exist_ok=True)
        (base / f"{ticker}_enriched.json").write_text(json.dumps({"ticker": ticker, "final_grade": final_grade, "qualitative": qualitative}))

    def test_distills_from_session_enriched_json(self, orchestrator, tmp_path, monkeypatch):
        # Arrange — session-scoped dir is preferred over the generic dir.
        monkeypatch.chdir(tmp_path)
        qualitative = {
            "investment_synthesis": {
                "investment_thesis": "Strong compounder.",
                "bull_case": "Upside scenario.",
                "bear_case": "Downside scenario.",
                "scenario_probabilities": {"bull": 0.3, "base": 0.5, "bear": 0.2},
                "final_recommendation": "BUY",
                "recommendation_confidence": "HIGH",
                "action_plan": {"immediate_actions": ["Buy now", "Watch earnings", "Ignore me"]},
            },
            "sec_insights": {"competitive_advantages": ["Network effects"], "risk_factors": ["Key risk A"]},
            "fundamental_context": {"growth_drivers": ["Driver 1", "Driver 2", "Driver 3"], "competitive_positioning": "Leader"},
            "contextual_risks": {"regulatory_risks": ["Reg risk"], "competitive_risks": ["Comp risk"], "operational_risks": []},
            "fact_pack": {
                "asset_class": "stock",
                "details": {
                    "kind": "equity",
                    "business_summary": "Single entity.",
                    "leadership": "CEO X.",
                    "recent_events": ["E1", "E2", "E3", "E4"],
                    "events_from_filings": False,
                },
                "fetched_at": datetime.now(UTC).isoformat(),
                "freshness": "fresh",
                "confidence": 0.9,
                "source_citations": ["https://a.com"],
                "sources_used": [],
            },
        }
        self._write_enriched(tmp_path / "output" / "enriched" / "default" / "stock", "AAPL", qualitative)

        # Act
        result = orchestrator._extract_holdings_insights({"AAPL": {}})

        # Assert
        assert result is not None
        card = result["AAPL"]
        assert card["thesis"] == "Strong compounder."
        assert card["moat"] == "Network effects"
        assert card["top_sec_risk"] == "Key risk A"
        assert card["growth_drivers"] == ["Driver 1", "Driver 2"]  # capped at 2
        assert card["immediate_actions"] == ["Buy now", "Watch earnings"]  # capped at 2
        assert card["key_risks"] == ["Reg risk", "Comp risk"]  # operational empty → omitted
        # fact_pack is now rendered once via finwiz.analysis.fact_pack.render.to_rows,
        # not re-distilled here with its own truncation rules.
        rows = dict(card["fact_pack"]["rows"])
        assert rows["Structure"] == "Single entity."
        assert rows["Direction"] == "CEO X."
        # All 4 fixture events must survive uncapped -- proves the old
        # report-side cap-at-3 truncation is gone (to_rows has no cap of its
        # own; only the schema's max_length=10 bounds this).
        assert rows["Événements récents (presse)"] == "- E1\n- E2\n- E3\n- E4"
        assert card["fact_pack"]["freshness"] == "fresh"
        assert card["fact_pack"]["source_citations"] == ["https://a.com"]
        assert card["report_link"] == "stock/AAPL_report.html"
        assert card["grade"] == "A"

    def test_returns_none_when_no_qualitative(self, orchestrator, tmp_path, monkeypatch):
        # Arrange — enriched file with no qualitative section (ETF/crypto-only).
        monkeypatch.chdir(tmp_path)
        base = tmp_path / "output" / "enriched" / "default" / "etf"
        base.mkdir(parents=True, exist_ok=True)
        (base / "SPY_enriched.json").write_text(json.dumps({"ticker": "SPY", "qualitative": None}))

        # Act / Assert
        assert orchestrator._extract_holdings_insights({"SPY": {}}) is None

    def test_distills_from_canonical_asset_dir(self, orchestrator, tmp_path, monkeypatch):
        # Regression: a real kickoff writes to output/{asset_class} (not output/enriched/...).
        # The extractor must find files there or the Quintessence section silently vanishes.
        monkeypatch.chdir(tmp_path)
        qualitative = {"investment_synthesis": {"investment_thesis": "Real layout thesis.", "final_recommendation": "BUY"}}
        self._write_enriched(tmp_path / "output" / "crypto", "BTC-USD", qualitative, final_grade="B")

        result = orchestrator._extract_holdings_insights({"BTC-USD": {}})

        assert result is not None
        assert result["BTC-USD"]["thesis"] == "Real layout thesis."
        assert result["BTC-USD"]["report_link"] == "crypto/BTC-USD_report.html"

    def test_session_dir_takes_precedence_over_asset_dir(self, orchestrator, tmp_path, monkeypatch):
        # Both dirs exist; the session-scoped dir wins (no stale leakage from output/{asset}).
        monkeypatch.chdir(tmp_path)
        self._write_enriched(
            tmp_path / "output" / "enriched" / "default" / "stock",
            "AAPL",
            {"investment_synthesis": {"investment_thesis": "Session thesis.", "final_recommendation": "BUY"}},
        )
        self._write_enriched(
            tmp_path / "output" / "stock",
            "AAPL",
            {"investment_synthesis": {"investment_thesis": "Stale asset-dir thesis.", "final_recommendation": "SELL"}},
        )

        result = orchestrator._extract_holdings_insights({"AAPL": {}})

        assert result is not None
        assert result["AAPL"]["thesis"] == "Session thesis."

    def test_returns_none_when_no_deep_analysis(self, orchestrator):
        assert orchestrator._extract_holdings_insights(None) is None


class TestRecordFilteringToHoldings:
    """_filter_records_to_holdings drops stale tickers left in output/{asset_class}."""

    @staticmethod
    def _review(*tickers: str) -> PortfolioReview:
        from datetime import datetime

        from finwiz.schemas.common import RiskAssessmentStandardized

        holdings = [
            HoldingDecision(
                ticker=t,
                name=t,
                asset_class="stock",
                currency="USD",
                decision="KEEP",
                grade="A",
                composite_score=0.8,
                grade_description="x",
                recommended_action="Keep",
                risk=RiskAssessmentStandardized(score=2.0, level="Low"),
                rationale_bullets=["x"],
            )
            for t in tickers
        ]
        return PortfolioReview(as_of=datetime.now(), holdings=holdings)

    def test_drops_records_not_in_portfolio(self):
        records = [("stock", {"ticker": "AAPL"}), ("stock", {"ticker": "STALE"}), ("stock", {"ticker": "MSFT"})]
        kept = ReportingOrchestrator._filter_records_to_holdings(records, self._review("AAPL", "MSFT"))
        assert [d["ticker"] for _ac, d in kept] == ["AAPL", "MSFT"]

    def test_no_filter_when_portfolio_has_no_tickers(self):
        records = [("stock", {"ticker": "AAPL"}), ("stock", {"ticker": "STALE"})]
        kept = ReportingOrchestrator._filter_records_to_holdings(records, self._review())
        assert len(kept) == 2

    def test_accepts_iterator_input(self):
        records = iter([("stock", {"ticker": "AAPL"}), ("stock", {"ticker": "GONE"})])
        kept = ReportingOrchestrator._filter_records_to_holdings(records, self._review("AAPL"))
        assert [d["ticker"] for _ac, d in kept] == ["AAPL"]


class TestSentimentAndStrategicExtraction:
    """Regression: sentiment + strategic extractors must read the canonical output/{asset_class}.

    Both previously scanned only output/enriched/... (never created on a real
    kickoff), so the Sentiment and Strategic Posture sections silently vanished.
    They now share _iter_enriched_records with the insights extractor.
    """

    @pytest.fixture
    def orchestrator(self):
        return ReportingOrchestrator(FinwizState())

    @staticmethod
    def _write(base, ticker: str, payload: dict) -> None:
        base.mkdir(parents=True, exist_ok=True)
        (base / f"{ticker}_enriched.json").write_text(json.dumps({"ticker": ticker, **payload}))

    def test_sentiment_reads_canonical_asset_dir(self, orchestrator, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self._write(
            tmp_path / "output" / "stock",
            "AAPL",
            {"sentiment_summary": {"score": 0.4, "confidence": 0.8, "article_count": 5}},
        )

        result = orchestrator._extract_holdings_sentiment({"AAPL": {}})

        assert result is not None
        assert result["AAPL"]["score"] == 0.4

    def test_strategic_reads_canonical_asset_dir(self, orchestrator, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self._write(
            tmp_path / "output" / "etf",
            "SPY",
            {"qualitative": {"strategic_analysis": {"swot": {"strengths": ["Liquidity"]}}}},
        )

        result = orchestrator._extract_holdings_strategic({"SPY": {}})

        assert result is not None
        assert result["SPY"]["swot"]["strengths"] == ["Liquidity"]

    def test_session_dir_preferred_for_sentiment(self, orchestrator, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self._write(tmp_path / "output" / "enriched" / "default" / "stock", "AAPL", {"sentiment_summary": {"score": 0.9}})
        self._write(tmp_path / "output" / "stock", "AAPL", {"sentiment_summary": {"score": -0.9}})

        result = orchestrator._extract_holdings_sentiment({"AAPL": {}})

        assert result is not None
        assert result["AAPL"]["score"] == 0.9  # session dir wins, no stale leakage

    def test_both_return_none_without_deep_analysis(self, orchestrator):
        assert orchestrator._extract_holdings_sentiment(None) is None
        assert orchestrator._extract_holdings_strategic(None) is None

    def test_iter_enriched_records_skips_unreadable_files(self, orchestrator, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        base = tmp_path / "output" / "crypto"
        base.mkdir(parents=True, exist_ok=True)
        (base / "BTC-USD_enriched.json").write_text("{not valid json")
        (base / "ETH-USD_enriched.json").write_text(json.dumps({"ticker": "ETH-USD", "sentiment_summary": {"score": 0.1}}))

        result = orchestrator._extract_holdings_sentiment({"BTC-USD": {}, "ETH-USD": {}})

        # Bad file skipped (fail-soft); good file still surfaced.
        assert result is not None
        assert set(result.keys()) == {"ETH-USD"}


class TestSynthesizePortfolioStrategicCoverage:
    """_synthesize_portfolio_strategic must compute honest coverage, never fabricate it.

    Regression: after strategic.py made holdings_covered/holdings_total/
    value_covered_pct required, this method's only production caller
    (synthesize_portfolio_posture_sync(holdings_models)) called it with none
    of the new required kwargs. Because the whole method body was wrapped in
    a bare `except Exception: ... return None`, that TypeError was logged as
    "non-fatal" and the report silently lost its entire strategic posture
    section — every single run, with no visible failure.

    These tests exercise the fix through the real ``ReportingOrchestrator``
    (real logger, real mixin composition) using ``portfolio_review.holdings``
    — the authoritative source for both the coverage denominator and the
    per-holding EUR values that make ``value_covered_pct`` honest. The bare
    ``ReportEnrichmentMixin`` + stubbed-logger variant of these same
    scenarios lives in ``tests/unit/orchestrators/test_posture_coverage_wiring.py``.
    """

    @pytest.fixture
    def orchestrator(self):
        return ReportingOrchestrator(FinwizState())

    @staticmethod
    def _sa_dict(score: float = 0.6) -> dict:
        return {"swot": {"strategic_score": score, "confidence": 0.7}}

    @classmethod
    def _record(cls, ticker: str, with_strategic: bool = True) -> tuple[str, dict]:
        data: dict = {"ticker": ticker}
        if with_strategic:
            data["qualitative"] = {"strategic_analysis": cls._sa_dict()}
        return ("stock", data)

    @classmethod
    def _records(cls, *tickers: str) -> list[tuple[str, dict]]:
        """Every ticker carries a valid strategic_analysis (fully covered)."""
        return [cls._record(t) for t in tickers]

    @staticmethod
    def _holding(ticker: str, *, eur_value: float | None = None) -> HoldingDecision:
        from finwiz.schemas.common import RiskAssessmentStandardized

        return HoldingDecision(
            ticker=ticker,
            name=f"{ticker} Inc.",
            asset_class="stock",
            currency="USD",
            decision="KEEP",
            composite_score=0.7,
            grade="B",
            grade_description="Solide",
            recommended_action="Conserver",
            risk=RiskAssessmentStandardized(score=2.0, level="Medium"),
            eur_value=eur_value,
        )

    def _mock_synthesize(self, mocker):
        """Patch the real Perplexity call and capture the kwargs it was called with."""
        captured: dict = {}

        def _fake(_holdings_models, **kwargs):
            captured.update(kwargs)
            from finwiz.schemas.hybrid_analysis.strategic import PortfolioStrategicPosture

            return PortfolioStrategicPosture(
                competitive_verdict="c",
                swot_verdict="s",
                strategic_score=0.6,
                confidence=0.6,
                holdings_covered=kwargs["holdings_covered"],
                holdings_total=kwargs["holdings_total"],
                value_covered_pct=kwargs["value_covered_pct"],
                uncovered_tickers=kwargs.get("uncovered_tickers") or [],
            )

        mocker.patch("finwiz.analysis.strategic_research.synthesize_portfolio_posture_sync", side_effect=_fake)
        return captured

    def test_value_weighted_coverage_from_real_portfolio_holdings(self, orchestrator, mocker):
        """holdings_total/uncovered/value_covered_pct all come from portfolio_review.holdings."""
        captured = self._mock_synthesize(mocker)
        deep_analysis_results = {"total_holdings": 3}
        records = self._records("AAPL")
        holdings = [self._holding("AAPL", eur_value=900.0), self._holding("MSFT", eur_value=50.0), self._holding("TSLA", eur_value=50.0)]

        result = orchestrator._synthesize_portfolio_strategic(deep_analysis_results, records=records, holdings=holdings)

        assert result is not None
        assert captured["holdings_covered"] == 1
        assert captured["holdings_total"] == 3
        assert sorted(captured["uncovered_tickers"]) == ["MSFT", "TSLA"]
        # AAPL (covered) is 900 of 1000 total EUR -> 90%, not the 33% count-based ratio.
        assert captured["value_covered_pct"] == pytest.approx(90.0)

    def test_never_reports_full_coverage_when_holdings_are_missing(self, orchestrator, mocker):
        """The exact defect being fixed: holdings_total must never equal holdings_covered
        when there is a real, known gap — that would silently claim 100%."""
        captured = self._mock_synthesize(mocker)
        deep_analysis_results = {"total_holdings": 5}
        records = self._records("AAPL")
        holdings = [self._holding(t) for t in ("AAPL", "MSFT", "TSLA", "NVDA", "AMZN")]

        orchestrator._synthesize_portfolio_strategic(deep_analysis_results, records=records, holdings=holdings)

        assert captured["holdings_total"] != captured["holdings_covered"]
        assert captured["holdings_total"] == 5

    def test_falls_back_to_count_ratio_without_priced_holdings(self, orchestrator, mocker):
        """No holding in the portfolio has an eur_value: value_covered_pct degrades to the
        honest count-based ratio, logged loudly, never fabricated as 100%."""
        captured = self._mock_synthesize(mocker)
        deep_analysis_results = {"total_holdings": 2}
        records = [self._record("AAPL", with_strategic=True), self._record("MSFT", with_strategic=False)]
        holdings = [self._holding("AAPL"), self._holding("MSFT")]
        warning = mocker.patch.object(orchestrator.logger, "warning")

        orchestrator._synthesize_portfolio_strategic(deep_analysis_results, records=records, holdings=holdings)

        assert captured["holdings_covered"] == 1  # only AAPL carries strategic_analysis
        assert captured["holdings_total"] == 2
        assert captured["uncovered_tickers"] == ["MSFT"]
        assert captured["value_covered_pct"] == pytest.approx(50.0)
        assert warning.called

    def test_type_error_from_synthesis_call_propagates_not_swallowed(self, orchestrator, mocker):
        """A programming error (wrong signature, wrong attribute) must surface as a loud
        failure, not be logged as 'non-fatal' and silently drop the whole section — that
        is exactly how the missing-kwargs regression went unnoticed."""
        mocker.patch("finwiz.analysis.strategic_research.synthesize_portfolio_posture_sync", side_effect=TypeError("missing 3 required keyword-only arguments"))
        deep_analysis_results = {"total_holdings": 1}
        records = self._records("AAPL")
        holdings = [self._holding("AAPL")]

        with pytest.raises(TypeError):
            orchestrator._synthesize_portfolio_strategic(deep_analysis_results, records=records, holdings=holdings)

    def test_attribute_error_from_synthesis_call_propagates_not_swallowed(self, orchestrator, mocker):
        mocker.patch("finwiz.analysis.strategic_research.synthesize_portfolio_posture_sync", side_effect=AttributeError("boom"))
        deep_analysis_results = {"total_holdings": 1}
        records = self._records("AAPL")
        holdings = [self._holding("AAPL")]

        with pytest.raises(AttributeError):
            orchestrator._synthesize_portfolio_strategic(deep_analysis_results, records=records, holdings=holdings)

    def test_genuine_runtime_failure_still_returns_none(self, orchestrator, mocker):
        """API-down/parse-error style failures must remain best-effort: None, report still renders."""
        mocker.patch("finwiz.analysis.strategic_research.synthesize_portfolio_posture_sync", side_effect=ConnectionError("Perplexity unreachable"))
        deep_analysis_results = {"total_holdings": 1}
        records = self._records("AAPL")
        holdings = [self._holding("AAPL")]

        result = orchestrator._synthesize_portfolio_strategic(deep_analysis_results, records=records, holdings=holdings)

        assert result is None


class TestEmptyStrategicAnalysisIsNotCoverage:
    """An all-``None`` StrategicAnalysis is the absence of evidence, not coverage.

    ``gather_strategic_analysis`` used to return
    ``StrategicAnalysis(swot=None, five_forces=None)`` after both Perplexity
    calls failed. That blob is a truthy dict on disk, it
    validates cleanly (both fields are Optional), and it therefore entered
    ``holdings_models`` and ``covered_tickers`` — so a total provider outage
    rendered "64 / 64 holdings · 100.0 %" in green above a score the model was
    forced to invent from ``{"T0": {}, "T1": {}, ...}``.

    Layer 1 (returning ``None`` from the gather) stops new blobs being written.
    This layer stops legacy ``*_enriched.json`` already on disk from counting.
    The predicate is the one the codebase already trusts for this exact
    question: ``StrategicAnalysis.composite_strategic_score is None`` — the same
    guard ``stages/synthesize.py`` uses before recomputing a holding's grade.

    The existing coverage tests above only ever use records where
    ``strategic_analysis`` is *absent*; present-but-empty is the gap that let
    this through.
    """

    @pytest.fixture
    def orchestrator(self):
        return ReportingOrchestrator(FinwizState())

    @staticmethod
    def _empty_record(ticker: str) -> tuple[str, dict]:
        """What a fully-failed strategic gather wrote to disk."""
        return ("stock", {"ticker": ticker, "qualitative": {"strategic_analysis": {"swot": None, "five_forces": None}}})

    @staticmethod
    def _partial_record(ticker: str) -> tuple[str, dict]:
        """One framework of two succeeded — real evidence, must still count."""
        return ("stock", {"ticker": ticker, "qualitative": {"strategic_analysis": {"swot": {"strategic_score": 0.62, "confidence": 0.7}, "five_forces": None}}})

    _holding = staticmethod(TestSynthesizePortfolioStrategicCoverage._holding)
    _mock_synthesize = TestSynthesizePortfolioStrategicCoverage._mock_synthesize

    def test_total_outage_reports_zero_coverage_not_full_coverage(self, orchestrator, mocker):
        """64 holdings, every strategic_analysis all-None: nothing is covered."""
        self._mock_synthesize(mocker)
        tickers = [f"T{i}" for i in range(64)]
        records = [self._empty_record(t) for t in tickers]
        holdings = [self._holding(t, eur_value=100.0) for t in tickers]

        result = orchestrator._synthesize_portfolio_strategic({"total_holdings": 64}, records=records, holdings=holdings)

        # No holding carries evidence, so there is nothing to synthesize a
        # posture from. Today layer 2 returns None before the synthesis call;
        # this outer assertion keeps the test from going vacuous if that ever
        # changes. If a posture were produced anyway it must name all 64 as
        # uncovered and claim zero coverage — never 64/64 · 100 %.
        assert result is None or result["holdings_covered"] == 0
        if result is not None:
            assert result["holdings_covered"] == 0
            assert result["value_covered_pct"] == 0.0
            assert sorted(result["uncovered_tickers"]) == sorted(tickers)

    def test_total_outage_never_reaches_the_paid_synthesis_call(self, orchestrator, mocker):
        """Zero evidence must not buy a synthesis call over 64 empty objects."""
        synthesize = mocker.patch("finwiz.analysis.strategic_research.synthesize_portfolio_posture_sync")
        tickers = [f"T{i}" for i in range(64)]
        records = [self._empty_record(t) for t in tickers]
        holdings = [self._holding(t, eur_value=100.0) for t in tickers]

        assert orchestrator._synthesize_portfolio_strategic({"total_holdings": 64}, records=records, holdings=holdings) is None
        synthesize.assert_not_called()

    def test_empty_holdings_are_excluded_from_coverage_alongside_real_ones(self, orchestrator, mocker):
        """Mixed run: one real blob, two empty ones. Coverage is 1/3, not 3/3."""
        captured = self._mock_synthesize(mocker)
        records = [self._partial_record("AAPL"), self._empty_record("MSFT"), self._empty_record("TSLA")]
        holdings = [self._holding("AAPL", eur_value=900.0), self._holding("MSFT", eur_value=50.0), self._holding("TSLA", eur_value=50.0)]

        orchestrator._synthesize_portfolio_strategic({"total_holdings": 3}, records=records, holdings=holdings)

        assert captured["holdings_covered"] == 1
        assert captured["holdings_total"] == 3
        assert sorted(captured["uncovered_tickers"]) == ["MSFT", "TSLA"]
        assert captured["value_covered_pct"] == pytest.approx(90.0)

    def test_a_partial_strategic_analysis_still_counts_as_covered(self, orchestrator, mocker):
        """Some frameworks present, some None: real evidence, real coverage.

        Only *no* evidence must be excluded. Dropping partials would trade the
        wrong-data failure for the lost-data one.
        """
        captured = self._mock_synthesize(mocker)
        records = [self._partial_record("AAPL"), self._partial_record("MSFT")]
        holdings = [self._holding("AAPL", eur_value=500.0), self._holding("MSFT", eur_value=500.0)]

        orchestrator._synthesize_portfolio_strategic({"total_holdings": 2}, records=records, holdings=holdings)

        assert captured["holdings_covered"] == 2
        assert captured["uncovered_tickers"] == []
        assert captured["value_covered_pct"] == pytest.approx(100.0)

    def test_the_exclusion_is_logged_loudly(self, orchestrator, mocker):
        """A holding dropped from coverage is a real degradation; it is not silent."""
        self._mock_synthesize(mocker)
        warning = mocker.patch.object(orchestrator.logger, "warning")
        records = [self._partial_record("AAPL"), self._empty_record("MSFT")]
        holdings = [self._holding("AAPL", eur_value=500.0), self._holding("MSFT", eur_value=500.0)]

        orchestrator._synthesize_portfolio_strategic({"total_holdings": 2}, records=records, holdings=holdings)

        assert any("MSFT" in str(call) for call in warning.call_args_list)


class TestFailedSynthesisIsLoggedLoudly:
    """Losing the whole posture is a degradation, not an incidental info line.

    A truncated or partial model response now fails validation on the five
    required narrative fields and drops the entire posture. That was logged at
    ``info``, indistinguishable from routine progress chatter in a run that
    produces thousands of lines.
    """

    @pytest.fixture
    def orchestrator(self):
        return ReportingOrchestrator(FinwizState())

    _records = TestSynthesizePortfolioStrategicCoverage._records
    _record = TestSynthesizePortfolioStrategicCoverage._record
    _sa_dict = staticmethod(TestSynthesizePortfolioStrategicCoverage._sa_dict)
    _holding = staticmethod(TestSynthesizePortfolioStrategicCoverage._holding)

    def test_a_none_posture_from_synthesis_logs_at_warning(self, orchestrator, mocker):
        mocker.patch("finwiz.analysis.strategic_research.synthesize_portfolio_posture_sync", return_value=None)
        warning = mocker.patch.object(orchestrator.logger, "warning")
        records = self._records("AAPL")
        holdings = [self._holding("AAPL")]

        assert orchestrator._synthesize_portfolio_strategic({"total_holdings": 1}, records=records, holdings=holdings) is None
        assert any("posture" in str(call).lower() for call in warning.call_args_list)


class TestIterEnrichedFiles:
    """_iter_enriched_files is the shared directory resolver (paths, not parsed dicts)."""

    @pytest.fixture
    def orchestrator(self):
        return ReportingOrchestrator(FinwizState())

    @staticmethod
    def _touch(base, ticker: str) -> None:
        base.mkdir(parents=True, exist_ok=True)
        (base / f"{ticker}_enriched.json").write_text(json.dumps({"ticker": ticker}))

    def test_yields_paths_from_canonical_asset_dir(self, orchestrator, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self._touch(tmp_path / "output" / "crypto", "BTC-USD")

        results = list(orchestrator._iter_enriched_files())

        assert len(results) == 1
        asset_class, path = results[0]
        assert asset_class == "crypto"
        assert path.name == "BTC-USD_enriched.json"
        # Records iterator (built on top) still parses the same file.
        assert orchestrator._extract_holdings_insights({"BTC-USD": {}}) is None  # no qualitative payload

    def test_first_existing_dir_wins(self, orchestrator, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self._touch(tmp_path / "output" / "enriched" / "default" / "stock", "AAPL")
        self._touch(tmp_path / "output" / "stock", "STALE")  # lower priority, ignored

        tickers = {p.name for _ac, p in orchestrator._iter_enriched_files()}

        assert tickers == {"AAPL_enriched.json"}

    def test_empty_when_no_dirs(self, orchestrator, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert list(orchestrator._iter_enriched_files()) == []


class TestGenerateEnrichedHtmlReports:
    """generate_enriched_html_reports now resolves files via _iter_enriched_files.

    Regression: it previously scanned only output/enriched/... so a real kickoff
    (which writes to output/{asset_class}) produced nothing.
    """

    @pytest.fixture
    def orchestrator(self):
        return ReportingOrchestrator(FinwizState())

    def test_generates_from_canonical_asset_dir(self, orchestrator, tmp_path, monkeypatch, mocker):
        monkeypatch.chdir(tmp_path)
        base = tmp_path / "output" / "stock"
        base.mkdir(parents=True, exist_ok=True)
        (base / "AAPL_enriched.json").write_text(json.dumps({"ticker": "AAPL"}))

        # Stub the report generator so we don't depend on Jinja templates.
        mock_gen = mocker.Mock()
        mocker.patch(
            "finwiz.reporting.enriched_analysis_report_generator.EnrichedAnalysisReportGenerator",
            return_value=mock_gen,
        )

        result = orchestrator.generate_enriched_html_reports()

        assert "stock" in result
        assert [p.name for p in result["stock"]] == ["AAPL_enriched.html"]
        mock_gen.generate_and_save_report.assert_called_once()

    def test_counts_failures_fail_soft(self, orchestrator, tmp_path, monkeypatch, mocker):
        monkeypatch.chdir(tmp_path)
        base = tmp_path / "output" / "etf"
        base.mkdir(parents=True, exist_ok=True)
        (base / "SPY_enriched.json").write_text("{not valid json")

        mocker.patch(
            "finwiz.reporting.enriched_analysis_report_generator.EnrichedAnalysisReportGenerator",
            return_value=mocker.Mock(),
        )

        # Bad JSON is caught per-file; no asset entry, no raise.
        assert orchestrator.generate_enriched_html_reports() == {}


class TestHTMLAutoGeneration:
    """Tests for HTML auto-generation functionality."""

    @pytest.fixture
    def state(self):
        """Create a FinwizState instance for testing."""
        return FinwizState()

    @pytest.fixture
    def orchestrator(self, state):
        """Create a ReportingOrchestrator instance for testing."""
        return ReportingOrchestrator(state)

    def test_should_generate_crew_html_report(self, orchestrator, tmp_path, mocker):
        """Test generating HTML report for a single crew export."""
        # Arrange
        export_file = tmp_path / "AAPL_export.json"
        export_data = {"ticker": "AAPL", "grade": "A", "composite_score": 0.85}
        export_file.write_text(json.dumps(export_data))

        # Mock the generator
        mock_generator = mocker.Mock()
        mock_generator.generate_report.return_value = "<html>test</html>"
        mocker.patch(
            "finwiz.orchestrators.reporting.crew_html.get_generator_for_crew",
            return_value=mock_generator,
        )

        # Act
        result = orchestrator.generate_crew_html_report("stock_crew", str(export_file))

        # Assert
        assert result is not None
        assert result.suffix == ".html"
        mock_generator.generate_report.assert_called_once()

    def test_should_return_none_when_no_generator_for_crew(self, orchestrator, tmp_path, mocker):
        """Test returns None when no generator is registered for crew."""
        # Arrange
        export_file = tmp_path / "test_export.json"
        export_file.write_text(json.dumps({"ticker": "TEST"}))

        mocker.patch(
            "finwiz.orchestrators.reporting.crew_html.get_generator_for_crew",
            return_value=None,
        )

        # Act
        result = orchestrator.generate_crew_html_report("unknown_crew", str(export_file))

        # Assert
        assert result is None

    def test_should_return_none_when_export_file_missing(self, orchestrator, mocker):
        """Test returns None when export file doesn't exist."""
        # Arrange
        nonexistent_path = "/nonexistent/path/export.json"

        # Act
        result = orchestrator.generate_crew_html_report("stock_crew", nonexistent_path)

        # Assert
        assert result is None

    def test_should_handle_generator_error_gracefully(self, orchestrator, tmp_path, mocker):
        """Test handles generator errors gracefully."""
        # Arrange
        export_file = tmp_path / "AAPL_export.json"
        export_file.write_text(json.dumps({"ticker": "AAPL"}))

        mock_generator = mocker.Mock()
        mock_generator.generate_report.side_effect = Exception("Template error")
        mocker.patch(
            "finwiz.orchestrators.reporting.crew_html.get_generator_for_crew",
            return_value=mock_generator,
        )

        # Act
        result = orchestrator.generate_crew_html_report("stock_crew", str(export_file))

        # Assert
        assert result is None

    def test_should_generate_all_crew_html_reports(self, orchestrator, tmp_path, mocker):
        """Test batch generation of HTML reports for all crews."""
        # Arrange
        stock_file = tmp_path / "AAPL_export.json"
        stock_file.write_text(json.dumps({"ticker": "AAPL"}))

        etf_file = tmp_path / "SPY_export.json"
        etf_file.write_text(json.dumps({"ticker": "SPY"}))

        crew_export_paths = {
            "stock_crew": [str(stock_file)],
            "etf_crew": [str(etf_file)],
        }

        mock_generator = mocker.Mock()
        mock_generator.generate_report.return_value = "<html>test</html>"
        mocker.patch(
            "finwiz.orchestrators.reporting.crew_html.get_generator_for_crew",
            return_value=mock_generator,
        )

        # Act
        result = orchestrator.generate_all_crew_html_reports(crew_export_paths)

        # Assert
        assert "stock_crew" in result
        assert "etf_crew" in result
        assert len(result["stock_crew"]) == 1
        assert len(result["etf_crew"]) == 1
        assert mock_generator.generate_report.call_count == 2

    def test_should_count_generated_and_failed_reports(self, orchestrator, tmp_path, mocker):
        """Test counting of generated vs failed reports."""
        # Arrange
        success_file = tmp_path / "AAPL_export.json"
        success_file.write_text(json.dumps({"ticker": "AAPL"}))

        crew_export_paths = {
            "stock_crew": [str(success_file), "/nonexistent/file.json"],
        }

        mock_generator = mocker.Mock()
        mock_generator.generate_report.return_value = "<html>test</html>"
        mocker.patch(
            "finwiz.orchestrators.reporting.crew_html.get_generator_for_crew",
            return_value=mock_generator,
        )

        # Act
        result = orchestrator.generate_all_crew_html_reports(crew_export_paths)

        # Assert
        # One file should succeed, one should fail (nonexistent)
        assert "stock_crew" in result
        assert len(result["stock_crew"]) == 1

    def test_consolidate_reports_should_auto_generate_html(self, orchestrator, tmp_path, mocker):
        """Test that consolidate_reports auto-generates HTML when enabled."""
        # Arrange
        export_file = tmp_path / "AAPL_export.json"
        export_file.write_text(json.dumps({"ticker": "AAPL", "grade": "A"}))

        crew_export_paths = {"stock_crew": [str(export_file)]}

        mock_generator = mocker.Mock()
        mock_generator.generate_report.return_value = "<html>test</html>"
        mocker.patch(
            "finwiz.orchestrators.reporting.crew_html.get_generator_for_crew",
            return_value=mock_generator,
        )

        # Act
        result = orchestrator.consolidate_reports(crew_export_paths, generate_html=True)

        # Assert
        assert result["success"] is True
        assert "html_report_paths" in result
        assert "stock_crew" in result["html_report_paths"]
        mock_generator.generate_report.assert_called_once()

    def test_consolidate_reports_should_skip_html_when_disabled(self, orchestrator, tmp_path, mocker):
        """Test that consolidate_reports skips HTML generation when disabled."""
        # Arrange
        export_file = tmp_path / "AAPL_export.json"
        export_file.write_text(json.dumps({"ticker": "AAPL", "grade": "A"}))

        crew_export_paths = {"stock_crew": [str(export_file)]}

        mock_generator = mocker.Mock()
        mock_generator.generate_report.return_value = "<html>test</html>"
        mocker.patch(
            "finwiz.orchestrators.reporting.crew_html.get_generator_for_crew",
            return_value=mock_generator,
        )

        # Act
        result = orchestrator.consolidate_reports(crew_export_paths, generate_html=False)

        # Assert
        assert result["success"] is True
        assert result["html_report_paths"] == {}
        mock_generator.generate_report.assert_not_called()

    def test_consolidate_reports_should_include_html_count_in_consolidated_data(self, orchestrator, tmp_path, mocker):
        """Test that consolidate_reports includes HTML generation count."""
        # Arrange
        stock_file = tmp_path / "AAPL_export.json"
        stock_file.write_text(json.dumps({"ticker": "AAPL"}))

        etf_file = tmp_path / "SPY_export.json"
        etf_file.write_text(json.dumps({"ticker": "SPY"}))

        crew_export_paths = {
            "stock_crew": [str(stock_file)],
            "etf_crew": [str(etf_file)],
        }

        mock_generator = mocker.Mock()
        mock_generator.generate_report.return_value = "<html>test</html>"
        mocker.patch(
            "finwiz.orchestrators.reporting.crew_html.get_generator_for_crew",
            return_value=mock_generator,
        )

        # Act
        result = orchestrator.consolidate_reports(crew_export_paths, generate_html=True)

        # Assert
        assert result["consolidated_data"]["html_reports_generated"] == 2
