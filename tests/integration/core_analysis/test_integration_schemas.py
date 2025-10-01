"""
Unit tests for integration schemas with comprehensive mocking.

Tests all integration schema models with mocked data to ensure proper validation
and behavior without external dependencies.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from finwiz.schemas.integration import (
    APlusOpportunityCollection,
    CrewOutputMetadata,
    CryptoCrewOutput,
    DataAvailabilityReport,
    DataQuality,
    DataSource,
    DataSourceType,
    DiscoveryCrewOutput,
    ETFCrewOutput,
    FreshnessStatus,
    IntegrationError,
    SECCitation,
    StockCrewOutput,
    ValidatedCrypto,
    ValidatedETF,
    ValidatedTicker,
    ValidationStatus,
)


class TestValidationStatus:
    """Test ValidationStatus model."""

    def test_should_create_valid_validation_status_when_all_fields_provided(self):
        """Test creating a valid ValidationStatus with all fields."""
        # Arrange
        timestamp = datetime.now(UTC)
        data = {
            "is_valid": True,
            "validation_timestamp": timestamp,
            "validation_errors": ["Error 1", "Error 2"],
            "validation_warnings": ["Warning 1"],
            "schema_version": 2,
        }

        # Act
        status = ValidationStatus(**data)

        # Assert
        assert status.is_valid is True
        assert status.validation_timestamp == timestamp
        assert status.validation_errors == ["Error 1", "Error 2"]
        assert status.validation_warnings == ["Warning 1"]
        assert status.schema_version == 2

    def test_should_create_validation_status_with_defaults_when_optional_fields_omitted(self):
        """Test creating ValidationStatus with default values."""
        # Arrange
        timestamp = datetime.now(UTC)
        data = {"is_valid": False, "validation_timestamp": timestamp}

        # Act
        status = ValidationStatus(**data)

        # Assert
        assert status.is_valid is False
        assert status.validation_timestamp == timestamp
        assert status.validation_errors == []
        assert status.validation_warnings == []
        assert status.schema_version == 1

    def test_should_raise_validation_error_when_required_fields_missing(self):
        """Test ValidationError when required fields are missing."""
        # Arrange
        data = {"is_valid": True}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ValidationStatus(**data)

        assert "validation_timestamp" in str(exc_info.value)

    def test_should_strip_whitespace_from_string_fields(self):
        """Test that string fields are stripped of whitespace."""
        # Arrange
        timestamp = datetime.now(UTC)
        data = {
            "is_valid": True,
            "validation_timestamp": timestamp,
            "validation_errors": ["  Error with spaces  "],
            "validation_warnings": ["  Warning with spaces  "],
        }

        # Act
        status = ValidationStatus(**data)

        # Assert
        assert status.validation_errors == ["Error with spaces"]
        assert status.validation_warnings == ["Warning with spaces"]


class TestFreshnessStatus:
    """Test FreshnessStatus model."""

    def test_should_create_valid_freshness_status_when_all_fields_provided(self):
        """Test creating a valid FreshnessStatus with all fields."""
        # Arrange
        last_updated = datetime.now(UTC)
        data = {"is_fresh": True, "age_hours": 2.5, "max_age_hours": 24, "refresh_recommended": False, "last_updated": last_updated}

        # Act
        status = FreshnessStatus(**data)

        # Assert
        assert status.is_fresh is True
        assert status.age_hours == 2.5
        assert status.max_age_hours == 24
        assert status.refresh_recommended is False
        assert status.last_updated == last_updated

    def test_should_use_default_max_age_when_not_provided(self):
        """Test default max_age_hours value."""
        # Arrange
        last_updated = datetime.now(UTC)
        data = {"is_fresh": False, "age_hours": 48.0, "refresh_recommended": True, "last_updated": last_updated}

        # Act
        status = FreshnessStatus(**data)

        # Assert
        assert status.max_age_hours == 24

    def test_should_raise_validation_error_when_age_hours_negative(self):
        """Test validation error for negative age_hours."""
        # Arrange
        data = {"is_fresh": False, "age_hours": -1.0, "refresh_recommended": True, "last_updated": datetime.now(UTC)}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            FreshnessStatus(**data)

        assert "age_hours" in str(exc_info.value)

    def test_should_raise_validation_error_when_max_age_hours_invalid(self):
        """Test validation error for invalid max_age_hours."""
        # Arrange
        data = {
            "is_fresh": True,
            "age_hours": 1.0,
            "max_age_hours": 0,  # Should be >= 1
            "refresh_recommended": False,
            "last_updated": datetime.now(UTC),
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            FreshnessStatus(**data)

        assert "max_age_hours" in str(exc_info.value)


class TestDataSource:
    """Test DataSource model."""

    def test_should_create_valid_data_source_when_all_fields_provided(self):
        """Test creating a valid DataSource with all fields."""
        # Arrange
        accessed_at = datetime.now(UTC)
        data = {
            "source_type": DataSourceType.YAHOO_FINANCE,
            "source_url": "https://finance.yahoo.com/quote/AAPL",
            "accessed_at": accessed_at,
            "data_quality": DataQuality.HIGH,
            "response_time_ms": 250.5,
        }

        # Act
        source = DataSource(**data)

        # Assert
        assert source.source_type == DataSourceType.YAHOO_FINANCE
        assert str(source.source_url) == "https://finance.yahoo.com/quote/AAPL"
        assert source.accessed_at == accessed_at
        assert source.data_quality == DataQuality.HIGH
        assert source.response_time_ms == 250.5

    def test_should_create_data_source_with_optional_fields_none(self):
        """Test creating DataSource with optional fields as None."""
        # Arrange
        accessed_at = datetime.now(UTC)
        data = {"source_type": DataSourceType.SEC_EDGAR, "accessed_at": accessed_at, "data_quality": DataQuality.MEDIUM}

        # Act
        source = DataSource(**data)

        # Assert
        assert source.source_type == DataSourceType.SEC_EDGAR
        assert source.source_url is None
        assert source.accessed_at == accessed_at
        assert source.data_quality == DataQuality.MEDIUM
        assert source.response_time_ms is None

    def test_should_raise_validation_error_when_response_time_negative(self):
        """Test validation error for negative response_time_ms."""
        # Arrange
        data = {
            "source_type": DataSourceType.ALPHA_VANTAGE,
            "accessed_at": datetime.now(UTC),
            "data_quality": DataQuality.LOW,
            "response_time_ms": -100.0,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DataSource(**data)

        assert "response_time_ms" in str(exc_info.value)

    def test_should_validate_all_data_source_types(self):
        """Test that all DataSourceType enum values are valid."""
        # Arrange
        accessed_at = datetime.now(UTC)
        source_types = [
            DataSourceType.SEC_EDGAR,
            DataSourceType.YAHOO_FINANCE,
            DataSourceType.ALPHA_VANTAGE,
            DataSourceType.COINMARKETCAP,
            DataSourceType.KRAKEN,
            DataSourceType.INTERNAL,
            DataSourceType.CACHED,
        ]

        # Act & Assert
        for source_type in source_types:
            data = {"source_type": source_type, "accessed_at": accessed_at, "data_quality": DataQuality.HIGH}
            source = DataSource(**data)
            assert source.source_type == source_type


class TestCrewOutputMetadata:
    """Test CrewOutputMetadata model."""

    def create_valid_validation_status(self) -> ValidationStatus:
        """Create a valid ValidationStatus."""
        return ValidationStatus(is_valid=True, validation_timestamp=datetime.now(UTC))

    def create_valid_freshness_status(self) -> FreshnessStatus:
        """Create a valid FreshnessStatus."""
        return FreshnessStatus(is_fresh=True, age_hours=1.0, refresh_recommended=False, last_updated=datetime.now(UTC))

    def create_valid_data_source(self) -> DataSource:
        """Create a valid DataSource."""
        return DataSource(source_type=DataSourceType.YAHOO_FINANCE, accessed_at=datetime.now(UTC), data_quality=DataQuality.HIGH)

    def test_should_create_valid_metadata_when_all_fields_provided(self):
        """Test creating valid CrewOutputMetadata with all fields."""
        # Arrange
        execution_timestamp = datetime.now(UTC)
        validation_status = self.create_valid_validation_status()
        freshness_status = self.create_valid_freshness_status()
        data_sources = [self.create_valid_data_source()]

        data = {
            "crew_name": "stock_crew",
            "execution_timestamp": execution_timestamp,
            "schema_version": 2,
            "validation_status": validation_status,
            "data_sources": data_sources,
            "dependencies_met": True,
            "freshness_status": freshness_status,
            "execution_duration_seconds": 45.2,
            "input_hash": "abc123def456",
        }

        # Act
        metadata = CrewOutputMetadata(**data)

        # Assert
        assert metadata.crew_name == "stock_crew"
        assert metadata.execution_timestamp == execution_timestamp
        assert metadata.schema_version == 2
        assert metadata.validation_status == validation_status
        assert metadata.data_sources == data_sources
        assert metadata.dependencies_met is True
        assert metadata.freshness_status == freshness_status
        assert metadata.execution_duration_seconds == 45.2
        assert metadata.input_hash == "abc123def456"

    def test_should_create_metadata_with_defaults_when_optional_fields_omitted(self):
        """Test creating CrewOutputMetadata with default values."""
        # Arrange
        execution_timestamp = datetime.now(UTC)
        validation_status = self.create_valid_validation_status()
        freshness_status = self.create_valid_freshness_status()

        data = {
            "crew_name": "etf_crew",
            "execution_timestamp": execution_timestamp,
            "validation_status": validation_status,
            "dependencies_met": False,
            "freshness_status": freshness_status,
        }

        # Act
        metadata = CrewOutputMetadata(**data)

        # Assert
        assert metadata.crew_name == "etf_crew"
        assert metadata.schema_version == 1  # Default value
        assert metadata.data_sources == []  # Default empty list
        assert metadata.execution_duration_seconds is None
        assert metadata.input_hash is None

    def test_should_raise_validation_error_when_crew_name_empty(self):
        """Test validation error for empty crew_name."""
        # Arrange
        data = {
            "crew_name": "",
            "execution_timestamp": datetime.now(UTC),
            "validation_status": self.create_valid_validation_status(),
            "dependencies_met": True,
            "freshness_status": self.create_valid_freshness_status(),
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CrewOutputMetadata(**data)

        assert "crew_name" in str(exc_info.value)

    def test_should_raise_validation_error_when_schema_version_invalid(self):
        """Test validation error for invalid schema_version."""
        # Arrange
        data = {
            "crew_name": "crypto_crew",
            "execution_timestamp": datetime.now(UTC),
            "schema_version": 0,  # Should be >= 1
            "validation_status": self.create_valid_validation_status(),
            "dependencies_met": True,
            "freshness_status": self.create_valid_freshness_status(),
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CrewOutputMetadata(**data)

        assert "schema_version" in str(exc_info.value)

    def test_should_raise_validation_error_when_execution_duration_negative(self):
        """Test validation error for negative execution_duration_seconds."""
        # Arrange
        data = {
            "crew_name": "discovery_crew",
            "execution_timestamp": datetime.now(UTC),
            "validation_status": self.create_valid_validation_status(),
            "dependencies_met": True,
            "freshness_status": self.create_valid_freshness_status(),
            "execution_duration_seconds": -10.0,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CrewOutputMetadata(**data)

        assert "execution_duration_seconds" in str(exc_info.value)

    def test_should_strip_whitespace_from_crew_name(self):
        """Test that crew_name is stripped of whitespace."""
        # Arrange
        data = {
            "crew_name": "  report_crew  ",
            "execution_timestamp": datetime.now(UTC),
            "validation_status": self.create_valid_validation_status(),
            "dependencies_met": True,
            "freshness_status": self.create_valid_freshness_status(),
        }

        # Act
        metadata = CrewOutputMetadata(**data)

        # Assert
        assert metadata.crew_name == "report_crew"

    def test_should_handle_multiple_data_sources(self):
        """Test handling multiple data sources in metadata."""
        # Arrange
        data_sources = [
            DataSource(source_type=DataSourceType.YAHOO_FINANCE, accessed_at=datetime.now(UTC), data_quality=DataQuality.HIGH),
            DataSource(source_type=DataSourceType.SEC_EDGAR, accessed_at=datetime.now(UTC), data_quality=DataQuality.MEDIUM),
        ]

        data = {
            "crew_name": "stock_crew",
            "execution_timestamp": datetime.now(UTC),
            "validation_status": self.create_valid_validation_status(),
            "data_sources": data_sources,
            "dependencies_met": True,
            "freshness_status": self.create_valid_freshness_status(),
        }

        # Act
        metadata = CrewOutputMetadata(**data)

        # Assert
        assert len(metadata.data_sources) == 2
        assert metadata.data_sources[0].source_type == DataSourceType.YAHOO_FINANCE
        assert metadata.data_sources[1].source_type == DataSourceType.SEC_EDGAR

    def test_should_forbid_extra_fields(self):
        """Test that extra fields are forbidden."""
        # Arrange
        data = {
            "crew_name": "test_crew",
            "execution_timestamp": datetime.now(UTC),
            "validation_status": self.create_valid_validation_status(),
            "dependencies_met": True,
            "freshness_status": self.create_valid_freshness_status(),
            "extra_field": "should_not_be_allowed",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CrewOutputMetadata(**data)

        assert "extra_field" in str(exc_info.value)


class TestSECCitation:
    """Test SECCitation model."""

    def create_valid_validation_status(self) -> ValidationStatus:
        """Create a valid ValidationStatus."""
        return ValidationStatus(is_valid=True, validation_timestamp=datetime.now(UTC))

    def test_should_create_valid_sec_citation_when_all_fields_provided(self):
        """Test creating a valid SECCitation with all fields."""
        # Arrange
        filed_at = datetime.now(UTC)
        extraction_timestamp = datetime.now(UTC)
        validation_status = self.create_valid_validation_status()

        data = {
            "ticker": "AAPL",
            "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000007/aapl-20240930.htm",
            "filed_at": filed_at,
            "section": "Item 1A - Risk Factors",
            "excerpt": "The Company faces intense competition in all areas of its business.",
            "sec_citation": "10-K (2024), Item 1A, p. 17",
            "extraction_timestamp": extraction_timestamp,
            "validation_status": validation_status,
        }

        # Act
        citation = SECCitation(**data)

        # Assert
        assert citation.ticker == "AAPL"
        assert str(citation.filing_url) == "https://www.sec.gov/Archives/edgar/data/320193/000032019324000007/aapl-20240930.htm"
        assert citation.filed_at == filed_at
        assert citation.section == "Item 1A - Risk Factors"
        assert citation.excerpt == "The Company faces intense competition in all areas of its business."
        assert citation.sec_citation == "10-K (2024), Item 1A, p. 17"
        assert citation.extraction_timestamp == extraction_timestamp
        assert citation.validation_status == validation_status

    def test_should_raise_validation_error_when_ticker_too_long(self):
        """Test validation error for ticker that's too long."""
        # Arrange
        data = {
            "ticker": "TOOLONGTICKERHERE",  # > 10 characters
            "filing_url": "https://www.sec.gov/test",
            "filed_at": datetime.now(UTC),
            "section": "Item 1A",
            "excerpt": "Test excerpt that is long enough",
            "sec_citation": "10-K (2024), Item 1A, p. 17",
            "extraction_timestamp": datetime.now(UTC),
            "validation_status": self.create_valid_validation_status(),
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SECCitation(**data)

        assert "ticker" in str(exc_info.value)

    def test_should_raise_validation_error_when_excerpt_too_short(self):
        """Test validation error for excerpt that's too short."""
        # Arrange
        data = {
            "ticker": "AAPL",
            "filing_url": "https://www.sec.gov/test",
            "filed_at": datetime.now(UTC),
            "section": "Item 1A",
            "excerpt": "Too short",  # < 20 characters
            "sec_citation": "10-K (2024), Item 1A, p. 17",
            "extraction_timestamp": datetime.now(UTC),
            "validation_status": self.create_valid_validation_status(),
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SECCitation(**data)

        assert "excerpt" in str(exc_info.value)


class TestValidatedTicker:
    """Test ValidatedTicker model."""

    def test_should_create_valid_ticker_when_all_fields_provided(self):
        """Test creating a valid ValidatedTicker with all fields."""
        # Arrange
        validation_timestamp = datetime.now(UTC)
        data = {
            "symbol": "AAPL",
            "is_valid": True,
            "validation_source": "Yahoo Finance",
            "validation_timestamp": validation_timestamp,
            "market": "NASDAQ",
            "sector": "Technology",
            "company_name": "Apple Inc.",
            "validation_errors": [],
            "alternative_suggestions": ["APPL", "APLE"],
        }

        # Act
        ticker = ValidatedTicker(**data)

        # Assert
        assert ticker.symbol == "AAPL"
        assert ticker.is_valid is True
        assert ticker.validation_source == "Yahoo Finance"
        assert ticker.validation_timestamp == validation_timestamp
        assert ticker.market == "NASDAQ"
        assert ticker.sector == "Technology"
        assert ticker.company_name == "Apple Inc."
        assert ticker.validation_errors == []
        assert ticker.alternative_suggestions == ["APPL", "APLE"]

    def test_should_create_ticker_with_defaults_when_optional_fields_omitted(self):
        """Test creating ValidatedTicker with default values."""
        # Arrange
        validation_timestamp = datetime.now(UTC)
        data = {
            "symbol": "INVALID",
            "is_valid": False,
            "validation_source": "Alpha Vantage",
            "validation_timestamp": validation_timestamp,
        }

        # Act
        ticker = ValidatedTicker(**data)

        # Assert
        assert ticker.symbol == "INVALID"
        assert ticker.is_valid is False
        assert ticker.market is None
        assert ticker.sector is None
        assert ticker.company_name is None
        assert ticker.validation_errors == []
        assert ticker.alternative_suggestions == []

    def test_should_handle_validation_errors_and_suggestions(self):
        """Test handling validation errors and alternative suggestions."""
        # Arrange
        validation_timestamp = datetime.now(UTC)
        data = {
            "symbol": "BADTICKER",
            "is_valid": False,
            "validation_source": "Yahoo Finance",
            "validation_timestamp": validation_timestamp,
            "validation_errors": ["Symbol not found", "Invalid format"],
            "alternative_suggestions": ["GOODTICKER", "ANOTHERTICKER"],
        }

        # Act
        ticker = ValidatedTicker(**data)

        # Assert
        assert ticker.validation_errors == ["Symbol not found", "Invalid format"]
        assert ticker.alternative_suggestions == ["GOODTICKER", "ANOTHERTICKER"]


class TestValidatedETF:
    """Test ValidatedETF model."""

    def test_should_create_valid_etf_when_all_fields_provided(self):
        """Test creating a valid ValidatedETF with all fields."""
        # Arrange
        validation_timestamp = datetime.now(UTC)
        data = {
            "symbol": "SPY",
            "is_valid": True,
            "validation_source": "Yahoo Finance",
            "validation_timestamp": validation_timestamp,
            "fund_name": "SPDR S&P 500 ETF Trust",
            "issuer": "State Street",
            "expense_ratio": 0.09,
            "validation_errors": [],
        }

        # Act
        etf = ValidatedETF(**data)

        # Assert
        assert etf.symbol == "SPY"
        assert etf.is_valid is True
        assert etf.validation_source == "Yahoo Finance"
        assert etf.fund_name == "SPDR S&P 500 ETF Trust"
        assert etf.issuer == "State Street"
        assert etf.expense_ratio == 0.09
        assert etf.validation_errors == []

    def test_should_raise_validation_error_when_expense_ratio_invalid(self):
        """Test validation error for invalid expense ratio."""
        # Arrange
        data = {
            "symbol": "SPY",
            "is_valid": True,
            "validation_source": "Yahoo Finance",
            "validation_timestamp": datetime.now(UTC),
            "expense_ratio": 10.0,  # > 5.0
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ValidatedETF(**data)

        assert "expense_ratio" in str(exc_info.value)


class TestValidatedCrypto:
    """Test ValidatedCrypto model."""

    def test_should_create_valid_crypto_when_all_fields_provided(self):
        """Test creating a valid ValidatedCrypto with all fields."""
        # Arrange
        validation_timestamp = datetime.now(UTC)
        data = {
            "symbol": "BTC",
            "is_valid": True,
            "validation_source": "CoinMarketCap",
            "validation_timestamp": validation_timestamp,
            "full_name": "Bitcoin",
            "market_cap_rank": 1,
            "is_active": True,
            "validation_errors": [],
        }

        # Act
        crypto = ValidatedCrypto(**data)

        # Assert
        assert crypto.symbol == "BTC"
        assert crypto.is_valid is True
        assert crypto.validation_source == "CoinMarketCap"
        assert crypto.full_name == "Bitcoin"
        assert crypto.market_cap_rank == 1
        assert crypto.is_active is True
        assert crypto.validation_errors == []

    def test_should_raise_validation_error_when_market_cap_rank_invalid(self):
        """Test validation error for invalid market cap rank."""
        # Arrange
        data = {
            "symbol": "BTC",
            "is_valid": True,
            "validation_source": "CoinMarketCap",
            "validation_timestamp": datetime.now(UTC),
            "market_cap_rank": 0,  # Should be >= 1
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ValidatedCrypto(**data)

        assert "market_cap_rank" in str(exc_info.value)


class TestEnhancedCrewOutputs:
    """Test enhanced crew output schemas."""

    def create_valid_metadata(self) -> CrewOutputMetadata:
        """Create valid CrewOutputMetadata."""
        validation_status = ValidationStatus(is_valid=True, validation_timestamp=datetime.now(UTC))
        freshness_status = FreshnessStatus(is_fresh=True, age_hours=1.0, refresh_recommended=False, last_updated=datetime.now(UTC))

        return CrewOutputMetadata(
            crew_name="test_crew",
            execution_timestamp=datetime.now(UTC),
            validation_status=validation_status,
            dependencies_met=True,
            freshness_status=freshness_status,
        )

    def test_should_create_valid_stock_crew_output(self):
        """Test creating a valid StockCrewOutput."""
        # Arrange
        metadata = self.create_valid_metadata()
        metadata.crew_name = "stock_crew"

        validated_ticker = ValidatedTicker(
            symbol="AAPL", is_valid=True, validation_source="Yahoo Finance", validation_timestamp=datetime.now(UTC)
        )

        sec_citation = SECCitation(
            ticker="AAPL",
            filing_url="https://www.sec.gov/test",
            filed_at=datetime.now(UTC),
            section="Item 1A",
            excerpt="Test excerpt that is long enough for validation",
            sec_citation="10-K (2024), Item 1A, p. 17",
            extraction_timestamp=datetime.now(UTC),
            validation_status=ValidationStatus(is_valid=True, validation_timestamp=datetime.now(UTC)),
        )

        data = {"metadata": metadata, "validated_tickers": [validated_ticker], "sec_citations": [sec_citation]}

        # Act
        output = StockCrewOutput(**data)

        # Assert
        assert output.metadata.crew_name == "stock_crew"
        assert len(output.validated_tickers) == 1
        assert output.validated_tickers[0].symbol == "AAPL"
        assert len(output.sec_citations) == 1
        assert output.sec_citations[0].ticker == "AAPL"
        assert output.ten_k_insights == []  # Default empty list
        assert output.market_sentiments == []  # Default empty list
        assert output.risk_assessments == []  # Default empty list

    def test_should_create_valid_etf_crew_output(self):
        """Test creating a valid ETFCrewOutput."""
        # Arrange
        metadata = self.create_valid_metadata()
        metadata.crew_name = "etf_crew"

        validated_etf = ValidatedETF(
            symbol="SPY", is_valid=True, validation_source="Yahoo Finance", validation_timestamp=datetime.now(UTC)
        )

        data = {"metadata": metadata, "validated_etfs": [validated_etf]}

        # Act
        output = ETFCrewOutput(**data)

        # Assert
        assert output.metadata.crew_name == "etf_crew"
        assert len(output.validated_etfs) == 1
        assert output.validated_etfs[0].symbol == "SPY"
        assert output.factsheets == []  # Default empty list
        assert output.holdings_analysis == []  # Default empty list
        assert output.risk_assessments == []  # Default empty list

    def test_should_create_valid_crypto_crew_output(self):
        """Test creating a valid CryptoCrewOutput."""
        # Arrange
        metadata = self.create_valid_metadata()
        metadata.crew_name = "crypto_crew"

        validated_crypto = ValidatedCrypto(
            symbol="BTC", is_valid=True, validation_source="CoinMarketCap", validation_timestamp=datetime.now(UTC)
        )

        data = {"metadata": metadata, "validated_symbols": [validated_crypto]}

        # Act
        output = CryptoCrewOutput(**data)

        # Assert
        assert output.metadata.crew_name == "crypto_crew"
        assert len(output.validated_symbols) == 1
        assert output.validated_symbols[0].symbol == "BTC"
        assert output.crypto_theses == []  # Default empty list
        assert output.risk_assessments == []  # Default empty list
        assert output.market_analysis == []  # Default empty list


class TestAPlusOpportunityCollection:
    """Test APlusOpportunityCollection model."""

    def test_should_create_valid_opportunity_collection_when_all_fields_provided(self):
        """Test creating a valid APlusOpportunityCollection with all fields."""
        # Arrange
        validation_timestamp = datetime.now(UTC)
        data = {
            "etf_opportunities": ["SPY", "QQQ", "VTI"],
            "stock_opportunities": ["AAPL", "MSFT", "GOOGL"],
            "crypto_opportunities": ["BTC", "ETH"],
            "discovery_summary": "Found several high-quality opportunities with strong fundamentals",
            "confidence_score": 0.85,
            "validation_timestamp": validation_timestamp,
            "allocation_recommendations": [{"symbol": "SPY", "allocation": 0.4}, {"symbol": "AAPL", "allocation": 0.3}],
            "replacement_notes": ["Replace low-performing bond ETF", "Upgrade tech exposure"],
        }

        # Act
        collection = APlusOpportunityCollection(**data)

        # Assert
        assert collection.etf_opportunities == ["SPY", "QQQ", "VTI"]
        assert collection.stock_opportunities == ["AAPL", "MSFT", "GOOGL"]
        assert collection.crypto_opportunities == ["BTC", "ETH"]
        assert collection.discovery_summary == "Found several high-quality opportunities with strong fundamentals"
        assert collection.confidence_score == 0.85
        assert collection.validation_timestamp == validation_timestamp
        assert len(collection.allocation_recommendations) == 2
        assert collection.replacement_notes == ["Replace low-performing bond ETF", "Upgrade tech exposure"]

    def test_should_create_collection_with_defaults_when_optional_fields_omitted(self):
        """Test creating APlusOpportunityCollection with default values."""
        # Arrange
        validation_timestamp = datetime.now(UTC)
        data = {
            "discovery_summary": "Basic discovery analysis completed successfully",
            "confidence_score": 0.5,
            "validation_timestamp": validation_timestamp,
        }

        # Act
        collection = APlusOpportunityCollection(**data)

        # Assert
        assert collection.etf_opportunities == []
        assert collection.stock_opportunities == []
        assert collection.crypto_opportunities == []
        assert collection.allocation_recommendations == []
        assert collection.replacement_notes == []

    def test_should_raise_validation_error_when_confidence_score_out_of_range(self):
        """Test validation error for confidence score outside valid range."""
        # Arrange
        data = {
            "discovery_summary": "Test summary that is long enough",
            "confidence_score": 1.5,  # > 1.0
            "validation_timestamp": datetime.now(UTC),
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            APlusOpportunityCollection(**data)

        assert "confidence_score" in str(exc_info.value)

    def test_should_raise_validation_error_when_discovery_summary_too_short(self):
        """Test validation error for discovery summary that's too short."""
        # Arrange
        data = {
            "discovery_summary": "Too short",  # < 10 characters
            "confidence_score": 0.7,
            "validation_timestamp": datetime.now(UTC),
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            APlusOpportunityCollection(**data)

        assert "discovery_summary" in str(exc_info.value)


class TestIntegrationError:
    """Test IntegrationError model."""

    def test_should_create_valid_integration_error_when_all_fields_provided(self):
        """Test creating a valid IntegrationError with all fields."""
        # Arrange
        timestamp = datetime.now(UTC)
        data = {
            "error_type": "MISSING_DATA",
            "crew_name": "stock_crew",
            "error_message": "Required stock data file not found",
            "expected_path": "/output/stock/stock_analysis.json",
            "actual_path": "/output/stock/",
            "recovery_suggestions": ["Run stock crew first", "Check file permissions"],
            "timestamp": timestamp,
            "context": {"ticker": "AAPL", "retry_count": 2},
        }

        # Act
        error = IntegrationError(**data)

        # Assert
        assert error.error_type == "MISSING_DATA"
        assert error.crew_name == "stock_crew"
        assert error.error_message == "Required stock data file not found"
        assert error.expected_path == "/output/stock/stock_analysis.json"
        assert error.actual_path == "/output/stock/"
        assert error.recovery_suggestions == ["Run stock crew first", "Check file permissions"]
        assert error.timestamp == timestamp
        assert error.context == {"ticker": "AAPL", "retry_count": 2}

    def test_should_create_error_with_defaults_when_optional_fields_omitted(self):
        """Test creating IntegrationError with default values."""
        # Arrange
        timestamp = datetime.now(UTC)
        data = {
            "error_type": "VALIDATION_ERROR",
            "crew_name": "etf_crew",
            "error_message": "Schema validation failed",
            "timestamp": timestamp,
        }

        # Act
        error = IntegrationError(**data)

        # Assert
        assert error.expected_path is None
        assert error.actual_path is None
        assert error.recovery_suggestions == []
        assert error.context == {}

    def test_should_validate_all_error_types(self):
        """Test that all IntegrationErrorType enum values are valid."""
        # Arrange
        timestamp = datetime.now(UTC)
        error_types = ["MISSING_DATA", "STALE_DATA", "VALIDATION_ERROR", "ACCESS_ERROR", "DEPENDENCY_ERROR", "SCHEMA_ERROR"]

        # Act & Assert
        for error_type in error_types:
            data = {
                "error_type": error_type,
                "crew_name": "test_crew",
                "error_message": "Test error message",
                "timestamp": timestamp,
            }
            error = IntegrationError(**data)
            assert error.error_type == error_type


class TestDataAvailabilityReport:
    """Test DataAvailabilityReport model."""

    def test_should_create_valid_availability_report_when_all_fields_provided(self):
        """Test creating a valid DataAvailabilityReport with all fields."""
        # Arrange
        report_timestamp = datetime.now(UTC)
        integration_error = IntegrationError(
            error_type="MISSING_DATA",
            crew_name="crypto_crew",
            error_message="Crypto data not available",
            timestamp=datetime.now(UTC),
        )

        data = {
            "stock_available": True,
            "etf_available": True,
            "crypto_available": False,
            "discovery_available": True,
            "portfolio_available": True,
            "missing_data": ["crypto_analysis.json"],
            "stale_data": ["old_stock_data.json"],
            "integration_errors": [integration_error],
            "overall_status": "PARTIAL",
            "report_timestamp": report_timestamp,
            "data_freshness_summary": {"stock": "fresh", "etf": "fresh", "crypto": "missing"},
            "recommendations": ["Run crypto crew", "Refresh stale data"],
        }

        # Act
        report = DataAvailabilityReport(**data)

        # Assert
        assert report.stock_available is True
        assert report.etf_available is True
        assert report.crypto_available is False
        assert report.discovery_available is True
        assert report.portfolio_available is True
        assert report.missing_data == ["crypto_analysis.json"]
        assert report.stale_data == ["old_stock_data.json"]
        assert len(report.integration_errors) == 1
        assert report.integration_errors[0].crew_name == "crypto_crew"
        assert report.overall_status == "PARTIAL"
        assert report.report_timestamp == report_timestamp
        assert report.data_freshness_summary == {"stock": "fresh", "etf": "fresh", "crypto": "missing"}
        assert report.recommendations == ["Run crypto crew", "Refresh stale data"]

    def test_should_create_report_with_defaults_when_optional_fields_omitted(self):
        """Test creating DataAvailabilityReport with default values."""
        # Arrange
        report_timestamp = datetime.now(UTC)
        data = {
            "stock_available": False,
            "etf_available": False,
            "crypto_available": False,
            "discovery_available": False,
            "portfolio_available": False,
            "overall_status": "UNAVAILABLE",
            "report_timestamp": report_timestamp,
        }

        # Act
        report = DataAvailabilityReport(**data)

        # Assert
        assert report.missing_data == []
        assert report.stale_data == []
        assert report.integration_errors == []
        assert report.data_freshness_summary == {}
        assert report.recommendations == []

    def test_should_validate_all_availability_status_values(self):
        """Test that all DataAvailabilityStatus enum values are valid."""
        # Arrange
        report_timestamp = datetime.now(UTC)
        status_values = ["COMPLETE", "PARTIAL", "INSUFFICIENT", "UNAVAILABLE"]

        # Act & Assert
        for status in status_values:
            data = {
                "stock_available": True,
                "etf_available": True,
                "crypto_available": True,
                "discovery_available": True,
                "portfolio_available": True,
                "overall_status": status,
                "report_timestamp": report_timestamp,
            }
            report = DataAvailabilityReport(**data)
            assert report.overall_status == status


class TestDiscoveryCrewOutput:
    """Test DiscoveryCrewOutput model."""

    def create_valid_metadata(self) -> CrewOutputMetadata:
        """Create valid CrewOutputMetadata."""
        validation_status = ValidationStatus(is_valid=True, validation_timestamp=datetime.now(UTC))
        freshness_status = FreshnessStatus(is_fresh=True, age_hours=1.0, refresh_recommended=False, last_updated=datetime.now(UTC))

        return CrewOutputMetadata(
            crew_name="discovery_crew",
            execution_timestamp=datetime.now(UTC),
            validation_status=validation_status,
            dependencies_met=True,
            freshness_status=freshness_status,
        )

    def create_valid_aplus_collection(self) -> APlusOpportunityCollection:
        """Create valid APlusOpportunityCollection."""
        return APlusOpportunityCollection(
            etf_opportunities=["SPY", "QQQ"],
            stock_opportunities=["AAPL", "MSFT"],
            crypto_opportunities=["BTC"],
            discovery_summary="Found excellent opportunities with strong fundamentals",
            confidence_score=0.9,
            validation_timestamp=datetime.now(UTC),
        )

    def test_should_create_valid_discovery_crew_output(self):
        """Test creating a valid DiscoveryCrewOutput."""
        # Arrange
        metadata = self.create_valid_metadata()
        aplus_collection = self.create_valid_aplus_collection()

        data = {
            "metadata": metadata,
            "a_plus_opportunities": aplus_collection,
            "portfolio_improvements": [{"type": "diversification", "impact": "high"}],
            "optimization_results": [{"strategy": "momentum", "expected_return": 0.12}],
            "validation_results": [{"symbol": "AAPL", "valid": True}],
            "market_analysis": {"trend": "bullish", "volatility": "moderate"},
        }

        # Act
        output = DiscoveryCrewOutput(**data)

        # Assert
        assert output.metadata.crew_name == "discovery_crew"
        assert len(output.a_plus_opportunities.etf_opportunities) == 2
        assert output.a_plus_opportunities.etf_opportunities == ["SPY", "QQQ"]
        assert len(output.portfolio_improvements) == 1
        assert output.portfolio_improvements[0]["type"] == "diversification"
        assert len(output.optimization_results) == 1
        assert output.optimization_results[0]["strategy"] == "momentum"
        assert len(output.validation_results) == 1
        assert output.validation_results[0]["symbol"] == "AAPL"
        assert output.market_analysis["trend"] == "bullish"

    def test_should_create_discovery_output_with_defaults_when_optional_fields_omitted(self):
        """Test creating DiscoveryCrewOutput with default values."""
        # Arrange
        metadata = self.create_valid_metadata()
        aplus_collection = self.create_valid_aplus_collection()

        data = {"metadata": metadata, "a_plus_opportunities": aplus_collection}

        # Act
        output = DiscoveryCrewOutput(**data)

        # Assert
        assert output.portfolio_improvements == []
        assert output.optimization_results == []
        assert output.validation_results == []
        assert output.market_analysis == {}
