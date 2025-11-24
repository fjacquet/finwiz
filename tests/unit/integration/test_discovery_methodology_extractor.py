"""
Unit tests for DiscoveryMethodologyExtractor.

Tests extraction of screening criteria, validation statistics, fundamental/technical scores,
and methodology summaries from discovery crew outputs.
"""

from datetime import datetime

import pytest
from pytest import approx

from finwiz.integration.discovery_methodology_extractor import (
    DiscoveryMethodologyExtractor,
    MethodologySummary,
)
from finwiz.schemas.investment_discovery import (
    APlusAnalysis,
    APlusCriteria,
    APlusDiscoveryResult,
    InvestmentCandidate,
    MarketRegime,
)


@pytest.fixture
def sample_criteria() -> APlusCriteria:
    """Create sample A+ criteria for testing."""
    return APlusCriteria(
        etf_max_expense_ratio=0.15,
        etf_min_aum=1e9,
        etf_max_tracking_error=0.002,
        etf_min_history_years=3,
        stock_min_roe=20.0,
        stock_min_revenue_growth=15.0,
        stock_max_debt_to_equity=0.3,
        stock_min_market_cap=1e9,
        crypto_min_market_cap=10e9,
        crypto_min_daily_volume=500e6,
        crypto_min_age_months=36,
        regime_adjusted=True,
        adjustment_rationale="Increased quality thresholds due to volatile market conditions",
    )


@pytest.fixture
def sample_market_regime() -> MarketRegime:
    """Create sample market regime for testing."""
    return MarketRegime(
        regime_type="sideways",
        vix_level=22.5,
        inflation_rate=3.2,
        interest_rate_trend="stable",
        market_stress_level="medium",
        assessment_date=datetime(2025, 3, 10),
    )


@pytest.fixture
def sample_candidate() -> InvestmentCandidate:
    """Create sample investment candidate for testing."""
    return InvestmentCandidate(
        symbol="AAPL",
        name="Apple Inc.",
        asset_type="stock",
        current_price=175.50,
        market_cap=2.8e12,
        preliminary_score=0.92,
        final_score=0.96,
        grade="A+",
        grade_description="Exceptional quality with strong fundamentals",
        recommended_action="Strong Buy",
        discovery_date=datetime(2025, 3, 10),
        data_source="SEC EDGAR Filings",
    )


@pytest.fixture
def sample_analysis(sample_candidate: InvestmentCandidate) -> APlusAnalysis:
    """Create sample A+ analysis for testing."""
    return APlusAnalysis(
        candidate=sample_candidate,
        fundamental_score=0.95,
        technical_score=0.92,
        quality_score=0.98,
        risk_score=0.88,
        composite_score=0.96,
        confidence_level=0.85,
        is_a_plus_candidate=True,
        rationale=[
            "Exceptional ROE of 45%",
            "Strong revenue growth of 25%",
            "Low debt-to-equity ratio of 0.15",
        ],
        key_metrics={"roe": 0.45, "revenue_growth": 0.25, "debt_to_equity": 0.15},
        competitive_advantages=["Brand strength", "Ecosystem lock-in", "Innovation pipeline"],
        risk_factors=["Regulatory scrutiny", "Supply chain dependencies"],
    )


@pytest.fixture
def sample_discovery_result(
    sample_criteria: APlusCriteria,
    sample_market_regime: MarketRegime,
    sample_analysis: APlusAnalysis,
) -> APlusDiscoveryResult:
    """Create sample discovery result for testing."""
    return APlusDiscoveryResult(
        asset_type="stock",
        total_screened=500,
        candidates_found=15,
        discovery_criteria=sample_criteria,
        market_context=sample_market_regime,
        discovery_timestamp=datetime(2025, 3, 10),
        a_plus_candidates=[sample_analysis],
        average_score=0.96,
        grade_distribution={"A+": 15},
        a_plus_percentage=3.0,
        top_recommendations=["AAPL", "MSFT", "GOOGL"],
        implementation_notes=["Consider tax implications", "Gradual implementation recommended"],
        high_confidence_count=12,
        screening_efficiency=3.0,
    )


@pytest.fixture
def extractor() -> DiscoveryMethodologyExtractor:
    """Create extractor instance for testing."""
    return DiscoveryMethodologyExtractor()


class TestDiscoveryMethodologyExtractor:
    """Test suite for DiscoveryMethodologyExtractor."""

    def test_should_initialize_extractor(self, extractor: DiscoveryMethodologyExtractor) -> None:
        """Test that extractor initializes correctly."""
        assert extractor is not None
        assert extractor.logger is not None

    def test_should_extract_screening_criteria(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
        sample_criteria: APlusCriteria,
    ) -> None:
        """Test extraction of screening criteria from discovery result."""
        # Act
        criteria = extractor.extract_screening_criteria(sample_discovery_result)

        # Assert
        assert criteria is not None
        assert criteria.etf_max_expense_ratio == sample_criteria.etf_max_expense_ratio
        assert criteria.stock_min_roe == sample_criteria.stock_min_roe
        assert criteria.crypto_min_market_cap == sample_criteria.crypto_min_market_cap
        assert criteria.regime_adjusted is True
        assert "volatile market" in criteria.adjustment_rationale

    def test_should_extract_validation_statistics(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
    ) -> None:
        """Test extraction of validation statistics from discovery result."""
        # Act
        statistics = extractor.extract_validation_statistics(sample_discovery_result)

        # Assert
        assert statistics is not None
        assert statistics.total_screened == 500
        assert statistics.candidates_found == 15
        assert statistics.passed_validation == 15
        assert statistics.failed_validation == 0
        assert statistics.validation_rate == approx(1.0)
        assert statistics.screening_efficiency == approx(3.0)

    def test_should_extract_fundamental_technical_scores(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
    ) -> None:
        """Test extraction of fundamental and technical score breakdowns."""
        # Act
        score_breakdowns = extractor.extract_fundamental_technical_scores(sample_discovery_result)

        # Assert
        assert len(score_breakdowns) == 1
        assert "AAPL" in score_breakdowns

        aapl_breakdown = score_breakdowns["AAPL"]
        assert aapl_breakdown.symbol == "AAPL"
        assert aapl_breakdown.fundamental_score == approx(0.95)
        assert aapl_breakdown.technical_score == approx(0.92)
        assert aapl_breakdown.quality_score == approx(0.98)
        assert aapl_breakdown.risk_score == approx(0.88)
        assert aapl_breakdown.composite_score == approx(0.96)
        assert aapl_breakdown.grade == "A+"

    def test_should_generate_methodology_summary(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
    ) -> None:
        """Test generation of comprehensive methodology summary."""
        # Act
        summary = extractor.get_methodology_summary(sample_discovery_result)

        # Assert
        assert summary is not None
        assert isinstance(summary, MethodologySummary)
        assert summary.screening_criteria is not None
        assert summary.validation_statistics is not None
        assert len(summary.score_breakdowns) == 1
        assert len(summary.methodology_notes) > 0
        assert len(summary.data_sources) > 0

    def test_should_include_asset_type_in_methodology_notes(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
    ) -> None:
        """Test that methodology notes include asset type information."""
        # Act
        summary = extractor.get_methodology_summary(sample_discovery_result)

        # Assert
        assert summary is not None
        notes = summary.methodology_notes
        assert any("stock" in note.lower() for note in notes)
        assert any("500" in note for note in notes)  # Total screened

    def test_should_include_criteria_thresholds_in_notes(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
    ) -> None:
        """Test that methodology notes include criteria thresholds."""
        # Act
        summary = extractor.get_methodology_summary(sample_discovery_result)

        # Assert
        assert summary is not None
        notes = summary.methodology_notes
        # Should mention stock criteria
        assert any("ROE" in note for note in notes)
        assert any("revenue growth" in note.lower() for note in notes)

    def test_should_include_regime_adjustment_in_notes(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
    ) -> None:
        """Test that methodology notes include regime adjustment information."""
        # Act
        summary = extractor.get_methodology_summary(sample_discovery_result)

        # Assert
        assert summary is not None
        notes = summary.methodology_notes
        assert any("regime" in note.lower() for note in notes)
        assert any("volatile" in note.lower() for note in notes)

    def test_should_include_market_context_in_notes(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
    ) -> None:
        """Test that methodology notes include market context."""
        # Act
        summary = extractor.get_methodology_summary(sample_discovery_result)

        # Assert
        assert summary is not None
        notes = summary.methodology_notes
        assert any("sideways" in note.lower() for note in notes)
        assert any("medium" in note.lower() for note in notes)

    def test_should_include_screening_efficiency_in_notes(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
    ) -> None:
        """Test that methodology notes include screening efficiency."""
        # Act
        summary = extractor.get_methodology_summary(sample_discovery_result)

        # Assert
        assert summary is not None
        notes = summary.methodology_notes
        assert any("efficiency" in note.lower() for note in notes)
        assert any("3.0%" in note or "3%" in note for note in notes)

    def test_should_include_high_confidence_count_in_notes(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
    ) -> None:
        """Test that methodology notes include high confidence count."""
        # Act
        summary = extractor.get_methodology_summary(sample_discovery_result)

        # Assert
        assert summary is not None
        notes = summary.methodology_notes
        assert any("12" in note and "confidence" in note.lower() for note in notes)

    def test_should_extract_data_sources_for_stocks(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
    ) -> None:
        """Test extraction of data sources for stock analysis."""
        # Act
        summary = extractor.get_methodology_summary(sample_discovery_result)

        # Assert
        assert summary is not None
        data_sources = summary.data_sources
        assert "SEC EDGAR Filings" in data_sources
        assert "Yahoo Finance" in data_sources
        assert "Alpha Vantage" in data_sources

    def test_should_extract_data_sources_for_etfs(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
        sample_criteria: APlusCriteria,
        sample_market_regime: MarketRegime,
    ) -> None:
        """Test extraction of data sources for ETF analysis."""
        # Arrange - Create ETF discovery result
        etf_result = APlusDiscoveryResult(
            asset_type="etf",
            total_screened=200,
            candidates_found=10,
            discovery_criteria=sample_criteria,
            market_context=sample_market_regime,
            discovery_timestamp=datetime(2025, 3, 10),
            a_plus_candidates=[],
            average_score=0.95,
            grade_distribution={"A+": 10},
            a_plus_percentage=5.0,
            top_recommendations=["SPY", "VOO", "VTI"],
            implementation_notes=[],
            high_confidence_count=8,
            screening_efficiency=5.0,
            ucits_compliant_count=3,
            ucits_compliant_symbols=["VUSA.L", "CSPX.L", "EQQQ.L"],
        )

        # Act
        summary = extractor.get_methodology_summary(etf_result)

        # Assert
        assert summary is not None
        data_sources = summary.data_sources
        assert "Yahoo Finance ETF Data" in data_sources
        assert "Fund Prospectuses" in data_sources
        assert "ETF.com" in data_sources

    def test_should_extract_data_sources_for_crypto(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
        sample_criteria: APlusCriteria,
        sample_market_regime: MarketRegime,
    ) -> None:
        """Test extraction of data sources for crypto analysis."""
        # Arrange - Create crypto discovery result
        crypto_result = APlusDiscoveryResult(
            asset_type="crypto",
            total_screened=100,
            candidates_found=5,
            discovery_criteria=sample_criteria,
            market_context=sample_market_regime,
            discovery_timestamp=datetime(2025, 3, 10),
            a_plus_candidates=[],
            average_score=0.93,
            grade_distribution={"A+": 5},
            a_plus_percentage=5.0,
            top_recommendations=["BTC-USD", "ETH-USD"],
            implementation_notes=[],
            high_confidence_count=4,
            screening_efficiency=5.0,
        )

        # Act
        summary = extractor.get_methodology_summary(crypto_result)

        # Assert
        assert summary is not None
        data_sources = summary.data_sources
        assert "CoinMarketCap" in data_sources
        assert "Coinbase" in data_sources
        assert "Kraken" in data_sources

    def test_should_include_ucits_note_for_etfs(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_criteria: APlusCriteria,
        sample_market_regime: MarketRegime,
    ) -> None:
        """Test that methodology notes include UCITS compliance for ETFs."""
        # Arrange - Create ETF discovery result with UCITS data
        etf_result = APlusDiscoveryResult(
            asset_type="etf",
            total_screened=200,
            candidates_found=10,
            discovery_criteria=sample_criteria,
            market_context=sample_market_regime,
            discovery_timestamp=datetime(2025, 3, 10),
            a_plus_candidates=[],
            average_score=0.95,
            grade_distribution={"A+": 10},
            a_plus_percentage=5.0,
            top_recommendations=["SPY", "VOO", "VTI"],
            implementation_notes=[],
            high_confidence_count=8,
            screening_efficiency=5.0,
            ucits_compliant_count=3,
            ucits_compliant_symbols=["VUSA.L", "CSPX.L", "EQQQ.L"],
        )

        # Act
        summary = extractor.get_methodology_summary(etf_result)

        # Assert
        assert summary is not None
        notes = summary.methodology_notes
        assert any("UCITS" in note for note in notes)
        assert any("3" in note and "UCITS" in note for note in notes)

    def test_should_handle_empty_candidates_list(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_criteria: APlusCriteria,
        sample_market_regime: MarketRegime,
    ) -> None:
        """Test handling of discovery result with no candidates."""
        # Arrange - Create discovery result with no candidates
        empty_result = APlusDiscoveryResult(
            asset_type="stock",
            total_screened=500,
            candidates_found=0,
            discovery_criteria=sample_criteria,
            market_context=sample_market_regime,
            discovery_timestamp=datetime(2025, 3, 10),
            a_plus_candidates=[],
            average_score=0.0,
            grade_distribution={},
            a_plus_percentage=0.0,
            top_recommendations=[],
            implementation_notes=[],
            high_confidence_count=0,
            screening_efficiency=0.0,
        )

        # Act
        summary = extractor.get_methodology_summary(empty_result)

        # Assert
        assert summary is not None
        assert len(summary.score_breakdowns) == 0
        assert summary.validation_statistics.candidates_found == 0

    def test_should_handle_multiple_candidates(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
        sample_candidate: InvestmentCandidate,
    ) -> None:
        """Test extraction with multiple A+ candidates."""
        # Arrange - Add more candidates
        msft_candidate = InvestmentCandidate(
            symbol="MSFT",
            name="Microsoft Corporation",
            asset_type="stock",
            current_price=420.00,
            market_cap=3.1e12,
            preliminary_score=0.94,
            final_score=0.97,
            grade="A+",
            grade_description="Exceptional quality",
            recommended_action="Strong Buy",
            discovery_date=datetime(2025, 3, 10),
            data_source="SEC EDGAR Filings",
        )

        msft_analysis = APlusAnalysis(
            candidate=msft_candidate,
            fundamental_score=0.96,
            technical_score=0.94,
            quality_score=0.99,
            risk_score=0.90,
            composite_score=0.97,
            confidence_level=0.88,
            is_a_plus_candidate=True,
            rationale=["Strong cloud growth", "High margins"],
            key_metrics={},
            competitive_advantages=[],
            risk_factors=[],
        )

        sample_discovery_result.a_plus_candidates.append(msft_analysis)

        # Act
        score_breakdowns = extractor.extract_fundamental_technical_scores(sample_discovery_result)

        # Assert
        assert len(score_breakdowns) == 2
        assert "AAPL" in score_breakdowns
        assert "MSFT" in score_breakdowns
        assert score_breakdowns["MSFT"].composite_score == approx(0.97)

    def test_should_return_none_when_extraction_fails(
        self,
        extractor: DiscoveryMethodologyExtractor,
        mocker,
    ) -> None:
        """Test that extractor returns None when extraction fails."""
        # Arrange - Create mock that raises exception
        mock_result = mocker.Mock()
        mock_result.discovery_criteria = mocker.PropertyMock(side_effect=Exception("Test error"))

        # Act
        criteria = extractor.extract_screening_criteria(mock_result)

        # Assert
        assert criteria is None

    def test_should_log_extraction_operations(
        self,
        extractor: DiscoveryMethodologyExtractor,
        sample_discovery_result: APlusDiscoveryResult,
        mocker,
    ) -> None:
        """Test that extractor logs extraction operations."""
        # Arrange
        mock_logger = mocker.Mock()
        extractor.logger = mock_logger

        # Act
        extractor.extract_screening_criteria(sample_discovery_result)

        # Assert
        assert mock_logger.info.called
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("screening criteria" in str(call).lower() for call in info_calls)
