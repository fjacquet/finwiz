"""Tests for screening_filters.py module."""

import pytest

from finwiz.quantitative.config import ScreeningCriteria
from finwiz.quantitative.screening_criteria import ScreeningFilter, ScreeningScore
from finwiz.quantitative.screening_filters import (
    ScreeningResult,
    ScreeningSummary,
    ScreeningUniverse,
    SortOrder,
    StockData,
    StockFilter,
)


class TestScreeningUniverse:
    """Tests for ScreeningUniverse enum."""

    def test_should_have_sp500(self):
        """Test SP500 universe."""
        assert ScreeningUniverse.SP500.value == "SP500"

    def test_should_have_nasdaq100(self):
        """Test NASDAQ100 universe."""
        assert ScreeningUniverse.NASDAQ100.value == "NASDAQ100"

    def test_should_have_russell2000(self):
        """Test RUSSELL2000 universe."""
        assert ScreeningUniverse.RUSSELL2000.value == "RUSSELL2000"

    def test_should_have_dow30(self):
        """Test DOW30 universe."""
        assert ScreeningUniverse.DOW30.value == "DOW30"

    def test_should_have_custom(self):
        """Test CUSTOM universe."""
        assert ScreeningUniverse.CUSTOM.value == "CUSTOM"

    def test_should_have_all_us(self):
        """Test ALL_US universe."""
        assert ScreeningUniverse.ALL_US.value == "ALL_US"


class TestSortOrder:
    """Tests for SortOrder enum."""

    def test_should_have_ascending(self):
        """Test ascending sort order."""
        assert SortOrder.ASCENDING.value == "asc"

    def test_should_have_descending(self):
        """Test descending sort order."""
        assert SortOrder.DESCENDING.value == "desc"


class TestStockData:
    """Tests for StockData model."""

    def test_should_create_with_required_fields(self):
        """Test creating stock data with required fields."""
        stock = StockData(
            symbol="AAPL",
            company_name="Apple Inc",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000000000000,
            price=185.50,
        )
        assert stock.symbol == "AAPL"
        assert stock.company_name == "Apple Inc"
        assert stock.sector == "Technology"
        assert stock.industry == "Consumer Electronics"
        assert stock.market_cap == 3000000000000
        assert stock.price == 185.50

    def test_should_have_none_optional_fields(self):
        """Test optional fields default to None."""
        stock = StockData(
            symbol="AAPL",
            company_name="Apple Inc",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000000000000,
            price=185.50,
        )
        assert stock.pe_ratio is None
        assert stock.pb_ratio is None
        assert stock.dividend_yield is None
        assert stock.roe is None
        assert stock.rsi is None

    def test_should_accept_all_optional_fields(self):
        """Test all optional fields."""
        stock = StockData(
            symbol="AAPL",
            company_name="Apple Inc",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000000000000,
            price=185.50,
            pe_ratio=28.5,
            pb_ratio=45.0,
            ps_ratio=7.5,
            dividend_yield=0.005,
            roe=1.5,
            roa=0.3,
            debt_to_equity=1.8,
            current_ratio=0.98,
            quick_ratio=0.85,
            revenue_growth=0.12,
            earnings_growth=0.15,
            eps_growth=0.18,
            rsi=55.0,
            price_change_1m=0.05,
            price_change_3m=0.12,
            price_change_1y=0.35,
            volume_avg_3m=75000000,
            beta=1.2,
            analyst_rating=4.2,
            price_target=210.0,
        )
        assert stock.pe_ratio == 28.5
        assert stock.dividend_yield == 0.005
        assert stock.rsi == 55.0
        assert stock.beta == 1.2

    def test_should_forbid_extra_fields(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(Exception):  # ValidationError
            StockData(
                symbol="AAPL",
                company_name="Apple Inc",
                sector="Technology",
                industry="Consumer Electronics",
                market_cap=3000000000000,
                price=185.50,
                unknown_field="value",
            )


class TestScreeningResult:
    """Tests for ScreeningResult model."""

    def test_should_create_screening_result(self):
        """Test creating screening result."""
        stock = StockData(
            symbol="AAPL",
            company_name="Apple Inc",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000000000000,
            price=185.50,
        )
        score = ScreeningScore(
            symbol="AAPL",
            total_score=85.0,
            criteria_scores={"pe_ratio": 80.0, "roe": 90.0},
            rank=1,
            percentile=99.0,
        )
        result = ScreeningResult(
            symbol="AAPL",
            company_name="Apple Inc",
            sector="Technology",
            industry="Consumer Electronics",
            stock_data=stock,
            screening_score=score,
            recommendation="STRONG BUY",
        )
        assert result.symbol == "AAPL"
        assert result.recommendation == "STRONG BUY"
        assert result.stock_data.price == 185.50
        assert result.screening_score.total_score == 85.0


class TestScreeningSummary:
    """Tests for ScreeningSummary model."""

    def test_should_create_screening_summary(self):
        """Test creating screening summary."""
        filter1 = ScreeningFilter(
            criteria=ScreeningCriteria.PE_RATIO,
            max_value=30,
        )
        summary = ScreeningSummary(
            total_stocks_screened=500,
            stocks_passed=25,
            pass_rate=5.0,
            top_sectors=["Technology", "Healthcare", "Financials"],
            screening_criteria=[filter1],
            execution_time=2.5,
        )
        assert summary.total_stocks_screened == 500
        assert summary.stocks_passed == 25
        assert summary.pass_rate == 5.0
        assert len(summary.top_sectors) == 3
        assert summary.execution_time == 2.5


class TestStockFilterApplyFilters:
    """Tests for StockFilter.apply_filters method."""

    def test_should_filter_stocks_by_criteria(self, mocker):
        """Test filtering stocks by criteria."""
        stock1 = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
            pe_ratio=25,
        )
        stock2 = StockData(
            symbol="MSFT",
            company_name="Microsoft",
            sector="Tech",
            industry="Software",
            market_cap=2.8e12,
            price=380,
            pe_ratio=35,
        )
        stocks = [stock1, stock2]

        filter1 = ScreeningFilter(
            criteria=ScreeningCriteria.PE_RATIO,
            max_value=30,
        )

        # Mock CriteriaEvaluator at its source module
        mock_evaluator = mocker.patch("finwiz.quantitative.screening_criteria.CriteriaEvaluator")
        # First stock passes (pe_ratio=25 < 30), second fails (pe_ratio=35 >= 30)
        mock_evaluator.passes_filter.side_effect = [True, False]

        result = StockFilter.apply_filters(stocks, [filter1])

        assert len(result) == 1
        assert result[0].symbol == "AAPL"

    def test_should_return_empty_when_no_match(self, mocker):
        """Test returning empty list when no stocks match."""
        stock1 = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        stocks = [stock1]
        filter1 = ScreeningFilter(
            criteria=ScreeningCriteria.PE_RATIO,
            max_value=10,
        )

        mock_evaluator = mocker.patch("finwiz.quantitative.screening_criteria.CriteriaEvaluator")
        mock_evaluator.passes_filter.return_value = False

        result = StockFilter.apply_filters(stocks, [filter1])

        assert len(result) == 0

    def test_should_return_all_when_all_pass(self, mocker):
        """Test returning all stocks when all pass."""
        stock1 = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        stock2 = StockData(
            symbol="MSFT",
            company_name="Microsoft",
            sector="Tech",
            industry="Software",
            market_cap=2.8e12,
            price=380,
        )
        stocks = [stock1, stock2]
        filter1 = ScreeningFilter(
            criteria=ScreeningCriteria.MARKET_CAP,
            min_value=1e12,
        )

        mock_evaluator = mocker.patch("finwiz.quantitative.screening_criteria.CriteriaEvaluator")
        mock_evaluator.passes_filter.return_value = True

        result = StockFilter.apply_filters(stocks, [filter1])

        assert len(result) == 2


class TestStockFilterSortAndRank:
    """Tests for StockFilter.sort_and_rank method."""

    def test_should_sort_by_total_score_descending(self):
        """Test sorting by total score descending."""
        stock1 = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        stock2 = StockData(
            symbol="MSFT",
            company_name="Microsoft",
            sector="Tech",
            industry="Software",
            market_cap=2.8e12,
            price=380,
        )
        score1 = ScreeningScore(
            symbol="AAPL",
            total_score=70.0,
            criteria_scores={"pe_ratio": 70.0},
            rank=0,
            percentile=0.0,
        )
        score2 = ScreeningScore(
            symbol="MSFT",
            total_score=85.0,
            criteria_scores={"pe_ratio": 85.0},
            rank=0,
            percentile=0.0,
        )
        scored_stocks = [(stock1, score1), (stock2, score2)]

        result = StockFilter.sort_and_rank(scored_stocks, "total_score", SortOrder.DESCENDING)

        # MSFT (85) should be first
        assert result[0][0].symbol == "MSFT"
        assert result[0][1].rank == 1
        assert result[1][0].symbol == "AAPL"
        assert result[1][1].rank == 2

    def test_should_sort_by_total_score_ascending(self):
        """Test sorting by total score ascending."""
        stock1 = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        stock2 = StockData(
            symbol="MSFT",
            company_name="Microsoft",
            sector="Tech",
            industry="Software",
            market_cap=2.8e12,
            price=380,
        )
        score1 = ScreeningScore(
            symbol="AAPL",
            total_score=70.0,
            criteria_scores={"pe_ratio": 70.0},
            rank=0,
            percentile=0.0,
        )
        score2 = ScreeningScore(
            symbol="MSFT",
            total_score=85.0,
            criteria_scores={"pe_ratio": 85.0},
            rank=0,
            percentile=0.0,
        )
        scored_stocks = [(stock1, score1), (stock2, score2)]

        result = StockFilter.sort_and_rank(scored_stocks, "total_score", SortOrder.ASCENDING)

        # AAPL (70) should be first in ascending
        assert result[0][0].symbol == "AAPL"
        assert result[0][1].rank == 1

    def test_should_sort_by_stock_field(self):
        """Test sorting by stock data field."""
        stock1 = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        stock2 = StockData(
            symbol="MSFT",
            company_name="Microsoft",
            sector="Tech",
            industry="Software",
            market_cap=2.8e12,
            price=380,
        )
        score1 = ScreeningScore(
            symbol="AAPL",
            total_score=70.0,
            criteria_scores={"pe_ratio": 70.0},
            rank=0,
            percentile=0.0,
        )
        score2 = ScreeningScore(
            symbol="MSFT",
            total_score=85.0,
            criteria_scores={"pe_ratio": 85.0},
            rank=0,
            percentile=0.0,
        )
        scored_stocks = [(stock1, score1), (stock2, score2)]

        result = StockFilter.sort_and_rank(scored_stocks, "price", SortOrder.DESCENDING)

        # MSFT (380) should be first by price
        assert result[0][0].symbol == "MSFT"

    def test_should_calculate_percentiles(self):
        """Test percentile calculation."""
        stock1 = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        stock2 = StockData(
            symbol="MSFT",
            company_name="Microsoft",
            sector="Tech",
            industry="Software",
            market_cap=2.8e12,
            price=380,
        )
        score1 = ScreeningScore(
            symbol="AAPL",
            total_score=70.0,
            criteria_scores={"pe_ratio": 70.0},
            rank=0,
            percentile=0.0,
        )
        score2 = ScreeningScore(
            symbol="MSFT",
            total_score=85.0,
            criteria_scores={"pe_ratio": 85.0},
            rank=0,
            percentile=0.0,
        )
        scored_stocks = [(stock1, score1), (stock2, score2)]

        result = StockFilter.sort_and_rank(scored_stocks, "total_score", SortOrder.DESCENDING)

        # First should have 100% percentile
        assert result[0][1].percentile == 100.0
        # Second should have 50% percentile
        assert result[1][1].percentile == 50.0


class TestStockFilterGenerateRecommendation:
    """Tests for StockFilter.generate_recommendation method."""

    def test_should_return_strong_buy_for_high_score(self):
        """Test STRONG BUY for score >= 80."""
        stock = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        score = ScreeningScore(
            symbol="AAPL",
            total_score=85.0,
            criteria_scores={"pe_ratio": 85.0},
            rank=1,
            percentile=99.0,
        )
        result = StockFilter.generate_recommendation(stock, score)
        assert result == "STRONG BUY"

    def test_should_return_buy_for_good_score(self):
        """Test BUY for score >= 60."""
        stock = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        score = ScreeningScore(
            symbol="AAPL",
            total_score=65.0,
            criteria_scores={"pe_ratio": 65.0},
            rank=1,
            percentile=80.0,
        )
        result = StockFilter.generate_recommendation(stock, score)
        assert result == "BUY"

    def test_should_return_hold_for_medium_score(self):
        """Test HOLD for score >= 40."""
        stock = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        score = ScreeningScore(
            symbol="AAPL",
            total_score=45.0,
            criteria_scores={"pe_ratio": 45.0},
            rank=1,
            percentile=50.0,
        )
        result = StockFilter.generate_recommendation(stock, score)
        assert result == "HOLD"

    def test_should_return_weak_hold_for_low_score(self):
        """Test WEAK HOLD for score >= 20."""
        stock = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        score = ScreeningScore(
            symbol="AAPL",
            total_score=25.0,
            criteria_scores={"pe_ratio": 25.0},
            rank=1,
            percentile=30.0,
        )
        result = StockFilter.generate_recommendation(stock, score)
        assert result == "WEAK HOLD"

    def test_should_return_avoid_for_very_low_score(self):
        """Test AVOID for score < 20."""
        stock = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Tech",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        score = ScreeningScore(
            symbol="AAPL",
            total_score=15.0,
            criteria_scores={"pe_ratio": 15.0},
            rank=1,
            percentile=10.0,
        )
        result = StockFilter.generate_recommendation(stock, score)
        assert result == "AVOID"


class TestStockFilterGenerateSummary:
    """Tests for StockFilter.generate_summary method."""

    def test_should_generate_summary(self):
        """Test generating screening summary."""
        filter1 = ScreeningFilter(
            criteria=ScreeningCriteria.PE_RATIO,
            max_value=30,
        )
        stock = StockData(
            symbol="AAPL",
            company_name="Apple",
            sector="Technology",
            industry="Electronics",
            market_cap=3e12,
            price=185,
        )
        score = ScreeningScore(
            symbol="AAPL",
            total_score=85.0,
            criteria_scores={"pe_ratio": 85.0},
            rank=1,
            percentile=99.0,
        )
        result = ScreeningResult(
            symbol="AAPL",
            company_name="Apple",
            sector="Technology",
            industry="Electronics",
            stock_data=stock,
            screening_score=score,
            recommendation="STRONG BUY",
        )

        summary = StockFilter.generate_summary(
            total_screened=100,
            passed_filters=10,
            filters=[filter1],
            execution_time=1.5,
            results=[result],
        )

        assert summary.total_stocks_screened == 100
        assert summary.stocks_passed == 10
        assert summary.pass_rate == 10.0
        assert summary.execution_time == 1.5
        assert "Technology" in summary.top_sectors

    def test_should_calculate_pass_rate(self):
        """Test pass rate calculation."""
        filter1 = ScreeningFilter(
            criteria=ScreeningCriteria.PE_RATIO,
            max_value=30,
        )
        summary = StockFilter.generate_summary(
            total_screened=500,
            passed_filters=25,
            filters=[filter1],
            execution_time=2.0,
            results=[],
        )

        assert summary.pass_rate == 5.0

    def test_should_handle_zero_screened(self):
        """Test handling zero stocks screened."""
        filter1 = ScreeningFilter(
            criteria=ScreeningCriteria.PE_RATIO,
            max_value=30,
        )
        summary = StockFilter.generate_summary(
            total_screened=0,
            passed_filters=0,
            filters=[filter1],
            execution_time=0.1,
            results=[],
        )

        assert summary.pass_rate == 0.0

    def test_should_get_top_sectors(self):
        """Test getting top sectors from results."""
        filter1 = ScreeningFilter(
            criteria=ScreeningCriteria.PE_RATIO,
            max_value=30,
        )
        results = []
        for i, sector in enumerate(["Tech", "Tech", "Health", "Finance", "Tech", "Health", "Energy"]):
            stock = StockData(
                symbol=f"STOCK{i}",
                company_name=f"Company {i}",
                sector=sector,
                industry="Industry",
                market_cap=1e12,
                price=100,
            )
            score = ScreeningScore(
                symbol=f"STOCK{i}",
                total_score=70.0,
                criteria_scores={"pe_ratio": 70.0},
                rank=i + 1,
                percentile=50.0,
            )
            results.append(
                ScreeningResult(
                    symbol=f"STOCK{i}",
                    company_name=f"Company {i}",
                    sector=sector,
                    industry="Industry",
                    stock_data=stock,
                    screening_score=score,
                    recommendation="BUY",
                )
            )

        summary = StockFilter.generate_summary(
            total_screened=100,
            passed_filters=7,
            filters=[filter1],
            execution_time=1.0,
            results=results,
        )

        # Tech (3) should be first
        assert summary.top_sectors[0] == "Tech"
        # Health (2) should be second
        assert summary.top_sectors[1] == "Health"
