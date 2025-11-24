"""Unit tests for CryptoAnalyzer."""

import pytest
from pytest import approx

from finwiz.scoring.asset_analyzers.crypto_analyzer import CryptoAnalyzer


class TestCryptoAnalyzer:
    """Test suite for CryptoAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create CryptoAnalyzer instance."""
        return CryptoAnalyzer()

    @pytest.fixture
    def excellent_crypto_data(self):
        """Create data for an excellent cryptocurrency."""
        return {
            "market_cap": 500e9,  # $500B (mega cap)
            "volume_24h": 20e9,  # $20B (very high liquidity)
            "age_years": 10.0,  # 10 years (very established)
            "circulating_supply": 19e6,
            "max_supply": 21e6,  # 90% circulating
        }

    @pytest.fixture
    def poor_crypto_data(self):
        """Create data for a poor cryptocurrency."""
        return {
            "market_cap": 50e6,  # $50M (micro cap)
            "volume_24h": 5e6,  # $5M (low liquidity)
            "age_years": 0.5,  # 6 months (very young)
            "circulating_supply": 10e6,
            "max_supply": 100e6,  # 10% circulating
        }

    def test_calculate_fundamental_score_excellent_crypto(self, analyzer, excellent_crypto_data):
        """Test scoring for excellent cryptocurrency."""
        score, details = analyzer.calculate_fundamental_score(excellent_crypto_data)

        # Should get high score
        assert score >= 0.9
        assert details["fundamental_score"] == score
        assert details["market_cap_score"] == approx(1.0)
        assert details["volume_score"] == approx(1.0)
        assert details["age_score"] == approx(1.0)

    def test_calculate_fundamental_score_poor_crypto(self, analyzer, poor_crypto_data):
        """Test scoring for poor cryptocurrency."""
        score, details = analyzer.calculate_fundamental_score(poor_crypto_data)

        # Should get low score
        assert score <= 0.3
        assert details["fundamental_score"] == score
        assert details["market_cap_score"] == approx(0.2)
        assert details["volume_score"] == approx(0.2)
        assert details["age_score"] == approx(0.2)

    def test_extract_metrics(self, analyzer, excellent_crypto_data):
        """Test metric extraction."""
        metrics = analyzer.extract_metrics(excellent_crypto_data)

        assert metrics["market_cap"] == 500e9
        assert metrics["volume_24h"] == 20e9
        assert metrics["age_years"] == approx(10.0)
        assert metrics["circulating_supply"] == 19e6
        assert metrics["max_supply"] == 21e6

    def test_validate_data_valid(self, analyzer, excellent_crypto_data):
        """Test data validation with valid data."""
        assert analyzer.validate_data(excellent_crypto_data) is True

    def test_validate_data_missing_fields(self, analyzer):
        """Test data validation with missing fields."""
        incomplete_data = {"market_cap": 100e9}  # Missing other required fields
        assert analyzer.validate_data(incomplete_data) is False

    def test_score_market_cap_thresholds(self, analyzer):
        """Test market cap scoring thresholds."""
        assert analyzer._score_market_cap(200e9) == approx(1.0)  # Mega cap
        assert analyzer._score_market_cap(50e9) == approx(0.8)  # Large cap
        assert analyzer._score_market_cap(5e9) == approx(0.6)  # Mid cap
        assert analyzer._score_market_cap(500e6) == approx(0.4)  # Small cap
        assert analyzer._score_market_cap(50e6) == approx(0.2)  # Micro cap

    def test_score_volume_thresholds(self, analyzer):
        """Test volume scoring thresholds."""
        assert analyzer._score_volume(15e9) == approx(1.0)  # Very high
        assert analyzer._score_volume(5e9) == approx(0.8)  # High
        assert analyzer._score_volume(500e6) == approx(0.6)  # Good
        assert analyzer._score_volume(50e6) == approx(0.4)  # Moderate
        assert analyzer._score_volume(5e6) == approx(0.2)  # Low

    def test_score_age_thresholds(self, analyzer):
        """Test age scoring thresholds."""
        assert analyzer._score_age(10.0) == approx(1.0)  # Very established
        assert analyzer._score_age(4.0) == approx(0.8)  # Established
        assert analyzer._score_age(2.5) == approx(0.6)  # Maturing
        assert analyzer._score_age(1.5) == approx(0.4)  # Young
        assert analyzer._score_age(0.5) == approx(0.2)  # Very young

    def test_score_supply_metrics_high_circulation(self, analyzer):
        """Test supply metrics with high circulation ratio."""
        score = analyzer._score_supply_metrics(95e6, 100e6)  # 95% circulating
        assert score == approx(1.0)

    def test_score_supply_metrics_low_circulation(self, analyzer):
        """Test supply metrics with low circulation ratio."""
        score = analyzer._score_supply_metrics(10e6, 100e6)  # 10% circulating
        assert score == approx(0.2)

    def test_score_supply_metrics_unlimited_supply(self, analyzer):
        """Test supply metrics with unlimited supply."""
        score = analyzer._score_supply_metrics(100e6, 0)  # No max supply
        assert score == approx(0.5)  # Neutral score
