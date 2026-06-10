"""
Unit tests for Enhanced Crypto Analysis Tool.

Tests the enhanced crypto analysis capabilities including investment thesis
generation, standardized risk assessment, and market dynamics analysis.
"""

import pytest

from finwiz.tools.enhanced_crypto_tool import (
    EnhancedCryptoAnalysisInput,
    EnhancedCryptoAnalysisTool,
)


class TestEnhancedCryptoAnalysisInput:
    """Test the input schema for Enhanced Crypto Analysis Tool."""

    def test_should_create_valid_input_with_defaults(self):
        """Test creating input with default values."""
        # Arrange & Act
        input_data = EnhancedCryptoAnalysisInput(symbol="BTC")

        # Assert
        assert input_data.symbol == "BTC"
        assert input_data.include_thesis is True
        assert input_data.include_risk_assessment is True
        assert input_data.max_thesis_bullets == 10

    def test_should_create_valid_input_with_custom_values(self):
        """Test creating input with custom values."""
        # Arrange & Act
        input_data = EnhancedCryptoAnalysisInput(symbol="ETH", include_thesis=False, include_risk_assessment=False, max_thesis_bullets=5)

        # Assert
        assert input_data.symbol == "ETH"
        assert input_data.include_thesis is False
        assert input_data.include_risk_assessment is False
        assert input_data.max_thesis_bullets == 5

    def test_should_validate_max_thesis_bullets_range(self):
        """Test validation of max_thesis_bullets parameter."""
        # Test valid range
        valid_input = EnhancedCryptoAnalysisInput(symbol="BTC", max_thesis_bullets=15)
        assert valid_input.max_thesis_bullets == 15

        # Test invalid range should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            EnhancedCryptoAnalysisInput(symbol="BTC", max_thesis_bullets=2)

        with pytest.raises(Exception):  # Pydantic validation error
            EnhancedCryptoAnalysisInput(symbol="BTC", max_thesis_bullets=25)


class TestEnhancedCryptoAnalysisTool:
    """Test the Enhanced Crypto Analysis Tool functionality."""

    @pytest.fixture
    def tool(self):
        """Create an instance of the Enhanced Crypto Analysis Tool."""
        return EnhancedCryptoAnalysisTool()

    @pytest.fixture
    def mock_coingecko_response(self):
        """Mock CoinGecko API response data."""
        return {
            "name": "Bitcoin",
            "description": {"en": "Bitcoin is the first successful internet money based on peer-to-peer technology"},
            "market_data": {
                "current_price": {"usd": 45000},
                "market_cap": {"usd": 850000000000},
                "market_cap_rank": 1,
                "total_volume": {"usd": 25000000000},
                "price_change_percentage_24h": 2.5,
                "price_change_percentage_7d": 8.2,
                "price_change_percentage_30d": 15.7,
                "ath": {"usd": 69000},
                "atl": {"usd": 0.05},
                "circulating_supply": 19500000,
                "total_supply": 19500000,
                "max_supply": 21000000,
            },
            "categories": ["Store of Value", "Digital Gold"],
            "links": {"homepage": ["https://bitcoin.org"]},
        }

    def test_should_normalize_symbol_input(self, tool, mocker):
        """Test symbol normalization."""
        # Arrange — mock the network boundaries (CoinGecko + Perplexity paths)
        mocker.patch.object(tool, "_get_crypto_data", return_value={"symbol": "BTC", "name": "Bitcoin", "sources": ["Test"]})
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=None)

        # Act
        result = tool._run(symbol="  btc  ", include_thesis=False, include_risk_assessment=False)

        # Assert
        assert result["symbol"] == "BTC"

    def test_should_get_coingecko_data_successfully(self, tool, mock_coingecko_response, mocker):
        """Test successful CoinGecko data retrieval."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_coingecko_response
        mocker.patch("requests.get", return_value=mock_response)

        # Act
        result = tool._get_coingecko_data("BTC")

        # Assert
        assert "error" not in result
        assert result["symbol"] == "BTC"
        assert result["name"] == "Bitcoin"
        assert result["current_price"] == 45000
        assert result["market_cap_rank"] == 1
        assert "Store of Value" in result["categories"]

    def test_should_handle_coingecko_404_with_symbol_mapping(self, tool, mock_coingecko_response, mocker):
        """Test CoinGecko 404 handling with symbol mapping."""
        # Arrange
        mock_response_404 = mocker.Mock()
        mock_response_404.status_code = 404

        mock_response_success = mocker.Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = mock_coingecko_response

        # First call returns 404, second call (with mapping) succeeds
        mock_get = mocker.patch("requests.get", side_effect=[mock_response_404, mock_response_success])

        # Act
        result = tool._get_coingecko_data("BTC")

        # Assert
        assert "error" not in result
        assert result["name"] == "Bitcoin"
        assert mock_get.call_count == 2

    def test_should_handle_coingecko_api_errors(self, tool, mocker):
        """Test CoinGecko API error handling."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 500
        mocker.patch("requests.get", return_value=mock_response)

        # Act
        result = tool._get_coingecko_data("INVALID")

        # Assert
        assert "error" in result
        assert "CoinGecko API error: 500" in result["error"]

    def test_should_create_fallback_crypto_data(self, tool):
        """Test fallback crypto data creation."""
        # Test known cryptocurrency
        btc_data = tool._create_fallback_crypto_data("BTC")
        assert btc_data["symbol"] == "BTC"
        assert btc_data["name"] == "Bitcoin"
        assert btc_data["market_cap_rank"] == 1
        assert "Store of Value" in btc_data["categories"]

        # Test unknown cryptocurrency
        unknown_data = tool._create_fallback_crypto_data("UNKNOWN")
        assert unknown_data["symbol"] == "UNKNOWN"
        assert "Cryptocurrency UNKNOWN" in unknown_data["name"]
        assert unknown_data["market_cap_rank"] == 100

    def test_should_generate_investment_thesis_for_btc(self, tool):
        """Test investment thesis generation for Bitcoin."""
        # Arrange
        crypto_data = {
            "name": "Bitcoin",
            "description": "The first cryptocurrency and digital store of value",
            "categories": ["Store of Value", "Digital Gold"],
            "market_cap_rank": 1,
            "max_supply": 21000000,
            "price_change_7d": 5.2,
            "price_change_30d": 12.8,
            "homepage": ["https://bitcoin.org"],
        }

        # Act
        thesis = tool._generate_investment_thesis("BTC", crypto_data, 8)

        # Assert
        assert thesis["symbol"] == "BTC"
        assert len(thesis["thesis_bullets"]) <= 8
        assert len(thesis["thesis_bullets"]) > 0
        assert any("top-10 cryptocurrency" in bullet for bullet in thesis["thesis_bullets"])
        assert any("digital store of value" in bullet for bullet in thesis["thesis_bullets"])
        assert any("21,000,000 tokens" in bullet for bullet in thesis["thesis_bullets"])
        assert len(thesis["references"]) > 0

    def test_should_generate_investment_thesis_for_defi_token(self, tool):
        """Test investment thesis generation for DeFi token."""
        # Arrange
        crypto_data = {
            "name": "Ethereum",
            "description": "Smart contract platform enabling decentralized applications and DeFi protocols",
            "categories": ["Smart Contract Platform", "DeFi"],
            "market_cap_rank": 2,
            "price_change_7d": 15.5,  # Strong momentum
            "homepage": ["https://ethereum.org"],
        }

        # Act
        thesis = tool._generate_investment_thesis("ETH", crypto_data, 10)

        # Assert
        assert thesis["symbol"] == "ETH"
        assert len(thesis["thesis_bullets"]) <= 10
        assert any("smart contract" in bullet.lower() for bullet in thesis["thesis_bullets"])
        assert any("defi" in bullet.lower() for bullet in thesis["thesis_bullets"])
        assert any("momentum" in bullet.lower() for bullet in thesis["thesis_bullets"])

    def test_should_perform_crypto_risk_assessment_high_risk(self, tool):
        """Test crypto risk assessment for high-risk scenario."""
        # Arrange
        crypto_data = {
            "market_cap_rank": 150,  # Low market cap
            "price_change_24h": 25.0,  # Extreme volatility
            "categories": ["Meme", "DeFi"],  # High-risk categories
            "max_supply": None,  # Unlimited supply
            "total_supply": 1000000000,
            "circulating_supply": 200000000,  # Low circulation ratio
            "description": "A meme coin with unlimited supply",
        }

        # Act
        risk_assessment = tool._perform_crypto_risk_assessment("HIGHRISK", crypto_data)

        # Assert
        assert risk_assessment["symbol"] == "HIGHRISK"
        assert risk_assessment["scale"] == "0_5"
        assert risk_assessment["score"] >= 4.0  # Should be high risk
        assert risk_assessment["level"] in ["High", "Very High"]
        assert any("market capitalization" in factor.lower() for factor in risk_assessment["risk_factors"])
        assert any("volatility" in factor.lower() for factor in risk_assessment["risk_factors"])
        assert any("meme coin" in factor.lower() for factor in risk_assessment["risk_factors"])
        assert any("unlimited supply" in factor.lower() for factor in risk_assessment["risk_factors"])

    def test_should_perform_crypto_risk_assessment_low_risk(self, tool):
        """Test crypto risk assessment for lower-risk scenario."""
        # Arrange
        crypto_data = {
            "market_cap_rank": 5,  # Top cryptocurrency
            "price_change_24h": 2.0,  # Low volatility
            "categories": ["Store of Value"],  # Lower-risk category
            "max_supply": 21000000,  # Fixed supply
            "total_supply": 19500000,
            "circulating_supply": 19500000,  # Full circulation
            "description": "Established cryptocurrency with fixed supply",
        }

        # Act
        risk_assessment = tool._perform_crypto_risk_assessment("LOWRISK", crypto_data)

        # Assert
        assert risk_assessment["symbol"] == "LOWRISK"
        assert risk_assessment["score"] < 4.0  # Should be lower risk
        assert any("large-cap" in factor.lower() for factor in risk_assessment["risk_factors"])
        # Should still have general crypto risks
        assert any("regulatory" in factor.lower() for factor in risk_assessment["risk_factors"])

    def test_should_map_risk_score_to_level_correctly(self, tool):
        """Test risk score to level mapping."""
        # Arrange & Act & Assert
        assert tool._map_score_to_level(1.0) == "Low"
        assert tool._map_score_to_level(2.0) == "Medium"
        assert tool._map_score_to_level(3.5) == "High"
        assert tool._map_score_to_level(4.5) == "Very High"

    def test_should_handle_complete_analysis_workflow(self, tool, mocker):
        """Test complete crypto analysis workflow."""
        # Arrange
        mocker.patch.object(
            EnhancedCryptoAnalysisTool,
            "_get_crypto_data",
            return_value={
                "symbol": "BTC",
                "name": "Bitcoin",
                "description": "Digital gold and store of value",
                "categories": ["Store of Value"],
                "market_cap_rank": 1,
                "max_supply": 21000000,
                "price_change_24h": 3.0,
                "sources": ["CoinGecko API"],
            },
        )
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=None)

        # Act
        result = tool._run(symbol="BTC", include_thesis=True, include_risk_assessment=True, max_thesis_bullets=5)

        # Assert
        assert "error" not in result
        assert result["symbol"] == "BTC"
        assert "crypto_data" in result
        assert "investment_thesis" in result
        assert "risk_assessment" in result
        assert result["investment_thesis"]["symbol"] == "BTC"
        assert len(result["investment_thesis"]["thesis_bullets"]) <= 5
        assert result["risk_assessment"]["symbol"] == "BTC"

    def test_should_handle_thesis_disabled(self, tool, mocker):
        """Test behavior when thesis generation is disabled."""
        # Arrange & Act
        mocker.patch.object(tool, "_get_crypto_data", return_value={"symbol": "BTC", "name": "Bitcoin", "sources": ["Test"]})
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=None)

        result = tool._run(symbol="BTC", include_thesis=False)

        # Assert
        assert "error" not in result
        assert result["investment_thesis"] is None

    def test_should_handle_risk_assessment_disabled(self, tool, mocker):
        """Test behavior when risk assessment is disabled."""
        # Arrange & Act
        mocker.patch.object(tool, "_get_crypto_data", return_value={"symbol": "BTC", "name": "Bitcoin", "sources": ["Test"]})
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=None)

        result = tool._run(symbol="BTC", include_risk_assessment=False)

        # Assert
        assert "error" not in result
        assert result["risk_assessment"] is None

    def test_should_handle_crypto_data_errors(self, tool, mocker):
        """Test handling of crypto data retrieval errors."""
        # Arrange
        mocker.patch.object(EnhancedCryptoAnalysisTool, "_get_crypto_data", return_value={"error": "API unavailable"})

        # Act
        result = tool._run(symbol="BTC")

        # Assert
        assert "error" in result
        assert "API unavailable" in result["error"]


class TestIntegrationScenarios:
    """Test integration scenarios for enhanced crypto analysis."""

    @pytest.fixture
    def tool(self):
        """Create tool instance for integration tests."""
        return EnhancedCryptoAnalysisTool()

    def test_should_handle_network_errors_gracefully(self, tool, mocker):
        """Test graceful handling of network errors."""
        # Arrange & Act
        mocker.patch.object(tool, "_get_crypto_data", return_value={"error": "Network error"})
        result = tool._run(symbol="BTC")

        # Assert
        assert "error" in result
        assert "Network error" in result["error"]

    def test_should_generate_thesis_with_error_fallback(self, tool):
        """Test thesis generation with error fallback."""
        # Arrange
        crypto_data = {}  # Empty data to trigger error handling

        # Act
        thesis = tool._generate_investment_thesis("TEST", crypto_data, 5)

        # Assert
        assert thesis["symbol"] == "TEST"
        assert len(thesis["thesis_bullets"]) >= 3  # Should have fallback bullets
        # Note: The method handles empty data gracefully without explicit error field

    def test_should_assess_risk_with_error_fallback(self, tool):
        """Test risk assessment with error fallback."""
        # Arrange
        crypto_data = {}  # Empty data to trigger error handling

        # Act
        risk_assessment = tool._perform_crypto_risk_assessment("TEST", crypto_data)

        # Assert
        assert risk_assessment["symbol"] == "TEST"
        assert risk_assessment["score"] >= 2.0  # Should be medium to high risk
        assert risk_assessment["level"] in ["Medium", "High", "Very High"]
        assert len(risk_assessment["risk_factors"]) > 0
        # Note: The method handles empty data gracefully without explicit error field
