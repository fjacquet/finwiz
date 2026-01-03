"""
Unit tests for MarketContextExtractor.

Tests extraction of market regime, VIX indicators, macro indicators,
and market context summaries from discovery crew outputs.

This comprehensive test suite covers:
- Context extraction from various market regimes
- VIX indicator calculations and classifications
- Macroeconomic indicator extraction
- Risk environment assessment
- Allocation implication generation
- Edge cases and error handling
- Data transformation and validation
"""

import logging
from datetime import datetime

import pytest
from faker import Faker
from pytest import approx

from finwiz.orchestrators.extraction.market_context import (
    MacroIndicators,
    MarketContextExtractor,
    MarketContextSummary,
    VIXIndicators,
)
from finwiz.schemas.investment_discovery import (
    APlusCriteria,
    APlusDiscoveryResult,
    MarketRegime,
)


@pytest.fixture
def fake() -> Faker:
    """Faker instance for generating test data."""
    return Faker()


class TestMarketContextExtractorInitialization:
    """Test MarketContextExtractor initialization and setup."""

    def test_should_initialize_with_default_logger(self) -> None:
        """Test extractor initializes with default logger."""
        # Act
        extractor = MarketContextExtractor()

        # Assert
        assert extractor.logger is not None
        assert isinstance(extractor.logger, logging.Logger)

    def test_should_initialize_with_custom_logger(self, mocker) -> None:
        """Test extractor initializes with custom logger instance."""
        # Arrange
        custom_logger = mocker.Mock(spec=logging.Logger)

        # Act
        extractor = MarketContextExtractor(logger=custom_logger)

        # Assert
        assert extractor.logger is custom_logger
        custom_logger.info.assert_called_once()

    def test_should_log_initialization_message(self, mocker) -> None:
        """Test that initialization is logged."""
        # Arrange
        mock_logger = mocker.Mock(spec=logging.Logger)

        # Act
        MarketContextExtractor(logger=mock_logger)

        # Assert
        mock_logger.info.assert_called_with("MarketContextExtractor initialized")


class TestMarketContextExtractorMarketRegime:
    """Test market regime extraction functionality."""

    @pytest.fixture
    def extractor(self) -> MarketContextExtractor:
        """Create extractor instance for testing."""
        return MarketContextExtractor()

    @pytest.fixture
    def bull_market_discovery(self) -> APlusDiscoveryResult:
        """Create discovery result with bull market context."""
        return APlusDiscoveryResult(
            asset_type="stock",
            total_screened=100,
            candidates_found=5,
            discovery_criteria=APlusCriteria(),
            market_context=MarketRegime(
                regime_type="bull",
                vix_level=12.5,
                inflation_rate=2.5,
                interest_rate_trend="stable",
                market_stress_level="low",
                assessment_date=datetime(2025, 3, 10),
            ),
            discovery_timestamp=datetime(2025, 3, 10),
            average_score=0.92,
            grade_distribution={},
            a_plus_percentage=5.0,
            screening_efficiency=5.0,
        )

    @pytest.fixture
    def bear_market_discovery(self) -> APlusDiscoveryResult:
        """Create discovery result with bear market context."""
        return APlusDiscoveryResult(
            asset_type="stock",
            total_screened=100,
            candidates_found=2,
            discovery_criteria=APlusCriteria(),
            market_context=MarketRegime(
                regime_type="bear",
                vix_level=35.0,
                inflation_rate=5.5,
                interest_rate_trend="rising",
                market_stress_level="high",
                assessment_date=datetime(2025, 3, 10),
            ),
            discovery_timestamp=datetime(2025, 3, 10),
            average_score=0.88,
            grade_distribution={},
            a_plus_percentage=2.0,
            screening_efficiency=2.0,
        )

    @pytest.fixture
    def volatile_market_discovery(self) -> APlusDiscoveryResult:
        """Create discovery result with volatile market context."""
        return APlusDiscoveryResult(
            asset_type="etf",
            total_screened=50,
            candidates_found=3,
            discovery_criteria=APlusCriteria(),
            market_context=MarketRegime(
                regime_type="volatile",
                vix_level=28.0,
                inflation_rate=3.8,
                interest_rate_trend="falling",
                market_stress_level="medium",
                assessment_date=datetime(2025, 3, 10),
            ),
            discovery_timestamp=datetime(2025, 3, 10),
            average_score=0.90,
            grade_distribution={},
            a_plus_percentage=6.0,
            screening_efficiency=6.0,
        )

    @pytest.fixture
    def sideways_market_discovery(self) -> APlusDiscoveryResult:
        """Create discovery result with sideways market context."""
        return APlusDiscoveryResult(
            asset_type="crypto",
            total_screened=30,
            candidates_found=1,
            discovery_criteria=APlusCriteria(),
            market_context=MarketRegime(
                regime_type="sideways",
                vix_level=18.5,
                inflation_rate=3.2,
                interest_rate_trend="stable",
                market_stress_level="low",
                assessment_date=datetime(2025, 3, 10),
            ),
            discovery_timestamp=datetime(2025, 3, 10),
            average_score=0.91,
            grade_distribution={},
            a_plus_percentage=3.0,
            screening_efficiency=3.0,
        )

    def test_should_extract_market_regime_when_bull_market(self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult) -> None:
        """Test extraction of market regime from bull market discovery."""
        # Act
        regime = extractor.extract_market_regime(bull_market_discovery)

        # Assert
        assert regime is not None
        assert regime.regime_type == "bull"
        assert regime.vix_level == approx(12.5)
        assert regime.inflation_rate == approx(2.5)
        assert regime.interest_rate_trend == "stable"
        assert regime.market_stress_level == "low"

    def test_should_extract_market_regime_when_bear_market(self, extractor: MarketContextExtractor, bear_market_discovery: APlusDiscoveryResult) -> None:
        """Test extraction of market regime from bear market discovery."""
        # Act
        regime = extractor.extract_market_regime(bear_market_discovery)

        # Assert
        assert regime is not None
        assert regime.regime_type == "bear"
        assert regime.vix_level == approx(35.0)
        assert regime.inflation_rate == approx(5.5)
        assert regime.interest_rate_trend == "rising"
        assert regime.market_stress_level == "high"

    def test_should_extract_market_regime_when_sideways_market(self, extractor: MarketContextExtractor, sideways_market_discovery: APlusDiscoveryResult) -> None:
        """Test extraction of market regime from sideways market discovery."""
        # Act
        regime = extractor.extract_market_regime(sideways_market_discovery)

        # Assert
        assert regime is not None
        assert regime.regime_type == "sideways"
        assert regime.vix_level == approx(18.5)
        assert regime.inflation_rate == approx(3.2)
        assert regime.interest_rate_trend == "stable"
        assert regime.market_stress_level == "low"

    def test_should_extract_market_regime_when_volatile_market(self, extractor: MarketContextExtractor, volatile_market_discovery: APlusDiscoveryResult) -> None:
        """Test extraction of market regime from volatile market discovery."""
        # Act
        regime = extractor.extract_market_regime(volatile_market_discovery)

        # Assert
        assert regime is not None
        assert regime.regime_type == "volatile"
        assert regime.vix_level == approx(28.0)
        assert regime.interest_rate_trend == "falling"

    def test_should_return_none_when_market_context_is_none(self, extractor: MarketContextExtractor, mocker) -> None:
        """Test extraction returns None when market context is missing."""
        # Arrange
        discovery = mocker.Mock(spec=APlusDiscoveryResult)
        discovery.market_context = None

        # Act
        regime = extractor.extract_market_regime(discovery)

        # Assert
        assert regime is None

    def test_should_return_none_when_extraction_raises_exception(self, extractor: MarketContextExtractor, mocker) -> None:
        """Test extraction returns None when exception occurs."""
        # Arrange
        discovery = mocker.Mock(spec=APlusDiscoveryResult)
        discovery.market_context = mocker.Mock(side_effect=RuntimeError("Data error"))

        # Act
        regime = extractor.extract_market_regime(discovery)

        # Assert
        assert regime is None

    def test_should_extract_vix_indicators_when_low_volatility(self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult) -> None:
        """Test VIX indicators extraction with low volatility."""
        # Act
        vix_indicators = extractor.extract_vix_indicators(bull_market_discovery)

        # Assert
        assert vix_indicators is not None
        assert vix_indicators.current_vix == approx(12.5)
        assert vix_indicators.volatility_regime == "low"
        assert vix_indicators.vix_trend == "falling"
        assert 0 <= vix_indicators.vix_percentile <= 100

    def test_should_extract_vix_indicators_when_high_volatility(self, extractor: MarketContextExtractor, bear_market_discovery: APlusDiscoveryResult) -> None:
        """Test VIX indicators extraction with high volatility."""
        # Act
        vix_indicators = extractor.extract_vix_indicators(bear_market_discovery)

        # Assert
        assert vix_indicators is not None
        assert vix_indicators.current_vix == approx(35.0)
        assert vix_indicators.volatility_regime == "extreme"
        assert vix_indicators.vix_trend == "rising"
        assert vix_indicators.vix_percentile > 85.0

    def test_should_extract_vix_indicators_when_market_context_none(self, extractor: MarketContextExtractor, mocker) -> None:
        """Test VIX indicators extraction returns None when context missing."""
        # Arrange
        discovery = mocker.Mock(spec=APlusDiscoveryResult)
        discovery.market_context = None

        # Act
        vix_indicators = extractor.extract_vix_indicators(discovery)

        # Assert
        assert vix_indicators is None

    def test_should_extract_vix_indicators_with_normal_regime(self, extractor: MarketContextExtractor, volatile_market_discovery: APlusDiscoveryResult) -> None:
        """Test VIX indicators extraction with normal volatility regime."""
        # Act
        vix_indicators = extractor.extract_vix_indicators(volatile_market_discovery)

        # Assert
        assert vix_indicators is not None
        assert vix_indicators.current_vix == approx(28.0)
        assert vix_indicators.volatility_regime == "elevated"
        assert vix_indicators.vix_percentile > 50.0


class TestMarketContextExtractorVIXCalculations:
    """Test VIX calculations and classifications."""

    @pytest.fixture
    def extractor(self) -> MarketContextExtractor:
        """Create extractor instance for testing."""
        return MarketContextExtractor()

    @pytest.mark.parametrize(
        "vix_level,expected_regime",
        [
            (12.0, "low"),
            (14.9, "low"),
            (15.0, "normal"),
            (18.0, "normal"),
            (19.9, "normal"),
            (20.0, "elevated"),
            (25.0, "elevated"),
            (29.9, "elevated"),
            (30.0, "extreme"),
            (35.0, "extreme"),
            (50.0, "extreme"),
        ],
    )
    def test_should_classify_volatility_regimes_correctly(self, extractor: MarketContextExtractor, vix_level: float, expected_regime: str) -> None:
        """Test volatility regime classification for various VIX levels."""
        # Act
        regime = extractor._classify_volatility_regime(vix_level)

        # Assert
        assert regime == expected_regime

    @pytest.mark.parametrize(
        "vix_level,min_percentile,max_percentile",
        [
            (0.0, 0.0, 10.0),
            (8.0, 0.0, 10.0),
            (10.0, 10.0, 15.0),
            (12.5, 10.0, 30.0),
            (15.0, 30.0, 40.0),
            (18.0, 30.0, 60.0),
            (20.0, 60.0, 65.0),
            (25.0, 60.0, 85.0),
            (30.0, 85.0, 95.0),
            (35.0, 85.0, 95.0),
            (40.0, 95.0, 99.0),
            (50.0, 95.0, 99.0),
        ],
    )
    def test_should_calculate_vix_percentile_within_ranges(
        self,
        extractor: MarketContextExtractor,
        vix_level: float,
        min_percentile: float,
        max_percentile: float,
    ) -> None:
        """Test VIX percentile calculation for various levels."""
        # Act
        percentile = extractor._calculate_vix_percentile(vix_level)

        # Assert
        assert min_percentile <= percentile <= max_percentile
        assert 0.0 <= percentile <= 100.0

    def test_should_calculate_vix_percentile_monotonically_increasing(self, extractor: MarketContextExtractor) -> None:
        """Test that VIX percentile increases monotonically with VIX level."""
        # Arrange
        vix_levels = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 50.0]

        # Act
        percentiles = [extractor._calculate_vix_percentile(vix) for vix in vix_levels]

        # Assert
        for i in range(len(percentiles) - 1):
            assert percentiles[i] <= percentiles[i + 1]


class TestMarketContextExtractorVIXTrend:
    """Test VIX trend determination."""

    @pytest.fixture
    def extractor(self) -> MarketContextExtractor:
        """Create extractor instance for testing."""
        return MarketContextExtractor()

    @pytest.mark.parametrize(
        "regime_type,stress_level,expected_trend",
        [
            ("bull", "low", "falling"),
            ("bull", "medium", "stable"),
            ("bull", "high", "rising"),
            ("bear", "low", "stable"),
            ("bear", "medium", "stable"),
            ("bear", "high", "rising"),
            ("sideways", "low", "stable"),
            ("sideways", "high", "rising"),
            ("volatile", "low", "rising"),
            ("volatile", "medium", "rising"),
            ("volatile", "high", "rising"),
        ],
    )
    def test_should_determine_vix_trend_correctly(
        self,
        extractor: MarketContextExtractor,
        regime_type: str,
        stress_level: str,
        expected_trend: str,
    ) -> None:
        """Test VIX trend determination for various regime and stress combinations."""
        # Arrange
        regime = MarketRegime(
            regime_type=regime_type,  # type: ignore
            vix_level=20.0,
            inflation_rate=3.0,
            interest_rate_trend="stable",
            market_stress_level=stress_level,  # type: ignore
        )

        # Act
        trend = extractor._determine_vix_trend(regime)

        # Assert
        assert trend == expected_trend


class TestMarketContextExtractorMacroIndicators:
    """Test macroeconomic indicator extraction."""

    @pytest.fixture
    def extractor(self) -> MarketContextExtractor:
        """Create extractor instance for testing."""
        return MarketContextExtractor()

    @pytest.fixture
    def bull_market_discovery(self) -> APlusDiscoveryResult:
        """Create discovery result with bull market context."""
        return APlusDiscoveryResult(
            asset_type="stock",
            total_screened=100,
            candidates_found=5,
            discovery_criteria=APlusCriteria(),
            market_context=MarketRegime(
                regime_type="bull",
                vix_level=12.5,
                inflation_rate=2.5,
                interest_rate_trend="stable",
                market_stress_level="low",
                assessment_date=datetime(2025, 3, 10),
            ),
            discovery_timestamp=datetime(2025, 3, 10),
            average_score=0.92,
            grade_distribution={},
            a_plus_percentage=5.0,
            screening_efficiency=5.0,
        )

    @pytest.fixture
    def bear_market_discovery(self) -> APlusDiscoveryResult:
        """Create discovery result with bear market context."""
        return APlusDiscoveryResult(
            asset_type="stock",
            total_screened=100,
            candidates_found=2,
            discovery_criteria=APlusCriteria(),
            market_context=MarketRegime(
                regime_type="bear",
                vix_level=35.0,
                inflation_rate=5.5,
                interest_rate_trend="rising",
                market_stress_level="high",
                assessment_date=datetime(2025, 3, 10),
            ),
            discovery_timestamp=datetime(2025, 3, 10),
            average_score=0.88,
            grade_distribution={},
            a_plus_percentage=2.0,
            screening_efficiency=2.0,
        )

    def test_should_extract_macro_indicators_when_stable_environment(self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult) -> None:
        """Test macro indicators extraction in stable environment."""
        # Act
        macro = extractor.extract_macro_indicators(bull_market_discovery)

        # Assert
        assert macro is not None
        assert isinstance(macro, MacroIndicators)
        assert macro.inflation_rate == approx(2.5)
        assert macro.interest_rate_trend == "stable"
        assert macro.interest_rate > 0
        assert macro.gdp_growth is None
        assert macro.unemployment_rate is None

    def test_should_extract_macro_indicators_when_rising_rates(self, extractor: MarketContextExtractor, bear_market_discovery: APlusDiscoveryResult) -> None:
        """Test macro indicators extraction with rising interest rates."""
        # Act
        macro = extractor.extract_macro_indicators(bear_market_discovery)

        # Assert
        assert macro is not None
        assert macro.inflation_rate == approx(5.5)
        assert macro.interest_rate_trend == "rising"
        assert macro.interest_rate == approx(5.5)

    def test_should_extract_macro_indicators_return_none_when_context_missing(self, extractor: MarketContextExtractor, mocker) -> None:
        """Test macro indicators extraction returns None when context missing."""
        # Arrange
        discovery = mocker.Mock(spec=APlusDiscoveryResult)
        discovery.market_context = None

        # Act
        macro = extractor.extract_macro_indicators(discovery)

        # Assert
        assert macro is None

    @pytest.mark.parametrize(
        "interest_rate_trend,expected_rate",
        [
            ("rising", 5.5),
            ("falling", 4.5),
            ("stable", 5.0),
        ],
    )
    def test_should_estimate_interest_rate_based_on_trend(
        self,
        extractor: MarketContextExtractor,
        interest_rate_trend: str,
        expected_rate: float,
    ) -> None:
        """Test interest rate estimation based on trend."""
        # Arrange
        regime = MarketRegime(
            regime_type="bull",
            vix_level=15.0,
            inflation_rate=3.0,
            interest_rate_trend=interest_rate_trend,  # type: ignore
            market_stress_level="low",
        )

        # Act
        rate = extractor._estimate_interest_rate(regime)

        # Assert
        assert rate == approx(expected_rate)

    def test_should_extract_gdp_growth_returns_none(self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult) -> None:
        """Test GDP growth extraction returns None (not in schema)."""
        # Act
        gdp = extractor._extract_gdp_growth(bull_market_discovery)

        # Assert
        assert gdp is None

    def test_should_extract_unemployment_rate_returns_none(self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult) -> None:
        """Test unemployment rate extraction returns None (not in schema)."""
        # Act
        unemployment = extractor._extract_unemployment_rate(bull_market_discovery)

        # Assert
        assert unemployment is None


class TestMarketContextExtractorRiskAssessment:
    """Test risk environment assessment."""

    @pytest.fixture
    def extractor(self) -> MarketContextExtractor:
        """Create extractor instance for testing."""
        return MarketContextExtractor()

    @pytest.fixture
    def favorable_components(self) -> tuple[MarketRegime, VIXIndicators, MacroIndicators]:
        """Create favorable market components."""
        regime = MarketRegime(
            regime_type="bull",
            vix_level=12.0,
            inflation_rate=2.5,
            interest_rate_trend="stable",
            market_stress_level="low",
        )
        vix = VIXIndicators(
            current_vix=12.0,
            vix_percentile=20.0,
            vix_trend="falling",
            volatility_regime="low",
        )
        macro = MacroIndicators(
            inflation_rate=2.5,
            interest_rate=5.0,
            interest_rate_trend="stable",
        )
        return regime, vix, macro

    @pytest.fixture
    def challenging_components(self) -> tuple[MarketRegime, VIXIndicators, MacroIndicators]:
        """Create challenging market components."""
        regime = MarketRegime(
            regime_type="bear",
            vix_level=40.0,
            inflation_rate=6.0,
            interest_rate_trend="rising",
            market_stress_level="high",
        )
        vix = VIXIndicators(
            current_vix=40.0,
            vix_percentile=95.0,
            vix_trend="rising",
            volatility_regime="extreme",
        )
        macro = MacroIndicators(
            inflation_rate=6.0,
            interest_rate=5.5,
            interest_rate_trend="rising",
        )
        return regime, vix, macro

    def test_should_assess_favorable_risk_environment(
        self,
        extractor: MarketContextExtractor,
        favorable_components: tuple[MarketRegime, VIXIndicators, MacroIndicators],
    ) -> None:
        """Test risk environment assessment for favorable conditions."""
        # Arrange
        regime, vix, macro = favorable_components

        # Act
        risk_env = extractor._assess_risk_environment(regime, vix, macro)

        # Assert
        assert risk_env == "favorable"

    def test_should_assess_challenging_risk_environment(
        self,
        extractor: MarketContextExtractor,
        challenging_components: tuple[MarketRegime, VIXIndicators, MacroIndicators],
    ) -> None:
        """Test risk environment assessment for challenging conditions."""
        # Arrange
        regime, vix, macro = challenging_components

        # Act
        risk_env = extractor._assess_risk_environment(regime, vix, macro)

        # Assert
        assert risk_env == "challenging"

    def test_should_assess_neutral_risk_environment(self, extractor: MarketContextExtractor) -> None:
        """Test risk environment assessment for neutral conditions."""
        # Arrange
        regime = MarketRegime(
            regime_type="sideways",
            vix_level=18.0,
            inflation_rate=3.0,
            interest_rate_trend="stable",
            market_stress_level="low",
        )
        vix = VIXIndicators(
            current_vix=18.0,
            vix_percentile=45.0,
            vix_trend="stable",
            volatility_regime="normal",
        )
        macro = MacroIndicators(
            inflation_rate=3.0,
            interest_rate=5.0,
            interest_rate_trend="stable",
        )

        # Act
        risk_env = extractor._assess_risk_environment(regime, vix, macro)

        # Assert
        assert risk_env in ["favorable", "neutral"]

    @pytest.mark.parametrize(
        "regime_type,stress_level,vix_regime,inflation,ir_trend,expected_risk",
        [
            ("bull", "low", "low", 2.0, "stable", "favorable"),
            ("bear", "high", "extreme", 6.0, "rising", "challenging"),
            ("volatile", "medium", "elevated", 3.5, "stable", "neutral"),
            ("sideways", "low", "normal", 3.0, "stable", "favorable"),
        ],
    )
    def test_should_assess_risk_environment_for_various_combinations(
        self,
        extractor: MarketContextExtractor,
        regime_type: str,
        stress_level: str,
        vix_regime: str,
        inflation: float,
        ir_trend: str,
        expected_risk: str,
    ) -> None:
        """Test risk assessment for various market combinations."""
        # Arrange
        regime = MarketRegime(
            regime_type=regime_type,  # type: ignore
            vix_level=20.0,
            inflation_rate=inflation,
            interest_rate_trend=ir_trend,  # type: ignore
            market_stress_level=stress_level,  # type: ignore
        )
        vix = VIXIndicators(
            current_vix=20.0,
            vix_percentile=50.0,
            vix_trend="stable",
            volatility_regime=vix_regime,  # type: ignore
        )
        macro = MacroIndicators(
            inflation_rate=inflation,
            interest_rate=5.0,
            interest_rate_trend=ir_trend,  # type: ignore
        )

        # Act
        risk_env = extractor._assess_risk_environment(regime, vix, macro)

        # Assert
        assert risk_env == expected_risk


class TestMarketContextExtractorAllocationImplications:
    """Test allocation implications generation."""

    @pytest.fixture
    def extractor(self) -> MarketContextExtractor:
        """Create extractor instance for testing."""
        return MarketContextExtractor()

    def test_should_generate_allocation_implications_for_bull_market(self, extractor: MarketContextExtractor) -> None:
        """Test allocation implications for bull market."""
        # Arrange
        regime = MarketRegime(
            regime_type="bull",
            vix_level=12.0,
            inflation_rate=2.5,
            interest_rate_trend="stable",
            market_stress_level="low",
        )
        vix = VIXIndicators(
            current_vix=12.0,
            vix_percentile=20.0,
            vix_trend="falling",
            volatility_regime="low",
        )
        macro = MacroIndicators(
            inflation_rate=2.5,
            interest_rate=5.0,
            interest_rate_trend="stable",
        )

        # Act
        implications = extractor._generate_allocation_implications(regime, vix, macro, "favorable")

        # Assert
        assert len(implications) > 0
        assert any("bull" in imp.lower() for imp in implications)
        assert any("growth" in imp.lower() for imp in implications)

    def test_should_generate_allocation_implications_for_bear_market(self, extractor: MarketContextExtractor) -> None:
        """Test allocation implications for bear market."""
        # Arrange
        regime = MarketRegime(
            regime_type="bear",
            vix_level=40.0,
            inflation_rate=6.0,
            interest_rate_trend="rising",
            market_stress_level="high",
        )
        vix = VIXIndicators(
            current_vix=40.0,
            vix_percentile=95.0,
            vix_trend="rising",
            volatility_regime="extreme",
        )
        macro = MacroIndicators(
            inflation_rate=6.0,
            interest_rate=5.5,
            interest_rate_trend="rising",
        )

        # Act
        implications = extractor._generate_allocation_implications(regime, vix, macro, "challenging")

        # Assert
        assert len(implications) > 0
        assert any("bear" in imp.lower() or "defensive" in imp.lower() for imp in implications)
        assert any("challenging" in imp.lower() or "conservative" in imp.lower() for imp in implications)

    def test_should_generate_allocation_implications_for_extreme_volatility(self, extractor: MarketContextExtractor) -> None:
        """Test allocation implications for extreme volatility."""
        # Arrange
        regime = MarketRegime(
            regime_type="volatile",
            vix_level=45.0,
            inflation_rate=3.0,
            interest_rate_trend="stable",
            market_stress_level="medium",
        )
        vix = VIXIndicators(
            current_vix=45.0,
            vix_percentile=97.0,
            vix_trend="rising",
            volatility_regime="extreme",
        )
        macro = MacroIndicators(
            inflation_rate=3.0,
            interest_rate=5.0,
            interest_rate_trend="stable",
        )

        # Act
        implications = extractor._generate_allocation_implications(regime, vix, macro, "neutral")

        # Assert
        assert len(implications) > 0
        assert any("extreme" in imp.lower() or "hedging" in imp.lower() for imp in implications)

    def test_should_generate_implications_for_rising_interest_rates(self, extractor: MarketContextExtractor) -> None:
        """Test allocation implications for rising interest rates."""
        # Arrange
        regime = MarketRegime(
            regime_type="bull",
            vix_level=15.0,
            inflation_rate=3.0,
            interest_rate_trend="rising",
            market_stress_level="low",
        )
        vix = VIXIndicators(
            current_vix=15.0,
            vix_percentile=40.0,
            vix_trend="stable",
            volatility_regime="normal",
        )
        macro = MacroIndicators(
            inflation_rate=3.0,
            interest_rate=5.5,
            interest_rate_trend="rising",
        )

        # Act
        implications = extractor._generate_allocation_implications(regime, vix, macro, "favorable")

        # Assert
        assert any("rising rates" in imp.lower() or "value stocks" in imp.lower() for imp in implications)

    def test_should_generate_implications_for_high_inflation(self, extractor: MarketContextExtractor) -> None:
        """Test allocation implications for high inflation."""
        # Arrange
        regime = MarketRegime(
            regime_type="sideways",
            vix_level=20.0,
            inflation_rate=5.0,
            interest_rate_trend="stable",
            market_stress_level="medium",
        )
        vix = VIXIndicators(
            current_vix=20.0,
            vix_percentile=55.0,
            vix_trend="stable",
            volatility_regime="normal",
        )
        macro = MacroIndicators(
            inflation_rate=5.0,
            interest_rate=5.0,
            interest_rate_trend="stable",
        )

        # Act
        implications = extractor._generate_allocation_implications(regime, vix, macro, "neutral")

        # Assert
        assert any("inflation" in imp.lower() or "commodities" in imp.lower() for imp in implications)


class TestMarketContextExtractorSummary:
    """Test market context summary generation."""

    @pytest.fixture
    def extractor(self) -> MarketContextExtractor:
        """Create extractor instance for testing."""
        return MarketContextExtractor()

    @pytest.fixture
    def complete_discovery(self) -> APlusDiscoveryResult:
        """Create discovery with complete market context."""
        return APlusDiscoveryResult(
            asset_type="stock",
            total_screened=100,
            candidates_found=5,
            discovery_criteria=APlusCriteria(),
            market_context=MarketRegime(
                regime_type="bull",
                vix_level=12.5,
                inflation_rate=2.5,
                interest_rate_trend="stable",
                market_stress_level="low",
                assessment_date=datetime(2025, 3, 10),
            ),
            discovery_timestamp=datetime(2025, 3, 10),
            average_score=0.92,
            grade_distribution={},
            a_plus_percentage=5.0,
            screening_efficiency=5.0,
        )

    def test_should_generate_market_context_summary_with_complete_data(self, extractor: MarketContextExtractor, complete_discovery: APlusDiscoveryResult) -> None:
        """Test market context summary generation with complete data."""
        # Act
        summary = extractor.get_market_context_summary(complete_discovery)

        # Assert
        assert summary is not None
        assert isinstance(summary, MarketContextSummary)
        assert summary.market_regime.regime_type == "bull"
        assert summary.vix_indicators.current_vix == approx(12.5)
        assert summary.macro_indicators.inflation_rate == approx(2.5)
        assert summary.risk_environment == "favorable"
        assert len(summary.allocation_implications) > 0

    def test_should_create_conservative_summary_when_extraction_fails(self, extractor: MarketContextExtractor, mocker) -> None:
        """Test conservative summary creation when extraction fails."""
        # Arrange
        mocker.patch.object(extractor, "extract_market_regime", return_value=None)
        discovery = APlusDiscoveryResult(
            asset_type="stock",
            total_screened=100,
            candidates_found=5,
            discovery_criteria=APlusCriteria(),
            market_context=MarketRegime(
                regime_type="bull",
                vix_level=15.0,
                inflation_rate=3.0,
                interest_rate_trend="stable",
                market_stress_level="low",
            ),
            discovery_timestamp=datetime(2025, 3, 10),
            average_score=0.90,
            grade_distribution={},
            a_plus_percentage=5.0,
            screening_efficiency=5.0,
        )

        # Act
        summary = extractor.get_market_context_summary(discovery)

        # Assert
        assert summary is not None
        assert summary.risk_environment == "neutral"
        assert summary.market_regime.regime_type == "sideways"
        assert summary.vix_indicators.current_vix == approx(20.0)

    def test_should_return_conservative_summary_when_all_extractions_fail(self, extractor: MarketContextExtractor, mocker) -> None:
        """Test that conservative summary is returned when all extractions fail."""
        # Arrange - create a discovery that causes all extractions to fail
        bad_discovery = mocker.Mock(spec=APlusDiscoveryResult)
        bad_discovery.market_context = mocker.Mock(side_effect=RuntimeError("Error"))

        # Act
        summary = extractor.get_market_context_summary(bad_discovery)

        # Assert - Should return conservative summary, not None
        assert summary is not None
        assert summary.market_regime.regime_type == "sideways"
        assert summary.risk_environment == "neutral"

    def test_should_include_valid_allocation_implications_in_summary(self, extractor: MarketContextExtractor, complete_discovery: APlusDiscoveryResult) -> None:
        """Test that summary includes meaningful allocation implications."""
        # Act
        summary = extractor.get_market_context_summary(complete_discovery)

        # Assert
        assert summary is not None
        assert isinstance(summary.allocation_implications, list)
        assert all(isinstance(imp, str) for imp in summary.allocation_implications)
        assert all(len(imp) > 0 for imp in summary.allocation_implications)


class TestMarketContextExtractorEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def extractor(self) -> MarketContextExtractor:
        """Create extractor instance for testing."""
        return MarketContextExtractor()

    def test_should_handle_minimum_vix_level(self, extractor: MarketContextExtractor) -> None:
        """Test handling of minimum VIX level."""
        # Act
        percentile = extractor._calculate_vix_percentile(0.0)
        regime = extractor._classify_volatility_regime(0.0)

        # Assert
        assert percentile >= 0.0 and percentile <= 100.0
        assert regime == "low"

    def test_should_handle_maximum_vix_level(self, extractor: MarketContextExtractor) -> None:
        """Test handling of maximum VIX level."""
        # Act
        percentile = extractor._calculate_vix_percentile(100.0)
        regime = extractor._classify_volatility_regime(100.0)

        # Assert
        assert percentile >= 0.0 and percentile <= 100.0
        assert regime == "extreme"

    def test_should_handle_extreme_inflation_rates(self, extractor: MarketContextExtractor) -> None:
        """Test handling of extreme inflation rates."""
        # Arrange
        regime = MarketRegime(
            regime_type="bear",
            vix_level=30.0,
            inflation_rate=15.0,  # Very high inflation
            interest_rate_trend="rising",
            market_stress_level="high",
        )
        vix = VIXIndicators(
            current_vix=30.0,
            vix_percentile=90.0,
            vix_trend="rising",
            volatility_regime="elevated",
        )
        macro = MacroIndicators(
            inflation_rate=15.0,
            interest_rate=5.5,
            interest_rate_trend="rising",
        )

        # Act
        risk_env = extractor._assess_risk_environment(regime, vix, macro)
        implications = extractor._generate_allocation_implications(regime, vix, macro, risk_env)

        # Assert
        assert risk_env == "challenging"
        assert len(implications) > 0
        assert any("inflation" in imp.lower() or "assets" in imp.lower() for imp in implications)

    def test_should_handle_low_inflation_rates(self, extractor: MarketContextExtractor) -> None:
        """Test handling of low inflation rates."""
        # Arrange
        regime = MarketRegime(
            regime_type="bull",
            vix_level=10.0,
            inflation_rate=0.5,  # Very low inflation
            interest_rate_trend="falling",
            market_stress_level="low",
        )
        vix = VIXIndicators(
            current_vix=10.0,
            vix_percentile=15.0,
            vix_trend="falling",
            volatility_regime="low",
        )
        macro = MacroIndicators(
            inflation_rate=0.5,
            interest_rate=4.5,
            interest_rate_trend="falling",
        )

        # Act
        risk_env = extractor._assess_risk_environment(regime, vix, macro)
        implications = extractor._generate_allocation_implications(regime, vix, macro, risk_env)

        # Assert
        assert risk_env == "favorable"
        assert any("low inflation" in imp.lower() for imp in implications)


class TestMarketContextExtractorLogging:
    """Test logging functionality."""

    def test_should_log_on_successful_extraction(self, mocker) -> None:
        """Test that successful extractions are logged."""
        # Arrange
        mock_logger = mocker.Mock(spec=logging.Logger)
        extractor = MarketContextExtractor(logger=mock_logger)
        discovery = APlusDiscoveryResult(
            asset_type="stock",
            total_screened=100,
            candidates_found=5,
            discovery_criteria=APlusCriteria(),
            market_context=MarketRegime(
                regime_type="bull",
                vix_level=15.0,
                inflation_rate=3.0,
                interest_rate_trend="stable",
                market_stress_level="low",
            ),
            discovery_timestamp=datetime(2025, 3, 10),
            average_score=0.90,
            grade_distribution={},
            a_plus_percentage=5.0,
            screening_efficiency=5.0,
        )

        # Act
        extractor.extract_market_regime(discovery)

        # Assert
        assert mock_logger.info.call_count >= 2  # Initialization + extraction

    def test_should_log_errors_on_extraction_failure(self, mocker) -> None:
        """Test that errors are logged on extraction failure."""
        # Arrange
        mock_logger = mocker.Mock(spec=logging.Logger)
        extractor = MarketContextExtractor(logger=mock_logger)
        bad_discovery = mocker.Mock(spec=APlusDiscoveryResult)
        bad_discovery.market_context = mocker.Mock(side_effect=RuntimeError("Test error"))

        # Act
        extractor.extract_market_regime(bad_discovery)

        # Assert
        assert mock_logger.error.called
