"""
Unit tests for comprehensive schema validation.

Tests all FinWiz schemas with valid and invalid data, including field constraints.
"""
from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError
from pytest import approx

from finwiz.schemas import (
    CryptoMarketAnalysis,
    CryptoTechnicalIndicators,
    CryptoThesis,
    ETFFactsheet,
    ETFTopHolding,
    MarketSentiment,
    QuantitativeMetrics,
    RiskAssessmentStandardized,
    StockCandidate,
    StockRiskProfile,
    StockScreeningResult,
    StockTechnicalAnalysis,
    TechnicalIndicators,
    TenKInsight,
)

# ============================================================================
# Common Schemas Tests
# ============================================================================


class TestRiskAssessmentStandardized:
    """Test RiskAssessmentStandardized schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid risk assessment data."""
        risk = RiskAssessmentStandardized(
            scale="0_5",
            score=3.5,
            level="High",
            risk_factors=["Market volatility", "Regulatory uncertainty"],
        )
        assert risk.score == approx(3.5)
        assert risk.level == "High"
        assert len(risk.risk_factors) == 2

    def test_should_reject_score_below_minimum(self) -> None:
        """Test schema rejects score below 0.0."""
        with pytest.raises(ValidationError) as exc_info:
            RiskAssessmentStandardized(
                scale="0_5",
                score=-0.1,
                level="Low",
                risk_factors=[],
            )
        errors = exc_info.value.errors()
        assert any("score" in str(e["loc"]) for e in errors)

    def test_should_reject_score_above_maximum(self) -> None:
        """Test schema rejects score above 5.0."""
        with pytest.raises(ValidationError) as exc_info:
            RiskAssessmentStandardized(
                scale="0_5",
                score=5.1,
                level="Very High",
                risk_factors=[],
            )
        errors = exc_info.value.errors()
        assert any("score" in str(e["loc"]) for e in errors)

    def test_should_reject_invalid_level(self) -> None:
        """Test schema rejects invalid risk level."""
        with pytest.raises(ValidationError) as exc_info:
            RiskAssessmentStandardized(
                scale="0_5",
                score=3.0,
                level="Invalid",  # type: ignore
                risk_factors=[],
            )
        errors = exc_info.value.errors()
        assert any("level" in str(e["loc"]) for e in errors)

    def test_should_reject_too_many_risk_factors(self) -> None:
        """Test schema rejects more than 10 risk factors."""
        with pytest.raises(ValidationError) as exc_info:
            RiskAssessmentStandardized(
                scale="0_5",
                score=3.0,
                level="High",
                risk_factors=[f"Risk {i}" for i in range(11)],
            )
        errors = exc_info.value.errors()
        assert any("risk_factors" in str(e["loc"]) for e in errors)

    def test_should_reject_extra_fields(self) -> None:
        """Test schema rejects extra fields (extra='forbid')."""
        with pytest.raises(ValidationError) as exc_info:
            RiskAssessmentStandardized(
                scale="0_5",
                score=3.0,
                level="High",
                risk_factors=[],
                extra_field="not allowed",  # type: ignore
            )
        errors = exc_info.value.errors()
        assert any("extra_field" in str(e["loc"]) for e in errors)


# ============================================================================
# Stock Schemas Tests
# ============================================================================


class TestTenKInsight:
    """Test TenKInsight schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid 10-K insight data."""
        insight = TenKInsight(
            ticker="AAPL",
            filing_url="https://www.sec.gov/Archives/edgar/data/0000320193/000032019324000066/aapl-20230930.htm",
            filed_at=datetime(2024, 1, 31, 12, 0, tzinfo=UTC),
            section="Item 1A",
            excerpt="Risk factors include supply chain disruptions and currency fluctuations.",
            sec_citation="10-K (2024), Item 1A, p. 17",
        )
        assert insight.ticker == "AAPL"
        assert insight.section == "Item 1A"

    def test_should_reject_invalid_section(self) -> None:
        """Test schema rejects invalid section."""
        with pytest.raises(ValidationError) as exc_info:
            TenKInsight(
                ticker="AAPL",
                filing_url="https://www.sec.gov/test.htm",
                filed_at=datetime(2024, 1, 31, 12, 0, tzinfo=UTC),
                section="Item 99",  # type: ignore
                excerpt="Some excerpt text here",
                sec_citation="10-K (2024)",
            )
        errors = exc_info.value.errors()
        assert any("section" in str(e["loc"]) for e in errors)

    def test_should_reject_short_excerpt(self) -> None:
        """Test schema rejects excerpt shorter than 20 characters."""
        with pytest.raises(ValidationError) as exc_info:
            TenKInsight(
                ticker="AAPL",
                filing_url="https://www.sec.gov/test.htm",
                filed_at=datetime(2024, 1, 31, 12, 0, tzinfo=UTC),
                section="Item 1A",
                excerpt="Too short",
                sec_citation="10-K (2024)",
            )
        errors = exc_info.value.errors()
        assert any("excerpt" in str(e["loc"]) for e in errors)

    def test_should_reject_invalid_url(self) -> None:
        """Test schema rejects invalid filing URL."""
        with pytest.raises(ValidationError) as exc_info:
            TenKInsight(
                ticker="AAPL",
                filing_url="not-a-valid-url",
                filed_at=datetime(2024, 1, 31, 12, 0, tzinfo=UTC),
                section="Item 1A",
                excerpt="Risk factors include supply chain disruptions.",
                sec_citation="10-K (2024)",
            )
        errors = exc_info.value.errors()
        assert any("filing_url" in str(e["loc"]) for e in errors)


class TestMarketSentiment:
    """Test MarketSentiment schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid market sentiment data."""
        sentiment = MarketSentiment(
            ticker="AAPL",
            mean_score=0.25,
            counts={"pos": 10, "neu": 5, "neg": 3},
            top_pos=[],
            top_neg=[],
        )
        assert sentiment.ticker == "AAPL"
        assert -1.0 <= sentiment.mean_score <= 1.0

    def test_should_reject_mean_score_out_of_range(self) -> None:
        """Test schema rejects mean_score outside [-1.0, 1.0]."""
        with pytest.raises(ValidationError) as exc_info:
            MarketSentiment(
                ticker="AAPL",
                mean_score=1.5,
                counts={"pos": 10, "neu": 5, "neg": 3},
            )
        errors = exc_info.value.errors()
        assert any("mean_score" in str(e["loc"]) for e in errors)


class TestStockTechnicalAnalysis:
    """Test StockTechnicalAnalysis schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid technical analysis data."""
        analysis = StockTechnicalAnalysis(
            ticker="AAPL",
            company_name="Apple Inc.",
            analysis_date=date(2024, 3, 10),
            investment_thesis="Strong fundamentals with consistent growth trajectory.",
        )
        assert analysis.ticker == "AAPL"
        assert analysis.company_name == "Apple Inc."

    def test_should_reject_short_investment_thesis(self) -> None:
        """Test schema rejects investment thesis shorter than 50 characters."""
        with pytest.raises(ValidationError) as exc_info:
            StockTechnicalAnalysis(
                ticker="AAPL",
                company_name="Apple Inc.",
                analysis_date=date(2024, 3, 10),
                investment_thesis="Too short",
            )
        errors = exc_info.value.errors()
        assert any("investment_thesis" in str(e["loc"]) for e in errors)

    def test_should_reject_negative_price_target(self) -> None:
        """Test schema rejects negative price target."""
        with pytest.raises(ValidationError) as exc_info:
            StockTechnicalAnalysis(
                ticker="AAPL",
                company_name="Apple Inc.",
                analysis_date=date(2024, 3, 10),
                investment_thesis="Strong fundamentals with consistent growth trajectory.",
                price_target=-100.0,
            )
        errors = exc_info.value.errors()
        assert any("price_target" in str(e["loc"]) for e in errors)


class TestTechnicalIndicators:
    """Test TechnicalIndicators schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid technical indicators."""
        indicators = TechnicalIndicators(
            ticker="AAPL",
            rsi=65.5,
            macd=2.3,
            macd_signal=1.8,
            support_levels=[150.0, 145.0],
            resistance_levels=[160.0, 165.0],
        )
        assert indicators.ticker == "AAPL"
        assert 0.0 <= indicators.rsi <= 100.0

    def test_should_reject_rsi_out_of_range(self) -> None:
        """Test schema rejects RSI outside [0, 100]."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicators(
                ticker="AAPL",
                rsi=105.0,
            )
        errors = exc_info.value.errors()
        assert any("rsi" in str(e["loc"]) for e in errors)


# ============================================================================
# ETF Schemas Tests
# ============================================================================


class TestETFFactsheet:
    """Test ETFFactsheet schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid ETF factsheet data."""
        factsheet = ETFFactsheet(
            ticker="SPY",
            issuer="State Street",
            expense_ratio=0.09,
            tracking_diff=0.05,
            replication_method="physical",
            factsheet_url="https://www.ssga.com/us/en/individual/etfs/funds/spdr-sp-500-etf-trust-spy",
            as_of=date(2024, 3, 10),
        )
        assert factsheet.ticker == "SPY"
        assert factsheet.expense_ratio == approx(0.09)

    def test_should_reject_expense_ratio_out_of_range(self) -> None:
        """Test schema rejects expense ratio outside [0, 5]."""
        with pytest.raises(ValidationError) as exc_info:
            ETFFactsheet(
                ticker="SPY",
                issuer="State Street",
                expense_ratio=6.0,
                factsheet_url="https://www.ssga.com/test",
                as_of=date(2024, 3, 10),
            )
        errors = exc_info.value.errors()
        assert any("expense_ratio" in str(e["loc"]) for e in errors)

    def test_should_reject_invalid_replication_method(self) -> None:
        """Test schema rejects invalid replication method."""
        with pytest.raises(ValidationError) as exc_info:
            ETFFactsheet(
                ticker="SPY",
                issuer="State Street",
                expense_ratio=0.09,
                replication_method="invalid",  # type: ignore
                factsheet_url="https://www.ssga.com/test",
                as_of=date(2024, 3, 10),
            )
        errors = exc_info.value.errors()
        assert any("replication_method" in str(e["loc"]) for e in errors)


class TestETFTopHolding:
    """Test ETFTopHolding schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid ETF holding data."""
        holding = ETFTopHolding(
            ticker="AAPL",
            weight_pct=6.5,
            source_url="https://www.ssga.com/holdings",
            as_of=date(2024, 3, 10),
        )
        assert holding.ticker == "AAPL"
        assert 0.0 <= holding.weight_pct <= 100.0

    def test_should_reject_weight_out_of_range(self) -> None:
        """Test schema rejects weight percentage outside [0, 100]."""
        with pytest.raises(ValidationError) as exc_info:
            ETFTopHolding(
                ticker="AAPL",
                weight_pct=105.0,
                source_url="https://www.ssga.com/holdings",
                as_of=date(2024, 3, 10),
            )
        errors = exc_info.value.errors()
        assert any("weight_pct" in str(e["loc"]) for e in errors)


# ============================================================================
# Crypto Schemas Tests
# ============================================================================


class TestCryptoThesis:
    """Test CryptoThesis schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid crypto thesis data."""
        thesis = CryptoThesis(
            symbol="BTC",
            thesis_bullets=["Strong institutional adoption", "Limited supply"],
            references=["https://bitcoin.org/bitcoin.pdf"],
        )
        assert thesis.symbol == "BTC"
        assert len(thesis.thesis_bullets) == 2

    def test_should_reject_too_many_thesis_bullets(self) -> None:
        """Test schema rejects more than 20 thesis bullets."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoThesis(
                symbol="BTC",
                thesis_bullets=[f"Bullet {i}" for i in range(21)],
            )
        errors = exc_info.value.errors()
        assert any("thesis_bullets" in str(e["loc"]) for e in errors)

    def test_should_reject_invalid_reference_url(self) -> None:
        """Test schema rejects invalid reference URLs."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoThesis(
                symbol="BTC",
                thesis_bullets=["Strong adoption"],
                references=["not-a-valid-url"],
            )
        errors = exc_info.value.errors()
        assert any("references" in str(e["loc"]) for e in errors)


class TestCryptoMarketAnalysis:
    """Test CryptoMarketAnalysis schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid crypto market analysis data."""
        analysis = CryptoMarketAnalysis(
            analysis_date=date(2024, 3, 10),
            market_sentiment="bullish",
            key_trends=["Institutional adoption", "DeFi growth"],
            emerging_opportunities=["Layer 2 solutions"],
            candidates=[],
        )
        assert analysis.market_sentiment == "bullish"
        assert len(analysis.key_trends) == 2

    def test_should_reject_invalid_market_sentiment(self) -> None:
        """Test schema rejects invalid market sentiment."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoMarketAnalysis(
                analysis_date=date(2024, 3, 10),
                market_sentiment="invalid",  # type: ignore
                key_trends=["Trend 1"],
                emerging_opportunities=["Opportunity 1"],
                candidates=[],
            )
        errors = exc_info.value.errors()
        assert any("market_sentiment" in str(e["loc"]) for e in errors)


class TestCryptoTechnicalIndicators:
    """Test CryptoTechnicalIndicators schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid crypto technical indicators."""
        indicators = CryptoTechnicalIndicators(
            symbol="BTC",
            rsi=55.0,
            macd=1500.0,
            volume_trend="increasing",
        )
        assert indicators.symbol == "BTC"
        assert 0.0 <= indicators.rsi <= 100.0

    def test_should_reject_rsi_out_of_range(self) -> None:
        """Test schema rejects RSI outside [0, 100]."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoTechnicalIndicators(
                symbol="BTC",
                rsi=150.0,
            )
        errors = exc_info.value.errors()
        assert any("rsi" in str(e["loc"]) for e in errors)


# ============================================================================
# Screening Result Tests
# ============================================================================


class TestStockScreeningResult:
    """Test StockScreeningResult schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid stock screening result."""
        result = StockScreeningResult(
            screening_date=date(2024, 3, 10),
            total_screened=500,
            candidates=[],
            screening_criteria=["P/E < 20", "ROE > 15%"],
            market_context="Bull market with strong momentum",
        )
        assert result.total_screened == 500
        assert len(result.screening_criteria) == 2

    def test_should_reject_negative_total_screened(self) -> None:
        """Test schema rejects negative total_screened."""
        with pytest.raises(ValidationError) as exc_info:
            StockScreeningResult(
                screening_date=date(2024, 3, 10),
                total_screened=-10,
                candidates=[],
                screening_criteria=["P/E < 20"],
                market_context="Bull market",
            )
        errors = exc_info.value.errors()
        assert any("total_screened" in str(e["loc"]) for e in errors)


class TestStockCandidate:
    """Test StockCandidate schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid stock candidate."""
        candidate = StockCandidate(
            ticker="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            market_cap=3000000000000.0,
            pe_ratio=28.5,
            dividend_yield=0.5,
            selection_rationale="Strong fundamentals and consistent growth",
            confidence_level=0.85,
        )
        assert candidate.ticker == "AAPL"
        assert 0.0 <= candidate.confidence_level <= 1.0

    def test_should_reject_confidence_out_of_range(self) -> None:
        """Test schema rejects confidence level outside [0, 1]."""
        with pytest.raises(ValidationError) as exc_info:
            StockCandidate(
                ticker="AAPL",
                company_name="Apple Inc.",
                selection_rationale="Strong fundamentals and consistent growth",
                confidence_level=1.5,
            )
        errors = exc_info.value.errors()
        assert any("confidence_level" in str(e["loc"]) for e in errors)

    def test_should_reject_short_rationale(self) -> None:
        """Test schema rejects selection rationale shorter than 20 characters."""
        with pytest.raises(ValidationError) as exc_info:
            StockCandidate(
                ticker="AAPL",
                company_name="Apple Inc.",
                selection_rationale="Too short",
                confidence_level=0.85,
            )
        errors = exc_info.value.errors()
        assert any("selection_rationale" in str(e["loc"]) for e in errors)


# ============================================================================
# Quantitative Metrics Tests
# ============================================================================


class TestQuantitativeMetrics:
    """Test QuantitativeMetrics schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid quantitative metrics."""
        metrics = QuantitativeMetrics(
            ticker="AAPL",
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            max_drawdown=-15.5,
            volatility=18.5,
            beta=1.1,
            alpha=2.5,
            recommendation="BUY",
            confidence=0.85,
        )
        assert metrics.ticker == "AAPL"
        assert metrics.recommendation == "BUY"

    def test_should_reject_positive_max_drawdown(self) -> None:
        """Test schema rejects positive max_drawdown."""
        with pytest.raises(ValidationError) as exc_info:
            QuantitativeMetrics(
                ticker="AAPL",
                max_drawdown=10.0,
            )
        errors = exc_info.value.errors()
        assert any("max_drawdown" in str(e["loc"]) for e in errors)

    def test_should_reject_invalid_recommendation(self) -> None:
        """Test schema rejects invalid recommendation."""
        with pytest.raises(ValidationError) as exc_info:
            QuantitativeMetrics(
                ticker="AAPL",
                recommendation="MAYBE",  # type: ignore
            )
        errors = exc_info.value.errors()
        assert any("recommendation" in str(e["loc"]) for e in errors)


# ============================================================================
# Risk Profile Tests
# ============================================================================


class TestStockRiskProfile:
    """Test StockRiskProfile schema validation."""

    def test_should_validate_with_valid_data(self) -> None:
        """Test schema accepts valid stock risk profile."""
        risk_profile = StockRiskProfile(
            ticker="AAPL",
            company_name="Apple Inc.",
            assessment_date=date(2024, 3, 10),
            risk_assessment=RiskAssessmentStandardized(
                scale="0_5",
                score=2.5,
                level="Medium",
                risk_factors=["Market volatility"],
            ),
            regulatory_risk="Low regulatory risk due to established compliance",
            financial_risk="Strong balance sheet with minimal debt",
            valuation_risk="Moderate valuation risk at current P/E ratio",
            competitive_risk="Strong competitive position in smartphone market",
            governance_risk="Excellent corporate governance practices",
            risk_summary="Overall moderate risk with strong fundamentals and solid market position",
        )
        assert risk_profile.ticker == "AAPL"
        assert risk_profile.risk_assessment.score == approx(2.5)

    def test_should_reject_short_risk_summary(self) -> None:
        """Test schema rejects risk summary shorter than 50 characters."""
        with pytest.raises(ValidationError) as exc_info:
            StockRiskProfile(
                ticker="AAPL",
                company_name="Apple Inc.",
                assessment_date=date(2024, 3, 10),
                risk_assessment=RiskAssessmentStandardized(
                    scale="0_5",
                    score=2.5,
                    level="Medium",
                    risk_factors=[],
                ),
                regulatory_risk="Low regulatory risk due to established compliance",
                financial_risk="Strong balance sheet with minimal debt",
                valuation_risk="Moderate valuation risk at current P/E ratio",
                competitive_risk="Strong competitive position in smartphone market",
                governance_risk="Excellent corporate governance practices",
                risk_summary="Too short",
            )
        errors = exc_info.value.errors()
        assert any("risk_summary" in str(e["loc"]) for e in errors)


# ============================================================================
# Integration Tests - Multiple Schemas
# ============================================================================


class TestSchemaIntegration:
    """Test integration between multiple schemas."""

    def test_should_validate_stock_technical_analysis_with_nested_schemas(self) -> None:
        """Test StockTechnicalAnalysis with nested TechnicalIndicators and QuantitativeMetrics."""
        analysis = StockTechnicalAnalysis(
            ticker="AAPL",
            company_name="Apple Inc.",
            analysis_date=date(2024, 3, 10),
            technical_indicators=TechnicalIndicators(
                ticker="AAPL",
                rsi=65.5,
                macd=2.3,
            ),
            quantitative_metrics=QuantitativeMetrics(
                ticker="AAPL",
                sharpe_ratio=1.5,
                max_drawdown=-15.5,
            ),
            investment_thesis="Strong fundamentals with consistent growth trajectory.",
        )
        assert analysis.technical_indicators is not None
        assert analysis.quantitative_metrics is not None
        assert analysis.technical_indicators.ticker == "AAPL"
        assert analysis.quantitative_metrics.ticker == "AAPL"

    def test_should_validate_etf_factsheet_with_risk_assessment(self) -> None:
        """Test ETFFactsheet with nested RiskAssessmentStandardized."""
        factsheet = ETFFactsheet(
            ticker="SPY",
            issuer="State Street",
            expense_ratio=0.09,
            factsheet_url="https://www.ssga.com/test",
            as_of=date(2024, 3, 10),
            risk=RiskAssessmentStandardized(
                scale="0_5",
                score=2.0,
                level="Low",
                risk_factors=["Market risk"],
            ),
        )
        assert factsheet.risk is not None
        assert factsheet.risk.score == approx(2.0)
