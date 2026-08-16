"""
Unit tests for CryptoOpportunityExtractor.

Tests crypto-specific extraction logic using the Template Method pattern.
"""

import pytest
from pytest import approx

from finwiz.orchestrators.discovery.extractors import CryptoOpportunityExtractor


class TestCryptoOpportunityExtractor:
    """Test suite for CryptoOpportunityExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create CryptoOpportunityExtractor instance."""
        return CryptoOpportunityExtractor()

    @pytest.fixture
    def valid_crypto_candidate(self):
        """Create valid crypto candidate for testing."""
        return {
            "symbol": "BTC-USD",
            "name": "Bitcoin",
            "grade": "A+",
            "market_cap_usd": 1200000000000,  # $1.2T
            "volume_24h_usd": 30000000000,  # $30B
            "risk_assessment": {"score": 7.0},
            "technology": {"consensus_mechanism": "Proof of Work", "primary_use_case": "Store of value", "competitive_advantage": "Network effect"},
            "implementation": {"entry_strategy": "Dollar-cost averaging"},
        }

    @pytest.fixture
    def crypto_candidate_with_string_technology(self):
        """Create crypto candidate with technology as string."""
        return {
            "symbol": "ETH-USD",
            "name": "Ethereum",
            "grade": "A",
            "market_cap_usd": 420000000000,  # $420B
            "volume_24h_usd": 15000000000,  # $15B
            "risk_assessment": {"score": 7.5},
            "technology": "Smart contract platform with proof of stake",
            "implementation": {"entry_strategy": "Buy on dips"},
        }

    def test_should_include_aplus_grade_crypto_with_high_market_cap(self, extractor, valid_crypto_candidate):
        """Test that A+ grade cryptos with high market cap are included."""
        # Act
        result = extractor._should_include(valid_crypto_candidate)

        # Assert
        assert result is True

    def test_should_include_a_grade_crypto_with_high_market_cap(self, extractor, valid_crypto_candidate):
        """Test that A grade cryptos with high market cap are included."""
        # Arrange
        valid_crypto_candidate["grade"] = "A"

        # Act
        result = extractor._should_include(valid_crypto_candidate)

        # Assert
        assert result is True

    def test_should_exclude_crypto_with_low_market_cap(self, extractor, valid_crypto_candidate):
        """Test that cryptos with low market cap are excluded."""
        # Arrange
        valid_crypto_candidate["market_cap_usd"] = 5000000000  # $5B (below $10B threshold)

        # Act
        result = extractor._should_include(valid_crypto_candidate)

        # Assert
        assert result is False

    def test_should_exclude_b_grade_crypto(self, extractor, valid_crypto_candidate):
        """Test that B grade cryptos are excluded."""
        # Arrange
        valid_crypto_candidate["grade"] = "B"

        # Act
        result = extractor._should_include(valid_crypto_candidate)

        # Assert
        assert result is False

    def test_should_exclude_crypto_without_symbol(self, extractor, valid_crypto_candidate):
        """Test that cryptos without symbol are excluded."""
        # Arrange
        valid_crypto_candidate["symbol"] = ""

        # Act
        result = extractor._should_include(valid_crypto_candidate)

        # Assert
        assert result is False

    def test_should_include_crypto_keyed_by_ticker_instead_of_symbol(self, extractor, valid_crypto_candidate):
        """NewcomerDiscoveryPipeline's writer emits "ticker", not "symbol" -- must still be included."""
        # Arrange
        del valid_crypto_candidate["symbol"]
        valid_crypto_candidate["ticker"] = "BTC-USD"

        # Act
        result = extractor._should_include(valid_crypto_candidate)

        # Assert
        assert result is True

    def test_should_include_crypto_with_no_market_cap_data_at_all(self, extractor, valid_crypto_candidate):
        """NewcomerDiscoveryPipeline's candidates never carry market_cap_usd/market_cap.

        Missing market-cap data must not be treated as a de-facto zero market
        cap -- there is no signal to gate on, so the candidate should pass
        through, not be silently dropped.
        """
        # Arrange
        del valid_crypto_candidate["market_cap_usd"]

        # Act
        result = extractor._should_include(valid_crypto_candidate)

        # Assert
        assert result is True

    def test_should_exclude_crypto_without_name(self, extractor, valid_crypto_candidate):
        """Test that cryptos without name are excluded."""
        # Arrange
        valid_crypto_candidate["name"] = ""

        # Act
        result = extractor._should_include(valid_crypto_candidate)

        # Assert
        assert result is False

    def test_should_build_opportunity_with_dict_technology(self, extractor, valid_crypto_candidate):
        """Test building opportunity with technology as dict."""
        # Act
        opportunity = extractor._build_opportunity(valid_crypto_candidate, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["symbol"] == "BTC"  # Should strip -USD
        assert opportunity["name"] == "Bitcoin"
        assert opportunity["grade"] == "A+"
        assert opportunity["composite_score"] > 0
        assert opportunity["confidence"] == approx(0.85)  # A+ confidence
        assert opportunity["risk_score"] == approx(7.0)
        assert "Consensus: Proof of Work" in opportunity["rationale"]
        assert "Use case: Store of value" in opportunity["rationale"]
        assert opportunity["allocation_recommendation"] == "Network effect"
        assert opportunity["replacement_note"] == "Dollar-cost averaging"
        assert "market_cap_usd" in opportunity["key_metrics"]
        assert opportunity["key_metrics"]["market_cap_usd"] == 1200000000000

    def test_should_build_opportunity_with_string_technology(self, extractor, crypto_candidate_with_string_technology):
        """Test building opportunity with technology as string."""
        # Act
        opportunity = extractor._build_opportunity(crypto_candidate_with_string_technology, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["symbol"] == "ETH"  # Should strip -USD
        assert opportunity["name"] == "Ethereum"
        assert opportunity["grade"] == "A"
        assert opportunity["confidence"] == approx(0.75)  # A confidence
        assert "Smart contract platform with proof of stake" in opportunity["rationale"]
        assert opportunity["allocation_recommendation"] == ""

    def test_should_strip_usd_suffix_from_symbol(self, extractor, valid_crypto_candidate):
        """Test that -USD suffix is stripped from symbol."""
        # Act
        opportunity = extractor._build_opportunity(valid_crypto_candidate, 0)

        # Assert
        assert opportunity["symbol"] == "BTC"
        assert "-USD" not in opportunity["symbol"]

    def test_should_calculate_composite_score_correctly(self, extractor, valid_crypto_candidate):
        """Test composite score calculation from market metrics."""
        # Act
        opportunity = extractor._build_opportunity(valid_crypto_candidate, 0)

        # Assert
        # Score = (market_cap_score * 0.6 + volume_score * 0.4) * 0.9
        # market_cap_score = min(1200e9 / 100e9, 1.0) = 1.0
        # volume_score = min(30e9 / 10e9, 1.0) = 1.0
        # Score = (1.0 * 0.6 + 1.0 * 0.4) * 0.9 = 1.0 * 0.9 = 0.9
        market_cap_score = min(1200000000000 / 100e9, 1.0)
        volume_score = min(30000000000 / 10e9, 1.0)
        expected_score = (market_cap_score * 0.6 + volume_score * 0.4) * 0.9
        assert abs(opportunity["composite_score"] - expected_score) < 0.01

    def test_should_cap_composite_score_at_ninety_percent(self, extractor, valid_crypto_candidate):
        """Test that composite score is capped at 0.9 for crypto."""
        # Arrange - Set very high market cap and volume
        valid_crypto_candidate["market_cap_usd"] = 10000000000000  # $10T
        valid_crypto_candidate["volume_24h_usd"] = 1000000000000  # $1T

        # Act
        opportunity = extractor._build_opportunity(valid_crypto_candidate, 0)

        # Assert
        assert opportunity["composite_score"] <= 0.9

    def test_should_extract_multiple_cryptos(self, extractor, valid_crypto_candidate, crypto_candidate_with_string_technology):
        """Test extracting multiple crypto opportunities."""
        # Arrange
        candidates = [valid_crypto_candidate, crypto_candidate_with_string_technology]

        # Act
        opportunities = extractor.extract(candidates)

        # Assert
        assert len(opportunities) == 2
        assert opportunities[0]["symbol"] == "BTC"
        assert opportunities[1]["symbol"] == "ETH"

    def test_should_mark_missing_market_metric_unavailable_when_partial_data_present(self, extractor, valid_crypto_candidate):
        """An entirely absent market metric must not be defaulted to 0 -- a 0
        reads as a real (and gate-failing) measurement, not as "unknown".

        Only volume_24h_usd is deleted here (market_cap_usd stays) so
        composite_score can still be derived from real data and the opportunity
        is still built -- isolating the key_metrics marker behavior from the
        "refuse entirely" case covered separately below.
        """
        # Arrange
        del valid_crypto_candidate["volume_24h_usd"]

        # Act
        opportunity = extractor._build_opportunity(valid_crypto_candidate, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["key_metrics"]["market_cap_usd"] == valid_crypto_candidate["market_cap_usd"]
        assert opportunity["key_metrics"]["volume_24h_usd"] == {
            "unavailable": True,
            "field": "volume_24h_usd",
            "reason": extractor._NO_DATA_REASON,
        }

    def test_should_refuse_when_no_composite_score_and_no_market_data_at_all(self, extractor, valid_crypto_candidate):
        """No composite_score and no market data at all: refuse rather than
        fabricate a composite_score from nothing.

        valid_crypto_candidate never carries composite_score directly, so
        deleting both market_cap_usd and volume_24h_usd removes every input the
        fallback derivation needs. This used to return an opportunity with
        composite_score computed from zeros -- a plausible-looking, fully
        fabricated 0.0 -- with every affected key_metrics value marked
        unavailable around it. Now the extractor refuses to build the
        opportunity at all: there is nothing here to score, so it says so.
        """
        # Arrange
        del valid_crypto_candidate["market_cap_usd"]
        del valid_crypto_candidate["volume_24h_usd"]

        # Act
        opportunity = extractor._build_opportunity(valid_crypto_candidate, 0)

        # Assert
        assert opportunity is None

    def test_should_handle_missing_risk_assessment_gracefully(self, extractor, valid_crypto_candidate):
        """Test handling of missing risk assessment."""
        # Arrange
        del valid_crypto_candidate["risk_assessment"]

        # Act
        opportunity = extractor._build_opportunity(valid_crypto_candidate, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["risk_score"] == approx(6.0)  # Default for crypto

    def test_should_return_empty_list_for_empty_candidates(self, extractor):
        """Test extraction with empty candidates list."""
        # Act
        opportunities = extractor.extract([])

        # Assert
        assert opportunities == []

    def test_should_filter_out_low_grade_cryptos(self, extractor, valid_crypto_candidate):
        """Test that low-grade cryptos are filtered out."""
        # Arrange
        valid_crypto_candidate["grade"] = "C"

        # Act
        opportunities = extractor.extract([valid_crypto_candidate])

        # Assert
        assert len(opportunities) == 0

    def test_should_filter_out_low_market_cap_cryptos(self, extractor, valid_crypto_candidate):
        """Test that low market cap cryptos are filtered out even with A+ grade."""
        # Arrange
        valid_crypto_candidate["market_cap_usd"] = 1000000000  # $1B (below $10B threshold)

        # Act
        opportunities = extractor.extract([valid_crypto_candidate])

        # Assert
        assert len(opportunities) == 0

    def test_should_refuse_when_composite_score_cannot_be_derived(self, extractor):
        """A candidate with no composite_score and no market data must be
        refused, not built with a fabricated composite_score computed from
        zeros.

        This used to return an opportunity with default values throughout,
        including a composite_score silently computed from absent market data
        (0.0 -- indistinguishable from a genuine "this asset scored zero").
        Refusing is the honest outcome: there's nothing here to score.
        """
        # Arrange
        invalid_candidate = {"symbol": "TEST"}  # No composite_score, no market data

        # Act
        opportunity = extractor._build_opportunity(invalid_candidate, 0)

        # Assert
        assert opportunity is None

    def test_should_handle_missing_optional_fields_gracefully(self, extractor):
        """Test handling of extraction errors for fields other than composite_score's inputs.

        As long as composite_score itself is derivable (supplied directly here),
        every other missing field still defaults gracefully -- Python doesn't
        raise on missing dict keys accessed via .get().
        """
        # Arrange
        minimal_candidate = {"symbol": "TEST", "composite_score": 0.5}  # Missing everything else

        # Act
        opportunity = extractor._build_opportunity(minimal_candidate, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["symbol"] == "TEST"
        assert opportunity["composite_score"] == approx(0.5)
