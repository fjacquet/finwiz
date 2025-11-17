"""
Unit tests for portfolio holdings grading improvements.

Tests verify that high-quality stocks (AAPL, MSFT, ASML) receive appropriate
grades when using shallow validation (deep analysis disabled).
"""

import pytest

from finwiz.orchestrators.portfolio_holdings_processor import (
    PortfolioHoldingsProcessor,
    RawHolding,
)
from finwiz.utils.grading_system import score_to_grade


class TestPortfolioHoldingsGrading:
    """Test suite for portfolio holdings grading improvements."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return PortfolioHoldingsProcessor()

    @pytest.fixture
    def mock_validator(self, mocker):
        """Mock the ticker validation tool."""
        mock = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        return mock

    async def test_should_assign_b_grade_to_valid_stock_with_shallow_validation(self, processor, mocker):
        """Test that valid stocks receive B grade (75%) with shallow validation."""
        # Arrange
        mock_validator = mocker.patch.object(processor, "validator")
        mock_validator._run.return_value = {
            "valid": True,
            "reason": "Ticker exists",
            "meta": {"source": "yahoo"},
        }

        holding = RawHolding(
            asset_class="stock",
            name="Apple Inc.",
            ticker="AAPL",
            currency="USD",
            source_file="data/stock.csv",
            line_number=2,
        )

        # Act
        decision = await processor._process_single_holding(holding, "CHF", 0.55)

        # Assert
        assert decision.composite_score == 0.75, "Valid stock should get 0.75 score"
        assert decision.grade == "B", f"Expected B grade, got {decision.grade}"
        assert decision.decision == "KEEP", "Valid stock with B grade should be KEEP"

    async def test_should_assign_b_grade_to_msft_with_shallow_validation(self, processor, mocker):
        """Test that MSFT receives B grade with shallow validation."""
        # Arrange
        mock_validator = mocker.patch.object(processor, "validator")
        mock_validator._run.return_value = {
            "valid": True,
            "reason": "Ticker exists",
            "meta": {"source": "yahoo"},
        }

        holding = RawHolding(
            asset_class="stock",
            name="Microsoft Corporation",
            ticker="MSFT",
            currency="USD",
            source_file="data/stock.csv",
            line_number=3,
        )

        # Act
        decision = await processor._process_single_holding(holding, "CHF", 0.55)

        # Assert
        assert decision.composite_score == 0.75
        assert decision.grade == "B"
        assert decision.decision == "KEEP"

    async def test_should_assign_b_grade_to_asml_with_shallow_validation(self, processor, mocker):
        """Test that ASML receives B grade with shallow validation."""
        # Arrange
        mock_validator = mocker.patch.object(processor, "validator")
        mock_validator._run.return_value = {
            "valid": True,
            "reason": "Ticker exists",
            "meta": {"source": "yahoo"},
        }

        holding = RawHolding(
            asset_class="stock",
            name="ASML Holding N.V.",
            ticker="ASML",
            currency="EUR",
            source_file="data/stock.csv",
            line_number=4,
        )

        # Act
        decision = await processor._process_single_holding(holding, "CHF", 0.55)

        # Assert
        assert decision.composite_score == 0.75
        assert decision.grade == "B"
        assert decision.decision == "KEEP"

    async def test_should_assign_b_plus_grade_to_valid_etf_with_shallow_validation(self, processor, mocker):
        """Test that valid ETFs receive B+ grade (80%) with shallow validation."""
        # Arrange
        mock_validator = mocker.patch.object(processor, "validator")
        mock_validator._run.return_value = {
            "valid": True,
            "reason": "Ticker exists",
            "meta": {"source": "yahoo"},
        }

        holding = RawHolding(
            asset_class="etf",
            name="Vanguard S&P 500 ETF",
            ticker="VOO",
            currency="USD",
            source_file="data/etf.csv",
            line_number=2,
        )

        # Act
        decision = await processor._process_single_holding(holding, "CHF", 0.55)

        # Assert
        assert decision.composite_score == 0.80, "Valid ETF should get 0.80 score"
        assert decision.grade == "B+", f"Expected B+ grade, got {decision.grade}"
        assert decision.decision == "KEEP"

    async def test_should_assign_f_grade_to_invalid_ticker(self, processor, mocker):
        """Test that invalid tickers receive F grade with shallow validation."""
        # Arrange
        mock_validator = mocker.patch.object(processor, "validator")
        mock_validator._run.return_value = {
            "valid": False,
            "reason": "Ticker not found",
            "meta": {},
        }

        holding = RawHolding(
            asset_class="stock",
            name="Invalid Company",
            ticker="INVALID",
            currency="USD",
            source_file="data/stock.csv",
            line_number=5,
        )

        # Act
        decision = await processor._process_single_holding(holding, "CHF", 0.55)

        # Assert
        assert decision.composite_score == 0.3, "Invalid ticker should get 0.3 score"
        assert decision.grade == "F", f"Expected F grade, got {decision.grade}"
        assert decision.decision == "SELL"

    async def test_should_include_shallow_validation_warning_in_rationale(self, processor, mocker):
        """Test that rationale includes shallow validation warning."""
        # Arrange
        mock_validator = mocker.patch.object(processor, "validator")
        mock_validator._run.return_value = {
            "valid": True,
            "reason": "Ticker exists",
            "meta": {"source": "yahoo"},
        }

        holding = RawHolding(
            asset_class="stock",
            name="Apple Inc.",
            ticker="AAPL",
            currency="USD",
            source_file="data/stock.csv",
            line_number=2,
        )

        # Act
        decision = await processor._process_single_holding(holding, "CHF", 0.55)

        # Assert
        rationale_text = " ".join(decision.rationale_bullets)
        assert "analyse superficielle" in rationale_text.lower()
        assert "DEEP_PORTFOLIO_ANALYSIS" in rationale_text
        assert "analyse complète" in rationale_text.lower()

    def test_should_calculate_correct_score_for_valid_stock(self, processor):
        """Test score calculation for valid stock."""
        # Act
        score = processor._calculate_score(is_valid=True, asset_class="stock")

        # Assert
        assert score == 0.75
        grade_info = score_to_grade(score)
        assert grade_info.grade == "B"

    def test_should_calculate_correct_score_for_valid_etf(self, processor):
        """Test score calculation for valid ETF."""
        # Act
        score = processor._calculate_score(is_valid=True, asset_class="etf")

        # Assert
        assert score == 0.80
        grade_info = score_to_grade(score)
        assert grade_info.grade == "B+"

    def test_should_calculate_correct_score_for_valid_crypto(self, processor):
        """Test score calculation for valid crypto."""
        # Act
        score = processor._calculate_score(is_valid=True, asset_class="crypto")

        # Assert
        assert score == 0.75
        grade_info = score_to_grade(score)
        assert grade_info.grade == "B"

    def test_should_calculate_correct_score_for_invalid_holding(self, processor):
        """Test score calculation for invalid holding."""
        # Act
        score = processor._calculate_score(is_valid=False, asset_class="stock")

        # Assert
        assert score == 0.3
        grade_info = score_to_grade(score)
        assert grade_info.grade == "F"

    async def test_should_process_multiple_quality_stocks_with_b_grades(self, processor, mocker):
        """Test processing multiple high-quality stocks."""
        # Arrange
        mock_validator = mocker.patch.object(processor, "validator")
        mock_validator._run.return_value = {
            "valid": True,
            "reason": "Ticker exists",
            "meta": {"source": "yahoo"},
        }

        holdings = [
            RawHolding(
                asset_class="stock",
                name="Apple Inc.",
                ticker="AAPL",
                currency="USD",
                source_file="data/stock.csv",
                line_number=2,
            ),
            RawHolding(
                asset_class="stock",
                name="Microsoft Corporation",
                ticker="MSFT",
                currency="USD",
                source_file="data/stock.csv",
                line_number=3,
            ),
            RawHolding(
                asset_class="stock",
                name="ASML Holding N.V.",
                ticker="ASML",
                currency="EUR",
                source_file="data/stock.csv",
                line_number=4,
            ),
        ]

        # Act
        decisions = await processor.process_holdings(holdings, "CHF", 0.55)

        # Assert
        assert len(decisions) == 3
        for decision in decisions:
            assert decision.grade == "B", f"{decision.ticker} should have B grade"
            assert decision.composite_score == 0.75
            assert decision.decision == "KEEP"

    async def test_should_indicate_data_freshness_as_fresh_for_valid_holdings(self, processor, mocker):
        """Test that valid holdings have 'fresh' data freshness."""
        # Arrange
        mock_validator = mocker.patch.object(processor, "validator")
        mock_validator._run.return_value = {
            "valid": True,
            "reason": "Ticker exists",
            "meta": {"source": "yahoo"},
        }

        holding = RawHolding(
            asset_class="stock",
            name="Apple Inc.",
            ticker="AAPL",
            currency="USD",
            source_file="data/stock.csv",
            line_number=2,
        )

        # Act
        decision = await processor._process_single_holding(holding, "CHF", 0.55)

        # Assert
        assert decision.data_freshness == "fresh"

    async def test_should_indicate_data_freshness_as_stale_for_invalid_holdings(self, processor, mocker):
        """Test that invalid holdings have 'stale' data freshness."""
        # Arrange
        mock_validator = mocker.patch.object(processor, "validator")
        mock_validator._run.return_value = {
            "valid": False,
            "reason": "Ticker not found",
            "meta": {},
        }

        holding = RawHolding(
            asset_class="stock",
            name="Invalid Company",
            ticker="INVALID",
            currency="USD",
            source_file="data/stock.csv",
            line_number=5,
        )

        # Act
        decision = await processor._process_single_holding(holding, "CHF", 0.55)

        # Assert
        assert decision.data_freshness == "stale"
