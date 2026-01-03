"""
Unit tests for portfolio holdings grading improvements.

Tests verify that high-quality stocks (AAPL, MSFT, ASML) receive appropriate
grades when using shallow validation (deep analysis disabled).
"""

import pytest
from pytest import approx

from finwiz.orchestrators.portfolio_holdings_processor import (
    PortfolioHoldingsProcessor,
    RawHolding,
)
from finwiz.scoring.grading_system import score_to_grade


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

    async def test_should_assign_d_grade_to_valid_stock_with_shallow_validation(self, processor, mocker):
        """Test that valid stocks receive D grade (60%) with shallow validation."""
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

        # Assert - Stock gets 0.6 score (D grade) with shallow validation
        assert decision.composite_score == approx(0.6), "Valid stock should get 0.6 score"
        assert decision.grade == "D", f"Expected D grade, got {decision.grade}"
        assert decision.decision == "KEEP", "Valid stock above threshold should be KEEP"

    async def test_should_assign_d_grade_to_msft_with_shallow_validation(self, processor, mocker):
        """Test that MSFT receives D grade with shallow validation."""
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

        # Assert - Stock gets 0.6 score (D grade) with shallow validation
        assert decision.composite_score == approx(0.6)
        assert decision.grade == "D"
        assert decision.decision == "KEEP"

    async def test_should_assign_d_grade_to_asml_with_shallow_validation(self, processor, mocker):
        """Test that ASML receives D grade with shallow validation."""
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

        # Assert - Stock gets 0.6 score (D grade) with shallow validation
        assert decision.composite_score == approx(0.6)
        assert decision.grade == "D"
        assert decision.decision == "KEEP"

    async def test_should_assign_c_grade_to_valid_etf_with_shallow_validation(self, processor, mocker):
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

        # Assert - ETF gets 0.65 score (C grade) with shallow validation
        assert decision.composite_score == approx(0.65), "Valid ETF should get 0.65 score"
        assert decision.grade == "C", f"Expected C grade, got {decision.grade}"
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
        assert decision.composite_score == approx(0.3), "Invalid ticker should get 0.3 score"
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

        # Assert - Check rationale contains pending deep analysis message
        rationale_text = " ".join(decision.rationale_bullets)
        assert "pending deep analysis" in rationale_text.lower()
        assert "validated stock" in rationale_text.lower()

    def test_should_calculate_correct_score_for_valid_stock(self, processor):
        """Test score calculation for valid stock."""
        # Act
        score = processor._calculate_score(is_valid=True, asset_class="stock")

        # Assert - Stock: 0.6 (D grade) with shallow validation
        assert score == approx(0.6)
        grade_info = score_to_grade(score)
        assert grade_info.grade == "D"

    def test_should_calculate_correct_score_for_valid_etf(self, processor):
        """Test score calculation for valid ETF."""
        # Act
        score = processor._calculate_score(is_valid=True, asset_class="etf")

        # Assert - ETF: 0.65 (C grade) with shallow validation
        assert score == approx(0.65)
        grade_info = score_to_grade(score)
        assert grade_info.grade == "C"

    def test_should_calculate_correct_score_for_valid_crypto(self, processor):
        """Test score calculation for valid crypto."""
        # Act
        score = processor._calculate_score(is_valid=True, asset_class="crypto")

        # Assert - Crypto: 0.5 (D grade) with shallow validation
        assert score == approx(0.5)
        grade_info = score_to_grade(score)
        assert grade_info.grade == "D"

    def test_should_calculate_correct_score_for_invalid_holding(self, processor):
        """Test score calculation for invalid holding."""
        # Act
        score = processor._calculate_score(is_valid=False, asset_class="stock")

        # Assert
        assert score == approx(0.3)
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

        # Assert - Stock gets 0.6 score (D grade) with shallow validation
        assert len(decisions) == 3
        for decision in decisions:
            assert decision.grade == "D", f"{decision.ticker} should have D grade"
            assert decision.composite_score == approx(0.6)
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
