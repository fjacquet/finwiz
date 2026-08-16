"""
Unit tests for AlternativeFinder tool.

Tests alternative finding for underperforming holdings with A+ integration.
"""

import json

import pytest

from finwiz.tools.alternative_finder_tool import AlternativeFinder, HoldingProfile


class TestAlternativeFinder:
    """Test suite for AlternativeFinder."""

    @pytest.fixture
    def finder(self, tmp_path):
        """Create finder instance with temp directory."""
        return AlternativeFinder(output_dir=tmp_path)

    @pytest.fixture
    def sample_discovery_output(self, tmp_path):
        """Create sample discovery output (consolidated_discovery.json, flat opportunities shape)."""
        discovery_dir = tmp_path / "discovery"
        discovery_dir.mkdir()

        discovery_data = {
            "timestamp": "2026-08-15T00:00:00",
            "total_opportunities": 4,
            "opportunities": [
                {
                    "ticker": "MSFT",
                    "name": "Microsoft Corporation",
                    "asset_class": "stock",
                    "composite_score": 0.90,
                    "grade": "A+",
                    "risk_score": 2.0,
                    "key_metrics": {"pe_ratio": 30, "growth_rate": 0.15},
                    "thesis_bullets": ["Strong cloud growth", "AI leadership"],
                    "citations": ["SEC 10-K", "Yahoo Finance"],
                    "confidence_level": 0.90,
                    "expected_annual_benefit": 0.12,
                },
                {
                    "ticker": "GOOGL",
                    "name": "Alphabet Inc.",
                    "asset_class": "stock",
                    "composite_score": 0.88,
                    "grade": "A",
                    "risk_score": 2.2,
                    "key_metrics": {"pe_ratio": 25, "growth_rate": 0.12},
                    "thesis_bullets": ["Search dominance", "Cloud growth"],
                    "citations": ["SEC 10-K"],
                    "confidence_level": 0.85,
                },
                {
                    "ticker": "VTI",
                    "name": "Vanguard Total Stock Market ETF",
                    "asset_class": "etf",
                    "composite_score": 0.92,
                    "grade": "A+",
                    "risk_score": 1.8,
                    "expense_ratio": 0.03,
                    "key_metrics": {"tracking_error": 0.02},
                    "thesis_bullets": ["Low cost", "Broad diversification"],
                    "citations": ["Vanguard"],
                    "confidence_level": 0.95,
                },
                {
                    "ticker": "BTC",
                    "name": "Bitcoin",
                    "asset_class": "crypto",
                    "composite_score": 0.85,
                    "grade": "A",
                    "risk_score": 3.5,
                    "market_cap": 1000000000000,
                    "key_metrics": {"volume_24h": 50000000000},
                    "thesis_bullets": ["Store of value", "Institutional adoption"],
                    "citations": ["CoinMarketCap"],
                    "confidence_level": 0.80,
                },
            ],
            "by_asset_class": {"stock": 2, "etf": 1, "crypto": 1},
        }

        consolidated_file = discovery_dir / "consolidated_discovery.json"
        with open(consolidated_file, "w") as f:
            json.dump(discovery_data, f)

        return consolidated_file

    def test_should_find_no_alternatives_for_grade_b_or_above(self, finder):
        """Test that no alternatives are found for holdings graded B or above."""
        # Arrange
        holding = HoldingProfile(
            ticker="AAPL",
            name="Apple Inc.",
            asset_class="stock",
            grade="B",
            composite_score=0.75,
        )

        # Act
        alternatives = finder.find_alternatives(holding)

        # Assert
        assert len(alternatives) == 0

    def test_should_find_aplus_alternatives_for_underperforming_stock(self, finder, sample_discovery_output):
        """Test finding A+ alternatives for underperforming stock."""
        # Arrange
        holding = HoldingProfile(
            ticker="IBM",
            name="IBM Corporation",
            asset_class="stock",
            grade="D",
            composite_score=0.55,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert len(alternatives) > 0
        assert all(alt.asset_class == "stock" for alt in alternatives)
        assert all(alt.is_a_plus_candidate for alt in alternatives)
        # Should find MSFT and GOOGL
        tickers = [alt.ticker for alt in alternatives]
        assert "MSFT" in tickers
        assert "GOOGL" in tickers

    def test_should_find_aplus_alternatives_for_underperforming_etf(self, finder, sample_discovery_output):
        """Test finding A+ alternatives for underperforming ETF."""
        # Arrange
        holding = HoldingProfile(
            ticker="EXPENSIVE.ETF",
            name="Expensive ETF",
            asset_class="etf",
            grade="C",
            composite_score=0.60,
            expense_ratio=0.50,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert len(alternatives) > 0
        assert all(alt.asset_class == "etf" for alt in alternatives)
        # Should find VTI
        tickers = [alt.ticker for alt in alternatives]
        assert "VTI" in tickers
        # Should have expense ratio savings
        vti_alt = next(alt for alt in alternatives if alt.ticker == "VTI")
        assert vti_alt.expense_ratio_savings is not None
        assert vti_alt.expense_ratio_savings > 0  # Savings from 0.50 to 0.03

    def test_should_find_aplus_alternatives_for_underperforming_crypto(self, finder, sample_discovery_output):
        """Test finding A+ alternatives for underperforming crypto."""
        # Arrange
        holding = HoldingProfile(
            ticker="SHIB",
            name="Shiba Inu",
            asset_class="crypto",
            grade="F",
            composite_score=0.40,
            market_cap=1000000,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert len(alternatives) > 0
        assert all(alt.asset_class == "crypto" for alt in alternatives)
        # Should find BTC
        tickers = [alt.ticker for alt in alternatives]
        assert "BTC" in tickers

    def test_should_not_include_current_holding_as_alternative(self, finder, sample_discovery_output):
        """Test that current holding is not included in alternatives."""
        # Arrange
        holding = HoldingProfile(
            ticker="MSFT",  # Same as one of the A+ alternatives
            name="Microsoft Corporation",
            asset_class="stock",
            grade="D",
            composite_score=0.55,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        tickers = [alt.ticker for alt in alternatives]
        assert "MSFT" not in tickers  # Should not include itself

    def test_should_limit_alternatives_to_max_count(self, finder, sample_discovery_output):
        """Test that alternatives are limited to max_alternatives."""
        # Arrange
        holding = HoldingProfile(
            ticker="BAD.STOCK",
            name="Bad Stock",
            asset_class="stock",
            grade="F",
            composite_score=0.40,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=1)

        # Assert
        assert len(alternatives) <= 1

    def test_should_create_immediate_swap_timing_for_large_grade_improvement(self, finder, sample_discovery_output):
        """Test immediate swap timing for large grade improvements (D to A+)."""
        # Arrange
        holding = HoldingProfile(
            ticker="BAD.STOCK",
            name="Bad Stock",
            asset_class="stock",
            grade="D",  # Grade value 4
            composite_score=0.40,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        # MSFT is A+ (grade value 10), improvement = 6
        msft_alt = next((alt for alt in alternatives if alt.ticker == "MSFT"), None)
        assert msft_alt is not None
        assert msft_alt.swap_timing == "immediate"
        assert "immédiatement" in msft_alt.transition_strategy.lower()

    def test_should_create_gradual_swap_timing_for_moderate_grade_improvement(self, finder, sample_discovery_output):
        """Test gradual swap timing for moderate grade improvements (C+ to A)."""
        # Arrange
        # GOOGL is grade A (value 9) in the base fixture; no discovery-output
        # modification needed here. (Note: a B+ alternative can no longer be
        # used to hit this bucket the way this test used to — B+ falls outside
        # the A-band grade filter now applied to consolidated_discovery.json's
        # opportunities list, so a B+ item would simply be excluded rather than
        # surfaced with a smaller grade_improvement.)
        holding = HoldingProfile(
            ticker="OK.STOCK",
            name="OK Stock",
            asset_class="stock",
            grade="C+",  # Grade value 6
            composite_score=0.60,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        # A (value 9) - C+ (value 6) = 3, should be gradual
        googl_alt = next((alt for alt in alternatives if alt.ticker == "GOOGL"), None)
        assert googl_alt is not None
        assert googl_alt.swap_timing == "gradual"
        assert "progressive" in googl_alt.transition_strategy.lower()

    def test_should_create_tax_optimized_swap_timing_for_small_grade_improvement(self, finder, sample_discovery_output):
        """Test tax-optimized swap timing for small grade improvements.

        Note: with the A-band-only filter (grade in {"A+", "A"}, value >= 9)
        applied to discovery opportunities, and alternatives only searched for
        holdings graded below B (value <= 6), the minimum achievable
        grade_improvement is 9 - 6 = 3 — always "gradual" or "immediate",
        never "tax_optimized" (< 2). This was already true before this file's
        A-band rewrite (the previous version of this test never actually
        asserted a tax_optimized outcome either); kept as a smoke test that
        the base fixture still yields alternatives at all.
        """
        # Arrange
        holding = HoldingProfile(
            ticker="DECENT.STOCK",
            name="Decent Stock",
            asset_class="stock",
            grade="C+",  # Grade value 6
            composite_score=0.65,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert len(alternatives) > 0

    def test_should_include_french_transition_strategy(self, finder, sample_discovery_output):
        """Test that transition strategy is in French."""
        # Arrange
        holding = HoldingProfile(
            ticker="BAD.STOCK",
            name="Bad Stock",
            asset_class="stock",
            grade="D",
            composite_score=0.40,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert len(alternatives) > 0
        for alt in alternatives:
            # Check for French keywords
            french_keywords = ["remplacer", "transition", "vendre", "acheter"]
            strategy_lower = alt.transition_strategy.lower()
            assert any(keyword in strategy_lower for keyword in french_keywords)

    def test_should_include_french_tax_implications(self, finder, sample_discovery_output):
        """Test that tax implications are in French."""
        # Arrange
        holding = HoldingProfile(
            ticker="BAD.STOCK",
            name="Bad Stock",
            asset_class="stock",
            grade="D",
            composite_score=0.40,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert len(alternatives) > 0
        for alt in alternatives:
            # Check for French keywords
            french_keywords = ["fiscal", "impôt", "gains", "pertes"]
            tax_lower = alt.tax_implications.lower()
            assert any(keyword in tax_lower for keyword in french_keywords)

    def test_should_include_fundamental_improvement_for_stocks(self, finder, sample_discovery_output):
        """Test that fundamental improvement is included for stock alternatives."""
        # Arrange
        holding = HoldingProfile(
            ticker="BAD.STOCK",
            name="Bad Stock",
            asset_class="stock",
            grade="D",
            composite_score=0.40,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert len(alternatives) > 0
        for alt in alternatives:
            assert alt.fundamental_improvement is not None
            assert "grade_improvement" in alt.fundamental_improvement
            assert "score_improvement" in alt.fundamental_improvement
            assert alt.fundamental_improvement["grade_improvement"] > 0
            assert alt.fundamental_improvement["score_improvement"] > 0

    def test_should_include_expense_ratio_savings_for_etfs(self, finder, sample_discovery_output):
        """Test that expense ratio savings is included for ETF alternatives."""
        # Arrange
        holding = HoldingProfile(
            ticker="EXPENSIVE.ETF",
            name="Expensive ETF",
            asset_class="etf",
            grade="C",
            composite_score=0.60,
            expense_ratio=0.50,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert len(alternatives) > 0
        vti_alt = next((alt for alt in alternatives if alt.ticker == "VTI"), None)
        assert vti_alt is not None
        assert vti_alt.expense_ratio_savings is not None
        # Savings should be 0.50 - 0.03 = 0.47
        assert vti_alt.expense_ratio_savings == pytest.approx(0.47, rel=0.01)

    def test_should_include_liquidity_improvement_for_crypto(self, finder, sample_discovery_output):
        """Test that liquidity improvement is included for crypto alternatives."""
        # Arrange
        holding = HoldingProfile(
            ticker="SHIB",
            name="Shiba Inu",
            asset_class="crypto",
            grade="F",
            composite_score=0.40,
            market_cap=1000000,  # 1M market cap
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert len(alternatives) > 0
        btc_alt = next((alt for alt in alternatives if alt.ticker == "BTC"), None)
        assert btc_alt is not None
        assert btc_alt.liquidity_improvement is not None
        # BTC has 1T market cap, so improvement should be huge
        assert btc_alt.liquidity_improvement > 1000  # 100,000% improvement

    def test_should_handle_missing_discovery_output_gracefully(self, finder):
        """Test graceful handling when discovery output doesn't exist."""
        # Arrange
        holding = HoldingProfile(
            ticker="BAD.STOCK",
            name="Bad Stock",
            asset_class="stock",
            grade="D",
            composite_score=0.40,
        )

        # Act (no discovery output file exists)
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        # Should return empty list, not crash
        assert alternatives == []

    def test_should_handle_corrupted_discovery_output_gracefully(self, finder, tmp_path):
        """Test graceful handling of corrupted discovery output."""
        # Arrange
        discovery_dir = tmp_path / "discovery"
        discovery_dir.mkdir()
        consolidated_file = discovery_dir / "consolidated_discovery.json"

        # Write corrupted JSON
        with open(consolidated_file, "w") as f:
            f.write("{invalid json")

        holding = HoldingProfile(
            ticker="BAD.STOCK",
            name="Bad Stock",
            asset_class="stock",
            grade="D",
            composite_score=0.40,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        # Should return empty list, not crash
        assert alternatives == []

    def test_should_compare_holdings_correctly(self, finder):
        """Test holding comparison metrics."""
        # Arrange
        current = HoldingProfile(
            ticker="OLD.STOCK",
            name="Old Stock",
            asset_class="stock",
            grade="D",
            composite_score=0.50,
            risk_score=3.0,
            market_cap=1000000,
        )

        alternative = HoldingProfile(
            ticker="NEW.STOCK",
            name="New Stock",
            asset_class="stock",
            grade="A",
            composite_score=0.85,
            risk_score=2.0,
            market_cap=10000000,
        )

        # Act
        comparison = finder.compare_holdings(current, alternative)

        # Assert
        assert comparison["grade_improvement"] == 5  # A (9) - D (4) = 5
        assert comparison["score_improvement"] == pytest.approx(0.35, rel=0.01)
        assert comparison["risk_change"] == pytest.approx(-1.0, rel=0.01)  # Lower risk
        assert comparison["market_cap_ratio"] == pytest.approx(10.0, rel=0.01)

    def test_should_compare_etf_expense_ratios(self, finder):
        """Test ETF expense ratio comparison."""
        # Arrange
        current = HoldingProfile(
            ticker="EXPENSIVE.ETF",
            name="Expensive ETF",
            asset_class="etf",
            grade="C",
            composite_score=0.60,
            expense_ratio=0.50,
        )

        alternative = HoldingProfile(
            ticker="CHEAP.ETF",
            name="Cheap ETF",
            asset_class="etf",
            grade="A",
            composite_score=0.85,
            expense_ratio=0.05,
        )

        # Act
        comparison = finder.compare_holdings(current, alternative)

        # Assert
        assert "expense_ratio_savings" in comparison
        assert comparison["expense_ratio_savings"] == pytest.approx(0.45, rel=0.01)

    def test_should_get_correct_grade_descriptions_in_french(self, finder):
        """Test French grade descriptions."""
        # Assert
        assert "Excellent" in finder._get_grade_description("A+")
        assert "Très bon" in finder._get_grade_description("A")
        assert "Bon" in finder._get_grade_description("B+")
        assert "Satisfaisant" in finder._get_grade_description("B")
        assert "Passable" in finder._get_grade_description("C")
        assert "Insuffisant" in finder._get_grade_description("D")
        assert "Très insuffisant" in finder._get_grade_description("F")

    def test_should_get_correct_recommended_actions_in_french(self, finder):
        """Test French recommended actions."""
        # Assert
        assert "Acheter et renforcer" in finder._get_recommended_action("A+")
        assert "Acheter" in finder._get_recommended_action("A")
        assert "Conserver" in finder._get_recommended_action("B")
        assert "Surveiller" in finder._get_recommended_action("C+")
        assert "Réduisez" in finder._get_recommended_action("D")
        assert "Vendez" in finder._get_recommended_action("F")

    def test_should_mark_alternatives_as_aplus_candidates(self, finder, sample_discovery_output):
        """Test that alternatives from discovery are marked as A+ candidates."""
        # Arrange
        holding = HoldingProfile(
            ticker="BAD.STOCK",
            name="Bad Stock",
            asset_class="stock",
            grade="D",
            composite_score=0.40,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert len(alternatives) > 0
        for alt in alternatives:
            assert alt.is_a_plus_candidate is True
            assert alt.discovery_source == "investment_discovery_crew"
            assert alt.confidence_level is not None
            assert alt.confidence_level > 0.0

    def test_should_remove_duplicate_alternatives(self, finder, tmp_path):
        """Test that duplicate alternatives are removed."""
        # Arrange - Create discovery output with duplicate
        discovery_dir = tmp_path / "discovery"
        discovery_dir.mkdir()

        discovery_data = {
            "opportunities": [
                {
                    "ticker": "MSFT",
                    "name": "Microsoft",
                    "asset_class": "stock",
                    "composite_score": 0.90,
                    "grade": "A+",
                    "risk_score": 2.0,
                },
                {
                    "ticker": "MSFT",  # Duplicate
                    "name": "Microsoft",
                    "asset_class": "stock",
                    "composite_score": 0.90,
                    "grade": "A+",
                    "risk_score": 2.0,
                },
            ],
        }

        consolidated_file = discovery_dir / "consolidated_discovery.json"
        with open(consolidated_file, "w") as f:
            json.dump(discovery_data, f)

        holding = HoldingProfile(
            ticker="BAD.STOCK",
            name="Bad Stock",
            asset_class="stock",
            grade="D",
            composite_score=0.40,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        # Should only have one MSFT, not two
        tickers = [alt.ticker for alt in alternatives]
        assert tickers.count("MSFT") == 1

    def test_should_exclude_opportunity_from_different_asset_class(self, finder, tmp_path):
        """An A-band opportunity for a different asset class must not surface as an alternative.

        Pins one of the two ways the consolidated_discovery.json filter can
        silently pass everything: forgetting the asset_class check.
        """
        # Arrange
        discovery_dir = tmp_path / "discovery"
        discovery_dir.mkdir()
        discovery_data = {
            "opportunities": [
                {
                    "ticker": "VTI",
                    "name": "Vanguard Total Stock Market ETF",
                    "asset_class": "etf",  # holding below is a stock
                    "composite_score": 0.92,
                    "grade": "A+",
                },
            ],
        }
        with open(discovery_dir / "consolidated_discovery.json", "w") as f:
            json.dump(discovery_data, f)

        holding = HoldingProfile(
            ticker="BAD.STOCK",
            name="Bad Stock",
            asset_class="stock",
            grade="D",
            composite_score=0.40,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert alternatives == []

    def test_should_exclude_non_a_band_opportunity(self, finder, tmp_path):
        """A same-asset-class opportunity below the A-band must not surface as an alternative.

        Pins the other way the consolidated_discovery.json filter can silently
        pass everything: forgetting the grade check (B+ and below are not
        A-band, even though they're above the "actionable" C floor upstream).
        """
        # Arrange
        discovery_dir = tmp_path / "discovery"
        discovery_dir.mkdir()
        discovery_data = {
            "opportunities": [
                {
                    "ticker": "DECENT.STOCK",
                    "name": "Decent Stock",
                    "asset_class": "stock",
                    "composite_score": 0.78,
                    "grade": "B+",  # below A-band (A+/A)
                },
            ],
        }
        with open(discovery_dir / "consolidated_discovery.json", "w") as f:
            json.dump(discovery_data, f)

        holding = HoldingProfile(
            ticker="BAD.STOCK",
            name="Bad Stock",
            asset_class="stock",
            grade="D",
            composite_score=0.40,
        )

        # Act
        alternatives = finder.find_alternatives(holding, max_alternatives=3)

        # Assert
        assert alternatives == []
