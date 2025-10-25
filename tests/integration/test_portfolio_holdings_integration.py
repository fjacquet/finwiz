"""
Integration tests for portfolio holdings analysis.

Tests end-to-end portfolio analysis with sample CSV data.
"""

import csv
import json
from datetime import datetime

import pytest

from finwiz.tools.alternative_finder_tool import AlternativeFinder
from finwiz.tools.holding_analyzer_orchestrator import HoldingAnalyzerOrchestrator
from finwiz.tools.price_target_calculator import PriceTargetCalculator


@pytest.mark.integration
class TestPortfolioHoldingsIntegration:
    """Integration tests for portfolio holdings analysis."""

    @pytest.fixture
    def sample_portfolio_dir(self, tmp_path):
        """Create sample portfolio CSV files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Create sample ETF CSV
        etf_file = data_dir / "etf.csv"
        with open(etf_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Ticker", "Currency"])
            writer.writerow(["Vanguard S&P 500", "Yahoo:VUSA.L", "USD"])
            writer.writerow(["iShares MSCI World", "Yahoo:2B7K.DE", "EUR"])
            writer.writerow(["UBS Gold ETF", "Yahoo:AUUSI.SW", "USD"])

        # Create sample stock CSV
        stock_file = data_dir / "stock.csv"
        with open(stock_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Ticker", "Currency"])
            writer.writerow(["Apple", "Yahoo:AAPL", "USD"])
            writer.writerow(["Microsoft", "Yahoo:MSFT", "USD"])
            writer.writerow(["Nestle", "Yahoo:NESN.SW", "CHF"])
            writer.writerow(["Google", "Yahoo:GOOGL", "USD"])

        return data_dir

    @pytest.fixture
    def mock_crew_outputs(self, tmp_path):
        """Create mock crew output files for sample holdings."""
        output_dir = tmp_path / "output"

        # Stock crew outputs
        stock_dir = output_dir / "stock"
        stock_dir.mkdir(parents=True, exist_ok=True)

        stock_outputs = {
            "AAPL": {
                "ticker": "AAPL",
                "composite_score": 0.88,
                "grade": "A",
                "ten_k_insights": {
                    "revenue_growth": 0.15,
                    "profit_margin": 0.28,
                    "roe": 0.45,
                },
                "technical_indicators": {
                    "rsi": 62,
                    "macd": "bullish",
                    "trend": "uptrend",
                },
                "sec_citations": [
                    {
                        "filing_type": "10-K",
                        "accession_number": "0000320193-24-000123",
                        "filing_date": "2024-10-30",
                    }
                ],
            },
            "MSFT": {
                "ticker": "MSFT",
                "composite_score": 0.92,
                "grade": "A+",
                "ten_k_insights": {
                    "revenue_growth": 0.18,
                    "profit_margin": 0.35,
                    "roe": 0.42,
                },
                "technical_indicators": {
                    "rsi": 58,
                    "macd": "bullish",
                    "trend": "uptrend",
                },
            },
            "NESN.SW": {
                "ticker": "NESN.SW",
                "composite_score": 0.75,
                "grade": "B",
                "ten_k_insights": {
                    "revenue_growth": 0.05,
                    "profit_margin": 0.15,
                    "roe": 0.25,
                },
            },
            "GOOGL": {
                "ticker": "GOOGL",
                "composite_score": 0.55,
                "grade": "D",
                "ten_k_insights": {
                    "revenue_growth": 0.02,
                    "profit_margin": 0.10,
                    "roe": 0.15,
                },
            },
        }

        for ticker, data in stock_outputs.items():
            output_file = stock_dir / f"stock_{ticker}_latest.json"
            with open(output_file, "w") as f:
                json.dump({"pydantic": data}, f)

        # ETF crew outputs
        etf_dir = output_dir / "etf"
        etf_dir.mkdir(parents=True, exist_ok=True)

        etf_outputs = {
            "VUSA.L": {
                "ticker": "VUSA.L",
                "composite_score": 0.90,
                "grade": "A+",
                "expense_ratio": 0.07,
                "tracking_error": 0.02,
                "holdings": [
                    {"ticker": "AAPL", "weight": 7.5},
                    {"ticker": "MSFT", "weight": 6.8},
                ],
            },
            "2B7K.DE": {
                "ticker": "2B7K.DE",
                "composite_score": 0.85,
                "grade": "A",
                "expense_ratio": 0.12,
                "tracking_error": 0.05,
            },
            "AUUSI.SW": {
                "ticker": "AUUSI.SW",
                "composite_score": 0.60,
                "grade": "C",
                "expense_ratio": 0.35,
                "tracking_error": 0.10,
            },
        }

        for ticker, data in etf_outputs.items():
            output_file = etf_dir / f"etf_{ticker}_latest.json"
            with open(output_file, "w") as f:
                json.dump({"pydantic": data}, f)

        # Discovery crew output for alternatives
        discovery_dir = output_dir / "discovery"
        discovery_dir.mkdir(parents=True, exist_ok=True)

        discovery_data = {
            "pydantic": {
                "aplus_stocks": [
                    {
                        "ticker": "NVDA",
                        "name": "NVIDIA Corporation",
                        "composite_score": 0.95,
                        "grade": "A+",
                        "risk_score": 2.5,
                        "key_metrics": {"pe_ratio": 35, "growth_rate": 0.25},
                        "thesis_bullets": ["AI leadership", "Strong growth"],
                        "confidence_level": 0.92,
                    },
                    {
                        "ticker": "META",
                        "name": "Meta Platforms",
                        "composite_score": 0.88,
                        "grade": "A",
                        "risk_score": 2.8,
                        "key_metrics": {"pe_ratio": 28, "growth_rate": 0.18},
                        "thesis_bullets": ["Metaverse potential", "Ad revenue"],
                        "confidence_level": 0.85,
                    },
                ],
                "aplus_etfs": [
                    {
                        "ticker": "VTI",
                        "name": "Vanguard Total Stock Market ETF",
                        "composite_score": 0.93,
                        "grade": "A+",
                        "risk_score": 1.8,
                        "expense_ratio": 0.03,
                        "key_metrics": {"tracking_error": 0.01},
                        "thesis_bullets": ["Ultra-low cost", "Broad diversification"],
                        "confidence_level": 0.95,
                    },
                ],
            }
        }

        discovery_file = discovery_dir / "discovery_latest.json"
        with open(discovery_file, "w") as f:
            json.dump(discovery_data, f)

        return output_dir

    def test_should_analyze_complete_portfolio_from_csv(self, sample_portfolio_dir, mock_crew_outputs):
        """Test analyzing complete portfolio from CSV files."""
        # Arrange
        orchestrator = HoldingAnalyzerOrchestrator(output_dir=mock_crew_outputs)
        price_calculator = PriceTargetCalculator()
        alternative_finder = AlternativeFinder(output_dir=mock_crew_outputs)

        # Read ETF CSV
        etf_file = sample_portfolio_dir / "etf.csv"
        etf_holdings = []
        with open(etf_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row["Ticker"].replace("Yahoo:", "")
                etf_holdings.append(
                    {
                        "name": row["Name"],
                        "ticker": ticker,
                        "currency": row["Currency"],
                        "asset_class": "etf",
                    }
                )

        # Read stock CSV
        stock_file = sample_portfolio_dir / "stock.csv"
        stock_holdings = []
        with open(stock_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row["Ticker"].replace("Yahoo:", "")
                stock_holdings.append(
                    {
                        "name": row["Name"],
                        "ticker": ticker,
                        "currency": row["Currency"],
                        "asset_class": "stock",
                    }
                )

        all_holdings = etf_holdings + stock_holdings

        # Act - Analyze all holdings
        analyzed_holdings = []
        for holding in all_holdings:
            analysis = orchestrator.analyze_holding(
                ticker=holding["ticker"],
                asset_class=holding["asset_class"],
                currency=holding["currency"],
                name=holding["name"],
            )
            analyzed_holdings.append(analysis)

        # Assert
        assert len(analyzed_holdings) == 7  # 3 ETFs + 4 stocks
        assert all(h.ticker is not None for h in analyzed_holdings)
        assert all(h.composite_score > 0 for h in analyzed_holdings)

        # Verify we have reasonable scores (baseline or from cache)
        scores = [h.composite_score for h in analyzed_holdings]
        assert all(0.0 <= score <= 1.0 for score in scores)
        assert len(scores) == 7

    def test_should_calculate_price_targets_for_all_holdings(self, sample_portfolio_dir, mock_crew_outputs):
        """Test price target calculation for all holdings."""
        # Arrange
        orchestrator = HoldingAnalyzerOrchestrator(output_dir=mock_crew_outputs)
        price_calculator = PriceTargetCalculator()

        # Sample holdings
        holdings = [
            {"ticker": "AAPL", "asset_class": "stock", "currency": "USD", "price": 150.0},
            {"ticker": "VUSA.L", "asset_class": "etf", "currency": "USD", "price": 75.0},
        ]

        # Act
        targets_list = []
        for holding in holdings:
            targets = price_calculator.calculate_targets(
                ticker=holding["ticker"],
                asset_class=holding["asset_class"],
                current_price=holding["price"],
                currency=holding["currency"],
                decision="KEEP",
            )
            targets_list.append(targets)

        # Assert
        assert len(targets_list) == 2
        for targets in targets_list:
            assert targets.current_price > 0
            assert targets.buy_target_primary is not None
            assert targets.sell_target_primary is not None
            assert targets.stop_loss_level is not None
            assert targets.confidence_level > 0

    def test_should_find_alternatives_for_underperforming_holdings(self, sample_portfolio_dir, mock_crew_outputs):
        """Test finding alternatives for underperforming holdings."""
        # Arrange
        orchestrator = HoldingAnalyzerOrchestrator(output_dir=mock_crew_outputs)
        alternative_finder = AlternativeFinder(output_dir=mock_crew_outputs)

        # Analyze underperforming holdings
        underperforming = [
            {"ticker": "GOOGL", "asset_class": "stock", "currency": "USD"},
            {"ticker": "AUUSI.SW", "asset_class": "etf", "currency": "USD"},
        ]

        # Act
        alternatives_map = {}
        for holding in underperforming:
            analysis = orchestrator.analyze_holding(
                ticker=holding["ticker"],
                asset_class=holding["asset_class"],
                currency=holding["currency"],
            )

            # Only find alternatives if score is below 0.70 (equivalent to grade B)
            if analysis.composite_score < 0.70:
                from finwiz.tools.alternative_finder_tool import HoldingProfile
                from finwiz.utils.grading_system import score_to_grade

                grade = score_to_grade(analysis.composite_score).grade

                # Extract risk score with proper None handling
                risk_score = getattr(analysis, "risk_score", None)
                if risk_score is None:
                    risk_score = 2.5  # Default risk score
                
                profile = HoldingProfile(
                    ticker=analysis.ticker,
                    name=analysis.name,
                    asset_class=analysis.asset_class,
                    grade=grade,
                    composite_score=analysis.composite_score,
                    risk_score=risk_score,
                    expense_ratio=analysis.fundamental_analysis.get("expense_ratio") if analysis.fundamental_analysis else None,
                )

                alternatives = alternative_finder.find_alternatives(profile, max_alternatives=3)
                alternatives_map[holding["ticker"]] = alternatives

        # Assert
        assert len(alternatives_map) > 0

        # GOOGL (grade D) should have alternatives
        if "GOOGL" in alternatives_map:
            googl_alts = alternatives_map["GOOGL"]
            assert len(googl_alts) > 0
            assert all(alt.asset_class == "stock" for alt in googl_alts)
            # Should include A+ candidates
            assert any(alt.is_a_plus_candidate for alt in googl_alts)

        # AUUSI.SW (grade C) should have alternatives
        if "AUUSI.SW" in alternatives_map:
            gold_alts = alternatives_map["AUUSI.SW"]
            assert len(gold_alts) > 0
            assert all(alt.asset_class == "etf" for alt in gold_alts)

    def test_should_generate_complete_portfolio_review_structure(self, sample_portfolio_dir, mock_crew_outputs):
        """Test generating complete portfolio review structure."""
        # Arrange
        orchestrator = HoldingAnalyzerOrchestrator(output_dir=mock_crew_outputs)
        price_calculator = PriceTargetCalculator()
        alternative_finder = AlternativeFinder(output_dir=mock_crew_outputs)

        # Read all holdings
        all_holdings = []

        etf_file = sample_portfolio_dir / "etf.csv"
        with open(etf_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row["Ticker"].replace("Yahoo:", "")
                all_holdings.append(
                    {
                        "name": row["Name"],
                        "ticker": ticker,
                        "currency": row["Currency"],
                        "asset_class": "etf",
                    }
                )

        stock_file = sample_portfolio_dir / "stock.csv"
        with open(stock_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row["Ticker"].replace("Yahoo:", "")
                all_holdings.append(
                    {
                        "name": row["Name"],
                        "ticker": ticker,
                        "currency": row["Currency"],
                        "asset_class": "stock",
                    }
                )

        # Act - Build complete portfolio review
        portfolio_review = {
            "analysis_date": datetime.now().isoformat(),
            "total_holdings": len(all_holdings),
            "holdings": [],
            "summary": {
                "grade_distribution": {},
                "aplus_opportunities_count": 0,
                "underperforming_count": 0,
            },
        }

        for holding in all_holdings:
            # Analyze holding
            analysis = orchestrator.analyze_holding(
                ticker=holding["ticker"],
                asset_class=holding["asset_class"],
                currency=holding["currency"],
                name=holding["name"],
            )

            # Calculate price targets (using mock price)
            mock_price = 100.0
            targets = price_calculator.calculate_targets(
                ticker=holding["ticker"],
                asset_class=holding["asset_class"],
                current_price=mock_price,
                currency=holding["currency"],
                decision="KEEP",
            )

            # Find alternatives if underperforming (score < 0.70)
            alternatives = []
            from finwiz.utils.grading_system import score_to_grade

            grade = score_to_grade(analysis.composite_score).grade

            if analysis.composite_score < 0.70:
                from finwiz.tools.alternative_finder_tool import HoldingProfile

                # Extract risk score with proper None handling
                risk_score = getattr(analysis, "risk_score", None)
                if risk_score is None:
                    risk_score = 2.5  # Default risk score
                
                profile = HoldingProfile(
                    ticker=analysis.ticker,
                    name=analysis.name,
                    asset_class=analysis.asset_class,
                    grade=grade,
                    composite_score=analysis.composite_score,
                    risk_score=risk_score,
                )
                alternatives = alternative_finder.find_alternatives(profile, max_alternatives=3)
                portfolio_review["summary"]["underperforming_count"] += 1

            # Build holding entry
            holding_entry = {
                "ticker": analysis.ticker,
                "name": analysis.name,
                "asset_class": analysis.asset_class,
                "grade": grade,
                "composite_score": analysis.composite_score,
                "price_targets": {
                    "current_price": targets.current_price,
                    "buy_target": targets.buy_target_primary,
                    "sell_target": targets.sell_target_primary,
                    "stop_loss": targets.stop_loss_level,
                },
                "alternatives": [
                    {
                        "ticker": alt.ticker,
                        "name": alt.name,
                        "grade": alt.grade,
                        "is_aplus": alt.is_a_plus_candidate,
                    }
                    for alt in alternatives
                ],
                "data_freshness": analysis.data_freshness,
            }

            portfolio_review["holdings"].append(holding_entry)

            # Update grade distribution
            portfolio_review["summary"]["grade_distribution"][grade] = (
                portfolio_review["summary"]["grade_distribution"].get(grade, 0) + 1
            )

            # Count A+ opportunities
            if any(alt.is_a_plus_candidate for alt in alternatives):
                portfolio_review["summary"]["aplus_opportunities_count"] += 1

        # Assert
        assert portfolio_review["total_holdings"] == 7
        assert len(portfolio_review["holdings"]) == 7

        # Verify all holdings have required fields
        for holding in portfolio_review["holdings"]:
            assert "ticker" in holding
            assert "grade" in holding
            assert "price_targets" in holding
            assert "alternatives" in holding
            assert holding["price_targets"]["current_price"] > 0
            assert holding["price_targets"]["buy_target"] is not None
            assert holding["price_targets"]["sell_target"] is not None

        # Verify summary statistics
        assert portfolio_review["summary"]["grade_distribution"]
        assert sum(portfolio_review["summary"]["grade_distribution"].values()) == 7

        # Should have some underperforming holdings
        assert portfolio_review["summary"]["underperforming_count"] > 0

    def test_should_handle_multi_currency_portfolio(self, sample_portfolio_dir, mock_crew_outputs):
        """Test handling portfolio with multiple currencies."""
        # Arrange
        orchestrator = HoldingAnalyzerOrchestrator(output_dir=mock_crew_outputs)

        # Holdings in different currencies
        holdings = [
            {"ticker": "AAPL", "asset_class": "stock", "currency": "USD"},
            {"ticker": "NESN.SW", "asset_class": "stock", "currency": "CHF"},
            {"ticker": "2B7K.DE", "asset_class": "etf", "currency": "EUR"},
        ]

        # Act
        analyzed = []
        for holding in holdings:
            analysis = orchestrator.analyze_holding(
                ticker=holding["ticker"],
                asset_class=holding["asset_class"],
                currency=holding["currency"],
            )
            analyzed.append(analysis)

        # Assert
        assert len(analyzed) == 3
        currencies = [h.currency for h in analyzed]
        assert "USD" in currencies
        assert "CHF" in currencies
        assert "EUR" in currencies

    def test_should_verify_output_json_structure(self, sample_portfolio_dir, mock_crew_outputs):
        """Test that output can be serialized to JSON."""
        # Arrange
        orchestrator = HoldingAnalyzerOrchestrator(output_dir=mock_crew_outputs)
        price_calculator = PriceTargetCalculator()

        # Analyze one holding
        analysis = orchestrator.analyze_holding(
            ticker="AAPL",
            asset_class="stock",
            currency="USD",
            name="Apple Inc.",
        )

        targets = price_calculator.calculate_targets(
            ticker="AAPL",
            asset_class="stock",
            current_price=150.0,
            currency="USD",
            decision="KEEP",
        )

        # Act - Try to serialize to JSON
        from finwiz.utils.grading_system import score_to_grade

        grade = score_to_grade(analysis.composite_score).grade

        output = {
            "ticker": analysis.ticker,
            "name": analysis.name,
            "grade": grade,
            "composite_score": analysis.composite_score,
            "price_targets": {
                "current_price": targets.current_price,
                "buy_target": targets.buy_target_primary,
                "sell_target": targets.sell_target_primary,
                "stop_loss": targets.stop_loss_level,
                "confidence": targets.confidence_level,
            },
            "analysis_date": analysis.analysis_date.isoformat(),
        }

        json_str = json.dumps(output, indent=2)

        # Assert
        assert json_str is not None
        assert len(json_str) > 0

        # Verify can be parsed back
        parsed = json.loads(json_str)
        assert parsed["ticker"] == "AAPL"
        assert parsed["grade"] in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]

    def test_should_handle_missing_holdings_gracefully(self, sample_portfolio_dir, mock_crew_outputs):
        """Test handling of holdings without cached crew data."""
        # Arrange
        orchestrator = HoldingAnalyzerOrchestrator(output_dir=mock_crew_outputs)

        # Ticker that doesn't have crew output
        missing_ticker = "UNKNOWN.TICKER"

        # Act
        analysis = orchestrator.analyze_holding(
            ticker=missing_ticker,
            asset_class="stock",
            currency="USD",
            name="Unknown Company",
        )

        # Assert - should return baseline analysis
        assert analysis.ticker == missing_ticker
        assert analysis.data_freshness == "stale"
        assert analysis.crew_analysis_used is None
        assert analysis.composite_score == 0.60  # Baseline for stocks
        assert analysis.confidence_level == 0.3  # Low confidence

    def test_should_calculate_portfolio_statistics(self, sample_portfolio_dir, mock_crew_outputs):
        """Test calculation of portfolio-level statistics."""
        # Arrange
        orchestrator = HoldingAnalyzerOrchestrator(output_dir=mock_crew_outputs)

        # Analyze all holdings
        holdings = [
            {"ticker": "AAPL", "asset_class": "stock", "currency": "USD"},
            {"ticker": "MSFT", "asset_class": "stock", "currency": "USD"},
            {"ticker": "GOOGL", "asset_class": "stock", "currency": "USD"},
            {"ticker": "VUSA.L", "asset_class": "etf", "currency": "USD"},
            {"ticker": "2B7K.DE", "asset_class": "etf", "currency": "EUR"},
        ]

        analyzed = []
        for holding in holdings:
            analysis = orchestrator.analyze_holding(
                ticker=holding["ticker"],
                asset_class=holding["asset_class"],
                currency=holding["currency"],
            )
            analyzed.append(analysis)

        # Act - Calculate statistics
        from finwiz.utils.grading_system import score_to_grade

        stats = {
            "total_holdings": len(analyzed),
            "average_score": sum(h.composite_score for h in analyzed) / len(analyzed),
            "grade_distribution": {},
            "asset_class_distribution": {},
            "aplus_count": 0,
            "underperforming_count": 0,
        }

        for holding in analyzed:
            grade = score_to_grade(holding.composite_score).grade

            # Grade distribution
            stats["grade_distribution"][grade] = stats["grade_distribution"].get(grade, 0) + 1

            # Asset class distribution
            stats["asset_class_distribution"][holding.asset_class] = (
                stats["asset_class_distribution"].get(holding.asset_class, 0) + 1
            )

            # Count A+ and underperforming
            if grade == "A+":
                stats["aplus_count"] += 1
            if grade in ["C", "D", "F"]:
                stats["underperforming_count"] += 1

        # Assert
        assert stats["total_holdings"] == 5
        assert 0.0 <= stats["average_score"] <= 1.0
        assert stats["aplus_count"] >= 0
        assert stats["underperforming_count"] >= 0
        assert sum(stats["grade_distribution"].values()) == 5
        assert sum(stats["asset_class_distribution"].values()) == 5
        assert "stock" in stats["asset_class_distribution"]
        assert "etf" in stats["asset_class_distribution"]
