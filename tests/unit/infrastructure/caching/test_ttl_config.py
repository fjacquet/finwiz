"""Tests for CacheTTLRegistry and CacheDataType."""

from finwiz.infrastructure.caching.ttl_config import CacheDataType, CacheTTLRegistry


class TestCacheTTLRegistry:
    def test_default_ttls(self):
        registry = CacheTTLRegistry()
        assert registry.get_ttl(CacheDataType.MARKET_DATA) == 900
        assert registry.get_ttl(CacheDataType.FUNDAMENTALS) == 86400
        assert registry.get_ttl(CacheDataType.STATIC_REFERENCE) == 604800
        assert registry.get_ttl(CacheDataType.CREW_OUTPUT) == 86400
        assert registry.get_ttl(CacheDataType.ANALYSIS_RESULT) == 1800
        assert registry.get_ttl(CacheDataType.VALIDATION) == 86400

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("CACHE_TTL_MARKET_DATA", "600")
        registry = CacheTTLRegistry()
        assert registry.get_ttl(CacheDataType.MARKET_DATA) == 600
        # Others unchanged
        assert registry.get_ttl(CacheDataType.FUNDAMENTALS) == 86400

    def test_env_override_invalid_ignored(self, monkeypatch):
        monkeypatch.setenv("CACHE_TTL_MARKET_DATA", "not_a_number")
        registry = CacheTTLRegistry()
        assert registry.get_ttl(CacheDataType.MARKET_DATA) == 900

    def test_env_override_negative_ignored(self, monkeypatch):
        monkeypatch.setenv("CACHE_TTL_MARKET_DATA", "-100")
        registry = CacheTTLRegistry()
        assert registry.get_ttl(CacheDataType.MARKET_DATA) == 900

    def test_classify_key_market_data(self):
        registry = CacheTTLRegistry()
        assert registry.classify_key("price_AAPL") == CacheDataType.MARKET_DATA
        assert registry.classify_key("quote_data") == CacheDataType.MARKET_DATA

    def test_classify_key_fundamentals(self):
        registry = CacheTTLRegistry()
        assert registry.classify_key("fundamental_MSFT") == CacheDataType.FUNDAMENTALS
        assert registry.classify_key("earnings_data") == CacheDataType.FUNDAMENTALS

    def test_classify_key_crew(self):
        registry = CacheTTLRegistry()
        assert registry.classify_key("crew_deep_analysis") == CacheDataType.CREW_OUTPUT

    def test_classify_key_default(self):
        registry = CacheTTLRegistry()
        assert registry.classify_key("unknown_key_xyz") == CacheDataType.ANALYSIS_RESULT

    def test_get_ttl_for_key(self):
        registry = CacheTTLRegistry()
        assert registry.get_ttl_for_key("price_AAPL") == 900
        assert registry.get_ttl_for_key("fundamental_MSFT") == 86400

    def test_get_all_ttls(self):
        registry = CacheTTLRegistry()
        all_ttls = registry.get_all_ttls()
        assert isinstance(all_ttls, dict)
        assert len(all_ttls) == len(CacheDataType)
        assert all_ttls["market_data"] == 900
