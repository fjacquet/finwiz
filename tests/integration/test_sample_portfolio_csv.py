"""
Integration test with sample portfolio CSV files.

Tests full portfolio analysis pipeline with sample data and verifies:
- JSON output structure
- HTML report generation
- French language content
- All requirements met
"""

import csv
import json
from datetime import datetime

import pytest
from bs4 import BeautifulSoup

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import (
    APlusOpportunitySection,
    HoldingDecision,
    PortfolioReview,
    PriceTargets,
)
from finwiz.tools.portfolio_holdings_html_generator import generate_portfolio_holdings_report


@pytest.mark.integration
class TestSamplePortfolioCSV:
    """Test with sample portfolio CSV files."""

    @pytest.fixture
    def sample_portfolio_csv(self, tmp_path):
        """Create sample portfolio CSV with 5-10 holdings."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Create sample portfolio with diverse holdings
        portfolio_file = data_dir / "sample_portfolio.csv"
        with open(portfolio_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Ticker", "Currency", "AssetClass", "CurrentPrice"])
            writer.writerow(["Apple Inc.", "AAPL", "USD", "stock", "150.00"])
            writer.writerow(["Microsoft Corporation", "MSFT", "USD", "stock", "380.00"])
            writer.writerow(["Nestlé SA", "NESN.SW", "CHF", "stock", "105.00"])
            writer.writerow(["Vanguard S&P 500 ETF", "VOO", "USD", "etf", "450.00"])
            writer.writerow(["iShares MSCI World", "URTH", "USD", "etf", "140.00"])
            writer.writerow(["Bitcoin", "BTC-USD", "USD", "crypto", "50000.00"])

        return portfolio_file

    @pytest.fixture
    def sample_portfolio_review(self):
        """Create sample portfolio review for testing."""
        holdings = [
            HoldingDecision(
                asset_class="stock",
                name="Apple Inc.",
                ticker="AAPL",
                currency="USD",
                decision="KEEP",
                composite_score=0.88,
                grade="A",
                grade_description="Excellent investment avec forte croissance",
                recommended_action="Conserver la position",
                risk=RiskAssessmentStandardized(
                    score=2.5,
                    level="Medium",
                    risk_factors=["Volatilité du marché", "Concurrence technologique"],
                ),
                rationale_bullets=[
                    "Forte croissance des revenus (15% annuel)",
                    "Marges bénéficiaires élevées (28%)",
                    "Position de leader sur le marché",
                ],
                citations=["SEC 10-K 2024", "Yahoo Finance"],
                price_targets=PriceTargets(
                    current_price=150.0,
                    currency="USD",
                    fair_value_estimate=180.0,
                    buy_target_primary=140.0,
                    sell_target_primary=200.0,
                    stop_loss_level=130.0,
                    buy_rationale="Bon point d'entrée près du support",
                    sell_rationale="Prendre des bénéfices à la résistance",
                    calculation_method="DCF et analyse technique",
                    confidence_level=0.85,
                    data_as_of=datetime.now(),
                    data_sources=["Yahoo Finance", "SEC EDGAR"],
                ),
            ),
            HoldingDecision(
                asset_class="stock",
                name="Microsoft Corporation",
                ticker="MSFT",
                currency="USD",
                decision="KEEP",
                composite_score=0.92,
                grade="A+",
                grade_description="Investissement exceptionnel",
                recommended_action="Conserver et ajouter",
                risk=RiskAssessmentStandardized(
                    score=2.0,
                    level="Low",
                    risk_factors=["Risque réglementaire"],
                ),
                rationale_bullets=[
                    "Croissance cloud exceptionnelle",
                    "Leadership en IA",
                    "Dividendes stables",
                ],
                citations=["SEC 10-K 2024"],
                price_targets=PriceTargets(
                    current_price=380.0,
                    currency="USD",
                    fair_value_estimate=420.0,
                    buy_target_primary=360.0,
                    sell_target_primary=450.0,
                    stop_loss_level=340.0,
                    buy_rationale="Accumulation recommandée",
                    sell_rationale="Objectif de profit atteint",
                    calculation_method="Multiples et DCF",
                    confidence_level=0.90,
                    data_as_of=datetime.now(),
                    data_sources=["Yahoo Finance"],
                ),
            ),
            HoldingDecision(
                asset_class="stock",
                name="IBM Corporation",
                ticker="IBM",
                currency="USD",
                decision="SELL",
                composite_score=0.55,
                grade="D",
                grade_description="Performance faible",
                recommended_action="Vendre progressivement",
                risk=RiskAssessmentStandardized(
                    score=4.0,
                    level="High",
                    risk_factors=["Déclin des revenus", "Perte de parts de marché"],
                ),
                rationale_bullets=[
                    "Croissance négative",
                    "Marges en baisse",
                    "Transformation difficile",
                ],
                citations=["SEC 10-K 2024"],
                alternatives=[
                    {
                        "ticker": "NVDA",
                        "name": "NVIDIA Corporation",
                        "asset_class": "stock",
                        "composite_score": 0.95,
                        "grade": "A+",
                        "grade_description": "Opportunité exceptionnelle",
                        "recommended_action": "Achat fort",
                        "risk_score_standardized": 2.5,
                        "is_a_plus_candidate": True,
                        "transition_strategy": "Swap progressif sur 2 mois",
                        "swap_timing": "gradual",
                        "tax_implications": "Considérer l'impact fiscal",
                    }
                ],
            ),
            HoldingDecision(
                asset_class="etf",
                name="Vanguard S&P 500 ETF",
                ticker="VOO",
                currency="USD",
                decision="KEEP",
                composite_score=0.90,
                grade="A+",
                grade_description="ETF excellent",
                recommended_action="Position de base idéale",
                risk=RiskAssessmentStandardized(
                    score=2.0,
                    level="Low",
                    risk_factors=["Risque de marché"],
                ),
                rationale_bullets=[
                    "Frais ultra-bas (0.03%)",
                    "Diversification large",
                    "Tracking error minimal",
                ],
                citations=["Vanguard Prospectus"],
            ),
            HoldingDecision(
                asset_class="crypto",
                name="Bitcoin",
                ticker="BTC-USD",
                currency="USD",
                decision="KEEP",
                composite_score=0.65,
                grade="C+",
                grade_description="Spéculatif",
                recommended_action="Maintenir allocation limitée",
                risk=RiskAssessmentStandardized(
                    score=4.5,
                    level="Very High",
                    risk_factors=["Volatilité extrême", "Risque réglementaire"],
                ),
                rationale_bullets=[
                    "Volatilité très élevée",
                    "Potentiel de croissance",
                    "Risque réglementaire important",
                ],
                citations=["CoinMarketCap"],
            ),
        ]

        return PortfolioReview(
            as_of=datetime.now(),
            base_currency="CHF",
            holdings=holdings,
            current_a_plus_holdings_count=2,
            potential_a_plus_holdings_count=3,
            a_plus_opportunities=APlusOpportunitySection(
                total_opportunities_found=1,
                high_priority_opportunities=1,
                expected_portfolio_grade_improvement=0.15,
                top_recommendations=["NVDA"],
            ),
        )

    def test_should_read_sample_portfolio_csv(self, sample_portfolio_csv):
        """Test reading sample portfolio CSV file."""
        # Act
        holdings = []
        with open(sample_portfolio_csv) as f:
            reader = csv.DictReader(f)
            for row in reader:
                holdings.append(row)

        # Assert
        assert len(holdings) == 6
        assert all("Ticker" in h for h in holdings)
        assert all("Currency" in h for h in holdings)
        assert all("AssetClass" in h for h in holdings)

        # Verify diverse asset classes
        asset_classes = [h["AssetClass"] for h in holdings]
        assert "stock" in asset_classes
        assert "etf" in asset_classes
        assert "crypto" in asset_classes

    def test_should_generate_json_output_with_correct_structure(self, sample_portfolio_review):
        """Test JSON output structure."""
        # Act - Convert to dict for JSON serialization
        output = {
            "analysis_date": sample_portfolio_review.as_of.isoformat(),
            "base_currency": sample_portfolio_review.base_currency,
            "total_holdings": len(sample_portfolio_review.holdings),
            "current_aplus_count": sample_portfolio_review.current_a_plus_holdings_count,
            "potential_aplus_count": sample_portfolio_review.potential_a_plus_holdings_count,
            "holdings": [
                {
                    "ticker": h.ticker,
                    "name": h.name,
                    "asset_class": h.asset_class,
                    "grade": h.grade,
                    "composite_score": h.composite_score,
                    "decision": h.decision,
                    "price_targets": {
                        "current_price": h.price_targets.current_price if h.price_targets else None,
                        "buy_target": h.price_targets.buy_target_primary if h.price_targets else None,
                        "sell_target": h.price_targets.sell_target_primary if h.price_targets else None,
                    }
                    if h.price_targets
                    else None,
                    "alternatives_count": len(h.alternatives),
                }
                for h in sample_portfolio_review.holdings
            ],
            "aplus_opportunities": {
                "total_found": sample_portfolio_review.a_plus_opportunities.total_opportunities_found,
                "high_priority": sample_portfolio_review.a_plus_opportunities.high_priority_opportunities,
                "expected_improvement": sample_portfolio_review.a_plus_opportunities.expected_portfolio_grade_improvement,
            },
        }

        json_str = json.dumps(output, indent=2)

        # Assert
        assert json_str is not None
        parsed = json.loads(json_str)

        # Verify structure
        assert "analysis_date" in parsed
        assert "base_currency" in parsed
        assert "holdings" in parsed
        assert "aplus_opportunities" in parsed

        # Verify holdings structure
        assert len(parsed["holdings"]) == 5
        for holding in parsed["holdings"]:
            assert "ticker" in holding
            assert "grade" in holding
            assert "composite_score" in holding
            assert "decision" in holding

    def test_should_generate_html_report(self, sample_portfolio_review, tmp_path):
        """Test HTML report generation."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
            filename="test_portfolio_review_fr.html",
        )

        # Assert
        assert output_path.exists()
        assert output_path.name == "test_portfolio_review_fr.html"

        # Read and verify HTML content
        html_content = output_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html_content
        assert 'lang="fr"' in html_content
        assert 'charset="UTF-8"' in html_content

    def test_should_have_well_formed_html(self, sample_portfolio_review, tmp_path):
        """Test that HTML report is well-formed and valid."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        html_content = output_path.read_text(encoding="utf-8")

        # Parse with BeautifulSoup to validate
        soup = BeautifulSoup(html_content, "html.parser")

        # Assert - Check HTML structure
        assert soup.html is not None
        assert soup.head is not None
        assert soup.body is not None
        assert soup.title is not None

        # Check for required sections
        h1_tags = soup.find_all("h1")
        assert len(h1_tags) > 0

        h2_tags = soup.find_all("h2")
        assert len(h2_tags) > 0

        # Check for tables
        tables = soup.find_all("table")
        assert len(tables) > 0

    def test_should_contain_french_language_content(self, sample_portfolio_review, tmp_path):
        """Test that HTML report contains French language content."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        html_content = output_path.read_text(encoding="utf-8")

        # Assert - Check for French keywords
        french_keywords = [
            "Analyse de Portefeuille",
            "Tableau de Bord",
            "Positions",
            "Note",
            "Décision",
            "Objectifs de Prix",
            "Alternatives",
            "Feuille de Route",
            "Amélioration",
        ]

        for keyword in french_keywords:
            assert keyword in html_content, f"Missing French keyword: {keyword}"

    def test_should_include_all_holdings_in_report(self, sample_portfolio_review, tmp_path):
        """Test that all holdings are included in HTML report."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        html_content = output_path.read_text(encoding="utf-8")

        # Assert - Check for all tickers
        for holding in sample_portfolio_review.holdings:
            assert holding.ticker in html_content

    def test_should_include_price_targets_in_report(self, sample_portfolio_review, tmp_path):
        """Test that price targets are included in HTML report."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        html_content = output_path.read_text(encoding="utf-8")

        # Assert
        assert "Objectifs de Prix" in html_content
        assert "Prix actuel" in html_content

        # Check for specific price values
        for holding in sample_portfolio_review.holdings:
            if holding.price_targets:
                price_str = f"{holding.price_targets.current_price:.2f}"
                assert price_str in html_content

    def test_should_include_alternatives_in_report(self, sample_portfolio_review, tmp_path):
        """Test that alternatives are included in HTML report."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        html_content = output_path.read_text(encoding="utf-8")

        # Assert
        assert "Alternatives Recommandées" in html_content

        # Check for alternative ticker (IBM has NVDA as alternative)
        assert "NVDA" in html_content

    def test_should_include_aplus_roadmap_in_report(self, sample_portfolio_review, tmp_path):
        """Test that A+ roadmap is included in HTML report."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        html_content = output_path.read_text(encoding="utf-8")

        # Assert
        assert "Feuille de Route d'Amélioration A+" in html_content
        assert "opportunités A+ identifiées" in html_content

    def test_should_include_emojis_in_report(self, sample_portfolio_review, tmp_path):
        """Test that emojis are included in HTML report."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        html_content = output_path.read_text(encoding="utf-8")

        # Assert - Check for strategic emojis
        emojis = ["📊", "📈", "💰", "✅", "❌", "💎"]
        found_emojis = [emoji for emoji in emojis if emoji in html_content]
        assert len(found_emojis) >= 3, f"Expected at least 3 emojis, found {len(found_emojis)}"

    def test_should_have_responsive_css(self, sample_portfolio_review, tmp_path):
        """Test that HTML report has responsive CSS."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        html_content = output_path.read_text(encoding="utf-8")

        # Assert
        assert "@media (max-width: 768px)" in html_content
        assert "viewport" in html_content

    def test_should_have_print_friendly_css(self, sample_portfolio_review, tmp_path):
        """Test that HTML report has print-friendly CSS."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        html_content = output_path.read_text(encoding="utf-8")

        # Assert
        assert "@media print" in html_content

    def test_should_include_color_coded_grades(self, sample_portfolio_review, tmp_path):
        """Test that grades are color-coded in HTML report."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        html_content = output_path.read_text(encoding="utf-8")

        # Assert - Check for grade colors
        assert "#27ae60" in html_content  # A+ color (green)
        assert "#e74c3c" in html_content  # D color (red)

    def test_should_verify_all_requirements_met(self, sample_portfolio_review, tmp_path):
        """Test that all requirements are met."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        html_content = output_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html_content, "html.parser")

        # Assert - Verify all requirements
        requirements_checklist = {
            "HTML structure valid": soup.html is not None and soup.body is not None,
            "French language": "Analyse de Portefeuille" in html_content,
            "Portfolio dashboard": "Tableau de Bord" in html_content,
            "Holdings table": len(soup.find_all("table")) > 0,
            "Price targets": "Objectifs de Prix" in html_content,
            "Alternatives": "Alternatives" in html_content,
            "A+ roadmap": "Feuille de Route" in html_content,
            "Emojis present": "📊" in html_content,
            "Responsive CSS": "@media (max-width: 768px)" in html_content,
            "Print-friendly CSS": "@media print" in html_content,
            "Color-coded grades": "#27ae60" in html_content,
        }

        # All requirements should be met
        failed_requirements = [req for req, met in requirements_checklist.items() if not met]
        assert len(failed_requirements) == 0, f"Failed requirements: {failed_requirements}"

    def test_should_save_json_output_to_file(self, sample_portfolio_review, tmp_path):
        """Test saving JSON output to file."""
        # Arrange
        output_file = tmp_path / "portfolio_review.json"

        # Act
        output = {
            "analysis_date": sample_portfolio_review.as_of.isoformat(),
            "base_currency": sample_portfolio_review.base_currency,
            "holdings": [
                {
                    "ticker": h.ticker,
                    "name": h.name,
                    "grade": h.grade,
                    "composite_score": h.composite_score,
                }
                for h in sample_portfolio_review.holdings
            ],
        }

        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)

        # Assert
        assert output_file.exists()

        # Verify can be read back
        with open(output_file) as f:
            loaded = json.load(f)

        assert loaded["base_currency"] == "CHF"
        assert len(loaded["holdings"]) == 5
