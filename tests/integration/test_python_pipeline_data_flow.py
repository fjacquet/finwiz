#!/usr/bin/env python3
"""
Data Flow Validation Tests for Pure Python Pipeline.

Tests that data flows correctly between components and that downstream processes
can access the generated data properly.

Requirements: 0.11, 0.12, 0.16, 0.17, 0.20, 0.21, 0.25, 0.26
"""

import json
import time
from pathlib import Path

import pytest

from finwiz.integration.aplus_discovery_integrator import integrate_aplus_discovery_with_deep_analysis
from finwiz.integration.backtesting_pipeline_connector import connect_backtesting_to_discovery_results
from finwiz.reporting.python_report_generator import generate_python_report
from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview, RiskAssessment
from finwiz.scoring.portfolio_deep_analyzer import analyze_portfolio_with_python


class TestPythonPipelineDataFlow:
    """Data flow validation tests for the pure Python pipeline."""

    @pytest.fixture
    def aplus_portfolio_holdings(self) -> list[HoldingDecision]:
        """Create portfolio with A+ holdings to test discovery and backtesting."""
        return [
            HoldingDecision(
                ticker="NVDA",
                name="NVIDIA Corporation",
                asset_class="stock",
                currency="USD",
                decision="KEEP",
                composite_score=0.92,
                grade="A+",
                grade_description="Grade A+ - Exceptional AI leader",
                recommended_action="BUY",
                rationale_bullets=["AI market leader", "Strong growth", "Excellent margins"],
                risk=RiskAssessment(score=2.8, level="Medium", risk_factors=["Tech volatility", "Competition"]),
                alternatives=[],
            ),
            HoldingDecision(
                ticker="TSLA",
                name="Tesla Inc.",
                asset_class="stock",
                currency="USD",
                decision="KEEP",
                composite_score=0.89,
                grade="A+",
                grade_description="Grade A+ - EV innovation leader",
                recommended_action="BUY",
                rationale_bullets=["EV market leader", "Innovation", "Strong brand"],
                risk=RiskAssessment(score=3.2, level="Medium-High", risk_factors=["Volatility", "Regulatory risk"]),
                alternatives=[],
            ),
            HoldingDecision(
                ticker="QQQ",
                name="Invesco QQQ Trust",
                asset_class="etf",
                currency="USD",
                decision="KEEP",
                composite_score=0.85,
                grade="A",
                grade_description="Grade A - Strong tech ETF",
                recommended_action="BUY",
                rationale_bullets=["Tech exposure", "Low fees", "Liquidity"],
                risk=RiskAssessment(score=2.5, level="Medium", risk_factors=["Tech concentration", "Market risk"]),
                alternatives=[],
            ),
            HoldingDecision(
                ticker="ETH",
                name="Ethereum",
                asset_class="crypto",
                currency="USD",
                decision="KEEP",
                composite_score=0.88,
                grade="A+",
                grade_description="Grade A+ - Leading smart contract platform",
                recommended_action="BUY",
                rationale_bullets=["Smart contracts", "DeFi ecosystem", "Network effects"],
                risk=RiskAssessment(score=4.2, level="High", risk_factors=["Crypto volatility", "Regulatory uncertainty"]),
                alternatives=[],
            ),
            HoldingDecision(
                ticker="F",
                name="Ford Motor Company",
                asset_class="stock",
                currency="USD",
                decision="SELL",
                composite_score=0.42,
                grade="D",
                grade_description="Grade D - Struggling traditional automaker",
                recommended_action="SELL",
                rationale_bullets=["Declining margins", "EV transition challenges", "Debt concerns"],
                risk=RiskAssessment(score=3.8, level="High", risk_factors=["Industry disruption", "Financial stress"]),
                alternatives=[],
            ),
        ]

    @pytest.fixture
    def session_id(self) -> str:
        """Generate unique session ID for data flow testing."""
        return f"dataflow_test_{int(time.time())}"

    @pytest.fixture
    def cleanup_output_files(self, session_id):
        """Clean up output files after test."""
        yield

        # Clean up test files
        output_dir = Path("output")
        if output_dir.exists():
            for pattern in [f"*{session_id}*"]:
                for file_path in output_dir.rglob(pattern):
                    try:
                        file_path.unlink()
                    except FileNotFoundError:
                        pass

    def test_should_verify_json_exports_accessible_to_downstream(self, aplus_portfolio_holdings, session_id, cleanup_output_files):
        """
        Test that JSON exports are accessible to downstream processes.

        Requirements: 0.11, 0.12 - Verify JSON exports accessible to downstream processes
        """
        # Execute deep analysis
        analysis_results = analyze_portfolio_with_python(holdings=aplus_portfolio_holdings, session_id=session_id)

        # Verify export structure exists
        output_dir = Path("output")
        assert output_dir.exists()

        # Check that files are created in proper directories
        expected_files = {"stock": ["NVDA", "TSLA", "F"], "etf": ["QQQ"], "crypto": ["ETH"]}

        for asset_class, expected_tickers in expected_files.items():
            asset_dir = output_dir / asset_class
            assert asset_dir.exists(), f"{asset_class} directory should exist"

            # Verify files for each ticker
            for ticker in expected_tickers:
                ticker_files = list(asset_dir.glob(f"{ticker}_{session_id}.json"))
                assert len(ticker_files) == 1, f"Should have exactly one file for {ticker}"

                # Verify file is readable and contains valid data
                ticker_file = ticker_files[0]
                with open(ticker_file, encoding="utf-8") as f:
                    ticker_data = json.load(f)

                # Verify required fields for downstream processing
                assert ticker_data["ticker"] == ticker
                assert "grade" in ticker_data
                assert "composite_score" in ticker_data
                assert "asset_class" in ticker_data
                assert ticker_data["asset_class"] == asset_class

        # Verify consolidated export
        consolidated_path = output_dir / f"deep_analysis_consolidated_{session_id}.json"
        assert consolidated_path.exists()

        with open(consolidated_path, encoding="utf-8") as f:
            consolidated_data = json.load(f)

        assert "session_id" in consolidated_data
        assert consolidated_data["session_id"] == session_id
        assert "analyses" in consolidated_data
        assert len(consolidated_data["analyses"]) == len(aplus_portfolio_holdings)

        print("✅ JSON Export Accessibility Verified:")
        print(f"   📁 Output directories created: {len(expected_files)}")
        print(f"   📄 Individual files created: {sum(len(tickers) for tickers in expected_files.values())}")
        print(f"   📋 Consolidated export created: {consolidated_path.exists()}")

    def test_should_show_actual_aplus_opportunities_not_zero(self, aplus_portfolio_holdings, session_id, cleanup_output_files):
        """
        Test that A+ discovery shows actual opportunities (not 0).

        Requirements: 0.16, 0.17 - Test A+ discovery shows actual opportunities (not 0)
        """
        # Execute deep analysis first
        analysis_results = analyze_portfolio_with_python(holdings=aplus_portfolio_holdings, session_id=session_id)

        # Execute A+ discovery integration
        discovery_results = integrate_aplus_discovery_with_deep_analysis(session_id)

        # Should find A+ opportunities (NVDA, TSLA, ETH have A+ grades, QQQ has A)
        assert discovery_results["has_a_plus_analysis"] is True, "Should detect A+ analysis exists"
        assert discovery_results["total_opportunities_found"] >= 3, (
            f"Should find ≥3 A+ opportunities, found {discovery_results['total_opportunities_found']}"
        )

        # Verify specific A+ holdings are identified
        aplus_tickers = [h["ticker"] for h in discovery_results["aplus_holdings"]]

        # Should find A+ grade holdings
        assert "NVDA" in aplus_tickers, "Should identify NVDA as A+ opportunity"
        assert "TSLA" in aplus_tickers, "Should identify TSLA as A+ opportunity"
        assert "ETH" in aplus_tickers, "Should identify ETH as A+ opportunity"
        assert "QQQ" in aplus_tickers, "Should identify QQQ as A opportunity"

        # Should NOT find D grade holdings
        assert "F" not in aplus_tickers, "Should NOT identify F (Grade D) as A+ opportunity"

        # Verify opportunity details
        for holding in discovery_results["aplus_holdings"]:
            assert holding["grade"] in ["A+", "A"], f"All opportunities should be A+ or A grade, found {holding['grade']}"
            assert holding["composite_score"] >= 0.80, (
                f"A+ opportunities should have high scores, {holding['ticker']} has {holding['composite_score']}"
            )
            assert "analysis_file" in holding, "Should reference source analysis file"

        print("✅ A+ Discovery Results:")
        print(f"   🎯 A+ opportunities found: {discovery_results['total_opportunities_found']}")
        print(f"   📈 A+ tickers: {aplus_tickers}")
        print("   ✅ No false positives (D grade excluded)")

    def test_should_execute_backtesting_when_aplus_candidates_exist(
        self, aplus_portfolio_holdings, session_id, cleanup_output_files
    ):
        """
        Test that backtesting executes when A+ candidates are found.

        Requirements: 0.20, 0.21 - Test backtesting executes and results included in final report
        """
        # Execute deep analysis
        analysis_results = analyze_portfolio_with_python(holdings=aplus_portfolio_holdings, session_id=session_id)

        # Execute A+ discovery
        discovery_results = integrate_aplus_discovery_with_deep_analysis(session_id)

        # Execute backtesting pipeline
        backtesting_results = connect_backtesting_to_discovery_results(session_id)

        # Should execute backtesting since A+ candidates exist
        assert backtesting_results["backtesting_executed"] is True, "Backtesting should execute when A+ candidates exist"
        assert backtesting_results["candidates_count"] >= 3, (
            f"Should have ≥3 candidates, found {backtesting_results['candidates_count']}"
        )

        # Verify backtesting results structure
        assert "results" in backtesting_results
        assert len(backtesting_results["results"]) >= 3

        # Verify each result has required fields
        for result in backtesting_results["results"]:
            assert "ticker" in result
            assert "annual_return" in result
            assert "sharpe_ratio" in result
            assert "max_drawdown" in result
            assert "win_rate" in result
            assert "status" in result
            assert result["status"] == "completed"

            # Verify reasonable performance metrics
            assert -1.0 <= result["annual_return"] <= 2.0, f"Annual return should be reasonable: {result['annual_return']}"
            assert 0.0 <= result["sharpe_ratio"] <= 5.0, f"Sharpe ratio should be reasonable: {result['sharpe_ratio']}"
            assert -1.0 <= result["max_drawdown"] <= 0.0, f"Max drawdown should be negative: {result['max_drawdown']}"
            assert 0.0 <= result["win_rate"] <= 1.0, f"Win rate should be 0-1: {result['win_rate']}"

        # Verify results file is created
        assert "results_file" in backtesting_results
        results_file_path = Path(backtesting_results["results_file"])
        assert results_file_path.exists(), "Backtesting results file should be created"

        # Verify results file contains valid data
        with open(results_file_path, encoding="utf-8") as f:
            file_data = json.load(f)

        assert "candidates" in file_data
        assert "results" in file_data
        assert file_data["session_id"] == session_id

        print("✅ Backtesting Execution Results:")
        print(f"   🔬 Backtesting executed: {backtesting_results['backtesting_executed']}")
        print(f"   📊 Candidates processed: {backtesting_results['candidates_count']}")
        print(f"   📈 Results generated: {len(backtesting_results['results'])}")
        print(f"   📄 Results file created: {results_file_path.exists()}")

    def test_should_generate_final_report_with_actual_data_not_placeholders(
        self, aplus_portfolio_holdings, session_id, cleanup_output_files
    ):
        """
        Test that final report contains real analysis data, not placeholders.

        Requirements: 0.25, 0.26 - Validate final report contains real analysis data, not placeholders
        """
        # Execute complete pipeline
        analysis_results = analyze_portfolio_with_python(holdings=aplus_portfolio_holdings, session_id=session_id)

        discovery_results = integrate_aplus_discovery_with_deep_analysis(session_id)
        backtesting_results = connect_backtesting_to_discovery_results(session_id)

        # Generate final report
        from datetime import datetime

        portfolio_review = PortfolioReview(as_of=datetime.now(), base_currency="USD", holdings=aplus_portfolio_holdings)

        report_path = generate_python_report(
            portfolio_review=portfolio_review, deep_analysis_results=analysis_results, session_id=session_id
        )

        # Verify report was generated
        assert report_path is not None
        report_file = Path(report_path)
        assert report_file.exists(), "Final report should be generated"
        assert report_file.suffix == ".html", "Report should be HTML format"

        # Read and analyze report content
        with open(report_file, encoding="utf-8") as f:
            report_content = f.read()

        # Should contain actual ticker symbols
        expected_tickers = ["NVDA", "TSLA", "QQQ", "ETH", "F"]
        for ticker in expected_tickers:
            assert ticker in report_content, f"Report should contain ticker {ticker}"

        # Should contain actual grades
        assert "A+" in report_content, "Report should show A+ grades"
        assert "Grade A" in report_content or "Grade: A" in report_content, "Report should show A grades"

        # Should NOT contain placeholder text
        placeholder_terms = [
            "TODO",
            "PLACEHOLDER",
            "TBD",
            "Not implemented",
            "Lorem ipsum",
            "Sample data",
            "Test data",
            "Non exécuté",
            "données non fournies",  # French placeholders
        ]

        for placeholder in placeholder_terms:
            assert placeholder not in report_content, f"Report should not contain placeholder: {placeholder}"

        # Should contain performance metrics
        performance_indicators = ["Grade", "Score", "Recommendation", "Risk", "A+", "BUY", "SELL", "HOLD"]

        for indicator in performance_indicators:
            assert indicator in report_content, f"Report should contain performance indicator: {indicator}"

        # Should contain backtesting results (since A+ candidates exist)
        backtesting_indicators = ["Backtesting", "Annual Return", "Sharpe", "Performance"]

        # At least some backtesting indicators should be present
        backtesting_found = sum(1 for indicator in backtesting_indicators if indicator in report_content)
        assert backtesting_found >= 2, f"Report should contain backtesting results, found {backtesting_found} indicators"

        # Should contain A+ discovery results
        discovery_indicators = ["Opportunities", "Discovery", "A+ Analysis"]

        discovery_found = sum(1 for indicator in discovery_indicators if indicator in report_content)
        assert discovery_found >= 1, f"Report should contain discovery results, found {discovery_found} indicators"

        print("✅ Final Report Validation:")
        print(f"   📄 Report generated: {report_file.exists()}")
        print(f"   📊 Contains actual tickers: {len(expected_tickers)}")
        print("   🎯 Contains grades and scores: ✅")
        print("   🚫 No placeholder text: ✅")
        print("   🔬 Contains backtesting results: ✅")
        print("   🔍 Contains discovery results: ✅")
        print(f"   📈 Report size: {len(report_content)} characters")

    def test_should_validate_complete_data_flow_integration(self, aplus_portfolio_holdings, session_id, cleanup_output_files):
        """
        Test complete data flow from analysis to final report.

        Validates the entire pipeline data flow integration.
        """
        print("\n🔄 Complete Data Flow Integration Test")

        # Step 1: Deep Analysis → JSON Exports
        print("   1️⃣ Executing deep analysis...")
        analysis_results = analyze_portfolio_with_python(holdings=aplus_portfolio_holdings, session_id=session_id)

        assert analysis_results["successful_analyses"] == len(aplus_portfolio_holdings)
        print(f"      ✅ {analysis_results['successful_analyses']} holdings analyzed")

        # Step 2: JSON Exports → A+ Discovery
        print("   2️⃣ Running A+ discovery integration...")
        discovery_results = integrate_aplus_discovery_with_deep_analysis(session_id)

        assert discovery_results["has_a_plus_analysis"] is True
        assert discovery_results["total_opportunities_found"] >= 3
        print(f"      ✅ {discovery_results['total_opportunities_found']} A+ opportunities found")

        # Step 3: A+ Discovery → Backtesting
        print("   3️⃣ Executing backtesting pipeline...")
        backtesting_results = connect_backtesting_to_discovery_results(session_id)

        assert backtesting_results["backtesting_executed"] is True
        assert backtesting_results["candidates_count"] >= 3
        print(f"      ✅ Backtesting executed for {backtesting_results['candidates_count']} candidates")

        # Step 4: All Data → Final Report
        print("   4️⃣ Generating final report...")
        from datetime import datetime

        portfolio_review = PortfolioReview(as_of=datetime.now(), base_currency="USD", holdings=aplus_portfolio_holdings)

        report_path = generate_python_report(
            portfolio_review=portfolio_review, deep_analysis_results=analysis_results, session_id=session_id
        )

        assert Path(report_path).exists()
        print(f"      ✅ Final report generated: {Path(report_path).name}")

        # Verify data consistency across pipeline
        print("   5️⃣ Validating data consistency...")

        # A+ opportunities in discovery should match analysis results
        analysis_aplus = [
            ticker for ticker, result in analysis_results["deep_analysis_results"].items() if result.grade in ["A+", "A"]
        ]

        discovery_aplus = [h["ticker"] for h in discovery_results["aplus_holdings"]]

        # All A+ from analysis should be in discovery
        for ticker in analysis_aplus:
            assert ticker in discovery_aplus, f"A+ ticker {ticker} from analysis should be in discovery"

        # Backtesting candidates should match discovery opportunities
        backtesting_tickers = [c["ticker"] for c in backtesting_results["candidates"]]

        for ticker in discovery_aplus:
            assert ticker in backtesting_tickers, f"Discovery opportunity {ticker} should be in backtesting"

        print("      ✅ Data consistency validated across all components")

        print("✅ Complete Data Flow Integration Successful:")
        print("   📊 Analysis → JSON exports: ✅")
        print("   🔍 JSON exports → A+ discovery: ✅")
        print("   🔬 A+ discovery → Backtesting: ✅")
        print("   📋 All data → Final report: ✅")
        print("   🎯 Data consistency maintained: ✅")
