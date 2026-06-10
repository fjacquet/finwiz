"""Unit tests for v4 feature flags (finnhub_news, fred_macro, fear_greed_index, etc.)."""

import pytest

from finwiz.config.features.definitions import (
    FallbackStrategy,
    FeatureFlagStrategy,
    create_default_flags,
)
from finwiz.config.features.evaluators import get_default_values

# Env vars that override v4 flag defaults
_V4_ENV_VARS = [
    "FF_FINNHUB_NEWS",
    "FF_FRED_MACRO",
    "FF_FEAR_GREED",
    "FF_SENTIMENT_SCORING",
    "FF_MACRO_SCORING",
    "FF_FINNHUB_BREAKER_THRESHOLD",
    "FF_FINNHUB_BREAKER_TIMEOUT",
    "FF_FRED_BREAKER_THRESHOLD",
    "FF_FRED_BREAKER_TIMEOUT",
    "FF_FEAR_GREED_BREAKER_THRESHOLD",
    "FF_FEAR_GREED_BREAKER_TIMEOUT",
]

# Env vars that override the perplexity_research flag defaults
_PERPLEXITY_ENV_VARS = [
    "FF_PERPLEXITY_RESEARCH",
    "FF_PERPLEXITY_BREAKER_THRESHOLD",
    "FF_PERPLEXITY_BREAKER_TIMEOUT",
]


@pytest.fixture()
def _clean_v4_env(monkeypatch):
    """Remove v4 feature flag env vars so tests see true defaults."""
    for var in _V4_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture()
def _clean_perplexity_env(monkeypatch):
    """Remove perplexity feature flag env vars so tests see true defaults."""
    for var in _PERPLEXITY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


class TestV4FeatureFlags:
    """Verify v4 feature flag definitions."""

    def setup_method(self):
        self.flags = create_default_flags()

    def test_finnhub_news_exists(self):
        assert "finnhub_news" in self.flags

    @pytest.mark.usefixtures("_clean_v4_env")
    def test_finnhub_news_defaults_off(self):
        flags = create_default_flags()
        assert flags["finnhub_news"].enabled is False

    def test_finnhub_news_circuit_breaker(self):
        assert self.flags["finnhub_news"].strategy == FeatureFlagStrategy.CIRCUIT_BREAKER
        assert self.flags["finnhub_news"].fallback_strategy == FallbackStrategy.DEFAULT_VALUES

    def test_fred_macro_exists(self):
        assert "fred_macro" in self.flags

    @pytest.mark.usefixtures("_clean_v4_env")
    def test_fred_macro_defaults_off(self):
        flags = create_default_flags()
        assert flags["fred_macro"].enabled is False

    def test_fred_macro_circuit_breaker(self):
        assert self.flags["fred_macro"].strategy == FeatureFlagStrategy.CIRCUIT_BREAKER

    def test_fear_greed_index_exists(self):
        assert "fear_greed_index" in self.flags

    @pytest.mark.usefixtures("_clean_v4_env")
    def test_fear_greed_index_defaults_off(self):
        flags = create_default_flags()
        assert flags["fear_greed_index"].enabled is False

    def test_fear_greed_index_circuit_breaker(self):
        assert self.flags["fear_greed_index"].strategy == FeatureFlagStrategy.CIRCUIT_BREAKER
        assert self.flags["fear_greed_index"].circuit_breaker_threshold == 3

    def test_sentiment_scoring_exists(self):
        assert "sentiment_scoring" in self.flags

    @pytest.mark.usefixtures("_clean_v4_env")
    def test_sentiment_scoring_defaults_off(self):
        flags = create_default_flags()
        assert flags["sentiment_scoring"].enabled is False

    def test_sentiment_scoring_boolean_strategy(self):
        assert self.flags["sentiment_scoring"].strategy == FeatureFlagStrategy.BOOLEAN

    def test_macro_scoring_exists(self):
        assert "macro_scoring" in self.flags

    @pytest.mark.usefixtures("_clean_v4_env")
    def test_macro_scoring_defaults_off(self):
        flags = create_default_flags()
        assert flags["macro_scoring"].enabled is False

    def test_macro_scoring_boolean_strategy(self):
        assert self.flags["macro_scoring"].strategy == FeatureFlagStrategy.BOOLEAN


class TestPerplexityResearchFlag:
    """Pin the circuit-breaker configuration of the perplexity_research flag."""

    def test_perplexity_research_exists(self):
        flags = create_default_flags()
        assert "perplexity_research" in flags

    @pytest.mark.usefixtures("_clean_perplexity_env")
    def test_perplexity_research_circuit_breaker_strategy(self):
        flags = create_default_flags()
        config = flags["perplexity_research"]
        assert config.strategy == FeatureFlagStrategy.CIRCUIT_BREAKER
        assert config.circuit_breaker_threshold == 5
        assert config.circuit_breaker_timeout == 300
        assert config.fallback_strategy == FallbackStrategy.DISABLE


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
