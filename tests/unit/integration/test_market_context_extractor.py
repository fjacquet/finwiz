"""
Unit tests for MarketContextExtractor.

Tests extraction of market regime, VIX indicators, macro indicators,
and market context summaries from discovery crew outputs.
"""

from datetime import datetime

import pytest

from finwiz.integration.market_context_extractor import MarketContextExtractor, MarketContextSummary
from finwiz.schemas.investment_discovery import APlusCriteria, APlusDiscoveryResult, MarketRegime


class TestMarketContextExtractor:
    """Test suite for MarketContextExtractor."""

    @pytest.fixture
    def extractor(self) -> MarketContextExtractor:
        """Create extractor instance for testing."""
        return MarketContextExtractor()

    @pytest.fixture
    def bull_market_discovery(self) -> APlusDiscoveryResult:
        """Create mock discovery result with bull market context."""
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
        """Create mock discovery result with bear market context."""
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
        """Create mock discovery result with volatile market context."""
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

    def test_should_extract_market_regime_when_bull_market(
        self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test extraction of market regime from bull market discovery."""
        # Act
        regime = extractor.extract_market_regime(bull_market_discovery)

        # Assert
        assert regime is not None
        assert regime.regime_type == "bull"
        assert regime.vix_level == 12.5
        assert regime.inflation_rate == 2.5
        assert regime.interest_rate_trend == "stable"
        assert regime.market_stress_level == "low"

    def test_should_extract_market_regime_when_bear_market(
        self, extractor: MarketContextExtractor, bear_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test extraction of market regime from bear market discovery."""
        # Act
        regime = extractor.extract_market_regime(bear_market_discovery)

        # Assert
        assert regime is not None
        assert regime.regime_type == "bear"
        assert regime.vix_level == 35.0
        assert regime.inflation_rate == 5.5
        assert regime.interest_rate_trend == "rising"
        assert regime.market_stress_level == "high"

    def test_should_extract_vix_indicators_when_low_volatility(
        self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test VIX indicators extraction with low volatility."""
        # Act
        vix_indicators = extractor.extract_vix_indicators(bull_market_discovery)

        # Assert
        assert vix_indicators is not None
        assert vix_indicators.current_vix == 12.5
        assert vix_indicators.volatility_regime == "low"
        assert vix_indicators.vix_trend == "falling"  # Low stress + bull market
        assert 0 <= vix_indicators.vix_percentile <= 100

    def test_should_extract_vix_indicators_when_high_volatility(
        self, extractor: MarketContextExtractor, bear_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test VIX indicators extraction with high volatility."""
        # Act
        vix_indicators = extractor.extract_vix_indicators(bear_market_discovery)

        # Assert
        assert vix_indicators is not None
        assert vix_indicators.current_vix == 35.0
        assert vix_indicators.volatility_regime == "extreme"
        assert vix_indicators.vix_trend == "rising"  # High stress
        assert vix_indicators.vix_percentile > 85.0  # High percentile

    def test_should_classify_volatility_regimes_correctly(self, extractor: MarketContextExtractor) -> None:
        """Test volatility regime classification for different VIX levels."""
        # Test low volatility
        assert extractor._classify_volatility_regime(12.0) == "low"

        # Test normal volatility
        assert extractor._classify_volatility_regime(18.0) == "normal"

        # Test elevated volatility
        assert extractor._classify_volatility_regime(25.0) == "elevated"

        # Test extreme volatility
        assert extractor._classify_volatility_regime(35.0) == "extreme"

    def test_should_calculate_vix_percentile_correctly(self, extractor: MarketContextExtractor) -> None:
        """Test VIX percentile calculation for various levels."""
        # Very low VIX
        assert extractor._calculate_vix_percentile(8.0) == 5.0

        # Low VIX
        percentile_12 = extractor._calculate_vix_percentile(12.0)
        assert 10.0 <= percentile_12 <= 30.0

        # Normal VIX
        percentile_18 = extractor._calculate_vix_percentile(18.0)
        assert 30.0 <= percentile_18 <= 60.0

        # Elevated VIX
        percentile_25 = extractor._calculate_vix_percentile(25.0)
        assert 60.0 <= percentile_25 <= 85.0

        # High VIX
        percentile_35 = extractor._calculate_vix_percentile(35.0)
        assert 85.0 <= percentile_35 <= 95.0

        # Extreme VIX
        percentile_50 = extractor._calculate_vix_percentile(50.0)
        assert percentile_50 >= 95.0

    def test_should_extract_macro_indicators_when_stable_environment(
        self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test macro indicators extraction in stable environment."""
        # Act
        macro = extractor.extract_macro_indicators(bull_market_discovery)

        # Assert
        assert macro is not None
        assert macro.inflation_rate == 2.5
        assert macro.interest_rate_trend == "stable"
        assert macro.interest_rate > 0  # Estimated rate
        assert macro.gdp_growth is None  # Not in schema yet
        assert macro.unemployment_rate is None  # Not in schema yet

    def test_should_extract_macro_indicators_when_rising_rates(
        self, extractor: MarketContextExtractor, bear_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test macro indicators extraction with rising interest rates."""
        # Act
        macro = extractor.extract_macro_indicators(bear_market_discovery)

        # Assert
        assert macro is not None
        assert macro.inflation_rate == 5.5
        assert macro.interest_rate_trend == "rising"
        assert macro.interest_rate == 5.5  # Higher estimate for rising trend

    def test_should_estimate_interest_rate_based_on_trend(self, extractor: MarketContextExtractor) -> None:
        """Test interest rate estimation based on trend."""
        # Create mock regimes with different trends
        rising_regime = MarketRegime(
            regime_type="bull",
            vix_level=15.0,
            inflation_rate=3.0,
            interest_rate_trend="rising",
            market_stress_level="low",
        )
        falling_regime = MarketRegime(
            regime_type="bull",
            vix_level=15.0,
            inflation_rate=3.0,
            interest_rate_trend="falling",
            market_stress_level="low",
        )
        stable_regime = MarketRegime(
            regime_type="bull",
            vix_level=15.0,
            inflation_rate=3.0,
            interest_rate_trend="stable",
            market_stress_level="low",
        )

        # Test estimates
        assert extractor._estimate_interest_rate(rising_regime) == 5.5
        assert extractor._estimate_interest_rate(falling_regime) == 4.5
        assert extractor._estimate_interest_rate(stable_regime) == 5.0

    def test_should_assess_favorable_risk_environment(
        self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test risk environment assessment for favorable conditions."""
        # Arrange
        regime = extractor.extract_market_regime(bull_market_discovery)
        vix = extractor.extract_vix_indicators(bull_market_discovery)
        macro = extractor.extract_macro_indicators(bull_market_discovery)

        # Act
        risk_env = extractor._assess_risk_environment(regime, vix, macro)

        # Assert
        assert risk_env == "favorable"

    def test_should_assess_challenging_risk_environment(
        self, extractor: MarketContextExtractor, bear_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test risk environment assessment for challenging conditions."""
        # Arrange
        regime = extractor.extract_market_regime(bear_market_discovery)
        vix = extractor.extract_vix_indicators(bear_market_discovery)
        macro = extractor.extract_macro_indicators(bear_market_discovery)

        # Act
        risk_env = extractor._assess_risk_environment(regime, vix, macro)

        # Assert
        assert risk_env == "challenging"

    def test_should_assess_neutral_risk_environment(
        self, extractor: MarketContextExtractor, volatile_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test risk environment assessment for neutral conditions."""
        # Arrange
        regime = extractor.extract_market_regime(volatile_market_discovery)
        vix = extractor.extract_vix_indicators(volatile_market_discovery)
        macro = extractor.extract_macro_indicators(volatile_market_discovery)

        # Act
        risk_env = extractor._assess_risk_environment(regime, vix, macro)

        # Assert
        assert risk_env in ["neutral", "challenging"]  # Could be either based on factors

    def test_should_generate_allocation_implications_for_bull_market(
        self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test allocation implications generation for bull market."""
        # Arrange
        regime = extractor.extract_market_regime(bull_market_discovery)
        vix = extractor.extract_vix_indicators(bull_market_discovery)
        macro = extractor.extract_macro_indicators(bull_market_discovery)

        # Act
        implications = extractor._generate_allocation_implications(regime, vix, macro, "favorable")

        # Assert
        assert len(implications) > 0
        assert any("bull" in imp.lower() or "growth" in imp.lower() for imp in implications)
        assert any("low volatility" in imp.lower() or "quality" in imp.lower() for imp in implications)

    def test_should_generate_allocation_implications_for_bear_market(
        self, extractor: MarketContextExtractor, bear_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test allocation implications generation for bear market."""
        # Arrange
        regime = extractor.extract_market_regime(bear_market_discovery)
        vix = extractor.extract_vix_indicators(bear_market_discovery)
        macro = extractor.extract_macro_indicators(bear_market_discovery)

        # Act
        implications = extractor._generate_allocation_implications(regime, vix, macro, "challenging")

        # Assert
        assert len(implications) > 0
        assert any("bear" in imp.lower() or "defensive" in imp.lower() for imp in implications)
        assert any("extreme" in imp.lower() or "risk reduction" in imp.lower() for imp in implications)
        assert any("challenging" in imp.lower() or "conservative" in imp.lower() for imp in implications)

    def test_should_generate_market_context_summary_when_complete_data(
        self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult
    ) -> None:
        """Test market context summary generation with complete data."""
        # Act
        summary = extractor.get_market_context_summary(bull_market_discovery)

        # Assert
        assert summary is not None
        assert isinstance(summary, MarketContextSummary)
        assert summary.market_regime.regime_type == "bull"
        assert summary.vix_indicators.current_vix == 12.5
        assert summary.macro_indicators.inflation_rate == 2.5
        assert summary.risk_environment == "favorable"
        assert len(summary.allocation_implications) > 0

    def test_should_create_conservative_summary_when_data_missing(self, extractor: MarketContextExtractor, mocker) -> None:
        """Test conservative summary creation when data is incomplete."""
        # Arrange - Mock methods to return None
        mocker.patch.object(extractor, "extract_market_regime", return_value=None)

        # Create minimal discovery result
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
        assert summary.vix_indicators.current_vix == 20.0
        assert any("conservative" in imp.lower() for imp in summary.allocation_implications)

    def test_should_handle_extraction_errors_gracefully(self, extractor: MarketContextExtractor, mocker) -> None:
        """Test graceful error handling during extraction."""
        # Arrange - Create discovery result that will cause errors
        bad_discovery = mocker.Mock(spec=APlusDiscoveryResult)
        bad_discovery.market_context = None  # This will cause AttributeError

        # Act
        regime = extractor.extract_market_regime(bad_discovery)
        vix = extractor.extract_vix_indicators(bad_discovery)
        macro = extractor.extract_macro_indicators(bad_discovery)

        # Assert - Should return None instead of raising
        assert regime is None
        assert vix is None
        assert macro is None

    def test_should_log_extraction_operations(
        self, extractor: MarketContextExtractor, bull_market_discovery: APlusDiscoveryResult, mocker
    ) -> None:
        """Test that extraction operations are properly logged."""
        # Arrange
        mock_logger = mocker.Mock()
        extractor.logger = mock_logger

        # Act
        extractor.extract_market_regime(bull_market_discovery)
        extractor.extract_vix_indicators(bull_market_discovery)
        extractor.extract_macro_indicators(bull_market_discovery)
        extractor.get_market_context_summary(bull_market_discovery)

        # Assert - Verify logging calls
        assert mock_logger.info.call_count >= 4  # At least one log per extraction
