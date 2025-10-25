"""
Unit tests for A+ Opportunity Data Extractor.

Tests the extraction and processing of A+ investment opportunities from
discovery crew markdown files with full mocking to avoid file system dependencies.
"""

from datetime import datetime

import pytest

from finwiz.integration.aplus_extractor import APlusDataExtractor
from finwiz.schemas.integration import APlusOpportunityCollection


class TestAPlusDataExtractor:
    """Test suite for APlusDataExtractor class."""

    @pytest.fixture
    def mock_output_dir(self, tmp_path):
        """Create a mock output directory structure."""
        output_dir = tmp_path / "output"
        discovery_dir = output_dir / "discovery"
        discovery_dir.mkdir(parents=True)
        return output_dir

    @pytest.fixture
    def extractor(self, mock_output_dir):
        """Create APlusDataExtractor instance with mocked directory."""
        return APlusDataExtractor(output_dir=mock_output_dir)

    @pytest.fixture
    def sample_stock_content(self):
        """Sample stock A+ opportunities content."""
        return """{
  "asset_type": "stock",
  "total_screened": 100,
  "candidates_found": 3,
  "discovery_timestamp": "2025-10-06T21:00:00",
  "average_score": 0.96,
  "a_plus_percentage": 3.0,
  "screening_efficiency": 3.0,
  "a_plus_candidates": [
    {
      "candidate": {
        "symbol": "NVDA",
        "name": "NVIDIA",
        "asset_type": "stock",
        "current_price": 450.0,
        "market_cap": 1100000000000,
        "preliminary_score": 0.98,
        "final_score": 0.98,
        "grade": "A+",
        "grade_description": "Exceptional quality",
        "recommended_action": "Strong buy",
        "discovery_date": "2025-10-06T21:00:00",
        "data_source": "Yahoo Finance",
        "risk_assessment": {
          "score": 3.5,
          "category": "Medium",
          "factors": ["Market volatility"]
        }
      },
      "composite_score": 0.98,
      "confidence_level": 0.95,
      "rationale": ["ROE 45%", "Revenue CAGR 36%"],
      "key_metrics": {"roe": 45.0, "revenue_growth": 36.0}
    },
    {
      "candidate": {
        "symbol": "AVGO",
        "name": "Broadcom",
        "asset_type": "stock",
        "current_price": 850.0,
        "market_cap": 400000000000,
        "preliminary_score": 0.96,
        "final_score": 0.96,
        "grade": "A+",
        "grade_description": "Exceptional quality",
        "recommended_action": "Buy",
        "discovery_date": "2025-10-06T21:00:00",
        "data_source": "Yahoo Finance",
        "risk_assessment": {
          "score": 3.0,
          "category": "Medium",
          "factors": ["Market risk"]
        }
      },
      "composite_score": 0.96,
      "confidence_level": 0.92,
      "rationale": ["ROE 40%", "Revenue CAGR 20%"],
      "key_metrics": {"roe": 40.0, "revenue_growth": 20.0}
    },
    {
      "candidate": {
        "symbol": "ADBE",
        "name": "Adobe",
        "asset_type": "stock",
        "current_price": 550.0,
        "market_cap": 250000000000,
        "preliminary_score": 0.93,
        "final_score": 0.93,
        "grade": "A",
        "grade_description": "High quality",
        "recommended_action": "Buy",
        "discovery_date": "2025-10-06T21:00:00",
        "data_source": "Yahoo Finance",
        "risk_assessment": {
          "score": 2.5,
          "category": "Low-Medium",
          "factors": ["Stable business"]
        }
      },
      "composite_score": 0.93,
      "confidence_level": 0.90,
      "rationale": ["ROE 32%", "Revenue CAGR 16%"],
      "key_metrics": {"roe": 32.0, "revenue_growth": 16.0}
    }
  ]
}"""

    @pytest.fixture
    def sample_etf_content(self):
        """Sample ETF A+ opportunities content."""
        return """{
  "asset_type": "etf",
  "total_screened": 200,
  "candidates_found": 3,
  "discovery_timestamp": "2025-10-06T21:00:00",
  "average_score": 0.96,
  "a_plus_percentage": 1.5,
  "screening_efficiency": 1.5,
  "a_plus_candidates": [
    {
      "candidate": {
        "symbol": "VWCE",
        "name": "Vanguard FTSE All-World UCITS ETF",
        "asset_type": "etf",
        "current_price": 105.0,
        "market_cap": 17500000000,
        "preliminary_score": 0.962,
        "final_score": 0.962,
        "grade": "A+",
        "grade_description": "Exceptional ETF",
        "recommended_action": "Core holding",
        "discovery_date": "2025-10-06T21:00:00",
        "data_source": "Yahoo Finance"
      },
      "composite_score": 0.962,
      "confidence_level": 0.95,
      "rationale": ["Low TER 0.22%", "Global diversification"],
      "key_metrics": {"ter": 0.0022, "aum_usd": 17500000000}
    },
    {
      "candidate": {
        "symbol": "IWDA",
        "name": "iShares Core MSCI World UCITS ETF",
        "asset_type": "etf",
        "current_price": 75.0,
        "market_cap": 60000000000,
        "preliminary_score": 0.958,
        "final_score": 0.958,
        "grade": "A+",
        "grade_description": "Exceptional ETF",
        "recommended_action": "Core holding",
        "discovery_date": "2025-10-06T21:00:00",
        "data_source": "Yahoo Finance"
      },
      "composite_score": 0.958,
      "confidence_level": 0.94,
      "rationale": ["Low TER 0.20%", "Developed markets"],
      "key_metrics": {"ter": 0.0020, "aum_usd": 60000000000}
    },
    {
      "candidate": {
        "symbol": "CSPX",
        "name": "iShares Core S&P 500 UCITS ETF",
        "asset_type": "etf",
        "current_price": 450.0,
        "market_cap": 65000000000,
        "preliminary_score": 0.957,
        "final_score": 0.957,
        "grade": "A+",
        "grade_description": "Exceptional ETF",
        "recommended_action": "Core holding",
        "discovery_date": "2025-10-06T21:00:00",
        "data_source": "Yahoo Finance"
      },
      "composite_score": 0.957,
      "confidence_level": 0.93,
      "rationale": ["Ultra-low TER 0.07%", "S&P 500 exposure"],
      "key_metrics": {"ter": 0.0007, "aum_usd": 65000000000}
    }
  ]
}"""

    @pytest.fixture
    def sample_crypto_content(self):
        """Sample crypto A+ opportunities content."""
        return """{
  "asset_type": "crypto",
  "total_screened": 50,
  "candidates_found": 3,
  "discovery_timestamp": "2025-10-06T21:00:00",
  "average_score": 0.96,
  "a_plus_percentage": 6.0,
  "screening_efficiency": 6.0,
  "a_plus_candidates": [
    {
      "candidate": {
        "symbol": "BTC-USD",
        "name": "Bitcoin",
        "asset_type": "crypto",
        "current_price": 65000.0,
        "market_cap": 1200000000000,
        "preliminary_score": 0.98,
        "final_score": 0.98,
        "grade": "A+",
        "grade_description": "Exceptional crypto",
        "recommended_action": "Core crypto holding",
        "discovery_date": "2025-10-06T21:00:00",
        "data_source": "CoinMarketCap",
        "risk_assessment": {
          "score": 7.0,
          "category": "High",
          "factors": ["Volatility"]
        }
      },
      "composite_score": 0.98,
      "confidence_level": 0.95,
      "rationale": ["Deepest liquidity", "Regulatory clarity"],
      "key_metrics": {"market_cap": 1200000000000, "volume_24h": 30000000000}
    },
    {
      "candidate": {
        "symbol": "ETH-USD",
        "name": "Ethereum",
        "asset_type": "crypto",
        "current_price": 3500.0,
        "market_cap": 420000000000,
        "preliminary_score": 0.96,
        "final_score": 0.96,
        "grade": "A+",
        "grade_description": "Exceptional crypto",
        "recommended_action": "Core crypto holding",
        "discovery_date": "2025-10-06T21:00:00",
        "data_source": "CoinMarketCap",
        "risk_assessment": {
          "score": 7.5,
          "category": "High",
          "factors": ["Volatility", "Smart contract risk"]
        }
      },
      "composite_score": 0.96,
      "confidence_level": 0.93,
      "rationale": ["Smart contract leader", "Deflationary tokenomics"],
      "key_metrics": {"market_cap": 420000000000, "volume_24h": 15000000000}
    },
    {
      "candidate": {
        "symbol": "SOL-USD",
        "name": "Solana",
        "asset_type": "crypto",
        "current_price": 150.0,
        "market_cap": 65000000000,
        "preliminary_score": 0.93,
        "final_score": 0.93,
        "grade": "A",
        "grade_description": "High quality crypto",
        "recommended_action": "Satellite holding",
        "discovery_date": "2025-10-06T21:00:00",
        "data_source": "CoinMarketCap",
        "risk_assessment": {
          "score": 8.0,
          "category": "High",
          "factors": ["High volatility", "Network stability"]
        }
      },
      "composite_score": 0.93,
      "confidence_level": 0.88,
      "rationale": ["High-throughput L1", "Strong payments momentum"],
      "key_metrics": {"market_cap": 65000000000, "volume_24h": 2000000000}
    }
  ]
}"""

    def test_should_initialize_extractor_when_valid_output_dir_provided(self, mock_output_dir):
        """Test extractor initialization with valid output directory."""
        # Act
        extractor = APlusDataExtractor(output_dir=mock_output_dir)

        # Assert
        assert extractor.output_dir == mock_output_dir
        assert extractor.discovery_dir == mock_output_dir / "discovery"
        assert extractor.logger is not None

    def test_should_return_none_when_discovery_directory_missing(self, tmp_path):
        """Test extraction returns None when discovery directory doesn't exist."""
        # Arrange
        output_dir = tmp_path / "output"
        # Don't create discovery directory
        extractor = APlusDataExtractor(output_dir=output_dir)

        # Act
        result = extractor.extract_aplus_opportunities()

        # Assert
        assert result is None

    def test_should_extract_stock_opportunities_when_valid_file_exists(self, mocker, extractor, sample_stock_content):
        """Test extraction of stock opportunities from markdown file."""
        # Arrange
        mock_exists = mocker.patch("pathlib.Path.exists")
        mock_read_text = mocker.patch("pathlib.Path.read_text")
        mock_exists.return_value = True
        mock_read_text.return_value = sample_stock_content

        # Act
        opportunities = extractor._extract_stock_opportunities()

        # Assert
        assert len(opportunities) == 3

        # Check first opportunity (NVIDIA)
        nvda = opportunities[0]
        assert nvda["symbol"] == "NVDA"
        assert nvda["name"] == "NVIDIA"
        assert nvda["grade"] == "A+"
        assert nvda["composite_score"] >= 0.85
        assert nvda["confidence"] >= 0.8
        assert "rationale" in nvda
        assert "key_metrics" in nvda

        # Check second opportunity (Broadcom)
        avgo = opportunities[1]
        assert avgo["symbol"] == "AVGO"
        assert avgo["name"] == "Broadcom"
        assert avgo["grade"] == "A+"
        assert avgo["composite_score"] >= 0.85
        assert avgo["confidence"] >= 0.8

        # Check third opportunity (Adobe - A grade)
        adbe = opportunities[2]
        assert adbe["symbol"] == "ADBE"
        assert adbe["grade"] == "A"
        assert adbe["confidence"] >= 0.8

    def test_should_extract_etf_opportunities_when_valid_file_exists(self, mocker, extractor, sample_etf_content):
        """Test extraction of ETF opportunities from markdown file."""
        # Arrange
        mock_exists = mocker.patch("pathlib.Path.exists", return_value=True)
        mock_read_text = mocker.patch("pathlib.Path.read_text", return_value=sample_etf_content)

        # Act
        opportunities = extractor._extract_etf_opportunities()

        # Assert
        assert len(opportunities) == 3

        # Check first opportunity (VWCE)
        vwce = opportunities[0]
        assert vwce["symbol"] == "VWCE"
        assert vwce["name"] == "Vanguard FTSE All-World UCITS ETF"
        assert vwce["grade"] == "A+"
        assert vwce["composite_score"] >= 0.85
        assert "key_metrics" in vwce
        assert "rationale" in vwce

        # Check second opportunity (IWDA)
        iwda = opportunities[1]
        assert iwda["symbol"] == "IWDA"
        assert iwda["grade"] == "A+"
        assert iwda["composite_score"] >= 0.85

        # Check third opportunity (CSPX)
        cspx = opportunities[2]
        assert cspx["symbol"] == "CSPX"
        assert cspx["grade"] == "A+"

    def test_should_extract_crypto_opportunities_when_valid_file_exists(self, mocker, extractor, sample_crypto_content):
        """Test extraction of crypto opportunities from markdown file."""
        # Arrange
        mock_exists = mocker.patch("pathlib.Path.exists", return_value=True)
        mock_read_text = mocker.patch("pathlib.Path.read_text", return_value=sample_crypto_content)

        # Act
        opportunities = extractor._extract_crypto_opportunities()

        # Assert
        assert len(opportunities) == 3

        # Check first opportunity (Bitcoin)
        btc = opportunities[0]
        assert btc["symbol"] == "BTC"  # Should strip -USD
        assert btc["name"] == "Bitcoin"
        assert btc["grade"] == "A+"
        assert btc["composite_score"] >= 0.80
        assert btc["confidence"] >= 0.8
        assert "rationale" in btc
        assert "key_metrics" in btc

        # Check second opportunity (Ethereum)
        eth = opportunities[1]
        assert eth["symbol"] == "ETH"
        assert eth["name"] == "Ethereum"
        assert eth["grade"] == "A+"
        assert eth["confidence"] >= 0.8

        # Check third opportunity (Solana - A grade)
        sol = opportunities[2]
        assert sol["symbol"] == "SOL"
        assert sol["grade"] == "A"
        assert sol["confidence"] >= 0.8

    def test_should_return_empty_list_when_file_missing(self, mocker, extractor):
        """Test extraction returns empty list when files are missing."""
        # Arrange
        mock_exists = mocker.patch("pathlib.Path.exists", return_value=False)

        # Act
        stock_opportunities = extractor._extract_stock_opportunities()
        etf_opportunities = extractor._extract_etf_opportunities()
        crypto_opportunities = extractor._extract_crypto_opportunities()

        # Assert
        assert stock_opportunities == []
        assert etf_opportunities == []
        assert crypto_opportunities == []

    def test_should_handle_file_read_errors_gracefully(self, mocker, extractor):
        """Test extraction handles file read errors gracefully."""
        # Arrange
        mock_exists = mocker.patch("pathlib.Path.exists")
        mock_read_text = mocker.patch("pathlib.Path.read_text")
        mock_exists.return_value = True
        mock_read_text.side_effect = OSError("File read error")

        # Act
        opportunities = extractor._extract_stock_opportunities()

        # Assert
        assert opportunities == []

    def test_should_extract_complete_aplus_collection_when_all_files_exist(
        self, mocker, extractor, sample_stock_content, sample_etf_content, sample_crypto_content
    ):
        mock_exists = mocker.patch("pathlib.Path.exists")
        mock_read_text = mocker.patch("pathlib.Path.read_text")
        """Test complete A+ opportunities extraction from all files."""
        # Arrange
        mock_exists.return_value = True

        def mock_read_side_effect(encoding=None):
            # Return different content based on which file is being read
            # This is a simplified approach - in reality we'd need to check the file path
            if "stock" in str(mock_read_text.call_count):
                return sample_stock_content
            elif "etf" in str(mock_read_text.call_count):
                return sample_etf_content
            else:
                return sample_crypto_content

        # Set up side effect to return appropriate content for each file
        mock_read_text.side_effect = [sample_stock_content, sample_etf_content, sample_crypto_content]

        # Act
        collection = extractor.extract_aplus_opportunities()

        # Assert
        assert collection is not None
        assert isinstance(collection, APlusOpportunityCollection)

        # Check extracted opportunities (now APlusOpportunity objects, not strings)
        assert len(collection.stock_opportunities) == 3
        stock_symbols = [opp.symbol for opp in collection.stock_opportunities]
        assert "NVDA" in stock_symbols
        assert "AVGO" in stock_symbols
        assert "ADBE" in stock_symbols

        assert len(collection.etf_opportunities) == 3
        etf_symbols = [opp.symbol for opp in collection.etf_opportunities]
        assert "VWCE" in etf_symbols
        assert "IWDA" in etf_symbols
        assert "CSPX" in etf_symbols

        assert len(collection.crypto_opportunities) == 3
        crypto_symbols = [opp.symbol for opp in collection.crypto_opportunities]
        assert "BTC" in crypto_symbols
        assert "ETH" in crypto_symbols
        assert "SOL" in crypto_symbols

        # Check metadata
        assert collection.confidence_score > 0.8  # Should be high with many A+ opportunities
        assert len(collection.discovery_summary) > 50
        assert collection.validation_timestamp is not None
        assert len(collection.allocation_recommendations) > 0
        assert len(collection.replacement_notes) > 0

    def test_should_generate_appropriate_discovery_summary_when_opportunities_exist(self, extractor):
        """Test discovery summary generation with various opportunity combinations."""
        # Arrange
        stocks = [{"grade": "A+"}, {"grade": "A"}]
        etfs = [{"grade": "A+"}, {"grade": "A+"}, {"grade": "A"}]
        cryptos = [{"grade": "A+"}, {"grade": "A"}]

        # Act
        summary = extractor._generate_discovery_summary(stocks, etfs, cryptos)

        # Assert
        assert "7 high-quality investment opportunities" in summary
        assert "2 stock opportunities" in summary
        assert "3 ETF opportunities" in summary
        assert "2 crypto opportunities" in summary
        assert "fundamental analysis" in summary
        assert "competitive moats" in summary

    def test_should_generate_empty_summary_when_no_opportunities_exist(self, extractor):
        """Test discovery summary generation with no opportunities."""
        # Arrange
        stocks, etfs, cryptos = [], [], []

        # Act
        summary = extractor._generate_discovery_summary(stocks, etfs, cryptos)

        # Assert
        assert summary == "No A+ opportunities identified in current market conditions."

    def test_should_calculate_confidence_score_based_on_opportunity_quality(self, extractor):
        """Test confidence score calculation based on opportunities."""
        # Test with no opportunities
        assert extractor._calculate_confidence_score([], [], []) == 0.0

        # Test with few opportunities
        few_opportunities = [{"grade": "A"}] * 3
        score_few = extractor._calculate_confidence_score(few_opportunities, [], [])
        assert 0.7 <= score_few <= 0.8

        # Test with many A+ opportunities
        many_aplus = [{"grade": "A+"}] * 6
        score_many = extractor._calculate_confidence_score(many_aplus, [], [])
        assert score_many >= 0.89  # Allow for floating point precision

        # Test with mixed grades
        mixed = [{"grade": "A+"}, {"grade": "A"}, {"grade": "A+"}]
        score_mixed = extractor._calculate_confidence_score(mixed, [], [])
        assert 0.75 <= score_mixed <= 0.85

    def test_should_extract_allocation_recommendations_from_all_asset_types(self, extractor):
        """Test allocation recommendations extraction."""
        # Arrange
        stocks = [
            {"symbol": "NVDA", "allocation_recommendation": "5-8% aggressive", "grade": "A+", "rank": 1},
            {"symbol": "AVGO", "allocation_recommendation": "4-6% aggressive", "grade": "A+", "rank": 2},
        ]
        etfs = [{"symbol": "VWCE", "allocation_recommendation": "Core global equity", "grade": "A+", "rank": 1}]
        cryptos = [{"symbol": "BTC", "allocation_recommendation": "2% of portfolio", "grade": "A+", "rank": 1}]

        # Act
        recommendations = extractor._extract_allocation_recommendations(stocks, etfs, cryptos)

        # Assert
        assert len(recommendations) == 4

        # Check stock recommendation
        nvda_rec = next(r for r in recommendations if r["symbol"] == "NVDA")
        assert nvda_rec["asset_type"] == "stock"
        assert nvda_rec["allocation"] == "5-8% aggressive"
        assert nvda_rec["grade"] == "A+"

        # Check ETF recommendation
        vwce_rec = next(r for r in recommendations if r["symbol"] == "VWCE")
        assert vwce_rec["asset_type"] == "etf"
        assert vwce_rec["allocation"] == "Core global equity"

        # Check crypto recommendation
        btc_rec = next(r for r in recommendations if r["symbol"] == "BTC")
        assert btc_rec["asset_type"] == "crypto"
        assert btc_rec["allocation"] == "2% of portfolio"

    def test_should_extract_replacement_notes_from_all_asset_types(self, extractor):
        """Test replacement notes extraction."""
        # Arrange
        stocks = [
            {"symbol": "NVDA", "replacement_note": "Fits growth-maximizing sleeve"},
            {"symbol": "AVGO", "replacement_note": "Strong cash compounder"},
        ]
        etfs = [{"symbol": "VWCE", "replacement_note": "Can replace IWDA+EMIM"}]
        cryptos = [{"symbol": "BTC", "replacement_note": "Acts as core ballast"}]

        # Act
        notes = extractor._extract_replacement_notes(stocks, etfs, cryptos)

        # Assert
        assert len(notes) == 4
        assert "NVDA: Fits growth-maximizing sleeve" in notes
        assert "AVGO: Strong cash compounder" in notes
        assert "VWCE: Can replace IWDA+EMIM" in notes
        assert "BTC: Acts as core ballast" in notes

    def test_should_validate_aplus_opportunities_successfully_when_complete_data(self, extractor):
        """Test validation of complete A+ opportunities collection."""
        # Arrange
        from finwiz.schemas.integration_models import APlusOpportunity

        etf_opps = [
            APlusOpportunity(
                symbol="VWCE",
                name="Vanguard FTSE All-World",
                grade="A+",
                composite_score=0.96,
                confidence=0.95,
                risk_score=3.0,
                rationale=["Low TER", "Global diversification"],
                key_metrics={"ter": 0.0022},
            ),
            APlusOpportunity(
                symbol="IWDA",
                name="iShares Core MSCI World",
                grade="A+",
                composite_score=0.95,
                confidence=0.94,
                risk_score=3.0,
                rationale=["Low TER", "Developed markets"],
                key_metrics={"ter": 0.0020},
            ),
        ]

        stock_opps = [
            APlusOpportunity(
                symbol="NVDA",
                name="NVIDIA",
                grade="A+",
                composite_score=0.98,
                confidence=0.95,
                risk_score=3.5,
                rationale=["ROE 45%", "Revenue CAGR 36%"],
                key_metrics={"roe": 45.0},
            ),
            APlusOpportunity(
                symbol="AVGO",
                name="Broadcom",
                grade="A+",
                composite_score=0.96,
                confidence=0.92,
                risk_score=3.0,
                rationale=["ROE 40%", "Revenue CAGR 20%"],
                key_metrics={"roe": 40.0},
            ),
        ]

        crypto_opps = [
            APlusOpportunity(
                symbol="BTC",
                name="Bitcoin",
                grade="A+",
                composite_score=0.98,
                confidence=0.95,
                risk_score=7.0,
                rationale=["Deepest liquidity", "Regulatory clarity"],
                key_metrics={"market_cap": 1200000000000},
            ),
            APlusOpportunity(
                symbol="ETH",
                name="Ethereum",
                grade="A+",
                composite_score=0.96,
                confidence=0.93,
                risk_score=7.5,
                rationale=["Smart contract leader", "Deflationary tokenomics"],
                key_metrics={"market_cap": 420000000000},
            ),
        ]

        collection = APlusOpportunityCollection(
            etf_opportunities=etf_opps,
            stock_opportunities=stock_opps,
            crypto_opportunities=crypto_opps,
            discovery_summary=(
                "Comprehensive analysis identified 6 high-quality opportunities with strong fundamentals and growth potential."
            ),
            confidence_score=0.85,
            validation_timestamp=datetime.now(),
            allocation_recommendations=[{"asset_type": "stock", "symbol": "NVDA", "allocation": "5-8%", "grade": "A+", "rank": 1}],
            replacement_notes=["NVDA: Fits growth portfolio"],
        )

        # Act
        is_valid, errors = extractor.validate_aplus_opportunities(collection)

        # Assert
        assert is_valid is True
        assert len(errors) == 0

    def test_should_identify_validation_errors_when_incomplete_data(self, extractor):
        """Test validation identifies errors in incomplete A+ opportunities."""
        # Arrange
        collection = APlusOpportunityCollection(
            etf_opportunities=[],
            stock_opportunities=[],
            crypto_opportunities=[],
            discovery_summary="Brief summary that meets minimum length requirement",  # Fixed length
            confidence_score=0.3,  # Too low
            validation_timestamp=datetime.now(),
            allocation_recommendations=[],  # Empty
            replacement_notes=[],
        )

        # Act
        is_valid, errors = extractor.validate_aplus_opportunities(collection)

        # Assert
        assert is_valid is False
        assert len(errors) >= 3
        assert any("No A+ opportunities found" in error for error in errors)
        assert any("Low confidence score" in error for error in errors)
        # The discovery summary validation is handled by Pydantic, so we check other errors
        assert len(errors) >= 2  # Should have at least low confidence and no allocation recommendations
        assert any("No allocation recommendations" in error for error in errors)

    def test_should_detect_duplicate_symbols_in_validation(self, extractor):
        """Test validation detects duplicate symbols across asset types."""
        # Arrange
        from finwiz.schemas.integration_models import APlusOpportunity

        # Create duplicate NVDA in both ETF and stock (unrealistic but tests validation)
        nvda_etf = APlusOpportunity(
            symbol="NVDA",
            name="NVIDIA ETF",
            grade="A+",
            composite_score=0.96,
            confidence=0.95,
            risk_score=3.0,
            rationale=["Test"],
            key_metrics={},
        )

        nvda_stock = APlusOpportunity(
            symbol="NVDA",
            name="NVIDIA",
            grade="A+",
            composite_score=0.98,
            confidence=0.95,
            risk_score=3.5,
            rationale=["Test"],
            key_metrics={},
        )

        btc = APlusOpportunity(
            symbol="BTC",
            name="Bitcoin",
            grade="A+",
            composite_score=0.98,
            confidence=0.95,
            risk_score=7.0,
            rationale=["Test"],
            key_metrics={},
        )

        collection = APlusOpportunityCollection(
            etf_opportunities=[nvda_etf],
            stock_opportunities=[nvda_stock],
            crypto_opportunities=[btc],
            discovery_summary="Analysis identified opportunities with duplicate symbols for testing validation.",
            confidence_score=0.8,
            validation_timestamp=datetime.now(),
            allocation_recommendations=[{"asset_type": "stock", "symbol": "NVDA", "allocation": "5%", "grade": "A+", "rank": 1}],
            replacement_notes=["NVDA: Test note"],
        )

        # Act
        is_valid, errors = extractor.validate_aplus_opportunities(collection)

        # Assert
        assert is_valid is False
        assert any("Duplicate symbols found" in error for error in errors)

    def test_should_handle_extraction_errors_gracefully(self, mocker, extractor):
        """Test extraction handles unexpected errors gracefully."""
        # Arrange
        mock_exists = mocker.patch("pathlib.Path.exists", return_value=True)
        mock_read_text = mocker.patch("pathlib.Path.read_text", side_effect=Exception("Unexpected error"))

        # Act
        collection = extractor.extract_aplus_opportunities()

        # Assert
        # The extractor should still return a collection even if individual extractions fail
        # It will just have empty opportunities lists
        assert collection is not None
        assert len(collection.stock_opportunities) == 0
        assert len(collection.etf_opportunities) == 0
        assert len(collection.crypto_opportunities) == 0

    def test_should_handle_validation_errors_gracefully(self, extractor):
        """Test validation handles unexpected errors gracefully."""
        # Arrange
        invalid_collection = None  # This will cause an error

        # Act
        is_valid, errors = extractor.validate_aplus_opportunities(invalid_collection)

        # Assert
        assert is_valid is False
        assert len(errors) == 1
        assert "Validation error" in errors[0]
