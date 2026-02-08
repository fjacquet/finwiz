"""Unit tests for IndustryAveragesAdapter."""

import pytest

from finwiz.data.adapters.industry_averages import IndustryAveragesAdapter


class TestIndustryAveragesAdapter:
    """Test IndustryAveragesAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        return IndustryAveragesAdapter()

    def test_should_always_be_available(self, adapter):
        """Test that industry averages are always available."""
        assert adapter.is_available() is True

    @pytest.mark.asyncio
    async def test_should_return_technology_sector_averages(self, adapter):
        """Test getting Technology sector averages."""
        data = await adapter.get_fundamental_data("AAPL", sector="Technology")

        assert data.ticker == "AAPL"
        assert data.source == "IndustryAverages"
        assert data.confidence == 0.5  # Low confidence for averages
        assert data.return_on_equity is not None
        assert data.debt_to_equity is not None
        assert data.revenue_growth is not None
        assert data.profit_margin is not None
        assert "Using industry average data as fallback" in data.warnings

    @pytest.mark.asyncio
    async def test_should_return_financial_sector_averages(self, adapter):
        """Test getting Financial sector averages."""
        data = await adapter.get_fundamental_data("JPM", sector="Financial")

        assert data.ticker == "JPM"
        assert data.source == "IndustryAverages"
        assert data.confidence == 0.5
        # Financial sector typically has higher debt/equity
        assert data.debt_to_equity > 1.0

    @pytest.mark.asyncio
    async def test_should_use_default_for_unknown_sector(self, adapter):
        """Test that unknown sectors use default averages."""
        data = await adapter.get_fundamental_data("XYZ", sector="UnknownSector")

        assert data.ticker == "XYZ"
        assert data.source == "IndustryAverages"
        assert "Sector: Default" in data.warnings

    @pytest.mark.asyncio
    async def test_should_use_default_when_no_sector_provided(self, adapter):
        """Test that None sector uses default averages."""
        data = await adapter.get_fundamental_data("XYZ", sector=None)

        assert data.ticker == "XYZ"
        assert data.source == "IndustryAverages"
        assert "Sector: Default" in data.warnings

    def test_should_get_available_sectors(self, adapter):
        """Test getting list of available sectors."""
        sectors = adapter.get_available_sectors()

        assert "Technology" in sectors
        assert "Financial" in sectors
        assert "Healthcare" in sectors
        assert "Default" not in sectors  # Default should be excluded

    def test_should_get_sector_averages(self, adapter):
        """Test getting averages for specific sector."""
        tech_averages = adapter.get_sector_averages("Technology")

        assert tech_averages is not None
        assert "return_on_equity" in tech_averages
        assert "debt_to_equity" in tech_averages
        assert "revenue_growth" in tech_averages
        assert "profit_margin" in tech_averages

    def test_should_return_none_for_invalid_sector(self, adapter):
        """Test that invalid sector returns None."""
        averages = adapter.get_sector_averages("InvalidSector")
        assert averages is None

    @pytest.mark.asyncio
    async def test_should_include_warnings(self, adapter):
        """Test that warnings are included in result."""
        data = await adapter.get_fundamental_data("AAPL", sector="Technology")

        assert len(data.warnings) > 0
        assert any("fallback" in w.lower() for w in data.warnings)
        assert any("low confidence" in w.lower() for w in data.warnings)

    @pytest.mark.asyncio
    async def test_should_pass_validation(self, adapter):
        """Test that industry averages pass validation rules."""
        data = await adapter.get_fundamental_data("AAPL", sector="Technology")

        # All industry averages should be within valid ranges
        assert data.is_valid()
