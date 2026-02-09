"""Unit tests for v4 feature flags (finnhub_news, fred_macro, fear_greed_index, etc.)."""

from finwiz.config.features.definitions import (
    FallbackStrategy,
    FeatureFlagStrategy,
    create_default_flags,
)
from finwiz.config.features.evaluators import get_default_values


class TestV4FeatureFlags:
    """Verify v4 feature flag definitions."""

    def setup_method(self):
        self.flags = create_default_flags()

    def test_finnhub_news_exists(self):
        assert "finnhub_news" in self.flags

    def test_finnhub_news_defaults_off(self):
        assert self.flags["finnhub_news"].enabled is False

    def test_finnhub_news_circuit_breaker(self):
        assert self.flags["finnhub_news"].strategy == FeatureFlagStrategy.CIRCUIT_BREAKER
        assert self.flags["finnhub_news"].fallback_strategy == FallbackStrategy.DEFAULT_VALUES

    def test_fred_macro_exists(self):
        assert "fred_macro" in self.flags

    def test_fred_macro_defaults_off(self):
        assert self.flags["fred_macro"].enabled is False

    def test_fred_macro_circuit_breaker(self):
        assert self.flags["fred_macro"].strategy == FeatureFlagStrategy.CIRCUIT_BREAKER

    def test_fear_greed_index_exists(self):
        assert "fear_greed_index" in self.flags

    def test_fear_greed_index_defaults_off(self):
        assert self.flags["fear_greed_index"].enabled is False

    def test_fear_greed_index_circuit_breaker(self):
        assert self.flags["fear_greed_index"].strategy == FeatureFlagStrategy.CIRCUIT_BREAKER
        assert self.flags["fear_greed_index"].circuit_breaker_threshold == 3

    def test_sentiment_scoring_exists(self):
        assert "sentiment_scoring" in self.flags

    def test_sentiment_scoring_defaults_off(self):
        assert self.flags["sentiment_scoring"].enabled is False

    def test_sentiment_scoring_boolean_strategy(self):
        assert self.flags["sentiment_scoring"].strategy == FeatureFlagStrategy.BOOLEAN

    def test_macro_scoring_exists(self):
        assert "macro_scoring" in self.flags

    def test_macro_scoring_defaults_off(self):
        assert self.flags["macro_scoring"].enabled is False

    def test_macro_scoring_boolean_strategy(self):
        assert self.flags["macro_scoring"].strategy == FeatureFlagStrategy.BOOLEAN


class TestV4DefaultValues:
    """Verify default values returned when flags are disabled."""

    def test_finnhub_news_defaults(self):
        defaults = get_default_values("finnhub_news")
        assert defaults["articles"] == []
        assert defaults["aggregate_sentiment"] == 0.0
        assert defaults["source"] == "default"

    def test_fred_macro_defaults(self):
        defaults = get_default_values("fred_macro")
        assert defaults["fed_rate"] is None
        assert defaults["vix"] is None
        assert defaults["source"] == "default"

    def test_fear_greed_defaults(self):
        defaults = get_default_values("fear_greed_index")
        assert defaults["value"] is None
        assert defaults["label"] is None

    def test_sentiment_scoring_defaults(self):
        defaults = get_default_values("sentiment_scoring")
        assert defaults["weight"] == 0.0

    def test_macro_scoring_defaults(self):
        defaults = get_default_values("macro_scoring")
        assert defaults["weight"] == 0.0
